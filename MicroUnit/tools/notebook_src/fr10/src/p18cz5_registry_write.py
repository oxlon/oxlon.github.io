# %%
# registry coefficients equal the notebook's own estimates (forecast-relevant values and every Layer-B estimate)
_cv = lambda eid, name, key='coef': next(r[key] for r in REGX.get(eid)['coefficients'] if r['name'] == name)
REG_CHK = [('pooled beta', _cv('FR10.pooled', 'x'), BETA), ('pooled beta s.e.', _cv('FR10.pooled', 'x', 'se'), BETA_SE),
           ('refining oil-price elasticity', _cv('FR10.oil_19', 'dln_oil_azn'), EPS_OIL['19']),
           ('quarrying elasticity (estimate)', _cv('FR10.mining_08', 'x'), E08_EST),
           ('quarrying neutral level factor', _cv('FR10.mining_08_rule', 'level_factor_vs_2025'), MINING_RULES['q08_level_factor'])]
REG_CHK += [(f'regional slope {k}', _cv('FR10.reg_system', slug(k)), v['slope']) for k, v in REG_SLOPES.items()]
REG_CHK += [(f'determinants {r.spec[:1]} {r.regressor}', _cv(f'FR10.det_{r.spec[:1]}', r.regressor), r.coef) for r in DET.itertuples()]
REG_CHK += [(f'{m} {c}', _cv(f'FR10.{m}', c), float(f.b[c])) for m, f in EBF.items() for c in f.b.index]
REG_CHK = pd.DataFrame(REG_CHK, columns=['check', 'registry', 'notebook'])
REG_CHK['abs_diff'] = (REG_CHK.registry - REG_CHK.notebook).abs()
assert (REG_CHK.abs_diff <= 1e-9 * np.maximum(1, REG_CHK.notebook.abs())).all(), REG_CHK[REG_CHK.abs_diff > 1e-9]
# verdict basis (contract rule: 'all USED coefficients'): the forecast-used slopes; for rejected / analysis equations every
# stochastic regressor. Deterministic dummies (d2019 step/impulse) and DOLS lead/lag terms are not part of the basis.
_DET = {'d2019'}
for e in REGX.equations:
    if e['id'].startswith('FR10.B_'): continue
    rows = [r for r in e['coefficients'] if r.get('role') == 'regressor' and r['name'] not in _DET]
    basis = [r['name'] for r in rows if e['used_in_forecast'] and r.get('used_value') is not None] or [r['name'] for r in rows]
    rb = e['robustness']
    vd, nt = MR.verdict(rb.get('recursive'), rb.get('loo'), rb.get('chow_tests'), rb.get('cusum_p'), basis, {r['name']: r['coef'] for r in rows})
    rb['verdict_registry_all_regressors'] = rb['verdict']; rb['verdict'], rb['notes_az'] = vd, nt; rb['verdict_basis'] = basis
    e['summary_text'] = build_summary(e)
REGX.validate()
REG_PATH = OUT / 'FR10_equations.json'
REGX.write(REG_PATH)
_j = json.loads(REG_PATH.read_text(encoding='utf-8'))
_j.update(layer_a_data_mode='OBSERVED', layer_b_data_mode=DATA_MODE, layer_b_watermark=SYN_MARK if DATA_MODE == 'SYNTHETIC' else None,
          layer_b_note_az=(f'B qatının bütün tənlikləri {SYN_AZ} (synthetic: true)' if DATA_MODE == 'SYNTHETIC' else 'B qatı real müəssisə məlumatı üzrədir'))
REG_PATH.write_text(json.dumps(_j, ensure_ascii=False, indent=1, allow_nan=False), encoding='utf-8')
from microlib.schema import validate_file
assert validate_file(REG_PATH) == []
REG_T = REGX.table()
REG_T['layer'] = np.where(REG_T.id.str.startswith('FR10.B_'), 'B', 'A')
REG_T['subtask'] = [e['subtask'] for e in REGX.equations]
print(f'{len(REG_CHK)} registry-vs-notebook coefficient checks pass (max abs diff {REG_CHK.abs_diff.max():.1e}); '
      f'{REG_PATH.name}: {len(REGX)} equations ({int((REG_T.layer == "A").sum())} Layer A, {int((REG_T.layer == "B").sum())} Layer B), '
      f'{int(REG_T.used.sum())} used in forecasting; verdicts: {REG_T.verdict.value_counts().to_dict()}')
display(REG_T.groupby(['layer', 'subtask']).agg(equations=('id', 'size'), used=('used', 'sum')))
print(REGX.summary('FR10.pooled'))
print(REGX.summary('FR10.B_pf_fe'))
