# %% [markdown]
# ## Hissə 8 — Ölçü qrupları üzrə məlumatlardan konsentrasiya hədləri
#
# Müəssisə məlumatları olmadan HHI və CR4 müşahidə olunmur, lakin ölçü qrupları üzrə saylar $n_c$ (qruplar və fəaliyyət
# növləri üzrə fəal KOB-lar, sahibkarlıq `005` — buraxılış payları ilə eyni məcmu; iri vahidlər `1_3` reyestrindən, 1 iyul
# 2026) və buraxılış payları $S_c$ (`012`-dən qruplar üzrə KOB-lar; iri = 100 − KOB payı) onları **məhdudlaşdırır**. Hər KOB
# qrupu üçün bir müəssisəyə düşən pay həddi $u_c$ = qanunvericilikdə müəyyən edilmiş gəlir həddi / bazar buraxılışı (mikro
# 0,2, kiçik 3, orta 30 mln manat).
#
# - **Aşağı hədd**: hər qrup daxilində bərabər paylar, $HHI_{low}=\sum_c S_c^2/n_c$; $CR4_{low}$ = həmin bölgüdə dörd ən böyük
#   müəssisə.
# - **Yuxarı hədd (əsas göstərici)**: $\sum s_i^2$ qabarıqdır, buna görə onun qutu-simpleks üzərində maksimumu təpə
#   nöqtəsindədir: hər həddi olan qrupda $\lfloor S_c/u_c\rfloor$ müəssisə həddə, biri isə qalıqla; iri qrup (hədd yoxdur)
#   ən çoxu $S_L^2$ — bir iri müəssisə bütün qrupu tutur, digərləri isə cüzi gəlirlə **məşğulluğa görə** (> 250) iridir.
#   $CR4_{up}$ uyğun təpə nöqtəsidir: $S_L$ üstəgəl həddi olan üç ən böyük müəssisə.
# - **Fərziyyəyə əsaslanan variant**: hər iri müəssisə **gəlirə görə** iridirsə (gəlir ≥ *f* həddi), yuxarı hədlər
#   $(S_L-(n_L-1)f)^2+(n_L-1)f^2$ və $CR4 \le S_L-(n_L-4)f$ olur. Bu, **fərziyyədir** (qanunvericilikdəki qrup "işçilər
#   > 250 **və ya** gəlir > 30 mln manat"-dır), əsas göstərici kimi deyil, *f* = 30 və 15 mln manat ilə həssaslıq variantı
#   kimi göstərilir.
#
# KOB-ların nəzərdə tutulan orta gəliri öz qrupunun həddini aşdıqda (F15) həmin qrup üçün hədlər **bütün illərdə** atılır
# (hər qrup üçün bir rejim, belə ki, proqnozlaşdırılan hədlər fasiləsiz dəyişir). Gəlir həddi variantları bu qruplar üçün də
# hesablanır (v2): bu halda supremumun KOB hissəsi $\sum_c S_c^2$-dir və hədd yalnız iri qrupu məhdudlaşdırır; variant yalnız
# **mümkün olmadıqda** boş saxlanılır ($n_L f$ iri qrupun buraxılışından böyükdür — məsələn, 56 iri səhiyyə vahidinin hamısı
# 30 mln manat qazana bilməz) və bu, `FR12_not_forecast.csv` faylında qeydə alınır. "Bazar" fəaliyyət qrupudur — antiinhisar
# bazarından xeyli genişdir — buna görə hədlər dar məhsul bazarlarında konsentrasiyanı azaldılmış göstərir.

# %%
CAP = {'micro': 0.2, 'small': 3.0, 'medium': 30.0}            # mn AZN, statutory revenue ceilings
SIZE_G = SIZE.assign(group=[SECT[s][3] for s in SIZE.index]).loc[MKT].groupby('group').sum()
GO_G = PCM_G.GO.unstack(0)
E005 = ent_series('005', 4, ['sme', 'micro', 'small', 'medium']).astype({'sme': float, 'micro': float, 'small': float, 'medium': float})

