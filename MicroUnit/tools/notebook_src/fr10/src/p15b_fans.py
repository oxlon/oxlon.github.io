# %%
def qtab(M, base_path, last=None):
    '''M: (R, 6) replication paths incl. 2025; returns quantiles by forecast year (+ growth row) and the baseline.'''
    lev = np.quantile(M[:, 1:], QTL, axis=0).T
    df = pd.DataFrame(lev, index=FC_YEARS, columns=[f'p{int(q*100)}' for q in QTL])
    df['baseline'] = np.asarray(base_path, float)[1:]
    if last is not None:
        g = ((M[:, -1] / last) ** (1 / H) - 1) * 100
        df.loc[f'{FC_YEARS[0]}-{FC_YEARS[-1]} growth % pa'] = list(np.quantile(g, QTL)) + [float(((base_path[-1] / last) ** (1 / H) - 1) * 100)]
    return df

FANS = {}
for j, b in enumerate(BCODES):
    FANS[('branch nominal output, mn AZN', b)] = qtab(SIM['nom'][..., j], B_['nom'][b].values, B_['nom'].loc[LAST_ACT, b])
    FANS[('branch real output, mn AZN 2015 prices', b)] = qtab(SIM['real'][..., j], B_['real'][b].values, B_['real'].loc[LAST_ACT, b])
    FANS[('branch share of industry, %', b)] = qtab(SIM['sh_ind'][..., j] * 100, B_['sh_ind'][b].values * 100)
    FANS[('labour productivity, thsd AZN 2015 prices per employee', b)] = qtab(SIM['lp'][..., j], B_['lp'][b].values, B_['lp'].loc[LAST_ACT, b])
for j, b in enumerate(MANUF):
    FANS[('branch share of manufacturing, %', b)] = qtab(SIM['sh_man'][..., j] * 100, B_['sh_man'][b].values * 100)
    FANS[('GOS-proxy margin, % of output', b)] = qtab(SIM['gosp'][..., j], B_['gosp'][b].values)
for j, s_ in enumerate(SECV):
    FANS[('section output, mn AZN', SECT[s_])] = qtab(SIM['sec_go'][..., j], B_['sec_go'][s_].values, B_['sec_go'].loc[LAST_ACT, s_])
    FANS[('section GOS, % of value added', SECT[s_])] = qtab(SIM['sec_gos'][..., j], B_['sec_fin'].xs(s_)['GOS_share_VA'].values)
FANS[('industry output, mn AZN', 'Industry')] = qtab(SIM['nom'].sum(-1), B_['nom'].sum(axis=1).values, B_['nom'].sum(axis=1).loc[LAST_ACT])
FANS[('non-state share of industry, %', 'Industry')] = qtab(SIM['ns_share'] * 100, B_['ns_share'].values * 100)
FANS[('HHI across manufacturing branches', 'Manufacturing')] = qtab(SIM['hhi_man'], hhi(B_['sh_man']).values)
for j, rg in enumerate(REG_NAMES):
    FANS[('regional share of industrial output, %', rg)] = qtab(SIM['reg_sh'][..., j] * 100, B_['reg_sh'][rg].values * 100)
FANS[('industry output, mn AZN — FR1 prices held at baseline', 'Industry')] = qtab(SIM_P['nom'].sum(-1), B_['nom'].sum(axis=1).values, B_['nom'].sum(axis=1).loc[LAST_ACT])
for j, s_ in enumerate(SECV):
    FANS[('section output, mn AZN — FR1 prices held at baseline', SECT[s_])] = qtab(SIM_P['sec_go'][..., j], B_['sec_go'][s_].values, B_['sec_go'].loc[LAST_ACT, s_])
FAN = pd.concat(FANS, names=['indicator', 'unit', 'year'])
lv = FAN[[isinstance(i[2], (int, np.integer)) for i in FAN.index]]
inside = (lv.baseline >= lv.p25 - 1e-9) & (lv.baseline <= lv.p75 + 1e-9)
inside90 = (lv.baseline >= lv.p5 - 1e-9) & (lv.baseline <= lv.p95 + 1e-9)
FAN_META = dict(n_reps=R_N, n_paths_C=len(POOLS['C'][1]), n_paths_R=len(POOLS['R'][1]),
                share_inside_iqr=float(inside.mean() * 100), share_inside_90=float(inside90.mean() * 100))
print(f'{len(FANS)} fan series; baseline inside the inter-quartile band in {FAN_META["share_inside_iqr"]:.1f}% of '
      f'series-years and inside the 90% band in {FAN_META["share_inside_90"]:.1f}%')
gk = f'{FC_YEARS[0]}-{FC_YEARS[-1]} growth % pa'
display(FAN.loc[[i for i in FAN.index if i[0].startswith(('industry output', 'section output')) and i[2] == gk]].round(2))
fig, ax = plt.subplots(1, 3, figsize=(16, 4.5))
for a, (ind, u, hist, ttl) in zip(ax, [('section output, mn AZN', 'Manufacturing', SEC_GO['C'], 'Manufacturing output, mn AZN'),
                                     ('branch share of manufacturing, %', '19', SH_MAN['19'] * 100, 'Refining share of manufacturing, %'),
                                     ('section GOS, % of value added', 'Manufacturing', SEC_FIN['GOS_share_VA'].xs('C'), 'Manufacturing GOS, % of VA')]):
    f = FAN.loc[(ind, u)]; f = f.loc[[y for y in f.index if isinstance(y, (int, np.integer))]].astype(float)
    a.plot(hist.loc[2012:LAST_ACT].index, hist.loc[2012:LAST_ACT], color='k', lw=2, label='actual')
    for lo_, hi_, al in [('p5', 'p95', 0.15), ('p10', 'p90', 0.25), ('p25', 'p75', 0.4)]:
        a.fill_between(FC_YEARS, f[lo_], f[hi_], color=PAL[0], alpha=al, lw=0)
    a.plot(FC_YEARS, f.baseline, color=PAL[1], lw=1.6, label='baseline')
    a.axvline(LAST_ACT, color='grey', ls=':'); a.set_title(ttl + ' — 50/80/90% bands', fontsize=8); a.legend(fontsize=7)
plt.tight_layout(); plt.show()
