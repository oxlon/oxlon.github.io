# Riskə məruz dəyər (VaR) və riskə məruz kapital (CaR) — metodologiya

MİİS §15.5.3, RiskUnit v2, istifadəçi tələbi U4 («iqtisadiyyatın ümumi risk məruz qalmasının qabaqcıl VaR və CaR
modelləri»), Metodologiya Blueprint L4 (FR2 «risk ölçüsü», FR3 «stoxastik DSA, ARDNF-in stress altında adekvatlığı,
şərti öhdəliklər»). Modullar: `riskunit/feeds_market.py`, `exposures.py`, `var.py`, `dsa.py`, `car.py`.

## 1. Əsas prinsiplər

* Risk qatı **öz mərkəzi yolunu dərc etmir**: makro baza OxLon (§15.5.1), fiskal blok və multiplikatorlar MikroUnit
  FR1 (§15.5.2), ARDNF transfert planı Nazirliyin Bottom-up «base 60» modelindən götürülür.
* Paylanmalar yalnız tarixi simulyasiya, bootstrap, kopula, EVT və Monte Karlo ilə qurulur. **GARCH, ARCH, AR/ARIMA,
  qiymətləndirilmiş dəyişkənlik dinamikası yoxdur.** Yaşa görə çəkili tarixi simulyasiyanın azalma əmsalı **sabitdir**
  (λ = 0,995 gündəlik, 0,98 aylıq; yarımömür 138 gün / 34 ay) və məlumatdan qiymətləndirilmir.
* Hər geriyə doğru sınaq müşahidə sayı (n) ilə verilir; «yoxlanıla bilməz» heç vaxt «keçdi» sayılmır.
* Hər rəqəmin mənbəyi, tarixi və statusu (`canlı`, `keş`, `fiksatura`, `törəmə`, `yuxarı axın`) `V1_exposures.csv`-də
  göstərilir; açıq olmayan rəqəmlər `V1b_data_requests.csv`-də məlumat sorğusu kimi qeyd olunur.

## 2. Məlumatların avtomatik toplanması

| Mənbə | Nə götürülür | Tezlik | Modul |
|---|---|---|---|
| ARDNF (oilfund.az) | «Son rəqəmlər» səhifəsi (cəmi aktivlər) və son rüblük investisiya nəticələri PDF-i: valyuta, aktiv sinfi, müddət qrupları, kredit reytinqi, qızıl (ton) | rüblük | exposures |
| AMB statistik bülleteni (xlsx, 68 cədvəl) | c.2.2 rəsmi ehtiyatlar; c.5.2 bank sektorunun balansı və kapitalı; c.5.6 qeyri-işlək kreditlər | aylıq | exposures |
| Maliyyə Nazirliyi, Dövlət borcu üzrə statistik bülleten (PDF) | dövlət, xarici, daxili və zəmanətli borc; valyuta və faiz tərkibi; ödəmə müddəti; avrobondlar; strateji ehtiyatlar | yarımillik | exposures |
| AMB rəsmi məzənnə XML-i | USD, EUR, GBP, RUB, TRY, CNY, JPY və qızıl (XAU) — manata qarşı, hər iş günü | gündəlik | feeds_market |
| FRED | Brent, Henry Hub, EUR/GBP/CNY/JPY məzənnələri, geniş dollar indeksi, UST 2/5/10 il, S&P 500, EM spredləri, VIX, OECD səhm indeksi, RUB/TRY aylıq | gündəlik/aylıq | feeds_market |
| Dünya Bankı «Pink Sheet» | aylıq qızıl, Brent, Avropa qazı | aylıq | feeds_market |
| ECB | TRY/EUR (TRY/USD gündəlik tarixçəsi üçün) | gündəlik | feeds_market |
| MikroUnit FR1, OxLon, Nazirlik «base 60» | büdcənin neft gəlirləri, ixrac, fiskal baza, ARDNF transfert planı, cari hesabın Brent həssaslığı | vintaj dəyişdikdə | exposures, dsa, car |

