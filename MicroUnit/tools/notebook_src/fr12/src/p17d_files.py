# %% [markdown]
# ### 17.3.1 `data/business_register/` qovluğundakı əvəz edilə bilən giriş faylları
#
# Generator **yalnız SYNTHETIC adlı faylları**, şablonu və sütun xəritəsini yazır; o, Nazirliyin öz reyestri üçün ayrılmış
# `FR12_business_register.csv/.xlsx` adlı faylı heç vaxt yaratmır və üzərinə yazmır. Fayllar yalnız məzmunu dəyişdikdə
# yenidən yazılır. Hər məlumat sətrinin birinci sütununda `SYNTHETIC — not real enterprise data` (*SİNTETİK — real müəssisə
# məlumatı deyil*) yazılır; müəssisə identifikatorları `SYN-…` formasındadır.

# %%
import hashlib
SYN_CSV = BRDIR / 'FR12_business_register_SYNTHETIC.csv'; SYN_XLSX = BRDIR / 'FR12_business_register_SYNTHETIC.xlsx'
_blob = SYN.to_csv(index=False).encode('utf-8')
_changed = not SYN_CSV.exists() or hashlib.sha256(SYN_CSV.read_bytes()).hexdigest() != hashlib.sha256(_blob).hexdigest()
GEN_WRITTEN = []                                 # every file name the generator writes (checked by the swap tests)
if _changed: SYN_CSV.write_bytes(_blob)
GEN_WRITTEN.append(SYN_CSV.name)
COLMAP = BR_SCHEMA.rename(columns={'field': 'column_en', 'field_az': 'column_az'})[['column_en', 'column_az', 'type', 'unit', 'required', 'constraint', 'source']]
COLMAP.to_csv(BRDIR / 'FR12_business_register_column_map.csv', index=False); GEN_WRITTEN.append('FR12_business_register_column_map.csv')
TEMPLATE = pd.DataFrame([dict(data_status='EXAMPLE ROW — delete before use / NÜMUNƏ SƏTİR — istifadədən əvvəl silin', firm_id='F000001', year=2025, nace2='47',
                              region='Baku city', ownership='private', size_class='small', revenue=1250.0, employees=18, registration_date='2017-03-15',
                              liquidation_date='', status='active', legal_form='LLC', exports=0.0, product_codes='', cost_of_sales=900.0,
                              operating_costs=150.0, weight=1)])[BR_COLS]
TEMPLATE.to_csv(BRDIR / 'FR12_business_register_TEMPLATE.csv', index=False); GEN_WRITTEN.append('FR12_business_register_TEMPLATE.csv')
README_BR = """# FR12 business register — input file / Biznes reyestri — giriş faylı

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
"""
(BRDIR / 'README_FR12_business_register.md').write_text(README_BR, encoding='utf-8'); GEN_WRITTEN.append('README_FR12_business_register.md')
README_SHEET = pd.DataFrame({'README': ['SİNTETİK MƏLUMAT — real müəssisə məlumatı deyil / SYNTHETIC DATA — not real enterprise data'] + README_BR.split('\n')})
def write_xlsx(path, data, readme=True):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook(write_only=False); ws = wb.active; ws.title = 'README'
    if readme:
        for v in README_SHEET.README: ws.append([v])
        ws['A1'].font = Font(bold=True, size=14, color='C00000'); ws.column_dimensions['A'].width = 120
    else:
        ws.append(['TEMPLATE — schema of the DSK business register extract for FR12 / FR12 üçün biznes reyestri çıxarışının şablonu'])
    wd = wb.create_sheet('data'); wd.append(list(data.columns))
    for row in data.itertuples(index=False): wd.append([None if (isinstance(v, float) and v != v) else v for v in row])
    sc = wb.create_sheet('schema'); sc.append(list(COLMAP.columns))
    for row in COLMAP.itertuples(index=False): sc.append(list(row))
    wb.save(path); GEN_WRITTEN.append(Path(path).name)
if _changed or not SYN_XLSX.exists(): write_xlsx(SYN_XLSX, SYN)
write_xlsx(BRDIR / 'FR12_business_register_TEMPLATE.xlsx', TEMPLATE, readme=False)
real_named = [p.name for p in BRDIR.glob('FR12_business_register.*')]
print(f"data/business_register: {sorted(p.name for p in BRDIR.iterdir() if not p.name.startswith('.'))}; real-named file present: {real_named or 'none'}; "
      f"synthetic files {'rewritten' if _changed else 'unchanged'}")
