"""fr1.py — FR1 page: sectors and markets."""
from . import core, html, req, common
from .core import v, esc
from .common import YEARS, SCEN, SCEN_AZ, u_cell
from . import fr1_data as D

SECT_AZ = [("Mədənçıxarma", "hasilat həcmi ilə; sabit miqyas gəliri sınanıb və rədd edilib"),
           ("Emal sənayesi", "istehsal gücü, tikinti və xarici tələb"),
           ("Elektrik enerjisi, qaz və buxar", "qeyri-neft fəallığından törəmə tələb"),
           ("Su təchizatı, tullantılar", "adambaşına kommunal tələb"),
           ("Kənd, meşə və balıqçılıq", "deterministik trend (kapital termi yanlış işarəli olduğu üçün çıxarılıb)"),
           ("Tikinti", "dövlət və özəl investisiyalar"),
           ("Ticarət; nəqliyyat vasitələrinin təmiri", "istehlak"),
           ("Nəqliyyat və anbar təsərrüfatı", "karbohidrogen tranziti və trend"),
           ("Turistlərin yerləşdirilməsi və ictimai iaşə", "adambaşına sərəncamda qalan gəlir və trend"),
           ("İnformasiya və rabitə", "adambaşına İKT kapitalı və trend"),
           ("Sosial və digər xidmətlər", "adambaşına gəlir; deflyatora İQİ-nin tam ötürülməsi"),
           ("Məhsula və idxala xalis vergilər", "istehlak və idxal (fiskal bloka bağlıdır)")]


def build(t, pre="../"):
    d = D.load()
    b = d["scen"]["Baseline"]
    hs = D.hold_summary(d)
    c5, cn, c10 = d["coint"]
    pr = core.csv("FR1_panel_region.csv")
    pi = core.csv("FR1_panel_industry.csv")
    o = [f"<h1>FR1 — İqtisadi sektorlar və bazarlar: təhlil və beşillik proqnoz</h1>",
         html.kicker("FR1", "FR1.ipynb", "docs/FR1_Methodology.md"),
         common.intro("Bu səhifə FR1 tələbini, onu qarşılayan struktur ekonometrik modeli (AZSEM-FR1), işlədilən "
                      "məlumatı, 2026–2030 proqnozunu üç ssenari üzrə, nümunədən kənar yoxlamanı və modelin "
                      "məhdudiyyətlərini göstərir. Bütün rəqəmlər yığım anında modulun çıxış fayllarından oxunur."),
         html.h2("teleb", 1, "Tələb"), req.block("FR1", t),
         "<p>Tələb DSK təsnifatı üzrə hər sektor üçün struktur, dinamik və çoxdəyişənli model, sektorların ayrılıqda "
         "və birlikdə təhlilini və proqnozunu istəyir. «Ayrılıqda» — hər sektorun öz tənliyi, öz sürücüləri və "
         "testləri; «birlikdə» — bu tənliklərin milli hesablar, fiskal, monetar və tədiyə balansı eynilikləri ilə "
         "qapanan vahid sistem kimi həlli deməkdir.</p>",
         html.h2("model", 2, "Model və seçim səbəbi"),
         f"<p>AZSEM-FR1 {v(d['n_eq'], 0)} qiymətləndirilmiş tənlikdən ibarət blok-rekursiv struktur sistemdir. Hər sektorun "
         "real əlavə dəyəri öz iqtisadi sürücüsü ilə izah olunur, sistem isə eyni vaxtda həll edilir: neft-qaz bloku "
         "kvazi-ekzogen gəlir mənbəyidir, sektorlararası ötürmə tələb, investisiya və fiskal kanallar vasitəsilə "
         "baş verir.</p>",
         html.table(["DSK sektoru", "Modeldə sürücü"], [[esc(a), esc(b2)] for a, b2 in SECT_AZ],
                    cols=["c-wide", "c-text"]),
         "<p><strong>Niyə struktur model.</strong> Əsas sürücü — karbohidrogen hasilatı və neftin qiyməti — ekzogendir "
         "və ssenari kimi verilməlidir; siyasət sualları (dövlət investisiyası, kredit şəraiti, neftin qiyməti) yalnız "
         "struktur modeldə rıçaq kimi mövcuddur; 2015 devalvasiyası, 2020 pandemiyası və 2021–22 enerji şoku "
         "avtoreqressiv parametrləşməni qeyri-sabit edir. Heç bir davranış tənliyində asılı dəyişənin gecikməsi, "
         "AR/ARIMA/ARCH/GARCH komponenti yoxdur.</p>",
         f"<p><strong>Qiymətləndirmə.</strong> Səviyyə əlaqələri DOLS ilə qiymətləndirilir; kointeqrasiya MacKinnon "
         f"p-dəyərləri ilə yoxlanılır və {v(cn, 0)} səviyyə əlaqəsindən yalnız {v(c5, 0)}-də 5 %, {v(c10, 0)}-də 10 % "
         "səviyyəsində təsdiqlənir — qalanlarında t-statistikaları təsviri xarakter daşıyır. Kiçik nümunə üçün HAC "
         "xətaları, məhdudiyyətlər HAC-F testi ilə; panel parametrləri (sənaye sahələri, regionlar) Driscoll–Kraay və "
         "vəhşi klaster bootstrap ilə. 2025-ci il qalığı sabit əlavə amil (add-factor) kimi saxlanılır, 2026 isə "
         "yanvar–aprel məlumatına lövbərlənir.</p>",
         html.h2("data", 3, "Məlumat"),
         f"<p>Əsas mənbə Nazirliyin iş kitabıdır ({html.chip('data/Statistik data dinamika 05.06.2026 +.xlsx')}): "
         f"illik sıralar, sənaye sahələri paneli ({int(pi.year.min())}–{int(pi.year.max())}, "
         f"{v(pi.branch.nunique(), 0)} sahə) və regional panel ({int(pr.year.min())}–{int(pr.year.max())}, "
         f"{v(pr.region.nunique(), 0)} region). Təhlil məlumat dəsti {html.chip('output/FR1_analysis_dataset.csv')} "
         f"faylındadır. Qiymətləndirmədən əvvəl iş kitabının eynilikləri yoxlanılıb: {v(d['ident'][1], 0)} eynilikdən "
         f"{v(d['ident'][0], 0)}-i tolerans daxilində ödənir, qalanları araşdırılıb və modelə təsiri sənədləşdirilib "
         f"({html.chip('output/FR1_identity_checks.csv')}).</p>"]
    o += results(d, b)
    o += check(d, hs)
    o += limits(hs)
    o.append(common.files_section(7, "FR1", pre))
    return "\n".join(o)


