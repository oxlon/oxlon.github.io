# %% [markdown]
# **Reyestrdə B qatı.** Hər müəssisə səviyyəli model tam nəticəsi ilə qeydə alınır; panel SİNTETİK olduğu müddətdə hər
# tənlik `synthetic: true`, `data_mode: "SYNTHETIC"`, su nişanı və Azərbaycan dilində *"sintetik məlumat — texniki
# nümayiş"* qeydini daşıyır. Dayanıqlıq: rekursiv (illər üzrə genişlənən) və bir ili çıxarmaqla əmsal trayektoriyaları,
# hökm reyestr qaydası ilə (Chow və CUSUM bu panel qiymətləndiriciləri üçün müəyyən edilmir).

# %%
EB = LB['E']; EBD = EB['D']; EBF = EB['F']; EB_INT = LB['ET']['econ_interpretation_az'].set_index('model_id').interpretation_az
SUB_B = 'B. Müəssisə səviyyəsi: ' + ('SİNTETİK məlumat — texniki nümayiş' if DATA_MODE == 'SYNTHETIC' else 'real müəssisə paneli')
def _refit(f):
    if f.kind == 'ols':
        return lambda sub: (lambda q: (q.b, q.se))(econ_ols(sub(EBD), f.y, f.xs, fe=f.fe, fast=True))
    return lambda sub: (lambda q: (q.b, q.se))(econ_logit(sub(EBD), f.y, f.xs, dummies=f.dummies, fast=True))
def _b_block(eq, f, mid):
    L = ['-' * 92, 'Müəssisə paneli: ' + (f'{f.firms:,} müəssisə, ' if f.firms else '') + f'{f.n:,} müşahidə'
         + (f', {f.G:,} klaster (müəssisə)' if f.G else '') + (f', illər {min(f.years)}–{max(f.years)}' if f.years else '')]
    if f.kind == 'logit':
        L.append(f"AUC = {f.auc:.3f}; Brier = {f.brier:.4f}; Hosmer–Lemeshow p = {f.hl_p:.3f}"
                 + (f"; nümunədən kənar AUC ({f.oos['test_years']}) = {f.oos['auc_oos']:.3f}" if getattr(f, 'oos', None) else ''))
        L.append('Orta marjinal effektlər (AME): ' + '; '.join(f"{ECON_AZ.get(i, i)} {r['ame']:.4f} (s.x. {r['se']:.4f})" for i, r in f.ame.iterrows()))
    rc = EB['REC']; rc = rc[rc.model_id == mid] if 'model_id' in rc else rc.iloc[0:0]
    if len(rc) and 'covered' in rc and rc.covered.notna().any():
        L.append('Generatorun həqiqi parametrləri ilə müqayisə: ' + '; '.join(
            f"{r.term} həqiqi {r.true:.3f} / qiym. {r.estimate:.3f} [{r.ci_low:.3f}, {r.ci_high:.3f}] {'əhatə olunur' if r.covered else 'ƏHATƏ OLUNMUR'}"
            for r in rc.dropna(subset=['covered']).itertuples()))
    elif len(rc):
        L.append('Həqiqi parametr: ' + str(rc.note_az.iloc[0]))
    if DATA_MODE == 'SYNTHETIC': L.append(f'*** {SYN_MARK} — {SYN_AZ} ***')
    eq['summary_text'] = build_summary(eq) + '\n' + '\n'.join(L)

