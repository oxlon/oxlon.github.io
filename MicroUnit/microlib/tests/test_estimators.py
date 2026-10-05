"""Estimators: known-answer coefficients, HAC vs statsmodels (with the notebook scaling), p-values, 2SLS, FE."""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from microlib.estimators import hac_cov, hac_lags, ols_np, panel_fe_dk, sm_ols, t_inference, tsls_np

from ._harness import approx, check


def _data(n=30, seed=0):
    rng = np.random.default_rng(seed)
    x1 = np.cumsum(rng.normal(size=n))
    x2 = rng.normal(size=n)
    e = np.zeros(n)
    for t in range(1, n):  # serially correlated errors so HAC matters
        e[t] = 0.6 * e[t - 1] + rng.normal(0, 0.3)
    X = np.column_stack([np.ones(n), x1, x2])
    return X, X @ np.array([1.0, 0.7, -0.4]) + e


def test_lag_rule():
    check(hac_lags(26) == 2 and hac_lags(10) == 2 and hac_lags(100) == 4 and hac_lags(5) == 2, "lag rule")
    check(hac_lags(3) == 1 and hac_lags(1) == 1, "small n")


def test_coefficients_exact_noise_free():
    X, _ = _data()
    y = X @ np.array([2.5, -1.25, 0.125])
    r = ols_np(y, X)
    approx(r["b"], [2.5, -1.25, 0.125], rtol=1e-10, atol=1e-10, msg="noise-free OLS")


def test_coefficients_vs_statsmodels():
    X, y = _data()
    res, base, L = sm_ols(y, X, "hac")
    approx(ols_np(y, X)["b"], res.params, rtol=1e-10, msg="OLS b")
    approx(res.params, base.params, rtol=1e-12, msg="cov type does not change b")


def test_hac_matches_statsmodels_with_scaling():
    X, y = _data(n=26)
    n, k = X.shape
    L = hac_lags(n)
    r = ols_np(y, X, "hac")
    sm_res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": L, "use_correction": True}, use_t=True)
    approx(r["se"], sm_res.bse, rtol=1e-10, msg="HAC SE with n/(n-k)")
    sm_raw = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": L})  # statsmodels default: no correction
    approx(r["se"], sm_raw.bse * np.sqrt(n / (n - k)), rtol=1e-10, msg="scaling factor is exactly n/(n-k)")
    # manual Bartlett check
    XtXi = np.linalg.inv(X.T @ X)
    approx(hac_cov(X, r["u"], XtXi, L), sm_res.cov_params(), rtol=1e-10, msg="HAC matrix")


def test_pvalues_t_distribution():
    X, y = _data(n=26)
    r = ols_np(y, X, "hac")
    t, p, lo, hi = t_inference(r["b"], r["se"], r["dof"], "t")
    sm_res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags(26), "use_correction": True}, use_t=True)
    approx(p, sm_res.pvalues, rtol=1e-8, msg="t(n-k) p-values")
    ci = sm_res.conf_int()
    approx(lo, ci[:, 0], rtol=1e-8, msg="CI low")
    approx(hi, ci[:, 1], rtol=1e-8, msg="CI high")
    pz = 2 * (1 - stats.norm.cdf(np.abs(t)))
    check(np.all(p >= pz - 1e-12), "t p-values are >= normal p-values")


def test_hc1_and_nonrobust():
    X, y = _data()
    approx(ols_np(y, X, "hc1")["se"], sm.OLS(y, X).fit(cov_type="HC1").bse, rtol=1e-10, msg="HC1")
    approx(ols_np(y, X, "nonrobust")["se"], sm.OLS(y, X).fit().bse, rtol=1e-10, msg="nonrobust")


def test_tsls_known_answer():
    rng = np.random.default_rng(3)
    n = 400
    z1, z2 = rng.normal(size=n), rng.normal(size=n)
    v = rng.normal(size=n)
    xe = 0.8 * z1 + 0.5 * z2 + v
    u = 0.7 * v + rng.normal(0, 0.5, n)  # endogeneity
    y = 1 + 2 * xe + u
    W = np.column_stack([np.ones(n), xe])
    I = np.column_stack([np.ones(n), z1, z2])
    r = tsls_np(y, W, I, "nonrobust")
    Pz = I @ np.linalg.pinv(I.T @ I) @ I.T
    b_manual = np.linalg.solve(W.T @ Pz @ W, W.T @ Pz @ y)
    approx(r["b"], b_manual, rtol=1e-10, msg="2SLS formula")
    check(abs(r["b"][1] - 2) < 0.15, f"2SLS consistent ({r['b'][1]:.3f})")
    check(abs(ols_np(y, W)["b"][1] - 2) > abs(r["b"][1] - 2), "OLS biased relative to 2SLS")


def test_panel_fe_equals_lsdv():
    rng = np.random.default_rng(5)
    N, T = 6, 12
    ent = np.repeat(np.arange(N), T)
    tim = np.tile(np.arange(2010, 2010 + T), N)
    x = rng.normal(size=N * T) + ent * 0.3
    y = 0.5 * x + ent * 1.0 + (tim - 2010) * 0.1 + rng.normal(0, 0.2, N * T)
    idx = pd.MultiIndex.from_arrays([ent, tim], names=["unit", "year"])
    r = panel_fe_dk(pd.Series(y, idx), pd.DataFrame({"x": x}, idx), ent, tim, twoway=True)
    D = pd.get_dummies(pd.DataFrame({"e": ent.astype(str), "t": tim.astype(str)}), drop_first=True).astype(float)
    lsdv = sm.OLS(y, np.column_stack([np.ones(N * T), x, D.to_numpy()])).fit()
    approx(r["b"][0], lsdv.params[1], rtol=1e-9, msg="two-way within == LSDV")
    check(r["dof"] == T - 1 and r["lags"] == int(np.floor(T ** 0.25)), "DK conventions")
