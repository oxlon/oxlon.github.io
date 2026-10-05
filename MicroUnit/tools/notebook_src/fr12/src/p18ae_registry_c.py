# %%
_SUM = ECON['tables']['summary'].set_index('model').interpretation_az
for k in ['scp', 'mob_instability', 'mob_rank']:
    r = EM[k]['res']; G_cl = int(EM[k]['data'].nace2.nunique())
    lb_add(f'FR12.LB_{k}', MODEL_AZ[k], k.replace('_', ' '), {'scp': 'qiymət-xərc marjası, %', 'mob_instability': 'payların qeyri-sabitliyi, f.b.', 'mob_rank': 'sıra mobilliyi (1 − ρ)'}[k],
           k, EM[k]['y'], EM[k]['X'], 'least squares, section/year dummies, cluster(division)' if k == 'scp' else 'least squares, year dummies, cluster(division)', 'cluster(nace2)', r.params, r.bse, _SUM.get(k, ''), fit_df=G_cl - 1, p_dist='t',
           fitted=np.asarray(r.fittedvalues, float), res_ns=SimpleNamespace(rsquared=r.rsquared, rsquared_adj=r.rsquared_adj, aic=r.aic, bic=r.bic, llf=r.llf),
           extra=dict(clusters=G_cl, endogeneity_caveat_az='konsentrasiya və marja birgə müəyyənləşir (Demsets); əmsal səbəb-nəticə deyil' if k == 'scp' else None),
           summary=r.summary().as_text())
WLS_META = {'boone_pooled': ('ln mənfəət (mənfəətli müəssisələr)', 'ln_profit', 'bölmə × il'), 'boone_sector': ('ln mənfəət (mənfəətli müəssisələr)', 'ln_profit', 'bölmə × il'),
            'entrant_profile': ('ln gəlir', 'ln_revenue', 'bölmə × il × ölçü qrupu'), 'postentry_growth': ('nisbi ölçünün illik dəyişməsi (log)', 'g_rel', 'il')}
def wls_add(eid, k, W_, title_az, notes, true=None):
    f = W_['fit']; dat = W_['data']; ix = _mi(dat.firm_id, dat.year); dep_az, dep, fe = WLS_META.get(k, ('ln gəlir', 'ln_revenue', 'bölmə × il × ölçü qrupu'))
    lines = [f'Udulmuş sabit effektlər: {fe} ({f["n_fe"]}); klasterlər (qeyd): {f["G"]}; daxili R² {f["r2_within"]:.4f}; nəticə t(G−1).']
    if true: lines.append('Həqiqi (generator) dəyərlər: ' + ', '.join(f'{c} = {v:+.3f}' for c, v in true.items()))
    lb_add(eid, title_az, k.replace('_', ' '), dep_az, dep, W_['y'].set_axis(ix), W_['X'].set_axis(ix), f'WLS, absorbed {fe} effects', 'cluster(record)',
           dict(zip(f['names'], f['b'])), dict(zip(f['names'], f['se'])), notes, fit_df=f['dof'], p_dist='t', fitted=f['fitted'],
           res_ns=SimpleNamespace(rsquared=f['r2_within']), extra=dict(absorbed_effects=fe, n_absorbed=f['n_fe'], clusters=f['G'], r2_type='within R²', true_values=true),
           summary='\n'.join(lines))
for k, W_ in ECON['wls'].items():
    wls_add(f'FR12.LB_{k}', k, W_, MODEL_AZ[k], _SUM.get(k, ''))
_sy = ECON['tables'].get('boone_sector_year')
if _sy is not None:
    _q = _sy.dropna(subset=['boone_beta'])
    lb_add('FR12.LB_boone_sector_year', 'Boone indikatoru: bölmə-il üzrə kəsişmə reqressiyaları', 'Boone indicator per section-year', 'ln mənfəət (mənfəətli müəssisələr)', 'ln_profit',
           None, None, 'WLS per section-year (HC0), cross-section', 'HC0', {f'boone_{r.section}_{int(r.year)}': float(r.boone_beta) for r in _q.itertuples()},
           {f'boone_{r.section}_{int(r.year)}': float(r.boone_se) for r in _q.itertuples()},
           f'{len(_q)} bölmə-il reqressiyası (≥ 20 mənfəətli müəssisə); hər birində ln mənfəət ln orta dəyişən xərc üzrə (çəkili). Mənfi = səmərəli müəssisələr daha çox qazanır; '
           'yalnız mənfəətli müəssisələr: seçim əyilməsi. Marja (PCM) hesablanır, qiymətləndirilmir. Proqnozsuz.', extra=dict(n_regressions=int(len(_q)), csv=f"{ECON['prefix']}boone_sector_year.csv"))
