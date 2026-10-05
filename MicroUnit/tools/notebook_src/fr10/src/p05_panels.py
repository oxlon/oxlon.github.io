# %% [markdown]
# ## Hissə 5 — Sahə, bölmə, region və məhsul panellərinin qurulması
#
# ### 5.1 DSK sənaye cədvəlləri əsasında sahə paneli
#
# | Sıra | DSK cədvəli | Vahid | İllər |
# |---|---|---|---|
# | Faktiki qiymətlərlə ümumi buraxılış, 30 sahə | `010` | mln manat | 1995–2025 |
# | Həcm indeksi, əvvəlki il = 100 | `009` vərəq 9.1 | % | 1990–2025 |
# | Buraxılışda dövlət / qeyri-dövlət sektorunun payı | `010_2` | % | 1997–2025 |
# | Fəaliyyət göstərən müəssisələr | `004-007-008` vərəq 4;7 | vahid | 1995–2025 |
# | Ölçü qrupları üzrə müəssisələr | `004-007-008` vərəq 8 | vahid | 2009–2025 |
# | Hazır məhsul ehtiyatları (1 yanvar) | `013` | mln manat | 1999–2025 (ilin sonu) |
# | Əsas kapitala investisiyalar (daxili / xarici) | `019` | mln manat | 2005–2025 |
# | Texnoloji innovasiyalara xərclər | `020_3` | min manat | 2005–2025 |
# | İşçilər; orta aylıq əmək haqqı | `006`, `006_2` | nəfər; manat | 2019–2025 |
#
# Real buraxılış dərc olunmuş həcm indeksindən 2015-ci il qiymətləri ilə zəncirvari üsulla hesablanır (rəsmi eynilik
# $Q_t = Q_{t-1}\,I_t/100$), sahə buraxılışının deflyatoru isə $P = $ nominal / real-dır. Uzlaşdırma xanası sahələrin
# cəminin dərc olunmuş mədənçıxarma, emal sənayesi və bütün sənaye yekunlarına bərabər olduğunu yoxlama ifadəsi ilə
# təsdiqləyir.
#
# **v2.1 — dərc olunmuş həcm indekslərinin yoxlanılması.** Kiçik sahələr üçün DSK-nın həcm indeksi bəzən sahənin öz
# nominal buraxılışı ilə uyğun gəlmir (məsələn, elektrik avadanlığı 2020: indeks 8 500%, nominal buraxılış isə 7% azalıb).
# Hər sahə indeksi zəncirvari hesablamadan əvvəl yoxlanılır (alətlər dəstindəki `validate_volume_index`): **T1** —
# nəzərdə tutulan deflyator dəyişikliyi $(N_t/N_{t-1})/(I_t/100)$ ×1/3…×3 aralığından kənardadır; **T2** — emal sənayesi
# deflyatoruna nisbətən sahə deflyatoru (2015 = 1) 1/6…6 aralığından çıxır. Testdən keçməyən indeks həmin ilin emal
# sənayesi deflyatorunun dəyişikliyi ilə deflyasiya edilmiş sahənin nominal artımı ilə əvəz olunur; hər əvəzetmə siyahıya
# alınır (F15 tapıntısı, `output/FR10_volume_index_validation.csv`) və təsirə məruz qalan real buraxılış dəyərləri
# *doldurulmuş* kimi işarələnir.

# %%
ROUND_TOL = 0.6   # per cent: DSK prints one decimal, so branch sums can miss the total by rounding
d010 = dsk_wide(P_('industry', '010en.xls'))
GO_all = branch_frame(d010).loc[1995:]                  # 1990-1994 are thousands of pre-denomination manats (F1)
GO = GO_all[BCODES]
d091 = dsk_wide(P_('industry', '009en.xls'), sheet=' 9.1')
VI_PUB = branch_frame(d091).loc[1991:]                  # as published (previous year = 100)
VI = VI_PUB.copy()
VI_FIX = []
for b in BCODES:                                         # v2.1: T1/T2 validation, fallback = nominal growth / C deflator change
    VI[b], _rep = validate_volume_index(GO[b], VI_PUB[b], GO_all['C'], VI_PUB['C'])
    VI_FIX += [dict(nace2=b, **r) for r in _rep]
VI_FIX = pd.DataFrame(VI_FIX, columns=['nace2', 'year', 'test', 'index_published', 'nominal_growth_pct', 'implied_deflator_change',
                                       'mfg_deflator_change', 'rel_deflator_if_published', 'index_used'])
Q = pd.DataFrame({b: chain_level(GO[b], VI[b]) for b in BCODES})        # real output, 2015 prices (validated indices)
Q_PUB = pd.DataFrame({b: chain_level(GO[b], VI_PUB[b]) for b in BCODES})  # as published, kept for the comparison only
Q_AGG = {a: chain_level(GO_all[a], VI[a]) for a in ['ALL', 'B', 'C']}
PDEF = GO / Q                                                              # branch output deflator, 2015 = 1

REC = []
def rec(what, a, b, years, tol=ROUND_TOL):
    gap = float(((a / b - 1).loc[years].abs().max()) * 100)
    REC.append(dict(check=what, years=f'{min(years)}-{max(years)}', max_gap_pct=round(gap, 4), tolerance_pct=tol,
                    passed=gap <= tol))
yrs_full = [y for y in GO.index if GO.loc[y].notna().all()]
rec('DSK 010: 4 mining branches = mining total', GO[MINING].sum(axis=1), GO_all['B'], yrs_full)
rec('DSK 010: 24 manufacturing branches = manufacturing total', GO[MANUF].sum(axis=1), GO_all['C'], yrs_full)
rec('DSK 010: 30 branches = all industry', GO.sum(axis=1), GO_all['ALL'], yrs_full)
print(f'branch output complete for all 30 branches in {yrs_full[0]}-{yrs_full[-1]} ({len(yrs_full)} years)')

