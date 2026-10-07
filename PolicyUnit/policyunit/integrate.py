"""Scenario -> adapters -> engines -> combined outcome table (P1), horizon classification and the
headline summary. Method comparison (NFR2) is in `compare.py` (re-exported as method_comparison).

ctx passed to every engine: {"scenario": s, "results": {engine: Result} (engines run so far, in
config.ENGINE_ORDER — micro first, longrun last), "registry": registry, "config": config}."""
from __future__ import annotations

import time
import traceback

import pandas as pd

from . import config, registry
from .engine_base import OUT_COLS, Result, horizon

P1_COLS = ["scenario", "scenario_name", "start_year", "engine", "horizon"] + OUT_COLS
HEADLINE = ["gdp_real", "gdp_nonoil_real", "cpi", "infl", "unemp_rate", "employment", "employment_hired",
            "wage_real", "hh_disp_real", "budget_balance_pct", "debt_pct", "ca_proxy", "fiscal_cost",
            "budget_balance"]
RATE_KIND = {"infl", "unemp_rate", "budget_balance_pct", "debt_pct", "policy_rate", "revenue_pct", "gini",
             "poverty_rate", "poverty_gap"}
PRIMARY_RISKFX = {"cpi", "infl"}     # FR4: RiskUnit's calibrated FX pass-through is the headline FX→CPI source
SUM_KIND = {"fiscal_cost", "budget_balance", "ca_proxy", "sofaz_assets"}


def engines_for_scenario(s: dict) -> list[str]:
    want = set()
    for it in s["instruments"]:
        want.update(registry.engines_for(it["instrument"]))
    if "micro" in want:
        want.add("longrun")              # every MicroUnit-based scenario gets the 2031+ extension
    return [e for e in config.ENGINE_ORDER if e in want]


def run_scenario(s: dict, engines: list[str] | None = None) -> dict:
    t0 = time.perf_counter()
    ctx = {"scenario": s, "results": {}, "registry": registry, "config": config}
    status = {}
    for e in engines or engines_for_scenario(s):
        try:
            mod = registry.engine_module(e)
        except Exception as err:  # noqa: BLE001 — a plug-in that fails to import must not stop the others
            status[e] = {"status": "xəta", "message_az": f"modul yüklənmədi: {type(err).__name__}: {err}"}
            continue
        if mod is None:
            status[e] = {"status": "yoxdur", "message_az": f"{config.ENGINE_LABEL_AZ.get(e, e)}: modul hələ qoşulmayıb"}
            continue
        te = time.perf_counter()
        try:
            res = mod.run(s, ctx)
        except Exception as err:  # noqa: BLE001 — one engine failing must not hide the others
            status[e] = {"status": "xəta", "message_az": f"{type(err).__name__}: {err}",
                         "trace": traceback.format_exc(limit=4)}
            continue
        if not isinstance(res, Result):
            status[e] = {"status": "xəta", "message_az": "mühərrik Result qaytarmadı"}
            continue
        ctx["results"][e] = res
        status[e] = {"status": "ok" if len(res.frame) else "tətbiq edilmir",
                     "rows": len(res.frame), "seconds": round(time.perf_counter() - te, 2),
                     "message_az": "; ".join(res.meta.get("warnings", []))}
    return {"scenario": s, "results": ctx["results"], "status": status, "frame": combine(s, ctx["results"]),
            "seconds": round(time.perf_counter() - t0, 2)}


def combine(s: dict, results: dict) -> pd.DataFrame:
    parts = []
    for e, r in results.items():
        if r.frame.empty:
            continue
        f = r.frame.copy()
        f.insert(0, "engine", e)
        parts.append(f)
    if not parts:
        return pd.DataFrame(columns=P1_COLS)
    f = pd.concat(parts, ignore_index=True)
    f["horizon"] = [horizon(y, s["start_year"]) for y in f["year"]]
    f = f[f["year"] >= s["start_year"]] if s["start_year"] > config.FIRST_YEAR else f
    f["scenario"], f["scenario_name"], f["start_year"] = s["id"], s["name_az"], s["start_year"]
    return f[P1_COLS].reset_index(drop=True)


def effect(g: pd.DataFrame, ind: str) -> float:
    """Horizon effect: mean Δ% (levels), mean Δ pp (rates), sum Δ (flows, mln AZN)."""
    if g.empty:
        return float("nan")
    if ind in SUM_KIND:
        return float(g["delta"].sum())
    col = "delta" if ind in RATE_KIND else "delta_pct"
    return float(g[col].mean())


def core_frame(f: pd.DataFrame) -> pd.DataFrame:
    """Core method = MicroUnit chain (≤2030) + its structural long-run extension (>2030)."""
    m = f[(f.engine == "micro") | ((f.engine == "longrun") & (f.year > config.MICRO_YEARS[-1]))].copy()
    m["engine"] = "micro"
    return m


def headline(f: pd.DataFrame) -> pd.DataFrame:
    """P1 headline: per scenario × indicator × horizon, preferred method = core (micro+longrun),
    fallback CAEM when the core has no channel."""
    from .engine_base import UNRELIABLE
    rows = []
    for sid, fs in f.groupby("scenario", sort=False):
        core = core_frame(fs)
        caem = fs[(fs.engine == "caem") & ~fs.note_az.astype(str).str.contains(UNRELIABLE)]
        rfx = fs[fs.engine == "riskfx"]
        for ind in HEADLINE:
            src, g0 = ("micro", core) if (core.indicator == ind).any() else ("caem", caem)
            if ind in PRIMARY_RISKFX and (rfx.indicator == ind).any():
                src, g0 = "riskfx", rfx                 # RiskUnit FX pass-through = primary FX→CPI source
            g0 = g0[g0.indicator == ind]
            if g0.empty:
                continue
            for hz in ("qısa", "orta", "uzun"):
                g = g0[g0.horizon == hz]
                if g.empty:
                    continue
                rows.append({"scenario": sid, "scenario_name": fs.scenario_name.iloc[0], "indicator": ind,
                             "label_az": g.label_az.iloc[0], "horizon": hz,
                             "years": f"{g.year.min()}–{g.year.max()}", "effect": round(effect(g, ind), 4),
                             "effect_unit": _eff_unit(ind), "method": g.method.iloc[-1], "source_engine": src,
                             "tier": "".join(sorted(set(g.tier))), "note_az": g.note_az.iloc[-1]})
    return pd.DataFrame(rows)


def _eff_unit(ind: str) -> str:
    if ind in SUM_KIND:
        return "mln AZN (müddət üzrə cəm)"
    return "f.b. (orta)" if ind in RATE_KIND else "% baza ilə fərq (orta)"


def method_comparison(f: pd.DataFrame, scenarios: dict | None = None) -> pd.DataFrame:
    from . import compare
    return compare.table(f, scenarios or {})