Qaydalar (v2 müqaviləsi): sorğu vaxtı ≤ 20 s, saniyədə ≤ 1 sorğu, xam cavab `data/vintages/<mənbə>/<tarix>/` altında
saxlanılır, uğursuz sorğuda son yaxşı keş istifadə olunur, hər cəhd `output/D2_feed_status.csv`-də qeyd olunur,
`RISK_NO_NETWORK=1` bütün sorğuları keşə yönəldir. PDF mətni `pdftotext` (poppler) ilə çıxarılır; maket dəyişərsə
əvvəlki uğurlu təhlil, o da yoxdursa sənədləşdirilmiş fiksatura (30.06.2026 / 01.07.2026 nəşrləri) istifadə olunur və
status «fiksatura» olur. AMB XML-i hər işə salınmada çatışmayan iş günlərini tamamlayır (ilk dəfə 3 il geriyə).

## 3. Portfellər və risk amilləri

**ARDNF portfeli** (mln USD). Aktiv sinifləri: sabit gəlirli alətlər UST açar faiz nöqtələrinə (2, 5, 10 il) bağlanır —
açar müddətlər ARDNF-in müddət qruplarından (0–1, 1–3, 3–5, 5+ il) fərz olunan qrup müddətləri 0,5 / 2 / 4 / 7,5 il ilə
hesablanır (modifikasiya olunmuş müddət ≈ 3,9 il; ARDNF müddəti açıqlamır — DR03). Səhmlər: S&P 500 (gündəlik) və
OECD ABŞ səhm indeksi (aylıq) qlobal səhm proksisi kimi. Qızıl: AMB XAU/USD (gündəlik; AMB məzənnəsi d−1 günü
müəyyən olunduğu üçün bir gün əvvələ çəkilir) və Pink Sheet (aylıq). Daşınmaz əmlak: səhm betası 0,5 (FƏRZİYYƏ).
**Kredit spredi (v2.4):** ARDNF sabit gəlirli hissəsinin A + BBB + NIG payı (≈ 37,6%, V1 reytinq bölgüsü) × modifikasiya
olunmuş müddət × Δ(Moody's Baa − UST 10 il) — FRED `BAA10Y`, 1986-dan gündəlik (ICE BofA EM OAS FRED-də yalnız son 3 ildir,
uzun pəncərə üçün yararsızdır; o, V2-də məlumat üçün qalır). V2-də sıra yoxdursa amil avtomatik düşür.
Valyuta tərcüməsi: EUR, GBP, CNY, JPY və «digər» (geniş dollar indeksi) payları USD-yə qarşı. Valyuta × yerli gəlir
çarpaz həddi nəzərə alınmır (ikinci dərəcəli).

**Suveren xalis valyuta mövqeyi** = ARDNF + AMB ehtiyatları − xarici dövlət borcu − xarici dövlət zəmanətli borc.
Öhdəliklər valyuta tərkibinə görə (XBH səbəti: USD 43,38%, EUR 29,31%, CNY 12,28%, JPY 7,59%, GBP 7,44%) eyni
amillərə bağlanır. AMB ehtiyatlarının tərkibi açıq deyil, 100% USD fərz edilir (DR04). Manat USD-yə bağlı olduğundan
2017-dən sonrakı gündəlik tarixçədə USD/AZN dəyişməsi yoxdur; **devalvasiya riski VaR-da görünmür** və CaR/DSA-da
RU birgə simulyasiyasının şərti devalvasiya hadisəsi ilə modelləşdirilir.

**Büdcənin neft gəlirləri (risk altında)** = FR1 bazası + k·(Brent − Brent_baza), k = FR1 «Brent +10 USD»
multiplikatorunun ümumi gəlirlərə təsiri (mln AZN / USD), × həcm şoku (OxLon ±5% hasilat diapazonu 80% interval kimi)
× (1 + 0,25·devalvasiya). Baza ili = qiymətləndirmə ili. VaR = FR1 bazası − kvantil (büdcə planına nisbətən çatışmazlıq).
**Vahid lövbər (v2.4, audit M7):** bütün metodlar FR1 baza gəliri R0 və baza Brent-dən (qiymətləndirmə ili, ≈ 69 USD)
ölçülür; tarixi metodlar 12 aylıq log-dəyişmələri baza Brent-ə tətbiq edir (əvvəl cari spota — 114 USD — tətbiq olunurdu və
simulyasiya 4 401 / tarixi −13 mln AZN kimi uyğunsuz nəticə verirdi; indi 5 584 / 5 061). İxrac qiyməti = Brent + FR1 spredi.

## 4. VaR və ES metodları

P&L = cari ekspozisiya × tarixi (və ya simulyasiya olunmuş) amil dəyişməsi (hipotetik P&L): log-gəlirli amillər üçün
E·(e^r − 1), faiz amilləri üçün −E·D·Δy/100.