def subrow(df, pos, pat, ahead=3):
    lab = df.label.map(az_lower)
    for j in range(pos + 1, min(pos + 1 + ahead, len(df))):
        if re.search(pat, lab.iloc[j]): return j
    return None

def branch_sub(df, pat, codes=BCODES):
    '''Sub-row (e.g. "non-state property") printed under each branch row.'''
    pos = match_rows(df, codes, aggregates=True)
    ycols = [c for c in df.columns if isinstance(c, (int, np.integer))]
    out = {}
    for k, p in pos.items():
        if p is None: continue
        j = subrow(df, p, pat)
        if j is not None: out[k] = df.iloc[j][ycols].astype(float)
    return pd.DataFrame(out).sort_index()

d102 = dsk_wide(P_('industry', '010_2en.xls'))
NS = branch_sub(d102, r'^non-state') / 100.0                 # non-state share of branch output
STATE_SH = branch_sub(d102, r'^state') / 100.0
d047 = dsk_wide(P_('industry', '004-007-008en.xls'), sheet='4;7')
NENT = branch_frame(d047)
pos_own = {lab: i for i, lab in enumerate(d047.label.map(az_lower))}
d013 = dsk_wide(P_('industry', '013en.xls'))
STK = branch_frame(d013)
STK.index = STK.index - 1                                    # "as of 1 January t+1" = end of year t
d019 = dsk_wide(P_('industry', '019-019_1en.xls'), sheet='19')
INV = branch_frame(d019)
INV_FOR = branch_sub(d019, r'^foreign')
d203 = dsk_wide(P_('industry', '020_3en.xls'))
INNOV = branch_frame(d203)
d006 = dsk_wide(P_('industry', '006en.xls')); EMP_DSK = branch_frame(d006)
d0062 = dsk_wide(P_('industry', '006_2en.xls')); WAGE_DSK = branch_frame(d0062)
INV_GAP = (INV[BCODES].sum(axis=1, min_count=1) / INV['ALL'] - 1) * 100     # finding F3 (Part 6)
rec('DSK 019: branch investment = industry total', INV[BCODES].sum(axis=1, min_count=1), INV['ALL'],
    [y for y in INV.index if y >= 2010], tol=0.6)
rec('DSK 006: branch employees = industry total', EMP_DSK[BCODES].sum(axis=1), EMP_DSK['ALL'], list(EMP_DSK.index))

# size classes (sheet 8): column groups per year, labels in the two header rows
sh8 = xlrd.open_workbook(P_('industry', '004-007-008en.xls')).sheet_by_name('8')
_yc = {c: int(sh8.cell_value(3, c)) for c in range(sh8.ncols) if isinstance(sh8.cell_value(3, c), float)}
_ystart = sorted(_yc)
SIZE = []
for i, c0 in enumerate(_ystart):
    c1 = _ystart[i + 1] if i + 1 < len(_ystart) else sh8.ncols
    labs = {c: az_lower(str(sh8.cell_value(5, c))).strip() or az_lower(str(sh8.cell_value(4, c))).strip() for c in range(c0, c1)}
    for r in range(6, sh8.nrows):
        lab = str(sh8.cell_value(r, 1)).strip()
        if not lab: continue
        for c in range(c0, c1):
            v = to_num(sh8.cell_value(r, c))
            cls = 'total' if c == c0 else labs[c].replace('of which:', '').strip()
            SIZE.append(dict(year=_yc[c0], label=lab, size_class=cls, n=v))
SIZE = pd.DataFrame(SIZE)
SIZE['size_class'] = SIZE.size_class.str.replace(r'\s+', ' ', regex=True).str.strip()
display(pd.DataFrame(REC))
assert pd.DataFrame(REC).passed.all(), 'a DSK adding-up check failed'

# %% [markdown]
# **Həcm indeksinin yoxlanılması (v2.1): hədlər və nəticə.** Hədlər birillik testin heç vaxt işarələmədiyi sahələr
# ("təmiz" sahələr) əsasında müəyyən edilir: onların birillik nəzərdə tutulan deflyator dəyişiklikləri və emal sənayesinə
# nisbətən deflyatorları aşağıda çap olunur və hədlərin daxilində olmalıdır; beləliklə, qayda qiymətləndirmə dövründə
# normal davranan sahəyə toxuna bilməz. Əvəzetmələrdən sonra hər sahənin nəzərdə tutulan deflyatoru hər il hər iki
# testdən keçməlidir.

# %%
_PC = GO_all['C'] / Q_AGG['C']                                              # manufacturing deflator, 2015 = 1
_d1 = lambda vi: (GO / GO.shift(1)) / (vi[BCODES] / 100.0)                   # one-year implied-deflator change
_clean = [b for b in BCODES if b not in set(VI_FIX[VI_FIX.test == 'T1'].nace2)]
_dc = _d1(VI_PUB).loc[1996:, _clean].stack()
_rc = (GO / Q_PUB).div(_PC, axis=0).loc[2005:LAST_ACT, _clean].stack()
VI_BANDS = dict(clean_branches=len(_clean), d1_min=float(_dc.min()), d1_max=float(_dc.max()), rel_min_2005=float(_rc.min()), rel_max_2005=float(_rc.max()))
print(f"clean branches ({len(_clean)}): one-year deflator change 1996-{LAST_ACT} within x{VI_BANDS['d1_min']:.3f} - x{VI_BANDS['d1_max']:.3f} "
      f"(band x1/{VI_BAND_1Y:g} - x{VI_BAND_1Y:g}); deflator relative to manufacturing 2005-{LAST_ACT} within "
      f"{VI_BANDS['rel_min_2005']:.3f} - {VI_BANDS['rel_max_2005']:.3f} (band 1/{VI_BAND_REL:g} - {VI_BAND_REL:g})")
