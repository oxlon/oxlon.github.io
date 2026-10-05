"""FR12 scenario engine (contract section B) — competition environment.

Re-implements the forecast solve of FR12.ipynb (Parts 13-16) from the exported state output/engine/FR12_state.*:
entry (log births) and exit rules for 11 activity groups and 14 regions with the stock-flow identity
N_t = (N_{t-1} + B_t) / (1 + x_t), the SME output-share system and the size-class concentration bounds, the projected
early-warning score, and the calibrated IO scenario toolkit (Cournot, merger, cost, import, mixed oligopoly).

    run(overrides=None, scenario="Baseline", upstream=None) -> {"series": {id: {year: v}}, "meta": {...}, "warnings": [...]}
    overrides = {"exogenous": {"fr1:rva_trd": {"pct": -5}}, "coefficients": {"FR12.act_lnB_dem|dem": 0.004},
                 "levers": {"io_market": "MOB", "io_elasticity": 1.5, "io_dN": 2}}
    upstream  = {"FR1": result, "FR10": result} (chain.run_chain); None -> the CSV-based paths in the state.
"""
from __future__ import annotations

import os
import re
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import fsolve

from . import base as B
from .. import project_root

MODULE = "FR12"
_S = None


def _st():
    global _S
    if _S is None:
        _S = B.load_state(MODULE)
    return _S


def inputs():
    return _st()["inputs"]


# ------------------------------------------------------------------ exogenous paths (state / upstream / overrides)
_FR10_ALIAS = {"Karabakh": ["Garabagh"], "East_Zangezur": ["Eastern_Zangezur"], "Nakhchivan": ["Nakhchivan_AR"]}


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def _from_upstream(upstream, sid, years):
    mod = sid.split(":")[0].upper()
    res = (upstream or {}).get(mod)
    if not res:
        return None, False
    ser = res.get("series", {}) or {}
    d = ser.get(sid)
    if d is None and mod == "FR10":          # FR10 engine ids: fr10:reg_output:<FR10 region code>
        code = sid.split(":")[-1]
        for alias in [code] + _FR10_ALIAS.get(code, []):
            if f"fr10:reg_output:{alias}" in ser:
                d = ser[f"fr10:reg_output:{alias}"]
                break
        if d is None:
            cand = [k for k in ser if k.startswith("fr10:reg_output:") and _norm(code) in _norm(k)]
            d = ser[cand[0]] if len(cand) == 1 else None
    if d is None:
        return None, True
    try:
        v = np.array([float(d[str(y)] if str(y) in d else d[y]) for y in years])
    except (KeyError, TypeError, ValueError):
        return None, True
    return (v, True) if np.all(np.isfinite(v)) else (None, True)


def _exogenous(cat, overrides, scenario, upstream, W):
    out, used_up = {}, []
    ex_ov = (overrides or {}).get("exogenous") or {}
    known = {e["id"] for e in cat["exogenous"]}
    for k in ex_ov:
        if k not in known:
            W.append(f"naməlum ekzogen dəyişən '{k}' — nəzərə alınmadı")
    for e in cat["exogenous"]:
        base = np.asarray(e["baseline"].get(scenario, e["baseline"]["Baseline"]), float)
        if not e["id"].startswith("fr12:"):
            up, asked = _from_upstream(upstream, e["id"], e["years"])
            if up is not None:
                base = up
                used_up.append(e["id"])
            elif asked:
                W.append(f"{e['id']}: yuxarı axın nəticəsində tapılmadı — baza yolu istifadə olunur")
        v = base
        if e["id"] in ex_ov:
            try:
                v = B._exo_value(ex_ov[e["id"]], base, e["years"])
            except (ValueError, IndexError, TypeError) as err:
                W.append(f"{e['id']}: yanlış dəyər ({err}) — nəzərə alınmadı")
                v = base
            if v.shape != base.shape:
                W.append(f"{e['id']}: {len(e['years'])} dəyər gözlənilirdi — nəzərə alınmadı")
                v = base
            c = B._clip(v, e.get("min"), e.get("max"))
            if not np.allclose(c, v, equal_nan=True):
                W.append(f"{e['id']}: dəyərlər [{e.get('min')}, {e.get('max')}] sərhədinə qədər kəsildi")
            v = c
        out[e["id"]] = np.asarray(v, float)
    return out, used_up