def results(d, b):
    o = [html.h2("results", 4, "Nəticələr")]
    o.append(html.fig("fr1_rgdp", "Real ÜDM-in artımı: faktiki, proqnoz və 5–95 % zolağı", D.growth_fig(d, "rgdp", "real artım, %"),
                      "Qalın xətt — Əsas ssenari, boz qırıq xətlər — Mənfi və İslahat ssenariləri; zolaq Əsas ssenarinin "
                      f"{v(d['draws'], 0)} birgə simulyasiyasından (tarixi qalıq yolları, parametr çəkilişləri) qurulub.",
                      "Pəncərə 2006–2030; 2025-ə qədər faktiki, 2026–2030 proqnoz."))
    o.append(html.fig("fr1_rgdpnon", "Qeyri-neft ÜDM-in real artımı", D.growth_fig(d, "rgdpnon", "real artım, %"),
                      "Qeyri-neft iqtisadiyyatı modelin daxili dinamikasıdır; neft-qaz hasilatı isə ssenari ilə verilir.",
                      "Pəncərə 2006–2030."))
    rows = []
    for k, lab in (("rgdp", "Real ÜDM, artım"), ("rgdpnon", "Qeyri-neft ÜDM, real artım")):
        f = d["fan"][k]
        rows.append((lab, "%", [v(x) for x in b[k]], common.band_txt(f.loc[2030, "p5"], f.loc[2030, "p95"])))
    o.append(common.year_table(rows))
    sc = d["scen"]
    o.append(html.h3("Ssenarilər: Əsas, Mənfi, İslahat"))
    o.append(common.scen_table([
        ("Real ÜDM, orta illik artım 2026–2030", "%", {s: v(sc[s]["avg_rgdp"], 2) for s in SCEN}),
        ("Qeyri-neft ÜDM, orta illik real artım", "%", {s: v(sc[s]["avg_rgdpnon"], 2) for s in SCEN}),
        ("İnflyasiya, 2030", "%", {s: v(sc[s]["infl30"], 2) for s in SCEN}),
        ("İşsizlik, 2030", "%", {s: v(sc[s]["unemp30"], 2) for s in SCEN}),
        ("Büdcə balansı, 2030", "ÜDM-ə %", {s: v(sc[s]["bal30"], 2, sign=True) for s in SCEN}),
        ("Dövlət borcu, 2030", "ÜDM-ə %", {s: v(sc[s]["debt30"], 1) for s in SCEN}),
        ("Nominal ÜDM, 2030", "mlrd AZN", {s: v(sc[s]["gdpn30"], 0) for s in SCEN})]))
    o.append("<p>Ssenarilər neftin qiyməti, neft və qaz hasilatı, dövlət investisiyası, faiz siyasəti və xarici "
             "tələb fərziyyələri ilə fərqlənir; İslahat ssenarisində əlavə olaraq qeyri-neft sektorlarına TFP artımı "
             "tətbiq olunur. Fərziyyələrin tam cədvəli metodologiya sənədinin 7.3-cü bölməsindədir.</p>")
    o.append(html.fig("fr1_sectors", "Sektorlar üzrə orta illik real artım, 2026–2030", D.sectors_fig(d),
                      "On iki komponentin hər biri öz tənliyi ilə proqnozlaşdırılır və sistemdə birlikdə həll olunur.",
                      "Mənbə: FR1_accounts_summary_baseline.csv və FR1_accounts_summary_adverse.csv."))
    return o


