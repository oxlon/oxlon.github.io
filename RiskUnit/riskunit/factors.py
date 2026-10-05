"""FR1 — risk factor analysis: indicator base, transmission channels, hazard frequencies,
event chronology.

Standards (as the §15.5.2 micro unit): no lagged dependent variable, no AR/GARCH model of a
factor; small-sample HAC (Newey-West, t(n-k) inference). A channel whose estimate is
statistically weak is not silently set to zero: its parameter uncertainty is carried into the
joint simulation (draws from N(b, se²)) and the channel table flags it.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from . import config, feeds, spine

REGIONAL_GPR = ["gpr_rus", "gpr_ukr", "gpr_isr", "gpr_tur"]


# ---------------------------------------------------------------- inputs
@lru_cache(maxsize=1)
def params() -> dict[str, float]:
    h = pd.read_csv(config.INPUT / "hedler.csv")
    return dict(zip(h["acar"], h["deyer"].astype(float)))


def register() -> pd.DataFrame:
    r = pd.read_csv(config.INPUT / "risk_reyestri.csv", dtype={"aktiv": int})
    return r[r["aktiv"] == 1].reset_index(drop=True)


FAMILY_AZ = {"MAL": "Maliyyə və əmtəə bazarları", "XSI": "Xarici-siyasi və xarici iqtisadi",
             "TEB": "Təbii fəlakətlər", "DAX": "Daxili makroiqtisadi və struktur",
             "SEK": "Sektor (mikro) riskləri"}


# ---------------------------------------------------------------- estimation helper
def ols_hac(y: pd.Series, X: pd.DataFrame, lags: int | None = None) -> dict:
    d = pd.concat([y, X], axis=1).dropna()
    n = len(d)
    lags = lags if lags is not None else max(1, int(np.floor(4 * (n / 100) ** (2 / 9))))
    r = sm.OLS(d.iloc[:, 0], sm.add_constant(d.iloc[:, 1:])).fit(
        cov_type="HAC", cov_kwds={"maxlags": lags, "use_correction": True}, use_t=True)
    return {"params": r.params, "se": r.bse, "p": r.pvalues, "cov": r.cov_params(), "n": n,
            "r2": r.rsquared, "sample": f"{d.index.min()}–{d.index.max()}", "resid_sd": float(np.sqrt(r.scale))}


def regional_gpr_monthly() -> pd.Series:
    """Regional composite: mean of the Russia, Ukraine, Israel and Türkiye country indices
    (each is a share of newspaper articles, so they share units)."""
    return pd.concat([feeds.monthly("gpr", s) for s in REGIONAL_GPR], axis=1).dropna().mean(axis=1)


# ---------------------------------------------------------------- transmission channels
@lru_cache(maxsize=1)
def channels() -> dict:
    """Estimate every reduced-form channel used by the simulation. Returns a dict of
    channel → {coef, se, ...} and writes output/FR1_transmission_channels.csv."""
    P = spine.annual_panel().copy()
    gm = regional_gpr_monthly()
    P["gpr_reg"] = gm.groupby(gm.index.year).mean().reindex(P.index)
    P["dl_gpr_reg"] = np.log(P["gpr_reg"]).diff() * 100
    P["remit_gw"] = P["remit_g"].clip(-60, 60)
    mi = spine.micro_fr1_dataset()
    P["inv_state_g"] = mi["rinv_state"].pct_change(fill_method=None).reindex(P.index) * 100
    P["dln_brent_l1"] = P["dln_brent"].shift(1)
    rows, ch = [], {}

    def add(key, label_az, y, xs, use_for):
        est = ols_hac(P[y], P[xs])
        for x in xs:
            ch[(key, x)] = {"coef": float(est["params"][x]), "se": float(est["se"][x])}
            rows.append({"kanal": key, "izah": label_az, "asili": y, "izahedici": x,
                         "emsal": est["params"][x], "st_xeta": est["se"][x], "p": est["p"][x],
                         "n": est["n"], "R2": est["r2"], "nümunə": est["sample"], "tezlik": "illik",
                         "istifade": use_for,
                         "sübut": "güclü (p<0,05)" if est["p"][x] < 0.05 else
                                  ("orta (p<0,10)" if est["p"][x] < 0.10 else
                                   "zəif — parametr qeyri-müəyyənliyi simulyasiyaya daxildir")})
        ch[(key, "resid_sd")] = est["resid_sd"]
        return est

    add("remit", "Pul baratlarının artımı ← Brent (tərəfdaş artımı əmsalı yanlış işarəli və əhəmiyyətsiz olduğu üçün çıxarılıb)",
        "remit_gw", ["dln_brent"], "R07 barat kanalı: Brent hissəsi R01-ə aid edilir")
    add("inv_brent", "Dövlət investisiyasının real artımı ← Brent (cari və 1 il gecikmə; tarixi prosiklik reaksiya)",
        "inv_state_g", ["dln_brent", "dln_brent_l1"], "R01 prosiklik fiskal reaksiya kanalı (FR3 T09 ilə idarə olunur)")
    add("agri_spi", "Kənd təsərrüfatı əlavə dəyəri ← SPI (quraqlıq indeksi)", "agri_g", ["spi"],
        "R09 quraqlıq kanalı")
    P["d_lend"] = P["lendrate"].diff()
    P["d_us"] = P["us_rate"].diff()
    add("lend_us", "Daxili kredit faizi dəyişməsi ← ABŞ faiz dəyişməsi", "d_lend", ["d_us"],
        "R02 faiz kanalı")
    add("partner_gpr", "Tərəfdaş artımı ← regional GPR dəyişməsi", "partner_g", ["dl_gpr_reg"],
        "R06 tərəfdaş kanalı")
    add("remit_gpr", "Pul baratlarının artımı ← regional GPR dəyişməsi", "remit_gw", ["dl_gpr_reg"],
        "R06 barat kanalı")
    add("nonoil_rf", "Qeyri-neft artımı ← Brent, tərəfdaş artımı (reduksiya forması; yalnız yoxlama)",
        "nonoil_g", ["dln_brent", "partner_g"], "NFR1 çarpaz yoxlama — simulyasiyada istifadə olunmur")

    # monthly local projections: regional GPR jump -> Brent (log points), h = 0..11
    b = np.log(feeds.monthly("brent"))
    d = pd.DataFrame({"lb": b, "lg": np.log(gm)}).dropna()
    d["dg"] = d["lg"].diff()
    betas, ses = [], []
    for h in range(12):
        y = (d["lb"].shift(-h) - d["lb"].shift(1)).rename("y")
        est = ols_hac(y, d[["dg"]], lags=h + 1)
        betas.append(float(est["params"]["dg"]))
        ses.append(float(est["se"]["dg"]))
        if h in (0, 3, 11):
            rows.append({"kanal": "gpr_brent_lp", "izah": f"Brent (log, h={h} ay) ← regional GPR sıçrayışı",
                         "asili": f"ln Brent(t+{h}) − ln Brent(t−1)", "izahedici": "Δ ln GPR_reg",
                         "emsal": est["params"]["dg"], "st_xeta": est["se"]["dg"], "p": est["p"]["dg"],
                         "n": est["n"], "R2": est["r2"], "nümunə": est["sample"], "tezlik": "aylıq",
                         "istifade": "R06 neft qiyməti kanalı (illik orta təsir = h=0..11 ortası)",
                         "sübut": "güclü (p<0,05)" if est["p"]["dg"] < 0.05 else
                                  ("orta (p<0,10)" if est["p"]["dg"] < 0.10 else "zəif")})
    # effect of a one-log-point jump on the annual-average Brent level (in log points)
    ch[("gpr_brent", "annual_avg")] = {"coef": float(np.mean(betas)),
                                       "se": float(np.sqrt(np.mean(np.square(ses))))}
    ch[("gpr_brent", "lp")] = betas

    # Brent central path: inverse-MSE combination of the macro structural path and no-change
    bt = spine._csv(config.MACRO_FILES["validation_backtest"])
    bb = bt[(bt.series_code == "brent_usd") & (bt.horizon_h == 1) & (bt.model != "DINAMIKLIK")]
    rmse = bb.groupby("model")["error"].apply(lambda e: float(np.sqrt(np.mean(np.square(e)))))
    rw_name = [m for m in rmse.index if m.upper() in ("RW", "TƏSADÜFİ_GƏZİŞMƏ", "RANDOM_WALK")]
    rw = float(rmse[rw_name[0]]) if rw_name else float(bb["rw_rmse_h"].iloc[0])
    struct = float(rmse.drop(rw_name, errors="ignore").min())
    w = (1 / struct ** 2) / (1 / struct ** 2 + 1 / rw ** 2)
    ch[("brent_combo", "w_struct")] = w
    rows.append({"kanal": "brent_combo", "izah": "Brent mərkəzi yolu: makro struktur yolu ⊕ dəyişməz (RW) yol, tərs-MSE çəkiləri",
                 "asili": "ln Brent", "izahedici": "struktur çəkisi", "emsal": w, "st_xeta": np.nan,
                 "p": np.nan, "n": len(bb), "R2": np.nan, "nümunə": "makro validation_backtest h=1",
                 "tezlik": "illik", "istifade": "R01 canlı mərkəzi yol",
                 "sübut": f"RMSE struktur {struct:.3f} / RW {rw:.3f} (log)"})

    tab = pd.DataFrame(rows)
    tab.to_csv(config.OUTPUT / "FR1_transmission_channels.csv", index=False, float_format="%.6g")
    ch["_panel"] = P
    return ch


# ---------------------------------------------------------------- hazards
def earthquake_episodes() -> pd.DataFrame:
    """Decluster the USGS catalogue: events within 30 days of each other form one episode."""
    q = feeds.latest("usgs")
    q["date"] = pd.to_datetime(q["date"])
    q = q.sort_values("date")
    ep, cur = [], None
    for r in q.itertuples():
        if cur is None or (r.date - cur["end"]).days > 30:
            if cur:
                ep.append(cur)
            cur = {"start": r.date, "end": r.date, "mag": r.value, "place": r.place}
        else:
            cur["end"] = r.date
            if r.value > cur["mag"]:
                cur["mag"], cur["place"] = r.value, r.place
    if cur:
        ep.append(cur)
    return pd.DataFrame(ep)


@lru_cache(maxsize=1)
def hazards() -> dict:
    p = params()
    ep = earthquake_episodes()
    years = (pd.Timestamp(config.as_of()) - pd.Timestamp("1950-01-01")).days / 365.25
    t1 = ep[(ep.mag >= p["eq_mag_tier1"]) & (ep.mag < p["eq_mag_tier2"])]
    t2 = ep[ep.mag >= p["eq_mag_tier2"]]
    spi = spine._spi(spine.precip_monthly())
    spi_hist = spi.loc[:config.as_of().year - (0 if config.as_of().month >= 10 else 1)]
    # running 12-month SPI for the current state (last 12 complete months)
    pm = spine.precip_monthly().mean(axis=1)
    last12 = pm.iloc[-12:].sum()
    ann = pm.rolling(12).sum().dropna()
    ref = ann[(ann.index.year >= 1961) & (ann.index.year <= 2020) & (ann.index.month == pm.index[-1].month)]
    a, loc, sc = stats.gamma.fit(ref, floc=0)
    spi_now = float(stats.norm.ppf(np.clip(stats.gamma.cdf(last12, a, loc, sc), 1e-4, 1 - 1e-4)))
    return {
        "eq_years": years, "eq_n_tier1": len(t1), "eq_n_tier2": len(t2),
        "eq_lambda_tier1": len(t1) / years, "eq_lambda_tier2": len(t2) / years,
        "eq_episodes": ep,
        "spi_hist": spi_hist, "spi_now": spi_now, "spi_now_end": pm.index[-1].strftime("%Y-%m"),
        "p_drought": float((spi_hist <= p["spi_threshold"]).mean()),
    }


# ---------------------------------------------------------------- devaluation analogue
@lru_cache(maxsize=1)
def devaluation() -> dict:
    """Conditional devaluation frequency and the 2015-2016 analogue impact net of the oil
    and public-investment channels (both from the FR1 structural multipliers)."""
    p = params()
    P = spine.annual_panel()
    br = P["brent"]
    drop = (br / br.shift(1).rolling(3).mean() - 1) * 100
    fx = P["usd_azn"].pct_change(fill_method=None) * 100
    trig = drop[drop <= p["devaluation_brent_drop"]].dropna()
    dev_years = [int(y) for y in trig.index if fx.get(y, 0) > 10]
    p_dev = len(dev_years) / max(len(trig), 1)
    # analogue 2016 vs 2010-2014 average, nonoil growth
    mi = spine.micro_fr1_dataset()
    M = spine.multipliers()
    pre = P.loc[2010:2014, "nonoil_g"].mean()
    actual_dev = P.loc[[2015, 2016], "nonoil_g"].mean() - pre
    d_brent = P.loc[[2015, 2016], "brent"].mean() - P.loc[2010:2014, "brent"].mean()
    oil_ch = d_brent / 10 * float(M["brent10"]["rgdpnon"].iloc[0])           # % level, 1st-year response
    d_inv = (mi.loc[[2015, 2016], "rinv_state"].mean() - mi.loc[2010:2014, "rinv_state"].mean()) / 1000
    inv_ch = d_inv * float(M["stateinv1bn"]["rgdpnon"].iloc[0])
    resid = actual_dev - oil_ch - inv_ch
    # CPI pass-through: 2016-2017 inflation over 2012-2014 average per log-unit depreciation
    dln_fx = np.log(P.loc[2017, "usd_azn"] / P.loc[2014, "usd_azn"])
    pt = (P.loc[[2016, 2017], "cpi"].mean() - P.loc[2012:2014, "cpi"].mean()) / dln_fx
    return {"trigger_years": [int(y) for y in trig.index], "dev_years": dev_years, "p_dev": p_dev,
            "nonoil_actual_dev": actual_dev, "nonoil_oil_channel": oil_ch, "nonoil_inv_channel": inv_ch,
            "nonoil_residual": resid, "cpi_passthrough": pt, "dln_fx_2014_2017": dln_fx,
            "drop_series": drop}


# ---------------------------------------------------------------- indicator base
INDICATORS = [
    # code, family, name, unit, freq, source, higher_is_worse
    ("brent", "MAL", "Brent neft qiyməti", "USD/barel", "gündəlik", "FRED DCOILBRENTEU", False),
    ("vix", "MAL", "VIX — qlobal risk iştahı indeksi", "indeks", "gündəlik", "FRED VIXCLS", True),
    ("ust10", "MAL", "ABŞ 10 illik istiqraz gəlirliyi", "%", "gündəlik", "FRED DGS10", True),
    ("fedfunds", "MAL", "ABŞ federal fondlar faizi", "%", "aylıq", "FRED FEDFUNDS", True),
    ("eurusd", "MAL", "EUR/USD məzənnəsi", "USD/EUR", "gündəlik", "FRED DEXUSEU", False),
    ("gpr_global", "XSI", "Geosiyasi risk indeksi (qlobal)", "indeks", "aylıq", "Caldara–Iacoviello GPR", True),
    ("gpr_reg", "XSI", "Regional geosiyasi risk (Rusiya, Ukrayna, İsrail, Türkiyə ortası)", "indeks", "aylıq", "Caldara–Iacoviello GPR", True),
    ("gpr_rus", "XSI", "Geosiyasi risk — Rusiya", "indeks", "aylıq", "Caldara–Iacoviello GPR", True),
    ("gpr_tur", "XSI", "Geosiyasi risk — Türkiyə", "indeks", "aylıq", "Caldara–Iacoviello GPR", True),
    ("epu", "XSI", "Qlobal iqtisadi siyasət qeyri-müəyyənliyi", "indeks", "aylıq", "Baker–Bloom–Davis GEPU", True),
    ("eq_12m", "TEB", "Son 12 ayda ən güclü zəlzələ (ölkə və yaxınlığı)", "M", "hadisə", "USGS ComCat", True),
    ("spi_12m", "TEB", "Quraqlıq indeksi SPI-12 (kənd təsərrüfatı bölgələri)", "SPI", "aylıq", "ERA5 (Open-Meteo)", False),
    ("cpi", "DAX", "İnflyasiya (illik orta)", "%", "illik", "makro §15.5.1", True),
    ("lendrate", "DAX", "Kredit faizi (orta)", "%", "illik", "mikro FR1", True),
    ("credit_g", "DAX", "Real kredit artımı", "%", "illik", "mikro FR1", False),
    ("remit_g", "XSI", "Pul baratlarının artımı", "%", "illik", "makro (MoE BOP, AMB)", False),
    ("debt_pct", "DAX", "Dövlət borcu / ÜDM", "%", "illik", "mikro FR1", True),
    ("fr10_watch", "SEK", "FR10 izləmə siyahısındakı emal sahələri", "say", "illik", "mikro FR10", True),
    ("fr12_score", "SEK", "FR12 rəqabət EWS — ən yüksək bal", "bal", "illik", "mikro FR12", True),
]


def _hist_and_last(code: str):
    P = spine.annual_panel()
    if code in ("brent", "vix", "ust10", "fedfunds", "eurusd", "epu"):
        feed = {"brent": "brent"}.get(code, code)
        m = feeds.monthly(feed)
        raw = feeds.latest(feed)
        return m, float(raw["value"].iloc[-1]), str(raw["date"].iloc[-1])
    if code.startswith("gpr_") and code != "gpr_reg":
        m = feeds.monthly("gpr", code)
        return m, float(m.iloc[-1]), m.index[-1].strftime("%Y-%m")
    if code == "gpr_reg":
        m = regional_gpr_monthly()
        return m, float(m.iloc[-1]), m.index[-1].strftime("%Y-%m")
    if code == "eq_12m":
        q = feeds.latest("usgs")
        q["date"] = pd.to_datetime(q["date"])
        s = q.set_index("date")["value"].resample("YS").max().dropna()
        last = q[q["date"] > pd.Timestamp(config.as_of()) - pd.Timedelta(days=365)]
        v = float(last["value"].max()) if len(last) else np.nan
        return s, v, last["date"].max().strftime("%Y-%m-%d") if len(last) else ""
    if code == "spi_12m":
        h = hazards()
        return h["spi_hist"], h["spi_now"], h["spi_now_end"]
    if code == "fr10_watch":
        e = spine._csv(config.MICRO_FILES["fr10_ews"])
        return pd.Series(dtype=float), float(e["watch_list"].sum()), "2025"
    if code == "fr12_score":
        e = spine._csv(config.MICRO_FILES["fr12_ews"])
        return pd.Series(dtype=float), float(e["score"].max()), "2025"
    s = P[code].dropna()
    return s, float(s.iloc[-1]), str(int(s.index[-1]))


def indicator_base() -> pd.DataFrame:
    rows = []
    for code, fam, name, unit, freq, src, worse_high in INDICATORS:
        hist, last, when = _hist_and_last(code)
        if len(hist) >= 10:
            pct = float((hist < last).mean() * 100)
            z = float((last - hist.mean()) / hist.std())
            tail = pct if worse_high else 100 - pct
            status = "xəbərdarlıq" if tail >= 90 else ("izləmə" if tail >= 75 else "normal")
            first = str(hist.index[0])[:10]
        else:
            pct, z, first = np.nan, np.nan, ""
            status = "xəbərdarlıq" if (code == "fr10_watch" and last > 0) else (
                "izləmə" if (code == "fr12_score" and last >= 0.25) else "normal")
        rows.append({"gosterici": code, "aile": fam, "ad": name, "vahid": unit, "tezlik": freq,
                     "menbe": src, "ilk_musahide": first, "son_tarix": when, "son_deyer": last,
                     "tarixi_faiz": pct, "z": z, "yuksek_pisdir": worse_high, "status": status})
    out = pd.DataFrame(rows)
    out.to_csv(config.OUTPUT / "FR1_indicator_base.csv", index=False, float_format="%.6g")
    return out


# ---------------------------------------------------------------- event chronology
def event_chronology() -> pd.DataFrame:
    ev = pd.read_csv(config.INPUT / "hadise_xronologiyasi.csv")
    gm = regional_gpr_monthly()
    gg = feeds.monthly("gpr", "gpr_global")
    br = feeds.monthly("brent")
    vix = feeds.monthly("vix")
    q = feeds.latest("usgs")
    q["date"] = pd.to_datetime(q["date"])
    fx = spine.annual_panel()["usd_azn"]
    rows = []
    for r in ev.itertuples():
        t = pd.Timestamp(r.tarix).to_period("M").to_timestamp()
        def ratio(s):
            if t not in s.index:
                return np.nan
            base = s.loc[t - pd.DateOffset(months=12): t - pd.DateOffset(months=1)].mean()
            return float(s.loc[t] / base) if base else np.nan
        def chg(s, k):
            if t not in s.index:
                return np.nan
            t2 = t + pd.DateOffset(months=k)
            prev = s.loc[:t - pd.DateOffset(months=1)]
            if t2 not in s.index or prev.empty:
                return np.nan
            return float(np.log(s.loc[t2] / prev.iloc[-1]) * 100)
        near = q[(q["date"] - pd.Timestamp(r.tarix)).abs() <= pd.Timedelta(days=3)]
        y = pd.Timestamp(r.tarix).year
        rows.append({"tarix": r.tarix, "aile": r.aile, "hadise": r.hadise, "risk_idler": r.risk_idler,
                     "gpr_qlobal_nisbet": ratio(gg), "gpr_regional_nisbet": ratio(gm),
                     "brent_3ay_log_deyisme": chg(br, 3), "brent_12ay_log_deyisme": chg(br, 12),
                     "vix_nisbet": ratio(vix),
                     "zelzele_M": float(near["value"].max()) if (len(near) and r.aile == "TEB") else np.nan,
                     "usd_azn_il_deyisme_pct": float((fx.get(y, np.nan) / fx.get(y - 1, np.nan) - 1) * 100),
                     "menbe_qeydi": r.menbe_qeydi})
    out = pd.DataFrame(rows)
    out.to_csv(config.OUTPUT / "FR1_event_chronology.csv", index=False, float_format="%.4g")
    return out


def clear_caches():
    for f in (params, channels, hazards, devaluation):
        f.cache_clear()
