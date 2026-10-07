"""Shared engine interface of the PolicyUnit (MİİS §15.5.4).

Every engine module exposes ``run(scenario, ctx) -> Result`` where ``frame`` is a
tidy DataFrame with columns ``OUT_COLS``. This file is owned by the CORE agent;
the interface is fixed by POLICY_CONTRACT.md — do not change column names.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math

import pandas as pd

OUT_COLS = ["indicator", "label_az", "unit", "year", "baseline", "value", "delta",
            "delta_pct", "method", "tier", "group", "note_az"]

ENGINES = ("micro", "caem", "oxlon", "riskfx", "io", "microsim", "longrun")
TIERS = ("A", "B", "C", "D")

# units that are rates/shares: delta_pct is reported in percentage points (pp)
RATE_UNITS = {"%", "pp", "f.b.", "%/il", "% ÜDM", "pct_gdp", "rate", "ratio_pct"}

# flows/balances that cross zero: % change is meaningless -> delta_pct = NaN
NO_PCT = {"budget_balance", "ca_proxy", "fiscal_cost", "sofaz_assets"}

# flag in note_az: result known to be unreliable -> excluded from KPIs / headline fallback
UNRELIABLE = "ETİBARSIZ"
# canonical horizon labels (Ministry 24.08.2026): t0 = start year
HORIZON_LABEL_AZ = {"qısa": "qısa müddət — başlanğıc il və növbəti il (t0, t0+1)",
                    "orta": "orta müddət — başlanğıc ildən 2–3 il sonra (t0+2…t0+3)",
                    "uzun": "uzun müddət — başlanğıc ildən 4 və daha çox il sonra (≥ t0+4, yəni 5-ci il və sonrası)"}

HORIZON_AZ = {"qısa": "qısa müddət", "orta": "orta müddət", "uzun": "uzun müddət"}


@dataclass
class Result:
    engine: str                       # one of ENGINES
    frame: pd.DataFrame               # columns OUT_COLS
    meta: dict = field(default_factory=dict)   # vintage ids, runtime, warnings (az), assumptions

    def __post_init__(self):
        self.frame = ensure_frame(self.frame)
        self.meta.setdefault("warnings", [])
        self.meta.setdefault("assumptions", [])


def horizon(year: int, start: int) -> str:
    """Ministry definition (24.08.2026): qısa = start, start+1; orta = start+2..start+3;
    uzun = >= start+4 (5th year onwards)."""
    d = int(year) - int(start)
    if d <= 1:
        return "qısa"
    if d <= 3:
        return "orta"
    return "uzun"


def is_rate(unit: str) -> bool:
    return str(unit).strip() in RATE_UNITS


def make_delta(baseline, value, unit: str):
    """Return (delta, delta_pct). For rates delta_pct = delta in pp; for levels % change."""
    try:
        b, v = float(baseline), float(value)
    except (TypeError, ValueError):
        return float("nan"), float("nan")
    d = v - b
    if is_rate(unit):
        return d, d
    if b == 0 or not math.isfinite(b):
        return d, float("nan")
    return d, 100.0 * d / abs(b)


def row(indicator, label_az, unit, year, baseline, value, method, tier, group,
        note_az="", delta=None, delta_pct=None) -> dict:
    """Build one tidy row; delta/delta_pct computed unless given (deviation-only engines)."""
    if delta is None or delta_pct is None:
        d, dp = make_delta(baseline, value, unit)
        if indicator in NO_PCT:
            dp = float("nan")
        delta = d if delta is None else delta
        delta_pct = dp if delta_pct is None else delta_pct
    return {"indicator": indicator, "label_az": label_az, "unit": unit, "year": int(year),
            "baseline": baseline, "value": value, "delta": delta, "delta_pct": delta_pct,
            "method": method, "tier": tier, "group": group, "note_az": note_az}


def ensure_frame(df) -> pd.DataFrame:
    """Coerce a list of dicts / DataFrame to OUT_COLS (missing cols -> NaN/empty)."""
    if df is None:
        df = pd.DataFrame(columns=OUT_COLS)
    elif not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(list(df))
    for c in OUT_COLS:
        if c not in df.columns:
            df[c] = "" if c in ("label_az", "unit", "method", "tier", "group", "note_az",
                                "indicator") else float("nan")
    df = df[OUT_COLS].copy()
    if len(df):
        df["year"] = df["year"].astype(int)
    return df


def empty_result(engine: str, reason_az: str) -> Result:
    """Engine not applicable / not available — empty frame + Azerbaijani reason."""
    return Result(engine, pd.DataFrame(columns=OUT_COLS),
                  {"warnings": [reason_az], "applicable": False})


def add_horizon(df: pd.DataFrame, start: int) -> pd.DataFrame:
    df = df.copy()
    df["horizon"] = [horizon(y, start) for y in df["year"]]
    return df
