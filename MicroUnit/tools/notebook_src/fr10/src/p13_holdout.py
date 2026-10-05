# %% [markdown]
# ## Hissə 13 — Nümunədən kənar yoxlama, 2020–2025 (NFR1)
#
# Bütün prosedur 2019-cu ilin sonunda mövcud olan informasiya ilə təkrarlanır: spesifikasiya və büzülmə intensivliyi
# ≤ 2019 qiymətləndirilən pəncərələrdə seçilib (Hissə 11), hər əmsal və lövbər 2019-cu ilədək olan məlumatlar üzrə
# yenidən qiymətləndirilir və model 2020–2025 üçün simulyasiya edilir. FR1-in sektorlar üzrə əlavə dəyəri və
# deflyatorları **faktiki** dəyərləri ilə daxil olur (onlar FR10-un ekzogen sürücüləridir, FR5 üçün ev təsərrüfatlarının
# gəlirləri kimi); **FR10 üçün endogen olan heç nə daxil edilmir**: sahə buraxılışı pay × (2019-cu il emal sənayesi
# buraxılışı × FR1-in nominal ƏD indeksi) kimi simulyasiya edilir — proqnozdakı eyni lövbərləmə qaydası (buraxılış/ƏD
# nisbəti lövbər ilində saxlanılır) — və sahənin real buraxılışı üçün 2019-cu ilin nisbi qiyməti istifadə olunur, necə ki
# proqnoz 2025-ci ilin nisbi qiymətini saxlayır.
#
# Müqayisə meyarları: **təsadüfi gəzişmə** (hər sahənin 2019-cu il buraxılışı saxlanılır; paylar üçün sabit paylar) və
# **sabit artım** (hər sahə 2014–2019-cu illər üzrə öz orta artımı ilə; əksər sahələr üçün aşağı artım dövrü, açıq
# göstərilir). Theil $U$ = modelin RMSE-si / müqayisə meyarının RMSE-si, sahələr və illər üzrə birləşdirilmiş faiz
# xətaları əsasında; DM/HLN hər hədəf ili üzrə sahələr üzrə orta hesablanmış itki üzərində (6 müşahidə: aşağı güc, açıq
# göstərilir).

# %%
CUT, END = SEL_END, LAST_ACT
HY = list(range(CUT + 1, END + 1))
def holdout_branches(sy, sec, spec, kappa, units):
    par = sy.fit(spec, CUT, kappa=kappa)
    W = sy.predict(par, sy.X, HY)
    va_n = F1H[f'va_{SECV[sec]}_n']
    tot = GO[units].sum(axis=1)
    tot_sim = tot.loc[CUT] * va_n.loc[HY] / va_n.loc[CUT]
    nom = W.mul(tot_sim, axis=0)
    pman = F1H[f'p_{SECV[sec]}']
    real = nom.div(PDEF.loc[CUT, units], axis=1).div(pman.loc[HY] / pman.loc[CUT], axis=0)
    act_n, act_r = GO.loc[HY, units], Q.loc[HY, units]
    g_n = (GO.loc[CUT, units] / GO.loc[CUT - 5, units]) ** (1 / 5) - 1
    g_r = (Q.loc[CUT, units] / Q.loc[CUT - 5, units]) ** (1 / 5) - 1
    cg_n = pd.DataFrame({y: GO.loc[CUT, units] * (1 + g_n) ** (y - CUT) for y in HY}).T
    cg_r = pd.DataFrame({y: Q.loc[CUT, units] * (1 + g_r) ** (y - CUT) for y in HY}).T
    rw_n = pd.DataFrame([GO.loc[CUT, units].values] * len(HY), index=HY, columns=units)
    rw_r = pd.DataFrame([Q.loc[CUT, units].values] * len(HY), index=HY, columns=units)
    pe = lambda p, a: (np.log(p / a) * 100)          # log-per-cent errors (symmetric for large misses)
    E = {'nominal': (pe(nom, act_n), pe(rw_n, act_n), pe(cg_n, act_n)), 'real': (pe(real, act_r), pe(rw_r, act_r), pe(cg_r, act_r))}
    w19 = sy.W.loc[CUT, units]
    cg_sh = cg_n.div(cg_n.sum(axis=1), axis=0)
    E['shares_pp'] = ((W - sy.W.loc[HY]) * 100, (pd.DataFrame([sy.W.loc[CUT].values] * len(HY), index=HY, columns=units) - sy.W.loc[HY]) * 100,
                      (cg_sh - sy.W.loc[HY]) * 100)
    rows = []
    for meas, (m, r, c) in E.items():
        for wt in ['unweighted', 'share-weighted']:
            ww = (pd.DataFrame([w19.values] * len(HY), index=HY, columns=units) if wt == 'share-weighted'
                  else pd.DataFrame(1.0 / len(units), index=HY, columns=units))
            rm = lambda e: float(np.sqrt((ww * e ** 2).sum().sum() / ww.sum().sum()))
            lm, lr_, lc = (ww * m ** 2).sum(axis=1), (ww * r ** 2).sum(axis=1), (ww * c ** 2).sum(axis=1)
            s1, p1 = dm_hln(lm.values, lr_.values); s2, p2 = dm_hln(lm.values, lc.values)
            rows.append(dict(system=sy.name, measure=meas, weighting=wt, model=LABEL[spec], RMSE=rm(m), RMSE_random_walk=rm(r),
                             RMSE_constant_growth=rm(c), U_vs_random_walk=rm(m) / rm(r), U_vs_constant_growth=rm(m) / rm(c),
                             DM_p_vs_rw=p1, DM_p_vs_cg=p2))
    tot_err = float((np.log(tot_sim / tot.loc[HY]) * 100).abs().max())
    per = pd.DataFrame({'model RMSE, nominal %': np.sqrt((E['nominal'][0] ** 2).mean()),
                        'U vs RW': np.sqrt((E['nominal'][0] ** 2).mean()) / np.sqrt((E['nominal'][1] ** 2).mean()),
                        'U vs CG': np.sqrt((E['nominal'][0] ** 2).mean()) / np.sqrt((E['nominal'][2] ** 2).mean())})
    return pd.DataFrame(rows), per, tot_err