# ------------------------------------------------------------------ drivers (FR12.ipynb Part 13: drivers_activity / drivers_region)
def _drivers_activity(S, X):
    y0, fc = S["years"]["last_act"], list(S["years"]["fc"])
    h = S["hist"]
    def va(g, y):
        codes = S["group_fr1"][g]
        if y <= y0:
            return float(sum(h["rva"][c][str(y)] for c in codes))
        return float(sum(X[f"fr1:{c}"][fc.index(y)] for c in codes))
    lend = {y0: h["lend_last"], **{y: X["fr1:lendrate"][i] for i, y in enumerate(fc)}}
    cr = {y0 - 1: h["rcred"][str(y0 - 1)], y0: h["rcred"][str(y0)], **{y: X["fr1:rcred_tot"][i] for i, y in enumerate(fc)}}
    rows = []
    for y in [y0] + fc:
        for g in S["groups"]:
            pcm = h["pcm_last"][g] if y <= y0 else X[f"fr12:assume:pcm:{g}"][fc.index(y)]
            rows.append(dict(unit=g, year=y, dem=float(np.log(va(g, y) / va(g, y - 1)) * 100), size=float(np.log(va(g, y))), lend=float(lend[y]),
                             cred=float(np.log(cr[y] / cr[y - 1]) * 100), pcm=float(pcm), brk=1.0, d2022=0.0))
    return pd.DataFrame(rows)


def _drivers_region(S, X, scenario):
    y0, fc = S["years"]["last_act"], list(S["years"]["fc"])
    h = S["hist"]
    rf0 = h["reg_out_last"].get(scenario, h["reg_out_last"]["Baseline"])
    rf = lambda u, y: rf0[u] if y <= y0 else X[f"fr10:output_mn_AZN:{S['region_ids'][u]}"][fc.index(y)]  # noqa: E731
    non = lambda y: h["rgdpnon_last"] if y <= y0 else X["fr1:rgdpnon"][fc.index(y)]  # noqa: E731
    rows = []
    for y in fc:
        d_non = np.log(non(y) / non(y - 1)) * 100
        for u in S["regions"]:
            rows.append(dict(unit=u, year=y, reg=float(np.log(rf(u, y) / rf(u, y - 1)) * 100), size=float(np.log(rf(u, y))), non=float(d_non),
                             lend=float(X["fr1:lendrate"][fc.index(y)])))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ applied rules (Part 12 apply_rule / Part 13 rule_pred)
def _part_pred(P, rows):
    p = np.array([P["a"][u] for u in rows.unit], float)
    if P["regs"]:
        p = p + rows[P["regs"]].to_numpy(float) @ np.asarray(P["b"], float)
    if P["fixed"]:
        p = p + rows[P["fixed"]].to_numpy(float) @ np.asarray(P["bf"], float)
    return p


def _edits(P, eq_id, rows, coefs):
    """Edited coefficient c -> prediction moves by (x_c - ref_c,unit) * (c_new - c_hat): the unit effect (and the anchor)
    re-adjust, exactly as the notebook's slope draws (ref = last training row if anchored, else the unit mean)."""
    d = np.zeros(len(rows))
    if P is None or eq_id is None:
        return d
    for c, hat in list(zip(P["regs"], P["b"])) + list(zip(P["fixed"], P["bf"])):
        new = coefs.get(f"{eq_id}|{c}", hat)
        if new != hat:
            ref = np.array([P["ref"][u][c] for u in rows.unit], float)
            d = d + (rows[c].to_numpy(float) - ref) * (new - hat)
    return d


def _rule(R, rows, coefs):
    p0 = _part_pred(R["m0"], rows) + _edits(R["m0"], R["eq_m0"], rows, coefs)
    if R["m1"] is None:
        return p0
    p1 = _part_pred(R["m1"], rows) + _edits(R["m1"], R["eq_m1"], rows, coefs)
    if R["shift"] is not None:
        p1 = p1 + np.array([R["shift"][u] for u in rows.unit], float)
    return R["wt"] * p1 + (1 - R["wt"]) * p0


def _stock_rates(rows, lnB, xr, N0):
    d = rows[["unit", "year"]].copy()
    d["B"] = np.exp(lnB)
    d["x"] = np.clip(xr, 0, None)
    d = d.sort_values(["unit", "year"])
    N = []
    for u, g in d.groupby("unit", sort=False):
        n = float(N0[u])
        for b_, x_ in zip(g.B, g.x):
            n = (n + b_) / (1 + x_ / 100)
            N.append(n)
    d["N"] = N
    d["entry"] = d.B / d.N * 100
    d["new"] = d.B
    d["exits"] = d.x / 100 * d.N
    return d.rename(columns={"x": "exit"})


