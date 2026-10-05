# %% [markdown]
# ## Hissə 11 — Sahə pay sistemi (5-ci məqsəd: FR1-ə şərtlənən bazar göstəriciləri)
#
# ### 11.1 Forma
#
# Sahələrin emal sənayesi buraxılışındakı nominal payları istinad sahəsinə (ən stabil böyük sahə olan qida məhsulları)
# nisbətən log-şans (log-odds) formasında **multinomial-logit pay sistemi** kimi modelləşdirilir:
#
# $$\ln\frac{w_{b,t}}{w_{r,t}} = \alpha_b + \beta_b \ln Y^{man}_t + \gamma_b \ln P^{oil}_t + u_{b,t},\qquad
#   w_{b,t} = \frac{e^{z_{b,t}}}{\sum_j e^{z_{j,t}}}$$
#
# $Y^{man}$ FR1-in emal sənayesi üzrə real əlavə dəyəridir (sektorun **miqyası**: emal sənayesi böyüdükdə hansı sahələr
# pay qazanır), $P^{oil}$ FR1-in neft ixrac qiymətidir (neft emalı, kimya və metallurgiya paylarının neft kompleksi ilə
# birgə dəyişdiyi **əlaqəli sektor** kanalı). Hər iki sürücü FR1 tərəfindən hər ssenaridə proqnozlaşdırılır; beləliklə,
# sahə proqnozu FR1-in trayektoriyalarına şərtlənir və ssenarilər üzrə fərqlənir. Softmax payların cəminin **dəqiq vahidə
# bərabər** olmasını təmin edir; toplanma struktur xüsusiyyətdir. Sahənin nominal buraxılışı = pay × FR1-dən irəli gələn
# emal sənayesi buraxılışı; sahənin real buraxılışı = nominal ÷ (FR1-in emal sənayesi deflyatoruna **nisbətən** 2025-ci il
# səviyyəsində saxlanılan sahə deflyatoru — qiymətləndirmə deyil, açıq göstərilmiş qayda).
#
# ### 11.2 Namizədlər, seçim və qərar qaydası
#
# | Namizəd | Sahə üzrə meyllər |
# |---|---|
# | sabit paylar (sıfır fərziyyəsi: log-şanslar lövbər ilində dondurulur) | 0 |
# | yalnız miqyas ilə MNL | 1 |
# | yalnız neft qiyməti ilə MNL | 1 |
# | miqyas + neft qiyməti ilə MNL | 2 |
# | kombinasiya: ½ sabit + ½ miqyas ilə MNL (FR4-ün proqnoz kombinasiyası) | 1 |
#
# Hər meyl DOLS qaydası ilə qiymətləndirilir; **uyğunluq qaydası** eyni tənliyin birinci fərqlərdəki 95% etibarlılıq
# intervalından kənarda qalan səviyyə meylini fərq formasındakı meyllə əvəz edir (bu, hər qiymətləndirmə pəncərəsinin
# daxilində qərara alınır); sonra sahə meylləri **dəqiqliklə çəkilmiş empirik Bayes** üsulu ilə ortaq dəyərə doğru
# büzülür (FR5-in qiymətləndiricisi: tam büzülmə = sabit paylar). Namizədlər 2011, 2013, 2015, 2017 sürüşən
# başlanğıclarında **bütün qiymətləndirmələr 2012–2019-cu illərdə olmaqla** müqayisə edilir; 2020–2025 heç vaxt seçim
# üçün istifadə olunmur. İtkilər hər (başlanğıc, hədəf ili) üzrə sahələr üzrə toplanır və Diebold–Mariano/HLN testi
# **hədəf ili üzrə orta hesablanmış** itkilər üzərində aparılır (üst-üstə düşməyə davamlı). Qayda, FR4/FR5-də olduğu kimi:
# ən yaxşıdan əhəmiyyətli dərəcədə pis olmayan (p > 0,10) namizədlər arasında ən az meylə malik olanı seçilir. Sonra
# büzülmə intensivliyi κ eyni pəncərələrdə eyni qayda ilə seçilir (əhəmiyyətli dərəcədə pis olmayan ən güclü büzülmə).

# %%
SHR_K = [0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 64.0, 256.0, np.inf]
COMPLEX = {'const': 0, 'scale': 1, 'oil': 1, 'scale+oil': 2, 'combo': 1}
SPEC_X = {'scale': ['x1'], 'oil': ['x2'], 'scale+oil': ['x1', 'x2'], 'combo': ['x1']}
LABEL = {'const': 'constant shares', 'scale': 'MNL: scale (FR1 real sector VA)', 'oil': 'MNL: oil export price',
         'scale+oil': 'MNL: scale + oil price', 'combo': 'combination: 1/2 constant + 1/2 MNL scale'}

