"""v2data.py — loaders for the v2 module outputs (registry, catalog, tidy forecasts, robustness,
coefficient sensitivity) and the English → Azerbaijani translation table.

Every file goes through core.csv / core.mark, so it is recorded in the page's provenance stamp.
"""
import json
import math
import re
from pathlib import Path

import pandas as pd

from . import core

MODULES = ["FR1", "FR3", "FR4", "FR5", "FR10", "FR12"]
VERDICTS = ["stabil", "qismən stabil", "qeyri-stabil"]
VERDICT_CLS = {"stabil": "done", "qismən stabil": "partial", "qeyri-stabil": "gap"}

_reg = {}


def registry(m):
    """The equation registry output/FRx_equations.json (cached)."""
    p = core.mark(core.OUT / f"{m}_equations.json")
    if m not in _reg:
        _reg[m] = json.loads(p.read_text(encoding="utf-8"))
    return _reg[m]


def equations(m):
    return registry(m)["equations"]


def catalog(m):
    return core.csv(f"{m}_indicator_catalog.csv")


def tidy(m):
    return core.csv(f"{m}_forecast_tidy.csv")


def robustness(m):
    return core.csv(f"{m}_robustness_summary.csv")


def not_forecast(m):
    return core.csv(f"{m}_not_forecast.csv")


# English number format in the modules' prose → Azerbaijani (decimal comma, no-break-space thousands, "−"); the same
# rule as the İş paneli (panel/_build/p_i18n.py az_numbers). Thousands commas only when the string also has an English
# decimal point; dotted codes (05.06.2026, 15.5.2), DSK/NACE table numbers and "9.2-ci hissə" are left alone.
_ENGDEC = re.compile(r"\d\.\d")
_NUMLIST = re.compile(r"([\[(])(\s*-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?)+\s*)([\])])")
_NUM = re.compile(r"((?<![^\s(\[=≈<>:;,/])-)?(?<![\w.,])([1-9]\d{0,2}(?:,\d{3})+(?!\d)|\d+)(\.\d+)?(?!\w|\.\w|,\d)")
_SKB = re.compile(r"(?:DSK|NACE|Part|§|cədvəl\w*|bölmə\w*|hissə\w*)\s*(?:\d+\.\d+\s*[–-]\s*)?$")
_SKA = re.compile(r"-(?:ci|cı|cu|cü)\b|\s*[–-]\s*\d+\.\d+\s*cədvəl|\s*cədvəl")


def az_numbers(s):
    if not isinstance(s, str) or not _ENGDEC.search(s):
        return s
    s = _NUMLIST.sub(lambda m: m.group(1) + re.sub(r"\s*,\s*", "; ", m.group(2)) + m.group(3) if "." in m.group(2) else m.group(0), s)

    def fix(m):
        sign, ip, dp = m.group(1) or "", m.group(2), m.group(3) or ""
        if not dp and "," not in ip:
            return m.group(0)
        if _SKB.search(m.string[max(0, m.start() - 16):m.start()]) or _SKA.match(m.string, m.end()):
            return m.group(0)
        return ("−" if sign else "") + ip.replace(",", "\u00a0") + ("," + dp[1:] if dp else "")
    return _NUM.sub(fix, s)


def fix_az(s):
    """Repair the 'i̇' that Python's lower() makes of 'İ' (combining dot above); Azerbaijani number format."""
    return az_numbers(s.replace("i̇", "i")) if isinstance(s, str) else s


# ------------------------------------------------------------ translation table
_az = None
_long = None


def _load_az():
    from . import az_extra
    t = {}
    for m in MODULES:
        p = core.OUT / f"{m}_strings_az.csv"
        if not p.exists():
            continue
        d = core.csv(p.name)
        for en, a in zip(d["en"], d["az"]):
            if isinstance(en, str) and isinstance(a, str) and a.strip():
                t.setdefault(en.strip(), a.strip())
    t.update(az_extra.FULL)
    return t


def _frag(s):
    from . import az_extra
    for en, a in az_extra.FRAG:
        if en in s:
            s = s.replace(en, a)
    return s


