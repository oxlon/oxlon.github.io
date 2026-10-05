"""fr4.py — FR4 page: employment."""
from . import html, req, common
from .core import v, esc
from .common import SCEN, u_cell
from . import fr4_data as D


def build(t, pre="../"):
    d = D.load()
    ic = d["ident"]
    o = ["<h1>FR4 — Əhalinin məşğulluq göstəriciləri: təhlil və beşillik proqnoz</h1>",
         html.kicker("FR4", "FR4.ipynb", "docs/FR4_Methodology.md"),
         common.intro("Məşğulların sayı və artım sürəti — iqtisadi fəaliyyət növləri, dövlət və qeyri-dövlət sektoru, "
                      "büdcə və qeyri-büdcə təşkilatları, neft və qeyri-neft sektoru üzrə — 2030-a qədər, FR1-in üç "
                      "ssenarisi ilə uzlaşdırılmış şəkildə."),
         html.h2("teleb", 1, "Tələb"), req.block("FR4", t),
         html.h2("model", 2, "Model və seçim səbəbi"),
         "<p>Ümumi məşğulluq və iqtisadi fəal əhali FR1-dən gəlir; FR4 onları bölüşdürür. Sektor tərkibi <strong>pay "
         "sistemi</strong> ilə verilir (paylar müsbət və cəmi bir), sürücü olaraq sektorun buraxılışı işlədilir. 2020-dən "
         "əvvəlki məlumatda heç bir sürücü sabit payları nümunədən kənar üstələmədiyi üçün əsas yol sabit paylarla "
         "kiçik birləşdirilmiş buraxılış elastikliyinin bərabər çəkili birləşməsidir (proqnoz kombinasiyası). Qrup "
         "daxilində bölgü, dövlət/qeyri-dövlət, büdcə/qeyri-büdcə və neft/qeyri-neft ayrı bloklardır; neft "
         "məşğulluğu vergi uçotu (DVX) əsasında neft hasilatı ilə əlaqələndirilir.</p>"
         "<p>Asılı dəyişənin gecikməsi, AR/ARIMA komponenti yoxdur; səviyyə əlaqələri DOLS ilə, hər biri həm də "
         "birinci fərqlərdə qiymətləndirilir və fərq formasının 95 % etibar intervalından kənara çıxan səviyyə əmsalı "
         "işlədilmir (uyğunluq qaydası). Rədd edilmiş spesifikasiyalar <code>FR4_rejected_specifications.csv</code> "
         "faylındadır.</p>",
         html.h2("data", 3, "Məlumat"),
         "<p>İş kitabında sektorlar üzrə məşğulluq olmadığından DSK-dan əlavə cədvəllər toplanıb: fəaliyyət növləri üzrə "
         f"məşğullar ({int(d['hist'].index.min())}–{int(d['hist'].index.max())}), muzdlu işçilər, mülkiyyət formaları "
         "üzrə bölgü, Dövlət Məşğulluq Agentliyinin göstəriciləri; üstəlik iş kitabının DVX sətirləri (əmək "
         "müqavilələri, büdcə təşkilatları, neft sektoru). Mənbələrin uzlaşdırılması və aşkarlanan məlumat "
         "problemləri (məsələn, Məşğulluq Agentliyinin sıralarında 2023 qırılması, iş kitabındakı iki fərqli işçi sayı) "
         f"<a href=\"{pre}data.html#integrity\">Məlumat mənbələri</a> səhifəsində. "
         f"{v(int(ic.passed.sum()), 0)}/{v(len(ic), 0)} eynilik və lövbər yoxlaması keçir.</p>"]
    o += results(d)
    o += check(d)
    o += limits()
    o.append(common.files_section(7, "FR4", pre))
    return "\n".join(o)


def _avg_row(d, var):
    a = d["avg"].loc[var]
    return [esc(D.GRP_AZ[var]), v(a.point, 2, sign=True), common.band_txt(a.q05, a.q95, 2)]


