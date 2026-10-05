"""FR1 engine run logic: resolve overrides into (CF, CAL, base add-factors, exogenous paths, levers), solve, and
assemble the indicator series."""
import numpy as np
import pandas as pd

from . import _fr1_fc as FCM
from . import _fr1_ids as I
from . import _fr1_post as P


def resolve_coefs(S, ov, W):
    """CF with overrides; ties keep imposed homogeneity (e.g. E3: ln_gdpnon + ln_pens_r = 1) when only one
    member is overridden. Returns (CF, changed {eq: {name: (old, new)}})."""
    CF = {eq: dict(c) for eq, c in S['CF'].items()}
    req = {}
    for key in (ov.get('changed') or []):
        if key[0] != 'coefficients': continue
        eqid, name = key[1].split('|', 1)
        req.setdefault(eqid.split('.', 1)[1], {})[name] = float(ov['coefficients'][key[1]])
    keep = bool(ov['levers'].get('keep_restrictions', True))
    changed = {}
    for eq, d in req.items():
        for name, v in d.items():
            changed.setdefault(eq, {})[name] = (CF[eq][name], v); CF[eq][name] = v
        for tie in (S['TIES'].get(eq) or []):
            if not keep: continue
            if len(tie) == 2:
                a, b = tie
                if a in d and b not in d:
                    changed[eq][b] = (CF[eq][b], 1.0 - CF[eq][a]); CF[eq][b] = 1.0 - CF[eq][a]
                    W.append(f"FR1.{eq}: '{b}' = 1 − '{a}' (homogenlik məhdudiyyəti saxlanıldı)")
                elif b in d and a not in d:
                    changed[eq][a] = (CF[eq][a], 1.0 - CF[eq][b]); CF[eq][a] = 1.0 - CF[eq][b]
                    W.append(f"FR1.{eq}: '{a}' = 1 − '{b}' (homogenlik məhdudiyyəti saxlanıldı)")
                continue
            # v2.3: (m1, ..., m_n, k): k = 1 - (m1 + ... + m_n) (E3: non-oil GDP, wage bill -> pension bill)
            mem, k = list(tie[:-1]), tie[-1]
            if any(m in d for m in mem) and k not in d:
                v = 1.0 - sum(CF[eq][m] for m in mem)
                changed[eq][k] = (CF[eq][k], v); CF[eq][k] = v
                W.append(f"FR1.{eq}: '{k}' = 1 − ({' + '.join(repr(m) for m in mem)}) (homogenlik məhdudiyyəti saxlanıldı)")
            elif k in d and not any(m in d for m in mem):
                m0 = mem[0]; v = 1.0 - CF[eq][k] - sum(CF[eq][m] for m in mem[1:])
                changed[eq][m0] = (CF[eq][m0], v); CF[eq][m0] = v
                W.append(f"FR1.{eq}: '{m0}' = 1 − '{k}' − qalanlar (homogenlik məhdudiyyəti saxlanıldı)")
    return CF, changed


def resolve_cal(S, CF, changed, alloc='last', lev=None):
    CAL = dict(S['CAL'])
    lev = lev or {}
    if alloc == 'avg3' and 'inv_share_avg3' in CAL:      # pre-v2.1 investment shares (sensitivity lever)
        CAL['inv_share'] = dict(CAL['inv_share_avg3'])
    if lev.get('income_block'):                          # v2.2 lever: 'share' (E3, default) | 'legs' (income by source)
        CAL['e3_mode'] = lev['income_block']
    if lev.get('fiscal_rule'):                           # v2.2 lever: 'F3' (default) | 'nobd'
        CAL['fiscal_rule'] = lev['fiscal_rule']
    if any(eq.startswith('G5_defl') for eq in changed):
        CAL['defl'] = {s: tuple(CF[f'G5_defl_{s}'].get(k, 0.0) for k in ('const', 'infl', 'dln_oil_azn', 'dln_xpi', 'dln_fx'))
                       for s in S['M']['COMP']}
        CAL['mkt_defl'] = {k: (CF[f'G5_defl_{k}']['const'], CF[f'G5_defl_{k}']['infl']) for k in S['M']['MKT']}
    return CAL


def resolve_base_addf(S, changed, recalibrate):
    """Base add-factor = the equation's own 2025 residual. With a changed coefficient it is recomputed so that
    the equation still reproduces 2025: a_new = a_old - sum_j (b_new - b_old) x_j,2025 (Part 13.4 convention)."""
    base = dict(S['BASE_ADDF'])
    if not recalibrate: return base
    var_of = {eq: v for v, eq in S['EQ_OF_VAR'].items()}
    for eq, d in changed.items():
        v = var_of.get(eq)
        if v is None or v not in base or eq not in S['x25']: continue   # v2.2: growth equations have no base add-factor
        x = S['x25'][eq]
        base[v] = base[v] - sum((new - old)*(1.0 if n == 'const' else x[n]) for n, (old, new) in d.items())
    return base


