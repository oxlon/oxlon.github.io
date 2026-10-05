"""FR1 post-solution tables: complete accounts (port of `accounts_for`, Part 16), accounts growth metrics (Part 16
tidy export), sector contributions to GDP growth (Part 13.3) and the driver decomposition (`decompose`)."""
import numpy as np
import pandas as pd


def accounts_for(S, source, years, fx_path):
    """Forecast branch of the notebook's accounts_for(source, years, is_forecast=True)."""
    COMP, LAST_ACT, D25, OILGDP_RATIO = S['M']['COMP'], S['M']['LAST_ACT'], S['d25'], S['OILGDP_RATIO']
    out = {}
    get = lambda nm: source[nm].reindex(years) if nm in source.columns else pd.Series(index=years, dtype=float)  # noqa
    pgdp = get('p_gdp'); cpi = get('cpi')
    nom_va = {s: get(f'p_{s}')*get(f'rva_{s}') for s in COMP}
    real_va = {s: get(f'rva_{s}') for s in COMP}
    for a in S['ACCT']:
        k, kind = a['key'], a['kind']
        if kind in ('va', 'own'):
            real = get(a['real']); defl = get(a['defl']); nom = real*defl
        elif kind == 'nonoil':
            real = get('rgdpnon'); nom = get('p_gdp')*get('rgdp') - OILGDP_RATIO*nom_va['min']; defl = nom/real
        elif kind == 'oil':
            real = get('rgdpoil'); nom = OILGDP_RATIO*nom_va['min']; defl = nom/real
        elif kind == 'comp':
            mem = a['members']
            nom = sum(nom_va[m] for m in mem)
            nv = {m: nom_va[m].copy() for m in mem}; rv = {m: real_va[m].copy() for m in mem}
            for m in mem:
                nv[m].loc[LAST_ACT] = float(D25[f'p_{m}']*D25[f'rva_{m}'])
                rv[m].loc[LAST_ACT] = float(D25[f'rva_{m}'])
                nv[m] = nv[m].sort_index(); rv[m] = rv[m].sort_index()
            w = pd.DataFrame(nv); w = w.div(w.sum(axis=1), axis=0)
            gr = pd.DataFrame({m: rv[m].pct_change() for m in mem})
            g = (w.shift(1)*gr).sum(axis=1, min_count=len(mem))
            real = pd.Series(index=years, dtype=float)
            base = float(D25.get(f'r{k}', np.nan))
            if np.isfinite(base):
                lvl = base
                for y in years:
                    gy = g.get(y, np.nan)
                    lvl = lvl*(1 + (gy if np.isfinite(gy) else 0.0)); real[y] = lvl
            elif f'r{k}' in source.columns:
                real = get(f'r{k}')
            defl = nom/real
        elif kind == 'invoil':
            real = get('rinv_tot') - get('rinv_non'); defl = get('p_inv'); nom = real*defl
        elif kind == 'wagebill':
            nom = get('wage')*get('emp')*12/1000.0; defl = cpi/100.0; real = nom/defl
        elif kind == 'xoil':
            nom = get('x_g_oil_usd')*fx_path.reindex(years); defl = pgdp; real = nom/defl
        elif kind == 'qty':
            real = get(a['real']); defl = pd.Series(1.0, index=years); nom = real
        elif kind == 'rate':
            real = get(a['real']); defl = pd.Series(np.nan, index=years); nom = real
        elif kind == 'price':
            defl = get(a['defl']); real = pd.Series(np.nan, index=years); nom = defl
        elif kind == 'defl':
            d = cpi/100.0 if a.get('defl_src') == 'cpi' else pgdp
            if a.get('real') and a['real'] in source.columns:
                real = get(a['real']); nom = real*d
            else:
                nom = get(a['nom']); real = nom/d
            defl = d
        else:
            continue
        out[k] = pd.DataFrame({'real': real, 'deflator': defl, 'nominal': nom})
    return out


