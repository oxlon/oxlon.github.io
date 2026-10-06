#!/usr/bin/env python3
"""
MİİS §15.5.3 — Risk modulunun (RiskUnit v2) API-si, canlı analiz və avtonom icra serveri (istinad tətbiqi).

HTTP qatı yalnız standart kitabxanadır (ThreadingHTTPServer, SQLite); analiz riskunit modullarını və MikroUnit
zəncirini (microlib.engines.chain) çağırır — numpy/pandas/scipy olan Python lazımdır. Müqavilə: openapi.yaml.

    python3 api/server.py                                    # http://127.0.0.1:8791/panel/
    python3 api/server.py --schedule 06:30,13:00,18:30 --watch   # avtonom rejim

Nişanlar: RISK_API_TOKENS (və ya API_TOKENS) = "oxu_nişanı:read,yaz_nişanı:write".
Standart (yalnız sınaq üçün): demo-read / demo-write — GET üçün read, POST/PUT/DELETE üçün write.
"""
import argparse, os, re, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import apidb, routes, static_files                                      # noqa: E402
from analysis_base import Base                                           # noqa: E402
from analysis_opt import Optimizer                                       # noqa: E402
from apicore import (API_VERSION, DEFAULT_PORT, DEFAULT_ROOT, ApiError, Config, dumps, load_tokens,  # noqa: E402
                     now_iso, read_json, using_default_tokens)
from data_views import Views                                             # noqa: E402
from risk_views import RiskViews                                         # noqa: E402
from run_manager import RefreshManager                                   # noqa: E402
from scenarios import Store                                              # noqa: E402

LOCAL_ORIGIN = re.compile(r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$")


class App:
    def __init__(self, cfg, tokens, log=print):
        apidb.init(cfg.db)
        self.cfg, self.tokens, self.log, self.version = cfg, tokens, log, API_VERSION
        self.views = Views(cfg)
        self.risks = RiskViews(self.views)
        self.base = Base(cfg)
        self.opt = Optimizer(self.base)
        self.store = Store(cfg)
        self.runs = RefreshManager(cfg, log=log)
        self.runs.on_finish.append(lambda job: self.views._cache.clear())
        self.started_at = now_iso()
        self.watcher = self.scheduler = None
        self.warm_state = {"status": "gözlənilir"}

    def baseline_id(self):
        s = read_json(self.cfg.output / "_run_summary_v2.json") or {}
        return s.get("baseline_id")

    def autonomous_state(self):
        return {"schedule": self.scheduler.state() if self.scheduler else None,
                "watch": self.watcher.state() if self.watcher else None,
                "no_network": os.environ.get("RISK_NO_NETWORK") == "1"}

    def warm(self):
        """Background warm-up of the analysis caches (first stress/optimize call is then fast)."""
        def job():
            import time
            t0 = time.time()
            self.warm_state = {"status": "isinir", "started": now_iso()}
            try:
                with routes.ANALYSIS_LOCK:
                    self.base.sc_state()
                    self.opt.state()
                self.warm_state = {"status": "hazır", "seconds": round(time.time() - t0, 1), "at": now_iso()}
            except Exception as e:
                self.warm_state = {"status": "xəta", "detail": "%s: %s" % (type(e).__name__, str(e)[:300])}
            self.log("analiz keşi: %s" % self.warm_state)
        threading.Thread(target=job, daemon=True, name="warm").start()


class Handler(BaseHTTPRequestHandler):
    server_version = "RiskModel-API/" + API_VERSION
    protocol_version = "HTTP/1.1"

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
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Actor")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
            self.send_header("Access-Control-Expose-Headers", "Content-Disposition")
            self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")

    def _finish_body(self):
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
        self.send_header("Cache-Control", "no-store")
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
        self.send_json(e.status, {"error": {"code": e.code, "message": e.message, "detail": e.detail}, **(e.extra or {})})

    def auth(self, need):
        m = re.match(r"Bearer\s+(.+)$", self.headers.get("Authorization", "").strip(), re.I)
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

    def drain(self):
        self._finish_body()

    def json_body(self, optional=False):
        import json
        n = self.content_length()
        if n <= 0:
            if optional:
                return None
            raise ApiError(400, "empty_body", "Boş sorğu gövdəsi — JSON gözlənilir")
        if n > 8 * 1024 * 1024:
            raise ApiError(413, "too_large", "Sorğu çox böyükdür (maks. 8 MB)")
        self.body_consumed = True
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception as ex:
            raise ApiError(400, "bad_json", "Sorğu gövdəsi düzgün JSON deyil", detail=str(ex)[:300])

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

    def do_PUT(self):
        self._dispatch("PUT")

    def do_DELETE(self):
        self._dispatch("DELETE")


class Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 128


def build_app(a, log=print):
    cfg = Config(root=Path(a.root), db=Path(a.db) if a.db else None, python=a.python, warm=not a.no_warm)
    app = App(cfg, load_tokens(), log=log)
    import autonomous
    if a.schedule:
        app.scheduler = autonomous.Scheduler(cfg, app.runs, autonomous.parse_schedule(a.schedule), log=log)
    if a.watch:
        app.watcher = autonomous.Watcher(cfg, app.runs, poll=a.watch_interval, log=log, mode=a.watch_mode)
    return app


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="MİİS §15.5.3 risk modulunun API-si və avtonom icra serveri")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=int(os.environ.get("RISK_API_PORT", DEFAULT_PORT)))
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="RiskUnit qovluğu (standart: api/-nin üst qovluğu)")
    ap.add_argument("--db", default=None, help="SQLite faylı (standart: <root>/api/risk.db)")
    ap.add_argument("--python", default=None, help="update.py / run_all.py üçün Python (standart: bu Python)")
    ap.add_argument("--schedule", default=None,
                    help="gündəlik cədvəl HH:MM[,HH:MM] (yerli vaxt): ilk vaxt tam icra (update.py --full), qalanları "
                         "gündəlik monitor (--daily); açıq rejim: 06:30=full,13:00=daily")
    ap.add_argument("--watch", action="store_true", help="yuxarı axın vintajlarını izlə (yeni hash → tam icra)")
    ap.add_argument("--watch-interval", type=float, default=300.0, help="izləmə intervalı, saniyə (standart 300)")
    ap.add_argument("--watch-mode", default="full", choices=["full", "pipeline", "daily"], help="yeni vintajda icra rejimi")
    ap.add_argument("--no-warm", action="store_true", help="analiz keşini başlanğıcda isitmə")
    ap.add_argument("--quiet", action="store_true", help="sorğu jurnalını çap etmə")
    return ap.parse_args(argv)


