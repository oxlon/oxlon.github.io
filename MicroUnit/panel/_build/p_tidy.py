"""p_tidy.py — v2 series records from output/FRx_forecast_tidy.csv + FRx_indicator_catalog.csv (stable ids).

Every catalog component becomes one record keyed by its stable id `fr<k>:<code>`:
  i id · f module · g group_az · e label_az · u unit_az · k kind (level|rate|share|index)
  s {B|A|R: [2026..2030]} · gr growth (% for level/index, change in p.p. for rate/share)
  q {B: [[lo5], [hi95]]} band · h [[year, value, imputed 0|1], ...] history ≤ 2025
  b 2025 value · b25 {A|R: v} when 2025 is a scenario-dependent nowcast · nc 1 when 2025 is a nowcast
  d decimals · eq equation ids · im {year: method_az} imputed points · src source csv:column
Completeness: every catalog component with has_forecast must have all of 2026–2030 in each of its scenarios.
"""
import math

import pandas as pd

from . import pcore as C

MODS = ["FR1", "FR3", "FR4", "FR5", "FR10", "FR12"]
SCK = {"Baseline": "B", "Adverse": "A", "Reform": "R"}
IMP_DEFAULT = "doldurulmuş (interpolyasiya)"


def _f(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) or math.isinf(v) else float(f"{v:.7g}")


def _dec(vals, kind):
    xs = [abs(v) for v in vals if v is not None]
    if not xs:
        return 1
    m = max(xs)
    if kind in ("rate", "share"):
        return 2 if m < 100 else 1
    return 0 if m >= 1000 else 1 if m >= 10 else 2 if m >= 0.1 else 4


def _growth(vals, prev0, kind):
    prev = [prev0] + vals[:-1]
    out = []
    for a, p in zip(vals, prev):
        if a is None or p is None:
            out.append(None)
        elif kind in ("rate", "share"):
            out.append(_f(a - p))
        else:
            out.append(None if p == 0 else _f((a / p - 1) * 100))
    return out


def _filled():
    """FR12_series_filled.csv: method_az of every imputed point (id, year)."""
    try:
        f = C.csv("FR12_series_filled.csv")
    except FileNotFoundError:
        return {}
    f = f[f.imputed.astype(str).str.lower() == "true"]
    return {(r.id, int(r.year)): str(r.method_az) for r in f.itertuples(index=False)}


def build_module(mod, filled, cov, errors):
    cat = C.csv(f"{mod}_indicator_catalog.csv", dtype=str, keep_default_na=False)
    t = C.csv(f"{mod}_forecast_tidy.csv")
    t["imputed"] = t.imputed.astype(str).str.lower() == "true"
    t["is_forecast"] = t.is_forecast.astype(str).str.lower() == "true"
    has_actual = (t.scenario == "ACTUAL").any()
    hist_src = t[(~t.is_forecast) & (t.scenario == ("ACTUAL" if has_actual else "Baseline"))]
    hist = {k: g.sort_values("year") for k, g in hist_src.groupby("id", sort=False)}
    fc = t[t.is_forecast & t.scenario.isin(list(SCK))]
    fcg = {k: g for k, g in fc.groupby("id", sort=False)}
    tidy_ids = set(t.id)
    recs, groups = [], []
    for r in cat.to_dict("records"):
        cid, kind = r["id"], r["kind"] or "level"
        if r["group_az"] not in groups:
            groups.append(r["group_az"])
        if cid not in tidy_ids:
            errors.append(f"{cid}: kataloqda var, forecast_tidy-də yoxdur")
            continue
        g = fcg.get(cid)
        scen = [s for s in (r["scenarios"] or "").split(";") if s in SCK]
        rec = {"i": cid, "f": mod, "g": r["group_az"], "e": r["label_az"], "u": r["unit_az"], "k": kind,
               "src": f"{r['source_csv']}:{r['source_column']}"}
        if r.get("equation_ids"):
            rec["eq"] = [x for x in r["equation_ids"].split(";") if x]
        hh = hist.get(cid)
        h, im = [], {}
        if hh is not None:
            for y, v, ip in zip(hh.year, hh.value, hh.imputed):
                v = _f(v)
                if v is None or int(y) > 2030:
                    continue
                h.append([int(y), v, 1 if ip else 0])
                if ip:
                    im[str(int(y))] = filled.get((cid, int(y)), IMP_DEFAULT)
        if h:
            rec["h"] = h
        if im:
            rec["im"] = im
        if str(r.get("has_forecast")).lower() != "true" or g is None:
            rec["nf"] = 1
            for s in scen or ["Baseline"]:
                cov.append({"fr": mod, "id": cid, "group": r["group_az"], "label": r["label_az"], "scenario": s,
                            "years_present": 0, "status": "proqnoz edilmir (not_forecast)"})
            recs.append(rec)
            continue
        s_, q, b25 = {}, {}, {}
        act = {y: v for y, v, _ in h if y >= C.YEARS[0]}      # observed points inside 2026–2030 (e.g. FR12 H1 2026)
        if act:
            rec["fa"] = sorted(act)
        for s in scen:
            gs = g[g.scenario == s].set_index("year")
            vals = [_f(gs.value.get(y)) if y in gs.index else act.get(y) for y in C.YEARS]
            s_[SCK[s]] = vals
            present = sum(v is not None for v in vals)
            st = ("OK" if not act else f"OK (faktiki: {', '.join(map(str, sorted(act)))})") if present == 5 else "İL ÇATIŞMIR"
            if present < 5:
                errors.append(f"{cid} [{s}]: {5 - present} il çatışmır")
            cov.append({"fr": mod, "id": cid, "group": r["group_az"], "label": r["label_az"], "scenario": s,
                        "years_present": present, "status": st})
            if 2025 in gs.index:
                b25[SCK[s]] = _f(gs.value.get(2025))
            lo = [_f(gs.lower_5.get(y)) if "lower_5" in gs else None for y in C.YEARS]
            hi = [_f(gs.upper_95.get(y)) if "upper_95" in gs else None for y in C.YEARS]
            if any(v is not None for v in lo + hi):
                q[SCK[s]] = [lo, hi]
        if not scen:
            errors.append(f"{cid}: kataloqda ssenari göstərilməyib")
        if b25:
            rec["nc"] = 1
            rec["b"] = b25.get("B", next(iter(b25.values())))
            diff = {k: v for k, v in b25.items() if k != "B" and v is not None and v != rec["b"]}
            if diff:
                rec["b25"] = diff
        else:
            h25 = [v for y, v, _ in h if y == 2025]
            if h25:
                rec["b"] = h25[0]
        rec["s"] = s_
        rec["gr"] = {k: _growth(v, b25.get(k, rec.get("b")), kind) for k, v in s_.items()}
        if q:
            rec["q"] = q
        rec["d"] = _dec([v for vs in s_.values() for v in vs] + [rec.get("b")], kind)
        recs.append(rec)
    extra = sorted(tidy_ids - set(cat.id))
    for cid in extra:
        errors.append(f"{cid}: forecast_tidy-də var, kataloqda yoxdur")
    return recs, groups


def build():
    filled = _filled()
    cov, errors, out, groups = [], [], {}, {}
    for m in MODS:
        out[m], groups[m] = build_module(m, filled, cov, errors)
    return out, groups, cov, errors
