"""Calibration of the synthetic household file to DSK aggregates (FR3).

1. Entropy (raking/GREG-type, Deville-Särndal exponential) calibration of household weights
   to population, urban population, formal employees by NACE section, state employees,
   own-account agriculture / non-agriculture, unemployed (LFS), pensioners (DSMF), children
   and the DSK decile structure (households 10 % per decile, persons per decile).
2. HBS-admin reconciliation factors for policy-relevant sources (net wages, pensions,
   benefits) — kept as parameters so that taxes/costs use administrative amounts.
3. ÜSY take-up probability calibrated to DSMF recipients.
4. Iterative decile adjustment of the NON-policy sources (self-employment, agriculture,
   property, inter-household transfers, remittances) to DSK table 25; consumption to
   table 53/54 (category baskets by decile); poverty reconciliation factor kappa so that the
   DSK headcount is reproduced at the official line. All of this is IN-SAMPLE."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import ms_metrics as M
from . import ms_policy as MP
from . import ms_targets as MT
from .ms_rawdata import SECTORS
from .taxben import Params

RESID_P = {"selfemp": "inc_selfemp", "agri": "inc_agri"}            # person-level
RESID_H = {"property": "inc_property", "interhh": "transfer_hh", "remit": "remit"}


def entropy_weights(X, T, d, soft=None, iters=300, tol=1e-7):
    """w = d*exp(X lam) with X'w = T (Newton + backtracking). `soft` (per constraint, >=0)
    turns a constraint into a penalised one (dual ridge): X'w - T = -soft*lam."""
    sc = np.where(np.abs(T) > 0, np.abs(T), np.abs(X).T @ d)
    Xs, Ts = X / sc, T / sc
    c = np.zeros(len(T)) if soft is None else np.asarray(soft, float)
    lam = np.zeros(X.shape[1])
    w = d.copy()
    F = Xs.T @ w - Ts + c * lam
    for _ in range(iters):
        err = np.max(np.abs(F))
        if err < tol:
            break
        J = Xs.T @ (Xs * w[:, None]) + np.diag(c)
        step = np.linalg.lstsq(J, F, rcond=None)[0]
        t = 1.0
        while True:
            lam_n = lam - t * step
            w_n = d * np.exp(np.clip(X @ (lam_n / sc), -30, 30))
            F_n = Xs.T @ w_n - Ts + c * lam_n
            if np.max(np.abs(F_n)) < err or t < 1e-4:
                break
            t /= 2
        lam, w, F = lam_n, w_n, F_n
    hard = c == 0
    resid = (Xs.T @ w - Ts)
    return w, float(np.max(np.abs(resid[hard]))) if hard.any() else 0.0


SRC_DEC = ("employment", "pensions")      # source x income-decile constraints (soft)


def design(p, T, inc_dec=None, con_dec=None, prof=None, hh=None):
    """Household-level constraint matrix and targets."""
    h = lambda v: MP.hh_sum(p, v)
    st, sec = p["status"].to_numpy(), p["sector"].to_numpy()
    cols = {"pop": h(np.ones(len(p))), "urban": h(p["urban"].to_numpy(float)),
            "hired_state": h((st == "employee") & (p["ownership"] == "state")),
            "agri_own": h(st == "agri"), "selfemp_own": h(st == "selfemp"),
            "unemployed": h(st == "unemployed"), "pensioners": h(st == "pensioner"),
            "children": h(p["age"].to_numpy() < 15),
            "wagebill_state": h(p["wage_gross"].to_numpy() * (st == "employee")
                                * (p["ownership"] == "state").to_numpy()),
            "wagebill_nonstate": h(p["wage_gross"].to_numpy() * (st == "employee")
                                   * (p["ownership"] == "nonstate").to_numpy())}
    for s in SECTORS:
        cols[f"hired:{s}"] = h((st == "employee") & (sec == s))
    tg = {k: T["counts"][k] for k in cols}
    n = cols["pop"]
    for nm, dec, pr in (("inc", inc_dec, prof and prof[0]), ("con", con_dec, prof and prof[1])):
        if dec is None:
            continue
        for d in range(1, 10):
            cols[f"{nm}_H{d}"] = (dec == d) - 0.1
            tg[f"{nm}_H{d}"] = 0.0
            cols[f"{nm}_P{d}"] = (dec == d) * n
            tg[f"{nm}_P{d}"] = pr[d - 1] * T["counts"]["pop"]
    if hh is not None and inc_dec is not None:
        for src in SRC_DEC:
            lv = T["inc_dec_tab"][src].to_numpy() * prof[0] * T["counts"]["pop"]
            lv = lv / lv.sum() * T["hbs_pc"][src] * T["counts"]["pop"]
            amt = hh[f"y_{src}"].to_numpy()
            for d in range(1, 11):
                cols[f"src_{src}_{d}"] = amt * (inc_dec == d)
                tg[f"src_{src}_{d}"] = lv[d - 1]
    keys = list(cols)
    return np.column_stack([cols[k] for k in keys]).astype(float), \
        np.array([tg[k] for k in keys], float), keys


