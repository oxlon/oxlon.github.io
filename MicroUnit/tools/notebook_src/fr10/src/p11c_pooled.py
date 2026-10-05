# %% [markdown]
# ### 11.5 Qeyri-neft sahələri: əlaqəli sektorlar üzrə birləşdirilmiş tələb modeli
#
# Hər qeyri-neft sahəsi xərc–buraxılış məntiqi əsasında öncədən (a priori) onun məhsulunu alan FR1 aqreqatı ilə
# əlaqələndirilir:
#
# | Sahələr | Əlaqəli sektor (FR1) |
# |---|---|
# | tikinti materialları (23), hazır metal məmulatları (25), karxanaların istismarı (08) | tikintinin əlavə dəyəri `rva_con` |
# | qida (10), içkilər (11) | ev təsərrüfatlarının istehlakı `rcons` |
# | elektrik avadanlığı, maşın və avadanlıq, avtomobillər, digər nəqliyyat vasitələri, təmir/quraşdırma (27–30, 33) | qeyri-neft investisiyaları `rinv_non` |
# | qalan bütün sahələr | öz sektorunun yekunu (nisbi hərəkət yoxdur) |
#
# $$\Delta\ln s_{b,t} = \mu_b + \beta\,\Delta\ln\!\left(\frac{R_{b,t}}{Y_t}\right) + e_{b,t}$$
#
# $s_b$ sahənin qeyri-neft emal sənayesindəki (karxanalar üçün mədənçıxarmadakı) payı, $R_b$ onun əlaqəli sektor indeksi,
# $Y$ isə sektorun yekunudur (FR1 `rva_man`, `rva_min`). **Bir ortaq elastiklik** β, sahə sabit effektləri, birinci
# fərqlər (heç bir yerdə gecikmiş pay yoxdur), t(T−1) üzrə Driscoll–Kraay xətaları və vəhşi (wild) butstrap p-dəyəri.
# Sahə dreyfləri μ_b β-nı identifikasiya edir, lakin **ekstrapolyasiya edilmir**. Uyğunluq: sahə effektləri ilə səviyyələrdə
# eyni model verilir və onun β-sı birinci fərqlər üzrə 95% etibarlılıq intervalı ilə müqayisə olunur. Bir birləşdirilmiş
# meyl olduğundan büzüləcək bir şey yoxdur. Proqnoz:
# $\ln s_{b,t} = \ln s_{b,2025} + \beta\,[\ln(R_b/Y)_t - \ln(R_b/Y)_{2025}]$, softmax ilə yenidən normallaşdırılır (dəqiq toplanma).
#
# Kəsimdən əvvəlki sxem üzrə (başlanğıclar 2011–2017, qiymətləndirmələr ≤ 2019, hədəf ili üzrə DM/HLN) sabit paylara
# qarşı qiymətləndirilir. Qayda (FR4-də olduğu kimi): sabit payları p < 0,10 ilə üstələyərsə, Əsas ssenari odur; əks halda
# Əsas ssenari onun və sabit payların **bərabər çəkili kombinasiyasıdır**, belə ki, FR1-in sektor ssenariləri yenə də
# sahələrə çatır.

# %%
LINK = {'23': 'rva_con', '25': 'rva_con', '08': 'rva_con', '10': 'rcons', '11': 'rcons',
        '27': 'rinv_non', '28': 'rinv_non', '29': 'rinv_non', '30': 'rinv_non', '33': 'rinv_non'}
GROUP = {'C': NONOIL, 'B': MINING}
SECTOT = {'C': 'rva_man', 'B': 'rva_min'}
def rel_index(Dget, units, grp):
    '''ln(R_b / Y_sector) for each unit; 0 for unlinked branches. Dget(name) -> array or Series.'''
    return {b: (np.log(Dget(LINK[b])) - np.log(Dget(SECTOT[grp]))) if b in LINK else 0.0 * np.log(Dget(SECTOT[grp])) for b in units}
SHH = {g: GO[u].div(GO[u].sum(axis=1), axis=0) for g, u in GROUP.items()}
RH = {g: pd.DataFrame(rel_index(lambda v: F1H[v], u, g)) for g, u in GROUP.items()}
def pooled_panel(upto, lev=False):
    rows = []
    for g, u in GROUP.items():
        for b in [b for b in u if b in LINK]:
            ls, r = np.log(SHH[g][b]), RH[g][b]
            d = pd.DataFrame({'y': ls if lev else ls.diff(), 'x': r if lev else r.diff()}).loc[EST0 + (0 if lev else 1):upto]
            rows.append(d.assign(unit=b, year=d.index))
    return pd.concat(rows, ignore_index=True).dropna()
def fit_pooled(upto):
    P = pooled_panel(upto); f = panel_fe(P, 'y', ['x'], twoway=False)
    return float(f.beta[0]), float(f.se[0]), f, P
