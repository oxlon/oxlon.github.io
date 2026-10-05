# FR12 business register — input file / Biznes reyestri — giriş faylı

## AZ

**SİNTETİK MƏLUMAT — real müəssisə məlumatı deyil.** `FR12_business_register_SYNTHETIC.*` fayllarında heç bir real müəssisə,
VÖEN və ya real rəqəm yoxdur. Fayl FR12 modulunun B qatını (müəssisə səviyyəsində rəqabət mühərriki) yoxlamaq üçün təsadüfi,
lakin DSK-nın aqreqat göstəriciləri ilə uzlaşdırılmış qaydada yaradılmışdır (bölmələr və regionlar üzrə yaradılan və ləğv edilən
vahidlər, 2025-ci ilin sonuna vahidlərin sayı, bölmələr üzrə buraxılış, KOS-un payı). Nəticələr yalnız texniki nümayişdir, təhlil
nəticəsi deyil. `weight` sütunu sətrin neçə eyni müəssisəni təmsil etdiyini göstərir (sintetik faylda mikro və kiçik müəssisələr
qruplaşdırılıb); real reyestrdə bu sütun olmaya və ya 1 ola bilər.

**Faylı necə əvəz etmək olar.** Nazirliyin öz reyestrini eyni sxemdə `data/business_register/FR12_business_register.csv` (və ya
`.xlsx`, `data` vərəqi) kimi saxlayın və ya `BUSREG_PATH` mühit dəyişənində faylın yolunu göstərin, sonra `FR12.ipynb`-ni yenidən
icra edin. Sütun adları ingilis və ya Azərbaycan dilində ola bilər (`FR12_business_register_column_map.csv`). `data_status` sütunu
olmadıqda və ya dəyəri sintetik qeyddən fərqli olduqda məlumat REAL sayılır. Nümunə sətri olan şablon:
`FR12_business_register_TEMPLATE.csv/.xlsx` (nümunə sətri silin).

**Yoxlama (validator).** Məcburi sütunlar, rəqəmsal və mənfi olmayan gəlir və işçi sayı, təkrarlanan müəssisə-il, NACE bölməsi,
region, mülkiyyət, ölçü qrupu, status, qeydiyyat və ləğvetmə tarixlərinin ardıcıllığı, ixrac ≤ gəlir. Hər səhv sətir və sahə üzrə
`output/FR12_business_register_validation_report.csv`-də yazılır; ciddi səhvlər icranı dayandırır, xəbərdarlıqlar dayandırmır.

**Məxfilik.** Müəssisə identifikatorları psevdonimləşdirilmiş qalmalıdır (VÖEN yox); real məlumatla nəticələr yalnız Nazirliyin
öz sistemində saxlanılır. Real adlı faylı bu layihəyə köçürməyin.

**Real reyestr yükləndikdə dəyişən nəticələr.** `FR12_SYNTHETIC_*.csv` əvəzinə `FR12_FIRM_*.csv` (su nişanı olmadan): NACE × region
üzrə HHI, CR4/CR8, entropiya, Gini, payların dəyişkənliyi, giriş/çıxış, sağ qalma, gənc müəssisələrin payı, marja və Boone
indikatoru; MIIS-də V7 görünüşü aktivləşir. A qatının nəticələri dəyişmir.

## EN

**SYNTHETIC DATA — not real enterprise data.** The `FR12_business_register_SYNTHETIC.*` files contain no real enterprise, no VÖEN
and no real figure. They were generated at random, but calibrated to DSK aggregates (units created and liquidated by NACE section
and by region, units at end-2025, output by section, SME shares), to test FR12 Layer B (the firm-level competition engine). Results
are a pipeline demonstration, not findings. Column `weight` gives the number of identical enterprises a row stands for (micro and
small units are grouped in the synthetic file); a real register may omit it or set it to 1.

**How to replace it.** Save the Ministry's register in the same schema as `data/business_register/FR12_business_register.csv`
(or `.xlsx`, sheet `data`), or set the environment variable `BUSREG_PATH` to the file, then re-run `FR12.ipynb`. Headers may be
English or Azerbaijani (`FR12_business_register_column_map.csv`). A file without a `data_status` column, or whose value differs
from the synthetic marker, is treated as REAL. Template with one example row: `FR12_business_register_TEMPLATE.csv/.xlsx`.

**What the validator checks.** Required columns, numeric non-negative revenue and employees, duplicate firm-years, NACE division,
region, ownership, size class, status, order of registration and liquidation dates, exports ≤ revenue. Every issue is written per
row and field to `output/FR12_business_register_validation_report.csv`; hard errors stop the run with a message, warnings do not.

**Confidentiality.** Keep firm identifiers pseudonymised (never the VÖEN); with real data the outputs stay inside the Ministry's
system. Do not copy a real-named file into this project.

**What changes once the real register is loaded.** `FR12_FIRM_*.csv` replace `FR12_SYNTHETIC_*.csv` (no watermark): HHI, CR4/CR8,
entropy, Gini, share instability, entry/exit, survival, young-firm share, margins and the Boone indicator by NACE × region; the
MIIS view V7 becomes active. Layer-A results do not change.
