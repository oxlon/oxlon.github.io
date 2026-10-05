"""pcore.py — the series registry behind the İş paneli bundles.

Every number in the panel passes through `Reg.add()`: the caller hands over values read from
MicroUnit/output; the registry computes growth rates, decimals and the coverage check, and writes
the JS bundles deterministically (sorted keys, fixed rounding).
"""
import json
import math
from pathlib import Path

import pandas as pd

PANEL = Path(__file__).resolve().parent.parent
UNIT = PANEL.parent
OUT = UNIT / "output"
YEARS = [2026, 2027, 2028, 2029, 2030]
SC = {"Baseline": "B", "Adverse": "A", "Reform": "R"}

_cache = {}
USED = set()


def read_retry(path, reader=None, tries=8, wait=4.0, **kw):
    """Read a CSV that a notebook may be rewriting right now: retry on empty/partial/locked files."""
    import time
    reader = reader or pd.read_csv
    for i in range(tries):
        try:
            return reader(path, **kw)
        except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError, OSError, ValueError) as e:
            if i == tries - 1:
                raise
            print(f"  ({Path(path).name} oxunmadı: {type(e).__name__}; {wait:.0f} s sonra yenidən)")
            time.sleep(wait)


def csv(name, **kw):
    key = (name, repr(sorted(kw.items())))
    if key not in _cache:
        _cache[key] = read_retry(OUT / name, **kw)
    USED.add(name)
    return _cache[key].copy()


def fnum(x):
    """Finite float or None, rounded to 8 significant digits (deterministic output)."""
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return float(f"{f:.8g}")


def yv(d, years):
    """Values of a {year: value} mapping (or Series) for the given years."""
    if hasattr(d, "to_dict"):
        d = d.to_dict()
    return [fnum(d.get(y, d.get(str(y)))) for y in years]


def decimals(vals, kind):
    xs = [abs(v) for v in vals if v is not None]
    if not xs:
        return 1
    m = max(xs)
    if kind == "rate":
        return 2 if m < 100 else 1
    return 0 if m >= 1000 else 1 if m >= 10 else 2 if m >= 0.1 else 4


class Reg:
    def __init__(self):
        self.S = []
        self.cov = []
        self.ids = set()
        self.errors = []

    def add(self, fr, grp, ent, unit, sc, var="", hist=None, base=None, band=None, kind="lvl", src="",
            info="", hold=None, note="", expect=("B", "A", "R")):
        """sc: {'Baseline'|'B': list5 or {year: v}}; hist: {year: v}; band: (lo5, hi5) for Baseline levels."""
        s = {}
        for k, vals in sc.items():
            k = SC.get(k, k)
            s[k] = yv(vals, YEARS) if not isinstance(vals, list) else [fnum(x) for x in vals]
        if all(v is None for vals in s.values() for v in vals):
            # the module exports the column but forecasts nothing in it (e.g. no source data): report, don't show
            for k in sorted(s):
                self.cov.append({"fr": fr, "group": grp, "indicator": ent, "variant": var, "scenario": k,
                                 "years_present": 0, "status": "not forecast by module (empty column)", "source": src})
            return None
        h = sorted((int(y), fnum(x)) for y, x in (hist or {}).items() if fnum(x) is not None and int(y) <= 2025)
        b = fnum(base) if base is not None else (h[-1][1] if h and h[-1][0] == 2025 else None)
        rid = f"{fr}|{grp}|{ent}|{var}"
        n = 2
        while rid in self.ids:
            rid = f"{fr}|{grp}|{ent}|{var}#{n}"
            n += 1
        self.ids.add(rid)
        gr = {}
        for k, vals in s.items():
            prev = [b] + vals[:-1]
            if kind == "rate":
                gr[k] = [None if (a is None or p is None) else fnum(a - p) for a, p in zip(vals, prev)]
            else:
                gr[k] = [None if (a is None or p in (None, 0)) else fnum((a / p - 1) * 100) for a, p in zip(vals, prev)]
        allv = [v for vals in s.values() for v in vals]
        rec = {"i": rid, "f": fr, "g": grp, "e": ent, "v": var, "u": unit, "k": kind, "s": s, "gr": gr,
               "d": decimals(allv + [b], kind)}
        if h:
            rec["h"] = h[-26:]
        if b is not None:
            rec["b"] = b
        if band is not None:
            lo, hi = band
            rec["q"] = [[fnum(x) for x in lo], [fnum(x) for x in hi]]
        for key, val in (("src", src), ("m", info), ("o", hold), ("nt", note)):
            if val:
                rec[key] = val
        self.S.append(rec)
        for k in sorted(set(s) | set(expect)):
            vals = s.get(k)
            if vals is None:
                status = "scenario not exported by module" if k in expect and len(s) == 1 else "missing scenario"
                present = 0
            else:
                present = sum(v is not None for v in vals)
                status = "OK" if present == 5 else ("MISSING YEARS" if present else "EMPTY")
            if status in ("MISSING YEARS", "EMPTY", "missing scenario"):
                self.errors.append(f"{rid} [{k}]: {status}")
            self.cov.append({"fr": fr, "group": grp, "indicator": ent, "variant": var, "scenario": k,
                             "years_present": present, "status": status, "source": src})
        return rec

    def write(self, data_dir):
        data_dir.mkdir(parents=True, exist_ok=True)
        frs = sorted({r["f"] for r in self.S}, key=lambda x: int(x[2:]))
        for fr in frs:
            recs = [r for r in self.S if r["f"] == fr]
            js = json.dumps(recs, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            (data_dir / f"{fr.lower()}.js").write_text(
                f"/* generated by build_panel.py from MicroUnit/output — do not edit */\n"
                f"window.MICRO=window.MICRO||{{S:[]}};window.MICRO.S=window.MICRO.S.concat({js});\n", encoding="utf-8")
        pd.DataFrame(self.cov).to_csv(PANEL / "coverage_report.csv", index=False)
        return frs


BUNDLES = {}     # var → object of every bundle written in this build (later builders read earlier bundles)


def js_bundle(path, var, obj):
    BUNDLES[var] = obj
    js = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    path.write_text(f"/* generated by build_panel.py — do not edit */\nwindow.MICRO=window.MICRO||{{S:[]}};"
                    f"window.MICRO.{var}={js};\n", encoding="utf-8")
