"""Core tests (offline): engine interface, horizons, configuration, scenario validation (NFR4),
MicroUnit mapping (warnings-as-errors), CAEM pinned copy. Run: python3 -m unittest discover -s tests"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ["POLICY_NO_NETWORK"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hermetic  # noqa: E402,F401  (temp work/ and output/)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from policyunit import (config, engine_base as EB, registry, scenario as scn)  # noqa: E402


class TestEngineBase(unittest.TestCase):
    def test_horizon_ministry_definition(self):
        self.assertEqual([EB.horizon(y, 2027) for y in range(2027, 2033)],
                         ["qısa", "qısa", "orta", "orta", "uzun", "uzun"])

    def test_row_and_frame(self):
        r = EB.row("gdp_real", "x", "mln AZN 2015", 2027, 100.0, 101.0, "m", "C", "makro")
        self.assertAlmostEqual(r["delta_pct"], 1.0)
        r = EB.row("infl", "x", "%", 2027, 5.0, 5.5, "m", "C", "makro")
        self.assertAlmostEqual(r["delta_pct"], 0.5)          # rates: pp
        r = EB.row("budget_balance", "x", "mln AZN", 2027, 10.0, 5.0, "m", "C", "fiskal")
        self.assertTrue(pd.isna(r["delta_pct"]))
        res = EB.Result("micro", [r])
        self.assertEqual(list(res.frame.columns), EB.OUT_COLS)


class TestConfig(unittest.TestCase):
    def test_catalogue_consistent(self):
        self.assertEqual(registry.validate_catalogue(), [])

    def test_every_instrument_has_an_adapter_for_listed_engines(self):
        ad = registry.adapters()
        for iid in registry.instruments().index:
            for e in registry.engines_for(iid):
                if e in ("micro", "caem", "oxlon"):
                    self.assertTrue(((ad.instrument == iid) & (ad.engine == e)).any(), f"{iid}/{e}")

    def test_kpi_catalogue(self):
        from policyunit import kpi
        cat = kpi.catalogue()
        self.assertGreaterEqual(len(cat), 20)
        self.assertGreaterEqual((cat.default_selected == "yes").sum(), 5)
        with self.assertRaises(kpi.KpiError):
            kpi.select(["gdp_short", "gdp_medium", "gdp_long", "inflation_short"])

    def test_example_scenarios(self):
        ids = scn.all_ids()
        self.assertGreaterEqual(len(ids), 8)
        fams = {registry.instrument(it["instrument"])["family"] for s in scn.load_all() for it in s["instruments"]}
        self.assertGreaterEqual(len(fams), 6)


class TestScenarioValidation(unittest.TestCase):
    def _errs(self, **kw):
        s = {"id": "t", "name_az": "t", "start_year": 2027,
             "instruments": [{"instrument": "min_wage", "years": "all", "size": 20, "unit": "pct"}]}
        s.update(kw)
        return scn.validate(s)

    def test_valid(self):
        self.assertEqual(self._errs(), [])

    def test_errors_in_azerbaijani(self):
        e = self._errs(instruments=[{"instrument": "nope", "size": 1}])
        self.assertIn("kataloqda belə alət yoxdur", e[0])
        e = self._errs(instruments=[{"instrument": "min_wage", "size": 500, "unit": "pct"}])
        self.assertIn("intervalından kənardır", e[0])
        e = self._errs(instruments=[{"instrument": "min_wage", "size": 5, "unit": "pp"}])
        self.assertIn("vahid", e[0])
        self.assertTrue(self._errs(start_year=2040))

    def test_new_scenario_by_configuration_only(self):
        """NFR4: a new JSON file is loaded, expanded and mapped without any code change."""
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "nfr4_demo.json"
            p.write_text(json.dumps({"id": "nfr4_demo", "name_az": "Demo", "start_year": 2026, "instruments": [
                {"instrument": "policy_rate", "years": [2026, 2027], "size": -0.5, "unit": "pp"}]}), encoding="utf-8")
            s = scn.load(p)
            self.assertEqual(s["instruments"][0]["years"], [2026, 2027])
            from policyunit import micro_map
            m = micro_map.build(s)
            self.assertIn("polrate", m["overrides"]["FR1"]["exogenous"])


class TestMicroMapping(unittest.TestCase):
    def test_override_ids_exist_in_microunit(self):
        from policyunit import micro_map, microbridge as mb
        known = {m: {e["id"] for e in mb.catalogue(m)["exogenous"]} | {lv["id"] for lv in mb.catalogue(m)["levers"]}
                 for m in ("FR1", "FR3", "FR5", "FR12")}
        for s in scn.load_all():
            ov = micro_map.build(s)["overrides"]
            for mod, d in ov.items():
                for kind in ("exogenous", "levers"):
                    for k in d.get(kind, {}):
                        self.assertIn(k, known[mod], f"{s['id']}: {mod}.{k}")

    def test_unknown_override_raises(self):
        from policyunit import microbridge as mb
        with self.assertRaises(mb.MicroOverrideError):
            mb.run({"FR1": {"exogenous": {"no_such_input": {"add": [1] * 5}}}})

    def test_baseline_has_no_override_warnings(self):
        from policyunit import microbridge as mb
        b = mb.baseline()
        self.assertEqual(mb.override_errors(b["warnings"]), [])


class TestCaem(unittest.TestCase):
    def test_pinned_copy(self):
        from policyunit import caem_core
        self.assertTrue(caem_core.vintage_status()["pinned_ok"])

    def test_policy_rate_cut_is_expansionary(self):
        from policyunit import eng_caem
        r = eng_caem.run(scn.load("polrate_m100"))
        g = r.frame[(r.frame.indicator == "gdp_real") & (r.frame.year == 2028)]["delta_pct"].iloc[0]
        self.assertGreater(g, 0)


if __name__ == "__main__":
    unittest.main()
