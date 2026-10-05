# %% [markdown]
# ## Hissə 7 — A qatının analitikası: üç sütun, tarixi dövr 2005–2025
#
# ### 7.1 Bazar mövqeyi
#
# Burada bazar payı sahənin (və ya regionun, ya da mülkiyyət qrupunun) ana aqreqatın **nominal** buraxılışındakı payıdır:
# nominal dəyərlər dəqiq toplanır, zəncirvari həcmlər isə toplanmır (FR1 və FR5-in sənədləşdirdiyi qeyri-additivlik).
# Sahələr və regionlar üzrə konsentrasiya Herfindahl–Hirschman indeksi (HHI, ×10 000) və dörd vahid üzrə konsentrasiya
# əmsalı CR4 ilə ölçülür. **Müəssisə səviyyəsində konsentrasiyanı bu məlumatlardan hesablamaq mümkün deyil**; onların
# imkan verdiyi yalnız *hədd*dir: N ən böyük müəssisə buraxılışın $s$ payını istehsal edirsə, müəssisə səviyyəsində HHI
# ən azı $s^2/N$-dir (onlar arasında bərabər bölgü). Buradan ekvivalent müəssisə sayı üçün $N/s^2$ həddi alınır.

# %%
GO_C = GO[MANUF]; GO_B = GO[MINING]
SH_MAN = GO_C.div(GO_C.sum(axis=1), axis=0)                 # shares within manufacturing
SH_MIN = GO_B.div(GO_B.sum(axis=1), axis=0)                 # shares within mining
SH_IND = GO.div(GO.sum(axis=1), axis=0)                     # shares within industry
SEC_GO = pd.DataFrame({'B': GO_B.sum(axis=1), 'C': GO_C.sum(axis=1), 'D': GO['35'], 'E': GO['36']})
SH_SEC = SEC_GO.div(SEC_GO.sum(axis=1), axis=0)
def hhi(S): return (S ** 2).sum(axis=1) * 1e4
def cr4(S): return S.apply(lambda r: r.sort_values(ascending=False).head(4).sum(), axis=1) * 100
REG_SH = REG_GO.div(REG_GO.sum(axis=1), axis=0)
CONC = pd.DataFrame({'HHI manufacturing branches': hhi(SH_MAN), 'CR4 manufacturing, %': cr4(SH_MAN),
                     'HHI industry branches': hhi(SH_IND), 'CR4 industry, %': cr4(SH_IND),
                     'HHI 14 regions': hhi(REG_SH), 'CR4 regions, %': cr4(REG_SH)}).loc[2005:LAST_ACT]
display(CONC.loc[[2005, 2010, 2015, 2019, 2020, 2022, 2024, LAST_ACT]].round(1))
top = SH_MAN.loc[LAST_ACT].sort_values(ascending=False)
print(f'{LAST_ACT} manufacturing leaders: ' + ', '.join(f'{BNAME[b]} {v*100:.1f}%' for b, v in top.head(5).items()))
ch = (SH_MAN.loc[LAST_ACT] - SH_MAN.loc[2015]) * 100
print('share gains 2015-2025, pp: ' + ', '.join(f'{BNAME[b]} {v:+.1f}' for b, v in ch.sort_values(ascending=False).head(4).items())
      + ' | losses: ' + ', '.join(f'{BNAME[b]} {v:+.1f}' for b, v in ch.sort_values().head(4).items()))

# ownership: the composition identity reproduces the published non-state share
NS_COMP = (GO[BCODES] * NS[BCODES]).sum(axis=1, min_count=20) / GO[BCODES].where(NS[BCODES].notna()).sum(axis=1, min_count=20)
own = pd.DataFrame({'published non-state share, %': NS['ALL'] * 100, 'composition identity, %': NS_COMP * 100,
                    'non-state share of manufacturing, %': NS['C'] * 100, 'non-state share of mining, %': NS['B'] * 100}).loc[2005:LAST_ACT]
