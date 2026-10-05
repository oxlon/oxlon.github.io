# %% [markdown]
# ### 17.5 Mühərrikin yüklənmiş panel üzərində işə salınması və onun testləri
#
# `run_layer_b` B qatının bütün hesablamalarını yüklənmiş istənilən panel üzərində aparır və SİNTETİK rejimdə
# `FR10_SYNTHETIC_*.csv` (su nişanı sütunu ilə), REAL rejimdə isə `FR10_FIRM_*.csv` (su nişanı olmadan) fayllarını yazır.
# **İstənilən** giriş üçün doğru olan testlər (DuPont eyniliyi, payların cəminin vahidə bərabərliyi, TFP indeksinin müstəqil
# təkrar hesablama ilə müqayisəsi, müəssisə proqnozlarının cəminin A qatının sahə proqnozuna bərabərliyi, validatorun
# qəsdən daxil edilmiş pozuntuları aşkarlaması) hər iki rejimdə işləyir. Yalnız sintetik panel üçün məna kəsb edən testlər
# (gəlirlərin DSK sahə buraxılışına bərabərliyi, sayların DSK müəssisələrinə bərabərliyi, məlum pay parametrlərinin
# bərpası) SİNTETİK rejimdə işləyir; REAL rejimdə eyni müqayisələr **əhatə diaqnostikası** kimi verilir.

