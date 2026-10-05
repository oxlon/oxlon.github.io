# %% [markdown]
# ### 14.1 Həssaslıq: doldurulmuş 2021 dəyərləri daxil edilməklə yenidən qiymətləndirmə
#
# Proqnoz tənlikləri **yalnız müşahidə olunan məlumatlar** üzrə qiymətləndirilir (Hissə 11–14). Həssaslıq təhlili kimi
# fəaliyyət paneli və KOB pay sistemi interpolyasiya edilmiş 2021 dəyərləri (Hissə 7.1) əlavə edilməklə, eyni başlanğıcda
# **eyni qaydalar** (sürücülər dəstləri, lövbərləmə, kombinasiya çəkiləri, uyğunluq filtri) tətbiq edilməklə yenidən
# qiymətləndirilir. 2021 üçün tərif qırılması termini və 2022 impulsu ½-ə bərabər götürülür — interpolyasiya edilmiş dəyər
# 2020 dəyəri (köhnə tərif, dalğa yoxdur) ilə 2022 dəyərinin (yeni tərif, dalğa) ortasındadır — və kənd təsərrüfatının
# 2021 doğumları kənarda qalır, çünki onların 2020 qonşusu xaric edilmiş fermer qeydiyyatı dalğasıdır (F7). Region
# panelində boşluq yoxdur. Nəticə: `FR12_gapfill_sensitivity.csv` (əmsallar və 2030 proqnozları, yalnız müşahidə olunan
# məlumatlar və doldurulmuş dəyərlərlə).

# %%
_f21 = FA[(FA.year == 2021) & FA.imputed & (FA.unit != 'ALL')].pivot_table(index='unit', columns='var', values='value')
_add = pd.DataFrame([dict(unit=g, year=2021, B=r['new'], D=r['dereg'], N=r['registered'], entry=r['entry'], exit=r['exit'], dem=dln(VAH[g]).get(2021),
                          lend=FR1X.lend.get(2021), cred=FR1X.cred.get(2021), pcm=PCM_G.PCM.get((g, 2021)), size=np.log(VAH[g]).get(2021))
                     for g, r in _f21.iterrows()])
_add['lnB'] = np.log(_add.B); _add['brk'] = 0.5; _add['d2022'] = 0.5
_add.loc[_add.unit == 'AGR', ['lnB', 'entry']] = np.nan
PA_F = pd.concat([PA, _add], ignore_index=True).sort_values(['unit', 'year']).reset_index(drop=True)
_s21 = FS_[(FS_.year == 2021) & FS_.imputed & (FS_['var'] == 'sme_output_share')][['unit', 'year', 'value']].rename(columns={'value': 'sme_output_share'})
PS_F = pd.concat([PS, _s21.merge(PA_F[['unit', 'year', 'dem', 'size', 'lend', 'cred']], on=['unit', 'year'], how='left')], ignore_index=True)
PS_F['lo'] = np.log(PS_F.sme_output_share / (100 - PS_F.sme_output_share)); PS_F = PS_F.sort_values(['unit', 'year']).reset_index(drop=True)
GAPSENS, GS_ROWS = {}, []
def _with_df(key, df, fn):
    old = MODELS[key]['df']; MODELS[key]['df'] = df
    try: return fn()
    finally: MODELS[key]['df'] = old
for key, dfF, orig in [(('activity', 'lnB'), PA_F, 2024), (('activity', 'exit'), PA_F, 2024), (('sme', 'lo'), PS_F, 2024)]:
    X0 = drivers_activity('Baseline')
    FSx = _with_df(key, dfF, lambda: apply_rule(key, SELECT[key]['rule'], orig, X0))
    F0 = FINAL[key] if key in FINAL else apply_rule(key, SELECT[key]['rule'], orig, X0)
    GAPSENS[key] = dict(F=FSx, F0=F0, df=dfF)
    for part in ['m1', 'm0']:
        a, b_ = F0[part], FSx[part]
        if a is None or b_ is None: continue
        for nm, va, vb in list(zip(a['regs'], a['b'], b_['b'])) + list(zip(a['fixed'], a['bf'], b_['bf'])):
            GS_ROWS.append(dict(kind='coefficient', item=f"{key[0]}/{key[1]} {part} ({'structural' if part == 'm1' else 'null'})", term=nm, observed_only=float(va),
                                with_filled=float(vb), diff=float(vb - va), rel_diff_pct=float((vb - va) / abs(va) * 100) if va else np.nan,
                                n_observed=int(len(a['d'])), n_with_filled=int(len(b_['d']))))
        if FSx['spec'] != F0['spec']: GS_ROWS.append(dict(kind='note', item=f'{key}', term='drivers kept', observed_only=np.nan, with_filled=np.nan, diff=np.nan,
                                                          rel_diff_pct=np.nan, note=f"observed {F0['spec']} vs with filled {FSx['spec']}"))
