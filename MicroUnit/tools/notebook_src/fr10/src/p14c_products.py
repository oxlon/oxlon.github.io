# %% [markdown]
# ### 14.3 Məhsul ölçüsü
#
# **Sahə daxilində məhsul tərkibi.** Məhsullar toplana bilməyən fiziki vahidlərlə ölçülür, buna görə məhsulun sahədaxili
# payı onun *intensivliyi* kimi ifadə olunur: sahənin real buraxılışının vahidinə düşən həcm (2023–2025 ortası verilir).
# **Məhsul həcmlərinin proqnozları** bu tərkibi saxlayır və **sonuncu faktiki ilə lövbərlənir** (v2.1, layihə qaydası):
# ln həcm_t = ln intensivlik + ln sahənin real buraxılışı_t + a, burada sabit baza düzəliş əmsalı a elə seçilir ki, 2025-ci
# il faktiki həcmi təkrar istehsal etsin — yəni həcm_t = həcm_2025 × real_t / real_2025. İlin bir hissəsini əhatə edən
# (2026) məhsul məlumatları yoxdur, buna görə sönən artım yoxdur. Bu, məhsul modeli deyil, sahə proqnozundan mütənasib,
# aydın işarələnmiş törəmədir.
#
# **İstehsal yerləri üzrə məhsulların bazar payları.** DSK `018_1` (2011–2025) əsas məhsulları şəhər və rayonlar üzrə
# sadalayır. Hər məhsul üçün hər yerin sadalanan ölkə həcmindəki payı və yerlər üzrə Herfindahl indeksi hesablanır — bu,
# məkan konsentrasiyası ölçüsüdür; müəssisə səviyyəsində məhsul payları üçün B qatı lazımdır.

# %%
yc18 = [c for c in PROD.columns if isinstance(c, (int, np.integer))]
pv = PROD.set_index('label')[yc18].astype(float)
PRODF = []
for _, r in PROD.iterrows():
    b, lab = r.branch, r.label
    if not isinstance(b, str) or b not in BCODES: continue
    v = pd.Series({y: float(r[y]) for y in range(LAST_ACT - 2, LAST_ACT + 1)})
    if v.isna().any() or (v <= 0).any(): continue
    inten = float(v.mean() / Q[b].loc[LAST_ACT - 2:LAST_ACT].mean())
    inten_used = float(v[LAST_ACT] / Q[b].loc[LAST_ACT])                  # anchored: reproduces the 2025 actual volume
    row = dict(product=lab, branch=b, branch_name=BNAME[b], intensity_2023_25=inten, volume_2023_25_avg=float(v.mean()),
               volume_2025=float(v[LAST_ACT]), intensity_used=inten_used, addfactor_log=float(np.log(inten_used / inten)))
    for s_ in SCEN:
        for y in FC_YEARS: row[f'{s_}_{y}'] = inten_used * float(SOL[s_]['real'].loc[y, b])
    row['baseline_growth_pa'] = ((row[f'Baseline_{FC_YEARS[-1]}'] / row['volume_2025']) ** (1 / (FC_YEARS[-1] - LAST_ACT)) - 1) * 100
    row['jump_2026_pct'] = (row[f'Baseline_{FC_YEARS[0]}'] / row['volume_2025'] - 1) * 100
    PRODF.append(row)
PRODF = pd.DataFrame(PRODF)
print(f'[derived, anchored on {LAST_ACT}] volume forecasts for {len(PRODF)} products in {PRODF.branch.nunique()} branches')
assert np.allclose(PRODF.intensity_used * [float(SOL['Baseline']['real'].loc[LAST_ACT, b_]) for b_ in PRODF.branch], PRODF.volume_2025, rtol=1e-12)
_jmp = PRODF[PRODF.jump_2026_pct.abs() > 25]
print(f'{FC_YEARS[0]} vs {LAST_ACT} actual (Baseline): |change| > 25% for {len(_jmp)} products'
      + (': ' + '; '.join(f'{r.branch} {r.product[:40]} {r.jump_2026_pct:+.1f}%' for r in _jmp.itertuples()) if len(_jmp) else ''))
display(PRODF[['product', 'branch_name', 'volume_2025', f'Baseline_{FC_YEARS[0]}', f'Baseline_{FC_YEARS[-1]}', 'baseline_growth_pa', 'jump_2026_pct']].head(12).round(2))

sh181 = xlrd.open_workbook(P_('industry', '018_1en.xls')).sheet_by_index(0)
hr1 = max(range(8), key=lambda r: sum(1 for c in range(sh181.ncols) if _yr(sh181.cell_value(r, c))))
yc1 = {c: _yr(sh181.cell_value(hr1, c)) for c in range(sh181.ncols)}; yc1 = {c: y for c, y in yc1.items() if y}
cur, rows = None, []
for r in range(hr1 + 1, sh181.nrows):
    lab = str(sh181.cell_value(r, 0)).strip() or str(sh181.cell_value(r, 1)).strip()
    vals = {y: to_num(sh181.cell_value(r, c)) for c, y in yc1.items()}
    if not lab: continue
    if not np.isfinite(list(vals.values())).any(): cur = lab; continue
    if cur: rows.append(dict(product=cur, place=lab, **{str(y): v for y, v in vals.items()}))
PLACE = pd.DataFrame(rows)
yl = str(LAST_ACT)
g = PLACE[PLACE[yl] > 0].groupby('product')
PMS = pd.DataFrame({'places': g.size(), 'listed_volume': g[yl].sum(),
                    'top_place': g.apply(lambda d: d.loc[d[yl].idxmax(), 'place']),
                    'top_place_share_pct': g.apply(lambda d: d[yl].max() / d[yl].sum() * 100),
                    'HHI_places': g.apply(lambda d: ((d[yl] / d[yl].sum()) ** 2).sum() * 1e4)})
key = lambda s: re.sub(r'[^a-z]', '', az_lower(s))
nat = {key(l): float(v_) for l, v_ in zip(PROD.label, PROD[LAST_ACT])}
PMS['national_volume_018'] = [nat.get(key(p_), np.nan) for p_ in PMS.index]
PMS['coverage_of_national_pct'] = PMS.listed_volume / PMS.national_volume_018 * 100
print(f'018_1 ({min(yc1.values())}-{max(yc1.values())}): {len(PMS)} products with producing places in {LAST_ACT}; median places '
      f'{PMS.places.median():.0f}; median top-place share {PMS.top_place_share_pct.median():.0f}%')
display(PMS.sort_values('HHI_places', ascending=False).head(10).round(1))
