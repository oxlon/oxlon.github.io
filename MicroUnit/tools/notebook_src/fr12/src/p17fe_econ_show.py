# %% [markdown]
# **Modellərin işə salınması.** Aşağıdakı hər model tam reqressiya nəticəsi ilə tənliklər reyestrinə (Hissə 18) daxil olur,
# SİNTETİK rejimdə `synthetic: true` ilə. Parametrlərin bərpası (g): **G1** generatorun gəlir–xərc elastikliklərini γ_s və
# gənc müəssisələrin ölçü cəriməsini tam nəzərdə tutulduğu kimi bərpa edir; **G2** gənc müəssisələr üzrə təhlükə
# multiplikatorunu və mülkiyyətin sıfır təsirini bərpa edir, lakin ölçü qruplarının nəzərdə tutulan nisbətlərini bərpa
# **etmir** — generator ölümləri *qruplaşdırılmış* qeydlər arasından seçir (mikro qeyd 40-a qədər müəssisəni təmsil edir və
# bir çəkiliş xananın bütün ölüm sayını götürə bilər), buna görə onun `HAZ` göstəricisi bir müəssisəyə düşən təhlükə nisbəti
# deyil. Bunu məhz bərpa testi aşkar edir; o, gizlədilmir, göstərilir. Girişlərin sayı, SCP, mobillik və Boone meyli üçün
# **generator parametri yoxdur** (doğumlar davranış modelindən çəkilmir, DSK aqreqatlarına kalibrlənir): onlar üçün bərpa
# müəyyən edilmir və cədvəl bunu göstərir.

# %%
ECON = layer_b_econ(REGISTER, DATA_MODE, OUT, LB)
_T = ECON['tables']; _C = _T['coefficients']
print(f"[{DATA_MODE}] Layer-B econometrics: {_C.model.nunique()} models, {len(_C)} coefficient rows, {ECON['runtime']:.1f} s; outputs {ECON['prefix']}*.csv")
display(_T['summary'][['model', 'n', 'interpretation_az']])
display(_T['entry_irr'][['model', 'term', 'ratio', 'ratio_ci_low', 'ratio_ci_high', 'p']].round(4))
display(_T['exit_hazard'][['model', 'term', 'ratio', 'ratio_ci_low', 'ratio_ci_high', 'p']].round(3))
print(f"overdispersion (NB2): alpha = {ECON['overdispersion']['alpha']:.2f}, LR = {ECON['overdispersion']['lr']:,.0f}, p = {ECON['overdispersion']['lr_p']:.2g}; "
      f"exit risk set: duration bands {ECON['exit_meta']['bands']} (reference 10+), dropped event-free categories: {ECON['exit_meta']['dropped'] or 'none'}")
if DATA_MODE == 'SYNTHETIC':
    _rec = _T['recovery']
    display(_rec[['block', 'parameter', 'true', 'estimate', 'ci_low', 'ci_high', 'covered']].round(3))
    display(_rec.groupby('block', sort=False).covered.agg(['sum', 'size', 'mean']).rename(columns={'sum': 'covered', 'size': 'parameters', 'mean': 'coverage'}))
    display(_T['recovery_not_defined'])
    _g1 = _rec[_rec.block.str.startswith('G1')]; _g2 = _rec[_rec.block.str.startswith('G2')]
    assert _g1.covered.mean() >= 0.8, 'G1 recovery: generator elasticities not recovered'
    assert bool(_g2.loc[_g2.parameter == 'young12', 'covered'].iloc[0]), 'G2 recovery: young-firm hazard multiplier not recovered'
    assert ECON['recovery_fits']['recovery_exit']['fit']['check'] < 1e-6, 'conditional Poisson differs from statsmodels Poisson with stratum dummies'
fig, ax = plt.subplots(2, 2, figsize=(14, 9))
for i, (k, a, ttl) in enumerate([('entry_irr', ax[0, 0], 'Entry counts: incidence-rate ratios (95% CI)'), ('exit_hazard', ax[0, 1], 'Exit: odds / hazard ratios (95% CI, log scale)')]):
    d = _T[k][_T[k].ratio.notna()].reset_index(drop=True); yy = np.arange(len(d))
    a.errorbar(d.ratio, yy, xerr=[d.ratio - d.ratio_ci_low, d.ratio_ci_high - d.ratio], fmt='o', color=PAL[i], ecolor='grey', capsize=2)
    a.set_yticks(yy); a.set_yticklabels([f'{m.split("_", 1)[1]}: {t}' for m, t in zip(d.model, d.term)], fontsize=7); a.axvline(1, color='k', lw=0.8); a.set_title(ttl)
    if k == 'exit_hazard': a.set_xscale('log')
sv = _T['survival']
for j, (c, g) in enumerate(sv.groupby('cohort')):
    ax[1, 0].plot(g.age, g.km_survival, 'o-', color=PAL[j % len(PAL)], ms=3, label=f'{c} KM')
    if 'pred_cloglog' in g: ax[1, 0].plot(g.age, g.pred_cloglog, 'x--', color=PAL[j % len(PAL)], lw=1, ms=4)
ax[1, 0].set_title('Kaplan–Meier (o, solid) vs cloglog-predicted survival (x, dashed) by cohort, at full years of age'); ax[1, 0].legend(fontsize=6, ncol=2)
if DATA_MODE == 'SYNTHETIC':
    r = _T['recovery']; r = r[r.block.str.startswith(('G1', 'G2'))]
    ax[1, 1].errorbar(r.true, r.estimate, yerr=[r.estimate - r.ci_low, r.ci_high - r.estimate], fmt='o', ms=3, color=PAL[3], ecolor='grey')
    lim = [min(r.true.min(), r.ci_low.min()), max(r.true.max(), r.ci_high.max())]; ax[1, 1].plot(lim, lim, 'k-', lw=0.8)
    ax[1, 1].set_xlabel('true (generator)'); ax[1, 1].set_ylabel('estimate, 95% CI'); ax[1, 1].set_title('Parameter recovery: G1 revenue, G2 exit')
else:
    b = _T['boone_sector_year']; ax[1, 1].errorbar(b.year + np.linspace(-.3, .3, len(b)), b.boone_beta, yerr=1.96 * b.boone_se, fmt='o', ms=2)
    ax[1, 1].set_title('Boone indicator by section-year (95% CI)')
if DATA_MODE == 'SYNTHETIC':
    for a in ax.flat: a.text(0.5, 0.5, 'SİNTETİK\ntexniki nümayiş', transform=a.transAxes, fontsize=24, color='red', alpha=0.2, ha='center', va='center', rotation=20)
plt.tight_layout(); plt.show()
