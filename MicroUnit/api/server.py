#!/usr/bin/env python3
"""
MİİS §15.5.2 — Mikroiqtisadi modulun məlumat API-si və avtonom icra serveri (istinad tətbiqi).

Yalnız Python standart kitabxanası (yükləmələrin yoxlanılması dəftərlərin istifadə etdiyi openpyxl / xlrd /
pandas-dan istifadə edir). Vəziyyət SQLite faylında saxlanılır. Müqavilə `openapi.yaml` faylındadır.

    python3 api/server.py                                  # http://127.0.0.1:8790/panel/
    python3 api/server.py --watch data/inbox_drop --auto-run --schedule 06:30 --dsk-refresh

Nişanlar (tokens): API_TOKENS mühit dəyişəni, "oxu_nişanı:read,yaz_nişanı:write" formatında.
Standart (yalnız sınaq üçün): read=demo-read, write=demo-write — GET üçün read, POST/DELETE üçün write.
"""
import argparse, json, os, re, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import apidb, routes, static_files                                    # noqa: E402
from apicore import API_VERSION, ApiError, Config, DEFAULT_ROOT, dumps, load_tokens, now_iso, using_default_tokens  # noqa: E402
from data_views import Views                                           # noqa: E402
from run_manager import RunManager                                     # noqa: E402
from scenario_engine import Engine                                     # noqa: E402
from upload_store import UploadStore                                   # noqa: E402
from az_errors import az_exc

