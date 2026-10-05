# %%
# --- A1/A2: manufacturing and mining share-system candidates (constant shares chosen; candidates as estimated at the 2019 cut)
for nm, sy, units in [('C', SYS_C, MANUF), ('B', SYS_B, MINING)]:
    sel = SELECT[nm]['table']
    for spec in ['scale', 'oil', 'scale+oil']:
        par = sy.fit(spec, CUT, kappa=1.0); xs = SPEC_X[spec]
        yrs = [y for y in sy.W.index if sy.est0 <= y <= CUT and sy.W.loc[y].notna().all() and sy.X.loc[y].notna().all()]
        hr = HOLD[(HOLD.system == sy.name + ' (Part 11 share systems)') & (HOLD.model == LABEL[spec]) & (HOLD.measure == 'shares_pp')
                  & (HOLD.weighting == 'unweighted')]
        srow = sel.loc[LABEL[spec]]
        ex = dict(selection_rmse_pp=float(srow.RMSE_pp), selection_dm_p_vs_best=None if pd.isna(srow.DM_p_vs_best) else float(srow.DM_p_vs_best),
                  chosen_system=LABEL[SELECT[nm]['chosen']], estimated_to=int(CUT))
        for k in [u for u in sy.units if u != sy.ref]:
            f = par[k]['fit']
            yl = sy.LO[k].loc[yrs]; Xl = sy.X.loc[yrs, xs]
            reg_lr(f'FR10.{"man" if nm == "C" else "min"}_{k}_{spec.replace("+", "_")}', f, yl, Xl, False,
                   [CID('share_of_manufacturing' if nm == 'C' else 'share_of_industry', k)], SUB[nm],
                   f'{BNAME[k]}: pay log-nisbəti, namizəd "{SPEC_AZ[spec]}" (2005–{CUT})',
                   f'{BNAME[k]}: share log-odds vs {BNAME[sy.ref]}, candidate "{LABEL[spec]}" (estimated to {CUT})',
                   f'ln(pay / {BNAME[sy.ref]} payı)', extra=ex, holdout=hold_block(hr.iloc[0]) if len(hr) else None,
                   notes=(f'Rədd edilmiş namizəd: seçim RMSE {srow.RMSE_pp:.3f} f.b.; seçilən sistem — {LABEL[SELECT[nm]["chosen"]]}. '
                          f'Nümunədən kənar yoxlama bloku sistem üzrədir (2020–{LAST_ACT}).'))
print(f'registry: manufacturing and mining share-system candidates registered; {len(REGX)} equations so far')

# --- A1: the pooled related-sector model (branch FE, first differences, DK, wild bootstrap), used in the forecast
_PP = P_POOL.set_index(['unit', 'year'])
_hf = HOLD_FULL[HOLD_FULL.selected & (HOLD_FULL.measure == 'nominal') & (HOLD_FULL.weighting == 'unweighted')].iloc[0]
_hb = dict(cut=int(CUT), years=list(HY), rmse=float(_hf.RMSE), theil_u_rw=float(_hf.U_vs_random_walk), theil_u_const=float(_hf.U_vs_constant_growth),
           dm_p_rw=float(_hf.DM_p_vs_rw), dm_p_const=float(_hf.DM_p_vs_cg), measure='nominal branch output, log-%', model=_hf.model)
