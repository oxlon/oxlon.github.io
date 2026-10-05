"""Shared helpers for the v2.2 documentation refresh (marker blocks, paths, number formatting).

Every generated passage lives between a marker pair in the same style as the notebooks' own AUTO blocks:

    block style (tables, paragraphs, notes)      inline style (a fragment inside hand-written prose)
    <!-- AUTO:v22_name -->                         ... text <!-- AUTO:v22_name -->generated<!-- /AUTO:v22_name --> text ...
    generated text
    <!-- /AUTO:v22_name -->

The content between the markers is regenerated on every run.  The first run (no markers yet) is a one-off migration:
the generated text must already be present verbatim in the document (it was written there on 2026-10-05), and it is
then wrapped; if it is not found the refresh fails instead of guessing, so the document is never silently changed.
"""
import json
import os
import re
from pathlib import Path

import pandas as pd

PKG = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("MICROUNIT_ROOT", PKG.parents[1]))
OUT = ROOT / "output"
DATA = ROOT / "data"
DOCS = ROOT / "docs"
MINUS = "−"


class RefreshError(RuntimeError):
    pass


# ------------------------------------------------------------------ inputs
def ref(module):
    """Frozen reference values of the 2026-10-05 v2.1 -> v2.2 change (v22_reference.json)."""
    with open(PKG / "v22_reference.json", encoding="utf-8") as f:
        return json.load(f)[module]


def csv(name, **kw):
    p = OUT / name
    if not p.exists():
        raise RefreshError(f"missing output file output/{name}")
    return pd.read_csv(p, **kw)


def registry(module):
    with open(OUT / f"{module}_equations.json", encoding="utf-8") as f:
        J = json.load(f)
    return {e["id"]: e for e in J["equations"]}, J


def nb_counts(module):
    with open(ROOT / f"{module}.ipynb", encoding="utf-8") as f:
        c = json.load(f)["cells"]
    return len(c), sum(x["cell_type"] == "code" for x in c)


# ------------------------------------------------------------------ number formatting
def num(v, d=1):
    """plain number, Unicode minus"""
    return f"{v:.{d}f}".replace("-", MINUS)


def pm(v, d=2):
    """signed number, Unicode minus"""
    return f"{v:+.{d}f}".replace("-", MINUS)


def az(v, d=2):
    """Azerbaijani prose number: decimal comma, space as thousands separator"""
    return f"{v:,.{d}f}".replace(",", " ").replace(".", ",")


def azm(v, d=2):
    """Azerbaijani prose number with Unicode minus"""
    return az(v, d).replace("-", MINUS)


def azpm(v, d=2):
    """signed Azerbaijani prose number (decimal comma, Unicode minus)"""
    return pm(v, d).replace(".", ",")


# Azerbaijani case suffixes after a bare integer follow the last spoken word (14 = on dörd -> 14-ü, 14-dən)
_POSS_UNIT = {1: "i", 2: "si", 3: "ü", 4: "ü", 5: "i", 6: "sı", 7: "si", 8: "i", 9: "u"}
_POSS_TENS = {0: "ı", 10: "u", 20: "si", 30: "u", 40: "ı", 50: "si", 60: "ı", 70: "i", 80: "i", 90: "ı"}
_ABL_UNIT = {1: "dən", 2: "dən", 3: "dən", 4: "dən", 5: "dən", 6: "dan", 7: "dən", 8: "dən", 9: "dan"}
_ABL_TENS = {0: "dan", 10: "dan", 20: "dən", 30: "dan", 40: "dan", 50: "dən", 60: "dan", 70: "dən", 80: "dən", 90: "dan"}


def az_poss(n):
    """'6-sı', '12-si', '14-ü' (3rd-person possessive after an integer < 100)"""
    n = int(n)
    return f"{n}-{_POSS_UNIT[n % 10] if n % 10 else _POSS_TENS[n % 100]}"


