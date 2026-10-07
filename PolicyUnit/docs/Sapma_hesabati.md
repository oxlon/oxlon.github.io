# Sapma hesabatı — təsir analizi modellərinin retrospektiv validasiyası (NFR1, MİİS §15.5.4)

*Avtomatik yaradılıb: `python3 -m policyunit.validate` (2026-10-07T01:57:22). Bütün rəqəmlər `output/V_nfr1_*.csv` fayllarındandır; bu sənəd əl ilə redaktə edilmir.*

## 1. Qəbul meyarı və xülasə

TT qəbul meyarı: «Model nəticələri ən azı 2 tarixi siyasət hadisəsi üzərində sınaqdan keçirilir və sapma hesabatı sənədləşdirilir». **Status: 4 hadisə, 45 proqnoz–fakt müqayisəsi, 7 metod — meyar yerinə yetirilib.** Meyar prosedurdur (sınaq + sənəd); hökmlər aşağıdakı təklif olunan tolerantlıq qaydası ilə verilir.

| Hadisə | Tarix | Nümunə | Metodlar | ≥2 metodlu göstərici (NFR2) | Həlledici / cəmi (əsas) | Uyğun / qismən / uyğunsuz (həlledicilər) | Hökm |
|---|---|---|---|---|---|---|---|
| E1. 2019 sosial paketi (minimum əmək haqqı + vergi islahatı) | 01.01.2019 (vergi), 01.03/01.09.2019 (minimum əmək haqqı) | daxili/kənar | 4 | 3 (bəli) | 9 / 12 (6) | 33 / 11 / 56 % | **keçmədi** |
| E3. Minimum əmək haqqının artımları 2022, 2023 və 2025 (2024 — plasebo) | 01.01.2022 (250 → 300), 01.01.2023 (300 → 345), 01.01.2025 (345 → 400); 2024 dəyişməyib | daxili/kənar | 4 | 8 (bəli) | 15 / 20 (9) | 53 / 47 / 0 % | **şərti keçdi** |
| E5. 2015 devalvasiyaları (21.02.2015 və 21.12.2015) | 21.02.2015 (0,78 → 1,05 AZN/USD), 21.12.2015 (üzən məzənnə) | daxili/kənar | 2 | 1 (bəli) | 4 / 6 (3) | 0 / 75 / 25 % | **keçmədi** |
| E7. Yanacaq qiyməti və nəqliyyat tarifləri paketi (30.06.2024) | 01.07.2024 (Tarif Şurası, 30.06.2024) | kənar | 3 | 1 (bəli) | 4 / 7 (1) | 0 / 75 / 25 % | **şərti keçdi** |

Metodlar üzrə (bütün hadisələr):

| Metod | Müqayisə (həlledici) | Hadisələr | Orta bal | İstiqamət uyğunluğu | Median % sapma | Orta sapma (işarəli) | Sadə etalondan yaxşı |
|---|---|---|---|---|---|---|---|
| MikroUnit FR1 E2 tənliyi (birbaşa, qismən tarazlıq) | 5 (3) | E1;E3 | 2,00 | 100 % | 30 | −0,19 | 80 % |
| MikroUnit struktur zənciri (köçürülmüş şok) | 21 (14) | E1;E3;E5;E7 | 1,21 | 100 % | 44 | −0,57 | 81 % |
| Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK) | 7 (5) | E1;E3 | 0,80 | 100 % | 74 | −3,50 | 57 % |
| MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa) | 5 (5) | E1;E3 | 1,20 | 100 % | 73 | +2,93 | 60 % |
| IO qiymət modeli (Leontief, tam ötürmə) | 1 (1) | E5 | 0,00 | 100 % | 108 | +26,61 | 0 % |
| IO qiymət modeli — E7 xüsusi şoku (IO agenti) | 5 (4) | E7 | 0,75 | 100 % | 44 | −1,58 | 80 % |
| Nazirlik CAEM modeli — müqayisə | 1 (0) | E7 | — | — % | 88 | −2,41 | 0 % |

## 2. Metodologiya

### 2.1 Əks-faktual (baza ilə müqayisə)

- `pre2` — hadisədən əvvəlki 2 ilin ortası (o vaxtkı informasiya dəsti)
- `pre1` — hadisədən əvvəlki il (təsadüfi gəzinti)
- `trend2` — son 2 ilin xətti trendi
- `zero` — sıfır (sadə fərq)
- `flat10` — son 10 ildə minimum əmək haqqının dəyişmədiyi illərdə dövlət − qeyri-dövlət fərqinin ortası (DiD paralel trend)
- `file` — IO/mikrosimulyasiya agentinin faylındakı əks-faktual (tənzimlənən qiymət: 0; bazar maddəsi: 2023 artımı; siyasətsiz paylanma)

Hər göstərici üçün əsas və alternativ qayda verilir (sinif hər ikisi ilə hesablanır). σ əks-faktual — eyni qaydanın hadisədən əvvəlki 10 ildə «psevdo-hadisələr» üzrə xətasının 1,4826 × median |xəta| ölçüsü (sürüşmə daxil); DiD üçün minimum əmək haqqının dəyişmədiyi illərdə fərqin standart kənarlaşması.

### 2.2 Model proqnozları

- **MikroUnit struktur zənciri (köçürülmüş şok)** (`micro_chain`)
- **MikroUnit FR1 E2 tənliyi (birbaşa, qismən tarazlıq)** (`e2_direct`)
- **MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa)** (`fr3_direct`)
- **IO qiymət modeli (Leontief, tam ötürmə)** (`io_price`)
- **IO qiymət modeli — E7 xüsusi şoku (IO agenti)** (`io_e7`)
- **Nazirlik CAEM modeli — müqayisə** (`caem`)
- **Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK)** (`microsim`)

MikroUnit zənciri: hadisənin alət yolu məlumatdan qurulur (illik orta minimum əmək haqqı — DSK 004_1; AMB rəsmi orta məzənnəsi; IO E7 yanacaq şoku) və cari zəncirə köçürülür; təsir = ssenari − eyni vintajın bazası.

### 2.3 Metriklər

sapma = proqnoz − fakt (təsir); % sapma = |sapma| / |fakt|; istiqamət (işarə) uyğunluğu; fakt model intervalındadırmı (ayrıca, tolerantlığa əlavə edilmir); fakt model intervalı ± 1,96·σ əks-faktual daxilindədirmi; model qeyri-trivial sadə etalondan yaxşıdırmı:

- `prev` — əvvəlki ilin nəticəsi təkrarlanır (təsadüfi gəzinti)
- `prev_d` — əvvəlki ilin dəyişməsi təkrarlanır
- `shock` — tam mexaniki ötürmə (tənzimlənən qiymət dəyişməsi = maddə qiyməti)
- `const` — tam mexaniki ötürmə (siyasət ölçüsü)
- `io_direct` — yalnız birbaşa mexaniki ötürmə (İQİ çəkisi × tənzimlənən qiymət, dolayı təsirsiz)
- `zero` — sıfır təsir (trivial)

### 2.4 Tolerantlıq qaydası — TƏKLİF (Nazirlik hədd müəyyən etməyib)

