> **İngilis dilində (English version):** [FR5_Methodology.md](../FR5_Methodology.md). Rəqəmlərin yazılışı: mətndə onluq kəsr vergüllə, minliklər boşluqla ayrılır; cədvəllərdə, düsturlarda, kodda və fayl adlarında onluq kəsr proqram çıxışında olduğu kimi nöqtə ilə verilir. `AUTO` işarələri arasındakı bloklar hər icrada notebook tərəfindən bu sənəddə də Azərbaycan dilində yenidən yazılır.

# FR5 — Əhaliyə göstərilən pullu xidmətlər
## Struktur ekonometrik metodologiya və beşillik proqnoz

**MİİS modulu 15.5.2 — Mikroiqtisadi təhlil və proqnozlaşdırma**
Azərbaycan Respublikasının İqtisadiyyat Nazirliyi

`FR5.ipynb` faylını müşayiət edən sənəd. Bir-biri ilə əlaqəli toplunun dördüncüsü: **FR1** (sektor buraxılışı və makroiqtisadiyyat),
**FR3** (əmək haqqı), **FR4** (məşğulluq), **FR5** (pullu xidmətlər).

---

<!-- AUTO:v22_note -->
## v2.2 (2026-10-05): Nazirliyin makro modulundan rəqib tənliklər

Makro modulda pullu xidmətlərin real artımı son istehlakın real artımı ilə izah olunur (U ≈ 0,60), Nazirliyin öz iş kitabında isə
(`MOE SOCIAL.xlsx` eq8) Δln pullu xidmətlər = −0,0055 + 1,07 Δln ticarət + 0,38 Δln əmək haqqı. Hər iki forma (artım forması,
gecikmiş asılı dəyişənsiz) və Nazirliyin dərc olunmuş əmsalları E1-in öz qaydaları ilə qiymətləndirilib (≤2019 başlanğıclar və
toxunulmamış 2020–2025 pəncərəsi). Nəticə (`FR5_macro_module_competition.csv`): istehlak forması yoxlamada U 0,99 / 0,68,
2019-a qədər yenidən qiymətləndirilmiş E1 isə 0,77 / 0,52; Nazirliyin forması 2,61 (yenidən qiymətləndirilmiş) və 3,95
(dərc olunmuş əmsallarla). **Heç biri qəbul edilmir**; hamısı ≤2019 başlanğıclarda E1-dən əhəmiyyətli dərəcədə pisdir. Reyestrdə:
`FR5.M1_cons_growth`, `FR5.M2_ministry_reest`, `FR5.M3_ministry_fixed` (rədd edilib).

**Pay modelləri — dəyişməzlik davranışı.** κ = 512 büzülmə və 2025 lövbəri ilə paylar dəyişməz yola yaxındır: 2025→2030 median
dəyişmə 0,02 f.b. (ən çox 0,29 f.b.), 13 növdən 12-si 0,1 f.b.-dən az dəyişir, yoxlamada U (təsadüfi gəzişmə) 11 növ üçün
1,00-dır (`FR5_share_change_check.csv`). Bu, ≤2019 κ seçiminin nəticəsidir, öz keçmişinə əsaslanan model deyil.
<!-- /AUTO:v22_note -->

<!-- AUTO:v23_note -->
## v2.3 (2026-10-05): düzəliş əmsallarının sabit yarımsönmə dövrü ilə sönməsi (qalıq AR qiymətləndirilmir)

v2.2-yə qədər Hissə 17-nin "düzəliş əmsallarının sönməsi" həssaslıq variantında E1-in, pay tənliklərinin və iki bölgünün 2025
düzəlişləri hər tənliyin qiymətləndirilmiş birinci tərtib qalıq avtokorrelyasiyası ρ̂ sürəti ilə sönürdü (E1 ρ̂ = 0,59) — bu,
müştərinin tələbinin istisna etdiyi qiymətləndirilmiş AR(1) əmsalıdır. v2.3-dən sönmə **sabitdir, qiymətləndirilmir**: 0,5^(h/H),
h — 2025-dən sonrakı illər, yarımsönmə dövrü **H = 1 il** (ildə 0,50; layihənin natamam il qaydası). H mühərrikdə
`addf_half_life` rıçağıdır (0,25–10 il, yalnız `addf_decay` açıq olduqda). ρ̂ yalnız diaqnostika kimi göstərilir. Ssenarilər sabit
düzəlişlərlə qalır və dəyişmir. Sönmə həssaslığında 2030 ümumi həcm Əsas ssenariyə nisbətən −492 mln manat
(−4,62%); v2.2-də (ρ̂ ilə sönmə) −483 (−4,44%).
<!-- /AUTO:v23_note -->

---

## v2 (2026-10-05): tənliklər reyestri, ssenari mühərriki, dayanıqlıq

<!-- AUTO:v2 -->
**Tənliklər reyestri** (`output/FR5_equations.json`): 84 tənlik, onlardan 15-i proqnozda istifadə
olunur — E1 (gəlir + nisbi qiymət, DOLS(0: eyni dövrün Δx-i), η = 1,155, ε = -0,182), proqnoz sistemindəki 12 büzülmüş Engel meyli
(κ = 512, seçim pəncərələri ≤2019) və iki sabit institusional pay. Qeydiyyatda həmçinin: 1-ci pillə namizədləri (yalnız gəlir, deflyasiya
edilmiş gəlir, gəlir + trend, yalnız trend, artım forması) və E1-in fərq forması, Hissə 9-un statik alternativləri, 12 pay tənliyinin
səviyyə (DOLS) və fərq formaları, qiymətlə genişləndirilmiş MNL, LA-AIDS (SUR, homogenlik + simmetriya), bölgü namizədləri (gəlir,
trend). Hər OLS/DOLS tənliyi statsmodels ilə yenidən qiymətləndirilib və notebook-un qiymətləri ilə yoxlanılıb (uyğunsuzluq: 0).
Dayanıqlıq hökmləri (bütün tənliklər): qeyri-stabil 49, qismən stabil 34, stabil 1; proqnozda istifadə olunanlar: qismən stabil 15 (büzülmüş meyllər və sabit
paylar üçün rekursiv testlər tətbiq olunmur; E1: rekursiv: c20 işarəsi yolun ilk yarısında dəyişir; bir ili çıxarmaqla: c20 işarəsi dəyişir; rekursiv: c21 işarəsi yolun ilk yarısında dəyişir).

**Ssenari mühərriki** (`microlib/engines/fr5.py`, `_fr5_core.py`; vəziyyət `output/engine/FR5_state.json` + `.npz`): Hissə 14-ün `solve()`
funksiyası köçürülüb. Girişlər: 4 FR1 yolu (`fr1:rhhdisp`, `fr1:p_cons`, `fr1:p_serv_hh`,
`fr1:pop`) və 13 növ üzrə nisbi qiymət yolu, 14 redaktə edilə bilən əmsal (η, ε və 12 büzülmüş
Engel meyli; SE və 95% interval reyestrdən), 6 rıçaq (növ qiymət qaydası, η seçimi, xidmətlərin nisbi qiyməti, əhali
artımı, düzəliş əmsalının sönməsi). `selftest()`: bütün 3 ssenaridə CSV çıxışları təkrarlanır (maks. nisbi fərq
2,5·10⁻¹⁶); rıçaqlar Hissə 17 rıçaq cədvəlini dəqiq təkrarlayır. Bir ssenari < 0,1 s.