* **(a) Tarixi simulyasiya (HS).** VaR_q = −Q_{1−q}(P&L); ES_q = −E[P&L | P&L ≤ −VaR_q].
* **(b) Yaşa görə çəkili HS** (Boudoukh–Richardson–Whitelaw, 1998): w_i ∝ λ^{n−i}, λ sabit (yuxarıda).
* **(c) Monte Karlo, t-kopula.** Korrelyasiya Kendall τ-dan: R = sin(πτ/2) (müsbət müəyyənliyə gətirilir); ν
  psevdo-müşahidələr üzrə profil maksimum həqiqətəoxşarlıq ilə {2,…,50} şəbəkəsindən seçilir; marjinallar empirik
  kvantil funksiyası (hamarlanmış bootstrap). N = 50 000. 1 illik horizont = 12 müstəqil aylıq çəkilişin cəmi
  (momentum/orta qayıdış nəzərə alınmır — qeyd olunur).
* **(d) EVT, POT.** İtkilərin 90-cı faizindən yuxarı həddə GPD (ξ, β) maksimum həqiqətəoxşarlıq ilə;
  VaR = u + β/ξ·[(n/N_u·(1−q))^{−ξ} − 1], ES = (VaR + β − ξu)/(1 − ξ). **1 illik horizontda EVT ETİBARSIZDIR**
  (üst-üstə düşən 12 aylıq pəncərələr: n_eff ≈ n/12, n_u = 24 asılı müşahidə, ξ ≈ −0,5 qeyri-real yuxarı sərhəd);
  V3-də `etibarli = False` ilə yalnız müqayisə üçün qalır, 1 il üçün əsas metod — MK t-kopula (müstəqil aylıq çəkilişlər).
* **(e) Kornish–Fişer.** z_cf = z + (z²−1)S/6 + (z³−3z)K/24 − (2z³−5z)S²/36; ES — KF kvantil funksiyasının
  quyruq üzrə ədədi inteqralı.

Horizontlar: **1 gün** (gündəlik amillər, son 750 iş günü — qızılın gündəlik tarixçəsi ilə məhdud), **1 ay** (aylıq
orta səviyyələr 2006-dan; aylıq ortaların dəyişməsi ay sonu dəyişməsinin dispersiyasının ≈ 2/3-ü olduğundan
Working düzəlişi √1,5 tətbiq edilir — TƏXMİNİ, qeyd olunur), **1 il** (üst-üstə düşən 12 aylıq dəyişmələr; effektiv
müstəqil müşahidə sayı ≈ n/12) və t-kopula simulyasiyası. **Kök-zaman** (1 günlük HS × √21, × √252) yalnız
müqayisə sətri kimi verilir və «TƏXMİNİ» işarəsi daşıyır.

## 5. Komponent və marjinal VaR (Euler)

Simulyasiya ssenarilərində: komponent VaR_i = −E[P&L_i | P&L ≈ −VaR] (VaR kvantili ətrafında ən yaxın
max(25; 0,25%·N) ssenari), cəmin VaR-a bərabər olması üçün miqyaslanır (xam dəyər də verilir); komponent ES_i =
−E[P&L_i | P&L ≤ −VaR] — dəqiq additivdir. Marjinal VaR = komponent / ekspozisiya (1 mln USD əlavə məruz qalmanın
VaR-a təsiri). Nəticələr amillər və aktiv sinifləri (sabit gəlirli, səhm, qızıl, daşınmaz əmlak, valyuta) üzrə.

## 6. Geriyə doğru sınaq

Bir addım irəli sürüşən proqnozlar: gündəlik pəncərə 250 gün (Bazel minimumu), aylıq pəncərə 120 ay; realizə olunmuş
hipotetik P&L ilə müqayisə. Testlər: **Kupiec** qeyri-şərti örtük (POF), **Christoffersen** müstəqillik və şərti örtük,
**Acerbi–Székely Z2** ES testi (Z2 = Σ X_t·1{X_t < −VaR_t}/(T·α·ES_t) + 1; p-dəyəri hər metodun öz proqnoz
paylanmasından H0 altında 1000 simulyasiya ilə), **Bazel svetoforu** (son 250 gün, 99%: 0–4 yaşıl, 5–9 sarı, ≥10
qırmızı). p ≥ 0,05 «keçdi», əks halda «keçmədi»; gözlənilən pozuntu sayı < 1 olduqda «yoxlanıla bilməz». 1 illik
horizont və neft gəlirləri üçün müstəqil müşahidə azdır — «yoxlanıla bilməz» (n = 0) kimi dərc olunur.

