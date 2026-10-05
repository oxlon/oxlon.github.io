"""Registry DOLS path, aligned with FR1 `dols` + `lr_fit` (re-centred constant, SE from the DOLS HAC V)."""
import numpy as np
import pandas as pd
from scipy import stats

from microlib.registry import EquationRegistry

from ._harness import approx, check

YRS = np.arange(2000, 2026)
KW = dict(components=["fr1:rva_man"], subtask="C. Real sektor", title_az="Emal sənayesi", title_en="Manufacturing",
          dependent_label_az="ln real emal ƏDV")


def _data(seed=0, n=26):
    rng = np.random.default_rng(seed)
    k = np.cumsum(rng.normal(0.05, 0.1, n))
    l_ = np.cumsum(rng.normal(0.02, 0.1, n))
    y = 0.3 + 0.4 * k + 0.6 * l_ + rng.normal(0, 0.05, n)
    return pd.Series(y, YRS[:n], name="ln_rva_man"), pd.DataFrame({"ln_K": k, "ln_L": l_}, index=YRS[:n])


def _hac(X, u, XtXi, lags=None):  # verbatim FR1 hac_cov
    n, k = X.shape
    if lags is None:
        lags = max(1, int(np.floor(4 * (n / 100) ** (2 / 9))))
    Xu = X * u[:, None]
    S = Xu.T @ Xu
    for L in range(1, lags + 1):
        G = Xu[L:].T @ Xu[:-L]
        S += (1 - L / (lags + 1)) * (G + G.T)
    return XtXi @ S @ XtXi * (n / max(n - k, 1))


def nb_lr_fit(y, X, L=1):
    """Replica of FR1 dols() + lr_fit(): long-run coefs, re-centred constant, SE from the DOLS HAC V."""
    aug = {}
    for c in X.columns:
        dx = X[c].diff()
        for j in range(-L, L + 1):
            aug[f'd_{c}_{"F" if j < 0 else "L" if j > 0 else "0"}{abs(j)}'] = dx.shift(j)
    Xa = pd.concat([X, pd.DataFrame(aug, index=X.index)], axis=1)
    d = pd.concat([y.rename("__y__"), Xa], axis=1).dropna()
    Z = np.column_stack([np.ones(len(d)), d.drop(columns="__y__").to_numpy(float)])
    XtXi = np.linalg.pinv(Z.T @ Z)
    b = XtXi @ Z.T @ d["__y__"].to_numpy(float)
    V = _hac(Z, d["__y__"].to_numpy(float) - Z @ b, XtXi)
    core = list(X.columns)
    b_lr = pd.Series(b[1:1 + len(core)], index=core)
    dl = pd.concat([y.rename("__y__"), X], axis=1).dropna()
    const = float((dl["__y__"] - dl[core] @ b_lr).mean())
    se = np.sqrt(np.diag(V))[: 1 + len(core)]
    return Xa, pd.Series([const, *b_lr], index=["const"] + core), pd.Series(se, index=["const"] + core), b[0]


def test_dols_notebook_convention():
    y, X = _data(seed=2)
    Xa, b_nb, se_nb, c_dols = nb_lr_fit(y, X)
    reg = EquationRegistry("FR1")
    e = reg.add("FR1.C3_man", y, Xa, estimator="DOLS(±1)", cov="hac", fit_coef=b_nb, fit_se=se_nb,
                dols_leads_lags=(1, 1), **KW)
    rows = {r["name"]: r for r in e["coefficients"]}
    check(e["checks"]["const_mode"].startswith("recentred"), "re-centred constant accepted")
    check(e["checks"]["se_max_rel_diff"] < 1e-9, "DOLS SE match")
    check(rows["d_ln_K_F1"]["used_value"] is None and not rows["d_ln_K_F1"]["editable"], "aug not used")
    check(rows["ln_K"]["used_value"] == b_nb["ln_K"] and rows["ln_K"]["editable"], "long-run used & editable")
    check(rows["const"]["used_value"] == b_nb["const"], "used const = re-centred")
    check(e["sample"]["n"] == 23 and e["sample"]["n_levels"] == 26 and e["sample"]["k"] == 9, str(e["sample"]))
    check(len(e["fitted"]["years"]) == 26 and abs(np.mean(e["fitted"]["resid"])) < 1e-10, "levels residual mean 0")
    lv = np.asarray(e["fitted"]["resid"])
    approx(e["diagnostics"]["dw_levels"], np.sum(np.diff(lv) ** 2) / np.sum(lv ** 2), rtol=1e-10, msg="DW levels")
    approx(e["diagnostics"]["jb_p_levels"], stats.jarque_bera(lv)[1], rtol=1e-10, msg="JB levels")
    check(e["diagnostics"]["eg_resid"] == "static levels residual" and e["diagnostics"]["eg_N"] == 3, "EG on levels")
    check(e["robustness"]["stability_form"].startswith("static"), "Chow on static levels form")
    check(set(e["robustness"]["recursive"]["coef"]) == {"const", "ln_K", "ln_L"}, "recursive LR only")
    # auto augmentation from levels X gives the same answer
    e2 = reg.add("FR1.C3_auto", y, X, estimator="DOLS(±1)", cov="hac", fit_coef=b_nb, fit_se=se_nb, **KW)
    approx([r["coef_recomputed"] for r in e2["coefficients"]], [r["coef_recomputed"] for r in e["coefficients"]],
           rtol=1e-12, msg="auto-augmented DOLS")
