# %%
SKEYS = list(SECV)
def frames(o, i=0):
    F_ = lambda a, cols: pd.DataFrame(a[i], index=YRS, columns=cols)
    R = {'nom': F_(o['nom'], BCODES), 'real': F_(o['real'], BCODES), 'emp': F_(o['emp'], BCODES), 'lp': F_(o['lp'], BCODES),
         'wage': F_(o['wage'], BCODES), 'sec_go': F_(o['sec_go'], SKEYS), 'sh_ind': F_(o['sh_ind'], BCODES),
         'sh_man': F_(o['sh_man'], MANUF), 'gosp': F_(o['gosp'], MANUF), 'reg_sh': F_(o['reg_sh'], REG_NAMES),
         'ns_share': pd.Series(o['ns_share'][i], index=YRS)}
    R['reg_go'] = R['reg_sh'].mul(REG_GO.loc[LAST_ACT].sum() * R['nom'].sum(axis=1) / R['nom'].loc[LAST_ACT].sum(), axis=0)
    R['sec_fin'] = pd.concat({s_: pd.DataFrame({'VA': o['sec_va'][i, :, j], 'CE': o['sec_ce'][i, :, j], 'OTP': o['sec_otp'][i, :, j],
                                                 'GOS_share_VA': o['sec_gos'][i, :, j], 'labour_share_VA': o['sec_ls'][i, :, j]}, index=YRS)
                              for j, s_ in enumerate(SKEYS)}, names=['sec', 'year'])
    R['sec_fin']['GOS'] = R['sec_fin'].VA - R['sec_fin'].CE - R['sec_fin'].OTP
    return R
def solve(s_, **kw):
    return frames(core(scen_arrays(s_), fr4_index(s_), **kw))
SOL = {s_: solve(s_) for s_ in SCEN}
B_ = SOL['Baseline']
cagr = lambda s: ((s.loc[FC_YEARS[-1]] / s.loc[LAST_ACT]) ** (1 / H) - 1) * 100
BR_FC = pd.DataFrame({'branch': [BNAME[b] for b in BCODES], 'section': [SECT[BSEC[b]] for b in BCODES],
                      'model': ['capacity + oil price' if b in OIL else ('quarrying: ' + MINING_RULES['rule08']) if b == '08' else
                                ('metal ores: ' + MINING_RULES['rule07']) if b == '07' else 'FR1 oil & gas real; residual nominal' if b in ('06', '09')
                                else ('related-sector: ' + LINK[b]) if b in LINK else 'sector total' for b in BCODES],
                      f'nominal {LAST_ACT}': B_['nom'].loc[LAST_ACT].values, f'nominal {FC_YEARS[-1]}': B_['nom'].loc[FC_YEARS[-1]].values,
                      'nominal growth % pa': cagr(B_['nom']).values, 'real growth % pa': cagr(B_['real']).values,
                      f'share of industry {LAST_ACT} %': B_['sh_ind'].loc[LAST_ACT].values * 100,
                      f'share of industry {FC_YEARS[-1]} %': B_['sh_ind'].loc[FC_YEARS[-1]].values * 100,
                      'LP growth % pa': cagr(B_['lp']).values}, index=BCODES)
display(BR_FC.round(2))
MIN_PATH = BR_FC.loc[MINING, ['branch', 'model', f'nominal {LAST_ACT}', f'nominal {FC_YEARS[-1]}', 'nominal growth % pa', 'real growth % pa']]
_od = pd.Series(core(scen_arrays('Baseline'), fr4_index('Baseline'))['oil_defl_idx'][0], index=YRS)
MIN_REC = dict(max_gap_pct=float((B_['nom'][MINING].sum(axis=1) / B_['sec_go']['B'] - 1).abs().max() * 100),
               implied_oil_deflator_growth_pa=cagr(_od), fr1_mining_deflator_growth_pa=cagr(pd.Series(scen_arrays('Baseline')['p_min'][0], index=YRS)))
print(f"mining reconciliation: 06+07+08+09 = FR1 mining output to {MIN_REC['max_gap_pct']:.1e}%; implied oil-part deflator "
      f"{MIN_REC['implied_oil_deflator_growth_pa']:+.2f}% a year vs FR1 mining deflator {MIN_REC['fr1_mining_deflator_growth_pa']:+.2f}%")