## 7. Riskə məruz kapital (CaR): fiskal kapital

Fiskal kapital NW_t = ARDNF_t + AMB ehtiyatları_t + xəzinə qalığı_t − dövlət borcu_t (mln USD), «şərti öhdəliklər
daxil» variantında çağırılmış zəmanətlər və bank rekapitalizasiyası da çıxılır. 2026–2030 il sonları üzrə paylanma
RU birgə Monte Karlosunun (`simulate.run`, N = 20 000) hər yolu üçün qurulur:

* **Birgə çəkilişlər.** Qeyri-neft artımı, İQİ, büdcə balansı (bütün kanallar), Brent və şərti devalvasiya
  `simulate.py`-dan; qlobal bazar amilləri (UST, valyutalar, səhm, qızıl) VaR qatının aylıq t-kopulasından 12 aylıq
  cəm kimi. İki blok **Brent-in ranqına görə** birləşdirilir: simulyasiyada k-cı ən kiçik Brent dəyişməsinə kopulanın
  k-cı ən kiçik Brent dəyişməsi olan amil vektoru verilir (kopulanın aktivlərlə asılılığı saxlanılır, Brent marjinalı
  RU-nunkudur). İllik amil çəkilişlərinin ortası sıfıra bərabərləşdirilir — risk qatı gəlirlilik proqnozlaşdırmır;
  gəlir (daşıma) ayrıca fərz olunur: sabit gəlirli = UST 5 il gəlirliliyi, səhm 1,5%, daşınmaz əmlak 3%, qızıl 0.
* **ARDNF**: ARDNF_t = ARDNF_{t−1}·(1 + R_t + daşıma) + (daxilolmalar_t − xərclər_t)/e_t; daxilolmalar = «base 60»
  ARDNF gəlirləri × Brent_t / Nazirliyin Brent fərziyyəsi (elastiklik 1, FƏRZİYYƏ); xərclər və transfert = Nazirlik planı.
* **AMB ehtiyatları**: neft səbəbli cari hesab sapmasının 10%-i (κ = 0,1; qalan hissə artıq ARDNF daxilolmalarında
  əks olunur), devalvasiya ilində −60% (2015 analoqu: 13,8 → 5,0 mlrd USD). FƏRZİYYƏ.
* **Borc**: §8-dəki stoxastik DSA. Kəsir borcla maliyyələşir (φ = 1, FR1 qaydası); profisit ən çoxu ödəmə vaxtı çatmış
  əsas borcu ödəyir, artığı xəzinədə yığılır (borc mənfi ola bilməz).

CaR_q = E[NW] − Q_{1−q}(NW); ES_q = E[NW] − E[NW | NW ≤ Q_{1−q}]; q = 95%, 99%. Risk iştahı həddləri parametrdir
(NW/ÜDM < 50% və < 75% ehtimalı, ARDNF örtüyü < 3 il; Nazirlik qərarı — DR10).

**Şərti öhdəliklər** (açıq hissə): dövlət zəmanətli borc (MN bülleteni). Çağırış ehtimalı ildə 2%, stressdə (devalvasiya
və ya Brent < 45) 20%, çağırılan pay 50%. Bank sektoru: devalvasiya ilində kredit itkisi 15%, Brent < 45 ilində 5%;
kapitalın kreditlərin 10%-indən artıq hissəsi itkini udur, qalan rekapitalizasiya dövlətin üzərinə düşür. Bütün bunlar
KALİBRLƏMƏ FƏRZİYYƏLƏRİDİR (DR01, DR02, DR08 cavablandıqda yenilənəcək).

## 8. Stoxastik borc davamlılığı (DSA)

