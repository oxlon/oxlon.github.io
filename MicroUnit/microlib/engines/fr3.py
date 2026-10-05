"""FR3 scenario engine (contract section B): average monthly wages by institutional sector, oil / non-oil,
industrial branch and sector hired employment — the notebook's solve, ported in _fr3_core.

    inputs()                          exogenous FR1 paths 2026-2030 (fr1:<col>), the forecast equations'
                                      coefficients (value, SE, 95% CI from FR3_equations.json), levers
    run(overrides, scenario, upstream=None) -> {"series": {id: {year: v}}, "meta", "warnings"}
                                      upstream = {"FR1": result}: FR1 paths are taken from it (fr1:cpi, fr1:rgdp,
                                      fr1:rgdpnon, fr1:emp, fr1:rexp_cur, fr1:rva_*); otherwise FR1_forecast_full.csv
    selftest()                        run({}) per scenario reproduces FR3_wage_forecast_full / industry_branch_wages /
                                      sector_employment / wage_accounts_long / wage_summary (rel. 1e-8)
Levers: mw_growth (% a year, number or 5 values), prem_target (2030 oil premium), prem_path (5 values),
nowcast_half_life (years), e1_mode ('cross-check' | 'fixed' | 'weighted'), branch_anchor (bool; default True =
baseline anchored on each branch's own 2025 residual, False = unanchored sensitivity)."""
from __future__ import annotations

import copy
import os
import time

import numpy as np
import pandas as pd

from . import base as B
from . import _fr3_core as C
from .. import project_root

MODULE = "FR3"
_S = None
_CSV = {}


def _st():
    global _S
    if _S is None:
        S = B.load_state(MODULE)
        S['M']['FY'] = [int(y) for y in S['M']['FY']]
        S['branch']['p0'] = [np.nan if v is None else float(v) for v in S['branch']['p0']]
        _S = S
    return _S


def reload():
    global _S
    _S = None
    _CSV.clear()
    return _st()


def _out(name):
    return os.path.join(project_root(), 'output', name)


def _read_csv(name, **kw):
    """Read an output CSV (cached by mtime); retries while another module rewrites it."""
    p = _out(name)
    for i in range(8):
        try:
            key = (p, os.path.getmtime(p), repr(sorted(kw.items())))
            if key not in _CSV:
                _CSV[key] = pd.read_csv(p, **kw)
            return _CSV[key].copy()
        except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError, ValueError):
            if i == 7:
                raise
            time.sleep(0.5)


def _fr1_csv(scenario):
    fc = _read_csv(_st()['csv']['fr1'], index_col=0)
    fc = fc[fc.scenario == scenario]
    fc.index = fc.index.astype(int)
    return fc


def _fr1_base(scenario, upstream, W):
    """FR1 driver paths for the scenario: upstream FR1 result if given, else FR1_forecast_full.csv."""
    S = _st(); FY = S['M']['FY']
    csv = _fr1_csv(scenario)
    out = pd.DataFrame(index=FY, columns=S['FR1_COLS'], dtype=float)
    ser = (((upstream or {}).get('FR1') or {}).get('series')) or {}
    miss = []
    for c in S['FR1_COLS']:
        d = ser.get(f'fr1:{c}')
        if d is not None and all(str(y) in d and d[str(y)] is not None for y in FY):
            out[c] = [float(d[str(y)]) for y in FY]
        else:
            out[c] = [float(csv.loc[y, c]) for y in FY]
            if upstream:
                miss.append(c)
    if miss:
        W.append(f"FR1 nəticəsində {', '.join('fr1:' + m for m in miss)} yoxdur — FR1_forecast_full.csv istifadə olundu")
    return out


def _catalogue(bases):
    """inputs catalogue with exogenous baselines replaced by the current FR1 paths {scenario: frame}."""
    cat = copy.deepcopy(_st()['inputs'])
    for e in cat['exogenous']:
        for sc, fc in bases.items():
            e['baseline'][sc] = [float(v) for v in fc[e['fr1_column']].values]
    return cat


def inputs():
    S = _st()
    return _catalogue({sc: _fr1_base(sc, None, []) for sc in S['M']['scenarios']})


def _lever_path(v, n, scale, W, name):
    if v is None:
        return None
    if isinstance(v, (list, tuple, np.ndarray)):
        if len(v) != n:
            W.append(f"{name}: {n} dəyər gözlənilirdi, {len(v)} verildi — nəzərə alınmadı")
            return None
        return [float(x)/scale for x in v]
    return [float(v)/scale]*n


