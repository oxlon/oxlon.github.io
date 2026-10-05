# %%
# A5: the IO scenario toolkit and the bound mapping are CALIBRATED (no estimation): parameters fixed, assumptions stated
IO_AZ = {'S1': ('Kurno: giriş maneələrinin azaldılması (ΔN)', 'simmetrik-ekvivalent rəqib sayı N = θ/(Lε) bir vahid artır; xətti tələb P = a − bQ, b = 1/ε; marjinal xərc c = 1 − L'),
         'S2': ('Kurno: birləşmə (ΔHHI = 2 s₁ s₂)', 'birləşmədən sonra HHI + 2 s₁ s₂; ABŞ 2010 və AB HHI hədləri; Farrell–Şapiro: qiymət yalnız birləşmiş müəssisənin xərci marjadan çox azalarsa düşür'),
         'S3': ('Kurno: xərc şoku / vergi', 'bütün müəssisələrin vahid xərci ilkin qiymətin 5%-i qədər artır; ötürülmə N/(N+θ) (xətti), Nε/(Nε−θ) (sabit elastiklik)'),
         'S4': ('Kurno: idxal rəqabəti (rəqabətli idxal kənarı)', 'L = θ HHI_d (1 − m)/(ε + η m); idxal payı m artır, idxal təklifinin elastikliyi η = 2'),
         'S5': ('Qarışıq oliqopoliya: dövlət müəssisəsinin özəlləşdirilməsi', 'dövlət müəssisəsi λπ + (1−λ)W maksimallaşdırır; σ = sənayedə dövlət payı; λ 0-dan 0.5/1-ə; artan marjinal xərc c + k q₀; ədədi tarazlıq')}
IO_PAR = {'S1': dict(delta_N=1.0), 'S2': dict(s1=0.10, s2=0.05, s1_bank=0.08, s2_bank=0.06), 'S3': dict(cost_shock=0.05),
          'S4': dict(m0=0.30, m1=0.40, m0_cement=0.20, m1_cement=0.30, eta=2.0), 'S5': dict(sigma_industry=SIG['industry'], sigma_manufacturing=SIG['manufacturing'], lambda_partial=0.5, lambda_full=1.0)}
for sid, (taz, aaz) in IO_AZ.items():
    a = SC_ASSUME[SC_ASSUME.scenario == sid]; s_ = SC_SUM[SC_SUM.scenario == sid]
    REGX.add(f'FR12.IO_{sid}', None, None, estimator='calibrated (Cournot, linear demand)', cov='—', fit_coef={}, fit_se={},
             fixed=IO_PAR[sid] | dict(elasticity_eps_central=1.0, elasticity_min=min(EPS_GRID), elasticity_max=max(EPS_GRID), conduct_theta_cournot=1.0, conduct_theta_alt=0.5),
             components=[], subtask=SUBT['IO'], title_az=taz, title_en=f'IO toolkit {sid}: ' + '; '.join(sorted(set(a.change))), dependent_label_az='Δqiymət, Δmarja, Δburaxılış, Δistehlakçı və istehsalçı rifahı',
             dependent_code='d_price_pct', used_in_forecast=False,
             notes_az=(f'Kalibrlənmiş model (qiymətləndirilmir). Fərziyyələr: {aaz}. Bazarlar: ' + '; '.join(f'{r.market} — HHI {r.hhi_range} ({r.structure_source})' for r in a.itertuples())
                       + f'. ε ∈ {EPS_GRID}, θ ∈ {THETA_GRID}; nəticələr illüstrativdir (FR12_scenario_results.csv). Mühərrikdə rıçaqlarla dəyişdirilə bilər.'),
             extra=dict(markets=sorted(set(a.market)), d_price_range=[float(s_.d_price_min.min()), float(s_.d_price_max.max())], results_csv='FR12_scenario_results.csv'))
