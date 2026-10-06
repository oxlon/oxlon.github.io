"""Offline tests of the Capital-at-Risk layer (dsa, car). unittest- and pytest-compatible.

    RISK_NO_NETWORK=1 python3 -m unittest tests.test_car -v
"""
import os
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["RISK_NO_NETWORK"] = "1"

from riskunit import car, config, dsa  # noqa: E402

OUT = config.OUTPUT
YEARS = config.FORECAST_YEARS


def _toy_engine(fis_row, n=3):
    T = len(YEARS)
    V1 = pd.DataFrame([
        {"kod": "debt_public_total", "mln_azn": 1000.0, "mln_usd": 1000 / 1.7, "deyer": 1000.0, "pay_faiz": None},
        {"kod": "debt_external", "mln_azn": 330.0, "mln_usd": 330 / 1.7, "deyer": 330 / 1.7, "pay_faiz": None},
        {"kod": "debt_floating_total", "mln_azn": None, "mln_usd": None, "deyer": 0.0, "pay_faiz": 0.0},
        {"kod": "cl_guaranteed_total", "mln_azn": 100.0, "mln_usd": 100 / 1.7, "deyer": 100.0, "pay_faiz": None},
        {"kod": "bank_loans", "mln_azn": 0.0, "mln_usd": 0.0, "deyer": 0.0, "pay_faiz": None},
        {"kod": "bank_capital", "mln_azn": 0.0, "mln_usd": 0.0, "deyer": 0.0, "pay_faiz": None}])
    zero = pd.DataFrame(0.0, index=range(n), columns=["ust2", "fx_eur", "fx_jpy", "fx_cny", "fx_gbp", "fx_oth"])
    res = type("R", (), {"brent": np.full((n, T), 70.0), "events": {"R03": np.zeros((n, T), bool)}})
    E = {"V1": V1, "Y": np.full((n, T), 10_000.0), "e": np.full((n, T), 1.7), "n": n, "moves": [zero] * T,
         "dev_on": np.zeros((n, T), bool), "res": res}
    return E, np.tile(np.asarray(fis_row, float), (n, 1))


class DebtIdentity(unittest.TestCase):
    def setUp(self):
        self.full = config.as_of().year != 2026          # 2026 counts half a year when the run is in 2026

    def test_deficit_adds_to_debt(self):
        E, fis = _toy_engine([-1.0] * len(YEARS))          # deficit 1 % of GDP = 100 mln AZN a year
        P = dsa.debt_paths(E, fis)
        step = np.diff(P["D"][0])
        self.assertTrue(np.allclose(step, 100.0))
        self.assertTrue((P["cash"] == 0).all())

    def test_surplus_capped_by_amortisation_and_saved(self):
        E, fis = _toy_engine([5.0] * len(YEARS))           # big surplus: 500 mln a year
        P = dsa.debt_paths(E, fis)
        self.assertTrue((P["D"] > 0).all())                # no negative debt
        self.assertTrue((np.diff(P["cash"][0]) > 0).all())  # the excess is saved
        amort = P["D"][0][:-1] * (0.33 * dsa.AMORT_EXT + 0.67 * dsa.AMORT_DOM)
        self.assertTrue(np.allclose(-np.diff(P["D"][0]), amort, rtol=0.02))

    def test_devaluation_revalues_fx_debt(self):
        E, fis = _toy_engine([0.0] * len(YEARS))
        E["e"][:, 2:] = 1.7 * 1.25
        P = dsa.debt_paths(E, fis)
        jump = P["D"][0, 2] - P["D"][0, 1]                 # balanced budget: only the revaluation moves debt
        self.assertAlmostEqual(jump, 0.25 * 0.33 * P["D"][0, 1], delta=1.0)


class Coupling(unittest.TestCase):
    def test_rank_coupling_keeps_order(self):
        rng = np.random.default_rng(1)
        sim = rng.standard_normal(5000)
        draws = pd.DataFrame({"brent": rng.standard_normal(5000), "eq": rng.standard_normal(5000)})
        draws["eq"] = 0.5 * draws["brent"] + draws["eq"]
        out = dsa.couple(sim, draws, rng)
        self.assertAlmostEqual(stats.spearmanr(sim, out["brent"])[0], 1.0, places=6)
        self.assertAlmostEqual(stats.spearmanr(out["brent"], out["eq"])[0],
                               stats.spearmanr(draws["brent"], draws["eq"])[0], delta=0.02)


class Merton(unittest.TestCase):
    def test_distance_to_distress(self):
        far = car.merton(100.0, 10.0, 0.1, 0.04)
        self.assertGreater(far["DD"], 20)
        self.assertLess(far["PD_risk_neytral"], 1e-10)
        near = car.merton(100.0, 100.0, 0.2, 0.0)
        self.assertAlmostEqual(near["DD"], -0.1, places=6)  # (0 − σ²/2)/σ
        self.assertGreater(near["spred_bp"], 0)


@unittest.skipUnless((OUT / "K2_car_distribution.csv").exists() and (OUT / "K3_dsa_fan.csv").exists(),
                     "CaR çıxışları yoxdur")
class PublishedOutputs(unittest.TestCase):
    def test_car_distribution(self):
        k = pd.read_csv(OUT / "K2_car_distribution.csv")
        self.assertTrue((k["CaR99_mln_usd"] >= k["CaR95_mln_usd"]).all())
        self.assertTrue((k["CaR95_mln_usd"] >= 0).all())
        self.assertTrue((k["ES99_mln_usd"] >= k["CaR99_mln_usd"]).all())
        self.assertEqual(sorted(k["il"].unique()), YEARS)

    def test_dsa_fan_monotone(self):
        k = pd.read_csv(OUT / "K3_dsa_fan.csv")
        q = k[["p05", "p10", "p25", "p50", "p75", "p90", "p95"]].to_numpy()
        self.assertTrue((np.diff(q, axis=1) >= -1e-9).all())
        self.assertTrue(((k["P_borc_gt_30"] >= k["P_borc_gt_45"]) & (k["P_borc_gt_45"] >= k["P_borc_gt_60"])).all())
        self.assertEqual(k["variant"].nunique(), 3)

    def test_summary_and_adequacy(self):
        k1 = pd.read_csv(OUT / "K1_at_risk_summary.csv")
        self.assertTrue({"GaR", "IaR", "FaR", "CAaR", "DaR", "SaR", "CaR"} <= set(k1["gosterici"]))
        k4 = pd.read_csv(OUT / "K4_sofaz_adequacy.csv")
        self.assertTrue({f"S{i}" for i in range(1, 9)} <= set(k4["ssenari"]))
        k5 = pd.read_csv(OUT / "K5_cca.csv")
        self.assertTrue(k5["PD_risk_neytral"].between(0, 1).all())
        self.assertTrue(k5["qeyd"].str.contains("TƏXMİNİ").all())


if __name__ == "__main__":
    unittest.main()
