# %%
# --- A2: mining rules (quarrying elasticity to construction; metal ores rule), both chosen pre-cut
_f08 = ols(np.log(Q['08']).diff().loc[2006:LAST_ACT], np.log(F1H['rva_con']).diff().loc[2006:LAST_ACT].rename('x').to_frame())
assert abs(_f08.beta[1] - E08_EST) < 1e-12
_won = MINING_RULES['rule08'].startswith('unit')                # v2: unit link adopted only if it beats the neutral null pre-cut
_u8 = T08.loc['unit elasticity to construction']
_q8c = [CID(c, '08') for c in ('output_nominal_mn_AZN', 'output_real_mn_AZN_2015', 'share_of_industry')] + \
       [CID(c, b) for b in ('06', '09') for c in ('output_nominal_mn_AZN', 'share_of_industry')]
eM8 = reg_ols('FR10.mining_08', _f08, _won, _q8c, SUB['B'],
              'Digər faydalı qazıntılar (08): FR1 tikinti əlavə dəyərinə elastiklik', 'Quarrying (08): elasticity to FR1 construction value added',
              'Δ ln real buraxılış (08)', 'dlnQ_08', editable=['x'],
              restrictions=[dict(text_az='Vahid elastiklik (β = 1): tam nümunədə məlumatla rədd edilir' if UNIT08_TEST['p'] < 0.05 else 'Vahid elastiklik (β = 1)',
                                 test=f"HAC t(n−k={UNIT08_TEST['df']})", stat=UNIT08_TEST['t'], p=UNIT08_TEST['p'], imposed=_won),
                            dict(text_az='Vahid elastiklik qaydası (son faktiki ilə lövbərlənmiş) neytral qaydadan (son faktiki səviyyə sabit) ilkin yoxlamada əhəmiyyətli dərəcədə dəqiqdir',
                                 test='DM/HLN, hədəf ili üzrə (2019-a qədər)', stat=None, p=float(_u8.DM_p_vs_first), imposed=_won,
                                 rmse_neutral=float(T08.iloc[0].RMSE_log_pct), rmse_unit=float(_u8.RMSE_log_pct),
                                 rmse_estimated=float(T08.loc['estimated elasticity to construction'].RMSE_log_pct))],
              extra=dict(rule08=MINING_RULES['rule08'], e08_link=float(MINING_RULES['e08']), e08_estimated=float(E08_EST), e08_se=float(E08_SE),
                         precut_table=T08.reset_index().to_dict('records')),
              notes=('Vahid elastiklik qaydası seçilib (neytral qaydadan əhəmiyyətli dərəcədə dəqiq). ' if _won else
                     f'Vahid məhdudiyyət tam nümunədə rədd edilir (p = {UNIT08_TEST["p"]:.3f}) və ilkin yoxlamada neytral qaydadan dəqiq deyil '
                     f'(DM p = {_u8.DM_p_vs_first:.3f}): baza proqnozu neytral qaydadır (FR10.mining_08_rule); tikinti əlaqəsi rıçaq kimi saxlanılır. ')
                    + 'Sərbəst qiymətləndirmə qeyri-stabildir; neft-qaz hissəsi (06, 09) mədənçıxarma cəminin qalığıdır.')
set_used(eM8, 'x', MINING_RULES['e08'] if _won else None, **({'imposed_value': float(MINING_RULES['e08'])} if _won else {}))
set_used(eM8, 'const', None)
_y8 = np.log(Q['08']).loc[2005:LAST_ACT].rename('ln_Q_08')
REGX.add('FR10.mining_08_rule', _y8, None, estimator='Calibrated rule: anchored null, real output constant at the last actual level',
         cov='calibrated (no s.e.)', fit_coef={'level_factor_vs_2025': float(MINING_RULES['q08_level_factor'])}, fit_se={}, components=_q8c,
         subtask=SUB['B'], title_az='Digər faydalı qazıntılar (08): neytral qayda — real buraxılış 2025 faktiki səviyyəsində sabit',
         title_en='Quarrying (08): anchored null, real output constant at its 2025 actual level', dependent_label_az='ln real buraxılış (08)',
         used_in_forecast=not _won, editable=[], notes_az='Qiymət: FR1 tikinti deflyatoru. Seçim ilkin yoxlama pəncərələrində (2011–2017, hədəflər ≤ 2019).',
         extra=dict(precut_table=T08.reset_index().to_dict('records')))
