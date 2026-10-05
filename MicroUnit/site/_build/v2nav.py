"""v2nav.py — the per-FR tab strip (Xülasə · Proqnoz cədvəlləri · Tənliklər · Dayanıqlıq · Sintetik B qatı)
and the links to the İş paneli."""
from .core import esc

PANEL = "../panel/index.html"            # relative to the site root
PANEL_SCEN = PANEL + "#/ssenari"
PANEL_REPORT = PANEL + "#/hesabat"
SYNTH = {"FR10", "FR12"}


def pages(m):
    c = m.lower()
    out = [(f"fr/{c}.html", "Xülasə"), (f"fr/{c}-proqnoz.html", "Proqnoz cədvəlləri"),
           (f"fr/{c}-tenlikler.html", "Tənliklər"), (f"fr/{c}.html#dayaniqliq", "Dayanıqlıq")]
    if m in SYNTH:
        out.append((f"fr/{c}-sintetik.html", "Sintetik B qatı"))
    return out


def strip(m, cur):
    """Tab strip under the h1; `cur` is the page path (e.g. 'fr/fr1-proqnoz.html')."""
    items = []
    for href, lab in pages(m):
        on = href == cur
        h = href.split("/", 1)[1]
        cls = ' class="on" aria-current="page"' if on else ""
        items.append(f'<a{cls} href="{esc(h)}">{esc(lab)}</a>')
    items.append(f'<a class="to-panel" href="../{PANEL}">İş panelində aç →</a>')
    return f'<nav class="fr-tabs" aria-label="{esc(m)} bölmələri">' + "".join(items) + "</nav>"
