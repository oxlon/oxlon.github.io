# Sosial və əmək bazarı mikrosimulyasiyası — metodologiya (MİİS §15.5.4, FR3)

> **SİNTETİK — real ev təsərrüfatı məlumatı deyil.** Bütün nəticələr DSK aqreqatlarına kalibrlənmiş sintetik fayl üzərində
> hesablanıb və metodologiyanın texniki nümayişidir. Nazirlik EBT mikroməlumatını yükləyəndə (bölmə 9) eyni kod real nəticə verir.

## 1. Tələb və qəbul meyarı
TT FR3: «Sistem siyasət ssenarisi üzrə məşğulluq, gəlir bölgüsü (Gini əmsalı) və yoxsulluq səviyyəsi göstəricilərinin dəyişimini
hesablayır.» Mühərrik `policyunit/eng_microsim.py` (`run(scenario, ctx) -> Result`) hər ssenari və il (2024–2030) üçün baza və ssenari
hesablayır və fərqi vahid cədvəl formatında (OUT_COLS) qaytarır: məşğulluq (formal / qeyri-formal / 19 NACE bölməsi), orta və median
gəlir, desillər, Gini (gəlir və istehlak), yoxsulluq səviyyəsi, dərinliyi və kəskinliyi üç xətt üzrə, qazanan/uduzanlar, statik fiskal təsir.

## 2. Məlumat
**Sintetik fayl** (`data/households/PU_households_SYNTHETIC.csv/.xlsx`, 12 000 ev, 51 677 şəxs; sxem — `PU_households_column_map.csv`).
Generator (`synth_households.py`): region (14 iqtisadi rayon) və şəhər/kənd, ev ölçüsü, yaş/cins, fəaliyyət statusu; muzdlu işçilərin
maaşı DSK 004_11 (noyabr 2024, sektor × maaş intervalı) paylanmasından, yuxarı açıq interval Pareto ilə (sektorun orta maaşına — DSK 004_2 —
uyğunlaşdırılır); pensiya, digər müavinətlər, mülkiyyət gəliri, pul köçürmələri, ev arası transfertlər, istehlak küyü.
**Kalibrləmə** (`ms_calib.py`), hamısı IN-SAMPLE:
1. *Entropiya (raking/GREG tipli) çəkiləndirmə* — sərt hədəflər: əhali, şəhər əhalisi, 19 bölmə üzrə muzdlu işçilər, dövlət sektoru işçiləri,
   öz hesabına k/t və qeyri-k/t məşğullar, işsizlər, pensiyaçılar, uşaqlar, dövlət və qeyri-dövlət əmək haqqı fondu; yumşaq (cəzalı) hədəflər:
   DSK desil quruluşu (hər desildə 10 % ev, desillər üzrə şəxs sayı), məşğulluq və pensiya gəlirinin desillər üzrə səviyyəsi (cədvəl 25).
2. *EBT–inzibati uzlaşdırma amilləri* siyasətə həssas mənbələr üçün (xalis maaş, pensiya, digər müavinətlər) — vergi və xərclər
   inzibati məbləğlərlə, paylanma EBT anlayışı ilə ölçülür.
3. *ÜSY müraciət ehtimalı* P = min(1; a × (boşluq/(üzv × meyar))^γ); `a` DSMF alanlarına (266,3 min nəfər), γ orta məbləğə
   (109,6 AZN/nəfər) uyğunlaşdırılır. Siyasət ssenarisində baza alanları müraciəti saxlayır (gəlir artımı ilə ÜSY-dən sıçrayışla çıxış yoxdur).
4. *Desil uyğunlaşdırması* yalnız siyasət olmayan mənbələrdə (özünüməşğulluq, k/t, mülkiyyət, transfertlər, köçürmələr) — cədvəl 25.
5. *İstehlak* cədvəl 53/54 desil səviyyələrinə və kateqoriya səbətlərinə (13 COICOP-a yaxın kateqoriya).
6. *Kappa*: dərc olunmuş istehlak desilləri ilə rəsmi yoxsulluq səviyyəsi (5,3 %, 270,1 AZN) adambaşına əsasda uyğun gəlmir;
   istehlak aqreqatı kappa ilə vurularaq rəsmi səviyyə bərpa edilir (2018-də kappa ≈ 1,0).