assert 1 / VI_BAND_1Y < VI_BANDS['d1_min'] and VI_BANDS['d1_max'] < VI_BAND_1Y, 'T1 band would cut into the clean branches'
assert 1 / VI_BAND_REL < VI_BANDS['rel_min_2005'] and VI_BANDS['rel_max_2005'] < VI_BAND_REL, 'T2 band would cut into the clean branches'
print(f"{len(VI_FIX)} branch-year indices replaced in {VI_FIX.nace2.nunique()} branches (T1 {int((VI_FIX.test == 'T1').sum())}, "
      f"T2 {int((VI_FIX.test == 'T2').sum())}); {int((VI_FIX.year >= 2005).sum())} of them in 2005-{LAST_ACT}")
_rel = PDEF.div(_PC, axis=0).loc[1995:LAST_ACT]
_dd = _d1(VI).loc[1996:LAST_ACT]
DEFL_RANGE = pd.DataFrame({'deflator_min': PDEF.loc[1995:LAST_ACT].min(), 'deflator_max': PDEF.loc[1995:LAST_ACT].max(),
                           f'deflator_{LAST_ACT}': PDEF.loc[LAST_ACT], 'one_year_change_min': _dd.min(), 'one_year_change_max': _dd.max(),
                           'rel_to_mfg_min': _rel.min(), 'rel_to_mfg_max': _rel.max(),
                           f'real_to_nominal_{LAST_ACT}': Q.loc[LAST_ACT] / GO.loc[LAST_ACT],
                           f'real_to_nominal_{LAST_ACT}_published_index': Q_PUB.loc[LAST_ACT] / GO.loc[LAST_ACT],
                           'indices_replaced': VI_FIX.groupby('nace2').size().reindex(BCODES).fillna(0).astype(int)})
display(DEFL_RANGE.round(3))
assert (_dd.isna() | ((_dd >= 1 / VI_BAND_1Y - 1e-12) & (_dd <= VI_BAND_1Y + 1e-12))).all().all(), 'implausible one-year deflator change remains'
assert (_rel.isna() | ((_rel >= 1 / VI_BAND_REL - 1e-12) & (_rel <= VI_BAND_REL + 1e-12))).all().all(), 'implausible relative deflator remains'
_nv = [f'{b} {y}' for (y, b), v in _dd.isna().stack().items() if v]
print(f'every branch implied deflator passes T1 and T2 in every year 1996-{LAST_ACT}; not testable (no nominal output in the year before): {_nv}')

# %% [markdown]
# ### 5.2 Sahələr və bölmələr üzrə milli hesablar
#
# DSK-nın milli hesablar cədvəlləri `015`, `015_1`, `015_2` **emal sənayesinin hər sahəsi (NACE 10–33)** və dörd sənaye
# bölməsi üçün 2005–2025-ci illər üzrə **buraxılışı, aralıq istehlakı və əlavə dəyəri** verir; `013` bölmələr üzrə tam
# istehsal hesabını və gəlirlərin formalaşması hesabını (muzdlu işçilərin əməyinin ödənilməsi, istehsala digər vergilər,
# ümumi əməliyyat mənfəəti, əsas kapitalın istehlakı), 2005–2025, verir; `031` bölmələr üzrə əsas fondları verir. Bunlar
# səmərəlilik və maliyyə vəziyyəti sütunlarının giriş məlumatlarıdır.

# %%
def na_branch(fn):
    d = dsk_wide(P_('system_nat_accounts', fn))
    ycols = [c for c in d.columns if isinstance(c, (int, np.integer))]
    out = {}
    for _, r in d.iterrows():
        lab = az_lower(r.label)
        if r.code in MANUF or r.code == '06': out[r.code] = r[ycols].astype(float)
        m = re.match(r'^([bcde])\s', lab)
        if m and m.group(1).upper() not in out: out[m.group(1).upper()] = r[ycols].astype(float)
    return pd.DataFrame(out).sort_index()
NA_GO, NA_IC, NA_VA = na_branch('015en.xls'), na_branch('015_1en.xls'), na_branch('015_2en.xls')
for nm, fr in [('output', NA_GO), ('intermediate consumption', NA_IC), ('value added', NA_VA)]:
    missing = [c for c in MANUF + ['B', 'C', 'D', 'E', '06'] if c not in fr.columns]
    assert not missing, f'national accounts {nm}: branches missing {missing}'
REC2 = []
for nm, fr in [('output', NA_GO), ('value added', NA_VA)]:
    gap = float(((fr[MANUF].sum(axis=1) / fr['C'] - 1).abs().max()) * 100)
    REC2.append(dict(check=f'NA {nm}: 24 branches = manufacturing', max_gap_pct=round(gap, 4), passed=gap < ROUND_TOL))
gap = float(((NA_GO - NA_IC - NA_VA)[MANUF + ['B', 'C', 'D', 'E']].abs().max().max()))
REC2.append(dict(check='NA identity output - IC - VA (mn AZN, max abs)', max_gap_pct=round(gap, 3), passed=gap < 0.6))
gap = float(((NA_GO['C'] / GO_all['C']).loc[2005:] - 1).abs().max() * 100)
REC2.append(dict(check='NA manufacturing output vs DSK industry 010 (per cent)', max_gap_pct=round(gap, 3), passed=gap < 5))
display(pd.DataFrame(REC2))
assert pd.DataFrame(REC2).passed.all()

