"""Engine helpers (contract section B): state save/load (JSON + NPZ, plain data only, no pickle),
override application with bounds and warnings, self-test comparison against notebook CSVs, and the
standard result format {"series": {id: {year: v}}, "meta": {...}, "warnings": [...]}."""
from __future__ import annotations

import numpy as np

from ._state import engine_dir, load_state, save_state  # noqa: F401


# ------------------------------------------------------------------ overrides
def _clip(v, lo, hi):
    a = np.asarray(v, float)
    if lo is not None:
        a = np.maximum(a, lo)
    if hi is not None:
        a = np.minimum(a, hi)
    return a


def _exo_value(spec, base, years):
    base = np.asarray(base, float)
    if isinstance(spec, dict):
        if "pct" in spec:
            return base * (1 + np.asarray(spec["pct"], float) / 100.0)
        if "add" in spec:
            return base + np.asarray(spec["add"], float)
        if "values" in spec:
            return np.asarray(spec["values"], float)
        out = base.copy()  # {year: value} partial override
        for y, v in spec.items():
            out[list(years).index(int(y))] = float(v)
        return out
    return np.asarray(spec, float) * np.ones(len(years)) if np.ndim(spec) == 0 else np.asarray(spec, float)


def apply_overrides(catalogue, overrides=None, scenario="Baseline"):
    """catalogue = engine.inputs(). Returns {"exogenous": {id: array}, "coefficients": {"EQ|name": v},
    "levers": {id: v}, "changed": [...], "warnings": [...]}. Unknown ids and non-editable coefficients are
    ignored with a warning; values outside [min, max] are clipped; coefficients outside the 95% CI are
    allowed but flagged."""
    ov = overrides or {}
    W, changed = [], []
    exo = {}
    for e in catalogue.get("exogenous", []):
        b = e["baseline"].get(scenario, e["baseline"].get("Baseline"))
        exo[e["id"]] = np.asarray(b, float)
    ex_cat = {e["id"]: e for e in catalogue.get("exogenous", [])}
    for k, spec in (ov.get("exogenous") or {}).items():
        if k not in ex_cat:
            W.append(f"naməlum ekzogen dəyişən '{k}' — nəzərə alınmadı")
            continue
        e = ex_cat[k]
        try:
            v = _exo_value(spec, exo[k], e["years"])
        except (ValueError, IndexError, TypeError) as err:
            W.append(f"{k}: yanlış dəyər ({err}) — nəzərə alınmadı")
            continue
        if v.shape != exo[k].shape:
            W.append(f"{k}: {len(e['years'])} dəyər gözlənilirdi, {v.size} verildi — nəzərə alınmadı")
            continue
        c = _clip(v, e.get("min"), e.get("max"))
        if not np.allclose(c, v, equal_nan=True):
            W.append(f"{k}: dəyərlər [{e.get('min')}, {e.get('max')}] sərhədinə qədər kəsildi")
        exo[k] = c
        changed.append(("exogenous", k))
    coefs = {f"{c['eq_id']}|{c['name']}": float(c["value"]) for c in catalogue.get("coefficients", [])}
    c_cat = {f"{c['eq_id']}|{c['name']}": c for c in catalogue.get("coefficients", [])}
    for k, v in (ov.get("coefficients") or {}).items():
        c = c_cat.get(k)
        if c is None:
            W.append(f"naməlum əmsal '{k}' (format 'EQID|ad') — nəzərə alınmadı")
            continue
        if c.get("editable", True) is False:
            W.append(f"{k}: redaktə edilə bilməz — nəzərə alınmadı")
            continue
        v = float(v)
        cv = float(_clip(v, c.get("min"), c.get("max")))
        if cv != v:
            W.append(f"{k}: {v} sərhədə qədər kəsildi → {cv}")
        lo, hi = c.get("ci_low"), c.get("ci_high")
        if lo is not None and hi is not None and not (lo <= cv <= hi):
            W.append(f"{k}: {cv} 95% etibarlılıq intervalından kənardadır [{lo:.4g}, {hi:.4g}]")
        coefs[k] = cv
        changed.append(("coefficients", k))
    lev = {l["id"]: l.get("value", l.get("default")) for l in catalogue.get("levers", [])}
    l_cat = {l["id"]: l for l in catalogue.get("levers", [])}
    for k, v in (ov.get("levers") or {}).items():
        if k not in l_cat:
            W.append(f"naməlum rıçaq '{k}' — nəzərə alınmadı")
            continue
        l = l_cat[k]
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            cv = float(_clip(v, l.get("min"), l.get("max")))
            if cv != float(v):
                W.append(f"{k}: {v} sərhədə qədər kəsildi → {cv}")
            v = cv
        lev[k] = v
        changed.append(("levers", k))
    for k in ov:
        if k not in ("exogenous", "coefficients", "levers"):
            W.append(f"naməlum override bölməsi '{k}' — nəzərə alınmadı")
    return {"exogenous": exo, "coefficients": coefs, "levers": lev, "changed": changed, "warnings": W}


def coef_value(resolved, eq_id, name):
    return resolved["coefficients"][f"{eq_id}|{name}"]


from ._compare import selftest_compare, make_result, validate_result, series_from_frame, result_to_frame  # noqa: E402,F401