REGX.add('FR12.conc_bounds_map', None, None, estimator='calibrated identity (box-simplex vertices)', cov='—', fit_coef={}, fit_se={},
         fixed=dict(cap_micro_mn=CAP['micro'], cap_small_mn=CAP['small'], cap_medium_mn=CAP['medium'], floor_large_mn_headline_variant=30.0, floor_large_mn_sensitivity=15.0),
         components=[f'fr12:conc:{c}:{g}' for c in CONC_COLS[2:] for g in GRP], subtask=SUBT['sme'], title_az='HHI/CR4 hədləri: ölçü qrupları üzrə payların xəritələnməsi (eynilik)',
         title_en='Concentration bounds from size-class shares (identity)', dependent_label_az='HHI aşağı/yuxarı hədd, CR4 hədləri', dependent_code='hhi_bounds', used_in_forecast=True,
         notes_az=('Qiymətləndirilmir: aşağı hədd Σ S²/n (sinif daxilində bərabər paylar), yuxarı hədd qutu-simpleksin təpəsi (sinif tavanları: mikro 0.2, kiçik 3, orta 30 mln AZN); '
                   'tavanlar F15 olan qruplarda (AGR, EDU, HEA) atılır. 30/15 mln AZN gəlir döşəməsi fərziyyəsi yalnız mümkün olduqda hesablanır.'))
# A2: NACE-section flows by allocation of the region-panel total (calibrated: shares fixed at their observed average)
_ah = '; '.join(f"{r.variable}: RMSE ankerlənmiş {r.rmse:.1f}, Theil U ankerlənmiş / orta paylar {r.theil_vs_other_variant:.2f}" for r in ALLOC_HOLD[ALLOC_HOLD.used_in_baseline].itertuples())
REGX.add('FR12.alloc_sections', None, None, estimator='calibrated allocation (constant observed shares)', cov='—', fit_coef={}, fit_se={},
         fixed={f'share_{v}_{s}': float(ALLOC.loc[s, v]) for s in SECS for v in AVAR} | dict(nowcast_half_life_years=HALF_LIFE, nowcast_year=float(NOW_Y)), editable=[],
         components=[f'fr12:sec:{m}:{s}' for s in MKT for m in ['stock', 'new', 'liq', 'entry', 'exit']], subtask=SUBT['alloc'],
         title_az='NACE bölmələri: statistik vahidlərin doğulma, ölüm və ehtiyatının bölüşdürülməsi', title_en='Section register flows: allocation of the region-panel total',
         dependent_label_az='bölmənin yeni, ləğv edilən vahidləri və ehtiyatı', dependent_code='section_flows', used_in_forecast=True,
         notes_az=('Qiymətləndirilmir: regional panelin statistik vahid proqnozu (doğulma, ölüm, ehtiyat) əvvəlcə 11 fəaliyyət qrupuna, sonra qrup daxilində bölmələrə '
                   'son faktiki ilin (2025) paylarına ankerlənərək bölünür; 2026: yanvar–iyun 2026 faktı / bölmənin I yarım–il nisbəti (2024–2025 ortası) ilə cari qiymətləndirmə, '
                   'artım 2026-da tam, sonra bir illik yarımömürlə sönür (O, U istisna, F10); hər il bölmələr cəmə yenidən miqyaslanır — bölmələr qrupa, qruplar cəmə dəqiq bərabərdir. '
                   'Bölməyə xas sürücü qaydası seçimdən əvvəlki dizaynda yoxlana bilmir (≤ 2022 yalnız bir il). Nümunədən kənar (2024 → 2025): ' + _ah + '.'),
         extra=dict(holdout=ALLOC_HOLD.to_dict('records'), shares_csv='FR12_section_allocation.csv', nowcast_csv='FR12_section_nowcast_2026.csv', total='fr12:reg:*:ALL'))
REGX.add('FR12.alloc_sections_h1', None, None, estimator='calibrated allocation (observed half-year ratio)', cov='—', fit_coef={}, fit_se={},
         fixed={f'h1_ratio_{v}_{s}': float(H1RATIO.loc[s, v]) for s in SECS for v in AVAR}, editable=[],
         components=[f'fr12:sec_h1:{m}:{s}' for s in MKT for m in ['stock', 'new', 'liq']], subtask=SUBT['alloc'],
         title_az='NACE bölmələri: yanvar–iyun axınları = tam il proqnozu × müşahidə edilmiş I yarım / il nisbəti', title_en='Section half-year flows: full-year allocation x observed H1 ratio',
         dependent_label_az='bölmənin yanvar–iyun göstəriciləri', dependent_code='section_h1_flows', used_in_forecast=True,
         notes_az='Qiymətləndirilmir: nisbət 2024 və 2025-in orta I yarım / tam il nisbətidir; 2026-cı ilin I yarımı müşahidə edilib və 2026 tam il cari qiymətləndirməsinə daxil olunur (proqnoz 2027–2030).')
