# %% [markdown]
# ### 17.7 Yüklənmiş reyestr üzərində B qatının ekonometrikası (hazırda SİNTETİK, Nazirliyin faylı olduqda REAL)
#
# > **sintetik məlumat — texniki nümayiş.** SİNTETİK rejimdə aşağıdakı hər qiymətləndirmə uydurulmuş müəssisələri təsvir
# > edir: o, ekonometrik emal xəttinin əvvəldən sonadək işlədiyini və generatorun daxil etdiyi parametrləri bərpa etdiyini
# > sübut edir. Bu, Azərbaycan bazarları haqqında tapıntı **deyil**. Eyni kod Nazirliyin reyestri üzərində dəyişmədən işləyir
# > (REAL rejim, nəticələr `FR12_FIRM_econ_*.csv`, su nişanı olmadan) — 17.8-dəki əvəzetmə testi bunu sübut edir.
#
# | | Model | Vahid, nümunə | Qiymətləndirici, statistik nəticə |
# |---|---|---|---|
# | (a) | girişlərin sayı sektor tələbinin artımı, konsentrasiya (ln HHI, t−1), bazarın ölçüsü (ln gəlir, t−1), region və il sabit effektləri üzrə (+ bölmə sabit effektləri ilə variant) | NACE bölməsi (iki rəqəmli) × region × il, t−1 ilində mövcud müəssisələri olan bazarlar | Puasson və mənfi binomial (NB2) maksimum həqiqətəbənzərlik; hadisə tezliyi nisbətləri (IRR); bazar üzrə klasterləşdirilmiş standart xətalar |
# | (b) | çıxış: müddət fiktiv dəyişənləri, ölçü qrupu, sektor artımı, konsentrasiya, mülkiyyət, bölmə / region / il sabit effektləri üzrə diskret zamanlı təhlükə (hazard) modeli | müəssisə-il risk dəsti (yaş ≥ 1; yaş 0 yalnız çıxışları olduqda daxil olur) | Binomial GLM, logistik əlaqə (şans nisbətləri) və tamamlayıcı log-log əlaqəsi (qruplaşdırılmış zaman üzrə proporsional təhlükələr: təhlükə nisbətləri); tezlik çəkiləri; bölmə × region üzrə klasterləşdirilmiş standart xətalar; Kaplan–Meier ilə proqnozlaşdırılan sağ qalmanın müqayisəsi |
# | (c) | 95% etibarlılıq intervalı ilə hər bölmə-il üzrə Boone göstəricisi; birləşdirilmiş Boone reqressiyası (ortaq meyl + trend və bölmə meylləri) | mənfəətli müəssisələr | udulmuş bölmə × il effektləri ilə WLS; qeyd üzrə klasterləşdirilmiş standart xətalar |
# | (d) | struktur–davranış–nəticə (SCP): PCM-in ln HHI, ixrac intensivliyi (idxal payı reyestrdə yoxdur — gömrük məlumatları sorğu edilib, matris I21), ln ölçü üzrə reqressiyası | bölmə (iki rəqəmli) × il | bölmə və il sabit effektləri ilə OLS, bölmə (iki rəqəmli) üzrə klasterləşdirilmiş standart xətalar; aşağıda **endogenlik qeydi** |
# | (e) | bazar paylarının mobilliyinin (payların qeyri-sabitliyi, sıra mobilliyi) konsentrasiya (t−1), giriş əmsalı, ölçü (t−1), tələbin artımı üzrə reqressiyası | bölmə (iki rəqəmli) × il | il sabit effektləri ilə OLS, bölmə (iki rəqəmli) üzrə klasterləşdirilmiş standart xətalar |
# | (f) | daxil olanların ölçüsü və girişdən sonrakı artım: nisbi ölçünün yaş profili; yaşa görə nisbi ölçünün artımı (fərq, **gecikmiş asılı dəyişən yoxdur**); kohort × yaş cədvəli | müəssisə-il | udulmuş bölmə × il × ölçü qrupu effektləri ilə WLS; qeyd üzrə klasterləşdirilmiş standart xətalar |
# | (g) | generatorun həqiqi dəyərlərinə qarşı parametrlərin bərpası (yalnız SİNTETİK) | (b), (f) kimi | qiymətləndirilmiş və həqiqi dəyər, 95% etibarlılıq intervalının əhatəsi |
#
# **Endogenlik qeydi (d).** Konsentrasiya və marjalar birgə müəyyən olunur: səmərəli müəssisələr böyüyür, bu da həm onların
# payını, həm də marjasını artırır (Demsetz), giriş isə marjalara reaksiya verir. SCP meyli konsentrasiyanın qiymətlərə
# səbəbli təsiri deyil, şərti əlaqədir. Reyestr heç bir alət (məsələn, ekzogen giriş xərcləri və ya birləşmə hadisələri)
# vermir; meyl bu qeydlə verilir və heç bir proqnozda istifadə olunmur.

