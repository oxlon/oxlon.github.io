# MİİS §15.5.3 — İqtisadi risklərin idarəedilməsi və qərar dəstək sistemi
## Metodologiya sənədi

**Alt modul:** 15.5.3 İqtisadi Risklərin İdarəedilməsi və Qərar Dəstək Sistemləri
**Sifarişçi:** Azərbaycan Respublikasının İqtisadiyyat Nazirliyi
**Əsas:** Texniki Tapşırıq, §15.5.3 (FR1–FR4, NFR1–NFR3); OxLon Metodologiya Blueprint v0.1, L4 qatı

Bu sənəddəki bütün rəqəmlər `AUTO` markerləri arasında yerləşir və `python3 run_all.py` hər dəfə işlədikdə
nəticə fayllarından yenidən yazılır. Sənəd nəticələrdən ayrıla bilməz.

<!-- AUTO:status -->
Vəziyyət tarixi **2026-10-02**, qiymətləndirmə ili **2027**, baza identifikatoru **B-7854a9d6fc**. Birgə simulyasiya: 20000 ssenari, butstrap illəri 2003–2025. Qeyri-neft artımı 2027: median 7,44%, P10 1,58%, P5 −0,24% (makro baza 5,43%). Yüksək prioritetli risklər: R12, R11, R01, R14; xəbərdarlıq sayı 8.
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
| Dövlət investisiyasının real artımı ← Brent (cari və 1 il gecikmə; tarixi prosiklik reaksiya) | dln_brent | 0,805 | 0,330 | 0,023 | 25 | 2001–2025 | güclü (p<0,05) |
| Dövlət investisiyasının real artımı ← Brent (cari və 1 il gecikmə; tarixi prosiklik reaksiya) | dln_brent_l1 | 0,609 | 0,403 | 0,145 | 25 | 2001–2025 | zəif — parametr qeyri-müəyyənliyi simulyasiyaya daxildir |
| Kənd təsərrüfatı əlavə dəyəri ← SPI (quraqlıq indeksi) | spi | 0,936 | 1,006 | 0,362 | 25 | 2001–2025 | zəif — parametr qeyri-müəyyənliyi simulyasiyaya daxildir |
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

- **Canlı mərkəzi yol.** Brent-in mərkəzi yolu makro modelin struktur yolu ilə son ayın səviyyəsinin tərs-MSE
  çəkili birləşməsidir; çəkilər makro geriyə sınaqdan götürülür. Cari il üçün il ərzində müşahidə olunmuş
  qiymət ortası birbaşa istifadə olunur.
- **Prosiklik investisiya reaksiyası.** Mikro FR1 struktur modelində dövlət investisiyası siyasət səviyyəsi kimi
  verilir; tarixi məlumat isə dövlət investisiyasının Brent-ə prosiklik reaksiyasını göstərir (cari və bir il
  gecikmə ilə paylanmış gecikmə; gecikmiş asılı dəyişən yoxdur). Bu reaksiya ayrıca kanal kimi modelləşdirilir,
  çünki onun qarşısını almaq tədbir məsələsidir (T09): prosiklik kəsinti olmadıqda R01-in aşağı quyruğu daralır.
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
4. Nüvənin öz qalıq qeyri-müəyyənliyi (t₅ paylanması) elə seçilir ki, ümumi yayılma makro modelin eyni il üçün
   yelpik eninə bərabər olsun; NFR1 kalibrləmə əmsalı bu eni düzəldir.

Hər kanal ayrıca toplanan komponentdir, ona görə dispersiya payları və aşağı quyruq (P10) töhfələri dəqiq
Eyler bölgüsüdür.

