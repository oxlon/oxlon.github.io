"""core.py — paths, file access with provenance tracking, Azerbaijani number format.

Every number on the site is read through `csv()` / `raw()` below, which record the file
in the current page's provenance set; the footer stamp is the md5 of exactly those files.
"""
import hashlib
import html
import math
import os
from pathlib import Path

import pandas as pd

SITE = Path(__file__).resolve().parent.parent          # MicroUnit/site
UNIT = SITE.parent                                     # MicroUnit
OUT = UNIT / "output"
DOCS = UNIT / "docs"
DATA = UNIT / "data"
ROOT = UNIT.parent                                     # MIIS_Micro_Risk_Policy

NBSP = " "
MINUS = "−"

_used = set()          # files read for the page being built
_all_used = set()      # files read for the whole site


def reset_used():
    _used.clear()


def used():
    return sorted(_used)


def all_used():
    return sorted(_all_used)


def _mark(p):
    p = Path(p)
    _used.add(str(p))
    _all_used.add(str(p))


_cache = {}


def csv(name, **kw):
    """Read an output CSV (name relative to MicroUnit/output) and record it."""
    p = OUT / name
    _mark(p)
    key = (str(p), repr(sorted(kw.items())))
    if key not in _cache:
        _cache[key] = pd.read_csv(p, **kw)
    return _cache[key].copy()


def raw(path):
    """Read any text file (absolute or relative to MicroUnit) and record it."""
    p = Path(path)
    if not p.is_absolute():
        p = UNIT / p
    _mark(p)
    return p.read_text(encoding="utf-8")


def mark(path):
    p = Path(path)
    if not p.is_absolute():
        p = UNIT / p
    _mark(p)
    return p


def md5_of(paths):
    h = hashlib.md5()
    for p in sorted(paths):
        h.update(Path(p).name.encode())
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    return h.hexdigest()


def build_date():
    """Build date; SOURCE_DATE_EPOCH (if set) pins it for byte-identical rebuilds."""
    import datetime as dt
    sde = os.environ.get("SOURCE_DATE_EPOCH")
    if sde:
        return dt.datetime.utcfromtimestamp(int(sde)).strftime("%Y-%m-%d")
    return dt.date.today().isoformat()


def esc(s):
    if s is None or (isinstance(s, float) and math.isnan(s)):
        return "—"
    return html.escape(str(s), quote=True)


def esc_az(s):
    """esc() of the Azerbaijani text of an output string (module strings_az tables + site table)."""
    from . import v2data
    return esc(v2data.az(s) if isinstance(s, str) else s)


def isnum(x):
    try:
        return x is not None and not (isinstance(x, float) and math.isnan(x)) and not isinstance(x, str)
    except Exception:
        return False


def num(x, d=1, sign=False, pct=False):
    """Azerbaijani number: decimal comma, NBSP thousands, U+2212 minus."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    x = float(x)
    s = f"{abs(x):,.{d}f}"
    s = s.replace(",", "_").replace(".", ",").replace("_", NBSP)
    if round(x, d) < 0:
        s = MINUS + s
    elif sign and round(x, d) > 0:
        s = "+" + s
    if pct:
        s += NBSP + "%"
    return s


def v(x, d=1, sign=False, pct=False):
    """Number wrapped in the macro site's .val span."""
    return f'<span class="val">{num(x, d, sign, pct)}</span>'


def iv(x):
    """Integer with thousands separators."""
    return v(x, 0)


def growth(series):
    """Percent growth of a pandas Series indexed by year."""
    s = series.sort_index()
    return (s / s.shift(1) - 1) * 100


def nrows(name):
    """Data rows of an output CSV (header excluded)."""
    p = OUT / name
    with open(p, "rb") as f:
        n = sum(1 for _ in f)
    return max(n - 1, 0)
