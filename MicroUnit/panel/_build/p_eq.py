"""p_eq.py — equation registry → panel bundles.

data/eqidx.js   compact index of every equation of every module (strip under each component, Tənliklər index)
data/eq_frX.js  full regression output per module, loaded on demand (coefficient table, fit, diagnostics,
                restrictions, recursive / LOO / Chow / CUSUM, hold-out, fitted–actual–residual, summary text)
data/sens.js    coefficient tornado data per component (FRx_coef_sensitivity.csv, ±1 SE → % change in 2030)
Only displayed fields are kept; display strings pass through the az.csv translator.
"""
import json
import math

from . import pcore as C

MODS = ["FR1", "FR3", "FR4", "FR5", "FR10", "FR12"]


def r6(x):
    if isinstance(x, bool) or x is None:
        return x
    if isinstance(x, (int, float)):
        if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
            return None
        return float(f"{x:.6g}") if isinstance(x, float) else x
    if isinstance(x, list):
        return [r6(v) for v in x]
    if isinstance(x, dict):
        return {k: r6(v) for k, v in x.items()}
    return x


def load(mod):
    p = C.OUT / f"{mod}_equations.json"
    C.USED.add(p.name)
    return C.read_retry(p, reader=lambda q: json.loads(q.read_text(encoding="utf-8")))


def _num_or_reason(v, tr):
    return r6(v) if not isinstance(v, str) else {"x": tr(v)}


def full(e, tr):
    dg = e.get("diagnostics") or {}
    rb = e.get("robustness") or {}
    ho = e.get("holdout") or None
    fit = e.get("fit") or {}
    df = dg.get("diff_form") or None
    allow = sorted({c["name"] for c in e.get("coefficients", [])} | {e["dependent"].get("code", "")})
    o = {"id": e["id"], "f": e["module"], "st": tr(e.get("subtask")), "t": tr(e.get("title_az")),
         "dep": {"c": e["dependent"].get("code"), "l": tr(e["dependent"].get("label_az"))},
         "est": tr(e.get("estimator")), "cov": tr(e.get("cov_type")), "smp": r6(e.get("sample")),
         "used": bool(e.get("used_in_forecast")), "comp": e.get("components") or [], "syn": bool(e.get("synthetic")),
         "nt": tr(e.get("notes_az")), "sum": tr(e.get("summary_text")), "_allow": allow,
         "rs": [{"t": tr(r.get("text_az")), "test": tr(r.get("test")), "stat": r6(r.get("stat")), "p": r6(r.get("p")),
                 "imp": r.get("imposed")} for r in e.get("restrictions") or []],
         "co": [{"n": c["name"], "l": tr(c.get("label_az")), "c": r6(c.get("coef")), "se": r6(c.get("se")),
                 "t": r6(c.get("t")), "p": r6(c.get("p")), "lo": r6(c.get("ci_low")), "hi": r6(c.get("ci_high")),
                 "fx": bool(c.get("fixed")), "u": r6(c.get("used_value")), "ed": bool(c.get("editable")),
                 "r": c.get("role")} for c in e.get("coefficients") or []],
         "fit": {k2: _num_or_reason(fit.get(k1), tr) for k1, k2 in
                 (("r2", "r2"), ("r2_adj", "r2a"), ("ser", "ser"), ("aic", "aic"), ("bic", "bic"), ("loglik", "ll"),
                  ("f_stat", "F"), ("f_p", "Fp"), ("r2_levels", "r2l")) if k1 in fit},
         "dg": {k2: _num_or_reason(dg.get(k1), tr) for k1, k2 in
                (("dw", "dw"), ("bg_lm_p", "bg"), ("jb_p", "jb"), ("white_p", "wh"), ("bp_p", "bp"), ("reset_p", "reset"),
                 ("vif_max", "vif"), ("cond_number", "cond"), ("eg_coint_p", "egp"), ("eg_stat", "egs"), ("dw_levels", "dwl"))
                if k1 in dg}}
    if fit.get("f_type"):
        o["fit"]["Ft"] = tr(fit["f_type"])
    o["dg"]["egt"] = dg.get("eg_trend")
    o["dg"]["ce"] = dg.get("coint_established")
    if isinstance(df, dict):
        o["df"] = {"c": r6(df.get("coef")), "ci": r6(df.get("ci")), "lv": r6(df.get("level")),
                   "ok": df.get("coherent"), "out": df.get("outside")}
    rec = rb.get("recursive") or {}
    o["rb"] = {"v": rb.get("verdict"), "nt": tr(rb.get("notes_az")), "cusum": r6(rb.get("cusum_p")),
               "rec": r6({"y": rec.get("years"), "c": rec.get("coef"), "se": rec.get("se")}) if rec.get("years") else None,
               "loo": r6(rb.get("loo_year_range")),
               "chow": [{"y": c.get("break_year"), "l": tr(c.get("label")), "f": r6(c.get("f")), "p": r6(c.get("p")),
                         "x": tr(c.get("reason"))} for c in (rb.get("chow_tests") or ([rb["chow"]] if rb.get("chow") else []))]}
    if ho:
        o["ho"] = r6({"cut": ho.get("cut"), "y": ho.get("years"), "rmse": ho.get("rmse"), "urw": ho.get("theil_u_rw"),
                      "uc": ho.get("theil_u_const"), "dm": ho.get("dm_p_rw"), "dmc": ho.get("dm_p_const"),
                      "mae": ho.get("mae")})
        o["ho"]["md"] = tr(ho.get("mode_az"))
        o["ho"]["bm"] = tr(ho.get("benchmarks_az"))
        o["ho"]["un"] = tr(ho.get("units_az"))
    fv = e.get("fitted") or {}
    if fv.get("years"):
        o["fv"] = r6({"y": fv.get("years"), "a": fv.get("actual"), "f": fv.get("fitted"), "r": fv.get("resid")})
    return o


