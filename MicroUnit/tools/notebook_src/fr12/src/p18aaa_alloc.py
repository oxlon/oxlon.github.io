# %% [markdown]
# **NACE bölmələri üzrə reyestr axınları** (statistik vahidlər, DSK 2_1) öz modeli ilə deyil, **bölüşdürmə** yolu ilə
# proqnozlaşdırılır. Bölmə axınları region paneli ilə eyni məcmudur (statistik vahidlər: hər tam ildə 2_1 bölmə yekunları
# 2_3 region yekunlarına bərabərdir), buna görə region panelinin doğumlar, ölümlər və ehtiyat proqnozu (Hissə 13) yekundur;
# o, əvvəlcə DSK-nın 11 fəaliyyət qrupu arasında, sonra isə hər qrupun bölmələri arasında bölünür. 006 fəaliyyət proqnozları
# istifadə olunmur: onlar başqa məcmunu — qeydiyyatdan keçmiş sahibkarlıq subyektlərini sayır (F6).
#
# - **Sonuncu faktiki ilə (2025) lövbərlənmiş paylar** — hər modulun qaydası (səviyyəni sonuncu müşahidə daşıyır).
#   2024 → 2025 nümunədən kənar yoxlaması (faktiki 2025 yekunu verildikdə) lövbərlənmiş qaydanı (keçən ilin payları) əvvəlki
#   müşahidə olunan illərin ortasında saxlanılan paylarla müqayisə edir; hər ikisi verilir, Əsas ssenari lövbərlənmiş 2025
#   paylarından istifadə edir. Bölməyə xas sürücü qaydasını kəsimdən əvvəlki sxem üzrə yoxlamaq mümkün deyil (2022-yədək və
#   ya 2022-də yalnız bir müşahidə olunan tam il var, 2021).
# - **Müşahidə olunan 2026-cı il yanvar–iyun məlumatlarından 2026 üçün cari qiymətləndirmə (nowcast)** (FR1-in ilin
#   əvvəlindən bəri məlumatlardan istifadə etdiyi kimi): 2026 tam il = 2026 I yarımil ÷ bölmənin müşahidə olunan I yarımil /
#   tam il nisbəti (2024–2025 ortası). Bölüşdürmənin 2026 dəyərinə nisbətən artım 2026-da tam daxil olur və bir illik
#   yarımparçalanma dövrü ilə sönür (çəki 0.5^(t−2026)); hər il daxilində düzəldilmiş bölmələr region panelinin yekununa
#   yenidən miqyaslanır, belə ki, bölmələr dəqiq öz qruplarına, qruplar isə yekuna toplanır. Bazar xarakterli olmayan O və
#   U bölmələri artım almır: 2026-cı ilin yanvar–iyun dövründə dövlət idarəetməsində 228 inzibati ləğvetmə var (F10) və bu,
#   tam il üzrə bazar əmsalı kimi oxuna bilməz; onlar lövbərlənmiş paylarını saxlayır.
# - Giriş və çıxış əmsalları doğumlar / ehtiyat və ölümlər / ehtiyat kimi alınır; zolaqlar yekunun zolağının bölmənin
#   (düzəldilmiş) payına hasilidir; 2027–2030 yanvar–iyun axınları bölmənin tam il dəyərinin müşahidə olunan I yarımil
#   nisbətinə hasilidir.

# %%
_fy = FLOWS[(FLOWS.kind == 'section') & (FLOWS.period == 'FY')]; _h1 = FLOWS[(FLOWS.kind == 'section') & (FLOWS.period == 'H1')]
_grp = {s: SECT[s][3] for s in SECS}
def alloc_shares(years, var):
    """group-of-total share x within-group share, each averaged over `years` (observed full years only)"""
    P = _fy[_fy.year.isin(years)].pivot_table(index='year', columns='unit', values=var).reindex(columns=SECS).fillna(0.0)
    Gt = P.T.groupby(_grp).sum().T; gsh = Gt.div(P.sum(axis=1), axis=0).mean()
    W = P.div(Gt[[_grp[s] for s in SECS]].set_axis(SECS, axis=1)).replace([np.inf, -np.inf], np.nan).mean()
    W = W.fillna(0.0) / W.fillna(0.0).groupby(_grp).transform('sum').replace(0, np.nan)
    return (W.fillna(0.0) * pd.Series({s: gsh[_grp[s]] for s in SECS})).rename(var)
