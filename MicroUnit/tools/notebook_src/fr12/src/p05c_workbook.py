# %% [markdown]
# ### 5.3 İş kitabının vərəqləri, FR1 və FR10
#
# İş kitabından: vergi ödəyicilərinin ölçü qrupları və sektorlar üzrə fəal vergi ödəyiciləri (`DVX üzrə göstəricilər`),
# verilmiş lisenziyalar (`Verilmiş lisenziyalar`, bazara giriş baryerinin proksisi) və yoxlamalar (`Aparılan yoxlamalar`),
# 2015–2025. Region panelləri (statistik vahidlər, yeni, ləğv edilmiş, 2021–2025) FR10-un regional və bölmə proqnozları
# kimi **FR10-dan təkrar istifadə olunur** (`FR10_regional_entry_exit.csv`). FR1 sektorların real əlavə dəyərini, krediti
# və kredit faiz dərəcəsini (tarixi məlumatlar və üç ssenari), habelə Əsas ssenari üzrə 500 çəkilişini verir.

# %%
_wb = openpyxl.load_workbook(XL, read_only=True, data_only=True)
def wb_mat(sheet):
    ws = _wb[sheet]; n = ws.max_column
    return [list(r) + [None] * (n - len(r)) for r in ws.iter_rows(values_only=True)]
def wb_yearcols(mat, scan=6):
    best = {}
    for i in range(min(scan, len(mat))):
        yc = {}
        for j, v in enumerate(mat[i]):
            if isinstance(v, (int, float)) and not isinstance(v, bool) and float(v).is_integer() and 1990 <= v <= 2035: yc[j] = int(v)
            elif isinstance(v, str):
                m = re.match(r'\s*((?:19|20)\d\d)(-c[iıuü] il)?\s*$', v)
                if m: yc[j] = int(m.group(1))
        if len(yc) > len(best): best = yc
    return best
def wb_rows(sheet, pats):
    mat = wb_mat(sheet); yc = wb_yearcols(mat); out, lab = {}, {}
    for nm, pat in pats.items():
        hits = [i for i, row in enumerate(mat) if row[0] and re.search(pat, az_lower(str(row[0])).strip())]
        assert hits, f'{sheet}: /{pat}/ not found'
        i = hits[0]; out[nm] = pd.Series({y: to_num(mat[i][j]) for j, y in yc.items()}).sort_index(); lab[nm] = (i + 1, str(mat[i][0])[:60])
    return pd.DataFrame(out), lab

DVXC = {}
for cl, az in [('large', 'iri'), ('medium', 'orta'), ('small', 'kiçik'), ('micro', 'mikro'), ('budget', 'büdcə təşkilatları')]:
    pre = rf'^{az} vergi ödəyici' if cl != 'budget' else r'^büdcə təşkilatları üzrə'
    d_, _ = wb_rows('DVX üzrə göstəricilər', {'count': pre + (r'lərin sayı' if cl != 'budget' else r' vergi ödəyicilərin sayı'),
                                               'turnover': pre + r'.*dövriyyə', 'receipts': pre + r'.*daxilolma', 'employees': pre + r'.*işçi sayı'})
    DVXC[cl] = d_
DVXC = pd.concat(DVXC, axis=1).dropna(how='all')
TAXP, TAXP_LAB = wb_rows('DVX üzrə göstəricilər', {'all': r'^aktiv vergi ödəyiciləri$', 'IND': r'^sənaye üzrə aktiv', 'AGR': r'^kənd təsərrüfatı üzrə aktiv',
                                                   'CON': r'^tikinti üzrə aktiv', 'TRD': r'^ticarət üzrə aktiv', 'ICT': r'^informasiya və rabitə üzrə aktiv'})
