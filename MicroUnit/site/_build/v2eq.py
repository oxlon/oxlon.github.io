"""v2eq.py — one equation card: <details> with a performance strip in the <summary>, and the full
regression output inside (works without JavaScript; the two charts render when the card opens)."""
import re

from . import core, html, v2data as V, v2text, v2eqfig
from .core import esc
from .v2data import pval, isnum
from .v2eqparts import cf, coef_table, fit_table, diag_table, diff_form, restrictions


def anchor(eq_id):
    return "eq-" + re.sub(r"[^A-Za-z0-9_-]+", "-", eq_id)


def verdict_pill(vd):
    if vd in V.VERDICT_CLS:
        return html.pill(V.VERDICT_CLS[vd], vd)
    return html.pill("neutral", "hökm yoxdur")


def u_txt(u):
    if not isnum(u):
        return "—"
    cls = "skill-pos" if u < 1 else "skill-neg"
    return f'<span class="{cls}">{core.num(u, 2)}</span>'


def perf(e):
    f, d, s = e.get("fit") or {}, e.get("diagnostics") or {}, e.get("sample") or {}
    h = e.get("holdout") or {}
    items = [("R²", cf(f.get("r2"), 3)), ("düz. R²", cf(f.get("r2_adj"), 3)),
             ("n", core.num(s.get("n"), 0) if isnum(s.get("n")) else "—"), ("DW", cf(d.get("dw"), 2)),
             ("kointeqrasiya p", pval(d.get("eg_coint_p"))),
             ("U: təsadüfi gəzişmə", u_txt(h.get("theil_u_rw"))), ("U: sabit artım", u_txt(h.get("theil_u_const")))]
    return '<span class="perf">' + "".join(f'<span class="pf"><span class="pf-k">{k}</span> {v}</span>'
                                           for k, v in items) + "</span>"


def robust_block(e):
    r = e.get("robustness") or {}
    nr = r.get("null_reasons") or {}
    rows = []
    for c in r.get("chow_tests") or []:
        lab = V.az(str(c.get("label") or c.get("break_year")))
        rows.append([f"Chow struktur qırılma testi — {esc(lab)}", f'{cf(c.get("f"), 2)} / {pval(c.get("p"))}'])
    if not rows and nr.get("chow"):
        rows.append(["Chow struktur qırılma testi", f'<span class="na" title="{esc(V.az(nr["chow"]))}">—</span>'])
    if isnum(r.get("cusum_p")) or nr.get("cusum_p"):
        rows.append(["CUSUM (rekursiv qalıqlar), p", pval(r.get("cusum_p")) if isnum(r.get("cusum_p"))
                     else f'<span class="na" title="{esc(V.az(nr["cusum_p"]))}">—</span>'])
    rec = r.get("recursive") or {}
    if rec.get("years"):
        rows.append(["Rekursiv qiymətləndirmə (genişlənən pəncərə)",
                     f'{rec["years"][0]}–{rec["years"][-1]} ({len(rec["years"])} pəncərə)'])
    for k, rg in (r.get("loo_year_range") or {}).items():
        if rg and len(rg) == 2:
            rows.append([f"Bir ili çıxarmaqla: <code>{esc(k)}</code>", f"{cf(rg[0])} … {cf(rg[1])}"])
    o = [html.table(["Yoxlama", "Nəticə"], rows, cls="tbl tbl-dense tbl-kv", cols=["c-text", "c-num"]) if rows else ""]
    note = V.az(r.get("notes_az") or "")
    o.append(f"<p>Hökm: {verdict_pill(r.get('verdict'))}" + (f" — {esc(note)}" if note else "") + "</p>")
    if r.get("stability_form"):
        o.append(f'<p class="eq-na">Sabitlik testlərinin forması: {esc(V.az(r["stability_form"]))}.</p>')
    return "<h4>Dayanıqlıq</h4>" + "".join(o)