Kalibrləmə parametrləri (avtomatik, çıxışlardan): <!-- AUTO:ms_params -->EBT–inzibati uzlaşdırma amilləri: xalis maaş 0,894, pensiya 1,156, digər müavinətlər 1,203. ÜSY müraciət qaydası P = min(1; a × (boşluq/(üzv × meyar))^γ): a = 1,617, γ = 1,5. Kappa = 1,212: kappa olmadan adambaşına istehlakı 270,1 AZN-dən aşağı olanların payı 17,1 % olardı (rəsmi 5,3 %).<!-- /AUTO:ms_params -->

<!-- AUTO:ms_fit -->**Uyğunluq (2024, `V_microsim_calibration_2024.csv`):** gəlir mənbələri dəqiq (cəmi 359,2 AZN); gəlir desillərinin maksimal sapması 7,6 % (D1 199,4 / 201,2; D10 14,5 / 15,0); istehlak desilləri dəqiq, orta istehlak 2,2 %; yoxsulluq 5,30 % (hədəf 5,3, kappa ilə); şəhər 4,8 / 4,4 və kənd 5,9 / 6,2 % (hədəf deyil); ÜSY alanlar 265,6 / 266,3 min, ailələr 55,0 / 61,5 min, orta məbləğ 105,6 / 109,6 AZN; orta maaş 1 010 / 1 009 AZN. Gini: gəlir 21,2, istehlak 18,9, DSK desil cədvəlindən aşağı sərhəd 20,9 (DSK Gini dərc etmir).<!-- /AUTO:ms_fit -->

## 3. Vergi-müavinət qaydaları (`config/tax_benefit.csv`, `taxben.py`)
Hər parametr tarixli (`valid_from`), mənbəli və statusludur: **V** — 2026-10-06 onlayn yoxlanılıb (URL), **D** — DSK faylı, **K** — məlum,
yoxlanılmayıb (Nazirliklə təsdiq lazımdır). İllik dəyər = 12 ayın 1-i günü qüvvədə olan dəyərlərin ortası (MikroUnit FR1 ilə eyni konvensiya;
məs. 2019 MƏH = (2×130 + 6×180 + 4×250)/12 = 195 AZN).
- Gəlir vergisi: dövlət + neft-qaz — 14 % ≤ 2 500, 350 + 25 % artıq hissə, 200 AZN azad (gəlir ≤ 2 500 olduqda) [V]; qeyri-neft özəl —
  2019–2025 ≤ 8 000 AZN 0 % [V], > 8 000 14 % [K]; 2026: 3 % ≤ 2 500, 75 + 10 %, 625 + 14 %; 2027: 5 %; 2028-dən 7 % [V]; 2018: ümumi
  rejim, 173 AZN azad [K].
- Sosial sığorta: dövlət/neft 3 % + 22 % [V]; qeyri-neft özəl 2019-dan ≤ 200 AZN 3 % + 22 %, artıq hissə 10 % + 15 % [V]; 2026-dan
  > 8 000 hissədə işəgötürən 11 % [V]; 2018: 3 % + 22 % [K]. İşsizlik sığortası 0,5 % + 0,5 % (2018-dən) [V].
- İcbari tibbi sığorta (2021-dən) 2 % + 2 % hədd qədər, 0,5 % artıq hissə; hədd dövlət/neft 8 000, qeyri-neft özəl 2026-dan 2 500 [V];
  2021–2022 özəl sektor güzəşti 50 % [K].
- Minimum əmək haqqı (DSK 004_1) [D]; 2026 — 400 AZN [V]; 2027+ qanun yoxdur → MikroUnit FR3 baza yolu (449 → 535 AZN).
- Minimum əmək pensiyası 110 → 116 → 119,75 → 160 → 200 → 240 → 280 → 320 AZN [V/K]; indeksasiya = əvvəlki ilin orta maaş artımı (qayda [V];
  2025 8,1 %, 2026 9,3 % [V]); qanun olmayan illər üçün FR1 maaş yolundan.
- ÜSY: ehtiyac meyarı 130 (2018) … 270 (2024), 285 (2025), 300 (2026) [V]; məbləğ = üzv sayı × meyar − ailənin orta aylıq gəliri,
  yuxarı hədd yoxdur [V, dsmf.gov.az]. Yaşayış minimumu 2025/2026 ümumi və qruplar üzrə [V].
- ƏDV 18 %, ƏDV geri qaytarma 15 % / 10 %, sadələşdirilmiş vergi 2 % [K]. DSK yoxsulluq xətti 2015–2024 [D].

