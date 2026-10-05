> **İngilis dilində (English version):** [FR10_Methodology.md](../FR10_Methodology.md). Rəqəmlərin yazılışı: mətndə onluq kəsr vergüllə, minliklər boşluqla ayrılır; cədvəllərdə, düsturlarda, kodda və fayl adlarında onluq kəsr proqram çıxışında olduğu kimi nöqtə ilə verilir. `AUTO` işarələri arasındakı bloklar hər icrada ingiliscə sənəddən Azərbaycan dilinə köçürülür: `run_all.py` FR10 mərhələsi uğurla başa çatdıqdan sonra `microlib/docgen_az_fr10_fr12.py` faylını çağırır.

# FR10 — Müəssisələrin və istehsalların maliyyə vəziyyəti, istehsal səmərəliliyi və bazar mövqeyi
## Struktur metodologiya, göstəricilər sistemi və beşillik proqnoz

**MİİS modulu 15.5.2 — Mikroiqtisadi təhlil və proqnozlaşdırma**
Azərbaycan Respublikasının İqtisadiyyat Nazirliyi

`FR10.ipynb` faylını müşayiət edən sənəd. **FR1** (sektor buraxılışı, qiymətlər, makroiqtisadiyyat), **FR3** (əmək haqqı) və
**FR4** (məşğulluq) modullarına əsaslanır.

---

## Yenidənbaxma / vəziyyət qeydi (2026-10-05, v2)

**v2 A qatının heç bir nəticəsini dəyişmədən aşağıdakıları əlavə edir:** (1) notebook-da qiymətləndirilən bütün
tənlikləri əhatə edən tənliklər reyestri `output/FR10_equations.json` (Azərbaycan dilində tam reqressiya nəticəsi,
diaqnostika, rekursiv / bir ili çıxarmaqla dayanıqlıq yoxlamaları, nümunədən kənar yoxlama blokları), (2) göstəricilər
kataloqu və hər komponent, ssenari və il üzrə tam proqnoz cədvəli, (3) proqnozu dəqiq təkrarlayan və istifadəçiyə FR1-in
sürücü yollarını, proqnoz əmsallarını və rıçaqları dəyişməyə imkan verən ssenari mühərriki `microlib/engines/fr10.py`,
(4) dayanıqlıq xülasəsi və əmsallar üzrə tornado diaqramı, (5) CSV fayllarındakı bütün ingiliscə sətirlərin Azərbaycan
dilində variantları (məhsullar və yerlər üçün DSK-nın rəsmi adları) və (6) yüklənmiş istənilən müəssisə paneli üzərində
işləyən **B qatında müəssisə səviyyəsində tam ekonometrik təhlil** (§15.1) — hazırda SİNTETİK panel üzərində; bütün
nəticələr su nişanı ilə işarələnir və `synthetic: true` kimi qeydə alınır. Ətraflı: §19.

*Xülasə (AZ):* v2 tənliklər reyestrini, göstərici kataloqunu, tam proqnoz cədvəlini, ssenari mühərrikini, dayanıqlıq
xülasəsini və B qatında müəssisə səviyyəsində tam ekonometrik təhlili əlavə edir; A qatının nəticələri dəyişmir. B qatı
hazırda **sintetik məlumat — texniki nümayiş** üzərində işləyir.

## Yenidənbaxma / vəziyyət qeydi (2026-10-05, v2.1 — məlumat bütövlüyü üzrə düzəlişlər)

**Nə səhv idi.** Sahə üzrə real buraxılış (`output_real_mn_AZN_2015`) və sahə deflyatoru (`deflator_2015_1`) DSK-nın
həcm indeksləri (cədvəl 009, vərəq 9.1) əsasında 2015-ci il nominal buraxılışından zəncirlənir. Bir neçə kiçik sahədə
DSK indeksi sahənin öz nominal buraxılışı ilə uyğun gəlmir — məsələn, elektrik avadanlığı (27), 2020: nominal buraxılış
7% azaldığı halda indeks 8 500% (nəzərdə tutulan deflyator ÷ 100); əczaçılıq məhsulları (21), 2020: 11 200%; avtomobillər
(29), 2010: 84 400% və 2018: 31 000%. Dərc olunduğu kimi zəncirləndikdə 2025-ci ildə real buraxılış 27-ci sahədə nominal
buraxılışın 429 mislinə, 21-ci sahədə 195 mislinə və 16-cı sahədə 44 mislinə bərabər idi; bunun nəticəsində proqnoz
27-ci sahəni 2030-cu ildə təxminən 186 mlrd manata (2015-ci il qiymətləri ilə) — ölkənin real ÜDM-indən çox —
çatdırırdı, bir işçiyə düşən əmək məhsuldarlığı 61 mln manat olurdu, məhsul həcmləri isə 2025-ci ildən 2026-cı ilə
+181%-dək sıçrayırdı. Bu qüsur v2-dən əvvəl də mövcud idi.

**Qayda (Hissə 5.1, alətlər dəstində `validate_volume_index`).** Zəncirləmədən əvvəl hər sahə-il indeksi yoxlanılır.
**T1:** nəzərdə tutulan deflyator dəyişməsi (N_t / N_t−1) / (I_t / 100) ×1/3…×3 intervalından kənardadır. **T2** (T1-dən
sonra, 2015-ci ildən hər iki istiqamətə doğru): sahə deflyatorunun emal sənayesi (C bölməsi) deflyatoruna nisbəti
(2015 = 1) 1/6…6 intervalından kənardadır. Hər iki interval T1-in heç vaxt işarələmədiyi sahələrin zərfindən bir qədər
kənarda yerləşir (rəqəmlər aşağıdakı blokdadır), buna görə qayda 2005–2025 dövründə normal davranan sahəyə toxuna
bilməz. Yoxlamadan keçməyən indeks sahənin nominal artımının həmin ilin emal sənayesi deflyatoru dəyişməsinə bölünməsi
ilə əvəz olunur (sahənin nisbi qiyməti həmin ildə sabit saxlanılır). Əvəz olunan nöqtələr işarələnir: `FR10_forecast_tidy.csv`
faylında `imputed` = True və kataloqda `imputed_years` (real buraxılış və əmək məhsuldarlığı üçün real səviyyəsi əvəz
olunmuş həlqə vasitəsilə hesablanan il); **F15** tapıntısı (ingilis və Azərbaycan dillərində) əvəz olunmuş hər sahə-ili
dərc olunmuş indeksi ilə birlikdə sadalayır, `FR10_volume_index_validation.csv` faylı isə təfərrüatları verir. Notebook
bundan sonra hər sahənin hər ildə hər iki yoxlamadan keçdiyini və hər sahənin 2030-cu il real buraxılışının C bölməsinin
real buraxılışından aşağı qaldığını yoxlayır (assert).

**Təsir.** Proqnozda istifadə olunan heç bir tənliyin əmsalı dəyişmir: pay sistemləri, əlaqəli sektorlar üzrə
birləşdirilmiş model, neft emalı bloku, mədənçıxarma qaydaları və regional sistem nominal paylar, neft emalı deflyatoru
və FR1-in sürücüləri əsasında qiymətləndirilir. Dəyişənlər: təsirə məruz qalan sahələrin real buraxılışı, deflyatoru,
əmək məhsuldarlığı, TFP-si və artımın dekompozisiyası — həm tarixdə, həm də proqnozda (qeyri-neft real buraxılışı =
nominal ÷ (2025 deflyatoru × FR1 indeksi), buna görə 2025 deflyatoru düzəlişi 2026–2030-cu illərə ötürür); amillər
paneli (proqnozda istifadə olunmur, §10); real buraxılış üzrə nümunədən kənar yoxlama göstəriciləri (§12); inandırıcılıq
işarələri (§14).
Nominal buraxılış, paylar, bölmələr, regionlar — deməli, FR12-nin giriş məlumatları da — dəyişmir.

**v2.1-də həmçinin.** (i) **Məhsullar** 2025-ci il faktiki səviyyəsinə lövbərlənir (sabit baza düzəliş əmsalı; natamam
il üzrə məhsul məlumatları olmadığından sönən artım tətbiq olunmur); 2023–25-ci illərin orta intensivliyi ilə 38 məhsul
2025-ci ildən 2026-cı ilə 25%-dən çox sıçrayırdı. (ii) Meyli empirik Bayes üsulu ilə büzülən 13 **regional tənlik**
indi `eb_shrinkage` məhdudiyyətini (`imposed: true`, qiymət, apriori orta, çəki, κ, τ²) və büzülmüş əmsalda
`fixed: true` işarəsini daşıyır. (iii) **Ssenari mühərriki** zəncirvari icrada (`chain.run_chain`) FR4-ün muzdlu işçilər
yollarını yuxarı axındakı FR4 nəticəsindən götürür, beləliklə FR4-dəki dəyişiklik FR10-un məşğulluğuna və əmək
məhsuldarlığına çatır; FR3 FR10 tərəfindən istifadə olunmur (F13).

<!-- AUTO:v21 -->
Həcm indekslərinin yoxlanması: **15 sahədə 64 sahə-il indeksi əvəz olunub** (T1 41, T2 23; 2005–2025 dövründə 29). Zolaqlar T1-in heç vaxt işarələmədiyi 17 sahə əsasında müəyyən edilir: onların 1996–2025 dövründə deflyatorunun bir illik dəyişmələri ×0,34–×2,85 intervalındadır (T1 zolağı ×1/3–×3), 2005–2025 dövründə emal sənayesinə nisbətən deflyatorları isə 0,26–5,24 intervalındadır (T2 zolağı 1/6–6). Düzəlişdən sonra hər sahə hər ildə hər iki yoxlamadan keçir və bütün ssenarilərdə hər sahənin 2030-cu il real buraxılışı C bölməsinin real buraxılışından aşağıdır (ən böyüyü: 06, 13 084, müqayisədə 18 374+ mln manat, 2015-ci il qiymətləri ilə). Tam siyahı: `FR10_volume_index_validation.csv`; sahələr üzrə deflyator diapazonları: `FR10_branch_deflator_check.csv`.

| nace2 | sahə | əvəz olunub (il, test, dərc olunmuş indeks) | real/nominal 2025, dərc olunmuş indekslər | real/nominal 2025, yoxlanılmış | real buraxılış 2030 (Əsas), mln manat, 2015 qiymətləri ilə | əmək məhsuldarlığı 2030, min manat, 2015 qiymətləri ilə |
|---|---|---|---|---|---|---|
| 07 | Metal filizlərinin hasilatı | 2000 (T1, 631.7), 2003 (T1, 829.3), 2008 (T1, 159.7) | 0.22 | 0.22 | 151.61 | 64.17 |
| 14 | Geyim | 1998 (T2, 82.6) | 1.31 | 1.31 | 408.36 | 74.15 |
| 16 | Ağac emalı | 1997 (T1, 21.1), 1999 (T2, 103.1), 2000 (T1, 194.5), 2013 (T1, 91.6), 2014 (T1, 305.9), 2020 (T2, 256), 2023 (T1, 165.1), 2024 (T2, 125.9) | 44.24 | 4.20 | 248.50 | 299.81 |
| 17 | Kağız və karton | 1999 (T2, 171), 2002 (T2, 61.3) | 0.31 | 0.31 | 134.04 | 55.55 |
| 21 | Əczaçılıq məhsulları | 2011 (T2, 83.7), 2016 (T1, 122.4), 2020 (T1, 11200) | 194.91 | 0.96 | 45.18 | 75.36 |
| 22 | Rezin və plastik kütlə | 1996 (T1, 77.8), 1998 (T2, 80.5), 1999 (T2, 40.3), 2000 (T2, 76.7), 2001 (T1, 52.9), 2002 (T2, 86.9), 2004 (T2, 126.5) | 1.75 | 1.75 | 1 808.95 | 246.05 |
| 25 | Hazır metal məmulatları | 1996 (T1, 85.7) | 0.79 | 0.79 | 901.99 | 128.06 |
| 26 | Kompüter və elektronika | 2000 (T2, 36.9), 2002 (T2, 54.4), 2004 (T2, 67.5), 2005 (T1, 75.7), 2006 (T2, 64.9), 2007 (T2, 92.3) | 2.26 | 2.26 | 246.17 | 960.74 |
| 27 | Elektrik avadanlığı | 2011 (T1, 72.9), 2016 (T1, 333.8), 2020 (T1, 8500) | 428.67 | 1.11 | 473.61 | 156.84 |
| 28 | Maşın və avadanlıq | 2025 (T1, 84.1) | 1.42 | 0.40 | 81.33 | 28.03 |
| 29 | Avtomobil və qoşqular | 1997 (T1, 112.3), 2000 (T1, 1156.4), 2003 (T1, 119.5), 2006 (T1, 2230.7), 2009 (T1, 23), 2010 (T1, 84400), 2012 (T1, 27.8), 2014 (T1, 158.2), 2017 (T1, 1.2), 2018 (T1, 31000) | 4.17 | 0.76 | 396.34 | 403.44 |
| 30 | Digər nəqliyyat vasitələri | 1996 (T2, 124.6), 1997 (T1, 110.5), 1998 (T2, 114.9), 1999 (T1, 88.2), 2000 (T1, 143), 2002 (T2, 178.6), 2003 (T2, 117.4), 2004 (T1, 97.9), 2005 (T2, 208.2), 2006 (T2, 105.7), 2014 (T1, 339.9), 2021 (T1, 12.5), 2024 (T1, 54.9) | 0.13 | 2.62 | 168.32 | 118.52 |
| 31 | Mebel | 2002 (T1, 47.1), 2010 (T1, 24.1) | 0.87 | 0.87 | 539.85 | 59.79 |
| 33 | Maşın və avadanlığın təmiri və quraşdırılması | 1996 (T1, 104.9) | 0.40 | 0.40 | 683.54 | 65.36 |
| 36 | Su təchizatı, tullantılar | 1996 (T1, 95), 1998 (T1, 89.5), 1999 (T1, 96.6) | 0.57 | 0.57 | 475.23 | 9.47 |

Məhsullar: 2025-ci il faktiki səviyyəsinə lövbərlənib; 2025-ci ildən 2026-cı ilə 25%-dən çox dəyişən məhsulların sayı: 127 məhsuldan 0 (Əsas). Regional pay tənlikləri: 13 əmsal proqnozda istifadə olunan dəyərin əsasında duran qiyməti, apriori ortanı, büzülmə çəkisini, κ və τ²-ni qeyd edən `eb_shrinkage` məhdudiyyətini (`imposed: true`, `fixed: true`) daşıyır.
<!-- /AUTO:v21 -->

*Xülasə (AZ):* v2.1 DSK həcm indekslərinin yoxlanmasını əlavə edir: bəzi kiçik sahələrdə (16, 21, 27, 29, 30 və s.)
indeks sahənin öz nominal buraxılışı ilə uyğun gəlmir, buna görə zəncirlənmiş real buraxılış qeyri-real səviyyələrə
çatırdı. Deflyatorun bir illik dəyişməsi ×1/3…×3 intervalından (T1) və ya emal sənayesi deflyatoruna nisbətən deflyator
1/6…6 intervalından (T2) çıxdıqda indeks nominal artımın emal sənayesi deflyatoru dəyişməsinə bölünməsi ilə əvəz olunur;
əvəz olunan dəyərlər doldurulmuş kimi işarələnir (F15). Proqnozda istifadə olunan tənliklərin əmsalları
dəyişmir. Məhsul proqnozları 2025 faktiki səviyyəsinə bağlanır; regional əmsalların empirik Bayes büzülməsi reyestrdə
məhdudiyyət kimi qeyd olunur; mühərrik FR4 yuxarı axın nəticəsini istifadə edir.

## Yenidənbaxma / vəziyyət qeydi (2026-10-01)

**B qatı əvəz edilə bilən müəssisə paneli faylı üzərində işləyir.** Nazirlik müəssisə məlumatlarını layihə ilə
paylaşmayacaq; öz məlumatlarını öz sisteminə yükləyəcək. Buna görə B qatı `data/firm_panel/` qovluğunu oxuyur: təhvil
verilən `FR10_firm_panel_SYNTHETIC.csv/.xlsx` faylı **sintetikdir** (hər sətir `SYNTHETIC — not real enterprise data`
kimi işarələnib), Nazirlik onu eyni sxemdə `FR10_firm_panel.csv/.xlsx` faylı (və ya `FIRM_PANEL_PATH`) ilə əvəz edir.
Aşağıdakı məlumat rejimi icra zamanı yaradılır; SİNTETİK rejimdə B qatının hər bir nəticəsi `output/FR10_SYNTHETIC_*.csv`
faylıdır, su nişanı daşıyır və tapıntıların heç birində istifadə olunmur. A qatı (müəssisə qrupları: sahələr, ölçü
qrupları, mülkiyyət, regionlar, məhsullar) DSK və iş kitabı məlumatları əsasında artıq işləkdir.

Bu sənəddəki rəqəmlər icranın CSV nəticələrindən **notebook-un sonuncu kod xanası tərəfindən** `AUTO` işarələri
arasında yaradılır, buna görə sənəd nəticələrdən fərqlənə bilməz.

<!-- AUTO:mode_header -->
**B qatının məlumat rejimi: SİNTETİK** — giriş faylı `data/firm_panel/FR10_firm_panel_SYNTHETIC.csv`, 22 495 sətir, 5 255 müəssisə, 24 NACE sahəsi, 2019–2025. Müəssisə paneli **SİNTETİKDİR — real müəssisə məlumatı deyil**; B qatının nəticələri tapıntılar deyil, emal xəttinin nümayişidir.
<!-- /AUTO:mode_header -->

<!-- AUTO:rev -->
Bu icra: 114 DSK cədvəli, 15 bütövlük tapıntısı, mənbə matrisində 52 göstərici (hazırda mövcud 40, sorğu edilib 7, mövcud deyil 5); sahə modeli: Neft emalı məhsulları emal gücü və neft qiyməti ilə, qeyri-neft sahələri əlaqəli sektorlar üzrə birləşdirilmiş modelin (β = 0,219) və sabit payların bərabər çəkili kombinasiyası ilə; regionlar MNL: neft sektoru qarışığı (FR1 mədənçıxarma/emal sənayesi əlavə dəyəri) (κ = 0,5); Əsas ssenaridə sənaye buraxılışı 2026–2030 dövründə ildə +4,21% (nominal); 88 FR10 CSV faylı, onlardan 24 SİNTETİK.
<!-- /AUTO:rev -->

Tətbiq olunan standartlar (FR1–FR5 yoxlamasının dərsləri): gecikmiş asılı dəyişən və dəyişənin öz tarixi əsasında
proqnoz yoxdur; səviyyə əlaqələri MacKinnon-un qalıqlara əsaslanan kointeqrasiya p-dəyərləri ilə DOLS üsulu ilə
qiymətləndirilir; kiçik nümunə üçün HAC və t(n−k) əsasında statistik nəticə; uyğunluq qaydası (öz fərq formasının 95%
etibarlılıq intervalından kənarda qalan səviyyə meyli istifadə olunmur); panellər t(T−1) üzrə Driscoll–Kraay xətaları
və illər üzrə klaster wild bootstrap ilə iki yönlü sabit effektlər üsulu ilə qiymətləndirilir; vahidlərə xas səs-küylü
meyllər intensivliyi kəsimdən əvvəl seçilən empirik Bayes büzülməsi ilə; hər seçim ≤ 2019 sürüşən başlanğıclarda
qiymətləndirilir, 2020–2025 nümunədən kənar yoxlaması toxunulmaz saxlanılır; Theil U həm təsadüfi gəzişməyə, həm də
sabit artıma qarşı; DM/HLN testləri hədəf ili üzrə orta itki əsasında; 2025-ci ilə lövbərlənmiş softmax pay sistemləri;
sabit düzəliş əmsalları; inandırıcılıq hər vahidin öz tarixinə qarşı yoxlanılır; arifmetik eynilik yoxlamaları elə də
adlandırılır.

---

## 1. Tapşırıq

> *Müəssisələrin və istehsalatların maliyyə vəziyyəti, istehsal effektivliyi və bazar paylarının təhlili və
> proqnozlaşdırılması mümkün olmalıdır.*

Müəssisələrin və istehsalların **maliyyə vəziyyətinin, istehsal səmərəliliyinin və bazar mövqeyinin** analitik
qiymətləndirilməsi, müqayisəli təhlili və proqnozlaşdırılması; bir neçə mənbədən müəssisə, maliyyə, istehsal və bazar
göstəricilərinin əlaqələndirilməsi; məqsədlər: fəaliyyət səmərəliliyini müqayisə etmək; istehsalın artımını və ya
azalmasını müəyyən etmək; regionlar, fəaliyyət növləri və məhsullar üzrə müqayisə aparmaq; əsas amilləri müəyyən etmək;
istehsal və bazar göstəricilərini proqnozlaşdırmaq; qərarların qəbuluna dəstək vermək. Nəticə **hansı göstərici üçün
hansı mənbədən hansı məlumatların hansı formada istifadə olunduğunu** konkret göstərməlidir — §5–§7.

Məhdudiyyətlər (FR1–FR5-də olduğu kimi): AR/ARIMA/ARCH/GARCH, gecikmiş asılı dəyişən, dəyişənin öz tarixi əsasında
proqnoz yoxdur; əlaqəli sektorların təsirini göstərən struktur modellər; çatışmayan məlumatlar DSK-dan toplanır;
proqnoz dəqiqliyi proqnoz anında mövcud olan informasiya əsasında sadə müqayisə meyarlarına qarşı yoxlanılır (NFR1).

## 2. Arxitektura

| Qat | Vahidlər | Vəziyyət |
|---|---|---|
| **A — işlək** | 30 sənaye sahəsi (NACE 06–09, 10–33, 35, 36), 4 bölmə, ölçü qrupları, dövlət/qeyri-dövlət, 14 iqtisadi rayon, ~140 məhsul | nəticələr (§8–§14) |
| **B — müəssisə mühərriki** | müəssisə (sxem, validator, əmsallar, Altman Z''-EM, TFP indeksi, NACE × region üzrə bazar payları/HHI/CR4, giriş/çıxış/sağ qalma, həmkarlarla müqayisə, müəssisə proqnozları) | emal xətti yalnız SİNTETİK məlumatlar üzərində sınaqdan keçirilib (§15) |

Əlaqələr: FR1 üç ssenari üzrə mədənçıxarma, emal sənayesi, elektrik enerjisi və su təchizatının real əlavə dəyərini və
deflyatorlarını, neftin ixrac qiymətini, orta əmək haqqını və ümumi məşğulluğu, habelə Əsas ssenari üzrə 500 çəkilişi
verir; FR4 fəaliyyət növləri üzrə muzdlu işçiləri verir; FR3-ün sahələr üzrə əmək haqqı cədvəli oxunur, lakin
səviyyələr üçün istifadə olunmur (F13 tapıntısı).

## 3. Toplanmış məlumatlar

DSK cədvəlləri `stat.gov.az/source/<section>/en/` ünvanından `data/dsk_enterprise/` qovluğuna (sənaye, sahibkarlıq,
statistik reyestr, milli hesablar) yüklənib və sonrakı icralarda diskdən yenidən oxunur; təhlil keşi
(`_fr10_parse_cache.pkl`, fayl ölçüləri və tarixləri üzrə açarlanır) təkrar təhlili ötürür. Bölmələr üzrə vəziyyət:

<!-- AUTO:data -->
| bölmə | DƏRC EDİLMƏYİB (URL HTML səhifəsi qaytarır, HTTP 200) | mövcuddur |
|---|---|---|
| sahibkarlıq | 0 | 29 |
| sənaye | 6 | 60 |
| st_units | 0 | 10 |
| system_nat_accounts | 0 | 15 |

Sahələrin buraxılışı 1996–2025 dövründə dərc olunmuş mədənçıxarma, emal sənayesi və sənaye yekunlarına 0,001% dəqiqliklə cəmlənir; milli hesablar üzrə sahə əlavə dəyəri 0,018% dəqiqliklə; FR1 və DSK üzrə bölmə əlavə dəyəri 2025-ci ildə üst-üstə düşür.
<!-- /AUTO:data -->

İstifadə olunan iş kitabı vərəqləri: `Emal Sənayesi`, `Mədənçıxarma`, `Elektrik enerjisi `, `Su təchizatı` (sahələr,
2016–2025), `DVX üzrə göstəricilər` (r43 vergi borcları, r53–r57 dövriyyə, r111–r129 vergi ödəyicilərinin ölçü
qrupları, r215–r232 mənfəət vergisi və gəlir vergisi bəyannamələri), `Real sektor` (r80, r114–r118 mənbələr üzrə
investisiya; r10 özəl payı), `Regionlar*` (regionlar üzrə müəssisələr, giriş, çıxış, ölçü, sənaye buraxılışı,
2021–2025), `Park`, `KOBİA`, `İnvestisiya təşviqi sənədi `.

## 4. Məlumat bütövlüyü üzrə tapıntılar

