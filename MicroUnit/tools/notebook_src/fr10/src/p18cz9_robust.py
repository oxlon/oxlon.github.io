# %% [markdown]
# ### 19.4 Mühərrikin öz-özünü yoxlaması, dayanıqlıq xülasəsi və əmsal həssaslığı (tornado)
#
# Mühərrik yenidən idxal edilir və tam proqnoz cədvəlini təkrar istehsal etməlidir. Dayanıqlıq: hər tənlik üzrə reyestr
# hökmü və onun əsasındakı test(lər). Həssaslıq: hər redaktə edilə bilən proqnoz əmsalı −1 və +1 standart xəta qədər
# dəyişdirilir (Əsas ssenari), 2030-cu ilin əsas komponentlərinə (sənaye, emal sənayesi və mədənçıxarma buraxılışı, neft
# emalının emal sənayesindəki payı, emal sənayesində əlavə dəyərdə ÜƏM-in payı) təsir Əsas ssenari dəyərinin %-i ilə;
# rıçaqlar da eyni qaydada.

# %%
import importlib
import microlib.engines.fr10 as ENG
ENG = importlib.reload(ENG); ENG._S = None
import time as _time
_t0 = _time.perf_counter(); ENG_ST = ENG.selftest(); _t1 = _time.perf_counter() - _t0
print(f"engine selftest: {'PASS' if ENG_ST['ok'] else 'FAIL'}; max rel diff " +
      ', '.join(f"{s_} {v['max_rel_diff']:.1e} ({v['n_rows']} rows)" for s_, v in ENG_ST['detail'].items()) + f"; {_t1:.2f} s for 3 scenarios")
assert ENG_ST['ok'], {s_: v['problems'] for s_, v in ENG_ST['detail'].items()}
CAT_PROBS = check_catalog(OUT / 'FR10_indicator_catalog.csv', OUT / 'FR10_equations.json', ENG.run({}, 'Baseline'))
assert not CAT_PROBS, CAT_PROBS[:5]
print('catalogue cross-check (registry components, catalogue equation ids, engine series ids): 0 problems')
# --- robustness summary from the registry
RB = []
for e in REGX.equations:
    rb, dg = e['robustness'], e['diagnostics']; used = rb.get('verdict_basis') or [c['name'] for c in e['coefficients'] if c.get('role') == 'regressor']
    fails = []
    rec = rb.get('recursive') or {}
    for c in used:
        s0 = np.sign(next(r['coef'] for r in e['coefficients'] if r['name'] == c) or 0)
        p_ = [v for v in (rec.get('coef') or {}).get(c, []) if v is not None]
        if p_ and s0 and (np.sign(p_) != s0).any(): fails.append(f'rekursiv işarə dəyişməsi ({c})')
        lo = (rb.get('loo') or {}).get('coef', {}).get(c, [])
        if lo and s0 and (np.sign(lo) != s0).any(): fails.append(f'LOO işarə dəyişməsi ({c})')
    for r in rb.get('chow_tests') or []:
        if r.get('p') is not None and r['p'] < 0.05: fails.append(f"Chow {r['break_year']} p={r['p']:.3f}")
    if rb.get('cusum_p') is not None and rb['cusum_p'] <= 0.05: fails.append(f"CUSUM p={rb['cusum_p']:.3f}")
    if (dg.get('diff_form') or {}).get('coherent') is False: fails.append('fərq forması ilə uyğunsuzluq')
    if dg.get('coint_established') is False: fails.append('kointeqrasiya müəyyən edilməyib')
    for c in e['coefficients']:
        uv = c.get('used_value')
        if e['used_in_forecast'] and uv is not None and c.get('ci_low') is not None and c['role'] in ('regressor',) and not (c['ci_low'] <= uv <= c['ci_high']):
            fails.append(f"istifadə olunan dəyər ({c['name']} = {uv:.3g}) 95% intervaldan kənar" + (' (EB büzülməsi)' if e['id'].startswith('FR10.reg_') else
                                                                                                   ' (tətbiq edilmiş qayda)' if c.get('imposed_value') is not None else ''))
    RB.append(dict(equation=e['id'], layer='B' if e['id'].startswith('FR10.B_') else 'A', subtask=e['subtask'], used_in_forecast=e['used_in_forecast'],
                   estimator=e['estimator'], verdict=rb['verdict'], failed_tests='; '.join(dict.fromkeys(fails)) or '—',
                   note_az=(rb.get('notes_az') or '') + (f' [{SYN_AZ}]' if e.get('synthetic') else ''), synthetic=e.get('synthetic', False)))
