"""fr12_imp.py — FR12 § Doldurulmuş məlumat: the gap-filled points of FR12_series_filled.csv drawn as
hollow markers on dashed segments (legend «Doldurulmuş (interpolyasiya)») and listed in italics."""
from collections import Counter

from . import core, html, figs, v2data as V
from .core import esc
from .fr12_data import filled

IMP = figs.IMP_NAME


def fc_line(i, scen="Baseline"):
    t = V.tidy("FR12")
    t = t[(t.id == i) & (t.scenario == scen) & t.is_forecast.astype(bool)].sort_values("year")
    return t


def series_fig(ids, ytitle, hfmt):
    data = []
    cols = [figs.ACCENT, figs.GREY]
    cat = V.catalog("FR12").set_index("id")
    for k, i in enumerate(ids):
        fl = filled(i)
        lab = V.az(cat.label_az.get(i, i))
        col = cols[k % 2]
        data += figs.imputed_series(fl.index, fl.value, fl.imputed, f"{lab} — faktiki", color=col, hfmt=hfmt,
                                    rank=1000 + 10 * k, show_imp_legend=(k == 0))
        f = fc_line(i)
        if len(f):
            if k == 0 and f.lower_5.notna().any():
                data = figs.band(f.year, f.lower_5, f.upper_95) + data
            x = [int(fl.index.max())] + [int(y) for y in f.year]
            data.append(figs.line(x, [fl.value.iloc[-1]] + list(f.value), f"{lab} — Əsas ssenari", col, "dot", 2,
                                  hfmt=hfmt, rank=1005 + 10 * k))
    lay = figs.layout(ytitle, x0=2019, dtick=1)
    lay["shapes"][0]["x0"] = 2024.5
    lay["shapes"][1]["x0"] = lay["shapes"][1]["x1"] = 2024.5
    lay["annotations"][0]["x"] = 2024.6
    lay["annotations"][0]["text"] = "Cari qiymətləndirmə 2025, proqnoz 2026–2030"
    return figs.spec(data, lay)


def history_table(ids):
    """Observed and gap-filled history, 2019–2025, of the national series; imputed cells in italics."""
    cat = V.catalog("FR12").set_index("id")
    years = list(range(2019, 2026))
    rows = []
    for i in ids:
        fl = filled(i)
        d = V.decimals(list(fl.value))
        cells = []
        for y in years:
            if y in fl.index:
                r = fl.loc[y]
                txt = core.num(r.value, d)
                cells.append(f'<i class="imp" title="{IMP}: {esc(V.az(r.method_az))}">{txt}</i>' if r.imputed else txt)
            else:
                cells.append("—")
        rows.append([f'{esc(V.az(cat.label_az.get(i, i)))}<span class="cid">{esc(i)}</span>'] + cells)
    return html.table(["Göstərici"] + [str(y) for y in years], rows, cls="tbl tbl-dense",
                      cols=["c-wide"] + ["c-num"] * len(years))


def listing():
    f = core.csv("FR12_series_filled.csv")
    im = f[f.imputed.astype(bool)].sort_values(["id", "year"])
    cat = V.catalog("FR12").set_index("id")
    rows = []
    for r in im.itertuples(index=False):
        d = V.decimals([r.value])
        rows.append([f'{esc(V.az(cat.label_az.get(r.id, r.id)))}<span class="cid">{esc(r.id)}</span>', str(int(r.year)),
                     f'<i class="imp" title="{IMP}">{core.num(r.value, d)}</i>', esc(V.az(r.method_az)),
                     esc(str(r.neighbours_used).replace(";", ", ")) if isinstance(r.neighbours_used, str) else "—"])
    return html.table(["Göstərici", "İl", "Doldurulmuş dəyər", "Üsul", "İstifadə olunan qonşu illər"], rows,
                      cls="tbl tbl-dense", cols=["c-wide", "c-tight", "c-num", "c-text", "c-tight"])


def section(n, pre="../"):
    f = core.csv("FR12_series_filled.csv")
    im = f[f.imputed.astype(bool)]
    by_m = Counter(V.az(x) for x in im.method_az)
    by_y = Counter(int(y) for y in im.year)
    g = core.csv("FR12_gapfill_sensitivity.csv")
    mx = g.rel_diff_pct.abs().max() if "rel_diff_pct" in g else float("nan")
    o = [html.h2("doldurulmus", n, "Doldurulmuş məlumat (boşluqlar)"),
         "<p>DSK bəzi illəri nəşr etməyib (fəaliyyət qrupları üzrə 2021, NACE bölmələri üzrə 2021–2023 və s.). "
         f"Bu boşluqlar qonşu illərdən interpolyasiya ilə doldurulub və saytın hər yerində eyni cür göstərilir: "
         f'qrafiklərdə <span class="imp-key">◯</span> boş marker və qırıq xətt (legenddə «{IMP}»), cədvəllərdə '
         f'<i class="imp">kursiv</i>. Cəmi {core.num(len(im), 0)} nöqtə, {core.num(im.id.nunique(), 0)} sırada: '
         + ", ".join(f"{esc(k)} — {core.num(v, 0)}" for k, v in by_m.most_common()) + "; illər üzrə: "
         + ", ".join(f"{y} — {core.num(v, 0)}" for y, v in sorted(by_y.items())) + ".</p>",
         "<p>Doldurulmuş nöqtələr tənliklərin qiymətləndirilməsinə daxil edilmir (yalnız müşahidə edilmiş illər); "
         "onlar qrafiklərdə və bölmə cəmlərinin uzlaşdırılmasında istifadə olunur. Həssaslıq yoxlaması "
         f"({html.flink('output/FR12_gapfill_sensitivity.csv', pre)}): doldurulmuş illəri daxil etmək əmsalları ən çox "
         f"{core.num(mx, 1)} % dəyişir.</p>",
         html.fig("fr12_imp_entry", "Giriş və çıxış əmsalları, bütün sahələr: doldurulmuş 2021",
                  series_fig(["fr12:act:entry:ALL", "fr12:act:exit:ALL"], "əmsal, %", ".2f"),
                  f"Boş marker və qırıq xətt — {IMP.lower()}; nöqtəli xətt — Əsas ssenari proqnozu, zolaq — "
                  "giriş əmsalının 5–95 % zolağı.", "Mənbə: FR12_series_filled.csv, FR12_forecast_tidy.csv."),
         html.fig("fr12_imp_flows", "Yeni qeydiyyatlar və ləğv edilənlər, bütün sahələr",
                  series_fig(["fr12:act:new:ALL", "fr12:act:exits:ALL"], "vahid", ",.0f"),
                  "2021-in dəyəri fəaliyyət qrupları üzrə doldurulmuş komponentlərin cəmidir.",
                  "Mənbə: FR12_series_filled.csv."),
         html.h3("Bütün sahələr üzrə sıralar: müşahidə və doldurulmuş illər"),
         history_table(["fr12:act:N:ALL", "fr12:act:new:ALL", "fr12:act:exits:ALL", "fr12:act:entry:ALL",
                        "fr12:act:exit:ALL"]),
         f'<p class="eq-na"><i class="imp">Kursiv</i> — {IMP.lower()}; «—» — həmin il üçün müşahidə də, '
         "doldurulmuş dəyər də yoxdur.</p>",
         f'<details class="fc-group"><summary><span class="fc-title">Bütün doldurulmuş nöqtələr</span> '
         f'<span class="grp-n">{core.num(len(im), 0)} nöqtə</span></summary>{listing()}</details>']
    return "\n".join(o)
