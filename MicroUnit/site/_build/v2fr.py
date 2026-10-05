"""v2fr.py — adds the v2 pieces to an existing FR page body: the FR tab strip, a one-line summary box
(components, equations, verdicts) with links, the robustness section (and, for FR12, the gap-filled
data section) before § Fayllar, and a pointer from § B qatı to the synthetic econometrics page."""
import re

from . import core, html, v2data as V, v2nav, v2rob, fr12_imp
from .core import esc


def summary_box(m):
    cat = V.catalog(m)
    st = v2rob.stats(m)
    c = m.lower()
    n_fc = int(cat.has_forecast.astype(bool).sum())
    lb = (f' · <a href="{c}-sintetik.html">B qatının sintetik ekonometrikası →</a>' if m in v2nav.SYNTH else "")
    return ('<div class="box fr-summary"><p>'
            f'<strong>{core.num(n_fc, 0)}</strong> komponent 2026–2030 üçün üç ssenari üzrə proqnozlaşdırılır — '
            f'<a href="{c}-proqnoz.html">tam proqnoz cədvəlləri →</a><br>'
            f'<strong>{core.num(st["n"], 0)}</strong> tənlik qiymətləndirilib ({core.num(st["n_used"], 0)}-i proqnozda) — '
            f'<a href="{c}-tenlikler.html">tam reqressiya nəticələri →</a><br>'
            f'Dayanıqlıq: {html.pill("done", "stabil")} {core.num(st["all"].get("stabil", 0), 0)} · '
            f'{html.pill("partial", "qismən stabil")} {core.num(st["all"].get("qismən stabil", 0), 0)} · '
            f'{html.pill("gap", "qeyri-stabil")} {core.num(st["all"].get("qeyri-stabil", 0), 0)} — '
            f'<a href="#dayaniqliq">ətraflı →</a>{lb}<br>'
            f'Öz ssenarinizi qurmaq və hesabat almaq: <a href="../{v2nav.PANEL_SCEN}">ssenari qurucusu</a> · '
            f'<a href="../{v2nav.PANEL_REPORT}">hesabat qurucusu</a> (İş paneli).</p></div>')


def augment(m, body, secs, path):
    body = body.replace("</h1>", "</h1>\n" + v2nav.strip(m, path), 1)
    k = body.find('<p class="lead-in">')
    if k >= 0:
        e = body.find("</p>", k) + 4
        body = body[:e] + "\n" + summary_box(m) + body[e:]
    else:
        body = body.replace("</nav>", "</nav>\n" + summary_box(m), 1)
    i = body.index('<h2 id="files"')
    n = int(re.search(r'<span class="section-num">(\d+)</span>', body[i:]).group(1))
    extra, add = [], []
    if m == "FR12":
        extra.append(fr12_imp.section(n))
        add.append(("doldurulmus", "Doldurulmuş məlumat"))
        n += 1
    extra.append(v2rob.section(m, n))
    add.append(("dayaniqliq", "Dayanıqlıq"))
    n += 1
    tail = re.sub(r'(<h2 id="files".*?<span class="section-num">)\d+(</span>)', rf"\g<1>{n}\g<2>", body[i:], count=1)
    body = body[:i] + "\n".join(extra) + "\n" + tail
    if m in v2nav.SYNTH:
        j = body.find('<h2 id="layerb"')
        if j >= 0:
            j = body.find("</h2>", j) + 5
            body = (body[:j] + f'\n<p class="box">Bütün B qatı modelləri — model kartları, əmsallar, marjinal effektlər, '
                    f'parametr bərpası: <a href="{m.lower()}-sintetik.html">{esc(m)} · Sintetik B qatı →</a></p>' + body[j:])
    secs = [s for s in secs if s[0] != "files"] + add + [("files", "Fayllar")]
    return body, secs
