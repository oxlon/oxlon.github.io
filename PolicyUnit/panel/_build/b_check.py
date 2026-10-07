"""b_check.py — build checks of the Siyasət paneli (copied from RiskUnit/panel/_build/b_check.py) (each returns a list of error strings; the build fails on any):
parse (every bundle and JS file parses: JSON payload + `node --check`), routes/links, completeness (every scenario has
headline results, every output is shown somewhere or listed as intentionally hidden) and the untranslated-English scan."""
import json
import re
import shutil
import subprocess
from pathlib import Path

from . import bcore as C
from .b_i18n import CODE_COLS, bad_words

# outputs deliberately not shown in the panel (reason in Azerbaijani, listed on the Metodologiya page)
HIDDEN = {
    "P1_run_meta.json": "işin metaməlumatı (vintaj id-ləri) — Metodologiya səhifəsində «Son icra» kartında göstərilir",
    "P1_freshness.csv": "işin sonunda (panel qurulduqdan sonra) yazılan texniki təzəlik/vintaj yoxlaması — log faylı kimi",
}
PAGES = ["", "qurucu", "tesir", "sektor", "sosial", "risk", "kpi", "muqayise", "validasiya", "hesabat", "metod"]


def _payload(txt):
    i = txt.index("={") if "={" in txt else txt.index("=[")
    return json.loads(txt[i + 1:txt.rstrip().rindex(";")])