for sc in SCEN:
    X = drivers_activity(sc).sort_values(['unit', 'year']).reset_index(drop=True); N0 = PA[PA.year == 2024].set_index('unit').N
    S0 = stock_rates(X, rule_pred(FINAL[('activity', 'lnB')], X), rule_pred(FINAL[('activity', 'exit')], X), N0)
    S1 = stock_rates(X, rule_pred(GAPSENS[('activity', 'lnB')]['F'], X), rule_pred(GAPSENS[('activity', 'exit')]['F'], X), N0)
    for nm, S in [('observed_only', S0), ('with_filled', S1)]:
        a = S[S.year == 2030][['N', 'new', 'exits']].sum(); GAPSENS[(sc, nm)] = dict(N=a.N, new=a.new, entry=a.new / a.N * 100, exit=a.exits / a.N * 100)
    for v, lab in [('entry', 'fr12:act:entry:ALL'), ('exit', 'fr12:act:exit:ALL'), ('N', 'fr12:act:N:ALL'), ('new', 'fr12:act:new:ALL')]:
        a, b_ = GAPSENS[(sc, 'observed_only')][v], GAPSENS[(sc, 'with_filled')][v]
        GS_ROWS.append(dict(kind='forecast_2030', item=lab, term=sc, observed_only=a, with_filled=b_, diff=b_ - a, rel_diff_pct=(b_ / a - 1) * 100))
    lo0 = rule_pred(GAPSENS[('sme', 'lo')]['F0'], X); lo1 = rule_pred(GAPSENS[('sme', 'lo')]['F'], X); m30 = (X.year == 2030).to_numpy()
    for g, a, b_ in zip(X.unit[m30], 100 / (1 + np.exp(-lo0[m30])), 100 / (1 + np.exp(-lo1[m30]))):
        GS_ROWS.append(dict(kind='forecast_2030', item=f'fr12:conc:sme_output_share:{g}', term=sc, observed_only=a, with_filled=b_, diff=b_ - a, rel_diff_pct=(b_ / a - 1) * 100))
GAPSENS_T = pd.DataFrame(GS_ROWS)
GAPSENS_T['note_az'] = np.where(GAPSENS_T.kind == 'coefficient', 'əmsal: yalnız müşahidə vs doldurulmuş 2021 daxil (eyni qayda)',
                                np.where(GAPSENS_T.kind == 'forecast_2030', '2030 proqnozu: yalnız müşahidə vs doldurulmuş 2021 daxil', 'qeyd'))
GAPSENS_T.to_csv(OUT / 'FR12_gapfill_sensitivity.csv', index=False)
display(GAPSENS_T[GAPSENS_T.kind == 'coefficient'].round(4))
_fc = GAPSENS_T[(GAPSENS_T.kind == 'forecast_2030') & GAPSENS_T.item.str.startswith('fr12:act')]
display(_fc.round(3))
print(f"gap-fill sensitivity: max |coefficient change| {GAPSENS_T[GAPSENS_T.kind == 'coefficient'].rel_diff_pct.abs().max():.1f}%; "
      f"max |2030 change| all-group entry/exit/stock {_fc.rel_diff_pct.abs().max():.2f}%; SME share 2030 max |change| "
      f"{GAPSENS_T[GAPSENS_T.item.str.contains('sme_output')]['diff'].abs().max():.2f} pp")
