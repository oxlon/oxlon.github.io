> **İngilis dilində (English version):** [FR12_Methodology.md](../FR12_Methodology.md). Rəqəmlərin yazılışı: mətndə onluq kəsr vergüllə, minliklər boşluqla ayrılır; cədvəllərdə, düsturlarda, kodda və fayl adlarında onluq kəsr proqram çıxışında olduğu kimi nöqtə ilə verilir. `AUTO` işarələri arasındakı bloklar hər icrada ingiliscə sənəddən Azərbaycan dilinə köçürülür: `run_all.py` FR12 mərhələsi uğurla başa çatdıqdan sonra `microlib/docgen_az_fr10_fr12.py` faylını çağırır.

# FR12 — Rəqabət mühiti: intensivlik, bazara giriş və çıxış, ssenarilər, erkən xəbərdarlıq
## Göstəricilər sistemi, giriş/çıxışın struktur proqnozları, sənaye təşkilatı (IO) ssenari alətləri və müəssisə səviyyəli rəqabət mühərriki

**MİİS modulu 15.5.2 — Mikroiqtisadi təhlil və proqnozlaşdırma**
Azərbaycan Respublikasının İqtisadiyyat Nazirliyi

`FR12.ipynb` faylını müşayiət edən sənəd. **FR1** (sektor tələbi yolları, kredit, kredit faiz dərəcəsi, makroiqtisadi
qeyri-müəyyənlik) və **FR10** (regional sənaye buraxılışı, sahə payları, müəssisə qrupları üzrə konsentrasiya)
modullarına əsaslanır və müəssisə səviyyəli qat üçün FR10-un əvəz edilə bilən giriş faylı yanaşmasından istifadə edir.

---

## Vəziyyət qeydi (2026-10-02, müstəqil yoxlamadan sonra yenidən işlənib)

**A qatı işləkdir; B qatı DSK biznes reyestrini gözləyir və SİNTETİK məlumatlar üzərində işləyir.** "NACE × region
üzrə müəssisə səviyyəsində gəlir; giriş və çıxış — DSK biznes reyestri" məlumat sorğusu (son tarix 26 avqust 2026)
cavablandırılmayıb. Nazirlik bütün müəssisə məlumatlarını layihə ilə paylaşmayacaq: öz reyestrini öz sisteminə
yükləyəcək. Buna görə B qatı `data/business_register/` qovluğunu oxuyur. Təhvil verilən
`FR12_business_register_SYNTHETIC.csv/.xlsx` faylı **SİNTETİKDİR — real müəssisə məlumatı deyil**: hər sətrin birinci
sütununda bu qeyd olunub, hər müəssisə identifikatoru `SYN-` ilə başlayır, xlsx faylı xəbərdarlığı qalın şriftlə
göstərən README vərəqində açılır və B qatının hər nəticəsi su nişanı sütunu olan `output/FR12_SYNTHETIC_*.csv`
faylıdır. Ondan heç nə A qatının tapıntılarına daxil olmur. Nazirlik onu eyni sxemdə (§17) `FR12_business_register.csv/.xlsx`
faylı (və ya `BUSREG_PATH`-dakı yol) ilə əvəz edir; bundan sonra nəticələr `FR12_FIRM_*.csv` olur.

**v2 (2026-10-05).** Qiymətləndirilmiş hər tənlik `output/FR12_equations.json` faylındadır (reyestr), hər proqnoz
komponentinin `FR12_indicator_catalog.csv` faylında identifikatoru və `FR12_forecast_tidy.csv` faylında tam yolu var
(boşluqlar `FR12_not_forecast.csv` faylında sadalanır), ssenari mühərriki `microlib/engines/fr12.py` notebook-u
təkrarlayır, daxili məlumat boşluqları yalnız təqdimat üçün doldurulur (`FR12_series_filled.csv`), B qatı isə müəssisə
səviyyəsində tam ekonometrik təhlil daşıyır (SİNTETİK nümayiş). Bax §20 (Azərbaycan dilində).

Bu sənəddəki rəqəmlər icranın CSV nəticələrindən **notebook-un sonuncu kod xanası tərəfindən** `AUTO` işarələri
arasında yaradılır, buna görə sənəd nəticələrdən fərqlənə bilməz.

<!-- AUTO:mode_header -->
**B qatının məlumat rejimi: SİNTETİK** — giriş faylı `data/business_register/FR12_business_register_SYNTHETIC.csv`, 92 032 sətir, 15 725 qeyd (2025-ci ildə 226 643 fəal müəssisə), 20 NACE bölməsi, 86 sahə, 14 region, 2019–2025. Reyestr **SİNTETİKDİR — real müəssisə məlumatı deyil**; B qatının nəticələri tapıntılar deyil, emal xəttinin nümayişidir.
<!-- /AUTO:mode_header -->

<!-- AUTO:rev -->
Bu icra: DSK-nın 19 arxivləşdirilmiş buraxılışı və 141 giriş faylı (hər biri URL və SHA-256 ilə); 18 məlumat bütövlüyü tapıntısı; mənbə matrisində 26 göstərici (hazırda mövcud 21, sorğu edilib 4, mövcud deyil 1); Əsas ssenari, 2030, qeydiyyatdan keçmiş sahibkarlıq subyektləri: 104 893 yeni qeydiyyat (90% zolaq 95 603–123 368), giriş əmsalı 5,50% (4,94–6,45), çıxış əmsalı 2,18%; statistik vahidlər 298 998 (292 369–311 669); erkən xəbərdarlıq həddi z* = 2, müşahidə siyahısı: boşdur; 70 FR12 CSV faylı, onlardan 18 SİNTETİK; icra müddəti 24 san.
<!-- /AUTO:rev -->

Tətbiq olunan standartlar (FR10-da olduğu kimi): gecikmiş asılı dəyişən, dəyişənin öz tarixi əsasında proqnoz və
qiymətləndirilmiş qalıq avtoreqressiyası yoxdur; t(n−k) əsasında statistik nəticə ilə kiçik nümunə üçün HAC; sabit
effektlər balanslaşdırılmamış panellərdə dəqiq qiymətləndirilir; hər paneldə cəmi beş il olduğundan göstərilən
əmsallar üzrə statistik nəticə **illər üzrə klaster wild bootstrap** (Webb çəkiləri, icra olunub, B = 499) ilə əldə
edilir və Driscoll–Kraay p-dəyərləri göstərilmir; hər spesifikasiya və lövbərləmə seçimi kəsimdən əvvəlki məlumatlar
üzrə edilir, nümunədən kənar yoxlama toxunulmaz saxlanılır; qayda hər başlanğıcda yenidən tətbiq olunan prosedurdur,
buna görə nümunədən kənar yoxlama və proqnoz eyni lövbərləmədən və eyni ehtiyat variantdan istifadə edir; Theil U həm
təsadüfi gəzişməyə, həm də sabitə qarşı; DM/HLN testləri vahidlər üzrə cütləşdirilir (illər üzrə test üçün hədəf illəri
çox azdır — qeyd olunur); uyğunluq qaydası təlim nümunəsində hər vahid üzrə ən azı iki keçid olduqda tətbiq olunur (əks
halda tətbiq edilmədiyi göstərilir); struktur model üstün gəlmədikdə sıfır model ilə kombinasiya; son qalığa
lövbərləmə (FR1–FR10-un düzəliş əmsalı konvensiyası), hər qaydanın nəzərdə tutduğu təsadüfi gəzişmə çəkisi göstərilməklə;
əmsalların, axınların və ehtiyat artımının inandırıcılığı hər vahidin öz tarixinə qarşı yoxlanılır; arifmetik eynilik
yoxlamaları elə də adlandırılır. Giriş və çıxış *əmsalları* stoxastik trendi olmayan məhdud nisbətlərdir, doğulmalar
isə beş il üzrə vahid effektləri ilə loqarifmlərdə modelləşdirilir, buna görə FR12-də uzunmüddətli səviyyə əlaqəsi
yoxdur: DOLS və Engle–Granger tətbiq edilə bilməz (qeyd olunur, formal olaraq tətbiq edilmir).

---

## 1. Tapşırıq

> *Rəqabət mühitinin təhlili, sektorlarda rəqabət intensivliyinin və müəssisələrin rəqabət strategiyalarının
> qiymətləndirilməsi və proqnazlaşdırılması mümkün olmalıdır.*

Razılaşdırılmış tövsiyə (Tövsiyə – D.Ə., 24 avqust 2026): FR12 aşağıdakıları təqdim edir: (1) **sektorlar üzrə rəqabət
intensivliyinin** və **bazara giriş və çıxışın tezliyinin** ölçülməsi və proqnozları; (2) sənaye təşkilatı (IO)
nəzəriyyəsinə əsaslanaraq sektorların konkret siyasət və ya bazar dəyişikliyinə ehtimal olunan reaksiyasının
fərziyyələr göstərilməklə **ssenari təhlili**; (3) erkən xəbərdarlıq göstəriciləri vasitəsilə rəqabətin **pisləşdiyi**
sektorların aşkarlanması; habelə **bazar konsentrasiyasının** təhlili və proqnozlaşdırılması. Göstəricilər məlumatların
mövcudluğundan asılı olaraq Sifarişçi ilə razılaşdırılır — buna görə məlumat mənbələri matrisi (§5) və boşluqlar
cədvəli (§6) verilir. Məhdudiyyətlər: AR/ARIMA/ARCH/GARCH, gecikmiş asılı dəyişən, dəyişənin öz tarixi əsasında
proqnozlaşdırma yoxdur; əlaqəli sektorların təsirini göstərən struktur modellər; iş kitabında olmayan məlumatlar DSK-dan;
yalnız proqnoz anında mövcud olan məlumatlardan istifadə etməklə sadə müqayisə meyarlarına qarşı NFR1 dəqiqliyi.

### 1.1 Müəssisələrin "rəqabət strategiyası" niyə qiymətləndirilmir və onu nə əvəz edir

Rəqabət strategiyası — xərc liderliyi, diferensiasiya, gizli sövdələşmə, bazara girişin qarşısının alınması, yırtıcı
qiymət siyasəti — **idarəetmə niyyətidir**. Heç bir statistik mənbə onu qeydə almır və aqreqat məlumatlardan niyyətlər
haqqında nəticə çıxarmaq ölçmə kimi təqdim edilən fərziyyə olardı. Rəqabət orqanları strategiyaların təzahür etdiyi
**müşahidə olunan davranışı** izləyir və FR12 də eyni şeyi edir:

| Strategiya səviyyəsində sual | FR12-nin ölçdüyü müşahidə olunan göstərici | Harada |
|---|---|---|
| Mövcud müəssisələr bazara girişin qarşısını alırmı? | giriş əmsalı, yeni daxil olanların ölçüsü, verilmiş lisenziyalar | §8, §16, B qatı |
| Bazar zəif müəssisələri sıradan çıxarırmı? | çıxış əmsalı, kohortlar üzrə Kaplan–Meier sağ qalması, çıxanların ölçüsü | §8, B qatı |
| Müştərilər uğrunda rəqabət varmı? | bazar paylarının qeyri-sabitliyi, sıra mobilliyi | §8, B qatı |
| Bazar gücündən istifadə olunurmu? | qiymət-xərc marjası, Boone mənfəət elastikliyi, giriş azaldıqca marjaların artması | §8, §16, B qatı |
| Bazar strukturu sıxlaşırmı? | HHI, CR4/CR8, ölçü qrupları üzrə konsentrasiya hədləri | §9, §14, B qatı |

## 2. Arxitektura

| Qat | Vahid | Məlumatlar | Vəziyyət |
|---|---|---|---|
| **A — hazırda işləkdir** | DSK-nın 11 fəaliyyət qrupu; 19 NACE bölməsi; 14 iqtisadi rayon; vergi ödəyicilərinin ölçü qrupları | DSK statistik reyestri (`st_units`), sahibkarlıq, milli hesablar; **DSK-nın arxivləşdirilmiş buraxılışları**; iş kitabı `Regionlar*`, `DVX üzrə göstəricilər`, `Verilmiş lisenziyalar`, `Aparılan yoxlamalar`; FR1, FR10 nəticələri | nəticələr (§8–§16) |
| **B — müəssisə səviyyəli rəqabət mühərriki** | müəssisə (statistik vahid) × NACE sahəsi (iki rəqəmli kod) × region × il | DSK biznes reyestri (sorğu edilib) | SİNTETİK emal xəttinin nümayişi (§17) |

Mənbələrdə üç müəssisə məcmusu var və onlar heç vaxt bir əmsalda qarışdırılmır (F6 tapıntısı): **qeydiyyatdan keçmiş
sahibkarlıq subyektləri** (hüquqi şəxslər və fərdi sahibkarlar, DSK sahibkarlıq 006 — ən uzun fəaliyyət sırası),
reyestrin **statistik vahidləri** (hüquqi vahidlər, `st_units` və iş kitabının regional vərəqləri) və **fəal vergi
ödəyiciləri** (DVX).

## 3. Toplanmış məlumatlar

DSK sahibkarlıq cədvəllərini **yalnız son iki il üzrə**, statistik reyestri isə **yalnız son dövr üzrə** dərc edir.
Buna görə FR12 **eyni DSK fayllarının əvvəlki buraxılışlarını** Internet Archive-dan bərpa edir
(`web.archive.org/web/<timestamp>id_/…`, orijinal baytları qaytarır), hər birinin həqiqi Excel faylı olduğunu yoxlayır,
onu bir dəfə `data/dsk_competition/vintages/` qovluğunda saxlayır və sonra diskdən yenidən oxuyur. Bu, ikiillik
cədvəlləri 2019–2024 fəaliyyət panelinə çevirir (heç bir arxiv buraxılışının əhatə etmədiyi 2021-ci il istisna olmaqla)
və 2021, 2024 və 2025-ci illər üçün NACE bölmələri üzrə tam illik reyestr axınlarını verir. FR10-un `data/dsk_enterprise/`
qovluğundakı yükləmələri oxunur, heç vaxt dəyişdirilmir.

<!-- AUTO:data -->
| mənşə | vəziyyət | fayllar |
|---|---|---|
| DSK cari fayl | mövcuddur | 7 |
| FR10 yükləməsi (yalnız oxumaq üçün) | mövcuddur | 115 |
| arxiv versiyası | mövcuddur | 19 |

Arxivləşdirilmiş buraxılışlar və DSK-dan yeni yükləmələr (SHA-256 ilə tam siyahı `FR12_dsk_manifest.csv` faylındadır):

| fayl | mənbə URL | məzmun | sha256 |
|---|---|---|---|
| e006_v2022.xls | https://web.archive.org/web/20220403145449id_/http://www.stat.gov.az/source/entrepreneurship/en/006en.xls | qeydiyyatda / yeni / qeydiyyatdan çıxan, 11 qrup, 2019–2020 | 44f2d2706080403f… |
| e006_v2025.xls | https://web.archive.org/web/20250421050555id_/http://www.stat.gov.az/source/entrepreneurship/en/006en.xls | qeydiyyatda / yeni / qeydiyyatdan çıxan, 11 qrup, 2022–2023 | b057faa225e5cada… |
| e012_v2022.xls | https://web.archive.org/web/20220403145405id_/http://www.stat.gov.az/source/entrepreneurship/en/012en.xls | fəaliyyət növləri üzrə KOS-un buraxılışda payı | 2ab90d4957b5df96… |
| e012_v2025.xls | https://web.archive.org/web/20250421045614id_/http://www.stat.gov.az/source/entrepreneurship/en/012en.xls | fəaliyyət növləri üzrə KOS-un buraxılışda payı | b9ba7429133cb42b… |
| e013_v2022.xls | https://web.archive.org/web/20220403145451id_/http://www.stat.gov.az/source/entrepreneurship/en/013en.xls | fəaliyyət növləri üzrə KOS-un işçi sayında payı | 10245846c60add67… |
| e013_v2025.xls | https://web.archive.org/web/20250421050729id_/http://www.stat.gov.az/source/entrepreneurship/en/013en.xls | fəaliyyət növləri üzrə KOS-un işçi sayında payı | f2adde71b767b91c… |
| e002_v2022.xls | https://web.archive.org/web/20220403145508id_/http://www.stat.gov.az/source/entrepreneurship/en/002en.xls | ölçü üzrə fəal KOS | 6e0f07d0a1b3fd66… |
| e002_v2025.xls | https://web.archive.org/web/20250421045707id_/http://www.stat.gov.az/source/entrepreneurship/en/002en.xls | ölçü üzrə fəal KOS | ee431314a2413a86… |
| e024_v2022.xls | https://web.archive.org/web/20220403145523id_/http://www.stat.gov.az/source/entrepreneurship/en/024en.xls | bir il əvvəl yaradılmış fəal KOS | 221ec757c3dee0a0… |
| e024_v2025.xls | https://web.archive.org/web/20250421045635id_/http://www.stat.gov.az/source/entrepreneurship/en/024en.xls | bir il əvvəl yaradılmış fəal KOS | b9b52861245c4d0f… |
| s21_FY2021_az.xls | https://web.archive.org/web/20220307165205id_/http://www.stat.gov.az/source/st_units/az/2_1_az.xls | bölmələr üzrə yaradılan / ləğv edilən vahidlər, 2021 tam il | eed343178b2e0218… |
| s21_H1_2022_en.xls | https://web.archive.org/web/20220818184803id_/http://www.stat.gov.az/source/st_units/en/2_1en.xls | bölmələr üzrə yaradılan / ləğv edilən vahidlər, 2022 yanvar–iyun | 62a7fbc564a87b3b… |
| s21_H1_2024_az.xls | https://web.archive.org/web/20240927033915id_/http://www.stat.gov.az/source/st_units/az/2_1_az.xls | bölmələr üzrə yaradılan / ləğv edilən vahidlər, 2024 yanvar–iyun | 342d93cc34315a62… |
| s21_FY2024_en.xls | https://web.archive.org/web/20250416142637id_/http://www.stat.gov.az/source/st_units/en/2_1en.xls | bölmələr üzrə yaradılan / ləğv edilən vahidlər, 2024 tam il | c7a843aeb14578ce… |
| s21_H1_2025_az.xls | https://web.archive.org/web/20250712215241id_/http://www.stat.gov.az/source/st_units/az/2_1_az.xls | bölmələr üzrə yaradılan / ləğv edilən vahidlər, 2025 yanvar–iyun | 37991621e15c2cbf… |
| s21_FY2025_az.xls | https://web.archive.org/web/20260213212129id_/http://www.stat.gov.az/source/st_units/az/2_1_az.xls | bölmələr üzrə yaradılan / ləğv edilən vahidlər, 2025 tam il | 5bed3580d3ffde57… |
| s23_FY2021_az.xls | https://web.archive.org/web/20220307165212id_/http://www.stat.gov.az/source/st_units/az/2_3_az.xls | regionlar üzrə yaradılan / ləğv edilən vahidlər, 2021 tam il | 4b0196b144ce9001… |
| s23_FY2024_en.xls | https://web.archive.org/web/20250416142923id_/http://www.stat.gov.az/source/st_units/en/2_3en.xls | regionlar üzrə yaradılan / ləğv edilən vahidlər, 2024 tam il | bb21aee319bc60e0… |
| s23_FY2025_az.xls | https://web.archive.org/web/20260213212343id_/http://www.stat.gov.az/source/st_units/az/2_3_az.xls | regionlar üzrə yaradılan / ləğv edilən vahidlər, 2025 tam il | 8492a16cbe46fe5d… |
| 1_4_o_en.xls | https://www.stat.gov.az/source/st_units/en/1_4_o_en.xls | regionlar üzrə orta sahibkarlıq subyektləri | e2b137f53977a5e2… |
| 1_4_k_en.xls | https://www.stat.gov.az/source/st_units/en/1_4_k_en.xls | regionlar üzrə kiçik sahibkarlıq subyektləri | f03ea5aa5a132007… |
| 1_4_m_en.xls | https://www.stat.gov.az/source/st_units/en/1_4_m_en.xls | regionlar üzrə mikro sahibkarlıq subyektləri | cb4ff476f7c2887b… |
| 1_5_en.xls | https://www.stat.gov.az/source/st_units/en/1_5_en.xls | fəaliyyət növləri üzrə fərdi sahibkarlar | c032938e98ef6350… |
| 1_6_en.xls | https://www.stat.gov.az/source/st_units/en/1_6_en.xls | regionlar üzrə fərdi sahibkarlar | 8b6a4fe9d15c7306… |
| 1_7_en.xls | https://www.stat.gov.az/source/st_units/en/1_7_en.xls | cins və fəaliyyət növü üzrə fərdi sahibkarlar | 29304857b87c0d8c… |
| 1_8_en.xls | https://www.stat.gov.az/source/st_units/en/1_8_en.xls | cins və region üzrə fərdi sahibkarlar | 92319b5ae23bbe65… |

Fəaliyyət panelinin illəri: 2019, 2020, 2022, 2023, 2024; regional panel: 2021, 2022, 2023, 2024, 2025; bölmələr üzrə reyestr axınları: tam illər 2021, 2024, 2025, yarımillər 2022, 2024, 2025, 2026.
<!-- /AUTO:data -->

## 4. Məlumat bütövlüyü üzrə tapıntılar

