"""HTTP tests over a synthetic root (offline; analysis engines stubbed). Run: python3 -m unittest discover -s api/tests"""
import io, sys, time, unittest

from helpers import Live, make_root

import analysis_scal, analysis_stress  # noqa: E402


class StubOpt:
    def inputs(self):
        return {"measures": [{"tedbir_id": "T01"}], "appetite": {"P_g_max": 0.2}}

    def run(self, req):
        if req.get("budget", 0) < 0:
            raise ValueError("negative")
        return {"mode": "optimallaşdırma", "budget": req.get("budget", 500), "portfolio": [{"tedbir_id": "T01"}],
                "objective": 5.0, "metrics": [{"metrika": "ES10_g", "baza": -0.7, "plan": -0.5}]}


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.L = Live(make_root(), refresh_cmd=[sys.executable, "-c", "import time;print('[10:00:00] A0  onurğa', flush=True);"
                                                                     "time.sleep(30)"])
        cls.L.app.opt = StubOpt()
        cls._stress, cls._scal = analysis_stress.run, analysis_scal.run

        def fake_stress(B, req):
            if not req.get("shocks"):
                from apicore import ApiError
                raise ApiError(400, "empty_scenario", "Ən azı bir şok verilməlidir")
            if req["shocks"][0].get("factor") == "boom":
                raise ValueError("operands could not be broadcast together")
            return {"name": req.get("name", "x"), "seconds": 0.01, "ru": {"deviation": [{"kind": "g", "il": 2027, "sapma": -1.0}]}}
        analysis_stress.run = fake_stress
        analysis_scal.run = lambda B, req, views=None: {"factor": {"amil": req["factor"]}, "headline": [{"il": 2027, "delta": 0.4}]}

    @classmethod
    def tearDownClass(cls):
        analysis_stress.run, analysis_scal.run = cls._stress, cls._scal
        cls.L.stop()

    # ------------------------------------------------------------ auth
    def test_auth(self):
        L = self.L
        self.assertEqual(L.req("GET", "/api/v1/health", token=None)[0], 200)
        st, b, _ = L.req("GET", "/api/v1/openapi.yaml", token=None, raw=True)
        self.assertEqual(st, 200)
        self.assertIn(b"/api/v1/stress/run", b)
        st, b, _ = L.req("GET", "/api/v1/status", token=None)
        self.assertEqual((st, b["error"]["code"]), (401, "unauthorized"))
        self.assertEqual(L.req("GET", "/api/v1/status", token="wrong")[0], 401)
        st, b, _ = L.req("POST", "/api/v1/stress/run", {"shocks": [{"factor": "brent"}]}, token="t-read")
        self.assertEqual((st, b["error"]["code"]), (403, "forbidden"))
        self.assertIn("icazəsi", b["error"]["message"])
        self.assertEqual(L.req("GET", "/api/v1/status", token="t-write")[0], 200)     # write implies read

    def test_openapi_paths_are_routed(self):
        import re
        from helpers import API
        spec = (API / "openapi.yaml").read_text(encoding="utf-8")
        paths = re.findall(r"^  (/api/v1/[^:]+):\n((?:    .*\n|\s*\n)*)", spec, re.M)
        self.assertGreaterEqual(len(paths), 20)
        for path, body in paths:
            if "{" in path or "\n    get:" not in "\n" + body:
                continue
            st = self.L.req("GET", path, token="t-read", raw=True)[0]
            self.assertNotIn(st, (404, 405), path)

    # ------------------------------------------------------------ read endpoints
    def test_status_catalog(self):
        st, b, _ = self.L.req("GET", "/api/v1/status", token="t-read")
        self.assertEqual(st, 200)
        self.assertEqual(b["baseline_id"], "B-test")
        self.assertEqual(b["feeds"]["n"], 1)
        self.assertEqual(b["alerts"]["by_severity"], {"yüksək": 1})
        self.assertIn("autonomous", b)
        st, b, _ = self.L.req("GET", "/api/v1/catalog?prefix=D5", token="t-read")
        self.assertEqual([f["file"] for f in b["files"]], ["D5_daily_monitor.csv"])
        self.assertEqual(b["files"][0]["columns"], ["indicator", "latest"])
        st, b, _ = self.L.req("GET", "/api/v1/catalog", token="t-read")
        self.assertIn("FR2_risk_scores.csv", [f["file"] for f in b["files"]])

    def test_outputs(self):
        L = self.L
        st, b, _ = L.req("GET", "/api/v1/outputs/FR2_risk_scores.csv?sort=-skor&cols=risk_id,skor&limit=1", token="t-read")
        self.assertEqual((st, b["total"], b["rows"]), (200, 2, [{"risk_id": "R12", "skor": 20}]))
        st, b, _ = L.req("GET", "/api/v1/outputs/D6_forecast_impact.csv?driver=brent&year=2027&offset=1", token="t-read")
        self.assertEqual((b["total"], len(b["rows"])), (2, 1))
        st, b, _ = L.req("GET", "/api/v1/outputs/D6_forecast_impact.csv?q=infl", token="t-read")
        self.assertEqual(b["total"], 1)
        st, b, _ = L.req("GET", "/api/v1/outputs/D6_forecast_impact.csv?nope=1", token="t-read")
        self.assertEqual((st, b["error"]["code"]), (400, "bad_parameter"))
        st, b, _ = L.req("GET", "/api/v1/outputs/D6_forecast_impact.csv?year=abc", token="t-read")
        self.assertEqual(st, 400)
        st, b, _ = L.req("GET", "/api/v1/outputs/_run_summary_v2.json", token="t-read")
        self.assertEqual(b["json"]["baseline_id"], "B-test")
        st, b, _ = L.req("GET", "/api/v1/outputs/forecast_archive/a.csv", token="t-read")
        self.assertEqual(b["rows"], [{"x": 1}])
        st, b, h = L.req("GET", "/api/v1/outputs/D7_changes.csv?format=csv", token="t-read", raw=True)
        self.assertTrue(b.startswith(b"kind,item"))
        self.assertIn("attachment", h["Content-Disposition"])
        for bad in ("/api/v1/outputs/..%2Frun_all.py", "/api/v1/outputs/.hidden.csv", "/api/v1/outputs/missing.csv"):
            self.assertIn(L.req("GET", bad, token="t-read")[0], (400, 404), bad)

    def test_risks(self):
        st, b, _ = self.L.req("GET", "/api/v1/risks", token="t-read")
        self.assertEqual([r["risk_id"] for r in b["risks"]], ["R12", "R01"])
        r01 = b["risks"][1]
        self.assertEqual((r01["tedbir_sayi"], r01["xeberdarliq_sayi"], r01["skor_evvelki"], r01["qaliq_skor"]), (1, 1, 12, 9))
        st, b, _ = self.L.req("GET", "/api/v1/risks?priority=orta", token="t-read")
        self.assertEqual(b["risks"], [])
        st, b, _ = self.L.req("GET", "/api/v1/risks/r01", token="t-read")
        self.assertEqual((st, b["risk"]["risk_id"], len(b["measures"]), len(b["factors"]), len(b["monitor"])), (200, "R01", 1, 1, 1))
        st, b, _ = self.L.req("GET", "/api/v1/risks/R99", token="t-read")
        self.assertEqual((st, b["error"]["code"]), (404, "not_found"))

    def test_monitor(self):
        st, b, _ = self.L.req("GET", "/api/v1/monitor?signal=x%C9%99b%C9%99rdarl%C4%B1q", token="t-read")
        self.assertEqual((len(b["D5"]), len(b["D6"]), len(b["D7"]), len(b["feeds"])), (1, 2, 1, 1))
        st, b, _ = self.L.req("GET", "/api/v1/monitor?targets=*", token="t-read")
        self.assertEqual(b["D6_total"], 3)

    # ------------------------------------------------------------ analysis (stubbed engines)
    def test_analysis_routes_and_errors(self):
        L = self.L
        st, b, _ = L.req("POST", "/api/v1/stress/run", {"shocks": [{"factor": "brent", "k_sigma": -2}]})
        self.assertEqual((st, b["ru"]["deviation"][0]["sapma"]), (200, -1.0))
        st, b, _ = L.req("POST", "/api/v1/stress/run", {"shocks": [{"factor": "boom"}]})
        self.assertEqual((st, b["error"]["code"]), (422, "engine_error"))
        self.assertIn("5 dəyər", b["error"]["message"])                    # translated numpy broadcast error
        self.assertIn("broadcast", b["error"]["detail"])
        st, b, _ = L.req("POST", "/api/v1/stress/run", {})
        self.assertEqual((st, b["error"]["code"]), (400, "empty_scenario"))
        st, b, _ = L.req("POST", "/api/v1/stress/run", b"{oops")
        self.assertEqual((st, b["error"]["code"]), (400, "bad_json"))
        st, b, _ = L.req("POST", "/api/v1/stress/run")
        self.assertEqual((st, b["error"]["code"]), (400, "empty_body"))
        st, b, _ = L.req("POST", "/api/v1/scalability/run", {"factor": "brent", "k_sigma": [1]})
        self.assertEqual((st, b["factor"]["amil"]), (200, "brent"))
        st, b, _ = L.req("POST", "/api/v1/optimize/run", {"budget": 100})
        self.assertEqual((st, b["objective"]), (200, 5.0))
        st, b, _ = L.req("POST", "/api/v1/optimize/run", {"budget": -1})
        self.assertEqual((st, b["error"]["message"]), (422, "Hesablama alınmadı: giriş dəyəri yanlışdır"))
        self.assertEqual(L.req("GET", "/api/v1/optimize/inputs", token="t-read")[1]["measures"][0]["tedbir_id"], "T01")
        self.assertEqual(L.req("GET", "/api/v1/nope", token="t-read")[0], 404)
        self.assertEqual(L.req("DELETE", "/api/v1/stress/run")[0], 405)

    # ------------------------------------------------------------ saved scenarios
    def test_saved_scenarios_crud(self):
        L = self.L
        st, b, _ = L.req("POST", "/api/v1/scenarios/saved", {"name": "Neft", "kind": "stress",
                                                             "request": {"shocks": [{"factor": "brent", "k_sigma": -1}]}})
        self.assertEqual(st, 201)
        sid = b["id"]
        self.assertEqual(L.req("POST", "/api/v1/scenarios/saved", {"name": "x", "kind": "bad", "request": {}})[0], 400)
        self.assertEqual(L.req("POST", "/api/v1/scenarios/saved", {"kind": "stress", "request": {}})[0], 400)
        st, b, _ = L.req("GET", "/api/v1/scenarios/saved?kind=stress", token="t-read")
        self.assertIn(sid, [s["id"] for s in b["scenarios"]])
        st, b, _ = L.req("POST", "/api/v1/scenarios/saved/%s/run" % sid)
        self.assertEqual((st, b["name"]), (200, "Neft"))
        st, b, _ = L.req("GET", "/api/v1/scenarios/saved/" + sid, token="t-read")
        self.assertEqual(b["result"]["name"], "Neft")
        st, b, _ = L.req("PUT", "/api/v1/scenarios/saved/" + sid, {"name": "Neft 2", "note": "q"})
        self.assertEqual((b["name"], b["note"], b["kind"]), ("Neft 2", "q", "stress"))
        st, b, _ = L.req("POST", "/api/v1/scenarios/saved/" + sid, {"note": "post-as-put"})
        self.assertEqual(b["note"], "post-as-put")
        self.assertEqual(L.req("DELETE", "/api/v1/scenarios/saved/" + sid)[0], 200)
        self.assertEqual(L.req("GET", "/api/v1/scenarios/saved/" + sid, token="t-read")[0], 404)

    # ------------------------------------------------------------ reports, static, events
    def test_reports_static_events(self):
        L = self.L
        st, b, _ = L.req("GET", "/api/v1/reports", token="t-read")
        self.assertEqual(b["reports"][0]["file"], "r.xlsx")
        st, b, h = L.req("GET", "/api/v1/reports/r.xlsx", token="t-read", raw=True)
        self.assertEqual((st, b), (200, b"not really xlsx"))
        st, b, h = L.req("POST", "/api/v1/reports/xlsx", {"files": ["FR2_risk_scores.csv"],
                                                          "result": {"ru": {"deviation": [{"il": 2027, "sapma": -1}]}}}, raw=True)
        self.assertEqual(st, 200)
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(b))
        self.assertEqual(wb.sheetnames, ["Məlumat", "FR2_risk_scores", "ru.deviation"])
        self.assertEqual(L.req("POST", "/api/v1/reports/xlsx", {"files": []})[0], 400)
        for path, code in (("/panel/", 200), ("/site/", 200), ("/docs/a.md", 200), ("/panel", 200), ("/run_all.py", 404),
                           ("/panel/../run_all.py", 404)):
            r = L.req("GET", path, token=None, raw=True)
            self.assertEqual(r[0], code, path)
        st, b, _ = L.req("GET", "/api/v1/events?since=0", token="t-read")
        self.assertEqual(st, 200)
        self.assertIn("last", b)