_d07 = 'rva_min' if 'mining' in RULE07 else ('rva_con' if 'construction' in RULE07 else None)
RULE07_AZ = {'neutral: held at trailing 3-year average': 'neytral: son 3 ilin ortası səviyyəsində saxlanılır',
             'grows with FR1 mining VA': 'FR1 mədənçıxarma əlavə dəyəri ilə eyni tempdə artır',
             'grows with FR1 construction VA': 'FR1 tikinti əlavə dəyəri ilə eyni tempdə artır'}
_y7 = np.log(Q['07']).diff().loc[2006:LAST_ACT].rename('dlnQ_07')
if _d07:
    _x7 = np.log(F1H[_d07]).diff().loc[2006:LAST_ACT].rename(f'dln_{_d07}')
    eM7 = REGX.add('FR10.mining_07', _y7, _x7.to_frame(), estimator='Calibrated rule: unit elasticity, chosen pre-cut', cov='calibrated (no s.e.)',
                   fit_coef={f'dln_{_d07}': 1.0}, fit_se={}, resid=(_y7 - _x7), fitted=_x7, add_const=False,
                   components=[CID(c, '07') for c in ('output_nominal_mn_AZN', 'output_real_mn_AZN_2015', 'share_of_industry')], subtask=SUB['B'],
                   title_az=f'Metal filizləri (07): {RULE07_AZ.get(RULE07, RULE07)}', title_en=f'Metal ores (07): {RULE07}', dependent_label_az='Δ ln real buraxılış (07)',
                   editable=[f'dln_{_d07}'], notes_az='Qayda 2019-a qədərki pəncərələrdə neytral qaydadan əhəmiyyətli dərəcədə dəqiq olduğu üçün seçilib (DM p < 0.10).',
                   extra=dict(precut_table=T07.reset_index().to_dict('records')))
print(f'registry: mining rules registered; {len(REGX)} equations so far')

# --- A5: determinants panel (two-way FE, DK on t(T-1), wild cluster bootstrap), division-bias variants, between, co-movement
def _tw(d, dep, regs):
    w = _within(d, dep, regs, 'unit', 'year', True)               # exact two-way within transform (unbalanced panel)
    ix = pd.MultiIndex.from_arrays([w.unit.values, w.year.values], names=['unit', 'year'])
    return pd.Series(w[dep].values, index=ix, name=dep), pd.DataFrame(w[regs].values, index=ix, columns=regs)
DET_LAB = {'inv_rate_l1': 'investisiya norması, t−1', 'drelp_l1': 'Δ ln nisbi qiymət, t−1', 'nonstate_l1': 'qeyri-dövlət payı, t−1',
           'stocks_go_l1': 'ehtiyatlar / buraxılış, t−1', 'dln_ent_l1': 'Δ ln müəssisələrin sayı, t−1', 'dln_rwage_l1': 'Δ ln real əmək haqqı, t−1',
           'labour_share_l1': 'əməyin payı, t−1'}
