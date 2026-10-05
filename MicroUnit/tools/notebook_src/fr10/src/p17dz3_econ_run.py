# %%
SYN_AZ = 'sintetik məlumat — texniki nümayiş'
def _keep(d, xs, y, extra=()):
    '''Drop optional regressors with < 80% coverage among rows where the dependent variable exists.'''
    base = d[d[y].notna()]
    if any(x.endswith('_l1') for x in xs) and 'first_obs' in d:
        base = base[~base.first_obs.astype(bool)]           # lagged regressors: coverage among firm-years with a previous year
    keep = [x for x in xs if x in d and base[x].notna().mean() >= 0.8 and base[x].nunique() > 1]
    return keep, [x for x in xs if x not in keep]

def coef_rows(mid, f, est_label):
    tq = stats.t.ppf(0.975, f.dof) if f.dof else stats.norm.ppf(0.975)
    t = f.b / f.se
    p = 2 * (stats.t.sf(np.abs(t), f.dof) if f.dof else stats.norm.sf(np.abs(t)))
    return pd.DataFrame({'model_id': mid, 'estimator': est_label, 'dependent': f.y, 'term': f.b.index,
                         'term_az': [ECON_AZ.get(c, c) for c in f.b.index], 'coef': f.b.values, 'se': f.se.values,
                         't': t.values, 'p': p, 'ci_low': (f.b - tq * f.se).values, 'ci_high': (f.b + tq * f.se).values,
                         'n_obs': f.n, 'n_firms': f.firms, 'n_clusters': f.G, 'year_min': min(f.years), 'year_max': max(f.years)})

def rts_test(f):
    a = np.array([1.0, 1.0]); r = float(f.b['ln_L'] + f.b['ln_K']); se = float(np.sqrt(a @ f.V @ a))
    t = (r - 1) / se; p = float(2 * stats.t.sf(abs(t), f.dof)); tq = stats.t.ppf(0.975, f.dof)
    return dict(RTS=r, se=se, ci_low=r - tq * se, ci_high=r + tq * se, crs_wald_F=t * t, crs_p=p, df=f.dof)