class ShareSystem:
    '''Multinomial-logit share system with DOLS slopes, the coherence rule and empirical-Bayes shrinkage.
    S: nominal levels (years x units); drivers: DataFrame with columns x1, x2 (history); dum: optional step dummies.'''
    def __init__(self, name, S, ref, drivers, est0=EST0, dum=None):
        self.name, self.ref = name, ref
        self.units = list(S.columns); self.W = S.div(S.sum(axis=1), axis=0)
        self.LO = {k: np.log(self.W[k] / self.W[ref]) for k in self.units}
        self.X = drivers; self.est0 = est0; self.dum = dum

    def fit(self, spec, upto, anchor=None, kappa=1.0):
        anchor = upto if anchor is None else anchor
        yrs = [y for y in self.W.index if self.est0 <= y <= upto and self.W.loc[y].notna().all()
               and self.X.loc[y].notna().all()]
        par = {'spec': spec, 'anchor': anchor, 'kappa': kappa, 'u': {}}
        xs = SPEC_X.get(spec, [])
        for k in self.units:
            if k == self.ref or spec == 'const':
                par[k] = dict(b=pd.Series(0.0, index=xs), se=pd.Series(np.nan, index=xs), fit=None, rule=''); continue
            Xd = None if self.dum is None else self.dum
            f = lr_fit(self.LO[k], self.X[xs], Xd, sample=yrs)
            fd = diff_fit(self.LO[k], self.X[xs], Xd, sample=yrs)
            b = f.lr[xs].copy(); se = f.lr_se[xs].copy(); rule = []
            for x in xs:
                if x in fd.names:
                    lo_, hi_ = ci95(fd, x)
                    if not (lo_ <= b[x] <= hi_):
                        b[x] = fd.beta[fd.names.index(x)]; se[x] = fd.se[fd.names.index(x)]; rule.append(f'{x}: difference form')
            par[k] = dict(b=b, se=se, fit=f, rule='; '.join(rule), eg_p=f.eg_p, est=f.estimator)
        if spec != 'const' and xs:
            self._shrink(par, xs, anchor, kappa)
        # anchor every equation on the anchor year (constant add-factor = own last-actual residual)
        for k in self.units:
            p = par[k]
            p['z0'] = float(self.LO[k].loc[anchor]) - float((p['b'] * self.X.loc[anchor, xs]).sum()) if xs else float(self.LO[k].loc[anchor])
            if p.get('fit') is not None:
                p['resid'] = self.LO[k].loc[yrs] - (p['z0'] + (self.X.loc[yrs, xs] * p['b']).sum(axis=1))
        return par

    def _shrink(self, par, xs, anchor, kappa):
        w = self.W.loc[anchor]
        for x in xs:
            b = pd.Series({k: par[k]['b'][x] for k in self.units}); se = pd.Series({k: par[k]['se'][x] for k in self.units})
            se[self.ref] = float((se.drop(self.ref) * w.drop(self.ref)).sum() / w.drop(self.ref).sum())
            d = b - float((w * b).sum())
            tau2 = max(float(d.var(ddof=1) - (se ** 2).mean()), 1e-4)
            B = (kappa * se ** 2 / (kappa * se ** 2 + tau2)) if np.isfinite(kappa) else pd.Series(1.0, index=b.index)
            ds = (1 - B) * d; bs = ds - ds[self.ref]
            for k in self.units:
                par[k]['b'] = par[k]['b'].copy(); par[k]['b'][x] = float(bs[k])
                par[k]['se'] = par[k]['se'].copy(); par[k]['se'][x] = float(np.sqrt(max(1 - B[k], 0)) * se[k])
                par[k].setdefault('B', {})[x] = float(B[k])

    def predict(self, par, X, years, zshift=None):
        xs = SPEC_X.get(par['spec'], [])
        z = pd.DataFrame({k: par[k]['z0'] + ((X.loc[years, xs] * par[k]['b']).sum(axis=1) if xs else 0.0)
                          for k in self.units}, index=years)
        if zshift is not None: z = z + zshift.reindex(index=years, columns=self.units).fillna(0.0)
        e = np.exp(z - z.max(axis=1).values[:, None])
        W = e.div(e.sum(axis=1), axis=0)
        if par['spec'] == 'combo':
            W = 0.5 * W + 0.5 * pd.DataFrame([self.W.loc[par['anchor']].values] * len(years), index=years, columns=self.units)
        return W

    def errors(self, spec, origins, end, kappa=1.0):
        '''share errors (pp), indexed (origin, target year) x unit'''
        out = {}
        for o in origins:
            fy = [y for y in range(o + 1, end + 1) if y in self.W.index]
            par = self.fit(spec, o, kappa=kappa)
            out[o] = (self.predict(par, self.X, fy) - self.W.loc[fy]) * 100
        return pd.concat(out)

