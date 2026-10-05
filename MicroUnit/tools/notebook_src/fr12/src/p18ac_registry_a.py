# %%
SELMAP = pd.DataFrame(SELTAB)
FINAL_SME = apply_rule(('sme', 'lo'), SELECT[('sme', 'lo')]['rule'], 2024, drivers_activity('Baseline'))
FIN = {**FINAL, ('sme', 'lo'): FINAL_SME, ('sme_emp', 'lo'): FINAL_SMEEMP}; ORIGX = {**ORIG, 'sme': 2024, 'sme_emp': 2024}
def sel_extra(pn, dep, spec):
    out = {}
    for lab, k in [('', 'sel_mse_2023'), (' | anchored', 'sel_mse_2023_anchored')]:
        cand = 'null (FE + fixed terms)' if not spec else f'structural: {spec_name(spec)}{lab}'
        r = SELMAP[(SELMAP.panel == pn) & (SELMAP.dep == dep) & (SELMAP.candidate == cand)]
        if len(r): out[k] = float(r.sel_mse.iloc[0])
    return out
EQ_MAP, NOTE_T5 = {}, 'DK p-dəyərləri t(T−1) ilə; T = 5 olduğundan etibarsızdır — vəhşi bootstrap p-dəyərləri "restrictions" bölməsindədir.'
for (pn, dep), M in MODELS.items():
    df, fixed, rule, Fk = M['df'], M['fixed'], SELECT[(pn, dep)]['rule'], FIN[(pn, dep)]; up = used_parts((pn, dep), Fk)
    tr = df[df.year <= ORIGX[pn]]
    _coh_last = coherence_filter(tr, dep, rule['spec'], fixed)[1] if rule['spec'] else []
    for spec in M['specs']:
        spec = list(spec); is_m1 = rule['mode'] != 'null' and bool(spec) and Fk['m1'] is not None and spec == list(Fk['spec']); is_m0 = not spec
        used = bool((is_m1 and 'm1' in up) or (is_m0 and 'm0' in up))
        eid = f"FR12.{PAB[pn]}_{dep}_{'_'.join(spec) if spec else 'null'}"
        restr = []
        if spec:
            m_ = fit_fe(tr, dep, spec, fixed); restr = wcb_restr(m_['d'], dep, spec + m_['fixed'], spec)
            if pn not in ('sme', 'sme_emp'):
                for x, r_ in zip(spec, restr):
                    ref = FULL[(FULL.panel == pn) & (FULL.dep == dep) & (FULL.spec == spec_name(spec)) & (FULL.driver == x)].wcb_p
                    assert len(ref) == 1 and abs(ref.iloc[0] - r_['p']) < 1e-12, (eid, x)
        role = ('proqnozda istifadə olunur: ' + rname(rule)) if used else 'namizəd spesifikasiya (proqnozda istifadə olunmur)'
        if spec and spec == list(rule['spec']) and Fk['m1'] is None:
            role = (f"seçilmiş qayda {rname(rule)}, lakin son mənbə ilində ({ORIGX[pn]}) uyğunluq (coherence) qaydası bütün sürücüləri çıxarıb: "
                    "proqnoz qaydanın sıfır hissəsidir (yalnız sabit effektlər)")
        elif not spec and used and Fk['m1'] is None and rule['mode'] != 'null':
            role = f"proqnozda istifadə olunur: {rname(rule)} qaydasının sıfır hissəsi (son mənbə ilində sürücülər uyğunluq qaydası ilə çıxarılıb)"
        notes = (f"{role}. Nümunə: illər {', '.join(str(int(y)) for y in sorted(tr.year.unique()))}, müşahidə edilmiş məlumat (doldurulmuş dəyərlər daxil deyil). "
                 + (NOTE_T5 if pn not in ('sme', 'sme_emp') else 'DK p-dəyərləri t(T−1).') + (f" Seçim (≤ {SEL_END} → 2023) və nümunədən kənar yoxlama bloku qaydaya aiddir." if used else ''))
        hold = holdout_block(pn, dep) if used and (is_m1 or rule['mode'] == 'null' or Fk['m1'] is None) else None
        coh = COHTAB[(COHTAB.key == str((pn, dep))) & COHTAB.driver.isin(spec)].drop(columns='key').to_dict('records') if spec else []
        ex_ = dict(selection=sel_extra(pn, dep, spec), coherence=coh, coherence_last_origin=_coh_last if spec == list(rule['spec']) else None, rule=rname(rule), implied_rw_weight=SELECT[(pn, dep)]['w_rw'], anchored=rule['anchor'] == 'last',
                   combination_weight=(0.5 if rule['mode'] == 'combination' else 1.0) if used else None)
        chk_m = Fk['m1'] if (is_m1 and used) else (Fk['m0'] if (is_m0 and used) else None)
        reg_fe(eid, (pn, dep), tr, spec, fixed, used, notes=notes, holdout=hold, extra=ex_, restrictions=restr, check_against=chk_m)
        if used: EQ_MAP[(pn, dep, 'm1' if is_m1 else 'm0')] = eid
# break term / impulse: wild bootstrap on the fixed term of each used equation
for (pn, dep, part), eid in EQ_MAP.items():
    m_ = FIN[(pn, dep)][part]
    if m_['fixed']:
        eq = REGX.get(eid); rr = wcb_restr(m_['d'], dep, m_['regs'] + m_['fixed'], m_['fixed'], label='= 0')
        for r_ in rr: r_['p'] = float(wild_cluster_p(m_['d'], dep, m_['regs'] + m_['fixed'], m_['fixed'][0], entity='unit', time='year', twoway=False, B=499, seed=SEED + 100)[0])
        eq['restrictions'] += rr
# gap-fill sensitivity re-estimates (Part 14.1): same rules on the panel with the filled 2021 values (not used in forecasting)
for key, G_ in [(k, v) for k, v in GAPSENS.items() if isinstance(k, tuple) and k[0] in ('activity', 'sme', 'sme_emp')]:
    pn, dep = key; dfF = G_['df']; dfF = dfF[dfF.year <= 2024]
    for part in ['m1', 'm0']:
        if G_['F'][part] is None: continue
        spec = G_['F']['spec'] if part == 'm1' else []
        reg_fe(f"FR12.gapsens_{PAB[pn]}_{dep}_{part}", key, dfF, spec, MODELS[key]['fixed'], False, sub=SUBT['gap'],
               notes=('Həssaslıq: doldurulmuş 2021 dəyərləri daxil edilməklə eyni qayda (2021 üçün brk = d2022 = ½; kənd təsərrüfatının 2021 doğulmaları çıxarılıb). '
                      'Proqnozda istifadə olunmur; dəyişikliklər FR12_gapfill_sensitivity.csv-dədir.'), title_extra=' [doldurulmuş 2021 ilə]',
               extra=dict(compare_with=EQ_MAP.get((pn, dep, part))), check_against=G_['F'][part])
print(f"Layer-A equations registered: {len(REGX)} ({sum(e['used_in_forecast'] for e in REGX.equations)} used in forecasting); forecasting map: "
      + '; '.join(f'{k[0]}/{k[1]}/{k[2]} -> {v}' for k, v in EQ_MAP.items()))
