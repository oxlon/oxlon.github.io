# SXEM — `2_neticeler/` qovluğundakı beş CSV faylının və Excel iş kitabının quruluşu

Bu sənəd Nazirliyin dashboard tərtibatçısı üçündür. Hər fayl üçün sütunların adı, tipi, vahidi və
mənası verilir; sonda faktiki bir sətir sətir-sətir izah olunur, ardınca isə eyni məlumatın Excel
təqdimatı (`neticeler_15_5_1.xlsx`) vərəq-vərəq və JSON təqdimatı (`neticeler_15_5_1.json`)
bölmə-bölmə göstərilir. Bütün CSV faylları UTF-8 kodlaşdırmasında, vergüllə ayrılmış, birinci sətri
başlıq olan adi CSV formatındadır; ondalıq ayırıcı NÖQTƏ-dir (`68.98`), boş xana isə tam boşdur
(`NA`, `null` və ya `-` yazılmır). Sətirlərin sırası təbii açar üzrə sabitdir, ona görə iki icra
arasında fayllar sətir-sətir müqayisə oluna bilər.

Beş fayl bir-birinə `series_code` sütunu ilə bağlanır: `series_dictionary.csv` sıra kodlarının
lüğətidir, `forecast_long.csv` onların illik dəyərlərini, `equations_catalog.csv` həmin sıraları
istehsal edən tənlikləri, `validation_backtest.csv` isə dəqiqlik ölçmələrini saxlayır.
`assumptions.csv` proqnoz üfüqünün ekzogen girişlərini ayrıca saxlayır.

---

## 1. `forecast_long.csv` — sıraların illik dəyərləri (uzun format)

14 603 sətir, 12 sütun. Təbii açar: `fr` + `series_code` + `year` + `kind` + `source`. Tarixi və
proqnoz dəyərləri EYNİ cədvəldədir; onları `kind` sütunu ayırır.

| # | Sütun | Tip | Vahid / mümkün dəyərlər | Mənası |
|---|---|---|---|---|
| 1 | `fr` | mətn | `FR1`, `FR1B`, `FR2`, `FR3`, `FR4`, `FR5`, `FR5B`, `FR6`, `FR7`, `FR8`, `FR9`, `FR10`, `FR11`, `FR12`, `FR13` | Sətri yazan funksional tələb. |
| 2 | `series_code` | mətn | 653 fərqli kod | Göstəricinin maşın kodu; `series_dictionary.csv` ilə birləşdirmə açarıdır. |
| 3 | `series_name_az` | mətn | — | Göstəricinin Azərbaycan dilində adı (lüğətdəki `name_az` ilə eynidir). |
| 4 | `unit` | mətn | 36 vahid, məsələn `%`, `mln AZN`, `mln USD`, `USD/barel`, `min ton` | Dəyərin ölçü vahidi. Faiz sıralarında dəyər artıq faizlə verilir (`2.51` = 2,51 %), nisbət kimi deyil. |
| 5 | `year` | tam ədəd | 1985–2030 | Təqvim ili. 1985–2025 faktiki, 2026–2030 proqnoz üfüqüdür. |
| 6 | `kind` | mətn | `actual`, `forecast` | `actual` — hesabat (faktiki) dəyər; `forecast` — proqnoz dəyəri. Qiymətləndirmə nümunəsi heç vaxt `forecast` sətirlərini əhatə etmir. |
| 7 | `source` | mətn | `imf_reference`, `ministry_spec`, `ours`, `template_sample` | `ours` — bu paketin modeli; `template_sample` — 8 vərəq şablonundakı nümunə (şablon) rəqəmləri, AZ etiketi "şablon-nümunə ssenarisi (75 saylı qərar formatı üzrə)", YALNIZ müqayisə üçün; `ministry_official` — Nazirliyin RƏSMİ proqnozu üçün ayrılmış slot, hazırda BOŞDUR; `ministry_spec` — **Nazirlik spesifikasiyası ssenarisi** (FR13): Nazirliyin öz 92 sətirlik tənlik kataloqunun ÖZ əmsalları ilə, bu paketin məlumat qatı və ekzogen yolları üzərində həll edilmiş yolu — baza proqnoz DEYİL, müqayisə sütunudur; `imf_reference` — **BVF etalon proqnozu**: Beynəlxalq Valyuta Fondunun (BVF; beynəlxalq mətnlərdə IMF) Maddə IV məsləhətləşməsi üzrə ölkə hesabatı 26/112 (Cədvəl 1) və eyni buraxılışın WEO yolu, buraxılış qeydi "BVF Maddə IV 26/112, aprel 2026 vintajı" — yalnız tərifi üst-üstə düşən üç sıra üçün (15 sətir: `gdp_realg`, `nonoil_realg`, `cpi_infl`), zolaqsız, müqayisə sütunudur. Dashboard-da baza ssenari kimi `ours` göstərilməlidir. |
| 8 | `value` | onluq ədəd | `unit` sütununa uyğun | Göstəricinin dəyəri. Boş ola bilməz. |
| 9 | `lo80` | onluq ədəd | `unit` ilə eyni | 80 % yelpik zolağının aşağı həddi. **Boş ola bilər.** |
| 10 | `hi80` | onluq ədəd | `unit` ilə eyni | 80 % yelpik zolağının yuxarı həddi. **Boş ola bilər.** |
| 11 | `lo50` | onluq ədəd | `unit` ilə eyni | 50 % yelpik zolağının aşağı həddi. **Boş ola bilər.** |
| 12 | `hi50` | onluq ədəd | `unit` ilə eyni | 50 % yelpik zolağının yuxarı həddi. **Boş ola bilər.** |