def loss_of(E): return (E ** 2).sum(axis=1)
def rmse_of(E): return float(np.sqrt(np.nanmean(E.values ** 2)))

def select(sys_, cands, origins, end, kappa=1.0):
    E = {c: sys_.errors(c, origins, end, kappa) for c in cands}
    T = pd.DataFrame({'RMSE_pp': {c: rmse_of(E[c]) for c in cands}})
    best = min(cands, key=lambda c: T.loc[c, 'RMSE_pp'])
    for c in cands:
        s_, p_, ny = (np.nan, np.nan, np.nan) if c == best else dm_by_year(loss_of(E[best]), loss_of(E[c]))
        T.loc[c, 'DM_HLN_vs_best'] = s_; T.loc[c, 'DM_p_vs_best'] = p_; T.loc[c, 'target_years'] = ny
    ok = [c for c in cands if c == best or T.loc[c, 'DM_p_vs_best'] > 0.10]
    chosen = min(ok, key=lambda c: (COMPLEX.get(c, 0), T.loc[c, 'RMSE_pp']))
    T['slopes'] = [COMPLEX.get(c, 0) for c in cands]; T['non_inferior'] = [c in ok for c in cands]
    T['decision'] = ['CHOSEN' if c == chosen else '' for c in cands]
    T.index = [LABEL.get(c, c) for c in T.index]
    return T, chosen, E

def select_kappa(sys_, spec, origins, end, allow_full=True):
    '''Shrinkage intensity by the same rule. Full shrinkage (= constant shares) is a candidate only if constant
    shares were non-inferior at the specification stage; otherwise the two stages would contradict each other.'''
    grid = [k_ for k_ in SHR_K if allow_full or np.isfinite(k_)]
    E = {k_: sys_.errors(spec, origins, end, kappa=k_) for k_ in grid}
    T = pd.DataFrame({'RMSE_pp': {k_: rmse_of(E[k_]) for k_ in grid}})
    best = min(grid, key=lambda k_: T.loc[k_, 'RMSE_pp'])
    for k_ in grid:
        s_, p_, _ = (np.nan, np.nan, 0) if k_ == best else dm_by_year(loss_of(E[best]), loss_of(E[k_]))
        T.loc[k_, 'DM_HLN_vs_best'] = s_; T.loc[k_, 'DM_p_vs_best'] = p_
    ok = [k_ for k_ in grid if k_ == best or T.loc[k_, 'DM_p_vs_best'] > 0.10]
    if allow_full:
        chosen = max(ok)                              # the most shrinkage that is not significantly worse
    else:
        # constant shares were rejected: an intensity that converges to constant shares cannot be chosen by the
        # parsimony rule. Take the lowest-RMSE kappa among those significantly BETTER than constant shares (DM p < 0.10);
        # if none is, the lowest-RMSE non-inferior kappa.
        Ec = sys_.errors('const', origins, end)
        for k_ in grid:
            s_, p_, _ = dm_by_year(loss_of(E[k_]), loss_of(Ec)); T.loc[k_, 'DM_p_vs_const'] = p_
        sig = [k_ for k_ in grid if T.loc[k_, 'RMSE_pp'] < rmse_of(Ec) and T.loc[k_, 'DM_p_vs_const'] < 0.10]
        chosen = min(sig or ok, key=lambda k_: T.loc[k_, 'RMSE_pp'])
    T['non_inferior'] = [k_ in ok for k_ in grid]; T['decision'] = ['CHOSEN' if k_ == chosen else '' for k_ in grid]
    T.index = [f'kappa = {k_:g}' + (' (no shrinkage)' if k_ == 0 else ' (full shrinkage = constant shares)' if not np.isfinite(k_) else '') for k_ in grid]
    return T, chosen