def az_abl(n):
    """'14-dən', '16-dan' (ablative after an integer < 100)"""
    n = int(n)
    return f"{n}-{_ABL_UNIT[n % 10] if n % 10 else _ABL_TENS[n % 100]}"


def plan_fmt(v, d=1):
    """growth rate for a list: signed, but an exact zero (at the shown precision) as '0.0'"""
    return f"{0:.{d}f}" if round(v, d) == 0 else pm(v, d)


# ------------------------------------------------------------------ marker blocks
def _open(tag):
    return f"<!-- AUTO:{tag} -->"


def _close(tag):
    return f"<!-- /AUTO:{tag} -->"


class Doc:
    """One Markdown document; put() regenerates (or, on the first run, wraps) one marker block."""

    def __init__(self, path):
        self.path = Path(path)
        self.rel = self.path.relative_to(ROOT).as_posix()
        self.text = self.path.read_text(encoding="utf-8")
        self.orig = self.text
        self.tags = []

    def put(self, tag, body, inline=False, legacy=None):
        """legacy: (old_open, old_close) markers that are renamed to this tag's markers (one-off migration)."""
        o, c = _open(tag), _close(tag)
        t = self.text
        if legacy and legacy[0] in t and o not in t:
            if t.count(legacy[0]) != 1 or t.count(legacy[1]) != 1:
                raise RefreshError(f"{self.rel}: legacy markers {legacy} not unique")
            t = t.replace(legacy[0], o).replace(legacy[1], c)
        if o in t:
            if t.count(o) != 1 or t.count(c) != 1:
                raise RefreshError(f"{self.rel}: AUTO:{tag} has {t.count(o)} opening and {t.count(c)} closing markers "
                                   f"(expected one of each)")
            i, j = t.index(o) + len(o), t.index(c)
            if j < i:
                raise RefreshError(f"{self.rel}: marker {tag} closes before it opens")
            new = body if inline else "\n" + body + "\n"
            t = t[:i] + new + t[j:]
        else:                                       # first run: wrap the passage written on 2026-10-05
            n = t.count(body)
            if n != 1:
                raise RefreshError(f"{self.rel}: AUTO:{tag} markers missing and the passage was found {n} times "
                                   f"(expected exactly once) — start: {body[:90]!r}")
            k = t.index(body)
            if inline:
                t = t[:k] + o + body + c + t[k + len(body):]
            else:
                if not (k == 0 or t[k - 1] == "\n") or not t[k + len(body):k + len(body) + 1] in ("\n", ""):
                    raise RefreshError(f"{self.rel}: AUTO:{tag} block passage does not start/end on a line boundary")
                t = t[:k] + o + "\n" + body + "\n" + c + t[k + len(body):]
        self.text = t
        self.tags.append(tag)

    def check_wildcard(self, tags):
        """FR4.ipynb rewrites its English blocks with `<!-- AUTO:<tag>[^>]*-->(.*?)<!-- /AUTO:<tag> -->`; make sure
        no generated marker can be captured by that pattern for any of the given notebook tags."""
        for tg in tags:
            m = re.search(r"<!-- AUTO:" + re.escape(tg) + r"[^>]*-->", self.text)
            if m and not re.match(r"<!-- AUTO:" + re.escape(tg) + r"(\s[^>]*)?-->", m.group(0)):
                raise RefreshError(f"{self.rel}: marker {m.group(0)} would be captured by the notebook's AUTO:{tg}")

    def save(self):
        changed = self.text != self.orig
        if changed:
            self.path.write_text(self.text, encoding="utf-8")
        return changed


def run(module, docs):
    """docs: list of (Doc, fill function).  All documents are generated first and written only if all succeed."""
    for d, fill in docs:
        fill(d)
    msgs = []
    for d, _ in docs:
        ch = d.save()
        msgs.append(f"{d.rel}: {len(d.tags)} v2.2 blocks {'updated' if ch else 'unchanged'}")
    print(f"docrefresh {module}: " + "; ".join(msgs))
