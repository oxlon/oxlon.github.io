"""Engine `micro` — MicroUnit structural chain FR1→FR3→FR4→FR5→FR10→FR12 (the CORE engine).

Impact = scenario chain − baseline chain of the same vintage and the same structural levers.
Instruments with an FR1 channel are mapped to chain overrides (tier C: estimated AZ structural
equations); instruments without one use the documented FR1 overlay (micro_overlay, tier D).
Custom transforms: `custom:<name>` in adapters.csv -> micro_map.c_<name>.
"""
from __future__ import annotations

import time

import pandas as pd

from . import config, fiscal, micro_harmonise as H, micro_map, micro_overlay, microbridge as mb
from .engine_base import Result, empty_result, row

ENGINE = "micro"
# instrument-specific caveats (side-effect notes, quantified later by the FR4 side-effects phase)
CAVEATS = {
    "min_wage": ("YAN TƏSİR XƏBƏRDARLIĞI: modeldə minimum əmək haqqının işdən çıxarma (disemployment) və "
                 "qeyri-formallaşma kanalı yoxdur — məşğulluq təsiri yuxarı sərhəddir; risk FR4 yan təsir "
                 "mərhələsində qiymətləndirilir. Büdcə xərci: büdcə təşkilatlarında yeni minimuma qaldırma + "
                 "sıxılma + 22 % sosial ayırma (mw_budget). Nəticə metodlar arası diapazondur (P1_ranges.csv): "
                 "MikroUnit makro reaksiyası yuxarı, mikrosimulyasiyanın statik döşəməsi aşağı sərhəd"),
    "fx_deval": ("Büdcə işarəsi: neft gəliri AZN ilə artır (+1,1 mlrd/il), lakin FR1 fiskal qaydaları (F3: cari xərc "
                 "gəlirə, istate_rule = policy_oilrev: dövlət investisiyası neft gəlirinə bağlıdır) əlavə gəliri "
                 "xərcləyir — balans azca pisləşir. İQİ üçün əsas mənbə RiskUnit FX ötürməsidir (riskfx)"),
}
METHOD = "MikroUnit struktur zənciri"


def plan(s: dict) -> dict:
    """Overrides + overlay inputs for a scenario (no model run). Financing per instrument (C2)."""
    m = micro_map.build(s)
    Y = config.MICRO_YEARS
    cost = fiscal.scenario_cost(s, Y, only=set(m["handled"]))
    m["cost"] = cost
    m["financing"] = fiscal.financing(dict(s, instruments=[it for it in s["instruments"]
                                                          if it["instrument"] in m["handled"]] or s["instruments"]))
    m["fin_tax"], m["sofaz"], m["realloc"] = (cost["by_fin"]["tax"], cost["by_fin"]["sofaz"],
                                              cost["by_fin"]["reallocation"])
    # non-standard (PolicyUnit-only) channel present? (the overlay itself is always applied: pension indexation)
    m["use_overlay"] = bool(m["overlay"]) or any(abs(x) > 0 for p in (cost["off_fr1"], m["fin_tax"], m["sofaz"],
                                                                         m["realloc"]) for x in p)
    return m


def make_overlay(m: dict, base=None):
    """The FR1 overlay for a plan (shared by FR4 side-effect variants and sensitivity runs)."""
    base = base or mb.baseline(m["struct_levers"])
    return micro_overlay.make(m["overlay"], m["cost"]["off_fr1"], m["fin_tax"], m["sofaz"], m["realloc"],
                              pension_base=mb.series(base, "FR1", "fr1:pension"), pension_R=_pension_R(m))


def _fiscal_story(s, m, base, scen) -> list[str]:
    """Explain a balance whose sign differs from the direct cost (e.g. fuel: direct revenue gain, balance worse)."""
    Y = config.MICRO_YEARS
    y = max(s["start_year"], Y[0])
    i = Y.index(y)
    bal = mb.series(scen, "FR1", "fr1:balance_n")[i] - mb.series(base, "FR1", "fr1:balance_n")[i]
    direct = -m["cost"]["total"][i]
    ov = scen["results"]["FR1"].get("meta", {}).get("policy_overlay") or {}
    pens = -(ov.get("pension_correction") or [0.0] * len(Y))[i]
    fb = bal - direct - pens
    if abs(direct) < 1 or (direct > 0) == (bal > 0):
        return []
    az = lambda x: f"{x:+,.0f}".replace(",", " ")
    return [f"Büdcə izahı ({y}): birbaşa təsir {az(direct)} mln AZN, lakin balans {az(bal)}: pensiyaların İQİ "
            f"indeksasiyası {az(pens)}, ÜDM/gəlir geri əlaqəsi və fiskal qaydalar (real gəlirin azalması → istehlak "
            f"və vergi bazası, F3 xərc qaydası) {az(fb)} mln AZN"]


