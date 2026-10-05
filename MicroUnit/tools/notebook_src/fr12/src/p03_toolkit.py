# %% [markdown]
# ## Hissə 3 — Ekonometrik alətlər
#
# Qiymətləndiricilər **FR1, FR4, FR5 və FR10-dakı kodun eynisidir** (notebook-un müstəqil olması üçün köçürülüb); beləliklə,
# bütün modullar vahid kovariasiya qaydasından istifadə edir. Giriş, çıxış və dövriyyə (churn) *əmsalları* stoxastik trendi
# olmayan məhdud nisbətlərdir, buna görə FR12-də qiymətləndiriləcək uzunmüddətli səviyyə əlaqəsi yoxdur: FR10-un DOLS və
# Engle–Granger/MacKinnon mexanizmi burada lazım deyil və bu, formal olaraq tətbiq edilmək əvəzinə açıq göstərilir.
#
# | Funksiya | Nə edir |
# |---|---|
# | `ols` | n/(n−k) ilə miqyaslanmış Newey–West HAC kovariasiyası ilə OLS; p-dəyərləri t(n−k) paylanmasından |
# | `wald_F` | Xətti məhdudiyyətlərin HAC-F testi, F(m, n−k) |
# | `dm_hln`, `dm_by_year` | Harvey–Leybourne–Newbold düzəlişi ilə Diebold–Mariano; `dm_by_year` itkini əvvəlcə hədəf ili üzrə orta hesablayır (üst-üstə düşməyə davamlı) — ≥ 3 hədəf ili tələb edir, buna görə FR12-nin nümunədən kənar yoxlaması (1–2 hədəf ili) əvəzində vahidlər üzrə cütləşdirilmiş testdən istifadə edir |
# | `panel_fe` | Sabit effektlər (bir və ya iki yönlü, balanslaşdırılmamış panellərdə növbəli proyeksiyalarla dəqiq), ⌊T^¼⌋ gecikmə ilə Driscoll–Kraay standart xətaları və **t(T−1)** üzrə statistik nəticə |
# | `wild_cluster_p` | İllər üzrə klasterli vəhşi (wild) butstrap-t, Webb altı nöqtəli çəkiləri, sıfır fərziyyəsi qoyulmaqla |
# | `between_fit` | Vahidlərin ortaları üzrə between qiymətləndiricisi (kəsişmə üzrə əlaqə, within təsirindən fərqlidir) |
# | `theil` | Theil U = RMSE(model) / RMSE(müqayisə meyarı) |
#
# Təriflərdən sonrakı xana onları simulyasiya edilmiş məlumatlar üzərində statsmodels ilə 1e-8 dəqiqliklə yoxlayır.

# %%
class Fit:
    def __init__(self, **kw): self.__dict__.update(kw)
    def table(self, digits=4):
        t = pd.DataFrame({'coef': self.beta, 'se': self.se, 't': self.tstat, 'p': self.pval}, index=self.names)
        t['sig'] = ['***' if p < .01 else '**' if p < .05 else '*' if p < .10 else '' for p in self.pval]
        return t.round(digits)

def _prep(y, X, add_const=True):
    d = pd.concat([y.rename('__y__'), X], axis=1).dropna()
    yv = d['__y__'].to_numpy(float); Xv = d.drop(columns='__y__').to_numpy(float)
    names = [c for c in d.columns if c != '__y__']
    if add_const:
        Xv = np.column_stack([np.ones(len(Xv)), Xv]); names = ['const'] + names
    return yv, Xv, names, d.index

def hac_cov(X, u, XtXi, lags=None):
    '''Newey-West HAC covariance: corrects INFERENCE for residual dependence; no lag enters the model.'''
    n = len(X)
    if lags is None: lags = max(1, int(np.floor(4 * (n / 100) ** (2 / 9))))
    Xu = X * u[:, None]; S = Xu.T @ Xu
    for L_ in range(1, lags + 1):
        G = Xu[L_:].T @ Xu[:-L_]; S += (1 - L_ / (lags + 1)) * (G + G.T)
    return XtXi @ S @ XtXi