## 4. Siyasət alətləri və adapterlər (NFR4)
Alətlər `config/instruments.csv`-dən, mikrosimulyasiya üçün tərcümə `config/adapters.csv` (engine = microsim) sətirlərindən oxunur:
`param:<tax_benefit parametri>[@rejim]` (pct/add/level), `pol:<açar>` və ya `custom:<funksiya>`. Birbaşa alətlər: `min_wage`,
`pension_index`, `tsa_benefit` (ödəniş ×), `tsa_need` (ehtiyac meyarı), `min_pension`, `pit_rate` (bütün pillələr ± f.b.),
`pit_nonoil_private` (≤ 2 500 pilləsi), `ssc_employee`, `public_wage` (büdcə təşkilatları), `vat_rate`, `fuel_price`, `utility_tariff`,
`fx_deval`, `import_tariff`, `consumer_price` (kateqoriya), `agri_subsidy`, `sector_jobs`. Makro alətlər (`pub_invest`, `gov_current`)
yalnız əlaqə ilə işləyir. Yeni ssenari üçün yalnız JSON faylı kifayətdir; yeni alət = instruments + adapters sətri.

## 5. Davranış fərziyyələri və makro/IO əlaqəsi
- **Statik, birinci raund** (defolt): qiymətlər, məşğulluq və maaş strukturu sabit; **minimum əmək haqqı yalnız tam ştatlı formal işçilərə
  döşəmə kimi, yayılma (spill-over) OLMADAN** — bu, diapazonun aşağı ucudur. **Etiketli yayılma variantı** (nüvənin büdcə əmək haqqı fondu
  fərziyyəsi ilə eyni): minimumdan 25 %-ə qədər yuxarı maaşlar artımın yarısını alır (`eng_microsim.SPILL_CORE`; ssenaridə
  `"microsim_options": {"mw_spill": 0.5, "mw_spill_band": 1.25}`); `min_wage` olan hər ssenaridə əsas göstəricilər əlavə olaraq
  `<göstərici>@spill` sətirləri kimi verilir (diapazonun yuxarı ucu); istehlak dəyişməsi = ev təsərrüfatının orta istehlak meyli ×
  gəlir dəyişməsi; qiymət dəyişmələri desil səbətləri ilə real gəlirə və istehlaka (yükün bölüşdürülməsi).
- **ƏDV / qiymət alətləri**: ƏDV-yə cəlb olunan pay (ərzaq 0,55, səhiyyə 0,4, təhsil 0,2 …), idxal payı və məzənnənin ötürülməsi 0,30,
  nəqliyyatda yanacaq payı 0,35, mənzil xərcində kommunal payı 0,75 — **fərziyyələr**; IO mühərriki qiymət nəticəsi verdikdə
  (`io_price:<kod>`), kateqoriya → IO məhsul xəritəsi (`ms_links.CAT_IO`) ilə onlar istifadə olunur (dolayı təsirlər daxil).
- **Məşğulluq əlaqəsi** (koordinator qaydası): formal iş yerlərinin sektor dəyişməsi MikroUnit FR4 `sector_hired:<bölmə>`-dən (yoxdursa IO
  `io_emp`), FR1 `emp` (ümumi İQS, elastiklik kiçik) yox. Dəyişiklik *çəki bölünməsi* ilə tətbiq olunur: hər namizəd ev iki nüsxəyə
  bölünür (θ və 1 − θ çəkili), dəyişən nüsxədə bir şəxs işsizlikdən (sonra qeyri-fəallardan) muzdlu işə keçir və eyni sektordan donor maaşı
  alır, ya da əksinə — cəmlər dəqiqdir, təsadüfi küy yoxdur. Orta maaş dəyişməsi FR1 `wage_nominal`-dan yalnız makro alətlər üçün götürülür.
- **İsteğe bağlı davranış qatı (etiketli, Tier D):** formallaşma elastikliyi η = 0,7 (xalis maaş / işəgötürən xərci nisbətinə) — yalnız NFR1
  testində ayrıca sütun kimi; 2019 nəticəsinə kalibrlənməyib.
- **ÜSY xərcinin vahid tərifi** (nüvə ilə razılaşdırılıb): benefisiar əsaslı — alan ailələr üzrə max(0; üzv × meyar − gəlir) cəmi;
  funksiya `eng_microsim.tsa_spending(year, pct, need_pct)` (baza, ssenari, fərq mln AZN, alanlar).
- **Pensiya xərcinin vahid bazası** (nüvə ilə): `config/fiscal_params.csv` `pension_spending` (`fiscal.base_value`, FR1 orta pensiya
  yolu ilə); model yalnız faiz dəyişməsini verir. `ms_fiscal:pensions` fərqi = BRÜT xərc (büdcədən DSMF-ə transfert);
  `fiscal_cost` = XALİS (müavinət + büdcə əmək xərci artımı − gəlir vergisi, sığorta haqları və ƏDV daxilolmalarının artımı).
