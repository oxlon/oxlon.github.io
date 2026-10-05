# %% [markdown]
# ### 18.1b Proqnoz cədvəlinin tamamlanması (v2): işçilərdə KOB-ların payı və NACE bölmələri üzrə reyestr axınları
#
# **İşçilərdə KOB-ların payı** (DSK 013) **buraxılışda KOB payı ilə eyni qaydalar ailəsi** ilə (Hissə 14) proqnozlaşdırılır:
# qrup sabit effektləri ilə log-şans payı; namizədlər: sıfır variantı, tələbin artımı, ölçü, kredit faiz dərəcəsi, tələb +
# kredit faiz dərəcəsi; ≤ 2022 məlumatlar üzrə seçim, 2023 üzrə qiymətləndirmə; ən yaxşı namizəd yalnız qruplar üzrə
# cütləşdirilmiş DM testi bərabər dəqiqliyi 10% səviyyəsində rədd etdikdə sıfır variantını əvəz edir (əks halda itkisi daha
# aşağı olduqda bərabər çəkili kombinasiya, əks halda sıfır variantı); toxunulmamış nümunədən kənar yoxlama (2022 və 2023
# başlanğıcları, hədəf 2024) təsadüfi gəzişmə və sabit müqayisə meyarlarına qarşı; sonuncu başlanğıcda (2024) uyğunluq
# filtri. Yalnız müşahidə olunan illər. Bu nəticələr yeni fayllara yazılır; Hissə 12-nin cədvəlləri dəyişdirilmir.

# %%
PSE = SME.reset_index()[['group', 'year', 'sme_employment_share']].rename(columns={'group': 'unit'})
PSE = PSE[PSE.unit.isin(GRP)].merge(PA[['unit', 'year', 'dem', 'size', 'lend', 'cred']], on=['unit', 'year'], how='left')
PSE['lo'] = np.log(PSE.sme_employment_share / (100 - PSE.sme_employment_share))
MODELS[('sme_emp', 'lo')] = dict(df=PSE, fixed=[], specs=[[], ['dem'], ['size'], ['lend'], ['dem', 'lend']], sel=(2022, [2023]),
                                 hold=[(2022, [2024]), (2023, [2024])], scale='log-odds SME employment share')
_nsel = len(SELTAB); select_rule(('sme_emp', 'lo')); SEL_EMP = pd.DataFrame(SELTAB[_nsel:])
_h = []
for origin, tgs in MODELS[('sme_emp', 'lo')]['hold']:
    tr = PSE[PSE.year <= origin]; rows = PSE[PSE.year.isin(tgs)]
    pm = apply_rule(('sme_emp', 'lo'), SELECT[('sme_emp', 'lo')]['rule'], origin, rows)['pred']; pn_ = apply_rule(('sme_emp', 'lo'), NULLR, origin, rows)['pred']
    last = tr.sort_values('year').groupby('unit').lo.last(); cm = tr.groupby('unit').lo.mean()
    for u_, y_, a1, m1, n1 in zip(rows.unit, rows.year, rows.lo, pm, pn_):
        _h.append(dict(panel='sme_emp', metric='log-odds SME employment share', origin=origin, unit=u_, target=y_, actual=a1, rule=m1, null=n1, rw=last[u_], constant=cm[u_]))
_h = pd.DataFrame(_h); e = {k: _h[k] - _h.actual for k in ['rule', 'null', 'rw', 'constant']}
lu = pd.DataFrame({k: v ** 2 for k, v in e.items()}).assign(u=_h.unit.values).groupby('u').mean()
HOLDV_EMP = pd.DataFrame([dict(panel='sme_emp', metric='log-odds SME employment share', rule=rname(SELECT[('sme_emp', 'lo')]['rule']), implied_rw_weight=SELECT[('sme_emp', 'lo')]['w_rw'],
    n=len(_h), targets='2024', rmse_rule=float(np.sqrt((e['rule'] ** 2).mean())), rmse_null=float(np.sqrt((e['null'] ** 2).mean())), rmse_rw=float(np.sqrt((e['rw'] ** 2).mean())),
    rmse_constant=float(np.sqrt((e['constant'] ** 2).mean())), theil_rule_vs_rw=theil(e['rule'], e['rw']), theil_rule_vs_constant=theil(e['rule'], e['constant']),
    theil_null_vs_rw=theil(e['null'], e['rw']), theil_constant_vs_rw=theil(e['constant'], e['rw']), dm_p_rule_vs_rw=dm_hln(lu.rule.values, lu.rw.values)[1],
    dm_p_rule_vs_constant=dm_hln(lu.rule.values, lu.constant.values)[1])])