def results(d):
    o = [html.h2("results", 4, "Nəticələr"),
         html.fig("fr4_total", "Məşğul əhali: faktiki və proqnoz", D.total_fig(d),
                  "2025 dəyəri FR1-in lövbəridir; zolaq tarixi qalıq yolları, parametr çəkilişləri və FR1-in makro "
                  "çəkilişlərini birləşdirən simulyasiyadan qurulub.", "Pəncərə 2000–2030."),
         html.h3("Qruplar üzrə orta illik artım, 2026–2030 (Əsas ssenari)")]
    a = d["avg"]
    grp = sorted([k for k in a.index if k in D.GRP_AZ and k[0].isupper()], key=lambda k: -a.loc[k, "point"])
    o.append(html.table(["Qrup", "% illik", "5–95 % zolağı"], [_avg_row(d, k) for k in grp],
                        cols=["c-wide", "c-num", "c-text"]))
    o.append(html.fig("fr4_groups", "Fəaliyyət qrupları üzrə orta illik artım, 2026–2030", D.groups_fig(d),
                      "Sektor tərkibi iqtisadiyyata zəif reaksiya verir: qruplar arasındakı fərq kiçikdir və zolaqlar "
                      "geniş.", "Mənbə: FR4_fan_employment.csv (orta artım sətirləri)."))
    I = d["inst"]
    b25 = I[(I.scenario == "Baseline") & (I.year == 2025)].iloc[0]
    b30 = I[(I.scenario == "Baseline") & (I.year == 2030)].iloc[0]
    rows = []
    for var, col in (("state", "state"), ("budget organisations", "budget organisations"),
                     ("oil, tax-record basis", "oil, tax-record basis")):
        av = d["avg"].loc[var]
        rows.append([esc(D.GRP_AZ[var]), v(b25[col], 1), v(b30[col], 1), v(av.point, 2, sign=True),
                     common.band_txt(av.q05, av.q95, 2)])
    o.append(html.h3("İnstitusional bölgülər, Əsas ssenari"))
    o.append(html.table(["Bölgü", "2025, min", "2030, min", "% illik", "5–95 % zolağı"], rows,
                        cols=["c-wide", "c-num", "c-num", "c-num", "c-text"]))
    o.append(html.fig("fr4_state", "Dövlət sektorunda və büdcə təşkilatlarında məşğulluq", D.state_fig(d),
                      "Dövlət sektoru tarixi DSK mülkiyyət formaları cədvəlindən; büdcə təşkilatlarının tarixi sırası "
                      "yalnız DVX-də qısa müddət üçün mövcuddur, ona görə yalnız proqnoz göstərilir.", "Pəncərə 2000–2030."))
    sc = d["sc"]
    o.append(html.h3("Ssenarilər, 2030"))
    o.append(common.scen_table([
        ("Məşğul əhali", "min nəfər", {s: v(sc.loc[s, "employed_2030"], 1) for s in SCEN}),
        ("Məşğul əhali, orta illik artım", "%", {s: v(sc.loc[s, "employed_growth_pa"], 2, sign=True) for s in SCEN}),
        ("Dövlət sektoru", "min nəfər", {s: v(sc.loc[s, "state_2030"], 1) for s in SCEN}),
        ("Dövlət sektorunun payı", "%", {s: v(sc.loc[s, "state_share_2030"], 1) for s in SCEN}),
        ("Büdcə təşkilatları", "min nəfər", {s: v(sc.loc[s, "budget_2030"], 1) for s in SCEN}),
        ("Neft sektoru (vergi uçotu)", "min nəfər", {s: v(sc.loc[s, "oil_tax_2030"], 1) for s in SCEN}),
        ("Kənd təsərrüfatı", "min nəfər", {s: v(sc.loc[s, "agriculture_2030"], 1) for s in SCEN})]))
    o.append("<p>Ssenarilər arasında fərq kiçikdir, çünki FR1-in ssenariləri ümumi məşğulluğu az fərqləndirir; ən "
             "böyük fərq neft sektorundadır. Dövlət payı ssenaridən asılı deyil — o, proqnoz deyil, fərziyyədir "
             "(siyasi qərar) və rıçaqlar cədvəlində ayrıca göstərilir (<code>FR4_sensitivity_levers.csv</code>).</p>")
    return o


