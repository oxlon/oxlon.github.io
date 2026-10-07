# PolicyUnit nüvəsi — metodologiya (MİİS §15.5.4, FR1, FR5, NFR2, NFR4)

## 1. Əsas prinsip
Siyasət təsiri = **ssenari − baza** (əks-faktual, eyni vintaj). Baza yolu PolicyUnit tərəfindən yaradılmır: MikroUnit
FR1→FR12 zənciri (15.5.2) və Nazirliyin CAEM modelinin sabitlənmiş nüsxəsi istifadə olunur. Hər işin vintaj id-ləri
`output/P1_run_meta.json`-da yazılır (MikroUnit FR1 reyestri + proqnoz faylının MD5-i, CAEM.xlsx MD5 `12c22d22…`).
Struktur modellər: AR/ARIMA/GARCH, gecikmiş asılı dəyişən və öz tarixinə əsaslanan proqnoz **istifadə olunmur**.

## 2. Arxitektura (plug-in, NFR4)
`config/instruments.csv` (siyasət alətləri) → `config/adapters.csv` (alət → mühərrik → giriş) → mühərriklər
(`run(ssenari, ctx) → Result`, vahid sütunlar: göstərici, il, baza, dəyər, fərq, % fərq, metod, sübut səviyyəsi) →
`integrate.py` (birləşdirmə, üfüqlər) → `compare.py` (NFR2) → `kpi.py` (FR5). Yeni ssenari = yeni JSON fayl
(`config/scenarios/`), yeni alət = CSV sətirləri; kod dəyişikliyi lazım deyil (bax `config/README_az.md`).

## 3. Üfüqlər (Nazirliyin 24.08.2026 cavabı)
qısa = başlanğıc il və növbəti il; orta = +2…+3; uzun = ≥ +4 (5-ci il və sonrası). MikroUnit 2030-da bitir, ona görə
2031–2035 üçün `eng_longrun` — **«uzun müddət (struktur ekstrapolyasiya)»** — istifadə olunur. Üfüq effekti: səviyyə
göstəriciləri üçün baza ilə orta % fərq, dərəcələr üçün orta f.b. fərq, axınlar (xərc, balans) üçün cəm.

## 4. MikroUnit mühərriki (`eng_micro`, əsas metod)
Ssenari və baza zənciri eyni struktur rıçaqları ilə (məs. `income_block=legs`) işə salınır; ekzogen girişlər yalnız
ssenaridə dəyişir. MikroUnit naməlum açarı yalnız xəbərdarlıqla keçir — PolicyUnit bunu **xəta** sayır.

| Alət | MikroUnit kanalı | Sübut |
|---|---|---|
| Dövlət investisiyası | `istate_add` = nominal / (p_inv × kapital xərci əmsalı) → Δkapital xərci = ölçü | C |
| Minimum əmək haqqı | FR1 `minwage` (%) + FR3 `mw_growth` (səviyyə → artım yolu) | C |
| Pensiya | `pension_real_g` (səviyyə → artım), `income_block=legs`; xərc FR1 v2.3.5-də büdcədədir | C |
| ÜSY | `dsmf_add_g` proksisi (ÜSY xərci / DSMF xərci); xərc büdcəyə PolicyUnit tərəfindən əlavə edilir | C/D |
| Uçot dərəcəsi | `polrate` + `deprate` (ötürmə 0,5) | C |
| Məzənnə | `fx` | C |
| Kredit subsidiyası | `deprate` (subsidiya / kredit qalığı / 1,40) | D |
| TFP proqramı | `tfp_boost` | C |
| İxrac subsidiyası | `extdem` (elastiklik 1,5 × subsidiya / qeyri-neft ixracı) | D |
| İdxal rüsumu | `pm_usd_infl` (səviyyə → bir dəfəlik artım) + rüsum gəliri | D |
| ƏDV, gəlir vergisi, yanacaq, kommunal tariflər, aqrar subsidiya | FR1 **overlay** (bax 4.1) | D |
| Bazar girişi | FR12 sənaye iqtisadiyyatı alət dəsti (`io_market`, `io_dN`) | D |
| Mənfəət vergisi | FR1 overlay proksisi: gəlir itkisi + özəl investisiya (istifadə dəyəri, daxili vəsait) — bax §12 C1 | D |
| Cari xərc, büdcə maaşları | MikroUnit kanalı yoxdur → CAEM / IO / mikrosimulyasiya | — |