**Yelpik sütunlarının boşluğu haqqında.** Dörd zolaq sütunu müqavilədə nullable elan olunub və
faylın 14 603 sətrinin yalnız 445-ində doludur (89 sıra üzrə). Zolaq YALNIZ `kind=forecast` və
`source=ours` sətirlərində, yəni bu paketin öz mərkəzi yolunda mövcuddur; `actual` sətirlərində
qeyri-müəyyənlik anlayışı tətbiq olunmur, `template_sample` və `imf_reference` sətirlərində isə
mənbənin öz rəqəmi zolaqsız nəşr olunduğu üçün sütunlar boş qalır (uydurulmur). Törənmiş (qalıq)
sıralar — məsələn daxili investisiya — qəsdən ayrıca zolaq daşımır. Dörd sütun həmişə birlikdə
doludur və ya birlikdə boşdur, ona görə dashboard `lo80` sütununun boşluğunu yoxlamaqla zolağın
olub-olmadığını müəyyən edə bilər. Zolaq olmayan sətirdə xətt sadəcə zolaqsız çəkilməlidir; sıfır
kimi oxunmamalıdır.

**`ours` və `template_sample` bəzən eyni dəyəri daşıyır.** Bu, xəta deyil: neft-qaz sektorunun real
artımı və altı vərəq məhsulu üçün Nazirliyin öz göstəricisi açıq şəkildə ekzogen fərziyyə olaraq
qəbul edilib (izahı `README.md`, Bölmə 4).

---

## 2. `equations_catalog.csv` — qiymətləndirilmiş tənliklərin kataloqu

486 sətir, 12 sütun. Bir qiymətləndirilmiş tənlik = bir sətir. Təbii açar: `fr` + `eq_name`.

