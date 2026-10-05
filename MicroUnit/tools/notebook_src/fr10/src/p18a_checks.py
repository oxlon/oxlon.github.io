# %% [markdown]
# ## Hissə 18 — Eynilik yoxlamaları, nəticə faylları, tapıntılar, sənədləşdirmə
#
# ### 18.1 Arifmetik yoxlamalar
#
# Bunlar modeli deyil, kodu yoxlayır: hər biri quruluşa görə ödənilir (softmax ilə toplanma, dəyər = həcm × qiymət,
# lövbərləmə, gəlirlər hesabının eyniliyi). Model haqqında sübutlar Hissə 11–13 və 16-dadır.

# %%
CH = []
def check(name, value, tol, unit='abs'):
    CH.append(dict(check=name, kind='arithmetic check - holds by construction', result=float(value), tolerance=tol, unit=unit,
                   passed=bool(abs(value) <= tol)))
for s_ in SCEN:
    S = SOL[s_]
    check(f'{s_}: manufacturing branch shares sum to 1', float((S['sh_man'].sum(axis=1) - 1).abs().max()), 1e-12)
    check(f'{s_}: industry branch shares sum to 1', float((S['sh_ind'].sum(axis=1) - 1).abs().max()), 1e-12)
    check(f'{s_}: regional shares sum to 1', float((S['reg_sh'].sum(axis=1) - 1).abs().max()), 1e-12)
    check(f'{s_}: manufacturing branches add up to section output', float((S['nom'][MANUF].sum(axis=1) / S['sec_go']['C'] - 1).abs().max()), 1e-12, 'ratio')
    check(f'{s_}: mining branches (oil part = residual) reconcile with FR1 mining output', float((S['nom'][MINING].sum(axis=1) / S['sec_go']['B'] - 1).abs().max()), 1e-12, 'ratio')
    _a = scen_arrays(s_)
    pidx = {k: pd.Series(_a[f'p_{v}'][0] / _a[f'p_{v}'][0, 0], index=YRS) for k, v in SECV.items()}
    oidx = pd.Series(_a['oil_exp_price'][0] / _a['oil_exp_price'][0, 0], index=YRS)
    gidx = pd.Series(_a['p_gdp'][0] / _a['p_gdp'][0, 0], index=YRS); cidx = pd.Series(_a['p_con'][0] / _a['p_con'][0, 0], index=YRS)
    defl = {b: PDEF.loc[LAST_ACT, b] * (oidx ** EPS_OIL[b] if b in OIL else gidx if b == '07' else cidx if b == '08' else pidx[BSEC[b]])
            for b in BCODES if b not in ('06', '09')}                 # 06, 09: residual (implied) deflator
    vv = max(float((S['real'][b] * defl[b] / S['nom'][b] - 1).abs().max()) for b in defl)
    check(f'{s_}: nominal = real x deflator for every branch (oil-linked: oil-price deflator)', vv, 1e-12, 'ratio')
    check(f'{s_}: non-oil + oil-linked branches add up to manufacturing output', float((S['nom'][MANUF].sum(axis=1) / S['sec_go']['C'] - 1).abs().max()), 1e-12, 'ratio')
    f_ = S['sec_fin']
    check(f'{s_}: section VA = compensation + other taxes + GOS', float((f_.VA - f_.CE - f_.OTP - f_.GOS).abs().max()), 1e-9, 'mn AZN')
B0 = SOL['Baseline']
check(f'model reproduces {LAST_ACT} branch output', float((B0['nom'].loc[LAST_ACT] / GO.loc[LAST_ACT, BCODES] - 1).abs().max()), 1e-12, 'ratio')
check(f'model reproduces {LAST_ACT} regional shares', float((B0['reg_sh'].loc[LAST_ACT] - SYS_R.W.loc[LAST_ACT]).abs().max()), 1e-12, 'share')
check(f'non-state share {LAST_ACT}: composition vs published (pp)', float(B0['ns_share'].loc[LAST_ACT] * 100 - NS.loc[LAST_ACT, 'ALL'] * 100), 0.05, 'pp')
check('vectorised fan simulator reproduces the solver (zero shocks)', VEC_CHECK, 1e-9)
check('Törnqvist TFP decomposition closes', float(gap_), 1e-9)
check('DSK adding-up checks (Part 5) all pass', float((~pd.DataFrame(REC).passed).sum()), 0, 'count')
check(f'Layer-B pipeline tests all pass ({DATA_MODE} panel)', float((~PIPE.passed).sum()), 0, 'count')
check('firm-panel swap tests all pass (temporary directory)', float((~SWAP.passed).sum()), 0, 'count')
CHK_T = pd.DataFrame(CH)
display(CHK_T)
assert CHK_T.passed.all(), f'failed checks: {CHK_T[~CHK_T.passed].check.tolist()}'
print(f'all {len(CHK_T)} arithmetic checks pass')

# %% [markdown]
# **v2.1 sahənin real buraxılışının inandırıcılığı.** Həcm indeksinin yoxlanılmasından (Hissə 5.1) sonra hər sahənin
# 2030-cu ildəki real buraxılışı hər ssenaridə bütöv emal sənayesi bölməsinin real buraxılışından (öz 2025-ci il
# deflyatoru və FR1-in emal sənayesi qiymət indeksi ilə deflyasiya edilmiş C bölməsinin buraxılışı) aşağı qalmalıdır.

# %%
_PC25 = float(GO_all['C'].loc[LAST_ACT] / Q_AGG['C'].loc[LAST_ACT])
REAL_CHECK = []
for s_ in SCEN:
    _pm = scen_arrays(s_)['p_man'][0]
    _secC = SOL[s_]['sec_go']['C'] / (_PC25 * pd.Series(_pm / _pm[0], index=YRS))
    for b in BCODES:
        REAL_CHECK.append(dict(scenario=s_, nace2=b, real_2025=float(SOL[s_]['real'].loc[LAST_ACT, b]), real_2030=float(SOL[s_]['real'].loc[FC_YEARS[-1], b]),
                               section_C_real_2030=float(_secC.loc[FC_YEARS[-1]]), lp_2030=float(SOL[s_]['lp'].loc[FC_YEARS[-1], b])))
REAL_CHECK = pd.DataFrame(REAL_CHECK)
REAL_CHECK['below_section_C'] = REAL_CHECK.real_2030 < REAL_CHECK.section_C_real_2030
DEFL_CHECK = DEFL_RANGE.join(REAL_CHECK[REAL_CHECK.scenario == 'Baseline'].set_index('nace2')[['real_2030', 'section_C_real_2030', 'lp_2030', 'below_section_C']]
                             .add_suffix('_Baseline')).rename_axis('nace2')
display(DEFL_CHECK[[f'real_to_nominal_{LAST_ACT}', f'real_to_nominal_{LAST_ACT}_published_index', 'real_2030_Baseline', 'lp_2030_Baseline']].round(2))
assert REAL_CHECK.below_section_C.all(), REAL_CHECK[~REAL_CHECK.below_section_C]
print(f"every branch's {FC_YEARS[-1]} real output is below section C real output ({REAL_CHECK.section_C_real_2030.min():,.0f}-"
      f"{REAL_CHECK.section_C_real_2030.max():,.0f} mn AZN 2015) in all scenarios; largest branch: "
      f"{REAL_CHECK.loc[REAL_CHECK.real_2030.idxmax(), 'nace2']} {REAL_CHECK.real_2030.max():,.0f}")