AVAR = {'new': 'new', 'liq': 'exits', 'stock': 'N'}
ALLOC = pd.DataFrame({v: alloc_shares([2025], v) for v in AVAR})                    # baseline: anchored on the last actual year
ALLOC_AVG = pd.DataFrame({v: alloc_shares([2021, 2024, 2025], v) for v in AVAR})   # alternative (reported only)
assert np.allclose(ALLOC.sum(), 1.0, atol=1e-12) and np.allclose(ALLOC_AVG.sum(), 1.0, atol=1e-12), 'allocation shares must add to 1'
_ho = []
for v in AVAR:
    act = _fy[_fy.year == 2025].set_index('unit')[v].reindex(SECS).fillna(0.0); tot = act.sum()
    anc = alloc_shares([2024], v) * tot; avg = alloc_shares([2021, 2024], v) * tot
    ea, eb = ((anc - act) ** 2).values, ((avg - act) ** 2).values; _, dmp = dm_hln(ea, eb)
    for nm, e_, o_, base in [('anchored: last observed year (2024 at the origin; 2025 in the forecast)', ea, eb, True), ('average of observed years (2021, 2024 at the origin)', eb, ea, False)]:
        _ho.append(dict(variable=v, variant=nm, used_in_baseline=base, origin=2024, target=2025, rmse=float(np.sqrt(e_.mean())), theil_vs_other_variant=float(np.sqrt(e_.mean() / o_.mean())),
                        dm_p_anchored_vs_average=dmp, driver_rule='not identified pre-cut: one observed full year (2021) at or before 2022'))
ALLOC_HOLD = pd.DataFrame(_ho)
_r = {}
for v in AVAR:
    f_ = _fy[_fy.year.isin([2024, 2025])].pivot_table(index='unit', columns='year', values=v); h_ = _h1[_h1.year.isin([2024, 2025])].pivot_table(index='unit', columns='year', values=v)
    _r[v] = (h_ / f_.where(f_ > 0)).reindex(SECS).mean(axis=1).fillna(float(h_.sum().sum() / f_.sum().sum()))
H1RATIO = pd.DataFrame(_r)
H1OBS26 = _h1[_h1.year == 2026].pivot_table(index='unit', values=list(AVAR)).reindex(SECS).fillna(0.0)
NOWC26 = H1OBS26[list(AVAR)] / H1RATIO[list(AVAR)]                                   # full-year 2026 nowcast by section
NOW_Y, HALF_LIFE = 2026, 1.0
NOW_EXEMPT = ['O', 'U']      # non-market sections: H1 2026 carries 228 administrative liquidations in O (F10) — no increment, shares only
def section_paths(tot):
    """tot: {(y, v): total}; anchored shares x total + decaying 2026 nowcast increment, rescaled to the total."""
    out = {}
    for v in AVAR:
        d26 = (NOWC26[v] - ALLOC[v] * tot[(NOW_Y, v)]).where(~pd.Index(SECS).isin(NOW_EXEMPT), 0.0)
        for y in FC_YEARS:
            raw = (ALLOC[v] * tot[(y, v)] + 0.5 ** ((y - NOW_Y) / HALF_LIFE) * d26).clip(lower=0.0)
            out[(y, v)] = raw * tot[(y, v)] / raw.sum()
    return out
