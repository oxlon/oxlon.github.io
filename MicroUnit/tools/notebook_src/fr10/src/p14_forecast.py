# %% [markdown]
# ## Hissə 14 — FR1-in üç ssenarisi üzrə 2026–2030 proqnozu
#
# ### 14.1 Hissələr bir-birinə necə bağlanır
#
# | Obyekt | Qayda | Sürücü (ssenariyə xas) |
# |---|---|---|
# | Bölmə buraxılışı | 2025-ci il buraxılışı × FR1-in nominal ƏD indeksi (buraxılış/ƏD 2025 səviyyəsində saxlanılır) | FR1 `rva_*` × `p_*` |
# | Neft emalı, kimya | real = 2025 × güc əmsalı (2023–25 orta emal həcmi); qiymət = 2025 × (manatla neft qiyməti)^ε | DSK 018 emal həcmi; FR1 neft qiyməti |
# | Qeyri-neft emal sənayesi sahələri | (emal sənayesi buraxılışı − neftlə bağlı buraxılış) × §11.5-in payları (kombinasiya və ya birləşdirilmiş model) | FR1 `rva_con`, `rcons`, `rinv_non`, `rva_man` |
# | Mədənçıxarma sahələri | karxanalar kəsimdən əvvəlki qayda üzrə (v2: tikinti əlaqəsi üstün gəlmirsə, neytral sıfır variant); metal filizləri kəsimdən əvvəlki qayda üzrə; xam neft, qaz və yardımçı xidmətlər FR1 `rgdpoil` əsasında, nominal = FR1-in mədənçıxarma buraxılışının qalığı (§11.6) | FR1 `rva_con`, `rgdpoil`, `p_con`, `p_gdp` |
# | Qeyri-neft sahələrinin real buraxılışı | nominal ÷ (2025 deflyatoru × FR1-in bölmə deflyatoru indeksi) | FR1 `p_*` |
# | Sənayedə qeyri-dövlət sektorunun payı | buraxılışla çəkilmiş **2025-ci il sahədaxili** qeyri-dövlət payları — sırf tərkib effekti, mülkiyyət proqnozu deyil | — |
# | Regionlar | Hissə 12 sistemi × sənaye buraxılışı indeksi | FR1 neft tərkibi, miqyas |
# | Məşğulluq; əmək haqları | 2025-ci il işçi sayı × FR4-ün bölmə indeksi; 2025-ci il əmək haqqı × FR1-in orta əmək haqqı indeksi (F13) | FR4; FR1 |
# | ÜƏM marjası (Əsas ssenari) | ƏD-də əməyin payı 2023–25 ortasında saxlanılır (neytral, şərti marja); FR1-in əmək haqqı trayektoriyası və sabit məhsul əmək haqları həssaslıq variantlarıdır | — |
# | KOB payı, giriş/çıxış | saxlanılır / təqdim olunur (F11) | — |
#
# Bir funksiya (`core`) hər göstəricini istənilən sayda sürücü trayektoriyası üçün eyni anda hesablayır: üç ssenari,
# rıçaqlar və 500 butstrap təkrarlaması eyni koddan keçir.

# %%
fr3b = FR3W[FR3W.scenario == 'Baseline'].set_index('year')
_c3 = [c for c in fr3b.columns if c in BCODES]
_lev = (fr3b.loc[FC_YEARS[0], _c3] / WAGEC.loc[LAST_ACT, _c3] - 1) * 100
_g = ((fr3b.loc[FC_YEARS[-1], _c3] / fr3b.loc[FC_YEARS[0], _c3]) ** (1 / (H - 1)) - 1) * 100
finding('F13', 'FR3\'s branch wage paths are not anchored on 2025 branch wages and share one growth rate',
        f'FR3 2026 branch wage / DSK 2025 branch wage - 1 ranges {_lev.min():+.0f}% to {_lev.max():+.0f}% across {len(_lev)} branches; '
        f'2026-2030 growth is {_g.min():.2f}-{_g.max():.2f}% a year for every branch',
        'FR10 applies FR1\'s average-wage index to each branch\'s 2025 DSK wage; FR3 is not used for levels')
FINDINGS = pd.DataFrame(FIND).set_index('id')

YRS = [LAST_ACT] + FC_YEARS
DVARS = ['rva_min', 'rva_man', 'rva_elc', 'rva_wat', 'p_min', 'p_man', 'p_elc', 'p_wat', 'oil_exp_price', 'wage', 'emp',
         'rva_con', 'rcons', 'rinv_non', 'rgdpoil', 'p_con', 'p_gdp']
def drv_arrays(fcs):
    '''fcs: FR1 rows indexed (draw, year) -> dict of arrays (R, 6), 2025 actual (FR1 history) first.'''
    out = {}
    for v in DVARS:
        M = fcs[v].unstack('year')[FC_YEARS].to_numpy(float)
        out[v] = np.column_stack([np.full(len(M), F1H.loc[LAST_ACT, v] if v != 'emp' else np.nan), M])
    for s_, v in SECV.items():
        out[f'va_{v}_n'] = out[f'rva_{v}'] * out[f'p_{v}']
    return out
