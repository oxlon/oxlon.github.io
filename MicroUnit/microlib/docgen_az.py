"""docgen_az — keeps the Azerbaijani methodology documents (docs/az/FRx_Metodologiya.md) in sync with every run.

Each module notebook's documentation step first regenerates the `<!-- AUTO:name -->…<!-- /AUTO:name -->` blocks of the
English document (docs/FRx_Methodology.md) and then calls one function here, which writes the SAME blocks into the
Azerbaijani document with Azerbaijani wording and the same numbers:

    from microlib import docgen_az
    docgen_az.fr4_results(globals())     # FR4 Part 20.2   (AUTO:e2gap, AUTO:results)
    docgen_az.fr4_v2(globals())          # FR4 Part 26     (AUTO:v2, AUTO:cells)
    docgen_az.fr5_blocks(globals())      # FR5 Part 18     (16 AUTO blocks)
    docgen_az.copy_v2('FR3') / copy_v2('FR5')   # v2 blocks, already Azerbaijani in the English document

Number convention (stated at the top of each Azerbaijani document): decimal comma and space thousands separator in prose;
tables, formulas, code and file names keep the numerals exactly as produced by the code.
Blocks whose wording is already Azerbaijani in the English document are copied and only their prose numbers converted
(`az_prose`). Labels inside generated tables are translated with the module's own `output/FRx_strings_az.csv` plus the
small dictionary `LOCAL` below; anything still untranslated is listed in `UNTRANSLATED` (checked by the QA script).
Only the standard library and pandas are used. Nothing here changes any model output.
"""
import os
import re

from . import project_root

AZ_NAMES = {m: f"{m}_Metodologiya.md" for m in ("FR1", "FR3", "FR4", "FR5")}
UNTRANSLATED = set()
_MARK = r"(<!-- AUTO:{tag}(?:\s[^>]*)?-->)(.*?)(<!-- /AUTO:{tag} -->)"
_SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


# ------------------------------------------------------------------ paths and markers
def az_path(module):
    return os.path.join(project_root(), "docs", "az", AZ_NAMES[module])


def en_path(module):
    return os.path.join(project_root(), "docs", f"{module}_Methodology.md")


def get_block(text, tag):
    m = re.search(_MARK.format(tag=re.escape(tag)), text, re.S)
    assert m, f"AUTO:{tag} marker missing"
    return m.group(2)


def put(text, tag, new):
    pat = re.compile(_MARK.format(tag=re.escape(tag)), re.S)
    assert pat.search(text), f"AUTO:{tag} marker missing in the Azerbaijani document"
    return pat.sub(lambda m: m.group(1) + new + m.group(3), text)


def write_blocks(module, blocks):
    """blocks: {tag: text}; text is inserted verbatim between the markers of docs/az/<module>_Metodologiya.md."""
    p = az_path(module)
    with open(p, encoding="utf-8") as f:
        t = f.read()
    for tag, new in blocks.items():
        t = put(t, tag, new)
    with open(p, "w", encoding="utf-8") as f:
        f.write(t)
    print(f"docs/az/{AZ_NAMES[module]}: {len(blocks)} AUTO blocks written in Azerbaijani: {sorted(blocks)}")
    return t


# ------------------------------------------------------------------ number formatting (prose)
def num(x, d=2, sign=False, thou=True):
    """Azerbaijani prose number: decimal comma, space as thousands separator; e.g. num(5105.3, 1) -> '5 105,3'."""
    s = f"{float(x):{'+' if sign else ''}{',' if thou else ''}.{d}f}"
    return s.replace(",", " ").replace(".", ",")


def num_t(x, d=1, sign=False):
    """Table number: decimal point kept (as in the code output), space as thousands separator: '+1 049.3'."""
    return f"{float(x):{'+' if sign else ''},.{d}f}".replace(",", " ")


def pct(x, d=2, sign=True):
    return num(x, d, sign=sign, thou=False) + "%"


def sci(x, d=1):
    """7.4e-14 -> '7,4·10⁻¹⁴'"""
    m, e = f"{float(x):.{d}e}".split("e")
    return f"{m.replace('.', ',')}·10{str(int(e)).translate(_SUP)}"


_UNITS = ["", "bir", "iki", "üç", "dörd", "beş", "altı", "yeddi", "səkkiz", "doqquz"]
_TENS = ["", "on", "iyirmi", "otuz", "qırx", "əlli", "altmış", "yetmiş", "səksən", "doxsan"]