DET_LAB.update({k + '_same': v + ' (eyni il məxrəci)' for k, v in DET_LAB.items()})
for spec, regs, yr0 in [('A', REGS1, 2011), ('B', REGS2, 2018)]:
    rows = DET[DET.spec.str.startswith(spec)].set_index('regressor')
    d = PNL[(PNL.year >= yr0) & (PNL.year <= LAST_ACT)].dropna(subset=['dlnQ_w'] + regs)
    yv, Xv = _tw(d, 'dlnQ_w', regs)
    REGX.add(f'FR10.det_{spec}', yv, Xv, estimator='FE-twoway (branch + year), within', cov='DK', fit_coef=rows.coef, fit_se=rows.se_DK,
             panel={'entity': 'unit', 'time': 'year', 'twoway': True}, components=[], subtask=SUB['D'], used_in_forecast=False,
             title_az=f'Sahə artımının amilləri, spesifikasiya {spec} ({yr0}–{LAST_ACT})', title_en=f'Determinants of branch real growth, spec {spec}',
             dependent_label_az='Δ ln real buraxılış ×100 (5/95% vinzorlaşdırılmış)', coef_labels_az=DET_LAB,
             notes_az='İki yönlü daxili çevirmə dəqiqdir (balanslaşdırılmamış panel); DK SE, t(T−1). Rekursiv/LOO yolları sadə ikiqat orta çıxarma ilə təqribidir.',
             extra=dict(p_wild_bootstrap=rows.p_wild.to_dict(), between_coef=rows.between_coef.to_dict(), between_p=rows.between_p.to_dict(),
                        branches=int(rows.branches.iloc[0]), years=int(rows.years.iloc[0])))
    bw = between_fit(d, 'dlnQ_w', regs)
    reg_ols(f'FR10.det_{spec}_between', bw, False, [], SUB['D'], f'Sahələr arası (between) qiymətləndirici, spesifikasiya {spec}',
            f'Between estimator (branch means), spec {spec}', 'sahə ortası: Δ ln real buraxılış', 'dlnQ_w_mean', cov='hc1',
            index=pd.RangeIndex(len(bw.y)), notes='Kəsişmə üzrə əlaqə (hansı növ sahələr sürətli böyüyür), sahə daxili təsir deyil; rekursiv/LOO sahələr üzrədir.')
    regs_s = [r + '_same' if r + '_same' in PNL else r for r in regs]
    d2 = PNL[PNL.year >= yr0].dropna(subset=['dlnQ_w'] + regs + regs_s)
    f2 = panel_fe(d2, 'dlnQ_w', regs_s); y2, X2 = _tw(d2, 'dlnQ_w', regs_s)
    REGX.add(f'FR10.det_{spec}_same', y2, X2, estimator='FE-twoway (branch + year), within', cov='DK', fit_coef=dict(zip(regs_s, f2.beta)),
             fit_se=dict(zip(regs_s, f2.se)), panel={'entity': 'unit', 'time': 'year', 'twoway': True}, components=[], subtask=SUB['D'],
             used_in_forecast=False, title_az=f'Amillər paneli {spec}: eyni il məxrəcli nisbətlər (bölmə sürüşməsi yoxlaması)',
             title_en=f'Determinants spec {spec}, same-year denominators (division-bias variant)', dependent_label_az='Δ ln real buraxılış ×100',
             coef_labels_az=DET_LAB, notes_az='Həssaslıq variantı: məxrəc t−1 ilində (əsas spesifikasiyada t−2).')
_dl = PNL.merge(pd.DataFrame({'year': F1H.index, 'dln_rva_man': np.log(F1H.rva_man).diff().values * 100}), on='year').dropna(subset=['dlnQ_w', 'dln_rva_man'])
_fl = panel_fe(_dl, 'dlnQ_w', ['dln_rva_man'], twoway=False)
_il = pd.MultiIndex.from_arrays([_dl.unit.values, _dl.year.values], names=['unit', 'year'])
REGX.add('FR10.det_link', pd.Series(_dl.dlnQ_w.values, index=_il), pd.DataFrame({'dln_rva_man': _dl.dln_rva_man.values}, index=_il),
         estimator='FE-oneway (branch), within', cov='DK', fit_coef={'dln_rva_man': float(_fl.beta[0])}, fit_se={'dln_rva_man': float(_fl.se[0])},
         panel={'entity': 'unit', 'time': 'year', 'twoway': False}, components=[], subtask=SUB['D'], used_in_forecast=False,
         title_az='Sahə artımının FR1 emal əlavə dəyəri ilə birgə hərəkəti (təsviri)', title_en='Co-movement of branch growth with FR1 manufacturing VA growth',
         dependent_label_az='Δ ln real buraxılış ×100', coef_labels_az={'dln_rva_man': 'Δ ln FR1 real emal əlavə dəyəri ×100'},
         notes_az='Təsviri: aqreqat qismən sahələrin cəmidir.')
print(f'registry: determinants panel registered; {len(REGX)} Layer-A equations')