**Tam proqnoz cədvəli** (`FR5_forecast_tidy.csv`, `FR5_indicator_catalog.csv`): 79 komponent (cəmi həcm və dəyər, adambaşına
həcm, deflyator və artım templəri, 13 növün həcmi, dəyəri, payı, deflyatoru və artımı, iki bölgünün payları və dəyərləri) ×
3 ssenari × 2026–2030, hamısı dolu, tarix ilə; 5–95% zolaqlar 21 komponent üçün (Əsas).
`FR5_not_forecast.csv`: regional sıralar (milli sıra ilə uzlaşmır, Hissə 13).

**Əmsal həssaslığı** (`FR5_coef_sensitivity.csv`, ±1 SE, 2030, Əsas; başlıq: cəmi həcm və dəyər, 2030 dəyərinə görə ən böyük üç növ —
Rabitə xidmətləri, Kommunal xidmətlər, Nəqliyyat xidmətləri): ən böyük təsirlər — Pullu xidmətlər, cəmi: nominal dəyər: FR5.E1_income_relprice|ln_income_pc (-1,65% / +1,67%); Rabitə xidmətləri: real həcm: FR5.E1_income_relprice|ln_income_pc (-1,65% / +1,68%); Pullu xidmətlər, cəmi: real həcm: FR5.E1_income_relprice|ln_income_pc (-1,65% / +1,67%); Nəqliyyat xidmətləri: real həcm: FR5.E1_income_relprice|ln_income_pc (-1,68% / +1,71%); Kommunal xidmətlər: real həcm: FR5.E1_income_relprice|ln_income_pc (-1,68% / +1,71%). Mətnlər: `FR5_strings_az.csv` (446 ingiliscə mətn → azərbaycanca). Kernel: `miis-model` (Python 3.13).
<!-- /AUTO:v2 -->

---

## Yenidənbaxma qeydi (2026-09-27; sonrakı mərhələlər 2026-09-28)

§7–§11-dəki rəqəmlər onları yaradan icranın CSV nəticə fayllarından `AUTO` markerləri arasında **notebook tərəfindən
generasiya olunur** (sonuncu kod xanası), buna görə sənəd nəticələrdən ayrı düşə bilməz.

<!-- AUTO:rev -->
Cari əsas nəticələr (bu icra): 1-ci pillə = gəlir + nisbi qiymət, η = 1,155; 2-ci pillə = MNL: Engel həddi, koherent olduqda səviyyə meyli, əks halda fərq forması, Engel meylinin büzülməsi κ = 512; 2026–2030-cu illərdə həcm ildə +4,04%, dəyər +7,58%; E1 üzrə işarəyə görə rədd edilmə nisbəti 22,8%; FR5-in 56 CSV çıxışı.
<!-- /AUTO:rev -->

Nə dəyişdi və nə üçün:

1. **Kointeqrasiya testləri düzəldildi** (MacKinnon qalıqlara əsaslanan `eg_coint_p`); kointeqrasiya olunmayan səviyyə
   münasibətləri təsviri kimi işarələnir və artıq kointeqrasiya olunan münasibətlər adlandırılmır.
2. **Qiymətləndirici və statistik nəticə** — səviyyə münasibətləri üçün DOLS (müqavilədəki sərbəstlik dərəcəsi (df) qaydası);
   n/(n−k) miqyaslaşdırması ilə HAC, t(n−k), HAC-F; hər səviyyə tənliyi həmçinin birinci fərqlərdə qiymətləndirilir.
3. **Hər seçim üçün vahid qərar qaydası** (aqreqat, paylar, büzülmə, bölgülər): xəta ölçümləri ≤ 2019 illərinə düşən
   pəncərələrdə ən yaxşısından əhəmiyyətli dərəcədə pis olmayan namizədlər (DM/HLN, p > 0,10); onların arasında
   **uyğun (koherent)** olanlara üstünlük verilir (səviyyə meylləri qiymətləndirmə nümunəsində fərqlərdə qiymətləndirilmiş eyni
   tənliyin 95% etibarlılıq intervalının daxilindədir); sonra isə ən sadəsinə. Artım formalı 1-ci pillə namizədi eyni dizaynda
   yarışır. Homogenlik qoyulmuş tənlik (səviyyədə η 0,43, fərqlərdə isə 1,29) uyğunsuz kimi rədd edilir.
4. **"Dəbdəbə" (luxury) xarakteristikası statistik tapıntı kimi geri götürüldü**; xidmətlərin nisbi qiyməti 2005–2025-ci
   illərdə **azalıb**.
5. **2-ci pillə multinomial-logit pay sistemi kimi yenidən adlandırıldı**; elastiklik $1+\beta_i-\sum_j w_j\beta_j$;
   orta elastikliyin 1-ə bərabər olması mexaniki xarakter daşıyır; IIA və istinad növünün öz qiymət elastikliyi göstərilir;
   namizəd kimi həqiqi LA-AIDS əlavə edildi. Uyğunsuz səviyyə Engel meylləri fərq formasındakı meyllərlə əvəz olunur və
   bütün növ meylləri dəqiqliyə görə çəkilənmiş empirik Bayes üsulu ilə ümumi elastiklik 1-ə doğru **büzülür**, büzülmə
   intensivliyi isə eyni qayda ilə seçilir — FR1-in yekun, xeyli güclü gəlir trayektoriyası ilə büzülməmiş meyllər
   inandırıcı olmayan növ trayektoriyaları verirdi.
6. Proqnoz xətalarının ölçülməsində **gələcək məlumatlara baxmadan seçim** (look-ahead olmadan); 2020–2025 toxunulmamış test
   pəncərəsidir.
7. Qiymətlə genişləndirilmiş variantlarda **tələb qanunu dəqiq qoyulub** (seçilməyib; `FR5_nonselected_*` kimi ixrac
   olunur); proqnozun istifadə etdiyi dəyərlər `FR5_own_price_elasticities_forecast_system.csv` faylında verilir.
8. **Növlərin sıralaması** — qaydadan asılı olmayaraq zəif əsaslandırılır; hər növün öz tarixi ilə müqayisə olunur.
9. **Qiymətlərin öz tarixinə əsaslanan ekstrapolyasiyası yoxdur**; **əhali FR1-dən götürülür**; **nümunədən kənar
   yoxlamalar (hold-out)** bütün qərar qaydası kəsimdən əvvəlki məlumatlara tətbiq edilməklə yenidən aparılıb;
   **institusional bölgülər** proqnozlaşdırılıb və yelpik qrafikləri ilə ixrac olunub.
10. **Yelpik qrafikləri** — mərkəzləşdirilmiş tarixi qalıq trayektoriyalarının təkrar seçimi (resampling; ρ̂ prosesi
    olmadan), işarəyə görə rədd etmə ilə parametr çəkilişləri, FR1 makro çəkilişləri yalnız qeyri-sonlu dəyərlərə görə
    süzülür; yalnız doqquz birgə trayektoriya istifadəyə yararlıdır (açıqlanır); hər tənlik üzrə birləşdirilmiş variant da
    təqdim olunur.

---

