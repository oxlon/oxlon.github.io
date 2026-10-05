"""
routes — /api/v1/ endpoint-ləri. Handler (server.py) sorğunu bura ötürür: route(h, method, parts, query).
"""
import json, re, threading
from urllib.parse import quote, unquote

import apidb
import multipart_form
import report_xlsx
import scenario_engine as SE
import status_view
from apicore import API_DIR, ApiError, DB_LOCK, MODULES, SCENARIOS, module_name, now_iso
from upload_store import KINDS, classify


def _hdr(h, name):
    """Başlıq dəyəri: faiz kodlaması (%C6%8F) və ya xam UTF-8 baytları (latin-1 kimi oxunmuş) düzəldilir."""
    v = h.headers.get(name)
    if v is None:
        return None
    if v.lower().startswith("utf-8''"):
        v = v[7:]
    if "%" in v:
        v = unquote(v)
    try:
        v = v.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return v.strip()


def _flag(q, k):
    return str(q.get(k, [""])[0]).lower() in ("1", "true", "yes", "bəli")


def _list(q, k):
    vals = []
    for v in q.get(k, []):
        vals += [x.strip() for x in v.split(",") if x.strip()]
    return vals


def _int(q, k, d=None):
    v = q.get(k, [None])[0]
    if v in (None, ""):
        return d
    try:
        return int(v)
    except ValueError:
        raise ApiError(400, "bad_parameter", "«%s» tam ədəd olmalıdır: %r" % (k, v))


