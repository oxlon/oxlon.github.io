# %% [markdown]
# ### 17.5 Mühərrikin işə salınması, kalibrləmə xətaları cədvəli və emal xəttinin testləri
#
# DSK aqreqatları ilə müqayisə SİNTETİK rejimdə **kalibrləmə xətaları cədvəli**, REAL rejimdə isə Nazirliyin reyestrinin
# **əhatə yoxlamasıdır** (eyni kod). SİNTETİK rejimdə daha iki test mühərrikin generatorun daxil etdiyi xüsusiyyətləri
# bərpa etdiyini yoxlayır (səmərəli müəssisələrin daha böyük olduğu yerlərdə Boone meylləri mənfidir; konsentrasiyalı
# bölmələr daha konsentrasiyalıdır) — bunlar tapıntı deyil, məlumat yaradan prosesin yoxlamaları kimi işarələnir.

# %%
PRE = 'FR12_SYNTHETIC_' if DATA_MODE == 'SYNTHETIC' else 'FR12_FIRM_'
if DATA_MODE == 'REAL':                     # never leave synthetic outputs next to real ones
    for p_ in OUT.glob('FR12_SYNTHETIC_*.csv'): p_.unlink()
elif list(OUT.glob('FR12_FIRM_*.csv')):
    print('NOTE: FR12_FIRM_*.csv from an earlier REAL run are present in output/ and are not overwritten by this SYNTHETIC run')
LB = run_layer_b(REGISTER, DATA_MODE, OUT)
def calib_table(REG):
    '''Comparison of a register with the DSK aggregates (calibration errors / coverage).'''
    R_ = REG.copy(); R_['w'] = wcol(R_); R_['sec'] = R_.nace2.map(DIV2SEC)
    R_['reg_year'] = pd.to_datetime(R_.registration_date).dt.year
    CAL = []
    def cal(target, dim, unit, year, pub, syn, q):
        CAL.append(dict(target=target, dimension=dim, unit=unit, year=year, published=float(pub), synthetic=float(syn), abs_error=float(syn - pub),
                        rel_error_pct=float((syn - pub) / pub * 100) if pub else np.nan, status=q))
    for y in sorted(R_.year.unique()):
        d = R_[R_.year == y]
        nb = d[d.reg_year == y].groupby('sec').w.sum(); nd = d[d.status == 'liquidated'].groupby('sec').w.sum(); st = d[d.status == 'active'].groupby('sec').w.sum()
        for s in SECS:
            if y in (2021, 2024, 2025):
                cal('births', 'section', s, y, REG_FY['new'][y].get(s, 0), nb.get(s, 0), 'exact where published')
                cal('deaths', 'section', s, y, REG_FY['liq'][y].get(s, 0), nd.get(s, 0), 'exact where published')
                cal('active units, end of year', 'section', s, y, REG_FY['stock'][y].get(s, 0), st.get(s, 0), 'exact 2025; earlier via stock-flow (F5)')
            if (s, y) in NA.index: cal('revenue (thsd AZN) = output', 'section', s, y, NA.loc[(s, y), 'GO'] * 1000, (d[d.sec == s].w * d[d.sec == s].revenue).sum(), 'exact')
        nbr = d[d.reg_year == y].groupby('region').w.sum(); ndr = d[d.status == 'liquidated'].groupby('region').w.sum(); str_ = d[d.status == 'active'].groupby('region').w.sum()
        if y >= 2021:
            for r in REGS:
                q = rg.loc[(r, y)]
                cal('births', 'region', r, y, q.new, nbr.get(r, 0), 'exact'); cal('deaths', 'region', r, y, q.liquidated, ndr.get(r, 0), 'exact')
                cal('active units, end of year', 'region', r, y, q.enterprises, str_.get(r, 0), 'exact 2025; earlier via stock-flow')
        d2 = d.assign(grp=d.sec.map(lambda s: SECT[s][3]), wr=d.w * d.revenue)
        for g in GRP:
            dg = d2[d2.grp == g]
            if (g, y) in E012.index and dg.wr.sum() > 0:
                cal('SME share of revenue, %', 'activity group', g, y, E012.loc[(g, y), 'sme'], dg[dg.size_class != 'large'].wr.sum() / dg.wr.sum() * 100, 'exact (output base)')
            if (g, y) in E013.index and dg.w.sum() > 0:
                emp = dg.w * dg.employees
                cal('SME share of employees, %', 'activity group', g, y, E013.loc[(g, y), 'sme'], emp[dg.size_class != 'large'].sum() / emp.sum() * 100, 'exact except where the 251-employee floor of large units binds')
    _last = R_[(R_.year == R_.year.max()) & (R_.status == 'active')]
    for s in SECS:
        if s in SIZE.index and SIZE.loc[s].sum() > 0:
            for z in SIZES:
                cal(f'size mix: {z} share of units, %', 'section', s, int(R_.year.max()), SIZE.loc[s, z] / SIZE.loc[s].sum() * 100,
                    _last[(_last.sec == s) & (_last.size_class == z)].w.sum() / max(_last[_last.sec == s].w.sum(), 1) * 100, 'approximate (1 July 2026 snapshot)')
    return pd.DataFrame(CAL)
