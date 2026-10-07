"""Core output stage: run scenarios through all engines and write P1_, N2_, P5_ (+ catalogue)."""
from __future__ import annotations

import json
import time

import pandas as pd

from . import catalog, config, integrate, kpi, registry, scenario as scn

OWNER = "core"


def run_scenarios(ids=None, log=print) -> tuple[pd.DataFrame, list[dict], dict]:
    ids = ids or scn.all_ids()
    frames, status, scen = [], [], {}
    for sid in ids:
        s = scn.load(sid)
        scen[sid] = s
        r = integrate.run_scenario(s)
        frames.append(r["frame"])
        for e, st in r["status"].items():
            status.append({"scenario": sid, "engine": e, **{k: v for k, v in st.items() if k != "trace"}})
            if st["status"] == "xəta":
                log(f"  XƏTA {sid}/{e}: {st['message_az'][:300]}")
        log(f"  {sid}: {len(r['frame'])} sətir, {r['seconds']} s, mühərriklər: "
            + ", ".join(f"{e}={st['status']}" for e, st in r["status"].items()))
    p1 = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=integrate.P1_COLS)
    return p1, status, scen


def _merge(df: pd.DataFrame, name: str, ids) -> pd.DataFrame:
    """Merge mode (NFR4 single-scenario run): replace only the rows of `ids` in an existing output."""
    p = config.OUTPUT / name
    if not ids or not p.exists() or "scenario" not in df.columns:
        return df
    old = pd.read_csv(p, low_memory=False)
    if "scenario" not in old.columns:
        return df
    keep = old[~old.scenario.isin(ids)]
    return pd.concat([keep, df], ignore_index=True) if len(keep) else df


def write_all(ids=None, kpis=None, log=print) -> dict:
    """All scenarios (ids=None) or MERGE mode: only `ids` are recomputed, their rows replaced in P1_/N2_."""
    t0 = time.perf_counter()
    config.ensure_dirs()
    p1, status, scen = run_scenarios(ids, log)
    if ids:
        log(f"  birləşdirmə rejimi: yalnız {', '.join(ids)} sətirləri əvəz olunur")
    out = {}
    p1_new = p1
    p1 = _merge(p1, "P1_effects.csv", ids)
    out["P1_effects.csv"] = catalog.write_csv(
        p1, "P1_effects.csv", OWNER, "FR1: ssenari × mühərrik × göstərici × il üzrə makro/mikro təsirlər "
        "(baza, ssenari, fərq, % fərq, üfüq qısa/orta/uzun, metod, sübut səviyyəsi)")
    hl = _merge(integrate.headline(p1_new), "P1_headline.csv", ids)
    out["P1_headline.csv"] = catalog.write_csv(
        hl, "P1_headline.csv", OWNER, "FR1: əsas göstəricilərin üfüq üzrə orta təsiri (əsas metod: MikroUnit + "
        "uzun müddət ekstrapolyasiyası; kanal yoxdursa CAEM)")
    n2_new = integrate.method_comparison(p1_new, scen)
    n2 = _merge(n2_new, "N2_method_comparison.csv", ids)
    out["N2_method_comparison.csv"] = catalog.write_csv(
        n2, "N2_method_comparison.csv", OWNER, "NFR2: eyni ssenari üçün ≥2 metodun nəticəsi, fərq (spread), işarə "
        "uyğunluğu və Azərbaycan dilində izah")
    from . import ranges
    rg = _merge(ranges.table(n2_new, scen, p1_new), "P1_ranges.csv", ids)
    out["P1_ranges.csv"] = catalog.write_csv(
        rg, "P1_ranges.csv", OWNER, "FR1/NFR2: əsas göstəricilər metodlar arası DİAPAZON kimi (aşağı/yuxarı sərhəd, "
        "metod, izah; minimum əmək haqqında NFR1 sitatı)")
    ct = _merge(ranges.continuity(p1_new), "P1_longrun_continuity.csv", ids)
    out["P1_longrun_continuity.csv"] = catalog.write_csv(
        ct, "P1_longrun_continuity.csv", OWNER, "Uzun müddət ekstrapolyasiyasının kəsilməzlik yoxlaması: 2029/2030/2031 "
        "sapmaları və addımlar (ok = 2031 addımı limit daxilində)")
    if len(ct) and not ct.ok.all():
        log(f"  XƏBƏRDARLIQ: kəsilməzlik yoxlaması {int((~ct.ok).sum())} sətirdə uğursuz")
    st = _merge(pd.DataFrame(status), "P1_run_status.csv", ids)
    out["P1_run_status.csv"] = catalog.write_csv(st, "P1_run_status.csv", OWNER,
                                                 "Hər ssenari üçün mühərriklərin vəziyyəti (ok / tətbiq edilmir / xəta)")
    meta = {"run_at": pd.Timestamp.now().isoformat(timespec="seconds"), "scenarios": sorted(p1.scenario.unique()), "recomputed": list(scen),
            "seconds": round(time.perf_counter() - t0, 1), "long_end": config.LONG_END,
            "catalogue_errors": registry.validate_catalogue()}
    try:
        from . import freshness
        meta["vintage"] = freshness.current()
        from . import caem_core
        meta["vintage"]["caem_pinned_ok"] = caem_core.vintage_status()["pinned_ok"]
    except Exception as e:  # noqa: BLE001
        meta["vintage_error"] = str(e)
    (config.OUTPUT / "P1_run_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    catalog.register("P1_run_meta.json", OWNER, "İşin metaməlumatı: baza vintaj id-ləri (MikroUnit, CAEM md5), vaxt",
                     list(meta))
    try:
        refresh_docs(p1, log)
    except Exception as e:  # noqa: BLE001
        log(f"  docs AUTO yenilənmədi: {e}")
    return {"files": out, "meta": meta, "p1": p1, "headline": hl, "n2": n2}