<!-- AUTO:integrity -->
| id | tapıntı | sübut | nəticə |
|---|---|---|---|
| F1 | DSK-nın sahibkarlıq cədvəlləri yalnız son iki ili, reyestr isə yalnız son dövrü dərc edir | cari fayllar: 2023–2024 (sahibkarlıq), 1 iyul 2026 (st_units) | DSK-nın arxiv versiyaları bərpa edilib (4-cü hissə): 006 üçün 2019, 2020, 2022–2024; bölmələr üzrə reyestr axınları üçün 2021, 2024, 2025 |
| F2 | Sahibkarlıq 006 üçün 2021-ci ili, reyestr axınları üçün isə 2022–2023-cü illərin tam ilini əhatə edən arxiv versiyası yoxdur | İnternet Arxivində 006 yalnız 2022-ci ilin aprel və 2025-ci ilin aprel versiyaları, 2_1 isə 2022 mart, 2022 avqust, 2024 sentyabr, 2025 aprel, 2025 iyul, 2026 fevral versiyaları ilə var | fəaliyyət paneli zaman üzrə balanssızdır (2019, 2020, 2022, 2023, 2024); 2021 qiymətləndirmədə istifadə olunmur; qrafiklər və cədvəllər üçün interpolyasiya ilə doldurulur və işarələnir (FR12_series_filled.csv, 7.1-ci hissə) |
| F3 | 2023-cü il 006-nın iki versiyasında dərc olunub; düzəlişlər qeydə alınıb | maks. /yenidənbaxma/: yeni qeydiyyata alınmış 0, qeydiyyatdan çıxarılmış 0 vahid | sonrakı versiya istifadə olunur; NFR1 real vaxt qeydi: nümunədən kənar yoxlamanın faktiki dəyərləri son versiyadandır |
| F4 | Qeydiyyatdakı sahibkarlıq subyektləri ehtiyat-axın eyniliyinə dəqiq tabe deyil | 2020: ΔN − (yeni − qeydiyyatdan çıxan) = -17,137; 2023: ΔN − (yeni − qeydiyyatdan çıxan) = +8,716; 2024: ΔN − (yeni − qeydiyyatdan çıxan) = +6,653 | qeydiyyata əsaslanan əmsallar DSK kimi ilin sonundakı qeydiyyat ehtiyatını məxrəc götürür; bərpalar / yenidən təsnifatlar qalıqdır |
| F5 | Bölmələr üzrə reyestr ehtiyatı N(t) = N(t−1) + yeni − ləğv edilən eyniliyinə dəqiq tabe deyil | 2025, bölmələr üzrə cəm: +0 vahid; ən böyük bölmə fərqləri: S +129, L +50, G +36 | reyestrdə bölmələrin yenidən təsnifatı; SİNTETİK reyestr doğulma və ölümləri dəqiq təkrarlayır və ehtiyat fərqini göstərir (17-ci hissə) |
| F6 | Mənbələrdə üç fərqli müəssisə məcmusu var | qeydiyyatdakı sahibkarlıq subyektləri (fərdi sahibkarlar daxil) 1,505,893 (2024), statistik vahidlər 226,643 (1 yanvar 2026); aktiv vergi ödəyiciləri 859,345 (2025) | hər göstərici öz məcmusunu bildirir; əmsallar məcmular arasında qarışdırılmır |
| F7 | 2020-ci ildə kənd təsərrüfatında qeydiyyat sıçrayışı | kənd təsərrüfatında yeni qeydiyyatlar 28,521 (2019) → 108,807 (2020) | bazara giriş deyil, fermerlərin inzibati qeydiyyatı (subsidiya sistemi); kənd təsərrüfatı paneldə saxlanılır, onun sabit effekti və 2020 dayanıqlıq yoxlaması verilir |
| F8 | İş kitabı DVX: mikro vergi ödəyicisi sətirləri büdcə təşkilatı sətirlərini təkrarlayır | say, dövriyyə və daxilolmalar 4 ildə eynidir: bəli | mikro vergi ödəyiciləri ölçü qrupu konsentrasiyasından çıxarılır; Vergi Xidməti tərəfindən düzəldilməlidir |
| F9 | DSK 1_1_en.xls: A bölməsinin sətri `of which:` kimi adlanıb | kənd təsərrüfatı sətri yuxarı sətrin adını daşıyır | FR12 ölçü qrupu cədvəllərini bölmə nümunəsi ilə oxuyur və bölmə cəmlərini dərc olunmuş cəmlə yoxlayır |
| F10 | Dövlət idarəetməsi (O) inzibati yenidənqurma ilə bağlı ləğvlər göstərir | FY 2021: ləğv edilən 71, yeni 20; FY 2024: ləğv edilən 74, yeni 14; FY 2025: ləğv edilən 167, yeni 37; H1 2022: ləğv edilən 5, yeni 31; H1 2024: ləğv edilən 38, yeni 10; H1 2025: ləğv edilən 17, yeni 27; H1 2026: ləğv edilən 228, yeni 10 | O və U (ekstraterritorial) qeyri-bazar bölmələridir: rəqabət göstəricilərindən çıxarılır, cəmlərdə saxlanılır |
| F11 | İş kitabının region vərəqləri DSK reyestrinin region məlumatına bərabərdir | statistik vahidlər, yeni və ləğv edilənlər: 2021, 2024 və 2025-də eynidir (5-ci hissədə yoxlanılıb) | 2021–2025 regional panel reyestr sırasıdır; regional giriş/çıxış onun üzərində modelləşdirilir |
| F12 | Ölçü qrupu sayları (1_3) yalnız kommersiya təşkilatlarını əhatə edir | iri + orta + kiçik + mikro = 215,416, statistik vahidlər 232 847 (1 iyul 2026) | ölçü qrupu konsentrasiya hədləri kommersiya təşkilatlarının saylarından istifadə edir |
| F13 | Yanvar–iyun axınları tam il axınlarının yarısı deyil | 2024-cü il I yarım: yeni 6,390, 2024 tam il: 14,865 | yarımillik fayllar yalnız təsviri monitorinq üçündür; modellər tam il axınlarından istifadə edir |
| F14 | Reyestr üzrə ləğvlər sahibkarlıq subyektlərinin qeydiyyatdan çıxarılmasından xeyli azdır | reyestr üzrə çıxış əmsalı 0.31% (2025), qeydiyyatdan çıxma əmsalı 1.66% (2024, 006) | fəaliyyətsiz hüquqi vahidlər reyestrdə qalır: reyestr üzrə çıxış bazardan çıxışı azaldılmış göstərir; çıxış proqnozları 006-nın qeydiyyatdan çıxma sırasından istifadə edir |
| F15 | KOS-un buraxılış payları (012) və milli hesablar buraxılışı fərqli bazalardan istifadə edir | təhsil və səhiyyədə pay milli hesablar buraxılışına tətbiq edildikdə KOS-un orta gəliri qanuni sinif tavanını aşır (bazada dövlət buraxılışı var) | həmin qrup-illər üçün yuxarı hədd gəlir tavanlarını atır (tavansız supremum) və işarələnir |
| F16 | 2022-ci ildə ölkə üzrə qeydiyyatdan çıxarma dalğası | qeydiyyatdan çıxarılan subyektlər 22,572 (2020), 57,734 (2022), 21,000 (2023) | birdəfəlik inzibati təmizləmə: çıxış tənliklərində ümumi 2022 impuls dummy-si, nümunədən kənarda sıfır |
| F17 | DSK 006-da versiyalar arasında tərif dəyişikliyi | 2019–2020 versiyası: 'yeni yaradılmış' / 'ləğv edilmiş' müəssisələr (tapıldı: bəli); 2022+ versiyalar: 'yeni qeydiyyatdan keçmiş' / 'qeydiyyatdan çıxarılmış' (tapıldı: bəli) | doğulma tənliyi qırılma termini daşıyır (2022-dən 1); çıxış yalnız 2022 impulsunu saxlayır (2023–2024 çıxış səviyyələri 2019–2020-yə yaxındır: davamlı qırılma görünmür) |
| F18 | Yoxlamaların sayı zamanla əhatəni dəyişir | yoxlamaların cəmi 17 (2015), 1,648 (2019), 17,082 (2020), 50,071 (2025); Fövqəladə Hallar Nazirliyinin yanğın təhlükəsizliyi yoxlamaları 2020-dən, kommunal yoxlamalar (Azərişıq, Azəriqaz) 2021–2022-dən daxil olur | yoxlamalar illər arasında müqayisəli deyil və erkən xəbərdarlıq balında istifadə olunmur; yalnız məlumat üçün verilir |
<!-- /AUTO:integrity -->

## 5. Göstəricilər sistemi: hansı məlumatlar, hansı mənbədən, hansı göstərici üçün, hansı formada

`output/FR12_data_source_matrix.csv` faylında hər göstərici üçün bir sətir (göstərici Azərbaycan və ingilis dillərində,
düstur, ölçü vahidi, mənbə qurum, cədvəl və sətir, təfərrüat səviyyəsi, tezlik, hazırda mövcud olan illər, vəziyyət,
MİİS-ə inteqrasiya üsulu, analitik istifadə, təqdimat forması, yenilənmə tezliyi, alternativ).

<!-- AUTO:matrix_summary -->
| istiqamət | hazırda mövcuddur | mövcud deyil | sorğu göndərilib |
|---|---|---|---|
| Maneələr və tənzimləmə | 3 | 1 | 0 |
| Konsentrasiya və rəqabət intensivliyi | 8 | 0 | 0 |
| Giriş və çıxış | 7 | 0 | 0 |
| Müəssisə səviyyəsi (B qatı) | 0 | 0 | 4 |
| Marjalar və bazar gücü | 3 | 0 | 0 |
<!-- /AUTO:matrix_summary -->

<!-- AUTO:matrix -->
| id | istiqamət | göstərici (azərbaycanca) | göstərici (ingiliscə) | düstur | mənbə qurum | məlumat dəsti / cədvəl / sətir | təfərrüat səviyyəsi | hazırda mövcud olan illər | vəziyyət | MİİS-ə inteqrasiya üsulu | analitik istifadə | təqdimat forması | mövcud olmadıqda alternativ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I01 | Giriş və çıxış | Giriş əmsalı (fəaliyyət növləri) | Entry rate by activity group | yeni qeydiyyat / qeydiyyatda olanlar (ilin sonu) × 100; doğulmalar log axın kimi modelləşdirilir, əmsal ehtiyat eyniliyi ilə | DSK | sahibkarlıq 006 (+ arxiv versiyaları; 2022-ci il tərif dəyişikliyi, F17) | 11 fəaliyyət qrupu | 2019-2024 (5 il: 2019, 2020, 2022, 2023, 2024) | hazırda mövcuddur | DSK-nın arxiv versiyaları (skriptlə) | struktur doğulma modeli (11–13-cü hissələr) | proqnoz zolaqlı zaman sırası qrafiki | - |
| I02 | Giriş və çıxış | Çıxış əmsalı (fəaliyyət növləri) | Exit rate by activity group | qeydiyyatdan çıxarılanlar / qeydiyyatda olanlar × 100 | DSK | sahibkarlıq 006 | 11 fəaliyyət qrupu | 2019-2024 (5 il: 2019, 2020, 2022, 2023, 2024) | hazırda mövcuddur | DSK-nın arxiv versiyaları (skriptlə) | struktur çıxış modeli | proqnoz zolaqlı zaman sırası qrafiki | - |
| I03 | Giriş və çıxış | Xalis giriş, dövriyyə (churn) | Net entry and churn | giriş − çıxış; giriş + çıxış | DSK | sahibkarlıq 006 | 11 fəaliyyət qrupu | 2019-2024 (5 il: 2019, 2020, 2022, 2023, 2024) | hazırda mövcuddur | DSK-nın arxiv versiyaları (skriptlə) | erkən xəbərdarlıq | idarə paneli KPI kartı | - |
| I04 | Giriş və çıxış | Statistik vahidlərin yaranması/ləğvi (bölmələr) | New / liquidated statistical units by NACE section | yaradılan və ya ləğv edilən / dövrün sonuna vahidlər | DSK | st_units 2_1 (+ versiyalar) | 19 NACE bölməsi | 2021, 2024, 2025 (FY); H1 2022, 2024-2026 | hazırda mövcuddur | DSK-nın arxiv versiyaları (skriptlə) | bölmə monitorinqi; B qatının kalibrləməsi | istilik xəritəsi bölmə × il | - |
| I05 | Giriş və çıxış | Regionlar üzrə giriş və çıxış | Entry and exit by economic region | yaradılan və ya ləğv edilən / vahidlər | DSK (iş kitabı vasitəsilə) | iş kitabı 'Regionlar*' r38/r42/r43; st_units 2_3 | 14 iqtisadi rayon | 2021-2025 | hazırda mövcuddur | iş kitabının yüklənməsi (Nazirlik) | regional giriş/çıxış modeli; istilik xəritəsi | xəritə; region × il istilik xəritəsi | - |
| I06 | Giriş və çıxış | Kohort ölçüsü nisbəti (1-5 il) | Cohort-size ratio, ages 1-5 (not a survival rate) | eyni ildə k yaşlı fəal KOS / 1 yaşlı fəal KOS (kohort ölçüsü ilə sağ qalmanı qarışdırır) | DSK | sahibkarlıq 024–028 | 11 qrup × ölçü | 2023-2024 | hazırda mövcuddur | faylın yüklənməsi (DSK saytı, skriptlə) | yalnız məlumat üçün (erkən xəbərdarlıq balına daxil deyil) | cədvəl | reyestr üzrə kohortlar üçün Kaplan–Meyer sağ qalma əyrisi (B qatı) |
| I07 | Giriş və çıxış | Fəal müəssisələrin sayı (proqnoz) | Number of active units (forecast) | N(t) = (N(t−1) + doğulmalar(t)) / (1 + çıxış əmsalı(t)) (ehtiyat-axın eyniliyi) | hesablanmış | 13-cü hissə | qruplar, regionlar | 2026-2030 | hazırda mövcuddur | MİİS daxili (FR modulunun nəticəsi) | proqnoz | proqnoz zolağı | - |
| I08 | Konsentrasiya və rəqabət intensivliyi | KOS-un buraxılışda payı | SME share of output | KOS buraxılışı / cəmi × 100 | DSK | sahibkarlıq 012 (+ versiyalar) | 11 qrup × mikro/kiçik/orta | 2019-2024 (5 il: 2019, 2020, 2022, 2023, 2024) | hazırda mövcuddur | DSK-nın arxiv versiyaları (skriptlə) | konsentrasiya hədləri; payların proyeksiyası | yığılmış sütun; trend | - |
| I09 | Konsentrasiya və rəqabət intensivliyi | KOS-un məşğulluqda payı | SME share of employees | KOS işçiləri / cəmi × 100 | DSK | sahibkarlıq 013 (+ versiyalar) | 11 qrup × ölçü | 2019-2024 (5 il: 2019, 2020, 2022, 2023, 2024) | hazırda mövcuddur | DSK-nın arxiv versiyaları (skriptlə) | ölçü strukturu | yığılmış sütun | - |
| I10 | Konsentrasiya və rəqabət intensivliyi | Ölçü qrupları üzrə müəssisələr | Units by size class | say | DSK | st_units 1_3, 1_4; sahibkarlıq 005 | bölmə / region × ölçü | 2026 vəziyyəti; 2023-2024 | hazırda mövcuddur | faylın yüklənməsi (DSK saytı, skriptlə) | konsentrasiya hədləri; B qatının kalibrləməsi | cədvəl | - |
| I11 | Konsentrasiya və rəqabət intensivliyi | HHI/CR4 hədləri (ölçü qrupları) | HHI / CR4 bounds from size classes | aşağı hədd Σ S²/n; yuxarı hədd qutu-simpleksin təpəsi (8-ci hissə) | hesablanmış (DSK) | 8-ci hissə | 11 qrup | 2023-2024 | hazırda mövcuddur | MİİS daxili (FR modulunun nəticəsi) | konsentrasiya monitorinqi; erkən xəbərdarlıq | konsentrasiya hədləri qrafiki (interval sütunları) | müəssisə səviyyəsində HHI (B qatı) |
| I12 | Konsentrasiya və rəqabət intensivliyi | Vergi ödəyicilərinin ölçü qrupları | Taxpayer size classes: count, turnover, receipts, employees | bəyan edilmiş dövriyyədə iri ödəyicilərin payı; HHI aşağı həddi | DVX | iş kitabı 'DVX üzrə göstəricilər' r111–r126 | iqtisadiyyat, 4 qrup | 2022-2025 | hazırda mövcuddur | iş kitabının yüklənməsi (Nazirlik) | iqtisadiyyat üzrə konsentrasiya | KPI kartı; trend | - |
| I13 | Konsentrasiya və rəqabət intensivliyi | Sahələr üzrə aktiv vergi ödəyiciləri | Active taxpayers by sector | say | DVX | iş kitabı 'DVX üzrə göstəricilər' r131–r145 | 5 sahə (digərləri boşdur) | 2021-2025 | hazırda mövcuddur | iş kitabının yüklənməsi (Nazirlik) | giriş dinamikasının çarpaz yoxlanışı | cədvəl | reyestr sayları (DSK) |
| I14 | Konsentrasiya və rəqabət intensivliyi | Sahə paylarının qeyri-sabitliyi | Share instability across branches | ½ Σ/Δs/ | FR10 | FR10_branch_shares_history.csv | emal sənayesinin 24 sahəsi | 2006-2025 | hazırda mövcuddur | MİİS daxili (FR modulunun nəticəsi) | erkən xəbərdarlıq (mobilliyin azalması) | trend | - |
| I15 | Konsentrasiya və rəqabət intensivliyi | Regional dispersiya | Regional dispersion of entry; HHI of units across regions | variasiya əmsalı; Σ s² | hesablanmış | 7-ci hissə | 14 iqtisadi rayon | 2021-2025 | hazırda mövcuddur | MİİS daxili (FR modulunun nəticəsi) | regional monitorinq | xəritə | - |
| I16 | Marjalar və bazar gücü | Qiymət-xərc marjası (proksi) | Price-cost margin proxy | (ƏDV − əmək haqqı) / buraxılış × 100 | DSK | milli hesablar 013 | 19 bölmə / 11 qrup | 2005-2025 | hazırda mövcuddur | faylın yüklənməsi (DSK saytı, skriptlə) | giriş modelinin sürücüsü; erkən xəbərdarlıq (marja artır, giriş azalır) | trend; kvadrant | - |
| I17 | Marjalar və bazar gücü | Sənaye marjası (FR10 proqnozu) | Industry margin path (FR10 section forecasts) | (ƏDV − əmək haqqı) / buraxılış, B–E | FR10 | FR10_forecast_sections.csv | B–E bölmələri | 2025-2030 | hazırda mövcuddur | MİİS daxili (FR modulunun nəticəsi) | qayda marjanı seçərsə sənaye üçün marja yolu; cari qaydalar seçmir, bu icrada istifadə olunmur | trend | - |
| I18 | Marjalar və bazar gücü | Lerner indeksi (ssenari) | Lerner index (scenario calibration) | HHI / ε (Kurno) | hesablanmış | 15-ci hissə | sahə | - | hazırda mövcuddur | MİİS daxili (FR modulunun nəticəsi) | ssenari simulyatoru | fərziyyələr paneli olan simulyator | - |
| I19 | Maneələr və tənzimləmə | Verilmiş lisenziyalar | Licences issued | say; 1000 vahidə | İqtisadiyyat Nazirliyi | iş kitabı 'Verilmiş lisenziyalar' | 24 lisenziya növü → qruplar | 2016-2025 | hazırda mövcuddur | iş kitabının yüklənməsi (Nazirlik) | giriş göstəricisi (məlumat; maneə bayrağı deyil) | trend; cədvəl | - |
| I20 | Maneələr və tənzimləmə | Aparılan yoxlamalar | Inspections of businesses (coverage changes over time, F18) | say | yoxlama orqanları | iş kitabı 'Aparılan yoxlamalar' | 19 orqan | 2015-2025 (illər üzrə müqayisəli deyil) | hazırda mövcuddur | iş kitabının yüklənməsi (Nazirlik) | yalnız məlumat üçün | cədvəl | NACE kodları və sabit əhatəli yoxlamalar reyestri |
| I21 | Maneələr və tənzimləmə | Dövlət mülkiyyətinin payı | State share: of industrial output (S5 calibration); of active SMEs (information) | dövlət buraxılışı / buraxılış; dövlət KOS-ları / fəal KOS | DSK | sənaye 010_2, FR10_ownership.csv vasitəsilə (buraxılış, 2005–2025); sahibkarlıq 005 (KOS, 2023–2024) | sənaye; 11 qrup | 2005-2025; 2023-2024 | hazırda mövcuddur | faylın yüklənməsi (DSK saytı, skriptlə) | qarışıq oliqopoliya ssenarisi (S5); məlumat | sütun | reyestrdən bazarlar üzrə dövlət müəssisələrinin gəlir payı (B qatı) |
| I22 | Maneələr və tənzimləmə | İdxal rəqabəti (daxili bazarda payı) | Import penetration by product group | idxal / (buraxılış − ixrac + idxal) | DGK / DSK | HS × NACE üzrə gömrük məlumatı | sahə | - | mövcud deyil | Dövlət Gömrük Komitəsi ilə məlumat mübadiləsi razılaşması | tarif / idxal rəqabəti ssenarisi | simulyator girişi | FR5/FR1 idxal aqreqatları; ədəbiyyatdakı kənar paylar |
| I23 | Müəssisə səviyyəsi (B qatı) | Müəssisə gəliri (bazar payları, HHI) | Firm revenue (market shares, HHI, CR4/CR8, entropy, Gini) | 17-ci hissənin mühərriki | DSK | biznes reyestri: gəlir | müəssisə × NACE × region × il | yalnız SİNTETİK | sorğu göndərilib | DSK ilə məlumat mübadiləsi razılaşması (biznes reyestrindən çıxarış) | B qatının rəqabət mühərriki | müəssisə səviyyəsində bazar strukturu görünüşü | A qatının hədləri və əmsalları (bu modul) |
| I24 | Müəssisə səviyyəsi (B qatı) | Qeydiyyat və ləğv tarixləri | Firm entry and exit dates (entry/exit, survival, cohort shares) | 17-ci hissənin mühərriki | DSK | biznes reyestri: qeydiyyat / ləğv tarixi | müəssisə × NACE × region × il | yalnız SİNTETİK | sorğu göndərilib | DSK ilə məlumat mübadiləsi razılaşması (biznes reyestrindən çıxarış) | B qatının rəqabət mühərriki | müəssisə səviyyəsində bazar strukturu görünüşü | A qatının hədləri və əmsalları (bu modul) |
| I25 | Müəssisə səviyyəsi (B qatı) | Xərclər (marja, Boone indikatoru) | Firm costs (price-cost margin, Boone indicator) | 17-ci hissənin mühərriki | DSK | biznes reyestri: satışın maya dəyəri / əməliyyat xərcləri | müəssisə × NACE × region × il | yalnız SİNTETİK | sorğu göndərilib | DSK ilə məlumat mübadiləsi razılaşması (biznes reyestrindən çıxarış) | B qatının rəqabət mühərriki | müəssisə səviyyəsində bazar strukturu görünüşü | A qatının hədləri və əmsalları (bu modul) |
| I26 | Müəssisə səviyyəsi (B qatı) | Mülkiyyət, region, ölçü | Firm attributes (SOE share, region × sector view) | 17-ci hissənin mühərriki | DSK | biznes reyestri: mülkiyyət, region, ölçü qrupu | müəssisə × NACE × region × il | yalnız SİNTETİK | sorğu göndərilib | DSK ilə məlumat mübadiləsi razılaşması (biznes reyestrindən çıxarış) | B qatının rəqabət mühərriki | müəssisə səviyyəsində bazar strukturu görünüşü | A qatının hədləri və əmsalları (bu modul) |
<!-- /AUTO:matrix -->

