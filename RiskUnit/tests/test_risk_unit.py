"""Acceptance tests for MİİS §15.5.3 — one block per FR/NFR acceptance criterion of the TT,
plus self-checks of the statistical core. Run after `python3 run_all.py`:

    python3 -m unittest discover -s tests -v
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from riskunit import backtest, config, factors, measures, simulate  # noqa: E402

OUT = config.OUTPUT


class FR1_RiskFactors(unittest.TestCase):
    """≥ 3 categories (financial, external-political, natural); P and I computed for every risk;
    transmission channels of political events and natural disasters identified."""

    def test_categories(self):
        fam = set(factors.register()["aile"])
        self.assertTrue({"MAL", "XSI", "TEB"} <= fam, fam)

    def test_probability_and_impact_for_every_risk(self):
        S = pd.read_csv(OUT / "FR2_risk_scores.csv")
        self.assertEqual(set(S["risk_id"]), set(factors.register()["risk_id"]))
        self.assertTrue(S["ehtimal"].between(0, 1).all())
        self.assertTrue(S[["tesir_g", "tesir_cpi", "tesir_fis"]].notna().all().all())

    def test_indicator_base_and_channels(self):
        I = pd.read_csv(OUT / "FR1_indicator_base.csv")
        self.assertTrue({"MAL", "XSI", "TEB", "DAX", "SEK"} <= set(I["aile"]))
        C = pd.read_csv(OUT / "FR1_transmission_channels.csv")
        for k in ("gpr_brent_lp", "partner_gpr", "remit_gpr", "agri_spi", "inv_brent"):
            self.assertIn(k, set(C["kanal"]), k)

    def test_event_chronology_is_data_coded(self):
        E = pd.read_csv(OUT / "FR1_event_chronology.csv")
        self.assertGreaterEqual(len(E), 10)
        self.assertTrue(E["gpr_qlobal_nisbet"].notna().mean() > 0.8)


class FR2_Prioritisation(unittest.TestCase):
    """risk score = probability × impact; automatic ranking; alerts for high priority."""

    def setUp(self):
        self.S = pd.read_csv(OUT / "FR2_risk_scores.csv")

    def test_score_is_product(self):
        self.assertTrue((self.S["skor"] == self.S["P_bal"] * self.S["I_bal"]).all())

    def test_sorted(self):
        self.assertTrue(self.S["skor"].is_monotonic_decreasing)
        self.assertEqual(list(self.S["sira"]), list(range(1, len(self.S) + 1)))

    def test_alert_for_each_high_priority_risk(self):
        A = pd.read_csv(OUT / "FR2_alerts.csv")
        high = set(self.S[self.S["prioritet"] == "yüksək"]["risk_id"])
        alerted = set(A[A["tip"] == "yüksək prioritet"]["risk_id"])
        self.assertEqual(high, alerted)

    def test_euler_decomposition_is_exact(self):
        r = simulate.run(n=3000, seed=7)
        tot = r.total("g")
        recon = r.base["g"][None, :] + sum(r.comp_g.values())
        np.testing.assert_allclose(tot, recon)
        C = simulate.contributions(r, "g")
        self.assertAlmostEqual(C["dispersiya_payi"].sum(), 1.0, places=6)

    def test_convolution_reproduces_step(self):
        step = np.array([0.2, 0.25, 0.3, 0.32, 0.33])
        out = simulate._convolve(np.ones((1, 5)), step)
        np.testing.assert_allclose(out[0], step)


class FR3_Measures(unittest.TestCase):
    """At least one mitigating measure per risk; status tracking."""

    def test_every_risk_has_a_measure(self):
        cov = measures.coverage(measures.load())
        self.assertTrue((cov["tedbir_sayi"] >= 1).all(), cov[cov["tedbir_sayi"] < 1])
        self.assertEqual(cov.attrs["unknown_links"], [])

    def test_register_fields_valid(self):
        m = measures.load()
        self.assertTrue((m["yoxlama"] == "ok").all(), m[m["yoxlama"] != "ok"][["tedbir_id", "yoxlama"]])
        for col in ("tedbir", "mesul", "muddet", "status"):
            self.assertTrue(m[col].str.len().gt(0).all(), col)

    def test_status_change_is_tracked(self):
        tmp = Path(tempfile.mkdtemp())
        old = measures.STATUS_HISTORY
        try:
            measures.STATUS_HISTORY = tmp / "h.csv"
            m = measures.load()
            measures.track_status(m)
            m2 = m.copy()
            m2.loc[0, "status"] = "icrada"
            h = measures.track_status(m2)
            last = h[h["tedbir_id"] == m.loc[0, "tedbir_id"]].iloc[-1]
            self.assertEqual(last["status"], "icrada")
            self.assertEqual(last["evvelki_status"], m.loc[0, "status"])
        finally:
            measures.STATUS_HISTORY = old
            shutil.rmtree(tmp)

    def test_stress_and_analogues(self):
        st = pd.read_csv(OUT / "FR3_stress_scenarios.csv")
        self.assertGreaterEqual(st["ssenari"].nunique(), 6)
        A = pd.read_csv(OUT / "FR3_historical_analogues.csv")
        self.assertLess(np.sqrt((A["xeta"] ** 2).mean()), np.sqrt((A["faktiki_sapma"] ** 2).mean()))


class FR4_DecisionSupport(unittest.TestCase):
    """Executive panel exists; report exportable to PDF and Excel."""

    def test_exports(self):
        for role in ("rehberlik", "analitik"):
            for ext in ("pdf", "xlsx"):
                f = config.REPORTS / f"risk_hesabati_{role}.{ext}"
                self.assertTrue(f.exists() and f.stat().st_size > 10_000, f)
        self.assertIn("Risk xəritəsi", (config.SITE / "index.html").read_text(encoding="utf-8"))

    def test_api(self):
        api = json.loads((OUT / "risk_api.json").read_text(encoding="utf-8"))
        for k in ("indicator_time_series", "scenario", "forecast_result", "risk_register", "policy_measure", "alerts"):
            self.assertIn(k, api)
            self.assertTrue(len(api[k]) > 0, k)


class NFR1_Backtesting(unittest.TestCase):
    """Backtest vs a simple benchmark, real-time data, separate distribution tests, quarterly register."""

    def test_register_has_current_quarter_with_all_test_families(self):
        R = pd.read_csv(backtest.REGISTER)
        cur = R[R["rub"] == backtest.quarter()]
        self.assertTrue(len(cur))
        fams = {t[0] for t in cur["test_id"]}
        self.assertTrue({"D", "P", "E", "R"} <= fams, fams)
        self.assertTrue(cur["melumat_bazasi"].str.startswith("real vaxt").any())

    def test_kupiec_zero_at_nominal_rate(self):
        b = np.zeros(100, bool)
        b[:10] = True
        lr, p = backtest.kupiec(b, 0.10)
        self.assertAlmostEqual(lr, 0.0, places=8)
        self.assertAlmostEqual(p, 1.0, places=6)

    def test_pit_tests_have_correct_size_and_power(self):
        """Calibrated forecasts: rejection rate near 5 %; overdispersed forecasts: rejected."""
        rng = np.random.default_rng(1)
        from scipy import stats
        rej_ks = np.mean([backtest.ks_uniform(stats.norm.cdf(rng.standard_normal(60)))[1] < 0.05 for _ in range(200)])
        rej_bk = np.mean([backtest.berkowitz(stats.norm.cdf(rng.standard_normal(60)))[1] < 0.05 for _ in range(200)])
        self.assertLess(rej_ks, 0.12)
        self.assertLess(rej_bk, 0.12)
        wide = stats.norm.cdf(0.4 * rng.standard_normal(200))          # fan twice too wide
        self.assertLess(backtest.berkowitz(wide)[1], 0.01)

    def test_christoffersen_detects_clustering(self):
        b = np.array([0] * 40 + [1] * 10 + [0] * 50, bool)
        self.assertLess(backtest.christoffersen(b, 0.10)["p_ind"], 0.01)

    def test_auroc(self):
        self.assertAlmostEqual(backtest.auroc([0.9, 0.8, 0.1], [1, 1, 0]), 1.0)

    def test_calibration_feeds_simulation(self):
        C = pd.read_csv(OUT / "NFR1_calibration.csv")
        f = simulate.calibration_factors()
        for r in C.itertuples():
            self.assertAlmostEqual(f[r.hedef], r.miqyas, places=6)


class NFR2_Adaptation(unittest.TestCase):
    """Scores recomputed within 24 h of new data; changed inputs are detected."""

    def test_last_update_within_sla(self):
        U = pd.read_csv(OUT / "NFR2_update_log.csv")
        ok = U[U["status"] == "uğurlu"]
        self.assertTrue(len(ok))
        self.assertLessEqual(float(ok["sla_saat"].iloc[-1]), 24.0)

    def test_fingerprint_detects_register_change(self):
        import update
        tmp = Path(tempfile.mkdtemp())
        old = config.INPUT
        try:
            shutil.copytree(old, tmp / "input")
            config.INPUT = tmp / "input"
            a = update.fingerprint()
            p = config.INPUT / "tedbirler_reyestri.csv"
            p.write_text(p.read_text(encoding="utf-8").replace("təklif", "təsdiqlənib", 1), encoding="utf-8")
            b = update.fingerprint()
            self.assertEqual([k for k in a if a[k] != b[k]], ["giriş:tedbirler_reyestri.csv"])
        finally:
            config.INPUT = old
            shutil.rmtree(tmp)


class NFR3_RoleBasedReports(unittest.TestCase):
    """Different level of detail by user role."""

    def test_roles_differ(self):
        reh = (config.SITE / "index.html").read_text(encoding="utf-8")
        ana = (config.SITE / "analitik.html").read_text(encoding="utf-8")
        self.assertNotIn('id="backtest"', reh)
        self.assertIn('id="backtest"', ana)
        self.assertGreater(len(ana), len(reh))
        from openpyxl import load_workbook
        n_reh = len(load_workbook(config.REPORTS / "risk_hesabati_rehberlik.xlsx", read_only=True).sheetnames)
        n_ana = len(load_workbook(config.REPORTS / "risk_hesabati_analitik.xlsx", read_only=True).sheetnames)
        self.assertGreater(n_ana, n_reh)


class Consistency(unittest.TestCase):
    """The risk unit publishes no central path of its own: baselines are the upstream models'."""

    def test_baseline_matches_macro(self):
        D = pd.read_csv(OUT / "FR2_distribution.csv")
        from riskunit import spine
        B = spine.baseline()
        g = D[D["gosterici"] == "g"].set_index("il")["baza"]
        np.testing.assert_allclose(g.values, B["nonoil_realg"].reindex(g.index).values)

    def test_every_output_carries_baseline_id(self):
        for f in ("FR2_distribution.csv", "FR2_risk_scores.csv", "FR2_alerts.csv"):
            self.assertIn("baseline_id", pd.read_csv(OUT / f).columns, f)


if __name__ == "__main__":
    unittest.main(verbosity=2)