| Parametr | Dəyər | Qayda | Status |
|---|---|---|---|
| rel_ok | 0,25 | «uyğun»: \|sapma\| ≤ max(rel_ok·\|fakt\|, min(sig_ok·σ_əf, cap_ok·\|fakt\|)) | TƏKLİF — Nazirliklə razılaşdırılmalıdır |
| cap_ok | 0,35 | əks-faktual səs-küyü tolerantlığı ən çox cap_ok·\|fakt\|-a qədər genişləndirir | TƏKLİF — Nazirliklə razılaşdırılmalıdır |
| sig_ok | 1,00 | σ_əf — yalnız əks-faktualın səs-küyü; model intervalı ayrıca göstərilir (toplanmır) | TƏKLİF — Nazirliklə razılaşdırılmalıdır |
| rel_part | 0,50 | «qismən uyğun»: \|sapma\| ≤ max(rel_part·\|fakt\|, min(sig_part·σ_əf, cap_part·\|fakt\|)) | TƏKLİF — Nazirliklə razılaşdırılmalıdır |
| cap_part | 0,75 | qismən uyğunluq üçün yuxarı hədd | TƏKLİF — Nazirliklə razılaşdırılmalıdır |
| sig_part | 2,00 | əks halda «uyğunsuz»; istiqamət səhvdirsə həmişə «uyğunsuz» | TƏKLİF — Nazirliklə razılaşdırılmalıdır |
| naive_required | True | sadə etalonu (əvvəlki ilin nəticəsi / tam mexaniki ötürmə) üstələməyən müqayisə ən çox «qismən uyğun» | TƏKLİF — Nazirliklə razılaşdırılmalıdır |
| min_decisive | 2,00 | «keçdi» üçün ən azı bu qədər həlledici əsas müqayisə; az olduqda ən çox «şərti keçdi» | TƏKLİF — Nazirliklə razılaşdırılmalıdır |
| ident_sigma | 1,00 | \|fakt\| < ident_sigma·σ_əf → təsir müəyyən edilmir (aşağı güc); yalnız 2σ_əf-dən böyük səhv həlledicidir | TƏKLİF — Nazirliklə razılaşdırılmalıdır |

Hadisə hökmü — əsas göstəricilər üzrə həlledici müqayisələrin orta balı: ≥ 1,50 «keçdi», ≥ 0,75 «şərti keçdi», əks halda «keçmədi». Aşağı güclü müqayisələr hökmə daxil edilmir, plasebo sətirləri isə |sapma| ≤ σ_əf olduqda «uyğun» sayılır; «keçdi» üçün ən azı 2 həlledici əsas müqayisə tələb olunur.

### 2.5 Hökmlərin tolerantlıq seçiminə həssaslığı

| Hadisə | qatı | təklif | yumşaq (v1: σ_model+σ_əf, limitsiz) |
|---|---|---|---|
| E1 | keçmədi (0,50; 2/2/5) | keçmədi (0,50; 3/1/5) | şərti keçdi (1,00; 3/5/1) |
| E3 | şərti keçdi (1,22; 6/6/3) | şərti keçdi (1,44; 8/7/0) | keçdi (1,89; 12/3/0) |
| E5 | keçmədi (0,67; 0/2/2) | keçmədi (0,67; 0/3/1) | keçdi (1,67; 2/2/0) |
| E7 | şərti keçdi (1,00; 0/1/3) | şərti keçdi (1,00; 0/3/1) | keçdi (2,00; 1/2/1) |

Xanada: hökm (əsas balı; uyğun/qismən/uyğunsuz sayı). Parametrlər:

- **qatı**: rel_ok=0.15, cap_ok=0.2, sig_ok=1.0, rel_part=0.35, cap_part=0.5, sig_part=2.0, sigma=cf, naive_required=True, min_decisive=2
- **təklif**: rel_ok=0.25, cap_ok=0.35, sig_ok=1.0, rel_part=0.5, cap_part=0.75, sig_part=2.0, sigma=cf, naive_required=True, min_decisive=2
- **yumşaq (v1: σ_model+σ_əf, limitsiz)**: rel_ok=0.3, cap_ok=1000000000.0, sig_ok=1.0, rel_part=0.6, cap_part=1000000000.0, sig_part=2.0, sigma=total, naive_required=False, min_decisive=1

«Keçdi» hökmlərinin sayı: qatı — 0, təklif — 0, yumşaq (v1: σ_model+σ_əf, limitsiz) — 3 (cəmi 4 hadisə). Nazirlik qaydanı təsdiqləyənə qədər «təklif» sütunu əsasdır; yumşaq qayda bu hesabatın ilk versiyasında istifadə edilmişdi.

## 3. Hadisələr

### E1. 2019 sosial paketi (minimum əmək haqqı + vergi islahatı)

- **Siyasət:** Minimum əmək haqqı 130 → 180 (01.03.2019) → 250 AZN (01.09.2019); illik orta MikroUnit DSK 004_1 fərman faylından hesablanır; minimum pensiya 116 → 160 → 200 AZN; qeyri-neft özəl sektorda ≤8000 AZN gəlir vergisindən azadolma (7 il); büdcə maaşlarının artımı; problemli kreditlər üzrə kompensasiya
- **Tarix:** 01.01.2019 (vergi), 01.03/01.09.2019 (minimum əmək haqqı); **hüquqi əsas:** Prezidentin Sərəncamları və Fərmanları (2019); Vergi Məcəlləsinə dəyişikliklər (20.12.2018)
- **Nümunə statusu:** nümunədaxili / nümunədən kənar — FR1 E2 (2002–2024) və FR3 E4 (DOLS) 2019-u əhatə edən tam nümunə üzrə qiymətləndirilib — test nümunədaxilidir (in-sample); hadisədən əvvəlki məlumatla yenidən qiymətləndirmə aparılmayıb
- **Modellər:** MikroUnit FR1 E2 tənliyi (birbaşa, qismən tarazlıq); MikroUnit struktur zənciri (köçürülmüş şok); Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK); MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa)
- **Ötürmə mexanizmi və qarışıqlıq:** Minimum əmək haqqı FR1 E2 (orta maaş), FR3 E4 (dövlət sektoru maaşı) və G4 (maaş → İQİ) tənlikləri ilə ötürülür; mikrosimulyasiya statik ilk dövrə qaydalarını və formallaşma üçün davranış qatını tətbiq edir. Vergi islahatının formallaşma (bəyan edilən maaş və muzdlu məşğulluq) kanalı MikroUnit zəncirində yoxdur; büdcə maaşlarının ayrıca artımı modelləşdirilməyib — dövlət sektoru üzrə fakt həm də bu artımları ehtiva edir.

**Məlumat və əks-faktual:**

| Göstərici | İl | Fakt | Əks-faktual (qayda) | Müşahidə olunan təsir | σ əks-faktual (n) | Mənbə |
|---|---|---|---|---|---|---|
| Orta aylıq nominal əmək haqqının artımı | 2019 | 16,62 | 4,39 (pre2) | 12,22 | 3,83 (10) | DSK cədvəl 4.5–4.8 (MikroUnit fr345 paneli) — büdcə maaşları və vergi islahatı ilə qarışıq (formallaşma — bəyan edilən maaşın artımı) |
| Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) | 2019 | 10,86 | −1,17 (flat10) | 12,04 | 5,87 (5) | DSK cədvəl 4.5–4.8 — nəzarət qrupu: qeyri-dövlət sektoru; dövlət sektorunda əlavə büdcə maaşı artımları var |
| İQİ inflyasiyası (illik orta) | 2019 | 2,60 | 2,30 (pre1) | 0,30 | 5,04 (10) | DSK (Macro_OxLon macro_annual.csv) — 2017-dən sonra devalvasiya ötürülməsi bitib — əks-faktual: 2018-ci ilin inflyasiyası |
| Qeyri-dövlət sektorunda muzdlu işçilərin artımı | 2019 | 9,45 | 3,46 (pre2) | 5,99 | 4,50 (10) | DSK cədvəl 2.12 — vergi islahatı ilə formallaşma (E2) — MikroUnit-də bu kanal yoxdur |
| Real orta əmək haqqının artımı | 2019 | 13,66 | −2,81 (pre2) | 16,47 | 6,49 (10) | DSK 4.5–4.8 / İQİ — nominal maaş / İQİ (illik orta) |
| Real qeyri-neft ÜDM artımı | 2019 | 3,96 | 2,42 (pre2) | 1,54 | 9,31 (4) | DSK milli hesablar (macro_annual.csv) — ilkin dərc: fərqli ola bilər (vintaj yoxdur, yenidən işlənmiş dəyər) |
| Yoxsulluq səviyyəsi (rəsmi xətt) | 2019 | 4,80 | 5,10 (pre1) | −0,30 | 1,26 (10) | DSK yoxsulluq cədvəli (poverty_line_rate.csv) — əhalinin ehtiyac meyarı xətti üzrə; mikrosimulyasiya 2018 sintetik bazası ilə |

