"""P1_ranges — headline result as a RANGE between methods (C3): for each scenario × headline indicator ×
horizon the lowest / highest method value, the core (MikroUnit) value and an Azerbaijani explanation;
for minimum-wage scenarios the NFR1 retrospective evidence (chain over-prediction) is cited."""
from __future__ import annotations

import math

import pandas as pd

from . import config
from .compare import METHODS, NAME

HEAD = ["gdp_real", "gdp_nonoil_real", "cpi", "infl", "wage_nominal", "wage_real", "employment",
        "employment_hired", "unemp_rate", "gini", "poverty_rate", "budget_balance_pct", "debt_pct"]


def _az(x, d=1) -> str:
    """Azerbaijani number format for a NUMBER only (never applied to text: 'f.b.' stays)."""
    return f"{x:.{d}f}".replace(".", ",")


def nfr1_note(indicators=("wage_growth", "infl")) -> str:
    p = config.OUTPUT / "V_nfr1_comparisons.csv"
    if not p.exists():
        return ""
    d = pd.read_csv(p)
    d = d[(d.method == "micro_chain") & d.indicator.isin(indicators) & d.event_id.isin(["E1", "E3"])]
    parts = []
    for r in d.itertuples():
        if r.indicator == "wage_growth" and r.year in (2019, 2025):
            parts.append(f"maaş artımı {r.year}: zəncir {_az(r.pred)} % / fakt {_az(r.obs_effect)} %")
        if r.indicator == "infl" and r.year == 2019:
            parts.append(f"inflyasiya 2019: zəncir {_az(r.pred)} f.b. / fakt {_az(r.obs_effect)} f.b.")
    return ("NFR1 retrospektiv yoxlama: MikroUnit zənciri minimum əmək haqqı şokunda maaşı və inflyasiyanı "
            "yüksək qiymətləndirir (" + "; ".join(parts) + ") — makro rəqəm yuxarı sərhəd kimi oxunmalıdır.") if parts else ""


SPILL = "microsim_spill"
LABEL = dict(NAME, **{SPILL: "mikrosimulyasiya + spill-over"})


def _spill(p1, sid, ind, hz):
    if p1 is None:
        return None
    from .integrate import effect
    g = p1[(p1.scenario == sid) & (p1.engine == "microsim") & (p1.indicator == ind + "@spill") & (p1.horizon == hz)]
    return None if g.empty else effect(g, ind)


def table(n2: pd.DataFrame, scenarios: dict, p1: pd.DataFrame | None = None) -> pd.DataFrame:
    """Range per row; for minimum-wage scenarios three points: microsim static floor, microsim with the
    labelled spill-over option (`<indicator>@spill`, eng_microsim.SPILL_CORE) and the MikroUnit macro response."""
    if n2.empty:
        return n2
    rows, mw_note = [], nfr1_note()
    for r in n2[n2.indicator.isin(HEAD)].itertuples():
        vals = {m: getattr(r, m) for m in METHODS if m in n2.columns and getattr(r, m) is not None
                and not (isinstance(getattr(r, m), float) and math.isnan(getattr(r, m)))}
        excl = ""
        if "caem" in vals and str(getattr(r, "caem_reliable", "")) == "xeyr":
            excl = f"CAEM {_az(vals.pop('caem'), 3)} — ETİBARSIZ (vergi şokunun fiskal nəticəsi), diapazondan çıxarılıb"
        sp = _spill(p1, r.scenario, r.indicator, r.horizon)
        if sp is not None and not math.isnan(sp):
            vals[SPILL] = sp
        if len(vals) < 2:
            continue
        lo, hi = min(vals, key=vals.get), max(vals, key=vals.get)
        az = lambda x: _az(x, 2)
        txt = f"Diapazon {az(vals[lo])} ({LABEL[lo]}) … {az(vals[hi])} ({LABEL[hi]}) {r.effect_unit}. "
        if SPILL in vals:
            txt += (f"Üç nöqtə: statik döşəmə {az(vals.get('microsim', float('nan')))}, spill-over ilə "
                    f"{az(vals[SPILL])} (yeni minimumdan 25 %-ə qədər yuxarı maaşlar artımın yarısını alır), "
                    f"MikroUnit makro {az(vals.get('micro', float('nan')))}. ")
        txt += r.explanation_az
        s = scenarios.get(r.scenario, {})
        if mw_note and any(it["instrument"] == "min_wage" for it in s.get("instruments", [])) and \
                r.indicator in ("wage_nominal", "wage_real", "cpi", "infl", "gdp_real", "gdp_nonoil_real"):
            txt += " " + mw_note
        rows.append({"scenario": r.scenario, "scenario_name": r.scenario_name, "indicator": r.indicator,
                     "label_az": r.label_az, "horizon": r.horizon, "years": r.years, "effect_unit": r.effect_unit,
                     "low": round(vals[lo], 4), "low_method": lo, "high": round(vals[hi], 4), "high_method": hi,
                     "core_micro": vals.get("micro"), "n_methods": len(vals), "methods": ";".join(vals),
                     "excluded_az": excl, "explanation_az": txt})
    return pd.DataFrame(rows)


def continuity(p1: pd.DataFrame) -> pd.DataFrame:
    """2029/2030/2031 continuity check of the long-run splice (C4): the 2030→2031 step must not exceed
    max(tol, 2,5 × the 2029→2030 step, 12 % of the 2030 deviation — consistent with a 3-year half-life)."""
    from . import registry
    tol = float(registry.params("longrun").get("continuity_tol", 0.05))
    rows = []
    core = p1[((p1.engine == "micro") & (p1.year <= 2030)) | ((p1.engine == "longrun") & (p1.year == 2031))]
    for (sid, ind), g in core.groupby(["scenario", "indicator"]):
        if ind not in ("gdp_real", "gdp_nonoil_real", "employment", "budget_balance", "debt_pct", "cpi"):
            continue
        col = "delta" if ind in ("budget_balance", "debt_pct") else "delta_pct"
        v = g.set_index("year")[col]
        if ind == "budget_balance":            # direct cost may start/stop at 2030 by policy design: check before it
            fc = core[(core.scenario == sid) & (core.indicator == "fiscal_cost")].groupby("year")["value"].sum()
            v = v.add(fc.reindex(v.index).fillna(0.0))
            col = "fərq+xərc"
        if not {2029, 2030, 2031} <= set(v.index):
            continue
        s30, s31 = v[2030] - v[2029], v[2031] - v[2030]
        lim = max(tol if col == "delta_pct" or ind == "debt_pct" else 25.0, 2.5 * abs(s30), 0.12 * abs(v[2030]))
        rows.append({"scenario": sid, "indicator": ind, "measure": col, "v2029": round(v[2029], 4),
                     "v2030": round(v[2030], 4), "v2031": round(v[2031], 4), "step_2029_30": round(s30, 4),
                     "step_2030_31": round(s31, 4), "limit": round(lim, 4), "ok": bool(abs(s31) <= lim)})
    return pd.DataFrame(rows)