# %%
from statsmodels.genmod import families as _fam
ECON_TAG = {'SYNTHETIC': 'sintetik məlumat — texniki nümayiş', 'REAL': 'real reyestr məlumatı'}
AGE_BANDS = [('age0', 0, 0), ('age1', 1, 1), ('age2', 2, 2), ('age3_4', 3, 4), ('age5_9', 5, 9)]     # reference: age 10+
SIZE_D, OWN_D = ['small', 'medium', 'large'], ['state', 'municipal', 'foreign', 'joint']             # references: micro, private

def econ_prep(P, LB):
    '''Firm-year frame with the regressors of models (a)-(g); local market = NACE division x region.'''
    P = P.copy(); P['w'] = wcol(P)
    P['sec'] = P.nace2.map(DIV2SEC); P['grp'] = P.sec.map(lambda s: SECT[s][3])
    P['reg_year'] = pd.to_datetime(P.registration_date).dt.year.astype(int)
    for c in ['revenue', 'cost_of_sales', 'operating_costs', 'exports']:
        P[c] = pd.to_numeric(P[c], errors='coerce') if c in P else np.nan      # optional cost / export fields may be absent
    P['age'] = (P.year - P.reg_year).astype(int)
    P['event'] = (P.status == 'liquidated').astype(float)
    P['cell'] = P.sec + '|' + P.region; P['mkt'] = P.nace2 + '|' + P.region
    dem = {g: dln(VAH[g]) for g in GRP}                      # FR1 sector real value added growth, % (history)
    P['dem'] = [float(dem[g].get(y, np.nan)) for g, y in zip(P.grp, P.year)]
    cr = LB['concentration_nace_region'][['nace2', 'region', 'year', 'HHI', 'revenue']]
    lag = cr.assign(year=cr.year + 1).rename(columns={'HHI': 'hhi_l1', 'revenue': 'mrev_l1'})
    P = P.merge(lag, on=['nace2', 'region', 'year'], how='left')
    P['ln_hhi_l1'] = np.log(P.hhi_l1.where(P.hhi_l1 > 0))
    return P

def _dummies(s, levels, prefix=''):
    return pd.DataFrame({f'{prefix}{v}': (s == v).astype(float).to_numpy() for v in levels}, index=s.index)

def _fe(s, prefix):
    lv = sorted(pd.Series(s).dropna().unique())
    return _dummies(s, lv[1:], prefix)

def _drop_eventless(X, ev, w, cols):
    '''Categorical dummy with no (weighted) event: the category is not identified (separation) -> its rows leave the
    risk set and the column is dropped. Returns the row mask and the dropped columns.'''
    keep = pd.Series(True, index=X.index); dropped = []
    for c in cols:
        if c in X and X[c].sum() > 0 and float((X[c] * ev * w).sum()) == 0.0:
            keep &= X[c] == 0; dropped.append(c)
    return keep, dropped

def ratio_table(model_id, res, kind, names=None, cov='', n=None):
    '''Tidy coefficient rows; kind = IRR | OR | HR | coef (normal inference for ML, as statsmodels reports).'''
    b, se = pd.Series(res.params), pd.Series(res.bse); p = pd.Series(res.pvalues); ci = pd.DataFrame(res.conf_int())
    ci.columns = ['lo', 'hi']; names = names or list(b.index); rows = []
    for c in names:
        r = dict(model=model_id, term=c, coef=float(b[c]), se=float(se[c]), z=float(b[c] / se[c]) if se[c] > 0 else np.nan, p=float(p[c]),
                 ci_low=float(ci.loc[c, 'lo']), ci_high=float(ci.loc[c, 'hi']), ratio_type=kind, n=n, cov_type=cov)
        if kind != 'coef':
            r.update(ratio=float(np.exp(b[c])), ratio_ci_low=float(np.exp(ci.loc[c, 'lo'])), ratio_ci_high=float(np.exp(ci.loc[c, 'hi'])))
        rows.append(r)
    return pd.DataFrame(rows)

