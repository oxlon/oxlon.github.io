"""FRx_indicator_catalog.csv writer (contract section C) and cross-checks with the registry / engine."""
from __future__ import annotations

import json
import os

import pandas as pd

from ._util import ID_RE

COLUMNS = ["id", "module", "group_az", "label_az", "label_en", "unit_az", "freq", "kind", "has_forecast",
           "scenarios", "has_band", "source_csv", "source_column", "equation_ids", "imputed_years"]
KINDS = ("level", "rate", "share", "index")
REQUIRED = ("id", "label_az", "kind")


def _join(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, (list, tuple, set)):
        return ";".join(str(x) for x in v)
    return str(v)


def _bool(v):
    if isinstance(v, str):
        return "true" if v.strip().lower() in ("true", "1", "yes", "bəli") else "false"
    return "true" if bool(v) else "false"


def make_rows(rows, module):
    """rows: list of dicts (any order of keys; lists allowed for scenarios/equation_ids/imputed_years)."""
    mod = module.upper()
    out, errs, seen = [], [], set()
    for i, r in enumerate(rows):
        r = dict(r)
        for k in REQUIRED:
            if not r.get(k):
                errs.append(f"row {i}: missing '{k}'")
        sid = str(r.get("id", ""))
        if not ID_RE.match(sid) or not sid.startswith(mod.lower() + ":"):
            errs.append(f"row {i}: id '{sid}' must look like '{mod.lower()}:<code>'")
        if sid in seen:
            errs.append(f"row {i}: duplicate id '{sid}'")
        seen.add(sid)
        if r.get("kind") not in KINDS:
            errs.append(f"row {i} ({sid}): kind must be one of {KINDS}")
        unknown = set(r) - set(COLUMNS)
        if unknown:
            errs.append(f"row {i} ({sid}): unknown columns {sorted(unknown)}")
        rec = {c: "" for c in COLUMNS}
        rec.update(module=mod, freq="A")
        rec.update({k: v for k, v in r.items() if k in COLUMNS})
        for c in ("scenarios", "equation_ids", "imputed_years"):
            rec[c] = _join(rec[c])
        for c in ("has_forecast", "has_band"):
            rec[c] = _bool(rec[c]) if rec[c] != "" else "false"
        out.append(rec)
    return pd.DataFrame(out, columns=COLUMNS), errs


def write_catalog(rows, path, module, strict=True):
    df, errs = make_rows(rows, module)
    if errs and strict:
        raise ValueError(f"{len(errs)} catalog errors: " + "; ".join(errs[:10]))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    return df


def read_catalog(path):
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    for c in ("has_forecast", "has_band"):
        df[c] = df[c].str.lower().eq("true")
    for c in ("scenarios", "equation_ids", "imputed_years"):
        df[c] = df[c].apply(lambda s: [x for x in s.split(";") if x])
    return df


def check_catalog(catalog_path, equations_path=None, engine_result=None):
    """Cross-check: every registry `components` id and every engine series id is in the catalogue; every
    catalogue equation_id exists in the registry. Returns list of problems."""
    cat = read_catalog(catalog_path)
    ids = set(cat["id"])
    probs = []
    if equations_path and os.path.exists(equations_path):
        with open(equations_path, encoding="utf-8") as fh:
            reg = json.load(fh)
        eq_ids = {e["id"] for e in reg["equations"]}
        for e in reg["equations"]:
            for c in e.get("components", []):
                if c not in ids:
                    probs.append(f"registry {e['id']}: component '{c}' not in catalogue")
        for _, r in cat.iterrows():
            for q in r["equation_ids"]:
                if q not in eq_ids:
                    probs.append(f"catalogue {r['id']}: equation '{q}' not in registry")
    if engine_result is not None:
        for sid in engine_result.get("series", {}):
            if sid not in ids:
                probs.append(f"engine series '{sid}' not in catalogue")
    return probs