# ------------------------------------------------------------------ concentration bounds (Part 8 hhi_bounds, v2 floor rule)
def _hhi_bounds(n, S_, nL, SL, mkt, capped, CAP):
    u = {c: (CAP[c] / mkt if capped else max(S_[c], 1e-12)) for c in CAP}
    low = sum(S_[c] ** 2 / n[c] for c in n if n[c] > 0) + (SL ** 2 / nL if nL > 0 else 0)
    vert, up_caps = [], 0.0
    for c in CAP:
        if n[c] <= 0 or S_[c] <= 0:
            continue
        q = min(int(np.floor(S_[c] / u[c] + 1e-12)), int(n[c]))
        r = max(S_[c] - q * u[c], 0.0)
        up_caps += q * u[c] ** 2 + (r ** 2 if q < n[c] else 0.0)
        vert += [u[c]] * min(q, 4) + ([r] if q < n[c] else [])
    vert = sorted(vert, reverse=True)
    eq = sorted([(SL / nL, nL)] + [(S_[c] / n[c], n[c]) for c in CAP if n[c] > 0], reverse=True)
    c4l, k = 0.0, 4.0
    for sh, cnt in eq:
        t = min(k, cnt)
        c4l += t * sh
        k -= t
        if k <= 0:
            break
    out = dict(hhi_lower=low, hhi_upper=up_caps + SL ** 2, cr4_lower=c4l,
               cr4_upper=min(1.0, SL + sum(vert[:3])) if nL >= 1 else sum(vert[:4]))
    for fl in (30.0, 15.0):
        f = fl / mkt
        if capped and nL >= 1 and SL >= nL * f:
            out[f"hhi_upper_floor{int(fl)}"] = up_caps + (SL - (nL - 1) * f) ** 2 + (nL - 1) * f ** 2
            out[f"cr4_upper_floor{int(fl)}"] = (SL - (nL - 4) * f) if nL >= 4 else min(1.0, SL + sum(vert[:int(4 - nL)]))
        elif not capped and nL >= 1 and SL >= nL * f:
            out[f"hhi_upper_floor{int(fl)}"] = up_caps + (SL - (nL - 1) * f) ** 2 + (nL - 1) * f ** 2
            top = sorted([SL - (nL - 1) * f] + [f] * int(min(nL - 1, 3)) + [S_[c] for c in CAP if n[c] > 0 and S_[c] > 0], reverse=True)
            out[f"cr4_upper_floor{int(fl)}"] = min(1.0, sum(top[:4]))
        else:
            out[f"hhi_upper_floor{int(fl)}"] = np.nan
            out[f"cr4_upper_floor{int(fl)}"] = np.nan
    return out


def _conc_paths(S, Xa, sme_pred, Nf):
    C = S["conc"]
    CAP = C["cap"]
    va_last = C["va_last"]
    rows = []
    for (g, y, size), lo in zip(Xa[["unit", "year", "size"]].itertuples(index=False, name=None), sme_pred):
        sme = 100 / (1 + np.exp(-lo))
        mkt = C["go"][g][str(y)] if str(y) in C["go"][g] else C["go"][g][str(S["years"]["last_act"])] * np.exp(size - np.log(va_last[g]))
        grow = Nf[(g, y)] / C["n2024"][g]
        n = {c: C["e005"][g][c] * grow for c in CAP}
        cls = C["cls"][g]
        S_ = {c: sme / 100 * cls[c] / cls["sme"] for c in CAP}
        b = _hhi_bounds(n, S_, C["n_large"][g], 1 - sme / 100, float(mkt), C["capped"][g], CAP)
        rows.append(dict(group=g, year=int(y), sme_output_share=sme, large_share=(1 - sme / 100) * 100, hhi_lower=b["hhi_lower"] * 1e4,
                         hhi_upper=b["hhi_upper"] * 1e4, hhi_upper_floor30=b["hhi_upper_floor30"] * 1e4, cr4_upper=b["cr4_upper"] * 100,
                         cr4_lower=b["cr4_lower"] * 100))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ projected early-warning score (Part 16 / 16.1)
def _zchange(s, recent=3):
    s = pd.Series(s, dtype=float).dropna().sort_index()
    if len(s) < 4:
        return np.nan
    sd = s.diff().std()
    return float((s.iloc[-recent:].mean() - s.iloc[:-recent].mean()) / sd) if sd > 0 else np.nan


