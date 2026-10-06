"""
routes — /api/v1/... marşrutları. GET → «read» nişanı, POST/PUT/DELETE → «write» nişanı (health, openapi.yaml açıq).
"""
import threading, time

import analysis_scal, analysis_stress, apidb
from analysis_base import RU_KEYS
from apicore import API_DIR, API_VERSION, ApiError, now_iso
from az_errors import az_exc
from data_views import records

ANALYSIS_LOCK = threading.Lock()


def q1(qs, k, default=None):
    v = qs.get(k)
    v = v[0] if isinstance(v, list) and v else v
    return default if v in (None, "") else v


def engine_call(fn, *a, **kw):
    """Serialised call into riskunit/MicroUnit; Python errors → 422 with an Azerbaijani explanation."""
    with ANALYSIS_LOCK:
        try:
            return fn(*a, **kw)
        except ApiError:
            raise
        except Exception as e:
            raise ApiError(422, "engine_error", "Hesablama alınmadı: %s" % az_exc(e), detail="%s: %s" % (type(e).__name__, str(e)[:500]))


def route(h, method, parts, qs):
    app = h.server.app
    p = "/".join(parts)
    if method == "HEAD":
        method = "GET"
    # ---------------------------------------------------------------- open
    if p == "health" and method == "GET":
        import os
        return h.send_json(200, {"status": "ok", "version": API_VERSION, "time": now_iso(), "root": str(app.cfg.root),
                                 "no_network": os.environ.get("RISK_NO_NETWORK") == "1", "started": app.started_at})
    if p == "openapi.yaml" and method == "GET":
        return h.send_bytes(200, (API_DIR / "openapi.yaml").read_bytes(), "application/yaml; charset=utf-8")
    need = "read" if method == "GET" else "write"
    h.auth(need)
    actor = (h.headers.get("X-Actor") or "api")[:80]
    V, R = app.views, app.risks

    if method == "GET":
        if p == "status":
            s = V.status()
            s["refresh"] = app.runs.active()
            s["busy"] = app.runs.busy()
            s["autonomous"] = app.autonomous_state()
            s["analysis_ready"] = app.warm_state
            return h.send_json(200, s)
        if p == "events":
            ev = apidb.events(app.cfg.db, since=int(q1(qs, "since", 0)), limit=min(int(q1(qs, "limit", 100)), 1000))
            return h.send_json(200, {"last": apidb.last_seq(app.cfg.db), "events": ev})
        if p == "catalog":
            return h.send_json(200, V.catalog(q1(qs, "prefix")))
        if parts[:1] == ["outputs"] and len(parts) >= 2:
            name = "/".join(parts[1:])
            if q1(qs, "format") == "csv":
                rel, body = V.output_csv(name, qs)
                return h.send_bytes(200, body, "text/csv; charset=utf-8",
                                    {"Content-Disposition": 'attachment; filename="%s"' % rel.split("/")[-1]})
            return h.send_json(200, V.output(name, qs))
        if p == "risks":
            return h.send_json(200, R.table(qs))
        if parts[:1] == ["risks"] and len(parts) == 2:
            return h.send_json(200, R.bundle(parts[1]))
        if p == "monitor":
            return h.send_json(200, V.monitor(qs))
        if p == "stress/inputs":
            return h.send_json(200, engine_call(stress_inputs, app))
        if p == "scalability/factors":
            st = engine_call(app.base.sc_state)
            return h.send_json(200, {"factors": records(st["S0"]), "score_year": st["hy"], "years": st["years"],
                                     "k_grid": [-3, -2, -1, -0.5, 0.5, 1, 2, 3]})
        if p == "optimize/inputs":
            return h.send_json(200, engine_call(app.opt.inputs))
        if p == "scenarios/saved":
            return h.send_json(200, {"scenarios": app.store.list(q1(qs, "kind"))})
        if parts[:2] == ["scenarios", "saved"] and len(parts) == 3:
            return h.send_json(200, app.store.get(parts[2]))
        if p == "refresh":
            return h.send_json(200, {"active": app.runs.active(), "busy": app.runs.busy(), "jobs": app.runs.list()})
        if parts[:1] == ["refresh"] and len(parts) == 2:
            j = app.runs.get(parts[1], tail=int(q1(qs, "tail", 200)))
            if not j:
                raise ApiError(404, "not_found", "Yeniləmə işi tapılmadı: %s" % parts[1])
            return h.send_json(200, j)
        if p == "autonomous":
            return h.send_json(200, app.autonomous_state())
        if p == "reports":
            fs = sorted(x for x in app.cfg.reports.glob("*") if x.is_file() and not x.name.startswith("."))
            return h.send_json(200, {"reports": [{"file": x.name, "bytes": x.stat().st_size,
                                                  "mtime": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(x.stat().st_mtime)),
                                                  "url": "/api/v1/reports/" + x.name} for x in fs]})
        if parts[:1] == ["reports"] and len(parts) == 2 and parts[1] != "xlsx":
            return send_report(h, app, parts[1])
    if method == "POST":
        if p == "stress/run":
            return h.send_json(200, engine_call(analysis_stress.run, app.base, h.json_body()))
        if p == "scalability/run":
            return h.send_json(200, engine_call(analysis_scal.run, app.base, h.json_body(), app.views))
        if p == "optimize/run":
            return h.send_json(200, engine_call(app.opt.run, h.json_body(optional=True) or {}))
        if p == "scenarios/saved":
            return h.send_json(201, app.store.create(h.json_body(), actor, app.baseline_id()))
        if parts[:2] == ["scenarios", "saved"] and len(parts) == 4 and parts[3] == "run":
            sc = app.store.get(parts[2])
            req = dict(sc["request"] or {})
            if sc["kind"] == "stress":
                req.setdefault("name", sc["name"])
            res = run_kind(app, sc["kind"], req)
            h.drain()
            app.store.set_result(sc["id"], res, app.baseline_id())
            return h.send_json(200, res)
        if parts[:2] == ["scenarios", "saved"] and len(parts) == 3:        # POST as PUT (clients without PUT)
            return h.send_json(200, app.store.update(parts[2], h.json_body(), actor))
        if p == "refresh":
            b = h.json_body(optional=True) or {}
            j = app.runs.start(mode=b.get("mode", "daily"), no_fetch=bool(b.get("no_fetch")), actor=actor, trigger="api",
                               note=b.get("note"))
            return h.send_json(202, j)
        if parts[:1] == ["refresh"] and len(parts) == 3 and parts[2] == "cancel":
            h.drain()
            return h.send_json(200, app.runs.cancel(parts[1]))
        if p == "reports/xlsx":
            return export_xlsx(h, app, h.json_body(optional=True) or {})
    if method == "PUT" and parts[:2] == ["scenarios", "saved"] and len(parts) == 3:
        return h.send_json(200, app.store.update(parts[2], h.json_body(), actor))
    if method == "DELETE" and parts[:2] == ["scenarios", "saved"] and len(parts) == 3:
        h.drain()
        return h.send_json(200, app.store.delete(parts[2]))
    raise ApiError(404 if method == "GET" else 405, "not_found" if method == "GET" else "method_not_allowed",
                   "Belə API yolu yoxdur: %s /api/v1/%s" % (method, p))


