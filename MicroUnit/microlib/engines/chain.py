"""Chained scenarios: FR1 -> FR3 -> FR4 -> FR5 and FR1 -> FR10 -> FR12 (contract section B).
Each engine receives `upstream` = {module: result} of the modules it depends on that ran successfully.
Engines not yet written are skipped with a warning."""
from __future__ import annotations

import importlib
import time
import traceback

ORDER = ["FR1", "FR3", "FR4", "FR5", "FR10", "FR12"]
UPSTREAM = {"FR1": [], "FR3": ["FR1"], "FR4": ["FR1", "FR3"], "FR5": ["FR1"],
            "FR10": ["FR1", "FR3", "FR4"], "FR12": ["FR1", "FR10"]}


def load_engine(module):
    """Import microlib.engines.frX; returns the module or None if it does not exist yet."""
    name = f"microlib.engines.{module.lower()}"
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as e:
        if e.name == name:
            return None
        raise


def available_engines():
    return [m for m in ORDER if load_engine(m) is not None]


def run_chain(overrides_by_module=None, scenario="Baseline", modules=None, stop_on_error=False):
    """overrides_by_module = {"FR1": {"exogenous": {...}, "coefficients": {...}, "levers": {...}}, ...}.
    Returns {"scenario", "results": {module: result}, "order", "skipped", "errors", "warnings", "timing"}."""
    ov = overrides_by_module or {}
    mods = [m for m in ORDER if modules is None or m in modules]
    out = {"scenario": scenario, "results": {}, "order": [], "skipped": [], "errors": {}, "warnings": [],
           "timing": {}}
    for m in [k for k in ov if k not in ORDER]:
        out["warnings"].append(f"naməlum modul '{m}' üçün override nəzərə alınmadı")
    for m in mods:
        eng = None
        try:
            eng = load_engine(m)
        except Exception as e:  # noqa: BLE001  (engine exists but fails to import)
            out["errors"][m] = f"import: {type(e).__name__}: {e}"
        if eng is None:
            if m not in out["errors"]:
                out["skipped"].append(m)
                out["warnings"].append(f"{m}: mühərrik (engines/{m.lower()}.py) hələ yoxdur — buraxıldı")
            continue
        missing = [u for u in UPSTREAM[m] if u not in out["results"]]
        if missing:
            out["warnings"].append(f"{m}: yuxarı axın nəticəsi yoxdur ({', '.join(missing)}) — baza dəyərləri istifadə olunur")
        upstream = {u: out["results"][u] for u in UPSTREAM[m] if u in out["results"]}
        t0 = time.perf_counter()
        try:
            res = eng.run(ov.get(m, {}), scenario=scenario, upstream=upstream or None)
        except Exception as e:  # noqa: BLE001
            out["errors"][m] = f"{type(e).__name__}: {e}"
            out["errors"][m + "_trace"] = traceback.format_exc(limit=3)
            if stop_on_error:
                break
            continue
        out["timing"][m] = round(time.perf_counter() - t0, 3)
        out["results"][m] = res
        out["order"].append(m)
        out["warnings"].extend(f"{m}: {w}" for w in res.get("warnings", []))
    return out
