"""Live end-to-end test (real engines, FR4 with RiskUnit over HTTP — or its cache when unreachable).
Runs only with POLICY_API_LIVE=1 (≈ 10–40 s):  POLICY_API_LIVE=1 python3 -m unittest discover -s api/tests -t api/tests -p test_live.py"""
import os, shutil, sys, tempfile, time, unittest, warnings
from pathlib import Path

LIVE = os.environ.get("POLICY_API_LIVE") == "1"
if LIVE:
    os.environ.setdefault("POLICY_NO_NETWORK", "0")          # live = RiskUnit over HTTP (cache if unreachable)

import helpers  # noqa: E402
from helpers import Live  # noqa: E402


@unittest.skipUnless(LIVE, "POLICY_API_LIVE=1 deyil — canlı sınaq buraxıldı")
class LiveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.simplefilter("ignore", ResourceWarning)
        tmp = Path(tempfile.mkdtemp(prefix="pu_live_"))
        (tmp / "output").mkdir()
        shutil.copy2(helpers.PU / "output" / "_catalog.csv", tmp / "output" / "_catalog.csv")
        cls.L = Live(tmp, config_dir=helpers.PU / "config")      # real config (read-only here), temp DB/output

    @classmethod
    def tearDownClass(cls):
        cls.L.stop()
        helpers.rebind_default()

    def test_full_run(self):
        t0 = time.time()
        st, b, _ = self.L.req("POST", "/api/v1/scenarios/mw20_2027/run",
                              {"side_effects": "full", "detail": "summary", "wait": 240, "force": True})
        secs = time.time() - t0
        self.assertEqual(st, 200, b)
        sys.stderr.write("\n  canlı: %.1f s, vaxtlar %s\n" % (secs, b["timings"]))
        self.assertLess(b["seconds"], 30.0)
        self.assertEqual({e["id"]: e["status"] for e in b["engines"]}["micro"], "ok")
        hz = {r["horizon"] for r in b["headline"] if r["indicator"] == "gdp_real"}
        self.assertEqual(hz, {"qısa", "orta", "uzun"})
        se = b["side_effects"]
        self.assertTrue(se["items"], se.get("warnings"))
        self.assertTrue(se["variants"])
        self.assertTrue(se["mitigation"])
        self.assertTrue(b["comparison"])
        self.assertGreaterEqual(len(b["kpi"]["values"]), 5)
        self.assertTrue(b["vintage"]["vintage_id"].startswith("PV-"))
        sys.stderr.write("  %s\n  risk: %s\n" % (b["text_az"], (se.get("risk_profile") or {}).get("status")))


if __name__ == "__main__":
    unittest.main()
