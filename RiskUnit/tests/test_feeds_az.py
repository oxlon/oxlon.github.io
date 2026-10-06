"""Offline tests of the Azerbaijan feeds (parsers on saved fixtures, cache fallback, status table).

    RISK_NO_NETWORK=1 python3 -m unittest tests.test_feeds_az -v
"""
import os
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["RISK_NO_NETWORK"] = "1"

from riskunit import config, feeds, feeds_az as F  # noqa: E402

FX = ROOT / "tests" / "fixtures" / "az"


def rd(name):
    return (FX / name).read_bytes()


class Parsers(unittest.TestCase):
    def test_number_formats(self):
        for s, v in (("87 709,5", 87709.5), ("20,000,000 AZN", 2e7), ("99,459.2731", 99459.2731), ("+1,2%", 1.2),
                     ("1 086,3*", 1086.3), ("1.7", 1.7)):
            self.assertAlmostEqual(F.num(s), v)
        self.assertTrue(pd.isna(F.num("x")))

    def test_cbar_fx_bulletin(self):
        d = F.parse_cbar_fx(rd("cbar_fx_2026-10-05.xml"), "2026-10-05").set_index("series")["value"]
        self.assertEqual(d["cbar_usd"], 1.7)
        self.assertAlmostEqual(d["cbar_eur"], 1.9014)
        self.assertAlmostEqual(d["cbar_rub"], 0.020238, places=6)          # nominal 100 → per 1 RUB
        self.assertGreater(d["cbar_xau"], 1000)
        self.assertTrue({f"cbar_{c.lower()}" for c in F.HEADLINE_FX} <= set(d.index))

    def test_cbar_rate_and_decisions(self):
        r = F.parse_cbar_rate(rd("cbar_corridor_percent_2026.html"), "cbar_policy_rate")
        self.assertEqual(r.iloc[0]["date"], "2026-02-05")
        self.assertEqual(r.iloc[0]["value"], 6.5)
        d = F.parse_cbar_decisions(rd("cbar_decisions.html"))
        self.assertGreater(len(d), 30)
        self.assertEqual(float(d.set_index("date").at["2026-02-04", "value"]), -0.25)
        self.assertEqual(float(d.set_index("date").at["2026-07-31", "value"]), 0.0)

    def test_dsk_macro_both_layouts(self):
        n = F.parse_dsk_macro(rd("dsk_macro_page1.html")).set_index("series")
        self.assertEqual(n.at["dsk_gdp_ytd_yoy", "date"], "2026-08-01")
        self.assertAlmostEqual(n.at["dsk_gdp_ytd_yoy", "value"], 1.2)
        self.assertAlmostEqual(n.at["dsk_gdp_nonoil_ytd_yoy", "value"], 2.1)
        self.assertAlmostEqual(n.at["dsk_budget_rev_ytd", "value"], 26486.5)
        self.assertAlmostEqual(n.at["dsk_cpi_ytd_yoy", "value"], 5.7)
        o = F.parse_dsk_macro(rd("dsk_macro_page10_oldlayout.html")).set_index("series")
        self.assertEqual(o.at["dsk_gdp_ytd_yoy", "date"], "2025-11-01")
        self.assertAlmostEqual(o.at["dsk_gdp_ytd_yoy", "value"], 1.6)      # index 101,6 → +1,6 %

    def test_dsk_cpi_release(self):
        c = F.parse_dsk_cpi(rd("dsk_cpi_release.html")).set_index("series")
        self.assertEqual(c.at["dsk_cpi_mm", "date"], "2026-08-01")
        self.assertAlmostEqual(c.at["dsk_cpi_mm", "value"], 0.2)
        self.assertAlmostEqual(c.at["dsk_cpi_yoy", "value"], 5.7)

    def test_dsk_xls_tables(self):
        a = F.parse_dsk_xls(rd("001_1en.xls"), "001_1en.xls")
        self.assertTrue(a["series"].str.startswith("dsk_a_").all())
        q = F.parse_dsk_xls(rd("03qua.xls"), "03qua.xls")
        self.assertTrue({"dsk_q_gdp_nominal", "dsk_q_gdp_real", "dsk_q_gdp_real_yoy"} <= set(q["series"]))
        with self.assertRaises(ValueError):
            F.parse_dsk_xls(b"<html>not xls</html>", "03qua.xls")

    def test_sofaz_minfin_bfb(self):
        s = F.parse_sofaz_recent(rd("sofaz_recent.html")).set_index("series")
        self.assertAlmostEqual(s.at["sofaz_assets_usd_mln", "value"], 72596.6)
        p = F.parse_sofaz_pdf_text((FX / "sofaz_h1_2026.txt").read_text(), "2026-06-30").set_index("series")["value"]
        self.assertAlmostEqual(p[[k for k in p.index if k.startswith("sofaz_class_")]].sum(), 100, delta=1)
        self.assertAlmostEqual(p["sofaz_gold_share_pct"], 31.4)
        m = F.parse_minfin_xlsx(rd("minfin_revenue_2025.xlsx"), "t").set_index(["series", "date"])["value"]
        self.assertAlmostEqual(m[("minfin_state_rev_tesdiq", "2025-01-01")], 38356)
        b = F.parse_bfb_post(rd("bfb_cbar_note_post.html"), "x")
        self.assertEqual((b["kind"], b["maturity_days"], b["avg_yield"]), ("cbar_note", 28.0, 6.5))
        self.assertEqual(b["volume_azn"], 2e7)
        mb = F.parse_bfb_post(rd("bfb_mof_bond_post.html"), "y")
        self.assertEqual(mb["kind"], "mof_bond")
        self.assertAlmostEqual(mb["avg_yield"], 7.1844)

    def test_fx_backfill_plan(self):
        d = F.fx_dates(date(2026, 10, 6), 10000, set())
        self.assertEqual(d[0], date(2026, 10, 6))
        self.assertTrue(all(x.weekday() < 5 for x in d[:400]))
        self.assertIn(date(2015, 1, 1), d)                                  # month-starts back to 2015
        self.assertEqual(len(F.fx_dates(date(2026, 10, 6), 5, set())), 5)   # per-run budget


