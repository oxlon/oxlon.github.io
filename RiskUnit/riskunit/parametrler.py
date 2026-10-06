"""Documented model parameters (input/parametrler.csv): value, unit, source and justification in Azerbaijani.

Every hard-coded constant of the risk-finance layer (dsa, car, var, optimize) is read from here, so a
Ministry reviewer can see and change it without touching code. `get(key, default)` falls back to the
default (and records the key in MISSING) when the file or the row is absent — tests stay offline-safe.
"""
from __future__ import annotations

import pandas as pd

from . import config

FILE = config.INPUT / "parametrler.csv"
MISSING: set[str] = set()
_CACHE: dict = {}


def table() -> pd.DataFrame:
    if not FILE.exists():
        return pd.DataFrame(columns=["acar", "deyer", "vahid", "izah", "menbe", "esaslandirma", "modul", "status"])
    key = FILE.stat().st_mtime
    if _CACHE.get("mtime") != key:
        _CACHE["df"], _CACHE["mtime"] = pd.read_csv(FILE, dtype=str), key
    return _CACHE["df"]


def get(key: str, default=None):
    """Numeric value when it parses as a float, else the string; `default` when the key is absent."""
    t = table()
    r = t.loc[t["acar"] == key, "deyer"]
    if not len(r) or pd.isna(r.iloc[0]):
        MISSING.add(key)
        return default
    v = str(r.iloc[0]).strip()
    try:
        return float(v)
    except ValueError:
        return v


def source(key: str) -> str:
    t = table()
    r = t.loc[t["acar"] == key, "menbe"]
    return str(r.iloc[0]) if len(r) else "parametr faylda yoxdur — kod daxili ehtiyat dəyəri"
