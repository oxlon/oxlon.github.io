# %% [markdown]
# ## Hissə 8 — Göstəricilər sistemi: hansı məlumatlar, hansı mənbədən, hansı göstərici üçün, hansı formada
#
# Tələb icraçıdan hansı analitik göstərici üçün hansı mənbədən hansı məlumatların istifadə olunduğunu və onların
# istifadəçiyə necə çatdığını **konkret** göstərməyi xahiş edir. Aşağıdakı məlumat–mənbə matrisində
# (`output/FR10_data_source_matrix.csv`) hər göstəriciyə bir sətir ayrılıb. "Hazırda mövcud olan illər" sütunu əl ilə
# yazılmır, **Hissə 4–5-də oxunan fayllardan hesablanır**. Vəziyyət: *hazırda mövcuddur* (iş kitabındadır və ya bu gün
# DSK-dan yüklənə bilər), *sorğu edilib* (24 avqust 2026 tarixli məlumat sorğusundadır, hələ alınmayıb), *mövcud deyil*
# (heç bir mənbə onu dərc etmir; alternativ göstərilir).

# %%
def cov(x):
    if isinstance(x, str): return x
    s = x.dropna(how='all') if isinstance(x, pd.DataFrame) else x.dropna()
    yrs = [int(y) for y in s.index if isinstance(y, (int, np.integer)) and 1990 <= y <= 2035]
    return f'{min(yrs)}-{max(yrs)}' if yrs else 'n/a'
MX = []
def mrow(pillar, az, en, formula, unit, inst, dataset, gran, freq, years, status, integ, use, form, upd, alt=''):
    MX.append(dict(pillar=pillar, indicator_az=az, indicator_en=en, formula=formula, unit=unit, source_institution=inst,
                   dataset_table_row=dataset, granularity=gran, frequency=freq, years_available_now=cov(years), status=status,
                   integration_into_MIIS=integ, analytical_use=use, presentation_form=form, update_frequency=upd,
                   alternative_if_unavailable=alt))
