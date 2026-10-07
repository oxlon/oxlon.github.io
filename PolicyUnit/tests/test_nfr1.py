"""Offline tests of the NFR1 retrospective validation (python3 -m unittest tests.test_nfr1)."""
import math
import os
import re
import sys
import unittest
from pathlib import Path

os.environ["POLICY_NO_NETWORK"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from policyunit import nfr1_data as D  # noqa: E402
from policyunit import nfr1_models as M  # noqa: E402
from policyunit import nfr1_report as R  # noqa: E402
from policyunit import validate as V  # noqa: E402


class TestRegister(unittest.TestCase):
    # read-only checks against the CURRENT outputs: point config.OUTPUT at the project folder while they run
    # (other test modules redirect it to an empty temporary folder via tests/_hermetic.py)
    @classmethod
    def setUpClass(cls):
        from policyunit import config as C
        cls._out = C.OUTPUT
        C.OUTPUT = Path(__file__).resolve().parents[1] / "output"

    @classmethod
    def tearDownClass(cls):
        from policyunit import config as C
        C.OUTPUT = cls._out

    def setUp(self):
        self.ev = D.events()

    def test_at_least_two_events_with_metadata(self):
        self.assertGreaterEqual(self.ev.event_id.nunique(), 4)
        for c in D.EVENT_COLS:
            self.assertFalse(self.ev[c].isna().any(), c)
        self.assertTrue(set(self.ev.in_sample) <= {"bəli", "xeyr"})
        self.assertEqual(set(self.ev[self.ev.event_id == "E5"].in_sample), {"bəli"})   # FX calibration episode
        self.assertTrue(set(self.ev.row_id).__len__() == len(self.ev))

    def test_methods_and_rules_known(self):
        for _, r in self.ev.iterrows():
            for m in r["methods"].split(";"):
                self.assertIn(m, M.METHODS)
            self.assertIn(r["cf_rule"], R.CF_AZ)

    def test_registered_values_match_data(self):
        for _, r in self.ev.iterrows():
            o = D.observed(r)
            self.assertEqual(o["obs_check"], "", f"{r['row_id']}: {o['obs_check']}")
            self.assertTrue(math.isfinite(o["obs_effect"]), r["row_id"])


class TestCounterfactual(unittest.TestCase):
    def test_rules(self):
        x = pd.Series({2016: 2.0, 2017: 4.0, 2018: 6.0, 2019: 10.0})
        self.assertAlmostEqual(D.cf_value(x, "pre2", 2019, 2019, "growth"), 5.0)
        self.assertAlmostEqual(D.cf_value(x, "pre1", 2019, 2019, "growth"), 6.0)
        self.assertAlmostEqual(D.cf_value(x, "trend2", 2019, 2019, "level_pp"), 8.0)
        e, cf = D.effect(x, "pre1", 2019, 2019, "growth")
        self.assertAlmostEqual(e, 4.0)
        e, cf = D.effect(pd.Series({2017: 0.0, 2018: 0.0, 2019: 10.0, 2020: 10.0}), "pre1", 2019, 2020, "cumlevel")
        self.assertAlmostEqual(e, 21.0)

    def test_minimum_wage_series(self):
        m = D.mw_annual()
        self.assertTrue(130 < m[2019] < 250)
        self.assertIn(2024, D.mw_flat_years())
        self.assertNotIn(2019, D.mw_flat_years())


class TestClassify(unittest.TestCase):
    def test_classes(self):
        self.assertEqual(V.classify(11, 10, 9, 13, 1.0)["score"], 2)
        self.assertEqual(V.classify(-5, 10, -6, -4, 1.0)["score"], 0)            # wrong direction
        self.assertEqual(V.classify(15, 10, float("nan"), float("nan"), 1.0)["score"], 1)
        self.assertEqual(V.classify(2, 0.5, float("nan"), float("nan"), 3.0)["score"], -1)   # low power
        self.assertEqual(V.classify(0, 0.5, 0, 0, 3.0, placebo=True)["score"], 2)
        self.assertEqual(V.classify(20, 0.5, 19, 21, 3.0)["score"], 0)             # decisive miss in noise


class TestTightenedRules(unittest.TestCase):
    def test_sigma_widening_capped(self):
        # huge counterfactual noise must not let a 45 % error pass as 'uyğun'
        self.assertLess(V.classify(14.5, 25.0, 5, 24, 22.0)["score"], 2)

    def test_naive_benchmark_caps_class(self):
        self.assertEqual(V.classify(7.75, 7.1, float("nan"), float("nan"), float("nan"), naive=7.75)["score"], 1)
        self.assertEqual(V.classify(7.2, 7.1, float("nan"), float("nan"), float("nan"), naive=7.75)["score"], 2)

    def test_min_decisive_for_pass(self):
        self.assertEqual(V._verdict(2.0, 1), "şərti keçdi")
        self.assertEqual(V._verdict(2.0, 2), "keçdi")
        self.assertEqual(V._verdict(float("nan"), 0), "qiymətləndirilmədi")

    def test_sensitivity_sets(self):
        _, cmp = V.comparisons(log=lambda *_: None)
        t = V.sensitivity(cmp)
        self.assertEqual(set(t.tol_set), set(V.TOL_SETS))
        strict, lenient = (t[t.tol_set == k].primary_mean_score.fillna(0).sum() for k in ("qatı", list(V.TOL_SETS)[-1]))
        self.assertLessEqual(strict, lenient)


class TestModels(unittest.TestCase):
    def test_direct_equations(self):
        ev = D.events().set_index("row_id")
        self.assertAlmostEqual(M.m_e2_direct(ev.loc["E3.w24"].copy().rename(None))["pred"], 0.0)
        r = M.m_fr3_direct(ev.loc["E1.did"].copy())
        self.assertGreater(r["pred"], 0)
        self.assertLess(r["lo"], r["pred"])
        self.assertLess(r["pred"], r["hi"])

    def test_chain_signs(self):
        ev = D.events().set_index("row_id")
        w = M.m_micro_chain(ev.loc["E1.w"].copy())
        self.assertGreater(w["pred"], 0)
        i = M.m_micro_chain(ev.loc["E5.i16"].copy())
        self.assertGreater(i["pred"], 0)                       # devaluation raises inflation

    def test_comparisons_cover_nfr2(self):
        obs, cmp = V.comparisons(log=lambda *_: None)
        self.assertGreaterEqual(cmp.event_id.nunique(), 2)
        evs = V.event_summary(D.events(), cmp)
        self.assertTrue((evs.nfr2_ok == "bəli").all())
        self.assertTrue(set(evs.verdict_az) <= {"keçdi", "şərti keçdi", "keçmədi", "qiymətləndirilmədi"})


class TestReport(unittest.TestCase):
    def test_az_number_format(self):
        self.assertEqual(R.fmt(1234.56, 1), "1 234,6")
        self.assertEqual(R.fmt(-0.25, 2), "−0,25")
        self.assertEqual(R.fmt(float("nan")), "—")

    def test_generated_report_clean(self):
        if not R.DOC.exists():
            self.skipTest("hesabat hələ yaradılmayıb")
        t = R.DOC.read_text(encoding="utf-8")
        self.assertIn("Sapma hesabatı", t)
        self.assertIsNone(re.search(r"\bnan\b", t))
        self.assertIn("TƏKLİF", t)


if __name__ == "__main__":
    unittest.main()
