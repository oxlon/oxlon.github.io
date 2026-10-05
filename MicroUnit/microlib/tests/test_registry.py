"""Registry: OLS and DOLS (notebook lr_fit convention), coefficient assertion, JSON schema, AZ summary labels."""
import json
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.tsa.stattools import coint

from microlib.registry import EquationRegistry
from microlib.schema import validate_file, validate_registry

from ._harness import approx, check, raises, tmpdir
from .test_registry_dols import nb_lr_fit

YRS = np.arange(2000, 2026)
KW = dict(components=["fr1:rva_man"], subtask="C. Real sektor", title_az="Emal sənayesi", title_en="Manufacturing",
          dependent_label_az="ln real emal ƏDV")
LABELS = ["Asılı dəyişən", "əmsal", "standart xəta", "t-statistikası", "p-dəyəri", "etibarlılıq intervalı",
          "Müşahidələr", "Determinasiya əmsalı (R²)", "Düzəldilmiş R²", "qalıq", "Kointeqrasiya", "Dayanıqlıq",
          "avtokorrelyasiya", "heteroskedastiklik", "normallıq", "Durbin-Watson", "Struktur qırılma", "rekursiv",
          "Bir ili çıxarmaqla", "Hökm"]


def _data(seed=0, n=26):
    rng = np.random.default_rng(seed)
    k = np.cumsum(rng.normal(0.05, 0.1, n))
    l_ = np.cumsum(rng.normal(0.02, 0.1, n))
    y = 0.3 + 0.4 * k + 0.6 * l_ + rng.normal(0, 0.05, n)
    return pd.Series(y, YRS[:n], name="ln_rva_man"), pd.DataFrame({"ln_K": k, "ln_L": l_}, index=YRS[:n])


