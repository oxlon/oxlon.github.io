# %% [markdown]
# ### 17.2 Hesablama mühərriki
#
# Bazar = NACE bölməsi (iki rəqəmli kod) × iqtisadi rayon × il (və ölkə üzrə bölmə × il). Sətir `weight` sayda eyni
# müəssisəni təmsil edə bilər (siyahıyaalma reyestrində 1); hər statistika onu həmin sayda müəssisə kimi nəzərə alır.
#
# | Göstərici | Tərif |
# |---|---|
# | HHI, CR4, CR8 | Σ s², 4 / 8 ən böyük payın cəmi (müəssisə səviyyəsində), 0–10 000 və % |
# | entropiya, ekvivalent say | −Σ s ln s; 10 000 / HHI |
# | Cini | müəssisə gəlirlərinin Cini əmsalı |
# | payların qeyri-sabitliyi | t−1 və ya t ilində mövcud olan müəssisələr üzrə ½ Σ\|s_i,t − s_i,t−1\| (daxil olanlar və çıxanlar 0 ilə nəzərə alınır) |
# | sıra mobilliyi | t−1 və t arasında mövcud müəssisələrin gəlir sıralarının 1 − Spearman ρ |
# | giriş / çıxış / dövriyyə | daxil olanlar (t ilində qeydiyyata alınmış) və çıxanlar (t ilində ləğv edilmiş) / t ilinin sonunda fəaliyyət göstərənlər, %; nisbi ölçü = mövcud müəssisələrə nisbətən orta gəlir |
# | sağ qalma | qeydiyyat kohortları üzrə Kaplan–Meier (sonuncu ildə senzurlanır) |
# | gənc müəssisələrin payı | 5 yaşdan kiçik müəssisələrin gəlirdə payı |
# | qiymət-xərc marjası | (gəlir − satışın maya dəyəri − əməliyyat xərcləri) / gəlir |
# | Boone göstəricisi | mənfəətli müəssisələr üzrə ln(mənfəət)-in ln(orta dəyişən xərc)-ə meyli, hər bölmə-il üzrə (kəsişmə üzrə, mənfəətin davamlılığı modeli yoxdur); ≥ 20 mənfəətli müəssisə tələb edir (çəkili say) |
#
# **Boone göstəricisinin seçim meyli.** ln(mənfəət) yalnız müsbət mənfəəti olan müəssisələr üçün mövcuddur, buna görə
# meyl yalnız mənfəətli müəssisələr üzrə qiymətləndirilir; zərərlə işləyənlər — adətən ən az səmərəli olanlar — xaric
# edilir, bu da nümunəni nəticə üzrə kəsir və meyli sıfıra doğru sürüşdürür. O, struktur elastiklik kimi deyil, sektorlar
# arasında və zamana görə sıralama kimi oxunur; qiymət-xərc marjası isə əksinə, zərərlə işləyən müəssisələri də əhatə edir.
# Hər göstərici `weight` tezlik çəkisini nəzərə alır (sətir başına eyni müəssisələrin sayı; sütun olmadıqda 1).

# %%
def mkt_stats(r, w):
    r = np.asarray(r, float); w = np.asarray(w, float)
    N = w.sum(); R = (w * r).sum()
    if N <= 0 or R <= 0: return dict(n_firms=N, revenue=R, HHI=np.nan, CR4=np.nan, CR8=np.nan, entropy=np.nan, number_equivalent=np.nan, gini=np.nan)
    s = r / R; o = np.argsort(-s); so, wo = s[o], w[o]
    def crk(k):
        take = np.minimum(wo, np.maximum(k - (np.cumsum(wo) - wo), 0)); return float((take * so).sum() * 100)
    hhi = float((w * s ** 2).sum() * 1e4)
    nz = s > 0; ent = float(-(w[nz] * s[nz] * np.log(s[nz])).sum())
    oa = np.argsort(r); ra, wa = r[oa], w[oa]; cw = np.cumsum(wa); cy = np.cumsum(wa * ra)
    gini = float(1 - 2 * np.sum(wa * (cy - wa * ra / 2)) / (cw[-1] * cy[-1])) if cy[-1] > 0 else np.nan
    return dict(n_firms=N, revenue=R, HHI=hhi, CR4=crk(4), CR8=crk(8), entropy=ent, number_equivalent=1e4 / hhi, gini=gini)

def km_curve(dur, event, w):
    '''Weighted Kaplan-Meier by year of life. dur = years from registration to liquidation (0 = liquidated in the
    registration year, counted) or to the last observed year (censored, survived that year). out[k] = share surviving
    k full years.'''
    d = pd.DataFrame({'t': np.asarray(dur, float), 'e': np.asarray(event, bool), 'w': np.asarray(w, float)}); S, out = 1.0, {0: 1.0}
    for t in range(0, int(d.t.max()) + 1):
        at_risk = d.loc[d.t >= t, 'w'].sum(); ev = d.loc[(d.t == t) & d.e, 'w'].sum()
        if at_risk > 0: S *= 1 - ev / at_risk
        out[t + 1] = S
    return out