def calibrate(p, year=2024, n_outer=4, n_inner=12, p_takeup=None, soft_dec=1e-7, soft_src=1.0,
              takeup_gamma=None,
              log=print):
    T = MT.load(year)
    p = MP.prepare(p)
    for k in MP.CATS:
        if f"cons_{k}" not in p:
            p[f"cons_{k}"] = 0.0
    P = Params()
    cal = {"base_year": year, "factors": {}, "uprate": {str(year): {}}, "p_takeup": 1.0,
           "takeup_rule": "P = min(1, a*(gap/(n*need))**gamma)"}
    n = MP.hh_sum(p, np.ones(len(p)))
    pop = T["counts"]["pop"]
    d0 = np.full(len(n), pop / n.sum())
    prof = (MT.person_profile(T["inc_dec"], T["hbs_pc"]["total"]),
            MT.person_profile(T["cons_dec"], T["cons_pc"]))
    inc_dec = con_dec = None
    for outer in range(n_outer):
        X, tg, keys = design(p, T, inc_dec, con_dec, prof if inc_dec is not None else None,
                             hh if inc_dec is not None else None)
        soft = np.array([soft_dec * (0.01 if k.startswith("con_P") else 1.0)
                         * (soft_src if k.startswith("src_") else 1.0)
                         if ("_H" in k or "_P" in k or k.startswith("src_")) else 0.0
                         for k in keys])
        w, err = entropy_weights(X, tg, d0, soft)
        p["weight"] = w[p["_h"].to_numpy()]
        for _ in range(n_inner):
            _reconcile(p, cal, T, P, year, p_takeup, takeup_gamma)
            hh, _ = MP.compute(p, cal, year, P)
            inc_dec = M.hh_deciles(hh["y_pc"].to_numpy(), hh["w"].to_numpy())
            _decile_adjust(p, hh, inc_dec, T["inc_dec"])
        _reconcile(p, cal, T, P, year, p_takeup, takeup_gamma)
        hh, _ = MP.compute(p, cal, year, P)
        inc_dec = M.hh_deciles(hh["y_pc"].to_numpy(), hh["w"].to_numpy())
        con_dec = _consumption(p, hh, T, rebuild=(outer == 0))
        log(f"[ms_calib] {year} outer {outer}: weight err {err:.2e}")
    hh, _ = MP.compute(p, cal, year, P)
    pw = (hh["w"] * hh["n"]).to_numpy()
    q = M.wquantile(hh["c_pc"].to_numpy(), pw, T["pov_rate"] / 100)
    cal["kappa"] = float(T["pov_line"] / q)
    cal["pov_line"] = T["pov_line"]
    cal["weight_err"] = err
    return p.drop(columns=["_h", "_first"]), cal, T