# production and generation of income account: one block per year
sh13 = xlrd.open_workbook(P_('system_nat_accounts', '013en.xls')).sheet_by_index(0)
INC = []; yr = None
for r in range(sh13.nrows):
    v3 = sh13.cell_value(r, 3)
    y = _yr(v3) if isinstance(v3, (str, float)) else None
    if y and isinstance(sh13.cell_value(r, 4), str) and not str(sh13.cell_value(r, 4)).strip(): yr = y; continue
    code = str(sh13.cell_value(r, 1)).strip()
    if yr and code in ('B', 'C', 'D', 'E') and 'total' not in az_lower(sh13.cell_value(r, 2)):
        vals = [to_num(sh13.cell_value(r, c)) for c in range(3, 11)]
        INC.append(dict(year=yr, sec=code, GO=vals[0], IC=vals[1], VA=vals[2], CE=vals[3], OTP=vals[4], GOS=vals[5],
                        CFC=vals[6], NOS=vals[7]))
INC = pd.DataFrame(INC).drop_duplicates(['year', 'sec']).set_index(['sec', 'year']).sort_index()
INC_RESID = (INC.VA - INC.CE - INC.OTP - INC.GOS)                 # finding F5 (Part 6)
INC_BAD = INC_RESID[INC_RESID.abs() > 0.6]
_g = INC_RESID.drop(index=INC_BAD.index).abs().max()
print(f'income account parsed: sections {sorted(INC.index.get_level_values(0).unique())}, years '
      f'{INC.index.get_level_values(1).min()}-{INC.index.get_level_values(1).max()}; identity VA = CE + OTP + GOS holds to '
      f'{_g:.2f} mn AZN except {len(INC_BAD)} section-years (Part 6, F5): '
      + ', '.join(f'{s_} {y_} {v_:+.1f}' for (s_, y_), v_ in INC_BAD.items()))
assert _g < 0.6 and len(INC_BAD.index.get_level_values(1).unique()) <= 1 and abs(INC_BAD.sum()) < 0.6
d031 = dsk_wide(P_('system_nat_accounts', '031en.xls'))
FA = {}
for _, r in d031.iterrows():
    m = re.match(r'^([bcde])\s', az_lower(r.label))
    if m: FA[m.group(1).upper()] = r[[c for c in d031.columns if isinstance(c, (int, np.integer))]].astype(float)
FA = pd.DataFrame(FA)
print(f'fixed assets by section {sorted(FA.columns)}: {FA.index.min()}-{FA.index.max()}')

# %% [markdown]
# ### 5.3 İş kitabının sənaye vərəqləri, DVX bəyannamələri, investisiya mənbələri və regionlar
#
# İş kitabının dörd sənaye vərəqi eyni 30 sahə üzrə **2016–2025**-ci illər üçün buraxılışı, əlavə dəyəri, investisiyanı,
# orta əmək haqqını və işçilərin sayını *əvvəlcə buraxılış sətri, sonra onun ƏD / investisiya / əmək haqqı / işçi sayı
# sətirləri* ardıcıllığı ilə verir; sahə adı buraxılış sətrindən sonrakı sətirlərə ötürülür — FR1 onları məhz belə oxuyur.
# Xana iş kitabını hər iki mənbənin eyni anlayışı dərc etdiyi bütün hallarda DSK ilə müqayisə edir.

# %%
class _LazyWB:
    '''Open the workbook only if a sheet is not in the parse cache.'''
    _wb = None
    def __getitem__(self, k):
        if _LazyWB._wb is None: _LazyWB._wb = openpyxl.load_workbook(XL, read_only=True, data_only=True)
        return _LazyWB._wb[k]
    @property
    def sheetnames(self):
        if ('wb', '_sheetnames') not in CACHE:
            if _LazyWB._wb is None: _LazyWB._wb = openpyxl.load_workbook(XL, read_only=True, data_only=True)
            CACHE[('wb', '_sheetnames')] = list(_LazyWB._wb.sheetnames)
        return CACHE[('wb', '_sheetnames')]
WBK = _LazyWB()
def wb_mat(sheet):
    key = ('wb', sheet)
    if key not in CACHE: CACHE[key] = _wb_mat(sheet)
    return CACHE[key]
def _wb_mat(sheet):
    ws = WBK[sheet]; n = ws.max_column
    return [list(r) + [None] * (n - len(r)) for r in ws.iter_rows(values_only=True)]
def wb_years(mat, scan=4):
    best = {}
    for i in range(min(scan, len(mat))):
        yc = {j: int(v) for j, v in enumerate(mat[i]) if isinstance(v, (int, float)) and not isinstance(v, bool)
              and float(v).is_integer() and 1985 <= v <= 2035}
        if len(yc) > len(best): best = yc
    return best

