# %% [markdown]
# ## Hissə 11 — Giriş/çıxış panelləri və struktur modellər
#
# Zaman ölçüsünə iki panel malikdir: **fəaliyyət paneli** (DSK-nın 11 qrupu × 2019, 2020, 2022, 2023, 2024; qeydiyyatdan
# keçmiş sahibkarlıq subyektləri, 006) və **region paneli** (14 iqtisadi rayon × 2021–2025; statistik vahidlər).
#
# **Giriş əmsal kimi deyil, axın kimi modelləşdirilir**: yeni qeydiyyatların (yaradılmaların) loqarifmi, vahid sabit
# effektləri ilə və gecikmiş asılı dəyişən olmadan, $\ln B_{it} = a_i + \sum_k b_k x_{k,it} + \delta\,\mathrm{brk}_t + u_{it}$.
# Giriş *əmsalı* sonra ehtiyat-axın eyniliyindən alınır, $e_t = B_t/N_t$, burada $N_t = (N_{t-1}+B_t)/(1+x_t)$; beləliklə,
# doğumlar eyni sürətlə artmırsa, ehtiyat böyüdükcə əmsal azalır. Sabit vahid ortası olan əmsal modeli bunu edə bilməz
# (yoxlama zamanı aşkar edilmiş artefakt). **Çıxış** əmsal modeli olaraq qalır, $x_{it} = a_i + \sum_k b_k x_{k,it} + u_{it}$
# (ölümlər ehtiyatla mütənasibdir). Fəaliyyət paneli: `brk` = 2022-ci ildən 1, 006-da DSK tərifinin dəyişməsi (2020-ci
# ilədək "yeni yaradılmış / ləğv edilmiş" → 2022-ci ildən "yeni qeydiyyata alınmış / qeydiyyatdan çıxarılmış", F17
# tapıntısı); çıxış tənliyi 2022-ci il impulsunu daşıyır (F16: 2023–2024 çıxış səviyyələri 2019–2020-yə yaxındır, buna
# görə davamlı qırılma görünmür). 2020-ci ilin kənd təsərrüfatı üzrə qeydiyyat dalğası (F7) xaric edilir.
#
# Namizəd sürücülər — fəaliyyət: sektor tələbinin artımı `dem` (qrupun sektorunun FR1 real ƏD-si, % dəyişmə), sektorun
# ölçüsü `size` (log real ƏD), kredit faiz dərəcəsi `lend`, real kreditin artımı `cred` (FR1), qiymət-xərc marjası proksisi
# `pcm`. Region: regional sənaye buraxılışının artımı `reg` və ölçüsü `size` (FR10), qeyri-neft ÜDM-in artımı `non`,
# kredit faiz dərəcəsi `lend` (FR1). Milli sürücülər yalnız zamana görə dəyişir, buna görə il effektləri əlavə edilə
# bilməz. Statistik nəticə: T = 5 il olduqda Driscoll–Kraay t(T−1) p-dəyərləri etibarsızdır və **verilmir**; cədvəl
# **klasterli vəhşi (wild) butstrap** p-dəyərini verir (Webb altı nöqtəli çəkiləri, klasterlər = illər, sıfır fərziyyəsi
# qoyulmaqla, B = 499). 5 klasterlə o kobuddur; qiymətləndirmələr təsviri xarakter daşıyır.

# %%
def dln(s): return np.log(s).diff() * 100
FR1X = pd.DataFrame({'lend': FR1H.lendrate, 'cred': dln(FR1H.rcred_tot), 'non': dln(FR1H.rgdpnon)})
VAH = pd.DataFrame({g: FR1H[GROUPS[g][2]].sum(axis=1) for g in GRP})
PA = []
for (g, y), r in G.iterrows():
    PA.append(dict(unit=g, year=y, B=r.new, D=r.dereg, N=r.registered, entry=r.entry, exit=r.exit, dem=dln(VAH[g]).get(y),
                   lend=FR1X.lend.get(y), cred=FR1X.cred.get(y), pcm=PCM_G.PCM.get((g, y)), size=np.log(VAH[g]).get(y)))
