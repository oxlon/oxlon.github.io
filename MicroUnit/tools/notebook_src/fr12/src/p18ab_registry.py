# %% [markdown]
# ## Hissə 18A — Tənliklər reyestri (v2)
#
# Bu notebook-da qiymətləndirilmiş hər tənlik `microlib.registry` vasitəsilə qeydə alınır və `output/FR12_equations.json`
# faylına yazılır: giriş/çıxış panellərinin namizəd və proqnoz sabit effektlər tənlikləri (məhdudiyyət testləri kimi
# klasterli vəhşi (wild) butstrap p-dəyərləri və tətbiq olunan qaydanın nümunədən kənar yoxlama bloku ilə), KOB pay
# sistemi, boşluqların doldurulması üzrə həssaslıq yenidən qiymətləndirmələri, IO ssenari alətləri və konsentrasiya
# hədlərinin xəritələnməsi (**kalibrlənmiş**, qiymətləndirilməmiş: parametrlər sabitdir, fərziyyələr `notes_az`-dadır),
# habelə B qatının ekonometrikası (SİNTETİK rejimdə `synthetic: true`). Reyestr hər reqressiyanı statsmodels ilə müstəqil
# şəkildə yenidən qiymətləndirir və əmsalların notebook-un öz əmsallarına bərabər olduğunu (nisbi 1e-6) yoxlama ifadəsi
# ilə təsdiqləyir. Driscoll–Kraay p-dəyərləri t(T−1) paylanmasından istifadə edir; T = 5 olduqda onlar etibarsızdır —
# oxunmalı olanlar `restrictions` blokundakı vəhşi butstrap p-dəyərləridir.

# %%
from types import SimpleNamespace
if str(BASE) not in sys.path: sys.path.insert(0, str(BASE))          # microlib lives in the project root
from microlib.registry import EquationRegistry
REGX = EquationRegistry('FR12', data_mode='OBSERVED')
GROUP_AZ = {'AGR': 'Kənd təsərrüfatı', 'IND': 'Sənaye', 'CON': 'Tikinti', 'TRD': 'Ticarət', 'TRA': 'Nəqliyyat', 'ACC': 'Yerləşdirmə və iaşə',
            'ICT': 'İnformasiya və rabitə', 'REA': 'Daşınmaz əmlak', 'EDU': 'Təhsil', 'HEA': 'Səhiyyə və sosial xidmətlər', 'OTH': 'Digər sahələr', 'ALL': 'Bütün sahələr'}
REGION_AZ = {'Baku city': 'Bakı şəhəri', 'Nakhchivan': 'Naxçıvan', 'Absheron-Khizi': 'Abşeron-Xızı', 'Daghlig Shirvan': 'Dağlıq Şirvan',
             'Ganja-Dashkasan': 'Gəncə-Daşkəsən', 'Karabakh': 'Qarabağ', 'Gazakh-Tovuz': 'Qazax-Tovuz', 'Guba-Khachmaz': 'Quba-Xaçmaz',
             'Lankaran-Astara': 'Lənkəran-Astara', 'Central Aran': 'Mərkəzi Aran', 'Mil-Mughan': 'Mil-Muğan', 'Shaki-Zagatala': 'Şəki-Zaqatala',
             'East Zangezur': 'Şərqi Zəngəzur', 'Shirvan-Salyan': 'Şirvan-Salyan', 'ALL': 'Bütün regionlar'}
SECT_AZ = {'A': 'Kənd, meşə təsərrüfatı və balıqçılıq', 'B': 'Mədənçıxarma', 'C': 'Emal sənayesi', 'D': 'Elektrik enerjisi, qaz və buxar',
           'E': 'Su təchizatı, tullantıların emalı', 'F': 'Tikinti', 'G': 'Ticarət; avtomobil təmiri', 'H': 'Nəqliyyat və anbar təsərrüfatı',
           'I': 'Yerləşdirmə və ictimai iaşə', 'J': 'İnformasiya və rabitə', 'K': 'Maliyyə və sığorta', 'L': 'Daşınmaz əmlak',
           'M': 'Peşə, elmi və texniki fəaliyyət', 'N': 'İnzibati və yardımçı xidmətlər', 'O': 'Dövlət idarəetməsi və müdafiə', 'P': 'Təhsil',
           'Q': 'Səhiyyə və sosial xidmətlər', 'R': 'İstirahət, əyləncə və incəsənət', 'S': 'Digər xidmətlər', 'U': 'Ekstraterritorial təşkilatlar'}