ROB = pd.DataFrame(RB); ROB.to_csv(OUT / 'FR10_robustness_summary.csv', index=False)
print('robustness verdicts:', ROB.groupby(['layer', 'verdict']).size().to_dict())
print('used in forecasting:', ROB[ROB.used_in_forecast & (ROB.layer == 'A')].verdict.value_counts().to_dict())
# --- coefficient and lever sensitivity, Baseline, 2030
HL = ENG_STATE['headline']; HL_AZ = {c['id']: c['label_az'] for c in COMP if c['id'] in HL}
_b0 = ENG.run({}, 'Baseline')['series']; y30 = str(FC_YEARS[-1])
SENS = []
def _sens(kind, key, lab, val, se, lo, hi, ovl, ovh, note='', base=None):
    rl, rh = ENG.run(ovl, 'Baseline'), ENG.run(ovh, 'Baseline'); b0 = _b0 if base is None else base
    for h in HL:
        b, l_, h_ = b0[h][y30], rl['series'][h][y30], rh['series'][h][y30]
        SENS.append(dict(type=kind, input=key, label_az=lab, value=val, se=se, low_value=lo, high_value=hi, component=h, component_az=HL_AZ[h],
                         base_2030=b, low_2030=l_, high_2030=h_, effect_low_pct=(l_ / b - 1) * 100, effect_high_pct=(h_ / b - 1) * 100, note_az=note))
for c in ENG.inputs()['coefficients']:
    k = f"{c['eq_id']}|{c['name']}"
    if c.get('se') is None or not np.isfinite(c['se'] or np.nan):
        SENS.append(dict(type='coefficient', input=k, label_az=c['label_az'], value=c['value'], note_az='standart xəta yoxdur (kalibrlənmiş qayda): ±1 s.x. tətbiq olunmur'))
        continue
    lo, hi = c['value'] - c['se'], c['value'] + c['se']
    _lv8 = {'quarrying_rule': 'construction_link'} if k == 'FR10.mining_08|x' else {}          # this elasticity acts through the lever only
    _sens('coefficient', k, c['label_az'], c['value'], c['se'], lo, hi, {'coefficients': {k: lo}, 'levers': _lv8}, {'coefficients': {k: hi}, 'levers': _lv8},
          'quarrying_rule = construction_link ilə (baza: neytral qayda)' if _lv8 else '', base=ENG.run({'levers': _lv8}, 'Baseline')['series'] if _lv8 else None)
for l in ENG.inputs()['levers']:
    if l['id'].startswith('cap_factor'):
        _sens('lever', l['id'], l['label_az'], l['value'], None, l['value'] - 0.05, l['value'] + 0.05, {'levers': {l['id']: l['value'] - 0.05}}, {'levers': {l['id']: l['value'] + 0.05}}, '±0,05')
    elif l['id'] == 'labour_share_shift_pp':
        _sens('lever', l['id'], l['label_az'], 0.0, None, -1.0, 1.0, {'levers': {l['id']: -1.0}}, {'levers': {l['id']: 1.0}}, '±1 faiz bəndi')
    elif l['id'] == 'combo_weight':
        _sens('lever', l['id'], l['label_az'], l['value'], None, 0.0, 1.0, {'levers': {l['id']: 0.0}}, {'levers': {l['id']: 1.0}}, '0 = sabit paylar, 1 = model')
    elif l['id'] == 'kappa_regions':
        _sens('lever', l['id'], l['label_az'], l['value'], None, 0.0, 1e6, {'levers': {l['id']: 0.0}}, {'levers': {l['id']: 1e6}}, 'büzülməsiz / tam büzülmə')
    elif l['id'] == 'quarrying_rule':
        _sens('lever', l['id'], l['label_az'], np.nan, None, np.nan, np.nan, {'levers': {l['id']: 'neutral'}}, {'levers': {l['id']: 'construction_link'}},
              'aşağı = neytral qayda (baza), yuxarı = FR1 tikinti əlaqəsi (vahid elastiklik)')
    elif l['id'] == 'quarrying_link_elasticity':                  # the unit-link rule's elasticity, ± the estimate's s.e., with the link switched on
        _q8 = {'quarrying_rule': 'construction_link'}; _s8 = l['estimate_se']
        _sens('lever', l['id'], l['label_az'], l['value'], _s8, l['value'] - _s8, l['value'] + _s8, {'levers': {**_q8, l['id']: l['value'] - _s8}},
              {'levers': {**_q8, l['id']: l['value'] + _s8}}, 'quarrying_rule = construction_link ilə, ±1 s.x. (qiymətləndirmənin); baza: neytral qayda',
              base=ENG.run({'levers': _q8}, 'Baseline')['series'])
    elif l['id'] == 'margin_mode':
        _sens('lever', l['id'], l['label_az'], np.nan, None, np.nan, np.nan, {'levers': {l['id']: 'fr1_wage'}}, {'levers': {l['id']: 'product_wage'}},
              'aşağı = FR1 əmək haqqı yolu, yuxarı = məhsul ifadəsində sabit əmək haqqı')
