"""Small shared helpers: JSON conversion (NaN -> null, numpy -> python), coercion, relative diffs."""
from __future__ import annotations

import datetime as _dt
import math
import re

import numpy as np
import pandas as pd

ID_RE = re.compile(r"^fr\d+:[A-Za-z0-9_.:\-]+$")


def to_jsonable(obj):
    """Recursively convert numpy / pandas objects to plain JSON types; NaN/inf -> None."""
    if obj is None or isinstance(obj, (str, bool)):
        return obj
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        v = float(obj)
        return v if math.isfinite(v) else None
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [to_jsonable(v) for v in obj.tolist()]
    if isinstance(obj, pd.Series):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, pd.DataFrame):
        return {"columns": [str(c) for c in obj.columns], "index": to_jsonable(list(obj.index)),
                "data": to_jsonable(obj.to_numpy().tolist())}
    if isinstance(obj, (pd.Timestamp, _dt.datetime, _dt.date)):
        return obj.isoformat()
    if obj is pd.NA or obj is pd.NaT:
        return None
    if hasattr(obj, "item"):
        try:
            return to_jsonable(obj.item())
        except Exception:
            pass
    return str(obj)


def fnum(x):
    """float or None (for NaN/inf/None)."""
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def as_series(v, name="y"):
    if isinstance(v, pd.Series):
        return v.astype(float)
    if isinstance(v, pd.DataFrame):
        if v.shape[1] != 1:
            raise ValueError("y must be one column")
        return v.iloc[:, 0].astype(float)
    return pd.Series(np.asarray(v, float), name=name)


def as_frame(X, index=None):
    if X is None:
        return pd.DataFrame(index=index)
    if isinstance(X, pd.DataFrame):
        return X.astype(float)
    if isinstance(X, pd.Series):
        return X.astype(float).to_frame(X.name or "x1")
    a = np.asarray(X, float)
    if a.ndim == 1:
        a = a[:, None]
    return pd.DataFrame(a, index=index, columns=[f"x{i+1}" for i in range(a.shape[1])])


def as_dict(v):
    """dict / Series / None -> {name: float}."""
    if v is None:
        return {}
    if isinstance(v, pd.Series):
        return {str(k): float(x) for k, x in v.items()}
    if isinstance(v, dict):
        return {str(k): float(x) for k, x in v.items()}
    raise TypeError("expected dict or pandas Series")


def years_of(index):
    """Index -> list of int years when possible, else list of positions."""
    out = []
    for i, v in enumerate(index):
        if isinstance(v, tuple):
            v = v[-1]
        try:
            fv = float(v)
            out.append(int(fv) if float(int(fv)) == fv else fv)
        except (TypeError, ValueError):
            if hasattr(v, "year"):
                out.append(int(v.year))
            else:
                out.append(i)
    return out


def rel_diff(a, b, floor=1e-10):
    """|a-b| / max(|a|, |b|, floor), elementwise; NaN==NaN counts as 0, one-sided NaN as inf."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    both = np.isnan(a) & np.isnan(b)
    one = np.isnan(a) ^ np.isnan(b)
    d = np.abs(a - b) / np.maximum(np.maximum(np.abs(a), np.abs(b)), floor)
    d = np.where(both, 0.0, d)
    return np.where(one, np.inf, d)


def close(a, b, rtol=1e-6, atol=1e-10):
    return bool(abs(float(a) - float(b)) <= rtol * max(abs(float(a)), abs(float(b))) + atol)


def now_iso():
    return _dt.datetime.now().astimezone().replace(microsecond=0).isoformat()
