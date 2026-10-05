# %% [markdown]
# ### 19.3 Ssenari mühərriki: ixrac edilən vəziyyət və `microlib/engines/fr10.py`
#
# Mühərrik Hissə 14-ün proqnoz həlledicisini (`core`) bir trayektoriya üçün yenidən həyata keçirir. Redaktə edilə
# bilənlər: FR1-in 2026–2030 üzrə hər sürücü trayektoriyası və FR4-ün məşğulluq indeksləri (ekzogen), proqnoz əmsalları
# (birləşdirilmiş elastiklik β, neft emalının neft qiymətinə görə elastikliyi, mədənçıxarma qaydalarının iki elastikliyi,
# 13 regional meyl — dəyər, s.x. və etibarlılıq intervalı reyestrdən) və rıçaqlar (neft emalı zavodunun güc əmsalı,
# əmək payının sürüşməsi və marja qaydası, qeyri-neft bölüşdürməsinin kombinasiya çəkisi, regional büzülmə κ).
# `selftest()` hər ssenaridə `FR10_forecast_tidy.csv` faylını təkrar istehsal etməlidir (nisbi 1e-8) — bu, son xanada
# yoxlama ifadəsi ilə təsdiqlənir. Zəncirvari icrada (`microlib.engines.chain.run_chain`) FR1-in sürücü trayektoriyaları
# və — v2.1 — FR4-ün muzdlu işçilər indeksləri (`fr4:hired:<activity>`, 2025 = 1) yuxarı axındakı mühərriklərin
# nəticələrindən gəlir; FR3 istifadə olunmur (F13).

# %%
from microlib.engines import base as EB_
_regeq = {e['id']: e for e in REGX.equations}
def _coef_row(eid, name, label_az, sign=None, value=None, ci=None):
    r = next(c for c in _regeq[eid]['coefficients'] if c['name'] == name)
    v = r['used_value'] if value is None else value
    return dict(eq_id=eid, name=name, label_az=label_az, value=float(v), se=r['se'], ci_low=(ci or (r['ci_low'], r['ci_high']))[0],
                ci_high=(ci or (r['ci_low'], r['ci_high']))[1], estimate=r['coef'], sign_expected=sign, editable=True,
                min=None, max=None)
DV_AZ = {'rva_min': ('FR1: mədənçıxarma real əlavə dəyəri', 'mln manat (2015)'), 'rva_man': ('FR1: emal sənayesi real əlavə dəyəri', 'mln manat (2015)'),
         'rva_elc': ('FR1: elektrik enerjisi real əlavə dəyəri', 'mln manat (2015)'), 'rva_wat': ('FR1: su təchizatı real əlavə dəyəri', 'mln manat (2015)'),
         'p_min': ('FR1: mədənçıxarma deflyatoru', 'indeks'), 'p_man': ('FR1: emal sənayesi deflyatoru', 'indeks'), 'p_elc': ('FR1: elektrik enerjisi deflyatoru', 'indeks'),
         'p_wat': ('FR1: su təchizatı deflyatoru', 'indeks'), 'oil_exp_price': ('FR1: neftin ixrac qiyməti', 'ABŞ dolları / barel'),
         'wage': ('FR1: orta aylıq nominal əmək haqqı', 'manat'), 'rva_con': ('FR1: tikinti real əlavə dəyəri', 'mln manat (2015)'),
         'rcons': ('FR1: ev təsərrüfatlarının real istehlakı', 'mln manat (2015)'), 'rinv_non': ('FR1: qeyri-neft real investisiya', 'mln manat (2015)'),
         'rgdpoil': ('FR1: neft-qaz real ÜDM', 'mln manat (2015)'), 'p_con': ('FR1: tikinti deflyatoru', 'indeks'), 'p_gdp': ('FR1: ÜDM deflyatoru', 'indeks')}
EX_V = [v for v in DVARS if v != 'emp']
_exo = [dict(id=f'fr1_{v}', label_az=DV_AZ[v][0], unit=DV_AZ[v][1], years=FC_YEARS, min=1e-9, max=None, step=None, source='FR1_forecast_full.csv',
             baseline={s_: [float(x) for x in scen_arrays(s_)[v][0, 1:]] for s_ in SCEN}) for v in EX_V]
