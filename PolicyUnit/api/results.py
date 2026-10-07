"""
results — integrate.run_scenario nəticəsindən API cavabı (RunResult): üfüqlər üzrə əsas göstəricilər (P1_headline
məntiqi), geniş cədvəl, sektorlar (FR2), sosial göstəricilər (FR3), metodların müqayisəsi (NFR2), KPI (FR5), qısa izah.
"""
import math

import pu
from fr4_bridge import _records

SECTOR_PREFIX = ("sector_va:", "sector_emp:", "sector_hired:", "sector_price:", "io_va:", "io_emp:", "io_price:", "io_go:")
SOCIAL = ("gini", "poverty_rate", "poverty_gap", "hh_disp_real", "decile", "ms_")
SYNTH_AZ = "SİNTETİK — real ev təsərrüfatı məlumatı deyil"


def num(x, nd=2):
    """Azerbaijani number format for prose: decimal comma, sign."""
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "—"
    if abs(x) < 0.5 * 10 ** -nd:
        return "0," + "0" * nd
    s = ("%+." + str(nd) + "f") % x
    return s.replace(".", ",").replace("-", "−")


def wide(hl):
    rows = {}
    for r in _records(hl):
        k = r["indicator"]
        d = rows.setdefault(k, {"indicator": k, "label_az": r["label_az"], "effect_unit": r["effect_unit"],
                                "source_engine": r["source_engine"], "tier": r["tier"], "qısa": None, "orta": None, "uzun": None})
        d[r["horizon"]] = r["effect"]
    return list(rows.values())


def sectors(f, limit=400):
    I = pu.P("integrate")
    g = f[f.indicator.astype(str).str.startswith(SECTOR_PREFIX)]
    out = []
    for (e, ind, hz), x in g.groupby(["engine", "indicator", "horizon"], sort=False):
        v = I.effect(x, ind)
        if v is None or not math.isfinite(v):
            continue
        out.append({"engine": e, "indicator": ind, "kind": ind.split(":", 1)[0], "sector": ind.split(":", 1)[1],
                    "label_az": x.label_az.iloc[0], "horizon": hz, "effect": round(v, 4), "unit": "% baza ilə fərq (orta)",
                    "tier": "".join(sorted(set(x.tier.astype(str))))})
    out.sort(key=lambda r: -abs(r["effect"]))
    return out[:limit]


def social(f):
    I = pu.P("integrate")
    g = f[(f.engine == "microsim") | f.indicator.astype(str).isin(["gini", "poverty_rate", "poverty_gap"])]
    out = []
    for (e, ind, hz), x in g.groupby(["engine", "indicator", "horizon"], sort=False):
        v = I.effect(x, ind)
        out.append({"engine": e, "indicator": ind, "label_az": x.label_az.iloc[0], "horizon": hz,
                    "effect": None if v is None or not math.isfinite(v) else round(v, 4), "unit": x.unit.iloc[0],
                    "group": x.group.iloc[0], "tier": "".join(sorted(set(x.tier.astype(str)))),
                    "note_az": SYNTH_AZ if e == "microsim" else ""})
    return out


def kpi_block(f, ids=None, weights=None, ext=None):
    """Single-scenario raw KPI values (normalisation needs ≥ 2 scenarios — see /compare)."""
    K = pu.P("kpi")
    sel = K.select(ids, weights)
    vals, ext = [], {**K.external(None), **(ext or {})}
    for _, k in sel.iterrows():
        try:
            v = K.value(f, k, ext)
        except Exception:
            v = float("nan")
        vals.append({"kpi": k["id"], "name_az": k["name_az"], "value": v, "unit": k["unit"], "direction": k["direction"],
                     "weight": float(k["default_weight"]), "horizon": k["horizon"], "source_engine": k["source_engine"]})
    return {"selected": list(sel.index), "values": vals, "min_selected": K.MIN_SELECTED}