| # | Sütun | Tip | Vahid / mümkün dəyərlər | Mənası |
|---|---|---|---|---|
| 1 | `workbook` | mətn | `Statistik data dinamika 05.06.2026 +.xlsx`, `8 vərəq` | Tənliyin sol tərəfindəki sıranın gəldiyi mənbə sənəd. Mənbə sənədə bağlı olmayan (kalibrlənmiş/etalon) tənliklərdə boş ola bilər. |
| 2 | `sheet` | mətn | məsələn `Real sektor`, `Monetar sektoru`, `2.4.1.4.` | Mənbə vərəqi. Yuxarıdakı halda boş ola bilər. |
| 3 | `eq_name` | mətn | unikal ad, məsələn `FR1_neft_deflyatoru` | Tənliyin adı; `fr` ilə birlikdə sətri unikal identifikasiya edir. |
| 4 | `description` | mətn | — | Tənliyin bir cümləlik izahı (AZ). Rejim etiketi ilə başlayır: `STRUKTUR` (əsas davranış tənliyi), `ETALON` (müqayisə bazası), `ROBUSTLİK` (eyni tənliyin yoxlama variantı). |
| 5 | `lhs` | mətn | dəyişən adı | Tənliyin sol tərəfi (asılı dəyişən). |
| 6 | `rhs` | mətn | dəyişənlərin cəmi, `+` ilə | Tənliyin sağ tərəfi (izahedici dəyişənlər). |
| 7 | `series_code` | mətn | lüğətdəki kod | Tənliyin xidmət etdiyi sıra; `forecast_long.csv` ilə birləşdirmə açarıdır. |
| 8 | `fr` | mətn | `FR1`, `FR1B`, `FR2`, `FR4`, `FR5`, `FR5B`, `FR6`, `FR7`, `FR8`, `FR9`, `FR11`, `FR12`, `FR13` | Tənliyi yazan funksional tələb. FR3, FR10 və FR12 bu fayla sətir yazmır (uyğun olaraq identiklik, rejim və konsolidasiya xarakterlidirlər). |
| 9 | `sample_start` | tam ədəd | 1992–2025 | Qiymətləndirmə nümunəsinin ilk ili. |
| 10 | `sample_end` | tam ədəd | ≤ 2030 | Qiymətləndirmə nümunəsinin son ili. Heç bir tənlikdə 2025-dən böyük ola bilməz — proqnoz illəri reqressiyaya daxil edilmir. |
| 11 | `adj_r2` | onluq ədəd | 0–1 | Düzəldilmiş determinasiya əmsalı R². **Boş ola bilər** (213 sətir): ETALON rejimində tənlik qiymətləndirilmir, sadə orta götürülür. |
| 12 | `se_regression` | onluq ədəd | `lhs` vahidi ilə | Reqressiyanın standart xətası. Eyni 213 sətirdə boş olur. |

---

## 3. `validation_backtest.csv` — geriyə doğru sınağın (backtest) nəticələri

6 747 sətir, 11 sütun. 169 sıra və 113 fərqli `model` etiketi üzrə (RW etalonu daxil; onsuz 112
model) genişlənən pəncərəli, bir addımlıq, nümunədən kənar sınaq. Təbii açar: `series_code` +
`model` + `vintage_year` + `horizon_h`.

| # | Sütun | Tip | Vahid / mümkün dəyərlər | Mənası |
|---|---|---|---|---|
| 1 | `series_code` | mətn | lüğətdəki kod | Sınaqdan keçirilən sıra. |
| 2 | `model` | mətn | məsələn `STRUKTUR`, `AR(1)`, `RW`, `ORTA5`, `KOMPONENT-ANSAMBL`, `DINAMIKLIK` | Sınanan üsulun adı. `RW` təsadüfi gəzişmə etalonudur. `DINAMIKLIK` sınaq DEYİL — dinamiklik göstəricisidir (aşağıda ayrıca izah olunur). |
| 3 | `vintage_year` | tam ədəd | 2002–2025 | Təlim nümunəsinin bitdiyi il — model YALNIZ bu il daxil olmaqla məlumatı görür. |
| 4 | `horizon_h` | tam ədəd | `1`, `5` | Proqnoz üfüqü. Proqnozlaşdırılan il = `vintage_year` + `horizon_h`. |
| 5 | `actual` | onluq ədəd | modelin öz dəyişəninin vahidi | Faktiki dəyər. |
| 6 | `forecast` | onluq ədəd | modelin öz dəyişəninin vahidi | Modelin həmin il üçün proqnozu. |
| 7 | `error` | onluq ədəd | eyni vahid | `forecast − actual`. Müsbət dəyər modelin yuxarı qiymətləndirdiyini göstərir. |
| 8 | `abs_error` | onluq ədəd | eyni vahid | `error`-un mütləq qiyməti. |
| 9 | `rmse_h` | onluq ədəd | eyni vahid | Modelin bütün sınaq illəri üzrə orta kvadratik xətası. Bu, PƏNCƏRƏ səviyyəsində göstəricidir — hər `(series_code, model)` cütünün bütün sətirlərində eyni təkrarlanır. |
| 10 | `rw_rmse_h` | onluq ədəd | eyni vahid | Təsadüfi gəzişmə (RW) etalonunun eyni pəncərədəki orta kvadratik xətası. Eyni şəkildə təkrarlanır. |
| 11 | `coverage80` | onluq ədəd | 0–1 | 80 % zolağın faktiki əhatəsi: faktiki dəyərin zolağın içində qaldığı illərin payı. |

