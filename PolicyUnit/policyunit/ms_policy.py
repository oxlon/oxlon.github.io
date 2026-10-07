"""Household income/consumption computation for one year under a (policy) parameter set —
static first-round microsimulation with optional, explicitly labelled behavioural layer.

Policy dict `pol` keys (all optional):
  params        {param: {"pct"|"add"|"set": x}}   overrides of config/tax_benefit.csv
  mw_old        minimum wage of the counterfactual (for spill-over); mw_spill share (0..1)
  wage_pct      {"all"|"state"|"nonstate"|"budget"|<FR4 sector>: %}   gross-wage changes
  pension_extra_pct  % on all pensions (and the minimum pension)
  utsy_scale    multiplier on ÜSY payments (catalogue instrument tsa_benefit)
  income_pct    {"selfemp"|"agri"|"remit"|"interhh"|"property": %}
  prices_pct    {consumption category: %}   (VAT / tariffs / IO price model)
  base_y        baseline household income (for the consumption response)"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import taxben
from .ms_rawdata import CONS_KEYS

CATS = CONS_KEYS[1:]
# [assumption] share of category spending bearing standard-rate VAT (exempt food staples,
# own production, health/education services); import content for FX/tariff pass-through
VATABLE = {"food": .55, "alc": 1, "tobacco": 1, "clothing": .9, "housing": .6, "furnish": .9,
           "health": .4, "transport": .8, "comm": .9, "recreation": .8, "education": .2,
           "restaurants": .9, "misc": .8}
IMPORT_SHARE = {"food": .25, "alc": .3, "tobacco": .5, "clothing": .8, "housing": .15,
                "furnish": .7, "health": .5, "transport": .45, "comm": .4, "recreation": .4,
                "education": .05, "restaurants": .15, "misc": .45}
FUEL_SHARE_TRANSPORT, UTILITY_SHARE_HOUSING, FX_PASS = .35, .75, .30
SRC = ["employment", "selfemp", "agri", "property", "pensions", "benefits", "interhh",
       "remit"]
HH_VARS = ["inc_property", "remit", "transfer_hh", "utsy_u", "weight"] + \
          [f"cons_{c}" for c in CATS]


def prepare(p: pd.DataFrame) -> pd.DataFrame:
    """Integer household codes and first-member flag (household variables are repeated)."""
    p = p.copy()
    p["_h"] = pd.factorize(p["hh_id"])[0]
    p["_first"] = ~p["hh_id"].duplicated()
    return p


def hh_sum(p, v):
    return np.bincount(p["_h"].to_numpy(), weights=np.asarray(v, float),
                       minlength=int(p["_h"].max()) + 1)


def hh_first(p, col):
    out = np.zeros(int(p["_h"].max()) + 1)
    f = p["_first"].to_numpy()
    out[p["_h"].to_numpy()[f]] = p[col].to_numpy(float)[f]
    return out


def gross_wages(p, cal, year, P, pol):
    up = cal["uprate"].get(str(year), {"wage": 1.0})
    g = p["wage_gross"].to_numpy(float) * up.get("wage", 1.0)
    for key, pct in (pol.get("wage_pct") or {}).items():
        if key == "all":
            m = np.ones(len(p), bool)
        elif key in ("state", "nonstate"):
            m = (p["ownership"] == key).to_numpy()
        elif key == "budget":
            m = (p["budget"] == 1).to_numpy()
        else:
            m = (p["sector"] == key).to_numpy()
        g = np.where(m, g * (1 + pct / 100.0), g)
    mw = P.get("minwage", year)
    ft = (p["formal_ft"] == 1).to_numpy()
    return taxben.min_wage_shift(g, ft, pol.get("mw_old", mw), mw, pol.get("mw_spill", 0.0),
                                 pol.get("mw_spill_band", 1.25), pol.get("mw_spill_taper", False))


def compute(p, cal, year, P, pol=None):
    """Return (hh DataFrame, person dict) for `year`. p must come from prepare()."""
    pol = pol or {}
    f = cal.get("factors", {})
    up = cal["uprate"].get(str(year), {})
    uo, uc = up.get("other", 1.0), up.get("cons", up.get("other", 1.0))
    ip = pol.get("income_pct") or {}
    k = lambda s: 1 + ip.get(s, 0.0) / 100.0
    g = gross_wages(p, cal, year, P, pol)
    tx = taxben.wage_taxes(g, p["regime"].to_numpy(), P, year)
    if "pension" in up:            # projection: FR1 average-pension index (CPI-indexed, same vintage)
        ex = 1 + pol.get("pension_extra_pct", 0.0) / 100.0
        b = p["pension"].to_numpy(float)
        pen = np.where(b > 0, np.maximum(b * up["pension"] * ex, P.get("min_pension", year) * ex), 0.0)
    else:
        pen = taxben.pension_level(p["pension"], cal["base_year"], year, P,
                                   pol.get("pension_extra_pct", 0.0), cal.get("pension_index_proj"))
    n = hh_sum(p, np.ones(len(p)))
    hh = pd.DataFrame({"w": hh_first(p, "weight"), "n": n})
    hh["y_employment"] = f.get("employment", 1) * hh_sum(p, tx["net"])
    hh["y_selfemp"] = hh_sum(p, p["inc_selfemp"]) * uo * k("selfemp")
    hh["y_agri"] = hh_sum(p, p["inc_agri"]) * uo * k("agri")
    hh["y_property"] = hh_first(p, "inc_property") * uo * k("property")
    hh["y_pensions"] = f.get("pensions", 1) * hh_sum(p, pen)
    hh["y_benother"] = f.get("benefits", 1) * hh_sum(p, p["benefit_other"]) * uo
    hh["y_interhh"] = hh_first(p, "transfer_hh") * uo * k("interhh")
    hh["y_remit"] = hh_first(p, "remit") * uo * k("remit")
    pre = hh[[c for c in hh.columns if c.startswith("y_")]].sum(axis=1).to_numpy()
    need = P.get("need_criterion", year)
    # take-up rises with the relative entitlement gap: P(take) = min(1, a * gap/(n*need))
    gs = np.maximum(n * need - pre, 0) / np.maximum(n * need, 1e-9)
    take = hh_first(p, "utsy_u") < np.minimum(1.0, cal.get("p_takeup", 1e9)
                                              * gs ** cal.get("takeup_gamma", 1.0))
    if pol.get("take_base") is not None:      # baseline recipients keep applying (no flip-out)
        take = take | np.asarray(pol["take_base"], bool)
    hh["utsy"], hh["utsy_elig"] = taxben.utsy(pre, n, need, take, pol.get("utsy_scale", 1.0))
    hh["utsy_gapshare"] = gs
    hh["y_benefits"] = hh["y_benother"] + hh["utsy"]
    hh["y_total"] = pre + hh["utsy"]
    hh["y_pc"] = hh["y_total"] / n
    # consumption: base basket uprated; first-round response with household APC (assumption)
    c0 = np.column_stack([hh_first(p, f"cons_{c}") for c in CATS]) * uc
    base_y = np.asarray(pol.get("base_y", hh["y_total"]), float)
    c0_tot = c0.sum(axis=1)
    apc = np.clip(c0_tot / np.maximum(base_y, 1.0), 0.3, 1.2)
    c_nom = np.maximum(c0_tot + apc * (hh["y_total"].to_numpy() - base_y), 0.0)
    shares = c0 / np.maximum(c0_tot, 1e-9)[:, None]
    dp = np.array([(pol.get("prices_pct") or {}).get(c, 0.0) / 100.0 for c in CATS])
    pidx = 1 + shares @ dp
    hh["c_nom"], hh["price_idx"] = c_nom, pidx
    hh["c_pc"] = c_nom / pidx / n                 # real (base-price) consumption per capita
    hh["y_pc_real"] = hh["y_pc"] / pidx
    hh["vat"] = (c_nom[:, None] * shares) @ np.array([VATABLE[c] for c in CATS]) * \
        (P.get("vat_rate", year) / (1 + P.get("vat_rate", year)))
    hh["urban"] = hh_first(p, "urban")
    per = {"gross": g, "pension": pen, **tx}
    return hh, per


def prices_from_instruments(vat_pp=0.0, vat0=0.18, fuel_pct=0.0, utility_pct=0.0,
                            fx_pct=0.0, tariff_pp=0.0, extra=None):
    """Consumer price changes (%) by category from price instruments (first round)."""
    out = {}
    for c in CATS:
        d = VATABLE[c] * ((1 + vat0 + vat_pp / 100) / (1 + vat0) - 1) * 100
        d += FX_PASS * IMPORT_SHARE[c] * fx_pct
        if c not in ("education", "health", "restaurants", "comm"):
            d += IMPORT_SHARE[c] * tariff_pp
        if c == "transport":
            d += FUEL_SHARE_TRANSPORT * fuel_pct
        if c == "housing":
            d += UTILITY_SHARE_HOUSING * utility_pct
        out[c] = d + (extra or {}).get(c, 0.0)
    return out
