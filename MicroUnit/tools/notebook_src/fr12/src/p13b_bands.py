# %% [markdown]
# ### 13.1 Qeyri-müəyyənlik zolaqları və inandırıcılıq
#
# 500 təkrarlama, hər biri (i) sürücülər üçün FR1-in Əsas ssenari üzrə 500 çəkilişindən birini, (ii) meyllərin
# qiymətləndirilmiş paylanmasından işarəyə görə rədd etməklə çəkilişi və (iii) qalıqların **birgə tarixi trayektoriyasını**
# birləşdirir: hər təkrarlama üçün bir tarixi başlanğıc ili *s* çəkilir və hər *h* üfüqü üçün xəta qaydanın öz modelinin
# qalıqlarından qurulur, $e_h = w\,(u_{s+h}-u_s) + (1-w)\,u_{s+h}$, burada *w* qaydanın nəzərdə tutulan təsadüfi gəzişmə
# çəkisidir (lövbərlənmiş hissə xətaları fərqlərdə, lövbərlənməmiş hissə səviyyələrdə yaradır) — hər üfüq üçün bir tarixi
# cüt $(s, s+h)$, **doğumlar və çıxış üçün və bütün vahidlər üçün eyni**, cütlər üzrə mərkəzləşdirilmiş. Ən azı iki dəfə
# müşahidə olunan ən uzun fasilədən (fəaliyyət 4 il, regionlar 3) uzun üfüqlər həmin fasilədəki cütlərdən təkrar istifadə
# edir; ili çatışmayan vahid (kənd təsərrüfatı 2020) ən yaxın müşahidə olunan ildən istifadə edir. Heç bir qalıq AR
# qiymətləndirilmir, heç bir boşluq sıfırla doldurulmur və hər üfüq üzrə tarixi cütlərin sayı (kiçik: 1–4) göstərilir.
# Hər üfüq çox az cütə əsaslandığından, xəta dəsti əvvəlki üfüqünkündən az dağınıq olan üfüq (doğumlar və ya çıxış üçün)
# hər iki tənlik üçün birgə əvvəlki üfüqün dəstindən təkrar istifadə edir — beləliklə, xəta dəsti üfüq artdıqca heç vaxt
# daha az dağınıq olmur (bu qayda olmadan iki yaxın tarixi cüt 2026 və 2028-dən xeyli dar 2027 zolağı yaradırdı); axın və
# əmsal zolaqları sürücü çəkilişləri və ehtiyat eyniliyi vasitəsilə yenə də tədricən daralına bilər.

# %%
rng_f = np.random.default_rng(SEED + 13)
ND = 500
def param_draw(F):
    if F['m1'] is None or not len(F['m1']['b']): return None
    b, V = F['m1']['b'], F['m1']['V']
    for _ in range(50):
        d = rng_f.multivariate_normal(b, V)
        if np.all(np.sign(d) == np.sign(b)): return d
    return b
def resid_grid(F, units, years):
    m = F['m1'] if F['m1'] is not None else F['m0']
    U = pd.DataFrame({'unit': m['d'].unit.values, 'year': m['d'].year.values, 'u': m['resid'].to_numpy(float)}).pivot_table(index='year', columns='unit', values='u')
    U = U.reindex(index=years, columns=units)
    return U.T.apply(lambda r: r.interpolate(method='nearest', limit_direction='both') if r.notna().sum() > 1 else r.fillna(r.mean()), axis=1).T
PATHS = {}
for pn, df in PANELS.items():
    Y = sorted(df.year.unique()); units = sorted(df.unit.unique()); Hn = len(DRV[pn]('Baseline').year.unique())
    pairs = {}
    for a in Y:
        for b_ in Y:
            if b_ > a: pairs.setdefault(b_ - a, []).append((a, b_))
    cap = max(g for g, v in pairs.items() if len(v) >= 2)
    E = {}
    for dep in ['lnB', 'exit']:
        F = FINAL[(pn, dep)]; U = resid_grid(F, units, Y); w = F['w_rw']; E[dep] = {}
        for h in range(1, Hn + 1):
            g = min(h, cap); arr = np.stack([w * (U.loc[t] - U.loc[s_]).to_numpy(float) + (1 - w) * U.loc[t].to_numpy(float) for s_, t in pairs[g]])
            E[dep][h] = arr - arr.mean(axis=0)
    _disp = lambda a: float(np.nanmean(np.nanvar(a, axis=0)))
    reused = []
    for h in range(2, Hn + 1):                     # non-narrowing rule (joint for births and exit)
        if any(_disp(E[dep][h]) < _disp(E[dep][h - 1]) for dep in E):
            for dep in E: E[dep][h] = E[dep][h - 1]
            reused.append(h)
    PATHS[pn] = dict(E=E, npairs={h: E['lnB'][h].shape[0] for h in range(1, Hn + 1)}, cap=cap, units=units, Hn=Hn, reused=reused)
    print(f'{pn}: horizons reusing the previous horizon error set (non-narrowing rule): {reused or "none"}')
