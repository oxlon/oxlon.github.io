"""common.py — pieces shared by the six requirement pages."""
from . import core, html
from .core import esc, v

YEARS = [2026, 2027, 2028, 2029, 2030]
SCEN = ["Baseline", "Adverse", "Reform"]
SCEN_AZ = {"Baseline": "Əsas", "Adverse": "Mənfi", "Reform": "İslahat"}

FR_SECTIONS = [("teleb", "Tələb"), ("model", "Model və seçim səbəbi"), ("data", "Məlumat"),
               ("results", "Nəticələr"), ("check", "Yoxlama"), ("limits", "Məhdudiyyətlər"),
               ("files", "Fayllar")]


def files_section(n, code, pre="../"):
    """§ Fayllar — every output CSV of the module as a link with its row count."""
    outs = sorted(p.name for p in core.OUT.glob(f"{code}_*.csv"))
    syn = [o for o in outs if "_SYNTHETIC_" in o]
    real = [o for o in outs if o not in syn]
    li = "".join(f"<li>{html.flink('output/' + o, pre)} <span class=\"tt-where\" style=\"display:inline\">· "
                 f"{v(core.nrows(o), 0)} sətir</span></li>" for o in real)
    body = [html.h2("files", n, "Fayllar"),
            f"<p>Dəftər: {html.flink(code + '.ipynb', pre)} · metodologiya sənədi: "
            f"{html.flink('docs/' + code + '_Methodology.md', pre)}. Modulun <span class=\"val\">{len(outs)}</span> "
            f"çıxış faylı <code>MicroUnit/output/</code> qovluğundadır; hər biri aşağıda birbaşa açılır.</p>",
            f'<ul class="file-list">{li}</ul>']
    if syn:
        lis = "".join(f"<li>{html.flink('output/' + o, pre)} <span class=\"pill pill-gap\">SİNTETİK</span></li>"
                      for o in syn)
        body.append(f"<p><strong>Sintetik (B qatı) çıxışları</strong> — su nişanlıdır, nəticə kimi işlədilmir:</p>"
                    f'<ul class="file-list">{lis}</ul>')
    body.append(f'<p>Bütün modullar üzrə tam siyahı: <a href="{pre}results.html">Nəticələr və fayllar</a>.</p>')
    return "\n".join(body)


def u_cell(u, d=2):
    """Theil U cell: below 1 = beats the benchmark (green), otherwise neutral grey."""
    if not core.isnum(u):
        return "—"
    cls = "skill-pos" if u < 1 else "skill-neg"
    return f'<span class="{cls}">{core.num(u, d)}</span>'


def beat_count(series):
    s = [x for x in series if core.isnum(x)]
    return sum(1 for x in s if x < 1), len(s)


def median(xs):
    s = sorted(x for x in xs if core.isnum(x))
    if not s:
        return float("nan")
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


def scen_table(rows, unit_col=True):
    """rows: [(label, unit, {'Baseline': html, 'Adverse': html, 'Reform': html})]."""
    head = ["Göstərici"] + (["Vahid"] if unit_col else []) + [SCEN_AZ[s] for s in SCEN]
    cols = ["c-wide"] + (["c-tight"] if unit_col else []) + ["c-num"] * 3
    body = [[esc(lab)] + ([esc(u)] if unit_col else []) + [d.get(s, "—") for s in SCEN] for lab, u, d in rows]
    return html.table(head, body, cols=cols)


def year_table(rows, band_head="5–95 % zolağı, 2030"):
    """rows: [(label, unit, [5 values html], band html)]."""
    head = ["Göstərici", "Vahid"] + [str(y) for y in YEARS] + [band_head]
    cols = ["c-wide", "c-tight"] + ["c-num"] * 5 + ["c-text"]
    return html.table(head, [[esc(a), esc(b)] + list(c) + [d] for a, b, c, d in rows], cols=cols)


def band_txt(lo, hi, d=1):
    return f"{v(lo, d)} … {v(hi, d)}"


def intro(text):
    return f'<p class="lead-in">{text}</p>'


def limits_list(items):
    return "<ol>" + "".join(f"<li>{x}</li>" for x in items) + "</ol>"
