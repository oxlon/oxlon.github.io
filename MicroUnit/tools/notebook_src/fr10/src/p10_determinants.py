# %% [markdown]
# ## Hissə 10 — Artım və azalmanın əsas amilləri (4-cü məqsəd)
#
# ### 10.1 Uçot cavabı: sənaye artımını hansı sahələr təmin edib
#
# Hər hansı reqressiyadan əvvəl dəqiq dekompozisiya aparılır: emal sənayesinin real buraxılışının artımı sahələrin artım
# sürətlərinin paylarla çəkilmiş cəminə bərabərdir (Törnqvist çəkiləri = qonşu illərin orta nominal payları). Bu,
# genişlənməni və ya daralmanı təmin edən sahələri heç bir modelləşdirmə fərziyyəsi olmadan müəyyən edir.
#
# ### 10.2 Ekonometrik cavab: amillər paneli
#
# $$\Delta \ln Q_{b,t} = \alpha_b + \tau_t + \beta_1\,\text{inv\_rate}_{b,t-1} + \beta_2\,\Delta\ln(P_b/P_C)_{t-1}
#   + \beta_3\,\text{nonstate}_{b,t-1} + \beta_4\,\text{stocks/GO}_{b,t-1} + \beta_5\,\Delta\ln N^{ent}_{b,t-1} + u_{b,t}$$
#
# tam məlumatı olan emal sənayesi sahələri (24-dən 21-i daxil olur; say çap olunur), 2011–2025 (investisiyalar yalnız
# 2010-cu ildən dəqiq toplanır, F3 tapıntısı). İki yönlü sabit effektlər (balanslaşdırılmamış panel üzrə dəqiq iki yönlü
# within çevrilməsi, fiktiv dəyişənlərlə (dummy) OLS-ə bərabərdir) sahəyə xas artımı və bütün ümumi il şoklarını (FR1-in
# makro tsiklini) aradan qaldırır; statistik nəticə ⌊T^¼⌋ gecikmə ilə Driscoll–Kraay üzrə **t(T−1)** paylanması ilə
# aparılır — effektiv müşahidələrin sayı illərin sayıdır — və hər əmsal üçün əlavə olaraq **klasterli vəhşi (wild)
# butstrap** p-dəyəri hesablanır (klasterlər = illər, Webb çəkiləri, sıfır fərziyyəsi qoyulmaqla). İzahedici dəyişənlər
# əvvəlcədən müəyyən olunmuş qalmaları üçün bir il gecikdirilir; sahə buraxılışının artımı heç vaxt sağ tərəfdə yer almır.
# İkinci spesifikasiya işçi sayı məlumatı olan yerlərdə (2018–2025) real məhsul əmək haqqı və əmək məhsuldarlığı
# terminlərini əlavə edir. **Between** qiymətləndiricisi (sahə ortaları) within qiymətləndirməsinin yanında verilir və
# təsir kimi şərh edilmir: o, sahəni nəyin böyütdüyünü deyil, hansı *növ* sahələrin daha sürətlə böyüdüyünü göstərir.
#
# **Bölmə meyli (division bias).** Məxrəcində buraxılış olan nisbətlər (investisiya/buraxılış, ehtiyatlar/buraxılış,
# əməyin payı) buraxılışın artımı ilə ortaq ölçmə xətasına malikdir. Buna görə onların məxrəcləri **t−2** dövrü üzrə
# (surət t−1 üzrə) götürülür; əmsalların nə qədər dəyişdiyini göstərmək üçün eyni il məxrəcli variant da yanında verilir.
#
# İxrac yönümlülüyü, kredit və enerji xərcləri bu tənliyə aid olardı; sahələr üzrə onların heç biri mövcud deyil
# (boşluqlar cədvəli).