def _ew_score(z, E):
    zs, W, D = E["z_star"], E["W"], E["dirs"]
    f = {}
    for k, nm in [("conc", "F_conc"), ("entry", "F_entry"), ("exit", "F_exit"), ("mob", "F_mob")]:
        f[nm] = "insufficient data" if not np.isfinite(z[k]) else bool(D[k] * z[k] > zs)
    f["F_margin_entry"] = ("insufficient data" if not (np.isfinite(z["margin"]) and np.isfinite(z["entry"]))
                           else bool(z["margin"] > zs and z["entry"] < 0))
    av = {k: v for k, v in f.items() if isinstance(v, bool)}
    sc = sum(W[k] for k, v in av.items() if v) / sum(W[k] for k in av) if av else np.nan
    return sc, int(sum(av.values())), bool(av) and (sc >= 0.30 or sum(av.values()) >= 2), f


def _ew_project(S, FCa, CP, Xpcm):
    E = S["ew"]
    y0 = S["years"]["last_act"]
    out = []
    for g in S["groups"]:
        h = E["hist"][g]
        f = FCa[FCa.unit == g].set_index("year")
        c = CP[CP.group == g].set_index("year")
        for t in [y0] + list(S["years"]["fc"]):
            fy = [y for y in f.index if y <= t]
            cy = [y for y in c.index if y <= t]
            ser = dict(conc=(pd.concat([pd.Series({int(k): v for k, v in h["conc"].items()}), c.large_share.loc[cy]]), 3),
                       entry=(pd.concat([pd.Series({int(k): v for k, v in h["lnB"].items()}), np.log(f.new.loc[fy])]), 3),
                       exit=(pd.concat([pd.Series({int(k): v for k, v in h["exit"].items()}), f.exit.loc[fy]]), 2), mob=(pd.Series(dtype=float), 3),
                       margin=(pd.concat([pd.Series({int(k): v for k, v in h["pcm"].items()}),
                                          pd.Series({y: Xpcm[g][y] for y in range(y0 + 1, t + 1)}, dtype=float)]), 3))
            z = {k: _zchange(s_.groupby(level=0).last(), r) for k, (s_, r) in ser.items()}
            sc, nf, ls, fl = _ew_score(z, E)
            out.append(dict(group=g, year=int(t), score=sc, n_flags=nf, watch_list=ls))
    return pd.DataFrame(out)


# ------------------------------------------------------------------ IO scenario toolkit (Part 15, calibrated; assumptions as levers)
def _lin_eq(N, eps, theta, c, ab):
    a, b = ab
    Q = N * (a - c) / (b * (N + theta))
    return a - b * Q, Q


def _calibrate(hhi, eps, theta):
    L = min(theta * hhi / eps, 0.95)
    b = 1 / eps
    return dict(L=L, c=1 - L, a=1 + b, b=b, N=theta / (L * eps) if L > 0 else np.inf)


def _outcome(P0, Q0, c0, P1, Q1, c1, rev, dps=None):
    dcs = 0.5 * (Q0 + Q1) * (P0 - P1)
    dps = (P1 - c1) * Q1 - (P0 - c0) * Q0 if dps is None else dps
    ok = rev is not None and rev == rev
    return dict(d_price_pct=(P1 / P0 - 1) * 100, d_markup_pp=((P1 - c1) / P1 - (P0 - c0) / P0) * 100, d_output_pct=(Q1 / Q0 - 1) * 100,
                d_cs_pct_rev=dcs / (P0 * Q0) * 100, d_ps_pct_rev=dps / (P0 * Q0) * 100,
                d_cs_mn=dcs / (P0 * Q0) * rev if ok else np.nan, d_ps_mn=dps / (P0 * Q0) * rev if ok else np.nan)


def _sc_entry(hhi, eps, theta, dN, rev):
    k = _calibrate(hhi, eps, theta)
    P0, Q0 = _lin_eq(k["N"], eps, theta, k["c"], (k["a"], k["b"]))
    P1, Q1 = _lin_eq(k["N"] + dN, eps, theta, k["c"], (k["a"], k["b"]))
    return _outcome(P0, Q0, k["c"], P1, Q1, k["c"], rev)