def route(h, method, p, q):
    app = h.server.app
    one = lambda k, d=None: q.get(k, [d])[0]
    if p == ["health"] and method == "GET":
        return h.send_json(200, {"status": "ok", "version": app.version, "time": now_iso(), "service": "MikroModel API"})
    if p == ["openapi.yaml"] and method == "GET":
        body = (API_DIR / "openapi.yaml").read_bytes()
        return h.send_bytes(200, body, "application/yaml; charset=utf-8")
    actor = h.auth("read" if method in ("GET", "HEAD") else "write")

    # ---------------------------------------------------------------- status
    if p == ["status"] and method == "GET":
        st = status_view.status(app.cfg, app.runs, app.uploads, app.engine, app.started_at)
        st["autonomous"] = app.autonomous_state()
        return h.send_json(200, st)
    if p == ["events"] and method == "GET":
        return h.send_json(200, {"items": apidb.events(app.cfg.db, max(1, min(1000, _int(q, "limit", 100))))})

    # ---------------------------------------------------------------- uploads
    if p == ["uploads"] and method == "GET":
        return h.send_json(200, {"items": app.uploads.list(max(1, min(1000, _int(q, "limit", 100))), one("kind"), one("status"))})
    if p == ["uploads"] and method == "POST":
        up = receive_upload(h, app, q, actor)
        out, code = {"upload": up, "validation": up.get("report")}, 201 if up["valid"] else 422
        if not up["valid"]:
            out["error"] = {"code": "validation_failed", "message": "Fayl yoxlamadan keçmədi — səhvlər «validation.errors» siyahısındadır"}
        elif _flag(q, "apply"):
            out.update(apply_upload(app, up["id"], actor, _flag(q, "run")))
        return h.send_json(code, out)
    if len(p) == 2 and p[0] == "uploads" and method == "GET":
        up = app.uploads.get(p[1])
        if not up:
            raise ApiError(404, "not_found", "Yükləmə tapılmadı: %s" % p[1])
        return h.send_json(200, up)
    if len(p) == 3 and p[0] == "uploads" and p[2] == "apply" and method == "POST":
        h.drain()
        return h.send_json(200, apply_upload(app, p[1], actor, _flag(q, "run")))

    # ---------------------------------------------------------------- runs
    if p == ["runs"] and method == "GET":
        return h.send_json(200, {"items": app.runs.list(max(1, min(500, _int(q, "limit", 50)))), "running": app.runs.busy(),
                                 "pending": app.runs.pending})
    if p == ["runs"] and method == "POST":
        b = h.json_body(optional=True) or {}
        if not isinstance(b, dict):
            raise ApiError(400, "bad_request", "JSON obyekt gözlənilir: {\"stage\": \"FR4\"} və ya {\"only\": \"FR5\"}")
        r = app.runs.start(stage=b.get("stage"), only=b.get("only"), stages=b.get("stages"), skip_build=bool(b.get("skip_build")),
                           dry_run=bool(b.get("dry_run")), snapshot=b.get("snapshot"), actor=b.get("actor") or actor, trigger="api")
        return h.send_json(202, r)
    if len(p) == 2 and p[0] == "runs" and method == "GET":
        r = app.runs.get(p[1], log_lines=max(5, min(2000, _int(q, "lines", 40))))
        if not r:
            raise ApiError(404, "not_found", "İcra tapılmadı: %s" % p[1])
        return h.send_json(200, r)
    if len(p) == 3 and p[0] == "runs" and p[2] == "cancel" and method == "POST":
        h.drain()
        return h.send_json(202, app.runs.cancel(p[1]))

    # ---------------------------------------------------------------- data
    if p == ["catalog"] and method == "GET":
        return h.send_json(200, app.views.catalog_view(module_name(one("module"), required=False), one("q")))
    if p == ["forecasts"] and method == "GET":
        scen = _list(q, "scenario")
        bad = [s for s in scen if s not in SCENARIOS + ["Actual"]]
        if bad:
            raise ApiError(400, "bad_parameter", "Naməlum ssenari: %s (mümkün: %s, Actual)" % (", ".join(bad), ", ".join(SCENARIOS)))
        return h.send_json(200, app.views.forecasts(module_name(one("module"), required=False), _list(q, "id") or None, scen or None,
                                                    _int(q, "from"), _int(q, "to"), max(1, min(500000, _int(q, "limit", 200000)))))
    if p == ["equations"] and method == "GET":
        return h.send_json(200, app.views.equations(module_name(one("module"), required=False), one("id"), _flag(q, "full")))
    if p == ["observations"] and method == "GET":
        return h.send_json(200, observations(app, q))
    if p == ["history"] and method == "GET":
        where, args = [], []
        for k in ("module", "code"):
            if one(k):
                where.append(k + "=?")
                args.append(one(k).upper() if k == "module" else one(k))
        sql = "SELECT * FROM observation_history" + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY id DESC LIMIT ?"
        rows = [dict(r) for r in apidb.conn(app.cfg.db).execute(sql, args + [max(1, min(5000, _int(q, "limit", 500)))])]
        return h.send_json(200, {"items": rows})

    # ---------------------------------------------------------------- scenarios
    if p == ["scenarios", "inputs"] and method == "GET":
        return h.send_json(200, app.engine.inputs(one("module")))
    if p == ["scenarios", "run"] and method == "POST":
        b = h.json_body()
        if not isinstance(b, dict):
            raise ApiError(400, "bad_request", "JSON obyekt gözlənilir: {\"overrides\": {...}, \"scenario\": \"Baseline\"}")
        res = app.engine.run(b.get("overrides"), b.get("scenario") or "Baseline", b.get("modules"))
        if b.get("name") and b.get("save", True):
            sv, _ = SE.saved_put(app.cfg.db, {"name": b["name"], "scenario": res["scenario"], "overrides": res["overrides"],
                                              "result": res["result"], "note": b.get("note"), "author": b.get("author")}, actor)
            res["saved"] = {k: sv[k] for k in ("id", "name", "author", "created_at")}
        return h.send_json(200, res)
    if p == ["scenarios", "saved"] and method == "GET":
        return h.send_json(200, {"items": SE.saved_list(app.cfg.db, one("author"))})
    if p == ["scenarios", "saved"] and method == "POST":
        sv, created = SE.saved_put(app.cfg.db, h.json_body(), actor)
        return h.send_json(201 if created else 200, sv)
    if len(p) == 3 and p[:2] == ["scenarios", "saved"] and method == "GET":
        return h.send_json(200, SE.saved_get(app.cfg.db, p[2]))
    if len(p) == 3 and p[:2] == ["scenarios", "saved"] and method == "DELETE":
        return h.send_json(200, SE.saved_delete(app.cfg.db, p[2]))

    # ---------------------------------------------------------------- reports
    if p == ["reports"] and method == "POST":
        spec = h.json_body()
        vin = status_view.vintage(app.cfg)
        last = app.runs.last()
        meta = {"İş kitabı": vin["workbook"].get("file"), "İş kitabının son ili": vin["workbook"].get("last_annual_year"),
                "Son icra": (last or {}).get("id")}
        body, name = report_xlsx.build(spec, app.views, lambda sid: SE.saved_get(app.cfg.db, sid), meta)
        return h.send_bytes(200, body, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            {"Content-Disposition": "attachment; filename=\"%s\"; filename*=UTF-8''%s" % (name, quote(name))})

    # ---------------------------------------------------------------- DSK refresh / autonomous
    if p == ["dsk", "refresh"] and method == "GET":
        return h.send_json(200, app.dsk_state)
    if p == ["dsk", "refresh"] and method == "POST":
        h.drain()
        return h.send_json(202, app.start_dsk_refresh(actor, run=_flag(q, "run")))
    if p == ["autonomous"] and method == "GET":
        return h.send_json(200, app.autonomous_state())

    raise ApiError(404, "not_found", "Belə bir endpoint yoxdur: %s /api/v1/%s" % (method, "/".join(p)))