BETA, BETA_SE, F_POOL, P_POOL = fit_pooled(LAST_ACT)
WILD_POOL, _ = wild_cluster_p(P_POOL, 'y', ['x'], 'x', twoway=False, B=999)
F_LEV = panel_fe(pooled_panel(LAST_ACT, lev=True), 'y', ['x'], twoway=False)
lo_, hi_ = BETA - stats.t.ppf(0.975, F_POOL.dof) * BETA_SE, BETA + stats.t.ppf(0.975, F_POOL.dof) * BETA_SE
POOL_EST = dict(beta=BETA, se=BETA_SE, p_DK=float(F_POOL.pval[0]), p_wild=WILD_POOL, n=F_POOL.n, branches=F_POOL.nN, years=F_POOL.nT,
                beta_levels=float(F_LEV.beta[0]), levels_inside_fd_ci=bool(lo_ <= F_LEV.beta[0] <= hi_), ci_lo=lo_, ci_hi=hi_)
print(f'pooled related-sector elasticity beta = {BETA:.3f} (DK s.e. {BETA_SE:.3f}, p {POOL_EST["p_DK"]:.3f} on t({F_POOL.dof}); wild p {WILD_POOL:.3f}); '
      f'{F_POOL.nN} branches x {F_POOL.nT} years; levels-with-FE estimate {F_LEV.beta[0]:.3f} '
      f'{"inside" if POOL_EST["levels_inside_fd_ci"] else "OUTSIDE"} the FD 95% CI [{lo_:.2f}, {hi_:.2f}]')

def alloc(s_base, dr, beta, mode, zsh=None):
    '''Shares from 2025 (or anchor) shares s_base (K,), relative-index changes dr (..., T, K), slope beta (scalar or (R,)).'''
    lz = np.log(s_base) + (0 if zsh is None else zsh)
    b_ = np.asarray(beta, float).reshape(-1, *([1] * (dr.ndim - 1))) if np.ndim(beta) else beta
    sm_ = lambda z: (lambda e: e / e.sum(-1, keepdims=True))(np.exp(z - z.max(-1, keepdims=True)))
    if mode == 'const': return sm_(lz + 0 * dr)
    W = sm_(lz + b_ * dr)
    return W if mode == 'pooled' else 0.5 * W + 0.5 * sm_(lz + 0 * dr)

def pooled_errors(mode, origins, end):
    out = {}
    for o in origins:
        b_ = fit_pooled(o)[0] if mode != 'const' else 0.0
        fy = list(range(o + 1, end + 1)); s0 = SHH['C'].loc[o, NONOIL].to_numpy(float)
        dr = (RH['C'].loc[fy, NONOIL] - RH['C'].loc[o, NONOIL]).to_numpy(float)
        out[o] = (pd.DataFrame(alloc(s0, dr, b_, mode), index=fy, columns=NONOIL) - SHH['C'].loc[fy, NONOIL]) * 100
    return pd.concat(out)
EP = {m: pooled_errors(m, SEL_ORIGINS, SEL_END) for m in ['const', 'pooled', 'combo']}
PSEL = pd.DataFrame({'RMSE_pp': {m: rmse_of(e) for m, e in EP.items()}})
for m in ['pooled', 'combo']:
    s_, p_, ny = dm_by_year(loss_of(EP[m]), loss_of(EP['const']))
    PSEL.loc[m, 'DM_HLN_vs_const'] = s_; PSEL.loc[m, 'DM_p_vs_const'] = p_; PSEL.loc[m, 'target_years'] = ny
MAN_MODE = 'pooled' if (PSEL.loc['pooled', 'RMSE_pp'] < PSEL.loc['const', 'RMSE_pp'] and PSEL.loc['pooled', 'DM_p_vs_const'] < 0.10) else 'combo'
PSEL['decision'] = ['BASELINE' if m == MAN_MODE else '' for m in PSEL.index]
display(PSEL.round(3))
print(f'non-oil branch allocation: {"pooled related-sector model" if MAN_MODE == "pooled" else "equal-weight combination of the pooled model and constant shares"} '
      f'(pooled vs constant shares: RMSE {PSEL.loc["pooled", "RMSE_pp"]:.3f} vs {PSEL.loc["const", "RMSE_pp"]:.3f} pp, DM p {PSEL.loc["pooled", "DM_p_vs_const"]:.3f})')
if MAN_MODE != 'pooled':
    reject('pooled related-sector model alone', 'non-oil branch allocation', 'enters via the equal-weight combination',
           f'RMSE {PSEL.loc["pooled", "RMSE_pp"]:.3f} vs {PSEL.loc["const", "RMSE_pp"]:.3f} pp, DM p {PSEL.loc["pooled", "DM_p_vs_const"]:.3f}')
