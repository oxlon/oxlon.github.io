# Riskin miqyaslanması və risk azaldıcı tədbirlər (S1–S7, M1–M7)

MİİS §15.5.3 — İqtisadi Risklərin İdarəedilməsi. Modullar: `riskunit/scalability.py` (S), `riskunit/optimize.py` (M),
`riskunit/measures.py` (reyestr v2). Əmrlər: `python3 -m riskunit.scalability [--force] [--no-params]`,
`python3 -m riskunit.optimize`. Hər ikisi `run(ctx)` funksiyasını ixrac edir (inteqrasiya: `run_all.py`).

## 1. Miqyaslanma modeli — nə ölçülür

Sual: *risk amili X qədər dəyişsə, hansı dəyişənlər, hansı ölçüdə və hansı parametrlər vasitəsilə təsirlənir?*

1. **Amillər və σ vahidi** (`S0_factor_sigma.csv`). Hər amil təbii vahiddə (USD/barel, %, f.b., % ÜDM) və σ
   vahidində verilir; σ 1990–2025 tarixindən hesablanır: qiymətlər üçün illik log dəyişmənin standart kənarlaşması
   (Brent, qaz, məzənnə, dövlət investisiyası, GPR), dərəcələr üçün illik dəyişmə (uçot dərəcəsi, NPL), artım üçün
   səviyyə (tərəfdaş artımı, ərzaq və idxal qiymətləri), bir ilin üstünlük təşkil etdiyi sıra üçün robast σ
   (pul baratları, 1,4826×MAD — 2022 axını quyruqdur). Zəlzələ birtərəfli təhlükədir: zərər log-normal
   paylanmadan (M ≥ 6: median 0,5%, P90 3% ÜDM — kalibrləmə fərziyyəsi), yalnız k > 0, yuxarı hədd 15% ÜDM.
2. **Ötürmə — yalnız struktur.** Şok 2026–2030 üçün davamlı sapma kimi MikroUnit zəncirinə
   (FR1→FR3→FR4→FR5→FR10→FR12, `chain.run_chain`) verilir: ekzogen yol (`brent`, `gas_exp_price`, `fx`,
   `extdem`, `polrate`/`deprate`, `istate_add`, `npl_ratio`, `tfp_boost`) və ya kanalı daşıyan FR1 tənliyinin
   sabitinin sürüşməsi (E3 — sərəncamda qalan gəlir: baratlar; C1 — kənd təsərrüfatı: SPI; G4 — inflyasiya:
   ərzaq/idxal qiymətləri və xərc şoku). Sabitin sürüşməsi 2025 düzəliş əmsalına udulmasın deyə
   `addf_recalibrate=False` istifadə olunur (Baseline dəyişmir — test edilib). Ərzaq və idxal qiymətlərinin İQİ-yə
   ötürülməsi (v2.1: vahid qiymətləndirmə, gecikmiş asılı dəyişən yoxdur):
   <!-- AUTO:s_passthrough -->
Vahid xarici qiymət ötürməsi (`cpi_ext`, HAC, 2001–2025, n = 25): AZN idxal qiymətləri b0 = 0,176, b1 = 0,084; ərzaq → USD idxal qiymətləri γ = 0,68; Brent → idxal qiymətləri 0,46.
<!-- /AUTO:s_passthrough --> Mühərrikin tanımadığı açar yalnız xəbərdarlıq verir —
   modul belə halda **xəta ilə dayanır** (`EngineError`); sərhədə qədər kəsilmə qeyd olunur.
3. **Şəbəkə** (`S1_scalability_grid.csv`): k ∈ {−3; −2; −1; −0,5; +0,5; +1; +2; +3}σ və bugünkü canlı sapma (D5).
   Baş göstəricilər: qeyri-neft ÜDM səviyyəsi və artımı, İQİ, büdcə balansı (Δ mln AZN / Baseline ÜDM —
   MikroUnit v2.3.1 vahidi), mal ticarəti balansı (cari hesab proksisi), dövlət borcu / ÜDM və 31 komponent.
4. **Elastikliklər** (`S2`): σ-ya və təbii vahidə düşən cavab, log amillər üçün nisbi elastiklik.
5. **Qeyri-xəttilik** (`S3`): asimmetriya |r(+k)|/|r(−k)|, əyrilik (r(+k)+r(−k))/(|r(+k)|+|r(−k)|), miqyas sapması
   r(k)/(k·r(1)) − 1, sərhəd kəsilməsi (məs., uçot dərəcəsinin sıfır həddi k ≤ −2σ). Risk iştahı həddinin
   (GaR 2%, İQİ 6%, büdcə −1% ÜDM, borc 30% ÜDM, ticarət balansı 0) keçildiyi ən kiçik σ ölçüsü və inandırıcılıq
   həddi (məs. |Δ İQİ| > 10 f.b.) göstərilir. Mənbələr: zəncirvari real ÜDM, nisbətlər, log/səviyyə çevrilmələri.