def text(s, hl, fr4, cmp_rows):
    """Short Azerbaijani explanation (NFR3 text layer)."""
    by = {(r["indicator"], r["horizon"]): r for r in _records(hl)}
    parts = ["«%s» (%d-ci ildən):" % (s["name_az"], s["start_year"])]
    for ind, name, unit in (("gdp_real", "real ÜDM", "%"), ("infl", "inflyasiya", "f.b."), ("unemp_rate", "işsizlik", "f.b."),
                            ("employment_hired", "muzdlu məşğulluq", "%"), ("budget_balance_pct", "büdcə balansı (% ÜDM)", "f.b.")):
        xs = ["%s %s" % (hz, num(by[(ind, hz)]["effect"])) for hz in ("qısa", "orta", "uzun") if (ind, hz) in by]
        if xs:
            parts.append("%s — %s %s;" % (name, ", ".join(xs), unit))
    if len(parts) == 1:
        parts.append("əsas makro göstəricilərə təsir hesablanmadı (alət yalnız sektor/sosial kanallardan keçir).")
    se = [x for x in (fr4 or {}).get("items", []) if x.get("variant") == "base"]
    if se:
        top = max(se, key=lambda x: x.get("severity", 0))
        parts.append("Ən ciddi yan təsir: %s (%s)." % (top["name_az"], top["severity_az"]))
    elif fr4 and fr4.get("status") not in ("hesablanmadı",):
        parts.append("Qaydalar kitabxanası üzrə yan təsir aşkar edilmədi.")
    agree = [r for r in cmp_rows if r.get("sign_agree") is not None]
    if agree:
        parts.append("Metodların müqayisəsi: %d göstərici × üfüq cütündən %d-də işarələr uyğundur." %
                     (len(agree), sum(1 for r in agree if r["sign_agree"])))
    parts.append("Təsir = ssenari − eyni vintajlı baza (əks-faktual).")
    return " ".join(parts)


def build(s, r, fr4, kpi_ids=None, weights=None, detail="full"):
    I = pu.P("integrate")
    f = r["frame"]
    hl = I.headline(f) if len(f) else f.iloc[0:0]
    try:
        with pu.ENGINE_LOCK:
            cmp_df = I.method_comparison(f, {s["id"]: s}) if len(f) else None
        cmp_rows = _records(cmp_df)
    except Exception as e:
        cmp_rows = [{"error": "metod müqayisəsi alınmadı: %s" % e}]
    c = pu.P("config")
    engines = []
    for e, st in r["status"].items():
        engines.append({"id": e, "label_az": c.ENGINE_LABEL_AZ.get(e, e),
                        **{k: st.get(k) for k in ("status", "rows", "seconds", "message_az")}})
    ext = {(x["scenario"], x["kpi"]): x["value"] for x in (fr4 or {}).get("kpi_inputs", [])}
    warnings = [x["message_az"] for x in engines if x["status"] in ("xəta", "yoxdur") and x.get("message_az")]
    try:
        kb = kpi_block(f, kpi_ids, weights, ext) if len(f) else {"selected": [], "values": []}
    except Exception as e:
        kb = {"selected": [], "values": [], "error": str(e)}
        warnings.append("KPI: %s" % e)
    meta_v = {}
    for e, res in r["results"].items():
        meta_v.update((res.meta or {}).get("vintage") or {})
    out = {"scenario": s, "engines": engines, "engine_vintage": meta_v, "horizons": pu.horizons(s["start_year"]),
           "headline": _records(hl), "headline_wide": wide(hl), "sectors": sectors(f) if len(f) else [],
           "social": social(f) if len(f) else [], "comparison": cmp_rows, "side_effects": fr4, "kpi": kb,
           "text_az": text(s, hl, fr4, [x for x in cmp_rows if "error" not in x]),
           "warnings": warnings + list((fr4 or {}).get("warnings", [])), "engine_seconds": r["seconds"]}
    if detail == "full":
        out["effects"] = _records(f)
    return out
