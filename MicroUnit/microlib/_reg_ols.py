"""OLS / DOLS builder: independent statsmodels recomputation, diagnostics and robustness."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import diagnostics as D
from . import robustness as R
from ._regcore import AUG_RE, Nulls, dols_augment, empty_diag, empty_fit, empty_rob, pack_fitted, pack_robustness
from ._util import rel_diff, years_of
from .estimators import cov_label, ols_np, parse_cov, sm_ols


def _filter(d, sample_years):
    if sample_years is None:
        return d
    sy = list(sample_years)
    if len(sy) == 2 and sy[1] - sy[0] > 1:
        return d[(d.index >= sy[0]) & (d.index <= sy[1])]
    return d[d.index.isin(sy)]


def _sort(d):
    try:
        return d.sort_index()
    except TypeError:
        return d


def build_ols(y, X, o):
    dols = o["family"] == "dols"
    X = X.copy()
    if dols and o.get("leads_lags") and not any(AUG_RE.match(c) for c in X.columns):
        _, dets, _ = D.classify(X.dropna(), o.get("det"))
        X = dols_augment(X, *o["leads_lags"], det=dets)
    lr = o.get("lr_names") or [c for c in X.columns if c != "const" and not (dols and AUG_RE.match(c))]
    if o.get("levels") is not None:
        yl, Xl = o["levels"]
        Xl = Xl[lr]
    else:
        yl, Xl = y, X[lr]
    dl = _sort(_filter(pd.concat([yl.rename("__y__"), Xl], axis=1).dropna(), o.get("sample_years")))
    d = _sort(_filter(pd.concat([y.rename("__y__"), X], axis=1).dropna(), o.get("sample_years")))
    yv = d["__y__"].to_numpy(float)
    Xd = d.drop(columns="__y__")
    if o.get("add_const", True) and "const" not in Xd.columns:
        Xd.insert(0, "const", 1.0)
    names = list(Xd.columns)
    Xv = Xd.to_numpy(float)
    n, k = Xv.shape
    if n <= k:
        raise ValueError(f"n={n} <= k={k}: equation not estimable")
    kind, _ = parse_cov(o["cov"])
    res, base, L = sm_ols(yv, Xv, o["cov"], o.get("hac_lags"))
    rnp = ols_np(yv, Xv, o["cov"], L)
    checks = {"sm_vs_numpy_se_max_rel": float(np.max(rel_diff(res.bse, rnp["se"]))) if kind != "other" else None}
    coef_rec = dict(zip(names, map(float, res.params)))
    se_rec = dict(zip(names, map(float, res.bse if kind != "other" else rnp["se"])))
    roles = {c: ("const" if c == "const" else "regressor" if c in lr else "dols_aug") for c in names}

    # long-run (solver) form on the levels sample, with the constant actually reported by the notebook
    fc = o.get("fit_coef") or {}
    b_lr = {c: fc.get(c, coef_rec[c]) for c in lr}
    yl_v = dl["__y__"].to_numpy(float)
    xb = dl[lr].to_numpy(float) @ np.array([b_lr[c] for c in lr]) if lr else np.zeros(len(dl))
    const_recentred = float(np.mean(yl_v - xb))
    const_used = fc.get("const", coef_rec.get("const", 0.0) if "const" in names else 0.0)
    lvl_fit = const_used + xb
    lvl_res = yl_v - lvl_fit
    checks["const_recentred"] = const_recentred

    fit = empty_fit()
    N = Nulls(fit)
    for key, v in (("r2", res.rsquared), ("r2_adj", res.rsquared_adj), ("ser", np.sqrt(res.scale)),
                   ("aic", res.aic), ("bic", res.bic), ("loglik", res.llf)):
        N.put(key, (v, None))
    if k > 1:
        N.put("f_stat", (res.fvalue, "F hesablanmadı"))
        N.put("f_p", (res.f_pvalue, "F hesablanmadı"))
        fit["f_type"] = "HAC-Wald F(m, n-k)" if kind == "hac" else "F"
        fit["f_stat_classical"], fit["f_p_classical"] = float(base.fvalue), float(base.f_pvalue)
    else:
        N.na(["f_stat", "f_p"], "yalnız sabit: F tətbiq olunmur")
    if dols:
        tss = ((yl_v - yl_v.mean()) ** 2).sum()
        fit["r2_levels"] = float(1 - (lvl_res ** 2).sum() / tss) if tss > 0 else None

    diag = empty_diag()
    G = Nulls(diag)
    u = np.asarray(base.resid)
    G.put("dw", D.dw(u))
    G.put("bg_lm_p", D.bg_lm_p(base, 2))
    G.put("bg_lm_p_lag1", D.bg_lm_p(base, 1))
    G.put("jb_p", D.jb_p(u))
    G.put("white_p", D.white_p(u, Xv))
    G.put("bp_p", D.bp_p(u, Xv))
    G.put("reset_p", D.reset_p(base))
    G.put("bp_fitted_p", D.bp_fitted_p(u, base.fittedvalues))
    if dols:  # FR1 `register` computes these on the static levels residual
        G.put("dw_levels", D.dw(lvl_res))
        G.put("jb_p_levels", D.jb_p(lvl_res))
        G.put("bp_fitted_p_levels", D.bp_fitted_p(lvl_res, lvl_fit))
    Xlr = dl[lr] if lr else pd.DataFrame(index=dl.index)
    G.put("vif_max", D.vif_max(Xlr) if lr else (None, "izahedici dəyişən yoxdur"))
    G.put("cond_number", D.cond_number(Xlr) if lr else (None, "izahedici dəyişən yoxdur"))
    if lr:
        diag["cond_number_raw_sm"] = float(np.linalg.cond(np.column_stack([np.ones(len(dl)), Xlr.to_numpy(float)])))
    stoch, dets, has_trend = D.classify(Xlr, o.get("det")) if lr else ([], [], False)
    trend = bool(o.get("trend")) or has_trend
    diag["eg_trend"] = "ct" if trend else "c"
    diag["deterministic"] = dets
    n_i1 = o.get("n_i1") if o.get("n_i1") is not None else len(stoch)
    want = o.get("coint", "auto")
    if want is False or (want == "auto" and n_i1 < 1):
        G.na(["eg_coint_p", "eg_stat", "eg_N", "coint_established"],
             "tətbiq olunmur (dərəcə/stasionar tənlik və ya I(1) izahedici yoxdur)")
    else:
        eg = D.eg_coint_p(lvl_res, n_i1, trend)
        diag.update(eg_coint_p=eg["p"], eg_stat=eg["stat"], eg_N=eg["N"], eg_n_i1=n_i1,
                    eg_resid="static levels residual" if dols else "OLS residual")
        diag["coint_established"] = (eg["p"] <= 0.10) if eg["p"] is not None else None
        if eg.get("reason"):
            diag["null_reasons"]["eg_coint_p"] = eg["reason"]
    if stoch:
        ds = o.get("diff_spec")
        yd, Xdd = (ds[0], ds[1][[c for c in ds[1].columns if c in stoch] or list(ds[1].columns)]) if ds \
            else (dl["__y__"], dl[stoch])
        G.put("diff_form", D.diff_form(yd, Xdd, b_lr, o["cov"] if kind in ("hac", "hc1", "nonrobust") else "hac"))
    else:
        G.na(["diff_form"], "stoxastik izahedici dəyişən yoxdur")

    rob = empty_rob()
    rob["null_reasons"] = {}
    keep = [c for c in names if roles[c] != "dols_aug"]
    ix = [names.index(c) for c in keep]
    yrs = np.asarray(years_of(d.index))

    def fit_fn(m):
        r = ols_np(yv[m], Xv[m], o["cov"], o.get("hac_lags"))
        return r["b"][ix], r["se"][ix]

    rec = R.recursive(fit_fn, yrs, keep, n_min=k + 5)
    lo = R.loo(fit_fn, yrs, keep)
    if dols:  # notebook convention: Chow on the static levels form
        Xs = np.column_stack([np.ones(len(dl)), dl[lr].to_numpy(float)])
        ys, ysy = yl_v, np.asarray(years_of(dl.index))
        rob["stability_form"] = "static levels regression (y on const + long-run regressors)"
    else:
        Xs, ys, ysy = Xv, yv, yrs
        rob["stability_form"] = "estimated regression"
    chow_list = R.chow_set(ys, Xs, ysy, o.get("chow_breaks", (2015, 2020)))
    cus = R.cusum_test(ys, Xs)
    pack_robustness(rob, rec, lo, chow_list, cus, keep)

    if dols:
        fitted = pack_fitted(dl.index, yl_v, lvl_fit)
        fitted["form"] = "long-run levels form (solver add-factor units)"
    else:
        fitted = pack_fitted(d.index, yv, Xv @ np.array([fc.get(c, coef_rec[c]) for c in names]))
    sample = dict(start=int(yrs.min()), end=int(yrs.max()), n=int(n), k=int(k), df_resid=int(n - k))
    if dols:
        sample.update(n_levels=int(len(dl)), levels_start=int(min(years_of(dl.index))),
                      levels_end=int(max(years_of(dl.index))))
    return dict(names=names, roles=roles, coef_rec=coef_rec, se_rec=se_rec, dof=int(n - k), p_dist="t",
                sample=sample, cov_type=cov_label(kind, L, o["cov"]), fit=fit, diagnostics=diag,
                robustness=rob, fitted=fitted, checks=checks, const_recentred=const_recentred,
                dols_const=coef_rec.get("const"), hac_lags=L)
