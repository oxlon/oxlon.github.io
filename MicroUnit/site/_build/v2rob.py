"""v2rob.py — robustness pieces: verdict counts, fragile equations, tornado charts of the coefficient
sensitivity (FRx_coef_sensitivity.csv). Used by every FR page (§ Dayanıqlıq) and by dayaniqliq.html."""
from collections import Counter

from . import core, html, figs, v2data as V, v2eq
from .core import esc

FAIL_COL = ("failed_tests_az", "failed_tests", "failed_test")


def failed_map(m):
    r = V.robustness(m)
    col = next((c for c in FAIL_COL if c in r.columns), None)
    eqc = "equation" if "equation" in r.columns else r.columns[0]
    if not col:
        return {}
    return {str(a): V.az(str(b)) for a, b in zip(r[eqc], r[col]) if isinstance(b, str) and b.strip() not in ("", "—")}


def stats(m):
    eqs = V.equations(m)
    allc = Counter(V.verdict_of(e) for e in eqs)
    used = [e for e in eqs if e.get("used_in_forecast")]
    usedc = Counter(V.verdict_of(e) for e in used)
    return {"n": len(eqs), "all": allc, "n_used": len(used), "used": usedc,
            "fragile": [e for e in used if V.verdict_of(e) == "qeyri-stabil"],
            "fragile_all": sum(1 for e in eqs if V.verdict_of(e) == "qeyri-stabil")}


def count_strip(st):
    items = [(st["n"], "tənlik cəmi")] + [(st["all"].get(k, 0), k) for k in V.VERDICTS] + \
            [(st["n_used"], "proqnozda istifadə olunur"), (st["used"].get("stabil", 0), "onlardan stabil"),
             (len(st["fragile"]), "onlardan qeyri-stabil")]
    return '<ul class="count-strip cs-many">' + "".join(
        f'<li><span class="cs-n">{core.num(n, 0)}</span><span class="cs-l">{esc(lab)}</span></li>' for n, lab in items) + "</ul>"


def fragile_table(m, st, pre, limit=None):
    fm = failed_map(m)
    page = f"{pre}fr/{m.lower()}-tenlikler.html"
    rows = []
    for e in st["fragile"][:limit]:
        h = e.get("holdout") or {}
        rows.append([f'<a href="{page}#{v2eq.anchor(e["id"])}">{esc(V.az(e.get("title_az") or e["id"]))}</a>'
                     f'<span class="cid">{esc(e["id"])}</span>',
                     esc(V.az(e.get("subtask") or "")), esc(fm.get(e["id"], V.az((e.get("robustness") or {}).get("notes_az") or ""))),
                     v2eq.u_txt(h.get("theil_u_rw")), v2eq.u_txt(h.get("theil_u_const"))])
    if not rows:
        return ("<p>Proqnozda istifadə olunan tənliklərin heç biri «qeyri-stabil» deyil.</p>")
    return html.table(["Tənlik", "Alt-tapşırıq", "Hansı yoxlamadan keçmir", "U: təsadüfi gəzişmə", "U: sabit artım"], rows,
                      cls="tbl tbl-dense", cols=["c-wide", "c-text", "c-text", "c-num", "c-num"])


def fragile_block(m, st, pre):
    """The fragile-equation table, collapsible when long (open when ≤ 8 rows)."""
    n = len(st["fragile"])
    head = "Proqnozda istifadə olunan, lakin qeyri-stabil tənliklər"
    if n <= 8:
        return html.h3(head) + fragile_table(m, st, pre)
    return (f'<details class="fc-group"><summary><span class="fc-title">{head}</span> '
            f'<span class="grp-n">{core.num(n, 0)} tənlik — açmaq üçün klikləyin</span></summary>'
            + fragile_table(m, st, pre) + "</details>")


