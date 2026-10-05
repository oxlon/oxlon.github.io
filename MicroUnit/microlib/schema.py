"""Schema check for FRx_equations.json (contract section A). validate_registry(d) -> list of error strings."""
from __future__ import annotations

import json
import math
import numbers

from ._util import ID_RE
from .glossary import VERDICTS

TOP = ("module", "generated", "data_mode", "equations")
EQ_KEYS = ("id", "module", "subtask", "components", "title_az", "title_en", "dependent", "estimator", "cov_type",
           "sample", "used_in_forecast", "restrictions", "coefficients", "fit", "diagnostics", "robustness",
           "holdout", "fitted", "summary_text", "notes_az", "synthetic")
COEF_KEYS = ("name", "label_az", "coef", "se", "t", "p", "ci_low", "ci_high", "fixed", "used_value", "editable")
FIT_KEYS = ("r2", "r2_adj", "ser", "aic", "bic", "loglik", "f_stat", "f_p")
DIAG_KEYS = ("dw", "bg_lm_p", "jb_p", "white_p", "reset_p", "vif_max", "cond_number", "eg_coint_p", "eg_trend",
             "coint_established", "diff_form")
ROB_KEYS = ("recursive", "loo_year_range", "chow", "cusum_p", "verdict", "notes_az")
SAMPLE_KEYS = ("start", "end", "n", "k", "df_resid")
HOLD_KEYS = ("cut", "years", "rmse", "theil_u_rw", "theil_u_const", "dm_p_rw")


def _num(v):
    return v is None or (isinstance(v, numbers.Real) and not isinstance(v, bool) and math.isfinite(v))


def _no_nan(o, path, errs):
    if isinstance(o, float) and not math.isfinite(o):
        errs.append(f"{path}: NaN/inf (must be null)")
    elif isinstance(o, dict):
        for k, v in o.items():
            _no_nan(v, f"{path}.{k}", errs)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            _no_nan(v, f"{path}[{i}]", errs)
    elif o is not None and not isinstance(o, (str, bool, int, float)):
        errs.append(f"{path}: non-JSON type {type(o).__name__}")


def _keys(d, keys, path, errs):
    if not isinstance(d, dict):
        errs.append(f"{path}: must be an object")
        return False
    for k in keys:
        if k not in d:
            errs.append(f"{path}: missing '{k}'")
    return True


def validate_eq(e, module, errs, p):
    if not _keys(e, EQ_KEYS, p, errs):
        return
    if not (isinstance(e["id"], str) and e["id"].startswith(module + ".")):
        errs.append(f"{p}.id must start with '{module}.'")
    if e["module"] != module:
        errs.append(f"{p}.module != {module}")
    if not isinstance(e["components"], list) or not all(isinstance(c, str) and ID_RE.match(c) and
                                                         c.startswith(module.lower() + ":")
                                                         for c in e["components"]):
        errs.append(f"{p}.components must be ids '{module.lower()}:<code>'")
    for k in ("subtask", "title_az", "title_en", "estimator", "cov_type", "summary_text", "notes_az"):
        if not isinstance(e.get(k), str):
            errs.append(f"{p}.{k} must be a string")
    if isinstance(e.get("summary_text"), str) and len(e["summary_text"]) < 50:
        errs.append(f"{p}.summary_text too short")
    if _keys(e["dependent"], ("code", "label_az", "label_en"), p + ".dependent", errs):
        pass
    if _keys(e["sample"], SAMPLE_KEYS, p + ".sample", errs):
        for k in ("n", "k", "df_resid"):
            v = e["sample"].get(k)
            if v is not None and not isinstance(v, int):
                errs.append(f"{p}.sample.{k} must be int")
    for k in ("used_in_forecast", "synthetic"):
        if not isinstance(e.get(k), bool):
            errs.append(f"{p}.{k} must be bool")
    if not isinstance(e["restrictions"], list):
        errs.append(f"{p}.restrictions must be a list")
    else:
        for i, r in enumerate(e["restrictions"]):
            _keys(r, ("text_az", "test", "stat", "p", "imposed"), f"{p}.restrictions[{i}]", errs)
    if not isinstance(e["coefficients"], list) or not e["coefficients"]:
        errs.append(f"{p}.coefficients must be a non-empty list")
    else:
        names = set()
        for i, c in enumerate(e["coefficients"]):
            q = f"{p}.coefficients[{i}]"
            if not _keys(c, COEF_KEYS, q, errs):
                continue
            if c["name"] in names:
                errs.append(f"{q}: duplicate name {c['name']}")
            names.add(c["name"])
            for k in ("coef", "se", "t", "p", "ci_low", "ci_high", "used_value"):
                if not _num(c.get(k)):
                    errs.append(f"{q}.{k} must be number|null")
            for k in ("fixed", "editable"):
                if not isinstance(c.get(k), bool):
                    errs.append(f"{q}.{k} must be bool")
    if _keys(e["fit"], FIT_KEYS, p + ".fit", errs):
        for k in FIT_KEYS:
            if not _num(e["fit"].get(k)):
                errs.append(f"{p}.fit.{k} must be number|null")
    if _keys(e["diagnostics"], DIAG_KEYS, p + ".diagnostics", errs):
        if e["diagnostics"].get("eg_trend") not in ("c", "ct", None):
            errs.append(f"{p}.diagnostics.eg_trend must be c|ct|null")
        df_ = e["diagnostics"].get("diff_form")
        if df_ is not None:
            _keys(df_, ("coef", "ci", "coherent"), p + ".diagnostics.diff_form", errs)
    if _keys(e["robustness"], ROB_KEYS, p + ".robustness", errs):
        if e["robustness"].get("verdict") not in VERDICTS:
            errs.append(f"{p}.robustness.verdict must be one of {VERDICTS}")
        rec = e["robustness"].get("recursive")
        if rec is not None and _keys(rec, ("years", "coef", "se"), p + ".robustness.recursive", errs):
            for c, v in rec["coef"].items():
                if len(v) != len(rec["years"]):
                    errs.append(f"{p}.robustness.recursive.coef.{c}: length mismatch")
    if e["holdout"] is not None:
        _keys(e["holdout"], HOLD_KEYS, p + ".holdout", errs)
    if _keys(e["fitted"], ("years", "actual", "fitted", "resid"), p + ".fitted", errs):
        lens = {k: len(e["fitted"][k]) for k in ("years", "actual", "fitted", "resid")}
        if len(set(lens.values())) != 1:
            errs.append(f"{p}.fitted: unequal lengths {lens}")


def validate_registry(d):
    errs = []
    if not _keys(d, TOP, "registry", errs):
        return errs
    if d["data_mode"] not in ("OBSERVED", "SYNTHETIC", "REAL"):
        errs.append("data_mode must be OBSERVED|SYNTHETIC|REAL")
    if not isinstance(d["equations"], list):
        return errs + ["equations must be a list"]
    ids = [e.get("id") for e in d["equations"] if isinstance(e, dict)]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        errs.append(f"duplicate equation ids: {sorted(dup)}")
    for i, e in enumerate(d["equations"]):
        validate_eq(e, d["module"], errs, f"equations[{i}]")
    _no_nan(d, "registry", errs)
    try:
        json.dumps(d, allow_nan=False, ensure_ascii=False)
    except (TypeError, ValueError) as ex:
        errs.append(f"not JSON-serialisable: {ex}")
    return errs


def validate_file(path):
    with open(path, encoding="utf-8") as fh:
        return validate_registry(json.load(fh))
