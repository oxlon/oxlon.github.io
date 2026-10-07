> **İngilis dilində (English version):** [FR1_Methodology.md](../FR1_Methodology.md). Rəqəmlərin yazılışı: mətndə onluq kəsr vergüllə, minliklər boşluqla ayrılır; cədvəllərdə, düsturlarda, kodda və fayl adlarında onluq kəsr proqram çıxışında olduğu kimi nöqtə ilə verilir.

# FR1 — Sektor və bazar təhlili, habelə beşillik proqnozlaşdırma üçün struktur ekonometrik metodologiya

**Modul:** 15.5.2 Mikroiqtisadi təhlil və proqnozlaşdırma
**Tələb:** FR1 — *iqtisadi sektorların və bazarların dərin təhlili; sektorlara xas dinamikanın və trendlərin proqnozlaşdırılması*
**Model:** AZSEM-FR1 (Azərbaycanın Struktur Ekonometrik Modeli, 1-ci proqnoz raundu)
**Məlumat mənbəyi:** `Statistik data dinamika 05.06.2026 +.xlsx` (41 vərəq, İqtisadiyyat Nazirliyinin statistik dinamika məlumat bazası)
**Məlumat buraxılışı (vintage):** 2025-ci ilədək illik faktiki məlumatlar; 2026-cı ilin aprel ayınadək kumulyativ aylıq faktiki məlumatlar
**Proqnoz üfüqü:** 2026–2030
**İcra:** `FR1.ipynb` (əvvəldən sona xətasız icra olunur; <!-- AUTO:v23_cells -->Hissə 1–17 = 70 kod xanası<!-- /AUTO:v23_cells -->, Hissə 18 (v2) = reyestr, mühərrik üçün ixrac, kataloq və öz-özünə test; nüvə (kernel) `miis-model`) və ssenari mühərriki `microlib/engines/fr1.py`
**Nəticələr:** `MicroUnit/output/` qovluğunda `FR1_*.csv` CSV faylları, o cümlədən `FR1_forecast_full.csv` (indi `pop` sütunu ilə,
min nəfər) və `FR1_fan_draws.csv` (FR3–FR5 üçün Əsas ssenari üzrə 500 təkrarlama)

---

## Yenidənbaxma qeydi (2026-09-27)

Metodoloji yoxlama zamanı proqram xətaları, qiymətləndirici səhvləri və şişirdilmiş iddialar aşkar edilmişdir. Onların hamısı düzəldilmiş və notebook yenidən icra olunmuşdur; aşağıdakı bütün
rəqəmlər yenidən icra olunmuş nəticələrdən götürülmüşdür.

| Sahə | Nə dəyişdi | Səbəb |
|---|---|---|
| Uzunmüddətli qiymətləndirici | Hər bir səviyyə əlaqəsi indi **DOLS** ilə qiymətləndirilir (df ≥ 10 olduqda Δx-in ±1 qabaqlayıcı/gecikməsi, əks halda Δx-in cari qiyməti, əks halda OLS); həlledicinin istifadə etdiyi əmsallar məhz uzunmüddətli əmsallardır | DOLS müəyyən edilmişdi, lakin heç vaxt istifadə olunmamışdı |
| Kointeqrasiya testi | Dickey–Fuller cədvəlləri ilə ADF p-dəyərləri deyil, MacKinnon cavab səthindən (response surface) alınan, qalıqlara əsaslanan Engle–Granger p-dəyərləri (`eg_coint_p`); inflyasiya/deflyator tənliklərinə tətbiq edilmir | Köhnə p-dəyərləri kointeqrasiyanı şişirdirdi (əvvəl 47-dən 26-sı "p<0.05"; indi səviyyə əlaqələrinin **30-dan 2-si**) |
| Statistik nəticə | n/(n−k) miqyaslaşdırması ilə HAC, t(n−k) p-dəyərləri, yoxlanılan kombinasiyanın s.x.-si ilə HAC-F şəklində məhdudiyyət testləri; rədd edilməmə halları "aşağı güc" kimi işarələnir; hər səviyyə əmsalı birinci fərqlərdə qiymətləndirilmiş eyni tənliklə müqayisə edilir | Kiçik nümunələr |
| Məhdudiyyətlər | DOLS altında yenidən test edilib: **vahid ticarət elastikliyi, mədənçıxarmada CRS və emal sənayesində α_K = amil payı rədd edilir** və artıq qoyulmur; vahid qeyri-neft vergi elastikliyi (buoyancy) və dövlət investisiyasının vahid elastikliyi saxlanılır (rədd edilməyib, aşağı güc). B1 vahid ötürülmə əmsalı rədd edilir (p = 0.017) | Əvvəllər qoyulmuşdu və ya qoyulmadan "qoyulmuş" kimi işarələnmişdi (C3) |
| Səhv işarələr | Ev təsərrüfatlarının gəliri (E3) sosial xərclər (n = 7, səhv işarə) əvəzinə yenidən spesifikasiya edilib (yekun: qeyri-neft ÜDM + pensiya xərcləri, homogenlik qoyulub); qeyri-neft ÜDM kredit tənliyindən (G1, səhv işarə) çıxarılıb; qalan səhv işarəli, statistik əhəmiyyətsiz hədlər qaydaya əsasən çıxarılıb | |
| Kredit kanalı | Kredit həddi investisiya tənliyindən çıxarılıb: sərbəst qiymətləndirmənin işarəsi səhvdir, 0.134 panel dəyəri rədd edilir (HAC-F p = 0.028); multiplikatorlarda ekspert rəyinə əsaslanan əlavə (judgemental overlay) təklif olunur | Əvvəllər qiymətləndirmədən sonra sonradan əlavə edilirdi |
| Eyni zamanlılıq | Alətlər trenddən və dövlət investisiyasından (F4 vasitəsilə endogen) təmizlənib; hər tənlik üçün DWH testi; 2SLS yalnız DWH rədd etdikdə, bütün birinci mərhələ F ≥ 10 olduqda və Sargan rədd etmədikdə istifadə olunur — **heç bir tənlik bu şərtlərə cavab vermir** | |
| Panellər | ⌊T^¼⌋ gecikmə və t(T−1) ilə Driscoll–Kraay; wild cluster bootstrap (illər, Webb çəkiləri); əməyin payı 22%-lik işəgötürən ayırmaları nəzərə alınmaqla artırılmış qeyri-karbohidrogen sahələri üzrə yenidən hesablanıb (α_K 0.66 → 0.56); regional ticarət üzrə "çarpaz yoxlama" geri götürülüb (doldurma (interpolyasiya) artefaktı) | |
| Proqram xətaları | Artım dekompozisiyasında trend töhfələrinin ×100 xətası; neft sektoru investisiyasının mürəkkəb artımla hesablanması; İslahat ssenarisinin TFP artımı indi həqiqətən tətbiq olunur; struktur cədvəldə NaN düzəldilib; əhali artımı 0.4% sabit kodlanmış dəyər əvəzinə hesablanır (illik 0.483%, 2021–25) | |
| 2026 lövbəri | Yanvar–aprel artımı 1:1 köçürülür (dayanıqlı (robust) körpü 1:1-dən üstün deyil, HLN-DM p = 0.13); lövbər artımları bir illik yarımsönmə dövrü ilə sönür | Əvvəllər 2030-cu ilədək saxlanılırdı |
| Nümunədən kənar yoxlama (hold-out) | Hər əmsal, məhdudiyyət qərarı, qiymətləndiricinin dəyişdirilməsi və kalibrlənmiş nisbət ≤2020 məlumatları əsasında yenidən müəyyən edilib; dövlət investisiyası endogendir (F4); müqayisə meyarları: 2019 və 2020-ci illərdən təsadüfi gəzişmə (RW), 2010–19 və 2010–20 üzrə sabit artım; HLN-DM testləri | Əvvəllər məlumat sızması və həddən artıq əlverişli müqayisə meyarı var idi |
| Qeyri-müəyyənlik | Bütün 29 qalıq üzrə tarixi qalıq yollarının təkrar seçimi (resampling) (qalıq dinamikası qiymətləndirilmir), Brent/neft/qaz yolları birgə, antitetik, işarəni qoruyan parametr çəkilişləri, sıçrayışların süzgəcdən keçirilməsi, Əsas ssenari ətrafında mərkəzləşdirmə; artım yelpikləri hər çəkilişin artımından; çəkilişlər ixrac olunur | Əvvəllər 16 tənlik, iid, parametr/ekzogen qeyri-müəyyənlik yox idi |


**İkinci yoxlama mərhələsi (2026-09-28).** Müstəqil təkrar yoxlama qiymətləndirici, panel, nümunədən kənar yoxlama və proqram xətaları üzrə düzəlişləri təsdiqləmiş və
əlavə qərarlar tələb etmişdir; onların hamısı tətbiq olunub: yanvar–aprel körpüsü (meyl əmsalı 0,52) 2021-ci ilin baza effektinin artefaktı idi — 2022–25 üzrə
dayanıqlı üsulla yenidən qiymətləndirildikdə 1:1-dən üstün deyil (HLN-DM p = 0,13), buna görə də **1:1 köçürmə** istifadə olunur; **kredit həddi** investisiya tənliyindən
**çıxarılıb** (0,134 panel dəyəri aqreqat məlumatlarla rədd edilir, HAC-F p = 0,028) və kredit şərtlərinin yumşaldılmasının investisiyaya təsiri yalnız
işarələnmiş ekspert əlavəsi kimi qalır; **ev təsərrüfatlarının gəliri** qeyri-neft ÜDM + pensiya xərcləri üzrə yenidən spesifikasiya edilib, homogenlik test edilib və
qoyulub (əmək haqqı fondu əsasında versiya homogenlik testindən keçmədi və istehlakı 23%-ə qədər aşağı proqnozlaşdırırdı); **ex-post real faiz dərəcəsi**
istehlak tənliyindən çıxarılıb (o, inflyasiya sürprizlərini istehlak bumlarına çevirirdi); **nəqliyyat** tənliyində karbohidrogen tranziti saxlanılır (kəsimdən əvvəlki
məlumatlarda statistik əhəmiyyətlidir, t = 5,2); **sosial xidmətlər deflyatoru** üçün İQİ-dən vahid ötürülmə əmsalı qoyulub (dreyf saxlanılır; dreyfin olmaması üzrə birgə hipotez
rədd edilir); səhv işarəli, statistik əhəmiyyətsiz uzunmüddətli hədlər nümunədən kənar yoxlamada yenidən tətbiq olunan qayda ilə çıxarılıb; ssenari üzrə TFP artımı
təklif tərəfi sektorları ilə məhdudlaşdırılıb; nümunədən kənar yoxlamanın DM testlərində h = 3 istifadə olunur; deflyator dəyişikliklərinin tətbiqindəki vahidlər xətası (loqarifmik
dəyişikliklər sadə faiz kimi tətbiq olunurdu) düzəldilib; yelpik qrafikləri isə indi **tarixi qalıq yollarını təkrar tətbiq edir** (qalıq dinamikası qiymətləndirilmir) —
birgə ekzogen yollar, antitetik, işarəni qoruyan parametr çəkilişləri, sıçrayışların süzgəcdən keçirilməsi və Əsas ssenari ətrafında
mərkəzləşdirmə ilə. Bu dəyişikliklər nöqtəvi proqnozları dəyişdirir (Bölmə 7.4).

---

<!-- v2-begin -->
## v2 (2026-10-05): tənliklər reyestri, ssenari mühərriki, dayanıqlıq

Bu mərhələdə modelin heç bir tənliyi, əmsalı və ya proqnozu dəyişdirilməyib: mövcud `FR1_*.csv` faylları əvvəlki ilə eynidir
(dəyişməzlik (no-regression) yoxlaması: maks. nisbi fərq 2·10⁻¹³, nüvə (kernel) `miis-model`, Python 3.13), iki düzəldilmiş diaqnostika faylı istisna olmaqla (aşağıya bax). `FR1.ipynb`-yə Hissə 18 əlavə olunub.

**Tənliklər reyestri** — `output/FR1_equations.json`, 146 tənlik: 47 proqnoz tənliyi (46 davranış/dərəcə tənliyi və istehsal
boşluğu üçün təsviri trend; G6 ÜDM deflyatoru qiymətləndirilir, lakin həlledicidə istifadə olunmur), 42 rədd edilmiş / namizəd /
həssaslıq spesifikasiyası, 20 2SLS (DWH qaydası) və 7 alət uyğunluğu reqressiyası, 5 3SLS, 9 SUR pay tənliyi, 14 panel
(Driscoll–Kraay, t(T−1), wild cluster bootstrap p-dəyərləri `extra`-da) və cari qiymətləndirmə (nowcast) körpüsü. Hər OLS/DOLS/2SLS/panel tənliyi
statsmodels ilə müstəqil yenidən qiymətləndirilib, əmsalların notebook-unkularla eyni olduğu assert ilə yoxlanılır; məhdudiyyətlə bağlı
formalarda reyestr əmsalları `to_cf` vasitəsilə həlledici əmsallarına (CF) dəqiq çevrilir. Məhdudiyyət testləri yenidən
hesablanıb və notebook mətni ilə yoxlanılıb. ≤2020 məlumatla yenidən qiymətləndirmə və 2021–2025 dinamik nümunədən kənar
yoxlama (RMSE, Theil U təsadüfi gəzişmə və sabit artıma qarşı, HLN-DM p) hər proqnoz tənliyinin `holdout` blokundadır
(46 tənlik üzrə median U: təsadüfi gəzişməyə qarşı 0,74, sabit artıma qarşı 1,20). Yalnız bir müqayisə spesifikasiyası
(sosial xərclərlə E3, ≤2020, n = 2 < k) qeydə alınmayıb — dəqiq uyğunlaşmadır.

**Dayanıqlıq** (`output/FR1_robustness_summary.csv`; qayda reyestr başlığında): 47 proqnoz tənliyindən 15 stabil,
12 qismən stabil, 20 qeyri-stabil. Qeyri-stabil olanlar əsasən 2013/2015/2020 Chow qırılmaları (devalvasiya, pandemiya) və bəzi
rekursiv işarə dəyişmələri ilə: B2, B3, C3, C4, C5, C7, C8, C9, C10, C12, D1, D3, D4, E1, E3, G1, G2, G3, G5 (k/t deflyatoru) və
təsviri trend. Bu, modelin 2021–2025 nümunədən kənar yoxlamada sabit artımı üstələməməsi ilə uyğundur (§6.2).

**Ssenari mühərriki** — `microlib/engines/fr1.py` (+ `_fr1_*.py`), vəziyyət `output/engine/FR1_state.json`. Hissə 11–16-nın həlli
sətir-sətir köçürülüb: sönümlü Gauss–Seidel, eyniliklər, zəncirvari aqreqasiya, baza düzəliş əmsalları (2025 qalıqları) və 2026
ankor artımlarının 0,5 əmsalı ilə sönməsi, dövlət investisiyasının siyasət səviyyəsi + neft gəlirləri sapmasına F4 reaksiyası,
TFP əlavəsi, əhali yolu, hesablar (real, deflyator, nominal), töhfələr və dekompozisiya. Redaktə edilə bilən: 16 baza fərziyyəsi
yolu (2026–2030, hər ssenari), 122 həlledici əmsalı (dəyər, s.x., 95% etibarlılıq intervalı reyestrdən), 10 rıçaq (rejim
`shock`/`reanchor`, ankor və sönmə, ρ ilə sönmə, düzəliş əmsalının yenidən kalibrlənməsi, dövlət investisiyası qaydası, kredit
əlavəsi, homogenlik; v2.1-dən 11-ci: sektor bölgüsü payları `alloc_shares`). Standart `shock` rejimi notebook-un Hissə 14 konvensiyasıdır; mühərrik Hissə 14-ün beş multiplikator
təcrübəsini 10⁻¹⁴ dəqiqliklə təkrarlayır. Son xana `selftest()`-i assert ilə yoxlayır: hər üç ssenari üzrə hər iki rejimdə
`FR1_forecast_full.csv`, `FR1_accounts_*` və bütün ssenarilər üzrə töhfə/dekompozisiya cədvəlləri maks. nisbi fərq ~10⁻¹⁴ ilə
təkrarlanır; bir ssenari ~0,06 s.

**Tamlıq** — `FR1_indicator_catalog.csv` və `FR1_forecast_tidy.csv`: 471 komponent × 3 ssenari × 2026–2030 (tam), tarix
1990-dan, 43 komponent üçün Əsas ssenari 5–95% zolağı. Töhfələr və dekompozisiya artıq bütün ssenarilər üçündür
(`FR1_gdp_growth_contributions_all.csv`, `FR1_sector_decomposition_all.csv`). Yeni bölgülər: sektorlar üzrə kreditlər
(`FR1_credit_by_sector.csv`; ev təsərrüfatları G2, qalan kreditlər 2023–25 orta payları ilə; v2.1-dən 2025-ci ilin faktiki payları ilə — aşağıya bax) və sektorlar üzrə real investisiya
(`FR1_investment_by_sector.csv`; kapital eyniliyinin istifadə etdiyi axın; v2.1-dən 2025-ci ilin payları ilə). Proqnozlaşdırılmayanlar səbəbi ilə
`FR1_not_forecast.csv`-dədir. İngilis mətnləri: `FR1_strings_az.csv` (240 sətir).

<!-- AUTO:fr1v236_coefsens -->
**Əmsal həssaslığı** (`FR1_coef_sensitivity.csv`, ±1 s.x., 2030, Əsas ssenari; cari icra): ən güclü təsirlər E3 ev təsərrüfatlarının gəliri tənliyinin əmsallarındandır — qeyri-neft ÜDM (ev təsərrüfatlarının gəliri −7,61/+22,52%, qeyri-neft ÜDM −3,66/+10,94%, İQİ −1,19/+3,35%) və real əmək haqqı fondu (ev təsərrüfatlarının gəliri −2,10/+1,82%); sonra D1 gəlir elastikliyi (qeyri-neft ÜDM −1,74/+2,56%); İQİ üçün G4 əmək haqqı ötürülməsi (+2,35/−2,50%); məşğulluq üçün E4 iştirak trendi (−0,63/+0,64%). E3 təsirləri asimmetrikdir: ±1 s.x. dəyişikliyi eksponent daxilindəki loqarifmik səviyyəyə vurulur və gəlir–istehlak dövrəsi ilə güclənir.
<!-- /AUTO:fr1v236_coefsens -->

**v2-də düzəldilmiş iki xəta (yalnız diaqnostika / həssaslıq çıxışları dəyişir).** (1) `FR1_iv_dwh.csv`: E2 və G1-də daxil
edilmiş ekzogen dəyişən (`ln_minwage`, `polrate`) həm də xaric edilmiş alət kimi sayılırdı (təkrarlanan sütun). İndi daxil edilmiş
ekzogen dəyişənlər yalnız özləri üçün alətdir. Endogen 2SLS əmsalları dəyişmir; düzələn göstəricilər: E2 birinci mərhələ F
(ln_cpi 5,5 → 9,8; ln_prod_non 43,3 → 76,9), Sargan p 0,044 → 0,011, DWH p 0,683 → 0,663; G1 F 37,7 → 67,1, Sargan p 0,043 → 0,013,
DWH p 0,123 → 0,111. Heç bir DWH/2SLS qərarı dəyişmir — nə tam nümunədə, nə də ≤2020 nümunədən kənar yoxlama modelində (orada D2 və
G2 əvvəlki kimi 2SLS ilə). (2) Hissə 13-ün ρ həssaslığı (`FR1_addfactor_sensitivity.csv`) əsas proqnozdan qalmış neft gəlirləri
istinad yolunu təkrar istifadə edirdi; indi öz istinad yolu ilə hesablanır (yeni dəyərlər §7.4-də). (3) Dəyişdirilməyib: 2026
ankor dövrü 20 iterasiya ilə məhdudlaşır və hədəflərə ən çoxu 0,12% (turizm; Mənfi ssenaridə 0,07%, İslahatda 0,16%) fərqlə
çatır — 0,5% dözümlülük həddinin daxilindədir; mühərrikdə `anchor_maxit` rıçağı ilə artırıla bilər.
<!-- v2-end -->

<!-- v2.1-begin -->
## v2.1 (2026-10-05): sektor bölgüləri son faktiki ilə ankorlanır

