"""p_synecon.py — Layer-B firm-level econometrics (FR10_SYNTHETIC_econ_*, FR12_SYNTHETIC_econ_*) → data/synecon.js.

Model cards, coefficient tables, marginal effects, ROC / calibration, survival curves, cohorts, Boone slopes and
parameter-recovery tables. When the modules run on REAL files the same tables are named *_FIRM_econ_*; the
bundle then switches its labelling (mode REAL) automatically.
"""
from . import pcore as C


def _f(x):
    return C.fnum(x)


def _pick(stem10):
    """Return (prefix, mode): REAL outputs (FRx_FIRM_econ_*) win over the synthetic ones."""
    real = stem10.replace("SYNTHETIC", "FIRM")
    if (C.OUT / f"{real}models.csv").exists() or (C.OUT / f"{real}summary.csv").exists():
        return real, "REAL"
    return stem10, "SYNTHETIC"


def _rows(name, cols, tr, txt=()):
    if not (C.OUT / name).exists():
        return []
    d = C.csv(name)
    out = []
    for r in d.to_dict("records"):
        o = {}
        for c in cols:
            if c not in r:
                continue
            v = r[c]
            o[c] = tr(v) if c in txt and isinstance(v, str) else (v if isinstance(v, str) else _f(v))
        out.append(o)
    return out


def _fr10(tr):
    p, mode = _pick("FR10_SYNTHETIC_econ_")
    T = ("title_az", "estimator", "r2_type", "term_az", "interpretation_az", "note_az", "scope_az", "rule_az", "block", "sample")
    models = _rows(f"{p}models.csv", ["model_id", "block", "title_az", "estimator", "dependent", "regressors", "n_obs", "n_firms",
                                     "n_clusters", "year_min", "year_max", "r2", "r2_type", "r2_adj", "ser", "wald_F", "wald_F_p",
                                     "loglik", "lr_chi2", "lr_p", "aic", "bic", "auc", "brier", "hosmer_lemeshow",
                                     "hosmer_lemeshow_p", "event_rate", "auc_oos", "brier_oos", "RTS"], tr, T)
    coef = {}
    for r in _rows(f"{p}coefficients.csv", ["model_id", "term", "term_az", "coef", "se", "t", "p", "ci_low", "ci_high"], tr, T):
        coef.setdefault(r.pop("model_id"), []).append(r)
    interp = {r["model_id"]: r.get("interpretation_az", "") for r in _rows(f"{p}interpretation_az.csv", ["model_id", "interpretation_az"], tr, T)}
    roc = {}
    for k in ("distress", "export"):
        rs = _rows(f"{p}{k}_roc.csv", ["fpr", "tpr", "sample"], tr, T)
        by = {}
        for r in rs:
            by.setdefault(r.get("sample") or "in-sample", {"fpr": [], "tpr": []})
            by[r.get("sample") or "in-sample"]["fpr"].append(r["fpr"])
            by[r.get("sample") or "in-sample"]["tpr"].append(r["tpr"])
        roc[k] = by
    return {"mode": mode, "models": models, "coef": coef, "interp": interp, "roc": roc,
            "ame": {k: _rows(f"{p}{k}_ame.csv", ["term", "term_az", "ame", "se", "z", "p", "ci_low", "ci_high"], tr, T)
                    for k in ("distress", "export")},
            "cal": {k: _rows(f"{p}{k}_calibration.csv", ["decile", "n", "mean_predicted", "observed_rate", "sample"], tr, T)
                    for k in ("distress", "export")},
            "pf": _rows(f"{p}production_function.csv", ["model_id", "RTS", "se", "ci_low", "ci_high", "crs_wald_F", "crs_p", "df"], tr, T),
            "rec": _rows(f"{p}recovery.csv", ["model_id", "term", "term_az", "true", "estimate", "se", "ci_low", "ci_high", "covered",
                                              "bias", "bias_in_se", "note_az"], tr, T),
            "mc": _rows(f"{p}recovery_mc.csv", ["model_id", "term", "term_az", "true", "mean_estimate", "mc_sd", "mean_se",
                                                "coverage_95", "reps", "bias", "bias_t", "se_ratio", "consistent_estimator"], tr, T),
            "rules": _rows(f"{p}sample_rules.csv", ["scope_az", "rule_az"], tr, T)}


def _fr12(tr):
    p, mode = _pick("FR12_SYNTHETIC_econ_")
    T = ("model_az", "term_az", "interpretation_az", "cov_type", "term_type", "why_no_true_parameter_az", "block", "ratio_type")
    cc = ["model", "model_az", "term", "term_az", "coef", "se", "z", "p", "ci_low", "ci_high", "ratio_type", "n", "cov_type",
          "ratio", "ratio_ci_low", "ratio_ci_high", "term_type"]
    coef = {}
    for r in _rows(f"{p}coefficients.csv", cc, tr, T):
        coef.setdefault(r["model"], []).append(r)
    return {"mode": mode, "summary": _rows(f"{p}summary.csv", ["model", "model_az", "n", "interpretation_az"], tr, T), "coef": coef,
            "entry": _rows(f"{p}entry_irr.csv", cc, tr, T), "exit": _rows(f"{p}exit_hazard.csv", cc, tr, T),
            "surv": _rows(f"{p}survival.csv", ["cohort", "age", "km_survival", "cohort_size", "pred_logit", "pred_cloglog"], tr, T),
            "coh": _rows(f"{p}cohorts.csv", ["cohort", "age", "enterprises", "mean_rel_size", "survivor_share"], tr, T),
            "boone": _rows(f"{p}boone_sector_year.csv", ["section", "year", "pcm_pct", "boone_beta", "boone_se", "ci_low", "ci_high"], tr, T),
            "rec": _rows(f"{p}recovery.csv", ["block", "parameter", "true", "estimate", "se", "ci_low", "ci_high", "covered", "error"], tr, T),
            "nodef": _rows(f"{p}recovery_not_defined.csv", ["model", "why_no_true_parameter_az"], tr, T + ("model",))}


def build(data_dir, tr, hdr):
    d = {"FR10": _fr10(tr), "FR12": _fr12(tr)}
    for m in ("FR10", "FR12"):
        lb = (hdr.get(m) or {}).get("lb")
        if lb:
            d[m]["mode"] = "REAL" if str(lb).upper().startswith("REAL") else d[m]["mode"]
    C.js_bundle(data_dir / "synecon.js", "SYNE", d)
    return d
