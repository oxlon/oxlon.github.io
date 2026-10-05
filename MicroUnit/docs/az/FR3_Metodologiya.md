> **İngilis dilində (English version):** [FR3_Methodology.md](../FR3_Methodology.md). Rəqəmlərin yazılışı: mətndə onluq kəsr vergüllə, minliklər boşluqla ayrılır; cədvəllərdə, düsturlarda, kodda və fayl adlarında onluq kəsr proqram çıxışında olduğu kimi nöqtə ilə verilir. `AUTO` işarələri arasındakı bloklar hər icrada notebook tərəfindən bu sənəddə də Azərbaycan dilində yenidən yazılır.

# FR3 — Əmək haqqının təhlili və beşillik proqnozlaşdırılması üçün struktur ekonometrik metodologiya

**Modul:** 15.5.2 Mikroiqtisadi təhlil və proqnozlaşdırma
**Tələb:** FR3 — *"Orta aylıq əmək haqqının (onların iqtisadiyyatın sahələri, dövlət və qeyri-dövlət sektoru, büdcə və
qeyri-büdcə təşkilatları, neft və qeyri-neft sektoru üzrə səviyyəsi və artım sürətləri) təhlili və proqnozlaşdırılması"* —
orta aylıq əmək haqqının, onun **səviyyəsinin** və **artım sürətinin** iqtisadi sahələr, dövlət və qeyri-dövlət sektoru, büdcə və
qeyri-büdcə təşkilatları, neft və qeyri-neft sektoru üzrə təhlili və proqnozlaşdırılması.

**Model:** AZWAGE-FR3
**Mənbə:** `Statistik data dinamika 05.06.2026 +.xlsx`
**Faktiki məlumatlar:** illik — 2025-ci ilədək; dərc olunan bütün əmək haqqı sıraları üzrə **aylıq — 2026-cı ilin fevralınadək**
**Proqnoz:** 2026–2030, FR1-in üç makro ssenarisi əsasında
**Reallaşdırma:** `FR3.ipynb` (<!-- AUTO:v22_cells -->92 xana, onlardan 59-i kod xanası<!-- /AUTO:v22_cells -->; `miis-model` kernelində əvvəldən sona qədər xətasız icra olunur; Hissə 21 = v2)
**Çıxış faylları:** `MicroUnit/output/` qovluğunda 18 CSV faylı (yeni: `FR3_fan_wages.csv`, `FR3_specification_selection.csv`,
`FR3_homogeneity_break_tests.csv`, `FR3_minimum_wage_elasticities.csv`, `FR3_nowcast_2026.csv`, `FR3_forecast_sensitivity.csv`).
`FR3_wage_forecast_full.csv` faylı əvvəlki bütün sütunlarını saxlayır (yalnız yeni sütunlar əlavə edilib).
**v2 çıxış faylları:** `FR3_equations.json`, `FR3_indicator_catalog.csv`, `FR3_forecast_tidy.csv`, `FR3_not_forecast.csv`, `FR3_robustness_summary.csv`, `FR3_coef_sensitivity.csv`, `FR3_strings_az.csv`, `engine/FR3_state.json` (+ `.npz`); mühərrik `microlib/engines/fr3.py`.

---

<!-- AUTO:v22_note -->
## v2.2 (2026-10-05): Nazirliyin makro modulunun məlumatları və yanaşmaları

**Məlumat.** `data/macro_module/fr345_public_sources_panel.csv` (DSK 4.5–4.8 əmək haqları və 2.12 muzdlu işçilər, 19 fəaliyyət ×
dövlət / qeyri-dövlət, 2005–2024; mənbə yolu və MD5: `data/macro_module/README_fr345.md`). Onun dövlət / qeyri-dövlət əmək haqları
FR3-ün sıraları ilə dəqiq eynidir — deməli **sahə əmək haqları dərc olunur**; aşağıdakı §8.1 və §8.2 köhnəlib.

**Qəbul edildi — 8 sektor və büdcə / qeyri-büdcə təşkilatları üzrə əmək haqları** (yeni komponentlər `fr3:sw:*`, `fr3:swg:*`,
`fr3:w_budget`, `fr3:w_nonbudget` + artım; `FR3_sector_wages.csv`, tarix `FR3_dsk_sector_wages_history.csv`). Qayda 2014–2016
sürüşən başlanğıclarında (≤2020) seçilib: hər sektor son dərc olunmuş ilin (2024) nisbi əmək haqqını saxlayır; nisbi məhsuldarlıq
sürücüsü daha pisdir (RMSE 14,9% və 12,3%, DM p = 0,004; β = 0,045, SE 0,063) və rədd edilmiş kimi
reyestrdədir. Sektor çəkiləri FR3-ün sektor məşğulluğu ilə hərəkət edir; çəkili orta FR3-ün orta əmək haqqına bərabərdir, 2024 dəqiq
təkrarlanır. Büdcə təşkilatları (dövlət idarəetməsi, təhsil, səhiyyə, incəsənətdə dövlət müəssisələri — FR4-ün tərifi; 2024-də
588,6 min nəfər) 2024-cü ilin dövlət sektoru əmək haqqına nisbətini (0,923) saxlayır; qeyri-büdcə əmək haqqı eynilikdən alınır.
2025 qiymətləndirmədir. Nümunədən kənar yoxlama (kəsim 2020, 2021–2024, FR3-ün öz simulyasiya edilmiş orta əmək haqqı ilə):
təsadüfi gəzişmədən 6/8, sabit artımdan 1/8 sektorda üstündür (median U 0,64 / 1,28) —
xətalar aqreqatın +12,7% meylini miras alır; faktiki orta əmək haqqı verildikdə tərkib qaydası 7/8 və 6/8.

| Əsas ssenari | 2024 faktiki | 2030 | illik % |
|---|---|---|---|
| Sənaye | 1 247,4 | 1 934,3 | 7,59 |
| Kənd təsərrüfatı | 611,7 | 948,6 | 7,59 |
| Tikinti | 1 087,1 | 1 685,7 | 7,59 |
| Ticarət | 691,7 | 1 072,6 | 7,59 |
| Turizm və ictimai iaşə | 751,7 | 1 165,6 | 7,59 |
| Nəqliyyat | 1 392,5 | 2 159,3 | 7,59 |
| İnformasiya və rabitə | 1 672,1 | 2 592,9 | 7,59 |
| Sosial və digər xidmətlər | 1 025,6 | 1 590,4 | 7,59 |
| Büdcə təşkilatları | 900,7 | 1 502,0 | 8,90 |
| Qeyri-büdcə | 1 058,6 | 1 578,1 | 6,88 |

Nisbi əmək haqları 2024 səviyyəsində saxlanıldığı üçün **bütün sektorlar eyni tempdə artır** — məşğulluğun sektorlar arasında
yerdəyişməsinə görə düzəldilmiş orta əmək haqqı artımı (bütün sektorlar üçün ortaq amil); sektora xas əmək haqqı dinamikası yoxdur.
Bu, ≤2020 testinin dürüst nəticəsidir (heç bir sektor sürücüsü lövbərlənmiş nisbi əmək haqqını üstələmir).

**Rədd edildi (reyestrdə, istifadə olunmur).** (a) Orta, dövlət və özəl əmək haqqı tənlikləri fəaliyyət panelində artım forması
ilə (19 fəaliyyət, 2006–2020, İQİ + məhsuldarlıq + minimum əmək haqqı, gecikmiş asılı dəyişənsiz): U (təsadüfi gəzişmə / sabit artım)
0,73/3,82 (orta; cari 0,49/3,02), 0,59/1,92 (dövlət; cari 0,32/1,24),
1,04/8,70 (özəl; cari 0,87/8,48) — **heç bir əmək haqqı tənliyi sabit artımı üstələmir**. (b) Uzun DSK 2.12
panelində sektor məşğulluğu (iki tərəfli FE, β = 0,165): pay RMSE 15,50% və cari elastiklik üçün 14,22% — cari saxlanılır.

Reyestr: 97 tənlik (12-i proqnozda); 109 komponent × 3 ssenari × 2026–2030; `FR3_not_forecast.csv`: 0 sətir.
<!-- /AUTO:v22_note -->

---

## v2 (2026-10-05): tənliklər reyestri, ssenari mühərriki, dayanıqlıq

<!-- AUTO:v2 -->
**Tənliklər reyestri** (`output/FR3_equations.json`): 97 tənlik, onlardan 12-i proqnozda istifadə olunur
(E1–E4 DOLS, homogenlik real forma ilə qoyulub; sektor məşğulluğu üçün iki tərəfli FE; beş 2026 nowcast nisbəti; sahə
between paneli yalnız lövbərsiz həssaslıqda). Qalanları: E5, sürüşən başlanğıc namizədləri, həssaslıq variantları, ≤2020 qırılma/homogenlik test
reqressiyaları, P1, minimum əmək haqqı OLS/2SLS (DWH ilə), Gregory–Hansen, rədd edilmiş spesifikasiyalar, 2SLS/3SLS, sənaye və
region panelləri (within və between). Hər OLS/DOLS/2SLS/panel tənliyi statsmodels ilə yenidən qiymətləndirilib, əmsallar notebook-un
öz qiymətləri ilə yoxlanılıb (uyğunsuzluq: 0). Dayanıqlıq hökmləri (bütün tənliklər): qeyri-stabil 43, qismən stabil 38, stabil 16;
proqnozda istifadə olunanlar: qismən stabil 9, qeyri-stabil 2, stabil 1 — qeyri-stabil: FR3.E1_w_avg, FR3.E3_w_priv
(`FR3_robustness_summary.csv`).

