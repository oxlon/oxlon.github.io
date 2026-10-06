# MİİS §15.5.3 — İqtisadi risklərin idarəedilməsi və qərar dəstək sistemi
## Metodologiya sənədi

**Alt modul:** 15.5.3 İqtisadi Risklərin İdarəedilməsi və Qərar Dəstək Sistemləri
**Sifarişçi:** Azərbaycan Respublikasının İqtisadiyyat Nazirliyi
**Əsas:** Texniki Tapşırıq, §15.5.3 (FR1–FR4, NFR1–NFR3); OxLon Metodologiya Blueprint v0.1, L4 qatı

Bu sənəddəki bütün rəqəmlər `AUTO` markerləri arasında yerləşir və `python3 run_all.py` hər dəfə işlədikdə
nəticə fayllarından yenidən yazılır. Sənəd nəticələrdən ayrıla bilməz.

<!-- AUTO:status -->
Vəziyyət tarixi **2026-10-06**, qiymətləndirmə ili **2027**, baza identifikatoru **B-949799ba38**. Birgə simulyasiya: 20000 ssenari, butstrap illəri 2003–2025. Qeyri-neft artımı 2027: median 5,43%, P10 1,33%, P5 0,11% (makro baza 5,43%). Yüksək prioritetli risklər: R12, R01; xəbərdarlıq sayı 18.
<!-- /AUTO:status -->

---

## 1. Tələb və cavab

| Tələb | Qəbul meyarı (TT) | Həll | Yoxlama |
|---|---|---|---|
| FR1 | ən azı 3 risk kateqoriyası; hər risk üçün ehtimal və təsir; xarici-siyasi hadisələrin və təbii fəlakətlərin kəmiyyətləşdirilməsi və ötürmə kanalları | 5 ailə, 16 risk; 19 göstəricili baza; GPR indeksləri + hadisə xronologiyası; təhlükə × məruz qalma × həssaslıq; ötürmə kanalları cədvəli | `tests/` FR1 bloku |
| FR2 | risk skoru = ehtimal × təsir; avtomatik sıralama; yüksək prioritet üçün xəbərdarlıq | birgə Monte Karlo; 5×5 skor; Eyler quyruq töhfəsi; 6 növ xəbərdarlıq | FR2 bloku |
| FR3 | hər risk üçün ən azı bir tədbir; icra statusunun izlənməsi | tədbirlər reyestri (tədbir, məsul, müddət, status); risk-tədbir əlaqəsi; status tarixçəsi; qalıq risk; 8 stress ssenarisi | FR3 bloku |
| FR4 | rəhbərlik üçün icmal risk paneli; PDF/Excel ixracı | `site/index.html`, `site/analitik.html`; PDF və Excel hər rol üçün; JSON API | FR4 bloku |
| NFR1 | sadə etalona qarşı geriyə sınaq; yalnız proqnoz anında mövcud məlumat; paylanmanın ayrıca statistik testləri; rüblük yeniləmə və sənədləşdirmə | rüblük test reyestri (D, P, E, R ailələri); kalibrləmə qaydası simulyasiyaya avtomatik tətbiq olunur; vintaj arxivi | NFR1 bloku |
| NFR2 | yeni məlumatdan 24 saat ərzində skorların yenilənməsi | `update.py`: barmaq izi, gündəlik cədvəl, izləmə rejimi, gecikmə jurnalı | NFR2 bloku |
| NFR3 | istifadəçi roluna uyğun fərqli detallıq | `input/rollar.csv` ilə idarə olunan iki rol: rəhbərlik və analitik | NFR3 bloku |

## 2. Arxitektura: bir nüvə, üç baxış

Risk bölməsi öz mərkəzi yolunu nəşr etmir (Blueprint §1.1). Makro model (§15.5.1) iqtisadiyyatın şərti
orta yolunu, mikro bölmə (§15.5.2) sektor strukturunu və şok ötürmə mexanizmini verir; risk bölməsi bu
yolun ətrafındakı paylanmanı, xüsusilə aşağı quyruğu hesablayır.

| Mənbə | Nə götürülür |
|---|---|
| Makro model §15.5.1 (`outputs/forecast_long.csv`, `data/assumptions.csv`, `outputs/validation_backtest.csv`) | qeyri-neft artımı, inflyasiya, Brent, cari hesab üzrə mərkəzi yol və 80%/50% yelpik zolaqları; cari hesab üçün başabaş Brent qiyməti; geriyə sınaq xətaları |
| Mikro bölmə §15.5.2 FR1 (`FR1_multipliers.csv`, `FR1_forecast_full.csv`, `FR1_fan_draws.csv`, `FR1_analysis_dataset.csv`) | struktur modelin şoklara addım cavabları (Brent, xarici tələb, dövlət investisiyası, kredit faizi); büdcə bloku; 2001–2025 qeyri-neft tarixi |
| Mikro bölmə FR10, FR12 | müəssisə və rəqabət erkən xəbərdarlıq siqnalları, Kurno ssenariləri |
| Canlı axınlar | Brent, VIX, ABŞ faizləri, EUR/USD (FRED); GPR (Caldara–Iacoviello); EPU (Baker–Bloom–Davis); zəlzələ kataloqu (USGS); yağıntı (ERA5) |

Hər çıxış faylı `baseline_id` sütununu daşıyır: bu, yuxarı axın fayllarının SHA-256 heşlərindən qurulan
identifikatordur və hansı makro/mikro buraxılışından istifadə edildiyini birmənalı göstərir.

## 3. FR1 — risk amillərinin təhlili və qiymətləndirilməsi

### 3.1 Taksonomiya

| Ailə | Risklər | Ölçmə |
|---|---|---|
| MAL — maliyyə və əmtəə bazarları | R01 neft qiymətinin enməsi; R02 maliyyə şəraitinin sərtləşməsi; R03 məzənnəyə təzyiq; R04 bank sektoru | Brent, VIX, ABŞ faizləri, kredit faizi |
| XSI — xarici-siyasi və xarici iqtisadi | R05 tərəfdaş resessiyası; R06 regional geosiyasi eskalasiya; R07 pul baratlarının azalması | tərəfdaş ÜDM-i, GPR (qlobal və ölkə üzrə), EPU, pul baratları |
| TEB — təbii fəlakətlər | R08 zəlzələ; R09 quraqlıq; R10 daşqın və Xəzərin səviyyəsi | USGS kataloqu, ERA5 SPI |
| DAX — daxili makroiqtisadi | R11 büdcə; R12 inflyasiya; R13 qeyri-neft artımı (Growth-at-Risk); R14 enerji keçidi | birgə simulyasiyanın nəticə paylanmaları |
| SEK — sektor (mikro) | R15 emal sahələrində gərginlik; R16 rəqabət mühitinin pisləşməsi | FR10 və FR12 erkən xəbərdarlıq sistemləri |

Risk növləri: **amil** (risk mənbəyi; ehtimal və təsir simulyasiyadan), **nəticə** (R11–R13; həddin pozulma
ehtimalı və həddən kənar gözlənilən çatışmazlıq), **siqnal** (R15–R16; mikro EWS), **ekspert** (R04, R10, R14
ehtimalı; Nazirliyin təsdiqinə təqdim olunan, ayrıca işarələnmiş örtük).

### 3.2 Xarici-siyasi hadisələrin kəmiyyətləşdirilməsi

Xarici-siyasi hadisələr qəzet məqalələrinə əsaslanan Geosiyasi Risk indeksi (Caldara və Iacoviello, 2022) ilə
ölçülür. Qlobal indeksdən əlavə regional kompozit qurulur: Rusiya, Ukrayna, İsrail və Türkiyə ölkə
indekslərinin ortası. Ehtimal empirik keçid tezliyidir: cari ilin rejimində (75-ci faizdən yuxarı/aşağı)
olan illərdən sonra gələn ildə indeksin tarixi 90-cı faizi aşma tezliyi. Avtoreqressiv model qurulmur.

Ötürmə kanalları ayrıca qiymətləndirilir: (i) regional GPR sıçrayışı → Brent qiyməti (aylıq lokal
proyeksiyalar, h = 0…11); (ii) regional GPR → tərəfdaş ölkələrin artımı; (iii) regional GPR → pul baratları.
Statistik zəif kanal sıfırlanmır — onun əmsal qeyri-müəyyənliyi simulyasiyaya daxil edilir. Hadisə
xronologiyası (`input/hadise_xronologiyasi.csv`) 17 epizodu sənədləşdirir; hər epizod ətrafında GPR, Brent,
VIX və məzənnənin dəyişməsi məlumatdan hesablanır (`output/FR1_event_chronology.csv`).