D_t = D_{t−1} + max(axın, 0) − min(profisit, amortizasiya) + VAL_t, axın = −φ·balans_t + ΔFAİZ_t (+ ŞÖ_t);
VAL_t = xarici valyutada borc × [(e_t/e_{t−1})·(1 + çarpaz məzənnə dəyişməsi) − 1]; ΔFAİZ_t = dəyişkən faizli borc
(ümumi borcun 16,3%-i) × ΔUST2. **Başlanğıc qalıq (v2.4, audit M7):** MikroUnit FR1 məlumat bazasının 2025-ci il
sonu qalığı (MN anlayışı, 25 987,5 mln AZN) və 2026-cı ilin tam büdcə ili — FR1 ilə eyni lövbər (RU-nun deterministik
yolu FR1 debt/ÜDM ilə üst-üstə düşür). MN bülleteni (01.07.2026, 23 830,6 mln AZN) FR1 v2.3.4-dən **2026 lövbəridir**: ilsonu = bülleten − 2026 balansı × 6/12
≈ 23 387 mln AZN; fərq birdəfəlik qalıq-axın düzəlişi (−1 713,5 mln AZN) kimi 2026-ya əlavə olunur və birbaşa
`MicroUnit/output/FR1_debt_nowcast.csv`-dən oxunur (RU yenidən hesablamır); 2027-dən identitet. Bülleten artıq müstəqil
yoxlama deyil (`MN_bulleten_rolu`, `qaliq_axin_duzelisi_2026_mln_azn` sütunları). Nominal ÜDM =
FR1 bazası × [(1 − neft payı)·Π(1+Δg)(1+Δπ) + neft payı·Brent/Brent_baza·e/1,70]; neft payı OxLon oil_nom/gdp_nom.
Ümumi maliyyələşmə ehtiyacı (GFN) = −balans + amortizasiya + ΔFAİZ; borc xidməti/gəlir = (effektiv faiz × borc +
amortizasiya) / FR1 büdcə gəlirləri. Bütün sabitlər `input/parametrler.csv`-dədir (mənbə və əsaslandırma ilə).

**Həddlər.** 30/45/60% ÜDM (risk iştahı, DR10 — Nazirlik qərarı) heç vaxt aşılmır (P ≤ 0,003), ona görə məlumat
xarakterli həddlər əlavə olunub: borc > 20% və > 25% ÜDM, borcun 2025 səviyyəsini aşması, GFN > 5% ÜDM, borc
xidməti > 10% gəlir; beynəlxalq müqayisə üçün BVF MAC DSA bençmarkları (borc 70%, GFN 15% ÜDM). Bunlar risk iştahı
deyil. **Variantlar:** (i) φ = 1 (FR1 qaydası, bütün fiskal kanallar); (ii) φ = 0,5 — kəsirin/profisitin yarısı
ARDNF-dən/ARDNF-ə (v2.3-dəki «investisiya reaksiyası xaric» variantı (i) ilə eyni idi, çünki reaksiya transfertlə
maliyyələşir — çıxarılıb); (iii) (i) + şərti öhdəliklər (zəmanətli borc 7 232,3 mln AZN, bank rekapitalizasiyası).

## 9. ARDNF-in stress altında adekvatlığı

RU-nun daimi stress dəsti S1–S8 (`measures.stress_scenarios`, eyni Brent yolları) üçün: Brent yolu → daxilolmalar;
portfel gəlirliliyi = kopulada eyni Brent dəyişməsinə şərti orta (ən yaxın 2% çəkiliş) + daşıma; S3-də 2027
devalvasiyası (25%) manat transfertlərinin dollar dəyərini azaldır. ψ = 0: yalnız plan transferti; ψ = 1: ssenarinin
büdcə balansı sapması ARDNF-dən əlavə transfertlə örtülür. Çıxış: ARDNF aktivləri, istinad yolundan fərq və
**transfert örtüyü (il)** = ARDNF (manatla) / illik transfert; stoxastik sətirlər p05 və P(örtük < 3 il) verir.

## 10. Suveren şərti öhdəliklər yanaşması (CCA) — ƏLAVƏ (qərar göstəricisi deyil)

Gray–Merton–Bodie (2007): A log-normal, qəza həddi DB = qısamüddətli + 0,5 × uzunmüddətli borc (KMV), r = UST 2 il,
T = 1 il, DD = [ln(A/DB) + (r − σ²/2)T]/(σ√T). v2.4-də yenidən qurulub (V4): A = ARDNF + AMB ehtiyatlarının 50%-i
(qalanı pul bazasını və valyuta depozitlərini təmin edir — FƏRZİYYƏ), σ_ARDNF V3-ün 1 illik t-kopula VaR99-undan,
AMB ehtiyatlarının σ-sı devalvasiya itkisindən (60% × devalvasiya ehtimalı), öhdəliklərə bütün dövlət borcu və
zəmanətli borc (7 232,3 mln AZN) daxildir. Nəticə: bütün variantlarda DD ≈ 26–42, PD ≈ 0, aktivlər qəza həddinə
çatmaq üçün ≈ 87–95% düşməlidir. Suveren xalis kreditor olduğu üçün CCA **məlumatsızdır** və K5-də «ƏLAVƏ» statusu ilə
saxlanılır; qərar göstəriciləri K2 (CaR) və K4 (ARDNF örtüyü)-dür.

