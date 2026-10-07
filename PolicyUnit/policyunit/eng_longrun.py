"""Engine `longrun` — "uzun müddət (struktur ekstrapolyasiya)", 2031–LONG_END. CONTINUOUS splice on the
MicroUnit FR1 2030 deviation (no own-history forecasting, no AR terms). n = t − 2030:

  dlnY_t = S_t + D_2030 · d_t          (non-oil; at n = 0 exactly the FR1 2030 deviation)
  S_t    = c · [θ_g·ΔK_g,t/K_g,t + α·ΔK_p,t/K_t + φ·T_2030 + g_TFP·n]      supply side, persists
           ΔK_x,t = (1−δ)·ΔK_x,t−1 + ΔI_x,t (policy capital: public investment, profit-tax private investment;
           flows continue after 2030 only while the instrument is in force); T_2030 = residual of the 2030
           deviation after the capital terms, φ = structural share (adapters: sector_tfp 1, market_entry 1,
           agri 0,5, otherwise 0); c ∈ [0, 1] keeps S_2030 within the 2030 deviation (same sign).
  D_2030 = dlnY_2030 − S_2030          demand side; d_t = ψ + (1−ψ)·0.5^(n/h) while the policy is in force,
                                         0.5^(n/h) after it ended (h = demand_halflife, ψ = active_demand_retained)
  dlnL_t = dlnL_2030 · d_t(h_L)        employment returns towards the natural rate
  Fiscal: Δbal_t = R_t + τ·ΔY_nom,t − cost_t − i·Δdebt_{t−1}; R_2030 is the FR1 2030 residual (price-level /
          import / indexation channels) so the balance is continuous; R_t = R_2030 scaled with nominal GDP while the
          policy is in force, decaying with h after it ended; cost = deficit-financed
          direct cost (SOFAZ / tax / reallocation-financed costs are offset). Tier D."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import config, fiscal, registry, scenario as scn
from .engine_base import Result, empty_result, row

ENGINE = "longrun"
METHOD = "Uzun müddət (struktur ekstrapolyasiya)"
NOTE = ("uzun müddət (struktur ekstrapolyasiya) — 2030 sapmasından kəsilməz davam: tələb effekti sönür, "
        "kapital/TFP effekti qalır; sübut səviyyəsi D")


def _p(name, default):
    v = registry.params("longrun").get(name, default)
    return default if isinstance(v, str) else float(v)


def persistence(s) -> float:
    phi = 0.0
    for it in s["instruments"]:
        for _, a in registry.adapters_for(ENGINE, it["instrument"]).iterrows():
            name, k = registry.parse_transform(a["transform"])
            if a["target_key"] == "tfp_persistence":
                phi = max(phi, k)
    return phi


def run(s: dict, ctx: dict | None = None) -> Result:
    mic = (ctx or {}).get("results", {}).get("micro")
    if mic is None or mic.frame.empty or "fr1_base" not in mic.meta:
        return empty_result(ENGINE, "Uzun müddətli ekstrapolyasiya MikroUnit nəticəsi tələb edir — bu ssenari üçün yoxdur")
    B, S = mic.meta["fr1_base"], mic.meta["fr1_scen"]
    L = lambda d, k, i=-1: d[k][i]
    a, thg, shg = _p("alpha_k", 0.4), _p("public_capital_elast", 0.10), _p("public_capital_share", 0.4)
    hd, hL, psi = _p("demand_halflife", 3.0), _p("labour_halflife", 3.0), _p("active_demand_retained", 0.5)
    gA, gL = _p("tfp_growth", 1.0) / 100, _p("labour_growth", 0.5) / 100
    g = gL + gA / (1 - a)
    K29, K30, I30 = B["fr1:K_non"][-2], B["fr1:K_non"][-1], B["fr1:rinv_non"][-1]
    delta = (I30 - (K30 - K29)) / K29
    delta = delta if 0.01 <= delta <= 0.2 else 0.06
    handled = set(mic.meta.get("handled", []))
    its = [it for it in s["instruments"] if it["instrument"] in handled]
    active = any(y > 2030 for it in its for y in it["years"])
    years_all = list(range(config.FIRST_YEAR, config.LONG_END + 1))
    years = [y for y in years_all if y > 2030]
    p_inv = B["fr1:p_inv"] if "fr1:p_inv" in B else [1.8] * 5
    # policy capital flows (real 2015 prices)
    Ig = np.zeros(len(years_all))
    for it in its:
        if it["instrument"] == "pub_invest":
            c = np.array(fiscal.direct_cost(it, years_all))
            pinv = np.array([p_inv[min(i, 4)] * (1.04 ** max(0, i - 4)) for i in range(len(years_all))])
            Ig += c / (pinv * 1.2225)                       # Δexp_cap_n = cost (FR1 capexp_ratio)
    ov = mic.meta.get("overlay") or {}
    Ip = np.zeros(len(years_all))
    inv = ov.get("invest_real") or [0.0] * 5
    Ip[:5] = inv
    if any(it["instrument"] == "profit_tax" and any(y > 2030 for y in it["years"]) for it in its):
        Ip[5:] = inv[-1]
    dKg, dKp = np.zeros(len(years_all)), np.zeros(len(years_all))
    for i in range(len(years_all)):
        dKg[i] = (1 - delta) * (dKg[i - 1] if i else 0) + Ig[i]
        dKp[i] = (1 - delta) * (dKp[i - 1] if i else 0) + Ip[i]
    i30 = years_all.index(2030)
    Kb = {2030: K30}
    for t in years:
        Kb[t] = Kb[t - 1] * (1 + g)
    sup = lambda t: thg * dKg[years_all.index(t)] / (shg * Kb[t]) + a * dKp[years_all.index(t)] / Kb[t]
    dlnY30 = math.log(L(S, "fr1:rgdpnon") / L(B, "fr1:rgdpnon"))
    dlnL30 = math.log(L(S, "fr1:emp") / L(B, "fr1:emp"))
    cap30 = sup(2030)
    phi = persistence(s)
    T30 = dlnY30 - cap30
    S30 = cap30 + phi * T30
    c = 1.0 if dlnY30 == 0 or S30 == 0 else max(0.0, min(1.0, dlnY30 / S30))
    tfp_prog = sum(it["size"] / 100 for it in its if it["instrument"] == "sector_tfp" and any(y > 2030 for y in it["years"]))
    D30 = dlnY30 - c * S30
    decay = (lambda n, h: psi + (1 - psi) * 0.5 ** (n / h)) if active else (lambda n, h: 0.5 ** (n / h))
    # fiscal continuity residual
    gdp_b, gdp_s = L(B, "fr1:gdp_n"), L(S, "fr1:gdp_n")
    oil = L(B, "fr1:rgdp") - L(B, "fr1:rgdpnon")
    tau = (L(B, "fr1:rev_tot_n") - L(B, "fr1:rev_oil_n")) / gdp_b
    irate = L(B, "fr1:debt_serv_n") / L(B, "fr1:debt_azn")
    pi = L(B, "fr1:cpi") / B["fr1:cpi"][-2] - 1
    cost_all = fiscal.scenario_cost(s, years_all, only=handled)["by_fin"]["deficit"]
    dbal30 = L(S, "fr1:balance_n") - L(B, "fr1:balance_n")
    ddebt29 = S["fr1:debt_azn"][-2] - B["fr1:debt_azn"][-2]
    ddebt = L(S, "fr1:debt_azn") - L(B, "fr1:debt_azn")
    O30 = (L(S, "fr1:rgdp") - L(S, "fr1:rgdpnon")) - oil          # non-"non-oil" part (net taxes, oil) at 2030
    p30 = (gdp_s / gdp_b - 1) - (L(S, "fr1:rgdp") / L(B, "fr1:rgdp") - 1)   # price-level part of nominal GDP
    R30 = dbal30 + cost_all[i30] - tau * (gdp_s - gdp_b) + irate * ddebt29
    bal_ratio, debt_b = L(B, "fr1:balance_n") / gdp_b, L(B, "fr1:debt_azn")
    cpi_dev = L(S, "fr1:cpi") / L(B, "fr1:cpi") - 1
    lf_b, Lb0, Yb0 = L(B, "fr1:lf"), L(B, "fr1:emp"), L(B, "fr1:rgdpnon")
    rows = []
    for t in years:
        n, j = t - 2030, years_all.index(t)
        St = c * (sup(t) + phi * T30) + tfp_prog * n
        dlnY = St + D30 * decay(n, hd)
        dlnL = dlnL30 * decay(n, hL)
        Yb, Lb, lf = Yb0 * (1 + g) ** n, Lb0 * (1 + gL) ** n, lf_b * (1 + gL) ** n
        gn = fiscal.gdp_nominal()[t] / fiscal.gdp_nominal()[2030]      # same nominal scaling as the cost bases
        gdp_bt = gdp_b * gn
        Ot = O30 * decay(n, hd) * (1 + g) ** n
        dYnom = (p30 + ((math.exp(dlnY) - 1) * Yb + Ot) / (Yb + oil)) * gdp_bt
        Rt = R30 * gn * (1.0 if active else 0.5 ** (n / hd))
        dbal = Rt + tau * dYnom - cost_all[j] - irate * ddebt
        ddebt -= dbal
        debt_b -= bal_ratio * gdp_bt
        add = lambda ind, lab, unit, b, v, grp: rows.append(row(ind, lab, unit, t, b, v, METHOD, "D", grp, NOTE))
        add("gdp_nonoil_real", "Real qeyri-neft ÜDM", "mln AZN 2015", Yb, Yb * math.exp(dlnY), "makro")
        add("gdp_real", "Real ÜDM", "mln AZN 2015", Yb + oil, Yb * math.exp(dlnY) + oil + Ot, "makro")
        add("employment", "Məşğulluq (ümumi)", "min nəfər", Lb, Lb * math.exp(dlnL), "əmək")
        ub = 100 * (lf - Lb) / lf
        add("unemp_rate", "İşsizlik səviyyəsi", "%", ub, ub - 100 * Lb * (math.exp(dlnL) - 1) / lf, "əmək")
        dK = (L(S, "fr1:K_non") - K30) * (1 - delta) ** n + (dKg[j] + dKp[j]) - (dKg[i30] + dKp[i30]) * (1 - delta) ** n
        add("capital_nonoil", "Qeyri-neft kapital ehtiyatı", "mln AZN 2015", Kb[t], Kb[t] + dK, "uzun")
        add("tfp_nonoil", "Qeyri-neft TFP (səviyyə)", "indeks", 1.0, math.exp(c * phi * T30 + tfp_prog * n), "uzun")
        cpi_b = L(B, "fr1:cpi") * (1 + pi) ** n
        add("cpi", "İstehlak qiymətləri indeksi (səviyyə sapması sabit)", "2015 = 100", cpi_b, cpi_b * (1 + cpi_dev), "makro")
        add("budget_balance", "Dövlət büdcəsinin balansı", "mln AZN", bal_ratio * gdp_bt, bal_ratio * gdp_bt + dbal, "fiskal")
        add("debt_pct", "Dövlət borcu (ÜDM-ə %)", "% ÜDM", 100 * debt_b / gdp_bt,
            100 * (debt_b + ddebt) / (gdp_bt + dYnom), "fiskal")
        add("fiscal_cost", "Birbaşa fiskal xərc / gəlir itkisi (ex ante, brutto — geri əlaqədən əvvəl)", "mln AZN", 0.0,
            fiscal.scenario_cost(s, [t], only=handled)["total"][0], "fiskal")
    meta = {"params": {"alpha": a, "theta_g": thg, "delta": delta, "g_balanced": g, "phi_tfp": phi, "psi": psi,
                       "h_demand": hd, "S2030": c * S30, "D2030": D30, "R2030_fiscal": R30, "scale_c": c,
                       "dlnY_2030": dlnY30, "active_after_2030": active},
            "warnings": [], "assumptions": [NOTE]}
    return Result(ENGINE, pd.DataFrame(rows), meta)