# B: Layer-B econometrics (synthetic: true in SYNTHETIC mode)
LBS = DATA_MODE == 'SYNTHETIC'; LBT = ECON_TAG[DATA_MODE]
def _mi(a, b): return pd.MultiIndex.from_arrays([np.asarray(a), np.asarray(b, int)], names=['unit', 'year'])
def lb_add(eid, title_az, title_en, dep_az, dep, y, X, est, cov, coef, se, notes, fit_df=None, fitted=None, res_ns=None, extra=None, summary=None, p_dist=None):
    Xn = X.drop(columns=[c for c in X.columns if c == 'const']) if X is not None else None
    eq = REGX.add(eid, y, Xn, estimator=est, cov=cov, fit_coef=coef, fit_se=se, fit_df=fit_df, p_dist=p_dist, results=res_ns, fitted=fitted, components=[], subtask=SUBT['LB'],
                  title_az=title_az, title_en=title_en, dependent_label_az=dep_az, dependent_code=dep, used_in_forecast=False, synthetic=LBS,
                  notes_az=(f'{LBT}. ' if LBS else '') + notes, extra=extra)
    if summary: eq['summary_text'] += '\n\n' + summary
    return eq
EM = ECON['models']
for k in ['entry_poisson', 'entry_poisson_secfe']:
    r = EM[k]['res']; dat = EM[k]['data']; ix = _mi(dat.nace2 + '|' + dat.region, dat.year)
    eq = REGX.add(f'FR12.LB_{k}', EM[k]['y'].set_axis(ix), EM[k]['X'].set_axis(ix), estimator='Poisson ML', cov='cluster', results=r, fit_coef=r.params, fit_se=r.bse,
                  cov_label='klaster (NACE bölməsi × region)', components=[], subtask=SUBT['LB'], title_az=MODEL_AZ[k], title_en=k.replace('_', ' '), dependent_label_az='girişlərin sayı (müəssisə)',
                  dependent_code='entrants', used_in_forecast=False, synthetic=LBS, notes_az=(f'{LBT}. ' if LBS else '') + ECON['tables']['summary'].set_index('model').interpretation_az.get(k, ''),
                  extra=dict(irr={c: float(np.exp(v)) for c, v in r.params.items() if not c.startswith(('yr_', 'reg_', 'sec_'))}))
    eq['summary_text'] += '\n\n' + r.summary().as_text()
_od = ECON['overdispersion']
for k, est in [('entry_nb2', 'NegBin-2 ML'), ('exit_logit', 'Binomial GLM, logistic link (frequency weights)'), ('exit_cloglog', 'Binomial GLM, complementary log-log link (frequency weights)')]:
    r = EM[k]['res']; dat = EM[k]['data']
    ix = _mi(dat.nace2 + '|' + dat.region, dat.year) if k.startswith('entry') else _mi(dat.firm_id, dat.year)
    llnull = getattr(r, 'llnull', np.nan)
    ex_ = dict(pseudo_r2_mcfadden=float(1 - r.llf / llnull) if llnull == llnull and llnull else None, ratio_type=EM[k]['kind'],
               ratios={c: float(np.exp(v)) for c, v in r.params.items() if not c.startswith(('yr_', 'reg_', 'sec_'))})
    if k == 'entry_nb2': ex_.update(alpha=_od['alpha'], lr_vs_poisson=_od['lr'], lr_p=_od['lr_p'])
    else: ex_.update(enterprise_years=float(dat.w.sum()), exits=float((dat.event * dat.w).sum()), frequency_weights=True)
    lb_add(f'FR12.LB_{k}', MODEL_AZ[k], k.replace('_', ' '), 'girişlərin sayı' if k.startswith('entry') else 'çıxış (0/1), müəssisə-il', 'entrants' if k.startswith('entry') else 'exit',
           EM[k]['y'].set_axis(ix), EM[k]['X'].set_axis(ix), est, 'cluster', r.params, r.bse, ECON['tables']['summary'].set_index('model').interpretation_az.get(k, ''),
           fitted=np.asarray(r.predict() if k.startswith('entry') else r.fittedvalues, float), res_ns=SimpleNamespace(aic=r.aic, llf=r.llf, bic=(r.bic_llf if hasattr(r, 'bic_llf') else r.bic)),
           extra=ex_, summary=r.summary().as_text())
