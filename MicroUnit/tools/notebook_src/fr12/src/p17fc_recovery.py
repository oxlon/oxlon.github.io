# %%
def cond_poisson(E, expo, X, strata, clusters, tol=1e-11, maxit=100):
    '''Poisson with stratum fixed effects by conditional ML (multinomial within each stratum; identical to Poisson with
    stratum dummies and offset ln exposure). Cluster-robust sandwich, G/(G-1). Normal inference.'''
    Xv = np.asarray(X, float); E = np.asarray(E, float); ex = np.asarray(expo, float)
    s = pd.factorize(pd.Series(strata).astype(str))[0]; Es = np.bincount(s, E)
    keep = Es[s] > 0; Xv, E, ex = Xv[keep], E[keep], ex[keep]
    s = pd.factorize(s[keep])[0]; ns = s.max() + 1; Es = np.bincount(s, E, ns); k = Xv.shape[1]
    cl = pd.factorize(pd.Series(np.asarray(clusters)[keep]).astype(str))[0]; G = cl.max() + 1; b = np.zeros(k)
    def parts(b):
        eta = Xv @ b; r = ex * np.exp(eta - eta.max()); pi = r / np.bincount(s, r, ns)[s]
        xb = np.zeros((ns, k)); np.add.at(xb, s, Xv * pi[:, None]); return pi, xb
    for _ in range(maxit):
        pi, xb = parts(b)
        g = Xv.T @ E - (Es[:, None] * xb).sum(0)
        H = (Xv * (Es[s] * pi)[:, None]).T @ Xv - (xb * Es[:, None]).T @ xb
        step = np.linalg.solve(H, g); b = b + step
        if np.abs(step).max() < tol: break
    pi, xb = parts(b); H = (Xv * (Es[s] * pi)[:, None]).T @ Xv - (xb * Es[:, None]).T @ xb; Hi = np.linalg.inv(H)
    sc = np.zeros((G, k)); np.add.at(sc, cl, (E - Es[s] * pi)[:, None] * Xv)
    V = Hi @ (sc.T @ sc) @ Hi * G / max(G - 1, 1); se = np.sqrt(np.diag(V)); z = stats.norm.ppf(.975)
    names = list(X.columns)
    return dict(names=names, b=b, se=se, t=b / se, p=2 * stats.norm.sf(np.abs(b / se)), V=V, n=int(keep.sum()), k=k, n_fe=ns, G=G,
                loglik=float((E * np.log(np.maximum(pi, 1e-300))).sum()), ci=(b - z * se, b + z * se), events=float(E.sum()))

def cond_poisson_check(R, X):
    '''Validation on a subset of strata: conditional ML = statsmodels Poisson GLM with stratum dummies + offset.'''
    st = (R.cell + '|' + R.year.astype(str)); top = (R.event * R.w).groupby(st).sum().sort_values(ascending=False).index[:60]
    m = st.isin(top).to_numpy(); sub = R[m]; ss = st[m]; Xs = X[m]; E_ = sub.event * sub.w
    binary = lambda c: set(np.unique(Xs[c])) <= {0.0, 1.0}
    keepc = [c for c in Xs.columns if (Xs[c] - Xs[c].groupby(ss.values).transform('mean')).abs().sum() > 1e-9
             and (not binary(c) or (float((E_ * Xs[c]).sum()) >= 10 and float((E_ * (1 - Xs[c])).sum()) >= 10))]
    if not keepc: return 0.0
    Xs = Xs[keepc]; cp = cond_poisson(sub.event * sub.w, sub.w, Xs, ss, sub.cell)
    D = pd.get_dummies(ss, dtype=float); Z = pd.concat([Xs.reset_index(drop=True), D.reset_index(drop=True)], axis=1)
    gl = sm.GLM((sub.event * sub.w).to_numpy(), Z, family=_fam.Poisson(), offset=np.log(sub.w.to_numpy())).fit()
    return float(np.max(np.abs(cp['b'] - gl.params[keepc].to_numpy())))