<!-- AUTO:integrity -->
| id | tapıntı | sübut | nəticə |
|---|---|---|---|
| F1 | DSK artıq sahələr üzrə əsas fondların yenilənməsi, xaric olması və köhnəlməsi cədvəllərini, eləcə də fondverimi indeksini dərc etmir | 6 URL (017_2en.xls, 017_3en.xls, 017_4en.xls, 017_5en.xls, 017_6en.xls, 017_7en.xls) HTTP 200 kodu ilə HTML səhifə qaytarır; bu bölmə DSK-nın sənaye bölməsinin indeks səhifəsində deaktiv edilib (şərhə alınıb), 017_1/018_1/018_2 nömrəli fayllarda isə hazırda iqtisadi rayonlar üzrə məhsul cədvəlləri yerləşir | Sahələr üzrə yenilənmə və köhnəlmə əmsalları MÖVCUD DEYİL; FR10 alternativ olaraq investisiya normasından (I/GO, DSK 019) və milli hesablar üzrə bölmələr üzrə əsas kapitalın istehlakı və əsas fondlardan (DSK NA 013, 031) istifadə edir (boşluqlar cədvəli) |
| F2 | İş kitabındakı 2025 sahə sütunları DSK məlumatlarından fərqli (ilkin) versiyadır | iş kitabında sənaye üzrə yekun 63,123, DSK-da 63,011 mln manat (+0.18%); sahələr üzrə ən böyük fərqlər: Maşın və avadanlıq +228%, Hazır metal məmulatları -40%, Metallurgiya -20%, Digər nəqliyyat vasitələri -12%; 2016-2024 illərində 0.000% dəqiqliklə üst-üstə düşür | FR10 2025 ili üzrə sahə məlumatlarını DSK-dan götürür; iş kitabının sahə sətirlərindən yalnız DSK ilə uyğun gəldiyi hallarda istifadə olunur |
| F3 | 2010 ilinədək sahələr üzrə investisiyaların cəmi sənaye üzrə yekuna bərabər deyil | 2005-2009 illərində bölüşdürülməmiş investisiya yekunun -3.05% ilə -0.41% arasında; 2010 ilindən dəqiqdir (<0.01%); mədənçıxarma sahəsində xidmətlər üzrə investisiya 2017 ilinədək "-" kimi göstərilib, halbuki bu sahənin buraxılışı ildə 1,342 mln manat olub | Amillər panelində investisiya normalarından 2010 ilindən etibarən istifadə edilir; 2018 ilinədək mədənçıxarma sahəsində xidmətlər üzrə investisiya sıfır deyil, çatışmayan dəyər kimi qəbul edilir |
| F4 | Həcm indeksləri "t." işarəsi ilə min faiz ifadəsində dərc edilib | DSK 009 faylında, məsələn, "7.8 t." (= 2010 ilinin 7 800%-i) yazılışı 9.2 vərəqinin 48 xanasında və 9.1 vərəqinin 4 xanasında rast gəlinir; sadə oxunduqda bu xanalar çatışmayan dəyərə çevrilir | to_num "t." işarəsini nəzərə alır (Hissə 2); real buraxılış yalnız 9.1 ilindən zəncirvari üsulla hesablanır (əvvəlki il = 100) |
| F5 | 2016 ilində milli hesabların gəlir hesabı bölmələr üzrə balanslaşmır | 2016 ilində ƏD - əmək ödənişləri - digər vergilər - ümumi mənfəət = C -22.5, D +7.3, E +15.2 mln manat (cəmi -0.00); digər bütün illərdə dəqiq bərabərlik | C, D, E bölmələri arasında bölüşdürmə xətası; həmin bölmələrin 2016 ilində ümumi mənfəət marjaları bu məbləğlər qədər qeyri-müəyyəndir |
| F6 | Su təchizatında ümumi mənfəət mənfidir; gəlir hesabının yekun sətrində "C" bölmə kodu göstərilib | 2025 ilində E bölməsinin ümumi mənfəəti -155.7 mln manat (əmək ödənişləri 454.3 > əlavə dəyər 301.7); 21 il ərzində 5 il mənfi olub | Xəta deyil, iqtisadi faktdır (subsidiyalaşdırılan kommunal xidmət); yekun sətir kodu ilə deyil, adı ilə müəyyən edilir |
| F7 | DVX-nin "rentabellik" sətri rentabellik deyil, vergi nisbətidir | 2021-2025 illərinin hər birində r223 ödənilməli mənfəət vergisi / çıxılmalardan sonrakı gəlir nisbətinə 0.05 faiz bəndi dəqiqliklə bərabərdir (2.2-2.8%); bəyannamələrdən irəli gələn rentabellik, yəni (çıxılmalardan sonrakı gəlir - gəlirdən çıxılan xərclər) / gəlirdən çıxılan xərclər, 10.0-13.2% təşkil edir; vergiyə cəlb olunan mənfəət ilə bəyan edilmiş zərərin fərqi həmin xalis nəticəyə 7.60 mln manat dəqiqliklə bərabərdir | FR10 komponentlərdən hesablanmış bəyannamə marjasını təqdim edir və r223-ü effektiv vergi nisbəti kimi işarələyir |
| F8 | DVX-nin büdcə təşkilatları sətirləri mikro vergi ödəyiciləri sətirlərini təkrarlayır; mikro vergi ödəyicilərinin sayı pul vahidi ilə göstərilib | 127-129 sətirləri bütün illərdə 123-125 sətirlərinə bərabərdir: Bəli; 123 sətri (say göstəricisi) "mln. manat" kimi işarələnib | Büdcə təşkilatı olan vergi ödəyicilərinin sayı MÖVCUD DEYİL; ölçü qrupları cədvəlində yalnız mikro sətirlərdən istifadə olunur (FR4 F4-də olduğu kimi) |
| F14 | DVX-nin vergi ödəyicilərinin sayı əhali ölçü vahidi (nəfər) ilə göstərilib | 111, 115 və 119 sətirləri (iri, orta və kiçik vergi ödəyicilərinin sayı, məsələn, 2022 ilində 846 iri ödəyici) "min nəfər" kimi işarələnib | Vergi ödəyicilərinin sayı kimi oxunur; ölçü vahidi iş kitabında düzəldilməlidir |
| F9 | 2019 ilinədək iqtisadi rayonlar üzrə sənaye buraxılışının cəmi ölkə üzrə yekuna bərabər deyil, sonrakı illərdə isə ev təsərrüfatlarının sənaye fəaliyyətini də əhatə edir | 14 iqtisadi rayonun cəmi DSK 010 faylı ilə müqayisədə: 2003-2018 illərində -13.9% ilə -1.7% arasında, 2019 ilindən dəqiq; DSK 022 faylında 2019 və sonrakı illər üçün "ev təsərrüfatlarının və qeyri-formal fərdi sahibkarların sənaye fəaliyyəti nəzərə alınmaqla" qeydi verilib | İqtisadi rayonların payları iqtisadi rayonların cəminə görə modelləşdirilir (payların cəmi konstruksiyaya görə birə bərabərdir); 2018/2019 əhatə dəyişikliyi səviyyə qırılmasıdır və iqtisadi rayonların pay tənliklərində pilləli fiktiv dəyişənlə nəzərə alınır |
| F10 | FR1-in 2024 ili üzrə bölmələrin əlavə dəyəri DSK məlumatlarından daha əvvəlki versiyadır | FR1 emal sənayesi əlavə dəyəri (2024) 7,475.5, DSK milli hesablarında (NA) 7,019.4 mln manat (+6.5%); 2025 ilində ikisi tam üst-üstə düşür | FR10 FR1 və DSK məlumatlarının üst-üstə düşdüyü 2025 ilinə bağlanır və 2025 ilindən FR1-dən yalnız artım indeksləri kimi istifadə edir |
| F11 | KOS (SME) göstəriciləri yalnız iki il üzrə mövcuddur; statistik registr yalnız bir tarixə olan vəziyyəti əks etdirir | DSK sahibkarlıq cədvəlləri 2023 və 2024 illərini əhatə edir; st_units cədvəlləri 1 iyul 2026 tarixinə olan vəziyyəti əks etdirir (giriş/çıxış: 2026, yanvar-iyun) | KOS (SME) payları və registr əsasında giriş/çıxış əmsalları modelləşdirilmir, yalnız təqdim olunur: proqnozu müəyyənləşdirmək üçün zaman sırası mövcud deyil |
| F15 | Kiçik sahələrin DSK həcm indeksləri onların öz nominal buraxılışı ilə uyğun gəlmir | 64 sahə-il həcm indeksi (DSK 009, 9.1 vərəqi) 15 sahədə yoxlamadan keçmir: T1 (deflyatorun bir illik dəyişməsi x1/3-x3 intervalından kənar) 41, T2 (emal sənayesi deflyatoruna nisbətən deflyator, 2015 = 1, 1/6-6 intervalından kənar) 23. Əvəz olunanlar (il və dərc olunmuş indeks, əvvəlki il = 100): 07: 2000 631.7, 2003 829.3, 2008 159.7; 14: 1998 82.6; 16: 1997 21.1, 1999 103.1, 2000 194.5, 2013 91.6, 2014 305.9, 2020 256, 2023 165.1, 2024 125.9; 17: 1999 171, 2002 61.3; 21: 2011 83.7, 2016 122.4, 2020 11200; 22: 1996 77.8, 1998 80.5, 1999 40.3, 2000 76.7, 2001 52.9, 2002 86.9, 2004 126.5; 25: 1996 85.7; 26: 2000 36.9, 2002 54.4, 2004 67.5, 2005 75.7, 2006 64.9, 2007 92.3; 27: 2011 72.9, 2016 333.8, 2020 8500; 28: 2025 84.1; 29: 1997 112.3, 2000 1156.4, 2003 119.5, 2006 2230.7, 2009 23, 2010 84400, 2012 27.8, 2014 158.2, 2017 1.2, 2018 31000; 30: 1996 124.6, 1997 110.5, 1998 114.9, 1999 88.2, 2000 143, 2002 178.6, 2003 117.4, 2004 97.9, 2005 208.2, 2006 105.7, 2014 339.9, 2021 12.5, 2024 54.9; 31: 2002 47.1, 2010 24.1; 33: 1996 104.9; 36: 1996 95, 1998 89.5, 1999 96.6. Dərc olunmuş indekslərlə zəncirləndikdə 2025 ilində real / nominal buraxılış nisbəti 429 (27), 195 (21), 44.2 (16) idi | Yoxlamadan keçməyən hər indeks sahənin nominal artımının həmin ilin emal sənayesi deflyatoru dəyişməsinə bölünməsi ilə əvəz olunur (nisbi qiymət sabit saxlanılır); təsirlənən real buraxılış və əmək məhsuldarlığı dəyərləri doldurulmuş kimi işarələnir (FR10_volume_index_validation.csv); indekslər DSK ilə dəqiqləşdirilməlidir |
| F12 | Bəzi illərdə sənayedə dərc edilmiş qeyri-dövlət payı onun öz sahə bölgüsü ilə uyğun gəlmir | buraxılışla çəkilənmiş sahə qeyri-dövlət payları (DSK 010_2 x 010) sənaye üzrə dərc edilmiş yekundan fərqlənir: 2005: -0.8 faiz bəndi, 2013: +6.3 faiz bəndi, 2014: +7.6 faiz bəndi, 2015: +7.9 faiz bəndi, 2016: +6.7 faiz bəndi; digər bütün illərdə fərq 0.15 faiz bəndi daxilindədir | Qeyri-dövlət payının proqnozu sahə strukturu əsasında qurulur (konstruksiyaya görə uyğundur); həmin illər üzrə dərc edilmiş yekun göstərici barədə DSK-ya sorğu göndərilməlidir |
| F13 | FR3-ün sahə əmək haqqı trayektoriyaları 2025 ilinin sahə əmək haqlarına bağlanmayıb və vahid artım tempinə malikdir | FR3 2026 sahə əmək haqqı / DSK 2025 sahə əmək haqqı - 1 nisbəti 29 sahə üzrə -21% ilə +21% arasında dəyişir; 2026-2030 illərində artım hər sahə üçün ildə 7.49-7.49% təşkil edir | FR10 FR1-in orta əmək haqqı indeksini hər sahənin DSK üzrə 2025 əmək haqqına tətbiq edir; səviyyələr üçün FR3-dən istifadə edilmir |
<!-- /AUTO:integrity -->

## 5. Göstəricilər sistemi: hansı məlumatlar, hansı mənbədən, hansı göstərici üçün, hansı formada

Hər göstərici üçün bir sətir; tam sütun dəsti ilə (düstur, ölçü vahidi, tezlik, yenilənmə tezliyi daxil olmaqla)
`output/FR10_data_source_matrix.csv` faylına ixrac olunur. "Hazırda mövcud olan illər" əl ilə yazılmır, oxunan
fayllardan hesablanır. Vəziyyət: *hazırda mövcuddur* — iş kitabında var və ya bu gün DSK-dan yüklənə bilər; *sorğu
edilib* — 24 avqust 2026-cı il tarixli sorğuya daxildir, hələ alınmayıb; *mövcud deyil* — heç bir mənbə onu dərc etmir,
alternativ göstərilir.

İstiqamətlər və vəziyyət üzrə say:

<!-- AUTO:matrix_summary -->
| istiqamət | hazırda mövcuddur | mövcud deyil | sorğu edilib |
|---|---|---|---|
| maliyyə vəziyyəti | 13 | 1 | 5 |
| bazar mövqeyi | 18 | 1 | 1 |
| istehsal səmərəliliyi | 9 | 3 | 1 |
<!-- /AUTO:matrix_summary -->

İnteqrasiya yolları: **faylın yüklənməsi** (DSK `.xls` cədvəllərinin planlı şəkildə əldə edilməsi; cədvəllər mövqeyə
görə deyil, yalnız etiketlərə görə təhlil olunur, cəmlərin uyğunluğu yoxlanılır); **iş kitabının yüklənməsi**
(Nazirliyin iş kitabı vərəq və sətir etiketinə görə oxunur); **məlumat mübadiləsi sazişi + təhlükəsiz API** (müəssisə
və əməliyyat məlumatları üçün DVX, DSMF, DGK, CBAR).

<!-- AUTO:matrix -->
| id | istiqamət | göstərici (azərbaycanca) | göstərici (ingiliscə) | mənbə qurum | məlumat dəsti / cədvəl / sətir | təfərrüat səviyyəsi | hazırda mövcud olan illər | vəziyyət | MİİS-ə inteqrasiya üsulu | analitik istifadə | təqdimat forması | mövcud olmadıqda alternativ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I01 | bazar mövqeyi | Sahənin sənaye məhsulunda payı | Branch share of industrial output | DSK | sənaye 010 | sahə (30) | 1995-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | paylar sistemi, HHI (Hissələr 7, 11) | reytinq cədvəli; yelpik zolaqlı zaman sırası | — |
| I02 | bazar mövqeyi | Emal sənayesində sahənin payı | Branch share of manufacturing output | DSK | sənaye 010 | sahə (24) | 1995-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | MNL paylar sistemi (Hissə 11), proqnoz | yığılmış sahə qrafiki; yelpik qrafiki | — |
| I03 | bazar mövqeyi | Konsentrasiya indeksi (HHİ, CR4) — sahələr | Concentration across branches (HHI, CR4) | DSK | sənaye 010 (hesablanmış) | sənaye / emal sənayesi | 1995-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | bazar strukturu üzrə KPI, proqnoz | idarəetmə panelində KPI kartı | — |
| I04 | bazar mövqeyi | Müəssisə səviyyəsində HHİ | Firm-level HHI / CR4 by NACE x region | DVX / DSMF | müəssisə paneli (24.08.2026 tarixində sorğu edilib) | müəssisə | yoxdur | sorğu edilib | məlumat mübadiləsi sazişi + təhlükəsiz API | B qatında konsentrasiya | istilik xəritəsi NACE x iqtisadi rayon | DSK reyestrindəki iri vahidlərin sayı və KOS-un buraxılışdakı payı əsasında aşağı hədd (Hissə 7.1) |
| I05 | bazar mövqeyi | Qeyri-dövlət bölməsinin payı | Non-state share of output by branch | DSK | sənaye 010_2 | sahə | 1997-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | mülkiyyət tərkibinin proqnozu (Hissə 14) | zaman sırası; KPI kartı | — |
| I06 | bazar mövqeyi | Fəaliyyət göstərən müəssisələrin sayı | Active enterprises by branch and ownership | DSK | sənaye 004-007-008, vərəq 4;7 | sahə x mülkiyyət növü | 1995-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | giriş/xalis giriş dərəcələri, determinantlar paneli | reytinq cədvəli | — |
| I07 | bazar mövqeyi | Ölçü qrupları üzrə müəssisələr | Enterprises by size class | DSK | sənaye 004-007-008, vərəq 8 | sahə x ölçü | 2009-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | ölçü strukturu, konsentrasiya həddi | yığılmış sütun qrafiki | — |
| I08 | bazar mövqeyi | KOB-ların payı (buraxılış, məşğulluq, investisiya) | SME share of output, employment, investment | DSK | sahibkarlıq 001_1, 012, 013, 015 | bölmə x ölçü | 2023-2024 | hazırda mövcuddur (2 il) | fayl endirmə (DSK xls, qrafik üzrə) | sabit saxlanılır (identifikasiya olunmur, F11) | KPI kartı | DVX vergi ödəyicilərinin ölçü qrupları r111-r126 (2022-2025) |
| I09 | bazar mövqeyi | Vergi ödəyicilərinin ölçü qrupları | Taxpayer size classes: count, turnover, employees | DVX | iş kitabı 'DVX üzrə göstəricilər' r111-r126 | ölçü qrupu | 2022-2025 | hazırda mövcuddur | iş kitabının yüklənməsi (İqtisadiyyat Nazirliyi) | ölçü strukturunun çarpaz yoxlanması | cədvəl | — |
| I10 | bazar mövqeyi | Regionun sənaye məhsulunda payı | Regional share of industrial output | DSK | sənaye 022 (və 023 fiziki həcm indeksi) | iqtisadi rayon (14) | 2003-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | regional paylar sistemi (Hissə 12) | xəritə; iqtisadi rayon x il istilik xəritəsi | — |
| I11 | bazar mövqeyi | Regionlarda qeyri-dövlət payı | Non-state share of industrial output by region | DSK | sənaye 024 | region | 2005-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | regional mülkiyyət profili | xəritə | — |
| I12 | bazar mövqeyi | Regionlarda müəssisələrin sayı | Industrial enterprises by region | DSK | sənaye 021 | region | 2005-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | regionlarda bazara giriş dinamikası | xəritə | — |
| I13 | bazar mövqeyi | Yeni yaradılmış / ləğv edilmiş müəssisələr (regionlar) | New and liquidated enterprises by region (all sectors) | DSK (iş kitabı vasitəsilə) | iş kitabı 'Regionlar*' sətirlər 'Müəssisə və təşkilatların sayı', 'Yeni yaradılmış', 'Ləğv edilmiş' | region | 2021-2025 | hazırda mövcuddur | iş kitabının yüklənməsi (İqtisadiyyat Nazirliyi) | giriş/çıxış dərəcələri | xəritə; cədvəl | — |
| I14 | bazar mövqeyi | Yaradılmış və ləğv edilmiş vahidlər (fəaliyyət növləri) | Created and liquidated statistical units by activity | DSK | st_units 2_1-2_3 (1 iyul 2026 tarixinə vəziyyət) | bölmə, iqtisadi rayon, mülkiyyət növü | H1 2026 | hazırda mövcuddur (anlıq vəziyyət) | fayl endirmə (DSK xls, qrafik üzrə) | giriş/çıxış dərəcələri | cədvəl | DVX reyestr axınları (sorğu edilib) |
| I15 | bazar mövqeyi | Əsas məhsulların natura ilə istehsalı | Main products in physical units | DSK | sənaye 018; məhsul siyahıları: 014_x, 015_x, 016, 017 | məhsul (~140) x sahə | 1995-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | məhsullar üzrə baxış, artım reytinqi | mini-qrafikli (sparkline) məhsul cədvəli | — |
| I16 | bazar mövqeyi | Regionlar üzrə məhsullar | Main products by place of production; product location shares | DSK | sənaye 018_1 (2011-2025), 018_2 (2019-2025); 017_1 (2022 ilədək) | məhsul x şəhər/rayon | 2011-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | yerlər üzrə məhsul bazar payları, yerlər arasında HHI (Hissə 14.3) | xəritə; məhsul cədvəli | — |
| I17 | bazar mövqeyi | Sahələr üzrə ixrac | Exports by branch (export orientation) | Dövlət Gömrük Komitəsi (DGK) | HS kodları səviyyəsində ixrac (layihədə yoxdur) | sahə / məhsul | yoxdur | mövcud deyil | DGK ilə məlumat mübadiləsi sazişi + təhlükəsiz API; HS-NACE uyğunluq cədvəli | paylar sisteminin amili, determinantlar paneli | səpələnmə diaqramı; zaman sırası | sənaye parklarının ixracı (iş kitabı Park, 2019-2025); DSK-nın yüklənmiş mallar cədvəli 011 ixrac deyil |
| I18 | bazar mövqeyi | Sənaye parkları: istehsal, ixrac, iş yerləri | Industrial parks and zones: output, exports, jobs, investment | Sənaye parkı operatorları (İZİA, İqtisadiyyat Nazirliyi) | iş kitabı 'Park' | park | 2019-2025 | hazırda mövcuddur | iş kitabının yüklənməsi (İqtisadiyyat Nazirliyi) | parkların fəaliyyət nəticələri | cədvəl; KPI kartı | — |
| I19 | bazar mövqeyi | İnvestisiya təşviqi sənədləri | Investment promotion certificates: projects, jobs, value | İqtisadiyyat Nazirliyi | iş kitabı 'İnvestisiya təşviqi sənədi ' | ölkə üzrə | 2016-2025 | hazırda mövcuddur | iş kitabının yüklənməsi (İqtisadiyyat Nazirliyi) | dəstək tədbirləri konteksti | cədvəl | — |
| I20 | bazar mövqeyi | KOBİA dəstək xidmətləri | SME agency (KOBİA) support services | KOBİA | iş kitabı 'KOBİA' | ölkə üzrə / KOB evi (SME house) | 2021-2025 | hazırda mövcuddur | iş kitabının yüklənməsi (İqtisadiyyat Nazirliyi) | dəstək tədbirləri konteksti | cədvəl | — |
| I21 | istehsal səmərəliliyi | Əmək məhsuldarlığı (buraxılış/işçi) | Labour productivity, real output per employee | DSK; iş kitabı | sənaye 010, 009, 006; sənaye vərəqləri (işçi sayı) | sahə | 2016-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə); iş kitabının yüklənməsi (İqtisadiyyat Nazirliyi) | səmərəlilik reytinqi, kvadrant, proqnoz trayektoriyası | reytinq cədvəli; kvadrant; yelpik qrafiki | — |
| I22 | istehsal səmərəliliyi | Əmək məhsuldarlığı (ƏD/işçi) | Labour productivity, real value added per employee | DSK | milli hesablar 015_2; 006 | sahə | 2016-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | səmərəlilik reytinqi | reytinq cədvəli | — |
| I23 | istehsal səmərəliliyi | Əmək məhsuldarlığı (rəsmi) | Labour productivity by section (official) | DSK | milli hesablar 030_2 | bölmə | 2017-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | çarpaz yoxlama | KPI kartı | — |
| I24 | istehsal səmərəliliyi | Aralıq istehlakın payı | Intermediate-consumption share of output | DSK | milli hesablar 015, 015_1 | sahə | 2005-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | TFP üçün material xərclərinin payı; xərc strukturu | zaman sırası | — |
| I25 | istehsal səmərəliliyi | Kapital məhsuldarlığı | Capital productivity | DSK | sənaye 019; milli hesablar 031 | sahə / bölmə | 2010-2025 | hazırda mövcuddur (hesablanmış) | fayl endirmə (DSK xls, qrafik üzrə) | səmərəlilik, TFP üçün kapital amili | zaman sırası | — |
| I26 | istehsal səmərəliliyi | Ümumi amil məhsuldarlığı (TFP) | TFP growth, gross output (branches) and value added (sections) | DSK; FR1; FR4 | milli hesablar 013, 015, 015_1, 031; sənaye 019; FR4 muzdlu işçilər | sahə, bölmə | 2017-2025 | hazırda mövcuddur (hesablanmış) | fayl endirmə (DSK xls, qrafik üzrə) | səmərəliliyin dekompozisiyası (Hissə 7.2) | şəlalə / dekompozisiya qrafiki | — |
| I27 | istehsal səmərəliliyi | Əmək haqqı - məhsuldarlıq fərqi | Wage-productivity gap | DSK; iş kitabı | sənaye 006_2; sənaye vərəqləri | sahə | 2016-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | vahid əmək xərclərinin təzyiqi | sütun qrafiki | — |
| I28 | istehsal səmərəliliyi | İnnovasiya intensivliyi | Innovation intensity | DSK | sənaye 020_3 (həmçinin 020_1, 020_2, 020_4, 020_5) | sahə | 2005-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | səmərəlilik profili | reytinq cədvəli | — |
| I29 | istehsal səmərəliliyi | İnvestisiya norması | Investment rate (renewal proxy) | DSK | sənaye 019, 010 | sahə | 2005-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | determinantlar paneli; erkən xəbərdarlıq siqnalı | istilik xəritəsi | — |
| I30 | istehsal səmərəliliyi | Əsas fondların yenilənmə, çıxma, köhnəlmə dərəcəsi | Fixed-asset renewal, disposal and depreciation rates | DSK | sənaye 017_2-017_7 (artıq dərc edilmir, F1) | sahə | yoxdur | mövcud deyil | dərcin bərpası üçün DSK-ya sorğu | yeniləşmə siqnalı | istilik xəritəsi | investisiya dərəcəsi (DSK 019/010); bölmələr üzrə əsas kapitalın istehlakı / əlavə dəyər (milli hesablar 013, 025) |
| I31 | istehsal səmərəliliyi | Kapital qoyuluşlarının səmərəlilik indeksi | Capital-yield index | DSK | sənaye 018_1 (köhnə nömrələmə, dayandırılıb) | sahə | yoxdur | mövcud deyil | DSK-ya sorğu | səmərəlilik | zaman sırası | fasiləsiz inventar metodu ilə kapital məhsuldarlığı |
| I32 | istehsal səmərəliliyi | Enerji intensivliyi | Energy intensity of production | DSK; Azərenerji | sahələr üzrə dərc edilmir (yalnız KOS-un elektrik enerjisi xərcləri, sahibkarlıq 037, 2023-2024) | sahə | yoxdur | mövcud deyil | məlumat mübadiləsi sazişi + təhlükəsiz API | xərc strukturu, determinantlar | reytinq cədvəli | KOS-un elektrik enerjisi və yanacaq xərcləri (sahibkarlıq 035, 037) |
| I33 | maliyyə vəziyyəti | Ümumi əməliyyat mənfəəti (bölmələr) | Gross operating surplus margin by section | DSK | milli hesablar 013 | bölmə (B, C, D, E) | 2005-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | maliyyə vəziyyətinin proqnozu (Hissə 14) | yelpik zolaqlı zaman sırası | — |
| I34 | maliyyə vəziyyəti | Əmək haqqının ƏD-də payı | Labour share of value added | DSK | milli hesablar 013, 023 | bölmə | 2005-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | marjanın dekompozisiyası | zaman sırası | — |
| I35 | maliyyə vəziyyəti | Əsas kapitalın istehlakı | Consumption of fixed capital / VA | DSK | milli hesablar 013, 025 | bölmə | 2005-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | yeniləşmə üzrə proksi göstərici, xalis marja | zaman sırası | — |
| I36 | maliyyə vəziyyəti | Sahə üzrə mənfəət proksisi | GOS-proxy margin by manufacturing branch | DSK; iş kitabı | milli hesablar 015, 015_2; sənaye 006, 006_2; sənaye vərəqləri | sahə | 2016-2025 | hazırda mövcuddur (hesablanmış) | fayl endirmə (DSK xls, qrafik üzrə); iş kitabının yüklənməsi (İqtisadiyyat Nazirliyi) | kvadrant, erkən xəbərdarlıq, proqnoz | kvadrant; reytinq; yelpik qrafiki | — |
| I37 | maliyyə vəziyyəti | Mənfəət vergisi bəyannamələri: xalis marja | Profit-tax declarations: net margin | DVX | iş kitabı 'DVX üzrə göstəricilər' r215-r222 | bütün vergi ödəyiciləri | 2021-2025 | hazırda mövcuddur | iş kitabının yüklənməsi (İqtisadiyyat Nazirliyi) | bütün iqtisadiyyat üzrə rentabellik KPI | KPI kartı | sahələr üzrə bölgü DVX-dən sorğu edilib |
| I38 | maliyyə vəziyyəti | Bəyan edilmiş zərər | Declared losses | DVX | DVX r221 | bütün vergi ödəyiciləri | 2021-2025 | hazırda mövcuddur | iş kitabının yüklənməsi (İqtisadiyyat Nazirliyi) | maliyyə çətinliyi KPI | KPI kartı | — |
| I39 | maliyyə vəziyyəti | Effektiv mənfəət vergisi nisbəti | Effective profit-tax ratio (DVX "rentabellik", F7) | DVX | DVX r223 | bütün vergi ödəyiciləri | 2021-2025 | hazırda mövcuddur | iş kitabının yüklənməsi (İqtisadiyyat Nazirliyi) | vergi yükü | KPI kartı | — |
| I40 | maliyyə vəziyyəti | Gəlir vergisi bəyannamələri (fərdi sahibkarlar) | Income-tax declarations of individual entrepreneurs | DVX | DVX r224-r232 | bütün vergi ödəyiciləri | 2021-2025 | hazırda mövcuddur | iş kitabının yüklənməsi (İqtisadiyyat Nazirliyi) | kiçik biznesin rentabelliyi | KPI kartı | — |
| I41 | maliyyə vəziyyəti | Vergi borcları | Tax arrears | DVX | DVX r43 | ölkə üzrə | 2021-2025 | hazırda mövcuddur | iş kitabının yüklənməsi (İqtisadiyyat Nazirliyi) | erkən xəbərdarlıq konteksti | KPI kartı | — |
| I42 | maliyyə vəziyyəti | Sənaye dövriyyəsi (vergi bazası) | Industry turnover on the tax basis | DVX | DVX r53-r57 | sənaye / qeyri-neft sənayesi | 2021-2025 | hazırda mövcuddur | iş kitabının yüklənməsi (İqtisadiyyat Nazirliyi) | buraxılışın çarpaz yoxlanması | zaman sırası | — |
| I43 | maliyyə vəziyyəti | İnvestisiyanın öz vəsaitləri hesabına maliyyələşməsi | Investment self-financing share | DSK (iş kitabı vasitəsilə) | iş kitabı 'Real sektor' r114 / r80 | ölkə üzrə | 2023-2025 | hazırda mövcuddur (3 il, illik) | iş kitabının yüklənməsi (İqtisadiyyat Nazirliyi) | maliyyə imkanları KPI | KPI kartı | — |
| I44 | maliyyə vəziyyəti | Hazır məhsul ehtiyatları | Finished-goods stocks to output | DSK | sənaye 013 | sahə | 1999-2025 | hazırda mövcuddur | fayl endirmə (DSK xls, qrafik üzrə) | erkən xəbərdarlıq siqnalı (ehtiyatların artması) | istilik xəritəsi | — |
| I45 | maliyyə vəziyyəti | KOB-ların aktivləri, ehtiyatları, vergiləri | SME assets, stocks and taxes paid | DSK | sahibkarlıq 039, 040, 041 | bölmə x ölçü | 2023-2024 | hazırda mövcuddur (2 il) | fayl endirmə (DSK xls, qrafik üzrə) | KOS-un balans profili | cədvəl | — |
| I46 | maliyyə vəziyyəti | Likvidlik əmsalları | Liquidity: current, quick, cash ratios | DVX | müəssisələrin balans hesabatı və mənfəət-zərər hesabatı paneli (24.08.2026 tarixində sorğu edilib) | müəssisə | yoxdur | sorğu edilib | məlumat mübadiləsi sazişi + təhlükəsiz API | B qatının hesablama modulu (Hissə 17) | müəssisə qiymətləndirmə kartı; analoqlar arasında persentil; erkən xəbərdarlıq siyahısı | müəssisələr üzrə yoxdur; yuxarıdakı aqreqat proksi göstəricilər |
| I47 | maliyyə vəziyyəti | Borc yükü, faiz örtüyü | Leverage and interest cover | DVX | müəssisələrin balans hesabatı və mənfəət-zərər hesabatı paneli (24.08.2026 tarixində sorğu edilib) | müəssisə | yoxdur | sorğu edilib | məlumat mübadiləsi sazişi + təhlükəsiz API | B qatının hesablama modulu (Hissə 17) | müəssisə qiymətləndirmə kartı; analoqlar arasında persentil; erkən xəbərdarlıq siyahısı | müəssisələr üzrə yoxdur; yuxarıdakı aqreqat proksi göstəricilər |
| I48 | maliyyə vəziyyəti | Rentabellik (DuPont) | Profitability: ROE (DuPont), ROA, EBIT margin | DVX | müəssisələrin balans hesabatı və mənfəət-zərər hesabatı paneli (24.08.2026 tarixində sorğu edilib) | müəssisə | yoxdur | sorğu edilib | məlumat mübadiləsi sazişi + təhlükəsiz API | B qatının hesablama modulu (Hissə 17) | müəssisə qiymətləndirmə kartı; analoqlar arasında persentil; erkən xəbərdarlıq siyahısı | müəssisələr üzrə yoxdur; yuxarıdakı aqreqat proksi göstəricilər |
| I49 | maliyyə vəziyyəti | Dövriyyə göstəriciləri | Turnover: assets, inventories, receivable days | DVX | müəssisələrin balans hesabatı və mənfəət-zərər hesabatı paneli (24.08.2026 tarixində sorğu edilib) | müəssisə | yoxdur | sorğu edilib | məlumat mübadiləsi sazişi + təhlükəsiz API | B qatının hesablama modulu (Hissə 17) | müəssisə qiymətləndirmə kartı; analoqlar arasında persentil; erkən xəbərdarlıq siyahısı | müəssisələr üzrə yoxdur; yuxarıdakı aqreqat proksi göstəricilər |
| I50 | maliyyə vəziyyəti | Altman Z''-EM | Distress score (Altman Z''-EM, literature coefficients) | DVX | müəssisələrin balans hesabatı və mənfəət-zərər hesabatı paneli (24.08.2026 tarixində sorğu edilib) | müəssisə | yoxdur | sorğu edilib | məlumat mübadiləsi sazişi + təhlükəsiz API | B qatının hesablama modulu (Hissə 17) | müəssisə qiymətləndirmə kartı; analoqlar arasında persentil; erkən xəbərdarlıq siyahısı | müəssisələr üzrə yoxdur; yuxarıdakı aqreqat proksi göstəricilər |
| I51 | istehsal səmərəliliyi | Müəssisə məşğulluğu və əmək haqqı fondu | Firm employment and wage bill | DSMF | sığorta haqqı ödəyicilərinin qeydləri (sorğu edilib) | müəssisə | yoxdur | sorğu edilib | məlumat mübadiləsi sazişi + təhlükəsiz API | B qatı: məhsuldarlıq, TFP | müəssisə qiymətləndirmə kartı | sahələr üzrə işçi sayı (DSK 006, iş kitabı) |
| I52 | maliyyə vəziyyəti | Sahələr üzrə kredit, problemli kreditlər | Credit and NPLs by branch | CBAR | layihədə yoxdur (FR1 sənaye üzrə ümumi kredit həcmini əhatə edir) | sahə | yoxdur | mövcud deyil | Mərkəzi Bank (CBAR) ilə məlumat mübadiləsi sazişi + təhlükəsiz API | maliyyə vəziyyətinin amili | zaman sırası | bölmə səviyyəsində FR1 sənaye krediti (cred_ind_n) |
<!-- /AUTO:matrix -->

