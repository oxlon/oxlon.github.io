# %% [markdown]
# ## Hissə 19 — v2: tənliklər reyestri, göstəricilər kataloqu, tam proqnoz cədvəli, ssenari mühərriki, dayanıqlıq
#
# ### 19.1 Tənliklər reyestri
#
# Bu notebook-un istənilən yerində qiymətləndirilmiş hər tənlik `microlib.registry` vasitəsilə qeydə alınır və
# `output/FR10_equations.json` faylına yazılır: pay sistemləri (2019-cu il kəsimində qiymətləndirildiyi kimi emal sənayesi
# və mədənçıxarma namizədləri, κ seçimi ilə faktiki istifadə olunan regional sistem), əlaqəli sektorlar üzrə
# birləşdirilmiş model, neftlə bağlı blok, mədənçıxarma qaydaları, amillər paneli (iki yönlü sabit effektlər, DK, vəhşi
# (wild) butstrap, bölmə meyli variantları, between və birgə hərəkət reqressiyaları) və — **B qatı** — hər müəssisə
# səviyyəli model (panel SİNTETİK olduğu müddətdə `synthetic: true` ilə işarələnir). Reyestr hər OLS / DOLS / panel
# tənliyini statsmodels ilə müstəqil şəkildə yenidən qiymətləndirir və əmsalların notebook-dakılara bərabər olduğunu
# (nisbi 1e-6) yoxlama ifadəsi ilə təsdiqləyir; proqnozda çevrilmiş dəyər (κ ilə büzülmüş meyllər, qoyulmuş qayda)
# istifadə olunduqda sətrin `used_value` sahəsi onu daşıyır və qeyddə bu göstərilir. Nümunədən kənar yoxlama üzrə yenidən
# qiymətləndirmələr müvafiq tənliyin `holdout` blokudur.

# %%
if str(BASE) not in sys.path: sys.path.insert(0, str(BASE))
from microlib.registry import EquationRegistry
from microlib.summary import build_summary
from microlib import robustness as MR
REGX = EquationRegistry('FR10', data_mode='OBSERVED')
slug = lambda s: re.sub(r'[^A-Za-z0-9]+', '_', str(s)).strip('_')
CID = lambda kind, code: f'fr10:{kind}:{code}'
SUB = {'C': 'A1. Bazar payları: emal sənayesi sahələri', 'B': 'A2. Bazar payları: mədənçıxarma sahələri',
       'R': 'A3. Regional bölgü: iqtisadi rayonların sənaye payları', 'O': 'A4. Neftlə bağlı sahələr (neft emalı, kimya)',
       'D': 'A5. İnkişaf və tənəzzülün amilləri (determinantlar paneli)'}
SPEC_AZ = {'scale': 'miqyas (FR1 real əlavə dəyəri)', 'oil': 'neft qiyməti', 'scale+oil': 'miqyas + neft qiyməti',
           'combo': 'kombinasiya'}
def hold_block(r):
    return None if r is None else dict(cut=int(CUT), years=list(HY), rmse=float(r['RMSE']), theil_u_rw=float(r['U_vs_random_walk']),
                                       theil_u_const=float(r['U_vs_constant_growth']), dm_p_rw=float(r['DM_p_vs_rw']),
                                       dm_p_const=float(r['DM_p_vs_cg']), measure=r['measure'], weighting=r['weighting'], model=r['model'])

def reg_lr(eid, f, yl, Xl, used, comps, subtask, title_az, title_en, dep_az, notes='', extra=None, holdout=None):
    '''Register an lr_fit (DOLS rule) result with its exact design matrix and static levels sample.'''
    y = pd.Series(f.y, index=f.index, name='log_odds'); X = pd.DataFrame(f.X[:, 1:], index=f.index, columns=f.names[1:])
    est = f.estimator if f.estimator.startswith('DOLS') else 'OLS'
    eq = REGX.add(eid, y, X, estimator=est, cov='hac', fit_coef=f.lr, fit_se=f.lr_se, components=comps, subtask=subtask,
                  title_az=title_az, title_en=title_en, dependent_label_az=dep_az, used_in_forecast=used,
                  levels=(yl, Xl) if est.startswith('DOLS') else None, det=list(f.dcols), n_i1=len(f.icols),
                  lr_names=list(f.icols) + list(f.dcols), editable=[], notes_az=notes, extra=extra, holdout=holdout)
    eq['diagnostics']['eg_coint_p_notebook'] = None if not np.isfinite(f.eg_p) else float(f.eg_p)
    eq['diagnostics']['eg_note'] = 'eg_coint_p_notebook: ADF on the static OLS residual (Part 3 eg_coint_p); eg_coint_p: on the DOLS long-run residual'
    return eq