**Xəta.** Audit göstərdi ki, sektorlar üzrə 2026-cı il real investisiyası (`FR1_investment_by_sector.csv`, `fr1:inv:*`) 2025-ci ilin
faktiki səviyyəsinə nisbətən sıçrayırdı — ticarət +58%, emal sənayesi +49%, turizm −25%, elektrik enerjisi −23%, su təchizatı −22%,
İKT +22% — halbuki ümumi real investisiya demək olar ki, dəyişmir (−0,1%). Səbəb: ümumi real investisiyada 2023–25 *orta* payları
2026-cı ildən etibarən 2025-ci il tərkibi ortalamadan fərqlənən cəmə tətbiq olunurdu. Sektorlar üzrə kreditlərdə
(`FR1_credit_by_sector.csv`) eyni problem var idi: biznes krediti 3,7% artdığı halda enerji krediti +25,2% (İslahatda +28,2%).

**Qayda.** Layihənin ümumi konvensiyasına uyğun olaraq (FR3 sahə əmək haqları, FR12 bölmə bölgüsü, düzəliş əmsalları) bölgü son
faktiki ilə ankorlanır: hər sektorun **2025-ci ildəki payı 2030-a qədər saxlanılır** — ümumi real investisiyada (Hissə 11.2,
`calibrate`) və biznes (ev təsərrüfatlarından başqa) kreditlərində (Hissə 9.7, `CRED_SHARE_ANCH`; "digər" dəqiq qalıq olaraq qalır).
Beləliklə, 2026-cı ildə sektor dəyərləri cəmlə eyni sürətlə dəyişir: investisiya hər sektorda −0,1% (Mənfi −3,8%, İslahat +2,2%),
kredit +3,7% (Mənfi −6,0%, İslahat +6,3%). Orta paylara yaxınlaşma tətbiq olunmur: notebook-da ortalama hamarlaşdırma üçündür,
uzunmüddətli pay əsaslandırması deyil, aşağıdakı nümunədən kənar yoxlama da birini aydın dəstəkləmir. Sektorların tarixi sıraları
(investisiya 2000–2025, kredit 2006–2025, `is_forecast = False`) `FR1_forecast_tidy.csv`-də artıq var idi; indi 2026 ilə fasiləsizdir.

**Modelə təsiri.** İnvestisiya payları kapital fondu eyniliyinin axınlarıdır,
K<sub>s,t</sub> = (1−δ<sub>s</sub>)K<sub>s,t−1</sub> + pay<sub>s</sub>·I<sub>t</sub>, buna görə də orada da eyni ankorlanmış paylar
istifadə olunur (dərc edilən sektor investisiyası və əsas fondlar uzlaşmış qalır). Əhəmiyyətli olanlar K<sub>man</sub> (C3) və
K<sub>ict</sub> (C10): 2025-ci il payları ilə (emal 3,0%, orta 4,5%; İKT 1,8%, orta 2,1%) hər iki fond 2030-da ~9,6% aşağıdır və Əsas
ssenaridə 2030-cu il əlavə dəyəri azalır — emal −3,2%, İKT −7,6%, qeyri-neft ÜDM −0,93%, real ÜDM −0,78% (2026 dəyişmir: yanvar–aprel
məlumatlarına ankorlanıb). 2026–30 orta artımı (v2 → v2.1, hər ikisi 2026-10-05; cari icra §7-dədir): real ÜDM 2,56 → **2,40%** (Mənfi 1,51 → 1,37, İslahat 3,50 → 3,32); qeyri-neft
4,18 → **3,99%** (3,07 → 2,90, 5,26 → 5,03). §6–§9-dakı və yuxarıdakı v2 qeydindəki icradan asılı bütün rəqəmlər
v2.1 icrasına aiddir (çıxış CSV fayllarından və icra olunmuş notebook-dan skriptlə yenilənib). `FR1_forecast_full.csv` və `FR1_fan_draws.csv`-ni oxuyan
FR3, FR4 və FR5 yenidən icra edilib; FR10 və FR12 də həmin faylları oxuyur.

**Nümunədən kənar yoxlama (2020 kəsimində eyni qayda).** 14 dəyişən üzrə median Theil U:

| Kapital eyniliyində pay qaydası | median U RW2020 | median U CG 2010–19 | real ÜDM U RW2020 | emal U | İKT U |
|---|---|---|---|---|---|
| 3 illik orta (v2.1-dən əvvəl) | 0.578 | 1.024 | 0.595 | 0.677 | 0.282 |
| **kəsim ilinin payı saxlanılır (v2.1)** | 0.585 | 1.019 | 0.624 | 0.577 | 0.820 |
| 4 il ərzində ortalamaya xətti yaxınlaşma | 0.594 | 1.026 | 0.613 | 0.611 | 0.596 |
| 0,5 ankor sönmə əmsalı ilə yaxınlaşma | 0.580 | 1.026 | 0.609 | 0.625 | 0.516 |

Qaydalar İKT istisna olmaqla yaxındır; İKT-nin 2020-ci il investisiya payı dib nöqtəsi idi (1,1%, orta 2,2%). İki yaxınlaşma qaydası
qəbul edilməyib: biri medianlarda daha yaxşı deyil, digəri sıçrayışı sadəcə 2027-yə keçirir (ticarət +30%).

**Rıçaq və mühərrik.** 3 illik orta paylar saxlanılır (`CAL['inv_share_avg3']`, `CRED_SHARE_FIX`) və çap olunur; mühərrikdə
`alloc_shares='avg3'` rıçağı v2.1-dən əvvəlki qaydanı bərpa edir (`mode='reanchor'` ilə v2.1-dən əvvəlki proqnozu 8·10⁻¹⁶ dəqiqliklə
təkrarlayır). `selftest()` indi `FR1_investment_by_sector.csv` və `FR1_credit_by_sector.csv`-ni də təkrarlayır (maks. nisbi fərq 2·10⁻¹⁶).

**Yoxlanılmış digər bölgü çıxışları.** `FR1_gdp_growth_contributions_all.csv` və `FR1_sector_decomposition_all.csv` pay bölgüsü deyil,
artım templəridir (faiz bəndi): töhfələr 2025-ci ilin faktiki nominal çəkilərindən istifadə edir; 2026-cı il dəyərləri sektor
tənliklərindən və 2026 yanvar–aprel ankorundan gəlir (tikinti real −19% → −1,24 faiz bəndi), buna görə dəyişdirilməyib. İstehlak
bazarlarının paylarında 25%-dən böyük sıçrayış yoxdur. 2025→2026 səviyyə sıçrayışı 25%-dən böyük olan yeganə digər göstərici büdcə
balansıdır (iki böyük aqreqatın fərqi). FR1-in 14 Driscoll–Kraay panelində p-dəyərləri və intervallar artıq t(T−1) ilədir (yoxlanılıb).
<!-- v2.1-end -->

<!-- AUTO:v23_note -->
## v2.3 (2026-10-05): FR1-in yekun təmizlənməsi — sabit düzəliş əmsalı sönməsi, idxalda qiymət həddi, gəlirdə əmək haqqı fondu, fiskal sıra

Dörd spesifikasiya məsələsi: hər namizəd modelin öz builder-ləri ilə ≤2020 məlumatla qiymətləndirilib və toxunulmamış dinamik 2021–2025
nümunədən kənar yoxlamada v2.2 spesifikasiyası ilə müqayisə edilib (notebook-da yeni Hissə 11.7, `FR1_v23_candidates.csv`); ssenari nəticələri
və qərarlar Hissə 14.1-dədir (`FR1_v23_forecast_checks.csv`, `FR1_v23_fiscal_diagnosis.csv`, `FR1_v23_decisions.csv`). Qayda: hər iki nümunədə
düzgün (və ya neytral) işarələr, əsas dəyişənin Theil U-su v2.2 spesifikasiyasından ən çoxu 10% yüksək, E3 üçün uyğun əmək haqqı elastikliyi,
fiskal namizədlər üçün isə 2030 büdcə balansının Mənfi < Əsas < İslahat sırası. Rədd edilmiş namizədlər `used_in_forecast = false` ilə reyestrdədir.

| Məsələ | Qərar | Sübut |
|---|---|---|
| 1. Düzəliş əmsallarının sönməsi üzrə həssaslıq | **Dəyişdirilib.** v2.2-yə qədər `base_addf_decay` rıçağı baza düzəliş əmsallarını hər tənliyin *qiymətləndirilmiş* qalıq avtokorrelyasiyası ρ̂ ilə söndürürdü — bu, qiymətləndirilmiş qalıq-AR prosesidir və sifarişçinin məhdudiyyətləri ilə istisna olunur. İndi sabit, qiymətləndirilməyən yarımparçalanma müddəti: `addf_halflife` rıçağı (standart 1 il, ildə 0,50 əmsalı — yanvar–aprel ankor əlavələrinin qaydası); ρ̂ proqnoz yolunun heç bir yerində qiymətləndirilmir (DW və BG diaqnostik test kimi qalır) | Proqnoz (sabit düzəliş əmsalları) bu bənddən dəyişmir. `FR1_addfactor_sensitivity.csv`, sönmə ilə 2026–30 orta artım: real ÜDM 2,31 / 1,12 / 3,33% (Əsas / Mənfi / İslahat; sabit düzəliş əmsalları ilə 2,57%), qeyri-neft 3,51 / 2,35 / 4,62% (3,76%); ρ̂ ilə (v2.2 icrası) real ÜDM 2,42%, qeyri-neft 3,67% |
| 2. D4 qeyri-neft idxalı: nisbi qiymət ln(p_gdp/fx), əmsal −0,245 | **Yenidən parametrləşdirilib (qəbul edilib).** Real idxal = ABŞ dolları ilə idxal × məzənnə / ÜDM deflyatoru (Hissə 3), buna görə ln(p_gdp/fx) asılı dəyişənə tərif üzrə −1 əmsalı ilə daxildir. İdxal həcmi (sabit ABŞ dolları qiymətləri) ilə ifadə edildikdə eyni qiymətləndirmə həcm elastikliyini verir: **c = +0,755** (p = 0,0001; ≤2020: +0,278) — işarə düzgündür: real möhkəmlənmə idxal həcmini artırır. Həlledici ÜDM qiymətləri ilə real idxal üçün c − 1 istifadə edir, buna görə proqnoz və nümunədən kənar yoxlama eynidir. Həddin çıxarılması (= əmsalın 0 həddində məhdudlaşdırılması; hədd məcburidir) rədd edilib | İdxal U 0,84 / 0,56 (v2.2 ilə eyni). Hədsiz: idxal 0,95 / 0,63 (+13%, əhəmiyyətli itki), qeyri-neft gəlirləri U 0,87 — 0,44-ə qarşı, büdcə balansı 0,99 — 0,61-ə qarşı. Birinci fərqlərdə həcm elastikliyi +0,08 [−0,26, +0,42]-dir, uzunmüddətli qiymət bu intervaldan kənardadır — v2.2 formasında olduğu kimi (göstərilir) |
| 3. E3 ev təsərrüfatlarının gəliri: + real əmək haqqı fondu | **Qəbul edilib.** ln(gəlir / pensiya xərcləri) ln(qeyri-neft ÜDM / pensiya xərcləri) və ln(əmək haqqı fondu / pensiya xərcləri) üzrə, homogenlik qoyulub: elastikliklər qeyri-neft ÜDM 0,603, **real əmək haqqı fondu 0,377** (2025-ci ildə əmək ödənişlərinin ev təsərrüfatlarının gəlirindəki payı 0,425), pensiya xərcləri 0,021; ≤2020: 0,690, 0,102, 0,208. Homogenlik seçim nümunəsində rədd edilmir (p = 0,16), tam nümunədə isə rədd edilir (p = 0,001); orada sərbəst formada qeyri-neft ÜDM elastikliyi səhv işarəlidir (−1,34) — buna görə "yoxla və qoy" variantı rədd edilib. Əmək haqqı elastikliyi uyğundur (birinci fərqlərdə 0,20 [−0,20, +0,59]) | Real sərəncamda qalan gəlir üzrə U 1,26 / 1,00 — 1,24 / 0,98-ə qarşı (+2,3%, 10%-dən az); istehlak U 0,08 — 0,14-ə qarşı. **Minimum əmək haqqı +10%** (Əsas ssenari 2030, şok konvensiyası): real sərəncamda qalan gəlir −0,31% → **+1,19%**, istehlak −0,35% → +1,31%, qeyri-neft ÜDM −0,21% → +0,51% (əmək haqqı +3,59%, İQİ +1,16%; gəlir ayaqları rıçağı ilə +1,03%) |
| 4. Fiskal blok: Mənfi ssenari ən yaxşı büdcə balansı ilə bitir | **Saxlanılıb — heç bir namizəd keçmir.** Diaqnostika, 2030, Mənfi — Əsas: gəlirlər −9,2 mlrd AZN (neft −3,9, qeyri-neft −5,3), xərclər −10,7 mlrd (cari −5,7, əsaslı −5,0): **itirilən hər manat gəlirə 1,17 manat xərc azalması düşür**. Bunu iki əlaqə yaradır: F3 (cari xərclər ümumi real gəlirlər üzrə, elastiklik 0,99, 95% interval [0,52, 1,46]) və ssenarilərin dövlət investisiyası yolları (Mənfi ildə −4%: real dövlət investisiyası −23,4%, real neft gəlirləri −15,9%; F4 vahid elastiklik, sərbəst qiymət 0,90 [0,22, 1,58]). Əsas ssenarinin dövlət investisiyası səviyyəsi ilə Mənfi ssenari ÜDM-in −1,85%-i ilə bitərdi | Sıranı bərpa edən hər struktur düzəliş nümunədən kənar balans xətasında ciddi itirir (v2.2-də U 0,61, RMSE ÜDM-in 1,1 f.b.-i) — aşağıdakı cədvəl. Deməli, sıra qiymətləndirilmiş fiskal reaksiyanın xassəsidir (xərclər gəlirləri, əsaslı xərclər neft gəlirlərini izləyir), kod xətası deyil; o, gizlədilmir, açıqlanır |

| Fiskal namizəd (v2.2 modelində, nümunədən kənar yoxlamada olduğu kimi) | 2030 balansı, ÜDM-ə nisbətdə % (Əsas / Mənfi / İslahat) | Mənfi < Əsas < İslahat | Balansın nümunədən kənar U-su (dəyişmə) | Qərar |
|---|---|---|---|---|
| F3: qeyri-neft və neft gəlirləri ayrıca | +1,84 / +3,06 / +1,33 | xeyr | 0,92 (+50%) | rədd edilib |
| F3: yalnız qeyri-neft gəlirləri (neft gəlirləri yığılır) | −0,13 / −0,76 / +0,67 | bəli | 1,43 (+134%) | rədd edilib |
| F3: gəlir elastikliyi 95% etibarlılıq intervalının aşağı həddində | +0,43 / +0,62 / +0,64 | xeyr | 1,41 (+131%) | rədd edilib |
| F4: ssenari kapital xərcləri qaydası (Əsas ssenarinin siyasət səviyyəsi + F4 reaksiyası), vahid elastiklik | +0,43 / +0,67 / +0,46 | xeyr | 0,61 (+0%) | rədd edilib |
| F4: ssenari kapital xərcləri qaydası, neft gəlirləri elastikliyi 95% intervalın aşağı həddində | +0,43 / −0,83 / +1,43 | bəli | 0,75 (+23%) | rədd edilib |

**Proqnoza təsir (Əsas ssenari 2030, v2.2 icrası ilə müqayisədə)** — hamısı E3-ün əmək haqqı fondu həddindən irəli gəlir (1-ci və 2-ci bəndlər
proqnozu dəyişmir): real ÜDM −1,59%, qeyri-neft ÜDM −2,10%, nominal ÜDM +1,68%, İQİ +4,25%, real sərəncamda qalan gəlir
−4,26%, istehlak −4,63%, qeyri-neft idxalı −5,60%: proqnozda real əmək haqqı fondu qeyri-neft
ÜDM-dən yavaş artır. 2026–30 orta artım: real ÜDM **2,57%** (v2.2 2,90; Mənfi
1,32, İslahat 3,62), qeyri-neft **3,76%** (4,20; 2,54, 4,91). 2030 büdcə balansı: Əsas +0,01, Mənfi
+0,98, İslahat −0,39% (ÜDM-ə nisbətdə; v2.2 +0,22 / +1,10 / −0,12). §6.2-nin 14 dəyişəni üzrə median U: təsadüfi gəzişməyə
qarşı 0,591 (v2.2-də 0,592), sabit artıma qarşı 1,036 (1,035).

**Reyestr, mühərrik, sənədləşmə.** `FR1_equations.json`: 174 tənlik (proqnozda 47; v2.2-də 157), yeni: 8 v2.3 spesifikasiyası
(D4 və E3-ün əvəz olunmuş v2.2 formaları və rədd edilmiş namizədlər), hər biri nümunədən kənar müqayisəsi və qərar sətri ilə. Mühərrik:
`addf_halflife` rıçağı; E3 homogenlik bağı indi üç üzvlüdür (pensiya xərcləri elastikliyi = 1 − qeyri-neft ÜDM − əmək haqqı fondu), buna
görə dəyişdirilmiş əmsal məhdudiyyəti saxlayır; öz-özünü yoxlama hər ssenari üzrə hər iki rejimdə keçir. Heç bir CSV-də olmayan icradan asılı
rəqəmlər (§7.1 həlledici iterasiyaları, §7.2 yanvar–aprel ankoru, §7.5 yelpik diaqnostikası, v2.2 müqayisə rəqəmləri) `FR1_doc_figures.json`-a
(Hissə 18.17) ixrac olunur və burada `microlib.docrefresh` ilə yaradılır. FR3, FR4 və FR5 v2.3 proqnozu ilə yenidən icra olunub. §6–§9 v2.3
icrasına istinad edir.

**v2.3.1 düzəlişi (2026-10-06): büdcə balansı multiplikatorları.** `FR1_multipliers.csv` büdcə balansını sıfırdan keçən Əsas
ssenari balansından (2028-ci ildə −97 mln AZN) faiz kənarlaşması kimi verirdi, buna görə reaksiyalar partlayır və işarəsini
dəyişirdi (dövlət investisiyası +1 mlrd AZN: 2026–30-da −306, −849, +2248, −3359, −1569 "%"; v2.2-də 2028-ci ildə +52 130%). Modelin özü səhv deyildi:
hər şok həlli yığılıb (ən böyük qalıq 1e−10), pul ifadəsində reaksiyalar isə hamardır. Balans sütunu indi cari qiymətlərlə mln
AZN fərqidir (inflyasiya f.b.-də, digər sütunlar %-lə qalır): dövlət investisiyası +1 mlrd AZN −1980, −2139, −2352, −2577, −2812; Brent +10 ABŞ dolları/barel
+183, +124, +62, +41, +14; xarici tələb +10% +155, +183, +220, +262, +309. Real və qiymət reaksiyaları və proqnoz dəyişmir. Notebook indi hər şok həllinin yığıldığını və
balance_n, rgdpnon və infl reaksiyalarının 2-ci ildən sonra işarəsini dəyişmədiyini yoxlayır (assert).

**v2.3.2 düzəlişi (2026-10-06): dövlət borcu.** `debt_azn` iş kitabındakı ümumi dövlət borcunu məzənnə ilə çevirirdi, lakin bu
sətir üç fərqli əsasdadır (§2.3, 5-ci bənd): 2025-ci il 38 451 mln AZN idi, düzgün dəyər isə **25 987,5 mln AZN**-dir (xarici
4 813,5 mln ABŞ dolları × 1,70 + daxili 17 804,5 mln AZN; ÜDM-in 20,1%-i); 2010–2020 isə məzənnə qədər təhrif olunmuşdu.
Dövlət borcu indi hər il xarici borc × ilin sonuna məzənnə + daxili borc kimi hesablanır — Maliyyə Nazirliyinin anlayışı (dövlət zəmanətli
borc daxil deyil və iş kitabında yoxdur); `fr1:debt_azn` müvafiq adlandırılıb. Kalibrlənmiş borc xidməti dərəcəsi (2023–25 üzrə borc xidməti
/ borc ortası) və borc eyniliyi düzəldilmiş qalıqdan istifadə edir: 2026 borc xidməti 1 491 mln AZN (əvvəl 1 871);
2030 dövlət borcu ÜDM-in 12,3 / 12,9 / 11,5%-i (Əsas / Mənfi / İslahat; əvvəl 20,5 /
22,2 / 18,9); 2030 büdcə balansı +0,01 / +0,98 / −0,39% (əvvəl +0,09 / +0,99 / −0,26).