def solve(overrides=None, scenario="Baseline", upstream=None):
    """Full solve; returns (frames dict, resolved overrides, warnings)."""
    S = _st(); M = S['M']; FY = M['FY']
    if scenario not in M['scenarios']:
        raise ValueError(f"naməlum ssenari '{scenario}' (mümkün: {M['scenarios']})")
    W = []
    fcb = _fr1_base(scenario, upstream, W)
    ov = B.apply_overrides(_catalogue({scenario: fcb}), overrides, scenario)
    W += ov['warnings']
    fc = pd.DataFrame({c: ov['exogenous'][f'fr1:{c}'] for c in S['FR1_COLS']}, index=FY)
    coefs = {nm: pd.Series([ov['coefficients'].get(f'FR3.{nm}|{n}', v) for n, v in zip(S['CF'][nm]['names'],
                                                                                    S['CF'][nm]['values'])],
                           index=S['CF'][nm]['names']) for nm in S['FC_EQS']}
    emp_el = ov['coefficients'].get('FR3.PAN_sec_emp_2w|ln_gva', S['EMP_EL'])
    beta = ov['coefficients'].get('FR3.PAN_ind_between|ln_prod', S['BETA_BETWEEN'])
    lv = ov['levers']
    mwg = _lever_path(lv.get('mw_growth'), len(FY), 100.0, W, 'mw_growth') or [S['MW_GROWTH'][scenario]]*len(FY)
    ppath = _lever_path(lv.get('prem_path'), len(FY), 1.0, W, 'prem_path')
    pt = lv.get('prem_target')
    pt = S['PREM_TARGET'][scenario] if pt is None else float(pt)
    hl = float(lv.get('nowcast_half_life') or M['HALF_LIFE'])
    var = dict(S['VAR_REC'])
    mode = lv.get('e1_mode') or 'cross-check'
    if mode == 'fixed':
        var['w_avg'] = 0.0
    elif mode == 'weighted':
        var['w_avg'] = S['E1_MSE']
    elif mode != 'cross-check':
        W.append(f"e1_mode '{mode}' naməlumdur — 'cross-check' istifadə olundu")
    ex = C.build_ex(S, fc, mwg, pt)
    f3, inc = C.run_wage_forecast(S, ex, coefs, var, S['NOWCAST_W'], hl, ppath)
    empf, gva_f = C.sector_employment(S, fc, {y: ex[y]['hired'] for y in FY}, emp_el)
    ba = lv.get('branch_anchor')
    brf = C.branch_wages(S, f3, gva_f, empf['ind'], beta, anchor=True if ba is None else bool(ba))
    return dict(full=f3, sector=empf, branch=brf, inc=inc, fc=fc), ov, W


def series(fr):
    S = _st(); W25 = S['W25']
    f3 = fr['full'].astype(float)
    out = {f'fr3:{c}': f3[c] for c in f3.columns}
    out['fr3:prem_sp'] = f3['w_state']/f3['w_priv']
    for k in ['w_avg', 'w_state', 'w_priv', 'w_non', 'w_oil']:
        r = 'r' + k
        n = pd.concat([pd.Series({S['M']['LAST_ACT']: W25[k]}), f3[k]])
        rr = pd.concat([pd.Series({S['M']['LAST_ACT']: W25[k]/W25['cpi']*100}), f3[k]/f3['cpi']*100])
        out[f'fr3:{k}_g'] = (n.pct_change()*100).iloc[1:]
        out[f'fr3:{r}_g'] = (rr.pct_change()*100).iloc[1:]
    for k in S['SEC8']:
        out[f'fr3:emp:{k}'] = fr['sector'][k]
        out[f'fr3:empsh:{k}'] = fr['sector'][k]/fr['sector'].sum(axis=1)*100
    for nm, code in zip(S['branch']['names'], S['branch']['code']):
        out[f'fr3:brw:{code}'] = fr['branch'][nm]
    return out


def run(overrides=None, scenario="Baseline", upstream=None):
    t0 = time.perf_counter()
    fr, ov, W = solve(overrides, scenario, upstream)
    meta = {"module": MODULE, "scenario": scenario, "years": _st()['M']['FY'], "levers": ov['levers'],
            "changed": [f"{a}:{b}" for a, b in ov['changed']], "upstream": sorted((upstream or {}).keys()),
            "nowcast_increment": {k: float(v) for k, v in fr['inc'].items()},
            "seconds": round(time.perf_counter() - t0, 3)}
    return B.make_result(series(fr), meta=meta, warnings=W)


from ._fr3_selftest import selftest  # noqa: E402,F401