def _short(s, n=52):
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def tornado_spec(sub):
    sub = sub.sort_values("swing", ascending=False)
    labels = [f"{_short(V.az(c))} · {e.split('.', 1)[-1]}" for c, e in zip(sub["coef"], sub["eq"])]
    lay = {"height": max(300, 30 * len(labels) + 120), "autosize": True, "paper_bgcolor": "rgba(0,0,0,0)",
           "plot_bgcolor": "rgba(0,0,0,0)", "font": {"family": figs.FONT, "size": 12.5, "color": "#1c1e21"},
           "separators": ", ", "margin": {"l": 300, "r": 26, "t": 52, "b": 50}, "barmode": "overlay",
           "hovermode": "y unified", "bargap": 0.35,
           "legend": {"orientation": "h", "y": 1.02, "yanchor": "bottom", "x": 0, "xanchor": "left",
                      "font": {"size": 12, "color": figs.GREY}},
           "xaxis": {"title": {"text": "2030 səviyyəsinə təsir, Əsas ssenaridən fərq, %"}, "gridcolor": "#eceff1",
                     "zeroline": True, "zerolinecolor": "#80868b", "ticksuffix": " %"},
           "yaxis": {"autorange": "reversed", "automargin": True}}
    data = [{"type": "bar", "orientation": "h", "y": labels, "x": figs._clean(sub["lo"]), "name": "əmsal −1 standart xəta",
             "marker": {"color": "#9aa0a6"}, "hovertemplate": "%{x:.3f} %<extra>−1 standart xəta</extra>"},
            {"type": "bar", "orientation": "h", "y": labels, "x": figs._clean(sub["hi"]), "name": "əmsal +1 standart xəta",
             "marker": {"color": figs.ACCENT}, "hovertemplate": "%{x:.3f} %<extra>+1 standart xəta</extra>"}]
    return {"data": data, "layout": lay}


def tornados(m, n_comp=2, top=10):
    try:
        s = V.sensitivity(m)
    except FileNotFoundError:
        return [], 0
    s = s[s.swing > 1e-9]
    # the module's headline indicators: most sensitivity rows first, ties in file order (FR1: real GDP first)
    first = {c: i for i, c in reversed(list(enumerate(s["comp"])))}
    size = s.groupby("comp").size()
    comps = sorted(size.index, key=lambda c: (-int(size[c]), first[c]))[:n_comp]
    out = []
    for c in comps:
        sub = s[s.comp == c].sort_values("swing", ascending=False).head(top)
        label = V.az(sub.comp_label.iloc[0])
        out.append((c, label, tornado_spec(sub), len(s[s.comp == c])))
    return out, len(s)


def section(m, n, pre="../"):
    """The § Dayanıqlıq section of an FR page."""
    st = stats(m)
    reg = V.registry(m)
    o = [html.h2("dayaniqliq", n, "Dayanıqlıq"),
         "<p>Dayanıqlıq — tənliyin əmsallarının nümunə dəyişəndə (illər əlavə olunduqda, bir il çıxarıldıqda, "
         "struktur qırılma ehtimal olunan illərdə) nə qədər sabit qaldığıdır. Hər tənliyə üç hökmdən biri verilir: "
         f'{html.pill("done", "stabil")}, {html.pill("partial", "qismən stabil")}, {html.pill("gap", "qeyri-stabil")}. '
         f'Qayda bütün modullar üçün eynidir: <a href="{pre}dayaniqliq.html#qayda">Dayanıqlıq səhifəsi</a>.</p>',
         count_strip(st),
         fragile_block(m, st, pre),
         f'<p>Bütün {core.num(st["fragile_all"], 0)} qeyri-stabil tənlik (alternativlər daxil) və hər birinin tam '
         f'yoxlamaları: <a href="{m.lower()}-tenlikler.html#siyahi">Tənliklər</a> (süzgəc: «Hökm»).</p>']
    tor, nrows = tornados(m)
    if tor:
        o.append(html.h3("Əmsallara həssaslıq (tornado qrafiki)"))
        o.append(f"<p>Hər zolaq bir əmsalı ±1 standart xəta dəyişdikdə göstəricinin 2030 səviyyəsinin Əsas ssenaridən "
                 f"neçə faiz fərqləndiyini göstərir (digər hər şey sabit). Ən uzun zolaqlar — proqnozun ən çox asılı "
                 f"olduğu əmsallardır. Mənbə: {html.flink('output/' + m + '_coef_sensitivity.csv', pre)} "
                 f"({core.num(nrows, 0)} sətir).</p>")
        for c, label, spec, k in tor:
            o.append(html.fig(f"tor-{m.lower()}-{c.replace(':', '-')}", f"{label}: ən təsirli {min(10, k)} əmsal",
                              spec, "Boz — əmsal 1 standart xəta az, yaşıl — 1 standart xəta çox.",
                              "2030, Əsas ssenari."))
    if reg.get("verdict_rule_az"):
        o.append(f'<details class="rule"><summary>Formal qayda (reyestrdən)</summary><p>{esc(V.az_numbers(reg["verdict_rule_az"]))}</p></details>')
    return "\n".join(o)
