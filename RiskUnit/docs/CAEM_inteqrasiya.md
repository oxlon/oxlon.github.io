# Nazirliyin CAEM risk vərəqlərinin RiskUnit v2-yə inteqrasiyası

Modul: `riskunit/caem.py` (siqnallar, risk balansı, kateqoriya xəritəsi, qüsurlar) və
`riskunit/caem_model.py` (AZE Model). İşə salma: `python3 -m riskunit.caem [--fetch] [--no-fr13]`.
Mənbə: `data/ministry/CAEM.xlsx` (MD5 `12c22d22…`, bax `data/ministry/README.md`). Nəticələr `output/C1_…C6_`.

## 1. Əsas qayda
CAEM vərəqləri Nazirliyin daxil etdiyi məlumat kimi qəbul edilir və yoxlanılır, həqiqət kimi yox.
RU öz mərkəzi yolunu dərc etmir: proqnoz illəri OxLon (§15.5.1) və MikroUnit FR1 (§15.5.2)
bazalarından götürülür; CAEM yolu yalnız müqayisə üçündür. `AZE Model` gecikmiş hədli sistemdir,
ona görə yalnız **"Nazirlik CAEM modeli — müqayisə (gecikmiş hədli sistem; əsas ötürmə kanalı
deyil)"** kimi göstərilir və RU-nun ötürmə hesablamasına daxil olmur.

## 2. σ-zolaq siqnalları (C1)
Hər vərəq dəyərin ortadan kənarlaşmasını σ vahidi ilə 7 zolağa bölür. Kəsiklər **düsturlardan**
oxunub (başlıqlardan yox):

| Vərəq | Ölçü | Orta / σ (Nazirlik) | Kəsiklər (σ) | Aşağı dəyər |
|---|---|---|---|---|
| `Risk-oil price` | Brent səviyyəsi; statistikalar aylıq 2004M01–2024M11 | 74,40 / 24,78 | ±0,5 / 1 / 1,5 | mənfi |
| `Risk-food price` | illik artım; statistikalar **aylıq** illik artımdan | 4,89 / 17,42 | ±0,5 / 1 / 1,5 | əlverişli |
| `Risk-import price` | illik artım; seçilmiş illər + əl ilə əlavə | 5,10 / 4,46 | **±1 / 1,5 / 2** | əlverişli |
| `Risk-gdp tp` | tərəfdaş ÜDM artımı 2001–2024 | 1,52 / 2,88 | **±1 / 1,5 / 2** | mənfi |

Zolaqlar 1–3 kənar tərəf, 4 neytral (|z| < e1), 5–7 əks tərəfdir. Aşkar edilən uyğunsuzluqlar:
- `Risk-import price` və `Risk-gdp tp`: başlıq ±0,5/1/1,5 σ yazır, düsturlar (F1:K2) ±1/1,5/2 σ istifadə edir.
- `Risk-import price` D28 `=AVERAGE(D6:D12,D20)+0.8+1`: yalnız 2010–2016 və 2024 illəri, üstəgəl
  əl ilə **+1,8 pp**; D29 σ-ya +1,3 əlavə olunub. 2017–2023-də indeks ildə 17–30% artır (məzənnə sabit ikən).
- `Risk-food price`: aylıq illik artımın σ-sı (17,42) illik artıma tətbiq olunur (illik σ 9,84); başlıq
  "Crude oil, Brent" yazır.
- `Risk-oil price`: aylıq blok (C:I) ±1/1,5/2 σ, illik blok (N:T) ±0,5/1/1,5 σ; 2025–2029 yolu sabit
  yazılıb (`=74.711-15*0`) və modelin Brent fərziyyəsindən (70,5; 65,9; …) fərqlidir.
- Bütün zolaq düsturlarında ciddi bərabərsizlik: tam kəsikdəki dəyər heç bir zolağa düşmür (RU onu daxili zolağa aid edir).

**Təkrar:** Python təsnifatı vərəqin öz zolaq sütunları ilə 101/101 halda üst-üstə düşür
(`C1_band_reproduction.csv`).