def firm_econometrics(P, RAT, mode, share_fit=None):
    syn = mode == 'SYNTHETIC'
    D = econ_vars(P, RAT); F, ROWS, SUMM, DROPPED = {}, [], [], {}
    est_name = {'firm+year': 'Two-way fixed effects (firm + year), firm-demeaned; cluster(firm)',
                'nace_year': 'Pooled LS + NACE x year fixed effects; cluster(firm)', 'nace+year': 'Pooled LS + NACE and year dummies; cluster(firm)'}
    for mid, taz, ten, kind, y, xs, fe, blk in ECON_MODELS:
        if y == 'tfp_pf':
            pf = F.get('B_pf_fe')
            if pf is None: continue
            D['tfp_pf'] = D.ln_va - pf.b['ln_L'] * D.ln_L - pf.b['ln_K'] * D.ln_K
        if y not in D or D[y].notna().sum() < 50 or (kind == 'logit' and D[y].dropna().nunique() < 2):
            DROPPED[mid] = 'dependent variable not available'; continue
        keep, drop = _keep(D, xs, y)
        if drop: DROPPED[mid] = drop
        f = econ_ols(D, y, keep, fe=fe) if kind == 'ols' else econ_logit(D, y, keep, dummies=fe)
        f.mid, f.title_az, f.title_en, f.block, f.est = mid, taz, ten, blk, (est_name.get(fe) if kind == 'ols' else
                                                         'Logit (MLE), dummies ' + ' + '.join(fe) + '; cluster(firm)')
        F[mid] = f; ROWS.append(coef_rows(mid, f, f.est))
        row = dict(model_id=mid, block=ECON_BLOCK_AZ[blk], title_az=taz, title_en=ten, estimator=f.est, dependent=y,
                   regressors=';'.join(keep), dropped_regressors=';'.join(drop), n_obs=f.n, n_firms=f.firms, n_clusters=f.G,
                   year_min=min(f.years), year_max=max(f.years), synthetic=syn)
        if kind == 'ols':
            row.update(r2=f.r2, r2_type='within R²' if fe == 'firm+year' else 'R²', r2_adj=f.r2_adj, ser=f.ser,
                       wald_F=f.F, wald_F_p=f.F_p)
            if blk == 'b': row.update({k: v for k, v in rts_test(f).items()})
        else:
            row.update(r2=f.r2, r2_type='McFadden pseudo-R²', loglik=f.llf, lr_chi2=f.lr, lr_p=f.lr_p, aic=f.aic, bic=f.bic,
                       auc=f.auc, brier=f.brier, hosmer_lemeshow=f.hl_stat, hosmer_lemeshow_p=f.hl_p, event_rate=float(f.yv.mean()))
        SUMM.append(row)
    # (d) out-of-sample check of the distress model: estimated on target years <= T-2, scored on the last two years
    OOS = None
    if 'B_distress' in F:
        f = F['B_distress']; ly = max(f.years); tr = D[D.year <= ly - 2]
        fo = econ_logit(tr, 'distress', f.xs, dummies=('year',), fast=True)
        te = D[(D.year > ly - 2)].dropna(subset=['distress'] + f.xs)
        Xte = pd.concat([pd.Series(1.0, index=te.index, name='const'), te[f.xs]], axis=1)
        for c in fo.res.params.index:
            if c not in Xte: Xte[c] = 0.0                     # test years are outside the training year dummies
        lp = Xte[fo.res.params.index].to_numpy(float) @ fo.res.params.to_numpy(float)
        yr_ = [c for c in fo.res.params.index if c.startswith('year_')]
        lp = lp + (fo.res.params[yr_[-1]] if yr_ else 0.0)     # last training-year effect carried forward
        pt = 1 / (1 + np.exp(-lp)); yt = te.distress.to_numpy(float)
        OOS = dict(train_years=f'{min(f.years)}-{ly - 2}', test_years=f'{ly - 1}-{ly}', n_test=len(te), auc_oos=auc(yt, pt),
                   brier_oos=float(np.mean((pt - yt) ** 2)), event_rate_test=float(yt.mean()))
        F['B_distress'].oos = OOS; F['B_distress'].calib_oos = calibration(yt, pt); F['B_distress'].roc_oos = roc_points(yt, pt)
        SUMM[[s_['model_id'] for s_ in SUMM].index('B_distress')].update(auc_oos=OOS['auc_oos'], brier_oos=OOS['brier_oos'])
    # (f) the market-share model of Part 17.2 (HC1, within NACE x year): full output
    if share_fit is not None:
        fs_, n_firms = share_fit
        F['B_share'] = EFit(kind='share', mid='B_share', b=pd.Series(fs_.beta, index=['rel_lp_l1', 'rel_leverage_l1']),
                            se=pd.Series(fs_.se, index=['rel_lp_l1', 'rel_leverage_l1']), dof=fs_.dof, n=fs_.n, firms=n_firms, G=None,
                            y='dlsh', years=[], fit=fs_, block='f', title_az='Bazar payının dəyişməsinin amilləri',
                            title_en='Market-share growth determinants', est='OLS within NACE x year (demeaned), HC1')
    COEF = pd.concat(ROWS, ignore_index=True); SUM = pd.DataFrame(SUMM)
    # (h) parameter recovery against the generator's true values
    REC = []
    for mid, f in F.items():
        tk = TRUE_MAP.get(mid) if mid != 'B_share' else 'share'
        if not syn:
            continue
        if tk is None:
            REC.append(dict(model_id=mid, term='—', true=np.nan, note_az=NO_TRUTH_AZ.get(mid, 'həqiqi parametr yoxdur'))); continue
        tv = {'rel_lp_l1': BETA_TRUE[0], 'rel_leverage_l1': BETA_TRUE[1]} if tk == 'share' else DGP_TRUE[tk]
        tq = stats.t.ppf(0.975, f.dof) if f.dof else stats.norm.ppf(0.975)
        items = [(c, f.b[c], f.se[c]) for c in f.b.index if c in tv]
        if mid.startswith('B_pf'):
            rt = rts_test(f); items.append(('RTS', rt['RTS'], rt['se'])); tv = dict(tv, RTS=tv['ln_L'] + tv['ln_K'])
        for c, b_, s_ in items:
            lo_, hi_ = b_ - tq * s_, b_ + tq * s_
            REC.append(dict(model_id=mid, term=c, term_az=ECON_AZ.get(c, c), true=tv[c], estimate=b_, se=s_, ci_low=lo_, ci_high=hi_,
                            covered=bool(lo_ <= tv[c] <= hi_), bias=b_ - tv[c], bias_in_se=(b_ - tv[c]) / s_,
                            note_az=('birləşdirilmiş OLS: məhsuldarlıq kapitalla korrelyasiyalıdır, sürüşmə gözlənilir' if mid == 'B_pf_pool' else
                                     'birləşdirilmiş model: müəssisə effekti ilkin ölçü ilə korrelyasiyalıdır, ölçü əmsalında sürüşmə gözlənilir'
                                     if (mid == 'B_margin_pool' and c == 'ln_emp') else '')))
    REC = pd.DataFrame(REC) if REC else pd.DataFrame([dict(model_id='—', term='—', note_az='REAL məlumat: həqiqi parametrlər məlum deyil, bərpa testi tətbiq olunmur')])
    return dict(D=D, F=F, COEF=COEF, SUM=SUM, REC=REC, OOS=OOS, DROPPED=DROPPED, syn=syn)
print('firm_econometrics defined: models (a)-(g), out-of-sample distress check, parameter recovery (h)')