**Ssenari mühərriki** (`microlib/engines/fr3.py`, `_fr3_core.py`; vəziyyət `output/engine/FR3_state.json` + `.npz`): notebook-un həll
kodu dəyişmədən köçürülüb (real forma/homogenlik, E4 → E1 → E2 → E3 ardıcıllığı, birgə WLS uzlaşdırması, nowcast artımının yarım
ömürlə sönməsi, sektor məşğulluğu, sahə əmək haqları). Girişlər: 16 FR1 yolu (`fr1:cpi`, `fr1:rgdp`,
`fr1:rgdpnon`, `fr1:emp`, `fr1:rexp_cur`, `fr1:rva_*`), 6 redaktə edilə bilən əmsal
(SE və 95% interval reyestrdən), 6 rıçaq (minimum əmək haqqı artımı, neft mükafatı hədəfi/yolu, nowcast yarım ömrü,
E1-in uzlaşdırmada rolu, sahə lövbəri). `selftest()`: bütün 3 ssenaridə CSV çıxışları təkrarlanır (maks. nisbi fərq
4,9·10⁻¹⁴); rıçaqlar Hissə 15 həssaslıq cədvəlini dəqiq təkrarlayır. Bir ssenari < 0,1 s.

**Tam proqnoz cədvəli** (`FR3_forecast_tidy.csv`, `FR3_indicator_catalog.csv`): 109 komponent × 3 ssenari × 2026–2030
(hamısı dolu), tarix ilə; 5–95% zolaqlar 13 komponent üçün (Əsas ssenari). `FR3_not_forecast.csv`: 0 komponent —
heç bir komponent qalmır (v2.2: 8 sektorun və büdcə/qeyri-büdcə təşkilatlarının əmək haqları DSK 4,5–4,8 əsasında proqnozlaşdırılır, `FR3_sector_wages.csv`).

**Sahə əmək haqları (v2).** Baza proqnoz LÖVBƏRLƏNİB (digər modullardakı düzəliş əmsalı qaydası): hər sahənin between əlaqəsindən
2025 qalığı sabit saxlanılır, əlavə dəyəri olmayan iki sahə (metal filizləri, digər mədənçıxarma; əvvəllər boş) 2025 nisbi əmək
haqqında saxlanılır və məşğulluqla çəkilmiş orta bütün 29 sahə üzrə sənaye əmək haqqına dəqiq bərabərdir. FR1 sahəyə xas məhsuldarlıq
yolu vermədiyi üçün bütün sahələr sənaye əmək haqqı tempi ilə artır: 2026-da +6,67%…+6,67%
(bütün ssenarilərdə). Hər sahənin öz 2017-2025 tarixi ilə müqayisə (`FR3_branch_wage_plausibility.csv`): 2026 artımı öz
illik diapazonundan kənarda — 0 / 87 sahə-ssenari; 2026–2030 orta artımı öz 5 illik orta
diapazonundan kənarda — 35 (Avtomobil, qoşqu və yarımqoşquların istehsalı, Dəri və dəridən məmulatların,ayaqqabıların istehsalı, Elektrik enerjisi, qaz və buxar istehsalı, bölüşdürülməsi və təchizatı, Geyim istehsalı, Kimya sənayesi, Komputer, elektron və optik məhsulların istehsalı, Maşın və avadanlıqların istehsalı, Metal filizlərinin hasilatı, Metallurgiya sənayesi, Mədənçıxarma sənayesinin digər sahələri, Neft məhsullarının istehsalı, Su təchizatı, tullantıların təmizlənməsi və emalı, Tikinti materiallarının istehsalı, Toxuculuq sənayesi, Tütün məmulatlarının istehsalı, Xam neft və təbii qaz hasilatı, Zərgərlik məmulatları, musiqi alətləri,idman mallarının və tibb avadanlıqlarının istehsalı).
Lövbərsiz yol (sahə məhsuldarlığına uyğun nisbi səviyyə; 2026-da -25%…+76%,
54 sahə-ssenari öz tarixi diapazonundan kənarda) yalnız həssaslıqdır:
`FR3_industry_branch_wages_unanchored.csv`, mühərrikdə `branch_anchor = False`.

**Əmsal həssaslığı** (`FR3_coef_sensitivity.csv`, ±1 SE, 2030, Əsas): ən böyük təsirlər — Real orta aylıq əmək haqqı: FR3.E2_w_non|ln_prod_non (-0,67% / +0,68%); Real qeyri-dövlət (özəl) sektor əmək haqqı: FR3.E3_w_priv|ln_prod_non (-1,98% / +2,02%); Real dövlət sektoru əmək haqqı: FR3.E4_w_state|ln_prod_non (-1,51% / +1,51%). Mətnlər: `FR3_strings_az.csv` (431 ingiliscə mətn → azərbaycanca). Kernel: `miis-model` (Python 3.13).
<!-- /AUTO:v2 -->

---

## Yenidənbaxma qeydi (2026-09-27)

Bu versiyada xarici rəyin tövsiyələri və FR1, FR4 və FR5 ilə ortaq olan ümumi düzəlişlər müqaviləsi tətbiq edilib.

| # | Nə dəyişib | Nə üçün |
|---|---|---|
| 1 | Hər bir spesifikasiya seçimi (amillər, homogenlik, qırılma fiktiv dəyişəni) **2020-ci ildə bitən** məlumatlar əsasında edilir: ≤2020 məlumatları üzrə testlər və **sürüşən başlanğıclı** proqnoz müqayisəsi (başlanğıclar 2014–2016, 2015–2020 üzrə qiymətləndirilir, Diebold–Mariano/HLN). 2021–2025 yalnız yekun nümunədən kənar yoxlama (hold-out) dövrü kimi istifadə olunur və təsadüfi gəzişmə **və** sabit artım ilə müqayisədə qiymətləndirilir. Neft sektoru əmək haqqının yoxlanılması indi faktiki istifadə olunan mexanizmi (qeyri-neft əmək haqqı × mükafat rıçağı) təsdiqləyir, əmək haqqı fondu isə validasiya cədvəlindən çıxarılıb. | Spesifikasiyalar eyni 2021–25 dövrü üzrə seçilir və yoxlanılırdı; əmək haqqı fondunun "validasiyası" konstruksiyaya görə orta əmək haqqı xətasını təkrarlayırdı. |
| 2 | Özəl sektor əmək haqqı artıq qeyri-neft əmək haqqı üzrə reqressiya edilmir; onun öz fundamental amilləri var (seçilmiş: qeyri-neft məhsuldarlığı, homogen forma). Dövlət sektoru əmək haqqı, neft sektoru əmək haqqı və nisbət alternativləri yoxlanılıb və seçilməyib. | Köhnə E3 demək olar ki, tavtoloji idi (özəl sektorun əmək haqqı qeyri-neft əmək haqqı fondunun yarısından çoxunu təşkil edir). |
| 3 | Minimum əmək haqqı: alətlər dəstindən çıxarılıb; alət kimi onun **fərmanla müəyyən edilmiş səviyyəsinin gecikməsi** ilə IV, Durbin–Wu–Hausman testləri, **2018-ci il qırılması** üçün fiktiv dəyişən və test (həmçinin Gregory–Hansen), elastikliklər **diapazon** kimi təqdim olunur; onun özəl sektor tənliyindən çıxarılması proqnoz sübutları əsasında yenidən qərara alınıb. | Minimum əmək haqqı əmək haqlarına reaksiya verir, lakin ekzogen kimi qəbul edilirdi; onun variasiyasında 2018-ci il islahatı üstünlük təşkil edir. |
| 4 | Homogenlik real formanın faktiki qoyduğu məhdudiyyət kimi — **İQİ + nominal amil elastiklikləri = 1** — hər tənlik üzrə, DOLS çərçivəsində, HAC-F ilə yoxlanılır; o, nəzəri əsaslarla bütün proqnoz tənliklərində qoyulur (ikinci mərhələ), rədd edilmə halları açıqlanır, məhdudiyyətsiz formalar həssaslıq variantlarıdır. | Əvvəlki test (yalnız İQİ elastikliyi = 1) yanlış məhdudiyyət idi. |
| 5 | Engle–Granger p-dəyərləri MacKinnon-un kointeqrasiya cavab səthindən alınır; proqnozda **DOLS** uzunmüddətli əmsallarından (DOLS qaydası) istifadə olunur; EG hər bir tənlik üçün təqdim olunur; fərq forması ilə müqayisə aparılır. | Əvvəlki p-dəyərləri adi ADF p-dəyərləri idi; `dols` müəyyən edilmişdi, lakin istifadə olunmurdu. |
| 6 | Muzdlu məşğulluq üzrə fərq əmsalı (wedge) 2021–23 üzrə kalibrlənib və 2024–25 üzrə yoxlanılıb; tarixi sıra DVX səviyyəsinə birləşdirilib. | Fərq əmsalı eyni illər üzrə kalibrlənir və "yoxlanılırdı"; əmək haqqı fondu proqnozun başlanğıc nöqtəsində sıçrayış edirdi. |
| 7 | Hər iki bölgünün (dövlət × özəl və neft × qeyri-neft) komponent tənlikləri üzrə **birgə WLS uzlaşdırılması** — hər iki eynilik dəqiq ödənilir; E1 çarpaz yoxlamadır; düzəliş amilləri təqdim olunur. | Neft/qeyri-neft ölçüsü heç vaxt uzlaşdırılmırdı (2030-cu ilədək 5–6% fərq). |
| 8 | Cari qiymətləndirmə (nowcast) çoxillik mövsümi nisbət əsasında, geriyə test (backtest) xəta zolağı ilə aparılır; onun əlavəsi bir illik yarımsönmə dövrü ilə azalır. | Bir ilin nisbəti tətbiq edilir və düzəliş 2030-cu ilədək saxlanılırdı. |
| 9 | Panellər üçün həqiqi **between** qiymətləndiricisi; Driscoll–Kraay zolaq genişliyi (bandwidth) floor(T^¼), t(T−1) əsasında statistik nəticə; "panellər səviyyə formasını dəstəkləyir" arqumenti çıxarılıb. | 0.336 "between" qiyməti birtərəfli within qiymətləndiricisi idi. |
| 10 | Qeyri-neft məhsuldarlığı **qeyri-neft** məşğulluğuna bölünməklə hesablanır. | O, neft sektoru daxil olmaqla bütün məşğul əhaliyə bölünürdü. |
| 11 | **Yelpik qrafikləri** reallaşdırılıb (tarixi qalıq trayektoriyalarının yenidən seçilməsi + parametr + cari qiymətləndirmə + FR1 makro çəkilişləri) və `FR3_fan_wages.csv` faylına ixrac edilib. | Vəd edilmişdi, lakin reallaşdırılmamışdı. |
| 12 | Mətn bütövlükdə düzəldilib (bax §3, §6, §8). | Bir sıra müddəalar nəticələrə zidd idi. |