def solve(S, scenario, ov, W):
    M = S['M']; FY = M['FY']; lev = ov['levers']
    CF, changed = resolve_coefs(S, ov, W)
    alloc = lev.get('alloc_shares', 'last')
    CAL = resolve_cal(S, CF, changed, alloc, lev)
    base = resolve_base_addf(S, changed, bool(lev.get('addf_recalibrate', True)))
    exch = {k for (sec, k) in ov['changed'] if sec == 'exogenous'}
    ex = FCM.build_ex(S, scenario, ov['exogenous'], exch)
    rule = lev.get('istate_rule', 'policy_oilrev')
    if rule == 'F4':
        for y in FY: ex[y]['istate_mode'] = 'F4'
    if lev.get('credit_overlay'):
        el = float(lev.get('credit_overlay_el', S['CRED_EL_OUT']))
        for y in FY:
            ex[y]['credit_overlay'] = el; ex[y]['cred_ref'] = S['cred_ref'][scenario][y]
    mode = lev.get('mode', 'shock'); info = {}
    anchor, decay = bool(lev.get('anchor', True)), float(lev.get('anchor_decay', M['ANCHOR_DECAY']))
    # v2.3: optional decay of the base add-factors at a FIXED, user-set half-life (no estimated residual dynamics)
    hl = float(lev.get('addf_halflife', M.get('ADDF_HALFLIFE', 1.0)))
    bdecay = {k: 0.5**(1.0/hl) for k in base} if lev.get('base_addf_decay') else None
    if mode == 'reanchor':
        fc, conv, path, ref = FCM.run_forecast(M, CF, CAL, ex, base, anchor=anchor, base_decay=bdecay,
                                               anchor_decay=decay, oilrev_ref=None, warn=W, info=info,
                                               anchor_maxit=int(lev.get('anchor_maxit', 20)))
        if rule == 'policy_level':
            for y in FY: ex[y]['oilrev_ref'] = None
            fc, conv, path, _ = FCM.run_forecast(M, CF, CAL, ex, {}, addf_fixed=path,
                                                 oilrev_ref={y: None for y in FY})
    else:
        default_path = (not changed or not lev.get('addf_recalibrate', True)) and anchor and bdecay is None \
            and decay == M['ANCHOR_DECAY']
        if default_path:
            path = {y: dict(S['ADDF'][scenario][y]) for y in FY}
        else:
            inc = S['ANCHOR_INC'][scenario] if anchor else {}
            path = {}
            for y in FY:
                a = {k: v*bdecay.get(k, 1.0)**(y-M['LAST_ACT']) for k, v in base.items()} if bdecay else dict(base)
                for k, v in inc.items(): a[k] = a.get(k, 0.0) + v*decay**(y-M['NOWCAST_Y'])
                path[y] = a
        ref = {y: None for y in FY} if rule == 'policy_level' else dict(S['OILREF'][scenario])
        fc, conv, path, ref = FCM.final_pass(M, CF, CAL, ex, path, ref)
    bad = [y for y, (it, err) in conv.items() if not err < 1e-9]
    if bad:
        W.append(f"həlledici {bad} illərində tam yığılmadı (Gauss–Seidel); nəticələri ehtiyatla şərh edin")
    return dict(fc=fc, conv=conv, path=path, ref=ref, CF=CF, CAL=CAL, base=base, ex=ex, changed=changed, info=info,
                alloc=alloc)


def series(S, R):
    """All FR1 indicator series of one solved scenario: {id: {year: value}}."""
    fc, FY = R['fc'], S['M']['FY']
    out = {}
    for col in S['FC_COLS']:
        out[I.var_id(col)] = {y: float(fc[col][y]) for y in FY}
    fx = pd.Series({y: R['ex'][y]['fx'] for y in FY})
    acc = P.accounts_for(S, fc, FY, fx)
    for (k, m), d in P.accounts_long(S, acc).items():
        out[I.acc_id(k, m)] = d
    con = P.contributions(S, fc)
    code = {v: k for k, v in S['SECT_LABEL'].items()}
    for c in con.columns:
        out[I.contrib_id(code.get(c, 'total'))] = {int(y): float(v) for y, v in con[c].items()}
    dec = P.decompose(S, R['CF'], R['ex'], fc, R['path'], R['base'])
    for _, r in dec.iterrows():
        sec = code[r['sector']]
        for c in dec.columns:
            if c in ('sector', 'year') or not np.isfinite(r[c]): continue
            out.setdefault(I.dec_id(sec, c), {})[int(r['year'])] = float(r[c])
    for sec, s in P.credit_by_sector(S, fc, R.get('alloc', 'last')).items():
        out[I.cred_id(sec)] = {int(y): float(v) for y, v in s.items()}
    for sec, s in P.investment_by_sector(S, fc, R['CAL']).items():
        out[I.inv_id(sec)] = {int(y): float(v) for y, v in s.items()}
    return out, dict(acc=acc, contrib=con, dec=dec)