<!-- AUTO:fr1_channels -->
| Kanal | İzahedici | Əmsal | St. xəta | p | n | Nümunə | Sübut |
|---|---|---:|---:|---:|---:|---|---|
| Pul baratlarının artımı ← Brent (tərəfdaş artımı əmsalı yanlış işarəli və əhəmiyyətsiz olduğu üçün çıxarılıb) | dln_brent | 0,324 | 0,289 | 0,273 | 29 | 1997–2025 | zəif — parametr qeyri-müəyyənliyi simulyasiyaya daxildir |
| Dövlət investisiyasının real artımı (log) ← Brent (cari və 1 il gecikmə; 2007–2025, 2005–06 sıra qırılması xaric) | dln_brent | 0,525 | 0,227 | 0,034 | 19 | 2007–2025 | güclü (p<0,05) |
| Dövlət investisiyasının real artımı (log) ← Brent (cari və 1 il gecikmə; 2007–2025, 2005–06 sıra qırılması xaric) | dln_brent_l1 | 0,351 | 0,118 | 0,009 | 19 | 2007–2025 | güclü (p<0,05) |
| Dünya ərzaq qiymətləri artımı ← Brent (ortoqonallaşdırma; qalıq = R18 amili) | dln_brent | 0,208 | 0,078 | 0,012 | 33 | 1993–2025 | güclü (p<0,05) |
| İdxal qiymətləri inflyasiyası (USD) ← Brent, ərzaq qiymətlərinin öz hissəsi (qalıq = R17 amili) | dln_brent | 0,455 | 0,028 | 0,000 | 25 | 2001–2025 | güclü (p<0,05) |
| İdxal qiymətləri inflyasiyası (USD) ← Brent, ərzaq qiymətlərinin öz hissəsi (qalıq = R17 amili) | food_own | 0,679 | 0,068 | 0,000 | 25 | 2001–2025 | güclü (p<0,05) |
| İnflyasiya ← AZN ilə idxal qiymətləri inflyasiyası (cari + 1 il gecikmə; asılı dəyişənin gecikməsi yoxdur) | impA | 0,176 | 0,042 | 0,000 | 25 | 2001–2025 | güclü (p<0,05) |
| İnflyasiya ← AZN ilə idxal qiymətləri inflyasiyası (cari + 1 il gecikmə; asılı dəyişənin gecikməsi yoxdur) | impA_l1 | 0,084 | 0,042 | 0,056 | 25 | 2001–2025 | orta (p<0,10) |
| Kənd təsərrüfatı əlavə dəyəri ← SPI (quraqlıq indeksi) | spi | 0,936 | 1,006 | 0,362 | 25 | 2001–2025 | zəif — parametr qeyri-müəyyənliyi simulyasiyaya daxildir |
| İnflyasiya ← SPI (AZN idxal qiymətləri nəzarətdə) — quraqlığın təklif-qiymət kanalının yoxlanması | impA | 0,177 | 0,045 | 0,001 | 25 | 2001–2025 | güclü (p<0,05) |
| İnflyasiya ← SPI (AZN idxal qiymətləri nəzarətdə) — quraqlığın təklif-qiymət kanalının yoxlanması | impA_l1 | 0,082 | 0,047 | 0,098 | 25 | 2001–2025 | orta (p<0,10) |
| İnflyasiya ← SPI (AZN idxal qiymətləri nəzarətdə) — quraqlığın təklif-qiymət kanalının yoxlanması | spi | −0,372 | 1,116 | 0,742 | 25 | 2001–2025 | zəif — parametr qeyri-müəyyənliyi simulyasiyaya daxildir |
| Daxili kredit faizi dəyişməsi ← ABŞ faiz dəyişməsi | d_us | −0,044 | 0,160 | 0,785 | 23 | 2003–2025 | zəif — parametr qeyri-müəyyənliyi simulyasiyaya daxildir |
| Tərəfdaş artımı ← regional GPR dəyişməsi | dl_gpr_reg | 0,007 | 0,010 | 0,483 | 26 | 2000–2025 | zəif — parametr qeyri-müəyyənliyi simulyasiyaya daxildir |
| Pul baratlarının artımı ← regional GPR dəyişməsi | dl_gpr_reg | 0,256 | 0,117 | 0,038 | 29 | 1997–2025 | güclü (p<0,05) |
| Qeyri-neft artımı ← Brent, tərəfdaş artımı (reduksiya forması; yalnız yoxlama) | dln_brent | 0,091 | 0,035 | 0,015 | 25 | 2001–2025 | güclü (p<0,05) |
| Qeyri-neft artımı ← Brent, tərəfdaş artımı (reduksiya forması; yalnız yoxlama) | partner_g | 0,153 | 0,428 | 0,723 | 25 | 2001–2025 | zəif — parametr qeyri-müəyyənliyi simulyasiyaya daxildir |
| Brent (log, h=0 ay) ← regional GPR sıçrayışı | Δ ln GPR_reg | 0,030 | 0,017 | 0,074 | 472 | 1987-06-01 00:00:00–2026-09-01 00:00:00 | orta (p<0,10) |
| Brent (log, h=3 ay) ← regional GPR sıçrayışı | Δ ln GPR_reg | 0,012 | 0,030 | 0,686 | 469 | 1987-06-01 00:00:00–2026-06-01 00:00:00 | zəif |
| Brent (log, h=11 ay) ← regional GPR sıçrayışı | Δ ln GPR_reg | −0,003 | 0,024 | 0,900 | 461 | 1987-06-01 00:00:00–2025-10-01 00:00:00 | zəif |
| Brent mərkəzi yolu: makro struktur yolu ⊕ dəyişməz (RW) yol, tərs-MSE çəkiləri | struktur çəkisi | 0,618 | — | — | 85 | makro validation_backtest h=1 | RMSE struktur 0.242 / RW 0.308 (log) |
<!-- /AUTO:fr1_channels -->

**Nəticə.** Geosiyasi şoklar neft qiymətini təsir anında və ilk rübdə qaldırır, 12 ay ərzində təsir sönür;
tərəfdaş artımına illik təsir statistik olaraq təsdiqlənmir. Regional eskalasiya pul baratlarını artırıb
(2022 epizodu). Birbaşa kanallar (tranzit, logistika, turizm) məlumatla ölçülmür və S4 stress ssenarisi ilə
modelləşdirilir.

### 3.3 Təbii fəlakətlərin kəmiyyətləşdirilməsi

Təbii təhlükələr zaman sırası şoku kimi deyil, təhlükə × məruz qalma × həssaslıq kimi modelləşdirilir.

- **Zəlzələ (R08).** USGS kataloqunda (38,3–42,0° şm. e., 44,7–50,7° ş. u.; M ≥ 4,5; 1950–cari) 30 günlük
  pəncərə ilə klasterləşdirilmiş epizodlar iki maqnituda pilləsinə bölünür; hər pillə üçün Puasson tezliyi
  qiymətləndirilir. Birbaşa zərər (ÜDM-ə %) loqnormal paylanır; hadisə ilində məhsul itkisi = 0,25 × zərər,
  növbəti ildə bərpa; büdcəyə düşən hissə 0,5. Zərər parametrləri kalibrləmə fərziyyəsidir və Fövqəladə
  Hallar Nazirliyinin zərər məlumatı ilə əvəz edilməlidir (`input/hedler.csv`).
- **Quraqlıq (R09).** ERA5 reanaliz məlumatı ilə dörd kənd təsərrüfatı bölgəsi (Gəncə-Qazax, Aran, Şəki-Zaqatala,
  Lənkəran) üzrə hidroloji il (oktyabr–sentyabr) yağıntısından WMO standartında SPI (qamma paylanması,
  1961–2020 istinad dövrü). Həssaslıq: kənd təsərrüfatı əlavə dəyərinin SPI-yə HAC reqressiyası; məruz qalma:
  kənd təsərrüfatının qeyri-neft ÜDM-də payı.
- **Daşqın və Xəzərin səviyyəsi (R10).** Hidroloji sıralar daxil olana qədər ekspert örtüyü.

