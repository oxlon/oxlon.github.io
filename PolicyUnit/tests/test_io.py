"""Offline tests of the IO engine (python3 -m unittest tests.test_io)."""
import os
import sys
import unittest
from pathlib import Path

os.environ["POLICY_NO_NETWORK"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from policyunit import engine_base as EB  # noqa: E402
from policyunit import eng_io as E  # noqa: E402
from policyunit import io_data as D  # noqa: E402
from policyunit import io_models as M  # noqa: E402
from policyunit import io_update as U  # noqa: E402
from policyunit import io_validate as V  # noqa: E402


class TestData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p21 = D.load_iot(2021)
        cls.a21 = D.aggregate(cls.p21)

    def test_parse_all_years(self):
        for y in D.YEARS:
            t = D.load_iot(y)
            self.assertEqual(t.n, 81)
            c = t.check()
            self.assertLess(c["row_resid_max"], 0.01)
            self.assertLess(c["col_resid_max"], 1e-6)
        self.assertAlmostEqual(self.p21.x.sum() / 1e3, 131736.7, delta=1.0)  # = FR1 out_tot 2021

    def test_aggregation_preserves_totals(self):
        self.assertEqual(self.a21.n, len(D.sectors()))
        self.assertAlmostEqual(self.a21.Z.sum(), self.p21.Z.sum(), delta=1.0)
        self.assertLess(self.a21.check()["row_resid_max"], 1e-5)

    def test_import_split(self):
        sp = D.domestic_split(self.a21)
        self.assertTrue(np.all((sp["s"] >= 0) & (sp["s"] <= 1)))
        np.testing.assert_allclose(sp["Zd"] + sp["Zm"], self.a21.Z)
        self.assertLess(abs(sp["imp_resid"]), 1.0)
        self.assertEqual(float(sp["fdm"]["exp"].abs().sum()), 0.0)

    def test_employment_matches_lfs(self):
        e = D.employment(2021)
        self.assertAlmostEqual(e.sum(), D.employment_sections().loc[2021].sum(), delta=0.5)
        self.assertTrue((e >= 0).all())

    def test_offline_fetch_missing(self):
        with self.assertRaises(FileNotFoundError):
            D.SOURCES["__nope__.xls"] = "x/__nope__.xls"
            try:
                D.fetch("__nope__.xls")
            finally:
                D.SOURCES.pop("__nope__.xls")


class TestModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = M.build(2021)

    def test_leontief_inverse(self):
        m = self.m
        np.testing.assert_allclose(m.L @ (np.eye(m.n) - m.Ad), np.eye(m.n), atol=1e-9)
        mu = m.multipliers()
        self.assertTrue((mu["output_I"] >= 1).all())
        self.assertTrue((mu["output_II"] >= mu["output_I"] - 1e-12).all())
        self.assertTrue((mu["va_I"] <= 1 + 1e-9).all())   # domestic VA per unit FD <= 1

    def test_price_homogeneity(self):
        """Uniform +10 % in all primary costs and import prices -> all prices +10 %."""
        m = self.m
        cif = m.t.cif / np.where(m.x > 0, m.x, 1)
        pr = m.price(dv=0.1 * (m.v + m.tx + cif), dpm=0.1 * np.ones(m.n))
        np.testing.assert_allclose(pr["dp"], 0.1, atol=1e-8)

    def test_exogenous_price(self):
        pr = self.m.price(exog={"PETR": 0.11})
        k = self.m.codes.index("PETR")
        self.assertAlmostEqual(pr["dp"][k], 0.11)
        self.assertTrue((np.delete(pr["dp"], k) >= -1e-12).all())

    def test_ghosh_reproduces_output(self):
        m = self.m
        vprim = m.va_vec + m.t.tax + m.Zm.sum(0) + m.t.cif
        np.testing.assert_allclose(m.ghosh(vprim), m.x, rtol=1e-6)

    def test_linkages_and_extraction(self):
        lk = self.m.linkages()
        self.assertAlmostEqual(lk["bl_index"].mean(), 1.0)
        ex = self.m.extraction()
        self.assertTrue((ex["extract_total_pct"] >= -1e-9).all())


class TestGRAS(unittest.TestCase):
    def test_toy_with_negatives(self):
        Z0 = np.array([[5.0, 2, -1], [1, 4, 3], [2, -0.5, 6]])
        Z, info = U.gras(Z0, np.array([7.0, 9, 8.5]), np.array([9.0, 6, 9.5]))
        self.assertTrue(info["converged"])
        np.testing.assert_allclose(Z.sum(1), [7, 9, 8.5], atol=1e-5)
        np.testing.assert_allclose(Z.sum(0), [9, 6, 9.5], atol=1e-5)
        self.assertTrue(np.all(np.sign(Z) == np.sign(Z0)))

    def test_update_2025(self):
        t, diag, info = U.update(D.aggregate(D.load_iot(2021)), 2025)
        self.assertTrue(info["converged"])
        self.assertAlmostEqual(t.x.sum() / 1e3, U.fr1_margins().loc[2025, "out_tot_n"], delta=1.0)
        self.assertLess(t.check()["row_resid_max"], 1e-5)
        self.assertLess(t.check()["col_resid_max"], 1e-6)


class TestEngine(unittest.TestCase):
    def _run(self, **it):
        it.setdefault("years", [2026])
        return E.run({"id": "t", "start_year": 2026, "instruments": [it]}, {"io_table": 2025})

    def test_frame_contract(self):
        r = self._run(instrument="pub_invest", size=1000)
        self.assertEqual(list(r.frame.columns), EB.OUT_COLS)
        f = r.frame
        np.testing.assert_allclose(f["delta"], f["value"] - f["baseline"], atol=1e-9)
        codes = set(D.sectors()["code"]) | {"ümumi"}
        self.assertTrue(set(f["group"]) <= codes)
        tot = f[f.indicator == "io_output_total"]["delta"].iloc[0]
        self.assertGreater(tot, 0)
        self.assertTrue(r.meta["vintage"]["io_update"]["converged"])

    def test_price_instruments(self):
        r = self._run(instrument="fuel_price", size=10)
        cpi = r.frame[r.frame.indicator == "io_cpi"]["delta_pct"].iloc[0]
        self.assertGreater(cpi, 0.1)
        self.assertLess(cpi, 2.0)
        r = self._run(instrument="vat_rate", size=-2)
        self.assertLess(r.frame[r.frame.indicator == "io_cpi"]["delta_pct"].iloc[0], 0)

    def test_bad_target_and_missing_adapter(self):
        with self.assertRaises(ValueError):
            self._run(instrument="io_sector_demand", size=10, target="XYZ")
        r = self._run(instrument="profit_tax", size=-2)
        self.assertTrue(r.meta["warnings"])

    def test_adapters_reference_handlers(self):
        a = E._adapters()
        self.assertGreater(len(a), 10)
        for tr in a["transform"]:
            name = E._scale(tr)[0].split(":", 1)[-1]
            self.assertIn(name, E.HANDLERS)


class TestValidation(unittest.TestCase):
    def test_stability(self):
        df, s = V.stability(2016, 2021)
        self.assertEqual(len(df), 23)
        self.assertTrue(s["io_beats_naive_wmape"])

    def test_e7(self):
        dev, sect = V.e7_fuel(2021)
        self.assertIn("fuel_item", set(dev["indicator"]))
        self.assertTrue(dev["sign_match"].iloc[0])


if __name__ == "__main__":
    unittest.main()
