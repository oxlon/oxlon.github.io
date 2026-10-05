"""FR5 scenario engine (contract section B): paid services rendered to the population — total volume and value,
volume per head, the 13 service types (volume, value, share, deflator) and the two institutional splits; the
notebook's Part 14 solve, ported in _fr5_core.

    inputs()            exogenous: FR1 paths fr1:rhhdisp, fr1:p_cons, fr1:p_serv_hh, fr1:pop (2026-2030) and the 13 type
                        relative-price paths relp:<type>; coefficients: E1 eta / epsilon and the 12 shrunk Engel slopes
                        (value, SE, 95% CI from FR5_equations.json); levers (below)
    run(overrides, scenario, upstream=None)  upstream = {"FR1": result} replaces the FR1 paths (else FR1_forecast_full.csv)
    selftest()          run({}) per scenario reproduces FR5_forecast_long / institutional_split / total_volume /
                        total_value / scenario_summary (rel. 1e-8)
Levers: price_rule ('constant' | 'drift' | 'admin'), e1_spec ('chosen' | 'difference' | alternative specifications),
relp_shift_pct (services relative price, %), pop_growth_shift_pp, addf_decay (bool; sensitivity only, baseline False =
constant add-factors) and addf_half_life (years, default 1: FIXED decay 0.5 ** (h / half-life); v2.3 — no estimated
residual-AR coefficient)."""
from __future__ import annotations

import copy
import time

import numpy as np
import pandas as pd

from . import base as B
from . import _fr5_core as C
from ._fr3_selftest import _ren  # noqa: F401  (shared helper)
from .fr3 import _read_csv, _out  # CSV reader with retries (output/), shared with FR3

MODULE = "FR5"
_S = None
FR1C = ['rhhdisp', 'p_cons', 'p_serv_hh', 'pop']


def _st():
    global _S
    if _S is None:
        S = B.load_state(MODULE)
        S['M']['FY'] = [int(y) for y in S['M']['FY']]
        S['YDPC_hist'] = {int(k): float(v) for k, v in S['YDPC_hist'].items()}
        _S = S
    return _S


def reload():
    global _S
    _S = None
    return _st()


def _fr1_base(scenario, upstream, W):
    S = _st(); FY = S['M']['FY']
    fc = _read_csv(S['csv']['fr1'])
    fc = fc.rename(columns={'Unnamed: 0': 'year'})
    fc = fc[fc.scenario == scenario].set_index('year')
    fc.index = fc.index.astype(int)
    out = pd.DataFrame(index=FY, columns=FR1C, dtype=float)
    ser = (((upstream or {}).get('FR1') or {}).get('series')) or {}
    miss = []
    for c in FR1C:
        d = ser.get(f'fr1:{c}')
        if d is not None and all(str(y) in d and d[str(y)] is not None for y in FY):
            out[c] = [float(d[str(y)]) for y in FY]
        else:
            out[c] = [float(fc.loc[y, c]) for y in FY]
            if upstream:
                miss.append(c)
    if miss:
        W.append(f"FR1 nəticəsində {', '.join('fr1:' + m for m in miss)} yoxdur — FR1_forecast_full.csv istifadə olundu")
    return out


def _catalogue(bases):
    cat = copy.deepcopy(_st()['inputs'])
    for e in cat['exogenous']:
        if 'fr1_column' in e:
            for sc, fc in bases.items():
                e['baseline'][sc] = [float(v) for v in fc[e['fr1_column']].values]
    return cat


def inputs():
    S = _st()
    return _catalogue({sc: _fr1_base(sc, None, []) for sc in S['M']['scenarios']})


