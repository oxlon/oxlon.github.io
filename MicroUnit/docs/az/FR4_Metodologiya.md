> **İngilis dilində (English version):** [FR4_Methodology.md](../FR4_Methodology.md). Rəqəmlərin yazılışı: mətndə onluq kəsr vergüllə, minliklər boşluqla ayrılır; cədvəllərdə, düsturlarda, kodda və fayl adlarında onluq kəsr proqram çıxışında olduğu kimi nöqtə ilə verilir. `AUTO` işarələri arasındakı bloklar hər icrada notebook tərəfindən bu sənəddə də Azərbaycan dilində yenidən yazılır.

# FR4 — Əhalinin məşğulluq göstəriciləri
## Struktur ekonometrik metodologiya və beşillik proqnoz

**MİİS modulu 15.5.2 — Mikroiqtisadi təhlil və proqnozlaşdırma**
Azərbaycan Respublikasının İqtisadiyyat Nazirliyi

`FR4.ipynb` faylını müşayiət edən sənəd. Bir-biri ilə əlaqəli üç nəticə məhsulunun üçüncüsü: **FR1** (sahələr üzrə
buraxılış və makroiqtisadiyyat), **FR3** (orta aylıq əmək haqqı), **FR4** (məşğulluq).

---

## Yenidənbaxma qeydi (2026-09-27, ikinci mərhələ 2026-09-28)

Aparılmış ekspertiza göstərdi ki, birinci versiyada seçim və validasiya üst-üstə düşürdü, bir sıra iddialar
(kointeqrasiya, “lövbəri dəqiq təkrarlayır”, “faktiki məşğulluq nəticələrindən istifadə edilmir”) özünü doğrultmurdu və
qeyri-müəyyənlik dərc edilməmişdi. Notebook ümumi düzəliş müqaviləsi çərçivəsində iki mərhələdə yenidən işlənmiş və
FR1-in yenidən icra olunmuş nəticələri (əhali trayektoriyası və 500 makro təkrarlama trayektoriyası) əsasında əvvəldən
sona qədər yenidən icra edilmişdir (0 xəta, ehtiyat variant (fallback) xəbərdarlığı yoxdur). Aşağıdakı bütün rəqəmlər
həmin icradan götürülmüşdür.

1. **Seçim artıq nümunədən kənar yoxlama (hold-out) dövrünü “görmür”.** Hər bir seçim yalnız 2019-cu ilədək olan
   məlumatlardan istifadə edir və yalnız 2019-cu ilədək olan illəri qiymətləndirir: başlanğıclar 2011–2014 (2010-cu il
   təsnifat qırılmasından sonra), beşillik pəncərələr. Namizədlər sabit paylarla Diebold–Mariano testi (HLN düzəlişi ilə)
   vasitəsilə **hədəf ilinə görə orta hesablanmış** itki fərqi əsasında müqayisə edilir (hər qiymətləndirilən il üçün
   bir müşahidə, cəmi səkkiz), çünki eyni ili qiymətləndirən üst-üstə düşən başlanğıclar müstəqil deyil.
2. **Sahələr üzrə bölgü (ikinci mərhələ).** Birləşdirilmiş, məhdudiyyətli pay sistemi — nisbi məşğulluq payının nisbi
   real buraxılış payına görə vahid ümumi elastikliyi, qrup sabit effektləri ilə birinci fərqlərdə qiymətləndirilir —
   sabit paylarla müqayisədə yoxlanılır. O, 10% səviyyəsində üstünlük qazanmır (6,96%-ə qarşı 6,48%, p = 0,45), buna
   görə də həm 1-ci pillədə, həm də sənaye daxilində **əsas variant bu ikisinin bərabər çəkili kombinasiyasıdır**. Təmiz
   sabit paylar, yalnız birləşdirilmiş sistem və qrupa xas amillər Hissə 18-in həssaslıq variantlarıdır. Adambaşına
   gəlir (birinci versiyanın qalibi) yalnız məlumat üçün təqdim olunur.
3. DSK-nın fəaliyyət növləri cədvəllərində **2010-cu il təsnifat qırılması**: hər səviyyə tənliyində pilləvari fiktiv
   dəyişən (step dummy) daxil edilir, birinci fərq qiymətləndirmələrində 2010-cu il fərqi çıxarılır, başlanğıclar və
   yelpik qrafiki üçün təkrar seçmə (resampling) 2011-ci ildən başlayır, shift-share dekompozisiyasının 2010-cu il sətri
   isə əsas bölgüdən kənarlaşdırılır.
4. **Qiymətləndirmə və statistik nəticə.** Səviyyə əlaqələri üçün DOLS (qiymətləndirici və sərbəstlik dərəcələri (df)
   qeyd olunur), qalıqlara əsaslanan kointeqrasiya p-dəyərləri (`eg_coint_p`), n/(n−k) miqyaslaması ilə HAC, kiçik nümunə
   üçün t/F statistik nəticəsi və hər səviyyə əmsalının yanında fərq formasında qiymətləndirmə. Əlaqələrin əksəriyyəti
   kointeqrasiya olunmayıb, buna görə də onların t-statistikaları təsviri kimi işarələnir.
5. **2019-cu ilədək məlumatlar əsasında qəbul edilmiş qərarlar**: E1-də vahid əhali elastikliyi (2019-cu ilədək
   məlumatlar üzrə HAC-F p = 0,081; tam nümunə üzrə 0,38; rədd edilmir, aşağı güc), E3-də trendin olmaması barədə qərar
   (2019-cu ilədək məlumatlar üzrə t = 0,28) və E8-in qiymətləndirmə nümunəsi (2000-ci ildən başlanğıc; 1990-cı ildən
   başlanğıc xeyli pis proqnoz verir, DM p = 0,03).
6. **Aqreqat blok və lövbərlər.** Əsas məşğulluq və işçi qüvvəsi göstəriciləri FR1-dən götürülür, E1–E2 isə 2025-ci ilə
   lövbərlənmiş çarpaz yoxlamadır. Muzdlu işçilərin payı üçün yalnız bir trayektoriya var (2024-cü ilin faktiki
   göstəricisi, 0,3540), buna görə də əvvəlki 2026-cı il sıçrayışı aradan qalxmışdır. 2025-ci ilin bütün lövbərləri
   təkrarlanır.
7. **İnstitusional bölgülər.** Büdcə = σ × dörd büdcə fəaliyyət növündə muzdlu işçilər; burada σ = <!-- AUTO:fr4v22_sigma1 -->0,9092 (v2.2: 2024 dəyəri; əvvəl 0,913)<!-- /AUTO:fr4v22_sigma1 --> DSK-nın
   2.12–2.13 cədvəllərindən götürülmüş dövlət payıdır; F3 tapıntısı anlayış (tərif) fərqi kimi yenidən şərh edilir.
   R7-dəki iddia düzəldilmişdir. E9 n = 10 üzrə OLS-dir, onun nümunədən kənar yoxlaması qiymətləndirilə bilmir və neftin
   hər iki bazası 2025-ci ilə lövbərlənir.
8. **Mədənçıxarma və neft emalı E9 ilə uyğunlaşdırılmışdır (ikinci mərhələ).** Neft hasilatı və neft yataqlarına
   xidmətlər (mədənçıxarmanın təxminən 86%-i) və neft emalı (emal sənayesinin daxilində) E9-a uyğun hərəkət edir.
   Sənayenin qalan qeyri-neft hissəsi 1-ci pillə mexanizmi ilə bölüşdürülür.
9. **Faktiki nəticələrdən istifadə edilmədən nümunədən kənar yoxlama**: cəmlər proqnozlaşdırılan əhali ilə 2019-cu
   ilədək qiymətləndirilmiş E1–E2 vasitəsilə simulyasiya edilir və bütün sabitlər 2019-cu ilədək olan məlumatlar üzrə
   yenidən qiymətləndirilir.
10. **Shift-share (struktur sürüşmə)** dekompozisiyasında nominal paylara əsaslanan Törnqvist çəkilərindən istifadə
    olunur, buna görə də zəncirvari həcmlər toplanmır. Neft və qeyri-neft bölgüsü hər biri vahid baza daxilində aparılır.
    Mətndəki səhvlər düzəldilmişdir.
11. **Yelpik qrafikləri** (`FR4_fan_employment.csv`): 2011-ci ildən etibarən tarixi qalıq trayektoriyalarının təkrar
    seçməsi (qiymətləndirilmiş avtokorrelyasiya olmadan), parametr çəkilişləri və FR1-in 500 çəkilişi. Notebook hər bir
    nöqtəvi proqnozun öz kvartillərarası zolağının daxilində olduğunu yoxlayır (assert). Düzəliş əmsalları sabit
    saxlanılır; onların sabit bir illik yarımsönmə dövrü ilə sönməsi (v2.3; heç nə qiymətləndirilmir) yalnız həssaslıq variantı kimi göstərilir.

---

## 1. Tapşırıq

> *Əhalinin məşğulluq göstəriciləri (onların iqtisadiyyatın sahələri, dövlət və qeyri-dövlət sektoru,
> büdcə və qeyri-büdcə təşkilatları, neft və qeyri-neft sektoru üzrə **sayı** və **artım sürətləri**)
> təhlili və proqnozlaşdırılması mümkün olmalıdır.*

