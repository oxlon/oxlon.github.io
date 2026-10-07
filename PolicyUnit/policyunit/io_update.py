"""Update of the 2021 benchmark IOT to a recent year by GRAS (Junius-Oosterhaven 2003,
Lenzen et al. 2007 correction) using national-accounts margins.

Targets for year T (all nominal, mln AZN in sources, thousand AZN here):
  * sector gross output x_T: MicroUnit FR1 out_tot/out_oil/out_man/out_agr/out_con; other
    sectors from FR1 value-added growth of their FR1 group (va_*_n), then scaled so that the
    non-oil total equals out_nonoil_n;
  * sector VA_T: FR1 va_*_n by group, split with the benchmark within-group shares;
  * final demand by component: DSK 027en totals (hh, gov, npish, gfcf, dinv, exp), product
    structure of the benchmark (oil/gas exports scaled with out_oil); imports: 027en P.7 total;
  * intermediate column totals u_j = x_j - VA_j - tax_j; row totals v_i = x_i + m_i - f_i.
GRAS balances Z to (v, u); the NA inconsistency (sum v != sum u) is reported and absorbed in
changes in inventories (as in DSK practice for the statistical discrepancy).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import io_data as D

FR1_FILE = D.MP / "MicroUnit" / "output" / "FR1_annual_raw.csv"


def gras(Z0: np.ndarray, row_t: np.ndarray, col_t: np.ndarray, tol: float = 1e-7,
         maxit: int = 2000) -> tuple[np.ndarray, dict]:
    """Generalised RAS for matrices with negative entries. Z = diag(r) P diag(s) -
    diag(1/r) N diag(1/s), P/N = positive/negative parts of Z0."""
    P = np.where(Z0 > 0, Z0, 0.0)
    N = np.where(Z0 < 0, -Z0, 0.0)
    m, n = Z0.shape
    r, s = np.ones(m), np.ones(n)

    def solve(p, q, t):
        # root of p*z - q/z = t  (z > 0)
        out = np.ones_like(t)
        pos = p > 0
        out[pos] = (t[pos] + np.sqrt(t[pos] ** 2 + 4 * p[pos] * q[pos])) / (2 * p[pos])
        neg = (~pos) & (q > 0) & (t < 0)
        out[neg] = -q[neg] / t[neg]
        return np.clip(out, 1e-9, 1e9)
    it, err = 0, np.inf
    scale = max(np.abs(row_t).max(), 1.0)
    for it in range(1, maxit + 1):
        r = solve(P @ s, N @ (1 / s), row_t)
        s = solve(P.T @ r, N.T @ (1 / r), col_t)
        Z = r[:, None] * P * s[None, :] - (1 / r)[:, None] * N * (1 / s)[None, :]
        err = max(np.abs(Z.sum(1) - row_t).max(), np.abs(Z.sum(0) - col_t).max()) / scale
        if err < tol:
            break
    return Z, {"iterations": it, "max_rel_resid": float(err), "converged": bool(err < tol)}


def fr1_margins() -> pd.DataFrame:
    if not FR1_FILE.exists():
        raise FileNotFoundError(f"{FR1_FILE} tapılmadı (MicroUnit FR1 çıxışı)")
    return pd.read_csv(FR1_FILE).set_index("year")


def targets(base: D.IOT, year: int) -> dict:
    """Output, VA and final-demand targets for `year` (thousand AZN) on base classification."""
    fr = fr1_margins()
    sec = D.sectors().set_index("code").reindex(base.codes)
    g = sec["fr1_group"].to_numpy()
    b0, b1 = fr.loc[base.year], fr.loc[year]
    x0 = base.x.copy()
    va0 = base.va.loc[D.VA_KEYS].sum(0).to_numpy()
    va_g = {k: b1[f"va_{k}_n"] / b0[f"va_{k}_n"] for k in set(g)}
    x = np.array([x0[j] * va_g[g[j]] for j in range(len(x0))])
    idx = {c: i for i, c in enumerate(base.codes)}
    man = [idx[c] for c in base.codes if sec.loc[c, "fr1_group"] == "man"]
    x[man] *= (b1["out_man_n"] * 1e3) / x[man].sum()
    x[idx["AGR"]] = b1["out_agr_n"] * 1e3
    x[idx["CONS"]] = b1["out_con_n"] * 1e3
    x[idx["OILGAS"]] = b1["out_oil_n"] * 1e3 - x[idx["PETR"]]
    fixed = set(man) | {idx["AGR"], idx["CONS"], idx["OILGAS"]}
    rest = [j for j in range(len(x)) if j not in fixed]
    x[rest] *= (b1["out_tot_n"] * 1e3 - x[list(fixed)].sum()) / x[rest].sum()
    va = np.zeros_like(x)
    for k in set(g):
        jj = np.where(g == k)[0]
        w = va0[jj] * x[jj] / x0[jj]
        va[jj] = w / w.sum() * b1[f"va_{k}_n"] * 1e3
    va = np.minimum(va, 0.97 * x)
    na = D.na_final_demand()
    fd0 = base.fd[D.FD_KEYS].copy()
    fd = fd0.copy()
    for k in ["hh", "gov", "npish", "gfcf", "dinv"]:
        tot0 = na.loc[base.year, k]
        if tot0 and np.isfinite(tot0) and abs(tot0) > 1:
            fd[k] = fd0[k] * na.loc[year, k] / tot0
    e = fd0["exp"].to_numpy().copy()
    io_ = idx["OILGAS"]
    e[io_] *= x[io_] / x0[io_]
    oth = [j for j in range(len(e)) if j != io_]
    e[oth] *= (na.loc[year, "exp"] * 1e3 - e[io_]) / e[oth].sum()
    fd["exp"] = e
    imp = base.imp * na.loc[year, "imp"] / na.loc[base.year, "imp"]
    return {"x": x, "va": va, "fd": fd, "imp": imp, "va_group_growth": va_g,
            "fd_na": na.loc[year].to_dict()}


def update(base: D.IOT, year: int = 2025) -> tuple[D.IOT, pd.DataFrame, dict]:
    """GRAS-updated IOT for `year` (aggregated classification recommended)."""
    T = targets(base, year)
    x, va, fd, imp = T["x"], T["va"], T["fd"], T["imp"]
    taxr = base.tax / base.x
    tax = taxr * x
    u = x - va - tax - base.cif
    f = fd[D.FD_KEYS].sum(axis=1).to_numpy()
    v_na = x + imp - f                       # row totals implied by NA final demand
    v0 = base.Z.sum(1) * x / np.where(base.x > 0, base.x, 1.0)   # prior: grows with output
    v = np.clip(v_na, 0.5 * v0, 2.0 * v0)    # bound implausible NA-implied rows
    disc = u.sum() - v.sum()
    v = v * u.sum() / v.sum()                # column/row grand totals must agree
    # implied final demand; the gap to the NA targets is booked as changes in inventories
    # (statistical discrepancy), reported by sector in the diagnostics
    f_new = x + imp - v
    fd["dinv"] = fd["dinv"].to_numpy() + (f_new - f)
    Z, info = gras(base.Z, v, u)
    va_df = base.va.copy()
    share = base.va.loc[D.VA_KEYS] / base.va.loc[D.VA_KEYS].sum(0)
    va_df.loc[D.VA_KEYS] = share.to_numpy() * va[None, :]
    t = D.IOT(year, list(base.codes), list(base.names), Z, fd, imp, tax, base.cif.copy(),
              va_df, x, {k: v_ * (fd[k].sum() / max(base.fd[k].sum(), 1.0))
                         for k, v_ in base.fd_tax.items()},
              dict(base.meta, updated_from=base.year, method="GRAS"))
    info.update({"na_discrepancy_thsd": float(disc), "na_discrepancy_pct_output":
                 float(disc / x.sum() * 100), "check": t.check()})
    diag = pd.DataFrame({"sector": base.codes, "x_base": base.x, "x_target": x,
                         "va_base": base.va.loc[D.VA_KEYS].sum(0).to_numpy(), "va_target": va,
                         "ic_col_target": u, "ic_row_target": v, "ic_col_result": Z.sum(0), "ic_row_na_implied": v_na,
                         "fd_na_target": f, "fd_result": f_new,
                         "ic_row_result": Z.sum(1)})
    return t, diag, info