def scen_arrays(s_):
    return drv_arrays(F1F[F1F.scenario == s_].assign(draw=0).set_index(['draw', 'year']))
def fr4_index(scen):
    h = FR4H[FR4H.scenario == scen].set_index('year')
    return {s_: (h.loc[YRS, c] / h.loc[LAST_ACT, c]).to_numpy(float)[None, :] for s_, c in [('B', 'mining'), ('C', 'manuf'), ('D', 'elec'), ('E', 'water')]}

EMP25 = EMP_DSK.loc[LAST_ACT, BCODES]; WAGE25 = WAGEC.loc[LAST_ACT, BCODES]
OTP_SH = (INC.OTP / INC.VA).xs(LAST_ACT, level=1)
LS_AVG = (INC.CE / INC.VA).unstack(0).loc[LAST_ACT - 2:LAST_ACT].mean()
VAGO25 = (NA_VA[MANUF] / NA_GO[MANUF]).loc[LAST_ACT]
WBVA_AVG = (WBILL[MANUF] / NA_VA[MANUF]).loc[LAST_ACT - 2:LAST_ACT].mean()
S25 = {g: SHH[g].loc[LAST_ACT, u].to_numpy(float) for g, u in GROUP.items()}
IC_, IB_ = [BCODES.index(b) for b in NONOIL], [BCODES.index(b) for b in MINING]
NS25 = NS.loc[LAST_ACT, BCODES].to_numpy(float)

