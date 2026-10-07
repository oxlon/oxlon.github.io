"""docgen_az_fr10_fr12 — keeps the AUTO blocks of docs/az/FR10_Metodologiya.md and docs/az/FR12_Metodologiya.md in sync.

The FR10 and FR12 notebooks regenerate the `<!-- AUTO:name -->…<!-- /AUTO:name -->` blocks of the ENGLISH documents
(docs/FR10_Methodology.md, docs/FR12_Methodology.md) on every run. The notebooks are not changed: `run_all.py` calls
`sync('FR10')` / `sync('FR12')` after the stage has succeeded, and this module writes the same blocks, in Azerbaijani,
into the Azerbaijani documents. It can also be run by hand:

    python3 -m microlib.docgen_az_fr10_fr12 FR10 FR12

How a block is translated
  * every table cell and every prose sentence is reduced to a *skeleton*: numbers become ⟦0⟧, ⟦1⟧ …, code spans,
    LaTeX and links become ⟦c0⟧ …; the skeleton (or the exact text) is looked up in
      1. microlib/i18n/<module>_auto_az.json   (translation memory: English skeleton -> Azerbaijani skeleton),
      2. output/<module>_strings_az.csv          (labels written by the notebook itself: en -> az),
    and the numbers and code spans are put back. Templates may write ⟦k:ci⟧ (number + ordinal suffix, 2025-ci) or
    ⟦k:da⟧ (number + locative suffix, 2026-da).
  * numbers in prose get the Azerbaijani format (decimal comma, space thousands separator); numbers in tables keep the
    decimal point as produced by the code (only the thousands separator becomes a space); code spans are kept verbatim.
  * lines already in Azerbaijani are copied, only their prose numbers converted.
  * blocks the notebook words in both languages (the v2 blocks: English in the English document, the same block in
    Azerbaijani in output/<module>_doc_blocks_az.json, written by `write_az_sources`) are rendered from the Azerbaijani
    wording — used only while its recorded English text equals the block in the English document (else translated).
  * cells that are numbers or identifiers (codes, file names, T1/T2 flags) are kept.
  * text without a template is kept in English and listed in docs/az/_untranslated_<module>.txt (and printed), so a
    change of wording in a notebook is visible; numbers alone never cause a miss.
The function is idempotent (it only replaces the contents between existing markers) and raises AssertionError when a
block of the English document has no marker pair in the Azerbaijani document (or vice versa).
Only the standard library and pandas are used. Nothing here changes any model output.
"""
import json
import os
import re
import sys

from . import project_root
from .docgen_az import AZ_NAMES, _SUP, az_prose, ordsuf, locsuf

MODULES = ("FR10", "FR12")
for _m in MODULES:
    AZ_NAMES.setdefault(_m, f"{_m}_Metodologiya.md")

AUTO = re.compile(r"(<!-- AUTO:(\w+)(?:\s[^>]*)?-->)(.*?)(<!-- /AUTO:\2 -->)", re.S)
PROT = re.compile(r"(`[^`\n]*`|\$[^$\n]+\$|\[[^\]\n]*\]\([^)\n]*\)|https?://\S+)")
NUM = re.compile(r"(?<![\w.§⟦])(?<!Part )(?<!Parts )(?<!Section )(?<!Python )(?<!Hissə )"
                 r"([-+−]?\d+(?:,\d{3})*(?:\.\d+)?(?:e[-+]?\d+)?)(?![\w⟧]|\.\d)")
SLOT = re.compile(r"⟦(c?\d+)(?::(ci|da))?⟧")
IDENT = re.compile(r"[\w.:/<>*|+=×()\[\],;%~^'’≥≤<>−–—-]+")
AZL = re.compile(r"[əğışöüçİƏŞÇÖÜĞ]")
ENW = re.compile(r"\b(the|and|of|is|are|with|from|which|this|that|for|not|by|in|on|to|a|an|as|no|or)\b")
LISTP = re.compile(r"^(\s*(?:[-*+]\s+|\d+\.\s+|#+\s+|>\s*)?)")
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z*(\"“]|⟦c)")
HEX = re.compile(r"[0-9a-f]{8,64}…?")  # hashes (sha256 prefixes)
SEP = re.compile(r"\|(\s*:?-+:?\s*\|)+")