6. **Təsir xəritəsi** (`S4`): +1σ şokda bütün ≈1 500 komponentin dəyişməsi (səviyyə/indeks — %, dərəcə/pay —
   f.b.), amil daxilində 0–1 normallaşdırılmış əhəmiyyət, modul və qrup üzrə xülasə — «hansı dəyişənlər».
7. **Parametrlər** (`S5`): hər FR1 əmsalı (72 qiymətləndirilmiş meyl) ±1 SE dəyişdirilir, 2025 düzəlişi
   mühərrikin öz qaydası ilə (a − Δb·x₂₀₂₅, homogenlik bağları saxlanılır) əl ilə yenidən hesablanır və şok
   altında cavabın dəyişməsi ölçülür: d(cavab)/d(əmsal) və nisbi dalğalanma. Aşağı axın modulları (FR3–FR12)
   üçün MikroUnit `FRx_coef_sensitivity` statik dalğalanmaları S4 əhəmiyyəti ilə çəkilir — «hansı parametrlər».
8. **Modellər arası dispersiya** (`S6`): eyni +1σ şok MikroUnit zənciri, Nazirlik CAEM 8a kitabxanası
   (müqayisə; gecikmiş hədli sistem — əsas ötürmə deyil; davamlı axın şokları IRF-lərin cəmi ilə) və OxLon/FR1
   həssaslıqları (C5, xətti miqyas). CAEM-də məzənnə şoku (dS) heç bir dəyişənə təsir etmir — qüsur kimi qeyd.
9. **Gündəlik qərar cədvəli** (`S7`): D5 canlı sapmaları (Brent, məzənnə, uçot dərəcəsi, büdcə xərclərinin icrası
   — proksi, SPI, dünya ərzaq indeksi, İQİ sürprizi, regional GPR, USGS) dəqiq zəncir hesabı ilə baş proqnozlara
   çevrilir, xətti təxminlə müqayisə olunur, əlverişsiz təsir balı (hedler.csv təsir zolaqlarına nisbətən) üzrə
   sıralanır; ən çox təsirlənən 5 dəyişən, ən həssas 3 parametr və M1 effektinə görə təklif olunan tədbirlər
   əlavə edilir. Canlı göstəricisi olmayan amillər potensial (1σ) təsirlə aşağıda verilir.

Keş: ağır hissələr (S1 şəbəkəsi, S4, S5) MikroUnit mühərrik vəziyyətinin heşi ilə keşlənir
(`work/scalability_cache/`); mühərrik və ya σ dəyişəndə tam yenidən hesablanır, gündəlik yalnız canlı sətirlər.

## 2. Tədbirlər reyestri v2

`input/tedbirler_reyestri.csv` (T01–T30) + `input/tedbirler_v2.csv`: strategiya növü (qaçınma / ötürmə /
azaltma / qəbul; əvvəlki «izləmə» → qəbul), xərc (mln AZN, 2027–2030, **əsaslandırma ilə — Nazirlik
təsdiq etməlidir**), hazırlıq müddəti, KPI həddi, effekt modeli. Yeni tədbirlər: T24 strateji ərzaq ehtiyatı
(R18), T25 idxal rüsumlarının şok mexanizmi (R17), T26 neft gəlirlərinin put hedcinqi, T27 ARDNF valyuta
strukturunun balanslaşdırılması (VaR/CaR), T28 struktur neft qiymətinə əsaslanan fiskal qayda, T29 büdcə
ehtiyat fondu (birinci zərər qatı), T30 model riski — konsensus bazası (R19). T13 fəlakət istiqrazını da əhatə edir.
Status iş axını: təklif → təsdiq → icrada → tamamlandı (`measures.STATUS_FLOW`).

## 3. Tədbirin effekti necə hesablanır (M1, M2)

RU birgə Monte Karlo (`simulate.run`, N = 20 000, 2027) hər kanal üzrə (Brent, prosiklik investisiya reaksiyası,
tərəfdaş, faiz, baratlar, devalvasiya, zəlzələ, quraqlıq, idxal, ərzaq, …) ayrıca çəkiliş verir. Tədbir bu
çəkilişlərə təsir edir və bütün metrikalar yenidən hesablanır:

