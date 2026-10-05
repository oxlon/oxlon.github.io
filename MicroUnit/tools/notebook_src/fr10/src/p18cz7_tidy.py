# %%
from microlib.catalog import write_catalog, check_catalog
_fanY = lambda key: (lambda f: f.loc[[i for i in f.index if isinstance(i, (int, np.integer))]].astype(float))(FAN.loc[key]) if key in FAN.index.droplevel(2) else None
# v2.1: every replaced volume index (finding F15) and the implied-deflator check of every branch
_TEST = {'T1': ('one-year implied deflator change outside x1/3-x3', 'deflyatorun bir illik dəyişməsi x1/3-x3 intervalından kənar'),
         'T2': ('deflator relative to manufacturing (2015 = 1) outside 1/6-6', 'emal sənayesi deflyatoruna nisbətən deflyator (2015 = 1) 1/6-6 intervalından kənar')}
VI_VAL = VI_FIX.assign(branch=VI_FIX.nace2.map(BNAME), branch_az=VI_FIX.nace2.map(BNAME_AZ),
                       test_en=VI_FIX.test.map(lambda t: _TEST[t][0]), test_az=VI_FIX.test.map(lambda t: _TEST[t][1]),
                       replacement_en='nominal growth deflated by the manufacturing deflator change of the same year',
                       replacement_az='nominal artım həmin ilin emal sənayesi deflyatoru dəyişməsinə bölünür',
                       imputed_level_year=[int(y) if y > BASE_YR else int(y) - 1 for y in VI_FIX.year])
VI_VAL = VI_VAL[['nace2', 'branch', 'branch_az', 'year', 'test', 'test_en', 'test_az', 'index_published', 'nominal_growth_pct', 'implied_deflator_change',
                 'mfg_deflator_change', 'rel_deflator_if_published', 'index_used', 'replacement_en', 'replacement_az', 'imputed_level_year']]
VI_VAL.to_csv(OUT / 'FR10_volume_index_validation.csv', index=False)
DEFL_CHECK.to_csv(OUT / 'FR10_branch_deflator_check.csv')
# v2.1: history years whose real level was derived through a replaced volume index (Part 5.1): the replaced year itself
# after the 2015 base, the year before it up to the base (backward chaining); later / earlier years inherit the level shift
IMP_YEARS = {}
for r in VI_FIX.itertuples():
    for code in ('output_real_mn_AZN_2015', 'lp_thsd_AZN_2015'):
        IMP_YEARS.setdefault(CID(code, r.nace2), set()).add(int(r.year) if r.year > BASE_YR else int(r.year) - 1)
TIDY, CAT = [], []
for c in COMP:
    h = pd.Series(c['hist'], dtype=float).dropna(); h = h[h.index <= LAST_ACT]; h.index = h.index.astype(int)
    band = _fanY(c['fan']) if c['fan'] else None
    for s_ in SCEN:
        fc = c['get'](SOL[s_]).loc[FC_YEARS].astype(float)
        if s_ == 'Baseline' and band is not None:
            assert np.allclose(band.baseline.loc[FC_YEARS].values, fc.values, rtol=1e-9, atol=1e-9), c['id']
        TIDY.append(pd.DataFrame({'id': c['id'], 'scenario': s_, 'year': h.index, 'value': h.values, 'lower_5': np.nan, 'upper_95': np.nan,
                                  'is_forecast': False}))
        TIDY.append(pd.DataFrame({'id': c['id'], 'scenario': s_, 'year': FC_YEARS, 'value': fc.values,
                                  'lower_5': band.p5.loc[FC_YEARS].values if (band is not None and s_ == 'Baseline') else np.nan,
                                  'upper_95': band.p95.loc[FC_YEARS].values if (band is not None and s_ == 'Baseline') else np.nan, 'is_forecast': True}))
    CAT.append(dict(id=c['id'], group_az=c['group_az'], label_az=c['label_az'], label_en=c['label_en'], unit_az=c['unit_az'], kind=c['kind'],
                    has_forecast=True, scenarios=SCEN, has_band=band is not None, source_csv=c['source_csv'], source_column=c['source_column'],
                    equation_ids=c['equation_ids'], imputed_years=sorted(y for y in IMP_YEARS.get(c['id'], ()) if y in set(h.index))))