Əhalinin məşğulluq göstəricilərinin — **sayının** və **artım sürətlərinin** — (1) iqtisadiyyatın sahələri, (2) dövlət
və qeyri-dövlət sektoru, (3) büdcə və qeyri-büdcə təşkilatları, (4) neft və qeyri-neft sektoru üzrə təhlili və
proqnozlaşdırılması. Proqnoz üfüqü 2026–2030.

**Məhdudiyyətlər.** AR, ARIMA, ARCH və ya GARCH modellərindən istifadə edilmir. Əlaqəli sahələrin təsirinin görünməsi
üçün yalnız struktur ekonometrik modellər tətbiq olunur. İş kitabında (Excel faylında) məlumat çatışmadıqda, o, Dövlət
Statistika Komitəsindən (DSK) toplanmalıdır.

---

## 2. Kənar məlumatlara niyə ehtiyac yarandı

`Statistik data dinamika 05.06.2026 +.xlsx` iş kitabı məşğulluğun sahə və institusional bölgüsünü **yalnız beş il
üçün** əks etdirir:

| İş kitabında yeri | Məzmun | İllər |
|---|---|---|
| `Sosial sektor ` r58–r59 | İşçi qüvvəsi; məşğul əhali | 1995–2025 |
| `DVX üzrə göstəricilər` r91–r103 | Əmək müqavilələri: cəmi, neft, dövlət, qeyri-dövlət, 8 sahə | **2021–2025** |
| `DVX üzrə göstəricilər` r130 | Büdcə təşkilatlarında işçilərin sayı | **2022–2025** |
| dörd sənaye vərəqi | Muzdlu işçilər, 29 sənaye sahəsi | 2016–2025 |
| `Regionlar`…`Regionlar 13` | Muzdlu işçilər, 14 region | 2021–2025 |

Beş il üzrə illik müşahidələr on doqquz fəaliyyət növündən ibarət struktur sistemi identifikasiya etməyə imkan vermir.
Buna görə də DSK məlumatlarının toplanması tələbi təkmilləşdirmə deyil, ilkin şərt idi.

**Toplanmış məlumatlar** `stat.gov.az/source/labour/` ünvanından götürülmüş, `data/dsk/` qovluğunda saxlanılır və
olmadıqda avtomatik olaraq yenidən yüklənir:

| Fayl | Vərəq | Anlayış | İllər |
|---|---|---|---|
| `002_1-2en.xls` | `Dynamics_2.1` | Məşğul əhali, 19 fəaliyyət növü üzrə | 1999–2024 |
| `002_8-9en.xls` | `Dynamics_2.8` | Muzdlu işçilər, 19 fəaliyyət növü üzrə | 1999–2024 |
| `002_3en.xls` | `Dynamcs_2.3` | Məşğul əhali, mülkiyyət formaları üzrə | 1990–2024 |
| `002_12-13en.xls` | `2.12`, `2.13` | Muzdlu işçilər, fəaliyyət növü × mülkiyyət forması üzrə | 2023, 2024 |
| `006_1-5en.xls` | `Dynamics_6.1` | Dövlət Məşğulluq Agentliyinin göstəriciləri | 1991–2024 |

`Dynamcs_2.3` vərəq adı mənbənin özündəki orfoqrafik səhvi ehtiva edir və məhz bu formada uyğunlaşdırılmalıdır. Heç
bir oxuma funksiyası sabit sütun sürüşməsi fərz etmir; hər biri il sütunlarını başlıq sətrini skan etməklə müəyyən edir.

**Validasiya.** Hər bir fəaliyyət növü bloku dərc edilmiş cəmini maşın dəqiqliyi ilə təkrarlayır. DSK-nın müstəqil
şəkildə dərc edilmiş üç cədvəli 2024-cü il üçün bütün iyirmi sətir üzrə üst-üstə düşür. Həlledici olan odur ki, iş
kitabındakı məşğul əhali sırası (`Sosial sektor ` r59) və DSK-nın fəaliyyət növləri üzrə cəmi **üst-üstə düşən bütün
26 ildə son onluq rəqəmə qədər eyni sıradır**. Deməli, DSK bölgüsü məhz FR1-in proqnozlaşdırdığı aqreqatın
dekompozisiyasıdır və DSK paylarının FR1-in cəminə tətbiqi heç bir sıraların birləşdirilməsini (splice), bazanın
dəyişdirilməsini (rebasing) və ya anlayış fərqini tələb etmir.

---

## 3. Mənbələrin uzlaşdırılması və hansı mənbənin hansı funksiyanı yerinə yetirdiyi

Məşğulluğu sahələr üzrə iki mənbə əks etdirir və onlar müxtəlif kəmiyyətləri hesablayır.

- **DSK `Dynamics_2.8`** — müəssisə müayinəsindən (establishment survey) əldə olunan muzdlu işçilər; müəssisənin
  faktiki fəaliyyət növünə görə təsnif edilir.
- **İş kitabı, `DVX`** — vergi xidmətində qeydiyyata alınmış əmək müqavilələri; vergi ödəyicisinin qeydiyyatdakı
  fəaliyyət kodu üzrə təsnif edilir, dövrün sonuna.

**Cəmlər** 1–5% daxilində üst-üstə düşür. **Sahə strukturu isə üst-üstə düşmür**: DVX/DSK nisbəti 0,70-dən (kənd
təsərrüfatı) 1,81-ə qədər (yerləşdirmə və ictimai iaşə) dəyişir və bu nisbətlər 2021–2024-cü illərdə 0,55-ə qədər
**sürüşür**. İki mənbə artım baxımından da fərqlənir, buna görə də onları birləşdirmək (splice) mümkün deyil.

| Obyekt | İstifadə olunan mənbə | Səbəb |
|---|---|---|
| 19 fəaliyyət növü, 8 sahə qrupu | DSK müayinəsi, 1999–2024 | 26 il; cəmi dəqiq toplanır; onun cəmi iş kitabındakı cəmin *özüdür* |
| Dövlət / qeyri-dövlət | DSK, mülkiyyət forması, 1990–2024 | 35 il; iş kitabında məşğulluq üzrə ekvivalenti yoxdur |
| Büdcə / qeyri-büdcə | DSK, fəaliyyət növü × mülkiyyət + DVX r130 | Büdcədən maliyyələşən məşğulluğu müəyyən edən yeganə mənbələr |
| Neft / qeyri-neft | İş kitabındakı sənaye sahələri + DVX r92 | DSK-nın fəaliyyət növləri cədvəllərinin heç biri nefti ayrıca göstərmir |
| 2025-ci il dəyərləri, cari qiymətləndirmə (nowcast) lövbəri | İş kitabı | DSK-nın fəaliyyət növləri cədvəlləri 2024-cü ildə bitir |

Diqqətdən kənarda qalmamalı olan anlayış məsələsi. **Vergi uçotu bazasında** neft + dövlət + qeyri-dövlət = cəm
bərabərliyi **dəqiq** ödənilir, deməli, iş kitabındakı dövlət və qeyri-dövlət sətirləri **yalnız qeyri-neft
iqtisadiyyatını** əhatə edir. **DSK bazasında** dövlət + qeyri-dövlət = cəm bərabərliyi də dəqiq ödənilir, lakin neft
daxil olmaqla **bütün** məşğulluq üzrə. Beləliklə, “dövlət sektoru” iki mənbədə müxtəlif mənalar daşıyır; FR4 əsas
göstərici kimi DSK tərifini təqdim edir, iş kitabının daha dar bölgüsünü isə ayrıca təkrarlayır.

---

## 4. Məlumatların bütövlüyü üzrə tapıntılar

**F1 — Dövlət Məşğulluq Agentliyinin sıraları qiymətləndirmə üçün yararsızdır.** Qeydiyyatdakı işsizlərin sayı 81
272-dən (2019) 217 608-ə (2023) sıçrayır, 2020–2022-ci illər üzrə məlumat dərc edilməyib; vakansiyaların sayı 5 715-dən
(2022) 59 849-a (2023) sıçrayır. Hər iki qırılma eyni vaxta düşür və rəqəmsal qeydiyyata keçidi əks etdirir. Vakansiya
sırası FR4-ə əmək bazarının gərginliyi kanalını — FR3-də də çatışmayan həmin kanalı — verə bilərdi, buna görə də bu,
real itkidir və onun ətrafında model uyğunlaşdırmaq əvəzinə qeydə alınır.

**F2 — İş kitabındakı `priv_share` məşğulluqda özəl sektorun payı deyil.** O, DSK-nın qeyri-dövlət məşğulluq payından
14 faiz bəndinə qədər fərqlənir və fərqli dinamikaya malikdir. Ondan dövlət/qeyri-dövlət bölgüsü üçün istifadə etmək —
1995–2025-ci illəri əhatə etdiyi üçün aşkar qısa yol — yanlış olardı.

**F3 — Büdcə təşkilatlarında işçilərin sayı 2025-ci ildə 9% azalır, halbuki əmək müqavilələrinin ümumi sayı artır.**
DVX r130 2022–2024-cü illər üçün 636,7, 640,7, 645,9, 2025-ci il üçün isə 588,0 göstərir. *Yenidən şərh:* DSK-nın
2.12–2.13 cədvəlləri dörd büdcə fəaliyyət növündə 2024-cü ildə muzdlu işçiləri 588,6 min dövlət və 58,8 min qeyri-dövlət
hissəsinə bölür. 2022–2024-cü illərin dəyərləri həmin fəaliyyət növlərinin bütün muzdlu işçilərinə uyğun gəlir (nisbət
0,994); 2025-ci ilin dəyəri onların dövlət hissəsinə (−0,1%), azalma (57,8 min) isə qeyri-dövlət hissəsinə uyğun gəlir.
Bu “azalma”, çox güman ki, sətrin nəyi hesabladığındakı dəyişiklikdir; məlumat sahibindən təsdiq istənilmişdir.

