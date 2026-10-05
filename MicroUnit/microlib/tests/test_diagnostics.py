"""Diagnostics: MacKinnon residual cointegration p vs statsmodels coint, DW/JB/BG/VIF/cond, classification."""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson, jarque_bera
from statsmodels.tsa.adfvalues import mackinnonp
from statsmodels.tsa.stattools import adfuller, coint

from microlib import diagnostics as D

from ._harness import approx, check


def _coint_data(n=40, k=1, seed=11):
    rng = np.random.default_rng(seed)
    X = np.cumsum(rng.normal(size=(n, k)), axis=0)
    y = 0.5 + X @ np.linspace(0.8, -0.4, k) + rng.normal(0, 0.4, n)
    return y, X


def _eg_from_ols(y, X, trend=False):
    Z = np.column_stack([np.ones(len(y)), X] + ([np.arange(len(y), dtype=float)] if trend else []))
    u = sm.OLS(y, Z).fit().resid
    return D.eg_coint_p(u, X.shape[1], trend)


def test_mackinnon_matches_coint_one_regressor_c():
    """one I(1) regressor, constant -> MacKinnon N = 2, 'c' (statsmodels coint's k_vars)."""
    y, X = _coint_data(k=1)
    eg = _eg_from_ols(y, X)
    st, p, _ = coint(y, X, trend="c", maxlag=1, autolag=None)
    check(eg["N"] == 2 and eg["regression"] == "c", "N = n_i1 + 1")
    approx(eg["stat"], st, rtol=1e-10, msg="ADF stat")
    approx(eg["p"], p, rtol=1e-10, msg="MacKinnon p (N=2,'c')")


def test_mackinnon_matches_coint_two_regressors_and_trend():
    y, X = _coint_data(k=2, seed=12)
    eg = _eg_from_ols(y, X)
    approx(eg["p"], coint(y, X, trend="c", maxlag=1, autolag=None)[1], rtol=1e-10, msg="N=3 'c'")
    y, X = _coint_data(k=1, seed=13)
    y = y + 0.05 * np.arange(len(y))
    eg = _eg_from_ols(y, X, trend=True)
    check(eg["regression"] == "ct", "trend -> 'ct'")
    approx(eg["p"], coint(y, X, trend="ct", maxlag=1, autolag=None)[1], rtol=1e-10, msg="N=2 'ct'")


def test_mackinnon_N1_case():
    """N=1 'c' surface = the plain ADF(c) distribution used by adfuller; with no I(1) regressor the
    registry reports null (EG not applicable)."""
    rng = np.random.default_rng(4)
    s = np.cumsum(rng.normal(size=50))
    r = adfuller(s, maxlag=1, regression="c", autolag=None)
    approx(mackinnonp(r[0], regression="c", N=1), r[1], rtol=1e-12, msg="N=1 'c'")
    e = D.eg_coint_p(s - s.mean(), 0, False)
    check(e["p"] is None and "I(1)" in e["reason"], "n_i1=0 -> null with reason")


def test_eg_detects_and_rejects():
    y, X = _coint_data(k=1, n=60)
    check(_eg_from_ols(y, X)["p"] < 0.05, "cointegrated pair detected")
    rng = np.random.default_rng(99)
    y2 = np.cumsum(rng.normal(size=60))
    check(_eg_from_ols(y2, X)["p"] > 0.10, "independent random walks not cointegrated")


def test_dw_jb_bg_vs_statsmodels():
    y, X = _coint_data(k=2, seed=21)
    Z = sm.add_constant(X)
    res = sm.OLS(y, Z).fit()
    u = res.resid
    approx(D.dw(u)[0], durbin_watson(u), rtol=1e-12, msg="DW")
    approx(D.jb_p(u)[0], jarque_bera(u)[1], rtol=1e-10, msg="JB p")
    from statsmodels.stats.diagnostic import acorr_breusch_godfrey
    approx(D.bg_lm_p(res, 2)[0], acorr_breusch_godfrey(res, nlags=2)[1], rtol=1e-12, msg="BG")
    check(D.white_p(u[:6], Z[:6])[0] is None, "White infeasible for tiny n -> null")
    check(D.reset_p(res)[0] is not None, "RESET computed")


def test_vif_and_condition_number():
    rng = np.random.default_rng(2)
    n = 50
    a = rng.normal(size=n)
    b = 0.9 * a + 0.3 * rng.normal(size=n)
    c = rng.normal(size=n)
    Xdf = pd.DataFrame({"a": a, "b": b, "c": c})
    v = D.vif(Xdf)
    ex = sm.add_constant(Xdf.to_numpy())
    approx(v.to_numpy(), [variance_inflation_factor(ex, i) for i in (1, 2, 3)], rtol=1e-9, msg="VIF")
    q, _ = np.linalg.qr(rng.normal(size=(n, 3)))
    q = q - q.mean(axis=0)
    q, _ = np.linalg.qr(q)
    cn = D.cond_number(pd.DataFrame(q / q.std(axis=0)))[0]
    check(cn < 1.05, f"orthogonal standardized -> cond ~ 1 ({cn:.3f})")
    check(D.cond_number(Xdf)[0] > cn, "collinear -> larger cond")


def test_classify_deterministics():
    yrs = np.arange(2000, 2026)
    X = pd.DataFrame({"lnk": np.log(np.arange(1, 27) + np.random.default_rng(0).random(26)), "trend": yrs - 1999.0,
                      "tr15": np.maximum(0, yrs - 2015.0), "d2020": (yrs == 2020).astype(float)}, index=yrs)
    st, de, tr = D.classify(X)
    check(st == ["lnk"] and set(de) == {"trend", "tr15", "d2020"} and tr, f"classify {st} {de} {tr}")
    st, de, tr = D.classify(X[["lnk", "d2020"]])
    check(not tr and de == ["d2020"], "dummy is deterministic but not a trend")


def test_diff_form_coherence():
    rng = np.random.default_rng(8)
    n = 60
    x = np.cumsum(rng.normal(size=n))
    y = 1 + 0.8 * x + rng.normal(0, 0.2, n)
    yi, Xs = pd.Series(y), pd.DataFrame({"x": x})
    out, _ = D.diff_form(yi, Xs, {"x": 0.8})
    check(out["coherent"] and out["ci"]["x"][0] < 0.8 < out["ci"]["x"][1], "true level inside diff CI")
    out2, _ = D.diff_form(yi, Xs, {"x": 3.0})
    check(not out2["coherent"] and out2["outside"] == ["x"], "far level flagged")
