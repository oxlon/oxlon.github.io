"""FR1 overlay (documented PROXY, tier D) for instruments without an FR1 channel and for fiscal
items outside the FR1 budget. Applied to the FR1 scenario result BEFORE the downstream modules
(FR3–FR12). FR1's own estimated coefficients (microlib.engines.fr1.inputs()):

  dlnH = dh + ω·β·dp − dp      real disposable income (ω = E3 wage-bill elasticity, β = E2 CPI elasticity)
  dlnC = γ·dlnH  (D1);  dlnM = μ·dlnC + m_inv·ΔI/M  (D4 + investment imports)
  ΔI   = dlnI·I_priv (profit-tax proxy); ΔK_t = (1−δ)ΔK_{t−1} + ΔI_t
  ΔYn  = ΔC − ΔM + ΔI + ΔS + ΔG ;  dln emp = ε·dlnYn (E1)
  Δrev = rrev_nonoil·p_gdp·(η_y·dlnYn + η_m·dlnM) + tax offset + SOFAZ transfer
  balance += Δrev − off-FR1 cost − pension correction + reallocation
Pension correction (C3/C6): FR1 indexes pensions to CPI but books in the budget only the policy real
increase on its own base (CAL pens_exp_base 7 783). The overlay replaces it by the reconciled base
B_t (fiscal_params pension_spending) × (P_scen/P_base − 1), i.e. it also costs CPI indexation."""
from __future__ import annotations

import numpy as np

from . import config, fiscal, microbridge as mb, registry

Y = [str(y) for y in config.MICRO_YEARS]
NONOIL = ["agr", "man", "elc", "wat", "con", "trd", "tou", "tra", "ict", "oth"]
DELTA_K = 0.06


def coefs() -> dict:
    c = mb.coef
    return {"beta": c("FR1.E2_wage|ln_cpi"), "omega": c("FR1.E3_hhdisp|ln_wagebill_r"),
            "gamma": c("FR1.D1_cons|ln_hhdisp_pc"), "mu": c("FR1.D4_mnon|ln_cons"),
            "eps": c("FR1.E1_emp|ln_gdpnon_pc"), "eta_y": c("FR1.F2_revnon|ln_gdpnon"),
            "eta_m": c("FR1.F2_revnon|ln_m_non")}


def _cal():
    mb.chain()
    from microlib.engines import fr1
    return fr1._st()["CAL"]