## 1. Tapşırıq

> *Əhaliyə göstərilən pullu xidmətlərin **həcmi** və **artım sürətinin** təhlili və proqnozlaşdırılması.*

Əhaliyə göstərilən pullu xidmətlərin **həcminin** və **artım sürətinin** təhlili və proqnozlaşdırılması, 2026–2030.
AR, ARIMA, ARCH və ya GARCH modelləri istifadə olunmur; yalnız struktur ekonometrik modellər; çatışmayan məlumatlar
Dövlət Statistika Komitəsindən (DSK) toplanmalıdır.

## 2. Burada "struktur" nə deməkdir

Əhaliyə göstərilən pullu xidmətlər **ev təsərrüfatlarının xidmət istehlakıdır**. Bu obyektin struktur modeli zaman sırası
münasibəti deyil, **tələb sistemidir**. FR5 iki pillədə qurulub:

1. **Nə qədər** — adambaşına real həcm üçün aqreqat tələb tənliyi; izahedici dəyişənlər adambaşına real ev təsərrüfatı
   gəliri və xidmətlərin nisbi qiymətidir. Bu, *həcmi* və onun *artım sürətini* verir.
2. **Nədən ibarət** — dərc olunan on üç xidmət növü üzrə **multinomial-logit pay sistemi**; tənliklər loqarifmik şans
   nisbətləri (log-odds) şəklində yazılır ki, paylar qurulma etibarilə müsbət olsun və cəmi vahidə bərabər olsun. Onun Engel
   meylləri xərc elastikliklərini verir — ev təsərrüfatları daha çox xərclədikcə hansı xidmət bazarlarının böyüdüyünü göstərir.

Əlavə olaraq iki institusional bölgü daxil edilir və proqnozlaşdırılır: hüquqi şəxslər və fərdi sahibkarlar, habelə
dövlət və qeyri-dövlət sektoru.

---

## 3. Məlumatlar və DSK-nın nə üçün lazım olduğu

İş kitabında aqreqat göstərici və xidmət göstərənlər üzrə bölgü var, lakin **xidmət növləri üzrə heç bir bölgü yoxdur**.
Bu bölgü olmadan nə tələb sistemi qurmaq, nə də hansı xidmətlərin artdığını demək mümkündür.

| Mənbə | Məzmun | İllər |
|---|---|---|
| İş kitabı `Sosial sektor ` r27–r34 | Ümumi dəyər və real artım; hüquqi şəxslər; qeyri-dövlət sektoru; fərdi sahibkarlar | 1990–2025 |
| İş kitabı `Sosial sektor ` r35–r36 | Əhalinin nominal gəlirləri, cəmi və adambaşına | 1997–2025 |
| İş kitabı `Monetar sektoru` r89, r93 | **Pullu xidmətlər üzrə İQİ**, 12 aylıq və orta illik | 2000–2025 |
| İş kitabı `Regionlar`…`13` r100 | 14 iqtisadi rayon üzrə xidmətlərin real artımı | 2021–2025 |
| **DSK `007_4-5en.xls`, vərəq 7.4** | **13 xidmət növü üzrə dəyər** | **1995–2025** |
| **DSK `007_18en.xls`, vərəq 7.18** | **Növlər üzrə fiziki həcm indeksi** | **2006–2025** |
| DSK `007_3en.xls`, vərəq 7.3 | Dövlət/qeyri-dövlət, dəyər və həcm indeksi | 1995–2025 |
| DSK `007_1en.xls`, vərəq 7.1 | Uzun ümumi sıra | 1985–2025 |

**Validasiya.** On üç növ bütün 31 ildə dərc olunmuş yekunu 2 × 10⁻¹⁴% dəqiqliklə təkrarlayır, deməli, onlar büdcə
paylarının cəmi vahidə bərabər olan tam bölgü təşkil edir — məhz buna görə tələb sistemi düzgün obyektdir və toplanma şərti
(adding-up) avtomatik ödənilir. Müstəqil şəkildə dərc olunan dörd cədvəl nominal yekun üzrə iş kitabındakı yuvarlaqlaşdırma
həddində, real artım indeksi üzrə isə dəqiq uyğun gəlir.

## 4. Əsas eynilik

**Dərc olunmuş sıranın implisit deflyatoru iş kitabındakı pullu xidmətlər üzrə orta illik İQİ ilə dəqiq eynidir** — üst-üstə
düşən on doqquz ilin hər birində 0,04 indeks bəndi dəqiqliyi ilə uyğunluq:

$$\frac{\text{value}_t/\text{value}_{t-1}}{\text{volume index}_t} = \text{paid-services CPI}_t$$

Deməli, bu bazarın qiymət tərəfi **qiymətləndirilmir, müşahidə olunur**. Nəticələri: həcm struktur şəkildə modelləşdirilə
bilər, dəyər isə eynilikdən alınır; nisbi qiymət müşahidə olunan izahedici dəyişəndir; FR1-in deflyator proqnozundan ikinci
xəta mənbəyi əlavə etmədən birbaşa istifadə olunur. FR5-in həcm və dəyər sıraları FR1-in sıraları ilə müvafiq olaraq
0,0005% və 0,02% dəqiqliklə uyğun gəlir, beləliklə on üç növ üzrə bölgü FR1-in öz aqreqatını dekompozisiya edir.

## 5. Məlumatların bütövlüyü üzrə tapıntılar

**F1 — 1995-ci ildən əvvəlki nominal dəyərlər denominasiyadan əvvəlki manatla ifadə olunur.** İş kitabının 27-ci sətrində
1995-ci ildən əvvəlki dəyərlər min köhnə manatla, 1995-ci il və sonrakı dəyərlər isə milyon cari manatla saxlanılır, **eyni
sətirdə və heç bir qeyd olmadan**; iş kitabı və DSK rəqəmləri arasındakı nisbət 1995-ci ildən əvvəl dəqiq 1 000, sonra isə
1,000-dır. Bu sətir əsasında 1994/1995 arasında hesablanan artım sürəti mənasızdır. FR5 nominal məlumatlardan yalnız
1995-ci ildən istifadə edir; həcm indekslərinə bu təsir etmir.

**F2 — DSK-nın bir neçə xanası mətn kimi saxlanılır**; bu xanalarda minliklər ayırıcısı kimi bölünməz boşluq, onluq ayırıcı
kimi isə vergül istifadə olunur (`'4 088 188,1'`). Sadə üsulla oxunduqda onlar buraxılmış dəyərə çevrilir və uzun sıradan
2009, 2014 və 2016–2022-ci illəri səssizcə çıxarır. Xüsusi oxuma aləti (parser) onları emal edir; dörd mənbə üzrə uzlaşdırma
bunun düzgün işlədiyini sübut edir.

**F3 — "Digər pullu xidmətlər" kateqoriyası tərif baxımından qeyri-stabildir**: onun payı 31,4%-dən (1995) 0,3%-ə (2005)
enir, rabitənin payı isə 4,0%-dən 34,2%-ə yüksəlir — bu, davranış deyil, yenidən təsnifatdır. Tələb sistemi 2006-cı ildən
qiymətləndirilir; bu, həm də növlər üzrə həcm indekslərinin dərc olunduğu ilk ildir.