**v2.3.3 (2026-10-06): məzənnənin ötürülməsi.** G4-də (məzənnə + əmək haqqı) ötürülmə 0,06 idi: +16,5% devalvasiya İQİ-ni 1-ci ildə
+1,14 f.b., 2-ci ildə +0,02 f.b. artırır, qeyri-neft ÜDM isə *artırdı* (2030-a qədər +0,44%); 2015–17-də ötürülmə ≈0,29 olub.
Namizədlər (Hissə 11.7; yalnız izahedici dəyişənlərin gecikmələri, gecikmiş inflyasiya yoxdur), inflyasiyanın təsadüfi gəzişməyə qarşı U-su (v2.3
forması 1,30): əvvəlki ilin məzənnə dəyişməsi 1,37; manatla idxal qiymətləri (cari il) 0,73; manatla idxal qiymətləri (cari + əvvəlki il) 0,51; 2015-dən sonrakı rejim (cari + əvvəlki il) 1,39; manatla idxal qiymətləri, DSK ilə birləşdirilmiş 0,88. v2.3.3-də manatla idxal qiymətləri forması qəbul edilmişdi (makro modulun ABŞ dolları ilə idxal qiymətləri +
məzənnə, cari + əvvəlki il; U 0,50): devalvasiyada İQİ +3,63 / +0,99 f.b., lakin Əsas ssenaridə 2027–30 inflyasiyası 7,3%.
Qeyri-neft ÜDM niyə artırdı: ötürülmə demək olar ki, olmadığından real gəlirlər az azalırdı, manatla neft gəlirləri isə cari xərcləri (F3) və
dövlət investisiyasını (F4) artırır; real gəlir kanalı (E3-də real əmək haqqı fondu, İQİ-yə indeksləşən pensiyalar) mövcud idi, lakin zəif idi.

**v2.3.4 (2026-10-06): idxal qiymətləri məlumatlarının yoxlanılması — G4 = məzənnə + məzənnə (t−1) + əmək haqqı.** v2.3.3-ün 2023–25
qalıqları (−0,5, +3,2, +3,4 f.b.) idxal qiymətləri sırasından irəli gəlirdi: 2021–25-də ABŞ dolları ilə idxal qiymətlərinin artımı makro modulun
sırasında +33,5, +15,3, −12,7, −6,3, −8,9%, iş kitabının DSK idxal qiymətləri indeksində (`Monetar sektoru`, 98-ci sətir, yalnız 2021–25) isə +20,5, +21,9, +15,8, +19,4, +32,1%-dir —
5 ilin 3-də əks işarəli. (A) 2021–25 üçün DSK indeksi ilə birləşdirilmiş sıra (2020-yə qədər makro modulun artım templəri, 2021–25 DSK):
nümunədən kənar U 0,88 (makro forma 0,51; 10% qaydasından kənar), 2023–25 qalıqları −5,2, −1,9, −3,9 f.b. — aradan qalxmır,
işarəsini dəyişir. İki mənbə uzlaşdırıla bilmədiyi üçün (B) **məzənnə + məzənnə (t−1)** qəbul edilib (U 1,37, v2.3 formasına qarşı
+5%, qayda daxilində; 2023–25 qalıqları −2,9, +0,8, +0,8 f.b.; `FR1_v234_g4_check.csv`). İdxal qiymətləri formaları reyestrdə qalır
(`used_in_forecast = false`). İndi +16,5% devalvasiya: İQİ **1-ci ildə +0,82 f.b., 2-ci ildə +2,20 f.b.** (2030-a qədər səviyyə +2,9%),
qeyri-neft ÜDM +0,26% (2026) / −0,07% (2030), real sərəncamda qalan gəlir −0,68%, dövlət borcu ÜDM-in −0,02 f.b.-i;
F4 reaksiyası olmadan qeyri-neft ÜDM −0,60%.

**2026 İQİ ankoru.** 2026 inflyasiyası, real sektorların yanvar–aprel məlumatında olduğu kimi, son aylıq İQİ-yə ankorlanır:
dsk_cpi.csv 2026-ci ilin 8-ci ayı üçün illik 5,7% verir; qalan aylarda ötən ilin aylıq dəyişmələri təkrarlanır
(1:1; 2021–25-də RMSE 3,6 f.b.), deməli 2026-cı ilin dekabrı = 5,7%. Real sektorların yanvar–aprel ankorlarında olduğu kimi,
bu natamam il məlumatı **əlavə (increment)** kimi daxil olur: G4-ün baza düzəliş əmsalı 2025 qalığı olaraq qalır (+0,77 f.b., sabit), 2026
əlavəsi isə (+2,69 f.b. = nowcast − model) 2026-da tam tətbiq olunur və 2027-dən bir illik yarımsönmə ilə azalır (×0,5, ×0,25, …).
`data/dsk_cpi/`-yə yeni aylıq fayl və ya RiskUnit DSK vintajı gəldikdə yenilənir. Əsas ssenaridə 2026–30 İQİ inflyasiyası: 5,7, 6,1, 5,2, 4,9, 4,6%
(2027–30 ortası 5,2%; Mənfi 4,4, İslahat 6,0).

**2026 dövlət borcu ankoru (v2.3.4).** Maliyyə Nazirliyinin son qalıq məlumatı — 2026-07-01 tarixinə 23 830,6 mln AZN (2025-ci ilin sonu
25 987,5 ilə müqayisədə −8,3%; debt_parsed.json) — 2026-cı ili İQİ və real sektorlar kimi ankorlayır: 2026-cı ilin sonuna
borc = müşahidə olunan qalıq − modelin 2026 büdcə balansı × ilin qalan 6/12 hissəsi = **23 387,4 mln AZN** (ÜDM-in 17,3%-i).
Yalnız eynilik (borc − balans) 25 101,0 verərdi; fərq, −1714 mln AZN, Əsas ssenaridə nəzərdə tutulan 2026 qalıq-axın
düzəlişidir (büdcə balansından kənar maliyyələşdirilən ödənişlər, məs. ARDNF-dən). Düstur həlledicinin daxilində hər hesablamada (ssenarilər,
şoklar, mühərrik) tətbiq olunur, ona görə 2026-cı ilin sonuna borcu yalnız ikinci yarımilin balansı dəyişir (Δborc = −0,50 × Δbalans):
Mənfi 23 518,5, İslahat 23 479,8 mln AZN; 2027-dən eynilik tətbiq olunur. `data/minfin_debt/`-yə daha
yeni bülleten və ya RiskUnit MinFin vintajı gəldikdə yenilənir (`FR1_debt_nowcast.csv`). 2030 dövlət borcu: ÜDM-in 12,3 / 12,9 /
11,5%-i (Əsas / Mənfi / İslahat).

**v2.3.5 (2026-10-06): pensiya xərci, məşğulluq, minimum əmək haqqı.** (1) Pensiyanın real artımı büdcə balansını yaxşılaşdırırdı: pensiyaları
dövlət büdcəsindən kənar DSMF ödəyir, FR1-də isə maliyyələşdirmə eyniliyi yox idi, buna görə yalnız gəlir qazancı (istehlak → ƏDV) görünürdü. İQİ
indeksasiyasından yuxarı real artım (siyasət girişi `pension_real_g`) indi dövlət büdcəsindən DSMF-ə transfertlə (cari xərclər) maliyyələşdirilir =
DSMF pensiya xərcləri (2025-də 7 783 mln AZN, 2024-dən körpü ilə) × (1 − 1/məcmu real artım); tarixdə və nümunədən kənar yoxlamada faktiki
artımlar müşahidə olunan xərclərin içindədir (orada söndürülüb). 2026-dan +10% real pensiya: balans 2026–30-da −825, −902, −1001, −1106, −1216 mln AZN (əvvəl:
+30, +36, +43, +50, +58); xərclər +912, +998, +1109, +1227, +1352, gəlirlər +87, +97, +108, +121, +136. (2) Məşğulluq: FR1-in E1 tənliyi məşğulluq SƏVİYYƏSİNİ adambaşına qeyri-neft
ÜDM ilə 0,034 elastikliklə əlaqələndirir (p = 0,008; ölçülən işsizlik çox sabitdir), buna görə +1 mlrd AZN dövlət investisiyası
2030-a qədər qeyri-neft ÜDM-i +1,20%, məşğulluğu isə cəmi +0,040% artırır — bu qiymətləndirilmiş elastiklikdir, yenidən spesifikasiya
edilməyib. FR4-ün sektor tənlikləri muzdlu (formal) işçilər üçün ümumi məşğulluqdan daha yüksək elastiklik verir: sektor payı 0,174 — 0,108-ə qarşı, bazar xidmətləri 1,63 — 0,70-ə qarşı; siyasət bölməsi FR1-in məşğulluğunu özünüməşğulluq və kənd təsərrüfatının üstünlük təşkil etdiyi ümumi (İQM) məşğulluq kimi oxumalı, formal iş yerlərinə təsiri isə FR4-dən götürməlidir. (3) İş kitabındakı minimum əmək haqqı (`Sosial sektor`, 51-ci sətir) t ilində t+1 ilin 1 yanvarından qüvvədə olan səviyyəni göstərir (2024: 400,
01.01.2025-dən). FR1 indi qüvvədə olan səviyyənin illik ortasından istifadə edir (`data/dsk_minwage/`, DSK 004_1): 2019 203,3 (v2.3.5; v2.3.6-da 195,0),
2024 345, 2025 400. E2 yenidən qiymətləndirilib: minimum əmək haqqı elastikliyi 0,186 (p = 0,14) → **0,384**
(p = 0,000), məhsuldarlıq 0,82 → 0,49, İQİ 0,62 → 0,39; əmək haqqının nümunədən kənar U-su
0,52 → 0,58 (məlumat düzəlişidir, spesifikasiya seçimi deyil). Minimum əmək haqqı +10% (2030): əmək haqqı +2,64 →
+4,67%, real sərəncamda qalan gəlir +0,91 → +1,59%, İQİ +0,85 → +1,50%. Əsas ssenaridə 2026–30
İQİ inflyasiyası: 5,7, 5,2, 4,5, 4,3, 4,0% (əvvəl: 5,7, 5,9, 5,1, 4,9, 4,5). (v2.3.5 icrası; v2.3.6-da düzəldilib.)

**v2.3.6 (2026-10-06): minimum əmək haqqı — ayların çəkisi və dövlət sektoru kanalı.** (1) İllik minimum əmək haqqı DSK 004_1 cədvəli üzrə
qüvvədə olan səviyyənin ay çəkili ortasıdır: 2019 = (2×130 + 6×180 + 4×250)/12 = 195,0 (v2.3.5: 203,3); FR3 eyni sırayı və 2026-nın qanuni səviyyəsini
(400 AZN, 01.01.2025-dən) istifadə edir, artım rıçağı 2027-dən tətbiq olunur. (2) Minimum əmək haqqının hər artımı (2019, 2022, 2023) dövlət sektorunda
əmək haqqı islahatı ilə üst-üstə düşüb. Minimum əmək haqqı elastikliyi DÖVLƏT əmək haqları üçün +0,598 (p = 0,000), QEYRİ-DÖVLƏT
əmək haqları üçün −0,032-dir (p = 0,69), yəni vahid orta əmək haqqı elastikliyi dövlət sektorunun artımını bütün işçilərə aid edir.
Namizədlər (Hissə 11.7; əmək haqqının U-su, v2.3.5 forması 0,55): dövlət sektoru islahatı addımları: U 0,55 (yanlış işarə — rədd edilib); islahatların məcmu indeksi: U 0,25 (yanlış işarə — rədd edilib); dövlət / qeyri-dövlət kanalları ilə məhdudlaşdırılmış elastiklik: U 0,49. **Qəbul edilib: dövlət / qeyri-dövlət kanalları ilə
məhdudlaşdırılmış minimum əmək haqqı elastikliyi**: **0,384 → 0,272**; məhsuldarlıq və İQİ yenidən qiymətləndirilib (0,86, 0,44).
Minimum əmək haqqı +20% (Əsas ssenari, 2030): orta əmək haqqı +9,11 → **+6,98%**, real ÜDM +1,13 → +0,85%, real sərəncamda qalan
gəlir +3,07 → +2,30%, İQİ +2,86 → +2,21% (inflyasiya 2026-da +3,04 → +2,36 f.b.). (3) G4-də əmək haqqının
ötürülməsi 0,347-dir (s.x. 0,176, p = 0,06): dövlət sektorunun əmək haqqı artımlarını özəl sektorun vahid əmək xərcləri kimi qəbul
edir, buna görə minimum əmək haqqı → əmək haqqı → İQİ reaksiyası güclü tərəfdə qalır (PolicyUnit-in 2019 yoxlaması: faktiki İQİ reaksiyası xeyli kiçik);
qeyri-dövlət əmək haqqı xərci həddi ayrıca qeyri-dövlət əmək haqqı bloku tələb edir və burada qəbul edilməyib. Əsas ssenaridə 2026–30 İQİ
inflyasiyası: 5,7, 6,1, 5,2, 4,9, 4,6% (v2.3.5: 5,7, 5,2, 4,5, 4,3, 4,0).
<!-- /AUTO:v23_note -->

<!-- AUTO:v22_note -->
## v2.2 (2026-10-05): Nazirliyin makro modulundan (15.5.1) nə götürülüb

Makro modul (`18august/model`, yalnız oxunur) FR1–FR5-i makro tərəfdən əhatə edir. Onun məlumatları və rəsmi plan rəqəmləri FR1 üçün
nəzərdən keçirilib; hər namizəd **FR1-in öz çərçivəsində yenidən qiymətləndirilib** (eyni nümunə qaydaları, kiçik nümunə HAC, uyğunluq
qaydası), ≤2020 məlumatla seçilib və §6.2-nin **toxunulmamış dinamik 2021–2025 nümunədən kənar yoxlamasında** v2.2-dən əvvəlki modellə
müqayisə olunub (notebook-un yeni Hissə 11.6-sı, `FR1_v22_macro_candidates.csv`). Məlumat surətləri, mənbə yolu və MD5:
`data/macro_module/README_FR1.md`. Makro modulun öz proqnozlaşdırmasından (AR(1)/beşillik orta profillər, İQİ/əmək haqqı/işsizlik
ansamblları, ECM/AR(6) spesifikasiyaları, Okun tənliyi, 2026 yanvar–aprel faktiki göstəricilərini nəzərə almayan 2026 ÜDM yolu) heç nə
istifadə olunmur.

| Bənd | Qərar | Nümunədən kənar yoxlama (Theil U təsadüfi gəzişməyə 2020 / sabit artıma 2010–19 qarşı; RMSE) |
|---|---|---|
| 1. Neft və qaz hasilatı | **Qəbul edilib** (fərziyyə): Əsas ssenari 2027–30 = Nazirliyin planının artım tempi (`8_vereq_original.xlsx`, 2.4.1.4), yanvar–mart faktiki göstəricisindən 2026 səviyyəsinə tətbiq olunur; Mənfi = v2.2-dən əvvəlki Əsas ssenarinin neft azalması (−4,2…−3,0%), qaz plan − 1 f.b.; İslahat = plan + v2.2-dən əvvəlki İslahat fərqləri | Plan qiymətləndirmə deyil. Plan 2025-ci il neft hasilatını artıq göstərib (28,45 əvəzinə 27,68 mln ton, +2,8%; qaz −1,0%). Əsas ssenaridə 2030 neft hasilatı: 26,0 mln ton (əvvəl 22,8) |
| 2. Gəlirin mənbələr üzrə bölgüsü (əmək haqqı fondu + DSMF transfertləri + digər gəlirlər, Δln ayaqları) | Proqnoz üçün **rədd edilib**; mühərrik rıçağı `income_block = legs` | Nümunədaxili ayaqlar daha yaxşıdır (≤2020 real gəlir artımının bir addımlıq RMSE-si 3,5 və 5,0 f.b.; elastikliklər 0,83 əmək haqqı fondu, 0,52 DSMF, 1,24 digər gəlirlər — makro modulda olduğu kimi). Dinamik yoxlamada real sərəncamda qalan gəlir: U 1,79 / 1,42, RMSE 11,6% — **1,27 / 1,01, 8,3%**-ə qarşı; istehlak 0,28 — 0,13-ə qarşı. Ayaqlar nominaldır: kəsimdən əvvəlki model 2025 qiymət səviyyəsini 31% aşağı proqnozlaşdırır, tam indeksləşməyən nominal ayaqlar bunu artıq real gəlirə çevirir. İstehlak qiymətləri ilə deflyasiya edilmiş forma: 1,52 / 1,21 (rədd edilib). Nominal sərəncamda qalan gəlir ayaqlarla daha yaxşıdır (U 0,53 — 0,65-ə qarşı) |
| 3. Mədənçıxarma deflyatoru ixrac dəyəri ilə çəkili neft+qaz ixrac qiymətləri indeksi + məzənnə üzrə | **Qəbul edilib** (makro modulun forması, İQİ həddi olmadan) | Mədənçıxarma deflyatoru U **0,13 / 0,16** (RMSE 6,8%) — 0,52 / 0,63 (27,3%)-ə qarşı; nominal ÜDM 0,48 / 0,75 — 0,64 / 1,00-ya qarşı; ÜDM deflyatoru 0,36 — 0,62-ə qarşı. Yan təsirlər: real ÜDM 0,72 / 1,12 — 0,62 / 0,96-ya qarşı (zəncirvari çəkilər), idxal 0,83 — 0,68-ya qarşı (D4-də yanlış işarəli nisbi qiymət). İQİ əlavə olunmuş variant (≤2020 ən kiçik standart xəta) daha pisdir (0,63) və rədd edilib. Yeni tənlik: 2,5 + 1,02 Δln XPI + 0,51 Δln FX, düzəldilmiş R² 0,80; dayanıqlıq *qeyri-stabil* (2016 orta nöqtəsində Chow, p = 0,005) |
| 4. 2026 Dövlət İnvestisiya Proqramı | **Qəbul edilib**: 2 700 mln AZN (öz iş kitabı, `DİP 2016-2026`, nəzərdə tutulmuş vəsait; 2025 faktiki 2 305; makro modul eyni xanaya istinad edir) | Fərziyyə. Proqramın 2025-ci ildə real dövlət investisiyasındakı payı (20,4%) 2026-da modelin öz 2026 investisiya deflyatoru ilə proqramla əvəz olunur (tərpənməz nöqtə); 2026 real dövlət investisiyası +3,9% (əvvəl +1,5%). `fr1:exp_pubinv_n` kimi dərc olunur (hər ssenaridə 2026 = 2 700) |
| 5. Fiskal qapanma: qeyri-neft balansı / qeyri-neft ÜDM kəsim ilinin səviyyəsində | **Rədd edilib**; mühərrik rıçağı `fiscal_rule = nobd`; nisbət dərc olunur (`fr1:nobd_pct`) | Ümumi xərclər yaxşılaşır (U 0,32 — 0,51-ə qarşı), lakin qaydanın məqsədi olan büdcə balansı xeyli pisləşir: RMSE ÜDM-in 5,2 f.b.-i — 1,1-ə qarşı (U 2,80 — 0,61-ə qarşı), çünki neft gəlirlərinin xətaları balansa 1:1 keçir. F3 ilə Mənfi ssenari 2030-da ən yaxşı balansı saxlayır (ÜDM-in +1,1%-i; Əsas +0,2, İslahat −0,1): xərclər gəlirləri izləyir və Mənfi ssenari dövlət investisiyasını ildə 4% azaldır. Rıçaqla 2030 balansları −13,4 / −15,2 / −12,0 mlrd AZN-dir (Mənfi ən pis) |
| 6. İdxal udma + real effektiv məzənnə üzrə | **Rədd edilib** | REER hər iki nümunədə yanlış işarəlidir (≤2020 −1,06, p = 0,02; tam −0,32, p = 0,12); idxal U 1,31 / 0,87 — 0,68 / 0,45-ə qarşı. D4 dəyişməyib |
| 7. Sektor deflyatorları sektor qiymət sürücüləri üzrə | **Buraxılıb** | Sürücülərin (kənd təsərrüfatı istehsalçı qiymətləri, nəqliyyat və rabitə tarifləri, tikinti deflyatoru) 2026–30 üçün ekzogen yolu yoxdur: makro modul onları AR/orta profillərlə proqnozlaşdırır (`pdrv_*`), bir neçəsi yalnız 2021-dən mövcuddur |

**Proqnoza təsiri (Əsas ssenari, v2.1-ə nisbətən).** 2026 real göstəricilərdə dəyişmir (yanvar–aprel ilə ankorlanıb); dəyişikliklər
2027-dən başlayır: 2030 real ÜDM +2,5% (neft-qaz ÜDM +11,8%), qeyri-neft ÜDM +1,0%, nominal ÜDM +4,4% (mədənçıxarma deflyatoru), 2030 İQİ
+0,3%, real sərəncamda qalan gəlir +0,9%. 2026–30 orta artım: real ÜDM **2,90%** (v2.1 2,40; Mənfi 1,76, İslahat 3,85), qeyri-neft **4,20%**
(3,99; 3,09, 5,23). Fəallıq üzrə ssenari sırası dəyişməyib (Mənfi < Əsas < İslahat). 2030 büdcə balansı ÜDM-in +0,22%-i (Əsas); 2026
balansı aşağıdır (+948 əvəzinə +636 mln AZN: proqram). §6.2-nin 14 dəyişəni üzrə median U: təsadüfi gəzişməyə qarşı 0,59 (əvvəl 0,58),
sabit artıma qarşı 1,04 (1,02); median RMSE 13,2% (14,6%).

