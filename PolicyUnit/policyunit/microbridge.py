"""Bridge to the MicroUnit scenario engines (read-only import from MicroUnit on sys.path; never
writes into MicroUnit). Re-implements `chain.run_chain` so that an FR1 *overlay* (documented proxy
for instruments without an FR1 channel) can be applied between FR1 and the downstream modules.
Override warnings of MicroUnit (unknown id, ignored, clipped) are raised as errors."""
from __future__ import annotations

import copy
import json
import sys
import time
from functools import lru_cache

from . import config

OVERRIDE_WARN = ("naməlum", "nəzərə alınmadı", "kəsildi", "yanlış dəyər", "gözlənilirdi",
                 "redaktə edilə bilməz")


class MicroOverrideError(RuntimeError):
    pass


def _path():
    p = str(config.MICRO_ROOT)
    if p not in sys.path:
        sys.path.insert(0, p)


def chain():
    _path()
    from microlib.engines import chain as ch
    return ch


@lru_cache(maxsize=8)
def catalogue(module: str = "FR1") -> dict:
    return chain().load_engine(module).inputs()


def coef(key: str) -> float:
    for c in catalogue("FR1")["coefficients"]:
        if f"{c['eq_id']}|{c['name']}" == key:
            return float(c["value"])
    raise KeyError(key)


def exo_baseline(eid: str, module: str = "FR1", scenario: str = "Baseline") -> list[float]:
    for e in catalogue(module)["exogenous"]:
        if e["id"] == eid:
            return [float(v) for v in e["baseline"].get(scenario, e["baseline"]["Baseline"])]
    raise KeyError(eid)


def override_errors(warnings) -> list[str]:
    return [w for w in warnings if any(t in w for t in OVERRIDE_WARN)]


def run(overrides: dict | None = None, overlay=None, scenario: str = "Baseline") -> dict:
    """overrides = {"FR1": {...}, "FR3": {...}}; overlay(fr1_result) -> modified copy (or None)."""
    ch = chain()
    ov = overrides or {}
    out = {"results": {}, "warnings": [], "timing": {}, "errors": {}}
    for m in [k for k in ov if k not in ch.ORDER]:
        raise MicroOverrideError(f"naməlum MikroUnit modulu '{m}'")
    for m in ch.ORDER:
        eng = ch.load_engine(m)
        if eng is None:
            out["warnings"].append(f"{m}: mühərrik yoxdur — buraxıldı")
            continue
        up = {u: out["results"][u] for u in ch.UPSTREAM[m] if u in out["results"]}
        t0 = time.perf_counter()
        try:
            res = eng.run(ov.get(m, {}), scenario=scenario, upstream=up or None)
        except Exception as e:  # noqa: BLE001
            out["errors"][m] = f"{type(e).__name__}: {e}"
            continue
        out["timing"][m] = round(time.perf_counter() - t0, 3)
        if m == "FR1" and overlay is not None:
            res = overlay(copy.deepcopy(res)) or res
        out["results"][m] = res
        out["warnings"].extend(f"{m}: {w}" for w in res.get("warnings", []))
    bad = override_errors(out["warnings"])
    if bad:
        raise MicroOverrideError("MikroUnit override xəbərdarlıqları xəta sayılır:\n- " + "\n- ".join(bad))
    if out["errors"]:
        raise MicroOverrideError("MikroUnit mühərrik xətası: " + json.dumps(out["errors"], ensure_ascii=False))
    return out


_BASE = {}


def baseline(levers: dict | None = None, scenario: str = "Baseline") -> dict:
    """Baseline chain with the scenario's structural levers (same vintage, exogenous at baseline)."""
    key = json.dumps({"l": levers or {}, "s": scenario}, sort_keys=True)
    if key not in _BASE:
        ov = {m: {"levers": lv} for m, lv in (levers or {}).items() if lv}
        _BASE[key] = run(ov, scenario=scenario)
    return _BASE[key]


def series(res: dict, module: str, sid: str) -> list[float] | None:
    s = res["results"].get(module, {}).get("series", {}).get(sid)
    if s is None:
        return None
    return [float(s.get(str(y), float("nan"))) for y in config.MICRO_YEARS]


def vintage() -> dict:
    """MicroUnit vintage id: md5 of the FR1 equation registry + FR1 forecast (content hashes)."""
    import hashlib
    h = hashlib.md5()
    for name in ("FR1_equations.json", "FR1_forecast_full.csv", "FR1_multipliers.csv"):
        p = config.MICRO_ROOT / "output" / name
        if p.exists():
            h.update(name.encode())
            h.update(p.read_bytes())
    return {"micro_vintage": h.hexdigest()[:12]}
