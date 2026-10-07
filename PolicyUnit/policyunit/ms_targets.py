"""Calibration targets for the synthetic household file (DSK HBS/LFS aggregates, DSMF)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .ms_rawdata import SECTORS, TARGETS, CONS_KEYS

CATS = CONS_KEYS[1:]
CHILD_SHARE = 0.225          # [K] population aged 0-14 (DSK demography, approx.)


def _series(fname, year):
    t = pd.read_csv(TARGETS / fname)
    return t[t.year == year].set_index("key")["value"]


def decile_levels(kind, year):
    """Decile means (AZN p.c./month). 2024 = DSK table 25/53; other years = 2024 relative
    profile x that year's national mean (assumption — no decile tables cached)."""
    f = "income_deciles_2024.csv" if kind == "income" else "cons_deciles_2024.csv"
    t = pd.read_csv(TARGETS / f).pivot(index="decile", columns="key", values="value")
    if year == 2024:
        return t
    src = "hbs_income_sources.csv" if kind == "income" else "hbs_consumption.csv"
    r = _series(src, year)["total"] / _series(src, 2024)["total"]
    return t * r


def cons_shares(year):
    """Category shares by consumption decile (rows decile, cols CATS). food excludes alcohol
    (DSK 'food' includes alcoholic beverages; tobacco separate)."""
    t = pd.read_csv(TARGETS / "cons_deciles_2024.csv").pivot(index="decile", columns="key",
                                                             values="value")
    t["food"] = t["food"] - t["alc"]
    sh = t[CATS].div(t[CATS].sum(axis=1), axis=0)
    if year != 2024:
        a, b = _series("hbs_consumption.csv", year), _series("hbs_consumption.csv", 2024)
        a["food"], b["food"] = a["food"] - a["alc"], b["food"] - b["alc"]
        r = (a[CATS] / a[CATS].sum()) / (b[CATS] / b[CATS].sum())
        sh = sh * r
        sh = sh.div(sh.sum(axis=1), axis=0)
    return sh


def load(year):
    lt = pd.read_csv(TARGETS / "labour_targets.csv")
    lt = lt[lt.year == year].set_index("key")["value"]
    inc, con = _series("hbs_income_sources.csv", year), _series("hbs_consumption.csv", year)
    pov = pd.read_csv(TARGETS / "poverty_line_rate.csv").set_index("year").loc[year]
    pop = lt["population"] * 1e3
    rate = lt["unemp_rate"] / 100
    hired = {s: lt[f"hired:{s}"] * 1e3 for s in SECTORS}
    agri_own = (lt["employed:agr"] - lt["hired:agr"]) * 1e3
    T = {"pop": pop, "urban": pop * lt["urban_share"] / 100,
         **{f"hired:{s}": v for s, v in hired.items()},
         "hired_state": lt["hired_state:total"] * 1e3,
         "agri_own": agri_own,
         "selfemp_own": (lt["employed:total"] - lt["hired:total"]) * 1e3 - agri_own,
         "unemployed": rate / (1 - rate) * lt["employed:total"] * 1e3,
         "pensioners": lt["pension_spend"] * 1e6 / 12 / lt["pension_avg"],
         "children": CHILD_SHARE * pop}
    T["wagebill_state"] = lt["wage_state"] * T["hired_state"]
    T["wagebill_nonstate"] = lt["wage_nonstate"] * (sum(hired.values()) - T["hired_state"])
    hbs = {"employment": inc["employment"], "selfemp": inc["selfemp"] - inc["agri"],
           "agri": inc["agri"], "property": inc["property"], "pensions": inc["pensions"],
           "benefits": inc["benefits"] + inc["inkind"], "interhh": inc["interhh"],
           "remit": inc["remit"], "total": inc["total"]}
    return {"year": year, "counts": T, "hbs_pc": hbs, "cons_pc": float(con["total"]),
            "pov_line": float(pov["line"]), "pov_rate": float(pov["rate"]),
            "pov_urban": float(pov["urban"]), "pov_rural": float(pov["rural"]),
            "utsy_members": lt.get("utsy_members", np.nan) * 1e3,
            "utsy_avg_pp": lt.get("utsy_avg_pp", np.nan),
            "wage_avg": lt["wage_avg"], "wage_state": lt.get("wage_state", np.nan),
            "wage_nonstate": lt.get("wage_nonstate", np.nan),
            "inc_dec": decile_levels("income", year)["total"].to_numpy(),
            "inc_dec_tab": decile_levels("income", year),
            "cons_dec": decile_levels("cons", year)["total"].to_numpy(),
            "cons_shares": cons_shares(year)}


def person_profile(levels, mean):
    """Persons share by decile s_d ~ exp(-b d) such that sum s_d*level_d = national mean
    (DSK deciles are household deciles; poorer deciles hold larger households)."""
    d = np.arange(1, 11)
    lo, hi = -2.0, 2.0
    for _ in range(80):
        b = 0.5 * (lo + hi)
        s = np.exp(-b * d); s /= s.sum()
        if (s * levels).sum() > mean:
            lo = b
        else:
            hi = b
    return s
