"""NFR1 validation of the IO engine.

(a) Coefficient stability back-test: project year-T sector outputs with the Leontief inverse
    of an earlier benchmark table and the OBSERVED year-T domestic final demand
    (2016 -> 2021, also 2011 -> 2016). Benchmark: naive proportional scaling of the earlier
    output vector by total final-demand growth. Nominal values (relative prices change
    between benchmarks; this is part of the error and is reported as such).
(b) Event E7 — Tariff Council decision of 30.06.2024: AI-92 1.00 -> 1.10 AZN/l (+10 %),
    diesel 0.80 -> 1.00 AZN/l (+25 %); AI-95 market price cut to 1.60 (-20 %, 15.07.2024);
    same day: Baku bus fare 0.40 -> 0.50 (+25 %), metro 0.40 -> 0.50 (+25 %); Absheron refuse
    collection 0.30 -> 0.70 AZN/person (x2.33). Observed: DSK 001_5en (Dec 2024 / Dec 2023 CPI
    by item). Counterfactual for "excess" inflation: the same item's Dec/Dec rate in 2023
    (naive no-policy benchmark). Tier D (model) vs observed; annual data only (monthly DSK CPI
    by item not available as a machine-readable series — see docs).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import io_data as D
from . import io_models as M

# ---- E7 shock specification (assumption weights: docs/Metodologiya_IO.md §6)
E7 = {
    # value shares in domestic (intermediate+final) use of CPA 19 refined products
    "fuel_mix_use": {"ai92": 0.45, "diesel": 0.30, "ai95": 0.05, "other": 0.20},
    # household motor-fuel spending mix
    "fuel_mix_hh": {"ai92": 0.85, "diesel": 0.05, "ai95": 0.10},
    "dp": {"ai92": 0.10, "diesel": 0.25, "ai95": -0.20, "other": 0.0},
    "fare": 0.25, "fare_share_trans_hh": 0.35,     # urban bus+metro in HH transport spending
    "refuse": 4.0 / 3.0, "refuse_share_water_hh": 0.20,
}


def _mix(mix, dp):
    return sum(w * dp.get(k, 0.0) for k, w in mix.items())


def stability(base_year: int, target_year: int) -> tuple[pd.DataFrame, dict]:
    mb = M.build(base_year)
    mt = M.build(target_year)
    f_t = mt.fdd.sum(axis=1).to_numpy()
    x_hat = mb.L @ f_t
    x_obs = mt.x
    f_b = mb.fdd.sum(axis=1).to_numpy()
    x_naive = mb.x * f_t.sum() / f_b.sum()
    df = pd.DataFrame({"sector": mt.codes, "x_obs_mln": x_obs / 1e3, "x_io_mln": x_hat / 1e3,
                       "x_naive_mln": x_naive / 1e3})
    df["err_io_pct"] = (df.x_io_mln / df.x_obs_mln - 1) * 100
    df["err_naive_pct"] = (df.x_naive_mln / df.x_obs_mln - 1) * 100
    w = x_obs / x_obs.sum()

    def summ(col_pct, col_lvl):
        e = df[col_pct].to_numpy()
        lv = (df[col_lvl] - df.x_obs_mln).to_numpy()
        return {"rmse_mln": float(np.sqrt(np.mean(lv ** 2))), "mape": float(np.mean(np.abs(e))),
                "wmape": float(np.sum(w * np.abs(e))), "median_ape": float(np.median(np.abs(e))),
                "total_err_pct": float((df[col_lvl].sum() / df.x_obs_mln.sum() - 1) * 100)}
    s_io, s_nv = summ("err_io_pct", "x_io_mln"), summ("err_naive_pct", "x_naive_mln")
    df.insert(0, "pair", f"{base_year}->{target_year}")
    summary = {"pair": f"{base_year}->{target_year}", "n_sectors": len(df),
               **{f"io_{k}": v for k, v in s_io.items()},
               **{f"naive_{k}": v for k, v in s_nv.items()},
               "io_beats_naive_wmape": s_io["wmape"] < s_nv["wmape"]}
    return df, summary


def _observed_cpi() -> pd.DataFrame:
    x = D.read_sheet(D.fetch("001_5en.xlsx"))
    hdr = next(i for i in range(10) if any(_y(v) == 2024 for v in x.iloc[i]))
    cols = {_y(v): j for j, v in enumerate(x.iloc[hdr]) if _y(v)}
    rows = []
    for i in range(hdr + 1, x.shape[0]):
        name = D._txt(x.iat[i, 1])
        if name:
            rows.append({"item": name, **{y: D._num(x.iat[i, j]) for y, j in cols.items()}})
    return pd.DataFrame(rows).set_index("item")


def _y(v):
    try:
        f = float(v)
        return int(f) if 1990 < f < 2100 else None
    except (TypeError, ValueError):
        return None


def _obs(cpi, key):
    m = [i for i in cpi.index if i.lower().startswith(key.lower())]
    return cpi.loc[m[0]] if m else None


def e7_fuel(year_table: int = 2021, mix_use=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Price-model prediction for the June-2024 package vs DSK Dec/Dec 2024 CPI items."""
    m = M.build(year_table)
    sup = D.aggregate_supply(D.load_supply(year_table))
    w = m.cpi_weights(sup)
    dp_use = _mix(mix_use or E7["fuel_mix_use"], E7["dp"])
    dp_hh = _mix(E7["fuel_mix_hh"], E7["dp"])
    # (1) fuel only
    pr = m.price(exog={"PETR": dp_use})
    c_fuel = m.cpi_effect(pr, w, exog_retail={"PETR": dp_hh})
    # (2) full regulated package: fares + refuse collection on household purchases
    tr = c_fuel["TRANS"]
    wa = c_fuel["WATER"]
    trans_hh = E7["fare_share_trans_hh"] * E7["fare"] + (1 - E7["fare_share_trans_hh"]) * tr
    water_hh = E7["refuse_share_water_hh"] * E7["refuse"] + (1 - E7["refuse_share_water_hh"]) * wa
    c_pack = m.cpi_effect(pr, w, exog_retail={"PETR": dp_hh, "TRANS": trans_hh, "WATER": water_hh})
    food = ["AGR", "FOOD"]
    nonfood = [c for c in m.codes if c not in food]
    wn = w.loc[nonfood, "w"]

    def grp(c):
        return float((c[nonfood] * wn).sum() / wn.sum())
    cpi = _observed_cpi()

    def ex(key):
        r = _obs(cpi, key)
        return (r[2024] - 100, r[2023] - 100) if r is not None else (np.nan, np.nan)
    rows = []

    def add(ind, label, pred, key, naive=0.0, note="", regulated=False):
        # counterfactual: regulated item -> 0 (no change without a decision);
        # market item / group -> the same item's 2023 Dec/Dec rate
        o24, o23 = ex(key)
        obs_ex = o24 if regulated else o24 - o23
        rows.append({"indicator": ind, "label_az": label, "observed_2024_pct": o24,
                     "observed_2023_pct": o23, "observed_excess_pp": obs_ex,
                     "counterfactual": "0 (tənzimlənən)" if regulated else "2023 artımı",
                     "model_pct": pred * 100, "naive_pct": naive,
                     "deviation_pp": pred * 100 - obs_ex,
                     "rel_deviation": abs(pred * 100 - obs_ex) / abs(obs_ex) if obs_ex else np.nan,
                     "sign_match": bool(np.sign(pred) == np.sign(obs_ex)),
                     "model_better_than_naive": abs(pred * 100 - obs_ex) < abs(naive - obs_ex),
                     "note_az": note})
    add("fuel_item", "İQİ: yanacaq məhsulları", dp_hh, "Fuel products",
        note="birbaşa: ev təsərrüfatı yanacaq qarışığı (AI-92 85 %, dizel 5 %, AI-95 10 %)",
        regulated=True)
    add("auto_passenger", "İQİ: avtomobil sərnişin nəqliyyatı", trans_hh, "Passenger transportation service by auto",
        note="paket: avtobus gediş haqqı +25 % (çəki 0,35) + yanacaq xərcinin dolayı ötürülməsi; "
        "2023-də də +18,4 % (şəhərlərarası tariflər) — tam izah olunmur", regulated=True)
    add("other_transport", "İQİ: digər nəqliyyat xidmətləri", tr, "Other transport services",
        note="yalnız yanacağın dolayı təsiri (IO qiymət modeli, TRANS sektoru)")
    add("refuse", "İQİ: zibil yığılması xidməti", E7["refuse"], "Refuse collection",
        note="tənzimlənən tarif x2,33 (Abşeron) — birbaşa, ölçü yoxlaması", regulated=True)
    add("nonfood_group_fuel", "İQİ: qeyri-ərzaq mallar və xidmətlər (yalnız yanacaq)", grp(c_fuel),
        "Non-food products, services", note="qrup çəkiləri IO ev təsərrüfatı səbətindən")
    add("nonfood_group_pack", "İQİ: qeyri-ərzaq mallar və xidmətlər (tam paket)", grp(c_pack),
        "Non-food products, services", note="digər şoklar (telefon +27,6 %, aviabilet +26,3 %) modeldə yoxdur")
    add("cpi_total_pack", "Ümumi İQİ (tam paket)", c_pack["CPI"], "Total goods and services",
        note="ərzaq inflyasiyasının sürətlənməsi (0,8 → 5,5 %) siyasətlə bağlı deyil")
    dev = pd.DataFrame(rows)
    sect = pd.DataFrame({"sector": m.codes, "dp_fuel_only_pct": pr["dp"] * 100,
                         "cpi_item_fuel_only_pct": c_fuel[m.codes].to_numpy() * 100,
                         "cpi_item_package_pct": c_pack[m.codes].to_numpy() * 100,
                         "cpi_weight": w["w"].to_numpy()})
    meta = {"dp_PETR_use": dp_use, "dp_PETR_hh": dp_hh, "cpi_fuel_only": c_fuel["CPI"],
            "cpi_package": c_pack["CPI"]}
    sect.attrs.update(meta)
    return dev, sect


def e7_sensitivity() -> pd.DataFrame:
    rows = []
    for name, mix in {"baza": E7["fuel_mix_use"],
                      "dizel_yüksək": {"ai92": 0.35, "diesel": 0.45, "ai95": 0.05, "other": 0.15},
                      "benzin_yüksək": {"ai92": 0.55, "diesel": 0.20, "ai95": 0.05, "other": 0.20},
                      "digər_yüksək": {"ai92": 0.35, "diesel": 0.20, "ai95": 0.05, "other": 0.40}}.items():
        for yr in (2016, 2021):
            dev, sect = e7_fuel(yr, mix)
            rows.append({"variant": name, "table": yr, "dp_PETR_pct": sect.attrs["dp_PETR_use"] * 100,
                         "cpi_fuel_only_pp": sect.attrs["cpi_fuel_only"] * 100,
                         "cpi_package_pp": sect.attrs["cpi_package"] * 100,
                         "other_transport_pct": float(dev.loc[dev.indicator == "other_transport",
                                                              "model_pct"].iloc[0])})
    return pd.DataFrame(rows)
