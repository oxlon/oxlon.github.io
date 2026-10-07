"""
apidb — SQLite saxlancı: ssenari qaralamaları, hesablamalar (nəticə keşi), KPI dəstləri, API ilə əlavə edilən
alətlərin jurnalı, yeniləmə işləri, hadisələr lenti. (RiskUnit/api/apidb.py-dən uyğunlaşdırılıb.)
"""
import json, sqlite3, threading

from apicore import DB_LOCK, now_iso

SCHEMA = """
CREATE TABLE IF NOT EXISTS draft (
  id TEXT PRIMARY KEY, body TEXT NOT NULL, note TEXT, actor TEXT, origin TEXT, created TEXT NOT NULL, updated TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS run (
  id TEXT PRIMARY KEY, scenario_id TEXT, source TEXT, request TEXT, scenario TEXT, cache_key TEXT, vintage_id TEXT,
  status TEXT NOT NULL, progress TEXT, result TEXT, error TEXT, actor TEXT, started TEXT, finished TEXT, seconds REAL
);
CREATE INDEX IF NOT EXISTS run_key ON run(cache_key, status);
CREATE INDEX IF NOT EXISTS run_scn ON run(scenario_id, started);
CREATE TABLE IF NOT EXISTS kpiset (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, kpis TEXT NOT NULL, weights TEXT, note TEXT, actor TEXT,
  created TEXT NOT NULL, updated TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS instrument_log (
  id TEXT NOT NULL, action TEXT NOT NULL, body TEXT, backup TEXT, actor TEXT, time TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS job (
  id TEXT PRIMARY KEY, mode TEXT, trigger TEXT, actor TEXT, status TEXT NOT NULL, command TEXT, pid INTEGER,
  started TEXT, finished TEXT, seconds REAL, returncode INTEGER, log TEXT, note TEXT, error TEXT
);
CREATE TABLE IF NOT EXISTS event (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT NOT NULL, kind TEXT, message TEXT, data TEXT
);
"""

_local = threading.local()


def init(db_path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(db_path), timeout=30)
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(SCHEMA)
    c.commit()
    c.close()


def conn(db_path):
    """Hər işçi axını (thread) öz bağlantısını alır; WAL oxucuları yazıçını bloklamır."""
    key = str(db_path)
    cache = getattr(_local, "cons", None)
    if cache is None:
        cache = _local.cons = {}
    c = cache.get(key)
    if c is None:
        c = sqlite3.connect(key, check_same_thread=False, timeout=30)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA busy_timeout=30000")
        cache[key] = c
    return c


def row(r, json_cols=()):
    if r is None:
        return None
    d = dict(r)
    for k in json_cols:
        if d.get(k):
            try:
                d[k] = json.loads(d[k])
            except ValueError:
                pass
    return d


def execute(db_path, sql, args=()):
    con = conn(db_path)
    with DB_LOCK:
        cur = con.execute(sql, args)
        con.commit()
        return cur.rowcount


def query(db_path, sql, args=(), json_cols=()):
    return [row(r, json_cols) for r in conn(db_path).execute(sql, args).fetchall()]


def event(db_path, kind, message, data=None):
    con = conn(db_path)
    with DB_LOCK:
        cur = con.execute("INSERT INTO event(time,kind,message,data) VALUES(?,?,?,?)",
                          (now_iso(), kind, message, json.dumps(data, ensure_ascii=False, default=str) if data is not None else None))
        con.commit()
        return cur.lastrowid


def events(db_path, since=0, limit=100):
    rows = query(db_path, "SELECT * FROM event WHERE seq>? ORDER BY seq DESC LIMIT ?", (int(since), int(limit)), ("data",))
    return list(reversed(rows))


def last_seq(db_path):
    r = conn(db_path).execute("SELECT MAX(seq) AS m FROM event").fetchone()
    return int(r["m"] or 0)