**İkinci mərhələ (2026-09-28).** Müstəqil yoxlama daha beş qərara gətirib çıxarıb və onların hamısı reallaşdırılıb:
(a) nümunədən kənar yoxlama **dəqiq proqnozdakı kimi** lövbərlənir (hər tənliyin kəsim nöqtəsindən əvvəlki son ildəki öz
qalığı); (b) uzunmüddətli **homogenlik nəzəri əsaslarla hər bir proqnoz tənliyində qoyulur** (daimi pul illüziyası yoxdur), qısa
nümunənin onu rədd etdiyi hallarda bu açıqlanır, məhdudiyyətsiz formalar isə həssaslıq variantlarıdır; (c) 2018-ci il **qırılma
fiktiv dəyişəni əsas spesifikasiyaya daxil deyil**, çünki onun proqnoz dəqiqliyini 2018-ci ildən əvvəl nümunədən kənar
qiymətləndirmək mümkün deyil (onun 0,843 dövlət sektoru əmək haqqı elastikliyi həssaslıq variantıdır), Diebold–Mariano testləri
isə üst-üstə düşən çoxbaşlanğıclı xətalara qarşı dayanıqlıdır (Bartlett HAC, h−1 gecikmə); (d) uzlaşdırmada **E1 səviyyə
məhdudiyyəti deyil, çarpaz yoxlamadır**; (e) yelpik qrafiklərində **tarixi qalıq trayektoriyalarının yenidən seçilməsindən**
istifadə olunur (qalıq dinamikası qiymətləndirilmir); FR1 çəkilişləri yalnız sonlu olmayan dəyərlərə görə süzgəcdən keçirilir;
(f) **siyasət rıçaqlarının uyğunluğu (koherentliyi) qaydası** (FR1/FR3/FR5 üçün ortaq): minimum əmək haqqı əsas tənliyə yalnız
onun işarəsi nəzəriyyəyə uyğun olduqda (və ya onun fərq formasındakı qiyməti əhəmiyyətli dərəcədə eyni işarəli olduqda) və o,
2018-ci il qırılma nəzarətindən sonra da saxlanıldıqda daxil olur — bu, onu özəl sektor əmək haqqı tənliyindən çıxarır.

**Əsas göstəricilər üçün nəticələr.** 2026–2030-cu illərdə Əsas ssenari üzrə orta əmək haqqının artımı **nominal ifadədə ildə
+7,13%, real ifadədə +2,64%** təşkil edir (ilk versiyada +5,26% / +1,19%). Proqnozun öz lövbərləmə qaydası ilə 2021–2025
nümunədən kənar yoxlama **sabit artımla müqayisədə zəifdir**: model 5 sıranın 4-ündə təsadüfi gəzişmədən üstündür, lakin sabit
artımdan **heç bir sırada** üstün deyil (orta əmək haqqı: təsadüfi gəzişməyə qarşı Theil U 0,49, sabit artıma qarşı 3,03;
2025-ci ilədək səviyyə xətası +12,7%). Heç bir tənlik kointeqrasiyanı təsdiqləmir; tənliklər təsdiqlənmiş kointeqrasiya
münasibətləri deyil, sabit düzəliş əmsallı təsviri uzunmüddətli münasibətlərdir.

**Asılılıq qeydi.** FR3 FR1-in ssenarilərini və `FR1_fan_draws.csv` faylını oxuyur (bu icrada 500 çəkiliş, heç biri
çıxarılmayıb). Aşağıdakı bütün rəqəmlər bu icraya aiddir və yekun ardıcıl FR1 → FR3 təkrar icrası ilə dəyişəcək.

---

## 1. Əsas nəticə: tələb olunan dörd bölgü bir-birinin içinə yerləşmir

| Bölgü | Struktur | Rəqəmlərlə yoxlama |
|---|---|---|
| **Dövlət × qeyri-dövlət** | Muzdlu işçilərin **dəqiq bölgüsü** | Ümumi əmək haqqı = məşğulluqla çəkilmiş orta, **0.17–0.31%** dəqiqliklə |
| **İqtisadi sahələr** (8 DSK sahəsi) | Muzdlu işçilərin **dəqiq bölgüsü** | Sahələr üzrə məşğulluğun cəmi ümumi göstəriciyə **tam bərabərdir (0.000)** |
| **Neft / qeyri-neft** | Üçüncü qrup deyil, **kəsişən bölgü** | Onun üçüncü qrup kimi nəzərə alınması **6.7–10.4% ikiqat hesablamaya** gətirib çıxarır; neft/qeyri-neft çəkiləri ilə orta göstərici 1.9–3.7% dəqiqliklə təkrarlanır |
| **Büdcə / qeyri-büdcə** | Dövlət sektorunun alt bölgüsü, qismən müşahidə olunur | İşçi sayı və sosial sığorta haqları müşahidə olunur; əmək haqqı səviyyəsi **müəyyən edilə (identifikasiya oluna) bilmir** |

Neft şirkətləri *həm* dövlət (SOCAR), *həm də* özəl (AIOC konsorsiumu) şirkətlərdir, ona görə də neft bölgüsü institusional
bölgünü kəsir. Buna görə də FR3 eyni ölkə üzrə orta əmək haqqına aparan **iki aqreqasiya** daşıyır və proqnozda **hər ikisini**
onunla birgə uzlaşdırır (§6.3).

---

## 2. İlk növbədə həll edilməli olan ölçmə məsələsi

Əmək haqqı **muzdlu işçiyə** ödənilir. Ümumi məşğul əhaliyə özünüməşğul şəxslər də daxildir: 2025-ci ildə **2,06 milyon**
muzdlu işçiyə qarşı **5,11 milyon** məşğul şəxs.

| Əmək haqqı fondu, 2025 | mln AZN |
|---|---|
| əmək haqqı × **muzdlu işçilər** × 12 | 27 263 |
| DVX-in bildirdiyi əmək haqqı fondu | 26 527 |
| muzdlu işçilərin əməyinin ödənişi (milli hesablar) | 38 227 |
| əmək haqqı × **ümumi məşğul əhali** × 12 | **67 566** ← 2.5 dəfə səhv |

Muzdlu məşğulluq yalnız 2021–2025 üçün dərc olunur. Əvvəlki illər üçün o, muzdlu işçilərin əməyinin ödənişinin illik əmək
haqqına bölünməsi yolu ilə hesablanır; bu zaman fərq əmsalı (wedge) (**1,452**) **2021–2023 üzrə kalibrlənir** (nümunədaxili
xəta ≤ 1,51%) və **2024–2025 üzrə yoxlanılır** (nümunədən kənar xəta **4,6%**-dək). Daha sonra tarixi sıra DVX səviyyəsinə
**birləşdirilir** (2021–2025 üçün DVX-in özü; hesablanmış sıra 2021-ci ildə nisbət üzrə birləşdirilir, amil 1,014), proqnoz isə
eyni DVX səviyyəsindən başlayır — beləliklə 2026-cı ildə əmək haqqı fondu +7,5% artır, yəni əmək haqqı artımı (+6,9%) üstəgəl
muzdlu məşğulluğun artımı qədər, səviyyə qırılması olmadan.