- **Fiskal xərc** (mln AZN/il, statik): Δ(pensiya + ÜSY + digər müavinət + büdcə təşkilatlarının əmək xərci) − Δ(gəlir vergisi + sosial,
  işsizlik, tibbi sığorta + ƏDV). Pensiya artımı MikroUnit FR1 v2.3.5 kimi **dövlət büdcəsindən DSMF-ə transfert** konsepsiyasındadır.

## 6. Göstəricilər və yoxsulluq xətləri
Yoxsulluq xətləri baza səviyyəsində sabit saxlanılır (ehtiyac meyarının özü dəyişsə də): (i) **DSK rəsmi xətti** (270,1 AZN 2024; sonrakı
illər FR1 İQİ ilə) — istehlak × kappa; (ii) **ÜSY ehtiyac meyarı** — adambaşına real gəlir (EBT anlayışında aşağı olduğu üçün səviyyə
yüksəkdir, ≈ 28 % 2024; dəyişmə istiqaməti üçün); (iii) **yaşayış minimumu** — gəlir. FGT(0,1,2): səviyyə, dərinlik, kəskinlik.
Gini — şəxslər üzrə adambaşına gəlir və istehlak (0–100). Desillər DSK qaydası ilə (evlərin 10 %-i, adambaşına gəlirə görə) baza
sıralamasında sabit; qazanan/uduzan: real adambaşına gəlir dəyişməsi > 0,5 AZN.

## 7. 2025–2030 üçün qocaldılma
`ms_uprate.py`: MikroUnit bazası (eyni vintaj, MD5 meta-da): FR1 orta nominal maaş, İQS məşğulluğu, işsizlik, İQİ; FR4 bölmələr üzrə
muzdlu işçilər — çəkilər bu strukturlara yenidən kalibrlənir; maaşlar FR1 maaş indeksi, digər xüsusi gəlirlər FR1 adambaşına sərəncamda qalan gəlir ilə (fərziyyə), pensiyalar
MikroUnit FR1 konvensiyası ilə — FR1 orta pensiya yolu (`fr1:pension`, proqnozda İQİ-yə indeksli) indeksi + minimum pensiya döşəməsi
(qanuni 2025/2026 artımları FR1 faktiki dəyərlərinə daxildir); minimum əmək haqqı 2026 qanuni 400 AZN, sonra MikroUnit `minwage_path.json`
(+6 %/il); ehtiyac meyarı 2027+ üçün real səviyyədə saxlanılır (İQİ ilə, fərziyyə); minimum pensiya qanuni son səviyyədə (320 AZN).

**Baza yolunun dinamikası.** İstehlak hər ev üçün öz nominal gəlirinin artımı ilə (baza ilinin istehlak meyli saxlanılır), digər xüsusi
gəlirlər FR1 adambaşına nominal sərəncamda qalan gəlir (`fr1:hhdisp_n`) ilə qocaldılır; yoxsulluq xətti FR1 İQİ ilə. Ona görə illik
dəyişmələr MikroUnit bazasından gəlir: 2025-də real gəlir artır (FR1 maaş +9,3 %, orta pensiya +12,5 %, İQİ +5,2 %), 2026-da FR1 nominal
maaş artımı (+2,6 %) İQİ-dən (+5,7 %) aşağıdır; ÜSY xərci ehtiyac meyarının qanuni addımları (270 → 285 → 300 AZN) ilə gəlir
artımının fərqini izləyir. 2025 üçün çəkilərin yenidən kalibrlənməsinin təsiri kiçikdir (yoxsulluq −0,09 f.b.).
<!-- AUTO:ms_baseline -->Baza yolu (`P3_microsim_baseline.csv`): gini: 2024 21,18, 2025 21,37, 2026 21,17, 2027 21,21, 2028 21,28, 2029 21,31, 2030 21,37; income_mean_pc: 2024 359,20, 2025 392,03, 2026 405,23, 2027 437,01, 2028 467,03, 2029 501,98, 2030 536,42; ms_fiscal:utsy: 2024 337, 2025 283, 2026 328, 2027 323, 2028 314, 2029 309, 2030 293; poverty_rate: 2024 5,30, 2025 4,15, 2026 4,32, 2027 3,88, 2028 3,50, 2029 3,03, 2030 2,71.<!-- /AUTO:ms_baseline -->


