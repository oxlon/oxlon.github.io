"""v2.1 core-transmission fixes (audit C1–C3, M1–M3, M6, minors) — offline."""
import os
import unittest

import numpy as np

os.environ.setdefault("RISK_NO_NETWORK", "1")

from riskunit import config, factors, fx, measures, scalability as sc, scoring, simulate  # noqa: E402

YRS = config.FORECAST_YEARS
_SIM = {}


def sim(view="baseline", n=4000):
    if view not in _SIM:
        _SIM[view] = simulate.run(n=n, seed=3, view=view)
    return _SIM[view]


class FXModule(unittest.TestCase):
    def test_calibration_matches_2015_17(self):
        c = fx.calibration()
        self.assertTrue(0.22 <= c["pt"] <= 0.36, c["pt"])            # cumulative pass-through ≈ 0,25–0,3
        self.assertTrue(0.5 <= c["w0"] <= 0.8)
        self.assertLess(c["L"], 0.0)                                  # devaluation lowers non-oil output
        self.assertAlmostEqual(c["p_dev"], 1 / 3, places=6)          # 2015–16 is ONE episode

    def test_two_year_cpi_and_overlay_no_double_count(self):
        x = np.full(len(YRS), 100 * np.log(1.165))
        t, ch, o = fx.responses(x), fx.chain_part(x), fx.overlay(x)
        self.assertGreater(t["cpi"][0, 0], 0)
        self.assertGreater(t["cpi"][0, 1], 0)
        np.testing.assert_allclose(t["cpi"][0, 2:], 0, atol=1e-12)
        for k in ("cpi", "nonoil_lvl", "debt_gdp"):
            np.testing.assert_allclose(ch[k] + o[k], t[k], atol=1e-9)  # chain + overlay = calibrated total
        self.assertGreater(t["debt_gdp"][0, 0], 0)

    def test_simulation_devaluation_uses_fx_module(self):
        T = len(YRS)
        neutral = measures.neutral_overrides()
        a = simulate.run(n=50, overrides={**neutral, "deval_year": YRS[1]})
        x = np.zeros(T)
        x[1:] = 100 * np.log1p(factors.params()["devaluation_size"])
        np.testing.assert_allclose(np.median(a.comp_cpi["deval"], axis=0), fx.responses(x)["cpi"][0], atol=0.6)
        self.assertGreater(a.comp_cpi["deval"][:, 2].mean(), 0)      # second-year pass-through exists


class ImpulseShocks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.D = sc.factor_data()
        cls.S = sc.factor_specs(cls.D)
        cls.base, _ = sc.run_chain({}, "t-base")

    def d(self, f, k):
        ov, _ = self.S[f]["build"](k)
        fl, _ = sc.run_chain(ov, f)
        return sc.derived_delta(self.base, fl, self.D["rgdpnon_2025"])

    def test_cost_shocks_are_not_permanent(self):
        j = YRS.index(config.score_year())
        for f in ("food", "import", "costpush"):
            dd = self.d(f, 1.0)
            self.assertGreater(dd[("ru:cpi", YRS[j])], 0.1, f)
            self.assertAlmostEqual(dd[("ru:cpi", YRS[0])], 0.0, places=6)
            self.assertLess(abs(dd[("ru:cpi", YRS[-1])]), 0.05, f)   # v2.0: +3,7 pp in every year

    def test_quake_event_year_is_negative(self):
        j = YRS.index(config.score_year())
        dd = self.d("quake", 3.0)
        self.assertLess(dd[("ru:nonoil_lvl", YRS[j])], 0.0)

    def test_fx_factor_includes_overlay(self):
        dd = self.d("fx", 1.0)
        j = YRS.index(config.score_year())
        self.assertLess(dd[("ru:nonoil_lvl", YRS[j + 1])], -0.5)
        self.assertGreater(dd[("ru:debt_gdp", YRS[j])], 0.0)

    def test_effect_metric_near_zero_base(self):
        e, u = sc.effect("level", "mln AZN", 1.0, 500.0, gdp=130000.0)
        self.assertEqual(u, "% ÜDM (f.b.)")
        self.assertLess(abs(e), 1.0)
        self.assertIs(sc._head_rows, sc.head_rows)


