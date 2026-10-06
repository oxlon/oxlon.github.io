"""Live end-to-end: stress/run and scalability/run against the REAL riskunit modules and the MicroUnit chain
(read-only; offline with RISK_NO_NETWORK=1). Skipped when the upstream units are not on this machine.
Targets (contract): stress/run < 10 s, scalability/run < 5 s (after the one-off cache preparation)."""
import time, unittest
from pathlib import Path

from helpers import API, Live

ROOT = API.parent
MICRO = ROOT.parent / "MicroUnit" / "microlib" / "engines" / "chain.py"


@unittest.skipUnless(MICRO.exists() and (ROOT / "output" / "S0_factor_sigma.csv").exists(), "MicroUnit / RU çıxışları yoxdur")
class LiveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.L = Live(ROOT)
        t0 = time.time()
        st, b, _ = cls.L.req("GET", "/api/v1/scalability/factors", token="t-read")   # warm-up (prepare caches)
        cls.prepare_s = time.time() - t0
        assert st == 200, b

    @classmethod
    def tearDownClass(cls):
        cls.L.stop(rm_root=False)

    def test_stress_run(self):
        req = {"name": "Neft −2σ + devalvasiya + faiz", "shocks": [{"factor": "brent", "k_sigma": -2}, {"factor": "fx", "size": 25},
                                                                  {"factor": "rate", "k_sigma": 1}], "n": 4000}
        t0 = time.time()
        st, b, _ = self.L.req("POST", "/api/v1/stress/run", req)
        dt = time.time() - t0
        self.assertEqual(st, 200, b)
        self.assertLess(dt, 10.0)
        print("\n  stress/run: %.2f s (server %.2f s; hazırlıq %.1f s)" % (dt, b["seconds"], self.prepare_s))
        head = {(r["hedef_id"], r["il"]): r["delta"] for r in b["micro"]["headline"]}
        self.assertLess(head[("ru:nonoil_lvl", b["score_year"])], 0)          # lower oil → lower non-oil GDP level
        self.assertGreater(b["micro"]["components"]["n_affected"], 100)
        dev = {(r["kind"], r["il"]): r for r in b["ru"]["deviation"]}
        self.assertLess(dev[("g", b["score_year"])]["sapma"], 0)
        self.assertIn("brent_path", b["ru"]["ru_overrides_used"])
        self.assertEqual(b["ru"]["ru_overrides_used"]["deval_year"], b["score_year"])
        views = {r["baxis"] for r in b["ru"]["distribution"]}
        self.assertEqual(views, {"şərtsiz", "şoka şərtli"})
        # natural-unit size round-trips to the same k
        st, b2, _ = self.L.req("POST", "/api/v1/stress/run", {"shocks": [{"factor": "brent", "size": b["shocks"][0]["size"]}],
                                                              "stochastic": False})
        self.assertAlmostEqual(b2["shocks"][0]["k_sigma"], -2.0, places=4)
        self.assertNotIn("distribution", b2["ru"])

    def test_scalability_run(self):
        t0 = time.time()
        st, b, _ = self.L.req("POST", "/api/v1/scalability/run", {"factor": "brent", "k_sigma": [-2, -1, 1, 2]})
        dt = time.time() - t0
        self.assertEqual(st, 200, b)
        self.assertLess(dt, 5.0)
        print("\n  scalability/run (4 ölçü + canlı): %.2f s (server %.2f s)" % (dt, b["seconds"]))
        self.assertGreaterEqual(len(b["sizes"]), 4)
        e = [x for x in b["elasticity"] if x["hedef_id"] == "ru:nonoil_lvl" and x["il"] == b["score_year"]][0]
        self.assertGreater(e["orta_per_sigma"], 0)                               # +Brent raises non-oil level
        self.assertTrue(b["components"] and b["groups"])
        st, b, _ = self.L.req("POST", "/api/v1/scalability/run", {"factor": "quake", "k_sigma": [-1]})
        self.assertEqual((st, b["error"]["code"]), (400, "bad_shock"))

    def test_optimize_run(self):
        t0 = time.time()
        st, b, _ = self.L.req("POST", "/api/v1/optimize/run", {"budget": 500})
        self.assertEqual(st, 200, b)
        print("\n  optimize/run (hazırlıq daxil): %.2f s; portfel %d tədbir, hədəf funksiyası %.2f"
              % (time.time() - t0, len(b["portfolio"]), b["objective"]))
        self.assertLessEqual(b["frontier_point"]["xerc"], 500 + 1e-6)
        self.assertTrue(b["residual"] and b["metrics"])
        st, b, _ = self.L.req("POST", "/api/v1/optimize/run", {"budget": 500, "include": ["T99"]})
        self.assertEqual((st, b["error"]["code"]), (400, "unknown_measure"))

    def test_stress_errors_real(self):
        st, b, _ = self.L.req("POST", "/api/v1/stress/run", {"micro_overrides": {"FR1": {"exogenous": {"bogus": {"pct": 1}}}}})
        self.assertEqual((st, b["error"]["code"]), (422, "engine_error"))
        self.assertIn("override", b["error"]["message"])
        st, b, _ = self.L.req("POST", "/api/v1/stress/run", {"shocks": [{"factor": "brent", "k_sigma": 9}]})
        self.assertEqual(st, 400)


if __name__ == "__main__":
    unittest.main()