**Proqnoz və fakt:**

| Göstərici | İl | Metod | Proqnoz [interval] | Fakt (təsir) | Sapma | % sapma | İstiqamət | İntervalda | Sadə etalon (qayda) | Etalondan yaxşı | Güc | Nümunə | Sinif | Alt. əks-faktual |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Orta aylıq nominal əmək haqqının artımı** | 2019 | MikroUnit FR1 E2 tənliyi (birbaşa, qismən tarazlıq) | 11,68 — | 12,22 | −0,54 | 4 | bəli | — | −1,35 (prev) | bəli | yüksək | daxili | **uyğun** | uyğun |
| **Orta aylıq nominal əmək haqqının artımı** | 2019 | MikroUnit struktur zənciri (köçürülmüş şok) | 16,43 — | 12,22 | +4,21 | 34 | bəli | — | −1,35 (prev) | bəli | yüksək | daxili | **qismən uyğun** | uyğun |
| **Orta aylıq nominal əmək haqqının artımı** | 2019 | Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK) | 0,49 — | 12,22 | −11,74 | 96 | bəli | — | −1,35 (prev) | bəli | yüksək | kənar | **uyğunsuz** | uyğunsuz |
| **Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD)** | 2019 | MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa) | 27,87 [15,8; 41,2] | 12,04 | +15,83 | 132 | bəli | xeyr | 14,17 (prev) | xeyr | yüksək | daxili | **uyğunsuz** | uyğunsuz |
| **Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD)** | 2019 | MikroUnit struktur zənciri (köçürülmüş şok) | 23,98 [14,3; 33,6] | 12,04 | +11,95 | 99 | bəli | xeyr | 14,17 (prev) | xeyr | yüksək | daxili | **uyğunsuz** | uyğunsuz |
| **Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD)** | 2019 | Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK) | 1,07 — | 12,04 | −10,97 | 91 | bəli | — | 14,17 (prev) | xeyr | yüksək | kənar | **uyğunsuz** | uyğunsuz |
| **İQİ inflyasiyası (illik orta)** | 2019 | MikroUnit struktur zənciri (köçürülmüş şok) | 5,27 [0,0; 10,5] | 0,30 | +4,97 | 1 657 | — | bəli | −10,60 (prev_d) | bəli | aşağı | daxili | müəyyən deyil (aşağı güc) | uyğunsuz |
| Qeyri-dövlət sektorunda muzdlu işçilərin artımı | 2019 | MikroUnit struktur zənciri (köçürülmüş şok) | 0,08 — | 5,99 | −5,91 | 99 | bəli | — | −0,27 (prev) | bəli | orta | daxili | **uyğunsuz** | uyğunsuz |
| Qeyri-dövlət sektorunda muzdlu işçilərin artımı | 2019 | Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK) | 5,92 — | 5,99 | −0,07 | 1 | bəli | — | −0,27 (prev) | bəli | orta | kənar | **uyğun** | uyğun |
| Real orta əmək haqqının artımı | 2019 | MikroUnit struktur zənciri (köçürülmüş şok) | 10,92 [0,1; 21,8] | 16,47 | −5,55 | 34 | bəli | bəli | 3,53 (prev) | bəli | yüksək | daxili | **uyğun** | uyğun |
| Real qeyri-neft ÜDM artımı | 2019 | MikroUnit struktur zənciri (köçürülmüş şok) | 2,48 [0,5; 4,5] | 1,54 | +0,95 | 61 | — | bəli | −0,42 (prev) | bəli | aşağı | daxili | müəyyən deyil (aşağı güc) | müəyyən deyil (aşağı güc) |
| **Yoxsulluq səviyyəsi (rəsmi xətt)** | 2019 | Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK) | −0,86 — | −0,30 | −0,56 | 188 | — | — | −0,30 (prev_d) | xeyr | aşağı | kənar | müəyyən deyil (aşağı güc) | müəyyən deyil (aşağı güc) |

**Sapmalar və izah (əsas göstəricilər):**

- Orta aylıq nominal əmək haqqının artımı (2019, MikroUnit FR1 E2 tənliyi (birbaşa, qismən tarazlıq)): proqnoz 11,7, fakt 12,2 — model təsiri 4 % az qiymətləndirir (sapma −0,5); sinif: uyğun; alternativ əks-faktualla: uyğun.
- Orta aylıq nominal əmək haqqının artımı (2019, MikroUnit struktur zənciri (köçürülmüş şok)): proqnoz 16,4, fakt 12,2 — model təsiri 34 % artıq qiymətləndirir (sapma +4,2); sinif: qismən uyğun; alternativ əks-faktualla: uyğun.
- Orta aylıq nominal əmək haqqının artımı (2019, Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK)): proqnoz 0,5, fakt 12,2 — model təsiri 96 % az qiymətləndirir (sapma −11,7); sinif: uyğunsuz; alternativ əks-faktualla: uyğunsuz.
- Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) (2019, MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa)): proqnoz 27,9, fakt 12,0 — model təsiri 132 % artıq qiymətləndirir (sapma +15,8); sinif: uyğunsuz; alternativ əks-faktualla: uyğunsuz.
- Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) (2019, MikroUnit struktur zənciri (köçürülmüş şok)): proqnoz 24,0, fakt 12,0 — model təsiri 99 % artıq qiymətləndirir (sapma +11,9); sinif: uyğunsuz; alternativ əks-faktualla: uyğunsuz.
- Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) (2019, Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK)): proqnoz 1,1, fakt 12,0 — model təsiri 91 % az qiymətləndirir (sapma −11,0); sinif: uyğunsuz; alternativ əks-faktualla: uyğunsuz.
- İQİ inflyasiyası (illik orta) (2019, MikroUnit struktur zənciri (köçürülmüş şok)): müşahidə olunan təsir 0,3 əks-faktualın səs-küyündən (σ = 5,0) kiçikdir — test aşağı güclüdür; proqnoz 5,3, sapma +5,0.
- Yoxsulluq səviyyəsi (rəsmi xətt) (2019, Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK)): müşahidə olunan təsir −0,3 əks-faktualın səs-küyündən (σ = 1,3) kiçikdir — test aşağı güclüdür; proqnoz −0,9, sapma −0,6.

**Hökm:** keçmədi — əsas göstəricilər üzrə həlledici müqayisələrin orta balı 0,50 (2 = uyğun, 1 = qismən, 0 = uyğunsuz); həlledici müqayisələr: 9 / 12; istiqamət uyğunluğu 100 %; sadə etalondan yaxşı: 67 %. Nümunədaxili müqayisələr struktur uyğunluğu göstərir, proqnoz gücünü yox.

### E3. Minimum əmək haqqının artımları 2022, 2023 və 2025 (2024 — plasebo)

