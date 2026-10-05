# %% [markdown]
# ## Hissə 16 — Erkən xəbərdarlıq: rəqabət harada pisləşir?
#
# Hər siqnal son ortanı (son üç müşahidə; çıxış: son iki) əvvəlki orta ilə müqayisə edir, həmin sektorda göstəricinin öz
# illik dəyişkənliyi ilə miqyaslanır (z-göstəricisi) və əlverişsiz istiqamətdə |z| > z* olduqda verilir. Kompozit
# göstəricidəki siqnallar: **konsentrasiya** (iri müəssisələrin buraxılış payı artır), **giriş** (log yeni qeydiyyatlar
# azalır — axın, belə ki, artan ehtiyat yalançı azalma yarada bilməz), **çıxış** (çıxış əmsalı artır; 2022 dalğası xaric
# edilir), **payların mobilliyi** (sahə paylarının qeyri-sabitliyi azalır; yalnız sənaye), **giriş azaldıqca marjaların
# artması**. Çəkilər 0,25, 0,25, 0,15, 0,10, 0,25; göstərici = mövcud siqnallar arasında verilmiş siqnalların çəkili payı;
# nəzarət siyahısı: göstərici ≥ 0,30 və ya ≥ 2 siqnal. Çatışmayan məlumatlar sıfır deyil, "məlumat kifayət deyil" verir.
#
# **Kompozit göstəriciyə daxil deyil** (məlumat kimi verilir): verilmiş lisenziyalar — verilmənin artması baryer deyil,
# daha çox icazəli giriş deməkdir; **kohort ölçüsü nisbəti** (eyni ildə k yaşlı fəal KOB-lar / 1 yaşlı fəal KOB-lar; yalnız
# iki il — kohortun ölçüsünü sağ qalma ilə qarışdırır, buna görə sağ qalma əmsalı deyil; reyestr real olduqda sağ qalma
# B qatının Kaplan–Meier qiymətləndirməsindən gəlir); **fəal KOB-lar** arasında dövlət mülkiyyətinin payı (yalnız iki il).
#
# **z\* həddi** elə seçilir ki, **yalançı siyahıya salınma ehtimalı** — rəqabət şəraiti dəyişməyən sektorun nəzarət
# siyahısına düşmə ehtimalı — hər sıra üçün sektorun faktiki sıra uzunluqları ilə **hər iki** sıfır prosesi altında (i.i.d.
# küy və davamlı sıraları təqlid edən dreyfsiz təsadüfi gəzişmə) ən çoxu 10% olsun; simulyasiya ilə hesablanır (hər sektor
# və sıfır prosesi üçün 20 000 təkrarlama).

# %%
_r = [(l, n) for _, l, n in sheet_rows(DDIR / 'entrepreneurship' / '005en.xls') if l]
SOE = {}
for g in GRP:
    i = next(k for k, (l, n) in enumerate(_r) if re.search(GROUPS[g][1] if g != 'TRA' else 'transportation', az_lower(l)) and len(n) >= 8)
    j = next(k for k in range(i + 1, len(_r)) if 'state owned' in az_lower(_r[k][0]) and 'non-state' not in az_lower(_r[k][0]))
    SOE[g] = {2023: _r[j][1][0] / _r[i][1][0] * 100, 2024: _r[j][1][4] / _r[i][1][4] * 100}
SOE = pd.DataFrame(SOE).T
W = {'F_conc': .25, 'F_entry': .25, 'F_exit': .15, 'F_mob': .10, 'F_margin_entry': .25}
def zchange(s, recent=3):
    s = pd.Series(s).dropna().sort_index()
    if len(s) < 4: return np.nan
    sd = s.diff().std()
    return float((s.iloc[-recent:].mean() - s.iloc[:-recent].mean()) / sd) if sd > 0 else np.nan
SER = {}
for g in GRP:
    e = PA[PA.unit == g].set_index('year'); ex = e.exit.copy(); ex.loc[2022] = np.nan
    SER[g] = dict(conc=((100 - SME.loc[g].sme_output_share), 3, +1), entry=(e.lnB, 3, -1), exit=(ex, 2, +1),
                  mob=((INSTAB.loc[2010:], 3, -1) if g == 'IND' else (pd.Series(dtype=float), 3, -1)),
                  margin=(PCM_G.PCM.xs(g, level=0).loc[2010:], 3, +1))
def flags_from_z(z, zs):
    f = {}
    for k, nm in [('conc', 'F_conc'), ('entry', 'F_entry'), ('exit', 'F_exit'), ('mob', 'F_mob')]:
        f[nm] = 'insufficient data' if not np.isfinite(z[k]) else bool(SER_DIR[k] * z[k] > zs)
    f['F_margin_entry'] = 'insufficient data' if not (np.isfinite(z['margin']) and np.isfinite(z['entry'])) else bool(z['margin'] > zs and z['entry'] < 0)
    return f
