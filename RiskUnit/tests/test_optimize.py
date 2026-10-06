"""Offline tests for riskunit.optimize (M1–M7) and the v2 measures register."""
import os
import unittest

os.environ.setdefault("RISK_NO_NETWORK", "1")

import numpy as np  # noqa: E402

from riskunit import measures, optimize as op  # noqa: E402


class TestRegisterV2(unittest.TestCase):
    def test_every_measure_has_v2_attributes(self):
        m = measures.load_v2()
        self.assertTrue(m["strategiya_v2"].isin(measures.STRATEGY_V2).all())
        self.assertTrue(m["xerc_esasi"].astype(str).str.len().gt(3).all())
        self.assertTrue((m["yoxlama"] == "ok").all())

    def test_coverage_incl_new_risks(self):
        cov = measures.coverage(measures.load())
        self.assertEqual(cov.attrs["unknown_links"], [])
        self.assertTrue((cov["tedbir_sayi"] >= 1).all())


class TestOptimise(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.C = op.prepare(n=3000)
        cls.M = op.measure_table(cls.C)
        cls.m0 = op.evaluate(cls.C, cls.M, {})
        cls.W = op.weights()

    def test_no_measure_is_baseline(self):
        tot = self.m0["_tot"]["g"]
        j = self.C["j"]
        ref = self.C["base"]["g"][j] + sum(a[:, j] for a in self.C["comp"]["g"].values())
        np.testing.assert_allclose(tot, ref)
        self.assertEqual(op.objective(self.m0, self.m0, self.W, self.C), 0.0)

    def test_put_hedge_improves_fiscal_tail(self):
        m = op.evaluate(self.C, self.M, {"T26": 1.0})
        self.assertGreater(m["ES10_fis"], self.m0["ES10_fis"])
        self.assertLess(m["ORaR95"], self.m0["ORaR95"])

    def test_hedge_priced_off_forward_one_year(self):
        H = self.C["hedge"]
        self.assertTrue(np.isfinite(H["F"]) and H["F"] > 0)
        self.assertLess(H["sigma_asian"], H["sigma"])               # averaging lowers the effective volatility
        self.assertEqual(H["tenor"], 1.0)
        c = float(self.M.loc[self.M["effekt_modeli"] == "put_hedge", "xerc_mln_azn"].iloc[0])
        a = float(self.M.loc[self.M["effekt_modeli"] == "put_hedge", "effekt_guc"].iloc[0])
        self.assertAlmostEqual(c, round(a * self.C["oil"]["k"] * H["put"], 1), delta=0.11)

    def test_reserve_caps_t09_and_consolidated_metric(self):
        m = op.evaluate(self.C, self.M, {"T09": 1.0})
        self.assertGreater(m["ES10_g"], self.m0["ES10_g"])
        self.assertGreater(op.objective(m, self.m0, self.W, self.C), 0.0)   # was −7,85 on the state-budget-only metric
        self.assertNotEqual(m["CaR95"], self.m0["CaR95"])

    def test_fixed_and_excluded(self):
        M2, E = op.individual_effects(self.C, self.M, self.m0, self.W)
        cand = [t for t in self.M.index if self.M.at[t, "effekt_modeli"] != "none"]
        o = op.optimise(self.C, self.M, E, self.m0, self.W, op.appetite(), 300, cand, fixed=["T28"], excluded=["T27"])
        self.assertIn("T28", o["sel"])
        self.assertNotIn("T27", o["sel"])
        self.assertLessEqual(o["cost"], 300 + 1e-9)
        self.assertIs(op._score, op.score)

    def test_rebalancing_lowers_var(self):
        m = op.evaluate(self.C, self.M, {"T27": 1.0})
        self.assertLess(m["VaR95_ARDNF"], self.m0["VaR95_ARDNF"])

    def test_cpi_measures_lower_upper_tail(self):
        m = op.evaluate(self.C, self.M, {"T24": 1.0, "T25": 1.0})
        self.assertLess(m["ES10_cpi"], self.m0["ES10_cpi"])

    def test_budget_respected(self):
        M2, E = op.individual_effects(self.C, self.M, self.m0, self.W)
        cand = [t for t in self.M.index if self.M.at[t, "effekt_modeli"] != "none"]
        for B in (50, 300):
            o = op.optimise(self.C, self.M, E, self.m0, self.W, op.appetite(), B, cand)
            self.assertLessEqual(o["cost"], B + 1e-9)

    def test_implementation_plan_phases(self):
        P = op.implementation_plan(self.M, {"T01"})
        self.assertEqual(len(P), 4 * len(self.M))
        self.assertTrue((P["baslama"] <= P["bitme"]).all())


if __name__ == "__main__":
    unittest.main()
