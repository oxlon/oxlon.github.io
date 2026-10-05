"""pg_fc.py — fr/frX-proqnoz.html: the full 2026–2030 forecast of every catalog component in every
scenario (level, growth, 2030 band), one collapsible table per component group, from FRx_forecast_tidy.csv.
The build fails if a catalog component with a forecast lacks any year in any of its scenarios."""
import re

from . import core, html, v2data as V, v2nav, v2eq
from .core import esc
from .v2data import isnum

YEARS = [2026, 2027, 2028, 2029, 2030]
SCEN = ["Baseline", "Adverse", "Reform"]
SCEN_AZ = {"Baseline": "Əsas", "Adverse": "Mənfi", "Reform": "İslahat"}
IMP = "Doldurulmuş (interpolyasiya)"


class Incomplete(Exception):
    pass


def cid(i):
    return "c-" + re.sub(r"[^A-Za-z0-9_-]+", "-", i)


def index(m):
    """{id: {scenario: {year: (value, lo, hi, imputed, is_forecast)}}} from the tidy file."""
    t = V.tidy(m)
    out = {}
    for r in t.itertuples(index=False):
        out.setdefault(r.id, {}).setdefault(r.scenario, {})[int(r.year)] = (
            r.value, r.lower_5, r.upper_95, bool(r.imputed), bool(r.is_forecast))
    return out


def check(m, cat, idx):
    miss = []
    for r in cat.itertuples(index=False):
        if not bool(r.has_forecast):
            continue
        for s in str(r.scenarios).split(";"):
            got = idx.get(r.id, {}).get(s, {})
            lack = [y for y in YEARS if y not in got or not isnum(got[y][0])]
            if lack:
                miss.append(f"{r.id} [{s}] {lack}")
    if miss:
        raise Incomplete(f"{m}: {len(miss)} komponent-ssenaridə proqnoz ili çatmır: " + "; ".join(miss[:20]))


def last_actual(series_by_scen):
    best = None
    for s in ["ACTUAL"] + SCEN:
        for y, rec in (series_by_scen.get(s) or {}).items():
            if y <= 2025 and not rec[4] and isnum(rec[0]) and (best is None or y > best[0]):
                best = (y, rec)
    return best


def cell(rec, d):
    if rec is None or not isnum(rec[0]):
        return "—"
    s = core.num(rec[0], d)
    return f'<i class="imp" title="{IMP}">{s}</i>' if rec[3] else s


def growth(kind, base, end, d):
    if not (isnum(base) and isnum(end)):
        return "—"
    if kind in ("level", "index"):
        if base <= 0 or end <= 0:
            return "—"
        return core.num(((end / base) ** (1 / 5) - 1) * 100, 1, sign=True) + core.NBSP + "%"
    return core.num(end - base, max(d, 1), sign=True) + core.NBSP + "f.b."


def eq_links(ids, known, m):
    seen = []
    for i in str(ids or "").split(";"):
        i = i.strip()
        if i and i in known and i not in seen:
            seen.append(i)
    if not seen:
        return "—"
    page = f"{m.lower()}-tenlikler.html"
    out = [f'<a href="{page}#{v2eq.anchor(i)}"><code>{esc(i.split(".", 1)[-1])}</code></a>' for i in seen[:3]]
    if len(seen) > 3:
        out.append(f'<span class="more">+{len(seen) - 3}</span>')
    return " ".join(out)


