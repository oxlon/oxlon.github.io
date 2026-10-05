"""FR5 engine self-test: run({}) for every scenario must reproduce the notebook's CSV outputs (rel. 1e-8)."""
from __future__ import annotations

import time

import pandas as pd

from . import base as B


def frames(res, S):
    s = B.result_to_frame(res)
    TK, LA, FY = S['TKEYS'], S['M']['LAST_ACT'], S['M']['FY']
    rows = []
    for y in s.index:
        rows.append(dict(year=int(y), type='TOTAL', volume_2015_prices=s.loc[y, 'fr5:vol:total'],
                         value_current=s.loc[y, 'fr5:val:total'], deflator=s.loc[y, 'fr5:defl:total'], share_pct=100.0,
                         volume_growth_pct=s.loc[y, 'fr5:volg:total']))
        for k in TK:
            rows.append(dict(year=int(y), type=k, volume_2015_prices=s.loc[y, f'fr5:vol:{k}'], value_current=s.loc[y, f'fr5:val:{k}'],
                             deflator=s.loc[y, f'fr5:defl:{k}'], share_pct=s.loc[y, f'fr5:sh:{k}'],
                             volume_growth_pct=s.loc[y, f'fr5:volg:{k}']))
    spl = pd.DataFrame({c: s[f'fr5:split:{c}']/(100 if c.endswith('_share') else 1) for c in
                        ['indiv_share', 'legal_share', 'state_share', 'nonstate_share', 'indiv_value', 'legal_value',
                         'state_value', 'nonstate_value']}).rename_axis('year').reset_index()
    H, n = FY[-1], len(FY)
    q, v = s.loc[H, 'fr5:vol:total'], s.loc[H, 'fr5:val:total']
    summ = dict(volume_2030=q, volume_growth_pa=((q/S['Q_LONG25'])**(1/n) - 1)*100, value_2030=v,
                value_growth_pa=((v/S['PSN25'])**(1/n) - 1)*100, volume_per_head_2030=s.loc[H, 'fr5:vol_pc'])
    tv = s[['fr5:vol:total']].rename(columns={'fr5:vol:total': 'v'}).rename_axis('year').reset_index()
    tn = s[['fr5:val:total']].rename(columns={'fr5:val:total': 'v'}).rename_axis('year').reset_index()
    return pd.DataFrame(rows), spl, summ, tv, tn


def selftest(tol=1e-8):
    from .fr5 import _st, _out, run
    S = _st()
    t0 = time.perf_counter()
    det, ok = {}, True
    for sc in S['M']['scenarios']:
        lg, spl, summ, tv, tn = frames(run({}, sc), S)
        g = lambda d, sc=sc: d[d.scenario == sc]  # noqa: E731
        r = {'long': B.selftest_compare(lg, _out(S['csv']['long']), ['volume_2015_prices', 'value_current', 'deflator',
                                                                      'share_pct', 'volume_growth_pct'], tol,
                                        on=['year', 'type'], csv_filter=g),
             'split': B.selftest_compare(spl, _out(S['csv']['split']), [c for c in spl.columns if c != 'year'], tol, on=['year'],
                                         csv_filter=g),
             'total_volume': B.selftest_compare(tv, _out(S['csv']['vol']), {'v': sc}, tol, on=['year'],
                                                csv_filter=lambda d: d.rename(columns={'Unnamed: 0': 'year'})),
             'total_value': B.selftest_compare(tn, _out(S['csv']['val']), {'v': sc}, tol, on=['year'],
                                               csv_filter=lambda d: d.rename(columns={'Unnamed: 0': 'year'})),
             'summary': B.selftest_compare(pd.DataFrame([dict(summ, scenario=sc)]), _out(S['csv']['summary']),
                                           list(summ), tol, on=['scenario'], csv_filter=g)}
        det[sc] = r
        ok = ok and all(v['ok'] for v in r.values())
    mx = max(v['max_rel_diff'] for r in det.values() for v in r.values())
    return {"ok": bool(ok), "max_rel_diff": mx, "seconds": round(time.perf_counter() - t0, 3), "detail": det}