def reg_ols(eid, f, used, comps, subtask, title_az, title_en, dep_az, ycode, coint=False, notes='', extra=None, holdout=None,
            editable=None, restrictions=None, cov='hac', index=None):
    ix = f.index if index is None else index
    y = pd.Series(f.y, index=ix, name=ycode); X = pd.DataFrame(f.X[:, 1:], index=ix, columns=f.names[1:])
    return REGX.add(eid, y, X, estimator='OLS', cov=cov, fit_coef=dict(zip(f.names, f.beta)), fit_se=dict(zip(f.names, f.se)),
                    components=comps, subtask=subtask, title_az=title_az, title_en=title_en, dependent_label_az=dep_az,
                    used_in_forecast=used, coint=coint, notes_az=notes, extra=extra, holdout=holdout,
                    editable=editable if editable is not None else [], restrictions=restrictions)

def set_used(eq, name, value, **kw):
    for r in eq['coefficients']:
        if r['name'] == name:
            r['used_value'] = None if value is None else float(value); r.update(kw)
    eq['summary_text'] = build_summary(eq)

# --- A3: the regional share system actually used (spec, kappa chosen pre-cut), estimated 2005-2025
_sR = SELECT['R']; _xsR = SPEC_X.get(_sR['chosen'], [])
_yrsR = [y for y in SYS_R.W.index if SYS_R.est0 <= y <= LAST_ACT and SYS_R.W.loc[y].notna().all() and SYS_R.X.loc[y].notna().all()]
RAW_R = SYS_R.fit(_sR['chosen'], LAST_ACT, kappa=0.0) if _xsR else None        # coherence applied, no shrinkage
def eb_detail(x):
    '''v2.1: the empirical-Bayes step of ShareSystem._shrink recomputed from the unshrunk slopes, for the registry record.'''
    U, ref, kap = SYS_R.units, SYS_R.ref, float(_sR['kappa'])
    w = SYS_R.W.loc[LAST_ACT, U].astype(float)
    b_ = pd.Series({k: float(RAW_R[k]['b'][x]) if k != ref else 0.0 for k in U})
    se_ = pd.Series({k: float(RAW_R[k]['se'][x]) if k != ref else np.nan for k in U})
    se_[ref] = float((se_.drop(ref) * w.drop(ref)).sum() / w.drop(ref).sum())
    m = float((w * b_).sum()); d = b_ - m
    tau2 = max(float(d.var(ddof=1) - (se_ ** 2).mean()), 1e-4)
    Bk = (kap * se_ ** 2 / (kap * se_ ** 2 + tau2)) if np.isfinite(kap) else pd.Series(1.0, index=U)
    ds = (1 - Bk) * d
    return dict(prior_mean=m, tau2=tau2, B=Bk, se=se_, b=b_, used=ds - ds[ref], ref_offset=float(-ds[ref]), kappa=kap)
