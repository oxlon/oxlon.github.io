"""Engines: state round trip, overrides (values / pct / bounds / coefficients), selftest_compare, chain."""
import os
import sys
import types

import numpy as np
import pandas as pd

from microlib.engines import base as B
from microlib.engines import chain as C

from ._harness import approx, check, tmpdir

YEARS = [2026, 2027, 2028, 2029, 2030]
CAT = {"exogenous": [{"id": "brent", "label_az": "Brent", "unit": "$", "years": YEARS,
                      "baseline": {"Baseline": [80, 78, 76, 75, 75], "Adverse": [60, 55, 55, 55, 55]},
                      "min": 20, "max": 150, "step": 1}],
       "coefficients": [{"eq_id": "FR1.C3_man", "name": "ln_K", "label_az": "kapital", "value": 0.4, "se": 0.1,
                         "ci_low": 0.2, "ci_high": 0.6, "editable": True},
                        {"eq_id": "FR1.C3_man", "name": "const", "value": 0.3, "editable": False}],
       "levers": [{"id": "tax_rate", "label_az": "vergi", "value": 0.2, "min": 0.0, "max": 0.5}]}


def test_state_roundtrip():
    d = tmpdir()
    idx = pd.MultiIndex.from_tuples([("a", 2020), ("b", 2021)], names=["k", "year"])
    st = {"coef": {"C3": pd.Series([0.3, 0.4], index=["const", "ln_K"], name="b")},
          "hist": pd.DataFrame({"y": [1.0, np.nan], "lab": ["x", "y"]}, index=[2024, 2025]),
          "num": pd.DataFrame({"a": [1.0, 2.0]}, index=idx), "arr": np.arange(6.0).reshape(2, 3),
          "scal": float("nan"), "names": ("x", "y"), "n": np.int64(3)}
    B.save_state("FR1", st, out_dir=d)
    check(os.path.exists(os.path.join(d, "FR1_state.json")) and os.path.exists(os.path.join(d, "FR1_state.npz")), "files")
    back = B.load_state("FR1", in_dir=d)
    pd.testing.assert_series_equal(back["coef"]["C3"], st["coef"]["C3"])
    check(back["hist"]["lab"].tolist() == ["x", "y"] and np.isnan(back["hist"]["y"].iloc[1]), "mixed frame")
    pd.testing.assert_frame_equal(back["num"], st["num"])
    approx(back["arr"], st["arr"])
    check(np.isnan(back["scal"]) and back["names"] == ["x", "y"] and back["n"] == 3, "scalars")


def test_overrides():
    r = B.apply_overrides(CAT, {}, "Adverse")
    approx(r["exogenous"]["brent"], [60, 55, 55, 55, 55])
    r = B.apply_overrides(CAT, {"exogenous": {"brent": {"pct": -10}}})
    approx(r["exogenous"]["brent"], np.array([80, 78, 76, 75, 75]) * 0.9)
    r = B.apply_overrides(CAT, {"exogenous": {"brent": [200, 10, 70, 70, 70]}})
    approx(r["exogenous"]["brent"], [150, 20, 70, 70, 70])
    check(any("sərhəd" in w for w in r["warnings"]), "clip warning")
    r = B.apply_overrides(CAT, {"exogenous": {"brent": {"2028": 90}, "nope": [1]}})
    approx(r["exogenous"]["brent"], [80, 78, 90, 75, 75])
    check(any("nope" in w for w in r["warnings"]), "unknown id warning")
    r = B.apply_overrides(CAT, {"exogenous": {"brent": [1, 2]}})
    check(any("5 dəyər" in w for w in r["warnings"]) and r["exogenous"]["brent"][0] == 80, "length check")
    r = B.apply_overrides(CAT, {"coefficients": {"FR1.C3_man|ln_K": 0.9, "FR1.C3_man|const": 1.0, "X|y": 1},
                                "levers": {"tax_rate": 0.9}})
    check(B.coef_value(r, "FR1.C3_man", "ln_K") == 0.9, "coef applied")
    check(any("etibarlılıq intervalından kənar" in w for w in r["warnings"]), "outside-CI flagged")
    check(r["coefficients"]["FR1.C3_man|const"] == 0.3 and any("redaktə" in w for w in r["warnings"]), "non-editable")
    check(r["levers"]["tax_rate"] == 0.5, "lever clipped")


def test_selftest_compare_and_result_format():
    d = tmpdir()
    ref = pd.DataFrame({"scenario": ["Baseline"] * 3, "year": [2026, 2027, 2028], "rgdp": [1.0, 2.0, 3.0]})
    p = os.path.join(d, "x.csv")
    ref.to_csv(p, index=False)
    ok = B.selftest_compare(ref.copy(), p, ["rgdp"], on=["scenario", "year"])
    check(ok["ok"] and ok["max_rel_diff"] == 0 and ok["n_rows"] == 3, str(ok))
    bad = ref.copy()
    bad.loc[1, "rgdp"] += 1e-6
    r = B.selftest_compare(bad, p, ["rgdp"], on=["scenario", "year"])
    check(not r["ok"] and r["max_rel_diff"] > 1e-8, "detects 1e-6 drift")
    r = B.selftest_compare(ref.set_index("year")[["rgdp"]], p, {"rgdp": "rgdp"}, index_col="year")
    check(r["ok"], f"index alignment {r}")
    res = B.make_result({"fr1:rgdp": pd.Series([1.0, np.nan], index=[2026, 2027])}, meta={"scenario": "Baseline"})
    check(res["series"]["fr1:rgdp"] == {"2026": 1.0, "2027": None} and B.validate_result(res, "FR1") == [], "result")
    check(B.validate_result({"series": {"rgdp": {}}, "meta": {}, "warnings": []}) != [], "bad id caught")
    check(list(B.result_to_frame(res).index) == [2026, 2027], "to frame")


def test_chain_skips_missing_and_passes_upstream():
    out = C.run_chain({}, "Baseline")
    present = C.available_engines()
    check(set(out["skipped"]) == set(C.ORDER) - set(present), "missing engines skipped")
    seen = {}

    def fake(mod):
        m = types.ModuleType(f"microlib.engines.{mod.lower()}")

        def run(overrides, scenario="Baseline", upstream=None):
            seen[mod] = sorted((upstream or {}).keys())
            return B.make_result({f"{mod.lower()}:x": {2026: 1.0}}, warnings=[f"w{mod}"])
        m.run = run
        return m

    saved = {k: sys.modules.get(f"microlib.engines.{k.lower()}") for k in ("FR1", "FR10", "FR12")}
    try:
        for k in saved:
            sys.modules[f"microlib.engines.{k.lower()}"] = fake(k)
        out = C.run_chain({"FR1": {"exogenous": {}}}, "Adverse", modules=["FR1", "FR10", "FR12"])
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(f"microlib.engines.{k.lower()}", None)
            else:
                sys.modules[f"microlib.engines.{k.lower()}"] = v
    check(out["order"] == ["FR1", "FR10", "FR12"], str(out["order"]))
    check(seen == {"FR1": [], "FR10": ["FR1"], "FR12": ["FR1", "FR10"]}, f"upstream {seen}")
    check("FR12: wFR12" in out["warnings"], "engine warnings propagated")
