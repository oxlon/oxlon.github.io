# %%
# v2 blocks of the methodology document (registry, components, engine, robustness, strings, Layer-B econometrics)
_pre = 'SYNTHETIC_' if DATA_MODE == 'SYNTHETIC' else 'FIRM_'
_hdr = (f"**Data mode: {DATA_MODE}** ({PANEL_META['file']}, {PANEL_META['rows']:,} rows, {PANEL_META['firms']:,} firms, {PANEL_META['year_min']}–{PANEL_META['year_max']})"
        + (f' — **{SYN_MARK}** / *{SYN_AZ}*.' if DATA_MODE == 'SYNTHETIC' else '.'))
_rt = REG_T.assign(layer=np.where(REG_T.id.str.startswith('FR10.B_'), 'B', 'A'))
_g = _rt.groupby(['layer', 'subtask']).agg(equations=('id', 'size'), used_in_forecast=('used', 'sum'),
                                          stabil=('verdict', lambda v: int((v == 'stabil').sum())),
                                          qismen=('verdict', lambda v: int((v == 'qismən stabil').sum())),
                                          qeyri=('verdict', lambda v: int((v == 'qeyri-stabil').sum()))).reset_index()
_g.columns = ['layer', 'subtask', 'equations', 'used in forecast', 'stabil', 'qismən stabil', 'qeyri-stabil']
_ru = ROB[ROB.used_in_forecast & (ROB.layer == 'A')][['equation', 'estimator', 'verdict', 'failed_tests']]
G['v2_registry'] = (f"{len(REGX)} equations ({int((_rt.layer == 'A').sum())} Layer A, {int((_rt.layer == 'B').sum())} Layer B — "
                    f"{'SYNTHETIC, `synthetic: true`' if DATA_MODE == 'SYNTHETIC' else 'REAL'}); {int(_rt[_rt.layer == 'A'].used.sum())} Layer-A equations "
                    f"enter the forecast. Registry vs notebook: {len(REG_CHK)} coefficient checks, max abs difference {REG_CHK.abs_diff.max():.1e}.\n\n"
                    + mdt(_g, dflt='{:.0f}') + '\n\nEquations used in the forecast:\n\n' + mdt(_ru))
G['v2_tidy'] = (f"{len(COMP)} components ({', '.join(f'{k} {v}' for k, v in pd.Series([c['id'].split(':')[1] for c in COMP]).value_counts().items())}) × "
                f"{len(SCEN)} scenarios × {len(FC_YEARS)} years: complete (asserted); history from each series' first year; 5–95% bands for "
                f"{int(CATALOG.has_band.eq('true').sum())} components (Baseline). Not forecast, with the reason:\n\n"
                + mdt(NOT_FC[['id_pattern', 'label_az', 'reason_az']]))
_inp = ENG.inputs()
G['v2_engine'] = (f"Inputs: {len(_inp['exogenous'])} exogenous paths (FR1 drivers and FR4 indices, 2026–2030, per scenario), "
                  f"{len(_inp['coefficients'])} coefficients, {len(_inp['levers'])} levers. Self-test: " +
                  ', '.join(f"{s_} max rel. diff {v['max_rel_diff']:.1e} over {v['n_rows']} values" for s_, v in ENG_ST['detail'].items())
                  + f" — {'PASS' if ENG_ST['ok'] else 'FAIL'}; run time {ENG_ST['max_runtime_s']:.3f} s per scenario.\n\n"
                  + mdt(pd.DataFrame(_inp['coefficients'])[['eq_id', 'name', 'label_az', 'value', 'se', 'ci_low', 'ci_high']], dflt='{:.3f}'))
_sx2 = SENS[SENS.type.isin(['coefficient', 'lever'])].dropna(subset=['effect_low_pct']).copy(); _sx2['span'] = (_sx2.effect_high_pct - _sx2.effect_low_pct).abs()
_nz = _sx2[_sx2.span > 1e-9]
_top = _nz.sort_values('span', ascending=False).groupby('component').head(4).sort_values(['component', 'span'], ascending=[True, False])
_zero = [HL_AZ[h] for h in HL if h not in set(_nz.component)]
G['v2_sens'] = ('Robustness verdicts: ' + ', '.join(f'{l} {v}: {n}' for (l, v), n in ROB.groupby(['layer', 'verdict']).size().items())
                + '. Non-zero 2030 effects on the headline components (Baseline, % of the baseline value, −1 s.e. / +1 s.e. or lever low / high); '
                + ('no coefficient or lever moves: ' + '; '.join(_zero) + ' (they are FR1 paths). ' if _zero else '') + '\n\n'
                + mdt(_top[['component_az', 'type', 'input', 'effect_low_pct', 'effect_high_pct']], dflt='{:+.3f}')
                + '\n\nEach coefficient\'s largest 2030 effect on any component (± 1 s.e.):\n\n'
                + mdt(SENS[SENS.type == 'coefficient: largest effect on any component'][['input', 'component_az', 'effect_low_pct', 'effect_high_pct']], dflt='{:+.3f}'))
G['v2_strings'] = (f"{len(STR_AZ)} English strings in FR10's CSVs; " + ', '.join(f'{k} {v}' for k, v in STR_AZ.how.value_counts().items())
                   + f". Products with the official DSK Azerbaijani name: {len(PROD) - len(_np_)} of {len(PROD)}.")