def _sc_merger(hhi, eps, theta, s1, s2, rev):
    hhi = max(hhi, s1 ** 2 + s2 ** 2)
    dH = 2 * s1 * s2
    h1 = hhi + dH
    us = ("presumed to enhance market power" if h1 > .25 and dH > .02 else
          ("potentially raises significant concerns" if h1 > .15 and dH > .01 else "unlikely to have adverse effects"))
    eu = "concern" if ((h1 > .2 and dH >= .015) or (.1 <= h1 <= .2 and dH >= .025)) else "no presumption"
    k = _calibrate(hhi, eps, theta)
    P0, Q0 = _lin_eq(k["N"], eps, theta, k["c"], (k["a"], k["b"]))
    P1, Q1 = _lin_eq(max(theta / (min(theta * h1 / eps, 0.95) * eps), 1.0), eps, theta, k["c"], (k["a"], k["b"]))
    return _outcome(P0, Q0, k["c"], P1, Q1, k["c"], rev) | dict(hhi_used=hhi * 1e4, hhi_post=h1 * 1e4, d_hhi=dH * 1e4, us_2010_screen=us,
                                                               eu_screen=eu, fs_required_mc_cut_pct=(P0 - k["c"]) / k["c"] * 100)


def _sc_cost(hhi, eps, theta, t, rev):
    k = _calibrate(hhi, eps, theta)
    P0, Q0 = _lin_eq(k["N"], eps, theta, k["c"], (k["a"], k["b"]))
    P1, Q1 = _lin_eq(k["N"], eps, theta, k["c"] + t, (k["a"], k["b"]))
    ne = k["N"] * eps
    return _outcome(P0, Q0, k["c"], P1, Q1, k["c"] + t, rev) | dict(passthrough_linear=(P1 - P0) / t if t else np.nan,
                                                                   passthrough_const_elast=ne / (ne - theta) if ne > theta else np.nan)


def _sc_import(hhi_d, eps, theta, m0, m1, eta, rev):
    L0 = min(theta * hhi_d * (1 - m0) / (eps + eta * m0), .95)
    L1 = min(theta * hhi_d * (1 - m1) / (eps + eta * m1), .95)
    b = 1 / eps
    a = 1 + b
    c = 1 - L0
    P1 = c / (1 - L1)
    Q1 = max(a - P1, 0) / b
    return _outcome(1.0, 1.0, c, P1, Q1, c, rev)


def _mixed(hhi, sigma, eps, theta, lam, rev, n_max=1000):
    b = 1 / eps
    a = 1 + b
    hhi = min(max(hhi, sigma ** 2 + (1 - sigma) ** 2 / n_max), sigma ** 2 + (1 - sigma) ** 2)
    n = (1 - sigma) ** 2 / (hhi - sigma ** 2)
    c = 1 - theta * b * (1 - sigma) / n
    k = theta * b * (1 - sigma) / (n * sigma)

    def foc(x, lm):
        q0, q = x
        P = a - b * (q0 + n * q)
        return [P - c - k * q0 - lm * theta * b * q0, P - c - theta * b * q]
    with warnings.catch_warnings():       # the FOCs are linear: fsolve reaches machine precision and may then report "no progress"
        warnings.simplefilter("ignore", RuntimeWarning)
        x0 = fsolve(foc, [sigma, (1 - sigma) / n], args=(0.0,), xtol=1e-12)
        x1 = fsolve(foc, x0, args=(lam,), xtol=1e-12)
    pr = lambda q0, q: (a - b * (q0 + n * q)) * (q0 + n * q) - c * (q0 + n * q) - k * q0 ** 2 / 2  # noqa: E731
    P0, Q0 = a - b * (x0[0] + n * x0[1]), x0[0] + n * x0[1]
    P1, Q1 = a - b * (x1[0] + n * x1[1]), x1[0] + n * x1[1]
    mc_avg = lambda q0, q: (c * n * q + (c + k * q0) * q0) / (q0 + n * q)  # noqa: E731
    o = _outcome(P0, Q0, mc_avg(*x0), P1, Q1, mc_avg(*x1), rev, dps=pr(*x1) - pr(*x0))
    return o | dict(hhi_used=hhi * 1e4, n_private=n, soe_share_after=x1[0] / Q1 * 100, d_welfare_pct_rev=o["d_cs_pct_rev"] + o["d_ps_pct_rev"],
                    calib_resid=float(abs(P0 - 1) + abs(Q0 - 1) + abs(x0[0] - sigma)), foc_residual=float(np.max(np.abs(foc(x1, lam)))))


def _io_fn(d):
    k = d["kind"]
    if k == "entry":
        return lambda h, e, t, r: _sc_entry(h, e, t, d["dN"], r)
    if k == "merger":
        return lambda h, e, t, r: _sc_merger(h, e, t, d["s1"], d["s2"], r)
    if k == "cost":
        return lambda h, e, t, r: _sc_cost(h, e, t, d["t"], r)
    if k == "import":
        return lambda h, e, t, r: _sc_import(h, e, t, d["m0"], d["m1"], d["eta"], r)
    return lambda h, e, t, r: _mixed(h, d["sigma"], e, t, d["lam"], r)


