# %% [markdown]
# ## Hissə 13 — FR1-in üç ssenarisi üzrə 2026–2030-cu illər üçün giriş və çıxış proqnozları
#
# Hissə 12-də yoxlanılmış qaydalar — eyni prosedur, eyni lövbərləmə — FR1-in ssenari trayektoriyaları (sektorların real
# ƏD-si, kredit faiz dərəcəsi, kredit, qeyri-neft ÜDM) və FR10-un regional sənaye buraxılışı ilə idarə olunmaqla sonuncu
# başlanğıcda (fəaliyyət 2024, regionlar 2025) tətbiq edilir. Qiymət-xərc marjası trayektoriyası: sənaye üçün FR10-un
# bölmə proqnozları (B–E: (ƏD − əməyin ödənilməsi) / buraxılış) 2025 səviyyəsinə dəyişiklik kimi tətbiq olunur; digər
# qruplar üçün 2025 səviyyəsində saxlanılır (açıq göstərilmiş fərziyyə). Doğumlar log modelin medianıdır (geri çevirmə
# yoxdur); ehtiyat $N_t = (N_{t-1}+B_t)/(1+x_t)$ eyniliyinə tabedir ($N_t = N_{t-1} + B_t - D_t$, əmsallar ilin sonundakı
# ehtiyat üzrə); giriş əmsalı $B_t/N_t$-dir. Fəaliyyət qrupları üçün 2025 cari qiymətləndirmədir (nowcast) (2025 üzrə 006
# hələ dərc olunmayıb). Nümunədən kənarda `brk` = 1, 2022 impulsu = 0.

# %%
_sf = FR10_SECF.groupby(['scenario', 'year']).apply(lambda d: ((d.VA - d.CE).sum() / d.output.sum()) * 100)
def pcm_path(g, scen, y):
    base = float(PCM_G.PCM.get((g, LAST_ACT)))
    if g != 'IND' or y <= LAST_ACT: return base
    return base + float(_sf.loc[(scen, y)] - _sf.loc[(scen, LAST_ACT)])

def drivers_activity(scen='Baseline', draw=None):
    src = FR1D[FR1D.draw == draw].set_index('year') if draw is not None else FR1F[FR1F.scenario == scen].set_index('year')
    va = pd.concat([VAH.loc[[2024, LAST_ACT]], pd.DataFrame({g: src[GROUPS[g][2]].sum(axis=1) for g in GRP})])
    lend = pd.concat([FR1H.lendrate.loc[[LAST_ACT]], src.lendrate]); cr = pd.concat([FR1H.rcred_tot.loc[[2024, LAST_ACT]], src.rcred_tot])
    rows = []
    for y in [LAST_ACT] + FC_YEARS:
        for g in GRP:
            rows.append(dict(unit=g, year=y, dem=float(np.log(va.loc[y, g] / va.loc[y - 1, g]) * 100), size=float(np.log(va.loc[y, g])),
                             lend=float(lend.loc[y]), cred=float(np.log(cr.loc[y] / cr.loc[y - 1]) * 100), pcm=pcm_path(g, scen, y), brk=1.0, d2022=0.0))
    return pd.DataFrame(rows)

def drivers_region(scen='Baseline', draw=None):
    rf = FR10_REGF[FR10_REGF.scenario == scen].set_index('year')[REGS]
    src = FR1D[FR1D.draw == draw].set_index('year') if draw is not None else FR1F[FR1F.scenario == scen].set_index('year')
    non = pd.concat([FR1H.rgdpnon.loc[[LAST_ACT]], src.rgdpnon])
    non_b = pd.concat([FR1H.rgdpnon.loc[[LAST_ACT]], FR1F[FR1F.scenario == scen].set_index('year').rgdpnon])
    rows = []
    for y in FC_YEARS:
        d_non = np.log(non.loc[y] / non.loc[y - 1]) * 100; sh = d_non - np.log(non_b.loc[y] / non_b.loc[y - 1]) * 100 if draw is not None else 0.0
        for u in REGS:
            g = np.log(rf.loc[y, u] / rf.loc[y - 1, u]) * 100 + sh      # FR1 macro uncertainty passed to regional output
            lv = np.log(rf.loc[y, u]) + (np.log(non.loc[y] / non_b.loc[y]) if draw is not None else 0.0)
            rows.append(dict(unit=u, year=y, reg=float(g), size=float(lv), non=float(d_non), lend=float(src.lendrate.loc[y])))
    return pd.DataFrame(rows)
DRV = {'activity': drivers_activity, 'region': drivers_region}
ORIG = {'activity': 2024, 'region': LAST_ACT}

def rule_pred(F, rows, b=None):
    '''Rule forecast; with a slope draw b the unit effects (and the anchor) re-adjust, so the draw acts on driver
    deviations from the unit's in-sample mean (unanchored) or from its last training value (anchored).'''
    if F['m1'] is None: return predict(F['m0'], rows)
    m1 = F['m1']; p1 = predict(m1, rows) + (rows.unit.map(F['shift']).to_numpy(float) if F['shift'] is not None else 0.0)
    if b is not None:
        d = m1['d'].sort_values('year'); ref = d.groupby('unit')[m1['regs']].last() if F['shift'] is not None else d.groupby('unit')[m1['regs']].mean()
        dev = rows[m1['regs']].to_numpy(float) - ref.reindex(rows.unit).to_numpy(float)
        p1 = p1 + dev @ (np.asarray(b) - m1['b'])
    return F['wt'] * p1 + (1 - F['wt']) * predict(F['m0'], rows)

FINAL = {}
for pn in PANELS:
    X = DRV[pn]('Baseline')
    for dep in ['lnB', 'exit']:
        FINAL[(pn, dep)] = apply_rule((pn, dep), SELECT[(pn, dep)]['rule'], ORIG[pn], X, COHLOG)
COHTAB = pd.DataFrame(COHLOG).drop_duplicates(subset=['key', 'origin', 'driver'])
FC = []
for sc in SCEN:
    for pn in PANELS:
        X = DRV[pn](sc).sort_values(['unit', 'year']).reset_index(drop=True)
        N0 = PANELS[pn][PANELS[pn].year == ORIG[pn]].set_index('unit').N
        S = stock_rates(X, rule_pred(FINAL[(pn, 'lnB')], X), rule_pred(FINAL[(pn, 'exit')], X), N0)
        FC.append(S.rename(columns={'x': 'exit'}).assign(scenario=sc, panel=pn))
FC = pd.concat(FC, ignore_index=True)
AGG = FC.groupby(['scenario', 'panel', 'year'])[['N', 'new', 'exits']].sum().reset_index()
AGG['entry'] = AGG.new / AGG.N * 100; AGG['exit'] = AGG.exits / AGG.N * 100
_ch = FC.sort_values(['scenario', 'panel', 'unit', 'year']).copy()
_ch['N_prev'] = _ch.groupby(['scenario', 'panel', 'unit']).N.shift()
_sfg = float((_ch.N - (_ch.N_prev + _ch.new - _ch.exits)).abs().max())
chk('stock-flow identity N(t) = N(t-1) + births(t) - deaths(t) in every forecast path', _sfg, _sfg < 1e-6)
display(AGG[AGG.year.isin([2025, 2026, 2028, 2030])].pivot_table(index=['panel', 'year'], columns='scenario', values=['new', 'entry', 'exit', 'N']).round(2))
print('applied rules at the last origin: ' + '; '.join(f"{k[0]}/{k[1]}: {rname(SELECT[k]['rule'])} -> drivers kept {FINAL[k]['spec']}, implied RW weight {FINAL[k]['w_rw']:.2f}" for k in FINAL))
