"""webcore — shared core of the in-browser backend («Brauzerdə hesabla»): the panel loads Pyodide, mounts the unit's
Python bundle (panel/py/<unit>_bundle.zip, built by build_panel.py) under /mp/ with the project layout and calls
`<unit>_web.handle(method, path, body_json)`, which runs the SAME Python functions the local API calls.

Identical copy in MicroUnit/, RiskUnit/ and PolicyUnit/ panel/py/. Also used natively by the bundle builder:
    python3 webcore.py record <web module> <out.pkl>    # native results of the REPLAY functions (see below)
    python3 webcore.py trace  <web module> <replay.pkl> <out.json>   # files/modules used by SAMPLES + responses

REPLAY: a few functions only read big workbooks or hash upstream files (baseline ids, CAEM cells, IO sheets). Their
native results are recorded at build time and replayed in the browser, so the bundle stays small and needs no
openpyxl/xlrd; every computation downstream of them runs unchanged.
"""
import importlib, json, os, pickle, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
IN_BROWSER = sys.platform == "emscripten"
REPLAY_FILE = HERE / "_replay.pkl"
MODE = {"replay": None, "record": None}
if IN_BROWSER:
    for _k in ("MICRO_NO_NETWORK", "RISK_NO_NETWORK", "POLICY_NO_NETWORK"):
        os.environ.setdefault(_k, "1")


def unit_root(f):
    """<Unit>/ from <Unit>/panel/py/<x>.py"""
    return Path(f).resolve().parents[2]


def paths(*ps):
    for p in reversed(ps):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))


# ------------------------------------------------------------------ replay
def _key(how, args, kwargs):
    if how == "noargs":
        return ""
    if how == "basename":
        args = (Path(str(args[0])).name,) + tuple(args[1:])
    return repr((tuple(args), sorted(kwargs.items())))


def _resolve(name):
    mod, attr = name.rsplit(".", 1)
    return importlib.import_module(mod), attr


def install(spec):
    """spec = {"pkg.module.fn": (key_rule, "same" | "fresh")}. Record mode (native build) stores every call's
    result; replay mode (browser) answers known calls from _replay.pkl and falls back to the original otherwise."""
    if MODE["replay"] is None and MODE["record"] is None and REPLAY_FILE.exists():
        MODE["replay"] = pickle.loads(REPLAY_FILE.read_bytes())
    for name, (how, share) in spec.items():
        m, attr = _resolve(name)
        orig = getattr(m, attr)
        if getattr(orig, "_webcore", False):
            continue

        def wrap(*a, _o=orig, _n=name, _h=how, _s=share, **kw):
            k = _key(_h, a, kw)
            rec = MODE["record"]
            if rec is not None:
                res = _o(*a, **kw)
                rec.setdefault(_n, {})[k] = pickle.dumps(res, protocol=4)
                return res
            rep = (MODE["replay"] or {}).get(_n, {})
            if k in rep:
                if _s == "same":
                    cache = _SAME.setdefault(_n, {})
                    if k not in cache:
                        cache[k] = pickle.loads(rep[k])
                    return cache[k]
                return pickle.loads(rep[k])
            return _o(*a, **kw)
        wrap._webcore = True
        wrap.__wrapped__ = orig
        setattr(m, attr, wrap)


_SAME = {}


# ------------------------------------------------------------------ responses
def respond(fn, dumps, ApiError, az_exc=None):
    """API-shaped JSON: {"status", "body", "seconds"} — errors as the server sends them ({"error": {...}})."""
    t0 = time.perf_counter()
    try:
        body, st = fn(), 200
    except ApiError as e:
        st = e.status
        body = {"error": {"code": e.code, "message": e.message, "detail": e.detail}, **(getattr(e, "extra", None) or {})}
    except Exception as e:  # noqa: BLE001
        msg = az_exc(e) if az_exc else "%s: %s" % (type(e).__name__, e)
        st, body = 422, {"error": {"code": "engine_error", "message": "Hesablama alınmadı (brauzer): %s" % msg,
                                   "detail": "%s: %s" % (type(e).__name__, str(e)[:500])}}
    return dumps({"status": st, "body": body, "seconds": round(time.perf_counter() - t0, 3)})


# ------------------------------------------------------------------ build-time helpers (native CPython only)
def _load(modname):
    paths(HERE)
    return importlib.import_module(modname)


def record(modname, out):
    MODE["record"] = {}
    w = _load(modname)
    for method, path, body in w.SAMPLES:
        json.loads(w.handle(method, path, json.dumps(body)))
    Path(out).write_bytes(pickle.dumps({k: dict(sorted(v.items())) for k, v in sorted(MODE["record"].items())}, protocol=4))


def trace(modname, replay, out):
    MODE["replay"] = pickle.loads(Path(replay).read_bytes())
    root = HERE.parents[2]
    seen = set()

    def hook(ev, args):
        if ev == "open" and isinstance(args[0], str):
            seen.add(os.path.abspath(args[0]))
    sys.addaudithook(hook)
    w = _load(modname)
    resp = []
    for method, path, body in w.SAMPLES:
        t0 = time.time()
        r = json.loads(w.handle(method, path, json.dumps(body)))
        resp.append({"method": method, "path": path, "request": body, "status": r["status"], "body": r["body"],
                     "native_s": round(time.time() - t0, 3)})
    mods = sorted({os.path.abspath(m.__file__) for m in list(sys.modules.values()) if getattr(m, "__file__", None)})
    rel = lambda p: os.path.relpath(p, root)  # noqa: E731
    keep = lambda p: p.startswith(str(root) + os.sep) and os.path.isfile(p) and "__pycache__" not in p  # noqa: E731
    files = sorted(rel(p) for p in seen if keep(p) and not p.endswith((".py", ".pyc")))
    py = sorted(rel(p) for p in mods if keep(p) and p.endswith(".py"))
    meta = {k: getattr(w, k, None) for k in ("UNIT", "PACKAGES", "INCLUDE", "ROUTES", "NOTES")}
    meta["ENTRY"] = modname
    Path(out).write_text(json.dumps({"files": files, "py": py, "meta": meta, "responses": resp}, ensure_ascii=False,
                                    allow_nan=True, default=str), encoding="utf-8")


if __name__ == "__main__":
    paths(HERE)
    _W = importlib.import_module("webcore")        # the module the web modules import (not __main__)
    if sys.argv[1] == "record":
        _W.record(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "trace":
        _W.trace(sys.argv[2], sys.argv[3], sys.argv[4])