def ols(y, X, cov='hac', lags=None, add_const=True):
    yv, Xv, names, idx = _prep(y, X, add_const)
    n, k = Xv.shape
    XtXi = np.linalg.pinv(Xv.T @ Xv); b = XtXi @ Xv.T @ yv; u = yv - Xv @ b
    dof = max(n - k, 1)
    if   cov == 'hac': V = hac_cov(Xv, u, XtXi, lags) * n / dof
    elif cov == 'hc1': V = XtXi @ ((Xv * u[:, None]).T @ (Xv * u[:, None])) @ XtXi * n / dof
    else:              V = XtXi * (u @ u) / dof
    se = np.sqrt(np.maximum(np.diag(V), 0))
    with np.errstate(divide='ignore', invalid='ignore'): t = b / se
    tss = ((yv - yv.mean()) ** 2).sum() if add_const else (yv ** 2).sum()
    r2 = 1 - (u @ u) / tss if tss > 0 else np.nan
    return Fit(kind=f'OLS[{cov}]', beta=b, se=se, tstat=t, pval=2 * (1 - stats.t.cdf(np.abs(t), dof)),
               names=names, n=n, k=k, r2=r2, V=V, X=Xv, y=yv, index=idx, dof=dof,
               resid=pd.Series(u, index=idx), fitted=pd.Series(Xv @ b, index=idx), sigma2=(u @ u) / dof)

def wald_F(fit, R, q):
    '''HAC-F test of R beta = q against F(m, n-k).'''
    R = np.atleast_2d(np.asarray(R, float)); q = np.atleast_1d(np.asarray(q, float))
    d = R @ fit.beta - q; Vr = R @ fit.V @ R.T
    m = R.shape[0]; Fs = float(d @ np.linalg.pinv(Vr) @ d) / m
    return Fs, float(1 - stats.f.cdf(Fs, m, fit.dof))

