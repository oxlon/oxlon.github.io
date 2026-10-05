# %% [markdown]
# ## Hissə 12 — Sənaye buraxılışının regional bölgüsü
#
# Eyni pay mexanizmi 14 iqtisadi rayonun sənaye buraxılışındakı paylarına tətbiq olunur (DSK `022`, payların cəmi vahidə
# bərabər olsun deyə məxrəc kimi regionların cəmi götürülür, F9 tapıntısı), istinad regionu Bakıdır. Struktur sürücülər
# FR1-in **neft sektoru tərkibi** — ln(nominal mədənçıxarma ƏD / nominal emal sənayesi ƏD), çünki Bakının payı neft
# kompleksinin payıdır — və digər regionların sənayesinin əsas hissəsini təşkil edən emal sənayesinin **miqyasıdır**.
# 2019-cu ildən pilləli fiktiv dəyişən (dummy) regional sıranın əhatə dairəsindəki dəyişikliyi udur (2019-cu ildən ev
# təsərrüfatlarının sənaye fəaliyyəti daxil edilib). Namizədlər, pəncərələr (bütün qiymətləndirmələr ≤ 2019) və qərar
# qaydası Hissə 11-də olduğu kimidir.

# %%
X_REG = pd.DataFrame({'x1': np.log(F1H.rva_man), 'x2': np.log(F1H.va_min_n / F1H.va_man_n)})
D_REG = pd.DataFrame({'d2019': (X_REG.index >= 2019).astype(float)}, index=X_REG.index)
SYS_R = ShareSystem('14 economic regions', REG_GO.loc[EST0:LAST_ACT], 'Baku city', X_REG, dum=D_REG)
REG_LABEL = {LABEL['oil']: 'MNL: oil-sector mix (FR1 mining/manufacturing VA)', LABEL['scale+oil']: 'MNL: scale + oil-sector mix'}
T, ch, E = select(SYS_R, CANDS, SEL_ORIGINS, SEL_END)
kap, KT = 1.0, None
if ch != 'const':
    KT, kap = select_kappa(SYS_R, ch, SEL_ORIGINS, SEL_END, allow_full=bool(T.loc[LABEL['const'], 'non_inferior']))
    if not np.isfinite(kap): ch = 'const'
SELECT['R'] = dict(table=T.rename(index=REG_LABEL), chosen=ch, kappa=kap, ktable=KT)
display(SELECT['R']['table'].round(3))
if KT is not None: display(KT.round(3))
print(f'CHOSEN for regions: {REG_LABEL.get(LABEL[ch], LABEL[ch])}' + (f', kappa {kap:g}' if ch != 'const' else ''))
PAR['R'] = SYS_R.fit(ch, LAST_ACT, kappa=kap)
for c in CANDS:
    if c != ch:
        r = T.loc[LABEL[c]]
        reject(f'{REG_LABEL.get(LABEL[c], LABEL[c])} (regions)', 'regional share system', 'NOT CHOSEN',
               f'selection RMSE {r.RMSE_pp:.3f} pp vs {T.loc[LABEL[ch], "RMSE_pp"]:.3f} pp; DM/HLN p vs best {r.DM_p_vs_best:.2f}')
if ch != 'const':
    for k in SYS_R.units:
        for x in SPEC_X[ch]:
            COEF_ROWS.append(dict(system=SYS_R.name, branch=k, name=k, driver={'x1': 'ln FR1 real manufacturing VA', 'x2': 'ln FR1 mining/manufacturing VA'}[x],
                                  slope_used=PAR['R'][k]['b'][x], se_posterior=PAR['R'][k]['se'][x], shrink_B=PAR['R'][k].get('B', {}).get(x, np.nan),
                                  eg_coint_p=PAR['R'][k].get('eg_p', np.nan), estimator=PAR['R'][k].get('est', 'reference'),
                                  coherence=PAR['R'][k].get('rule', '')))
    SHARE_COEF = pd.DataFrame(COEF_ROWS)
    display(SHARE_COEF[SHARE_COEF.system == SYS_R.name].round(3))
fig, ax = plt.subplots(figsize=(13, 3.8))
hm = (REG_SH.loc[2005:LAST_ACT].drop(columns='Baku city') * 100).T
im = ax.imshow(hm.values, aspect='auto', cmap='viridis'); ax.set_yticks(range(len(hm))); ax.set_yticklabels(hm.index, fontsize=7)
ax.set_xticks(range(len(hm.columns))); ax.set_xticklabels(hm.columns, fontsize=7, rotation=90)
plt.colorbar(im, ax=ax, label='% of industrial output'); ax.set_title('Regional shares of industrial output (Baku excluded for scale), %')
plt.tight_layout(); plt.show()
print(f'Baku city share of industrial output: {REG_SH.loc[2005, "Baku city"]*100:.1f}% (2005), {REG_SH.loc[2019, "Baku city"]*100:.1f}% (2019), '
      f'{REG_SH.loc[LAST_ACT, "Baku city"]*100:.1f}% ({LAST_ACT})')
