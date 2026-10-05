# %% [markdown]
# ### 17.4b Müəssisə səviyyəli ekonometrika (v2): qiymətləndiricilər
#
# Eyni kod yüklənmiş istənilən müəssisə paneli üzərində işləyir — hazırda SİNTETİK panel, Vergi Xidmətinin / DSMF-nin
# paneli daxil olduqda isə həmin panel (DATA_MODE = REAL). Hər model tam reqressiya nəticəsini (əmsallar, standart
# xətalar, t, p, 95% intervallar, müəssisələrin və müşahidələrin sayı, uyğunluq və diaqnostika) verir və tənliklər
# reyestrinə yazılır.
#
# * **İki yönlü sabit effektlər (müəssisə + il)**: balanslaşdırılmamış panel üzrə müəssisələrə görə dəqiq within
#   çevrilməsi, il fiktiv dəyişənləri (dummy) çıxarılır (Frisch–Waugh), yalnız bir dəfə müşahidə olunanlar (singletons)
#   atılır; $G/(G-1)\cdot(N-1)/(N-K)$ düzəlişi və $t(G-1)$ üzrə statistik nəticə ilə **müəssisələr üzrə klasterə davamlı
#   standart xətalar**.
# * **NACE × il sabit effektləri ilə birləşdirilmiş OLS** (xana fiktiv dəyişənləri), eyni klasterləşdirmə ilə.
# * **Logit** (maksimum həqiqətəbənzərlik, müəssisələr üzrə klasterə davamlı) orta marjinal effektlər (AME), ROC/AUC,
#   Brier göstəricisi və kalibrləmə cədvəli ilə.
#
# Hər qiymətləndirmə statsmodels ilə hesablanır və əmsalların və klasterli kovariasiyanın müstəqil numpy hesablaması ilə
# tutuşdurulur (1e-8 dəqiqliklə yoxlama ifadəsi ilə təsdiqlənir). Heç bir modeldə gecikmiş asılı dəyişən yoxdur;
# gecikmiş izahedici dəyişənlər əvvəlcədən müəyyən olunmuş digər dəyişənlərdir.

# %%
import statsmodels.api as sm
class EFit:
    def __init__(self, **kw): self.__dict__.update(kw)

def _cluster_V(X, u, g, XtXi=None):
    '''CR1 cluster covariance, statsmodels convention: G/(G-1) * (N-1)/(N-K).'''
    n, k = X.shape; XtXi = np.linalg.pinv(X.T @ X) if XtXi is None else XtXi
    gu, gi = np.unique(g, return_inverse=True); G = len(gu)
    sc = np.zeros((G, k)); np.add.at(sc, gi, X * u[:, None])
    return XtXi @ (sc.T @ sc) @ XtXi * G / (G - 1) * (n - 1) / (n - k), G

def _demean(df, cols, by):
    return df[cols] - df.groupby(by)[cols].transform('mean')

def econ_ols(d, y, xs, fe='firm+year', cluster='firm_id', check=True, fast=False):
    '''fe: 'firm+year' (within by firm, year dummies partialled out) or 'nace_year' (pooled, NACE x year dummies)
    or 'nace+year' (pooled, NACE and year dummies). Returns EFit with statsmodels results (unless fast).'''
    s = d.dropna(subset=[y] + xs).copy()
    if fe == 'firm+year':
        s = s[s.groupby('firm_id').year.transform('size') > 1]
        yd = pd.get_dummies(s.year.astype(int), prefix='yr', drop_first=True, dtype=float)
        Z = pd.concat([s[xs].astype(float), yd], axis=1); Z['__y'] = s[y].astype(float)
        Zd = _demean(pd.concat([Z, s[['firm_id']]], axis=1), list(Z.columns), 'firm_id')
        X = Zd.drop(columns='__y'); X = X.loc[:, X.abs().sum() > 1e-10]; yv = Zd['__y'].to_numpy(float)
    else:
        key = s.nace2 + '_' + s.year.astype(int).astype(str) if fe == 'nace_year' else None
        dm = (pd.get_dummies(key, prefix='cell', drop_first=True, dtype=float) if fe == 'nace_year' else
              pd.concat([pd.get_dummies(s.nace2, prefix='nace', drop_first=True, dtype=float),
                         pd.get_dummies(s.year.astype(int), prefix='yr', drop_first=True, dtype=float)], axis=1))
        X = pd.concat([pd.Series(1.0, index=s.index, name='const'), s[xs].astype(float), dm], axis=1)
        X = X.loc[:, (X != 0).any()]; yv = s[y].to_numpy(float)
    Xv = X.to_numpy(float); g = s[cluster].to_numpy()
    XtXi = np.linalg.pinv(Xv.T @ Xv); b = XtXi @ Xv.T @ yv; u = yv - Xv @ b
    V, G = _cluster_V(Xv, u, g, XtXi); se = np.sqrt(np.maximum(np.diag(V), 0))
    ix = [list(X.columns).index(c) for c in xs]
    res = None
    if not fast:
        res = sm.OLS(yv, Xv).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(g)[0]}, use_t=True)
        if check:
            db = float(np.max(np.abs(res.params - b) / np.maximum(np.abs(b), 1.0)))
            dse = float(np.max(np.abs(res.bse[ix] - se[ix]) / np.maximum(se[ix], 1e-12)))
            assert db < 1e-8 and dse < 1e-8, f'{y}: statsmodels vs numpy mismatch (b {db:.1e}, se {dse:.1e})'
    n, k = Xv.shape
    tss = ((yv - yv.mean()) ** 2).sum() if fe != 'firm+year' else (yv ** 2).sum()
    r2 = 1 - (u @ u) / tss
    bb, Vb = b[ix], V[np.ix_(ix, ix)]
    F = float(bb @ np.linalg.pinv(Vb) @ bb) / len(ix)
    return EFit(kind='ols', fe=fe, y=y, xs=list(xs), b=pd.Series(bb, index=xs), se=pd.Series(se[ix], index=xs), V=Vb,
                dof=G - 1, n=n, k=k, G=G, firms=int(s.firm_id.nunique()), years=sorted(s.year.astype(int).unique()),
                r2=float(r2), r2_adj=float(1 - (1 - r2) * (n - 1) / max(n - k - (s.firm_id.nunique() if fe == 'firm+year' else 0), 1)),
                ser=float(np.sqrt((u @ u) / max(n - k, 1))), F=F, F_p=float(1 - stats.f.cdf(F, len(ix), G - 1)),
                res=res, resid=u, fitted=yv - u, yv=yv, X=X[xs] if fe != 'firm+year' else s[xs], sample=s, cluster=cluster,
                y_raw=s[y].to_numpy(float))

