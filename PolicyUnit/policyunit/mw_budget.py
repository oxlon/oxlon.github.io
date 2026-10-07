"""Budget cost of a minimum-wage increase (cost_rule `mw_budget`): budget-funded employees below or
near the new minimum wage are lifted to it, wages just above get a compression spill-over, and the
employer social contribution is added. Counted as government current spending (off-FR1 cost).

Data: DSK wage-band × sector distribution (004_11-12, Nov 2025; data/households/targets/wage_bands.csv,
built by ms_rawdata) for the budget sectors (fiscal_params `mw_budget_sectors`), scaled to FR4 budget-
funded employees (`fr4:budget`). Wages are uniform within bands; the open bottom band (< 400 AZN) is
placed at 400 (the 2025 minimum wage, full-time equivalent), the open top band at 3 000 AZN.
Uprating 2025 -> t (assumption, documented): wages up to 600 AZN (bottom grades tied to the minimum wage)
move with the baseline minimum wage (FR1 `minwage` / 400); wages from 1 000 AZN move with the FR3 budget-
sector average wage (`fr3:w_budget`, mean of the profile); linear blend in between; floor = baseline minimum.

  Δw_i = max(0, MW_new − w_i)                                   (lift to the new minimum)
       + κ·(MW_new − MW_base)·max(0, 1 − (w_i − MW_new)/(s·MW_new))  for w_i ≥ MW_new (spill-over)
  cost_t = 12 · (1 + ssc) · Σ n_i·Δw_i / 10⁶   (mln AZN)
κ = mw_spill_share, s = mw_spill_range, ssc = employer_ssc (fiscal_params.csv; assumptions)."""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd

from . import config, microbridge as mb, registry

BANDS = config.DATA / "households" / "targets" / "wage_bands.csv"
POINTS = 10


@lru_cache(maxsize=1)
def profile() -> tuple[np.ndarray, np.ndarray]:
    """(wage points AZN, employee shares) of the budget sectors, Nov 2025."""
    if not BANDS.exists():
        raise FileNotFoundError(f"əmək haqqı bölgüsü tapılmadı: {BANDS} (ms_rawdata.wage_bands)")
    p = registry.params("fiscal")
    secs = str(p.get("mw_budget_sectors", "pubadm;educ;health;art")).split(";")
    w = pd.read_csv(BANDS)
    w = w[(w.year == w.year.max()) & w.sector.isin(secs)].groupby(["lo", "hi"], as_index=False)["count"].sum()
    pts, n = [], []
    for r in w.itertuples():
        if r.lo <= 0:
            xs = np.full(POINTS, 400.0)
        elif not np.isfinite(r.hi):
            xs = np.full(POINTS, 3000.0)
        else:
            xs = r.lo + (np.arange(POINTS) + 0.5) / POINTS * (r.hi - r.lo)
        pts.append(xs)
        n.append(np.full(POINTS, r.count / POINTS))
    x, c = np.concatenate(pts), np.concatenate(n)
    return x, c / c.sum()


def cost_path(levels_pct, years) -> list[float]:
    """levels_pct: minimum-wage level change (%) per year -> budget cost mln AZN per year."""
    p = registry.params("fiscal")
    kappa, s, ssc = p.get("mw_spill_share", 0.5), p.get("mw_spill_range", 0.25), p.get("employer_ssc", 22.0)
    x, sh = profile()
    m0 = float((x * sh).sum())
    b = mb.baseline()
    mw = dict(zip(config.MICRO_YEARS, mb.exo_baseline("minwage")))
    wb = dict(zip(config.MICRO_YEARS, mb.series(b, "FR3", "fr3:w_budget")))
    s4 = b["results"]["FR4"]["series"]["fr4:budget"]
    nb = {y: float(s4[str(y)]) * 1000 for y in config.MICRO_YEARS}
    last = config.MICRO_YEARS[-1]
    blend = np.clip((x - 600.0) / 400.0, 0.0, 1.0)
    out = []
    for y, L in zip(years, levels_pct):
        if L == 0:
            out.append(0.0)
            continue
        yy = min(y, last)
        g = (1.05 ** (y - last)) if y > last else 1.0          # after 2030: wages/minimum wage +5 %/y (scaling)
        base_mw, mean_w, n = mw[yy] * g, wb[yy] * g, nb[yy]
        w = np.maximum(x * ((1 - blend) * base_mw / 400.0 + blend * mean_w / m0), base_mw)
        new_mw = base_mw * (1 + L / 100)
        lift = np.maximum(0.0, new_mw - w)
        spill = kappa * (new_mw - base_mw) * np.clip(1 - (w - new_mw) / (s * new_mw), 0, 1) * (w >= new_mw)
        dw = float((sh * (lift + spill)).sum())
        out.append(12 * (1 + ssc / 100) * dw * n / 1e6)
    return out


def affected_share(level_pct, year) -> float:
    """Share of budget-funded employees whose wage rises (lift or spill-over)."""
    x, sh = profile()
    b = mb.baseline()
    yy = min(year, config.MICRO_YEARS[-1])
    i = config.MICRO_YEARS.index(yy)
    base_mw = mb.exo_baseline("minwage")[i]
    bl = np.clip((x - 600.0) / 400.0, 0.0, 1.0)
    r_m = mb.series(b, "FR3", "fr3:w_budget")[i] / float((x * sh).sum())
    w = np.maximum(x * ((1 - bl) * base_mw / 400.0 + bl * r_m), base_mw)
    new_mw = base_mw * (1 + level_pct / 100)
    s = registry.params("fiscal").get("mw_spill_range", 0.25)
    return float(sh[w < new_mw * (1 + s)].sum())
