# %%
for g in GRP: AZ[f'{g} ({GROUPS[g][0]})'] = f'{g} ({GROUP_AZ[g]})'
AZ.update({'Mobile telecommunications (3 operators)': 'Mobil rabitə (3 operator)', 'Banking (assets)': 'Bank sektoru (aktivlər)', 'Cement (domestic producers)': 'Sement (yerli istehsalçılar)',
           'log-linear interpolation': 'log-xətti interpolyasiya', 'linear interpolation': 'xətti interpolyasiya', 'sum of filled components': 'doldurulmuş komponentlərin cəmi',
           'linear interpolation (non-positive neighbour)': 'xətti interpolyasiya (müsbət olmayan qonşu)',
           'not filled: leading gap (before the first observed year; no extrapolation)': 'doldurulmayıb: ilkin boşluq (ilk müşahidədən əvvəl; ekstrapolyasiya yoxdur)'})
AZ.update({'%; units': '%; vahid', 'pp': 'faiz bəndi', 'ratio': 'nisbət', 'units': 'vahid', 'index 0-10000; %': 'indeks 0–10 000; %', '%; index': '%; indeks', 'ratio; index': 'nisbət; indeks',
           'number': 'say', 'thsd AZN / dates': 'min AZN / tarixlər',
           'potentially raises significant concerns / unlikely to have adverse effects': 'potensial olaraq ciddi narahatlıq yaradır / mənfi təsir ehtimalı azdır'})
for _k, _ka in [('section', 'bölmələr'), ('region', 'regionlar')]:
    for _y in range(2019, 2027):
        AZ[f'new / liquidated units by {_k}, full year {_y}'] = f'{_ka} üzrə yaradılan / ləğv edilən vahidlər, {_y} tam il'
        AZ[f'new / liquidated units by {_k}, Jan-Jun {_y}'] = f'{_ka} üzrə yaradılan / ləğv edilən vahidlər, {_y} yanvar–iyun'
_P = 'FR12_SYNTHETIC_' if DATA_MODE == 'SYNTHETIC' else 'FR12_FIRM_'
SCAN = {'FR12_data_gaps_and_alternatives.csv': None, 'FR12_noar_constructs.csv': None, 'FR12_presentation_spec.csv': ['name', 'content', 'refresh'],
        'FR12_data_source_matrix.csv': ['pillar', 'indicator_en', 'formula', 'unit', 'source_institution', 'dataset_table_row', 'granularity', 'frequency', 'status', 'integration_into_MIIS',
                                        'analytical_use', 'presentation_form', 'update_frequency', 'alternative_if_unavailable', 'status_group'],
        'FR12_scenario_assumptions.csv': ['market', 'change', 'assumption', 'structure_source', 'elasticity_range', 'conduct', 'demand', 'status'], 'FR12_scenario_summary.csv': ['change', 'assumption'],
        'FR12_scenario_results.csv': ['change', 'assumption', 'us_2010_screen', 'eu_screen'], 'FR12_merger_screen.csv': ['us', 'eu'], 'FR12_identity_checks.csv': ['check'],
        'FR12_business_register_swap_tests.csv': ['test', 'detail'], f'{_P}pipeline_tests.csv': ['test'], f"{_P}{'calibration_errors' if DATA_MODE == 'SYNTHETIC' else 'coverage_vs_dsk'}_summary.csv": ['target', 'dimension', 'status'],
        'FR12_business_register_schema.csv': ['type', 'constraint', 'source'], 'FR12_coherence.csv': ['status'], 'FR12_selection_summary.csv': ['rule', 'best_candidate'], 'FR12_selection_scores.csv': ['candidate'],
        'FR12_fe_estimates.csv': ['spec'], 'FR12_holdout_validation.csv': ['metric', 'rule'], 'FR12_holdout_detail.csv': ['metric'], 'FR12_plausibility.csv': ['variable', 'flag'],
        'FR12_last_actual_vs_2026_band.csv': ['explanation'], 'FR12_early_warning.csv': ['name', 'flags', 'F_conc', 'F_entry', 'F_exit', 'F_mob', 'F_margin_entry'], 'FR12_early_warning_false_listing.csv': ['null'],
        'FR12_dsk_manifest.csv': ['origin', 'content', 'status'], 'FR12_series_filled.csv': ['method'], f'{_P}econ_coefficients.csv': ['ratio_type'], 'FR12_gapfill_sensitivity.csv': ['kind']}
