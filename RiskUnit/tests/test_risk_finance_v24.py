"""Offline tests of the v2.4 audit fixes (M4 objective, M5 hedge, M7 DSA/CaR/VaR, M8 feed status).

    RISK_NO_NETWORK=1 python3 -m unittest tests.test_risk_finance_v24 -v
"""
import os
import sys
import unittest
import urllib.error
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["RISK_NO_NETWORK"] = "1"

from riskunit import config, dsa, feeds, feeds_az, parametrler, var  # noqa: E402

OUT = config.OUTPUT


class Parameters(unittest.TestCase):
    def test_file_has_source_and_justification(self):
        t = parametrler.table()
        self.assertTrue({"acar", "deyer", "vahid", "izah", "menbe", "esaslandirma", "modul", "status"} <= set(t.columns))
        for k in ("dsa_int_eff", "dsa_amort_ext", "car_cbar_deval_drain", "car_carry_equities", "var_re_beta",
                  "sim_f_obs_growth", "sim_transition_drift", "hedge_strike_ratio", "obj_fk_tail_weight"):
            self.assertIn(k, set(t["acar"]), k)
        self.assertTrue(t["menbe"].str.len().gt(3).all())

    def test_modules_read_the_file(self):
        self.assertAlmostEqual(dsa.INT_EFF, parametrler.get("dsa_int_eff"))
        self.assertAlmostEqual(dsa.AMORT_EXT, parametrler.get("dsa_amort_ext"))
        self.assertAlmostEqual(var.RE_BETA, parametrler.get("var_re_beta"))
        self.assertEqual(parametrler.get("no_such_key", 7.0), 7.0)


class FeedStatus(unittest.TestCase):
    def test_core_failure_is_stage_error(self):
        glob = [k for k in feeds_az.GLOBAL_FEEDS if k != "azeri_light"]
        rows = pd.DataFrame({"feed": glob, "status": ["xeta: URLError: timed out"] * len(glob)})
        lvl = feeds_az.stage_level(glob, attempted=rows)
        self.assertTrue(lvl.startswith("xəta"), lvl)                   # brent is core
        self.assertIn("brent", lvl)

    def test_noncore_failure_is_warning_and_offline_is_ok(self):
        self.assertEqual(feeds_az.row_level("xeta: URLError", "təzə", False), "xəbərdarlıq")
        self.assertEqual(feeds_az.row_level("keş: şəbəkə yoxdur", "təzə", True), "ok")
        self.assertEqual(feeds_az.row_level("ok", "köhnə", True), "xəta")
        self.assertEqual(feeds_az.row_level("ok", "köhnə", False), "xəbərdarlıq")

    def test_freshness_rules_by_frequency(self):
        today = pd.Timestamp("2026-10-06")
        q = feeds_az.freshness("dsk_tables", "rüblük", "2026-04-01", None, today)
        self.assertEqual(q["dovr_sonu"], "2026-06-30")               # age counted from the END of the quarter
        self.assertEqual(q["tazelik"], "təzə")
        old = feeds_az.freshness("dsk_tables", "rüblük", "2025-10-01", None, today)
        self.assertEqual(old["tazelik"], "köhnə")
        d = feeds_az.freshness("brent", "gündəlik", "2026-09-10", None, today)
        self.assertEqual(d["tazelik"], "köhnə")
        e = feeds_az.freshness("cbar_rate", "hadisə", "2026-02-05", "2026-10-06T01:00:00Z", today)
        self.assertEqual(e["tazelik"], "təzə")                       # events: age of the last successful check

    def test_dead_host_breaker(self):
        calls = []
        orig = feeds._get_once
        os.environ["RISK_NO_NETWORK"] = "0"
        try:
            def boom(url, host, timeout, ua):
                calls.append(url)
                raise urllib.error.URLError("simulated outage")
            feeds._get_once = boom
            feeds._DEAD_HOSTS.clear()
            with self.assertRaises(urllib.error.URLError):
                feeds._get("https://example.invalid/a")
            self.assertEqual(len(calls), 2)                          # one retry
            with self.assertRaises(feeds.HostDown):
                feeds._get("https://example.invalid/b")
            self.assertEqual(len(calls), 2)                          # no further request to a dead host
            self.assertIn("simulated outage", feeds._fail_status(urllib.error.URLError("simulated outage")))
        finally:
            feeds._get_once = orig
            feeds._DEAD_HOSTS.clear()
            os.environ["RISK_NO_NETWORK"] = "1"


