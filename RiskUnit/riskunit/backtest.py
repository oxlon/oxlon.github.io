"""NFR1 — periodic backtesting of the risk models.

TT §15.5.3 NFR1 asks for three things, each implemented here:
  (1) accuracy against a simple benchmark;
  (2) using only data available at the forecast origin (no later revisions);
  (3) separate statistical tests of the probability distribution, because the risk module's
      output is a distribution, not a number.

Data basis is stated on every row. Market series (Brent, VIX, GPR, USGS, ERA5) are not revised,
so expanding-window tests on them are real-time by construction. National-accounts targets are
revised; until the vintage archive (data/vintages, output/forecast_archive) has matured, those
tests are pseudo-real-time and say so. `evaluate_archive()` scores the archived real-time risk
forecasts as soon as their target year has a first-release outcome.

Distribution tests: PIT uniformity (Kolmogorov-Smirnov), Berkowitz LR (normality of the
inverse-normal PIT, mean 0 / variance 1 / no autocorrelation), Kupiec unconditional coverage and
Christoffersen independence / conditional coverage for lower-tail breaches, interval coverage
against the 75-85 % (80 %) and 86-94 % (90 %) tolerance bands, CRPS and pinball loss against a
benchmark distribution, AUROC and noise-to-signal ratio for the early-warning signals.
"""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from . import config, factors, feeds, simulate, spine


# ---------------------------------------------------------------- statistical tests
def kupiec(breaches: np.ndarray, p: float) -> tuple[float, float]:
    """Unconditional coverage LR test (Kupiec 1995). Returns (LR, p-value)."""
    b = np.asarray(breaches, dtype=bool)
    n, x = len(b), int(b.sum())
    if n == 0:
        return np.nan, np.nan
    pi = x / n
    ll0 = (n - x) * np.log(1 - p) + x * np.log(p)
    ll1 = ((n - x) * np.log(1 - pi) if pi < 1 else 0) + (x * np.log(pi) if pi > 0 else 0)
    lr = -2 * (ll0 - ll1)
    return float(lr), float(1 - stats.chi2.cdf(lr, 1))


def christoffersen(breaches: np.ndarray, p: float) -> dict:
    """Independence and conditional-coverage LR tests (Christoffersen 1998)."""
    b = np.asarray(breaches, dtype=int)
    if len(b) < 3:
        return {"LR_ind": np.nan, "p_ind": np.nan, "LR_cc": np.nan, "p_cc": np.nan}
    a, c = b[:-1], b[1:]
    n00 = int(((a == 0) & (c == 0)).sum()); n01 = int(((a == 0) & (c == 1)).sum())
    n10 = int(((a == 1) & (c == 0)).sum()); n11 = int(((a == 1) & (c == 1)).sum())
    pi01 = n01 / max(n00 + n01, 1); pi11 = n11 / max(n10 + n11, 1)
    pi = (n01 + n11) / max(n00 + n01 + n10 + n11, 1)
    def ll(p_, k0, k1):
        return (k0 * np.log(1 - p_) if p_ < 1 else 0) + (k1 * np.log(p_) if p_ > 0 else 0)
    lr_ind = -2 * (ll(pi, n00 + n10, n01 + n11) - ll(pi01, n00, n01) - ll(pi11, n10, n11))
    lr_uc, _ = kupiec(b.astype(bool), p)
    lr_cc = lr_uc + lr_ind
    return {"LR_ind": float(lr_ind), "p_ind": float(1 - stats.chi2.cdf(lr_ind, 1)),
            "LR_cc": float(lr_cc), "p_cc": float(1 - stats.chi2.cdf(lr_cc, 2))}


def berkowitz(pit: np.ndarray) -> tuple[float, float]:
    """Berkowitz (2001) LR test: z = Φ⁻¹(PIT) ~ iid N(0,1) against AR(1) with free mean/variance.
    (An AR(1) here is the test's alternative hypothesis, not a forecasting model.)"""
    z = stats.norm.ppf(np.clip(np.asarray(pit), 1e-6, 1 - 1e-6))
    if len(z) < 5:
        return np.nan, np.nan
    y, x = z[1:], z[:-1]
    X = sm.add_constant(x)
    r = sm.OLS(y, X).fit()
    s2 = r.ssr / len(y)
    ll1 = -0.5 * len(y) * (np.log(2 * np.pi * s2) + 1)
    ll0 = -0.5 * np.sum(np.log(2 * np.pi) + y ** 2)
    lr = -2 * (ll0 - ll1)
    return float(lr), float(1 - stats.chi2.cdf(lr, 3))


def ks_uniform(pit: np.ndarray) -> tuple[float, float]:
    if len(pit) < 3:
        return np.nan, np.nan
    r = stats.kstest(pit, "uniform")
    return float(r.statistic), float(r.pvalue)


