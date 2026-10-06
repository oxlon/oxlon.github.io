"""Daily forecast-impact monitor (v2): "what changed and how it moves the forecasts".

For every observed market / statistical indicator the monitor compares the latest value with the assumption embedded
in the current baselines of each unit and translates the deviation into forecast impact:

  D5_daily_monitor.csv   indicator, latest, date, baseline source/year/assumption, deviation, z-score, signal
  D6_forecast_impact.csv driver, target id, year, baseline, implied, delta, delta %, channel / source
  D7_changes.csv         day-over-day changes of D5 (and of the headline D6 impacts) plus new observations per feed

Impact channels (no own forecasting model — only the units' own engines / elasticities and transparent arithmetic):
  * MicroUnit chain `chain.run_chain` FR1 → FR3/FR4/FR5 → FR10 → FR12: the implied Brent path and the policy-rate path
    replace the FR1 exogenous assumptions; every component of every module is re-solved (delta vs an engine run with no
    override, so the comparison is like-for-like).
  * MicroUnit FR1 step responses (FR1_multipliers.csv, Brent +10 USD) — linear cross-check.
  * OxLon §15.5.1: current account vs Brent from the published lo80/hi80 Brent scenarios (finite-difference elasticity).
  * Observation arithmetic (labelled): annual CPI / GDP implied by the Jan–M outturn if the latest rate persists for the
    remaining months; budget revenue at the current execution pace; SOFAZ revaluation from gold and EUR moves.
"Implied" paths are conditional ("if today's level persists"), not forecasts: the Brent path is flat at today's spot
(no free, stable futures source exists — documented), 2026 combines the year-to-date average with the spot for the rest.

z-scores: deviation / σ, with σ the units' own historical forecast error where available (OxLon validation_backtest
h=1 RMSE of the best model; Brent RMSE is in logs → σ = RMSE × level), otherwise the historical sd of annual changes.
Signal: |z| < 1 "normal", 1–2 "diqqət", ≥ 2 "xəbərdarlıq" (with direction ↑/↓). The reference is the forecast
assumption (two-sided), unlike FR1_indicator_base (own history, one-sided) — columns istinad / signal_qaydasi say so.
"""
from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

from . import config, feeds, upstream

D5_COLS = ["indicator", "label_az", "latest", "date", "unit", "baseline_source", "baseline_year", "baseline_assumption",
           "deviation", "deviation_pct", "sigma", "z_score", "z_basis", "signal", "note", "istinad", "signal_qaydasi"]
# v2.1 (UI review): D5 measures the deviation from the units' FORECAST ASSUMPTION (two-sided), FR1_indicator_base the
# position in the indicator's own HISTORY (one-sided, risk direction) — each row says which, so the two can be read together.
SIGNAL_RULE = "ikitərəfli: |z| < 1 normal, 1–2 diqqət, ≥ 2 xəbərdarlıq (↑/↓ — sapmanın istiqaməti, risk istiqaməti deyil)"
D6_COLS = ["driver", "target_id", "label_az", "unit", "year", "baseline", "implied", "delta", "delta_pct", "channel",
           "source", "scenario_note"]
SRC = {"oxlon": "OxLon §15.5.1", "fr1": "MicroUnit FR1", "caem": "Nazirlik CAEM", "bu60": "Nazirlik Bottom-up",
       "imf": "BVF Art. IV"}


# ---------------------------------------------------------------- inputs
def _feed(feed: str, series: str | None = None) -> pd.DataFrame:
    try:
        d = feeds.latest(feed)
    except FileNotFoundError:
        return pd.DataFrame(columns=["series", "date", "value"])
    if series is not None and "series" in d.columns:
        d = d[d["series"] == series]
    d = d.dropna(subset=["value"]).copy()
    d["date"] = pd.to_datetime(d["date"].astype(str).str[:10], errors="coerce")
    d = d[d["date"] <= pd.Timestamp(config.as_of())]
    return d.sort_values("date")


def last(feed: str, series: str | None = None):
    d = _feed(feed, series)
    return (float(d["value"].iloc[-1]), d["date"].iloc[-1]) if len(d) else (np.nan, None)


def base(sid: str, year: int, scenario: str = "Baseline") -> float:
    s = upstream.series(sid)
    s = s[(s["year"] == year) & (s["scenario"].isin([scenario, "ACTUAL"]) | s["source"].str.startswith("ministry"))]
    return float(s["value"].iloc[0]) if len(s) else np.nan


def base_ref(ref: str, year: int) -> float:
    S = upstream.store()
    s = S[(S["row_ref"] == ref) & (S["year"] == year)]
    return float(s["value"].iloc[0]) if len(s) else np.nan


def growth(sid: str, year: int) -> float:
    a, b = base(sid, year), base(sid, year - 1)
    return (a / b - 1) * 100 if np.isfinite(a) and np.isfinite(b) and b else np.nan


def rmse(series_code: str) -> float:
    p = config.UPSTREAM_STORE / "oxlon_backtest_summary.csv"
    if not p.exists():
        upstream.store()
    b = pd.read_csv(p)
    b = b[(b["series_code"] == series_code) & (b["n"] >= 5)]
    if len(b):
        return float(b["rmse"].min())
    s = upstream.series(f"mx:{series_code}")                 # fallback: historical sd of the actuals 2010–2025
    s = s[(s["kind"] == "actual") & s["year"].between(2010, config.LAST_ACTUAL)]["value"]
    return float(s.std()) if len(s) >= 5 else np.nan


def signal(z: float) -> str:
    if not np.isfinite(z):
        return "qiymətləndirilmir"
    arrow = "↑" if z > 0 else "↓"
    return "normal" if abs(z) < 1 else (f"diqqət {arrow}" if abs(z) < 2 else f"xəbərdarlıq {arrow}")