## 8. Validasiya (NFR1) — `V_microsim_*.csv`
- **In-sample** (2024 və 2018 kalibrləməsi): bölmə 2-dəki uyğunluq; yoxsulluq səviyyəsi kappa ilə qurulub — sübut deyil.
- **E1+E2 2019 paketi** (2018-ə kalibrlənmiş populyasiya; 2019/2020 nəticələri istifadə olunmayıb → dəyişmələr üzrə out-of-sample).
  Rəqəmlər (avtomatik): <!-- AUTO:ms_valid -->E1+E2 (2019 vs 2018; model — statik siyasət effekti, fakt — ümumi dəyişmə): wage_avg 0,49 vs 16,6; wage_state 1,07 vs 22,1; wage_nonstate 0,00 vs 11,2; hbs_employment_pc 4,86 vs 7,5; hbs_pensions_pc 2,48 vs 9,8; hbs_benefits_pc 2,59 vs 25,0; hbs_total_pc 2,03 vs 6,0; poverty_rate −0,86 vs −0,3; nonstate_employees 0,00 vs 9,4. Davranış qatı (η = 0,7): qeyri-dövlət muzdlu işçilər 5,9 %. İşarə uyğunluğu 78 %, 'model + trend' trend etalonunu 67 % halda üstələyir. E3 (2025 MƏH 345→400): < 500 AZN payı model 29,0 / 25,7 % (MƏH / + 5,6 % artım), fakt 25,8 %, etalon 37,8 %.<!-- /AUTO:ms_valid -->
  Şərh: statik minimum əmək haqqı döşəməsi orta maaş artımının yalnız kiçik hissəsini izah edir; qalan hissə əsasən 2019-da büdcə
  təşkilatlarında maaş artımlarıdır (paketdə olub, ölçüsü yoxlanılmayıb; `public_wage` aləti ilə modelləşdirilə bilər) və 2018 maaş
  paylanmasının 2024 formasından geri hesablanmasıdır (DSK-nın 2018 maaş intervalı cədvəli keşdə yoxdur). 2020 COVID ilini model tuta bilmir.
- **E3 2025 MƏH 345 → 400** (2024 paylanması → noyabr 2025 DSK 004_12) — rəqəmlər yuxarıdakı avtomatik blokda.
- Tolerantlıq Nazirliklə razılaşdırılmalıdır (Sorğuda 15.5.4 NFR1 cavabsızdır).

## 9. Məhdudiyyətlər və Nazirlikdən məlumat sorğusu
Məhdudiyyətlər: sintetik məlumat; DSK desil cədvəlləri ev təsərrüfatı desilləridir və rəsmi yoxsulluq səviyyəsi ilə uyğun gəlmir (kappa);
ÜSY uyğunluğu EBT gəliri ilə qiymətləndirilir → ehtiyac meyarı dəyişməsinin əhatə effekti yuxarı sərhəddir; 2030-dan sonra hesablanmır.
**Sorğu:** (a) EBT 2018–2025 anonimləşdirilmiş mikroməlumatı (çəkilər, gəlir mənbələri, istehlak, DSK yoxsulluq aqreqatı və ekvivalentlik
şkalası); (b) İQS 2018–2025 mikroməlumatı (formal/qeyri-formal); (c) DSK 004_11 maaş intervalı cədvəlləri 2017–2023; (d) DSMF: ÜSY
alanlar (ailə ölçüsü, gəlir, məbləğ intervalı, region), pensiyaçılar növ və məbləğ intervalı üzrə; (e) VXX: gəlir vergisi və sosial
ayırmalar gəlir intervalı və sektor üzrə; (f) 2019 büdcə təşkilatları maaş artımlarının ölçüsü; (g) DSK daxili Gini / desil nisbətləri.

## 10. Fayllar və əmrlər
Kod: `policyunit/{taxben, hh_data, synth_households, ms_rawdata, ms_targets, ms_calib, ms_uprate, ms_policy, ms_links, ms_metrics,
ms_indicators, eng_microsim, ms_outputs, ms_validate, ms_build}.py`; parametrlər `config/tax_benefit.csv`; məlumat `data/households/`;
testlər `tests/test_microsim.py`. Əmrlər: `python3 -m policyunit.ms_build` (fayl + kalibrləmə, ~1 dəq), `python3 -m policyunit.ms_outputs`
(P3_, ~45 san), `python3 -m policyunit.ms_validate` (V_), `python3 -m unittest tests.test_microsim`.
Çıxışlar: `P3_microsim_{indicators, headline, deciles, fiscal, employment, baseline}.csv`, `V_microsim_{calibration_2024, calibration_2018,
2019_package, 2025_minwage, summary}.csv` (hamısı `output/_catalog.csv`-də).