def lb_entry(P):
    '''(a) entrants per NACE division x region x year, markets with incumbents at t-1.'''
    a = P.assign(_e=P.w * (P.reg_year == P.year), _a=P.w * (P.status == 'active'))
    m = a.groupby(['nace2', 'region', 'year']).agg(entrants=('_e', 'sum'), active=('_a', 'sum'), sec=('sec', 'first'),
                                                    dem=('dem', 'first'), ln_hhi_l1=('ln_hhi_l1', 'first'), mrev_l1=('mrev_l1', 'first')).reset_index()
    act_l1 = m[['nace2', 'region', 'year', 'active']].assign(year=m.year + 1).rename(columns={'active': 'active_l1'})
    m = m.merge(act_l1, on=['nace2', 'region', 'year'], how='left')
    m = m[(m.active_l1 > 0) & (m.mrev_l1 > 0) & m.ln_hhi_l1.notna() & m.dem.notna()].reset_index(drop=True)
    m['ln_size_l1'] = np.log(m.mrev_l1); m['entrants'] = m.entrants.round()
    base = m[['dem', 'ln_hhi_l1', 'ln_size_l1']]
    X0 = sm.add_constant(pd.concat([base, _fe(m.region, 'reg_'), _fe(m.year, 'yr_')], axis=1))
    X1 = sm.add_constant(pd.concat([base, _fe(m.region, 'reg_'), _fe(m.year, 'yr_'), _fe(m.sec, 'sec_')], axis=1))
    g = m.nace2 + '|' + m.region; ck = dict(cov_type='cluster', cov_kwds={'groups': pd.factorize(g)[0]})
    out = {}
    pois = sm.Poisson(m.entrants, X0).fit(disp=0, maxiter=300, **ck)
    out['entry_poisson'] = dict(res=pois, y=m.entrants, X=X0, kind='IRR', data=m)
    nb = sm.NegativeBinomial(m.entrants, X0, loglike_method='nb2').fit(start_params=np.append(pois.params.values, 1.0), disp=0, maxiter=300, **ck)
    out['entry_nb2'] = dict(res=nb, y=m.entrants, X=X0, kind='IRR', data=m)
    out['entry_poisson_secfe'] = dict(res=sm.Poisson(m.entrants, X1).fit(disp=0, maxiter=300, **ck), y=m.entrants, X=X1, kind='IRR', data=m)
    llp, lln = pois.llf, nb.llf
    out['_overdispersion'] = dict(alpha=float(nb.params['alpha']), alpha_se=float(nb.bse['alpha']), lr=float(2 * (lln - llp)),
                                  lr_p=float(0.5 * stats.chi2.sf(2 * (lln - llp), 1)))      # boundary: half chi2(1)
    return out

def lb_exit(P):
    '''(b) discrete-time hazard on the enterprise-year risk set, frequency-weighted; logit and cloglog.'''
    R = P[(P.age >= 0) & P.ln_hhi_l1.notna() & P.dem.notna()].copy()
    if float((R.event * R.w)[R.age == 0].sum()) == 0: R = R[R.age >= 1]            # no exit in the registration year
    bands = [b for b in AGE_BANDS if (R.age.between(b[1], b[2])).any() and not (b[0] == 'age0' and (R.age == 0).sum() == 0)]
    A = pd.DataFrame({nm: R.age.between(lo, hi).astype(float) for nm, lo, hi in bands}, index=R.index)
    X = pd.concat([A, _dummies(R.size_class, SIZE_D), _dummies(R.ownership, OWN_D), R[['dem', 'ln_hhi_l1']],
                   _fe(R.year, 'yr_'), _fe(R.sec, 'sec_'), _fe(R.region, 'reg_')], axis=1)
    keep, dropped = _drop_eventless(X, R.event, R.w, [c for c in X.columns if c not in ('dem', 'ln_hhi_l1')])
    R, X = R[keep], X[keep]
    X = sm.add_constant(X.loc[:, (X != 0).any() & (X.nunique() > 1)])
    ck = dict(cov_type='cluster', cov_kwds={'groups': pd.factorize(R.cell)[0]})
    lg = sm.GLM(R.event, X, family=_fam.Binomial(), freq_weights=R.w).fit(**ck)
    cl = sm.GLM(R.event, X, family=_fam.Binomial(link=_fam.links.CLogLog()), freq_weights=R.w).fit(start_params=lg.params.values * 0.98, **ck)
    return dict(exit_logit=dict(res=lg, y=R.event, X=X, kind='OR', data=R), exit_cloglog=dict(res=cl, y=R.event, X=X, kind='HR', data=R),
                _dropped=dropped, _bands=[b[0] for b in bands])