def core(D, emp_idx, emp_ratio=None, zsh=None, beta=None, mode=None, capf=None, margin='labour_share', regb=None, q08=None):
    beta = BETA if beta is None else beta; mode = MAN_MODE if mode is None else mode; capf = CAPF if capf is None else capf
    R_ = D['rva_man'].shape[0]; T_ = len(YRS); zsh = zsh or {}; out = {}
    er = np.ones((R_, T_)) if emp_ratio is None else emp_ratio
    t0 = (np.arange(T_) == 0)[None, :]
    secgo = {s_: SEC_GO.loc[LAST_ACT, s_] * D[f'va_{v}_n'] / D[f'va_{v}_n'][:, :1] for s_, v in SECV.items()}
    pidx = {s_: D[f'p_{v}'] / D[f'p_{v}'][:, :1] for s_, v in SECV.items()}
    nom = np.zeros((R_, T_, len(BCODES))); real = np.zeros_like(nom)
    oilidx = D['oil_exp_price'] / D['oil_exp_price'][:, :1]
    for b in OIL:
        j = BCODES.index(b)
        real[..., j] = Q.loc[LAST_ACT, b] * np.where(t0, 1.0, capf[b])
        nom[..., j] = real[..., j] * PDEF.loc[LAST_ACT, b] * oilidx ** EPS_OIL[b]
    rem = secgo['C'] - nom[..., [BCODES.index(b) for b in OIL]].sum(-1)
    out['rem_clipped'] = int((rem < 0.01 * secgo['C']).sum()); rem = np.maximum(rem, 0.01 * secgo['C'])
    for g, idx, tot in [('C', IC_, rem)]:
        rel = rel_index(lambda v: D[v], GROUP[g], g)
        dr = np.stack([rel[b] - rel[b][:, :1] for b in GROUP[g]], -1)
        W = alloc(S25[g], dr, beta, mode, zsh.get(g))
        nom[..., idx] = W * tot[..., None]
        real[..., idx] = nom[..., idx] / (PDEF.loc[LAST_ACT, GROUP[g]].to_numpy(float) * pidx[g][..., None])
    # mining (Part 11.6): quarrying from construction, metal ores neutral, the oil part absorbs the residual
    ix = lambda v: D[v] / D[v][:, :1]
    j6, j7, j8, j9 = (BCODES.index(b) for b in ['06', '07', '08', '09'])
    real[..., j8] = Q.loc[LAST_ACT, '08'] * (np.where(t0, 1.0, MINING_RULES['q08_level_factor']) * np.ones_like(ix('rva_con'))
                                             if (q08 or MINING_RULES['rule08']).startswith('neutral') else ix('rva_con') ** MINING_RULES['e08'])
    nom[..., j8] = real[..., j8] * PDEF.loc[LAST_ACT, '08'] * ix('p_con')
    r7 = MINING_RULES['rule07']
    q7 = (np.where(t0, 1.0, MINING_RULES['q07_level_factor']) if r7.startswith('neutral') else ix('rva_min') if 'mining' in r7 else ix('rva_con'))
    real[..., j7] = Q.loc[LAST_ACT, '07'] * q7 * np.ones_like(ix('p_gdp'))
    nom[..., j7] = real[..., j7] * PDEF.loc[LAST_ACT, '07'] * ix('p_gdp')
    for j, b in [(j6, '06'), (j9, '09')]: real[..., j] = Q.loc[LAST_ACT, b] * ix('rgdpoil')
    resid = secgo['B'] - nom[..., j7] - nom[..., j8]
    out['oil_resid_floor'] = int((resid < 0.05 * secgo['B']).sum()); resid = np.maximum(resid, 0.05 * secgo['B'])
    nom[..., j6] = resid * MINING_RULES['oil_split_06']; nom[..., j9] = resid * (1 - MINING_RULES['oil_split_06'])
    out['oil_defl_idx'] = ((nom[..., j6] + nom[..., j9]) / (real[..., j6] + real[..., j9])) / ((nom[:, :1, j6] + nom[:, :1, j9]) / (real[:, :1, j6] + real[:, :1, j9]))
    out['p_min_idx'] = pidx['B']
    for b, s_ in [('35', 'D'), ('36', 'E')]:
        j = BCODES.index(b); nom[..., j] = secgo[s_]; real[..., j] = nom[..., j] / (PDEF.loc[LAST_ACT, b] * pidx[s_])
    # regions
    par = PAR['R']; xs = SPEC_X.get(par['spec'], []); units = REG_NAMES
    LO25 = np.array([SYS_R.LO[k].loc[LAST_ACT] for k in units])
    mix = np.log(D['va_min_n'] / D['va_man_n']); mix = mix - mix[:, :1] + SYS_R.X.loc[LAST_ACT, 'x2']
    XR = np.stack([np.log(D['rva_man']), mix], -1)
    if xs:
        b0 = np.array([[par[k]['b'][x] for x in xs] for k in units])
        br = np.broadcast_to(b0, (R_,) + b0.shape) if regb is None else regb
        ix = [{'x1': 0, 'x2': 1}[x] for x in xs]
        z = LO25[None, None, :] + np.einsum('rtx,rkx->rtk', XR[..., ix] - XR[:, :1, ix], br)
    else:
        z = np.broadcast_to(LO25, (R_, T_, len(units))).copy()
    z = z + (zsh.get('R') if zsh.get('R') is not None else 0)
    e = np.exp(z - z.max(-1, keepdims=True)); out['reg_sh'] = e / e.sum(-1, keepdims=True)
    # employment, wages, productivity
    eidx = {s_: emp_idx[s_] * er for s_ in SECV}
    emp = np.stack([EMP25[b] * eidx[BSEC[b]] for b in BCODES], -1)
    widx = D['wage'] / D['wage'][:, :1]
    out.update(nom=nom, real=real, emp=emp, lp=real / emp * 1e3, sec_go=np.stack([secgo[s_] for s_ in SECV], -1))
    out['wage'] = WAGE25.to_numpy(float)[None, None, :] * widx[..., None]
    out['sh_ind'] = nom / nom.sum(-1, keepdims=True)
    mi = [BCODES.index(b) for b in MANUF]
    out['sh_man'] = nom[..., mi] / nom[..., mi].sum(-1, keepdims=True)
    out['ns_share'] = (nom * NS25).sum(-1) / nom.sum(-1); out['hhi_man'] = (out['sh_man'] ** 2).sum(-1) * 1e4
    gs, ls, vas, ces, ots = [], [], [], [], []
    for s_, v in SECV.items():
        va = INC.loc[(s_, LAST_ACT), 'VA'] * D[f'va_{v}_n'] / D[f'va_{v}_n'][:, :1]
        ce25 = INC.loc[(s_, LAST_ACT), 'CE']
        if margin == 'labour_share': ce = np.where(t0, ce25, LS_AVG[s_] * va)
        elif margin == 'fr1_wage':   ce = ce25 * widx * eidx[s_]
        else:                        ce = ce25 * pidx[s_] * eidx[s_]          # wages constant in product terms
        gs.append((va - ce - OTP_SH[s_] * va) / va * 100); ls.append(ce / va * 100); vas.append(va); ces.append(ce); ots.append(OTP_SH[s_] * va)
    out['sec_gos'] = np.stack(gs, -1); out['sec_ls'] = np.stack(ls, -1)
    out['sec_va'], out['sec_ce'], out['sec_otp'] = np.stack(vas, -1), np.stack(ces, -1), np.stack(ots, -1)
    na_go = NA_GO.loc[LAST_ACT, MANUF].to_numpy(float) * nom[..., mi] / nom[:, :1, mi]
    va_b = na_go * VAGO25[MANUF].to_numpy(float)
    if margin == 'labour_share':
        wb = np.where(t0[..., None], WBILL.loc[LAST_ACT, MANUF].to_numpy(float), WBVA_AVG[MANUF].to_numpy(float) * va_b)
    else:
        wi = widx if margin == 'fr1_wage' else pidx['C']
        wb = WBILL.loc[LAST_ACT, MANUF].to_numpy(float) * wi[..., None] * eidx['C'][..., None]
    out['gosp'] = (va_b - wb) / na_go * 100
    return out