COEF_AZ = {'dem': 'sektor tələbinin artımı (FR1 real ƏDV), %', 'size': 'ln real ƏDV (ölçü)', 'lend': 'kredit faiz dərəcəsi, %', 'cred': 'real kredit artımı, %',
           'pcm': 'qiymət-xərc marjası (proksi), %', 'brk': 'tərif qırılması (006, 2022-dən 1)', 'd2022': '2022 impulsu (birdəfəlik silinmə dalğası)',
           'reg': 'regional sənaye buraxılışının artımı (FR10), %', 'non': 'qeyri-neft ÜDM artımı (FR1), %'}
SIGN = {('lnB', 'dem'): 1, ('lnB', 'lend'): -1, ('lnB', 'reg'): 1, ('lnB', 'non'): 1, ('lnB', 'pcm'): 1, ('lo', 'size'): -1}
PAB = {'activity': 'act', 'region': 'reg', 'sme': 'sme', 'sme_emp': 'smeemp'}
SUBT = {'activity': 'A1. Giriş və çıxış — fəaliyyət qrupları (DSK 006)', 'region': 'A2. Giriş və çıxış — iqtisadi rayonlar (statistik vahidlər)',
        'sme': 'A3. Konsentrasiya — KOS payı sistemi və HHI/CR4 hədləri', 'sme_emp': 'A3. Konsentrasiya — KOS-un işçi sayında payı',
        'alloc': 'A2. Giriş və çıxış — NACE bölmələri (bölüşdürmə)', 'gap': 'A4. Boşluqların doldurulması — həssaslıq (istifadə olunmur)',
        'IO': 'A5. Ssenari aləti — sənaye təşkilatı nəzəriyyəsi (kalibrlənmiş)', 'LB': 'B. Müəssisə səviyyəsində ekonometrika (B qatı)'}
UNITS = {'activity': GRP + ['ALL'], 'region': REGS + ['ALL']}
CONC_COLS = ['sme_output_share', 'large_share', 'hhi_lower', 'hhi_upper', 'hhi_upper_floor30', 'cr4_lower', 'cr4_upper']
def comps(pn, dep):
    if pn == 'sme': return [f'fr12:conc:{c}:{g}' for c in CONC_COLS for g in GRP]
    if pn == 'sme_emp': return [f'fr12:conc:sme_employment_share:{g}' for g in GRP]
    ms = ['new', 'entry', 'N'] if dep == 'lnB' else ['exit', 'exits', 'N']
    return [f'fr12:{PAB[pn]}:{m}:{iid(u)}' for m in ms for u in UNITS[pn]]
DEP_AZ = {'lnB': 'ln yeni qeydiyyatlar (doğulmalar)', 'exit': 'çıxış əmsalı, %', 'lo': 'KOS-un buraxılışda payının log-odds-u', 'lo_emp': 'KOS-un işçi sayında payının log-odds-u'}
HMET = {'lnB': 'log births', 'exit': 'exit rate, %', 'lo': 'log-odds SME output share'}
def holdout_block(pn, dep):
    h = HOLDV[(HOLDV.panel == pn) & (HOLDV.metric == ('log-odds SME employment share' if pn == 'sme_emp' else HMET[dep]))]
    if h.empty: return None
    r = h.iloc[0]; org = sorted({o for o, _ in MODELS[(pn, dep)]['hold']})
    out = dict(cut=int(org[0]), origins=org, years=[int(t) for t in str(r.targets).split(', ')], rmse=float(r.rmse_rule), theil_u_rw=float(r.theil_rule_vs_rw),
               theil_u_const=float(r.theil_rule_vs_constant), dm_p_rw=float(r.dm_p_rule_vs_rw), dm_p_const=float(r.dm_p_rule_vs_constant),
               rmse_rw=float(r.rmse_rw), rmse_constant=float(r.rmse_constant), rmse_null=float(r.rmse_null), rule=r.rule, metric=r.metric)
    if dep == 'lnB':
        e = HOLDV[(HOLDV.panel == pn) & HOLDV.metric.str.startswith('entry rate')]
        if len(e): out['entry_rate'] = dict(rmse=float(e.rmse_rule.iloc[0]), theil_u_rw=float(e.theil_rule_vs_rw.iloc[0]), theil_u_const=float(e.theil_rule_vs_constant.iloc[0]))
    return out
