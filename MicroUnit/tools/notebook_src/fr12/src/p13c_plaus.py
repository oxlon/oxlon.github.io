# %% [markdown]
# Hər vahidin 2026–2030 üzrə proqnoz ortasının giriş əmsalı, **doğumlar (axın)**, çıxış əmsalı və **ehtiyatın artımı** üzrə
# öz tarixi ilə (diapazon və son iki müşahidə) müqayisədə **inandırıcılığı**; habelə sonuncu faktiki giriş əmsalının 2026-cı
# ilin 5–95% zolağının daxilində olub-olmadığı, olmadıqda isə səbəbi. Tarixi məlumatlar yalnız burada istifadə olunur.

# %%
PL, LASTB = [], []
for pn, df in PANELS.items():
    h = df.sort_values(['unit', 'year']).copy()
    h['growth'] = h.groupby('unit').N.transform(lambda s: s.pct_change()) * 100 / h.groupby('unit').year.diff()
    f = FC[(FC.scenario == 'Baseline') & (FC.panel == pn)].sort_values(['unit', 'year']).copy()
    f['growth'] = f.groupby('unit').N.pct_change() * 100
    for u, g in h.groupby('unit'):
        fu = f[(f.unit == u) & f.year.isin(FC_YEARS)]
        for var, hv, fv in [('entry rate, %', 'entry', 'entry'), ('births', 'B', 'new'), ('exit rate, %', 'exit', 'exit'), ('stock growth, % a year', 'growth', 'growth')]:
            s = g[hv].dropna()
            if s.empty: continue
            fm = float(fu[fv].mean()); lo, hi, rec = s.min(), s.max(), s.tail(2).mean()
            flag = 'outside historical range' if (fm < lo - 1e-9 or fm > hi + 1e-9) else ('differs from recent mean by >25%' if abs(fm - rec) > 0.25 * abs(rec) else '')
            PL.append(dict(panel=pn, unit=u, variable=var, forecast_mean_2026_30=fm, hist_min=lo, hist_max=hi, recent_2obs_mean=rec, flag=flag))
    last = ORIG[pn]
    for u in list(df.unit.unique()) + ['ALL']:
        if u == 'ALL':
            a = df[df.year == last]; act = a.B.sum() / a.N.sum() * 100; bl = a.B.sum(); nl = a.N.sum()
        else:
            a = df[(df.year == last) & (df.unit == u)].iloc[0]; act, bl, nl = a.entry, a.B, a.N
        b = FAN[(FAN.panel == pn) & (FAN.unit == u) & (FAN.year == 2026)].iloc[0]
        inside = b.entry_p5 <= act <= b.entry_p95
        why = '' if inside else (f"births 2026 {b.new_baseline / bl - 1:+.1%} vs {last} and stock {b.N_baseline / nl - 1:+.1%}: "
                                 + ('the stock grows faster than births, so the rate falls' if b.new_baseline / bl < b.N_baseline / nl else 'births grow faster than the stock'))
        if not inside and np.isfinite(act) and u != 'ALL' and pn == 'activity' and act > b.entry_p95:
            why += f'; {last} births were {bl / df[(df.unit == u) & (df.year < last)].B.tail(2).mean() - 1:+.0%} vs the two earlier observations'
        LASTB.append(dict(panel=pn, unit=u, last_year=last, last_actual_entry=act, band2026_p5=b.entry_p5, band2026_p95=b.entry_p95, inside=bool(inside), explanation=why))
PLAUS = pd.DataFrame(PL); LASTB = pd.DataFrame(LASTB)
PLAUS.to_csv(OUT / 'FR12_plausibility.csv', index=False); LASTB.to_csv(OUT / 'FR12_last_actual_vs_2026_band.csv', index=False)
_b = FAN[FAN.unit == 'ALL']
display(_b[_b.year.isin([2025, 2026, 2028, 2030])][['panel', 'year', 'new_baseline', 'new_p5', 'new_p95', 'entry_baseline', 'entry_p5', 'entry_p95',
                                                    'exit_baseline', 'exit_p5', 'exit_p95', 'N_baseline', 'N_p5', 'N_p95']].round(2))
print(f"plausibility: {int((PLAUS.flag != '').sum())} of {len(PLAUS)} unit-variable forecasts flagged; last actual entry rate outside the 2026 band: "
      f"{int((~LASTB.inside).sum())} of {len(LASTB)}")
display(PLAUS[PLAUS.flag != ''].round(2)); display(LASTB[~LASTB.inside].round(2))
fig, ax = plt.subplots(1, 3, figsize=(15, 4))
for i, (pn, var, ttl) in enumerate([('activity', 'new', 'New registrations, all groups (006)'), ('activity', 'entry', 'Entry rate, all groups, %'), ('region', 'N', 'Statistical units, 14 regions')]):
    f = _b[_b.panel == pn].sort_values('year')
    ax[i].fill_between(f.year, f[f'{var}_p5'], f[f'{var}_p95'], alpha=0.2, color=PAL[0], label='5-95%')
    ax[i].fill_between(f.year, f[f'{var}_p25'], f[f'{var}_p75'], alpha=0.35, color=PAL[0], label='25-75%')
    for j, sc in enumerate(SCEN):
        a = AGG[(AGG.panel == pn) & (AGG.scenario == sc)].sort_values('year'); ax[i].plot(a.year, a[var], color=PAL[j + 1], label=sc)
    hh = PANELS[pn].groupby('year')[['B', 'N']].sum(); hv = {'new': hh.B, 'entry': hh.B / hh.N * 100, 'N': hh.N}[var]
    sf = SERIES_FILLED[(SERIES_FILLED.id == f"fr12:{'act' if pn == 'activity' else 'reg'}:{var}:ALL") & SERIES_FILLED.value.notna()]
    if len(sf): plot_filled(ax[i], sf.year, sf.value, sf.imputed, 'k', 'actual')        # 2021 filled: hollow marker, dashed
    else: plot_filled(ax[i], hv.index, hv.values, np.zeros(len(hv), bool), 'k', 'actual')
    ax[i].set_title(ttl); imp_legend(ax[i], fontsize=7)
plt.tight_layout(); plt.show()
