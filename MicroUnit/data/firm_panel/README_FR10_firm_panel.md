# FR10 firm panel — input file / Müəssisə paneli — giriş faylı

## AZ

**DİQQƏT: `FR10_firm_panel_SYNTHETIC.*` faylları SİNTETİKDİR. Onlarda heç bir real müəssisə, VÖEN və ya real rəqəm yoxdur.**
Fayl FR10 modulunun B qatını (müəssisə səviyyəsində hesablama mühərriki) yoxlamaq üçün təsadüfi, lakin DSK sahə
göstəriciləri ilə uzlaşdırılmış qaydada yaradılmışdır (müəssisələrin sayı, buraxılış, işçilərin sayı və əmək haqqı).
Nəticələr yalnız texniki nümayişdir, təhlil nəticəsi deyil. v2: balans və mənfəət-zərər maddələri məlum parametrli struktur
qatla yaradılır (ixrac, əlavə dəyər payı və marja, istehsal funksiyası, investisiya), ona görə müəssisə səviyyəsində
ekonometrik modellər (`output/FR10_SYNTHETIC_econ_*.csv`) həqiqi parametrləri bərpa edə bilir — sintetik məlumat — texniki nümayiş.

**Faylı necə əvəz etmək olar.** Nazirliyin öz məlumatlarını eyni sxemdə `data/firm_panel/FR10_firm_panel.csv` (və ya
`.xlsx`, `data` vərəqi) kimi saxlayın və ya `FIRM_PANEL_PATH` mühit dəyişənində faylın yolunu göstərin, sonra
`FR10.ipynb`-ni yenidən icra edin. Sütun adları ingilis və ya Azərbaycan dilində ola bilər
(`FR10_firm_panel_column_map.csv`). `data_status` sütunu olmadıqda və ya onun dəyəri sintetik qeyddən fərqli olduqda
məlumat REAL sayılır. Nümunə sətri olan şablon: `FR10_firm_panel_TEMPLATE.csv/.xlsx`.

**Yoxlama (validator).** Məcburi sütunların olması, rəqəmsal dəyərlər, mənfi dəyərlər, təkrarlanan müəssisə-il, NACE kodu,
region, mülkiyyət növü, balans bərabərliyi (kapital + öhdəliklər = aktivlər), aktivlər ≥ dövriyyə + uzunmüddətli aktivlər,
pul + debitor + ehtiyat ≤ dövriyyə aktivləri, ixrac ≤ gəlir, faizli borc ≤ öhdəliklər; xəbərdarlıq: EBIT uyğunsuzluğu,
bölüşdürülməmiş mənfəətin olmaması. Hər səhv sətir və sahə üzrə `output/FR10_firm_panel_validation_report.csv`-də
yazılır; ciddi səhvlər icranı dayandırır, xəbərdarlıqlar dayandırmır.

**Məxfilik.** Müəssisə identifikatorları psevdonimləşdirilmiş qalmalıdır; real məlumatla nəticələr yalnız Nazirliyin
öz sistemində saxlanılır.

**Real məlumat yükləndikdə dəyişən nəticələr.** `FR10_SYNTHETIC_*.csv` əvəzinə `FR10_FIRM_*.csv` (su nişanı olmadan):
maliyyə əmsalları, Altman Z''-EM, TFP indeksi, NACE × region üzrə HHI/CR4, giriş/çıxış, həmyaşıd müqayisəsi, müəssisə
proqnozları, müəssisə səviyyəsində ekonometrik modellər (`FR10_FIRM_econ_*.csv`); MIIS-də V12 "Müəssisə görünüşü" aktivləşir.
A qatının nəticələri dəyişmir.

## EN

**WARNING: the `FR10_firm_panel_SYNTHETIC.*` files are SYNTHETIC. They contain no real enterprise, no VÖEN and no real
figure.** They were generated at random, but consistent with DSK branch aggregates (enterprise counts, output, headcount
and wages), to test FR10 Layer B (the firm-level engine). Results are a pipeline demonstration, not findings. v2: the
balance-sheet and P&L items come from a structural layer with known parameters (exports, value-added share and margin,
production function, investment), so the firm-level econometric models (`output/FR10_SYNTHETIC_econ_*.csv`) can be checked
against the truth.

**How to replace it.** Save the Ministry's data in the same schema as `data/firm_panel/FR10_firm_panel.csv` (or `.xlsx`,
sheet `data`), or set the environment variable `FIRM_PANEL_PATH` to the file, then re-run `FR10.ipynb`. Headers may be
English or Azerbaijani (`FR10_firm_panel_column_map.csv`). A file without a `data_status` column, or whose value differs
from the synthetic marker, is treated as REAL. Template with one example row: `FR10_firm_panel_TEMPLATE.csv/.xlsx`.

**What the validator checks.** Required columns present, numeric values, no negative values, no duplicate firm-year,
valid NACE division, region and ownership, balance identity (equity + liabilities = assets), assets ≥ current + fixed
assets, cash + receivables + inventories ≤ current assets, exports ≤ revenue, interest-bearing debt ≤ liabilities;
warnings: EBIT inconsistent with revenue − costs, retained earnings missing. Every issue is written per row and field to
`output/FR10_firm_panel_validation_report.csv`; hard errors stop the run with a message, warnings do not.

**Confidentiality.** Keep firm identifiers pseudonymised; with real data the outputs stay inside the Ministry's system.

**What changes once real data are loaded.** `FR10_FIRM_*.csv` replace `FR10_SYNTHETIC_*.csv` (no watermark): financial
ratios, Altman Z''-EM, TFP index, HHI/CR4 by NACE × region, entry/exit/survival, peer benchmarking, firm forecasts and the
firm-level econometric models (`FR10_FIRM_econ_*.csv`); the MIIS
view V12 "Firm view" becomes active. Layer-A results do not change.