**F4 — DVX-nin 127–129-cu sətirləri 123–125-ci sətirləri bayt-bayt təkrarlayır.** Büdcə təşkilatları üzrə vergi
ödəyicilərinin sayını, dövriyyəni və daxilolmaları göstərməli olan blok mikro vergi ödəyiciləri blokunu təkrarlayır.
Yalnız 130-cu sətir həqiqidir.

**F5 — İş kitabında muzdlu işçilərin sayına dair bir-birindən 11% fərqlənən iki sıra var.** 91-ci sətir (müqavilələr,
dövrün sonuna) 2024-cü il üçün 1 872,9 min, 107-ci sətir (muzdlu işçilər, aylıq orta) isə 2 073,8 göstərir. DSK
müayinəsi üçüncü rəqəmi — 1 780,3 verir. FR4 bütün hesablamalarda DSK bazasından istifadə edir və əhəmiyyət kəsb etdiyi
hər yerdə bu fərqi göstərir.

---

## 5. İzah edilməli olan struktur

Modelləşdirmə ilə bağlı hər bir seçim dörd faktla müəyyən olunur.

1. **Muzdlu işçilər məşğulların sabit üçdə birini təşkil edir.** Bu nisbət 26 il ərzində 0,306 ilə 0,368 arasında
   qalmışdır. Məşğulların təxminən üçdə ikisi muzdlu işçi deyil — Azərbaycan əmək bazarında, böyük əksəriyyəti kənd
   təsərrüfatında olan özünüməşğulluq üstünlük təşkil edir.
2. **Buraxılış payları kəskin dəyişdikdə belə məşğulluq payları çox yavaş dəyişir.** 2005–2024-cü illərdə sənayenin
   real əlavə dəyərdəki payı 5,6 faiz bəndi azalmış, məşğulluqdakı payı isə 0,9 faiz bəndi **artmışdır**.
3. **Mədənçıxarmada buraxılış kəskin azaldığı halda məşğulluq demək olar ki, dəyişməyib.** 2010→2024: buraxılış −27%,
   məşğulluq −5%.
4. **Dövlət sektorunda məşğulluq yavaş-yavaş azalan, demək olar ki, sabit səviyyədir.** 2000-ci ildən bəri
   məşğulluğun 1 174 min nəfərlik artımının 1 399 mini qeyri-dövlət, −225 mini isə dövlət sektorunun payına düşür.

**Shift-share (struktur sürüşmə) dekompozisiyası** (dəqiq eynilik, 7 × 10⁻¹⁵ dəqiqliklə qapanır), 2001–2024, zəncirvari
uyğun: artım sürətləri Törnqvist nominal əlavə dəyər payı çəkiləri ilə hesablanır, buna görə də zəncirvari həcmlər heç
vaxt sahələr üzrə toplanmır (sənayenin çəkisi onun dörd alt sahəsinin additiv nominal cəmidir). Əmək məhsuldarlığının
+133,4 loq bəndlik kumulyativ artımının +122,9-u sahədaxili artımın, +10,4-ü isə yenidən bölüşdürmənin payına düşür.
2010-cu il sətri təsnifat qırılmasını ehtiva edir (həmin il sahədaxili +2,91, yenidən bölüşdürmə +0,39). **Onu
çıxmaqla məhsuldarlıq artımının 92,3%-i sahələrin daxilində baş verir, 7,7%-i isə yenidən bölüşdürmədən irəli gəlir.**
Azərbaycanda məşğulluq struktur baxımından ətalətlidir.

---

## 6. Avtoreqressiyanın istifadə edilməməsi məhdudiyyəti — dəqiq ifadə

Heç bir tənlikdə asılı dəyişənin gecikməsi, sürüşən orta xətası və ya şərti dispersiya prosesi yoxdur və heç bir
proqnoz və ya yelpik qrafiki qiymətləndirilmiş avtokorrelyasiyaya əsaslanmır. Modeldə mövcud olan gecikmə
konstruksiyaları:

| Konstruksiya | Harada | Niyə avtoreqressiya deyil |
|---|---|---|
| Newey–West HAC kovariasiyası, n/(n−k) miqyaslaması | hər bir zaman sırası tənliyi | Yalnız standart xətalar |
| **İzahedici dəyişən** fərqlərinin DOLS qabaqlayıcıları/gecikmələri (lead/lag) | stoxastik izahedici dəyişənli səviyyə tənlikləri | Endogenlik düzəlişi; səviyyə əmsallarından istifadə olunur |
| Qrup sabit effektləri ilə birinci fərqlər | birləşdirilmiş pay sistemləri (1-ci pillə, sənaye) | Məşğulluq və buraxılış paylarının bir il ərzindəki fərqləri; sağ tərəfdə asılı dəyişənin gecikməsi yoxdur |
| Qalıqlara əsaslanan kointeqrasiya testində bir gecikmə | hər bir səviyyə tənliyi | Yalnız test statistikası |
| Sabit düzəliş əmsalı; sabit yarımsönmə dövrü ilə sönmə | Hissə 15, 18 | Sabit səviyyə düzəlişi; sönmə (ildə 0,5, yarımsönmə dövrü bir il — v2.3, qalıq avtokorrelyasiyası qiymətləndirilmir) **yalnız həssaslıq variantıdır**, proqnoz qaydası deyil |
| Tarixi qalıq trayektoriyalarının təkrar seçməsi | yelpik qrafikləri | Müşahidə olunmuş proqnoz xətası trayektoriyalarını $u_{s+h}-u_s$ təkrar tətbiq edir; qiymətləndirilmiş dinamika yoxdur |
| Nominal pay çəkiləri | shift-share | Uçot eyniliyi |

FR4-də natamam il üzrə məlumatlar yoxdur, buna görə də müqavilədə nəzərdə tutulan cari qiymətləndirmə (nowcast)
düzəliş əmsalı qaydası tətbiq olunmur.

---

## 7. Spesifikasiya axtarışı: nə rədd edildi

| # | Spesifikasiya | Nəticə | Sübut |
|---|---|---|---|
| R1 | ln(sahə məşğulluğu) ln(sahənin real əlavə dəyəri) üzrə | yalançı (spurious) | səviyyələr və fərqlər arasında qeyri-stabil; fərq formasında orta R² 0.026 |
| R2 | mədənçıxarmada məşğulluq xam neft hasilatı üzrə | səhv işarə | −0.052 (t = −1.8) |
| R3 | neft hasilatı sahəsi birləşdirilmiş neft+qaz həcmi üzrə | səhv işarə | −0.670 (t = −4.4) |
| R4 | iştirak səviyyəsi real əmək haqqı üzrə | səhv işarə | −0.072 (t = −12.6) |
| R5 | dövlət xidmətlərində məşğulluq, sərbəst əhali elastikliyi | inandırıcı deyil | 2.8, blok bölgüsündə isə 4.8 |
| R6 | dövlət sektorunda məşğulluq fiskal imkanlar və ya buraxılış üzrə | heç bir amil hər iki testdən keçmir | adambaşına real ÜDM: səviyyə t = −2.12 (p = 0.044), fərq t = +0.50 (“heç biri əhəmiyyətli deyil” ifadəsini düzəldir) |
| R7 | real kredit termini ilə bazar xidmətləri | səhv işarə | −0.167 (t = −4.1) |
| R8 | sahə üzrə əməyə tələbdə əmək haqqı termini | göstərilir, qoyulmur | panel −0.128 (t = −0.7), n = 290 |
| R9 | 1-ci pillədə qrupa xas nisbi buraxılış elastiklikləri | qəbul edilməyib | 6.96%-ə qarşı 7.32%, DM p = 0.42 |
| R10 | 1-ci pillədə adambaşına real qeyri-neft ÜDM (birinci versiya) | rədd edilib | 6.96%-ə qarşı 7.45%, DM p = 0.24 |
| R11 | 1-ci pillədə sadə trend | rədd edilib | 12.23%, statistik əhəmiyyətli dərəcədə pis (p = 0.07) |
| R12 | adambaşına gəlir + nisbi buraxılış | rədd edilib | 13.70% |
| R13 | 1-ci pillədə **yalnız** birləşdirilmiş buraxılış sistemi | təkbaşına qəbul edilməyib | 6.96%-ə qarşı 6.48%, DM p = 0.45 → bərabər çəkili kombinasiya vasitəsilə daxil olur |

---

## 8. Model

### 8.1 Aqreqat blok — əsas göstərici deyil, çarpaz yoxlama

Ümumi məşğul əhali və işçi qüvvəsi üzrə əsas göstəricilər **FR1-ə** məxsusdur (`emp`, `lf`). FR4-ün öz bloku
§11-dəki çarpaz yoxlama və §10-dakı nümunədən kənar yoxlamanın mexanizmidir.

$$L_t = N_t \,\pi_t\,(1-u_t), \qquad H_t = \phi_t L_t$$