def _tm_path(module):
    return os.path.join(project_root(), "microlib", "i18n", f"{module}_auto_az.json")


def skeleton(text):
    """'HHI 1,234.5 (`x`)' -> ('HHI ⟦0⟧ (⟦c0⟧)', {'n': ['1,234.5'], 'c': ['`x`']})"""
    slots = {"n": [], "c": []}
    out = []
    for i, p in enumerate(PROT.split(text)):
        if i % 2:
            slots["c"].append(p)
            out.append(f"⟦c{len(slots['c']) - 1}⟧")
        else:
            def pn(m):
                slots["n"].append(m.group(1))
                return f"⟦{len(slots['n']) - 1}⟧"
            out.append(NUM.sub(pn, p))
    return "".join(out), slots


def az_num(s, prose=True):
    """'-1,234.5' -> prose '-1 234,5' / table '-1 234.5'; '7.4e-14' -> prose '7,4·10⁻¹⁴'."""
    sign = s[0] if s[0] in "+-−" else ""
    mant, _, exp = s.lstrip("+-−").partition("e")
    mant = mant.replace(",", " ")
    if prose:
        mant = mant.replace(".", ",")
        if exp:
            return f"{sign}{mant}·10{str(int(exp)).translate(_SUP)}"
    elif exp:
        mant += "e" + exp
    return sign + mant


def fill(sk_az, slots, prose):
    def rn(m):
        k, suf = m.group(1), m.group(2)
        if k.startswith("c"):
            return slots["c"][int(k[1:])]
        raw = slots["n"][int(k)]
        v = az_num(raw, prose)
        if suf:
            try:
                n = int(float(raw.replace(",", "").replace("−", "-")))
                v += "-" + (ordsuf(n) if suf == "ci" else locsuf(n))
            except ValueError:
                pass
        return v
    return SLOT.sub(rn, sk_az)


def _renumber(piece, slots):
    """Skeleton piece with global slot numbers -> (piece with local numbers, local slots)."""
    loc, mp = {"n": [], "c": []}, {}

    def rn(m):
        k = m.group(1)
        if k not in mp:
            kind = "c" if k.startswith("c") else "n"
            loc[kind].append(slots[kind][int(k[1:]) if kind == "c" else int(k)])
            mp[k] = ("c" if kind == "c" else "") + str(len(loc[kind]) - 1)
        return f"⟦{mp[k]}" + (f":{m.group(2)}" if m.group(2) else "") + "⟧"
    return SLOT.sub(rn, piece), loc


def sentences(core):
    """[(skeleton, slots)] of the sentences of one prose line (split on the skeleton, so code spans never split)."""
    sk, slots = skeleton(core)
    return [_renumber(p, slots) for p in SENT.split(sk)]


# English words that the notebooks leave inside otherwise Azerbaijani generated text (source references, rule labels);
# replaced outside code spans.
AZ_FIX = [(re.compile(r"\bworkbook\b"), "iş kitabı"), (re.compile(r"\brows\b"), "sətirlər"),
          (re.compile(r"\brow\b"), "sətir"), (re.compile(r"\(proxy\)"), "(proksi)"),
          (re.compile(r"\bcombination:"), "kombinasiya:"), (re.compile(r"\bstructural:"), "struktur:"),
          (re.compile(r"\bno driver \(null\)"), "sürücü yoxdur (sıfır model)"),
          (re.compile(r"\banchored\b"), "lövbərlənmiş"), (re.compile(r"\bcoherent\b"), "uyğun")]


def az_fix(text):
    parts = PROT.split(text)
    for i in range(0, len(parts), 2):
        for rx, sub in AZ_FIX:
            parts[i] = rx.sub(sub, parts[i])
    return "".join(parts)


THOU = re.compile(r"(?<![\d.,])(\d{1,3})((?:,\d{3})+)(?![\d,]|\.\d)")
IVAL = re.compile(r"\[([-+−]?\d[\d ]*,\d+), ([-+−]?\d[\d ]*,\d+)\]")


def az_text(text):
    """Prose already in Azerbaijani (v2 notes, interpretations): English thousands commas -> spaces, decimal points ->
    commas (docgen_az.az_prose), intervals [0,941, 0,949] -> [0,941; 0,949], leftover English words (AZ_FIX)."""
    parts = PROT.split(text)
    for i in range(0, len(parts), 2):
        parts[i] = THOU.sub(lambda m: m.group(1) + m.group(2).replace(",", " "), parts[i])
    text = az_prose("".join(parts))
    parts = PROT.split(text)
    for i in range(0, len(parts), 2):
        parts[i] = IVAL.sub(r"[\1; \2]", parts[i])
    return az_fix("".join(parts))