**FR1-də edilməli olan düzəliş:** FR1-in ev təsərrüfatlarının gəlirləri tənliyi öz əmək haqqı fondunu ümumi məşğulluq əsasında
qurur; səviyyə artıq qiymətləndirilir, lakin loqarifmlərdə xəta əsasən sərbəst hədd (intercept) tərəfindən udulur.

**Qeyri-neft məhsuldarlığı** qeyri-neft əlavə dəyərinin **qeyri-neft** məşğulluğuna bölünməsidir. Neft sektorunda məşğulluq DVX
göstəricisidir (2021–2025); 2021-ci ilədək onun əvəzinə (proksi kimi) DVX-ə nisbət üzrə birləşdirilmiş (2016–2020) mədənçıxarma
sənayesində işçi sayından, 2016-cı ilədək isə sabit paydan istifadə olunur; proqnozda 2025-ci il neft payı (məşğul əhalinin
0,94%-i) sabit saxlanılır. Bu düzəliş səviyyəni təxminən 1%, 2005–2025-ci illər üzrə artımı isə ümumilikdə 0,5 faiz bəndi dəyişir.

---

## 3. Nəzəriyyə və faktiki yoxlanılan məhdudiyyətlər

$$\ln W = \alpha + \beta \ln(\text{productivity}) + \gamma \ln P + \delta \ln(\text{minimum wage}) + \theta\,\text{tightness} + \sum_j \phi_j \ln W_j$$

Bütün statistik nəticələr n/(n−k) miqyaslandırması ilə HAC (Newey–West), t(n−k) p-dəyərləri və HAC-F(m, n−k) Wald testləri
əsasında çıxarılır. Uzunmüddətli münasibətlər **DOLS** ilə qiymətləndirilir (yalnız *izahedici dəyişənlərin* fərqlərinin
qabaqlayıcı və gecikmə dəyərləri; qalıq sərbəstlik dərəcələri ≥ 10 olduqda ±1, əks halda cari fərqlər, bu da mümkün olmadıqda OLS).

### 3.1 Nominal homogenlik — düzgün yoxlanılır, sonra nəzəri əsaslarla qoyulur

Tənlikdə nominal izahedici dəyişən (minimum əmək haqqı, digər əmək haqqı) olduqda tənliyin real ifadədə yazılması γ = 1 deyil,
**γ + δ = 1** məhdudiyyətini qoyur. İlkin versiyada yalnız γ = 1 yoxlanılırdı (OLS səviyyələrində p = 0,65); düzgün məhdudiyyət
isə aqreqat üçün OLS səviyyələrində rədd edilir (cəm 1,186, s.x. 0,073, HAC-F p = 0,018).

Məhdudiyyət hər namizəd üzrə, DOLS çərçivəsində, 2020-ci ildə bitən məlumatlar əsasında yoxlanılır (tam nümunə məlumat üçün
verilir; `FR3_homogeneity_break_tests.csv`). Seçilmiş tənliklər üçün:

| Tənlik (amillər) | qiymət elastiklikləri cəmi ≤2020 (s.x.) | HAC-F p ≤2020 | cəm / p ≤2025 | test nəticəsi |
|---|---|---|---|---|
| E1 aqreqat (məhsuldarlıq) | 1.305 (0.148) | 0.057 | 1.290 / 0.000 | ≤2020 rədd edilmir (aşağı güc); tam nümunədə rədd edilir |
| E2 qeyri-neft (qeyri-neft məhsuldarlığı) | 1.017 (0.196) | 0.932 | 1.028 / 0.849 | rədd edilmir (aşağı güc) |
| E3 özəl (qeyri-neft məhsuldarlığı) | 0.805 (0.043) | 0.001 | 0.588 / 0.009 | **rədd edilir** |
| E4 dövlət (qeyri-neft məhsuldarlığı, minimum əmək haqqı) | 0.970 (0.156) | 0.850 | 1.177 / 0.365 | rədd edilmir (aşağı güc) |
| E5 neft (qeyri-neft əmək haqqı; yalnız istinad üçün) | 2.185 (0.261) | 0.001 | 1.569 / 0.116 | rədd edilir — E5 proqnozda istifadə olunmur |

**Qərar.** Uzunmüddətli homogenlik **nəzəri əsaslarla hər bir proqnoz tənliyində qoyulur**: c ≠ 1 cəmi ilə real əmək haqqı hər
il sonsuzadək (c − 1) × inflyasiya qədər sürüşərdi (özəl sektor əmək haqqı üçün məhdudiyyətsiz 0,59 İQİ elastikliyi real özəl
sektor əmək haqqını ildə təxminən 0,4 × inflyasiya qədər aşındırardı). Özəl sektor əmək haqqı üçün rədd edilmə açıqlanır; o,
nominal özəl sektor əmək haqqının qiymətlərdən geri qaldığı 2021–22-ci illərdəki inflyasiya sıçrayışını (İQİ +12,0% və +14,4%)
əks etdirir. Bütün namizədlər homogen formada qiymətləndirilir (§4), məhdudiyyətsiz formalar isə proqnoz həssaslığı
variantlarıdır (§7). Yoxlanılan cəmlər üzrə 0,10–0,20 standart xətalar o deməkdir ki, "rədd edilmir" nəticəsi təsdiq deyil,
aşağı gücün nəticəsidir.

### 3.2 2018-ci il minimum əmək haqqı islahatı: qırılma testi

Səviyyə sürüşməsi fiktiv dəyişəni D18 (2018-ci ildən 1) hər bir namizədin ümumi formasında yoxlanılır (HAC-F, ≤2020). O, dövlət
sektoru əmək haqqı üçün (hər iki nümunədə p < 0,001), minimum əmək haqqı daxil olan qeyri-neft namizədi və nisbət modeli üçün
əhəmiyyətlidir; E1 (p = 0,559), E2 (0,961) və ya seçilmiş E3 (0,754) üçün əhəmiyyətli deyil. D18 hər bir seçim başlanğıcında
(2014–2016) sıfıra bərabər olduğundan onu ehtiva edən spesifikasiyanın **proqnoz dəqiqliyini nümunədən kənar qiymətləndirmək
mümkün deyil**, ona görə də o, **əsas spesifikasiyaya daxil edilmir**; D18 daxil olan dövlət sektoru əmək haqqı versiyası
(minimum əmək haqqı elastikliyi 0,843) proqnoz həssaslığı variantıdır. Gregory–Hansen tipli test (naməlum tarixdə bir səviyyə
sürüşməsi, C modelinin kritik qiymətləri) heç bir proqnoz tənliyi üçün kointeqrasiyanı təsdiqləmir (ADF* −3,94-dən −4,32-dək,
5% kritik qiymətləri isə −4,61 / −4,95).

### 3.3 Əmək haqlarının qarşılıqlı ötürülməsi (spillover) — "əlaqəli sektorlar" mexanizmi

Sürüşən başlanğıclı müqayisədə (§4) namizəd kimi yoxlanılıb; heç biri seçilməyib:

- Özəl sektor əmək haqqında **neft sektoru əmək haqqı ("Holland xəstəliyi")**: sürüşən RMSE 5,84%, seçilmiş tənlikdə isə 5,09% (DM p = 0,16).
- **Dövlət sektoru əmək haqqının özəl sektor əmək haqqına ötürülməsi**: 5,18%, seçilmiş tənlikdə isə 5,09% (DM p = 0,85) — daha yaxşı deyil və daha mürəkkəbdir.
- **Özəl/dövlət nisbət modeli**: 12,62%, seçilmiş tənlikdə isə 5,09% (DM p = 0,006).
- **Özəl sektor əmək haqqının dövlət sektoru əmək haqqına ötürülməsi** (OLS səviyyələri, fiskal imkanlar və minimum hədd ilə): +0,009, p = 0,987.
- İlkin E3 (özəl sektor əmək haqqının real qeyri-neft əmək haqqı üzrə reqressiyası) demək olar ki, tavtoloji olduğu üçün çıxarılıb (ilk icrada OLS 0,53, 2SLS isə 0,17).

Əmək haqları iki aqreqasiya eyniliyi və uzlaşdırma vasitəsilə, neft sektoru əmək haqqı isə mükafat rıçağı vasitəsilə
əlaqələndirilir.

### 3.4 Minimum əmək haqqı: indeksləşdirmə, endogenlik və elastikliklər diapazonu

