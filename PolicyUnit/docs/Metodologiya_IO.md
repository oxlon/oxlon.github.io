# Girdi-çıxdı (IO) mühərriki — metodologiya (MİİS §15.5.4, FR2)

**Tələb (FR2):** «Sistem sektor əsaslı siyasət ssenarisi üçün təsirlənən sektorların siyahısını və hər biri üzrə kəmiyyət
təsirini (faiz dəyişimi) göstərir.» IO mühərriki (`policyunit/eng_io.py`) bu tələbi sabit əmsallı girdi-çıxdı modeli ilə
ödəyir (Blueprint Tier 2; CGE — əlavə dəyər, öhdəlik deyil). Bütün nəticələr **sübut səviyyəsi D**-dir: fərziyyələrə şərti
model kontrfaktiki (əks-faktual), ölçülmüş təsir deyil.

## 1. Məlumatlar
- **DSK təklif, istifadə və simmetrik girdi-çıxdı cədvəlləri** 2011, 2016, 2021 (benchmark illəri; min AZN, əsas qiymətlər;
  `data/io/raw/`, MD5 — `data/io/MANIFEST_md5.csv`). IO cədvəli 81 məhsul × 81 məhsuldur (CPA 2 rəqəm; DSK 41–43 və 45–47-ni
  birləşdirir). Cədvəl **ümumi axınlar** cədvəlidir (daxili + idxal); idxal məhsul üzrə bir sütundur, ayrıca idxal matrisi yoxdur.
- Mühasibat eyniliklərinin yoxlanışı (`IOT.check`): sütun balansı (buraxılış = aralıq istehlak + xalis məhsul vergiləri +
  əlavə dəyər) bütün illərdə 10⁻⁶-dan dəqiq; sətir balansı (buraxılış = aralıq + son tələb − idxal) 2021-də ən çox 0,65 % qalıq
  (bir məhsulda), 23 sektora aqreqasiyadan sonra 2·10⁻⁷. 2021 ümumi buraxılışı 131 736,7 mln AZN = MikroUnit FR1 `out_tot_n`.
- **Son tələb komponentləri:** ev təsərrüfatları, dövlət, ETXQKT (ev təsərrüfatlarına xidmət edən qeyri-kommersiya
  təşkilatları), əsas kapitalın ümumi yığımı, ehtiyatların dəyişməsi, (2011: qiymətlilər), ixrac. **Əlavə dəyərin komponentləri:** əmək
  ödənişi, sosial ayırmalar, xalis gəlir (mənfəət + qarışıq gəlir), istehsala vergilər, əsas kapitalın istehlakı.
- **Məşğulluq:** DSK `002_1-2en.xls` (İQS əsasında, NACE bölmələri üzrə, 1999–2025). B (mədənçıxarma) və C (emal) bölmələri
  IO sektorlarına MikroUnit FR10 sənaye işçilərinin NACE bölmələri üzrə payları ilə bölünür (`io_data.employment`).
  Məşğulluq əmsalı = nəfər / 1 mln AZN buraxılış.
- **Yeniləmə hədəfləri:** MikroUnit `FR1_annual_raw.csv` (11 sektor qrupu üzrə əlavə dəyər, buraxılış: cəmi, neft, emal, k/t,
  tikinti) və DSK `027en.xls` (ÜDM-in istifadəsi 1993–2025).
- **Validasiya:** DSK `001_5en.xlsx` (İQİ maddələr üzrə, dekabr/dekabr), Tarif Şurasının 30.06.2024 qərarı (mənbələr §7).

## 2. Sektor təsnifatı (`config/io_sectors.csv`, 23 sektor)
NACE bölmələrinə uyğun: A; B → OILGAS (06, 09) və MINOTH (05, 07, 08); C → FOOD (10–12), LIGHT (13–18), PETR (19), CHEM (20–22),
METMIN (23–25), MACH (26–33); D; E; F; G; H; I; J; K; L; M+N → BUS; O; P; Q; R+S → OTHSERV. Hər sektor üçün MikroUnit xəritəsi:
`fr1_group` (FR1 11 qrup: agr, min, man, elc, wat, con, trd, tou, tra, ict, oth), `fr4_sector_map` (FR4 19 bölmə),
`fr10_branch_map` (FR10 emal/mədən bölmələri). Neft-qaz (OILGAS + PETR) FR1 `out_oil_n` ilə dəqiq üst-üstə düşür
(2021: 39 426,9 mln AZN). Alətlərdə `target` IO kodu, FR1/FR4 kodu, NACE hərfi və ya CPA iki rəqəmli kodu ola bilər.

