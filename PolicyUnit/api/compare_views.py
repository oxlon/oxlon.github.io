"""
compare_views — POST /compare: bir neçə ssenari yanaşı (cari vintajın son nəticəsi; yoxdursa hesablanır),
istifadəçinin seçdiyi ≥ 5 KPI və çəkilər → dəyərlər, normallaşdırılmış bal, reytinq, əsas göstəricilər matrisi, izah.
"""
import math
import time

import kpi_views, pu
from apicore import ApiError
from fr4_bridge import _records
from results import num
from runs import norm_request


def compare(app, body, actor="api"):
    if not isinstance(body, dict):
        raise ApiError(400, "bad_json", "JSON obyekt gözlənilir")
    ids = list(dict.fromkeys(body.get("scenarios") or []))
    if len(ids) < 2:
        raise ApiError(422, "too_few", "Müqayisə üçün ən azı 2 fərqli ssenari seçin")
    if len(ids) > 20:
        raise ApiError(422, "too_many", "Bir müqayisədə ən çoxu 20 ssenari")
    kids, weights, ksrc = kpi_views.resolve(app.cfg, body)
    t0 = time.perf_counter()
    vid = pu.vintage(app.cfg)["vintage_id"]
    mode = body.get("side_effects", "rules")
    req = norm_request({"side_effects": mode if mode in ("full", "rules", "none") else "rules",
                        "risk": mode == "full", "wait": body.get("wait", 120)})
    runs, pending, scen = {}, [], {}
    for sid in ids:
        s, src = app.store.load(sid)
        scen[sid] = s
        rid = None if body.get("force") else app.runs.latest_ok(s, vid)
        if rid is None:
            rid, _ = app.runs.submit(s, src, req, actor)
            pending.append(rid)
        runs[sid] = rid
    deadline = time.time() + req["wait"]
    for rid in pending:
        app.runs.wait(rid, max(0.1, deadline - time.time()))
    out_runs, results = [], {}
    for sid, rid in runs.items():
        r = app.runs.get(rid, with_result=False)
        if r["status"] != "ok":
            if r["status"] == "running":
                raise ApiError(409, "still_running", "Ssenari hələ hesablanır: %s (run %s) — bir azdan təkrarlayın" % (sid, rid),
                               extra={"runs": runs})
            raise ApiError(422, "run_failed", "Ssenari hesablanmadı: %s — %s" % (sid, (r.get("error") or {}).get("message")),
                           extra={"runs": runs})
        results[sid] = app.runs.result(rid)
        out_runs.append({"scenario": sid, "name_az": scen[sid]["name_az"], "run_id": rid, "vintage_id": r["vintage_id"],
                         "computed_now": rid in pending})
    import pandas as pd
    p1 = pd.concat([kpi_views.frame_of(results[s]) for s in ids], ignore_index=True)
    ext = {}
    for s in ids:
        ext.update(kpi_views.ext_of(results[s]))
    try:
        vals, rank = kpi_views.compute(p1, kids, weights, ext)
    except Exception as e:
        raise ApiError(422, "kpi_error", "KPI hesablanmadı: %s" % e)
    sel = kpi_views.check(kids, weights)
    matrix = []
    for k in sel.index:
        row = {"kpi": k, "name_az": sel.loc[k, "name_az"], "unit": sel.loc[k, "unit"], "direction": sel.loc[k, "direction"],
               "weight": float(sel.loc[k, "default_weight"])}
        g = vals[vals.kpi == k]
        for r in g.itertuples():
            row[r.scenario] = None if not math.isfinite(float(r.value)) else round(float(r.value), 4)
            row[r.scenario + "__norm"] = None if not math.isfinite(float(r.norm)) else round(float(r.norm), 4)
        matrix.append(row)
    head = {}
    for s in ids:
        for r in results[s].get("headline_wide", []):
            d = head.setdefault(r["indicator"], {"indicator": r["indicator"], "label_az": r["label_az"],
                                                 "effect_unit": r["effect_unit"]})
            for hz in ("qısa", "orta", "uzun"):
                d["%s|%s" % (s, hz)] = r.get(hz)
    se = {s: [x for x in ((results[s].get("side_effects") or {}).get("items") or []) if x.get("variant") == "base"] for s in ids}
    side = [{"scenario": s, "n": len(v), "max_severity": max([x["severity"] for x in v], default=0),
             "top_az": max(v, key=lambda x: x["severity"])["name_az"] if v else None} for s, v in se.items()]
    rk = _records(rank)
    txt = "Reytinq (%d KPI, %s): " % (len(sel), ksrc) + "; ".join(
        "%d. %s — bal %s" % (r["rank"], r["scenario_name"], num(r["score"], 3).lstrip("+")) for r in rk) + "."
    miss = sorted({m for r in rk for m in str(r.get("kpis_missing") or "").split(";") if m})
    if miss:
        txt += " Bəzi ssenarilər üçün hesablanmayan KPI-lar (balda nəzərə alınmayıb): %s." % ", ".join(miss)
    return {"scenarios": out_runs, "kpis": _records(sel), "kpi_source": ksrc, "values": _records(vals), "matrix": matrix,
            "ranking": rk, "headline": list(head.values()), "side_effects": side, "text_az": txt,
            "seconds": round(time.perf_counter() - t0, 2), "vintage_id": vid}
