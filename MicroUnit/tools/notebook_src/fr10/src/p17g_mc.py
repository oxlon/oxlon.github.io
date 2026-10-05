# %% [markdown]
# ### 17.7 Təkrarlamalar üzrə parametrlərin bərpası (yalnız SİNTETİK rejim)
#
# Bir sintetik panel hər qiymətləndirmənin bir çəkilişini verir; 95% intervalın həqiqi dəyəri əhatə edib-etməməsi tək
# Bernulli nəticəsidir. Buna görə struktur qat `MC_R` dəfə yenidən çəkilir (başlanğıc dəyərləri `SEED + 1717 + r`, v1
# baza paneli sabit saxlanılır) və generatorun parametrlərini bildiyi modellər hər dəfə yenidən qiymətləndirilir: 95%
# intervalı həqiqi dəyəri əhatə edən təkrarlamaların payı **əhatə dərəcəsidir**, orta qiymətləndirmə ilə həqiqi dəyər
# arasındakı fərqin Monte Karlo standart xətasına nisbəti isə meyl (sürüşmə) üçün testdir. Birləşdirilmiş
# qiymətləndiricilər within qiymətləndiricisinin aradan qaldırdığı meyli göstərmək üçün daxil edilib. REAL rejimdə
# işləmir (həqiqi parametrlər mövcud deyil).

# %%
MC_R = 40
MC_SPECS = [('B_pf_fe', 'ols', 'ln_va', ['ln_L', 'ln_K'], 'firm+year', 'pf'), ('B_pf_pool', 'ols', 'ln_va', ['ln_L', 'ln_K'], 'nace+year', 'pf'),
            ('B_margin_fe', 'ols', 'op_margin', X_PROF_FE, 'firm+year', 'margin'), ('B_margin_pool', 'ols', 'op_margin', X_PROF_PO, 'nace_year', 'margin'),
            ('B_invest_fe', 'ols', 'inv_rate', ['sales_growth', 'leverage_l1', 'roa_w_l1', 'ln_emp_l1'], 'firm+year', 'invest'),
            ('B_tfp_pf', 'ols', 'tfp_pf', ['state', 'foreign', 'joint'], 'nace_year', 'tfp_own'),
            ('B_export', 'logit', 'exporter', ['ln_emp_l1', 'foreign', 'state', 'joint', 'ln_age', 'baku'], ('nace2', 'year'), 'export')]
def recovery_mc(base, R=MC_R):
    rows = []
    for r in range(R):
        S_, _, _ = structural_overlay(base.copy(), GO, seed=DGP_SEED + 1 + r)
        S_ = S_.reset_index(drop=True); RT_ = ratios(S_); S_['tfp'] = tfp_index(S_); D_ = econ_vars(S_, RT_)
        for mid, kind, y, xs, fe, tk in MC_SPECS:
            if y == 'tfp_pf':
                D_['tfp_pf'] = D_.ln_va - bpf['ln_L'] * D_.ln_L - bpf['ln_K'] * D_.ln_K
            f = econ_ols(D_, y, xs, fe=fe, fast=True) if kind == 'ols' else econ_logit(D_, y, xs, dummies=fe, fast=True)
            if mid == 'B_pf_fe': bpf = f.b
            tq = stats.t.ppf(0.975, f.dof) if f.dof else stats.norm.ppf(0.975); tv = DGP_TRUE[tk]
            items = [(c, f.b[c], f.se[c], tv[c]) for c in xs if c in tv]
            if tk == 'pf':
                a = np.ones(2); items.append(('RTS', float(f.b.sum()), float(np.sqrt(a @ f.V @ a)), tv['ln_L'] + tv['ln_K']))
            rows += [dict(rep=r, model_id=mid, term=c, true=t_, est=b_, se=s_, covered=abs(b_ - t_) <= tq * s_) for c, b_, s_, t_ in items]
    d = pd.DataFrame(rows)
    out = d.groupby(['model_id', 'term'], sort=False).agg(true=('true', 'first'), mean_estimate=('est', 'mean'), mc_sd=('est', 'std'),
                                                          mean_se=('se', 'mean'), coverage_95=('covered', 'mean'), reps=('rep', 'nunique')).reset_index()
    out['bias'] = out.mean_estimate - out.true; out['bias_t'] = out.bias / (out.mc_sd / np.sqrt(out.reps))
    out['se_ratio'] = out.mean_se / out.mc_sd
    out['consistent_estimator'] = ~out.model_id.isin(['B_pf_pool', 'B_margin_pool'])
    out['term_az'] = out.term.map(ECON_AZ)
    return out
if DATA_MODE == 'SYNTHETIC':
    _base = PANEL.drop(columns=[c for c in ['data_status', 'tfp'] if c in PANEL]).copy()
    for f_ in SCHEMA[SCHEMA.type == 'float'].field:
        if f_ in _base: _base[f_] = pd.to_numeric(_base[f_], errors='coerce')
    MC = recovery_mc(_base)
    mc_c = MC[MC.consistent_estimator]
    MC_SUM = dict(reps=MC_R, params=len(mc_c), mean_coverage=float(mc_c.coverage_95.mean()), min_coverage=float(mc_c.coverage_95.min()),
                  max_abs_bias_t=float(mc_c.bias_t.abs().max()), pooled_max_abs_bias_t=float(MC[~MC.consistent_estimator].bias_t.abs().max()))
    _m = MC.copy(); _m.insert(0, 'WATERMARK', SYN_MARK); _m.to_csv(OUT / 'FR10_SYNTHETIC_econ_recovery_mc.csv', index=False)
    _ip = pd.read_csv(OUT / 'FR10_SYNTHETIC_econ_interpretation_az.csv')
    _ip = pd.concat([_ip[_ip.model_id != 'recovery_mc'], pd.DataFrame([dict(WATERMARK=SYN_MARK, model_id='recovery_mc', interpretation_az=(
        f"[{SYN_AZ}] {MC_R} təkrarlamada (struktur qat yenidən çəkilir) ardıcıl qiymətləndiricilərin {len(mc_c)} parametri üzrə 95% "
        f"etibarlılıq intervalının orta əhatəsi {100 * MC_SUM['mean_coverage']:.1f}% (minimum {100 * MC_SUM['min_coverage']:.0f}%); "
        f"sürüşmə testinin maksimum |t| = {MC_SUM['max_abs_bias_t']:.1f}. Birləşdirilmiş OLS-də maksimum |t| = {MC_SUM['pooled_max_abs_bias_t']:.0f}: "
        f"daimi müəssisə effektləri nəzərə alınmadıqda əmsallar sürüşür."))])], ignore_index=True)
    _ip.to_csv(OUT / 'FR10_SYNTHETIC_econ_interpretation_az.csv', index=False)
    display(MC.round(4))
    print(f"[{SYN_MARK}] recovery over {MC_R} replications: consistent estimators mean 95% coverage {MC_SUM['mean_coverage']:.3f} "
          f"(min {MC_SUM['min_coverage']:.3f}), max |bias t| {MC_SUM['max_abs_bias_t']:.2f}; pooled OLS max |bias t| {MC_SUM['pooled_max_abs_bias_t']:.1f}")
    assert MC_SUM['mean_coverage'] > 0.85 and MC_SUM['max_abs_bias_t'] < 5, 'synthetic recovery failed: estimator or generator bug'
else:
    MC, MC_SUM = None, None
    print('REAL data: no true parameters, the replication study is not run')