<!-- AUTO:fr2_contrib -->
| Kanal | Dispersiya payı % | P10 quyruğunda töhfə f.b. |
|---|---:|---:|
| Neft qiyməti — prosiklik investisiya reaksiyası (R01) | 52,8 | −4,15 |
| Neft qiyməti — birbaşa (R01) | 15,5 | −1,21 |
| Modelin qalıq qeyri-müəyyənliyi | 16,8 | −1,00 |
| Devalvasiya (R03) | 4,9 | −0,74 |
| Tərəfdaş tələbi (R05) | 5,4 | −0,49 |
| Geosiyasi eskalasiya (R06) | 1,7 | −0,12 |
| Zəlzələ (R08) | 0,6 | −0,06 |
| Bank sektoru (R04, ekspert) | 0,2 | −0,01 |
| Enerji keçidi (R14) | 0,0 | 0,00 |
| Quraqlıq (R09) | 0,1 | 0,00 |
| Rəqabət (R16) | 0,0 | 0,00 |
| Emal sahələri (R15) | 0,0 | 0,00 |
| Daşqın (R10, ekspert) | 0,0 | 0,00 |
| Kredit faizi (R02) | 0,0 | 0,00 |
| Pul baratları (R07) | 2,0 | 0,03 |
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
| 1 | R12 | İnflyasiyanın hədəf diapazonundan yuxarı olması | 57,0 | 0,00 | 3,67 | 0,00 | 5 | 5 | 25 | yüksək | — |
| 2 | R11 | Büdcə balansının pisləşməsi | 35,0 | 0,00 | 0,00 | 2,47 | 4 | 5 | 20 | yüksək | — |
| 3 | R01 | Neft qiymətinin kəskin enməsi | 25,9 | 3,79 | −1,07 | −0,31 | 3 | 5 | 15 | yüksək | −5,36 |
| 4 | R14 | Enerji keçidi: karbohidrogen tələbinin struktur azalması | 24,6 | 1,12 | −0,34 | −0,30 | 3 | 4 | 12 | yüksək | — |
| 5 | R13 | Qeyri-neft artımının kəskin zəifləməsi (Growth-at-Risk) | 11,4 | 2,36 | 0,00 | 0,00 | 2 | 5 | 10 | orta | — |
| 6 | R07 | Pul baratlarının kəskin azalması | 22,7 | 0,67 | 0,00 | 0,00 | 3 | 3 | 9 | orta | 0,03 |
| 7 | R03 | Manatın məzənnəsinə təzyiq və devalvasiya | 7,0 | 1,47 | 2,91 | 0,00 | 2 | 4 | 8 | orta | −0,74 |
| 8 | R05 | Tərəfdaş ölkələrdə iqtisadi tənəzzül | 14,2 | 0,70 | −0,21 | 0,01 | 2 | 3 | 6 | orta | −0,49 |
| 9 | R04 | Bank sektorunda aktiv keyfiyyətinin pisləşməsi | 10,1 | 0,36 | 0,09 | 0,04 | 2 | 3 | 6 | orta | −0,01 |
| 10 | R08 | Güclü zəlzələ | 19,9 | 0,13 | 0,00 | 0,19 | 3 | 2 | 6 | orta | −0,06 |
| 11 | R16 | Rəqabət mühitinin pisləşməsi | 45,9 | 0,09 | 0,14 | 0,00 | 4 | 1 | 4 | aşağı | 0,00 |
| 12 | R02 | Maliyyə şəraitinin sərtləşməsi (kredit faizi) | 8,9 | 0,20 | −0,06 | 0,00 | 2 | 2 | 4 | aşağı | 0,00 |
| 13 | R06 | Regional geosiyasi eskalasiya | 40,9 | −0,13 | 0,01 | 0,00 | 4 | 1 | 4 | aşağı | −0,12 |
| 14 | R15 | Emal sənayesi sahələrində maliyyə gərginliyi | 16,1 | 0,03 | 0,00 | 0,00 | 3 | 1 | 3 | aşağı | 0,00 |
| 15 | R09 | Quraqlıq | 14,8 | 0,09 | 0,00 | 0,00 | 2 | 1 | 2 | aşağı | 0,00 |
| 16 | R10 | Daşqın və Xəzər dənizinin səviyyəsinin dəyişməsi | 9,9 | 0,09 | 0,05 | 0,05 | 2 | 1 | 2 | aşağı | 0,00 |
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
| S1 | Davamlı aşağı neft qiyməti | 0,45 | −1,32 | −4,37 | −0,24 | 0,50 | 1,67 |
| S2 | Tərəfdaş ölkələrdə resessiya | 0,00 | −0,13 | −0,42 | 0,00 | 0,00 | 0,00 |
| S3 | Məzənnəyə təzyiq və ehtiyatların azalması | 0,45 | 1,81 | −5,95 | −0,24 | 0,50 | 1,67 |
| S4 | Regional münaqişənin eskalasiyası | −0,01 | −0,13 | −0,97 | 0,00 | 0,00 | 0,00 |
| S5 | Güclü seysmik hadisə | −1,50 | 0,00 | −1,05 | 0,00 | 0,00 | 0,00 |
| S6 | Enerji keçidi — tələbin struktur azalması | 0,03 | −0,11 | −0,37 | 0,00 | 0,00 | 0,00 |
| S7 | Şiddətli quraqlıq | 0,00 | 0,00 | −0,15 | 0,00 | 0,00 | 0,00 |
| S8 | Cari neft şokunun geri dönməsi | 0,23 | −0,73 | −2,41 | 0,00 | 0,01 | 0,02 |
<!-- /AUTO:fr3_stress -->

**Tarixi analoqlar.** Ötürmə mexanizmi hər tarixi ilin faktiki amil dəyişmələri ilə işə salınır və qeyri-neft
artımının əvvəlki beş ilin ortasından faktiki sapması ilə müqayisə olunur.

<!-- AUTO:fr3_analogues -->
2006–2025: korrelyasiya 0,80, RMSE 2,82 f.b. (sıfır sapma etalonu 4,60 f.b.).