own['identity gap, pp'] = own.iloc[:, 1] - own.iloc[:, 0]
display(own.loc[[2005, 2010, 2015, 2020, 2023, 2024, LAST_ACT]].round(2))
OWN_BAD = own['identity gap, pp'][own['identity gap, pp'].abs() > 0.5]
OWN_GAP = float(own['identity gap, pp'].drop(OWN_BAD.index).abs().max())
print(f'the branch-weighted non-state share reproduces the published industry figure to {OWN_GAP:.2f} pp, except in '
      + ', '.join(f'{int(y)} ({v:+.1f} pp)' for y, v in OWN_BAD.items()) + ' (Part 6, finding F12)')
finding('F12', 'The published non-state share of industry is inconsistent with its own branch breakdown in some years',
        'output-weighted branch non-state shares (DSK 010_2 x 010) differ from the published industry total by '
        + ', '.join(f'{int(y)} {v:+.1f} pp' for y, v in OWN_BAD.items()) + f'; within {OWN_GAP:.2f} pp in every other year',
        'The forecast of the non-state share is built from the branch composition (consistent by construction); the '
        'published total for those years should be queried with DSK')
FINDINGS = pd.DataFrame(FIND).set_index('id')

# enterprises, entry and exit, size classes, SMEs, firm-concentration bound
ENT = pd.DataFrame({'industry enterprises': NENT['ALL'], 'manufacturing': NENT['C'], 'mining': NENT['B'],
                    'state-owned (industry)': d047.set_index('label').loc['State property', [c for c in d047.columns if isinstance(c, (int, np.integer))]].astype(float),
                    'non-state (industry)': d047.set_index('label').loc['Non-state property', [c for c in d047.columns if isinstance(c, (int, np.integer))]].astype(float)})
ENT['net entry rate, % (industry)'] = ENT['industry enterprises'].pct_change() * 100
display(ENT.loc[[2005, 2010, 2015, 2019, 2021, 2023, 2024, LAST_ACT]].round(1))
sz = SIZE[SIZE.label == 'All industry'].pivot_table(index='year', columns='size_class', values='n')
sme_ind = SME_SHARE_OUT[SME_SHARE_OUT.label_en.str.contains('Industr')].iloc[0]
s_large = 1 - sme_ind.total_2024 / 100
n_large = float(ST_LARGE[ST_LARGE.activity.str.contains('Manufacturing|Mining|Electricity|Water')].large_units.sum())
HHI_BOUND = dict(non_sme_output_share=s_large, n_large_units=n_large, hhi_lower_bound=s_large ** 2 / n_large * 1e4,
                 equiv_firms_upper=n_large / s_large ** 2)
print(f'firm-level concentration bound: large (non-SME) enterprises produce {s_large*100:.1f}% of industrial output (2024, '
      f'= 100 - SME share); the register counts {n_large:.0f} large industrial units (1 Jul 2026). Split equally among them that '
      f'output gives HHI = s^2/N = {HHI_BOUND["hhi_lower_bound"]:.1f}; any unequal split, and the SME part, can only raise it, so it is a '
      f'lower bound (equivalent number of firms <= {HHI_BOUND["equiv_firms_upper"]:.0f}); the two sources refer to different dates. The actual HHI needs firm data (Layer B)')
ENTRY_REG = ST_ENTRY.copy()
display(ENTRY_REG[ENTRY_REG.activity.str.contains('Total|Mining|Manufactur|Electric|Water')].reset_index(drop=True))
rw = RG_WB.pivot_table(index=['region', 'year'], columns='var', values='value')
rw['entry_rate_pct'] = rw.new / rw.enterprises * 100; rw['exit_rate_pct'] = rw.liquidated / rw.enterprises * 100
REG_ENTRY = rw.reset_index()