def accounts_long(S, acc):
    """{(key, metric): {year: value}} incl. *_growth_pct (first year against the 2025 actual), finite values only,
    exactly as the notebook's FR1_accounts_long.csv construction."""
    H = S['acc_hist25']
    out = {}
    for k, df in acc.items():
        for m in ('real', 'deflator', 'nominal'):
            s = df[m]
            fin = [(int(y), float(v)) for y, v in s.items() if np.isfinite(v)]
            if not fin: continue
            out[(k, m)] = dict(fin)
            base = H.get(k, {}).get(m, np.nan)
            vals = np.array([v for _, v in fin]); yrs = [y for y, _ in fin]
            prev = np.concatenate([[base], vals[:-1]])
            with np.errstate(divide='ignore', invalid='ignore'):
                g = (vals/prev - 1)*100
            gg = {y: float(v) for y, v in zip(yrs, g) if np.isfinite(v)}
            if gg: out[(k, f'{m}_growth_pct')] = gg
    return out


def contributions(S, fc):
    """Port of Part 13.3 'Contribution of each sector to aggregate real GDP growth (chain-weighted)'."""
    FY, COMP, D25, LAB = S['M']['FY'], S['M']['COMP'], S['d25'], S['SECT_LABEL']
    rows = []
    for y in FY:
        prevy = y-1
        wN = {c: (D25[f'p_{c}']*D25[f'rva_{c}'] if y == FY[0]
                  else fc[f'p_{c}'][prevy]*fc[f'rva_{c}'][prevy]) for c in COMP}
        tot = sum(wN.values())
        r = {'year': y}
        for c in COMP:
            prev_v = D25[f'rva_{c}'] if y == FY[0] else fc[f'rva_{c}'][prevy]
            r[LAB[c]] = (wN[c]/tot)*(fc[f'rva_{c}'][y]/prev_v - 1)*100
        r['TOTAL real GDP growth'] = sum(v for k, v in r.items() if k != 'year')
        rows.append(r)
    return pd.DataFrame(rows).set_index('year')


def decompose(S, CF, ex, fc, ap, base_addf):
    """Port of the notebook's `decompose(nm)` with the run's coefficients, paths and add-factors."""
    FY, LAST_ACT, D25, POP25 = S['M']['FY'], S['M']['LAST_ACT'], S['d25'], S['anchor25']['pop']
    LAB, COEF_VAR, EQOF, PERCAP, TFP_SECT = (S['SECT_LABEL'], S['COEF_VAR'], S['EQOF'], set(S['PERCAP']),
                                            S['M']['TFP_SECT'])

    def val(y, v):
        if v == 'trend': return float(y - 2000)
        if v == 'trend_post2015': return float(max(y - 2015, 0))
        if v == 'hc':
            return float(ex[y]['oil_prod'] + 0.9*ex[y]['gas_prod']) if y >= FY[0] else \
                float(D25['oil_prod'] + 0.9*D25['gas_prod'])
        pop_ = ex[y]['pop'] if y >= FY[0] else POP25
        if v == 'pop': return float(pop_)
        src = (lambda c: fc[c][y]) if y >= FY[0] else (lambda c: D25[c])
        if v.endswith('_pc'): return float(src(v[:-3]))/pop_
        return float(src(v))

    def tf(yy):
        if yy < FY[0]: return 0.0
        e = ex[yy]
        return e['tfp_cum'] if e.get('tfp_cum') is not None else e['tfp_boost']*e['tfp_years']
    rows = []
    for var, eq in EQOF.items():
        for y in FY:
            tot = (np.log(val(y, var)) - np.log(val(y-1, var)))*100
            rec = dict(sector=LAB[var.replace('rva_', '')], year=y, total_growth=tot)
            expl = 0.0
            for cname, b in CF[eq].items():
                if cname == 'const': continue
                v = COEF_VAR[cname]
                d = (val(y, v) - val(y-1, v))*100 if v.startswith('trend') else (np.log(val(y, v)) - np.log(val(y-1, v)))*100
                key = 'trend (deterministic)' if v.startswith('trend') else v
                rec[key] = rec.get(key, 0.0) + b*d; expl += b*d
            if var in PERCAP:
                rec['population (unit elasticity)'] = (np.log(val(y, 'pop')) - np.log(val(y-1, 'pop')))*100
                expl += rec['population (unit elasticity)']
            if var.replace('rva_', '') in TFP_SECT:
                rec['scenario TFP boost'] = (tf(y) - tf(y-1))*100; expl += rec['scenario TFP boost']
            a_prev = base_addf.get(var, 0.0) if y == FY[0] else ap[y-1].get(var, 0.0)
            rec['add-factor change (anchor)'] = (ap[y].get(var, 0.0) - a_prev)*100
            expl += rec['add-factor change (anchor)']
            rec['residual (interaction)'] = tot - expl
            rows.append(rec)
    return pd.DataFrame(rows)