## 3. Daxili və idxal axınlarının ayrılması — idxal mütənasibliyi fərziyyəsi
DSK idxal matrisi dərc etmir. Hər məhsul *i* üçün idxal payı bütün **daxili** istifadələrdə (aralıq və son; ixrac istisna) eyni sayılır:
`s_i = m_i / (Σ_j Z_ij + f_i − e_i)`, `Z^d = (1 − s) ⊙ Z`, `Z^m = s ⊙ Z`; ixracın tam daxili istehsal olduğu qəbul edilir
(reeksport nəzərə alınmır). Nəticə: idxal sütunu tam bərpa olunur (qalıq < 1 min AZN). Məhdudiyyət: real idxal payları
istifadəçilər arasında fərqlənir (məs. neft konsorsiumlarının avadanlıq idxalı ƏKÜY-də yüksək, ev təsərrüfatlarında aşağı);
Nazirlikdən DSK-nın daxili idxal istifadə matrisi tələb olunmalıdır (§9).

## 4. Modellər (`policyunit/io_models.py`)
**4.1 Leontief kəmiyyət modeli.** `A^d = Z^d x̂⁻¹`, `L = (I − A^d)⁻¹`, `Δx = L Δf^d`. Multiplikatorlar (`P2_io_multipliers.csv`):
buraxılış `1'L`, əlavə dəyər `v'L`, əmək ödənişi `w'L` (əmək ödənişi + sosial ayırmalar), məşğulluq `e'L` (nəfər / 1 mln AZN
son tələb), idxal `m'L` (dolayı idxal tutumu). Son tələbin idxal hissəsi (məs. investisiya mallarının birbaşa idxalı) sızma kimi
ayrıca `io_imports_total`-a yazılır.

**4.2 Tip II (ev təsərrüfatları endogen).** Matris ev təsərrüfatı sətri və sütunu ilə genişlənir:
- gəlir sətri `h_j = (əmək ödənişi_j + α · xalis gəlir_j) / x_j`, burada α qarışıq gəlirin (fərdi sahibkarlar, fermerlər)
  payıdır və EBT nisbətinə kalibrlənir: özünüməşğulluq gəliri / muzdlu əmək gəliri = 117,6 / 135,1 (DSK e002en, 2024);
  α yalnız ev təsərrüfatlarının fəaliyyət göstərdiyi sektorların xalis gəlirinə tətbiq edilir (neft-qaz, neft emalı, maliyyə,
  enerji, dövlət, kimya, metallurgiya xaric). 2021: α = 0,65.
- istehlak sütunu `c_i = mpc · (1 − τ) · C^d_i / C`, istehlak strukturu IO ev təsərrüfatı sütunudur (MH-in EBT ilə
  uzlaşdırılmış istehlak strukturu); mpc = C / Y (≤ 0,95), τ = 0,10 (gəlir vergisi və sosial ayırmaların payı, fərziyyə).
Tip II nəticələr **yuxarı sərhəd** kimi təqdim olunur (`io_output_total_t2`, `io_emp_total_t2`).

**4.3 Leontief qiymət (xərc ötürülməsi) modeli.** Qiymət indeksi bazada 1:
`p_j = Σ_i a^d_ij p_i + Σ_i a^m_ij p^m_i + v_j + t_j` ⇒ `Δp' = (Δv' + Δp^m' A^m + Δt'_int) (I − A^d)⁻¹`.
Tənzimlənən (inzibati) qiymətlər **ekzogendir**: K sektorları üçün Δp_K verilir, qalanları
`Δp_N' = (Δp_K' A^d_KN + Δv_N' + …)(I − A^d_NN)⁻¹`. Şoklar: tənzimlənən yanacaq/elektrik/qaz/su qiymətləri, əmək xərci
(əmək haqqı və ya sosial ayırmalar), məhsuldarlıq (`Δv_j = −g v_j`), məhsul vergiləri (aksiz tipli, aralıq və son istifadə),
ƏDV (yalnız son istehlak — istehsalçı üçün əvəzləşdirilir; azad sektorlar: k/t, təhsil, səhiyyə, maliyyə, daşınmaz əmlak,
dövlət idarəetməsi), idxal rüsumu və məzənnə (idxal qiymətlərinə tam ötürmə). Fərziyyələr: tam ötürmə, sabit marjalar,
qiymət dəyişməsi kəmiyyətə təsir etmir. Homogenlik testi: bütün ilkin xərclər və idxal qiymətləri +10 % ⇒ bütün qiymətlər +10 %
(test `test_price_homogeneity`, dəqiqlik 10⁻⁸).