<!-- AUTO:fr1_hazards -->
Zəlzələ: M 5,5–6,0 — 13 epizod, λ = 0,169/il; M ≥ 6,0 — 4 epizod, λ = 0,052/il (76,8 il). Quraqlıq: P(SPI ≤ −1,0) = 15,2%; son 12 ayın SPI-si −0,41 (2026-09).
<!-- /AUTO:fr1_hazards -->

### 3.4 Neft qiyməti, büdcə reaksiyası və məzənnə

- **İki baxış (v2).** *Baza mərkəzli baxış* (skorlar, istilik xəritəsi, stress testləri, DSA): Brent makro
  modelin fərziyyəsində saxlanılır və hər göstəricinin medianı rəsmi bazaya bərabərdir — risk bölməsi öz mərkəzi
  yolunu dərc etmir. *Canlı şərtləndirilmiş baxış*: Brent-in mərkəzi yolu makro struktur yolu ilə son ayın
  səviyyəsinin tərs-MSE çəkili birləşməsidir (çəkilər makro geriyə sınaqdan); cari il üçün il ərzində müşahidə
  olunmuş qiymət ortası istifadə olunur. Canlı baxışda median yalnız canlı fərqin deterministik təsiri qədər
  (FR1 multiplikatorları, D6 monitorundakı eyni ötürmə) bazadan sürüşür (bölmə 12).
- **Prosiklik investisiya reaksiyası (v2).** Tarixi məlumat dövlət investisiyasının Brent-ə prosiklik reaksiyasını
  göstərir (cari və bir il gecikmə; gecikmiş asılı dəyişən yoxdur). v2-də: (i) elastiklik 2007–2025 üzrə log artımla
  qiymətləndirilir — `rinv_state` sırasında 2005–06 real/nominal qırılması (deflyator nisbəti 1,6 → 0,9; 2006-da
  +257% «real» artım) v1 əmsalını şişirdirdi; (ii) FR1 Brent multiplikatorunun özündə olan investisiya cavabı
  (`rinv_state` +3,2…3,8% / +10 USD) çıxılır — yalnız artıq hissə ayrıca kanaldır; (iii) reaksiya ARDNF transferi ilə
  maliyyələşir (2014→2016: transfer −18%, dövlət investisiyası −57%, balans −0,5 → −0,4% ÜDM), ona görə dövlət
  büdcəsinin balansına neytraldır; yalnız T09 (kəsintidən imtina) altında transfer yolundan yuxarı saxlanılan
  investisiya kəsirlə maliyyələşir və FR1 `balance_n` cavabı ilə büdcəyə düşür (T09-un fiskal dəyəri).
- **Devalvasiya (R03).** Tətik: Brent illik ortasının əvvəlki üç ilin ortasından ≥ 30% enməsi (1998, 2015,
  2016, 2020); şərti devalvasiya tezliyi bu epizodlardan hesablanır. Təsir — 2015–2016 analoqunun neft və
  dövlət investisiyası kanalları çıxıldıqdan sonrakı qalığı; inflyasiyaya ötürmə 2014–2017 məzənnə dəyişməsindən.

## 4. FR2 — miqyas, təsir dərəcəsi, prioritetləşdirmə

### 4.1 Birgə simulyasiya

1. Amil innovasiyaları (Brent, tərəfdaş artımı, pul baratları, kredit faizi, regional GPR) tarixi illərin bütöv
   vektorlar kimi butstrapı ilə çəkilir: amillər arasındakı müşahidə olunmuş korrelyasiya parametrik kopula
   olmadan qorunur.
2. Təbii təhlükələr, şərti devalvasiya, mikro siqnallar və ekspert örtükləri müstəqil hadisələr kimi əlavə olunur.
3. Hər amil mikro FR1 struktur modelinin addım cavablarının paylanmış gecikmə bükülməsi ilə, yaxud
   qiymətləndirilmiş birbaşa kanal ilə qeyri-neft ÜDM-ə, inflyasiyaya və büdcə balansına ötürülür.
4. Nüvənin öz qalıq qeyri-müəyyənliyi (t₅ paylanması) elə seçilir ki, ümumi yayılma kalibrlənmiş yelpik eninə
   bərabər olsun: qeyri-neft artımı və inflyasiya üçün makro yelpik × NFR1 əmsalı, büdcə balansı üçün FR1 yelpiyi ×
   NFR1 əmsalı (P15: təsadüfi gəzinti xətası etalonu). Qalığın minimum payı (0,25 σ)²-dir; amillərin dispersiyası
   hədəfi aşmır (`FR2_band_layering.csv`).
5. Mərkəzləmə: baza baxışında hər il üçün median = rəsmi baza (fərq nüvənin qalığına yazılır); hadisə kanalları
   (devalvasiya, zəlzələ, ekspert, mikro siqnallar) aşağı əyriliyi saxlayır — orta − median = risklərin balansı.
6. R17/R18 (CAEM kateqoriyaları): idxal qiymətləri və dünya ərzaq qiymətləri Brent-dən (ərzaq həm də idxaldan)
   ortoqonallaşdırılır, qalıqlar eyni illərlə butstrap olunur və HAC ötürmə əmsalı ilə inflyasiyaya keçir.

Hər kanal ayrıca toplanan komponentdir, ona görə dispersiya payları və aşağı quyruq (P10) töhfələri dəqiq
Eyler bölgüsüdür.

<!-- AUTO:fr2_contrib -->
| Kanal | Dispersiya payı % | P10 quyruğunda töhfə f.b. |
|---|---:|---:|
| Modelin qalıq qeyri-müəyyənliyi | 65,9 | −3,70 |
| Neft qiyməti — prosiklik investisiya reaksiyası (R01) | 13,1 | −0,92 |
| Neft qiyməti — birbaşa (R01) | 11,6 | −0,68 |
| Tərəfdaş tələbi (R05) | 4,3 | −0,26 |
| Pul baratları (R07) | 2,5 | −0,11 |
| Geosiyasi eskalasiya (R06) | 1,3 | −0,07 |
| Devalvasiya (R03) | 0,4 | −0,03 |
| Zəlzələ (R08) | 0,2 | −0,02 |
| Bank sektoru (R04, ekspert) | 0,3 | −0,02 |
| Rəqabət (R16) | 0,2 | −0,01 |
| Enerji keçidi (R14) | 0,0 | 0,00 |
| Quraqlıq (R09) | 0,1 | 0,00 |
| Daşqın (R10, ekspert) | 0,0 | 0,00 |
| Emal sahələri (R15) | 0,0 | 0,00 |
| Kredit faizi (R02) | 0,0 | 0,01 |
<!-- /AUTO:fr2_contrib -->

### 4.2 Skorlama

- **Ehtimal (P):** qiymətləndirmə ilində risk hadisəsinin baş verdiyi ssenarilərin payı.
- **Təsir (T):** həmin ssenarilərdə riskin kanal töhfəsinin gözlənilən dəyərdən sapması — qeyri-neft artımı (f.b.),
  inflyasiya (f.b.), büdcə balansı (ÜDM-ə %); üç ölçüdən ən ağır pillə götürülür.
- **Skor = P-pilləsi × T-pilləsi** (1–25). Pillə hədləri və prioritet hədləri `input/hedler.csv`-dədir və risk
  iştahı qərarı kimi Nazirlik tərəfindən təsdiq edilir.
- **Kəmiyyət prioriteti:** P10 quyruğuna Eyler töhfəsi. İstilik xəritəsi təqdimat qatıdır (Blueprint, FR2 qeydi).

