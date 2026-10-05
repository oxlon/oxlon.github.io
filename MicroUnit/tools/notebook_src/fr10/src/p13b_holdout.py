# %% [markdown]
# ### 13.1 Faktiki istifadə olunan proqnoz modelinin nümunədən kənar yoxlaması (neftlə bağlı blok + qeyri-neft bölüşdürməsi)
#
# Hər şey 2019-cu ilədək olan məlumatlar üzrə yenidən qiymətləndirilir: birləşdirilmiş elastiklik, neft emalı və kimya
# deflyatorlarının neft qiymətinə görə elastiklikləri və onların güc əmsalları (2017–2019 orta emal həcmi). Emal sənayesi
# buraxılışı proqnozda olduğu kimi 2019-cu ilin buraxılış/ƏD nisbəti ilə FR1-in faktiki nominal əlavə dəyərindən
# simulyasiya edilir.

# %%
def holdout_full(mode, cut=CUT, end=END):
    hy = list(range(cut + 1, end + 1)); yy = [cut] + hy
    b_ = fit_pooled(cut)[0]
    eps = {b: float(ols(np.log(PDEF[b]).diff().loc[2006:cut], np.log(OILAZN).diff().loc[2006:cut].rename('x').to_frame()).beta[1]) for b in OIL}
    capf = {b: float(THR[b].loc[cut - 2:cut].mean() / THR[b].loc[cut]) for b in OIL}
    gc = GO[MANUF].sum(axis=1).loc[cut] * F1H.va_man_n.loc[yy] / F1H.va_man_n.loc[cut]
    nom = pd.DataFrame(index=yy, columns=MANUF, dtype=float); real = nom.copy()
    oi = OILAZN.loc[yy] / OILAZN.loc[cut]
    for b in OIL:
        real[b] = Q.loc[cut, b] * np.where(np.array(yy) == cut, 1.0, capf[b]); nom[b] = real[b] * PDEF.loc[cut, b] * oi ** eps[b]
    rem = gc - nom[OIL].sum(axis=1)
    s0 = SHH['C'].loc[cut, NONOIL].to_numpy(float)
    dr = (RH['C'].loc[yy, NONOIL] - RH['C'].loc[cut, NONOIL]).to_numpy(float)
    nom[NONOIL] = alloc(s0, dr, b_, mode) * rem.to_numpy(float)[:, None]
    pm = F1H.p_man.loc[yy] / F1H.p_man.loc[cut]
    for b in NONOIL: real[b] = nom[b] / (PDEF.loc[cut, b] * pm)
    nom, real = nom.loc[hy], real.loc[hy]
    act_n, act_r = GO.loc[hy, MANUF], Q.loc[hy, MANUF]
    gn = (GO.loc[cut, MANUF] / GO.loc[cut - 5, MANUF]) ** 0.2 - 1; gr = (Q.loc[cut, MANUF] / Q.loc[cut - 5, MANUF]) ** 0.2 - 1
    bm = {'random walk': (pd.DataFrame([GO.loc[cut, MANUF].values] * len(hy), index=hy, columns=MANUF), pd.DataFrame([Q.loc[cut, MANUF].values] * len(hy), index=hy, columns=MANUF)),
          'constant growth': (pd.DataFrame({y: GO.loc[cut, MANUF] * (1 + gn) ** (y - cut) for y in hy}).T, pd.DataFrame({y: Q.loc[cut, MANUF] * (1 + gr) ** (y - cut) for y in hy}).T)}
    w19 = SH_MAN.loc[cut, MANUF]
    rows = []
    for meas, m, a, k in [('nominal', nom, act_n, 0), ('real', real, act_r, 1)]:
        em = np.log(m / a) * 100
        for wt in ['unweighted', 'share-weighted']:
            ww = (pd.DataFrame([w19.values] * len(hy), index=hy, columns=MANUF) if wt == 'share-weighted' else pd.DataFrame(1 / 24, index=hy, columns=MANUF))
            rm = lambda e: float(np.sqrt((ww * e ** 2).sum().sum() / ww.sum().sum()))
            r = dict(system='manufacturing (24 branches): forecasting model', measure=meas, weighting=wt, model=f'oil block + {mode}', RMSE=rm(em))
            for nb, (bn, br) in bm.items():
                eb = np.log((bn if k == 0 else br) / a) * 100
                r[f'U_vs_{nb.replace(" ", "_")}'] = rm(em) / rm(eb)
                r[f'DM_p_vs_{"rw" if nb == "random walk" else "cg"}'] = dm_hln((ww * em ** 2).sum(axis=1).values, (ww * eb ** 2).sum(axis=1).values)[1]
            rows.append(r)
    per = pd.DataFrame({'real error 2020-25, mean abs log %': (np.log(real / act_r) * 100).abs().mean()}).rename(index=BNAME)
    return pd.DataFrame(rows), per, dict(beta=b_, **{f'eps_{b}': v for b, v in eps.items()}, **{f'capf_{b}': v for b, v in capf.items()})
HF = {m: holdout_full(m) for m in ['combo', 'pooled', 'const']}
HOLD_FULL = pd.concat([HF[m][0].assign(selected=(m == MAN_MODE)) for m in HF], ignore_index=True)
display(HOLD_FULL.round(3))
print('pre-cut parameters: ' + ', '.join(f'{k} {v:.3f}' for k, v in HF[MAN_MODE][2].items()))
HOLD = pd.concat([HOLD_FULL, HOLD.assign(selected=HOLD.selected & HOLD.system.str.contains('regions'),
                                         system=np.where(HOLD.system.str.contains('regions'), HOLD.system, HOLD.system + ' (Part 11 share systems)'))], ignore_index=True)