LOCAL_ORIGIN = re.compile(r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$")


class App:
    def __init__(self, cfg, tokens, log=print):
        apidb.init(cfg.db)
        self.cfg, self.tokens, self.log, self.version = cfg, tokens, log, API_VERSION
        self.runs = RunManager(cfg)
        self.views = Views(cfg)
        self.uploads = UploadStore(cfg, runs=self.runs, catalog=self.views.catalog_ids)
        self.engine = Engine(cfg)
        self.started_at = now_iso()
        self.watcher = self.scheduler = None
        self.auto_run = False
        self.dsk_state = {"running": False, "last": None}

    def autonomous_state(self):
        w, s = self.watcher, self.scheduler
        return {"watch": {"folder": str(w.folder), "poll_s": w.poll, "auto_run": w.auto_run, "last_scan": w.last_scan,
                          "recent": w.processed[:20]} if w else None,
                "schedule": {"at": s.schedule, "dsk_refresh": s.dsk, "next": s.next.isoformat(timespec="minutes") if s.next else None,
                             "last": s.last} if s else None,
                "dsk_refresh": self.dsk_state}

    def start_dsk_refresh(self, actor, run=False):
        import autonomous
        if self.dsk_state["running"]:
            raise ApiError(409, "busy", "DSK yeniləməsi artıq gedir")
        if self.runs.busy():
            raise ApiError(409, "busy", "Hazırda model icra olunur — DSK faylları icra bitdikdən sonra yenilənə bilər")
        self.dsk_state = {"running": True, "started": now_iso(), "actor": actor, "last": self.dsk_state.get("last")}

        def job():
            try:
                rep = autonomous.dsk_refresh(self.cfg, log=self.log)
                if rep["affected_stages"] and (run or self.auto_run):
                    rep["run"] = self.runs.queue(rep["affected_stages"], actor=actor, trigger="dsk-refresh")
                self.dsk_state = {"running": False, "last": rep}
            except Exception as e:
                self.dsk_state = {"running": False, "last": {"error": az_exc(e), "detail": str(e)[:300], "at": now_iso()}}
        threading.Thread(target=job, daemon=True, name="dsk-refresh").start()
        return self.dsk_state


class Handler(BaseHTTPRequestHandler):
    server_version = "MikroModel-API/" + API_VERSION
    protocol_version = "HTTP/1.1"

    # ---- plumbing
    def log_message(self, fmt, *args):
        if not getattr(self.server, "quiet", False):
            sys.stderr.write("%s  %s\n" % (self.log_date_time_string(), fmt % args))

    def _cors(self):
        origin = self.headers.get("Origin")
        allowed = os.environ.get("API_ORIGINS", "localhost")
        ok = origin and (allowed == "*" or origin == "null" or (allowed == "localhost" and LOCAL_ORIGIN.match(origin))
                         or origin in [x.strip() for x in allowed.split(",")])
        if ok:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Headers",
                             "Authorization, Content-Type, X-Filename, X-Kind, X-Subfolder, X-Actor, X-Note")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
            self.send_header("Access-Control-Expose-Headers", "Content-Disposition")
            self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")

    def _finish_body(self):
        """Oxunmamış gövdə bağlantını pozmasın deyə: kiçikdirsə oxunur, böyükdürsə bağlantı bağlanır."""
        if getattr(self, "body_consumed", True):
            return
        n = self.content_length()
        if 0 < n <= 1024 * 1024:
            self.rfile.read(n)
        elif n > 0:
            self.close_connection = True
            self.send_header("Connection", "close")
        self.body_consumed = True

    def send_bytes(self, status, body, ctype, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self._cors()
        self._finish_body()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_json(self, status, payload, extra=None):
        self.send_bytes(status, dumps(payload).encode("utf-8"), "application/json; charset=utf-8", extra)

    def fail(self, e):
        err = {"code": e.code, "message": e.message, "detail": e.detail}
        self.send_json(e.status, {"error": err, **(e.extra or {})})

    def auth(self, need):
        h = self.headers.get("Authorization", "")
        m = re.match(r"Bearer\s+(.+)$", h.strip(), re.I)
        if not m:
            raise ApiError(401, "unauthorized", "Authorization: Bearer <nişan> başlığı tələb olunur")
        scopes = self.server.app.tokens.get(m.group(1).strip())
        if scopes is None:
            raise ApiError(401, "unauthorized", "Nişan tanınmadı")
        if need not in scopes:
            raise ApiError(403, "forbidden", "Bu nişanda «%s» icazəsi yoxdur" % need)
        return "write" if "write" in scopes else "read"

    def content_length(self):
        try:
            return int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise ApiError(400, "bad_request", "Content-Length yanlışdır")

    def read_body(self, n):
        self.body_consumed = True
        return self.rfile.read(n)

    def drain(self):
        self._finish_body()

    def json_body(self, optional=False):
        n = self.content_length()
        if n <= 0:
            if optional:
                return None
            raise ApiError(400, "empty_body", "Boş sorğu gövdəsi — JSON gözlənilir")
        if n > 32 * 1024 * 1024:
            raise ApiError(413, "too_large", "Sorğu çox böyükdür (maks. 32 MB)")
        try:
            return json.loads(self.read_body(n).decode("utf-8"))
        except Exception as ex:
            raise ApiError(400, "bad_json", "JSON oxunmadı: %s" % ex)

    # ---- routing
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _dispatch(self, method):
        self.body_consumed = True
        try:
            self.body_consumed = self.content_length() <= 0
            u = urlparse(self.path)
            path = u.path
            if path.startswith("/v1/"):
                path = "/api" + path
            if path.startswith("/api/"):
                parts = [x for x in path.split("/")[1:] if x]
                if len(parts) < 2 or parts[1] != "v1":
                    raise ApiError(404, "not_found", "API yolu /api/v1/ ilə başlamalıdır")
                return routes.route(self, method, parts[2:], parse_qs(u.query))
            if method in ("GET", "HEAD") and static_files.serve(self, self.server.app.cfg, path, head=(method == "HEAD")):
                return
            raise ApiError(404, "not_found", "Səhifə tapılmadı: %s" % path)
        except ApiError as e:
            self.fail(e)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True
        except Exception as ex:                                        # pragma: no cover
            self.fail(ApiError(500, "internal", "Daxili server xətası", detail="%s: %s" % (type(ex).__name__, ex)))

    def do_GET(self):
        self._dispatch("GET")

    def do_HEAD(self):
        self._dispatch("HEAD")

    def do_POST(self):
        self._dispatch("POST")

    def do_DELETE(self):
        self._dispatch("DELETE")


class Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 128


def build_app(a, log=print):
    cfg = Config(root=Path(a.root), db=Path(a.db) if a.db else Path(a.root) / "api" / "micro.db",
                 runner=Path(a.runner) if a.runner else None, engine_chain=a.engine_chain, engine_pkg=a.engine_pkg,
                 engine_paths=[str(Path(a.root).resolve())] + ([a.engine_path] if a.engine_path else []),
                 max_upload_mb=a.max_upload_mb, dry_run_runs=a.dry_run_runs, snapshot=a.snapshot,
                 keep_vintages=a.keep, stage_timeout=a.stage_timeout, run_extra_args=list(a.run_arg))
    app = App(cfg, load_tokens(), log=log)
    app.auto_run = bool(a.auto_run)
    if a.watch or a.schedule or a.dsk_refresh:
        import autonomous
        if a.watch:
            folder = Path(a.watch)
            folder = folder if folder.is_absolute() else (cfg.root / folder)
            app.watcher = autonomous.Watcher(cfg, app.uploads, app.runs, folder, poll=a.poll, auto_run=a.auto_run, log=log)
        if a.schedule or a.dsk_refresh:
            app.scheduler = autonomous.Scheduler(cfg, app.runs, schedule=a.schedule, dsk=a.dsk_refresh,
                                                 refresh_hours=a.dsk_refresh_hours, auto_run=True, log=log)
    return app


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="MİİS §15.5.2 mikroiqtisadi modulun məlumat API-si və avtonom icra serveri")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8790)
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="MicroUnit qovluğu (standart: api/-nin üst qovluğu)")
    ap.add_argument("--db", default=None, help="SQLite faylı (standart: <root>/api/micro.db)")
    ap.add_argument("--runner", default=None, help="run_all.py yolu (standart: <root>/run_all.py)")
    ap.add_argument("--watch", default=None, help="avtonom rejim: izlənən düşmə qovluğu, məs. data/inbox_drop")
    ap.add_argument("--poll", type=float, default=30.0, help="düşmə qovluğunun yoxlanma intervalı, saniyə")
    ap.add_argument("--auto-run", action="store_true", help="tətbiq olunan fayldan sonra icranı avtomatik başlat")
    ap.add_argument("--schedule", default=None, help="gündəlik icra vaxtı HH:MM (yerli vaxt)")
    ap.add_argument("--dsk-refresh", action="store_true", help="DSK fayllarını yenidən endir, dəyişiklik varsa icra et")
    ap.add_argument("--dsk-refresh-hours", type=float, default=24.0, help="--schedule olmadan DSK yeniləmə intervalı, saat")
    ap.add_argument("--snapshot", action="store_true", help="uğurlu icradan sonra output/vintages/<run_id>/ surəti")
    ap.add_argument("--keep", type=int, default=5, help="saxlanılan surətlərin sayı")
    ap.add_argument("--stage-timeout", type=int, default=3600, help="bir mərhələ üçün vaxt limiti, saniyə")
    ap.add_argument("--engine-chain", default="microlib.engines.chain", help="ssenari zənciri modulu")
    ap.add_argument("--engine-pkg", default="microlib.engines", help="modul mühərrikləri paketi")
    ap.add_argument("--engine-path", default=None, help="mühərrik modulu üçün əlavə sys.path qovluğu")
    ap.add_argument("--max-upload-mb", type=int, default=512)
    ap.add_argument("--dry-run-runs", action="store_true", help="sınaq rejimi: bütün icralar yalnız planlaşdırılır (--dry-run)")
    ap.add_argument("--quiet", action="store_true", help="sorğu jurnalını çap etmə")
    ap.add_argument("--run-arg", action="append", default=[], help=argparse.SUPPRESS)   # tests: extra run_all.py args
    return ap.parse_args(argv)