assert MIN_REC['max_gap_pct'] < 1e-9, 'mining branches do not reconcile with FR1 mining output'
nm_ = BR_FC.loc[NONOIL, 'real growth % pa']
print(f'manufacturing real branch growth 2026-30: min {BR_FC.loc[MANUF, "real growth % pa"].min():+.2f}% '
      f'({BR_FC.loc[MANUF, "real growth % pa"].idxmin()}), max {BR_FC.loc[MANUF, "real growth % pa"].max():+.2f}% ({BR_FC.loc[MANUF, "real growth % pa"].idxmax()}); '
      f'refining {BR_FC.loc["19", "real growth % pa"]:+.2f}% real, {BR_FC.loc["19", "nominal growth % pa"]:+.2f}% nominal')
# implied non-oil manufacturing growth (Törnqvist over the 22 non-oil branches) vs its own history
def tq_growth(nomF, realF, cols):
    w = nomF[cols].div(nomF[cols].sum(axis=1), axis=0); w = (w + w.shift(1)) / 2
    return (w * np.log(realF[cols]).diff()).sum(axis=1, min_count=1) * 100
NONOIL_FC = tq_growth(B_['nom'], B_['real'], NONOIL).loc[FC_YEARS].mean()
_h = tq_growth(GO, Q, NONOIL)
_roll = _h.rolling(5).mean().loc[2010:LAST_ACT]
NONOIL_HIST = dict(avg_2010_19=_h.loc[2010:2019].mean(), avg_2021_25=_h.loc[2021:LAST_ACT].mean(), best_5yr=_roll.max(), worst_5yr=_roll.min(),
                   forecast_2026_30=NONOIL_FC, flag=('ABOVE best 5-yr' if NONOIL_FC > _roll.max() else ''))
print('implied non-oil manufacturing real growth (Törnqvist, % a year): ' + ', '.join(f'{k} {v:+.2f}' if isinstance(v, float) else f'{k} {v}' for k, v in NONOIL_HIST.items()))
SEC_FC = pd.DataFrame({SECT[s_]: [cagr(B_['sec_go'][s_]), B_['sec_fin'].loc[(s_, LAST_ACT), 'GOS_share_VA'],
                                  B_['sec_fin'].loc[(s_, FC_YEARS[-1]), 'GOS_share_VA']] for s_ in SECV},
                      index=['nominal output growth % pa', f'GOS % of VA {LAST_ACT}', f'GOS % of VA {FC_YEARS[-1]}']).T
display(SEC_FC.round(2))
mshare = lambda S, y: S['sec_go'].loc[y, 'B'] / S['nom'].sum(axis=1).loc[y] * 100
SCEN_SUM = pd.DataFrame({s_: {'industry nominal output growth % pa': cagr(SOL[s_]['nom'].sum(axis=1)),
                              'manufacturing nominal growth % pa': cagr(SOL[s_]['nom'][MANUF].sum(axis=1)),
                              'manufacturing real growth % pa (FR1 rva_man)': cagr(pd.Series(scen_arrays(s_)['rva_man'][0], index=YRS)),
                              'refining real growth % pa': cagr(SOL[s_]['real']['19']),
                              f'mining share of industry {FC_YEARS[-1]} %': mshare(SOL[s_], FC_YEARS[-1]),
                              f'non-state share {FC_YEARS[-1]} % (composition)': SOL[s_]['ns_share'].loc[FC_YEARS[-1]] * 100,
                              f'HHI manufacturing {FC_YEARS[-1]}': float(hhi(SOL[s_]['sh_man']).loc[FC_YEARS[-1]]),
                              f'Baku share {FC_YEARS[-1]} %': SOL[s_]['reg_sh'].loc[FC_YEARS[-1], 'Baku city'] * 100,
                              f'manufacturing GOS % VA {FC_YEARS[-1]}': SOL[s_]['sec_fin'].loc[('C', FC_YEARS[-1]), 'GOS_share_VA']}
                         for s_ in SCEN}).T
display(SCEN_SUM.round(2))
# cross-sector multipliers implied by the pooled elasticity: d ln(branch output) / d ln(related sector), at given
# sector total, = beta x (1 - share of the branch in its group); halved under the equal-weight combination
wgt = 1.0 if MAN_MODE == 'pooled' else 0.5
MULT = pd.DataFrame([dict(branch=BNAME[b], related_sector=LINK[b], share_2025=float(SHH['B' if b in MINING else 'C'].loc[LAST_ACT, b]),
                          multiplier=wgt * BETA * (1 - float(SHH['B' if b in MINING else 'C'].loc[LAST_ACT, b])),
                          multiplier_p5=wgt * max(BETA - 1.645 * BETA_SE, 0) * (1 - float(SHH['B' if b in MINING else 'C'].loc[LAST_ACT, b])),
                          multiplier_p95=wgt * (BETA + 1.645 * BETA_SE) * (1 - float(SHH['B' if b in MINING else 'C'].loc[LAST_ACT, b])))
                     for b in LINK], index=list(LINK))