def check(d):
    ha = d["hagg"]
    rows = [[esc(D.HOLD_AZ.get(r.series, r.series)), v(r.model_RMSE_pct, 2), u_cell(r.U_vs_random_walk),
             u_cell(r.U_vs_constant_growth), v(r.err_2024_pct, 2, sign=True)] for r in ha.itertuples()]
    hs = d["hsum"]
    rows2 = [[esc(BASIS(r.basis)), esc(D.LEVEL_AZ.get(r.level, r.level)), v(r.median_RMSE_pct, 2), esc(r.beats_random_walk),
              u_cell(r.median_U_rw), esc(r.beats_constant_growth), u_cell(r.median_U_cg)] for r in hs.itertuples()]
    return [html.h2("check", 5, "Yoxlama"),
            "<p>Dinamik nümunədən kənar yoxlama 2020–2024: 2019-dan sonrakı heç bir məlumat işlədilmir; ümumi göstəricilər FR4-ün öz "
            "blokundan simulyasiya olunur. Etalonlar eyni informasiya ilə: təsadüfi gəzişmə (2019 səviyyəsi) və "
            "2005–2019 sabit artım. Neft hasilatı tənliyi (E9) 2020-dən əvvəl qiymətləndirilə bilmir — bu, açıq "
            "yazılır.</p>",
            html.table(["Sıra", "RMSE, %", "U: təsadüfi gəzişmə", "U: sabit artım", "2024 xətası, %"], rows,
                       cls="tbl tbl-dense tbl-backtest", cols=["c-wide", "c-num", "c-num", "c-num", "c-num"]),
            html.table(["Əsas", "Səviyyə", "Median RMSE, %", "TG-ni üstələyir", "Median U (TG)", "SA-nı üstələyir",
                        "Median U (SA)"], rows2, cls="tbl tbl-dense tbl-backtest",
                       cols=["c-tight", "c-tight", "c-num", "c-num", "c-num", "c-num", "c-num"]),
            "<p><strong>Açıq nəticə.</strong> Ümumi məşğulluq, iqtisadi fəal əhali və dövlət sektoru hər iki etalonu "
            "üstələyir; muzdlu işçilər sabit artımı üstələmir. Fəaliyyət növləri səviyyəsində dəqiqlik məhduddur: "
            "19 fəaliyyətin təxminən yarısı təsadüfi gəzişməni üstələyir, median U təxminən 1-dir. TG — təsadüfi "
            "gəzişmə, SA — sabit artım.</p>"]


def BASIS(b):
    return D.BASIS_AZ.get(b, b)


def limits():
    items = ["Sektor tərkibi iqtisadiyyata yalnız zəif reaksiya verir; 2020-dən əvvəl heç bir sürücü sabit payları üstələməyib.",
             "Fəaliyyət növləri səviyyəsində dəqiqlik məhduddur.",
             "Səviyyə əlaqələrinin əksəriyyəti kointeqrasiya olunmur; t-statistikaları təsviridir.",
             "Bu, səviyyə modelidir: uyğunlaşma sürəti qiymətləndirilmir.",
             "Ümumi məşğulluq və iqtisadi fəal əhali FR1-indir; əhali FR1-in fərziyyəsidir.",
             "Muzdlu işçilərin payı və dövlət payı proqnoz deyil, verilmiş yoldur.",
             "Neft məşğulluğu on müşahidəyə əsaslanır və nümunədən kənar sınana bilmir.",
             "2010 təsnifat qırılması pillə dəyişəni ilə nəzərə alınır, geriyə hesablanmır.",
             "Neft/qeyri-neft bölgüsü dövlət/qeyri-dövlət bölgüsü ilə toplana bilməz.",
             "Əmək bazarı gərginliyi və əmək haqqı kanalı yoxdur."]
    return [html.h2("limits", 6, "Məhdudiyyətlər"), "<p>Metodologiya sənədinin 13-cü bölməsindən.</p>",
            common.limits_list(items)]