# %%
w_ = ((SH_MAN + SH_MAN.shift(1)) / 2)
dq = np.log(Q[MANUF]).diff()
contrib = (w_ * dq) * 100
DECOMP = pd.DataFrame({'Törnqvist manufacturing growth, %': contrib.sum(axis=1, min_count=24)}).loc[2006:LAST_ACT]
cum = contrib.loc[2016:LAST_ACT].sum().sort_values()
print(f'contributions to manufacturing real growth 2016-{LAST_ACT} (log points x100, sum {cum.sum():.1f}):')
print('   top: ' + ', '.join(f'{BNAME[b]} {v:+.1f}' for b, v in cum[::-1].head(5).items()))
print('   bottom: ' + ', '.join(f'{BNAME[b]} {v:+.1f}' for b, v in cum.head(4).items()))
_chk = (DECOMP.iloc[:, 0] - (w_ * dq).sum(axis=1).loc[2006:] * 100).abs().max()
GROWTH_CONTRIB = contrib.loc[2006:LAST_ACT].rename(columns=BNAME)

PNL = []
for b in MANUF:
    d = pd.DataFrame({'year': range(2006, LAST_ACT + 1)})
    d['unit'] = b
    y_ = d.year
    d['dlnQ'] = dq[b].reindex(y_).values * 100
    d['inv_rate_l1'] = (INV[b].shift(1) / GO[b].shift(2) * 100).reindex(y_).values          # denominator at t-2
    d['inv_rate_l1_same'] = (INV[b] / GO[b] * 100).shift(1).reindex(y_).values
    d['drelp_l1'] = (np.log(PDEF[b] / (GO_C.sum(axis=1) / chain_level(GO_all['C'], VI['C']))).diff() * 100).shift(1).reindex(y_).values
    d['nonstate_l1'] = (NS[b] * 100).shift(1).reindex(y_).values
    d['stocks_go_l1'] = (STK[b].shift(1) / GO[b].shift(2) * 100).reindex(y_).values if b in STK else np.nan
    d['stocks_go_l1_same'] = (STK[b] / GO[b] * 100).shift(1).reindex(y_).values if b in STK else np.nan
    d['dln_ent_l1'] = (np.log(NENT[b]).diff() * 100).shift(1).reindex(y_).values
    d['dln_rwage_l1'] = (np.log(WAGEC[b] / PDEF[b]).diff() * 100).shift(1).reindex(y_).values
    d['labour_share_l1'] = (WBILL[b].shift(1) / GO[b].shift(2) * 100).reindex(y_).values
    d['labour_share_l1_same'] = (WBILL[b] / GO[b] * 100).shift(1).reindex(y_).values
    PNL.append(d)
PNL = pd.concat(PNL, ignore_index=True)
PNL = PNL[(PNL.year >= 2011)].replace([np.inf, -np.inf], np.nan)
# robustness to the extreme growth rates of very small branches: winsorise the dependent variable at 5/95%
lo, hi = PNL.dlnQ.quantile([0.05, 0.95])
PNL['dlnQ_w'] = PNL.dlnQ.clip(lo, hi)
REGS1 = ['inv_rate_l1', 'drelp_l1', 'nonstate_l1', 'stocks_go_l1', 'dln_ent_l1']
REGS2 = REGS1 + ['dln_rwage_l1', 'labour_share_l1']
DET_ROWS = []
for spec, regs, yrs in [('A: 2011-2025, core', REGS1, (2011, LAST_ACT)), ('B: 2018-2025, + wage and labour share', REGS2, (2018, LAST_ACT))]:
    d = PNL[(PNL.year >= yrs[0]) & (PNL.year <= yrs[1])].dropna(subset=['dlnQ_w'] + regs)
    f = panel_fe(d, 'dlnQ_w', regs)
    bw = between_fit(d, 'dlnQ_w', regs)
    for j, r in enumerate(regs):
        wp, _ = wild_cluster_p(d, 'dlnQ_w', regs, r, B=999)
        DET_ROWS.append(dict(spec=spec, regressor=r, coef=f.beta[j], se_DK=f.se[j], p_DK_t=f.pval[j], p_wild=wp,
                             between_coef=bw.beta[bw.names.index(r)], between_p=bw.pval[bw.names.index(r)],
                             n=f.n, branches=f.nN, years=f.nT, df=f.dof, DK_lags=f.dk_lags))
