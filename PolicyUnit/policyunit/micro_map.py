"""Scenario -> MicroUnit chain overrides + FR1 overlay spec, driven by config/adapters.csv
(engine = micro). Generic transforms pct|add|level(*k); custom transforms are the functions
`c_<name>` below (adapter `custom:<name>`). Every custom proxy is documented in note_az."""
from __future__ import annotations

import math

from . import config, fiscal, microbridge as mb, registry, scenario as scn

Y = config.MICRO_YEARS


class MapError(ValueError):
    pass


def _base(sid, module="FR1"):
    return mb.series(mb.baseline(), module, sid)


def _lvl_to_growth(levels_pct):
    """Level deviation path (%) -> growth path (%/y) with zero deviation before the first year."""
    out, prev = [], 0.0
    for L in levels_pct:
        out.append(100.0 * ((1 + L / 100) / (1 + prev / 100) - 1))
        prev = L
    return out


# ------------------------------------------------------------------ custom transforms
def c_inv_nominal_to_real(it, k):
    p_inv, cap, rinv = _base("fr1:p_inv"), _base("fr1:exp_cap_n"), _base("fr1:rinv_state")
    size = scn.path(it, Y)
    add = [k * s / (cap[i] / rinv[i]) for i, s in enumerate(size)]   # Δexp_cap_n == size
    return [("exo", "FR1", "istate_add", {"add": add})]


def c_mw_growth_path(it, k):
    m = _base("fr3:minwage", "FR3")
    m0 = m[0] ** 2 / m[1]
    new = [mi * (1 + k * s / 100) for mi, s in zip(m, scn.path(it, Y))]
    g = [100 * (new[i] / (new[i - 1] if i else m0) - 1) for i in range(len(Y))]
    return [("lever", "FR3", "mw_growth", g)]


def c_level_to_growth(it, k, eid="pension_real_g"):
    return [("exo", "FR1", eid, {"add": _lvl_to_growth([k * s for s in scn.path(it, Y)])})]


def c_tsa_to_dsmf(it, k):
    cost = fiscal.direct_cost(it, Y)
    lv = [100 * k * c / fiscal.base_value("dsmf_spending", y) for c, y in zip(cost, Y)]
    return [("exo", "FR1", "dsmf_add_g", {"add": _lvl_to_growth(lv)})]


def c_vat_overlay(it, k):
    p = registry.params("fiscal")
    dp = [k * p["vat_passthrough"] * s / (100 + p["vat_rate"]) for s in scn.path(it, Y)]
    return [("overlay", "price", dp)]


def c_pit_overlay(it, k):
    p = registry.params("fiscal")
    gdp, hh = fiscal.gdp_nominal(), _base("fr1:hhdisp_n")
    dh = [-k * s / p["pit_rate"] * p["pit_rev_gdp"] / 100 * gdp[y] * p["pit_hh_share"] / hh[i]
          for i, (s, y) in enumerate(zip(scn.path(it, Y), Y))]
    return [("overlay", "income", dh)]


def c_cit_overlay(it, k):
    """PROXY profit tax -> non-oil private investment: user-cost channel −ε_uc·Δτ/(100−τ) plus
    retained-earnings channel ε_cf·ΔCF/I, ΔCF = −Δτ/τ · CIT/GDP · GDP · non-oil share."""
    p = registry.params("fiscal")
    gdp, ip, pi = fiscal.gdp_nominal(), _base("fr1:rinv_priv"), _base("fr1:p_inv")
    out = []
    for i, (s, y) in enumerate(zip(scn.path(it, Y), Y)):
        uc = -p["inv_usercost_elast"] * s / (100 - p["cit_rate"])
        cf = -s / p["cit_rate"] * p["cit_rev_gdp"] / 100 * gdp[y] * p["cit_nonoil_share"]
        out.append(k * (uc + p["inv_cashflow_elast"] * cf / (ip[i] * pi[i])))
    return [("overlay", "invest", out)]


def c_tariff_import_price(it, k):
    p = registry.params("fiscal")
    lv = [100 * k * s / (100 + p["customs_rate"]) for s in scn.path(it, Y)]
    return [("exo", "FR1", "pm_usd_infl", {"add": _lvl_to_growth(lv)})]


def c_export_subsidy(it, k):
    p = registry.params("fiscal")
    x, pg = _base("fr1:rx_non"), _base("fr1:p_gdp")
    pct = [100 * k * p["export_price_elasticity"] * s / (x[i] * pg[i])
           for i, s in enumerate(scn.path(it, Y))]
    return [("exo", "FR1", "extdem", {"pct": pct})]


