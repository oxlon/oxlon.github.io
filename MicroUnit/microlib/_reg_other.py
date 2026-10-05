"""Non-OLS builders: 2SLS, two-way FE panel (Driscoll-Kraay), logit/poisson (statsmodels), other (precomputed).
Only the diagnostics that make sense are computed; the rest are null with a reason."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import diagnostics as D
from . import robustness as R
from ._regcore import Nulls, empty_diag, empty_fit, empty_rob, pack_fitted, pack_robustness
from ._util import years_of
from .estimators import cov_label, first_stage_F, panel_fe_dk, parse_cov, tsls_np

TS_KEYS = ["bg_lm_p", "bg_lm_p_lag1", "white_p", "bp_p", "reset_p"]


def _wald_all(b, V, dof, skip=1):
    bs, Vs = b[skip:], V[skip:, skip:]
    m = len(bs)
    if m == 0:
        return None, None
    F = float(bs @ np.linalg.pinv(Vs) @ bs) / m
    return F, float(1 - stats.f.cdf(F, m, dof))


def build_iv(y, X, o):
    iv = o["iv"]
    endog = list(iv["endog"])
    Z = iv["Z"] if isinstance(iv["Z"], pd.DataFrame) else pd.DataFrame(iv["Z"])
    exog = [c for c in X.columns if c not in endog and c != "const"]
    d = pd.concat([y.rename("__y__"), X[endog + exog], Z.add_prefix("__z__")], axis=1).dropna().sort_index()
    zc = [c for c in d.columns if c.startswith("__z__")]
    one = np.ones((len(d), 1))
    W = np.column_stack([one, d[endog + exog].to_numpy(float)])
    I = np.column_stack([one, d[exog].to_numpy(float), d[zc].to_numpy(float)])
    yv = d["__y__"].to_numpy(float)
    names = ["const"] + endog + exog
    r = tsls_np(yv, W, I, o["cov"], o.get("hac_lags"))
    n, k = W.shape
    fit = empty_fit()
    N = Nulls(fit)
    u = r["u"]
    tss = ((yv - yv.mean()) ** 2).sum()
    N.put("r2", (1 - (u @ u) / tss, None))
    N.put("r2_adj", (1 - (1 - fit["r2"]) * (n - 1) / r["dof"], None))
    N.put("ser", (np.sqrt((u @ u) / r["dof"]), None))
    F, Fp = _wald_all(r["b"], r["V"], r["dof"])
    N.put("f_stat", (F, "yalnız sabit"))
    N.put("f_p", (Fp, "yalnız sabit"))
    N.na(["aic", "bic", "loglik"], "2SLS: həqiqətəbənzərlik əsaslı göstəricilər tətbiq olunmur")
    diag = empty_diag()
    G = Nulls(diag)
    G.put("dw", D.dw(u))
    G.put("jb_p", D.jb_p(u))
    G.na(TS_KEYS, "2SLS: OLS köməkçi reqressiyasına əsaslanan test tətbiq olunmur")
    Xdf = d[endog + exog]
    G.put("vif_max", D.vif_max(Xdf))
    G.put("cond_number", D.cond_number(Xdf))
    fsF = first_stage_F(d[endog].to_numpy(float), d[exog].to_numpy(float), d[zc].to_numpy(float))
    diag["first_stage_F"] = dict(zip(endog, [float(v) for v in fsF]))
    diag["sargan_J"], diag["sargan_p"] = r["sargan_J"], r["sargan_p"]
    stoch, _, has_trend = D.classify(Xdf, o.get("det"))
    diag["eg_trend"] = "ct" if (o.get("trend") or has_trend) else "c"
    if o.get("coint") is True:
        eg = D.eg_coint_p(u, o.get("n_i1") or len(stoch), o.get("trend") or has_trend)
        diag.update(eg_coint_p=eg["p"], eg_stat=eg["stat"], eg_N=eg["N"])
        diag["coint_established"] = (eg["p"] <= 0.10) if eg["p"] is not None else None
    else:
        G.na(["eg_coint_p", "eg_stat", "eg_N", "coint_established"], "2SLS: kointeqrasiya testi tələb olunmayıb")
    G.na(["diff_form"], "2SLS: fərq forması hesablanmır")
    rob = empty_rob()
    rob["null_reasons"] = {}
    yrs = np.asarray(years_of(d.index))

    def fit_fn(m):
        q = tsls_np(yv[m], W[m], I[m], o["cov"], o.get("hac_lags"))
        return q["b"], q["se"]

    rec = R.recursive(fit_fn, yrs, names, n_min=k + 5)
    lo = R.loo(fit_fn, yrs, names)
    pack_robustness(rob, rec, lo, None, None, names)
    rob["null_reasons"].update(chow="2SLS: OLS əsaslı Chow tətbiq olunmur", cusum_p="2SLS: CUSUM tətbiq olunmur")
    kind, _ = parse_cov(o["cov"])
    return dict(names=names, roles={c: "const" if c == "const" else "regressor" for c in names},
                coef_rec=dict(zip(names, r["b"])), se_rec=dict(zip(names, r["se"])), dof=r["dof"], p_dist="t",
                sample=dict(start=int(yrs.min()), end=int(yrs.max()), n=int(n), k=int(k), df_resid=int(r["dof"])),
                cov_type=cov_label(kind, r["lags"], o["cov"]) + " on projected regressors", fit=fit,
                diagnostics=diag, robustness=rob, fitted=pack_fitted(d.index, yv, W @ r["b"]),
                checks={"instruments": list(Z.columns), "overid": r["overid"]})


def build_panel(y, X, o):
    p = o.get("panel") or {}
    idx = y.index
    ent = idx.get_level_values(p.get("entity", 0))
    tim = idx.get_level_values(p.get("time", 1))
    regs = [c for c in X.columns if c != "const"]
    tw = p.get("twoway", True)
    r = panel_fe_dk(y, X[regs], ent, tim, tw, p.get("dk_lags"))
    fit = empty_fit()
    N = Nulls(fit)
    N.put("r2", (r["r2"], None))
    fit["r2_type"] = "within R²"
    N.put("ser", (np.sqrt((r["u"] @ r["u"]) / max(r["n"] - r["k"], 1)), None))
    F, Fp = _wald_all(r["b"], r["V"], r["dof"], skip=0)
    N.put("f_stat", (F, None))
    N.put("f_p", (Fp, None))
    N.na(["r2_adj", "aic", "bic", "loglik"], "FE panel: hesablanmır")
    diag = empty_diag()
    G = Nulls(diag)
    G.put("jb_p", D.jb_p(r["u"]))
    G.na(["dw"] + TS_KEYS, "panel: zaman sırası qalıq testi tətbiq olunmur")
    Xw = pd.DataFrame(r["Xw"], columns=regs)
    G.put("vif_max", D.vif_max(Xw))
    G.put("cond_number", D.cond_number(Xw))
    G.na(["eg_coint_p", "eg_stat", "eg_N", "coint_established", "eg_trend", "diff_form"],
         "panel: kointeqrasiya / fərq forması tətbiq olunmur")
    diag["panel"] = dict(units=r["nN"], periods=r["nT"], dk_lags=r["lags"], inference_df=r["dof"])
    rob = empty_rob()
    rob["null_reasons"] = {}
    df = pd.concat([y.rename("__y__"), X[regs]], axis=1)
    df["__e__"], df["__t__"] = np.asarray(ent), np.asarray(tim)
    df = df.dropna()
    tarr = df["__t__"].to_numpy()

    def fit_fn(m):
        s = df[m]
        if s["__t__"].nunique() < 3:
            raise ValueError("too few periods")
        q = panel_fe_dk(s["__y__"], s[regs], s["__e__"], s["__t__"], tw, p.get("dk_lags"))
        return q["b"], q["se"]

    rec = R.recursive(fit_fn, tarr, regs, n_min=len(regs) + 5)
    lo = R.loo(fit_fn, tarr, regs)
    pack_robustness(rob, rec, lo, None, None, regs)
    rob["null_reasons"].update(chow="panel: Chow tətbiq olunmur", cusum_p="panel: CUSUM tətbiq olunmur")
    yw = r["yw"]
    tv = np.asarray(years_of(pd.Index(r["time"])))
    return dict(names=regs, roles={c: "regressor" for c in regs}, coef_rec=dict(zip(regs, r["b"])),
                se_rec=dict(zip(regs, r["se"])), dof=r["dof"], p_dist="t",
                sample=dict(start=int(tv.min()), end=int(tv.max()), n=int(r["n"]), k=int(r["k"]),
                            df_resid=int(r["dof"])),
                cov_type=f"DK(L={r['lags']}), n/(n-k), t(T-1)", fit=fit, diagnostics=diag, robustness=rob,
                fitted=pack_fitted(r["index"], yw, yw - r["u"], time=r["time"]),
                checks={"note": "fitted/actual are within-transformed"})