## 6. Boşluqlar, alternativlər və Sifarişçi ilə razılaşdırılmalı tədbirlər

<!-- AUTO:gaps -->
| boşluq | təsir | hazırda istifadə olunan alternativ | alternativin meyli və ya məhdudiyyəti | Sifarişçi ilə razılaşdırılmalı tədbir |
|---|---|---|---|---|
| NACE × region üzrə müəssisə səviyyəsində gəlir (DSK biznes reyestri) | müəssisə HHI/CR4-ü, bazar payı mobilliyi, Boone indikatoru yoxdur | ölçü qrupları üzrə konsentrasiya hədləri (8-ci hissə); FR10-dan sahə paylarının qeyri-sabitliyi | KOS üstünlük təşkil etdikdə hədlər genişdir; fəaliyyət qrupları antiinhisar bazarlarından genişdir | reyestr çıxarışını təsdiqləmək (24 avqust 2026 sorğusu); psevdonimləşdirilmiş firm_id və illik ötürülmə barədə razılaşmaq |
| Müəssisələrin giriş və çıxış tarixləri | kohort sağ qalması, giriş/çıxış edənlərin ölçüsü yoxdur | DSK 006 qeydiyyat axınları; 024–028 yaş strukturu; reyestr axınları 2_1/2_3 | 006 bazara girişi deyil, fərdi sahibkarlar daxil qeydiyyatları sayır; reyestr üzrə çıxış çıxışı azaldılmış göstərir (F14) | reyestr çıxarışına qeydiyyat/ləğv tarixlərini daxil etmək |
| Fəaliyyət növləri üzrə giriş/çıxışın uzun zaman sırası | hər qrup üzrə yalnız 5 illik müşahidə (2019–2024, 2021 yoxdur); testlərin gücü aşağıdır | DSK-nın arxiv versiyaları (4-cü hissə) | versiyalar arasında tərif dəyişib ("yeni yaradılmış" → "yeni qeydiyyatdan keçmiş") | DSK-dan 006 və 2_1 cədvəllərinin 2010–2025 sırasını vahid versiyada istəmək |
| Müəssisə xərcləri (satışın maya dəyəri, əməliyyat xərcləri) | müəssisə qiymət-xərc marjası və ya Boone indikatoru yoxdur | milli hesablardan bölmə üzrə PCM proksisi | aqreqat PCM kapital gəlirini renta ilə qarışdırır | FR10 Vergi Xidməti panelini firm_id ilə birləşdirmək və ya reyestr çıxarışına xərc sahələri əlavə etmək |
| Sahələr üzrə idxalın nüfuzu | idxal rəqabəti ssenariləri daxili payın kalibrləməsini tələb edir | ədəbiyyatdakı kənar paylar; FR1/FR5 aqreqat idxalı | sahəyə xas deyil | Dövlət Gömrük Komitəsindən HS × NACE uyğunluq cədvəli |
| Dar məhsul bazarları | fəaliyyət qrupları məhsul bazarlarında konsentrasiyanı azaldılmış göstərir | FR10 məhsul yerləşmə payları; lisenziya növləri | qismən əhatə | məhsul səviyyəli məlumat üçün prioritet bazarları razılaşdırmaq (yanacaq, sement, telekom, əczaçılıq, pərakəndə şəbəkələr) |
| NACE üzrə lisenziyalar və yoxlamalar | maneə proksiləri lisenziya növünə görə qruplara uyğunlaşdırılıb | 24 lisenziya növünün 11 qrupa uyğunlaşdırılması (5-ci hissə) | bir neçə növ sahələrarasıdır | NACE kodları ilə lisenziya və yoxlama reyestrlərini istəmək |
| DVX mikro vergi ödəyicisi sətirləri | mikro sətirlər büdcə təşkilatlarını təkrarlayır (F8) | mikro ödəyicilər DVX konsentrasiyasından çıxarılıb | iqtisadiyyat üzrə hədd bir qədər şişirdilib | Vergi Xidməti r123–r126 sətirlərini düzəltməlidir |
<!-- /AUTO:gaps -->

## 7. Təqdimat spesifikasiyası — MİİS istifadəçi görünüşləri

<!-- AUTO:pres -->
| görünüş | ad | məzmun | mənbə CSV faylları | yenilənmə |
|---|---|---|---|---|
| V1 | Sahələr üzrə rəqabət idarə paneli | Fəaliyyət qrupları üzrə KPI kartları: giriş, çıxış, dövriyyə, xalis giriş, PCM proksisi, HHI hədləri, erkən xəbərdarlıq balı | FR12_indicators_groups.csv, FR12_concentration_bounds.csv, FR12_early_warning.csv | illik |
| V2 | Proqnoz zolağı ilə giriş/çıxış dinamikası | tarix 2019–2025 və FR1-in üç ssenarisi üzrə 2026–2030, 5–95% zolaqlarla; fəal vahidlərin ehtiyatı | FR12_forecast_entry_exit.csv, FR12_fan_entry_exit.csv | illik |
| V3 | Region × sahə istilik xəritəsi | regionlar (2021–2025) və NACE bölmələri üzrə giriş və çıxış əmsalları; regionlar üzrə proqnozlar | FR12_indicators_regions.csv, FR12_indicators_sections.csv, FR12_forecast_entry_exit.csv (panel = region) | illik |
| V4 | Konsentrasiya hədləri qrafiki | qruplar üzrə HHI və CR4 üçün [aşağı, yuxarı] interval sütunları; 2026–2030 proqnoz hədləri | FR12_concentration_bounds.csv, FR12_concentration_paths.csv | illik |
| V5 | Fərziyyələr paneli olan ssenari simulyatoru | Kurno aləti: giriş, birləşmə, xərc/vergi, idxal, dövlət müəssisəsi ssenariləri; elastiklik intervalları ilə Δqiymət, Δmarja, Δburaxılış, ΔİR, ΔİstR | FR12_scenario_*.csv | tələb əsasında |
| V6 | Erkən xəbərdarlıq siyahısı | sahələr üzrə bayraqlar, ümumi bal, müşahidə siyahısı, "məlumat kifayət deyil" işarələri | FR12_early_warning.csv | illik |
| V7 | Müəssisə səviyyəsində bazar strukturu görünüşü (B qatı) | NACE × region üzrə HHI, CR4/CR8, entropiya, Cini, pay mobilliyi, sağ qalma əyriləri, Boone; reyestr gələnə qədər SİNTETİK su nişanı | FR12_SYNTHETIC_*.csv → FR12_FIRM_*.csv | illik |
<!-- /AUTO:pres -->

## 8. Aqreqat məlumatlardan rəqabət göstəriciləri (A qatı)

Giriş əmsalı = *t* ilində yeni qeydiyyata alınmış (yaradılmış) vahidlər / *t* ilinin sonuna vahidlər × 100 (DSK
konvensiyası); çıxış əmsalı da eyni qaydada qeydiyyatdan çıxarılmalar (ləğvetmələr) üzrə; dövriyyə (churn) = giriş +
çıxış; xalis giriş = giriş − çıxış. Dövlət idarəetməsi (O) və ekstraərazi təşkilatları (U) qeyri-bazar sahələridir və
istisna edilir (F10). **Qiymət-xərc marjasının proksi göstəricisi** istehsal hesabından (əlavə dəyər − işçilərin əməyinin
ödənişi) / buraxılış kimi hesablanır (Collins–Preston); o, kapitalın normal gəlirliliyini renta ilə qarışdırır, buna
görə bazar gücünün səviyyəsi kimi deyil, *dəyişmə* göstəricisi kimi şərh olunur.

Fəaliyyət qrupları üzrə giriş və çıxış (qeydiyyatdan keçmiş sahibkarlıq subyektləri, %):

<!-- AUTO:ind_groups -->
Yeni qeydiyyatlar:

| ad | 2019 | 2020 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| Yerləşdirmə və iaşə | 3 481 | 2 367 | 3 879 | 3 680 | 3 726 |
| Kənd təsərrüfatı | 28 521 | 108 807 | 55 049 | 58 346 | 38 557 |
| Tikinti | 3 844 | 3 885 | 3 126 | 3 032 | 2 670 |
| Təhsil | 1 986 | 1 987 | 2 658 | 2 485 | 2 426 |
| Səhiyyə və sosial xidmətlər | 513 | 740 | 717 | 694 | 424 |
| Sənaye | 2 360 | 2 654 | 3 270 | 3 218 | 3 354 |
| İnformasiya və rabitə | 1 362 | 1 393 | 1 897 | 1 814 | 1 400 |
| Digər sahələr | 34 485 | 13 831 | 16 985 | 17 432 | 15 621 |
| Daşınmaz əmlak | 914 | 568 | 727 | 899 | 944 |
| Ticarət | 19 022 | 15 757 | 20 495 | 20 782 | 17 451 |
| Nəqliyyat | 7 461 | 15 486 | 12 934 | 12 777 | 12 476 |

Giriş əmsalı, %:

| ad | 2019 | 2020 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| Yerləşdirmə və iaşə | 7.73 | 5.11 | 7.64 | 6.82 | 6.51 |
| Kənd təsərrüfatı | 11.43 | 30.85 | 12.46 | 11.71 | 7.31 |
| Tikinti | 13.55 | 10.83 | 7.42 | 6.69 | 5.58 |
| Təhsil | 19.20 | 15.31 | 14.94 | 12.36 | 10.82 |
| Səhiyyə və sosial xidmətlər | 10.36 | 8.52 | 7.11 | 6.54 | 3.93 |
| Sənaye | 7.73 | 7.62 | 8.15 | 7.49 | 7.30 |
| İnformasiya və rabitə | 11.62 | 9.48 | 10.49 | 9.21 | 6.73 |
| Digər sahələr | 14.27 | 6.45 | 7.32 | 7.07 | 6.02 |
| Daşınmaz əmlak | 5.53 | 3.39 | 4.03 | 4.67 | 4.66 |
| Ticarət | 7.26 | 5.78 | 6.81 | 6.55 | 5.28 |
| Nəqliyyat | 7.35 | 12.88 | 9.20 | 8.46 | 7.64 |

Çıxış əmsalı, %:

| ad | 2019 | 2020 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| Yerləşdirmə və iaşə | 1.58 | 1.36 | 4.66 | 1.71 | 1.69 |
| Kənd təsərrüfatı | 5.94 | 2.65 | 5.04 | 0.87 | 1.97 |
| Tikinti | 0.77 | 0.65 | 2.05 | 1.06 | 0.97 |
| Təhsil | 2.16 | 1.81 | 2.33 | 1.87 | 1.47 |
| Səhiyyə və sosial xidmətlər | 1.60 | 1.16 | 2.92 | 1.67 | 1.51 |
| Sənaye | 1.20 | 0.97 | 3.17 | 1.35 | 1.37 |
| İnformasiya və rabitə | 1.31 | 1.11 | 2.35 | 1.34 | 1.22 |
| Digər sahələr | 2.94 | 2.26 | 4.01 | 2.09 | 1.44 |
| Daşınmaz əmlak | 2.23 | 1.94 | 6.20 | 1.85 | 2.49 |
| Ticarət | 1.34 | 1.12 | 3.79 | 1.45 | 1.35 |
| Nəqliyyat | 2.86 | 2.74 | 5.71 | 2.49 | 1.89 |
<!-- /AUTO:ind_groups -->

NACE bölmələri üzrə statistik vahidlər, tam illər (reyestr axınları, %):

<!-- AUTO:ind_sections -->
| sec | ad | giriş 2021 | giriş 2024 | giriş 2025 | çıxış 2021 | çıxış 2024 | çıxış 2025 |
|---|---|---|---|---|---|---|---|
| A | Kənd, meşə və balıqçılıq təsərrüfatı | 3.89 | 4.14 | 2.91 | 0.37 | 0.19 | 0.24 |
| B | Mədənçıxarma sənayesi | 4.57 | 4.55 | 4.04 | 0.30 | 0.62 | 0.52 |
| C | Emal sənayesi | 9.38 | 9.64 | 8.13 | 0.18 | 0.29 | 0.20 |
| D | Elektrik enerjisi, qaz və buxar istehsalı | 3.79 | 5.20 | 9.42 | 0.58 | 0.00 | 0.22 |
| E | Su təchizatı, tullantıların təmizlənməsi | 15.16 | 6.35 | 7.02 | 0.89 | 0.53 | 5.65 |
| F | Tikinti | 7.38 | 4.56 | 4.99 | 0.18 | 0.26 | 0.15 |
| G | Ticarət, nəqliyyat vasitələrinin təmiri | 9.91 | 8.69 | 6.94 | 0.28 | 0.15 | 0.13 |
| H | Nəqliyyat və anbar təsərrüfatı | 13.95 | 11.77 | 11.62 | 0.24 | 0.27 | 0.28 |
| I | Turistlərin yerləşdirilməsi və ictimai iaşə | 7.78 | 11.28 | 9.53 | 0.19 | 0.16 | 0.19 |
| J | İnformasiya və rabitə | 12.17 | 8.82 | 8.83 | 0.36 | 0.19 | 0.20 |
| K | Maliyyə və sığorta fəaliyyəti | 8.32 | 7.37 | 6.91 | 0.19 | 2.65 | 0.30 |
| L | Daşınmaz əmlak | 6.05 | 5.76 | 7.11 | 0.38 | 0.59 | 0.42 |
| M | Peşə, elmi və texniki fəaliyyət | 9.30 | 8.98 | 9.32 | 0.29 | 0.50 | 0.42 |
| N | İnzibati və yardımçı xidmətlər | 7.10 | 7.69 | 9.23 | 0.24 | 0.12 | 0.19 |
| P | Təhsil | 7.77 | 8.02 | 8.66 | 0.26 | 1.21 | 0.35 |
| Q | Əhaliyə səhiyyə və sosial xidmətlərin göstərilməsi | 10.75 | 5.77 | 4.83 | 0.23 | 0.34 | 0.39 |
| R | İncəsənət, əyləncə və istirahət | 5.52 | 8.91 | 9.00 | 0.35 | 0.49 | 0.54 |
| S | Digər xidmət fəaliyyətləri | 1.75 | 2.01 | 1.82 | 0.30 | 0.28 | 0.25 |
<!-- /AUTO:ind_sections -->

<!-- AUTO:ind_other -->
Regionlar: giriş 1,7–22,1%, çıxış 0,00–4,69% (2021–2025); regional giriş əmsalının variasiya əmsalı 0,59 (2021) → 0,49 (2025); vahidlərin regionlar üzrə HHI-ı 4573. Emal sənayesində sahə paylarının qeyri-sabitliyi ildə 7,3 f.b. (2006–15), müqayisədə 5,4 f.b. (2016–25). Verilmiş lisenziyalar 1543 (2016) → 1785 (2025) — giriş göstəricisi. Yoxlamalar zaman üzrə müqayisəli deyil (F18: əhatə 2020–2022 dövründə genişləndirilib).

Qruplar üzrə qiymət-xərc marjasının proksi göstəricisi, buraxılışın %-i:

| qrup | 2015 | 2019 | 2022 | 2024 | 2025 |
|---|---|---|---|---|---|
| ACC | 57.70 | 52.80 | 48.80 | 50.40 | 50.70 |
| AGR | 51.70 | 45.70 | 42.90 | 37.60 | 37.10 |
| CON | 38.40 | 30.80 | 28.50 | 28.40 | 27.60 |
| EDU | 20.50 | 4.30 | 6.40 | 8.80 | 6.10 |
| HEA | 41.80 | 20.60 | 15.90 | 12.00 | 11.70 |
| ICT | 49.00 | 47.00 | 42.50 | 43.10 | 42.50 |
| IND | 60.30 | 64.20 | 74.40 | 61.90 | 58.50 |
| OTH | 42.90 | 19.50 | 19.20 | 20.90 | 20.00 |
| REA | 75.80 | 73.00 | 70.50 | 70.60 | 71.20 |
| TRA | 52.30 | 46.70 | 51.20 | 47.70 | 47.30 |
| TRD | 46.80 | 44.40 | 46.30 | 45.20 | 45.50 |

Kohort ölçüsü nisbəti (eyni ildə k yaşlı fəal KOS-lar / 1 yaşlılar — kohortun ölçüsünü və sağ qalmanı qarışdırır; sağ qalma əmsalı **deyil**):

| qrup | il | S2 | S3 | S4 | S5 |
|---|---|---|---|---|---|
| ACC | 2023 | 1.53 | 1.49 | 1.58 | 1.34 |
| ACC | 2024 | 1.74 | 1.44 | 1.32 | 1.44 |
| AGR | 2023 | 2.05 | 1.67 | 2.05 | 1.75 |
| AGR | 2024 | 1.94 | 1.89 | 1.62 | 1.92 |
| CON | 2023 | 1.85 | 1.66 | 1.63 | 1.62 |
| CON | 2024 | 1.99 | 1.80 | 1.67 | 1.64 |
| EDU | 2023 | 1.71 | 1.47 | 1.67 | 1.61 |
| EDU | 2024 | 1.63 | 1.54 | 1.29 | 1.50 |
| HEA | 2023 | 2.14 | 1.78 | 1.91 | 1.70 |
| HEA | 2024 | 2.01 | 2.19 | 1.79 | 1.91 |
| ICT | 2023 | 1.81 | 1.58 | 1.59 | 1.48 |
| ICT | 2024 | 1.85 | 1.77 | 1.50 | 1.48 |
| IND | 2023 | 1.97 | 1.92 | 1.89 | 1.62 |
| IND | 2024 | 1.77 | 1.61 | 1.60 | 1.54 |
| OTH | 2023 | 1.71 | 1.60 | 1.85 | 1.71 |
| OTH | 2024 | 1.82 | 1.58 | 1.46 | 1.72 |
| REA | 2023 | 1.58 | 1.79 | 1.45 | 1.48 |
| REA | 2024 | 1.77 | 1.61 | 1.55 | 1.41 |
| TRA | 2023 | 1.78 | 1.62 | 1.65 | 1.50 |
| TRA | 2024 | 1.77 | 1.59 | 1.43 | 1.44 |
| TRD | 2023 | 1.71 | 1.53 | 1.68 | 1.50 |
| TRD | 2024 | 1.87 | 1.64 | 1.44 | 1.58 |
<!-- /AUTO:ind_other -->

## 9. Ölçü qrupları üzrə məlumatlardan konsentrasiya hədləri

Müəssisə məlumatları olmadan HHI və CR4 müşahidə olunmur, lakin dərc olunan məlumatlarla **məhdudlaşdırılır**. Tutaq
ki, *c* ölçü qrupunda ümumi buraxılış payı $S_c$ olan $n_c$ müəssisə var; hər KOS qrupunun bir müəssisəyə düşən yuxarı
həddi $u_c$ = onun qanunvericilikdə müəyyən edilmiş gəlir həddinin (mikro 0,2, kiçik 3, orta 30 mln manat) bazar
buraxılışına nisbətidir.

- **Aşağı hədd.** Qrupun cəmi sabit olduqda $\sum_i s_i^2$ bərabər paylarda minimuma çatır: $HHI \ge \sum_c S_c^2/n_c$;
  $CR4_{low}$ belə bölgüdə dörd ən böyük payın cəmidir.
- **Yuxarı hədd (əsas göstərici).** $\sum_i s_i^2$ qabarıq funksiyadır, buna görə $\{0 \le s_i \le u_c, \sum_{i\in c} s_i = S_c\}$
  çoxluğunda onun maksimumu təpə nöqtəsindədir: $\lfloor S_c/u_c\rfloor$ müəssisə həddə, biri isə qalıqla. İri
  müəssisələr qrupunun həddi yoxdur, buna görə onun töhfəsi ən çoxu $S_L^2$-dir: bir iri müəssisə bütün qrupun payına
  sahibdir, digərləri isə cüzi gəlirlə **məşğulluğa görə** (> 250) iridir — qanunvericilikdəki tərif
  "işçilərin sayı > 250 **və ya** gəlir > 30 mln manat" olduğundan bu istisna edilə bilməz. $CR4_{up}$ uyğun təpə nöqtəsidir ($S_L$ və
  həddə çatan üç ən böyük müəssisə), beləliklə CR4 və HHI üzrə yuxarı hədlər eyni ekstremal bölgünü təsvir edir.
- **Fərziyyəyə əsaslanan variant.** Hər iri müəssisə **gəlirə görə** iridirsə (gəlir ≥ *f* aşağı həddi), yuxarı hədlər
  $(S_L-(n_L-1)f)^2+(n_L-1)f^2$ və $CR4 \le S_L-(n_L-4)f$ olur (ticarət: *f* = 30 mln manat olduqda 33,8% əvəzinə
  CR4 ≤ 4,2%). Bu, həssaslıq kimi *f* = 30 və 15 mln manat ilə göstərilən **fərziyyədir** və əsas göstərici deyil.

Saylar: qruplar və fəaliyyət növləri üzrə fəal KOS-lar (sahibkarlıq `005`, buraxılış payları `012` ilə eyni məcmu);
iri vahidlər reyestrdən (`1_3`). KOS-un nəzərdə tutulan orta gəliri öz qrupunun həddini aşdıqda (`012` cədvəlinin və
milli hesabların buraxılış bazası fərqlidir, F15) həmin qrup üçün hədlər **bütün illərdə** ləğv edilir (hər qrup üçün
bir rejim, beləliklə §14-dəki proqnozlaşdırılan hədlər fasiləsiz dəyişir; `caps_used = no`). "Bazar" fəaliyyət qrupudur
— antiinhisar bazarından xeyli genişdir — buna görə bu hədlər dar məhsul bazarlarında konsentrasiyanı azaldılmış
göstərir.