def make(spec: dict, off_cost, fin_offset, sofaz_transfer, realloc, pension_base=None, pension_R=None):
    """Return overlay(fr1_result) -> fr1_result. All paths are lists over MICRO_YEARS.
    spec: {"price": dp, "income": dh, "invest": dlnI_priv, "supply:<sec>": Δreal}; pension_base: baseline
    FR1 average pension path; pension_R: cumulative real policy factor of a pension instrument (1 = none)."""
    k = coefs()
    n = len(Y)
    z = np.zeros(n)
    arr = lambda v: np.asarray(v if v is not None else z, float)
    dp, dh0, dlnI = arr(spec.get("price")), arr(spec.get("income")), arr(spec.get("invest"))
    off, fin, sof, rea = arr(off_cost), arr(fin_offset), arr(sofaz_transfer), arr(realloc)
    supply = {key.split(":", 1)[1]: arr(v) for key, v in spec.items() if key.startswith("supply:")}
    m_inv = registry.params("fiscal").get("inv_import_share", 0.4)
    R = arr(pension_R) if pension_R is not None else np.ones(n)

    def overlay(res):
        s = res["series"]
        get = lambda kk: np.array([s[kk][y] for y in Y], float)
        g = {kk: get(kk) for kk in
             ("fr1:rcons", "fr1:rm_non", "fr1:rgdpnon", "fr1:rgdp", "fr1:rhhdisp", "fr1:hhdisp_n", "fr1:cpi",
              "fr1:p_cons", "fr1:wage", "fr1:emp", "fr1:lf", "fr1:rrev_nonoil", "fr1:p_gdp", "fr1:gdp_n",
              "fr1:gdpnon_n", "fr1:balance_n", "fr1:debt_azn", "fr1:infl", "fr1:rev_tot_n", "fr1:exp_tot_n",
              "fr1:rinv_priv", "fr1:rinv_non", "fr1:rinv_tot", "fr1:K_non", "fr1:pension", "fr1:pop")}
        dh = dh0 - fin / g["fr1:hhdisp_n"]
        dlnH = dh + k["omega"] * k["beta"] * dp - dp
        dlnC = k["gamma"] * dlnH
        dC = g["fr1:rcons"] * dlnC
        dI = g["fr1:rinv_priv"] * dlnI
        dM = g["fr1:rm_non"] * k["mu"] * dlnC + m_inv * dI
        dlnM = dM / g["fr1:rm_non"]
        dS = sum(supply.values()) if supply else z
        dG = -rea / g["fr1:p_gdp"]
        dYn = dC - dM + dI + dS + dG
        dlnYn = dYn / g["fr1:rgdpnon"]
        demand = dC - dM + dI + dG
        va = {sec: get(f"fr1:rva_{sec}") for sec in NONOIL}
        tot = sum(va.values())
        for sec in NONOIL:
            _put(s, f"fr1:rva_{sec}", va[sec] + demand * va[sec] / tot + supply.get(sec, z))
        dK = np.zeros(n)
        for i in range(n):
            dK[i] = (1 - DELTA_K) * (dK[i - 1] if i else 0.0) + dI[i]
        for kk, v in (("fr1:rcons", dC), ("fr1:rm_non", dM), ("fr1:rgdpnon", dYn), ("fr1:rgdp", dYn),
                      ("fr1:rinv_priv", dI), ("fr1:rinv_non", dI), ("fr1:rinv_tot", dI), ("fr1:K_non", dK)):
            _put(s, kk, g[kk] + v)
        _put(s, "fr1:rhhdisp", g["fr1:rhhdisp"] * np.exp(dlnH))
        _put(s, "fr1:hhdisp_n", g["fr1:hhdisp_n"] * (1 + dh + k["omega"] * k["beta"] * dp))
        cpi = g["fr1:cpi"] * (1 + dp)
        _put(s, "fr1:cpi", cpi)
        lvl = np.concatenate([[0.0], dp])
        _put(s, "fr1:infl", ((1 + g["fr1:infl"] / 100) * (1 + lvl[1:]) / (1 + lvl[:-1]) - 1) * 100)
        for p in ("fr1:p_cons", "fr1:p_serv_hh", "fr1:p_retail", "fr1:p_cater"):
            if p in s:
                _put(s, p, get(p) * (1 + dp))
        wage = g["fr1:wage"] * (1 + dp) ** k["beta"]
        _put(s, "fr1:wage", wage)
        _put(s, "fr1:rwage", wage / cpi * 100)
        emp = g["fr1:emp"] * (1 + k["eps"] * dlnYn)
        _put(s, "fr1:emp", emp)
        _put(s, "fr1:unemp", 100 * (g["fr1:lf"] - emp) / g["fr1:lf"])
        dgdp = dYn * g["fr1:p_gdp"]
        _put(s, "fr1:gdp_n", g["fr1:gdp_n"] + dgdp)
        _put(s, "fr1:gdpnon_n", g["fr1:gdpnon_n"] + dgdp)
        # pension indexation / base reconciliation
        pens_fix = np.zeros(n)
        if pension_base is not None:
            C = _cal()
            Pb = np.asarray(pension_base, float)
            Ps = g["fr1:pension"] * (1 + dp)                    # overlay price shift is indexed too
            _put(s, "fr1:pension", Ps)
            B = np.array([fiscal.base_value("pension_spending", int(y)) for y in Y]) * Pb / np.array(
                [fiscal.pension_path()[int(y)] for y in Y])
            ours = B * (Ps / Pb - 1)
            fr1 = C["pens_exp_base"] * (g["fr1:pension"] / C["pens_base_pension"]) * (
                g["fr1:pop"] / C["pens_base_pop"]) * (1 - 1 / R)
            pens_fix = ours - fr1
        d_rev = g["fr1:rrev_nonoil"] * g["fr1:p_gdp"] * (k["eta_y"] * dlnYn + k["eta_m"] * dlnM) + fin + sof
        d_bal = d_rev - off - pens_fix + rea
        _put(s, "fr1:rev_tot_n", g["fr1:rev_tot_n"] + d_rev)
        _put(s, "fr1:exp_tot_n", g["fr1:exp_tot_n"] + off + pens_fix - rea)
        _put(s, "fr1:balance_n", g["fr1:balance_n"] + d_bal)
        _put(s, "fr1:debt_azn", g["fr1:debt_azn"] - np.cumsum(d_bal))
        res.setdefault("meta", {})["policy_overlay"] = {
            "coefficients": k, "price": dp.tolist(), "income": dh.tolist(), "invest_real": dI.tolist(),
            "off_cost": off.tolist(), "tax_offset": fin.tolist(), "sofaz_transfer": sof.tolist(),
            "realloc": rea.tolist(), "pension_correction": pens_fix.tolist(),
            "supply": {kk: v.tolist() for kk, v in supply.items()}}
        return res

    return overlay


def _put(s, key, arr):
    s[key] = {y: float(v) for y, v in zip(Y, arr)} | {kk: v for kk, v in s.get(key, {}).items() if kk not in Y}