def wb_industry():
    recs = []
    for sh in ['Mədənçıxarma', 'Emal Sənayesi', 'Elektrik enerjisi ', 'Su təchizatı']:
        mat = wb_mat(sh); yc = wb_years(mat); branch = None
        for i, row in enumerate(mat):
            lab = az_lower(row[0] or '').strip()
            if not lab: continue
            vals = {y: to_num(row[j]) for j, y in yc.items()}
            if not np.isfinite(list(vals.values())).any(): continue
            var = None
            hit = [b for b in BR if re.search(b[3], lab)]
            if ('buraxılış' in lab or 'xidmətlərin göstərilməsi' in lab) and 'üzrə əlavə' not in lab:
                if hit:
                    branch, var = hit[0][0], 'GO'
                elif lab.startswith('emal sənayesi') or lab.startswith('mədənçıxarma sənayesi üzrə buraxılış'):
                    branch, var = ('C' if lab.startswith('emal') else 'B'), 'GO'
            elif 'əlavə dəyər' in lab or lab.startswith('üdm') or 'sahə üzrə üdm' in lab: var = 'VA'
            elif 'əsas kapitala' in lab: var = 'INV'
            elif 'əmək haqları' in lab: var = 'WAGE'
            elif 'orta siyahı sayı' in lab: var = 'EMP'
            if var is None or branch is None: continue
            if var == 'VA' and lab.startswith('mədənçıxarma sənayesi üzrə əlavə'): branch = 'B'
            for y, v in vals.items():
                if np.isfinite(v): recs.append(dict(branch=branch, year=y, var=var, value=v))
    W = pd.DataFrame(recs).pivot_table(index=['branch', 'year'], columns='var', values='value', aggfunc='first')
    return W
# text cells written with a dot as thousands separator ('1.581'): read as 1 581 by to_num; list every one
DOTK = [(sh, i + 1, j, str(v)) for sh in ['Mədənçıxarma', 'Emal Sənayesi', 'Elektrik enerjisi ', 'Su təchizatı', 'DVX üzrə göstəricilər', 'Real sektor']
        for i, row in enumerate(wb_mat(sh)) for j, v in enumerate(row)
        if isinstance(v, str) and re.fullmatch(r'\s*-?[1-9]\d{0,2}(\.\d{3})+\s*', v)]
print(f'text cells with a dot thousands separator in the workbook sheets used: {[(a, r, v) for a, r, _, v in DOTK]}')
assert len(DOTK) == 1 and DOTK[0][0] == 'Emal Sənayesi', f'unexpected dot-thousands text cells: {DOTK}'
WBI = wb_industry()
wgo = WBI.GO.unstack(0)
cmp_ = pd.DataFrame({'workbook output, 30 branches': wgo[BCODES].sum(axis=1), 'DSK 010 all industry': GO_all['ALL']}).dropna()
cmp_['gap %'] = (cmp_.iloc[:, 0] / cmp_.iloc[:, 1] - 1) * 100
display(cmp_.round(2))
_bgap = ((wgo[BCODES] / GO[BCODES]).loc[2016:LAST_ACT] - 1).abs() * 100
print(f'workbook vs DSK branch output 2016-{LAST_ACT}: median gap {np.nanmedian(_bgap.values):.3f}%, '
      f'max {np.nanmax(_bgap.values):.2f}% ({_bgap.max().idxmax()})')
WEMP = WBI.EMP.unstack(0); WWAGE = WBI.WAGE.unstack(0); WVA = WBI.VA.unstack(0); WINV = WBI.INV.unstack(0)
_eg = ((WEMP[BCODES] / EMP_DSK[BCODES]).loc[2019:LAST_ACT] - 1).abs() * 100
print(f'workbook vs DSK 006 employees 2019-{LAST_ACT}: median gap {np.nanmedian(_eg.values):.2f}%, max {np.nanmax(_eg.values):.1f}% '
      f'({_eg.max().idxmax()} in {int(_eg[_eg.max().idxmax()].idxmax())})')
_vg = ((WVA[MANUF] / NA_VA[MANUF]).loc[2016:LAST_ACT] - 1).abs() * 100
print(f'workbook vs national-accounts VA, manufacturing branches: median gap {np.nanmedian(_vg.values):.3f}%, max {np.nanmax(_vg.values):.2f}%')

def wb_rows_by_label(sheet, pats):
    mat = wb_mat(sheet); yc = wb_years(mat); out = {}; lab_found = {}
    for nm, (pat, nth) in pats.items():
        hits = [i for i, row in enumerate(mat) if row[0] and re.search(pat, az_lower(row[0]))]
        assert len(hits) > nth, f'{sheet}: label /{pat}/ not found'
        i = hits[nth]
        out[nm] = pd.Series({y: to_num(mat[i][j]) for j, y in yc.items()}).sort_index()
        lab_found[nm] = (i + 1, str(mat[i][0]).strip()[:70])
    return pd.DataFrame(out), lab_found