if LBS and ECON['recovery'] is not None:
    rf = ECON['recovery_fits']; rc = ECON['recovery']
    t1 = rc[rc.block.str.startswith('G1')].set_index('parameter').true.to_dict(); t2 = rc[rc.block.str.startswith('G2')].set_index('parameter').true.to_dict()
    wls_add('FR12.LB_recovery_revenue', 'recovery_revenue', rf['recovery_revenue'], MODEL_AZ['recovery_revenue'],
            f"G1 örtük {rc[rc.block.str.startswith('G1')].covered.mean():.0%}: generatorun γ_s və gənc müəssisə cəriməsi (−0.7) bərpa olunur.", true=t1)
    g2 = rf['recovery_exit']['fit']; dat = rf['recovery_exit']['data']
    lb_add('FR12.LB_recovery_exit', MODEL_AZ['recovery_exit'], 'parameter recovery: exit hazard', 'çıxışlar (müəssisə sayı)', 'exits', (dat.event * dat.w).set_axis(_mi(dat.firm_id, dat.year)),
           rf['recovery_exit']['X'].set_axis(_mi(dat.firm_id, dat.year)), 'conditional ML, cell-year strata (Hausman-Hall-Griliches)', 'cluster(section×region)',
           dict(zip(g2['names'], g2['b'])), dict(zip(g2['names'], g2['se'])),
           f"G2 örtük {rc[rc.block.str.startswith('G2')].covered.mean():.0%}: gənc müəssisə çarpanı (ln 2) və mülkiyyətin sıfır təsiri bərpa olunur; ölçü qruplarının dizayn nisbətləri "
           "(HAZ) bərpa olunmur — generator ölümləri qruplaşdırılmış qeydlər üzrə seçir, HAZ müəssisə səviyyəsində təhlükə nisbəti deyil.",
           res_ns=SimpleNamespace(llf=g2['loglik']), extra=dict(true_values=t2, strata=g2['n_fe'], clusters=g2['G'], events=g2['events'], statsmodels_check_max_abs_diff=g2['check']),
           summary='Həqiqi (generator) dəyərlər: ' + ', '.join(f'{c} = {v:+.3f}' for c, v in t2.items()))
REGX.validate()
REGX.write(OUT / 'FR12_equations.json')
_js = json.load(open(OUT / 'FR12_equations.json', encoding='utf-8'))
_js['layer_b_data_mode'] = DATA_MODE; _js['notes_az'] = ('A qatı müşahidə edilmiş DSK/iş kitabı məlumatı üzrədir (data_mode = OBSERVED). B qatının tənlikləri '
                                                         + ('SİNTETİK reyestr üzrədir (synthetic: true) — texniki nümayiş, nəticə deyil.' if LBS else 'Nazirliyin real reyestri üzrədir.'))
json.dump(_js, open(OUT / 'FR12_equations.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, allow_nan=False)
from microlib.schema import validate_file
assert not validate_file(OUT / 'FR12_equations.json'), 'registry file fails the schema'
REGT = REGX.table()
display(REGT.groupby(['used', 'verdict']).size().rename('equations').reset_index())
print(f"FR12_equations.json: {len(REGX)} equations ({int(REGT.used.sum())} used in forecasting, {sum(e['synthetic'] for e in REGX.equations)} synthetic); "
      f"coefficient checks failed: {int((REGT.coef_match == False).sum())}; registry warnings: {len(REGX.warnings)}")
assert all(e['checks'].get('coef_match', True) for e in REGX.equations), 'registry coefficients differ from the notebook estimates'