def index_row(o, rob):
    fit, dg, ho = o["fit"], o["dg"], o.get("ho") or {}
    num = lambda v: v if isinstance(v, (int, float)) else None    # noqa: E731
    row = {"id": o["id"], "f": o["f"], "st": o["st"], "t": o["t"], "est": o["est"], "used": o["used"], "comp": o["comp"],
           "v": o["rb"]["v"], "r2": num(fit.get("r2")), "r2a": num(fit.get("r2a")), "n": (o["smp"] or {}).get("n"),
           "dw": num(dg.get("dw")), "cp": num(dg.get("egp")), "ce": dg.get("ce"), "urw": ho.get("urw"), "uc": ho.get("uc"),
           "syn": o["syn"]}
    if rob:
        row["ft"] = rob
    return row


def sens_rows(mod, tr):
    p = C.OUT / f"{mod}_coef_sensitivity.csv"
    if not p.exists():
        return []
    s = C.csv(p.name)
    g = lambda r, *ks: next((r[k] for k in ks if k in r and r[k] == r[k]), None)   # noqa: E731
    out = []
    for r in s.to_dict("records"):
        if "type" in r and str(r.get("type")) != "coefficient":
            continue
        inp = g(r, "input", "coefficient")
        eq = g(r, "eq_id") or (str(inp).split("|")[0] if inp else None)
        name = g(r, "name") if "name" in r else (str(inp).split("|")[-1] if inp and "|" in str(inp) else g(r, "coefficient"))
        emin = g(r, "effect_minus_se_pct", "effect_minus_pct", "effect_low_pct", "effect_minus_1se_pct")
        epl = g(r, "effect_plus_se_pct", "effect_plus_pct", "effect_high_pct", "effect_plus_1se_pct")
        out.append({"comp": g(r, "component_id", "headline", "component"), "cl": tr(g(r, "component_label_az", "headline_label_az",
                    "component_az", "headline_az")), "eq": eq, "n": name, "l": tr(g(r, "label_az")),
                    "v": r6(g(r, "value", "coef_value")), "se": r6(g(r, "se", "coef_se")), "emin": r6(emin), "epl": r6(epl),
                    "base": r6(g(r, "baseline", "baseline_2030", "base_2030"))})
    return out


def build(data_dir, tr):
    idx, sens, hdr, scanobjs = [], {}, {}, []
    for m in MODS:
        d = load(m)
        rob = {}
        rp = C.OUT / f"{m}_robustness_summary.csv"
        if rp.exists():
            rs = C.csv(rp.name, dtype=str, keep_default_na=False)
            rob = {r["equation"]: tr(r.get("failed_tests_az") or "") for r in rs.to_dict("records")}
        fulls = [full(e, tr) for e in d["equations"]]
        idx += [index_row(o, rob.get(o["id"])) for o in fulls]
        hdr[m] = {"mode": d.get("data_mode"), "rule": tr(d.get("verdict_rule_az")), "conv": tr(d.get("conventions_az")),
                  "lb": d.get("layer_b_data_mode"), "n": len(fulls)}
        C.js_bundle(data_dir / f"eq_{m.lower()}.js", f"EQ_{m}", fulls)
        scanobjs.append((f"eq_{m.lower()}.js", fulls))
        for r in sens_rows(m, tr):
            c = r.pop("comp")
            if c:
                sens.setdefault(str(c), []).append(r)
    for k in sens:
        sens[k].sort(key=lambda r: -abs((r["epl"] or 0) - (r["emin"] or 0)))
    C.js_bundle(data_dir / "eqidx.js", "EQI", {"rows": idx, "hdr": hdr})
    C.js_bundle(data_dir / "sens.js", "SENS", sens)
    scanobjs += [("eqidx.js", idx), ("sens.js", sens)]
    return idx, hdr, scanobjs