_em = rd(f'{_pre}econ_models')
_cols = [c for c in ['model_id', 'estimator', 'dependent', 'n_obs', 'n_firms', 'r2', 'r2_type', 'auc', 'auc_oos', 'RTS', 'crs_p'] if c in _em]
_ec = rd(f'{_pre}econ_coefficients')
G['econ_models'] = (_hdr + '\n\n' + mdt(_em[_cols], fmt={'n_obs': '{:.0f}', 'n_firms': '{:.0f}'}, dflt='{:.3f}')
                    + '\n\nCoefficients (cluster-robust by firm):\n\n' + mdt(_ec[['model_id', 'term', 'coef', 'se', 'p', 'ci_low', 'ci_high']], dflt='{:.4f}')
                    + '\n\nInterpretation (Azerbaijani):\n\n' + '\n'.join(f"- **{r.model_id}**: {r.interpretation_az}" for r in rd(f'{_pre}econ_interpretation_az').itertuples()))
_rc = rd(f'{_pre}econ_recovery')
G['econ_recovery'] = ((mdt(_rc[['model_id', 'term', 'true', 'estimate', 'se', 'ci_low', 'ci_high', 'covered']].dropna(subset=['true']), dflt='{:.4f}')
                       + (f"\n\nOver {MC_R} replications of the structural layer (`FR10_SYNTHETIC_econ_recovery_mc.csv`): consistent estimators' mean 95% "
                          f"coverage {MC_SUM['mean_coverage'] * 100:.1f}% (minimum {MC_SUM['min_coverage'] * 100:.0f}%), largest |bias t| "
                          f"{MC_SUM['max_abs_bias_t']:.2f}; pooled OLS (production function, margin size effect) largest |bias t| "
                          f"{MC_SUM['pooled_max_abs_bias_t']:.0f} — the bias the within estimator removes.\n\n"
                          + mdt(MC[['model_id', 'term', 'true', 'mean_estimate', 'mc_sd', 'mean_se', 'coverage_95', 'bias_t']], dflt='{:.4f}')
                          if MC is not None else '')) if 'true' in _rc else 'REAL data: the true parameters are unknown; no recovery test.')
# v2.1 block: volume-index validation, product anchoring, regional shrinkage record
_vb = VI_FIX.groupby('nace2').apply(lambda d: ', '.join(f'{int(r.year)} ({r.test}, {r.index_published:g})' for r in d.sort_values('year').itertuples()),
                                   include_groups=False).rename('replaced (year, test, published index)')
_vt = pd.DataFrame({'branch': [BNAME[b] for b in _vb.index]}, index=_vb.index).join(_vb).join(
    DEFL_CHECK[[f'real_to_nominal_{LAST_ACT}_published_index', f'real_to_nominal_{LAST_ACT}', 'real_2030_Baseline', 'lp_2030_Baseline']])
_vt.columns = ['branch', 'replaced (year, test, published index)', f'real/nominal {LAST_ACT}, published indices', f'real/nominal {LAST_ACT}, validated',
               f'real output {FC_YEARS[-1]} (Baseline), mn AZN 2015', f'labour productivity {FC_YEARS[-1]}, thsd AZN 2015']
_nj = int((PRODF.jump_2026_pct.abs() > 25).sum())
_neb = sum(1 for e in REGX.equations for r in e['restrictions'] if r.get('kind') == 'eb_shrinkage')
G['v21'] = (f"Volume-index validation: **{len(VI_FIX)} branch-year indices replaced in {VI_FIX.nace2.nunique()} branches** "
            f"(T1 {int((VI_FIX.test == 'T1').sum())}, T2 {int((VI_FIX.test == 'T2').sum())}; {int((VI_FIX.year >= 2005).sum())} in 2005–{LAST_ACT}). "
            f"Bands from the {VI_BANDS['clean_branches']} branches T1 never flags: their one-year deflator changes 1996–{LAST_ACT} lie in "
            f"×{VI_BANDS['d1_min']:.2f}–×{VI_BANDS['d1_max']:.2f} (T1 band ×1/{VI_BAND_1Y:g}–×{VI_BAND_1Y:g}) and their deflators relative to "
            f"manufacturing 2005–{LAST_ACT} in {VI_BANDS['rel_min_2005']:.2f}–{VI_BANDS['rel_max_2005']:.2f} (T2 band 1/{VI_BAND_REL:g}–{VI_BAND_REL:g}). "
            f"After the fix every branch passes both tests in every year, and every branch's {FC_YEARS[-1]} real output is below section C real "
            f"output in all scenarios (largest: {REAL_CHECK.loc[REAL_CHECK.real_2030.idxmax(), 'nace2']}, {REAL_CHECK.real_2030.max():,.0f} vs "
            f"{REAL_CHECK.section_C_real_2030.min():,.0f}+ mn AZN 2015). Full list: `FR10_volume_index_validation.csv`; per-branch deflator ranges: "
            f"`FR10_branch_deflator_check.csv`.\n\n" + mdt(_vt.reset_index(), dflt='{:,.2f}')
            + f"\n\nProducts: anchored on the {LAST_ACT} actual; {_nj} of {len(PRODF)} products change by more than 25% from {LAST_ACT} to "
            f"{FC_YEARS[0]} (Baseline). Regional share equations: {_neb} coefficients carry an `eb_shrinkage` restriction (`imposed: true`, "
            "`fixed: true`) recording the estimate, prior mean, shrinkage weight, κ and τ² behind the value used in the forecast.")
