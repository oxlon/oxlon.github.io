"""b_docs.py — RiskUnit/docs/*.md rendered to HTML at build time (headings, paragraphs, lists, tables, code, emphasis,
links) → data/docs.js, loaded by the Metodologiya page. No dependency; the subset of Markdown the docs use."""
import html
import re

from . import bcore as C

TITLES = {
    "Risk_Metodologiyasi.md": "Risk metodologiyası (FR1–FR4, NFR1–NFR3)",
    "VaR_CaR_metodologiya.md": "VaR, ES və CaR metodologiyası",
    "CAEM_inteqrasiya.md": "CAEM inteqrasiyası",
    "Avtomatik_yenilenme_ve_gundelik_monitor.md": "Avtomatik yenilənmə və gündəlik monitor",
    "Miqyaslanma_ve_tedbirler.md": "Miqyaslanma və tədbirlər",
}


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
        if ln.strip() in ("---", "***"):
            out.append("<hr>")
            i += 1
            continue
        if not ln.strip():
            i += 1
            continue
        para = [ln]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||```|\s*([-*]|\d+\.)\s|<!--)", lines[i]):
            para.append(lines[i])
            i += 1
        out.append("<p>" + "<br>".join(inline(p.strip()) for p in para) + "</p>")
    return "\n".join(out), toc


def build(tr):
    D = []
    for p in sorted(C.DOCS.glob("*.md"), key=lambda p: (list(TITLES).index(p.name) if p.name in TITLES else 99, p.name)):
        body, toc = md(p.read_text(encoding="utf-8"))
        body = tr(body)
        D.append({"slug": p.stem, "file": f"docs/{p.name}", "title": TITLES.get(p.name, p.stem.replace("_", " ")),
                  "html": body, "toc": [list(t) for t in toc if t[0] <= 2]})
    return [("docs", {"docs": D})]
