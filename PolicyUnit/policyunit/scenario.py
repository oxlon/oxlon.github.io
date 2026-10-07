"""Policy scenarios: load / validate (Azerbaijani errors) / expand instrument paths.

CLI: python3 -m policyunit.scenario config/scenarios/<id>.json   (exit 1 on errors)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from . import config, registry

FINANCING = (None, "deficit", "sofaz", "tax", "reallocation")
FR12_MARKETS = ("AGR", "IND", "CON", "TRD", "TRA", "ACC", "ICT", "REA", "EDU", "HEA", "OTH",
                "MOB", "BNK", "CEM")
REQUIRED = ("id", "name_az", "start_year", "instruments")


class ScenarioError(ValueError):
    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("Ssenari yoxlanışı uğursuz oldu:\n- " + "\n- ".join(self.errors))


def validate(s: dict, source: str = "") -> list[str]:
    """Return a list of Azerbaijani error messages (empty = valid)."""
    e = []
    if not isinstance(s, dict):
        return ["ssenari JSON obyekti olmalıdır ({...})"]
    for k in REQUIRED:
        if k not in s:
            e.append(f"məcburi sahə '{k}' yoxdur")
    if e:
        return e
    if not re.fullmatch(r"[a-z0-9_]+", str(s["id"])):
        e.append(f"id '{s['id']}' yalnız kiçik latın hərfləri, rəqəmlər və '_' ola bilər")
    if source and Path(source).stem != s["id"]:
        e.append(f"fayl adı ({Path(source).stem}) id ilə ({s['id']}) eyni olmalıdır")
    sy = s["start_year"]
    if not isinstance(sy, int) or not (config.FIRST_YEAR <= sy <= config.MICRO_YEARS[-1]):
        e.append(f"start_year {sy}: {config.FIRST_YEAR}–{config.MICRO_YEARS[-1]} arasında tam ədəd olmalıdır")
        sy = config.FIRST_YEAR
    ins = s["instruments"]
    if not isinstance(ins, list) or not ins:
        return e + ["instruments boş olmayan siyahı olmalıdır"]
    cat = registry.instruments()
    for i, it in enumerate(ins, 1):
        p = f"alət #{i}"
        if not isinstance(it, dict) or "instrument" not in it:
            e.append(f"{p}: 'instrument' sahəsi yoxdur")
            continue
        iid = it["instrument"]
        p = f"alət #{i} ({iid})"
        if iid not in cat.index:
            e.append(f"{p}: kataloqda belə alət yoxdur (config/instruments.csv)")
            continue
        r = cat.loc[iid]
        unit = it.get("unit", r["unit"])
        if unit != r["unit"]:
            e.append(f"{p}: vahid '{unit}' yanlışdır — bu alət üçün '{r['unit']}' olmalıdır")
        size = it.get("size")
        if isinstance(size, bool) or not isinstance(size, (int, float)):
            e.append(f"{p}: 'size' ədəd olmalıdır")
        elif not (r["min"] <= size <= r["max"]):
            e.append(f"{p}: ölçü {size} icazə verilən [{r['min']:g}, {r['max']:g}] intervalından kənardır")
        yrs = it.get("years", "all")
        if yrs != "all":
            if not isinstance(yrs, list) or not yrs or not all(isinstance(y, int) for y in yrs):
                e.append(f"{p}: 'years' illərin siyahısı və ya \"all\" olmalıdır")
            elif min(yrs) < sy or max(yrs) > config.LONG_END:
                e.append(f"{p}: illər {sy}–{config.LONG_END} arasında olmalıdır")
        fin = it.get("financing")
        if fin not in FINANCING:
            e.append(f"{p}: maliyyələşmə '{fin}' yanlışdır (deficit, sofaz, tax, reallocation və ya null)")
        if iid == "market_entry" and it.get("target") not in FR12_MARKETS:
            e.append(f"{p}: 'target' FR12 bazar kodu olmalıdır ({', '.join(FR12_MARKETS)})")
    return e


def load(path_or_id) -> dict:
    p = Path(path_or_id)
    if not p.suffix:
        p = config.SCENARIOS / f"{path_or_id}.json"
    if not p.exists():
        raise ScenarioError([f"ssenari faylı tapılmadı: {p}"])
    try:
        s = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise ScenarioError([f"{p.name}: JSON sintaksis xətası (sətir {err.lineno}, sütun {err.colno}): {err.msg}"])
    errs = validate(s, str(p))
    if errs:
        raise ScenarioError(errs)
    return normalise(s)


def normalise(s: dict) -> dict:
    s = dict(s)
    s.setdefault("description_az", "")
    s.setdefault("tags", [])
    out = []
    for it in s["instruments"]:
        r = registry.instrument(it["instrument"])
        it = dict(it)
        it.setdefault("unit", r["unit"])
        it.setdefault("target", None)
        it.setdefault("financing", None)
        yrs = it.get("years", "all")
        it["years"] = list(range(s["start_year"], config.LONG_END + 1)) if yrs == "all" else sorted(yrs)
        out.append(it)
    s["instruments"] = out
    return s


def all_ids() -> list[str]:
    return sorted(p.stem for p in config.SCENARIOS.glob("*.json"))


def load_all() -> list[dict]:
    return [load(i) for i in all_ids()]


def path(it: dict, years) -> list[float]:
    """Instrument size per year (0 where inactive)."""
    return [float(it["size"]) if y in it["years"] else 0.0 for y in years]


def active_after(it: dict, year: int) -> bool:
    return any(y > year for y in it["years"])


def main(argv=None):
    argv = argv or sys.argv[1:]
    bad = 0
    for a in argv or [str(p) for p in config.SCENARIOS.glob("*.json")]:
        try:
            s = load(a)
            print(f"OK  {s['id']}: {s['name_az']} ({len(s['instruments'])} alət)")
        except ScenarioError as err:
            bad += 1
            print(f"XƏTA {a}:\n{err}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