def solve(overrides=None, scenario="Baseline", upstream=None):
    S = _st(); M = S['M']; FY = M['FY']; LA = M['LAST_ACT']
    if scenario not in M['scenarios']:
        raise ValueError(f"naməlum ssenari '{scenario}' (mümkün: {M['scenarios']})")
    W = []
    ov = B.apply_overrides(_catalogue({scenario: _fr1_base(scenario, upstream, W)}), overrides, scenario)
    W += ov['warnings']
    changed = {k for _, k in ov['changed']}
    fc = pd.DataFrame({c: ov['exogenous'][f'fr1:{c}'] for c in FR1C}, index=FY)
    dd = C.drivers(S, fc)
    lv = ov['levers']
    c = {k: float(S['E1'][k]) for k in ('const', 'eta', 'eps', 'tr')}
    spec = lv.get('e1_spec') or 'chosen'
    if spec == 'difference':
        c['eta'] = S['ETA_D']
        if S['E1']['srv']:
            c['eps'] = -c['eta']
    elif spec in S['E1_ALT']:
        c = {k: float(S['E1_ALT'][spec][k]) for k in ('const', 'eta', 'eps', 'tr')}
    elif spec != 'chosen':
        W.append(f"e1_spec '{spec}' naməlumdur — 'chosen' istifadə olundu")
    E1ID = 'FR5.E1_income_relprice'
    for nm, key in (('ln_income_pc', 'eta'), ('ln_relprice', 'eps')):
        if f'{E1ID}|{nm}' in changed:
            c[key] = ov['coefficients'][f'{E1ID}|{nm}']
    sysp = copy.deepcopy(S['SYS'])
    for k in S['TKEYS']:
        kid = f'FR5.S_{k}|x'
        if kid in changed:                      # a new slope is re-anchored on the 2025 log-odds (as the shrinkage is)
            bx = ov['coefficients'][kid]
            sysp[k]['b'] = {'x': bx}
            sysp[k]['const'] = S['LOW25'][k] - bx*S['x25']
            sysp[k]['addf'] = 0.0
    rule = lv.get('price_rule') or 'constant'
    if rule not in ('constant', 'drift', 'admin'):
        W.append(f"price_rule '{rule}' naməlumdur — 'constant' istifadə olundu"); rule = 'constant'
    rp = C.type_relp(S, rule, [LA] + FY)
    for k in S['TKEYS']:
        if f'relp:{k}' in changed:
            for j, y in enumerate(FY):
                rp[k].loc[y] = float(ov['exogenous'][f'relp:{k}'][j])
    rl = float(lv.get('relp_shift_pct') or 0.0)
    dg = float(lv.get('pop_growth_shift_pp') or 0.0)/100.0
    pop_ov = None
    if dg:
        pop_ov = dd['pop'].copy()
        for i, y in enumerate(FY):
            pop_ov.loc[y] = dd['pop'].loc[y]*(1 + dg)**(i + 1)
    sol = C.solve(S, dd, c, sysp, rp, relp_lever=np.log(1 + rl/100.0) if rl else 0.0, pop_override=pop_ov,
                  addf_decay=bool(lv.get('addf_decay')), half_life=_half_life(lv.get('addf_half_life')))
    return sol, ov, W, c


def _half_life(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 1.0
    return v if np.isfinite(v) and v > 0 else 1.0


def series(sol):
    S = _st(); TK = S['TKEYS']
    out = {'fr5:vol:total': sol['Q'], 'fr5:val:total': sol['NOM'], 'fr5:defl:total': sol['P'],
           'fr5:vol_pc': sol['Q']/sol['pop']*1000}
    LA = S['M']['LAST_ACT']
    out['fr5:volg:total'] = (pd.concat([pd.Series({LA: S['Q_LONG25']}), sol['Q']]).pct_change()*100).iloc[1:]
    out['fr5:valg:total'] = (pd.concat([pd.Series({LA: S['PSN25']}), sol['NOM']]).pct_change()*100).iloc[1:]
    for k in TK:
        out[f'fr5:vol:{k}'] = sol['q_t'][k]; out[f'fr5:val:{k}'] = sol['nom_t'][k]
        out[f'fr5:sh:{k}'] = sol['SH'][k]*100; out[f'fr5:defl:{k}'] = sol['p_t'][k]
        out[f'fr5:volg:{k}'] = (pd.concat([pd.Series({LA: S['Q_TYPE25'][k]}), sol['q_t'][k]]).pct_change()*100).iloc[1:]
    for col in sol['SPLIT'].columns:
        v = sol['SPLIT'][col]
        out[f'fr5:split:{col}'] = v*100 if col.endswith('_share') else v
    return out


def run(overrides=None, scenario="Baseline", upstream=None):
    t0 = time.perf_counter()
    sol, ov, W, c = solve(overrides, scenario, upstream)
    meta = {"module": MODULE, "scenario": scenario, "years": _st()['M']['FY'], "levers": ov['levers'],
            "e1": {k: float(v) for k, v in c.items()}, "changed": [f"{a}:{b}" for a, b in ov['changed']],
            "upstream": sorted((upstream or {}).keys()), "seconds": round(time.perf_counter() - t0, 3)}
    return B.make_result(series(sol), meta=meta, warnings=W)


from ._fr5_selftest import selftest  # noqa: E402,F401
