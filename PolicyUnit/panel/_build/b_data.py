"""b_data.py — the data bundles of the Siyasət paneli (window.POL.<bundle>.<output file stem> = compact table).

Bundles: core (always loaded: headline effects, KPI, scenario catalogue, instruments, run status), eff (P1_effects —
large, lazy), io (P2_*, D_io_*), soc (P3_*), risk (P4_*), cmp (N2_*), val (V_*). Every output file goes into exactly one
bundle by prefix; REQUIRED lists the files the pages read by name — a missing one fails the build."""
import json

from . import bcore as C

# files the pages read by name (the build stops if one is missing)
REQUIRED = {
    "core": ["P1_headline.csv", "P1_run_status.csv", "P1_run_meta.json", "P5_kpi_catalogue.csv", "P5_kpi_values.csv",
             "P5_ranking.csv", "P3_microsim_headline.csv"],
    "eff": ["P1_effects.csv"],
    "io": ["P2_io_affected_sectors.csv", "P2_io_multipliers.csv", "P2_io_linkages.csv", "P2_io_key_sectors.csv",
           "P2_io_competitiveness.csv", "P2_io_price_shocks.csv", "P2_io_scenarios.csv", "P2_io_ghosh_supply.csv",
           "P2_io_update_2025.csv", "P2_io_update_info.csv", "D_io_sector_map.csv", "D_io_tables.csv"],
    "soc": ["P3_microsim_baseline.csv", "P3_microsim_deciles.csv", "P3_microsim_employment.csv",
            "P3_microsim_fiscal.csv", "P3_microsim_indicators.csv"],
    "risk": [],          # filled from P4_REQUIRED (FR4 outputs)
    "cmp": ["N2_method_comparison.csv"],
    "val": ["V_nfr1_events.csv", "V_nfr1_comparisons.csv", "V_nfr1_methods.csv", "V_nfr1_observed.csv",
            "V_nfr1_tolerance.csv", "V_nfr1_run_meta.csv"],
}
P4_REQUIRED = ["P4_side_effects.csv", "P4_mitigation.csv", "P4_risk_profile.csv", "P4_sensitivity.csv",
               "P4_side_effect_scenarios.csv", "P4_uncertainty_bands.csv", "P4_kpi_inputs.csv"]
PREFIX = [("P1_effects", "eff"), ("P1_", "core"), ("P5_", "core"), ("P3_microsim_headline", "core"), ("P2_", "io"),
          ("D_", "io"), ("P3_", "soc"), ("P4_", "risk"), ("N2_", "cmp"), ("V_", "val")]
LAZY = ["eff", "io", "soc", "risk", "cmp", "val"]
SIG = {"eff": 6, "io": 6, "soc": 6, "cmp": 6}


def bundle_of(name):
    for pre, b in PREFIX:
        if name.startswith(pre):
            return b
    return None


def auto_pool(df):
    """String columns with repeated values → pooled (index into a string list) to keep bundles small."""
    if df is None or not len(df):
        return ()
    return tuple(c for c in df.columns if df[c].dtype == object and df[c].nunique() < 0.6 * len(df))


def tab(name, bundle, tr, required=True, sig=7, drop=()):
    d = C.csv(name, bundle, required=required)
    if d is None:
        return None
    d = d.drop(columns=[c for c in drop if c in d.columns])
    d = tr.df(d)
    return C.table(d, sig=sig, pool=auto_pool(d))


def scenarios(tr):
    """config/scenarios/*.json (the official scenario files) → list (sorted by id)."""
    out = []
    for p in sorted((C.CONFIG / "scenarios").glob("*.json")):
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  xəbərdarlıq — {p.name}: JSON oxunmur ({e})")
            continue
        s["_file"] = p.name
        out.append(tr.deep(s, skip=("id", "instrument", "unit", "target", "financing", "years", "_file")))
    return out


def cfg_tab(name, tr, keep_default_na=True):
    d = C.cfg(name, keep_default_na=keep_default_na)
    return None if d is None else C.table(tr.df(d), pool=auto_pool(d))


FRG = {"makro": "FR1 makro", "fiskal": "FR1 fiskal", "əmək": "FR1 əmək", "xarici": "FR1 xarici", "monetar": "FR1 monetar",
       "sosial": "FR1 sosial", "uzun": "FR1 uzun müddət", "sektor": "FR1 mikro: sektor (FR10)", "bazar": "FR1 mikro: bazar (FR12)",
       "xidmət": "FR1 mikro: xidmətlər (FR5)", "regional": "FR1 mikro: regionlar"}


