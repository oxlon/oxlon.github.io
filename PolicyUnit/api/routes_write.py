"""
routes_write — POST/PUT/DELETE marşrutları («write» nişanı): ssenarilər (NFR4), hesablama, müqayisə, KPI dəstləri,
yeni alət, yeniləmə, Excel hesabatı.
"""
import time

import compare_views, kpi_views, pu, results
from apicore import ApiError
from runs import norm_request


def _q(qs, k, default=None):
    v = qs.get(k)
    v = v[0] if isinstance(v, list) and v else v
    return default if v in (None, "") else v


def _qb(qs, k):
    return str(_q(qs, k, "")).lower() in ("1", "true", "yes", "bəli")


def route(h, app, method, parts, qs):
    p = "/".join(parts)
    actor = (h.headers.get("X-Actor") or "api")[:80]
    S = app.store
    if method == "POST":
        if p == "scenarios":
            return h.send_json(201, S.create(h.json_body(), actor, store=_q(qs, "store", "draft"), overwrite=_qb(qs, "overwrite")))
        if p == "scenarios/validate":
            return h.send_json(200, S.validate(h.json_body()))
        if p == "scenarios/import":
            return h.send_json(200, S.import_(h.json_body(), actor, store=_q(qs, "store", "draft"), overwrite=_qb(qs, "overwrite")))
        if parts[:1] == ["scenarios"] and len(parts) == 3:
            sid, act = parts[1], parts[2]
            if act == "duplicate":
                return h.send_json(201, S.duplicate(sid, h.json_body(optional=True), actor))
            if act == "promote":
                h.drain()
                return h.send_json(200, S.promote(sid, actor))
            if act == "run":
                body = h.json_body(optional=True) or {}
                s, src = S.load(sid)
                return run(h, app, s, src, body, actor)
        if parts[:1] == ["scenarios"] and len(parts) == 2:              # POST as PUT (clients without PUT)
            return h.send_json(200, S.update(parts[1], h.json_body(), actor))
        if p == "runs":
            body = h.json_body()
            if not isinstance(body, dict) or not isinstance(body.get("scenario"), dict):
                raise ApiError(400, "bad_json", "Gövdə {scenario: {...}, ...} formatında olmalıdır")
            s = S._require_valid(body["scenario"])["normalised"]
            return run(h, app, s, "adhoc", body, actor)
        if parts[:1] == ["runs"] and len(parts) == 3 and parts[2] == "cancel":
            h.drain()
            return h.send_json(200, app.runs.cancel(parts[1]))
        if p == "compare":
            return h.send_json(200, compare_views.compare(app, h.json_body(), actor))
        if p == "kpi/sets":
            return h.send_json(201, kpi_views.save_set(app.cfg, h.json_body(), actor))
        if p == "instruments/validate":
            b = h.json_body()
            return h.send_json(200, app.instruments.check(b, test_run=(b or {}).get("test_run", True)))
        if p == "instruments/new":
            r = app.instruments.add(h.json_body(), actor)
            return h.send_json(200 if r.get("dry_run") else 201, r)
        if p == "refresh":
            b = h.json_body(optional=True) or {}
            return h.send_json(202, app.refresh.start(b, actor=actor, trigger="api", note=b.get("note")))
        if parts[:1] == ["refresh"] and len(parts) == 3 and parts[2] == "cancel":
            h.drain()
            return h.send_json(200, app.refresh.cancel(parts[1]))
        if p == "reports/xlsx":
            return export_xlsx(h, app, h.json_body(optional=True) or {})
    if method == "PUT":
        if parts[:1] == ["scenarios"] and len(parts) == 2:
            return h.send_json(200, S.update(parts[1], h.json_body(), actor))
        if parts[:2] == ["kpi", "sets"] and len(parts) == 3:
            return h.send_json(200, kpi_views.save_set(app.cfg, h.json_body(), actor, sid=parts[2]))
    if method == "DELETE":
        h.drain()
        if parts[:1] == ["scenarios"] and len(parts) == 2:
            return h.send_json(200, S.delete(parts[1], force=_qb(qs, "force")))
        if parts[:2] == ["kpi", "sets"] and len(parts) == 3:
            return h.send_json(200, kpi_views.delete_set(app.cfg, parts[2]))
        if parts[:1] == ["instruments"] and len(parts) == 2:
            return h.send_json(200, app.instruments.delete(parts[1], S, actor))
    raise ApiError(405 if method in ("POST", "PUT", "DELETE") else 404, "method_not_allowed",
                   "Belə API yolu yoxdur: %s /api/v1/%s" % (method, p))


def run(h, app, s, src, body, actor):
    if not isinstance(body, dict):
        raise ApiError(400, "bad_json", "JSON obyekt gözlənilir")
    req = norm_request(body)
    if req["kpis"] or body.get("kpi_set") or req["weights"]:
        req["kpis"], req["weights"], _ = kpi_views.resolve(app.cfg, body)
    rid, cached = app.runs.submit(s, src, req, actor)
    if not cached:
        app.runs.wait(rid, req["wait"])
    r = app.runs.get(rid, detail=req["detail"])
    if r["status"] == "ok":
        res = r["result"]
        res["cached"] = cached
        if cached and (req["kpis"] or req["weights"]) and res.get("effects"):
            res["kpi"] = results.kpi_block(kpi_views.frame_of(res), req["kpis"], req["weights"], kpi_views.ext_of(res))
        elif cached and (req["kpis"] or req["weights"]):
            full = app.runs.result(rid)
            res["kpi"] = results.kpi_block(kpi_views.frame_of(full), req["kpis"], req["weights"], kpi_views.ext_of(full))
        return h.send_json(200, res)
    if r["status"] == "running":
        return h.send_json(202, {"run_id": rid, "status": "running", "status_az": r["status_az"], "progress": r["progress"],
                                 "poll": "/api/v1/runs/%s" % rid})
    err = r.get("error") or {}
    raise ApiError(422, "run_failed", err.get("message") or "Hesablama alınmadı", detail=err.get("detail"),
                   extra={"run_id": rid, "status": r["status"]})


def export_xlsx(h, app, b):
    import report_xlsx
    run_res = app.runs.result(b["run_id"]) if b.get("run_id") else None
    meta = {"vintage_id": pu.vintage(app.cfg)["vintage_id"]}
    with pu.ENGINE_LOCK:
        body = report_xlsx.build(app.views, app.cfg.root, b.get("files"), run_res, b.get("compare"), b.get("title"), meta)
    fn = "siyaset_ixrac_%s.xlsx" % time.strftime("%Y%m%d-%H%M%S")
    if b.get("save"):
        app.cfg.reports.mkdir(parents=True, exist_ok=True)
        (app.cfg.reports / fn).write_bytes(body)
    return h.send_bytes(200, body, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        {"Content-Disposition": 'attachment; filename="%s"' % fn})