### 4.1 FR1 overlay (proksi, sübut səviyyəsi D)
FR1-də vergi dərəcəsi girişi olmadığı üçün FR1-in öz qiymətləndirilmiş əmsalları ilə (iş vaxtı `inputs()`-dən oxunur)
FR1 nəticəsinə əlavə edilir və **sonra** FR3–FR12 bu düzəldilmiş yolu alır:
- qiymət səviyyəsi: ƏDV → dp = ötürmə (0,7) × Δdərəcə / (100 + 18); yanacaq → dp = çəki (3 %) × Δ% × (1 + dolayı 0,5);
- real sərəncamda qalan gəlir: dlnH = dh + ω·β·dp − dp (ω = E3 əmək haqqı fondu elastikliyi, β = E2 İQİ elastikliyi);
- istehlak dlnC = γ·dlnH (D1), idxal dlnM = μ·dlnC (D4), ΔYn = ΔC − ΔM + ΔS (sektor təklifi) + ΔG;
- məşğulluq dln emp = ε·dlnYn (E1), işsizlik İQS əsasında; gəlirlər F2 elastiklikləri ilə; borc = kumulyativ kəsir.
Tələb dəyişməsi qeyri-neft sektorlarına əlavə dəyər paylarına görə paylanır. Gəlir vergisi: dh = −Δdərəcə/dərəcə ×
gəlir/ÜDM × ÜDM × 0,9 / sərəncamda qalan gəlir. Aqrar subsidiya: ΔƏD(k/t) = 0,6 × subsidiya / deflator.

### 4.2 Fiskal uçot və maliyyələşmə
`fiscal_cost` — ex ante statik birbaşa xərc (`cost_rule`): xərc = ölçü; vergi gəlir itkisi = Δdərəcə/dərəcə × gəlir/ÜDM ×
ÜDM; müavinət = % × baza (`fiscal_params.csv`, mənbə və «təqribi» işarəsi ilə). FR1 büdcəsində olmayan xərclər balansa
əlavə edilir. Maliyyələşmə: **deficit** — borc artır; **sofaz** — ARDNF transferti gəlir kimi (borc dəyişmir,
`sofaz_assets` azalır); **tax** — eyni məbləğdə vergi artımı (sərəncamda qalan gəlir azalır); **reallocation** — digər cari
xərclərin azaldılması (tələb azalır). `budget_balance` — geri əlaqədən sonra xalis təsir.

### 4.3 Məşğulluq şərhi
FR1 `emp` İQS üzrə ümumi məşğulluqdur və ÜDM-ə elastikliyi kiçikdir (E1 ≈ 0,034) — işsizlik təsirləri sıfıra yaxın çıxır.
Formal iş yerləri FR4 muzdlu işçilər (`employment_hired`, `sector_hired:*`) ilə oxunmalıdır; hər ikisi çıxışdadır.