<!-- AUTO:bounds -->
| qrup | market_output_mn | n_large | large_share | caps_used | hhi_lower | hhi_upper | cr4_lower | cr4_upper | hhi_upper_floor30 | cr4_upper_floor30 | hhi_upper_floor15 | cr4_upper_floor15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AGR | 14220.20 | 32.00 | 40.70 | xeyr | 60.80 | 3249.90 | 5.10 | 100.00 | 2761.70 | 93.50 | 2994.80 | 96.70 |
| IND | 64971.20 | 237.00 | 89.20 | bəli | 33.60 | 7957.00 | 1.50 | 89.30 | 6132.20 | 78.40 | 7014.80 | 83.80 |
| CON | 20434.80 | 106.00 | 63.00 | bəli | 38.60 | 3972.70 | 2.40 | 63.40 | 2270.30 | 48.00 | 3061.60 | 55.50 |
| TRD | 20988.50 | 208.00 | 33.40 | bəli | 5.70 | 1118.30 | 0.60 | 33.80 | 21.50 | 4.20 | 350.00 | 18.80 |
| TRA | 14072.00 | 57.00 | 80.70 | bəli | 114.50 | 6513.90 | 5.70 | 81.30 | 4732.00 | 69.40 | 5586.70 | 75.10 |
| ACC | 4639.30 | 25.00 | 21.20 | bəli | 22.20 | 464.80 | 3.40 | 23.10 | 57.60 | 7.60 | 198.50 | 14.40 |
| ICT | 3781.60 | 34.00 | 63.40 | bəli | 121.60 | 4037.20 | 7.50 | 65.80 | 1423.80 | 39.60 | 2553.90 | 51.50 |
| REA | 5697.30 | 14.00 | 46.50 | bəli | 163.10 | 2175.70 | 13.30 | 48.10 | 1589.50 | 41.20 | 1870.00 | 43.90 |
| EDU | 5471.40 | 19.00 | 13.90 | xeyr | 12.70 | 5484.10 | 2.90 | 100.00 | 5312.60 | 90.10 | 5372.60 | 95.10 |
| HEA | 4692.40 | 56.00 | 29.70 | xeyr | 26.80 | 2849.10 | 2.10 | 100.00 | — | — | 2119.50 | 82.40 |
| OTH | 14489.00 | 130.00 | 47.60 | bəli | 18.70 | 2270.40 | 1.50 | 48.20 | 446.60 | 21.50 | 1178.80 | 34.60 |

Vergi ödəyicilərinin ölçü qrupları (DVX, mikro istisna olmaqla — F8):

| il | large_count | large_turnover_share | hhi_lower | turnover_per_large_mn | receipts_share_large |
|---|---|---|---|---|---|
| 2022.00 | 846.00 | 69.28 | 5.80 | 84.76 | 72.78 |
| 2023.00 | 927.00 | 68.32 | 5.15 | 86.63 | 76.31 |
| 2024.00 | 985.00 | 68.23 | 4.84 | 88.52 | 73.28 |
| 2025.00 | 1026.00 | 68.50 | 4.68 | 88.17 | 70.78 |
<!-- /AUTO:bounds -->

## 10. Avtoreqressiyanın qadağan olunması məhdudiyyəti

<!-- AUTO:noar -->
| konstruksiya | forma | niyə avtoreqressiya deyil | rol |
|---|---|---|---|
| Fəal vahidlərin ehtiyatı N(t) | N(t) = (N(t−1) + doğulmalar(t)) / (1 + çıxış əmsalı(t)), yəni N(t) = N(t−1) + B(t) − D(t), D ilin sonundakı ehtiyat üzrə | mühasibat eyniliyi (FR1-in kapital ehtiyatı kimi): doğulmalar və çıxış əmsalı struktur proqnozlaşdırılır, ehtiyat onların cəmidir | eynilik |
| Giriş əmsalı | doğulmalar(t) / N(t) | doğulma proqnozundan və eynilik ehtiyatından alınır; heç vaxt öz keçmişi üzrə modelləşdirilmir | eynilik |
| Son qalığa ankerləmə (düzəliş əmsalı) | proqnoz = model + (y_son − qiymətləndirilmiş_son); son müşahidəyə çəki 1 (kombinasiyada 0.5) | FR1–FR10 düzəliş əmsalı konvensiyası: son qalıq sabit saxlanılır, dinamika qiymətləndirilmir; hər qaydanın təsadüfi gəzişmə çəkisi 12-ci hissədə verilir | model |
| Tərif qırılması və impulslar | brk = 1 (2022-dən; 006 tərif dəyişikliyi); 2022 çıxış impulsu | deterministik dummy-lər, gecikmələr deyil | model |
| Sektor tələbinin artımı Δln ƏDV(t) | FR1 sürücüsünün artım tempi | asılı dəyişənin deyil, ekzogen sürücünün çevrilməsi | sürücü |
| Birinci fərqlər üzrə uyğunluq yoxlaması | Δgiriş(t) Δsürücülər(t) üzrə | yalnız diaqnostika: proqnoz heç vaxt gecikmiş əmsaldan istifadə etmir | diaqnostika |
| Təsadüfi gəzişmə müqayisə modeli | giriş(t+h) = giriş(t) | yalnız müqayisə modeli (NFR1 tələbi); heç vaxt proqnoz kimi istifadə olunmur | müqayisə modeli |
| Sabit (orta) əmsal müqayisə modeli / sıfır model | qiymətləndirmə pəncərəsi üzrə vahid ortası | vahidin sabit effektinin özü: dinamika deyil, səviyyə | müqayisə modeli / kombinasiya tərəfdaşı |
| Vahid sabit effektləri | a_i təlim pəncərəsində qiymətləndirilir | zamandan asılı olmayan sabitlər, dinamika yoxdur | model |
| Qeyri-müəyyənlik zolaqları | tarixi qalıq cütləri e_h = w(u_{s+h} − u_s) + (1 − w)u_{s+h}, vahidlər və tənliklər üzrə birgə; parametr çəkilişləri; FR1 çəkilişləri | yenidən seçilmiş tarixi xətalar; qalıq AR qiymətləndirilmir və tətbiq olunmur | zolaqlar |
| Sintetik reyestr (B qatı) | müəssisə ölçüsü bəyan edilmiş məlumat yaratma prosesi ilə dəyişir | yalnız test məlumatı; mühərrik dinamik model qiymətləndirmir | test məlumatı |
<!-- /AUTO:noar -->

## 11. Giriş və çıxışın struktur modeli

İki panel zaman ölçüsünə malikdir: **fəaliyyət paneli** (11 qrup × 2019, 2020, 2022, 2023, 2024; qeydiyyatdan keçmiş
sahibkarlıq subyektləri) və **regional panel** (14 region × 2021–2025; statistik vahidlər).

**Giriş axın kimi modelləşdirilir.** Yeni qeydiyyatların (yaradılmaların) loqarifmi vahid sabit effektləri ilə və
gecikmiş asılı dəyişən olmadan: $\ln B_{it} = a_i + \sum_k b_k x_{k,it} + \delta\,\mathrm{brk}_t + u_{it}$; giriş
*əmsalı* isə ehtiyat-axın eyniliyindən alınır: $e_t = B_t/N_t$, burada $N_t = (N_{t-1}+B_t)/(1+x_t)$. Buna görə
doğulmalar eyni sürətlə artmadıqca ehtiyat artdıqca əmsal azalır — sabit vahid ortası olan əmsal modeli bunu təkrarlaya
bilməz (yoxlamada aşkar edilən artefakt: sabit 2019–2024 orta əmsalı azalan son əmsallardan xeyli yuxarıda idi).
**Çıxış** əmsal modeli olaraq qalır (ölümlər ehtiyatla mütənasib dəyişir). Fəaliyyət paneli: 2022-ci ildən `brk` = 1
006 cədvəlində DSK tərifinin dəyişməsini əks etdirir (2020-ci ilədək "yeni yaradılmış / ləğv edilmiş" → 2022-ci ildən
"yeni qeydiyyata alınmış / qeydiyyatdan çıxarılmış", F17); çıxış tənliyi 2022-ci il impulsunu daşıyır (F16), çünki
2023–2024-cü illərdə çıxış səviyyələri 2019–2020-ci illərə yaxındır və davamlı qırılma görünmür. Kənd təsərrüfatında
2020-ci il qeydiyyat dalğası (F7) istisna edilir.

Namizəd sürücülər — fəaliyyət üzrə: sektor tələbinin artımı (qrupun sektorunun FR1 üzrə real əlavə dəyəri), sektorun
ölçüsü (real əlavə dəyərin loqarifmi), kredit faiz dərəcəsi, real kredit artımı (FR1) və qrupun qiymət-xərc marjası
proksi göstəricisi; region üzrə: regional sənaye buraxılışının artımı və ölçüsü (FR10), qeyri-neft ÜDM-in artımı və
kredit faiz dərəcəsi (FR1). Milli sürücülər yalnız zamana görə dəyişir, buna görə il effektləri əlavə edilə bilməz.
Beş illə Driscoll–Kraay p-dəyərləri etibarsızdır və göstərilmir; cədvəl **klaster wild bootstrap** p-dəyərini verir
(illər üzrə, Webb çəkiləri, sıfır fərziyyə qoyulmaqla, B = 499) — beş klasterlə bu kobud qiymətdir. Qiymətlər təsviri
xarakter daşıyır.

<!-- AUTO:fe -->
| panel | asılı dəyişən | spesifikasiya | sürücü | əmsal | se_DK | wcb_p | T | n |
|---|---|---|---|---|---|---|---|---|
| fəaliyyət | lnB | FE + size | size | 0.19 | 0.20 | 0.42 | 5 | 54 |
| fəaliyyət | lnB | FE + dem | dem | 0.00 | 0.00 | 0.24 | 5 | 54 |
| fəaliyyət | lnB | FE + size + dem | size | -0.02 | 0.31 | 0.94 | 5 | 54 |
| fəaliyyət | lnB | FE + size + dem | dem | 0.00 | 0.00 | 0.41 | 5 | 54 |
| fəaliyyət | lnB | FE + size + lend | size | 0.21 | 0.19 | 0.41 | 5 | 54 |
| fəaliyyət | lnB | FE + size + lend | lend | -0.12 | 0.09 | 0.40 | 5 | 54 |
| fəaliyyət | lnB | FE + size + cred | size | 0.25 | 0.20 | 0.40 | 5 | 54 |
| fəaliyyət | lnB | FE + size + cred | cred | -0.00 | 0.00 | 0.48 | 5 | 54 |
| fəaliyyət | lnB | FE + dem + lend | dem | 0.00 | 0.00 | 0.16 | 5 | 54 |
| fəaliyyət | lnB | FE + dem + lend | lend | -0.13 | 0.07 | 0.35 | 5 | 54 |
| fəaliyyət | lnB | FE + pcm | pcm | 0.01 | 0.01 | 0.18 | 5 | 54 |
| fəaliyyət | lnB | FE + size + pcm | size | 0.04 | 0.22 | 0.80 | 5 | 54 |
| fəaliyyət | lnB | FE + size + pcm | pcm | 0.01 | 0.01 | 0.27 | 5 | 54 |
| fəaliyyət | çıxış | FE + dem | dem | 0.01 | 0.00 | 0.17 | 5 | 55 |
| fəaliyyət | çıxış | FE + dem + pcm | dem | 0.01 | 0.00 | 0.32 | 5 | 55 |
| fəaliyyət | çıxış | FE + dem + pcm | pcm | 0.02 | 0.01 | 0.19 | 5 | 55 |
| fəaliyyət | çıxış | FE + dem + cred | dem | 0.01 | 0.00 | 0.08 | 5 | 55 |
| fəaliyyət | çıxış | FE + dem + cred | cred | -0.01 | 0.01 | 0.47 | 5 | 55 |
| fəaliyyət | çıxış | FE + lend | lend | 0.10 | 0.05 | 0.32 | 5 | 55 |
| fəaliyyət | çıxış | FE + cred | cred | -0.00 | 0.01 | 0.87 | 5 | 55 |
| fəaliyyət | çıxış | FE + size | size | -0.12 | 0.52 | 0.85 | 5 | 55 |
| region | lnB | FE + reg | reg | -0.00 | 0.00 | 0.74 | 5 | 70 |
| region | lnB | FE + size | size | 0.27 | 0.03 | 0.04 | 5 | 70 |
| region | lnB | FE + reg + size | reg | -0.00 | 0.00 | 0.18 | 5 | 70 |
| region | lnB | FE + reg + size | size | 0.33 | 0.04 | 0.05 | 5 | 70 |
| region | lnB | FE + non | non | -0.06 | 0.01 | 0.04 | 5 | 70 |
| region | lnB | FE + non + lend | non | -0.06 | 0.01 | 0.29 | 5 | 70 |
| region | lnB | FE + non + lend | lend | -0.11 | 0.04 | 0.06 | 5 | 70 |
| region | lnB | FE + reg + lend | reg | 0.00 | 0.00 | 0.89 | 5 | 70 |
| region | lnB | FE + reg + lend | lend | -0.13 | 0.05 | 0.33 | 5 | 70 |
| region | çıxış | FE + reg | reg | 0.00 | 0.00 | 0.81 | 5 | 70 |
| region | çıxış | FE + size | size | -0.10 | 0.05 | 0.30 | 5 | 70 |
| region | çıxış | FE + reg + size | reg | 0.00 | 0.00 | 0.57 | 5 | 70 |
| region | çıxış | FE + reg + size | size | -0.12 | 0.06 | 0.28 | 5 | 70 |
| region | çıxış | FE + non | non | -0.06 | 0.01 | 0.06 | 5 | 70 |
| region | çıxış | FE + non + lend | non | -0.06 | 0.01 | 0.20 | 5 | 70 |
| region | çıxış | FE + non + lend | lend | -0.04 | 0.01 | 0.09 | 5 | 70 |
| region | çıxış | FE + reg + lend | reg | 0.00 | 0.00 | 0.31 | 5 | 70 |
| region | çıxış | FE + reg + lend | lend | -0.06 | 0.03 | 0.39 | 5 | 70 |
<!-- /AUTO:fe -->

## 12. Kəsimdən əvvəl seçim, toxunulmaz nümunədən kənar yoxlama və hər iki müqayisə meyarı (NFR1)

**Qayda** prosedurdur — sürücülər dəsti, lövbərləmə, rejim (struktur / sıfır model ilə kombinasiya / sıfır model) və
uyğunluq filtri — hər başlanğıcda həmin başlanğıcadək olan məlumatlar üzrə yenidən tətbiq olunur. Nümunədən kənar
yoxlama və proqnoz **eyni prosedurdan** istifadə edir, buna görə proqnoz məhz yoxlanılmış qaydadır (nümunədən kənar
yoxlamadan sonra heç bir ehtiyat variant əlavə edilmir).

- **Seçim** (yalnız ≤ 2022 məlumatları): ≤ 2022 illəri üzrə qiymətləndirilir, 2023 üzrə dəyərləndirilir. Namizədlər:
  hər sürücülər dəsti, lövbərlənməmiş (sabit effekt səviyyəsi) və ya son qalığa lövbərlənmiş (FR1–FR10-un düzəliş
  əmsalı konvensiyası). Ən yaxşı namizəd itkisi daha aşağı olduqda və vahidlər üzrə cütləşdirilmiş test bərabər
  dəqiqliyi 10% səviyyəsində rədd etdikdə sıfır modeli əvəz edir; itki daha aşağı, lakin fərq əhəmiyyətsiz olduqda
  proqnoz sıfır model ilə bərabər çəkili kombinasiyadır; əks halda sıfır model götürülür. Lövbərlənmiş sıfır model
  təsadüfi gəzişmənin özüdür və həmin müqayisə meyarı kimi göstərilir; hər qaydanın **son müşahidəyə nəzərdə tutulan
  çəkisi** göstərilir (lövbərlənmiş qayda üçün 1, lövbərlənmiş model ilə sıfır modelin kombinasiyası üçün 0,5, digər
  hallarda 0). Kəsimdən əvvəlki iki-üç il ilə vahidlərə xas meyllərin büzülməsi identifikasiya olunmur: kəsimdən əvvəl
  müəyyən edilmiş birləşdirilmiş meyllər (κ = 0).
- **Uyğunluq qaydası**: within meyli birinci fərqlər üzrə qiymətinin 95% etibarlılıq intervalından kənarda qalan sürücü
  çıxarılır — yalnız təlim məlumatlarında hər vahid üzrə ən azı iki keçid olduqda tətbiq olunur. Bir keçid olduqda
  (2022 başlanğıcında regional panel) yoxlama mənasızdır və keçmiş kimi deyil, **tətbiq edilməmiş** kimi qeyd olunur.
- **Nümunədən kənar yoxlama** (heç vaxt seçim üçün istifadə olunmur): fəaliyyət — 2022 və 2023 başlanğıcları, hədəf
  2024; region — 2023 (hədəflər 2024, 2025) və 2024 (hədəf 2025) başlanğıcları. FR1/FR10-un reallaşmış sürücüləri
  (FR10-da olduğu kimi şərti proqnozlar); hər sabit hər başlanğıcda yenidən qiymətləndirilir. Giriş **əmsalı** başlanğıcdakı
  ehtiyatdan başlayaraq proqnozlaşdırılan doğulmalardan və çıxış qaydasının proqnozlaşdırdığı ölümlərdən eynilik
  vasitəsilə qurulur (heç bir reallaşmış endogen nəticə daxil olmur). Müqayisə meyarları: təsadüfi gəzişmə (son
  müşahidə olunan dəyər) və sabit (təlim illəri üzrə vahidin ortası). DM/HLN: bir və ya iki hədəf ili ilə hədəf illəri
  üzrə test mümkün deyil, buna görə test **vahidlər üzrə cütləşdirilir** (itkilər üst-üstə düşən başlanğıclar üzrə
  vahidlərə görə orta hesablanır); o, ümumi il şoklarını nəzərə almır və p-dəyərləri yalnız göstərici xarakter daşıyır.

<!-- AUTO:select -->
| panel | asılı dəyişən | qayda | best_candidate | dm_p_vs_null | implied_rw_weight | train_years | applied_at_last_origin |
|---|---|---|---|---|---|---|---|
| fəaliyyət | lnB | kombinasiya: FE + dem / lövbərlənmiş | struktur: FE + dem / lövbərlənmiş | 0.17 | 0.50 | 3 | dem |
| fəaliyyət | çıxış | sıfır model (FE + sabit hədlər) | struktur: FE + dem + pcm | 0.83 | 0.00 | 3 | sürücü yoxdur (sıfır model) |
| region | lnB | kombinasiya: FE + reg + lend / lövbərlənmiş | struktur: FE + reg + lend / lövbərlənmiş | 0.12 | 0.50 | 2 | reg, lend |
| region | çıxış | kombinasiya: FE + non / lövbərlənmiş | struktur: FE + non / lövbərlənmiş | 0.13 | 0.50 | 2 | non |
| sme | lo | kombinasiya: FE + size | struktur: FE + size | 0.56 | 0.00 | 3 | bax Hissə 14 |
<!-- /AUTO:select -->

Uyğunluq yoxlamaları (struktur qaydanın tətbiq olunduğu hər başlanğıc):

<!-- AUTO:coh -->
| açar | mənşə | sürücü | fe | fd | fd_lo | fd_hi | keçidlər | vəziyyət |
|---|---|---|---|---|---|---|---|---|
| ('activity', 'lnB') | 2022 | size | 0.48 | 0.39 | 0.16 | 0.63 | 2.00 | uyğundur |
| ('activity', 'lnB') | 2022 | dem | 0.00 | 0.00 | 0.00 | 0.01 | 2.00 | uyğundur |
| ('activity', 'lnB') | 2022 | lend | -0.06 | -0.19 | -3.30 | 2.92 | 2.00 | uyğundur |
| ('activity', 'lnB') | 2022 | cred | -0.00 | -0.00 | -0.03 | 0.02 | 2.00 | uyğundur |
| ('activity', 'lnB') | 2022 | pcm | 0.01 | 0.01 | -0.00 | 0.03 | 2.00 | uyğundur |
| ('activity', 'exit') | 2022 | dem | 0.01 | 0.01 | 0.00 | 0.01 | 2.00 | uyğundur |
| ('activity', 'exit') | 2022 | pcm | 0.01 | 0.01 | -0.03 | 0.04 | 2.00 | uyğundur |
| ('activity', 'exit') | 2022 | cred | 0.03 | 0.04 | -0.01 | 0.08 | 2.00 | uyğundur |
| ('activity', 'exit') | 2022 | lend | 5.47 | 5.47 | -0.18 | 11.11 | 2.00 | uyğundur |
| ('activity', 'exit') | 2022 | size | 0.77 | 0.77 | -0.35 | 1.90 | 2.00 | uyğundur |
| ('region', 'lnB') | 2022 | reg | — | — | — | — | — | tətbiq olunmayıb (boş: hər vahiddə 1 keçid) |
| ('region', 'lnB') | 2022 | size | — | — | — | — | — | tətbiq olunmayıb (boş: hər vahiddə 1 keçid) |
| ('region', 'lnB') | 2022 | non | — | — | — | — | — | tətbiq olunmayıb (boş: hər vahiddə 1 keçid) |
| ('region', 'lnB') | 2022 | lend | — | — | — | — | — | tətbiq olunmayıb (boş: hər vahiddə 1 keçid) |
| ('region', 'exit') | 2022 | reg | — | — | — | — | — | tətbiq olunmayıb (boş: hər vahiddə 1 keçid) |
| ('region', 'exit') | 2022 | size | — | — | — | — | — | tətbiq olunmayıb (boş: hər vahiddə 1 keçid) |
| ('region', 'exit') | 2022 | non | — | — | — | — | — | tətbiq olunmayıb (boş: hər vahiddə 1 keçid) |
| ('region', 'exit') | 2022 | lend | — | — | — | — | — | tətbiq olunmayıb (boş: hər vahiddə 1 keçid) |
| ('activity', 'lnB') | 2023 | dem | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | uyğundur |
| ('region', 'lnB') | 2023 | reg | -0.00 | 0.00 | -0.01 | 0.01 | 2.00 | uyğundur |
| ('region', 'lnB') | 2023 | lend | -0.13 | -0.12 | -0.18 | -0.05 | 2.00 | uyğundur |
| ('region', 'exit') | 2023 | non | -0.07 | -0.06 | -0.10 | -0.03 | 2.00 | uyğundur |
| ('region', 'lnB') | 2024 | reg | 0.00 | -0.00 | -0.01 | 0.01 | 3.00 | uyğundur |
| ('region', 'lnB') | 2024 | lend | -0.16 | -0.09 | -0.16 | -0.01 | 3.00 | çıxarılıb (uyğunsuz) |
| ('region', 'exit') | 2024 | non | -0.07 | -0.06 | -0.09 | -0.02 | 3.00 | uyğundur |
| ('activity', 'lnB') | 2024 | dem | 0.00 | 0.00 | 0.00 | 0.00 | 4.00 | uyğundur |
| ('region', 'lnB') | 2025 | reg | 0.00 | -0.00 | -0.00 | 0.00 | 4.00 | uyğundur |
| ('region', 'lnB') | 2025 | lend | -0.13 | -0.07 | -0.13 | -0.01 | 4.00 | uyğundur |
| ('region', 'exit') | 2025 | non | -0.06 | -0.05 | -0.09 | -0.00 | 4.00 | uyğundur |
| ('sme', 'lo') | 2022 | dem | 0.01 | 0.01 | 0.01 | 0.01 | 2.00 | uyğundur |
| ('sme', 'lo') | 2022 | size | 0.73 | 1.09 | 0.67 | 1.50 | 2.00 | uyğundur |
| ('sme', 'lo') | 2022 | lend | 0.02 | -0.07 | -0.21 | 0.06 | 2.00 | uyğundur |
| ('sme', 'lo') | 2023 | size | 0.70 | 0.99 | 0.61 | 1.36 | 3.00 | uyğundur |
<!-- /AUTO:coh -->