- **Siyasət:** Minimum əmək haqqı 250 → 300 (+20 %) → 345 (+15 %) → 400 AZN (+15,9 %, 2025); 2024-də artım yoxdur
- **Tarix:** 01.01.2022 (250 → 300), 01.01.2023 (300 → 345), 01.01.2025 (345 → 400); 2024 dəyişməyib; **hüquqi əsas:** Prezident Fərmanları (2021, 2022, 23.12.2024)
- **Nümunə statusu:** nümunədaxili / nümunədən kənar — FR1 E2 və FR3 E4 2022–2024-ü əhatə edən tam nümunə üzrə qiymətləndirilib — nümunədaxili; 2024 dəyişməyən il kimi plasebo testidir; NÜMUNƏDƏN KƏNAR: 2025 FR1 E2 (2002–2024) qiymətləndirmə nümunəsinə daxil deyil; 2025 məlumatı ilkin ola bilər
- **Modellər:** MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa); MikroUnit struktur zənciri (köçürülmüş şok); MikroUnit FR1 E2 tənliyi (birbaşa, qismən tarazlıq); Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK)
- **Ötürmə mexanizmi və qarışıqlıq:** Eyni kanallar; 2024 minimum əmək haqqının dəyişmədiyi ildir (plasebo: gözlənilən siyasət təsiri sıfırdır). 2022-də qlobal inflyasiya şoku və büdcə təşkilatlarında əlavə maaş artımları ilə qarışıqlıq var. 2025 sətirləri E2-nin qiymətləndirmə nümunəsindən kənardır (yeganə həqiqi nümunədən kənar makro yoxlama).

**Məlumat və əks-faktual:**

| Göstərici | İl | Fakt | Əks-faktual (qayda) | Müşahidə olunan təsir | σ əks-faktual (n) | Mənbə |
|---|---|---|---|---|---|---|
| Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) | 2022 | 13,64 | −2,40 (flat10) | 16,03 | 4,09 (5) | DSK cədvəl 4.5–4.8 — 2022-də büdcə təşkilatlarında əlavə maaş artımları — qarışıq |
| Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) | 2023 | 4,95 | −2,40 (flat10) | 7,35 | 4,09 (5) | DSK cədvəl 4.5–4.8 |
| Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) — plasebo | 2024 | −0,10 | −2,40 (flat10) | 2,30 | 4,09 (5) | DSK cədvəl 4.5–4.8 — plasebo: minimum əmək haqqı dəyişməyib, gözlənilən təsir ≈ 0 |
| Orta aylıq nominal əmək haqqının artımı | 2022 | 14,74 | 7,44 (pre2) | 7,30 | 3,83 (10) | DSK cədvəl 4.5–4.8 — qlobal inflyasiya şoku (İQİ 13,9 %) ilə qarışıq |
| Orta aylıq nominal əmək haqqının artımı | 2023 | 11,18 | 7,44 (pre2) | 3,74 | 5,71 (9) | DSK cədvəl 4.5–4.8 |
| Orta aylıq nominal əmək haqqının artımı — plasebo | 2024 | 8,08 | 7,44 (pre2) | 0,64 | 4,70 (8) | DSK cədvəl 4.5–4.8 — plasebo ili |
| İQİ inflyasiyası (illik orta) | 2022 | 13,90 | 4,73 (pre2) | 9,17 | 6,46 (10) | DSK (macro_annual.csv) — qlobal ərzaq/enerji şoku — siyasət təsirini ayırmaq mümkün deyil (yalnız informativ) |
| Orta aylıq nominal əmək haqqının artımı | 2025 | 9,26 | 7,44 (pre2) | 1,82 | 4,37 (7) | DSK (MikroUnit FR1_annual_raw.csv) — 2025 — ilkin illik məlumat |
| Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) | 2025 | 3,03 | −2,40 (flat10) | 5,43 | 4,09 (5) | DSK (MikroUnit FR1_annual_raw.csv) — 2025 — ilkin illik məlumat |
| Muzdlu işçilərin payı, maaşı < 500 AZN (noyabr 2025) | 2025 | 25,82 | 37,83 (file) | −12,01 | — (0) | DSK maaş qrupları (mikrosimulyasiya agentinin V_microsim_2025_minwage.csv) — əks-faktual: 2024 paylanmasının siyasətsiz yenilənməsi (naive) |
| Muzdlu işçilərin payı, maaşı < 600 AZN (noyabr 2025) | 2025 | 40,92 | 47,82 (file) | −6,90 | — (0) | DSK maaş qrupları (V_microsim_2025_minwage.csv) |

**Proqnoz və fakt:**

| Göstərici | İl | Metod | Proqnoz [interval] | Fakt (təsir) | Sapma | % sapma | İstiqamət | İntervalda | Sadə etalon (qayda) | Etalondan yaxşı | Güc | Nümunə | Sinif | Alt. əks-faktual |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD)** | 2022 | MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa) | 11,69 [6,8; 16,8] | 16,03 | −4,35 | 27 | bəli | bəli | 3,32 (prev) | bəli | yüksək | daxili | **qismən uyğun** | uyğun |
| **Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD)** | 2022 | MikroUnit struktur zənciri (köçürülmüş şok) | 11,05 [6,6; 15,5] | 16,03 | −4,99 | 31 | bəli | xeyr | 3,32 (prev) | bəli | yüksək | daxili | **qismən uyğun** | uyğun |
| **Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD)** | 2023 | MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa) | 8,84 [5,2; 12,6] | 7,35 | +1,49 | 20 | bəli | bəli | 16,03 (prev) | bəli | orta | daxili | **uyğun** | uyğunsuz |
| **Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD)** | 2023 | MikroUnit struktur zənciri (köçürülmüş şok) | 7,81 [4,7; 10,9] | 7,35 | +0,46 | 6 | bəli | bəli | 16,03 (prev) | bəli | orta | daxili | **uyğun** | qismən uyğun |
| **Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) — plasebo** | 2024 | MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa) | 0,00 [0,0; 0,0] | 2,30 | −2,30 | 100 | — | xeyr | 7,35 (prev) | bəli | aşağı | daxili | **uyğun** | uyğun |
| **Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) — plasebo** | 2024 | MikroUnit struktur zənciri (köçürülmüş şok) | 0,52 [0,3; 0,7] | 2,30 | −1,78 | 77 | — | xeyr | 7,35 (prev) | bəli | aşağı | daxili | **uyğun** | uyğun |
| Orta aylıq nominal əmək haqqının artımı | 2022 | MikroUnit FR1 E2 tənliyi (birbaşa, qismən tarazlıq) | 5,09 — | 7,30 | −2,21 | 30 | bəli | — | −3,99 (prev) | bəli | orta | daxili | **uyğun** | qismən uyğun |
| Orta aylıq nominal əmək haqqının artımı | 2022 | MikroUnit struktur zənciri (köçürülmüş şok) | 7,07 — | 7,30 | −0,23 | 3 | bəli | — | −3,99 (prev) | bəli | orta | daxili | **uyğun** | qismən uyğun |
| Orta aylıq nominal əmək haqqının artımı | 2023 | MikroUnit FR1 E2 tənliyi (birbaşa, qismən tarazlıq) | 3,88 — | 3,74 | +0,14 | 4 | — | — | 7,30 (prev) | bəli | aşağı | daxili | müəyyən deyil (aşağı güc) | qismən uyğun |
| Orta aylıq nominal əmək haqqının artımı | 2023 | MikroUnit struktur zənciri (köçürülmüş şok) | 5,40 — | 3,74 | +1,66 | 44 | — | — | 7,30 (prev) | bəli | aşağı | daxili | müəyyən deyil (aşağı güc) | qismən uyğun |
| Orta aylıq nominal əmək haqqının artımı — plasebo | 2024 | MikroUnit FR1 E2 tənliyi (birbaşa, qismən tarazlıq) | 0,00 — | 0,64 | −0,64 | 100 | — | — | 3,74 (prev) | bəli | aşağı | daxili | **uyğun** | müəyyən deyil (aşağı güc) |
| Orta aylıq nominal əmək haqqının artımı — plasebo | 2024 | MikroUnit struktur zənciri (köçürülmüş şok) | −0,01 — | 0,64 | −0,65 | 102 | — | — | 3,74 (prev) | bəli | aşağı | daxili | **uyğun** | müəyyən deyil (aşağı güc) |
| İQİ inflyasiyası (illik orta) | 2022 | MikroUnit struktur zənciri (köçürülmüş şok) | 2,37 [0,0; 4,7] | 9,17 | −6,80 | 74 | bəli | xeyr | 1,97 (prev) | bəli | orta | daxili | **qismən uyğun** | qismən uyğun |
| **Orta aylıq nominal əmək haqqının artımı** | 2025 | MikroUnit FR1 E2 tənliyi (birbaşa, qismən tarazlıq) | 4,11 — | 1,82 | +2,29 | 126 | — | — | 0,64 (prev) | xeyr | aşağı | kənar | müəyyən deyil (aşağı güc) | uyğun |
| **Orta aylıq nominal əmək haqqının artımı** | 2025 | MikroUnit struktur zənciri (köçürülmüş şok) | 5,81 — | 1,82 | +3,98 | 218 | — | — | 0,64 (prev) | xeyr | aşağı | kənar | müəyyən deyil (aşağı güc) | uyğun |
| **Orta aylıq nominal əmək haqqının artımı** | 2025 | Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK) | 0,47 — | 1,82 | −1,35 | 74 | — | — | 0,64 (prev) | xeyr | aşağı | kənar | müəyyən deyil (aşağı güc) | uyğunsuz |
| **Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD)** | 2025 | MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa) | 9,38 [5,5; 13,4] | 5,43 | +3,96 | 73 | bəli | xeyr | 2,30 (prev) | xeyr | orta | kənar | **qismən uyğun** | müəyyən deyil (aşağı güc) |
| **Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD)** | 2025 | MikroUnit struktur zənciri (köçürülmüş şok) | 7,50 [4,5; 10,5] | 5,43 | +2,07 | 38 | bəli | bəli | 2,30 (prev) | bəli | orta | kənar | **qismən uyğun** | müəyyən deyil (aşağı güc) |
| **Muzdlu işçilərin payı, maaşı < 500 AZN (noyabr 2025)** | 2025 | Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK) | −8,79 — | −12,01 | +3,22 | 27 | bəli | — | 0,00 (zero) | bəli | yüksək | kənar | **qismən uyğun** | — |
| Muzdlu işçilərin payı, maaşı < 600 AZN (noyabr 2025) | 2025 | Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK) | −9,94 — | −6,90 | −3,04 | 44 | bəli | — | 0,00 (zero) | bəli | yüksək | kənar | **qismən uyğun** | — |