def _pension_R(m) -> list[float]:
    g = m["overrides"].get("FR1", {}).get("exogenous", {}).get("pension_real_g", {}).get("add")
    R, out = 1.0, []
    for x in (g or [0.0] * len(config.MICRO_YEARS)):
        R *= 1 + x / 100
        out.append(R)
    return out


def run(s: dict, ctx: dict | None = None) -> Result:
    t0 = time.perf_counter()
    m = plan(s)
    if not m["handled"]:
        return empty_result(ENGINE, "Ssenarinin alətləri üçün MikroUnit kanalı yoxdur (adapters.csv)")
    base = mb.baseline(m["struct_levers"])
    ov = make_overlay(m, base)
    scen = mb.run(m["overrides"], overlay=ov)
    tier = "D" if (m["proxy"] or m["overlay"]) else "C"
    notes = []
    if m["proxy"]:
        notes.append("PROKSİ: " + ", ".join(m["proxy"]) + " — FR1 elastiklikləri ilə overlay (sübut səviyyəsi D)")
    if any(m["cost"]["off_fr1"]):
        notes.append("birbaşa xərc FR1 büdcəsində olmadığı üçün balansa əlavə edilib")
    notes.append("pensiyaların İQİ indeksasiyası uzlaşdırılmış pensiya bazası ilə büdcəyə yazılır")
    caveats = [CAVEATS[i] for i in m["handled"] if i in CAVEATS]
    if "min_wage" in m["handled"]:
        from .ranges import nfr1_note
        caveats += [x for x in [nfr1_note()] if x]
    notes += caveats
    if m["financing"] != "deficit":
        notes.append(f"maliyyələşmə (alət üzrə): {m['financing']}")
    notes += _fiscal_story(s, m, base, scen)
    note = "; ".join(notes)
    rows = H.rows(base, scen, METHOD, tier, note)
    Y = config.MICRO_YEARS
    for i, y in enumerate(Y):
        rows.append(row("fiscal_cost", "Birbaşa fiskal xərc / gəlir itkisi (ex ante, brutto — geri əlaqədən əvvəl)", "mln AZN", y, 0.0,
                        m["cost"]["total"][i], METHOD, tier, "fiskal", "statik, geri əlaqədən əvvəl"))
    if any(m["sofaz"]):
        cum = pd.Series(m["sofaz"]).cumsum().tolist()
        for i, y in enumerate(Y):
            rows.append(row("sofaz_assets", "ARDNF aktivlərinin dəyişməsi (kumulyativ)", "mln AZN", y, 0.0,
                            -cum[i], METHOD, tier, "fiskal", "ARDNF transferti ilə maliyyələşmə"))
    if any(it["instrument"] == "market_entry" for it in s["instruments"]):
        rows += H.fr12_io_rows(scen, METHOD, "D", s["start_year"])
    meta = {"vintage": mb.vintage(), "runtime_s": round(time.perf_counter() - t0, 2),
            "overrides": m["overrides"], "struct_levers": m["struct_levers"], "handled": m["handled"],
            "proxy": m["proxy"], "financing": m["financing"], "warnings": caveats, "side_effect_notes": caveats,
            "info_az": sorted(set(w for w in scen["warnings"])),
            "assumptions": notes, "fr1_base": _fr1(base), "fr1_scen": _fr1(scen),
            "cost_total": m["cost"]["total"], "overlay": scen["results"]["FR1"].get("meta", {}).get("policy_overlay")}
    return Result(ENGINE, pd.DataFrame(rows), meta)


LR_KEYS = ["fr1:rgdp", "fr1:rgdpnon", "fr1:K_non", "fr1:rinv_non", "fr1:rinv_tot", "fr1:emp", "fr1:lf",
           "fr1:gdp_n", "fr1:gdpnon_n", "fr1:balance_n", "fr1:debt_azn", "fr1:debt_serv_n",
           "fr1:rev_tot_n", "fr1:rev_oil_n", "fr1:cpi", "fr1:p_gdp", "fr1:unemp", "fr1:rwage", "fr1:wage",
           "fr1:p_inv", "fr1:pension"]


def _fr1(res) -> dict:
    return {k: mb.series(res, "FR1", k) for k in LR_KEYS}
