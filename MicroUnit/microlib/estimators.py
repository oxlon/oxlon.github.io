"""Estimators replicating the notebooks' conventions, plus the statsmodels cross-check.

Notebook conventions (FR1/FR3/FR4/FR5/FR10/FR12 `ols`/`hac_cov`):
  * HAC = Newey-West Bartlett, lags L = max(1, floor(4 (n/100)^(2/9))), sandwich scaled by n/(n-k);
  * p-values and CIs from t(n-k);
  * statsmodels equivalent: fit(cov_type='HAC', cov_kwds={'maxlags': L, 'use_correction': True}, use_t=True).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats


def hac_lags(n):
    return max(1, int(np.floor(4 * (n / 100) ** (2 / 9))))


def hac_cov(X, u, XtXi, lags=None, small=True):
    n, k = X.shape
    if lags is None:
        lags = hac_lags(n)
    Xu = X * u[:, None]
    S = Xu.T @ Xu
    for L in range(1, lags + 1):
        G = Xu[L:].T @ Xu[:-L]
        S += (1 - L / (lags + 1)) * (G + G.T)
    V = XtXi @ S @ XtXi
    return V * (n / max(n - k, 1)) if small else V


def parse_cov(cov):
    """'hac' | 'HAC' | 'HAC(L=2)' | 'hc1' | 'nonrobust' | other -> (kind, lags)."""
    c = (cov or "hac").strip()
    lo = c.lower()
    if lo.startswith("hac"):
        m = re.search(r"l\s*=\s*(\d+)", lo) or re.search(r"\((\d+)\)", lo)
        return "hac", (int(m.group(1)) if m else None)
    if lo in ("hc1", "hc0", "hc2", "hc3"):
        return lo, None
    if lo in ("nonrobust", "ols", "classical", "iid", "none"):
        return "nonrobust", None
    return "other", None


def cov_label(kind, lags=None, raw=None):
    if kind == "hac":
        return f"HAC(NW, L={lags}, small-sample n/(n-k))"
    if kind == "hc1":
        return "HC1"
    if kind == "nonrobust":
        return "nonrobust"
    return raw or kind


def ols_np(y, X, cov="hac", lags=None):
    """Plain-numpy OLS exactly as the notebooks compute it. y: (n,), X: (n,k) incl. constant column."""
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    n, k = X.shape
    XtXi = np.linalg.pinv(X.T @ X)
    b = XtXi @ X.T @ y
    u = y - X @ b
    dof = max(n - k, 1)
    kind, L0 = parse_cov(cov)
    L = lags if lags is not None else L0
    if kind == "hac":
        L = hac_lags(n) if L is None else L
        V = hac_cov(X, u, XtXi, L)
    elif kind == "hc1":
        V = XtXi @ ((X * u[:, None]).T @ (X * u[:, None])) @ XtXi * n / dof
    else:
        V = XtXi * (u @ u) / dof
    se = np.sqrt(np.maximum(np.diag(V), 0))
    return dict(b=b, se=se, V=V, u=u, n=n, k=k, dof=dof, lags=L if kind == "hac" else None)


def sm_ols(y, X, cov="hac", lags=None):
    """statsmodels OLS with the notebook convention applied. Returns (robust_results, nonrobust_results, L)."""
    kind, L0 = parse_cov(cov)
    mod = sm.OLS(np.asarray(y, float), np.asarray(X, float))
    base = mod.fit()
    L = lags if lags is not None else L0
    if kind == "hac":
        L = hac_lags(len(y)) if L is None else L
        res = mod.fit(cov_type="HAC", cov_kwds={"maxlags": int(L), "use_correction": True}, use_t=True)
    elif kind == "hc1":
        res = mod.fit(cov_type="HC1", use_t=True)
    else:
        res = base
        L = None
    return res, base, L


def t_inference(b, se, dof, dist="t", level=0.95):
    b = np.asarray(b, float)
    se = np.asarray(se, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = b / se
    if dist == "t":
        p = 2 * (1 - stats.t.cdf(np.abs(t), dof))
        q = stats.t.ppf(0.5 + level / 2, dof)
    else:
        p = 2 * (1 - stats.norm.cdf(np.abs(t)))
        q = stats.norm.ppf(0.5 + level / 2)
    return t, p, b - q * se, b + q * se


def tsls_np(y, W, I, cov="hac", lags=None):
    """2SLS as in the notebooks' `tsls`: W = [const, endog, exog], I = [const, exog, excluded Z].
    HAC is computed on the projected regressors Wh with the structural residual."""
    y = np.asarray(y, float)
    W = np.asarray(W, float)
    I = np.asarray(I, float)
    n, k = W.shape
    if I.shape[1] < k:
        raise ValueError(f"under-identified: {I.shape[1]} instruments for {k} parameters")
    PiI = np.linalg.pinv(I.T @ I)
    Wh = I @ (PiI @ (I.T @ W))
    b = np.linalg.pinv(Wh.T @ W) @ (Wh.T @ y)
    u = y - W @ b
    dof = max(n - k, 1)
    XtXi = np.linalg.pinv(Wh.T @ Wh)
    kind, L0 = parse_cov(cov)
    L = lags if lags is not None else L0
    if kind == "hac":
        L = hac_lags(n) if L is None else L
        V = hac_cov(Wh, u, XtXi, L)
    elif kind == "hc1":
        V = XtXi @ ((Wh * u[:, None]).T @ (Wh * u[:, None])) @ XtXi * n / dof
    else:
        V = XtXi * (u @ u) / dof
    over = I.shape[1] - k
    J = Jp = np.nan
    if over > 0:
        uh = I @ (PiI @ (I.T @ u))
        J = n * (uh @ uh) / (u @ u)
        Jp = 1 - stats.chi2.cdf(J, over)
    return dict(b=b, se=np.sqrt(np.maximum(np.diag(V), 0)), V=V, u=u, n=n, k=k, dof=dof,
                lags=L if kind == "hac" else None, sargan_J=J, sargan_p=Jp, overid=over)


def first_stage_F(E, Xx, Z):
    """Partial F of excluded instruments for each endogenous column (notebook convention)."""
    E = np.atleast_2d(np.asarray(E, float).T).T
    n = E.shape[0]
    one = np.ones((n, 1))
    X0 = np.column_stack([one, Xx]) if Xx.size else one
    I = np.column_stack([X0, Z])
    q = Z.shape[1]
    out = []
    for j in range(E.shape[1]):
        e = E[:, j]
        ru = e - I @ (np.linalg.pinv(I.T @ I) @ (I.T @ e))
        rr = e - X0 @ (np.linalg.pinv(X0.T @ X0) @ (X0.T @ e))
        den = (ru @ ru) / max(n - I.shape[1], 1)
        out.append(((rr @ rr - ru @ ru) / q) / den if den > 0 else np.nan)
    return out


def within(df, cols, entity, time, twoway=True):
    """Within transform used by the notebooks' panel_fe (two-way: x - x_i. - x_.t + x_..)."""
    d = df.copy()
    for c in cols:
        if twoway:
            d[c] = (d[c] - d.groupby(entity)[c].transform("mean")
                    - d.groupby(time)[c].transform("mean") + d[c].mean())
        else:
            d[c] = d[c] - d.groupby(entity)[c].transform("mean")
    return d