Nümunədən kənar yoxlamanın nəticələri. `theil_constant_vs_rw` sıfır modelin öz göstəricisidir: fəaliyyət üzrə giriş
əmsalı üçün sabit əmsallı sıfır model təsadüfi gəzişmədən açıq-aydın pisdir, məhz buna görə əmsal artıq sabit orta ilə
modelləşdirilmir.

<!-- AUTO:holdout -->
| panel | göstərici | qayda | implied_rw_weight | n | hədəflər | rmse_rule | rmse_null | rmse_rw | rmse_constant | theil_rule_vs_rw | theil_rule_vs_constant | theil_null_vs_rw | theil_constant_vs_rw | dm_p_rule_vs_rw | dm_p_rule_vs_constant |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fəaliyyət | giriş əmsalı, % (doğulmalar / eynilik ehtiyatı) | kombinasiya: FE + dem / lövbərlənmiş | 0.50 | 22 | 2024 | 1.36 | 1.42 | 2.33 | 3.27 | 0.59 | 0.42 | 0.61 | 1.40 | 0.06 | 0.01 |
| fəaliyyət | log doğulmalar | kombinasiya: FE + dem / lövbərlənmiş | 0.50 | 22 | 2024 | 0.23 | 0.24 | 0.23 | 0.21 | 0.98 | 1.09 | 1.05 | 0.90 | 0.86 | 0.47 |
| fəaliyyət | çıxış əmsalı, % | sıfır model (FE + sabit hədlər) | 0.00 | 22 | 2024 | 0.68 | 0.68 | 1.78 | 1.06 | 0.38 | 0.64 | 0.38 | 0.59 | 0.00 | 0.02 |
| region | giriş əmsalı, % (doğulmalar / eynilik ehtiyatı) | kombinasiya: FE + reg + lend / lövbərlənmiş | 0.50 | 42 | 2024, 2025 | 1.65 | 2.25 | 3.00 | 1.67 | 0.55 | 0.99 | 0.75 | 0.56 | 0.36 | 0.94 |
| region | log doğulmalar | kombinasiya: FE + reg + lend / lövbərlənmiş | 0.50 | 42 | 2024, 2025 | 0.32 | 0.39 | 0.29 | 0.39 | 1.07 | 0.81 | 1.32 | 1.32 | 0.61 | 0.25 |
| region | çıxış əmsalı, % | kombinasiya: FE + non / lövbərlənmiş | 0.50 | 42 | 2024, 2025 | 0.69 | 0.75 | 0.66 | 0.75 | 1.05 | 0.92 | 1.15 | 1.15 | 0.47 | 0.48 |
| sme | KOS buraxılış payının log-odds-u | kombinasiya: FE + size | 0.00 | 22 | 2024 | 0.35 | 0.35 | 0.30 | 0.35 | 1.17 | 1.00 | 1.17 | 1.17 | 0.50 | 0.93 |
<!-- /AUTO:holdout -->

Şərh: giriş əmsalı qaydaları nümunədən kənar yoxlamada (fəaliyyət və regionlar) hər iki müqayisə meyarından üstündür,
çünki doğulmalar sabitdir, ehtiyat isə artır; doğulmaların loqarifmi üzrə fəaliyyət qaydası təsadüfi gəzişməyə yaxındır
və sabitdən bir qədər pisdir, deməli, üstünlük sürücüdən deyil, axın və ehtiyatın birgə modelləşdirilməsindən irəli
gəlir. Çıxış: fəaliyyət üzrə sıfır model hər iki müqayisə meyarından üstündür; regional çıxış və KOS payı qaydaları
təsadüfi gəzişmədən üstün deyil. Təsadüfi gəzişmə yalnız müqayisə meyarıdır — son dəyərə görə proqnozlaşdırma
Sifarişçinin istisna etdiyi dəyişənin öz tarixi əsasında proqnozdur.

## 13. FR1-in üç ssenarisi üzrə 2026–2030-cu illər üçün giriş və çıxış proqnozları

Qaydalar son başlanğıcda (fəaliyyət 2024, regionlar 2025) FR1-in ssenari yolları və FR10-un regional buraxılışı ilə
tətbiq olunur; qayda marjanı seçərsə, sənaye marjası yolu FR10-un bölmə proqnozlarından götürülür (cari qaydalar onu
seçmir). Doğulmalar loqarifmik modelin medianıdır; ehtiyat $N_t = (N_{t-1}+B_t)/(1+x_t)$ ilə dəyişir; giriş əmsalı
$B_t/N_t$-dir. Fəaliyyət qrupları üçün 2025-ci il cari qiymətləndirmədir (nowcast; 2025-ci il üzrə 006 hələ dərc
olunmayıb). Zolaqlar: FR1-in Əsas ssenari çəkilişlərini, işarə üzrə rədd etmə ilə meyl çəkilişlərini (sürücü
kənarlaşmalarına təsir edir, buna görə vahid effektləri yenidən uyğunlaşır) və **tarixi xəta cütlərini**
$e_h = w(u_{s+h}-u_s) + (1-w)u_{s+h}$ (w = qaydanın nəzərdə tutduğu təsadüfi gəzişmə çəkisi) birləşdirən 500
təkrarlama; hər üfüq üçün bir cüt, doğulmalar və çıxış üçün və bütün vahidlər üçün eyni, mərkəzləşdirilmiş. Hər üfüq
üçün cəmi 1–4 tarixi cüt mövcuddur (aşağıda göstərilir), buna görə zolaqların eni kobuddur. İki yaxın tarixi cütün
üfüqlə daralan zolaq yaratmasının qarşısını almaq üçün (v2.0-da 2027-ci il üçün belə olmuşdu) xəta dəsti əvvəlki
üfüqdəkindən (doğulmalar və ya çıxış üzrə) az səpələnmiş olan üfüq əvvəlki üfüqün dəstindən hər iki tənlik üçün birgə
istifadə edir (v2.1). Beləliklə, tarixi xəta dəsti üfüqlə heç vaxt daha az səpələnmiş olmur və kəskin daralmalar
(məsələn, 2026–2028-ci illərdə doğulmalar proqnozun 32% → 9% → 19%-i) aradan qalxıb; axın və əmsal zolaqları FR1
sürücü çəkilişləri və ehtiyat eyniliyi vasitəsilə yenə də tədricən darala bilər.

<!-- AUTO:forecast -->
| panel | il | N Mənfi | N Əsas | N İslahat | giriş Mənfi | giriş Əsas | giriş İslahat | çıxış Mənfi | çıxış Əsas | çıxış İslahat | yeni Mənfi | yeni Əsas | yeni İslahat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fəaliyyət | 2025 | 1 576 172 | 1 576 172 | 1 576 172 | 6.64 | 6.64 | 6.64 | 2.18 | 2.18 | 2.18 | 104 650 | 104 650 | 104 650 |
| fəaliyyət | 2026 | 1 644 900 | 1 644 900 | 1 644 900 | 6.36 | 6.36 | 6.36 | 2.18 | 2.18 | 2.18 | 104 596 | 104 596 | 104 596 |
| fəaliyyət | 2027 | 1 712 363 | 1 712 488 | 1 712 617 | 6.12 | 6.13 | 6.13 | 2.18 | 2.18 | 2.18 | 104 797 | 104 924 | 105 056 |
| fəaliyyət | 2028 | 1 778 373 | 1 778 598 | 1 778 843 | 5.89 | 5.90 | 5.90 | 2.18 | 2.18 | 2.18 | 104 776 | 104 879 | 105 000 |
| fəaliyyət | 2029 | 1 843 040 | 1 843 383 | 1 843 742 | 5.69 | 5.69 | 5.70 | 2.18 | 2.18 | 2.18 | 104 831 | 104 955 | 105 074 |
| fəaliyyət | 2030 | 1 906 314 | 1 906 741 | 1 907 208 | 5.50 | 5.50 | 5.51 | 2.18 | 2.18 | 2.18 | 104 803 | 104 893 | 105 011 |
| region | 2026 | 239 573 | 240 598 | 240 399 | 5.77 | 6.17 | 6.09 | 0.37 | 0.37 | 0.37 | 13 821 | 14 850 | 14 651 |
| region | 2027 | 251 454 | 255 060 | 254 519 | 5.03 | 5.93 | 5.76 | 0.31 | 0.26 | 0.21 | 12 650 | 15 114 | 14 663 |
| region | 2028 | 263 300 | 269 723 | 268 564 | 4.81 | 5.70 | 5.46 | 0.31 | 0.27 | 0.23 | 12 657 | 15 385 | 14 661 |
| region | 2029 | 275 723 | 284 399 | 282 623 | 4.80 | 5.41 | 5.19 | 0.30 | 0.25 | 0.22 | 13 240 | 15 396 | 14 667 |
| region | 2030 | 288 695 | 298 998 | 296 608 | 4.79 | 5.15 | 4.94 | 0.30 | 0.27 | 0.23 | 13 838 | 15 393 | 14 661 |

Əsas ssenari zolaqları (5–95%):

| panel | il | new_baseline | new_p5 | new_p95 | entry_baseline | entry_p5 | entry_p95 | exit_baseline | exit_p5 | exit_p95 | N_baseline | N_p5 | N_p95 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fəaliyyət | 2025 | 104 650 | 95 664 | 122 736 | 6.64 | 6.10 | 7.68 | 2.18 | 1.93 | 2.49 | 1 576 172 | 1 567 558 | 1 597 783 |
| fəaliyyət | 2026 | 104 596 | 95 404 | 122 901 | 6.36 | 5.77 | 7.40 | 2.18 | 1.93 | 2.50 | 1 644 900 | 1 627 805 | 1 687 855 |
| fəaliyyət | 2028 | 104 879 | 95 684 | 123 246 | 5.90 | 5.32 | 6.92 | 2.18 | 1.93 | 2.51 | 1 778 598 | 1 746 269 | 1 834 178 |
| fəaliyyət | 2030 | 104 893 | 95 603 | 123 368 | 5.50 | 4.94 | 6.45 | 2.18 | 1.93 | 2.51 | 1 906 741 | 1 860 171 | 1 975 333 |
| region | 2026 | 14 850 | 13 359 | 16 920 | 6.17 | 5.60 | 6.97 | 0.37 | 0.13 | 0.63 | 240 598 | 238 784 | 243 064 |
| region | 2028 | 15 385 | 12 848 | 19 532 | 5.70 | 4.82 | 7.06 | 0.27 | 0.07 | 0.53 | 269 723 | 264 001 | 277 941 |
| region | 2030 | 15 393 | 13 808 | 18 439 | 5.15 | 4.71 | 5.95 | 0.27 | 0.08 | 0.59 | 298 998 | 292 369 | 311 669 |

Zolaqların qurulması:

| panel | horizon_cap_years | historical_pairs_by_horizon | təkrarlamalar | rw_weight_births | rw_weight_exit |
|---|---|---|---|---|---|
| fəaliyyət | 4 | h1:3, h2:3, h3:3, h4:3, h5:3, h6:3 | 500 | 0.50 | 0.00 |
| region | 3 | h1:4, h2:4, h3:4, h4:4, h5:4 | 500 | 0.50 | 0.50 |
<!-- /AUTO:forecast -->

Giriş əmsalı, doğulmalar, çıxış əmsalı və ehtiyat artımının 2026–2030 orta göstəricilərinin hər vahidin öz tarixinə
qarşı, habelə son faktiki giriş əmsalının 2026-cı il zolağına qarşı **inandırıcılığı**:

<!-- AUTO:plaus -->
İşarələnmiş vahid-dəyişən proqnozları: 37 / 100:

| panel | vahid | dəyişən | forecast_mean_2026_30 | hist_min | hist_max | recent_2obs_mean | işarə |
|---|---|---|---|---|---|---|---|
| fəaliyyət | ACC | ehtiyatın artımı, ildə % | 3.74 | 2.87 | 6.20 | 6.15 | son ortadan 25%-dən çox fərqlənir |
| fəaliyyət | AGR | giriş əmsalı, % | 6.67 | 7.31 | 12.46 | 9.51 | tarixi intervaldan kənar |
| fəaliyyət | AGR | çıxış əmsalı, % | 2.88 | 0.87 | 5.94 | 1.42 | son ortadan 25%-dən çox fərqlənir |
| fəaliyyət | AGR | ehtiyatın artımı, ildə % | 3.95 | 5.86 | 41.30 | 9.35 | tarixi intervaldan kənar |
| fəaliyyət | CON | giriş əmsalı, % | 5.14 | 5.58 | 13.55 | 6.14 | tarixi intervaldan kənar |
| fəaliyyət | CON | çıxış əmsalı, % | 0.68 | 0.65 | 2.05 | 1.01 | son ortadan 25%-dən çox fərqlənir |
| fəaliyyət | CON | ehtiyatın artımı, ildə % | 4.67 | 5.64 | 26.42 | 6.56 | tarixi intervaldan kənar |
| fəaliyyət | EDU | giriş əmsalı, % | 7.99 | 10.82 | 19.20 | 11.59 | tarixi intervaldan kənar |
| fəaliyyət | EDU | ehtiyatın artımı, ildə % | 6.94 | 11.47 | 25.46 | 12.27 | tarixi intervaldan kənar |
| fəaliyyət | ICT | giriş əmsalı, % | 5.84 | 6.73 | 11.62 | 7.97 | tarixi intervaldan kənar |
| fəaliyyət | ICT | çıxış əmsalı, % | 1.05 | 1.11 | 2.35 | 1.28 | tarixi intervaldan kənar |
| fəaliyyət | ICT | ehtiyatın artımı, ildə % | 5.04 | 5.66 | 25.38 | 7.31 | tarixi intervaldan kənar |
| fəaliyyət | IND | giriş əmsalı, % | 5.74 | 7.30 | 8.15 | 7.40 | tarixi intervaldan kənar |
| fəaliyyət | IND | ehtiyatın artımı, ildə % | 4.76 | 6.93 | 14.06 | 7.03 | tarixi intervaldan kənar |
| fəaliyyət | OTH | giriş əmsalı, % | 5.73 | 6.02 | 14.27 | 6.55 | tarixi intervaldan kənar |
| fəaliyyət | OTH | ehtiyatın artımı, ildə % | 3.74 | -11.28 | 6.32 | 5.74 | son ortadan 25%-dən çox fərqlənir |
| fəaliyyət | REA | ehtiyatın artımı, ildə % | 1.59 | 1.41 | 6.65 | 5.96 | son ortadan 25%-dən çox fərqlənir |
| fəaliyyət | TRA | giriş əmsalı, % | 6.42 | 7.35 | 12.88 | 8.05 | tarixi intervaldan kənar |
| fəaliyyət | TRA | ehtiyatın artımı, ildə % | 3.85 | 7.41 | 18.55 | 7.76 | tarixi intervaldan kənar |
| fəaliyyət | TRD | giriş əmsalı, % | 4.81 | 5.28 | 7.26 | 5.92 | tarixi intervaldan kənar |
| fəaliyyət | TRD | ehtiyatın artımı, ildə % | 3.54 | 4.00 | 5.41 | 4.77 | tarixi intervaldan kənar |
| region | Abşeron-Xızı | giriş əmsalı, % | 5.98 | 6.81 | 7.66 | 7.55 | tarixi intervaldan kənar |
| region | Abşeron-Xızı | ehtiyatın artımı, ildə % | 5.98 | 7.61 | 8.23 | 8.13 | tarixi intervaldan kənar |
| region | Bakı şəhəri | giriş əmsalı, % | 6.47 | 7.37 | 11.68 | 7.80 | tarixi intervaldan kənar |
| region | Bakı şəhəri | çıxış əmsalı, % | 0.21 | 0.22 | 0.32 | 0.23 | tarixi intervaldan kənar |
| region | Bakı şəhəri | ehtiyatın artımı, ildə % | 6.51 | 7.66 | 12.83 | 8.15 | tarixi intervaldan kənar |
| region | Şərqi Zəngəzur | giriş əmsalı, % | 6.03 | 4.00 | 12.90 | 10.76 | son ortadan 25%-dən çox fərqlənir |
| region | Şərqi Zəngəzur | doğulmalar | 100.99 | 42.00 | 167.00 | 143.50 | son ortadan 25%-dən çox fərqlənir |
| region | Şərqi Zəngəzur | çıxış əmsalı, % | 0.16 | 0.00 | 0.31 | 0.26 | son ortadan 25%-dən çox fərqlənir |
| region | Şərqi Zəngəzur | ehtiyatın artımı, ildə % | 6.09 | 3.14 | 14.80 | 11.19 | son ortadan 25%-dən çox fərqlənir |
| region | Gəncə-Daşkəsən | giriş əmsalı, % | 3.78 | 3.99 | 4.81 | 4.03 | tarixi intervaldan kənar |
| region | Gəncə-Daşkəsən | ehtiyatın artımı, ildə % | 3.54 | 3.55 | 4.51 | 3.80 | tarixi intervaldan kənar |
| region | Qarabağ | giriş əmsalı, % | 3.86 | 3.12 | 6.37 | 5.59 | son ortadan 25%-dən çox fərqlənir |
| region | Qarabağ | ehtiyatın artımı, ildə % | 3.67 | 3.79 | 6.19 | 5.56 | tarixi intervaldan kənar |
| region | Naxçıvan | giriş əmsalı, % | 6.99 | 2.55 | 22.09 | 10.07 | son ortadan 25%-dən çox fərqlənir |
| region | Naxçıvan | ehtiyatın artımı, ildə % | 3.70 | 2.40 | 27.44 | 7.38 | son ortadan 25%-dən çox fərqlənir |
| region | Şəki-Zaqatala | çıxış əmsalı, % | 0.31 | 0.17 | 0.62 | 0.45 | son ortadan 25%-dən çox fərqlənir |

Son faktiki giriş əmsalı 2026-cı il zolağına qarşı: 27 vahiddən zolaqdan kənarda olanlar 3, hər biri səbəbi ilə:

| panel | vahid | last_year | last_actual_entry | band2026_p5 | band2026_p95 | daxilində | izah |
|---|---|---|---|---|---|---|---|
| fəaliyyət | IND | 2024 | 7.30 | 6.12 | 6.47 | xeyr | 2026-cı ildə doğulmalar 2024-ə nisbətən -4.1%, ehtiyat +11.4%: ehtiyat doğulmalardan sürətlə artır, ona görə əmsal düşür; 2024-cü ilin doğulmaları əvvəlki iki müşahidəyə nisbətən +3% idi |
| fəaliyyət | ACC | 2024 | 6.51 | 5.22 | 6.18 | xeyr | 2026-cı ildə doğulmalar 2024-ə nisbətən -4.0%, ehtiyat +8.8%: ehtiyat doğulmalardan sürətlə artır, ona görə əmsal düşür; 2024-cü ilin doğulmaları əvvəlki iki müşahidəyə nisbətən -1% idi |
| fəaliyyət | EDU | 2024 | 10.82 | 8.92 | 9.18 | xeyr | 2026-cı ildə doğulmalar 2024-ə nisbətən -1.1%, ehtiyat +18.0%: ehtiyat doğulmalardan sürətlə artır, ona görə əmsal düşür; 2024-cü ilin doğulmaları əvvəlki iki müşahidəyə nisbətən -6% idi |
<!-- /AUTO:plaus -->

İşarələrin əsas səbəbi: doğulmalar 2022–2024-cü illər səviyyəsinə yaxın proqnozlaşdırılır (fəaliyyət panelində ildə
təxminən 105 000), qeydiyyatdakı ehtiyat isə eynilik vasitəsilə artmaqda davam edir; buna görə giriş əmsalları və
ehtiyat artımı 2019-cu ildən bəri müşahidə olunan azalmanı davam etdirir (bütün qruplar üzrə giriş əmsalı 2019-cu ildə
10,4%, 2023-cü ildə 8,8%, 2024-cü ildə 6,6%) və bir neçə qrupda qısa tarixi minimumdan aşağı düşür. Bu, uyğunlaşdırma
artefaktı deyil, mexanizmdir. Son faktiki əmsal qrupun 2026-cı il zolağından yuxarıda olduqda cədvəl arifmetikanı
göstərir: iki il ərzində ehtiyat 4–18% artdığı halda doğulmalar az dəyişir. Tarixi ehtiyat artımına eyniliyin nəzərə
almadığı fəaliyyətin bərpası və yenidən təsnifləşdirmələr də daxildir (F4), buna görə proqnozlaşdırılan ehtiyat artımı
aşağı istinad göstəricisidir.