**F4 — Komponent həcmləri dərc olunmuş yekuna toplanmır**; fərq 21%-ə qədərdir. Bu, komponentlərin nisbi qiymətləri
ayrıldıqda zəncirvari həcmlərin standart qeyri-additivliyidir (2025-ci ildə kommunal xidmətlərin deflyatoru 181, rabitənin
deflyatoru isə 107 təşkil edir, 2015 = 100). Nominal komponentlər dəqiq toplanır. Buna görə də FR5 **ümumi həcmi** və
**nominal payları** modelləşdirir, beləliklə heç bir proqnoz ödənilməyən additivliyə əsaslanmır.

**F5 — Regional sıraları milli sıra ilə uzlaşdırmaq mümkün deyil.** 2023–2025-ci illər üçün milli artım indeksi **hesabat
verən bütün rayonların diapazonundan kənardadır**: 2023-cü ildə milli indeks 114,0 olduğu halda, ən yüksək regional göstərici
109,6, bazarın böyük hissəsini təşkil edən Bakı üzrə göstərici isə 108,2-dir. Tam bölgünün çəkili ortası onun ekstremal
dəyərləri arasında olmalıdır. Ya regional sətirlər daha dar anlayışa əsaslanır, ya da böyük komponent çatışmır. Buna görə də
regional məlumatlar təqdim olunur, lakin nə validasiya, nə də amil kimi istifadə olunur. Bir rayon (Şərqi Zəngəzur) yalnız
sıfırlar təqdim edir və çıxarılır.

---

## 6. Avtoreqressiyasızlıq məhdudiyyəti

Heç bir tənlik gecikmiş asılı dəyişən, sürüşkən orta xəta və ya şərti dispersiya prosesi ehtiva etmir. Gecikməyə bənzər
konstruksiyalar uçot və ya statistik nəticə vasitələridir:

| Konstruksiya | Harada | Nə üçün avtoreqressiya deyil |
|---|---|---|
| Newey–West HAC kovariasiyası (n/(n−k) ilə miqyaslandırılmış) | hər bir zaman sırası tənliyi | Yalnız standart xətalar |
| Zəncirvari həcm indeksləri | §4 | Dərc olunmuş səviyyə ilə dərc olunmuş indeks arasında rəsmi eynilik $Q_t = Q_{t-1} I_t$ |
| **İzahedici dəyişən** fərqlərinin DOLS qabaqlayıcı/gecikmə dəyərləri | hər bir səviyyə münasibəti | Endogenlik düzəlişi; asılı dəyişənin gecikmələri heç vaxt daxil olmur |
| Engle–Granger qalıq ADF testi (maksimum gecikmə 1) | kointeqrasiya testləri | Test statistikasıdır, model deyil |
| Qalıqların avtokorrelyasiyası ρ̂ | yalnız diaqnostika cədvəlləri | Diaqnostik statistika (DW kimi); v2.3-dən heç bir proqnoz, ssenari və ya həssaslıq yolunda istifadə olunmur; heç vaxt izahedici dəyişən deyil |
| Düzəliş əmsallarının sönməsi (yalnız həssaslıq) | Hissə 17 | **Sabit** bir illik yarımsönmə dövrü (ildə 0,5; layihənin natamam il qaydası); heç nə qiymətləndirilmir |
| Tarixi qalıq trayektoriyaları $u_{s+h}-u_s$ | yelpik qrafikləri | Müşahidə olunmuş kənarlaşmaların yenidən seçilməsi; heç bir avtokorrelyasiya qiymətləndirilmir |
| Artım formalı namizədin lövbərdən başlayaraq kumulyasiyası | 1-ci pillə namizədi | Zəncir eyniliyi $Q_t = Q_{t-1}(1+g_t)$, qiymətləndirilmiş gecikmə deyil |

**2020 və 2021-ci illər üçün fiktiv dəyişənlər** adı bəlli hadisəni identifikasiya edir və proqnoz dövründə sıfıra bərabər
götürülür. 2020-ci ildən əvvəl bitən hər bir nümunədə onlar sıfırdır və identifikasiya olunmur, ona görə də seçim namizədi
deyil və seçim pəncərələrində və nümunədən kənar yoxlamalarda iştirak etmir. FR5 natamam il üzrə heç bir məlumatdan istifadə
etmir, buna görə müqavilənin cari qiymətləndirmə (nowcast) düzəliş əmsalı qaydası burada tətbiq olunmur.

---

## 7. Yoxlanılmış spesifikasiyalar — qərar cədvəlləri

**1-ci pillə** (başlanğıclar 2011–2017, ballar ≤ 2019; uyğunluq qiymətləndirmə nümunəsi üzrə yoxlanılır):

<!-- AUTO:t1table -->
| spesifikasiya | meyllərin sayı | seçim RMSE, % | DM/HLN p (ən yaxşıya qarşı) | səviyyə η | fərq η | koherent | qərar |
|---|---|---|---|---|---|---|---|
| gəlir + nisbi qiymət | 2 | 7.18 | — | 1.15 | 1.44 | bəli | SEÇİLİB: ən sadə koherent, digərlərindən pis olmayan səviyyə spesifikasiyası |
| xidmət qiyməti ilə deflyasiya edilmiş gəlir | 1 | 8.14 | 0.681 | 0.43 | 1.29 | xeyr | — |
| yalnız gəlir | 1 | 8.80 | 0.000 | 1.67 | 1.35 | bəli | — |
| gəlir + trend | 2 | 11.86 | 0.000 | 1.64 | 1.35 | bəli | — |
| artım forması: deflyasiya edilmiş gəlir | 1 | 28.98 | 0.078 | — | — | bəli | — |
| yalnız trend | 1 | 63.74 | 0.000 | — | — | xeyr | — |
<!-- /AUTO:t1table -->

**2-ci pillə** (eyni pəncərələr və qayda):

<!-- AUTO:t2table -->
| spesifikasiya | seçim RMSE, f.b. | DM/HLN p (ən yaxşıya qarşı) | meyllərin sayı | ən yaxşıdan əhəmiyyətli dərəcədə pis deyil | koherent | qərar |
|---|---|---|---|---|---|---|
| sabit paylar | 0.77 | 0.011 | 0 | xeyr | bəli | — |
| MNL: yalnız Engel həddi | 0.68 | — | 1 | bəli | xeyr | — |
| MNL: Engel həddi, fərq forması meylləri | 0.75 | 0.381 | 1 | bəli | bəli | — |
| MNL: Engel həddi, koherent olduqda səviyyə meyli, əks halda fərq forması | 0.73 | 0.331 | 1 | bəli | bəli | SEÇİLİB |
| MNL: Engel + öz nisbi qiyməti (məhdudiyyətsiz) | 1.22 | 0.072 | 3 | xeyr | xeyr | — |
| MNL: Engel + öz nisbi qiyməti, tələb qanunu qoyulub | 0.89 | 0.154 | 2 | bəli | xeyr | — |
| LA-AIDS (xətti paylar, Stone indeksi, homogenlik + simmetriya, SUR) | 2.69 | 0.065 | 2 | xeyr | xeyr | — |
<!-- /AUTO:t2table -->

**Engel meyllərinin büzülmə intensivliyi** (eyni pəncərələr və qayda; daha güclü büzülmə = daha sadə):