**Bacarıq (skill) necə hesablanır.** Dashboard-da göstəriləcək rəqəm
`bacarıq = 1 − rmse_h / rw_rmse_h`-dir: müsbət dəyər modelin təsadüfi gəzişmədən dəqiq olduğunu
bildirir. Hər cüt üçün bir dəfə hesablanmalıdır (sətirlər üzrə cəmlənməməlidir), çünki `rmse_h` və
`rw_rmse_h` artıq pəncərə səviyyəsində aqreqasiya olunmuş kəmiyyətlərdir.

**`model = "DINAMIKLIK"` sətirləri — DİQQƏT, bunlar sınaq sətri DEYİL.** Fayl bir də proqnozun
**dinamiklik göstəricisini** daşıyır: σ(proqnoz 2026-2030) ⁄ σ(faktiki 2013-2025), hər ikisi
populyasiya standart kənarlaşmasıdır. Həmin sətirlərdə sütunların oxunuşu fərqlidir:

| Sütun | `DINAMIKLIK` sətrində nə deməkdir |
|---|---|
| `actual` | σ(faktiki), tarixi pəncərə (2013-2025) |
| `forecast` | σ(proqnoz), 2026-2030 |
| `error` / `abs_error` | σ(proqnoz) − σ(faktiki) və onun mütləq qiyməti |
| `rmse_h` | **GÖSTƏRİCİNİN ÖZÜ** — σ nisbəti (RMSE DEYİL) |
| `rw_rmse_h` | istinad dəyəri 1,0 (faktiki qədər dəyişkən proqnoz) |
| `vintage_year` | son faktiki il |
| `horizon_h` | proqnoz pəncərəsinin uzunluğu (il) |
| `coverage80` | boş |

**Dashboard üçün qayda:** bacarıq hesablanarkən, "ən yaxşı model" seçilərkən və RMSE ortalaması
götürülərkən `model = "DINAMIKLIK"` sətirləri **KƏNARLAŞDIRILMALIDIR** — əks halda σ nisbəti RMSE
kimi oxunar. Göstərici ayrıca sütun/panel kimi göstərilir: sıfıra yaxın dəyər proqnozun praktik
olaraq sabit olduğunu bildirir; şərti orta proqnoz tərifinə görə faktikidən az dəyişkən olduğu üçün
1-dən kiçik dəyər qüsur deyil. Göstərici DƏQİQLİK ölçüsü deyil — dəqiqlik `rmse_h` sütunundan gələn
bacarıqla ölçülür və iki göstərici birlikdə oxunmalıdır.

Eyni şəkildə, `series_code`-u `_dinamika` ilə bitən sətirlər bir tənliyin ÜÇ formasının (statik,
gecikmiş asılı dəyişənli, ECM) müqayisəsidir: onlar normal sınaq sətirləridir, lakin əsas sıranın öz
sınağı ilə eyni panelə qarışdırılmamalıdır.

**Vahid haqqında xəbərdarlıq.** `actual`, `forecast`, `error`, `abs_error`, `rmse_h` və `rw_rmse_h`
sütunları modelin ÖZ asılı dəyişəninin vahidindədir, sıranın nəşr olunan vahidində deyil. Məsələn
Brent qiyməti üçün model loqarifm səviyyəsində qiymətləndirildiyindən bu sütunlarda `4.12` kimi
dəyərlər görünür (ln 61,7), USD/barel deyil. Bu fayl dəqiqlik ölçüsüdür; səviyyələr üçün
`forecast_long.csv` istifadə olunmalıdır.

---

## 4. `series_dictionary.csv` — sıra lüğəti