print('implied cross-sector multipliers: % change in branch output per 1% change in its related sector, sector total given')
display(MULT.round(3))

# %% [markdown]
# ### 14.2 Həssaslıq variantları (rıçaqlar), Əsas ssenari
#
# Bölüşdürmə (yalnız birləşdirilmiş model; sabit paylar), 2015–2025-ci illərin maksimum emal həcmində neft emalı və
# kimya, habelə neytral əmək payı qaydasını əvəz edən iki marja trayektoriyası: FR1-in əmək haqqı trayektoriyası və
# məhsul ifadəsində sabit əmək haqları. Marja bu fərziyyələrə şərtlənir; o, ödəmə qabiliyyətini deyil, pul vəsaitinin
# yaradılmasını və rentaları ölçür.

# %%
LEV = {'allocation: pooled model alone': solve('Baseline', mode='pooled'), 'allocation: constant shares': solve('Baseline', mode='const'),
       'oil-linked branches at maximum throughput': solve('Baseline', capf=CAPMAX),
       'margin: FR1 wage path': solve('Baseline', margin='fr1_wage'),
       'margin: wages constant in product terms': solve('Baseline', margin='product_wage')}
QUARRY_LINK = solve('Baseline', q08='unit elasticity to construction')    # v2 lever (not part of the v1 LEVERS table)
LEVERS = pd.DataFrame({k: {'manufacturing real branch growth, min % pa': cagr(v['real'][MANUF]).min(),
                           'manufacturing real branch growth, max % pa': cagr(v['real'][MANUF]).max(),
                           'refining real growth % pa': cagr(v['real']['19']),
                           'building materials real growth % pa': cagr(v['real']['23']),
                           'manufacturing GOS % VA 2030': v['sec_fin'].loc[('C', FC_YEARS[-1]), 'GOS_share_VA'],
                           'median branch GOS-proxy margin 2030': float(v['gosp'].loc[FC_YEARS[-1]].median()),
                           'HHI manufacturing 2030': float(hhi(v['sh_man']).loc[FC_YEARS[-1]])}
                       for k, v in {'baseline': B_, **LEV}.items()}).T
display(LEVERS.round(2))

# %% [markdown]
# ### 14.4 Qeyri-dövlət sektorunun payı: yalnız tərkib effekti
#
# Sənayedə qeyri-dövlət sektorunun payı **yalnız tərkib vasitəsilə** proqnozlaşdırılır: hər sahə 2025-ci il sahədaxili
# qeyri-dövlət payını saxlayır (aşağıdakı cədvəl), sənaye payı isə sahələrin müxtəlif sürətlə böyüməsi hesabına dəyişir.
# Bu, **mülkiyyət proqnozu deyil** — heç bir özəlləşdirmə və ya milliləşdirmə modelləşdirilmir.

# %%
NS_TAB = pd.DataFrame({'branch': [BNAME[b] for b in BCODES], 'non-state share held (2025), %': NS.loc[LAST_ACT, BCODES].values * 100,
                       f'share of industry {LAST_ACT}, %': B_['sh_ind'].loc[LAST_ACT].values * 100,
                       f'share of industry {FC_YEARS[-1]}, %': B_['sh_ind'].loc[FC_YEARS[-1]].values * 100}, index=BCODES)
display(NS_TAB.round(2))
NS_COMP = dict(mining_share_2025=mshare(B_, LAST_ACT), mining_share_2030=mshare(B_, FC_YEARS[-1]),
               ns_2025=B_['ns_share'].loc[LAST_ACT] * 100, ns_2030=B_['ns_share'].loc[FC_YEARS[-1]] * 100,
               ns_mining=NS.loc[LAST_ACT, 'B'] * 100, ns_refining=NS.loc[LAST_ACT, '19'] * 100, ns_electricity=NS.loc[LAST_ACT, '35'] * 100)
print(f"composition: mining falls from {NS_COMP['mining_share_2025']:.1f}% to {NS_COMP['mining_share_2030']:.1f}% of industrial output; "
      f"non-state shares held at mining {NS_COMP['ns_mining']:.1f}%, refining {NS_COMP['ns_refining']:.1f}%, electricity {NS_COMP['ns_electricity']:.1f}%; "
      f"industry non-state share {NS_COMP['ns_2025']:.1f}% -> {NS_COMP['ns_2030']:.1f}% (composition, not ownership change)")
