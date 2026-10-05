"""FR5 solver core: a faithful port of FR5.ipynb Part 14 (`drivers`, `type_relp`, `predict_shares`, `split_share`,
`solve`). Block-recursive: E1 (volume per head on real income per head and the relative price of services, anchored on
2025) -> value by identity -> 13 multinomial-logit budget shares -> value / volume by type -> institutional splits."""
from __future__ import annotations

import numpy as np
import pandas as pd


def drivers(S, fc, pop_fc=None):
    """fc: DataFrame indexed by forecast year with rhhdisp, p_serv_hh, p_cons, pop (FR1 columns)."""
    M, F25 = S['M'], S['F25']
    yrs = [M['LAST_ACT']] + M['FY']
    ydp, pse, relp, pp = {}, {}, {}, {}
    for y in yrs:
        src = F25 if y == M['LAST_ACT'] else fc.loc[y]
        ydp[y] = float(src['rhhdisp'])
        pse[y] = float(src['p_serv_hh'])*100.0
        relp[y] = float(np.log(pse[y]/(float(src['p_cons'])*100)))
        if y == M['LAST_ACT']:
            pp[y] = float(S['pop25'])
        elif M['HAS_POP']:
            pp[y] = float(fc.loc[y, 'pop'])
        else:
            pp[y] = float(S['pop25'])*(1 + S['M']['POP_G'])**(y - M['LAST_ACT'])
    return dict(yd=pd.Series(ydp), p_serv=pd.Series(pse), relp=pd.Series(relp), pop=pd.Series(pp))


def type_relp(S, rule, years):
    out = {}
    LA = S['M']['LAST_ACT']
    for k in S['TKEYS']:
        r25, dr = S['RELP25'][k], S['DRIFT'][k]
        s = {}
        for y in years:
            h = int(y) - LA
            if h <= 0:
                s[y] = r25 if y == LA else np.nan
                continue
            if rule == 'constant':
                s[y] = r25
            elif rule == 'drift':
                s[y] = r25 + dr*sum(0.5**j for j in range(h))
            elif rule == 'admin':
                s[y] = r25 + (np.log(1.02)*h if k in S['ADMIN'] else 0.0)
            else:
                raise ValueError(f"price_rule '{rule}'")
        out[k] = pd.Series(s)
    return out


def e1_core(c, ydpc, relp, years):
    return c['const'] + c['eta']*ydpc + c['eps']*relp + c['tr']*(pd.Series(years, index=years) - 2000.)


def predict_shares(S, sysp, years, x, rp, zshift=None):
    REF = S['REF']
    z = {}
    for k in S['TKEYS']:
        p = sysp[k]
        if p['mode'] == 'reference':
            z[k] = pd.Series(0.0, index=years); continue
        if p['mode'] == 'const':
            z[k] = pd.Series(p['const'], index=years); continue
        X = pd.DataFrame({'x': x.reindex(years), 'p': (rp[k] - rp[REF]).reindex(years)}, index=years)
        z[k] = p['const'] + p['addf'] + sum(p['b'][n]*X[n] for n in p['b'])
    Z = pd.DataFrame(z, index=years)[S['TKEYS']]
    if zshift is not None:
        Z = Z + zshift.reindex(index=years, columns=S['TKEYS']).fillna(0.0)
    e = np.exp(Z)
    return e.div(e.sum(axis=1), axis=0)


def split_share(p, ydpc_path, years, addf_shift=None):
    if p['lr'] is None:
        z = pd.Series(p['const'], index=years)
    else:
        X = pd.DataFrame({'income': ydpc_path.reindex(years), 'trend': pd.Series(np.array(years) - 2000., index=years),
                          'c20': 0.0, 'c21': 0.0}, index=years)
        z = p['lr']['const'] + sum(p['lr'][c]*X[c] for c in p['icols'] + p['dcols'] if c in X) + p['addf']
    if addf_shift is not None:
        z = z + addf_shift.reindex(years).fillna(0.0)
    return 1/(1 + np.exp(-z))


def addf_decay_factor(h, half_life=1.0):
    """notebook `addf_decay_factor` (v2.3): FIXED add-factor decay 0.5 ** (h / half-life); no estimated residual rho."""
    return 0.5 ** (h / float(half_life))


def solve(S, dd, c, sysp, rp, relp_lever=0.0, pop_override=None, addf_decay=False, half_life=1.0):
    """The notebook's solve() for years = FC_YEARS with resolved inputs (no bootstrap shocks)."""
    M = S['M']; LA = M['LAST_ACT']; years = list(M['FY']); TK = S['TKEYS']
    pp = dd['pop'] if pop_override is None else pop_override
    _y0 = pd.Series([np.log(dd['yd'].loc[LA]/pp.loc[LA])], index=[LA])
    a1 = float(S['QPC25'] - e1_core(c, _y0, dd['relp'].loc[[LA]], [LA]).iloc[0])
    ydpc = np.log(dd['yd'].reindex(years)/pp.reindex(years))
    relp = dd['relp'].reindex(years) + relp_lever*(pd.Series(years, index=years) > LA)
    h = pd.Series([max(int(y) - LA, 0) for y in years], index=years)
    dfac = addf_decay_factor(h, half_life) if addf_decay else None
    a1_path = a1*(dfac if addf_decay else 1.0)
    qpc = a1_path + e1_core(c, ydpc, relp, years)
    Q = np.exp(qpc)*pp.reindex(years)
    P = dd['p_serv'].reindex(years)*np.exp(relp - dd['relp'].reindex(years))
    NOM = Q*P/100.0
    zs = pd.DataFrame(0.0, index=years, columns=TK)
    if addf_decay:
        for k in TK:
            p = sysp[k]
            if p['mode'] not in ('reference', 'const') and p.get('decays'):
                zs[k] = p['addf']*(dfac - 1.0)
    SH = predict_shares(S, sysp, years, qpc, rp, zshift=zs)
    nom_t = SH.mul(NOM, axis=0)
    pt = pd.DataFrame({k: P*np.exp(rp[k].reindex(years)) for k in TK}, index=years)
    q_t = nom_t/pt*100.0
    ydpc_full = pd.concat([pd.Series(S['YDPC_hist']), ydpc])
    spl = {}
    for nm, p in S['SPL'].items():
        sh_ = pd.Series(0.0, index=years)
        if addf_decay and p['lr'] is not None:
            sh_ = sh_ + p['addf']*(dfac - 1.0)
        spl[nm] = split_share(p, ydpc_full, years, addf_shift=sh_)
    SPLIT = pd.DataFrame({'indiv_share': spl['indiv'], 'legal_share': 1 - spl['indiv'],
                          'state_share': spl['state'], 'nonstate_share': 1 - spl['state']}, index=years)
    for a_, b_ in [('indiv', 'indiv_share'), ('legal', 'legal_share'), ('state', 'state_share'), ('nonstate', 'nonstate_share')]:
        SPLIT[f'{a_}_value'] = SPLIT[b_]*NOM
    return dict(Q=Q, P=P, NOM=NOM, SH=SH, nom_t=nom_t, q_t=q_t, p_t=pt, qpc=qpc, SPLIT=SPLIT, pop=pp.reindex(years))