CRED6 = ('trd', 'ene', 'agr', 'con', 'ind', 'tra')


def credit_by_sector(S, fc, rule='last'):
    """Nominal credit by sector: households = equation G2; business credit (total - households) split across the six
    sectors; 'oth' = the exact remainder. v2.1 rule 'last' (default): each sector's 2025 share WITHIN business credit,
    held through 2030 (anchored on the last actual year). Rule 'avg3' (pre-v2.1, sensitivity): the 2023-25 average
    shares of total credit renormalised by the average non-household share."""
    FY = S['M']['FY']
    tot, hh = fc['rcred_tot']*fc['p_gdp'], fc['rcred_hh']*fc['p_gdp']
    biz = tot - hh
    anch = S.get('CRED_SHARE_ANCH')
    if rule == 'last' and anch:
        out = {sec: (anch[sec]*biz).reindex(FY) for sec in CRED6}
    else:
        sh = S['CRED_SHARE_FIX']; w = 1 - sh['cred_hh_n']
        out = {sec: (sh[f'cred_{sec}_n']/w*biz).reindex(FY) for sec in CRED6}
    out['oth'] = (biz - sum(out.values())).reindex(FY)
    return out


def investment_by_sector(S, fc, CAL):
    """Real fixed investment by sector = sector share x total real investment: exactly the flow that the solver's
    capital-stock identity uses (Part 11.2/11.3). v2.1: CAL['inv_share'] = the 2025 (last actual) shares; lever
    alloc_shares='avg3' substitutes the pre-v2.1 3-year averages (CAL['inv_share_avg3']) in both places."""
    FY = S['M']['FY']
    return {sec: (CAL['inv_share'][sec]*fc['rinv_tot']).reindex(FY) for sec in S['M']['KSECT']}


def accounts_summary(S, acc):
    """Port of the notebook's summary_table(nm): 2025 -> 2030 real, deflator and nominal change per entity."""
    H, FY, rows = S['acc_hist25'], S['M']['FY'], []
    for a in S['ACCT']:
        k = a['key']
        if k not in acc: continue
        f = acc[k]
        r0, p0, n0 = (H.get(k, {}).get(m, np.nan) for m in ('real', 'deflator', 'nominal'))
        r1, n1, p1 = float(f.real.iloc[-1]), float(f.nominal.iloc[-1]), float(f.deflator.iloc[-1])
        yrs = len(FY)
        rows.append(dict(group=a['group'], entity=a['label'], entity_az=a['label_az'], unit=a['unit'],
                         real_2025=r0, real_2030=r1,
                         real_growth_cum_pct=(r1/r0-1)*100 if (np.isfinite(r0) and r0 != 0) else np.nan,
                         real_growth_avg_pct=((r1/r0)**(1/yrs)-1)*100 if (np.isfinite(r0) and r0 > 0) else np.nan,
                         deflator_2025=p0, deflator_2030=p1,
                         deflator_infl_cum_pct=(p1/p0-1)*100 if (np.isfinite(p0) and p0 != 0) else np.nan,
                         deflator_infl_avg_pct=((p1/p0)**(1/yrs)-1)*100 if (np.isfinite(p0) and p0 > 0) else np.nan,
                         nominal_2025=n0, nominal_2030=n1,
                         nominal_growth_cum_pct=(n1/n0-1)*100 if (np.isfinite(n0) and n0 != 0) else np.nan))
    return pd.DataFrame(rows)