EB_R = {x: eb_detail(x) for x in _xsR}
REG_SLOPES = {}
for k in [u for u in SYS_R.units if u != SYS_R.ref] if _xsR else []:
    p = PAR['R'][k]; f = p['fit']; s_ = slug(k)
    yl = SYS_R.LO[k].loc[_yrsR]; Xl = pd.concat([SYS_R.X.loc[_yrsR, _xsR], SYS_R.dum.loc[_yrsR, list(f.dcols)]], axis=1)
    fd = diff_fit(SYS_R.LO[k], SYS_R.X[_xsR], SYS_R.dum, sample=_yrsR)
    fd_used = 'difference form' in p.get('rule', '')
    comps = [CID('reg_share', s_), CID('reg_output', s_)]
    ex = dict(kappa=float(_sR['kappa']), shrink_B={x: p.get('B', {}).get(x) for x in _xsR}, slope_used={x: float(p['b'][x]) for x in _xsR},
              se_posterior={x: float(p['se'][x]) for x in _xsR}, slope_unshrunk={x: float(RAW_R[k]['b'][x]) for x in _xsR}, coherence=p.get('rule', ''))
    note = (f"Səviyyə (DOLS) və fərq formaları; uyğunluq qaydası: {'fərq forması istifadə olunur' if fd_used else 'səviyyə əmsalı istifadə olunur'}; "
            f"proqnozda empirik Bayes ilə büzülmüş dəyər (κ = {_sR['kappa']:g}) istifadə olunur — FR10.reg_system.")
    e1 = reg_lr(f'FR10.reg_{s_}_lvl', f, yl, Xl, not fd_used, comps, SUB['R'], f'{k}: sənaye payının log-nisbəti (səviyyə, DOLS)',
                f'{k}: log-odds of the industrial-output share vs Baku (levels, DOLS)', 'ln(pay / Bakı payı)', notes=note, extra=ex)
    e2 = reg_ols(f'FR10.reg_{s_}_fd', fd, fd_used, comps, SUB['R'], f'{k}: log-nisbət, fərq forması', f'{k}: log-odds, first differences',
                 'Δ ln(pay / Bakı payı)', 'd_log_odds', notes=note, extra=ex)
    for e in (e1, e2):
        if e['used_in_forecast']:
            for x in _xsR:
                q = EB_R[x]
                assert abs(float(q['used'][k]) - float(p['b'][x])) <= 1e-9 * max(1.0, abs(float(p['b'][x]))), (k, x)
                e['restrictions'].append(dict(
                    text_az=(f"{x} əmsalı empirik Bayes üsulu ilə büzülüb: qiymətləndirmə {float(q['b'][k]):.4f} (s.x. {float(q['se'][k]):.4f}) "
                             f"apriori orta {q['prior_mean']:.4f} (2025 payları ilə çəkilmiş bütün rayonların orta əmsalı, Bakı = 0) istiqamətində "
                             f"büzülür; büzülmə çəkisi B = κ·s.x.² / (κ·s.x.² + τ²) = {float(q['B'][k]):.3f} (κ = {q['kappa']:g}, τ² = {q['tau2']:.4f}), "
                             f"öz qiymətləndirmənin çəkisi 1 − B = {1 - float(q['B'][k]):.3f}; sonra bütün əmsallar Bakıya nisbətən ifadə olunur "
                             f"(sürüşmə {q['ref_offset']:+.4f}). Proqnozda istifadə olunan dəyər: {float(p['b'][x]):.4f}. κ 2019-a qədərki pəncərələrdə seçilib."),
                    test='empirical Bayes (precision-weighted) shrinkage, kappa chosen pre-cut', stat=None, p=None, imposed=True,
                    kind='eb_shrinkage', coefficient=x, estimate=float(q['b'][k]), estimate_se=float(q['se'][k]), prior_mean=float(q['prior_mean']),
                    shrink_B=float(q['B'][k]), weight_own=float(1 - q['B'][k]), kappa=float(q['kappa']), tau2=float(q['tau2']),
                    reference_offset=float(q['ref_offset']), used_value=float(p['b'][x]), source_equation='FR10.reg_system'))
                set_used(e, x, p['b'][x], fixed=True, used_value_basis='empirical_bayes_shrinkage')
        else:
            for r in e['coefficients']: r['used_value'] = None
    REG_SLOPES[k] = dict(slope=float(p['b'][_xsR[0]]), se=float(p['se'][_xsR[0]]), raw=float(RAW_R[k]['b'][_xsR[0]]),
                         raw_se=float(RAW_R[k]['se'][_xsR[0]]), eq_used=(e2 if fd_used else e1)['id'])
_hR = HOLD[HOLD.system.str.contains('regions') & HOLD.selected]
if REG_SLOPES:
    _hb = hold_block(_hR.iloc[0]) if len(_hR) else None
    eqS = REGX.add('FR10.reg_system', None, None, estimator=f'MNL log-odds share system, empirical-Bayes shrinkage (kappa={_sR["kappa"]:g})',
                   cov='posterior s.e. after shrinkage', fit_coef={slug(k): v['slope'] for k, v in REG_SLOPES.items()},
                   fit_se={slug(k): v['se'] for k, v in REG_SLOPES.items()}, p_dist='normal',
                   components=[CID('reg_share', slug(k)) for k in REG_NAMES] + [CID('reg_output', slug(k)) for k in REG_NAMES],
                   subtask=SUB['R'], title_az='14 iqtisadi rayonun sənaye payları sistemi (softmax, büzülmüş əmsallar)',
                   title_en='Regional share system (softmax, EB-shrunk slopes on the FR1 oil-sector mix)',
                   dependent_label_az='ln(rayon payı / Bakı payı)', dependent_code='log_odds', coef_labels_az={slug(k): f'{k}: neft-sektor qarışığına elastiklik' for k in REG_SLOPES},
                   used_in_forecast=True, holdout=_hb, notes_az='Bakı referensdir (əmsal 0). Spesifikasiya və κ 2019-a qədərki pəncərələrdə seçilib.',
                   extra=dict(selection=SELECT['R']['table'].reset_index().to_dict('records'),
                              kappa_selection=(SELECT['R']['ktable'].reset_index().to_dict('records') if SELECT['R']['ktable'] is not None else None),
                              chosen=_sR['chosen'], kappa=float(_sR['kappa'])))
    eqS['sample'].update(start=int(min(_yrsR)), end=int(max(_yrsR)), n=int(len(_yrsR)))
    eqS['summary_text'] = build_summary(eqS)
print(f'registry: regional share system registered ({len(REG_SLOPES)} region equations x level/difference form + the system); {len(REGX)} equations so far')