**Reyestr və mühərrik.** `FR1_equations.json`: 157 tənlik (47-si proqnozda): yeni — gəlirin dörd ayağı (E3a–E3d, qiymətləndirilib və
reyestrdədir, `used_in_forecast = false`, nümunədən kənar müqayisəsi ilə), onların İQİ ilə deflyasiya edilmiş variantları, v2.2-dən əvvəlki
və İQİ əlavə olunmuş mədənçıxarma deflyatorları, udma + REER ilə D4; G5_defl_min əvəz olunub. Mühərrik (`microlib/engines/fr1.py`,
`_fr1_*.py`): yeni girişlər `sip_n` (proqram, nominal) və `dsmf_add_g`; rıçaqlar `income_block`, `fiscal_rule`; yeni sıralar
`fr1:gdpnon_n`, `hhdisp_n`, `nobd_pct`, `exp_pubinv_n`, `gas_exp_price`, `xsh_oil`, `dln_xpi` (kataloqda 478 komponent).
`income_block = legs` ilə minimum əmək haqqının 10% artması 2030-a qədər real sərəncamda qalan gəliri ~1,0% artırır; proqnoz modelində
(E3) artırmır (−0,31%, qiymətlər vasitəsilə). Öz-özünü yoxlama bütün ssenarilər üzrə hər iki rejimdə keçir; FR3, FR4 və FR5 yenidən icra
olunub. Bu qeyd v2.2 mərhələsini qeyd edir (proqnoz rəqəmləri v2.2 icrasınındır; v2 və v2.1 qeydləri də öz icralarının rəqəmlərini
saxlayır); §6–§9 cari (v2.3) icraya istinad edir.
<!-- /AUTO:v22_note -->


## 0. Tələblərə uyğunluğun izlənilməsi

FR1 *"bu sektorların hər biri üçün hazırlanmış, həm ayrı-ayrılıqda, həm də birgə təhlil edilən və proqnozlaşdırılan struktur, dinamik və
çoxölçülü ekonometrik modellər"* tələb edir; sektor bölgüsü Dövlət Statistika Komitəsinin (DSK)
təsnifatına uyğun olmalıdır. AZSEM-FR1 bu bölgünü dəqiq tətbiq edir:

| FR1 sektoru (azərbaycanca adı) | Kod | Modeldə nəzərə alınması |
|---|---|---|
| Sənaye — mədənçıxarma | `min` | Həcmlə müəyyən edilir; miqyasdan sabit gəlir test edilib və rədd edilib |
| Sənaye — emal sənayesi | `man` | İstehsal gücü + tikinti + ixrac tələbi (α_K = amil payı test edilib, rədd edilib) |
| Sənaye — elektrik enerjisi, qaz və buxar | `elc` | Qeyri-neft fəaliyyətindən törəmə tələb |
| Sənaye — su təchizatı, tullantıların emalı | `wat` | Adambaşına kommunal xidmət tələbi |
| *Qeyri-neft-qaz sənayesi* | — | Qeyri-karbohidrogen sənaye komponentlərinin aqreqasiyası |
| Kənd, meşə və balıqçılıq təsərrüfatları | `agr` | Trend (kapital həddi çıxarılıb: səhv işarəli, statistik əhəmiyyətsiz; 2015-ci il trend qırılması kəsimdən əvvəlki məlumatlarda test edilib və qəbul edilməyib) |
| Tikinti | `con` | Dövlət və özəl investisiya |
| Ticarət; nəqliyyat vasitələrinin təmiri | `trd` | İstehlak (vahid elastiklik test edilib və rədd edilib; uzunmüddətli 0.96) |
| Nəqliyyat və anbar təsərrüfatı | `tra` | Karbohidrogen tranzit həcmi + trend (qeyri-neft ÜDM çıxarılıb: səhv işarəli, statistik əhəmiyyətsiz) |
| Turistlərin yerləşdirilməsi və ictimai iaşə | `tou` | Adambaşına sərəncamda qalan gəlir + trend |
| İnformasiya və rabitə | `ict` | Adambaşına İKT kapitalının dərinləşməsi + trend |
| Sosial və digər xidmətlər | `oth` | Adambaşına sərəncamda qalan gəlir + trend; İQİ-dən vahid ötürülmə əmsalı ilə deflyator |
| Məhsula və idxala xalis vergilər | `nettax` | İstehlak + idxal (fiskal blokla əlaqə) |

**"Ayrı-ayrılıqda"** tələbi hər sektor üçün öz amilləri, elastiklikləri, məhdudiyyət testləri və qalıq diaqnostikası olan
bir struktur tənlik vasitəsilə təmin edilir. **"Birgə"** tələbi isə bu tənliklərin milli hesablar, fiskal, monetar və tədiyə balansı
eynilikləri ilə qapanan vahid **eyni zamanlı sistem** kimi həll edilməsi ilə (beləliklə, hər sektorun proqnozu digər bütün sektorların
proqnozundan asılı olur), habelə notebook-un Hissə 14-dəki multiplikator təhlili ilə təmin edilir; bu təhlil hər hansı bir amilə verilən şokun
bütün on iki komponent üzrə necə yayıldığını izləyir.

---

## 1. Metodoloji mövqe

### 1.1 İstisna: nəyi əhatə edir və nəyi əhatə etmir

Modelin heç bir yerində avtoreqressiv, ARIMA, ARCH və ya GARCH komponenti yoxdur. Konkret olaraq: **heç bir davranış tənliyində asılı
dəyişənin gecikməsi yoxdur**, heç bir dəyişən öz tarixi əsasında proqnozlaşdırılmır və proqnoz qeyri-müəyyənliyi şərti dispersiya modelindən deyil,
qiymətləndirilmiş struktur qalıq *vektorlarının* butstrap (bootstrap) üsulu ilə təkrar seçilməsindən yaranır.

Aşağıdakı konstruksiyalar gecikmələri, davamlılığı (persistence) və ya avtoreqressiyaya bənzəyən hesablamaları ehtiva edir, lakin heç bir dəyişənin avtoreqressiv modeli
**deyil**. Hər biri notebook-da rast gəlindiyi yerdə qeyd olunur:

| Konstruksiya | Niyə AR modeli deyil |
|---|---|
| `K_t = (1−δ)K_{t−1} + I_t` | Milli hesablar eyniliyi; δ **qoyulub**, heç nə qiymətləndirilmir |
| `cpi_t = cpi_{t−1}(1+π_t)` | Qiymətləndirilmiş *sürəti* kumulyativ toplayan qiymət *səviyyəsi* |
| `debt_t = debt_{t−1} − balance_t` | Ehtiyat-axın uçotu |
| Zəncirvari aqreqasiya | Rəsmi aqreqasiya qaydası ötən ilin nominal çəkilərini tələb edir |
| DOLS qabaqlayıcı/gecikmələri | Yalnız **fərqləndirilmiş izahedici dəyişənlərin** qabaqlayıcı və gecikmələri; asılı dəyişənin öz gecikmələri heç vaxt daxil olmur |
| Sabit baza düzəliş əmsalları | Hər tənliyin öz 2025 qalığı sabit saxlanılır — bu, qalıqların stasionarlığının ümumiyyətlə **göstərilmədiyi** nəticəsinə uyğundur; həssaslıq təhlilində onlar sabit, istifadəçinin təyin etdiyi yarımparçalanma müddəti ilə sönür (v2.3; v2.2-yə qədər hər qalığın qiymətləndirilmiş avtokorrelyasiyası ρ̂ ilə — indi çıxarılıb) |
| 2026 lövbər artımının sönməsi | **Ekspert qaydası**: 2026-cı ilin yanvar–aprel məlumatlarından alınan düzəliş əmsalı artımı 2026-cı ildə tam tətbiq olunur və ildə sabit 0.5 əmsalı ilə sönür (yarımsönmə dövrü bir il); dəyişənin tarixi əsasında heç nə qiymətləndirilmir |
| Yanvar–aprel → tam il körpüsü | Eyni ilin iki ölçməsini əlaqələndirir |
| Yelpik qrafiki şokları | Tarixi beşillik qalıq *yolları* təkrar tətbiq olunur (u_{s+h} − u_s); qalıq dinamikası üzrə heç nə qiymətləndirilmir |
| Pensiyaların İQİ-yə indeksləşdirilməsi | Siyasət dəyişəni üçün qanunla müəyyən edilmiş siyasət qaydası |

Newey–West **HAC standart xətaları** yalnız statistik nəticəni düzəldir; onlar heç vaxt qiymətləndirilmiş dəyəri və ya proqnozu dəyişmir. **ADF/KPSS testləri**
spesifikasiya diaqnostikasıdır; onları heç bir proqnoz rəqəmini dəyişmədən silmək olar. Qalıqlara əsaslanan kointeqrasiya testləri
(MacKinnon) də diaqnostikadır.

### 1.2 Burada struktur yanaşma niyə düzgün seçimdir

- **Əsas amil ekzogendir.** Karbohidrogenlər ÜDM-in 28,5%-ni, mal ixracının 85,6%-ni və büdcə gəlirlərinin 48,1%-ni təşkil edir
  (2025). Neft hasilatı 2019-cu ildən bəri ildə 4,9% azalıb, qaz hasilatı isə plato səviyyəsinə çatıb (ildə +6,1%-dən sonra 2025-ci ildə +1,0%). Heç bir filtr
  bunu bilə bilməz; bu, ssenari kimi qoyulmalıdır.
- **Siyasət sualları siyasət rıçaqları tələb edir.** Model dövlət investisiyası, kredit şərtləri və ya neft qiyməti dəyişərsə nə baş verəcəyi
  sualına cavab verməlidir. Bu rıçaqlar yalnız struktur modeldə mövcuddur və Hissə 14 onların hər birinin təsirini kəmiyyətcə qiymətləndirir.
- **Nümunədə struktur qırılmalar üstünlük təşkil edir.** 2015-ci il devalvasiyası (0,78→1,77), 2020-ci il pandemiyası və 2021–22-ci illərin qaz qiyməti şoku
  istənilən avtoreqressiv parametrləşdirməni qeyri-stabil edir. Struktur model bunları öz səbəblərinə aid edir.

---

## 2. Məlumat qatı

### 2.1 İş kitabının quruluşu və üç tələ

Göstəricilər sətirlər üzrə, dövrlər isə sütunlar üzrə yerləşir və iki növdə olur: **illik** (sadəcə dördrəqəmli il) və **ilin əvvəlindən
kumulyativ** (`2026 yanvar-aprel` = yanvardan aprelədək toplanmış). Diqqətdən kənarda qalarsa, üç tələ nəticələri xəbərdarlıq etmədən təhrif edir:

1. **Qarışıq onluq yazılış qaydaları** — `29886,9`, `2.472,8`, `1 234,5` və çatışmayan dəyər üçün `-`, bəzən hamısı eyni sətirdə.
2. **Təkrarlanan adlar** — `"Sənaye"` eyni vərəqin əlavə dəyər, ümumi buraxılış *və* investisiya bloklarında rast gəlinir. Buna görə dəyişənlərə
   **(vərəq, sətir)** ünvanı ilə müraciət edilir və bütün 196 ünvanın gözlənilən ada və ölçü vahidinə uyğunluğu qurulma (build) mərhələsində
   yoxlanılır. Gələcəkdə sətir əlavə edilərsə, səhv sıranın səssizcə modelləşdirilməsi əvəzinə açıq xəta verilir.
3. **Azərbaycan dilində hərf registri** — `"İ".lower()` `"i"` deyil, `i` + U+0307 qaytarır. Bu, işlənmə zamanı faktiki olaraq bir dəyişənin itməsinə səbəb olmuşdur.
   Əks tələyə də diqqət yetirilməlidir: `"I".lower()` Azərbaycan dilindəki nöqtəsiz `ı` deyil, `i` qaytarır, buna görə `ı`-nın `i`-yə çevrilməsi onu ehtiva edən
   hər bir literalla (`buraxılış`, `sayı`, `balıqçılıq`) uyğunluğu pozur. Yalnız birləşən nöqtə (combining dot) halı unifikasiya olunur.

### 2.2 Məlumatların əhatə dairəsi blok-rekursiv quruluşu şərtləndirir

| Blok | Nümunə | n |
|---|---|---|
| Sektoral əlavə dəyər, buraxılış, istehlak, gəlir, əmək | 2000–2025 | 26 |
| Sənaye yarımsahələri | 2005–2025 | 21 |
| Monetar göstəricilər, kredit, depozitlər, dollarlaşma | 2006–2025 | 20 |
| Fiskal göstəricilər, tədiyə balansı, gömrük ticarəti, işsizlik | 2010–2025 | 16 |
| Sənaye yarımsahələri paneli (29 sahə) | 2016–2025 | 290 sətir; istehsal funksiyası üçün yararlı 259 sahə-il (27 sahə) |
| Regional panel (14 iqtisadi rayon) | 2021–2025 | 70 |

Təxminən on illik müşahidədən az olan sıralar (idxal/ixrac qiymət indeksləri, ixracın diversifikasiyası indeksləri, ƏDV) əsas tənliklərdən
çıxarılır və yalnız diaqnostika və ya ssenari girişləri kimi istifadə olunur. Beş müşahidəli izahedici dəyişən struktur
elastikliyi identifikasiya edə bilməz.

### 2.3 Yoxlanılmış eyniliklər — beş real problem aşkarlanıb

Qiymətləndirmədən əvvəl iyirmi dörd eynilik test edilir (dözümlülük həddi 1%, büdcə balansı və işsizlik eynilikləri üçün 5%);
onlardan on doqquzu ödənilir. Dörd uyğunsuzluq araşdırılmış (beşincisi, dövlət borcu, v2.3.2-də aşkarlanıb) və
hər biri modeldə dəyişikliyə səbəb olmuşdur:

1. **Büdcə xərcləri** — `total ≠ current + capital`; həqiqi eynilik `total = current + capital + debt service` şəklindədir və
   2010–2025-ci illərin hər birində 0,0 dəqiqliklə ödənilir. İkikomponentli eynilik xərcləri 10%-ə qədər təhrif edərdi.
2. **2006-cı ilədək ümumi investisiya** — neft/qeyri-neft, daxili/xarici və dövlət/özəl üzrə dekompozisiyalar bir-biri ilə uzlaşır,
   lakin dərc edilmiş yekunla uzlaşmır (2004: 4 922,8-ə qarşı 8 840,0). Onlar 2006-cı ildən etibarən tam uzlaşır, buna görə investisiya tənlikləri
   həmin ildən başlayır.
3. **1995–97-ci illərdə sənaye investisiyası** — yekun müsbət olduğu halda alt komponentlər hərfi sıfır kimi qeydə alınıb; bunlar yalançı sıfırlardır
   və çatışmayan dəyər kimi yenidən təyin edilib.
4. **2024-cü ildə sənaye investisiyası** — alt komponentlərin cəmi dərc edilmiş yekundan 3,6% aşağıdır. Bu, mənbədəki həqiqi uyğunsuzluqdur;
   düzəliş edilmək əvəzinə qeyd olunub və bu məsələnin məlumat təqdimatçısı qarşısında qaldırılmasına dəyər.
<!-- AUTO:v23_debt -->
5. **Dövlət borcu (v2.3.2)** — iş kitabındakı cəm ('Ümumi dövlət borcu', `Fiskal sektor` 22-ci sətir, mln ABŞ dolları kimi
   işarələnib) üç fərqli əsasdadır: 2010–2020-də mln AZN-lə (2020: 16 938,8 = xarici 8 821,5 mln ABŞ dolları × 1,7000 + daxili
   1 942,3 mln AZN), 2021–2024-də mln ABŞ dolları ilə (2024: 16 106,0), 2025-ci ildə isə çevrilmədən toplanmış
   22 618,0 = 4 813,5 (ABŞ dolları) + 17 804,5 (AZN). Bütün sətrin məzənnə ilə çevrilməsi 2025 üçün 38 451 mln AZN
   verir, 2010–2020-ni isə məzənnə qədər təhrif edirdi (2010-da ×0,80, 2020-də ×1,70). Dövlət borcu indi hər il xarici borc (24-cü sətir) × ilin sonuna məzənnə + daxili
   borc (23-cü sətir) kimi hesablanır — Maliyyə Nazirliyinin anlayışı, dövlət zəmanətli borc daxil deyil: **2025-ci ildə
   25 987,5 mln AZN (ÜDM-in 20,1%-i)**. Üç əsas notebook-da yoxlanılır (assert).
<!-- /AUTO:v23_debt -->

### 2.4 Törəmə dəyişənlər

- **Əhali** `GDP / GDP per capita` kimi bərpa edilir — 2025-ci ildə 10,24 mln; bu sıra faylda başqa şəkildə mövcud deyil. Proqnozda onun
  **kodda hesablanan 2021–2025-ci illər üzrə orta artım tempi — ildə 0,483%** — istifadə olunur; trayektoriya `FR1_forecast_full.csv` faylında `pop` (min nəfər) kimi ixrac edilir və
  FR4 və FR5 tərəfindən eyni şəkildə istifadə olunur.
- **Sabit (2015) qiymətlərlə həcmlər** rəsmi “əvvəlki il = 100” artım indekslərinin zəncirvari birləşdirilməsi yolu ilə.
- **İmplisit deflyatorlar** `nominal / real` kimi; beləliklə, qiymət bloku fərz edilmir, kəmiyyət blokundan *törədilir*.
- **Kapital ehtiyatları** aktivin xidmət müddətinə görə fərqləndirilmiş amortizasiya ilə daimi inventar üsulu (perpetual inventory) vasitəsilə (İKT 12%, tikinti 8%, emal sənayesi
  və mədənçıxarma 7%, ticarət 6%, kənd təsərrüfatı 5%, elektrik enerjisi və digər xidmətlər 4%, su təchizatı 3%). “Sosial və digər xidmətlər” üçün vahid
  investisiya sətri yoxdur, buna görə onun kapitalı dövlət idarəetməsi + təhsil + səhiyyə üzrə kapital xərcləri kimi qurulur.

### 2.5 Bütün modeli müəyyən edən iki aqreqasiya faktı

**Aqreqator istifadə edilməzdən əvvəl yoxlanılır.** Rəsmi real ÜDM artımı əvvəlki ilin qiymət çəkiləri ilə zəncirvari üsulla hesablanır:
`g_t = Σ_i w_{i,t−1} · g_{i,t}`. 2010–2025-ci illər üzrə dərc edilmiş artımın təkrar hesablanması **MAE 0,028 f.b. (maksimum 0,107 f.b.)** verir. Sadə
alternativ — sabit 2015 çəkiləri ilə real komponentlərin cəmlənməsi — **2,03 f.b.-yə qədər** xəta verir, çünki həcmi azaldıqca mədənçıxarmanın nominal çəkisi
45,9%-dən (2010) 25,6%-ə (2025) enmişdir. Bütün proqnoz aqreqasiyası yoxlanılmış qaydadan istifadə edir və məhz bu, model nəticələrinin
DSK nəşrləri ilə uzlaşdırıla bilməsini təmin edir.

**Zəncirvari həcmlər additiv deyil.** `real oil GDP + real non-oil GDP ≠ real GDP`; fərq −5,3%-dən (2010) +4,9%-ə
(2025) qədər dəyişir. Buna görə real qeyri-neft ÜDM heç vaxt çıxma yolu ilə deyil, **öz** zəncirvari artım tempi əsasında qurulmalıdır. *Nominal*
bölgü isə, əksinə, dəqiqdir: `non-oil GDP = Σ(non-mining VA) + net taxes − (oil GDP − mining VA)` hər il 0,000% dəqiqliklə
ödənilir; aradakı fərq neft emalı və neft xidmətlərindən (3–4 mlrd manat) ibarətdir.

---

## 3. Modelin arxitekturası

Səkkiz blokda 30 davranış səviyyə əlaqəsi, 17 temp (inflyasiya/deflyator) tənliyi və təxminən on iki eynilik; hər il 51 endogen
dəyişən eyni zamanda həll edilir.