**Sapmalar və izah (əsas göstəricilər):**

- Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) (2022, MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa)): proqnoz 11,7, fakt 16,0 — model təsiri 27 % az qiymətləndirir (sapma −4,3); sinif: qismən uyğun; alternativ əks-faktualla: uyğun.
- Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) (2022, MikroUnit struktur zənciri (köçürülmüş şok)): proqnoz 11,0, fakt 16,0 — model təsiri 31 % az qiymətləndirir (sapma −5,0); sinif: qismən uyğun; alternativ əks-faktualla: uyğun.
- Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) (2023, MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa)): proqnoz 8,8, fakt 7,3 — model təsiri 20 % artıq qiymətləndirir (sapma +1,5); sinif: uyğun; alternativ əks-faktualla: uyğunsuz.
- Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) (2023, MikroUnit struktur zənciri (köçürülmüş şok)): proqnoz 7,8, fakt 7,3 — model təsiri 6 % artıq qiymətləndirir (sapma +0,5); sinif: uyğun; alternativ əks-faktualla: qismən uyğun.
- Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) — plasebo (2024, MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa)): proqnoz 0,0, fakt 2,3 — model təsiri 100 % az qiymətləndirir (sapma −2,3); sinif: uyğun; alternativ əks-faktualla: uyğun.
- Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) — plasebo (2024, MikroUnit struktur zənciri (köçürülmüş şok)): proqnoz 0,5, fakt 2,3 — model təsiri 77 % az qiymətləndirir (sapma −1,8); sinif: uyğun; alternativ əks-faktualla: uyğun.
- Orta aylıq nominal əmək haqqının artımı (2025, MikroUnit FR1 E2 tənliyi (birbaşa, qismən tarazlıq)): müşahidə olunan təsir 1,8 əks-faktualın səs-küyündən (σ = 4,4) kiçikdir — test aşağı güclüdür; proqnoz 4,1, sapma +2,3.
- Orta aylıq nominal əmək haqqının artımı (2025, MikroUnit struktur zənciri (köçürülmüş şok)): müşahidə olunan təsir 1,8 əks-faktualın səs-küyündən (σ = 4,4) kiçikdir — test aşağı güclüdür; proqnoz 5,8, sapma +4,0.
- Orta aylıq nominal əmək haqqının artımı (2025, Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK)): müşahidə olunan təsir 1,8 əks-faktualın səs-küyündən (σ = 4,4) kiçikdir — test aşağı güclüdür; proqnoz 0,5, sapma −1,4.
- Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) (2025, MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa)): proqnoz 9,4, fakt 5,4 — model təsiri 73 % artıq qiymətləndirir (sapma +4,0); sinif: qismən uyğun; alternativ əks-faktualla: müəyyən deyil (aşağı güc).
- Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) (2025, MikroUnit struktur zənciri (köçürülmüş şok)): proqnoz 7,5, fakt 5,4 — model təsiri 38 % artıq qiymətləndirir (sapma +2,1); sinif: qismən uyğun; alternativ əks-faktualla: müəyyən deyil (aşağı güc).
- Muzdlu işçilərin payı, maaşı < 500 AZN (noyabr 2025) (2025, Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK)): proqnoz −8,8, fakt −12,0 — model təsiri 27 % artıq qiymətləndirir (sapma +3,2); sinif: qismən uyğun.

**Hökm:** şərti keçdi — əsas göstəricilər üzrə həlledici müqayisələrin orta balı 1,44 (2 = uyğun, 1 = qismən, 0 = uyğunsuz); həlledici müqayisələr: 15 / 20; istiqamət uyğunluğu 100 %; sadə etalondan yaxşı: 80 %. Nümunədaxili müqayisələr struktur uyğunluğu göstərir, proqnoz gücünü yox.

### E5. 2015 devalvasiyaları (21.02.2015 və 21.12.2015)

- **Siyasət:** Rəsmi orta məzənnə (AMB 2.16) 2014-cü il səviyyəsinə nisbətən: 2015, 2016, 2017 (illik orta) — dəyərlər məlumatdan hesablanır
- **Tarix:** 21.02.2015 (0,78 → 1,05 AZN/USD), 21.12.2015 (üzən məzənnə); **hüquqi əsas:** AMB qərarları (21.02.2015; 21.12.2015)
- **Nümunə statusu:** nümunədaxili / nümunədən kənar — NÜMUNƏDAXİLİ: FR1 G4 (2000–2025) və RiskUnit fx.py ötürmə əmsalı (0,30) məhz 2015–2017 epizoduna kalibrlənib; bu test model uyğunluğunu yoxlayır, proqnoz gücünü yox
- **Modellər:** MikroUnit struktur zənciri (köçürülmüş şok); IO qiymət modeli (Leontief, tam ötürmə)
- **Ötürmə mexanizmi və qarışıqlıq:** Məzənnə FR1 G4 tənliyində (cari və gecikmiş məzənnə dəyişməsi) inflyasiyaya, oradan real maaşa ötürülür; IO qiymət modeli idxal qiymətlərinin tam və dərhal ötürülməsini fərz edir (yuxarı hədd). Eyni dövrdə neft qiymətinin çöküşü baş verib — real göstəricilərdə siyasət təsirini ayırmaq mümkün deyil.