Minimum əmək haqqı əmək haqlarına reaksiya verir: onun orta əmək haqqına görə uzunmüddətli elastikliyi **1,50**-dir (DOLS;
vahid indeksləşdirmə rədd edilir, p < 0,001). Onun üçün alət kimi **fərmanla müəyyən edilmiş səviyyənin gecikməsindən** istifadə
olunur (ilin əmək haqqı nəticələrindən əvvəl müəyyən edilir; bu, avtoreqressiv hədd deyil, alətdir). Alətin güclü olduğu hallarda
(5 hal, birinci mərhələ F 10–32: D18-siz dörd tənliyin hamısı və D18 daxil olan aqreqat) **Durbin–Wu–Hausman testi 5 halın
4-ündə ekzogenliyi rədd edir** (özəl sektor əmək haqqı üçün rədd etmir, p = 0,34); digər D18 variantlarında alət zəifdir (F 0,5)
və həmin IV qiymətləri nəzərə alınmır. Etibarlı variantlar üzrə diapazonlar (OLS səviyyələri, DOLS, 2SLS; D18 ilə və onsuz;
hamısı homogen formada):

| Tənlik | minimum əmək haqqı elastikliyinin diapazonu | proqnozda |
|---|---|---|
| aqreqat (E1 namizədi) | 0.14 – 0.32 | yox (seçilməyib) |
| qeyri-neft (E2 namizədi) | 0.06 – 0.49 | yox (seçilməyib) |
| **özəl** (E3 namizədi) | **−0.25 – −0.01** | **yox** — rıçaqların uyğunluğu qaydasını ödəmir; yalnız həssaslıq variantı (−0.247) |
| **dövlət** (E4) | **0.24 – 0.84** | **bəli: 0.386** (DOLS, fiktiv dəyişənsiz; 3SLS 0.096; D18 versiyası 0.843 həssaslıq variantı kimi) |

Homogen formada minimum əmək haqqı özəl sektor əmək haqqı üçün ən aşağı sürüşən RMSE verir (3,65%, onsuz isə 5,09%, DM
p = 0,054), lakin **mənfi** işarə ilə. O, ≤2020 məlumatları üzrə **siyasət rıçaqlarının uyğunluğu qaydasını** ödəmir: (a) səviyyədə
−0,044, fərq formasındakı qiymət isə −0,029 (p = 0,66), yəni nə nəzəriyyəyə uyğundur, nə də fərqlərdə əhəmiyyətli dərəcədə
mənfidir; (b) 2018-ci il fiktiv dəyişəni ilə o, +0,008-ə çevrilir (p = 0,93) — islahatın zamanlaması ilə bağlı artefakt (islahat
dövlət sektorunda əmək haqqını artırdı; özəl sektor əmək haqqı bunu izləmədi). Buna görə də o, **özəl sektor tənliyindən
çıxarılır**; minimum əmək haqqı daxil olan E3 variantı işarələnmiş həssaslıq variantıdır. Minimum əmək haqqı rıçağı indi dövlət
sektoru əmək haqqına (və uzlaşdırma vasitəsilə aqreqata) təsir edir və ssenarilərin sıralanması hər bir qrup üçün monotondur (§7).

### 3.5 Əmək bazarının gərginliyi — belə kanal mövcud deyil

İşsizlik artım formasında müsbət işarə ilə (+1,3-dən +2,0-dək, p 0,10–0,41), səviyyələrdə isə əhəmiyyətsiz daxil olur. Ölçülən
işsizlik **2020-ci il istisna olmaqla hər il 4,9–5,6% daxilində** qalıb. Çıxarılıb.

---

## 4. Nümunədən kənar yoxlamadan əvvəl sürüşən başlanğıclar üzrə seçilmiş spesifikasiyalar

Başlanğıclar: 2014, 2015 və 2016; qiymətləndirmə başlanğıc ilinədək (daxil olmaqla) olan məlumatlar üzrə aparılır (DOLS qaydası),
lövbərləmə başlanğıc ilinin öz qalığı ilə həyata keçirilir, 2020-ci ilədək hər il faktiki amillərlə proqnozlaşdırılır (hər namizəd
üzrə 15 xəta), bütün namizədlər homogen formadadır. Siyasət rıçağı uyğunluq (koherentlik) qaydasını (§3.4) ödəməyən namizədlər
qiymətləndirilir və göstərilir, lakin seçilə bilməz. Ən aşağı RMSE-yə malik namizəd seçilir, daha sadə namizədin əhəmiyyətli
dərəcədə pis olmadığı hallar istisna olmaqla (h−1 = 5 gecikmə üzrə Bartlett HAC ilə DM-HLN, çoxbaşlanğıclı xətaların üst-üstə
düşməsinə qarşı dayanıqlıdır; p > 0,10).

| Qrup | Namizəd | rıçaq uyğundur | homogenlik testi ≤2020 | sürüşən RMSE % | ən yaxşı namizədə qarşı DM p | seçilib |
|---|---|---|---|---|---|---|
| E1 | məhsuldarlıq + minimum əmək haqqı | bəli | rədd edilməyib | 10.24 | 0.68 | |
| E1 | **məhsuldarlıq** | — | rədd edilməyib | **8.87** | — | ✓ |
| E2 | qeyri-neft məhsuldarlığı + minimum əmək haqqı | bəli | rədd edilməyib | 12.36 | 0.12 | |
| E2 | **qeyri-neft məhsuldarlığı** | — | rədd edilməyib | **8.26** | — | ✓ |
| E3 | **qeyri-neft məhsuldarlığı** | — | rədd edilib | **5.09** | — | ✓ |
| E3 | qeyri-neft məhsuldarlığı + minimum əmək haqqı | **XEYR** | rədd edilib | 3.65 | daha yaxşı (p 0.054) | çıxarılıb |
| E3 | + dövlət sektoru əmək haqqı | — | rədd edilib | 5.18 | 0.85 | |
| E3 | + neft sektoru əmək haqqı ("Holland xəstəliyi") | — | rədd edilməyib | 5.84 | 0.16 | |
| E3 | dövlət sektoru əmək haqqına nisbət | — | rədd edilməyib | 12.62 | 0.006 | |
| E4 | **qeyri-neft məhsuldarlığı + minimum əmək haqqı** | bəli | rədd edilməyib | **15.96** | — | ✓ |
| E4 | yalnız minimum əmək haqqı | bəli | rədd edilib | 46.43 | 0.005 | |
| E4 | fiskal imkanlar + minimum əmək haqqı | **XEYR** (qırılma nəzarətindən keçmir) | rədd edilməyib | 22.08 | 0.46 | |

**Neft sektoru əmək haqqı.** Eyni başlanğıclar üzrə neft/qeyri-neft mükafatının son dəyərində saxlanılması (RMSE 22,9%)
başlanğıcdan əvvəlki orta göstəricidən (37,7%, DM p = 0,003) və xətti trenddən (41,1%, p = 0,047) üstündür; kvadratik trend daha
pisdir (54,5%, p = 0,27). Mükafat 3,2×-dən (2010) 6,6×-ə (2017) qədər yüksəlib və **3,75×-ə (2025)** qədər enib. Neft sektoru
əmək haqqı E5 əsasında **proqnozlaşdırılmır**; o, uzlaşdırılmış qeyri-neft sektoru əmək haqqının açıq bildirilmiş **mükafat
rıçağına** hasilidir.

---

## 5. Yekun tənliklər dəsti

Homogen (real) formada tam nümunə üzrə DOLS; proqnozda uzunmüddətli əmsallardan istifadə olunur.

| # | Asılı dəyişən | Uzunmüddətli əmsallar (HAC s.x.) | qiymətləndirici, n, sərbəstlik dərəcəsi | R² | EG kointeqrasiya p | fərq forması |
|---|---|---|---|---|---|---|
| E1 | ln real orta əmək haqqı (çarpaz yoxlama) | məhsuldarlıq 1.040 (0.054) | DOLS(±1), 25, 20 | 0.974 | 0.339 | 0.563 ⚑ |
| E2 | ln real qeyri-neft sektoru əmək haqqı | qeyri-neft məhsuldarlığı 1.052 (0.086) | DOLS(±1), 20, 15 | 0.956 | 0.794 | 0.880 |
| E3 | ln real özəl sektor əmək haqqı | qeyri-neft məhsuldarlığı 0.432 (0.129) | DOLS(±1), 20, 15 | 0.851 | 0.614 | 0.457 |
| E4 | ln real dövlət sektoru əmək haqqı | qeyri-neft məhsuldarlığı 0.626 (0.154); real minimum əmək haqqı 0.386 (0.074) | DOLS(±1), 20, 11 | 0.981 | 0.330 | 0.988; 0.104 ⚑ |
| E5 | ln nominal neft sektoru əmək haqqı (yalnız istinad üçün) | qeyri-neft sektoru əmək haqqı −0.089 (0.514); ln İQİ 1.658 (0.822) | DOLS(0), 20, 15 | 0.916 | 0.927 | — |
| P1 | ln minimum əmək haqqı (təqdim olunur, istifadə olunmur) | orta əmək haqqı 1.502 (0.052) | DOLS(±1), 25, 20 | 0.988 | 0.905 | — |