PA = pd.DataFrame(PA)
PA['lnB'] = np.log(PA.B); PA['brk'] = (PA.year >= 2022).astype(float); PA['d2022'] = (PA.year == 2022).astype(float)
PA.loc[(PA.unit == 'AGR') & (PA.year == 2020), ['lnB', 'entry']] = np.nan        # F7: administrative farm-registration wave
_rgo = FR10_REGH.pivot_table(index='year', columns='region', values='value')
PR = RG[['region', 'year', 'new', 'liquidated', 'enterprises', 'entry', 'exit']].rename(columns={'region': 'unit', 'new': 'B', 'liquidated': 'D', 'enterprises': 'N'}).copy()
PR['lnB'] = np.log(PR.B)
PR['reg'] = [dln(_rgo[u]).get(y) for u, y in zip(PR.unit, PR.year)]
PR['size'] = [np.log(_rgo[u]).get(y) for u, y in zip(PR.unit, PR.year)]
PR['non'] = PR.year.map(FR1X.non); PR['lend'] = PR.year.map(FR1X.lend)
assert PA[['dem', 'lend', 'cred', 'pcm', 'size']].notna().all().all() and PR[['reg', 'non', 'lend', 'size']].notna().all().all()
SPA = [[], ['size'], ['dem'], ['size', 'dem'], ['size', 'lend'], ['size', 'cred'], ['dem', 'lend'], ['pcm'], ['size', 'pcm']]
SPX = [[], ['dem'], ['dem', 'pcm'], ['dem', 'cred'], ['lend'], ['cred'], ['size']]
SPR = [[], ['reg'], ['size'], ['reg', 'size'], ['non'], ['non', 'lend'], ['reg', 'lend']]
MODELS = {
 ('activity', 'lnB'): dict(df=PA, fixed=['brk'], specs=SPA, sel=(2022, [2023]), hold=[(2022, [2024]), (2023, [2024])], scale='log births'),
 ('activity', 'exit'): dict(df=PA, fixed=['d2022'], specs=SPX, sel=(2022, [2023]), hold=[(2022, [2024]), (2023, [2024])], scale='exit rate, %'),
 ('region', 'lnB'): dict(df=PR, fixed=[], specs=SPR, sel=(2022, [2023]), hold=[(2023, [2024, 2025]), (2024, [2025])], scale='log births'),
 ('region', 'exit'): dict(df=PR, fixed=[], specs=SPR, sel=(2022, [2023]), hold=[(2023, [2024, 2025]), (2024, [2025])], scale='exit rate, %')}
PANELS = {'activity': PA, 'region': PR}

def fit_fe(df, dep, regs, fixed=()):
    fixed = [c for c in fixed if c in df]
    d = df.dropna(subset=[dep] + regs + fixed)
    fx = [c for c in fixed if d[c].std() > 0]
    allr = list(regs) + fx
    if not allr:
        a = d.groupby('unit')[dep].mean()
        return dict(regs=[], b=np.zeros(0), V=np.zeros((0, 0)), fixed=[], bf=np.zeros(0), a=a, resid=d[dep] - d.unit.map(a), fit=None, d=d)
    f = panel_fe(d, dep, allr, entity='unit', time='year', twoway=False)
    Xa = d[allr].to_numpy(float)
    a = (d[dep] - Xa @ f.beta).groupby(d.unit).mean()
    k = len(regs)
    return dict(regs=list(regs), b=f.beta[:k], V=f.V[:k, :k], fixed=fx, bf=f.beta[k:], a=a, resid=d[dep] - d.unit.map(a) - Xa @ f.beta, fit=f, d=d)

def predict(m, rows, b=None):
    b = m['b'] if b is None else b
    p = rows.unit.map(m['a']).to_numpy(float)
    if m['regs']: p = p + rows[m['regs']].to_numpy(float) @ b
    if m['fixed']: p = p + rows[m['fixed']].to_numpy(float) @ m['bf']
    return p

def spec_name(s): return 'null (FE + fixed terms)' if not s else 'FE + ' + ' + '.join(s)

FULL = []
for (pn, dep), M in MODELS.items():
    for s in M['specs'][1:]:
        m = fit_fe(M['df'], dep, s, M['fixed'])
        d_ = m['d']; regs_all = s + m['fixed']
        for j, x in enumerate(s):
            p_w, t_w = wild_cluster_p(d_, dep, regs_all, x, entity='unit', time='year', twoway=False, B=499, seed=SEED + j)
            FULL.append(dict(panel=pn, dep=dep, spec=spec_name(s), driver=x, coef=m['b'][j], se_DK=m['fit'].se[j], wcb_p=p_w, T=m['fit'].nT, n=m['fit'].n))
FULL = pd.DataFrame(FULL)
print('full-sample FE estimates (descriptive; wild cluster bootstrap p by year, Webb, B = 499; DK p-values not reported with T = 5):')
display(FULL.round(3))