**Məlumat və əks-faktual:**

| Göstərici | İl | Fakt | Əks-faktual (qayda) | Müşahidə olunan təsir | σ əks-faktual (n) | Mənbə |
|---|---|---|---|---|---|---|
| İQİ inflyasiyası (illik orta) | 2015 | 4,00 | 1,90 (pre2) | 2,10 | 7,86 (10) | DSK (macro_annual.csv) — neft qiymətinin çöküşü ilə eyni vaxtda (əks-faktual: 2013–2014 ortası) |
| İQİ inflyasiyası (illik orta) | 2016 | 12,40 | 1,90 (pre2) | 10,50 | 6,52 (9) | DSK (macro_annual.csv) |
| İQİ inflyasiyası (illik orta) | 2017 | 12,90 | 1,90 (pre2) | 11,00 | 12,97 (8) | DSK (macro_annual.csv) |
| İQİ səviyyəsi — 2015–2017 kumulyativ artıq | 2017 | 31,98 | 5,81 (pre2) | 24,73 | 22,13 (8) | DSK (macro_annual.csv) — IO qiymət modeli tam (dərhal) ötürmə fərz edir — yuxarı hədd |
| Real orta əmək haqqının artımı | 2016 | −4,76 | 3,66 (pre2) | −8,42 | 4,74 (6) | DSK 4.5–4.8 / İQİ — neft gəlirlərinin azalması ilə qarışıq |

**Proqnoz və fakt:**

| Göstərici | İl | Metod | Proqnoz [interval] | Fakt (təsir) | Sapma | % sapma | İstiqamət | İntervalda | Sadə etalon (qayda) | Etalondan yaxşı | Güc | Nümunə | Sinif | Alt. əks-faktual |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **İQİ inflyasiyası (illik orta)** | 2015 | MikroUnit struktur zənciri (köçürülmüş şok) | 1,47 [0,5; 2,4] | 2,10 | −0,63 | 30 | — | bəli | −0,50 (prev) | bəli | aşağı | daxili | müəyyən deyil (aşağı güc) | müəyyən deyil (aşağı güc) |
| **İQİ inflyasiyası (illik orta)** | 2016 | MikroUnit struktur zənciri (köçürülmüş şok) | 6,31 [2,2; 10,5] | 10,50 | −4,19 | 40 | bəli | xeyr | 2,10 (prev) | bəli | orta | daxili | **qismən uyğun** | qismən uyğun |
| **İQİ inflyasiyası (illik orta)** | 2017 | MikroUnit struktur zənciri (köçürülmüş şok) | 6,77 [2,3; 11,2] | 11,00 | −4,23 | 38 | — | bəli | 10,50 (prev) | xeyr | aşağı | daxili | müəyyən deyil (aşağı güc) | müəyyən deyil (aşağı güc) |
| **İQİ səviyyəsi — 2015–2017 kumulyativ artıq** | 2017 | IO qiymət modeli (Leontief, tam ötürmə) | 51,34 [41,4; 51,3] | 24,73 | +26,61 | 108 | bəli | xeyr | −1,46 (prev) | xeyr | orta | kənar | **uyğunsuz** | uyğunsuz |
| **İQİ səviyyəsi — 2015–2017 kumulyativ artıq** | 2017 | MikroUnit struktur zənciri (köçürülmüş şok) | 14,40 [4,9; 23,9] | 24,73 | −10,33 | 42 | bəli | xeyr | −1,46 (prev) | bəli | orta | daxili | **qismən uyğun** | qismən uyğun |
| Real orta əmək haqqının artımı | 2016 | MikroUnit struktur zənciri (köçürülmüş şok) | −3,00 [−5,0; −1,0] | −8,42 | +5,42 | 64 | bəli | xeyr | −2,66 (prev) | bəli | orta | daxili | **qismən uyğun** | qismən uyğun |

**Sapmalar və izah (əsas göstəricilər):**

- İQİ inflyasiyası (illik orta) (2015, MikroUnit struktur zənciri (köçürülmüş şok)): müşahidə olunan təsir 2,1 əks-faktualın səs-küyündən (σ = 7,9) kiçikdir — test aşağı güclüdür; proqnoz 1,5, sapma −0,6.
- İQİ inflyasiyası (illik orta) (2016, MikroUnit struktur zənciri (köçürülmüş şok)): proqnoz 6,3, fakt 10,5 — model təsiri 40 % az qiymətləndirir (sapma −4,2); sinif: qismən uyğun; alternativ əks-faktualla: qismən uyğun.
- İQİ inflyasiyası (illik orta) (2017, MikroUnit struktur zənciri (köçürülmüş şok)): müşahidə olunan təsir 11,0 əks-faktualın səs-küyündən (σ = 13,0) kiçikdir — test aşağı güclüdür; proqnoz 6,8, sapma −4,2.
- İQİ səviyyəsi — 2015–2017 kumulyativ artıq (2017, IO qiymət modeli (Leontief, tam ötürmə)): proqnoz 51,3, fakt 24,7 — model təsiri 108 % artıq qiymətləndirir (sapma +26,6); sinif: uyğunsuz; alternativ əks-faktualla: uyğunsuz.
- İQİ səviyyəsi — 2015–2017 kumulyativ artıq (2017, MikroUnit struktur zənciri (köçürülmüş şok)): proqnoz 14,4, fakt 24,7 — model təsiri 42 % az qiymətləndirir (sapma −10,3); sinif: qismən uyğun; alternativ əks-faktualla: qismən uyğun.

**Hökm:** keçmədi — əsas göstəricilər üzrə həlledici müqayisələrin orta balı 0,67 (2 = uyğun, 1 = qismən, 0 = uyğunsuz); həlledici müqayisələr: 4 / 6; istiqamət uyğunluğu 100 %; sadə etalondan yaxşı: 67 %. Nümunədaxili müqayisələr struktur uyğunluğu göstərir, proqnoz gücünü yox.

### E7. Yanacaq qiyməti və nəqliyyat tarifləri paketi (30.06.2024)

- **Siyasət:** AI-92 1,00 → 1,10 AZN/l (+10 %), dizel 0,80 → 1,00 (+25 %), AI-95 −20 %; Bakı avtobus/metro 0,40 → 0,50 AZN; Abşeronda tullantı haqqı ×2,33
- **Tarix:** 01.07.2024 (Tarif Şurası, 30.06.2024); **hüquqi əsas:** Tarif Şurasının 30.06.2024 qərarları (apa.az 487837; turan.az)
- **Nümunə statusu:** nümunədən kənar — Nümunədən kənar: IO cədvəli 2021, yanacaq qarışığı ekspert fərziyyəsi; MikroUnit overlay çəkiləri fiscal_params.csv fərziyyəsi; heç bir parametr E7-yə kalibrlənməyib
- **Modellər:** IO qiymət modeli — E7 xüsusi şoku (IO agenti); MikroUnit struktur zənciri (köçürülmüş şok); Nazirlik CAEM modeli — müqayisə
- **Ötürmə mexanizmi və qarışıqlıq:** IO qiymət modeli tənzimlənən qiymətlərin birbaşa və dolayı (aralıq istehlak) ötürülməsini hesablayır; MikroUnit overlay və CAEM yalnız yanacaq şokunu İQİ səviyyəsinə ötürür (avtobus/metro və tullantı tarifləri onlarda yoxdur).

**Məlumat və əks-faktual:**