TAXP = TAXP.dropna(how='all')
LIC_M = wb_mat('Verilmiş lisenziyalar'); _yc = wb_yearcols(LIC_M)
LIC = pd.DataFrame({str(r[0]).strip()[:60]: {y: to_num(r[j]) for j, y in _yc.items()} for r in LIC_M[2:26] if r[0]}).T
LIC_NEW = pd.Series({y: to_num(r[j]) for r in LIC_M if r[0] and az_lower(str(r[0])).strip().startswith('yeni lisenziya') for j, y in _yc.items()})
INS_M = wb_mat('Aparılan yoxlamalar'); _yc2 = wb_yearcols(INS_M)
INSP = pd.DataFrame({str(r[0]).strip()[:60]: {y: to_num(r[j]) for j, y in _yc2.items()} for r in INS_M[2:] if r[0] and r[1] == 'ədəd'}).T
LIC_MAP = {'tibb': 'HEA', 'əczaçılıq': 'HEA', 'təhsil': 'EDU', 'rabitə': 'ICT', 'yüklərin': 'TRA', 'yanacaqdoldurma': 'TRD',
           'tikintisinə': 'CON', 'lift': 'CON', 'baytarlıq': 'AGR', 'bitki': 'AGR', 'ovçuluq': 'AGR'}
LIC['group'] = [next((g for k, g in LIC_MAP.items() if k in az_lower(i)), 'OTH') for i in LIC.index]
LIC_G = LIC.groupby('group').sum().T.loc[2016:LAST_ACT]
print(f'DVX size classes {DVXC.index.min()}-{DVXC.index.max()}; active taxpayers by sector {TAXP.index.min()}-{TAXP.index.max()}; '
      f'licences {LIC_G.index.min()}-{LIC_G.index.max()} ({len(LIC)} types); inspections {len(INSP)} bodies')

# FR1 and FR10
FR1H = pd.read_csv(OUT / 'FR1_analysis_dataset.csv', index_col=0)
FR1F = pd.read_csv(OUT / 'FR1_forecast_full.csv').rename(columns={'Unnamed: 0': 'year'})
FR1D = pd.read_csv(OUT / 'FR1_fan_draws.csv')
def reg_key(name):
    s = az_lower(str(name)).strip()
    for k, (pe, pa) in REG_PAT.items():
        if re.search(pe, s) or re.search(pa, s): return k
    raise KeyError(name)
RG = pd.read_csv(OUT / 'FR10_regional_entry_exit.csv'); RG['region'] = RG.region.map(reg_key)
FR10_REGF = pd.read_csv(OUT / 'FR10_forecast_regions.csv', header=[0, 1], index_col=[0, 1])
FR10_REGF = FR10_REGF['output_mn_AZN'].rename(columns=reg_key); FR10_REGF.index = FR10_REGF.index.set_names(['scenario', 'year'])
FR10_REGF = FR10_REGF.reset_index().dropna(subset=['year']); FR10_REGF['year'] = FR10_REGF.year.astype(int)
FR10_REGH = pd.read_csv(OUT / 'FR10_regional_history.csv'); FR10_REGH = FR10_REGH[FR10_REGH.series == 'output_mn_AZN'].copy()
FR10_REGH['region'] = FR10_REGH.unit.map(reg_key)
FR10_SECF = pd.read_csv(OUT / 'FR10_forecast_sections.csv')
FR10_SH = pd.read_csv(OUT / 'FR10_branch_shares_history.csv')
assert RG.region.nunique() == 14 and set(RG.year) == set(range(2021, 2026))
_rg = RG.groupby('year')[['enterprises', 'new', 'liquidated']].sum()
for y in [2021, 2024, 2025]:
    t = FLOW_TOT[(FLOW_TOT.kind == 'region') & (FLOW_TOT.year == y) & (FLOW_TOT.period == 'FY')].iloc[0]
    assert abs(_rg.loc[y, 'new'] - t.published_new) < 1 and abs(_rg.loc[y, 'enterprises'] - t.published_stock) < 1
print(f'FR10 region panel: 14 regions x 2021-2025; equals the DSK register (2_3) totals in 2021, 2024 and 2025; '
      f'FR1 history {FR1H.index.min()}-{FR1H.index.max()}, {FR1D.draw.nunique()} FR1 draws')
