"""Engine `oxlon` — OxLon §15.5.1 FR13 `ministry_spec` (the Ministry's 92-equation catalogue re-solved
by OxLon) for oil / partner / FX channels ONLY. Runs in a subprocess on a COPY
(`PolicyUnit/work/oxlon/{src,data,outputs}` or env POLICY_OXLON_COPY), never inside Macro_OxLon.
Only 16 output series exist (no GDP, unemployment, fiscal) -> partial comparison, tier D."""
from __future__ import annotations

import json
import subprocess
import sys
import time

import pandas as pd

from . import config, registry, scenario as scn
from .engine_base import Result, empty_result, row

ENGINE = "oxlon"
METHOD = "OxLon FR13 (ministry_spec — Nazirliyin tənlik kataloqu)"
MAP = {  # harmonised ids for the comparable OxLon series; all other series -> "oxlon:<code>"
    "cpi_infl": ("infl", "makro"), "wage_nonoil": ("wage_nominal", "əmək"),
    "final_consumption": ("cons_nominal", "makro"), "exp_goods_nonoil": ("exports_nonoil_usd", "xarici"),
    "imp_goods_nonoil": ("imports_nonoil_usd", "xarici"),
}


def _dictionary() -> dict:
    p = config.OXLON_ROOT / "delivery" / "2_neticeler" / "series_dictionary.csv"
    if not p.exists():
        return {}
    d = pd.read_csv(p)
    return {r.series_code: (r.name_az, r.unit) for r in d.itertuples()}


SCRIPT = r'''
import sys, json, pandas as pd
sys.dont_write_bytecode = True
src, out, spec = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
sys.path.insert(0, src)
import ministry_spec as ms
base = ms.forecast_rows(ms.run_scenario())[["series_code", "year", "value"]]
a = pd.read_csv(ms.ASSUMPTIONS)
for key, tr, path in spec:
    for y, v in path.items():
        k = (a.assumption_key == key) & (a.year == int(y))
        a.loc[k, "value"] = a.loc[k, "value"] * (1 + v / 100) if tr == "pct" else a.loc[k, "value"] + v
a.to_csv(out + "_assumptions.csv", index=False)
s = ms.forecast_rows(ms.run_scenario(assumptions_path=out + "_assumptions.csv"))[["series_code", "year", "value"]]
base.merge(s, on=["series_code", "year"], suffixes=("_b", "_s")).to_csv(out + ".csv", index=False)
'''


def unavailable_reason() -> str | None:
    """Azerbaijani reason when the engine is switched off (POLICY_OXLON_DISABLED=1, hosted CI), else None."""
    return config.OXLON_DISABLED_NOTE_AZ if config.OXLON_DISABLED else None


def available() -> bool:
    return not config.OXLON_DISABLED and (config.OXLON_COPY / "src" / "ministry_spec.py").exists()


def run(s: dict, ctx: dict | None = None) -> Result:
    t0 = time.perf_counter()
    spec = []
    for it in s["instruments"]:
        for _, a in registry.adapters_for(ENGINE, it["instrument"]).iterrows():
            name, k = registry.parse_transform(a["transform"])
            yrs = [y for y in it["years"] if y <= 2030]
            spec.append((a["target_key"], name, {str(y): k * float(it["size"]) for y in yrs}))
    if not spec:
        return empty_result(ENGINE, "OxLon yalnız neft/tərəfdaş/məzənnə kanalları üçün istifadə olunur — bu ssenaridə yoxdur")
    if unavailable_reason():
        return empty_result(ENGINE, unavailable_reason())
    if not available():
        return empty_result(ENGINE, f"OxLon nüsxəsi tapılmadı ({config.OXLON_COPY}); `policyunit.eng_oxlon.setup_copy()` ilə yaradın")
    work = config.WORK / "oxlon_runs"
    work.mkdir(parents=True, exist_ok=True)
    out = work / s["id"]
    r = subprocess.run([sys.executable, "-c", SCRIPT, str(config.OXLON_COPY / "src"), str(out), json.dumps(spec)],
                       capture_output=True, text=True, timeout=240, cwd=str(work))
    if r.returncode != 0 or not out.with_suffix(".csv").exists():
        return empty_result(ENGINE, "OxLon alt-prosesi uğursuz oldu: " + (r.stderr or "")[-400:])
    d = pd.read_csv(out.with_suffix(".csv"))
    rows, lab = [], _dictionary()
    d = d[d.year.between(config.FIRST_YEAR, config.LONG_END)]
    for x in d.itertuples():
        ind, grp = MAP.get(x.series_code, (f"oxlon:{x.series_code}", "makro"))
        name, unit = lab.get(x.series_code, (x.series_code, ""))
        rows.append(row(ind, name, str(unit), int(x.year), float(x.value_b), float(x.value_s), METHOD, "D", grp,
                        "OxLon FR13: yalnız 16 sıra; ÜDM/işsizlik/fiskal çıxış yoxdur"))
    meta = {"vintage": {"oxlon_copy": str(config.OXLON_COPY)}, "spec": spec, "warnings": [],
            "runtime_s": round(time.perf_counter() - t0, 2), "assumptions": ["usd_azn fərziyyəsi səviyyə üzrə dəyişdirilib"]}
    return Result(ENGINE, pd.DataFrame(rows), meta)


def setup_copy():
    """rsync Macro_OxLon/model 2/{src,data,outputs} -> PolicyUnit/work/oxlon (read-only source)."""
    src = config.OXLON_ROOT / "model 2"
    config.OXLON_COPY.mkdir(parents=True, exist_ok=True)
    return subprocess.run(["rsync", "-a", "--exclude", "__pycache__"] + [str(src / d) for d in ("src", "data", "outputs")]
                          + [str(config.OXLON_COPY) + "/"], capture_output=True, text=True, timeout=590).returncode
