"""FR4 scenario engine — employment by 19 activities (two bases), 8 groups, services blocs, state/non-state,
budget/non-budget, oil/non-oil, labour force and the employee share, 2025 (nowcast) and 2026-2030.

Re-implements the notebook's forecast solve (FR4.ipynb Part 15 `drivers`/`oil_parts`/`allocate`/`industry_split`,
Part 17 `institutions`, `own_total`) on the exported state (output/engine/FR4_state.json + .npz).

    inputs()                                  editable catalogue (exogenous FR1 paths, coefficients, levers)
    run(overrides, scenario, upstream=None)   {"series": {fr4:<id>: {year: v}}, "meta", "warnings"}
    selftest()                                run({}) per scenario reproduces the notebook CSVs (rel. 1e-8)

upstream = {"FR1": result} (from engines.fr1.run) replaces the FR1 CSV paths: series fr1:emp, fr1:lf, fr1:pop,
fr1:rgdpnon, fr1:rgdpoil, fr1:rva_*. FR3 is not used by the FR4 forecast (only by a Part 19 consistency check).
Levers: pop_growth_pp, phi_delta_2030_pp, state_share_mode (trend|frozen), budget_definition (sigma|kappa),
budget_ratio, addfactor_decay. Coefficients: "FR4.E4_pooled_emp|d_lo_sq", "FR4.E4_combo|w_pooled", ...
"""
from __future__ import annotations

import os
import time

import numpy as np
import pandas as pd

from . import base as B

MODULE = "FR4"
_S = None


def _st():
    global _S
    if _S is None:
        _S = B.load_state(MODULE)
    return _S


def reload():
    """Drop the cached state (after the notebook re-exports it)."""
    global _S
    _S = None
    return _st()


def inputs():
    return _st()["inputs"]


def _out_dir():
    from .. import project_root
    return os.path.join(project_root(), "output")


# ------------------------------------------------------------------ upstream + overrides
def _resolve(overrides, scenario, upstream):
    """Exogenous paths (FR1 CSV baseline, or the upstream FR1 engine result) with the user's overrides on top."""
    S, W, meta_up = _st(), [], {}
    cat = inputs()
    if upstream and upstream.get("FR1"):
        ser = upstream["FR1"].get("series", {})
        cat = dict(cat)
        exo = []
        for e in cat["exogenous"]:
            e = dict(e)
            d = ser.get(e["id"])
            vals = [None if d is None else d.get(str(y), d.get(y)) for y in e["years"]]
            if d is None or any(v is None for v in vals):
                W.append(f"FR1 yuxarı axınında '{e['id']}' tam deyil — FR1 CSV baza yolu istifadə olunur")
            else:
                e["baseline"] = dict(e["baseline"], **{scenario: [float(v) for v in vals]})
                meta_up[e["id"]] = "FR1 mühərriki"
            exo.append(e)
        cat["exogenous"] = exo
    if upstream and upstream.get("FR3"):
        meta_up["FR3"] = "istifadə olunmur (FR4 proqnozu FR3-dən asılı deyil)"
    ov = B.apply_overrides(cat, overrides, scenario)
    ov["warnings"] = W + ov["warnings"]
    ov["upstream"] = meta_up
    return ov


def _lev(ov, k):
    return ov["levers"].get(k)


def _coef(ov, key):
    return float(ov["coefficients"][key])


