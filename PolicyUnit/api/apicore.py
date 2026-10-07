"""
apicore — SiyasətModel (PolicyUnit) API-sinin ortaq hissəsi: konfiqurasiya, nişanlar (tokens), xətalar, JSON.

Yalnız standart kitabxana (RiskUnit/api/apicore.py-dən uyğunlaşdırılıb; ondan idxal edilmir).
"""
import json, math, os, re, threading, uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

API_VERSION = "1.0.0"
API_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = API_DIR.parent                     # PolicyUnit/
DEFAULT_PORT = 8792
DB_LOCK = threading.Lock()


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def stamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def new_id(prefix):
    return "%s%s-%s" % (prefix, stamp(), uuid.uuid4().hex[:6])


class ApiError(Exception):
    def __init__(self, status, code, message, detail=None, extra=None):
        super().__init__(message)
        self.status, self.code, self.message, self.detail, self.extra = status, code, message, detail, extra


# ------------------------------------------------------------------ configuration
@dataclass
class Config:
    root: Path = DEFAULT_ROOT           # PolicyUnit/ (outputs, logs, reports, panel)
    db: Path = None                     # SQLite (drafts, runs, KPI sets, jobs, events)
    config_dir: Path = None             # config/ (instruments, adapters, kpi, scenarios) — tests point to a copy
    python: str = None                  # interpreter for run_all.py (default: this one)
    refresh_cmd: list = None            # tests: explicit command override [exe, args...]
    warm: bool = True                   # warm up the engines (MicroUnit baseline) in the background at start-up
    extra_static: dict = field(default_factory=dict)
    risk_api: str = None                # RiskUnit API base (default policyunit.config.RISK_API)

    def __post_init__(self):
        self.root = Path(self.root).resolve()
        self.db = Path(self.db) if self.db else self.root / "api" / "policy.db"
        self.config_dir = Path(self.config_dir).resolve() if self.config_dir else self.root / "config"

    @property
    def output(self):
        return self.root / "output"

    @property
    def scenarios_dir(self):
        return self.config_dir / "scenarios"

    @property
    def backup_dir(self):
        return self.config_dir / "_backup"

    @property
    def reports(self):
        return self.root / "reports"

    @property
    def logs(self):
        return self.root / "logs" / "api"

    @property
    def lock_dir(self):
        return self.output / ".run_all.lock"    # mkdir lock (shared with cron/launchd wrappers)


# ------------------------------------------------------------------ tokens
def load_tokens(raw=None):
    """POLICY_API_TOKENS (və ya API_TOKENS) = "oxu_nişanı:read,yaz_nişanı:write" — write read-i də əhatə edir."""
    if raw is None:
        raw = os.environ.get("POLICY_API_TOKENS") or os.environ.get("API_TOKENS") or "demo-read:read,demo-write:write"
    out = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        tok, _, scopes = part.partition(":")
        sc = set(s.strip() for s in (scopes or "read").split("|") if s.strip())
        if "write" in sc:
            sc.add("read")
        out[tok.strip()] = sc
    return out


def using_default_tokens():
    return not (os.environ.get("POLICY_API_TOKENS") or os.environ.get("API_TOKENS"))


# ------------------------------------------------------------------ JSON
def jsonable(obj):
    """NaN/inf → null, numpy/pandas → adi tiplər (numpy idxal edilmədən)."""
    if obj is None or isinstance(obj, (str, bool)):
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    if hasattr(obj, "to_dict") and callable(obj.to_dict):          # pandas
        try:
            return jsonable(obj.to_dict(orient="records") if hasattr(obj, "columns") else obj.to_dict())
        except Exception:
            pass
    if hasattr(obj, "tolist") and callable(obj.tolist):            # numpy arrays
        try:
            return jsonable(obj.tolist())
        except Exception:
            pass
    if hasattr(obj, "item") and callable(obj.item):                # numpy scalars
        try:
            return jsonable(obj.item())
        except Exception:
            pass
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return str(obj)


def dumps(obj):
    return json.dumps(jsonable(obj), ensure_ascii=False, allow_nan=False)


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


SAFE_NAME = re.compile(r"[\x00-\x1f\x7f\\:*?\"<>|]")


def safe_relpath(name):
    """«P1_headline.csv» və ya «alt/x.csv»: «..», gizli hissələr, idarə simvolları rədd edilir."""
    name = str(name or "").strip()
    if not name or SAFE_NAME.search(name) or name.startswith("/"):
        raise ApiError(400, "bad_filename", "Fayl adı yanlışdır: %r" % name[:80])
    parts = [p for p in name.split("/") if p]
    if any(p in (".", "..") or p.startswith(".") for p in parts):
        raise ApiError(400, "bad_filename", "Fayl adı yanlışdır: %r" % name[:80])
    return "/".join(parts)


def within(base, path):
    try:
        b, p = os.path.realpath(base), os.path.realpath(path)
        return os.path.commonpath([b, p]) == b
    except ValueError:
        return False


def as_list(v):
    """'a,b' | ['a','b'] | None → ['a','b']"""
    if v is None:
        return []
    if isinstance(v, str):
        return [x.strip() for x in v.split(",") if x.strip()]
    return [str(x).strip() for x in v if str(x).strip()]
