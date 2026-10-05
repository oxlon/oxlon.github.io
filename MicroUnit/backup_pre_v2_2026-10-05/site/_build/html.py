"""html.py — page shell (sprite, sidebar, footer) and the macro site's components."""
import json

from . import core
from .core import esc

NAV = [
    ("Ümumi", [
        ("index.html", "Ümumi baxış", None),
        ("methodology.html", "Metod", None),
        ("data.html", "Məlumat mənbələri", None),
        ("synthetic.html", "Sintetik məlumat", None),
        ("notebooks.html", "Jupyter dəftərləri", None),
    ]),
    ("Funksional tələblər (§15.5.2)", [
        ("fr/fr1.html", "Sektorlar və bazarlar", "FR1"),
        ("fr/fr3.html", "Orta aylıq əmək haqqı", "FR3"),
        ("fr/fr4.html", "Məşğulluq", "FR4"),
        ("fr/fr5.html", "Pullu xidmətlər", "FR5"),
        ("fr/fr10.html", "Müəssisələr: maliyyə, effektivlik, bazar payı", "FR10"),
        ("fr/fr12.html", "Rəqabət mühiti", "FR12"),
    ]),
    ("Təhvil", [
        ("results.html", "Nəticələr və fayllar", None),
    ]),
]


def sprite():
    svg = (core.SITE / "assets" / "icons.svg").read_text(encoding="utf-8")
    return svg.strip()           # the macro sprite, verbatim (already display:none)


def _nav(path, sections, pre):
    out = []
    for title, items in NAV:
        lis = []
        for href, label, num in items:
            cur = ' class="current"' if href == path else ""
            n = f'<span class="nav-num">{num}</span>' if num else ""
            sub = ""
            if href == path and sections:
                sub = '<ul class="nav-sections">' + "".join(
                    f'<li><a href="#{i}">{esc(t)}</a></li>' for i, t in sections) + "</ul>"
            lis.append(f'<li><a{cur} href="{pre}{href}">{n}{esc(label)}</a>{sub}</li>')
        out.append(f'<div class="nav-group"><span class="nav-title">{esc(title)}</span><ul>{"".join(lis)}</ul></div>')
    return "".join(out)


def footer(files, date):
    rel = [core.Path(p).relative_to(core.UNIT) if core.Path(p).is_relative_to(core.UNIT) else core.Path(p).name
           for p in files]
    names = [f"<code>{esc(r)}</code>" for r in rel]
    if len(names) > 10:                          # group long lists: output/FR1_*.csv (12), …
        groups = {}
        for r in rel:
            r = str(r)
            d, _, n = r.rpartition("/")
            key = (d + "/" if d else "") + (n.split("_")[0] + "_*" + n[n.rfind("."):] if "_" in n else n)
            groups[key] = groups.get(key, 0) + 1
        names = [f"<code>{esc(k)}</code> ({c})" if c > 1 else f"<code>{esc(k)}</code>" for k, c in groups.items()]
    stamp = core.md5_of(files)[:12] if files else "—"
    if names:
        src = (f"Bu səhifədəki hər rəqəm yığım anında bu {len(files)} fayldan oxunur: "
               + ", ".join(names) + ". Möhür həmin faylların md5 cəmidir.")
    else:
        src = "Bu səhifədə çıxış faylından oxunan rəqəm yoxdur."
    return ('<footer class="site-footer">\n'
            f'  <span class="stamp-row">MİİS §15.5.2 · yığılıb {date} · möhür <code>{stamp}</code></span>\n'
            f'  <span class="stamp-row">{src}</span>\n'
            f'  <span class="stamp-row">Sayt <code>site/build_site.py</code> ilə yenidən qurulur; əl ilə redaktə edilmir.</span>\n'
            '</footer>')