⚑ = səviyyə əmsalı fərq formasındakı qiymətin 95%-lik intervalından kənardadır. **Heç bir tənlik üçün kointeqrasiya
təsdiqlənmir** (EG p 0,33–0,93), ona görə də `FR3_equation_audit.csv` faylında bütün t-statistikaları *təsviri* kimi işarələnir;
qalıqların stasionar olduğu göstərilmədiyi üçün baza düzəliş əmsalları sabit saxlanılır.

**Panellər.** Sənaye paneli (əlavə dəyəri olan 27 alt sahə, 10 il) 0,065 səviyyəsində ikitərəfli **within** elastikliyi (DK, t(9)
p = 0,078) və **0,305** səviyyəsində həqiqi **between** elastikliyi (alt sahə ortaları üzrə; s.x. 0,049) verir; birtərəfli FE
qiymətləndirməsi olan 0,336 within qiymətləndiricisidir. Regional panel within üzrə 0,070, between üzrə isə 0,269 (s.x. 0,186,
13 rayon) verir. Bunlar səviyyə fərqlərinə dair en kəsiyi üzrə (cross-sectional) faktlardır; onlar ölkə üzrə sıralar üçün
kointeqrasiya edən səviyyə münasibətini **təsdiqləmir**.

**Eyni zamanlılıq.** Cari minimum əmək haqqı artıq alət deyil. Yenidən baxılmış alətlər dəsti ilə 2SLS dövlət sektoru əmək haqqı
tənliyində minimum əmək haqqı əmsalını (D18 ilə) 0,474-dən (OLS) 0,922-yə dəyişir, lakin birinci mərhələ **zəifdir** (F = 4,0)
və Sargan p = 0,032 (**rədd edilir**); E5 üçün OLS 0,257, 2SLS isə −0,387 verir, Sargan p = 0,043 (**rədd edilir**). Bu fərqlər
böyükdür. Dörd proqnoz tənliyi üzrə 3SLS (2010–2025, 16 müşahidə) yalnız çarpaz yoxlamadır (dövlət sektoru əmək haqqında minimum
əmək haqqı əmsalı 0,096).

---

## 6. Validasiya

**Qiymətləndiricilər** maşın dəqiqliyi ilə `statsmodels` ilə müqayisədə yenidən yoxlanılıb (OLS, HC1, n/(n−k) ilə HAC, `coint`
vasitəsilə Engle–Granger p, 2SLS, 3SLS, panel FE).

### 6.1 Dinamik ex-post nümunədən kənar yoxlama (hold-out), 2021–2025

Hər şey 2020-ci ilədək (daxil olmaqla) olan məlumatlar üzrə yenidən qiymətləndirilir; düzəliş əmsalları **dəqiq proqnozdakı
qaydaya** uyğun müəyyən edilir (hər tənliyin öz 2020-ci il qalığı); mükafat rıçağı 2020-ci il dəyərində (5,14×) saxlanılır;
uzlaşdırma proqnozdakı kimi aparılır (E1 çarpaz yoxlamadır), bu zaman məşğulluq payları 2021-ci il DVX məlumatlarından götürülür
(açıq bildirilmiş əvəzedici göstərici — daha əvvəlki bölgü mövcud deyil), eynilik uyğunsuzluqları isə 2020-ci il əmək haqları ilə
hesablanır; faktiki amillər və faktiki minimum əmək haqqı; heç bir əmək haqqı geri ötürülmür; cari qiymətləndirmə (nowcast)
tətbiq edilmir. Loqarifmik xətalar ×100; sabit artım = hər sıranın 2010–2020 üzrə orta artımı.

| Dəyişən | model RMSE | təsadüfi gəzişməyə qarşı U | sabit artıma qarşı U | DM p: təsadüfi gəzişmə / sabit artım | 2025-ci il səviyyə xətası |
|---|---|---|---|---|---|
| **orta əmək haqqı** | 14.5% | **0.49** | **3.03** | 0.15 / 0.01 | +12.7% |
| qeyri-neft sektoru əmək haqqı | 11.9% | 0.37 | 1.50 | 0.11 / 0.20 | +8.8% |
| özəl sektor əmək haqqı | 18.8% | 0.87 | 8.48 | 0.63 / 0.01 | +20.0% |
| dövlət sektoru əmək haqqı | 11.8% | 0.33 | 1.24 | 0.09 / 0.47 | +7.4% |
| neft sektoru əmək haqqı (qeyri-neft × mükafat rıçağı) | 35.3% | 3.80 | 1.07 | 0.003 / 0.39 | +49.3% |

**Əsas nəticə: model 5 sıranın 4-ündə təsadüfi gəzişmədən üstündür (median U 0,49), sabit artımdan isə heç birində üstün deyil
(median U 1,50).** Sabit artıma qarşı DM p < 0,10 olan hallarda (orta və özəl sektor əmək haqqı) model əhəmiyyətli dərəcədə
*pisdir*. Xətalar 2020-ci il (COVID ili) qalığı ilə lövbərləmədən və 2021–22-ci illərin inflyasiya sıçrayışından qaynaqlanır:
lövbər kimi 2018–2020 orta qalığından istifadə edildikdə (işarələnmiş həssaslıq variantı) RMSE 5,3% (orta), 3,4% (qeyri-neft),
15,5% (özəl), 6,5% (dövlət), 25,8% (neft) olardı. Digər həssaslıq variantları: uzlaşdırılmamış E1-in özü üzrə orta əmək haqqı
RMSE-si 8,7%-dir; E1-ə sonlu çəki verilməsi 12,6% verir; E1-ə *uyğun* uzlaşdırma — 8,7%. Əmək haqqı fondu ayrıca hədəf deyil
(onun xətası konstruksiyaya görə orta əmək haqqı xətasına bərabərdir). Neft sektoru üzrə xəta mükafatla bağlıdır: faktiki
göstərici 3,75×-ə enərkən mükafat 5,14× səviyyəsində saxlanılıb.

### 6.2 2026-cı ilin cari qiymətləndirilməsi (nowcast)

2026-cı ilin yanvar–fevral ortası **2021–2025 üzrə həmin dövrün illik ortaya orta nisbətinə** bölünür. Geriyə test (backtest;
hər il üçün yalnız əvvəlki nisbətlərdən istifadə etməklə, 2022–2025) xəta zolağını verir. Bu qısa geriyə testdə çoxillik qayda
birillik y/y (ötən ilə nisbətən) qaydasından daha dəqiq deyil (orta əmək haqqı üzrə RMSE 2,18%-ə qarşı 2,11%); ona üstünlük
verilir, çünki o, bir ilin mövsümiliyinə əsaslanmır, və onun zolağı yelpik qrafiklərinə daxil olur.

| Sıra | 2025 | 2026 cari qiymətləndirmə | artım | geriyə test RMSE | köhnə y/y qaydası |
|---|---|---|---|---|---|
| orta əmək haqqı | 1 102.9 | 1 179.4 | +6.94% | ±2.2% | 1 161.6 |
| neft sektoru | 3 938.6 | 4 320.2 | +9.69% | ±6.3% | 4 330.8 |
| qeyri-neft sektoru | 1 050.7 | 1 124.4 | +7.02% | ±1.8% | 1 105.3 |
| dövlət sektoru | 1 080.8 | 1 167.2 | +7.99% | ±2.6% | 1 152.4 |
| özəl sektor | 1 124.4 | 1 187.1 | +5.58% | ±1.8% | 1 168.5 |

Cari qiymətləndirmənin modelə əlavəsi 2026-cı ildə tam tətbiq olunur və hər il yarıbayarı azalır (bu, asılı dəyişənin modeli
deyil, ekspert qiymətləndirməsinə əsaslanan düzəliş qaydasıdır). Baza düzəliş əmsalları (öz 2025-ci il qalıqları: E1 0,139,
E2 0,043, E3 −0,092, E4 0,077 loqarifmik bənd) sabit qalır.

### 6.3 Hər iki bölgünün birgə uzlaşdırılması

Komponent tənlikləri (E2, E3, E4; neft sektoru əmək haqqı mükafat vasitəsilə) çəkili ən kiçik kvadratlar üsulu (Stoun metodu)
ilə uzlaşdırılır; çəkilər hər tənliyin 2021-ci ilədək sürüşən başlanğıclar üzrə MSE-si ilə tərs mütənasibdir və hər iki eynilik
dəqiq ödənilir: institusional $W = k_1(s_{state}W_{state}+s_{priv}W_{priv})$ və neft/qeyri-neft $W = k_2(s_{oil}\,\text{prem}\,W_{non}+(1-s_{oil})W_{non})$;
burada məlumatların özündəki 2025-ci il uyğunsuzluqları $k_1$ = 0,998, $k_2$ = 0,982 sabit saxlanılır. **E1 səviyyə
məhdudiyyəti deyil**: o, azalan neft hasilatının aşağı çəkdiyi ümumi məhsuldarlıqla müəyyən edilir, komponentlər isə qeyri-neft
məhsuldarlığından istifadə edir, ona görə də E1 və E2 bir-birindən uzaqlaşır (E1-ə sonlu çəki verildikdə aqreqat aşağı çəkilmiş,
qeyri-neft sektoru əmək haqqı isə 2030-cu ilədək öz tənliyindən ~3% aşağı salınmışdı); E1-in 2021-ci ilədək göstəricisi (RMSE
8,9%) E2-ninkindən (8,3%) yaxşı deyil. Aqreqat uzlaşdırılmış komponentlər üzrə eynilikdir, E1 isə çarpaz yoxlamadır. Eynilik
qalıqları hər ssenari və hər il üzrə < 10⁻⁷%-dir. Əsas ssenari üzrə uzlaşdırma amilləri (uzlaşdırılmış ÷ tənlik), 2026 → 2030:
dövlət 1,005 → 1,062, özəl 1,001 → 1,007, qeyri-neft 0,997 → 0,966; uzlaşdırılmış aqreqat E1-in öz proqnozundan 0,0% → +3,9%
fərqlənir. 2026-cı ildə uzlaşdırılmış dəyərlər cari qiymətləndirmələrdən 0,6% daxilində fərqlənir.

