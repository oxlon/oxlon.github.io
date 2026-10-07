# %%
from microlib.catalog import write_catalog, check_catalog
NF = []
def nf(sid, az, en, scope='forecast'):    # scope: 'forecast' = not forecast; 'history' = forecast given, observed-year values missing (explained)
    NF.append(dict(id=sid, label_az=_cat.loc[sid, 'label_az'] if sid in _cat.index else sid, reason_az=az, reason_en=en, scope=scope))
for g in GRP:
    fx = TIDY[(TIDY.id == f'fr12:conc:hhi_upper_floor30:{g}') & TIDY.is_forecast]
    if fx.value.isna().any():
        yy = sorted(set(fx[fx.value.isna()].year)); ry = CONCP[(CONCP.group == g) & CONCP.year.isin(yy) & (CONCP.scenario == 'Baseline')]
        nf(f'fr12:conc:hhi_upper_floor30:{g}', f"Fərziyyə mümkün deyil ({', '.join(map(str, yy))}): {int(SIZE_G.loc[g, 'large'])} iri vahidin hər birinin gəliri ≥ 30 mln AZN olsaydı, iri sinfin "
           f"buraxılışını aşardı (iri pay {ry.large_share.min():.1f}–{ry.large_share.max():.1f}%). Əsas yuxarı hədd (hhi_upper) və 15 mln AZN variantı verilir.",
           f"infeasible assumption in {yy}: {int(SIZE_G.loc[g, 'large'])} large units with revenue >= 30 mn AZN each would exceed the large class's output; headline upper bound and the 15 mn variant are given")
# the 30 mn floor can also be infeasible in an OBSERVED year (2023-24) while the forecast years are feasible: the value is missing
# there, the forecast is given; the row explains the gap (scope 'history': the id keeps its forecast in the catalogue)
for g in GRP:
    sid = f'fr12:conc:hhi_upper_floor30:{g}'
    if sid in {r['id'] for r in NF}: continue
    hx = TIDY[(TIDY.id == sid) & ~TIDY.is_forecast]
    if hx.value.isna().any():
        yy = sorted(set(hx[hx.value.isna()].year)); rb = BND[(BND.group == g) & BND.year.isin(yy)]; nL = int(SIZE_G.loc[g, 'large'])
        lo_, hi_ = (rb.large_share / 100 * rb.market_output_mn).min(), (rb.large_share / 100 * rb.market_output_mn).max()
        _sp = lambda x: f'{x:,.0f}'.replace(',', ' ')
        nf(sid, f"Müşahidə illərində ({', '.join(map(str, yy))}) fərziyyə mümkün deyil: {nL} iri vahidin hər birinin gəliri ≥ 30 mln AZN olsaydı "
                f"(cəmi ≥ {_sp(nL * 30)} mln AZN), iri sinfin buraxılışını ({_sp(lo_)}–{_sp(hi_)} mln AZN; iri pay {rb.large_share.min():.1f}–{rb.large_share.max():.1f}%) "
                f"aşardı — həmin illərdə dəyər yoxdur. Proqnoz illərində fərziyyə mümkündür və dəyər verilir; əsas yuxarı hədd (hhi_upper) və 15 mln AZN variantı "
                f"bütün illər üçün verilir.",
           f"infeasible assumption in the observed years {yy}: {nL} large units with revenue >= 30 mn AZN each ({nL * 30:,.0f} mn AZN in total) would exceed the "
           f"large class's output ({lo_:,.0f}–{hi_:,.0f} mn AZN; large share {rb.large_share.min():.1f}–{rb.large_share.max():.1f}%), so those years have no value; "
           f"the forecast years are feasible and given; the headline upper bound and the 15 mn variant are given for every year", scope='history')
NOTFC = pd.DataFrame(NF); NOTFC.to_csv(OUT / 'FR12_not_forecast.csv', index=False)
_nf = set(NOTFC[NOTFC.scope == 'forecast'].id)
for r in CAT:
    if r['id'] in _nf: r['has_forecast'] = False; r['scenarios'] = []
CATDF = write_catalog(CAT, OUT / 'FR12_indicator_catalog.csv', 'FR12')
TIDY.to_csv(OUT / 'FR12_forecast_tidy.csv', index=False)
# completeness: every forecast component has every year 2026-2030 in every scenario, with a finite value
_need = [c['id'] for c in CAT if c['has_forecast']]
_f = TIDY[TIDY.year.isin(FC_YEARS) & TIDY.value.notna()].groupby('id').apply(lambda d: {(s, y) for s, y in zip(d.scenario, d.year)})   # forecast rows, or observed (H1 2026)
_miss = [i for i in _need if i not in _f.index or len(_f[i] & {(s, y) for s in SCEN for y in FC_YEARS}) != len(SCEN) * len(FC_YEARS)]
assert not _miss, f'forecast table incomplete for {len(_miss)} components, e.g. {_miss[:5]}'
assert set(TIDY.id) == set(CATDF.id), 'catalogue and forecast table ids differ'
_cc = check_catalog(OUT / 'FR12_indicator_catalog.csv', OUT / 'FR12_equations.json')
assert not _cc, _cc[:5]
_ti = TIDY[TIDY.imputed]
assert set(zip(_ti.id, _ti.year)) <= set(zip(SERIES_FILLED[SERIES_FILLED.imputed].id, SERIES_FILLED[SERIES_FILLED.imputed].year)), 'imputed flags differ from FR12_series_filled.csv'
_dup = TIDY.duplicated(['id', 'scenario', 'year']).sum(); assert _dup == 0, f'{_dup} duplicate id-scenario-year rows'
print(f"catalogue: {len(CATDF)} indicator ids ({int(CATDF.has_forecast.eq('true').sum())} forecast in {len(SCEN)} scenarios x {len(FC_YEARS)} years — complete); "
      f"forecast table {len(TIDY):,} rows, {int(TIDY.imputed.sum())} imputed history rows; not forecast: {len(NOTFC)} ids (FR12_not_forecast.csv)")
display(NOTFC.assign(block=NOTFC.id.str.split(':').str[1]).groupby('block').size().rename('ids not forecast'))
