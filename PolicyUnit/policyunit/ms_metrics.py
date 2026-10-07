"""Distributional metrics for the microsimulation: Gini, FGT poverty (headcount, gap,
severity), DSK-style household deciles, winners/losers. All person-weighted (household
weight x size) unless stated."""
from __future__ import annotations

import numpy as np


def wquantile(x, w, q):
    o = np.argsort(x)
    cw = np.cumsum(w[o]) / np.sum(w)
    return float(np.interp(q, cw, x[o]))


def gini(x, w):
    """Gini of x with weights w (exact for grouped-by-unit data)."""
    x, w = np.asarray(x, float), np.asarray(w, float)
    o = np.argsort(x)
    x, w = x[o], w[o]
    cw = np.cumsum(w)
    cx = np.cumsum(w * x)
    W, X = cw[-1], cx[-1]
    # area under Lorenz curve (trapezoids)
    L = cx / X
    F = cw / W
    B = np.sum((F - np.r_[0, F[:-1]]) * (L + np.r_[0, L[:-1]])) / 2
    return float(1 - 2 * B)


def fgt(x, w, z, alpha):
    x, w = np.asarray(x, float), np.asarray(w, float)
    z = np.broadcast_to(np.asarray(z, float), x.shape)
    poor = x < z * (1 - 1e-9)        # tolerance: incomes topped up exactly to the line are not poor (float knife-edge)
    g = np.where(poor, (z - x) / z, 0.0)
    val = g ** alpha if alpha > 0 else poor.astype(float)
    return float(np.sum(w * val) / np.sum(w))


def hh_deciles(y_pc, w_hh):
    """DSK convention (tables 25/53): households ranked by per-capita income/consumption,
    each decile = 10 % of (weighted) households. Returns decile 1..10 per household."""
    o = np.argsort(y_pc, kind="stable")
    cw = np.cumsum(w_hh[o]) / np.sum(w_hh)
    d = np.empty(len(y_pc), int)
    d[o] = np.minimum((cw * 10 - 1e-9).astype(int) + 1, 10)
    return d


def decile_means(v_pc, n, w_hh, dec):
    """Person-weighted mean of a per-capita variable by decile (DSK table definition)."""
    pw = w_hh * n
    return np.array([np.sum((pw * v_pc)[dec == d]) / np.sum(pw[dec == d])
                     for d in range(1, 11)])


def decile_shares(y_pc, n, w_hh, dec):
    tot = y_pc * n * w_hh
    return np.array([tot[dec == d].sum() for d in range(1, 11)]) / tot.sum()


def winners_losers(d_pc, dec, w_hh, n, tol=0.5):
    """Share of persons gaining (> tol AZN/month p.c.), losing (< -tol), by decile."""
    pw = w_hh * n
    rows = []
    for d in range(1, 11):
        m = dec == d
        rows.append((d, float(np.sum(pw[m] * (d_pc[m] > tol)) / pw[m].sum() * 100),
                     float(np.sum(pw[m] * (d_pc[m] < -tol)) / pw[m].sum() * 100),
                     float(np.sum(pw[m] * d_pc[m]) / pw[m].sum())))
    return rows


def summary(hh, lines, kappa=1.0):
    """Headline distribution indicators from a computed hh frame. lines: {name: (z, var)}
    where var is 'c' (DSK consumption aggregate x kappa) or 'y' (income per capita)."""
    w, n = hh["w"].to_numpy(), hh["n"].to_numpy()
    pw = w * n
    y, c = hh["y_pc"].to_numpy(), hh["c_pc"].to_numpy()
    out = {"mean_income_pc": float(np.sum(pw * y) / pw.sum()),
           "median_income_pc": wquantile(y, pw, .5),
           "mean_cons_pc": float(np.sum(pw * c) / pw.sum()),
           "gini_income": gini(y, pw), "gini_cons": gini(c, pw)}
    for name, (z, var) in lines.items():
        x = c * kappa if var == "c" else hh["y_pc_real"].to_numpy()
        for a, lab in ((0, "headcount"), (1, "gap"), (2, "severity")):
            out[f"pov_{lab}_{name}"] = 100 * fgt(x, pw, z, a)
    return out