DRAWS = []
for d in range(ND):
    for pn in PANELS:
        X = DRV[pn]('Baseline', draw=d % FR1D.draw.nunique()).sort_values(['unit', 'year']).reset_index(drop=True)
        P_ = PATHS[pn]; ui = X.unit.map({u: i for i, u in enumerate(P_['units'])}).to_numpy()
        hi_ = X.year.rank(method='dense').astype(int).to_numpy()
        pick = {h: rng_f.integers(P_['npairs'][h]) for h in range(1, P_['Hn'] + 1)}       # one historical pair per horizon, joint across units and equations
        sh = {dep: np.array([P_['E'][dep][h][pick[h], u] for h, u in zip(hi_, ui)]) for dep in ['lnB', 'exit']}
        lb = rule_pred(FINAL[(pn, 'lnB')], X, param_draw(FINAL[(pn, 'lnB')])) + sh['lnB']
        xr = rule_pred(FINAL[(pn, 'exit')], X, param_draw(FINAL[(pn, 'exit')])) + sh['exit']
        S = stock_rates(X, lb, xr, PANELS[pn][PANELS[pn].year == ORIG[pn]].set_index('unit').N)
        DRAWS.append(S.rename(columns={'x': 'exit'}).assign(draw=d, panel=pn)[['draw', 'panel', 'unit', 'year', 'new', 'exits', 'entry', 'exit', 'N']])
DRAWS = pd.concat(DRAWS, ignore_index=True)
_ag = DRAWS.groupby(['draw', 'panel', 'year'])[['N', 'new', 'exits']].sum()
_ag['entry'] = _ag.new / _ag.N * 100; _ag['exit'] = _ag.exits / _ag.N * 100
_all = pd.concat([DRAWS, _ag.reset_index().assign(unit='ALL')], ignore_index=True)
Q = [5, 25, 50, 75, 95]
FAN = _all.groupby(['panel', 'unit', 'year'])[['new', 'entry', 'exit', 'N']].quantile([q / 100 for q in Q]).unstack()
FAN.columns = [f'{v}_p{int(round(q * 100))}' for v, q in FAN.columns]; FAN = FAN.reset_index()
_bl = pd.concat([FC[FC.scenario == 'Baseline'][['panel', 'unit', 'year', 'new', 'entry', 'exit', 'N']],
                 AGG[AGG.scenario == 'Baseline'].assign(unit='ALL')[['panel', 'unit', 'year', 'new', 'entry', 'exit', 'N']]])
FAN = FAN.merge(_bl.rename(columns={c: f'{c}_baseline' for c in ['new', 'entry', 'exit', 'N']}), on=['panel', 'unit', 'year'])
FAN.to_csv(OUT / 'FR12_fan_entry_exit.csv', index=False)
pd.concat([FC[['scenario', 'panel', 'unit', 'year', 'new', 'exits', 'entry', 'exit', 'N']],
           AGG.assign(unit='ALL')[['scenario', 'panel', 'unit', 'year', 'new', 'exits', 'entry', 'exit', 'N']]]).to_csv(OUT / 'FR12_forecast_entry_exit.csv', index=False)
BAND_META = pd.DataFrame([dict(panel=pn, horizon_cap_years=PATHS[pn]['cap'], historical_pairs_by_horizon=', '.join(f"h{h}:{n}" for h, n in PATHS[pn]['npairs'].items()),
                               replications=ND, rw_weight_births=FINAL[(pn, 'lnB')]['w_rw'], rw_weight_exit=FINAL[(pn, 'exit')]['w_rw']) for pn in PANELS])
display(BAND_META)
