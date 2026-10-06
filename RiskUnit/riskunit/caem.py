"""CAEM risk-category worksheets in RiskUnit v2 (outputs C1–C6).

The Ministry's CAEM workbook carries four σ-band signal sheets (`Risk-oil price`, `Risk-food
price`, `Risk-import price`, `Risk-gdp tp`) and a hand-scored `Balance of risks`. This module
(1) reproduces the σ-band classification exactly and recomputes it on current data, (2) puts
the Ministry's typed balance of risks beside a data-driven one built from RU's quantitative
outputs, (3) maps CAEM categories onto the RU risk register, (4) runs the `AZE Model` shock
library as a labelled Ministry cross-check (`caem_model`) and (5) logs CAEM defects for the
Ministry. RU publishes no central path: forecast years use the OxLon / MicroUnit baselines.

    python3 -m riskunit.caem [--fetch] [--no-fr13]
"""
from __future__ import annotations

import os
import sys
import urllib.request
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from . import config
from . import caem_model as cm

OUT = config.OUTPUT
OXLON_OUT = cm.OXLON_OUT
OXLON_DATA = cm.OXLON_DIR / "model 2" / "data"
FOOD_FEED = "fred_pfoodindexm"
FOOD_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=PFOODINDEXM"

# σ-band specification as the FORMULAS compute it (not as the headers say).
#   edges e1<e2<e3 in sd units; low_bad: a value below the mean is unfavourable for AZE.
SPEC = {
    "oil_brent": {"az": "Brent neft qiyməti", "unit": "USD/barel (səviyyə)", "edges": (0.5, 1.0, 1.5),
                  "low_bad": True, "sheet": "Risk-oil price",
                  "rule": "N:T sütunları, N1:T2 kəsikləri: <-1,5 | -1,5:-1 | -1:-0,5 | ±0,5 | 0,5:1 | 1:1,5 | >1,5 σ"},
    "food_price": {"az": "Dünya ərzaq qiymətləri", "unit": "illik artım, %", "edges": (0.5, 1.0, 1.5),
                   "low_bad": False, "sheet": "Risk-food price",
                   "rule": "P:V sütunları, Q1:V2 kəsikləri: ±0,5/1/1,5 σ; aşağı = əlverişli"},
    "import_price": {"az": "İdxal qiymətləri", "unit": "illik artım, %", "edges": (1.0, 1.5, 2.0),
                     "low_bad": False, "sheet": "Risk-import price",
                     "rule": "E:K sütunları, F1:K2 kəsikləri: <-2 | -2:-1,5 | -1,5:-1 | ±1 | 1:1,5 | 1,5:2 | >2 σ "
                             "(başlıq ±0,5/1/1,5 yazır)"},
    "tp_gdp": {"az": "Ticarət tərəfdaşlarının real ÜDM artımı", "unit": "illik artım, %",
               "edges": (1.0, 1.5, 2.0), "low_bad": True, "sheet": "Risk-gdp tp",
               "rule": "E:K sütunları, F1:K2 kəsikləri: ±1/1,5/2 σ (başlıq ±0,5/1/1,5 yazır)"},
    "geopolitics": {"az": "Regional geosiyasi risk (GPR)", "unit": "indeks (illik orta)",
                    "edges": (0.5, 1.0, 1.5), "low_bad": False, "sheet": "— (CAEM-də vərəq yoxdur)",
                    "rule": "RU əlavəsi: Nazirliyin ±0,5/1/1,5 σ qaydası GPR-ə tətbiq edilir"},
}
CLASS_AZ = {"neg": "mənfi", "neu": "neytral", "fav": "əlverişli"}


def band_of(z: float, edges) -> int:
    """1..7 as the sheets number them; a value exactly on an edge (which the strict IF()
    inequalities leave unclassified) is put in the inner band."""
    e1, e2, e3 = edges
    if not np.isfinite(z):
        return 0
    a = abs(z)
    k = 0 if a <= e1 else 1 if a <= e2 else 2 if a <= e3 else 3
    return 4 + k if z > 0 else 4 - k


def class_of(band: int, low_bad: bool) -> str:
    if band == 0:
        return ""
    if band == 4:
        return CLASS_AZ["neu"]
    below = band < 4
    return CLASS_AZ["neg"] if below == low_bad else CLASS_AZ["fav"]


def score_of(z: float, edges, low_bad: bool) -> float:
    """Ministry 0–5 scale written under the band columns (`Risk-oil price` N31:T31,
    `Risk-food price` P43:V43, `Risk-import price` E26:K26): neutral band ↔ 2–3, each further
    band ↔ one point, beyond the last edge ↔ 5 (or 0). Piecewise linear, continuous, monotone in
    the unfavourable-direction deviation z_u (= −z when a low value is bad)."""
    if not np.isfinite(z):
        return np.nan
    zu = -z if low_bad else z
    e1, e2, e3 = edges
    a = abs(zu)
    if a <= e1:
        d = 0.5 * a / e1
    elif a <= e2:
        d = 0.5 + (a - e1) / (e2 - e1)
    elif a <= e3:
        d = 1.5 + (a - e2) / (e3 - e2)
    else:
        d = 2.5
    return float(np.clip(2.5 + np.sign(zu) * d, 0, 5))


def stats(x) -> tuple[float, float]:
    """Mean and STDEV.P, exactly the Ministry's formulas."""
    x = pd.Series(x, dtype=float).dropna()
    return float(x.mean()), float(x.std(ddof=0))


# ---------------------------------------------------------------- Ministry worksheet contents
def _period_index(labels) -> pd.DatetimeIndex:
    return pd.to_datetime([f"{s[:4]}-{s[5:7]}-01" for s in labels])


def ministry_sheets() -> dict:
    """Values of the four signal sheets and the balance of risks, read from the pinned copy."""
    S = {}
    o = cm.cells("Risk-oil price", 5, 255, 1, 2)
    S["oil_monthly"] = pd.Series([r[1] for r in o], index=_period_index([r[0] for r in o]), dtype=float)
    a = cm.cells("Risk-oil price", 5, 30, 12, 13)
    S["oil_annual"] = pd.Series({int(r[0]): float(r[1]) for r in a if r[0] is not None})
    S["oil_stats"] = (float(cm.cell("Risk-oil price", "M33")), float(cm.cell("Risk-oil price", "M34")))
    f = cm.cells("Risk-food price", 5, 267, 1, 3)
    S["food_monthly"] = pd.Series([r[1] for r in f], index=_period_index([r[0] for r in f]), dtype=float)
    S["food_yoy"] = pd.Series([r[2] for r in f], index=S["food_monthly"].index, dtype=float)
    fa = cm.cells("Risk-food price", 16, 42, 13, 15)
    S["food_annual"] = pd.Series({int(r[0]): (np.nan if r[2] is None else float(r[2])) for r in fa
                                  if r[0] is not None})
    S["food_stats"] = (float(cm.cell("Risk-food price", "O45")), float(cm.cell("Risk-food price", "O46")))
    im = cm.cells("Risk-import price", 5, 25, 2, 4)
    S["import_annual"] = pd.Series({int(r[0]): (np.nan if r[2] is None else float(r[2])) for r in im})
    S["import_stats"] = (float(cm.cell("Risk-import price", "D28")), float(cm.cell("Risk-import price", "D29")))
    tp = cm.cells("Risk-gdp tp", 5, 34, 2, 4)
    S["tp_annual"] = pd.Series({int(r[0]): (np.nan if r[2] is None else float(r[2])) for r in tp})
    S["tp_stats"] = (float(cm.cell("Risk-gdp tp", "D37")), float(cm.cell("Risk-gdp tp", "D38")))
    b = cm.cells("Balance of risks", 1, 8, 1, 5)
    yrs = [int(v) for v in b[0][1:4]]
    S["bor"] = pd.DataFrame([{"category": r[0], "year": y, "score": float(r[1 + i]), "weight": float(r[4])}
                             for r in b[1:6] for i, y in enumerate(yrs)])
    S["bor_total"] = {y: float(b[7][1 + i]) for i, y in enumerate(yrs)}
    og = cm.cells("Oil_and_gas_sector", 69, 69, 4, 38)[0]
    S["oil_model"] = pd.Series({1995 + i: float(v) for i, v in enumerate(og) if isinstance(v, (int, float))})
    return S


