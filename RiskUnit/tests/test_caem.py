"""Offline tests of the CAEM integration (riskunit.caem, riskunit.caem_model)."""
import os
import sys
import unittest
from pathlib import Path

os.environ["RISK_NO_NETWORK"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from riskunit import caem, caem_model as cm  # noqa: E402


class TestAZEModel(unittest.TestCase):
    def test_pinned_copy(self):
        self.assertTrue(cm.CAEM_COPY.exists())
        self.assertEqual(cm.md5(cm.CAEM_COPY), cm.CAEM_MD5)

    def test_ranges_and_solution(self):
        m = cm.load()
        for k in ("A0", "A1", "A2", "B1", "B2"):
            self.assertEqual(m[k].shape, (48, 48))
        A0i = np.linalg.inv(m["A0"])
        self.assertLess(np.abs(A0i @ m["A1"] - m["B1"]).max(), 1e-9)
        self.assertLess(np.abs(A0i @ m["A2"] - m["B2"]).max(), 1e-9)

    def test_loaded_irf_reproduced(self):
        m = cm.load()
        y = cm.simulate(m["E_loaded"])
        self.assertLess(np.nanmax(np.abs(y - m["Y_loaded"])), 1e-9)
        ix = m["ix"]
        self.assertAlmostEqual(y[ix["CR"], 1], 2.42, places=2)
        self.assertAlmostEqual(y[ix["dy"], 1], -0.13, delta=0.006)
        self.assertAlmostEqual(y[ix["dy"], 2], -0.20, delta=0.006)

    def test_validation_all_pass(self):
        v = cm.validate()
        self.assertTrue((v["netice"] == "keçdi").all(), v[v["netice"] != "keçdi"])

    def test_target_path_imposed(self):
        p = np.full(cm.H + 1, np.nan)
        p[1], p[2:] = 14.5, 0.0
        y = cm.simulate(targets={"dPoil": p})
        i = cm.load()["ix"]["dPoil"]
        self.assertAlmostEqual(y[i, 1], 14.5, places=9)
        self.assertLess(np.abs(y[i, 2:]).max(), 1e-9)

    def test_shock_library_shape(self):
        lib, ix, var = cm.shock_library()
        self.assertEqual(len(ix), 40)
        self.assertEqual(len(var), 48)
        self.assertTrue(ix["model"].str.contains("əsas ötürmə kanalı deyil").all())
        self.assertEqual(lib["shock_id"].nunique(), 40)
        self.assertEqual(lib.groupby("library")["shock_id"].nunique().sort_values().tolist(), [14, 26])
        self.assertEqual(len(lib), 40 * 48 * 13)
        self.assertTrue(lib["model"].str.contains("müqayisə").all())


class TestSignals(unittest.TestCase):
    def test_band_edges(self):
        e_oil, e_imp = caem.SPEC["oil_brent"]["edges"], caem.SPEC["import_price"]["edges"]
        self.assertEqual(e_imp, (1.0, 1.5, 2.0))           # formula, not header (±0.5/1/1.5)
        self.assertEqual(caem.band_of(0.6, e_oil), 5)
        self.assertEqual(caem.band_of(0.6, e_imp), 4)
        self.assertEqual(caem.band_of(-1.6, e_oil), 1)
        self.assertEqual(caem.class_of(1, True), "mənfi")
        self.assertEqual(caem.class_of(1, False), "əlverişli")

    def test_score_monotone(self):
        zs = np.linspace(-4, 4, 161)
        for ind in ("oil_brent", "food_price", "import_price"):
            sp = caem.SPEC[ind]
            s = np.array([caem.score_of(z, sp["edges"], sp["low_bad"]) for z in zs])
            d = np.diff(s)
            self.assertTrue((d <= 1e-12).all() if sp["low_bad"] else (d >= -1e-12).all())
            self.assertTrue(((s >= 0) & (s <= 5)).all())
            self.assertAlmostEqual(caem.score_of(0, sp["edges"], sp["low_bad"]), 2.5)

    def test_ministry_bands_reproduced_exactly(self):
        r = caem.reproduce_ministry_bands()
        self.assertGreaterEqual(len(r), 100)
        self.assertTrue(r["match"].all())

    def test_signals_frame(self):
        s = caem.signals()
        for c in ("indicator", "year", "value", "mean", "sd", "band", "class_az", "source"):
            self.assertIn(c, s.columns)
        p = s[s.primary & (s.variant == "cari")]
        for ind in ("oil_brent", "food_price", "import_price", "tp_gdp"):
            self.assertTrue(set(range(2026, 2031)) <= set(p[p.indicator == ind].year), ind)
        orig = s[(s.variant == "nazirlik_orijinal") & (s.indicator == "oil_brent")].set_index("year")
        self.assertAlmostEqual(orig.at[2025, "z"], 0.0124, places=3)


class TestBalanceAndRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = caem.run({"write": False, "run_fr13": False})

    def test_ministry_totals(self):
        b = self.res["C2_balance_of_risks.csv"]
        m = b[b.version.str.startswith("Nazirlik")]
        for y, tot in ((2022, 43), (2024, 47), (2025, 49)):
            sub = m[(m.year == y) & (m.category != "CƏMİ")]
            self.assertAlmostEqual(float((sub.score * sub.weight).sum()), tot, places=6)
            self.assertAlmostEqual(float(m[(m.year == y) & (m.category == "CƏMİ")].weighted.iloc[0]), tot)

    def test_data_driven_range(self):
        b = self.res["C2_balance_of_risks.csv"]
        d = b[b.version.str.startswith("məlumat")]
        self.assertEqual(sorted(d.year.unique()), list(range(2022, 2031)))
        t = d[d.category == "CƏMİ"].weighted
        self.assertTrue(((t >= 0) & (t <= 100)).all())
        s = d[d.category != "CƏMİ"].score
        self.assertTrue(((s >= 0) & (s <= 5)).all())
        self.assertEqual(caem.read_off(56), caem.read_off(80))
        self.assertNotEqual(caem.read_off(55), caem.read_off(56))
        self.assertNotEqual(caem.read_off(45), caem.read_off(44.9))

    def test_fr2_mapping(self):
        v = [caem.score_from_fr2(s) for s in range(1, 26)]
        self.assertTrue(np.all(np.diff(v) > 0))
        self.assertAlmostEqual(v[0], 2.0)
        self.assertAlmostEqual(v[-1], 5.0)

    def test_category_map(self):
        c = self.res["C3_category_map.csv"]
        for rid in ("R01", "R05", "R06", "R17 (təklif)", "R18 (təklif)"):
            self.assertIn(rid, set(c.ru_risk_id))

    def test_findings(self):
        f = self.res["C6_caem_findings.csv"]
        self.assertGreaterEqual(len(f), 20)
        txt = " ".join(f.astype(str).agg(" ".join, axis=1))
        for key in ("#REF!", "#NAME?", "41 965", "P384:T384", "Q26", "-16,57", "M26", "F109", "+0.8+1"):
            self.assertIn(key, txt, key)
        for c in ("sheet", "cell_range", "issue_az", "evidence", "consequence_az", "recommendation_az"):
            self.assertIn(c, f.columns)

    def test_transmission_labels(self):
        c = self.res["C5_transmission_comparison.csv"]
        self.assertTrue(set(c.shock_key) >= {"brent10", "extdem10", "rate_m200", "stateinv1bn"})
        caem_rows = c[c.model.str.startswith("CAEM")]
        self.assertTrue(caem_rows.note_az.str.contains("əsas ötürmə kanalı deyil").all())
        self.assertIn("MikroUnit FR1", set(c.model))


if __name__ == "__main__":
    unittest.main()