def main(argv=None):
    a = parse_args(argv)
    if using_default_tokens():
        if a.host not in ("127.0.0.1", "localhost", "::1"):
            sys.exit("XƏTA: standart sınaq nişanları ilə şəbəkəyə açıla bilməz.\n"
                     "      Əvvəlcə nişanları təyin edin, məsələn:\n"
                     '      export API_TOKENS="mikro-oxu:read,mikro-yaz:write"')
        print("XƏBƏRDARLIQ: standart sınaq nişanları istifadə olunur (demo-read / demo-write). "
              "İstehsalda API_TOKENS mühit dəyişənini təyin edin.", file=sys.stderr)
    if a.schedule:
        import autonomous
        try:
            autonomous.next_at(a.schedule)
        except ValueError:
            sys.exit("XƏTA: --schedule HH:MM formatında olmalıdır, məs. 06:30")
    app = build_app(a)
    httpd = Server((a.host, a.port), Handler)
    httpd.app, httpd.quiet = app, a.quiet
    for t in (app.watcher, app.scheduler):
        if t:
            t.start()
    host = "[%s]" % a.host if ":" in a.host else a.host
    print("MikroModel API %s  http://%s:%d/api/v1/health   panel: http://%s:%d/panel/" % (API_VERSION, host, httpd.server_port, host, httpd.server_port))
    print("kök: %s   baza: %s" % (app.cfg.root, app.cfg.db))
    print("nişanlar: %s" % ", ".join("%s=%s" % (k[:4] + "…" if not using_default_tokens() else k, "|".join(sorted(v)))
                                    for k, v in app.tokens.items()))
    if app.watcher:
        print("avtonom rejim: %s qovluğu hər %.0f s yoxlanılır%s" % (app.watcher.folder, app.watcher.poll,
                                                                    ", tətbiqdən sonra icra avtomatikdir" if a.auto_run else ""))
    if app.scheduler:
        print("cədvəl: %s%s" % (("hər gün %s" % a.schedule) if a.schedule else "cədvəlsiz",
                                ", DSK yeniləməsi" if a.dsk_refresh else ""))
    sys.stdout.flush()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\ndayandırıldı")


if __name__ == "__main__":
    main()