def holdout_block(e):
    h = e.get("holdout")
    if not h:
        return ("<h4>Nümunədən kənar yoxlama</h4><p>Bu tənlik üçün ayrıca nümunədən kənar yoxlama aparılmayıb "
                "(modulun sistem səviyyəsində yoxlaması FR səhifəsindədir).</p>")
    yrs = h.get("years") or []
    rows = [["Kəsim ili", esc(h.get("cut"))],
            ["Yoxlama illəri", f"{yrs[0]}–{yrs[-1]}" if yrs else "—"],
            ["RMSE", cf(h.get("rmse"), 3)],
            ["Theil U: təsadüfi gəzişməyə qarşı", u_txt(h.get("theil_u_rw"))],
            ["Theil U: sabit artıma qarşı", u_txt(h.get("theil_u_const"))],
            ["Diebold–Mariano p (təsadüfi gəzişmə)", pval(h.get("dm_p_rw"))]]
    if isnum(h.get("dm_p_const")):
        rows.append(["Diebold–Mariano p (sabit artım)", pval(h.get("dm_p_const"))])
    for k, lab in (("mode_az", "Üsul"), ("units_az", "Vahid"), ("benchmarks_az", "Etalonlar"), ("note_az", "Qeyd"),
                   ("measure", "Ölçü"), ("rule", "Qayda")):
        if isinstance(h.get(k), str) and h[k].strip():
            rows.append([lab, esc(V.az(h[k]))])
    return ("<h4>Nümunədən kənar yoxlama</h4><p>Theil U &lt; 1 — tənlik etalonu üstələyir (yaşıl).</p>"
            + html.table(["Göstərici", "Dəyər"], rows, cls="tbl tbl-dense tbl-kv", cols=["c-text", "c-num"]))


def card(e, pre):
    eid = e["id"]
    a = anchor(eid)
    vd = V.verdict_of(e)
    used = bool(e.get("used_in_forecast"))
    chips = [verdict_pill(vd), html.pill("done" if used else "neutral",
                                         "proqnozda istifadə olunur" if used else "alternativ / yoxlama")]
    if e.get("synthetic"):
        chips.append(html.pill("gap", "SİNTETİK"))
    dep = e.get("dependent") or {}
    s = e.get("sample") or {}
    meta = (f'<p class="eq-meta">Asılı dəyişən: <code>{esc(dep.get("code"))}</code> — {esc(V.az(dep.get("label_az") or ""))} · '
            f'Üsul: {esc(V.az(e.get("estimator") or ""))} · Kovariasiya: {esc(V.az(v2text.cov(e.get("cov_type"))))} · '
            f'Nümunə: {esc(s.get("start"))}–{esc(s.get("end"))}</p>')
    figs = []
    fs = v2eqfig.fitted(e)
    if fs:
        figs.append(html.fig(a + "-fit", "Faktiki və qiymətləndirilmiş dəyərlər; qalıqlar", fs,
                             "Yuxarı panel — asılı dəyişən, aşağı panel — qalıq (eyni illər).", "Mənbə: tənlik reyestri."))
    rs = v2eqfig.recursive(e)
    if rs:
        figs.append(html.fig(a + "-rec", "Rekursiv əmsallar (genişlənən pəncərə, ±2 standart xəta)", rs,
                             "Nöqtəli xətt — tam nümunə qiymətləndirməsi.", "Mənbə: tənlik reyestri."))
    notes = V.az(e.get("notes_az") or "")
    summ = V.az_long(v2text.summary(e.get("summary_text") or ""))
    body = [meta,
            "<h4>Əmsallar</h4>", coef_table(e),
            '<div class="eq-two"><div><h4>Uyğunluq</h4>' + fit_table(e) + "</div><div><h4>Diaqnostika</h4>"
            + diag_table(e) + "</div></div>",
            diff_form(e), restrictions(e), robust_block(e), holdout_block(e), "".join(figs),
            (f"<h4>Qeydlər</h4><p>{esc(notes)}</p>" if notes else ""),
            (f'<details class="eq-text"><summary>Mətn şəklində tam reqressiya nəticəsi</summary>'
             f'<button type="button" class="copy-btn" data-copy="txt-{a}">Kopyala</button>'
             f'<pre id="txt-{a}">{esc(summ)}</pre></details>' if summ else "")]
    attrs = (f'id="{a}" data-sub="{esc(V.az(e.get("subtask") or ""))}" data-used="{1 if used else 0}" '
             f'data-verdict="{esc(vd)}"')
    return (f'<details class="eq" {attrs}><summary><span class="eq-head"><span class="eq-title">'
            f'{esc(V.az(e.get("title_az") or eid))}</span> <code class="eq-id">{esc(eid)}</code></span>'
            f'<span class="eq-chips">{" ".join(chips)}</span>{perf(e)}</summary>'
            f'<div class="eq-body">{"".join(body)}</div></details>')
