"""Offline tests for riskunit.scalability (S1–S7)."""
import os
import unittest

os.environ.setdefault("RISK_NO_NETWORK", "1")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from riskunit import config, scalability as sc  # noqa: E402


class TestEngineAccess(unittest.TestCase):
    def test_unknown_override_fails_loudly(self):
        with self.assertRaises(sc.EngineError):
            sc.run_chain({"FR1": {"exogenous": {"no_such_input": {"add": 1}}}}, "test")
        with self.assertRaises(sc.EngineError):
            sc.run_fr1({"coefficients": {"FR1.XX|const": 1.0}}, "test")

    def test_baseline_unchanged_by_recalibration_lever(self):
        chain, _ = sc._micro()
        a = sc._flat(chain.run_chain({})["results"])
        b, _ = sc.run_chain({}, "base")
        for k in [("fr1:rgdpnon", 2027), ("fr1:infl", 2028), ("fr1:balance_n", 2030), ("fr10:ind_output", 2027)]:
            self.assertAlmostEqual(a[k], b[k], places=8)

    def test_manual_recalibration_matches_engine(self):
        """±1 SE on a slope with the intercept recalibrated by hand == engine's own recalibration."""
        _, fr1 = sc._micro()
        x25 = fr1._st()["x25"]
        cat = {f"{c['eq_id']}|{c['name']}": c for c in sc.fr1_catalogue()["coefficients"]}
        c = cat["FR1.C7_trd|ln_cons"]
        mine, _ = sc.run_fr1(sc._merge_fr1({}, sc._perturb(c, +1, x25, cat)))
        r = fr1.run({"coefficients": {"FR1.C7_trd|ln_cons": c["value"] + c["se"]}})
        eng = r["series"]["fr1:rva_trd"]
        for y, v in eng.items():
            self.assertAlmostEqual(mine[("fr1:rva_trd", int(y))] / v, 1.0, places=6)


class TestFactors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.D = sc.factor_data()
        cls.S = sc.factor_specs(cls.D)

    def test_all_factors_defined(self):
        need = {"brent", "gas", "fx", "partner", "rate", "state_inv", "remit", "drought", "quake", "food", "import", "geo"}
        self.assertTrue(need <= set(self.S))
        for f, s in self.S.items():
            self.assertGreater(s["sigma"], 0, f)
            ov, size = s["build"](1.0)
            self.assertIn("FR1", ov, f)
            self.assertTrue(np.isfinite(size), f)

    def test_hazard_is_one_sided(self):
        ov, size = self.S["quake"]["build"](-1.0)
        self.assertIsNone(ov)
        ov, size = self.S["quake"]["build"](3.0)
        self.assertLessEqual(size, 15.0)

    def test_brent_response_signs(self):
        base, _ = sc.run_chain({}, "b")
        out = {}
        for k in (-0.5, 0.5):
            f, _ = sc.run_chain(self.S["brent"]["build"](k)[0], "brent")
            out[k] = sc.derived_delta(base, f, self.D["rgdpnon_2025"])[("ru:tb_gdp", config.score_year())]
        self.assertLess(out[-0.5], 0)
        self.assertGreater(out[0.5], 0)

    def test_threshold_crossing(self):
        r = sc._cross([0, -1, -2, 1, 2], [5.0, 3.0, 1.0, 6.0, 7.0], 2.0, -1)
        self.assertAlmostEqual(r[-1], 1.5)
        self.assertTrue(np.isnan(r[1]))


class TestOutputs(unittest.TestCase):
    def test_outputs_if_present(self):
        p = config.OUTPUT / "S1_scalability_grid.csv"
        if not p.exists():
            self.skipTest("S1 hələ yaradılmayıb")
        S1 = pd.read_csv(p)
        self.assertGreaterEqual(S1["amil"].nunique(), 12)
        self.assertTrue({-3.0, 3.0} <= set(S1.loc[S1["variant"] == "σ-şəbəkə", "k_sigma"]))
        S4 = pd.read_csv(config.OUTPUT / "S4_impact_map.csv")
        self.assertGreater(S4[S4["seviyye"] == "komponent"]["komponent_id"].nunique(), 1000)
        S7 = pd.read_csv(config.OUTPUT / "S7_daily_decision.csv")
        self.assertEqual(list(S7["sira"]), list(range(1, len(S7) + 1)))
        self.assertTrue(S7["qerar_qeydi"].str.len().gt(20).all())


if __name__ == "__main__":
    unittest.main()