## 5. CAEM mühərriki (`eng_caem`, «Nazirlik CAEM modeli — müqayisə»)
`AZE Model` reduksiya forması y_t = Bc + B1·y_{t−1} + B2·e_t (48 vəziyyət, illik; h = 1 ↔ 2026, 2037-yə qədər).
Kod RiskUnit `caem_model.py`-dən **kopyalanıb** (`caem_core.py`), RiskUnit import edilmir; iş kitabı
`data/ministry/CAEM.xlsx` (MD5 sabitlənib, yalnız oxunur). Təsir = simulyasiya(siyasət) − simulyasiya(şoksuz); hədəf yolları
şoksuz yola nisbətən verilir. Xəritə: kapital xərci → `gcap_y` (ÜDM-ə %, yol), cari xərc/transfert/subsidiya → `pb_y` şoku
(−), ƏDV/mənfəət/gəlir vergisi/rüsum → `vatax_y/ptax_y/pitax_y/otax_y` (gəlir dəyişməsi ÜDM-ə %), uçot dərəcəsi → `CR`,
məhsuldarlıq → `dta`, tənzimlənən qiymətlər → `dP` xərc şoku, ixrac subsidiyası → `dx`. Sübut səviyyəsi D (kalibrlənmiş).
**CAEM xüsusiyyətləri (nəticələrin şərhi üçün vacib):** (i) vergi şokları yalnız büdcə kanalı ilə işləyir — gəlir
dəyişməsi xərclərə ötürülür, ona görə vergi endirimi CAEM-də daraldıcıdır; qiymət/sərəncamda qalan gəlir kanalı yoxdur;
(ii) `gcap_y` ilkin balansa və borca yazılmır — borc/ARDNF maliyyələşmə fərqi CAEM-də görünmür; (iii) `dS` (məzənnə)
şoku B2-də heç bir dəyişənə ötürülmür — devalvasiya ssenarisi üçün CAEM tətbiq edilmir; (iv) uçot dərəcəsi endogen
reaksiya verir (Teylor tipli), FR1-də isə ekzogendir.

## 6. OxLon (`eng_oxlon`)
Yalnız neft/tərəfdaş/məzənnə kanalları; OxLon FR13 `ministry_spec` **nüsxədə** (`work/oxlon`) alt-prosesdə işlədilir,
Macro_OxLon-a heç nə yazılmır. Cəmi 16 sıra (İQİ, sektor deflatorları və artım templəri, xidmət ixrac/idxalı); ÜDM,
işsizlik və fiskal çıxış yoxdur → qismən müqayisə. `usd_azn` +10 % yalnız 4 sıranı dəyişir (İQİ-yə ötürmə yoxdur).

## 7. Uzun müddət (`eng_longrun`, 2031–2035, «struktur ekstrapolyasiya»)
FR1-in 2030 sapmasından **kəsilməz** davam: dlnY_t = S_t + D_2030·d_t. Təklif hissəsi S (siyasət kapitalı — dövlət
investisiyası θ_g, mənfəət vergisi ilə özəl investisiya α; φ hissəsi struktur TFP) qalır; tələb hissəsi D sönür.
Cobb–Duglas, δ FR1 2030 bazasının eyniliyindən (I − ΔK)/K(−1). Baza səviyyələri balanslaşdırılmış artımla
g = g_L + g_A/(1−α) (struktur parametrlər — öz tarixindən proqnoz deyil). Fiskal qalıq kanal (qiymət səviyyəsi, idxal,
indeksasiya) 2030 səviyyəsində saxlanır. Sübut səviyyəsi D. Cari parametrlər (`config/longrun_params.csv`-dən avtomatik):
<!-- AUTO:longrun -->
- α = 0,40; θ_g = 0,10; tələb yarımömrü = 3,0 il; məşğulluq yarımömrü = 3,0 il; ψ = 0,50; kəsilməzlik tolerantlığı = 0,05
<!-- /AUTO -->

## 8. Metodların müqayisəsi (NFR2, `N2_method_comparison.csv`)
Hər ssenari × göstərici × üfüq üçün ≥ 2 metodun orta təsiri: əsas metod (MikroUnit + uzun müddət), CAEM, OxLon, IO,
mikrosimulyasiya. IO uyğunlaşdırılması: `io_va_total` ↔ real ÜDM, `io_cpi` ↔ İQİ, `io_va:<sektor>` FR1 qrupuna,
`io_emp:<sektor>` FR4 bölməsinə toplanır. Sütunlar: hər metodun dəyəri, fərq (spread), işarə uyğunluğu, avtomatik
Azərbaycan dilində izah (fərqin struktur səbəbləri: fiskal qayda, Okun qanunu, sabit əmsallar, proksi və s.).