def _ols_reg():
    y, X = _data()
    res = sm.OLS(y, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": 2, "use_correction": True}, use_t=True)
    reg = EquationRegistry("FR1", "OBSERVED")
    e = reg.add("FR1.C3_man", y, X, estimator="OLS", cov="hac", fit_coef=res.params, fit_se=res.bse, **KW)
    return reg, e, res, y, X


def test_ols_coefficients_se_and_fit():
    reg, e, res, y, X = _ols_reg()
    c = {r["name"]: r for r in e["coefficients"]}
    approx([c[k]["coef"] for k in ("const", "ln_K", "ln_L")], res.params.values, rtol=1e-12, msg="coef")
    approx([c[k]["se_recomputed"] for k in ("const", "ln_K", "ln_L")], res.bse.values, rtol=1e-10, msg="HAC SE")
    approx([c[k]["p"] for k in ("const", "ln_K", "ln_L")], res.pvalues.values, rtol=1e-8, msg="t(n-k) p")
    check(e["checks"]["coef_match"] and e["checks"]["se_max_rel_diff"] < 1e-9, "checks")
    approx(e["fit"]["r2"], res.rsquared, rtol=1e-12)
    approx(e["fit"]["aic"], res.aic, rtol=1e-12)
    approx(e["fit"]["f_stat"], res.fvalue, rtol=1e-10, msg="HAC-Wald F as statsmodels")
    check(e["cov_type"] == "HAC(NW, L=2, small-sample n/(n-k))", e["cov_type"])
    check(e["sample"] == {"start": 2000, "end": 2025, "n": 26, "k": 3, "df_resid": 23}, str(e["sample"]))
    check(len(e["fitted"]["years"]) == 26 and abs(sum(e["fitted"]["resid"])) < 1e-8, "fitted series")
    rec = e["robustness"]["recursive"]
    check(len(rec["years"]) == 26 - 8 + 1 and rec["years"][0] == 2007, "recursive from n=k+5")
    check(e["robustness"]["verdict"] in ("stabil", "qismən stabil", "qeyri-stabil"), "verdict")


def test_eg_in_registry_matches_coint():
    y, X = _data(seed=4)
    reg = EquationRegistry("FR1")
    r = sm.OLS(y, sm.add_constant(X[["ln_K"]])).fit()
    e = reg.add("FR1.T", y, X[["ln_K"]], estimator="OLS", cov="hac", fit_coef=r.params, fit_se={}, **KW)
    approx(e["diagnostics"]["eg_coint_p"], coint(y, X[["ln_K"]], trend="c", maxlag=1, autolag=None)[1], rtol=1e-10)
    check(e["diagnostics"]["eg_N"] == 2 and e["diagnostics"]["eg_trend"] == "c", "N, trend")
    Xt = X[["ln_K"]].assign(trend=np.arange(26.0))
    r2 = sm.OLS(y, sm.add_constant(Xt)).fit()
    e2 = reg.add("FR1.T2", y, Xt, estimator="OLS", cov="hac", fit_coef=r2.params, fit_se={}, **KW)
    approx(e2["diagnostics"]["eg_coint_p"], coint(y, X[["ln_K"]], trend="ct", maxlag=1, autolag=None)[1], rtol=1e-10)
    check(e2["diagnostics"]["eg_trend"] == "ct" and e2["diagnostics"]["eg_N"] == 2, "trend -> ct, N excludes trend")


def test_coefficient_mismatch_raises():
    y, X = _data()
    r = sm.OLS(y, sm.add_constant(X)).fit()
    bad = r.params.copy()
    bad["ln_K"] *= 1.001
    reg = EquationRegistry("FR1")
    raises(AssertionError, reg.add, "FR1.bad", y, X, estimator="OLS", cov="hac", fit_coef=bad, fit_se=r.bse, **KW)
    raises(ValueError, reg.add, "FR3.x", y, X, estimator="OLS", cov="hac", fit_coef=r.params, fit_se=r.bse, **KW)


def test_fixed_restrictions_and_flags():
    y, X = _data()
    ys = y - 1.0 * X["ln_L"]
    r = sm.OLS(ys, sm.add_constant(X[["ln_K"]])).fit()
    reg = EquationRegistry("FR1")
    e = reg.add("FR1.R", ys, X[["ln_K"]], estimator="OLS", cov="hac", fit_coef=r.params, fit_se={}, fixed={"ln_L": 1.0},
                restrictions=[{"text_az": "ln_L əmsalı = 1", "test": "HAC-F", "stat": 0.5, "p": 0.48, "imposed": True}],
                used_in_forecast=False, coint=False, sign_expected={"ln_K": 1}, **KW)
    rows = {q["name"]: q for q in e["coefficients"]}
    check(rows["ln_L"]["fixed"] and rows["ln_L"]["se"] is None and rows["ln_L"]["coef"] == 1.0, "fixed row")
    check(all(q["used_value"] is None for q in e["coefficients"]), "not used in forecast")
    check(e["diagnostics"]["eg_coint_p"] is None and "eg_coint_p" in e["diagnostics"]["null_reasons"], "coint off")
    check(e["restrictions"][0]["imposed"] is True and rows["ln_K"]["sign_expected"] == 1, "restriction/sign")


def test_json_write_schema_and_nan():
    reg, e, *_ = _ols_reg()
    e["robustness"]["cusum_p"] = float("nan")  # must come out as null
    e["fit"]["aic"] = np.float64("inf")
    e["sample"]["n"] = np.int64(26)  # numpy types converted
    d = tmpdir()
    p = os.path.join(d, "FR1_equations.json")
    reg.write(p)
    txt = open(p, encoding="utf-8").read()
    check("NaN" not in txt and "Infinity" not in txt, "no NaN in JSON")
    js0 = json.loads(txt)["equations"][0]
    check(js0["robustness"]["cusum_p"] is None and js0["fit"]["aic"] is None and js0["sample"]["n"] == 26, "NaN->null")
    check(validate_file(p) == [], f"schema: {validate_file(p)}")
    js = json.loads(txt)
    check(js["module"] == "FR1" and js["data_mode"] == "OBSERVED" and "verdict_rule_az" in js, "header")
    bad = json.loads(txt)
    bad["equations"][0]["robustness"]["verdict"] = "stable"
    bad["equations"][0]["components"] = ["rva_man"]
    bad["equations"][0]["coefficients"][0]["se"] = "x"
    errs = validate_registry(bad)
    check(len(errs) >= 3, f"validator catches errors: {errs}")
    check(reg.validate() == [], "validate() clean")


def test_summary_text_labels():
    _, e, *_ = _ols_reg()
    s = e["summary_text"]
    miss = [lab for lab in LABELS if lab not in s]
    check(not miss, f"missing labels {miss}")
    check("FR1.C3_man" in s and "ln_K" in s, "id and regressors in summary")
    y, X = _data(seed=2)
    Xa, b_nb, se_nb, _ = nb_lr_fit(y, X)
    e2 = EquationRegistry("FR1").add("FR1.D", y, Xa, estimator="DOLS(±1)", cov="hac", fit_coef=b_nb, fit_se=se_nb, **KW)
    check("DOLS fərq (lead/lag)" in e2["summary_text"] and "Fərq forması" in e2["summary_text"], "DOLS notes")


def test_holdout_sample_years_extra():
    from microlib.robustness import holdout_metrics
    y, X = _data(seed=9)
    sub = (y.index >= 2005)
    r = sm.OLS(y[sub], sm.add_constant(X[sub])).fit()
    ho = holdout_metrics([2021, 2022], [1.0, 2.0], [1.1, 1.9], rw=[0.9, 0.9], const=[1.0, 1.5], cut=2020)
    e = EquationRegistry("FR1").add("FR1.H", y, X, estimator="OLS", cov="hac", fit_coef=r.params, fit_se={},
                                    sample_years=(2005, 2025), holdout=ho, extra={"spec": "test"}, **KW)
    check(e["sample"]["start"] == 2005 and e["sample"]["n"] == 21, str(e["sample"]))
    check(e["holdout"]["cut"] == 2020 and e["holdout"]["theil_u_rw"] is not None and e["extra"]["spec"] == "test", "ho")
    check("Nümunədən kənar yoxlama" in e["summary_text"], "holdout in summary")