# each coefficient's largest effect on ANY component (the headline totals are FR1 paths; coefficients redistribute)
_ball = _b0
for c in ENG.inputs()['coefficients']:
    if c.get('se') is None: continue
    k = f"{c['eq_id']}|{c['name']}"
    _lv8 = {'quarrying_rule': 'construction_link'} if k == 'FR10.mining_08|x' else {}
    _bb = ENG.run({'levers': _lv8}, 'Baseline')['series'] if _lv8 else _ball
    rl, rh = [ENG.run({'coefficients': {k: c['value'] + d * c['se']}, 'levers': _lv8}, 'Baseline')['series'] for d in (-1, 1)]
    eff = {h: (rl[h][y30] / _bb[h][y30] - 1, rh[h][y30] / _bb[h][y30] - 1) for h in _bb if _bb[h][y30]}
    h = max(eff, key=lambda h: (round(max(abs(eff[h][0]), abs(eff[h][1])), 12), 'output_real' in h or 'reg_share' in h))
    SENS.append(dict(type='coefficient: largest effect on any component', input=k, label_az=c['label_az'], value=c['value'], se=c['se'],
                     low_value=c['value'] - c['se'], high_value=c['value'] + c['se'], component=h, component_az=next(x['label_az'] for x in COMP if x['id'] == h),
                     base_2030=_bb[h][y30], low_2030=rl[h][y30], high_2030=rh[h][y30], effect_low_pct=eff[h][0] * 100, effect_high_pct=eff[h][1] * 100,
                     note_az='quarrying_rule = construction_link ilə' if _lv8 else ''))
SENS = pd.DataFrame(SENS)
SENS.insert(1, 'type_az', SENS.type.map({'coefficient': 'əmsal (±1 standart xəta)', 'lever': 'rıçaq',
                                         'coefficient: largest effect on any component': 'əmsal: istənilən komponentə ən böyük təsir'}))
SENS.to_csv(OUT / 'FR10_coef_sensitivity.csv', index=False)
_sx = SENS[SENS.type != 'coefficient: largest effect on any component'].dropna(subset=['effect_low_pct']).assign(span=lambda d: (d.effect_high_pct - d.effect_low_pct).abs())
TORNADO_TOP = _sx.sort_values('span', ascending=False).groupby('component').head(2)[['component', 'input', 'effect_low_pct', 'effect_high_pct']]
display(TORNADO_TOP.round(3))
# sanity: the levers reproduce the notebook's sensitivity runs (Part 14.2)
_lv = ENG.run({'levers': {'combo_weight': 0.0}}, 'Baseline')['series']
assert abs(_lv['fr10:hhi_man'][y30] - LEVERS.loc['allocation: constant shares', 'HHI manufacturing 2030']) < 1e-6 * LEVERS.loc['allocation: constant shares', 'HHI manufacturing 2030']
_lv = ENG.run({'levers': {f'cap_factor_{OIL[0]}': CAPMAX[OIL[0]]}}, 'Baseline')['series'] if OIL else None
if OIL: assert abs(_lv['fr10:hhi_man'][y30] / LEVERS.loc['oil-linked branches at maximum throughput', 'HHI manufacturing 2030'] - 1) < 1e-9
_lq = ENG.run({'levers': {'quarrying_rule': 'construction_link'}}, 'Baseline')['series']
assert all(abs(_lq['fr10:output_nominal_mn_AZN:08'][str(y)] / QUARRY_LINK['nom'].loc[y, '08'] - 1) < 1e-12 for y in FC_YEARS)
assert all(abs(_lq['fr10:sec_output:B'][str(y)] / SOL['Baseline']['sec_go'].loc[y, 'B'] - 1) < 1e-12 for y in FC_YEARS)   # mining still = FR1
print('engine levers reproduce the notebook sensitivity runs (constant shares; maximum throughput; quarrying construction link)')
