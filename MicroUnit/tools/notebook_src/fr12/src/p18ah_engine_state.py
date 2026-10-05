# %% [markdown]
# ## Hissə 18C — Ssenari mühərriki: vəziyyətin ixracı və `microlib/engines/fr12.py`
#
# Mühərrik Hissə 13–16-nın proqnoz həllini burada ixrac edilən sadə məlumatlardan (`output/engine/FR12_state.json` +
# `.npz`) yenidən həyata keçirir: FR1-dən (sektorların real əlavə dəyəri, kredit faiz dərəcəsi, kredit, qeyri-neft ÜDM) və
# FR10-dan (regional sənaye buraxılışı, sənaye marjaları) sürücülər, tətbiq olunan qaydalar (vahid effektləri, meyllər,
# qırılma termini, lövbərlər, kombinasiya çəkiləri), ehtiyat-axın eyniliyi, KOB pay sistemi və konsentrasiya hədləri,
# proqnozlaşdırılan erkən xəbərdarlıq göstəricisi, IO ssenari alətləri (rıçaqlar) və Əsas ssenari zolaqları. `run({})`
# `FR12_forecast_tidy.csv` və `FR12_scenario_results.csv` fayllarını təkrar istehsal etməlidir (notebook-un sonunda
# `selftest()` ilə yoxlanılır).

# %%
def _rule_state(F, key):
    def part(m, anchored):
        if m is None: return None
        d = m['d'].sort_values(['unit', 'year']); cols = m['regs'] + m['fixed']
        return dict(a={u: float(v) for u, v in m['a'].items()}, regs=list(m['regs']), b=[float(v) for v in m['b']], fixed=list(m['fixed']), bf=[float(v) for v in m['bf']],
                    ref={u: {c: float(v) for c, v in (g[cols].iloc[-1] if anchored else g[cols].mean()).items()} for u, g in d.groupby('unit')} if cols else {})
    anch = F['shift'] is not None
    return dict(m0=part(F['m0'], False), m1=part(F['m1'], anch), shift={u: float(v) for u, v in F['shift'].items()} if anch else None,
                wt=float(F.get('wt', 1.0)) if F['m1'] is not None else 1.0, spec=list(F['spec']), rule=rname(SELECT[key]['rule']),
                eq_m1=EQ_MAP.get((key[0], key[1], 'm1')), eq_m0=EQ_MAP.get((key[0], key[1], 'm0')))
_src = {sc: FR1F[FR1F.scenario == sc].set_index('year') for sc in SCEN}
RVA = sorted({c for g in GRP for c in GROUPS[g][2]})
FR1_LAB = {'rva_agr': 'kənd təsərrüfatı', 'rva_min': 'mədənçıxarma', 'rva_man': 'emal sənayesi', 'rva_elc': 'elektrik enerjisi', 'rva_wat': 'su təchizatı', 'rva_con': 'tikinti',
           'rva_trd': 'ticarət', 'rva_tra': 'nəqliyyat', 'rva_tou': 'turizm (yerləşdirmə və iaşə)', 'rva_ict': 'informasiya və rabitə', 'rva_oth': 'digər xidmətlər'}
EXO = [dict(id=f'fr1:{c}', label_az=f'Real əlavə dəyər (FR1): {FR1_LAB.get(c, c)}', unit='mln AZN (real)', years=FC_YEARS,
            baseline={sc: [float(v) for v in _src[sc][c].loc[FC_YEARS]] for sc in SCEN}, min=0.0, max=None, step=1.0) for c in RVA]
EXO += [dict(id='fr1:lendrate', label_az='Kredit faiz dərəcəsi (FR1), %', unit='%', years=FC_YEARS, baseline={sc: [float(v) for v in _src[sc].lendrate.loc[FC_YEARS]] for sc in SCEN}, min=0.0, max=60.0, step=0.1),
        dict(id='fr1:rcred_tot', label_az='Real kredit qalığı (FR1)', unit='mln AZN (real)', years=FC_YEARS, baseline={sc: [float(v) for v in _src[sc].rcred_tot.loc[FC_YEARS]] for sc in SCEN}, min=0.0, max=None, step=1.0),
        dict(id='fr1:rgdpnon', label_az='Real qeyri-neft ÜDM (FR1)', unit='mln AZN (real)', years=FC_YEARS, baseline={sc: [float(v) for v in _src[sc].rgdpnon.loc[FC_YEARS]] for sc in SCEN}, min=0.0, max=None, step=1.0)]
