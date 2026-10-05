"""
test_units — serversiz sınaqlar: multipart təhlilçisi, run_all planı və asılılıq yoxlaması (real dəftərlərin
yalnız oxunması), iş kitabı və DSK validatorları, DSK yeniləməsi (saxta endirmə — şəbəkə yoxdur).
"""
import hashlib, os, shutil, sys, unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["MICRO_NO_NETWORK"] = "1"
import helpers as H                                                   # noqa: E402
import multipart_form as M                                            # noqa: E402
import run_manager                                                    # noqa: E402
import validate_dsk, validate_tables, validate_workbook                # noqa: E402

run_all = run_manager.run_all


class MultipartTest(unittest.TestCase):
    def test_roundtrip_and_edge_cases(self):
        payload = b"a,b\r\n1,2\r\n--not-a-boundary\r\n\r\n"
        body, ct = M.build({"kind": "dsk", "subfolder": "dsk_services"}, {"file": ("007_1en.xls", payload, None)})
        p = M.parse(body, ct)
        self.assertEqual(p["file"].data, payload)
        self.assertEqual((p["kind"].text, p["subfolder"].text), ("dsk", "dsk_services"))
        self.assertEqual(M.parse(body.replace(b"\r\n", b"\n"), ct)["kind"].text, "dsk")
        ct2 = 'multipart/form-data; boundary="b o"'
        b2 = (b'--b o\r\nContent-Disposition: form-data; name="file"; filename*=UTF-8\'\'%C6%8Fmlak.csv\r\n\r\n'
              b'x\r\n--b o\r\nContent-Disposition: form-data; name="e"\r\n\r\n\r\n--b o--\r\n')
        p2 = M.parse(b2, ct2)
        self.assertEqual((p2["file"].filename, p2["e"].data), ("Əmlak.csv", b""))
        for bad in ((b"x", "text/plain"), (b"no boundary here", "multipart/form-data; boundary=q"),
                    (b"--q\r\nContent-Disposition: form-data\r\n\r\nx\r\n--q--", "multipart/form-data; boundary=q"),
                    (b"--q\r\nX: y\r\n\r\nunterminated", "multipart/form-data; boundary=q")):
            with self.assertRaises(M.MultipartError):
                M.parse(*bad)


class RunAllPlanTest(unittest.TestCase):
    def test_plan(self):
        self.assertEqual(run_all.plan("FR4")[0], ["FR4", "FR10", "FR12"])
        self.assertEqual(run_all.plan("FR5")[0], ["FR5"])
        self.assertEqual(run_all.plan("FR1")[0], run_all.STAGES)
        self.assertEqual(run_all.plan("FR3")[0], ["FR3", "FR4", "FR10", "FR12"])
        self.assertEqual(run_all.plan(None, "FR12,FR1")[0], ["FR1", "FR12"])
        self.assertEqual(run_all.plan(None, None, True), (run_all.STAGES, []))
        with self.assertRaises(ValueError):
            run_all.plan("FR2")

    def test_declared_dag_matches_notebooks(self):
        """Elan olunmuş asılılıqlar real dəftərlərdəki read_csv oxumaları ilə eynidir (yalnız oxunur)."""
        rep = run_all.dep_check(H.REAL_ROOT)
        bad = {s: (r["declared"], r["detected"]) for s, r in rep.items() if not r["ok"] or not r["order_ok"]}
        self.assertEqual(bad, {})


class ValidatorSyncTest(unittest.TestCase):
    def test_regions_and_column_maps_from_notebooks(self):
        self.assertEqual(validate_tables.regions(H.REAL_ROOT, "firm_panel"), validate_tables.FR10_REGIONS)
        self.assertEqual(validate_tables.regions(H.REAL_ROOT, "business_register"), validate_tables.FR12_REGIONS)
        cm = validate_tables.column_map(H.REAL_ROOT, "firm_panel")
        self.assertTrue(cm["total_assets"][1] and not cm["exports"][1])
        self.assertEqual(len([k for k, v in cm.items() if v[1]]), 22)

    def test_workbook_addresses_extracted(self):
        a = validate_workbook.extract_addresses(H.REAL_ROOT)
        mods = {x["module"] for x in a}
        self.assertTrue({"FR1", "FR3", "FR4", "FR5", "FR12"} <= mods, mods)
        self.assertGreater(len([x for x in a if x["module"] == "FR1"]), 150)


class WorkbookValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = H.tmpdir("wbtest-")
        cls.wb = next((H.REAL_ROOT / "data").glob("Statistik data dinamika*.xlsx"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_current_workbook_passes_and_broken_fails(self):
        import openpyxl
        r = validate_workbook.validate_workbook(self.wb, H.REAL_ROOT)
        self.assertTrue(r["ok"], r["errors"][:3])
        self.assertEqual(r["summary"]["last_annual_year"], 2025)
        wb = openpyxl.load_workbook(self.wb)
        wb["Sosial sektor "]["A52"] = "Başqa sətir"
        del wb["Neft-Qaz sektoru"]
        bad = self.tmp / "Statistik data dinamika 01.01.2027.xlsx"
        wb.save(bad)
        r = validate_workbook.validate_workbook(bad, H.REAL_ROOT, reference=self.wb)
        self.assertFalse(r["ok"])
        msgs = [(e.get("module"), e.get("sheet"), e.get("row")) for e in r["errors"]]
        self.assertIn(("FR3", "Sosial sektor ", 52), msgs)
        self.assertTrue(any(e.get("sheet") == "Neft-Qaz sektoru" and "Vərəq yoxdur" in e["message"] for e in r["errors"]))
        (self.tmp / "junk.xlsx").write_bytes(b"not a zip")
        self.assertFalse(validate_workbook.validate_workbook(self.tmp / "junk.xlsx", H.REAL_ROOT)["ok"])


class DskRefreshTest(unittest.TestCase):
    def setUp(self):
        self.root = H.make_root()
        sys.path.insert(0, str(H.API))
        from apicore import Config
        import apidb
        self.cfg = Config(root=self.root, db=self.root / "t.db")
        apidb.init(self.cfg.db)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_download_blocked_in_tests(self):
        import autonomous
        with self.assertRaises(RuntimeError):
            autonomous.download("https://www.stat.gov.az/source/labour/en/002_1-2en.xls")

    def test_refresh_with_fake_fetch(self):
        import autonomous
        targets = autonomous.dsk_targets(self.cfg)
        self.assertGreater(len(targets), 100)
        cur = (self.root / "data/dsk/002_1-2en.xls").read_bytes()
        new = validate_dsk.XLS_MAGIC + b"new content"
        calls = []

        def fetch(url, timeout=60):
            calls.append(url)
            if url.endswith("/labour/en/002_1-2en.xls"):
                return new
            if url.endswith("002_3en.xls"):
                return b"<html>404</html>"
            raise OSError("offline")
        rep = autonomous.dsk_refresh(self.cfg, fetch=fetch, log=lambda *_: None)
        self.assertEqual(len(calls), len(targets))
        self.assertEqual([c["path"] for c in rep["changed"]], ["dsk/002_1-2en.xls"])
        self.assertEqual(rep["affected_stages"], ["FR4", "FR10", "FR12"])
        self.assertEqual((self.root / "data/dsk/002_1-2en.xls").read_bytes(), new)
        backups = list((self.root / "data/_replaced").glob("*_dsk-refresh/dsk/002_1-2en.xls"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), cur)
        self.assertTrue(any("HTML" in f["error"] for f in rep["failed"]))
        rep2 = autonomous.dsk_refresh(self.cfg, fetch=fetch, log=lambda *_: None)   # same bytes again: no change, no run
        self.assertEqual((rep2["changed"], rep2["affected_stages"]), ([], []))
        self.assertEqual(rep2["unchanged"], 1)


if __name__ == "__main__":
    unittest.main()
