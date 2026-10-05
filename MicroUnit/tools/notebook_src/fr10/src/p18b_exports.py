# %% [markdown]
# ### 18.2 Nəticə faylları

# %%
written = []
def save(df, name, index=True):
    p = OUT / f'FR10_{name}.csv'; df.to_csv(p, index=index); written.append((p.name, len(df)))
def long_frame(dct, value='value'):
    return pd.concat({k: (v.stack() if isinstance(v, pd.DataFrame) else v) for k, v in dct.items()}, names=['series', 'year', 'unit']).rename(value).reset_index()
SCORE = pd.DataFrame({'branch': [BNAME[b] for b in BCODES], 'section': [SECT[BSEC[b]] for b in BCODES],
                      f'share_of_industry_{LAST_ACT}_pct': SH_IND.loc[LAST_ACT, BCODES].values * 100,
                      'real_growth_2020_25_pct_pa': [avg_g(Q[b], 2020, LAST_ACT) for b in BCODES],
                      f'lp_{LAST_ACT}_thsd_AZN': LP_GO.loc[LAST_ACT, BCODES].values,
                      f'inv_rate_2023_25_pct': INV_RATE.loc[2023:LAST_ACT, BCODES].mean().values,
                      f'nonstate_share_{LAST_ACT}_pct': NS.loc[LAST_ACT, BCODES].values * 100,
                      'forecast_real_growth_2026_30_pct_pa': BR_FC['real growth % pa'].values}, index=BCODES)
SCORE = SCORE.join(EW[['margin_2023_25', 'n_flags', 'watch_list']]).join(PLAUS[['flag']].rename(columns={'flag': 'plausibility_flag'}))
save(SCORE.rename_axis('nace2'), 'branch_scorecard')
save(QUAD.rename_axis('nace2'), 'quadrant')
save(long_frame({'share_of_industry_pct': SH_IND * 100, 'share_of_manufacturing_pct': SH_MAN * 100}), 'branch_shares_history', False)
save(long_frame({'output_nominal_mn_AZN': GO, 'output_real_mn_AZN_2015': Q, 'deflator_2015_1': PDEF, 'nonstate_share': NS[BCODES],
                 'enterprises': NENT[BCODES], 'investment_mn_AZN': INV[BCODES], 'stocks_end_year_mn_AZN': STK.reindex(columns=BCODES),
                 'employees': EMPC, 'wage_AZN_month': WAGEC, 'va_nominal_NA': NA_VA}), 'branch_history', False)
fb = []
for s_ in SCEN:
    S = SOL[s_]
    for k_, nm_ in [('nom', 'output_nominal_mn_AZN'), ('real', 'output_real_mn_AZN_2015'), ('sh_ind', 'share_of_industry'),
                    ('sh_man', 'share_of_manufacturing'), ('emp', 'employees'), ('lp', 'lp_thsd_AZN_2015'), ('wage', 'wage_AZN_month'), ('gosp', 'gos_proxy_margin_pct')]:
        t = S[k_].stack().rename('value').reset_index(); t.columns = ['year', 'nace2', 'value']
        fb.append(t.assign(scenario=s_, indicator=nm_))
save(pd.concat(fb)[['scenario', 'indicator', 'year', 'nace2', 'value']], 'forecast_branches', False)
save(pd.concat({s_: SOL[s_]['sec_fin'].join(SOL[s_]['sec_go'].stack().rename('output').rename_axis(['year', 'sec']).swaplevel())
                for s_ in SCEN}, names=['scenario']), 'forecast_sections')
save(FAN, 'fan_charts')
save(pd.DataFrame([FAN_META]), 'fan_meta', False)
save(SCEN_SUM.rename_axis('scenario'), 'scenario_summary')
conc_f = pd.DataFrame({f'HHI manufacturing branches, {s_}': hhi(SOL[s_]['sh_man']).loc[FC_YEARS] for s_ in SCEN})
save(pd.concat([CONC, conc_f], axis=1), 'concentration')
save(pd.concat([own, pd.DataFrame({f'forecast non-state share %, {s_}': SOL[s_]['ns_share'].loc[FC_YEARS] * 100 for s_ in SCEN})], axis=1), 'ownership')
save(long_frame({'output_mn_AZN': REG_GO, 'share': REG_SH, 'nonstate_share': REG_NS, 'enterprises': REG_NENT, 'volume_index': REG_VI}), 'regional_history', False)
save(pd.concat({s_: pd.concat({'share': SOL[s_]['reg_sh'], 'output_mn_AZN': SOL[s_]['reg_go']}, axis=1) for s_ in SCEN}, names=['scenario', 'year']), 'forecast_regions')
save(REG_ENTRY, 'regional_entry_exit', False)
save(PROD_VIEW.rename_axis('product'), 'products')
save(EW.rename_axis('nace2'), 'early_warning')
save(SEC_FIN, 'financial_sections')
save(pd.concat([DVX_M, DVX], axis=1).rename_axis('year'), 'dvx_declarations')
save(GROWTH_CONTRIB.rename_axis('year'), 'growth_contributions')
save(DET, 'determinants_panel', False)
save(long_frame({'lp_output_thsd_AZN_2015': LP_GO, 'lp_va_thsd_AZN_2015': LP_VA, 'ic_share': IC_SH, 'capital_productivity': KPROD,
                 'investment_rate_pct': INV_RATE, 'innovation_intensity_pct': INNOV_INT, 'gos_proxy_margin_pct': GOSP}), 'efficiency_branches', False)
