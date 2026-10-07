"""Core engine/integration tests (offline): MicroUnit counterfactual signs, fiscal accounting,
financing variants, long-run extension, method comparison (NFR2) and KPI scoring (FR5)."""
import os
import sys
import unittest
from pathlib import Path

os.environ["POLICY_NO_NETWORK"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hermetic  # noqa: E402,F401  (temp work/ and output/)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policyunit import eng_micro, integrate, kpi, scenario as scn  # noqa: E402

_CACHE = {}


def run(sid):
    if sid not in _CACHE:
        _CACHE[sid] = integrate.run_scenario(scn.load(sid))
    return _CACHE[sid]


def val(f, ind, year, engine="micro", col="delta_pct"):
    g = f[(f.engine == engine) & (f.indicator == ind) & (f.year == year)]
    return float(g[col].iloc[0])


class TestMicro(unittest.TestCase):
    def test_baseline_counterfactual_zero(self):
        s = scn.normalise({"id": "z", "name_az": "z", "start_year": 2026, "instruments": [
            {"instrument": "policy_rate", "years": [2026], "size": 0.0, "unit": "pp"}]})
        f = eng_micro.run(s).frame
        self.assertLess(f[f.indicator.isin(["gdp_real", "cpi", "debt"])]["delta"].abs().max(), 1e-6)

    def test_min_wage_signs(self):
        f = run("mw20_2027")["frame"]
        self.assertGreater(val(f, "wage_real", 2028), 0)
        self.assertGreater(val(f, "cpi", 2028), 0)
        self.assertGreater(val(f, "gdp_nonoil_real", 2028), 0)

    def test_public_investment_financing(self):
        d = run("pubinv1bn_deficit")["frame"]
        s = run("pubinv1bn_sofaz")["frame"]
        self.assertAlmostEqual(val(d, "gdp_real", 2027), val(s, "gdp_real", 2027), places=6)
        self.assertGreater(val(d, "debt", 2028, col="delta"), val(s, "debt", 2028, col="delta") + 2000)
        self.assertLess(val(s, "sofaz_assets", 2028, col="value"), -2900)

    def test_vat_proxy_tier_and_cost(self):
        f = run("vat_minus2")["frame"]
        m = f[f.engine == "micro"]
        self.assertTrue((m.tier == "D").all())
        self.assertLess(val(f, "cpi", 2027), 0)
        self.assertGreater(val(f, "fiscal_cost", 2027, col="value"), 300)

    def test_min_wage_budget_cost_and_caveat(self):
        f = run("mw20_2027")["frame"]
        c = val(f, "fiscal_cost", 2027, col="value")
        self.assertTrue(50 < c < 400, c)
        m = f[(f.engine == "micro") & (f.indicator == "gdp_real")]
        self.assertTrue(m.note_az.str.contains("qeyri-formallaşma").all())

    def test_pension_costs_budget(self):
        f = run("pension10_2027")["frame"]
        self.assertLess(val(f, "budget_balance", 2028, col="delta"), 0)


class TestLongRunAndComparison(unittest.TestCase):
    def test_longrun_years_and_label(self):
        f = run("pubinv1bn_deficit")["frame"]
        lr = f[f.engine == "longrun"]
        self.assertEqual(lr.year.min(), 2031)
        self.assertTrue(lr.method.str.contains("struktur ekstrapolyasiya").all())
        self.assertTrue((lr[lr.year >= 2031].horizon == "uzun").all())

    def test_method_comparison_two_methods(self):
        r = run("polrate_m100")
        n = integrate.method_comparison(r["frame"], {"polrate_m100": r["scenario"]})
        g = n[(n.indicator == "gdp_real")]
        self.assertTrue(len(g) >= 2)
        self.assertTrue(g.methods.str.contains("caem").all())
        self.assertTrue(g.explanation_az.str.len().gt(20).all())

    def test_profit_tax_headline_from_core_proxy(self):
        h = integrate.headline(run("profit_tax_minus2")["frame"])
        self.assertTrue((h.source_engine == "micro").all())        # C1: MicroUnit proxy is the core method
        self.assertTrue(h.tier.str.contains("D").all())


class TestKpi(unittest.TestCase):
    def test_scores_and_ranking(self):
        import pandas as pd
        p1 = pd.concat([run(s)["frame"] for s in ("mw20_2027", "pubinv1bn_deficit", "vat_minus2")])
        v, r = kpi.compute(p1)
        self.assertEqual(len(r), 3)
        self.assertTrue(r.score.between(0, 1).all())
        self.assertEqual(list(r["rank"]), [1, 2, 3])
        self.assertGreaterEqual(v.kpi.nunique(), 5)

    def test_external_inputs_argument(self):
        import pandas as pd
        p1 = pd.concat([run(s)["frame"] for s in ("mw20_2027", "vat_minus2")])
        ids = ["gdp_short", "gdp_medium", "inflation_short", "unemployment", "fiscal_cost", "side_effects"]
        ext = pd.DataFrame({"scenario": ["mw20_2027", "vat_minus2"], "kpi": ["side_effects"] * 2, "value": [3, 1]})
        v, _ = kpi.compute(p1, ids, ext=ext)
        se = v[v.kpi == "side_effects"].set_index("scenario")
        self.assertEqual(se.loc["mw20_2027", "value"], 3.0)
        self.assertEqual(se.loc["vat_minus2", "norm"], 1.0)          # fewer side effects = better
        v2, _ = kpi.compute(p1, ids, ext={("mw20_2027", "side_effects"): 5.0})
        self.assertEqual(v2[(v2.kpi == "side_effects") & (v2.scenario == "mw20_2027")]["value"].iloc[0], 5.0)


if __name__ == "__main__":
    unittest.main()
