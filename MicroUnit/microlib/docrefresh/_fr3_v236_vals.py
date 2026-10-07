"""FR3 v2.3.6 doc figures: every run-dependent number of the FR3 methodology text, read from the FR3 outputs.

Marker names start with 'fr3v236_' (the FR3 notebook itself owns the AUTO:v2 block and captures 'AUTO:v2...')."""
import math
import re

import numpy as np

from .common import csv, registry, RefreshError

HV = ['average wage', 'non-oil wage', 'private wage', 'state wage', 'oil wage (non-oil x premium lever)']
SC = ['Baseline', 'Adverse', 'Reform']


def _coef(e, name):
    for c in e['coefficients']:
        if c['name'] == name:
            return c
    raise RefreshError(f"{e['id']}: no coefficient {name}")


def _rx(pat, s, n=1):
    m = re.search(pat, s)
    if not m:
        raise RefreshError(f"FR3 doc figures: pattern {pat!r} not found in {s[:120]!r}")
    return [float(m.group(i + 1)) for i in range(n)]


def vals():
    R, _ = registry('FR3')
    V = {}
    # 3.1 homogeneity / break tests
    hb = csv('FR3_homogeneity_break_tests.csv')
    V['hb_rows'] = hb.to_dict('records')
    # 3.4 minimum-wage elasticities (credible variants = not weak IV)
    mw = csv('FR3_minimum_wage_elasticities.csv')
    ok = mw[~mw.weak_iv.astype(bool)]
    V['mw_rng'] = {e: (g.mw_coef.min(), g.mw_coef.max()) for e, g in ok.groupby('eq')}
    V['mw_dols'] = {e: float(g[g.variant == 'DOLS long run'].mw_coef.iloc[0]) for e, g in mw.groupby('eq')}
    V['mw_dols_d18'] = {e: (float(g[g.variant == 'DOLS long run + D18'].mw_coef.iloc[0]),
                            float(g[g.variant == 'DOLS long run + D18'].se.iloc[0])) for e, g in mw.groupby('eq')}
    iv = mw[mw.variant.str.startswith('2SLS')]
    strong, weak = iv[~iv.weak_iv.astype(bool)], iv[iv.weak_iv.astype(bool)]
    V['iv_strongF'] = (strong.first_stage_F.min(), strong.first_stage_F.max(), len(strong))
    V['iv_weakF'] = (weak.first_stage_F.min(), weak.first_stage_F.max())
    rej = strong[strong.DWH_p < 0.05]
    V['dwh'] = [(r.eq, r.DWH_p) for r in rej.itertuples()]
    V['sys3_e4'] = _coef(R['FR3.SYS3_E4_w_state'], 'ln_rmw')['coef']
    V['d18_e4'] = _coef(R['FR3.S_E4_D18'], 'D18')['coef']
    p1 = R['FR3.P1_minwage']
    V['p1'] = _coef(p1, 'ln_w_avg')['coef']
    # 4 selection
    V['sel'] = csv('FR3_specification_selection.csv')
    # rejected specifications (evidence strings written by the notebook)
    rs = csv('FR3_rejected_specifications.csv').set_index('what')
    ev = rs.loc['Minimum wage in the PRIVATE wage equation', 'evidence']
    V['sel_e3_ev'] = ev
    V['e3mw_rmse'] = _rx(r'RMSE ([\d.]+) vs ([\d.]+).*?DM p=([\d.]+)', ev, 3)
    V['e3mw_lev'] = _rx(r'level ([-+\d.]+); diff-form ([-+\d.]+) \(p=([\d.]+)\); with D18 ([-+\d.]+) \(p=([\d.]+)\)', ev, 5)
    ev = rs.loc['Private-wage spillover into state-sector pay', 'evidence']
    V['spill_sp'] = _rx(r'term ([-+\d.]+) \(p=([\d.]+)\)', ev, 2)
    # 5 equations
    V['R'] = R
    V['eg'] = {k: R[k]['diagnostics']['eg_coint_p'] for k in
               ['FR3.E1_w_avg', 'FR3.E2_w_non', 'FR3.E3_w_priv', 'FR3.E4_w_state', 'FR3.E5_w_oil']}
    gh = [R[k]['restrictions'][0] for k in ['FR3.GH_E1_w_avg', 'FR3.GH_E2_w_non', 'FR3.GH_E3_w_priv', 'FR3.GH_E4_w_state']]
    if any(g['verdict_en'] != 'not established' for g in gh):
        raise RefreshError('FR3: a Gregory-Hansen test now establishes cointegration - rewrite §3.2 by hand')
    V['gh'] = (min(g['stat'] for g in gh), max(g['stat'] for g in gh), sorted({g['cv_5'] for g in gh}))
    s4o, s4i = R['FR3.SYS_E4_OLS'], R['FR3.SYS_E4_2SLS']
    s5o, s5i = R['FR3.SYS_E5_OLS'], R['FR3.SYS_E5_2SLS']
    V['sim'] = dict(e4o=_coef(s4o, 'ln_rmw')['coef'], e4i=_coef(s4i, 'ln_rmw')['coef'],
                    e4F=s4i['diagnostics']['first_stage_F']['ln_rmw'], e4s=s4i['diagnostics']['sargan_p'],
                    e5o=_coef(s5o, 'ln_w_non')['coef'], e5i=_coef(s5i, 'ln_w_non')['coef'],
                    e5s=s5i['diagnostics']['sargan_p'])
    V['af'] = {k: R[k]['fitted']['resid'][-1] for k in ['FR3.E1_w_avg', 'FR3.E2_w_non', 'FR3.E3_w_priv', 'FR3.E4_w_state']}
    # 6 hold-out, nowcast
    V['ho'] = csv('FR3_holdout_validation.csv').set_index('variable').loc[HV]
    V['now'] = csv('FR3_nowcast_2026.csv').set_index('key')
    # 7 results
    V['sum'] = csv('FR3_wage_summary.csv')
    fc = csv('FR3_wage_forecast_full.csv').rename(columns={'Unnamed: 0': 'scenario', 'Unnamed: 1': 'year'})
    V['fc'] = fc.set_index(['scenario', 'year'])
    ds = csv('FR3_wage_dataset.csv').set_index('year')
    y0 = int(fc.year.min()) - 1
    b = V['fc'].loc['Baseline']
    wb0 = ds.loc[y0, 'w_avg'] * ds.loc[y0, 'hired'] * 12 / 1000
    chk = b.loc[y0 + 1, 'w_avg'] * b.loc[y0 + 1, 'hired'] * 12 / 1000
    if abs(chk / b.loc[y0 + 1, 'wagebill'] - 1) > 1e-6:
        raise RefreshError('FR3: wage-bill identity (w_avg x hired x 12) no longer reproduces the forecast column')
    V['y0'], V['wb0'] = y0, wb0
    V['sens'] = csv('FR3_forecast_sensitivity.csv', index_col=0)
    fan = csv('FR3_fan_wages.csv')
    V['fan'] = fan[fan.sources == 'all']
    own = fan[(fan.sources != 'all') & (fan.measure == 'level')].copy()
    own['hw'] = (np.log(own.q95) - np.log(own.q05)) / 2 * 100
    V['hw'] = own.pivot_table(index='variable', columns='year', values='hw')
    # FR1's own wage column
    t = csv('FR1_forecast_tidy.csv')
    w1 = t[t.id == 'fr1:wage'].set_index(['scenario', 'year'])['value']
    V['fr1gap'] = {(s, y): (fc.set_index(['scenario', 'year']).loc[(s, y), 'w_avg'] / w1.loc[(s, y)] - 1) * 100
                   for s in SC for y in sorted(fc.year.unique())}
    return V


def ceil1(x):
    return math.ceil(x * 10 - 1e-9) / 10