_rf = {sc: FR10_REGF[FR10_REGF.scenario == sc].set_index('year')[REGS] for sc in SCEN}
EXO += [dict(id=f'fr10:output_mn_AZN:{iid(u)}', label_az=f'Regional sənaye buraxılışı (FR10): {REGION_AZ[u]}', unit='mln AZN', years=FC_YEARS,
             baseline={sc: [float(v) for v in _rf[sc][u].loc[FC_YEARS]] for sc in SCEN}, min=0.0, max=None, step=1.0) for u in REGS]
EXO += [dict(id=f'fr12:assume:pcm:{g}', label_az=f'Qiymət-xərc marjası fərziyyəsi: {GROUP_AZ[g]}' + (' (FR10 sənaye marjası yolu)' if g == 'IND' else ' (2025 səviyyəsində saxlanılır)'), unit='%',
             years=FC_YEARS, baseline={sc: [float(pcm_path(g, sc, y)) for y in FC_YEARS] for sc in SCEN}, min=0.0, max=100.0, step=0.1) for g in GRP]
COEFS = []
for k_, eid in EQ_MAP.items():
    for r in REGX.get(eid)['coefficients']:
        if r['editable'] and r['role'] in ('regressor', 'fixed'):
            COEFS.append(dict(eq_id=eid, name=r['name'], label_az=r['label_az'], value=r['coef'], se=r['se'], ci_low=r['ci_low'], ci_high=r['ci_high'], sign_expected=r.get('sign_expected'),
                              editable=True, rule_key=f'{k_[0]}|{k_[1]}', part=k_[2],
                              note_az='ankerlənmiş qaydada qırılma termini sabit qalır (son il və proqnoz illərində brk = 1): təsiri sıfırdır' if (r['name'] == 'brk' and k_[2] == 'm1') else ''))
LEVERS = [dict(id='io_market', label_az='IO ssenarisi: bazar', value='ICT', options=list(MK), kind='choice'),
          dict(id='io_hhi', label_az='HHI (0–10 000); boş = hədlərin həndəsi ortası', value=None, min=1.0, max=10000.0, step=10.0),
          dict(id='io_elasticity', label_az='Tələbin qiymət elastikliyi ε', value=1.0, min=0.1, max=5.0, step=0.1),
          dict(id='io_conduct', label_az='Davranış parametri θ (1 = Kurno)', value=1.0, min=0.05, max=1.0, step=0.05),
          dict(id='io_dN', label_az='Yeni rəqiblər ΔN (giriş ssenarisi)', value=1.0, min=0.0, max=20.0, step=1.0),
          dict(id='io_merger_s1', label_az='Birləşən müəssisə 1-in payı', value=0.10, min=0.0, max=1.0, step=0.01),
          dict(id='io_merger_s2', label_az='Birləşən müəssisə 2-nin payı', value=0.05, min=0.0, max=1.0, step=0.01),
          dict(id='io_cost_shock', label_az='Vahid xərc şoku (ilkin qiymətin payı)', value=0.05, min=-0.5, max=0.5, step=0.01),
          dict(id='io_import_m0', label_az='İdxal payı, əvvəl', value=0.30, min=0.0, max=0.95, step=0.01),
          dict(id='io_import_m1', label_az='İdxal payı, sonra', value=0.40, min=0.0, max=0.95, step=0.01),
          dict(id='io_import_eta', label_az='İdxal təklifinin elastikliyi η', value=2.0, min=0.0, max=20.0, step=0.1),
          dict(id='io_soe_sigma', label_az='Dövlət müəssisəsinin payı σ', value=float(SIG['industry']), min=0.01, max=0.95, step=0.01),
          dict(id='io_soe_lambda', label_az='Özəlləşdirmə dərəcəsi λ (0 = dövlət, 1 = tam özəl)', value=1.0, min=0.0, max=1.0, step=0.05),
          dict(id='io_grid', label_az='Bütün IO cədvəlini yenidən hesabla (FR12_scenario_results)', value=False, kind='bool')]
