# %% [markdown]
# ### 18C.1 Dayanıqlıq xülasəsi və əmsal həssaslığı (tornado)
#
# Reyestrdən: hər tənliyin stabillik hökmü (müqavilə qaydası: rekursiv və bir ili çıxarmaqla işarələr, tətbiq oluna bildikdə
# Chow/CUSUM) və uğursuz test. Mühərrikdən: hər redaktə edilə bilən proqnoz əmsalı üçün onu −1 və +1 standart xəta qədər
# dəyişdirməyin dörd əsas komponentə 2030-cu il təsiri (Əsas ssenari dəyərinin %-i) — bütün qruplar üzrə giriş əmsalı,
# çıxış əmsalı və qeydiyyatdan keçmiş subyektlərin ehtiyatı (006), habelə statistik vahidlərin ehtiyatı (regionlar). B
# qatının modelləri SİNTETİK nümayişlərdir: onların yoxlaması zamana görə stabillik deyil, parametrlərin bərpasıdır
# (17.7 (g)).

# %%
RB = []
for e in REGX.equations:
    rb = e['robustness']; rec = rb.get('recursive') or {}; loo = rb.get('loo') or {}
    regs = [c['name'] for c in e['coefficients'] if c.get('role') == 'regressor']
    s0 = {c['name']: np.sign(c['coef']) for c in e['coefficients'] if c.get('coef') is not None}
    fr = [c for c in regs if any(np.sign(v) != s0[c] for v in (rec.get('coef', {}).get(c) or []) if v is not None)]
    fl = [c for c in regs if any(np.sign(v) != s0[c] for v in (loo.get('coef', {}).get(c) or []))]
    failed = '; '.join(x for x in [('rekursiv işarə dəyişir: ' + ', '.join(fr)) if fr else '', ('bir ili çıxarmaqla işarə dəyişir: ' + ', '.join(fl)) if fl else '',
                                   'Chow p < 0.05' if (rb.get('chow') or {}).get('p') is not None and rb['chow']['p'] < 0.05 else ''] if x)
    kind = ('B qatı (sintetik): yoxlama parametr bərpasıdır (17.7 g)' if e['id'].startswith('FR12.LB_') and e['synthetic'] else
            'kalibrlənmiş model: dayanıqlıq testi tətbiq olunmur' if e['estimator'].startswith('calibrated') else '')
    RB.append(dict(equation=e['id'], title_az=e['title_az'], used_in_forecast=e['used_in_forecast'], synthetic=e['synthetic'], verdict=rb['verdict'],
                   failed_test=failed or ('—' if rb['verdict'] == 'stabil' else 'testlər mümkün deyil / tam deyil'), note_az='; '.join(x for x in [rb.get('notes_az', ''), kind] if x)))
ROBS = pd.DataFrame(RB); ROBS.to_csv(OUT / 'FR12_robustness_summary.csv', index=False)
display(ROBS.groupby(['used_in_forecast', 'verdict']).size().rename('equations').reset_index())
display(ROBS[ROBS.used_in_forecast][['equation', 'verdict', 'failed_test']])
HEAD = {'fr12:act:entry:ALL': 'giriş əmsalı, bütün sahələr (006)', 'fr12:act:exit:ALL': 'çıxış əmsalı, bütün sahələr (006)',
        'fr12:act:N:ALL': 'qeydiyyatdakı subyektlər, bütün sahələr (006)', 'fr12:reg:N:ALL': 'statistik vahidlər, bütün regionlar'}
_b30 = {k: ENG12.run({}, 'Baseline')['series'][k]['2030'] for k in HEAD}
TOR = []
for c in ENG12.inputs()['coefficients']:
    if c.get('se') is None or not np.isfinite(c['se']) or c['se'] <= 0: continue
    key = f"{c['eq_id']}|{c['name']}"; row = dict(eq_id=c['eq_id'], coefficient=c['name'], label_az=c['label_az'], value=c['value'], se=c['se'], part=c['part'], rule=c['rule_key'])
    for sgn, lab in [(-1, 'minus_1se'), (1, 'plus_1se')]:
        r = ENG12.run({'coefficients': {key: c['value'] + sgn * c['se']}}, 'Baseline')['series']
        for hid in HEAD: row[f'{lab}:{hid}'] = (r[hid]['2030'] / _b30[hid] - 1) * 100
    TOR.append(row)
TORN = pd.DataFrame(TOR)
_long = []
for _, r in TORN.iterrows():
    for hid, hl in HEAD.items():
        _long.append(dict(eq_id=r.eq_id, coefficient=r.coefficient, label_az=r.label_az, coef_value=r.value, coef_se=r.se, headline=hid, headline_az=hl, baseline_2030=_b30[hid],
                          effect_minus_1se_pct=r[f'minus_1se:{hid}'], effect_plus_1se_pct=r[f'plus_1se:{hid}'],
                          swing_pct=abs(r[f'plus_1se:{hid}'] - r[f'minus_1se:{hid}'])))
COEFSENS = pd.DataFrame(_long).sort_values(['headline', 'swing_pct'], ascending=[True, False])
COEFSENS.to_csv(OUT / 'FR12_coef_sensitivity.csv', index=False)
display(COEFSENS.pivot_table(index=['eq_id', 'coefficient'], columns='headline', values='swing_pct').round(3))
_top = COEFSENS.loc[COEFSENS.groupby('headline').swing_pct.idxmax()]
print('tornado headline (largest ±1 SE swing in 2030): ' + '; '.join(f"{r.headline_az}: {r.coefficient} ({r.eq_id}) {r.effect_minus_1se_pct:+.2f}% / {r.effect_plus_1se_pct:+.2f}%"
                                                                     for r in _top.itertuples()))