def io_grid(S=None):
    """The full illustrative grid of Part 15.1 (FR12_scenario_results.csv): HHI lower -> upper bound (5 log points)
    x elasticity x conduct for every scenario-market."""
    S = S or _st()
    I = S["io"]
    rows = []
    for d in I["scenarios"]:
        M = I["markets"][d["market"]]
        fn = _io_fn(d)
        rev = np.nan if M["rev"] is None else M["rev"]
        for h in np.exp(np.linspace(np.log(M["lo"]), np.log(M["up"]), 5)):
            for e in I["eps_grid"]:
                for th in I["theta_grid"]:
                    rows.append(dict(scenario=d["sid"], market=d["market"], change=d["change"], assumption=d["assumption"], hhi=h * 1e4,
                                     elasticity=e, conduct=th, **fn(h, e, th, rev)))
    R = pd.DataFrame(rows)
    R["hhi_eff"] = R.hhi_used.fillna(R.hhi)
    return R


def io_run(lev, S=None):
    """User IO scenario: every mechanism for one market with the lever values (assumptions returned with the results)."""
    S = S or _st()
    I = S["io"]
    mk = lev.get("io_market") or "ICT"
    if mk not in I["markets"]:
        raise ValueError(f"io_market '{mk}' unknown; options {sorted(I['markets'])}")
    M = I["markets"][mk]
    h = float(lev["io_hhi"]) / 1e4 if lev.get("io_hhi") is not None else float(np.sqrt(M["lo"] * M["up"]))
    e, th = float(lev["io_elasticity"]), float(lev["io_conduct"])
    rev = np.nan if M["rev"] is None else M["rev"]
    out = dict(market=mk, market_name=M["name"], hhi=h * 1e4, elasticity=e, conduct=th, structure_source=M["source"],
               S1_entry=_sc_entry(h, e, th, float(lev["io_dN"]), rev),
               S2_merger=_sc_merger(h, e, th, float(lev["io_merger_s1"]), float(lev["io_merger_s2"]), rev),
               S3_cost=_sc_cost(h, e, th, float(lev["io_cost_shock"]), rev),
               S4_import=_sc_import(h, e, th, float(lev["io_import_m0"]), float(lev["io_import_m1"]), float(lev["io_import_eta"]), rev),
               S5_mixed=_mixed(h, float(lev["io_soe_sigma"]), e, th, float(lev["io_soe_lambda"]), rev))
    sg = float(lev["io_soe_sigma"])
    if h < sg ** 2 + (1 - sg) ** 2 / 1000:
        out["S5_note_az"] = (f"HHI ({h * 1e4:,.0f}) dövlət payı σ = {sg:.1%} ilə uyğun deyil (HHI ≥ σ² olmalıdır): qarışıq oliqopoliya HHI = "
                             f"{out['S5_mixed']['hhi_used']:,.0f} ilə hesablandı")
    out["assumptions_az"] = ("Kurno, xətti tələb, kalibrləmə nöqtəsində P = Q = 1; L = θ·HHI/ε; illüstrativ — bazar quruluşu fərziyyədir, "
                             "real bazar payları ilə əvəz edilməlidir")
    return out