def used_parts(key, F=None):
    '''Parts of the applied rule that enter the forecast: the coherence filter at the last origin can drop every driver,
    in which case the rule falls back to its null part (apply_rule: pred = p0).'''
    r = SELECT[key]['rule']
    if r['mode'] == 'null' or (F is not None and F['m1'] is None): return {'m0'}
    return {'m1'} | ({'m0'} if r['mode'] == 'combination' else set())
REG_LOG = []
def reg_fe(eid, key, df, spec, fixed, used, sub=None, notes='', title_extra='', holdout=None, extra=None, restrictions=None, check_against=None, comp=None):
    pn, dep = key; m = fit_fe(df, dep, spec, fixed); d = m['d'].sort_values(['unit', 'year']); regs = m['regs'] + m['fixed']
    dlab = DEP_AZ['lo_emp'] if pn == 'sme_emp' else DEP_AZ[dep]
    if check_against is not None:                  # forecasting equation: must equal the notebook's applied model
        assert np.allclose(np.r_[m['b'], m['bf']], np.r_[check_against['b'], check_against['bf']], rtol=1e-10, atol=1e-12), eid
    name = spec_name(spec) + (' + ' + ' + '.join(m['fixed']) if m['fixed'] else '')
    kw = dict(components=comp or comps(pn, dep), subtask=sub or SUBT[pn], title_en=f'{pn}: {dep} — {name}{title_extra}', dependent_label_az=dlab,
              dependent_code=dep, used_in_forecast=used, notes_az=notes, holdout=holdout, extra=extra, restrictions=restrictions)
    if not regs:                                   # unit means only: the null without fixed terms
        a = m['a']; y = d.set_index(['unit', 'year'])[dep]
        eq = REGX.add(eid, y, None, estimator='unit means (FE only)', cov='—', fit_coef={f'a_{iid(u)}': float(v) for u, v in a.items()},
                      fit_se={f'a_{iid(u)}': float(d[d.unit == u][dep].std(ddof=1) / np.sqrt((d.unit == u).sum())) for u in a.index},
                      fitted=y.index.get_level_values(0).map(a).to_numpy(float), editable=[], title_az=f'{dlab} — yalnız vahid ortaları (sabit effektlər){title_extra}', **kw)
    else:
        y = d.set_index(['unit', 'year'])[dep]; X = d.set_index(['unit', 'year'])[regs]
        eq = REGX.add(eid, y, X, estimator='FE-oneway (unit), Driscoll-Kraay', cov='DK', fit_coef=dict(zip(regs, m['fit'].beta)), fit_se=dict(zip(regs, m['fit'].se)),
                      panel={'entity': 'unit', 'time': 'year', 'twoway': False}, coef_labels_az=COEF_AZ, sign_expected={c: SIGN.get((dep, c)) for c in regs if SIGN.get((dep, c))},
                      editable=list(regs) if used else [], title_az=f"{dlab} — {name.replace('null (FE + fixed terms)', 'yalnız sabit effektlər')}{title_extra}", **kw)
    eq.setdefault('extra', {})['unit_effects'] = {iid(u): float(v) for u, v in m['a'].items()}
    REG_LOG.append(dict(id=eid, key=f'{pn}/{dep}', spec=name, used=used)); return eq, m

def wcb_restr(df, dep, regs_all, drivers, label='β = 0'):
    out = []
    for j, x in enumerate(drivers):
        p_w, t_w = wild_cluster_p(df.dropna(subset=[dep] + regs_all), dep, regs_all, x, entity='unit', time='year', twoway=False, B=499, seed=SEED + j)
        out.append(dict(text_az=f'{COEF_AZ.get(x, x)}: {label} — vəhşi klaster bootstrap-t (Webb, B = 499, illər üzrə klaster, H0 tətbiq olunub)',
                        test='WCB-t (Webb)', stat=float(t_w), p=float(p_w), imposed=False))
    return out