def run_kind(app, kind, req):
    if kind == "stress":
        return engine_call(analysis_stress.run, app.base, req)
    if kind == "scalability":
        return engine_call(analysis_scal.run, app.base, req, app.views)
    if kind == "optimize":
        return engine_call(app.opt.run, req)
    raise ApiError(400, "bad_parameter", "Naməlum ssenari növü: %s" % kind)


def stress_inputs(app):
    st = app.base.sc_state()
    ST = app.views.frame("FR3_stress_scenarios.csv", required=False)
    standing = records(ST[["ssenari", "ad", "sok_vektoru"]].drop_duplicates("ssenari")) if ST is not None else []
    return {"factors": records(st["S0"]), "ru_keys": RU_KEYS, "years": st["years"], "score_year": st["hy"],
            "brent_centre": st["centre"], "standing_scenarios": standing,
            "example": {"name": "Neft −2σ + devalvasiya", "shocks": [{"factor": "brent", "k_sigma": -2}, {"factor": "fx", "size": 25}]}}


def send_report(h, app, name):
    from apicore import safe_relpath, within
    rel = safe_relpath(name)
    f = app.cfg.reports / rel
    if not within(app.cfg.reports, f) or not f.is_file():
        raise ApiError(404, "not_found", "Hesabat tapılmadı: %s" % rel)
    import static_files
    return h.send_bytes(200, f.read_bytes(), static_files.mime_of(str(f)),
                        {"Content-Disposition": 'attachment; filename="%s"' % f.name})


def export_xlsx(h, app, b):
    import report_xlsx
    result = b.get("result")
    if b.get("scenario_id"):
        sc = app.store.get(b["scenario_id"])
        result = sc.get("result") or {}
    meta = {"baseline_id": app.baseline_id()}
    body = engine_call(report_xlsx.build, app.views, b.get("files"), result, b.get("title"), meta)
    fn = "risk_ixrac_%s.xlsx" % time.strftime("%Y%m%d-%H%M%S")
    return h.send_bytes(200, body, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        {"Content-Disposition": 'attachment; filename="%s"' % fn})