eqP = REGX.add('FR10.pooled', _PP['y'], _PP[['x']], estimator='FE-oneway (branch), first differences', cov='DK',
               fit_coef={'x': BETA}, fit_se={'x': BETA_SE}, panel={'entity': 'unit', 'time': 'year', 'twoway': False},
               components=[CID(c, b) for b in NONOIL for c in ('output_nominal_mn_AZN', 'output_real_mn_AZN_2015', 'share_of_manufacturing', 'share_of_industry')],
               subtask=SUB['C'], title_az='Əlaqəli sektor modeli: qeyri-neft sahə payları (ümumi elastiklik β)',
               title_en='Pooled related-sector model of non-oil branch shares (common elasticity)',
               dependent_label_az='Δ ln sahənin qeyri-neft emalında payı', dependent_code='dln_share', coef_labels_az={'x': 'Δ ln(əlaqəli sektor / sektor cəmi)'},
               sign_expected={'x': +1}, holdout=_hb, editable=['x'],
               notes_az=(f'Proqnozda {"bu model" if MAN_MODE == "pooled" else "bu model ilə sabit payların bərabər çəkili kombinasiyası"} istifadə olunur '
                         f'(seçim: DM p = {PSEL.loc["pooled", "DM_p_vs_const"]:.3f}). Sahə trendləri (μ_b) proqnoza köçürülmür.'),
               extra=dict(p_wild_bootstrap=float(WILD_POOL), beta_levels=float(F_LEV.beta[0]), levels_inside_fd_ci=bool(POOL_EST['levels_inside_fd_ci']),
                          mode=MAN_MODE, combination_weight=1.0 if MAN_MODE == 'pooled' else 0.5, links=LINK,
                          selection=PSEL.reset_index().to_dict('records')))
_PL = pooled_panel(LAST_ACT, lev=True).set_index(['unit', 'year'])
REGX.add('FR10.pooled_lev', _PL['y'], _PL[['x']], estimator='FE-oneway (branch), levels', cov='DK', fit_coef={'x': float(F_LEV.beta[0])},
         fit_se={'x': float(F_LEV.se[0])}, panel={'entity': 'unit', 'time': 'year', 'twoway': False}, components=[], subtask=SUB['C'],
         title_az='Əlaqəli sektor modeli, səviyyə forması (uyğunluq yoxlaması)', title_en='Pooled related-sector model in levels (coherence check)',
         dependent_label_az='ln sahə payı', dependent_code='ln_share', used_in_forecast=False, notes_az='Səviyyə əmsalı fərq formasının 95% intervalı daxilindədir: '
         + ('bəli' if POOL_EST['levels_inside_fd_ci'] else 'xeyr'))

# --- A4: oil-linked block: price elasticity of the refining / chemicals deflator to the oil price in manat (first differences)
OIL_EQ = {}
for b in OIL_CAND:
    yb = np.log(PDEF[b]).diff().loc[2006:LAST_ACT]; xb = np.log(OILAZN).diff().loc[2006:LAST_ACT].rename('dln_oil_azn').to_frame()
    fo = ols(yb, xb); used = b in OIL; r_ = OILB.loc[b]
    comps = [CID(c, b) for c in ('output_nominal_mn_AZN', 'share_of_manufacturing', 'share_of_industry')] if used else []
    e = reg_ols(f'FR10.oil_{b}', fo, used, comps, SUB['O'], f'{BNAME[b]}: deflyatorun neft qiymətinə (manatla) elastikliyi',
                f'{BNAME[b]}: elasticity of the branch deflator to the oil price in manat', 'Δ ln sahə deflyatoru', f'dln_pdef_{b}',
                editable=['dln_oil_azn'] if used else [],
                restrictions=[dict(text_az='Güc (emal həcmi) qaydası ilkin yoxlamada (2019-a qədər) sektor tempindən dəqiqdir', test='DM/HLN',
                                   stat=float(r_.precut_DM_stat), p=float(r_.precut_DM_p), imposed=bool(used))],
                extra=dict(cap_factor_baseline=float(r_.cap_factor_baseline), cap_factor_max=float(r_.cap_factor_max),
                           precut_rmse_capacity=float(r_.precut_RMSE_capacity), precut_rmse_sector=float(r_.precut_RMSE_sector_rate)),
                notes=('Real buraxılış = emal həcmi (güc); qiymət = 2025 × (neft qiyməti indeksi)^ε. Sabit proqnoza köçürülmür.' if used else
                       'Güc qaydası rədd edilib: sahə qeyri-neft bölgüsünə daxildir; elastiklik proqnozda istifadə olunmur.'))
    set_used(e, 'const', None); OIL_EQ[b] = e
    if not used:
        for r in e['coefficients']: r['used_value'] = None
print(f'registry: pooled model, oil-linked block registered; {len(REGX)} equations so far')