B_EQ = {}
for mid, f in EBF.items():
    eid = f'FR10.{mid}'; syn = DATA_MODE == 'SYNTHETIC'
    labels = {c: ECON_AZ.get(c, c) for c in list(f.b.index)}
    common = dict(components=[], subtask=SUB_B + ' — ' + ECON_BLOCK_AZ[f.block], title_az=f.title_az, title_en=f.title_en,
                  dependent_label_az=ECON_AZ.get(f.y, f.y), coef_labels_az=labels, used_in_forecast=(mid == 'B_share'), editable=[],
                  synthetic=syn, notes_az=EB_INT.get(mid, ''))
    if mid == 'B_share':
        fs_ = f.fit; yrs_ = LB['SD'].loc[fs_.index, 'year'].astype(int).values
        nm_ = list(f.b.index); y_ = pd.Series(fs_.y, index=yrs_, name='dlsh'); X_ = pd.DataFrame(fs_.X, index=yrs_, columns=nm_)
        eq = REGX.add(eid, y_, X_, estimator='OLS', cov='hc1', fit_coef=dict(zip(nm_, fs_.beta)), fit_se=dict(zip(nm_, fs_.se)),
                      add_const=False, coint=False, chow_breaks=(), dependent_code='dlsh', **common)
    elif f.kind == 'ols':
        yy = pd.Series(f.yv, index=f.sample.year.astype(int).values, name=f.y)
        eq = REGX.add(eid, yy, f.X.set_axis(f.sample.year.astype(int).values), estimator=f.est,
                      cov='cluster(firm)', cov_label='cluster(firm): CR1 G/(G-1)(N-1)/(N-K), t(G-1)', fit_coef=f.b, fit_se=f.se,
                      fit_df=int(f.dof), p_dist='t', results=f.res, resid=f.resid, fitted=pd.Series(f.fitted, index=yy.index), **common)
        eq['fit'].update(r2=f.r2, r2_adj=f.r2_adj, ser=f.ser, f_stat=f.F, f_p=f.F_p, f_type='cluster-robust Wald F(m, G-1)',
                         r2_type='within R²' if f.fe == 'firm+year' else 'R²')
        for k_ in ('r2_adj', 'ser', 'f_stat', 'f_p'): eq['fit'].get('null_reasons', {}).pop(k_, None)
        eq['diagnostics']['dw'] = None
        eq['diagnostics'].setdefault('null_reasons', {})['dw'] = 'müəssisə paneli: zaman sırası qalıq testi tətbiq olunmur'
        if f.block == 'b': eq['restrictions'] = [dict(text_az='Miqyasa görə sabit gəlir (βL + βK = 1)', test='cluster Wald F(1, G−1)',
                                                       stat=rts_test(f)['crs_wald_F'], p=rts_test(f)['crs_p'], imposed=False, rts=rts_test(f)['RTS'])]
        if f.fe == 'firm+year': eq['fitted']['note'] = 'within-transformed (firm-demeaned) actual and fitted, period means'
    else:
        eq = REGX.add(eid, pd.Series(f.yv, index=f.sample.year.astype(int).values), None, estimator=f.est,
                      cov='cluster(firm)', cov_label='cluster(firm), MLE sandwich', fit_coef=f.res.params, fit_se=f.res.bse, results=f.res,
                      **common)
        eq['diagnostics'].update(auc=f.auc, brier=f.brier, hosmer_lemeshow=f.hl_stat, hosmer_lemeshow_p=f.hl_p, event_rate=float(f.yv.mean()),
                                 calibration=f.calib.reset_index().to_dict('records'))
        if getattr(f, 'oos', None): eq['diagnostics'].update(auc_oos=f.oos['auc_oos'], brier_oos=f.oos['brier_oos'], oos=f.oos)
        eq['extra'] = dict(eq.get('extra') or {}, ame=f.ame.reset_index().rename(columns={'index': 'term'}).to_dict('records'))
    if f.kind != 'share':
        eq['sample'].update(firms=int(f.firms), clusters=int(f.G), years=[int(v) for v in f.years])
        rec, loo = year_paths(_refit(f), f.years, list(f.b.index))
        used_ = list(f.b.index)
        vd, nt = MR.verdict(rec, loo, [], None, used_, {c: float(f.b[c]) for c in used_})
        eq['robustness'].update(recursive=rec, loo=loo, loo_year_range=loo['range'], verdict=vd,
                                notes_az=nt + '; Chow və CUSUM bu panel qiymətləndiricisi üçün tətbiq olunmur')
        eq['robustness'].setdefault('null_reasons', {}).update(chow='panel: Chow tətbiq olunmur', cusum_p='panel: CUSUM tətbiq olunmur')
        for k_ in ('recursive', 'loo_year_range'): eq['robustness']['null_reasons'].pop(k_, None)
    eq['data_mode'] = DATA_MODE; eq['watermark'] = SYN_MARK if DATA_MODE == 'SYNTHETIC' else None
    eq['extra'] = dict(eq.get('extra') or {}, dropped_regressors=EB['DROPPED'].get(mid), interpretation_az=EB_INT.get(mid, ''))
    _b_block(eq, f, mid); B_EQ[mid] = eq
print(f'registry: {len(B_EQ)} Layer-B (firm-level, {DATA_MODE}) equations registered; {len(REGX)} equations in total')
