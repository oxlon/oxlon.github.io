# IO məlumat qovluğu (`data/io/`) — DSK təklif-istifadə və girdi-çıxdı cədvəlləri

Bu qovluq IO mühərrikinin (`policyunit/eng_io.py`, MİİS §15.5.4 FR2) xam məlumatlarını saxlayır.
Bütün fayllar Dövlət Statistika Komitəsinin (stat.gov.az) rəsmi saytından olduğu kimi, dəyişdirilmədən
endirilib (2026-10-06). Yoxlama cəmləri: `MANIFEST_md5.csv` (fayl, URL, ölçü, MD5) — hər işə salınmada
yenilənir.

## Fayllar (`raw/`)
| Fayl | Məzmun | Vahid |
|---|---|---|
| `2011_1en.xls`, `2016_1en.xls`, `2021_1en.xls` | Təklif cədvəli: 81 məhsul (CPA 2 rəqəm; 41–43 və 45–47 birləşik) × 19 fəaliyyət növü (NACE A–S), idxal, ticarət-nəqliyyat əlavələri, xalis məhsul vergiləri | min AZN, əsas qiymətlər |
| `2011_2en.xls`, `2016_2en.xls`, `2021_2en.xls` | İstifadə cədvəli | min AZN |
| `2011_3en.xls`, `2016_3en.xls`, `2021_3en.xls` | Simmetrik məhsul × məhsul girdi-çıxdı cədvəli (ümumi axınlar: daxili + idxal; idxal bir sütun) | min AZN, əsas qiymətlər |
| `027en.xls` | ÜDM-in istifadəsi (son tələb komponentləri, 1993–2025) | mln AZN |
| `014en.xls`, `015en.xls` | Fəaliyyət növləri üzrə ÜDM, buraxılış, aralıq istehlak (yeniləmə üçün yoxlama) | mln AZN |
| `002_1-2en.xls` | Fəaliyyət növləri üzrə məşğul əhali (İQS əsasında, 1999–2025; vərəq `Dynamics_2.1`) | min nəfər |
| `001_5en.xlsx` | İstehlak qiymətləri indeksi maddələr üzrə (dekabr / əvvəlki ilin dekabrı) — E7 validasiyası | % |
| `002_2en.xlsx` | Sənaye məhsulları istehsalçı qiymətləri indeksi | % |

Qeyd: 2021 faylları `.xls` uzantılı olsa da əslində `.xlsx` formatındadır — oxuyucu (`io_data.read_sheet`) formatı
faylın başlığından təyin edir.

## Yeniləmə
```
python3 -m policyunit.io_data --refresh     # stat.gov.az-dan yenidən endirir (≤1 sorğu/san, 20 san timeout)
POLICY_NO_NETWORK=1 python3 -m policyunit.io_data   # yalnız keş; MD5 manifestini çap edir
```
`POLICY_NO_NETWORK=1` olduqda heç bir şəbəkə sorğusu edilmir; keşdə olmayan fayl üçün Azərbaycan dilində xəta verilir.
Endirmə uğursuz olarsa köhnə keş saxlanılır. Növbəti benchmark cədvəli (2026) DSK tərəfindən ~2029–2030-da gözlənilir:
`io_data.YEARS`-ə il əlavə edin və `--refresh` işə salın.

## Digər mənbələr (yalnız oxunur, kopyalanmır)
- `MicroUnit/output/FR1_annual_raw.csv` — 2025 GRAS yeniləməsinin hədəfləri (sektor ƏDV və buraxılışı).
- `MicroUnit/output/FR10_branch_history.csv` — emal və mədənçıxarma bölmələrinin IO sektorlarına bölünməsi üçün
  sənaye işçilərinin sayı (NACE bölmələri üzrə); `FR10_branch_scorecard.csv` — rəqabətlilik əlaqəsi.