def crps_sample(draws: np.ndarray, y: float) -> float:
    d = np.asarray(draws)
    return float(np.mean(np.abs(d - y)) - 0.5 * np.mean(np.abs(d[:, None] - d[None, :]))) if len(d) <= 600 \
        else float(np.mean(np.abs(d - y)) - 0.5 * np.mean(np.abs(np.sort(d)[None, :] - np.sort(d)[:, None])[::4, ::4]))


def crps_normal(mu, sig, y):
    z = (y - mu) / sig
    return float(sig * (z * (2 * stats.norm.cdf(z) - 1) + 2 * stats.norm.pdf(z) - 1 / np.sqrt(np.pi)))


def pinball(y, q, tau):
    return float(np.mean(np.maximum(tau * (y - q), (tau - 1) * (y - q))))


def auroc(score: np.ndarray, event: np.ndarray) -> float:
    s, e = np.asarray(score, float), np.asarray(event, bool)
    pos, neg = s[e], s[~e]
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    return float(((pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum())
                 / (len(pos) * len(neg)))


def noise_to_signal(score, event, thr) -> float:
    s, e = np.asarray(score), np.asarray(event, bool)
    sig = s >= thr
    hit = (sig & e).sum() / max(e.sum(), 1)
    false = (sig & ~e).sum() / max((~e).sum(), 1)
    return float(false / hit) if hit > 0 else np.inf


# ---------------------------------------------------------------- B1: macro core fans
def macro_fan_calibration() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Are the macro model's published fan widths calibrated against its own out-of-sample
    errors? Ensemble forecast per vintage = inverse-RMSE² combination of the models that beat
    the random walk (the macro model's own rule); σ = width of the published 80 % band."""
    bt = spine._csv(config.MACRO_FILES["validation_backtest"])
    rows, pits = [], []
    for code, name in (("nonoil_realg", "Qeyri-neft real artımı"), ("cpi_infl", "İnflyasiya"),
                       ("brent_usd", "Brent (log)"), ("current_account", "Cari hesab")):
        b = bt[(bt.series_code == code) & (bt.horizon_h == 1) & ~bt.model.isin(["DINAMIKLIK", "NAZIRLIK_SPES"])]
        rm = b.groupby("model")["error"].apply(lambda e: np.sqrt(np.mean(e ** 2)))
        rw = rm.get("RW", np.inf)
        good = rm[(rm < rw) & (rm.index != "RW")]
        if good.empty:
            continue
        w = (1 / good ** 2) / (1 / good ** 2).sum()
        piv = b.pivot_table(index="vintage_year", columns="model", values="forecast").dropna(subset=list(good.index))
        act = b.groupby("vintage_year")["actual"].first().reindex(piv.index)
        f = (piv[good.index] * w).sum(axis=1)
        e = (act - f).to_numpy()
        if code == "brent_usd":
            sig = float(np.log(spine.baseline().at[2026, "brent_usd_hi80"] / spine.baseline().at[2026, "brent_usd_lo80"])
                        / (2 * stats.norm.ppf(0.9)))
        else:
            sig = spine.baseline_band_sigma(code, 2026)
        rmse_ens = float(np.sqrt(np.mean(e ** 2)))
        pit = stats.norm.cdf(e / sig)
        lo10 = pit < 0.10
        cov80 = float(np.mean((pit >= 0.10) & (pit <= 0.90)))
        cov90 = float(np.mean((pit >= 0.05) & (pit <= 0.95)))
        ks, ksp = ks_uniform(pit)
        bk, bkp = berkowitz(pit)
        lr, kp = kupiec(lo10, 0.10)
        cc = christoffersen(lo10, 0.10)
        rows.append({"hedef": code, "ad": name, "n": len(e), "pencere": f"{piv.index.min()}–{piv.index.max()}",
                     "rmse_model": rmse_ens, "rmse_rw": float(rw), "bacariq_rw": 1 - rmse_ens / rw,
                     "sigma_yelpik": sig, "rmse_sigma_nisbeti": rmse_ens / sig,
                     "ehate80": cov80, "ehate90": cov90, "KS_p": ksp, "Berkowitz_p": bkp,
                     "Kupiec10_p": kp, "Christoffersen_cc_p": cc["p_cc"],
                     "melumat_bazasi": "psevdo-real vaxt (makro model: son buraxılış məlumatı, genişlənən pəncərə)"})
        pits += [{"hedef": code, "il": int(y) + 1, "pit": float(p_)} for y, p_ in zip(piv.index, pit)]
    return pd.DataFrame(rows), pd.DataFrame(pits)


# ---------------------------------------------------------------- B2: Brent densities (real-time)
def brent_density_backtest(h_months: int = 12, start: str = "1995-12-01") -> tuple[dict, pd.DataFrame]:
    """Density of the h-month-ahead monthly-average Brent price: no-change centre with the
    empirical distribution of past h-month log changes (only data up to the origin).
    Annual non-overlapping origins (December) for the calibration tests."""
    b = np.log(feeds.monthly("brent"))
    ch = (b.shift(-h_months) - b).dropna()
    rows = []
    for t in b.index[(b.index >= start) & (b.index.month == 12)]:
        target = t + pd.DateOffset(months=h_months)
        if target not in b.index:
            continue
        past = (b - b.shift(h_months)).loc[:t].dropna()
        if len(past) < 60:
            continue
        y = b.loc[target] - b.loc[t]
        pit = float(((past < y).sum() + 0.5) / (len(past) + 1))       # rank PIT, never exactly 0 or 1
        rows.append({"orijin": t.strftime("%Y-%m"), "hedef_ay": target.strftime("%Y-%m"), "faktiki_log": float(y),
                     "pit": pit, "q05": float(past.quantile(0.05)), "q10": float(past.quantile(0.10)),
                     "q90": float(past.quantile(0.90)), "q95": float(past.quantile(0.95)),
                     "crps_model": crps_sample(past.to_numpy()[-600:], float(y)),
                     "crps_normal_bench": crps_normal(0.0, float(past.iloc[:24].std()) if len(past) > 24 else float(past.std()), float(y)),
                     "p_crash": float((past <= np.log(0.7)).mean()), "crash": bool(y <= np.log(0.7))})
    D = pd.DataFrame(rows)
    pit = D["pit"].to_numpy()
    lo5, lo10 = pit < 0.05, pit < 0.10
    out = {"n": len(D), "pencere": f"{D['orijin'].iloc[0]}–{D['orijin'].iloc[-1]}",
           "ehate80": float(np.mean((pit >= 0.1) & (pit <= 0.9))), "ehate90": float(np.mean((pit >= 0.05) & (pit <= 0.95))),
           "KS_p": ks_uniform(pit)[1], "Berkowitz_p": berkowitz(pit)[1],
           "Kupiec05_p": kupiec(lo5, 0.05)[1], "Kupiec10_p": kupiec(lo10, 0.10)[1],
           "Christoffersen_cc_p": christoffersen(lo10, 0.10)["p_cc"],
           "crps_model": float(D["crps_model"].mean()), "crps_bench": float(D["crps_normal_bench"].mean()),
           "brier_crash": float(np.mean((D["p_crash"] - D["crash"]) ** 2)),
           "brier_clim": float(np.mean((D["crash"].mean() - D["crash"]) ** 2))}
    return out, D


# ---------------------------------------------------------------- B3: Growth-at-Risk rolling origin
def gar_backtest(first_origin: int = 2012) -> tuple[dict, pd.DataFrame]:
    d = simulate._gar_frame()
    rows = []
    for t in range(first_origin, config.LAST_ACTUAL):
        train = d.loc[:t - 1].dropna()            # target y = nonoil_g(t+1): rows up to t-1 have y ≤ t
        if len(train) < 10 or d.loc[t, ["dln_brent", "ln_gpr_reg"]].isna().any():
            continue
        fits = simulate.gar_fit(train)
        qv = simulate.gar_quantiles(fits, d.loc[t, ["dln_brent", "ln_gpr_reg"]].to_dict())
        a, loc, sc = simulate.skew_fit(qv)
        y = d.loc[t, "y"]
        hist = train["y"].to_numpy()
        rows.append({"orijin": t, "hedef_il": t + 1, "faktiki": y, "q10": qv[0], "q50": qv[2], "q90": qv[4],
                     "pit": float(stats.skewnorm.cdf(y, a, loc, sc)),
                     "p_below2": float(stats.skewnorm.cdf(2.0, a, loc, sc)),
                     "bench_q10": float(np.quantile(hist, 0.10)), "bench_q50": float(np.quantile(hist, 0.5)),
                     "bench_q90": float(np.quantile(hist, 0.90)), "rw": float(train["y"].iloc[-1])})
    G = pd.DataFrame(rows)
    y = G["faktiki"].to_numpy()
    out = {"n": len(G), "pencere": f"{G['hedef_il'].min()}–{G['hedef_il'].max()}",
           "rmse_median": float(np.sqrt(np.mean((y - G["q50"]) ** 2))),
           "rmse_mean_bench": float(np.sqrt(np.mean((y - G["bench_q50"]) ** 2))),
           "rmse_rw_bench": float(np.sqrt(np.mean((y - G["rw"]) ** 2))),
           "pinball10": pinball(y, G["q10"], 0.10), "pinball10_bench": pinball(y, G["bench_q10"], 0.10),
           "pinball50": pinball(y, G["q50"], 0.50), "pinball50_bench": pinball(y, G["bench_q50"], 0.50),
           "ehate80": float(np.mean((y >= G["q10"]) & (y <= G["q90"]))),
           "KS_p": ks_uniform(G["pit"].to_numpy())[1], "Berkowitz_p": berkowitz(G["pit"].to_numpy())[1],
           "Kupiec10_p": kupiec(G["pit"].to_numpy() < 0.10, 0.10)[1],
           "auroc_below2": auroc(G["p_below2"], y < 2.0), "n_events": int((y < 2.0).sum())}
    return out, G


# ---------------------------------------------------------------- B4: early-warning (monthly, real-time)
def ews_brent_crash(h: int = 12, drop: float = 0.30) -> tuple[dict, pd.DataFrame]:
    """Logit early-warning for 'Brent falls ≥ 30 % over the next 12 months' on market
    signals known at the origin (VIX, regional GPR change, Brent 12-month momentum, US 10y
    change). Re-estimated each January on an expanding window; threshold chosen in-sample to
    maximise TPR − FPR, then applied out of sample."""
    b = np.log(feeds.monthly("brent"))
    vix = np.log(feeds.monthly("vix"))
    g = np.log(factors.regional_gpr_monthly())
    u = feeds.monthly("ust10")
    X = pd.DataFrame({"vix": vix, "dgpr": g.diff(3), "mom": b.diff(12), "dust": u.diff(12)}).dropna()
    yv = ((b.shift(-h) - b) <= np.log(1 - drop)).astype(float).where(b.shift(-h).notna())
    D = X.join(yv.rename("y")).dropna()
    preds = []
    for year in range(2000, pd.Timestamp(config.as_of()).year + 1):
        cut = pd.Timestamp(f"{year}-01-01") - pd.DateOffset(months=h)       # labels known at origin
        tr = D[D.index < cut]
        te = D[(D.index >= pd.Timestamp(f"{year}-01-01")) & (D.index < pd.Timestamp(f"{year + 1}-01-01"))]
        if tr["y"].sum() < 3 or te.empty:
            continue
        try:
            m = sm.Logit(tr["y"], sm.add_constant(tr[["vix", "dgpr", "mom", "dust"]])).fit(disp=0, maxiter=200)
        except Exception:
            continue
        ptr = m.predict(sm.add_constant(tr[["vix", "dgpr", "mom", "dust"]]))
        cand = np.unique(np.quantile(ptr, np.linspace(0.5, 0.99, 50)))
        j = [((ptr >= c) & (tr["y"] == 1)).sum() / tr["y"].sum() - ((ptr >= c) & (tr["y"] == 0)).sum() / (tr["y"] == 0).sum()
             for c in cand]
        thr = float(cand[int(np.argmax(j))])
        pte = m.predict(sm.add_constant(te[["vix", "dgpr", "mom", "dust"]], has_constant="add"))
        preds.append(pd.DataFrame({"ay": te.index.strftime("%Y-%m"), "ehtimal": pte.values,
                                   "hedd": thr, "hadise": te["y"].values}))
    P = pd.concat(preds, ignore_index=True)
    sig = P["ehtimal"] >= P["hedd"]
    e = P["hadise"].astype(bool)
    hit = (sig & e).sum() / max(e.sum(), 1)
    false = (sig & ~e).sum() / max((~e).sum(), 1)
    out = {"n": len(P), "pencere": f"{P['ay'].iloc[0]}–{P['ay'].iloc[-1]}", "n_events": int(e.sum()),
           "auroc": auroc(P["ehtimal"], e), "nts": float(false / hit) if hit > 0 else np.inf,
           "hit_rate": float(hit), "false_alarm_rate": float(false)}
    return out, P


def ews_slowdown(threshold: float | None = None) -> tuple[dict, pd.DataFrame]:
    """Signals-approach early warning for R13: 'non-oil growth next year below the threshold'.
    Signals with a direction fixed a priori by the transmission mechanism (FR1 channel table):
    a fall in Brent this year and a fall in real public investment this year. Each is
    standardised with data up to the origin only and the composite is their mean — no weights
    are estimated, so every score is out of sample. The alarm threshold is chosen on the
    expanding window (max TPR − FPR); with no past event the default is z ≥ 1."""
    p = factors.params()
    thr_g = p["nonoil_gar_threshold"] if threshold is None else threshold
    P = factors.channels()["_panel"]
    S = pd.DataFrame({"s_brent": -P["dln_brent"], "s_inv": -P["inv_state_g"]})
    y = P["nonoil_g"].shift(-1)
    rows = []
    for t in range(2003, config.LAST_ACTUAL):
        past = S.loc[:t].dropna()
        if len(past) < 5 or pd.isna(y.get(t)):
            continue
        z = ((past - past.mean()) / past.std()).mean(axis=1)
        score = float(z.loc[t])
        hist_ev = (y.loc[past.index[:-1]] < thr_g).to_numpy()
        hist_sc = z.iloc[:-1].to_numpy()
        if hist_ev.any() and (~hist_ev).any():
            cand = np.unique(hist_sc)
            j = [(hist_sc[hist_ev] >= c).mean() - (hist_sc[~hist_ev] >= c).mean() for c in cand]
            alarm_thr = float(cand[int(np.argmax(j))])
        else:
            alarm_thr = 1.0
        rows.append({"orijin": t, "hedef_il": t + 1, "siqnal": score, "hedd": alarm_thr,
                     "hadise": bool(y.loc[t] < thr_g), "faktiki": float(y.loc[t])})
    D = pd.DataFrame(rows)
    sig = D["siqnal"] >= D["hedd"]
    e = D["hadise"]
    hit = (sig & e).sum() / max(e.sum(), 1)
    false = (sig & ~e).sum() / max((~e).sum(), 1)
    return ({"n": len(D), "pencere": f"{D['hedef_il'].min()}–{D['hedef_il'].max()}", "n_events": int(e.sum()),
             "auroc": auroc(D["siqnal"], e), "nts": float(false / hit) if hit > 0 else np.inf,
             "hit_rate": float(hit), "false_alarm_rate": float(false),
             "current": float(((S.dropna() - S.dropna().mean()) / S.dropna().std()).mean(axis=1).iloc[-1])}, D)


# ---------------------------------------------------------------- B5: event probability R06
def gpr_probability_backtest() -> dict:
    p = factors.params()
    gm = factors.regional_gpr_monthly()
    a = gm.groupby(gm.index.year).agg(["mean", "count"])
    s = a[a["count"] == 12]["mean"]
    rows = []
    for t in range(s.index[0] + 10, s.index[-1]):
        past = s.loc[:t]
        q_hi, q_reg = past.quantile(p["gpr_quantile"]), past.quantile(0.75)
        prev, nxt = past.iloc[:-1], past.shift(-1).iloc[:-1]
        cond = (prev >= q_reg) if past.iloc[-1] >= q_reg else (prev < q_reg)
        k, n = int((nxt[cond] >= q_hi).sum()), int(cond.sum())
        prob = (k + 0.5) / (n + 1)
        clim = float((past >= q_hi).mean())
        rows.append({"t": t, "p": prob, "clim": clim, "y": float(s.loc[t + 1] >= q_hi)})
    R = pd.DataFrame(rows)
    return {"n": len(R), "pencere": f"{R['t'].min() + 1}–{R['t'].max() + 1}",
            "brier": float(np.mean((R["p"] - R["y"]) ** 2)), "brier_clim": float(np.mean((R["clim"] - R["y"]) ** 2)),
            "auroc": auroc(R["p"], R["y"].astype(bool)), "n_events": int(R["y"].sum())}


# ---------------------------------------------------------------- archive of real-time risk forecasts
ARCHIVE = config.OUTPUT / "forecast_archive"


def archive_forecast(res: simulate.SimResult) -> None:
    """Freeze this run's predictive distribution (quantiles) with its as-of date and input
    hashes: the real-time record the quarterly backtest scores once outcomes are published."""
    ARCHIVE.mkdir(exist_ok=True)
    tab = simulate.distribution_table(res)
    tab.insert(0, "as_of", config.as_of().isoformat())
    tab["baseline_id"] = spine.baseline_id()
    man = feeds.read_manifest()
    tab["feeds_sha"] = "|".join(man[man.status == "ok"].groupby("feed").tail(1)["sha256"].str[:8])
    tab.to_csv(ARCHIVE / f"risk_forecast_{config.as_of().isoformat()}.csv", index=False, float_format="%.6g")


def evaluate_archive() -> pd.DataFrame:
    """Score archived forecasts whose target year now has an actual in the macro model."""
    rows = []
    act = {"g": spine.macro_series("nonoil_realg", "actual")["value"],
           "cpi": spine.macro_series("cpi_infl", "actual")["value"]}
    for f in sorted(ARCHIVE.glob("risk_forecast_*.csv")) if ARCHIVE.exists() else []:
        t = pd.read_csv(f)
        for r in t[t["gosterici"].isin(act)].itertuples():
            a = act[r.gosterici]
            if r.il in a.index and r.il > int(r.as_of[:4]) - 1:
                qs = [r.p05, r.p10, r.p25, r.p50, r.p75, r.p90, r.p95]
                y = a[r.il]
                pit = float(np.interp(y, qs, [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95], left=0.025, right=0.975))
                rows.append({"as_of": r.as_of, "gosterici": r.gosterici, "il": r.il, "faktiki": y, "pit": pit,
                             "p10_pozuldu": y < r.p10})
    return pd.DataFrame(rows, columns=["as_of", "gosterici", "il", "faktiki", "pit", "p10_pozuldu"])


# ---------------------------------------------------------------- the quarterly run
REGISTER = config.OUTPUT / "NFR1_backtest_register.csv"


def quarter(d=None) -> str:
    d = d or config.as_of()
    return f"{d.year}Q{(d.month - 1) // 3 + 1}"


def run_all() -> dict:
    p = factors.params()
    a = p["test_alpha"]
    macro, macro_pit = macro_fan_calibration()
    brent, brent_d = brent_density_backtest()
    gar, gar_d = gar_backtest()
    ews, ews_d = ews_brent_crash()
    ews2, ews2_d = ews_slowdown()
    gpr = gpr_probability_backtest()
    from . import measures
    ana = measures.analogues()
    arch = evaluate_archive()
    RT = "real vaxt (bazar məlumatı yenidən baxılmır)"
    PRT = "psevdo-real vaxt (son buraxılış; vintaj arxivi 2026-10-02-dən yığılır)"
    rows = []
    def add(tid, model, hedef, n, pencere, metrik, deyer, hedd, kecdi, basis, qeyd=""):
        rows.append({"test_id": tid, "model": model, "hedef": hedef, "n": n, "pencere": pencere, "metrik": metrik,
                     "deyer": deyer, "hedd": hedd, "netice": "keçdi" if kecdi else "keçmədi",
                     "melumat_bazasi": basis, "qeyd": qeyd})
    # (1) accuracy against a simple benchmark
    for r in macro.itertuples():
        add("D1", "makro §15.5.1 ansamblı", r.hedef, r.n, r.pencere, "bacarıq RW-yə qarşı (1 − RMSE/RMSE_RW)",
            r.bacariq_rw, "> 0", r.bacariq_rw > 0, r.melumat_bazasi)
    add("D2", "GaR kvantil reqressiyası — müstəqil yoxlama (median)", "nonoil_g", gar["n"], gar["pencere"], "RMSE / RMSE(tarixi orta)",
        gar["rmse_median"] / gar["rmse_mean_bench"], "< 1", gar["rmse_median"] < gar["rmse_mean_bench"], PRT)
    add("D3", "GaR kvantil reqressiyası — müstəqil yoxlama (P10)", "nonoil_g", gar["n"], gar["pencere"], "pinball(0,10) / etalon",
        gar["pinball10"] / gar["pinball10_bench"], "< 1", gar["pinball10"] < gar["pinball10_bench"], PRT,
        "etalon: genişlənən pəncərənin şərtsiz empirik kvantili")
    rm_e, rm_0 = float(np.sqrt((ana["xeta"] ** 2).mean())), float(np.sqrt((ana["faktiki_sapma"] ** 2).mean()))
    add("D4", "ötürmə mühərriki (tarixi analoqlar)", "nonoil_g sapması", len(ana), f"{ana['il'].min()}–{ana['il'].max()}",
        "RMSE / RMSE(sıfır sapma etalonu)", rm_e / rm_0, "< 1", rm_e < rm_0, PRT,
        f"korrelyasiya {ana[['faktiki_sapma', 'proqnoz_sapma']].corr().iloc[0, 1]:.2f}; epizodlar 2009/2015/2016/2020")
    ep = ana[ana["epizod"] & ~ana["kalibrləməyə_daxil"]]
    add("D5", "ötürmə mühərriki (adlı epizodlar, kalibrləmədən kənar)", "nonoil_g sapması", len(ep),
        ";".join(map(str, ep["il"])), "tolerans (eyni işarə, |xəta| ≤ 3 f.b.) ödənilən pay",
        float(ep["tolerans_odenilir"].mean()), "≥ 0,5", ep["tolerans_odenilir"].mean() >= 0.5, PRT)
    add("D6", "Brent sıxlığı (CRPS)", "brent 12 ay", brent["n"], brent["pencere"], "CRPS / CRPS(normal etalon)",
        brent["crps_model"] / brent["crps_bench"], "< 1", brent["crps_model"] < brent["crps_bench"], RT,
        "etalon: ilk 24 müşahidənin σ-sı ilə normal paylanma")
    # (3) distribution tests
    for r in macro.itertuples():
        add("P1", "makro §15.5.1 yelpiyi", r.hedef, r.n, r.pencere, "80% interval əhatəsi", r.ehate80,
            f"[{p['coverage80_lo']:.2f}; {p['coverage80_hi']:.2f}]", p["coverage80_lo"] <= r.ehate80 <= p["coverage80_hi"],
            r.melumat_bazasi, f"RMSE/σ_yelpik = {r.rmse_sigma_nisbeti:.2f}")
        add("P2", "makro §15.5.1 yelpiyi", r.hedef, r.n, r.pencere, "PIT bərabərliyi (KS) p", r.KS_p, f"> {a}", r.KS_p > a, r.melumat_bazasi)
        add("P3", "makro §15.5.1 yelpiyi", r.hedef, r.n, r.pencere, "Kupiec (P10 pozuntuları) p", r.Kupiec10_p, f"> {a}",
            r.Kupiec10_p > a, r.melumat_bazasi)
    for tid, met, val, hedd, ok in (
            ("P4", "80% interval əhatəsi", brent["ehate80"], f"[{p['coverage80_lo']:.2f}; {p['coverage80_hi']:.2f}]",
             p["coverage80_lo"] <= brent["ehate80"] <= p["coverage80_hi"]),
            ("P5", "90% interval əhatəsi", brent["ehate90"], f"[{p['coverage90_lo']:.2f}; {p['coverage90_hi']:.2f}]",
             p["coverage90_lo"] <= brent["ehate90"] <= p["coverage90_hi"]),
            ("P6", "PIT bərabərliyi (KS) p", brent["KS_p"], f"> {a}", brent["KS_p"] > a),
            ("P7", "Berkowitz LR p", brent["Berkowitz_p"], f"> {a}", brent["Berkowitz_p"] > a),
            ("P8", "Kupiec (P5 pozuntuları) p", brent["Kupiec05_p"], f"> {a}", brent["Kupiec05_p"] > a),
            ("P9", "Kupiec (P10 pozuntuları) p", brent["Kupiec10_p"], f"> {a}", brent["Kupiec10_p"] > a),
            ("P10", "Christoffersen şərti əhatə p", brent["Christoffersen_cc_p"], f"> {a}", brent["Christoffersen_cc_p"] > a)):
        add(tid, "Brent sıxlığı (R01)", "brent 12 ay", brent["n"], brent["pencere"], met, val, hedd, ok, RT)
    for tid, met, val, hedd, ok in (
            ("P11", "80% interval (P10–P90) əhatəsi", gar["ehate80"], f"[{p['coverage80_lo']:.2f}; {p['coverage80_hi']:.2f}]",
             p["coverage80_lo"] <= gar["ehate80"] <= p["coverage80_hi"]),
            ("P12", "PIT bərabərliyi (KS) p", gar["KS_p"], f"> {a}", gar["KS_p"] > a),
            ("P13", "Berkowitz LR p", gar["Berkowitz_p"], f"> {a}", gar["Berkowitz_p"] > a),
            ("P14", "Kupiec (P10 pozuntuları) p", gar["Kupiec10_p"], f"> {a}", gar["Kupiec10_p"] > a)):
        add(tid, "GaR kvantil reqressiyası — müstəqil yoxlama (R13)", "nonoil_g", gar["n"], gar["pencere"], met, val, hedd, ok, PRT)
    add("E1", "EWS siqnal yanaşması: gələn il qeyri-neft artımı < hədd (R13)", "nonoil_g", ews2["n"], ews2["pencere"],
        "AUROC (nümunədən kənar)", ews2["auroc"], f"≥ {p['ews_auroc_min']:.2f}", ews2["auroc"] >= p["ews_auroc_min"], PRT,
        f"siqnallar: Brent enişi, dövlət investisiyasının azalması (istiqamət əvvəlcədən); səs-küy/siqnal = {ews2['nts']:.2f}; "
        f"hadisə sayı {ews2['n_events']} — kiçik nümunə; hədd Nazirliyin yanlış həyəcan tolerantlığı ilə dəqiqləşdirilməlidir")
    add("E1b", "EWS logit: Brent ≥30% enişi 12 ayda (R01) — mənfi nəticə", "brent", ews["n"], ews["pencere"],
        "AUROC (nümunədən kənar)", ews["auroc"], f"≥ {p['ews_auroc_min']:.2f}", ews["auroc"] >= p["ews_auroc_min"], RT,
        f"neft qiymətinin çöküşü bazar siqnalları ilə proqnozlaşdırılmır (səs-küy/siqnal {ews['nts']:.2f}); R01 ehtimalı EWS ilə deyil, paylanma ilə verilir")
    add("E2", "GaR kvantil reqressiyası — müstəqil yoxlama: P(qeyri-neft artımı < 2%) (R13)", "nonoil_g", gar["n"], gar["pencere"], "AUROC (nümunədən kənar)",
        gar["auroc_below2"], f"≥ {p['ews_auroc_min']:.2f}", (gar["auroc_below2"] or 0) >= p["ews_auroc_min"], PRT,
        f"hadisə sayı {gar['n_events']}")
    add("E3", "R06 keçid ehtimalı", "regional GPR ≥ P90", gpr["n"], gpr["pencere"], "Brier / Brier(klimatologiya)",
        gpr["brier"] / gpr["brier_clim"], "< 1", gpr["brier"] < gpr["brier_clim"], RT, f"AUROC {gpr['auroc']:.2f}")
    add("E4", "Brent sıxlığı: P(12 ayda ≥30% eniş)", "brent", brent["n"], brent["pencere"], "Brier / Brier(klimatologiya)",
        brent["brier_crash"] / brent["brier_clim"], "< 1", brent["brier_crash"] < brent["brier_clim"], RT)
    # (2) archived real-time forecasts
    add("R1", "arxivləşdirilmiş real vaxt risk proqnozları", "nonoil_g; cpi", len(arch), "—",
        "yetişmiş proqnoz sayı", len(arch), "≥ 0", True, "real vaxt (arxivdən)",
        "nəticəsi açıqlanmış hədəf ili olan arxiv proqnozları ilk buraxılış rəqəmi ilə qiymətləndirilir")
    T = pd.DataFrame(rows)
    T.insert(0, "rub", quarter())
    T.insert(1, "tarix", config.as_of().isoformat())
    T["baseline_id"] = spine.baseline_id()

    # recalibration rule: fan scale for the simulation's core residual, from the macro coverage tests
    cal = []
    for code, key in (("nonoil_realg", "nonoil"), ("cpi_infl", "cpi")):
        r = macro[macro["hedef"] == code]
        if r.empty:
            continue
        r = r.iloc[0]
        ok = p["coverage80_lo"] <= r["ehate80"] <= p["coverage80_hi"]
        mp = macro_pit[macro_pit["hedef"] == code]["pit"].to_numpy()
        zabs = np.abs(stats.norm.ppf(np.clip(mp, 1e-6, 1 - 1e-6)))
        scale = 1.0 if ok else float(np.clip(np.quantile(zabs, 0.8) / stats.norm.ppf(0.9), 0.5, 2.0))
        cal.append({"hedef": key, "miqyas": scale, "ehate80": r["ehate80"], "n": int(r["n"]),
                    "qerar": "dəyişiklik yoxdur — əhatə tolerans daxilindədir" if ok else
                    f"qalıq σ {scale:.2f} dəfə miqyaslanır (əhatə {r['ehate80']:.2f} tolerans xaricindədir)",
                    "rub": quarter(), "tarix": config.as_of().isoformat()})
    ok_b = p["coverage80_lo"] <= brent["ehate80"] <= p["coverage80_hi"]
    zb = np.abs(stats.norm.ppf(brent_d["pit"].to_numpy()))
    sb = 1.0 if ok_b else float(np.clip(np.quantile(zb, 0.8) / stats.norm.ppf(0.9), 0.5, 2.0))
    cal.append({"hedef": "brent", "miqyas": sb, "ehate80": brent["ehate80"], "n": int(brent["n"]),
                "qerar": "dəyişiklik yoxdur — əhatə tolerans daxilindədir" if ok_b else
                f"Brent innovasiyaları {sb:.2f} dəfə miqyaslanır (əhatə {brent['ehate80']:.2f} tolerans xaricindədir)",
                "rub": quarter(), "tarix": config.as_of().isoformat()})
    C = pd.DataFrame(cal)
    C.to_csv(config.OUTPUT / "NFR1_calibration.csv", index=False, float_format="%.4g")

    # quarterly register: one block per quarter (re-runs in the same quarter replace it)
    if REGISTER.exists():
        old = pd.read_csv(REGISTER)
        old = old[old["rub"] != quarter()]
        reg = pd.concat([old, T], ignore_index=True)
    else:
        reg = T
    reg.to_csv(REGISTER, index=False, float_format="%.4g")
    T.to_csv(config.OUTPUT / "NFR1_backtest_results.csv", index=False, float_format="%.4g")
    brent_d.to_csv(config.OUTPUT / "NFR1_brent_density_pit.csv", index=False, float_format="%.5g")
    gar_d.to_csv(config.OUTPUT / "NFR1_gar_rolling.csv", index=False, float_format="%.5g")
    ews_d.to_csv(config.OUTPUT / "NFR1_ews_brent_predictions.csv", index=False, float_format="%.5g")
    ews2_d.to_csv(config.OUTPUT / "NFR1_ews_slowdown.csv", index=False, float_format="%.5g")
    macro_pit.to_csv(config.OUTPUT / "NFR1_macro_fan_pit.csv", index=False, float_format="%.5g")
    ana.to_csv(config.OUTPUT / "FR3_historical_analogues.csv", index=False, float_format="%.4g")
    return {"table": T, "macro": macro, "brent": brent, "gar": gar, "ews": ews, "ews2": ews2, "gpr": gpr, "calibration": C,
            "archive": arch}


def due() -> bool:
    """True when the current quarter has no block in the register yet (quarterly cadence)."""
    if not REGISTER.exists():
        return True
    return quarter() not in set(pd.read_csv(REGISTER)["rub"])
