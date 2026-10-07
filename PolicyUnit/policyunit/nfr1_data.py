"""NFR1 retrospective validation — event register and OBSERVED effects (read-only data access).

`config/historical_events.csv`: one row per observed comparison; event-level columns (name, date,
in-sample flag, instruments, shock, legal source) are given on the event's first row and inherited
by the following rows (forward fill within event_id). Observed values are read from the data files
(series keys below); `obs_registered` is the value recorded at registration and is only checked.

series keys: panel:<var> (MicroUnit fr345 DSK panel, levels) | macro:<col> (Macro_OxLon macro_annual,
rates %) | pov:rate (PU poverty table) | derived:rwage (nominal wage / annual-average CPI) |
did:<a>-<b> (growth of a minus growth of b) | fr1raw:<col> (MicroUnit FR1_annual_raw) |
io_e7:<indicator> (IO agent's V_io_e7_fuel_2024.csv). kind: growth | rate | level_pp | cumlevel |
did | io_e7. cf rules: pre1, pre2 (years before event start), trend2, flat10 (DiD: mean differential
in minimum-wage-flat years within 10 years before the event), zero, file."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import config

EVENTS_CSV = config.CONFIG / "historical_events.csv"
EVENT_COLS = ["event_name_az", "event_start", "event_date_az", "in_sample", "in_sample_note_az",
              "instruments_az", "shock", "legal_source"]
PANEL = config.MICRO_ROOT / "data" / "macro_module" / "fr345_public_sources_panel.csv"
MACRO = config.OXLON_ROOT / "delivery" / "4_melumat" / "macro_annual.csv"
FR1RAW = config.MICRO_ROOT / "output" / "FR1_annual_raw.csv"
MW_DECREES = config.MICRO_ROOT / "data" / "dsk_minwage" / "minwage_decrees.csv"
POVERTY = config.DATA / "households" / "targets" / "poverty_line_rate.csv"
IO_E7 = config.OUTPUT / "V_io_e7_fuel_2024.csv"
SOURCES = {"panel": PANEL, "macro": MACRO, "fr1raw": FR1RAW, "pov": POVERTY, "io_e7": IO_E7,
           "mw": MW_DECREES}
_CACHE: dict = {}


def events() -> pd.DataFrame:
    df = pd.read_csv(EVENTS_CSV, dtype=str, keep_default_na=False)
    for c in EVENT_COLS:
        df[c] = df[c].replace("", np.nan)
        df[c] = df.groupby("event_id")[c].ffill()
    for c in ("event_start", "year", "primary"):
        df[c] = df[c].astype(int)
    df["obs_registered"] = pd.to_numeric(df["obs_registered"], errors="coerce")
    return df


# ------------------------------------------------------------------ raw series (year -> value)
def _panel() -> pd.DataFrame:
    if "panel" not in _CACHE:
        p = pd.read_csv(PANEL)
        p = p[pd.to_numeric(p["year"], errors="coerce").notna()]
        p["year"] = p["year"].astype(int)
        _CACHE["panel"] = p.pivot_table(index="year", columns="var", values="value", aggfunc="first")
    return _CACHE["panel"]


def _table(key: str, path) -> pd.DataFrame:
    if key not in _CACHE:
        _CACHE[key] = pd.read_csv(path).set_index("year")
    return _CACHE[key]


def level(src: str, var: str) -> pd.Series:
    if src == "panel":
        return _panel()[var].dropna().astype(float)
    if src == "macro":
        return _table("macro", MACRO)[var].dropna().astype(float)
    if src == "fr1raw":
        return _table("fr1raw", FR1RAW)[var].dropna().astype(float)
    if src == "pov":
        return _table("pov", POVERTY)[var].dropna().astype(float)
    raise KeyError(src)


def growth(s: pd.Series) -> pd.Series:
    s = s.sort_index()
    g = 100 * (s / s.shift(1) - 1)
    return g[(s.index.to_series().diff() == 1).values].dropna()


def series(key: str) -> pd.Series:
    """Annual series in the unit compared: growth % (levels), rate %, or rate level."""
    src, var = key.split(":", 1)
    if src == "derived" and var == "rwage":
        w = growth(level("panel", "wage_ssc_total"))
        p = level("macro", "cpi_infl")
        return (100 * ((1 + w / 100) / (1 + p.reindex(w.index) / 100) - 1)).dropna()
    if src == "did":
        a, b = (v.split("/", 1) if "/" in v else ("panel", v) for v in var.split("-"))
        return (growth(level(*a)) - growth(level(*b))).dropna()
    if src == "fr1raw" and var == "cpi_yoy":
        return level("fr1raw", var) - 100.0
    if src in ("panel", "fr1raw"):
        return growth(level(src, var))
    return level(src, var)


def ms_row(key: str) -> pd.Series | None:
    """'ms:<file>|<variant>|<indicator>' -> row of a microsimulation validation file (or None)."""
    fname, variant, ind = key.split(":", 1)[1].split("|")
    p = config.OUTPUT / fname
    if not p.exists():
        return None
    f = pd.read_csv(p)
    g = f[(f["variant"] == variant) & (f["indicator"] == ind)]
    return g.iloc[0] if len(g) else None


def mw_annual() -> pd.Series:
    """Annual average minimum wage in force (DSK 004_1 decrees, MicroUnit data, read-only)."""
    d = pd.read_csv(MW_DECREES, parse_dates=["effective_date"]).sort_values("effective_date")
    out = {}
    for y in range(2005, config.FIRST_YEAR):
        vals = []
        for m in range(1, 13):
            t = pd.Timestamp(year=y, month=m, day=1)
            v = d[d["effective_date"] <= t]["azn"]
            vals.append(float(v.iloc[-1]) if len(v) else math.nan)
        out[y] = float(np.mean(vals))
    return pd.Series(out)


def mw_flat_years() -> list[int]:
    m = mw_annual()
    return [int(y) for y in m.index[1:] if abs(m[y] / m[y - 1] - 1) < 1e-9]


def fx_annual() -> pd.Series:
    return level("panel", "fx_usd_azn_avg")


def io_e7() -> pd.DataFrame:
    f = config.OUTPUT / "V_io_e7_fuel_2024.csv"          # resolved at call time (config.OUTPUT may be redirected)
    return pd.read_csv(f).set_index("indicator") if f.exists() else pd.DataFrame()


# ------------------------------------------------------------------ counterfactuals and observed effects
SIGMA_PROXY = {"io_e7:cpi_total_pack": "fr1raw:cpi_yoy"}   # Dec/Dec CPI history for the noise of E7
WINDOW = 10                                                # pseudo-event window (years before start)


def cf_value(x: pd.Series, rule: str, y0: int, year: int, kind: str) -> float:
    g = lambda t: float(x.get(t, math.nan))  # noqa: E731
    if rule == "zero":
        return 0.0
    if rule == "pre1":
        return g(y0 - 1)
    if rule == "pre2":
        return (g(y0 - 1) + g(y0 - 2)) / 2
    if rule == "trend2":
        return g(y0 - 1) + (year - y0 + 1) * (g(y0 - 1) - g(y0 - 2))
    if rule == "flat10":
        fl = [t for t in mw_flat_years() if y0 - WINDOW <= t <= y0 - 1 and t in x.index]
        return float(np.mean([x[t] for t in fl])) if fl else math.nan
    raise ValueError(f"naməlum əks-faktual qaydası '{rule}'")


def effect(x: pd.Series, rule: str, y0: int, year: int, kind: str) -> tuple[float, float]:
    """(observed effect, counterfactual value) in the comparison unit."""
    cf = cf_value(x, rule, y0, year, kind)
    if kind == "cumlevel":
        n = year - y0 + 1
        cum = float(np.prod([1 + x.get(t, math.nan) / 100 for t in range(y0, year + 1)]))
        return 100 * (cum / (1 + cf / 100) ** n - 1), 100 * ((1 + cf / 100) ** n - 1)
    return float(x.get(year, math.nan)) - cf, cf


def sigma_cf(x: pd.Series, rule: str, y0: int, year: int, kind: str) -> tuple[float, int]:
    """Noise of the counterfactual rule: 1.4826 × median |error| of pseudo-events (bias included) with the
    same rule and horizon, start years t in [y0-WINDOW, y0-1-h]; DiD flat10: s.d. of the flat-year
    differentials in the window. Needs >= 3 errors."""
    if kind == "did":
        fl = [x[t] for t in mw_flat_years() if y0 - WINDOW <= t <= y0 - 1 and t in x.index]
        return (float(np.std(fl, ddof=1)), len(fl)) if len(fl) >= 2 else (math.nan, len(fl))
    h = year - y0
    errs = []
    for t in range(y0 - WINDOW, y0 - h):
        try:
            e, _ = effect(x, rule, t, t + h, kind)
        except ValueError:
            return math.nan, 0
        if math.isfinite(e):
            errs.append(e)
    if len(errs) < 3:
        return math.nan, len(errs)
    return float(1.4826 * np.median(np.abs(errs))), len(errs)   # robust RMSE-type: bias counts as error


def observed(row: pd.Series) -> dict:
    """Observed effect of one register row under the primary and the alternative counterfactual."""
    y0, year, kind, key = int(row["event_start"]), int(row["year"]), row["kind"], row["series"]
    out = {"row_id": row["row_id"], "obs_raw": math.nan, "cf": math.nan, "obs_effect": math.nan,
           "cf_alt": math.nan, "obs_effect_alt": math.nan, "sigma_cf": math.nan, "sigma_n": 0,
           "obs_check": ""}
    if kind == "io_e7":
        f = io_e7()
        ind = key.split(":", 1)[1]
        if f.empty or ind not in f.index:
            out["obs_check"] = "IO E7 faylı yoxdur"
            return out
        r = f.loc[ind]
        out["obs_raw"] = float(r["observed_2024_pct"])
        out["obs_effect"] = float(r["observed_excess_pp"])
        out["cf"] = out["obs_raw"] - out["obs_effect"]
        out["cf_alt"] = float(r["observed_2023_pct"])
        out["obs_effect_alt"] = out["obs_raw"] - out["cf_alt"]
        if key in SIGMA_PROXY:
            x = series(SIGMA_PROXY[key])
            out["sigma_cf"], out["sigma_n"] = sigma_cf(x, "pre1", y0, year, "rate")
    elif kind == "ms_file":
        r = ms_row(key)
        if r is None:
            out["obs_check"] = "mikrosimulyasiya faylı yoxdur"
            return out
        out["obs_raw"], out["cf"] = float(r["observed"]), float(r["naive_trend"])
        out["obs_effect"] = out["obs_raw"] - out["cf"]
    else:
        x = series(key)
        out["obs_raw"] = (100 * (np.prod([1 + x.get(t, math.nan) / 100 for t in range(y0, year + 1)]) - 1)
                          if kind == "cumlevel" else float(x.get(year, math.nan)))
        out["obs_effect"], out["cf"] = effect(x, row["cf_rule"], y0, year, kind)
        if row["cf_alt"]:
            out["obs_effect_alt"], out["cf_alt"] = effect(x, row["cf_alt"], y0, year, kind)
        out["sigma_cf"], out["sigma_n"] = sigma_cf(x, row["cf_rule"], y0, year, kind)
    reg = row["obs_registered"]
    if math.isfinite(reg) and math.isfinite(out["obs_raw"]) and abs(reg - out["obs_raw"]) > 0.05:
        out["obs_check"] = f"qeydiyyat dəyəri {reg} ≠ məlumat {out['obs_raw']:.2f}"
    return out


# ------------------------------------------------------------------ naive (non-trivial) benchmarks
IO_E7_SECTORS = config.OUTPUT / "V_io_e7_sectors.csv"
NAIVE_AZ = {"prev": "əvvəlki ilin nəticəsi təkrarlanır (təsadüfi gəzinti)",
            "prev_d": "əvvəlki ilin dəyişməsi təkrarlanır",
            "shock": "tam mexaniki ötürmə (tənzimlənən qiymət dəyişməsi = maddə qiyməti)",
            "const": "tam mexaniki ötürmə (siyasət ölçüsü)",
            "io_direct": "yalnız birbaşa mexaniki ötürmə (İQİ çəkisi × tənzimlənən qiymət, dolayı təsirsiz)",
            "zero": "sıfır təsir (trivial)"}


def naive(row: pd.Series, o: dict, shock_size: float = math.nan) -> tuple[float, str]:
    """Naive prediction of the policy EFFECT for one register row -> (value, rule id)."""
    rule = row.get("naive_rule") or "prev"
    y0, year, kind, key = int(row["event_start"]), int(row["year"]), row["kind"], row["series"]
    if rule == "zero":
        return 0.0, "zero"
    if rule == "shock":
        return shock_size, "shock"
    if rule.startswith("const:"):
        return float(rule.split(":", 1)[1]), "const"
    if rule == "io_direct":
        if not (config.OUTPUT / "V_io_e7_sectors.csv").exists():
            return math.nan, rule
        s = pd.read_csv(config.OUTPUT / "V_io_e7_sectors.csv").set_index("sector")
        direct = s["cpi_item_package_pct"] - s["cpi_item_fuel_only_pct"]
        direct["PETR"] = s.loc["PETR", "cpi_item_package_pct"]
        return float((s["cpi_weight"] * direct).sum()), rule
    if kind == "io_e7":                               # previous year of the item = its own counterfactual
        f = io_e7()
        ind = key.split(":", 1)[1]
        v = float(f.loc[ind, "observed_2023_pct"]) - o["cf"] if ind in f.index else math.nan
        return (v, "prev") if math.isfinite(v) and abs(v) > 1e-9 else (0.0, "zero")
    if kind == "ms_file":
        return 0.0, "zero"
    x = series(key)
    if kind == "cumlevel":
        n, cfa = year - y0 + 1, cf_value(x, row["cf_rule"], y0, year, kind)
        return float(100 * (((1 + x.get(y0 - 1, math.nan) / 100) / (1 + cfa / 100)) ** n - 1)), "prev"
    v = float(x.get(year - 1, math.nan)) - o["cf"]
    if math.isfinite(v) and abs(v) > 1e-9:
        return v, "prev"
    return float(x.get(y0 - 1, math.nan) - x.get(y0 - 2, math.nan)), "prev_d"