| Göstərici | İl | Fakt | Əks-faktual (qayda) | Müşahidə olunan təsir | σ əks-faktual (n) | Mənbə |
|---|---|---|---|---|---|---|
| Ümumi İQİ (dekabr/dekabr) — tam paket | 2024 | 4,90 | 2,15 (file) | 2,75 | 10,45 (10) | DSK price_tarif 001_5 (IO agentinin V_io_e7_fuel_2024.csv) — ərzaq inflyasiyasının sürətlənməsi siyasətlə bağlı deyil; MikroUnit və CAEM yalnız yanacaq şokunu görür |
| İQİ: yanacaq məhsulları | 2024 | 7,10 | 0,00 (file) | 7,10 | — (0) | DSK price_tarif 001_5 — tənzimlənən qiymət: əks-faktual 0 |
| İQİ: avtomobil sərnişin nəqliyyatı | 2024 | 15,90 | 0,00 (file) | 15,90 | — (0) | DSK price_tarif 001_5 — 2023-də də +18 % (şəhərlərarası tariflər) |
| İQİ: digər nəqliyyat xidmətləri | 2024 | 3,20 | 2,25 (file) | 0,95 | — (0) | DSK price_tarif 001_5 — yalnız dolayı ötürmə |
| İQİ: qeyri-ərzaq mallar və xidmətlər | 2024 | 4,50 | 3,26 (file) | 1,24 | — (0) | DSK price_tarif 001_5 |

**Proqnoz və fakt:**

| Göstərici | İl | Metod | Proqnoz [interval] | Fakt (təsir) | Sapma | % sapma | İstiqamət | İntervalda | Sadə etalon (qayda) | Etalondan yaxşı | Güc | Nümunə | Sinif | Alt. əks-faktual |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Ümumi İQİ (dekabr/dekabr) — tam paket** | 2024 | IO qiymət modeli — E7 xüsusi şoku (IO agenti) | 1,22 [1,2; 1,6] | 2,75 | −1,53 | 55 | — | xeyr | 1,07 (io_direct) | bəli | aşağı | kənar | müəyyən deyil (aşağı güc) | müəyyən deyil (aşağı güc) |
| **Ümumi İQİ (dekabr/dekabr) — tam paket** | 2024 | MikroUnit struktur zənciri (köçürülmüş şok) | 0,35 — | 2,75 | −2,40 | 87 | — | — | 1,07 (io_direct) | xeyr | aşağı | kənar | müəyyən deyil (aşağı güc) | müəyyən deyil (aşağı güc) |
| **Ümumi İQİ (dekabr/dekabr) — tam paket** | 2024 | Nazirlik CAEM modeli — müqayisə | 0,34 — | 2,75 | −2,41 | 88 | — | — | 1,07 (io_direct) | xeyr | aşağı | kənar | müəyyən deyil (aşağı güc) | müəyyən deyil (aşağı güc) |
| **İQİ: yanacaq məhsulları** | 2024 | IO qiymət modeli — E7 xüsusi şoku (IO agenti) | 7,75 — | 7,10 | +0,65 | 9 | bəli | — | 7,75 (shock) | xeyr | yüksək | kənar | **qismən uyğun** | qismən uyğun |
| İQİ: avtomobil sərnişin nəqliyyatı | 2024 | IO qiymət modeli — E7 xüsusi şoku (IO agenti) | 8,96 — | 15,90 | −6,94 | 44 | bəli | — | 25,00 (const) | bəli | yüksək | kənar | **qismən uyğun** | uyğunsuz |
| İQİ: digər nəqliyyat xidmətləri | 2024 | IO qiymət modeli — E7 xüsusi şoku (IO agenti) | 0,33 [0,1; 0,4] | 0,95 | −0,62 | 65 | bəli | xeyr | 0,00 (zero) | bəli | yüksək | kənar | **uyğunsuz** | uyğunsuz |
| İQİ: qeyri-ərzaq mallar və xidmətlər | 2024 | IO qiymət modeli — E7 xüsusi şoku (IO agenti) | 1,75 — | 1,24 | +0,51 | 41 | bəli | — | 0,00 (zero) | bəli | yüksək | kənar | **qismən uyğun** | qismən uyğun |

**Sapmalar və izah (əsas göstəricilər):**

- Ümumi İQİ (dekabr/dekabr) — tam paket (2024, IO qiymət modeli — E7 xüsusi şoku (IO agenti)): müşahidə olunan təsir 2,8 əks-faktualın səs-küyündən (σ = 10,5) kiçikdir — test aşağı güclüdür; proqnoz 1,2, sapma −1,5.
- Ümumi İQİ (dekabr/dekabr) — tam paket (2024, MikroUnit struktur zənciri (köçürülmüş şok)): müşahidə olunan təsir 2,8 əks-faktualın səs-küyündən (σ = 10,5) kiçikdir — test aşağı güclüdür; proqnoz 0,3, sapma −2,4.
- Ümumi İQİ (dekabr/dekabr) — tam paket (2024, Nazirlik CAEM modeli — müqayisə): müşahidə olunan təsir 2,8 əks-faktualın səs-küyündən (σ = 10,5) kiçikdir — test aşağı güclüdür; proqnoz 0,3, sapma −2,4.
- İQİ: yanacaq məhsulları (2024, IO qiymət modeli — E7 xüsusi şoku (IO agenti)): proqnoz 7,8, fakt 7,1 — model təsiri 9 % artıq qiymətləndirir (sapma +0,7); sinif: qismən uyğun; alternativ əks-faktualla: qismən uyğun.

**Hökm:** şərti keçdi — əsas göstəricilər üzrə həlledici müqayisələrin orta balı 1,00 (2 = uyğun, 1 = qismən, 0 = uyğunsuz); həlledici müqayisələr: 4 / 7; istiqamət uyğunluğu 100 %; sadə etalondan yaxşı: 57 %. Diqqət: hökm cəmi 1 həlledici əsas müqayisəyə əsaslanır — zəif sübut.

## 4. NFR2 — eyni hadisə üçün metodların müqayisəsi

| Sətir | Göstərici | İl | Fakt | Metodlar üzrə proqnoz | Metodlararası fərq | Ən yaxın metod |
|---|---|---|---|---|---|---|
| E1.w | Orta aylıq nominal əmək haqqının artımı | 2019 | 12,22 | e2_direct: 11,68; micro_chain: 16,43; microsim: 0,49 | 15,94 | e2_direct |
| E1.did | Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) | 2019 | 12,04 | fr3_direct: 27,87; micro_chain: 23,98; microsim: 1,07 | 26,80 | microsim |
| E1.emp | Qeyri-dövlət sektorunda muzdlu işçilərin artımı | 2019 | 5,99 | micro_chain: 0,08; microsim: 5,92 | 5,84 | microsim |
| E3.did22 | Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) | 2022 | 16,03 | fr3_direct: 11,69; micro_chain: 11,05 | 0,64 | fr3_direct |
| E3.did23 | Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) | 2023 | 7,35 | fr3_direct: 8,84; micro_chain: 7,81 | 1,04 | micro_chain |
| E3.did24 | Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) — plasebo | 2024 | 2,30 | fr3_direct: 0,00; micro_chain: 0,52 | 0,52 | micro_chain |
| E3.w22 | Orta aylıq nominal əmək haqqının artımı | 2022 | 7,30 | e2_direct: 5,09; micro_chain: 7,07 | 1,98 | micro_chain |
| E3.w23 | Orta aylıq nominal əmək haqqının artımı | 2023 | 3,74 | e2_direct: 3,88; micro_chain: 5,40 | 1,51 | e2_direct |
| E3.w24 | Orta aylıq nominal əmək haqqının artımı — plasebo | 2024 | 0,64 | e2_direct: 0,00; micro_chain: −0,01 | 0,01 | e2_direct |
| E3.w25 | Orta aylıq nominal əmək haqqının artımı | 2025 | 1,82 | e2_direct: 4,11; micro_chain: 5,81; microsim: 0,47 | 5,34 | microsim |
| E3.did25 | Dövlət − qeyri-dövlət sektoru maaş artımı fərqi (DiD) | 2025 | 5,43 | fr3_direct: 9,38; micro_chain: 7,50 | 1,89 | micro_chain |
| E5.cum | İQİ səviyyəsi — 2015–2017 kumulyativ artıq | 2017 | 24,73 | io_price: 51,34; micro_chain: 14,40 | 36,94 | micro_chain |
| E7.cpi | Ümumi İQİ (dekabr/dekabr) — tam paket | 2024 | 2,75 | io_e7: 1,22; micro_chain: 0,35; caem: 0,34 | 0,89 | io_e7 |