<!-- AUTO:shrink -->
| spesifikasiya | seçim RMSE, f.b. | DM/HLN p (ən yaxşıya qarşı) | ən yaxşıdan əhəmiyyətli dərəcədə pis deyil | qərar |
|---|---|---|---|---|
| koherentlik qaydası, büzülmə kappa = 0.0 (büzülməsiz) | 0.73 | 0.512 | bəli | — |
| koherentlik qaydası, büzülmə kappa = 0.5 | 0.72 | 0.521 | bəli | — |
| koherentlik qaydası, büzülmə kappa = 1.0 | 0.72 | 0.528 | bəli | — |
| koherentlik qaydası, büzülmə kappa = 2.0 | 0.71 | 0.542 | bəli | — |
| koherentlik qaydası, büzülmə kappa = 4.0 | 0.70 | 0.566 | bəli | — |
| koherentlik qaydası, büzülmə kappa = 8.0 | 0.69 | 0.604 | bəli | — |
| koherentlik qaydası, büzülmə kappa = 16.0 | 0.68 | 0.661 | bəli | — |
| koherentlik qaydası, büzülmə kappa = 32.0 | 0.67 | 0.746 | bəli | — |
| koherentlik qaydası, büzülmə kappa = 64.0 | 0.66 | 0.871 | bəli | — |
| koherentlik qaydası, büzülmə kappa = 128.0 | 0.66 | — | bəli | — |
| koherentlik qaydası, büzülmə kappa = 256.0 | 0.66 | 0.655 | bəli | — |
| koherentlik qaydası, büzülmə kappa = 512.0 | 0.68 | 0.271 | bəli | SEÇİLİB |
| koherentlik qaydası, büzülmə kappa = 1024.0 | 0.70 | 0.058 | xeyr | — |
| koherentlik qaydası, büzülmə kappa = 4096.0 | 0.74 | 0.013 | xeyr | — |
| sabit paylar | 0.77 | 0.014 | xeyr | — |

Seçilmiş: **koherentlik qaydası, büzülmə kappa = 512.0** — ən yaxşıdan statistik əhəmiyyətli dərəcədə pis olmayan ən güclü büzülmə (ən kiçik RMSE: κ = 128); tam büzülmə (sabit paylar) daha pisdir (p = 0,014).
<!-- /AUTO:shrink -->

**Bölgülər:** hər ikisi üçün sabit paylar seçilib (heç bir daha zəngin namizəd əhəmiyyətli dərəcədə üstün deyil).
**Rədd edilmiş digər variantlar:** pay spesifikasiyasının hər kateqoriya üzrə ayrıca seçilməsi (iç-içə test, üstünlük yoxdur);
2022-ci ilədək uzadılmış pandemiya fiktiv dəyişənləri və ya 2020-ci ildən sonrakı sərbəst hədd sürüşməsi (2020-ci ildən əvvəlki
hər bir pəncərədə Əsas spesifikasiya ilə eynidir, ona görə də seçilə bilməz); gəlir əvəzinə qeyri-neft ÜDM (qiymət həddinin
işarəsi yanlışdır). Test pəncərəsinin balları notebook-da yalnız məlumat üçün çap olunur.

---

## 8. Model

### 8.1 1-ci pillə — aqreqat tələb

$$\ln(Q_t/N_t) = \alpha + \eta \ln(Y^d_t/N_t) + \varepsilon \ln(P^s_t/P_t) + \delta_{20}D^{2020} + \delta_{21}D^{2021} + u_t$$

$Y^d$ FR1-in real sərəncamda qalan gəliridir (istehlak deflyatoru); $Q$ pullu xidmətlər həcmidir (xidmətlər deflyatoru);
$P^s/P$ bu ikisi arasındakı fərqdir.

<!-- AUTO:e1 -->
**Seçilmiş spesifikasiya: gəlir + nisbi qiymət.** DOLS(0: cari fərqlər) ilə 2005-2025 nümunəsində qiymətləndirilib (sərbəstlik dərəcəsi 13): ln_income_pc +1,155 (s.x. 0,116), ln_relprice -0,182 (s.x. 0,248), c20 -0,273 (s.x. 0,041), c21 -0,167 (s.x. 0,044). **eg_coint_p = 0,41** — kointeqrasiya yoxdur; t-statistikaları təsviridir. Fərq forması: η = 1,44 (95% etibarlılıq intervalı 0,86–2,02); səviyyə qiyməti bu intervalın **daxilindədir** (uyğundur). 2025-ci il düzəliş əmsalı +0,049; qalığın birinci tərtib avtokorrelyasiyası 0,59 (yalnız diaqnostika).

| qiymətləndirmə | eta (gəlir elastikliyi) | standart xəta | Engle–Granger kointeqrasiya p-dəyəri | sərbəstlik dərəcəsi | p(η = 1) |
|---|---|---|---|---|---|
| gəlir + nisbi qiymət, DOLS səviyyələr 2005–2025 | 1.155 | 0.116 | 0.41 | 13 | 0.204 |
| gəlir + nisbi qiymət, fərq forması | 1.440 | 0.271 | — | 15 | 0.125 |
| yalnız gəlir, DOLS səviyyələr 2000–2025 | 1.665 | 0.062 | 0.13 | 16 | 0.000 |
| yalnız gəlir, DOLS səviyyələr 2005–2025 | 1.443 | 0.145 | 0.30 | 13 | 0.009 |
| yalnız gəlir, fərq forması | 1.350 | 0.246 | — | 21 | 0.169 |

η 1,15–1,67 intervalında dəyişir; fərq forması qiymətləri 1,35–1,44 arasındadır və onların heç biri 5% səviyyəsində η = 1 fərziyyəsini rədd etmir.
<!-- /AUTO:e1 -->

Xidmətlər, ehtimal ki, gəlirə görə elastikdir, lakin **"dəbdəbə" (luxury) xarakteri statistik olaraq təsdiqlənməyib**.

### 8.2 2-ci pillə — on üç növdən ibarət pay sistemi

$$\ln\!\left(\frac{w_{i,t}}{w_{r,t}}\right) = \alpha_i + \beta_i \ln(Q_t/N_t) + \delta_{i}D^{2020,2021} + u_{i,t}, \qquad w_i = \frac{e^{z_i}}{\sum_j e^{z_j}}$$

İstinad növü nəqliyyatdır, 2006–2025. Bu, LA-AIDS deyil, **multinomial-logit pay sistemidir**:
$e_i = 1+\beta_i-\sum_j w_j\beta_j$; $e_i$-lərin paylarla çəkilmiş ortası istənilən əmsallar üçün 1-ə bərabərdir; qiymət həddi
olduqda öz qiymətinə görə elastiklik $\gamma_i(1-w_i)-1$, istinad növü üçün
$\sum_{j\ne r}w_j\gamma_j-1$ olur, çarpaz qiymət elastiklikləri $-w_i\gamma_i$ isə bütün növlər üçün eynidir (IIA).
Seçilmiş sistemdə qiymət həddi yoxdur (öz qiymətinə görə −1, çarpaz 0).