# products: volumes in kind, growth 2020-2025, linked to branches
yc18 = [c for c in PROD.columns if isinstance(c, (int, np.integer))]
pv = PROD.set_index('label')[yc18].astype(float)
PROD_VIEW = pd.DataFrame({'branch': PROD.set_index('label').branch, 'unit': [l.split(',')[-1].strip() for l in pv.index],
                          f'{LAST_ACT - 5}': pv[LAST_ACT - 5], f'{LAST_ACT}': pv[LAST_ACT],
                          'growth 2020-2025, % a year': ((pv[LAST_ACT] / pv[LAST_ACT - 5]) ** (1 / 5) - 1) * 100})
PROD_VIEW = PROD_VIEW[np.isfinite(PROD_VIEW['growth 2020-2025, % a year'])]
print(f'products with a 2020-2025 growth rate: {len(PROD_VIEW)}; fastest: ' +
      ', '.join(f'{i.split(",")[0]} {v:+.0f}%' for i, v in PROD_VIEW['growth 2020-2025, % a year'].sort_values(ascending=False).head(3).items()))
pk = PARKS[PARKS.park.str.contains('zonaları üzrə cəmi')].pivot_table(index='year', columns='indicator', values='value')
PARK_TOT = pk[[c for c in pk.columns if c.startswith(('Faktiki', 'İstehsalın həcmi', 'İxracın həcmi', 'İnvestisiyanın'))]]
display(PARK_TOT.round(1))

fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
for i, b in enumerate(top.head(8).index):
    ax[0].plot(SH_MAN.loc[2005:].index, SH_MAN.loc[2005:, b] * 100, color=PAL[i], lw=1.6, label=BNAME[b])
ax[0].set_title('Shares of manufacturing output, % (8 largest in 2025)'); ax[0].legend(fontsize=6.5)
ax[1].plot(CONC.index, CONC['HHI manufacturing branches'], lw=2, label='HHI manufacturing branches')
ax[1].plot(CONC.index, CONC['HHI 14 regions'], lw=2, label='HHI 14 regions'); ax[1].legend(fontsize=7)
ax[1].set_title('Concentration (HHI x 10 000)')
ax[2].plot(own.index, own.iloc[:, 0], lw=2, label='industry'); ax[2].plot(own.index, own.iloc[:, 2], lw=2, label='manufacturing')
ax[2].plot(own.index, own.iloc[:, 3], lw=2, label='mining'); ax[2].set_title('Non-state share of output, %'); ax[2].legend(fontsize=7)
plt.tight_layout(); plt.show()

# %% [markdown]
# ### 7.2 İstehsal səmərəliliyi
#
# | Göstərici | Düstur | Mənbə |
# |---|---|---|
# | Əmək məhsuldarlığı (buraxılış) | real ümumi buraxılış / işçilər | DSK 010, 009; iş kitabı və DSK 006 işçi sayı |
# | Əmək məhsuldarlığı (ƏD) | real əlavə dəyər / işçilər (ƏD sahə buraxılışının deflyatoru ilə deflyasiya edilir — tək deflyasiya, açıq göstərilir) | DSK MH 015_2 |
# | Aralıq istehlakın payı | Aİ / buraxılış | DSK MH 015, 015_1 |
# | Kapital məhsuldarlığı | real buraxılış / real kapital (sahə investisiyalarından fasiləsiz inventar üsulu, FR1-də olduğu kimi δ = 0,07; 2010-cu il ehtiyatı = bölmənin **müşahidə olunan** əsas fondları (DSK MH 031, FR1-in investisiya deflyatoru ilə deflyasiya edilib) 2005–10 investisiya payları üzrə bölüşdürülür) | DSK 019, MH 031 |
# | TFP artımı (ümumi buraxılış, Törnqvist) | Δln Q − s̄_M Δln M − s̄_L Δln L − s̄_K Δln K, **müşahidə olunan** paylarla: s_M = Aİ/ÜB, s_L = ümumi əmək haqqı fondu/ÜB (işəgötürən ayırmaları 22%, FR1), s_K = 1 − s_M − s_L | yuxarıdakı kimi |
# | TFP artımı (əlavə dəyər, bölmələr) | Δln VA − s̄_L Δln L − (1−s̄_L) Δln K, s_L = əməyin ödənilməsi/ƏD, K = sabit qiymətlərlə müşahidə olunan əsas fondlar (MH 031) | DSK MH 013, 031; FR1 rva_*, p_inv; FR4 muzdlu işçilər |
# | Əmək haqqı–məhsuldarlıq fərqi | Δln(əmək haqqı / buraxılış deflyatoru) − Δln LP | iş kitabı / DSK 006_2 |
# | İnnovasiya intensivliyi | innovasiya xərcləri / buraxılış | DSK 020_3 |
#
# Heç bir istehsal funksiyası parametri qiymətləndirilmir: tapşırığın tələb etdiyi kimi, xərc payları müşahidə olunur.
# Müşahidə olunan əmək və material xərcləri buraxılışı aşdıqda qalıq kapital payı mənfi olardı; belə sahə-illər məcburi
# düzəldilmir, işarələnir.

