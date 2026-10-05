"""fr3.py — FR3 page: average monthly wage."""
from . import core, html, req, common
from .core import v, esc
from .common import SCEN, SCEN_AZ, u_cell
from . import fr3_data as D

RATE_AZ = {"employer only, 22%": "yalnız işəgötürən, 22 %", "employer + employee, 25%": "işəgötürən + işçi, 25 %",
           "employer + employee + medical + unemployment, 29%": "işəgötürən + işçi + tibbi + işsizlik, 29 %"}


def build(t, pre="../"):
    d = D.load()
    now = d["now"].set_index("series").loc["average wage"]
    o = ["<h1>FR3 — Orta aylıq əmək haqqı: təhlil və beşillik proqnoz</h1>",
         html.kicker("FR3", "FR3.ipynb", "docs/FR3_Methodology.md"),
         common.intro("Orta aylıq əmək haqqının səviyyəsi və artım sürəti — ölkə üzrə, dövlət və qeyri-dövlət, neft və "
                      "qeyri-neft sektorları üzrə — 2030-a qədər. Səhifə həm də tələb olunan dörd bölgüdən hansının "
                      "məlumatla qarşılana bildiyini, hansının bilmədiyini açıq göstərir."),
         html.h2("teleb", 1, "Tələb"), req.block("FR3", t),
         html.h2("model", 2, "Model və seçim səbəbi"),
         "<p><strong>Əsas tapıntı: dörd bölgü bir-birinin içinə yerləşmir.</strong> Dövlət × qeyri-dövlət və iqtisadi "
         "sektorlar muzdlu işçilərin dəqiq bölgüsüdür; neft × qeyri-neft isə onları kəsir (neft şirkətləri həm dövlət, "
         "həm özəl sektordadır), ona görə üçüncü qrup kimi toplanarsa ikiqat sayılma yaranır; büdcə × qeyri-büdcə "
         "dövlət sektorunun qismən müşahidə olunan alt-bölgüsüdür. FR3 buna görə eyni milli ortaya gedən iki "
         "aqreqasiya aparır və proqnozda hər ikisini ona birgə uzlaşdırır.</p>",
         f"<p><strong>Tənliklər.</strong> {v(d['n_eq'], 0)} tənlik (orta, qeyri-neft, qeyri-dövlət, dövlət, neft əmək haqqı və "
         "minimum əmək haqqı qaydası) DOLS ilə qiymətləndirilib. Nominal homogenlik sınanıb və nəzəri əsasla tətbiq "
         "olunub; 2018 minimum əmək haqqı islahatı struktur qırılma kimi yoxlanılıb; minimum əmək haqqının təsiri "
         "elastikliklər aralığı ilə verilir. Spesifikasiya hold-out pəncərəsindən əvvəlki sürüşən başlanğıclarda seçilib "
         "(<code>FR3_specification_selection.csv</code>). Neft sektorunun əmək haqqı tənliklə deyil, qeyri-neft əmək haqqı × "
         f"açıq göstərilən mükafat rıçağı ilə verilir. Kointeqrasiya {v(d['n_eq'], 0)} tənliyin {v(d['coint'], 0)}-də "
         "təsdiqlənir, ona görə t-statistikaları təsviri xarakter daşıyır.</p>",
         html.h2("data", 3, "Məlumat"),
         f"<p>Mənbələr: Nazirliyin iş kitabı (illik 2025-ə qədər, aylıq 2026-cı ilin {v(now.months_observed, 0)} ayına qədər), "
         "DSK əmək haqqı və məşğulluq cədvəlləri, Vergi Xidmətinin (DVX) bəyannamə göstəriciləri. 2026 üçün ilin ilk "
         f"aylarından cari qiymətləndirmə (nowcast) aparılır: orta əmək haqqı {v(now.nowcast, 1)} AZN, "
         f"artım {v(now['growth_2026_%'], 1, sign=True, pct=True)} ({html.chip('output/FR3_nowcast_2026.csv')}).</p>",
         "<p><strong>Məlumatın verə bilmədiyi.</strong> İqtisadi sektorlar üzrə orta əmək haqqı nəşr olunmur və "
         "mövcud məlumatdan çıxarıla bilmir. Büdcə və qeyri-büdcə təşkilatlarının orta əmək haqqı identifikasiya "
         "olunmur: büdcə təşkilatlarının əmək haqqı fondu yalnız sosial ayırmalardan, ayırma dərəcəsinin fərziyyəsi "
         "ilə bərpa edilə bilir və nəticə bu fərziyyəyə həssasdır:</p>",
         bnb_table(d)]
    o += results(d)
    o += check(d)
    o += limits()
    o.append(common.files_section(7, "FR3", pre))
    return "\n".join(o)


def bnb_table(d):
    b = d["bnb"][d["bnb"].year == d["bnb"].year.max()]
    rows = [[esc(RATE_AZ.get(r.rate_assumption, r.rate_assumption)), v(r.budget_wage, 0), v(r.non_budget_wage, 0),
             v(r.budget_vs_national, 2)] for r in b.itertuples()]
    y = int(d["bnb"].year.max())
    return html.table([f"Ayırma dərəcəsi fərziyyəsi ({y})", "Büdcə, AZN", "Qeyri-büdcə, AZN", "Büdcə / ölkə ortası"],
                      rows, cols=["c-wide", "c-num", "c-num", "c-num"])


