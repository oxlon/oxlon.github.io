"""Data spine: one place that reads the §15.5.1 macro model, the §15.5.2 micro unit and the
live feeds, and hands the risk unit a single annual panel, a single baseline and a single
set of transmission multipliers.

Consistency rule (Methodology Blueprint §1.1): the risk unit publishes no central path of
its own. Headline central paths and their fan widths are the macro model's (`source=ours`);
the fiscal block and the shock multipliers are the micro FR1 structural model's. Every
output carries the baseline identifier built here from the hashes of those files.
"""
from __future__ import annotations

import hashlib
from functools import lru_cache

import numpy as np
import pandas as pd
from scipy import stats

from . import config, feeds


def _sha(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest() -> pd.DataFrame:
    rows = []
    for unit, files in (("makro §15.5.1", config.MACRO_FILES), ("mikro §15.5.2", config.MICRO_FILES)):
        for key, p in files.items():
            if not p.exists():
                raise FileNotFoundError(f"Yuxarı axın faylı tapılmadı: {p} (MIIS_MACRO_DIR / MIIS_MICRO_DIR)")
            rows.append({"unit": unit, "key": key, "path": str(p), "sha256": _sha(p),
                         "rows": sum(1 for _ in open(p, "rb")) - 1})
    return pd.DataFrame(rows)


@lru_cache(maxsize=1)
def baseline_id() -> str:
    """Short identifier of the upstream baseline the run was produced from."""
    m = manifest()
    keys = ["forecast_long", "assumptions", "fr1_forecast", "fr1_multipliers"]
    joined = "".join(m.set_index("key").loc[keys, "sha256"])
    return "B-" + hashlib.sha256(joined.encode()).hexdigest()[:10]


@lru_cache(maxsize=None)
def _csv(path) -> pd.DataFrame:
    return pd.read_csv(path, float_precision="round_trip")


def macro_fl() -> pd.DataFrame:
    return _csv(config.MACRO_FILES["forecast_long"])


def macro_series(code: str, kind: str | None = None) -> pd.DataFrame:
    f = macro_fl()
    f = f[(f.series_code == code) & (f.source == "ours")]
    if kind:
        f = f[f.kind == kind]
    return f.set_index("year").sort_index()


def micro_fr1_dataset() -> pd.DataFrame:
    return _csv(config.MICRO_DIR / "output" / "FR1_analysis_dataset.csv").set_index("year")


# ---------------------------------------------------------------- annual panel (history)
def _spi(prec_monthly: pd.DataFrame) -> pd.Series:
    """Standardised precipitation index by hydrological year (Oct y-1 .. Sep y), mean of
    the four agricultural grid cells; gamma fit on 1961-2020 (WMO SPI convention)."""
    p = prec_monthly.copy()
    p["hy"] = p.index.year + (p.index.month >= 10).astype(int)
    tot = p.groupby("hy").agg(["sum", "count"])
    vals = {}
    for col in prec_monthly.columns:
        s = tot[(col, "sum")][tot[(col, "count")] == 12]
        ref = s.loc[1961:2020]
        a, loc, scale = stats.gamma.fit(ref, floc=0)
        vals[col] = pd.Series(stats.norm.ppf(np.clip(stats.gamma.cdf(s, a, loc, scale), 1e-4, 1 - 1e-4)),
                              index=s.index)
    return pd.DataFrame(vals).mean(axis=1)


@lru_cache(maxsize=1)
def precip_monthly() -> pd.DataFrame:
    d = feeds.latest("era5")
    d["date"] = pd.to_datetime(d["date"])
    return d.pivot(index="date", columns="series", values="value").sort_index()


@lru_cache(maxsize=1)
def annual_panel() -> pd.DataFrame:
    """Complete calendar years only (≤ LAST_ACTUAL); the running year lives in `live()`."""
    yrs = range(1990, config.LAST_ACTUAL + 1)
    P = pd.DataFrame(index=pd.Index(yrs, name="year"))
    mi = micro_fr1_dataset()
    P["nonoil_g"] = mi["rgdpnon"].pct_change(fill_method=None) * 100
    P["agri_g"] = mi["rva_agr"].pct_change(fill_method=None) * 100
    P["credit_g"] = mi["rcred_tot"].pct_change(fill_method=None) * 100
    P["lendrate"] = mi["lendrate"].where(mi["lendrate"] > 0)
    P["balance_pct"] = mi["balance_n"] / mi["gdp_n"] * 100
    P["debt_pct"] = mi["debt_azn"] / mi["gdp_n"] * 100
    P["agri_share_nonoil"] = mi["va_agr_n"] / mi["gdp_nonoil_n"] * 100
    for code, col in (("gdp_realg", "gdp_g"), ("cpi_infl", "cpi"), ("brent_usd", "brent"),
                      ("fx_usd_azn_avg", "usd_azn"), ("ca_gdp_ratio", "ca_pct")):
        s = macro_series(code, "actual")["value"]
        P[col] = s.reindex(P.index)
    ext = _csv(config.MACRO_FILES["external_block"]).set_index("year")
    P["partner_g"] = ext["partner_gdp_realg"].reindex(P.index)
    P["us_rate"] = ext["us_policy_rate"].reindex(P.index)
    pub = _csv(config.MACRO_FILES["public_panel"])
    rem = pub[pub["var"] == "remit_credit"].set_index("year")["value"]
    rem_cbar = pub[pub["var"] == "remit_credit_cbar"].set_index("year")["value"]
    P["remit_usd"] = rem.combine_first(rem_cbar).reindex(P.index)
    P["remit_g"] = P["remit_usd"].pct_change(fill_method=None) * 100
    for feed, series, col in (("vix", None, "vix"), ("gpr", "gpr_global", "gpr"),
                              ("gpr", "gpr_rus", "gpr_rus"), ("epu", None, "epu"),
                              ("ust10", None, "ust10")):
        try:
            P[col] = feeds.annual(feed, series).reindex(P.index)
        except FileNotFoundError:
            P[col] = np.nan
    P["spi"] = _spi(precip_monthly()).reindex(P.index)
    P["dln_brent"] = np.log(P["brent"]).diff() * 100
    return P


# ---------------------------------------------------------------- baseline (forecast years)
@lru_cache(maxsize=1)
def baseline() -> pd.DataFrame:
    yrs = config.FORECAST_YEARS
    B = pd.DataFrame(index=pd.Index(yrs, name="year"))
    for code in ("nonoil_realg", "gdp_realg", "cpi_infl", "ca_gdp_ratio", "current_account",
                 "brent_usd", "gdp_nom", "brent_breakeven_ca0"):
        s = macro_series(code, "forecast")
        if s.empty:
            continue
        B[code] = s["value"].reindex(yrs)
        if s["lo80"].notna().any():
            for b in ("lo80", "hi80", "lo50", "hi50"):
                B[f"{code}_{b}"] = s[b].reindex(yrs)
    mf = _csv(config.MICRO_FILES["fr1_forecast"])
    mf = mf[mf["scenario"] == "Baseline"].set_index(mf.columns[0])
    for col in ("balance_n", "gdp_n", "debt_azn", "rgdpnon", "unemp", "rcred_tot", "oil_exp_price",
                "rev_oil_n", "rev_tot_n"):
        B[f"fr1_{col}"] = mf[col].reindex(yrs).values
    B["fr1_balance_pct"] = B["fr1_balance_n"] / B["fr1_gdp_n"] * 100
    B["fr1_debt_pct"] = B["fr1_debt_azn"] / B["fr1_gdp_n"] * 100
    A = _csv(config.MACRO_FILES["assumptions"])
    A = A.pivot(index="year", columns="assumption_key", values="value")
    for k in ("partner_gdp_realg", "usd_azn", "cbar_target"):
        B[k] = A[k].reindex(yrs)
    return B


def baseline_band_sigma(code: str, year: int) -> float:
    """σ implied by the macro 80 % band (normal approximation) — the core's own uncertainty."""
    B = baseline()
    lo, hi = B.at[year, f"{code}_lo80"], B.at[year, f"{code}_hi80"]
    return float((hi - lo) / (2 * stats.norm.ppf(0.9)))


# ---------------------------------------------------------------- multipliers (transmission)
MULT_KEYS = {"Brent +10 USD/bbl": "brent10",
             "State investment +1 bn AZN (real)": "stateinv1bn",
             "Credit easing (-200 bp policy, -100 bp deposit)": "credit_ease200",
             "External demand +10%": "extdem10"}


@lru_cache(maxsize=1)
def multipliers() -> dict[str, pd.DataFrame]:
    """Step responses of the micro FR1 structural model to sustained shocks starting 2026:
    % deviation of levels from baseline (balance_n in mln AZN, infl in pp)."""
    m = _csv(config.MICRO_FILES["fr1_multipliers"])
    m = m.rename(columns={m.columns[0]: "shock", m.columns[1]: "year"})
    out = {}
    for name, key in MULT_KEYS.items():
        out[key] = m[m["shock"] == name].set_index("year").drop(columns="shock")
    return out


# ---------------------------------------------------------------- live conditions (NFR2)
def live() -> dict:
    """Current-year conditions from the feeds: what is known today, not what was assumed."""
    d = pd.Timestamp(config.as_of())
    br = feeds.latest("brent")
    br["date"] = pd.to_datetime(br["date"])
    br = br[br["date"] <= d]
    ytd = br[br["date"].dt.year == d.year]
    m = br.set_index("date")["value"].resample("MS").mean()
    gpr = feeds.monthly("gpr", "gpr_global")
    vix = feeds.latest("vix")
    out = {
        "as_of": d.date().isoformat(),
        "brent_last": float(br["value"].iloc[-1]), "brent_last_date": br["date"].iloc[-1].date().isoformat(),
        "brent_ytd_avg": float(ytd["value"].mean()), "brent_ytd_n": int(len(ytd)),
        "brent_last_month": float(m.iloc[-1]), "brent_monthly": m,
        "gpr_last": float(gpr.iloc[-1]), "gpr_last_date": gpr.index[-1].date().isoformat(),
        "gpr_3m": float(gpr.iloc[-3:].mean()), "gpr_monthly": gpr,
        "vix_last": float(vix["value"].iloc[-1]), "vix_last_date": str(vix["date"].iloc[-1]),
    }
    for feed, key in (("fedfunds", "fedfunds_last"), ("ust10", "ust10_last"), ("eurusd", "eurusd_last"),
                      ("epu", "epu_last")):
        try:
            x = feeds.latest(feed)
            out[key] = float(x["value"].iloc[-1])
            out[key + "_date"] = str(x["date"].iloc[-1])
        except FileNotFoundError:
            out[key] = np.nan
    eq = feeds.latest("usgs")
    out["eq_last"] = eq.iloc[-1].to_dict()
    return out


def clear_caches():
    for f in (baseline_id, _csv, annual_panel, baseline, multipliers, precip_monthly):
        f.cache_clear()