# ------------------------------------------------------------------ the solve (notebook Part 15/17)
def _drivers(S, exo, scale, b9):
    """notebook `drivers` + `oil_parts`: 2025 from FR1 history, 2026-2030 from the exogenous paths."""
    K, H, yrs, fcy = S["keys"], S["hist2025"], S["meta"]["years"], S["meta"]["fc_years"]
    g8v, la = S["g8_var"], S["meta"]["last_act"]
    q8 = pd.DataFrame(index=yrs, columns=K["g8"], dtype=float)
    qi = pd.DataFrame(index=yrs, columns=K["ind"], dtype=float)
    for k in K["g8"]:
        q8.at[la, k] = H["rind"] if k == "industry" else H[g8v[k]]
    for k, v in S["ind_var"].items():
        qi.at[la, k] = H[v]
    for i, y in enumerate(fcy):
        src = {v: float(exo["fr1:" + v][i]) for v in S["exo_vars"]}
        for k in K["g8"]:
            q8.at[y, k] = (float(np.sum(np.array([src[c] for c in ("rva_min", "rva_man", "rva_elc", "rva_wat")])))
                           * S["ind_ratio"] if k == "industry" else src[g8v[k]])
        for k, v in S["ind_var"].items():
            qi.at[y, k] = src[v]
    ser = lambda v, h: pd.Series([h] + [float(x) for x in exo["fr1:" + v]], index=yrs)  # noqa: E731
    emp, lf = ser("emp", H["emp"]) * scale, ser("lf", H["lf"]) * scale
    pop = ser("pop", H["pop"]) * scale
    rgo = ser("rgdpoil", H["rgdpoil"])
    O = S["oil"]
    om, rf = {la: O["om25"]}, {la: O["rf25"]}
    for y in fcy:
        g = float(np.exp(b9 * (np.log(rgo.loc[y]) - np.log(O["rgdpoil25"]))))
        om[y], rf[y] = om[la] * g, rf[la] * g
    return dict(q8=q8, qi=qi, oth=ser("rva_oth", H["rva_oth"]), rgdpnon=ser("rgdpnon", H["rgdpnon"]), rgdpoil=rgo,
                emp=emp, lf=lf, pop=pop, oil_min=pd.Series(om), refin=pd.Series(rf))


def _softmax(z):
    e = np.exp(z)
    return e.div(e.sum(axis=1), axis=0)


def _tier1(Bs, dr, years, w):
    """pred_tier: (1-w) x constant shares + w x pooled output-share system, both anchored on 2024."""
    K = _st()["keys"]
    sq = dr["q8"].loc[years, K["g8"]].div(dr["q8"].loc[years, K["g8"]].sum(axis=1), axis=0)
    zc, zo = {}, {}
    for k in K["g8"]:
        if k == "services":
            zc[k] = zo[k] = pd.Series(0.0, index=years)
            continue
        lo_sq = np.log(sq[k] / sq["services"])
        addf = float(Bs["z_anchor"][k] - Bs["beta1"] * Bs["lo_sq_anchor"][k])
        zc[k] = (Bs["z_anchor"][k] + 0.0 + 0.0) * pd.Series(1.0, index=years)
        zo[k] = (0.0 + addf + Bs["beta1"] * lo_sq) * pd.Series(1.0, index=years)
    sC = _softmax(pd.DataFrame(zc, index=years)[K["g8"]])
    sO = _softmax(pd.DataFrame(zo, index=years)[K["g8"]])
    if w == 0.5:
        return 0.5 * sC + 0.5 * sO
    return (1.0 - w) * sC + w * sO


def _industry(Bs, dr, years, ind_lvl, w):
    """industry_split with the oil carve-out: oil parts follow E9, the non-oil rest is shared out."""
    IND = _st()["keys"]["ind"]
    yy = list(years)
    om, rf = dr["oil_min"].reindex(yy).to_numpy(float), dr["refin"].reindex(yy).to_numpy(float)
    rest = ind_lvl.to_numpy(float) - om - rf
    qi = dr["qi"]
    lq = {"mining": np.log(qi.loc[yy, ["manuf", "elec", "water"]].sum(axis=1)), "manuf": np.log(qi.loc[yy, "manuf"]),
          "elec": np.log(qi.loc[yy, "elec"]), "water": np.log(qi.loc[yy, "water"])}
    A, Q = Bs["indA"], Bs["indQ"]
    za = {k: np.log(A[k] / A["manuf"]) for k in IND}
    zc = pd.DataFrame({k: za[k] + 0.0 * lq[k].to_numpy() for k in IND}, index=yy)
    zo = pd.DataFrame({k: za[k] + Bs["beta2"] * ((lq[k].to_numpy() - Q[k]) - (lq["manuf"].to_numpy() - Q["manuf"]))
                       for k in IND}, index=yy)
    sh = 0.5 * _softmax(zc) + 0.5 * _softmax(zo) if w == 0.5 else (1.0 - w) * _softmax(zc) + w * _softmax(zo)
    out = sh.mul(rest, axis=0)
    out["mining"] += om
    out["manuf"] += rf
    return out