## 6. Boşluqlar, alternativlər və Sifarişçi ilə razılaşdırılmalı tədbirlər

<!-- AUTO:gaps -->
| id | boşluq | təsir | alternativ proksi | proksinin meyli | Sifarişçi ilə razılaşdırılmalı tədbir |
|---|---|---|---|---|---|
| G01 | Müəssisələrin balans və mənfəət-zərər hesabatı paneli (Vergi Xidməti, >= 5 il) | Müəssisə əmsalları, maliyyə çətinliyi balları, müəssisə səviyyəsində HHI, müəssisələr üzrə giriş/çıxış yoxdur; B qatı yalnız sintetik məlumatlarla işləyir | Bölmələr üzrə ümumi mənfəət marjaları (milli hesablar, NA 013), sahə üzrə ümumi mənfəətin təxmini göstəricisi, DVX bəyannamə aqreqatları, registr əsasında konsentrasiya həddi | Aqreqatlar dispersiyanı gizlədir; ümumi mənfəətin təxmini göstəricisi digər vergiləri və işçi olmayanlara ödənişləri nəzərə almır (marjaları şişirdir) | Hissə 17.1 sxemi üzrə məlumat mübadiləsi sazişini imzalamaq; psevdonimləşdirilmiş VÖEN; bəyannamə müddəti bitdikdən sonra illik ötürmə |
| G02 | Müəssisələr üzrə məşğulluq və əmək haqqı fondu (DSMF) | Müəssisə məhsuldarlığı və ya TFP yoxdur | DSK sahə üzrə işçi sayı və əmək haqqı (006, 006_2), iş kitabının sənaye vərəqləri | Yalnız sahə üzrə orta göstəricilər | Eyni psevdonimləşdirilmiş VÖEN-ə əsaslanan DSMF sazişi |
| G03 | Sahələr üzrə əsas fondların yenilənmə, xaricolma və köhnəlmə əmsalları (F1) | Birbaşa yenilənmə göstəricisi yoxdur | İnvestisiya norması I/GO (DSK 019/010); bölmələr üzrə əsas kapitalın istehlakı / əlavə dəyər (milli hesablar, NA 013, 025) | İnvestisiya norması fondların yaşını nəzərə almır və sıçrayışlıdır; bölmə üzrə əsas kapitalın istehlakı sahələri gizlədir | DSK-dan 017_2-017_7 cədvəllərini bərpa etməyi və ya onları MIIS-ə ötürməyi xahiş etmək |
| G04 | Fondverimi indeksi (köhnə DSK 018_1) | Kapitalın səmərəliliyi üzrə dərc edilmiş göstərici yoxdur | Daimi inventarizasiya metodu əsasında kapital məhsuldarlığı | Köhnəlmə dərəcəsindən (0.07) və 2010 ilinin başlanğıc fondundan asılıdır | Yuxarıdakı kimi |
| G05 | Sahələr / məhsullar üzrə ixrac (Dövlət Gömrük Komitəsi) | İxrac yönümlülüyü paylar sisteminə və ya amillər panelinə daxil edilə bilməz | Sənaye parklarının ixracı (iş kitabı, Park vərəqi) | Yalnız parkları və zonaları əhatə edir, sahə strukturu yoxdur | DGK-dan HS-NACE keçid cədvəli ilə HS səviyyəsində aylıq ixrac məlumatları |
| G06 | NACE 2 rəqəmli sahələr üzrə istehsalçı qiymətləri | Sahələrin real buraxılışı implisit deflyatorlara əsaslanır | Buraxılışın implisit deflyatoru = nominal buraxılış / zəncirvari həcm (DSK 010, 009) | Sahə daxilindəki struktur effektləri deflyatora daxil olur | Sahələr üzrə DSK istehsalçı qiymətləri indeksi (PPI) |
| G07 | Sahələr üzrə enerji xərcləri | Enerji tutumu göstəricisi yoxdur | KOS (SME) elektrik enerjisi və yanacaq xərcləri (sahibkarlıq 035, 037; 2023-2024) | Yalnız KOS subyektləri, iki il | DSK / Azərenerji: sahələr üzrə enerji istehlakı |
| G08 | Sahələr üzrə kreditlər və problemli kreditlər (Mərkəzi Bank, CBAR) | Sahələr üzrə maliyyələşmə şəraiti amili yoxdur | FR1 sənaye kreditləri, bölmə səviyyəsində | Bölmə səviyyəsi | Mərkəzi Bankın (CBAR) kredit reyestrinin NACE üzrə aqreqatları |
| G09 | KOS (SME) göstəricilərinin zaman sırası (F11) | KOS payını proqnozlaşdırmaq mümkün deyil | 2024 səviyyəsində saxlanılır | Heç bir trendi nəzərə almır | DSK-nın 2019 ilindən başlayan sahibkarlıq cədvəllərinin retrospektiv sıraları |
| G10 | İqtisadi rayon x sahə üzrə sənaye buraxılışı | İqtisadi rayonlar üzrə proqnozlarda sahə strukturundan istifadə etmək mümkün deyil | İqtisadi rayonlar üzrə yekunlar (022) və istehsal yeri üzrə məhsullar (018_1 2011-2025, 018_2 2019-2025) | Məhsullar yalnız natural ifadədə və yalnız əsas məhsullar üzrədir | DSK-nın iqtisadi rayon x NACE üzrə buraxılış cədvəli |
| G11 | Sahə və ölçü qrupu üzrə mənfəət vergisi bəyannamələri (DVX) | Maliyyə vəziyyəti yalnız bütün iqtisadiyyat üzrə, bəyannamələr əsasında | Bütün iqtisadiyyat üzrə DVX aqreqatları | Neft və iri vergi ödəyiciləri üstünlük təşkil edir | r215-r232 sətirlərinin NACE və ölçü üzrə DVX bölgüsü |
| G12 | Büdcə təşkilatı olan vergi ödəyicilərinin sətirləri (F8) | Büdcə təşkilatlarını ayırmaq mümkün deyil | — | - | DVX-nin iş kitabının 127-129 sətirlərini düzəltməsi |
| G13 | İş kitabındakı 2025 sahə məlumatlarının versiyası (F2) | İş kitabındakı 2025 sahə məlumatları istifadəyə yararsızdır | DSK-nın yekun məlumatları, 2025 | DSK-nın yekun məlumatlarından istifadə edildikdə yoxdur | Yeniləmə proseduru: yekun məlumatlar dərc edildikdə iş kitabının sətirləri DSK məlumatları ilə əvəz olunur |
| G14 | İqtisadi rayonlar üzrə əhatə dairəsində qırılma, 2019 (F9) | İqtisadi rayonların paylarında səviyyə qırılması | Pilləli fiktiv dəyişən; paylar iqtisadi rayonların cəminə görə | 2019 ilinədək olan paylara ev təsərrüfatlarının sənaye fəaliyyəti daxil deyil | DSK tərəfindən iqtisadi rayonlar üzrə buraxılışın 2019+ əhatəsi əsasında retrospektiv hesablanması |
| G15 | Dərc edilmiş qeyri-dövlət payı 2013-2016 uyğunsuzdur (F12) | 4 ildə mülkiyyət tarixçəsi qeyri-müəyyəndir | Struktur eyniliyi | Proqnozda yoxdur | DSK-ya sorğu göndərmək |
| G16 | FR3 sahə əmək haqqı səviyyələri 2025 ilinin göstəricilərinə bağlanmayıb (F13) | FR3 sahə əmək haqqı səviyyələri marjalar üçün yararsızdır | DSK-nın 2025 sahə əmək haqlarına tətbiq edilən FR1 orta əmək haqqı indeksi | Bütün sahələr üzrə eyni əmək haqqı artımı | FR3-ə cavabdeh olanlar sahə səviyyələrini 2025 ilinin faktiki göstəricilərinə bağlamalıdır |
<!-- /AUTO:gaps -->

## 7. Təqdimat spesifikasiyası — MİİS istifadəçi görünüşləri

<!-- AUTO:pres -->
| görünüş | məzmun | forma | mənbə fayllar |
|---|---|---|---|
| V1 Sahə göstəriciləri kartı | Hər sahə üçün bir kart: sənayedə və emal sənayesində pay, real artım, əmək məhsuldarlığı, ümumi mənfəət (proksi) marjası, investisiya norması, siqnallar | KPI kartları + mini-qrafik (sparkline) | FR10_branch_scorecard.csv |
| V2 Səmərəlilik və maliyyə vəziyyəti | Əmək məhsuldarlığının artımı ümumi mənfəət (proksi) marjasına qarşı, qabarcıq = bazar payı; kvadrant etiketləri | səpələnmə diaqramı / kvadrant | FR10_quadrant.csv |
| V3 Bazar payı dinamikası | Sahə payları 2005-2025 və 2026-2030, 50/80/90% zolaqlarla; HHI, CR4 | yığılmış sahə diaqramı; yelpik diaqramı; KPI | FR10_branch_shares_history.csv, FR10_forecast_branches.csv, FR10_fan_charts.csv, FR10_concentration.csv |
| V4 İqtisadi rayon x fəaliyyət növü | İllər üzrə sənaye buraxılışında iqtisadi rayonların payları; qeyri-dövlət payı; müəssisələr; bazara giriş/çıxış; proqnoz payları | xəritə + istilik xəritəsi | FR10_regional_history.csv, FR10_forecast_regions.csv, FR10_regional_entry_exit.csv |
| V5 Məhsullar üzrə görünüş | Natural ifadədə əsas məhsullar, 2020-2025 artım, sahə ilə əlaqə | mini-qrafikli cədvəl | FR10_products.csv |
| V6 Zolaqlı proqnoz | Bölmə və sahə buraxılışı (nominal, real), marjalar, qeyri-dövlət payı üç ssenari üzrə, 5-95% zolaqlarla | yelpik zolaqlı zaman sırası | FR10_forecast_branches.csv, FR10_forecast_sections.csv, FR10_fan_charts.csv, FR10_scenario_summary.csv |
| V7 Erkən xəbərdarlıq siqnalları | Marja, bazar payı, yenilənmə, ehtiyatlar və məhsuldarlıq siqnalları; müşahidə siyahısı | siqnal cədvəli (svetofor) | FR10_early_warning.csv |
| V8 Maliyyə vəziyyəti | Bölmələr üzrə ümumi mənfəət marjaları, əməyin payı, əsas kapitalın istehlakı (CFC); DVX bəyannamələri üzrə marjalar, zərərlər, borclar; özünümaliyyələşdirmə | zaman sıraları; KPI kartları | FR10_financial_sections.csv, FR10_dvx_declarations.csv |
| V9 Əsas amillər | Sahələr üzrə artıma töhfələr; düzgün statistik nəticə çıxarışı ilə müəyyənedici amillər paneli | şəlalə diaqramı; əmsallar cədvəli | FR10_growth_contributions.csv, FR10_determinants_panel.csv |
| V10 Səmərəlilik | TFP dekompozisiyası, kapitalın məhsuldarlığı, əmək haqqı-məhsuldarlıq boşluğu, innovasiya intensivliyi | dekompozisiya sütunları | FR10_efficiency_branches.csv, FR10_tfp_sections.csv |
| V11 Məlumat kataloqu | Göstərici, mənbə, cədvəl/sətir, illər, status, inteqrasiya yolu, alternativ | axtarışlı cədvəl | FR10_data_source_matrix.csv, FR10_data_gaps_and_alternatives.csv, FR10_data_integrity_findings.csv |
| V12 Müəssisə görünüşü (B qatı) | Müəssisə göstəriciləri kartı, analoq müəssisələr üzrə persentillər, maliyyə çətinliyi zonası, NACE x iqtisadi rayon üzrə müəssisə HHI, müəssisə proqnozu — YALNIZ DVX/DSMF paneli daxil olduqda AKTİVDİR | müəssisə kartı; istilik xəritəsi | hazırda FR10_SYNTHETIC_*.csv (yalnız emal xəttinin sınağı, su nişanı ilə) |
<!-- /AUTO:pres -->

## 8. A qatının analitikası, 2005–2025

### 8.1 Bazar mövqeyi

Paylar **nominal** buraxılış üzrə hesablanır (nominal dəyərlər dəqiq cəmlənir, zəncirvari həcmlər isə cəmlənmir).
Sahələr və regionlar üzrə konsentrasiya HHI (×10 000) və CR4 ilə ölçülür. Müəssisə səviyyəsində konsentrasiya üçün
müəssisə məlumatları lazımdır; mövcud məlumatlar bir hədd qoymağa imkan verir: N iri vahid buraxılışın s payını
istehsal edirsə, müəssisə HHI-ı ən azı s²/N-dir.

<!-- AUTO:market -->
Emal sənayesində sahələr üzrə HHI 2188 (2005) → 1400 (2025); CR4 62,4%; 14 region üzrə HHI 6460. 2025-ci ilin liderləri: Neft emalı məhsulları 25,3%, Qida məhsulları 23,0%, Kimya məhsulları 7,3%, Digər qeyri-metal mineral məhsullar 6,8%, Metallurgiya 5,2%. Sənayedə qeyri-dövlət payı 78,1% (emal sənayesi 64,9%, mədənçıxarma 94,1%). Fəaliyyət göstərən sənaye müəssisələri: 4 831 (2025) və 2 583 (2015). Müəssisə konsentrasiyası həddi: iri (KOS olmayan) müəssisələr sənaye buraxılışının 89,2%-ni istehsal edir (2024), reyestr isə 237 iri sənaye vahidi qeydə alır (1 iyul 2026); onlar arasında bərabər bölgü HHI = 33,6 verir, istənilən qeyri-bərabər bölgü isə onu artırır, buna görə bu aşağı həddir (iki mənbə müxtəlif tarixlərə aiddir). Buraxılışla çəkilənmiş sahə qeyri-dövlət payları dərc olunmuş sənaye göstəricisini 0,15 f.b. dəqiqliklə təkrarlayır; istisnalar: 2005 (-0,8 f.b.), 2013 (+6,3 f.b.), 2014 (+7,6 f.b.), 2015 (+7,9 f.b.), 2016 (+6,7 f.b.) (F12).
<!-- /AUTO:market -->

Qeyri-dövlət payının proqnozu sahələrin tərkibi əsasında qurulur (F12 tapıntısı).

### 8.2 İstehsal səmərəliliyi

Əmək məhsuldarlığı (bir işçiyə düşən real buraxılış və real əlavə dəyər), aralıq istehlakın payı, kapitalın
məhsuldarlığı (sahə investisiyalarından fasiləsiz inventar üsulu ilə, FR1-də olduğu kimi δ = 0,07; 2010-cu il ehtiyatı =
bölmənin müşahidə olunan əsas fondlarının 2005–2010 investisiya paylarına görə bölüşdürülməsi) və **müşahidə olunan**
xərc payları ilə artımın uçotu üsulu üzrə TFP — sahələr üçün ümumi buraxılış üzrə Törnqvist (s_M = IC/GO,
s_L = əmək haqqı fondu × 1,22 / GO, s_K qalıq), bölmələr üçün əlavə dəyər forması (s_L = əməyin ödənişi/VA, K = milli
hesablar üzrə sabit qiymətlərlə əsas fondlar). İstehsal funksiyasının heç bir parametri qiymətləndirilmir; əmək və
material paylarının cəmi birdən böyük olan sahə-illər işarələnir. Bölmələr üzrə TFP:

<!-- AUTO:eff -->
| bölmə (ildə orta %, 2007–2025) | dlnVA | əmək | kapital | TFP |
|---|---|---|---|---|
| Elektrik enerjisi | 2.21 | 0.11 | 7.00 | -4.90 |
| Emal sənayesi | 5.04 | 0.46 | 4.36 | 0.23 |
| Mədənçıxarma | 1.08 | -0.08 | 8.02 | -6.87 |
| Su təchizatı | 4.73 | 2.93 | 2.35 | -0.56 |

Sahələr üzrə TFP (ümumi buraxılış, 2017–2025 kumulyativ, log bəndləri × 100), ən yüksək və ən aşağı:

| sahə | buraxılış artımı 2016-25, log bəndi x100 | materiallar | əmək | kapital | TFP | kapitalın orta payı |
|---|---|---|---|---|---|---|
| Digər nəqliyyat vasitələri | 224.49 | 115.45 | -78.31 | 44.64 | 142.71 | -0.69 |
| Tütün məmulatları | 217.68 | 130.10 | 12.56 | 0.09 | 74.92 | 0.33 |
| Digər qeyri-metal mineral məhsullar | 185.06 | 112.37 | 0.44 | 0.40 | 71.86 | 0.25 |
| Hazır metal məmulatları | 103.16 | 37.18 | 8.04 | -10.44 | 68.37 | 0.23 |
| Avtomobil və qoşqular | 73.20 | 213.97 | 1.96 | 22.04 | -164.77 | 0.23 |
| Neft emalı məhsulları | 7.19 | 5.77 | -0.15 | 73.42 | -71.85 | 0.44 |
| Maşın və avadanlıq | -115.06 | -49.97 | -13.29 | -5.26 | -46.56 | 0.15 |
| Maşın və avadanlığın təmiri və quraşdırılması | -51.15 | -33.64 | 10.59 | 5.57 | -33.66 | 0.15 |
<!-- /AUTO:eff -->

Şərh: burada TFP müşahidə olunan resurslardan sonra qalan qalıqdır; mədənçıxarmada o, texnologiya qədər yataqların
tükənməsini də əks etdirir, kiçik sahələrdə isə TFP səs-küylüdür (implisit deflyatorlar, fasiləsiz inventar üsulu ilə
kapital).

### 8.3 Maliyyə vəziyyəti

Hər birinin öz məhdudiyyəti olan üç pəncərə: bölmələr üzrə milli hesabların ümumi mənfəəti (GOS); emal sənayesi
sahələri üzrə GOS-un proksi göstəricisi (əlavə dəyər − ümumi əmək haqqı fondu; digər vergilər və işçi olmayanlara
ödənişlər nəzərə alınmadığından yuxarı hədd); bütün iqtisadiyyat üzrə mənfəət vergisi bəyannamələri (DVX). Bölmələr
üzrə GOS, əlavə dəyərin %-i kimi:

<!-- AUTO:fin -->
| il | Mədənçıxarma | Emal sənayesi | Elektrik enerjisi | Su təchizatı |
|---|---|---|---|---|
| 2005.00 | 89.35 | 73.95 | 29.25 | 16.41 |
| 2010.00 | 96.40 | 83.45 | 68.18 | 18.00 |
| 2015.00 | 91.88 | 76.68 | 70.42 | 2.25 |
| 2019.00 | 93.40 | 62.68 | 62.46 | 9.17 |
| 2022.00 | 96.85 | 72.42 | 70.10 | -33.24 |
| 2025.00 | 93.56 | 65.82 | 65.44 | -51.61 |

DVX mənfəət vergisi bəyannamələri: xalis marja 10,0–13,2% (2021–2025); bəyan edilmiş zərərlər vergi tutulan mənfəətin 14–27%-i; vergi borcları 1 897 → 3 253 mln manat; investisiyaların öz vəsaiti hesabına maliyyələşdirilməsi 2023 50,1%, 2024 49,1%, 2025 51,4%. Sahələr üzrə GOS proksi marjası 2025: median buraxılışın 20,4%-i; mənfi olduğu sahələr: Əczaçılıq məhsulları, Digər nəqliyyat vasitələri.
<!-- /AUTO:fin -->

Likvidlik, borc yükü (leverage), faiz ödənişinin örtülməsi, DuPont ROE və maliyyə çətinliyi balı balans hesabatları
tələb edir və B qatında müəyyən edilir.

## 9. Avtoreqressiyanın qadağan olunması məhdudiyyəti

