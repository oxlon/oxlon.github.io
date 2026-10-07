"""FR5 — configurable KPI catalogue (config/kpi.csv): compute selected KPIs (user selects ≥ 5),
normalise across scenarios (min–max with direction), weighted multi-criteria score,
cost-effectiveness (score per 1 bn AZN of direct cost) and ranking. Outputs P5_.
External KPIs (risk, side effects) are read from output/P*_kpi_inputs.csv (scenario, kpi, value)."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import config, integrate as I
from .registry import ConfigError

MIN_SELECTED = 5


class KpiError(ValueError):
    pass


def catalogue() -> pd.DataFrame:
    df = pd.read_csv(config.KPI_CSV, dtype=str, keep_default_na=False)
    df["default_weight"] = pd.to_numeric(df["default_weight"], errors="coerce").fillna(0.0)
    if df["id"].duplicated().any():
        raise ConfigError("kpi.csv: təkrarlanan KPI id")
    bad = set(df["direction"]) - {"higher", "lower"}
    if bad:
        raise ConfigError(f"kpi.csv: direction yalnız higher/lower ola bilər ({bad})")
    return df.set_index("id", drop=False)


def select(ids=None, weights: dict | None = None) -> pd.DataFrame:
    cat = catalogue()
    ids = list(ids) if ids else list(cat.index[cat["default_selected"] == "yes"])
    unknown = [i for i in ids if i not in cat.index]
    if unknown:
        raise KpiError("naməlum KPI: " + ", ".join(unknown))
    if len(set(ids)) < MIN_SELECTED:
        raise KpiError(f"ən azı {MIN_SELECTED} fərqli göstərici seçilməlidir (seçilib: {len(set(ids))})")
    sel = cat.loc[list(dict.fromkeys(ids))].copy()
    for k, w in (weights or {}).items():
        if k in sel.index:
            sel.loc[k, "default_weight"] = float(w)
    return sel


def _hz(f, hz):
    return f[f.horizon.isin(hz.split("+"))]


def _core(fs):
    core = I.core_frame(fs)
    return core if len(core) else fs[fs.engine == "caem"]


def _eff(fs, ind, hz):
    if ind in I.PRIMARY_RISKFX:                       # same source as the P1 headline (verification 2)
        g = _hz(fs[(fs.engine == "riskfx") & (fs.indicator == ind)], hz)
        if len(g):
            return I.effect(g, ind)
    g = _core(fs)
    g = _hz(g[g.indicator == ind], hz)
    if g.empty:
        for e in ("caem", "microsim", "io"):
            g = _hz(fs[(fs.engine == e) & (fs.indicator == ind)], hz)
            if len(g):
                break
    return I.effect(g, ind)


DISAGREE = ["gdp_real", "cpi", "wage_nominal", "employment_hired"]


def _ranges(rg=None):
    if rg is not None:
        return rg
    p = config.OUTPUT / "P1_ranges.csv"
    return pd.read_csv(p) if p.exists() else None


def _bound(rg, sid, ind, hz, direction):
    """Conservative method value: lower bound for 'higher is better', upper bound otherwise (mean over horizons)."""
    if rg is None:
        return None
    g = rg[(rg.scenario == sid) & (rg.indicator == ind) & rg.horizon.isin(hz.split("+"))]
    if g.empty:
        return None
    return float((g["low"] if direction == "higher" else g["high"]).mean())


def value(fs: pd.DataFrame, k: pd.Series, ext: dict, conservative=False, rg=None) -> float:
    st, ind, hz = k["stat"], k["indicator"], k["horizon"]
    core = _core(fs)
    cost = _hz(core[core.indicator == "fiscal_cost"], hz)["delta"].sum()
    if st == "effect":
        if conservative:
            b = _bound(rg, fs.scenario.iloc[0], ind, hz, k["direction"])
            if b is not None:
                return b
        return _eff(fs, ind, hz)
    if st == "disagreement":
        if rg is None:
            return math.nan
        g = rg[(rg.scenario == fs.scenario.iloc[0]) & rg.indicator.isin(ind.split(";")) & rg.horizon.isin(hz.split("+"))]
        if g.empty:
            return 0.0                                    # only one method -> no measured disagreement
        cen = ((g["low"] + g["high"]) / 2).abs()            # central = midpoint of the method range
        return float(((g["high"] - g["low"]) / cen.clip(lower=0.1)).clip(upper=5.0).mean())
    if st == "sum":
        return float(cost)
    if st == "cost_gdp":
        g = _hz(core[core.indicator == "fiscal_cost"], hz).merge(
            _hz(core[core.indicator == "gdp_nominal"], hz)[["year", "baseline"]], on="year", suffixes=("", "_g"))
        return float((100 * g["delta"] / g["baseline_g"]).mean()) if len(g) else math.nan
    if st == "multiplier":
        d = _hz(core[core.indicator == "gdp_nominal"], hz)["delta"].sum()
        return float(d / cost) if abs(cost) > 1e-6 else math.nan
    if st == "cost_per_job":
        dj = _eff(fs, "employment_hired", "orta")
        b = _hz(core[core.indicator == "employment_hired"], "orta")["baseline"].mean()
        jobs = dj / 100 * b * 1000 if np.isfinite(dj) and np.isfinite(b) else math.nan
        return float(cost * 1000 / jobs) if jobs and abs(jobs) > 1 and abs(cost) > 1e-6 else math.nan  # thous. AZN/job
    if st == "elasticity":
        y = _eff(fs, "gdp_nonoil_real", hz)
        e = _eff(fs, ind, hz)
        return e / y if abs(y) > 1e-4 else math.nan
    if st == "ulc":
        w, y, e = _eff(fs, "wage_nominal", hz), _eff(fs, "gdp_nonoil_real", hz), _eff(fs, "employment", hz)
        return w - (y - e)
    if st == "share_gdp":
        g = _hz(core[core.indicator.isin([ind, "gdp_real"])], hz)
        p = g.pivot_table(index="year", columns="indicator", values=["baseline", "value"])
        if p.empty or ind not in p["value"]:
            return math.nan
        return float((100 * p["value"][ind] / p["value"]["gdp_real"] - 100 * p["baseline"][ind] / p["baseline"]["gdp_real"]).mean())
    if st in ("mean_prefix", "std_prefix"):
        g = _hz(core[core.indicator.str.startswith(ind)], hz).groupby("indicator")["delta_pct"].mean().dropna()
        if g.empty:
            return math.nan
        return float(g.mean() if st == "mean_prefix" else g.std(ddof=0))
    if st == "external":
        return ext.get((fs.scenario.iloc[0], k["id"]), math.nan)
    if st == "risk_profile":
        rp = _risk_profile()
        if rp is None:
            return math.nan
        g = rp[(rp.scenario == fs.scenario.iloc[0]) & (rp.variant == "base") & rp.kind.isin(ind.split(";"))]
        return float(g["dP"].max()) if len(g) else math.nan
    if st == "evidence":
        t = fs[fs.indicator == ind]["tier"]
        return float(t.isin(["A", "B", "C"]).mean()) if len(t) else math.nan
    raise ConfigError(f"kpi.csv: naməlum stat '{st}'")


def _risk_profile():
    p = config.OUTPUT / "P4_risk_profile.csv"
    return pd.read_csv(p, usecols=["scenario", "variant", "kind", "year", "dP"]) if p.exists() else None


def external(ext=None) -> dict:
    """External KPI inputs as {(scenario, kpi): value}. ext: None -> read output/P*_kpi_inputs.csv;
    a dict {(scenario, kpi): value}; or a DataFrame / list of rows with columns scenario, kpi, value."""
    if ext is None:
        return _external()
    if isinstance(ext, dict):
        return {k: float(v) for k, v in ext.items()}
    d = pd.DataFrame(ext)
    return {(r.scenario, r.kpi): float(r.value) for r in d.itertuples()}


def _external() -> dict:
    out = {}
    for p in config.OUTPUT.glob("P*_kpi_inputs.csv"):
        d = pd.read_csv(p)
        out.update({(r.scenario, r.kpi): float(r.value) for r in d.itertuples()})
    return out


def compute(p1: pd.DataFrame, ids=None, weights=None, ext=None, rg=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """p1: P1_effects frame; ids: selected KPI ids (>= 5; None = default selection); weights: {kpi: w};
    ext: external KPI inputs (see `external`; None = read output/P*_kpi_inputs.csv); rg: P1_ranges frame (None =
    read output/P1_ranges.csv) for the `model_disagreement` KPI and the conservative ranking
    (rank_conservative: every effect KPI takes the least favourable method bound from P1_ranges)."""
    from .engine_base import UNRELIABLE
    sel = select(ids, weights)
    ext = external(ext)
    p1 = p1[~p1.note_az.astype(str).str.contains(UNRELIABLE)]       # e.g. CAEM tax→fiscal results (C1)
    rg = _ranges(rg)
    v, r = _score(p1, sel, ext, False, rg)
    vc, rc = _score(p1, sel, ext, True, rg)
    rc = rc.sort_values("score", ascending=False).reset_index(drop=True)
    rc["rank_conservative"] = range(1, len(rc) + 1)
    r = r.merge(rc[["scenario", "score", "rank_conservative"]].rename(columns={"score": "score_conservative"}),
                on="scenario", how="left")
    r = r.sort_values("score", ascending=False)
    r.insert(0, "rank", range(1, len(r) + 1))
    return v, r


def _score(p1, sel, ext, conservative, rg):
    rows = []
    for sid, fs in p1.groupby("scenario", sort=False):
        for _, k in sel.iterrows():
            v = value(fs, k, ext, conservative, rg)
            rows.append({"scenario": sid, "scenario_name": fs.scenario_name.iloc[0], "kpi": k["id"],
                         "name_az": k["name_az"], "value": v, "unit": k["unit"], "direction": k["direction"],
                         "weight": k["default_weight"], "source_engine": k["source_engine"]})
    v = pd.DataFrame(rows)
    v["norm"] = np.nan
    for kid, g in v.groupby("kpi"):
        x = g["value"].astype(float)
        lo, hi = x.min(), x.max()
        if not np.isfinite(lo):
            continue
        n = pd.Series(0.5, index=g.index) if hi - lo < 1e-12 else (x - lo) / (hi - lo)
        if g["direction"].iloc[0] == "lower":
            n = 1 - n
        v.loc[g.index, "norm"] = n.where(x.notna())
    v["available"] = v["norm"].notna()
    rk = []
    for sid, g in v.groupby("scenario", sort=False):
        a = g[g.available]
        score = float((a.norm * a.weight).sum() / a.weight.sum()) if a.weight.sum() > 0 else math.nan
        c = p1[(p1.scenario == sid)]
        cost = _core(c)
        cost = cost[(cost.indicator == "fiscal_cost") & cost.horizon.isin(["qısa", "orta"])]["delta"].sum()
        rk.append({"scenario": sid, "scenario_name": g.scenario_name.iloc[0], "score": round(score, 4),
                   "kpis_used": int(g.available.sum()), "kpis_selected": int(len(g)),
                   "complete": bool(g.available.all()), "kpis_missing": ";".join(g[~g.available].kpi),
                   "cost_mln_azn": round(float(cost), 1),
                   "score_per_bn_azn": round(score / (cost / 1000), 4) if cost > 1 else math.nan,
                   "note_az": "; ".join(filter(None, [
                       (f"DİQQƏT: {int((~g.available).sum())} KPI hesablanmayıb ({', '.join(g[~g.available].kpi)}) — "
                        "bal yalnız mövcud KPI-lar üzrə (çəkilər yenidən normallaşdırılıb)") if not g.available.all() else "",
                       "xərcsiz və ya gəlir artıran alət" if cost <= 1 else "",
                       "XƏBƏRDARLIQ: işdən çıxarma/qeyri-formallaşma kanalı modeldə yoxdur — bal yuxarı sərhəddir (FR4)"
                       if c.note_az.astype(str).str.contains("YAN TƏSİR XƏBƏRDARLIĞI").any() else ""]))})
    return v, pd.DataFrame(rk)
