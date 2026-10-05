# %% [markdown]
# ### 5.2 Sahibkarlıq cədvəlləri (cari və arxivləşdirilmiş buraxılışlar) və istehsal hesabı
#
# Hər sahibkarlıq cədvəli iki il üzrə məlumat verir; üç buraxılış 2019, 2020, 2022, 2023 və 2024-cü illəri əhatə edir. İki
# buraxılış eyni ili (2023) əks etdirdikdə **sonrakı** buraxılış istifadə olunur və yenidənbaxma qeydə alınır (Hissə 6).
# İstehsal hesabı və gəlirlərin formalaşması hesabı (milli hesablar `013`) 2005-ci ildən etibarən hər NACE bölməsi üzrə
# buraxılışı, əlavə dəyəri, əməyin ödənilməsini və ümumi əməliyyat mənfəətini verir: bu, sektorun **qiymət-xərc marjası
# proksisinin** mənbəyidir: PCM = (əlavə dəyər − muzdlu işçilərin əməyinin ödənilməsi) / buraxılış.

# %%
def year_header(path, rows=6):
    sh = xlrd.open_workbook(path).sheet_by_index(0)
    for r in range(min(rows, sh.nrows)):
        ys = [int(v) for v in sh.row_values(r) if isinstance(v, (int, float)) and 2000 <= v <= 2035 and float(v).is_integer()]
        ys += [int(m.group(1)) for v in sh.row_values(r) if isinstance(v, str) for m in [re.fullmatch(r'\s*(20\d\d)\s*', v)] if m]
        if len(ys) >= 2: return sorted(ys)
    raise AssertionError(f'{path}: no year header')

def ent_table(path, width):
    '''Two-year entrepreneurship table: rows = 11 activity groups (+ total), `width` numbers per year.'''
    yrs = year_header(path)
    data = [(l, n) for r, l, n in sheet_rows(path) if l and len(n) >= 2 * width]
    labs = [l for l, _ in data]; out = []
    for g in ['TOT'] + GRP:
        pat = r'total for types' if g == 'TOT' else GROUPS[g][1]
        if g == 'TRA': pat = r'transportation'
        n = data[match_unique(labs, pat, f'{path.name} {g}')][1]
        for k, y in enumerate(yrs):
            out.append(dict(group=g, year=y, vals=[0.0 if v != v else v for v in n[k * width:(k + 1) * width]]))
    return out

def ent_series(fn, width, names):
    recs = {}
    for p in [VD / f'e{fn}_v2022.xls', VD / f'e{fn}_v2025.xls', DDIR / 'entrepreneurship' / f'{fn}en.xls']:
        if not p.exists(): continue
        for r in ent_table(p, width):
            recs[(r['group'], r['year'])] = dict(zip(names, r['vals'])) | {'vintage': p.name}
    d = pd.DataFrame(recs).T; d.index.names = ['group', 'year']
    return d

E006 = ent_series('006', 3, ['registered', 'new', 'dereg'])
E012 = ent_series('012', 4, ['sme', 'micro', 'small', 'medium'])          # % of output
E013 = ent_series('013', 4, ['sme', 'micro', 'small', 'medium'])          # % of employees
E024 = ent_series('024', 4, ['age1', 'age1_micro', 'age1_small', 'age1_medium'])
AGE = {}
for k, fn in enumerate(['024', '025', '026', '027', '028'], start=1):
    for r in ent_table(DDIR / 'entrepreneurship' / f'{fn}en.xls', 4):
        AGE[(r['group'], r['year'], k)] = r['vals'][0]
AGE = pd.Series(AGE).unstack(2); AGE.index.names = ['group', 'year']
for d_ in (E006, E012, E013, E024):
    for c in d_.columns:
        if c != 'vintage': d_[c] = d_[c].astype(float)
_rev = []   # 2023 is published in two vintages: record the revision
for p in [VD / 'e006_v2025.xls']:
    for r in ent_table(p, 3):
        if r['year'] == 2023:
            cur = E006.loc[(r['group'], 2023)]
            _rev.append(dict(group=r['group'], new_v2025=r['vals'][1], new_current=cur['new'], dereg_v2025=r['vals'][2], dereg_current=cur['dereg']))
E006_REV = pd.DataFrame(_rev)
print(f"entrepreneurship 006: groups x years = {E006.index.get_level_values(0).nunique()} x {sorted(E006.index.get_level_values(1).unique())}")
print(f"SME output shares 012: years {sorted(E012.index.get_level_values(1).unique())}; age structure 024-028: years {sorted(AGE.index.get_level_values(1).unique())}")
_t = E006.xs('TOT', level=0); _g = E006.drop('TOT', level=0).groupby(level=1)[['registered', 'new', 'dereg']].sum()
_gap = (_g - _t[['registered', 'new', 'dereg']]).abs().max().max()
print(f'11 groups add up to the published total: max gap {_gap:.0f} units')
assert _gap <= 2

# national accounts 013: production and generation of income account by section, every year
sh = xlrd.open_workbook(DDIR / 'nat_accounts' / '013en.xls').sheet_by_index(0)
NA, yr = [], None
for r in range(sh.nrows):
    row = sh.row_values(r)
    if any(isinstance(v, str) and 'IFNT' in v for v in row):
        ys = [int(m.group(1)) for v in row for m in [re.fullmatch(r'\s*(20\d\d)(?:\.0)?\s*\**\s*', str(v))] if m]
        yr = ys[0] if ys else yr
        continue
    code = str(row[1]).strip().replace('İ', 'I')
    if yr and code in SECS and 'total' not in str(row[2]).lower():
        v = [to_num(x) for x in row[3:11]]
        NA.append(dict(sec=code, year=yr, GO=v[0], IC=v[1], VA=v[2], CE=v[3], OTP=v[4], GOS=v[5], CFC=v[6]))
NA = pd.DataFrame(NA).set_index(['sec', 'year']).sort_index()
NA['PCM'] = (NA.VA - NA.CE) / NA.GO * 100           # price-cost margin proxy, % of output (Collins-Preston)
_chk = (NA.GO - NA.IC - NA.VA).abs().max()
print(f'national accounts 013: {NA.index.get_level_values(0).nunique()} sections, {NA.index.get_level_values(1).min()}-'
      f'{NA.index.get_level_values(1).max()}; identity output - IC = VA holds to {_chk:.2f} mn AZN')
assert _chk < 1.0