class RunningYearAndBands(unittest.TestCase):
    def test_running_year_conditioned_in_both_views(self):
        for view in ("baseline", "live"):
            r = sim(view)
            ry = r.meta["nowcast"]
            if "g_ytd" not in ry:
                self.skipTest("no DSK nowcast in the cache")
            d = simulate.distribution_table(r)
            g = d[(d.gosterici == "g") & (d.il == YRS[0])].iloc[0]
            self.assertLessEqual(g["p05"], ry["g_ytd"] + 1e-9, view)
            b = d[(d.gosterici == "brent") & (d.il == YRS[0])].iloc[0]
            self.assertGreater(b["p50"], 0.6 * ry["brent_ytd"])

    def test_cpi_lower_tail_bounded(self):
        x = sim().total("cpi")
        self.assertGreater(np.quantile(x[:, 1:], 0.05, axis=0).min(), 0.0)

    def test_r18_food_channel_material(self):
        S = scoring.score(sim())
        r18 = S[S.risk_id == "R18"].iloc[0]
        self.assertGreater(r18["tesir_cpi"], 0.25)                   # v2.0: 0,015 pp

    def test_r19_outside_heat_map(self):
        S = scoring.score(sim())
        r = S[S.risk_id == "R19"].iloc[0]
        self.assertEqual(int(r["P_bal"]), 0)
        self.assertNotIn("R19", ";".join(scoring.heatmap(S)["riskler"]))
        T = scoring.model_risk_table(sim())
        if len(T):
            self.assertFalse(T["menbeler"].str.contains("caem").any())

    def test_stress_vector_matches_named_set(self):
        T = len(YRS)
        v = measures.stress_vector({"partner_dev": [0, -3.0, -1.5] + [0] * (T - 3)}, with_measures=False, n=200)
        g = v[(v.kind == "g") & (v.il == YRS[1])]["sapma"].iloc[0]
        self.assertLess(g, 0.0)


if __name__ == "__main__":
    unittest.main()


class Followups20261007(unittest.TestCase):
    def test_fx_fiscal_and_debt_revaluation(self):
        c = fx.calibration()
        x = np.full(len(YRS), 100 * np.log(1.165))
        r = fx.responses(x)
        self.assertAlmostEqual(float(r["debt_gdp"][0, 0]), c["s_ext"] * c["debt_gdp"] * 0.165, places=6)
        self.assertLess(float(r["fis_interest"][0, 0]), 0.0)
        np.testing.assert_allclose(fx.chain_part(x)["debt_gdp"], 0.0)      # FR1 does not revalue the debt stock

    def test_s3_fiscal_differs_from_s1(self):
        T = len(YRS)
        c = measures.stress_centre()
        s1 = measures.stress_vector({"brent_path": [c[0]] + [45.0] * (T - 1)}, with_measures=False, n=200)
        s3 = measures.stress_vector({"brent_path": [c[0]] + [45.0] * (T - 1), "deval_year": YRS[1]}, with_measures=False, n=200)
        f1, f3 = (v[v.kind == "fis"]["sapma"].to_numpy() for v in (s1, s3))
        self.assertLess(f3[2], f1[2])

    def test_minwage_row_and_base_label(self):
        from riskunit import monitor
        D5 = monitor.daily_monitor(YRS[0])
        if monitor.MINWAGE_FILE.exists():
            self.assertTrue((D5["indicator"] == "minwage").any())
        d = simulate.distribution_table(sim())
        self.assertIn("baza_izah", d.columns)
        self.assertIn("merkez", d.columns)
