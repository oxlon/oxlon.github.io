"""
apidb — SQLite saxlancı: yükləmələr, icralar, saxlanmış ssenarilər, müşahidələr (makro API kimi), hadisələr.
"""
import json, sqlite3, threading

from apicore import DB_LOCK, now_iso

SCHEMA = """
CREATE TABLE IF NOT EXISTS upload (
  id TEXT PRIMARY KEY, kind TEXT NOT NULL, filename TEXT, subfolder TEXT, stored_path TEXT,
  bytes INTEGER, sha256 TEXT, actor TEXT, note TEXT, source TEXT, status TEXT, valid INTEGER,
  report TEXT, target TEXT, backup TEXT, affected TEXT, run_id TEXT,
  created_at TEXT NOT NULL, applied_at TEXT
);
CREATE TABLE IF NOT EXISTS run (
  id TEXT PRIMARY KEY, status TEXT NOT NULL, request TEXT, plan TEXT, actor TEXT, trigger TEXT,
  pid INTEGER, created_at TEXT NOT NULL, started_at TEXT, finished_at TEXT, returncode INTEGER,
  log_dir TEXT, error TEXT
);
CREATE TABLE IF NOT EXISTS scenario_saved (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, author TEXT, scenario TEXT, overrides TEXT, result TEXT,
  note TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS observation (
  module TEXT NOT NULL, code TEXT NOT NULL, period INTEGER NOT NULL,
  value REAL, source TEXT, actor TEXT, note TEXT, revision INTEGER DEFAULT 1,
  upload_id TEXT, updated_at TEXT NOT NULL, seq INTEGER NOT NULL,
  PRIMARY KEY (module, code, period)
);
CREATE INDEX IF NOT EXISTS obs_seq ON observation(seq);
CREATE TABLE IF NOT EXISTS observation_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT, module TEXT, code TEXT, period INTEGER,
  old_value REAL, new_value REAL, source TEXT, actor TEXT, note TEXT, upload_id TEXT, at TEXT
);
CREATE TABLE IF NOT EXISTS event (
  id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, kind TEXT, message TEXT, detail TEXT
);
CREATE TABLE IF NOT EXISTS counter (name TEXT PRIMARY KEY, value INTEGER);
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
    """Hər işçi axını (thread) öz bağlantısını alır; WAL oxucuları yazıçıdan bloklamır."""
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


def next_seq(con):
    r = con.execute("SELECT value FROM counter WHERE name='seq'").fetchone()
    v = (r["value"] if r else 0) + 1
    con.execute("INSERT INTO counter(name,value) VALUES('seq',?) ON CONFLICT(name) DO UPDATE SET value=?", (v, v))
    return v


def event(db_path, kind, message, detail=None):
    con = conn(db_path)
    with DB_LOCK:
        con.execute("INSERT INTO event(at,kind,message,detail) VALUES(?,?,?,?)",
                    (now_iso(), kind, message, json.dumps(detail, ensure_ascii=False) if detail is not None else None))
        con.commit()


def events(db_path, limit=100):
    con = conn(db_path)
    return [row(r, ("detail",)) for r in con.execute("SELECT * FROM event ORDER BY id DESC LIMIT ?", (limit,))]