<!-- AUTO:fr2_scores -->
| № | ID | Risk | Ehtimal % | Qeyri-neft f.b. | İnflyasiya f.b. | Büdcə % ÜDM | P | T | Skor | Prioritet | Quyruq töhfəsi f.b. |
|---|---|---|---:|---:|---:|---:|---|---|---|---|---:|
| 1 | R12 | İnflyasiyanın hədəf diapazonundan yuxarı olması | 47,4 | 0,00 | 3,67 | 0,00 | 4 | 5 | 20 | yüksək | — |
| 2 | R01 | Neft qiymətinin kəskin enməsi | 47,8 | 1,15 | −2,71 | 0,24 | 4 | 4 | 16 | yüksək | −1,60 |
| 3 | R13 | Qeyri-neft artımının kəskin zəifləməsi (Growth-at-Risk) | 14,1 | 1,85 | 0,00 | 0,00 | 2 | 5 | 10 | orta | — |
| 4 | R03 | Manatın məzənnəsinə təzyiq və devalvasiya | 9,8 | 0,19 | 4,10 | 0,00 | 2 | 5 | 10 | orta | −0,03 |
| 5 | R07 | Pul baratlarının kəskin azalması | 22,4 | 0,67 | 0,00 | 0,00 | 3 | 3 | 9 | orta | −0,11 |
| 6 | R14 | Enerji keçidi: karbohidrogen tələbinin struktur azalması | 25,0 | 0,56 | −1,17 | 0,13 | 3 | 3 | 9 | orta | — |
| 7 | R05 | Tərəfdaş ölkələrdə iqtisadi tənəzzül | 14,2 | 0,69 | −0,23 | 0,05 | 2 | 3 | 6 | orta | −0,26 |
| 8 | R04 | Bank sektorunda aktiv keyfiyyətinin pisləşməsi | 9,6 | 0,37 | 0,09 | 0,05 | 2 | 3 | 6 | orta | −0,02 |
| 9 | R11 | Büdcə balansının pisləşməsi | 8,7 | 0,00 | 0,00 | 0,64 | 2 | 3 | 6 | orta | — |
| 10 | R16 | Rəqabət mühitinin pisləşməsi | 46,5 | 0,09 | 0,14 | 0,00 | 4 | 1 | 4 | aşağı | −0,01 |
| 11 | R02 | Maliyyə şəraitinin sərtləşməsi (kredit faizi) | 8,9 | 0,20 | −0,07 | 0,03 | 2 | 2 | 4 | aşağı | 0,01 |
| 12 | R06 | Regional geosiyasi eskalasiya | 40,9 | −0,12 | 0,03 | −0,01 | 4 | 1 | 4 | aşağı | −0,07 |
| 13 | R18 | Dünya ərzaq qiymətlərinin şoku | 7,8 | 0,00 | 0,73 | 0,00 | 2 | 2 | 4 | aşağı | 0,00 |
| 14 | R08 | Güclü zəlzələ | 19,6 | 0,09 | 0,01 | 0,05 | 3 | 1 | 3 | aşağı | −0,02 |
| 15 | R09 | Quraqlıq | 15,5 | 0,09 | 0,00 | 0,00 | 3 | 1 | 3 | aşağı | 0,00 |
| 16 | R15 | Emal sənayesi sahələrində maliyyə gərginliyi | 16,5 | 0,03 | 0,00 | 0,00 | 3 | 1 | 3 | aşağı | 0,00 |
| 17 | R10 | Daşqın və Xəzər dənizinin səviyyəsinin dəyişməsi | 10,6 | 0,09 | 0,04 | 0,04 | 2 | 1 | 2 | aşağı | 0,00 |
| 18 | R17 | Qeyri-neft idxal qiymətlərinin kəskin artımı | 4,5 | 0,00 | 0,55 | 0,00 | 1 | 2 | 2 | aşağı | 0,00 |
| 19 | R19 | Proqnoz qeyri-müəyyənliyi / model riski | 0,0 | 1,04 | 0,00 | 0,00 | 0 | 0 | 0 | ayrıca göstərici | — |
<!-- /AUTO:fr2_scores -->

### 4.3 Xəbərdarlıqlar

Altı növ: yüksək prioritet; əvvəlki yeniləmədən bəri skor artımı (≥ 4 bal); göstərici həddi (tarixi paylanmanın
pis istiqamətdə ≥ 90-cı faizi); baza köhnəlib (canlı şərtləndirilmiş median makro baza yolundan ≥ 1 f.b. və ya
Brent mərkəzi yolu makro fərziyyədən ≥ 20% fərqlənir); tədbir gecikir; məlumat köhnəlib.

### 4.4 Müstəqil yoxlama: Growth-at-Risk kvantil reqressiyası

Blueprint-də nəzərdə tutulan kvantil reqressiyası (gələn ilin qeyri-neft artımı Brent dəyişməsi və regional GPR
üzərində) müstəqil yoxlama kimi saxlanılır. Geriyə sınaqda o, sadə etalonu üstələmir (bölmə 7): 2001–2025
nümunəsi 2014-cü il struktur qırılmasını əhatə edir və 13 nümunədən-kənar müşahidə quyruq kvantilləri üçün
kifayət deyil. Panel bu modeli qərar üçün istifadə etmir; birgə simulyasiya əsas paylanmadır.

## 5. FR3 — tədbirlər, strateji yanaşmalar, qalıq risk

- **Reyestr** (`input/tedbirler_reyestri.csv`): tədbir, əlaqəli risklər, strategiya (azaltma, ötürmə, qaçınma,
  qəbul, izləmə), alət növü, məsul qurum, başlama, müddət, status (təklif, təsdiqlənib, icrada, tamamlanıb,
  dayandırılıb), gözlənilən effekt, KPI. Hər yeniləmədə lüğət və tarix yoxlaması aparılır.
- **Status izlənməsi:** status və ya müddət dəyişdikdə `output/FR3_status_history.csv`-ə sətir əlavə olunur;
  müddəti keçmiş və tamamlanmamış tədbir xəbərdarlıq yaradır.
- **Qalıq risk:** tədbirlərin effekti icra statusu ilə çəkilir (cari) və tam icra fərziyyəsi ilə (hədəf).
- **Alətlərin ölçüsü:** kontrtsiklik investisiya, monetar yumşalma və prosiklik kəsintidən imtina üçün tələb olunan
  ölçü FR1 multiplikatorlarından hesablanır.
- **Stress ssenariləri** (Blueprint L4 siyahısı): eyni ötürmə mexanizmindən keçən elan olunmuş şok vektorları,
  T09 tədbiri ilə və tədbirsiz.

<!-- AUTO:fr3_stress -->
| ssenari | ad | sapma büdcə balansı, % ÜDM | sapma inflyasiya, f.b. | sapma qeyri-neft artımı, f.b. | tedbirin_effekti büdcə balansı, % ÜDM | tedbirin_effekti inflyasiya, f.b. | tedbirin_effekti qeyri-neft artımı, f.b. |
|---|---|---:|---:|---:|---:|---:|---:|
| S1 | Davamlı aşağı neft qiyməti | −0,28 | −3,59 | −1,32 | −0,47 | 0,16 | 0,34 |
| S2 | Tərəfdaş ölkələrdə resessiya | −0,03 | −0,14 | −0,41 | 0,00 | 0,00 | 0,00 |
| S3 | Məzənnəyə təzyiq və ehtiyatların azalması | −0,28 | 0,97 | −1,53 | −0,47 | 0,18 | 0,35 |
| S4 | Regional münaqişənin eskalasiyası | −0,04 | −0,14 | −0,96 | 0,00 | 0,00 | 0,00 |
| S5 | Güclü seysmik hadisə | −0,46 | 0,11 | −0,73 | 0,00 | 0,00 | 0,00 |
| S6 | Enerji keçidi — tələbin struktur azalması | −0,04 | −0,47 | −0,18 | 0,00 | 0,00 | 0,01 |
| S7 | Şiddətli quraqlıq | 0,00 | 0,00 | −0,16 | 0,00 | 0,00 | 0,00 |
| S8 | Cari neft şokunun geri dönməsi | −0,10 | −1,17 | −0,46 | 0,00 | 0,01 | 0,01 |
<!-- /AUTO:fr3_stress -->

**Tarixi analoqlar.** Ötürmə mexanizmi hər tarixi ilin faktiki amil dəyişmələri ilə işə salınır və qeyri-neft
artımının əvvəlki beş ilin ortasından faktiki sapması ilə müqayisə olunur.

<!-- AUTO:fr3_analogues -->
2006–2025: korrelyasiya 0,76, RMSE 3,29 f.b. (sıfır sapma etalonu 4,60 f.b.).

| il | faktiki_sapma | proqnoz_sapma | fiskal_reaksiya | neft_birbasa | terefdas | devalvasiya | tolerans_odenilir | kalibrləməyə_daxil |
|---|---:|---:|---:|---:|---:|---:|---|---|
| 2009 | −8,52 | −1,96 | −0,08 | −0,87 | −0,97 | 0,00 | False | False |
| 2015 | −7,70 | −3,08 | −1,70 | −1,16 | 0,02 | −0,25 | False | True |
| 2016 | −11,94 | −4,85 | −1,46 | −0,22 | 0,04 | −3,45 | False | True |
| 2020 | −3,98 | −2,57 | −0,84 | −0,55 | −1,10 | 0,00 | True | False |
<!-- /AUTO:fr3_analogues -->