class Runner(unittest.TestCase):
    def test_check_propagates_to_stage(self):
        import importlib.util                                         # by path: MicroUnit (on sys.path) has its own run_all
        spec = importlib.util.spec_from_file_location("ru_run_all", ROOT / "run_all.py")
        run_all = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(run_all)
        R = run_all.Runner(verbose=False)
        R("X1", "test", lambda: 1, False, check=lambda o: "xəta: brent (xeta: URLError)")
        R("X2", "test", lambda: 1, False, check=lambda o: "xəbərdarlıq: vix")
        R("X3", "test", lambda: 1, False)
        self.assertEqual([r["seviyye"] for r in R.rows], ["xəta", "xəbərdarlıq", "ok"])


class Verification(unittest.TestCase):
    def test_backtest_due_on_new_vintage(self):
        from riskunit import backtest
        if not backtest.REGISTER.exists():
            self.skipTest("reyestr yoxdur")
        reg = pd.read_csv(backtest.REGISTER, dtype=str)
        blk = reg[reg["rub"] == backtest.quarter()]
        if blk.empty:
            self.assertTrue(backtest.due("B-x"))
        else:
            self.assertTrue(backtest.due("B-heç-vaxt-olmayan"))
            self.assertEqual(backtest.due(blk["baseline_id"].iloc[0]), blk["baseline_id"].nunique() != 1)

    def test_pdf_label_marks_other_baseline(self):
        from riskunit import report
        lab = report.pdf_label("rehberlik", {"baseline_id": "B-heç-vaxt-olmayan"})
        self.assertTrue("KÖHNƏ" in lab or "naməlum" in lab)

    def test_docs_varcar_blocks(self):
        from riskunit import docs_varcar
        b = docs_varcar.blocks()
        if (OUT / "K3_dsa_fan.csv").exists():
            self.assertIn("vc_dsa", b)


class DebtStart(unittest.TestCase):
    def test_start_is_fr1_end_of_last_actual_year(self):
        V1 = pd.DataFrame([{"kod": "debt_public_total", "mln_azn": 23830.6, "mln_usd": 14018.0, "deyer": 23830.6,
                            "pay_faiz": None, "tarix": "2026-07-01"}])
        st = dsa.start_stock(V1)
        self.assertEqual(st["year_end"], config.LAST_ACTUAL)
        self.assertAlmostEqual(st["D0"], 25987.45, delta=1.0)
        self.assertAlmostEqual(st["check"], 23830.6, delta=1.0)

    @unittest.skipUnless((OUT / "K3_dsa_fan.csv").exists(), "K3 yoxdur")
    def test_k3_informative_thresholds_and_variants(self):
        k = pd.read_csv(OUT / "K3_dsa_fan.csv")
        for c in ("P_borc_gt_20", "P_borc_gt_25", "P_GFN_gt_5", "P_GFN_gt_15", "borc_xidmeti_gelir_p95",
                  "yoxlama_MN_bulleten_mln_azn", "baslangic_qaliq_mln_azn"):
            self.assertIn(c, k.columns)
        self.assertFalse(k["variant"].str.contains("investisiya reaksiyası xaric").any())
        self.assertTrue((k["P_borc_gt_20"] >= k["P_borc_gt_25"]).all())
        b = k[k["variant"].str.startswith("əsas: RU")]
        np.testing.assert_allclose(b["baza_FR1_MN"], b["FR1_borc_ÜDM"], atol=0.5)   # same anchor as FR1


@unittest.skipUnless((OUT / "K5_cca.csv").exists() and (OUT / "V3_var_es.csv").exists(), "çıxışlar yoxdur")
class Outputs(unittest.TestCase):
    def test_cca_demoted_with_note(self):
        k = pd.read_csv(OUT / "K5_cca.csv")
        self.assertTrue(k["status"].str.startswith("ƏLAVƏ").all())
        self.assertTrue(k["variant"].str.contains("yenidən qurulmuş").any())

    def test_evt_overlap_flagged_and_oil_anchor(self):
        v = pd.read_csv(OUT / "V3_var_es.csv")
        self.assertIn("etibarli", v.columns)
        e = v[(v["horizont"] == "1il") & (v["metod"] == "evt")]
        self.assertFalse(e["etibarli"].astype(bool).any())
        o = v[v["portfel"] == "oil_rev"]
        self.assertTrue(o["qeyd"].str.contains("vahid lövbər").all())


if __name__ == "__main__":
    unittest.main()