| Konstruksiya | Harada | Niyə avtoreqressiya deyil |
|---|---|---|
| HAC / Driscoll–Kraay kovariasiyası | bütün tənliklər | yalnız standart xətalar |
| İzahedici dəyişən fərqlərinin DOLS qabaqlayıcıları/gecikmələri | pay tənlikləri | endogenlik düzəlişi; öz gecikməsi yoxdur |
| Qalıqların ADF testi, bir sabit gecikmə | `eg_coint_p` | test statistikası |
| Zəncirlənmiş həcm səviyyələri; fasiləsiz inventar | məlumatların qurulması | mühasibat eynilikləri |
| Digər izahedici dəyişənlərin bir illik gecikmələri | amillər paneli | əvvəlcədən müəyyən olunmuş izahedici dəyişənlər; sahə artımı heç vaxt sağ tərəfdə deyil |
| Sabit düzəliş əmsalı (2025 lövbəri) | pay sistemləri | səviyyə lövbəri; ρ̂ ilə sönmə yalnız işarələnmiş həssaslıq kimi |
| Tarixi qalıq yolları | yelpik qrafikləri | müşahidə olunmuş xəta yollarının təkrar tətbiqi |
| 2025 səviyyəsində saxlanılan proqnoz qaydaları | proqnoz | açıq bəyan edilmiş fərziyyələr (`FR10_forecast_assumptions.csv`) |

## 10. Artım və azalmanın əsas amilləri

Dayanıqlı cavab real emal sənayesi artımının sahə töhfələrinə dəqiq Törnqvist dekompozisiyasıdır; ekonometrik cavab
sahə real artımının gecikmiş investisiya norması, nisbi qiymət dəyişməsi, qeyri-dövlət payı, ehtiyatların buraxılışa
nisbəti və müəssisə sayının artımı üzrə (A spesifikasiyası, 2011–2025), habelə real əmək haqqı və əməyin payı üzrə (B,
2018–2025) iki yönlü sabit effektli panelidir. 24 emal sənayesi sahəsindən 21-i tam məlumata malikdir və panelə daxil
edilir. Panel balanslaşdırılmamışdır, buna görə iki yönlü within çevrilməsi növbəli proyeksiyalarla hesablanır (fiktiv
dəyişənli OLS ilə eynidir, Hissə 3-də yoxlanılıb), o cümlədən wild bootstrap daxilində. t(T−1) üzrə ⌊T^¼⌋ gecikməli
Driscoll–Kraay xətaları, illər üzrə klaster wild bootstrap (Webb); between qiymətləndiricisi göstərilir, lakin təsir
kimi şərh olunmur. Bölmə meylini (division bias) məhdudlaşdırmaq üçün məxrəcində buraxılış olan nisbətlərdə t−2 ilinin
buraxılışı istifadə olunur. İxrac yönümlülüyü, kredit və enerji xərcləri sahələr üzrə mövcud deyil.

<!-- AUTO:det -->
| spesifikasiya | izahedici dəyişən | əmsal | se_DK | p_DK_t | p_wild | between_coef | n | illər |
|---|---|---|---|---|---|---|---|---|
| A: 2011-2025, əsas | inv_rate_l1 | -0.062 | 0.027 | 0.036 | 0.120 | 0.049 | 265 | 15 |
| A: 2011-2025, əsas | drelp_l1 | 0.079 | 0.066 | 0.253 | 0.300 | -0.478 | 265 | 15 |
| A: 2011-2025, əsas | nonstate_l1 | 0.009 | 0.202 | 0.965 | 0.950 | 0.060 | 265 | 15 |
| A: 2011-2025, əsas | stocks_go_l1 | -0.002 | 0.017 | 0.899 | 0.903 | -0.011 | 265 | 15 |
| A: 2011-2025, əsas | dln_ent_l1 | -0.250 | 0.175 | 0.175 | 0.154 | 0.038 | 265 | 15 |
| B: 2018-2025, + əmək haqqı və əməyin payı | inv_rate_l1 | 0.017 | 0.016 | 0.333 | 0.338 | 0.092 | 151 | 8 |
| B: 2018-2025, + əmək haqqı və əməyin payı | drelp_l1 | -0.243 | 0.376 | 0.538 | 0.556 | 0.043 | 151 | 8 |
| B: 2018-2025, + əmək haqqı və əməyin payı | nonstate_l1 | 0.265 | 0.335 | 0.455 | 0.460 | 0.086 | 151 | 8 |
| B: 2018-2025, + əmək haqqı və əməyin payı | stocks_go_l1 | 0.348 | 0.412 | 0.426 | 0.465 | -0.138 | 151 | 8 |
| B: 2018-2025, + əmək haqqı və əməyin payı | dln_ent_l1 | -0.174 | 0.346 | 0.631 | 0.772 | -0.064 | 151 | 8 |
| B: 2018-2025, + əmək haqqı və əməyin payı | dln_rwage_l1 | -0.258 | 0.320 | 0.447 | 0.458 | 0.320 | 151 | 8 |
| B: 2018-2025, + əmək haqqı və əməyin payı | labour_share_l1 | -0.026 | 0.676 | 0.970 | 0.944 | -0.003 | 151 | 8 |

2016–2025 dövründə real emal sənayesi artımına töhfələr (log bəndləri × 100): ən yüksək — Qida məhsulları +17,3, Digər qeyri-metal mineral məhsullar +10,9, Kimya məhsulları +6,4, Rezin və plastik kütlə +5,9, Tütün məmulatları +3,6; ən aşağı — Maşın və avadanlıq -2,5, Maşın və avadanlığın təmiri və quraşdırılması -2,3, Neft emalı məhsulları -1,3.
<!-- /AUTO:det -->

Bölmə meyli düzəlişinin əmsalları nə qədər dəyişdirdiyi (istifadə olunan t−2 məxrəcləri ilə eyni ilin məxrəcləri
müqayisədə):

<!-- AUTO:divb -->
| spesifikasiya | izahedici dəyişən | coef_t2_denominator | coef_same_year_denominator | dəyişmə | p_t2 | p_same |
|---|---|---|---|---|---|---|
| A | inv_rate_l1 | -0.062 | -0.049 | -0.013 | 0.036 | 0.078 |
| A | stocks_go_l1 | -0.002 | 0.002 | -0.004 | 0.899 | 0.987 |
| B | inv_rate_l1 | 0.017 | 0.040 | -0.023 | 0.333 | 0.211 |
| B | stocks_go_l1 | 0.348 | 0.540 | -0.192 | 0.426 | 0.212 |
| B | labour_share_l1 | -0.026 | 0.211 | -0.237 | 0.970 | 0.475 |
<!-- /AUTO:divb -->

Hər iki testdə əhəmiyyətli olmayan əmsallar "təsir yoxdur" deyil, "müəyyən edilməyib (aşağı güc)" kimi təsvir olunur.

## 11. Sahələr və regionlar üzrə bölüşdürmə

### 11.1 Sektor miqyaslı sürücülərlə pay sistemləri (müqayisə meyarı)

Sahələrin emal sənayesi və mədənçıxarma buraxılışındakı nominal payları və regionların sənaye buraxılışındakı payları
sektorun miqyası və neft kanalı (FR1) ilə idarə olunan multinomial-logit sistemləri kimi qurulur; DOLS meylləri, uyğunluq
qaydası və empirik Bayes büzülməsi tətbiq olunur; namizədlər 2011–2017 başlanğıclarında qiymətləndirilir (göstəricilər
≤ 2019, hədəf ili üzrə DM/HLN). Sahələr üçün sabit paylar seçilib; bu sistem struktur modelin qiymətləndirildiyi
müqayisə meyarı kimi saxlanılır.

<!-- AUTO:select -->
**emal sənayesi**

| namizəd | RMSE_pp | DM_HLN_vs_best | DM_p_vs_best | target_years | meyllər | non_inferior | qərar | mərhələ | DM_p_vs_const |
|---|---|---|---|---|---|---|---|---|---|
| sabit paylar | 1.869 | — | — | — | 0.000 | bəli | CHOSEN | spesifikasiya | — |
| MNL: miqyas (FR1 real sektor əlavə dəyəri) | 2.493 | -2.258 | 0.058 | 8.000 | 1.000 | xeyr | — | spesifikasiya | — |
| MNL: neft ixrac qiyməti | 1.950 | -1.166 | 0.282 | 8.000 | 1.000 | bəli | — | spesifikasiya | — |
| MNL: miqyas + neft qiyməti | 4.737 | -2.387 | 0.048 | 8.000 | 2.000 | xeyr | — | spesifikasiya | — |
| kombinasiya: 1/2 sabit paylar + 1/2 MNL miqyas | 2.037 | -2.544 | 0.038 | 8.000 | 1.000 | xeyr | — | spesifikasiya | — |

**mədənçıxarma**

| namizəd | RMSE_pp | DM_HLN_vs_best | DM_p_vs_best | target_years | meyllər | non_inferior | qərar | mərhələ | DM_p_vs_const |
|---|---|---|---|---|---|---|---|---|---|
| sabit paylar | 3.754 | -1.611 | 0.151 | 8.000 | 0.000 | bəli | CHOSEN | spesifikasiya | — |
| MNL: miqyas (FR1 real sektor əlavə dəyəri) | 3.712 | -1.531 | 0.170 | 8.000 | 1.000 | bəli | — | spesifikasiya | — |
| MNL: neft ixrac qiyməti | 3.760 | -1.660 | 0.141 | 8.000 | 1.000 | bəli | — | spesifikasiya | — |
| MNL: miqyas + neft qiyməti | 3.306 | — | — | — | 2.000 | bəli | — | spesifikasiya | — |
| kombinasiya: 1/2 sabit paylar + 1/2 MNL miqyas | 3.733 | -1.572 | 0.160 | 8.000 | 1.000 | bəli | — | spesifikasiya | — |

**regionlar**

| namizəd | RMSE_pp | DM_HLN_vs_best | DM_p_vs_best | target_years | meyllər | non_inferior | qərar | mərhələ | DM_p_vs_const |
|---|---|---|---|---|---|---|---|---|---|
| sabit paylar | 1.215 | -2.360 | 0.050 | 8.000 | 0.000 | xeyr | — | spesifikasiya | — |
| MNL: miqyas (FR1 real sektor əlavə dəyəri) | 1.377 | -2.862 | 0.024 | 8.000 | 1.000 | xeyr | — | spesifikasiya | — |
| MNL: neft sektoru strukturu (FR1 mədənçıxarma/emal sənayesi əlavə dəyəri) | 1.131 | — | — | — | 1.000 | bəli | CHOSEN | spesifikasiya | — |
| MNL: miqyas + neft sektoru strukturu | 1.341 | -4.354 | 0.003 | 8.000 | 2.000 | xeyr | — | spesifikasiya | — |
| kombinasiya: 1/2 sabit paylar + 1/2 MNL miqyas | 1.294 | -2.791 | 0.027 | 8.000 | 1.000 | xeyr | — | spesifikasiya | — |
| kappa = 0 (büzülmə (shrinkage) yoxdur) | 1.091 | — | — | — | — | bəli | — | büzülmə | 0.151 |
| kappa = 0.5 | 1.110 | -0.697 | 0.508 | — | — | bəli | CHOSEN | büzülmə | 0.054 |
| kappa = 1 | 1.131 | -0.995 | 0.353 | — | — | bəli | — | büzülmə | 0.050 |
| kappa = 2 | 1.152 | -1.203 | 0.268 | — | — | bəli | — | büzülmə | 0.047 |
| kappa = 4 | 1.170 | -1.347 | 0.220 | — | — | bəli | — | büzülmə | 0.043 |
| kappa = 8 | 1.185 | -1.446 | 0.191 | — | — | bəli | — | büzülmə | 0.041 |
| kappa = 16 | 1.196 | -1.512 | 0.174 | — | — | bəli | — | büzülmə | 0.038 |
| kappa = 64 | 1.209 | -1.580 | 0.158 | — | — | bəli | — | büzülmə | 0.036 |
| kappa = 256 | 1.213 | -1.602 | 0.153 | — | — | bəli | — | büzülmə | 0.035 |
<!-- /AUTO:select -->

### 11.2 Neft emalı — gücü məhdud, neft qiymətinə bağlı emalçı kimi

Real buraxılış = emal həcmi (sahənin yuxarı səviyyəli məhsullarının DSK 018 üzrə tonnajı); Əsas ssenaridə 2023–25-ci
illərin orta səviyyəsində, rıçaq kimi 2015–25-ci illərin maksimumunda; qiymət = manatla FR1 neft ixrac qiyməti,
qiymətləndirilmiş elastikliklə (birinci fərqlər, sabit irəli aparılmır; FR1-in proqnozunda məzənnə olmadığından məzənnə
sabit saxlanılır). Güc qaydası sahə üçün yalnız kəsimdən əvvəlki pəncərələrdə sektorla birgə artımdan daha dəqiq olduqda
qəbul edilir.

<!-- AUTO:oil -->
| sahə | ad | n_products | corr_dlnQ_dlnThroughput | real_growth_2015_25 | price_elasticity_oil | price_el_p | cap_factor_baseline | cap_factor_max | precut_RMSE_capacity | precut_RMSE_sector_rate | precut_DM_p | capacity_rule_adopted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 19 | Neft emalı məhsulları | 7 | 0.622 | -0.235 | 0.330 | 0.000 | 0.982 | 1.033 | 20.218 | 32.591 | 0.030 | bəli |
| 20 | Kimya məhsulları | 8 | 0.855 | 9.640 | 0.417 | 0.067 | 1.005 | 1.034 | 61.077 | 35.440 | 0.009 | xeyr |

İstehsal gücü qaydası qəbul edilib: Neft emalı məhsulları; Kimya məhsulları qeyri-neft bölüşdürməsinə qoşulur (güc qaydası kəsimdən əvvəl əhəmiyyətli dərəcədə az dəqiqdir, p 0,009).
<!-- /AUTO:oil -->

### 11.3 Qeyri-neft sahələri: əlaqəli sektorlar üzrə birləşdirilmiş tələb modeli

Tikinti materialları, hazır metal məmulatları və karxanalar ← tikinti; qida məhsulları və içkilər ← ev təsərrüfatlarının
istehlakı; maşın və avadanlıq, elektrik və nəqliyyat avadanlığı, təmir ← qeyri-neft investisiyası; digər sahələr ← öz
sektorlarının cəmi. Sahə payının əlaqəli sektor indeksinin sektor cəminə nisbəti üzrə vahid ümumi elastikliyi, birinci
fərqlərdə sahə sabit effektləri (dreyflər ekstrapolyasiya edilmir), softmax ilə yenidən normallaşdırma. Qayda əvvəlcədən
müəyyən edilib (FR4-də olduğu kimi): birləşdirilmiş model sabit paylardan p < 0,10 səviyyəsində daha dəqiq olarsa Əsas
ssenari kimi götürülür, əks halda ikisinin bərabər çəkili kombinasiyası götürülür ki, FR1-in sektor ssenariləri
sahələrə çatsın.

<!-- AUTO:pooled -->
β = 0,219 (Driscoll–Kraay s.x. 0,090, t(19) üzrə p 0,025; wild bootstrap p 0,089); 10 əlaqələndirilmiş sahə × 20 il; sabit effektli səviyyə qiyməti 0,082, birinci fərqlər üzrə 95% etibarlılıq intervalının [0,03; 0,41] daxilindədir.

| namizəd | RMSE_pp | DM_HLN_vs_const | DM_p_vs_const | target_years | qərar |
|---|---|---|---|---|---|
| sabit | 2.048 | — | — | — | — |
| birləşdirilmiş | 2.359 | 1.996 | 0.086 | 8.000 | — |
| kombinasiya | 2.195 | 2.010 | 0.084 | 8.000 | BASELINE |

Əsas bölüşdürmə: **birləşdirilmiş model ilə sabit payların bərabər çəkili kombinasiyası** (qərar qaydası əvvəlcədən müəyyən edilib). Kəsimdən əvvəlki pəncərələrdə birləşdirilmiş model sabit paylardan az dəqiqdir (2,359 və 2,048 f.b., DM p 0,086), kombinasiya isə 2,195 f.b. (p 0,084): əlaqəli sektor kanalı iqtisadi cəhətdən əsaslandırılmış, nümunədaxili statistik əhəmiyyətli elastiklikdir, lakin onun bölüşdürmədə nümunədən kənar üstünlüyü müəyyən edilməyib.
<!-- /AUTO:pooled -->

### 11.4 Mədənçıxarma: qeyri-neft sahələri birbaşa modelləşdirilir

Karxanalar (v2): FR1-in tikinti əlavə dəyəri ilə vahid elastiklikli əlaqə yalnız kəsimdən əvvəlki dizaynda lövbərlənmiş
sıfır modeldən — real buraxılış son faktiki səviyyəsində sabit, FR1-in tikinti deflyatoru ilə qiymətləndirilmiş —
əhəmiyyətli dərəcədə daha dəqiq olduqda qəbul edilir; hər iki qayda başlanğıcın son faktiki dəyərinə lövbərlənir (hədəf
ili üzrə DM/HLN, p < 0,10). Belə deyil (sıfır model əhəmiyyətli dərəcədə daha dəqiqdir, sərbəst elastiklik isə vahid
məhdudiyyətini rədd edir), buna görə Əsas ssenari karxanaların real buraxılışını 2026-cı ildə sıçrayış olmadan 2025-ci
il səviyyəsində saxlayır, tikinti əlaqəsi isə mühərrikdə `quarrying_rule` rıçağı kimi saxlanılır; metal filizləri,
FR1 sürücüsü kəsimdən əvvəl üstün gəlmədikcə, FR1-in ÜDM deflyatoru ilə 2023–25-ci illərin orta səviyyəsində saxlanılır;
xam neft və təbii qaz, habelə mədənçıxarma üzrə köməkçi xidmətlər FR1-in neft-qaz real ÜDM-ini izləyir, onların nominal
buraxılışı isə FR1-in mədənçıxarma buraxılışının qalığıdır, beləliklə bölmə dəqiq uzlaşır. Eyni məntiq emal sənayesində
də tətbiq olunur (neft emalı neft hissəsidir); elektrik enerjisi və su təchizatı müstəqil bölmələrdir.

<!-- AUTO:mining -->
| qayda | RMSE_log_pct | DM_p_vs_first | qərar | sahə |
|---|---|---|---|---|
| neytral: son faktiki səviyyədə saxlanılır | 67.384 | — | CHOSEN | 8 |
| tikintiyə görə vahid elastiklik | 89.668 | 0.042 | — | 8 |
| tikintiyə görə qiymətləndirilmiş elastiklik | 84.157 | 0.011 | yalnız məlumat üçün | 8 |
| neytral: son 3 ilin orta səviyyəsində saxlanılır | 79.006 | — | — | 7 |
| FR1 mədənçıxarma əlavə dəyəri ilə birgə artır | 72.297 | 0.009 | CHOSEN | 7 |
| FR1 tikinti əlavə dəyəri ilə birgə artır | 85.660 | 0.198 | — | 7 |

Digər faydalı qazıntılar: **neytral: son faktiki səviyyədə saxlanılır** — FR1-in tikinti əlavə dəyəri ilə vahid elastiklikli əlaqə neytral sıfır modelə qarşı: DM/HLN p = 0,042 (hər iki qayda başlanğıcın son faktiki dəyərinə lövbərlənib; kəsimdən əvvəl RMSE 89,7, sıfır model üçün 67,4 log-%; əlaqə yalnız əhəmiyyətli dərəcədə DAHA dəqiq olduqda qəbul edilir, p < 0,10); sərbəst elastiklik 0,111 (s.x. 0,334) vahid məhdudiyyətini rədd edir (p = 0,016). Tikinti əlaqəsi mühərrikdə `quarrying_rule` rıçağı kimi saxlanılır. Metal filizlərinin hasilatı: FR1-in mədənçıxarma əlavə dəyəri ilə artır. Xam neft və təbii qaz hasilatı: 33 349,0 → 31 475,2 mln manat nominal, real ildə -1,21%. Metal filizlərinin hasilatı: 729,9 → 854,2 mln manat nominal, real ildə -1,10%. Digər faydalı qazıntılar: 244,8 → 273,1 mln manat nominal, real ildə +0,00%. Mədənçıxarma sahəsində xidmətlər: 2 698,4 → 2 546,8 mln manat nominal, real ildə -1,21%. Uzlaşdırma: dörd sahənin cəmi hər ssenaridə və hər ildə FR1-in mədənçıxarma buraxılışına 2,2·10⁻¹⁴% dəqiqliklə bərabərdir (yoxlanılır); neft hissəsinin nəzərdə tutulan deflyatoru ildə +0,06% artır, FR1-in mədənçıxarma deflyatoru isə +0,07%.
<!-- /AUTO:mining -->

### 11.5 Regionlar

κ qaydası: sabit paylar spesifikasiya mərhələsində rədd edildikdə büzülmə intensivliyi sabit paylardan əhəmiyyətli
dərəcədə daha dəqiq olan κ dəyərləri arasında (heç biri belə deyilsə, geri qalmayanlar arasında) RMSE-si ən aşağı
olan κ kimi seçilir.

<!-- AUTO:regions -->
Seçilib: MNL: neft sektoru qarışığı (FR1 mədənçıxarma/emal sənayesi əlavə dəyəri), κ = 0,5. Bakının sənaye buraxılışındakı payı 2025-ci ildə 79,9%; 2030-cu ildə: Əsas 78,0%, Mənfi 76,9%, İslahat 78,4%.
<!-- /AUTO:regions -->

## 12. Nümunədən kənar yoxlama, 2020–2025

Faktiki istifadə olunan proqnoz modeli 2019-cu ilədək məlumatlar üzrə yenidən qiymətləndirilir (birləşdirilmiş
elastiklik, neft qiyməti elastikliyi, güc əmsalı) və FR1-in faktiki sektor əlavə dəyəri, deflyatorları, neft qiyməti və
əlaqəli sektor aqreqatları ilə 2020–2025 üçün simulyasiya olunur; FR10-un heç bir nəticəsi modelə verilmir. Müqayisə
meyarları: təsadüfi gəzişmə və sabit artım (öz 2014–2019 ortası).

<!-- AUTO:holdout -->
| sistem | göstərici | çəkiləndirmə | model | RMSE | U_vs_random_walk | U_vs_constant_growth | DM_p_vs_rw | DM_p_vs_cg |
|---|---|---|---|---|---|---|---|---|
| emal sənayesi (24 sahə): proqnoz modeli | nominal | çəkisiz | neft bloku + kombinasiya | 50.664 | 0.793 | 0.823 | 0.099 | 0.180 |
| emal sənayesi (24 sahə): proqnoz modeli | nominal | paylarla çəkilənmiş | neft bloku + kombinasiya | 38.160 | 0.814 | 0.981 | 0.039 | 0.714 |
| emal sənayesi (24 sahə): proqnoz modeli | real | çəkisiz | neft bloku + kombinasiya | 56.492 | 0.801 | 0.525 | 0.044 | 0.041 |
| emal sənayesi (24 sahə): proqnoz modeli | real | paylarla çəkilənmiş | neft bloku + kombinasiya | 30.814 | 0.765 | 0.704 | 0.088 | 0.051 |
| 14 iqtisadi rayon | shares_pp | çəkisiz | MNL: neft sektoru strukturu (FR1 mədənçıxarma/emal sənayesi əlavə dəyəri) | 0.877 | 0.789 | 0.330 | 0.051 | 0.047 |
<!-- /AUTO:holdout -->

<!-- AUTO:holdout_note -->
Sahələrin real buraxılışı **sabit artımdan daha dəqiqdir**: çəkisiz U = 0,525 (əhəmiyyətli dərəcədə yaxşı, DM p 0,041) və paylarla çəkilənmiş 0,704 (əhəmiyyətli dərəcədə yaxşı, DM p 0,051); Hissə 11-in sabit pay sistemi üçün göstəricilər 0,531 (p 0,039, çəkisiz) və 0,701 (p 0,031, paylarla çəkilənmiş) idi. Sahələrin real yolları zolaqları ilə birlikdə oxunmalıdır; nominal buraxılış daha etibarlı nəticədir.
<!-- /AUTO:holdout_note -->

Eyni model daxilində alternativ bölüşdürmələr (yalnız məlumat üçün):

<!-- AUTO:holdout_full_alt -->
| göstərici | çəkiləndirmə | model | RMSE | U_vs_random_walk | U_vs_constant_growth |
|---|---|---|---|---|---|
| nominal | çəkisiz | neft bloku + birləşdirilmiş model | 50.821 | 0.795 | 0.826 |
| nominal | paylarla çəkilənmiş | neft bloku + birləşdirilmiş model | 37.915 | 0.809 | 0.975 |
| real | çəkisiz | neft bloku + birləşdirilmiş model | 56.579 | 0.803 | 0.526 |
| real | paylarla çəkilənmiş | neft bloku + birləşdirilmiş model | 30.628 | 0.760 | 0.700 |
| nominal | çəkisiz | neft bloku + sabit paylar | 50.538 | 0.791 | 0.821 |
| nominal | paylarla çəkilənmiş | neft bloku + sabit paylar | 38.425 | 0.820 | 0.988 |
| real | çəkisiz | neft bloku + sabit paylar | 56.437 | 0.801 | 0.525 |
| real | paylarla çəkilənmiş | neft bloku + sabit paylar | 31.027 | 0.770 | 0.709 |
<!-- /AUTO:holdout_full_alt -->

2019-cu ilədək yenidən qiymətləndirilmiş Hissə 11.1 pay sistemləri (yalnız məlumat üçün; heç bir seçim üçün istifadə
olunmur):

