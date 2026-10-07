"""Review fixes C1–C7 (offline): CAEM tax-fiscal flag + second method for profit tax, per-instrument
financing, pension indexation cost, continuous long-run splice, fuel revenue channel, RiskUnit FX headline."""
import os
import sys
import unittest
from pathlib import Path

os.environ["POLICY_NO_NETWORK"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hermetic  # noqa: E402,F401  (temp work/ and output/)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policyunit import compare, eng_micro, fiscal, integrate, kpi, ranges, scenario as scn  # noqa: E402

_C = {}


def run(s, engines=None):
    key = (s if isinstance(s, str) else s["id"], tuple(engines or ()))
    if key not in _C:
        _C[key] = integrate.run_scenario(scn.load(s) if isinstance(s, str) else s, engines)
    return _C[key]


def d(f, eng, ind, year, col="delta"):
    g = f[(f.engine == eng) & (f.indicator == ind) & (f.year == year)]
    return float(g[col].iloc[0])


class TestC1(unittest.TestCase):
    def test_profit_tax_has_two_methods_and_caem_fiscal_flagged(self):
        r = run("profit_tax_minus2")
        f = r["frame"]
        self.assertIn("micro", set(f.engine))
        self.assertGreater(d(f, "micro", "fiscal_cost", 2028, "value"), 300)
        self.assertGreater(d(f, "micro", "exports_nonoil_real", 2028, "delta") + d(f, "micro", "gdp_real", 2028), 0)
        cf = f[(f.engine == "caem") & (f.group == "fiskal") & (f.indicator != "fiscal_cost")]
        self.assertTrue(cf.note_az.str.contains("ETİBARSIZ").all())
        n = integrate.method_comparison(f, {"profit_tax_minus2": r["scenario"]})
        self.assertTrue((n.indicator == "gdp_real").any())
        h = integrate.headline(f)
        self.assertFalse(h[h.indicator.isin(["debt_pct", "budget_balance_pct"])].source_engine.eq("caem").any())


class TestC2(unittest.TestCase):
    def test_mixed_financing_per_instrument(self):
        base = {"id": "mixfin", "name_az": "x", "start_year": 2026}
        mix = scn.normalise(dict(base, instruments=[
            {"instrument": "pub_invest", "years": [2026, 2027], "size": 500, "financing": "sofaz"},
            {"instrument": "vat_rate", "years": [2026, 2027], "size": -1, "financing": "deficit"}]))
        vat = scn.normalise(dict(base, id="vatonly", instruments=[
            {"instrument": "vat_rate", "years": [2026, 2027], "size": -1, "financing": "deficit"}]))
        m = eng_micro.plan(mix)
        self.assertGreater(m["sofaz"][0], 499)
        self.assertAlmostEqual(m["fin_tax"][0], 0.0)
        fm, fv = eng_micro.run(mix).frame, eng_micro.run(vat).frame
        dm = fm[(fm.indicator == "debt") & (fm.year == 2027)].delta.iloc[0]
        dv = fv[(fv.indicator == "debt") & (fv.year == 2027)].delta.iloc[0]
        self.assertLess(abs(dm - dv), 300)          # SOFAZ part adds (almost) no debt
        self.assertLess(fm[(fm.indicator == "sofaz_assets") & (fm.year == 2027)].value.iloc[0], -990)


class TestC3C6(unittest.TestCase):
    def test_pension_indexation_costed(self):
        f = run("mw20_2027", ["micro"])["frame"]
        ov = run("mw20_2027", ["micro"])["results"]["micro"].meta["overlay"]
        self.assertGreater(ov["pension_correction"][2], 100)
        self.assertLess(d(f, "micro", "budget_balance", 2030), 400)

    def test_pension_base_reconciled(self):
        self.assertLess(fiscal.base_value("pension_spending", 2026), fiscal.base_value("dsmf_spending", 2026))

    def test_ranges_and_microsim_note(self):
        self.assertIn("İSTİFADƏ ETMİR", compare.REASON[("microsim", "labour")])
        r = run("mw20_2027")
        n2 = integrate.method_comparison(r["frame"], {"mw20_2027": r["scenario"]})
        rg = ranges.table(n2, {"mw20_2027": r["scenario"]}, r["frame"])
        w = rg[rg.indicator == "wage_nominal"]
        self.assertTrue(len(w))
        self.assertTrue((w.low < w.high).all())
        self.assertTrue(w.methods.str.contains("microsim_spill").any())


class TestC4(unittest.TestCase):
    def test_longrun_continuity(self):
        for sid in ("fx_deval10", "pubinv1bn_deficit", "vat_minus2"):
            c = ranges.continuity(run(sid)["frame"])
            self.assertTrue(c.ok.all(), (sid, c[~c.ok].to_dict("records")))


class TestC7(unittest.TestCase):
    def test_fuel_raises_revenue(self):
        f = run("fuel_dereg20", ["micro"])["frame"]
        self.assertLess(d(f, "micro", "fiscal_cost", 2027, "value"), -100)

    def test_fx_headline_cpi_from_riskunit(self):
        h = integrate.headline(run("fx_deval10")["frame"])
        g = h[(h.indicator == "cpi") & (h.horizon == "qısa")]
        self.assertEqual(g.source_engine.iloc[0], "riskfx")


class TestKpiMissing(unittest.TestCase):
    def test_missing_flagged(self):
        import pandas as pd
        p1 = pd.concat([run(s, ["micro"])["frame"] for s in ("mw20_2027", "vat_minus2")])
        ids = ["gdp_short", "gdp_medium", "inflation_short", "unemployment", "fiscal_cost", "gini"]
        _, r = kpi.compute(p1, ids, ext={})
        self.assertTrue((~r.complete).all())
        self.assertTrue(r.note_az.str.contains("hesablanmayıb").all())


if __name__ == "__main__":
    unittest.main()


class TestVerification(unittest.TestCase):
    def test_kpi_uses_headline_source_for_fx_cpi(self):
        f = run("fx_deval10")["frame"]
        h = integrate.headline(f)
        hv = h[(h.indicator == "infl") & (h.horizon == "qısa")].effect.iloc[0]
        v, _ = kpi.compute(f, ["gdp_short", "gdp_medium", "inflation_short", "unemployment", "fiscal_cost"], ext={})
        self.assertAlmostEqual(v[v.kpi == "inflation_short"].value.iloc[0], hv, places=3)

    def test_ranges_exclude_unreliable_caem(self):
        r = run("profit_tax_minus2")
        n2 = integrate.method_comparison(r["frame"], {"profit_tax_minus2": r["scenario"]})
        rg = ranges.table(n2, {"profit_tax_minus2": r["scenario"]}, r["frame"])
        fis = rg[rg.indicator.isin(["budget_balance_pct", "debt_pct"])]
        self.assertFalse(fis.methods.str.contains("caem").any())
        self.assertTrue(fis.excluded_az.str.contains("ETİBARSIZ").all() if len(fis) else True)

    def test_disagreement_kpi_and_conservative_rank(self):
        import pandas as pd
        rs = {s: run(s) for s in ("mw20_2027", "vat_minus2", "polrate_m100")}
        p1 = pd.concat([x["frame"] for x in rs.values()])
        n2 = integrate.method_comparison(p1, {k: x["scenario"] for k, x in rs.items()})
        rg = ranges.table(n2, {k: x["scenario"] for k, x in rs.items()}, p1)
        ids = ["gdp_short", "gdp_medium", "inflation_short", "unemployment", "fiscal_cost", "model_disagreement"]
        v, r = kpi.compute(p1, ids, ext={}, rg=rg)
        d = v[v.kpi == "model_disagreement"].set_index("scenario").value
        self.assertGreater(d["mw20_2027"], d["polrate_m100"])
        self.assertIn("rank_conservative", r.columns)

    def test_merge_mode_keeps_other_scenarios(self):
        from policyunit import config, outputs
        outputs.write_all(["polrate_m100", "tsa_plus30"], log=lambda *_: None)
        outputs.write_all(["polrate_m100"], log=lambda *_: None)
        import pandas as pd
        p1 = pd.read_csv(config.OUTPUT / "P1_effects.csv")
        self.assertEqual(set(p1.scenario), {"polrate_m100", "tsa_plus30"})
        self.assertEqual(len(p1[p1.scenario == "polrate_m100"].drop_duplicates()), len(p1[p1.scenario == "polrate_m100"]))

    def test_vintage_ids_recorded(self):
        from policyunit import freshness
        v = freshness.current()
        for k in ("micro_vintage", "caem_md5", "oxlon_forecast_long_md5", "io_table", "riskunit_baseline_id"):
            self.assertIn(k, v)