class RefreshTest(unittest.TestCase):
    def setUp(self):
        self.L = Live(make_root(), refresh_cmd=[sys.executable, "-c", "import time;print('[10:00:00] A0  onurğa', flush=True);"
                                                                      "print('[10:00:01] A2  axınlar', flush=True);time.sleep(30)"])

    def tearDown(self):
        self.L.stop()

    def wait(self, jid, status, t=20):
        t0 = time.time()
        while time.time() - t0 < t:
            j = self.L.req("GET", "/api/v1/refresh/" + jid, token="t-read")[1]
            if j["status"] == status:
                return j
            time.sleep(0.2)
        self.fail("status %s not reached: %s" % (status, j["status"]))

    def test_lock_progress_cancel(self):
        L = self.L
        st, j, _ = L.req("POST", "/api/v1/refresh", {"mode": "daily"})
        self.assertEqual((st, j["status"]), (202, "running"))
        self.assertTrue(L.app.cfg.lock_dir.is_dir())
        st, b, _ = L.req("POST", "/api/v1/refresh", {"mode": "full"})
        self.assertEqual((st, b["error"]["code"]), (409, "busy"))
        time.sleep(1.0)
        g = L.req("GET", "/api/v1/refresh/%s?tail=5" % j["id"], token="t-read")[1]
        self.assertEqual((g["progress"]["done"], g["progress"]["stage"]), (2, "A2"))
        self.assertTrue(any("onurğa" in x for x in g["log_tail"]))
        self.assertEqual(L.req("GET", "/api/v1/status", token="t-read")[1]["refresh"]["id"], j["id"])
        st, b, _ = L.req("POST", "/api/v1/refresh/%s/cancel" % j["id"])
        self.assertEqual(st, 200)
        self.wait(j["id"], "cancelled")
        t0 = time.time()
        while L.app.cfg.lock_dir.is_dir() and time.time() - t0 < 5:
            time.sleep(0.1)
        self.assertFalse(L.app.cfg.lock_dir.is_dir())
        self.assertEqual(L.req("POST", "/api/v1/refresh/%s/cancel" % j["id"])[0], 409)
        self.assertEqual(L.req("GET", "/api/v1/refresh/nope", token="t-read")[0], 404)
        kinds = [e["kind"] for e in L.req("GET", "/api/v1/events", token="t-read")[1]["events"]]
        self.assertIn("refresh.started", kinds)
        self.assertIn("refresh.finished", kinds)

    def test_external_lock_and_bad_mode(self):
        L = self.L
        L.app.cfg.lock_dir.mkdir()                     # cron/launchd holds the lock
        try:
            st, b, _ = L.req("POST", "/api/v1/refresh", {"mode": "daily"})
            self.assertEqual((st, b["error"]["code"]), (409, "busy"))
            self.assertIn("xarici", b["running"]["source"])
        finally:
            L.app.cfg.lock_dir.rmdir()
        self.assertEqual(L.req("POST", "/api/v1/refresh", {"mode": "weekly"})[0], 400)

    def test_finishes_ok(self):
        L = self.L
        L.app.runs.cfg.refresh_cmd = [sys.executable, "-c", "print('[10:00:00] A0  x')"]
        st, j, _ = L.req("POST", "/api/v1/refresh", {"mode": "pipeline"})
        g = self.wait(j["id"], "ok")
        self.assertEqual((g["returncode"], g["progress"]["pct"]), (0, 100.0))
        self.assertEqual(L.req("GET", "/api/v1/refresh", token="t-read")[1]["jobs"][0]["id"], j["id"])


if __name__ == "__main__":
    unittest.main()