## 6. FR4 və NFR3 — qərar dəstək paneli və rol əsaslı hesabatlar

| Çıxış | Rəhbərlik | Analitik |
|---|---|---|
| HTML panel | `site/index.html` — əsas göstəricilər, xəbərdarlıqlar, risk xəritəsi, ilk 10 risk, GaR yelpiyi, Brent, stress ssenariləri, tədbirlərin icrası | `site/analitik.html` — əlavə olaraq tam reyestr, töhfələr, kvantillər, göstərici bazası, kanallar, təhlükələr, xronologiya, ssenari yolları, alətlər, tədbirlər reyestri, qalıq risk, geriyə sınaq, məlumat axınları |
| PDF | `reports/risk_hesabati_rehberlik.pdf` | `reports/risk_hesabati_analitik.pdf` |
| Excel | 5 vərəq | 19 vərəq |

Bölmələrin rollara bölgüsü `input/rollar.csv`-də verilir və kod dəyişmədən dəyişdirilə bilir.
`output/risk_api.json` MİİS dashboard-u üçün TT §3.5 məlumat modelindədir: Indicator Time Series, Scenario,
Forecast Result, Risk Register, Policy Measure.

## 7. NFR1 — dəqiqlik və etibarlılıq

Üç tələbin hər biri ayrıca test ailəsi ilə yerinə yetirilir:

1. **Sadə etalona qarşı dəqiqlik (D):** makro ansambl RW-yə qarşı; GaR medianı tarixi ortaya qarşı; ötürmə
   mexanizmi sıfır sapma etalonuna qarşı; Brent sıxlığı normal etalona qarşı (CRPS).
2. **Yalnız proqnoz anında mövcud məlumat:** bazar sıraları (Brent, VIX, GPR, USGS, ERA5) yenidən baxılmır və
   genişlənən pəncərəli sınaqlar onlar üzrə real vaxt sınağıdır. Milli hesablar üzrə sınaqlar psevdo-real
   vaxtdır və belə işarələnir. Hər yeniləmədə giriş vintajları (`data/vintages/`) və risk paylanması
   (`output/forecast_archive/`) dondurulur; hədəf ilinin ilk buraxılışı açıqlandıqda arxiv proqnozu R1 testi ilə
   qiymətləndirilir.
3. **Paylanmanın statistik testləri (P, E):** PIT bərabərliyi (KS), Berkowitz LR, Kupiec və Christoffersen,
   80% (75–85%) və 90% (86–94%) əhatə tolerantlığı, AUROC ≥ 0,70 və səs-küy/siqnal nisbəti.

**Rüblük dövr və qərar qaydası.** Hər rübün ilk işə salınmasında sınaq avtomatik aparılır və
`output/NFR1_backtest_register.csv`-ə rüb bloku yazılır. 80% əhatə tolerans xaricindədirsə, simulyasiyanın
müvafiq qalıq σ-sı (və ya Brent innovasiyaları) empirik |z|-in 80-ci faizinin nominala nisbəti ilə
miqyaslanır (`output/NFR1_calibration.csv`, 0,5–2,0 aralığı). Keçməyən model qərar üçün istifadə edilmir.

<!-- AUTO:nfr1 -->
Rüb 2026Q4: 22/39 test keçdi.

| test_id | model | hedef | n | metrik | deyer | hedd | netice |
|---|---|---|---|---|---:|---|---|
| D1 | makro §15.5.1 ansamblı | nonoil_realg | 9 | bacarıq RW-yə qarşı (1 − RMSE/RMSE_RW) | 0,457 | > 0 | keçdi |
| D1 | makro §15.5.1 ansamblı | cpi_infl | 14 | bacarıq RW-yə qarşı (1 − RMSE/RMSE_RW) | 0,194 | > 0 | keçdi |
| D1 | makro §15.5.1 ansamblı | brent_usd | 17 | bacarıq RW-yə qarşı (1 − RMSE/RMSE_RW) | 0,215 | > 0 | keçdi |
| D1 | makro §15.5.1 ansamblı | current_account | 7 | bacarıq RW-yə qarşı (1 − RMSE/RMSE_RW) | 0,473 | > 0 | keçdi |
| D2 | GaR kvantil reqressiyası — müstəqil yoxlama (median) | nonoil_g | 13 | RMSE / RMSE(tarixi orta) | 1,042 | < 1 | keçmədi |
| D3 | GaR kvantil reqressiyası — müstəqil yoxlama (P10) | nonoil_g | 13 | pinball(0,10) / etalon | 1,320 | < 1 | keçmədi |
| D4 | ötürmə mühərriki (tarixi analoqlar) | nonoil_g sapması | 20 | RMSE / RMSE(sıfır sapma etalonu) | 0,652 | < 1 | keçdi |
| D5 | ötürmə mühərriki (adlı epizodlar, kalibrləmədən kənar) | nonoil_g sapması | 2 | tolerans (eyni işarə, |xəta| ≤ 3 f.b.) ödənilən pay | 0,500 | ≥ 0,5 | keçdi |
| D6 | Brent sıxlığı (CRPS) | brent 12 ay | 30 | CRPS / CRPS(normal etalon) | 1,006 | < 1 | keçmədi |
| P1 | makro §15.5.1 yelpiyi | nonoil_realg | 9 | 80% interval əhatəsi | 1,000 | [0.75; 0.85] | keçmədi |
| P2 | makro §15.5.1 yelpiyi | nonoil_realg | 9 | PIT bərabərliyi (KS) p | 0,814 | > 0.05 | keçdi |
| P3 | makro §15.5.1 yelpiyi | nonoil_realg | 9 | Kupiec (P10 pozuntuları) p | 0,169 | > 0.05 | keçdi |
| P1 | makro §15.5.1 yelpiyi | cpi_infl | 14 | 80% interval əhatəsi | 0,786 | [0.75; 0.85] | keçdi |
| P2 | makro §15.5.1 yelpiyi | cpi_infl | 14 | PIT bərabərliyi (KS) p | 0,921 | > 0.05 | keçdi |
| P3 | makro §15.5.1 yelpiyi | cpi_infl | 14 | Kupiec (P10 pozuntuları) p | 0,709 | > 0.05 | keçdi |
| P1 | makro §15.5.1 yelpiyi | brent_usd | 17 | 80% interval əhatəsi | 0,941 | [0.75; 0.85] | keçmədi |
| P2 | makro §15.5.1 yelpiyi | brent_usd | 17 | PIT bərabərliyi (KS) p | 0,584 | > 0.05 | keçdi |
| P3 | makro §15.5.1 yelpiyi | brent_usd | 17 | Kupiec (P10 pozuntuları) p | 0,543 | > 0.05 | keçdi |
| P1 | makro §15.5.1 yelpiyi | current_account | 7 | 80% interval əhatəsi | 1,000 | [0.75; 0.85] | keçmədi |
| P2 | makro §15.5.1 yelpiyi | current_account | 7 | PIT bərabərliyi (KS) p | 0,533 | > 0.05 | keçdi |
| P3 | makro §15.5.1 yelpiyi | current_account | 7 | Kupiec (P10 pozuntuları) p | 0,225 | > 0.05 | keçdi |
| P4 | Brent sıxlığı (R01) | brent 12 ay | 30 | 80% interval əhatəsi | 0,733 | [0.75; 0.85] | keçmədi |
| P5 | Brent sıxlığı (R01) | brent 12 ay | 30 | 90% interval əhatəsi | 0,800 | [0.86; 0.94] | keçmədi |
| P6 | Brent sıxlığı (R01) | brent 12 ay | 30 | PIT bərabərliyi (KS) p | 0,863 | > 0.05 | keçdi |
| P7 | Brent sıxlığı (R01) | brent 12 ay | 30 | Berkowitz LR p | 0,159 | > 0.05 | keçdi |
| P8 | Brent sıxlığı (R01) | brent 12 ay | 30 | Kupiec (P5 pozuntuları) p | 0,080 | > 0.05 | keçdi |
| P9 | Brent sıxlığı (R01) | brent 12 ay | 30 | Kupiec (P10 pozuntuları) p | 0,262 | > 0.05 | keçdi |
| P10 | Brent sıxlığı (R01) | brent 12 ay | 30 | Christoffersen şərti əhatə p | 0,211 | > 0.05 | keçdi |
| P11 | GaR kvantil reqressiyası — müstəqil yoxlama (R13) | nonoil_g | 13 | 80% interval (P10–P90) əhatəsi | 0,538 | [0.75; 0.85] | keçmədi |
| P12 | GaR kvantil reqressiyası — müstəqil yoxlama (R13) | nonoil_g | 13 | PIT bərabərliyi (KS) p | 0,010 | > 0.05 | keçmədi |
| P13 | GaR kvantil reqressiyası — müstəqil yoxlama (R13) | nonoil_g | 13 | Berkowitz LR p | 0,000 | > 0.05 | keçmədi |
| P14 | GaR kvantil reqressiyası — müstəqil yoxlama (R13) | nonoil_g | 13 | Kupiec (P10 pozuntuları) p | 0,001 | > 0.05 | keçmədi |
| E1 | EWS siqnal yanaşması: gələn il qeyri-neft artımı < hədd (R13) | nonoil_g | 14 | AUROC (nümunədən kənar) | 0,879 | ≥ 0.70 | keçdi |
| E1b | EWS logit: Brent ≥30% enişi 12 ayda (R01) — mənfi nəticə | brent | 309 | AUROC (nümunədən kənar) | 0,291 | ≥ 0.70 | keçmədi |
| E2 | GaR kvantil reqressiyası — müstəqil yoxlama: P(qeyri-neft artımı < 2%) (R13) | nonoil_g | 13 | AUROC (nümunədən kənar) | 0,367 | ≥ 0.70 | keçmədi |
| E3 | R06 keçid ehtimalı | regional GPR ≥ P90 | 30 | Brier / Brier(klimatologiya) | 0,895 | < 1 | keçdi |
| E4 | Brent sıxlığı: P(12 ayda ≥30% eniş) | brent | 30 | Brier / Brier(klimatologiya) | 1,075 | < 1 | keçmədi |
| R1 | arxivləşdirilmiş real vaxt risk proqnozları (RU paylanması) | nonoil_g; cpi | 0 | 80% interval əhatəsi (PIT ∈ [0,1; 0,9]) | — | [0.75; 0.85], n ≥ 5 | yoxlanıla bilmir (n=0) |
| P15 | FR1 büdcə balansı yelpiyi (RU fiskal paylanmasının eni) | balance_pct | 14 | RW xətalarının FR1 80% intervalına düşmə payı | 1,000 | [0.75; 0.85] | keçmədi |