**4.4 İQİ effekti.** Səbət = IO ev təsərrüfatı istehlakı sektor üzrə (daxili + idxal, əsas qiymətlər) × (1 + xalis məhsul
vergisi dərəcəsi, təklif cədvəlindən). Maddə qiyməti = daxili hissə × Δp + idxal hissəsi × Δp^m; tənzimlənən pərakəndə qiymətlər
ev təsərrüfatı alışlarına birbaşa tətbiq olunur. Ticarət əlavələri əsas qiymətli cədvəldə ticarət sektorunun məhsuludur.

**4.5 Ghosh təklif modeli.** `B = x̂⁻¹ Z^d`, `G = (I − B)⁻¹`, `Δx' = Δv' G` (ilkin resursların — əlavə dəyər, idxal, vergilər —
dəyişməsi). **Məhdudiyyət:** sabit bölgü (çıxış) əmsalları tələbin tam elastik və girdilərin əvəzlənən olduğunu nəzərdə tutur;
kəmiyyət şərhi qeyri-real ola bilər (Oosterhaven 1988). Ghosh nəticələri yalnız irəli əlaqə və təklif şokunun yayılma
sırasının göstəricisi kimi, ayrıca metod etiketi ilə verilir («IO Ghosh təklif (məhdud şərh)»). Leontief nəticələri ilə
toplanmır.

**4.6 Əlaqə indeksləri və açar sektorlar.** Rasmussen geri əlaqə `BL_j = n·Σ_i L_ij / Σ L`; irəli əlaqə Ghosh tərsindən
`FL_i = n·Σ_j G_ij / Σ G` (Miller–Blair). Açar sektor: BL > 1 və FL > 1; «geri əlaqə yönümlü» (yalnız BL > 1), «irəli əlaqə
yönümlü», «zəif əlaqəli». Dispersiya əmsalı (`bl_cv`) təsirin genişliyini göstərir. **Hipotetik çıxarma** (Miller–Lahr):
sektorun sətir və sütunu çıxarılır (ümumi itki), yalnız sütun (geri), yalnız Ghosh sətri (irəli) — itki ümumi buraxılışın %-i ilə.

**4.7 Rəqabətlilik göstəriciləri** (`P2_io_competitiveness.csv`): əmək məhsuldarlığı (əlavə dəyər / məşğul), nominal vahid
əmək xərci (əmək ödənişi / əlavə dəyər), aylıq orta əmək ödənişi, idxal nüfuzu `m / (x − e + m)`, ixrac yönümü `e / x`, birbaşa
idxal tutumu, ixracda yaradılan daxili əlavə dəyərin payı `v̂ L e`. Emal sektorları üçün MikroUnit FR10 göstəriciləri
(sənayedə pay, məhsuldarlıq, qeyri-dövlət payı, 2026–2030 proqnoz artımı) birləşdirilir. RCA və effektiv müdafiə dərəcəsi üçün
HS səviyyəsində dünya ticarəti və tarif cədvəli lazımdır — növbəti mərhələ.

## 5. Siyasət alətləri və adapterlər
Alətlər `config/instruments.csv`, IO adapterləri `config/adapters.csv`-də (`engine = io`, `transform = custom:<funksiya>`,
`*k` miqyası). Yeni ssenari yalnız JSON ilə qurulur (NFR4). Kanallar:

