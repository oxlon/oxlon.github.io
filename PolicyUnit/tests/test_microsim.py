"""Offline tests of the household microsimulation (FR3): tax-benefit rules, metrics,
calibration tools, synthetic file / validator, engine interface and linkage."""
import os
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

os.environ.setdefault("POLICY_NO_NETWORK", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from policyunit import hh_data, ms_calib, ms_links, ms_metrics as M, taxben as tb  # noqa: E402
from policyunit.engine_base import OUT_COLS  # noqa: E402

P = tb.Params()


class TaxBenefit(unittest.TestCase):
    def test_minwage_annual_average_2019(self):
        self.assertAlmostEqual(P.get("minwage", 2019), (2 * 130 + 6 * 180 + 4 * 250) / 12)
        self.assertEqual(P.get("minwage", 2019, how="dec"), 250)

    def test_pit_regimes(self):
        g = np.array([400.0, 3000.0, 1000.0])
        r = np.array(["priv", "priv", "state"])
        self.assertAlmostEqual(tb.wage_taxes(g, r, P, 2018)["pit"][0], 0.14 * (400 - 173))
        t26 = tb.wage_taxes(g, r, P, 2026)["pit"]
        self.assertAlmostEqual(t26[1], 75 + 0.10 * 500)               # 3 % + 10 % pillə
        self.assertAlmostEqual(t26[2], 0.14 * (1000 - 200))            # dövlət: 200 AZN azad
        self.assertEqual(tb.wage_taxes(g, r, P, 2024)["pit"][1], 0.0)  # 2019–2025 güzəşt

    def test_social_contributions(self):
        o = tb.wage_taxes(np.array([700.0]), np.array(["priv"]), P, 2019)
        self.assertAlmostEqual(o["ssc_ee"][0], 6 + 0.10 * 500)
        self.assertAlmostEqual(o["ssc_er"][0], 44 + 0.15 * 500)
        m = tb.wage_taxes(np.array([3000.0]), np.array(["priv"]), P, 2026)
        self.assertAlmostEqual(m["med_ee"][0], 0.02 * 2500 + 0.005 * 500)
        inf = tb.wage_taxes(np.array([700.0]), np.array([""]), P, 2026)
        self.assertEqual(inf["net"][0], 700.0)

    def test_net_to_gross_roundtrip(self):
        g = np.array([400.0, 1500.0, 9000.0])
        r = np.array(["priv", "state", "priv"])
        net = tb.wage_taxes(g, r, P, 2026)["net"]
        np.testing.assert_allclose(tb.net_to_gross(net, r, P, 2026), g, atol=0.05)

    def test_utsy_and_pension(self):
        amt, el = tb.utsy([900.0, 2000.0], [4, 4], 300.0, [True, True])
        self.assertEqual(list(amt), [300.0, 0.0])
        self.assertTrue(el[0] and not el[1])
        self.assertAlmostEqual(tb.pension_level([100.0], 2024, 2025, P)[0],
                               (280 + 11 * 320) / 12)                     # minimum, il ortası
        self.assertAlmostEqual(tb.pension_level([1000.0], 2024, 2026, P)[0], 1000 * 1.081 * 1.093)

    def test_override_regime(self):
        Q = P.with_overrides({"pit_r1@priv": {"add": 0.02}})
        self.assertAlmostEqual(Q.get("pit_r1", 2026, "priv"), 0.05)
        self.assertAlmostEqual(Q.get("pit_r1", 2026, "state"), 0.14)


class Metrics(unittest.TestCase):
    def test_gini_fgt(self):
        w = np.ones(4)
        self.assertAlmostEqual(M.gini(np.full(4, 5.0), w), 0.0)
        self.assertAlmostEqual(M.gini(np.array([0, 0, 0, 1.0]), w), 0.75, places=6)
        x = np.array([50.0, 100.0, 200.0, 400.0])
        self.assertAlmostEqual(M.fgt(x, w, 150, 0), 0.5)
        self.assertAlmostEqual(M.fgt(x, w, 100, 1), (0.5 + 0) / 4)
        d = M.hh_deciles(np.arange(100.0), np.ones(100))
        self.assertEqual(np.bincount(d)[1:].tolist(), [10] * 10)

    def test_entropy_weights(self):
        rng = np.random.default_rng(1)
        X = rng.integers(0, 3, (500, 4)).astype(float)
        d = np.full(500, 10.0)
        T = X.T @ d * np.array([1.1, 0.9, 1.0, 1.05])
        w, err = ms_calib.entropy_weights(X, T, d)
        np.testing.assert_allclose(X.T @ w, T, rtol=1e-6)
        self.assertTrue((w > 0).all())


class SyntheticFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p, cls.cal, cls.synth = hh_data.load(mode="SYNTHETIC")

    def test_watermark_and_validator(self):
        self.assertTrue(self.synth)
        self.assertTrue((self.p["data_status"] == hh_data.WATERMARK).all())
        iss = hh_data.validate(self.p)
        self.assertFalse((iss.severity == "error").any())
        self.assertTrue(10000 <= self.p.hh_id.nunique() <= 20000)

    def test_validator_catches_errors(self):
        bad = self.p.head(20).drop(columns=["age"]).copy()
        bad.loc[bad.index[0], "pension"] = -5
        iss = hh_data.validate(bad)
        self.assertIn("age", set(iss.field))
        self.assertIn("pension", set(iss.field))

    def test_column_map_az_headers(self):
        az = {c: a for c, a, *_ in hh_data.COLUMNS}
        df = self.p.head(5).rename(columns=az)
        back = hh_data.normalise_columns(df)
        self.assertEqual(list(back.columns), list(self.p.columns))

    def test_calibration_in_sample(self):
        self.assertGreater(self.cal["kappa"], 0)
        from policyunit import ms_policy as MP
        hh, _ = MP.compute(MP.prepare(self.p), self.cal, 2024, P)
        pw = (hh.w * hh.n).to_numpy()
        pov = 100 * M.fgt(hh.c_pc.to_numpy() * self.cal["kappa"], pw, 270.1, 0)
        self.assertAlmostEqual(pov, 5.3, delta=0.3)
        self.assertAlmostEqual(np.sum(hh.w * hh.y_total) / pw.sum(), 359.2, delta=1.0)

    def test_switch_employment_exact(self):
        from policyunit import ms_policy as MP
        q = MP.prepare(self.p)
        base = q.loc[(q.status == "employee") & (q.sector == "constr"), "weight"].sum()
        pop = q.weight.sum()
        s = ms_links.switch_employment(q, {"constr": 10.0})
        new = s.loc[(s.status == "employee") & (s.sector == "constr"), "weight"].sum()
        self.assertAlmostEqual(new / base, 1.10, places=4)
        self.assertAlmostEqual(s.weight.sum(), pop, delta=1e-3 * pop)


class Engine(unittest.TestCase):
    def _run(self, inst, size, target=None, year=2026):
        from policyunit import eng_microsim as E
        s = {"id": "t", "name_az": "t", "start_year": year,
             "instruments": [{"instrument": inst, "years": [year], "size": size,
                              "target": target}]}
        return E.run(s, {})

    def test_interface_and_signs(self):
        r = self._run("min_wage", 20)
        self.assertEqual(r.engine, "microsim")
        self.assertEqual(list(r.frame.columns), OUT_COLS)
        f = r.frame.set_index(["indicator", "group"])
        self.assertLessEqual(f.loc[("poverty_rate", "dsk"), "delta"], 0)
        self.assertGreater(f.loc[("wage_nominal", ""), "delta"], 0)
        self.assertEqual(r.meta["data_mode"], "SYNTHETIC")

    def test_pension_cost_and_tsa(self):
        f = self._run("pension_index", 10).frame.set_index("indicator")
        self.assertAlmostEqual(f.loc["ms_fiscal:pensions", "delta_pct"], 10.0, places=3)
        self.assertGreater(f.loc["fiscal_cost", "value"], 0)
        g = self._run("tsa_benefit", 30).frame.set_index("indicator")
        self.assertAlmostEqual(g.loc["ms_fiscal:utsy", "delta_pct"], 30.0, places=3)

    def test_pit_raises_revenue(self):
        f = self._run("pit_nonoil_private", 2).frame.set_index("indicator")
        self.assertGreater(f.loc["ms_fiscal:pit", "delta"], 0)
        self.assertLess(f.loc["fiscal_cost", "value"], 0)


class Docs(unittest.TestCase):
    def test_auto_blocks_rendered(self):
        root = Path(__file__).resolve().parent.parent
        for f in (root / "docs" / "Metodologiya_mikrosimulyasiya.md",
                  root / "data" / "households" / "README_az.md"):
            t = f.read_text()
            self.assertNotIn("--><!-- /AUTO", t, f.name)
            self.assertNotIn("## EN", t)


if __name__ == "__main__":
    unittest.main()
