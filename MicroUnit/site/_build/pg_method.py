"""pg_method.py — the standards shared by all six requirements, with a cross-module hold-out summary."""
from . import core, html, common
from .core import esc
from . import fr1_data, fr3_data, fr4_data, fr5_data, fr10_data, fr12_data

SECS = [("stance", "Struktur yanaşma"), ("estimation", "Qiymətləndirmə"), ("selection", "Seçim və yoxlama"),
        ("holdout", "Hold-out xülasəsi"), ("coherence", "Uyğunluq qaydası və büzülmə"),
        ("anchoring", "Lövbər və əlavə amillər"), ("uncertainty", "Qeyri-müəyyənlik"),
        ("plausibility", "Ağlabatanlıq və eyniliklər"), ("links", "Modullar arası əlaqələr")]


LOSERS = []


def holdout_rows():
    LOSERS.clear()

    def u(x):
        return common.u_cell(x)

    rows = []
    h = fr1_data.load()["hold"].set_index("variable")
    for var, lab in (("real GDP", "Real ÜDM"), ("real non-oil GDP", "Qeyri-neft ÜDM")):
        rows.append(["FR1", lab, "2021–2025", u(h.loc[var, "U_rw2020"]), u(h.loc[var, "U_cg1019"])])
    h3 = fr3_data.load()["hold"].set_index("variable").loc["average wage"]
    rows.append(["FR3", "Orta əmək haqqı", "2021–2025", u(h3.U_rw), u(h3.U_cg)])
    h4 = fr4_data.load()["hagg"].iloc[0]
    rows.append(["FR4", "Məşğul əhali, cəmi", "2020–2024", u(h4.U_vs_random_walk), u(h4.U_vs_constant_growth)])
    h5 = fr5_data.load()["hold"]
    b = h5[h5.window.str.startswith("B")].iloc[0]
    rows.append(["FR5", "Pullu xidmətlər, real həcm", esc(b.scored_years.split(" ")[0]), u(b.U_vs_random_walk),
                 u(b.U_vs_constant_growth)])
    h10 = fr10_data.load()["hold"]
    h10 = h10[h10.selected == True]  # noqa: E712
    for meas, w, lab in (("nominal", "unweighted", "Emal sahələri, nominal"), ("real", "share-weighted", "Emal sahələri, real (çəkili)")):
        r = h10[(h10.measure == meas) & (h10.weighting == w)].iloc[0]
        rows.append(["FR10", lab, "2020–2025", u(r.U_vs_random_walk), u(r.U_vs_constant_growth)])
    h12 = fr12_data.load()["hold"]
    r = h12[(h12.panel == "activity") & h12.metric.str.startswith("entry")].iloc[0]
    rows.append(["FR12", "Giriş əmsalı, fəaliyyət qrupları", esc(str(r.targets)), u(r.theil_rule_vs_rw), u(r.theil_rule_vs_constant)])
    for r in rows:
        if "skill-neg" in r[4] and r[0] not in LOSERS:
            LOSERS.append(r[0])
    return rows