_agg = AGG[AGG.panel == 'region'].set_index(['scenario', 'year']); _fb = FAN[(FAN.panel == 'region') & (FAN.unit == 'ALL')].set_index('year')
SECFC, NOWTAB = [], []
for sc in SCEN:
    tot = {(y, v): float(_agg.loc[(sc, y), AVAR[v]]) for y in FC_YEARS for v in AVAR}; SP_ = section_paths(tot)
    for y in FC_YEARS:
        b = _fb.loc[y] if sc == 'Baseline' else None
        for s in SECS:
            new, liq, st = SP_[(y, 'new')][s], SP_[(y, 'liq')][s], SP_[(y, 'stock')][s]
            kn, kl, ks = new / tot[(y, 'new')], liq / tot[(y, 'liq')], st / tot[(y, 'stock')]
            band = lambda col, k: (k * b[f'{col}_p5'], k * b[f'{col}_p95']) if b is not None else (np.nan, np.nan)  # noqa: E731
            vals = dict(new=(new,) + band('new', kn), liq=(liq, np.nan, np.nan), stock=(st,) + band('N', ks),
                        entry=(new / st * 100,) + band('entry', kn / ks), exit=(liq / st * 100,) + band('exit', kl / ks))
            for m, (v_, lo_, hi_) in vals.items(): SECFC.append(dict(scenario=sc, fam='sec', sec=s, metric=m, year=y, value=v_, lower_5=lo_, upper_95=hi_))
            if y > 2026:                                                 # H1 2026 is observed (st_units, 1 July 2026)
                for m in ['stock', 'new', 'liq']:
                    v_, lo_, hi_ = vals[m]; k = H1RATIO.loc[s, m]
                    SECFC.append(dict(scenario=sc, fam='sec_h1', sec=s, metric=m, year=y, value=k * v_, lower_5=k * lo_, upper_95=k * hi_))
    if sc == 'Baseline':
        for s in SECS:
            for v in AVAR:
                m26 = ALLOC.loc[s, v] * tot[(2026, v)]
                NOWTAB.append(dict(section=s, variable=v, h1_2026_observed=H1OBS26.loc[s, v], h1_fy_ratio=H1RATIO.loc[s, v], nowcast_fy_2026=NOWC26.loc[s, v],
                                   allocation_2026_before=m26, adjusted_2026=SP_[(2026, v)][s], change_2026_pct=(SP_[(2026, v)][s] / m26 - 1) * 100 if m26 else np.nan,
                                   h1_2027_implied_before=H1RATIO.loc[s, v] * ALLOC.loc[s, v] * tot[(2027, v)], h1_2027_implied=H1RATIO.loc[s, v] * SP_[(2027, v)][s],
                                   h1_2027_implied_v1_average_shares=H1RATIO.loc[s, v] * ALLOC_AVG.loc[s, v] * tot[(2027, v)]))
SECFC = pd.DataFrame(SECFC); NOWTAB = pd.DataFrame(NOWTAB)
_chk = SECFC[SECFC.fam == 'sec'].pivot_table(index=['scenario', 'year'], columns='metric', values='value', aggfunc='sum')
_tot = _agg[['new', 'exits', 'N']].rename(columns={'exits': 'liq', 'N': 'stock'}).loc[_chk.index]
_gap = float((_chk[['new', 'liq', 'stock']] - _tot).abs().max().max())
assert _gap < 1e-6, f'sections do not add to the region-panel total ({_gap})'
ALLOC.add_prefix('share_').assign(group=[_grp[s] for s in SECS], **{f'share_avg_{v}': ALLOC_AVG[v] for v in AVAR}, **{f'h1_ratio_{v}': H1RATIO[v] for v in AVAR},
                                  **{f'nowcast_fy2026_{v}': NOWC26[v] for v in AVAR}).reset_index(names='section').to_csv(OUT / 'FR12_section_allocation.csv', index=False)
ALLOC_HOLD.to_csv(OUT / 'FR12_section_allocation_holdout.csv', index=False); NOWTAB.to_csv(OUT / 'FR12_section_nowcast_2026.csv', index=False)
display(ALLOC_HOLD[['variable', 'variant', 'rmse', 'theil_vs_other_variant', 'dm_p_anchored_vs_average']].round(3))
display(NOWTAB[(NOWTAB.variable == 'new') & NOWTAB.section.isin(MKT)].sort_values('allocation_2026_before', ascending=False).head(6).round(1))
print(f"section allocation: anchored 2025 shares + 2026 nowcast from H1 2026 (half-life {HALF_LIFE:g} year); sections add to groups and to the region-panel total (max gap {_gap:.1e})")