Kalibrləmə qərarları:

| hedef | miqyas | ehate80 | n | qerar |
|---|---:|---:|---|---|
| nonoil | 0,66 | 1,00 | 9 | qalıq σ 0.66 dəfə miqyaslanır (əhatə 1.00 tolerans xaricindədir) |
| cpi | 1,00 | 0,79 | 14 | dəyişiklik yoxdur — əhatə tolerans daxilindədir |
| brent | 1,23 | 0,73 | 30 | Brent innovasiyaları 1.23 dəfə miqyaslanır (əhatə 0.73 tolerans xaricindədir) |
| fis | 0,29 | 1,00 | 14 | büdcə qalıq σ 0.29 dəfə miqyaslanır (FR1 σ 3.49 f.b. ≫ RW xətası 1.00 f.b.; əhatə 1.00) |
<!-- /AUTO:nfr1 -->

**Erkən xəbərdarlıq.** Neft qiymətinin 12 ayda ≥ 30% enişi bazar siqnalları ilə proqnozlaşdırılmır (E1b, mənfi
nəticə; neft qiyməti martinqala yaxındır). Daxili ləngimə üçün siqnal yanaşması (E1) — bu il Brent-in enməsi və
dövlət investisiyasının azalması, istiqaməti əvvəlcədən müəyyən edilmiş, çəkisi qiymətləndirilməyən kompozit —
AUROC həddini keçir; hadisə sayı azdır və nəticə ehtiyatla şərh edilir. Yanlış həyəcan ilə buraxılmış hadisə
arasındakı balans Nazirliyin siyasət seçimidir və həddin dəqiqləşdirilməsi üçün Nazirlikdən tələb olunur.

## 8. NFR2 — dinamik vəziyyətlərə uyğunlaşma

`update.py` hər dövrdə canlı axınları yükləyir, bütün girişlərin barmaq izini (axın vintajları, makro və mikro
çıxış faylları, `input/` reyestrləri) əvvəlki vəziyyətlə müqayisə edir, dəyişiklik varsa bütün boru xəttini
işə salır və `output/NFR2_update_log.csv`-ə dəyişikliyin ilk görüldüyü və skorların yenidən yazıldığı vaxtı,
gecikməni saatla yazır. Cədvəl `scheduler/`-dədir (macOS launchd, Linux cron, Windows Task Scheduler): gündəlik
07:00 tam dövr və 30 dəqiqədən bir yerli giriş yoxlaması. Tam dövr ≈ 20 saniyə çəkir.

<!-- AUTO:nfr2 -->
| feed | vintage | last_obs | age_days | n_obs |
|---|---|---|---:|---:|
| brent | 2026-10-06 | 2026-09-29 | 7 | 9 097 |
| vix | 2026-10-06 | 2026-10-02 | 4 | 9 287 |
| ust10 | 2026-10-06 | 2026-10-02 | 4 | 16 174 |
| fedfunds | 2026-10-06 | 2026-09-01 | 35 | 867 |
| eurusd | 2026-10-06 | 2026-10-02 | 4 | 6 960 |
| gpr | 2026-10-06 | 2026-09-01 | 35 | 3 507 |
| epu | 2026-10-06 | 2026-07-01 | 97 | 355 |
| usgs | 2026-10-06 | 2026-10-01 | 5 | 251 |
| era5 | 2026-10-06 | 2026-09-01 | 35 | 3 204 |
| cbar_fx | 2026-10-06 | 2026-10-06 | 0 | 14 700 |
| cbar_rate | 2026-10-06 | 2026-09-24 | 12 | 215 |
| dsk_macro | 2026-10-06 | 2026-08-01 | 66 | 354 |
| dsk_cpi | 2026-10-06 | 2026-08-01 | 66 | 7 |
| dsk_tables | 2026-10-06 | 2026-04-01 | 188 | 412 |
| minfin | 2026-10-06 | 2026-03-01 | 219 | 5 |
| sofaz | 2026-10-06 | 2026-06-30 | 98 | 15 |
| bfb | 2026-10-06 | 2026-10-01 | 5 | 60 |
| azeri_light | 2026-10-06 | 2026-09-29 | 7 | 2 981 |
<!-- /AUTO:nfr2 -->

## 9. Məhdudiyyətlər və məlumat sorğuları

- Bank sektoru göstəriciləri (problemli kreditlər, kapital adekvatlığı) — Mərkəzi Bankdan sorğu; R04 o vaxta
  qədər ekspert örtüyüdür.
- Hidroloji sıralar və Xəzərin səviyyəsi — Ekologiya və Təbii Sərvətlər Nazirliyindən sorğu; R10 ekspert örtüyüdür.
- Fəlakət zərərləri — Fövqəladə Hallar Nazirliyindən sorğu; zəlzələ zərər parametrləri kalibrləmə fərziyyəsidir.
- ARDNF aktivləri — bufer adekvatlığı (T02) üçün.
- Tərəfdaş ölkələr üzrə ayrı-ayrı ÜDM sıraları — makro modeldə yalnız aqreqat `partner_gdp_realg` var.
- Milli hesabların real vaxt vintajları mövcud deyil; arxiv 2026-10-02-dən yığılır.
- Makro modelin qeyri-neft və cari hesab yelpikləri nümunədən-kənar xətalara nisbətən genişdir (bölmə 7);
  risk bölməsi bu eni kalibrləmə qaydası ilə düzəldir və bu nəticəni makro komandaya ötürür.

## 10. Nazirliyin qərar verməli olduğu parametrlər

1. Risk iştahı: ehtimal və təsir pillələrinin hədləri, prioritet hədləri (`input/hedler.csv`).
2. Erkən xəbərdarlıq sistemində yanlış həyəcan tolerantlığı.
3. Ekspert örtüklərinin (R04, R10, R14) təsdiqi və ya əvəzlənməsi.
4. Tədbirlər reyestrində məsul qurumlar, müddətlər və statuslar — hazırkı dəyərlər təklifdir.

## 11. İşə salma

