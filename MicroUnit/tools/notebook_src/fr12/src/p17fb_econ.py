# %%
def wls_absorb(y, X, groups, w, clusters):
    '''WLS with absorbed group effects (weighted within transformation, identical to dummy-variable WLS) and CR1
    cluster-robust SE, G/(G-1)(N-1)/(N-K) with K = slopes + absorbed effects; inference t(G-1).'''
    yv = np.asarray(y, float); Xv = np.asarray(X, float); wv = np.asarray(w, float)
    gc = pd.factorize(pd.Series(groups).astype(str))[0]; ng = gc.max() + 1; sw = np.bincount(gc, wv, ng)
    dm = lambda v: v - (np.bincount(gc, wv * v, ng) / sw)[gc]
    yt = dm(yv); Xt = np.column_stack([dm(Xv[:, j]) for j in range(Xv.shape[1])])
    H = (Xt * wv[:, None]).T @ Xt; Hi = np.linalg.pinv(H); b = Hi @ ((Xt * wv[:, None]).T @ yt); u = yt - Xt @ b
    cc = pd.factorize(pd.Series(clusters).astype(str))[0]; G = cc.max() + 1
    sc = np.zeros((G, Xv.shape[1])); np.add.at(sc, cc, Xt * (wv * u)[:, None])
    N, K = len(yv), Xv.shape[1] + ng
    V = Hi @ (sc.T @ sc) @ Hi * G / max(G - 1, 1) * (N - 1) / max(N - K, 1)
    se = np.sqrt(np.maximum(np.diag(V), 0)); t = b / se; dof = max(G - 1, 1)
    r2w = 1 - (wv * u ** 2).sum() / (wv * yt ** 2).sum()
    names = list(X.columns) if hasattr(X, 'columns') else [f'x{j}' for j in range(Xv.shape[1])]
    return dict(names=names, b=b, se=se, t=t, p=2 * stats.t.sf(np.abs(t), dof), dof=dof, V=V, n=N, k=Xv.shape[1], n_fe=ng, G=G,
                r2_within=float(r2w), fitted=yv - u, resid=u, ci=(b - stats.t.ppf(.975, dof) * se, b + stats.t.ppf(.975, dof) * se))

def wls_table(model_id, f, kind='coef', cov=''):
    rows = []
    for j, c in enumerate(f['names']):
        r = dict(model=model_id, term=c, coef=f['b'][j], se=f['se'][j], z=f['t'][j], p=f['p'][j], ci_low=f['ci'][0][j], ci_high=f['ci'][1][j],
                 ratio_type=kind, n=f['n'], cov_type=cov)
        rows.append(r)
    return pd.DataFrame(rows)

def lb_boone(P, LB):
    '''(c) Boone indicator: per section-year (engine estimate, Part 17.2) with 95% CI, and pooled regressions.'''
    mb = LB.get('margins_boone')
    if mb is None: return None
    sy = mb.copy(); z = stats.norm.ppf(.975)
    sy['ci_low'] = sy.boone_beta - z * sy.boone_se; sy['ci_high'] = sy.boone_beta + z * sy.boone_se
    D = P[(P.revenue > 0) & P.cost_of_sales.notna()].copy()
    D['profit'] = D.revenue - D.cost_of_sales - D.operating_costs.fillna(0); D['avc'] = D.cost_of_sales / D.revenue
    D = D[(D.profit > 0) & (D.avc > 0)].copy()
    D['ln_profit'] = np.log(D.profit); D['ln_avc'] = np.log(D.avc); D['ln_avc_trend'] = D.ln_avc * (D.year - 2022)
    gk = D.sec + '|' + D.year.astype(str)
    pooled = wls_absorb(D.ln_profit, D[['ln_avc', 'ln_avc_trend']], gk, D.w, D.firm_id)
    S = pd.DataFrame({f'ln_avc_{s}': D.ln_avc * (D.sec == s) for s in sorted(D.sec.unique())}, index=D.index)
    S = S.loc[:, (S != 0).any()]
    bysec = wls_absorb(D.ln_profit, S, gk, D.w, D.firm_id)
    return dict(sector_year=sy, boone_pooled=dict(fit=pooled, data=D, X=D[['ln_avc', 'ln_avc_trend']], y=D.ln_profit, groups=gk),
                boone_sector=dict(fit=bysec, data=D, X=S, y=D.ln_profit, groups=gk))