TIDY = pd.concat(TIDY, ignore_index=True)
_meta = pd.DataFrame(CAT).set_index('id')[['unit_az', 'kind']]
TIDY = TIDY.join(_meta, on='id')
TIDY['imputed'] = [(not f) and (int(y) in IMP_YEARS.get(i, ())) for i, y, f in zip(TIDY.id, TIDY.year, TIDY.is_forecast)]
TIDY = TIDY[['id', 'scenario', 'year', 'value', 'lower_5', 'upper_95', 'unit_az', 'kind', 'is_forecast', 'imputed']]
TIDY.to_csv(OUT / 'FR10_forecast_tidy.csv', index=False)
CATALOG = write_catalog(CAT, OUT / 'FR10_indicator_catalog.csv', 'FR10')
# completeness: every component has every year 2026-2030 in every scenario, finite
_fcT = TIDY[TIDY.is_forecast]
_cnt = _fcT.dropna(subset=['value']).groupby(['id', 'scenario']).year.nunique()
assert len(_cnt) == len(COMP) * len(SCEN) and (_cnt == len(FC_YEARS)).all(), 'forecast table incomplete'
assert np.isfinite(_fcT.value).all(), 'non-finite forecast values'
_fb = pd.read_csv(OUT / 'FR10_forecast_branches.csv', dtype={'nace2': str})
_fb = _fb[(_fb.indicator == 'output_nominal_mn_AZN') & _fb.year.isin(FC_YEARS)].assign(id=lambda d: 'fr10:output_nominal_mn_AZN:' + d.nace2.str.zfill(2))
_jj = _fb.merge(_fcT, on=['id', 'scenario', 'year'])
assert len(_jj) == len(_fb) and np.allclose(_jj.value_x, _jj.value_y, rtol=1e-12), 'tidy table differs from FR10_forecast_branches.csv'
NOT_FC = pd.DataFrame([
    ('fr10:tfp:<branch|section>', 'Ümumi amil məhsuldarlığı (TFP), sahə və bölmə', 'TFP by branch and section',
     'TFP artım uçotu ilə ölçülür; proqnozu sahə üzrə kapital ehtiyatı və aralıq istehlak proqnozu tələb edir, FR1-də bunlar sahə üzrə yoxdur', 'FR10_tfp_branches.csv'),
    ('fr10:early_warning:<branch>', 'Erkən xəbərdarlıq bayraqları', 'early-warning flags',
     'Bayraqlar son illərin müşahidə olunan dəyişmələri üzrə qərar qaydalarıdır (2023–25 vs 2020–22); proqnoz obyekti deyil', 'FR10_early_warning.csv'),
    ('fr10:investment_rate:<branch>', 'İnvestisiya norması, ehtiyatlar/buraxılış, innovasiya intensivliyi, kapital məhsuldarlığı', 'investment rate, stocks, innovation, capital productivity',
     'Bu səmərəlilik göstəriciləri üçün FR1-də ekzogen sürücü yoxdur; öz tarixindən proqnoz qadağandır (avtoreqressiya yoxdur)', 'FR10_efficiency_branches.csv'),
    ('fr10:sme_share:<activity>', 'KOS-un buraxılış, məşğulluq, aktivlərdə payı', 'SME shares', 'Yalnız 2023–2024 (iki il) mövcuddur; 2024 səviyyəsində saxlanılır, model yoxdur',
     'FR10_data_source_matrix.csv'),
    ('fr10:enterprises:<branch|region>', 'Müəssisələrin sayı, yaradılan və ləğv edilən müəssisələr', 'enterprise counts, entry and exit',
     'Giriş/çıxış üçün struktur sürücülü model qurulmayıb; öz tarixindən proqnoz qadağandır', 'FR10_regional_entry_exit.csv'),
    ('fr10:dvx:<indicator>', 'DVX bəyannamə göstəriciləri (mənfəət vergisi ödəyiciləri, zərər, borclar)', 'DVX declaration aggregates',
     'Yalnız 2021–2025 (5 il) və iqtisadiyyat üzrə; sahə üzrə deyil — proqnoz üçün kifayət deyil', 'FR10_dvx_declarations.csv'),
    ('fr10:product_location_share:<product>', 'Məhsulların istehsal yerləri üzrə payları (018_1)', 'product shares by place of production',
     'Yer üzrə paylar üçün sürücü yoxdur; təsviri göstərici', 'FR10_product_location_shares.csv'),
    ('fr10:firm:<firm_id>', 'Müəssisə səviyyəsində proqnozlar (B qatı)', 'firm-level forecasts (Layer B)',
     f'B qatı {DATA_MODE} panel üzrə işləyir; sintetik rejimdə yalnız texniki nümayişdir (FR10_SYNTHETIC_firm_forecast.csv), A qatının komponenti deyil', 'FR10_SYNTHETIC_firm_forecast.csv'),
    ('fr10:regional_nonstate_share:<region>', 'Regionlarda qeyri-dövlət sektorunun payı', 'regional non-state share',
     'Regional mülkiyyət strukturu üçün model yoxdur; tarixi göstərici', 'FR10_regional_history.csv')],
    columns=['id_pattern', 'label_az', 'label_en', 'reason_az', 'source_csv'])
NOT_FC.to_csv(OUT / 'FR10_not_forecast.csv', index=False)
print(f"imputed history points (volume-index replacements): {int(TIDY.imputed.sum())} rows, {sum(1 for c in CAT if c['imputed_years'])} components")
print(f'catalogue: {len(CATALOG)} components; forecast table: {len(TIDY):,} rows, {len(COMP)} components x {len(SCEN)} scenarios x '
      f'{len(FC_YEARS)} years complete; bands for {int(CATALOG.has_band.eq("true").sum())} components (Baseline); {len(NOT_FC)} groups not forecast (reasons listed)')