```bash
pip install -r requirements.txt
python3 run_all.py --fetch          # bütün canlı axınlar (qlobal + AZ + bazar) + tam boru xətti
python3 run_all.py                  # saxlanılmış axınlarla (RISK_NO_NETWORK=1 — tam oflayn)
python3 run_all.py --daily          # sürətli gündəlik dövr: axınlar → yuxarı axın → konsensus → monitor (D1–D7)
python3 update.py                   # NFR2 dövrü (cədvəldən çağırılır)
python3 -m unittest discover -s tests -v
```

Yuxarı axın qovluqları `MIIS_MACRO_DIR` və `MIIS_MICRO_DIR` mühit dəyişənləri ilə dəyişdirilə bilir.

## 12. v2 (2026-10-06): inteqrasiya və nüvə simulyasiyasının düzəlişləri

**Boru xətti (DAG).** `run_all.py`: A məlumat (manifest → [`--fetch`: bütün axınlar] → D1 yuxarı axın anbarı →
D3 konsensus → D2/D4 AZ axınları → D5–D7 gündəlik monitor) → B FR1 amillər → C CAEM (C1–C6) → D NFR1 →
E FR2 iki baxışda simulyasiya və skorlama → F FR3 (+ stress işarə yoxlaması) → G VaR/DSA/CaR (V*, K*) →
H miqyaslanma/optimallaşdırma (modul varsa) → I xəbərdarlıqlar və arxiv → J hesabatlar. Hər mərhələnin vaxtı və
statusu `output/_run_summary_v2.json`-dadır; `--daily` və `update.py --daily` eyni A mərhələlərini işlədir.

**Risk reyestri v2.** R17 «Qeyri-neft idxal qiymətlərinin kəskin artımı» və R18 «Dünya ərzaq qiymətlərinin şoku»
(CAEM `Risk-import price` / `Risk-food price` kateqoriyaları, C3), R19 «Proqnoz qeyri-müəyyənliyi / model riski»
(D3 konsensus: bazanın digər bölmələrdən ≥ 0,5 f.b. əlverişli tərəfdə olduğu mənbələrin payı və median fərq).
Hər riskin `caem_kateqoriya` sütunu var. Yeni xəbərdarlıq növləri: «gündəlik monitor» (D5 «xəbərdarlıq»
sətirləri), «məlumat köhnəlib»/«axın xətası» (D2 təzəliyi), «model riski», canlı baxışa əsaslanan «baza köhnəlib».

**Düzəlişlər və sübut** (2027, eyni giriş məlumatı ilə v1 kodu → v2 kodu):

| Məsələ | v1 | v2 | Səbəb və sübut |
|---|---|---|---|
| (a) Büdcə balansının medianı | −2,4% ÜDM (baza +0,46; reaksiya kanalı −3,1 f.b.) | baza baxışı +0,46 (= baza); canlı +0,60 | reaksiya FR1-in deficitlə maliyyələşən «+1 mlrd investisiya» multiplikatoru ilə büdcəyə yazılırdı və canlı Brent fərqi (84 vs 69) daimi səviyyə sürüşməsi yaradırdı |
| (b) S1 (Brent 45) büdcəyə təsiri | +4,2 f.b. (dərc olunmuş v1: +0,45) | −0,37 f.b.; artım −1,23; İQİ −0,37 | investisiya kəsintisi «qənaət» kimi sayılırdı; FR1: Brent +10 → balans +198…+77 mln AZN; reduksiya forması Δbalans ← Δln Brent = +1,57 (st.x. 0,79; n = 15) — müsbət işarə |
| (c) Mərkəz | median 7,25% (baza 5,43) | baza baxışı 5,43; canlı 6,21 | iki baxış ayrıca etiketlənir |
| (d) Qeyri-neft yelpiyi P5–P95 | −0,18…13,02 (σ ≈ 4,0) | −0,22…10,08 (σ 3,20) | makro yelpik σ 4,85, NFR1 P1 əhatəsi 1,00 (n = 9), RMSE/σ = 0,60 → əmsal 0,66; FR1 mikro yelpiyi (kalibrlənməmiş) −0,35…13,54 |
| (d) Büdcə yelpiyi P5–P95 | −8,3…3,8% ÜDM | −1,03…1,92 | FR1 yelpiyi σ 3,49 f.b. ≫ 2 illik RW xətası 1,00 f.b. (n = 14; P15) → əmsal 0,29 |
| (e) R1 (arxiv proqnozları) | «keçdi», n = 0 | «yoxlanıla bilmir (n=0)» | n = 0 heç vaxt keçid sayılmır; hər test n ilə |
| (f) Borc anlayışı | FR1 `debt_azn` 38 451 (2025) | FR1 v2.3.2: 25 987,5 (MN anlayışı) | DSA başlanğıc qalığı MN bülletenidir (23 830,6 mln AZN, 2026-07; zəmanətlər «şərti öhdəliklər» variantında) — dəyişiklik tələb olunmadı |

<!-- AUTO:v2_views -->
Qiymətləndirmə ili 2027; Brent mərkəzi: baza 69,0 USD, canlı 83,6 USD.

| Baxış | Göstərici | Baza | P5 | P50 | Orta | P95 | Hədəf σ | Ümumi σ |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| baza mərkəzli | Qeyri-neft artımı, % | 5,43 | 0,11 | 5,43 | 5,33 | 10,36 | 3,23 | 3,23 |
| baza mərkəzli | İnflyasiya, % | 5,74 | 1,64 | 5,74 | 6,47 | 13,71 | 4,65 | 4,65 |
| baza mərkəzli | Büdcə balansı, % ÜDM | 0,32 | −1,33 | 0,32 | 0,32 | 1,99 | 1,06 | 1,06 |
| canlı | Qeyri-neft artımı, % | 5,43 | 0,93 | 6,20 | 6,14 | 11,23 | 3,23 | 3,23 |
| canlı | İnflyasiya, % | 5,74 | 2,11 | 6,40 | 7,09 | 14,47 | 4,65 | 4,65 |
| canlı | Büdcə balansı, % ÜDM | 0,32 | −1,23 | 0,43 | 0,43 | 2,10 | 1,06 | 1,06 |
<!-- /AUTO:v2_views -->

Qeyd: canlı baxışın Brent mərkəzi (tərs-MSE birləşməsi) D6 monitorunun şərti ssenarisindən (spot səviyyəsində
saxlanılır) aşağıdır; ötürmə eynidir (FR1 multiplikatorları), fərq yalnız Brent fərqinin ölçüsündədir.

## 13. v2.1 (2026-10-06): nüvə ötürməsinin audit düzəlişləri

Müstəqil auditin tapıntıları (C1–C3, M1–M3, M6 və kiçik qeydlər) üzrə dəyişikliklər. Hər rəqəm `output/` fayllarından
təkrar hesablana bilər; əvvəlki/sonrakı müqayisə `FR1_fx_transmission.csv`, `NFR1_calibration_shrinkage.csv`,
`FR2_model_risk.csv`, `FR2_threshold_sensitivity.csv` cədvəllərindədir.

