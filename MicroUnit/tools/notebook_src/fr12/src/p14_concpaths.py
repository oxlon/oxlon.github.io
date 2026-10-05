# %% [markdown]
# ## Hissə 14 — Konsentrasiya yolları: KOB pay sistemi və proqnozlaşdırılan hədlər
#
# Aqreqat məlumatlarla konsentrasiya yolu yalnız **ölçü strukturu** vasitəsilə identifikasiya olunur: hər qrupun
# buraxılışında KOB-ların payı (log-şanslar, belə ki, paylar (0,1) aralığında qalır) qrup sabit effektləri ilə FR1-in sektor
# trayektoriyaları ilə idarə olunur, Hissə 12-dəki eyni prosedurla seçilir və yoxlanılır (seçim 2022 → 2023, nümunədən kənar
# yoxlamanın hədəfi 2024). Proqnozlaşdırılan hədlər proqnozlaşdırılan iri müəssisə payını proqnozlaşdırılan ehtiyatla
# (Hissə 13) birlikdə artan KOB qrupları üzrə saylarla və 2026-cı ilin iyul səviyyəsində saxlanılan iri vahidlərin sayı ilə
# birləşdirir; hər qrupun hədd rejimi hər il Hissə 8-də istifadə olunanla eynidir. **İdentifikasiya məhdudiyyəti**: hədlər
# yalnız iri müəssisə payı və müəssisələrin sayı vasitəsilə dəyişir; iri qrupun *daxilində* konsentrasiyanı müəssisə
# məlumatları olmadan (B qatı) proqnozlaşdırmaq mümkün deyil.

# %%
PS = SME.reset_index()[['group', 'year', 'sme_output_share']].rename(columns={'group': 'unit'})
PS = PS[PS.unit.isin(GRP)].merge(PA[['unit', 'year', 'dem', 'size', 'lend', 'cred']], on=['unit', 'year'], how='left')
PS['lo'] = np.log(PS.sme_output_share / (100 - PS.sme_output_share))
MODELS[('sme', 'lo')] = dict(df=PS, fixed=[], specs=[[], ['dem'], ['size'], ['lend'], ['dem', 'lend']], sel=(2022, [2023]),
                             hold=[(2022, [2024]), (2023, [2024])], scale='log-odds SME output share')
select_rule(('sme', 'lo'))
_h = []
for origin, tgs in MODELS[('sme', 'lo')]['hold']:
    tr = PS[PS.year <= origin]; rows = PS[PS.year.isin(tgs)]
    pm = apply_rule(('sme', 'lo'), SELECT[('sme', 'lo')]['rule'], origin, rows, COHLOG)['pred']; pn_ = apply_rule(('sme', 'lo'), NULLR, origin, rows)['pred']
    last = tr.sort_values('year').groupby('unit').lo.last(); cm = tr.groupby('unit').lo.mean()
    for u_, y_, a1, m1, n1 in zip(rows.unit, rows.year, rows.lo, pm, pn_):
        _h.append(dict(panel='sme', metric='log-odds SME output share', origin=origin, unit=u_, target=y_, actual=a1, rule=m1, null=n1, rw=last[u_], constant=cm[u_]))
_h = pd.DataFrame(_h); HOLDTAB = pd.concat([HOLDTAB, _h], ignore_index=True)
e = {k: _h[k] - _h.actual for k in ['rule', 'null', 'rw', 'constant']}
lu = pd.DataFrame({k: v ** 2 for k, v in e.items()}).assign(u=_h.unit.values).groupby('u').mean()
HOLDV = pd.concat([HOLDV, pd.DataFrame([dict(panel='sme', metric='log-odds SME output share', rule=rname(SELECT[('sme', 'lo')]['rule']),
    implied_rw_weight=SELECT[('sme', 'lo')]['w_rw'], n=len(_h), targets='2024', rmse_rule=float(np.sqrt((e['rule'] ** 2).mean())),
    rmse_null=float(np.sqrt((e['null'] ** 2).mean())), rmse_rw=float(np.sqrt((e['rw'] ** 2).mean())), rmse_constant=float(np.sqrt((e['constant'] ** 2).mean())),
    theil_rule_vs_rw=theil(e['rule'], e['rw']), theil_rule_vs_constant=theil(e['rule'], e['constant']), theil_null_vs_rw=theil(e['null'], e['rw']),
    theil_constant_vs_rw=theil(e['constant'], e['rw']), dm_p_rule_vs_rw=dm_hln(lu.rule.values, lu.rw.values)[1],
    dm_p_rule_vs_constant=dm_hln(lu.rule.values, lu.constant.values)[1])])], ignore_index=True)
_cls = E012.drop('TOT', level=0, errors='ignore').xs(2024, level=1)
CP = []
for sc in SCEN:
    X = drivers_activity(sc)
    FS = apply_rule(('sme', 'lo'), SELECT[('sme', 'lo')]['rule'], 2024, X)
    X['sme'] = 100 / (1 + np.exp(-FS['pred']))
    Nf = FC[(FC.scenario == sc) & (FC.panel == 'activity')].set_index(['unit', 'year']).N
    for _, r in X.iterrows():
        g, y = r.unit, int(r.year)
        s24 = float(PA[(PA.unit == g) & (PA.year == 2024)]['size'].iloc[0])
        mkt = float(GO_G.loc[y, g]) if y in GO_G.index else float(GO_G.loc[LAST_ACT, g]) * np.exp(r['size'] - float(np.log(VAH.loc[LAST_ACT, g])))
        grow = Nf.get((g, y), np.nan) / float(PA[(PA.unit == g) & (PA.year == 2024)].N.iloc[0])
        n = {c: float(E005.loc[(g, 2024), c]) * grow for c in CAP}; nL = float(SIZE_G.loc[g, 'large'])
        S = {c: r.sme / 100 * _cls.loc[g, c] / _cls.loc[g, 'sme'] for c in CAP}; SL = 1 - r.sme / 100
        b = hhi_bounds(n, S, nL, SL, mkt, CAPPED[g])
        CP.append(dict(scenario=sc, group=g, year=y, sme_output_share=r.sme, large_share=SL * 100, hhi_lower=b['hhi_lower'] * 1e4,
                       hhi_upper=b['hhi_upper'] * 1e4, hhi_upper_floor30=b['hhi_upper_floor30'] * 1e4, cr4_upper=b['cr4_upper'] * 100, cr4_lower=b['cr4_lower'] * 100))
CONCP = pd.DataFrame(CP)
_j = CONCP[CONCP.scenario == 'Baseline'].sort_values(['group', 'year']).groupby('group').hhi_upper.apply(lambda s: (s.pct_change().abs()).max())
chk('projected upper bounds evolve continuously (max year-on-year change < 25%)', float(_j.max()), bool(_j.max() < 0.25))
CONCP.drop(columns=['cr4_lower']).to_csv(OUT / 'FR12_concentration_paths.csv', index=False)      # cr4_lower: in FR12_forecast_tidy.csv (v2)
BND.to_csv(OUT / 'FR12_concentration_bounds.csv', index=False)
display(HOLDV[HOLDV.panel == 'sme'].round(3))
display(CONCP[(CONCP.scenario == 'Baseline') & CONCP.year.isin([2026, 2030])].pivot_table(index='group', columns='year', values=['large_share', 'hhi_lower', 'hhi_upper']).round(1))