- **E1 — işçi qüvvəsi.** Sərbəst əhali elastikliyi: 2019-cu ilədək məlumatlar üzrə (qərar nümunəsi) −3,64
  (s.x. 2,49), HAC-F(1,16) = 3,47, p = 0,081. Tam nümunə üzrə o, 0,14-dür (s.x. 0,96), p = 0,38.
  ln(əhali) ilə trend arasında korrelyasiya 0,996-dır. Vahid elastiklik **rədd edilmir (aşağı güc)**
  və identifikasiya fərziyyəsi kimi qoyulur. İştirak səviyyəsində trend yoxdur (2019-cu ilədək məlumatlar üzrə t = 0,4)
  və o, **2025-ci ilin faktiki səviyyəsində, 0,5256-da** saxlanılır.
- **E2 — məşğulluq səviyyəsi.** DOLS: $\ln(L/LF) = -0.860 + 0.0824\ln Q^{non} - 0.0036\,t$. Fərq forması
  0,0967 verir (95% etibarlılıq intervalı 0,021–0,172), bu interval səviyyə qiymətini ehtiva edir. Kointeqrasiya p-dəyəri
  0,225, DW isə 0,58-dir, buna görə səviyyə t-statistikaları təsviridir. FR1-in forması (adambaşına qeyri-neft ÜDM,
  trendsiz, iştirak trendi ilə) 0,0337 verir (kointeqrasiya p = 0,171). <!-- AUTO:e2gap -->İki blok 2030-cu ildə məşğulluq üzrə 1,05% (bütün ssenarilər və illər üzrə ən çoxu 1,33%), işçi qüvvəsi üzrə isə ən çoxu 0,23% fərqlənir. Hər ikisi 2025-ci ilin göstəricisini təkrarlayır.<!-- /AUTO:e2gap -->
- **E3 — muzdlu işçilərin payı.** 2019-cu ilədək məlumatlar üzrə trend +0,0006-dır (t = 0,28), tam nümunə üzrə isə
  t = 1,97. Fərq forması dreyf göstərmir və sıra U-formalıdır. O, **2025-ci ildən etibarən hər il üçün 2024-cü ilin
  faktiki səviyyəsində, 0,3540-da** saxlanılır.

### 8.2 Sahələr üzrə bölgü — proqnoz kombinasiyası ilə pay sistemi

$$\ln\!\left(\frac{s^L_{i,t}}{s^L_{r,t}}\right) = \alpha_i + \boldsymbol{\beta}_i'\mathbf{x}_t + \varepsilon_{i,t},
\qquad s^L_i = \frac{\exp(z_i)}{\sum_j \exp(z_j)}$$

**Seçim dizaynı.** Namizədlər 2011–2014-cü il başlanğıcları üzrə qiymətləndirilir: beşillik pəncərələr 2019-cu ildən gec olmayaraq
qiymətləndirilir, hər iki baza birləşdirilir, xətalar isə paylar üzrə ölçülür. Hər namizəd faktiki paylardan başlayır.
DM (HLN) testində hədəf ili üzrə itki fərqindən istifadə olunur:

| Namizəd | Birləşdirilmiş nümunədən kənar RMSE | Sabit paylara qarşı DM p |
|---|---|---|
| Birləşdirilmiş məhdudiyyətli buraxılış sistemi (vahid elastiklik, qrup FE ilə birinci fərqlər) | 6.48% | 0.45 |
| **Bərabər çəkili kombinasiya: sabit + birləşdirilmiş — əsas variant** | **6.56%** | 0.14 |
| Sabit paylar (sıfır model) | 6.96% | — |
| Qrupa xas nisbi buraxılış | 7.32% | 0.42 |
| Adambaşına real qeyri-neft ÜDM | 7.45% | 0.24 |
| Trend | 12.23% | 0.07 (pis) |
| Adambaşına gəlir + nisbi buraxılış | 13.70% | 0.13 (pis) |

**Qəbul edilmiş qayda.** Birləşdirilmiş sistem sabit payları p < 0,10 səviyyəsində üstələyərsə, əsas variant olur. O,
üstələmir, buna görə əsas variant iki proqnozun **bərabər çəkili kombinasiyasıdır**. Əsaslandırma: təmiz
sabit paylı əsas variantın özü davamlılıq (persistence) proqnozudur və FR1-in sahə ssenarilərinin sahə məşğulluğuna ötürülməsi üçün
heç bir yol vermir, faydası statistik əhəmiyyətli olmayan amil isə tam çəki daşımamalıdır.

**Birləşdirilmiş elastiklik** (birinci fərqlər, qrup sabit effektləri, 2010-cu il fərqi çıxarılmaqla, Driscoll–Kraay):
məşğul əhali bazasında **0,108** (s.x. 0,048, n = 161) və muzdlu işçilər bazasında **0,174** (s.x. 0,030).
Sabit effektlər β-nı identifikasiya edir, lakin qrup dreyfləri ekstrapolyasiya edilmir (sadə trend nümunədən kənar
uğursuz olur). Hər qrup 2024-cü ilin loq-şanslarından (log-odds) başlayır və β × onun nisbi buraxılış payındakı dəyişiklik
qədər, yarım çəki ilə hərəkət edir.

Sönümlənmiş gəlir elastikliyi də sınaqdan keçirilmişdir (λ ∈ {0,2; …; 1}, 2019-cu ildən əvvəlki başlanğıclar üzrə). Ən yaxşısı, λ = 0,2,
DM p = 0,29 verir; axtarış nəzərə alındıqdan sonra bu, 1,0-a çevrilir. **Qrupa xas gəlir elastiklikləri**
(2010-cu il pilləvari fiktiv dəyişəni ilə DOLS) təsviridir:
- 14-dən yalnız 3-ü 10% səviyyəsində kointeqrasiya olunub, 1-inin fərq forması əmsalı statistik əhəmiyyətlidir, 2-si isə
  öz fərq forması etibarlılıq intervalından kənarda yerləşir.
- Məşğul əhali bazası: kənd təsərrüfatı −0,055, sənaye +0,184, tikinti +0,216, ticarət −0,003,
  yerləşdirmə +0,595, nəqliyyat −0,008, İKT +0,003.

### 8.3 Qrupdaxili bölgü

- **Sənaye daxilində.** Neft hasilatı və neft yataqlarına xidmətlər (2024-cü ildə mədənçıxarmanın 86%-i: 33,0 min muzdlu işçidən
  28,3 mini) və neft emalı (4,0 min, emal sənayesinin daxilində) **E9**-a uyğun hərəkət edir: onlar 2024–2025-ci illərdə faktiki
  göstəricilərdir, sonra isə real neft ÜDM ilə birlikdə dəyişir. Sənayenin **qalan qeyri-neft hissəsi** eyni kombinasiya qaydası ilə
  qeyri-neft mədənçıxarma, neft emalından başqa emal sənayesi, elektrik enerjisi və su təchizatı arasında bölüşdürülür. Birləşdirilmiş
  sənayedaxili elastiklik 0,054 (məşğul əhali) və 0,160-dır (muzdlu işçilər). Seçimdə 2014–2016-cı il başlanğıcları istifadə olunmuşdur
  (sahələrin əlavə dəyəri 2009-cu ildən başlayır, buna görə bu, zəif dizayndır): birləşdirilmiş 10,64%, sabit isə 10,81%, DM p = 0,42, buna görə
  kombinasiya istifadə olunur. Qeyri-neft mədənçıxarma üçün buraxılış sırası yoxdur; onun amili qeyri-neft sənaye
  buraxılışıdır. Nəticə: mədənçıxarma indi öz neft hissəsi ilə birlikdə azalır (§11) və neft məşğulluğu azaldığı halda artıq
  sənayenin cəmi ilə birlikdə artmır.
- **Xidmətlər blokunun bölgüsü (E6)**: ln(bazar/büdcə xidmətləri) ln(digər xidmətlərin real əlavə dəyəri) üzrə, 2010-cu il
  pilləsi ilə, DOLS. Elastiklik 0,702 (məşğul əhali) və 1,626-dır (muzdlu işçilər). Kointeqrasiya yoxdur (p = 0,84 və
  0,39) və səviyyə qiymətləri fərq formasının etibarlılıq intervallarından kənarda yerləşir, buna görə t-statistikaları
  təsviridir. Nümunədən kənar o, sabit bölgünü üstələyir: 9,50%-ə qarşı 6,71%, DM p = 0,015, buna görə saxlanılır.
  Düzəliş əmsalları +0,054 və +0,028-dir və sabit saxlanılır.
- **Hər blokun daxilində struktur (E7)**: hər fəaliyyət növü üçün trend sabitlə müqayisə edilir; hər ikisi
  faktiki dəyərdən başlayır, 2019-cu ildən əvvəlki başlanğıclar, bazalar birləşdirilir. **Heç bir trend saxlanılmır (7-dən 0).** Bazar
  xidmətləri üçün fəaliyyət növü səviyyəsində buraxılış yoxdur, buna görə birləşdirilmiş mexanizm orada tətbiq edilə bilməz. Nəticədə
  birinci versiyanın ildə təxminən −1,8% ekstrapolyasiya etdiyi məşğul əhali bazasında daşınmaz əmlak indi bazar
  xidmətləri bloku ilə birlikdə artır (§11). Bu, §13-də qeyd olunan məlumat məhdudiyyətidir.

### 8.4 Dövlət və qeyri-dövlət

R6: heç bir amil həm səviyyə, həm də fərq testindən keçmir. E8 logistik trenddir; onun nümunəsi 2019-cu ildən əvvəlki başlanğıclar üzrə
seçilir (1990-cı ildən başlanğıc xeyli pis proqnoz verir: 2,7%-ə qarşı 22,3%, DM p = 0,03). 2000–2024-cü illər üzrə
trend ildə −0,0239-dur (t = −21,7, R² = 0,963). Fərq formasında orta dəyişiklik −0,0261-dir (etibarlılıq intervalı
−0,041-dən −0,011-dək) və onu ehtiva edir, trend-stasionarlıq p-dəyəri isə 0,063-dür. Dövlət payı
siyasət rıçağıdır.