<!-- AUTO:holdout_info -->
| sistem | göstərici | model | RMSE | U_vs_random_walk | U_vs_constant_growth |
|---|---|---|---|---|---|
| emal sənayesi (24 sahə) (Hissə 11, pay sistemləri) | nominal | sabit paylar | 47.315 | 0.740 | 0.769 |
| emal sənayesi (24 sahə) (Hissə 11, pay sistemləri) | shares_pp | sabit paylar | 1.462 | 1.000 | 0.586 |
| emal sənayesi (24 sahə) (Hissə 11, pay sistemləri) | nominal | MNL: miqyas (FR1 real sektor əlavə dəyəri) | 63.336 | 0.991 | 1.029 |
| emal sənayesi (24 sahə) (Hissə 11, pay sistemləri) | shares_pp | MNL: miqyas (FR1 real sektor əlavə dəyəri) | 2.247 | 1.537 | 0.901 |
| emal sənayesi (24 sahə) (Hissə 11, pay sistemləri) | nominal | MNL: neft ixrac qiyməti | 48.597 | 0.760 | 0.790 |
| emal sənayesi (24 sahə) (Hissə 11, pay sistemləri) | shares_pp | MNL: neft ixrac qiyməti | 1.458 | 0.997 | 0.585 |
| emal sənayesi (24 sahə) (Hissə 11, pay sistemləri) | nominal | MNL: miqyas + neft qiyməti | 66.203 | 1.036 | 1.076 |
| emal sənayesi (24 sahə) (Hissə 11, pay sistemləri) | shares_pp | MNL: miqyas + neft qiyməti | 2.134 | 1.460 | 0.856 |
| emal sənayesi (24 sahə) (Hissə 11, pay sistemləri) | nominal | kombinasiya: 1/2 sabit paylar + 1/2 MNL miqyas | 53.326 | 0.834 | 0.866 |
| emal sənayesi (24 sahə) (Hissə 11, pay sistemləri) | shares_pp | kombinasiya: 1/2 sabit paylar + 1/2 MNL miqyas | 1.509 | 1.033 | 0.605 |
| mədənçıxarma (4 sahə) (Hissə 11, pay sistemləri) | nominal | sabit paylar | 55.733 | 0.962 | 0.616 |
| mədənçıxarma (4 sahə) (Hissə 11, pay sistemləri) | shares_pp | sabit paylar | 3.122 | 1.000 | 0.337 |
| mədənçıxarma (4 sahə) (Hissə 11, pay sistemləri) | nominal | MNL: miqyas (FR1 real sektor əlavə dəyəri) | 55.733 | 0.962 | 0.616 |
| mədənçıxarma (4 sahə) (Hissə 11, pay sistemləri) | shares_pp | MNL: miqyas (FR1 real sektor əlavə dəyəri) | 3.122 | 1.000 | 0.337 |
| mədənçıxarma (4 sahə) (Hissə 11, pay sistemləri) | nominal | MNL: neft ixrac qiyməti | 53.597 | 0.925 | 0.593 |
| mədənçıxarma (4 sahə) (Hissə 11, pay sistemləri) | shares_pp | MNL: neft ixrac qiyməti | 2.695 | 0.863 | 0.291 |
| mədənçıxarma (4 sahə) (Hissə 11, pay sistemləri) | nominal | MNL: miqyas + neft qiyməti | 49.263 | 0.850 | 0.545 |
| mədənçıxarma (4 sahə) (Hissə 11, pay sistemləri) | shares_pp | MNL: miqyas + neft qiyməti | 1.976 | 0.633 | 0.213 |
| mədənçıxarma (4 sahə) (Hissə 11, pay sistemləri) | nominal | kombinasiya: 1/2 sabit paylar + 1/2 MNL miqyas | 55.733 | 0.962 | 0.616 |
| mədənçıxarma (4 sahə) (Hissə 11, pay sistemləri) | shares_pp | kombinasiya: 1/2 sabit paylar + 1/2 MNL miqyas | 3.122 | 1.000 | 0.337 |
| 14 iqtisadi rayon | shares_pp | sabit paylar | 1.111 | 1.000 | 0.418 |
| 14 iqtisadi rayon | shares_pp | MNL: miqyas (FR1 real sektor əlavə dəyəri) | 0.888 | 0.799 | 0.334 |
| 14 iqtisadi rayon | shares_pp | MNL: miqyas + neft sektoru strukturu | 0.928 | 0.835 | 0.349 |
| 14 iqtisadi rayon | shares_pp | kombinasiya: 1/2 sabit paylar + 1/2 MNL miqyas | 0.931 | 0.838 | 0.351 |
<!-- /AUTO:holdout_info -->

## 13. FR1-in üç ssenarisi üzrə 2026–2030 proqnozu

Bölmə buraxılışı = 2025-ci il buraxılışı × FR1-in nominal əlavə dəyər indeksi. Neft emalı §11.2-yə uyğun; emal
sənayesinin qalan buraxılışı §11.3-ə uyğun olaraq qeyri-neft sahələrinə bölüşdürülür; mədənçıxarma sahələri §11.4-ə
uyğun. Qeyri-neft real buraxılışı = nominal ÷ (2025 deflyatoru × FR1-in bölmə deflyatoru indeksi). Məşğulluq = 2025-ci
il üzrə DSK-nın işçi sayı × FR4-ün bölmə indeksi; əmək haqqı (məhsuldarlıq və marja həssaslıqları üçün) = 2025-ci il
üzrə DSK-nın əmək haqqı × FR1-in orta əmək haqqı indeksi (F13).

<!-- AUTO:forecast -->
| ssenari | sənaye nominal buraxılışının artımı, illik % | emal sənayesi nominal artım, illik % | emal sənayesi real artım, illik % (FR1 rva_man) | neft emalı real artım, illik % | mədənçıxarmanın sənayedə payı 2030 % | qeyri-dövlət payı 2030 % (struktur üzrə) | HHI emal sənayesi 2030 | Bakı şəhərinin payı 2030 % | emal sənayesi ümumi mənfəət, ƏD-nin %-i 2030 |
|---|---|---|---|---|---|---|---|---|---|
| Əsas | 4.21 | 10.52 | 6.38 | -0.36 | 45.39 | 77.36 | 1203.20 | 77.97 | 65.81 |
| Mənfi | -1.53 | 6.62 | 2.90 | -0.36 | 38.05 | 73.89 | 1218.78 | 76.91 | 65.81 |
| İslahat | 8.80 | 14.30 | 9.74 | -0.36 | 48.79 | 79.44 | 1189.66 | 78.41 | 65.81 |

Bölmələr, Əsas ssenari:

| bölmə | nominal buraxılışın artımı, ildə % | GOS, əlavə dəyərin %-i, 2025 | GOS, əlavə dəyərin %-i, 2030 |
|---|---|---|---|
| Mədənçıxarma | -1.03 | 93.56 | 94.39 |
| Emal sənayesi | 10.52 | 65.82 | 65.81 |
| Elektrik enerjisi | 8.69 | 65.44 | 65.89 |
| Su təchizatı | 8.54 | -51.61 | -40.05 |
<!-- /AUTO:forecast -->

**Sahələr.**

<!-- AUTO:branches -->
| nace2 | sahə | model | nominal artım, illik % | real artım, illik % | sənayedə payı 2030, % | əmək məhsuldarlığının artımı, illik % |
|---|---|---|---|---|---|---|
| 06 | Xam neft və təbii qaz hasilatı | FR1 neft və qaz (real); qalıq (nominal) | -1.15 | -1.21 | 40.65 | -0.51 |
| 07 | Metal filizlərinin hasilatı | metal filizləri: FR1 mədənçıxarma əlavə dəyəri ilə birgə artır | 3.20 | -1.10 | 1.10 | -0.40 |
| 08 | Digər faydalı qazıntılar | digər faydalı qazıntılar: neytral: son faktiki səviyyədə saxlanılır | 2.21 | 0.00 | 0.35 | 0.70 |
| 09 | Mədənçıxarma sahəsində xidmətlər | FR1 neft və qaz (real); qalıq (nominal) | -1.15 | -1.21 | 3.29 | -0.51 |
| 10 | Qida məhsulları | əlaqəli sektor: rcons | 13.47 | 9.22 | 12.11 | 8.42 |
| 11 | İçkilər | əlaqəli sektor: rcons | 13.47 | 9.22 | 2.23 | 8.42 |
| 12 | Tütün məmulatları | sektor üzrə cəmi | 13.77 | 9.50 | 2.75 | 8.70 |
| 13 | Toxuculuq məhsulları | sektor üzrə cəmi | 13.77 | 9.50 | 1.02 | 8.70 |
| 14 | Geyim | sektor üzrə cəmi | 13.77 | 9.50 | 0.49 | 8.70 |
| 15 | Dəri və ayaqqabı | sektor üzrə cəmi | 13.77 | 9.50 | 0.09 | 8.70 |
| 16 | Ağac emalı | sektor üzrə cəmi | 13.77 | 9.50 | 0.09 | 8.70 |
| 17 | Kağız və karton | sektor üzrə cəmi | 13.77 | 9.50 | 0.67 | 8.70 |
| 18 | Poliqrafiya | sektor üzrə cəmi | 13.77 | 9.50 | 0.38 | 8.70 |
| 19 | Neft emalı məhsulları | istehsal gücü + neft qiyməti | -0.96 | -0.36 | 6.76 | -1.09 |
| 20 | Kimya məhsulları | sektor üzrə cəmi | 13.77 | 9.50 | 3.89 | 8.70 |
| 21 | Əczaçılıq məhsulları | sektor üzrə cəmi | 13.77 | 9.50 | 0.07 | 8.70 |
| 22 | Rezin və plastik kütlə | sektor üzrə cəmi | 13.77 | 9.50 | 1.61 | 8.70 |
| 23 | Digər qeyri-metal mineral məhsullar | əlaqəli sektor: rva_con | 13.12 | 8.88 | 3.55 | 8.08 |
| 24 | Metallurgiya | sektor üzrə cəmi | 13.77 | 9.50 | 2.77 | 8.70 |
| 25 | Hazır metal məmulatları | əlaqəli sektor: rva_con | 13.12 | 8.88 | 1.78 | 8.08 |
| 26 | Kompüter və elektronika | sektor üzrə cəmi | 13.77 | 9.50 | 0.17 | 8.70 |
| 27 | Elektrik avadanlığı | əlaqəli sektor: rinv_non | 13.31 | 9.06 | 0.67 | 8.26 |
| 28 | Maşın və avadanlıq | əlaqəli sektor: rinv_non | 13.31 | 9.06 | 0.31 | 8.26 |
| 29 | Avtomobil və qoşqular | əlaqəli sektor: rinv_non | 13.31 | 9.06 | 0.82 | 8.26 |
| 30 | Digər nəqliyyat vasitələri | əlaqəli sektor: rinv_non | 13.31 | 9.06 | 0.10 | 8.26 |
| 31 | Mebel | sektor üzrə cəmi | 13.77 | 9.50 | 0.97 | 8.70 |
| 32 | Digər hazır məmulatlar | sektor üzrə cəmi | 13.77 | 9.50 | 0.30 | 8.70 |
| 33 | Maşın və avadanlığın təmiri və quraşdırılması | əlaqəli sektor: rinv_non | 13.31 | 9.06 | 2.64 | 8.26 |
| 35 | Elektrik enerjisi, qaz və buxar | sektor üzrə cəmi | 8.69 | 2.90 | 7.08 | 2.38 |
| 36 | Su təchizatı, tullantılar | sektor üzrə cəmi | 8.54 | 4.53 | 1.29 | 3.87 |

Emal sənayesi sahələri, Əsas ssenaridə 2026–2030 dövründə real artım: minimum -0,36% (Neft emalı məhsulları), maksimum +9,50% (Tütün məmulatları). Qeyri-neft emal sənayesinin nəzərdə tutulan real artımı ildə +8,86%; müqayisə üçün: +8,11% (2010–19), +9,45% (2021–25), ən yaxşı beşillik +10,32% — tarixi hədlər daxilində.

Nəzərdə tutulan sektorlararası multiplikatorlar (sektor cəmi verilmiş halda əlaqəli sektorda 1% dəyişməyə görə sahə buraxılışının %-lə dəyişməsi):

| nace2 | sahə | related_sector | multiplikator | multiplier_p5 | multiplier_p95 |
|---|---|---|---|---|---|
| 23 | Digər qeyri-metal mineral məhsullar | rva_con | 0.100 | 0.032 | 0.167 |
| 25 | Hazır metal məmulatları | rva_con | 0.105 | 0.034 | 0.175 |
| 08 | Digər faydalı qazıntılar | rva_con | 0.109 | 0.035 | 0.182 |
| 10 | Qida məhsulları | rcons | 0.076 | 0.025 | 0.127 |
| 11 | İçkilər | rcons | 0.103 | 0.034 | 0.173 |
| 27 | Elektrik avadanlığı | rinv_non | 0.108 | 0.035 | 0.181 |
| 28 | Maşın və avadanlıq | rinv_non | 0.109 | 0.035 | 0.182 |
| 29 | Avtomobil və qoşqular | rinv_non | 0.107 | 0.035 | 0.180 |
| 30 | Digər nəqliyyat vasitələri | rinv_non | 0.109 | 0.035 | 0.183 |
| 33 | Maşın və avadanlığın təmiri və quraşdırılması | rinv_non | 0.102 | 0.033 | 0.171 |
<!-- /AUTO:branches -->

**Əməliyyat mənfəəti marjası — şərti.** Əsas ssenari hər bölmədə əməyin əlavə dəyərdəki payını 2023–25-ci illərin
orta səviyyəsində saxlayır, buna görə marja quruluşca neytraldır; o, **ödəmə qabiliyyətini deyil, pul vəsaiti
yaradılmasını və rentanı** ölçür (balans hesabatı daxil edilmir). Sahə üzrə GOS proksi göstəricisi digər vergiləri və
işçi olmayanlara ödənişləri də nəzərə almır və DSK-nın sahə buraxılışına qeydə alınmış əmək haqqı fondu olmayan qeyri-formal
və ev təsərrüfatı istehsalı daxil olduğundan, qeyri-formal buraxılışı çox olan sahələrdə marjaları şişirdir.

<!-- AUTO:margin -->
Əsas ssenari (əməyin əlavə dəyərdəki payı 2023–25 ortasında saxlanılır): emal sənayesində GOS 2025-ci ildə əlavə dəyərin 65,8%-i, 2030-cu ildə 65,8%-i. Həssaslıqlar: FR1-in əmək haqqı yolu 70,5%; məhsul ifadəsində sabit əmək haqqı 73,8%. Sahələr üzrə GOS proksi marjasının medianı 2030: Əsas ssenari 19,7%, FR1-in əmək haqqı yolu 23,9%.

| rıçaq | emal sənayesi sahələrinin real artımı, minimum, illik % | emal sənayesi sahələrinin real artımı, maksimum, illik % | neft emalı real artım, illik % | tikinti materialları real artım, illik % | emal sənayesi ümumi mənfəət, ƏD-nin %-i 2030 | sahələr üzrə median ümumi mənfəət (proksi) marjası 2030 | HHI emal sənayesi 2030 |
|---|---|---|---|---|---|---|---|
| Əsas | -0.36 | 9.50 | -0.36 | 8.88 | 65.81 | 19.71 | 1203.20 |
| bölgü: yalnız birləşdirilmiş model | -0.36 | 9.74 | -0.36 | 8.49 | 65.81 | 19.71 | 1200.75 |
| bölgü: sabit paylar | -0.36 | 9.26 | -0.36 | 9.26 | 65.81 | 19.71 | 1205.74 |
| neftlə bağlı sahələr maksimal emal həcmində | 0.66 | 9.30 | 0.66 | 8.68 | 65.81 | 19.71 | 1208.47 |
| marja: FR1 əmək haqqı trayektoriyası | -0.36 | 9.50 | -0.36 | 8.88 | 70.51 | 23.86 | 1203.20 |
| marja: məhsul ifadəsində sabit əmək haqqı | -0.36 | 9.50 | -0.36 | 8.88 | 73.76 | 25.39 | 1203.20 |
<!-- /AUTO:margin -->

**Qeyri-dövlət payı.**

<!-- AUTO:ns -->
Mədənçıxarmanın sənaye buraxılışındakı payı 58,8%-dən 45,4%-ə enir (Əsas ssenari); sahələr daxilində qeyri-dövlət payları sabit saxlanıldıqda (mədənçıxarma 94,1%, neft emalı 1,9%, elektrik enerjisi 3,4%) sənayedə qeyri-dövlət payı 78,1%-dən 77,4%-ə dəyişir — **bu, mülkiyyət proqnozu deyil, sırf tərkib effektidir**.

| nace2 | sahə | qeyri-dövlət payı sabit saxlanılır (2025), % | sənayedə pay 2025, % | sənayedə pay 2030, % |
|---|---|---|---|---|
| 6 | Xam neft və təbii qaz hasilatı | 95.71 | 52.93 | 40.65 |
| 7 | Metal filizlərinin hasilatı | 39.61 | 1.16 | 1.10 |
| 8 | Digər faydalı qazıntılar | 98.02 | 0.39 | 0.35 |
| 9 | Mədənçıxarma sahəsində xidmətlər | 88.50 | 4.28 | 3.29 |
| 10 | Qida məhsulları | 99.99 | 7.91 | 12.11 |
| 11 | İçkilər | 99.11 | 1.45 | 2.23 |
| 12 | Tütün məmulatları | 100.00 | 1.77 | 2.75 |
| 13 | Toxuculuq məhsulları | 91.75 | 0.65 | 1.02 |
| 14 | Geyim | 95.73 | 0.31 | 0.49 |
| 15 | Dəri və ayaqqabı | 94.94 | 0.06 | 0.09 |
| 16 | Ağac emalı | 99.84 | 0.06 | 0.09 |
| 17 | Kağız və karton | 100.00 | 0.43 | 0.67 |
| 18 | Poliqrafiya | 98.44 | 0.24 | 0.38 |
| 19 | Neft emalı məhsulları | 1.86 | 8.72 | 6.76 |
| 20 | Kimya məhsulları | 20.13 | 2.51 | 3.89 |
| 21 | Əczaçılıq məhsulları | 100.00 | 0.05 | 0.07 |
| 22 | Rezin və plastik kütlə | 100.00 | 1.04 | 1.61 |
| 23 | Digər qeyri-metal mineral məhsullar | 99.60 | 2.36 | 3.55 |
| 24 | Metallurgiya | 100.00 | 1.79 | 2.77 |
| 25 | Hazır metal məmulatları | 60.39 | 1.18 | 1.78 |
| 26 | Kompüter və elektronika | 92.74 | 0.11 | 0.17 |
| 27 | Elektrik avadanlığı | 98.83 | 0.44 | 0.67 |
| 28 | Maşın və avadanlıq | 93.75 | 0.21 | 0.31 |
| 29 | Avtomobil və qoşqular | 76.47 | 0.54 | 0.82 |
| 30 | Digər nəqliyyat vasitələri | 87.96 | 0.07 | 0.10 |
| 31 | Mebel | 100.00 | 0.62 | 0.97 |
| 32 | Digər hazır məmulatlar | 89.80 | 0.19 | 0.30 |
| 33 | Maşın və avadanlığın təmiri və quraşdırılması | 54.15 | 1.74 | 2.64 |
| 35 | Elektrik enerjisi, qaz və buxar | 3.37 | 5.73 | 7.08 |
| 36 | Su təchizatı, tullantılar | 29.10 | 1.05 | 1.29 |
<!-- /AUTO:ns -->

**Məhsullar.** Məhsul həcmi yolları məhsul tərkibi sabit saxlanılmaqla və 2025-ci il faktiki səviyyəsinə lövbərlənməklə
sahə proqnozundan hesablanır (v2.1: volume_t = volume_2025 × sahənin real buraxılışı_t / real buraxılış_2025, sabit baza
düzəliş əmsalı; məhsul modeli deyil, işarələnmiş törəmə hesablama); məhsul bazar payları istehsal yerləri üzrədir
(DSK 018_1).

<!-- AUTO:products -->
25 sahədə 127 məhsul **törəmə** həcm yolları alır (məhsul tərkibi 2023–25 səviyyəsində saxlanılır); 2025-ci ildə 91 məhsulun istehsal yerləri var (yerlərin sayının medianı 3, ən böyük yerin payının medianı 81%). İstehsal yerləri üzrə ən konsentrasiyalı:

| məhsul | yerlər | top_place | top_place_share_pct | HHI_places | coverage_of_national_pct |
|---|---|---|---|---|---|
| Yüngül neft məhsulları, yüngül distillatlar, min ton | 1 | Bakı şəhəri | 100.0 | 10000.0 | 100.0 |
| Pambıq ipliyi, ton | 1 | Bakı şəhəri | 100.0 | 10000.0 | — |
| Dərmanlar, min manat | 1 | Bakı şəhəri | 100.0 | 10000.0 | 100.0 |
| Mayonez, ton | 1 | Sumqayıt şəhəri | 100.0 | 10000.0 | 100.0 |
| Sürtkü yağları, min ton | 1 | Bakı şəhəri | 100.0 | 10000.0 | 100.0 |
| Alüminium borular, ton | 1 | Gəncə şəhəri | 100.0 | 10000.0 | 100.0 |
| Noutbuklar, ədəd | 1 | Mingəçevir şəhəri | 100.0 | 10000.0 | 100.0 |
| Ağ neft, min ton | 1 | Bakı şəhəri | 100.0 | 10000.0 | 100.0 |
<!-- /AUTO:products -->

**Qeyri-müəyyənlik.** FR1-in Əsas ssenari üzrə 500 təkrarlamasının hər biri mərkəzləşdirilmiş tarixi model xətası yolu
(model qalıqlarının $e_h = u_{s+h} - u_s$ fərqi, vahidlər üzrə birgə; qiymətləndirilmiş avtokorrelyasiya yoxdur), işarə
üzrə rədd etmə ilə parametr çəkilişləri və FR1-in məşğulluq çəkilişi ilə birləşdirilir; paket simulyasiyası ssenari
həlledicisini dəqiq təkrarlayır.

<!-- AUTO:bands -->
FR1-in 500 təkrarlaması; sahə bölüşdürməsi üçün 16, regionlar üçün 11 tarixi model xətası yolu (2019-cu il əhatə qırılmasını keçən yollar istisna edilib). 2026–2030 dövründə orta artım — sənaye buraxılışı: Əsas +4,21%, median +4,81%, 90% zolaq -4,3%-dən +14,6%-ədək; mədənçıxarma: Əsas -1,03%, median -0,96%, 90% zolaq -12,1%-dən +10,2%-ədək; emal sənayesi: Əsas +10,52%, median +10,22%, 90% zolaq -0,4%-dən +22,7%-ədək; elektrik enerjisi: Əsas +8,69%, median +8,71%, 90% zolaq -13,6%-dən +43,5%-ədək; su təchizatı: Əsas +8,54%, median +8,45%, 90% zolaq -1,8%-dən +19,9%-ədək. Əsas ssenari FR1-in ssenari yoludur, median isə təkrarlamaların medianıdır; FR1-in çəkilişləri onun ssenarisi ətrafında mərkəzləşmədiyindən onlar fərqlənir. Sənaye və elektrik enerjisi üzrə geniş quyruqlar FR1-in neft və elektrik enerjisi qiymətləri çəkilişlərindən irəli gəlir: FR1-in qiymətləri baza yollarında saxlanıldıqda zolaqlar belədir — sənaye: Əsas +4,21%, median +4,16%, 90% zolaq +1,3%-dən +8,2%-ədək; elektrik enerjisi: Əsas +8,69%, median +8,69%, 90% zolaq +6,0%-dən +11,7%-ədək. 2030-cu ildə neft emalının emal sənayesindəki payı: 9,0–24,4% (Əsas 14,6%). 2030-cu ildə emal sənayesində GOS-un əlavə dəyərdəki payı: 65,8–65,8%. Sıra-illərin 98,8%-ində Əsas ssenari kvartillərarası zolağın, 100,0%-ində 90% zolağın daxilindədir.
<!-- /AUTO:bands -->

## 14. İnandırıcılıq və erkən xəbərdarlıq

Hər proqnoz artım tempi vahidin öz 2010–2019 və 2021–2025 orta göstəriciləri, habelə 2005-ci ildən bəri ən yaxşı və
ən pis beşillik orta göstəriciləri ilə müqayisə olunur; işarələr əsas səbəbləri ilə birlikdə dərc olunur.

<!-- AUTO:plaus -->
| kod | vahid | forecast_real_growth | hist_2010_2019 | hist_2021_2025 | best_5yr | worst_5yr | işarə | hist_2010_19_inside_90band |
|---|---|---|---|---|---|---|---|---|
| 06 | Xam neft və təbii qaz hasilatı | -1.21 | -2.57 | -0.01 | 17.50 | -3.46 | — | xeyr |
| 07 | Metal filizlərinin hasilatı | -1.10 | 10.43 | -0.42 | 252.03 | -8.81 | — | xeyr |
| 08 | Digər faydalı qazıntılar | 0.00 | 12.22 | 15.14 | 27.98 | -8.70 | — | xeyr |
| 09 | Mədənçıxarma sahəsində xidmətlər | -1.21 | 18.79 | -18.41 | 27.50 | -20.68 | — | xeyr |
| 10 | Qida məhsulları | 9.22 | 3.80 | 10.22 | 10.22 | 2.39 | — | bəli |
| 11 | İçkilər | 9.22 | 8.73 | 7.56 | 10.96 | 0.24 | — | bəli |
| 12 | Tütün məmulatları | 9.50 | 16.66 | 13.10 | 50.73 | -14.63 | — | bəli |
| 13 | Toxuculuq məhsulları | 9.50 | 18.84 | 11.63 | 43.24 | -22.65 | — | bəli |
| 14 | Geyim | 9.50 | 10.32 | 5.29 | 21.66 | 0.71 | — | bəli |
| 15 | Dəri və ayaqqabı | 9.50 | -9.20 | 10.64 | 19.67 | -18.10 | — | bəli |
| 16 | Ağac emalı | 9.50 | 41.13 | -12.70 | 73.42 | -17.94 | — | xeyr |
| 17 | Kağız və karton | 9.50 | 6.84 | 7.41 | 60.85 | -18.43 | — | bəli |
| 18 | Poliqrafiya | 9.50 | 31.14 | -12.71 | 38.68 | -12.71 | — | xeyr |
| 19 | Neft emalı məhsulları | -0.36 | -3.18 | 3.78 | 3.78 | -5.46 | — | xeyr |
| 20 | Kimya məhsulları | 9.50 | 12.52 | 10.04 | 17.94 | -3.85 | — | bəli |
| 21 | Əczaçılıq məhsulları | 9.50 | -3.24 | 40.95 | 55.64 | -30.70 | — | bəli |
| 22 | Rezin və plastik kütlə | 9.50 | 11.86 | 16.26 | 28.01 | -2.69 | — | bəli |
| 23 | Digər qeyri-metal mineral məhsullar | 8.88 | 14.58 | 25.80 | 29.01 | -3.50 | — | bəli |
| 24 | Metallurgiya | 9.50 | 8.71 | 5.98 | 28.12 | -15.56 | — | bəli |
| 25 | Hazır metal məmulatları | 8.88 | 6.32 | 15.15 | 29.97 | -17.49 | — | bəli |
| 26 | Kompüter və elektronika | 9.50 | 14.59 | -2.03 | 31.08 | -4.94 | — | bəli |
| 27 | Elektrik avadanlığı | 9.06 | 29.25 | 3.96 | 49.69 | 1.45 | — | bəli |
| 28 | Maşın və avadanlıq | 9.06 | -3.70 | -22.20 | 33.34 | -22.20 | — | bəli |
| 29 | Avtomobil və qoşqular | 9.06 | 32.29 | 28.95 | 151.62 | -27.11 | — | bəli |
| 30 | Digər nəqliyyat vasitələri | 9.06 | -1.18 | 91.08 | 91.08 | -23.93 | — | bəli |
| 31 | Mebel | 9.50 | 32.66 | 21.72 | 34.29 | 9.58 | ən zəif 5 illik dövrdən AŞAĞI | xeyr |
| 32 | Digər hazır məmulatlar | 9.50 | 12.63 | 30.95 | 30.95 | -27.63 | — | bəli |
| 33 | Maşın və avadanlığın təmiri və quraşdırılması | 9.06 | 23.16 | 4.10 | 57.65 | -11.50 | — | bəli |
| 35 | Elektrik enerjisi, qaz və buxar | 2.90 | 3.96 | 2.08 | 7.48 | 0.73 | — | bəli |
| 36 | Su təchizatı, tullantılar | 4.53 | 4.47 | 9.07 | 9.07 | -4.22 | — | bəli |
| B | Mədənçıxarma | -1.10 | -2.21 | -1.39 | 23.44 | -3.37 | — | — |
| C | Emal sənayesi | 6.38 | 4.32 | 8.09 | 10.15 | 1.28 | — | — |
| D | Elektrik enerjisi | 2.90 | 4.21 | 2.06 | 7.57 | 0.36 | — | — |
| E | Su təchizatı | 4.53 | 4.51 | 8.88 | 8.88 | 0.59 | — | — |