def _is_az(sk):
    """True for text already in Azerbaijani (Azerbaijani letters, no English function words; '-in', '-a' suffixes
    after codes such as OLS-in are not English words)."""
    return bool(AZL.search(sk)) and not ENW.search(re.sub(r"-\w+", "", sk))


def _plain(sk):
    """True when a skeleton carries no translatable words (numbers, codes, flags such as T1, symbols only)."""
    return not re.search(r"[a-z]{2,}", re.sub(r"⟦c?\d+⟧|[^\s,;]*_[^\s,;]*|[^\s,;]+\.(?:csv|md|py|json|xlsx?|xls|ipynb)\b", " ", sk))


class TM:
    def __init__(self, module):
        import pandas as pd
        self.module = module
        p = os.path.join(project_root(), "output", f"{module}_strings_az.csv")
        self.exact = {}
        if os.path.exists(p):
            s = pd.read_csv(p, dtype=str, keep_default_na=False)
            self.exact = {e: a for e, a in zip(s["en"], s["az"]) if a}
        tp = _tm_path(module)
        self.mem = json.load(open(tp, encoding="utf-8")) if os.path.exists(tp) else {}
        self.misses = []

    def _look(self, sk):
        if sk in self.mem:
            return self.mem[sk]
        if sk in self.exact:
            return self.exact[sk]
        return None

    def cell(self, text, tag):
        core = text.strip()
        if not core:
            return core
        if core in self.mem:
            return self.mem[core]
        if core in self.exact:
            return self.exact[core]
        sk, slots = skeleton(core)
        if _is_az(sk):
            return az_fix(core)
        az = self._look(sk)
        if az is not None:
            return fill(az, slots, False)
        if _plain(sk) or (IDENT.fullmatch(core) and re.search(r"[_.]\w", core)) or HEX.fullmatch(core):
            return fill(sk, slots, False)
        self.misses.append((tag, "cell", sk))
        return core

    def prose(self, line, tag):
        if not line.strip():
            return line
        tail = line[len(line.rstrip()):]
        line = line.rstrip()
        pre = LISTP.match(line).group(1)
        core = line[len(pre):]
        sk, slots = skeleton(core)
        if _is_az(sk) or _plain(sk):
            return (pre + az_text(core) if not _plain(sk) else pre + fill(sk, slots, True)) + tail
        az = self._look(sk)
        if az is not None:
            return pre + fill(az, slots, True) + tail
        out = []
        for psk, psl in sentences(core):
            a = self._look(psk)
            if a is None and (_plain(psk) or _is_az(psk)):
                a = psk
            if a is None:
                self.misses.append((tag, "prose", psk))
                a = psk
            out.append(fill(a, psl, True))
        return pre + " ".join(out) + tail


def render(tm, tag, block):
    """Translate one AUTO block. Columns whose header ends in '_en' (e.g. indicator_en) hold the English name by design
    and are copied verbatim (only their header is translated)."""
    out, keep, lines = [], set(), block.split("\n")
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("|") and s.endswith("|") and not SEP.fullmatch(s):
            cells = s[1:-1].split("|")
            if i + 1 < len(lines) and SEP.fullmatch(lines[i + 1].strip()):  # header row: remember '_en' columns
                keep = {k for k, c in enumerate(cells) if c.strip().endswith("_en")}
                out.append("| " + " | ".join(tm.cell(c, tag) for c in cells) + " |")
                continue
            out.append("| " + " | ".join(c.strip() if k in keep else tm.cell(c, tag)
                                         for k, c in enumerate(cells)) + " |")
        elif s.startswith("|") or s.startswith("<!--") or s.startswith("```"):
            out.append(ln)
        else:
            out.append(tm.prose(ln, tag))
    return "\n".join(out)