def panel_fe_dk(y, X, entity, time, twoway=True, dk_lags=None):
    """Two-way FE within estimator with Driscoll-Kraay SE (notebook FR1 `panel_fe` convention):
    DK lags floor(T^(1/4)), Bartlett, scaled n/(n-k) with k = regs + N + (T-1); inference t(T-1)."""
    regs = list(X.columns)
    df = pd.concat([y.rename("__y__"), X], axis=1)
    df["__e__"] = np.asarray(entity)
    df["__t__"] = np.asarray(time)
    df = df.dropna()
    d = within(df, ["__y__"] + regs, "__e__", "__t__", twoway)
    yv = d["__y__"].to_numpy(float)
    Xv = d[regs].to_numpy(float)
    XtXi = np.linalg.pinv(Xv.T @ Xv)
    b = XtXi @ Xv.T @ yv
    u = yv - Xv @ b
    nN, nT = d["__e__"].nunique(), d["__t__"].nunique()
    L = int(np.floor(nT ** 0.25)) if dk_lags is None else int(dk_lags)
    k = len(regs) + nN + (nT - 1 if twoway else 0)
    ht = (pd.DataFrame(Xv * u[:, None], index=d["__t__"].to_numpy()).groupby(level=0).sum()
          .sort_index().to_numpy())
    S = ht.T @ ht
    for l_ in range(1, L + 1):
        G = ht[l_:].T @ ht[:-l_]
        S += (1 - l_ / (L + 1)) * (G + G.T)
    V = XtXi @ S @ XtXi * (len(d) / max(len(d) - k, 1))
    r2 = 1 - (u @ u) / (yv @ yv) if yv @ yv > 0 else np.nan
    return dict(b=b, se=np.sqrt(np.maximum(np.diag(V), 0)), V=V, u=u, n=len(d), k=k, dof=max(nT - 1, 1),
                lags=L, nN=nN, nT=nT, r2=r2, Xw=Xv, yw=yv, time=d["__t__"].to_numpy(),
                index=d.index)