| il | faktiki_sapma | proqnoz_sapma | fiskal_reaksiya | neft_birbasa | terefdas | devalvasiya | tolerans_odenilir | kalibrləməyə_daxil |
|---|---:|---:|---:|---:|---:|---:|---|---|
| 2009 | −8,52 | −2,89 | −1,16 | −0,70 | −0,99 | 0,00 | False | False |
| 2015 | −7,70 | −8,01 | −5,20 | −0,92 | 0,02 | −1,91 | True | True |
| 2016 | −11,94 | −6,07 | −3,05 | −0,17 | 0,04 | −3,13 | False | True |
| 2020 | −3,98 | −4,10 | −2,46 | −0,44 | −1,12 | 0,00 | True | False |
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
Rüb 2026Q4: 23/38 test keçdi.

| test_id | model | hedef | n | metrik | deyer | hedd | netice |
|---|---|---|---|---|---:|---|---|
| D1 | makro §15.5.1 ansamblı | nonoil_realg | 9 | bacarıq RW-yə qarşı (1 − RMSE/RMSE_RW) | 0,457 | > 0 | keçdi |
| D1 | makro §15.5.1 ansamblı | cpi_infl | 14 | bacarıq RW-yə qarşı (1 − RMSE/RMSE_RW) | 0,194 | > 0 | keçdi |
| D1 | makro §15.5.1 ansamblı | brent_usd | 17 | bacarıq RW-yə qarşı (1 − RMSE/RMSE_RW) | 0,215 | > 0 | keçdi |
| D1 | makro §15.5.1 ansamblı | current_account | 7 | bacarıq RW-yə qarşı (1 − RMSE/RMSE_RW) | 0,473 | > 0 | keçdi |
| D2 | GaR kvantil reqressiyası — müstəqil yoxlama (median) | nonoil_g | 13 | RMSE / RMSE(tarixi orta) | 1,042 | < 1 | keçmədi |
| D3 | GaR kvantil reqressiyası — müstəqil yoxlama (P10) | nonoil_g | 13 | pinball(0,10) / etalon | 1,320 | < 1 | keçmədi |
| D4 | ötürmə mühərriki (tarixi analoqlar) | nonoil_g sapması | 20 | RMSE / RMSE(sıfır sapma etalonu) | 0,614 | < 1 | keçdi |
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
| E1 | EWS siqnal yanaşması: gələn il qeyri-neft artımı < hədd (R13) | nonoil_g | 20 | AUROC (nümunədən kənar) | 0,882 | ≥ 0.70 | keçdi |
| E1b | EWS logit: Brent ≥30% enişi 12 ayda (R01) — mənfi nəticə | brent | 309 | AUROC (nümunədən kənar) | 0,291 | ≥ 0.70 | keçmədi |
| E2 | GaR kvantil reqressiyası — müstəqil yoxlama: P(qeyri-neft artımı < 2%) (R13) | nonoil_g | 13 | AUROC (nümunədən kənar) | 0,367 | ≥ 0.70 | keçmədi |
| E3 | R06 keçid ehtimalı | regional GPR ≥ P90 | 30 | Brier / Brier(klimatologiya) | 0,895 | < 1 | keçdi |
| E4 | Brent sıxlığı: P(12 ayda ≥30% eniş) | brent | 30 | Brier / Brier(klimatologiya) | 1,075 | < 1 | keçmədi |
| R1 | arxivləşdirilmiş real vaxt risk proqnozları | nonoil_g; cpi | 0 | yetişmiş proqnoz sayı | 0,000 | ≥ 0 | keçdi |

Kalibrləmə qərarları:

| hedef | miqyas | ehate80 | n | qerar |
|---|---:|---:|---|---|
| nonoil | 0,66 | 1,00 | 9 | qalıq σ 0.66 dəfə miqyaslanır (əhatə 1.00 tolerans xaricindədir) |
| cpi | 1,00 | 0,79 | 14 | dəyişiklik yoxdur — əhatə tolerans daxilindədir |
| brent | 1,23 | 0,73 | 30 | Brent innovasiyaları 1.23 dəfə miqyaslanır (əhatə 0.73 tolerans xaricindədir) |
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
| brent | 2026-10-02 | 2026-09-29 | 3 | 9 097 |
| vix | 2026-10-02 | 2026-09-30 | 2 | 9 285 |
| ust10 | 2026-10-02 | 2026-09-30 | 2 | 16 172 |
| fedfunds | 2026-10-02 | 2026-09-01 | 31 | 867 |
| eurusd | 2026-10-02 | 2026-09-25 | 7 | 6 955 |
| gpr | 2026-10-02 | 2026-09-01 | 31 | 3 507 |
| epu | 2026-10-02 | 2026-07-01 | 93 | 355 |
| usgs | 2026-10-02 | 2026-08-14 | 49 | 250 |
| era5 | 2026-10-02 | 2026-09-01 | 31 | 3 204 |
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
python3 run_all.py --fetch          # canlı axınlar + tam boru xətti (≈ 20 san)
python3 run_all.py                  # saxlanılmış axınlarla
python3 update.py                   # NFR2 dövrü (cədvəldən çağırılır)
python3 -m unittest discover -s tests -v
```

Yuxarı axın qovluqları `MIIS_MACRO_DIR` və `MIIS_MICRO_DIR` mühit dəyişənləri ilə dəyişdirilə bilir.