def _allocate(Bs, dr, years, total, w1, w2, decay):
    """allocate: 8 groups -> industry (4) and other services (two blocs, 9 activities); sums to the total."""
    K = _st()["keys"]
    s8 = _tier1(Bs, dr, years, w1)
    lvl8 = s8.mul(pd.Series(total, index=years), axis=0)
    out = pd.DataFrame(index=years, dtype=float)
    for g in ["agr", "constr", "trade", "hotel", "transp", "ict"]:
        out[g] = lvl8[g]
    ind = _industry(Bs, dr, years, lvl8["industry"], w2)
    for k in K["ind"]:
        out[k] = ind[k]
    yy = np.asarray(years, float)
    dfac = np.power(Bs["rho6"], np.maximum(yy - Bs["anchor6"], 0)) if decay else 1.0
    addf6 = Bs["lhs6"] - (Bs["c6"] + Bs["b6"] * np.log(Bs["oth6"]))
    ratio = np.exp(Bs["c6"] + Bs["b6"] * np.log(dr["oth"].reindex(years).to_numpy(float)) + addf6 * dfac)
    pub = lvl8["services"] / (1 + ratio)
    mkt = lvl8["services"] - pub
    for keys, a, c, lvl in [(K["pub"], Bs["aP"], Bs["cP"], pub), (K["mkt"], Bs["aM"], Bs["cM"], mkt)]:
        z = pd.DataFrame({k: a[k] + c[k] * (yy - Bs["by"]) for k in keys}, index=years)
        e = np.exp(z)
        sh = e.div(e.sum(axis=1), axis=0)
        for k in keys:
            out[k] = sh[k] * lvl
    out = out[K["act"]]
    out["total"] = out.sum(axis=1)
    gap = float((out["total"] / pd.Series(total, index=years) - 1).abs().max())
    assert gap < 1e-9, f"allocation does not sum to the total ({gap:.2e})"
    return out


def _institutions(S, dr, tot, hir, Hfr, ov, decay):
    """institutions: state/non-state (E8), budget (sigma x 4 budget activities), oil on both bases (E9)."""
    yrs, ld, la, C, E8 = S["meta"]["years"], S["meta"]["last_dsk"], S["meta"]["last_act"], S["calib"], S["e8"]
    trf = pd.Series({y: y - E8["base"] for y in yrs})
    b8 = {"const": E8["const"], "trend": _coef(ov, "FR4.E8_state|trend")}
    add8 = float(np.log(E8["state24"] / E8["nonstate24"]) - (b8["const"] + b8["trend"] * (ld - E8["base"])))
    f8 = pd.Series({y: (E8["rho"] ** (y - ld) if decay else 1.0) for y in yrs})
    od = np.exp(b8["const"] + b8["trend"] * trf + add8 * f8)
    state = tot * od / (1 + od) if _lev(ov, "state_share_mode") != "frozen" else tot * C["state_share24"]
    out = pd.DataFrame({"employed, total": tot, "labour force (FR1)": dr["lf"], "state": state, "non-state": tot - state})
    out["state share, %"] = out.state / out["employed, total"] * 100
    out["hired, total"] = hir
    sig = _lev(ov, "budget_ratio")
    if sig is None or (isinstance(sig, float) and not np.isfinite(sig)):
        sig = C["kappa"] if _lev(ov, "budget_definition") == "kappa" else C["sigma"]
    out["budget organisations"] = float(sig) * Hfr[S["keys"]["pub"]].sum(axis=1)
    out["non-budget"] = hir - out["budget organisations"]
    out["budget share of hired, %"] = out["budget organisations"] / hir * 100
    b9 = _coef(ov, "FR4.E9_oil|ln_rgdpoil")
    ext = np.exp(b9 * (np.log(dr["rgdpoil"].reindex(yrs)) - np.log(S["oil"]["rgdpoil25"])))
    out["oil, statistical basis"] = C["oil_stat_anchor"] * ext
    out["non-oil, statistical basis (hired)"] = hir - out["oil, statistical basis"]
    out["employment contracts, tax-record basis"] = C["dvx_contracts25"] * hir / float(hir.loc[la])
    out["oil, tax-record basis"] = C["dvx_oil_anchor"] * ext
    out["non-oil, tax-record basis"] = out["employment contracts, tax-record basis"] - out["oil, tax-record basis"]
    return out


def _own_total(S, dr):
    """own_total: FR4's own aggregate block (E1 participation x population, E2 employment rate) - cross-check."""
    yrs, E2 = S["meta"]["years"], S["e2"]
    lf = dr["pop"].reindex(yrs) * S["calib"]["part"]
    add2 = float(np.log(E2["emp25"] / E2["lf25"]) - (E2["const"] + E2["ln_rgdpnon"] * np.log(E2["rgdpnon25"]) + E2["trend"] * E2["tr25"]))
    trf = pd.Series({y: y - 2000. for y in yrs})
    er = np.exp(E2["const"] + E2["ln_rgdpnon"] * np.log(dr["rgdpnon"].reindex(yrs)) + E2["trend"] * trf + add2)
    return lf * er, lf