def group_table(rows_cat, idx, known, m):
    head = ["Göstərici", "Ssenari", "Son faktiki"] + [str(y) for y in YEARS] + ["Artım 2025→30", "Zolaq 2030"]
    body = []
    for r in rows_cat:
        ser = idx.get(r.id, {})
        la = last_actual(ser)
        scens = [s for s in str(r.scenarios).split(";") if s in ser] or [s for s in SCEN if s in ser]
        vals = [rec[0] for s in scens for rec in ser[s].values()]
        d = V.decimals(vals)
        lab = esc(V.fix_az(V.az(r.label_az)))
        unit = esc(V.az(r.unit_az)) if isinstance(r.unit_az, str) else "—"
        for k, s in enumerate(scens):
            rec = ser[s]
            end = rec.get(2030)
            band = "—"
            if end is not None and isnum(end[1]) and isnum(end[2]):
                band = f"{core.num(end[1], d)} … {core.num(end[2], d)}"
            la_txt = f'{cell(la[1], d)} <span class="yr">({la[0]})</span>' if la else "—"
            lead = []
            if k == 0:
                n = len(scens)
                eqs = eq_links(r.equation_ids, known, m)
                eqs = f'<span class="eqlinks">tənlik: {eqs}</span>' if eqs != "—" else ""
                lead = [f'<td class="c-wide" rowspan="{n}" id="{cid(r.id)}">{lab}<span class="unit">{unit}</span>'
                        f'<span class="cid">{esc(r.id)}</span>{eqs}</td>']
            tds = lead + [f'<td class="c-tight sc sc-{s.lower()}">{SCEN_AZ.get(s, s)}</td>',
                          f'<td class="c-num">{la_txt if k == 0 else ""}</td>']
            tds += [f'<td class="c-num">{cell(rec.get(y), d)}</td>' for y in YEARS]
            tds += [f'<td class="c-num">{growth(r.kind, la[1][0] if la else None, end[0] if end else None, d)}</td>',
                    f'<td class="c-num band">{band}</td>']
            body.append(f'<tr class="{"first" if k == 0 else "cont"}">' + "".join(tds) + "</tr>")
    th = "".join(f"<th>{esc(h)}</th>" for h in head)
    return (f'<div class="table-wrap"><table class="tbl tbl-dense tbl-fc"><thead><tr>{th}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def not_forecast_list(m):
    try:
        nf = V.not_forecast(m)
    except FileNotFoundError:
        return ""
    if nf.empty:
        return ""
    lab = next(c for c in ("component_az", "label_az") if c in nf.columns) if any(
        c in nf.columns for c in ("component_az", "label_az")) else None
    items = []
    for r in nf.itertuples(index=False):
        name = getattr(r, lab) if lab else getattr(r, nf.columns[0])
        items.append(f"<li><strong>{esc(V.az(name))}</strong> — {esc(V.az(getattr(r, 'reason_az', '')))}</li>")
    return ("<p>Aşağıdakı komponentlər üçün proqnoz qurulmur; səbəb məlumatdadır və açıq yazılıb:</p>"
            "<ul class=\"nf-list\">" + "".join(items) + "</ul>")


def build(m, title, pre="../"):
    cat = V.catalog(m)
    idx = index(m)
    check(m, cat, idx)
    known = {e["id"] for e in V.equations(m)}
    path = f"fr/{m.lower()}-proqnoz.html"
    fc = cat[cat.has_forecast.astype(bool)]
    groups = {}
    for r in fc.itertuples(index=False):
        groups.setdefault(V.fix_az(V.az(r.group_az)), []).append(r)
    n_imp = sum(1 for s in idx.values() for ys in s.values() for rec in ys.values() if rec[3])
    secs = [("oxu", "Cədvəlləri necə oxumalı"), ("cedveller", "Qruplar üzrə cədvəllər")]
    o = [f"<h1>{esc(m)} — Proqnoz cədvəlləri, 2026–2030</h1>", v2nav.strip(m, path),
         f'<p class="lead-in">{esc(title)}: kataloqdakı bütün {core.num(len(fc), 0)} komponentin 2026–2030 proqnozu — '
         "hər üç ssenari (Əsas, Mənfi, İslahat) üzrə səviyyə, orta illik artım və 2030 zolağı. Cədvəllər "
         f"{core.num(len(groups), 0)} qrupa bölünüb; qrupun başlığına klikləyin. Bütün rəqəmlər "
         f"{html.flink('output/' + m + '_forecast_tidy.csv', pre)} faylından oxunur.</p>",
         html.h2("oxu", 1, "Cədvəlləri necə oxumalı"),
         "<ul><li><strong>Son faktiki</strong> — 2025-ci il və ya ondan əvvəlki son müşahidə.</li>"
         "<li><strong>Artım 2025→30</strong> — səviyyə və indekslər üçün orta illik artım (%), dərəcə və paylar üçün "
         "2030 ilə son faktiki il arasındakı fərq (faiz bəndi, f.b.).</li>"
         "<li><strong>Zolaq 2030</strong> — modulun simulyasiyasından 5-ci və 95-ci faizlər; zolaq qurulmayan "
         "komponentlərdə «—».</li>"
         "<li><strong>tənlik:</strong> (göstəricinin adı altında) — komponenti proqnozlaşdıran və ya ona təsir edən tənliklər; kod üzərinə "
         "klikləyin — tam reqressiya nəticəsi açılır.</li>"
         + (f'<li><i class="imp">Kursivlə</i> yazılmış dəyərlər — {IMP.lower()}: müşahidə yoxdur, qonşu illərdən '
          f"doldurulub (bu modulda {core.num(n_imp, 0)} belə nöqtə var).</li></ul>" if n_imp else
          "<li>Bu modulun cədvəllərində doldurulmuş (interpolyasiya edilmiş) nöqtə yoxdur.</li></ul>"),
         f'<p class="dl">Bütün cədvəl bir faylda: {html.flink("output/" + m + "_forecast_tidy.csv", pre)} · '
         f'kataloq: {html.flink("output/" + m + "_indicator_catalog.csv", pre)} · öz seçiminizlə hesabat: '
         f'<a href="{pre}{v2nav.PANEL_REPORT}">İş panelində hesabat qurucusu →</a></p>',
         html.h2("cedveller", 2, "Qruplar üzrə cədvəllər"),
         '<div class="fc-tools" hidden><button type="button" class="fc-expand" data-open="1">Bütün qrupları aç</button>'
         '<button type="button" class="fc-expand" data-open="0">Hamısını bağla</button></div>']
    for i, (g, rows) in enumerate(groups.items(), 1):
        gid = f"qrup-{i}"
        op = " open" if i == 1 else ""
        o.append(f'<details class="fc-group" id="{gid}"{op}><summary><span class="fc-title">{esc(g)}</span> '
                 f'<span class="grp-n">{core.num(len(rows), 0)} göstərici</span></summary>'
                 + group_table(rows, idx, known, m) + "</details>")
    nf = not_forecast_list(m)
    if nf:
        o += [html.h2("proqnozsuz", 3, "Proqnozlaşdırılmayan komponentlər"), nf]
        secs.append(("proqnozsuz", "Proqnozlaşdırılmayan komponentlər"))
    return "\n".join(o), secs