## 11. Makro «X-risk altında» xülasəsi (K1)

Qiymətləndirmə ili üzrə: **ÜDM-ə risk** (qeyri-neft artım, baza − p05), **inflyasiyaya risk** (p95 − baza),
**fiskal risk** (balans/ÜDM, baza − p05), **cari hesaba risk** (yalnız Brent kanalı: OxLon cari hesab–Brent
həssaslığı × RU Brent paylanması), **borca risk** (DSA p95 − baza, qiymətləndirmə ili və 2030), **ARDNF-ə risk**
(simulyasiya ortası − p05), **fiskal kapitala risk** (CaR95, CaR99), **neft gəlirlərinə risk** və **ARDNF bazar VaR-ı**.

## 12. Fərziyyələr və parametrlər (Nazirlik tərəfindən dəyişdirilə bilər)

v2.4-dən bütün sabitlər `input/parametrler.csv` faylındadır (açar, dəyər, vahid, izah, **mənbə**, **əsaslandırma**, modul,
status) və `riskunit/parametrler.py` ilə oxunur: dsa_* (faiz, amortizasiya, φ, şərti öhdəliklər, həddlər), car_* (AMB
devalvasiya itkisi 0,60, daşıma gəlirləri səhm 1,5% / daşınmaz əmlak 3% / qızıl 0 / sabit gəlirli = UST 5 il → cəmi
≈ 2,3%/il), var_re_beta, hedge_*, obj_fk_tail_weight; simulate.py-nin f_obs_growth (0,5) və enerji keçidi sürüşməsi
(−3%/il) də sənədləşdirilib (simulyasiya bölməsi oxumağa keçməlidir). Aşağıdakı cədvəl tarixçə üçündür.

| Parametr | Dəyər | Əsas | Harada |
|---|---|---|---|
| λ (yaşa görə çəki) | 0,995 gündəlik; 0,98 aylıq | sabit, sənədləşdirilmiş (BRW 1998) | var.LAMBDA |
| EVT həddi | itkilərin 90-cı faizi | standart POT seçimi | var.EVT_Q |
| Daşınmaz əmlakın səhm betası | 0,5 | FƏRZİYYƏ (DR03) | var.RE_BETA |
| ARDNF müddət qruplarının müddəti | 0,5 / 2 / 4 / 7,5 il | FƏRZİYYƏ (DR03) | exposures.fi_key_rate_durations |
| Working düzəlişi (1 ay) | √1,5 | aylıq ortaların dispersiya əmsalı 2/3 | var.WORKING |
| Barel/ton | 7,33 | Azeri Light | exposures.BBL_PER_TONNE |
| φ (kəsirin borcla maliyyələşən payı) | 1 | FR1 qaydası | dsa.PHI_DEBT |
| Effektiv faiz | 3,8% | MN bülleteni, 2026 I yarımil faiz ödənişləri / qalıq | dsa.INT_EFF |
| Amortizasiya | xarici 11,9%, daxili 7,4%, zəmanətli 13,1% /il | MN ödəmə profili (5 ilədək paylar / 5) | dsa.AMORT_* |
| Zəmanət çağırışı | 2% / stressdə 20%, pay 50% | KALİBRLƏMƏ FƏRZİYYƏSİ (DR02) | dsa.CL_* |
| Bank itkisi | devalvasiya 15%, Brent < 45: 5%; kapital həddi 10% | KALİBRLƏMƏ FƏRZİYYƏSİ (DR01) | dsa.BANK_* |
| κ (AMB-nin cari hesab payı) | 0,1 | FƏRZİYYƏ | car.KAPPA_CA |
| AMB-nin devalvasiya ilində itkisi | 60% | 2015 analoqu | car.CBAR_DEVAL_DRAIN |
| Daşıma gəliri | UST 5 il / 1,5% / 3% / 0 | FƏRZİYYƏ | car.CARRY |
| Risk iştahı | NW/ÜDM 50% və 75%; örtük 3 il; borc 30/45/60% | **Nazirlik qərarı (DR10)** | car.APPETITE, dsa.THRESH_DEBT |

## 13. Məhdudiyyətlər və mənfi nəticələr

