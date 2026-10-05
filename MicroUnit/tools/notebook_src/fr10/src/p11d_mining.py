# %% [markdown]
# ### 11.6 Mədənçıxarma: qeyri-neft sahələri birbaşa modelləşdirilir, qalığı neft hissəsi udur
#
# FR1-in mədənçıxarma yekunu xam neft və qazla müəyyən olunur. Karxanaların istismarını və metal filizlərini onun *payları*
# kimi bölüşdürmək onların öz bazarları böyüdükdə belə neft hasilatının azalmasını miras almalarına səbəb olardı. Buna görə
# mədənçıxarma sürücülər üzrə bölünür:
#
# | Sahə | Real buraxılış | Qiymət |
# |---|---|---|
# | Karxanaların istismarı (08) | v2: lövbərlənmiş sıfır variant — real buraxılış sonuncu faktiki (2025) səviyyəsində sabit — əgər eyni sonuncu faktiki ilə lövbərlənmiş FR1-in tikinti ƏD-si ilə vahid elastiklikli əlaqə kəsimdən əvvəl əhəmiyyətli dərəcədə daha dəqiq deyilsə (hədəf ili üzrə DM/HLN, p < 0,10); əlaqə işarələnmiş rıçaq kimi saxlanılır | FR1-in tikinti deflyatoru `p_con` |
# | Metal filizləri (07) | 2023–25 ortasında saxlanılır (neytral), əgər hansısa sürücü (FR1-in mədənçıxarma və ya tikinti ƏD-si) kəsimdən əvvəl üstün gəlmirsə | FR1-in ÜDM deflyatoru `p_gdp` (FR1-də metal qiyməti yoxdur) |
# | Xam neft və qaz (06), mədənçıxarmaya yardımçı xidmətlər (09) | 2025 × FR1-in neft-qaz ÜDM indeksi `rgdpoil` | **qalıq**: FR1-in mədənçıxarma buraxılışı − 07 − 08, 06/09 arasında 2025-ci ilin nominal nisbətlərində bölünür |
#
# Qalığı neft hissəsi udur, beləliklə, dörd sahənin cəmi FR1-in mədənçıxarma buraxılışına dəqiq bərabərdir (Hissə 18-də
# yoxlama ifadəsi ilə təsdiqlənir); nəzərdə tutulan neft deflyatoru FR1-in mədənçıxarma deflyatoru ilə müqayisədə verilir.
# Eyni məntiq artıq emal sənayesində də tətbiq olunur (neft emalı neft hissəsidir; qeyri-neft sahələri qalığı bölüşür);
# elektrik enerjisi və su təchizatı müstəqil bölmələrdir.

# %%
def precut_rule(b, rules):
    '''Score real-output rules for branch b on origins 2011-2017 (scores <= 2019); rules: name -> f(origin, year) -> predicted Q.'''
    E = {nm: [] for nm in rules}; idx = []
    for o in SEL_ORIGINS:
        for y in range(o + 1, SEL_END + 1):
            idx.append((o, y))
            for nm, f in rules.items(): E[nm].append(np.log(f(o, y) / Q.loc[y, b]) * 100)
    E = {nm: pd.Series(v, index=pd.MultiIndex.from_tuples(idx)) for nm, v in E.items()}
    T = pd.DataFrame({'RMSE_log_pct': {nm: float(np.sqrt((e ** 2).mean())) for nm, e in E.items()}})
    for nm in rules:
        T.loc[nm, 'DM_p_vs_first'] = np.nan if nm == list(rules)[0] else dm_by_year(E[nm] ** 2, E[list(rules)[0]] ** 2)[1]
    return T
def el_fd(b, drv, upto):
    f = ols(np.log(Q[b]).diff().loc[2006:upto], np.log(F1H[drv]).diff().loc[2006:upto].rename('x').to_frame())
    return float(f.beta[1]), float(f.se[1])
# quarrying (v2 decision): the unit-elasticity link to FR1 construction VA is adopted only if it is significantly more
# accurate than the anchored null (real output constant at the origin's last actual) on the pre-cut design; both rules are
# anchored on the origin's last actual (no level step); the estimated
# elasticity is reported for information (its full-sample CI excludes 1 and its sign is unstable), never chosen.
T08 = precut_rule('08', {'neutral: held at the last actual level': lambda o, y: Q.loc[o, '08'],
                          'unit elasticity to construction': lambda o, y: Q.loc[o, '08'] * F1H.rva_con.loc[y] / F1H.rva_con.loc[o],
                          'estimated elasticity to construction': lambda o, y: Q.loc[o, '08'] * (F1H.rva_con.loc[y] / F1H.rva_con.loc[o]) ** el_fd('08', 'rva_con', o)[0]})
