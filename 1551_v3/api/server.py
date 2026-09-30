#!/usr/bin/env python3
"""
MİİS §15.5.1 — baza məlumatı API-si (istinad tətbiqi / reference implementation).

Yalnız Python standart kitabxanasından istifadə edir — heç bir paket quraşdırmaq lazım deyil.
Məlumat SQLite faylında saxlanılır. İstehsal mühitində bu xidməti öz stekinizlə əvəz edə
bilərsiniz: müqavilə `openapi.yaml` faylındadır, bu server isə onun işlək nümunəsidir.

    python3 server.py --seed catalogue.json      # bazanı ilk dəfə doldurur
    python3 server.py                            # 127.0.0.1:8787 üzərində işə salır

Nişanlar (tokens): API_TOKENS mühit dəyişəni, "oxu_nişanı:read,yaz_nişanı:write" formatında.
Standart (yalnız sınaq üçün): read=demo-read, write=demo-write
"""
import argparse, json, os, re, sqlite3, sys, threading, time, uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

DB_LOCK = threading.Lock()
DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "miis.db")
API_VERSION = "1.0.0"

SCHEMA = """
CREATE TABLE IF NOT EXISTS model (
  id TEXT PRIMARY KEY, name_az TEXT, sheets INTEGER, formulas INTEGER,
  first_year INTEGER, last_year INTEGER, last_actual INTEGER
);
CREATE TABLE IF NOT EXISTS series (
  model TEXT NOT NULL, code TEXT NOT NULL, kind TEXT, label_az TEXT, unit_az TEXT,
  freq TEXT, book TEXT, sheet TEXT, row INTEGER, first_year INTEGER, last_year INTEGER,
  options TEXT, updated_at TEXT,
  PRIMARY KEY (model, code)
);
CREATE TABLE IF NOT EXISTS observation (
  model TEXT NOT NULL, code TEXT NOT NULL, period INTEGER NOT NULL,
  value REAL, source TEXT, actor TEXT, note TEXT, revision INTEGER DEFAULT 1,
  updated_at TEXT NOT NULL, seq INTEGER NOT NULL,
  PRIMARY KEY (model, code, period)
);
CREATE INDEX IF NOT EXISTS obs_seq ON observation(seq);
CREATE TABLE IF NOT EXISTS observation_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT, model TEXT, code TEXT, period INTEGER,
  old_value REAL, new_value REAL, source TEXT, actor TEXT, note TEXT, at TEXT
);
CREATE TABLE IF NOT EXISTS forecast (
  vintage TEXT NOT NULL, model TEXT NOT NULL, code TEXT NOT NULL, period INTEGER NOT NULL,
  value REAL, PRIMARY KEY (vintage, model, code, period)
);
CREATE TABLE IF NOT EXISTS vintage (
  name TEXT PRIMARY KEY, model TEXT, created_at TEXT, actor TEXT, note TEXT, points INTEGER
);
CREATE TABLE IF NOT EXISTS counter (name TEXT PRIMARY KEY, value INTEGER);
"""

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def connect(db):
    c = sqlite3.connect(db, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(SCHEMA)
    return c

def next_seq(con):
    cur = con.execute("SELECT value FROM counter WHERE name='seq'")
    r = cur.fetchone()
    v = (r["value"] if r else 0) + 1
    con.execute("INSERT INTO counter(name,value) VALUES('seq',?) ON CONFLICT(name) DO UPDATE SET value=?", (v, v))
    return v

# ---------------------------------------------------------------- seeding
def seed(con, path):
    data = json.load(open(path, encoding="utf-8"))
    ts = now_iso()
    with DB_LOCK:
        for m in data["models"]:
            con.execute("INSERT INTO model(id,name_az,sheets,formulas,first_year,last_year,last_actual) VALUES(?,?,?,?,?,?,?) "
                        "ON CONFLICT(id) DO UPDATE SET name_az=excluded.name_az, sheets=excluded.sheets, formulas=excluded.formulas,"
                        "first_year=excluded.first_year, last_year=excluded.last_year, last_actual=excluded.last_actual",
                        (m["id"], m["name_az"], m.get("sheets"), m.get("formulas"), m.get("first"), m.get("last"), m.get("lastActual")))
        n_s = n_o = 0
        for s in data["series"]:
            src = s.get("source") or {}
            con.execute("INSERT INTO series(model,code,kind,label_az,unit_az,freq,book,sheet,row,first_year,last_year,options,updated_at) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(model,code) DO UPDATE SET "
                        "kind=excluded.kind,label_az=excluded.label_az,unit_az=excluded.unit_az,freq=excluded.freq,"
                        "book=excluded.book,sheet=excluded.sheet,row=excluded.row,first_year=excluded.first_year,"
                        "last_year=excluded.last_year,options=excluded.options,updated_at=excluded.updated_at",
                        (s["model"], s["code"], s.get("kind", "series"), s.get("label_az"), s.get("unit_az"),
                         s.get("freq", "A"), src.get("book"), src.get("sheet"), src.get("row"),
                         s.get("first"), s.get("last"),
                         json.dumps(s["options"], ensure_ascii=False) if s.get("options") else None, ts))
            n_s += 1
            for per, val in (s.get("obs") or {}).items():
                sq = next_seq(con)
                con.execute("INSERT INTO observation(model,code,period,value,source,actor,note,revision,updated_at,seq) "
                            "VALUES(?,?,?,?,?,?,?,1,?,?) ON CONFLICT(model,code,period) DO NOTHING",
                            (s["model"], s["code"], int(per), float(val), "model-baseline", "seed", None, ts, sq))
                n_o += 1
        con.commit()
    return n_s, n_o

# ---------------------------------------------------------------- auth
def load_tokens():
    raw = os.environ.get("API_TOKENS", "demo-read:read,demo-write:write")
    out = {}
    for part in raw.split(","):
        part = part.strip()
        if not part: continue
        tok, _, scopes = part.partition(":")
        sc = set(s.strip() for s in (scopes or "read").split("|") if s.strip())
        if "write" in sc: sc.add("read")      # a writer must be able to read back what it wrote
        out[tok.strip()] = sc
    return out
TOKENS = load_tokens()

class ApiError(Exception):
    def __init__(self, status, code, message, detail=None):
        self.status, self.code, self.message, self.detail = status, code, message, detail

# ---------------------------------------------------------------- handler
class Handler(BaseHTTPRequestHandler):
    server_version = "MIIS-API/" + API_VERSION
    protocol_version = "HTTP/1.1"

    # ---- plumbing
    def log_message(self, fmt, *args):
        sys.stderr.write("%s  %s\n" % (self.log_date_time_string(), fmt % args))

    def _cors(self):
        origin = self.headers.get("Origin")
        allowed = os.environ.get("API_ORIGINS", "*")
        # a package opened from disk sends Origin: null — it must be allowed explicitly
        self.send_header("Access-Control-Allow-Origin", origin if (allowed == "*" and origin) else (allowed if allowed != "*" else "*"))
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, If-None-Match")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")

    def _send(self, status, payload, extra=None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _fail(self, e):
        self._send(e.status, {"error": {"code": e.code, "message": e.message, "detail": e.detail}})

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.send_header("Content-Length", "0"); self.end_headers()

    def _auth(self, need):
        h = self.headers.get("Authorization", "")
        m = re.match(r"Bearer\s+(.+)$", h.strip(), re.I)
        if not m: raise ApiError(401, "unauthorized", "Authorization: Bearer <token> başlığı tələb olunur")
        scopes = TOKENS.get(m.group(1).strip())
        if scopes is None: raise ApiError(401, "unauthorized", "Nişan tanınmadı")
        if need not in scopes: raise ApiError(403, "forbidden", "Bu nişanda «%s» icazəsi yoxdur" % need)
        return m.group(1).strip()

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0: raise ApiError(400, "empty_body", "Boş sorğu gövdəsi")
        if n > 32 * 1024 * 1024: raise ApiError(413, "too_large", "Sorğu çox böyükdür (maks. 32 MB)")
        try: return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception as ex: raise ApiError(400, "bad_json", "JSON oxunmadı: %s" % ex)

    # ---- routing
    def do_GET(self):
        try: self._route("GET")
        except ApiError as e: self._fail(e)
        except Exception as ex: self._fail(ApiError(500, "internal", str(ex)))

    def do_POST(self):
        try: self._route("POST")
        except ApiError as e: self._fail(e)
        except Exception as ex: self._fail(ApiError(500, "internal", str(ex)))

    def _route(self, method):
        u = urlparse(self.path)
        p = [x for x in u.path.strip("/").split("/") if x]
        q = parse_qs(u.query)
        one = lambda k, d=None: (q.get(k, [d])[0])
        con = self.server.con

        if p == ["v1", "health"] and method == "GET":
            r = con.execute("SELECT COUNT(*) n FROM series").fetchone()
            o = con.execute("SELECT COUNT(*) n FROM observation").fetchone()
            return self._send(200, {"status": "ok", "version": API_VERSION, "time": now_iso(),
                                    "series": r["n"], "observations": o["n"]})

        if p == ["v1", "openapi.yaml"] and method == "GET":
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "openapi.yaml")
            if not os.path.exists(path): raise ApiError(404, "not_found", "openapi.yaml tapılmadı")
            body = open(path, "rb").read()
            self.send_response(200); self.send_header("Content-Type", "application/yaml; charset=utf-8")
            self.send_header("Content-Length", str(len(body))); self._cors(); self.end_headers(); self.wfile.write(body); return

        self._auth("write" if method == "POST" else "read")

        if p == ["v1", "models"] and method == "GET":
            rows = [dict(r) for r in con.execute("SELECT * FROM model ORDER BY id")]
            return self._send(200, {"items": rows})

        if p == ["v1", "series"] and method == "GET":
            where, args = [], []
            if one("model"): where.append("model=?"); args.append(one("model"))
            if one("kind"): where.append("kind=?"); args.append(one("kind"))
            if one("q"):
                where.append("(code LIKE ? OR IFNULL(label_az,'') LIKE ?)")
                args += ["%" + one("q") + "%"] * 2
            lim = max(1, min(2000, int(one("limit", "500")))); off = max(0, int(one("offset", "0")))
            sql = "SELECT * FROM series" + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY model, code LIMIT ? OFFSET ?"
            rows = [dict(r) for r in con.execute(sql, args + [lim, off])]
            for r in rows:
                if r.get("options"):
                    try: r["options"] = json.loads(r["options"])
                    except Exception: pass
            tot = con.execute("SELECT COUNT(*) n FROM series" + (" WHERE " + " AND ".join(where) if where else ""), args).fetchone()["n"]
            return self._send(200, {"items": rows, "total": tot, "limit": lim, "offset": off})

        if len(p) == 4 and p[0] == "v1" and p[1] == "series" and method == "GET":
            model, code = p[2], p[3]
            s = con.execute("SELECT * FROM series WHERE model=? AND code=?", (model, code)).fetchone()
            if not s: raise ApiError(404, "not_found", "Sıra tapılmadı: %s/%s" % (model, code))
            d = dict(s)
            if d.get("options"):
                try: d["options"] = json.loads(d["options"])
                except Exception: pass
            d["observations"] = [{"period": r["period"], "value": r["value"], "source": r["source"],
                                  "actor": r["actor"], "updated_at": r["updated_at"], "revision": r["revision"]}
                                 for r in con.execute("SELECT * FROM observation WHERE model=? AND code=? ORDER BY period", (model, code))]
            return self._send(200, d)

        if p == ["v1", "observations"] and method == "GET":
            where, args = [], []
            if one("model"): where.append("model=?"); args.append(one("model"))
            if one("code"):
                codes = [c for c in one("code").split(",") if c]
                where.append("code IN (%s)" % ",".join("?" * len(codes))); args += codes
            if one("from"): where.append("period>=?"); args.append(int(one("from")))
            if one("to"): where.append("period<=?"); args.append(int(one("to")))
            if one("updated_since"): where.append("updated_at>=?"); args.append(one("updated_since"))
            if one("since_seq"): where.append("seq>?"); args.append(int(one("since_seq")))
            lim = max(1, min(50000, int(one("limit", "10000")))); off = max(0, int(one("offset", "0")))
            sql = "SELECT model,code,period,value,source,actor,note,revision,updated_at,seq FROM observation"
            sql += (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY seq LIMIT ? OFFSET ?"
            rows = [dict(r) for r in con.execute(sql, args + [lim, off])]
            tot = con.execute("SELECT COUNT(*) n FROM observation" + (" WHERE " + " AND ".join(where) if where else ""), args).fetchone()["n"]
            mx = con.execute("SELECT IFNULL(MAX(seq),0) s FROM observation").fetchone()["s"]
            return self._send(200, {"items": rows, "total": tot, "limit": lim, "offset": off, "max_seq": mx})

        if p == ["v1", "observations"] and method == "POST":
            body = self._body()
            items = body.get("items") if isinstance(body, dict) else body
            if not isinstance(items, list): raise ApiError(400, "bad_request", "«items» massivi gözlənilir")
            if len(items) > 20000: raise ApiError(413, "too_large", "Bir sorğuda maksimum 20 000 nöqtə")
            actor = (body.get("actor") if isinstance(body, dict) else None) or "api"
            source = (body.get("source") if isinstance(body, dict) else None) or "api"
            note = (body.get("note") if isinstance(body, dict) else None)
            dry = str(one("dry_run", "")).lower() in ("1", "true", "yes")
            applied, rejected, ts = [], [], now_iso()
            with DB_LOCK:
                for i, it in enumerate(items):
                    try:
                        model = str(it["model"]); code = str(it["code"]); per = int(it["period"])
                        val = it.get("value")
                        if val is not None:
                            val = float(val)
                            if val != val or val in (float("inf"), float("-inf")): raise ValueError("ədəd deyil")
                    except Exception as ex:
                        rejected.append({"index": i, "reason": "bad_item", "message": str(ex)}); continue
                    s = con.execute("SELECT first_year,last_year FROM series WHERE model=? AND code=?", (model, code)).fetchone()
                    if not s:
                        rejected.append({"index": i, "model": model, "code": code, "reason": "unknown_series",
                                         "message": "Bu kodla sıra yoxdur"}); continue
                    if per < 1990 or per > 2100:
                        rejected.append({"index": i, "model": model, "code": code, "period": per,
                                         "reason": "period_out_of_range", "message": "İl 1990–2100 aralığında olmalıdır"}); continue
                    prev = con.execute("SELECT value,revision FROM observation WHERE model=? AND code=? AND period=?", (model, code, per)).fetchone()
                    if dry:
                        applied.append({"model": model, "code": code, "period": per, "value": val,
                                        "previous": prev["value"] if prev else None, "action": "update" if prev else "insert"})
                        continue
                    sq = next_seq(con)
                    rev = (prev["revision"] + 1) if prev else 1
                    con.execute("INSERT INTO observation(model,code,period,value,source,actor,note,revision,updated_at,seq) "
                                "VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(model,code,period) DO UPDATE SET "
                                "value=excluded.value, source=excluded.source, actor=excluded.actor, note=excluded.note,"
                                "revision=excluded.revision, updated_at=excluded.updated_at, seq=excluded.seq",
                                (model, code, per, val, it.get("source", source), it.get("actor", actor), it.get("note", note), rev, ts, sq))
                    con.execute("INSERT INTO observation_history(model,code,period,old_value,new_value,source,actor,note,at) VALUES(?,?,?,?,?,?,?,?,?)",
                                (model, code, per, prev["value"] if prev else None, val, it.get("source", source), it.get("actor", actor), it.get("note", note), ts))
                    applied.append({"model": model, "code": code, "period": per, "value": val,
                                    "previous": prev["value"] if prev else None, "revision": rev,
                                    "action": "update" if prev else "insert"})
                if not dry: con.commit()
            mx = con.execute("SELECT IFNULL(MAX(seq),0) s FROM observation").fetchone()["s"]
            return self._send(200 if dry else 201, {"dry_run": dry, "applied": len(applied), "rejected": len(rejected),
                                                    "max_seq": mx, "items": applied, "errors": rejected})

        if p == ["v1", "history"] and method == "GET":
            where, args = [], []
            for k, col in (("model", "model"), ("code", "code")):
                if one(k): where.append(col + "=?"); args.append(one(k))
            if one("period"): where.append("period=?"); args.append(int(one("period")))
            lim = max(1, min(5000, int(one("limit", "500"))))
            sql = "SELECT * FROM observation_history" + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY id DESC LIMIT ?"
            return self._send(200, {"items": [dict(r) for r in con.execute(sql, args + [lim])]})

        if p == ["v1", "forecasts"] and method == "GET":
            where, args = [], []
            for k in ("model", "code", "vintage"):
                if one(k): where.append(k + "=?"); args.append(one(k))
            lim = max(1, min(50000, int(one("limit", "10000"))))
            sql = "SELECT * FROM forecast" + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY vintage, model, code, period LIMIT ?"
            return self._send(200, {"items": [dict(r) for r in con.execute(sql, args + [lim])]})

        if p == ["v1", "forecasts"] and method == "POST":
            body = self._body()
            name = (body.get("vintage") or "").strip() or ("v" + now_iso().replace(":", "").replace("-", ""))
            items = body.get("items") or []
            if not isinstance(items, list): raise ApiError(400, "bad_request", "«items» massivi gözlənilir")
            ts, n = now_iso(), 0
            with DB_LOCK:
                for it in items:
                    try:
                        con.execute("INSERT INTO forecast(vintage,model,code,period,value) VALUES(?,?,?,?,?) "
                                    "ON CONFLICT(vintage,model,code,period) DO UPDATE SET value=excluded.value",
                                    (name, str(it["model"]), str(it["code"]), int(it["period"]),
                                     None if it.get("value") is None else float(it["value"])))
                        n += 1
                    except Exception: pass
                con.execute("INSERT INTO vintage(name,model,created_at,actor,note,points) VALUES(?,?,?,?,?,?) "
                            "ON CONFLICT(name) DO UPDATE SET points=excluded.points, note=excluded.note",
                            (name, body.get("model"), ts, body.get("actor", "api"), body.get("note"), n))
                con.commit()
            return self._send(201, {"vintage": name, "points": n, "created_at": ts})

        if p == ["v1", "vintages"] and method == "GET":
            return self._send(200, {"items": [dict(r) for r in con.execute("SELECT * FROM vintage ORDER BY created_at DESC LIMIT 200")]})

        raise ApiError(404, "not_found", "Belə bir endpoint yoxdur: %s %s" % (method, u.path))

def main():
    ap = argparse.ArgumentParser(description="MİİS §15.5.1 baza məlumatı API-si")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--seed", help="catalogue.json faylından bazanı doldur və çıx")
    a = ap.parse_args()
    con = connect(a.db)
    if a.seed:
        s, o = seed(con, a.seed)
        print("seeded: %d series, %d observations -> %s" % (s, o, a.db)); return
    httpd = ThreadingHTTPServer((a.host, a.port), Handler)
    httpd.con = con
    print("MİİS API %s  http://%s:%d/v1/health   (db: %s)" % (API_VERSION, a.host, a.port, a.db))
    print("tokens: %s" % ", ".join("%s=%s" % (k, "|".join(sorted(v))) for k, v in TOKENS.items()))
    try: httpd.serve_forever()
    except KeyboardInterrupt: print("\nstopped")

if __name__ == "__main__":
    main()