| Alət | IO kanalı | Əsas fərziyyə |
|---|---|---|
| `pub_invest` | Leontief: ƏKÜY məhsul strukturu (target = məhsul, məs. `CONS`) | birbaşa idxal hissəsi sızır |
| `gov_current` | Leontief: dövlət istehlakı strukturu | — |
| `io_sector_demand` | Leontief: hədəf sektorun məhsuluna son tələb (sektor proqramı) | idxal payı sızır |
| `io_export_demand`, `export_subsidy` | Leontief: ixrac; subsidiya → ΔE = ε·S (ε = 1,5, `fiscal_params`) | ixrac tam daxili |
| `public_wage` | gəlir → istehlak (mpc·(1−τ)) | büdcə əmək haqqı fondu `fiscal_params` |
| `fuel_price` | qiymət: PETR ekzogen +%·0,75; ev təsərrüfatı yanacağı +%·0,90 | AI-92+dizel payı (fərziyyə) |
| `utility_tariff`, `elec_tariff`, `gas_tariff`, `water_tariff` | qiymət: D (elektrik 0,55; qaz 0,40 payı), E ekzogen | — |
| `vat_rate` | yalnız son istehlak qiymətləri; azad sektorlar istisna | tam ötürmə |
| `product_tax` | aralıq + son istifadə (əvəzləşdirilməyən; mənfi = subsidiya) | — |
| `import_tariff`, `fx_deval` | idxal qiymətləri (mallar / bütün) | Armington əvəzlənməsi yoxdur |
| `labour_cost`, `sector_productivity` | qiymət: Δv; məhsuldarlıqda məşğulluq əmsalı /(1+g) | sabit buraxılışda |
| `agri_subsidy` | qiymət (k/t vahid xərci −S/x) + Ghosh (S·0,6) | ayrıca metod etiketi |
| `sector_supply_shock` | Ghosh | məhdud şərh |

`profit_tax` üçün IO kanalı yoxdur (sabit əmsallı modeldə mənfəət xərc deyil) — mühərrik xəbərdarlıq verir.
**Çıxış formatı** (`engine_base.OUT_COLS`): `io_output:<sektor>`, `io_va:<sektor>` (mln AZN), `io_emp:<sektor>` (min nəfər),
`io_price:<sektor>` (indeks, baza = 100), cəmlər `io_output_total`, `io_va_total`, `employment`, `io_imports_total`,
`io_output_total_t2`, `io_emp_total_t2`, `io_cpi`, `infl` (səviyyə şokunun il ərzində dəyişməsi, f.b.), Ghosh üçün
`io_output_ghosh:<sektor>`, `io_output_ghosh_total`; `group` = sektor kodu və ya «ümumi»; `note_az` təsir rütbəsini verir.
Baza = 2025 GRAS cədvəlinin səviyyəsi (statik; hər il həmin ilin alət ölçüsünün eyni il təsiri). FR2 qəbul cədvəli:
`P2_io_affected_sectors.csv` (ssenari, sektor, növ — buraxılış/əlavə dəyər/məşğulluq/qiymət, Δ %, rütbə).

## 6. 2025-ə yeniləmə (GRAS) — `policyunit/io_update.py`
Hədəflər: (i) sektor buraxılışı — FR1 `out_tot/out_oil/out_man/out_agr/out_con`, digər sektorlar FR1 qrupunun əlavə dəyər
artımı ilə, sonra cəmi `out_tot_n`-ə uyğunlaşdırılır (OILGAS = `out_oil` − PETR); (ii) sektor əlavə dəyəri — FR1 `va_*_n`, qrup
daxilində 2021 payları ilə; (iii) son tələb — DSK 027en cəmləri (ev təsərrüfatı, dövlət = fərdi + kollektiv, ETXQKT, ƏKÜY,
ehtiyatlar, ixrac; neft-qaz ixracı neft buraxılışı ilə), idxal — 027en P.7. Aralıq istehlakın sütun cəmləri `u = x − əlavə dəyər
− vergilər`; sətir cəmləri `v = x + m − f`, buraxılışla böyüyən əvvəlki səviyyənin [0,5; 2] intervalı ilə məhdudlaşdırılır,
sonra `Σv = Σu`-ya miqyaslanır; son tələbin MH hədəfindən fərqi ehtiyatların dəyişməsinə (statistik uyğunsuzluq) yazılır və
sektor üzrə `P2_io_update_2025.csv`-də göstərilir. GRAS (Junius–Oosterhaven 2003; Lenzen və b. 2007) mənfi elementləri saxlayır.
**Yığılma:** 16 iterasiya, maks. nisbi qalıq 5·10⁻⁸; MH uyğunsuzluğu −1 052 mln AZN (buraxılışın −0,56 %-i); yenilənmiş cədvəl
FR1 2025 ümumi buraxılışını (188 933 mln AZN) dəqiq təkrarlayır. İstifadəçi `ctx = {"io_table": 2021}` ilə **2021 benchmark**
cədvəlini seçə bilər. Məşğulluq 2025 İQS (5 105,2 min nəfər).