```
     ┌── A. EKZOGEN DƏYİŞƏNLƏR / SSENARİ ─────────────────┐
     │ Brent · neft hasilatı · qaz hasilatı · qazın ixrac │
     │ qiyməti · əhali · məzənnə · uçot və depozit        │
     │ dərəcələri · dövlət investisiyasının SƏVİYYƏSİ ·   │
     │ xarici tələb · minimum əmək haqqı                  │
     └─────────┬──────────────────────────────────┬───────┘
               ▼                                  ▼
     ┌── B. KARBOHİDROGEN ────────┐      ┌── F. FİSKAL ───────────────┐
     │ ixrac qiymətləri           │─────▶│ neft gəlirləri             │
     │ mədənçıxarmada əlavə dəyər │      │ qeyri-neft gəlirləri       │
     │ neft və qaz ixracı         │      │ cari xərclər               │
     └─────────┬──────────────────┘      │ DÖVLƏT İNVESTİSİYASI (F4)◀─┤ neftdən qeyri-neft sektoruna
               │                         │ kəsir, borc                │ ötürülmə kanalı
               │                         └────────┬───────────────────┘
               ▼                                  ▼
     ┌── C. REAL SEKTOR (11 sektor + vergi fərqi) ────────────────────────────┐
     │ agr  min  man  elc  wat  con  trd  tou  tra  ict  oth  nettax          │
     │ hər biri: istehsal gücü + sektorlararası əlaqələr + tələb + TFP trendi │
     └──────┬──────────────────────────────────────────────────────────┬──────┘
            │                 zəncirvari ÜDM eyniliyi                  │
            ▼                                                          ▼
   ┌── D. TƏLƏB ────────┐                           ┌── E. GƏLİR / ƏMƏK ───────┐
   │ istehlak           │◀─────────────────────────▶│ iştirak səviyyəsi        │
   │ investisiya        │                           │ məşğulluq səviyyəsi      │
   │ ixrac              │                           │ əmək haqqı               │
   │ idxal              │                           │ sərəncamda qalan gəlir   │
   └────────┬───────────┘                           └──────────────────┬───────┘
            ▼                                                          ▼
   ┌── G. PUL VƏ QİYMƏTLƏR ─┐                               ┌── H. XARİCİ SEKTOR ┐
   │ depozitlər, kredit     │                               │ cari hesab         │
   │ sektorlar üzrə bölgü   │                               │ ticarət balansı    │
   │ kredit faizi           │                               └────────────────────┘
   │ İQİ inflyasiyası       │
   │ 12 sektor deflyatoru   │
   └────────────────────────┘
```

### 3.1 B bloku — karbohidrogenlər kvazi-ekzogen gəlir kimi

Qiyməti qəbul edən və həcmlə məhdudlaşan blok. Qiymətləndirilənlər: neftin ixrac qiyməti Brent üzrə, **uzunmüddətli elastiklik 1,17** — **vahid ötürülmə
əmsalı rədd edilir** (HAC-F p = 0,017; s.x. 0,068), yəni Azərbaycanın ixrac qiyməti Brent-ə həddindən artıq reaksiya verir; mədənçıxarmanın real əlavə dəyəri neft
və qaz həcmləri üzrə, **0,86 / 0,26** — miqyasdan sabit gəlir **rədd edilir** (p = 0,046) və qoyulmur; karbohidrogen mallarının ixracı
həcm × qiymət kimi (bir tonda 7,400 barel və tədiyə balansı (BOP) nisbəti 1,002 olan eynilik).

Qazın *ixrac* qiyməti **qəsdən modelləşdirilmir**: Brent üzrə reqressiya statistik əhəmiyyətli əmsal olmadan R² 0,17 verir,
çünki 2022-ci ildə Avropa qaz şoku bu ikisi arasındakı əlaqəni qırmışdır (Brent xeyli az dəyişdiyi halda 276 → 790 USD/min m³). Əlaqənin məcburi
qurulması artıq mövcud olmayan ötürülmə kanalını süni şəkildə yaradardı, buna görə o, ekzogen ssenari dəyişənidir.

### 3.2 C bloku — sektorlararası ötürülmə

Hər sektor aşağıdakı formaya malikdir

> `ln(real VA_i) = α_i + β_i ln(capacity_i) + Σ_j δ_ij ln(real VA_j) + γ_i ln(demand_i) + λ_i·trend`

burada `δ_ij` əmsalları hər sektorun əlaqəli sektorlardan necə təsirləndiyini göstərmək barədə FR1 tələbinə cavab verir. Əlaqələr heç vaxt uyğunluq
axtarışı ilə deyil, *a priori* xərclər–buraxılış (input–output) məntiqi əsasında seçilir: tikinti ← dövlət və özəl investisiya; emal sənayesi ←
kapital, tikinti (tikinti materialları) və qeyri-neft ixracı; ticarət ← istehlak; nəqliyyat ← qeyri-neft fəaliyyəti; turizm və
digər xidmətlər ← adambaşına sərəncamda qalan gəlir; İKT ← adambaşına İKT kapitalı; elektrik enerjisi və su təchizatı ← törəmə tələb; xalis vergilər ←
istehlak və idxal.

**Trend intizamı üzrə dərs.** İlkin spesifikasiyada miqyas dəyişəni kimi `ln(population)` istifadə edilmiş və 2–4 həddində elastikliklər
alınmışdı, çünki 2000–2025-ci illərdə əhali demək olar ki, determinist trenddir və TFP artımını özünə çəkirdi. Bütün model boyu iki düzəliş tətbiq
olunur: ev təsərrüfatlarının tələbi ilə müəyyən olunan sektorlar **adambaşına** modelləşdirilir (əhali üzrə elastiklik qiymətləndirilmir, vahidə bərabər qoyulur) və
texniki tərəqqi trendə malik izahedici dəyişən vasitəsilə gizli şəkildə daxil edilmək əvəzinə **açıq trend** ilə ifadə olunur.

### 3.3 D–H blokları və fiskal ötürülmə kanalı

- **İstehlak** — adambaşına sərəncamda qalan gəlir (uzunmüddətli elastiklik 0,93) və ev təsərrüfatlarına verilən kredit (0,12, statistik əhəmiyyətsiz). Ex-post
  real kredit faiz dərəcəsi çıxarılmışdır (Bölmə 5).
<!-- AUTO:v23_e3 -->
- **Ev təsərrüfatlarının gəliri (E3)** — pay əlaqəsi (v2.3: real əmək haqqı fondu ilə): ln(gəlir / pensiya xərcləri) ln(qeyri-neft ÜDM /
  pensiya xərcləri) və ln(əmək haqqı fondu / pensiya xərcləri) üzrə; elastikliklər qeyri-neft ÜDM üzrə 0,60, real əmək haqqı fondu
  (orta əmək haqqı × məşğulluq / istehlak qiymətləri; 2025-ci ildə əmək ödənişlərinin ev təsərrüfatlarının gəlirindəki payı 0,43) üzrə
  0,38, pensiya xərcləri üzrə 0,02 (homogenlik qoyulub: ≤2020 məlumatla rədd edilmir, p = 0,16; tam nümunədə rədd
  edilir, p = 0,001, orada sərbəst formada qeyri-neft ÜDM həddi səhv işarəlidir). Qeyri-neft ÜDM qalan bazar gəlirlərini (sahibkarlıq
  və mülkiyyət gəlirləri), əmək haqqı fondu isə əmək haqqı və minimum əmək haqqı kanalını təmsil edir. Pensiya xərcləri **proksidir**: orta
  pensiya × ümumi əhali (iş kitabında pensiyaçıların sayı yoxdur). Pensiyalar siyasət dəyişənidir və proqnozda İQİ-yə indeksləşdirilir.
<!-- /AUTO:v23_e3 -->
- **İnvestisiya** — qeyri-neft buraxılışı (0,20) və dövlət investisiyası (0,89) üzrə akselerator. Kredit termini yoxdur: onun sərbəst qiymətləndirməsi səhv
  işarəlidir, regional panel qiyməti isə aqreqat məlumatlarla rədd edilir.
- **Dövlət investisiyası (F4)** — real dövlət investisiyası real neft gəlirləri üzrə, qiymət 0,90; vahid elastiklik **rədd edilmir (aşağı
  güc**: p = 0,76, s.x. 0,31) və qoyulub.
- **Qeyri-neft gəlirləri** — qeyri-neft ÜDM-ə görə uzunmüddətli elastiklik (buoyancy) 1,32; vahid elastiklik rədd edilmir (aşağı güc: p = 0,12, s.x. 0,19)
  və qoyulub, üstəgəl idxal (0,56).
- **Kredit (G1)** — real depozitlər (0,52) və uçot dərəcəsi (−0,043); qeyri-neft ÜDM çıxarılıb (səhv işarə, −0,67).
<!-- AUTO:v23_g4 -->
- **İnflyasiya** — struktur xərc əlavəsi (v2.3.4): cari ildə məzənnə dəyişməsi (0,041, p = 0,25) və əvvəlki ildə məzənnə
  dəyişməsi (0,131, p = 0,010; izahedici dəyişənin gecikməsi, gecikmiş inflyasiya yoxdur) və əmək haqqı artımı (0,347, p = 0,06);
  R² 0,31. Məzənnənin məcmu ötürülməsi 0,17 (2015–17 tarixi: 0,29); idxal qiymətləri formaları çıxarılıb, çünki
  iki idxal qiyməti mənbəyi 2021–25-də bir-birinə ziddir (v2.3.4 qeydi).
<!-- /AUTO:v23_g4 -->
- **Deflyatorlar** — hər sektorun deflyator inflyasiyası İQİ inflyasiyası üzrə; mədənçıxarma (v2.2, makro modulun forması) ixrac dəyəri ilə
  çəkili neft + qaz ixrac qiymətləri indeksi (ABŞ dolları) və məzənnə üzrə, İQİ həddi olmadan. Sosial və digər
  xidmətlər üçün sərbəst qiymətləndirmə (dreyf 6,6 f.b., ötürülmə əmsalı 0,59) ildə ~9% nəzərdə tuturdu; “dreyf yoxdur, vahid
  ötürülmə əmsalı” birgə hipotezi rədd edilir (p = 0,001), lakin təkcə vahid ötürülmə əmsalı rədd edilmir (p = 0,22), buna görə vahid ötürülmə əmsalı qoyulur və
  dreyf saxlanılır. Deflyatorun loqarifmik dəyişiklikləri indi dəqiq (exp) tətbiq olunur; bu, ölçü vahidləri ilə bağlı proqram xətasını aradan qaldırır.
- **Kreditin sektorlar üzrə bölgüsü** — cəmlənmə şərti (adding-up) qoyulmaqla SUR ilə qiymətləndirilmiş pay sistemi.

## 4. İdentifikasiya və qiymətləndirmə

### 4.1 1-ci vasitə — məhdudiyyətlər əvvəlcə test edilir, sonra qoyulur

Məhdudiyyətlər uzunmüddətli DOLS əmsalları üzərində kiçik nümunə üçün HAC-F testi ilə yoxlanılır və yalnız rədd edilmədikdə qoyulur (məhdudiyyət
altında yenidən qiymətləndirmə yolu ilə); rədd edilməmə test edilmiş kombinasiyanın s.x.-i ilə birlikdə təqdim olunur və heç vaxt təsdiq kimi deyil, “rədd edilmir
(aşağı güc)” kimi şərh olunur:

| Məhdudiyyət | Qiymət | HAC-F p | Kombinasiyanın s.x.-i | Nəticə |
|---|---|---|---|---|
| Neftin ixrac qiyməti: Brent-dən vahid ötürülmə əmsalı | 1.174 | 0.017 | 0.068 | Rədd edilib (qoyulmayıb) |
| Ticarətin əlavə dəyərinin istehlaka görə elastikliyi = 1 | 0.961 | 0.003 | 0.011 | **Rədd edilib** |
| Mədənçıxarma: neft + qaz elastiklikləri = 1 | 1.126 | 0.046 | 0.056 | **Rədd edilib** |
| Neft-qaz ÜDM: neft + qaz elastiklikləri = 1 | 1.246 | 0.000 | 0.026 | Rədd edilib |
| Emal sənayesi: kapital elastikliyi = amil payı 0.56 | 0.241 | 0.029 | 0.120 | **Rədd edilib** |
| İnvestisiyanın kredit elastikliyi = regional panel qiyməti 0.134 | −0.135 | 0.028 | — | **Rədd edilib** (kredit termini çıxarılıb) |
| <!-- AUTO:fr1v236_e3hom -->Ev təsərrüfatlarının gəliri: qeyri-neft ÜDM + pensiya fondu + əmək haqqı fondu elastiklikləri = 1 | 0.342 | 0.001 | 0.132 | **Rədd edilib** — nəzəri əsaslarla qoyulub (v2.3)<!-- /AUTO:fr1v236_e3hom --> |
| <!-- AUTO:fr1v236_socdefl -->Sosial xidmətlərin deflyatoru: ötürülmə əmsalı 1 (dreyf sərbəst) | 0.59 | 0.222 | — | Rədd edilməyib — qoyulub (dreyfsiz birgə test rədd edilib, p = 0.001)<!-- /AUTO:fr1v236_socdefl --> |
| Qeyri-neft vergi elastikliyi (buoyancy) = 1 | 1.322 | 0.124 | 0.192 | Rədd edilməyib (aşağı güc) — qoyulub |
| Dövlət investisiyasının neft gəlirlərinə görə elastikliyi = 1 | 0.901 | 0.757 | 0.312 | Rədd edilməyib (aşağı güc) — qoyulub |

Bundan əlavə, bütün adambaşına tənliklərdə və işçi qüvvəsində iştirak tənliyində əhali üzrə vahid elastiklik qoyulur.

### 4.2 2-ci vasitə — paneldən aqreqata parametr ötürülməsi

İki mikropanel illik sıralardan xeyli çox informasiya daşıyır.

**Sənaye yarımsahələri paneli** (29 sahə × 2016–2025, 290 sətir; əlavə dəyər funksiyasında 27 sahədən 259 sahə-il). Driscoll–Kraay
standart xətaları ilə (1 gecikmə, t(9) paylanması əsasında statistik nəticə) ikitərəfli sabit effektlər **0,12** kapital elastikliyi
(wild cluster bootstrap p = 0,16) və **1,03** əmək elastikliyi (p = 0,001) verir. Müşahidə olunan **əməyin payı** 0,339 (median,
bütün sahələr, yalnız əmək haqqı — əvvəllər istifadə olunan göstərici), qeyri-karbohidrogen sahələr üzrə 0,361 və **işəgötürənin 22%-lik sosial sığorta ayırmaları
nəzərə alınmaqla qeyri-karbohidrogen sahələr üzrə 0,441** təşkil edir (aqreqat nisbət 0,375). Birinci göstərici iki səbəbdən aşağıya doğru sürüşmüşdü — o, işəgötürən
ayırmalarını nəzərə almırdı və əlavə dəyəri əsasən rentadan ibarət olan xam neft hasilatı və neft emalını (əməyin payı 3–4%) əhatə edirdi. İki qiymət bir-biri ilə uyğun gəlmir və bu uyğunsuzluq uğursuzluq deyil, informativdir: sahədaxili cəmi on illik
variasiya şəraitində əlavə dəyər məşğulluqla demək olar ki, birə-bir dəyişir (əməyin saxlanılması (labour hoarding); daimi inventar üsulu ilə
hesablanmış kapital ehtiyatında hələ də ilkin şərt üstünlük təşkil edir), buna görə panel *qısamüddətli* reaksiyanı identifikasiya edir.
Gəlir payı isə rəqabətli amil qiymətləri şəraitində *uzunmüddətli* texnologiyanı identifikasiya edir, Azərbaycan sənayesi isə kapitaltutumludur
(neft emalı, kimya, metallurgiya). Düzəldilmiş amil payı **α_K = 0,56, α_L = 0,44** verir. O, aqreqat emal sənayesi üçün *namizəd* məhdudiyyət
kimi istifadə olunur və orada **rədd edilir** (uzunmüddətli kapital elastikliyi 0,24, p = 0,029), buna görə emal sənayesinin kapital
elastikliyi sərbəst qiymətləndirilir. (Əvvəlki versiya “IMPOSED α_K = 0.66” yazırdı, lakin faktiki olaraq tənliyi sərbəst qiymətləndirirdi.)

**Regional panel** (14 iqtisadi rayon × 2021–2025, 70 müşahidə). T = 5 olduğundan statistik nəticə üçün 1 gecikməli və
t(4) paylanmalı Driscoll–Kraay, üstəgəl wild cluster bootstrap p-dəyərləri (klasterlər = illər, Webb altı nöqtəli çəkiləri) istifadə olunur. Buraxılışın kredit elastikliyi
**+0,134** (DK p < 0,001, wild p = 0,022; yalnız region effektləri ilə +0,422), sənaye buraxılışının **+0,682** (wild p = 0,016), kənd təsərrüfatı
buraxılışının **+0,430** (wild p = 0,027); tikintinin ümumi investisiyaya görə elastikliyi **+0,518** (wild p = 0,021). Panel
nümunədən kənar yoxlama kəsimindən sonra başlayır, buna görə bunların heç biri nümunədən kənar yoxlama modelinə daxil ola bilməz.

**Sübut deyil: regional ticarət tənliyi.** Regional ticarətin əlavə dəyəri **63 region-ildən 58-də pərakəndə ticarət dövriyyəsinin dəqiq 0,320
mislidir** — bu, mənbə tərəfindən aparılmış doldurmadır (imputasiya). Onun 1,009-a bərabər “elastikliyi” doldurma qaydasını təkrarlayır və onun
aqreqat ticarət tənliyini çarpaz təsdiqlədiyi barədə əvvəlki iddia geri götürülmüşdür.

**Ötürmə ilə bağlı xəbərdarlıq.** İkitərəfli sabit effektlər aqreqat effektlərdən təmizlənmiş *nisbi* (kəsişmə üzrə) elastiklikləri identifikasiya edir. Regional
vergi elastikliyi 0,30-dur, uzunmüddətli aqreqat elastiklik (buoyancy) isə 1,32-dir (sərbəst qiymətləndirmə), məhz ona görə ki, aqreqat elastiklik sabit effektlərin aradan qaldırdığı milli
birgə dəyişmə ilə müəyyən olunur. Yalnız kəsişmə və aqreqat səviyyələrində ağlabatan şəkildə invariant olan parametrlər
ötürülür. Bunların heç biri belə deyil: buraxılış-kredit elastikliyi aqreqat investisiya məlumatları ilə rədd edilir (HAC-F p = 0,028) və investisiya deyil,
buraxılış elastikliyidir, buna görə o, multiplikator eksperimentlərində yalnız işarələnmiş ekspert əlavəsi (judgemental overlay) kimi göstərilir;
vergi elastikliyi isə ötürülmür.

### 4.3 3-cü və 4-cü vasitələr — qənaətlilik (parsimony) və kointeqrasiya qiymətləndirməsi

Hər tənlikdə nəzəriyyə əsasında seçilmiş bir-üç izahedici dəyişən; onlar VIF və standartlaşdırılmış izahedici dəyişənlər matrisinin şərt ədədi ilə
yoxlanılır (üç tənlik yüksək kimi qeyd olunub: E2, D3, C4). Uzunmüddətli əlaqələrdə **Dinamik OLS (Stock–Watson)** istifadə olunur: səviyyə reqressiyası
*izahedici dəyişənlərin fərqlərinin* cari dəyəri və qabaqlayıcı/gecikmələri ilə genişləndirilir, beləliklə, asılı dəyişənin öz
gecikmələri heç vaxt daxil olmur. 15 tənlikdə DOLS ±1, 12 tənlikdə cari fərqlərlə DOLS, 3 tənlikdə statik OLS (stoxastik izahedici dəyişən yoxdur) istifadə olunur;
hər tənlik üzrə qiymətləndirici və qalıq sərbəstlik dərəcələri (df) `FR1_equation_audit.csv` faylında verilib. Səhv işarəli, statistik əhəmiyyətsiz uzunmüddətli hədlər
qiymətləndirmə daxilində tətbiq olunan qayda ilə çıxarılır (və nümunədən kənar yoxlamada kəsimdən əvvəlki məlumatlar üzərində yenidən tətbiq olunur); belə hədd qalmayıb.

**Kointeqrasiya əsasən təsdiqlənməyib.** Düzgün, qalıqlara əsaslanan (MacKinnon) p-dəyərləri ilə kointeqrasiya 5% səviyyəsində
30 səviyyə əlaqəsindən yalnız **2-də** (mədənçıxarma, qeyri-neft gəlirləri), 10% səviyyəsində isə **4-də** (neft gəlirləri və kredit faiz dərəcəsi əlavə olunmaqla) aşkarlanır. Qalan
26 əlaqə üçün t-statistikaları *təsviri* kimi işarələnir və 21 tənlikdə ən azı bir səviyyə əmsalı birinci fərqlərlə qiymətləndirilmiş eyni tənliyin 95%
intervalından kənarda yerləşir. Nəticələr: baza düzəliş əmsalları sabit saxlanılır (qalıqların sönməsinə dair sübut yoxdur) və sönmə üzrə həssaslıq təhlili aparılır;
dinamik nümunədən kənar yoxlama isə həlledici testdir.