SER_DIR = {'conc': 1, 'entry': -1, 'exit': 1, 'mob': -1}
def listed(f):
    av = {k: v for k, v in f.items() if isinstance(v, bool)}
    sc = sum(W[k] for k, v in av.items() if v) / sum(W[k] for k in av) if av else np.nan
    return sc, int(sum(av.values())), bool(av) and (sc >= 0.30 or sum(av.values()) >= 2)
rng_e = np.random.default_rng(SEED + 16); NSIM = 20000
def false_listing(zs, null='iid'):
    rates = {}
    for g in GRP:
        lens = {k: (int(SER[g][k][0].dropna().size), SER[g][k][1]) for k in SER[g]}
        Z = {}
        for k, (n, rc) in lens.items():
            if n < 4: Z[k] = np.full(NSIM, np.nan); continue
            x = rng_e.standard_normal((NSIM, n)); x = np.cumsum(x, axis=1) if null == 'random walk' else x; sd = np.diff(x, axis=1).std(axis=1, ddof=1)
            Z[k] = (x[:, -rc:].mean(1) - x[:, :-rc].mean(1)) / sd
        av = {k: np.isfinite(Z[k]).all() for k in ['conc', 'entry', 'exit', 'mob']}
        F_ = {f'F_{k}': (SER_DIR[k] * Z[k] > zs) for k in av if av[k]}
        if np.isfinite(Z['margin']).all() and av['entry']: F_['F_margin_entry'] = (Z['margin'] > zs) & (Z['entry'] < 0)
        wsum = sum(W[k] for k in F_); sc = sum(W[k] * v for k, v in F_.items()) / wsum; nf = sum(v.astype(int) for v in F_.values())
        hit = int(((sc >= 0.30) | (nf >= 2)).sum())
        rates[g] = hit / NSIM
    return float(np.mean(list(rates.values()))), rates
FL = {}
for zs in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
    FL[zs] = {nl: false_listing(zs, nl) for nl in ['iid', 'random walk']}
    if max(v[0] for v in FL[zs].values()) <= 0.10: break
Z_STAR = zs
FALSE_LIST = pd.DataFrame([dict(z_threshold=k, null=nl, false_listing_rate=v[0], **{f'rate_{g}': r for g, r in v[1].items()}) for k, d in FL.items() for nl, v in d.items()])
EW = []
for g in GRP:
    z = {k: zchange(SER[g][k][0], SER[g][k][1]) for k in SER[g]}
    f = flags_from_z(z, Z_STAR); sc, nf, ls = listed(f)
    row = dict(group=g, name=GROUPS[g][0], **{f'z_{k}': v for k, v in z.items()}, **f, n_available=sum(isinstance(v, bool) for v in f.values()),
               n_flags=nf, score=sc, watch_list=ls, flags=', '.join(k[2:] for k, v in f.items() if v is True))
    lic = LIC_G[g].loc[2016:LAST_ACT] if g in LIC_G.columns else None
    row['info_licences_z'] = zchange(lic) if lic is not None else np.nan
    row['info_cohort_size_ratio_change_pct'] = ((AGE.loc[(g, 2024)][[2, 3, 4, 5]] / AGE.loc[(g, 2024)][1]).mean() / (AGE.loc[(g, 2023)][[2, 3, 4, 5]] / AGE.loc[(g, 2023)][1]).mean() - 1) * 100 if (g, 2024) in AGE.index else np.nan
    row['info_state_share_of_active_SMEs_2024'] = SOE.loc[g, 2024]
    EW.append(row)
EWS = pd.DataFrame(EW)
EWS.to_csv(OUT / 'FR12_early_warning.csv', index=False); FALSE_LIST.to_csv(OUT / 'FR12_early_warning_false_listing.csv', index=False)
display(FALSE_LIST.round(3).T)
display(EWS[['group', 'name', 'z_conc', 'z_entry', 'z_exit', 'z_margin', 'F_conc', 'F_entry', 'F_exit', 'F_mob', 'F_margin_entry', 'n_flags', 'score', 'watch_list']].round(2))
print(f"z* = {Z_STAR}: simulated false-listing rate {FL[Z_STAR]['iid'][0]:.1%} (i.i.d. null) / {FL[Z_STAR]['random walk'][0]:.1%} (random-walk null); "
      f"at z = 1: {FL[1.0]['iid'][0]:.1%} / {FL[1.0]['random walk'][0]:.1%}; watch list ({int(EWS.watch_list.sum())}): "
      + (', '.join(f"{r['name']} [{r['flags']}]" for _, r in EWS[EWS.watch_list].iterrows()) or 'none'))