### 8.5 Büdcə və qeyri-büdcə

$$B_t = \sigma \sum_{i \in \{\text{pubadm, educ, health, art}\}} H_{i,t}, \qquad \text{non-budget}_t = H_t - B_t$$

σ dörd fəaliyyət növündə muzdlu işçilərin **dövlət payıdır** və DSK-nın 2.12–2.13 cədvəllərindən götürülür: <!-- AUTO:fr4v22_sigma2 -->0,9169
(2023) və 0,9092 (2024). **v2.2:** `Dynamics_2.12` 2005-ci ildən hər ili verir; son dərc olunmuş il 2010–2019
başlanğıclarında iki ilin ortasından dəqiqdir, buna görə σ = **0,9092** (əvvəl orta 0,913).<!-- /AUTO:fr4v22_sigma2 --> Birinci versiyanın bütün muzdlu işçilərə tətbiq edilən κ = 0,994 əmsalı
2022–2024-cü illər üçün DVX r130-u təkrarlayırdı, lakin özəl məktəbləri və klinikaları da hesablayırdı. Eynilik 2025-ci il <!-- AUTO:fr4v22_r130 -->üçün
r130-un 588,0 min göstəricisinə qarşı 594,2 min verir (1,0%; köhnə orta ilə 596,7)<!-- /AUTO:fr4v22_r130 -->, bu da F3-ün anlayış baxımından şərhi ilə uyğundur. <!-- AUTO:fr4v22_history -->2005–2022-ci illər üçün
müşahidə olunan σ istifadə olunur (v2.2); 2005-dən əvvəl mülkiyyət bölgüsü yoxdur.<!-- /AUTO:fr4v22_history -->

### 8.6 Neft və qeyri-neft

Statistik baza: 2025-ci ildə 30,87 min. Vergi uçotu bazası (DVX r92): 47,78. **E9** OLS-dir (n = 10,
df = 8), elastiklik 0,80 (t = 4,9). Onun fərq forması (−0,45, etibarlılıq intervalı −1,13-dən 0,24-dək) bu qiyməti ehtiva etmir və
kointeqrasiya p-dəyəri 0,17-dir, buna görə o, təsviridir. O, yeganə ssenari kanalı kimi saxlanılır və
indi mədənçıxarma və emal sənayesinin neft hissələrini də müəyyən edir. Neft emalı və yardımçı xidmətlər hasilata nisbətdə 2025-ci il
səviyyəsində saxlanılır, beləliklə, 2025-ci il təkrarlanır. Qeyri-neft hər baza daxilində hesablanır.

---

## 9. Həll və düzəliş əmsalları

Sistem blok-rekursivdir:
- FR1 cəmi → muzdlu işçilər (φ) → 8 qrup (kombinasiya) → sənaye (neft hissələri E9 üzrə, qeyri-neft qalığı
  kombinasiya ilə) və xidmətlər (E6, sonra sabit struktur) → 19 fəaliyyət növü.
- Dövlət (E8) cəmə, büdcə (σ) isə muzdlu işçilərin bölgüsünə tətbiq olunur.

Düzəliş əmsalları hər qiymətləndirilmiş tənliyin öz lövbər ilindəki qalığıdır; bir dəfə oxunur və **sabit saxlanılır**,
çünki qalıqların stasionarlığı ümumiyyətlə göstərilməyib:
- E6: +0,054 (məşğul əhali) və +0,028 (muzdlu işçilər).
- E8: −0,018.
- E9: 2025-ci ilin faktiki göstəricisinə lövbərlənir.

Pay bloklarına düzəliş lazım deyil. Sabit bir illik yarımsönmə dövrü ilə sönmə (v2.3; ρ̂ istifadə olunmur) **yalnız həssaslıq variantı** kimi göstərilir (§12, §18). Lövbərlər
dəqiq təkrarlanır (Hissə 19-dakı 2025 lövbəri yoxlaması): paylar 2024-cü il üzrə (3 × 10⁻¹⁴% dəqiqliklə), cəm, işçi qüvvəsi, hər iki bazada neft
və vergi uçotu üzrə müqavilələr isə 2025-ci il üzrə. **Əhali** FR1-in dərc edilmiş trayektoriyasıdır.

---

## 10. Validasiya

**Dinamik nümunədən kənar yoxlama, 2020–2024, 2019-cu ildən sonrakı heç bir məlumatdan istifadə edilmədən.**
- Cəmlər 2019-cu ilədək yenidən qiymətləndirilmiş FR4-ün E1–E2 tənlikləri ilə simulyasiya edilir: əhali ildə 1,07% artımla proqnozlaşdırılır,
  iştirak səviyyəsi 0,5073, muzdlu işçilərin payı 0,3441, E2 elastikliyi isə 0,077-dir.
- Bütün pay lövbərləri, birləşdirilmiş elastikliklər, meyl əmsalları və düzəliş əmsalları 2019-cu ilədək yenidən qiymətləndirilir.
- Modelə faktiki buraxılış amilləri verilir.
- Sənaye daxilində neft hissəsinin ayrılması tətbiq edilmir, çünki E9 2020-ci ildən əvvəl qiymətləndirilə bilmir (4
  müşahidə). **E9-un nümunədən kənar yoxlaması qiymətləndirilə bilməyən kimi göstərilir.**
- Müqayisə meyarlarına eyni informasiya verilir: təsadüfi gəzişmə = 2019-cu il səviyyəsi; sabit artım = 2005–2019-cu illərin
  orta artımı (2005 neft bumunun başlanğıcıdır).

| Sıra | RMSE | Təsadüfi gəzişməyə qarşı U | Sabit artıma qarşı U |
|---|---|---|---|
| Ümumi məşğul əhali (E1–E2, simulyasiya) | 1.12% | **0.37** | **0.73** |
| Muzdlu işçilər | 2.06% | **0.39** | 2.41 |
| İşçi qüvvəsi | 0.10% | **0.03** | **0.67** |
| Dövlət sektorunda məşğulluq | 3.89% | **0.60** | **0.82** |
| Neft hasilatı (E9) | qiymətləndirilə bilmir | — | — |

| Səviyyə | Median RMSE | Təsadüfi gəzişməni (RW) üstələyir | Median U (RW) | Sabit artımı (CG) üstələyir | Median U (CG) |
|---|---|---|---|---|---|
| 19 fəaliyyət növü, məşğul əhali | 4.85% | 9/19 | 1.04 | 6/19 | 1.36 |
| 8 qrup, məşğul əhali | 2.79% | 5/8 | 0.77 | 4/8 | 1.11 |
| 19 fəaliyyət növü, muzdlu işçilər | 7.12% | 9/19 | 1.06 | 11/19 | 0.98 |
| 8 qrup, muzdlu işçilər | 7.21% | 5/8 | 0.80 | 5/8 | 0.97 |

Müqayisə üçün birinci versiya: cəm üzrə U = 0,35 / 0,69, fəaliyyət növlərindən isə 14/19 və 10/19-u təsadüfi
gəzişməni üstələyirdi. Həmin versiyaya faktiki cəmlər verilmişdi və o, öz amilini 2020–2024-cü illəri nəzərə alaraq seçmişdi.

**On eynilik və lövbər yoxlamasının hamısı uğurla keçir:**
1. 19 fəaliyyət növünün cəmi ümumi göstəriciyə bərabərdir.
2. Dövlət + qeyri-dövlət = məşğul əhali.
3. Büdcə + qeyri-büdcə = muzdlu işçilər.
4. Hər baza daxilində neft + qeyri-neft = cəm.
5. Model 2024 lövbər ilində hər fəaliyyət növünü təkrarlayır.
6. Hər pay (0; 1) intervalında qalır.
7. Məşğulluq / işçi qüvvəsi < 1, hər ikisi FR1-dən.
8. Hər düzəliş əmsalı tətbiq olunur.
9. 2025-ci il lövbərləri təkrarlanır.
10. Muzdlu işçilərin payı üçün yalnız bir trayektoriya var.

**2025-ci il üzrə cari qiymətləndirmənin (nowcast) vergi uçotu ilə müqayisəsi — zəif yoxlama.** DVX/DSK sahə nisbətlərinin
2024-dən 2025-ə orta mütləq sürüşməsi 0,033-dür. Bu, əsasən vergi uçotu üzrə sahə artımını ümumi artımla müqayisə edir.

**FR3 ilə uyğunluq.** FR4-ün muzdlu işçilər trayektoriyası FR3-ünkündən sabit olaraq 12,3% aşağıdır və artım 0,000 f.b. dəqiqliklə üst-üstə düşür —
bu, konstruksiya etibarilə belədir, buna görə bu, təsdiq deyil, uyğunluqdur.

---

<!-- AUTO:results (FR4.ipynb Hissə 20.2 tərəfindən icranın nəticələri əsasında yaradılır; əl ilə redaktə etməyin) -->
## 11. Əsas ssenarinin nəticələri, 2026–2030

Ümumi məşğulluq (FR1) 5 105 min nəfərdən 5 270 min nəfərədək artır — **ildə +0,64%** (90% zolaq: -0,27% ilə +1,52% arası).