DVX, DVX_LAB = wb_rows_by_label('DVX üzrə göstəricilər', {
    'pt_payers':   (r'^mənfəət vergisi bəyannamələr üzrə ödəyici sayı', 0),
    'pt_income':   (r'^mənfəət vergisi bəyannamələri üzrə ümumi gəlirlər', 0),
    'pt_income_net': (r'^mənfəət vergisi bəyannamələri üzrə çıxılmalardan sonra', 0),
    'pt_expenses': (r'^mənfəət vergisi bəyannamələri üzrə cəmi xərclər', 0),
    'pt_deductible': (r'^mənfəət vergisi bəyannamələri üzrə ümumi gəlirdən çıxılan', 0),
    'pt_profit':   (r'^mənfəət vergisi bəyannamələri üzrə vergitutma məqsədləri', 0),
    'pt_loss':     (r'^mənfəət vergisi bəyannamələri üzrə zərər', 0),
    'pt_tax':      (r'^mənfəət vergisi bəyannamələri üzrə ödənilməli', 0),
    'pt_rent':     (r'^mənfəət vergisi bəyannamələri üzrə rentabellik', 0),
    'it_payers':   (r'^gəlir vergisi bəyannamələr üzrə ödəyici sayı', 0),
    'it_income':   (r'^gəlir vergisi bəyannamələri üzrə ümumi gəlirlər', 0),
    'it_profit':   (r'^gəlir vergisi bəyannamələri üzrə vergitutma', 0),
    'it_loss':     (r'^gəlir vergisi bəyannamələri üzrə zərər', 0),
    'it_rent':     (r'^gəlir vergisi bəyannamələri üzrə rentabellik', 0),
    'arrears':     (r'^vergi borcları', 0),
    'turn_total':  (r'^cəmi dövriyyə', 0),
    'turn_ind':    (r'^sənaye sektrou üzrə dövriyyə', 0),
    'turn_ind_non': (r'^qeyri neft-qaz sənayesi üzrə dövriyyə', 0),
    'tax_ind':     (r'^sənaye üzrə vergi daxilolmaları', 0),
    'large_n': (r'^iri vergi ödəyicilərin sayı', 0), 'large_turn': (r'^iri vergi ödəyiciləri üzrə dövriyyə', 0),
    'large_emp': (r'^iri vergi ödəyiciləri üzrə işçi', 0),
    'medium_n': (r'^orta vergi ödəyicilərin sayı', 0), 'medium_turn': (r'^orta vergi ödəyiciləri üzrə dövriyyə', 0),
    'medium_emp': (r'^orta vergi ödəyiciləri üzrə işçi', 0),
    'small_n': (r'^kiçik vergi ödəyicilərin sayı', 0), 'small_turn': (r'^kiçik vergi ödəyiciləri üzrə dövriyyə', 0),
    'small_emp': (r'^kiçik vergi ödəyiciləri üzrə işçi', 0),
    'micro_n': (r'^mikro vergi ödəyicilərin sayı', 0), 'micro_turn': (r'^mikro vergi ödəyiciləri üzrə dövriyyə', 0),
    'micro_emp': (r'^mikro vergi ödəyiciləri üzrə işçi', 0),
    'budget_n': (r'^büdcə təşkilatları üzrə vergi ödəyicilərin sayı', 0),
    'budget_turn': (r'^büdcə təşkilatları üzrə dövriyyə', 0)})
DVX = DVX.loc[2021:LAST_ACT]
RS, RS_LAB = wb_rows_by_label('Real sektor', {
    'inv_total': (r'^əsas kapitala cəmi investisiyalar', 0), 'inv_own': (r'^müəssisə və təşkilatların öz vəsaitləri', 0),
    'inv_budget': (r'^büdcə vəsaitləri hesabına', 0), 'inv_other': (r'^digər maliyyə mənbələri', 0),
    'priv_share_gdp': (r'^özəl sektorun ümumi daxili məhsulda payı|^özəl sektorun üdm-də payı', 0),
    'inv_ind': (r'^sənaye üzrə əsas kapitala', 0)})
print('workbook rows used (sheet row, label):')
display(pd.DataFrame({**{f'DVX {k}': v for k, v in DVX_LAB.items()}, **{f'Real sektor {k}': v for k, v in RS_LAB.items()}},
                     index=['row', 'label']).T)

# %% [markdown]
# ### 5.4 Regionlar, məhsullar, KOB-lar, statistik reyestr, sənaye parkları
#
# On dörd iqtisadi rayon (DSK `021`–`024`, 2003/2005–2025, və iş kitabının `Regionlar` vərəqləri, 2021–2025); fiziki
# vahidlərlə təxminən 150 məhsul (DSK `018`, 1995–2025), sahə cədvəllərinin `014_x`, `015_x`, `016`, `017` məhsul
# siyahıları vasitəsilə öz sahəsinə bağlanır; KOB göstəriciləri (DSK sahibkarlıq, **yalnız 2023 və 2024**); statistik
# reyestr (bir anlıq vəziyyət, 1 iyul 2026); sənaye parkları və zonaları (iş kitabının `Park` vərəqi, 2019–2025).

# %%
REG_PAT = {'Baku city': r'^baku', 'Nakhchivan AR': r'^nakh?chivan', 'Absheron-Khizi': r'^absheron-khizi',
           'Daghlig Shirvan': r'^da[gğ]h?lig shirvan', 'Ganja-Dashkasan': r'^ganja-dashkasan', 'Garabagh': r'^garaba[gğ]h',
           'Gazakh-Tovuz': r'^gazakh-tovuz', 'Guba-Khachmaz': r'^guba-khachmaz', 'Lankaran-Astara': r'^lankaran-astara',
           'Central Aran': r'^central aran', 'Mil-Mughan': r'^mil-mu[gğ]han', 'Shaki-Zagatala': r'^sh[ae]ki-zagatala',
           'Eastern Zangezur': r'^eastern zang[ae]zur', 'Shirvan-Salyan': r'^shirvan-salyan'}
REG_NAMES = list(REG_PAT)
def region_frame(fn):
    d = dsk_wide(P_('industry', fn)); lab = d.label.map(az_lower)
    ycols = [c for c in d.columns if isinstance(c, (int, np.integer))]
    out = {}
    for r in REG_NAMES:
        hits = list(d.index[lab.str.contains(REG_PAT[r], regex=True)])
        assert len(hits) >= 1, f'{fn}: region {r} not found'
        out[r] = d.loc[hits[0], ycols].astype(float)
    return pd.DataFrame(out).sort_index()
REG_GO = region_frame('022en.xls') / 1000.0            # thousand -> million AZN
REG_VI = region_frame('023en.xls'); REG_NS = region_frame('024en.xls') / 100.0; REG_NENT = region_frame('021en.xls')
_rg = ((REG_GO.sum(axis=1) / GO_all['ALL']).loc[REG_GO.index.min():LAST_ACT] - 1) * 100
REG_GAP = _rg
print(f'14 regions vs DSK 010 all-industry output: gap {_rg.min():+.2f}% to {_rg.max():+.2f}% '
      f'({REG_GO.index.min()}-{LAST_ACT}; worst {int(_rg.abs().idxmax())})')
