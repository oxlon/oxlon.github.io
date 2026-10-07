# Ev təsərrüfatları faylı — mikrosimulyasiyanın giriş faylı (FR3)

> **DİQQƏT: sintetik fayllar (PU_households_SYNTHETIC.csv və PU_households_SYNTHETIC.xlsx) real ev təsərrüfatı məlumatı deyil.**
> Faylda heç bir real ev təsərrüfatı, şəxs və ya sorğu cavabı yoxdur. Fayl təsadüfi yaradılıb (policyunit/synth_households.py, seed 20241)
> və DSK-nın dərc etdiyi aqreqatlara kalibrlənib (policyunit/ms_calib.py). Nəticələr metodologiyanın texniki nümayişidir; real təhlil üçün
> Nazirlik ev təsərrüfatları büdcə tədqiqatının (EBT) mikroməlumatını yükləməlidir.

## Tərkib
12 000 ev təsərrüfatı, 51 677 şəxs. Hər sətir bir şəxsdir; ev səviyyəli sütunlar (çəki, region, şəhər/kənd, mülkiyyət gəliri, xaricdən
pul köçürmələri, ev arası transfertlər, istehlak kateqoriyaları) hər üzvün sətrində təkrarlanır (PU_households_column_map.csv, sütun
«level» = H). Pul məbləğləri AZN/ay, baza ili 2024. Fəaliyyət statusu: muzdlu işçi (NACE bölməsi, dövlət/qeyri-dövlət, vergi rejimi —
dövlət və neft-qaz / qeyri-neft özəl, büdcə təşkilatı), öz hesabına (qeyri-formal), kənd təsərrüfatı, işsiz, pensiyaçı, tələbə,
qeyri-fəal, uşaq.

## Kalibrləmə hədəfləri (2024; hamısı kalibrləmə nümunəsi daxilindədir)
Əhali 10,15 mln; şəhər payı; NACE bölmələri üzrə muzdlu işçilər (DSK 2.12 / MikroUnit FR4); dövlət sektoru işçiləri; öz hesabına kənd
təsərrüfatı və qeyri-kənd təsərrüfatı məşğulları (İQS); işsizlər; pensiyaçılar (DSMF xərci / orta pensiya); dövlət və qeyri-dövlət əmək
haqqı fondu; maaşların sektor × interval paylanması (DSK 004_11, noyabr 2024); adambaşına gəlir mənbələr üzrə (DSK e002); gəlir desilləri
(cədvəl 25); istehlak desilləri və kateqoriya səbətləri (cədvəl 53/54); ÜSY alanlar və orta məbləğ (DSMF, 01.07.2024); yoxsulluq səviyyəsi
5,3 % (xətt 270,1 AZN) — uzlaşdırma əmsalı kappa ilə. Uyğunluq hesabatı: output/V_microsim_calibration_2024.csv (2018 üçün
V_microsim_calibration_2018.csv).

Cari parametrlər (avtomatik, çıxışlardan): <!-- AUTO:ms_params -->EBT–inzibati uzlaşdırma amilləri: xalis maaş 0,894, pensiya 1,156, digər müavinətlər 1,203. ÜSY müraciət qaydası P = min(1; a × (boşluq/(üzv × meyar))^γ): a = 1,617, γ = 1,5. Kappa = 1,212: kappa olmadan adambaşına istehlakı 270,1 AZN-dən aşağı olanların payı 17,1 % olardı (rəsmi 5,3 %).<!-- /AUTO:ms_params -->

## Kappa haqqında
DSK-nın dərc etdiyi istehlak desilləri ilə rəsmi yoxsulluq səviyyəsi adambaşına əsasda bir-biri ilə uyğun gəlmir. DSK-nın yoxsulluq
aqreqatının metodikası cədvəllərdə açıqlanmır, ona görə istehlak aqreqatı kappa ilə vurularaq rəsmi səviyyə bərpa edilir. Real EBT
mikroməlumatı ilə bu əmsal 1-ə yaxın olmalıdır.

## Faylı necə əvəz etmək olar
Nazirliyin məlumatını eyni sxemdə data/households/PU_households.csv (və ya .xlsx, vərəq «data») kimi saxlayın və mühit dəyişəni
POLICY_HH_MODE=REAL təyin edin (və ya POLICY_HH_PATH ilə faylın yolunu göstərin). Sütun adları ingilis və ya Azərbaycan dilində ola bilər
(PU_households_column_map.csv). Şablon: PU_households_TEMPLATE.csv və PU_households_TEMPLATE.xlsx (bir ev təsərrüfatı nümunəsi).
«data_status» sütunu olmadıqda və ya su nişanından fərqli olduqda fayl REAL sayılır. Əmək haqqı hesablanmış (wage_gross) və ya xalis
(wage_net) verilə bilər — xalisdən hesablanmışa keçid vergi qaydalarının tərsinə çevrilməsi ilə aparılır (taxben.net_to_gross). Real faylda
utsy_u = 0 ÜSY alan, 1 almayan ev təsərrüfatıdır. İstəyə görə PU_households.calibration.json (baza ili, kappa, amillər) əlavə edilir;
yoxdursa bütün amillər 1-dir (məlumat EBT anlayışındadır).

## Yoxlama (hh_data.validate)
Məcburi sütunlar, rəqəmsal dəyərlər, mənfi dəyərlər, fəaliyyət statusunun kodları, ev daxilində eyni çəki, şəxs identifikatorunun
təkrarlanmaması; xəbərdarlıq: qeyri-muzdlu şəxsdə əmək haqqı. Səhvlər icranı dayandırır, xəbərdarlıqlar dayandırmır.

## Məxfilik
Ev və şəxs identifikatorları psevdonim olmalıdır; real məlumatla nəticələr yalnız Nazirliyin sistemində saxlanılır.

## Real məlumat yükləndikdə nə dəyişir
P3_microsim_* və V_microsim_* fayllarında «SİNTETİK» qeydi götürülür, nəticənin meta məlumatında data_mode = REAL olur; kalibrləmə
yalnız çəkilərin yoxlanmasına çevrilir; kappa, ÜSY müraciət ehtimalı və desil uyğunlaşdırması lazım olmur.