class OfflineCache(unittest.TestCase):
    """RISK_NO_NETWORK=1: no request is made, the status says 'cache' and the last good vintage is served."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._v, self._m = config.VINTAGES, feeds.MANIFEST
        config.VINTAGES = self.tmp
        feeds.MANIFEST = self.tmp / "manifest.csv"

    def tearDown(self):
        config.VINTAGES, feeds.MANIFEST = self._v, self._m
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_get_raises_and_cache_is_used(self):
        with self.assertRaises(feeds.NoNetwork):
            feeds._get("https://www.cbar.az/currencies/05.10.2026.xml")
        F.raw_dir("cbar_rate", "2026-10-01").joinpath("decisions.html").write_bytes(rd("cbar_decisions.html"))
        self.assertEqual(F.get("https://x", "cbar_rate", "decisions.html", day="2026-10-01"), rd("cbar_decisions.html"))

    def test_fetch_records_cache_status_and_d2(self):
        man = feeds.read_manifest()
        df = F.parse_cbar_fx(rd("cbar_fx_2026-10-05.xml"), "2026-10-05")
        row = feeds._store("cbar_fx", df, "fixture", man, "2026-10-05")
        pd.DataFrame([row]).to_csv(feeds.MANIFEST, index=False)
        new = F.fetch_all_az(verbose=False, only=["cbar_fx"])
        self.assertTrue(new["status"].str.startswith("keş").all())
        st = F.feed_status_table().set_index("feed")
        self.assertEqual(st.at["cbar_fx", "son_deyer"], 1.7)
        self.assertEqual(st.at["cbar_fx", "last_obs"], "2026-10-05")
        self.assertTrue(st.at["cbar_fx", "status"].startswith("keş"))
        self.assertIn("tazelik", st.columns)


if __name__ == "__main__":
    unittest.main()
