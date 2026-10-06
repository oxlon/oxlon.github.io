"""
static_files — RiskUnit: ROOT/panel/ → /panel/, ROOT/site/ → /site/, ROOT/docs/ → /docs/, ROOT/index.html → /
(yoxdursa / → /panel/ yönləndirilir). MicroUnit/api/static_files.py-dən uyğunlaşdırılıb.

Yol keçidi (path traversal) bloklanır: URL deşifr edilir, «..», gizli fayllar, _build/__pycache__ və mənbə
kodu (.py) rədd olunur, yekun yol realpath ilə ağacın daxilində yoxlanılır. Qovluq siyahısı göstərilmir:
qovluq üçün yalnız onun index.html faylı verilir.
"""
import mimetypes, os
from email.utils import formatdate, parsedate_to_datetime
from urllib.parse import unquote

MIME = {".html": "text/html; charset=utf-8", ".htm": "text/html; charset=utf-8", ".js": "application/javascript; charset=utf-8",
        ".mjs": "application/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8",
        ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
        ".ico": "image/x-icon", ".webp": "image/webp", ".woff": "font/woff", ".woff2": "font/woff2", ".ttf": "font/ttf",
        ".csv": "text/csv; charset=utf-8", ".txt": "text/plain; charset=utf-8", ".md": "text/markdown; charset=utf-8",
        ".yaml": "application/yaml; charset=utf-8", ".yml": "application/yaml; charset=utf-8", ".pdf": "application/pdf",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".map": "application/json; charset=utf-8"}
BLOCKED_PARTS = {"_build", "__pycache__", ".git"}
BLOCKED_EXT = {".py", ".pyc", ".db", ".sqlite", ".lock", ".pkl"}


def mime_of(path):
    ext = os.path.splitext(path)[1].lower()
    return MIME.get(ext) or mimetypes.guess_type(path)[0] or "application/octet-stream"


def resolve(cfg, url_path):
    """URL yolu → fayl yolu; icazə verilmirsə və ya tapılmırsa None."""
    raw = url_path.split("?", 1)[0].split("#", 1)[0]
    path = unquote(raw, errors="strict") if "%" in raw else raw
    if "\x00" in path or "\\" in path:
        return None
    if path in ("", "/", "/index.html"):
        f = cfg.root / "index.html"
        return str(f) if f.is_file() else None
    trees = {"panel": cfg.root / "panel", "site": cfg.root / "site", "docs": cfg.root / "docs", **(cfg.extra_static or {})}
    parts = path.lstrip("/").split("/")
    if parts[0] not in trees:
        return None
    base = trees[parts[0]]
    rest = [p for p in parts[1:] if p != ""]
    for p in rest:
        if p in (".", "..") or p.startswith(".") or p in BLOCKED_PARTS:
            return None
    target = os.path.join(str(base), *rest) if rest else str(base)
    real_base, real = os.path.realpath(str(base)), os.path.realpath(target)
    try:
        if os.path.commonpath([real_base, real]) != real_base:
            return None
    except ValueError:
        return None
    if os.path.isdir(real):
        real = os.path.join(real, "index.html")
    if not os.path.isfile(real) or os.path.splitext(real)[1].lower() in BLOCKED_EXT:
        return None
    return real


def serve(handler, cfg, url_path, head=False):
    """True — cavab göndərildi; False — bu statik yol deyil (çağıran 404 qaytarsın)."""
    try:
        f = resolve(cfg, url_path)
    except UnicodeDecodeError:
        f = None
    bare = url_path.split("?", 1)[0]
    if f is None and bare in ("", "/") and (cfg.root / "panel").is_dir():
        f = "redirect"
    if f is None:
        return False
    if f == "redirect" or bare in ("/panel", "/site", "/docs"):          # /panel → /panel/ so relative links work
        handler.send_response(301)
        handler.send_header("Location", "/panel/" if f == "redirect" else bare + "/")
        handler.send_header("Content-Length", "0")
        handler.end_headers()
        return True
    st = os.stat(f)
    ims = handler.headers.get("If-Modified-Since")
    if ims:
        try:
            if int(st.st_mtime) <= parsedate_to_datetime(ims).timestamp():
                handler.send_response(304)
                handler.send_header("Content-Length", "0")
                handler.end_headers()
                return True
        except (TypeError, ValueError):
            pass
    handler.send_response(200)
    handler.send_header("Content-Type", mime_of(f))
    handler.send_header("Content-Length", str(st.st_size))
    handler.send_header("Last-Modified", formatdate(st.st_mtime, usegmt=True))
    handler.send_header("Cache-Control", "no-cache")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.end_headers()
    if not head:
        with open(f, "rb") as fh:
            while True:
                blk = fh.read(1 << 16)
                if not blk:
                    break
                handler.wfile.write(blk)
    return True