HOLDV = pd.concat([HOLDV, HOLDV_EMP], ignore_index=True)                 # in memory only (FR12_holdout_validation.csv already written)
_coh_emp = []
FINAL_SMEEMP = apply_rule(('sme_emp', 'lo'), SELECT[('sme_emp', 'lo')]['rule'], 2024, drivers_activity('Baseline'), _coh_emp)
SMEEMP_FC = []
for sc in SCEN:
    X = drivers_activity(sc); X['share'] = 100 / (1 + np.exp(-rule_pred(FINAL_SMEEMP, X)))
    SMEEMP_FC += [dict(scenario=sc, group=r.unit, year=int(r.year), sme_employment_share=float(r.share)) for r in X.itertuples()]
SMEEMP_FC = pd.DataFrame(SMEEMP_FC)
_sx = SELECT[('sme_emp', 'lo')]
pd.concat([SEL_EMP.assign(table='selection (<= 2022 -> 2023)'), HOLDV_EMP.assign(table='hold-out'),
           pd.DataFrame([dict(table='rule', rule=rname(_sx['rule']), best_candidate=_sx['best'], dm_p_vs_null=_sx['dm_p'], applied_at_last_origin=', '.join(FINAL_SMEEMP['spec']) or 'no driver (null)',
                              coherence_last_origin='; '.join(f"{r['driver']}: {r['status']}" for r in _coh_emp))])], ignore_index=True).to_csv(OUT / 'FR12_sme_employment_model.csv', index=False)
# gap-fill sensitivity for the new equation (Part 14.1 rule): the filled 2021 share added
_e21 = FS_[(FS_.year == 2021) & FS_.imputed & (FS_['var'] == 'sme_employment_share')][['unit', 'year', 'value']].rename(columns={'value': 'sme_employment_share'})
PSE_F = pd.concat([PSE, _e21.merge(PA_F[['unit', 'year', 'dem', 'size', 'lend', 'cred']], on=['unit', 'year'], how='left')], ignore_index=True)
PSE_F['lo'] = np.log(PSE_F.sme_employment_share / (100 - PSE_F.sme_employment_share)); PSE_F = PSE_F.sort_values(['unit', 'year']).reset_index(drop=True)
_FSe = _with_df(('sme_emp', 'lo'), PSE_F, lambda: apply_rule(('sme_emp', 'lo'), SELECT[('sme_emp', 'lo')]['rule'], 2024, drivers_activity('Baseline')))
GAPSENS[('sme_emp', 'lo')] = dict(F=_FSe, F0=FINAL_SMEEMP, df=PSE_F)
_rows = []
for sc in SCEN:
    X = drivers_activity(sc); m30 = (X.year == 2030).to_numpy()
    for g, a, b_ in zip(X.unit[m30], 100 / (1 + np.exp(-rule_pred(FINAL_SMEEMP, X)[m30])), 100 / (1 + np.exp(-rule_pred(_FSe, X)[m30]))):
        _rows.append(dict(kind='forecast_2030', item=f'fr12:conc:sme_employment_share:{g}', term=sc, observed_only=a, with_filled=b_, diff=b_ - a, rel_diff_pct=(b_ / a - 1) * 100,
                          note_az='2030 proqnozu: yalnız müşahidə vs doldurulmuş 2021 daxil'))
GAPSENS_T = pd.concat([GAPSENS_T, pd.DataFrame(_rows)], ignore_index=True); GAPSENS_T.to_csv(OUT / 'FR12_gapfill_sensitivity.csv', index=False)
display(HOLDV_EMP.round(3))
print(f"SME employment share: rule {rname(_sx['rule'])} (best {_sx['best']}, DM p vs null {_sx['dm_p']:.2f}); applied at 2024: "
      f"{', '.join(FINAL_SMEEMP['spec']) or 'null (no driver)'}; 2030 Baseline range {SMEEMP_FC[(SMEEMP_FC.year == 2030) & (SMEEMP_FC.scenario == 'Baseline')].sme_employment_share.min():.1f}-"
      f"{SMEEMP_FC[(SMEEMP_FC.year == 2030) & (SMEEMP_FC.scenario == 'Baseline')].sme_employment_share.max():.1f}%")
