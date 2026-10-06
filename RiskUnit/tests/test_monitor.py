"""Offline tests of the daily forecast-impact monitor (D5/D6/D7).

    RISK_NO_NETWORK=1 python3 -m unittest tests.test_monitor -v
"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["RISK_NO_NETWORK"] = "1"
os.environ["RISK_AS_OF"] = "2026-10-06"

from riskunit import config, monitor as M  # noqa: E402


def fake_feed(table):
    def f(feed, series=None):
        d = table.get((feed, series), pd.DataFrame(columns=["series", "date", "value"]))
        return d.copy()
    return f


def daily(vals, start="2026-01-01"):
    idx = pd.date_range(start, periods=len(vals), freq="D")
    return pd.DataFrame({"series": "s", "date": idx, "value": vals})


class Signals(unittest.TestCase):
    def test_signal_bands(self):
        self.assertEqual(M.signal(0.5), "normal")
        self.assertEqual(M.signal(-1.5), "diqqət ↓")
        self.assertEqual(M.signal(2.5), "xəbərdarlıq ↑")
        self.assertEqual(M.signal(np.nan), "qiymətləndirilmir")

    def test_row_deviation_and_z(self):
        r = M.row("x", "x", 110.0, pd.Timestamp("2026-10-01"), "", "src", 2026, 100.0, 5.0, "b")
        self.assertEqual((r["deviation"], r["deviation_pct"], r["z_score"]), (10.0, 10.0, 2.0))
        self.assertTrue(r["signal"].startswith("xəbərdarlıq"))


class ImpliedPaths(unittest.TestCase):
    def test_brent_ytd_plus_spot(self):
        br = daily([60.0] * 200 + [100.0] * 72)                 # last obs 2026-09-29, spot 100
        with mock.patch.object(M, "_feed", fake_feed({("brent", None): br})):
            b = M.brent_implied()
        self.assertEqual(b["spot"], 100.0)
        frac = b["spot_date"].dayofyear / 365
        ytd = (60 * 200 + 100 * 72) / 272
        self.assertAlmostEqual(b["path"][2026], ytd * frac + 100 * (1 - frac))
        self.assertEqual(b["path"][2030], 100.0)                 # flat at spot: conditional, not a forecast

    def test_policy_rate_effective_average(self):
        r = pd.DataFrame({"series": "cbar_policy_rate", "date": pd.to_datetime(["2025-12-11", "2026-02-05"]),
                          "value": [6.75, 6.5]})
        with mock.patch.object(M, "_feed", fake_feed({("cbar_rate", "cbar_policy_rate"): r})):
            p = M.policy_implied()
        self.assertEqual(p["rate"], 6.5)
        self.assertTrue(6.5 < p["path"][2026] < 6.55)            # 35 days at 6,75 then 6,5
        self.assertEqual(p["path"][2027], 6.5)


class Transmission(unittest.TestCase):
    """The impact channels are the units' own engines/elasticities; signs must match FR1 step responses."""

    def test_microunit_chain_brent(self):
        path = {y: M.base("fr1:exo:brent", y) + 10 for y in range(2026, 2031)}
        D = M.chain_impact("brent", "brent", path, "test +10")
        self.assertFalse(D.attrs["errors"])
        mods = set(D["target_id"].str.extract(r"^(fr\d+):")[0].dropna())
        self.assertTrue({"fr1", "fr3"} <= mods, mods)
        x = D.set_index(["target_id", "year"])["delta"]
        self.assertGreater(x[("fr1:rgdpnon", 2027)], 0)
        self.assertGreater(x[("fr1:rev_oil_n", 2027)], 0)
        lin = M.multiplier_impact(path).set_index(["target_id", "year"])["delta"]
        self.assertAlmostEqual(x[("fr1:rgdpnon", 2026)], lin[("fr1:rgdpnon", 2026)], delta=abs(lin[("fr1:rgdpnon", 2026)]) * 0.5)

    def test_oxlon_current_account_elasticity(self):
        D = M.macro_brent_impact({2026: M.base("mx:brent_usd", 2026) + 10})
        ca = D[D["target_id"] == "mx:current_account"].iloc[0]
        self.assertGreater(ca["delta"], 0)
        self.assertAlmostEqual(ca["delta"] / 10, 323.6, delta=5)  # mln USD per 1 USD/bbl (lo80/hi80 scenarios)


class Changes(unittest.TestCase):
    def test_day_over_day_diff(self):
        tmp = Path(tempfile.mkdtemp())
        old = config.MONITOR_HISTORY
        config.MONITOR_HISTORY = tmp
        try:
            prev = pd.DataFrame([{"indicator": "brent_spot", "label_az": "Brent", "baseline_source": "OxLon", "baseline_year": 2026,
                                  "latest": 100.0, "date": "2026-10-05", "signal": "diqqət ↑"}])
            prev.to_csv(tmp / "D5_2026-10-05.csv", index=False)
            cur = prev.assign(latest=114.0, date="2026-10-06", signal="xəbərdarlıq ↑")
            D7 = M.changes(cur, pd.DataFrame(columns=M.D6_COLS), "2026-10-06")
            r = D7[D7["kind"] == "göstərici"].iloc[0]
            self.assertEqual((r["change"], bool(r["signal_changed"]), r["reference_day"]), (14.0, True, "2026-10-05"))
        finally:
            config.MONITOR_HISTORY = old
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
