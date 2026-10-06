"""v2 core simulation / integration tests (offline): two views, centring, fiscal-reaction fix, stress signs,
bands, NFR1 honesty, register v2 and the run summary.  RISK_NO_NETWORK=1 python3 -m unittest discover -s tests"""
import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from riskunit import backtest, config, factors, scoring, simulate, spine  # noqa: E402

OUT = config.OUTPUT
_CACHE = {}


def sim(view="baseline", n=4000, **kw):
    key = (view, n, tuple(sorted(kw.items())) if kw else None)
    if kw:
        return simulate.run(n=n, seed=11, view=view, **kw)
    if key not in _CACHE:
        _CACHE[key] = simulate.run(n=n, seed=11, view=view)
    return _CACHE[key]


class Views(unittest.TestCase):
    def test_baseline_view_median_equals_official_baseline(self):
        """v2.1: median = official baseline for every year after the running one; the running year = YTD nowcast."""
        r = sim("baseline")
        for kind in ("g", "cpi", "fis"):
            np.testing.assert_allclose(np.median(r.total(kind), axis=0), r.meta["targets"][kind], atol=1e-6, err_msg=kind)
            np.testing.assert_allclose(r.meta["targets"][kind][1:], r.base[kind][1:], atol=1e-9, err_msg=kind)
        np.testing.assert_allclose(r.meta["brent_centre"][1:], r.brent_base[1:])

    def test_live_view_median_is_baseline_plus_live_gap_response_only(self):
        r = sim("live")
        for kind in ("g", "cpi", "fis"):
            np.testing.assert_allclose(np.median(r.total(kind), axis=0), r.meta["targets"][kind], atol=1e-6, err_msg=kind)
            np.testing.assert_allclose(r.meta["targets"][kind][1:], (r.base[kind] + r.meta["live_shift"][kind])[1:],
                                       atol=1e-9, err_msg=kind)
        self.assertEqual(r.meta["view"], "live")

    def test_high_live_brent_does_not_worsen_the_budget(self):
        """v1 defect: live Brent ≫ baseline dragged the median 2027 balance to −2,7 % GDP."""
        r = sim("live")
        j = r.col(r.score_year)
        if r.meta["brent_centre"][j] > r.brent_base[j]:
            self.assertGreaterEqual(r.meta["live_shift"]["fis"][j], 0.0)

    def test_distribution_files_label_views(self):
        self.assertEqual(set(pd.read_csv(OUT / "FR2_distribution.csv")["baxis"]), {"baseline"})
        self.assertEqual(set(pd.read_csv(OUT / "FR2_distribution_live.csv")["baxis"]), {"live"})

    def test_bad_view_rejected(self):
        with self.assertRaises(ValueError):
            simulate.run(n=10, view="mine")


class FiscalReaction(unittest.TestCase):
    def test_reaction_is_balance_neutral_without_T09(self):
        r = sim("baseline")
        self.assertEqual(float(np.abs(r.comp_fis["fiscal_react"]).max()), 0.0)

    def test_T09_floor_has_a_fiscal_cost(self):
        r = sim("baseline", n=3000, overrides={"fiscal_react_floor": True})
        self.assertLessEqual(float(r.comp_fis["fiscal_react"].max()), 1e-12)
        self.assertLess(float(r.comp_fis["fiscal_react"].min()), 0.0)

    def test_fr1_embedded_elasticity_is_removed(self):
        e = simulate.fr1_embedded_inv_elasticity(spine.multipliers(), spine.baseline()["brent_usd"].to_numpy())
        self.assertTrue(0.0 < e < 1.0, e)
        ch = factors.channels()
        self.assertLess(ch[("inv_brent", "dln_brent")]["coef"], 0.80)      # v1 (with the 2005–06 splice): 0.80

    def test_low_oil_worsens_balance_and_growth(self):
        T = len(config.FORECAST_YEARS)
        neutral = {"deterministic": True, "spi": [0.0] * T, "quake_damage": [0.0] * T, "remit_dev": [0.0] * T,
                   "partner_dev": [0.0] * T, "lend_dev": [0.0] * T}
        base = list(spine.baseline()["brent_usd"])
        lo = simulate.run(n=200, overrides={**neutral, "brent_path": [base[0]] + [45.0] * (T - 1)})
        ref = simulate.run(n=200, overrides={**neutral, "brent_path": base})
        for kind in ("g", "fis", "cpi"):
            d = np.median(lo.total(kind), axis=0) - np.median(ref.total(kind), axis=0)
            self.assertLess(d[1], 0.0, kind)