def build(texts):
    hrows = holdout_rows()
    draws = fr1_data.load()["draws"]
    o = ["<h1>Metod</h1>",
         '<p class="lead-in">Altı tələbin hamısına tətbiq olunan ortaq standartlar: nə qadağandır, nə ilə qiymətləndirilir, '
         "seçim necə aparılır, proqnoz nəyə qarşı yoxlanılır və qeyri-müəyyənlik necə qurulur. Hər modulun öz "
         "təfərrüatları onun səhifəsində və metodologiya sənədindədir.</p>",
         html.h2("stance", 1, "Struktur yanaşma"),
         "<p>Sifarişçinin tələbinə uyğun olaraq heç bir modeldə <strong>AR, ARIMA, ARCH və ya GARCH</strong> komponenti yoxdur, "
         "heç bir davranış tənliyində <strong>asılı dəyişənin gecikməsi</strong> işlədilmir və heç bir dəyişən öz tarixindən "
         "proqnozlaşdırılmır. Hər tənlik iqtisadi sürücülərlə — əlaqəli sektorların təsiri görünəcək şəkildə — izah olunur. "
         "Gecikmə ehtiva edən, lakin avtoreqressiv olmayan konstruksiyalar (kapital yığımı eyniliyi, qiymət səviyyəsinin "
         "artım tempindən yığılması, borc axını, DOLS-un fərqləndirilmiş regressor gecikmələri) hər modulda ayrıca "
         "sadalanır və əsaslandırılır (<code>FR10_noar_constructs.csv</code>, <code>FR12_noar_constructs.csv</code>, FR1 sənədi §1.1).</p>",
         html.h2("estimation", 2, "Qiymətləndirmə"),
         "<ul><li><strong>DOLS</strong> — bütün səviyyə əlaqələri dinamik ən kiçik kvadratlarla (fərqləndirilmiş "
         "regressorların ±1 irəli/geri gecikməsi, sərbəstlik dərəcəsi imkan verdikdə).</li>"
         "<li><strong>Kointeqrasiya</strong> — qalıqlara əsaslanan Engle–Granger testi, <strong>MacKinnon</strong> cavab "
         "səthi p-dəyərləri ilə; kointeqrasiya təsdiqlənməyən əlaqələrdə t-statistikaları «təsviri» adlanır.</li>"
         "<li><strong>Kiçik nümunə inferensiyası</strong> — n/(n−k) miqyaslı HAC xətaları, t(n−k) paylanması, məhdudiyyətlər "
         "üçün HAC-F; rədd edilməyən hipotezlər «aşağı güc» kimi işarələnir.</li>"
         "<li><strong>Panellər</strong> — iki tərəfli sabit effektlər, Driscoll–Kraay xətaları və illər üzrə vəhşi klaster "
         "bootstrap (Webb çəkiləri).</li>"
         "<li>Endogenlik — instrumentlər, Durbin–Wu–Hausman testi; 2SLS yalnız test rədd etdikdə və instrumentlər güclü olduqda.</li></ul>",
         html.h2("selection", 3, "Seçim və yoxlama"),
         "<p>Hər seçim (sürücülər, estimator, pay sistemi, büzülmə intensivliyi, lövbər) <strong>yalnız kəsimdən əvvəlki "
         "məlumatla</strong>, sürüşən başlanğıclarda aparılır; <strong>hold-out pəncərəsinə toxunulmur</strong>. Proqnoz "
         "dəqiqliyi iki sadə etalona qarşı ölçülür: <strong>təsadüfi gəzişmə</strong> (son müşahidə) və <strong>sabit "
         "artım</strong> (kəsimdən əvvəlki orta artım). Theil U &lt; 1 modelin etalonu üstələdiyini göstərir; fərqin "
         "əhəmiyyəti Diebold–Mariano testi (Harvey–Leybourne–Newbold düzəlişi ilə) ilə yoxlanılır. Model etalonu "
         "üstələmədikdə bu, gizlədilmir — səhifələrdə açıq yazılır.</p>",
         html.h2("holdout", 4, "Hold-out xülasəsi"),
         html.table(["Modul", "Sıra", "Hədəf illər", "U: təsadüfi gəzişmə", "U: sabit artım / sabit"], hrows,
                    cls="tbl tbl-dense tbl-backtest", cols=["c-tight", "c-wide", "c-tight", "c-num", "c-num"]),
         "<p>Yaşıl rəqəm etalonun üstələndiyini göstərir. Mənzərə qarışıqdır və bu dürüst nəticədir: modellər əksər hallarda "
         "təsadüfi gəzişməni üstələyir, sabit artım isə daha çətin etalondur — bu cədvəldə onu üstələməyən sıralar: "
         + ", ".join(LOSERS) + ". Hər modulun tam hold-out cədvəli öz səhifəsinin «Yoxlama» bölməsindədir.</p>",
         html.h2("coherence", 5, "Uyğunluq qaydası və büzülmə"),
         "<p><strong>Uyğunluq (coherence) qaydası:</strong> hər səviyyə tənliyi həm də birinci fərqlərdə qiymətləndirilir; "
         "səviyyə əmsalı fərq formasının 95 % etibar intervalından kənardadırsa, işlədilmir (fərq formasının əmsalı və ya "
         "sürücüsüz variant götürülür). <strong>Empirik Bayes büzülməsi:</strong> səs-küylü vahid-xüsusi əmsallar dəqiqliyə "
         "görə çəkilərək ümumi dəyərə doğru sıxılır; intensivlik kəsimdən əvvəl eyni qayda ilə seçilir.</p>",
         html.h2("anchoring", 6, "Lövbər və əlavə amillər"),
         "<p>Hər tənliyin son faktiki ildəki qalığı <strong>sabit əlavə amil</strong> (add-factor) kimi proqnoz üfüqündə "
         "saxlanılır, beləliklə model son faktiki ili dəqiq təkrarlayır. Qalıqların azalması (ρ̂ ilə) yalnız həssaslıq kimi "
         "göstərilir. FR1-də 2026 ili yanvar–aprel məlumatına lövbərlənir və bu artım bir illik yarımömürlə sönür.</p>",
         html.h2("uncertainty", 7, "Qeyri-müəyyənlik"),
         "<p>Zolaqlar qalıq dinamikasının modeli ilə deyil, <strong>tarixi qalıq yollarının təkrar seçilməsi</strong> ilə "
         "qurulur (bütün tənliklərin birgə beşillik qalıq yolları), üstəgəl <strong>parametr çəkilişləri</strong> (işarəni "
         "pozanlar rədd edilir) və aşağı axın modullarında <strong>FR1-in makro çəkilişləri</strong>. Birgə tarixi yolların "
         "sayı az olduqda (məsələn, FR5, FR12) zolaqlar göstərici xarakterli adlanır.</p>",
         html.h2("plausibility", 8, "Ağlabatanlıq və eyniliklər"),
         "<p>Hər proqnoz artımı vahidin öz tarixi ilə (2010–2019 və 2021–2025 ortaları, ən yaxşı və ən pis beşillik) "
         "müqayisə olunur və kənara çıxanlar səbəbi ilə bayraqlanır. Hesab eynilikləri (cəmlər, paylar, balanslar) hər "
         "modulda yoxlanılır və «konstruksiyaya görə ödənir» kimi düzgün adlandırılır. Metodologiya sənədlərinin rəqəm "
         'blokları çıxış fayllarından generasiya olunur (<a href="notebooks.html#rules">ətraflı</a>).</p>',
         html.h2("links", 9, "Modullar arası əlaqələr"),
         "<p>FR1 makro çərçivəni (sektor əlavə dəyəri, deflyatorlar, gəlir, məşğulluq, əhali, neftin qiyməti) üç ssenari və "
         f"{core.num(draws, 0)} çəkilişlə verir. FR3 və FR4 əmək bazarını, FR5 ev təsərrüfatlarının xidmət tələbini, FR10 sənaye sahələrini, "
         "FR12 giriş/çıxışı onunla uzlaşdırır; asılılıqlar dəftərlərin kodundan avtomatik oxunur "
         '(<a href="notebooks.html">Jupyter dəftərləri</a>).</p>']
    return "\n".join(o), SECS
