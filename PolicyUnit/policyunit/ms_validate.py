"""NFR1 retrospective validation of the microsimulation (deviation report).

E1+E2 "2019 package" simulated on the 2018-calibrated SYNTHETIC population (calibrated only
to 2018 DSK aggregates — 2019/2020 outcomes are NOT used => out-of-sample for the changes):
minimum wage 130 -> 180 (Mar) -> 250 (Sep), minimum pension 116 -> 160 -> 200, ÜSY need
criterion 130 -> 143, PIT exemption <= 8000 AZN and new social-contribution scheme in the
non-oil private sector. Counterfactual = 2018 rules in 2019 (pension indexation by rule in both).
E3 2025 minimum wage 345 -> 400 vs the DSK Nov-2025 wage-band distribution (004_12).
In-sample checks (2024 / 2018 calibration) are in V_microsim_calibration_<year>.csv.

    python3 -m policyunit.ms_validate"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import catalog, ms_build
from . import ms_metrics as M
from . import ms_policy as MP
from . import ms_targets as MT
from .taxben import Params

CF2018 = {"minwage": {"set": 130}, "min_pension": {"set": 116}, "need_criterion": {"set": 130},
          "pit_r1@priv": {"set": .14}, "pit_r2@priv": {"set": .25}, "pit_r3@priv": {"set": .25},
          "pit_exempt@priv": {"set": 173}, "pit_exempt@state": {"set": 173},
          "pit_exempt_cap@state": {"set": np.inf}, "ssc_thr@priv": {"set": np.nan}}
END2019 = {"minwage": {"set": 250}, "min_pension": {"set": 200}}
# observed (DSK; inv_requirements §5, e002, 5.4): 2019 vs 2018 and 2020 vs 2018
OBS = {"wage_avg": (16.6, 29.9), "wage_state": (22.1, 45.0), "wage_nonstate": (11.2, 16.1),
       "hbs_employment_pc": (7.5, 12.7), "hbs_pensions_pc": (9.8, 28.1),
       "hbs_benefits_pc": (25.0, 53.3), "hbs_total_pc": (6.0, 5.6), "poverty_rate": (-0.3, 1.1),
       "nonstate_employees": (9.4, 17.9)}
NAIVE = {"wage_avg": 3.0, "wage_state": 10.1, "wage_nonstate": -2.9, "hbs_employment_pc": 3.2,
         "hbs_pensions_pc": 5.0, "hbs_benefits_pc": 17.6, "hbs_total_pc": 2.8,
         "poverty_rate": -0.3, "nonstate_employees": 3.2}      # 2017->2018 change (trend)
ETA_FORMAL = 0.7      # [assumption] formal-employment elasticity to the net-of-wedge ratio


def _load2018():
    p = ms_build.WORK / "PU_households_SYNTHETIC_2018.csv"
    c = ms_build.WORK / "PU_households_calibration_2018.json"
    if not (p.exists() and c.exists()):
        c24 = json.loads(ms_build.hh_data.CAL_JSON.read_text())
        p18, cal, _ = ms_build.build(2018, p_takeup=c24["p_takeup"],
                                     takeup_gamma=c24.get("takeup_gamma"))
        return MP.prepare(p18), cal
    df = pd.read_csv(p, keep_default_na=False, low_memory=False)
    for col in ("sector", "ownership", "regime", "pension_type"):
        df[col] = df[col].astype(str).replace("nan", "")
    return MP.prepare(df), json.loads(c.read_text())


def _stats(q, cal, year, P, base_y=None):
    hh, per = MP.compute(q, cal, year, P, {} if base_y is None else {"base_y": base_y})
    w, n = hh["w"].to_numpy(), hh["n"].to_numpy()
    pw = w * n
    e = (q.status == "employee").to_numpy()
    wq = q["weight"].to_numpy()
    out = {"wage_avg": np.average(per["gross"][e], weights=wq[e])}
    for o in ("state", "nonstate"):
        m = e & (q.ownership == o).to_numpy()
        out[f"wage_{o}"] = np.average(per["gross"][m], weights=wq[m])
    for s in ("employment", "pensions", "benefits", "total"):
        out[f"hbs_{s}_pc"] = np.sum(w * hh["y_total" if s == "total" else f"y_{s}"]) / pw.sum()
    out["poverty_rate"] = 100 * M.fgt(hh["c_pc"].to_numpy() * cal["kappa"], pw, cal["pov_line"], 0)
    m = e & (q.regime == "priv").to_numpy()
    out["_netcost_priv"] = np.average(per["net"][m] / per["employer_cost"][m], weights=wq[m])
    out["nonstate_employees"] = wq[e & (q.ownership == "nonstate").to_numpy()].sum() / 1e3
    out["_y"] = hh["y_total"].to_numpy()
    return out


def event_2019():
    q, cal = _load2018()
    P = Params()
    cf = _stats(q, cal, 2019, P.with_overrides(CF2018))
    rows = []
    for var, ov, k in (("2019 orta illik qaydalar", {}, 0), ("2019-un sonu səviyyələri (2020 ilə)",
                                                                END2019, 1)):
        po = _stats(q, cal, 2019, P.with_overrides(ov), cf["_y"])
        beh = 100 * ETA_FORMAL * (po["_netcost_priv"] / cf["_netcost_priv"] - 1)
        for ind, obs in OBS.items():
            if ind == "poverty_rate":
                mod = po[ind] - cf[ind]
            elif ind == "nonstate_employees":
                mod = 0.0
            else:
                mod = 100 * (po[ind] / cf[ind] - 1)
            o, nv = obs[k], NAIVE[ind] * (1 + k)
            rows.append({"event": "E1+E2 2019 paketi", "variant": var,
                         "compare_to": "2019 vs 2018" if k == 0 else "2020 vs 2018",
                         "indicator": ind, "observed": o, "model_static": round(mod, 3),
                         "model_behavioural": round(beh, 3) if ind == "nonstate_employees" else np.nan,
                         "naive_trend": nv, "model_plus_trend": round(mod + nv, 3),
                         "beats_naive_combined": bool(abs(mod + nv - o) < abs(nv - o)),
                         "dev": round(mod - o, 3),
                         "rel_dev_pct": round(100 * abs(mod - o) / abs(o), 1) if o else np.nan,
                         "sign_ok": bool(np.sign(mod) == np.sign(o)) if mod else False,
                         "beats_naive": bool(abs(mod - o) < abs(nv - o)),
                         "sample": "out-of-sample (2018 kalibrləməsi)",
                         "unit": "f.b." if ind == "poverty_rate" else "%"})
    return pd.DataFrame(rows)


def event_2025_mw():
    """E3: floor 345 -> 400 on the 2024 file vs DSK Nov-2025 wage bands (fully worked)."""
    from . import hh_data
    p, cal, _ = hh_data.load()
    q = MP.prepare(p)
    e = (q.status == "employee") & (q.formal_ft == 1)
    w = q.loc[e, "weight"].to_numpy()
    g24 = q.loc[e, "wage_gross"].to_numpy()
    b = pd.read_csv(MT.TARGETS / "wage_bands.csv")
    obs = lambda y, hi: 100 * b[(b.year == y) & (b.hi <= hi)]["count"].sum() / b[b.year == y]["count"].sum()
    rows = []
    for drift, lab in ((0.0, "yalnız minimum əmək haqqı"), (5.6, "+ qeyri-siyasi artım 5,6 % (İQİ 2025)")):
        g25 = np.maximum(g24 * (1 + drift / 100), 400.0)
        for hi, nm in ((500, "işçilərin payı < 500 AZN"), (600, "işçilərin payı < 600 AZN")):
            mod = 100 * w[g25 <= hi].sum() / w.sum()
            o = obs(2025, hi)
            rows.append({"event": "E3 2025 MƏH 345→400", "variant": lab, "compare_to": "noyabr 2025",
                         "indicator": nm, "observed": round(o, 2), "model_static": round(mod, 2),
                         "naive_trend": round(obs(2024, hi), 2), "dev": round(mod - o, 2),
                         "rel_dev_pct": round(100 * abs(mod - o) / o, 1),
                         "beats_naive": bool(abs(mod - o) < abs(obs(2024, hi) - o)),
                         "sample": "out-of-sample (2024 paylanması → 2025)", "unit": "%"})
        mod = 100 * (np.average(g25, weights=w) / np.average(g24, weights=w) - 1)
        rows.append({"event": "E3 2025 MƏH 345→400", "variant": lab, "compare_to": "2025 vs 2024",
                     "indicator": "orta əmək haqqı (%)", "observed": 9.3, "model_static": round(mod, 2),
                     "naive_trend": 8.1, "dev": round(mod - 9.3, 2),
                     "rel_dev_pct": round(100 * abs(mod - 9.3) / 9.3, 1),
                     "beats_naive": bool(abs(mod - 9.3) < abs(8.1 - 9.3)),
                     "sample": "out-of-sample", "unit": "%"})
    return pd.DataFrame(rows)


def main():
    a, b = event_2019(), event_2025_mw()
    wm = "SİNTETİK — real ev təsərrüfatı məlumatı deyil. "
    catalog.write_csv(a, "V_microsim_2019_package.csv", "microsim", wm +
                      "NFR1: 2019 sosial paketi + vergi islahatı (E1+E2) — model vs fakt, sapma")
    catalog.write_csv(b, "V_microsim_2025_minwage.csv", "microsim", wm +
                      "NFR1: 2025 minimum əmək haqqı 345→400 — maaş intervalları (DSK 004_12)")
    s = pd.concat([a, b], ignore_index=True)
    summ = s.groupby(["event", "variant"]).agg(n=("indicator", "size"),
                                               sign_ok=("sign_ok", "mean"),
                                               beats_naive=("beats_naive", "mean"),
                                               beats_naive_comb=("beats_naive_combined", "mean"),
                                               median_rel_dev_pct=("rel_dev_pct", "median")).reset_index()
    catalog.write_csv(summ, "V_microsim_summary.csv", "microsim", wm +
                      "NFR1 mikrosimulyasiya sapma hesabatının xülasəsi")
    try:                                     # documentation numbers rendered from outputs
        from . import ms_docs
        ms_docs.render()
    except FileNotFoundError:
        pass
    return a, b, summ


if __name__ == "__main__":
    for t in main():
        print(t.to_string())