İşarələnmiş vahidlər: 1 / 34.
<!-- /AUTO:plaus -->

Erkən xəbərdarlıq işarələri 2023–25-ci illərin ortasını 2020–22-ci illərin ortası ilə müqayisə edir və hər sahənin öz
dəyişkənliyi ilə miqyaslanır; emal sənayesinin 0,5%-dən az hissəsini təşkil edən sahələr yalnız hesabat üçün iki işarə
tələb edir, mənfi marja avtomatik müşahidə statusudur, çatışmayan investisiya isə heç vaxt sıfır deyil, "məlumat
kifayət deyil" kimi göstərilir. Bunlar qiymətləndirilmiş ehtimallar deyil, şəffaf idarəetmə paneli hədləridir.

<!-- AUTO:ew -->
| nace2 | sahə | share_2025_pct | margin_2023_25 | margin_z | share_z | lp_z | F_renewal | F_stocks | n_flags | watch_list |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 | Qida məhsulları | 22.96 | 20.33 | 0.18 | -2.45 | 1.83 | FLAG | FLAG | 3 | bəli |
| 11 | İçkilər | 4.22 | 26.51 | -0.10 | 1.87 | 2.13 | — | — | 0 | xeyr |
| 12 | Tütün məmulatları | 5.14 | 40.31 | 0.78 | 0.54 | 0.56 | — | — | 0 | xeyr |
| 13 | Toxuculuq məhsulları | 1.90 | 22.42 | -0.61 | -0.35 | 1.51 | — | — | 0 | xeyr |
| 14 | Geyim | 0.91 | 7.43 | 0.20 | -0.82 | -0.28 | FLAG | — | 1 | xeyr |
| 15 | Dəri və ayaqqabı | 0.16 | 11.86 | 0.70 | 0.17 | 4.10 | — | — | 0 | xeyr |
| 16 | Ağac emalı | 0.17 | 19.41 | -1.13 | -4.07 | -0.56 | məlumat kifayət deyil | — | 2 | xeyr |
| 17 | Kağız və karton | 1.25 | 17.09 | 3.43 | 1.68 | 0.53 | — | — | 0 | xeyr |
| 18 | Poliqrafiya | 0.71 | 27.97 | 0.70 | 0.77 | -0.91 | — | məlumat kifayət deyil | 0 | xeyr |
| 19 | Neft emalı məhsulları | 25.31 | 36.80 | -1.85 | 0.90 | 0.41 | — | — | 1 | xeyr |
| 20 | Kimya məhsulları | 7.28 | 27.44 | 0.25 | -0.26 | 3.28 | — | — | 0 | xeyr |
| 21 | Əczaçılıq məhsulları | 0.14 | 1.62 | 0.02 | 0.89 | 0.78 | — | məlumat kifayət deyil | 0 | bəli |
| 22 | Rezin və plastik kütlə | 3.02 | 14.67 | 1.62 | 0.59 | 2.98 | — | — | 0 | xeyr |
| 23 | Digər qeyri-metal mineral məhsullar | 6.84 | 24.15 | -0.19 | 1.17 | 3.24 | — | — | 0 | xeyr |
| 24 | Metallurgiya | 5.19 | 25.24 | -2.89 | 0.02 | -0.11 | — | — | 1 | xeyr |
| 25 | Hazır metal məmulatları | 3.43 | 17.04 | -0.58 | 0.17 | 1.53 | — | — | 0 | xeyr |
| 26 | Kompüter və elektronika | 0.32 | 22.22 | 0.63 | -0.29 | 1.75 | məlumat kifayət deyil | — | 0 | xeyr |
| 27 | Elektrik avadanlığı | 1.27 | 13.25 | 0.64 | -0.30 | 1.69 | — | — | 0 | xeyr |
| 28 | Maşın və avadanlıq | 0.60 | 22.53 | 1.11 | -0.49 | -0.23 | — | — | 0 | xeyr |
| 29 | Avtomobil və qoşqular | 1.56 | 19.77 | -0.00 | 2.09 | 1.97 | FLAG | — | 1 | xeyr |
| 30 | Digər nəqliyyat vasitələri | 0.19 | -44.89 | 0.70 | 1.26 | 1.99 | — | məlumat kifayət deyil | 0 | bəli |
| 31 | Mebel | 1.81 | 18.29 | 1.84 | 2.95 | 1.49 | FLAG | — | 1 | xeyr |
| 32 | Digər hazır məmulatlar | 0.56 | 17.41 | 0.05 | -0.78 | 0.23 | — | məlumat kifayət deyil | 0 | xeyr |
| 33 | Maşın və avadanlığın təmiri və quraşdırılması | 5.05 | 17.45 | 0.70 | 0.74 | -1.49 | — | məlumat kifayət deyil | 1 | xeyr |

Müşahidə siyahısı (3): Qida məhsulları, Əczaçılıq məhsulları, Digər nəqliyyat vasitələri.
<!-- /AUTO:ew -->

## 15. B qatı — əvəz edilə bilən müəssisə paneli üzərində müəssisə səviyyəli mühərrik

**Giriş məlumatları.** `data/firm_panel/` qovluğunda sintetik panel (qalın şriftlə iki dilli README vərəqi və sxem
vərəqi olan `FR10_firm_panel_SYNTHETIC.csv` və `.xlsx`), bir işarələnmiş nümunə sətri olan boş şablon
(`FR10_firm_panel_TEMPLATE.csv/.xlsx`), ingiliscə ↔ azərbaycanca ↔ vahid ↔ məcburi ↔ mənbə sütun xəritəsi
(`FR10_firm_panel_column_map.csv`) və `README_FR10_firm_panel.md` (AZ/EN) yerləşir. Sxem məlumat müqaviləsidir
(`output/FR10_input_schema.csv`): identifikatorlar, NACE Rev.2 sahəsi (iki rəqəmli kod; bütün bölmələr), region, mülkiyyət, ölçü qrupu,
balans hesabatı (bölüşdürülməmiş mənfəət, faizli borc, kreditor borcları daxil olmaqla), mənfəət-zərər hesabatı
(amortizasiya daxil olmaqla), əməliyyat pul axını, əsaslı xərclər, işçilər, əmək haqqı fondu, ixrac, məhsul kodları,
qeydiyyat və ləğv tarixləri.

**Yükləyici.** Prioritet: `FIRM_PANEL_PATH` (mühit dəyişəni və ya konfiqurasiya xanası) → `data/firm_panel/FR10_firm_panel.csv`
və ya `.xlsx` → SİNTETİK fayl. `data_status` dəyəri sintetik işarə olmayan və ya ümumiyyətlə olmayan fayl REAL sayılır.
İngilis və ya Azərbaycan dilində sütun başlıqları qəbul edilir. Validator hər sətir və sahə üzrə
`FR10_firm_panel_validation_report.csv` faylını yazır; ciddi xətalar (məcburi sütunun olmaması, qeyri-rəqəmsal və ya
mənfi dəyərlər, təkrarlar, yanlış kodlar, balans eynilikləri) icranı mesajla dayandırır; xəbərdarlıqlar (EBIT
uyğunluğu, bölüşdürülməmiş mənfəətin olmaması) dayandırmır. Sintetik generator yalnız SYNTHETIC adlı fayllar yazır və
heç vaxt real adlı fayl yazmır.

**Mühərrik.** Likvidlik, borc yükü, faiz ödənişinin örtülməsi, DuPont ROE, dövriyyə əmsalları, Altman Z''-EM (əmsallar
və zonalar Altman 2005-dən götürülür — qiymətləndirilmir; bölüşdürülməmiş mənfəət olmadıqda hesablanmır), müşahidə
olunan xərc payları ilə çoxtərəfli Törnqvist TFP indeksi, NACE × region üzrə paylar/HHI/CR4, giriş/çıxış/sağ qalma,
həmkarlar üzrə persentillər, müəssisə proqnozları = A qatının sahə proqnozu × proqnozlaşdırılan pay (payın artımı
gecikmiş nisbi məhsuldarlıq və borc yükü üzrə, HC1 xətaları, gecikmiş pay yoxdur). Nəticələr: SİNTETİK rejimdə
`FR10_SYNTHETIC_*.csv` (su nişanı ilə), REAL rejimdə `FR10_FIRM_*.csv`.

<!-- AUTO:layerb -->
**B qatının məlumat rejimi: SİNTETİK** — giriş faylı `data/firm_panel/FR10_firm_panel_SYNTHETIC.csv`, 22 495 sətir, 5 255 müəssisə, 24 NACE sahəsi, 2019–2025. Müəssisə paneli **SİNTETİKDİR — real müəssisə məlumatı deyil**; B qatının nəticələri tapıntılar deyil, emal xəttinin nümayişidir.

**Bu bölmə tapıntılar deyil, emal xəttinin nümayişidir.** Nazirlik `data/firm_panel/FR10_firm_panel_SYNTHETIC.csv` faylını öz sistemində öz məlumatları ilə (`FR10_firm_panel.csv/.xlsx` və ya `FIRM_PANEL_PATH`) əvəz edir və notebook-u yenidən icra edir; bundan sonra nəticələr `FR10_FIRM_*.csv` olur.

Yüklənmiş panel üzrə emal xətti testləri:

| test | dəyər | keçib |
|---|---|---|
| yoxlayıcı qəsdən daxil edilmiş 6 xətanı aşkarlayır (balans, NACE, mənfi pul vəsaiti) | 6 | bəli |
| DuPont: marja x dövriyyə x multiplikator = ROE (maks. mütləq fərq) | 1.4e-14 | bəli |
| TFP indeksi müəssisələr üzrə müstəqil təkrar hesablamaya bərabərdir (NACE 10, 2024; maks. mütləq fərq) | 8.9e-16 | bəli |
| bazar paylarının cəmi hər NACE-il xanasında birə bərabərdir (maks. fərq) | 2.2e-16 | bəli |
| müəssisə proqnozlarının cəmi A qatının sahə proqnozuna bərabərdir (%) | 2.2e-14 | bəli |
| müəssisə səviyyəsində ekonometrik modellər qiymətləndirilib (statsmodels = müstəqil numpy hesablaması, yoxlanılıb) | 14 | bəli |
| parametrlərin bərpası: ardıcıl qiymətləndiricilər həqiqi dəyərdən 4 standart xəta daxilindədir (say) | 30/30 | bəli |
| həmkar qrup daxilində persentil ranqları (0, 100] intervalındadır | 0.048 | bəli |
| müəssisə gəlirlərinin cəmi DSK-nın sahə buraxılışına bərabərdir (maks. fərq, %) | 1.5e-08 | bəli |
| müəssisələrin sayı DSK-nın fəaliyyət göstərən müəssisələrinin sayına bərabərdir (maks. fərq) | 0.000 | bəli |
| amillər modeli məlumat yaradan prosesi (DGP) bərpa edir (həqiqi qiymətlər 0.15, -0.30) | 0.152, -0.296 (s.e. 0.005, 0.010) | bəli |

Əvəzləmə testləri (müvəqqəti qovluq; layihədə heç vaxt almadığı real adlı fayl saxlanılmır):

| test | keçib | təfərrüat |
|---|---|---|
| real adlı fayl, neytral data_status ilə -> DATA_MODE = REAL | bəli | rejim REAL, fayl FR10_firm_panel.csv |
| REAL fayl validatordan keçir (0 kritik xəta) | bəli | 0 xəbərdarlıq |
| REAL rejimi yalnız FR10_FIRM_* fayllarını su nişanı olmadan yazır, bütün testlər keçir | bəli | 11 fayl, məs. ['FR10_FIRM_cohort_survival.csv', 'FR10_FIRM_concentration_nace.csv', 'FR10_FIRM_concentration_nace_region_2025.csv'] |
| Azərbaycan dilində başlıqlar (xlsx, FIRM_PANEL_PATH) yüklənir və yoxlamadan keçir | bəli | 3000 sətir, naməlum sütunlar [], rejim REAL |
| FIRM_PANEL_PATH real adlı fayla nisbətən prioritet təşkil edir | bəli | panel_az.xlsx yükləndi |
| zədələnmiş fayl: məcburi sütunun olmaması kritik xəta kimi bildirilir | bəli | məcburi sütun yoxdur (EN və ya AZ başlığı) |
| zədələnmiş fayl: ümumi aktivlər < cari aktivlər halı hər sətir üzrə qeyd olunur və icra dayandırılır | bəli | müəssisə paneli rədd edildi: 15 kritik xəta (birincisi: sətir 2, sütun total_assets: ümumi aktivlər < cari aktivlər + əsas fondlar); bax: rep.csv |

Yüklənmiş panel üzrə validator: 0 xəbərdarlıq, 0 ciddi xəta (`FR10_firm_panel_validation_report.csv`).
<!-- /AUTO:layerb -->

### 15.1 Müəssisə səviyyəli ekonometrika (v2) — yüklənmiş panel üzərində işləyir, hazırda SİNTETİK

Eyni kod SİNTETİK və REAL rejimlərdə işləyir (əvəzləmə testi onu REAL adlı surət üzərində yenidən icra edir və eyni
qiymətləri tələb edir). Modellər: (a) rentabellik — ROA və əməliyyat marjası ölçü, borc yükü, likvidlik, yaş, mülkiyyət,
ixrac payı, region, sahə tələbinin artımı və vahid əmək xərci üzrə; iki yönlü sabit effektlərlə (müəssisə + il) və
NACE × il sabit effektləri ilə birləşdirilmiş OLS ilə; (b) within qiymətləndiricisi ilə və sektor və il fiktiv
dəyişənləri ilə birləşdirilmiş OLS ilə Kobb–Duqlas əlavə dəyər istehsal funksiyası, miqyas effekti və klasterə dayanıqlı
CRS testi ilə; (c) indeks üsulu ilə hesablanmış TFP-nin və istehsal funksiyası üzrə TFP-nin amilləri; (d) maliyyə
çətinliyi logit modeli (t ilində Altman Z''-EM çətinlik zonası və ya mənfi kapital, t−1 ilinin izahedici dəyişənləri
üzrə), orta marjinal effektlər, nümunədaxili və son iki il üzrə nümunədən kənar ROC/AUC və kalibrləmə cədvəli ilə;
(e) investisiya normasının amilləri (gecikmiş investisiya norması yoxdur); (f) tam nəticəsi ilə bazar payı modeli;
(g) ixracda iştirak logit modeli. Bütün standart xətalar müəssisələr üzrə klasterə dayanıqlıdır (CR1, t(G−1));
statsmodels nəticələri müstəqil numpy hesablaması ilə tutuşdurulur. **Olley–Pakes, Levinsohn–Petrin və
Ackerberg–Caves–Frazer üsulları istifadə olunmur**: onlar istehsal funksiyasını məhsuldarlıq üçün birinci dərəcəli
Markov (avtoreqressiv) hərəkət qanununu qiymətləndirməklə identifikasiya edir, sifarişçinin məhdudiyyətləri isə bunu
istisna edir.

**Parametrlərin bərpası.** v2-nin sintetik generatoru sərbəst balans və mənfəət-zərər maddələrini məlum parametrləri
olan struktur qat vasitəsilə (ixrac, əlavə dəyərin payı və marja, istehsal funksiyası, investisiya) yenidən yazır və pay
modelinin və A qatının uyğunluq yoxlamalarının istifadə etdiyi bütün v1 çəkilişlərini saxlayır. ROA, indeks üsulu ilə
TFP və çətinlik zonası bu blokların qeyri-xətti mühasibat funksiyalarıdır, buna görə onlar üçün qapalı formada həqiqi
parametr mövcud deyil (cədvəllərdə qeyd olunur). Əhatə əmsalı struktur qatın təkrarlamaları üzrə ölçülür.

**SİNTETİK panelin kalibrlənməsi (v2.2, `DGP_CAL`; səviyyə sabitləri, qiymətləndirilən parametrlər deyil).** Əvvəlki
versiyada zərərlə işləyən müəssisələrin payı (vergidən əvvəlki mənfəət < 0) 29%-dən (2019) 42%-ə (2025) qədər sürüşürdü,
aqreqat xalis marja isə 2025-ci ildə gəlirin 5,4%-i idi (2019–2025 üzrə 4,8–8,0%; vergidən əvvəlki mənfəət çıxılan
xərclərin 6,7–11,5%-i): kapitalın miqyas sabiti yalnız sahə üzrə müəyyən edildiyindən nominal əmək məhsuldarlığının
artımı kapital/gəlir nisbətini və faiz yükünü ildən-ilə mexaniki olaraq artırırdı. Üç dəyişiklik: (1) kapitalın miqyas
sabiti sahə və il üzrə additivdir (kapital/gəlir medianı hər sahə-ildə 0,5); (2) əlavə dəyərin payının sahənin vahid
əmək xərci üzərində əlavə qiyməti (mark-up) 0,18-dir (əvvəl 0,15); (3) əlavə dəyərin payının il üzrə ümumi sabit həddi
$\delta_t$ bisseksiya ilə elə seçilir ki, **hər il müəssisələrin 25%-i zərərlə işləsin**. Hədəfin əsası: DVX bəyannamələri
bəyan edilmiş zərərlərin *məbləğini* (vergi tutulan mənfəətin 14–27%-i) verir, lakin zərərli ödəyicilərin *sayını*
vermir; müəssisə səviyyəli mühasibat məlumatlarında emal sənayesi üzrə zərərli müəssisələrin payı adətən beşdə bir ilə
üçdə bir arasında olur və 25% bu intervalın ortasıdır — bu, kalibrləmə seçimidir, Azərbaycan statistikası deyil. Aqreqat
marja üçün istinad DVX bəyannaməsi üzrə xalis marjadır (çıxılan xərclərin 10,0–13,2%-i, 2021–2025, bütün ödəyicilər).
Nəticə (2019–2025): zərərli müəssisələrin payı hər il 25,0% (əvvəl 28,9–43,3%); vergidən əvvəlki mənfəət çıxılan
xərclərin 9,2–12,7%-i (əvvəl 6,7–11,5%); xalis mənfəət gəlirin 6,6–8,8%-i (əvvəl 4,8–8,0%; 2025: 8,5%, əvvəl 5,4%); Altman
Z''-EM çətinlik zonası müəssisələrin 6,3–8,2%-i (əvvəl 7,5–11,4%), təhlükəsiz zona 79–81% (əvvəl 74–80%). Zərərlər
mənfəətli müəssisələrin mənfəətinin 5–9%-nə bərabərdir, bu da DVX intervalından aşağıdır (bəyannamələr bütün sektorları
əhatə edir və onların zərərləri iri ödəyicilərdə cəmləşir; sintetik panel bunu təqlid etməyə çalışmır). $\delta_t$ və
kapitalın il sabiti hər qiymətləndiricinin il effektləri (müəssisə + il, NACE × il, NACE + il) tərəfindən udulur, buna
görə `DGP_TRUE`-dakı həqiqi parametrlər dəyişmir; ardıcıl qiymətləndiricilər üçün parametrlərin bərpası 4 s.x. daxilində
30/30 olaraq qalır, Monte Karlo əhatəsi isə praktiki olaraq dəyişmir. Gəlirlər əvvəlki kimi DSK-nın sahə buraxılışına
toplanır, müəssisələrin sayı DSK-nın fəaliyyət göstərən müəssisələrinə bərabərdir; hər fayl SİNTETİK su nişanını saxlayır.

<!-- AUTO:econ_models -->
**Məlumat rejimi: SİNTETİK** (FR10_firm_panel_SYNTHETIC.csv, 22 495 sətir, 5 255 müəssisə, 2019–2025) — **SİNTETİK — emal xəttinin sınağı, nəticə deyil** / *sintetik məlumat — texniki nümayiş*.

| model_id | qiymətləndirici | asılı dəyişən | n_obs | n_firms | r2 | r2_type | AUC | auc_oos | RTS | crs_p |
|---|---|---|---|---|---|---|---|---|---|---|
| B_roa_fe | İki yönlü sabit effektlər (müəssisə + il), müəssisə üzrə ortadan çıxarma; klaster (müəssisə) | roa | 21888 | 4648 | 0.258 | daxili R² | — | — | — | — |
| B_roa_pool | Birləşdirilmiş ƏKK + NACE × il sabit effektləri; klaster (müəssisə) | roa | 22495 | 5255 | 0.435 | R² | — | — | — | — |
| B_margin_fe | İki yönlü sabit effektlər (müəssisə + il), müəssisə üzrə ortadan çıxarma; klaster (müəssisə) | op_margin | 21849 | 4644 | 0.410 | daxili R² | — | — | — | — |
| B_margin_pool | Birləşdirilmiş ƏKK + NACE × il sabit effektləri; klaster (müəssisə) | op_margin | 22456 | 5251 | 0.643 | R² | — | — | — | — |
| B_pf_fe | İki yönlü sabit effektlər (müəssisə + il), müəssisə üzrə ortadan çıxarma; klaster (müəssisə) | ln_va | 21888 | 4648 | 0.950 | daxili R² | — | — | 0.945 | 0.000 |
| B_pf_pool | Birləşdirilmiş ƏKK + NACE və il dummy-ləri; klaster (müəssisə) | ln_va | 22495 | 5255 | 0.991 | R² | — | — | 0.955 | 0.000 |
| B_tfp_idx | Birləşdirilmiş ƏKK + NACE × il sabit effektləri; klaster (müəssisə) | tfp_idx | 22495 | 5255 | 0.151 | R² | — | — | — | — |
| B_tfp_idx_fe | İki yönlü sabit effektlər (müəssisə + il), müəssisə üzrə ortadan çıxarma; klaster (müəssisə) | tfp_idx | 21888 | 4648 | 0.033 | daxili R² | — | — | — | — |
| B_tfp_pf | Birləşdirilmiş ƏKK + NACE × il sabit effektləri; klaster (müəssisə) | tfp_pf | 22495 | 5255 | 0.601 | R² | — | — | — | — |
| B_distress | Logit (MHQ), il dummy-ləri; klaster (müəssisə) | maliyyə çətinliyi | 17240 | 4648 | 0.387 | McFadden psevdo-R² | 0.918 | 0.920 | — | — |
| B_invest_fe | İki yönlü sabit effektlər (müəssisə + il), müəssisə üzrə ortadan çıxarma; klaster (müəssisə) | inv_rate | 16279 | 3687 | 0.457 | daxili R² | — | — | — | — |
| B_invest_pool | Birləşdirilmiş ƏKK + NACE × il sabit effektləri; klaster (müəssisə) | inv_rate | 17240 | 4648 | 0.518 | R² | — | — | — | — |
| B_export | Logit (MHQ), NACE və il dummy-ləri; klaster (müəssisə) | ixracatçı | 17240 | 4648 | 0.112 | McFadden psevdo-R² | 0.724 | — | — | — |

Əmsallar (müəssisələr üzrə klasterə dayanıqlı):