from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.adfvalues import mackinnonp
def dm_hln(loss1, loss2, h=1):
    '''Diebold-Mariano with the HLN small-sample correction, t(T-1). Negative = model 1 has lower loss.'''
    d = np.asarray(loss1, float) - np.asarray(loss2, float)
    d = d[np.isfinite(d)]; T = len(d)
    if T < 3 or np.allclose(d, 0): return np.nan, 1.0
    h = int(max(1, min(h, T // 3))); db = d.mean()
    g = [np.mean((d[k:] - db) * (d[:T - k] - db)) for k in range(h)]
    V = (g[0] + 2 * sum(g[1:])) / T
    if V <= 0: V = g[0] / T
    s = db / np.sqrt(V) * np.sqrt(max((T + 1 - 2 * h + h * (h - 1) / T) / T, 1e-12))
    return float(s), float(2 * (1 - stats.t.cdf(abs(s), T - 1)))

def dm_by_year(loss1, loss2, h=2):
    '''Overlap-robust DM: losses indexed (origin, target year) are averaged by TARGET YEAR first, so overlapping
    origins that score the same year contribute one observation; then DM/HLN on the year series.'''
    a = pd.Series(loss1).groupby(level=1).mean(); b = pd.Series(loss2).groupby(level=1).mean()
    yrs = a.index.intersection(b.index)
    s, p = dm_hln(a.loc[yrs].values, b.loc[yrs].values, h=h)
    return s, p, len(yrs)

def _within(df, dep, regs, entity, time, twoway):
    d = df[[entity, time, dep] + regs].dropna().copy()
    for c in [dep] + regs:
        if twoway:
            # alternating projections: exact two-way within transformation on an UNBALANCED panel (equals LSDV)
            x = d[c].astype(float)
            for _ in range(10000):
                x_new = x - x.groupby(d[entity]).transform('mean')
                x_new = x_new - x_new.groupby(d[time]).transform('mean')
                if float((x_new - x).abs().max()) < 1e-13: x = x_new; break
                x = x_new
            d[c] = x
        else:
            d[c] = d[c] - d.groupby(entity)[c].transform('mean')
    return d

def panel_fe(df, dep, regs, entity='unit', time='year', twoway=True, dk_lags=None):
    '''Two-way FE within estimator; Driscoll-Kraay SEs, bandwidth floor(T^(1/4)); t(T-1) inference because the
    DK variance is built from T year-level score sums.'''
    d = _within(df, dep, regs, entity, time, twoway)
    yv = d[dep].to_numpy(float); Xv = d[regs].to_numpy(float)
    XtXi = np.linalg.pinv(Xv.T @ Xv); b = XtXi @ Xv.T @ yv; u = yv - Xv @ b
    nN, nT = d[entity].nunique(), d[time].nunique()
    if dk_lags is None: dk_lags = int(np.floor(nT ** 0.25))
    k = len(regs) + nN + (nT - 1 if twoway else 0)
    ht = pd.DataFrame(Xv * u[:, None], index=d[time].to_numpy()).groupby(level=0).sum().sort_index().to_numpy()
    S = ht.T @ ht
    for L_ in range(1, dk_lags + 1):
        G = ht[L_:].T @ ht[:-L_]; S += (1 - L_ / (dk_lags + 1)) * (G + G.T)
    V = XtXi @ S @ XtXi * (len(d) / max(len(d) - k, 1))
    se = np.sqrt(np.maximum(np.diag(V), 0)); t = b / se; dof = max(nT - 1, 1)
    r2 = 1 - (u @ u) / (yv @ yv) if (yv @ yv) > 0 else np.nan
    return Fit(kind='two-way FE [Driscoll-Kraay]' if twoway else 'entity FE [DK]', beta=b, se=se, tstat=t,
               pval=2 * (1 - stats.t.cdf(np.abs(t), dof)), names=regs, n=len(d), k=k, r2=r2, V=V,
               resid=pd.Series(u, index=d.index), nN=nN, nT=nT, dof=dof, dk_lags=dk_lags)

WEBB6 = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])

def wild_cluster_p(df, dep, regs, test, entity='unit', time='year', twoway=True, B=999, seed=None):
    '''Wild cluster bootstrap-t (null imposed), clusters = years, Webb six-point weights, CR1 t-statistics.'''
    d = _within(df, dep, regs, entity, time, twoway)
    yv = d[dep].to_numpy(float); Xv = d[regs].to_numpy(float)
    tt = d[time].to_numpy(); ug = np.unique(tt); G = len(ug); gi = np.searchsorted(ug, tt)
    j = regs.index(test); XtXi = np.linalg.pinv(Xv.T @ Xv)
    def tstat(y_):
        b = XtXi @ Xv.T @ y_; u = y_ - Xv @ b
        sc = np.zeros((G, Xv.shape[1])); np.add.at(sc, gi, Xv * u[:, None])
        V = XtXi @ (sc.T @ sc) @ XtXi * G / max(G - 1, 1)
        return b[j] / np.sqrt(max(V[j, j], 1e-300))
    t0 = tstat(yv)
    Xr = np.delete(Xv, j, axis=1)
    fr = Xr @ (np.linalg.pinv(Xr.T @ Xr) @ Xr.T @ yv) if Xr.shape[1] else np.zeros_like(yv)
    ur = yv - fr
    rg = np.random.default_rng(SEED if seed is None else seed)
    W = rg.choice(WEBB6, size=(B, G))
    ts = np.array([tstat(fr + ur * W[b_, gi]) for b_ in range(B)])
    return float(np.mean(np.abs(ts) >= abs(t0))), float(t0)

def between_fit(df, dep, regs, entity='unit'):
    '''Between estimator: OLS on unit means (HC1). Cross-sectional association, NOT a within-unit effect.'''
    m = df[[entity, dep] + regs].dropna().groupby(entity).mean()
    return ols(m[dep], m[regs], cov='hc1')

def theil(m, b):
    a = float(np.sqrt(np.nanmean(np.asarray(m, float) ** 2))); c = float(np.sqrt(np.nanmean(np.asarray(b, float) ** 2)))
    return a / c if c > 0 else np.nan

print('toolkit defined: ols, wald_F, dm_hln, dm_by_year, panel_fe (DK, t(T-1)), wild_cluster_p (Webb), between_fit, theil')

# %%
import statsmodels.api as sm
_rng = np.random.default_rng(SEED)
n = 80
Xt = pd.DataFrame(_rng.standard_normal((n, 3)), columns=['a', 'b', 'c'])
yt = pd.Series(1 + 2 * Xt.a - 1.5 * Xt.b + .5 * Xt.c + _rng.standard_normal(n) * .3, name='y')
rows = []
f0 = ols(yt, Xt, cov='nonrobust'); r0 = sm.OLS(yt, sm.add_constant(Xt)).fit()
rows.append(['OLS coefficients', np.abs(f0.beta - r0.params.values).max()])
rows.append(['OLS standard errors', np.abs(f0.se - r0.bse.values).max()])
f1 = ols(yt, Xt, cov='hc1'); r1 = sm.OLS(yt, sm.add_constant(Xt)).fit(cov_type='HC1')
rows.append(['HC1 robust SE', np.abs(f1.se - r1.bse.values).max()])
f2 = ols(yt, Xt, cov='hac', lags=3)
r2_ = sm.OLS(yt, sm.add_constant(Xt)).fit(cov_type='HAC', cov_kwds={'maxlags': 3, 'use_correction': True})
rows.append(['Newey-West HAC SE, n/(n-k) scaled', np.abs(f2.se - r2_.bse.values).max()])
pdf = pd.DataFrame({'unit': np.repeat(np.arange(10), 8), 'year': np.tile(np.arange(8), 10)})
pdf['x'] = _rng.standard_normal(80); pdf['y'] = 1 + 0.6 * pdf.x + pdf.unit * 0.3 + _rng.standard_normal(80) * .2
fp = panel_fe(pdf, 'y', ['x'], twoway=False)
dd = pdf.copy()
for c in ['y', 'x']: dd[c] = dd[c] - dd.groupby('unit')[c].transform('mean')
rows.append(['panel FE coefficient vs OLS on demeaned data', abs(fp.beta[0] - ols(dd.y, dd[['x']], cov='nonrobust').beta[1])])
_ub = pdf.drop(index=[3, 11, 12, 40, 41, 42, 77]).copy(); _ub['x2'] = _rng.standard_normal(len(_ub)) + _ub.year * 0.1
_f2 = panel_fe(_ub, 'y', ['x', 'x2'])
_D = pd.get_dummies(_ub[['unit', 'year']].astype(str), drop_first=True).astype(float)
_l = sm.OLS(_ub.y, sm.add_constant(pd.concat([_ub[['x', 'x2']], _D], axis=1))).fit()
rows.append(['two-way FE on an UNBALANCED panel vs dummy-variable OLS', float(np.abs(_f2.beta - _l.params[['x', 'x2']].values).max())])
_f1w = panel_fe(_ub, 'y', ['x', 'x2'], twoway=False)
_D1 = pd.get_dummies(_ub[['unit']].astype(str), drop_first=True).astype(float)
_l1 = sm.OLS(_ub.y, sm.add_constant(pd.concat([_ub[['x', 'x2']], _D1], axis=1))).fit()
rows.append(['one-way FE on an UNBALANCED panel vs dummy-variable OLS', float(np.abs(_f1w.beta - _l1.params[['x', 'x2']].values).max())])
chk = pd.DataFrame(rows, columns=['check', 'max abs difference'])
chk['verdict'] = np.where(chk['max abs difference'] < 1e-8, 'exact', 'MISMATCH')
display(chk)
assert (chk.verdict == 'exact').all(), 'estimator validation failed'
_s, _p = dm_hln(np.ones(20), np.ones(20) + _rng.standard_normal(20) * 0.01)
print(f'all estimators reproduce statsmodels to 1e-8 | DM/HLN on (nearly) equal losses p = {_p:.2f}')