_exo += [dict(id=f'fr4_hired_{s_}', label_az=f'FR4: muzdlu işçilərin indeksi, {SECT_AZ[s_].lower()} (2025 = 1)', unit='indeks (2025 = 1)', years=FC_YEARS,
              min=1e-9, max=None, step=None, source='FR4_hired_by_activity.csv', baseline={sc: [float(x) for x in fr4_index(sc)[s_][0, 1:]] for sc in SCEN})
         for s_ in SECV]
_coefs = [_coef_row('FR10.pooled', 'x', 'Əlaqəli sektor elastikliyi β (qeyri-neft sahə payları)', +1),
          _coef_row('FR10.mining_08', 'x', 'Digər faydalı qazıntılar: tikinti əlavə dəyərinə elastiklik (yalnız quarrying_rule = construction_link olduqda)',
                    +1, value=MINING_RULES['e08'])]
_coefs += [_coef_row(f'FR10.oil_{b}', 'dln_oil_azn', f'{BNAME_AZ[b]}: deflyatorun neft qiymətinə elastikliyi', +1) for b in OIL]
if 'FR10.mining_07' in _regeq:
    _r7 = next(c for c in _regeq['FR10.mining_07']['coefficients'])
    _coefs.append(dict(eq_id='FR10.mining_07', name=_r7['name'], label_az='Metal filizləri: sürücüyə elastiklik (qayda: 1)', value=1.0, se=None,
                       ci_low=None, ci_high=None, estimate=1.0, sign_expected=+1, editable=True, min=None, max=None))
_coefs += [_coef_row('FR10.reg_system', slug(k), f'{REGION_AZ[k]}: neft-sektor qarışığına elastiklik (büzülmüş)', None) for k in REG_SLOPES]
_levers = [dict(id=f'cap_factor_{b}', label_az=f'{BNAME_AZ[b]}: emal həcmi əmsalı (2026–30 / 2025)', value=float(CAPF[b]), default=float(CAPF[b]),
                min=0.5, max=1.5, step=0.005, note_az=f'baza: 2023–25 orta emal həcmi; maksimum 2015–25: {CAPMAX[b]:.3f}') for b in OIL]
_levers += [dict(id='quarrying_rule', label_az='Digər faydalı qazıntılar (08): proqnoz qaydası',
                 value='construction_link' if MINING_RULES['rule08'].startswith('unit') else 'neutral',
                 default='construction_link' if MINING_RULES['rule08'].startswith('unit') else 'neutral', options=['neutral', 'construction_link'],
                 note_az=f"neutral: real buraxılış 2025 faktiki səviyyəsində sabit (baza, DM p = {MINING_RULES['unit08_dm_p']:.3f}); "
                         "construction_link: FR1 tikinti əlavə dəyəri indeksi^elastiklik (həssaslıq)"),
            dict(id='labour_share_shift_pp', label_az='Əməyin əlavə dəyərdə payına düzəliş (faiz bəndi, marja qaydası)', value=0.0, default=0.0,
                 min=-20.0, max=20.0, step=0.5),
            dict(id='margin_mode', label_az='Marja qaydası', value='labour_share', default='labour_share',
                 options=['labour_share', 'fr1_wage', 'product_wage'], note_az='labour_share: əməyin payı 2023–25 ortası; fr1_wage: FR1 əmək haqqı yolu; product_wage: məhsul ifadəsində sabit əmək haqqı'),
            dict(id='combo_weight', label_az='Qeyri-neft bölgüsündə əlaqəli sektor modelinin çəkisi (0 = sabit paylar, 1 = model)',
                 value=1.0 if MAN_MODE == 'pooled' else 0.5, default=1.0 if MAN_MODE == 'pooled' else 0.5, min=0.0, max=1.0, step=0.05),
            dict(id='kappa_regions', label_az='Regional əmsalların büzülmə intensivliyi κ (0 = büzülmə yoxdur)', value=float(SELECT['R']['kappa']),
                 default=float(SELECT['R']['kappa']), min=0.0, max=1e6, step=None)]
