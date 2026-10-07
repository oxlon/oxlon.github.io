"""Engine `riskfx` — RiskUnit's calibrated FX transmission (R03; riskunit/fx.py, 2015–17 episode) as the
primary FX → CPI pass-through source (FR4). Parameters are READ from RiskUnit/output/FR1_fx_transmission.csv
(no RiskUnit import, nothing written there). For a level path of AZN/USD x_t (log points vs baseline):
  CPI level   = pt · (Σ_{j<t} Δx_j + w0·Δx_t)       (share w0 in the event year, the rest next year)
  non-oil GDP = L_nonoil · (Σ_{j<t} Δx_j + w0g·Δx_t)  (2015–16 level analogue)
  debt/GDP    = s_ext · debt/GDP · (e^x − 1)                                 (FX-debt revaluation)
NB: in-sample for the 2015 devaluation (NFR1); stand-alone calibrated totals (no chain layering here)."""
from __future__ import annotations

import math

import pandas as pd

from . import config, fiscal, microbridge as mb, registry, scenario as scn
from .engine_base import Result, empty_result, row

ENGINE = "riskfx"
METHOD = "RiskUnit FX ötürməsi (kalibrlənmiş 2015–17)"
SRC = config.RISK_ROOT / "output" / "FR1_fx_transmission.csv"


def params() -> dict:
    d = pd.read_csv(SRC)
    d = d[d["setir_novu"] == "parametr"]
    return {r.parametr: float(r.deyer) for r in d.itertuples()}


def run(s: dict, ctx: dict | None = None) -> Result:
    its = [it for it in s["instruments"] if not registry.adapters_for(ENGINE, it["instrument"]).empty]
    if not its:
        return empty_result(ENGINE, "RiskUnit FX ötürməsi yalnız məzənnə alətləri üçündür")
    if not SRC.exists():
        return empty_result(ENGINE, f"RiskUnit FX parametrləri tapılmadı: {SRC}")
    p = params()
    pt, w0, L, w0g, sx = p["pt_episode"], p["w0"], p["L_nonoil"], p["w0g"], p["s_ext"]
    years = list(range(config.FIRST_YEAR, config.LONG_END + 1))
    lev = [0.0] * len(years)
    for it in its:
        lev = [a + b for a, b in zip(lev, scn.path(it, years))]
    x = [math.log(1 + v / 100) for v in lev]
    dx = [x[0]] + [x[i] - x[i - 1] for i in range(1, len(x))]
    b = mb.baseline()
    debt = dict(zip(config.MICRO_YEARS, mb.series(b, "FR1", "fr1:debt_azn")))
    gdp = fiscal.gdp_nominal()
    note = (f"{METHOD}: ötürmə {pt:.2f} (hadisə ilində {w0:.0%}), qeyri-neft səviyyə itkisi {L:.1f} %/log, "
            f"xarici borc payı {sx:.2f}; 2015 devalvasiyası kalibrləmə nümunəsinə daxildir (in-sample)")
    rows, prev_c = [], 0.0
    for i, y in enumerate(years):
        c = pt * (sum(dx[:i]) + w0 * dx[i])            # step j: share w0 in year j, full from j+1
        gq = L * (sum(dx[:i]) + w0g * dx[i])
        dpct = 100 * (math.exp(c) - 1)
        rows.append(row("cpi", "İstehlak qiymətləri indeksi", "2015 = 100", y, float("nan"), float("nan"),
                        METHOD, "C", "makro", note, delta=float("nan"), delta_pct=dpct))
        rows.append(row("infl", "İnflyasiya (İQİ)", "%", y, float("nan"), float("nan"), METHOD, "C", "makro",
                        note, delta=100 * (c - prev_c), delta_pct=100 * (c - prev_c)))
        rows.append(row("gdp_nonoil_real", "Real qeyri-neft ÜDM", "mln AZN 2015", y, float("nan"), float("nan"),
                        METHOD, "D", "makro", note, delta=float("nan"), delta_pct=gq))
        dr = debt.get(min(y, config.MICRO_YEARS[-1])) / gdp[min(y, config.MICRO_YEARS[-1])] * 100
        rows.append(row("debt_pct", "Dövlət borcu (ÜDM-ə %)", "% ÜDM", y, float("nan"), float("nan"), METHOD,
                        "D", "fiskal", note, delta=sx * dr * (math.exp(x[i]) - 1), delta_pct=sx * dr * (math.exp(x[i]) - 1)))
        prev_c = c
    return Result(ENGINE, pd.DataFrame(rows), {"params": p, "warnings": [], "assumptions": [note],
                                               "vintage": {"riskunit_fx": str(SRC)}})