_ng = (REG_NENT.sum(axis=1) / NENT['ALL'] - 1).dropna() * 100
print(f'14 regions vs DSK 004 enterprise count: gap {_ng.min():+.2f}% to {_ng.max():+.2f}%')

# workbook region sheets (2021-2025): enterprises, entry, exit, size classes, industrial output
RG_WB = []
for sh in [s for s in WBK.sheetnames if s.startswith('Regionlar')]:
    mat = wb_mat(sh); yc = wb_years(mat)
    title = str(mat[0][0] or '')
    def grab(pat, nth=0):
        hits = [i for i, row in enumerate(mat) if row[0] and re.search(pat, az_lower(row[0]))]
        return {y: to_num(mat[hits[nth]][j]) for j, y in yc.items()} if len(hits) > nth else {}
    for var, pat, nth in [('enterprises', r'^müəssisə və təşkilatların sayı', 0), ('new', r'^yeni yaradılmış müəssisə', 0),
                          ('liquidated', r'^ləğv edilmiş müəssisə', 0), ('micro', r'^mikro sahibkarların sayı', 0),
                          ('small', r'^kiçik sahibkarların sayı', 0), ('medium', r'^orta sahibkarların sayı', 0),
                          ('ind_vi', r'^sənaye', 0), ('ind_go', r'^sənaye', 1)]:
        for y, v in grab(pat, nth).items():
            RG_WB.append(dict(sheet=sh, region=re.sub(r'\s+', ' ', title.split('iqtisadi rayon')[0].split('sosial')[0]).strip(),
                              year=y, var=var, value=v))
RG_WB = pd.DataFrame(RG_WB)
print(f'workbook region sheets: {RG_WB.sheet.nunique()} sheets, years {RG_WB.year.min()}-{RG_WB.year.max()}')

# products in physical units, and the product -> branch link from the branch tables' product lists
d018 = dsk_wide(P_('industry', '018en.xls'))
PROD = d018[d018.label.str.contains(',')].copy()
PROD['key'] = PROD.label.map(lambda s: re.sub(r'[^a-z]', '', az_lower(s)))
PROD_BR = {}
for fn in ['014_1en.xls', '014_2en.xls', '014_3en.xls', '014_4en.xls'] + [f'015_{i}en.xls' for i in range(1, 25)] + ['016en.xls', '017en.xls']:
    sh = xlrd.open_workbook(P_('industry', fn)).sheet_by_index(0)
    title = ' '.join(str(sh.cell_value(r, c)) for r in range(0, 3) for c in range(sh.ncols) if isinstance(sh.cell_value(r, c), str))
    tl = az_lower(title)
    code = [b[0] for b in BR if re.search(b[4], tl) and not (b[5] and re.search(b[5], tl))]
    code = code[-1] if code else None
    on = False
    for r in range(sh.nrows):
        lab = str(sh.cell_value(r, 0)).strip() or str(sh.cell_value(r, 1)).strip()
        if 'products in kind' in az_lower(lab): on = True; continue
        if on and ',' in lab and code:
            PROD_BR[re.sub(r'[^a-z]', '', az_lower(lab))] = code
PROD['branch'] = PROD.key.map(PROD_BR)
print(f'DSK 018: {len(PROD)} product rows; {PROD.branch.notna().sum()} linked to a branch through the branch tables')

# SMEs (2023, 2024), the statistical register (1 July 2026), industrial parks
def sme_table(fn, first_row_pat=r'sənaye|industry'):
    sh = xlrd.open_workbook(P_('entrepreneurship', fn)).sheet_by_index(0)
    out = []
    for r in range(sh.nrows):
        lab = str(sh.cell_value(r, 0)).strip()
        if not lab: continue
        vals = [to_num(sh.cell_value(r, c)) for c in range(1, sh.ncols)]
        if np.isfinite(vals).sum() >= 4:
            out.append([lab] + vals[:8])
    df = pd.DataFrame(out, columns=['label', 'total_2023', 'micro_2023', 'small_2023', 'medium_2023',
                                    'total_2024', 'micro_2024', 'small_2024', 'medium_2024'][:len(out[0])])
    df['label_en'] = df.label.map(lambda s: re.split(r'(?<=[a-zəüöğıçş)])\s+(?=[A-Z])', s, maxsplit=1)[-1])
    return df
SME_SHARE_OUT = sme_table('012en.xls'); SME_ASSETS = sme_table('039en.xls'); SME_STOCKS = sme_table('040en.xls')
SME_TAX = sme_table('041en.xls'); SME_MAIN = sme_table('001_1en.xls')
def stu(fn, ncol):
    """Statistical-register snapshot: numeric columns are located on the 'Total' row and read at the same
    positions in every row (a '-' cell is a missing value, not a shift)."""
    sh = xlrd.open_workbook(P_('st_units', fn)).sheet_by_index(0)
    lab_of = lambda r: (str(sh.cell_value(r, 0)).strip() or str(sh.cell_value(r, 1)).strip())
    tot = [r for r in range(sh.nrows) if az_lower(lab_of(r)) == 'total'][0]
    cols = [c for c in range(1, sh.ncols) if np.isfinite(to_num(sh.cell_value(tot, c)))][:ncol]
    out = []
    for r in range(tot, sh.nrows):
        lab = lab_of(r)
        vals = [to_num(sh.cell_value(r, c)) for c in cols]
        if lab and not az_lower(lab).startswith('of which') and np.isfinite(vals[0]): out.append([lab] + vals)
    return pd.DataFrame(out)