# %%
EMPC = WEMP[BCODES].loc[2016:LAST_ACT - 1].combine_first(EMP_DSK[BCODES]).loc[2016:LAST_ACT]   # DSK for 2025 (F2)
WAGEC = WWAGE[BCODES].loc[2016:LAST_ACT - 1].combine_first(WAGE_DSK[BCODES]).loc[2016:LAST_ACT]
SSC = 0.22                                                                                 # as FR1 EMPLOYER_SSC
WBILL = WAGEC * EMPC * 12 / 1e6 * (1 + SSC)                                                # mn AZN, gross of employer SSC
VA_B = NA_VA[[b for b in MANUF]].copy()
VA_B['06'] = NA_VA['06']; VA_B['35'] = NA_VA['D']; VA_B['36'] = NA_VA['E']
IC_SH = (NA_IC / NA_GO)[MANUF + ['06']].rename(columns={})
LP_GO = (Q[BCODES] / EMPC * 1e3).loc[2016:LAST_ACT]                                         # thousand AZN (2015 prices) per employee
LP_VA = (VA_B / PDEF[VA_B.columns] / EMPC[VA_B.columns] * 1e3).loc[2016:LAST_ACT]
# perpetual-inventory capital by branch, consistent with FR1's section capital in 2010
DELTA = 0.07
PINV = F1H.p_inv
K = {}
FA_REAL = FA.div(PINV, axis=0).loc[2006:]          # FR1's investment deflator has a level break 2005/06: start 2006
for sec, cols in [('C', MANUF), ('B', MINING)]:
    cum = INV.loc[2005:2010, cols].fillna(0).sum()
    for b in cols:
        k = pd.Series(np.nan, index=range(2010, LAST_ACT + 1), dtype=float)
        k[2010] = FA_REAL.loc[2010, sec] * cum[b] / cum.sum() if cum[b] > 0 else np.nan
        for y in range(2011, LAST_ACT + 1):
            k[y] = (1 - DELTA) * k[y - 1] + np.nan_to_num(INV.loc[y, b]) / PINV.loc[y]
        K[b] = k
for b, sec in [('35', 'D'), ('36', 'E')]:
    K[b] = FA_REAL[sec].loc[2010:LAST_ACT]
K = pd.DataFrame(K)
KPROD = (Q[BCODES].loc[2010:LAST_ACT] / K[BCODES])
INV_RATE = (INV[BCODES] / GO[BCODES] * 100)