def az(s):
    """Azerbaijani text for an output string: whole-string tables first, then fragment replacements."""
    global _az
    if _az is None:
        _az = _load_az()
    if not isinstance(s, str):
        return s
    k = s.strip()
    if k in _az:
        return fix_az(_frag(_az[k]))
    if k.startswith(("ValueError", "LinAlgError", "TypeError")) or "Error:" in k[:40]:
        test = ("RESET" if "RESET" in k else "White" if "White" in k else "Breusch–Pagan" if "Breusch" in k else "")
        return (f"{test} testi " if test else "Test ") + "tətbiq olunmur: izahedici dəyişənlər kifayət deyil (yalnız sabit)"
    return fix_az(_frag(s))


def az_long(s):
    """Fragment-translate a long text (regression summary): every multi-word strings_az pair, then FRAG."""
    global _long, _az
    if _az is None:
        _az = _load_az()
    if _long is None:
        _long = sorted(((en, a) for en, a in _az.items() if " " in en and len(en) >= 12 and en != a),
                       key=lambda x: -len(x[0]))
    if not s:
        return ""
    for en, a in _long:
        if en in s:
            s = s.replace(en, a)
    return fix_az(_frag(s))


def codes():
    """Variable codes of every registry (coefficient names, dependent codes) — identifiers, not prose."""
    out = set()
    for m in MODULES:
        for e in equations(m):
            for c in e.get("coefficients") or []:
                out.add(str(c.get("name")))
            out.add(str((e.get("dependent") or {}).get("code")))
    return {c for c in out if c.isascii() and c.isalpha()}


# ------------------------------------------------------------ documents
def doc_az(code):
    """Relative path (to MicroUnit) of the Azerbaijani methodology doc in docs/az/, or None."""
    d = core.DOCS / "az"
    if not d.is_dir():
        return None
    hits = sorted(p for p in d.glob(f"{code}_*.md")) + sorted(p for p in d.glob(f"{code}.md"))
    if not hits:
        return None
    core.mark(hits[0])
    return str(hits[0].relative_to(core.UNIT))


# ------------------------------------------------------------ formatting helpers
def isnum(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and not math.isnan(float(x)) \
        and not math.isinf(float(x))


def pval(p):
    if not isnum(p):
        return "—"
    if p < 0.001:
        return "&lt;" + core.NBSP + "0,001"
    return core.num(p, 3)


def stat(x, d=3):
    return core.num(x, d) if isnum(x) else "—"


def decimals(vals):
    """Display decimals for a series, from the median magnitude of its values."""
    a = sorted(abs(float(v)) for v in vals if isnum(v))
    if not a:
        return 1
    m = a[len(a) // 2]
    return 0 if m >= 1000 else 1 if m >= 10 else 2 if m >= 0.1 else 3


# ------------------------------------------------------------ coefficient sensitivity, one shape
_SENS = {  # module: (eq, coefficient label, component id, component label, low %, high %)
    "FR1": ("eq_id", "label_az", "component_id", "component_label_az", "effect_minus_se_pct", "effect_plus_se_pct"),
    "FR3": ("eq_id", "label_az", "component_id", "component_label_az", "effect_minus_se_pct", "effect_plus_se_pct"),
    "FR5": ("eq_id", "label_az", "component_id", "component_label_az", "effect_minus_se_pct", "effect_plus_se_pct"),
    "FR4": ("eq_id", "label_az", "headline", "headline_label_az", "effect_minus_pct", "effect_plus_pct"),
    "FR10": ("input", "label_az", "component", "component_az", "effect_low_pct", "effect_high_pct"),
    "FR12": ("eq_id", "label_az", "headline", "headline_az", "effect_minus_1se_pct", "effect_plus_1se_pct"),
}


def sensitivity(m):
    """DataFrame eq, coef, comp, comp_label, lo, hi, swing — effect on the 2030 level, % of baseline."""
    d = core.csv(f"{m}_coef_sensitivity.csv")
    e, lab, c, cl, lo, hi = _SENS[m]
    out = pd.DataFrame({"eq": d[e].astype(str), "coef": d[lab].astype(str), "comp": d[c].astype(str),
                        "comp_label": d[cl].astype(str), "lo": d[lo].astype(float), "hi": d[hi].astype(float)})
    if m == "FR10":
        out["eq"] = out["eq"].str.split("|").str[0]
        out["kind"] = d["type_az"].astype(str)
    else:
        out["kind"] = "əmsal (±1 standart xəta)"
    out["swing"] = (out["hi"] - out["lo"]).abs()
    return out


def verdict_of(e):
    return (e.get("robustness") or {}).get("verdict") or "—"
