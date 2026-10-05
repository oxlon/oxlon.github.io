"""Logit / Poisson (statsmodels refit or a precomputed results object) and the generic 'other' builder
(SUR, 3SLS, LA-AIDS, calibrated relations): values taken as given, diagnostics only where possible."""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from . import diagnostics as D
from . import robustness as R
from ._regcore import Nulls, empty_diag, empty_fit, empty_rob, pack_fitted, pack_robustness
from ._util import years_of

TS_ALL = ["dw", "bg_lm_p", "bg_lm_p_lag1", "white_p", "bp_p", "reset_p", "eg_coint_p", "eg_stat", "eg_N",
          "coint_established", "eg_trend", "diff_form"]


def _model(family, yv, Xv):
    return sm.Logit(yv, Xv) if family == "logit" else sm.Poisson(yv, Xv)


def build_glm(y, X, o):
    fam = o["family"]
    res = o.get("results")
    if res is None:
        d = pd.concat([y.rename("__y__"), X], axis=1).dropna()
        Xd = d.drop(columns="__y__")
        if o.get("add_const", True) and "const" not in Xd.columns:
            Xd.insert(0, "const", 1.0)
        names = list(Xd.columns)
        yv, Xv, index = d["__y__"].to_numpy(float), Xd.to_numpy(float), d.index
        res = _model(fam, yv, Xv).fit(disp=0, maxiter=200)
    else:
        names = list(getattr(res.model, "exog_names", None) or X.columns)
        yv, Xv = np.asarray(res.model.endog, float), np.asarray(res.model.exog, float)
        index = y.index if len(y) == len(yv) else pd.RangeIndex(len(yv))
        Xd = pd.DataFrame(Xv, columns=names, index=index)
    n, k = Xv.shape
    fit = empty_fit()
    N = Nulls(fit)
    N.put("r2", (getattr(res, "prsquared", np.nan), "pseudo-R² yoxdur"))
    fit["r2_type"] = "McFadden pseudo-R²"
    N.put("aic", (res.aic, None))
    N.put("bic", (res.bic, None))
    N.put("loglik", (res.llf, None))
    fit["lr_chi2"], fit["lr_p"] = float(res.llr), float(res.llr_pvalue)
    N.na(["r2_adj", "ser", "f_stat", "f_p"], f"{fam}: tətbiq olunmur (LR chi² verilib)")
    diag = empty_diag()
    G = Nulls(diag)
    G.na(TS_ALL + ["jb_p"], f"{fam}: OLS qalıq diaqnostikası tətbiq olunmur")
    Xr = Xd.drop(columns=[c for c in Xd.columns if c == "const"])
    G.put("vif_max", D.vif_max(Xr) if Xr.shape[1] else (None, "izahedici dəyişən yoxdur"))
    G.put("cond_number", D.cond_number(Xr) if Xr.shape[1] else (None, "izahedici dəyişən yoxdur"))
    rob = empty_rob()
    rob["null_reasons"] = {}
    t = o.get("time_index")
    tarr = np.asarray(t) if t is not None else (np.asarray(years_of(index)) if n <= 200 else None)
    if tarr is not None and len(tarr) == n and len(set(tarr.tolist())) >= 3:
        def fit_fn(m):
            q = _model(fam, yv[m], Xv[m]).fit(disp=0, maxiter=200, start_params=res.params)
            return q.params, q.bse

        rec = R.recursive(fit_fn, tarr, names, n_min=k + 5)
        lo = R.loo(fit_fn, tarr, names)
        pack_robustness(rob, rec, lo, None, None, names)
    else:
        rob["null_reasons"].update(recursive="zaman indeksi verilməyib (time_index)", loo_year_range="zaman indeksi yoxdur")
    rob["null_reasons"].update(chow=f"{fam}: Chow tətbiq olunmur", cusum_p=f"{fam}: CUSUM tətbiq olunmur")
    yrs = np.asarray(tarr if tarr is not None and len(tarr) == n else years_of(index))
    return dict(names=names, roles={c: "const" if c == "const" else "regressor" for c in names},
                coef_rec=dict(zip(names, map(float, res.params))), se_rec=dict(zip(names, map(float, res.bse))),
                dof=int(n - k), p_dist="normal",
                sample=dict(start=int(np.min(yrs)), end=int(np.max(yrs)), n=int(n), k=int(k), df_resid=int(n - k)),
                cov_type=o.get("cov_label") or "MLE (inverse Hessian)", fit=fit, diagnostics=diag, robustness=rob,
                fitted=pack_fitted(index, yv, res.predict(Xv), time=yrs), checks={})


def build_other(y, X, o):
    fc, fs = o.get("fit_coef") or {}, o.get("fit_se") or {}
    res = o.get("results")
    names = list(fc)
    resid = o.get("resid")
    if resid is None and res is not None and hasattr(res, "resid"):
        resid = res.resid
    fit = empty_fit()
    N = Nulls(fit)
    if res is not None:
        for key, attr in (("r2", "rsquared"), ("r2_adj", "rsquared_adj"), ("aic", "aic"), ("bic", "bic"),
                          ("loglik", "llf")):
            N.put(key, (getattr(res, attr, None), "nəticə obyektində yoxdur"))
    N.fill_missing("qiymətləndirici üçün yenidən hesablanmayıb")
    diag = empty_diag()
    G = Nulls(diag)
    if resid is not None:
        u = np.asarray(pd.Series(resid).dropna(), float)
        G.put("dw", D.dw(u))
        G.put("jb_p", D.jb_p(u))
    if X is not None and X.shape[1]:
        G.put("vif_max", D.vif_max(X.dropna()))
        G.put("cond_number", D.cond_number(X.dropna()))
    G.fill_missing("bu qiymətləndirici üçün tətbiq olunmur / hesablanmayıb")
    rob = empty_rob()
    rob["null_reasons"] = {k: "bu qiymətləndirici üçün hesablanmayıb" for k in ("recursive", "loo_year_range",
                                                                                   "chow", "cusum_p")}
    if y is not None and len(y):
        yy = y.dropna()
        fv = o.get("fitted")
        fv = pd.Series(fv, index=yy.index) if fv is not None and not isinstance(fv, pd.Series) else fv
        fv = fv.reindex(yy.index) if fv is not None else (yy - pd.Series(resid, index=yy.index[-len(resid):])
                                                          if resid is not None else yy * np.nan)
        fitted = pack_fitted(yy.index, yy.to_numpy(float), fv.to_numpy(float))
        yrs = years_of(yy.index)
    else:
        fitted, yrs = dict(years=[], actual=[], fitted=[], resid=[]), [None]
    dfr = o.get("fit_df")
    num = [v for v in yrs if isinstance(v, (int, float))]
    return dict(names=names, roles={c: "const" if c == "const" else "regressor" for c in names},
                coef_rec=dict(fc), se_rec=dict(fs), dof=dfr, p_dist=o.get("p_dist") or ("t" if dfr else "normal"),
                sample=dict(start=int(min(num)) if num else None, end=int(max(num)) if num else None,
                            n=int(len(y.dropna())) if y is not None else None, k=len(names),
                            df_resid=int(dfr) if dfr is not None else None),
                cov_type=o.get("cov_label") or o["cov"], fit=fit, diagnostics=diag, robustness=rob,
                fitted=fitted, checks={"recomputed": False})