ST_ENTRY = stu('2_1_en.xls', 5); ST_ENTRY.columns = ['activity', 'units', 'new', 'new_pct', 'liquidated', 'liquidated_pct']
ST_LARGE = stu('1_3_i_en.xls', 3); ST_LARGE.columns = ['activity', 'large_units', 'pct_of_large', 'share_large_in_units_pct']
PARK, _ = None, None
_pm = wb_mat('Park'); _grp = {}; cur = None
for j, v in enumerate(_pm[1]):
    if v: cur = str(v).strip()
    _grp[j] = cur
PARKS = []
for i in range(3, len(_pm)):
    nm = str(_pm[i][0] or '').strip()
    if not nm or nm.startswith('Qeyd'): continue
    for j in range(1, len(_pm[i])):
        y = _pm[2][j]
        if isinstance(y, (int, float)) and 2015 <= y <= 2035 and _grp.get(j):
            PARKS.append(dict(park=nm, indicator=_grp[j], year=int(y), value=to_num(_pm[i][j])))
PARKS = pd.DataFrame(PARKS)
print(f'SME tables (2023-2024): {len(SME_SHARE_OUT)} activity rows; register snapshot: {len(ST_ENTRY)} activity rows; '
      f'industrial parks/zones: {PARKS.park.nunique()} rows x {PARKS.indicator.nunique()} indicators, '
      f'{PARKS.year.min()}-{PARKS.year.max()}')

# %% [markdown]
# ### 5.5 FR1, FR3 və FR4-dən giriş məlumatları
#
# FR10 FR1-in proqnozunu (`FR1_forecast_full.csv`: dörd sənaye bölməsinin real əlavə dəyəri və deflyatorları, neftin
# ixrac qiyməti, qeyri-neft ÜDM, investisiya deflyatoru, əmək haqqı, məşğulluq — üç ssenari), FR1-in Əsas ssenari üzrə
# 500 butstrap çəkilişini (`FR1_fan_draws.csv`), FR1-in tarixi məlumatlarını (`FR1_analysis_dataset.csv`), FR3-ün sahələr
# üzrə əmək haqlarını və FR4-ün fəaliyyət növləri üzrə muzdlu işçilərini oxuyur. Fayl və ya sütun olmadıqda notebook
# dayanır: FR10-un onu makro ssenarilərdən xəbərsiz ayıra biləcək ehtiyat variantı yoxdur.

# %%
need = ['FR1_forecast_full.csv', 'FR1_fan_draws.csv', 'FR1_analysis_dataset.csv', 'FR3_industry_branch_wages.csv',
        'FR4_hired_by_activity.csv']
for fn in need: assert (OUT / fn).exists(), f'{fn} missing: run FR1, FR3, FR4 first'
F1H = pd.read_csv(OUT / 'FR1_analysis_dataset.csv', index_col=0)
F1F = pd.read_csv(OUT / 'FR1_forecast_full.csv').rename(columns={'Unnamed: 0': 'year'})
F1D = pd.read_csv(OUT / 'FR1_fan_draws.csv'); F1D = F1D.drop(columns=[c for c in F1D.columns if c.startswith('Unnamed')])
assert list(F1F.scenario.unique()) == SCEN and sorted(F1F.year.unique()) == FC_YEARS
SECV = {'B': 'min', 'C': 'man', 'D': 'elc', 'E': 'wat'}
for v in [f'rva_{s}' for s in SECV.values()] + [f'p_{s}' for s in SECV.values()] + ['oil_exp_price', 'rgdpnon', 'p_inv', 'wage', 'emp']:
    assert v in F1F.columns and v in F1D.columns, f'{v} absent from FR1 outputs'
FR3W = pd.read_csv(OUT / 'FR3_industry_branch_wages.csv').rename(columns={'Unnamed: 0': 'scenario', 'Unnamed: 1': 'year'})
FR4H = pd.read_csv(OUT / 'FR4_hired_by_activity.csv').rename(columns={'Unnamed: 0': 'scenario', 'Unnamed: 1': 'year'})
# FR3 branch columns carry the workbook's Azerbaijani branch names: map them to NACE codes
FR3_MAP = {}
for c in FR3W.columns[2:]:
    hit = [b[0] for b in BR if re.search(b[3], az_lower(c))]
    assert len(hit) == 1, f'FR3 column {c} maps to {hit}'
    FR3_MAP[c] = hit[0]
FR3W = FR3W.rename(columns=FR3_MAP)
print(f'FR1: {F1D.draw.nunique()} baseline draws; FR3 branch wages for {len(FR3_MAP)} branches '
      f'(not: {[b for b in BCODES if b not in FR3_MAP.values()]}); FR4 hired employees by activity, 3 scenarios')
# FR1 history vs DSK national accounts: the section value added FR10 anchors on
_c = pd.DataFrame({'FR1 va_man_n': F1H.va_man_n, 'DSK NA manufacturing VA': NA_VA['C'],
                   'FR1 va_min_n': F1H.va_min_n, 'DSK NA mining VA': NA_VA['B']}).loc[2015:LAST_ACT]
display(_c.round(1))
_gap = float(max((_c.iloc[:, 0] / _c.iloc[:, 1] - 1).abs().max(), (_c.iloc[:, 2] / _c.iloc[:, 3] - 1).abs().max()) * 100)
print(f'FR1 and the DSK national accounts agree on section value added to {_gap:.2f}% (2015-{LAST_ACT})')
save_cache()
print(f'parse cache saved: {len(CACHE)} tables -> {CACHE_PATH.name}')
