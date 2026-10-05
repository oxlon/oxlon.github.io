"""FR3 solver core: a faithful port of FR3.ipynb Parts 13-17 (wage block).

    xrow / predict_ln_nominal   homogeneity form: real form = ln(W/P) on real drivers, nominal drivers deflated
    eq_values                   the four forecasting equations, recursive order E4 -> E1 -> E2 -> E3
    reconcile                   joint WLS (Stone) reconciliation of the institutional and oil/non-oil identities
    solve_year                  one year: equations -> reconciliation -> reported columns (notebook order)
    build_ex / run_wage_forecast  scenario drivers and the forward solve with the 2026 nowcast increment
                                decaying with a half-life (base add-factor = own 2025 residual, held)
    sector_employment / branch_wages  Part 16-17 blocks (branch adding-up over all 29 branches, v2 fix)
Only numpy/pandas; every formula is the notebook's own (copied, not re-derived)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def xname(r, form, REAL_DRV):
    if r in REAL_DRV:
        return 'ln_' + r
    return ('ln_r' + r.replace('w_', 'w_')) if form == 'real' else 'ln_' + r


def xrow(spec, drv, REAL_DRV, NOM_DRV):
    form, x = spec['form'], {}
    for r in spec['regs']:
        if r in REAL_DRV:
            x[xname(r, form, REAL_DRV)] = np.log(drv[REAL_DRV[r]])
        else:
            v = drv[NOM_DRV[r]]
            x[xname(r, form, REAL_DRV)] = np.log(v/drv['cpi']*100) if form == 'real' else np.log(v)
    if form == 'nominal':
        x['ln_cpi'] = np.log(drv['cpi'])
    for d in spec.get('dummies', ()):
        x[d] = drv.get(d, 1.0)
    return x


def predict_ln_nominal(spec, coef, drv, addf, REAL_DRV, NOM_DRV):
    x = xrow(spec, drv, REAL_DRV, NOM_DRV)
    v = coef['const'] + sum(coef[k]*x[k] for k in x) + addf
    if spec['dep'] == 'rel_priv':
        return np.log(drv['w_state']) + v
    return v + (np.log(drv['cpi']/100) if spec['form'] == 'real' else 0.0)


def eq_values(S, drv, coefs, addf):
    d, out = dict(drv), {}
    for nm in S['FC_EQS']:
        k = S['VAR_OF'][nm]
        out[k] = float(np.exp(predict_ln_nominal(S['SPEC'][nm], coefs[nm], d, addf.get(nm, 0.0),
                                                 S['REAL_DRV'], S['NOM_DRV'])))
        d[k] = out[k]
    return out


def reconcile(x0, sh, kap, prem, var, tol=1e-13):
    keys = ['w_avg', 'w_state', 'w_priv', 'w_non']
    z0 = np.log(np.array([x0[k] for k in keys])); z = z0.copy()
    V = np.diag([max(var[k], 1e-14) for k in keys])
    c2 = -np.log(kap['k2']*(sh['s_oil']*prem + 1 - sh['s_oil']))
    for _ in range(100):
        es, ep = sh['s_state']*np.exp(z[1]), sh['s_priv']*np.exp(z[2])
        g1 = z[0] - np.log(kap['k1']) - np.log(es + ep); g2 = z[3] - z[0] - c2
        if max(abs(g1), abs(g2)) < tol:
            break
        R = np.array([[1, -es/(es+ep), -ep/(es+ep), 0], [-1, 0, 0, 1]])
        b = R @ z - np.array([g1, g2])
        z = z0 + V @ R.T @ np.linalg.solve(R @ V @ R.T, b - R @ z0)
    out = dict(zip(keys, np.exp(z)))
    out['w_oil'] = prem*out['w_non']
    fac = {k: out[k]/x0[k] for k in keys}
    return out, fac


def solve_year(S, drv, coefs, addf, sh, kap, prem, var):
    x0 = eq_values(S, drv, coefs, addf)
    rec, fac = reconcile(x0, sh, kap, prem, var)
    s = dict(rec)
    for k in ['w_avg', 'w_non', 'w_priv', 'w_state']:
        s[k+'_unbalanced'] = x0[k]; s['factor_'+k] = fac[k]
    s['prem_oil'] = prem
    s['w_avg_from_parts'] = kap['k1']*(sh['s_state']*s['w_state'] + sh['s_priv']*s['w_priv'])
    s['agg_gap_pct'] = (s['w_avg_from_parts']/s['w_avg'] - 1)*100
    s['w_avg_from_oil_split'] = kap['k2']*(sh['s_oil']*s['w_oil'] + (1-sh['s_oil'])*s['w_non'])
    s['oil_split_gap_pct'] = (s['w_avg_from_oil_split']/s['w_avg'] - 1)*100
    for k in ['avg', 'non', 'priv', 'state', 'oil']:
        s['rw_'+k] = s['w_'+k]/drv['cpi']*100
    return s


def base_addf(S, coefs):
    '''Own 2025 long-run residual of each equation (contract decision 4), for any coefficient set.'''
    out = {}
    for nm in S['FC_EQS']:
        h, c = S['H25'][nm], coefs[nm]
        out[nm] = float(h['y'] - (c['const'] + sum(c[k]*h['x'][k] for k in list(c.index[1:]))))
    return out


def build_ex(S, fc, mw_growth, prem_target):
    '''fc: DataFrame indexed by year with the FR1 columns; mw_growth: list of 5 rates (fractions).'''
    M, W25 = S['M'], S['W25']
    ex, mw = {}, float(W25['minwage'])
    hired0, emp0 = float(W25['hired_dvx']), float(W25['emp_tot'])
    sh = S['SH25']
    for i, y in enumerate(M['FY']):
        mw *= (1 + mw_growth[i])
        emp_t = float(fc.loc[y, 'emp'])
        hired = hired0*emp_t/emp0
        ex[y] = dict(cpi=float(fc.loc[y, 'cpi']), prod_tot=float(fc.loc[y, 'rgdp'])/emp_t,
                     prod_non=float(fc.loc[y, 'rgdpnon'])/(emp_t*(1 - S['OIL_EMP_SHARE'])),
                     exp_per_emp=float(fc.loc[y, 'rexp_cur'])/emp_t, minwage=mw, D18=1.0, hired=hired,
                     e_state=hired*sh['s_state']*(1-sh['s_oil']), e_nonstate=hired*sh['s_priv']*(1-sh['s_oil']),
                     prem_target=prem_target, year=y, i=i)
    return ex


def run_wage_forecast(S, ex, coefs, var, nowcast, half_life, prem_path=None):
    '''Notebook run_wage_forecast (main path): base add-factor held, nowcast increment full in 2026 and
    x 0.5^((y-2026)/half_life) after; premium glides linearly from the 2026 nowcast premium to the target
    unless an explicit path is given.'''
    M = S['M']; FY3, NY = M['FY'], M['NOWCAST_Y']
    base = base_addf(S, coefs)
    EQ_OF3 = {v: k for k, v in S['VAR_OF'].items()}

    def addf_at(y, inc):
        return {nm: base[nm]*1.0 + inc.get(nm, 0.0)*0.5**((y-NY)/half_life) for nm in S['FC_EQS']}
    x0 = eq_values(S, ex[NY], coefs, addf_at(NY, {}))
    inc = {EQ_OF3[k]: float(np.log(nowcast[k]/x0[k])) for k in EQ_OF3}
    prem_start = nowcast['w_oil']/nowcast['w_non']
    out = {}
    for j, y in enumerate(FY3):
        if prem_path is not None:
            prem_y = float(prem_path[j])
        elif y == FY3[0]:
            prem_y = prem_start
        else:
            prem_y = prem_start + (ex[y]['prem_target'] - prem_start)*(y - FY3[0])/max(len(FY3)-1, 1)
        sol = solve_year(S, ex[y], coefs, addf_at(y, inc), S['SH25'], S['KAP25'], prem_y, var)
        sol['balance_factor'] = sol['factor_w_priv']
        sol['wagebill'] = sol['w_avg']*ex[y]['hired']*12/1000
        sol['minwage'] = ex[y]['minwage']; sol['cpi'] = ex[y]['cpi']
        sol['hired'] = ex[y]['hired']; sol['kaitz'] = ex[y]['minwage']/sol['w_avg']
        for nm in S['FC_EQS']:
            sol['nowcast_incr_'+S['VAR_OF'][nm]] = inc[nm]*0.5**((y-NY)/half_life)
        out[y] = sol
    return pd.DataFrame(out).T, inc


def sector_employment(S, fc, hired, emp_el):
    SEC8 = S['SEC8']
    gva_f = pd.DataFrame({'ind': fc.rva_min+fc.rva_man+fc.rva_elc+fc.rva_wat, 'agr': fc.rva_agr,
                          'con': fc.rva_con, 'trd': fc.rva_trd, 'tou': fc.rva_tou,
                          'tra': fc.rva_tra, 'ict': fc.rva_ict, 'oth': fc.rva_oth})
    base_e, base_g = pd.Series(S['base_e']), pd.Series(S['base_g'])
    raw = pd.DataFrame({k: base_e[k]*(gva_f[k]/base_g[k])**emp_el for k in SEC8})
    tot = pd.Series(hired)
    return raw.div(raw.sum(axis=1), axis=0).mul(tot, axis=0), gva_f


def branch_wages(S, fc3, gva_f, emp_ind, beta, anchor=True):
    '''Part 17 (v2). anchor=True (baseline): each value-added branch keeps its own 2025 residual from the between
    relation (add-factor convention), so with no branch-specific productivity path every branch grows at the
    industry-wage rate; anchor=False (labelled sensitivity): productivity-implied relative wages. Branches without
    value added keep their 2025 relative wage; the adding-up over all branches is exact in both.'''
    b = S['branch']
    br_w0 = pd.Series(b['w0'], index=b['names']); br_e0 = pd.Series(b['e0'], index=b['names'])
    br_p0 = pd.Series(b['p0'], index=b['names'], dtype=float)
    nova = list(b['nova'])
    w_ind_0 = S['w_ind_0']; w_non25 = S['W25']['w_non']
    gva_ind0 = float(S['base_g']['ind'])
    rel_nova0 = br_w0[nova]/w_ind_0
    E = float(br_e0.sum())
    rel0 = (br_p0/br_p0.mean())**beta
    k0 = (w_ind_0*E - float((br_w0[nova]*br_e0[nova]).sum()))/(rel0*br_e0).sum()
    U = np.log(br_w0/(rel0*k0))
    rows = {}
    for y in S['M']['FY']:
        gscale = (float(gva_f['ind'][y])/gva_ind0)/(float(emp_ind[y])/float(br_e0.sum()))
        rel = (br_p0*gscale/br_p0.mean())**beta
        if anchor:
            rel = rel*np.exp(U)
        w_ind_y = fc3.w_non[y]*(w_ind_0/w_non25)
        w_nova = rel_nova0*w_ind_y
        k = (w_ind_y*E - float((w_nova*br_e0[nova]).sum()))/(rel*br_e0).sum()
        row = rel*k
        row[nova] = w_nova
        rows[y] = row
    return pd.DataFrame(rows).T