# ---------------------------------------------------------------- current-data loaders
def _csv(p) -> pd.DataFrame:
    return pd.read_csv(p, float_precision="round_trip")


def oxlon_fl() -> pd.DataFrame:
    p = OXLON_OUT / "forecast_long.csv"
    return _csv(p if p.exists() else config.MACRO_FILES["forecast_long"])


def oxlon_series(code: str, kind: str) -> pd.Series:
    f = oxlon_fl()
    f = f[(f.series_code == code) & (f.source == "ours") & (f.kind == kind)]
    return f.drop_duplicates("year", keep="last").set_index("year")["value"].astype(float)


def oxlon_assumption(key: str) -> pd.Series:
    p = OXLON_OUT / "assumptions.csv"
    a = _csv(p if p.exists() else config.MACRO_FILES["assumptions"])
    return a[a.assumption_key == key].set_index("year")["value"].astype(float)


def external_block() -> pd.DataFrame:
    p = OXLON_DATA / "external_block_annual.csv"
    return _csv(p if p.exists() else config.MACRO_FILES["external_block"]).set_index("year")


def fr1_baseline(col: str) -> pd.Series:
    mf = _csv(config.MICRO_FILES["fr1_forecast"])
    mf = mf[mf["scenario"] == "Baseline"].set_index(mf.columns[0])
    return mf[col].astype(float)


def fr1_history(col: str) -> pd.Series:
    d = _csv(config.MICRO_DIR / "output" / "FR1_analysis_dataset.csv").set_index("year")
    return d[col].astype(float)


def brent_monthly() -> pd.Series | None:
    """Monthly mean of the RU Brent feed (FRED DCOILBRENTEU), complete months only."""
    try:
        from . import feeds
        d = feeds.latest("brent")
    except Exception:
        return None
    d["date"] = pd.to_datetime(d["date"])
    asof = pd.Timestamp(config.as_of())
    d = d[d["date"] < asof.to_period("M").to_timestamp()]
    return d.set_index("date")["value"].resample("MS").mean().dropna()


def brent_ytd() -> tuple[float, int, str] | None:
    try:
        from . import feeds
        d = feeds.latest("brent")
    except Exception:
        return None
    d["date"] = pd.to_datetime(d["date"])
    asof = pd.Timestamp(config.as_of())
    y = d[(d["date"].dt.year == asof.year) & (d["date"] <= asof)]
    if y.empty:
        return None
    return float(y["value"].mean()), int(len(y)), y["date"].max().date().isoformat()


def _food_cache_dir() -> Path:
    return config.VINTAGES / FOOD_FEED