681 sətir, 7 sütun. Bir `series_code` = bir sətir; `series_code` həm təbii açar, həm də digər
fayllarla birləşdirmə açarıdır.

| # | Sütun | Tip | Vahid / mümkün dəyərlər | Mənası |
|---|---|---|---|---|
| 1 | `series_code` | mətn | unikal, 681 kod | Göstəricinin maşın kodu. |
| 2 | `name_az` | mətn | — | Azərbaycan dilində tam ad. |
| 3 | `name_en` | mətn | — | İngilis dilində ad. Bəzi texniki sıralarda AZ adı ilə eyni saxlanılıb. |
| 4 | `unit` | mətn | `forecast_long.csv`-dəki vahidlərlə eyni | Ölçü vahidi. |
| 5 | `fr` | mətn | FR1–FR12, birgə sahiblikdə `FR2/FR3`, `FR7/FR11` | Sıranı istehsal edən funksional tələb. |
| 6 | `statutory_sheet_ref` | mətn | məsələn `8 vərəq, 2.4.1.1.` və ya `Real sektor` | Statutar şablondakı və ya iş kitabındakı mənbə yeri; məhsul sıralarında sətir nömrəsi də göstərilir. Mənbədə mövcud olmayan sıralarda DATA-GAP qeydi yazılır. |
| 7 | `price_basis` | mətn | `cari`, `sabit-2025`, `indeks`, `natural` | Sıranın QİYMƏT BAZASI: cari (nominal) qiymətlər; 2025-ci ilin sabit qiymətləri; faiz/indeks göstəricisi; natural göstərici. Səviyyə sıralarında iki baza ayrı kodlarla nəşr olunur (məsələn `inv_total_nom` və `inv_total_real2025`). |

Lüğət `forecast_long.csv`-dəki bütün sıraları əhatə edir. Əks istiqamətdə tam örtük yoxdur: lüğətdə
statutar şablonda mövcud olan, lakin proqnozlaşdırılmayan bir neçə sıra da saxlanılır.

---

## 5. `assumptions.csv` — vahid fərziyyə dəsti

325 sətir (65 açar × 5 il), 5 sütun. Təbii açar: `assumption_key` + `year`. Bu fayl proqnoz üfüqünün
BÜTÜN ekzogen girişlərini bir yerdə saxlayır; modelin heç bir hissəsi sürücü yolunu başqa yerdən
oxumur.

| # | Sütun | Tip | Vahid / mümkün dəyərlər | Mənası |
|---|---|---|---|---|
| 1 | `assumption_key` | mətn | 65 açar, məsələn `brent_usd`, `cpi_infl`, `usd_azn`, `pop_avg` | Fərziyyənin adı. `_lo80`/`_hi80` sonluqlu açarlar həmin fərziyyənin yelpik həddləridir. |
| 2 | `year` | tam ədəd | 2026–2030 | Proqnoz üfüqünün ili. Hər açar üçün beş sətir var. |
| 3 | `value` | onluq ədəd | `unit` sütununa uyğun | Fərziyyənin dəyəri. |
| 4 | `unit` | mətn | `%`, `AZN/EUR`, `AZN/USD`, `USD/barel`, `USD/min m³`, `min nəfər`, `mln USD`, `pay` | Ölçü vahidi. |
| 5 | `note` | mətn | — | Dəyərin mənşəyi: hansı FR-in hansı modelindən gəldiyi və ya ekzogen mənbə (məsələn IMF WEO, ECB istinad məzənnəsi). Müqavilədə nullable elan olunub, lakin faktiki faylda bütün sətirlərdə doludur. |

`brent_usd` açarı bütün paketdə YEGANƏ neft qiyməti yoludur — beş sətir, il başına bir.

### 5.1 `assumption_registry.csv` — əvəzləmə reyestri

Fərziyyə dəstinin İDARƏETMƏ qatı: hansı açarın rəsmi göstərici ilə əvəz oluna biləcəyini və dəyərin
sahibi olan qurumu təsbit edir. 65 sətir — hər fərziyyə açarı üçün bir. *Ssenari qurucusu* ekranının
seçim siyahısı məhz bu fayldan qurulur.

