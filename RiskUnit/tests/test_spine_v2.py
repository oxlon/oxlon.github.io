"""Offline tests of the v2 data spine: macro path switch, manifest, upstream tidy store (D1), consensus (D3).

    RISK_NO_NETWORK=1 python3 -m unittest tests.test_spine_v2 -v
"""
import hashlib
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["RISK_NO_NETWORK"] = "1"

from riskunit import config, consensus, spine, upstream  # noqa: E402


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class MacroPath(unittest.TestCase):
    def test_delivery_contract_is_default_and_complete(self):
        if "MIIS_MACRO_DIR" not in os.environ:
            self.assertEqual(config.MACRO_DIR.name, "delivery")
        for p in {**config.MACRO_FILES, **config.MACRO_FILES_V2}.values():
            self.assertTrue(p.exists(), p)

    def test_hash_identical_to_former_18august_copy(self):
        old = config.PROJECT.parents[0] / "18august" / "model"
        if not old.exists():
            self.skipTest("18august/model mövcud deyil")
        pairs = {"forecast_long": "outputs/forecast_long.csv", "validation_backtest": "outputs/validation_backtest.csv",
                 "assumptions": "data/assumptions.csv", "external_block": "data/external_block_annual.csv",
                 "monthly_panel": "data/monthly_panel.csv", "public_panel": "data/public_sources_panel.csv"}
        for k, rel in pairs.items():
            self.assertEqual(sha(config.MACRO_FILES[k]), sha(old / rel), k)

    def test_layout_detection(self):
        o, d = config._macro_layout(config.PROJECT / "Macro_OxLon" / "model")
        self.assertEqual((o.name, d.name), ("outputs", "data"))

    def test_manifest_has_all_units(self):
        m = spine.manifest()
        self.assertTrue({"makro §15.5.1", "mikro §15.5.2", "nazirlik (MU)"} <= set(m["unit"]))
        self.assertTrue((m[m["key"].isin(config.MINISTRY_FILES)]["sha256"].str.len() == 64).all())
        self.assertRegex(spine.baseline_id(), r"^B-[0-9a-f]{10}$")


class UpstreamStore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.S = upstream.store()
        cls.C = upstream.catalog(cls.S)

    def test_ids_and_coverage(self):
        ids = self.C["id"]
        self.assertGreater((ids.str.startswith("mx:")).sum(), 500)
        self.assertGreater((ids.str.startswith("mn:")).sum(), 300)
        micro = ids[ids.str.match(r"^fr\d+:")]
        self.assertGreaterEqual(len(micro), 1500)
        for k in (1, 3, 4, 5, 10, 12):
            self.assertTrue(micro.str.startswith(f"fr{k}:").any(), k)
        self.assertTrue(ids.is_unique)
        self.assertEqual(list(self.C.columns[:6]), ["id", "source", "label_az", "unit", "years", "forecast_years"])

    def test_bands_and_baselines(self):
        c = self.C.set_index("id")
        self.assertTrue(c.at["mx:brent_usd", "has_band"])
        b = upstream.series("mx:brent_usd")
        self.assertAlmostEqual(float(b[b["year"] == 2026]["value"].iloc[0]), 68.98, places=2)
        self.assertTrue(upstream.series("fr1:exo:brent").size)               # FR1 engine assumption
        caem = self.S[self.S["row_ref"] == "CAEM.xlsx/Oil_and_gas_sector!R69"]
        self.assertAlmostEqual(float(caem[caem["year"] == 2026]["value"].iloc[0]), 65.86, places=1)

    def test_generic_sheet_parser(self):
        rows = [("Title", None, None, None), (None, None, 2023, 2024, 2025, 2026), ("ÜDM", "mln AZN", 0.5, 1.0, 2.0, 3.0),
                ("real artım tempi", "%", None, 4.0, "#REF!", 5.0), ("Section", None, None, None, None),
                ("ÜDM", "mln AZN", 6, 7, 8, 9)]
        r = pd.DataFrame(upstream.parse_sheet(rows, "t:", "test", "ref", first_forecast=2025, max_label_col=2))
        self.assertEqual(sorted(r["id"].unique()), ["t:udm", "t:udm.mln_azn", "t:udm.real_artim_tempi"])
        self.assertEqual(len(r[r["id"] == "t:udm.real_artim_tempi"]), 2)   # '#REF!' dropped
        self.assertEqual(set(r[r["year"] >= 2025]["kind"]), {"forecast"})

    def test_rebuild_when_upstream_hash_changes(self):
        self.assertFalse(upstream.is_stale())
        meta = upstream.STORE_META.read_text()
        try:
            upstream.STORE_META.write_text(meta.replace('"micro:fr1_tidy": "', '"micro:fr1_tidy": "x', 1))
            self.assertTrue(upstream.is_stale())
        finally:
            upstream.STORE_META.write_text(meta)


class Consensus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.L = consensus.flag(consensus.extract(), upstream.store())
        cls.D = consensus.build()

    def test_table_shape_and_statistics(self):
        self.assertEqual(set(self.D["year"]), set(range(2025, 2031)))
        self.assertTrue(set(consensus.V) <= set(self.D["variable"]))
        ok = self.D.dropna(subset=["spread"])
        self.assertTrue(np.allclose(ok["spread"], ok["max"] - ok["min"]))
        self.assertTrue(self.D["model_risk"].isin(["aşağı", "orta", "yüksək", "qiymətləndirilmir"]).all())

    def test_documented_defects_are_flagged(self):
        f = self.L.set_index(["variable", "source", "year"])["flag"]
        self.assertEqual(f[("cpi_inflation", "bu60", 2027)], "qeyri-real")        # = trade deflator row
        self.assertEqual(f[("current_account_pct_gdp", "caem", 2029)], "qeyri-real")
        self.assertEqual(f[("cpi_inflation", "oxlon", 2027)], "")

    def test_model_risk_indicator(self):
        M = consensus.model_risk(self.D)
        self.assertTrue((M["risk_adi"] == "Proqnoz qeyri-müəyyənliyi / model riski").all())
        self.assertTrue(M["disagreement_index"].notna().all())


class Catalog(unittest.TestCase):
    def test_register_output_upserts_one_row_per_file(self):
        tmp = Path(tempfile.mkdtemp())
        old = config.CATALOG_V2
        config.CATALOG_V2 = tmp / "_catalog_v2.csv"
        try:
            spine.register_output("D9_x.csv", "t", "a", ["a", "b"])
            spine.register_output("D9_x.csv", "t", "b", ["a"])
            c = pd.read_csv(config.CATALOG_V2)
            self.assertEqual(len(c), 1)
            self.assertEqual(c.iloc[0]["description_az"], "b")
        finally:
            config.CATALOG_V2 = old
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