## 14. Konsentrasiya yolları

Aqreqat məlumatlarla konsentrasiya yolu yalnız **ölçü strukturu** vasitəsilə identifikasiya olunur: hər qrupun
buraxılışında KOS payı (log-odds) FR1-in sektor yolları ilə idarə olunur, qrup sabit effektləri ilə, §12-dəki eyni
prosedurla seçilir və yoxlanılır; qruplar üzrə saylar proqnozlaşdırılan ehtiyatla birlikdə artır; iri vahidlərin sayı
2026-cı ilin iyul səviyyəsində saxlanılır; hər qrupun hədd rejimi sabitdir (§9), buna görə hədlər fasiləsiz dəyişir.
Hədlər yalnız iri müəssisələrin payı və müəssisələrin sayı vasitəsilə dəyişir: iri müəssisələr qrupu *daxilində*
konsentrasiya müəssisə məlumatları olmadan proqnozlaşdırıla bilməz (B qatı).

<!-- AUTO:concpaths -->
| qrup | hhi_lower 2026 | hhi_lower 2030 | hhi_upper 2026 | hhi_upper 2030 | large_share 2026 | large_share 2030 |
|---|---|---|---|---|---|---|
| ACC | 24.40 | 23.90 | 528.10 | 524.10 | 22.70 | 22.70 |
| AGR | 50.70 | 49.40 | 3156.00 | 3156.00 | 36.30 | 36.30 |
| CON | 38.40 | 38.20 | 3965.90 | 3964.80 | 62.90 | 62.90 |
| EDU | 6.80 | 6.30 | 5967.00 | 5967.00 | 9.20 | 9.20 |
| HEA | 33.40 | 32.50 | 2963.70 | 2963.70 | 37.60 | 37.60 |
| ICT | 131.00 | 130.60 | 4380.50 | 4377.30 | 66.10 | 66.10 |
| IND | 35.00 | 35.00 | 8277.60 | 8277.60 | 91.00 | 91.00 |
| OTH | 20.90 | 20.70 | 2578.00 | 2577.60 | 50.70 | 50.70 |
| REA | 112.70 | 112.10 | 1436.00 | 1437.20 | 37.70 | 37.70 |
| TRA | 118.70 | 118.70 | 6757.40 | 6757.20 | 82.20 | 82.20 |
| TRD | 4.70 | 4.60 | 907.60 | 907.30 | 30.10 | 30.10 |
<!-- /AUTO:concpaths -->

## 15. Sənaye təşkilatı nəzəriyyəsi ilə ssenari təhlili

Kalibrlənmiş, şəffaf Kurno (Cournot) alətlər dəsti. Bazar öz HHI-ı (simmetrik ekvivalent müəssisə sayı $N=1/HHI$),
kalibrləmə nöqtəsində tələbin elastikliyi ε və davranış parametri θ (1 = Kurno, < 1 daha rəqabətli) ilə ümumiləşdirilir.
Sahə üzrə Lerner indeksi $L=\theta\,HHI/\varepsilon$; qiymət və buraxılış 1-ə normallaşdırıldıqda son hədd xərci
$c=1-L$; xətti tələb $P=a-bQ$, burada $b=1/\varepsilon$; simmetrik tarazlıq $Q=N(a-c)/(b(N+\theta))$.

| Ssenari | Mexanizm |
|---|---|
| (a) bazara giriş maneələrinin azaldılması / lisenziyalaşdırmanın sadələşdirilməsi | $N \to N+\Delta N$ |
| (b) birləşmə | $\Delta HHI = 2s_1s_2$; istifadə olunan HHI heç vaxt $s_1^2+s_2^2$-dən aşağı olmur; meyarlar: ABŞ 2010 (1500/2500; ΔHHI 100/200) və AB (ΔHHI ≥ 250 olduqda HHI 1000–2000, ΔHHI ≥ 150 olduqda > 2000); Farrell–Shapiro: qiymət yalnız birləşmiş müəssisənin son hədd xərci ən azı birləşmədən əvvəlki əlavə qiymət (markup) qədər azaldıqda düşür |
| (c) xərc şoku / vahid vergisi *t* | ötürülmə əmsalı xətti tələbdə $dP/dc = N/(N+\theta)$ (Kurno şəraitində = N/(N+1)), sabit elastiklikdə $N\varepsilon/(N\varepsilon-\theta)$ — koddakı eyni düsturlar, ədədi yoxlanılıb |
| (d) idxal rəqabəti / gömrük tarifinin dəyişməsi | *m* payı və η təklif elastikliyi olan rəqabətli idxal kənarı: $L=\theta\,HHI_d(1-m)/(\varepsilon+\eta m)$ |
| (e) dövlət müəssisəsi | **qarışıq oliqopoliya** (aşağıda) |

**Qarışıq oliqopoliya (De Fraja və Delbono 1989; qismən özəlləşdirmə Matsumura 1998-də olduğu kimi).** Buraxılış payı σ
və artan son hədd xərci $c+kq_0$ olan bir dövlət müəssisəsi $\lambda\pi_0+(1-\lambda)W$ ifadəsini maksimallaşdırır
(λ = 0: rifahı maksimallaşdıran dövlət müəssisəsi; λ = 1: tam özəlləşdirilmiş); son hədd xərci *c* olan *n* simmetrik
özəl müəssisə θ davranışı ilə Kurno oyunu oynayır. Birinci dərəcəli şərtlər: dövlət müəssisəsi $P=c+kq_0+\lambda\theta bq_0$;
özəl müəssisə $P=c+\theta bq_i$. Mövcud vəziyyətdə kalibrləmə (λ = 0, P = 1, Q = 1): $c=1-\theta b(1-\sigma)/n$,
$k=\theta b(1-\sigma)/(n\sigma)$ və $n=(1-\sigma)^2/(HHI-\sigma^2)$, buna görə istifadə olunan HHI heç vaxt σ²-dən
aşağı olmur (və n ≥ 1). Fərziyyələr: dövlət müəssisəsinin son hədd xərci özəl müəssisələrin səviyyəsindən başlayır və
buraxılışla artır; bütün dövlət sənaye istehsalçıları bir dövlət müəssisəsi kimi çıxış edir. σ = 2025-ci ildə dövlətin
sənaye buraxılışındakı payı (21,9%, `FR10_ownership.csv` vasitəsilə DSK sənaye `010_2`), həssaslıq kimi emal
sənayesinin 35,1%-i. Ssenari λ-nı 0,5-ə (qismən) və ya 1-ə (tam özəlləşdirmə) qaldırır; tarazlıq ədədi üsulla həll
olunur.

Hər ssenari bütün konsentrasiya diapazonu — HHI aşağı həddən yuxarı həddədək — × ε ∈ {0,5; 1; 1,5; 2} (FR5-in xidmətlər
sistemi 1,0 nəzərdə tutur) × θ ∈ {1; 0,5} üzrə **diapazon** kimi göstərilir; ε = 1, θ = 1 olduqda uc nöqtələr
göstərilir; heç bir "mərkəzi" dəyər ayrıca seçilmir. **Əsas nümunə bazarlar** təxmini ictimai struktur əsasında
kalibrlənir və tənzimləyici məlumatları ilə əvəz edilməli olan **illüstrativ fərziyyələrdir**: mobil telekommunikasiya
(üç operator, HHI 3 300–4 000), bank sektoru (təxminən 22 bank, ilk beşliyin aktivlərdəki payı ≈ 60%, HHI 800–1 300;
əvəz etmək üçün Mərkəzi Bankın (CBAR) konsentrasiya statistikası), sement (2–3 yerli istehsalçı və idxal, yerli HHI
3 500–5 500). Onların gəliri FR12-nin məlumatlarında yoxdur, buna görə onların rifah effektləri yalnız bazar gəlirinin
%-i ilə verilir.

<!-- AUTO:scen -->
| ssenari | bazar | dəyişiklik | fərziyyə | hhi_range | structure_source |
|---|---|---|---|---|---|
| S1 | ICT (İnformasiya və rabitə) | Giriş maneələrinin azaldılması / lisenziyalaşdırmanın sadələşdirilməsi | bir əlavə simmetrik-ekvivalent rəqib (ΔN = +1) | 122-4 037 | A qatının ölçü qrupu hədləri (8-ci hissə), 2024 |
| S1 | Mobil rabitə (3 operator) | Dördüncü mobil operatorun girişi | ΔN = +1 simmetrik-ekvivalent rəqib | 3 300-4 000 | FƏRZİYYƏ: 3 operator, abunəçi payları ≈ 50–55 / 25–30 / 20% (təxmini açıq hesabatlar) → HHI 3 300–4 000 |
| S2 | CON (Tikinti) | İki müəssisənin birləşməsi | birləşən paylar 10% və 5%; istifadə olunan HHI ≥ 0.10² + 0.05² | 39-3 973 | A qatının ölçü qrupu hədləri (8-ci hissə), 2024 |
| S2 | Bank sektoru (aktivlər) | İki bankın birləşməsi | birləşən aktiv payları 8% və 6%; istifadə olunan HHI ≥ 0.08² + 0.06² | 800-1 300 | FƏRZİYYƏ: ~22 bank, ilk 5 bank aktivlərin ≈ 60%-i (təxmini, AMB illik hesabatları) → HHI 800–1 300; AMB konsentrasiya məlumatı ilə əvəz edilməlidir |
| S3 | ACC (Yerləşdirmə və iaşə) | Xərc şoku / aksiz və ya vergi artımı | vahid xərc ilkin qiymətin +5%-i, bütün müəssisələr | 22-465 | A qatının ölçü qrupu hədləri (8-ci hissə), 2024 |
| S3 | Sement (yerli istehsalçılar) | Enerji xərcləri şoku | vahid xərc ilkin qiymətin +5%-i, bütün istehsalçılar | 3 500-5 500 | FƏRZİYYƏ: 2–3 yerli inteqrasiya olunmuş istehsalçı və idxal (təxmini) → daxili HHI 3 500–5 500 |
| S4 | IND (Sənaye) | İdxal rəqabəti (tarifin azaldılması) | idxal payı 30% → 40%, idxal təklifinin elastikliyi η = 2 | 34-7 957 | A qatının ölçü qrupu hədləri (8-ci hissə), 2024 |
| S4 | Sement (yerli istehsalçılar) | İdxal rəqabəti (tarifin azaldılması) | idxal payı 20% → 30%, η = 2 | 3 500-5 500 | FƏRZİYYƏ: 2–3 yerli inteqrasiya olunmuş istehsalçı və idxal (təxmini) → daxili HHI 3 500–5 500 |
| S5 | IND (Sənaye) | Dövlət müəssisəsinin qismən özəlləşdirilməsi (qarışıq oliqopoliya) | σ = 21.9% (sənaye), λ: 0 → 0.5 | 34-7 957 | A qatının ölçü qrupu hədləri (8-ci hissə), 2024 |
| S5 | IND (Sənaye) | Dövlət müəssisəsinin tam özəlləşdirilməsi (qarışıq oliqopoliya) | σ = 21.9% (sənaye), λ: 0 → 1.0 | 34-7 957 | A qatının ölçü qrupu hədləri (8-ci hissə), 2024 |
| S5 | IND (Sənaye) | Dövlət müəssisəsinin qismən özəlləşdirilməsi (qarışıq oliqopoliya) | σ = 35.1% (emal sənayesi), λ: 0 → 0.5 | 34-7 957 | A qatının ölçü qrupu hədləri (8-ci hissə), 2024 |
| S5 | IND (Sənaye) | Dövlət müəssisəsinin tam özəlləşdirilməsi (qarışıq oliqopoliya) | σ = 35.1% (emal sənayesi), λ: 0 → 1.0 | 34-7 957 | A qatının ölçü qrupu hədləri (8-ci hissə), 2024 |

Bütün diapazon üzrə nəticələr (HHI aşağı → yuxarı hədd × ε 0,5–2 × θ ∈ {1; 0,5}); ε = 1, θ = 1 olduqda uc nöqtələr:

| ssenari | bazar | fərziyyə | hhi_min | hhi_max | d_price_min | d_price_max | d_price_at_lower_bound | d_price_at_upper_bound | d_output_min | d_output_max | d_cs_pct_min | d_cs_pct_max | d_cs_mn_min | d_cs_mn_max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | ICT | bir əlavə simmetrik-ekvivalent rəqib (ΔN = +1) | 122 | 4 037 | -18.04 | -0.00 | -0.01 | -9.02 | 0.01 | 9.02 | 0.00 | 18.85 | 0.15 | 778.69 |
| S1 | MOB | ΔN = +1 simmetrik-ekvivalent rəqib | 3 300 | 4 000 | -17.78 | -1.82 | -6.56 | -8.89 | 3.64 | 8.89 | 1.85 | 18.57 | — | — |
| S2 | CON | birləşən paylar 10% və 5%; istifadə olunan HHI ≥ 0.10² + 0.05² | 125 | 3 973 | 0.21 | 1.96 | 0.98 | 0.71 | -0.98 | -0.42 | -1.95 | -0.21 | -402.89 | -42.90 |
| S2 | BNK | birləşən aktiv payları 8% və 6%; istifadə olunan HHI ≥ 0.08² + 0.06² | 800 | 1 300 | 0.22 | 1.76 | 0.88 | 0.84 | -0.88 | -0.45 | -1.75 | -0.22 | — | — |
| S3 | ACC | vahid xərc ilkin qiymətin +5%-i, bütün müəssisələr | 22 | 465 | 4.78 | 4.99 | 4.99 | 4.78 | -9.99 | -2.39 | -4.93 | -4.55 | -262.07 | -241.75 |
| S3 | CEM | vahid xərc ilkin qiymətin +5%-i, bütün istehsalçılar | 3 500 | 5 500 | 3.23 | 4.26 | 3.70 | 3.23 | -8.51 | -1.69 | -4.21 | -3.12 | — | — |
| S4 | IND | idxal payı 30% → 40%, idxal təklifinin elastikliyi η = 2 | 34 | 7 957 | -21.98 | -0.01 | -0.04 | -11.28 | 0.01 | 11.28 | 0.01 | 23.19 | 5.84 | 14657.68 |
| S4 | CEM | idxal payı 20% → 30%, η = 2 | 3 500 | 5 500 | -21.37 | -1.18 | -5.54 | -9.70 | 2.35 | 10.68 | 1.19 | 22.51 | — | — |
| S5 | IND | σ = 21.9% (sənaye), λ: 0 → 0.5 | 484 | 6 583 | 0.01 | 2.75 | 0.02 | 1.20 | -1.38 | -0.01 | -2.73 | -0.01 | -1727.00 | -3.42 |
| S5 | IND | σ = 21.9% (sənaye), λ: 0 → 1.0 | 484 | 6 583 | 0.01 | 4.31 | 0.02 | 2.16 | -2.16 | -0.01 | -4.27 | -0.01 | -2695.46 | -3.44 |
| S5 | IND | σ = 35.1% (emal sənayesi), λ: 0 → 0.5 | 1 238 | 5 442 | 0.01 | 6.17 | 0.03 | 3.09 | -3.09 | -0.02 | -6.08 | -0.01 | -3839.59 | -5.52 |
| S5 | IND | σ = 35.1% (emal sənayesi), λ: 0 → 1.0 | 1 238 | 5 442 | 0.01 | 10.50 | 0.03 | 5.25 | -5.25 | -0.02 | -10.22 | -0.01 | -6460.11 | -5.53 |

Birləşmə meyarları (S2):

| bazar | hhi_post_min | hhi_post_max | d_hhi | ABŞ | AB | fs_mc_cut_min | fs_mc_cut_max |
|---|---|---|---|---|---|---|---|
| BNK | 896.00 | 1396.00 | 96.00 | mənfi təsir ehtimalı azdır | ehtimal yoxdur | 2.00 | 35.10 |
| CON | 225.00 | 4072.70 | 100.00 | potensial olaraq ciddi narahatlıq yaradır / mənfi təsir ehtimalı azdır | ehtimal yoxdur | 0.30 | 386.70 |

Qarışıq oliqopoliya (S5): rifahı maksimallaşdıran dövlət müəssisəsi qiyməti artan son hədd xərcinə bərabər müəyyən edir və buraxılışı genişləndirir; özəlləşdirmə onu özəl müəssisə kimi buraxılışı məhdudlaşdırmağa vadar edir, buna görə onun payı azalır (hallar üzrə 0,1–29,9%-ə qədər), qiymət 0,01–10,50% artır və ümumi rifah bazar gəlirinin 0,00–4,50%-i qədər dəyişir; özəl Kurno müəssisələri (simmetrik ekvivalent) 1,0–1 000.
<!-- /AUTO:scen -->

## 16. Erkən xəbərdarlıq

Hər işarə son ortanı (son üç müşahidə; çıxış üçün son iki) əvvəlki orta ilə müqayisə edir, göstəricinin həmin sektorda
öz illik dəyişkənliyi ilə miqyaslanır (z) və mənfi istiqamətdə |z| > z* olduqda qaldırılır. Kompozit göstəriciyə daxil
olan işarələr: **konsentrasiya** (iri müəssisələrin buraxılış payı artır), **giriş** (yeni qeydiyyatların loqarifmi
azalır — axın, buna görə artan ehtiyat saxta azalma yarada bilməz), **çıxış** (çıxış əmsalı artır; 2022 dalğası
istisna edilir), **pay mobilliyi** (yalnız sənaye), **giriş azaldıqca marjaların artması**; çəkilər 0,25; 0,25; 0,15;
0,10; 0,25; bal = mövcud işarələr arasında qaldırılmış işarələrin çəkili payı; müşahidə siyahısı: bal ≥ 0,30 və ya
≥ 2 işarə; çatışmayan məlumatlar "məlumat kifayət deyil" verir. Yalnız məlumat üçün, kompozitə daxil deyil: verilmiş
lisenziyalar (artan lisenziya verilməsi maneə deyil, daha çox icazəli girişdir), kohort ölçüsü nisbəti (sağ qalma
əmsalı deyil), dövlətin fəal KOS-lardakı payı (iki il), yoxlamalar (F18).

**Hədd.** z* simulyasiya olunmuş **yanlış siyahıya salınma tezliyinin** — heç bir dəyişiklik olmayan sektorun müşahidə
siyahısına düşməsi ehtimalının — hər sıra üçün həm i.i.d., həm də təsadüfi gəzişmə sıfır fərziyyəsi şəraitində,
hər sektorun faktiki sıra uzunluqları ilə ən çoxu 10% olduğu ən kiçik dəyərdir (hər sektor və sıfır fərziyyə üçün
20 000 təkrarlama). Ənənəvi z = 1 həddi təsadüfi gəzişmə sıfır fərziyyəsi şəraitində dəyişiklik olmayan sektoru
halların dörddə birində siyahıya salır.

<!-- AUTO:ew -->
Hədd z* = 2. Simulyasiya olunmuş yanlış siyahıya salınma tezlikləri (dəyişiklik olmayan sektorlardan müşahidə siyahısına düşənlərin payı):

| z_threshold | sıfır fərziyyə | false_listing_rate |
|---|---|---|
| 1.00 | müstəqil eyni paylanmış (iid) | 0.03 |
| 1.00 | təsadüfi gəzişmə | 0.25 |
| 1.50 | müstəqil eyni paylanmış (iid) | 0.01 |
| 1.50 | təsadüfi gəzişmə | 0.14 |
| 2.00 | müstəqil eyni paylanmış (iid) | 0.00 |
| 2.00 | təsadüfi gəzişmə | 0.08 |

| qrup | ad | z_conc | z_entry | z_exit | z_mob | z_margin | F_conc | F_entry | F_exit | F_mob | F_margin_entry | n_available | n_flags | bal | watch_list | info_licences_z | info_cohort_size_ratio_change_pct | info_state_share_of_active_SMEs_2024 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AGR | Kənd təsərrüfatı | 1.13 | 1.04 | -1.29 | — | -6.48 | xeyr | xeyr | xeyr | məlumat kifayət deyil | xeyr | 4 | 0 | 0.00 | xeyr | -1.07 | -1.96 | 3.60 |
| IND | Sənaye | 0.00 | 2.78 | 0.90 | -0.63 | -1.01 | xeyr | xeyr | xeyr | xeyr | xeyr | 5 | 0 | 0.00 | xeyr | — | -11.99 | 2.16 |
| CON | Tikinti | -0.62 | -2.69 | 1.01 | — | -4.54 | xeyr | bəli | xeyr | məlumat kifayət deyil | xeyr | 4 | 1 | 0.28 | xeyr | 0.45 | 4.72 | 0.87 |
| TRD | Ticarət | 3.84 | 0.57 | 0.58 | — | 0.20 | bəli | xeyr | xeyr | məlumat kifayət deyil | xeyr | 4 | 1 | 0.28 | xeyr | -0.73 | 1.80 | 0.06 |
| TRA | Nəqliyyat | -0.42 | 0.41 | -2.47 | — | -1.23 | xeyr | xeyr | xeyr | məlumat kifayət deyil | xeyr | 4 | 0 | 0.00 | xeyr | 0.37 | -4.78 | 0.18 |
| ACC | Yerləşdirmə və iaşə | -0.64 | 0.74 | 0.81 | — | -0.52 | xeyr | xeyr | xeyr | məlumat kifayət deyil | xeyr | 4 | 0 | 0.00 | xeyr | — | -0.07 | 0.06 |
| ICT | İnformasiya və rabitə | -0.92 | 0.87 | 0.29 | — | -4.59 | xeyr | xeyr | xeyr | məlumat kifayət deyil | xeyr | 4 | 0 | 0.00 | xeyr | 1.83 | 2.35 | 1.46 |
| REA | Daşınmaz əmlak | 0.13 | 0.50 | 0.17 | — | 0.81 | xeyr | xeyr | xeyr | məlumat kifayət deyil | xeyr | 4 | 0 | 0.00 | xeyr | — | 0.60 | 1.01 |
| EDU | Təhsil | 0.23 | 1.46 | -1.22 | — | -1.28 | xeyr | xeyr | xeyr | məlumat kifayət deyil | xeyr | 4 | 0 | 0.00 | xeyr | -0.90 | -7.82 | 0.37 |
| HEA | Səhiyyə və sosial xidmətlər | -0.49 | -0.10 | 0.44 | — | -3.11 | xeyr | xeyr | xeyr | məlumat kifayət deyil | xeyr | 4 | 0 | 0.00 | xeyr | -0.83 | 4.98 | 1.01 |
| OTH | Digər sahələr | -1.66 | -0.55 | -2.94 | — | -2.60 | xeyr | xeyr | xeyr | məlumat kifayət deyil | xeyr | 4 | 0 | 0.00 | xeyr | -1.12 | -4.16 | 0.28 |