def row(ind, lab, latest, d, unit, src, yr, assumption, sigma, basis, note="") -> dict:
    dev = latest - assumption if np.isfinite(latest) and np.isfinite(assumption) else np.nan
    z = dev / sigma if np.isfinite(dev) and sigma and np.isfinite(sigma) else np.nan
    return {"indicator": ind, "label_az": lab, "latest": latest, "date": d.date().isoformat() if d is not None else "",
            "unit": unit, "baseline_source": src, "baseline_year": yr, "baseline_assumption": assumption, "deviation": dev,
            "deviation_pct": dev / abs(assumption) * 100 if np.isfinite(dev) and assumption else np.nan, "sigma": sigma,
            "z_score": z, "z_basis": basis, "signal": signal(z), "note": note,
            "istinad": (f"proqnoz fərziyyəsinə görə ({src}, {yr}); z = (son − fərziyyə) / σ ({basis})"
                        if src in SRC.values() else
                        f"sabit istinada görə ({src}; proqnoz fərziyyəsi yoxdur); z = (son − istinad) / σ ({basis})"),
            "signal_qaydasi": SIGNAL_RULE}


def month_share(d: pd.Timestamp | None) -> float:
    """Share of the year covered by a Jan–M cumulative observation dated YYYY-MM-01."""
    return (d.month / 12) if d is not None else np.nan


# ---------------------------------------------------------------- implied paths (conditional, not forecasts)
def brent_implied(year0: int | None = None) -> dict:
    """2026: year-to-date average of daily Brent combined with today's spot for the remaining calendar days;
    later years: today's spot (flat). Returns {'spot', 'spot_date', 'ytd', 'n_ytd', 'path': {year: value}}."""
    br = _feed("brent")
    if br.empty:
        return {}
    today = pd.Timestamp(config.as_of())
    y0 = year0 or today.year
    spot, sd = float(br["value"].iloc[-1]), br["date"].iloc[-1]
    ytd = br[br["date"].dt.year == y0]["value"]
    frac = (sd.dayofyear) / (366 if sd.is_leap_year else 365)
    y_avg = float(ytd.mean()) * frac + spot * (1 - frac) if len(ytd) else spot
    path = {y: (y_avg if y == y0 else spot) for y in config.FORECAST_YEARS if y >= y0}
    m30 = float(br[br["date"] > sd - pd.Timedelta(days=30)]["value"].mean())
    return {"spot": spot, "spot_date": sd, "ytd": float(ytd.mean()) if len(ytd) else np.nan, "n_ytd": int(len(ytd)),
            "avg30": m30, "frac": frac, "path": path}


def policy_implied() -> dict:
    rate = _feed("cbar_rate", "cbar_policy_rate")
    if rate.empty:
        return {}
    today = pd.Timestamp(config.as_of())
    cur, cd = float(rate["value"].iloc[-1]), rate["date"].iloc[-1]
    # 2026 average of the effective rate (step function) so far + current rate for the rest of the year
    days = pd.date_range(f"{today.year}-01-01", f"{today.year}-12-31", freq="D")
    eff = rate.set_index("date")["value"].reindex(days.union(rate["date"])).sort_index().ffill().reindex(days)
    eff[eff.index > today] = cur
    path = {y: (float(eff.mean()) if y == today.year else cur) for y in config.FORECAST_YEARS if y >= today.year}
    return {"rate": cur, "date": cd, "path": path}


# ---------------------------------------------------------------- D5: latest observation vs embedded assumptions
BRENT_BASE = {"oxlon": ("id", "mx:brent_usd"), "fr1": ("id", "fr1:exo:brent"),
              "caem": ("ref", "CAEM.xlsx/Oil_and_gas_sector!R69"), "bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R141")}
GDP_BASE = {  # DSK series → (label, {source: (selector, transform)})
    "dsk_gdp_ytd_yoy": ("Real ÜDM artımı (Yanvar–ay)", "mx:gdp_realg", {
        "oxlon": ("id", "mx:gdp_realg", "level"), "fr1": ("id", "fr1:rgdp", "growth"),
        "caem": ("ref", "CAEM.xlsx/6a. SEI!R9", "level"), "bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R6", "level"),
        "imf": ("id", "mx:imf:gdp_realg", "level")}),
    "dsk_gdp_nonoil_ytd_yoy": ("Qeyri-neft ÜDM artımı (Yanvar–ay)", "mx:nonoil_realg", {
        "oxlon": ("id", "mx:nonoil_realg", "level"), "fr1": ("id", "fr1:rgdpnon", "growth"),
        "caem": ("ref", "CAEM.xlsx/MOE_report!R38", "level"), "bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R13", "level"),
        "imf": ("id", "mx:imf:nonoil_realg", "level")}),
    "dsk_gdp_oil_ytd_yoy": ("Neft-qaz ÜDM artımı (Yanvar–ay)", "mx:oil_realg", {
        "oxlon": ("id", "mx:oil_realg", "level"), "fr1": ("id", "fr1:rgdpoil", "growth"),
        "caem": ("ref", "CAEM.xlsx/MOE_report!R34", "level"), "bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R9", "level")}),
}
CPI_BASE = {"oxlon": ("id", "mx:cpi_infl", "level"), "fr1": ("id", "fr1:infl", "level"),
            "caem": ("ref", "CAEM.xlsx/6a. SEI!R19", "level"), "imf": ("id", "mx:imf:cpi_infl", "level")}


def _val(sel, year: int) -> float:
    how, key, *tr = sel
    if tr and tr[0] == "growth":
        return growth(key, year)
    return base(key, year) if how == "id" else base_ref(key, year)


def brent_rows(Y: int) -> list[dict]:
    b = brent_implied()
    if not b:
        return []
    out, s_log = [], rmse("brent_usd")
    for src, (how, key) in BRENT_BASE.items():
        a = _val((how, key), Y)
        sig = s_log * a if np.isfinite(s_log) and np.isfinite(a) else np.nan
        out.append(row("brent_spot", "Brent (spot)", b["spot"], b["spot_date"], "USD/barel", SRC[src], Y, a, sig,
                       "OxLon Brent h=1 RMSE (log) × fərziyyə", f"30 günlük orta {b['avg30']:.2f}"))
        out.append(row("brent_implied_annual", f"Brent {Y} illik ortası (YTD + spot)", b["path"].get(Y, np.nan),
                       b["spot_date"], "USD/barel", SRC[src], Y, a, sig * (1 - b["frac"]) if np.isfinite(sig) else sig,
                       "σ × qalan il payı", f"YTD ortası {b['ytd']:.2f} (n={b['n_ytd']}), il payı {b['frac']:.2f}"))
    az, azd = last("azeri_light")
    ex = base("fr1:oil_exp_price", Y)
    out.append(row("azeri_light_proxy", "Azeri Light (proksi) vs FR1 ixrac qiyməti", az, azd, "USD/barel", SRC["fr1"], Y,
                   ex, s_log * ex if np.isfinite(ex) else np.nan, "OxLon Brent h=1 RMSE (log)",
                   "Proksi: Brent + sənədləşdirilmiş spred (azad Azeri Light mənbəyi yoxdur)"))
    return out