def tornqvist_tfp(b):
    y = list(range(2017, LAST_ACT + 1))
    go, ic = NA_GO[b] if b in NA_GO else GO[b], NA_IC[b] if b in NA_IC else np.nan
    sM = (NA_IC[b] / NA_GO[b]) if b in NA_IC else pd.Series(np.nan, index=GO.index)
    sL = WBILL[b] / GO[b]
    sK = 1 - sM - sL
    dQ = np.log(Q[b]).diff(); dM = np.log(NA_IC[b] / PDEF[b]).diff() if b in NA_IC else np.nan
    dL = np.log(EMPC[b]).diff(); dK = np.log(K[b]).diff()
    av = lambda s: (s + s.shift(1)) / 2
    t = dQ - av(sM) * dM - av(sL) * dL - av(sK) * dK
    return pd.DataFrame({'dlnQ': dQ, 'contrib_M': av(sM) * dM, 'contrib_L': av(sL) * dL, 'contrib_K': av(sK) * dK,
                         'dlnTFP': t, 'sM': sM, 'sL': sL, 'sK': sK}).loc[y]
TFP = pd.concat({b: tornqvist_tfp(b) for b in MANUF}, names=['branch', 'year'])
neg_sk = TFP[TFP.sK < 0]
_sum = lambda s: s.sum(min_count=len(s))          # a branch with any missing year has no cumulative TFP
TFP_SUM = TFP.groupby(level=0).agg(dlnQ=('dlnQ', _sum), contrib_M=('contrib_M', _sum), contrib_L=('contrib_L', _sum),
                                   contrib_K=('contrib_K', _sum), dlnTFP=('dlnTFP', _sum), mean_sK=('sK', 'mean'))
TFP_SUM = (TFP_SUM * [100, 100, 100, 100, 100, 1]).rename(index=BNAME)
TFP_SUM.columns = ['output growth 2016-25, log pts x100', 'materials', 'labour', 'capital', 'TFP', 'mean capital share']
gap_ = (TFP.dlnQ - TFP.contrib_M - TFP.contrib_L - TFP.contrib_K - TFP.dlnTFP).abs().max()
print(f'gross-output Törnqvist TFP, 24 manufacturing branches, 2017-{LAST_ACT}: decomposition closes to {gap_:.1e} (arithmetic); '
      f'{len(neg_sk)} branch-years have labour + materials cost shares above 1 (negative residual capital share) - flagged')
display(TFP_SUM.sort_values('TFP', ascending=False).round(2))

# section level (value added), 2006-2025: FR1 real VA and capital, NA labour share, FR4/DSK hired employees
HIRED_H = pd.read_csv(OUT / 'FR4_dsk_hired_by_activity_history.csv', index_col=0)
FR4H_B = FR4H[FR4H.scenario == 'Baseline'].set_index('year')
SEC_TFP = {}
for sec, v, h4 in [('B', 'min', 'mining'), ('C', 'man', 'manuf'), ('D', 'elc', 'elec'), ('E', 'wat', 'water')]:
    L_ = HIRED_H[h4].copy(); L_.loc[LAST_ACT] = FR4H_B.loc[LAST_ACT, h4] if LAST_ACT not in L_.index else L_.loc[LAST_ACT]
    sL = (INC.loc[sec].CE / INC.loc[sec].VA).clip(0, 1)
    dVA = np.log(F1H[f'rva_{v}']).diff(); dL = np.log(L_).diff(); dK = np.log(FA_REAL[sec]).diff()
    a = (sL + sL.shift(1)) / 2
    SEC_TFP[SECT[sec]] = pd.DataFrame({'dlnVA': dVA, 'labour': a * dL, 'capital': (1 - a) * dK,
                                       'TFP': dVA - a * dL - (1 - a) * dK}).loc[2007:LAST_ACT]
SEC_TFP = pd.concat(SEC_TFP, names=['section', 'year'])
st_ = SEC_TFP.groupby(level=0).agg(['mean']).droplevel(1, axis=1) * 100
st_.columns = [c + ', % a year (2007-2025 mean)' for c in st_.columns]
display(st_.round(2))
WPG = pd.DataFrame({'real product wage growth': np.log(WAGEC[MANUF] / PDEF[MANUF]).diff().loc[2017:].sum(),
                    'labour productivity growth': np.log(LP_GO[MANUF]).diff().loc[2017:].sum()}) * 100
