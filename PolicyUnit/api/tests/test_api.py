"""API tests (offline; engines stubbed). Run: python3 -m unittest discover -s api/tests -t api/tests"""
import json, sys, time, unittest, warnings

from helpers import Live, make_root, rebind_default, stub_engines

SCN = {"id": "t_mw10", "name_az": "Sınaq: MƏH +10 %", "start_year": 2027,
       "instruments": [{"instrument": "min_wage", "years": "all", "size": 10}], "tags": ["sınaq"]}
KPIS = ["gdp_short", "gdp_medium", "gdp_long", "inflation_short", "unemployment"]


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.simplefilter("ignore", ResourceWarning)
        cls.L = Live(make_root(), refresh_cmd=[sys.executable, "-c",
                                               "print('[core.validate] başladı');print('[core.validate] OK (0.0 s)')"])
        cls.restore = stub_engines()

    @classmethod
    def tearDownClass(cls):
        cls.restore()
        cls.L.stop()
        rebind_default()

    def r(self, *a, **k):
        return self.L.req(*a, **k)

    # ---------------------------------------------------------------- system & auth
    def test_health_open_and_auth(self):
        self.assertEqual(self.r("GET", "/api/v1/health", token=None)[0], 200)
        self.assertEqual(self.r("GET", "/api/v1/openapi.yaml", token=None, raw=True)[0], 200)
        st, b, _ = self.r("GET", "/api/v1/status", token=None)
        self.assertEqual(st, 401)
        self.assertIn("Bearer", b["error"]["message"])
        self.assertEqual(self.r("POST", "/api/v1/scenarios/validate", SCN, token="t-read")[0], 403)
        self.assertEqual(self.r("GET", "/api/v1/status", token="bad")[0], 401)
        self.assertEqual(self.r("GET", "/api/v2/status")[0], 404)

    def test_status(self):
        st, b, _ = self.r("GET", "/api/v1/status")
        self.assertEqual(st, 200)
        self.assertTrue(b["vintage"]["vintage_id"].startswith("PV-"))
        self.assertEqual({e["id"] for e in b["engines"]}, {"micro", "caem", "oxlon", "io", "microsim", "longrun", "riskfx"})
        self.assertIn("qısa", b["horizons"])

    # ---------------------------------------------------------------- data
    def test_catalog_outputs(self):
        b = self.r("GET", "/api/v1/catalog?prefix=P1_")[1]
        self.assertTrue(any(f["file"] == "P1_headline.csv" and f["exists"] for f in b["files"]))
        b = self.r("GET", "/api/v1/outputs/P1_headline.csv?scenario=mw20_2027&sort=-effect&limit=1")[1]
        self.assertEqual((b["total"], b["rows"][0]["effect"]), (2, 0.9))
        st, body, h = self.r("GET", "/api/v1/outputs/P1_headline.csv?format=csv", raw=True)
        self.assertTrue(body.startswith(b"scenario,"))
        self.assertEqual(self.r("GET", "/api/v1/outputs/P1_headline.csv?nosuch=1")[0], 400)
        self.assertEqual(self.r("GET", "/api/v1/outputs/..%2Fconfig%2Fkpi.csv")[0], 400)
        self.assertEqual(self.r("GET", "/api/v1/outputs/none.csv")[0], 404)

    def test_static(self):
        self.assertEqual(self.r("GET", "/panel/", token=None, raw=True)[1], b"<html>panel</html>")
        self.assertEqual(self.r("GET", "/api-docs/OXUYUN.md", token=None, raw=True)[0], 200)
        self.assertEqual(self.r("GET", "/api-docs/secret.py", token=None, raw=True)[0], 404)
        self.assertEqual(self.r("GET", "/run_all.py", token=None, raw=True)[0], 404)

    # ---------------------------------------------------------------- instruments
    def test_instruments(self):
        b = self.r("GET", "/api/v1/instruments")[1]
        self.assertGreater(b["n"], 10)
        mw = [i for i in b["instruments"] if i["id"] == "min_wage"][0]
        self.assertIn("micro", mw["engines"])
        self.assertTrue(mw["adapters"])
        self.assertEqual(self.r("GET", "/api/v1/instruments/nope")[0], 404)
        sch = self.r("GET", "/api/v1/instruments/schema")[1]
        self.assertIn("micro", sch["target_keys"])
        self.assertTrue(sch["procedure_az"])

    def test_new_instrument(self):
        body = {"instrument": {"id": "t_reg_inv", "name_az": "Sınaq regional investisiya", "family": "xərc", "unit": "mln_azn",
                               "default_size": 300, "min": 0, "max": 3000, "cost_rule": "spend", "cost_in_fr1": "yes"},
                "adapters": [{"engine": "caem", "target_key": "gcap_y", "transform": "target_gdp", "note_az": "sınaq"}],
                "test_run": False}
        bad = dict(body, instrument=dict(body["instrument"], family="yox", min=500))
        st, b, _ = self.r("POST", "/api/v1/instruments/validate", bad)
        self.assertFalse(b["valid"])
        self.assertTrue(any("ailə" in e for e in b["errors"]))
        st, b, _ = self.r("POST", "/api/v1/instruments/new", bad)
        self.assertEqual(st, 422)
        st, b, _ = self.r("POST", "/api/v1/instruments/new", dict(body, dry_run=True))
        self.assertEqual((st, b["dry_run"]), (200, True))
        st, b, _ = self.r("POST", "/api/v1/instruments/new", body)
        self.assertEqual(st, 201, b)
        got = self.r("GET", "/api/v1/instruments/t_reg_inv")[1]
        self.assertEqual(got["origin"], "api")
        s = {"id": "t_reg", "name_az": "Reg", "start_year": 2026, "instruments": [{"instrument": "t_reg_inv", "size": 100}]}
        self.assertTrue(self.r("POST", "/api/v1/scenarios/validate", s)[1]["valid"])
        self.assertEqual(self.r("POST", "/api/v1/instruments/new", body)[0], 422)          # duplicate id
        self.assertEqual(self.r("DELETE", "/api/v1/instruments/min_wage")[0], 409)          # not API-added
        self.assertEqual(self.r("DELETE", "/api/v1/instruments/t_reg_inv")[0], 200)
        self.assertEqual(self.r("GET", "/api/v1/instruments/t_reg_inv")[0], 404)

    # ---------------------------------------------------------------- scenarios
    def test_validate_errors_az(self):
        b = self.r("POST", "/api/v1/scenarios/validate", {"id": "Bad Id", "name_az": "x", "start_year": 2040,
                                                          "instruments": [{"instrument": "vat_rate", "size": 99}]})[1]
        self.assertFalse(b["valid"])
        txt = " ".join(b["errors"])
        self.assertIn("kiçik latın", txt)
        self.assertIn("intervalından kənardır", txt)
        b = self.r("POST", "/api/v1/scenarios/validate", SCN)[1]
        self.assertTrue(b["valid"], b)
        self.assertEqual(b["normalised"]["instruments"][0]["years"][0], 2027)

    def test_scenario_crud(self):
        self.assertEqual(self.r("POST", "/api/v1/scenarios", dict(SCN, id="t_crud"))[0], 201)
        self.assertEqual(self.r("POST", "/api/v1/scenarios", dict(SCN, id="t_crud"))[0], 409)
        self.assertEqual(self.r("POST", "/api/v1/scenarios", dict(SCN, id="mw20_2027"))[0], 409)
        st, b, _ = self.r("PUT", "/api/v1/scenarios/t_crud", dict(SCN, id="t_crud", instruments=[{"instrument": "min_wage", "size": 500}]))
        self.assertEqual(st, 422)
        self.assertTrue(b["errors"])
        self.assertEqual(self.r("PUT", "/api/v1/scenarios/t_crud", dict(SCN, id="other"))[0], 400)
        b = self.r("PUT", "/api/v1/scenarios/t_crud", dict(SCN, id="t_crud", name_az="Yeni ad"))[1]
        self.assertEqual((b["source"], b["scenario"]["name_az"]), ("draft", "Yeni ad"))
        st, b, _ = self.r("POST", "/api/v1/scenarios/t_crud/duplicate", {})
        self.assertEqual((st, b["id"]), (201, "t_crud_kopya"))
        st, raw, h = self.r("GET", "/api/v1/scenarios/t_crud/export", raw=True)
        self.assertIn("attachment", h.get("Content-Disposition", ""))
        exp = json.loads(raw)
        b = self.r("POST", "/api/v1/scenarios/import", {"scenarios": [dict(exp, id="t_imp"), {"id": "t_bad"}]})[1]
        self.assertEqual(b["imported"], ["t_imp"])
        self.assertIn("t_bad", b["errors"])
        lst = self.r("GET", "/api/v1/scenarios?source=draft")[1]
        self.assertTrue({"t_crud", "t_crud_kopya", "t_imp"} <= {s["id"] for s in lst["scenarios"]})
        b = self.r("POST", "/api/v1/scenarios/t_imp/promote")[1]
        self.assertEqual(b["source"], "official")
        self.assertTrue((self.L.root / "config" / "scenarios" / "t_imp.json").is_file())
        self.assertEqual(self.r("DELETE", "/api/v1/scenarios/t_imp")[0], 409)
        b = self.r("DELETE", "/api/v1/scenarios/t_imp?force=1")[1]
        self.assertIn("_arxiv", b["archived"])
        for sid in ("t_crud", "t_crud_kopya"):
            self.assertEqual(self.r("DELETE", "/api/v1/scenarios/" + sid)[0], 200)
        self.assertEqual(self.r("GET", "/api/v1/scenarios/t_crud")[0], 404)

    # ---------------------------------------------------------------- runs, compare, KPI
    def test_run_and_cache(self):
        self.r("POST", "/api/v1/scenarios", dict(SCN, id="t_run"))
        st, b, _ = self.r("POST", "/api/v1/scenarios/t_run/run", {"side_effects": "rules", "kpis": KPIS})
        self.assertEqual(st, 200, b)
        self.assertFalse(b["cached"])
        self.assertEqual(set(b["horizons"]), {"qısa", "orta", "uzun"})
        self.assertTrue(any(r["indicator"] == "gdp_real" for r in b["headline_wide"]))
        self.assertEqual(b["kpi"]["selected"], KPIS)
        self.assertIn("Təsir = ssenari", b["text_az"])
        self.assertTrue(b["comparison"])                            # micro vs caem (NFR2)
        st, b2, _ = self.r("POST", "/api/v1/scenarios/t_run/run", {"side_effects": "rules", "detail": "summary"})
        self.assertTrue(b2["cached"])
        self.assertNotIn("effects", b2)
        self.assertEqual(self.r("POST", "/api/v1/scenarios/t_run/run", {"kpis": KPIS[:3]})[0], 422)
        self.assertEqual(self.r("POST", "/api/v1/scenarios/t_run/run", {"side_effects": "x"})[0], 400)
        st, b, _ = self.r("POST", "/api/v1/runs", {"scenario": dict(SCN, id="t_adhoc"), "side_effects": "none", "wait": 0})
        self.assertIn(st, (200, 202))
        rid = b["run_id"]
        for _ in range(100):
            g = self.r("GET", "/api/v1/runs/%s?detail=summary" % rid)[1]
            if g["status"] != "running":
                break
            time.sleep(0.1)
        self.assertEqual(g["status"], "ok")
        self.assertEqual(g["progress"]["pct"], 100.0)
        self.assertEqual(self.r("POST", "/api/v1/runs/%s/cancel" % rid)[0], 409)
        self.assertEqual(self.r("GET", "/api/v1/runs/nope")[0], 404)
        st, x, h = self.r("POST", "/api/v1/reports/xlsx", {"run_id": b["run_id"]}, raw=True)
        self.assertEqual(st, 200)
        self.assertTrue(x[:2] == b"PK")

    def test_compare_kpi(self):
        self.assertEqual(self.r("POST", "/api/v1/compare", {"scenarios": ["mw20_2027"]})[0], 422)
        st, b, _ = self.r("POST", "/api/v1/compare", {"scenarios": ["mw20_2027", "vat_minus2"], "kpis": KPIS[:4]})
        self.assertEqual(st, 422)
        self.assertIn("ən azı 5", b["error"]["message"])
        st, b, _ = self.r("POST", "/api/v1/compare", {"scenarios": ["mw20_2027", "vat_minus2", "pension10_2027"],
                                                      "kpis": KPIS, "weights": {"gdp_short": 3}})
        self.assertEqual(st, 200, b)
        self.assertEqual([r["rank"] for r in b["ranking"]], [1, 2, 3])
        self.assertEqual(len(b["matrix"]), 5)
        self.assertIn("Reytinq", b["text_az"])
        cat = self.r("GET", "/api/v1/kpi")[1]
        self.assertEqual(cat["min_selected"], 5)
        self.assertEqual(self.r("POST", "/api/v1/kpi/sets", {"name": "az", "kpis": KPIS[:4]})[0], 422)
        self.assertEqual(self.r("POST", "/api/v1/kpi/sets", {"name": "w", "kpis": KPIS, "weights": {"gdp_short": -1}})[0], 422)
        st, ks, _ = self.r("POST", "/api/v1/kpi/sets", {"name": "Mənim", "kpis": KPIS, "weights": {"gdp_long": 2}})
        self.assertEqual(st, 201)
        b = self.r("PUT", "/api/v1/kpi/sets/" + ks["id"], {"name": "Dəyişdi"})[1]
        self.assertEqual(b["name"], "Dəyişdi")
        st, c, _ = self.r("POST", "/api/v1/compare", {"scenarios": ["mw20_2027", "vat_minus2"], "kpi_set": ks["id"]})
        self.assertEqual(st, 200)
        self.assertIn("Dəyişdi", c["kpi_source"])
        self.assertEqual(self.r("DELETE", "/api/v1/kpi/sets/" + ks["id"])[0], 200)

    # ---------------------------------------------------------------- refresh
    def test_refresh(self):
        st, j, _ = self.r("POST", "/api/v1/refresh", {"note": "sınaq"})
        self.assertEqual(st, 202, j)
        for _ in range(100):
            g = self.r("GET", "/api/v1/refresh/" + j["id"])[1]
            if g["status"] != "running":
                break
            time.sleep(0.1)
        self.assertEqual(g["status"], "ok")
        self.assertEqual(g["progress"]["stage"], "core.validate")
        self.assertEqual(self.r("POST", "/api/v1/refresh", {"only": "a;rm -rf"})[0], 400)
        self.assertEqual(self.r("GET", "/api/v1/refresh/nope")[0], 404)


if __name__ == "__main__":
    unittest.main()