**Uyğunluq (koherentlik) qaydası.** <!-- AUTO:coh -->
12 səviyyə Engel meylindən kointeqrasiya olunanların sayı: 1; **9 meyl eyni tənliyin fərq formasındakı 95% etibarlılıq intervalından kənardadır** (Məişət (fərdi) xidmətləri, Rabitə xidmətləri, Mənzil xidmətləri, Mədəniyyət xidmətləri, Bədən tərbiyəsi və idman, Tibbi xidmətlər, Sanatoriya-sağlamlıq xidmətləri, Hüquqi və bank xidmətləri, Digər pullu xidmətlər); bunlar üçün fərq forması meyli, qalanları (Kommunal xidmətlər, Turizm və ekskursiya xidmətləri, Təhsil xidmətləri) üçün isə DOLS səviyyə meyli istifadə olunur. Tibbi xidmətlər: səviyyə +2,82, fərq -0,21 [-0,77; 0,34]. Mədəniyyət xidmətləri: səviyyə -2,42, fərq +1,05 [0,03; 2,07].
<!-- /AUTO:coh -->

**Büzülmə.** Meyllər (səviyyə və ya fərq formasında, hər biri öz standart xətası $s_i$ ilə) bütün xərc elastikliklərinin
1-ə bərabər olduğu ümumi qiymətə doğru büzülür: kənarlaşmalar
$d_i=\beta_i-\sum_j w_j\beta_j$ $1-B_i$-yə vurulur, burada $B_i=\kappa s_i^2/(\kappa s_i^2+\hat\tau^2)$,
$\hat\tau^2$ isə momentlər metodu ilə qiymətləndirilmiş növlərarası dispersiyadır; κ = 0 büzülmənin olmaması, κ → ∞ isə sabit
paylar deməkdir. Qeyri-dəqiq meyllər daha çox büzülür. κ §7-də seçilir.

**Pandemiya qırılması (səviyyə meylləri).**

<!-- AUTO:pandemic -->
| variant | mədəniyyət beta (səviyyə) | tibbi beta (səviyyə) | təhsil beta (səviyyə) | kommunal beta (səviyyə) | seçim RMSE, f.b. (pəncərələr ≤2019), səviyyə sistemi |
|---|---|---|---|---|---|
| baza: 2020, 2021 dummy-ləri | -2.42 | 2.82 | 0.95 | 0.58 | 0.68 |
| dummy-lər 2022-yə qədər genişləndirilib | -2.60 | 3.48 | 1.45 | 0.91 | 0.68 |
| 2020-dən sonra sabitin sürüşməsi (qırılma) + 2020, 2021 dummy-ləri | 0.00 | 1.15 | 0.59 | -0.65 | 0.68 |
<!-- /AUTO:pandemic -->

### 8.3 Qiymət reaksiyaları (seçilməmiş variantlar)

Məhdudiyyətsiz, qiymətlə genişləndirilmiş sistem qiymətləri inzibati qaydada tənzimlənən xidmətlər (kommunal xidmətlər,
təhsil, mədəniyyət, tibbi xidmətlər) üçün öz qiymətinə görə müsbət elastikliklər verir. Orada γ = 0 və digər növlərdə γ ≤ 1
qoyulduqda sistem seçilmir; endogenlik β-ya keçir. `FR5_nonselected_own_price_elasticities_*.csv` fayllarına bax.

### 8.4 Xərc elastiklikləri — zəif əsaslandırılmış sıralama

2025-ci il paylarında, proqnoz sistemi üzrə (uyğunluq qaydası + büzülmə), 90%-lik parametr zolaqları ilə, habelə bütünlüklə
səviyyə formalı və bütünlüklə fərq formalı sistemlərin verəcəyi sıralamalarla birlikdə:

<!-- AUTO:elast -->
| xidmət | e_i (proqnoz sistemi) | 5% | 95% | sıra | sıra, hamısı səviyyə | sıra, hamısı fərq forması |
|---|---|---|---|---|---|---|
| Mənzil xidmətləri | 1.04 | 0.99 | 1.09 | 1 | 8 | 8 |
| Digər pullu xidmətlər | 1.04 | 0.99 | 1.09 | 2 | 12 | 3 |
| Hüquqi və bank xidmətləri | 1.03 | 0.97 | 1.08 | 3 | 11 | 7 |
| Bədən tərbiyəsi və idman | 1.03 | 0.97 | 1.08 | 4 | 10 | 1 |
| Mədəniyyət xidmətləri | 1.03 | 0.97 | 1.08 | 5 | 13 | 2 |
| Sanatoriya-sağlamlıq xidmətləri | 1.02 | 0.97 | 1.08 | 6 | 9 | 4 |
| Təhsil xidmətləri | 1.02 | 0.97 | 1.07 | 7 | 2 | 6 |
| Turizm və ekskursiya xidmətləri | 1.02 | 0.97 | 1.07 | 8 | 3 | 5 |
| Kommunal xidmətlər | 1.02 | 0.98 | 1.06 | 9 | 4 | 11 |
| Nəqliyyat xidmətləri | 1.02 | 1.00 | 1.04 | 10 | 5 | 9 |
| Tibbi xidmətlər | 1.02 | 0.97 | 1.07 | 11 | 1 | 10 |
| Rabitə xidmətləri | 1.01 | 0.96 | 1.05 | 12 | 6 | 13 |
| Məişət (fərdi) xidmətləri | 0.85 | 0.81 | 0.90 | 13 | 7 | 12 |
<!-- /AUTO:elast -->

Sıralama meylin hansı qiymətinə etibar edilməsindən asılıdır və **zəif əsaslandırılıb**. Seçilmiş büzülmə güclüdür, ona görə
də proqnoz sisteminin elastiklikləri 1-ə yaxındır və növlər üzrə proqnozlar mütənasib artımdan az fərqlənir (§10):
məlumatlar daha kəskin sıralamanı dəstəkləmir.

### 8.5 İnstitusional bölgülər

<!-- AUTO:splits -->
Hər iki bölgü 2025-ci ilin dəyərlərində sabit paylarla proqnozlaşdırılır (fərdi sahibkarlar 24,87%, dövlət 22,19%). 2030-cu il üçün Əsas ssenari dəyərləri: hüquqi şəxslər 16 192, fərdi sahibkarlar 5 361, dövlət 4 783, qeyri-dövlət 16 770 mln manat. 2030-cu il üçün 90% zolaqlar: fərdi sahibkarların payı 20,1–28,9%, dövlətin payı 19,7–28,2%.
<!-- /AUTO:splits -->

---

## 9. Həll və validasiya

Sistem blok-rekursivdir; FR1 bütün ssenarilər üzrə gəliri, əhalini (`pop`) və iki deflyatoru təqdim edir.
Düzəliş əmsalları hər tənliyin sabit saxlanılan 2025-ci il qalığıdır; növlər üzrə nisbi qiymətlər 2025-ci il səviyyəsində
saxlanılır. Model 2025-ci ili dəqiq təkrarlayır. On bir arifmetik yoxlamanın hamısı ödənilir (onlar konstruksiyaya görə ödənilir).

**Nümunədən kənar yoxlamalar** (bütün qərar qaydası kəsim ilinədək olan məlumatlara yenidən tətbiq edilir; paylar simulyasiya
olunmuş yekunla idarə olunur; sabit artım müqayisə meyarı = kəsimdən əvvəlki beş il, burada 2008–13 neft bumunun son mərhələsidir):