WPG['gap (wage - productivity), log pts'] = WPG.iloc[:, 0] - WPG.iloc[:, 1]
INNOV_INT = (INNOV.reindex(columns=BCODES) / 1000 / GO[BCODES] * 100)

# %% [markdown]
# ### 7.3 Maliyyə vəziyyəti
#
# Rentabelliyə üç baxış bucağı, hər birinin məhdudiyyətləri göstərilməklə:
#
# 1. **Bölmələr üzrə milli hesablar** (DSK MH 013, 2005–2025): ümumi əməliyyat mənfəəti = əlavə dəyər − əməyin ödənilməsi −
#    istehsala digər vergilər; ÜƏM/buraxılış və ÜƏM/ƏD marjaları; əməyin payı; əsas kapitalın istehlakı.
# 2. **Emal sənayesi sahələri üzrə ÜƏM proksisi** (2016–2025): əlavə dəyər (DSK MH) − ümumi əmək haqqı fondu (iş kitabı /
#    DSK işçi sayı × orta əmək haqqı × 12 × 1,22). O, istehsala digər vergiləri (bölmə səviyyəsində ƏD-nin 0,3–1,0%-i) və
#    muzdlu olmayan işçilərin əməyinin ödənilməsini nəzərə almır, buna görə həqiqi marjanın yuxarı həddidir.
# 3. **Mənfəət vergisi bəyannamələri** (DVX, bütün ödəyicilər, 2021–2025): bəyannamə üzrə xalis marja, bəyan edilmiş
#    zərərlərin payı, effektiv vergi nisbəti (F7 tapıntısı) — sahə ölçüsü olmayan, bütün iqtisadiyyat üzrə aqreqatlar.
#
# Likvidlik, ödəmə qabiliyyəti, borc yükü, faiz ödənişinin örtülməsi və maliyyə çətinliyi göstəricisi balans hesabatları
# tələb edir: onlar B qatında müəyyən edilib və Vergi Xidmətinin / DSMF-nin panelini gözləyir.

# %%
SEC_FIN = INC.copy()
SEC_FIN['GOS_margin_GO'] = SEC_FIN.GOS / SEC_FIN.GO * 100; SEC_FIN['GOS_share_VA'] = SEC_FIN.GOS / SEC_FIN.VA * 100
SEC_FIN['labour_share_VA'] = SEC_FIN.CE / SEC_FIN.VA * 100; SEC_FIN['CFC_share_VA'] = SEC_FIN.CFC / SEC_FIN.VA * 100
SEC_FIN['IC_share_GO'] = SEC_FIN.IC / SEC_FIN.GO * 100
sf = SEC_FIN['GOS_share_VA'].unstack(0).rename(columns=SECT)
display(sf.loc[[2005, 2010, 2015, 2019, 2020, 2022, 2024, LAST_ACT]].round(1))
# margins use the national-accounts output of the same branch (consistent with its value added; DSK 010 output
# differs from NA output for a few small branches, e.g. machinery in 2025, where NA VA exceeds DSK 010 output)
GOSP = ((VA_B[MANUF] - WBILL[MANUF]) / NA_GO[MANUF] * 100).loc[2016:LAST_ACT]        # branch GOS-proxy margin, % of output
VA_MARG = (VA_B[MANUF] / NA_GO[MANUF] * 100).loc[2016:LAST_ACT]
print(f'branch GOS-proxy margin {LAST_ACT}: median {GOSP.loc[LAST_ACT].median():.1f}% of output; negative in '
      f'{int((GOSP.loc[LAST_ACT] < 0).sum())} branches: ' + ', '.join(BNAME[b] for b in GOSP.columns[GOSP.loc[LAST_ACT] < 0]))