Müşahidə siyahısı (0): boşdur. Tək işarələr (izləmə): Tikinti — giriş; Ticarət — konsentrasiya.
<!-- /AUTO:ew -->

## 17. B qatı — müəssisə səviyyəli rəqabət mühərriki (reyestr daxil olana qədər SİNTETİK)

### 17.1 Giriş məlumatlarının sxemi

Hər müəssisə və il üçün bir sətir: `data_status` (sintetik işarə; olmadıqda və ya istənilən digər dəyərdə = REAL),
`firm_id` (psevdonimləşdirilmiş, heç vaxt VÖEN deyil), `year`, `nace2` (iki rəqəmli sahə kodu, A–S və U bölmələri),
`region` (14), `ownership` (dövlət, bələdiyyə, özəl, xarici, birgə), `size_class` (mikro, kiçik, orta, iri), `revenue`
(min manat), `employees`, `registration_date`, `liquidation_date` (fəaliyyət davam etdikcə boş), `status` (fəal; ləğv
ilində ləğv edilmiş); əlavə olaraq `legal_form`, `exports`, `product_codes`, `cost_of_sales`, `operating_costs`
(marjalar və Boone göstəricisi üçün; FR10-un müəssisə panelindən `firm_id` üzrə də birləşdirilə bilər) və `weight`
(sətrin təmsil etdiyi eyni müəssisələrin sayı; tam siyahıyaalma reyestrində 1 və ya yoxdur). Azərbaycan dilində
adlarla tam sxem: `data/business_register/FR12_business_register_column_map.csv` və
`output/FR12_business_register_schema.csv`.

### 17.2 Mühərrik

Bazar = NACE sahəsi × region × il (və ölkə üzrə sahə × il). Gəlirlərin HHI, CR4/CR8, entropiya, ekvivalent müəssisə
sayı və Cini əmsalı; payların qeyri-sabitliyi (½Σ|Δs|, daxil olanlar və çıxanlar sıfır pay ilə hesablanır) və sıra
mobilliyi (mövcud müəssisələrin sıralarının 1 − Spearman ρ); giriş, çıxış və dövriyyə (churn) əmsalları, daxil olan
və çıxan müəssisələrin nisbi ölçüsü; qeydiyyat kohortları üzrə Kaplan–Meier sağ qalması (qeydiyyat ilində ölümlər
nəzərə alınır); beş yaşdan kiçik müəssisələrin gəlir payı; xərc sahələri mövcud olduqda isə qiymət-xərc marjası və
**Boone göstəricisi** — hər bölmə-il üzrə mənfəətin loqarifminin orta dəyişən xərcin loqarifminə görə kəsişən meyli
(mənfəətin davamlılığı üzrə AR modeli yoxdur); ən azı 20 mənfəətli müəssisə (çəkili say) olduqda hesablanır. **Seçim
meyli:** mənfəətin loqarifmi yalnız mənfəətli müəssisələr üçün mövcuddur, buna görə zərərlə işləyənlər — adətən ən az
səmərəli olanlar — istisna edilir; nümunə nəticə dəyişəni üzrə kəsilmişdir və meyl sıfıra doğru sürüşür. Boone
göstəricisi struktur elastiklik kimi deyil, sektorlar arasında və zaman üzrə sıralama kimi şərh olunur; qiymət-xərc
marjasına zərərlə işləyən müəssisələr də daxildir. Hər göstərici (HHI, CR4/CR8, giriş və çıxış, Kaplan–Meier,
Spearman sıra mobilliyi, Boone sayı) `weight` tezlik çəkisini nəzərə alır və olmayan sütunu çəki 1 kimi qəbul edir;
əvəzləmə testi çəkili faylın və onun hər müəssisəyə bir sətir olmaqla açılmış variantının eyni nəticələr verdiyini
yoxlayır. §15-in IO alətləri müəssisə səviyyəli HHI-ı birbaşa qəbul edir.

### 17.3 SİNTETİK reyestr

Toxumlu (`SEED + 17`); bütün NACE bölmələri (A–S, U), 14 region, 2019–2025. Bölmə × region üzrə doğulmalar və
ölümlər hər iki marjinal cəmi dəqiq saxlayan iterativ proporsional uyğunlaşdırma və tam ədədə yuvarlaqlaşdırma ilə
qurulur, beləliklə reyestr dərc olunduğu yerdə NACE bölmələri üzrə (2021, 2024, 2025) və regionlar üzrə (2021–2025)
DSK-nın doğulma və ölümlərini, 2025-ci ilin sonuna bölmələr və regionlar üzrə ehtiyatı, bölmələr üzrə milli hesablar
buraxılışını (gəlir kimi), fəaliyyət qrupları üzrə KOS-un gəlir payını və onun mikro/kiçik/orta bölgüsünü (012) və —
iri vahidlərin 251 işçi aşağı həddinin məhdudlaşdırdığı hallar istisna olmaqla — KOS-un işçilərdəki payını (013)
**dəqiq** təkrarlayır. Əvvəlki ehtiyatlar doğulmalardan və ölümlərdən alınır (reyestrin öz ehtiyatları ehtiyat-axın
eyniliyini ödəmir, F5, buna görə onların hamısını uyğunlaşdırmaq mümkün deyil); ölçü qrupları tərkibi 1 iyul 2026-cı
il vəziyyətinə təxminən uyğunlaşdırılır. Heterogenlik: iri müəssisələrin ölçüləri mədənçıxarma, kommunal xidmətlər,
telekommunikasiya və maliyyədə aşağı forma parametrli (konsentrasiyalı), ticarət və ictimai iaşədə isə yüksək forma
parametrli (parçalanmış) Pareto paylanmasına malikdir; açıq bəyan edilmiş məlumat yaradan proses xərc səmərəliliyini
ölçü ilə əlaqələndirir ki, Boone göstəricisinin aşkar edəcəyi bir şey olsun. Faylı kiçik saxlamaq üçün mikro və kiçik
vahidlər 40 və 5-ə qədər eyni müəssisədən ibarət sətirlərdə qruplaşdırılır (`weight`); mühərrik sətri həmin sayda
müəssisə kimi qəbul edir.

<!-- AUTO:layerb -->
**B qatının məlumat rejimi: SİNTETİK** — giriş faylı `data/business_register/FR12_business_register_SYNTHETIC.csv`, 92 032 sətir, 15 725 qeyd (2025-ci ildə 226 643 fəal müəssisə), 20 NACE bölməsi, 86 sahə, 14 region, 2019–2025. Reyestr **SİNTETİKDİR — real müəssisə məlumatı deyil**; B qatının nəticələri tapıntılar deyil, emal xəttinin nümayişidir.

**Bu bölmə tapıntılar deyil, emal xəttinin nümayişidir.** Nazirlik `data/business_register/FR12_business_register_SYNTHETIC.csv` faylını öz sistemində öz reyestri ilə (`FR12_business_register.csv/.xlsx` və ya `BUSREG_PATH`) əvəz edir və notebook-u yenidən icra edir; bundan sonra nəticələr `FR12_FIRM_*.csv` olur.

DSK aqreqatlarına qarşı kalibrləmə xətaları:

| hədəf | ölçü | vəziyyət | xanalar | max_abs_error | median_abs_rel_error_pct | max_abs_rel_error_pct |
|---|---|---|---|---|---|---|
| KOS-un işçi sayında payı, % | fəaliyyət qrupu | dəqiq (iri vahidlərin 251 işçi döşəməsi məhdudlaşdırdığı hallar istisna) | 55 | 7.95 | 0.00 | 10.58 |
| KOS-un gəlirdə payı, % | fəaliyyət qrupu | dəqiq (buraxılış bazası) | 55 | 0.00 | 0.00 | 0.00 |
| fəal vahidlər, ilin sonu | region | dəqiq 2025; əvvəlki illər ehtiyat-axın ilə | 70 | 117.00 | 0.11 | 2.45 |
| fəal vahidlər, ilin sonu | bölmə | dəqiq 2025; əvvəlki illər ehtiyat-axın ilə (F5) | 60 | 731.00 | 0.12 | 10.19 |
| doğulmalar | region | dəqiq | 70 | 0.00 | 0.00 | 0.00 |
| doğulmalar | bölmə | dərc olunduğu yerdə dəqiq | 60 | 0.00 | 0.00 | 0.00 |
| ölümlər | region | dəqiq | 70 | 0.00 | 0.00 | 0.00 |
| ölümlər | bölmə | dərc olunduğu yerdə dəqiq | 60 | 0.00 | 0.00 | 0.00 |
| gəlir (min AZN) = buraxılış | bölmə | dəqiq | 133 | 0.86 | 0.00 | 0.00 |
| ölçü strukturu: iri vahidlərin payı, % | bölmə | təxmini (1 iyul 2026 vəziyyəti) | 18 | 2.08 | 17.73 | 52.69 |
| ölçü strukturu: orta vahidlərin payı, % | bölmə | təxmini (1 iyul 2026 vəziyyəti) | 18 | 1.73 | 9.49 | 31.23 |
| ölçü strukturu: mikro vahidlərin payı, % | bölmə | təxmini (1 iyul 2026 vəziyyəti) | 18 | 5.09 | 0.47 | 6.44 |
| ölçü strukturu: kiçik vahidlərin payı, % | bölmə | təxmini (1 iyul 2026 vəziyyəti) | 18 | 1.57 | 4.13 | 19.97 |

Emal xətti testləri:

| test | dəyər | keçib |
|---|---|---|
| hər bazarda HHI ≥ 10000 / N | 0.00 | bəli |
| CR4 ≤ CR8 ≤ 100 | 0.00 | bəli |
| entropiya ≤ ln N | 0.00 | bəli |
| gəliri olan hər milli bölmə bazarında paylar cəmi 1-dir | 0.00 | bəli |
| Kaplan–Meyer sağ qalma əyrisi artmır və [0, 1] aralığındadır | 0.00 | bəli |
| kalibrləmə: doğulmalar, ölümlər, gəlir və KOS gəlir payları dərc olunduğu yerdə DSK-nı təkrarlayır (maks. /nisbi xəta/ %) | 0.00 | bəli |
| MYP yoxlaması: bölmə-illərin ≥ 90%-ində Boone meyli mənfidir (səmərəli müəssisələr böyükdür) | 1.00 | bəli |
| MYP yoxlaması: aşağı Pareto-α bölmələri daha konsentrasiyalıdır (median HHI nisbəti) | 14.07 | bəli |

Əvəzləmə testləri (müvəqqəti qovluq):

