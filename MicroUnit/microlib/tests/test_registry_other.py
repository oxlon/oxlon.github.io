"""Registry with non-OLS estimators: logit, poisson, 2SLS, FE panel, precomputed 'other'."""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from microlib.registry import EquationRegistry
from microlib.estimators import panel_fe_dk, tsls_np

from ._harness import approx, check, raises

KW = dict(components=["fr4:emp:agr"], subtask="T", title_az="Test", title_en="Test", dependent_label_az="y")


def test_logit_refit_and_results_object():
    rng = np.random.default_rng(1)
    n = 300
    yrs = np.repeat(np.arange(2010, 2025), 20)
    x = rng.normal(size=n)
    y = (rng.random(n) < 1 / (1 + np.exp(-(-0.3 + 1.2 * x)))).astype(float)
    X = pd.DataFrame({"x": x})
    res = sm.Logit(y, sm.add_constant(X)).fit(disp=0)
    reg = EquationRegistry("FR4")
    e = reg.add("FR4.L1", pd.Series(y), X, estimator="logit", cov="MLE", fit_coef=res.params, fit_se=res.bse,
                time_index=yrs, **KW)
    rows = {r["name"]: r for r in e["coefficients"]}
    approx(rows["x"]["p"], res.pvalues["x"], rtol=1e-6, msg="normal p-values for logit")
    check(e["fit"]["r2_adj"] is None and "r2_adj" in e["fit"]["null_reasons"], "r2_adj null with reason")
    check(e["diagnostics"]["dw"] is None and "dw" in e["diagnostics"]["null_reasons"], "DW null for logit")
    check(len(e["robustness"]["recursive"]["years"]) > 0, "recursive by year for logit")
    e2 = reg.add("FR4.L2", pd.Series(y), X, estimator="logit", cov="MLE", fit_coef=res.params, fit_se=res.bse,
                 results=res, **KW)
    approx(e2["fit"]["loglik"], res.llf, rtol=1e-12)
    check(reg.validate() == [], "schema")


def test_poisson():
    rng = np.random.default_rng(2)
    n = 200
    x = rng.normal(size=n)
    y = rng.poisson(np.exp(0.5 + 0.4 * x)).astype(float)
    X = pd.DataFrame({"x": x}, index=np.arange(n))
    res = sm.Poisson(y, sm.add_constant(X)).fit(disp=0)
    e = EquationRegistry("FR4").add("FR4.P", pd.Series(y), X, estimator="poisson", cov="MLE", fit_coef=res.params,
                                    fit_se=res.bse, **KW)
    check(e["checks"]["coef_match"], "poisson refit matches")
    check(e["robustness"]["verdict"] in ("stabil", "qismən stabil", "qeyri-stabil"), "verdict present")


def test_2sls():
    rng = np.random.default_rng(3)
    n = 40
    yrs = np.arange(1986, 1986 + n)
    z = rng.normal(size=(n, 2))
    v = rng.normal(size=n)
    xe = z @ [0.8, 0.5] + v
    w = rng.normal(size=n)
    y = 1 + 2 * xe - 0.5 * w + 0.7 * v + rng.normal(0, 0.5, n)
    X = pd.DataFrame({"xe": xe, "w": w}, index=yrs)
    Z = pd.DataFrame(z, index=yrs, columns=["z1", "z2"])
    W = np.column_stack([np.ones(n), xe, w])
    I = np.column_stack([np.ones(n), w, z])
    nb = tsls_np(y, W, I, "hac")
    e = EquationRegistry("FR1").add("FR1.IV", pd.Series(y, yrs), X, estimator="2SLS", cov="hac",
                                    fit_coef=dict(zip(["const", "xe", "w"], nb["b"])),
                                    fit_se=dict(zip(["const", "xe", "w"], nb["se"])), iv={"endog": ["xe"], "Z": Z},
                                    components=["fr1:x"], subtask="T", title_az="T", title_en="T", dependent_label_az="y")
    check(e["checks"]["coef_match"] and e["checks"]["se_max_rel_diff"] < 1e-10, "2SLS recomputed")
    check(e["diagnostics"]["first_stage_F"]["xe"] > 10 and e["diagnostics"]["sargan_p"] is not None, "IV extras")
    check(e["diagnostics"]["bg_lm_p"] is None and e["robustness"]["chow"] is None, "OLS-only tests null")


def test_fe_panel():
    rng = np.random.default_rng(5)
    N, T = 8, 10
    ent = np.repeat(np.arange(N), T)
    tim = np.tile(np.arange(2014, 2014 + T), N)
    x = rng.normal(size=N * T)
    y = 0.6 * x + ent * 0.5 + rng.normal(0, 0.3, N * T)
    idx = pd.MultiIndex.from_arrays([ent, tim], names=["unit", "year"])
    ys, X = pd.Series(y, idx), pd.DataFrame({"x": x}, idx)
    r = panel_fe_dk(ys, X, ent, tim)
    e = EquationRegistry("FR3").add("FR3.FE", ys, X, estimator="FE-twoway", cov="DK", fit_coef={"x": r["b"][0]},
                                    fit_se={"x": r["se"][0]}, panel={"entity": "unit", "time": "year"},
                                    components=["fr3:x"], subtask="T", title_az="T", title_en="T",
                                    dependent_label_az="y")
    check(e["checks"]["coef_match"] and e["sample"]["df_resid"] == T - 1, "FE + t(T-1)")
    check(len(e["robustness"]["loo"]["years"]) == T, "LOO by year in panel")
    check(e["diagnostics"]["eg_coint_p"] is None, "no EG in panel")


def test_other_precomputed():
    yrs = np.arange(2005, 2026)
    rng = np.random.default_rng(6)
    y = pd.Series(rng.normal(size=21), yrs)
    resid = pd.Series(rng.normal(0, 0.1, 21), yrs)
    e = EquationRegistry("FR5").add("FR5.SUR1", y, None, estimator="SUR", cov="SUR-GLS",
                                    fit_coef={"const": 0.1, "p_food": -0.3}, fit_se={"const": 0.05, "p_food": 0.1},
                                    resid=resid, components=["fr5:vol:food"], subtask="T", title_az="T",
                                    title_en="T", dependent_label_az="y")
    rows = {r["name"]: r for r in e["coefficients"]}
    check(rows["p_food"]["p"] is not None and e["diagnostics"]["dw"] is not None, "normal p + DW from resid")
    check(e["robustness"]["verdict"] == "qismən stabil", "verdict for untested estimator")
    raises(ValueError, EquationRegistry, "FR5", "WRONG")
