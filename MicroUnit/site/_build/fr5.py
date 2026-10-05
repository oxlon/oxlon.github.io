"""fr5.py — FR5 page: paid services rendered to the population."""
from . import html, req, common
from .core import v, esc
from .common import SCEN, u_cell
from . import fr5_data as D

WIN_AZ = {"A": "A: pandemiyadan əvvəl, 2014–2019", "B": "B: test pəncərəsi, 2020–2025"}


def build(t, pre="../"):
    d = D.load()
    e1 = d["e1"]
    eta = e1.loc["ln_income_pc"]
    m = d["meta"]
    ic = d["ident"]
    o = ["<h1>FR5 — Əhaliyə göstərilən pullu xidmətlər: təhlil və beşillik proqnoz</h1>",
         html.kicker("FR5", "FR5.ipynb", "docs/FR5_Methodology.md"),
         common.intro("Pullu xidmətlərin real həcmi və artım sürəti, on üç xidmət növü üzrə tərkib, hüquqi şəxs / fərdi "
                      "sahibkar və dövlət / qeyri-dövlət bölgüləri — 2030-a qədər, FR1-in gəlir və qiymət yolları ilə."),
         html.h2("teleb", 1, "Tələb"), req.block("FR5", t),
         html.h2("model", 2, "Model və seçim səbəbi"),
         "<p>Əhaliyə pullu xidmətlər ev təsərrüfatlarının xidmət istehlakıdır; onun struktur modeli zaman sırası deyil, "
         "<strong>tələb sistemidir</strong>. Model iki pillədir: (1) <em>nə qədər</em> — adambaşına real həcmin "
         "adambaşına real gəlir və xidmətlərin nisbi qiyməti ilə izah olunduğu aqreqat tələb tənliyi (həcm və artım "
         "sürəti buradan gəlir); (2) <em>nəyə</em> — on üç xidmət növü üzrə multinomial-logit pay sistemi (paylar müsbət "
         "və cəmi birə bərabər), onun Engel əmsalları xərc elastiklikləridir.</p>",
         f"<p>Seçilmiş aqreqat tənlikdə gəlir elastikliyi {v(eta.coef, 3)} (s.x. {v(eta.se, 3)}, {esc(eta.estimator)}); "
         f"eyni tənlik fərq formasında {v(eta.diff_eta, 3)} verir. Kointeqrasiya təsdiqlənmir (MacKinnon p = "
         f"{v(eta.eg_coint_p, 2)}), ona görə elastiklik tək rəqəm deyil, aralıq kimi oxunmalıdır "
         "(<code>FR5_income_elasticity_range.csv</code>); «dəbdəbə əmtəəsi» nəticəsi statistik tapıntı kimi geri "
         "götürülüb. Bütün seçimlər (aqreqat, paylar, büzülmə, bölgülər) eyni qaydaya tabedir: 2019-a qədər qiymətləndirilən "
         "pəncərələrdə ən yaxşıdan əhəmiyyətli dərəcədə pis olmayan namizədlər, onlardan uyğun (coherent) olanlar, sonra "
         f"ən sadəsi. Növ əmsalları empirik Bayes üsulu ilə ümumi elastikliyə doğru büzülür (κ = {v(m.kappa, 0)}).</p>",
         html.h2("data", 3, "Məlumat"),
         "<p>İş kitabının pullu xidmətlər sətirləri və DSK-dan toplanmış cədvəllər: növlər üzrə dəyər, həcm indeksləri, "
         "deflyatorlar, dövlət / qeyri-dövlət bölgüsü və regional sıralar. DSK məlumatı ona görə lazım oldu ki, iş "
         "kitabı növ bölgüsünü vermir. Aşkarlanan problemlər — 1995-dən əvvəl denominasiyadan əvvəlki manat, mətn kimi "
         "saxlanılan xanalar, «digər xidmətlər»in təsnifat qeyri-sabitliyi, zəncirvari həcmlərin toplanmaması, regional "
         f"sıraların milli cəmlə uzlaşmaması — <a href=\"{pre}data.html#integrity\">Məlumat mənbələri</a> səhifəsindədir. "
         f"{v(int(ic.passed.sum()), 0)}/{v(len(ic), 0)} hesab yoxlaması keçir.</p>"]
    o += results(d)
    o += check(d)
    o += limits()
    o.append(common.files_section(7, "FR5", pre))
    return "\n".join(o)