| Model | Tədbirlər | Mənbə |
|---|---|---|
| kanalın zəiflədilməsi (ekspert parametri × RU ötürmə) | T04, T06, T08, T10, T12, T15, T21–T25 | reyestrdəki təsir faizi |
| 1 000 mln AZN (nominal) ehtiyat: əvvəl prosiklik kəsintinin qarşısı alınır, qalanı GaR pozulan ildə inyeksiya | T09 | RU `fiscal_react_floor` + MikroUnit zənciri (+1 mlrd nominal) |
| İQİ > 6% olduqda uçot dərəcəsi +1 f.b. | T19 | MikroUnit zənciri |
| fiskal qayda (`fiscal_rule=nobd`, `istate_rule=policy_level`): artım/İQİ cavab nisbəti, büdcəyə ƏLAVƏ təsir / 1σ Brent | T28 | MikroUnit FR1 rıçaqları, Brent ±1σ, bütün illər |
| konservativ büdcə qiyməti (P25) | T01 | RU çəkilişləri |
| Asiya put opsionu (25%, K = 0,9×baza; forvard = spot, σ = OVX, 1 il) | T26 | `optimize.hedge_price`, `var.oil_revenue` |
| parametrik sığorta / ehtiyat fondu qatları | T13, T29 | RU zəlzələ/daşqın fiskal kanalı |
| ARDNF valyuta balanslaşdırılması | T27 | V4 Euler töhfələri (birinci tərtib) |

Metrikalar: ES10 və VaR5 (qeyri-neft artımı, büdcə), İQİ-nin yuxarı quyruq ES10-u, hədd pozulma ehtimalları,
ORaR95, ARDNF VaR95, CaR95 və **konsolidasiya olunmuş fiskal kapital axını** FK (v2.4, audit M4). FK_t (mln AZN, plana
nisbətən) = Δ dövlət büdcəsi balansı + ARDNF-in xalis neft daxilolması (Nazirlik «base 60» ARDNF gəlirləri ∝ Brent,
FR1 büdcə neft gəlirinin transfert hissəsi çıxılmaqla) − transfertlə maliyyələşən prosiklik investisiya reaksiyası
(pis illərdə kəsilir → qənaət, yaxşı illərdə artır → xərc; ölçüsü T09 «floor» simulyasiyasından) + tədbirin xərci
kimi büdcə məhdudiyyətində artıq sayılmış ehtiyat çəkilişləri. FK hər yol üzrə 2026–2030 cəmlənir — **yaxşı illərin
qənaəti pis illərin xərcini örtür** (simmetrik). Hədəf funksiyası: baza quyruq boşluğunun aradan qaldırılan payı,
FR2 skorları ilə çəkili (R13 → artım ES10, R12 → inflyasiya ES10, R11 → fiskal kapital, R01 → CaR-ın bazar hissəsi).
Fiskal hissə FK-nın əminlik ekvivalentidir: E − λ·(E − ES10), λ = 0,5 (`obj_fk_tail_weight`, FƏRZİYYƏ — risk iştahı);
M1-də λ = 0 (`effekt_hedef_simmetrik`) və λ = 1 (`effekt_hedef_quyruq`) də verilir. Əvvəlki versiyada yalnız dövlət
büdcəsinin ES-i sayılırdı (T09 −7,85, T28 −7,27).

Cari məqsəd funksiyası dəyərləri (`M1_measures_v2.csv`, λ — FK quyruq çəkisi):

<!-- AUTO:m_results -->
| tedbir_id | λ = 0,5 | λ = 0 | λ = 1 |
|---|---:|---:|---:|
| T09 | 0,86 | 0,86 | 0,87 |
| T26 | 0,34 | 0,30 | 0,38 |
| T28 | −18,53 | −0,58 | −36,48 |
<!-- /AUTO:m_results -->

**Nəticə (06.10.2026 vintajı; cari rəqəmlər yuxarıdakı AUTO cədvəldədir):** T09 +0,88 (1 000 mln ilə məhdud ehtiyat; artım quyruğu +0,30 f.b.); T28 λ = 0,5-də −17,5,
λ = 0-da −0,70, λ = 1-də −34,4: qayda artım quyruğunu +0,68 f.b. yaxşılaşdırır, lakin neft riskini ARDNF buferinə
keçirir (FK quyruğu −19,8% ÜDM, 5 il cəmi) — bu, qaydanın məqsədidir və qiymətləndirmə Nazirliyin λ seçimindən asılıdır.
T26: Asiya put mükafatı 0,74 USD/barel (forvard 114,0, OVX 0,51 → orta üzrə σ 0,35), 1 il → 30,7 mln AZN (əvvəl
4,72 × 4 il = 787,6 mln). Bazar P(Brent < K) = 0,08, RU baza baxışında ödəniş ortası 5,95 USD/barel: baza fərziyyəsi
(69 USD) ilə bazar (114 USD) arasındakı uyğunsuzluq hedcin dəyərini şişirdə bilər — qərar üçün canlı baxış da yoxlanmalıdır.

