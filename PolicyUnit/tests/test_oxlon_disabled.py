"""POLICY_OXLON_DISABLED=1 (hosted CI without the OxLon model copy): the OxLon engine is marked unavailable
with an Azerbaijani note; scenarios without OxLon channels and all other engines are unaffected."""
import os
import sys
import unittest
from pathlib import Path

os.environ["POLICY_NO_NETWORK"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hermetic  # noqa: E402,F401  (temp work/ and output/)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policyunit import config, eng_oxlon, scenario as scn  # noqa: E402


class TestOxlonDisabled(unittest.TestCase):
    def setUp(self):
        self._old = config.OXLON_DISABLED
        config.OXLON_DISABLED = True

    def tearDown(self):
        config.OXLON_DISABLED = self._old

    def test_marked_unavailable_with_az_note(self):
        self.assertFalse(eng_oxlon.available())
        self.assertIn("GitHub Actions", eng_oxlon.unavailable_reason())

    def test_run_returns_empty_with_note(self):
        r = eng_oxlon.run(scn.load("fx_deval10"))
        self.assertTrue(r.frame.empty)
        self.assertFalse(r.meta.get("applicable", True))
        self.assertEqual(r.meta["warnings"], [config.OXLON_DISABLED_NOTE_AZ])

    def test_scenario_without_oxlon_channels_unchanged(self):
        r = eng_oxlon.run(scn.load("mw20_2027"))
        self.assertIn("neft/tərəfdaş/məzənnə", r.meta["warnings"][0])

    def test_api_engine_list_marks_it(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
        import pu
        pu._ENG["rows"] = None
        rows = {e["id"]: e for e in pu.engines()}
        self.assertFalse(rows["oxlon"]["available"])
        self.assertEqual(rows["oxlon"]["message_az"], config.OXLON_DISABLED_NOTE_AZ)
        self.assertTrue(rows["micro"]["available"])
        pu._ENG["rows"] = None


if __name__ == "__main__":
    unittest.main()