def lb_recovery(P, ex):
    '''(g) estimated vs true generator parameters (SYNTHETIC only). Two DGP-exact estimators plus the main models.
    G1 revenue: ln revenue = cell(section x year x size) + mu_i - gamma_s e_i + 0.25 shock - 0.7 [age < 2], avc = v_s exp(e_i)
       -> slope of ln revenue on ln avc by section = -gamma_s; age-0/1 dummies = -0.7, age 2 = 0 (unclipped avc, records).
    G2 exit: deaths fixed per section x region x year cell, selected with score HAZ[size] x 2 [age < 3]
       -> conditional Poisson with cell-year strata: ln HR small/medium/large vs micro = ln .4/.2/.08, ages 1-2 = ln 2;
       ownership and concentration are not in the generator (true 0).'''
    rows = []; fits = {}
    D = P[(P.revenue > 0) & P.cost_of_sales.notna()].copy(); D['avc'] = D.cost_of_sales / D.revenue
    D = D[(D.avc > 0.151) & (D.avc < 0.979)].copy()                    # clipped cost ratios carry no information on e_i
    D['ln_rev'] = np.log(D.revenue); D['ln_avc'] = np.log(D.avc)
    secs = sorted(D.sec.unique()); X1 = pd.DataFrame({f'ln_avc_{s}': D.ln_avc * (D.sec == s) for s in secs}, index=D.index)
    for a in range(3): X1[f'age{a}'] = (D.age == a).astype(float)
    X1 = X1.loc[:, X1.abs().sum() > 0]
    g1 = wls_absorb(D.ln_rev, X1, D.sec + '|' + D.year.astype(str) + '|' + D.size_class, np.ones(len(D)), D.firm_id)
    fits['recovery_revenue'] = dict(fit=g1, data=D, X=X1, y=D.ln_rev)
    true1 = {f'ln_avc_{s}': -GAMMA[s] for s in secs} | {'age0': -YOUNG_SIZE_PEN, 'age1': -YOUNG_SIZE_PEN, 'age2': 0.0}
    for j, c in enumerate(g1['names']):
        rows.append(dict(block='G1 revenue-cost elasticity (records, section x year x size FE)', parameter=c, true=true1[c], estimate=g1['b'][j], se=g1['se'][j],
                         ci_low=g1['ci'][0][j], ci_high=g1['ci'][1][j]))
    R = P[(P.age >= 1) & P.ln_hhi_l1.notna()].copy()
    X2 = pd.concat([_dummies(R.size_class, SIZE_D), pd.DataFrame({'young12': R.age.between(1, YOUNG_HAZ_AGE - 1).astype(float)}, index=R.index),
                    _dummies(R.ownership, OWN_D), R[['ln_hhi_l1']]], axis=1)
    X2 = X2.loc[:, X2.abs().sum() > 0]
    g2 = cond_poisson(R.event * R.w, R.w, X2, R.cell + '|' + R.year.astype(str), R.cell)
    g2['check'] = cond_poisson_check(R, X2); fits['recovery_exit'] = dict(fit=g2, data=R, X=X2, y=R.event)
    true2 = {c: np.log(HAZ[c] / HAZ['micro']) for c in SIZE_D} | {'young12': np.log(YOUNG_HAZ_MULT)} | {c: 0.0 for c in OWN_D + ['ln_hhi_l1']}
    for j, c in enumerate(g2['names']):
        rows.append(dict(block='G2 exit hazard (conditional Poisson, cell-year strata)', parameter=c, true=true2[c], estimate=g2['b'][j], se=g2['se'][j],
                         ci_low=g2['ci'][0][j], ci_high=g2['ci'][1][j]))
    for key, lab in [('exit_cloglog', '(b) cloglog, additive section/region/year FE'), ('exit_logit', '(b) logit, additive section/region/year FE')]:
        r = ex[key]['res']; ci = r.conf_int()
        tb = {c: np.log(HAZ[c] / HAZ['micro']) for c in SIZE_D} | {'age1': np.log(YOUNG_HAZ_MULT), 'age2': np.log(YOUNG_HAZ_MULT), 'age3_4': 0.0, 'age5_9': 0.0} \
             | {c: 0.0 for c in OWN_D + ['dem', 'ln_hhi_l1']}
        for c, tv in tb.items():
            if c in r.params:
                rows.append(dict(block=lab, parameter=c, true=tv, estimate=float(r.params[c]), se=float(r.bse[c]), ci_low=float(ci.loc[c, 0]), ci_high=float(ci.loc[c, 1])))
    T = pd.DataFrame(rows); T['covered'] = (T.ci_low <= T.true) & (T.true <= T.ci_high); T['error'] = T.estimate - T.true
    return T, fits
