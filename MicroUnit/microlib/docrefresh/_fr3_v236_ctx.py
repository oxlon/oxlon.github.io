"""Derived FR3 v2.3.6 prose figures shared by the EN and AZ texts (all from _fr3_v236_vals.vals())."""
import numpy as np

from .common import csv, RefreshError
from ._fr3_v236_vals import HV, SC, ceil1, _coef

KEYS = ['w_avg', 'w_non', 'w_priv', 'w_state', 'w_oil']   # same order as HV


def ctx(V):
    C = {}
    s = V['sum'].set_index(['scenario', 'breakdown'])
    C['nom'], C['real'] = s.loc[('Baseline', 'average wage'), ['nominal_growth_avg_pct', 'real_growth_avg_pct']]
    for b in ['average wage', 'oil sector', 'non-oil sector', 'state sector', 'private sector']:
        for k in ['nominal_growth_avg_pct', 'real_growth_avg_pct']:
            g = [s.loc[(sc, b), k] for sc in ['Adverse', 'Baseline', 'Reform']]
            if not g[0] <= g[1] <= g[2]:
                raise RefreshError(f'FR3 doc: scenario ordering Adverse <= Baseline <= Reform fails for {b} ({k}) - '
                                   f'rewrite the §7 ordering sentence')
    h = V['ho']
    urw, ucg = h['U vs random walk'].values, h['U vs const growth'].values
    C['nrw'], C['ncg'] = int((urw < 1).sum()), int((ucg < 1).sum())
    C['mrw'], C['mcg'] = float(np.median(urw)), float(np.median(ucg))
    C['cg_not'] = [i for i in range(5) if ucg[i] >= 1]
    C['cg_worse'] = [i for i in range(5) if ucg[i] > 1 and h.DM_p_vs_cg.values[i] < 0.10]
    C['cg_better'] = [i for i in range(5) if ucg[i] < 1 and h.DM_p_vs_cg.values[i] < 0.10]
    C['avg'] = h.loc[HV[0]]
    C['oil'] = h.loc[HV[4]]
    C['anch'] = h.avg2018_20_anchor_RMSE.values
    ds = csv('FR3_wage_dataset.csv').set_index('year')
    prem = ds.w_oil / ds.w_non
    C['p20'], C['p25'] = prem.loc[2020], prem.loc[V['y0']]
    C['af'] = [V['af'][k] for k in ['FR3.E1_w_avg', 'FR3.E2_w_non', 'FR3.E3_w_priv', 'FR3.E4_w_state']]
    fc = V['fc']
    b = fc.loc['Baseline']
    y1, yN = int(b.index.min()), int(b.index.max())
    C['y1'], C['yN'] = y1, yN
    C['fac'] = {k: (b.loc[y1, f'factor_{k}'], b.loc[yN, f'factor_{k}']) for k in ['w_state', 'w_priv', 'w_non']}
    C['e1gap'] = ((b.loc[y1, 'factor_w_avg'] - 1) * 100, (b.loc[yN, 'factor_w_avg'] - 1) * 100)
    nc = V['now']
    C['ncgap'] = ceil1(max(abs(b.loc[y1, k] / nc.loc[k, 'nowcast'] - 1) * 100 for k in KEYS))
    C['mw26'] = b.loc[y1, 'minwage']
    C['mwg'] = [(fc.loc[(sc, y1 + 1), 'minwage'] / fc.loc[(sc, y1), 'minwage'] - 1) * 100 for sc in SC]
    C['prem26'] = b.loc[y1, 'prem_oil']
    C['premN'] = [fc.loc[(sc, yN), 'prem_oil'] for sc in SC]
    C['wb1'], C['wbN'] = b.loc[y1, 'wagebill'], b.loc[yN, 'wagebill']
    C['wbg'] = (C['wb1'] / V['wb0'] - 1) * 100
    C['wg1'] = (b.loc[y1, 'w_avg'] / ds.loc[V['y0'], 'w_avg'] - 1) * 100
    rat = {sc: fc.loc[sc, 'w_state'] / fc.loc[sc, 'w_priv'] for sc in SC}
    C['rat'] = (rat['Baseline'].loc[y1], rat['Baseline'].loc[yN], rat['Adverse'].loc[yN], rat['Reform'].loc[yN])
    rb = rat['Baseline'].round(2)
    cross = [y for y in rb.index[1:] if (rb.loc[y - 1] - 1) * (rb.loc[y] - 1) < 0 or (rb.loc[y - 1] < 1 <= rb.loc[y])]
    C['cross'] = cross[0] if cross else None
    g = V['fr1gap']
    C['fr1'] = (g[('Baseline', y1)], g[('Baseline', yN)], min(g.values()), max(g.values()))
    hw = V['hw']
    C['hw'] = {k: (hw.loc[k, y1], hw.loc[k, y1 + 1:yN].min(), hw.loc[k, y1 + 1:yN].max()) for k in ['w_avg', 'w_state', 'w_priv']}
    C['rmse'] = dict(zip(KEYS, h.model_RMSE.values))
    S = V['sens']
    c3 = [x for x in S.columns if 'E3 unrestricted' in x][0]
    C['e3u_priv'], C['main_priv'] = S.loc['private sector', c3], S.loc['private sector', S.columns[0]]
    if any(p < 0.05 for p in V['eg'].values()):
        raise RefreshError('FR3 doc: an EG test now establishes cointegration - rewrite §5 / limitation 6 by hand')
    hb = {(r['eq'], r['drivers']): r for r in V['hb_rows']}
    if hb[('E3', 'prod_non')]['HAC-F p (<=2020)'] >= 0.05:
        raise RefreshError('FR3 doc: E3 homogeneity no longer rejected - rewrite §3.1 decision / limitation 7 by hand')
    C['e3u'] = _coef(V['R']['FR3.S_E3_unrestricted'], 'ln_cpi')['coef']
    return C