## 5. Ümumi nəticələr

- E1: əsas göstəricilər üzrə ən kiçik median % sapma — MikroUnit FR1 E2 tənliyi (birbaşa, qismən tarazlıq) (4 %); ən böyük — MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa) (132 %).
- E3: əsas göstəricilər üzrə ən kiçik median % sapma — Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK) (27 %); ən böyük — MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa) (50 %).
- E5: əsas göstəricilər üzrə ən kiçik median % sapma — MikroUnit struktur zənciri (köçürülmüş şok) (41 %); ən böyük — IO qiymət modeli (Leontief, tam ötürmə) (108 %).
- E7: əsas göstəricilər üzrə ən kiçik median % sapma — IO qiymət modeli — E7 xüsusi şoku (IO agenti) (9 %).
- Tolerantlıqdan kənar (uyğunsuz) müqayisələr: E1.w microsim (proqnoz 0,5, fakt 12,2); E1.did fr3_direct (proqnoz 27,9, fakt 12,0); E1.did micro_chain (proqnoz 24,0, fakt 12,0); E1.did microsim (proqnoz 1,1, fakt 12,0); E1.emp micro_chain (proqnoz 0,1, fakt 6,0); E5.cum io_price (proqnoz 51,3, fakt 24,7); E7.otr io_e7 (proqnoz 0,3, fakt 1,0).
- Aşağı güclü (hökmə daxil edilməyən) müqayisələr: 13 — E1.infl, E1.gdp, E1.pov, E3.w23, E3.w25, E5.i15, E5.i17, E7.cpi; bu göstəricilərdə illik məlumatla siyasət təsirini əks-faktualın səs-küyündən ayırmaq mümkün deyil.
- Plasebo (2024, minimum əmək haqqı dəyişməyib): 4 müqayisədən 4 «uyğun» — modellər siyasət olmayan ildə saxta təsir yaratmır.

Metodlar üzrə sistematik meyl (vahidlər qarışıqdır — yalnız işarə informativdir):

- MikroUnit FR1 E2 tənliyi (birbaşa, qismən tarazlıq): orta bal 2,00, təsirləri orta hesabla az qiymətləndirir (orta sapma −0,19), median % sapma 30.
- MikroUnit struktur zənciri (köçürülmüş şok): orta bal 1,21, təsirləri orta hesabla az qiymətləndirir (orta sapma −0,57), median % sapma 44.
- Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK): orta bal 0,80, təsirləri orta hesabla az qiymətləndirir (orta sapma −3,50), median % sapma 74.
- MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa): orta bal 1,20, təsirləri orta hesabla artıq qiymətləndirir (orta sapma +2,93), median % sapma 73.
- IO qiymət modeli (Leontief, tam ötürmə): orta bal 0,00, təsirləri orta hesabla artıq qiymətləndirir (orta sapma +26,61), median % sapma 108.
- IO qiymət modeli — E7 xüsusi şoku (IO agenti): orta bal 0,75, təsirləri orta hesabla az qiymətləndirir (orta sapma −1,58), median % sapma 44.
- Nazirlik CAEM modeli — müqayisə: orta bal —, təsirləri orta hesabla az qiymətləndirir (orta sapma −2,41), median % sapma 88.

**Məhdudiyyətlər:**

- Parametrlər tam nümunə üzrədir: hadisədən əvvəlki məlumatla yenidən qiymətləndirmə aparılmayıb, OxLon/Nazirlik proqnoz vintajları (hadisədən əvvəlki rəsmi proqnoz) layihədə yoxdur, CAEM-də vintaj yoxdur → nümunədaxili hadisələr proqnoz gücünü deyil, struktur uyğunluğu yoxlayır (Blueprint «Option 2 — honest»).
- Bütün fakt dəyərləri cari (yenidən işlənmiş) DSK/AMB vintajıdır; ilkin dərc dəyərləri arxivləşdirilməyib.
- Köçürülmüş şok: tarixi alət yolu MikroUnit-in cari (2026–2030) strukturuna tətbiq edilir; hadisə ili zəncirin 2027-ci ilinə uyğunlaşdırılır, çünki FR3-də 2026 nowcast ilə bağlanıb və ilk il reaksiya vermir.
- Model intervalı yalnız əsas əmsalların standart xətalarından (delta metodu, kovariasiyalar nəzərə alınmadan) qurulur; IO intervalı cədvəl ili / yanacaq qarışığı həssaslığıdır; CAEM və overlay üçün statistik interval yoxdur.
- Mikrosimulyasiya SİNTETİK ev təsərrüfatı faylı ilə işləyir — real ev təsərrüfatı məlumatı deyil.

**Tövsiyələr:**

- Tolerantlıq qaydası (bölmə 2.4) Nazirlik tərəfindən təsdiqlənməli və ya dəyişdirilməlidir (Sorğuda NFR1 cavabsızdır); parametrlər `validate.TOL`-da, nəticə `V_nfr1_tolerance.csv`-də.
- Proqnoz vintajlarının arxivi (ex ante ssenari nəticələri vintaj id ilə) yaradılmalıdır ki, növbəti hadisələr (məs. 2026 gəlir vergisinin bərpası) həqiqi nümunədən kənar qiymətləndirilsin.
- DSK-dan aylıq İQİ maddə sıraları və ilkin dərc dəyərləri alınmalıdır (E7 tipli hadisə tədqiqatı və vintaj testi üçün).
- Ev təsərrüfatı büdcə sorğusu (HBS) mikroməlumatı ilə sintetik fayl əvəz edildikdə E1 yoxsulluq testi təkrarlanmalıdır.
- Yeni hadisə = `config/historical_events.csv`-yə sətirlər (kod dəyişikliyi tələb olunmur; yeni şok növü üçün `nfr1_models.shock`).

## 6. Fayllar və vintaj

`config/historical_events.csv` (hadisə reyestri), `output/V_nfr1_observed.csv`, `V_nfr1_comparisons.csv`, `V_nfr1_events.csv`, `V_nfr1_methods.csv`, `V_nfr1_tolerance.csv`, `V_nfr1_run_meta.csv`; istifadə olunan digər agentlərin faylları: `V_io_e7_fuel_2024.csv`, `V_io_e7_sensitivity.csv`, `V_microsim_2019_package.csv`, `V_microsim_2025_minwage.csv`.

| Açar | Dəyər |
|---|---|
| run_at | `2026-10-07T01:57:22` |
| seconds | `1.55` |
| n_events | `4` |
| n_comparisons | `45` |
| chain_offset | `1` |
| micro_vintage | `7099d341e599` |
| events_md5 | `98414cf5ef8f` |
| panel_md5 | `fd4967d58477` |
| macro_md5 | `efe6012097a6` |
| fr1raw_md5 | `7d3ef61529b1` |
| pov_md5 | `2bf3ca24252d` |
| io_e7_md5 | `801340e6b93c` |
| mw_md5 | `1a93a4a75865` |
| caem_md5 | `12c22d22eda046e050643004a8d7eec5` |