## 7. Retrospektiv validasiya (NFR1) — `policyunit/io_validate.py`
**7a. Əmsalların sabitliyi (geriyə proqnoz).** Əvvəlki benchmark cədvəlinin Leontief tərsi × hədəf ilin **müşahidə olunan**
daxili son tələbi → hədəf ilin sektor buraxılışı; etalon: əvvəlki buraxılış vektoru son tələbin ümumi artımı ilə miqyaslanır.
Nominal dəyərlər (nisbi qiymət dəyişmələri xətanın bir hissəsidir). `V_io_stability*.csv`:

| Cüt | RMSE, mln AZN | MAPE, % | Çəkili MAPE, % | Ümumi xəta, % | Etalon çəkili MAPE, % |
|---|---|---|---|---|---|
| 2016 → 2021 | 934 | 13,3 | 8,5 | −2,0 | 17,0 |
| 2011 → 2016 | 587 | 11,9 | 9,3 | +1,8 | 29,6 |

IO hər iki cütdə sadə etalondan yaxşıdır. Ən böyük xətalar (2016→2021): MINOTH −46 %, TRANS −38 % (boru kəməri nəqliyyatının
strukturu dəyişib), BUS −25 %, METMIN −24 %, MACH +21 %, ICT +22 % — kiçik və ya struktur dəyişən sektorlar. Neft-qaz +5 %,
tikinti −1 %, ticarət −1,5 %, dövlət sektorları < 3 %.

**7b. Hadisə E7 — 30.06.2024 yanacaq və tarif paketi.** Tarif Şurası: AI-92 1,00 → 1,10 AZN/l (+10 %), dizel 0,80 → 1,00
(+25 %); AI-95 (bazar qiyməti) 15.07.2024-dən 1,60 AZN (−20 %); eyni gün Bakıda avtobus 0,40 → 0,50 və metro 0,40 → 0,50 AZN
(+25 %), Abşeronda məişət tullantıları 0,30 → 0,70 AZN/nəfər (×2,33). Model şoku: CPA 19 istifadəsində yanacaq qarışığı
(AI-92 0,45; dizel 0,30; AI-95 0,05; digər 0,20 — **fərziyyə**) ⇒ PETR əsas qiyməti +11,0 %; ev təsərrüfatı yanacaq qarışığı
(0,85 / 0,05 / 0,10) ⇒ +7,75 %. Müşahidə: DSK İQİ dekabr 2024 / dekabr 2023. Əks-faktual: tənzimlənən maddələr üçün 0 (qərar
olmadan dəyişmir), bazar maddələri/qruplar üçün 2023-cü ilin eyni göstəricisi. `V_io_e7_fuel_2024.csv`:

| Göstərici | Müşahidə (artıq), % | Model, % | Sapma, f.b. | İşarə |
|---|---|---|---|---|
| Yanacaq məhsulları | 7,1 | 7,75 | +0,65 | ✓ |
| Avtomobil sərnişin nəqliyyatı | 15,9 | 9,0 | −6,9 | ✓ |
| Digər nəqliyyat xidmətləri (yalnız dolayı yanacaq) | 0,95 | 0,33 | −0,6 | ✓ |
| Zibil yığılması | 134,8 | 133,3 | −1,5 | ✓ |
| Qeyri-ərzaq mallar və xidmətlər (yalnız yanacaq / tam paket) | 1,24 | 0,98 / 1,75 | −0,26 / +0,51 | ✓ |
| Ümumi İQİ (tam paket) | 2,75 | 1,22 | −1,5 | ✓ |