| Qrup | İllik, % | 90% zolaq |
|---|---|---|
| Yerləşdirmə və iaşə | +0.90 | -1.89 ilə +3.77 arası |
| İnformasiya və rabitə | +0.86 | -0.32 ilə +1.96 arası |
| Nəqliyyat və anbar | +0.74 | -0.61 ilə +2.20 arası |
| Kənd, meşə və balıqçılıq | +0.67 | -0.21 ilə +1.52 arası |
| Ticarət və təmir | +0.64 | -0.28 ilə +1.56 arası |
| Digər xidmətlər (9 fəaliyyət) | +0.60 | -0.41 ilə +1.61 arası |
| Sənaye | +0.55 | -0.64 ilə +1.64 arası |
| Tikinti | +0.52 | -0.96 ilə +1.89 arası |

- **Sənaye daxilində** (məşğul əhali əsasında): mədənçıxarma ildə -0,46% (onun neft hissəsi E9 tənliyinə tabedir), emal sənayesi +0,66%.
- **Digər xidmətlər daxilində**: bazar xidmətləri artır (məşğul əhali üzrə ildə +1,67%, muzdlu işçilər üzrə +3,49%), büdcədən maliyyələşən xidmətlər isə məşğul əhali əsasında azalır (-0,04%), muzdlu işçilər əsasında azalır (-0,50%): digər xidmətlərin buraxılışı artdıqca E6 məşğulluğu büdcədən maliyyələşən blokdan bazar xidmətlərinə doğru keçirir və burada bu keçid büdcədən maliyyələşən bloku mütləq ifadədə kiçildəcək qədər sürətlidir.
- **Tikinti**: FR1-də tikinti buraxılışı 2026-cı ildə -19,0% dəyişir; tikintidə məşğulluq həmin il -0,60%, ümumi məşğulluq isə +0,53% dəyişir — enmə var, lakin sönümlüdür (kiçik elastikliyə yarım çəki verilir).

Müqayisə üçün birinci versiya (FR1-in əvvəlki yolu ilə): yerləşdirmə və iaşə +2,42%, informasiya və rabitə +1,43%, tikinti +1,24% … ticarət +0,32%, cəmi +0,53%.

- **Dövlət sektorunda** məşğulluq: 1 049,3 → 984,0 min nəfər (ildə -1,28%; zolaq -2,40% ilə -0,19% arası), pay 20,6% → 18,7%.
- **Büdcə təşkilatları** (σ = 0,909): 594,2 → 579,5 min nəfər (ildə -0,50%; zolaq -1,75% ilə +0,55% arası), 2030-cu ildə muzdlu işçilərin 31,1%-i.
- **Neft sektorunda** məşğulluq, vergi uçotu əsasında: 47,8 → 45,5 min nəfər (ildə -0,97%; zolaq -2,46% ilə +0,69% arası); statistik əsasda 30,9 → 29,4.

**Ssenarilər.** 2030-cu ildə FR1-in ssenariləri real neft ÜDM-i üzrə 22,0%, qeyri-neft ÜDM üzrə 12,10%, məşğulluq üzrə 0,39% fərqlənir; buna görə FR4-ün məşğulluğu da 0,39% (20,3 min nəfər) fərqlənir. Neft sektorunda məşğulluq ssenarilər arasında 17,3% ayrılır (Mənfi 40,7, İslahat 47,8 min nəfər).

**Yelpik qrafikləri** (`FR4_fan_employment.csv`, `FR4_fan_summary_2030.csv`): 2 000 təkrarlama — tarixi qalıq yollarının yenidən seçilməsi (18 tənlik üzrə 2011–2018 illərində başlayan 8 birgə 6 illik yol, mərkəzləşdirilmiş; E9 üçün başlanğıclar 2016–2020), parametr çəkilişləri və FR1-in 500 makro çəkilişi birləşdirilir. Hər nöqtəvi proqnoz öz kvartillərarası zolağının daxilindədir (Hissə 17.5-də yoxlanılır).

---

## 12. Rıçaqlar və həssaslıqlar (2030, Əsas ssenari)

| Rıçaq | 2030-cu ilə təsir |
|---|---|
| əhali artımı 0.3 faiz bəndi aşağı | ümumi -78.6 min (-1.5%); işçi qüvvəsi -82.4 min (-1.5%); kənd təsərrüfatı -27.9 min (-1.5%) |
| əhali artımı 0.3 faiz bəndi yuxarı | ümumi +79.5 min (+1.5%); işçi qüvvəsi +83.4 min (+1.5%); kənd təsərrüfatı +28.2 min (+1.5%) |
| muzdlu işçilərin payı 2030-a qədər +2 faiz bəndi | muzdlu işçilər +105.4 min (+5.7%); büdcə +32.7 min (+5.7%); qeyri-büdcə +72.7 min (+5.7%) |
| dövlət payı 2024-cü il səviyyəsində dondurulmuş | dövlət +119.9 min (+12.2%); qeyri-dövlət -119.9 min (-2.8%) |
| büdcə = 4 fəaliyyətin bütün muzdlu işçiləri (κ = 0.994, 1-ci versiya) | büdcə +53.9 min (+9.3%) |
| 1-ci pillə + sənaye: təmiz sabit paylar | yerləşdirmə və iaşə -1.8 min (-1.7%); informasiya və rabitə -0.9 min (-1.5%); tikinti +2.9 min (+0.7%) |
| 1-ci pillə + sənaye: yalnız birləşdirilmiş buraxılış sistemi | yerləşdirmə və iaşə +1.8 min (+1.7%); informasiya və rabitə +0.9 min (+1.5%); tikinti -2.9 min (-0.7%) |
| 1-ci pillə sürücüsü: qrupa xas nisbi buraxılış payı (qəbul edilməyib) | yerləşdirmə və iaşə +6.5 min (+5.8%); informasiya və rabitə -1.2 min (-1.9%); tikinti +4.4 min (+1.0%) |
| 1-ci pillə sürücüsü: qrupa xas adambaşına gəlir (qəbul edilməyib) | yerləşdirmə və iaşə +10.1 min (+9.1%); tikinti +17.9 min (+4.3%); sənaye +15.0 min (+3.5%) |
| YALNIZ HƏSSASLIQ: düzəliş əmsalları sabit yarımsönmə dövrü ilə sönür (1 il; E6, E8) | bazar xidmətləri -17.8 min (-3.3%); dövlət +14.3 min (+1.4%); büdcə +4.7 min (+0.8%) |

Sönmə sətri proqnoz qaydası deyil, yalnız həssaslıqdır. Ən böyük dəyişkənliyi yenə dövlət payı rıçağı yaradır: bu, ekonometrik deyil, siyasi qərardır.

---

<!-- /AUTO:results -->

## 13. Məhdudiyyətlər

1. **Sahə strukturu iqtisadiyyata yalnız zəif reaksiya verir.** 2020-ci ildən əvvəl heç bir amil nümunədən kənar
   sabit payları üstələməmişdir. Əsas variant kiçik birləşdirilmiş buraxılış elastikliyi ilə bərabər çəkili
   kombinasiyadır. Bazar xidmətlərinin strukturu fəaliyyət növü səviyyəsində buraxılış məlumatları olmadığı üçün sabitdir.
2. **Fəaliyyət növü səviyyəsində dəqiqlik məhduddur**: obyektiv nümunədən kənar yoxlamada hər bazada 19 fəaliyyət növündən 9-u
   təsadüfi gəzişməni üstələyir.
3. **Səviyyə əlaqələrinin əksəriyyəti kointeqrasiya olunmayıb**, buna görə onların t-statistikaları təsviridir.
4. **Bu, səviyyələr modelidir**: uyğunlaşma sürəti qiymətləndirilmir.
5. **Ümumi məşğulluq və işçi qüvvəsi FR1-ə məxsusdur**; FR4-ün öz bloku çarpaz yoxlamadır (fərq ≤ 1,45%).
6. **Əhali FR1-in fərziyyəsidir.**
7. **Muzdlu işçilərin payı və dövlət payı proqnozlaşdırılmır, təyin edilir.**
8. **Neft sektorunda məşğulluq on müşahidəyə əsaslanır**, nümunədən kənar test edilə bilmir və indi mədənçıxarma
   və emal sənayesinin neft hissələrini də müəyyən edir.
9. **2010-cu il təsnifat qırılması** geriyə hesablama (back-cast) ilə deyil, pilləvari fiktiv dəyişənlə nəzərə alınır.
10. **Neft/qeyri-neft bölgüsünü dövlət/qeyri-dövlət bölgüsü ilə toplamaq olmaz.**
11. **Əmək bazarının gərginliyi kanalı və əmək haqqı kanalı yoxdur.**

### Növbəti məlumat buraxılışını (vintage) nə təkmilləşdirərdi

- 2023-cü il qırılmasını əhatə edən uzlaşdırılmış vakansiya və ya qeydiyyatdakı işsizlik sırası.
- Daha çox il üçün DSK-nın fəaliyyət növü × mülkiyyət forması cədvəlləri və 2010-cu il qırılması üzrə DSK-nın geriyə hesablaması.
- Bazar xidmətləri üçün fəaliyyət növü səviyyəsində buraxılış.
- Rəsmi əhali proqnozu və daha uzun sənaye sahələri paneli.
- DVX r130-un 2025-ci ildə nəyi hesabladığının (F3) və 127–129-cu sətirlərin (F4) təsdiqi.

---

## 14. Nəticə faylları