## 9. KPI kataloqu və çoxkriteriyalı qiymətləndirmə (FR5)
`config/kpi.csv` — 30 göstərici (id, ad, düstur, göstərici, üfüq, statistika, vahid, istiqamət, çəki, mənbə mühərrik).
İstifadəçi ≥ 5 göstərici seçir (az seçim → xəta). Normallaşdırma ssenarilər arasında min–maks (istiqamətə görə 0–1),
bal = Σ w·n / Σ w (mövcud KPI-lar üzrə), xərc-effektivlik = bal / 1 mlrd AZN birbaşa xərc (qısa + orta), reytinq.
Xarici KPI-lar (risk ES10, yan təsirlər sayı) FR4 mərhələsində `output/P4_kpi_inputs.csv` (scenario, kpi, value) ilə.

## 10. Sübut səviyyəsi (Blueprint §6.3)
Bütün ex ante rəqəmlər model əks-faktualıdır. Etiket nəticəni sürən elastikliyin identifikasiyasını göstərir:
**C** — Azərbaycan məlumatı ilə qiymətləndirilmiş MikroUnit struktur tənliyi birbaşa kanal kimi; **D** — kalibrlənmiş
(CAEM), fərziyyəyə əsaslanan proksi (overlay) və ya 2030-dan sonrakı ekstrapolyasiya. A/B yalnız NFR1 retrospektiv
validasiyada mümkündür.

## 11. Məhdudiyyətlər və açıq məsələlər
- `fiscal_params.csv`-dəki bəzi bazalar təqribidir (ƏDV/mənfəət/gəlir vergisi gəlirləri, ÜSY, DSMF, büdcə maaş fondu) —
  Nazirlik (MN) dəqiqləşdirməlidir; dəyişiklik yalnız CSV-də.
- Minimum əmək haqqının büdcə xərci (`mw_budget.py`, cost_rule `mw_budget`): DSK 004_11-12 əmək haqqı intervalları ×
  sektor (noyabr 2025; dövlət idarəetməsi, təhsil, səhiyyə, incəsənət) FR4 büdcə işçilərinin sayına (`fr4:budget`)
  miqyaslanır; ≤ 600 AZN maaşlar baza minimum əmək haqqı ilə, ≥ 1 000 AZN FR3 büdcə maaşı ilə indekslənir (arada xətti);
  yeni minimumdan aşağı maaşlar ona qaldırılır, 25 %-ə qədər yuxarı maaşlar artımın 50 %-ni (xətti azalan) alır
  (sıxılma fərziyyəsi), üstəgəl 22 % işəgötürən sosial ayırması; cari xərc kimi büdcə balansına yazılır.
  +20 % (2027-dən), son işin nəticəsi (`output/P1_effects.csv`-dən avtomatik):
<!-- AUTO:mw_budget -->
  ≈ 101,0–117,7 mln AZN/il (2027–2030); büdcə işçilərinin ~36 %-i təsirlənir
<!-- /AUTO -->
- **Minimum əmək haqqında işdən çıxarma / qeyri-formallaşma kanalı yoxdur** — məşğulluq təsiri yuxarı sərhəddir;
  xəbərdarlıq hər nəticə sətrində (`note_az`) və mühərrik vəziyyətində verilir, risk FR4 mərhələsində ölçülür.
- FR1-də cari hesab yoxdur (proksi); vergi alətləri MikroUnit-də proksidir (D).
- Uzun müddət effektləri struktur fərziyyələrə həssasdır (α, φ, yarımömürlər — `longrun_params.csv`).

## 12. Müstəqil rəy düzəlişləri (C1–C7)
- **C1 CAEM vergi → fiskal:** CAEM-də vergi şoku yalnız büdcə kanalı ilə işləyir və balans/borc işarələri uyğunsuzdur
  (mənfəət vergisi −2 f.b.: balans +0,05 f.b., borc +0,28 f.b.). Vergi alətlərində CAEM-in fiskal sətirləri
  **ETİBARSIZ** işarəsi alır, KPI-lardan və başlıq ehtiyatından çıxarılır. Mənfəət vergisi üçün ikinci metod — MikroUnit
  proksisi: gəlir itkisi (mənfəət vergisi bazası) + qeyri-neft özəl investisiyası
  dlnI = −ε_uc·Δτ/(100−τ) + ε_cf·ΔCF/I (ε_uc = 0,5, ε_cf = 0,3, idxal payı 0,4; sübut D); kapital FR1 K_non-a yığılır.
