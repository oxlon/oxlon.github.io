# %%
NULLR = dict(spec=[], anchor='fe', mode='null')
def stock_rates(rows, lnB, xr, N0):
    '''identity: N_t = (N_{t-1} + B_t) / (1 + x_t), entry rate = B_t / N_t (rates on the end-year stock).'''
    d = rows[['unit', 'year']].copy(); d['B'] = np.exp(lnB); d['x'] = np.clip(xr, 0, None)
    d = d.sort_values(['unit', 'year']); N = []
    for u, g in d.groupby('unit', sort=False):
        n = float(N0[u])
        for b_, x_ in zip(g.B, g.x):
            n = (n + b_) / (1 + x_ / 100); N.append(n)
    d['N'] = N; d['entry'] = d.B / d.N * 100; d['new'] = d.B; d['exits'] = d.x / 100 * d.N
    return d

HOLDTAB = []
for pn, df in PANELS.items():
    hold = MODELS[(pn, 'lnB')]['hold']
    for origin, tgs in hold:
        yrs_ = [y for y in sorted(df.year.unique()) if origin < y <= max(tgs)]
        rows = df[df.year.isin(yrs_)].sort_values(['unit', 'year']).reset_index(drop=True)
        tr = df[df.year <= origin]
        N0 = tr[tr.year == origin].set_index('unit').N
        res = {}
        for nm, re_, rx_ in [('rule', SELECT[(pn, 'lnB')]['rule'], SELECT[(pn, 'exit')]['rule']), ('null', NULLR, NULLR)]:
            lb = apply_rule((pn, 'lnB'), re_, origin, rows, COHLOG if nm == 'rule' else None)['pred']
            xr = apply_rule((pn, 'exit'), rx_, origin, rows, COHLOG if nm == 'rule' else None)['pred']
            res[nm] = stock_rates(rows, lb, xr, N0).set_index(['unit', 'year']).assign(lnB=lambda d: np.log(d.B), exit=lambda d: d.x)
        for metric, col in [('entry rate, % (births / identity stock)', 'entry'), ('log births', 'lnB'), ('exit rate, %', 'exit')]:
            base = tr.dropna(subset=[col]).sort_values('year')
            rw = base.groupby('unit')[col].last(); cm = base.groupby('unit')[col].mean()
            for _, r in df[df.year.isin(tgs)].dropna(subset=[col]).iterrows():
                k = (r.unit, r.year)
                HOLDTAB.append(dict(panel=pn, metric=metric, origin=origin, unit=r.unit, target=r.year, actual=r[col],
                                    rule=res['rule'].loc[k, col], null=res['null'].loc[k, col], rw=rw[r.unit], constant=cm[r.unit]))
HOLDTAB = pd.DataFrame(HOLDTAB)
HOLDV = []
for (pn, metric), h in HOLDTAB.groupby(['panel', 'metric'], sort=False):
    e = {k: h[k] - h.actual for k in ['rule', 'null', 'rw', 'constant']}
    lu = pd.DataFrame({k: v ** 2 for k, v in e.items()}).assign(u=h.unit.values).groupby('u').mean()
    rk = SELECT[(pn, 'exit' if metric.startswith('exit') else 'lnB')]
    HOLDV.append(dict(panel=pn, metric=metric, rule=rname(rk['rule']), implied_rw_weight=rk['w_rw'], n=len(h), targets=', '.join(str(int(t)) for t in sorted(h.target.unique())),
                      rmse_rule=float(np.sqrt((e['rule'] ** 2).mean())), rmse_null=float(np.sqrt((e['null'] ** 2).mean())),
                      rmse_rw=float(np.sqrt((e['rw'] ** 2).mean())), rmse_constant=float(np.sqrt((e['constant'] ** 2).mean())),
                      theil_rule_vs_rw=theil(e['rule'], e['rw']), theil_rule_vs_constant=theil(e['rule'], e['constant']),
                      theil_null_vs_rw=theil(e['null'], e['rw']), theil_constant_vs_rw=theil(e['constant'], e['rw']),
                      dm_p_rule_vs_rw=dm_hln(lu.rule.values, lu.rw.values)[1], dm_p_rule_vs_constant=dm_hln(lu.rule.values, lu.constant.values)[1]))
HOLDV = pd.DataFrame(HOLDV)
COHTAB = pd.DataFrame(COHLOG).drop_duplicates(subset=['key', 'origin', 'driver'])
display(HOLDV.round(3))
display(COHTAB.drop_duplicates().round(3) if len(COHTAB) else 'coherence: no structural driver in the chosen rules')