def write_kpi(ids=None, kpis=None, log=print, p1: pd.DataFrame | None = None, ext=None) -> dict:
    """P5 stage (runs AFTER FR4/NFR1 so external KPI inputs are final): reads output/P1_effects.csv."""
    out = {}
    if p1 is None:
        p = config.OUTPUT / "P1_effects.csv"
        if not p.exists():
            log("  P1_effects.csv yoxdur — KPI buraxıldı")
            return out
        p1 = pd.read_csv(p)
    # KPIs are always normalised and ranked over ALL scenarios in P1 (ids only trigger the recomputation)
    try:
        vals, rank = kpi.compute(p1, kpis, ext=ext)
    except kpi.KpiError as e:
        log(f"  KPI XƏTA: {e}")
        return out
    out["P5_kpi_values.csv"] = catalog.write_csv(
        vals, "P5_kpi_values.csv", OWNER, "FR5: seçilmiş KPI-ların dəyərləri, normallaşdırılmış bal (0–1) və çəkilər "
        "(FR4 risk/yan təsir girişləri daxil)")
    out["P5_ranking.csv"] = catalog.write_csv(
        rank, "P5_ranking.csv", OWNER, "FR5: çoxkriteriyalı bal, xərc-effektivlik (bal / 1 mlrd AZN) və ssenari reytinqi")
    cat = kpi.catalogue().copy()
    cat["selected"] = cat["id"].isin(kpis or cat.index[cat.default_selected == "yes"])
    out["P5_kpi_catalogue.csv"] = catalog.write_csv(cat, "P5_kpi_catalogue.csv", OWNER,
                                                    "FR5: KPI kataloqu (config/kpi.csv) + bu işdə seçilənlər",
                                                    "konfiqurasiya dəyişdikdə")
    log(f"  yazıldı: {', '.join(out)}")
    return out


def refresh_docs(p1: pd.DataFrame | None = None, log=print):
    """Render the <!-- AUTO:... --> blocks of docs/Metodologiya_core.md from config/outputs (no hand-typed numbers)."""
    import re
    from . import mw_budget, registry
    doc = config.DOCS / "Metodologiya_core.md"
    if not doc.exists():
        return
    lp = registry.params("longrun")
    az = lambda x, d=1: f"{x:.{d}f}".replace(".", ",") if isinstance(x, (int, float)) else str(x)
    blocks = {"longrun": (f"- α = {az(lp.get('alpha_k'), 2)}; θ_g = {az(lp.get('public_capital_elast'), 2)}; "
                          f"tələb yarımömrü = {az(lp.get('demand_halflife'))} il; məşğulluq yarımömrü = "
                          f"{az(lp.get('labour_halflife'))} il; ψ = {az(lp.get('active_demand_retained'), 2)}; "
                          f"kəsilməzlik tolerantlığı = {az(lp.get('continuity_tol'), 2)}")}
    p1 = p1 if p1 is not None else pd.read_csv(config.OUTPUT / "P1_effects.csv", low_memory=False)
    g = p1[(p1.scenario == "mw20_2027") & (p1.engine == "micro") & (p1.indicator == "fiscal_cost") & p1.year.between(2027, 2030)]
    if len(g):
        blocks["mw_budget"] = (f"  ≈ {az(g.value.min())}–{az(g.value.max())} mln AZN/il (2027–2030); büdcə işçilərinin "
                               f"~{az(100 * mw_budget.affected_share(20, 2027), 0)} %-i təsirlənir")
    t = doc.read_text(encoding="utf-8")
    for k, v in blocks.items():
        t = re.sub(rf"(<!-- AUTO:{k} -->\n).*?(<!-- /AUTO -->)", lambda m: m.group(1) + v + "\n" + m.group(2), t, flags=re.S)
    doc.write_text(t, encoding="utf-8")
    log("  docs/Metodologiya_core.md AUTO blokları yeniləndi")
