"""
routes — /api/v1/... marşrutları (oxuma). GET → «read» nişanı, POST/PUT/DELETE → «write» (routes_write.py);
health və openapi.yaml açıqdır.
"""
import os, time

import apidb, kpi_views, pu, routes_write
from apicore import API_DIR, API_VERSION, ApiError, now_iso


def q1(qs, k, default=None):
    v = qs.get(k)
    v = v[0] if isinstance(v, list) and v else v
    return default if v in (None, "") else v


def qbool(qs, k):
    return str(q1(qs, k, "")).lower() in ("1", "true", "yes", "bəli")


def route(h, method, parts, qs):
    app = h.server.app
    p = "/".join(parts)
    if method == "HEAD":
        method = "GET"
    if p == "health" and method == "GET":
        return h.send_json(200, {"status": "ok", "version": API_VERSION, "time": now_iso(), "root": str(app.cfg.root),
                                 "no_network": os.environ.get("POLICY_NO_NETWORK") == "1", "started": app.started_at})
    if p == "openapi.yaml" and method == "GET":
        return h.send_bytes(200, (API_DIR / "openapi.yaml").read_bytes(), "application/yaml; charset=utf-8")
    h.auth("read" if method == "GET" else "write")
    if method != "GET":
        return routes_write.route(h, app, method, parts, qs)
    V = app.views
    if p == "status":
        return h.send_json(200, app.status())
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
    # ---------------------------------------------------------------- instruments
    if p == "instruments":
        return h.send_json(200, app.instruments.list(q1(qs, "family")))
    if p == "instruments/schema":
        return h.send_json(200, app.instruments.schema())
    if parts[:1] == ["instruments"] and len(parts) == 2:
        return h.send_json(200, app.instruments.get(parts[1], app.store))
    # ---------------------------------------------------------------- scenarios
    if p == "scenarios":
        rows = app.store.list(q1(qs, "source", "all"), q1(qs, "tag"), q1(qs, "q"))
        return h.send_json(200, {"scenarios": rows, "n": len(rows)})
    if p == "scenarios/schema":
        return h.send_json(200, scenario_schema(app))
    if parts[:1] == ["scenarios"] and len(parts) == 2:
        return h.send_json(200, app.store.get(parts[1]))
    if parts[:1] == ["scenarios"] and len(parts) == 3 and parts[2] == "export":
        return h.send_bytes(200, app.store.export(parts[1]), "application/json; charset=utf-8",
                            {"Content-Disposition": 'attachment; filename="%s.json"' % parts[1]})
    # ---------------------------------------------------------------- runs
    if p == "runs":
        return h.send_json(200, {"runs": app.runs.list(q1(qs, "scenario"))})
    if parts[:1] == ["runs"] and len(parts) == 2:
        return h.send_json(200, app.runs.get(parts[1], detail=q1(qs, "detail", "full")))
    # ---------------------------------------------------------------- KPI
    if p == "kpi":
        return h.send_json(200, kpi_views.catalogue())
    if p == "kpi/sets":
        return h.send_json(200, {"sets": kpi_views.list_sets(app.cfg)})
    if parts[:2] == ["kpi", "sets"] and len(parts) == 3:
        return h.send_json(200, kpi_views.get_set(app.cfg, parts[2]))
    # ---------------------------------------------------------------- refresh / autonomous / reports
    if p == "refresh":
        return h.send_json(200, {"active": app.refresh.active(), "busy": app.refresh.busy(), "jobs": app.refresh.list()})
    if parts[:1] == ["refresh"] and len(parts) == 2:
        j = app.refresh.get(parts[1], tail=int(q1(qs, "tail", 200)))
        if not j:
            raise ApiError(404, "not_found", "Yeniləmə işi tapılmadı: %s" % parts[1])
        return h.send_json(200, j)
    if p == "autonomous":
        return h.send_json(200, app.autonomous_state())
    if p == "reports":
        d = app.cfg.reports
        fs = sorted(x for x in d.glob("*") if x.is_file() and not x.name.startswith(".")) if d.is_dir() else []
        return h.send_json(200, {"reports": [{"file": x.name, "bytes": x.stat().st_size,
                                              "mtime": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(x.stat().st_mtime)),
                                              "url": "/api/v1/reports/" + x.name} for x in fs]})
    if parts[:1] == ["reports"] and len(parts) == 2 and parts[1] != "xlsx":
        return send_report(h, app, parts[1])
    raise ApiError(404, "not_found", "Belə API yolu yoxdur: GET /api/v1/%s" % p)


def scenario_schema(app):
    import scenarios
    c = pu.P("config")
    io_sec = []
    try:
        import csv
        with open(c.IO_SECTORS_CSV, encoding="utf-8") as f:
            io_sec = [{"code": r["code"], "name_az": r.get("name_az", "")} for r in csv.DictReader(f)]
    except OSError:
        pass
    ex = {"id": "yeni_ssenari", "name_az": "Minimum əmək haqqı +10 % (2027-dən)", "description_az": "Nümunə",
          "start_year": 2027, "instruments": [{"instrument": "min_wage", "years": "all", "size": 10, "unit": "pct",
                                               "target": None, "financing": None}], "tags": ["əmək"]}
    return {"fields": [
                {"id": "id", "label_az": "id (kiçik latın hərfləri, rəqəm, _; fayl adı ilə eyni)", "required": True},
                {"id": "name_az", "label_az": "Ad", "required": True},
                {"id": "description_az", "label_az": "Təsvir"},
                {"id": "start_year", "label_az": "Başlanğıc il", "required": True, "min": c.FIRST_YEAR, "max": c.MICRO_YEARS[-1]},
                {"id": "instruments", "label_az": "Alətlər (≥ 1)", "required": True},
                {"id": "tags", "label_az": "Etiketlər"}],
            "instrument_fields": [
                {"id": "instrument", "label_az": "Alət (GET /instruments)", "required": True},
                {"id": "years", "label_az": "İllər: \"all\" (başlanğıc il…%d) və ya siyahı" % c.LONG_END},
                {"id": "size", "label_az": "Ölçü (alətin min/max intervalında)", "required": True},
                {"id": "unit", "label_az": "Vahid (alətin vahidi ilə eyni)"},
                {"id": "target", "label_az": "Hədəf sektor/bazar (lazım olduqda)"},
                {"id": "financing", "label_az": "Maliyyələşmə"}],
            "years": {"first": c.FIRST_YEAR, "last": c.LONG_END, "micro_last": c.MICRO_YEARS[-1]},
            "horizons": pu.HORIZON_AZ,
            "financing": [{"id": k, "label_az": v} for k, v in pu.FINANCING_AZ.items()],
            "targets": {"io_sectors": io_sec, "fr12_markets": list(pu.P("scenario").FR12_MARKETS),
                        "all_codes": sorted(scenarios.target_codes())},
            "example": ex}


def send_report(h, app, name):
    from apicore import safe_relpath, within
    import static_files
    rel = safe_relpath(name)
    f = app.cfg.reports / rel
    if not within(app.cfg.reports, f) or not f.is_file():
        raise ApiError(404, "not_found", "Hesabat tapılmadı: %s" % rel)
    return h.send_bytes(200, f.read_bytes(), static_files.mime_of(str(f)),
                        {"Content-Disposition": 'attachment; filename="%s"' % f.name})
