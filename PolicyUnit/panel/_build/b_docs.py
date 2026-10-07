"""b_docs.py — PolicyUnit/docs/*.md (+ config and data READMEs) rendered to HTML at build time (headings, paragraphs, lists, tables, code, emphasis,
links) → data/docs.js, loaded by the Metodologiya page. No dependency; the subset of Markdown the docs use.
Copied from RiskUnit/panel/_build/b_docs.py. Also: config tables shown on the Metodologiya page."""
import html
import re

from . import bcore as C

TITLES = {
    "Metodologiya_core.md": "Nüvə: FR1 makro/mikro, FR5 KPI, NFR2, NFR4",
    "Metodologiya_IO.md": "Girdi-çıxdı (IO) modeli — FR2",
    "Metodologiya_mikrosimulyasiya.md": "Mikrosimulyasiya — FR3 (SİNTETİK məlumat)",
    "Metodologiya_yan_tesirler.md": "Yan təsirlər və risk inteqrasiyası — FR4",
    "Metodologiya_FR4.md": "Yan təsirlər və risk inteqrasiyası — FR4",
    "Sapma_hesabati.md": "Sapma hesabatı — tarixi validasiya (NFR1)",
    "config/README_az.md": "Konfiqurasiya: ssenari və alət əlavə etmək (NFR4)",
    "data/households/README_az.md": "Ev təsərrüfatı məlumatı: şablon və sütun xəritəsi",
    "data/io/README_az.md": "IO məlumatı: mənbələr və MD5",
}
EXTRA = ["config/README_az.md", "data/households/README_az.md", "data/io/README_az.md"]
CFG = ["kpi.csv", "side_effect_rules.csv", "mitigation_map.csv", "historical_events.csv", "fiscal_params.csv",
       "tax_benefit.csv", "longrun_params.csv"]


def inline(s):
    s = {"True": "bəli", "False": "xeyr"}.get(s.strip(), s)
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", lambda m: "<code>" + m.group(1) + "</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*([^*\s][^*]*)\*(?!\w)", r"<i>\1</i>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: _link(m.group(1), m.group(2)), s)
    return s


def _link(text, href):
    if href.startswith("http"):
        return f'<a href="{href}" target="_blank" rel="noopener">{text}</a>'
    if href.endswith(".md"):
        return f'<a href="#/metod/{href.split("/")[-1][:-3]}">{text}</a>'
    return f"<span title=\"{html.escape(href)}\">{text}</span>"


def md(txt):
    txt = re.sub(r"(?ms)^## EN\b.*?(?=^## |\Z)", "", txt)          # the short English summaries are not shown
    txt = re.sub(r"<!--.*?-->", "", txt, flags=re.S)                 # AUTO markers of generated sections
    lines = txt.replace("\r", "").split("\n")
    out, i, toc = [], 0, []
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("<!--"):
            i += 1
            continue
        if ln.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append("<pre class=\"eqtxt\">" + html.escape("\n".join(lines[i + 1:j])) + "</pre>")
            i = j + 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", ln)
        if m:
            lvl = len(m.group(1))
            hid = f"h{len(toc)}"
            toc.append((lvl, hid, re.sub(r"[`*]", "", m.group(2))))
            out.append(f'<h{lvl + 1} id="{hid}">{inline(m.group(2))}</h{lvl + 1}>')
            i += 1
            continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                    rows.append(cells)
                i += 1
            h = '<div class="itbl-wrap"><table class="itbl doc"><thead><tr>' + "".join(f"<th class=\"l\">{inline(c)}</th>" for c in rows[0]) + "</tr></thead><tbody>"
            h += "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
            out.append(h + "</tbody></table></div>")
            continue
        if re.match(r"^\s*([-*]|\d+\.)\s+", ln):
            tag = "ol" if re.match(r"^\s*\d+\.", ln) else "ul"
            items = []
            while i < len(lines) and (re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]) or (lines[i].startswith("  ") and lines[i].strip())):
                if re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                    items.append(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i]))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        if ln.startswith(">"):
            q = []
            while i < len(lines) and lines[i].startswith(">"):
                q.append(lines[i].lstrip(">").strip())
                i += 1
            out.append('<div class="note-b">' + "<br>".join(inline(x) for x in q if x) + "</div>")
            continue
        if ln.strip() in ("---", "***"):
            out.append("<hr>")
            i += 1
            continue
        if not ln.strip():
            i += 1
            continue
        para = [ln]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||```|>|\s*([-*]|\d+\.)\s|<!--)", lines[i]):
            para.append(lines[i])
            i += 1
        out.append("<p>" + "<br>".join(inline(p.strip()) for p in para) + "</p>")
    return "\n".join(out), toc


def build(tr):
    D = []
    paths = [(p, f"docs/{p.name}") for p in sorted(C.DOCS.glob("*.md"))]
    paths += [(C.UNIT / rel, rel) for rel in EXTRA if (C.UNIT / rel).exists()]
    order = list(TITLES)
    for p, rel in sorted(paths, key=lambda x: (order.index(x[1].replace("docs/", "")) if x[1].replace("docs/", "") in order else 99, x[1])):
        body, toc = md(p.read_text(encoding="utf-8"))
        body = tr(body)
        key = rel.replace("docs/", "")
        slug = p.stem if rel.startswith("docs/") else rel[:-3].replace("/", "_")
        D.append({"slug": slug, "file": rel, "title": TITLES.get(key, p.stem.replace("_", " ")),
                  "html": body, "toc": [list(t) for t in toc if t[0] <= 2]})
    from .b_data import auto_pool
    cfg = {}
    for n in CFG:
        d = C.cfg(n, keep_default_na=False)
        if d is not None:
            d = tr.df(d)
            cfg["cfg_" + n[:-4]] = C.table(d, pool=auto_pool(d))
    cat = C.csv("_catalog.csv", "docs")
    cfg["_catalog"] = C.table(tr.df(cat), pool=auto_pool(cat)) if cat is not None else None
    return [("docs", dict(docs=D, **cfg))]