def receive_upload(h, app, q, actor):
    """Xam gövdə (X-Filename, X-Kind, X-Subfolder başlıqları) və ya multipart/form-data (file, kind, subfolder)."""
    n = h.content_length()
    if n <= 0:
        raise ApiError(400, "empty_body", "Boş sorğu gövdəsi — fayl göndərilməyib")
    if n > app.cfg.max_upload_mb * 1024 * 1024:
        raise ApiError(413, "too_large", "Fayl çox böyükdür (maks. %d MB)" % app.cfg.max_upload_mb)
    ctype = h.headers.get("Content-Type", "")
    kind, sub = _hdr(h, "X-Kind") or q.get("kind", [None])[0], _hdr(h, "X-Subfolder") or q.get("subfolder", [None])[0]
    note, who = _hdr(h, "X-Note") or q.get("note", [None])[0], _hdr(h, "X-Actor") or actor
    if ctype.lower().startswith("multipart/form-data"):
        body = h.read_body(n)
        try:
            parts = multipart_form.parse(body, ctype)
        except multipart_form.MultipartError as e:
            raise ApiError(400, "bad_multipart", "multipart/form-data oxunmadı: %s" % e)
        f = parts.get("file") or next((x for x in parts.values() if x.filename), None)
        if f is None:
            raise ApiError(400, "no_file", "multipart gövdəsində fayl hissəsi («file») yoxdur")
        txt = lambda k: parts[k].text.strip() if k in parts and parts[k].filename is None else None
        kind, sub = txt("kind") or kind, txt("subfolder") or sub
        note, who = txt("note") or note, txt("actor") or who
        filename, data, stream = (f.filename or txt("filename") or ""), f.data, None
    else:
        filename, data, stream = _hdr(h, "X-Filename") or q.get("filename", [None])[0], None, h.rfile
        if not filename:
            raise ApiError(400, "no_filename", "X-Filename başlığı (və ya ?filename=) tələb olunur")
    if not kind:
        kind, why = classify(filename.replace("\\", "/").split("/")[-1])
        if not kind:
            raise ApiError(400, "no_kind", "Növ göstərilməyib (X-Kind / kind): %s. Mümkün olanlar: %s" % (why, ", ".join(KINDS)))
    kind = kind.strip().lower()
    if kind not in KINDS:
        if stream is not None:
            h.drain()
        raise ApiError(400, "bad_kind", "Naməlum yükləmə növü: %r. Mümkün olanlar: %s" % (kind, ", ".join(KINDS)))
    try:
        up = app.uploads.create(kind, filename, data=data, stream=stream, length=n if stream is not None else None,
                                subfolder=sub, actor=who, note=note, source="api")
    finally:
        h.body_consumed = True
    return up


def apply_upload(app, uid, actor, run=False):
    up = app.uploads.apply(uid, actor)
    out = {"upload": {k: v for k, v in up.items() if k != "report"}, "apply": up["apply"], "run": None}
    stages = up["apply"].get("affected_stages") or []
    if run and stages:
        r = app.runs.queue(stages, actor=actor, trigger="upload:%s" % uid)
        out["run"] = r
        if r and r.get("id"):
            app.uploads.set_run(uid, r["id"])
    elif run:
        out["run_note"] = "Bu növ məlumat dəftərlərin girişinə təsir etmir — icra başladılmadı"
    return out


def observations(app, q):
    one = lambda k, d=None: q.get(k, [d])[0]
    where, args = [], []
    if one("module"):
        where.append("module=?")
        args.append(module_name(one("module")))
    codes = _list(q, "code")
    if codes:
        where.append("code IN (%s)" % ",".join("?" * len(codes)))
        args += codes
    for k, op in (("from", ">="), ("to", "<=")):
        if one(k):
            where.append("period%s?" % op)
            args.append(_int(q, k))
    if one("since_seq"):
        where.append("seq>?")
        args.append(_int(q, "since_seq"))
    lim, off = max(1, min(50000, _int(q, "limit", 10000))), max(0, _int(q, "offset", 0))
    w = (" WHERE " + " AND ".join(where)) if where else ""
    con = apidb.conn(app.cfg.db)
    rows = [dict(r) for r in con.execute("SELECT * FROM observation" + w + " ORDER BY seq LIMIT ? OFFSET ?", args + [lim, off])]
    tot = con.execute("SELECT COUNT(*) n FROM observation" + w, args).fetchone()["n"]
    mx = con.execute("SELECT IFNULL(MAX(seq),0) s FROM observation").fetchone()["s"]
    return {"items": rows, "total": tot, "limit": lim, "offset": off, "max_seq": mx}
