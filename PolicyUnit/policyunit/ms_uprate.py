"""Static ageing of the calibrated household file to projection years (2025–2030) using the
MicroUnit baseline of the same vintage: FR1 average nominal wage, LFS employment,
unemployment rate and CPI; FR4 hired employees by NACE section. Weights are re-calibrated
(entropy, hard constraints) to the projected labour-market structure; incomes are uprated
(wages by FR1 wage index, other private incomes by the same index — assumption; pensions by
the legal indexation and, for years without a decree, by the rule 'previous-year wage
growth'); the DSK poverty line follows FR1 CPI. Read-only access to MicroUnit/output."""
from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from . import config
from . import ms_calib as C
from . import ms_policy as MP
from .ms_rawdata import SECTORS

POP_G, PENS_G = 0.005, 0.015          # [K] population and pensioner growth per year
# snapshot of MicroUnit Baseline (2026-10-06) used only if MicroUnit/output is unavailable
FALLBACK = {2024: (1009.4, 5029.8, 5.3, 182.689), 2025: (1102.9, 5105.2, 5.2, 192.189),
            2026: (1149.0, 5132.5, 5.18, 203.144), 2027: (1217.8, 5166.8, 5.05, 213.747),
            2028: (1283.8, 5200.4, 4.93, 223.361), 2029: (1354.5, 5234.8, 4.81, 232.868),
            2030: (1424.6, 5268.6, 4.69, 242.209)}
_BASE = {}


def microunit_baseline():
    if _BASE:
        return _BASE
    out = config.MICRO_ROOT / "output"
    f1, f4 = out / "FR1_accounts_long.csv", out / "FR4_hired_by_activity.csv"
    rows, meta = {}, {"source": "fallback snapshot 2026-10-06"}
    try:
        d = pd.read_csv(f1)
        d = d[d.scenario.isin(["ACTUAL", "Baseline"]) & (d.metric == "nominal")]
        piv = d.pivot_table(index="year", columns="key", values="value", aggfunc="last")
        h = pd.read_csv(f4)
        h = h[h.iloc[:, 0] == "Baseline"].set_index(h.columns[1])
        for y in range(2024, 2031):
            rows[y] = {"wage": piv.loc[y, "wage"], "emp": piv.loc[y, "emp"],
                       "unemp": piv.loc[y, "unemp"], "cpi": piv.loc[y, "cpi"],
                       "hired": {s: float(h.loc[y, s]) for s in SECTORS} if y in h.index
                       else None}
        meta = {"source": "MicroUnit/output FR1_accounts_long.csv + FR4_hired_by_activity.csv",
                "md5_fr1": hashlib.md5(f1.read_bytes()).hexdigest(),
                "md5_fr4": hashlib.md5(f4.read_bytes()).hexdigest()}
    except Exception as e:                                   # noqa: BLE001
        meta["warning_az"] = f"MikroUnit baza yolu oxunmadı ({type(e).__name__}); ehtiyat snapshot"
        rows = {y: {"wage": a, "emp": b, "unemp": c, "cpi": d_, "hired": None}
                for y, (a, b, c, d_) in FALLBACK.items()}
    hd = {}
    try:
        t = pd.read_csv(out / "FR1_forecast_tidy.csv")
        t = t[(t.id == "fr1:hhdisp_n") & t.scenario.isin(["ACTUAL", "Baseline"])]
        hd = {int(y): float(v) for y, v in zip(t.year, t.value) if y >= 2018}
    except Exception:                                        # noqa: BLE001
        pass
    _BASE["hhdisp"] = hd
    pen = {2024: 441.3, 2025: 496.6, 2026: 524.9, 2027: 557.0, 2028: 585.9, 2029: 614.8,
           2030: 643.0}                                   # FR1 snapshot (fallback)
    try:
        t = pd.read_csv(out / "FR1_forecast_tidy.csv")
        t = t[(t.id == "fr1:pension") & t.scenario.isin(["ACTUAL", "Baseline"])]
        pen.update({int(y): float(v) for y, v in zip(t.year, t.value) if y >= 2018})
        meta["pension_path"] = "MicroUnit FR1_forecast_tidy.csv fr1:pension (CPI-indeksli proqnoz)"
    except Exception:                                        # noqa: BLE001
        meta["pension_path"] = "ehtiyat snapshot (FR1 2026-10-06)"
    mw = {}
    try:
        t = pd.read_csv(out / "FR3_forecast_tidy.csv")
        t = t[(t.id == "fr3:minwage") & (t.scenario == "Baseline")]
        mw = {int(y): float(v) for y, v in zip(t.year, t.value)}
        meta["minwage_path"] = "MicroUnit FR3_forecast_tidy.csv fr3:minwage (Baseline)"
    except Exception:                                        # noqa: BLE001
        mw = {y: 424.0 * 1.06 ** (y - 2026) for y in range(2026, 2031)}
        meta["minwage_path"] = "ehtiyat: 424 AZN (2026) x 1,06/il"
    _BASE.update({"rows": rows, "meta": meta, "minwage": mw, "pension": pen})
    return _BASE