| test | keçib | təfərrüat |
|---|---|---|
| neytral data_status ilə real adlı fayl → DATA_MODE = REAL | bəli | rejim REAL, fayl FR12_business_register.csv |
| REAL fayl yoxlamadan keçir (0 ciddi səhv) | bəli | 0 xəbərdarlıq |
| REAL rejimi yalnız su nişanı olmayan FR12_FIRM_* yazır; eynilik testləri keçir; B qatının ekonometrikası REAL rejimdə işləyir (FR12_FIRM_econ_*) | bəli | 15 fayl, məsələn ['FR12_FIRM_concentration_nace.csv', 'FR12_FIRM_concentration_nace_region.csv', 'FR12_FIRM_econ_boone_sector_year.csv']; ekonometrika: 12 rejiml, 262 əmsal = SİNTETİK icra ilə eyni, no wa |
| Azərbaycan dilində başlıqlar (xlsx) yüklənir və yoxlanılır | bəli | 3000 sətir, naməlum sütunlar [], rejim REAL |
| BUSREG_PATH mühit dəyişəni real adlı fayldan üstündür | bəli | yükləndi register_az.xlsx (BUSREG_PATH mühitdə təyin edilib) |
| çəki sütunu olmayan reyestr: mühərrik tam işləyir (çəkilər 1 qəbul edilir) | bəli | 38,849 sətir, rejim REAL; mühərrik + DSK müqayisəsi (615 xana) icra olundu |
| çəkilər nəzərə alınır: çəkili fayl = genişləndirilmiş çəkisiz fayl (HHI, CR4/CR8, giriş/çıxış, KM, Boone n, PCM) | bəli | maks. mütləq fərq 6.37e-12 — 112 xana |
| xətalı fayl: çatışmayan məcburi sütun ciddi səhv kimi göstərilir | bəli | məcburi sütun yoxdur (EN və ya AZ başlıq) |
| xətalı fayl: mənfi gəlir və qeydiyyatdan əvvəl ləğv sətir-sətir göstərilir; icra dayanır | bəli | biznes reyestri rədd edildi: 8 ciddi səhv (birinci: sətir 2, sahə revenue: mənfi dəyər); bax: rep.csv |
| generator heç vaxt real fayl adını yazmır; layihə qovluğu real adlı fayllar üçün yoxlanılır | bəli | generator yazdı ['FR12_business_register_SYNTHETIC.csv', 'FR12_business_register_TEMPLATE.csv', 'FR12_business_register_TEMPLATE.xlsx', 'FR12_business_register_column_map.csv', 'README_FR12_business_r |

Yüklənmiş reyestr üzrə validator: 0 xəbərdarlıq, 0 ciddi xəta.
<!-- /AUTO:layerb -->

### 17.4 Sintetik faylın əvəz edilməsi (Nazirlik tərəfindən, öz sistemində)

1. Reyestri `data/business_register/FR12_business_register.csv` (və ya `.xlsx`, `data` vərəqi) kimi saxlayın və ya
   `BUSREG_PATH` mühit dəyişənini fayla yönləndirin (prioritet: `BUSREG_PATH` → real adlı fayl → SİNTETİK; dəyişən
   yükləmə zamanı oxunur və onun prioriteti sınaqdan keçirilir).
2. Sütun başlıqları ingilis və ya Azərbaycan dilində ola bilər; `weight` buraxıla bilər (1 kimi qəbul edilir);
   şablondakı nümunə sətrini silin.
3. `FR12.ipynb` faylını yenidən icra edin. Başlıqda `DATA_MODE = REAL` çap olunur; validator hər sətir və sahə üzrə
   `output/FR12_business_register_validation_report.csv` faylını yazır (ciddi xətalar icranı mesajla dayandırır,
   xəbərdarlıqlar dayandırmır); nəticələr su nişanı olmadan `FR12_FIRM_*.csv` olur, sintetik nəticələr silinir və DSK
   aqreqatları ilə müqayisə əhatə yoxlamasına çevrilir (`FR12_FIRM_coverage_vs_dsk*.csv`).
4. İdentifikatorları psevdonimləşdirilmiş saxlayın; real nəticələr Nazirliyin sistemi daxilində qalır. A qatının
   nəticələri dəyişmir.

## 18. Yoxlamalar və nəticə faylları

<!-- AUTO:checks -->
Arifmetik yoxlamalardan keçənlər: 19 / 19 (`FR12_identity_checks.csv`).
<!-- /AUTO:checks -->

Bu icranın nəticə faylları:

<!-- AUTO:outputs -->
`FR12_SYNTHETIC_calibration_errors.csv`, `FR12_SYNTHETIC_calibration_errors_summary.csv`, `FR12_SYNTHETIC_concentration_nace.csv`, `FR12_SYNTHETIC_concentration_nace_region.csv`, `FR12_SYNTHETIC_econ_boone_sector_year.csv`, `FR12_SYNTHETIC_econ_coefficients.csv`, `FR12_SYNTHETIC_econ_cohorts.csv`, `FR12_SYNTHETIC_econ_entry_irr.csv`, `FR12_SYNTHETIC_econ_exit_hazard.csv`, `FR12_SYNTHETIC_econ_recovery.csv`, `FR12_SYNTHETIC_econ_recovery_not_defined.csv`, `FR12_SYNTHETIC_econ_summary.csv`, `FR12_SYNTHETIC_econ_survival.csv`, `FR12_SYNTHETIC_entry_exit_section.csv`, `FR12_SYNTHETIC_entry_exit_section_region.csv`, `FR12_SYNTHETIC_margins_boone.csv`, `FR12_SYNTHETIC_pipeline_tests.csv`, `FR12_SYNTHETIC_survival_km.csv`, `FR12_band_meta.csv`, `FR12_barriers.csv`, `FR12_business_register_schema.csv`, `FR12_business_register_swap_tests.csv`, `FR12_business_register_validation_report.csv`, `FR12_coef_sensitivity.csv`, `FR12_coherence.csv`, `FR12_cohort_size_ratio.csv`, `FR12_concentration_bounds.csv`, `FR12_concentration_paths.csv`, `FR12_data_gaps_and_alternatives.csv`, `FR12_data_integrity_findings.csv`, `FR12_data_source_matrix.csv`, `FR12_dsk_manifest.csv`, `FR12_early_warning.csv`, `FR12_early_warning_false_listing.csv`, `FR12_early_warning_projected.csv`, `FR12_fan_entry_exit.csv`, `FR12_fe_estimates.csv`, `FR12_forecast_entry_exit.csv`, `FR12_forecast_tidy.csv`, `FR12_gapfill_sensitivity.csv`, `FR12_holdout_detail.csv`, `FR12_holdout_validation.csv`, `FR12_identity_checks.csv`, `FR12_indicator_catalog.csv`, `FR12_indicators_groups.csv`, `FR12_indicators_regions.csv`, `FR12_indicators_sections.csv`, `FR12_last_actual_vs_2026_band.csv`, `FR12_merger_screen.csv`, `FR12_noar_constructs.csv`, `FR12_not_forecast.csv`, `FR12_pcm_sections.csv`, `FR12_plausibility.csv`, `FR12_presentation_spec.csv`, `FR12_regional_dispersion.csv`, `FR12_register_flows.csv`, `FR12_robustness_summary.csv`, `FR12_scenario_assumptions.csv`, `FR12_scenario_results.csv`, `FR12_scenario_summary.csv`, `FR12_section_allocation.csv`, `FR12_section_allocation_holdout.csv`, `FR12_section_nowcast_2026.csv`, `FR12_selection_scores.csv`, `FR12_selection_summary.csv`, `FR12_series_filled.csv`, `FR12_share_instability_branches.csv`, `FR12_sme_employment_model.csv`, `FR12_strings_az.csv`, `FR12_taxpayer_concentration.csv`
<!-- /AUTO:outputs -->

## 19. Məhdudiyyətlər

- Hər fəaliyyət qrupu və hər region üzrə beş illik müşahidə: seçim və nümunədən kənar yoxlama testlərinin gücü çox
  aşağıdır, nümunədən kənar yoxlamada bir və ya iki hədəf ili var, uyğunluq yoxlaması zəifdir (hər vahid üzrə iki-dörd
  keçid), zolaqlar isə hər üfüq üzrə 1–4 tarixi xəta cütünə əsaslanır; protokol zərəri məhdudlaşdırır, lakin informasiya
  yarada bilməz.
- 006 cədvəlində 2022-ci il tərif dəyişikliyi qırılmadan sonrakı üç il üzrə qiymətləndirilmiş bir qırılma termini ilə
  udulur.
- Fəaliyyət paneli bazara girişi deyil, fərdi sahibkarlar daxil olmaqla qeydiyyatları sayır; reyestr üzrə çıxış bazardan
  çıxışı azaldılmış göstərir (fəaliyyətsiz vahidlər qeydiyyatda qalır, F14).
- Fəaliyyət qrupları antiinhisar bazarlarından xeyli genişdir; A qatında konsentrasiya ölçülmür, hədlərlə
  məhdudlaşdırılır.
- IO ssenariləri qiymətləndirmələr deyil, açıq bəyan edilmiş fərziyyələr şəraitində kalibrləmələrdir; davranış
  parametri və elastikliklər qeyri-müəyyənliyin əsas mənbələridir və açıq şəkildə dəyişdirilir.
- B qatı SİNTETİK məlumatlar üzərində işləyir: o, Azərbaycan müəssisələri haqqında hər hansı faktı deyil, emal xəttinin
  işlədiyini sübut edir.

## 20. v2 qeydi: boşluqların doldurulması, B qatının ekonometrikası, tənliklər reyestri, ssenari mühərriki, dayanıqlıq

### 20.1 Müşahidə dövrü daxilindəki boşluqlar (yalnız qrafik və cədvəllər üçün)

İki müşahidə ili arasındakı boşluq qonşu müşahidə illərindən doldurulur: **səviyyələr log-xətti, əmsallar və paylar xətti
interpolyasiya** ilə; fəaliyyət qruplarının cəmi doldurulmuş komponentlərin cəmidir. İlk müşahidədən əvvəl və sonuncudan sonra
**ekstrapolyasiya edilmir** (ilkin boşluq "doldurulmayıb" kimi qeyd olunur; gələcək proqnozun işidir). Hər doldurulmuş dəyər
`FR12_series_filled.csv` və `FR12_forecast_tidy.csv`-də `imputed = True` ilə işarələnir; notebook-un qrafiklərində doldurulmuş nöqtələr
boş markerlə və qırıq xətlə, "Doldurulmuş (interpolyasiya)" legendası ilə göstərilir. **Qiymətləndirmə yalnız müşahidə edilmiş
məlumatla aparılır.** 2021-ci il üçün doldurulmuş dəyər 2020 (köhnə tərif) və 2022 (yeni tərif, birdəfəlik silinmə dalğası) arasındadır:
o ölçmə deyil, təqdimat dəyəridir.

<!-- AUTO:v2_gaps -->
Doldurulmuş dəyərlər: 327 (237 sıra). Qiymətləndirmə yalnız müşahidə edilmiş məlumatla aparılır.

| sıra ailəsi | sıra | dəyər | doldurulmuş illər |
|---|---|---|---|
| fəaliyyət qrupları (006) | 60 | 60 | 2021 |
| KOS payları (012/013) | 33 | 33 | 2021 |
| NACE bölmələri, tam il (2_1) | 90 | 180 | 2022, 2023 |
| NACE bölmələri, yanvar–iyun (2_1) | 54 | 54 | 2023 |

İlkin boşluqlar (doldurulmayıb, ekstrapolyasiya yoxdur):

| sıra ailəsi | sıra | illər |
|---|---|---|
| regionlar | 70 | 2019–2020 |
| NACE bölmələri, tam il (2_1) | 90 | 2019–2020 |
| NACE bölmələri, yanvar–iyun (2_1) | 54 | 2019–2021 |
<!-- /AUTO:v2_gaps -->

### 20.2 Həssaslıq: doldurulmuş 2021 dəyərləri ilə yenidən qiymətləndirmə

Eyni qaydalar (sürücülər, ankerləmə, kombinasiya, uyğunluq filtri) doldurulmuş 2021 dəyərləri əlavə edilmiş panelə tətbiq olunur;
2021 üçün qırılma termini və 2022 impulsu ½ götürülür, kənd təsərrüfatının 2021 doğulmaları çıxarılır (qonşusu F7 dalğasıdır).

<!-- AUTO:v2_gapsens -->
Əmsallar (yalnız müşahidə vs doldurulmuş 2021 daxil):

| maddə | termin | observed_only | with_filled | rel_diff_pct |
|---|---|---|---|---|
| activity/lnB m1 (struktur) | dem | 0.0026 | 0.0022 | -17.03 |
| activity/lnB m1 (struktur) | brk | 0.0867 | 0.0918 | 5.92 |
| activity/lnB m0 (sıfır model) | brk | 0.1137 | 0.1134 | -0.20 |
| activity/exit m0 (sıfır model) | d2022 | 2.0924 | 2.0738 | -0.89 |

2030 proqnozları (bütün qruplar):

| maddə | termin | observed_only | with_filled | rel_diff_pct |
|---|---|---|---|---|
| fr12:act:entry:ALL | Əsas | 5.501 | 5.499 | -0.05 |
| fr12:act:exit:ALL | Əsas | 2.178 | 2.182 | 0.19 |
| fr12:act:N:ALL | Əsas | 1 906 740.911 | 1 905 853.274 | -0.05 |
| fr12:act:new:ALL | Əsas | 104 893.430 | 104 797.124 | -0.09 |
| fr12:act:entry:ALL | Mənfi | 5.498 | 5.496 | -0.03 |
| fr12:act:exit:ALL | Mənfi | 2.179 | 2.183 | 0.18 |
| fr12:act:N:ALL | Mənfi | 1 906 313.614 | 1 905 498.719 | -0.04 |
| fr12:act:new:ALL | Mənfi | 104 803.121 | 104 722.172 | -0.08 |
| fr12:act:entry:ALL | İslahat | 5.506 | 5.503 | -0.06 |
| fr12:act:exit:ALL | İslahat | 2.178 | 2.182 | 0.19 |
| fr12:act:N:ALL | İslahat | 1 907 208.277 | 1 906 241.113 | -0.05 |
| fr12:act:new:ALL | İslahat | 105 011.183 | 104 894.853 | -0.11 |

KOS-un buraxılış payı 2030: maksimal |dəyişmə| 1,44 faiz bəndi.
<!-- /AUTO:v2_gapsens -->

### 20.3 Tam proqnoz cədvəli: bölmə axınları, KOS-un məşğulluq payı və proqnozlaşdırılmayan komponent

**NACE bölmələri üzrə reyestr axınları** (statistik vahidlər, 2_1) öz modeli ilə deyil, **bölüşdürmə** ilə proqnozlaşdırılır: bölmə
axınları regional panellə eyni məcmudur (hər tam ildə 2_1 bölmə cəmi 2_3 region cəminə bərabərdir), ona görə regional panelin
doğulma, ölüm və ehtiyat proqnozu cəmdir; o əvvəlcə 11 fəaliyyət qrupuna, sonra qrup daxilində bölmələrə **son faktiki ilin (2025)
paylarına ankerlənərək** bölünür (bütün modullarda olduğu kimi son müşahidə səviyyəni daşıyır; 2024 → 2025 yoxlamasında ankerlənmiş
paylar orta paylardan, xüsusilə ehtiyat üçün, xeyli dəqiqdir). 006 fəaliyyət proqnozu istifadə olunmur — o başqa məcmudur
(qeydiyyatdakı sahibkarlıq subyektləri, F6). **2026**: yanvar–iyun 2026 faktı FR1-in il-əvvəlindən-bu-günə məlumatı kimi istifadə
olunur — tam il = I yarım 2026 ÷ bölmənin müşahidə edilmiş I yarım / il nisbəti (2024–2025 ortası); bölüşdürmənin 2026 dəyərinə görə
artım 2026-da tam tətbiq olunur və sonra bir illik yarımömürlə sönür; qeyri-bazar bölmələri O və U istisnadır (I yarım 2026-da dövlət
idarəetməsində 228 inzibati ləğv, F10). Hər il bölmələr cəmə yenidən miqyaslanır: bölmələr qrupa, qruplar cəmə dəqiq bərabərdir;
zolaqlar cəmin zolağı × (düzəldilmiş) pay. Bölməyə xas sürücü qaydası seçimdən əvvəlki dizaynda yoxlana bilmir (≤ 2022 yalnız 2021
müşahidə olunub). Yanvar–iyun axınları 2027–2030 = tam il bölmə dəyəri × müşahidə edilmiş I yarım / il nisbəti.
Kataloqda bu sıralar `derived: allocation` kimi işarələnib. **KOS-un işçi sayında payı** KOS-un buraxılış payı ilə eyni qayda ailəsi ilə
(log-odds, qrup sabit effektləri, seçim ≤ 2022 → 2023, nümunədən kənar yoxlama, son mənbə ilində uyğunluq filtri) proqnozlaşdırılır.

<!-- AUTO:v2_alloc -->
Kataloq: 378 id, onlardan 377 tam proqnozlaşdırılır (3 ssenari × 2026–2030), 1 yalnız tarix / qismən. Bölüşdürmənin nümunədən kənar yoxlaması (2024 → 2025, faktiki cəm verilmişkən):

| dəyişən | variant | used_in_baseline | rmse | theil_vs_other_variant | dm_p_anchored_vs_average |
|---|---|---|---|---|---|
| yeni | ankerlənmiş: son müşahidə ili (mənbədə 2024; proqnozda 2025) | bəli | 198.91 | 0.94 | 0.18 |
| yeni | müşahidə illərinin ortası (mənbədə 2021, 2024) | xeyr | 211.17 | 1.06 | 0.18 |
| ləğv edilən | ankerlənmiş: son müşahidə ili (mənbədə 2024; proqnozda 2025) | bəli | 30.35 | 1.16 | 0.36 |
| ləğv edilən | müşahidə illərinin ortası (mənbədə 2021, 2024) | xeyr | 26.18 | 0.86 | 0.36 |
| ehtiyat | ankerlənmiş: son müşahidə ili (mənbədə 2024; proqnozda 2025) | bəli | 449.85 | 0.29 | 0.09 |
| ehtiyat | müşahidə illərinin ortası (mənbədə 2021, 2024) | xeyr | 1532.33 | 3.41 | 0.09 |

2026 cari qiymətləndirmə (yanvar–iyun 2026 faktı), ən böyük bölmələr, doğulmalar (Əsas ssenari):

| bölmə | h1_2026_observed | nowcast_fy_2026 | allocation_2026_before | adjusted_2026 | change_2026_pct | h1_2027_implied_before | h1_2027_implied |
|---|---|---|---|---|---|---|---|
| G | 1 921.0 | 4 225.3 | 5 143.1 | 4 334.8 | -15.7 | 2 379.8 | 2 198.4 |
| M | 843.0 | 1 806.0 | 1 630.9 | 1 852.8 | 13.6 | 774.8 | 825.9 |
| N | 540.0 | 1 217.0 | 1 207.9 | 1 248.5 | 3.4 | 545.5 | 554.4 |
| C | 503.0 | 1 088.6 | 1 128.8 | 1 116.8 | -1.1 | 530.9 | 528.1 |
| F | 501.0 | 1 183.9 | 996.0 | 1 214.6 | 22.0 | 428.9 | 474.6 |
| H | 342.0 | 750.8 | 849.9 | 770.2 | -9.4 | 394.0 | 376.1 |

KOS-un işçi sayında payı: qayda **kombinasiya: FE + size | lövbərlənmiş** (ən yaxşı namizəd struktur: FE + size | lövbərlənmiş, sıfır modelə qarşı DM p = 0,62); son mənbə ilində tətbiq olunan: size (size: uyğun).
<!-- /AUTO:v2_alloc -->

Proqnozlaşdırılmayan komponent və müşahidə ilindəki boşluqlar:

HHI-nin "iri müəssisələr ≥ 30 mln AZN" variantı v2-də tavanları atılmış qruplar (AGR, EDU, HEA) üçün də hesablanır: KOS hissəsinin
supremumu Σ S², döşəmə yalnız iri sinfə tətbiq olunur. Variant yalnız **mümkün olmadıqda** (iri vahidlərin sayı × 30 mln > iri sinfin
buraxılışı) boş qalır və səbəbi yazılır. EDU üçün bu, proqnoz illərində baş verir, ona görə id proqnozlaşdırılmır; HEA üçün yalnız
2023–2024 müşahidə illərində (proqnoz illərində fərziyyə mümkündür və dəyərlər verilir) — `scope = history` sətri həmin boş müşahidə
dəyərlərini izah edir.

<!-- AUTO:v2_notforecast -->
`FR12_not_forecast.csv`: 2 id. conc: 2.

| id | səbəb (azərbaycanca) |
|---|---|
| fr12:conc:hhi_upper_floor30:EDU | Fərziyyə mümkün deyil (2025, 2026, 2027, 2028): 19 iri vahidin hər birinin gəliri ≥ 30 mln AZN olsaydı, iri sinfin buraxılışını aşardı (iri pay 9.2–9.2%). Əsas yuxarı hədd (hhi_upper) və 15 mln AZN variantı verilir. |
| fr12:conc:hhi_upper_floor30:HEA | Müşahidə illərində (2023, 2024) fərziyyə mümkün deyil: 56 iri vahidin hər birinin gəliri ≥ 30 mln AZN olsaydı (cəmi ≥ 1 680 mln AZN), iri sinfin buraxılışını (1 122–1 394 mln AZN; iri pay 27.0–29.7%) aşardı — həmin illərdə dəyər yoxdur. Proqnoz illərində fərziyyə mümkündür və dəyər verilir; əsas yuxarı hədd (hhi_upper) və 15 mln AZN variantı bütün illər üçün verilir. |
<!-- /AUTO:v2_notforecast -->

### 20.4 B qatının ekonometrikası (sintetik məlumat — texniki nümayiş)

(a) NACE bölməsi × region × il üzrə girişlərin sayı: Puasson və mənfi binomial (NB2), insident nisbətləri, bazar üzrə klaster;
(b) çıxış: müəssisə-il risk dəstində diskret zamanlı təhlükə modeli (logit və cloglog, tezlik çəkiləri, bölmə × region üzrə klaster),
Kaplan–Meyer ilə proqnozlaşdırılan sağ qalma müqayisəsi; (c) bölmə-il üzrə Boone indikatoru (95% EI) və birləşdirilmiş Boone reqressiyası;
(d) struktur–davranış–nəticə (PCM ln HHI üzrə; **endogenlik**: konsentrasiya və marja birgə müəyyənləşir, əmsal səbəb-nəticə deyil;
idxal payı reyestrdə yoxdur, ixrac intensivliyi istifadə olunur); (e) bazar payı mobilliyinin determinantları; (f) yeni müəssisələrin
ölçüsü və girişdən sonrakı artım (kohort təhlili, gecikmiş asılı dəyişən yoxdur); (g) generatorun həqiqi parametrlərinin bərpası.
Eyni kod REAL rejimdə işləyir (swap testi), nəticələr `FR12_FIRM_econ_*.csv`.

<!-- AUTO:v2_econ -->
Rejim: **SYNTHETIC** (sintetik məlumat — texniki nümayiş). Nəticələr: `FR12_SYNTHETIC_econ_*.csv`.

| model | model (azərbaycanca) | n | şərh (azərbaycanca) |
|---|---|---|---|
| entry_poisson | Girişlərin sayı: Puasson (region və il sabit effektləri) | 6557 | sintetik məlumat — texniki nümayiş: tələb artımı 1 faiz bəndi yüksək olduqda girişlərin sayı +0.54% dəyişir (IRR 1.005); HHI 10% yüksək olduqda -4.6%, bazar həcmi 10% böyük olduqda +3.9%. |
| entry_nb2 | Girişlərin sayı: mənfi binomial NB2 (region və il sabit effektləri) | 6557 | sintetik məlumat — texniki nümayiş: tələb artımı 1 faiz bəndi yüksək olduqda girişlərin sayı +0.85% dəyişir (IRR 1.009); HHI 10% yüksək olduqda -3.9%, bazar həcmi 10% böyük olduqda +2.7%. Həddən artıq dispersiya α = 6.47 (LR p = 0): Puasson SE-ləri yalnız klaster düzəlişi ilə etibarlıdır. |
| entry_poisson_secfe | Girişlərin sayı: Puasson + bölmə sabit effektləri | 6557 | sintetik məlumat — texniki nümayiş: tələb artımı 1 faiz bəndi yüksək olduqda girişlərin sayı +0.11% dəyişir (IRR 1.001); HHI 10% yüksək olduqda -2.2%, bazar həcmi 10% böyük olduqda +3.4%. |
| exit_logit | Çıxış: diskret zamanlı təhlükə (hazard) modeli, logit | 76148 | sintetik məlumat — texniki nümayiş: iri müəssisələr üçün şans nisbəti 0.029, orta 0.079, kiçik 0.298 (mikro = 1); 1 yaşda 1.81, 2 yaşda 2.32 (10+ yaş = 1); dövlət mülkiyyəti 0.65. |
| exit_cloglog | Çıxış: diskret zamanlı təhlükə (hazard) modeli, cloglog | 76148 | sintetik məlumat — texniki nümayiş: iri müəssisələr üçün təhlükə nisbəti 0.030, orta 0.079, kiçik 0.299 (mikro = 1); 1 yaşda 1.81, 2 yaşda 2.31 (10+ yaş = 1); dövlət mülkiyyəti 0.65. |
| scp | Struktur–davranış–nəticə: marja (PCM) HHI üzrə | 595 | sintetik məlumat — texniki nümayiş: ln HHI 1 vahid artdıqda marja -0.24 faiz bəndi dəyişir (p = 0.81). Endogenlik: konsentrasiya və marja birgə müəyyənləşir (Demsets) — səbəb-nəticə əlaqəsi deyil, şərti assosiasiyadır; idxal payı reyestrdə yoxdur. |
| mob_instability | Bazar paylarının qeyri-sabitliyinin determinantları | 510 | sintetik məlumat — texniki nümayiş: ln HHI(t−1) 1 vahid yüksək olduqda payların qeyri-sabitliyi -2.22 f.b., giriş əmsalı 1 f.b. yüksək olduqda +0.050 f.b. dəyişir. |
| mob_rank | Sıra mobilliyinin determinantları | 510 | sintetik məlumat — texniki nümayiş: sıra mobilliyi (1 − Spirmen ρ) üzrə ln HHI(t−1) əmsalı -0.0014, giriş əmsalı +0.0002. |
| entrant_profile | Yeni müəssisələrin nisbi ölçüsü: yaş profili | 91844 | sintetik məlumat — texniki nümayiş: qeydiyyat ilində müəssisə eyni bölmə-il-ölçü qrupundakı 5+ yaşlı müəssisələrdən -50% kiçikdir; 2 yaşda fərq -0.2%. |
| postentry_growth | Girişdən sonrakı artım (nisbi ölçünün dəyişməsi) yaş üzrə | 76148 | sintetik məlumat — texniki nümayiş: nisbi ölçünün illik artımı 2 yaşda +0.690 log vahid (5+ yaşa nisbətən); asılı dəyişən fərqdir, sağ tərəfdə gecikmiş asılı dəyişən yoxdur. |
| boone_pooled | Boone indikatoru: birləşdirilmiş reqressiya (ümumi meyl + trend) | 84107 | sintetik məlumat — texniki nümayiş: ümumi Boone meyli -4.06 — xərci 1% yüksək müəssisənin mənfəəti 4.06% aşağıdır; trend +0.006 ildə (mənfi trend = rəqabətin güclənməsi). Yalnız mənfəətli müəssisələr: seçim əyilməsi meyli sıfıra doğru çəkir. |
| boone_sector | Boone indikatoru: bölmələr üzrə meyllər | 84107 | sintetik məlumat — texniki nümayiş: bölmələr üzrə Boone meylləri -11.74 ilə -2.19 arasındadır; daha mənfi = daha sərt rəqabət (sıralama kimi oxunur). |
| bərpa | Parametr bərpası (G1, G2, (b)) | 57 | sintetik məlumat — texniki nümayiş: 49 / 57 həqiqi dəyər 95% EI daxilindədir; G1 95%; G2 67%; (b) cloglog 85%; (b) logit 85% |

Parametr bərpası (həqiqi dəyər 95% EI daxilində):

| blok | parametrlər | əhatə olunur |
|---|---|---|
| G1 gəlir–xərc elastikliyi (qeydlər, bölmə × il × ölçü sabit effektləri) | 22 | 21 |
| G2 çıxış təhlükəsi (şərti Puasson, xana-il təbəqələri) | 9 | 6 |
| (b) cloglog, additiv bölmə/region/il sabit effektləri | 13 | 11 |
| (b) logit, additiv bölmə/region/il sabit effektləri | 13 | 11 |
<!-- /AUTO:v2_econ -->

### 20.5 Tənliklər reyestri

<!-- AUTO:v2_registry -->
`FR12_equations.json`: 69 tənlik, proqnozda istifadə olunan 13, sintetik 15; bütün qiymətləndirilmiş əmsallar reyestrin statsmodels yenidən hesablaması ilə üst-üstə düşür (uyğunsuzluq: 0).

| istifadə olunur | hökm | tənlik |
|---|---|---|
| xeyr | qeyri-stabil | 7 |
| xeyr | qismən stabil | 40 |
| xeyr | stabil | 9 |
| bəli | qismən stabil | 10 |
| bəli | stabil | 3 |
<!-- /AUTO:v2_registry -->

### 20.6 Ssenari mühərriki

`run(overrides, scenario, upstream)` FR1 və FR10-un nəticələrini (və ya CSV baza yollarını) qəbul edir; ekzogen yollar, əmsallar və
IO rıçaqları dəyişdirilə bilər; `selftest()` notebook-un nəticələrini 10⁻⁸ dəqiqliklə təkrarlamalıdır (son xana bunu yoxlayır).

<!-- AUTO:v2_engine -->
`microlib/engines/fr12.py`: 39 ekzogen yol (FR1 sektor ƏDV, faiz, kredit, qeyri-neft ÜDM; FR10 regional buraxılış; marja fərziyyələri), 8 redaktə edilə bilən əmsal (giriş/çıxış sürücüləri və qırılma termini), 14 rıçaq (IO ssenarisi: ε, θ, ΔN, birləşmə payları, xərc şoku, idxal payı, dövlət payı σ, λ). Yuxarı axın: FR1 və FR10 (`run_chain`). Öz-özünü yoxlama: keçdi (maks. nisbi fərq 3,0·10⁻¹⁴); bir ssenari 0,12 s.
<!-- /AUTO:v2_engine -->

### 20.7 Dayanıqlıq və əmsal həssaslığı

Hökm qaydası: rekursiv və bir ili çıxarmaqla qiymətləndirmədə işarə saxlanılırsa və Chow/CUSUM p > 0,05-dirsə "stabil"; rekursiv
yolun son yarısında işarə dəyişirsə və ya Chow p < 0,01-dirsə "qeyri-stabil"; qalan hallarda "qismən stabil". T = 5 olduğundan
panel tənliklərinin testləri zəifdir.

<!-- AUTO:v2_robust -->
| tənlik | hökm | failed_test |
|---|---|---|
| FR12.act_lnB_null | stabil | — |
| FR12.act_lnB_dem | qismən stabil | bir ili çıxarmaqla işarə dəyişir: dem |
| FR12.act_exit_null | qismən stabil | bir ili çıxarmaqla işarə dəyişir: d2022 |
| FR12.reg_lnB_null | qismən stabil | testlər mümkün deyil / tam deyil |
| FR12.reg_lnB_reg_lend | qismən stabil | rekursiv işarə dəyişir: reg; bir ili çıxarmaqla işarə dəyişir: reg, lend |
| FR12.reg_exit_null | qismən stabil | testlər mümkün deyil / tam deyil |
| FR12.reg_exit_non | stabil | — |
| FR12.sme_lo_null | qismən stabil | testlər mümkün deyil / tam deyil |
| FR12.smeemp_lo_null | qismən stabil | testlər mümkün deyil / tam deyil |
| FR12.smeemp_lo_size | stabil | — |
| FR12.conc_bounds_map | qismən stabil | testlər mümkün deyil / tam deyil |
| FR12.alloc_sections | qismən stabil | testlər mümkün deyil / tam deyil |
| FR12.alloc_sections_h1 | qismən stabil | testlər mümkün deyil / tam deyil |

Əmsal həssaslığı (±1 SE, 2030, Əsas ssenari) — hər başlıq göstəricisi üçün ən böyük təsir:

| əsas nəticə (azərbaycanca) | eq_id | əmsal | effect_minus_1se_pct | effect_plus_1se_pct |
|---|---|---|---|---|
| qeydiyyatdakı subyektlər, bütün sahələr (006) | FR12.act_lnB_null | brk | -0.200 | +0.201 |
| giriş əmsalı, bütün sahələr (006) | FR12.act_lnB_null | brk | -0.452 | +0.454 |
| çıxış əmsalı, bütün sahələr (006) | FR12.act_exit_null | d2022 | +1.201 | -1.201 |
| statistik vahidlər, bütün regionlar | FR12.reg_lnB_reg_lend | lend | +0.428 | -0.420 |
<!-- /AUTO:v2_robust -->