# ------------------------------------------------------------------ public API
def run(overrides=None, scenario="Baseline", upstream=None):
    t0 = time.perf_counter()
    S = _st()
    if scenario not in S["meta"]["scenarios"]:
        raise ValueError(f"unknown scenario '{scenario}' (expected one of {S['meta']['scenarios']})")
    ov = _resolve(overrides, scenario, upstream)
    K, yrs, fcy, la = S["keys"], S["meta"]["years"], S["meta"]["fc_years"], S["meta"]["last_act"]
    dg = float(_lev(ov, "pop_growth_pp") or 0.0) / 100.0
    scale = pd.Series([1.0] + [(1 + dg) ** (i + 1) for i in range(len(fcy))], index=yrs) if dg != 0 else 1.0
    dr = _drivers(S, ov["exogenous"], scale, _coef(ov, "FR4.E9_oil|ln_rgdpoil"))
    tot = dr["emp"]
    phi, dphi = S["calib"]["phi"], float(_lev(ov, "phi_delta_2030_pp") or 0.0) / 100.0
    hir = tot * (pd.Series({y: phi + dphi * (y - la) / (fcy[-1] - la) for y in yrs}) if dphi != 0 else phi)
    decay = bool(_lev(ov, "addfactor_decay"))
    w1, w2 = _coef(ov, "FR4.E4_combo|w_pooled"), _coef(ov, "FR4.E5_combo|w_pooled")
    FCs, series = {}, {}
    for tg, total in [("emp", tot), ("hired", hir)]:
        Bs = dict(S["basis"][tg], beta1=_coef(ov, f"FR4.E4_pooled_{tg}|d_lo_sq"),
                  beta2=_coef(ov, f"FR4.E5_pooled_{tg}|d_lo_sq"), b6=_coef(ov, f"FR4.E6_{tg}|ln_rva_oth"))
        fr = FCs[tg] = _allocate(Bs, dr, yrs, [float(total.loc[y]) for y in yrs], w1, w2, decay)
        for k in K["act"] + ["total"]:
            series[f"fr4:{tg}:{k}"] = fr[k]
        for g in K["g8"]:
            series[f"fr4:{tg}:grp:{g}"] = fr[K["g8_members"][g]].sum(axis=1)
        series[f"fr4:{tg}:bloc:pub"], series[f"fr4:{tg}:bloc:mkt"] = fr[K["pub"]].sum(axis=1), fr[K["mkt"]].sum(axis=1)
    inst = _institutions(S, dr, tot, hir, FCs["hired"], ov, decay)
    for col, sid in S["inst_id"].items():
        series[sid] = inst[col]
    series["fr4:phi"] = (hir / tot).reindex(yrs)
    series["fr4:emp_own"], series["fr4:lf_own"] = _own_total(S, dr)
    meta = {"module": MODULE, "scenario": scenario, "years": list(yrs), "nowcast_year": la,
            "units": "min nəfər (paylar: %, fr4:phi: 0–1)", "upstream": ov["upstream"],
            "levers": ov["levers"], "changed": [list(c) for c in ov["changed"]],
            "runtime_s": round(time.perf_counter() - t0, 4)}
    return B.make_result(series, meta=meta, warnings=ov["warnings"])


def _frame(res):
    df = B.result_to_frame(res)
    df.index.name = "year"
    return df.reset_index()