<!-- AUTO:holdout -->
| spesifikasiya | A: pandemiyadan əvvəl, 2014–2019 | B: test pəncərəsi, 2020–2025 |
|---|---|---|
| 1-ci pillə spesifikasiyası | xidmət qiyməti ilə deflyasiya edilmiş gəlir | xidmət qiyməti ilə deflyasiya edilmiş gəlir |
| 1-ci pillə qiymətləndirmə üsulu | OLS (DOLS üçün sərbəstlik dərəcəsi çatmır) | DOLS(0: cari fərqlər) |
| sabit artım tempi, % | 9.44 | 2.24 |
| sabit artım pəncərəsi | 2008-2013 | 2014-2019 |
| RMSE, % | 4.88 | 12.82 |
| Theil U (təsadüfi gəzişməyə qarşı) | 0.41 | 1.01 |
| Theil U (sabit artıma qarşı) | 0.18 | 0.69 |
| son il xətası, % | 8.74 | -1.38 |
| qiymətləndirilən illər | 2014-2019 | 2022–2025 (2020–21 çıxılıb) |
| 2-ci pillə spesifikasiyası | sabit paylar | koherentlik qaydası, büzülmə kappa = 512.0 |
| paylar RMSE, f.b. | 0.79 | 2.38 |
| paylar: Theil U (təsadüfi gəzişməyə qarşı) | 1.00 | 1.00 |
| təsadüfi gəzişmədən yaxşı olan növlərin sayı | 0 | 3 |
| RMSE, % (pandemiya illəri daxil) | — | 18.92 |
| Theil U təsadüfi gəzişməyə qarşı (pandemiya daxil) | — | 0.82 |
| Theil U sabit artıma qarşı (pandemiya daxil) | — | 0.68 |
<!-- /AUTO:holdout -->

**FR1 ilə müqayisə.** <!-- AUTO:fr1gap -->
FR5 bu sıra üzrə FR1-in öz proqnozundan 2026-cı ildə +0,67%, 2030-cu ildə +1,06%, ən çox isə +1,87% (2028) fərqlənir. Hər ikisi 2025-ci ilin eyni dəyərindən başlayır və eyni FR1 amillərindən istifadə edir, lakin tənliklər fərqlidir: bu fərq təsdiq deyil, modelləşdirmədəki real fərqdir.
<!-- /AUTO:fr1gap -->

---

## 10. Əsas ssenari üzrə proqnoz 2026–2030

<!-- AUTO:forecast -->
| | 2025 | 2030 | illik |
|---|---|---|---|
| Həcm, 2015-ci il qiymətləri ilə mln manat | 8 735 | 10 650 | **+4.04%** |
| Dəyər, cari qiymətlərlə mln manat | 14 957 | 21 554 | **+7.58%** |

Həcmin illik artımı: 2026 +0,64%, 2027 +5,55%, 2028 +4,70%, 2029 +5,01%, 2030 +4,41%. FR1 Əsas ssenarisində adambaşına real gəlir: 2026 +0,04%, 2027 +4,17%, 2028 +3,46%, 2029 +3,72%, 2030 +3,21%; xidmətlər deflyatorunun artımı orta hesabla ildə +3,40%; xidmətlərin nisbi qiyməti 2030-cu ilədək -0,047 log bəndi dəyişir.
<!-- /AUTO:forecast -->

**Növlər üzrə həcm artımı onların öz tarixi ilə müqayisədə** (ildə, %):

<!-- AUTO:types -->
| növ | ad | proqnoz ortası 2026–30, % | proqnozun maks. ili, % | 2010–19, % | 2021–25, % | ən yaxşı 5 illik orta, % | pəncərə | ən yaxşı 5 illiyi aşır |
|---|---|---|---|---|---|---|---|---|
| Mənzil xidmətləri | Mənzil xidmətləri | 4.18 | 5.74 | -1.06 | 20.59 | 51.93 | 2005-2010 | xeyr |
| Digər pullu xidmətlər | Digər pullu xidmətlər | 4.18 | 5.74 | 7.65 | 7.30 | 100.30 | 2006-2011 | xeyr |
| Hüquqi və bank xidmətləri | Hüquqi və bank xidmətləri | 4.14 | 5.69 | -4.01 | 8.60 | 78.20 | 2005-2010 | xeyr |
| Bədən tərbiyəsi və idman xidmətləri | Bədən tərbiyəsi və idman | 4.14 | 5.68 | 8.04 | 13.08 | 79.97 | 2005-2010 | xeyr |
| Mədəniyyət xidmətləri | Mədəniyyət xidmətləri | 4.13 | 5.68 | 7.36 | 14.47 | 61.25 | 2005-2010 | xeyr |
| Sanatoriya-sağlamlıq xidmətləri | Sanatoriya-sağlamlıq xidmətləri | 4.13 | 5.68 | 6.58 | 24.92 | 44.52 | 2005-2010 | xeyr |
| Təhsil xidmətləri | Təhsil xidmətləri | 4.13 | 5.67 | 6.81 | 22.90 | 45.52 | 2005-2010 | xeyr |
| Turizm və ekskursiya xidmətləri | Turizm və ekskursiya xidmətləri | 4.13 | 5.67 | 11.47 | 30.77 | 34.46 | 2006-2011 | xeyr |
| Kommunal xidmətlər | Kommunal xidmətlər | 4.12 | 5.66 | 5.92 | 7.15 | 9.31 | 2005-2010 | xeyr |
| Nəqliyyat xidmətləri | Nəqliyyat xidmətləri | 4.12 | 5.65 | 6.18 | 16.14 | 25.94 | 2005-2010 | xeyr |
| Tibbi xidmətlər | Tibbi xidmətlər | 4.11 | 5.64 | 15.05 | 15.64 | 51.14 | 2005-2010 | xeyr |
| Rabitə xidmətləri | Rabitə xidmətləri | 4.06 | 5.58 | 9.09 | 6.95 | 22.19 | 2005-2010 | xeyr |
| Məişət xidmətləri | Məişət (fərdi) xidmətləri | 3.50 | 4.77 | 3.43 | 11.25 | 16.39 | 2005-2010 | xeyr |
| CƏMİ | CƏMİ | 4.04 | 5.55 | 4.67 | 9.87 | 29.34 | 2003-2008 | xeyr |

Qeyd edilənlər (proqnoz ortası növün öz ən yaxşı beş illik ortasından yuxarıdır): yoxdur.
<!-- /AUTO:types -->

**Qeyri-müəyyənlik.** <!-- AUTO:bands -->
*Ehtiyat: yalnız 9 birgə tarixi qalıq yolu (başlanğıc illəri 2006–2014) istifadə oluna bilir; zolaqlar göstərici xarakteri daşıyır.* 1 000 təkrarlama (mərkəzləşdirilmiş yollar, işarə məhdudiyyəti ilə parametr çəkilişləri — E1 çəkilişlərinin 22,8%-i rədd edilir — və FR1-in 500 makro çəkilişi): 2030-cu ildə həcmin 90% zolağı 8 589–14 144 mln manat (median 10 619); həcmin orta artımı -0,3% ilə +10,1% arası (median +3,98%); dəyərin orta artımı +1,5% ilə +15,7% arası (median +7,74%). Yalnız FR5-in öz qalıq və parametr qeyri-müəyyənliyi: +2,2% ilə +6,7% arası. E1 və bölgü yollarının öz tam nümunələri üzrə birləşdirildiyi variant: həcm -0,6% ilə +11,2% arası, dəyər +1,3% ilə +16,9% arası. Kvartillərarası zolağın daxilində olan nöqtəvi proqnozlar: həcm 5/5 il, dəyər 5/5, paylar 64/65 növ-il.
<!-- /AUTO:bands -->