### 4.4 Eyni zamanlılıq (simultaneity)

Kənarlaşdırılmış alətlər (excluded instruments) yalnız modeldə ekzogen olan dəyişənlərdir: Brent (cari və gecikmə ilə), neft və qaz hasilatı, əhali,
uçot dərəcəsi və minimum əmək haqqı. Trend (alət deyil, izahedici dəyişən) və dövlət investisiyası (F4 vasitəsilə endogen olan və özü
C6 və D2-də alətlə qiymətləndirilən) çıxarılmışdır. Modeldaxili endogen izahedici dəyişəni olan 20 tənliyin hər biri üçün Durbin–Wu–Hausman
testi (nəzarət funksiyası, HAC-F) aparılır. **Qayda:** 2SLS DOLS/OLS-i yalnız o halda əvəz edir ki, DWH 5% səviyyəsində rədd etsin, hər bir
birinci mərhələ F ≥ 10 olsun və Sargan rədd etməsin. DWH 2 tənlikdə rədd edir, Sargan 20 tənlikdən 14-də rədd edir və **heç bir tənlik bu
şərtlərə cavab vermir**; model nüvəsi üzrə 3SLS yalnız dayanıqlıq yoxlaması kimi təqdim olunur. 3SLS kovariasiyası yelpik qrafikləri üçün
istifadə olunmur (Bölmə 7.5).

## 5. Uğursuz spesifikasiyalar və onların əvəzinə görülən işlər

Bu bölmə ona görə mövcuddur ki, model yalnız açıqlanmış uğursuzluqları qədər etibarlıdır. Bunların hər biri sınaqdan keçirilmiş, sübutlar
əsasında rədd edilmiş və əvəz olunmuşdur — hamısı notebook-da rədd edilmiş nəticə göstərilməklə sənədləşdirilmişdir.

| Nə uğursuz oldu | Sübut | Model bunun əvəzinə nə edir |
|---|---|---|
| İnflyasiya tənliyində **buraxılış kəsiri (output gap)** | Dörd ölçü sınaqdan keçirilmişdir. Sərbəst qiymətləndirilmiş istehsal funksiyası *mənfi* əmək elastikliyi verir; panel amil payları qoyulduqda ildə −1.31% TFP artımı və sürüşən "kəsir" alınır; xətti determinist trend kəsiri statistik əhəmiyyətsizdir; seqmentləşdirilmiş trend kəsiri əhəmiyyətlidir, lakin məzənnə əmsalını mənfiyə çevirir, çünki onun qırılmaları devalvasiya ilə üst-üstə düşür. Proksi kimi real kredit artımı *mənfi* işarə ilə daxil olur. | Tələb təzyiqi termini yoxdur. İnflyasiya sırf xərc əlavəsidir (cost markup). Fəallıq inflyasiyaya hələ də endogen əmək haqları vasitəsilə ötürülür, lakin ayrıca buraxılış kəsiri effekti identifikasiya **edilmir** və model bunu açıq bildirir. |
| İnvestisiya tənliyində **kapitalın istifadə dəyəri (user cost)** | Dörd ölçünün hamısında işarəsi yanlışdır (real kredit faiz dərəcəsi, nominal, ÜDM deflyatoruna əsaslanan, hamarlanmış). Dövlət investisiyası ümumi investisiyanın 53%-ni təşkil edir (2025); 20 müşahidə və sabitlənmiş (peg) məzənnə şəraitində müstəqil variasiya çox azdır. | İstifadə dəyəri çıxarılmışdır. Kredit termini də buraxılmışdır: onun sərbəst qiyməti yanlış işarəlidir (−0.14), regional panel üzrə 0.134 isə rədd edilir (HAC-F p = 0.028). |
| **Ev təsərrüfatlarının gəlirinin büdcə sosial xərclərinə reqressiyası** | Dörd parametr üçün n = 7, sosial xərclərin işarəsi yanlışdır (−0.10); nümunədən kənar yoxlamada n = 2 (dəqiq uyğunlaşma). Əmək haqqı fondu + pensiya ödənişləri fondu ilə əvəzetmə homogenlik testindən keçmədi (cəm 0.62, p < 0.001) və statik həlldə istehlakı 23%-ə qədər aşağı proqnozlaşdırdı. | Qeyri-neft ÜDM + pensiya ödənişləri fondu (orta pensiya × ümumi əhali; iş kitabında pensiyaçıların sayı yoxdur), kəsimdən əvvəlki (pre-cut) sübutlar əsasında seçilmişdir; homogenlik rədd edilmir (p = 0.12, aşağı güc) və qoyulmuşdur. Statik istehlak xətaları indi 2016–18 (−12%-dən −14%-ə qədər) istisna olmaqla ±10% daxilindədir. Qoruyucu mexanizm qalıq sərbəstlik dərəcəsi (df) 5-dən az olan istənilən nümunədən kənar yoxlama reqressiyasını dayandırır. |
| İstehlak tənliyində **ex-post real faiz dərəcəsi** | Uzunmüddətli əmsal −0.019, birinci fərqlərdə isə −0.001; tərkibində cari inflyasiya olduğundan, 1 standart kənarlaşma həcmində inflyasiya şoku real istehlakı 14% artırırdı. | Çıxarılmışdır. |
| **Yanlış işarəli, statistik əhəmiyyətsiz uzunmüddətli terminlər** | Kənd təsərrüfatı kapitalı (−0.004), idxal tənliyində investisiya (−0.07), nəqliyyat tənliyində qeyri-neft ÜDM (−0.10). | Nümunədən kənar yoxlamada kəsimdən əvvəlki məlumatlar üzərində yenidən tətbiq olunan qayda ilə çıxarılmışdır. Yanlış işarəli heç bir uzunmüddətli əmsal qalmamışdır. |
| **Yanvar–aprel → tam il körpüsü** | Birləşdirilmiş meyl əmsalı 0.52 2021-ci ilin baza effektindən irəli gəlirdi (turizm −32.8%/+99.3%). 2022–25 üzrə Huber körpüsü (meyl 0.68) 1:1 uyğunluğu üstələmir: HLN-DM birtərəfli p = 0.126. | 1:1 uyğunluq. |
| **Qeyri-neft ÜDM tənliyində kredit** | Depozitlərlə yanaşı yanlış işarə (−0.67). | Çıxarılmışdır. |
| **Qoyulmuş vahid/CRS məhdudiyyətləri** | Ticarətdə vahid elastiklik, mədənçıxarmada CRS və emal sənayesində α_K DOLS + HAC-F altında rədd edilir. | Sərbəst saxlanılmışdır. |
| **Regional ticarət üzrə çarpaz yoxlama** | Doldurma (interpolyasiya) artefaktı (63 region-ildən 58-də 0.320 × pərakəndə ticarət). | Sübut kimi geri götürülmüşdür. |
| Bazar faiz dərəcələrinə **uçot dərəcəsinin ötürülməsi** | İşarəsi yanlışdır. 2016–17-ci illərdə uçot dərəcəsi müdafiə məqsədilə 15%-ə qaldırıldığı halda kredit faiz dərəcələri *azalırdı* (2010-cu ildə 20.7% → 2016-cı ildə 16.4%): bu nümunə üzrə o, idarəedici dərəcə deyil, böhran alətidir. | Kredit faiz dərəcəsi **depozit faiz dərəcəsinə** reqressiya olunur (uzunmüddətli ötürülmə əmsalı 1.40), üstəgəl problemli kreditlər (NPL) üzrə risk mükafatı; depozit faiz dərəcəsi ssenari dəyişənidir. Uçot dərəcəsi kreditin **həcminə** təsir edir və orada işarəsi düzgündür (−0.043). |
| **Səviyyələrdə əmək tələbi** | VIF 20-dən yuxarıdır; ekstrapolyasiya edildikdə birinci proqnoz ilində işsizliyi bir faiz bəndindən çox dəyişdirirdi. | Okun tipli **məşğulluq səviyyəsi** əlaqəsi: `ln(emp/lf)` adambaşına qeyri-neft ÜDM-ə reqressiya olunur, uzunmüddətli elastiklik 0.034, tək izahedici dəyişən. Ölçülmüş işsizlik 2010-cu ildən bəri, 2020-ci il istisna olmaqla, hər il 4.9–5.6% olmuşdur. |
| **Sərbəst işçi qüvvəsi tənliyi** | Əhali üzrə elastiklik ildə 1.1%-lik trendlə birlikdə 0.05-ə qədər çökür (VIF > 100), bu da işsizliyin 3 faiz bəndi yuxarı sürüşməsini nəzərdə tutur. | Vahid əhali elastikliyi qoyulmuşdur; yalnız iştirak səviyyəsinin sürüşməsi qiymətləndirilir (ildə +0.045%). İştirak səviyyəsi faktiki olaraq sabitdir: 2010-cu ildə 51.35%, 2025-ci ildə 52.56%. |
| **Nisbi qiymət olmadan idxal tənliyi** | İnvestisiya əmsalı *mənfidir* — kapital mallarının demək olar ki, hamısının idxal olunduğu şəraitdə bu mümkün deyil. 2015–16-cı illərin devalvasiyası idxalı sıxışdırdı, investisiya isə dəyişməkdə davam edirdi. | Real məzənnə termini əlavə edilmişdir. O, işarəni yalnız statik OLS-də bərpa edir; uzunmüddətli DOLS qiymətləndirməsində investisiya əmsalı yanlış işarəli və statistik əhəmiyyətsizdir, buna görə də çıxarılmışdır: idxal istehlakdan və nisbi qiymətdən asılıdır (v2.3: idxal həcmi formasında qiymətləndirilir, orada onun elastikliyi müsbətdir — v2.3 qeydinə bax). |
| **Karbohidrogen ixracı dəyərinin reqressiya kimi modelləşdirilməsi** | Neft gəlirləri üzrə 1.285 elastiklik — bu mümkün deyil, çünki dəyər *məhz* həcm × qiymətdir. Vahid xətası: həcm tonla, qiymət isə bir barel üçün. | Bərpa edilmiş 7.400 barel/ton çevirmə əmsalı (dəqiq) və tədiyə balansı göstəricisinə nisbətən kalibrlənmiş 1.002 nisbəti (2021–25) ilə **eynilik** vasitəsilə əvəz edilmişdir. |
| **Dövlət investisiyası üçün mexaniki resurs qaydası** | Qiymətləndirilmiş vahid elastikliyin neftin azalan trayektoriyası şəraitində tətbiqi 2030-cu ilədək real dövlət investisiyasını ~30% azaldır və ÜDM-in ~3%-i həcmində profisit yaradır — bu, neytral baza trayektoriyası deyil, prosiklik qənaət siyasətinin proyeksiyasıdır və suveren sərvət fonduna malik ölkənin edəcəyi addım deyil. | Dövlət investisiyası **siyasət səviyyəsi** kimi müəyyən edilir (hər ssenaridə açıq şəkildə göstərilir), neft gəlirlərinin ssenarinin öz istinad trayektoriyasından *kənarlaşmaları* isə onu qiymətləndirilmiş elastikliklə dəyişdirir — beləliklə, neftin ötürülmə kanalı multiplikator təcrübələrində tam gücü ilə işləyir. |

Hazırlanma zamanı aşkar edilmiş həllediciyə aid beş xəta da sənədləşdirilmişdir, çünki onların hər biri inandırıcı görünən, lakin
yanlış proqnozlar verirdi:

1. **Baza düzəliş əmsallarının sönümləndirilməsi** saxta artım dalğalanması yaradırdı (real ÜDM-də əvvəlcə +18%, sonra −18%). Baza
   düzəlişləri sabit saxlanılır (qalıqların stasionar olduğu göstərilməmişdir); yalnız 2026-cı ilin natamam il məlumatlarına əsaslanan lövbər əlavəsi (increment) sönür.
2. **Bütün sistemi dəqiq təkrarlayan düzəlişlərin həll yolu ilə tapılması** yığılmırdı (divergensiya), çünki eyni zamanlı əks əlaqə hər
   addımı gücləndirir. Qalıqların tək irəli keçiddən götürülməsi **ikiqat hesablamaya** gətirirdi, çünki işçi qüvvəsi üzərində
   multiplikativ şəkildə müəyyən edilən məşğulluq həmin dəyişənin xətasını da özünə hopdururdu. Hər tənliyin **öz qalığı** hər iki problemin qarşısını alır.
3. **Şok hesablamalarının yenidən lövbərlənməsi** lövbərlənmiş dəyişənləri müşahidə olunan 2026 hədəflərinə geri qayıtmağa məcbur edir və
   beləliklə şoku ləğv edirdi, nəticədə fiskal multiplikator həddindən artıq kiçik görünürdü. Şok hesablamaları Əsas ssenarinin düzəlişlərindən təkrar istifadə edir.
4. **Üç tənlik öz sabit düzəlişini xəbərdarlıq olmadan buraxırdı** (ev təsərrüfatlarına kreditlər, depozitlər, karbohidrogen ixracı), bu da
   birinci proqnoz ilində səviyyədə 20%-lik kəsilmə (sıçrayış) yaradırdı. İndi avtomatlaşdırılmış özünüyoxlama tam əhatəni təsdiqləyir.
5. **Kompozit aqreqatlar proqnoz real trayektoriyasını itirirdi**, çünki birinci proqnoz ilində əvvəlki ilin zəncir çəkiləri yox idi.
   İndi zəncir son faktiki ildən başlayır.

---

## 6. Validasiya

### 6.1 Qiymətləndiricilərin düzgünlüyü

Bu mühitdə `linearmodels` mövcud olmadığından OLS/HAC, 2SLS, 3SLS, SUR, DOLS və Driscoll–Kraay xətaları ilə panel FE birbaşa
reallaşdırılmış və **`statsmodels` ilə maşın dəqiqliyinə qədər yoxlanılmışdır** (əmsallar və standart xətalar, HC1 və kiçik nümunə üçün
Newey–West HAC, 2SLS, dəqiq identifikasiya olunmuş halda 3SLS-in 2SLS-ə bərabərliyi, panel within-çevrilməsi və
`statsmodels.tsa.stattools.coint` ilə müqayisədə qalıqlara əsaslanan kointeqrasiya p-dəyəri).

### 6.2 Dinamik ex-post nümunədən kənar yoxlama (hold-out), 2021–2025 — qəti test

Hər şey **yalnız 2020-ci ilədək olan məlumatlar əsasında** yenidən qurulur: bütün əmsallar (eyni qurucu funksiyalar və DOLS qaydası; ən
kiçik qalıq df 7-dir, qoruyucu mexanizm df 5-dən aşağı olan istənilən reqressiyanı dayandırır), hər bir məhdudiyyət və yanlış işarə qərarı,
DWH qiymətləndirici qaydası, emal sənayesi üzrə α_K testi (amil payı 2016–2020 panel illərindən) və hər bir kalibrlənmiş pay və nisbət.
Regional panel 2021-ci ildən başlayır və heç istifadə olunmur. Sistem 2021–2025 üçün yalnız faktiki *ekzogen* trayektoriyalarla **dinamik
şəkildə** həll edilir; **dövlət investisiyası endogendir və F4-ə uyğun dəyişir** (faktiki dövlət investisiyasını daxil edən siyasət səviyyəsi
variantı ayrıca təqdim olunur); pensiyalar İQİ-yə indeksləşmə üstəgəl onların faktiki real artımı ilə müəyyən olunur. Əmsalların işarələri
30 səviyyə tənliyindən 28-də 2021-ci ilədək olan nümunə ilə tam nümunə arasında üst-üstə düşür (işarəsi dəyişənlər: C3, G3). DM testləri
h = 3 ilə HLN düzəlişindən istifadə edir (xətalar bir trayektoriyanın 1–5 addımlıq xətalarıdır; beş müşahidə ilə düzəliş yalnız h = 3-ə
qədər müəyyəndir) və yalnız göstərici xarakter daşıyır.

<!-- AUTO:v22_holdout -->
| | Nəticə (14 dəyişən) |
|---|---|
| 2020-ci ildən (pandemiyanın dib nöqtəsi) təsadüfi gəzişməni üstələyir | 14-dən 14-ü, median U **0.59** |
| 2019-cu ildən təsadüfi gəzişməni üstələyir | 14-dən 11-i, median U 0.58 |
| 2010–2019 sabit artımını üstələyir (pandemiyadan əvvəl) | **14-dən 6-sı, median U 1.04** |
| 2010–2020 sabit artımını üstələyir | 14-dən 8-i, median U 0.95 |
| Statistik əhəmiyyətli üstünlüklər (HLN-DM p < 0.10) | RW2020 ilə müqayisədə 2; 2010–19 sabit artımı ilə müqayisədə 1 |
| 5 ildən sonra real ÜDM səviyyəsinin xətası | **−11.4%** (RW2020 ilə müqayisədə U 0.71, CG 2010–19 ilə müqayisədə 1.10) |
| 5 ildən sonra real qeyri-neft ÜDM səviyyəsinin xətası | −10.6% (RW2020 ilə müqayisədə U 0.47, CG 2010–19 ilə müqayisədə 1.39) |
| Siyasət səviyyəsi variantı | RW2020 ilə müqayisədə median U 0.54, CG 2010–19 ilə müqayisədə 0.90 |

*(v2.2 rəqəmləri: mədənçıxarma deflyatoru karbohidrogen ixrac qiymətləri indeksi üzrə — v2.2 qeydinə bax. Onun öz xətası 27,3%-dən
6,8%-ə, nominal ÜDM-in xətası 25,6%-dən 19,1%-ə enir, real ÜDM-inki isə 7,3%-dən 8,5%-ə qalxır: 2021–22-nin daha dəqiq mədənçıxarma
qiymətləri həcmi azalan mədənçıxarmaya zəncirvari çəkidə daha böyük pay verir.)*
<!-- /AUTO:v22_holdout -->

<!-- AUTO:v22_headline62 -->
**Əsas nəticə:** 2020-ci ildən təsadüfi gəzişmə modeli olduğundan yaxşı göstərir (2020-ci il pandemiyanın dib nöqtəsi idi). Pandemiyadan
əvvəlki onillik üzrə qiymətləndirilmiş sabit artımla müqayisədə model təxminən **eyni səviyyədədir** (median U 1,04; 1 statistik əhəmiyyətli
üstünlük). Yaxşı izlənilənlər: istehlak (RMSE 1,1%), ticarət 2,4%, məşğulluq 3,0%, kənd təsərrüfatı 4,3%, real ÜDM 8,3%. Zəif izlənilənlər:
tikinti 21,0%, nəqliyyat 17,6%, emal sənayesi 14,5%, dövlət investisiyası 17,9%, İKT 25,7% (v2.1: kəsim ili olan 2020 İKT investisiyasının dib nöqtəsi idi) — 2020-ci ildən sonra transformasiyaya uğramış sektorlar
(yeni emal sənayesi gücləri, Qarabağ və Şərqi Zəngəzurun bərpası, Orta Dəhliz). Real cari xərclər 2025-ci ilədək 33% yüksək proqnozlaşdırılır.
<!-- /AUTO:v22_headline62 -->

### 6.3 Digər yoxlamalar

Hər tənlik üzrə: işarə və böyüklüyün nəzəriyyə ilə müqayisəsi; kiçik nümunə üçün HAC əhəmiyyətliliyi; qalıqlara əsaslanan kointeqrasiya;
birinci fərqlərlə çarpaz yoxlama; heteroskedastiklik; normallıq; VIF və şərtilik ədədi (condition number); və yekun spesifikasiyalar üzrə
2015, 2020 və 2022-ci illərdə Chow testləri (yoxlanılan əmsal dəstlərindən **20-dən 10-u** qeyri-stabillik göstərir). Sistem səviyyəsində:
eyniliklərin qapanması, həll edilən hər il üçün yığılma (konvergensiya) və statik həll yoxlaması (orta |real ÜDM xətası| 1,7%; istehlak
2016–19 istisna olmaqla ±10% daxilində).

---

## 7. Həll, lövbərləmə və proqnozlaşdırma

### 7.1 Həlledici

Hər il tərpənməz nöqtəyə qədər **sönümləndirilmiş Gauss–Seidel** iterasiyası ilə həll edilir (qalıq < 1e-10; hər proqnoz ili üçün <!-- AUTO:v23_solver -->57–78
iterasiya, nümunədən kənar yoxlamada 52–57<!-- /AUTO:v23_solver -->), eyniliklər isə hər iterasiyada dəqiq şəkildə qoyulur.

### 7.2 2026-cı ilin müşahidə olunan məlumatlara lövbərlənməsi