def results(d):
    sc, m = d["sc"], d["meta"]
    b = d["tot"]["Baseline"]
    f = D.fan_years(d)
    o = [html.h2("results", 4, "Nəticələr"),
         html.fig("fr5_volume", "Pullu xidmətlərin real həcmi", D.volume_fig(d),
                  f"Zolaq yalnız {v(m.n_paths_joint, 0)} birgə tarixi qalıq yoluna ({int(m.first_start)}–{int(m.last_start)} "
                  f"başlanğıcları), parametr çəkilişlərinə və FR1-in {v(m.n_fr1_draws, 0)} makro çəkilişinə əsaslanır — "
                  "göstərici xarakterlidir.", "Pəncərə 2000–2030. Tarixi səviyyə DSK-nın zəncirvari həcm indeksindən 2025 "
                  "lövbərinə qədər geriyə hesablanıb."),
         html.fig("fr5_growth", "Real həcmin illik artımı", D.growth_fig(d),
                  "2020 pandemiya enişi tarixi sıranın ən böyük şokudur; proqnoz FR1-in gəlir yolunu izləyir.",
                  "Pəncərə 2001–2030.")]
    rows = [("Real həcm", "mln AZN (2015)", [v(x, 0) for x in b.loc[[2026, 2027, 2028, 2029, 2030], "volume_2015_prices"]],
             common.band_txt(f.loc[2030, "level_p5"], f.loc[2030, "level_p95"], 0)),
            ("Real həcm, artım", "%", [v(x, 2) for x in b.loc[[2026, 2027, 2028, 2029, 2030], "volume_growth_pct"]],
             common.band_txt(f.loc[2030, "growth_pct_p5"], f.loc[2030, "growth_pct_p95"], 1)),
            ("Nominal dəyər", "mln AZN", [v(x, 0) for x in b.loc[[2026, 2027, 2028, 2029, 2030], "value_current"]], "—")]
    o.append(common.year_table(rows))
    o.append(html.h3("Ssenarilər"))
    o.append(common.scen_table([
        ("Real həcm, 2030", "mln AZN (2015)", {s: v(sc.loc[s, "volume_2030"], 0) for s in SCEN}),
        ("Real həcm, orta illik artım", "%", {s: v(sc.loc[s, "volume_growth_pa"], 2, sign=True) for s in SCEN}),
        ("Nominal dəyər, 2030", "mln AZN", {s: v(sc.loc[s, "value_2030"], 0) for s in SCEN}),
        ("Nominal dəyər, orta illik artım", "%", {s: v(sc.loc[s, "value_growth_pa"], 2, sign=True) for s in SCEN}),
        ("Adambaşına real həcm, 2030", "AZN (2015)", {s: v(sc.loc[s, "volume_per_head_2030"], 0) for s in SCEN})]))
    fr = d["fr1"]
    o.append(f"<p>FR1-in eyni sıra üzrə öz proqnozu ilə fərq 2030-da {v(fr.loc[2030, 'volume diff, %'], 2, sign=True, pct=True)}, "
             f"ən çox {v(fr['volume diff, %'].max(), 2, sign=True, pct=True)}: hər ikisi eyni 2025 dəyərindən və eyni FR1 "
             "sürücülərindən başlayır, lakin tənliklər fərqlidir — bu, təsdiq deyil, həqiqi modelləşdirmə fərqidir.</p>")
    o.append(html.fig("fr5_types", "Xidmət növləri üzrə orta illik həcm artımı", D.types_fig(d),
                      "Növlər arasında sıralama zəif dəstəklənir: büzülmə onu ümumi elastikliyə doğru sıxır. Heç bir "
                      "növün proqnozu öz ən yaxşı beşillik tarixi ortasını aşmır.",
                      "Mənbə: FR5_type_growth_vs_history.csv."))
    sp = d["split"]
    s30 = sp[(sp.scenario == "Baseline") & (sp.year == 2030)].iloc[0]
    o.append(f"<p><strong>İnstitusional bölgülər (Əsas, 2030):</strong> hüquqi şəxslər {v(s30.legal_share * 100, 1, pct=True)}, "
             f"fərdi sahibkarlar {v(s30.indiv_share * 100, 1, pct=True)}; dövlət {v(s30.state_share * 100, 1, pct=True)}, "
             f"qeyri-dövlət {v(s30.nonstate_share * 100, 1, pct=True)} (<code>FR5_institutional_split.csv</code>).</p>")
    return o