DL, WB_, DSA = 'file download (DSK xls, scheduled)', 'workbook upload (Ministry of Economy)', 'data-sharing agreement + secure API'
MP = 'market position'
mrow(MP, 'Sahənin sənaye məhsulunda payı', 'Branch share of industrial output', 'GO_b / sum GO', '%', 'DSK', 'industry 010', 'branch (30)', 'annual', GO, 'available now', DL, 'share system, HHI (Parts 7, 11)', 'ranking table; time series with fan', 'annual (DSK release)')
mrow(MP, 'Emal sənayesində sahənin payı', 'Branch share of manufacturing output', 'GO_b / GO_C', '%', 'DSK', 'industry 010', 'branch (24)', 'annual', GO[MANUF], 'available now', DL, 'MNL share system (Part 11), forecast', 'stacked area; fan chart', 'annual')
mrow(MP, 'Konsentrasiya indeksi (HHİ, CR4) — sahələr', 'Concentration across branches (HHI, CR4)', 'sum s^2 x 10^4; top-4 share', 'index; %', 'DSK', 'industry 010 (derived)', 'industry / manufacturing', 'annual', GO, 'available now', DL, 'market-structure KPI, forecast', 'dashboard KPI card', 'annual')
mrow(MP, 'Müəssisə səviyyəsində HHİ', 'Firm-level HHI / CR4 by NACE x region', 'sum firm s^2 within cell', 'index', 'DVX / DSMF', 'enterprise panel (requested 24.08.2026)', 'firm', 'annual', 'none', 'requested', DSA, 'Layer B concentration', 'heat map NACE x region', 'annual', 'lower bound from DSK register large-unit count and SME output share (Part 7.1)')
mrow(MP, 'Qeyri-dövlət bölməsinin payı', 'Non-state share of output by branch', 'non-state output / output', '%', 'DSK', 'industry 010_2', 'branch', 'annual', NS, 'available now', DL, 'ownership composition forecast (Part 14)', 'time series; KPI card', 'annual')
mrow(MP, 'Fəaliyyət göstərən müəssisələrin sayı', 'Active enterprises by branch and ownership', 'count', 'units', 'DSK', 'industry 004-007-008 sheet 4;7', 'branch x ownership', 'annual', NENT, 'available now', DL, 'entry/net-entry rates, determinants panel', 'ranking table', 'annual')
mrow(MP, 'Ölçü qrupları üzrə müəssisələr', 'Enterprises by size class', 'count by micro/small/medium-large', 'units', 'DSK', 'industry 004-007-008 sheet 8', 'branch x size', 'annual', SIZE.set_index('year').n, 'available now', DL, 'size structure, concentration bound', 'stacked bar', 'annual')
mrow(MP, 'KOB-ların payı (buraxılış, məşğulluq, investisiya)', 'SME share of output, employment, investment', 'SME value / total', '%', 'DSK', 'entrepreneurship 001_1, 012, 013, 015', 'section x size', 'annual', '2023-2024', 'available now (2 years)', DL, 'held constant (not identifiable, F11)', 'KPI card', 'annual', 'DVX taxpayer size classes r111-r126 (2022-2025)')
mrow(MP, 'Vergi ödəyicilərinin ölçü qrupları', 'Taxpayer size classes: count, turnover, employees', 'by large/medium/small/micro', 'units; mn AZN; thsd', 'DVX', "workbook 'DVX üzrə göstəricilər' r111-r126", 'size class', 'annual', DVX.large_n, 'available now', WB_, 'size structure cross-check', 'table', 'annual')
mrow(MP, 'Regionun sənaye məhsulunda payı', 'Regional share of industrial output', 'GO_r / sum GO_r', '%', 'DSK', 'industry 022 (and 023 volume index)', 'economic region (14)', 'annual', REG_GO, 'available now', DL, 'regional share system (Part 12)', 'map; region x year heat map', 'annual')
mrow(MP, 'Regionlarda qeyri-dövlət payı', 'Non-state share of industrial output by region', 'published', '%', 'DSK', 'industry 024', 'region', 'annual', REG_NS, 'available now', DL, 'regional ownership profile', 'map', 'annual')
mrow(MP, 'Regionlarda müəssisələrin sayı', 'Industrial enterprises by region', 'count', 'units', 'DSK', 'industry 021', 'region', 'annual', REG_NENT, 'available now', DL, 'regional entry dynamics', 'map', 'annual')
mrow(MP, 'Yeni yaradılmış / ləğv edilmiş müəssisələr (regionlar)', 'New and liquidated enterprises by region (all sectors)', 'new / stock; liquidated / stock', '%', 'DSK via workbook', "workbook 'Regionlar*' rows 'Müəssisə və təşkilatların sayı', 'Yeni yaradılmış', 'Ləğv edilmiş'", 'region', 'annual', RG_WB.set_index('year').value, 'available now', WB_, 'entry/exit rates', 'map; table', 'annual')
mrow(MP, 'Yaradılmış və ləğv edilmiş vahidlər (fəaliyyət növləri)', 'Created and liquidated statistical units by activity', 'new / units; liquidated / units', '%', 'DSK', 'st_units 2_1-2_3 (snapshot 1 Jul 2026)', 'section, region, ownership', 'semi-annual snapshot', 'H1 2026', 'available now (snapshot)', DL, 'entry/exit rates', 'table', 'semi-annual', 'DVX register flows (requested)')
mrow(MP, 'Əsas məhsulların natura ilə istehsalı', 'Main products in physical units', 'volume', 'tonnes, units', 'DSK', 'industry 018; product lists in 014_x, 015_x, 016, 017', 'product (~140) x branch', 'annual', PROD.set_index('label')[[c for c in PROD.columns if isinstance(c, (int, np.integer))]].T, 'available now', DL, 'product view, growth ranking', 'product table with sparklines', 'annual')
mrow(MP, 'Regionlar üzrə məhsullar', 'Main products by place of production; product location shares', 'volume; place / national', 'tonnes, units; %', 'DSK', 'industry 018_1 (2011-2025), 018_2 (2019-2025); 017_1 (to 2022)', 'product x city/district', 'annual', '2011-2025', 'available now', DL, 'product market shares by place, HHI across places (Part 14.3)', 'map; product table', 'annual')
mrow(MP, 'Sahələr üzrə ixrac', 'Exports by branch (export orientation)', 'exports / output', '%', 'State Customs Committee (DGK)', 'HS-level exports (not in project)', 'branch / product', 'monthly', 'none', 'not available', DSA + ' with DGK; HS-NACE concordance', 'share-system driver, determinants panel', 'scatter; time series', 'monthly', 'industrial-park exports (workbook Park, 2019-2025); DSK shipped goods 011 is not exports')
mrow(MP, 'Sənaye parkları: istehsal, ixrac, iş yerləri', 'Industrial parks and zones: output, exports, jobs, investment', 'published', 'mn AZN; persons', 'Industrial-park operators (İZİA, Ministry of Economy)', "workbook 'Park'", 'park', 'quarterly', PARKS.set_index('year').value, 'available now', WB_, 'park performance', 'table; KPI card', 'quarterly')
mrow(MP, 'İnvestisiya təşviqi sənədləri', 'Investment promotion certificates: projects, jobs, value', 'count, value', 'units; mn AZN', 'Ministry of Economy', "workbook 'İnvestisiya təşviqi sənədi '", 'national', 'annual', '2016-2025', 'available now', WB_, 'support-measure context', 'table', 'annual')
mrow(MP, 'KOBİA dəstək xidmətləri', 'SME agency (KOBİA) support services', 'counts', 'units; thsd AZN', 'KOBİA', "workbook 'KOBİA'", 'national / SME house', 'annual', '2021-2025', 'available now', WB_, 'support-measure context', 'table', 'annual')
print(f'{len(MX)} market-position indicators')