def units(text):
    """All translatable units of the AUTO blocks of an English document: [(kind, tag, skeleton)] (for building the TM)."""
    U = []
    for m in AUTO.finditer(text):
        keep = set()
        for ln in m.group(3).split("\n"):
            s = ln.strip()
            if not s or SEP.fullmatch(s) or s.startswith("<!--"):
                continue
            if not s.startswith("|"):
                keep = set()
            if s.startswith("|") and s.endswith("|"):
                cells = [c.strip() for c in s[1:-1].split("|")]
                if any(c.endswith("_en") for c in cells):
                    keep = {k for k, c in enumerate(cells) if c.endswith("_en")}
                    U += [("cell", m.group(2), c) for c in cells]
                    continue
                U += [("cell", m.group(2), c) for k, c in enumerate(cells) if k not in keep]
            else:
                core = s[len(LISTP.match(s).group(1)):]
                U.append(("line", m.group(2), skeleton(core)[0]))
                U += [("sent", m.group(2), p) for p, _ in sentences(core)]
    return U


def az_sources(module):
    """Azerbaijani sources of AUTO blocks written by the notebook next to the English document:
    output/<module>_doc_blocks_az.json = {tag: {"en": English block, "az": the same block worded in Azerbaijani}}.
    For such a block the Azerbaijani wording is rendered (numbers converted as for any Azerbaijani prose) instead of a
    translation of the English block — but only while "en" equals the block now in the English document."""
    p = os.path.join(project_root(), "output", f"{module}_doc_blocks_az.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def write_az_sources(module, en_blocks, az_blocks):
    """Called by the notebook's documentation step: en_blocks / az_blocks = {tag: text between the markers}."""
    p = os.path.join(project_root(), "output", f"{module}_doc_blocks_az.json")
    d = {t: {"en": en_blocks[t], "az": az_blocks[t]} for t in az_blocks}
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    print(f"output/{module}_doc_blocks_az.json: Azerbaijani sources of {len(d)} AUTO blocks: {sorted(d)}")
    return p


def sync(module):
    """Write every AUTO block of docs/<module>_Methodology.md, in Azerbaijani, into docs/az/<module>_Metodologiya.md."""
    root = project_root()
    enp = os.path.join(root, "docs", f"{module}_Methodology.md")
    azp = os.path.join(root, "docs", "az", AZ_NAMES[module])
    en = open(enp, encoding="utf-8").read()
    az = open(azp, encoding="utf-8").read()
    en_tags = [m.group(2) for m in AUTO.finditer(en)]
    az_tags = [m.group(2) for m in AUTO.finditer(az)]
    missing = [t for t in en_tags if t not in az_tags]
    extra = [t for t in az_tags if t not in en_tags]
    assert not missing and not extra, (f"{module}: AUTO markers differ between the English and the Azerbaijani "
                                       f"document — missing in docs/az: {missing}; not in English: {extra}")
    tm = TM(module)
    side = az_sources(module)
    blocks = {}
    for m in AUTO.finditer(en):
        tag, body = m.group(2), m.group(3)
        s = side.get(tag)
        if s is not None and s.get("en") != body:
            print(f"    {module} AUTO:{tag}: the Azerbaijani source in output/{module}_doc_blocks_az.json is not from the run "
                  f"that wrote the English block — the English block is translated instead")
            s = None
        blocks[tag] = render(tm, tag, s["az"] if s is not None else body)
    new = AUTO.sub(lambda m: m.group(1) + blocks[m.group(2)] + m.group(4), az)
    if new != az:
        with open(azp, "w", encoding="utf-8") as f:
            f.write(new)
    up = os.path.join(root, "microlib", "i18n", f"{module}_untranslated.txt")
    if tm.misses:
        with open(up, "w", encoding="utf-8") as f:
            f.write("".join(f"{a}\t{k}\t{b}\n" for a, k, b in tm.misses))
    elif os.path.exists(up):
        os.remove(up)
    print(f"docs/az/{AZ_NAMES[module]}: {len(blocks)} AUTO blocks synced from docs/{module}_Methodology.md"
          f" ({'changed' if new != az else 'unchanged'}); {len(tm.misses)} generated text unit(s) without an"
          f" Azerbaijani template" + (f" -> microlib/i18n/{module}_untranslated.txt" if tm.misses else ""))
    for a, k, b in tm.misses[:10]:
        print(f"    [{a}] {b[:160]}")
    return len(tm.misses)


if __name__ == "__main__":
    for _mod in (sys.argv[1:] or MODULES):
        sync(_mod.upper())