def check(d):
    h = d["hold"]
    rows = []
    for r in h.itertuples():
        k = r.window.split(":")[0]
        rows.append([esc(WIN_AZ.get(k, r.window)), v(r.RMSE_pct, 2), u_cell(r.U_vs_random_walk), u_cell(r.U_vs_constant_growth),
                     v(r.final_year_err_pct, 2, sign=True), v(r.shares_RMSE_pp, 2), v(r.types_beating_rw, 0)])
    B = h[h.window.str.startswith("B")].iloc[0]
    return [html.h2("check", 5, "Yoxlama"),
            "<p>İki nümunədən kənar yoxlama: hər birində bütün qərar qaydası kəsimə qədərki məlumatla yenidən tətbiq olunur, paylar "
            "simulyasiya olunan cəmlə idarə edilir. Sabit artım etalonu kəsimdən əvvəlki beş ilin ortasıdır.</p>",
            html.table(["Pəncərə", "RMSE, %", "U: təsadüfi gəzişmə", "U: sabit artım", "Son il xətası, %",
                        "Paylar RMSE, f.b.", "TG-ni üstələyən növlər"], rows, cls="tbl tbl-dense tbl-backtest",
                       cols=["c-wide", "c-num", "c-num", "c-num", "c-num", "c-num", "c-num"]),
            f"<p><strong>Açıq nəticə.</strong> Test pəncərəsində (2022–2025 qiymətləndirilir, 2020–21 çıxarılır) aqreqat "
            f"təsadüfi gəzişməni üstələmir (U {v(B.U_vs_random_walk, 2)}), sabit artımı isə üstələyir (U "
            f"{v(B.U_vs_constant_growth, 2)}). Pay sistemi heç bir pəncərədə təsadüfi gəzişmədən yaxşı deyil (U "
            f"{v(B.shares_U_vs_random_walk, 2)}). Pandemiya illəri daxil edildikdə U {v(B.U_vs_rw_incl_pandemic, 2)}.</p>"]


def limits():
    items = ["Nəticələr FR1-in gəlir və qiymət yollarından asılıdır.",
             "Gəlir elastikliyi kointeqrasiya olunmayan səviyyə əlaqələrindən gələn aralıqdır; «dəbdəbə» təsdiqlənmir.",
             "Uyğunlaşma dinamikası yoxdur (asılı dəyişənin gecikməsinə icazə verilmir).",
             "Növlər üzrə sıralama zəif dəstəklənir; büzülmə onu ümumi elastikliyə doğru sıxır.",
             "Pay sistemində IIA fərziyyəsi var, seçilmiş sistemdə qiymət termi yoxdur.",
             "Növlər üzrə nisbi qiymətlər sabit saxlanılır — rıçaq kimi göstərilir.",
             "Əlavə amillər sabitdir; azalma yalnız həssaslıqdır.",
             "Zolaqlar doqquz birgə yola əsaslanır — göstərici xarakterlidir.",
             "Aqreqat 2022–2025 test pəncərəsində təsadüfi gəzişməni üstələmir.",
             "Regional məlumat milli cəmlə uzlaşmır; «digər xidmətlər» sırasında qırılmalar var; ev təsərrüfatları "
             "büdcə sorğusunun mikro-məlumatı yoxdur."]
    return [html.h2("limits", 6, "Məhdudiyyətlər"), "<p>Metodologiya sənədinin 12-ci bölməsindən.</p>",
            common.limits_list(items)]