def division_year(P, LB):
    '''Division x year market table: PCM (all firms), ln HHI, export intensity, size, entry rate, mobility.'''
    a = P.assign(_wr=P.w * P.revenue, _wp=P.w * (P.revenue - P.cost_of_sales.fillna(np.nan) - P.operating_costs.fillna(0)),
                 _wx=P.w * P.exports.fillna(0) if 'exports' in P else 0.0, _e=P.w * (P.reg_year == P.year), _a=P.w * (P.status == 'active'))
    d = a.groupby(['nace2', 'year']).agg(sec=('sec', 'first'), dem=('dem', 'first'), rev=('_wr', 'sum'), prof=('_wp', 'sum'), exp_=('_wx', 'sum'),
                                         ent=('_e', 'sum'), act=('_a', 'sum')).reset_index()
    cn = LB['concentration_nace'][['nace2', 'year', 'HHI', 'share_instability', 'rank_mobility']]
    d = d.merge(cn, on=['nace2', 'year'], how='left')
    d['pcm'] = d.prof / d.rev * 100; d['ln_hhi'] = np.log(d.HHI); d['export_share'] = d.exp_ / d.rev * 100
    d['ln_size'] = np.log(d.rev); d['entry_rate'] = d.ent / d.act.where(d.act > 0) * 100
    lag = d[['nace2', 'year', 'ln_hhi', 'ln_size']].assign(year=d.year + 1).rename(columns={'ln_hhi': 'ln_hhi_l1', 'ln_size': 'ln_size_l1'})
    return d.merge(lag, on=['nace2', 'year'], how='left').replace([np.inf, -np.inf], np.nan)

def lb_scp_mob(D):
    '''(d) SCP and (e) share mobility: OLS with fixed effects as dummies, SE clustered by division.'''
    out = {}
    s = D.dropna(subset=['pcm', 'ln_hhi', 'export_share', 'ln_size']).reset_index(drop=True)
    s = s[s.rev > 0]
    X = sm.add_constant(pd.concat([s[['ln_hhi', 'export_share', 'ln_size']], _fe(s.sec, 'sec_'), _fe(s.year, 'yr_')], axis=1))
    X = X[['const'] + [c for c in X.columns if c != 'const' and X[c].nunique() > 1]]
    r = sm.OLS(s.pcm, X).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(s.nace2)[0]}, use_t=True)
    out['scp'] = dict(res=r, y=s.pcm.set_axis(pd.MultiIndex.from_arrays([s.nace2, s.year])), X=X.set_axis(pd.MultiIndex.from_arrays([s.nace2, s.year])), data=s)
    for dep, nm in [('share_instability', 'mob_instability'), ('rank_mobility', 'mob_rank')]:
        m = D.dropna(subset=[dep, 'ln_hhi_l1', 'entry_rate', 'ln_size_l1', 'dem']).reset_index(drop=True)
        Xm = sm.add_constant(pd.concat([m[['ln_hhi_l1', 'entry_rate', 'ln_size_l1', 'dem']], _fe(m.year, 'yr_')], axis=1))
        rm = sm.OLS(m[dep], Xm).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(m.nace2)[0]}, use_t=True)
        out[nm] = dict(res=rm, y=m[dep].set_axis(pd.MultiIndex.from_arrays([m.nace2, m.year])), X=Xm.set_axis(pd.MultiIndex.from_arrays([m.nace2, m.year])), data=m)
    return out

def lb_entrant(P):
    '''(f) entrant size and post-entry growth. Relative size = ln revenue minus the weighted mean of its section x year x
    size-class cell. Age profile (levels) and growth of relative size between consecutive years (a difference of the
    firm's own relative size, never a lagged dependent variable on the right-hand side); cohort x age table.'''
    E = P[P.revenue > 0].copy(); E['ln_rev'] = np.log(E.revenue); E['cellz'] = E.sec + '|' + E.year.astype(str) + '|' + E.size_class
    cw = E.groupby('cellz').apply(lambda d: np.average(d.ln_rev, weights=d.w)); E['rel'] = E.ln_rev - E.cellz.map(cw)
    A = pd.DataFrame({nm: E.age.between(lo, hi).astype(float) for nm, lo, hi in AGE_BANDS[:4]}, index=E.index)
    A = A.loc[:, A.sum() > 0]
    prof = wls_absorb(E.ln_rev, A, E.cellz, E.w, E.firm_id); E0 = E
    E = E.sort_values(['firm_id', 'year']); E['rel_l'] = E.groupby('firm_id').rel.shift(); E['yr_l'] = E.groupby('firm_id').year.shift()
    Gr = E[(E.yr_l == E.year - 1)].copy(); Gr['g_rel'] = Gr.rel - Gr.rel_l
    B = pd.DataFrame({f'age{a}': (Gr.age == a).astype(float) for a in [1, 2, 3, 4]}, index=Gr.index); B = B.loc[:, B.sum() > 0]
    grow = wls_absorb(Gr.g_rel, B, Gr.year.astype(str), Gr.w, Gr.firm_id)
    C = E[E.reg_year >= int(P.year.min())]
    coh = C.groupby(['reg_year', 'age']).apply(lambda d: pd.Series(dict(enterprises=d.w.sum(), mean_rel_size=np.average(d.rel, weights=d.w)))).reset_index()
    coh['survivor_share'] = coh.enterprises / coh.groupby('reg_year').enterprises.transform('first')
    return dict(entrant_profile=dict(fit=prof, data=E0, X=A, y=E0.ln_rev, groups=E0.cellz), postentry_growth=dict(fit=grow, data=Gr, X=B, y=Gr.g_rel, groups=Gr.year),
                cohorts=coh.rename(columns={'reg_year': 'cohort'}))