# ------------------------------------------------------------------ NACE-section flows: allocation of the region-panel total (v2)
def _sections(S, F):
    """Section births / deaths / stock = 2025-anchored share x region-panel total (statistical units) plus the 2026 nowcast
    increment from the observed January-June 2026 (full in 2026, half-life one year), rescaled to the total each year;
    entry and exit rates follow; bands = adjusted share x the total's band; half-year flows = full year x observed H1 ratio."""
    A = S["alloc"]
    secs = A["sections"]
    tot = F[F.id.str.match(r"^fr12:reg:(new|exits|N|entry|exit):ALL$")].copy()
    tot["m"] = tot.id.str.split(":").str[2]
    T = {(m, int(y)): (v, lo, hi) for m, y, v, lo, hi in zip(tot.m, tot.year, tot.value, tot.lower_5, tot.upper_95)}
    years = sorted({k[1] for k in T})
    tmap = {"new": "new", "liq": "exits", "stock": "N"}
    ex = pd.Index(secs).isin(A["exempt"])
    adj = {}
    for v, tm in tmap.items():
        sh = pd.Series({s: A["shares"][s][v] for s in secs})
        d26 = (pd.Series({s: A["nowcast"][s][v] for s in secs}) - sh * T[(tm, A["now_year"])][0]).where(~ex, 0.0)
        for y in years:
            raw = (sh * T[(tm, y)][0] + 0.5 ** ((y - A["now_year"]) / A["half_life"]) * d26).clip(lower=0.0)
            adj[(y, v)] = raw * T[(tm, y)][0] / raw.sum()
    rows = []
    for y in years:
        for s in A["publish"]:
            new, liq, st = adj[(y, "new")][s], adj[(y, "liq")][s], adj[(y, "stock")][s]
            kn, kl, ks = new / T[("new", y)][0], liq / T[("exits", y)][0], st / T[("N", y)][0]
            band = lambda m, k: (k * T[(m, y)][1], k * T[(m, y)][2])  # noqa: E731
            vals = dict(new=(new,) + band("new", kn), liq=(liq, np.nan, np.nan), stock=(st,) + band("N", ks),
                        entry=(new / st * 100,) + band("entry", kn / ks), exit=(liq / st * 100,) + band("exit", kl / ks))
            rows += [(f"fr12:sec:{m}:{s}", y, v, lo, hi) for m, (v, lo, hi) in vals.items()]
            if y >= A["h1_first_year"]:
                rows += [(f"fr12:sec_h1:{m}:{s}", y, A["h1"][s][m] * vals[m][0], A["h1"][s][m] * vals[m][1], A["h1"][s][m] * vals[m][2]) for m in ["stock", "new", "liq"]]
    return pd.DataFrame(rows, columns=["id", "year", "value", "lower_5", "upper_95"])


# ------------------------------------------------------------------ solve
def _solve(overrides=None, scenario="Baseline", upstream=None):
    S = _st()
    cat = S["inputs"]
    W = []
    ov = dict(overrides or {})
    res = B.apply_overrides(cat, {k: v for k, v in ov.items() if k != "exogenous"}, scenario)
    W += res["warnings"]
    X, used_up = _exogenous(cat, ov, scenario, upstream, W)
    coefs, lev = res["coefficients"], res["levers"]
    fc = list(S["years"]["fc"])
    Xa = _drivers_activity(S, X).sort_values(["unit", "year"]).reset_index(drop=True)
    Xr = _drivers_region(S, X, scenario).sort_values(["unit", "year"]).reset_index(drop=True)
    rec = []
    FCx = {}
    for pn, rows in [("activity", Xa), ("region", Xr)]:
        st = _stock_rates(rows, _rule(S["rules"][f"{pn}|lnB"], rows, coefs), _rule(S["rules"][f"{pn}|exit"], rows, coefs), S["N0"][pn])
        FCx[pn] = st
        pab = "act" if pn == "activity" else "reg"
        ids = (lambda u: u) if pn == "activity" else (lambda u: S["region_ids"][u])
        for r in st.itertuples():
            for m in ["new", "exits", "N", "entry", "exit"]:
                rec.append((f"fr12:{pab}:{m}:{ids(r.unit)}", int(r.year), float(getattr(r, m))))
        a = st.groupby("year")[["N", "new", "exits"]].sum()
        for y, r in a.iterrows():
            for m, v in [("N", r.N), ("new", r.new), ("exits", r.exits), ("entry", r.new / r.N * 100), ("exit", r.exits / r.N * 100)]:
                rec.append((f"fr12:{pab}:{m}:ALL", int(y), float(v)))
    Nf = {(r.unit, int(r.year)): float(r.N) for r in FCx["activity"].itertuples()}
    Xs = _drivers_activity(S, X)                                   # notebook row order (year-major) for the share system
    CP = _conc_paths(S, Xs, _rule(S["rules"]["sme|lo"], Xs, coefs), Nf)
    for r in CP.itertuples():
        for c in ["sme_output_share", "large_share", "hhi_lower", "hhi_upper", "hhi_upper_floor30", "cr4_lower", "cr4_upper"]:
            rec.append((f"fr12:conc:{c}:{r.group}", int(r.year), float(getattr(r, c))))
    emp = 100 / (1 + np.exp(-_rule(S["rules"]["sme_emp|lo"], Xs, coefs)))       # SME share of employees (same rule family)
    rec += [(f"fr12:conc:sme_employment_share:{g}", int(y), float(v)) for g, y, v in zip(Xs.unit, Xs.year, emp)]
    Xpcm = {g: {y: float(X[f"fr12:assume:pcm:{g}"][i]) for i, y in enumerate(fc)} for g in S["groups"]}
    EWp = _ew_project(S, FCx["activity"], CP, Xpcm)
    for r in EWp.itertuples():
        rec.append((f"fr12:ew:score:{r.group}", int(r.year), float(r.score)))
    F = pd.DataFrame(rec, columns=["id", "year", "value"])
    F["lower_5"], F["upper_95"] = np.nan, np.nan
    if scenario == "Baseline":
        bands = S["bands"]
        lo, hi = [], []
        for sid, y, v in zip(F.id, F.year, F.value):
            b = bands.get(sid, {}).get(str(y))
            lo.append(b[0] + (v - b[2]) if b else np.nan)
            hi.append(b[1] + (v - b[2]) if b else np.nan)
        F["lower_5"], F["upper_95"] = lo, hi
    F = pd.concat([F, _sections(S, F)], ignore_index=True)
    if scenario == "Baseline":
        if res["changed"] or any(k == "exogenous" for k in ov):
            W.append("zolaq (5–95%) notebook-un Əsas zolağıdır, nöqtə proqnozunun dəyişməsi qədər sürüşdürülüb (eni yenidən hesablanmayıb)")
    meta = dict(module=MODULE, scenario=scenario, upstream_used=used_up, changed=[f"{a}:{b}" for a, b in res["changed"]] + [f"exogenous:{k}" for k in (ov.get("exogenous") or {})],
                watch_list={int(y): sorted(EWp[(EWp.year == y) & EWp.watch_list].group) for y in sorted(EWp.year.unique())})
    try:
        meta["io"] = io_run(lev, S)
    except (ValueError, TypeError, KeyError) as err:
        W.append(f"IO ssenarisi hesablanmadı: {err}")
    if lev.get("io_grid"):
        meta["io_grid"] = io_grid(S).to_dict("records")
    return F, meta, W