save(TFP_SUM.rename_axis('branch'), 'tfp_branches'); save(SEC_TFP, 'tfp_sections')
save(WPG.rename(index=BNAME).rename_axis('branch'), 'wage_productivity_gap')
save(SRC_MATRIX.rename_axis('id'), 'data_source_matrix'); save(GAPS.rename_axis('id'), 'data_gaps_and_alternatives')
save(FINDINGS, 'data_integrity_findings'); save(PRES, 'presentation_spec', False); save(NOAR, 'noar_constructs', False)
sel = []
for nm, lab in [('C', 'manufacturing'), ('B', 'mining'), ('R', 'regions')]:
    sel.append(SELECT[nm]['table'].assign(system=lab, stage='specification'))
    if SELECT[nm]['ktable'] is not None: sel.append(SELECT[nm]['ktable'].assign(system=lab, stage='shrinkage'))
save(pd.concat(sel).rename_axis('candidate'), 'share_system_selection')
save(SHARE_COEF if len(SHARE_COEF) else pd.DataFrame([{'note': 'no estimated slopes: constant-share systems'}]), 'share_system_coefficients', False)
save(HOLD, 'holdout_validation', False); save(HOLD_PER['C'].rename_axis('branch'), 'holdout_branches')
save(PLAUS, 'plausibility'); save(LEVERS.rename_axis('lever'), 'sensitivity_levers')
save(pd.DataFrame(REJ), 'rejected_specifications', False); save(CHK_T, 'identity_checks', False)
save(MANIFEST, 'dsk_manifest', False)
ASSUME = pd.DataFrame([('section output', 'output/VA ratio held at 2025', 'FR1 nominal VA'), ('non-oil branch relative prices', 'held at 2025', '-'),
                       ('refining real output', '2023-25 average throughput (capacity)', 'DSK 018'), ('refining price', 'oil export price in manat, estimated elasticity; exchange rate held', 'FR1 oil price'),
                       ('labour share of VA (margin baseline)', 'held at 2023-25 average', '-'),
                       ('within-branch non-state shares', 'held at 2025', '-'), ('within-section employment shares', 'held at 2025', 'FR4 section index'),
                       ('branch wages (sensitivity, productivity)', '2025 DSK wage x FR1 average-wage index', 'FR1 wage'), ('other taxes on production / VA', 'held at 2025', '-'),
                       ('branch VA / output', 'held at 2025', '-'), ('SME shares', 'held at 2024 (no time series)', '-')],
                      columns=['object', 'forecast rule', 'driver'])
save(ASSUME, 'forecast_assumptions', False)
save(OILB, 'oil_linked_block'); save(PSEL.rename_axis('candidate'), 'nonoil_allocation_selection')
save(pd.DataFrame([dict(**POOL_EST, mode=MAN_MODE)]), 'pooled_related_sector_model', False)
save(MULT.rename_axis('nace2'), 'cross_sector_multipliers'); save(pd.DataFrame([NONOIL_HIST]), 'nonoil_growth_vs_history', False)
save(DIVB, 'determinants_division_bias', False); save(PRODF, 'product_forecasts_derived', False)
save(PMS.rename_axis('product'), 'product_location_shares'); save(NS_TAB.rename_axis('nace2'), 'nonstate_composition')
save(pd.DataFrame([NS_COMP]), 'nonstate_composition_summary', False)
save(BR_FC.rename_axis('nace2'), 'branch_growth_table')
save(pd.concat([T08.assign(branch='08'), T07.assign(branch='07')]).rename_axis('rule'), 'mining_rules_selection')
save(pd.DataFrame([dict(**MINING_RULES, **MIN_REC)]), 'mining_reconciliation', False)
print(f'{len(written)} FR10 files written to {OUT} (plus {len(list(OUT.glob("FR10_SYNTHETIC_*.csv")))} SYNTHETIC files)')
display(pd.DataFrame(written, columns=['file', 'rows']))
