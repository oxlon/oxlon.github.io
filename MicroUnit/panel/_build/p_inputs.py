"""p_inputs.py — scenario-builder bundles.

data/inputs.js  editable inputs of every engine (microlib.engines.<frx>.inputs()): exogenous paths 2026–2030 per
                scenario, coefficients (estimate, SE, 95 % CI, editable), levers. Lets the builder render offline.
data/saved.js   saved custom scenarios exported into the bundle (api/micro.db table scenario_saved, read-only,
                and panel/scenarios/*.json), so their results can be viewed from file:// without the server.
"""
import json
import os
import sqlite3
import sys

from . import pcore as C

MODS = ["FR1", "FR3", "FR4", "FR5", "FR10", "FR12"]
KEEP = 30


def _plain(o):
    try:
        return o.tolist()
    except AttributeError:
        return str(o)


def inputs(tr):
    sys.path.insert(0, str(C.UNIT))
    out, errs = {}, {}
    for m in MODS:
        try:
            mod = __import__(f"microlib.engines.{m.lower()}", fromlist=["inputs"])
            raw = json.loads(json.dumps(mod.inputs(), default=_plain, allow_nan=True).replace("NaN", "null"))
            out[m] = tr.deep(raw, skip=("id", "eq_id", "name", "options", "value", "baseline", "years", "default",
                                                  "rule_key", "part", "tied_with", "source", "type", "kind"))
        except Exception as e:                                  # engine missing: builder shows the reason
            errs[m] = f"{type(e).__name__}: {e}"
    return out, errs


def _compact(result):
    """chain result → {id: [2025?, 2026..2030]} rounded; keeps per-module warnings."""
    res = (result or {}).get("result", result) or {}
    out, warn = {}, {}
    if res and "results" not in res and all(isinstance(v, list) for v in res.values()):   # already compact (panel export)
        return {k: [C.fnum(x) for x in v] for k, v in res.items()}, {}
    for m, r in (res.get("results") or {}).items():
        for cid, ser in (r.get("series") or {}).items():
            out[cid] = [C.fnum(ser.get(str(y), ser.get(y))) for y in [2025] + C.YEARS]
        if r.get("warnings"):
            warn[m] = r["warnings"][:20]
    return out, warn


def saved(db=None):
    rows = []
    db = db or os.environ.get("MIKRO_DB") or str(C.UNIT / "api" / "micro.db")
    if os.path.exists(db):
        try:
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            con.row_factory = sqlite3.Row
            for r in con.execute("SELECT * FROM scenario_saved ORDER BY updated_at DESC LIMIT ?", (KEEP,)):
                rows.append(dict(r))
            con.close()
        except sqlite3.Error as e:
            print(f"  (saxlanmış ssenarilər oxunmadı: {e})")
    for p in sorted((C.PANEL / "scenarios").glob("*.json")) if (C.PANEL / "scenarios").exists() else []:
        try:
            rows.append(json.loads(p.read_text(encoding="utf-8")) | {"file": p.name})
        except (ValueError, OSError) as e:
            print(f"  ({p.name} oxunmadı: {e})")
    out = []
    for r in rows:
        ov = r.get("overrides")
        res = r.get("result")
        ov = json.loads(ov) if isinstance(ov, str) else ov
        res = json.loads(res) if isinstance(res, str) else res
        series, warn = _compact(res)
        out.append({"id": r.get("id") or r.get("file"), "name": r.get("name"), "author": r.get("author"),
                    "scenario": r.get("scenario") or "Baseline", "note": r.get("note"), "created": r.get("created_at"),
                    "updated": r.get("updated_at"), "overrides": ov or {}, "series": series, "warn": warn,
                    "src": "fayl" if r.get("file") else "server"})
    return out


def build(data_dir, tr, db=None):
    inp, errs = inputs(tr)
    C.js_bundle(data_dir / "inputs.js", "INP", {"inputs": inp, "errors": errs})
    sv = saved(db)
    C.js_bundle(data_dir / "saved.js", "SAVED", sv)
    return inp, errs, sv