**Cari məlumatla yenidən hesablama** (`variant = cari`): neft — RU Brent lenti (FRED, aylıq
2004-01–2026-09, orta 74,71, σ 24,36), tarix OxLon faktiki, proqnoz OxLon bazası, MikroUnit FR1
ixrac qiyməti, CAEM yolu və CAEM model Brenti; ərzaq — IMF qlobal ərzaq indeksi (FRED PFOODINDEXM,
CAEM-in FAO sırası 2024M11-də bitir), proqnoz OxLon `eviews_data` FPI_WEO (illik 1,5%); idxal
qiyməti — OxLon `import_price_infl` (2000–2025, əlavəsiz; Nazirlik qaydası ayrıca `nazirlik_qaydasi`
variantında); tərəfdaş ÜDM — OxLon `partner_gdp_realg`. GPR (regional) üçün eyni qayda RU əlavəsidir.

**Nəticə 2026–2030:** neft, ərzaq, idxal qiyməti və tərəfdaş artımı bütün bazalarda (OxLon,
FR1, CAEM yolu) **neytraldır** (|z| ≤ 0,5). İstisnalar: 2026-cı ilin faktiki Brent ortası (93 USD,
z = +0,75) **əlverişli**, regional GPR (z = +2,7) **mənfi**. Qeyd: OxLon `assumptions.csv` və
`external_block` idxal qiyməti proqnozları bir-birinə ziddir (2027: +5,3 vs −3,8).

## 3. Risk balansı (C2)
Nazirliyin indeksi: 5 kateqoriya, çəkilər neft 12, geosiyasət, tərəfdaş artımı, idxal və ərzaq
qiymətləri 2-şər (cəmi 20); bal 0 (ən əlverişli) – 2–3 (neytral) – 5 (ən əlverişsiz); ümumi =
SUMPRODUCT(bal, çəki), 0–100. Oxu: >55 mənfi tərəfə meyl, 45–55 balans, <45 müsbət tərəfə meyl.

**Məlumat əsaslı versiya (RU, 2022–2030).** Hər kateqoriya balı mövcud komponentlərin sadə ortasıdır:
1. `s_signal` — C1 siqnalının Nazirliyin öz 0–5 şkalası ilə balı (`Risk-oil price` N31:T31,
   `Risk-food price` P43:V43, `Risk-import price` E26:K26): neytral zolaq ↔ 2–3, hər növbəti zolaq ↔
   +1 bal, son kəsikdən kənar ↔ 5 (və ya 0). Kəsiklər arasında xətti, kəsilməz, monoton.
2. `s_indicator` — cari il üçün RU göstərici bazasının z-balı (`FR1_indicator_base.csv`: `brent`,
   `gpr_reg`), eyni şkala ilə (±0,5/1/1,5 σ).
3. `s_fr2` — FR2 risk skoru (P×I, 1–25; `FR2_risk_scores.csv`, öz üfüq ilində): aşağı prioritet
   (1–6) ↔ 2–3, orta (6–12) ↔ 3–4, yüksək (12–25) ↔ 4–5 (hədlər `input/hedler.csv`). FR2 yalnız
   aşağı quyruğu ölçdüyü üçün bu komponent 2-dən aşağı düşmür. R01 → neft, R06 → geosiyasət, R05 → tərəfdaş.
4. Heç bir komponent yoxdursa (məs. 2028–2030 geosiyasət) bal neytral 2,5 qəbul olunur və qeyd edilir.

| İl | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|---|---|---|
| Nazirlik (əl ilə) | 43 | – | 47 | 49 | – | – | – | – | – |
| Məlumat əsaslı | 37,8 | 47,0 | 50,3 | 55,4 | 41,3 | 62,4 | 52,5 | 52,4 | 52,6 |

2025-də fərq geosiyasətdən gəlir (GPR z = +2,1 → 5,0, Nazirlik 3,5). 2026 aşağıdır, çünki faktiki
Brent yüksəkdir (göstərici z = +1,9 → neft balı 1,4). 2027 yüksəkdir, çünki FR2 R01 skoru 15-dir
(yüksək prioritet → 4,2). Nazirliyin ərzaq balı öz siqnalına uyğun gəlmir (2024: zolaq 2 → 0–1,
yazılıb 2,5; 2025: neytral → 2–3, yazılıb 1,0).

## 4. Kateqoriya xəritəsi (C3)
Neft ↔ R01 (tam; R03, R14 əlaqəli); geosiyasət ↔ R06; tərəfdaş artımı ↔ R05 (R07 əlaqəli). İdxal
və ərzaq qiymətləri üçün RU-da amil riski yoxdur (yalnız R12 nəticə riski) — yeni sətir təklifi:
**R17** qeyri-neft idxal qiymətlərinin kəskin artımı (hadisə: z > +1σ, tarixi tezlik 4/26 = 15%),
**R18** dünya ərzaq qiymətlərinin şoku (z > +0,5σ, 6/22 = 27%). R02, R04, R08–R13, R15, R16-nın
CAEM-də kateqoriyası yoxdur. Yeni sətirləri Nazirlik təsdiq etməlidir; ehtimal ilkin olaraq tarixi tezlikdir.