- **C2 maliyyələşmə alət üzrə:** hər alətin öz maliyyələşmə sahəsi (kəsir / ARDNF / vergi / xərclərin yenidən bölüşdürülməsi) ayrıca tətbiq olunur
  (`fiscal.scenario_cost(...)["by_fin"]`), qarışıq ssenari artıq kəsirə çevrilmir.
- **C3 minimum əmək haqqı:** nəticə diapazon kimi (`P1_ranges.csv`): mikrosimulyasiyanın statik döşəməsi, spill-over
  seçimi ilə mikrosimulyasiya, MikroUnit makro reaksiyası. NFR1: zəncir maaşı və 2019 inflyasiyasını yüksək qiymətləndirir
  (sitat nəticə mətnində). Pensiyaların İQİ indeksasiyası indi büdcəyə yazılır (overlay pensiya düzəlişi).
- **C4 uzun müddət:** 2030 sapmasından kəsilməz davam (bölmə 7-nin yeni forması `eng_longrun.py` başlığında):
  tələb hissəsi `demand_halflife` yarımömrü ilə sönür (siyasət qüvvədə olduqca ψ səviyyəsinə; dəyərlər §7-də), kapital/TFP hissəsi qalır,
  dövlət kapitalının elastikliyi 0,10; fiskal qalıq kanal (qiymət səviyyəsi, idxal, indeksasiya) 2030 səviyyəsində saxlanır.
  Yoxlama: `P1_longrun_continuity.csv` (addım ≤ max(tol, 2,5 × əvvəlki addım, 2030 sapmasının 12 %-i); balans birbaşa
  xərcdən əvvəl yoxlanır, çünki siyasətin 2030-da bitməsi qanuni addımdır).
- **C5 ardıcıllıq:** io.outputs → microsim.outputs → core.scenarios → fr4 → nfr1 → core.kpi → panel.build →
  core.freshness (P3/P4/V_nfr1/P5/panel təzəliyi və P5 risk_breach = P4, P3 Gini = P1 yoxlanır).
- **C6 fiskal bazalar:** pensiya bazası DSMF əmək pensiyaları 2024 faktiki 6 469 mln AZN × 1,08 = 6 990 (2025), DSMF
  xərcləri 6 889 × 1,08 = 7 440 — hər ikisi FR1 orta pensiya yolu ilə; FR1-in daxili bazası (7 783) overlay-də düzəldilir.
  ÜSY xərci — mikrosimulyasiyanın benefisiar əsaslı tərifi (`eng_microsim.tsa_spending`; +30 % ≈ 95–101 mln AZN/il).
- **C7 yanacaq və məzənnə:** tənzimlənən yanacaq qiymətinin gəlir kanalı = satış dəyərindən ƏDV + əlavə marjadan
  mənfəət vergisi (satış 4,2 mlrd AZN, elastiklik −0,2) → mənfi fiskal xərc. Devalvasiya: İQİ üçün başlıq mənbəyi
  RiskUnit-in kalibrlənmiş FX ötürməsidir (`eng_riskfx`, ötürmə 0,30, hadisə ilində 68 %; 2015 epizodu nümunədaxilidir);
  FR1 zənciri ilə yanaşı göstərilir. Büdcə işarəsi: neft gəliri AZN ilə artır, lakin FR1 fiskal qaydaları (F3, F4) əlavə
  gəliri xərcləyir — balans azca pisləşir (izah nəticə qeydində).
- **KPI:** seçilmiş KPI hesablanmırsa bal mövcud KPI-larla hesablanır, lakin «bütün KPI-lar hesablanıb» sütunu «xeyr» olur və qeyddə açıq
  xəbərdarlıq verilir. Aqrar subsidiyanın fermer gəlirinə ötürülməsi `fiscal_params.agri_income_passthrough` (defolt 1,0 —
  yuxarı hədd) kimi sənədləşdirilib.
