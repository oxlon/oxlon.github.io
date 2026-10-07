"""
http_handler — HTTP qatı (yalnız standart kitabxana): nişan yoxlaması, CORS (yalnız yerli mənşələr; API_ORIGINS),
JSON gövdə, xətaların Azərbaycan dilində JSON formatı, statik fayllar. RiskUnit/api/server.py-dən uyğunlaşdırılıb.
"""
import os, re, sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

import routes, static_files
from apicore import API_VERSION, ApiError, dumps

LOCAL_ORIGIN = re.compile(r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$")


class Handler(BaseHTTPRequestHandler):
    server_version = "SiyasetModel-API/" + API_VERSION
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