| # | Sütun | Tip | Vahid / mümkün dəyərlər | Mənası |
|---|---|---|---|---|
| 1 | `assumption_key` | mətn | `assumptions.csv`-dəki açar | Birəbir uyğunluq məcburidir. |
| 2 | `override_class` | mətn | `A` (8), `B` (40), `C` (17) | **A** — rəsmi/ekzogen giriş, əvəzləmə baza yolunu dəyişir; **B** — modul nəticəsi, əvəzləmə yalnız adlandırılmış ssenari kimi; **C** — törəmə, eynilik, zolaq və ya audit möhürü, əvəzləmə qapalıdır. |
| 3 | `owner_org` | mətn | qurum adı və ya `modul — FRxx` | Dəyərin rəsmi sahibi. A sinfi üçün boş ola bilməz. |
| 4 | `basis` | mətn | — | Dəyərin haradan gəldiyinin bir sətirlik izahı. |

Uyğunluq boru xəttində yoxlanılır (`run_all.py` → `src/outputs.py`, `validate_assumption_registry`):
təsnif olunmamış açar, yetim açar, naməlum sinif və ya A sinfində boş sahib qurum icranı dayandırır.
Qaydaların tam mətni: `6_mezmun_paketi/01_FERZIYYE_EVEZLEME_MUQAVILESI.md`.

---

## 6. Nümunə sətir və onun oxunuşu

`forecast_long.csv` faylından faktiki bir sətir:

```
fr,series_code,series_name_az,unit,year,kind,source,value,lo80,hi80,lo50,hi50
FR5,brent_usd,Neftin dünya bazarında qiyməti (Brent),USD/barel,2026,forecast,ours,68.98,46.49,102.72,55.97,85.11
```

Oxunuşu: sətri **FR5** (neftin dünya bazarında qiyməti) yazıb; göstərici `brent_usd` kodu ilə
lüğətdə "Neftin dünya bazarında qiyməti (Brent)" adı altında qeyd olunub; ölçü vahidi USD/barel; il
2026; `kind=forecast` olduğu üçün bu, hesabat dəyəri deyil, proqnozdur; `source=ours` olduğu üçün
rəqəm bu paketin modelinə aiddir (şablon-nümunə ssenarisi eyni il üçün ayrı sətirdə,
`source=template_sample` ilə saxlanılır). Mərkəzi qiymət 68,98 USD/barel; 80 % ehtimalla faktiki
qiymətin 46,49 ilə 102,72 arasında, 50 % ehtimalla isə 55,97 ilə 85,11 arasında qalacağı gözlənilir.
Dashboard-da bu sətir mərkəzi xətt və onun ətrafında iki kölgəli zolaq kimi göstərilməlidir; zolağın
enliyi üfüq uzandıqca artır.

---

## 7. `neticeler_15_5_1.xlsx` — nəticələrin Excel təqdimatı

Eyni beş CSV faylından proqram vasitəsilə yığılmış 19 vərəqlik iş kitabı. Rəqəm mənbəyi budur: iş
kitabında ƏL İLƏ yerləşdirilmiş bir dəyər də yoxdur, ona görə model yenidən işlədikdə iş kitabı da
yenidən yaradılır və CSV-lərdən sürüşə bilmir. Fayl dashboard müqaviləsini ƏVƏZ ETMİR — o, eyni
məlumatın Excel-də oxunan formasıdır.

| Vərəq | Məzmun |
|---|---|
| `Mündəricat` | vərəqlərin siyahısı, mənbə faylları və `source` sözlüyü; keçidlər yalnız daxilidir |
| `2.4.1.1` | statutar 8 vərəq şablonunun 2.4.1.1. forması: 2013–2030, «Hesabat» / «Proqnoz» başlıq bölgüsü ilə |
| `FR1` … `FR13` | hər funksional tələb üçün baş proqnoz cədvəli: mərkəzi yol, 80 % zolaq və mövcud müqayisə mənbələri |
| `Fərziyyələr` | `assumptions.csv`-in tam məzmunu: hər açarın 2026–2030 yolu, vahidi və mənşə qeydi |
| `Geriyə Sınaq` | bacarıq xülasəsi: ən yaxşı model, RMSE, etalon (RW) RMSE, bacarıq faizi, 80 % əhatə və `NAZIRLIK_SPES` ssenarisinin öz sütunları |

