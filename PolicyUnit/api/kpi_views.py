"""
kpi_views — FR5: KPI kataloqu (config/kpi.csv), istifadəçinin saxladığı KPI dəstləri (SQLite «kpiset»: ≥ 5 KPI +
çəkilər) və ssenarilərin müqayisəsi/reytinqi (policyunit.kpi.compute; tək ssenari nəticələri API hesablamalarından).
"""
import json, math

import apidb, pu
from apicore import ApiError, new_id, now_iso
from fr4_bridge import _records


def resolve(cfg, body):
    """(ids|None, weights|None, source) from {kpis, weights} or {kpi_set}; validated (≥ 5) → 422."""
    ids, w, src = body.get("kpis"), body.get("weights"), "istifadəçi"
    if body.get("kpi_set"):
        ks = get_set(cfg, body["kpi_set"])
        ids, w, src = ks["kpis"], ks["weights"] or {}, "dəst: %s" % ks["name"]
    if not ids:
        src = "standart seçim (config/kpi.csv default_selected)"
    check(ids, w)
    return ids or None, w or None, src


def check(ids, weights):
    K = pu.P("kpi")
    if ids is not None and not isinstance(ids, list):
        raise ApiError(400, "bad_parameter", "kpis siyahı olmalıdır")
    if weights is not None:
        if not isinstance(weights, dict):
            raise ApiError(400, "bad_parameter", "weights obyekt olmalıdır ({kpi: çəki})")
        for k, v in weights.items():
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
                raise ApiError(422, "bad_weight", "«%s» çəkisi mənfi olmayan ədəd olmalıdır" % k)
        if ids and sum(float(weights.get(i, 1.0)) for i in ids) <= 0:
            raise ApiError(422, "bad_weight", "Çəkilərin cəmi sıfırdan böyük olmalıdır")
    try:
        sel = K.select(ids, weights)
    except K.KpiError as e:
        raise ApiError(422, "kpi_selection", "KPI seçimi yanlışdır: %s" % e, extra={"min_selected": K.MIN_SELECTED})
    return sel


def catalogue():
    K = pu.P("kpi")
    cat = K.catalogue()
    return {"kpis": _records(cat), "n": len(cat), "min_selected": K.MIN_SELECTED,
            "default_selected": list(cat.index[cat["default_selected"] == "yes"]),
            "stats": sorted(set(cat["stat"])), "horizons": ["qısa", "orta", "uzun", "qısa+orta"]}


# ------------------------------------------------------------------ saved sets
def _set_row(r):
    return {"id": r["id"], "name": r["name"], "kpis": r["kpis"], "weights": r["weights"] or {}, "note": r["note"],
            "actor": r["actor"], "created": r["created"], "updated": r["updated"]}


def list_sets(cfg):
    return [_set_row(r) for r in apidb.query(cfg.db, "SELECT * FROM kpiset ORDER BY updated DESC", (), ("kpis", "weights"))]


def get_set(cfg, sid):
    r = apidb.query(cfg.db, "SELECT * FROM kpiset WHERE id=?", (sid,), ("kpis", "weights"))
    if not r:
        raise ApiError(404, "not_found", "KPI dəsti tapılmadı: %s" % sid)
    return _set_row(r[0])


def save_set(cfg, body, actor, sid=None):
    if not isinstance(body, dict):
        raise ApiError(400, "bad_json", "JSON obyekt gözlənilir")
    cur = get_set(cfg, sid) if sid else {}
    name = str(body.get("name", cur.get("name")) or "").strip()
    if not name:
        raise ApiError(400, "bad_parameter", "«name» tələb olunur")
    ids = body.get("kpis", cur.get("kpis"))
    w = body.get("weights", cur.get("weights")) or {}
    if not ids:
        raise ApiError(422, "kpi_selection", "kpis siyahısı tələb olunur (ən azı %d KPI)" % pu.P("kpi").MIN_SELECTED)
    check(ids, w)
    unknown_w = [k for k in w if k not in ids]
    if unknown_w:
        raise ApiError(422, "bad_weight", "Çəki seçilməmiş KPI üçün verilib: %s" % ", ".join(unknown_w))
    t = now_iso()
    if sid:
        apidb.execute(cfg.db, "UPDATE kpiset SET name=?, kpis=?, weights=?, note=?, actor=?, updated=? WHERE id=?",
                      (name[:200], json.dumps(ids), json.dumps(w), str(body.get("note", cur.get("note")) or "")[:2000], actor, t, sid))
    else:
        sid = new_id("KS")
        apidb.execute(cfg.db, "INSERT INTO kpiset(id,name,kpis,weights,note,actor,created,updated) VALUES(?,?,?,?,?,?,?,?)",
                      (sid, name[:200], json.dumps(ids), json.dumps(w), str(body.get("note") or "")[:2000], actor, t, t))
        apidb.event(cfg.db, "kpiset.saved", "KPI dəsti saxlanıldı: %s" % name[:80], {"id": sid})
    return get_set(cfg, sid)


def delete_set(cfg, sid):
    get_set(cfg, sid)
    apidb.execute(cfg.db, "DELETE FROM kpiset WHERE id=?", (sid,))
    return {"deleted": sid}


# ------------------------------------------------------------------ compute helpers
def frame_of(result):
    import pandas as pd
    f = pd.DataFrame(result.get("effects") or [])
    cols = pu.P("integrate").P1_COLS
    for c in cols:
        if c not in f.columns:
            f[c] = None
    return f[cols]


def ext_of(result):
    return {(x["scenario"], x["kpi"]): x["value"] for x in ((result.get("side_effects") or {}).get("kpi_inputs") or [])}


def compute(p1, ids, weights, ext):
    """policyunit.kpi.compute; FR4 KPI inputs of the API runs override the pipeline's P*_kpi_inputs.csv."""
    K = pu.P("kpi")
    return K.compute(p1, ids, weights, ext={**K.external(None), **ext})