def c_credit_subsidy(it, k):
    p = registry.params("fiscal")
    cr, pg = _base("fr1:rcred_tot"), _base("fr1:p_gdp")
    add = [-k * 100 * s / (cr[i] * pg[i]) / p["credit_lend_pass"] for i, s in enumerate(scn.path(it, Y))]
    return [("exo", "FR1", "deprate", {"add": add})]


def c_agri_overlay(it, k):
    p = registry.params("fiscal")
    pa = _base("fr1:p_agr")
    d = [k * p["agri_supply_mult"] * s / pa[i] for i, s in enumerate(scn.path(it, Y))]
    return [("overlay", "supply:agr", d)]


def _price(it, k, w, ind):
    p = registry.params("fiscal")
    return [("overlay", "price", [k * p[w] / 100 * s / 100 * (1 + p[ind]) for s in scn.path(it, Y)])]


def c_fuel_overlay(it, k):
    return _price(it, k, "fuel_cpi_weight", "fuel_indirect")


def c_utility_overlay(it, k):
    return _price(it, k, "utility_cpi_weight", "utility_indirect")


def c_log_level(it, k, target=None):
    return [("exo", "FR5", target, {"add": [math.log(1 + k * s / 100) for s in scn.path(it, Y)]})]


def c_fr12_entry(it, k):
    return [("lever", "FR12", "io_market", it["target"]), ("lever", "FR12", "io_dN", k * float(it["size"]))]


# ------------------------------------------------------------------ builder
def _ops_for(it):
    ops, proxy = [], False
    rows = registry.adapters_for("micro", it["instrument"])
    for _, a in rows.iterrows():
        name, k = registry.parse_transform(a["transform"])
        tk = a["target_key"]
        parts = tk.split("/", 2)
        proxy = proxy or "PROKSİ" in a["note_az"]
        if name.startswith("custom:"):
            fn = globals().get("c_" + name.split(":", 1)[1])
            if fn is None:
                raise MapError(f"{it['instrument']}: custom funksiya '{name}' tapılmadı")
            if name == "custom:log_level":
                ops += fn(it, k, target=parts[2])
            elif name == "custom:level_to_growth":
                ops += fn(it, k, eid=parts[2])
            else:
                ops += fn(it, k)
            continue
        if len(parts) != 3:
            raise MapError(f"adapters.csv: target_key '{tk}' formatı MODUL/növ/id olmalıdır")
        mod, kind, eid = parts
        if kind == "levers":
            if "=" in eid:
                eid, v = eid.split("=", 1)
                ops.append(("slever", mod, eid, v))          # structural lever (also in baseline)
            else:
                ops.append(("lever", mod, eid, k * float(it["size"])))
        elif name in ("pct", "add"):
            ops.append(("exo", mod, eid, {name: [k * s for s in scn.path(it, Y)]}))
        else:
            raise MapError(f"{it['instrument']}: transform '{name}' micro üçün dəstəklənmir")
    return ops, proxy, len(rows) > 0


def build(s: dict) -> dict:
    """-> {"overrides", "struct_levers", "overlay", "handled", "proxy", "notes"}"""
    ov, struct, overlay, handled, proxies = {}, {}, {}, [], []
    for it in s["instruments"]:
        ops, proxy, has = _ops_for(it)
        if not has:
            continue
        handled.append(it["instrument"])
        if proxy:
            proxies.append(it["instrument"])
        for op in ops:
            if op[0] == "overlay":
                key, path = op[1], op[2]
                overlay[key] = [a + b for a, b in zip(overlay.get(key, [0.0] * len(Y)), path)]
                continue
            tag, mod, eid, val = op
            if tag == "exo":
                d = ov.setdefault(mod, {}).setdefault("exogenous", {})
                if eid in d:
                    (k1, a), (k2, b) = next(iter(d[eid].items())), next(iter(val.items()))
                    if k1 != k2:
                        raise MapError(f"{eid}: eyni girişə müxtəlif tipli iki alət ({k1}/{k2})")
                    val = {k1: [x + y for x, y in zip(a, b)] if k1 == "add" else
                           [100 * ((1 + x / 100) * (1 + y / 100) - 1) for x, y in zip(a, b)]}
                d[eid] = val
            else:
                if tag == "slever":
                    val = {"true": True, "false": False}.get(val.lower(), val)
                    struct.setdefault(mod, {})[eid] = val
                lv = ov.setdefault(mod, {}).setdefault("levers", {})
                if eid in lv and lv[eid] != val:
                    raise MapError(f"rıçaq {mod}.{eid}: alətlər ziddiyyətli dəyərlər verir")
                lv[eid] = val
    return {"overrides": ov, "struct_levers": struct, "overlay": overlay, "handled": handled,
            "proxy": proxies}