def wspearman(x, y, w):
    '''Spearman correlation with frequency weights: weighted mid-ranks, then weighted Pearson.'''
    x, y, w = (np.asarray(v, float) for v in (x, y, w))
    def wrank(v):
        o = np.argsort(v, kind='mergesort'); r = np.empty_like(v); cw = np.cumsum(w[o]); r[o] = cw - (w[o] - 1) / 2; return r
    rx, ry = wrank(x), wrank(y); mx, my = np.average(rx, weights=w), np.average(ry, weights=w)
    c = np.average((rx - mx) * (ry - my), weights=w); v = np.sqrt(np.average((rx - mx) ** 2, weights=w) * np.average((ry - my) ** 2, weights=w))
    return float(c / v) if v > 0 else np.nan

def wcol(df):
    '''Frequency weight of each row: the `weight` column if present (missing -> 1), else 1 for every row.'''
    return pd.to_numeric(df['weight'], errors='coerce').fillna(1.0).astype(float) if 'weight' in df else pd.Series(1.0, index=df.index)

def run_layer_b(P, mode, outdir, write=True):
    P = P.copy(); pre = 'FR12_SYNTHETIC_' if mode == 'SYNTHETIC' else 'FR12_FIRM_'
    P['w'] = wcol(P)
    P['sec'] = P.nace2.map(DIV2SEC); P['reg_year'] = pd.to_datetime(P.registration_date).dt.year
    P['liq_year'] = pd.to_datetime(P.liquidation_date, errors='coerce').dt.year if 'liquidation_date' in P else np.nan
    P['revenue'] = pd.to_numeric(P.revenue, errors='coerce'); P['age'] = P.year - P.reg_year
    out = {}
    rows = []
    for (d, rg, y), g in P.groupby(['nace2', 'region', 'year']):
        rows.append(dict(nace2=d, region=rg, year=y, **mkt_stats(g.revenue, g.w)))
    out['concentration_nace_region'] = pd.DataFrame(rows)
    rows = []
    for (d, y), g in P.groupby(['nace2', 'year']):
        rows.append(dict(nace2=d, section=DIV2SEC[d], year=y, **mkt_stats(g.revenue, g.w)))
    CN = pd.DataFrame(rows)
    # share instability and rank mobility, national division markets
    P['_wr'] = P.w * P.revenue
    P['share'] = P._wr / P.groupby(['nace2', 'year'])._wr.transform('sum')
    mob = []
    yrs_ = sorted(P.year.unique())
    for d, g in P.groupby('nace2'):
        piv = g.pivot_table(index='firm_id', columns='year', values='share', aggfunc='sum').fillna(0.0)
        rv = g.pivot_table(index='firm_id', columns='year', values='revenue', aggfunc='sum'); wv = g.pivot_table(index='firm_id', columns='year', values='w', aggfunc='first')
        for y in yrs_[1:]:
            if y in piv and (y - 1) in piv:
                inc = rv[[y - 1, y]].dropna()
                rho = wspearman(inc[y - 1], inc[y], wv.loc[inc.index, y]) if len(inc) > 2 else np.nan
                mob.append(dict(nace2=d, year=y, share_instability=0.5 * (piv[y] - piv[y - 1]).abs().sum() * 100, rank_mobility=1 - rho if rho == rho else np.nan))
    CN = CN.merge(pd.DataFrame(mob), on=['nace2', 'year'], how='left')
    out['concentration_nace'] = CN
    # entry, exit, churn by section x year and by section x region x year
    P['entrant'] = P.reg_year == P.year; P['exiter'] = P.status == 'liquidated'
    inc_ = ~P.entrant & ~P.exiter; wr = P.w * P.revenue
    P['_act'] = P.w * (P.status == 'active'); P['_ne'] = P.w * P.entrant; P['_nx'] = P.w * P.exiter; P['_ni'] = P.w * inc_
    P['_re'] = wr * P.entrant; P['_rx'] = wr * P.exiter; P['_ri'] = wr * inc_; P['_ry'] = wr * (P.age < 5); P['_rt'] = wr
    def flows(keys):
        a = P.groupby(keys)[['_act', '_ne', '_nx', '_ni', '_re', '_rx', '_ri', '_ry', '_rt']].sum()
        mi = a._ri / a._ni.where(a._ni > 0)
        return pd.DataFrame({'active_end': a._act, 'entrants': a._ne, 'exits': a._nx, 'entry_rate': a._ne / a._act.where(a._act > 0) * 100,
                             'exit_rate': a._nx / a._act.where(a._act > 0) * 100, 'churn': (a._ne + a._nx) / a._act.where(a._act > 0) * 100,
                             'entrant_rel_size': a._re / a._ne.where(a._ne > 0) / mi, 'exiter_rel_size': a._rx / a._nx.where(a._nx > 0) / mi,
                             'young_firm_revenue_share': a._ry / a._rt.where(a._rt > 0) * 100}).reset_index()
    out['entry_exit_section'] = flows(['sec', 'year'])
    out['entry_exit_section_region'] = flows(['sec', 'region', 'year'])
    # Kaplan-Meier survival by registration cohort (first record of each firm)
    F = P.sort_values('year').groupby('firm_id').agg(reg_year=('reg_year', 'first'), liq_year=('liq_year', 'max'), w=('w', 'first'), sec=('sec', 'first'))
    F = F[F.reg_year >= P.year.min()]
    F['event'] = F.liq_year.notna(); F['dur'] = np.where(F.event, F.liq_year - F.reg_year, P.year.max() - F.reg_year)
    km = []
    for c, g in F.groupby('reg_year'):
        for k, s in km_curve(g.dur, g.event, g.w).items(): km.append(dict(cohort=c, age=k, survival=s, cohort_size=g.w.sum()))
    out['survival_km'] = pd.DataFrame(km)
    # margins and the Boone indicator
    if 'cost_of_sales' in P and P.cost_of_sales.notna().any():
        P['cos'] = pd.to_numeric(P.cost_of_sales, errors='coerce'); P['opx'] = pd.to_numeric(P.get('operating_costs', 0), errors='coerce').fillna(0)
        P['profit'] = P.revenue - P.cos - P.opx; P['avc'] = P.cos / P.revenue
        bo = []
        for (s_, y), g in P[P.revenue > 0].groupby(['sec', 'year']):
            pcm = (g.w * g.profit).sum() / (g.w * g.revenue).sum() * 100
            h = g[(g.profit > 0) & (g.avc > 0)]
            if h.w.sum() >= 20:                            # weighted count of profitable firms
                X = np.column_stack([np.ones(len(h)), np.log(h.avc)]); W_ = h.w.to_numpy(float); yv = np.log(h.profit.to_numpy(float))
                XtW = X.T * W_; b = np.linalg.solve(XtW @ X, XtW @ yv); u = yv - X @ b
                V = np.linalg.inv(XtW @ X) @ ((X * (W_ * u)[:, None]).T @ (X * (W_ * u)[:, None])) @ np.linalg.inv(XtW @ X)
                bo.append(dict(section=s_, year=y, pcm_pct=pcm, boone_beta=b[1], boone_se=float(np.sqrt(V[1, 1])), n_profitable=float(h.w.sum())))
            else:
                bo.append(dict(section=s_, year=y, pcm_pct=pcm, boone_beta=np.nan, boone_se=np.nan, n_profitable=float(h.w.sum())))
        out['margins_boone'] = pd.DataFrame(bo)
    # pipeline tests (identities)
    cr = out['concentration_nace_region']; cr = cr[cr.revenue > 0]
    _sh = P[P.groupby(['nace2', 'year'])._wr.transform('sum') > 0].groupby(['nace2', 'year']).share.sum()
    T = [('HHI >= 10000 / N in every market', float((1e4 / cr.n_firms - cr.HHI).clip(lower=0).max()), bool((cr.HHI >= 1e4 / cr.n_firms - 1e-6).all())),
         ('CR4 <= CR8 <= 100', float((cr.CR4 - cr.CR8).clip(lower=0).max()), bool(((cr.CR4 <= cr.CR8 + 1e-9) & (cr.CR8 <= 100 + 1e-9)).all())),
         ('entropy <= ln N', float((cr.entropy - np.log(cr.n_firms)).clip(lower=0).max()), bool((cr.entropy <= np.log(cr.n_firms) + 1e-9).all())),
         ('shares add to 1 in every national division market with revenue', float((_sh - 1).abs().max()), bool((_sh - 1).abs().max() < 1e-9)),
         ('Kaplan-Meier survival non-increasing and in [0, 1]', 0.0, bool(out['survival_km'].groupby('cohort').survival.apply(lambda s: (s.diff().dropna() <= 1e-12).all() and s.between(0, 1).all()).all()))]
    out['PIPE'] = pd.DataFrame(T, columns=['test', 'value', 'passed'])
    if write:
        for k, v in out.items():
            v = v.copy()
            if mode == 'SYNTHETIC': v.insert(0, 'WATERMARK', SYN_MARK)
            v.to_csv(Path(outdir) / f'{pre}{"pipeline_tests" if k == "PIPE" else k}.csv', index=False)
    return out
print('engine defined: mkt_stats (weighted HHI, CR4/CR8, entropy, Gini), share instability, rank mobility, entry/exit/churn, KM survival, PCM, Boone')