# %%
def run_layer_b(panel, mode, outdir, write=True, plot=False):
    P = panel.copy(); syn = mode == 'SYNTHETIC'
    for f in SCHEMA[SCHEMA.type == 'float'].field:
        if f in P: P[f] = pd.to_numeric(P[f], errors='coerce')
    if 'size_class' not in P or P.size_class.isna().any():
        P['size_class'] = size_class(P.employees.values, P.revenue.values)
    T = []
    def t(name, value, ok, note=''):
        if isinstance(value, (float, np.floating)):
            value = f'{value:.1e}' if (value != 0 and abs(value) < 1e-3) else f'{value:.3f}'
        T.append(dict(test=name, value=str(value), passed=bool(ok), note=note))
    bad = P.sample(min(6, len(P)), random_state=SEED).index
    PB = P.copy(); PB.loc[bad[:2], 'equity'] *= 1.5; PB.loc[bad[2:4], 'nace2'] = '34'; PB.loc[bad[4:], 'cash'] = -1.0
    v1 = validate(PB); caught = set(v1[v1.severity == 'error'].row - 2)
    t('validator catches 6 seeded corruptions (balance, NACE, negative cash)', len(caught & set(bad)), set(bad) <= caught)
    RAT = ratios(P)
    t('DuPont: margin x turnover x multiplier = ROE (max abs)', float((RAT.net_margin * RAT.asset_turnover * RAT.equity_multiplier - RAT.roe).abs().max()),
      float((RAT.net_margin * RAT.asset_turnover * RAT.equity_multiplier - RAT.roe).abs().max()) < 1e-9)
    P['tfp'] = tfp_index(P)
    cell = P.groupby(['nace2', 'year']).size().idxmax(); c = P[(P.nace2 == cell[0]) & (P.year == cell[1])]
    sL = (c.wage_bill / c.revenue).clip(0, 1).values; sM = ((c.cost_of_sales - c.wage_bill).clip(lower=0) / c.revenue).clip(0, 1).values
    sK = np.clip(1 - sL - sM, 0, None)
    X = {'l': np.log(c.employees.where(c.employees > 0).values), 'm': np.log(np.maximum((c.cost_of_sales - c.wage_bill).values, 1)),
         'k': np.log(np.maximum(c.fixed_assets.values, 1))}
    ref = np.log(c.revenue.values) - np.log(c.revenue.values).mean()
    for x, sh_ in [('l', sL), ('m', sM), ('k', sK)]: ref = ref - 0.5 * (sh_ + sh_.mean()) * (X[x] - np.nanmean(X[x]))
    mt = float(np.nanmax(np.abs(ref - P.loc[c.index, 'tfp'].values)))
    t(f'TFP index equals an independent firm-by-firm re-computation (NACE {cell[0]}, {cell[1]}; max abs gap)', mt, mt < 1e-10)
    CN = concentration(P, ['nace2']); CNR = concentration(P, ['nace2', 'region'])
    shs = (P.revenue / P.groupby(['nace2', 'year']).revenue.transform('sum')).groupby([P.nace2, P.year]).sum()
    t('market shares sum to one in every NACE-year cell (max gap)', float((shs - 1).abs().max()), (shs - 1).abs().max() < 1e-9)
    EE, SURV = entry_exit(P)
    fsh, SD = share_model(P)
    est = pd.Series(fsh.beta, index=fsh.names); se = pd.Series(fsh.se, index=fsh.names)
    fc_b = [b for b in P.nace2.unique() if b in BCODES]
    FF = firm_forecast(SD[SD.nace2.isin(fc_b)], est.values, B_['nom'])
    agg = FF.groupby(['year', 'nace2']).revenue_fc.sum() / 1000
    ffg = float((agg / B_['nom'].loc[FC_YEARS].stack().rename_axis(['year', 'nace2']).reindex(agg.index) - 1).abs().max() * 100)
    t('firm forecasts add up to the Layer-A branch forecast (%)', ffg, ffg < 1e-9)
    # v2: the firm-level econometric analysis (Part 17.4b-c) on the same panel, in both modes
    n_sh = int(SD.dropna(subset=['dlsh', 'rlp_l1', 'rlev_l1']).firm_id.nunique())
    E = firm_econometrics(P, RAT, mode, share_fit=(fsh, n_sh)); ET = econ_tables(E)
    t('firm-level econometric models estimated (statsmodels = independent numpy computation, asserted)', len(E['F']), len(E['F']) >= 13)
    if syn:
        rc = E['REC'].dropna(subset=['covered']); rc_ = rc[~rc.model_id.isin(['B_pf_pool', 'B_margin_pool'])]
        t('parameter recovery: consistent estimators within 4 s.e. of the true values (count)', f'{int((rc_.bias_in_se.abs() < 4).sum())}/{len(rc_)}',
          bool((rc_.bias_in_se.abs() < 4).all()), f'95% CI coverage {int(rc.covered.sum())}/{len(rc)} (all), {int(rc_.covered.sum())}/{len(rc_)} (consistent)')
    PR = peer_rank(P, RAT)
    t('peer percentile ranks lie in (0, 100]', float(PR.min().min()), (PR.min().min() > 0) and (PR.max().max() <= 100))
    rev = P.groupby(['year', 'nace2']).revenue.sum() / 1000
    cover = rev / GO.stack().rename_axis(['year', 'nace2']).reindex(rev.index)
    cnt = P.groupby(['year', 'nace2']).firm_id.nunique() / NENT.stack().rename_axis(['year', 'nace2']).reindex(rev.index)
    if syn:
        t('firm revenues add up to DSK branch output (max gap, %)', float((cover - 1).abs().max() * 100), (cover - 1).abs().max() < 1e-6)
        t('firm counts equal DSK active enterprises (max gap)', float((cnt - 1).abs().max()), (cnt - 1).abs().max() < 1e-9)
        t('determinant model recovers the DGP (true 0.15, -0.30)', f'{est.iloc[0]:.3f}, {est.iloc[1]:.3f} (s.e. {se.iloc[0]:.3f}, {se.iloc[1]:.3f})',
          all(abs(est.iloc[i] - BETA_TRUE[i]) < 3 * se.iloc[i] + 0.02 for i in range(2)))
    else:
        t('coverage diagnostic: firm revenue / DSK branch output (median)', float(cover.median()), True, 'diagnostic, not a test')
        t('coverage diagnostic: firms / DSK active enterprises (median)', float(cnt.median()), True, 'diagnostic, not a test')
        t('share model estimated (lagged relative productivity, leverage)', f'{est.iloc[0]:.3f}, {est.iloc[1]:.3f}', True, 'estimates, not a test')
    PIPE_ = pd.DataFrame(T)
    if write:
        pre = 'FR10_SYNTHETIC_' if syn else 'FR10_FIRM_'
        def sv(df, name):
            d = df.reset_index() if not isinstance(df.index, pd.RangeIndex) else df.copy()
            if syn and 'WATERMARK' not in d: d.insert(0, 'WATERMARK', SYN_MARK)
            d.to_csv(Path(outdir) / f'{pre}{name}.csv', index=False)
        sv(PIPE_, 'pipeline_tests')
        sv(pd.concat([v1.assign(dataset='with 6 seeded corruptions')]), 'validation_seeded_corruptions')
        ly = int(P.year.max()); m = P.year == ly
        sv(pd.concat([P.loc[m, ['firm_id', 'nace2', 'region', 'size_class']], RAT[m], PR[m].add_prefix('peer_pct_')], axis=1), f'firm_ratios_{ly}')
        sv(CNR.xs(ly, level='year'), f'concentration_nace_region_{ly}'); sv(CN, 'concentration_nace')
        sv(EE, 'entry_exit'); sv(SURV.rename_axis('cohort'), 'cohort_survival')
        sv(pd.DataFrame({'estimate': est.values, 'se': se.values, **({'true': BETA_TRUE} if syn else {})}, index=['rel_lp_l1', 'rel_leverage_l1']), 'share_model')
        sv(FF, 'firm_forecast'); sv(pd.DataFrame({'coverage_revenue_vs_DSK': cover, 'coverage_firms_vs_DSK': cnt}), 'coverage_vs_layer_a')
        for nm_, df_ in ET.items(): sv(df_, nm_)
    return dict(P=P, RAT=RAT, CN=CN, PIPE=PIPE_, FF=FF, est=est, se=se, E=E, ET=ET, fsh=fsh, SD=SD)