| model_id | termin | əmsal | s.x. | p | ci_low | ci_high |
|---|---|---|---|---|---|---|
| B_roa_fe | ln_emp | 0.0152 | 0.0024 | 0.0000 | 0.0105 | 0.0200 |
| B_roa_fe | borc yükü | -0.1807 | 0.0262 | 0.0000 | -0.2322 | -0.1293 |
| B_roa_fe | ln_current_ratio | -0.0150 | 0.0024 | 0.0000 | -0.0197 | -0.0104 |
| B_roa_fe | ln_age | 0.0026 | 0.0015 | 0.0817 | -0.0003 | 0.0054 |
| B_roa_fe | export_share | 0.0296 | 0.0043 | 0.0000 | 0.0211 | 0.0380 |
| B_roa_fe | demand_growth | 0.0885 | 0.0072 | 0.0000 | 0.0743 | 0.1027 |
| B_roa_fe | ulc | -1.1098 | 0.0636 | 0.0000 | -1.2345 | -0.9851 |
| B_roa_pool | ln_emp | 0.0102 | 0.0009 | 0.0000 | 0.0085 | 0.0120 |
| B_roa_pool | borc yükü | -0.1753 | 0.0088 | 0.0000 | -0.1926 | -0.1579 |
| B_roa_pool | ln_current_ratio | -0.0136 | 0.0023 | 0.0000 | -0.0182 | -0.0090 |
| B_roa_pool | ln_age | 0.0034 | 0.0009 | 0.0002 | 0.0016 | 0.0052 |
| B_roa_pool | dövlət | -0.0349 | 0.0038 | 0.0000 | -0.0423 | -0.0275 |
| B_roa_pool | xarici | 0.0218 | 0.0042 | 0.0000 | 0.0136 | 0.0300 |
| B_roa_pool | birgə | 0.0085 | 0.0049 | 0.0811 | -0.0010 | 0.0180 |
| B_roa_pool | export_share | 0.0244 | 0.0048 | 0.0000 | 0.0151 | 0.0338 |
| B_roa_pool | baku | 0.0059 | 0.0021 | 0.0046 | 0.0018 | 0.0100 |
| B_roa_pool | ulc | -1.0098 | 0.0330 | 0.0000 | -1.0745 | -0.9451 |
| B_margin_fe | ln_emp | 0.0094 | 0.0012 | 0.0000 | 0.0070 | 0.0117 |
| B_margin_fe | borc yükü | -0.0614 | 0.0134 | 0.0000 | -0.0877 | -0.0352 |
| B_margin_fe | ln_current_ratio | 0.0120 | 0.0013 | 0.0000 | 0.0094 | 0.0145 |
| B_margin_fe | ln_age | 0.0042 | 0.0009 | 0.0000 | 0.0025 | 0.0059 |
| B_margin_fe | export_share | 0.0513 | 0.0030 | 0.0000 | 0.0455 | 0.0572 |
| B_margin_fe | demand_growth | 0.0778 | 0.0022 | 0.0000 | 0.0736 | 0.0820 |
| B_margin_fe | ulc | -1.0063 | 0.0142 | 0.0000 | -1.0342 | -0.9784 |
| B_margin_pool | ln_emp | 0.0156 | 0.0004 | 0.0000 | 0.0149 | 0.0163 |
| B_margin_pool | borc yükü | -0.0585 | 0.0044 | 0.0000 | -0.0671 | -0.0499 |
| B_margin_pool | ln_current_ratio | 0.0115 | 0.0012 | 0.0000 | 0.0091 | 0.0138 |
| B_margin_pool | ln_age | 0.0064 | 0.0005 | 0.0000 | 0.0055 | 0.0074 |
| B_margin_pool | dövlət | -0.0283 | 0.0017 | 0.0000 | -0.0317 | -0.0249 |
| B_margin_pool | xarici | 0.0238 | 0.0021 | 0.0000 | 0.0197 | 0.0278 |
| B_margin_pool | birgə | 0.0053 | 0.0027 | 0.0528 | -0.0001 | 0.0107 |
| B_margin_pool | export_share | 0.0545 | 0.0029 | 0.0000 | 0.0488 | 0.0602 |
| B_margin_pool | baku | 0.0087 | 0.0011 | 0.0000 | 0.0065 | 0.0108 |
| B_margin_pool | ulc | -0.9946 | 0.0085 | 0.0000 | -1.0112 | -0.9779 |
| B_pf_fe | ln_L | 0.4468 | 0.0025 | 0.0000 | 0.4419 | 0.4517 |
| B_pf_fe | ln_K | 0.4984 | 0.0014 | 0.0000 | 0.4958 | 0.5011 |
| B_pf_pool | ln_L | 0.4956 | 0.0027 | 0.0000 | 0.4903 | 0.5009 |
| B_pf_pool | ln_K | 0.4599 | 0.0021 | 0.0000 | 0.4558 | 0.4640 |
| B_tfp_idx | ln_emp | -0.0210 | 0.0009 | 0.0000 | -0.0229 | -0.0192 |
| B_tfp_idx | ln_age | -0.0034 | 0.0009 | 0.0002 | -0.0051 | -0.0016 |
| B_tfp_idx | dövlət | -0.0175 | 0.0035 | 0.0000 | -0.0244 | -0.0107 |
| B_tfp_idx | xarici | 0.0260 | 0.0054 | 0.0000 | 0.0154 | 0.0365 |
| B_tfp_idx | birgə | 0.0089 | 0.0067 | 0.1843 | -0.0042 | 0.0220 |
| B_tfp_idx | ixracatçı | -0.0055 | 0.0015 | 0.0002 | -0.0085 | -0.0026 |
| B_tfp_idx | borc yükü | 0.0196 | 0.0063 | 0.0019 | 0.0072 | 0.0319 |
| B_tfp_idx | baku | -0.0014 | 0.0024 | 0.5692 | -0.0062 | 0.0034 |
| B_tfp_idx_fe | ln_emp | -0.0201 | 0.0015 | 0.0000 | -0.0230 | -0.0172 |
| B_tfp_idx_fe | ln_age | -0.0014 | 0.0008 | 0.0883 | -0.0030 | 0.0002 |
| B_tfp_idx_fe | ixracatçı | -0.0036 | 0.0009 | 0.0001 | -0.0054 | -0.0018 |
| B_tfp_idx_fe | borc yükü | 0.0288 | 0.0143 | 0.0437 | 0.0008 | 0.0569 |
| B_tfp_pf | dövlət | -0.0756 | 0.0082 | 0.0000 | -0.0917 | -0.0595 |
| B_tfp_pf | xarici | 0.0983 | 0.0089 | 0.0000 | 0.0809 | 0.1157 |
| B_tfp_pf | birgə | 0.0350 | 0.0140 | 0.0127 | 0.0075 | 0.0625 |
| B_distress | leverage_l1 | 10.0756 | 0.3592 | 0.0000 | 9.3716 | 10.7796 |
| B_distress | ln_current_ratio_l1 | 0.0172 | 0.1188 | 0.8849 | -0.2156 | 0.2500 |
| B_distress | roa_w_l1 | -7.7893 | 0.4027 | 0.0000 | -8.5785 | -7.0000 |
| B_distress | ln_emp_l1 | -0.0677 | 0.0254 | 0.0077 | -0.1175 | -0.0179 |
| B_distress | export_share_l1 | 0.3731 | 0.2626 | 0.1554 | -0.1417 | 0.8878 |
| B_distress | ln_age | -0.1709 | 0.0468 | 0.0003 | -0.2627 | -0.0791 |
| B_distress | dövlət | 0.2897 | 0.1183 | 0.0143 | 0.0578 | 0.5217 |
| B_distress | xarici | -0.0374 | 0.1535 | 0.8075 | -0.3383 | 0.2635 |
| B_distress | demand_growth | -2.5513 | 0.1566 | 0.0000 | -2.8583 | -2.2443 |
| B_invest_fe | sales_growth | 0.0810 | 0.0010 | 0.0000 | 0.0791 | 0.0830 |
| B_invest_fe | leverage_l1 | -0.0578 | 0.0103 | 0.0000 | -0.0780 | -0.0376 |
| B_invest_fe | roa_w_l1 | 0.2080 | 0.0044 | 0.0000 | 0.1992 | 0.2167 |
| B_invest_fe | ln_emp_l1 | -0.0045 | 0.0010 | 0.0000 | -0.0064 | -0.0026 |
| B_invest_pool | sales_growth | 0.0820 | 0.0013 | 0.0000 | 0.0795 | 0.0845 |
| B_invest_pool | leverage_l1 | -0.0523 | 0.0024 | 0.0000 | -0.0570 | -0.0475 |
| B_invest_pool | roa_w_l1 | 0.2102 | 0.0040 | 0.0000 | 0.2024 | 0.2180 |
| B_invest_pool | ln_emp_l1 | -0.0040 | 0.0003 | 0.0000 | -0.0045 | -0.0034 |
| B_invest_pool | dövlət | -0.0207 | 0.0014 | 0.0000 | -0.0233 | -0.0180 |
| B_invest_pool | xarici | -0.0004 | 0.0016 | 0.8184 | -0.0034 | 0.0027 |
| B_invest_pool | birgə | -0.0001 | 0.0019 | 0.9670 | -0.0038 | 0.0037 |
| B_export | ln_emp_l1 | 0.4057 | 0.0138 | 0.0000 | 0.3787 | 0.4327 |
| B_export | xarici | 1.0329 | 0.0624 | 0.0000 | 0.9107 | 1.1551 |
| B_export | dövlət | -0.6258 | 0.0642 | 0.0000 | -0.7517 | -0.4999 |
| B_export | birgə | 0.3588 | 0.1114 | 0.0013 | 0.1404 | 0.5772 |
| B_export | ln_age | 0.1913 | 0.0247 | 0.0000 | 0.1429 | 0.2397 |
| B_export | baku | 0.2878 | 0.0385 | 0.0000 | 0.2123 | 0.3633 |
| B_share | rel_lp_l1 | 0.1520 | 0.0046 | 0.0000 | 0.1431 | 0.1610 |
| B_share | rel_leverage_l1 | -0.2963 | 0.0104 | 0.0000 | -0.3167 | -0.2759 |

Şərh (Azərbaycan dilində):

- **B_roa_fe**: [sintetik məlumat — texniki nümayiş] 4 648 müəssisə, 21 888 müşahidə (2019–2025). Daxili R² = 0,258. Əsas amillər: vahid əmək xərci (əmək haqqı fondu / gəlir) −1,110 (azaldır, p < 0,001); sahə tələbinin artımı (Δln DSK buraxılışı) 0,089 (artırır, p < 0,001); borc yükü (öhdəliklər / aktivlər) −0,181 (azaldır, p < 0,001); ixracın gəlirdə payı 0,030 (artırır, p < 0,001). Zamanla dəyişməyən amillər (mülkiyyət, region) müəssisə effektlərinə daxildir; onlar birləşdirilmiş modeldə qiymətləndirilir.
- **B_roa_pool**: [sintetik məlumat — texniki nümayiş] 5 255 müəssisə, 22 495 müşahidə (2019–2025). R² = 0,435. Əsas amillər: vahid əmək xərci (əmək haqqı fondu / gəlir) −1,010 (azaldır, p < 0,001); borc yükü (öhdəliklər / aktivlər) −0,175 (azaldır, p < 0,001); ln işçilərin sayı (ölçü) 0,010 (artırır, p < 0,001); dövlət mülkiyyəti −0,035 (azaldır, p < 0,001). Sahə tələbinin artımı NACE × il effektlərinə daxildir; o, iki yönlü FE modelində qiymətləndirilir.
- **B_margin_fe**: [sintetik məlumat — texniki nümayiş] 4 644 müəssisə, 21 849 müşahidə (2019–2025). Daxili R² = 0,410. Əsas amillər: vahid əmək xərci (əmək haqqı fondu / gəlir) −1,006 (azaldır, p < 0,001); sahə tələbinin artımı (Δln DSK buraxılışı) 0,078 (artırır, p < 0,001); ixracın gəlirdə payı 0,051 (artırır, p < 0,001); ln cari likvidlik əmsalı 0,012 (artırır, p < 0,001). Zamanla dəyişməyən amillər (mülkiyyət, region) müəssisə effektlərinə daxildir; onlar birləşdirilmiş modeldə qiymətləndirilir.
- **B_margin_pool**: [sintetik məlumat — texniki nümayiş] 5 251 müəssisə, 22 456 müşahidə (2019–2025). R² = 0,643. Əsas amillər: vahid əmək xərci (əmək haqqı fondu / gəlir) −0,995 (azaldır, p < 0,001); ln işçilərin sayı (ölçü) 0,016 (artırır, p < 0,001); ixracın gəlirdə payı 0,054 (artırır, p < 0,001); dövlət mülkiyyəti −0,028 (azaldır, p < 0,001). Sahə tələbinin artımı NACE × il effektlərinə daxildir; o, iki yönlü FE modelində qiymətləndirilir.
- **B_pf_fe**: [sintetik məlumat — texniki nümayiş] 4 648 müəssisə, 21 888 müşahidə (2019–2025). Daxili R² = 0,950. Əmək elastikliyi 0,447, kapital elastikliyi 0,498; miqyasdan gəlir 0,945 [0,941; 0,949]; sabit gəlir (CRS) hipotezi p = 0,0000 ilə rədd edilir. Olley–Pakes / Levinsohn–Petrin / ACF tətbiq edilmir: onlar məhsuldarlıq üçün avtoreqressiv (Markov) hərəkət qanunu qiymətləndirir, bu isə sifarişçinin məhdudiyyətinə ziddir.
- **B_pf_pool**: [sintetik məlumat — texniki nümayiş] 5 255 müəssisə, 22 495 müşahidə (2019–2025). R² = 0,991. Əmək elastikliyi 0,496, kapital elastikliyi 0,460; miqyasdan gəlir 0,955 [0,953; 0,958]; sabit gəlir (CRS) hipotezi p = 0,0000 ilə rədd edilir. Olley–Pakes / Levinsohn–Petrin / ACF tətbiq edilmir: onlar məhsuldarlıq üçün avtoreqressiv (Markov) hərəkət qanunu qiymətləndirir, bu isə sifarişçinin məhdudiyyətinə ziddir. Birləşdirilmiş OLS müəssisənin daimi məhsuldarlığını nəzərə almır; FE qiymətləndiricisi ilə fərq bu sürüşməni göstərir.
- **B_tfp_idx**: [sintetik məlumat — texniki nümayiş] 5 255 müəssisə, 22 495 müşahidə (2019–2025). R² = 0,151. TFP ilə əlaqəli amillər: ln işçilərin sayı (ölçü) −0,021 (azaldır, p < 0,001); dövlət mülkiyyəti −0,018 (azaldır, p < 0,001); xarici mülkiyyət 0,026 (artırır, p < 0,001); ln(1 + yaş) −0,003 (azaldır, p < 0,001).
- **B_tfp_idx_fe**: [sintetik məlumat — texniki nümayiş] 4 648 müəssisə, 21 888 müşahidə (2019–2025). Daxili R² = 0,033. TFP ilə əlaqəli amillər: ln işçilərin sayı (ölçü) −0,020 (azaldır, p < 0,001); ixracatçı (0/1) −0,004 (azaldır, p < 0,001); borc yükü (öhdəliklər / aktivlər) 0,029 (artırır, p = 0,044).
- **B_tfp_pf**: [sintetik məlumat — texniki nümayiş] 5 255 müəssisə, 22 495 müşahidə (2019–2025). R² = 0,601. TFP ilə əlaqəli amillər: xarici mülkiyyət 0,098 (artırır, p < 0,001); dövlət mülkiyyəti −0,076 (azaldır, p < 0,001); birgə mülkiyyət 0,035 (artırır, p = 0,013).
- **B_distress**: [sintetik məlumat — texniki nümayiş] 4 648 müəssisə, 17 240 müşahidə (2020–2025). Çətinlik tezliyi 7,1%. AUC nümunədə 0,918, son iki ildə (nümunədən kənar, 2020-2023 üzrə qiymətləndirilmiş) 0,920; Brier 0,0460; Hosmer–Lemeshow p = 0,152. Ən böyük orta marjinal effektlər: borc yükü, t−1 0,4550; ROA, t−1 (±0,3 hüdudunda) −0,3518; sahə tələbinin artımı (Δln DSK buraxılışı) −0,1152. Gecikmiş çətinlik statusu modelə daxil edilmir.
- **B_invest_fe**: [sintetik məlumat — texniki nümayiş] 3 687 müəssisə, 16 279 müşahidə (2020–2025). Daxili R² = 0,457. İnvestisiya normasının amilləri: satışların artımı (Δln gəlir) 0,081 (artırır, p < 0,001); ROA, t−1 (±0,3 hüdudunda) 0,208 (artırır, p < 0,001); borc yükü, t−1 −0,058 (azaldır, p < 0,001); ln işçilərin sayı, t−1 −0,004 (azaldır, p < 0,001). Gecikmiş investisiya norması modeldə yoxdur.
- **B_invest_pool**: [sintetik məlumat — texniki nümayiş] 4 648 müəssisə, 17 240 müşahidə (2020–2025). R² = 0,518. İnvestisiya normasının amilləri: satışların artımı (Δln gəlir) 0,082 (artırır, p < 0,001); ROA, t−1 (±0,3 hüdudunda) 0,210 (artırır, p < 0,001); borc yükü, t−1 −0,052 (azaldır, p < 0,001); dövlət mülkiyyəti −0,021 (azaldır, p < 0,001). Gecikmiş investisiya norması modeldə yoxdur.
- **B_export**: [sintetik məlumat — texniki nümayiş] 4 648 müəssisə, 17 240 müşahidə (2020–2025). İxracatçıların payı 25,3%; AUC 0,724. Ən böyük orta marjinal effektlər: xarici mülkiyyət 0,1703; dövlət mülkiyyəti −0,1031; ln işçilərin sayı, t−1 0,0669.
- **B_share**: [sintetik məlumat — texniki nümayiş] Bazar payının illik dəyişməsi əvvəlki ilin nisbi əmək məhsuldarlığı ilə 0,152 (s.x. 0,005), nisbi borc yükü ilə −0,296 (s.x. 0,010) əlaqəlidir; 17 240 müşahidə. Gecikmiş pay modeldə yoxdur; proqnozda paylar sahə daxilində normallaşdırılır.
- **recovery**: [sintetik məlumat — texniki nümayiş] Generatorun məlum parametrləri ilə müqayisə: 35/43 həqiqi parametr 95% etibarlılıq intervalına düşür; ardıcıl (FE, logit, pay modeli) qiymətləndiricilərdə 26/30. Birləşdirilmiş OLS-in istehsal funksiyasında və marjanın ölçü əmsalında sürüşmə gözləniləndir (daimi müəssisə effekti izahedici dəyişənlərlə korrelyasiyalıdır). ROA, indeks TFP və çətinlik modeli üçün generatorda qapalı həqiqi parametr yoxdur.
- **recovery_mc**: [sintetik məlumat — texniki nümayiş] 40 təkrarlamada (struktur qat yenidən çəkilir) ardıcıl qiymətləndiricilərin 23 parametri üzrə 95% etibarlılıq intervalının orta əhatəsi 94,7% (minimum 88%); sürüşmə testinin maksimum |t| = 3,8. Birləşdirilmiş OLS-də maksimum |t| = 131: daimi müəssisə effektləri nəzərə alınmadıqda əmsallar sürüşür.
<!-- /AUTO:econ_models -->

<!-- AUTO:econ_recovery -->
| model_id | termin | həqiqi | qiymət | s.x. | ci_low | ci_high | əhatə olunur |
|---|---|---|---|---|---|---|---|
| B_margin_fe | ln_emp | 0.0100 | 0.0094 | 0.0012 | 0.0070 | 0.0117 | bəli |
| B_margin_fe | borc yükü | -0.0600 | -0.0614 | 0.0134 | -0.0877 | -0.0352 | bəli |
| B_margin_fe | ln_current_ratio | 0.0120 | 0.0120 | 0.0013 | 0.0094 | 0.0145 | bəli |
| B_margin_fe | ln_age | 0.0060 | 0.0042 | 0.0009 | 0.0025 | 0.0059 | xeyr |
| B_margin_fe | export_share | 0.0500 | 0.0513 | 0.0030 | 0.0455 | 0.0572 | bəli |
| B_margin_fe | demand_growth | 0.0800 | 0.0778 | 0.0022 | 0.0736 | 0.0820 | bəli |
| B_margin_fe | ulc | -1.0000 | -1.0063 | 0.0142 | -1.0342 | -0.9784 | bəli |
| B_margin_pool | ln_emp | 0.0100 | 0.0156 | 0.0004 | 0.0149 | 0.0163 | xeyr |
| B_margin_pool | borc yükü | -0.0600 | -0.0585 | 0.0044 | -0.0671 | -0.0499 | bəli |
| B_margin_pool | ln_current_ratio | 0.0120 | 0.0115 | 0.0012 | 0.0091 | 0.0138 | bəli |
| B_margin_pool | ln_age | 0.0060 | 0.0064 | 0.0005 | 0.0055 | 0.0074 | bəli |
| B_margin_pool | dövlət | -0.0300 | -0.0283 | 0.0017 | -0.0317 | -0.0249 | bəli |
| B_margin_pool | xarici | 0.0250 | 0.0238 | 0.0021 | 0.0197 | 0.0278 | bəli |
| B_margin_pool | birgə | 0.0100 | 0.0053 | 0.0027 | -0.0001 | 0.0107 | bəli |
| B_margin_pool | export_share | 0.0500 | 0.0545 | 0.0029 | 0.0488 | 0.0602 | bəli |
| B_margin_pool | baku | 0.0100 | 0.0087 | 0.0011 | 0.0065 | 0.0108 | bəli |
| B_margin_pool | ulc | -1.0000 | -0.9946 | 0.0085 | -1.0112 | -0.9779 | bəli |
| B_pf_fe | ln_L | 0.4500 | 0.4468 | 0.0025 | 0.4419 | 0.4517 | bəli |
| B_pf_fe | ln_K | 0.5000 | 0.4984 | 0.0014 | 0.4958 | 0.5011 | bəli |
| B_pf_fe | RTS | 0.9500 | 0.9452 | 0.0021 | 0.9410 | 0.9494 | xeyr |
| B_pf_pool | ln_L | 0.4500 | 0.4956 | 0.0027 | 0.4903 | 0.5009 | xeyr |
| B_pf_pool | ln_K | 0.5000 | 0.4599 | 0.0021 | 0.4558 | 0.4640 | xeyr |
| B_pf_pool | RTS | 0.9500 | 0.9555 | 0.0015 | 0.9526 | 0.9584 | xeyr |
| B_tfp_pf | dövlət | -0.0800 | -0.0756 | 0.0082 | -0.0917 | -0.0595 | bəli |
| B_tfp_pf | xarici | 0.1000 | 0.0983 | 0.0089 | 0.0809 | 0.1157 | bəli |
| B_tfp_pf | birgə | 0.0500 | 0.0350 | 0.0140 | 0.0075 | 0.0625 | bəli |
| B_invest_fe | sales_growth | 0.0800 | 0.0810 | 0.0010 | 0.0791 | 0.0830 | bəli |
| B_invest_fe | leverage_l1 | -0.0600 | -0.0578 | 0.0103 | -0.0780 | -0.0376 | bəli |
| B_invest_fe | roa_w_l1 | 0.2000 | 0.2080 | 0.0044 | 0.1992 | 0.2167 | bəli |
| B_invest_fe | ln_emp_l1 | -0.0040 | -0.0045 | 0.0010 | -0.0064 | -0.0026 | bəli |
| B_invest_pool | sales_growth | 0.0800 | 0.0820 | 0.0013 | 0.0795 | 0.0845 | bəli |
| B_invest_pool | leverage_l1 | -0.0600 | -0.0523 | 0.0024 | -0.0570 | -0.0475 | xeyr |
| B_invest_pool | roa_w_l1 | 0.2000 | 0.2102 | 0.0040 | 0.2024 | 0.2180 | xeyr |
| B_invest_pool | ln_emp_l1 | -0.0040 | -0.0040 | 0.0003 | -0.0045 | -0.0034 | bəli |
| B_invest_pool | dövlət | -0.0200 | -0.0207 | 0.0014 | -0.0233 | -0.0180 | bəli |
| B_export | ln_emp_l1 | 0.4000 | 0.4057 | 0.0138 | 0.3787 | 0.4327 | bəli |
| B_export | xarici | 1.0000 | 1.0329 | 0.0624 | 0.9107 | 1.1551 | bəli |
| B_export | dövlət | -0.6000 | -0.6258 | 0.0642 | -0.7517 | -0.4999 | bəli |
| B_export | birgə | 0.4000 | 0.3588 | 0.1114 | 0.1404 | 0.5772 | bəli |
| B_export | ln_age | 0.2000 | 0.1913 | 0.0247 | 0.1429 | 0.2397 | bəli |
| B_export | baku | 0.3000 | 0.2878 | 0.0385 | 0.2123 | 0.3633 | bəli |
| B_share | rel_lp_l1 | 0.1500 | 0.1520 | 0.0046 | 0.1431 | 0.1610 | bəli |
| B_share | rel_leverage_l1 | -0.3000 | -0.2963 | 0.0104 | -0.3167 | -0.2759 | bəli |

Struktur qatın 40 təkrarlaması üzrə (`FR10_SYNTHETIC_econ_recovery_mc.csv`): ardıcıl qiymətləndiricilərdə orta 95% əhatə əmsalı 94,7% (minimum 88%), ən böyük |bias t| 3,77; birləşdirilmiş OLS (istehsal funksiyası, marjanın ölçü effekti) üzrə ən böyük |bias t| 131 — within qiymətləndiricisinin aradan qaldırdığı sürüşmə.

| model_id | termin | həqiqi | mean_estimate | mc_sd | mean_se | coverage_95 | bias_t |
|---|---|---|---|---|---|---|---|
| B_pf_fe | ln_L | 0.4500 | 0.4500 | 0.0027 | 0.0025 | 0.9000 | 0.1063 |
| B_pf_fe | ln_K | 0.5000 | 0.5002 | 0.0011 | 0.0014 | 1.0000 | 1.0525 |
| B_pf_fe | RTS | 0.9500 | 0.9502 | 0.0025 | 0.0021 | 0.9500 | 0.5976 |
| B_pf_pool | ln_L | 0.4500 | 0.4953 | 0.0027 | 0.0027 | 0.0000 | 106.3899 |
| B_pf_pool | ln_K | 0.5000 | 0.4592 | 0.0020 | 0.0020 | 0.0000 | -130.5119 |
| B_pf_pool | RTS | 0.9500 | 0.9544 | 0.0012 | 0.0015 | 0.1000 | 23.6317 |
| B_margin_fe | ln_emp | 0.0100 | 0.0099 | 0.0012 | 0.0012 | 0.9750 | -0.4439 |
| B_margin_fe | borc yükü | -0.0600 | -0.0616 | 0.0127 | 0.0134 | 0.9750 | -0.7993 |
| B_margin_fe | ln_current_ratio | 0.0120 | 0.0118 | 0.0013 | 0.0013 | 0.9500 | -0.7807 |
| B_margin_fe | ln_age | 0.0060 | 0.0060 | 0.0009 | 0.0009 | 0.9500 | 0.3225 |
| B_margin_fe | export_share | 0.0500 | 0.0504 | 0.0029 | 0.0030 | 0.9750 | 0.9139 |
| B_margin_fe | demand_growth | 0.0800 | 0.0801 | 0.0022 | 0.0021 | 0.9500 | 0.2799 |
| B_margin_fe | ulc | -1.0000 | -0.9979 | 0.0175 | 0.0142 | 0.8750 | 0.7490 |
| B_margin_pool | ln_emp | 0.0100 | 0.0156 | 0.0004 | 0.0004 | 0.0000 | 94.7993 |
| B_margin_pool | borc yükü | -0.0600 | -0.0561 | 0.0041 | 0.0044 | 0.8750 | 5.9568 |
| B_margin_pool | ln_current_ratio | 0.0120 | 0.0121 | 0.0011 | 0.0012 | 0.9500 | 0.6802 |
| B_margin_pool | ln_age | 0.0060 | 0.0066 | 0.0004 | 0.0005 | 0.8500 | 10.6394 |
| B_margin_pool | dövlət | -0.0300 | -0.0299 | 0.0018 | 0.0017 | 0.9250 | 0.4389 |
| B_margin_pool | xarici | 0.0250 | 0.0245 | 0.0019 | 0.0020 | 0.9500 | -1.7820 |
| B_margin_pool | birgə | 0.0100 | 0.0101 | 0.0029 | 0.0028 | 0.9250 | 0.1139 |
| B_margin_pool | export_share | 0.0500 | 0.0509 | 0.0026 | 0.0029 | 0.9750 | 2.2057 |
| B_margin_pool | baku | 0.0100 | 0.0099 | 0.0009 | 0.0011 | 1.0000 | -0.9627 |
| B_margin_pool | ulc | -1.0000 | -0.9904 | 0.0083 | 0.0085 | 0.7750 | 7.3042 |
| B_invest_fe | sales_growth | 0.0800 | 0.0800 | 0.0009 | 0.0010 | 0.9750 | 0.0194 |
| B_invest_fe | leverage_l1 | -0.0600 | -0.0537 | 0.0105 | 0.0103 | 0.9250 | 3.7716 |
| B_invest_fe | roa_w_l1 | 0.2000 | 0.1999 | 0.0038 | 0.0045 | 0.9750 | -0.1291 |
| B_invest_fe | ln_emp_l1 | -0.0040 | -0.0040 | 0.0010 | 0.0010 | 0.9250 | -0.1100 |
| B_tfp_pf | dövlət | -0.0800 | -0.0787 | 0.0078 | 0.0077 | 0.9000 | 1.0428 |
| B_tfp_pf | xarici | 0.1000 | 0.0975 | 0.0087 | 0.0088 | 0.9250 | -1.8122 |
| B_tfp_pf | birgə | 0.0500 | 0.0505 | 0.0113 | 0.0128 | 1.0000 | 0.2770 |
| B_export | ln_emp_l1 | 0.4000 | 0.4000 | 0.0162 | 0.0134 | 0.9000 | -0.0087 |
| B_export | xarici | 1.0000 | 0.9834 | 0.0446 | 0.0618 | 1.0000 | -2.3469 |
| B_export | dövlət | -0.6000 | -0.6159 | 0.0700 | 0.0671 | 0.9500 | -1.4362 |
| B_export | birgə | 0.4000 | 0.3957 | 0.0908 | 0.0920 | 0.9250 | -0.2991 |
| B_export | ln_age | 0.2000 | 0.1961 | 0.0230 | 0.0241 | 0.9250 | -1.0839 |
| B_export | baku | 0.3000 | 0.3013 | 0.0333 | 0.0382 | 0.9500 | 0.2411 |
<!-- /AUTO:econ_recovery -->

## 16. Arifmetik yoxlamalar

