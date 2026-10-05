"""Robustness: recursive / LOO shapes, Chow and CUSUM on known-break vs stable series, verdict rule."""
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.diagnostic import recursive_olsresiduals

from microlib import robustness as R
from microlib.estimators import ols_np

from ._harness import approx, check

YRS = np.arange(1990, 2030)  # 40 years


def _series(brk=None, seed=0, n=40, shift=1.5):
    rng = np.random.default_rng(seed)
    x = np.cumsum(rng.normal(size=n)) + 0.3 * np.arange(n)
    b = np.full(n, 0.5)
    if brk is not None:
        b = np.where(YRS[:n] >= brk, 0.5 + shift, 0.5)
    y = 1 + b * x + rng.normal(0, 0.4, n)
    return y, np.column_stack([np.ones(n), x])


def _fit_fn(y, X):
    return lambda m: (lambda r: (r["b"], r["se"]))(ols_np(y[m], X[m], "hac"))


def test_recursive_shapes():
    y, X = _series()
    n, k = X.shape
    rec = R.recursive(_fit_fn(y, X), YRS, ["const", "x"], n_min=k + 5)
    check(len(rec["years"]) == n - (k + 5) + 1, "number of windows = n-(k+5)+1")
    check(rec["years"][0] == YRS[k + 4] and rec["years"][-1] == YRS[-1], "window end years")
    check(all(len(rec["coef"][c]) == len(rec["years"]) == len(rec["se"][c]) for c in ("const", "x")), "lengths")
    approx(rec["coef"]["x"][-1], ols_np(y, X)["b"][1], rtol=1e-12, msg="last window = full sample")


def test_loo_shapes():
    y, X = _series()
    lo = R.loo(_fit_fn(y, X), YRS, ["const", "x"])
    full = ols_np(y, X)["b"][1]
    check(len(lo["years"]) == 40 and len(lo["coef"]["x"]) == 40, "one estimate per year")
    check(lo["range"]["x"][0] <= full <= lo["range"]["x"][1], "full-sample inside LOO range")


def test_chow_detects_known_break():
    y, X = _series(brk=2015, seed=1)
    r = R.chow_test(y, X, YRS, 2015)
    check(r["p"] is not None and r["p"] < 0.01, f"break detected p={r['p']}")
    y, X = _series(seed=1)
    r = R.chow_test(y, X, YRS, 2015)
    check(r["p"] > 0.05, f"stable not rejected p={r['p']:.3f}")
    r = R.chow_test(y[:12], X[:12], YRS[:12], 1999)
    check(r["p"] is None and "reason" in r, "infeasible -> null with reason")
    cs = R.chow_set(y, X, YRS, (2015, 2020))
    check([c["break_year"] for c in cs] == [2010, 2015, 2020], "midpoint, 2015, 2020")


def test_recursive_residuals_match_statsmodels():
    y, X = _series(seed=3)
    w = R.recursive_residuals(y, X)
    rr = recursive_olsresiduals(sm.OLS(y, X).fit(), skip=X.shape[1])
    approx(w, np.asarray(rr[4])[X.shape[1]:], rtol=1e-8, msg="recursive residuals")
    approx((w ** 2).sum(), sm.OLS(y, X).fit().ssr, rtol=1e-9, msg="sum w^2 = SSR")


def test_cusum_detects_break_not_stable():
    det = sum(R.cusum_test(*_series(brk=2010, seed=s, shift=1.0))["p"] < 0.05 for s in range(40))
    fp = sum(R.cusum_test(*_series(seed=100 + s))["p"] < 0.05 for s in range(40))
    check(det >= 32, f"CUSUM power on known break: {det}/40")
    check(fp <= 4, f"CUSUM false positives on stable series: {fp}/40")
    y, X = _series(brk=2010, seed=7, shift=1.5)
    check(R.cusum_test(y, X)["p"] < 0.05, "single known-break series detected")
    y, X = _series(seed=7)
    check(R.cusum_test(y, X)["p"] > 0.05, "single stable series not rejected")
    approx(R.cusum_p_from_stat(0.948), 0.05, rtol=2e-3, msg="BDE 5% constant")
    approx(R.cusum_p_from_stat(1.143), 0.01, rtol=5e-3, msg="BDE 1% constant")


def test_verdict_rule():
    rec = {"years": list(range(10)), "coef": {"x": [0.5] * 10}}
    lo = {"coef": {"x": [0.4, 0.6]}}
    ok = [{"p": 0.4}]
    check(R.verdict(rec, lo, ok, 0.5, ["x"], {"x": 0.5})[0] == "stabil", "stabil")
    late = {"years": list(range(10)), "coef": {"x": [0.5] * 8 + [-0.1, 0.5]}}
    check(R.verdict(late, lo, ok, 0.5, ["x"], {"x": 0.5})[0] == "qeyri-stabil", "late flip")
    check(R.verdict(rec, lo, [{"p": 0.005}], 0.5, ["x"], {"x": 0.5})[0] == "qeyri-stabil", "Chow p<0.01")
    early = {"years": list(range(10)), "coef": {"x": [-0.1] + [0.5] * 9}}
    check(R.verdict(early, lo, ok, 0.5, ["x"], {"x": 0.5})[0] == "qismən stabil", "early flip")
    check(R.verdict(rec, lo, [{"p": 0.03}], 0.5, ["x"], {"x": 0.5})[0] == "qismən stabil", "Chow 0.01<p<0.05")
    check(R.verdict(rec, {"coef": {"x": [-0.1, 0.6]}}, ok, 0.5, ["x"], {"x": 0.5})[0] == "qismən stabil", "LOO flip")
    check(R.verdict({"years": [], "coef": {"x": []}}, lo, ok, 0.5, ["x"], {"x": 0.5})[0] == "qismən stabil",
          "no recursive path cannot be stabil")


def test_holdout_metrics():
    a = np.array([1.0, 2, 3, 4, 5])
    h = R.holdout_metrics([2021, 2022, 2023, 2024, 2025], a, a + 0.1, rw=np.ones(5), const=a + 1, cut=2020)
    approx(h["rmse"], 0.1, rtol=1e-12)
    check(h["theil_u_rw"] < 1 and abs(h["theil_u_const"] - 0.1) < 1e-12 and 0 <= h["dm_p_rw"] <= 1, "holdout")
