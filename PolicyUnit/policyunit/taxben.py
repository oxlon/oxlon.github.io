"""Tax-benefit calculator of the household microsimulation (FR3, MİİS §15.5.4).

Rules are read from config/tax_benefit.csv (dated, sourced). Monthly amounts in AZN.
Annual convention: the value of a parameter for a year is the AVERAGE of the values in force
on the 1st day of each of the 12 months (e.g. minimum wage 2019 = (2x130 + 6x180 + 4x250)/12),
consistent with the MicroUnit FR1 annual-average convention for dated DSK schedules.
Static first-round calculator: no behavioural response here (see ms_policy for the optional
labelled behavioural layer)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TB_CSV = ROOT / "config" / "tax_benefit.csv"


class Params:
    """Dated parameter table with optional scenario overrides.

    overrides: {param: {"pct": x} | {"add": x} | {"set": x} | {"mult": x}}, applied to
    every year >= override_from (default: all years)."""

    def __init__(self, path=TB_CSV, overrides=None, override_from=None):
        t = pd.read_csv(path, dtype={"valid_from": str})
        t["date"] = pd.to_datetime(t["valid_from"])
        self.t = t.sort_values("date")
        self.overrides = dict(overrides or {})
        self.override_from = override_from

    def with_overrides(self, overrides, override_from=None):
        p = Params.__new__(Params)
        p.t, p.override_from = self.t, override_from
        p.overrides = {**self.overrides, **(overrides or {})}
        return p

    def _rows(self, param, regime):
        r = self.t[self.t.param == param]
        sub = r[r.regime == regime]
        return sub if len(sub) else r[r.regime == "all"]

    def at(self, param, date, regime="all", default=np.nan):
        r = self._rows(param, regime)
        r = r[r.date <= pd.Timestamp(date)]
        return float(r.value.iloc[-1]) if len(r) else default

    def get(self, param, year, regime="all", how="avg", default=np.nan):
        months = [12] if how == "dec" else ([1] if how == "jan" else range(1, 13))
        vals = [self.at(param, f"{int(year)}-{m:02d}-01", regime, default) for m in months]
        v = float(np.mean(vals)) if all(np.isfinite(vals)) else (
            vals[-1] if np.isfinite(vals[-1]) else default)
        ov = self.overrides.get(f"{param}@{regime}", self.overrides.get(param))
        if ov is not None and (self.override_from is None or year >= self.override_from):
            v = _apply(v, ov)
        return v


def _apply(v, ov):
    if isinstance(ov, (int, float)):
        return float(ov)
    if "set" in ov:
        return float(ov["set"])
    if "pct" in ov:
        v = v * (1 + ov["pct"] / 100.0)
    if "mult" in ov:
        v = v * ov["mult"]
    if "add" in ov:
        v = v + ov["add"]
    return v


def _band(x, lo, hi):
    return np.clip(x - lo, 0, max(hi - lo, 0) if np.isfinite(hi) else None)


def wage_taxes(gross, regime, P: Params, year):
    """Vectorised payroll taxes. regime: array of 'state' (state + oil/gas), 'priv'
    (non-oil non-state); anything else = untaxed (informal). Returns dict of arrays."""
    g = np.asarray(gross, float)
    reg = np.asarray(regime).astype(str)
    out = {k: np.zeros_like(g) for k in ("pit", "ssc_ee", "ssc_er", "ui_ee", "ui_er",
                                          "med_ee", "med_er")}
    for rg in ("state", "priv"):
        m = (reg == rg) & (g > 0)
        if not m.any():
            continue
        x = g[m]
        ex = P.get("pit_exempt", year, rg, default=0.0)
        cap = P.get("pit_exempt_cap", year, rg, default=np.inf)
        taxable = np.where(x <= cap, np.maximum(x - ex, 0), x)
        t1, t2 = P.get("pit_thr1", year, rg), P.get("pit_thr2", year, rg, default=np.inf)
        r1, r2 = P.get("pit_r1", year, rg), P.get("pit_r2", year, rg)
        r3 = P.get("pit_r3", year, rg, default=r2)
        out["pit"][m] = (r1 * _band(taxable, 0, t1) + r2 * _band(taxable, t1, t2)
                         + r3 * _band(taxable, t2, np.inf))
        ee, er = P.get("ssc_ee", year, rg), P.get("ssc_er", year, rg)
        thr = P.get("ssc_thr", year, rg, default=np.nan)
        if np.isfinite(thr):
            thr2 = P.get("ssc_thr2", year, rg, default=np.inf)
            ee_hi, er_hi = P.get("ssc_ee_hi", year, rg), P.get("ssc_er_hi", year, rg)
            er_top = P.get("ssc_er_top", year, rg, default=er_hi)
            out["ssc_ee"][m] = ee * _band(x, 0, thr) + ee_hi * _band(x, thr, np.inf)
            out["ssc_er"][m] = (er * _band(x, 0, thr) + er_hi * _band(x, thr, thr2)
                                + er_top * _band(x, thr2, np.inf))
        else:
            out["ssc_ee"][m], out["ssc_er"][m] = ee * x, er * x
        out["ui_ee"][m] = P.get("ui_ee", year, default=0.0) * x
        out["ui_er"][m] = P.get("ui_er", year, default=0.0) * x
        mr = P.get("med_r", year, default=0.0)
        if mr > 0:
            mthr, mhi = P.get("med_thr", year, rg), P.get("med_r_hi", year, default=0.0)
            fac = P.get("med_priv_factor", year, rg, default=1.0) if rg == "priv" else 1.0
            med = fac * (mr * _band(x, 0, mthr) + mhi * _band(x, mthr, np.inf))
            out["med_ee"][m], out["med_er"][m] = med, med
    out["net"] = g - out["pit"] - out["ssc_ee"] - out["ui_ee"] - out["med_ee"]
    out["employer_cost"] = g + out["ssc_er"] + out["ui_er"] + out["med_er"]
    return out


def net_to_gross(net, regime, P: Params, year, iters=40):
    """Invert wage_taxes by bisection (for REAL HBS files that record net wages)."""
    net = np.asarray(net, float)
    lo, hi = net.copy(), net * 1.6 + 10
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        f = wage_taxes(mid, regime, P, year)["net"] - net
        lo, hi = np.where(f < 0, mid, lo), np.where(f < 0, hi, mid)
    return 0.5 * (lo + hi)


def apply_min_wage(gross, formal_ft, minwage, spill=0.0, spill_band=1.2):
    """Floor full-time formal wages at the minimum wage; optional spill-over for wages in
    [MW_old.. spill_band*MW]: share `spill` of the floor increase (labelled assumption)."""
    g = np.asarray(gross, float).copy()
    m = np.asarray(formal_ft, bool) & (g > 0)
    g[m] = np.maximum(g[m], minwage)
    return g


def min_wage_shift(gross, formal_ft, mw_old, mw_new, spill=0.0, spill_band=1.25, taper=False):
    """Wage change from moving the minimum wage mw_old -> mw_new (static, first round).
    Default = pure floor (no spill-over). Labelled option: formal full-time wages in
    [mw_new, spill_band*mw_new) get `spill` x (mw_new - mw_old) (core convention: 0.5, 1.25,
    no taper; taper=True lets the share fall linearly to 0 at the band top)."""
    g = np.asarray(gross, float).copy()
    m = np.asarray(formal_ft, bool) & (g > 0)
    new = g.copy()
    new[m] = np.maximum(g[m], mw_new)
    if spill > 0 and mw_new > mw_old:
        z = m & (g >= mw_new) & (g < spill_band * mw_new)
        w = 1 - (g[z] - mw_new) / ((spill_band - 1) * mw_new) if taper else 1.0
        new[z] = g[z] + spill * w * (mw_new - mw_old)
    return new


def pension_level(base, base_year, year, P: Params, extra_pct=0.0, proj=None):
    """Pension in `year` from a base-year amount: indexation path (config pension_index,
    January) + minimum pension floor + optional extra increase (policy)."""
    b = np.asarray(base, float)
    f = 1.0
    proj = proj or {}
    legal = set(P.t.loc[P.t.param == "pension_index", "date"].dt.year)

    def idx(y):                      # legal indexation if decreed, else projection rule
        return P.get("pension_index", y, how="jan") if y in legal else proj.get(str(y), 0.0)

    for y in range(int(base_year) + 1, int(year) + 1):
        f *= 1 + idx(y) / 100.0
    for y in range(int(year) + 1, int(base_year) + 1):          # back-casting
        f /= 1 + idx(y) / 100.0
    lvl = b * f * (1 + extra_pct / 100.0)
    floor = P.get("min_pension", year) * (1 + extra_pct / 100.0)
    return np.where(b > 0, np.maximum(lvl, floor), 0.0)


def utsy(income_hh, size, need, takeup, scale=1.0):
    """Targeted state social assistance: max(0, size*need - family income) (dsmf.gov.az),
    paid to eligible families with take-up flag; `scale` multiplies the payment."""
    gap = np.maximum(np.asarray(size, float) * need - np.asarray(income_hh, float), 0.0)
    elig = gap > 0
    return np.where(elig & np.asarray(takeup, bool), gap * scale, 0.0), elig
