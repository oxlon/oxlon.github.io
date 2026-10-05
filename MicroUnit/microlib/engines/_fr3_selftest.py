"""FR3 engine self-test: run({}) for every scenario must reproduce the notebook's CSV outputs (rel. 1e-8)."""
from __future__ import annotations

import pandas as pd

from . import base as B


def _ren(d):
    return d.rename(columns={'Unnamed: 0': 'scenario', 'Unnamed: 1': 'year'})


def frames(res):
    """Engine result -> frames shaped like the notebook CSVs (via the indicator ids)."""
    from .fr3 import _st
    S = _st()
    s = B.result_to_frame(res)
    full_cols = [c[4:] for c in s.columns if c.startswith('fr3:') and ':' not in c[4:]
                 and not c.endswith('_g') and c not in ('fr3:prem_sp', 'fr3:w_budget', 'fr3:w_nonbudget')]
    full = s[[f'fr3:{c}' for c in full_cols]].rename(columns=lambda c: c[4:]).rename_axis('year').reset_index()
    br = s[[f'fr3:brw:{c}' for c in S['branch']['code']]]
    br.columns = S['branch']['names']
    br = br.rename_axis('year').reset_index()
    se = s[[f'fr3:emp:{k}' for k in S['SEC8']]]
    se.columns = S['SEC8']
    se = se.rename_axis('year').reset_index()
    acc, summ = [], []
    LA = S['M']['LAST_ACT']; H = S['M']['H_END']; n = len(S['M']['FY'])
    for k, lbl in S['WAGE_SERIES'].items():
        for y in s.index:
            acc.append(dict(breakdown=lbl, year=int(y), nominal=s.loc[y, f'fr3:{k}'], real=s.loc[y, f'fr3:r{k}'],
                            nominal_growth_pct=s.loc[y, f'fr3:{k}_g'], real_growth_pct=s.loc[y, f'fr3:r{k}_g']))
        n0, n1 = S['W25'][k], s.loc[H, f'fr3:{k}']
        r0, r1 = n0/S['W25']['cpi']*100, n1/s.loc[H, 'fr3:cpi']*100
        summ.append(dict(breakdown=lbl, nominal_2025=n0, nominal_2030=n1, nominal_growth_avg_pct=((n1/n0)**(1/n)-1)*100,
                         real_2025=r0, real_2030=r1, real_growth_avg_pct=((r1/r0)**(1/n)-1)*100,
                         cumulative_nominal_pct=(n1/n0-1)*100))
    sw = None
    if S.get('SW'):                                        # v2.2 sector and budget / non-budget wages
        cols = list(S['SW']['sectors']) + ['budget', 'nonbudget']
        sw = pd.DataFrame({c: s[f'fr3:sw:{c}'] if c in S['SW']['sectors'] else s[f'fr3:w_{c}'] for c in cols})
        sw = sw.rename_axis('year').reset_index()
    return dict(full=(full, full_cols), branch=br, sector=se, accounts=pd.DataFrame(acc), summary=pd.DataFrame(summ),
                sector_wages=sw), LA


def selftest(tol=1e-8):
    from .fr3 import _st, _out, run
    import time
    S = _st()
    t0 = time.perf_counter()
    det, ok = {}, True
    for sc in S['M']['scenarios']:
        fr, _ = frames(run({}, sc))
        full, cols = fr['full']
        f = lambda d, sc=sc: _ren(d)[lambda x: x.scenario == sc]  # noqa: E731
        g = lambda d, sc=sc: d[d.scenario == sc]  # noqa: E731
        r = {'full': B.selftest_compare(full, _out(S['csv']['full']), cols, tol, on=['year'], csv_filter=f),
             'branch': B.selftest_compare(fr['branch'], _out(S['csv']['branch']), list(S['branch']['names']), tol,
                                          on=['year'], csv_filter=f),
             'sector': B.selftest_compare(fr['sector'], _out(S['csv']['sector']), list(S['SEC8']), tol, on=['year'],
                                          csv_filter=f),
             'accounts': B.selftest_compare(fr['accounts'], _out(S['csv']['accounts']),
                                            ['nominal', 'real', 'nominal_growth_pct', 'real_growth_pct'], tol,
                                            on=['breakdown', 'year'], csv_filter=g),
             'summary': B.selftest_compare(fr['summary'], _out(S['csv']['summary']),
                                           ['nominal_2025', 'nominal_2030', 'nominal_growth_avg_pct', 'real_2025',
                                            'real_2030', 'real_growth_avg_pct', 'cumulative_nominal_pct'], tol,
                                           on=['breakdown'], csv_filter=g)}
        if fr.get('sector_wages') is not None:
            FY = [int(y) for y in S['M']['FY']]
            r['sector_wages'] = B.selftest_compare(
                fr['sector_wages'], _out(S['csv']['sector_wages']), list(S['SW']['sectors']) + ['budget', 'nonbudget'], tol,
                on=['year'], csv_filter=lambda d, sc=sc, FY=FY: d[(d.scenario == sc) & d.year.isin(FY)])
        u = run({'levers': {'branch_anchor': False}}, sc)
        bu = frames(u)[0]['branch']
        r['branch_unanchored'] = B.selftest_compare(bu, _out(S['csv']['branch_unanchored']), list(S['branch']['names']), tol,
                                                    on=['year'], csv_filter=f)
        det[sc] = r
        ok = ok and all(v['ok'] for v in r.values())
    mx = max(v['max_rel_diff'] for r in det.values() for v in r.values())
    return {"ok": bool(ok), "max_rel_diff": mx, "seconds": round(time.perf_counter() - t0, 3), "detail": det}