<!-- AUTO:checks -->
Arifmetik yoxlamalardan keçənlər: 32 / 32 (`FR10_identity_checks.csv`); hər biri quruluşca ödənilir.
<!-- /AUTO:checks -->

## 17. Məhdudiyyətlər

1. Əlaqəli sektor elastikliyi nümunədaxili əhəmiyyətlidir, lakin onun bölüşdürmədə sabit paylarla müqayisədə nümunədən
   kənar üstünlüyü müəyyən edilməyib; Əsas ssenari kombinasiyası əvvəlcədən müəyyən edilmiş qaydaya əsaslanır (§11.3).
2. Sahələrin real buraxılışı implisit deflyatorlara və bir neçə kiçik sahədə nominal buraxılışla uyğun gəlməyən DSK həcm
   indekslərinə əsaslanır (F15; yoxlamadan keçməyən indekslər v2.1 qaydası ilə əvəz olunur və doldurulmuş kimi
   işarələnir); onun nümunədən kənar yoxlama nəticəsi §12-dədir. Nominal buraxılış daha etibarlı nəticə olaraq qalır.
3. Neft emalının güc qaydası yeni güclərin olmadığını fərz edir; rıçaq 2015–25-ci illərin maksimumunu göstərir.
4. B qatının məlumatları daxil olana qədər maliyyə vəziyyəti aqreqat səviyyədədir; marja əməyin payı qaydasından asılıdır,
   sahə üzrə GOS proksi göstəricisi isə yuxarı həddir (qeyri-formal buraxılış, nəzərə alınmayan vergilər).
5. Səmərəlilik göstəriciləri implisit deflyatorlara və fasiləsiz inventar üsulu ilə hesablanmış kapitala əsaslanır;
   kiçik sahələrdə TFP səs-küylüdür.
6. Amillər panelinin gücü onun 15 (8) ili ilə məhduddur.
7. İxrac, sahə üzrə istehsalçı qiymətləri indeksləri (PPI), enerji xərcləri, sahə üzrə kreditlər və yenilənmə
   əmsalları mövcud deyil (§6).
8. SİNTETİK rejimdə B qatının ekonometrikası (§15.1) metodu nümayiş etdirir və generatorun məlum parametrlərini bərpa
   edir; bunlar Azərbaycan müəssisələri haqqında tapıntılar deyil. Nazirlik öz məlumatlarını yüklədikdə təhlilə çevrilir.

## 18. Nəticə faylları

`FR10.ipynb` — əvvəldən sona 0 xəta ilə icra olunub; onun sonuncu kod xanası bu sənədin rəqəmsal bloklarını yenidən
yaradır. Notebook öz fayllarını öz qovluğuna nisbətən tapır.

<!-- AUTO:outputs -->
`FR10_SYNTHETIC_cohort_survival.csv`, `FR10_SYNTHETIC_concentration_nace.csv`, `FR10_SYNTHETIC_concentration_nace_region_2025.csv`, `FR10_SYNTHETIC_coverage_vs_layer_a.csv`, `FR10_SYNTHETIC_econ_coefficients.csv`, `FR10_SYNTHETIC_econ_distress_ame.csv`, `FR10_SYNTHETIC_econ_distress_calibration.csv`, `FR10_SYNTHETIC_econ_distress_roc.csv`, `FR10_SYNTHETIC_econ_export_ame.csv`, `FR10_SYNTHETIC_econ_export_calibration.csv`, `FR10_SYNTHETIC_econ_export_roc.csv`, `FR10_SYNTHETIC_econ_interpretation_az.csv`, `FR10_SYNTHETIC_econ_models.csv`, `FR10_SYNTHETIC_econ_production_function.csv`, `FR10_SYNTHETIC_econ_recovery.csv`, `FR10_SYNTHETIC_econ_recovery_mc.csv`, `FR10_SYNTHETIC_econ_sample_rules.csv`, `FR10_SYNTHETIC_econ_true_parameters.csv`, `FR10_SYNTHETIC_entry_exit.csv`, `FR10_SYNTHETIC_firm_forecast.csv`, `FR10_SYNTHETIC_firm_ratios_2025.csv`, `FR10_SYNTHETIC_pipeline_tests.csv`, `FR10_SYNTHETIC_share_model.csv`, `FR10_SYNTHETIC_validation_seeded_corruptions.csv`, `FR10_branch_deflator_check.csv`, `FR10_branch_growth_table.csv`, `FR10_branch_history.csv`, `FR10_branch_scorecard.csv`, `FR10_branch_shares_history.csv`, `FR10_coef_sensitivity.csv`, `FR10_concentration.csv`, `FR10_cross_sector_multipliers.csv`, `FR10_data_gaps_and_alternatives.csv`, `FR10_data_integrity_findings.csv`, `FR10_data_source_matrix.csv`, `FR10_determinants_division_bias.csv`, `FR10_determinants_panel.csv`, `FR10_dsk_manifest.csv`, `FR10_dvx_declarations.csv`, `FR10_early_warning.csv`, `FR10_efficiency_branches.csv`, `FR10_fan_charts.csv`, `FR10_fan_meta.csv`, `FR10_financial_sections.csv`, `FR10_firm_panel_swap_tests.csv`, `FR10_firm_panel_swap_tests_econ.csv`, `FR10_firm_panel_validation_report.csv`, `FR10_forecast_assumptions.csv`, `FR10_forecast_branches.csv`, `FR10_forecast_regions.csv`, `FR10_forecast_sections.csv`, `FR10_forecast_tidy.csv`, `FR10_growth_contributions.csv`, `FR10_holdout_branches.csv`, `FR10_holdout_validation.csv`, `FR10_identity_checks.csv`, `FR10_indicator_catalog.csv`, `FR10_input_schema.csv`, `FR10_mining_reconciliation.csv`, `FR10_mining_rules_selection.csv`, `FR10_noar_constructs.csv`, `FR10_nonoil_allocation_selection.csv`, `FR10_nonoil_growth_vs_history.csv`, `FR10_nonstate_composition.csv`, `FR10_nonstate_composition_summary.csv`, `FR10_not_forecast.csv`, `FR10_oil_linked_block.csv`, `FR10_ownership.csv`, `FR10_plausibility.csv`, `FR10_pooled_related_sector_model.csv`, `FR10_presentation_spec.csv`, `FR10_product_forecasts_derived.csv`, `FR10_product_location_shares.csv`, `FR10_products.csv`, `FR10_quadrant.csv`, `FR10_regional_entry_exit.csv`, `FR10_regional_history.csv`, `FR10_rejected_specifications.csv`, `FR10_robustness_summary.csv`, `FR10_scenario_summary.csv`, `FR10_sensitivity_levers.csv`, `FR10_share_system_coefficients.csv`, `FR10_share_system_selection.csv`, `FR10_strings_az.csv`, `FR10_tfp_branches.csv`, `FR10_tfp_sections.csv`, `FR10_volume_index_validation.csv`, `FR10_wage_productivity_gap.csv`
<!-- /AUTO:outputs -->

## 19. v2: tənliklər reyestri, ssenari mühərriki, dayanıqlıq, Azərbaycan dilində sətirlər

**Reyestr** (`output/FR10_equations.json`, `microlib.registry` ilə qurulur; reyestr hər OLS, DOLS və panel tənliyini
statsmodels ilə yenidən qiymətləndirir və əmsalların notebook-dakı əmsallara bərabər olduğunu yoxlayır). Qeydə alınanlar:
faktiki istifadə olunan regional pay sistemi (hər region üzrə səviyyə və fərq formaları və büzülmüş sistem), 2019 kəsimində
qiymətləndirilmiş emal sənayesi və mədənçıxarma pay sistemi namizədləri (rədd edilmiş: sabit paylar seçilib), əlaqəli
sektorlar üzrə birləşdirilmiş model və onun səviyyə variantı, neftə bağlı qiymət elastiklikləri, mədənçıxarma
qaydaları, amillər paneli (iki yönlü FE, DK, wild bootstrap p-dəyərləri, bölmə meyli variantları, between və birgə
hərəkət reqressiyaları) və B qatının bütün modelləri.

<!-- AUTO:v2_registry -->
133 tənlik (A qatı 119, B qatı 14 — SİNTETİK, `synthetic: true`); A qatının 18 tənliyi proqnoza daxil olur. Reyestr və notebook: 111 əmsal yoxlaması, maksimal mütləq fərq 0,0·10⁰.

| qat | alt tapşırıq | tənliklər | proqnozda istifadə olunur | stabil | qismən stabil | qeyri-stabil |
|---|---|---|---|---|---|---|
| A | A1. Bazar payları: emal sənayesi sahələri | 71 | 1 | 20 | 27 | 24 |
| A | A2. Bazar payları: mədənçıxarma sahələri | 12 | 2 | 0 | 3 | 9 |
| A | A3. Regional bölgü: iqtisadi rayonların sənaye payları | 27 | 14 | 13 | 12 | 2 |
| A | A4. Neftlə bağlı sahələr (neft emalı, kimya) | 2 | 1 | 1 | 1 | 0 |
| A | A5. İnkişaf və tənəzzülün amilləri (determinantlar paneli) | 7 | 0 | 0 | 3 | 4 |
| B | B. Müəssisə səviyyəsi: SİNTETİK məlumat — texniki nümayiş — (a) Rentabellik amilləri | 4 | 0 | 4 | 0 | 0 |
| B | B. Müəssisə səviyyəsi: SİNTETİK məlumat — texniki nümayiş — (b) İstehsal funksiyası | 2 | 0 | 2 | 0 | 0 |
| B | B. Müəssisə səviyyəsi: SİNTETİK məlumat — texniki nümayiş — (c) TFP amilləri | 3 | 0 | 3 | 0 | 0 |
| B | B. Müəssisə səviyyəsi: SİNTETİK məlumat — texniki nümayiş — (d) Maliyyə çətinliyi modeli | 1 | 0 | 0 | 1 | 0 |
| B | B. Müəssisə səviyyəsi: SİNTETİK məlumat — texniki nümayiş — (e) İnvestisiya norması | 2 | 0 | 1 | 1 | 0 |
| B | B. Müəssisə səviyyəsi: SİNTETİK məlumat — texniki nümayiş — (f) Bazar payının amilləri | 1 | 1 | 1 | 0 | 0 |
| B | B. Müəssisə səviyyəsi: SİNTETİK məlumat — texniki nümayiş — (g) İxrac iştirakı | 1 | 0 | 1 | 0 | 0 |

Proqnozda istifadə olunan tənliklər:

| tənlik | qiymətləndirici | hökm | failed_tests |
|---|---|---|---|
| FR10.reg_Nakhchivan_AR_fd | OLS | qeyri-stabil | Chow 2016 p=0.007; Chow 2015 p=0.011 |
| FR10.reg_Absheron_Khizi_fd | OLS | qismən stabil | CUSUM p=0.026 |
| FR10.reg_Daghlig_Shirvan_fd | OLS | stabil | istifadə olunan dəyər (x2 = -0.422) 95% intervaldan kənar (EB büzülməsi) |
| FR10.reg_Ganja_Dashkasan_fd | OLS | qismən stabil | CUSUM p=0.042 |
| FR10.reg_Garabagh_fd | OLS | stabil | istifadə olunan dəyər (x2 = -0.256) 95% intervaldan kənar (EB büzülməsi) |
| FR10.reg_Gazakh_Tovuz_fd | OLS | stabil | istifadə olunan dəyər (x2 = -0.403) 95% intervaldan kənar (EB büzülməsi) |
| FR10.reg_Guba_Khachmaz_lvl | DOLS(+-1) | stabil | kointeqrasiya müəyyən edilməyib; istifadə olunan dəyər (x2 = -0.246) 95% intervaldan kənar (EB büzülməsi) |
| FR10.reg_Lankaran_Astara_fd | OLS | stabil | istifadə olunan dəyər (x2 = -0.412) 95% intervaldan kənar (EB büzülməsi) |
| FR10.reg_Central_Aran_lvl | DOLS(+-1) | qismən stabil | CUSUM p=0.003; kointeqrasiya müəyyən edilməyib; istifadə olunan dəyər (x2 = -0.288) 95% intervaldan kənar (EB büzülməsi) |
| FR10.reg_Mil_Mughan_fd | OLS | stabil | — |
| FR10.reg_Shaki_Zagatala_fd | OLS | stabil | istifadə olunan dəyər (x2 = -0.254) 95% intervaldan kənar (EB büzülməsi) |
| FR10.reg_Eastern_Zangezur_fd | OLS | qismən stabil | rekursiv işarə dəyişməsi (x2) |
| FR10.reg_Shirvan_Salyan_fd | OLS | qismən stabil | rekursiv işarə dəyişməsi (x2) |
| FR10.reg_system | MNL log-nisbət pay sistemi, empirik Bayes büzülməsi (kappa=0.5) | qismən stabil | — |
| FR10.pooled | Bir yönlü sabit effektlər (sahə), birinci fərqlər | qismən stabil | rekursiv işarə dəyişməsi (x) |
| FR10.oil_19 | OLS | qismən stabil | CUSUM p=0.046 |
| FR10.mining_08_rule | Kalibrlənmiş qayda: lövbərlənmiş neytral qayda, real buraxılış son faktiki səviyyədə sabit | qismən stabil | — |
| FR10.mining_07 | Kalibrlənmiş qayda: vahid elastiklik, kəsimdən əvvəl seçilib | qismən stabil | — |
<!-- /AUTO:v2_registry -->

**Komponentlər və proqnoz cədvəli.** `output/FR10_indicator_catalog.csv`, `output/FR10_forecast_tidy.csv`,
`output/FR10_not_forecast.csv`.

<!-- AUTO:v2_tidy -->
414 komponent (prod 127, lp_thsd_AZN_2015 30, output_real_mn_AZN_2015 30, wage_AZN_month 30, output_nominal_mn_AZN 30, employees 30, share_of_industry 30, share_of_manufacturing 24, gos_proxy_margin_pct 24, reg_share 14, reg_output 14, sec_output 4, sec_VA 4, sec_OTP 4, sec_GOS 4, sec_GOS_share_VA 4, sec_labour_share_VA 4, sec_CE 4, ind_output 1, hhi_man 1, nonstate_share 1) × 3 ssenari × 5 il: tamdır (yoxlanılır); tarix hər sıranın ilk ilindən; 193 komponent üçün 5–95% zolaqları (Əsas ssenari). Proqnozlaşdırılmayanlar, səbəbi ilə:

| id_pattern | ad (azərbaycanca) | səbəb (azərbaycanca) |
|---|---|---|
| fr10:tfp:<branch/section> | Ümumi amil məhsuldarlığı (TFP), sahə və bölmə | TFP artım uçotu ilə ölçülür; proqnozu sahə üzrə kapital ehtiyatı və aralıq istehlak proqnozu tələb edir, FR1-də bunlar sahə üzrə yoxdur |
| fr10:early_warning:<branch> | Erkən xəbərdarlıq bayraqları | Bayraqlar son illərin müşahidə olunan dəyişmələri üzrə qərar qaydalarıdır (2023–25 vs 2020–22); proqnoz obyekti deyil |
| fr10:investment_rate:<branch> | İnvestisiya norması, ehtiyatlar/buraxılış, innovasiya intensivliyi, kapital məhsuldarlığı | Bu səmərəlilik göstəriciləri üçün FR1-də ekzogen sürücü yoxdur; öz tarixindən proqnoz qadağandır (avtoreqressiya yoxdur) |
| fr10:sme_share:<activity> | KOS-un buraxılış, məşğulluq, aktivlərdə payı | Yalnız 2023–2024 (iki il) mövcuddur; 2024 səviyyəsində saxlanılır, model yoxdur |
| fr10:enterprises:<branch/region> | Müəssisələrin sayı, yaradılan və ləğv edilən müəssisələr | Giriş/çıxış üçün struktur sürücülü model qurulmayıb; öz tarixindən proqnoz qadağandır |
| fr10:dvx:<indicator> | DVX bəyannamə göstəriciləri (mənfəət vergisi ödəyiciləri, zərər, borclar) | Yalnız 2021–2025 (5 il) və iqtisadiyyat üzrə; sahə üzrə deyil — proqnoz üçün kifayət deyil |
| fr10:product_location_share:<product> | Məhsulların istehsal yerləri üzrə payları (018_1) | Yer üzrə paylar üçün sürücü yoxdur; təsviri göstərici |
| fr10:firm:<firm_id> | Müəssisə səviyyəsində proqnozlar (B qatı) | B qatı SYNTHETIC panel üzrə işləyir; sintetik rejimdə yalnız texniki nümayişdir (FR10_SYNTHETIC_firm_forecast.csv), A qatının komponenti deyil |
| fr10:regional_nonstate_share:<region> | Regionlarda qeyri-dövlət sektorunun payı | Regional mülkiyyət strukturu üçün model yoxdur; tarixi göstərici |
<!-- /AUTO:v2_tidy -->

**Ssenari mühərriki** (`microlib/engines/fr10.py`, vəziyyət faylı `output/engine/FR10_state.json` + `.npz`). Yuxarı
axında FR1 (sürücü yolları `fr1:<code>`) və v2.1-dən etibarən FR4 (`fr4:hired:<activity>` → bölmələr üzrə məşğulluq
indeksləri, 2025 = 1); yuxarı axın nəticələri olmadıqda vəziyyət faylındakı CSV baza dəyərləri istifadə olunur; FR3
istifadə olunmur (F13). FR4-ün indeksləri redaktə edilə bilən ekzogen giriş məlumatlarıdır. Əmsallar reyestrdən
götürülən dəyər, s.x. və etibarlılıq intervalı ilə redaktə edilə bilər; rıçaqlar: neft emalı zavodunun güc əmsalı,
əməyin payının sürüşməsi və marja qaydası, qeyri-neft bölüşdürməsinin kombinasiya çəkisi, regional sistemin κ-sı.

<!-- AUTO:v2_engine -->
Giriş məlumatları: 20 ekzogen yol (FR1 sürücüləri və FR4 indeksləri, 2026–2030, hər ssenari üzrə), 17 əmsal, 6 rıçaq. Öz-özünə test: Əsas — 2070 dəyər üzrə maksimal nisbi fərq 1,2·10⁻¹⁵, Mənfi — 2070 dəyər üzrə maksimal nisbi fərq 1,5·10⁻¹⁵, İslahat — 2070 dəyər üzrə maksimal nisbi fərq 1,4·10⁻¹⁵ — KEÇDİ; icra müddəti hər ssenari üçün 0,007 san.

| eq_id | ad | ad (azərbaycanca) | dəyər | s.x. | ci_low | ci_high |
|---|---|---|---|---|---|---|
| FR10.pooled | x | Əlaqəli sektor elastikliyi β (qeyri-neft sahə payları) | 0.219 | 0.090 | 0.031 | 0.408 |
| FR10.mining_08 | x | Digər faydalı qazıntılar: tikinti əlavə dəyərinə elastiklik (yalnız quarrying_rule = construction_link olduqda) | 1.000 | 0.334 | -0.590 | 0.813 |
| FR10.oil_19 | dln_oil_azn | Neft emalı məhsulları: deflyatorun neft qiymətinə elastikliyi | 0.330 | 0.074 | 0.175 | 0.486 |
| FR10.mining_07 | dln_rva_min | Metal filizləri: sürücüyə elastiklik (qayda: 1) | 1.000 | — | — | — |
| FR10.reg_system | Nakhchivan_AR | Naxçıvan MR: neft-sektor qarışığına elastiklik (büzülmüş) | -0.161 | 0.130 | -0.417 | 0.094 |
| FR10.reg_system | Absheron_Khizi | Abşeron-Xızı: neft-sektor qarışığına elastiklik (büzülmüş) | -0.164 | 0.127 | -0.414 | 0.085 |
| FR10.reg_system | Daghlig_Shirvan | Dağlıq Şirvan: neft-sektor qarışığına elastiklik (büzülmüş) | -0.422 | 0.108 | -0.634 | -0.210 |
| FR10.reg_system | Ganja_Dashkasan | Gəncə-Daşkəsən: neft-sektor qarışığına elastiklik (büzülmüş) | -0.203 | 0.133 | -0.464 | 0.057 |
| FR10.reg_system | Qarabağ | Qarabağ: neft-sektor qarışığına elastiklik (büzülmüş) | -0.256 | 0.132 | -0.514 | 0.002 |
| FR10.reg_system | Gazakh_Tovuz | Qazax-Tovuz: neft-sektor qarışığına elastiklik (büzülmüş) | -0.403 | 0.106 | -0.612 | -0.194 |
| FR10.reg_system | Guba_Khachmaz | Quba-Xaçmaz: neft-sektor qarışığına elastiklik (büzülmüş) | -0.246 | 0.132 | -0.505 | 0.013 |
| FR10.reg_system | Lankaran_Astara | Lənkəran-Astara: neft-sektor qarışığına elastiklik (büzülmüş) | -0.412 | 0.086 | -0.580 | -0.243 |
| FR10.reg_system | Central_Aran | Mərkəzi Aran: neft-sektor qarışığına elastiklik (büzülmüş) | -0.288 | 0.136 | -0.554 | -0.022 |
| FR10.reg_system | Mil_Mughan | Mil-Muğan: neft-sektor qarışığına elastiklik (büzülmüş) | -0.127 | 0.127 | -0.376 | 0.121 |
| FR10.reg_system | Shaki_Zagatala | Şəki-Zaqatala: neft-sektor qarışığına elastiklik (büzülmüş) | -0.254 | 0.129 | -0.508 | -0.001 |
| FR10.reg_system | Eastern_Zangezur | Şərqi Zəngəzur: neft-sektor qarışığına elastiklik (büzülmüş) | -0.096 | 0.153 | -0.397 | 0.204 |
| FR10.reg_system | Shirvan_Salyan | Şirvan-Salyan: neft-sektor qarışığına elastiklik (büzülmüş) | -0.119 | 0.122 | -0.358 | 0.120 |
<!-- /AUTO:v2_engine -->

**Dayanıqlıq və həssaslıq** (`output/FR10_robustness_summary.csv`, `output/FR10_coef_sensitivity.csv`). Reyestrin
qərar qaydası: istifadə olunan hər əmsal rekursiv və bir ili çıxarmaqla yollarda işarəsini saxlayırsa və Chow/CUSUM
p > 0,05 olarsa — *stabil*; rekursiv yolun son yarısında işarə dəyişirsə və ya Chow p < 0,01 olarsa — *qeyri-stabil*;
əks halda — *qismən stabil*. FR10-un bölmə cəmləri FR1-in yollarıdır, buna görə əmsallar buraxılışı sahələr və
regionlar arasında yenidən bölüşdürür, lakin sənaye, emal sənayesi və ya mədənçıxarma cəmlərini dəyişmir — tornado
diaqramı bunu açıq şəkildə göstərir.

<!-- AUTO:v2_sens -->
Dayanıqlıq hökmləri: A qeyri-stabil: 39, A qismən stabil: 46, A stabil: 34, B qismən stabil: 2, B stabil: 12. Əsas komponentlərə sıfırdan fərqli 2030 təsir (Əsas ssenari, baza dəyərinin %-i, −1 s.x. / +1 s.x. və ya rıçağın aşağı / yuxarı dəyəri); heç bir əmsal və ya rıçaq dəyişdirmir: Sənaye buraxılışı, cəmi (30 sahə); Emal sənayesi: Buraxılış; Mədənçıxarma: Buraxılış (bunlar FR1-in yollarıdır). 

| komponent (azərbaycanca) | növ | giriş | effect_low_pct | effect_high_pct |
|---|---|---|---|---|
| Emal sənayesi: Ümumi mənfəət / əlavə dəyər | rıçaq | margin_mode | +7.149 | +12.075 |
| Emal sənayesi: Ümumi mənfəət / əlavə dəyər | rıçaq | labour_share_shift_pp | +1.520 | -1.520 |
| 19 Neft emalı məhsulları: Emal sənayesində pay | rıçaq | cap_factor_19 | -5.091 | +5.091 |
| 19 Neft emalı məhsulları: Emal sənayesində pay | əmsal | FR10.oil_19/dln_oil_azn | +0.683 | -0.678 |

Hər əmsalın istənilən komponentə ən böyük 2030 təsiri (± 1 s.x.):

| giriş | komponent (azərbaycanca) | effect_low_pct | effect_high_pct |
|---|---|---|---|
| FR10.pooled/x | 23 Digər qeyri-metal mineral məhsullar: Real buraxılış (2015 qiymətləri) | +0.725 | -0.718 |
| FR10.mining_08/x | 08 Digər faydalı qazıntılar: Real buraxılış (2015 qiymətləri) | -1.590 | +1.616 |
| FR10.oil_19/dln_oil_azn | 19 Neft emalı məhsulları: Nominal buraxılış | +0.683 | -0.678 |
| FR10.reg_system/Nakhchivan_AR | Naxçıvan MR: sənaye buraxılışında pay | +7.399 | -6.894 |
| FR10.reg_system/Absheron_Khizi | Abşeron-Xızı: sənaye buraxılışında pay | +6.687 | -6.301 |
| FR10.reg_system/Daghlig_Shirvan | Dağlıq Şirvan: sənaye buraxılışında pay | +6.144 | -5.789 |
| FR10.reg_system/Ganja_Dashkasan | Gəncə-Daşkəsən: sənaye buraxılışında pay | +7.451 | -6.945 |
| FR10.reg_system/Garabagh | Qarabağ: sənaye buraxılışında pay | +7.347 | -6.856 |
| FR10.reg_system/Gazakh_Tovuz | Qazax-Tovuz: sənaye buraxılışında pay | +5.966 | -5.635 |
| FR10.reg_system/Guba_Khachmaz | Quba-Xaçmaz: sənaye buraxılışında pay | +7.502 | -6.982 |
| FR10.reg_system/Lankaran_Astara | Lənkəran-Astara: sənaye buraxılışında pay | +4.817 | -4.598 |
| FR10.reg_system/Central_Aran | Mərkəzi Aran: sənaye buraxılışında pay | +7.646 | -7.111 |
| FR10.reg_system/Mil_Mughan | Mil-Muğan: sənaye buraxılışında pay | +7.160 | -6.687 |
| FR10.reg_system/Shaki_Zagatala | Şəki-Zaqatala: sənaye buraxılışında pay | +7.325 | -6.830 |
| FR10.reg_system/Eastern_Zangezur | Şərqi Zəngəzur: sənaye buraxılışında pay | +8.819 | -8.105 |
| FR10.reg_system/Shirvan_Salyan | Şirvan-Salyan: sənaye buraxılışında pay | +6.849 | -6.417 |
<!-- /AUTO:v2_sens -->

**Azərbaycan dilində sətirlər** (`output/FR10_strings_az.csv`).

<!-- AUTO:v2_strings -->
FR10-un CSV fayllarında 1083 ingiliscə sətir; tərcümə şablonu 866, DSK az (018) 137, DSK az (018_1) 49, sahələr lüğəti 24, regionlar lüğəti 4, icra zamanı tərtib olunan (v2.1) 3. DSK-nın rəsmi Azərbaycan dilində adı olan məhsullar: 142 / 142.
<!-- /AUTO:v2_strings -->