def fx_rows(Y: int) -> list[dict]:
    out = []
    usd, ud = last("cbar_fx", "cbar_usd")
    for src, key in (("oxlon", "mx:fx_usd_azn_avg"), ("fr1", "fr1:exo:fx")):
        out.append(row("usd_azn", "USD/AZN rəsmi məzənnə", usd, ud, "AZN", SRC[src], Y, base(key, Y),
                       0.0555 * 1.70, "OxLon FX fan σ 5,55 %/il (peq dövrü)"))
    eur, ed = last("cbar_fx", "cbar_eur")
    s = upstream.series("mx:fx_eur_azn")
    s = s[s["year"] == Y]
    sig = float((s["hi80"] - s["lo80"]).iloc[0] / 2.563) if len(s) and s["hi80"].notna().any() else rmse("fx_eur_azn")
    out.append(row("eur_azn", "EUR/AZN rəsmi məzənnə", eur, ed, "AZN", SRC["oxlon"], Y, base("mx:fx_eur_azn", Y), sig,
                   "OxLon EUR/AZN 80 % intervalı"))
    for code, lab in (("rub", "RUB/AZN (pul köçürmələri kanalı)"), ("try", "TRY/AZN (ticarət tərəfdaşı)"),
                      ("cny", "CNY/AZN"), ("gbp", "GBP/AZN"), ("xau", "Qızıl (XAU/AZN)")):
        d = _feed("cbar_fx", f"cbar_{code}")
        if d.empty:
            continue
        cur, cd = float(d["value"].iloc[-1]), d["date"].iloc[-1]
        yago = d[d["date"] <= cd - pd.Timedelta(days=365)]
        if yago.empty:
            out.append(row(f"{code}_azn", lab, cur, cd, "AZN", "tarix (1 il əvvəl yoxdur)", Y, np.nan, np.nan, ""))
            continue
        ref = float(yago["value"].iloc[-1])
        m = d.set_index("date")["value"].resample("MS").last().dropna()
        chg = (m / m.shift(12) - 1).dropna() * 100
        out.append(row(f"{code}_azn", lab + " — illik dəyişmə", (cur / ref - 1) * 100, cd, "%", "tarixi orta illik dəyişmə",
                       Y, float(chg.mean()) if len(chg) else 0.0, float(chg.std()) if len(chg) > 3 else np.nan,
                       f"illik dəyişmələrin sd ({len(chg)} ay)", f"səviyyə {cur:.4g}"))
    return out


def rate_rows(Y: int) -> list[dict]:
    p = policy_implied()
    if not p:
        return []
    hist = _feed("cbar_rate", "cbar_policy_rate").set_index("date")["value"]
    ann = hist.resample("YE").last().ffill().diff().dropna()
    sig = float(ann.std()) if len(ann) > 3 else np.nan
    out = []
    for yr in (Y, Y + 1):
        out.append(row("policy_rate", f"AMB uçot dərəcəsi vs FR1 fərziyyəsi ({yr})", p["rate"], p["date"], "%", SRC["fr1"],
                       yr, base("fr1:exo:polrate", yr), sig, "illik dəyişmələrin sd (AMB tarixi)",
                       f"{Y} effektiv orta (YTD + cari) {p['path'].get(Y, np.nan):.3f}"))
    fl, _ = last("cbar_rate", "cbar_corridor_floor")
    ce, _ = last("cbar_rate", "cbar_corridor_ceiling")
    out[-1]["note"] += f"; dəhliz {fl:g}–{ce:g}"
    for kind, lab in (("mof_bond", "DQK (MN istiqrazı) orta gəlirlilik − uçot"), ("cbar_note", "AMB notu orta gəlirlilik − uçot")):
        y, yd = last("bfb", f"bfb_{kind}_avg_yield")
        out.append(row(f"bfb_{kind}_spread", lab, y - p["rate"] if np.isfinite(y) else np.nan, yd, "f.b.", "spred = 0 istinadı",
                       Y, 0.0, 1.0, "1 f.b. şərti miqyas", f"gəlirlilik {y:.2f} %"))
    return out


def cpi_rows(Y: int) -> list[dict]:
    out = []
    yoy, d = last("dsk_cpi", "dsk_cpi_yoy")
    ytd, _ = last("dsk_cpi", "dsk_cpi_ytd_avg_yoy")
    if not np.isfinite(ytd):
        ytd, d2 = last("dsk_macro", "dsk_cpi_ytd_yoy")
        d = d or d2
        yoy = yoy if np.isfinite(yoy) else ytd
    if d is None:
        return out
    m = d.month
    implied = (ytd * m + yoy * (12 - m)) / 12 if np.isfinite(ytd) and np.isfinite(yoy) else np.nan
    sig = rmse("cpi_infl")
    for src, sel in CPI_BASE.items():
        a = _val(sel, Y)
        out.append(row("cpi_implied_annual", f"İQİ {Y} illik orta (Yanvar–{m}. ay + son ay saxlanılır)", implied, d, "%",
                       SRC[src], Y, a, sig * (12 - m) / 12 if np.isfinite(sig) else sig, "OxLon CPI h=1 RMSE × qalan il payı",
                       f"Yanvar–ay orta {ytd:.2f}, son ay illik {yoy:.2f}"))
    mm, md = last("dsk_cpi", "dsk_cpi_mm")
    if np.isfinite(mm):
        a = base("mx:cpi_infl", Y)
        path_mm = ((1 + a / 100) ** (1 / 12) - 1) * 100 if np.isfinite(a) else np.nan
        hist = pd.read_csv(config.MACRO_FILES["monthly_panel"])
        h = (hist["cpi"].dropna() - 100).tail(120)          # cpi column = index, previous month = 100
        out.append(row("cpi_mm", "İQİ aylıq dəyişmə vs OxLon illik yolunun aylıq ekvivalenti", mm, md, "%", SRC["oxlon"], Y,
                       path_mm, float(h.std()) if len(h) > 12 else np.nan, "aylıq İQİ dəyişmələrinin sd (son 10 il)"))
    return out