def _lever_checks(tol=0.0501):
    """The engine's levers reproduce the notebook's Part 18 lever table (rounded to 0.1 thousand there)."""
    p = os.path.join(_out_dir(), "FR4_sensitivity_levers.csv")
    if not os.path.exists(p):
        return {"ok": True, "skipped": "FR4_sensitivity_levers.csv absent"}
    L = pd.read_csv(p)
    y = str(_st()["meta"]["fc_years"][-1])
    QID = {"total": "fr4:emp:total", "labour_force": "fr4:lf", "agriculture": "fr4:emp:agr", "services": "fr4:emp:grp:services",
           "construction": "fr4:emp:constr", "hired": "fr4:hired:total", "budget": "fr4:budget", "nonbudget": "fr4:nonbudget",
           "state": "fr4:state", "nonstate": "fr4:nonstate", "hotel": "fr4:emp:hotel", "ict": "fr4:emp:ict",
           "industry": "fr4:emp:grp:industry", "mining": "fr4:emp:mining", "market_services": "fr4:emp:bloc:mkt"}
    cases = [("population growth 0.3pp lower", {"levers": {"pop_growth_pp": -0.3}}),
             ("population growth 0.3pp higher", {"levers": {"pop_growth_pp": 0.3}}),
             ("employee share +2pp", {"levers": {"phi_delta_2030_pp": 2.0}}),
             ("state share frozen", {"levers": {"state_share_mode": "frozen"}}),
             ("budget = all hired", {"levers": {"budget_definition": "kappa"}}),
             ("Tier 1 + industry: pure constant", {"coefficients": {"FR4.E4_combo|w_pooled": 0.0, "FR4.E5_combo|w_pooled": 0.0}}),
             ("Tier 1 + industry: pooled output system alone", {"coefficients": {"FR4.E4_combo|w_pooled": 1.0, "FR4.E5_combo|w_pooled": 1.0}}),
             ("SENSITIVITY ONLY: add-factors decay", {"levers": {"addfactor_decay": True}})]
    worst, n, probs = 0.0, 0, []
    for prefix, ov in cases:
        rows = L[L.lever.str.startswith(prefix)]
        if rows.empty:
            probs.append(f"lever '{prefix}' not in the CSV")
            continue
        s = run(ov, "Baseline")["series"]
        for _, r in rows.iterrows():
            d = abs(s[QID[r.quantity]][y] - float(r.alternative))
            worst, n = max(worst, d), n + 1
            if d > tol:
                probs.append(f"{prefix} / {r.quantity}: engine {s[QID[r.quantity]][y]:.3f} vs notebook {r.alternative}")
    return {"ok": not probs, "max_abs_diff": worst, "n_checked": n, "problems": probs, "tol": tol}


def selftest(tol=1e-8):
    """run({}, scenario) reproduces the notebook: activities (both bases), institutional breakdown and the
    full forecast table (every component), all scenarios; plus the Part 18 levers."""
    S, od = _st(), _out_dir()
    K, yrs = S["keys"], S["meta"]["years"]
    tidy = pd.read_csv(os.path.join(od, "FR4_forecast_tidy.csv"))
    detail, t0 = {}, time.perf_counter()
    for sc in S["meta"]["scenarios"]:
        df = _frame(run({}, sc))
        flt = lambda d, sc=sc: d[d["Unnamed: 0"] == sc].rename(columns={"Unnamed: 1": "year"})  # noqa: E731
        r = {}
        for nm, tg in [("FR4_employed_by_activity.csv", "emp"), ("FR4_hired_by_activity.csv", "hired")]:
            r[nm] = B.selftest_compare(df, os.path.join(od, nm), {f"fr4:{tg}:{k}": k for k in K["act"] + ["total"]},
                                       tol=tol, on=["year"], csv_filter=flt)
        imap = dict({v: k for k, v in S["inst_id"].items()}, **{"fr4:emp:total": "employed, total", "fr4:hired:total": "hired, total"})
        r["FR4_institutional_breakdown.csv"] = B.selftest_compare(df, os.path.join(od, "FR4_institutional_breakdown.csv"), imap,
                                                                  tol=tol, on=["year"], csv_filter=flt)
        t = tidy[(tidy.scenario == sc) & tidy.year.isin(yrs)].pivot(index="year", columns="id", values="value").reset_index()
        ids = [c for c in t.columns if c != "year"]
        miss = sorted(set(ids) ^ set(c for c in df.columns if c != "year"))
        m = df.merge(t, on="year", suffixes=("", "__nb"))
        mx = max(float(np.max(np.abs(m[i] - m[i + "__nb"]) / np.maximum(np.abs(m[i + "__nb"]), 1e-10))) for i in ids)
        r["FR4_forecast_tidy.csv"] = {"ok": (not miss) and mx <= tol and len(m) == len(yrs), "max_rel_diff": mx,
                                      "n_ids": len(ids), "problems": [f"ids differ: {miss[:5]}"] if miss else []}
        detail[sc] = r
    lv = _lever_checks()
    ok = all(v["ok"] for r in detail.values() for v in r.values()) and lv["ok"]
    mx = max(v["max_rel_diff"] for r in detail.values() for v in r.values())
    return {"ok": bool(ok), "max_rel_diff": mx, "levers": lv, "detail": detail,
            "runtime_s": round(time.perf_counter() - t0, 3)}