`FR4.ipynb` — <!-- AUTO:cells -->119 xana (83 kod, 36 markdown)<!-- /AUTO:cells -->, əvvəldən sona qədər 0 xəta ilə icra olunur. Onun Hissə 20.2 xanası bu sənədin §8.1-dəki çarpaz yoxlama fərqini, §11 və §12-ni icranın nəticələri əsasında (`AUTO` markerləri arasında) yenidən yaradır, buna görə bu rəqəmlər heç vaxt əl ilə yazılmır.
`docs/FR4_Methodology.md` — bu sənəd. `output/` qovluğundakı CSV faylları:

| Fayl | Məzmun |
|---|---|
| `FR4_employment_long.csv` | Uzun (tidy) format: ssenari × baza × il × fəaliyyət növü, səviyyə və artım sürəti |
| `FR4_employed_by_activity.csv`, `FR4_hired_by_activity.csv` | Səviyyələr, 19 fəaliyyət növü, 3 ssenari |
| `FR4_employed_growth_rates.csv`, `FR4_hired_growth_rates.csv` | Artım sürətləri |
| `FR4_institutional_breakdown.csv` | Dövlət/qeyri-dövlət, büdcə/qeyri-büdcə, neft/qeyri-neft (hər iki baza), FR1 işçi qüvvəsi |
| `FR4_fan_employment.csv`, `FR4_fan_summary_2030.csv` | Nöqtəvi proqnozla birlikdə kvantil zolaqları, səviyyələr və artım |
| `FR4_dsk_*.csv` (5 fayl) | Toplanmış DSK tarixi məlumatları |
| `FR4_tier1_driver_selection.csv`, `FR4_tier2_driver_selection.csv`, `FR4_e6_bloc_split_selection.csv` | Hədəf ili üzrə DM testləri ilə 2019-cu ilədək məlumatlar əsasında seçim |
| `FR4_tier1_income_elasticities_descriptive.csv` | Kointeqrasiya və fərq forması testləri ilə DOLS elastiklikləri |
| `FR4_rejected_specifications.csv` | Rədd edilmiş / qəbul edilməmiş spesifikasiyalar |
| `FR4_holdout_validation.csv`, `FR4_holdout_validation_groups.csv`, `FR4_holdout_summary.csv`, `FR4_holdout_aggregate.csv` | Təsadüfi gəzişməyə və sabit artıma qarşı Theil U |
| `FR4_identity_checks.csv`, `FR4_equation_audit.csv`, `FR4_add_factors.csv` | Yoxlama; audit faylında qiymətləndirici, df, `eg_coint_p`, statistik nəticə işarəsi və fərq formasının etibarlılıq intervalı göstərilir |
| `FR4_sensitivity_levers.csv`, `FR4_scenario_summary.csv` | Rıçaqlar və ssenarilər |
| `FR4_shift_share_decomposition.csv` | Zəncirvari uyğun dekompozisiya |

---

<!-- AUTO:v2 (FR4.ipynb Hissə 26 tərəfindən icranın nəticələri əsasında yaradılır; əl ilə redaktə etməyin) -->
## 15. v2 — tənliklər reyestri, tam proqnoz cədvəli, ssenari mühərriki və dayanıqlıq

*Bu bölmə FR4.ipynb-nin 21–26-cı hissələri tərəfindən hər icrada yenidən yazılır.*

**Tənliklər reyestri** (`output/FR4_equations.json`, 21-ci hissə): notebook-da qiymətləndirilən hər tənlik — cəmi **125**, onlardan **11**-i proqnozda istifadə olunur. Bloklar üzrə: A 9, B 37, C 31, D 5, E 1, R 42 (R — rədd edilmiş/alternativ spesifikasiyalar, A — məcmu blok, B — 1-ci pillə pay sistemi, C — sənaye daxilində və xidmətlər, D — institusional bölgülər, E — shift-share). Reyestr hər tənliyi statsmodels ilə eyni (y, X) üzərində müstəqil yenidən qiymətləndirir və əmsalların notebook-un öz qiymətləndirmələrinə bərabər olduğunu yoxlayır (hamısı uyğun gəlir); diaqnostika (DW, BG, JB, White, RESET, VIF, kointeqrasiya, fərq forması), rekursiv və bir ili çıxarmaqla qiymətləndirmələr, Chow və CUSUM əlavə olunur.

**Dayanıqlıq hökmləri** (`FR4_robustness_summary.csv`): bütün tənliklər — stabil 19, qismən stabil 40, qeyri-stabil 66; proqnozda istifadə olunanlar — stabil 4, qismən stabil 4, qeyri-stabil 3. Kövrək (qeyri-stabil) proqnoz tənlikləri: `FR4.E5_pooled_emp` (rekursiv: d_lo_sq işarəsi son yarıda dəyişir; bir ili çıxarmaqla: d_lo_sq işarəsi dəyişir); `FR4.E6_emp` (rekursiv: d2010 işarəsi son yarıda dəyişir; Chow 2012 (orta nöqtə) p = 0,000; Chow 2015 (2015) p = 0,000; Chow 2020 (2020) p = 0,000; CUSUM p = 0,022); `FR4.E6_hired` (Chow 2012 (orta nöqtə) p = 0,034; Chow 2015 (2015) p = 0,012; Chow 2020 (2020) p = 0,000). Kointeqrasiya testi aparılan 73 səviyyə tənliyindən yalnız 11-ində 10%-də müəyyən edilir — t-statistikaları əksər hallarda təsviridir (19.4-cü hissə ilə uyğun). R9 sənaye panelində əmək haqqı elastikliyi -0,128: Driscoll–Kraay p = 0,508, wild-cluster bootstrap (illər üzrə, Webb) p = 0,544; buraxılış elastikliyinin bootstrap p-dəyəri 0,066 (DK: 0,031).

**Tam proqnoz cədvəli** (`FR4_forecast_tidy.csv`): 75 komponent × 3 ssenari, tarix ilk mövcud ildən, 2025 (nowcast) və 2026–2030; tamlıq yoxlanılır (1125 dəyər). 8 qrup və iki xidmət bloku indi hər üç ssenari üçün verilir (əvvəl qruplar yalnız Əsas ssenarinin fan cədvəlində idi). Zolaqlar (5–95%) Əsas ssenari üçün 14 sıra üzrə. Proqnozlaşdırılmayanlar və səbəbləri: `FR4_not_forecast.csv` (15 sıra: Məşğulluq Agentliyinin qırılan sıraları, vergi uçotu üzrə sahə bölgüsü, DVX r130/r107, regionlar). Kataloq: `FR4_indicator_catalog.csv` (id-lər `fr4:emp:<fəaliyyət>`, `fr4:hired:<fəaliyyət>`, `fr4:<əsas>:grp:<qrup>`, `fr4:<əsas>:bloc:pub|mkt`, `fr4:state`, `fr4:budget`, `fr4:oil:stat|tax`, `fr4:lf`, `fr4:phi` və s.).

**Ssenari mühərriki** (`microlib/engines/fr4.py`, vəziyyət `output/engine/FR4_state.json`): notebook-un 15–17-ci hissələrdəki həllini təkrarlayır. Redaktə olunan girişlər: 16 ekzogen FR1 yolu (`fr1:emp`, `fr1:lf`, `fr1:pop`, `fr1:rgdpnon`, `fr1:rgdpoil`, 11 `fr1:rva_*`), 10 əmsal (birləşdirilmiş β-lar, birləşmə çəkiləri, E6, E8, E9) və 7 rıçaq (əhali artımı, muzdlu payı, dövlət payı trend/dondurulmuş, σ/κ, düzəliş əmsallarının sönməsi). `upstream={"FR1": ...}` verildikdə FR1 mühərrikinin yolları istifadə olunur; FR3 proqnozda istifadə olunmur. Özünü yoxlama: hər ssenari üzrə notebook CSV-ləri maksimal nisbi fərq 3,8·10⁻¹⁶ ilə təkrarlanır, 18-ci hissənin rıçaq cədvəli də (34 dəyər) təkrarlanır; bir ssenari ~16 ms.

**Əmsal həssaslığı** (`FR4_coef_sensitivity.csv`, ±1 standart xəta, 2030, Əsas): dövlət məşğulluğu — `FR4.E8_state|trend` ilə -0,54% / +0,54%; büdcə təşkilatları — `FR4.E6_hired|ln_rva_oth` ilə +0,87% / -0,88%; ən böyük üç qrup (Kənd, meşə və balıqçılıq, Digər xidmətlər (9 fəaliyyət), Ticarət və təmir) birləşmə çəkisinə ən həssasdır (çəki üçün SE olmadığından ±0,25) — Kənd, meşə və balıqçılıq ±0,07%, Digər xidmətlər (9 fəaliyyət) ±0,09%, Ticarət və təmir ±0,06%. Ümumi məşğulluq FR1-dəndir və FR4 əmsallarından asılı deyil.

Yeni fayllar: `FR4_equations.json`, `FR4_indicator_catalog.csv`, `FR4_forecast_tidy.csv`, `FR4_not_forecast.csv`, `FR4_robustness_summary.csv`, `FR4_coef_sensitivity.csv`, `FR4_strings_az.csv` (istifadəçiyə görünən hər ingiliscə sətrin Azərbaycan dilində qarşılığı, 438 sətir), `engine/FR4_state.json` (yalnız sadə məlumat). v2-dən əvvəlki bütün CSV-lər dəyişməz qalır (reqressiya yoxlaması).

<!-- /AUTO:v2 -->