DET = pd.DataFrame(DET_ROWS)
display(DET.round(3))
DIVB = []
for spec, regs, yrs in [('A', REGS1, 2011), ('B', REGS2, 2018)]:
    regs_s = [r + '_same' if r + '_same' in PNL else r for r in regs]
    d = PNL[PNL.year >= yrs].dropna(subset=['dlnQ_w'] + regs + regs_s)
    f1_, f2_ = panel_fe(d, 'dlnQ_w', regs), panel_fe(d, 'dlnQ_w', regs_s)
    for j, r in enumerate(regs):
        if regs_s[j] != r:
            DIVB.append(dict(spec=spec, regressor=r, coef_t2_denominator=f1_.beta[j], coef_same_year_denominator=f2_.beta[j],
                             change=f1_.beta[j] - f2_.beta[j], p_t2=f1_.pval[j], p_same=f2_.pval[j]))
DIVB = pd.DataFrame(DIVB)
print('division bias: coefficients with t-2 denominators (used) vs same-year denominators')
display(DIVB.round(3))
sig = DET[(DET.p_DK_t < 0.10) & (DET.p_wild < 0.10)]
print('within-branch effects significant at 10% on BOTH the DK t(T-1) and the wild-bootstrap test: ' +
      (', '.join(f'{r.regressor} ({r.spec[:1]}) {r.coef:+.3f}' for _, r in sig.iterrows()) if len(sig) else 'none'))
print('Reading: with 15 (8) years of data the panel has the power of 14 (7) observations; coefficients that are not')
print('significant are "not established (low power)", not "no effect". The decomposition in 10.1 is exact and is the')
print('robust answer to "which branches drove growth"; the panel is the answer to "what is associated with it".')
for _, r in DET.iterrows():
    if r.p_DK_t > 0.10 or r.p_wild > 0.10:
        reject(f'{r.regressor} as a determinant of branch growth ({r.spec[:1]})', 'determinants panel',
               'NOT ESTABLISHED (low power)', f'coef {r.coef:+.3f}, DK p {r.p_DK_t:.2f} on t({int(r.df)}), wild p {r.p_wild:.2f}')
# sector linkage: how branch growth co-moves with FR1's manufacturing aggregate (branch FE, no year FE)
d = PNL.merge(pd.DataFrame({'year': F1H.index, 'dln_rva_man': np.log(F1H.rva_man).diff().values * 100}), on='year')
fl = panel_fe(d.dropna(subset=['dlnQ_w', 'dln_rva_man']), 'dlnQ_w', ['dln_rva_man'], twoway=False)
LINK = dict(coef=float(fl.beta[0]), se=float(fl.se[0]), p=float(fl.pval[0]), n=fl.n)
print(f'average co-movement of branch real growth with FR1 manufacturing real VA growth (branch FE, DK): '
      f'{LINK["coef"]:.2f} (s.e. {LINK["se"]:.2f}, p {LINK["p"]:.3f}) - descriptive; the aggregate is partly the sum of the branches')
fig, ax = plt.subplots(figsize=(13, 4.2))
c_ = contrib.loc[2006:LAST_ACT]
big = cum.abs().sort_values(ascending=False).head(7).index
bottom = np.zeros(len(c_)); bneg = np.zeros(len(c_))
for i, b in enumerate(list(big) + ['rest']):
    v = (c_[b] if b != 'rest' else c_.drop(columns=big).sum(axis=1)).values
    ax.bar(c_.index, np.where(v > 0, v, 0), bottom=bottom, color=PAL[i % len(PAL)], label=BNAME.get(b, 'other branches'))
    ax.bar(c_.index, np.where(v < 0, v, 0), bottom=bneg, color=PAL[i % len(PAL)])
    bottom += np.where(v > 0, v, 0); bneg += np.where(v < 0, v, 0)
ax.plot(DECOMP.index, DECOMP.iloc[:, 0], color='k', lw=1.5, marker='o', ms=3, label='manufacturing growth')
ax.set_title('Contributions to real manufacturing output growth, log points x100'); ax.legend(fontsize=6.5, ncol=4)
plt.tight_layout(); plt.show()