def results(d):
    s = d["sum"]
    o = [html.h2("results", 4, "Nəticələr"),
         html.fig("fr3_wavg", "Orta aylıq nominal əmək haqqı", D.wavg_fig(d),
                  "Qalın xətt — Əsas ssenari; boz xətlər — Mənfi və İslahat; zolaq FR1-in makro çəkilişlərini də daxil "
                  "edən 5–95 % aralığıdır.", "Pəncərə 2005–2030.")]
    b = s[s.scenario == "Baseline"]
    rows = [[esc(D.BRK_AZ[r.breakdown]), v(r.nominal_2025, 1), v(r.nominal_2030, 1), v(r.nominal_growth_avg_pct, 2, sign=True),
             v(r.real_growth_avg_pct, 2, sign=True)] for r in b.itertuples()]
    o.append(html.h3("Əsas ssenari, 2025 → 2030"))
    o.append(html.table(["Bölgü", "2025, AZN", "2030, AZN", "Nominal, % illik", "Real, % illik"], rows,
                        cols=["c-wide", "c-num", "c-num", "c-num", "c-num"]))
    o.append(html.h3("Ssenarilər: real əmək haqqının orta illik artımı, 2026–2030"))
    srows = []
    for brk in D.BRK_AZ:
        vals = {sc: v(s[(s.scenario == sc) & (s.breakdown == brk)].real_growth_avg_pct.iloc[0], 2, sign=True) for sc in SCEN}
        srows.append((D.BRK_AZ[brk], "%", vals))
    nom = {sc: v(s[(s.scenario == sc) & (s.breakdown == "average wage")].nominal_growth_avg_pct.iloc[0], 2, sign=True) for sc in SCEN}
    srows.insert(0, ("Orta əmək haqqı, nominal", "%", nom))
    o.append(common.scen_table(srows))
    o.append(html.fig("fr3_breakdowns", "Bölgülər üzrə nominal əmək haqqı, Əsas ssenari", D.breakdown_fig(d),
                      "Neft sektoru (ölkə ortasının təxminən dörd misli) miqyası sıxmamaq üçün qrafikdən kənarda "
                      "saxlanılıb; onun rəqəmləri yuxarıdakı cədvəldədir.", "Pəncərə 2005–2030."))
    return o


def check(d):
    h = d["hold"]
    rows = [[esc(D.HOLD_AZ.get(r.variable, r.variable)), v(r.model_RMSE, 1), u_cell(r.U_rw), u_cell(r.U_cg),
             f"{core.num(r.DM_p_vs_rw, 2)} / {core.num(r.DM_p_vs_cg, 2)}", v(r.err_2025, 1, sign=True)]
            for r in h.itertuples(index=False)]
    rw = common.beat_count(h["U_rw"])
    cg = common.beat_count(h["U_cg"])
    worse = int(((h.DM_p_vs_cg < 0.10) & (h["U_cg"] > 1)).sum())
    return [html.h2("check", 5, "Yoxlama"),
            "<p>Hər şey 2020-ci ilə qədərki məlumatla yenidən qiymətləndirilib; 2021–2025 dinamik simulyasiya proqnozla "
            "eyni lövbər qaydası ilə aparılıb. Etalonlar: təsadüfi gəzişmə və 2010–2020 sabit artım.</p>",
            html.table(["Sıra", "RMSE, %", "U: təsadüfi gəzişmə", "U: sabit artım", "DM p (TG / SA)", "2025 xətası, %"],
                       rows, cls="tbl tbl-dense tbl-backtest", cols=["c-wide", "c-num", "c-num", "c-num", "c-num", "c-num"]),
            f"<p><strong>Açıq nəticə.</strong> Model təsadüfi gəzişməni {v(rw[0], 0)}/{v(rw[1], 0)} sırada üstələyir, sabit "
            f"artımı isə {v(cg[0], 0)}/{v(cg[1], 0)} sırada. {v(worse, 0)} sırada (DM p &lt; 0,10) model sabit artımdan "
            "əhəmiyyətli dərəcədə <em>pisdir</em>. Xətanın əsas mənbəyi 2020 (COVID ili) qalığına lövbərlənmə və 2021–22 "
            "inflyasiya sıçrayışıdır; neft sektorunda isə mükafat rıçağı faktiki enişi tutmur.</p>"]


def limits():
    items = ["Sektorlar üzrə orta əmək haqqı nəşr olunmur və çıxarıla bilmir.",
             "Büdcə və qeyri-büdcə təşkilatlarının orta əmək haqqı identifikasiya olunmur (yuxarıdakı aralıq fərziyyədən asılıdır).",
             "DVX məlumatında sətir təkrarı aşkarlanıb (sənəd, §8.3).",
             "Neft sektorunun əmək haqqı tənliklə proqnozlaşdırılmır; hold-out-da təsadüfi gəzişmə bu mexanizmi üstələyir.",
             "Hold-out sabit artım etalonuna qarşı zəifdir; lövbər ilinin seçimi nəticəni güclü dəyişir.",
             "Heç bir tənlikdə kointeqrasiya təsdiqlənmir; əlavə amillər sabit saxlanılır.",
             "Homogenlik nəzəri əsasla tətbiq olunub, qeyri-dövlət sektorunda isə qısa nümunədə rədd edilir.",
             "Minimum əmək haqqının təsiri qeyri-dəqiqdir; qeyri-dövlət sektorunda tutulmur.",
             "Əmək bazarı gərginliyi kanalı yoxdur; 2021-dən əvvəlki muzdlu məşğulluq törəmədir.",
             "Nümunələr qısadır; məşğulluq tərkibi 2026-dan sonra sabit saxlanılır; FR1-in makro qeyri-müəyyənliyi miras alınır.",
             "DSK və DVX orta əmək haqqını fərqli göstərir; FR3 DSK sırasını proqnozlaşdırır."]
    return [html.h2("limits", 6, "Məhdudiyyətlər"), "<p>Metodologiya sənədinin 9-cu bölməsindən.</p>",
            common.limits_list(items)]