## 4. Portfel optimallaşdırması və qalıq risk (M3–M5)

Büdcə (mln AZN) və risk iştahı (`input/risk_istahi.csv` — FƏRZİYYƏ, Nazirlik qərarı DR10) məhdudiyyətləri
altında seçim: (1) fərdi effektlərin xətti cəmi üzrə `scipy.optimize.milp` başlanğıc həlli; (2) dəqiq
yenidən qiymətləndirmə ilə əlavə et / çıxar / dəyiş lokal axtarışı (effektlər qarşılıqlı təsirdədir). Risk iştahı
bütün əlçatan tədbirlərlə ödənilə bilirsə məcburi şərtdir, əks halda pozuntu bildirilir. İmkanlandırıcı
(məlumat, izləmə) tədbirlər ≤ 1 mln AZN xərclə həmişə plana daxildir. `M4_frontier.csv` — səmərəli sərhəd
(0–3 000 mln AZN), `M3_portfolio.csv` — 100/500/1 500 mln AZN portfelləri və marginal töhfələr,
`M5_residual_v2.csv` — risk üzrə kanal quyruq töhfələri (baza / cari status çəkili / plan) və qalıq skor.
API üçün: `optimize.optimise(C, M, E, m0, W, A, budget, cand, fixed=(), excluded=())` — `fixed` tədbirlər həmişə
portfeldədir (xərci büdcəyə daxildir; `budget_ok = False` əgər onların özü büdcəni aşırsa), `excluded` heç vaxt
seçilmir; `optimize.score(...)` (köhnə ad `_score` saxlanılır).

## 5. İcra planı və strategiya (M6, M7)

`M6_implementation_plan.csv`: hər tədbir üçün 4 mərhələ (hazırlıq, təsdiq, icra, KPI qiymətləndirməsi) — Qant
tarixləri, məsul qurum, status (iş axını addımı 1/4–4/4), növbəti addım, KPI həddi, gecikmə və 30 günlük
xəbərdarlıq. `M7_strategy.csv`: risk ailələri üzrə əsas yanaşma — MAL: azaltma + ötürmə (fiskal qayda,
hedc, valyuta balansı); XSI: azaltma (şaxələndirmə, ehtiyat, rüsum çevikliyi); TEB: laylı maliyyələşdirmə
(ehtiyat fondu — qəbul, sığorta/istiqraz — ötürmə, suvarma — azaltma); DAX: nəticə risklərinin amillər vasitəsilə
idarəsi; SEK: hədəfli diaqnostika.

## 6. Məhdudiyyətlər (dürüstlük)

* FR1-də kredit faizi (G3) real göstəricilərə ötürülmür: NPL şoku yalnız faizi dəyişir, uçot dərəcəsinin təsiri
  kiçikdir — T04/T19 effekti buna görə kiçikdir; bu, model nəticəsidir, «effektsizlik» sübutu deyil.
* Sabit sürüşməsi ilə verilən şoklar (baratlar, SPI, ərzaq, idxal, xərc şoku) bütün illərdə davamlıdır —
  birillik hadisə üçün təsiri yuxarı qiymətləndirir; canlı SPI və İQİ sürprizi üçün bu qeyd S7-də yazılıb.
* GPR-in təxmin edilmiş kanalları (Brent, tərəfdaş, baratlar) müsbət işarəlidir (2022 analoqu); eskalasiya
  üçün S4 stress vektoru ayrıca amil kimi verilir (`geo_stress`, ekspert).
* Ekspert zəiflətmə faizləri, xərclər və risk iştahı həddləri Nazirlik tərəfindən təsdiq edilməlidir; CaR
  effekti birinci tərtib təxmindir; CAEM yalnız müqayisə üçündür.

## 7. v2.1 (2026-10-06): audit düzəlişləri (S0–S7, stress)