def main(argv=None):
    a = parse_args(argv)
    if using_default_tokens():
        if a.host not in ("127.0.0.1", "localhost", "::1"):
            sys.exit("XƏTA: standart sınaq nişanları ilə şəbəkəyə açıla bilməz.\n"
                     '      Əvvəlcə nişanları təyin edin, məsələn: export RISK_API_TOKENS="risk-oxu:read,risk-yaz:write"')
        print("XƏBƏRDARLIQ: standart sınaq nişanları istifadə olunur (demo-read / demo-write). "
              "İstehsalda RISK_API_TOKENS mühit dəyişənini təyin edin.", file=sys.stderr)
    if a.schedule:
        import autonomous
        try:
            autonomous.parse_schedule(a.schedule)
        except ValueError as e:
            sys.exit("XƏTA: --schedule: %s (məs. 06:30,13:00)" % e)
    app = build_app(a)
    httpd = Server((a.host, a.port), Handler)
    httpd.app, httpd.quiet = app, a.quiet
    for t in (app.watcher, app.scheduler):
        if t:
            t.start()
    if app.cfg.warm:
        app.warm()
    host = "[%s]" % a.host if ":" in a.host else a.host
    print("RiskModel API %s  http://%s:%d/api/v1/health   panel: http://%s:%d/panel/" % (API_VERSION, host, httpd.server_port,
                                                                                       host, httpd.server_port))
    print("kök: %s   baza: %s   şəbəkə: %s" % (app.cfg.root, app.cfg.db,
                                               "söndürülüb (RISK_NO_NETWORK=1)" if os.environ.get("RISK_NO_NETWORK") == "1" else "açıq"))
    if app.scheduler:
        print("cədvəl: %s; növbəti: %s (%s)" % (", ".join(app.scheduler.state()["slots"]), app.scheduler.next.isoformat(timespec="minutes"),
                                               app.scheduler.next_mode))
    if app.watcher:
        print("izləmə: yuxarı axın faylları hər %.0f s yoxlanılır (yeni vintaj → %s)" % (app.watcher.poll, app.watcher.mode))
    sys.stdout.flush()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\ndayandırıldı")


if __name__ == "__main__":
    main()