def check(d, hs):
    h = d["hold"]
    rows = [[esc(D.VAR_AZ.get(r.variable, r.variable)), v(r.model_RMSE, 1), u_cell(r.U_rw2020), u_cell(r.U_cg1019),
             v(r.err_2025, 1, sign=True)] for r in h.itertuples()]
    a, n, m = hs["cg19"]
    return [html.h2("check", 5, "Yoxlama"),
            "<p>Bütün əmsallar, məhdudiyyət qərarları və kalibrlənmiş nisbətlər yalnız 2020-ci ilə qədərki məlumatla "
            "yenidən qurulub; sistem 2021–2025 üçün dinamik həll edilib (yalnız faktiki ekzogen yollarla). Etalonlar: "
            "2020-dən təsadüfi gəzişmə və 2010–2019 sabit artım. Theil U &lt; 1 modelin etalonu üstələdiyini göstərir.</p>",
            html.table(["Dəyişən", "RMSE, %", "U: təsadüfi gəzişmə (2020)", "U: sabit artım (2010–19)", "2025 səviyyə xətası, %"],
                       rows, cls="tbl tbl-dense tbl-backtest", cols=["c-wide", "c-num", "c-num", "c-num", "c-num"]),
            f"<p><strong>Açıq nəticə.</strong> Model 2020-dən təsadüfi gəzişməni {v(hs['rw20'][0], 0)}/{v(hs['rw20'][1], 0)} "
            f"dəyişəndə üstələyir (median U {v(hs['rw20'][2], 2)}), lakin 2020 pandemiya dibi olduğu üçün bu etalon "
            f"modelə əlverişlidir. Pandemiyadan əvvəlki onilliyin sabit artımına qarşı model yalnız {v(a, 0)}/{v(n, 0)} "
            f"dəyişəndə qalib gəlir, median U {v(m, 2)} — yəni təxminən bərabərdir. Real ÜDM-in 2025 səviyyə xətası "
            f"{v(hs['gdp'].err_2025, 1, sign=True, pct=True)}, qeyri-neft ÜDM-inki {v(hs['non'].err_2025, 1, sign=True, pct=True)}. "
            "2020-dən sonra transformasiyaya uğrayan sektorlar (emal, tikinti, nəqliyyat, dövlət investisiyası) ən zəif "
            "izlənilir.</p>"]


def limits(hs):
    items = ["İş kitabında giriş-çıxış (input–output) cədvəli yoxdur; sektorlararası əlaqələr ölçülmür, zaman sırası və "
             "panel kovariasiyasından qiymətləndirilir.",
             "Sektorlar üzrə illik məşğulluq yoxdur — tam istehsal funksiyası yalnız sənaye üçün qiymətləndirilə bilir.",
             "Xarici tələb dəyişəni yoxdur; o, istifadəçinin verdiyi ssenari girişidir.",
             "Faiz dərəcəsi və istehsal boşluğu kanalı identifikasiya olunmayıb; siyasət faizinin bazar faizlərinə "
             "ötürülməsi simulyasiya edilə bilmir.",
             "Məzənnə 2017-dən faktiki sabitdir; ötürmə praktiki olaraq yalnız 2015–16 devalvasiyasından identifikasiya olunur.",
             "Emal, tikinti və nəqliyyat proqnozları ən zəifdir; sabit artım etalonuna qarşı model ancaq bərabərdir "
             f"(median U {v(hs['cg19'][2], 2)}).",
             "Səviyyə əlaqələrinin əksəriyyətində kointeqrasiya təsdiqlənmir; proqnoz səviyyəsi sabit əlavə amil "
             "fərziyyəsindən asılıdır (azalan əlavə amil həssaslığı FR1_addfactor_sensitivity.csv faylındadır).",
             "Nəqliyyat, kənd təsərrüfatı, İKT və elektrik enerjisində 2027–2030 artımının böyük hissəsi deterministik trenddir.",
             "Dövlət investisiyasının səviyyəsi proqnoz deyil, fərziyyədir; investisiyada aqreqat kredit kanalı yoxdur.",
             "Zolaqlar İQİ, istehlak və cari xərclər üzrə genişdir və sıçrayış süzgəci ilə kəsilib."]
    return [html.h2("limits", 6, "Məhdudiyyətlər"),
            "<p>Metodologiya sənədinin 9-cu bölməsindən; hər biri məlumata bağlıdır, ümumi ehtiyat qeydi deyil.</p>",
            common.limits_list(items)]