---

## 7. Proqnoz nəticələri, 2026–2030

Makro amillər FR1-in ssenarilərindən götürülür. FR3-ün rıçaqları: **minimum əmək haqqı** (ildə 6% / 3% / 9% nominal artım) və
**neft mükafatının trayektoriyası** (2026-cı il cari qiymətləndirmə dəyəri olan 3,84×-dən 2030-cu ilədək 3,4× / 3,2× / 3,7×-ə
qədər). Muzdlu məşğulluq DVX səviyyəsindən başlayaraq 2025-ci ilin muzdlu işçi payı ilə FR1-in məşğulluğunu izləyir; dövlət/özəl
və neft sektoru payları sabit saxlanılır. FR3 heç bir əhali fərziyyəsindən istifadə etmir.

| Əsas | 2025 | 2030 | nominal, illik % | real, illik % |
|---|---|---|---|---|
| Orta əmək haqqı | 1 102.9 | 1 556.4 | **+7.13** | **+2.64** |
| Qeyri-neft sektoru | 1 050.7 | 1 495.0 | +7.31 | +2.81 |
| Dövlət sektoru | 1 080.8 | 1 625.9 | +8.51 | +3.96 |
| Özəl sektor | 1 124.4 | 1 507.1 | +6.03 | +1.59 |
| Neft sektoru | 3 938.6 | 5 083.1 | +5.23 | +0.83 |

| | Əsas | Mənfi | İslahat |
|---|---|---|---|
| Orta əmək haqqı, nominal, illik % | 7.13 | 5.67 | 8.59 |
| Orta əmək haqqı, **real**, illik % | 2.64 | 1.55 | 3.74 |
| Real qeyri-neft sektoru əmək haqqı, illik % | 2.81 | 1.82 | 3.76 |
| Real özəl sektor əmək haqqı, illik % | 1.59 | 1.13 | 2.03 |
| Real dövlət sektoru əmək haqqı, illik % | 3.96 | 2.10 | 5.83 |
| Real neft sektoru əmək haqqı, illik % | 0.83 | −1.35 | 3.49 |

**Mənfi ≤ Əsas ≤ İslahat sıralanması hər bir qrup üçün ödənilir** (notebook-da yoxlanılıb).

Əsas ssenari üzrə əmək haqqı fondu: 2026-cı ildə 29 302 mln manat (+7,5%), 2030-cu ildə 39 729 mln manata qədər artır.
**Dövlət/özəl nisbəti** Əsas ssenaridə 2026-cı ildə 0,99, 2030-cu ildə 1,08 təşkil edir (2027-ci ildə 1,00 həddini keçir),
2030-cu ildə Mənfi ssenaridə 1,01, İslahat ssenarisində isə 1,15 olur; bu, dövlət sektoru tənliyindəki minimum əmək haqqı ilə
müəyyən edilir.

**Həssaslıq** (Əsas ssenari, nominal, illik %; orta / dövlət / özəl):

| Variant | orta | dövlət | özəl |
|---|---|---|---|
| **Əsas variant** (birgə WLS, E1 çarpaz yoxlama, sabit baza düzəliş əmsalları) | 7.13 | 8.51 | 6.03 |
| yalnız E1-ə uyğun dəqiq uzlaşdırma | 6.31 | 6.91 | 5.84 |
| çəkili məhdudiyyət kimi E1 | 6.89 | 8.04 | 5.98 |
| qalığın ρ̂ əmsalı ilə sönən baza düzəliş əmsalları (müqavilə qərarı 4) | 6.83 | 6.08 | 7.39 |
| məhdudiyyətsiz E3 (ln İQİ elastikliyi 0.588) | 7.16 | 8.46 | 6.13 |
| minimum əmək haqqı daxil edilmiş E3 (−0.247; rıçaq uyğunluğu qaydasını ödəmir) | 7.36 | 8.09 | 6.79 |
| məhdudiyyətsiz E4 (ln İQİ sərbəst) | 7.05 | 8.30 | 6.05 |
| 2018-ci il fiktiv dəyişənli E4 (minimum əmək haqqı elastikliyi 0.843; proqnoz dəqiqliyi qiymətləndirilməyib) | 7.16 | 8.57 | 6.03 |

**FR1-in öz əmək haqqı proqnozu ilə müqayisə.** FR3-ün orta əmək haqqı FR1-in `wage` sütunundan 2026-cı ildə +3,6%, 2030-cu
ildə isə +3,4% fərqlənir (Əsas ssenari); ssenarilər üzrə fərq +1,6%-dən +5,4%-dək təşkil edir. Dərc olunan əmək haqqı proqnozu
FR3-dür.

**Dekompozisiya.** Tarixən (2021–2025) artımın demək olar ki, hamısı **within** (qrupdaxili) həddin payına düşür; **between**
(qruplararası) hədd kiçik və müsbətdir (ildə +0,10-dan +0,30 faiz bəndinədək), çünki məşğulluq daha yüksək ödənişli qeyri-dövlət
sektoruna doğru yerdəyişib. Proqnozda paylar sabit saxlanılır, ona görə də between həddi konstruksiyaya görə sıfırdır.

### 7.1 Proqnoz qeyri-müəyyənliyi

1 000 təkrarlama **tarixi qalıq trayektoriyalarının yenidən seçilməsini** (resampling) — başlanğıc il *s* seçilir və dörd
tənliyin uzunmüddətli qalıqlarının və mükafat loqarifminin birgə kənarlaşmaları $u_{s+h}-u_s$ ($h$ = 1…4) 2027–2030 üçün əlavə
edilir; bu, heç bir qalıq prosesi qiymətləndirilmədən empirik davamlılığı və tənliklərarası korrelyasiyanı ötürür (AR komponenti
yoxdur) — N(β̂, V̂_HAC) paylanmasından əmsal çəkilişləri, cari qiymətləndirmə xətasının birgə çəkilişi və FR1-in Əsas ssenari
üzrə makro çəkilişləri ilə birləşdirir (500 çəkilişdən 500-ü istifadə olunub; yalnız sonlu olmayan dəyərlərə görə süzgəcdən
keçirilib, 0 çəkiliş çıxarılıb). Artım zolaqları hər təkrarlama üzrə artım sürətlərinin kvantilləridir.

| Əsas ssenari, 2030 | 5% | 25% | median | 75% | 95% | mərkəzi proqnoz |
|---|---|---|---|---|---|---|
| Orta əmək haqqı, AZN | 1 104 | 1 335 | 1 586 | 1 872 | 2 313 | 1 556 |
| 2030-cu ildə orta əmək haqqının artımı, % | −4.0 | 3.1 | 8.2 | 14.2 | 23.8 | 7.3 |
| Dövlət sektoru əmək haqqı, AZN | 1 122 | 1 373 | 1 630 | 1 933 | 2 424 | 1 626 |
| Özəl sektor əmək haqqı, AZN | 1 017 | 1 286 | 1 534 | 1 858 | 2 315 | 1 507 |
| Neft sektoru əmək haqqı, AZN | 3 021 | 4 007 | 4 988 | 6 364 | 9 341 | 5 083 |

**Məntiqi yoxlama (sanity check).** Yalnız FR3-ün öz qeyri-müəyyənlik mənbələri nəzərə alındıqda (makro amillər Əsas ssenari
səviyyəsində) orta əmək haqqı üzrə 90%-lik səviyyə zolağının yarım eni 2026-cı ildə 3,5%, 2027–2030-cu illərdə isə 10–17% təşkil
edir, nümunədən kənar yoxlamanın RMSE-si isə 14,5%-dir; dövlət sektoru əmək haqqı üzrə 11,8%-ə qarşı 14–22%; özəl sektor əmək
haqqı üzrə 18,8%-ə qarşı 9–14%. Səviyyə zolaqları nümunədən kənar yoxlamada faktiki alınmış xətalarla eyni tərtibdədir. Birillik
artım zolaqları tarixi artım diapazonundan genişdir (2005-ci ildən bəri orta əmək haqqının ən aşağı illik artımı +3,0% olub),
çünki tarixi qalıq kənarlaşmaları illər arasında böyük dalğalanmaları əhatə edir; mümkün başlanğıc illərin sayı 17 olduğundan
zolaqlar qeyri-hamardır. Hər iki variant `FR3_fan_wages.csv` faylında verilir (`sources` sütunu).

