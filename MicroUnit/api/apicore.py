"""
apicore — MikroModel API-sinin ortaq hissəsi: konfiqurasiya, nişanlar (tokens), xətalar, SQLite, JSON.

Yalnız standart kitabxana.
"""
import json, math, os, re, sqlite3, threading, uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

API_VERSION = "2.0.0"
API_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = API_DIR.parent
MODULES = ["FR1", "FR3", "FR4", "FR5", "FR10", "FR12"]
SCENARIOS = ["Baseline", "Adverse", "Reform"]
SCEN_AZ = {"Baseline": "Əsas", "Adverse": "Mənfi", "Reform": "İslahat", "Actual": "Faktiki"}
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


def module_name(v, required=True):
    """«fr10», «FR10» → «FR10»; naməlum modul — 400."""
    if v in (None, ""):
        if required:
            raise ApiError(400, "bad_parameter", "«module» parametri tələb olunur (%s)" % ", ".join(MODULES))
        return None
    k = str(v).strip().upper()
    if k not in MODULES:
        raise ApiError(400, "bad_parameter", "Naməlum modul: %r. Mümkün olanlar: %s" % (v, ", ".join(MODULES)))
    return k


# ------------------------------------------------------------------ configuration
@dataclass
class Config:
    root: Path = DEFAULT_ROOT
    db: Path = API_DIR / "micro.db"
    runner: Path = None                 # run_all.py
    python: str = None                  # interpreter for run_all.py
    engine_chain: str = "microlib.engines.chain"
    engine_pkg: str = "microlib.engines"
    engine_paths: list = field(default_factory=list)
    max_upload_mb: int = 512
    dry_run_runs: bool = False          # tests / integration rehearsals: every pipeline run is --dry-run
    run_extra_args: list = field(default_factory=list)
    snapshot: bool = False
    keep_vintages: int = 5
    stage_timeout: int = 3600

    def __post_init__(self):
        self.root = Path(self.root).resolve()
        self.db = Path(self.db)
        if self.runner is None:
            self.runner = self.root / "run_all.py"
        self.runner = Path(self.runner)
        if not self.engine_paths:
            self.engine_paths = [str(self.root)]

    @property
    def data(self):
        return self.root / "data"

    @property
    def output(self):
        return self.root / "output"

    @property
    def logs(self):
        return self.root / "logs"

    @property
    def inbox(self):
        return self.data / "inbox"

    @property
    def replaced(self):
        return self.data / "_replaced"


# ------------------------------------------------------------------ tokens
def load_tokens(raw=None):
    """API_TOKENS="oxu_nişanı:read,yaz_nişanı:write" — write avtomatik read-i də əhatə edir."""
    raw = os.environ.get("API_TOKENS", "demo-read:read,demo-write:write") if raw is None else raw
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
    return not os.environ.get("API_TOKENS")


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
    if hasattr(obj, "to_dict") and callable(obj.to_dict):          # pandas Series / DataFrame
        try:
            return jsonable(obj.to_dict())
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


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(jsonable(obj), ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


SAFE_NAME = re.compile(r"[\x00-\x1f\x7f/\\:*?\"<>|]")


def safe_filename(name):
    """Yalnız faylın adı (yol hissələri atılır); idarəetmə və təhlükəli simvollar «_» ilə əvəz olunur."""
    name = str(name or "").replace("\\", "/").split("/")[-1].strip()
    name = SAFE_NAME.sub("_", name).strip(" .")
    if not name or name in (".", ".."):
        raise ApiError(400, "bad_filename", "Fayl adı boşdur və ya yanlışdır")
    return name[:200]


def within(base, path):
    """path base qovluğunun daxilindədirmi (simvolik keçidlər həll edilərək)."""
    try:
        b, p = os.path.realpath(base), os.path.realpath(path)
        return os.path.commonpath([b, p]) == b
    except ValueError:
        return False
