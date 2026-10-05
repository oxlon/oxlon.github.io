"""FR1 forecast driver: port of the notebook's `run_forecast` (Part 13.1) and of the scenario builder's derived
fields, applied to (possibly overridden) exogenous paths."""
import copy

import numpy as np
import pandas as pd

from ._fr1_solver import solve_year


def run_forecast(M, CF, CAL, ex_path, base_addf, anchor=True, oilrev_ref=None, addf_fixed=None, base_decay=None,
                 anchor_decay=None, nowcast_target=None, inc_out=None, anchor_maxit=20, warn=None, info=None):
    """Same algorithm as the notebook: anchoring of the first year on the YTD targets (iterated), anchor
    increments decaying by ANCHOR_DECAY a year, pass 1 for the oil-revenue reference path, final pass.
    The notebook caps the anchoring at 20 iterations (default here too, so the notebook is reproduced exactly);
    at that cap its 2026 targets are met to ~0.1% (tourism). Lever `anchor_maxit` raises the cap."""
    FY, LAST_ACT, NOWCAST_Y = M['FY'], M['LAST_ACT'], M['NOWCAST_Y']
    ANCHOR_DECAY = M['ANCHOR_DECAY'] if anchor_decay is None else anchor_decay
    NOWCAST_TARGET = M['NOWCAST_TARGET'] if nowcast_target is None else nowcast_target
    prev = dict(M['prev0'])
    if addf_fixed is not None:
        path = {y: dict(addf_fixed[y]) for y in FY}
    else:
        base = dict(base_addf)

        def base_y(y):
            if base_decay is None: return dict(base)
            return {k: v*base_decay.get(k, 1.0)**(y-LAST_ACT) for k, v in base.items()}
        inc = {}
        if anchor:
            for _ in range(anchor_maxit):
                a0 = base_y(NOWCAST_Y)
                for k, v in inc.items(): a0[k] = a0.get(k, 0.0) + v
                sol0, _, _ = solve_year(M, CF, CAL, prev, ex_path[NOWCAST_Y], addf=a0)
                worst = 0.0
                for k, tgt in NOWCAST_TARGET.items():
                    if k in sol0 and sol0[k] > 0:
                        d = np.log(tgt/sol0[k]); inc[k] = inc.get(k, 0.0) + 0.7*d
                        worst = max(worst, abs(d))
                if worst < 1e-8: break
            if info is not None: info['anchor_max_log_gap'] = float(worst)
            if worst >= 5e-3 and warn is not None:
                warn.append(f"2026 ankoru tam yığılmadı: maks. |log(hədəf/model)| = {worst:.2e} "
                            "(rıçaq 'anchor_maxit' ilə iterasiya sayını artırın)")
        if inc_out is not None: inc_out.update(inc)
        path = {}
        for y in FY:
            a = base_y(y)
            for k, v in inc.items(): a[k] = a.get(k, 0.0) + v*ANCHOR_DECAY**(y-NOWCAST_Y)
            path[y] = a
    if oilrev_ref is None:
        p2, out2 = dict(prev), {}
        for y in FY:
            s2, _, _ = solve_year(M, CF, CAL, p2, ex_path[y], addf=path[y])
            out2[y] = s2; p2 = dict(s2)
        ref = {y: out2[y]['rev_oil_n']/out2[y]['p_gdp'] for y in FY}
    else:
        ref = oilrev_ref
    for y in FY: ex_path[y]['oilrev_ref'] = ref[y]
    out, conv = {}, {}
    for y in FY:
        sol, it, err = solve_year(M, CF, CAL, prev, ex_path[y], addf=path[y])
        out[y] = dict(sol); conv[y] = (it, err); prev = dict(sol)
    return pd.DataFrame(out).T, conv, path, ref


def final_pass(M, CF, CAL, ex_path, path, ref):
    """The notebook's shock-run convention (Part 14 `shock_run`, Part 13.4 replications): add-factor path and
    oil-revenue reference held at the scenario's own solution; one forward pass."""
    return run_forecast(M, CF, CAL, ex_path, {}, addf_fixed=path, oilrev_ref=ref)


def build_ex(S, scenario, exo, changed):
    """Scenario exogenous paths. Unchanged inputs keep the notebook's exact values; changed inputs are written in
    and the fields the scenario builder derives from them are recomputed with the builder's formulas."""
    M, FY = S['M'], S['M']['FY']
    ex = {y: dict(S['scen_ex'][scenario][y]) for y in FY}
    a = S['anchor25']
    simple = {'brent': 'brent', 'gas_exp_price': 'gas_exp_price', 'istate_level': 'istate_level',
              'istate_add': 'istate_add', 'fx': 'fx', 'polrate': 'polrate', 'deprate': 'deprate',
              'extdem': 'extdem', 'minwage': 'minwage', 'npl_ratio': 'npl_ratio', 'oil_prod': 'oil_prod',
              'gas_prod': 'gas_prod', 'rinv_oil': 'rinv_oil'}
    for k, f in simple.items():
        if k in changed:
            for i, y in enumerate(FY): ex[y][f] = float(exo[k][i])
    if 'oil_prod' in changed:
        for y in FY:
            ex[y]['oil_exp_vol'] = ex[y]['oil_prod']*S['CAL']['oil_exp_ratio']
            if 'rinv_oil' not in changed:
                ex[y]['rinv_oil'] = a['rinv_oil']*ex[y]['oil_prod']/a['oil_prod']
    if 'gas_prod' in changed:
        for y in FY: ex[y]['gas_exp_vol'] = ex[y]['gas_prod']*S['CAL']['gas_exp_ratio']
    if 'brent' in changed or 'fx' in changed:
        fx_prev, brent_prev = a['fx'], a['brent']
        for y in FY:
            fx, br = ex[y]['fx'], ex[y]['brent']
            ex[y]['dln_fx'] = (np.log(fx)-np.log(fx_prev))*100
            ex[y]['dln_oil_azn'] = (np.log(br*fx)-np.log(brent_prev*fx_prev))*100
            fx_prev, brent_prev = fx, br
    if 'pop_g' in changed:
        pop = a['pop']
        for i, y in enumerate(FY):
            pop *= (1 + float(exo['pop_g'][i])/100); ex[y]['pop'] = pop
    if 'tfp_boost' in changed:
        g = [float(v)/100 for v in exo['tfp_boost']]
        cum = 0.0
        for i, y in enumerate(FY):
            cum = cum + (g[i] if y > M['NOWCAST_Y'] else 0.0)
            ex[y]['tfp_cum'] = cum
    if 'pension_real_g' in changed:
        for i, y in enumerate(FY): ex[y]['pension_real_g'] = float(exo['pension_real_g'][i])/100
    for y in FY: ex[y]['oilrev_ref'] = None
    return ex


def scen_copy(ex):
    return copy.deepcopy(ex)
