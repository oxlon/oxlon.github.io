"""FR1 one-year solver: a line-by-line port of the notebook's `solve_year` (Part 11.3), damped Gauss-Seidel.
Only change: the coefficient set `c` (CF), the calibration `CAL` and the model lists come from the arguments
instead of notebook globals; `tfp_cum` (optional) generalises tfp_boost x tfp_years to a non-constant path."""
import numpy as np


def Lin(cf, **vals):
    """const + sum of coefficient x value over every coefficient of an equation (raises on a missing value)."""
    return cf['const'] + sum(cf[k]*vals[k] for k in cf if k != 'const')


def solve_year(M, c, CAL, prev, ex, maxit=800, tol=1e-10, damp=0.5, addf=None, init=None, freeze_capital=False):
    ENDO, KSECT, COMP, SECT, MKT, TFP_SECT, DELTA = (M['ENDO'], M['KSECT'], M['COMP'], M['SECT'], M['MKT'],
                                                    M['TFP_SECT'], M['DELTA'])
    A_ = addf or {}
    s = {k: prev.get(k, np.nan) for k in ENDO}
    for k in ['K_'+x for x in KSECT] + ['K_non']: s[k] = prev[k]
    if init is not None:
        for k, v in init.items():
            if np.isfinite(v): s[k] = v
    tfp = ex['tfp_cum'] if ex.get('tfp_cum') is not None else ex.get('tfp_boost', 0.0)*ex.get('tfp_years', 0.0)
    pop = ex['pop']; lpop = np.log(pop)
    err = np.inf
    for it in range(maxit):
        old = dict(s)
        # ===== Block B: hydrocarbons =====
        oil_p = np.exp(Lin(c['B1_oil_price'], ln_brent=np.log(ex['brent'])))
        s['oil_exp_price'] = oil_p
        s['x_g_oil_usd'] = CAL['bop_oil_ratio']*(ex['oil_exp_vol']*CAL['bbl']*oil_p
                                                 + ex['gas_exp_vol']*ex['gas_exp_price'])
        s['rva_min'] = np.exp(Lin(c['B2_mining'], ln_oil=np.log(ex['oil_prod']), ln_gas=np.log(ex['gas_prod']))
                              + A_.get('rva_min', 0))
        s['rgdpoil'] = np.exp(Lin(c['B3_oilgdp'], ln_oil=np.log(ex['oil_prod']), ln_gas=np.log(ex['gas_prod']))
                              + A_.get('rgdpoil', 0))
        # ===== Block G: prices and rates =====
        s['gap'] = 100*(np.log(s['rgdpnon']) - Lin(c['POT'], trend=ex['trend']))
        dln_wage = (np.log(s['wage']) - np.log(prev['wage']))*100
        s['infl'] = Lin(c['G4_infl'], dln_fx=ex['dln_fx'], dln_wage=dln_wage) + A_.get('infl', 0)
        s['cpi'] = prev['cpi']*(1 + s['infl']/100)
        s['p_cons'] = prev['p_cons']*(1 + s['infl']/100)
        s['p_inv'] = prev['p_inv'] *(1 + s['infl']/100)
        for sec in COMP:
            a0, b1, b2 = CAL['defl'][sec]
            s['p_'+sec] = prev['p_'+sec]*np.exp((a0 + b1*s['infl'] + b2*ex['dln_oil_azn'])/100)
        s['lendrate'] = Lin(c['G3_lendrate'], deprate=ex['deprate'], npl_ratio=ex['npl_ratio']) + A_.get('lendrate', 0)
        s['realrate'] = s['lendrate'] - s['infl']
        s['pension'] = ex['pension'] if ex.get('pension') is not None else \
            prev['pension']*(1 + s['infl']/100)*(1 + ex.get('pension_real_g', 0.0))
        # ===== Block E: income and labour =====
        s['lf'] = pop*np.exp(Lin(c['E4_lf'], trend=ex['trend']) + A_.get('lf', 0))
        s['emp'] = s['lf']*np.exp(Lin(c['E1_emp'], ln_gdpnon_pc=np.log(s['rgdpnon'])-lpop) + A_.get('emp', 0))
        s['unemp'] = 100*(s['lf'] - s['emp'])/s['lf']
        prod_non = s['rgdpnon']/s['emp']
        s['wage'] = np.exp(Lin(c['E2_wage'], ln_prod_non=np.log(prod_non), ln_cpi=np.log(s['cpi']),
                               ln_minwage=np.log(ex['minwage'])) + A_.get('wage', 0))
        s['rwage'] = s['wage']/s['cpi']*100
        wagebill_r = s['wage']*s['emp']*12/1000.0/s['p_cons']
        pens_r = s['pension']*pop/1000.0/s['p_cons']
        s['rhhdisp'] = np.exp(Lin(c['E3_hhdisp'], ln_wagebill_r=np.log(wagebill_r), ln_pens_r=np.log(pens_r),
                                  ln_gdpnon=np.log(s['rgdpnon'])) + A_.get('rhhdisp', 0))
        # ===== Block G: credit =====
        s['rdep_tot'] = np.exp(Lin(c['G7_dep'], ln_gdpnon=np.log(s['rgdpnon']), ln_hhdisp=np.log(s['rhhdisp']))
                               + A_.get('rdep_tot', 0))
        s['rcred_tot'] = np.exp(Lin(c['G1_credit'], ln_dep_r=np.log(s['rdep_tot']), polrate=ex['polrate'],
                                    ln_gdpnon=np.log(s['rgdpnon'])) + A_.get('rcred_tot', 0))
        s['rcred_hh'] = np.exp(Lin(c['G2_credhh'], ln_cred_tot_r=np.log(s['rcred_tot']), ln_hhdisp=np.log(s['rhhdisp']))
                               + A_.get('rcred_hh', 0))
        # ===== Block D: demand =====
        s['rcons'] = pop*np.exp(Lin(c['D1_cons'], ln_hhdisp_pc=np.log(s['rhhdisp'])-lpop,
                                    ln_cred_hh_pc=np.log(s['rcred_hh'])-lpop, realrate=s['realrate'])
                                + A_.get('rcons', 0))
        rev_oil_r = max(s['rev_oil_n']/s['p_gdp'], 1e-6)
        if ex.get('istate_mode', 'policy') == 'F4':
            s['rinv_state'] = np.exp(Lin(c['F4_pubinv'], ln_rev_oil=np.log(rev_oil_r)) + A_.get('rinv_state', 0))
        elif ex.get('oilrev_ref') is None:
            s['rinv_state'] = max(ex['istate_level'] + ex['istate_add'], 1e-6)
        else:
            resp = (rev_oil_r/max(ex['oilrev_ref'], 1e-6))**c['F4_pubinv']['ln_rev_oil']
            s['rinv_state'] = max(ex['istate_level']*resp + ex['istate_add'], 1e-6)
        s['rinv_non'] = np.exp(Lin(c['D2_inv'], ln_gdpnon=np.log(s['rgdpnon']), ln_inv_state=np.log(s['rinv_state']),
                                   ln_cred=np.log(s['rcred_tot'])) + A_.get('rinv_non', 0)
                               + ex.get('credit_overlay', 0.0)*(np.log(s['rcred_tot']) - ex.get('cred_ref', np.log(s['rcred_tot']))))
        s['rinv_tot'] = ex['rinv_oil'] + s['rinv_non']
        s['rinv_priv'] = max(s['rinv_tot'] - s['rinv_state'], 1e-6)
        if not freeze_capital:
            for sec in KSECT:
                s['K_'+sec] = (1-DELTA[sec])*prev['K_'+sec] + CAL['inv_share'][sec]*s['rinv_tot']
            s['K_non'] = (1-DELTA['tot'])*prev['K_non'] + s['rinv_non']
        s['rx_non'] = np.exp(Lin(c['D3_xnon'], ln_va_man=np.log(s['rva_man']), ln_va_agr=np.log(s['rva_agr']))
                             + np.log(ex['extdem']) + A_.get('rx_non', 0))
        s['rm_non'] = np.exp(Lin(c['D4_mnon'], ln_cons=np.log(s['rcons']), ln_inv_non=np.log(s['rinv_non']),
                                 ln_relprice=np.log(s['p_gdp']/(ex['fx']*100))) + A_.get('rm_non', 0))
        # ===== Block C: the eleven sectors plus the tax wedge =====
        tb = {sec: (tfp if sec in TFP_SECT else 0.0) for sec in SECT}
        s['rva_agr'] = np.exp(Lin(c['C1_agr'], ln_K_agr=np.log(s['K_agr']), trend=ex['trend'],
                                  trend_post2015=max(ex['trend'] - 15, 0.0)) + tb['agr'] + A_.get('rva_agr', 0))
        s['rva_man'] = np.exp(Lin(c['C3_man'], ln_K_man=np.log(s['K_man']), ln_va_con=np.log(s['rva_con']),
                                  ln_x_non=np.log(s['rx_non']), ln_va_agr=np.log(s['rva_agr']),
                                  ln_gdpnon=np.log(s['rgdpnon']), trend=ex['trend']) + tb['man'] + A_.get('rva_man', 0))
        s['rva_elc'] = np.exp(Lin(c['C4_elc'], ln_gdpnon=np.log(s['rgdpnon']), trend=ex['trend'])
                              + tb['elc'] + A_.get('rva_elc', 0))
        s['rva_wat'] = pop*np.exp(Lin(c['C5_wat'], ln_gdpnon_pc=np.log(s['rgdpnon'])-lpop, trend=ex['trend'])
                                  + tb['wat'] + A_.get('rva_wat', 0))
        s['rva_con'] = np.exp(Lin(c['C6_con'], ln_inv_state=np.log(s['rinv_state']), ln_inv_priv=np.log(s['rinv_priv']))
                              + A_.get('rva_con', 0))
        s['rva_trd'] = np.exp(Lin(c['C7_trd'], ln_cons=np.log(s['rcons'])) + A_.get('rva_trd', 0))
        s['rva_tou'] = pop*np.exp(Lin(c['C8_tou'], ln_hhdisp_pc=np.log(s['rhhdisp'])-lpop, trend=ex['trend'])
                                  + tb['tou'] + A_.get('rva_tou', 0))
        s['rva_tra'] = np.exp(Lin(c['C9_tra'], ln_gdpnon=np.log(s['rgdpnon']), trend=ex['trend'],
                                  ln_hc=np.log(ex['oil_prod'] + 0.9*ex['gas_prod'])) + tb['tra'] + A_.get('rva_tra', 0))
        s['rva_ict'] = pop*np.exp(Lin(c['C10_ict'], ln_K_ict_pc=np.log(s['K_ict'])-lpop, trend=ex['trend'])
                                  + tb['ict'] + A_.get('rva_ict', 0))
        s['rva_oth'] = pop*np.exp(Lin(c['C11_oth'], ln_hhdisp_pc=np.log(s['rhhdisp'])-lpop, trend=ex['trend'])
                                  + tb['oth'] + A_.get('rva_oth', 0))
        cm_nom = s['p_cons']*s['rcons']
        for k in MKT:
            a0, b1 = CAL['mkt_defl'][k]
            s['p_'+k] = prev['p_'+k]*np.exp((a0 + b1*s['infl'])/100)
            s['nom_'+k] = float(CAL['mkt_share'][k])*cm_nom
            s['r'+k if k != 'serv_hh' else 'rserv_hh'] = s['nom_'+k]/s['p_'+k]
            s['share_'+k] = float(CAL['mkt_share'][k])
        s['rva_nettax'] = np.exp(Lin(c['C12_nettax'], ln_cons=np.log(s['rcons']), ln_m_non=np.log(s['rm_non']))
                                 + A_.get('rva_nettax', 0))
        # ===== chain-linked aggregation =====
        wN = {k: prev['p_'+k]*prev['rva_'+k] for k in COMP}
        tot_all = sum(wN.values())
        g_all = sum((wN[k]/tot_all)*(s['rva_'+k]/prev['rva_'+k] - 1) for k in COMP)
        s['rgdp'] = prev['rgdp']*(1 + g_all)
        nm = [k for k in COMP if k != 'min']
        tot_non = sum(wN[k] for k in nm)
        g_non = sum((wN[k]/tot_non)*(s['rva_'+k]/prev['rva_'+k] - 1) for k in nm)
        s['rgdpnon'] = prev['rgdpnon']*(1 + g_non - CAL['nonoil_bias']/100)
        s['gdp_n'] = sum(s['p_'+k]*s['rva_'+k] for k in COMP)
        s['p_gdp'] = s['gdp_n']/s['rgdp']
        # ===== Block F: fiscal =====
        s['rev_oil_n'] = np.exp(Lin(c['F1_revoil'], ln_xoil_azn=np.log(s['x_g_oil_usd']*ex['fx'])) + A_.get('rev_oil_n', 0))
        s['rrev_nonoil'] = np.exp(Lin(c['F2_revnon'], ln_gdpnon=np.log(s['rgdpnon']), ln_m_non=np.log(s['rm_non']))
                                  + A_.get('rrev_nonoil', 0))
        s['rev_tot_n'] = s['rev_oil_n'] + s['rrev_nonoil']*s['p_gdp']
        s['rexp_cur'] = np.exp(Lin(c['F3_expcur'], ln_rev_r=np.log(s['rev_tot_n']/s['p_gdp']), ln_gdpnon=np.log(s['rgdpnon']))
                               + A_.get('rexp_cur', 0))
        s['rexp_soc'] = CAL['soc_share']*s['rexp_cur']
        s['exp_cap_n'] = CAL['capexp_ratio']*s['rinv_state']*s['p_inv']
        debt_serv = CAL['debtserv_ratio']*prev['debt_azn']
        s['exp_tot_n'] = s['rexp_cur']*s['p_gdp'] + s['exp_cap_n'] + debt_serv
        s['balance_n'] = s['rev_tot_n'] - s['exp_tot_n']
        s['debt_azn'] = prev['debt_azn'] - s['balance_n']
        s['debt_serv_n'] = debt_serv
        # ---- damped update and convergence test
        err = 0.0
        for k in ENDO:
            if not np.isfinite(s[k]): s[k] = old[k]
            o = old[k]
            if o is None or not np.isfinite(o): continue
            s[k] = damp*s[k] + (1-damp)*o
            err = max(err, abs(s[k]-o)/max(abs(o), 1e-6))
        if err < tol:
            s['pop'] = pop
            return s, it+1, err
    s['pop'] = pop
    return s, maxit, err