LB = run_layer_b(PANEL, DATA_MODE, OUT)
PIPE = LB['PIPE']
display(PIPE)
assert PIPE.passed.all(), 'Layer-B pipeline test failed'
print(f'[{DATA_MODE}] all {len(PIPE)} Layer-B tests pass; outputs {"FR10_SYNTHETIC_*" if DATA_MODE == "SYNTHETIC" else "FR10_FIRM_*"}.csv')
fig, ax = plt.subplots(1, 2, figsize=(13, 4)); ly = int(PANEL.year.max())
ax[0].hist(LB['RAT'].loc[LB['P'].year == ly, 'z_em'].clip(-5, 20), bins=50, color=PAL[7]); ax[0].axvline(4.35, color='r', ls=':'); ax[0].axvline(5.85, color='g', ls=':')
c_ = LB['CN'].xs(ly, level='year').HHI.rename(index=lambda b: BNAME.get(b, b)).sort_values()
ax[1].barh(c_.index, c_.values, color=PAL[7]); ax[1].tick_params(axis='y', labelsize=6)
for a, ttl in zip(ax, [f"Altman Z''-EM, {ly}", f'firm-level HHI by branch, {ly}']):
    a.set_title((SYN_MARK + '\n' if DATA_MODE == 'SYNTHETIC' else 'REAL DATA\n') + ttl, fontsize=8)
    if DATA_MODE == 'SYNTHETIC': a.text(0.5, 0.5, 'SYNTHETIC', transform=a.transAxes, fontsize=34, color='grey', alpha=0.25, ha='center', va='center', rotation=25)
plt.tight_layout(); plt.show()
SCHEMA.to_csv(OUT / 'FR10_input_schema.csv', index=False)
for _old in ['FR10_SYNTHETIC_input_schema.csv', 'FR10_SYNTHETIC_panel_sample.csv', 'FR10_SYNTHETIC_validation_report.csv',
             'FR10_SYNTHETIC_firm_forecast_2030.csv', 'FR10_SYNTHETIC_firm_ratios_2025.csv', 'FR10_SYNTHETIC_concentration_nace_region_2025.csv']:
    if (OUT / _old).exists() and DATA_MODE == 'SYNTHETIC' and not _old.endswith(('ratios_2025.csv', 'region_2025.csv')): (OUT / _old).unlink()
