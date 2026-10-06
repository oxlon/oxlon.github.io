"""Offline tests of the VaR / ES layer (feeds_market, exposures, var). unittest- and pytest-compatible.

    RISK_NO_NETWORK=1 python3 -m unittest tests.test_var -v
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["RISK_NO_NETWORK"] = "1"

from riskunit import config, exposures, feeds_market as fm, var  # noqa: E402

OUT = config.OUTPUT


class RiskMeasures(unittest.TestCase):
    def setUp(self):
        self.x = np.random.default_rng(1).standard_normal(200_000)

    def test_hs_normal(self):
        v, e = var.hs(self.x, 0.99)
        self.assertAlmostEqual(v, stats.norm.ppf(0.99), delta=0.03)
        self.assertAlmostEqual(e, stats.norm.pdf(stats.norm.ppf(0.99)) / 0.01, delta=0.05)

    def test_awhs_weights_and_limit(self):
        w = var.age_weights(500, 0.995)
        self.assertAlmostEqual(w.sum(), 1.0)
        self.assertEqual(int(np.argmax(w)), 499)                 # newest observation weighs most
        v1, _ = var.awhs(self.x[:5000], 0.95, 0.999999)
        v2, _ = var.hs(self.x[:5000], 0.95)
        self.assertAlmostEqual(v1, v2, delta=0.02)

    def test_cornish_fisher_reduces_to_normal(self):
        v, e = var.cornish_fisher(self.x, 0.99)
        self.assertAlmostEqual(v, 2.326, delta=0.03)
        self.assertAlmostEqual(e, 2.665, delta=0.04)

    def test_evt_on_student_t(self):
        x = stats.t.rvs(4, size=100_000, random_state=2)
        v, e, f = var.evt(x, 0.995)
        self.assertAlmostEqual(v, stats.t.ppf(0.995, 4), delta=0.15)
        self.assertGreater(f["xi"], 0.1)                         # heavy tail detected
        self.assertGreater(e, v)

    def test_t_copula_recovers_nu_and_rho(self):
        rng = np.random.default_rng(3)
        R = np.array([[1, .6], [.6, 1]])
        Z = rng.multivariate_normal([0, 0], R, size=3000)
        X = Z / np.sqrt(rng.chisquare(4, 3000) / 4)[:, None]
        cop = var.fit_t_copula(pd.DataFrame(X, columns=["a", "b"]))
        self.assertIn(cop["nu"], (3, 4, 5, 6))
        self.assertAlmostEqual(cop["R"][0, 1], 0.6, delta=0.05)
        sim = var.sample_t_copula(cop, pd.DataFrame(X, columns=["a", "b"]), 20000, rng)
        self.assertAlmostEqual(stats.kendalltau(sim["a"], sim["b"])[0], 2 / np.pi * np.arcsin(0.6), delta=0.03)

    def test_euler_additivity(self):
        rng = np.random.default_rng(4)
        comp = pd.DataFrame(rng.standard_normal((50_000, 3)) * [1, 2, 3], columns=["a", "b", "c"])
        lines = {k: (1.0, "log") for k in comp}
        eu = var.euler(comp, 0.99, lines)
        self.assertAlmostEqual(eu["tohfe_VaR"].sum(), eu.attrs["VaR"], places=6)
        self.assertAlmostEqual(eu["tohfe_ES"].sum(), eu.attrs["ES"], places=6)
        self.assertGreater(eu.set_index("komponent").at["c", "tohfe_VaR"], eu.set_index("komponent").at["a", "tohfe_VaR"])

    def test_acerbi_szekely_sign(self):
        rng = np.random.default_rng(5)
        x = rng.standard_normal(5000)
        v, e = stats.norm.ppf(0.975), stats.norm.pdf(stats.norm.ppf(0.975)) / 0.025
        self.assertAlmostEqual(var.acerbi_szekely_z2(x, np.full(5000, v), np.full(5000, e), 0.025), 0, delta=0.15)
        self.assertLess(var.acerbi_szekely_z2(2 * x, np.full(5000, v), np.full(5000, e), 0.025), -0.5)

    def test_rolling_backtest_on_iid(self):
        pnl = pd.Series(np.random.default_rng(6).standard_normal(700),
                        index=pd.bdate_range("2020-01-01", periods=700))
        hist, t = var.rolling_backtest(pnl, 250, "d", methods=("hs", "cf"), M=200)
        self.assertEqual(len(hist), 450)
        k = t["tests"]
        self.assertTrue({"Kupiec POF", "Christoffersen müstəqillik", "Acerbi–Székely Z2 (ES)"} <= set(k["test"]))
        self.assertTrue((k["n"] > 0).all())
        self.assertGreater(k[(k.test == "Kupiec POF") & (k.metod == "hs") & (k.etibarlilik == 0.95)]["p_deyer"].iloc[0], 0.01)


class FactorsAndExposures(unittest.TestCase):
    def test_factor_moves_sign_conventions(self):
        idx = pd.bdate_range("2024-01-01", periods=4)
        L = pd.DataFrame({"spx": [100, 101, 102, 103], "gold": [2000, 2010, 2020, 2030], "eurusd": [1.1, 1.2, 1.2, 1.2],
                          "gbpusd": 1.3, "usdcny": [7.0, 7.7, 7.7, 7.7], "usdjpy": 150.0, "usd_broad": 120.0,
                          "ust2": [4.0, 4.1, 4.1, 4.1], "ust5": 4.0, "ust10": 4.0, "brent": 80.0}, index=idx)
        m = var.factor_moves(L, "d")
        self.assertGreater(m["fx_eur"].iloc[0], 0)               # EUR appreciates -> EUR assets gain in USD
        self.assertLess(m["fx_cny"].iloc[0], 0)                  # USD/CNY up -> CNY assets lose
        lines = {"ust2": (1000.0, "rate"), "fx_eur": (100.0, "log")}
        p = var.pnl_components(m.iloc[:1], lines)
        self.assertAlmostEqual(p["ust2"].iloc[0], -1000 * 0.1 / 100)

    def test_cbar_xml_parser(self):
        xml = ('<ValCurs Date="02.10.2026"><ValType Type="x"><Valute Code="USD"><Nominal>1</Nominal><Name>d</Name>'
               '<Value>1.7</Value></Valute><Valute Code="RUB"><Nominal>100</Nominal><Name>r</Name><Value>2.05</Value>'
               '</Valute><Valute Code="XAU"><Nominal>1 t.u.</Nominal><Name>g</Name><Value>7114.3555</Value></Valute>'
               '</ValType></ValCurs>').encode()
        d = fm.parse_cbar_xml(xml).set_index("code")["azn_per_unit"]
        self.assertEqual(fm.parse_cbar_xml(xml)["date"].iloc[0], "2026-10-02")
        self.assertAlmostEqual(d["RUB"], 0.0205)
        self.assertAlmostEqual(d["XAU"] / d["USD"], 4184.9, delta=0.1)

    def test_number_formats_and_mix(self):
        self.assertEqual(exposures._num_az("23.830,6"), 23830.6)
        self.assertEqual(exposures._num_en("72 595.1"), 72595.1)
        mix = exposures._mix("ABŞ dolları – 86,4 faiz, avro – 6,1 faiz, XBH (x) – 2,9 faiz, yapon yeni – 3,1 faiz, "
                             "digər valyutalar – 1,5 faiz")
        self.assertEqual(mix, {"USD": 86.4, "EUR": 6.1, "XDR": 2.9, "JPY": 3.1, "OTHER": 1.5})
        krd = exposures.fi_key_rate_durations(exposures.SEED_SOFAZ["maturity_pct"])
        self.assertAlmostEqual(sum(krd.values()), 3.8915, places=3)

    def test_offline_fetch_uses_cache(self):
        with tempfile.TemporaryDirectory() as td:
            old = config.VINTAGES
            try:
                config.VINTAGES = Path(td)
                (Path(td) / "fred" / "2026-01-01").mkdir(parents=True)
                (Path(td) / "fred" / "2026-01-01" / "DGS2.csv").write_text("observation_date,DGS2\n2026-01-02,4.1\n")
                with self.assertRaises(fm.FeedUnavailable):
                    fm.http_get("https://example.org")
                s = fm.fred("ust2")
                self.assertEqual(float(s.iloc[-1]), 4.1)
                self.assertTrue(fm._STATUS_ROWS[-1]["status"].startswith("keş"))
                with self.assertRaises(fm.FeedUnavailable):
                    fm.fred("ust10")                             # no cache, no network
            finally:
                config.VINTAGES = old
                fm._STATUS_ROWS.clear()


@unittest.skipUnless((OUT / "V3_var_es.csv").exists() and (OUT / "V1_exposures.csv").exists(), "VaR çıxışları yoxdur")
class PublishedOutputs(unittest.TestCase):
    def test_exposures_sourced(self):
        v = pd.read_csv(OUT / "V1_exposures.csv")
        for k in ("sofaz_total", "cbar_reserves", "debt_public_total", "cl_guaranteed_total", "budget_rev_oil_2025"):
            self.assertIn(k, set(v["kod"]))
        self.assertFalse(v["menbe"].isna().any())
        self.assertFalse(v["tarix"].isna().any())
        cls = v[v.kod.str.startswith("sofaz_class_")]["pay_faiz"].sum()
        self.assertAlmostEqual(cls, 100, delta=0.6)
        self.assertTrue((OUT / "V1b_data_requests.csv").exists())

    def test_var_table_coherent(self):
        v = pd.read_csv(OUT / "V3_var_es.csv")
        self.assertTrue({"hs", "awhs", "mc_tcop", "evt", "cf"} <= set(v["metod"]))
        self.assertTrue({"1g", "1a", "1il"} <= set(v["horizont"]))
        w = v.dropna(subset=["VaR_mln_usd"]).pivot_table(index=["portfel", "horizont", "metod"], columns="etibarlilik",
                                                         values="VaR_mln_usd")
        self.assertTrue((w[0.99] >= w[0.95] - 1e-6).all())
        m = v[(v.portfel != "oil_rev") & v.VaR_mln_usd.notna()]
        self.assertTrue((m["ES_mln_usd"] >= m["VaR_mln_usd"] - 1e-6).all())
        self.assertTrue(v[v.metod == "sqrt_time"]["qeyd"].str.contains("TƏXMİNİ").all())

    def test_backtest_reports_n(self):
        b = pd.read_csv(OUT / "V5_var_backtest.csv")
        self.assertIn("n", b.columns)
        ok = b[b.netice.isin(["keçdi", "keçmədi"])]
        self.assertTrue((ok["n"] > 0).all())
        self.assertTrue((b[b.n == 0]["netice"] == "yoxlanıla bilməz").all())

    def test_contributions_add_up(self):
        c = pd.read_csv(OUT / "V4_var_contributions.csv")
        v = pd.read_csv(OUT / "V3_var_es.csv")
        g = c[c.qrup == "amil"].groupby(["portfel", "horizont", "etibarlilik"])["pay_VaR"].sum()
        self.assertTrue(np.allclose(g.to_numpy(), 1.0, atol=1e-6))
        self.assertTrue(len(v))


if __name__ == "__main__":
    unittest.main()