1. Gündəlik qızıl tarixçəsi yalnız AMB XML-indən (≈ 3 il) gəlir; buna görə gündəlik VaR pəncərəsi və geriyə doğru
   sınağın n-i qısadır. LBMA/FRED qızıl seriyası əlçatan deyil (FRED seriyanı ləğv edib, LBMA 403 qaytarır).
2. Qlobal səhm proksisi ABŞ indeksidir (S&P 500 / OECD); ARDNF səhmlərinin yalnız ≈ 27,5%-i Şimali Amerikadadır.
   Valyuta tərcüməsi ayrıca modelləşdirildiyi üçün bu, əsasən yerli səhm bazarlarının korrelyasiya xətasıdır.
3. EM korporativ spredi (ICE BofA, FRED-də yalnız son 3 il) Azərbaycan suveren spredinin proksisidir (DR06).
4. Devalvasiya riski VaR-da yoxdur (bağlı məzənnə rejimi); CaR/DSA-da RU-nun şərti devalvasiya hadisəsi istifadə olunur.
5. **RU birgə simulyasiyasının fiskal kanalı** (MikroUnit v2.3.1 multiplikatorları, balance_n mln AZN): Brent-in
   bazadan yuxarı mərkəzi yolu prosiklik investisiya reaksiyası kanalı vasitəsilə büdcə balansını mediana görə
   ≈ 3% ÜDM pisləşdirir; bu, DSA-nın əsas variantında borcun yüksək quyruğunu böyüdür. Buna görə «reaksiya xaric»
   variantı ayrıca verilir. `simulate.py`-ın `via()` funksiyası balance_n-i mln AZN kimi qəbul edir (gdp_n-ə bölür) —
   yeni vahidlə uyğundur; ara versiya v2.3 (faiz sapması) ilə uyğun deyildi.
6. 1 illik VaR-da tarixi üst-üstə düşən pəncərələr effektiv olaraq ≈ 20 müstəqil müşahidədir — yoxlanıla bilməz.
7. Nazirlik «base 60» ARDNF aktivləri (2025: 58 984 mln USD) faktiki qalıqdan (73 541) xeyli aşağıdır (DR12);
   ARDNF yolu faktiki qalıqdan başlayır, Nazirlik planından yalnız axınlar götürülür.

## 14. İşə salma

```
python3 -m riskunit.feeds_market [--backfill 1100 --max-requests 800]   # V2 (+ AMB XML keşi)
python3 -m riskunit.exposures                                          # V1, V1b
python3 -m riskunit.var                                                # V3–V6
python3 -m riskunit.dsa                                                # K3
python3 -m riskunit.car                                                # K1, K2, K4, K5 (K3 daxil)
RISK_NO_NETWORK=1 python3 -m unittest tests.test_var tests.test_car -v
```
Hər modulda `run(ctx: dict) -> dict` var; eyni `ctx` ötürüldükdə `var` → `dsa` → `car` ardıcıllığı simulyasiyanı və
kopulanı təkrar hesablamır.

## 15. İlk canlı işə salmanın nəticələri (06.10.2026)

**Məruz qalmalar (V1).** ARDNF aktivləri 72 596,6 mln USD (30.06.2026): sabit gəlirli 33,8%, səhm 28,1%, qızıl 31,4%
(178,1 ton), daşınmaz əmlak 6,7%; valyuta: USD 69,7% (qızıl daxil), EUR 17,7%, GBP 4,9%, CNY 2,3%, JPY 1,5%, digər
3,9%. AMB ehtiyatları 15 301,3 mln USD (31.08.2026). Dövlət borcu 23 830,6 mln AZN (ÜDM-in 18,2%-i, 01.07.2026):
xarici 4 616,8 mln USD, daxili 15 982,0 mln AZN; dövlət zəmanətli borc 7 232,3 mln AZN (5,5%). Büdcənin neft gəlirləri
2025: 18 828 mln AZN (ümumi gəlirlərin 48,0%-i). Neft-qaz ixracı 2025: 20 605 mln USD (mal ixracının 85,6%-i).
Bank sektoru (31.08.2026): aktivlər 62 476, kapital 7 753 mln AZN, QİK 946,8 mln AZN (2,88%). Fiskal kapital
73 880 mln USD (zəmanətlər çıxılmaqla 69 626).

**ARDNF portfelinin VaR-ı (mln USD; 95% / 99%).**