DVX_M = pd.DataFrame({'profit-tax payers, thsd': DVX.pt_payers,
                      'declaration net margin, % of deductible expenses': true_marg,
                      'taxable profit / gross income, %': DVX.pt_profit / DVX.pt_income * 100,
                      'declared losses / taxable profit, %': DVX.pt_loss / DVX.pt_profit * 100,
                      'effective tax ratio (r223), %': DVX.pt_rent,
                      'tax arrears, mn AZN': DVX.arrears,
                      'industry turnover share of total, %': DVX.turn_ind / DVX.turn_total * 100})
display(DVX_M.round(2))
SELF_FIN = (RS.inv_own / RS.inv_total * 100).dropna()
print(f'investment self-financing (own funds / total investment, workbook Real sektor r114/r80): ' +
      ', '.join(f'{int(y)} {v:.1f}%' for y, v in SELF_FIN.items()) + ' (annual values exist only for these years)')
STK_RATIO = (STK.reindex(columns=BCODES) / GO[BCODES] * 100)
sme_rows = lambda df: df[df.label_en.str.contains('Industry|Mining|Manufact|Electric|Water')]
SME_FIN = pd.concat({'assets, mn AZN': sme_rows(SME_ASSETS).set_index('label_en')[['total_2023', 'total_2024']],
                     'stocks, thsd AZN': sme_rows(SME_STOCKS).set_index('label_en')[['total_2023', 'total_2024']],
                     'taxes paid, mn AZN': sme_rows(SME_TAX).set_index('label_en')[['total_2023', 'total_2024']]})
display(SME_FIN.round(1))

# the quadrant the presentation layer uses: efficiency vs financial health, manufacturing branches
QUAD = pd.DataFrame({'branch': [BNAME[b] for b in MANUF],
                     'LP growth 2020-25, % a year': (((LP_GO.loc[LAST_ACT, MANUF] / LP_GO.loc[2020, MANUF]) ** (1 / 5) - 1) * 100).values,
                     f'GOS-proxy margin {LAST_ACT}, %': GOSP.loc[LAST_ACT, MANUF].values,
                     f'share of manufacturing {LAST_ACT}, %': (SH_MAN.loc[LAST_ACT, MANUF] * 100).values}, index=MANUF)
mx, my = QUAD.iloc[:, 1].median(), QUAD.iloc[:, 2].median()
QUAD['quadrant'] = np.select([(QUAD.iloc[:, 1] >= mx) & (QUAD.iloc[:, 2] >= my), (QUAD.iloc[:, 1] >= mx) & (QUAD.iloc[:, 2] < my),
                              (QUAD.iloc[:, 1] < mx) & (QUAD.iloc[:, 2] >= my)],
                             ['efficient and profitable', 'efficient, thin margin', 'profitable, lagging efficiency'], 'lagging on both')
fig, ax = plt.subplots(1, 2, figsize=(15, 5.2))
a = ax[0]
a.scatter(QUAD.iloc[:, 1], QUAD.iloc[:, 2], s=QUAD.iloc[:, 3] * 40 + 10, alpha=0.6, color=PAL[0])
for b, r in QUAD.iterrows(): a.annotate(r.branch[:14], (r.iloc[1], r.iloc[2]), fontsize=6)
a.axvline(mx, color='grey', ls=':'); a.axhline(my, color='grey', ls=':')
a.set_xlabel('labour productivity growth 2020-25, % a year'); a.set_ylabel(f'GOS-proxy margin {LAST_ACT}, % of output')
a.set_title('Efficiency vs financial health (bubble = market share)')
for i, s_ in enumerate(['Mining', 'Manufacturing', 'Electricity', 'Water']):
    ax[1].plot(sf.index, sf[s_], lw=1.8, color=PAL[i], label=s_)
ax[1].axhline(0, color='k', lw=0.7); ax[1].set_title('Gross operating surplus, % of value added (DSK NA 013)'); ax[1].legend(fontsize=7)
plt.tight_layout(); plt.show()
display(QUAD.round(2).sort_values('quadrant'))