## 5. AZE Model — müqayisə (C4, C5)
y_t = Bc + B1·y_{t−1} + B2·e_t, 48 vəziyyət. B1 = `AZE Model`!C211:AX258 = MMULT(MINVERSE(A0), A1),
B2 = C262:AX309 = MMULT(MINVERSE(A0), A2) (fərq 0); Ac (C159:C206) sıfırdır. Borc sətirləri (d_y,
dd_y, df_y) 8a düsturları ilə hesablanır. **Yoxlama:** yüklənmiş +1 pp CPI şoku 48×13 cədvəldə
tam təkrarlanır (max|Δ| = 0): uçot dərəcəsi +2,42, ÜDM artımı −0,13 / −0,20 (`C4_caem_irf_validation.csv`, 15/15).
Kitabxana: 8a-nın 26 struktur şoku (+1, h=1) və 7. Scenario-nun 14 şoku (h=1..3, ±1; ən yaxın AZE
şokuna xəritələnib, bax `C4_caem_shock_index.csv`) — 40 × 48 × 13.

**Ötürmə müqayisəsi (C5, 2026 → 2030):**
| Şok | Göstərici | CAEM | MikroUnit FR1 | OxLon |
|---|---|---|---|---|
| Brent +10 USD | ÜDM səviyyəsi, % | +0,79 → −0,04 | +0,18 → −0,08 | – |
| | qeyri-neft səviyyəsi, % | +0,67 → +2,34 | +0,25 → +0,38 | – |
| | inflyasiya, pp | +0,20 → −0,03 | +0,07 → +0,01 | FR13: +2,20 → +0,01 |
| | büdcə, ÜDM-ə % | 0,00 → −0,36 (ilkin) | +0,15 → +0,04 | FR12 cari hesab +3,9 → +2,6 |
| Xarici tələb +10% | ÜDM səviyyəsi, % | +2,98 → −0,11 | +1,03 → +1,19 | – |
| Uçot dərəcəsi −200 bp | ÜDM səviyyəsi, % | +0,20 → +0,53 | +0,22 → +0,23 | kanal yoxdur |
| Dövlət investisiyası +1 mlrd | ÜDM səviyyəsi, % | 0,00 → +0,14 | +0,70 → +0,98 | kanal yoxdur |

CAEM cavabları qısamüddətli və daha kəskindir, gecikmiş hədlər və vahid köklər səbəbindən səviyyələr
"sürüşür"; dövlət investisiyası kanalı demək olar ki, işləmir (gcap_y g_y/pb_y-yə düşmür — C6).
FR1 addım cavabları (06.10.2026 01:04 vintajı) yoxlanılıb: balance_n artıq salınmır (`C5_fr1_oscillation.csv`).

## 6. Qüsurlar reyestri (C6)
`C6_caem_findings.csv` Nazirlik üçün təhvil sənədidir: vərəq, xana, problem, sübut (canlı oxunmuş
dəyər/düstur), nəticə və tövsiyə. Əsasları: #REF!/#NAME?/#VALUE! xətaları (15 vərəq), istehsal və xərc
ÜDM fərqi (P384:T384, cəmi 41 965), sıfır şokla sıfırdan fərqli "Difference", CPI yelpiyinin səhv
sətrə istinadı, bazadan yuxarı pessimist yol, 2027-dən mənfi ehtiyatlar və −16,6% cari hesab,
Brent yollarının uyğunsuzluğu, köhnə 2025, idxal qiyməti qaydası, 8a xarici borc düsturu (F109 → E108),
xərc şokunun işarəsi.

## 7. Məhdudiyyətlər və Nazirlik qərarları
- Ərzaq indeksi IMF (PFOODINDEXM) ilə əvəz edilib; FAO sırası lentə əlavə edilməlidir.
- Geosiyasət üçün proqnoz yoxdur; 2028–2030 neytral qəbul edilir.
- Məlumat əsaslı balların komponent çəkiləri bərabərdir — Nazirlik dəyişə bilər.
- 7. Scenario şoklarının AZE Model xəritələnməsi yaxın analoqdur (SC07/SC09 → CR proksi).
- Yeni R17/R18 sətirləri və CAEM qüsurlarının düzəlişi Nazirliyin qərarıdır.