| Horizont | HS | Yaşa çəkili HS | MK t-kopula | EVT | Kornish–Fişer | Kök-zaman (təxmini) |
|---|---|---|---|---|---|---|
| 1 gün | 673 / 1 177 | 820 / 1 408 | 637 / 1 198 | 663 / 1 243 | 644 / 1 654 | — |
| 1 ay | 2 463 / 4 919 | 2 410 / 4 697 | 2 678 / 4 682 | 2 515 / 4 962 | 2 972 / 5 323 | 3 082 / 5 393 |
| 1 il | 7 913 / 12 298 | 6 666 / 9 952 | 6 819 / 11 376 | 8 314 / 12 389 | 7 678 / 12 450 | 10 678 / 18 681 |

t-kopulanın ν = 10 (gündəlik və aylıq). 99% 1 illik VaR portfelin ≈ 15,7%-idir (MK). Kök-zaman 1 illik VaR-ı
≈ 50% şişirdir — yalnız müqayisə üçündür. Büdcənin neft gəlirlərinə risk (2027, FR1 bazası 17 723 mln AZN): birgə
simulyasiya 2 809 / 4 728 mln AZN (95/99%); yalnız Brent-in tarixi 12 aylıq dəyişmələri ilə −14 / 2 050 (cari Brent
bazadan yüksək olduğundan 95%-də çatışmazlıq yoxdur).

**Geriyə doğru sınaq (ARDNF).** Gündəlik, n = 360 (18.12.2024–29.09.2026): HS 99% — 6 pozuntu (gözlənilən 3,6),
Kupiec p = 0,25, Christoffersen p = 0,06, Acerbi–Székely p = 0,10, svetofor yaşıl (son 250 gündə 4); HS 95% —
Kupiec keçdi (p = 0,11), **müstəqillik keçmədi** (p = 0,004: pozuntular qruplaşır — sabit pəncərəli HS-in gözlənilən
zəifliyi, dəyişkənlik dinamikası qəsdən modelləşdirilmir); yaşa çəkili HS 99% ES testi keçmədi (p = 0,019); KF 95%
Kupiec keçmədi (30 pozuntu). Aylıq, n = 127 (2016–2026): bütün HS/yaşa çəkili HS testləri keçdi; KF 99% ES testi
keçmədi (p = 0,031); EVT aylıq pəncərədə (120 ay) yoxlanıla bilməz. 1 illik horizont yoxlanıla bilməz.

**Fiskal kapital (K2, şərti öhdəliklər xaric).** 2027: orta 80 459 mln USD, CaR95 15 034, CaR99 21 503, ES99 24 349;
2030: orta 92 936, CaR95 31 655, CaR99 43 807. Şərti öhdəliklər daxil 2030 CaR99 44 102. NW/ÜDM < 75% ehtimalı 2030-da 0,4.

**DSA (K3).** Əsas variant: borc/ÜDM 2027 median 18,3%, p95 22,6%; 2030 median 21,5%, p95 48,8%;
P(> 30%) = 0,28, P(> 45%) = 0,07 (2030); GFN p95 17,8% ÜDM. Prosiklik reaksiya xaric: 2030 median 11,8%, p95 20,8%,
P(> 30%) ≈ 0. Fərq tamamilə RU fiskal kanalından irəli gəlir (§13.5).

**ARDNF adekvatlığı (K4).** İstinad yolunda transfert örtüyü 11,6 il (2027) → 16,5 il (2030). S1 (Brent 45): 2030
aktivləri 76,5 mlrd USD (istinaddan −22,3 mlrd), örtük 12,7 il; S3: 77,5 mlrd. Stoxastik: 2027 örtüyün p05-i 9,6 il,
P(örtük < 3 il) ≈ 0. Qeyd: RU stress dəstində S1/S3 büdcə balansını yaxşılaşdırır (+0,45…+2,0% ÜDM), ona görə ψ = 1
əlavə çıxarış yaratmır — bu, `measures.py`/`simulate.py` fiskal kanalının yoxlanılmalı xüsusiyyətidir.

**CCA (K5, təxmini).** Qəzaya qədər məsafə: V1 41,6; V2 29,9; V3 (S3 + borcun p95-i) 7,9 — risk-neytral ehtimal ≈ 0.
Likvid valyuta aktivləri valyuta borcunu ≈ 18 dəfə üstələyir; suveren balansın zəif yeri likvidlik deyil, fiskal axın
(neft gəlirlərindən asılılıq, 48%) və ARDNF-in bazar riskidir.