Şərh: birbaşa təsirlər (yanacaq, tullantı) 10 %-dən az sapma ilə; qeyri-ərzaq qrupu müşahidə olunan artıq inflyasiyanı
yanacaq-only və tam paket qiymətləndirmələri arasında əhatə edir; ümumi İQİ-nin artıq hissəsinin yarıdan çoxu siyasətlə bağlı
deyil (ərzaq inflyasiyası 0,8 → 5,5 %, telefon xidmətləri +27,6 %, aviabilet +26,3 %). Avtomobil sərnişin nəqliyyatının
müşahidə olunan artımı (15,9 %) modeldən yüksəkdir — şəhərlərarası və rayon marşrutlarının tarifləri, taksi; 2023-də də +18,4 %.
Dolayı nəqliyyat ötürülməsi aşağıdır, çünki TRANS sektoruna boru kəməri nəqliyyatı daxildir (aqreqasiya qərəzi).
Həssaslıq (`V_io_e7_sensitivity.csv`): qarışıq çəkiləri və cədvəl ili (2016/2021) üzrə tam paket İQİ təsiri 1,18–1,62 f.b.
**Məhdudiyyət:** yalnız illik (dekabr/dekabr) maddə indeksləri maşınla oxunur; aylıq hadisə tədqiqatı üçün DSK aylıq İQİ
maddə seriyaları Nazirlik vasitəsilə tələb olunmalıdır. Sübut səviyyəsi D (model) — kalibrləmə E7-yə edilməyib (out-of-sample),
lakin yanacaq qarışığı fərziyyələri ekspert qiymətləridir.

## 8. Başlıq nəticələri (2025 GRAS cədvəli, tip I)
- Buraxılış multiplikatorları (ən yüksək 5): qida 1,72; kimya 1,59; metallurgiya və mineral 1,50; k/t 1,48; tikinti 1,47
  (tip II: 2,26; 1,96; 1,89; 2,09; 2,05). Neft-qaz 1,08 — zəif daxili əlaqə.
- Məşğulluq multiplikatorları (nəfər / 1 mln AZN): k/t 140; su-tullantı 88; digər xidmətlər 74; təhsil 65; yüngül sənaye 52.
- Açar sektorlar (BL > 1, FL > 1): METMIN, MACH, LIGHT, WATER, MINOTH; hipotetik çıxarmada ən böyük itki: tikinti 3,3 %,
  ticarət 2,9 %, qida 2,9 %, dövlət idarəetməsi 2,4 %, k/t 2,4 %.
- Vahid qiymət şokları (İQİ, f.b.): yanacaq +10 % → 0,74; elektrik +10 % → 0,21; qaz +10 % → 0,15; əmək xərci +10 % → 1,82;
  məzənnə +10 % → 3,90 (tam ötürmə, yuxarı sərhəd); idxal rüsumu +5 f.b. → 1,44; ƏDV +1 f.b. → 0,69.
- Dövlət investisiyası +1 mlrd AZN: buraxılış +904 mln, əlavə dəyər +442 mln, məşğulluq +19,5 min (tip II: +33,4 min), idxal
  +524 mln; yalnız tikinti hədəfi ilə əlavə dəyər +497 mln. MikroUnit FR1 multiplikatoru (+0,93 % qeyri-neft ÜDM) ilə fərq
  (NFR2): IO-da sürətləndirici/kapital kanalı yoxdur və idxal sızması açıq hesablanır.

## 9. Məhdudiyyətlər və Nazirliyə məlumat sorğusu
Sabit texniki əmsallar və qiymətlər; təklif məhdudiyyəti yoxdur; qiymət–kəmiyyət qarşılıqlı təsiri yoxdur; idxal
mütənasibliyi; Ghosh kəmiyyət şərhi şərtidir; 2025 cədvəli müşahidə deyil, GRAS proqnozudur; tip II yuxarı sərhəddir.
Sorğu: (a) 2021 SUT üçün idxal istifadə matrisi; (b) məhsul × fəaliyyət məşğulluğu; (c) aylıq İQİ maddə indeksləri və çəkiləri;
(d) yanacaq növləri üzrə satış həcmləri (SOCAR) — E7 qarışıq çəkilərinin dəqiqləşdirilməsi; (e) növbəti benchmark (2026) cədvəli.

## 10. İşə salma
```
POLICY_NO_NETWORK=1 python3 -m policyunit.io_outputs      # P2_*, V_io_*, D_io_* + output/_catalog.csv
python3 -m unittest tests.test_io                         # oflayn testlər
python3 -m policyunit.io_data --refresh                   # DSK xam fayllarının yenilənməsi
```
Mənbələr (E7): apa.az/energy-and-industry/azerbaijan-increases-ai-92-gasoline-diesel-prices-487837;
jam-news.net/prices-surge-in-azerbaijan; turan.az (782042, 782075); DSK `price_tarif/en/001_5en.xlsx`.