SCAN.update({'FR12_sme_employment_model.csv': ['table', 'metric', 'candidate', 'rule', 'best_candidate', 'applied_at_last_origin', 'coherence_last_origin'],
             'FR12_section_allocation_holdout.csv': ['variable', 'variant', 'driver_rule'], 'FR12_section_nowcast_2026.csv': ['variable']})
AZ.update({'anchored: last observed year (2024 at the origin; 2025 in the forecast)': 'ankerlənmiş: son müşahidə ili (mənbədə 2024; proqnozda 2025)',
           'average of observed years (2021, 2024 at the origin)': 'müşahidə illərinin ortası (mənbədə 2021, 2024)'})
AZ.update({'selection (<= 2022 -> 2023)': 'seçim (≤ 2022 → 2023)', 'hold-out': 'nümunədən kənar yoxlama', 'rule': 'qayda', 'log-odds SME employment share': 'KOS-un işçi sayında payının log-odds-u',
           'not identified pre-cut: one observed full year (2021) at or before 2022': 'seçimdən əvvəl identifikasiya olunmur: 2022-yə qədər yalnız bir müşahidə edilmiş tam il (2021)',
           'constant shares (observed average)': 'sabit paylar (müşahidə edilmiş orta)', 'new': 'yeni', 'liq': 'ləğv edilən', 'stock': 'ehtiyat'})
for _d in ['dem', 'size', 'lend', 'cred', 'pcm', 'reg', 'non']:
    for _st_en, _st_az in [('coherent', 'uyğundur'), ('dropped (incoherent)', 'çıxarılıb (uyğunsuz)')]: AZ[f'{_d}: {_st_en}'] = f'{_d}: {_st_az}'
if DATA_MODE == 'SYNTHETIC': SCAN[f'{_P}econ_recovery.csv'] = ['block']
SROWS, MISS = [], []
for f, cols in SCAN.items():
    d = pd.read_csv(OUT / f)
    for c in (cols or [c for c in d.columns if d[c].dtype == object]):
        for v in d[c].dropna().astype(str).unique():
            if v in ('True', 'False') or not re.search(r'[A-Za-z]', v): continue
            if all(t.strip() in ('dem', 'size', 'lend', 'cred', 'pcm', 'reg', 'non') for t in v.split(',')): continue      # driver codes, not text
            az, how = to_az(v, c)
            if az is None: MISS.append((f, c, v))
            else: SROWS.append(dict(source_csv=f, column=c, en=v, az=az, method=how))
for r in FINDINGS.itertuples():
    for c, k in [('finding', 0), ('evidence', 1), ('consequence', 2)]:
        SROWS.append(dict(source_csv='FR12_data_integrity_findings.csv', column=c, en=getattr(r, c), az=FIND_AZ[r.id][k], method=f'tapıntı {r.id}'))
STRINGS_AZ = pd.DataFrame(SROWS).drop_duplicates(subset=['source_csv', 'column', 'en'])
STRINGS_AZ.to_csv(OUT / 'FR12_strings_az.csv', index=False)
print(f'FR12_strings_az.csv: {len(STRINGS_AZ)} English strings with Azerbaijani text ({STRINGS_AZ.method.value_counts().to_dict()}); untranslated: {len(MISS)}')
assert not MISS, f'untranslated strings: {MISS[:8]}'