def gdp_rows(Y: int) -> list[dict]:
    out = []
    for ser, (lab, hist_code, srcs) in GDP_BASE.items():
        v, d = last("dsk_macro", ser)
        if d is None or d.year != Y:
            continue
        sig = rmse(hist_code.split(":", 1)[1])
        for src, sel in srcs.items():
            out.append(row(ser, lab, v, d, "%", SRC[src], Y, _val(sel, Y), sig, "OxLon h=1 RMSE (yoxdursa tarixi sd)",
                           f"DSK Yanvar–{d.month}. ay; FR1 üçün {Y} illik 'nowcast'"))
    q, qd = last("dsk_tables", "dsk_q_gdp_real_yoy")
    if np.isfinite(q):
        out.append(row("dsk_q_gdp_real_yoy", "Rüblük real ÜDM artımı (DSK 03qua)", q, qd, "%", SRC["fr1"], Y,
                       growth("fr1:rgdp", Y), rmse("gdp_realg"), "OxLon h=1 RMSE"))
    return out


def budget_rows(Y: int) -> list[dict]:
    out = []
    for ser, lab, plans in (
            ("dsk_budget_rev_ytd", "Dövlət büdcəsi gəlirləri: icra", {"bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R89"),
                                                                     "caem": ("ref", "CAEM.xlsx/MOE_report!R95"),
                                                                     "fr1": ("id", "fr1:rev_tot_n")}),
            ("dsk_budget_exp_ytd", "Dövlət büdcəsi xərcləri: icra", {"bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R90"),
                                                                    "caem": ("ref", "CAEM.xlsx/MOE_report!R96"),
                                                                    "fr1": ("id", "fr1:exp_tot_n")})):
        v, d = last("dsk_macro", ser)
        if d is None or d.year != Y:
            continue
        share = month_share(d)
        for src, sel in plans.items():
            plan = _val(sel, Y)
            ex = v / plan * 100 if np.isfinite(plan) and plan else np.nan
            out.append(row(ser + "_exec", f"{lab} (illik planın %-i)", ex, d, "%", SRC[src], Y, share * 100, 5.0,
                           "5 f.b. şərti miqyas (mövsümilik nəzərə alınmır)",
                           f"Yanvar–{d.month}. ay {v:,.0f} mln AZN; illik {plan:,.0f}".replace(",", " ")))
    bal, d = last("dsk_macro", "dsk_budget_bal_ytd")
    if d is not None and d.year == Y:
        for src, sel in (("bu60", ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R92")), ("fr1", ("id", "fr1:balance_n"))):
            out.append(row("dsk_budget_bal_ytd", "Dövlət büdcəsinin balansı (Yanvar–ay) vs illik fərziyyə", bal, d, "mln AZN",
                           SRC[src], Y, _val(sel, Y), 1500.0, "1 500 mln AZN şərti miqyas"))
    return out


def stock_rows(Y: int) -> list[dict]:
    out = []
    a, d = last("sofaz", "sofaz_assets_usd_mln")
    plan = base_ref("MOE REPORT 3 PAGES.xlsx/base 60!R96", Y)
    if np.isfinite(a):
        out.append(row("sofaz_assets", "ARDNF aktivləri vs Nazirlik ilsonu fərziyyəsi", a, d, "mln USD", SRC["bu60"], Y, plan,
                       0.05 * plan if np.isfinite(plan) else np.nan, "5 % şərti miqyas"))
    r, rd = last("dsk_macro", "dsk_reserves_usd_ytd")
    g, _ = last("dsk_macro", "dsk_reserves_usd_ytd_yoy")
    if np.isfinite(r):
        out.append(row("strategic_reserves_yoy", "Strateji valyuta ehtiyatları: illik artım", g, rd, "%", "sıfır istinadı", Y,
                       0.0, 10.0, "10 % şərti miqyas", f"səviyyə {r:,.1f} mln USD".replace(",", " ")))
    for feed, ser, lab in (("vix", None, "VIX (qlobal risk iştahı)"), ("ust10", None, "ABŞ 10 illik gəlirlilik"),
                           ("gpr", "gpr_global", "Geosiyasi risk (GPR qlobal)"), ("gpr", "gpr_rus", "Geosiyasi risk (Rusiya)"),
                           ("epu", None, "Qlobal siyasət qeyri-müəyyənliyi (EPU)")):
        h = _feed(feed, ser)
        if h.empty:
            continue
        cur, cd = float(h["value"].iloc[-1]), h["date"].iloc[-1]
        w = h[h["date"] > cd - pd.Timedelta(days=3653)]["value"]
        out.append(row(f"{feed}_{ser or ''}".strip("_"), lab, cur, cd, "", "son 10 ilin ortası", Y, float(w.mean()),
                       float(w.std()), "son 10 ilin sd"))
    return out


def daily_monitor(Y: int | None = None) -> pd.DataFrame:
    Y = Y or config.as_of().year
    rows = []
    for f in (brent_rows, fx_rows, rate_rows, cpi_rows, gdp_rows, budget_rows, stock_rows):
        try:
            rows += f(Y)
        except Exception as exc:                     # noqa: BLE001 — one failing block must not stop the monitor
            rows.append({"indicator": f.__name__, "label_az": "hesablanmadı", "note": f"{type(exc).__name__}: {exc}"[:200],
                         "signal": "xəta"})
    return pd.DataFrame(rows, columns=D5_COLS)


# ---------------------------------------------------------------- D6: translation into forecast impact
def _chain():
    root = str(config.MICRO_DIR)
    if root not in sys.path:
        sys.path.insert(0, root)
    from microlib.engines import chain
    return chain


def _flatten(res: dict) -> dict[tuple[str, int], float]:
    out = {}
    for m, r in res.get("results", {}).items():
        for sid, by in r.get("series", {}).items():
            for y, v in by.items():
                if v is not None and np.isfinite(v):
                    out[(sid, int(y))] = float(v)
    return out


_BASE_RUN = {}


def chain_impact(driver: str, exo_id: str, path: dict, note: str, extra: dict | None = None) -> pd.DataFrame:
    """Re-solve the MicroUnit chain with one FR1 exogenous path replaced (plus optional `extra` {exo: {year: v}});
    delta vs the no-override engine run."""
    ch = _chain()
    if "base" not in _BASE_RUN:
        _BASE_RUN["base"] = _flatten(ch.run_chain({}, scenario="Baseline"))
    b = _BASE_RUN["base"]
    years = [2026, 2027, 2028, 2029, 2030]
    base_path = [base(f"fr1:exo:{exo_id}", y) for y in years]
    new_path = [float(path.get(y, bp)) for y, bp in zip(years, base_path)]
    t0 = time.time()
    exo = {exo_id: new_path}
    for k, pth in (extra or {}).items():
        exo[k] = [float(pth.get(y, base(f"fr1:exo:{k}", y))) for y in years]
    res = ch.run_chain({"FR1": {"exogenous": exo}}, scenario="Baseline")
    n = _flatten(res)
    cat = upstream.catalog()[["id", "label_az", "unit"]].set_index("id")
    rows = []
    for (sid, y), v in n.items():
        bv = b.get((sid, y))
        if bv is None or abs(v - bv) < 1e-9 * max(1.0, abs(bv)):
            continue
        rows.append({"driver": driver, "target_id": sid, "label_az": cat["label_az"].get(sid, sid),
                     "unit": cat["unit"].get(sid, ""), "year": y, "baseline": bv, "implied": v, "delta": v - bv,
                     "delta_pct": (v / bv - 1) * 100 if bv > 0 and v > 0 and abs(v / bv - 1) <= 5 else np.nan,
                     "channel": f"MicroUnit zənciri FR1→… ({exo_id})",
                     "source": "microlib.engines.chain.run_chain",
                     "scenario_note": note + (f"; {CHAINLINK}" if sid == "fr1:rgdp" and exo_id in ("brent", "fx") else "")})
    D = pd.DataFrame(rows, columns=D6_COLS)
    D.attrs["seconds"] = round(time.time() - t0, 2)
    D.attrs["warnings"] = [w for w in res.get("warnings", [])][:5]
    D.attrs["errors"] = {k: v for k, v in res.get("errors", {}).items() if not k.endswith("_trace")}
    D.attrs["path"] = dict(zip(years, new_path))
    D.attrs["base_path"] = dict(zip(years, base_path))
    return D


CHAINLINK = ("real ÜDM zəncirvari üsulla (əvvəlki ilin qiymətləri) hesablanır: neft qiyməti artanda azalan neft-qaz hasilatının "
             "çəkisi artır, ona görə real ÜDM baza ilə müqayisədə azala bilər (MikroUnit FR1 xəbərdarlığı) — fəallığı qeyri-neft "
             "ÜDM üzrə oxuyun")


def ru_layer_impact(path: dict) -> pd.DataFrame:
    """v2.1 (audit M2): the RU transmission channels that the joint simulation adds to FR1 for a Brent path —
    (a) R01 procyclical public-investment reaction in excess of FR1's own F4 response (SOFAZ-financed, balance-neutral);
    (b) Brent-linked import (incl. food) prices → CPI through the single external-price pass-through. Same functions
    as simulate.py (simulate.fiscal_reaction / simulate.brent_import_cpi), so D6 = FR2 transmission set."""
    from . import simulate
    years = list(config.FORECAST_YEARS)
    b0 = np.array([base("fr1:exo:brent", y) for y in years])
    bn = np.array([float(path.get(y, bb)) for y, bb in zip(years, b0)])
    r = simulate.fiscal_reaction(bn, b0)
    c_imp = simulate.brent_import_cpi(bn, b0)
    rows = []
    for t, y in enumerate(years):
        bv = base("fr1:rgdpnon", y)
        rows.append({"driver": "brent", "target_id": "fr1:rgdpnon", "label_az": "Real qeyri-neft ÜDM", "unit": "mln AZN (2015)",
                     "year": y, "baseline": bv, "implied": bv * (1 + r["g_lvl"][t] / 100), "delta": bv * r["g_lvl"][t] / 100,
                     "delta_pct": r["g_lvl"][t], "channel": "RU: R01 prosiklik investisiya reaksiyası (FR1-dən artıq hissə; simulate ilə eyni)",
                     "source": "riskunit.simulate.fiscal_reaction",
                     "scenario_note": f"Δ dövlət investisiyası {r['inv_bn'][t]:+.2f} mlrd AZN (real), ARDNF transferi ilə — büdcə balansına neytral"})
        for val, ch_ in ((r["cpi"][t], "RU: R01 investisiya reaksiyasının İQİ təsiri"),
                         (c_imp[t], "RU: Brent → idxal (ərzaq daxil) qiymətləri → İQİ (vahid ötürmə 'cpi_ext')")):
            rows.append({"driver": "brent", "target_id": "fr1:infl", "label_az": "İnflyasiya", "unit": "f.b.", "year": y,
                         "baseline": base("fr1:infl", y), "implied": base("fr1:infl", y) + val, "delta": val, "delta_pct": np.nan,
                         "channel": ch_, "source": "riskunit.simulate", "scenario_note": "FR1-də olmayan kanal (RU qatı)"})
    return pd.DataFrame(rows, columns=D6_COLS)


def fx_impact(Y: int) -> pd.DataFrame:
    """USD/AZN deviation from the FR1 assumption → the single FX module (total, chain part, overlay). Zero rows while
    the peg holds (|deviation| < 0,1 %)."""
    from . import fx
    usd, ud = last("cbar_fx", "cbar_usd")
    years = list(config.FORECAST_YEARS)
    fb = np.array([base("fr1:exo:fx", y) for y in years])
    if not np.isfinite(usd) or not np.isfinite(fb[0]) or abs(usd / fb[0] - 1) < 1e-3:
        return pd.DataFrame(columns=D6_COLS)
    f_rem = max(0.0, (12 - pd.Timestamp(config.as_of()).month) / 12)
    x = fx.path_from_fx(fb * (usd / fb[0]), fb)
    x[0] *= f_rem
    tot, ovl = fx.responses(x), fx.overlay(x)
    rows = []
    for k, tid, lab, unit in (("cpi", "fr1:infl", "İnflyasiya", "f.b."), ("nonoil_lvl", "fr1:rgdpnon", "Real qeyri-neft ÜDM", "% sapma"),
                              ("debt_gdp", "ru:debt_gdp", "Dövlət borcu / ÜDM", "f.b.")):
        for t, y in enumerate(years):
            for part, v in (("cəmi (kalibrlənmiş)", tot[k][0, t]), ("əlavə qat (cəmi − zəncir)", ovl[k][0, t])):
                rows.append({"driver": "usd_azn", "target_id": tid, "label_az": lab, "unit": unit, "year": y,
                             "baseline": np.nan, "implied": np.nan, "delta": float(v), "delta_pct": np.nan,
                             "channel": f"RU məzənnə modulu: {part}", "source": "riskunit.fx",
                             "scenario_note": f"USD/AZN {usd:.4f} ({ud.date() if ud is not None else ''}) vs FR1 {fb[0]:.4f}; səviyyə saxlanılır"})
    return pd.DataFrame(rows, columns=D6_COLS)


def macro_brent_impact(path: dict) -> pd.DataFrame:
    """OxLon CA response to Brent: finite difference of the published lo80/hi80 Brent scenarios per year."""
    rows = []
    for y, b_new in path.items():
        hi, lo = base("mx:current_account_brent_hi80", y), base("mx:current_account_brent_lo80", y)
        s = upstream.series("mx:brent_usd")
        s = s[s["year"] == y]
        if s.empty or not np.isfinite(hi) or not np.isfinite(lo):
            continue
        slope = (hi - lo) / float(s["hi80"].iloc[0] - s["lo80"].iloc[0])
        b0, ca0 = float(s["value"].iloc[0]), base("mx:current_account", y)
        d = slope * (b_new - b0)
        gdp = base("mx:gdp_nom", y)
        fx = base("mx:fx_usd_azn_avg", y) or 1.7
        note = f"elastiklik {slope:.1f} mln USD / 1 USD Brent; Brent {b0:.1f} → {b_new:.1f}"
        rows.append({"driver": "brent", "target_id": "mx:current_account", "label_az": "Cari hesab balansı", "unit": "mln USD",
                     "year": y, "baseline": ca0, "implied": ca0 + d, "delta": d, "delta_pct": d / abs(ca0) * 100 if ca0 else np.nan,
                     "channel": "OxLon: Brent lo80/hi80 ssenarilərindən cari hesab elastikliyi", "source": "forecast_long.csv",
                     "scenario_note": note})
        if np.isfinite(gdp):
            r0 = base("mx:ca_gdp_ratio", y)
            dr = d * fx / gdp * 100
            rows.append({"driver": "brent", "target_id": "mx:ca_gdp_ratio", "label_az": "Cari hesab / ÜDM", "unit": "%",
                         "year": y, "baseline": r0, "implied": r0 + dr, "delta": dr, "delta_pct": np.nan,
                         "channel": "OxLon: Brent lo80/hi80 elastikliyi (ÜDM sabit)", "source": "forecast_long.csv",
                         "scenario_note": note})
    return pd.DataFrame(rows, columns=D6_COLS)


def multiplier_impact(path: dict) -> pd.DataFrame:
    """Linear cross-check with the FR1 step responses to Brent +10 USD/bbl (sustained from 2026)."""
    m = pd.read_csv(config.MICRO_FILES["fr1_multipliers"])
    m = m.rename(columns={m.columns[0]: "shock", m.columns[1]: "year"})
    m = m[m["shock"] == "Brent +10 USD/bbl"].set_index("year")
    rows = []
    for var, lab, unit, kind in (("rgdpnon", "Real qeyri-neft ÜDM", "% sapma", "pct"), ("infl", "İnflyasiya", "f.b.", "pp"),
                                 ("balance_n", "Dövlət büdcəsinin balansı", "mln AZN", "lvl"), ("rgdp", "Real ÜDM", "% sapma", "pct")):
        for y, b_new in path.items():
            if y not in m.index or var not in m.columns:
                continue
            d_brent = b_new - base("fr1:exo:brent", y)
            resp = float(m.at[y, var]) * d_brent / 10
            bv = base(f"fr1:{var}", y)
            delta = resp * bv / 100 if kind == "pct" and np.isfinite(bv) else resp
            rows.append({"driver": "brent", "target_id": f"fr1:{var}", "label_az": lab, "unit": unit, "year": y, "baseline": bv,
                         "implied": bv + delta if np.isfinite(bv) else np.nan, "delta": delta,
                         "delta_pct": resp if kind == "pct" else np.nan,
                         "channel": "FR1 multiplikatoru (Brent +10, xətti miqyas)", "source": "FR1_multipliers.csv",
                         "scenario_note": f"ΔBrent {d_brent:+.1f} USD"})
    return pd.DataFrame(rows, columns=D6_COLS)


def observation_impact(D5: pd.DataFrame, Y: int) -> pd.DataFrame:
    """Labelled observation arithmetic: implied annual CPI / GDP from the Jan–M outturn, revenue at the current
    execution pace, SOFAZ revaluation from gold / EUR moves since the last SOFAZ report."""
    rows = []
    tgt = {"cpi_implied_annual": {"OxLon §15.5.1": "mx:cpi_infl", "MicroUnit FR1": "fr1:infl", "BVF Art. IV": "mx:imf:cpi_infl"},
           "dsk_gdp_ytd_yoy": {"OxLon §15.5.1": "mx:gdp_realg", "MicroUnit FR1": "fr1:rgdp"},
           "dsk_gdp_nonoil_ytd_yoy": {"OxLon §15.5.1": "mx:nonoil_realg", "MicroUnit FR1": "fr1:rgdpnon"},
           "dsk_gdp_oil_ytd_yoy": {"OxLon §15.5.1": "mx:oil_realg", "MicroUnit FR1": "fr1:rgdpoil"}}
    for ind, m in tgt.items():
        for r in D5[D5["indicator"] == ind].itertuples():
            if r.baseline_source in m and np.isfinite(r.latest) and np.isfinite(r.baseline_assumption):
                rows.append({"driver": ind.replace("_implied_annual", "").replace("_ytd_yoy", ""), "target_id": m[r.baseline_source],
                             "label_az": r.label_az, "unit": "%", "year": Y, "baseline": r.baseline_assumption,
                             "implied": r.latest, "delta": r.deviation, "delta_pct": np.nan,
                             "channel": "müşahidə hesabı (Yanvar–ay faktiki; qalan aylarda son templər saxlanılır)",
                             "source": "DSK", "scenario_note": r.note})
    for r in D5[D5["indicator"] == "dsk_budget_rev_ytd_exec"].itertuples():
        if r.baseline_source == "MicroUnit FR1" and np.isfinite(r.latest):
            plan = base("fr1:rev_tot_n", Y)
            pace = plan * r.latest / r.baseline_assumption if r.baseline_assumption else np.nan
            rows.append({"driver": "budget_execution", "target_id": "fr1:rev_tot_n", "label_az": "Dövlət büdcəsi gəlirləri",
                         "unit": "mln AZN", "year": Y, "baseline": plan, "implied": pace, "delta": pace - plan,
                         "delta_pct": (pace / plan - 1) * 100 if plan else np.nan,
                         "channel": "icra tempi (Yanvar–ay icrası / ötən ay payı; mövsümilik nəzərə alınmır)", "source": "DSK",
                         "scenario_note": r.note})
    gold_mln, gd = last("sofaz", "sofaz_gold_usd_mln")
    xau = _feed("cbar_fx", "cbar_xau")
    usd = _feed("cbar_fx", "cbar_usd").set_index("date")["value"]
    if np.isfinite(gold_mln) and len(xau) and gd is not None:
        then = xau[xau["date"] <= gd]
        if len(then):
            g0, g1 = float(then["value"].iloc[-1]), float(xau["value"].iloc[-1])
            d = gold_mln * (g1 / g0 - 1)
            a0, _ = last("sofaz", "sofaz_assets_usd_mln")
            rows.append({"driver": "gold", "target_id": "sofaz:assets_usd", "label_az": "ARDNF aktivləri (qızıl yenidənqiymətləndirməsi)",
                         "unit": "mln USD", "year": Y, "baseline": a0, "implied": a0 + d, "delta": d, "delta_pct": d / a0 * 100,
                         "channel": "ARDNF qızıl payı × XAU dəyişməsi (AMB bülleteni, AZN; USD peqi)", "source": "ARDNF + AMB",
                         "scenario_note": f"XAU {g0:.0f} → {g1:.0f} AZN ({gd.date()} → bu gün)"})
    eur_mln, ed = last("sofaz", "sofaz_ccy_eur_mln")
    eur = _feed("cbar_fx", "cbar_eur")
    if np.isfinite(eur_mln) and len(eur) and ed is not None and len(usd):
        then = eur[eur["date"] <= ed]
        if len(then):
            e0 = float(then["value"].iloc[-1]) / float(usd[usd.index <= ed].iloc[-1])
            e1 = float(eur["value"].iloc[-1]) / float(usd.iloc[-1])
            d = eur_mln * (e1 - e0)
            a0, _ = last("sofaz", "sofaz_assets_usd_mln")
            rows.append({"driver": "eur_usd", "target_id": "sofaz:assets_usd", "label_az": "ARDNF aktivləri (EUR portfelinin yenidənqiymətləndirməsi)",
                         "unit": "mln USD", "year": Y, "baseline": a0, "implied": a0 + d, "delta": d, "delta_pct": d / a0 * 100,
                         "channel": "ARDNF EUR mövqeyi × EUR/USD dəyişməsi (AMB kross-kursu)", "source": "ARDNF + AMB",
                         "scenario_note": f"EUR/USD {e0:.4f} → {e1:.4f}"})
    return pd.DataFrame(rows, columns=D6_COLS)


def forecast_impact(D5: pd.DataFrame, Y: int) -> pd.DataFrame:
    parts = []
    b = brent_implied()
    if b:
        note = (f"Brent: {Y} = YTD ortası {b['ytd']:.2f} + qalan günlər üçün spot {b['spot']:.2f}; sonrakı illər spot "
                "səviyyəsində saxlanılır (şərti ssenari, proqnoz deyil)")
        try:
            parts.append(chain_impact("brent", "brent", b["path"], note))
        except Exception as exc:                     # noqa: BLE001
            print(f"  DİQQƏT: MicroUnit zənciri işləmədi ({type(exc).__name__}: {exc})")
        parts += [macro_brent_impact(b["path"]), multiplier_impact(b["path"])]
        try:
            parts.append(ru_layer_impact(b["path"]))
        except Exception as exc:                     # noqa: BLE001
            print(f"  DİQQƏT: RU qatı (R01 reaksiyası) hesablanmadı ({type(exc).__name__}: {exc})")
    try:
        parts.append(fx_impact(Y))
    except Exception as exc:                         # noqa: BLE001
        print(f"  DİQQƏT: məzənnə modulu hesablanmadı ({type(exc).__name__}: {exc})")
    p = policy_implied()
    if p:
        try:
            # v2.1: same rate shock definition as scalability/FR1 multiplier: deposit rate moves 0,5× the policy rate
            dep = {y: base("fr1:exo:deprate", y) + 0.5 * (v - base("fr1:exo:polrate", y)) for y, v in p["path"].items()}
            parts.append(chain_impact("policy_rate", "polrate", p["path"],
                                      f"Uçot dərəcəsi: {Y} effektiv orta {p['path'].get(Y, np.nan):.3f}; sonrakı illər cari "
                                      f"{p['rate']:.2f} saxlanılır; depozit faizi 0,5× (G3 kredit faizi — FR1-də real təsiri yoxdur)",
                                      extra={"deprate": dep}))
        except Exception as exc:                     # noqa: BLE001
            print(f"  DİQQƏT: uçot dərəcəsi zənciri işləmədi ({type(exc).__name__}: {exc})")
    parts.append(observation_impact(D5, Y))
    parts = [x for x in parts if len(x)]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=D6_COLS)


HEADLINE = ["fr1:rgdp", "fr1:rgdpnon", "fr1:infl", "fr1:balance_n", "fr1:rev_tot_n", "fr1:gdp_n", "mx:current_account",
            "mx:ca_gdp_ratio", "sofaz:assets_usd"]


def changes(D5: pd.DataFrame, D6: pd.DataFrame, today: str) -> pd.DataFrame:
    """D7: compare with the most recent snapshot from an earlier day (or the previous run today if none)."""
    H = config.MONITOR_HISTORY
    prev = sorted(p for p in H.glob("D5_*.csv") if p.stem[3:] < today)
    rows = []
    key = ["indicator", "baseline_source", "baseline_year"]
    if prev:
        P = pd.read_csv(prev[-1])
        ref_day = prev[-1].stem[3:]
        M = D5.merge(P[key + ["latest", "date", "signal"]], on=key, how="outer", suffixes=("", "_prev"), indicator="merge_how")
        for r in M.itertuples():
            ch = r.latest - r.latest_prev if np.isfinite(r.latest) and np.isfinite(r.latest_prev) else np.nan
            if r.merge_how == "both" and (not np.isfinite(ch) or abs(ch) < 1e-12) and r.signal == r.signal_prev \
                    and str(r.date) == str(r.date_prev):
                continue
            rows.append({"kind": "göstərici", "item": r.indicator, "label_az": r.label_az, "baseline_source": r.baseline_source,
                         "previous": r.latest_prev, "previous_date": r.date_prev, "latest": r.latest, "date": r.date,
                         "change": ch, "change_pct": ch / abs(r.latest_prev) * 100 if np.isfinite(ch) and r.latest_prev else np.nan,
                         "previous_signal": r.signal_prev, "signal": r.signal,
                         "signal_changed": str(r.signal) != str(r.signal_prev), "reference_day": ref_day})
        p6 = H / f"D6_headline_{ref_day}.csv"
        if p6.exists():
            Q = pd.read_csv(p6)
            cur = D6[D6["target_id"].isin(HEADLINE)].groupby(["driver", "target_id", "year", "channel"], as_index=False)["delta"].sum()
            M6 = cur.merge(Q, on=["driver", "target_id", "year", "channel"], how="outer", suffixes=("", "_prev"))
            for r in M6.itertuples():
                if np.isfinite(r.delta) and np.isfinite(r.delta_prev) and abs(r.delta - r.delta_prev) < 1e-9:
                    continue
                rows.append({"kind": "proqnoz təsiri", "item": f"{r.driver}→{r.target_id} {r.year}", "label_az": r.channel,
                             "previous": r.delta_prev, "latest": r.delta, "change": r.delta - r.delta_prev
                             if np.isfinite(r.delta) and np.isfinite(r.delta_prev) else np.nan, "reference_day": ref_day})
    man = feeds.read_manifest()
    ok = man[man["status"] == "ok"]
    for feed, g in ok.groupby("feed"):
        g = g.drop_duplicates("sha256")
        if len(g) >= 2 and g.iloc[-1]["vintage"] == today:
            a, b = g.iloc[-2], g.iloc[-1]
            rows.append({"kind": "axın", "item": feed, "label_az": "yeni vintaj", "previous": float(a["n_obs"]),
                         "previous_date": a["last_obs"], "latest": float(b["n_obs"]), "date": b["last_obs"],
                         "change": float(b["n_obs"]) - float(a["n_obs"]), "reference_day": a["vintage"]})
    return pd.DataFrame(rows)


def run(ctx: dict | None = None, verbose: bool = True) -> dict:
    from . import spine
    t0 = time.time()
    Y = (ctx or {}).get("year") or config.as_of().year
    today = config.as_of().isoformat()
    D5 = daily_monitor(Y)
    D6 = forecast_impact(D5, Y)
    D7 = changes(D5, D6, today)
    D5.to_csv(config.OUTPUT / "D5_daily_monitor.csv", index=False, float_format="%.6g")
    D6.to_csv(config.OUTPUT / "D6_forecast_impact.csv", index=False, float_format="%.6g")
    D7.to_csv(config.OUTPUT / "D7_changes.csv", index=False, float_format="%.6g")
    D5.to_csv(config.MONITOR_HISTORY / f"D5_{today}.csv", index=False, float_format="%.6g")
    hd = D6[D6["target_id"].isin(HEADLINE)].groupby(["driver", "target_id", "year", "channel"], as_index=False)["delta"].sum()
    hd.to_csv(config.MONITOR_HISTORY / f"D6_headline_{today}.csv", index=False, float_format="%.6g")
    spine.register_output("D5_daily_monitor.csv", "monitor", "Gündəlik monitor: son müşahidə (Brent, məzənnələr, uçot dərəcəsi, İQİ, "
                          "DSK ÜDM, büdcə icrası, ARDNF, qlobal risk) PROQNOZ FƏRZİYYƏSİNƏ GÖRƏ — bölmələrin baza fərziyyəsindən sapma, "
                          "z = sapma/σ (σ — bölmənin proqnoz xətası), ikitərəfli siqnal (|z| ≥ 1 diqqət, ≥ 2 xəbərdarlıq). "
                          "Tarixi paylanmaya görə vəziyyət FR1_indicator_base-dədir (eyni səviyyə orada «normal» ola bilər)",
                          D5_COLS, "gündəlik")
    spine.register_output("D6_forecast_impact.csv", "monitor", "Proqnoz təsiri: sapmaların MicroUnit zənciri (FR1→FR12 bütün "
                          "komponentlər), OxLon elastiklikləri, FR1 multiplikatorları və müşahidə hesabı ilə proqnozlara ötürülməsi",
                          D6_COLS, "gündəlik")
    spine.register_output("D7_changes.csv", "monitor", "Nə dəyişdi: əvvəlki günə nisbətən göstərici, siqnal və əsas proqnoz təsiri "
                          "dəyişmələri, yeni məlumat vintajları", list(D7.columns) if len(D7) else
                          ["kind", "item", "label_az", "previous", "latest", "change"], "gündəlik")
    out = {"D5": D5, "D6": D6, "D7": D7, "seconds": round(time.time() - t0, 1)}
    if verbose:
        alerts = D5[D5["signal"].astype(str).str.startswith("xəbərdarlıq")]
        print(f"  monitor: {len(D5)} göstərici ({len(alerts)} xəbərdarlıq), {len(D6)} təsir sətri, {len(D7)} dəyişiklik "
              f"({out['seconds']} san)")
        for r in alerts.drop_duplicates("indicator").head(8).itertuples():
            print(f"    {r.label_az[:50]:50s} {r.latest:10.3f} vs {r.baseline_assumption:10.3f} ({r.baseline_source}) z={r.z_score:+.1f}")
    return out


if __name__ == "__main__":
    run()