class StressSigns(unittest.TestCase):
    def test_stored_stress_set_has_sensible_signs(self):
        st = pd.read_csv(OUT / "FR3_stress_scenarios.csv")
        bad = simulate.check_stress_signs(st)
        self.assertTrue(bad.empty, bad.to_string())

    def test_sign_check_catches_the_v1_defect(self):
        st = pd.DataFrame([{"ssenari": "S1", "gosterici": "büdcə balansı, % ÜDM", "il": 2027, "sapma": 0.45}])
        self.assertEqual(len(simulate.check_stress_signs(st, year=2027)), 1)


class Bands(unittest.TestCase):
    def test_total_sigma_matches_calibrated_fan(self):
        r = sim("baseline")
        for kind, lay in r.meta["layering"].items():
            np.testing.assert_allclose(lay["sig_total"], np.maximum(lay["sig_target"], lay["sig_factors"]),
                                       rtol=0.10, err_msg=kind)

    def test_fiscal_calibration_row(self):
        C = pd.read_csv(OUT / "NFR1_calibration.csv")
        self.assertIn("fis", set(C["hedef"]))
        self.assertTrue(C["n"].notna().all())


class NFR1Honesty(unittest.TestCase):
    def test_verdict_never_passes_on_n0(self):
        self.assertEqual(backtest.verdict(True, 0), "yoxlanıla bilmir (n=0)")
        self.assertEqual(backtest.verdict(None, 3), "yoxlanıla bilmir (n=3)")
        self.assertEqual(backtest.verdict(True, 5), "keçdi")

    def test_register_reports_n_and_no_default_pass(self):
        R = pd.read_csv(backtest.REGISTER)
        cur = R[R["rub"] == backtest.quarter()]
        self.assertTrue(cur["n"].notna().all())
        self.assertFalse(((cur["n"] == 0) & (cur["netice"] == "keçdi")).any())
        self.assertIn("yoxlanıla bilmir", " ".join(cur[cur["test_id"] == "R1"]["netice"]) or "yoxlanıla bilmir")


class RegisterV2(unittest.TestCase):
    def test_new_risks(self):
        reg = factors.register().set_index("risk_id")
        for rid in ("R17", "R18", "R19"):
            self.assertIn(rid, reg.index)
            self.assertTrue(str(reg.at[rid, "sahib"]).strip())
            self.assertTrue(str(reg.at[rid, "caem_kateqoriya"]).strip())
        self.assertTrue(reg.at["R17", "caem_kateqoriya"].startswith("Import prices"))
        self.assertTrue(reg.at["R18", "caem_kateqoriya"].startswith("Food prices"))

    def test_new_risks_are_scored(self):
        S = pd.read_csv(OUT / "FR2_risk_scores.csv").set_index("risk_id")
        for rid in ("R17", "R18", "R19"):
            self.assertTrue(0 <= S.at[rid, "ehtimal"] <= 1, rid)
        r = sim("baseline")
        self.assertIn("R17", r.events)
        self.assertTrue(0.0 < r.events["R17"][:, 1].mean() < 0.6)

    def test_model_risk_reads_d3(self):
        m = scoring.model_risk(config.score_year())
        self.assertTrue(0.0 <= m["ehtimal"] <= 1.0)


class RunSummary(unittest.TestCase):
    def test_summary(self):
        p = OUT / "_run_summary_v2.json"
        self.assertTrue(p.exists())
        s = json.loads(p.read_text(encoding="utf-8"))
        self.assertTrue(s["baseline_id"].startswith("B-"))
        self.assertTrue(all({"stage", "status", "seconds"} <= set(r) for r in s["merheleler"]))
        self.assertIn("baza_merkezli", s["bashliq"])
        self.assertIn("canli", s["bashliq"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