HOLD_ROWS, HOLD_PER, HOLD_TOT = [], {}, {}
for nm, sy, units in [('C', SYS_C, MANUF), ('B', SYS_B, MINING)]:
    for spec in CANDS:
        k_ = SELECT[nm]['kappa'] if spec == SELECT[nm]['chosen'] and spec != 'const' else 1.0
        r_, per, te = holdout_branches(sy, nm, spec, k_, units)
        r_['selected'] = spec == SELECT[nm]['chosen']
        HOLD_ROWS.append(r_)
        if spec == SELECT[nm]['chosen']:
            HOLD_PER[nm] = per.rename(index=BNAME); HOLD_TOT[nm] = te
# regions: shares only (the regional total changes coverage in 2019, F9)
for spec in CANDS:
    par = SYS_R.fit(spec, CUT, kappa=SELECT['R']['kappa'] if spec == SELECT['R']['chosen'] and spec != 'const' else 1.0)
    W = SYS_R.predict(par, SYS_R.X, HY)
    m = (W - SYS_R.W.loc[HY]) * 100
    r = (pd.DataFrame([SYS_R.W.loc[CUT].values] * len(HY), index=HY, columns=SYS_R.units) - SYS_R.W.loc[HY]) * 100
    g = (REG_GO.loc[CUT] / REG_GO.loc[CUT - 5]) ** (1 / 5) - 1
    cg = pd.DataFrame({y: REG_GO.loc[CUT] * (1 + g) ** (y - CUT) for y in HY}).T
    c = (cg.div(cg.sum(axis=1), axis=0) - SYS_R.W.loc[HY]) * 100
    rm = lambda e: float(np.sqrt((e ** 2).mean().mean()))
    _, p1 = dm_hln((m ** 2).sum(axis=1).values, (r ** 2).sum(axis=1).values); _, p2 = dm_hln((m ** 2).sum(axis=1).values, (c ** 2).sum(axis=1).values)
    HOLD_ROWS.append(pd.DataFrame([dict(system=SYS_R.name, measure='shares_pp', weighting='unweighted',
                                        model=REG_LABEL.get(LABEL[spec], LABEL[spec]), RMSE=rm(m), RMSE_random_walk=rm(r),
                                        RMSE_constant_growth=rm(c), U_vs_random_walk=rm(m) / rm(r), U_vs_constant_growth=rm(m) / rm(c),
                                        DM_p_vs_rw=p1, DM_p_vs_cg=p2, selected=spec == SELECT['R']['chosen'])]))
HOLD = pd.concat(HOLD_ROWS, ignore_index=True)
display(HOLD[HOLD.selected].round(3))
print('information only (the hold-out was used for no choice): every candidate re-estimated to 2019, unweighted nominal % errors')
display(HOLD[(~HOLD.selected) & (HOLD.measure.isin(['nominal', 'shares_pp'])) & (HOLD.weighting == 'unweighted')]
        [['system', 'measure', 'model', 'RMSE', 'U_vs_random_walk', 'U_vs_constant_growth']].round(3))
print(f'anchoring-rule error (manufacturing output simulated from FR1 VA with the 2019 output/VA ratio): at most '
      f'{HOLD_TOT["C"]:.1f} log-% over 2020-2025; mining {HOLD_TOT["B"]:.1f}')
display(HOLD_PER['C'].round(2).sort_values('model RMSE, nominal %'))