<!-- AUTO:v23_anchor -->
2026-cı il üzrə dörd aylıq müşahidə mövcuddur. ÜDM-in on iki komponentinin hamısı üzrə ilin əvvəlindən hesablanmış real artım indeksləri
dərc olunmuşdur. Yanvar–aprel artımından tam il artımına dayanıqlı (Huber) proporsional körpü 2022–2025 üzrə qiymətləndirilmişdir (2021
istisna edilib: onun yanvar–aprel artımı 2020-ci ilin baza effektidir); onun meyl əmsalı 0,68, çarpaz yoxlanılmış RMSE-si isə 1:1 uyğunluq
üçün 6,4 f.b.-yə qarşı 3,9 f.b.-dir, lakin HLN düzəlişli Diebold–Mariano testində (birtərəfli p = 0,126) 1:1 uyğunluğu
**üstələmir**, buna görə də **1:1 uyğunluq** istifadə olunur. Hər komponentin nəzərdə tutulan tam il səviyyəsi düzəliş əmsalı
əlavələri (increments) vasitəsilə çatılan lövbərləmə hədəfidir; **əlavələr 2026-cı ildə tam tətbiq olunur və hər il yarıbayarı azalır**
(2030-cu ildə 1/16 hissəsi qalır). Ən böyüyü tikinti komponentinə aiddir (−0,210 loqarifmik bənd,
yanvar–aprel artımının −19% olmasından irəli gəlir).
<!-- /AUTO:v23_anchor -->

**2026→2027 mişar dişi effekti (sawtooth).** Tikinti lövbəri bir illik yarımsönmə dövrü ilə aradan qalxdığından, tikinti <!-- AUTO:v22_sawtooth -->−19,0% (2026) →
+12,1% (2027) → +6,4% (2028) dinamikası göstərir; qeyri-neft ÜDM +0,66% → +4,81% → +4,31%<!-- /AUTO:v22_sawtooth --> (v2.3), yəni 2027-ci il qeyri-neft göstəricisinin
təxminən 1 f.b.-si lövbərin aradan qalxmasının nəticəsidir. Kənd təsərrüfatı (<!-- AUTO:v23_agr -->+2,0% → +4,8%<!-- /AUTO:v23_agr -->,
ikincisi onun qiymətləndirilmiş trendidir) lövbərdən qaynaqlanan mişar dişi effekti göstərmir; informasiya və rabitə (ICT) (<!-- AUTO:v22_sawtooth_ict -->+9,0% → +6,3%<!-- /AUTO:v22_sawtooth_ict -->) isə v2.1-dən göstərir: <!-- AUTO:v23_ict -->yanvar–aprel lövbəri 2026-cı ildə 1,7 f.b. əlavə edir, 2027-ci ildə 0,9 f.b. geri alır, adambaşına İKT kapitalı isə 2025-ci ilin investisiya payı ilə artıq artmır (2027-ci ildə −0,1 f.b.<!-- /AUTO:v23_ict -->, `FR1_sector_decomposition_all.csv`).

<!-- AUTO:v23_jantable -->
| | Dərc olunmuş yanvar–aprel | Model 2026 (tam il) | Fərq |
|---|---|---|---|
| Real ÜDM artımı | +0,20% | +0,24% | +0,04 f.b. |
| Real qeyri-neft ÜDM artımı | +0,70% | +0,66% | −0,04 f.b. |
<!-- /AUTO:v23_jantable -->

İstifadəçiyə iki məlumat ziddiyyəti çatdırılır: ümumi investisiya 15% artdığı halda tikintinin 19% azalması və I rübdə həm ixracın, həm də
idxalın kəskin enməsi.

### 7.3 Ssenarilər

Karbohidrogenlər ekzogen olduğundan, proqnoz öz quruluşuna görə ssenaridən asılıdır — bu xüsusiyyət fərziyyələri açıq şəkildə ifadə etməyə
məcbur edir. 2025-ci ilin başlanğıc nöqtəsinə əsasən kalibrlənmişdir (Brent 69,1, neft 27,68 mln ton, qaz 50,92 mlrd kub metr, məzənnə 1,70,
uçot dərəcəsi 6,75%). Bütün ssenarilər üçün ümumi: əhali ildə +0,483% (hesablanmış), neft sektoruna investisiya neft hasilatı
trayektoriyası ilə birlikdə dəyişir (mürəkkəb artımla), <!-- AUTO:fr1v236_pens -->pensiyalar 2026-cı ildə qərar verilmiş indeksasiya ilə (+9,3%, Prezidentin Sərəncamı; `data/dsmf_pension/pension_indexation.csv`), 2027-ci ildən İQİ-yə indeksləşdirilir<!-- /AUTO:fr1v236_pens -->, <!-- AUTO:fr1v236_mw -->minimum əmək haqqı 2026-cı ildə qanuni 400 manat, sonra ildə +6% (Mənfi ssenaridə +3%, İslahatda +9%; `data/dsk_minwage/minwage_path.json`, FR3 ilə eyni yol)<!-- /AUTO:fr1v236_mw -->; v2.2: 2026-cı ilin neft və qaz hasilatı hər ssenaridə yanvar–mart
faktiki göstəricisindən, 2026-cı ilin dövlət investisiyası isə <!-- AUTO:v22_sip -->təsdiq edilmiş Dövlət İnvestisiya Proqramına (2 700 mln AZN, `DİP 2016-2026`)<!-- /AUTO:v22_sip --> ankorlanır.

<!-- AUTO:v22_scenarios -->
| Amil | Əsas | Mənfi | İslahat |
|---|---|---|---|
| 2030-cu ilədək Brent | ~66 USD/barel | ~48 | ~80 |
| Neft hasilatı 2027–30 (v2.2) | Nazirliyin planının artımı: −2.1, −1.8, +3.0, −0.4% | v2.2-dən əvvəlki Əsas ssenarinin azalması: −4.2, −3.8, −3.5, −3.0% | plan + 1.2, 0.8, 0.5, 0 f.b. |
| Qaz hasilatı 2027–30 (v2.2) | Nazirliyin planının artımı: −1.1, −4.7, +5.2, 0.0% | plan − 1 f.b. | plan + 3 f.b. |
| Dövlət İnvestisiya Proqramı 2026 | 2 700 mln AZN (təsdiq edilmiş) | eyni | eyni |
| Qazın ixrac qiyməti | → 300 USD/min kub metr | 230 | 380 |
| Dövlət investisiyası (siyasət səviyyəsi, real) | illik +1.5% | illik −4% | illik +5% |
| Uçot / depozit faiz dərəcəsi | yumşalma | sərtləşmə | yumşalma |
| Məzənnə | 1.70 | 1.70 | 1.70 |
| Xarici tələb | illik +3% | illik +0.5% | illik +5% |
| Qeyri-neft TFP | trend | trend | 2027-ci ildən etibarən TFP/trend termini olan hər sektor üzrə ildə +0.4 loqarifmik bənd (agr, man, elc, wat, tou, tra, ict, oth) — indi həlledici tərəfindən faktiki olaraq tətbiq olunur |
<!-- /AUTO:v22_scenarios -->

### 7.4 Əsas nəticələr

<!-- AUTO:v22_results -->
| | Əsas | Mənfi | İslahat |
|---|---|---|---|
| Real ÜDM artımı, orta illik %, 2026–30 | **2.57** (cari icra; əvvəlki versiyalar: v2.2 2.90, v2.1 2.40, v2 (2026-10-05) 2.56; birinci raund 1.34; ilkin versiya 1.23) | 1.32 | 3.62 |
| Real qeyri-neft ÜDM artımı, orta illik % | **3.76** (cari icra; əvvəlki versiyalar: v2.2 4.20, v2.1 3.99, v2 (2026-10-05) 4.18; birinci raund 2.68; ilkin versiya 2.35) | 2.54 | 4.91 |
| İQİ inflyasiyası 2030, % | 4.58 | 3.86 | 5.34 |
| İşsizlik 2030, % | 4.67 | 4.86 | 4.49 |
| Büdcə balansı 2030, ÜDM-ə nisbətən % | +0.01 | +0.98 | −0.39 |
| Dövlət borcu 2030, ÜDM-ə nisbətən % | 12.3 | 12.9 | 11.5 |
| Əlavə dəyərdə karbohidrogenlərin payı 2030, % | 16.7 | 12.2 | 19.8 |
| Nominal ÜDM 2030, mlrd AZN | 188 | 163 | 212 |
| Qeyri-neft büdcə balansı 2030, qeyri-neft ÜDM-ə nisbətən % (v2.2) | −11.3 | −8.4 | −13.1 |
<!-- /AUTO:v22_results -->

<!-- AUTO:v22_path -->
Əsas ssenari trayektoriyası, artım %-lə (v2.3):

| | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| Real ÜDM | 0.24 | 2.55 | 2.47 | 4.37 | 3.25 |
| Real qeyri-neft ÜDM | 0.66 | 4.81 | 4.31 | 4.78 | 4.28 |
| İstehlak | 4.60 | 1.83 | 2.79 | 3.89 | 3.77 |
| Emal sənayesi | 6.20 | 6.05 | 6.20 | 6.75 | 6.53 |
| Kənd təsərrüfatı | 2.00 | 4.75 | 4.29 | 4.06 | 3.94 |
| Tikinti | −19.00 | 12.07 | 6.39 | 5.27 | 2.74 |
| İnformasiya və rabitə (ICT) | 9.00 | 6.35 | 6.90 | 7.34 | 7.55 |
<!-- /AUTO:v22_path -->

**Nəticələr niyə birinci yenidənbaxmadakından yüksəkdir.** Yenidən spesifikasiya edilmiş ev təsərrüfatlarının gəliri tənliyi gəliri
qeyri-neft ÜDM-ə bağlayır (pay əlaqəsi), buna görə də qeyri-neft ÜDM → gəlir → istehlak → ticarət, vergilər və xidmətlər → qeyri-neft ÜDM
tələb dövrəsi daha güclüdür; istehlak indi <!-- AUTO:v22_whycons -->ildə 1,8–4,6% artır<!-- /AUTO:v22_whycons --> (tarixən təxminən 5%), halbuki birinci yenidənbaxmanın əmək haqqı fonduna
əsaslanan versiyası 0,1–2,4% verir və nümunədaxili istehlakı 23%-ə qədər aşağı proqnozlaşdırırdı. İlin əvvəlindən (YTD) məlumatların 1:1
uyğunluğu, nəqliyyat tənliyindəki tranzit termini və deflyator vahidləri üzrə düzəliş də töhfə verir. <!-- AUTO:v22_whynonoil -->İldə 3,8% (v2.3)<!-- /AUTO:v22_whynonoil --> qeyri-neft artımı 2021–25
diapazonu (2,7–9,1%) daxilindədir, lakin 2015–25 ortalamasından (təxminən 3%) yüksəkdir.

**Açıqlanan inandırıcılıq xəbərdarlıqları.** *Emal sənayesi* <!-- AUTO:v22_man -->ildə ~6,3% artır (v2.3<!-- /AUTO:v22_man -->; v2.1-dən əvvəlki 3 illik investisiya payları ilə 6,9%): istehsal gücü üstəgəl ildə +3% xarici tələbə tətbiq edilən
ixrac ↔ emal sənayesi dövrəsi (C3 ixrac elastikliyi 0,71 × D3 emal sənayesi elastikliyi 0,35; dövrə gücləndirmə əmsalı 0,25). Son dövrün
tarixi müqayisə ediləndir (2021–25-də ildə ≈8%), lakin <!-- AUTO:v22_manrmse -->emal sənayesi üçün nümunədən kənar yoxlama RMSE-si 14,5%-dir<!-- /AUTO:v22_manrmse -->; kəsimdən əvvəlki heç
bir sübut fərqli spesifikasiyanı dəstəkləmir (hər bir namizəd kəsimdən əvvəlki məlumatlar üzrə işarə yoxlamasından keçmir). *Kənd təsərrüfatı*
ildə ~4,2% artır, bunun 90%-i qiymətləndirilmiş determinist trenddir, son illərdə isə bu göstərici 0,9–3,4% olmuşdur; 2015-ci ildə trend
qırılması kəsimdən əvvəlki məlumatlar üzrə yoxlanılmış və statistik əhəmiyyətli olmamışdır (p = 0,52), buna görə də heç bir qırılma qoyulmur.
Nəqliyyatda <!-- AUTO:v22_trend -->(102%), informasiya və rabitədə (98%; v2.3), kənd təsərrüfatında (90%) və elektrik enerjisində (65%)<!-- /AUTO:v22_trend --> 2027–2030-cu illər artımının
yarıdan çoxu determinist trenddir — bu trayektoriyalar yalnız tarixi trendin davam edəcəyi fərziyyəsi qədər etibarlıdır.

**Düzəliş əmsallarına həssaslıq:** baza düzəliş əmsalları sabit saxlanılmaq əvəzinə sabit, qiymətləndirilməyən yarımparçalanma
müddəti ilə sönərsə (v2.3; qalıq avtokorrelyasiyası qiymətləndirilmir), orta artım
daha aşağı olur — <!-- AUTO:v22_addfactor -->real ÜDM 2,31% (Əsas), 1,12% (Mənfi), 3,33% (İslahat); qeyri-neft 3,51%, 2,35%, 4,62% (v2.3, yarımparçalanma müddəti 1 il; sabit düzəliş əmsalları ilə: 2,57% və 3,76%)<!-- /AUTO:v22_addfactor --> (v2: hər həssaslıq hesablaması indi öz neft gəlirləri istinad trayektoriyasını qurur).

**Ən aydın struktur nəticə:** Əsas ssenaridə əlavə dəyərdə karbohidrogenlərin payı <!-- AUTO:v22_hcshare -->25,6%-dən 16,7%-ə düşür (v2.2: Nazirliyin hasilat planı; v2.1-də 14,5%)<!-- /AUTO:v22_hcshare -->, çünki neft həcmləri azalır,
qeyri-neft sektorları isə artır.

### 7.5 Qeyri-müəyyənlik

<!-- AUTO:v23_fan -->
Əsas ssenari üzrə 500 təkrarlama aşağıdakıları birləşdirir: (1) **qalıq trayektoriyalarının tarixi təkrar seçimi (resampling)** — başlanğıc
ili s (2010–2020) çəkilir və bütün 29 davranış qalığının birgə kənarlaşmaları u_{s+h} − u_s (h = 1…5) sabit düzəliş əmsallarına əlavə olunur;
qalıq dinamikası üzrə heç nə qiymətləndirilmir; trayektoriyalar mərkəzləşdirilir və hər iki işarə ilə istifadə olunur (antitetik); (2) log
Brent, neft və qaz hasilatı üçün eyni beşillik tarix, **eyni başlanğıc ili ilə**; (3) N(β̂, V̂_HAC)-dan antitetik, işarəni qoruyan parametr
çəkilişləri (əmsal çəkilişlərinin 21,1%-i işarə dəyişməsinə görə rədd edilmişdir), baza düzəliş əmsalları isə 2025-ci ili təkrarlamaq üçün
yenidən hesablanır. 2026 kənarlaşmaları 0,84 (yanvar–aprel məlum olduqdan sonra qalan tam il qeyri-müəyyənliyi), ekzogen amillər üçün isə
2/3 ilə miqyaslanır.

**Diaqnostika.** 500 etibarlı təkrarlama (58,4%) əldə etmək üçün 856 təkrarlamaya (428 antitetik cüt) cəhd edilmişdir. Kənarlaşdırılmışdır:
194-ü bir illik dəyişikliyin Əsas ssenarinin müvafiq dəyişikliyindən 0,3 loqarifmik bənddən çox fərqlənməsinə görə (və ya, daha böyük olduğu
hallarda, dəyişənin 2000–2025-ci illərdə etdiyi ən böyük dəyişikliyin 1,5 mislindən çox — məsələn, turizm, dövlət investisiyası, neftlə bağlı
qiymətlər), 7-si sonlu olmayan qiymətlərə görə, 0-ı partlayıcı dinamikaya görə, 1-i yığılmamağa görə (uğursuz üzv öz antitetik
cütünü də kənarlaşdırır). Buna görə də bu filtr quyruqları müəyyən qədər kəsir. İxrac edilmiş çəkilişlərdə |Δlog| > 0,3 olan çəkiliş-illərin payı
real ÜDM üçün 0,0%, qeyri-neft ÜDM üçün 0,0%, İQİ üçün 0,0%, məşğulluq üçün 0,0%, istehlak üçün 0,2%, real cari xərclər
üçün 10,0% və qeyri-neft investisiyası üçün 18%-dir (onun öz tarixində dəyişikliklər daha böyükdür).

**Mərkəzləşdirmə.** Şoklar və parametr kənarlaşmaları simmetrikdir, lakin aqreqatlar log-normal şoklara məruz qalan hissələrin hesabi
cəmləridir (zəncirvari ÜDM, neft + qeyri-neft büdcə gəlirləri, gəlir dövrəsi), buna görə də xam median Əsas ssenaridən yuxarıda yerləşir:
2030-cu ilədək +1,6% (real ÜDM), +2,4% (qeyri-neft), +3,1% (istehlak), +1,6% (gəlir), +6,2% (cari xərclər), +5,6% (büdcə gəlirləri). Daha sonra ixrac edilmiş çəkilişlər Əsas ssenari üzrə mərkəzləşdirilir (səviyyələr üçün multiplikativ, dərəcələr üçün
additiv şəkildə): median hər il dərc edilmiş Əsas ssenariyə bərabərdir (maksimal fərq 1e−13), səpələnmə dəyişmir; dəyişənlərarası eyniliklər
yalnız bu sürüşmələr dəqiqliyi ilə ödənilir.
<!-- /AUTO:v23_fan -->

<!-- AUTO:v22_bands -->
| 2030, Əsas | 5–95% zolağı (medianın %-i) | 25–75% | nümunədən kənar yoxlamanın 5 illik xətası |
|---|---|---|---|
| Real ÜDM | 19.5 | 7.8 | −11.4% |
| Real qeyri-neft ÜDM | 25.3 | 10.3 | −10.6% |
| İQİ səviyyəsi | 52.6 | 31.3 | −30.7% |
| Məşğulluq | 8.9 | 4.2 | −4.2% |
| Real sərəncamda qalan gəlir | 42.9 | 15.1 | +10.5% |
| Real istehlak | 58.7 | 25.7 | +0.7% |
| Real cari xərclər | 67.8 | 27.5 | +32.5% |
<!-- /AUTO:v22_bands -->

Zolaqlar istehlak istisna olmaqla modelin 2021–25 üzrə öz xətaları ilə eyni tərtibdədir (istehlak zolağı gəlir dövrəsi səbəbindən onun kiçik
nümunədən kənar yoxlama xətasından xeyli genişdir). **Artım və İQİ zolaqları** — real ÜDM artımı üçün p5–p95 <!-- AUTO:v22_growthband -->ildə təxminən −4%-dən +14%-ə
qədər, İQİ inflyasiyası üçün təxminən −5%-dən +16%-ə qədər<!-- /AUTO:v22_growthband --> — 2015–16 devalvasiyasını, 2020 pandemiyasını və 2021–22 inflyasiya epizodunu
*hər iki işarə ilə* təkrarlayır: İQİ-nin yuxarı quyruğu 2016 devalvasiyasıdır (15,7%), deflyasiya xarakterli aşağı quyruq isə həmin
epizodların güzgü əksidir və sabitlənmiş məzənnə (peg) rejimi şəraitində tarixi presedenti yoxdur — onu asimmetrik tarixin simmetrik təkrar
seçiminin artefaktı kimi oxumaq lazımdır.

### 7.6 Multiplikatorlar — sektorlararası ötürülmə üzrə FR1 cavabı

Hər təcrübə **həll edilmiş** sistemdə bir ekzogen amilə şok verir və Əsas ssenarinin düzəliş əmsalı trayektoriyalarından təkrar istifadə edir.
2030-cu ilədək Əsas ssenaridən kənarlaşmalar, faizlə (`FR1_multipliers.csv`):