<!-- AUTO:scen -->
**Ssenarilər** (2030-cu ildə həcm): Əsas 10 650, Mənfi 10 096, İslahat 11 191 mln manat — 10,9% diapazon; həcmin artımı: Əsas +4,04%, Mənfi +2,94%, İslahat +5,08%; dəyərin artımı: Əsas +7,58%, Mənfi +6,23%, İslahat +8,85%.
<!-- /AUTO:scen -->

## 11. Rıçaqlar

<!-- AUTO:levers -->
| rıçaq | həcm, 2030 | həcm, Əsas ssenariyə nisbətən % | dəyər, Əsas ssenariyə nisbətən % |
|---|---|---|---|
| seçilmiş spesifikasiya (gəlir + nisbi qiymət), eta = 1.44: onun fərq forması qiymətləndirməsi | 11 094 | 4.17 | 4.17 |
| alternativ spesifikasiya: xidmət qiyməti ilə deflyasiya edilmiş gəlir (DOLS 2005–2025; koherent deyil), eta = 0.43, eps = -0.43 | 9 708 | -8.84 | -8.84 |
| alternativ spesifikasiya: yalnız gəlir (DOLS 2000–2025), eta = 1.67, eps = +0.00 | 11 361 | 6.68 | 6.68 |
| xidmətlərin nisbi qiyməti 10% yüksək (tarif rıçağı) | 10 467 | -1.72 | 8.11 |
| xidmətlərin nisbi qiyməti 10% aşağı | 10 856 | 1.94 | -8.26 |
| əhali artımı 0.3 f.b. aşağı | 10 675 | 0.23 | 0.23 |
| əhali artımı 0.3 f.b. yüksək | 10 625 | -0.23 | -0.23 |
| düzəliş əmsalları sabit yarımsönmə dövrü ilə sönür (1 il) | 10 158 | -4.62 | -4.62 |
| növlər üzrə nisbi qiymətlər: 2020–25 meyli davam edir, 0.5 sönmə ilə | 10 650 | 0.00 | 0.00 |
| növlər üzrə nisbi qiymətlər: inzibati tariflər ildə +2% | 10 650 | 0.00 | 0.00 |

Növlər üzrə nisbi qiymət rıçaqları yalnız növlərin daxilində həcm/qiymət bölgüsünü dəyişir; məsələn, rabitə xidmətlərinin 2026-cı ildə həcm artımı Əsas ssenaridə +0,64%, 2020–25-ci illərin qiymət dreyfi davam etdirilsə +6,10% olur.
<!-- /AUTO:levers -->

Alternativ spesifikasiyalar parametri deyil, tənliyi dəyişir və belə olduqları işarələnir. Düzəliş əmsallarının sönməsi halı
yalnız həssaslıq təhlilidir.

## 12. Məhdudiyyətlər

1. **Proqnoz FR1-in gəlir və qiymət trayektoriyaları ilə müəyyən edilir.**
2. **Gəlir elastikliyi bir diapazondur** və kointeqrasiya əlaqəsi olmayan səviyyə münasibətlərindən alınır; "dəbdəbə" (luxury)
   xarakteri təsdiqlənməyib.
3. **Uyğunlaşma dinamikası yoxdur** (gecikmiş asılı dəyişənə icazə verilmir).
4. **Növlərin sıralaması zəif əsaslandırılıb**; büzülmə onu ümumi elastikliyə doğru sıxlaşdırır.
5. **IIA**, habelə seçilmiş pay sistemində qiymət həddinin olmaması.
6. **Növlər üzrə nisbi qiymətlər sabit saxlanılır** — rıçaqlar kimi təqdim olunur.
7. **Düzəliş əmsalları sabit saxlanılır**; sönmə yalnız həssaslıq təhlilidir.
8. **Yelpik qrafikləri doqquz mərkəzləşdirilmiş birgə trayektoriyaya əsaslanır** — yalnız indikativdir.
9. **Aqreqat göstərici 2022–2025 test pəncərəsində təsadüfi gəzişmədən üstün deyil** (§9).
10. **Regional məlumatlar uzlaşdırıla bilmədi** (F5); "digər pullu xidmətlər" kateqoriyasında qırılmalar var; ev təsərrüfatlarının
    müayinəsi məlumatlarından istifadə olunmur.

### Növbəti buraxılışı (vintage) nə yaxşılaşdırardı

- Ev təsərrüfatlarının büdcə müayinəsinin mikroməlumatları.
- Regional sıraların milli yekunla uzlaşdırılması (F5).
- Hər xidmət növü üzrə dərc olunmuş qiymət indeksi və inzibati qaydada tənzimlənən tariflərin təqvimi.
- Rəsmi əhali proqnozu.
- 2006-cı ildən əvvəlki dövr üçün "digər pullu xidmətlər" üzrə uyğunlaşdırılmış geriyə doğru sıra.

## 13. Nəticə faylları

`FR5.ipynb` — əvvəldən sona qədər 0 xəta ilə icra olunub; onun sonuncu kod xanası bu sənədin rəqəmsal bloklarını yenidən
generasiya edir. `output/` qovluğundakı CSV fayllarına daxildir: `FR5_forecast_long.csv`, `FR5_institutional_split.csv`,
`FR5_demand_system_coefficients.csv` (istifadə olunan əmsallar, s.x. ilə), `FR5_e1_coefficients.csv`,
`FR5_expenditure_elasticities.csv`, `FR5_income_elasticity_range.csv`,
`FR5_aggregate_specification_selection.csv`, `FR5_demand_system_specification_selection.csv`,
`FR5_engel_shrinkage_selection.csv`, `FR5_engel_level_vs_difference.csv`,
`FR5_type_growth_vs_history.csv`, `FR5_own_price_elasticities_forecast_system.csv`, `FR5_nonselected_*`,
`FR5_type_ranking_level_vs_difference_*.csv`, `FR5_holdout_validation.csv`, `FR5_fr1_comparison.csv`,
`FR5_fr1_drivers_baseline.csv`, `FR5_fan_*.csv`, `FR5_sensitivity_levers.csv`, `FR5_type_price_levers.csv`,
`FR5_equation_audit.csv`, `FR5_identity_checks.csv`, `FR5_rejected_specifications.csv` və DSK tarixi məlumatları.

**v2 (Hissə 19):** `FR5_equations.json` (tənliklər reyestri), `FR5_indicator_catalog.csv`, `FR5_forecast_tidy.csv`, `FR5_not_forecast.csv`, `FR5_robustness_summary.csv`, `FR5_coef_sensitivity.csv`, `FR5_strings_az.csv`, `engine/FR5_state.json` (+ `.npz`); ssenari mühərriki `microlib/engines/fr5.py`. Notebook `miis-model` kernel-i ilə işləyir (83 xana, 59 kod).