def hhi_bounds(n, S, nL, SL, mkt, capped=True):
    '''n, S: dicts by SME class (shares 0-1); nL, SL: large class; mkt: market output, mn AZN. Shares 0-1 returned.'''
    u = {c: (CAP[c] / mkt if capped else max(S[c], 1e-12)) for c in CAP}
    low = sum(S[c] ** 2 / n[c] for c in n if n[c] > 0) + (SL ** 2 / nL if nL > 0 else 0)
    vert, up_caps = [], 0.0
    for c in CAP:
        if n[c] <= 0 or S[c] <= 0: continue
        q = min(int(np.floor(S[c] / u[c] + 1e-12)), int(n[c])); r = max(S[c] - q * u[c], 0.0)
        up_caps += q * u[c] ** 2 + (r ** 2 if q < n[c] else 0.0); vert += [u[c]] * min(q, 4) + ([r] if q < n[c] else [])
    vert = sorted(vert, reverse=True)
    eq = sorted([(SL / nL, nL)] + [(S[c] / n[c], n[c]) for c in CAP if n[c] > 0], reverse=True); c4l, k = 0.0, 4.0
    for sh, cnt in eq:
        t = min(k, cnt); c4l += t * sh; k -= t
        if k <= 0: break
    out = dict(hhi_lower=low, hhi_upper=up_caps + SL ** 2, cr4_lower=c4l, cr4_upper=min(1.0, SL + sum(vert[:3])) if nL >= 1 else sum(vert[:4]))
    for fl in (30.0, 15.0):
        f = fl / mkt
        if capped and nL >= 1 and SL >= nL * f:
            out[f'hhi_upper_floor{int(fl)}'] = up_caps + (SL - (nL - 1) * f) ** 2 + (nL - 1) * f ** 2
            out[f'cr4_upper_floor{int(fl)}'] = (SL - (nL - 4) * f) if nL >= 4 else min(1.0, SL + sum(vert[:int(4 - nL)]))
        elif not capped and nL >= 1 and SL >= nL * f:
            # SME caps dropped (F15): the SME part of the supremum is sum S_c^2 (each class in one firm); the floor binds the large class only
            out[f'hhi_upper_floor{int(fl)}'] = up_caps + (SL - (nL - 1) * f) ** 2 + (nL - 1) * f ** 2
            top = sorted([SL - (nL - 1) * f] + [f] * int(min(nL - 1, 3)) + [S[c] for c in CAP if n[c] > 0 and S[c] > 0], reverse=True)
            out[f'cr4_upper_floor{int(fl)}'] = min(1.0, sum(top[:4]))
        else:          # infeasible: nL firms with revenue >= f would exceed the large class's output
            out[f'hhi_upper_floor{int(fl)}'] = np.nan; out[f'cr4_upper_floor{int(fl)}'] = np.nan
    return out

def caps_ok(g, y, sh, mkt):
    return all((sh[c] / 100) / float(E005.loc[(g, y), c]) <= CAP[c] / mkt * (1 + 1e-9) for c in CAP if E005.loc[(g, y), c] > 0)
CAPPED = {g: all(caps_ok(g, y, E012.loc[(g, y)], GO_G.loc[y, g]) for y in [2023, 2024]) for g in GRP}
BND = []
for g in GRP:
    for y in [2023, 2024]:
        sh = E012.loc[(g, y)]; mkt = float(GO_G.loc[y, g])
        n = {c: float(E005.loc[(g, y), c]) for c in CAP}; nL = float(SIZE_G.loc[g, 'large'])
        S = {c: sh[c] / 100 for c in CAP}; SL = max(1 - sh['sme'] / 100, 0.0)
        b = hhi_bounds(n, S, nL, SL, mkt, CAPPED[g])
        BND.append(dict(group=g, year=y, market_output_mn=mkt, n_large=nL, large_share=SL * 100, caps_used=CAPPED[g],
                        **{k: v * (1e4 if k.startswith('hhi') else 100) for k, v in b.items()}))
BND = pd.DataFrame(BND); BND['number_equivalent_max'] = 1e4 / BND.hhi_lower
display(BND[BND.year == 2024].set_index('group').round(1))
chk('HHI lower <= floor variants <= headline upper; CR4 lower <= CR4 upper (all groups, years)', 0.0,
    bool(((BND.hhi_lower <= BND.hhi_upper + 1e-6) & (BND.cr4_lower <= BND.cr4_upper + 1e-6)
          & (BND.hhi_upper_floor30.isna() | ((BND.hhi_lower <= BND.hhi_upper_floor30 + 1e-6) & (BND.hhi_upper_floor30 <= BND.hhi_upper + 1e-6)))).all()))
chk('CR4 bounds consistent with HHI bounds: CR4^2/4 <= HHI_upper (all groups, years)', 0.0, bool(((BND.cr4_lower / 100) ** 2 / 4 * 1e4 <= BND.hhi_upper + 1e-6).all()))

# taxpayer size classes (DVX): economy-wide lower bound on the concentration of declared turnover (micro excluded, F8)
_d = DVXC.loc[DVXC[('large', 'turnover')].notna()]
TAXB = []
for y, r in _d.iterrows():
    T = sum(r[(c, 'turnover')] for c in ['large', 'medium', 'small'])
    S = {c: r[(c, 'turnover')] / T for c in ['large', 'medium', 'small']}; n = {c: r[(c, 'count')] for c in S}
    TAXB.append(dict(year=y, large_count=n['large'], large_turnover_share=S['large'] * 100, hhi_lower=sum(S[c] ** 2 / n[c] for c in S) * 1e4,
                     turnover_per_large_mn=r[('large', 'turnover')] / n['large'], receipts_share_large=r[('large', 'receipts')] /
                     sum(r[(c, 'receipts')] for c in ['large', 'medium', 'small']) * 100))
TAXB = pd.DataFrame(TAXB).set_index('year')
display(TAXB.round(2))
_b = BND[BND.year == 2024].set_index('group')
print(f"2024: HHI lower bound {_b.hhi_lower.min():.0f}-{_b.hhi_lower.max():.0f}; headline upper bound up to {_b.hhi_upper.max():.0f} ({_b.hhi_upper.idxmax()}); "
      f"trade CR4 {_b.loc['TRD', 'cr4_lower']:.1f}-{_b.loc['TRD', 'cr4_upper']:.1f}% (30 mn revenue floor: {_b.loc['TRD', 'cr4_upper_floor30']:.1f}%); "
      f"caps used for {sum(CAPPED.values())} of {len(CAPPED)} groups")