SEL_ORIGINS = [2011, 2013, 2015, 2017]
X_MAN = pd.DataFrame({'x1': np.log(F1H.rva_man), 'x2': np.log(F1H.oil_exp_price)})
X_MIN = pd.DataFrame({'x1': np.log(F1H.rva_min), 'x2': np.log(F1H.oil_exp_price)})
SYS_C = ShareSystem('manufacturing (24 branches)', GO[MANUF].loc[EST0:], '10', X_MAN)
SYS_B = ShareSystem('mining (4 branches)', GO[MINING].loc[EST0:], '06', X_MIN)
CANDS = ['const', 'scale', 'oil', 'scale+oil', 'combo']
SELECT = {}
for nm, sy in [('C', SYS_C), ('B', SYS_B)]:
    T, ch, E = select(sy, CANDS, SEL_ORIGINS, SEL_END)
    kap, KT = 1.0, None
    if ch != 'const':
        KT, kap = select_kappa(sy, ch, SEL_ORIGINS, SEL_END, allow_full=bool(T.loc[LABEL['const'], 'non_inferior']))
        if not np.isfinite(kap): ch = 'const'
    SELECT[nm] = dict(table=T, chosen=ch, kappa=kap, ktable=KT)
    print(f'=== {sy.name}: selection on origins {SEL_ORIGINS}, every score in years <= {SEL_END}')
    display(T.round(3))
    if KT is not None:
        display(KT.round(3))
    print(f'CHOSEN: {LABEL[ch]}' + (f', shrinkage kappa = {kap:g}' if ch != 'const' else ''))
    for c in CANDS:
        if c != SELECT[nm]['chosen']:
            r = T.loc[LABEL[c]]
            reject(f'{LABEL[c]} ({sy.name})', 'branch share system', 'NOT CHOSEN',
                   f'selection RMSE {r.RMSE_pp:.3f} pp vs {T.loc[LABEL[SELECT[nm]["chosen"]], "RMSE_pp"]:.3f} pp for the chosen system; '
                   f'DM/HLN p vs best {r.DM_p_vs_best:.2f}')

# %% [markdown]
# ### 11.3 Müqayisə meyarı olan pay sistemləri, 2005–2025 üzrə qiymətləndirilmiş və 2025-ə lövbərlənmiş
#
# Sahələr üçün bu sektor sürücülü sistemlər **müqayisə meyarıdır**: proqnozda §11.4–11.5-in struktur modeli istifadə
# olunur. Regionlar üçün isə aşağıdakı sistem istifadə olunur. Əmsallar (`output/FR10_share_system_coefficients.csv`):
# DOLS səviyyə meyli və ya uyğunsuz olduqda onu əvəz edən fərq formasındakı meyl; büzülmədən sonrakı aposterior
# standart xətası; qalıqlara əsaslanan kointeqrasiya p-dəyəri. Kointeqrasiya təsdiqlənmədikdə səviyyə meyli *təsviri*
# xarakter daşıyır; proqnoza yalnız büzülmüş dəyər vasitəsilə daxil olur.

# %%
PAR = {}
COEF_ROWS = []
for nm, sy in [('C', SYS_C), ('B', SYS_B)]:
    s_ = SELECT[nm]
    PAR[nm] = sy.fit(s_['chosen'], LAST_ACT, kappa=s_['kappa'])
    xs = SPEC_X.get(s_['chosen'], [])
    raw = sy.fit(s_['chosen'], LAST_ACT, kappa=0.0) if xs else None
    for k in sy.units:
        p = PAR[nm][k]
        for x in xs:
            COEF_ROWS.append(dict(system=sy.name, branch=k, name=BNAME[k], driver={'x1': 'ln FR1 real VA', 'x2': 'ln oil price'}[x],
                                  slope_used=p['b'][x], se_posterior=p['se'][x],
                                  slope_unshrunk=raw[k]['b'][x] if k != sy.ref else 0.0,
                                  shrink_B=p.get('B', {}).get(x, np.nan), eg_coint_p=p.get('eg_p', np.nan),
                                  estimator=p.get('est', 'reference'), coherence=p.get('rule', ''),
                                  inference=('reference' if k == sy.ref else 'descriptive (cointegration not established)'
                                             if not (p.get('eg_p', 1) <= 0.10) else 'cointegration supported at 10%')))
SHARE_COEF = pd.DataFrame(COEF_ROWS)
if len(SHARE_COEF):
    display(SHARE_COEF.round(3))
    print(f'{int((SHARE_COEF.coherence != "").sum())} of {len(SHARE_COEF)} slopes replaced by the difference form (coherence rule); '
          f'{int((SHARE_COEF.eg_coint_p <= 0.10).sum())} cointegrating at 10%')
else:
    print('Both share systems are constant shares: no slope is estimated for the forecast.')
for nm in ['C', 'B']:
    print(f'{SYS_C.name if nm == "C" else SYS_B.name}: benchmark selection = {LABEL[SELECT[nm]["chosen"]]}'
          + (f', kappa {SELECT[nm]["kappa"]:g}' if SELECT[nm]['chosen'] != 'const' else ''))