**13.1 Vahid məzənnə modulu (`riskunit/fx.py`, C1).** Simulyasiya, miqyaslanma (S-şəbəkə), gündəlik monitor (D6) və
stress S3 eyni modulu çağırır. (i) İQİ: AZN ilə idxal qiymətləri inflyasiyasının ötürməsi, cari il + 1 il gecikmə
(asılı dəyişənin gecikməsi yoxdur; HAC, 2001–2025, n = 25): b0 = 0,176, b1 = 0,084 (cəm 0,26, se 0,037). Cəmi
2015–17 epizoduna kalibrlənir: 2015–18 artıq inflyasiya (2012–14 ortasına nisbətən) 25,1 f.b., USD idxal qiyməti hissəsi
çıxıldıqda 23,7 f.b. / 78,6 log bənd = **0,30 / log bənd**; hadisə ilinin payı 68% (reqressiyadan; epizodun özü 58%).
Qeyri-müəyyənlik aralığı 0,22–0,37; Monte Karloda N(0,30; 0,037). (ii) Qeyri-neft: 2015–16 analoqu səviyyə ilə —
simmetrik etalon (2010–14 və 2017–19 ortalarının ortası, 5,9%) üzrə məcmu çatışmazlıqdan FR1 neft (Brent addım cavabı) və
dövlət investisiyası kanalları çıxılır: −8,6% / 0,71 log vahid = **−12% / log vahid** (aralıq −20…−4: yalnız əvvəlki /
yalnız sonrakı etalon; Monte Karloda üçbucaq paylanma); itkinin 7%-i hadisə ilində, qalanı növbəti ildə. (iii) Borc:
xarici borcun payı 33% (MN bülleteni 2026-07), borc/ÜDM 18,2% → Δ(borc/ÜDM) = 0,33·18,2·(e^x − 1). **Qatlama:**
MikroUnit zənciri `fx` şokunda İQİ-ni (yeni G4: AZN idxal qiymətləri), deflyatorları və neft gəlirlərini artıq dəyişir;
zənciri işlədən istehlakçılar yalnız *əlavə qatı* = kalibrlənmiş cəm − zəncirin öz cavabı (zəncirin addım cavabının
konvolyusiyası, MikroUnit mühərrik barmaq izi dəyişəndə yenidən hesablanır) əlavə edir; FR1-ə idxal qiyməti kanalı
əlavə olunduqca qat avtomatik kiçilir (bu gün İQİ üçün cəmi 4,60 vs zəncir 4,62 f.b. — qat yalnız vaxt bölgüsüdür).
Devalvasiya ehtimalı: ardıcıl çöküş illəri bir epizoddur (1998; 2015–16; 2020) → P = 1/3 (v2.0: 2/4); simulyasiyada
yalnız epizodun ilk ili tetikləyir.

**13.2 Şok ilinin impulsu (C2).** S-şəbəkədə hər amil yalnız şok ilində (qiymətləndirmə ili) verilir, 2026 = 0.
Dəyişmə ilə ölçülən amillər (Brent, qaz, məzənnə, faiz, investisiya, tərəfdaş artımı, baratlar, NPL) bir dəfəlik
innovasiyadır — səviyyə sonra yeni yolda qalır (illik dəyişmələrin avtokorrelyasiyası ≈ 0). Səviyyə/axın amilləri
(SPI, xərc şoku, ərzaq və idxal inflyasiyası, GPR sıçrayışı, S4 vektoru) yalnız şok ilinin impulsudur; İQİ tipli
şoklar FR1 tənliyinin düzəliş əmsalına bir illik impuls kimi verilir (RU qatı `RU.addf`, MikroUnit-ə heç nə yazılmır).
Keş açarı (`VERSION s-2026-10-06b` + mühərrik barmaq izi) dəyişdi — S0–S7 yenidən hesablandı.

**13.3 Cari ilin şərtləndirilməsi (C3).** Hər iki baxışda 2026 il-əvvəlindən məlumatla: Brent — müşahidə olunmuş aylar
YTD ortası ilə sabitdir (sentyabr sonu, 93,0 USD), qalan aylar baza baxışında rəsmi fərziyyə, canlı baxışda canlı
mərkəz; qeyri-neft ÜDM və İQİ — DSK Yanvar–avqust (8 ay) faktiki sabitdir, qalan 4 ay baza baxışında rəsmi illik templə,
canlı baxışda son müşahidə olunan templə; qalıq σ qalan payla (4/12) miqyaslanır. Büdcə balansı şərtləndirilmir
(IV rüb mövsümiliyi; σ-nın yarısı qalır). 2027-dən baza baxışının medianı yenə rəsmi bazadır.

**13.4 Ərzaq kanalı (M1).** Bir qiymətləndirmə: `cpi_ext` (13.1) ərzaq, idxal və məzənnə üçün ortaqdır. Ortoqonallaşdırma
sırası dəyişdi: ərzaq ⟂ Brent (qalıq = R18), idxal ⟂ (Brent, ərzaq qalığı) (qalıq = R17; ərzaq→idxal yükü γ ≈ 1,0).
USD idxal qiyməti sapmasının Brent-ə bağlı hissəsi (0,44·ΔlnBrent) R01-ə (GPR və enerji keçidi mənbəyinə görə R06/R14-ə)
aid edilir; v2.0-da bu kanal heç bir riskdə yox idi. S-şəbəkə və simulyasiya eyni əmsalı istifadə edir.

**13.5 Ötürmə dəstinin eyniliyi (M2).** R01 prosiklik investisiya reaksiyası (FR1 F4-dən artıq hissə, ARDNF transferi —
büdcəyə neytral) və Brent → idxal qiymətləri → İQİ kanalı `simulate.fiscal_reaction` / `simulate.brent_import_cpi`
funksiyalarıdır; S-şəbəkə (`ru:ovl:react:*`), D6 (`RU:` kanallı sətirlər) və API həmin funksiyaları çağırır. **Real ÜDM
Brent artanda azalır:** FR1 real ÜDM-i zəncirvari (əvvəlki ilin qiymətləri) hesablayır; baza yolunda neft-qaz hasilatı
azaldığı üçün yüksək neft qiyməti bu azalmanın çəkisini artırır. Bu, FR1 mühərrikinin xəbərdarlığıdır, düzəldilmir;
fəallıq qeyri-neft ÜDM üzrə oxunur (S1 `izah`, D6 `scenario_note`).

**13.6 Model riski R19 (M3).** İstilik xəritəsindən çıxarıldı (P_bal = I_bal = 0, prioritet "ayrıca göstərici"): v2.0-ın
P = 0,75 köhnəlmiş mənbələrin (CAEM CF04, Bottom-up, 8 vərəq — D3 "köhnəlmiş") daxil olduğu səs payı idi. İndi:
köhnəlməmiş konsensus (FR1, BVF, Nazirlik spesifikasiyası; OxLon xaric) ilə baza fərqi və bu fərq qədər sürüşdürülmüş
alternativ paylanma; əlverişsiz fərq ≥ 0,5 f.b. (`model_risk_gap_pp`) olduqda xəbərdarlıq. R11–R13 üçün hədd
həssaslığı: R12-nin ehtimalı əsasən bazanın 6% həddinə yaxınlığıdır (2027: 5,74%, 0,07σ).

**13.7 Paylanmanın quyruqları və kalibrləmə (M6).** İQİ qalığı sağa əyilmiş, aşağıdan məhdud (sürüşdürülmüş lognormal,
alt hədd 0%: 2000–2025-də deflyasiya olmayıb, minimum 1,1%, n = 26) və cəmi İQİ-yə monoton, medianı saxlayan yumşaq
alt sərhəd tətbiq olunur. NFR1 miqyas əmsalları 1-ə doğru n/(n+10) çəki ilə büzülür və eyni nümunədən kənar nöqtələrdə
80% örtük yenidən yoxlanılır; örtük tolerans xaricinə çıxarsa əmsal tolerans daxilində ən yaxın dəyərə qədər xam əmsala
qaytarılır (qeyri-neft 0,66 → 0,67; büdcə 0,29 → 0,34; Brent 1,23 → 1,17, yenidən yoxlanmış örtük 0,77).

**13.8 Kiçik qeydlər.** Zəlzələ: itki kapital bərpa olunduqca azalır (1; 0,75; 0,25), bərpa xərcləri 25/50/25% (v2.0:
50% hadisə ilində → 15% zərərdə hadisə ilində +0,83%); hadisə ili indi mənfidir; FR1 `tfp_boost` ±3 sərhədində itki və
bərpa eyni nisbətdə kəsilir. Quraqlıq → İQİ mənfi: FR1-də yalnız tələb (əmək haqqı) kanalı var; daxili təklif-qiymət
kanalı məlumatla təsdiqlənmir (`cpi_spi`: SPI əmsalı müsbət, əhəmiyyətsiz) — məhdudiyyət. GPR +1σ → qeyri-neft müsbət:
təxmin edilmiş kanallarda Brent artımı üstünlük təşkil edir (neft ixracatçısı); əlverişsiz ssenari `geo_stress`. Faiz:
uçot dərəcəsi FR1-də yalnız G1 (kredit həcmi) ilə işləyir; depozit faizi, kredit faizi və NPL G3-dən o yana real təsir
vermir (D1 istehlak tənliyində real faiz yoxdur) — NPL-in sıfır təsiri konstruksiyadır; təklif: NPL → kredit təklifi
(G1) və ya D1/D2-yə real faiz (AMB bank paneli ilə qiymətləndirilməlidir). Canlı faiz sətrində 2026 indi effektiv orta
(YTD + cari) ilə hesablanır; D6 faiz şoku FR1 multiplikatoru kimi depozit faizini 0,5× dəyişir.