E08_EST, E08_SE = el_fd('08', 'rva_con', LAST_ACT)
_u08 = T08.loc['unit elasticity to construction']
won = bool(_u08.RMSE_log_pct < T08.iloc[0].RMSE_log_pct and _u08.DM_p_vs_first < 0.10)
RULE08 = 'unit elasticity to construction' if won else 'neutral: held at the last actual level'
E08 = 1.0                                                        # elasticity of the construction link (baseline only if adopted; else lever)
T08['decision'] = ['CHOSEN' if nm == RULE08 else ('information only' if nm.startswith('estimated') else '') for nm in T08.index]
_t08 = (E08_EST - 1.0) / E08_SE; _p08 = float(2 * stats.t.sf(abs(_t08), _f08_dof := len(np.log(Q['08']).diff().loc[2006:LAST_ACT].dropna()) - 2))
UNIT08_TEST = dict(t=float(_t08), p=_p08, df=int(_f08_dof))
# metal ores: neutral (held at the trailing three-year average) vs FR1 drivers; a driver is used only if significantly better
T07 = precut_rule('07', {'neutral: held at trailing 3-year average': lambda o, y: Q['07'].loc[o - 2:o].mean(),
                          'grows with FR1 mining VA': lambda o, y: Q.loc[o, '07'] * F1H.rva_min.loc[y] / F1H.rva_min.loc[o],
                          'grows with FR1 construction VA': lambda o, y: Q.loc[o, '07'] * F1H.rva_con.loc[y] / F1H.rva_con.loc[o]})
_w = [nm for nm in T07.index[1:] if T07.loc[nm, 'RMSE_log_pct'] < T07.iloc[0].RMSE_log_pct and T07.loc[nm, 'DM_p_vs_first'] < 0.10]
RULE07 = min(_w, key=lambda nm: T07.loc[nm, 'RMSE_log_pct']) if _w else T07.index[0]
T07['decision'] = ['CHOSEN' if nm == RULE07 else '' for nm in T07.index]
display(T08.round(3)); display(T07.round(3))
MINING_RULES = dict(e08=E08, e08_est=E08_EST, e08_se=E08_SE, rule07=RULE07, rule08=RULE08,
                    q08_level_factor=1.0,                                   # anchored null: real output constant at the 2025 actual
                    unit08_dm_p=float(_u08.DM_p_vs_first), unit08_wald_p=_p08,
                    q07_level_factor=float(Q['07'].loc[LAST_ACT - 2:LAST_ACT].mean() / Q.loc[LAST_ACT, '07']),
                    oil_split_06=float(GO.loc[LAST_ACT, '06'] / GO.loc[LAST_ACT, ['06', '09']].sum()))
print(f'quarrying: {RULE08} (unit link vs neutral null: DM p {_u08.DM_p_vs_first:.3f}; estimated elasticity {E08_EST:.3f}, s.e. {E08_SE:.3f}, '
      f'H0 elasticity = 1: t {_t08:.2f}, p {_p08:.3f}); metal ores: {RULE07}')
for nm in T08.index.tolist():
    if nm != RULE08:
        reject(nm + ' (quarrying)', 'mining branches', 'NOT CHOSEN (pre-cut)' + ('; kept as a lever' if nm.startswith('unit') else ''),
               f"RMSE {T08.loc[nm, 'RMSE_log_pct']:.1f} vs {T08.loc[RULE08, 'RMSE_log_pct']:.1f} log-%, DM p vs neutral {T08.loc[nm, 'DM_p_vs_first']:.3f}"
               + (f'; unit restriction rejected on the full sample (t {_t08:.2f}, p {_p08:.3f})' if nm.startswith('unit') else ''))
for nm in T07.index.tolist():
    if nm != RULE07:
        reject(nm + ' (metal ores)', 'mining branches', 'NOT CHOSEN (pre-cut)', 'see Part 11.6 tables')