def econ_logit(d, y, xs, dummies=('year',), cluster='firm_id', fast=False):
    s = d.dropna(subset=[y] + xs).copy()
    parts = [pd.Series(1.0, index=s.index, name='const'), s[xs].astype(float)]
    for dm in dummies:
        parts.append(pd.get_dummies(s[dm].astype(str), prefix=dm, drop_first=True, dtype=float))
    X = pd.concat(parts, axis=1); X = X.loc[:, (X != 0).any()]
    yv = s[y].astype(float).to_numpy(); g = pd.factorize(s[cluster])[0]
    mod = sm.Logit(yv, X)
    res = mod.fit(disp=0, maxiter=300, method='newton', cov_type='cluster', cov_kwds={'groups': g})
    p = res.predict(X)
    out = EFit(kind='logit', y=y, xs=list(xs), b=res.params[xs], se=res.bse[xs], V=res.cov_params().loc[xs, xs].to_numpy(),
               dof=None, n=len(s), k=X.shape[1], G=int(len(np.unique(g))), firms=int(s.firm_id.nunique()),
               years=sorted(s.year.astype(int).unique()), res=res, prob=np.asarray(p), yv=yv, X=s[xs], sample=s,
               cluster=cluster, dummies=list(dummies), r2=float(res.prsquared), llf=float(res.llf),
               lr=float(res.llr), lr_p=float(res.llr_pvalue), aic=float(res.aic), bic=float(res.bic))
    if not fast:
        me = res.get_margeff(at='overall', method='dydx').summary_frame()
        out.ame = me.loc[[c for c in xs if c in me.index]].rename(columns={'dy/dx': 'ame', 'Std. Err.': 'se', 'Pr(>|z|)': 'p',
                                                                             'Conf. Int. Low': 'ci_low', 'Cont. Int. Hi.': 'ci_high'})
        out.auc = auc(yv, p); out.brier = float(np.mean((p - yv) ** 2)); out.calib = calibration(yv, p)
        out.hl_stat, out.hl_p = hosmer_lemeshow(yv, p)
    return out

def auc(y, p):
    '''Area under the ROC curve = Mann-Whitney probability (ties counted one half).'''
    y = np.asarray(y, float); r = stats.rankdata(p); n1 = y.sum(); n0 = len(y) - n1
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)) if n1 and n0 else np.nan

def roc_points(y, p, n=101):
    th = np.quantile(p, np.linspace(0, 1, n))[::-1]
    y = np.asarray(y, bool)
    return pd.DataFrame({'threshold': th, 'tpr': [(p[y] >= t).mean() for t in th], 'fpr': [(p[~y] >= t).mean() for t in th]})

def calibration(y, p, q=10):
    b = pd.qcut(pd.Series(p).rank(method='first'), q, labels=False)
    t = pd.DataFrame({'bin': b, 'p': p, 'y': y}).groupby('bin').agg(n=('y', 'size'), mean_predicted=('p', 'mean'),
                                                                   observed_rate=('y', 'mean'))
    t.index = t.index + 1
    return t.rename_axis('decile')

def hosmer_lemeshow(y, p, q=10):
    c = calibration(y, p, q); e = c.n * c.mean_predicted; o = c.n * c.observed_rate
    hl = float((((o - e) ** 2) / (e * (1 - c.mean_predicted)).clip(lower=1e-12)).sum())
    return hl, float(1 - stats.chi2.cdf(hl, q - 2))

def year_paths(fitfun, years, names, n_min_years=3):
    '''Recursive (expanding window over years) and leave-one-year-out coefficient paths (registry robustness).'''
    rec = dict(years=[], coef={c: [] for c in names}, se={c: [] for c in names}, n_min=n_min_years)
    loo = dict(years=[], coef={c: [] for c in names})
    for i, yr in enumerate(years):
        if i + 1 >= n_min_years:
            try:
                b, s_ = fitfun(lambda d: d[d.year <= yr])
                rec['years'].append(int(yr)); [rec['coef'][c].append(float(b[c])) or rec['se'][c].append(float(s_[c])) for c in names]
            except Exception:
                pass
        try:
            b, _ = fitfun(lambda d: d[d.year != yr])
            loo['years'].append(int(yr)); [loo['coef'][c].append(float(b[c])) for c in names]
        except Exception:
            pass
    loo['range'] = {c: ([min(v), max(v)] if v else None) for c, v in loo['coef'].items()}
    return rec, loo
print('firm-level estimators defined: econ_ols (two-way FE / pooled NACE x year FE, cluster by firm, statsmodels-checked), '
      'econ_logit (cluster by firm, AME, AUC, calibration), year_paths (recursive / leave-one-year-out)')
