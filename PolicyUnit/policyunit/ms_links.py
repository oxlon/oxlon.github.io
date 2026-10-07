"""Macro/IO -> microsimulation linkage (top-down, first round).

* employment: sector changes of formal (hired) jobs from MicroUnit FR4 (`sector_hired:<s>`,
  preferred — coordinator rule) or from the IO engine (`io_emp:<io code>` aggregated to FR4
  sections) are imposed by exact *weight splitting*: every candidate household is split into a
  changed copy (weight share theta) and an unchanged copy (1 - theta). Entrants come from the
  unemployed (then inactive working-age persons) and receive a donor wage of the same sector;
  job losses move employees to unemployment. No random noise, totals exact.
* wages: average nominal wage change from MicroUnit FR1 (`wage_nominal`) — only for macro
  instruments (not when the instrument itself acts on wages in the microsimulation).
* prices: IO Leontief price model (`io_price:<code>`) mapped to the HBS consumption
  categories (basket incidence by decile)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .synth_households import BUDGET_SECTORS

# [assumption] consumption category -> IO product groups (weights)
CAT_IO = {"food": {"FOOD": .7, "AGR": .3}, "alc": {"FOOD": 1}, "tobacco": {"FOOD": 1},
          "clothing": {"LIGHT": .8, "TRADE": .2}, "housing": {"ENERGY": .5, "WATER": .15,
                                                             "REAL": .25, "CONS": .1},
          "furnish": {"MACH": .5, "LIGHT": .2, "METMIN": .1, "TRADE": .2},
          "health": {"HEALTH": .6, "CHEM": .4}, "transport": {"PETR": .4, "TRANS": .4, "MACH": .2},
          "comm": {"ICT": 1}, "recreation": {"OTHSERV": 1}, "education": {"EDU": 1},
          "restaurants": {"ACCOM": 1}, "misc": {"OTHSERV": .5, "FIN": .2, "CHEM": .3}}


def _io_to_fr4():
    try:
        t = pd.read_csv(config.IO_SECTORS_CSV, dtype=str, keep_default_na=False)
        return {r.code: [x for x in r.fr4_sector_map.split(";") if x] for r in t.itertuples()}
    except Exception:                                           # noqa: BLE001
        return {}


def from_ctx(ctx, year):
    """Extract linkage signals for `year` from engine results already in ctx."""
    out = {"hired_pct": {}, "wage_pct": None, "prices_pct": {}, "source": []}
    res = (ctx or {}).get("results", {}) if isinstance(ctx, dict) else {}
    mic = res.get("micro")
    if mic is not None and len(mic.frame):
        f = mic.frame[mic.frame.year == year]
        h = f[f.indicator.str.startswith("sector_hired:")]
        out["hired_pct"] = {i.split(":", 1)[1]: float(v) for i, v in zip(h.indicator, h.delta_pct)
                            if np.isfinite(v)}
        w = f[f.indicator == "wage_nominal"]
        if len(w) and np.isfinite(w.delta_pct.iloc[0]):
            out["wage_pct"] = float(w.delta_pct.iloc[0])
        if out["hired_pct"]:
            out["source"].append("MikroUnit FR4 (muzdlu işçilər)")
    io = res.get("io")
    if io is not None and len(io.frame):
        f = io.frame[io.frame.year == year]
        if not out["hired_pct"]:
            m = _io_to_fr4()
            e = f[f.indicator.str.startswith("io_emp:")]
            agg, base = {}, {}
            for i, d, b in zip(e.indicator, e.delta, e.baseline):
                secs = m.get(i.split(":", 1)[1], [])
                for s in secs:
                    agg[s] = agg.get(s, 0) + d / len(secs)
                    base[s] = base.get(s, 0) + b / len(secs)
            out["hired_pct"] = {s: 100 * agg[s] / base[s] for s in agg if base[s]}
            if agg:
                out["source"].append("IO məşğulluq multiplikatoru")
        pr = f[f.indicator.str.startswith("io_price:")]
        dp = {i.split(":", 1)[1]: float(v) for i, v in zip(pr.indicator, pr.delta_pct)
              if np.isfinite(v)}
        if dp:
            out["prices_pct"] = {c: sum(wt * dp.get(k, 0.0) for k, wt in m_.items())
                                 for c, m_ in CAT_IO.items()}
            out["source"].append("IO Leontief qiymət modeli")
    return out


def _split(p, sel_person, target, change):
    """Duplicate households of selected persons: copy A (weight*theta) gets `change` for one
    selected person per household; theta = target / weight of those persons (exact)."""
    hh_sel = p.loc[sel_person, "hh_id"].unique()
    first = p[sel_person].groupby("hh_id").head(1).index        # one person per household
    theta = min(1.0, target / max(float(p.loc[first, "weight"].sum()), 1e-9))
    a = p[p.hh_id.isin(hh_sel)].copy()
    a["weight"] = a["weight"] * theta
    a["hh_id"] = a["hh_id"] + "s"
    a["person_id"] = a["person_id"] + "s"
    idx = a.index.isin(first)
    a.loc[idx] = change(a.loc[idx])
    p = p.copy()
    p.loc[p.hh_id.isin(hh_sel), "weight"] *= (1 - theta)
    return pd.concat([p, a], ignore_index=True)


def switch_employment(p, hired_pct, seed=7, min_pct=0.01):
    """Impose formal-job changes by sector (dict sector -> %); returns a new person frame.
    Losses: sector by sector (only households with employees of that sector are split).
    Gains: ONE split of the candidate households into one copy per gaining sector (weight
    share theta_s = jobs_s / candidate weight) — no repeated duplication."""
    rng = np.random.default_rng(seed)
    q = p.drop(columns=[c for c in ("_h", "_first") if c in p.columns]).copy()
    gains = {}
    for s, pct in sorted(hired_pct.items()):
        if not pct or not np.isfinite(pct) or abs(pct) < min_pct:
            continue
        emp = (q.status == "employee") & (q.sector == s)
        dlt = pct / 100.0 * float(q.loc[emp, "weight"].sum())
        if abs(dlt) < 1:
            continue
        if dlt > 0:
            gains[s] = (dlt, q.loc[emp & q.formal_ft.eq(1), "wage_gross"].to_numpy())
            continue
        ch = lambda x: x.assign(status="unemployed", wage_gross=0.0, formal_ft=0,
                                ownership="", regime="", budget=0)
        q = _split(q, emp & q.formal_ft.eq(1), -dlt, ch)
    if not gains:
        return q
    sel = q.status.eq("unemployed")
    first = q[sel].groupby("hh_id").head(1).index
    tot = sum(d for d, _ in gains.values())
    if tot > q.loc[first, "weight"].sum():
        sel = sel | (q.status.eq("inactive") & q.age.between(18, 60))
        first = q[sel].groupby("hh_id").head(1).index
    pool = float(q.loc[first, "weight"].sum())
    k = min(1.0, pool / tot)                        # cap: cannot exceed the candidate pool
    hh_sel = q.loc[first, "hh_id"].unique()
    part = q[q.hh_id.isin(hh_sel)]
    copies = []
    for j, (s, (d, donors)) in enumerate(sorted(gains.items())):
        a = part.copy()
        a["weight"] = a["weight"] * (k * d / pool)
        a["hh_id"] = a["hh_id"] + "s" * (j + 1)
        a["person_id"] = a["person_id"] + "s" * (j + 1)
        idx = a.index.isin(first)
        own = "state" if s in BUDGET_SECTORS else "nonstate"
        a.loc[idx, ["status", "sector", "ownership", "regime"]] = [
            "employee", s, own, "state" if own == "state" else "priv"]
        a.loc[idx, "budget"] = int(own == "state")
        a.loc[idx, "formal_ft"] = 1
        a.loc[idx, "wage_gross"] = rng.choice(donors, idx.sum()) if len(donors) else 500.0
        copies.append(a)
    q.loc[q.hh_id.isin(hh_sel), "weight"] *= (1 - k * tot / pool)
    return pd.concat([q] + copies, ignore_index=True)