<!-- AUTO:v22_multipliers -->
| | Brent +10 USD/barel | Dövlət investisiyası +1 mlrd AZN | Kredit şərtlərinin yumşaldılması (qiymətləndirilmiş) | Kredit şərtlərinin yumşaldılması + ekspert mülahizəsinə əsaslanan əlavə (overlay) | Xarici tələb +10% |
|---|---|---|---|---|---|
| Tikinti | +1.72 | +5.60 | +0.02 | +1.32 | +0.12 |
| Emal sənayesi | +0.62 | +2.07 | +0.00 | +0.40 | +9.46 |
| Ticarət | +0.35 | +1.12 | +0.85 | +1.08 | +1.36 |
| İnformasiya və rabitə (ICT) | +1.00 | +3.52 | −0.01 | +0.36 | −0.02 |
| Real ÜDM (zəncirvari) | −0.06 | +0.96 | +0.22 | +0.41 | +1.17 |
| Real qeyri-neft ÜDM | +0.38 | +1.20 | +0.27 | +0.52 | +1.46 |
| İstehlak | +0.36 | +1.16 | +0.89 | +1.12 | +1.41 |
| Qeyri-neft investisiyası | +3.47 | +11.42 | −0.03 | +1.17 | −0.08 |
| Büdcə gəlirləri | +3.78 | +1.41 | +0.57 | +0.86 | +1.75 |
| Qeyri-neft idxalı | −0.16 | +1.14 | +0.91 | +1.14 | +1.37 |
<!-- /AUTO:v22_multipliers -->

<!-- AUTO:fr1v236_brent -->
**Brent +10 və zəncirvari real ÜDM.** Heç bir sektorun əlavə dəyəri azalmasa da (ən kiçik sektor kənarlaşması +0,00%), real ÜDM 2026–2030-cu illərdə +0,18, +0,07, −0,01, −0,01, −0,06% kənarlaşır. Zəncirvari ÜDM hər sektorun artımını onun əvvəlki ilin nominal payı ilə çəkiləndirir; yüksək neft qiyməti real hasilatı azalan neft-qaz trayektoriyasını izləyən (ildə −1,1%) mədənçıxarmanın payını artırır, ona görə də eyni sektor həcmləri bir qədər aşağı aqreqat artım verir. Bu, indeksin çəki effektidir, azalma deyil; qeyri-neft ÜDM artır.
<!-- /AUTO:fr1v236_brent -->

Nəqliyyat artıq bu şokların heç birinə reaksiya vermir (onun tənliyi tranzit həcmi + trenddir). **Kredit şərtlərinin yumşaldılması** (uçot
dərəcəsi −200 baza bəndi, depozit faiz dərəcəsi −100 baza bəndi) qiymətləndirilmiş modeldə yalnız ev təsərrüfatlarına kreditlər və istehlak
vasitəsilə təsir göstərir; "ekspert mülahizəsinə əsaslanan əlavə" adlı sütun bundan əlavə investisiya tənliyində kreditin kənarlaşmalarına
regional panel üzrə 0,134 buraxılış elastikliyini tətbiq edir — bu, istifadəçi rıçağıdır, qiymətləndirilmiş effekt **deyil** (aqreqat
məlumatlar onu rədd edir, HAC-F p = 0,028).

<!-- AUTO:v22_fiscal -->
**Fiskal multiplikator (`FR1_fiscal_multiplier.csv`).** İldə +1 mlrd manat real dövlət investisiyası (F4 reaksiyasından sonra faktiki inyeksiya
977 mln): 2030-cu ildə real qeyri-neft ÜDM +741 mln (2015-ci il qiymətləri ilə) — **2030-cu il üzrə səviyyə multiplikatoru 0,76**;
**kumulyativ multiplikator** (2026–30 üzrə Δ qeyri-neft ÜDM cəmi / inyeksiyaların cəmi) **0,63** (zəncirvari çəkili real ÜDM üzrə 0,57). O,
birinci yenidənbaxmadakından (0,54/0,46) böyükdür, çünki gəlir dövrəsi daha güclüdür; idxal indi artır (+1,14%).
<!-- /AUTO:v22_fiscal -->

<!-- AUTO:v22_oilprice -->
**Neft qiymətinin artması zəncirvari çəkili real ÜDM-i azaldır** (−0,06%; v2.2-dən əvvəl −0,48%), eyni zamanda qeyri-neft ÜDM-i (+0,38%) və büdcə gəlirlərini
(+3,78%) artırır: daha yüksək neft qiyməti mədənçıxarma deflyatorunu və deməli, mədənçıxarmanın zəncir çəkisini artırır, mədənçıxarmanın
həcmi (ekzogen) isə azalır. v2.2: mədənçıxarma deflyatoru indi ixrac dəyəri ilə çəkili neft + qaz ixrac qiymətləri indeksinə (2025-də neft karbohidrogen ixracının 58%-i) bağlıdır, manatla Brent qiymətinə deyil, buna görə çəki effekti — və real ÜDM-in azalması — daha kiçikdir.
<!-- /AUTO:v22_oilprice -->

---

## 8. Tam hesablar: hər sektor və bazar üzrə beş göstərici

Notebook-un Hissə 16-sı analitikə lazım olan tam hesabları təqdim edir: **49 obyekt** üzrə — 12 DSK sektoru, 7 aqreqat,
4 istehlak bazarı, 5 investisiya aqreqatı, 5 əmək bazarı sırası, 4 kredit və depozit sırası, 3 xarici ticarət sırası,
7 fiskal sıra və 2 qiymət indeksi — həm tarixi dövr (2005–2025), həm də proqnoz dövrü (2026–2030) üçün, hər üç
ssenari üzrə beş uzlaşdırılmış sıra:

**real dəyər · real artım tempi · deflyator · deflyator inflyasiyası · nominal dəyər**

bunlar `nominal = real × deflator` eyniliyi ilə əlaqələndirilir və bu eynilik ədədi olaraq yoxlanılıb (maksimum mütləq xəta 1,5×10⁻¹¹).

### 8.1 Hər obyekt üçün “real” və “deflyator” nə deməkdir — fərz edilmir, açıq göstərilir

Əlavə dəyər sektorları və istehlak bazarlarının **öz** implisit deflyatoru var (nominal ÷ zəncirvari real; Bölmə 2.4-də
törədilib). Maliyyə, fiskal və əmək aqreqatları üçün dərc edilmiş deflyator yoxdur, buna görə deflyator *seçilməlidir* və bu seçim
hər obyekt üzrə açıq bəyan edilir:

| Obyekt qrupu | Öz deflyatoru varmı? | İstifadə olunan deflyator | “Real”ın mənası |
|---|---|---|---|
| 12 sektor, ÜDM, qeyri-neft ÜDM, neft-qaz ÜDM | Bəli, implisit | Nominal ÷ real əlavə dəyər | Sabit qiymətlərlə həcm |
| İstehlak bazarı, pərakəndə ticarət, ictimai iaşə, pullu xidmətlər | Bəli, implisit | Dövriyyə deflyatoru | Sabit qiymətlərlə dövriyyə |
| Əsas kapitala investisiya (5 aqreqat) | Bəli, implisit | Aqreqat investisiya deflyatoru | Sabit qiymətlərlə investisiya |
| Kredit, depozitlər, büdcə gəlirləri və xərcləri, borc | Xeyr | **ÜDM deflyatoru** | Daxili buraxılış üzrə alıcılıq qabiliyyəti |
| Əmək haqları | Xeyr | **İQİ** | İstehlak üzrə alıcılıq qabiliyyəti |
| Məşğulluq, işçi qüvvəsi | tətbiq olunmur | — | Kəmiyyət özü *realdır* |
| Mal ixracı və idxalı | Qismən | Manatla dəyərə tətbiq olunan ÜDM deflyatoru | Sabit qiymətlərlə ticarət həcmi |

**Yoxlama:** hesablardakı hər bir tarixi nominal sıra yoxlanılmış bütün obyektlər üzrə iş kitabının özündə dərc edilmiş sıranı
**0,000000%** dəqiqliklə təkrarlayır, o cümlədən neft / qeyri-neft ÜDM bölgüsü; bu bölgüdə tarixi dövr üçün dərc edilmiş dəqiq nominal
dekompozisiya, yalnız proqnoz dövrü üçün isə kalibrləşdirilmiş mədənçıxarma/neft ÜDM nisbəti (1,100) istifadə olunur.

### 8.2 Əhatəni tamamlamaq üçün əlavə edilmiş bazarlar

Tələb sektorlarla yanaşı bazarları da əhatə edir, buna görə istehlak bazarı dərc edilmiş üç komponentinə —
pərakəndə ticarət, ictimai iaşə və pullu xidmətlər — ayrılmışdır; onların yekunla eyniliyi mənbədə dəqiq ödənilir. Onların **nominal payları**
cəmlənmə şərti (adding-up) qoyulmaqla SUR ilə sistem kimi qiymətləndirilir, lakin **ekstrapolyasiya edilmir** və bunun səbəbi məlumatlarda görünür:
paylar 2020-ci ildə kəskin dəyişmiş və o vaxtdan bəri əvvəlki səviyyəsinə *qayıdır* (pullu xidmətlər 2019-cu ildə 19,0% → 2020-ci ildə 14,6% → 2025-ci ildə
17,5%). Trend spesifikasiyası nümunədaxili yaxşı uyğunlaşır (R² ≈ 0,84), lakin 2030-cu ilədək pərakəndə ticarətin payını 85,5%-ə, pullu xidmətlərin payını isə 11,5%-ə çatdırır —
bu, son beş ilin dinamikasının əksidir. Buna görə struktur üç illik orta səviyyədə saxlanılır və yenidən normallaşdırılır; sektoral kredit paylarına da
eyni yanaşma, eyni səbəbdən tətbiq olunur.

### 8.3 Hesablar üzərində işin aşkar etdiyi daha iki xəta

Hesabların qurulması hər bir sıranın mənbə ilə uzlaşdırılmasını tələb etdi və bu, təkcə proqnoz cədvəllərində gizli qalan iki qüsuru
üzə çıxardı:

1. **Karbohidrogen ixracı tənliyində ölçü vahidi xətası.** Reqressiya kimi qiymətləndirildikdə o, neft gəlirləri üzrə **1,285** elastiklik verirdi —
   bu, iqtisadi baxımdan mümkün deyil, çünki ixracın dəyəri *elə* həcm × qiymətdir. Artıqlıq ölçü vahidlərinin qarışdırılmasından irəli gəlirdi: neft ixracının
   həcmi milyon **tonla**, ixrac qiyməti isə bir **barel** üçün ifadə olunur. Çevirmə əmsalının dərc edilmiş neft ixracı dəyərindən bərpası
   **bir tonda 7,400 barel** verir və bununla əlaqə dəqiq eyniliyə çevrilir (maksimum xəta neft üzrə 0,00%, qaz üzrə
   0,01%). B4 gömrük həcmi × qiymət hasilini daha geniş tədiyə balansı göstəricisi ilə əlaqələndirən kalibrləşdirilmiş nisbətli (1,002, 2021–25-ci illərin ortası)
   eynilikdir.
2. **Həlledicidə üç tənlik öz sabit düzəlişindən xəbərsiz şəkildə məhrum qalmışdı** — ev təsərrüfatlarına kredit, depozitlər və
   karbohidrogen ixracı. Təsir hesablar cədvəl şəklində tərtib edildikdən sonra görünürdü: real ev təsərrüfatı krediti proqnozun birinci
   ilində 20% azalır, sonra normal artırdı — açıq-aşkar səviyyə kəsintisi. Notebook indi hər düzəliş edilmiş dəyişənin öz terminini həlledici daxilində
   faktiki tətbiq etdiyini təsdiqləyən **avtomatlaşdırılmış özünüyoxlama** ehtiva edir, beləliklə, bu sinif xətalar bir daha səssizcə təkrarlana bilməz.

### 8.4 Beş göstərici üzrə əsas nəticələr, Əsas ssenari

<!-- AUTO:v22_accounts -->
| | Real artım<br>illik % | Deflyator inflyasiyası<br>illik % | Nominal artım<br>kumulyativ % | Nominal 2030<br>mln AZN |
|---|---|---|---|---|
| **ÜDM** | +2.6 | +5.1 | +45.4 | 187 727 |
| **Qeyri-neft ÜDM** | +3.8 | +6.7 | +65.9 | 153 142 |
| Neft-qaz ÜDM | −1.2 | −0.0 | −6.0 | 34 585 |
| Turizm və ictimai iaşə | **+8.2** | +5.9 | +97.5 | 7 055 |
| İnformasiya və rabitə | +7.4 | −2.7 | +25.0 | 3 337 |
| Emal sənayesi | +6.3 | +4.7 | +71.3 | 13 220 |
| Nəqliyyat və anbar təsərrüfatı | +5.0 | +2.7 | +46.0 | 13 299 |
| Su təchizatı və tullantıların emalı | +4.4 | +4.5 | +54.7 | 467 |
| Kənd təsərrüfatı | +3.8 | +4.3 | +48.5 | 11 360 |
| Ticarət və nəqliyyat vasitələrinin təmiri | +3.2 | +7.1 | +65.2 | 24 163 |
| Məhsula xalis vergilər | +3.2 | +7.2 | +66.0 | 20 575 |
| Elektrik enerjisi, qaz və buxar | +2.9 | +8.1 | +70.3 | 2 478 |
| Sosial və digər xidmətlər | +2.4 | +9.7 | +79.0 | 50 244 |
| Tikinti | +0.9 | +2.8 | +19.8 | 10 096 |
| Mədənçıxarma | −1.1 | +0.1 | −5.1 | 31 433 |
<!-- /AUTO:v22_accounts -->

<!-- AUTO:fr1v236_tou -->Turizmin ildə +8,2% artımı daha sürətlə artan adambaşına gəlirə görə onun gəlir elastikliyindən (1,9)<!-- /AUTO:fr1v236_tou --> və trenddən irəli gəlir — bu da ehtiyatla
şərh edilməli olan tələb dövrəsinin daha bir nəticəsidir. Sosial xidmətlərin deflyatoru hələ də <!-- AUTO:fr1v236_soc -->ildə 9,7% artır<!-- /AUTO:fr1v236_soc -->: İQİ-dən vahid ötürülmə əmsalı qoyulub, lakin
dreyfsiz hipotez rədd edildiyi üçün qiymətləndirilmiş dreyf saxlanılır.

## 9. Məhdudiyyətlər

Hər biri ümumi xəbərdarlıq deyil, konkretdir və bilavasitə məlumatlarla əlaqələndirilə bilər.

1. **İş kitabında xərclər–buraxılış cədvəli yoxdur**, buna görə sektorlararası əlaqələr *ölçülmür*, zaman sıraları və panel üzrə birgə dəyişmə əsasında
   *qiymətləndirilir*. Bu, ən yüksək dəyərə malik məlumat əlavəsidir və hər halda siyasət modulunun FR2 tələbi üçün zəruridir.
2. **İllik tezlikdə sektor səviyyəsində məşğulluq məlumatı yoxdur** — yalnız sənaye yarımsahələri (2016–2025) və regionlar (2021–2025) üzrə mövcuddur. Tam
   sektor istehsal funksiyaları yalnız sənaye üçün qiymətləndirilə bilər. Bu, FR3 və FR4-ün (*sektorlar üzrə* əmək haqqı və məşğulluq) yalnız bu
   fayl əsasında nə təqdim edə biləcəyini birbaşa məhdudlaşdırır.
3. **İş kitabının heç bir yerində xarici tələb dəyişəni yoxdur**, buna görə o, istifadəçi tərəfindən təyin edilən ssenari girişidir və qeyri-neft ixracı tənliyi
   yalnız təklif tərəfini əks etdirir.
4. **İdentifikasiya edilmiş faiz dərəcəsi və ya buraxılış kəsiri kanalı yoxdur** (Bölmə 5). Model nə uçot dərəcəsinin dəyişməsini bazar faiz dərəcələri
   vasitəsilə, nə də xalis tələb təzyiqinin inflyasiyaya təsirini simulyasiya edə bilir.
5. **Fiskal və tədiyə balansı nümunələrinin qısalığı** (16 illik müşahidə) bu blokların parametr qeyri-müəyyənliyinin xeyli geniş olması deməkdir.
6. **Regional panel cəmi beş illikdir**; bir sıra əmsallar birtərəfli və ikitərəfli spesifikasiyalar arasında işarəsini dəyişir,
   bu, notebook-da göstərilir. Onun statistik nəticəsində indi t(4) paylanması və beş il üzrə wild cluster bootstrap istifadə olunur.
7. **2017-ci ildən məzənnə faktiki olaraq sabitlənib (de facto peg)**, buna görə ötürülmə əmsalı demək olar ki, tamamilə 2015–16-cı illərin devalvasiyası ilə identifikasiya edilir.
   Məzənnəni dəyişən istənilən ssenari tək bir epizoddan ekstrapolyasiya edir.
8. **Sektorlar üzrə investisiya deflyatorları dərc edilmir**, buna görə aqreqat investisiya deflyatoru hər sektora tətbiq olunur.
9. **Zəncirvari həcmlər additiv deyil**; qeyri-neft fərqi (wedge) üçün ölçüsü göstərilən kalibrləşdirilmiş düzəliş istifadə olunur.
10. **İnformasiya və rabitə, tikinti, nəqliyyat və emal sənayesi üzrə proqnozlar ən zəifdir** (nümunədən kənar yoxlamada <!-- AUTO:v22_lim10 -->RMSE 14,5–25,7%<!-- /AUTO:v22_lim10 -->; İKT-də ona görə ki, yoxlamanın kəsim ili olan 2020 onun investisiya payının dib nöqtəsi idi); pandemiyadan əvvəlki
    sabit artımla müqayisədə model yalnız eyni səviyyədədir (median U 1,02).
11. **Kalibrləşdirilmiş paylar sabit saxlanılır** (sektorlar üzrə investisiya və kredit payları — v2.1-dən 2025-ci ilin faktiki səviyyəsində —, sosial xərclərin payı, borcxidmət dərəcəsi).
12. **Dövlət investisiyasının səviyyəsi proqnoz deyil, fərziyyədir** (Bölmə 5, sonuncu sətir).
13. **Kointeqrasiya 30 səviyyə əlaqəsindən yalnız 2-si üçün təsdiqlənib** (10% səviyyəsində 4); səviyyə t-statistikalarının əksəriyyəti təsviridir və
    proqnoz səviyyəsi sabit düzəliş əmsalı fərziyyəsindən asılıdır (Bölmə 7.4, həssaslıq).
14. **Trendlə müəyyən olunan artım** — 2027–2030-cu illərdə nəqliyyat, kənd təsərrüfatı, İKT və elektrik enerjisi artımı əsasən qiymətləndirilmiş determinist
    trenddən ibarətdir (Bölmə 7.4).
15. **Güclü tələb dövrəsi** (gəlirin qeyri-neft ÜDM-ə bağlılığı) artımı, turizmi və fiskal multiplikatoru yüksəldir; emal sənayesi
    ixrac ↔ emal sənayesi əlaqəsi ilə gücləndirilir. Ev təsərrüfatlarının gəlir elastikliyi pensiya xərcləri proksisinə
    (orta pensiya × ümumi əhali) əsaslanır; v2.2-də makro modulun gəlirin mənbələr üzrə bölgüsü (DSMF transfertləri) yoxlanılıb:
    nümunədaxili daha yaxşı, dinamik nümunədən kənar yoxlamada daha pis — proqnoz deyil, mühərrik rıçağıdır (v2.2 qeydi).
16. İnvestisiyada **aqreqat kredit kanalı yoxdur**; kredit şərtlərinin yumşaldılmasının investisiyaya təsiri ekspert mülahizəsinə əsaslanan əlavədir (overlay).
<!-- AUTO:v23_lim17 -->
17. **Yelpiklər** İQİ, istehlak və cari xərclər üçün genişdir, sıçrayışların süzgəcdən keçirilməsi ilə kəsilir (cəhd edilmiş təkrarlamaların
    22,7%-i rədd edilir, antitetik cütləri ilə birlikdə 41,6%-i əvəz olunur), İQİ üzrə güzgü əksi şəklində deflyasiya quyruğuna
    malikdir və göstərilən median düzəlişindən sonra Əsas ssenari ətrafında mərkəzləşdirilir.
<!-- /AUTO:v23_lim17 -->

## 10. Modeli ən çox nə təkmilləşdirərdi

1. **Resurslar və istifadə / xərclər–buraxılış cədvəli** — qiymətləndirilmiş əlaqələri ölçülmüş əlaqələrlə əvəz edir və siyasət modulunun FR2 tələbinin icrasına imkan yaradır.
2. **Sektorlar üzrə məşğulluq və əməyin ödənilməsi**, illik — istehsal funksiyası blokunu tamamlayır və FR3/FR4-ə birbaşa xidmət edir.
3. **Tərəfdaş ölkələrin çəkiləri ilə xarici tələb** və tarixi sırası olan idxal qiymət indeksi — ticarət blokunun düzgün identifikasiyasını təmin edir.
4. **Sektorlar üzrə rüblük milli hesablar** — effektiv nümunəni təxminən dörd dəfə artırır və dinamikanın qoyulmaq əvəzinə qiymətləndirilməsinə imkan verir.
5. **Daha uzun regional panel** — kəsişmə modelin ən yaxşı identifikasiya vasitəsidir və hazırda cəmi beş il dərinliyindədir.
