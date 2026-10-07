"""FR4 tests (offline: POLICY_NO_NETWORK=1, no RiskUnit server needed). python3 -m unittest tests.test_fr4"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ["POLICY_NO_NETWORK"] = "1"
os.environ.setdefault("POLICY_FR4_WORKERS", "0")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from policyunit import risk_link as RL, sensitivity as SN, side_effects as S  # noqa: E402
from policyunit.integrate import P1_COLS  # noqa: E402

Y = [2027, 2028, 2029, 2030]


def frame(rows, sid="t"):
    out = []
    for ind, unit, base, dpct in rows:
        for y in Y:
            d = base * dpct / 100 if unit not in ("%", "% ÜDM") else dpct
            hz = "qısa" if y - 2027 <= 1 else "orta"
            out.append({"scenario": sid, "scenario_name": "test", "start_year": 2027, "engine": "micro", "horizon": hz,
                        "indicator": ind, "label_az": ind, "unit": unit, "year": y, "baseline": base,
                        "value": base + d, "delta": d, "delta_pct": dpct, "method": "t", "tier": "C",
                        "group": "", "note_az": ""})
    return pd.DataFrame(out, columns=P1_COLS)


MW = {"id": "t", "name_az": "test", "start_year": 2027,
      "instruments": [{"instrument": "min_wage", "years": Y, "size": 20, "unit": "pct", "target": None,
                       "financing": None}]}


class Rules(unittest.TestCase):
    def test_library_valid_and_families(self):
        r = S.load_rules()
        self.assertGreaterEqual(len(r), 20)
        self.assertEqual(set(r.family), set(S.FAMILIES))          # all ten families covered

    def test_bad_rule_rejected(self):
        r = pd.read_csv(S.RULES_CSV, dtype=str, keep_default_na=False)
        r.loc[0, "metric"] = "yoxdur"
        r.loc[1, "thresholds"] = "3;2;1;0"
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            r.to_csv(f.name, index=False)
        with self.assertRaises(S.RuleError) as cm:
            S.load_rules(f.name)
        self.assertIn("naməlum metrika", str(cm.exception))
        self.assertIn("monoton", str(cm.exception))

    def test_evaluate_min_wage(self):
        f = frame([("infl", "%", 5.0, 3.0), ("employment_hired", "min nəfər", 1800.0, 0.05),
                   ("cpi", "2015 = 100", 200.0, 2.9)])
        se = {x["rule_id"]: x for x in S.evaluate(MW, f)}
        self.assertIn("SE04", se)
        self.assertEqual(se["SE04"]["severity"], 4)               # +3 pp > 2 pp
        p = S._params(S.load_rules().set_index("id").loc["SE08", "params"])
        exp = p["eps_mid"] * 20 * p["bound_share"] * 1800 / 100
        self.assertAlmostEqual(se["SE08"]["value"], exp, places=3)
        self.assertEqual(se["SE08"]["tier"], "D")
        self.assertIn("kanal YOXDUR", se["SE08"]["explanation_az"])
        self.assertEqual(se["SE20"]["family"], "sosial bölgü")    # fixed-income inflation loss

    def test_severity_less_than(self):
        self.assertEqual(S._severity(-0.6, "<", [-0.25, -0.5, -1, -2]), 2)
        self.assertEqual(S._severity(0.1, "<", [-0.25, -0.5, -1, -2]), 0)

    def test_diff_policy_under_condition(self):
        f2 = frame([("gdp_real", "mln AZN 2015", 100.0, 3.0)])
        f3 = frame([("gdp_real", "mln AZN 2015", 100.0, 1.0)])
        d = S._diff(f2, f3)
        self.assertTrue(np.allclose(d.delta, 2.0))
        self.assertTrue(np.allclose(d.delta_pct, 100 * 2 / 101))


class Sobol(unittest.TestCase):
    def test_ishigami(self):
        a, b = 7.0, 0.1

        def f(Z):
            X = -np.pi + 2 * np.pi * Z
            return (np.sin(X[:, 0]) + a * np.sin(X[:, 1]) ** 2 + b * X[:, 2] ** 4 * np.sin(X[:, 0]))[:, None]
        S1, ST, _ = SN.saltelli(f, [[0], [1], [2]], lambda r, n: r.random((n, 3)), 2 ** 14, np.random.default_rng(1))
        np.testing.assert_allclose(S1[:, 0], [0.314, 0.442, 0.0], atol=0.04)
        np.testing.assert_allclose(ST[:, 0], [0.558, 0.442, 0.244], atol=0.04)

    def test_io_block(self):
        from policyunit import scenario as scn
        r = SN.io_block(scn.load("pubinv1bn_deficit"), N=128)
        self.assertIsNotNone(r)
        self.assertTrue(np.all(np.isfinite(r["ST"])))
        self.assertGreater(r["H0"][0], 0)                         # VA effect positive


class StubClient:
    offline = True

    def __init__(self, dist=True):
        self.dist = dist

    def alive(self):
        return False

    def call(self, method, path, body=None, use_cache_first=False):
        if path == "optimize/inputs":
            return {"measures": [{"tedbir_id": "T19", "tedbir": "AMB reaksiyası", "risk_idler": "R12",
                                  "strategiya_v2": "azaltma", "mesul": "AMB", "xerc_mln_azn": 0.0,
                                  "status": "planlaşdırılıb", "effekt_modeli": "rate_response"}]}, "keş (test)", "t"
        if path == "stress/run" and self.dist:
            q = {"p05": 0.0, "p10": 1.0, "p25": 3.0, "p50": 5.0, "p75": 7.0, "p90": 9.0, "p95": 10.0}
            dist = [{"baxis": "şərtsiz", "kind": k, "il": y, "baza": 5.0, **q, "P_hedd": 0.15,
                     "hedd": "> 6" if k == "cpi" else "< 2"} for k in ("g", "cpi", "fis") for y in range(2026, 2031)]
            met = {k: {"şərtsiz": {"P_hedd": 0.15, "ES10": -0.5, "median": 5.0}} for k in ("g", "cpi", "fis")}
            ru = {"distribution": dist, "metrics": met}
            if (body or {}).get("micro_overrides"):            # RiskUnit's own policy view (+1 pp inflation)
                q2 = {k: v + 1.0 for k, v in q.items()}
                ru["distribution"] = dist + [{"baxis": "siyasətlə", "kind": "cpi", "il": y, "baza": 5.0, **q2,
                                              "P_hedd": 0.25, "ES10": 16.0, "hedd": "> 6"} for y in range(2026, 2031)]
                ru["policy_shift"] = [{"kind": "cpi", "il": y, "deyisme": 1.0} for y in range(2026, 2031)]
            return {"score_year": 2027, "baseline_id": "B-test", "ru": ru, "micro": None}, "keş (test)", "t"
        return None, "əlçatmaz (test)", ""


class Risk(unittest.TestCase):
    def test_offline_client_status(self):
        c = RL.Client(offline=True)
        r, st, _ = c.call("POST", "stress/run", {"test": "heç vaxt keşlənməyib-unikal-" + str(os.getpid())})
        self.assertIsNone(r)
        self.assertIn("əlçatmaz", st)

    def test_profile_location_shift(self):
        f = frame([("infl", "%", 5.0, 1.0), ("gdp_nonoil_real", "mln AZN 2015", 100.0, 0.0),
                   ("budget_balance_pct", "% ÜDM", 0.3, 0.0)])
        p = RL.profile(StubClient(), MW, f, None, [], {})
        c = p[(p.kind == "cpi") & (p.year == 2027)].iloc[0]
        self.assertAlmostEqual(c.dES10, 1.0)
        self.assertGreater(c.P_with, c.P_without)                  # inflation +1 pp raises P(cpi > 6)
        g = p[(p.kind == "g") & (p.year == 2028)].iloc[0]
        self.assertAlmostEqual(g.P_with, g.P_without, places=6)    # no shift -> same probability
        self.assertEqual(c.es_method.split()[0], "RiskUnit")

    def test_profile_riskunit_policy_view(self):
        f = frame([("infl", "%", 5.0, 1.0)])
        orig = RL.primary_source
        RL.primary_source = lambda s, ov: ("RiskUnit", "(a) test")
        try:
            p = RL.profile(StubClient(), MW, f, {"FR1": {"exogenous": {"minwage": {"pct": [0, 20, 20, 20, 20]}}}}, [], {})
        finally:
            RL.primary_source = orig
        c = p[(p.kind == "cpi") & (p.year == 2027)].iloc[0]
        self.assertEqual(c.esas_menbe, "RiskUnit")
        self.assertAlmostEqual(c.P_with_ru, 0.25)
        self.assertTrue(c.source.startswith("RiskUnit"))
        self.assertAlmostEqual(c.P_with, 0.25)                     # RiskUnit figure is primary
        self.assertAlmostEqual(c.ru_policy_shift, 1.0)
        self.assertAlmostEqual(c.shift_pu, 1.0)                    # PolicyUnit cross-check kept
        self.assertAlmostEqual(c.agree_dP, abs(c.dP - c.dP_pu))
        g = p[(p.kind == "g") & (p.year == 2027)].iloc[0]
        self.assertTrue(g.source.startswith("PolicyUnit"))         # no RiskUnit policy row -> fallback

    def test_primary_source_rule(self):
        from policyunit import scenario as scn
        fx = RL.primary_source(scn.load("fx_deval10"), {"FR1": {"exogenous": {"fx": {"pct": [0, 10, 10, 10, 10]}}}})
        self.assertEqual(fx[0], "RiskUnit")
        self.assertIn("riskunit/fx.py", fx[1])                      # (c) FX pass-through layer
        sof = scn.load("pubinv1bn_sofaz")
        self.assertEqual(RL.primary_source(sof, {"FR1": {"exogenous": {"istate_add": {"add": [1] * 5}}}})[0], "PolicyUnit")
        self.assertEqual(RL.primary_source(scn.load("vat_minus2"), None)[0], "PolicyUnit")

    def test_profile_fallback_when_overrides_rejected(self):
        class Rejecting(StubClient):
            def call(self, method, path, body=None, use_cache_first=False):
                if path == "stress/run" and (body or {}).get("micro_overrides"):
                    return None, "RiskUnit xətası 422: test", ""
                return super().call(method, path, body, use_cache_first)
        f = frame([("infl", "%", 5.0, 1.0)])
        p = RL.profile(Rejecting(), MW, f, {"FR1": {"exogenous": {"dsmf_add_g": {"add": [1] * 5}}}}, [], {})
        c = p[(p.kind == "cpi") & (p.year == 2027)].iloc[0]
        self.assertEqual(c.esas_menbe, "PolicyUnit")
        self.assertGreater(c.P_with, c.P_without)
        self.assertIn("alınmadı", c.status)

    def test_fallback_port_range(self):
        import socket
        p = RL.free_port()
        self.assertIn(int(p), range(8793, 8800))
        self.assertNotIn(8792, RL.FALLBACK_PORTS)
        with socket.socket() as s:                                  # an occupied port is skipped
            s.bind(("127.0.0.1", int(p)))
            s.listen(1)
            self.assertNotEqual(RL.free_port(), p)

    def test_purge_stale_cache(self):
        import json as js
        orig = RL.CACHE
        with tempfile.TemporaryDirectory() as d:
            RL.CACHE = Path(d)
            try:
                (RL.CACHE / "a.json").write_text(js.dumps({"baseline_id": "B-old", "response": {}}))
                (RL.CACHE / "b.json").write_text(js.dumps({"response": {"baseline_id": "B-new"}}))
                self.assertEqual(RL.purge_stale("B-new", log=lambda *_: None), 1)
                self.assertEqual([f.name for f in RL.CACHE.glob("*.json")], ["b.json"])
            finally:
                RL.CACHE = orig

    def test_unavailable_profile_and_mitigation(self):
        f = frame([("infl", "%", 5.0, 3.0)])
        p = RL.profile(StubClient(dist=False), MW, f, None, [], {})
        self.assertTrue(p.status.str.contains("əlçatmaz").all())
        se = S.evaluate(MW, f)
        m = RL.mitigate(StubClient(), MW, se, p)
        self.assertTrue((m.source == "siyasətə xas təklif (mitigation_map.csv)").any())
        self.assertIn("T19", set(m.measure_id))
        self.assertTrue(m.status.str.contains("əlçatmaz").any())  # optimize/run unavailable is reported
        k = {x["kpi"]: x["value"] for x in RL.kpi_inputs("t", se, p, 2027)}
        self.assertEqual(k["side_effects"], len(se))


class Variants(unittest.TestCase):
    def test_specs(self):
        from policyunit import scenario as scn
        v = {x["id"]: x for x in S.variant_specs(scn.load("pubinv1bn_deficit"), {"FR1.D1_cons|ln_hhdisp_pc": 0.5})}
        self.assertEqual(set(v), {"oil_m1s", "fx_p1s", "weak_coef", "fin_alt"})
        self.assertEqual(v["fin_alt"]["instruments"][0]["financing"], "tax")
        self.assertLess(v["oil_m1s"]["cond"]["FR1"]["exogenous"]["brent"]["pct"][1], -20)
        v2 = {x["id"] for x in S.variant_specs(scn.load("fx_deval10"))}
        self.assertNotIn("fx_p1s", v2)                             # no double devaluation


if __name__ == "__main__":
    unittest.main()