<!-- v2.1-begin -->
## 16. v2.1 (2026-10-05) — Driscoll–Kraay p-dəyərləri t(T−1) ilə

**Xəta.** `FR4_equations.json`-da Driscoll–Kraay panel tənliklərinin p-dəyərləri t(n−k) paylanmasından (n — vahid-il müşahidələri),
etibarlılıq intervalları isə t(T−1)-dən (T — illərin sayı, DK zaman klasterləri) hesablanırdı — məsələn, `FR4.E4_pooled_emp`: t(n−k) ilə
p = 0,028, t(T−1) ilə 0,037. Notebook-un öz `panel_fe` funksiyası (Hissə 8) da t(n−k) p-dəyərləri verirdi.

**Düzəliş.** `panel_fe` p-dəyərlərini indi t(T−1) ilə hesablayır — FR1, FR3 və reyestrin konvensiyası (microlib konvensiyası 7);
əmsallar, standart xətalar (DK, 2 gecikmə, n/(n−k) miqyaslaşdırması) və t-statistikaları dəyişmir. Reyestr bu p-dəyərlərini alır
(`fit_p`), ixrac xanası isə hər DK əmsalı üçün yoxlayır (assert): reyestrin p-dəyəri notebook-un p-dəyərinə və
2·P(t<sub>T−1</sub> > |t|)-yə bərabərdir, interval eyni t(T−1) kvantilindən qurulur. Heç bir proqnoz, seçim və ya rədd qərarı bu
p-dəyərlərindən istifadə etmir (qərarlar t-statistikalarına, işarələrə və nümunədən kənar testlərə əsaslanır), buna görə CSV faylları
dəyişmir; yalnız `FR4_equations.json`, R9 qeydi və yuxarıdakı §15 dəyişir.

| Tənlik | əmsal | T−1 | t | əvvəlki p (t(n−k)) | yeni p (t(T−1)) |
|---|---|---|---|---|---|
| C1_real_lvl = E4_panel_hired_lvl | lo_sq | 24 | 5.99 | 1.3e-08 | 3.5e-06 |
| C1_real_diff = E4_panel_hired_fd | d_lo_sq | 23 | 5.80 | 3.4e-08 | 6.5e-06 |
| C1_nom_lvl | lo_sq | 19 | 2.68 | 0.0083 | 0.0148 |
| C1_nom_diff | d_lo_sq | 18 | 4.36 | 0.00003 | 0.00038 |
| R9_wage_panel | ln_real_output | 9 | 2.55 | 0.0114 | 0.0313 |
| R9_wage_panel | ln_real_wage | 9 | −0.69 | 0.491 | 0.508 |
| E4_pooled_emp | d_lo_sq | 22 | 2.22 | 0.0279 | 0.0371 |
| E4_panel_emp_fd | d_lo_sq | 23 | 2.31 | 0.0223 | 0.0303 |
| E4_pooled_hired | d_lo_sq | 22 | 5.91 | 2.1e-08 | 6.0e-06 |
| E4_panel_hired_lvl_tw | lo_sq | 24 | 3.77 | 0.00024 | 0.00093 |
| E5_pooled_emp | d_lo_sq | 13 | 0.64 | 0.527 | 0.535 |
| E5_pooled_hired | d_lo_sq | 13 | 0.82 | 0.416 | 0.426 |
| E4_panel_emp_lvl, E4_panel_emp_lvl_tw | lo_sq | 24 | 12.7, 13.5 | < 1e-15 | 4.1e-12, 1.1e-12 |

5% səviyyəsində heç bir əhəmiyyətlilik hökmü dəyişmir (C1_nom_lvl 1% zolağından 5% zolağına keçir). Bu icrada FR4-ün məşğulluq
proqnozlarının dəyişməsinin yeganə səbəbi FR1 v2.1-in onun girişlərini dəyişməsidir (`FR1_forecast_full.csv`, `FR1_fan_draws.csv`;
FR1 v2.1 qeydinə bax).
<!-- v2.1-end -->

---

<!-- AUTO:fr4v22_note -->
## 17. v2.2 (2026-10-05) — Nazirliyin makro modulunun məlumatları

**Dövlət sektorunda məşğulluq (E8).** Trendsiz və öz gecikmələri olmayan struktur alternativlər E8 kimi yoxlanılıb (2011–2014
başlanğıcları, ≤2019; 2020–2024 yoxlaması × simulyasiya edilmiş cəm): adambaşına real dövlət istehlakı (MOE SNA `GC`, 1995–2024,
`data/macro_module/fr345_moe_spec_panel.csv`), onun real qeyri-neft ÜDM-ə nisbəti, adambaşına real qeyri-neft ÜDM və tərkib modeli
(DSK `Dynamics_2.12` üzrə fəaliyyətlərin dövlət payları). Fayl: `FR4_e8_structural_candidates.csv`.

| spesifikasiya | seçim RMSE, % | DM p (trendə qarşı) | yoxlama U (TG) | U (SA) | qərar |
|---|---|---|---|---|---|
| trend (E8, istifadə olunur) | 2,73 | — | 0,60 | 0,81 | istifadə olunur |
| C tərkib modeli (fəaliyyətlər üzrə dövlət payları) | 5,15 | 0,162 | 1,50 | 2,05 | rədd edildi |
| G3 adambaşına real qeyri-neft ÜDM | 6,11 | 0,315 | 1,23 | 1,68 | rədd edildi |
| G1 adambaşına real dövlət istehlakı | 6,97 | 0,305 | 0,96 | 1,31 | rədd edildi |
| G2 dövlət istehlakı / qeyri-neft ÜDM | 10,35 | 0,129 | 1,07 | 1,46 | rədd edildi |

**Heç biri trendi üstələmir**; fiskal və buraxılış sürücüləri səviyyədə mənfi işarəlidir və fərq formasında əhəmiyyətsizdir, tərkib
modeli isə fəaliyyətlər daxilində özəlləşdirməni tutmur. E8 siyasət rıçağı kimi logistik trend olaraq qalır; üç reqressiya
`FR4.E8_alt_G1–G3` kimi reyestrdədir (rədd edilib).

**Büdcə təşkilatları (σ).** `Dynamics_2.12` vərəqi (2005–2024) σ-nı hər il üçün verir (0,9586 — 2005, 0,9092 — 2024);
2005–2022 tarixi artıq doldurulmuş deyil. 2010–2019 başlanğıclarında son dərc olunmuş il iki ilin ortasından dəqiqdir (RMSE
1,46% və 1,59%): **σ = 0,9092** (əvvəl 0,913). Əsas ssenaridə büdcə məşğulluğu 2030-da 579,5 min
(əvvəl 579,5, 0,00%); dövlət məşğulluğu dəyişmir.

**Sahə məşğulluğu.** 19 fəaliyyət artıq 1999–2024-ü əhatə edir; makro modul daha uzun tarix vermir, tənliklər dəyişmir.
<!-- /AUTO:fr4v22_note -->

<!-- AUTO:fr4v23_note -->
## 18. v2.3 (2026-10-05) — düzəliş əmsallarının sabit yarımsönmə dövrü ilə sönməsi (qalıq AR qiymətləndirilmir)

Müştərinin tələbi qiymətləndirilmiş qalıq-AR prosesini istisna edir. v2.2-yə qədər Hissə 18-in "düzəliş əmsallarının sönməsi"
həssaslıq variantında E6 (blok bölgüsü) və E8 (dövlət payı) düzəlişləri hər tənliyin qiymətləndirilmiş birinci tərtib qalıq
avtokorrelyasiyası ρ̂ sürəti ilə sönürdü (E6 məşğul 0,85, muzdlu 0,63; E8 0,52). v2.3-dən sönmə **sabitdir,
qiymətləndirilmir**: düzəliş 0,5^(h/H) ilə vurulur (h — lövbər ilindən, 2024, sonrakı illər), yarımsönmə dövrü **H = 1 il**
(ildə 0,50) — FR1 və FR3-dəki kimi layihənin natamam il qaydası. H mühərrikdə rıçaqdır (`addfactor_half_life`, 0,25–10 il;
yalnız `addfactor_decay` açıq olduqda təsir edir). ρ̂ yalnız diaqnostika kimi (DW və BG ilə yanaşı) göstərilir, heç bir proqnoz,
ssenari və ya həssaslıq yolunda istifadə olunmur; `FR4_add_factors.csv` ρ̂ əvəzinə yarımsönmə dövrünü və illik əmsalı verir.
Əsas, Mənfi və İslahat ssenariləri sabit düzəlişlərlə qalır və dəyişmir. Sönmə həssaslığı, 2030, Əsas ssenariyə nisbətən (min nəfər):

| kəmiyyət | v2.2: ρ̂ ilə sönmə | v2.3: yarımsönmə 1 il |
|---|---|---|
| dövlət sektorunda məşğulluq | +14,2 (+1,44%) | +14,3 (+1,45%) |
| büdcə təşkilatları | +4,5 (+0,79%) | +4,7 (+0,81%) |
| bazar xidmətləri | −11,4 (−2,09%) | −17,8 (−3,26%) |
| xidmətlər (cəmi) | 0,0 (0,00%) | 0,0 (0,00%) |

Sabit sönmə ρ̂-dən sürətlidir: 2030-a qədər E6-nın 2024 düzəlişinin daha çox hissəsi aradan qalxır və bazar xidmətləri daha çox dəyişir; dövlət payına təsir az dəyişir (E8-in ρ̂-su 0,5-ə yaxın idi).
<!-- /AUTO:fr4v23_note -->