def _reconcile(p, cal, T, P, year, p_takeup, takeup_gamma):
    """Source factors (policy sources) + residual source totals + ÜSY take-up."""
    f = cal["factors"]
    cal["factors"] = {}
    hh, per = MP.compute(p, cal, year, P)
    w = hh["w"].to_numpy()
    pop = T["counts"]["pop"]
    tot = lambda c: float(np.sum(w * hh[c]))
    f["employment"] = T["hbs_pc"]["employment"] * pop / tot("y_employment")
    f["pensions"] = T["hbs_pc"]["pensions"] * pop / tot("y_pensions")
    for s, col in {**RESID_P, **RESID_H}.items():
        r = T["hbs_pc"][s] * pop / max(tot(f"y_{s}"), 1e-9)
        p[col] = p[col] * r
    cal["factors"] = dict(f)
    hh, _ = MP.compute(p, {**cal, "p_takeup": 1e9}, year, P)
    pw = (hh["w"] * hh["n"]).to_numpy()
    if p_takeup is not None:
        cal["p_takeup"], cal["takeup_gamma"] = float(p_takeup), float(takeup_gamma or 1.0)
    elif np.isfinite(T["utsy_members"]) and hh["utsy_elig"].any():
        u = MP.hh_first(p, "utsy_u")
        gs = hh["utsy_gapshare"].to_numpy()
        gap = gs * hh["n"].to_numpy() * P.get("need_criterion", year)
        best = None
        for gm in ([takeup_gamma] if takeup_gamma else (1.0, 1.5, 2.0, 2.5, 3.0, 4.0)):
            lo, hi = 0.0, 1e4
            for _ in range(60):
                a = 0.5 * (lo + hi)
                rec = (u < np.minimum(1, a * gs ** gm)) & (gs > 0)
                lo, hi = (a, hi) if np.sum(pw * rec) < T["utsy_members"] else (lo, a)
            rec = (u < np.minimum(1, a * gs ** gm)) & (gs > 0)
            avg = np.sum(hh["w"].to_numpy() * gap * rec) / max(np.sum(pw * rec), 1)
            err = abs(avg - T.get("utsy_avg_pp", avg))
            if best is None or err < best[0]:
                best = (err, a, gm)
        cal["p_takeup"], cal["takeup_gamma"] = best[1], best[2]
    hh, _ = MP.compute(p, cal, year, P)
    ut = float(np.sum(hh["w"] * hh["utsy"]))
    bo = float(np.sum(hh["w"] * hh["y_benother"])) / f.get("benefits", 1.0)
    f["benefits"] = max(T["hbs_pc"]["benefits"] * pop - ut, 0.0) / max(bo, 1e-9)
    cal["factors"] = dict(f)


def _decile_adjust(p, hh, dec, target, damp=0.7):
    """Scale NON-policy sources (self-employment, agriculture, property, inter-household
    transfers, remittances) decile by decile towards DSK table 25 (person-weighted means);
    households without such income receive inter-household transfers when below target."""
    pw = (hh["w"] * hh["n"]).to_numpy()
    n = hh["n"].to_numpy()
    y = hh["y_pc"].to_numpy()
    res = (hh[[f"y_{s}" for s in list(RESID_P) + list(RESID_H)]].sum(axis=1)).to_numpy() / n
    s = np.ones(len(hh))
    add = np.zeros(len(hh))
    for d in range(1, 11):
        m = dec == d
        gap = target[d - 1] - np.sum(pw[m] * y[m]) / pw[m].sum()
        r = np.sum(pw[m] * res[m]) / pw[m].sum()
        s[m] = np.clip(1 + damp * gap / max(r, 1e-6), 0.2, 5.0)
        z = m & (res < 1.0)
        if gap > 0 and z.any():
            add[z] = damp * gap * n[z]
    hcode = p["_h"].to_numpy()
    for col in list(RESID_P.values()) + list(RESID_H.values()):
        p[col] = p[col] * s[hcode]
    p["transfer_hh"] = p["transfer_hh"] + add[hcode]


def _consumption(p, hh, T, rebuild=False, iters=25):
    """Per-capita consumption: c = y^0.85 * exp(noise), then decile levels (table 53) and
    category baskets by consumption decile (table 53/54)."""
    n, w = hh["n"].to_numpy(), hh["w"].to_numpy()
    if rebuild or "cons_food" not in p:
        noise = MP.hh_first(p, "cons_noise")
        c = np.maximum(hh["y_pc"].to_numpy(), 20) ** 0.85 * np.exp(noise)
    else:
        c = np.column_stack([MP.hh_first(p, f"cons_{k}") for k in MP.CATS]).sum(1) / n
    for _ in range(iters):
        dec = M.hh_deciles(c, w)
        mod = M.decile_means(c, n, w, dec)
        c = c * (T["cons_dec"] / mod)[dec - 1] ** 0.8
    dec = M.hh_deciles(c, w)
    sh = T["cons_shares"].to_numpy()[dec - 1]
    hcode = p["_h"].to_numpy()
    for j, k in enumerate(MP.CATS):
        p[f"cons_{k}"] = np.round((c * n * sh[:, j])[hcode], 2)
    return dec