def run(overrides=None, scenario="Baseline", upstream=None):
    S = _st()
    if scenario not in S["scenarios"]:
        raise ValueError(f"scenario must be one of {S['scenarios']}")
    F, meta, W = _solve(overrides, scenario, upstream)
    series = {}
    for sid, d in S["hist_series"].items():
        series[sid] = {int(y): v[0] for y, v in d.items()}
    for sid, g in F.groupby("id"):
        series.setdefault(sid, {}).update({int(y): v for y, v in zip(g.year, g.value)})
    meta["bands"] = {sid: {str(int(y)): [lo, hi] for y, lo, hi in zip(g.year, g.lower_5, g.upper_95) if lo == lo}
                     for sid, g in F[F.lower_5.notna()].groupby("id")}
    meta["imputed"] = {sid: sorted(int(y) for y, v in d.items() if v[1]) for sid, d in S["hist_series"].items() if any(v[1] for v in d.values())}
    meta["forecast_years"] = sorted(int(y) for y in F.year.unique())
    return B.make_result({k: dict(sorted(v.items())) for k, v in series.items()}, meta=meta, warnings=W)


def selftest(tol=1e-8):
    """run({}) for each scenario reproduces FR12_forecast_tidy.csv (forecast rows: value and Baseline band), the panel
    file FR12_forecast_entry_exit.csv, and the IO grid FR12_scenario_results.csv."""
    S = _st()
    out = os.path.join(project_root(), "output")
    detail = {}
    for sc in S["scenarios"]:
        F, _, _ = _solve({}, sc)
        detail[f"tidy:{sc}"] = B.selftest_compare(F, os.path.join(out, "FR12_forecast_tidy.csv"), ["value", "lower_5", "upper_95"], tol=tol, on=["id", "year"],
                                                  csv_filter=lambda d, sc=sc: d[(d.scenario == sc) & d.is_forecast.astype(str).str.lower().eq("true")][["id", "year", "value", "lower_5", "upper_95"]])
    G = pd.DataFrame(_solve({"levers": {"io_grid": True}}, "Baseline")[1]["io_grid"])
    ref = pd.read_csv(os.path.join(out, "FR12_scenario_results.csv"))
    cols = [c for c in G.columns if c in ref.columns and pd.api.types.is_numeric_dtype(G[c]) and pd.api.types.is_numeric_dtype(ref[c])]
    detail["io_grid"] = B.selftest_compare(G[cols], os.path.join(out, "FR12_scenario_results.csv"), cols, tol=tol)
    return {"ok": all(v["ok"] for v in detail.values()), "detail": detail}
