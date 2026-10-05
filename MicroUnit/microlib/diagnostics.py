"""Residual / specification diagnostics. Every test returns (value, reason): value is None when the
test is infeasible and `reason` says why (written to `null_reasons` in the registry)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.diagnostic import acorr_breusch_godfrey, het_breuschpagan, het_white, linear_reset
from statsmodels.tsa.adfvalues import mackinnonp
from statsmodels.tsa.stattools import adfuller

from .estimators import ols_np, t_inference


def _try(fn, *a, **k):
    try:
        v = fn(*a, **k)
        v = float(v)
        return (v, None) if np.isfinite(v) else (None, "nəticə sonlu deyil (non-finite)")
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"[:160]


def dw(u):
    u = np.asarray(u, float)
    if len(u) < 3:
        return None, "n < 3"
    return float(np.sum(np.diff(u) ** 2) / np.sum(u ** 2)), None


def bg_lm_p(res, nlags=2):
    """Breusch-Godfrey LM p-value (joint lags 1..nlags) from a statsmodels OLS results object."""
    n, k = res.model.exog.shape
    if n - k - nlags < 2:
        return None, f"n-k-{nlags} < 2"
    return _try(lambda: acorr_breusch_godfrey(res, nlags=nlags)[1])


def jb_p(u):
    u = np.asarray(u, float)
    if len(u) < 4:
        return None, "n < 4"
    return _try(lambda: stats.jarque_bera(u)[1])


def bp_fitted_p(u, fitted):
    """FR1 `register` variant: u^2 on a constant and the fitted values, nonrobust t-test p of the slope."""
    u = np.asarray(u, float)
    f = np.asarray(fitted, float)
    if len(u) < 5 or np.std(f) == 0:
        return None, "n < 5 və ya sabit qiymətləndirilmiş dəyər"
    r = ols_np(u ** 2, np.column_stack([np.ones(len(u)), f]), cov="nonrobust")
    return _try(lambda: t_inference(r["b"], r["se"], r["dof"], "t")[1][1])


def white_p(u, exog):
    exog = np.asarray(exog, float)
    n, k = exog.shape
    m = k * (k + 1) // 2
    if k < 2:
        return None, "izahedici dəyişən yoxdur"
    if n <= m + 1:
        return None, f"White köməkçi reqressiyası üçün n={n} ≤ {m + 1}"
    return _try(lambda: het_white(np.asarray(u, float), exog)[1])


def bp_p(u, exog):
    exog = np.asarray(exog, float)
    if exog.shape[1] < 2:
        return None, "izahedici dəyişən yoxdur"
    return _try(lambda: het_breuschpagan(np.asarray(u, float), exog)[1])


def reset_p(res, power=3):
    n, k = res.model.exog.shape
    if n - k - (power - 1) < 2:
        return None, "RESET üçün sərbəstlik dərəcəsi çatmır"
    return _try(lambda: linear_reset(res, power=power, test_type="fitted", use_f=True).pvalue)


def vif(Xdf):
    """Notebook convention: each regressor on the others WITH a constant; constant itself excluded."""
    Xd = Xdf.drop(columns=[c for c in Xdf.columns if c == "const"]).dropna()
    out = {}
    for c in Xd.columns:
        rest = Xd.drop(columns=c)
        if rest.shape[1] == 0:
            out[c] = 1.0
            continue
        yv = Xd[c].to_numpy(float)
        Z = np.column_stack([np.ones(len(Xd)), rest.to_numpy(float)])
        r = ols_np(yv, Z, cov="nonrobust")
        tss = ((yv - yv.mean()) ** 2).sum()
        r2 = 1 - (r["u"] @ r["u"]) / tss if tss > 0 else 1.0
        out[c] = np.inf if r2 >= 1 else 1 / (1 - r2)
    return pd.Series(out, dtype=float)


def vif_max(Xdf):
    v = vif(Xdf)
    if v.empty:
        return None, "izahedici dəyişən yoxdur"
    m = float(v.max())
    return (m, None) if np.isfinite(m) else (None, f"tam kollinearlıq ({v.idxmax()})")


def cond_number(Xdf):
    """Condition number of the standardised regressors (demeaned, unit variance, constant excluded) -
    the notebooks' definition; NOT statsmodels' `condition_number` (raw exog incl. constant)."""
    Xd = Xdf.drop(columns=[c for c in Xdf.columns if c == "const"]).dropna().to_numpy(float)
    if Xd.shape[1] < 2:
        return 1.0, None
    sd = Xd.std(axis=0)
    if np.any(sd == 0):
        return None, "sabit sütun var"
    s = np.linalg.svd((Xd - Xd.mean(axis=0)) / sd, compute_uv=False)
    return (float(s.max() / s.min()), None) if s.min() > 0 else (None, "tam kollinearlıq")


def is_trend_like(name, s):
    if "trend" in str(name).lower():
        return True
    v = pd.Series(s).dropna().to_numpy(float)
    if len(v) < 3:
        return False
    d = np.diff(v)
    nz = d[np.abs(d) > 1e-12]
    return len(nz) >= 2 and np.allclose(nz, nz[0]) and np.all(np.diff(v) * nz[0] >= -1e-12)


def is_dummy(s):
    v = pd.Series(s).dropna().unique()
    return len(v) <= 2 and set(np.round(v, 12)).issubset({0.0, 1.0})


def classify(Xdf, det=None):
    """-> (stochastic, deterministic, has_trend). `det` (names) overrides the automatic rule
    (name contains 'trend' / linear or broken-linear in time / 0-1 dummy / constant)."""
    cols = [c for c in Xdf.columns if c != "const"]
    if det is not None:
        dset = [c for c in cols if c in set(det)]
    else:
        dset = [c for c in cols if is_trend_like(c, Xdf[c]) or is_dummy(Xdf[c]) or Xdf[c].nunique() <= 1]
    trend = any(is_trend_like(c, Xdf[c]) for c in dset)
    return [c for c in cols if c not in dset], dset, trend


def eg_coint_p(resid, n_i1, trend=False):
    """Residual-based Engle-Granger p: ADF on residuals, no deterministics, maxlag 1, MacKinnon
    response surface with N = n_i1 + 1 (capped at 6), 'ct' if the relation has a trend.
    Returns dict(stat, p, N, regression) or (None, reason) via the `p` key."""
    u = np.asarray(pd.Series(resid).dropna(), float)
    reg = "ct" if trend else "c"
    if n_i1 < 1:
        return dict(stat=None, p=None, N=None, regression=reg, reason="I(1) izahedici dəyişən yoxdur")
    if len(u) < 8:
        return dict(stat=None, p=None, N=None, regression=reg, reason="n < 8")
    N = int(min(n_i1 + 1, 6))
    stat = float(adfuller(u, maxlag=1, regression="n", autolag=None)[0])
    p = float(mackinnonp(stat, regression=reg, N=N))
    note = None if n_i1 + 1 <= 6 else f"N={n_i1 + 1} > 6: MacKinnon cədvəli N=6 ilə məhdudlaşdırıldı"
    return dict(stat=stat, p=p, N=N, regression=reg, reason=note)


def diff_form(y, Xs, level_coef, cov="hac", level=0.95):
    """Same equation in first differences (constant absorbs the trend): dy on d(stochastic regressors).
    coherent = every level coefficient lies inside the difference-form CI."""
    if Xs.shape[1] == 0:
        return None, "stoxastik izahedici dəyişən yoxdur"
    d = pd.concat([y.diff().rename("__y__"), Xs.diff()], axis=1).dropna()
    n, k = len(d), Xs.shape[1] + 1
    if n - k < 3:
        return None, f"fərq formasında sərbəstlik dərəcəsi {n - k} < 3"
    Z = np.column_stack([np.ones(n), d[list(Xs.columns)].to_numpy(float)])
    r = ols_np(d["__y__"].to_numpy(float), Z, cov=cov)
    _, _, lo, hi = t_inference(r["b"], r["se"], r["dof"], "t", level)
    out = dict(coef={}, se={}, ci={}, level={}, outside=[], n=n, dof=r["dof"], hac_lags=r["lags"])
    for j, c in enumerate(Xs.columns, start=1):
        lv = level_coef.get(c, np.nan)
        out["coef"][c], out["se"][c] = float(r["b"][j]), float(r["se"][j])
        out["ci"][c] = [float(lo[j]), float(hi[j])]
        out["level"][c] = float(lv) if lv is not None else None
        if lv is not None and np.isfinite(lv) and not (lo[j] <= lv <= hi[j]):
            out["outside"].append(c)
    out["coherent"] = len(out["outside"]) == 0
    return out, None


def sm_fit_nonrobust(y, X):
    return sm.OLS(np.asarray(y, float), np.asarray(X, float)).fit()