* **Şok ilinin impulsu:** bütün amillər yalnız qiymətləndirmə ilində verilir (2026 = 0); qiymət/faiz/artım
  innovasiyalarında səviyyə qalır, SPI, xərc şoku, ərzaq/idxal inflyasiyası və GPR sıçrayışı keçici impulsdur. v2.0-da
  ərzaq +11% hər il İQİ-ni +3,77 f.b. artırırdı; indi ərzaqın Brent-dən asılı olmayan hissəsi +1σ İQİ-ni yalnız şok ilində və növbəti ildə dəyişir (cari rəqəmlər: AUTO:s_food).b., sonra ≈ 0 dəyişir. S0 `sok_qaydasi`, `qeyd` sütunları əlavə olundu.
* **RU qatı:** override-ın `RU` açarı — `addf` (FR1 tənliyinə bir illik düzəliş impulsu: `infl`, `rva_agr`, `rhhdisp`,
  `lendrate`) və `overlays` (məzənnə modulu; R01 investisiya reaksiyası). Qat yalnız `ru:*` başlıq göstəricilərinə daxil
  olur; `fr1:*` komponentləri və S4 təmiz zəncir nəticəsidir. S1-ə `ru_qat` (qatın payı) və `izah` (real ÜDM-in
  zəncirvari hesablanması qeydi) sütunları əlavə olundu.
* **Təsir metrikası:** baza sıfıra yaxın və ya işarəni dəyişən komponentlərdə (balanslar, artımlar) % yerinə səviyyə fərqi
  (mln AZN axınları üçün % ÜDM); S4 əhəmiyyəti amil × ölçü sinfi üzrə 95-ci faizə normallaşdırılır.
* **Zəlzələ:** bərpa 25/50/25%, itki bərpa ilə azalır — hadisə ilində xalis təsir mənfidir.
* **Stress testləri:** `measures.stress_vector(overrides, with_measures=True, n=4000)` — S1–S8 qaydası istənilən şok
  vektoruna (API bunu istifadə edir); S3 devalvasiyası vahid məzənnə modulundan (İQİ iki il, qeyri-neft analoqu).
* **Public API:** `scalability.head_rows`, `effect`, `base_levels`, `labels` (köhnə `_`-li adlar saxlanılıb),
  `scalability.ru_overlays`, `addf_impulse`, `fx.responses / chain_part / overlay`.

+1σ şoka cavablar (S1, cari vintaj):

<!-- AUTO:s_food -->
| Amil (+1σ) | Göstərici | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---:|---:|---:|---:|---:|
| Daxili xərc şoku (inflyasiya sürprizi) | Büdcə balansı | 0,00 | 0,01 | 0,01 | 0,02 | 0,02 |
| Daxili xərc şoku (inflyasiya sürprizi) | Qeyri-neft real ÜDM səviyyəsi | 0,00 | −1,02 | −1,06 | −1,09 | −1,11 |
| Daxili xərc şoku (inflyasiya sürprizi) | İnflyasiya (İQİ, illik orta) | 0,00 | 4,77 | −0,01 | −0,01 | −0,01 |
| Dünya ərzaq qiymətləri (Brent-dən asılı olmayan hissə) | Büdcə balansı | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| Dünya ərzaq qiymətləri (Brent-dən asılı olmayan hissə) | Qeyri-neft real ÜDM səviyyəsi | 0,00 | −0,17 | −0,26 | −0,26 | −0,27 |
| Dünya ərzaq qiymətləri (Brent-dən asılı olmayan hissə) | İnflyasiya (İQİ, illik orta) | 0,00 | 0,77 | 0,36 | 0,00 | 0,00 |
| Manatın məzənnəsi (+ = devalvasiya) | Büdcə balansı | 0,00 | −0,12 | −0,18 | −0,20 | −0,22 |
| Manatın məzənnəsi (+ = devalvasiya) | Qeyri-neft real ÜDM səviyyəsi | 0,00 | −0,10 | −1,85 | −1,86 | −1,86 |
| Manatın məzənnəsi (+ = devalvasiya) | İnflyasiya (İQİ, illik orta) | 0,00 | 3,12 | 1,47 | 0,00 | 0,00 |
| İdxal qiymətləri (Brent və ərzaqdan asılı olmayan hissə) | Büdcə balansı | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| İdxal qiymətləri (Brent və ərzaqdan asılı olmayan hissə) | Qeyri-neft real ÜDM səviyyəsi | 0,00 | −0,11 | −0,17 | −0,18 | −0,18 |
| İdxal qiymətləri (Brent və ərzaqdan asılı olmayan hissə) | İnflyasiya (İQİ, illik orta) | 0,00 | 0,51 | 0,24 | 0,00 | 0,00 |
<!-- /AUTO:s_food -->