---

## 8. Məlumatların təmin edə bilmədikləri

### 8.1 İqtisadi sahələr üzrə orta əmək haqları — əldə etmək mümkün deyil

<!-- AUTO:v22_s81 -->
> **v2.2: köhnəlib.** DSK 4.5–4.8 onları dərc edir (2005–2024); FR3 indi səkkiz sektorun hamısını proqnozlaşdırır (v2.2 qeydinə bax).
<!-- /AUTO:v22_s81 -->

**1-ci cəhd** — əmək haqlarının alt sahələrarası (between) elastiklik (0,305) ilə muzdlu işçi başına əlavə dəyərə görə
bölüşdürülməsi, ölkə üzrə əmək haqqına lövbərləməklə. Rədd edilib: hesablanmış **sənaye** əmək haqqı faktiki göstəricidən
**25–42% yüksəkdir** (işçi başına sənaye əlavə dəyəri — 216 min manat — əsasən neft və qaz rentasıdır), **kənd təsərrüfatı isə
orta göstəricidən 1,40–1,46 dəfə yüksək əmək haqqı ilə ən yüksək ödənişli sahəyə çevrilir** (~1 000 min kənd təsərrüfatı
işçisindən yalnız təxminən 50 mini muzdlu işçidir).

**2-ci cəhd** — rentanı çıxarmaq və sənayeyə uyğun gələn elastikliyi axtarmaq: bir hədəf üçün bu, həmişə mümkündür, lakin kənd
təsərrüfatı yenə də orta göstəricidən xeyli yüksək alınır. Bu, identifikasiya deyil, əyrinin məlumatlara uyğunlaşdırılmasıdır
(curve-fitting).

**Bunun əvəzinə təqdim olunur:** 2 rəqəmli səviyyədə sənaye əmək haqları (v2: əmək haqqı dərc olunan bütün 29 alt sahə proqnozlaşdırılır, hər alt sahənin öz 2025-ci il qalığı ilə lövbərlənir — düzəliş əmsalı qaydası — və 29 alt sahənin hamısı üzrə cəmləmə dəqiqdir; lövbərlənməmiş alt sahələrarası trayektoriya işarələnmiş həssaslıq variantıdır),
bütün səkkiz sahə üzrə muzdlu məşğulluğun strukturu və dekompozisiya aparatı. **Nə həll edərdi:** əmək haqqı fondunun və ya
muzdlu işçilərin əməyinin ödənişinin sahələr üzrə bölgüsü.

### 8.2 Büdcə və qeyri-büdcə təşkilatları üzrə orta əmək haqları — identifikasiya etmək mümkün deyil

<!-- AUTO:v22_s82 -->
> **v2.2: köhnəlib.** Dörd büdcə fəaliyyətində DSK 4.5–4.8 dövlət əmək haqları onları müəyyən edir (2024: 900,7 və 1 058,6 AZN); v2.2-də proqnozlaşdırılır.
<!-- /AUTO:v22_s82 -->

İşəgötürən haqqının dərəcəsini büdcə hesablarından bərpa etmək mümkündür (212100 ÷ 211xxx ≈ 0,218, yəni qanunla müəyyən edilmiş
22%), lakin fərz edilən dərəcələrin DVX-in büdcə təşkilatları üzrə sosial sığorta haqlarına tətbiqi 2025-ci il üçün yalnız
dərəcədən asılı olaraq 1 062–1 399 manat büdcə əmək haqqı verir və hər bir variant büdcə əmək haqqını qeyri-büdcə əmək haqqından
yuxarıda yerləşdirir ki, bu da dərc olunmuş dövlət < özəl sıralanmasına ziddir. Bölgü müşahidə olunan göstəricilər kimi təqdim
olunur — işçi sayı (588 min, muzdlu işçilərin 29%-i) və sosial sığorta haqları (cəminin 34%-i). Fiskal 211xxx əmək haqqı
maddələri (2025-ci ildə **4 017 mln manat**) bütün iqtisadiyyat üzrə büdcə əmək haqqı fondu ola bilməz: təkcə təhsil xərcləri
4 618 mln manatdır.

### 8.3 Mənbədə aşkar edilmiş məlumat xətası

DVX vərəqinin **127–129**-cu sətirləri 123–125-ci sətirlərlə (mikro vergi ödəyiciləri) bayt-bayt eynidir. Yalnız 130-cu sətir
(işçi sayı) həqiqidir.

---

## 9. Məhdudiyyətlər

1. <!-- AUTO:v22_limits -->(v2.2) Sektor və büdcə / qeyri-büdcə əmək haqları yalnız 2024-ədək dərc olunur və 2024 nisbi əmək haqları ilə proqnozlaşdırılır — heç bir sektora xas sürücü bu qaydanı üstələmir.
2. (v2.2) DSK çəkili ortası ilə dərc olunmuş orta 1,05%-ədək fərqlənir; nisbət 2024 səviyyəsində saxlanılır.<!-- /AUTO:v22_limits -->
3. DVX-in 127–129-cu sətirlərində mənbə məlumatı xətası (§8.3).
4. **Neft sektoru əmək haqqı** tənlik vasitəsilə proqnozlaşdırılmır: o, qeyri-neft sektoru əmək haqqının açıq bildirilmiş mükafat
   rıçağına hasilidir; nümunədən kənar yoxlamada təsadüfi gəzişmə bu mexanizmdən üstündür (U 3,80), sabit artım isə təxminən eyni
   nəticə verir (1,07).
5. **Nümunədən kənar yoxlama sabit artımla müqayisədə zəifdir**: proqnozun öz lövbərləmə qaydası ilə model beş sıranın heç
   birində sabit artımdan üstün deyil (orta əmək haqqı U 3,03, 2025-ci ilədək +12,7%). Lövbər ili çox mühüm rol oynayır (2018–20
   orta qalığı ilə lövbərləmədə: 5,3%).
6. Heç bir tənlik üçün **kointeqrasiya təsdiqlənmir** (EG və Gregory–Hansen); t-statistikaları təsviri xarakter daşıyır, baza
   düzəliş əmsalları isə sabit saxlanılır.
7. **Homogenlik nəzəri əsaslarla qoyulur**, baxmayaraq ki, qısa nümunədə özəl sektor əmək haqqı üçün rədd edilir; məhdudiyyətsiz
   forma özəl sektor əmək haqqının illik artımını 6,03% əvəzinə 6,13% verir.
8. **Minimum əmək haqqının təsiri qeyri-dəqiqdir**: dövlət sektoru üzrə 0,24–0,84 (proqnozda 0,386; proqnoz dəqiqliyi
   qiymətləndirilməmiş qırılma fiktiv dəyişəni ilə 0,843). Özəl sektor əmək haqqında onun qiymətləri mənfidir (−0,25-dən
   −0,01-dək), lakin rıçaq uyğunluğu qaydasını ödəmir, ona görə də orada çıxarılır; özəl sektora hər hansı həqiqi təsir nəzərə
   alınmır.
9. **Əmək bazarının gərginliyi kanalı yoxdur.**
10. **2021-ci ilədək muzdlu məşğulluq hesablanır** (2024–25-ci illərdə nümunədən kənar xəta 4,6%-dək).
11. **Qısa nümunələr:** hər proqnoz tənliyi üzrə 20–25 müşahidə (qalıq sərbəstlik dərəcələri 11–20), seçimdə hər namizəd üzrə 15
    üst-üstə düşən xəta, nümunədən kənar yoxlamanın 5 ili, DVX məşğulluğunun 5 ili.
12. 2026-cı ildən sonra **məşğulluq strukturu sabit saxlanılır** (dövlət və neft sektoru payları, alt sahə strukturu, muzdlu
    işçilərin payı).
13. FR1 çəkilişləri vasitəsilə **FR3 FR1-in makro qeyri-müəyyənliyini miras alır** (§7.1).
14. **İki mənbə sistemi** orta əmək haqqı üzrə **−4%-dən +2%-dək fərqlənir** (DSK və DVX); FR3 DSK sırasını proqnozlaşdırır.

## 10. FR3-ü ən çox nə təkmilləşdirərdi

1. **Sahələr üzrə əmək haqqı fondları və ya muzdlu işçilərin əməyinin ödənişi** — ən böyük boşluq, FR3-ün tələb etdiyi ilk bölgü.
2. **Seqmentlər üzrə qanuni sosial sığorta haqları dərəcələrinin cədvəli** və ya büdcə təşkilatlarının əmək haqqı fondu.
3. **2005-ci ilədək geriyə doğru sahələr və institusional sektorlar üzrə muzdlu məşğulluq.**
4. **2021-ci ildən əvvəlki aylıq əmək haqqı məlumatları** — cari qiymətləndirmənin mövsümi amilini və onun xəta zolağını xeyli
   etibarlı edərdi.
5. **Dərc olunmuş median əmək haqqı və ya əmək haqqı paylanması** — minimum əmək haqqının sıxlaşdırıcı təsirlərini identifikasiya
   etmək üçün.