def check_parse(data_dir):
    errs = []
    node = shutil.which("node")
    for p in sorted(data_dir.glob("*.js")):
        try:
            _payload(p.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            errs.append(f"{p.name}: JSON oxunmur ({e})")
    for p in sorted(data_dir.glob("*.js")) + sorted((C.PANEL / "js").glob("*.js")):
        if node:
            r = subprocess.run([node, "--check", str(p)], capture_output=True, text=True)
            if r.returncode:
                errs.append(f"{p.name}: JS sintaksis xətası: {r.stderr.strip().splitlines()[-1] if r.stderr else ''}")
    if not node:
        print("  (node tapılmadı — JS sintaksis yoxlaması buraxıldı)")
    return errs


def js_sources():
    return {p.name: p.read_text(encoding="utf-8") for p in sorted((C.PANEL / "js").glob("*.js"))}


def check_links(hub):
    errs = []
    js = js_sources()
    html = (C.PANEL / "index.html").read_text(encoding="utf-8")
    for src in re.findall(r'(?:src|href)="([^"#?]+)"', html):
        if not src.startswith(("http", "data:")) and not (C.PANEL / src).exists():
            errs.append(f"index.html: fayl yoxdur: {src}")
    pages = {""}
    for t in js.values():
        pages |= set(re.findall(r"U\.pages\.(\w+)\s*=", t)) | set(re.findall(r"U\.pages\['(\w*)'\]\s*=", t))
    for name, t in js.items():
        for r in re.findall(r"#/([a-z0-9]*)", t):
            if r not in pages:
                errs.append(f"{name}: '#/{r}' marşrutu üçün səhifə yoxdur")
        for rel in re.findall(r"'\.\./((?:docs|output|api|config|data)/[^'#?]*)'", t):
            if not (C.UNIT / rel).exists():
                errs.append(f"{name}: keçid yoxdur: ../{rel}")
        for rel in re.findall(r"'\.\./\.\./([^'#?]+)'", t):
            if not (C.MP / rel).exists():
                errs.append(f"{name}: keçid yoxdur: ../../{rel}")
        for b in re.findall(r"U\.lazy\('(\w+)'", t):
            if not (C.PANEL / "data" / f"{b}.js").exists():
                errs.append(f"{name}: paket yoxdur: data/{b}.js")
    txt = hub.read_text(encoding="utf-8")
    for p in PAGES:
        if p not in pages:
            errs.append(f"səhifə yoxdur: #/{p}")
    for href in re.findall(r'href="([^"#?]+)', txt):
        if not href.startswith(("http", "data:", "mailto:")) and not (C.UNIT / href).resolve().exists():
            errs.append(f"{hub.name} (mərkəz): keçid yoxdur: {href}")
    return errs, sorted(pages)


def check_complete():
    """Every output (catalogue + output/) is bundled and read by a page, or hidden with a reason; every catalogued file
    exists; every official scenario has headline results (P1) and KPI ranking (P5)."""
    errs = []
    js = "\n".join(js_sources().values())
    cat = C.csv("_catalog.csv", "docs")
    files = set(cat["file"]) if cat is not None else set()
    present = {p.name for p in C.OUT.glob("*.csv")} | {p.name for p in C.OUT.glob("*.json")}
    for f in sorted(files - present):
        errs.append(f"{f}: kataloqda var, output/ qovluğunda yoxdur")
    for f in sorted(present - files - {"_catalog.csv"}):
        print(f"  xəbərdarlıq — {f}: output/ qovluğunda var, kataloqda yoxdur")
    for f in sorted(files | present):
        if f in HIDDEN or f == "_catalog.csv":
            continue
        if f not in C.USED:
            errs.append(f"{f}: paneldə göstərilmir və gizli siyahıda deyil")
            continue
        stem = f.rsplit(".", 1)[0]
        if f.endswith(".csv") and f"'{stem}'" not in js:
            errs.append(f"{f}: paketə yazılıb, lakin heç bir səhifə onu oxumur ('{stem}')")
    ids = sorted(p.stem for p in (C.CONFIG / "scenarios").glob("*.json"))
    hl = C.csv("P1_headline.csv", "core")
    rk = C.csv("P5_ranking.csv", "core")
    for sid in ids:
        if hl is not None and sid not in set(hl["scenario"]):
            errs.append(f"{sid}: P1_headline.csv-də nəticə yoxdur (run_all.py-ni işə salın)")
        if rk is not None and sid not in set(rk["scenario"]):
            errs.append(f"{sid}: P5_ranking.csv-də KPI reytinqi yoxdur")
    return errs, ids


def _scan_obj(o, where, out, col=None):
    if isinstance(o, dict):
        if "c" in o and "r" in o and isinstance(o["r"], list):
            pool, pc = o.get("p", []), set(o.get("pc", []))
            for j, c in enumerate(o["c"]):
                if c in CODE_COLS:
                    continue
                seen = set()
                for r in o["r"]:
                    v = r[j] if j < len(r) else None
                    if c in pc and isinstance(v, int):
                        v = pool[v]
                    if isinstance(v, str) and v not in seen:
                        seen.add(v)
                        _scan_str(v, f"{where}.{c}", out)
            return
        for k, v in o.items():
            if k not in CODE_COLS and k not in ("x", "html_raw"):
                _scan_obj(v, f"{where}.{k}", out, k)
    elif isinstance(o, list):
        for v in o:
            _scan_obj(v, where, out, col)
    elif isinstance(o, str):
        _scan_str(o, where, out)


def _scan_str(s, where, out):
    s = re.sub(r"<(code|pre)[^>]*>.*?</\1>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]*>", " ", s)
    s = re.sub(r"\{[^{}]*\}", " ", s)                                  # template placeholders {value}
    s = re.sub(r"`[^`]*`|'[^'\n]*'|\"[^\"\n]*\"", " ", s)          # quoted names (Ministry sheet / cell citations)
    for line in s.split("\n"):
        b = bad_words(line)
        if b:
            out.append((where, line.strip()[:200], ",".join(sorted(set(b)))))


_JSSTR = re.compile(r"'((?:[^'\\\n]|\\.)*)'")


def check_english(hub):
    bad = []
    for name, (var, obj) in sorted(C.BUNDLES.items()):
        _scan_obj(obj, name, bad)
    for name, t in js_sources().items():
        for i, line in enumerate(t.split("\n"), 1):
            if line.strip().startswith(("//", "/*", "*")):
                continue
            for m in _JSSTR.finditer(line):
                s = re.sub(r"<[^>]*>|^[^<]*?>|<[^>]*$|\b[\w-]+=\"[^\"]*\"?", " ", m.group(1))
                if " " not in s.strip():
                    continue
                b = bad_words(s)
                if b:
                    bad.append((f"{name}:{i}", s.strip()[:160], ",".join(sorted(set(b)))))
    for p in (C.PANEL / "index.html", hub):
        txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", p.read_text(encoding="utf-8"), flags=re.S)
        for ln in re.sub(r"<[^>]+>", "\n", txt).split("\n"):
            b = bad_words(ln)
            if b:
                bad.append((p.name, ln.strip()[:160], ",".join(sorted(set(b)))))
    (C.PANEL / "i18n" / "untranslated.txt").write_text("\n".join("\t".join(r) for r in bad) + ("\n" if bad else ""),
                                                      encoding="utf-8")
    return bad