Say formatı: pul və natural səviyyələr min ayırıcısı ilə, faiz sıraları bir onluq rəqəmlə. İş
kitabında XARİCİ KEÇİD (external link) yoxdur və heç bir formul başqa fayla istinad etmir.

---

## 8. `neticeler_15_5_1.json` — nəticələrin JSON təqdimatı

MİİS §15.5.1-in FR1–FR12 üzrə alt-tapşırıq 5-i nəticələrin İKİ maşın-oxunan formada saxlanılmasını
tələb edir — «Excel (xlsx) və json fayl formatında». Bu fayl həmin ikinci formatdır: eyni beş CSV
faylından proqram vasitəsilə yığılır, 5,9 MB həcmindədir və Excel iş kitabından FƏRQLİ olaraq
məlumatı TAM CSV dəqiqliyi ilə, heç bir yuvarlaqlaşdırma və ya format itkisi olmadan daşıyır. İş
kitabı insan üçün oxunan təqdimatdır; JSON isə birbaşa proqram girişi üçündür.

**Sənədin quruluşu.** Üst səviyyə JSON obyektidir və altı açardan ibarətdir:

| Açar | Məzmun |
|---|---|
| `meta` | sənədin təsviri: bölmə adları, hər bölmənin izahı, MƏNBƏ FAYLI, sətir sayı və sütun siyahısı; həmçinin son faktiki il və proqnoz illəri |
| `proqnoz` | `forecast_long.csv` faylının bütün 14 603 sətri, obyekt massivi kimi |
| `tenlikler` | `equations_catalog.csv` faylının bütün 486 sətri, obyekt massivi kimi |
| `geriye_sinaq` | `validation_backtest.csv` faylının bütün 6 747 sətri, obyekt massivi kimi |
| `sira_lugeti` | `series_dictionary.csv` faylının bütün 681 sətri, obyekt massivi kimi |
| `ferziyyeler` | `assumptions.csv` faylının bütün 325 sətri, obyekt massivi kimi |
| `evezleme_reyestri` | `assumption_registry.csv` faylının bütün 65 sətri, obyekt massivi kimi |

Bölmələrin sırası sabitdir: `proqnoz`, `tenlikler`, `geriye_sinaq`, `sira_lugeti`, `ferziyyeler`,
`evezleme_reyestri`.

**Sətir formatı.** Hər bölmə obyektlər massividir; hər obyektin açarları həmin CSV faylının sütun
adlarıdır. Boş xana JSON `null`-udur (boş sətir `""` DEYİL) — ona görə zolaqsız proqnoz sətrində
`lo80` açarı `null` qaytarır. Ədədi sütunlar ədəd, mətn sütunları sətir kimi verilir; il sütunları
tam ədəddir.

**Faylın fiziki düzülüşü.** `meta` bloku oxunaqlı formada (girinti ilə), məlumat sətirləri isə HƏR
BİRİ AYRICA SƏTİRDƏ, sıxılmış şəkildə yazılır. Beləliklə fayl həm `json.load()` ilə bütöv oxuna
bilir, həm də adi mətn alətləri ilə işlənə bilir — məsələn `grep '"series_code":"brent_usd"'` bir
sıranın bütün sətirlərini birbaşa tapır, `diff` isə iki buraxılışı sətir-sətir müqayisə edir.

**Təkrar istehsal.** Açarlar əlifba sırası ilə yazılır, sətirlərin sırası CSV-lərdəki təbii açar
sırası ilə eynidir, faylda heç bir zaman möhürü, icra nömrəsi və ya mütləq yol saxlanılmır — eyni
girişlərdən HƏMİŞƏ eyni bayt ardıcıllığı alınır.

**Oxunuş nümunəsi (Python):**

```python
import json
d = json.load(open("2_neticeler/neticeler_15_5_1.json", encoding="utf-8"))
d["meta"]["bolmeler"]["proqnoz"]["setir_sayi"]        # sətir sayı
[r for r in d["proqnoz"]
 if r["series_code"] == "brent_usd" and r["kind"] == "forecast"]
```