def glossary(tr):
    """Output-variable glossary: every indicator code that appears in results → Azerbaijani label, unit, area, engines, files."""
    parts = []
    for f, eng in [("P1_effects.csv", None), ("P2_io_scenarios.csv", "io"), ("P3_microsim_indicators.csv", "microsim")]:
        d = C.csv(f, bundle_of(f), required=False)
        if d is None:
            continue
        d = d[["indicator", "label_az", "unit", "group"] + (["engine"] if "engine" in d.columns else [])].copy()
        if eng:
            d["engine"] = eng
        d["file"] = f
        parts.append(d.drop_duplicates(["indicator", "engine"]))
    if not parts:
        return None
    a = C.pd.concat(parts, ignore_index=True)
    a["area"] = [("FR2 IO" if e == "io" else "FR3 mikrosimulyasiya" if e == "microsim" else FRG.get(str(g), "FR1")) for e, g in zip(a["engine"], a["group"])]
    g = a.groupby("indicator", sort=True).agg(label_az=("label_az", "first"), unit=("unit", "first"), area=("area", "first"),
                                               engines=("engine", lambda x: ";".join(sorted(set(map(str, x))))),
                                               files=("file", lambda x: ";".join(sorted(set(x)))))
    g = tr.df(g.reset_index())
    return C.table(g, pool=("unit", "area", "engines", "files"))


def kpi_matrix():
    """Raw value of EVERY catalogue KPI per scenario (PolicyUnit's own policyunit.kpi on P1_effects, read-only) so the
    KPI page can re-rank for any user selection; falls back to P5_kpi_values (default selection only)."""
    import sys
    try:
        sys.path.insert(0, str(C.UNIT))
        from policyunit import kpi
        p1 = C.read_retry(C.OUT / "P1_effects.csv")
        v, _ = kpi.compute(p1, ids=list(kpi.catalogue()["id"]))
        v = v[["scenario", "kpi", "value"]].sort_values(["scenario", "kpi"])
        return C.table(v, sig=7, pool=("scenario", "kpi"))
    except Exception as e:  # noqa: BLE001
        print(f"  xəbərdarlıq — bütün KPI-ların matrisi hesablanmadı ({type(e).__name__}: {e}); yalnız P5_kpi_values")
        return None
    finally:
        if str(C.UNIT) in sys.path:
            sys.path.remove(str(C.UNIT))


def build(tr):
    """→ list of (bundle name, object)."""
    files = sorted({p.name for p in C.OUT.glob("*.csv")} | {p.name for p in C.OUT.glob("*.json")})
    req = {k: list(v) for k, v in REQUIRED.items()}
    req["risk"] = list(P4_REQUIRED)
    B = {b: {} for b in ["core"] + LAZY}
    for b, names in req.items():
        for n in names:
            if n not in files:
                C.MISSING.append(n)
    for f in files:
        b = bundle_of(f)
        if b is None or f.endswith(".json"):
            continue
        stem = f.rsplit(".", 1)[0]
        B[b][stem] = tab(f, b, tr, sig=SIG.get(b, 7))
    meta = C.jsonf("P1_run_meta.json", "core") or {}
    core = B["core"]
    core["_meta"] = {"run": meta, "lazy": LAZY, "files": {b: sorted(k for k in B[b] if not k.startswith("_")) for b in LAZY}}
    core["scen"] = scenarios(tr)
    se = C.csv("P4_side_effects.csv", "risk", required=False)
    summ = {}
    if se is not None and len(se):
        b0 = se[se["variant"] == "base"] if "variant" in se.columns else se
        for sc, d in b0.groupby("scenario"):
            summ[str(sc)] = {"n": int(len(d)), "max": int(d["severity"].max()), "n3": int((d["severity"] >= 3).sum())}
    core["_meta"]["se"] = summ
    core["kpi_all"] = kpi_matrix()
    core["glossary"] = glossary(tr)
    io = C.csv("P2_io_affected_sectors.csv", "io", required=False)
    core["_meta"]["ioscen"] = [] if io is None else [[a, tr(b)] for a, b in io[["scenario", "scenario_name_az"]].drop_duplicates("scenario").itertuples(index=False)]
    for n in ["instruments.csv", "io_sectors.csv", "indicators.csv", "adapters.csv"]:
        core["cfg_" + n[:-4]] = cfg_tab(n, tr, keep_default_na=False)
    return [(b, B[b]) for b in ["core"] + LAZY]