def predicted_survival(P, LB, ex):
    '''Cohort survival implied by each hazard model vs Kaplan-Meier: each entrant's hazard at ages 1..(last year - cohort),
    covariates fixed at entry, calendar effects and demand growth of the year, market HHI of the previous year.'''
    R = ex['exit_logit']['data']; ylast = int(P.year.max()); y0 = int(P.year.min())
    first = P[(P.reg_year >= y0) & (P.year == P.reg_year)].drop_duplicates('firm_id')
    hhi = LB['concentration_nace_region'].pivot_table(index='year', columns=['nace2', 'region'], values='HHI').sort_index().ffill()
    dem = {g: dln(VAH[g]) for g in GRP}; rows = []
    a0 = 0 if 'age0' in ex['exit_logit']['X'] else 1                 # age 0 is in the risk set only if it has exits
    for _, f in first.iterrows():
        for a in range(a0, ylast - int(f.reg_year) + 1):
            y = int(f.reg_year) + a; hk = (f.nace2, f.region)
            h_ = hhi[hk].get(y - 1, np.nan) if hk in hhi.columns else np.nan
            rows.append(dict(firm_id=f.firm_id, cohort=int(f.reg_year), w=f.w, age=a, year=y, size_class=f.size_class, ownership=f.ownership,
                             sec=f.sec, region=f.region, dem=float(dem[f.grp].get(y, np.nan)), ln_hhi_l1=np.log(h_) if h_ > 0 else np.nan))
    Gd = pd.DataFrame(rows)
    out = LB['survival_km'][['cohort', 'age', 'survival', 'cohort_size']].rename(columns={'survival': 'km_survival'}).copy()
    if Gd.empty: return out
    Gd['ln_hhi_l1'] = Gd.ln_hhi_l1.fillna(R.ln_hhi_l1.median())
    for key, col in [('exit_logit', 'pred_logit'), ('exit_cloglog', 'pred_cloglog')]:
        X = ex[key]['X']; cols = [c for c in X.columns if c != 'const']; Z = pd.DataFrame(0.0, index=Gd.index, columns=cols)
        for nm, lo, hi in AGE_BANDS:
            if nm in Z: Z[nm] = Gd.age.between(lo, hi).astype(float)
        for c in SIZE_D + OWN_D:
            if c in Z: Z[c] = ((Gd.size_class == c) | (Gd.ownership == c)).astype(float)
        Z['dem'] = Gd.dem; Z['ln_hhi_l1'] = Gd.ln_hhi_l1
        for pre, s in [('yr_', Gd.year), ('sec_', Gd.sec), ('reg_', Gd.region)]:
            for c in [c for c in cols if c.startswith(pre)]: Z[c] = (s.astype(str) == c[len(pre):]).astype(float)
        h = ex[key]['res'].predict(sm.add_constant(Z, has_constant='add')[X.columns])
        Gd['s'] = 1 - np.asarray(h, float)
        Gd['S'] = Gd.sort_values('age').groupby('firm_id').s.cumprod()
        cur = Gd.assign(k=Gd.age + 1).groupby(['cohort', 'k']).apply(lambda d: np.average(d.S, weights=d.w)).rename(col).reset_index().rename(columns={'k': 'age'})
        out = out.merge(cur, on=['cohort', 'age'], how='left')
        out.loc[out.age <= a0, col] = out.loc[out.age <= a0, col].fillna(1.0)   # before the first age at risk survival is 1
    return out