def baseline_params(year):
    """Params of the baseline for `year`: legal schedule where decreed; for years after the
    last decree the minimum wage follows the MicroUnit FR3 baseline path (same vintage)."""
    from .taxben import Params
    P = Params()
    last = int(P.t.loc[P.t.param == "minwage", "date"].dt.year.max())
    mw = microunit_baseline()["minwage"].get(int(year))
    ov = {}
    if year > last and mw:
        ov["minwage"] = {"set": mw}
    lastn = int(P.t.loc[P.t.param == "need_criterion", "date"].dt.year.max())
    B = microunit_baseline()["rows"]
    if year > lastn and year in B and lastn in B:       # [assumption] real value held (CPI)
        ov["need_criterion"] = {"set": P.get("need_criterion", lastn) * B[year]["cpi"]
                                / B[lastn]["cpi"]}
    return (P.with_overrides(ov), True) if ov else (P, False)


def project(p, cal, T, year):
    """Return (p with projected weights, cal with uprate factors) for `year`.
    p: prepared base file (ms_policy.prepare); T: base-year targets (ms_targets.load)."""
    b = int(cal["base_year"])
    if year == b:
        return p, cal
    B = microunit_baseline()["rows"]
    rb, ry = B[b], B[year]
    k = year - b
    wi = ry["wage"] / rb["wage"]
    HD = microunit_baseline().get("hhdisp", {})
    # other private incomes: FR1 nominal disposable income per capita (smoother than wages)
    oi = HD[year] / HD[b] / (1 + POP_G) ** (year - b) if b in HD and year in HD else wi
    cal = {**cal, "uprate": {**cal.get("uprate", {}),
                             str(year): {"wage": wi, "other": oi, "cons": 1.0,
                                         "cpi": ry["cpi"] / rb["cpi"]}}}
    PB = microunit_baseline().get("pension", {})
    if b in PB and year in PB:                  # FR1 convention: average pension index (CPI)
        cal["uprate"][str(year)]["pension"] = PB[year] / PB[b]
    proj = dict(cal.get("pension_index_proj", {}))
    for y in range(b + 1, year + 1):
        if (y - 1) in B and (y - 2) in B:
            proj[str(y)] = 100 * (B[y - 1]["wage"] / B[y - 2]["wage"] - 1)
    cal["pension_index_proj"] = proj
    cal["pov_line_year"] = cal.get("pov_line", T["pov_line"]) * ry["cpi"] / rb["cpi"]
    cnt = dict(T["counts"])
    pf = (1 + POP_G) ** k
    hired_b = sum(cnt[f"hired:{s}"] for s in SECTORS)
    if ry["hired"] and rb["hired"] is None and b == 2024:
        rb = {**rb, "hired": {s: cnt[f"hired:{s}"] / 1e3 for s in SECTORS}}
    for s in SECTORS:
        if ry["hired"] and rb["hired"]:
            cnt[f"hired:{s}"] *= ry["hired"][s] / rb["hired"][s]
        else:
            cnt[f"hired:{s}"] *= ry["emp"] / rb["emp"]
    hired_y = sum(cnt[f"hired:{s}"] for s in SECTORS)
    own = (ry["emp"] * 1e3 - hired_y) / (rb["emp"] * 1e3 - hired_b)
    cnt.update({"pop": cnt["pop"] * pf, "urban": cnt["urban"] * pf,
                "children": cnt["children"] * pf, "pensioners": cnt["pensioners"] * (1 + PENS_G) ** k,
                "hired_state": cnt["hired_state"] * hired_y / hired_b,
                "wagebill_state": cnt["wagebill_state"] * hired_y / hired_b,
                "wagebill_nonstate": cnt["wagebill_nonstate"] * hired_y / hired_b,
                "agri_own": cnt["agri_own"] * own, "selfemp_own": cnt["selfemp_own"] * own,
                "unemployed": ry["unemp"] / (100 - ry["unemp"]) * ry["emp"] * 1e3})
    X, tg, keys = C.design(p, {**T, "counts": cnt})
    d = MP.hh_first(p, "weight")
    w, err = C.entropy_weights(X, tg, d)
    q = p.copy()
    q["weight"] = w[q["_h"].to_numpy()]
    cal["projection_weight_err"] = err
    # consumption: each household keeps its base-year propensity (c/y) — own income growth
    from .taxben import Params
    yb = MP.compute(p, {**cal, "uprate": {}}, b, Params())[0]["y_total"].to_numpy()
    yt = MP.compute(q, cal, year, baseline_params(year)[0])[0]["y_total"].to_numpy()
    r = np.clip(yt / np.maximum(yb, 1.0), 0.5, 2.0)[q["_h"].to_numpy()]
    for c in MP.CATS:
        q[f"cons_{c}"] = q[f"cons_{c}"] * r
    return q, cal
