"""EquationRegistry: one per module -> ROOT/output/FRx_equations.json (contract section A).

The notebook passes its OWN estimates (fit_coef / fit_se); the registry re-estimates the same equation
independently with statsmodels on the same (y, X), asserts the coefficients agree (rel. 1e-6) and adds the
diagnostics, robustness checks and the Azerbaijani summary text.
"""
from __future__ import annotations

import json
import os
import pandas as pd

from . import robustness as R
from ._reg_glm import build_glm, build_other
from ._reg_ols import build_ols
from ._reg_other import build_iv, build_panel
from ._regcore import dols_augment, family_of, parse_leads_lags  # noqa: F401  (dols_augment re-exported)
from ._regchecks import build_rows, check_coefs, norm_restrictions
from ._util import as_dict, as_frame, as_series, now_iso, to_jsonable
from .glossary import CONVENTIONS_AZ, VERDICT_RULE_AZ, VERDICT_RULE_EN
from .schema import HOLD_KEYS, validate_eq, validate_registry
from .summary import build_summary

BUILDERS = {"ols": build_ols, "dols": build_ols, "iv": build_iv, "panel": build_panel, "logit": build_glm,
            "poisson": build_glm, "other": build_other}


class EquationRegistry:
    def __init__(self, module, data_mode="OBSERVED", *, strict=True, verbose=False):
        if data_mode not in ("OBSERVED", "SYNTHETIC", "REAL"):
            raise ValueError("data_mode must be OBSERVED|SYNTHETIC|REAL")
        self.module, self.data_mode = module.upper(), data_mode
        self.strict, self.verbose = strict, verbose
        self.equations, self.warnings = [], []

    # ------------------------------------------------------------------ add
    def add(self, id, y, X, *, estimator, cov, fit_coef, fit_se, components, subtask, title_az, title_en,
            dependent_label_az, coef_labels_az=None, used_in_forecast=True, restrictions=None, holdout=None,
            fixed=None, notes_az="", dols_leads_lags=None, trend=False, sample_years=None, extra=None,
            dependent_code=None, dependent_label_en=None, fit_p=None, fit_df=None, p_dist=None, results=None,
            levels=None, lr_names=None, det=None, n_i1=None, coint="auto", diff_spec=None, iv=None, panel=None,
            time_index=None, hac_lags=None, editable=None, sign_expected=None, chow_breaks=(2015, 2020),
            tol=1e-6, resid=None, fitted=None, synthetic=None, add_const=True, cov_label=None):
        if not str(id).startswith(self.module + "."):
            raise ValueError(f"equation id '{id}' must start with '{self.module}.'")
        if any(e["id"] == id for e in self.equations):
            raise ValueError(f"duplicate equation id '{id}'")
        y = as_series(y) if y is not None else None
        X = as_frame(X, y.index if y is not None else None) if X is not None else None
        fam = family_of(estimator)
        fc, fs, fp = as_dict(fit_coef), as_dict(fit_se), as_dict(fit_p)
        fixed = as_dict(fixed)
        o = dict(family=fam, cov=cov, hac_lags=hac_lags, add_const=add_const, lr_names=lr_names, levels=levels,
                 det=det, n_i1=n_i1, coint=coint, trend=trend, diff_spec=diff_spec, chow_breaks=chow_breaks,
                 fit_coef=fc, fit_se=fs, leads_lags=parse_leads_lags(dols_leads_lags, estimator),
                 sample_years=sample_years, iv=iv, panel=panel, time_index=time_index, results=results,
                 resid=resid, fitted=fitted, fit_df=fit_df, p_dist=p_dist, cov_label=cov_label)
        core = BUILDERS[fam](y, X, o)
        checks = dict(core.get("checks") or {}, family=fam, warnings=[])
        check_coefs(id, fam, core, fc, fs, fixed, tol, checks, self.strict, self.warnings)
        rows = build_rows(core, fc, fs, fp, fixed, used_in_forecast, editable, coef_labels_az or {},
                          sign_expected or {}, p_dist)
        rob = core["robustness"]
        used = [r["name"] for r in rows if r["role"] == "regressor"]
        if rob.get("recursive") is None and rob.get("loo") is None and fam == "other":
            rob["verdict"], rob["notes_az"] = "qismən stabil", "dayanıqlıq testləri bu qiymətləndirici üçün aparılmayıb"
        else:
            rob["verdict"], rob["notes_az"] = R.verdict(rob.get("recursive"), rob.get("loo"), rob.get("chow_tests"),
                                                        rob.get("cusum_p"), used, {r["name"]: r["coef"] for r in rows})
        hold = None if holdout is None else {k: holdout.get(k) for k in HOLD_KEYS} | dict(holdout)
        eq = {"id": id, "module": self.module, "subtask": subtask, "components": list(components),
              "title_az": title_az, "title_en": title_en,
              "dependent": {"code": dependent_code or (y.name if y is not None and y.name else id.split(".", 1)[1]),
                            "label_az": dependent_label_az, "label_en": dependent_label_en or title_en},
              "estimator": estimator, "cov_type": core["cov_type"], "sample": core["sample"],
              "used_in_forecast": bool(used_in_forecast), "restrictions": norm_restrictions(restrictions),
              "coefficients": rows, "fit": core["fit"], "diagnostics": core["diagnostics"], "robustness": rob,
              "holdout": hold, "fitted": core["fitted"], "summary_text": "", "notes_az": notes_az or "",
              "synthetic": bool(self.data_mode == "SYNTHETIC" if synthetic is None else synthetic),
              "checks": checks}
        if extra:
            eq["extra"] = extra
        eq = to_jsonable(eq)
        eq["summary_text"] = build_summary(eq)
        errs = []
        validate_eq(eq, self.module, errs, id)
        if errs:
            raise ValueError("registry schema errors: " + "; ".join(errs[:8]))
        self.equations.append(eq)
        if self.verbose:
            print(eq["summary_text"])
        return eq

    # ---------------------------------------------------------------- output
    def to_dict(self):
        return {"module": self.module, "generated": now_iso(), "data_mode": self.data_mode, "schema_version": "2.0",
                "verdict_rule_az": VERDICT_RULE_AZ, "verdict_rule_en": VERDICT_RULE_EN,
                "conventions_az": CONVENTIONS_AZ, "equations": self.equations}

    def validate(self, raise_=True):
        errs = validate_registry(to_jsonable(self.to_dict()))
        if errs and raise_:
            raise ValueError(f"{len(errs)} schema errors: " + "; ".join(errs[:10]))
        return errs

    def write(self, path):
        d = to_jsonable(self.to_dict())
        errs = validate_registry(d)
        if errs:
            raise ValueError(f"{len(errs)} schema errors, not written: " + "; ".join(errs[:10]))
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        tmp = str(path) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False, indent=1, allow_nan=False)
        os.replace(tmp, path)
        return path

    def get(self, id):
        return next(e for e in self.equations if e["id"] == id)

    def summary(self, id):
        return self.get(id)["summary_text"]

    def table(self):
        return pd.DataFrame([{"id": e["id"], "estimator": e["estimator"], "n": e["sample"]["n"],
                              "used": e["used_in_forecast"], "r2": e["fit"]["r2"],
                              "eg_p": e["diagnostics"].get("eg_coint_p"), "verdict": e["robustness"]["verdict"],
                              "coef_match": e["checks"].get("coef_match")} for e in self.equations])

    def __len__(self):
        return len(self.equations)
