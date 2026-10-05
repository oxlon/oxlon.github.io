"""pg_rob.py — dayaniqliq.html: robustness of every module's equations, the verdict rule in plain
Azerbaijani, counts and the fragile equations per FR."""
from . import core, html, figs, v2data as V, v2rob
from .core import esc

NAMES = {"FR1": "Sektorlar və bazarlar", "FR3": "Orta aylıq əmək haqqı", "FR4": "Məşğulluq",
         "FR5": "Pullu xidmətlər", "FR10": "Müəssisələr: maliyyə, effektivlik, bazar payı", "FR12": "Rəqabət mühiti"}
COL = {"stabil": "#1e7e34", "qismən stabil": "#9a6700", "qeyri-stabil": "#b3261e"}

RULE = ("<ol class=\"rule-list\">"
        "<li><strong>Rekursiv qiymətləndirmə.</strong> Tənlik əvvəlcə ən qısa mümkün nümunədə (k + 5 müşahidə) "
        "qiymətləndirilir, sonra hər dəfə bir il əlavə olunur — ta tam nümunəyə qədər. Proqnozda istifadə olunan hər "
        "əmsalın işarəsi bu yol boyu dəyişməməlidir.</li>"
        "<li><strong>Bir ili çıxarmaqla.</strong> Tənlik hər dəfə bir il çıxarılmaqla yenidən qiymətləndirilir; "
        "əmsalların işarəsi yenə dəyişməməlidir — nəticə tək bir ilin üzərində dayanmamalıdır.</li>"
        "<li><strong>Struktur qırılma (Chow).</strong> Nümunə ortada, 2015-ci il (devalvasiya) və 2020-ci il "
        "(pandemiya) nöqtələrində ikiyə bölünür; iki hissənin əmsalları statistik fərqlənməməlidir.</li>"
        "<li><strong>CUSUM.</strong> Rekursiv qalıqların toplanmış cəmi gözlənilən zolaqdan çıxmamalıdır.</li></ol>"
        "<div class=\"box\"><p>"
        "<span class=\"pill pill-done\">stabil</span> — bütün işarələr hər iki yoxlamada sabitdir və bütün Chow/CUSUM "
        "testlərinin p-dəyəri 0,05-dən böyükdür. "
        "<span class=\"pill pill-gap\">qeyri-stabil</span> — rekursiv yolun son yarısında hansısa əmsalın işarəsi "
        "dəyişir və ya hər hansı Chow testinin p-dəyəri 0,01-dən kiçikdir (güclü struktur qırılma). "
        "<span class=\"pill pill-partial\">qismən stabil</span> — qalan bütün hallar: məsələn, işarə yalnız "
        "qısa nümunənin əvvəlində dəyişir və ya testin p-dəyəri 0,01 ilə 0,05 arasındadır. Rekursiv yol qurula "
        "bilmirsə (müşahidə azdır), hökm «stabil» ola bilməz.</p></div>"
        "<p><strong>Bu nə deməkdir.</strong> «Qeyri-stabil» tənlik səhv demək deyil: illik məlumat qısadır, 2015 və "
        "2020 şokları böyükdür. Lakin belə tənliyə əsaslanan proqnozun qeyri-müəyyənliyi zolaqdan da geniş ola bilər; "
        "ona görə həmin əmsalları İş panelinin ssenari qurucusunda dəyişib nəticəyə təsirini yoxlamaq tövsiyə olunur.</p>")


def overview_fig(rows):
    mods = [m for m, _ in rows]
    data = []
    for k in V.VERDICTS:
        vals = [st["all"].get(k, 0) / st["n"] * 100 if st["n"] else 0 for _, st in rows]
        data.append({"type": "bar", "orientation": "h", "y": mods, "x": figs._clean(vals), "name": k,
                     "marker": {"color": COL[k], "line": {"color": "#ffffff", "width": 2}},
                     "hovertemplate": "%{x:.0f} %<extra>" + k + "</extra>"})
    lay = {"height": 340, "autosize": True, "barmode": "stack", "paper_bgcolor": "rgba(0,0,0,0)",
           "plot_bgcolor": "rgba(0,0,0,0)", "font": {"family": figs.FONT, "size": 13, "color": "#1c1e21"},
           "separators": ", ", "margin": {"l": 64, "r": 26, "t": 52, "b": 46}, "hovermode": "y unified",
           "legend": {"orientation": "h", "y": 1.02, "yanchor": "bottom", "x": 0, "xanchor": "left",
                      "font": {"size": 12, "color": figs.GREY}, "traceorder": "normal"},
           "xaxis": {"title": {"text": "tənliklərin payı, %"}, "range": [0, 100], "ticksuffix": " %",
                     "gridcolor": "#eceff1"},
           "yaxis": {"autorange": "reversed"}}
    return {"data": data, "layout": lay}


def build(texts):
    rows = [(m, v2rob.stats(m)) for m in V.MODULES]
    secs = [("qayda", "Hökm qaydası"), ("icmal", "Bütün modullar üzrə")] + [(m.lower(), m) for m in V.MODULES]
    tbl = []
    for m, st in rows:
        tbl.append([f'<a href="fr/{m.lower()}.html#dayaniqliq">{m}</a> {esc(NAMES[m])}', core.num(st["n"], 0)]
                   + [core.num(st["all"].get(k, 0), 0) for k in V.VERDICTS]
                   + [core.num(st["n_used"], 0)] + [core.num(st["used"].get(k, 0), 0) for k in V.VERDICTS])
    o = ["<h1>Modellərin dayanıqlığı</h1>",
         '<p class="lead-in">Proqnoz yalnız onu verən tənliklər qədər etibarlıdır. Bu səhifə altı modulun bütün '
         f'{core.num(sum(st["n"] for _, st in rows), 0)} tənliyinin dayanıqlıq yoxlamalarını bir yerdə göstərir: '
         "hansı tənliklər nümunə dəyişəndə sabit qalır, hansılar qalmır və bu, proqnoza necə təsir edir.</p>",
         html.h2("qayda", 1, "Hökm qaydası — sadə dillə"), RULE,
         html.h2("icmal", 2, "Bütün modullar üzrə"),
         html.fig("rob_overview", "Tənliklərin dayanıqlıq hökmləri üzrə bölgüsü", overview_fig(rows),
                  "Bütün qiymətləndirilmiş tənliklər (alternativlər daxil); yaşıl — stabil, sarı — qismən, qırmızı — qeyri-stabil.",
                  "Mənbə: FRx_equations.json."),
         html.table(["Modul", "Tənlik", "stabil", "qismən stabil", "qeyri-stabil", "Proqnozda",
                     "onlardan stabil", "qismən", "qeyri-stabil"], tbl,
                    cols=["c-wide"] + ["c-num"] * 8)]
    for i, (m, st) in enumerate(rows, 3):
        o += [html.h2(m.lower(), i, f"{m} — {NAMES[m]}"), v2rob.count_strip(st),
              v2rob.fragile_block(m, st, ""),
              f'<p>Tornado qrafiki və ətraflı: <a href="fr/{m.lower()}.html#dayaniqliq">{m} səhifəsinin «Dayanıqlıq» '
              f'bölməsi</a> · bütün tənliklər: <a href="fr/{m.lower()}-tenlikler.html">{m} tənlikləri</a>.</p>']
    return "\n".join(o), secs