def fetch_food(timeout: int = 20) -> dict:
    """IMF global food price index (FRED PFOODINDEXM, monthly) — current proxy for the FAO
    index of `Risk-food price` (the CAEM series stops at 2024M11). Polite single request,
    cached under data/vintages/fred_pfoodindexm/<date>/; RISK_NO_NETWORK=1 disables it."""
    day = config.as_of().isoformat()
    dest = _food_cache_dir() / day / "PFOODINDEXM.csv"
    st = {"feed": FOOD_FEED, "url": FOOD_URL, "vintage": day, "path": str(dest)}
    if os.environ.get("RISK_NO_NETWORK") == "1":
        return {**st, "status": "şəbəkə söndürülüb (RISK_NO_NETWORK=1) — keş"}
    if dest.exists():
        return {**st, "status": "bu günün keşi mövcuddur"}
    try:
        req = urllib.request.Request(FOOD_URL, headers={"User-Agent": "MIIS-15.5.3-risk-unit"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
        d = pd.read_csv(__import__("io").BytesIO(raw))
        if d.shape[1] != 2 or len(d) < 100:
            raise ValueError("gözlənilməz format")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        return {**st, "status": f"yeniləndi ({len(d)} müşahidə)"}
    except Exception as e:  # network or format failure → last good cache is used
        return {**st, "status": f"xəta: {type(e).__name__} — son keş istifadə olunur"}


def food_monthly() -> tuple[pd.Series | None, str]:
    vs = sorted(p for p in _food_cache_dir().glob("*/PFOODINDEXM.csv")) if _food_cache_dir().exists() else []
    if not vs:
        return None, ""
    d = pd.read_csv(vs[-1])
    d.columns = ["date", "value"]
    d["value"] = pd.to_numeric(d["value"], errors="coerce")
    s = d.dropna().set_index(pd.to_datetime(d.dropna()["date"]))["value"]
    return s, vs[-1].parent.name


def fpi_weo_growth() -> pd.Series:
    p = cm.MINISTRY_ROOT / "eviews" / "eviews_data.csv"
    if not p.exists():
        return pd.Series(dtype=float)
    e = pd.read_csv(p, index_col="year")["FPI_WEO"]
    return (e.pct_change(fill_method=None) * 100).astype(float)


def gpr_regional_annual() -> tuple[pd.Series, pd.Series | None]:
    """Annual mean of the regional GPR (Russia, Ukraine, Israel, Türkiye country indices —
    the RU indicator `gpr_reg`); complete years and the running year separately."""
    from . import feeds
    d = feeds.latest("gpr")
    d = d[d["series"].isin(["gpr_rus", "gpr_ukr", "gpr_isr", "gpr_tur"])]
    d["date"] = pd.to_datetime(d["date"])
    m = d.pivot_table(index="date", columns="series", values="value").mean(axis=1)
    g = m.groupby(m.index.year)
    n = g.size()
    full = g.mean()[n == 12]
    cur = config.as_of().year
    ytd = g.mean().get(cur) if cur in n.index else None
    return full[full.index < cur], (None if ytd is None else pd.Series({cur: float(ytd)}))


# ---------------------------------------------------------------- C1: σ-band signals
def _rows(ind, values: pd.Series, mean, sd, source, variant, period, basis, primary=False,
          edges=None) -> list[dict]:
    sp = SPEC[ind]
    edges = edges or sp["edges"]
    out = []
    for yr, v in values.dropna().items():
        z = (v - mean) / sd if sd > 0 else np.nan
        b = band_of(z, edges)
        out.append({"indicator": ind, "indicator_az": sp["az"], "year": int(yr), "value": round(float(v), 4),
                    "mean": round(mean, 4), "sd": round(sd, 4), "z": round(float(z), 4), "band": b,
                    "class_az": class_of(b, sp["low_bad"]),
                    "score_0_5": round(score_of(z, edges, sp["low_bad"]), 3),
                    "source": source, "variant": variant, "period": period, "stat_basis": basis,
                    "primary": primary})
    return out


def _period(yr: int) -> str:
    return "tarix" if yr <= config.LAST_ACTUAL else "proqnoz"


def _split(s: pd.Series, src, mean, sd, ind, basis, primary_hist=True, primary_fc=True, variant="cari"):
    s = s.dropna()
    h, f = s[s.index <= config.LAST_ACTUAL], s[s.index > config.LAST_ACTUAL]
    return (_rows(ind, h, mean, sd, src, variant, "tarix", basis, primary_hist)
            + _rows(ind, f, mean, sd, src, variant, "proqnoz", basis, primary_fc))


def _signals_oil_food(S: dict) -> list[dict]:
    R: list[dict] = []
    cur = config.as_of().year
    fc_yrs = config.FORECAST_YEARS
    # --- oil (level vs mean of MONTHLY Brent, STDEV.P; Ministry: B5:B255 = 2004M01-2024M11)
    bm = brent_monthly()
    if bm is not None and len(bm) > 100:
        bm = bm[bm.index >= "2004-01-01"]
        mo, so = stats(bm)
        basis = f"aylıq Brent (FRED) {bm.index[0]:%Y-%m}–{bm.index[-1]:%Y-%m}, n={len(bm)}"
    else:
        mo, so = S["oil_stats"]
        basis = "CAEM aylıq Brent 2004M01–2024M11 (lent əlçatan deyil)"
    hist = oxlon_series("brent_usd", "actual")
    src_h = "OxLon faktiki (forecast_long, source=ours)"
    if hist.empty:
        hist, src_h = fr1_history("brent"), "MikroUnit FR1 analiz dəsti"
    R += _rows("oil_brent", hist[hist.index >= 2004], mo, so, src_h, "cari", "tarix", basis, True)
    ytd = brent_ytd()
    if ytd:
        R += _rows("oil_brent", pd.Series({cur: ytd[0]}), mo, so,
                   f"canlı: FRED Brent, {cur} ilin əvvəlindən orta ({ytd[1]} gün, son {ytd[2]})",
                   "cari", "canlı", basis)
    R += _rows("oil_brent", oxlon_series("brent_usd", "forecast").reindex(fc_yrs), mo, so,
               "OxLon baza (source=ours)", "cari", "proqnoz", basis, True)
    R += _rows("oil_brent", fr1_baseline("oil_exp_price").reindex(fc_yrs), mo, so,
               "MikroUnit FR1 baza (neft ixrac qiyməti)", "cari", "proqnoz", basis)
    R += _rows("oil_brent", S["oil_annual"][S["oil_annual"].index >= 2025], mo, so,
               "CAEM `Risk-oil price` yolu (M26:M30)", "cari", "proqnoz", basis)
    R += _rows("oil_brent", S["oil_model"].loc[2025:2029], mo, so,
               "CAEM model Brent (`Oil_and_gas_sector` r69)", "cari", "proqnoz", basis)
    mm, ms = S["oil_stats"]
    R += [dict(r, period=_period(r["year"])) for r in _rows(
        "oil_brent", S["oil_annual"], mm, ms, "CAEM orijinal (Nazirlik statistikası, təkrar)",
        "nazirlik_orijinal", "", "M33/M34: aylıq 2004M01–2024M11")]
    # --- food (annual growth vs mean/sd of MONTHLY y/y growth — the Ministry convention)
    fm, vint = food_monthly()
    if fm is not None and len(fm) > 150:
        yoy = (fm / fm.shift(12) * 100 - 100).dropna()
        yoy = yoy[yoy.index >= "2004-01-01"]
        mf, sf = stats(yoy)
        basis = f"aylıq illik artım, IMF ərzaq indeksi (FRED PFOODINDEXM, keş {vint}) {yoy.index[0]:%Y-%m}–{yoy.index[-1]:%Y-%m}, n={len(yoy)}"
        g = fm.groupby(fm.index.year)
        ann = g.mean()[g.size() == 12]
        fh = (ann / ann.shift(1) * 100 - 100).dropna()
        fh = fh[(fh.index >= 2004) & (fh.index <= config.LAST_ACTUAL)]
        R += _rows("food_price", fh, mf, sf, "IMF qlobal ərzaq qiymətləri indeksi (FRED PFOODINDEXM)",
                   "cari", "tarix", basis, True)
        last = fm.index[-1]
        if last.year == cur:
            a = fm[(fm.index.year == cur)].mean()
            b = fm[(fm.index.year == cur - 1) & (fm.index.month <= last.month)].mean()
            R += _rows("food_price", pd.Series({cur: a / b * 100 - 100}), mf, sf,
                       f"canlı: {cur} yanvar–{last.month:02d} orta / {cur - 1} eyni aylar", "cari", "canlı", basis)
    else:
        mf, sf = S["food_stats"]
        basis = "CAEM aylıq FAO 2004M01–2024M11 (keş yoxdur)"
        R += _rows("food_price", S["food_annual"].loc[2004:config.LAST_ACTUAL], mf, sf,
                   "CAEM FAO illik artımı", "cari", "tarix", basis, True)
    R += _rows("food_price", fpi_weo_growth().reindex(fc_yrs), mf, sf,
               "OxLon fərziyyəsi (eviews_data FPI_WEO)", "cari", "proqnoz", basis, True)
    R += _rows("food_price", S["food_annual"].loc[2025:2029], mf, sf, "CAEM `Risk-food price` yolu (O38:O42)",
               "cari", "proqnoz", basis)
    mm, ms = S["food_stats"]
    R += [dict(r, period=_period(r["year"])) for r in _rows(
        "food_price", S["food_annual"].loc[2004:], mm, ms, "CAEM orijinal (Nazirlik statistikası, təkrar)",
        "nazirlik_orijinal", "", "O45/O46: aylıq illik artım 2004M01–2024M11")]
    return R


def _signals_import_tp_geo(S: dict) -> list[dict]:
    R: list[dict] = []
    fc_yrs = config.FORECAST_YEARS
    ext = external_block()
    # --- import prices: OxLon import_price_infl (USD, non-oil import deflator proxy)
    ih = ext["import_price_infl"].loc[2000:config.LAST_ACTUAL]
    mi, si = stats(ih)
    basis = f"OxLon external_block import_price_infl {ih.index[0]}–{ih.index[-1]}, n={len(ih)}, əlavəsiz"
    R += _split(pd.concat([ih, oxlon_assumption("import_price_infl").reindex(fc_yrs)]),
                "OxLon (tarix: external_block; proqnoz: assumptions.csv)", mi, si, "import_price", basis)
    R += _rows("import_price", ext["import_price_infl"].reindex(fc_yrs), mi, si,
               "OxLon external_block proqnozu (assumptions.csv ilə ziddiyyətli)", "cari", "proqnoz", basis)
    R += _rows("import_price", S["import_annual"].loc[2025:2029], mi, si,
               "CAEM `Risk-import price` yolu (D21:D25)", "cari", "proqnoz", basis)
    sel = ih.reindex(list(range(2010, 2017)) + [2024])          # D6:D12, D20 of the sheet
    mq, sq = stats(sel)
    mq, sq = mq + 0.8 + 1, sq + 1.3
    R += _split(pd.concat([ih, oxlon_assumption("import_price_infl").reindex(fc_yrs)]),
                "OxLon, Nazirlik qaydası ilə", mq, sq, "import_price",
                "Nazirlik qaydası: AVERAGE(2010–2016, 2024)+0,8+1; STDEV.P(...)+1,3", False, False,
                "nazirlik_qaydasi")
    mm, ms = S["import_stats"]
    R += [dict(r, period=_period(r["year"])) for r in _rows(
        "import_price", S["import_annual"].dropna(), mm, ms, "CAEM orijinal (Nazirlik statistikası, təkrar)",
        "nazirlik_orijinal", "", "D28/D29: seçilmiş illər + 1,8 pp / +1,3")]
    # --- trading-partner growth: OxLon partner_gdp_realg (WEO weights)
    th = ext["partner_gdp_realg"].loc[2001:config.LAST_ACTUAL]
    mt, st_ = stats(th)
    basis = f"OxLon external_block partner_gdp_realg {th.index[0]}–{th.index[-1]}, n={len(th)}"
    R += _split(pd.concat([th, oxlon_assumption("partner_gdp_realg").reindex(fc_yrs)]),
                "OxLon (tarix: external_block; proqnoz: assumptions.csv)", mt, st_, "tp_gdp", basis)
    R += _rows("tp_gdp", S["tp_annual"].loc[2025:2029], mt, st_, "CAEM `Risk-gdp tp` yolu (D30:D34)",
               "cari", "proqnoz", basis)
    mm, ms = S["tp_stats"]
    R += [dict(r, period=_period(r["year"])) for r in _rows(
        "tp_gdp", S["tp_annual"].dropna(), mm, ms, "CAEM orijinal (Nazirlik statistikası, təkrar)",
        "nazirlik_orijinal", "", "D37/D38: 2001–2024")]
    # --- geopolitics (no CAEM sheet; RU adds the same σ-band rule on the regional GPR)
    try:
        full, ytd = gpr_regional_annual()
        mg, sg = stats(full)
        basis = f"regional GPR illik orta {full.index[0]}–{full.index[-1]}, n={len(full)}"
        R += _rows("geopolitics", full.loc[2000:], mg, sg, "Caldara–Iacoviello GPR (RU lenti)", "cari",
                   "tarix", basis, True)
        if ytd is not None:
            R += _rows("geopolitics", ytd, mg, sg, "canlı: GPR, ilin əvvəlindən orta", "cari", "canlı",
                       basis, True)
    except Exception:
        pass
    return R


def signals(S: dict | None = None) -> pd.DataFrame:
    """C1: the four CAEM σ-band signals (+ GPR) recomputed on current data, the CAEM paths
    under current statistics, and an exact reproduction of the Ministry's own classification."""
    S = S or ministry_sheets()
    df = pd.DataFrame(_signals_oil_food(S) + _signals_import_tp_geo(S))
    order = {k: i for i, k in enumerate(SPEC)}
    df["_o"] = df["indicator"].map(order)
    return df.sort_values(["_o", "variant", "source", "year"], kind="stable").drop(columns="_o").reset_index(drop=True)


def reproduce_ministry_bands() -> pd.DataFrame:
    """Exactness check: Python band vs the non-zero band column the sheet itself computed."""
    S = ministry_sheets()
    spec = [("oil_brent", "Risk-oil price", 5, 30, 12, 14, S["oil_annual"], S["oil_stats"]),
            ("food_price", "Risk-food price", 17, 42, 13, 16, S["food_annual"], S["food_stats"]),
            ("import_price", "Risk-import price", 6, 25, 2, 5, S["import_annual"], S["import_stats"]),
            ("tp_gdp", "Risk-gdp tp", 6, 34, 2, 5, S["tp_annual"], S["tp_stats"])]
    rows = []
    for ind, sh, r0, r1, ycol, c0, ser, (mu, sd) in spec:
        yrs = [r[0] for r in cm.cells(sh, r0, r1, ycol, ycol)]
        bl = cm.block(sh, r0, r1, c0, c0 + 6)
        for yr, b in zip(yrs, bl):
            if yr is None or not np.isfinite(ser.get(int(yr), np.nan)):
                continue
            nz = np.flatnonzero(np.nan_to_num(b) != 0)
            sheet_band = int(nz[0]) + 1 if len(nz) == 1 else (4 if len(nz) == 0 else -1)
            z = (ser[int(yr)] - mu) / sd
            rows.append({"indicator": ind, "year": int(yr), "z": round(z, 4), "sheet_band": sheet_band,
                         "python_band": band_of(z, SPEC[ind]["edges"]),
                         "match": sheet_band == band_of(z, SPEC[ind]["edges"])})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- C2: balance of risks
CATEGORIES = [  # key, Ministry label (Balance of risks!A2:A6), AZ, weight, C1 indicator, RU risk, indicator-base id
    ("oil", "Oil prices", "Neft qiymətləri", 12, "oil_brent", "R01", "brent"),
    ("geo", "Geopolitical risks", "Geosiyasi risklər", 2, "geopolitics", "R06", "gpr_reg"),
    ("tp", "Regional trading partners growth", "Regional ticarət tərəfdaşlarının artımı", 2, "tp_gdp", "R05", None),
    ("imp", "Import prices", "İdxal qiymətləri", 2, "import_price", None, None),
    ("food", "Food prices", "Ərzaq qiymətləri", 2, "food_price", None, None),
]
BOR_YEARS = list(range(2022, 2031))


def read_off(total: float) -> str:
    if total > 55:
        return "risklər mənfi makroiqtisadi nəticələrə doğru meyllidir (>55)"
    if total >= 45:
        return "risklər balanslaşdırılıb (45–55)"
    return "risklər müsbət makroiqtisadi nəticələrə doğru meyllidir (<45)"


def score_from_fr2(skor: float, medium: float = 6, high: float = 12) -> float:
    """RU FR2 risk score (P×I, 1–25) → CAEM 0–5 scale using RU's own priority thresholds:
    low (1–6) → 2–3 (neutral band), medium (6–12) → 3–4, high (12–25) → 4–5. FR2 measures only
    downside risk, so this component cannot go below 2 (it never signals an upside)."""
    s = float(skor)
    if s <= medium:
        return 2 + (s - 1) / (medium - 1)
    if s <= high:
        return 3 + (s - medium) / (high - medium)
    return min(5.0, 4 + (s - high) / (25 - high))


def _thresholds() -> tuple[float, float]:
    try:
        h = _csv(config.INPUT / "hedler.csv").drop_duplicates("acar").set_index("acar")["deyer"]
        return float(h["score_medium"]), float(h["score_high"])
    except Exception:
        return 6.0, 12.0


def balance_of_risks(sig: pd.DataFrame, S: dict) -> pd.DataFrame:
    rows = []
    for (y, total) in S["bor_total"].items():
        sub = S["bor"][S["bor"].year == y]
        for key, en, az, w, *_ in CATEGORIES:
            r = sub[sub.category == en].iloc[0]
            rows.append({"version": "Nazirlik (əl ilə yazılmış, CAEM)", "year": y, "category": key,
                         "category_az": az, "weight": r.weight, "score": r.score,
                         "weighted": r.score * r.weight, "note_az": "'Balance of risks'!B2:D6"})
        rows.append({"version": "Nazirlik (əl ilə yazılmış, CAEM)", "year": y, "category": "CƏMİ",
                     "category_az": "Ümumi risk indeksi", "weight": 20, "score": None, "weighted": total,
                     "read_off_az": read_off(total), "note_az": "'Balance of risks'!B8:D8 = SUMPRODUCT"})
    try:
        fr2 = _csv(OUT / "FR2_risk_scores.csv").set_index("risk_id")
    except Exception:
        fr2 = pd.DataFrame()
    try:
        ib = _csv(OUT / "FR1_indicator_base.csv").set_index("gosterici")
    except Exception:
        ib = pd.DataFrame()
    med, high = _thresholds()
    prim = sig[sig.primary & (sig.variant == "cari")]
    cur = config.as_of().year
    for y in BOR_YEARS:
        tot = 0.0
        for key, en, az, w, ind, rid, ibid in CATEGORIES:
            comp, notes = {}, []
            p = prim[(prim.indicator == ind) & (prim.year == y)]
            if not p.empty:
                comp["s_signal"] = float(p.iloc[0]["score_0_5"])
                notes.append(f"siqnal: {p.iloc[0]['class_az']} (z={p.iloc[0]['z']:+.2f}; {p.iloc[0]['period']})")
            if ibid and y == cur and ibid in ib.index and np.isfinite(ib.at[ibid, "z"]):
                low_bad = str(ib.at[ibid, "yuksek_pisdir"]).lower() != "true"
                comp["s_indicator"] = score_of(float(ib.at[ibid, "z"]), (0.5, 1.0, 1.5), low_bad)
                notes.append(f"göstərici bazası {ibid}: z={float(ib.at[ibid, 'z']):+.2f} ({ib.at[ibid, 'son_tarix']})")
            if rid and rid in fr2.index and int(fr2.at[rid, "ufuq"]) == y:
                comp["s_fr2"] = score_from_fr2(float(fr2.at[rid, "skor"]), med, high)
                notes.append(f"FR2 {rid}: P={float(fr2.at[rid, 'ehtimal']):.2f}, skor={fr2.at[rid, 'skor']}")
            sc = float(np.mean(list(comp.values()))) if comp else 2.5
            if not comp:
                notes.append("kəmiyyət komponenti yoxdur → neytral 2,5")
            tot += sc * w
            rows.append({"version": "məlumat əsaslı (RU)", "year": y, "category": key, "category_az": az,
                         "weight": w, "score": round(sc, 3), "weighted": round(sc * w, 3),
                         "s_signal": comp.get("s_signal"), "s_indicator": comp.get("s_indicator"),
                         "s_fr2": comp.get("s_fr2"), "fr2_risk": rid, "n_components": len(comp),
                         "note_az": "; ".join(notes)})
        rows.append({"version": "məlumat əsaslı (RU)", "year": y, "category": "CƏMİ",
                     "category_az": "Ümumi risk indeksi", "weight": 20, "weighted": round(tot, 2),
                     "read_off_az": read_off(tot),
                     "note_az": "SUMPRODUCT(bal, çəki); bal = mövcud komponentlərin sadə ortası"})
    cols = ["version", "year", "category", "category_az", "weight", "score", "weighted", "s_signal",
            "s_indicator", "s_fr2", "fr2_risk", "n_components", "read_off_az", "note_az"]
    return pd.DataFrame(rows).reindex(columns=cols)


# ---------------------------------------------------------------- C3: CAEM categories ↔ RU register
LINKS = [  # category key, RU risk, match, note
    ("oil", "R01", "tam", "CAEM neft kateqoriyası = R01 (Brent illik ortası başabaşdan aşağı)"),
    ("oil", "R03", "əlaqəli", "neft çöküşü şərti ilə devalvasiya — CAEM-də ayrıca kateqoriya yoxdur"),
    ("oil", "R14", "əlaqəli", "struktur (uzunmüddətli) neft tələbi — CAEM üfüqündən kənar"),
    ("geo", "R06", "tam", "CAEM-də dəstəkləyici vərəq yoxdur; RU GPR siqnalı əlavə edir"),
    ("tp", "R05", "tam", "CAEM `Risk-gdp tp` = R05 göstəricisi (tərəfdaş real ÜDM artımı)"),
    ("tp", "R07", "əlaqəli", "pul baratları Rusiya ÜDM-i ilə bağlıdır (Nazirlik metodologiyası)"),
    ("imp", "R12", "qismən (nəticə)", "R12 inflyasiya nəticə riskidir; idxal qiyməti amil riski RU-da yoxdur"),
    ("food", "R12", "qismən (nəticə)", "ərzaq qiyməti CPI-yə keçir; amil riski RU-da yoxdur"),
    ("food", "R09", "qismən", "quraqlıq daxili ərzaq təklifinə təsir edir; dünya qiyməti deyil"),
]
NO_CAEM = {"R02": "CAEM `7. Scenario` SC07/SC09/SC11 şokları ilə yalnız ssenari kimi",
           "R04": "CAEM-də bank sektoru bloku yoxdur", "R08": "CAEM-də təbii fəlakət yoxdur",
           "R09": "CAEM-də təbii fəlakət yoxdur", "R10": "CAEM-də təbii fəlakət yoxdur",
           "R11": "CAEM `7. Scenario` SC04/SC05 fiskal şokları (ssenari)",
           "R12": "CAEM `Fancharts` CPI yelpiyi (simmetrik, σ=2 əl ilə)",
           "R13": "CAEM `Fancharts` ÜDM yelpiyi (simmetrik, σ=2 əl ilə)",
           "R15": "CAEM-də sahə səviyyəsi yoxdur", "R16": "CAEM-də rəqabət göstəricisi yoxdur"}
PROPOSALS = {
    "imp": ("R17 (təklif)", "XSI", "Qeyri-neft idxal qiymətlərinin kəskin artımı",
            "idxal qiymətləri artımı > orta + 1σ (CAEM `Risk-import price` mənfi zolağının sərhədi)",
            "import_price_infl (OxLon external_block / assumptions)",
            "tarixi tezlik + MC-də illik bootstrap (FR2 birgə simulyasiyasına əlavə)",
            "idxal qiymətləri → CPI (FR1 infl elastikliyi; OxLon FR9), real gəlir → istehlak",
            "İqtisadiyyat Nazirliyi; Mərkəzi Bank (AMB)", 1.0),
    "food": ("R18 (təklif)", "XSI", "Dünya ərzaq qiymətlərinin şoku",
             "dünya ərzaq indeksi illik artımı > orta + 0,5σ (CAEM `Risk-food price` mənfi zolağı)",
             "IMF/FAO ərzaq qiymətləri indeksi (FRED PFOODINDEXM; CAEM FAO)",
             "tarixi tezlik + MC-də illik bootstrap; R09 quraqlıqla kopula",
             "ərzaq qiymətləri → CPI ərzaq komponenti → R12; aşağı gəlirli ev təsərrüfatları",
             "İqtisadiyyat Nazirliyi; Kənd Təsərrüfatı Nazirliyi; AMB", 0.5),
}


def category_map(sig: pd.DataFrame) -> pd.DataFrame:
    try:
        reg = _csv(config.INPUT / "risk_reyestri.csv").set_index("risk_id")
    except Exception:
        reg = pd.DataFrame(columns=["ad"])
    try:
        fr2 = _csv(OUT / "FR2_risk_scores.csv").set_index("risk_id")
    except Exception:
        fr2 = pd.DataFrame()
    cat = {c[0]: c for c in CATEGORIES}
    sheets = {"oil": "Risk-oil price", "geo": "—", "tp": "Risk-gdp tp", "imp": "Risk-import price",
              "food": "Risk-food price"}
    rows = []

    def base(key):
        _, en, az, w, ind, *_ = cat[key]
        return {"caem_category": en, "caem_category_az": az, "caem_weight": w, "caem_sheet": sheets[key],
                "c1_indicator": ind}

    def ru(rid):
        return {"ru_risk_id": rid, "ru_risk_name": reg["ad"].get(rid, "") if "ad" in reg else "",
                "ru_fr2_skor": fr2["skor"].get(rid) if "skor" in fr2 else None,
                "ru_fr2_ehtimal": fr2["ehtimal"].get(rid) if "ehtimal" in fr2 else None}

    for key, rid, match, note in LINKS:
        rows.append({**base(key), **ru(rid), "match_az": match, "note_az": note})
    hist = sig[sig.primary & (sig.variant == "cari") & (sig.period == "tarix")]
    for key, (rid, fam, name, ev, ind, meth, chan, owner, thr) in PROPOSALS.items():
        h = hist[hist.indicator == cat[key][4]]
        n_ev = int((h["z"] > thr).sum())
        rows.append({**base(key), "ru_risk_id": rid, "ru_risk_name": name, "match_az": "RU-da yoxdur → yeni sətir təklifi",
                     "proposed_family": fam, "proposed_event_az": ev, "proposed_indicator": ind,
                     "proposed_method_az": meth, "proposed_channel_az": chan, "proposed_owner": owner,
                     "hist_events": n_ev, "hist_n": int(len(h)),
                     "hist_frequency": round(n_ev / len(h), 3) if len(h) else None,
                     "note_az": f"ilkin ehtimal = tarixi tezlik {h.year.min()}–{h.year.max()}; Nazirlik təsdiq etməlidir"
                     if len(h) else ""})
    for rid, note in NO_CAEM.items():
        rows.append({"caem_category": "", "caem_category_az": "CAEM-də kateqoriya yoxdur", **ru(rid),
                     "match_az": "yalnız RU", "note_az": note})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- C6: CAEM findings register
ERR = ("#REF!", "#NAME?", "#VALUE!", "#DIV/0!", "#N/A", "#NUM!", "#NULL!")


def error_scan(max_row: int = 1200, max_col: int = 80) -> pd.DataFrame:
    rows = []
    for ws in cm.workbook(True).worksheets:
        mr, mc = min(ws.max_row or 0, max_row), min(ws.max_column or 0, max_col)
        if not mr or not mc:
            continue
        hits = {}
        for r in ws.iter_rows(min_row=1, max_row=mr, max_col=mc):
            for c in r:
                if isinstance(c.value, str) and c.value in ERR:
                    hits.setdefault(c.value, []).append(c.coordinate)
        for e, refs in hits.items():
            rows.append({"sheet": ws.title, "error": e, "n": len(refs), "examples": ", ".join(refs[:6])})
    return pd.DataFrame(rows, columns=["sheet", "error", "n", "examples"])


def _f(x, d=2) -> str:
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


def findings(S: dict | None = None, val: pd.DataFrame | None = None) -> pd.DataFrame:
    S = S or ministry_sheets()
    c, F = cm.cell, []

    def add(sev, sheet, rng, issue, evidence, consequence, rec):
        F.append({"finding_id": f"CF{len(F) + 1:02d}", "severity_az": sev, "sheet": sheet, "cell_range": rng,
                  "issue_az": issue, "evidence": evidence, "consequence_az": consequence,
                  "recommendation_az": rec})

    es = error_scan()
    for sheet, g in es.groupby("sheet", sort=False):
        ev = "; ".join(f"{r.error} × {r.n} ({r.examples})" for r in g.itertuples())
        crit = sheet in ("8b. Summary", "8a. Simulation")
        add("yüksək" if crit else "orta", sheet, g.iloc[0]["examples"].split(",")[0] + " …",
            "Xəta dəyərləri olan xanalar" + (" — 'Alternative' ssenari sətirləri qırılıb" if sheet == "8b. Summary"
                                             else " — 8a başlıq düsturları (makrolar itib)" if sheet == "8a. Simulation" else ""),
            ev, "Həmin xanalardan asılı cədvəl/qrafiklər yanlış və ya boşdur",
            "İstinadları bərpa etmək; xlsb-dən makroları köçürmək və ya düsturları yenidən qurmaq")
    w = [x for x in cm.cells("1d. Real GDP - Expenditure", 384, 384, 16, 20)[0]]
    add("yüksək", "1d. Real GDP - Expenditure", "P384:T384",
        "İstehsal və xərc üsulu ÜDM arasında bağlanmamış fərq (supply-demand wedge)",
        f"2025–2029: {', '.join(_f(v, 0) for v in w)}; cəmi {_f(sum(w), 0)}",
        "Proqnoz identikliyi pozulur; ssenari nəticələri ziddiyyətlidir",
        "Ssenari makrosu ilə fərqi bağlamaq (Sənədləşmə §XI, addım 4) və ya xərc komponentlərini uyğunlaşdırmaq")
    d9 = c("7. Scenario", "D9")
    dif = cm.cells("7. Scenario", 65, 65, 17, 21)[0]
    ca = cm.cells("7. Scenario", 74, 74, 17, 21)[0]
    add("yüksək", "7. Scenario", "D9; Q65:U83",
        "Şoklar sıfır olduğu halda 'Difference' bloku sıfırdan fərqlidir (dondurulmuş baza köhnəlib)",
        f"şokların cəmi D9={d9}; ÜDM fərqi Q65:U65 = {', '.join(_f(v) for v in dif)}; "
        f"cari hesab Q74:U74 = {', '.join(_f(v) for v in ca)}; baza 2024 ÜDM J65={_f(c('7. Scenario', 'J65'))} vs faktiki C65={_f(c('7. Scenario', 'C65'))}",
        "'Difference' bloku risk təsiri kimi istifadə edilə bilməz",
        "Bazanı mavi xanalara dəyər kimi yenidən yapışdırıb dondurmaq; sonra şok tətbiq etmək")
    add("orta", "Fancharts", "Q26:U31 (CPI); Q2:U2",
        "CPI yelpiyi 24-cü sətir əvəzinə 2-ci sətrin üfüqünə istinad edir; üfüq 2-ci ildən sonra artmır",
        f"Q26 düsturu: {c('Fancharts', 'Q26', data_only=False)}; Q2:U2 = {cm.cells('Fancharts', 2, 2, 17, 21)[0]}; "
        f"Q24:U24 = {cm.cells('Fancharts', 24, 24, 17, 21)[0]} (istifadə olunmur)",
        "Qeyri-müəyyənlik 3–5-ci illərdə əhəmiyyətli dərəcədə azaldılır (√2 əvəzinə √5)",
        "Q26:U31-də Q$2 → Q$24; Q2:U2 = 1..5")
    pess = cm.cells("Fancharts", 10, 11, 17, 21)
    above = [2025 + i for i, (p, b) in enumerate(zip(*pess)) if p > b]
    add("orta", "Fancharts", "Q10:U12",
        "Pessimist ssenari bazadan yuxarıdır; pessimist/optimist yolları əl ilə yazılıb",
        f"pessimist > baza illər: {above}; pessimist {', '.join(_f(v) for v in pess[0])} vs baza {', '.join(_f(v) for v in pess[1])}",
        "Yelpik və ssenari mənası ziddiyyətlidir", "Ssenariləri model (7. Scenario) nəticəsindən bağlamaq")
    add("orta", "Fancharts", "I4, I26, H4, H25",
        "Yelpik σ=2 pp əl ilə yazılıb, meyl (tilt) 0 → simmetrik",
        f"I4={c('Fancharts', 'I4')}, I26={c('Fancharts', 'I26')}, H4={c('Fancharts', 'H4')}, H25={c('Fancharts', 'H25')}",
        "Risk balansı (Balance of risks) yelpiyə ötürülmür", "σ-nı tarixi proqnoz xətalarından, meyli risk balansından almaq")
    res = cm.cells("6a. SEI", 40, 40, 14, 18)[0]
    cur = cm.cells("6a. SEI", 37, 37, 14, 18)[0]
    add("yüksək", "6a. SEI", "N40:R40; N37:R37",
        "Ehtiyatlar 2027-dən mənfi, cari hesab 2029-da ÜDM-in −16,6%-i — baza ardıcıl deyil",
        f"ehtiyatlar/ÜDM 2025–29: {', '.join(_f(v) for v in res)}; cari hesab/ÜDM: {', '.join(_f(v) for v in cur)}",
        "CAEM bazası risk təhlili üçün etibarlı deyil (RU bunu baza kimi istifadə etmir)",
        "BOP bloku və neft ixracı fərziyyələrini yoxlamaq; ehtiyat dinamikasını maliyyələşmə ilə bağlamaq")
    rp = S["oil_annual"].loc[2025:2029]
    mp = S["oil_model"].loc[2025:2029]
    add("orta", "Risk-oil price; Oil_and_gas_sector", "M26:M30; AH69:AL69",
        "Risk vərəqindəki Brent yolu modelin öz Brent fərziyyəsindən fərqlidir; 2025–29 sabit yazılıb ('şok açarı' ×0)",
        f"Risk-oil {', '.join(_f(v, 1) for v in rp)} vs model {', '.join(_f(v, 1) for v in mp)}; M26 = {c('Risk-oil price', 'M26', data_only=False)}",
        "Siqnal başqa fərziyyəyə əsaslanır", "M26:M30-u Oil_and_gas_sector!AH69:AL69-a bağlamaq")
    _findings_b(S, add)
    df = pd.DataFrame(F)
    rank = {"yüksək": 0, "orta": 1, "aşağı": 2}
    df["_err"] = df["issue_az"].str.startswith("Xəta dəyərləri")
    df = df.sort_values(["_err", "severity_az"], key=lambda s: s.map(rank) if s.name == "severity_az" else s,
                        kind="stable").drop(columns="_err").reset_index(drop=True)
    df["finding_id"] = [f"CF{i + 1:02d}" for i in range(len(df))]
    return df


def _findings_b(S: dict, add) -> None:
    c = cm.cell
    ox = oxlon_series("gdp_realg", "actual")
    oc = oxlon_series("cpi_infl", "actual")
    add("yüksək", "6a. SEI; MOE_report", "N9, N19",
        "2025 hələ də proqnoz kimidir (köhnəlmiş vintaj)",
        f"ÜDM 2025 = {_f(c('6a. SEI', 'N9'))} vs faktiki {_f(ox.get(2025, np.nan))}; CPI 2025 = {_f(c('6a. SEI', 'N19'))} vs faktiki {_f(oc.get(2025, np.nan))}",
        "Bütün yollar səhv başlanğıcdan çıxır", "INPUT!B9 = 2026; 2025 faktiki məlumatlarını Data vərəqinə yükləmək")
    add("aşağı", "Risk-food price", "C3, O3",
        "Başlıq 'Crude oil, Brent' yazır (neft vərəqindən köçürmə qalığı)",
        f"C3='{c('Risk-food price', 'C3')}', O3='{c('Risk-food price', 'O3')}'", "İstifadəçini çaşdırır",
        "Başlığı 'FAO Food Price Index' etmək")
    fa = S["food_annual"].loc[2004:2024].dropna()
    add("orta", "Risk-food price", "O45:O46",
        "Orta və σ AYLIQ illik artımdan hesablanır, lakin İLLİK artıma tətbiq olunur",
        f"aylıq σ = {_f(S['food_stats'][1])} vs illik artımın σ = {_f(fa.std(ddof=0))} (2004–2024)",
        "Zolaqlar illik dəyərlər üçün çox geniş/dar ola bilər (siqnal həssaslığı dəyişir)",
        "Statistikanı illik artımdan hesablamaq və ya aylıq siqnalı aylıq dəyərlərə tətbiq etmək")
    add("yüksək", "Risk-import price", "D28:D29",
        "Orta və σ seçilmiş illərdən (2010–2016, 2024) + əl ilə əlavələrlə (+0,8+1 pp; σ +1,3) hesablanır",
        f"D28 = {c('Risk-import price', 'D28', data_only=False)} = {_f(S['import_stats'][0])}; D29 = {c('Risk-import price', 'D29', data_only=False)} = {_f(S['import_stats'][1])}",
        "Siqnal mühakiməyə əsaslanır, təkrarlana bilən deyil",
        "Bütün tarixi nümunədən, əlavəsiz hesablamaq; mühakimə varsa ayrıca sətirdə sənədləşdirmək")
    ia = S["import_annual"]
    ext = external_block()["import_price_infl"]
    add("yüksək", "Risk-import price", "C5:D25",
        "İdxal qiymət indeksi 2017–2023-də ildə 17–30% artır (məzənnə 1,70-də sabit ikən) — inandırıcı deyil",
        f"CAEM artımı 2017–2023: {', '.join(_f(ia.get(y, np.nan), 1) for y in range(2017, 2024))}; "
        f"OxLon import_price_infl: {', '.join(_f(ext.get(y, np.nan), 1) for y in range(2017, 2024))}",
        "Seçilmiş-illər qaydası (D28) bu illəri gizlədir; indeks tərifi aydın deyil",
        "Mənbəni və valyuta əsasını yoxlamaq (USD/AZN, səviyyə vs artım)")
    add("orta", "Risk-import price; Risk-gdp tp", "E3:K3 vs F1:K2",
        "Başlıq ±0,5/1/1,5 σ yazır, düsturlar isə ±1/1,5/2 σ kəsiklərini istifadə edir",
        f"F1:K1 = {cm.cells('Risk-import price', 1, 1, 6, 11)[0]}; H3 = '{c('Risk-import price', 'H3')}'",
        "Oxucu neytral zolağı iki dəfə dar zənn edir", "Başlıqları düsturlara uyğunlaşdırmaq (və ya əksinə — qərar Nazirliyindir)")
    add("aşağı", "Risk-oil price", "C3:I3 vs N3:T3",
        "Eyni vərəqdə aylıq blok ±1/1,5/2 σ, illik blok ±0,5/1/1,5 σ istifadə edir",
        f"C3:I3 = '{c('Risk-oil price', 'D3')}' …; N1:T2 = {cm.cells('Risk-oil price', 2, 2, 14, 19)[0]}",
        "Aylıq və illik təsnifat müqayisə edilə bilmir", "Vahid kəsik dəsti seçmək")
    add("aşağı", "Risk-oil price; Risk-food price; Risk-import price", "T31; P43; E26",
        "0–5 şkala etiketlərində yazı xətası ('0<', '>0' → '<0')",
        f"T31='{c('Risk-oil price', 'T31')}', P43='{c('Risk-food price', 'P43')}', E26='{c('Risk-import price', 'E26')}'",
        "Şkala mənası qeyri-müəyyən", "Etiketləri düzəltmək")
    add("aşağı", "Risk-* (bütün zolaq düsturları)", "N:T, P:V, E:K",
        "Ciddi bərabərsizliklər (<, >): dəyər tam kəsikdə olarsa heç bir zolağa düşmür",
        "məs. N5: IF((M5-$M$33)<$N$2*$M$34, …); bərabərlik halı yoxdur", "Nadir halda boş təsnifat",
        "Bir tərəfdə ≤ istifadə etmək (RU daxili zolağa aid edir)")
    rep = reproduce_ministry_bands()
    sig = {(r.indicator, r.year): r.python_band for r in rep.itertuples()}
    fb = {y: S["bor"].query("category == 'Food prices' and year == @y")["score"].iloc[0] for y in (2024, 2025)}
    add("orta", "Balance of risks", "A2:E8",
        "Ballar əl ilə yazılıb, Risk-* vərəqlərinə bağlı deyil; ərzaq balı öz siqnalına uyğun gəlmir; 2026+ sütunu yoxdur",
        f"ərzaq: 2024 bal {fb[2024]} (siqnal zolağı {sig.get(('food_price', 2024))} → şkala 0–1), "
        f"2025 bal {fb[2025]} (zolaq {sig.get(('food_price', 2025))} → 2–3); ehtimal/təsir/sahib sahələri yoxdur",
        "İndeks təkrarlana bilmir və yenilənmir", "Balları C2 qaydası ilə siqnallardan avtomatik hesablamaq (RU C2)")
    add("aşağı", "AZE Model", "A106, A157",
        "Blok etiketləri səhvdir: A2 bloku 'A1', sabit bloku 'A0' adlanır",
        f"A106='{c('AZE Model', 'A106')}', A157='{c('AZE Model', 'A157')}'", "Sənədləşmə çaşdırıcıdır", "Etiketləri A2, Ac etmək")
    add("aşağı", "8a. Simulation; AZE Model", "E62:P106; C159:C206",
        "İmpuls cavablarına struktur sabit Ac əlavə olunur, həll sabiti Bc = inv(A0)·Ac deyil",
        "E62: … +'AZE Model'!$C159; Ac cəmi = 0", "Hazırda təsirsizdir (Ac=0); sabit dəyişərsə cavablar səhv olar",
        "Bc blokunu MMULT(MINVERSE(A0),Ac) kimi əlavə edib ona istinad etmək")
    m = cm.load()
    yb, yf = cm.simulate(m["E_loaded"]), cm.simulate(m["E_loaded"], fix_debt_bug=True)
    ix = m["ix"]
    add("yüksək", "8a. Simulation", "F109:P109",
        "Xarici borc sətri t=2-dən öz gecikməsi (E109) əvəzinə daxili borcun gecikməsini (E108) istifadə edir",
        f"F109 = {c('8a. Simulation', 'F109', data_only=False)}; +1 pp CPI şokunda df_y h=5: {_f(yb[ix['df_y'], 5], 3)} vs düzəldilmiş {_f(yf[ix['df_y'], 5], 3)}",
        "Borc cavabları (d_y, df_y) və borcdan asılı fiskal qayda səhvdir", "F109:P109-da E108 → E109 (nisbi istinad)")
    add("orta", "8a. Simulation", "E108:P109",
        "Daxili borc ilkin balansı (pb_y), xarici borc isə dövlət XƏRCİNİ (g_y) çıxır — işarə/tərif uyğunsuzluğu",
        f"E109 = {c('8a. Simulation', 'E109', data_only=False)}; +1 pp CPI: g_y h1 = {_f(yb[ix['g_y'], 1], 3)} → df_y h1 = {_f(yb[ix['df_y'], 1], 3)}",
        "Xərc artımı xarici borcu AZALDIR", "(1−ψ)·g_y → (1−ψ)·pb_y")
    E = np.zeros((cm.N_STATE, cm.H + 1)); E[ix["pb_y"], 1] = 1
    y1 = cm.simulate(E)
    E = np.zeros((cm.N_STATE, cm.H + 1)); E[ix["gcap_y"], 1] = 1
    y2 = cm.simulate(E)
    add("orta", "8a. Simulation", "A34:P34; A37:P37",
        "'Government current spending shock' pb_y (ilkin balans) tənliyinə daxil olur; kapital xərci şoku g_y/pb_y-yə düşmür",
        f"pb_y +1 → g_y h1 = {_f(y1[ix['g_y'], 1], 3)}, ÜDM h1 = {_f(y1[ix['dy'], 1], 3)}; gcap_y +1 → g_y h1 = {_f(y2[ix['g_y'], 1], 3)}, pb_y = {_f(y2[ix['pb_y'], 1], 3)}",
        "İstifadəçi '+xərc' daxil etdikdə əks (konsolidasiya) şoku alır", "Etiketi 'İlkin balans şoku' etmək; gcap_y-ni g_y identikliyinə daxil etmək")
    add("orta", "CAEM.xlsx (bütün iş kitabı)", "xl/vbaProject.bin",
        "xlsx nüsxəsində makrolar yoxdur (xlsb-də var); üfüq 2025–2029 (2030 yoxdur)",
        f"xlsx MD5 {cm.CAEM_MD5}; INPUT!B9 = {c('INPUT', 'B9')}",
        "Ssenari iş axını (fərqin bağlanması) xlsx-də işləmir; büdcə dövrü 2030-u əhatə etmir",
        "Makroları xlsb-dən bərpa etmək; üfüqü 2030-a uzatmaq")


# ---------------------------------------------------------------- catalog, run, CLI
CATALOG = OUT / "_catalog_v2.csv"
CAT_COLS = ["file", "owner_module", "description_az", "columns", "update_frequency"]
FILES = {
    "C1_caem_signals.csv": "CAEM risk vərəqlərinin σ-zolaq siqnalları (neft, ərzaq, idxal qiyməti, tərəfdaş ÜDM, + GPR) cari məlumatla; OxLon/MikroUnit bazası və CAEM yolu; Nazirlik təsnifatının təkrarı",
    "C1_band_reproduction.csv": "Nazirlik σ-zolaq təsnifatının Python təkrarı ilə vərəqin öz zolaq sütunlarının müqayisəsi",
    "C2_balance_of_risks.csv": "Risk balansı indeksi (0–100): Nazirliyin əl ilə yazdığı ballar (2022/2024/2025) və RU-nun məlumat əsaslı balları (2022–2030)",
    "C3_category_map.csv": "CAEM risk kateqoriyaları ↔ RU risk reyestri (R01–R16) uyğunluğu və yeni reyestr sətri təklifləri (R17, R18)",
    "C4_caem_shock_library.csv": "Nazirlik CAEM modeli — müqayisə: AZE Model impuls cavabları (8a: 26 struktur şok; 7. Scenario: 14 şok)",
    "C4_caem_shock_index.csv": "C4 şok kitabxanasının indeksi: 40 şokun adı, vahidi, giriş xanaları və 7. Scenario → AZE Model xəritələnməsi",
    "C4_caem_variables.csv": "AZE Model 48 vəziyyət dəyişəninin adı və vahidi (C4 üçün lüğət)",
    "C4_caem_irf_validation.csv": "AZE Model diapazonlarının və yüklənmiş 8a təcrübəsinin (+1 pp CPI) təkrarının yoxlaması",
    "C5_transmission_comparison.csv": "Müqayisəli şoklar üzrə ötürmə: CAEM AZE Model (müqayisə) vs MikroUnit FR1 vs OxLon (FR12, FR13)",
    "C5_fr1_oscillation.csv": "MikroUnit FR1 addım cavablarında işarə salınımı yoxlaması (balance_n, rgdpnon, infl)",
    "C6_caem_findings.csv": "CAEM iş kitabında aşkar edilən qüsurlar reyestri (vərəq, xana, sübut, nəticə, tövsiyə) — Nazirlik üçün",
}


def update_catalog(frames: dict) -> None:
    cat = _csv(CATALOG) if CATALOG.exists() else pd.DataFrame(columns=CAT_COLS)
    cat = cat[~cat["file"].isin(FILES)]
    new = [{"file": f, "owner_module": "riskunit.caem", "description_az": d,
            "columns": "; ".join(map(str, frames[f].columns)) if f in frames else "",
            "update_frequency": "CAEM yeni vintajında və gündəlik yeniləmədə (siqnallar lent ilə)"}
           for f, d in FILES.items()]
    cols = list(cat.columns) + [c for c in CAT_COLS if c not in cat.columns]   # keep others' columns
    if "updated_utc" in cols:
        stamp = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
        for r in new:
            r["updated_utc"] = stamp
    pd.concat([cat, pd.DataFrame(new)], ignore_index=True).reindex(columns=cols).to_csv(CATALOG, index=False)


def run(ctx: dict | None = None) -> dict:
    """Stage C (CAEM). ctx: fetch (bool, food index download), run_fr13 (bool, default True),
    write (bool, default True). Returns {file name: DataFrame, 'meta': dict}."""
    ctx = ctx or {}
    meta = {"label": cm.LABEL_AZ, "as_of": config.as_of().isoformat(), "vintage": cm.vintage_status()}
    if ctx.get("fetch"):
        meta["food_feed"] = fetch_food()
    S = ministry_sheets()
    sig = signals(S)
    rep = reproduce_ministry_bands()
    val = cm.validate()
    comp, osc = cm.transmission_comparison(run_fr13=ctx.get("run_fr13", True))
    lib, lib_ix, lib_var = cm.shock_library()
    frames = {
        "C1_caem_signals.csv": sig,
        "C1_band_reproduction.csv": rep,
        "C2_balance_of_risks.csv": balance_of_risks(sig, S),
        "C3_category_map.csv": category_map(sig),
        "C4_caem_shock_library.csv": lib,
        "C4_caem_shock_index.csv": lib_ix,
        "C4_caem_variables.csv": lib_var,
        "C4_caem_irf_validation.csv": val,
        "C5_transmission_comparison.csv": comp,
        "C5_fr1_oscillation.csv": osc,
        "C6_caem_findings.csv": findings(S),
    }
    meta["fr1_oscillating"] = osc[osc.oscillates][["shock", "column"]].to_dict("records")
    meta["irf_validation_ok"] = bool((val["netice"] == "keçdi").all())
    meta["band_reproduction_ok"] = bool(rep["match"].all())
    if ctx.get("write", True):
        for f, df in frames.items():
            df.to_csv(OUT / f, index=False)
        update_catalog(frames)
    return {**frames, "meta": meta}


def headline(res: dict) -> str:
    sig = res["C1_caem_signals.csv"]
    p = sig[sig.primary & (sig.variant == "cari") & sig.year.between(2026, 2030)]
    t = p.pivot_table(index="indicator", columns="year", values="class_az", aggfunc="first")
    b = res["C2_balance_of_risks.csv"]
    b = b[b.category == "CƏMİ"][["version", "year", "weighted"]]
    v = res["C4_caem_irf_validation.csv"]
    return "\n".join([cm.LABEL_AZ, "", "C1 siqnallar 2026–2030:", t.to_string(), "",
                      "C2 risk balansı:", b.to_string(index=False), "",
                      f"C4 yoxlama: {(v.netice == 'keçdi').sum()}/{len(v)} keçdi",
                      f"C6 qüsurlar: {len(res['C6_caem_findings.csv'])}",
                      f"FR1 salınım: {res['meta']['fr1_oscillating'] or 'yoxdur'}"])


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    res = run({"fetch": "--fetch" in argv, "run_fr13": "--no-fr13" not in argv})
    print(headline(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
