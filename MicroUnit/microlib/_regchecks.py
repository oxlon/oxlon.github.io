"""Registry internals: coefficient assertion against the recomputation, coefficient rows, restrictions."""
from __future__ import annotations

import warnings

import numpy as np

from ._util import close, rel_diff
from .estimators import t_inference
from .glossary import coef_label

STRICT_FAMILIES = ("ols", "dols", "iv", "panel")


def check_coefs(id, fam, core, fc, fs, fixed, tol, checks, strict=True, sink=None):
    rec, mism = core["coef_rec"], []
    for c, a in fc.items():
        if c in fixed:
            continue
        if c not in rec:
            if fam in STRICT_FAMILIES:
                mism.append(f"{c}: not a column of the recomputed regression")
            continue
        ok = close(a, rec[c], tol)
        if not ok and c == "const" and fam == "dols" and core.get("const_recentred") is not None:
            ok = close(a, core["const_recentred"], tol)
            checks["const_mode"] = "recentred (static levels residual mean zero)" if ok else None
        elif c == "const" and fam == "dols":
            checks["const_mode"] = "DOLS regression constant"
        if not ok:
            mism.append(f"{c}: notebook {a:.10g} vs statsmodels {rec[c]:.10g}")
    lr = [c for c, r in core["roles"].items() if r == "regressor"]
    missing = [c for c in lr if c not in fc]
    if missing:
        checks["warnings"].append(f"notebook did not report {missing}; recomputed values used")
    checks["coef_max_rel_diff"] = float(max([rel_diff(fc[c], rec[c]).item() for c in fc if c in rec
                                             and not (c == "const" and (checks.get("const_mode") or "").startswith("rec"))]
                                            or [0.0]))
    se_d = {c: rel_diff(fs[c], core["se_rec"][c]).item() for c in fs if c in core["se_rec"]
            and core["se_rec"][c] is not None}
    checks["se_max_rel_diff"] = float(max(se_d.values())) if se_d else None
    bad_se = [c for c, v in se_d.items() if v > max(tol, 1e-6)]
    if bad_se and fam != "other":
        checks["warnings"].append(f"SE differ from recomputed (> {tol:g}): {bad_se}")
    if mism:
        msg = f"{id}: coefficient check failed: " + "; ".join(mism)
        if fam in STRICT_FAMILIES and strict:
            raise AssertionError(msg)
        checks["warnings"].append(msg)
    checks["coef_match"] = not mism
    for w in checks["warnings"]:
        if sink is not None:
            sink.append(f"{id}: {w}")
        warnings.warn(f"{id}: {w}", stacklevel=3)


def build_rows(core, fc, fs, fp, fixed, used, editable, labels, signs, p_dist):
    dist = p_dist or core["p_dist"]
    dof = core["dof"]
    if dof is None:
        dist = "normal" if dist == "t" else dist
    names = list(core["names"])
    aug = [c for c in names if core["roles"].get(c) == "dols_aug"]
    order = [c for c in names if c not in aug] + [c for c in fixed if c not in names] + aug
    rows = []
    for c in order:
        role = "fixed" if c in fixed else core["roles"].get(c, "regressor")
        if role == "fixed":
            b, se = float(fixed[c]), None
            t = p = lo = hi = None
        else:
            b = fc.get(c, core["coef_rec"].get(c))
            se = fs.get(c, core["se_rec"].get(c))
            t, p, lo, hi = (None,) * 4
            if b is not None and se is not None and np.isfinite(se) and se > 0:
                t, p, lo, hi = [float(np.ravel(v)[0]) for v in t_inference([b], [se], dof, dist)]  # type: ignore[misc]
            if c in fp:
                p = fp[c]
        is_used = bool(used) and role in ("const", "regressor", "fixed")
        ed = (c in editable) if isinstance(editable, (list, tuple, set)) else (bool(used) and role in ("regressor", "fixed"))
        rows.append({"name": c, "label_az": coef_label(c, labels), "coef": b, "se": se, "t": t, "p": p,
                     "ci_low": lo, "ci_high": hi, "fixed": role == "fixed", "used_value": b if is_used else None,
                     "editable": bool(ed), "role": role, "sign_expected": signs.get(c),
                     "coef_recomputed": core["coef_rec"].get(c), "se_recomputed": core["se_rec"].get(c)})
    return rows


def norm_restrictions(restrictions):
    out = []
    for r in restrictions or []:
        r = dict(r)
        if "text_az" not in r:
            raise ValueError("each restriction needs 'text_az'")
        out.append({"text_az": r.pop("text_az"), "test": r.pop("test", None), "stat": r.pop("stat", None),
                    "p": r.pop("p", None), "imposed": bool(r.pop("imposed", False)), **r})
    return out