CALT = calib_table(REGISTER)
CALS = CALT.groupby(['target', 'dimension', 'status']).agg(cells=('published', 'size'), max_abs_error=('abs_error', lambda x: x.abs().max()),
                                                          median_abs_rel_error_pct=('rel_error_pct', lambda x: x.abs().median()),
                                                          max_abs_rel_error_pct=('rel_error_pct', lambda x: x.abs().max())).reset_index()
_cn = 'calibration_errors' if DATA_MODE == 'SYNTHETIC' else 'coverage_vs_dsk'
for nm, t in [(_cn, CALT), (_cn + '_summary', CALS)]:
    t = t.copy()
    if DATA_MODE == 'SYNTHETIC': t.insert(0, 'WATERMARK', SYN_MARK)
    t.to_csv(OUT / f'{PRE}{nm}.csv', index=False)
display(CALS.round(3))
PIPE = LB['PIPE'].copy()
if DATA_MODE == 'SYNTHETIC':
    ex = CALT[CALT.status.str.startswith('exact') & ~CALT.target.str.startswith('active') & ~CALT.target.str.startswith('SME share of emp')]
    _tol = (ex.abs_error.abs() <= 0.5 + 1e-7 * ex.published.abs()).all()
    PIPE.loc[len(PIPE)] = ['calibration: births, deaths, revenue and SME revenue shares reproduce DSK where published (max |relative error| %)',
                           float(ex.rel_error_pct.abs().max()), bool(_tol)]
    mb = LB.get('margins_boone')
    neg = float((mb.boone_beta.dropna() < 0).mean()) if mb is not None else np.nan
    PIPE.loc[len(PIPE)] = ['DGP check: Boone slope negative (efficient firms larger) in >= 90% of section-years', neg, bool(neg >= 0.9)]
    cn = LB['concentration_nace'].assign(alpha=lambda d: d.section.map(ALPHA))
    hi_c, lo_c = cn[cn.alpha <= 1.15].HHI.median(), cn[cn.alpha >= 2.0].HHI.median()
    PIPE.loc[len(PIPE)] = ['DGP check: low-Pareto-alpha sections more concentrated (median HHI ratio)', float(hi_c / lo_c), bool(hi_c > lo_c)]
PIPE.insert(0, 'WATERMARK', SYN_MARK) if DATA_MODE == 'SYNTHETIC' else None
PIPE.to_csv(OUT / f'{PRE}pipeline_tests.csv', index=False)
display(PIPE)
assert PIPE.passed.all(), 'Layer-B pipeline test failed'
_c = LB['concentration_nace']; _c = _c[_c.year == _c.year.max()].sort_values('HHI', ascending=False)
print(f'[{DATA_MODE}] most concentrated divisions {int(_c.year.max())} (pipeline demonstration): ' + ', '.join(f'{d} HHI {h:.0f}' for d, h in zip(_c.nace2.head(5), _c.HHI.head(5))))
fig, ax = plt.subplots(1, 2, figsize=(13, 4))
km = LB['survival_km']
for c, g in km.groupby('cohort'): ax[0].step(g.age, g.survival, where='post', label=str(c))
ax[0].set_title(f'Kaplan-Meier survival by cohort — {DATA_MODE}'); ax[0].legend(fontsize=7)
ee = LB['entry_exit_section'].pivot_table(index='year', columns='sec', values='entry_rate')
ax[1].plot(ee.index, ee.values, alpha=0.6); ax[1].set_title(f'Entry rate by section, % — {DATA_MODE}')
if DATA_MODE == 'SYNTHETIC':
    for a in ax: a.text(0.5, 0.5, 'SYNTHETIC\nnot real data', transform=a.transAxes, fontsize=26, color='red', alpha=0.25, ha='center', va='center', rotation=20)
plt.tight_layout(); plt.show()
