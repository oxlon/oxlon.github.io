"""Self-test comparison against notebook CSVs and the standard engine result format."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .._util import ID_RE, fnum, rel_diff


def selftest_compare(df_engine, csv_path, cols, tol=1e-8, on=None, index_col=None, floor=1e-10, csv_filter=None):
    """Compare engine output with the notebook CSV.
    cols: list of column names, or {engine_col: csv_col}. on: key columns to merge on (e.g. ['scenario','year']);
    index_col: read the CSV with this index and align on the engine frame's index; otherwise positional.
    csv_filter: optional callable(df_csv) -> df_csv (e.g. select one scenario).
    Returns {"ok", "max_rel_diff", "per_col", "n_rows", "problems"}; relative diff = |a-b|/max(|a|,|b|,floor)."""
    ref = pd.read_csv(csv_path, index_col=index_col)
    if csv_filter is not None:
        ref = csv_filter(ref)
    cmap = dict(cols) if isinstance(cols, dict) else {c: c for c in cols}
    probs, per = [], {}
    eng = df_engine.copy()
    if on:
        keys = list(on)
        m = eng.merge(ref, on=keys, how="outer", suffixes=("__e", "__r"), indicator=True)
        if (m["_merge"] != "both").any():
            probs.append(f"{int((m['_merge'] != 'both').sum())} rows not matched on {keys}")
        m = m[m["_merge"] == "both"]
        get = lambda ce, cr: (m[ce + "__e"] if ce + "__e" in m else m[ce],  # noqa: E731
                              m[cr + "__r"] if cr + "__r" in m else m[cr])
        n = len(m)
    else:
        if index_col is not None:
            eng.index = eng.index.astype(ref.index.dtype) if len(eng.index) else eng.index
            common = eng.index.intersection(ref.index)
            if len(common) != len(ref.index) or len(common) != len(eng.index):
                probs.append(f"index mismatch: engine {len(eng.index)}, csv {len(ref.index)}, common {len(common)}")
            e2, r2 = eng.loc[common], ref.loc[common]
        else:
            if len(eng) != len(ref):
                probs.append(f"row count: engine {len(eng)} vs csv {len(ref)}")
            k = min(len(eng), len(ref))
            e2, r2 = eng.iloc[:k].reset_index(drop=True), ref.iloc[:k].reset_index(drop=True)
        get = lambda ce, cr: (e2[ce], r2[cr])  # noqa: E731
        n = len(e2)
    for ce, cr in cmap.items():
        try:
            a, b = get(ce, cr)
        except KeyError as err:
            probs.append(f"missing column {err}")
            per[ce] = None
            continue
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            d = rel_diff(a.to_numpy(float), b.to_numpy(float), floor)
            per[ce] = float(np.max(d)) if d.size else 0.0
        else:
            per[ce] = 0.0 if (a.astype(str).to_numpy() == b.astype(str).to_numpy()).all() else float("inf")
    mx = max([v for v in per.values() if v is not None] or [0.0])
    ok = not probs and mx <= tol and all(v is not None for v in per.values())
    return {"ok": bool(ok), "max_rel_diff": mx, "per_col": per, "n_rows": int(n), "problems": probs,
            "csv": str(csv_path), "tol": tol}


def _year(y):
    f = float(y)
    return int(f) if f == int(f) else f


def make_result(series, meta=None, warnings=None, years=None):
    """series: {id: pd.Series(year-indexed) | {year: v} | list aligned with `years`}."""
    out = {}
    for sid, s in (series or {}).items():
        if isinstance(s, pd.Series):
            d = {str(_year(k)): fnum(v) for k, v in s.items()}
        elif isinstance(s, dict):
            d = {str(_year(k)): fnum(v) for k, v in s.items()}
        else:
            if years is None:
                raise ValueError(f"{sid}: list values need `years`")
            d = {str(_year(y)): fnum(v) for y, v in zip(years, s)}
        out[sid] = d
    return {"series": out, "meta": dict(meta or {}), "warnings": list(warnings or [])}


def validate_result(res, module=None):
    errs = []
    for k in ("series", "meta", "warnings"):
        if k not in res:
            errs.append(f"missing '{k}'")
    for sid, d in (res.get("series") or {}).items():
        if not ID_RE.match(sid):
            errs.append(f"bad id '{sid}'")
        if module and not sid.startswith(module.lower() + ":"):
            errs.append(f"id '{sid}' not in module {module}")
        if not isinstance(d, dict):
            errs.append(f"{sid}: must be {{year: value}}")
            continue
        for y, v in d.items():
            try:
                float(y)
            except ValueError:
                errs.append(f"{sid}: bad year '{y}'")
            if v is not None and not isinstance(v, (int, float)):
                errs.append(f"{sid}[{y}]: non-numeric")
    return errs


def series_from_frame(df, mapping, years=None):
    """df indexed by year; mapping {column: indicator_id} -> {id: {year: v}}."""
    d = df if years is None else df.loc[[y for y in years if y in df.index]]
    return {sid: {str(_year(y)): fnum(v) for y, v in d[col].items()} for col, sid in mapping.items()}


def result_to_frame(res):
    s = res["series"]
    return pd.DataFrame({k: pd.Series({int(float(y)): v for y, v in d.items()}) for k, d in s.items()}).sort_index()
