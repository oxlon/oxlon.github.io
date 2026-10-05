"""
test_runs — icra endpoint-ləri (run_all.py --dry-run ilə), bir icra qaydası (409), ləğv, run_all.py CLI və
avtonom rejim (düşmə qovluğu). Heç bir dəftər icra edilmir.
"""
import json, os, shutil, subprocess, sys, time, unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import helpers as H                                                   # noqa: E402


class RunsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = H.make_root()
        cls.s = H.ServerProc(cls.root, "--run-arg=--sleep=0.6")

    @classmethod
    def tearDownClass(cls):
        cls.s.stop()
        shutil.rmtree(cls.root, ignore_errors=True)

    def test_1_dry_run_stage_plus_downstream(self):
        code, r = self.s.req("POST", "/api/v1/runs", {"stage": "FR10"}, token=H.WRITE)
        self.assertEqual(code, 202, r)
        self.assertEqual(r["plan"], ["FR10", "FR12", "panel", "site"])
        self.assertTrue(r["request"]["dry_run"])                                    # --dry-run-runs forces it
        done = self.s.wait_run(r["id"])
        self.assertEqual(done["status"], "dry-run", done)
        self.assertEqual([s["status"] for s in done["progress"]["steps"]], ["planned"] * 4)
        self.assertEqual(done["percent"], 100.0)
        self.assertIn("FR10", done["log_tail"])
        dep = done["manifest"]["dependency_check"]
        self.assertTrue(all(v["ok"] for v in dep.values()), dep)
        self.assertEqual(dep["FR12"]["detected"], ["FR1", "FR10"])
        m = json.loads((self.root / "logs" / r["id"] / "manifest.json").read_text(encoding="utf-8"))
        fr10 = [s for s in m["steps"] if s["name"] == "FR10"][0]
        self.assertIn("output/FR1_forecast_full.csv", fr10["inputs"])                # upstream input recorded (missing here)
        self.assertIn("nbconvert", " ".join(fr10["command"]))
        code, lst = self.s.req("GET", "/api/v1/runs")
        self.assertIn(r["id"], [x["id"] for x in lst["items"]])

    def test_2_only_and_bad_stage(self):
        code, r = self.s.req("POST", "/api/v1/runs", {"only": "FR5", "skip_build": True}, token=H.WRITE)
        self.assertEqual(r["plan"], ["FR5"])
        self.s.wait_run(r["id"])
        code, d = self.s.req("POST", "/api/v1/runs", {"stage": "FR99"}, token=H.WRITE)
        self.assertEqual(code, 400)
        self.assertIn("naməlum mərhələ", d["error"]["message"])
        self.assertEqual(self.s.req("GET", "/api/v1/runs/r20990101-000000-abcd")[0], 404)

    def test_3_busy_409_apply_blocked_and_cancel(self):
        code, r = self.s.req("POST", "/api/v1/runs", {}, token=H.WRITE)                # 8 steps x 0.6 s
        self.assertEqual(code, 202)
        code, d = self.s.req("POST", "/api/v1/runs", {"only": "FR1"}, token=H.WRITE)
        self.assertEqual(code, 409)
        self.assertIn("başqa icra gedir", d["error"]["message"])
        fields, rows = H.firm_panel_rows(20)
        code, up = self.s.req("POST", "/api/v1/uploads", H.to_csv_bytes(fields, rows), token=H.WRITE,
                              headers={"X-Filename": "FR10_firm_panel.csv", "X-Kind": "firm_panel"})
        self.assertEqual(code, 201)                                                  # validation is allowed while running
        code, d = self.s.req("POST", "/api/v1/uploads/%s/apply" % up["upload"]["id"], token=H.WRITE)
        self.assertEqual(code, 409)                                                  # inputs never change mid-run
        code, c = self.s.req("POST", "/api/v1/runs/%s/cancel" % r["id"], token=H.WRITE)
        self.assertEqual(code, 202)
        done = self.s.wait_run(r["id"], timeout=30)
        self.assertEqual(done["status"], "cancelled", done)
        st = [s["status"] for s in done["manifest"]["steps"]]
        self.assertIn("cancelled", st)
        self.assertEqual(st[-1], "skipped")
        self.assertEqual(self.s.req("POST", "/api/v1/runs/%s/cancel" % r["id"], token=H.WRITE)[0], 409)
        code, a = self.s.req("POST", "/api/v1/uploads/%s/apply?run=1" % up["upload"]["id"], token=H.WRITE)
        self.assertEqual(code, 200, a)                                               # idle again: apply + run FR10 → FR12
        self.assertEqual(a["run"]["plan"], ["FR10", "FR12", "panel", "site"])
        self.s.wait_run(a["run"]["id"])


class RunAllCliTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = H.make_root()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def cli(self, *args):
        p = subprocess.run([sys.executable, str(self.root / "run_all.py"), "--root", str(self.root)] + list(args),
                           capture_output=True, text=True, timeout=120)
        return p.returncode, p.stdout + p.stderr

    def test_dry_run_and_errors(self):
        rc, out = self.cli("--dry-run", "--stage", "FR4,FR5", "--skip-build")
        self.assertEqual(rc, 0, out)
        self.assertIn("FR4 → FR5 → FR10 → FR12", out)
        latest = json.loads((self.root / "logs/latest.json").read_text(encoding="utf-8"))
        self.assertEqual((latest["status"], latest["dry_run"]), ("dry-run", True))
        rc, out = self.cli("--dry-run", "--stage", "FR99")
        self.assertEqual(rc, 2)
        rc, out = self.cli("--stage", "FR1", "--only", "FR3")
        self.assertEqual(rc, 2)
        rc, out = self.cli("--list")
        self.assertEqual(rc, 0)
        self.assertNotIn("FƏRQ", out)

    def test_failure_stops_downstream(self):
        """Həqiqi icra: müvəqqəti kökdə FR5-in yerinə dərhal səhv verən mini dəftər — FR5 failed, panel/site skipped."""
        nb = {"cells": [{"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                         "source": "raise ValueError('sınaq xətası')"}],
              "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}},
              "nbformat": 4, "nbformat_minor": 5}
        (self.root / "FR5.ipynb").write_text(json.dumps(nb), encoding="utf-8")
        rc, out = self.cli("--only", "FR5", "--timeout", "120")
        self.assertEqual(rc, 1, out)
        m = json.loads((self.root / "logs/latest.json").read_text(encoding="utf-8"))
        self.assertEqual(m["status"], "failed")
        self.assertEqual([s["status"] for s in m["steps"]], ["failed", "skipped", "skipped"])
        self.assertIn("ValueError", m["steps"][0]["error"] or "")


class RunAllRealExecutionTest(unittest.TestCase):
    """Müvəqqəti kökdə kiçik, determinist dəftər həqiqətən icra olunur (nbconvert) — iki ardıcıl icra bayt-bayt eyni."""

    @classmethod
    def setUpClass(cls):
        cls.root = H.make_root()
        src = ("from pathlib import Path\n"
               "Path('output').mkdir(exist_ok=True)\n"
               "Path('output/FR5_test_table.csv').write_text('year,value\\n2026,1.5\\n2027,1.75\\n')\n")
        nb = {"cells": [{"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": src}],
              "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}},
              "nbformat": 4, "nbformat_minor": 5}
        (cls.root / "FR5.ipynb").write_text(json.dumps(nb), encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def test_two_runs_identical_and_snapshot(self):
        ids = []
        for _ in range(2):
            p = subprocess.run([sys.executable, str(self.root / "run_all.py"), "--root", str(self.root), "--only", "FR5",
                                "--skip-build", "--snapshot", "--keep", "1", "--timeout", "180"],
                               capture_output=True, text=True, timeout=240)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            ids.append(json.loads((self.root / "logs/latest.json").read_text(encoding="utf-8"))["run_id"])
        m = json.loads((self.root / "logs" / ids[1] / "manifest.json").read_text(encoding="utf-8"))
        st = m["steps"][0]
        self.assertEqual(st["status"], "ok")
        self.assertIn("output/FR5_test_table.csv", st["outputs"])
        self.assertTrue(all(len(v) == 32 for v in st["outputs"].values()))          # md5
        self.assertTrue(all(v is None or len(v) == 64 for v in st["inputs"].values()))  # sha256
        rep = m["reproducibility"]
        self.assertEqual((rep["previous_run"], rep["identical"]), (ids[0], True), rep)
        vint = sorted(d.name for d in (self.root / "output/vintages").iterdir())
        self.assertEqual(vint, [ids[1]])                                             # --keep 1 pruned the first
        self.assertTrue((self.root / "output/vintages" / ids[1] / "FR5_test_table.csv").exists())


class WatchModeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = H.make_root()
        cls.drop = cls.root / "data/inbox_drop"
        cls.s = H.ServerProc(cls.root, "--watch", str(cls.drop), "--poll", "0.4", "--auto-run")

    @classmethod
    def tearDownClass(cls):
        cls.s.stop()
        shutil.rmtree(cls.root, ignore_errors=True)

    def wait_for(self, pred, timeout=30):
        t0 = time.time()
        while time.time() - t0 < timeout:
            if pred():
                return True
            time.sleep(0.2)
        return False

    def test_drop_rejected_then_applied_and_run(self):
        fields, rows = H.firm_panel_rows(40)
        bad = [dict(r) for r in rows]
        bad[2]["employees"] = "-3"
        (self.drop / "FR10_firm_panel.csv").write_bytes(H.to_csv_bytes(fields, bad))
        rej = self.drop / "_rejected"
        self.assertTrue(self.wait_for(lambda: (rej / "FR10_firm_panel.csv.report.json").exists()), self.s.lines[-5:])
        rep = json.loads((rej / "FR10_firm_panel.csv.report.json").read_text(encoding="utf-8"))
        self.assertEqual(rep["errors"][0]["row"], 4)
        self.assertIn("mənfi dəyər", (rej / "FR10_firm_panel.csv.report.txt").read_text(encoding="utf-8"))
        self.assertFalse((self.root / "data/firm_panel/FR10_firm_panel.csv").exists())
        (self.drop / "FR10_firm_panel.csv").write_bytes(H.to_csv_bytes(fields, rows))
        self.assertTrue(self.wait_for(lambda: (self.root / "data/firm_panel/FR10_firm_panel.csv").exists()))
        self.assertTrue(self.wait_for(lambda: list((self.drop / "_applied").glob("*FR10_firm_panel.csv"))))
        code, runs = self.s.req("GET", "/api/v1/runs")
        watch_runs = [r for r in runs["items"] if r.get("trigger") == "watch"]
        self.assertTrue(watch_runs, runs)
        self.assertEqual(watch_runs[0]["plan"], ["FR10", "FR12", "panel", "site"])
        code, st = self.s.req("GET", "/api/v1/autonomous")
        self.assertEqual(st["watch"]["recent"][0]["status"], "applied")
        # Google Drive 'Icon\r' and temporary files are ignored
        (self.drop / "Icon\r").write_bytes(b"")
        (self.drop / "~$tmp.xlsx").write_bytes(b"x")
        time.sleep(1.5)
        self.assertFalse(list(rej.glob("Icon*")))
        self.assertTrue((self.drop / "~$tmp.xlsx").exists())


if __name__ == "__main__":
    unittest.main()
