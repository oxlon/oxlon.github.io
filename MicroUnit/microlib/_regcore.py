"""Internals shared by the registry builders: estimator families, DOLS augmentation (notebook naming),
empty diagnostic/fit/robustness templates with null reasons."""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from ._util import fnum, years_of
from .diagnostics import _try

AUG_RE = re.compile(r"^d_.+_(F\d+|L\d+|0\d*)$")


def family_of(estimator):
    e = (estimator or "").upper().replace(" ", "")
    if "DOLS" in e:
        return "dols"
    if e.startswith("2SLS") or e.startswith("IV") or e.startswith("TSLS"):
        return "iv"
    if e.startswith("FE") or "PANEL" in e or "WITHIN" in e or "TWOWAY" in e:
        return "panel"
    if "LOGIT" in e or "PROBIT" in e:
        return "logit"
    if "POISSON" in e:
        return "poisson"
    if e.startswith("OLS") or e in ("LS", "STATICOLS"):
        return "ols"
    return "other"


def dols_augment(X, leads=1, lags=1, det=()):
    """Stock-Watson DOLS augmentation with the notebooks' column names d_<x>_F1, d_<x>_00, d_<x>_L1."""
    aug = {}
    for c in [c for c in X.columns if c not in set(det) and c != "const"]:
        dx = X[c].diff()
        for L in range(-leads, lags + 1):
            aug[f'd_{c}_{"F" if L < 0 else "L" if L > 0 else "0"}{abs(L)}'] = dx.shift(L)
    return pd.concat([X, pd.DataFrame(aug, index=X.index)], axis=1)


def parse_leads_lags(v, estimator):
    if v is None:
        m = re.search(r"DOLS\(\s*(?:±|\+/-|\+-)?\s*(\d+)", estimator or "")
        if m:
            return int(m.group(1)), int(m.group(1))
        return None
    if isinstance(v, int):
        return v, v
    return int(v[0]), int(v[1])


def empty_fit():
    return dict(r2=None, r2_adj=None, ser=None, aic=None, bic=None, loglik=None, f_stat=None, f_p=None)


def empty_diag():
    return dict(dw=None, bg_lm_p=None, bg_lm_p_lag1=None, jb_p=None, white_p=None, bp_p=None, reset_p=None,
                vif_max=None, cond_number=None, eg_coint_p=None, eg_stat=None, eg_N=None, eg_trend=None,
                coint_established=None, diff_form=None)


def empty_rob():
    return dict(recursive=None, loo_year_range=None, chow=None, chow_tests=[], cusum_p=None, verdict=None,
                notes_az="")


class Nulls:
    """Collects (value, reason) results into a target dict and a `null_reasons` sub-dict."""

    def __init__(self, target):
        self.t = target
        self.t.setdefault("null_reasons", {})

    def put(self, key, vr):
        v, r = vr if isinstance(vr, tuple) else (vr, None)
        self.t[key] = fnum(v) if not isinstance(v, (dict, list, str, bool)) and v is not None else v
        if self.t[key] is None:
            self.t["null_reasons"][key] = r or "hesablanmayıb"
        else:
            self.t["null_reasons"].pop(key, None)

    def na(self, keys, reason):
        for k in keys:
            if self.t.get(k) is None:
                self.t[k] = None
                self.t["null_reasons"][k] = reason

    def fill_missing(self, reason):
        for k, v in list(self.t.items()):
            if k != "null_reasons" and v is None and k not in self.t["null_reasons"]:
                self.t["null_reasons"][k] = reason


def pack_fitted(index, actual, fitted, max_rows=3000, time=None):
    a = np.asarray(actual, float)
    f = np.asarray(fitted, float)
    yrs = years_of(index) if time is None else list(np.asarray(time).tolist())
    if len(a) > max_rows:  # large micro samples: store period means only
        df = pd.DataFrame({"t": yrs, "a": a, "f": f}).groupby("t").mean().sort_index()
        return dict(years=list(df.index), actual=df["a"].tolist(), fitted=df["f"].tolist(),
                    resid=(df["a"] - df["f"]).tolist(), aggregated="period means")
    return dict(years=yrs, actual=a.tolist(), fitted=f.tolist(), resid=(a - f).tolist())


def pack_robustness(rob, rec, lo, chow_list, cusum, names_keep):
    if rec is not None:
        rob["recursive"] = dict(years=rec["years"], n_min=rec.get("n_min"),
                                coef={c: rec["coef"][c] for c in names_keep if c in rec["coef"]},
                                se={c: rec["se"][c] for c in names_keep if c in rec["se"]})
        if not rec["years"]:
            rob["null_reasons"]["recursive"] = f"n < k+5 (minimum {rec.get('n_min')})"
    if lo is not None:
        rob["loo_year_range"] = {c: lo["range"][c] for c in names_keep if c in lo["range"]}
        rob["loo"] = dict(years=lo["years"], coef={c: lo["coef"][c] for c in names_keep if c in lo["coef"]})
    if chow_list is not None:
        rob["chow_tests"] = chow_list
        feas = [r for r in chow_list if r.get("p") is not None]
        if feas:
            rob["chow"] = min(feas, key=lambda r: r["p"])
        else:
            rob["chow"] = dict(break_year=None, f=None, p=None,
                               reason="; ".join(r.get("reason", "") for r in chow_list))
            rob["null_reasons"]["chow"] = "heç bir Chow testi mümkün deyil"
    if cusum is not None:
        rob["cusum_p"] = cusum.get("p")
        rob["cusum_stat"] = cusum.get("stat")
        if cusum.get("p") is None:
            rob["null_reasons"]["cusum_p"] = cusum.get("reason", "")
    return rob


def jb_dw(diag, u):
    from .diagnostics import dw, jb_p
    N = Nulls(diag)
    N.put("dw", dw(u))
    N.put("jb_p", jb_p(u))
    return N


__all__ = ["AUG_RE", "family_of", "dols_augment", "parse_leads_lags", "empty_fit", "empty_diag", "empty_rob",
           "Nulls", "pack_fitted", "pack_robustness", "jb_dw", "_try"]