ENG_INPUTS = dict(exogenous=_exo, coefficients=_coefs, levers=_levers)
_xsR = SPEC_X.get(PAR['R']['spec'], [])
ENG_STATE = dict(
    module='FR10', scen=SCEN, years=YRS, fc_years=FC_YEARS, last_act=LAST_ACT, bcodes=BCODES, manuf=MANUF, mining=MINING, oil=OIL, nonoil=NONOIL,
    bsec=BSEC, secv=SECV, link=LINK, sectot=SECTOT, reg_names=REG_NAMES, dvars=DVARS,
    q25={b: float(Q.loc[LAST_ACT, b]) for b in BCODES}, pdef25={b: float(PDEF.loc[LAST_ACT, b]) for b in BCODES},
    capf={b: float(v) for b, v in CAPF.items()}, eps_oil={b: float(v) for b, v in EPS_OIL.items()}, beta=float(BETA), man_mode=MAN_MODE,
    s25C=[float(x) for x in S25['C']], mining_rules={k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in MINING_RULES.items()},
    d07=_d07, sec_go25={s_: float(SEC_GO.loc[LAST_ACT, s_]) for s_ in SECV},
    inc25={s_: dict(VA=float(INC.loc[(s_, LAST_ACT), 'VA']), CE=float(INC.loc[(s_, LAST_ACT), 'CE'])) for s_ in SECV},
    otp_sh={s_: float(OTP_SH[s_]) for s_ in SECV}, ls_avg={s_: float(LS_AVG[s_]) for s_ in SECV},
    na_go25={b: float(NA_GO.loc[LAST_ACT, b]) for b in MANUF}, vago25={b: float(VAGO25[b]) for b in MANUF},
    wbva_avg={b: float(WBVA_AVG[b]) for b in MANUF}, wbill25={b: float(WBILL.loc[LAST_ACT, b]) for b in MANUF},
    emp25={b: float(EMP25[b]) for b in BCODES}, wage25={b: float(WAGE25[b]) for b in BCODES}, ns25=[float(x) for x in NS25],
    reg=dict(xs=_xsR, lo25=[float(SYS_R.LO[k].loc[LAST_ACT]) for k in REG_NAMES], x2_25=float(SYS_R.X.loc[LAST_ACT, 'x2']),
             b={k: [float(PAR['R'][k]['b'][x]) for x in _xsR] for k in REG_NAMES},
             raw_b={k: [float(RAW_R[k]['b'][x]) if k != SYS_R.ref else 0.0 for x in _xsR] for k in REG_NAMES} if _xsR else {},
             raw_se={k: [float(RAW_R[k]['se'][x]) if k != SYS_R.ref else float('nan') for x in _xsR] for k in REG_NAMES} if _xsR else {},
             w25=[float(SYS_R.W.loc[LAST_ACT, k]) for k in REG_NAMES], ref=SYS_R.ref, kappa=float(SELECT['R']['kappa']),
             go25_sum=float(REG_GO.loc[LAST_ACT].sum()), slugs={k: slug(k) for k in REG_NAMES}),
    f1h25={v: float(F1H.loc[LAST_ACT, v]) for v in DVARS if v != 'emp'},
    products=[dict(id=CID('prod', PROD_IDS[r['product']]), branch=r.branch, intensity=float(r.intensity_used)) for _, r in PRODF.iterrows()],
    components=[c['id'] for c in COMP], inputs=ENG_INPUTS, tidy_csv='FR10_forecast_tidy.csv',
    headline=['fr10:ind_output', 'fr10:sec_output:C', 'fr10:sec_output:B', 'fr10:share_of_manufacturing:19', 'fr10:sec_GOS_share_VA:C'])
EB_.save_state('FR10', ENG_STATE, root=str(BASE))
print(f'engine state written: output/engine/FR10_state.json (+ .npz) — {len(_exo)} exogenous paths, {len(_coefs)} coefficients, '
      f'{len(_levers)} levers, {len(COMP)} output series')