def _last_vowel(n):
    n = abs(int(n))
    w = (_UNITS[n % 10] if n % 10 else _TENS[(n // 10) % 10] if n % 100 else "yüz" if n % 1000 else "min") if n else "sıfır"
    return [c for c in w if c in "aıoueəiöü"][-1]


def ordsuf(n):
    """Azerbaijani ordinal suffix for a number written in digits: 2025 -> 'ci', 2026 -> 'cı', 2030 -> 'cu', 2024 -> 'cü'."""
    v = _last_vowel(n)
    return {"a": "cı", "ı": "cı", "o": "cu", "u": "cu", "ö": "cü", "ü": "cü"}.get(v, "ci")


def locsuf(n):
    """Locative suffix: 2026 -> 'da', 2025 -> 'də'."""
    return "da" if _last_vowel(n) in "aıou" else "də"


_CODE = re.compile(r"(`[^`]*`|\$[^$]*\$|\[[^\]]*\]\([^)]*\)|https?://\S+)")
_DEC = re.compile(r"(?<![\w.§/\\-])(?<!Python )(?<!Hissə )(?<!Part )(?<!Bölmə )(?<!hissə )"
                  r"([-+]?\d+)\.(\d+)(?:e([-+]?\d+))?(?!\.?\w|-c[iıuü]|-dək)")
_TERMS = [(re.compile(r"\bPart (\d+)"), r"Hissə \1"), (re.compile(r"\bParts (\d+)"), r"Hissə \1"),
          (re.compile(r"\bTier 1\b"), "1-ci pillə"), (re.compile(r"\bTier 2\b"), "2-ci pillə"),
          (re.compile(r"contemporaneous dx"), "eyni dövrün Δx-i"), (re.compile(r"\bcells\b"), "xana")]


def _conv(seg):
    def rep(m):
        if m.group(3) is not None:
            return f"{m.group(1)},{m.group(2)}·10{str(int(m.group(3))).translate(_SUP)}"
        return f"{m.group(1)},{m.group(2)}"
    for pat, sub in _TERMS:
        seg = pat.sub(sub, seg)
    return _DEC.sub(rep, seg)


def az_prose(text):
    """Convert decimal points of prose numbers to commas (and a few fixed English words to Azerbaijani) in a text that
    is already Azerbaijani. Table rows, code spans, LaTeX, links, section numbers (§8.1, 19.4-cü) and versions are kept."""
    out = []
    for line in text.split("\n"):
        if line.lstrip().startswith("|"):
            out.append(line)
            continue
        parts = _CODE.split(line)
        out.append("".join(p if i % 2 else _conv(p) for i, p in enumerate(parts)))
    return "\n".join(out)


# ------------------------------------------------------------------ label translation for generated tables
LOCAL = {
    "yes": "bəli", "no": "xeyr", "True": "bəli", "False": "xeyr", "—": "—", "": "",
}


def translator(module, extra=None):
    """Returns tr(s): Azerbaijani label from output/<module>_strings_az.csv, then `extra`, then LOCAL; else s."""
    import pandas as pd
    d = {}
    p = os.path.join(project_root(), "output", f"{module}_strings_az.csv")
    if os.path.exists(p):
        s = pd.read_csv(p, dtype=str, keep_default_na=False)
        d = dict(zip(s["en"], s["az"]))
    d.update(LOCAL)
    d.update(extra or {})
    low = {k.lower(): v for k, v in d.items()}

    def tr(x):
        s = str(x)
        if s in d:
            return d[s]
        if s.lower() in low:
            return low[s.lower()]
        if re.search(r"[A-Za-z]{3,}", s) and not re.fullmatch(r"[\w.:|/-]+", s):
            UNTRANSLATED.add((module, s))
        return s
    return tr


def md_table(df, fmt=None, index=True, tr=None, index_name="spesifikasiya"):
    """Markdown table like the notebooks' `mdt`, with translated headers and text cells (numbers formatted as in English)."""
    import numpy as np
    fmt, tr = fmt or {}, tr or (lambda s: s)
    d = df.rename_axis(df.index.name or index_name).reset_index() if index else df.copy()
    cols = list(d.columns)

    def cell(c, v):
        if isinstance(v, (float, np.floating)):
            return "—" if not np.isfinite(v) else fmt.get(c, "{:.2f}").format(v).replace(",", " ")
        if isinstance(v, (bool, np.bool_)):
            return "bəli" if v else "xeyr"
        return tr(v)
    out = ["| " + " | ".join(tr(c) for c in cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(cell(c, r[c]) for c in cols) + " |" for _, r in d.iterrows()]
    return "\n".join(out)


# ------------------------------------------------------------------ blocks already in Azerbaijani: copy + convert
def copy_v2(module, tags=("v2",)):
    """Copy AUTO blocks that the English document already carries in Azerbaijani, converting prose numbers."""
    with open(en_path(module), encoding="utf-8") as f:
        en = f.read()
    return write_blocks(module, {t: az_prose(get_block(en, t)) for t in tags})


def fr4_results(ns):
    from ._docgen_az_fr4 import results
    return write_blocks("FR4", results(ns))


def fr4_v2(ns):
    from ._docgen_az_fr4 import cells
    with open(en_path("FR4"), encoding="utf-8") as f:
        en = f.read()
    return write_blocks("FR4", {"v2": az_prose(get_block(en, "v2")), "cells": cells(ns)})


def fr5_blocks(ns):
    from ._docgen_az_fr5 import blocks
    return write_blocks("FR5", blocks(ns))