def page(path, title, sections, body, date, desc=""):
    depth = path.count("/")
    pre = "../" * depth
    files = core.used()
    css_micro = f'<link rel="stylesheet" href="{pre}assets/micro.css">'
    return f"""<!doctype html>
<html lang="az">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — MİİS §15.5.2</title>
<meta name="description" content="{esc(desc or title)}">
<meta name="robots" content="noindex,nofollow">
<link rel="stylesheet" href="{pre}assets/base.css">
{css_micro}
</head>
<body>
{sprite()}
<a class="skip" href="#main">Məzmuna keç</a>
<button class="menu-button" id="menu-button" aria-expanded="false" aria-controls="sidebar">
<svg class="icon" aria-hidden="true"><use href="#icon-menu"/></svg>Mündəricat</button>
<div class="shell">
<nav class="sidebar" id="sidebar" aria-label="Saytın bölmələri">
  <div class="sidebar-head">
    <a class="mark" href="{pre}index.html">MİİS §15.5.2
      <span class="mark-sub">Mikroiqtisadi təhlil və proqnozlaşdırma modulu</span></a>
  </div>
  {_nav(path, sections, pre)}
</nav>
<main class="content" id="main">
{body}
{footer(files, date)}
</main>
</div>
<script src="{pre}assets/plotly.min.js"></script>
<script src="{pre}assets/site.js"></script>
</body>
</html>
"""


# ---------------------------------------------------------------- components
def h2(id_, n, title, extra=""):
    return (f'<h2 id="{id_}"{extra}><a class="anchor" href="#{id_}" aria-hidden="true">#</a>'
            f'<span class="section-num">{n}</span>{esc(title)}</h2>')


def h3(title, id_=None):
    i = f' id="{id_}"' if id_ else ""
    return f"<h3{i}>{esc(title)}</h3>"


ICON = {"csv": "data", "xlsx": "data", "ipynb": "flask", "md": "document", "py": "document"}


def chip(rel, label=None):
    """File chip (macro .file-held) — rel is relative to MicroUnit."""
    ext = rel.rsplit(".", 1)[-1]
    ic = ICON.get(ext, "document")
    lab = label or rel.split("/")[-1]
    return (f'<span class="file-held" title="MicroUnit/{esc(rel)}"><svg class="icon icon-sm" aria-hidden="true">'
            f'<use href="#icon-{ic}"/></svg>{esc(lab)}</span>')


def flink(rel, pre, label=None):
    """A real link to a module file (relative to MicroUnit) from a page at depth `pre`."""
    ext = rel.rsplit(".", 1)[-1]
    ic = "download" if ext in ("csv", "xlsx") else ICON.get(ext, "document")
    lab = label or rel.split("/")[-1]
    return (f'<a class="file-link" href="{pre}../{esc(rel)}"><svg class="icon icon-sm" aria-hidden="true">'
            f'<use href="#icon-{ic}"/></svg>{esc(lab)}</a>')


def pill(kind, text):
    return f'<span class="pill pill-{kind}">{esc(text)}</span>'


def table(head, rows, cls="tbl tbl-dense", cols=None, raw_head=False):
    """head: list of str; rows: list of lists of already-rendered HTML; cols: css class per column."""
    cols = cols or ["c-text"] * len(head)
    th = "".join(f'<th class="{c}">{h if raw_head else esc(h)}</th>' for h, c in zip(head, cols))
    body = "".join("<tr>" + "".join(f'<td class="{c}">{x}</td>' for x, c in zip(r, cols)) + "</tr>"
                   for r in rows)
    return f'<div class="table-wrap"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def fig(fid, title, spec, cap, window, pre=""):
    js = json.dumps(spec, ensure_ascii=False, separators=(",", ":"), sort_keys=True).replace("</", "<\\/")
    return (f'<figure class="fig" id="fig-{fid}"><h4 class="fig-title" id="fig-{fid}-title">{esc(title)}</h4>'
            f'<div class="fig-mount is-loading" data-fig="{fid}">qrafik yüklənir…</div>'
            f'<script type="application/json" id="figdata-{fid}">{js}</script>'
            f'<figcaption><span class="fig-cap">{cap}</span><span class="fig-window">{window}</span>'
            f'<span class="fig-id">[{fid}]</span></figcaption></figure>')


def kicker(code, nb, doc):
    return (f'<p class="page-kicker">{code} · dəftər {chip(nb)} · metodologiya {chip(doc)}</p>')


def synth_banner(pre, what):
    return (f'<div class="synth-banner" role="note"><svg class="icon" aria-hidden="true"><use href="#icon-warning"/></svg>'
            f'<div><strong>SİNTETİK MƏLUMAT — real müəssisə məlumatı deyil.</strong> {what} '
            f'Bu bölmədəki nəticələr yalnız texniki nümayişdir (boru xəttinin yoxlanılması), təhlil nəticəsi deyil. '
            f'<a href="{pre}synthetic.html">Faylın necə əvəz olunduğu →</a></div></div>')


def box(inner):
    return f'<div class="box">{inner}</div>'
