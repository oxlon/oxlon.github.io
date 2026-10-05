# %% [markdown]
# ### 15.1 Ssenarilər: fəaliyyət qrupları üzrə kalibrləmələr və əsas bazarlar, diapazonlar kimi verilir
#
# Hər ssenari **bütün konsentrasiya diapazonu** üzrə — HHI aşağı həddən yuxarı həddədək (fəaliyyət qrupları üçün Hissə 8;
# əsas bazarlar üçün açıq göstərilmiş ictimai struktur), loqarifmik şəbəkədə beş nöqtə — × tələbin elastikliyi
# {0.5, 1, 1.5, 2} × davranış {Kurno θ = 1, θ = 0.5} aparılır. Heç bir "mərkəzi" dəyər ayrılmır; ε = 1, θ = 1 üçün uc
# nöqtələr göstərilir. **Əsas bazarlar təxmini ictimai struktur əsasında illüstrativ kalibrləmələrdir, fərziyyə kimi
# göstərilir və tənzimləyicinin məlumatları ilə əvəz edilməlidir** (mobil rabitə üçün Rəqəmsal İnkişaf və Nəqliyyat
# Nazirliyi / İKTA, bank sektoru üçün AMB, sement üçün istehsalçıların hesabatları); onların gəliri FR12-nin
# məlumatlarında yoxdur, buna görə rifah yalnız bazar gəlirinin %-i ilə verilir. Qarışıq oliqopoliya ssenarisi üçün dövlət
# payı: sənaye buraxılışının 21,9%-i (2025; DSK sənaye `010_2`, `FR10_ownership.csv` vasitəsilə), həssaslıq variantı kimi
# emal sənayesi üzrə 35,1%; bütün dövlət sənaye istehsalçıları bir dövlət müəssisəsi kimi nəzərdən keçirilir (fərziyyə).

# %%
_own = pd.read_csv(OUT / 'FR10_ownership.csv', index_col=0)
SIG = {'industry': 1 - float(_own.loc[LAST_ACT, 'published non-state share, %']) / 100,
       'manufacturing': 1 - float(_own.loc[LAST_ACT, 'non-state share of manufacturing, %']) / 100}
_b24 = BND[BND.year == 2024].set_index('group')
MK = {g: dict(name=f'{g} ({GROUPS[g][0]})', lo=_b24.loc[g, 'hhi_lower'] / 1e4, up=_b24.loc[g, 'hhi_upper'] / 1e4, rev=float(GO_G.loc[LAST_ACT, g]),
              source='Layer-A size-class bounds (Part 8), 2024') for g in GRP}
MK['MOB'] = dict(name='Mobile telecommunications (3 operators)', lo=0.33, up=0.40, rev=np.nan,
                 source='ASSUMPTION: 3 operators, subscriber shares ≈ 50-55 / 25-30 / 20% (approximate public reports) -> HHI 3,300-4,000')
MK['BNK'] = dict(name='Banking (assets)', lo=0.08, up=0.13, rev=np.nan,
                 source='ASSUMPTION: ~22 banks, top-5 ≈ 60% of assets (approximate, CBAR annual reports) -> HHI 800-1,300; replace with CBAR concentration data')
MK['CEM'] = dict(name='Cement (domestic producers)', lo=0.35, up=0.55, rev=np.nan,
                 source='ASSUMPTION: 2-3 domestic integrated producers plus imports (approximate) -> domestic HHI 3,500-5,500')
EPS_GRID, THETA_GRID = [0.5, 1.0, 1.5, 2.0], [1.0, 0.5]
SCN = [
 ('S1', 'ICT', 'Entry-barrier reduction / licensing simplification', 'one additional symmetric-equivalent competitor (ΔN = +1)', lambda h, e, t, r: sc_entry(h, e, t, 1.0, r)),
 ('S1', 'MOB', 'Entry of a 4th mobile operator', 'ΔN = +1 symmetric-equivalent competitor', lambda h, e, t, r: sc_entry(h, e, t, 1.0, r)),
 ('S2', 'CON', 'Merger of two firms', 'merging shares 10% and 5%; HHI used >= 0.10² + 0.05²', lambda h, e, t, r: sc_merger(h, e, t, 0.10, 0.05, r)),
 ('S2', 'BNK', 'Merger of two banks', 'merging asset shares 8% and 6%; HHI used >= 0.08² + 0.06²', lambda h, e, t, r: sc_merger(h, e, t, 0.08, 0.06, r)),
 ('S3', 'ACC', 'Cost shock / excise or tax increase', 'per-unit cost +5% of the initial price, all firms', lambda h, e, t, r: sc_cost(h, e, t, 0.05, r)),
 ('S3', 'CEM', 'Energy-cost shock', 'per-unit cost +5% of the initial price, all producers', lambda h, e, t, r: sc_cost(h, e, t, 0.05, r)),
 ('S4', 'IND', 'Import competition (tariff cut)', 'import share 30% -> 40%, import supply elasticity η = 2', lambda h, e, t, r: sc_import(h, e, t, 0.3, 0.4, 2.0, r)),
 ('S4', 'CEM', 'Import competition (tariff cut)', 'import share 20% -> 30%, η = 2', lambda h, e, t, r: sc_import(h, e, t, 0.2, 0.3, 2.0, r))]
for nm_, sg in SIG.items():
    for lam in (0.5, 1.0):
        SCN.append(('S5', 'IND', f'SOE {"partial" if lam < 1 else "full"} privatisation (mixed oligopoly)', f'σ = {sg:.1%} ({nm_}), λ: 0 -> {lam}',
                    (lambda sg_, lm_: (lambda h, e, t, r: mixed_oligopoly(h, sg_, e, t, lm_, r)))(sg, lam)))
SC_ASSUME, SC_RES = [], []
for sid, mk, name, assumption, fn in SCN:
    M_ = MK[mk]; grid = np.exp(np.linspace(np.log(M_['lo']), np.log(M_['up']), 5))
    SC_ASSUME.append(dict(scenario=sid, market=M_['name'], change=name, assumption=assumption, hhi_range=f"{M_['lo']*1e4:,.0f}-{M_['up']*1e4:,.0f}",
                          structure_source=M_['source'], elasticity_range='0.5-2.0 (FR5 services system: 1.0)', conduct='Cournot θ = 1; θ = 0.5',
                          demand='linear', status='illustrative'))
    for h in grid:
        for e in EPS_GRID:
            for th in THETA_GRID:
                SC_RES.append(dict(scenario=sid, market=mk, change=name, assumption=assumption, hhi=h * 1e4, elasticity=e, conduct=th, **fn(h, e, th, M_['rev'])))
SC_ASSUME = pd.DataFrame(SC_ASSUME); SC_RES = pd.DataFrame(SC_RES)
SC_RES['hhi_eff'] = SC_RES.hhi_used.fillna(SC_RES.hhi)          # merger: >= s1² + s2²; mixed oligopoly: within [σ², σ² + (1-σ)²]
_k = ['scenario', 'market', 'change', 'assumption']
_end = SC_RES[(SC_RES.elasticity == 1.0) & (SC_RES.conduct == 1.0)].sort_values('hhi').groupby(_k, sort=False)
SC_SUM = SC_RES.groupby(_k, sort=False).agg(hhi_min=('hhi_eff', 'min'), hhi_max=('hhi_eff', 'max'), d_price_min=('d_price_pct', 'min'), d_price_max=('d_price_pct', 'max'),
                                            d_markup_min=('d_markup_pp', 'min'), d_markup_max=('d_markup_pp', 'max'), d_output_min=('d_output_pct', 'min'),
                                            d_output_max=('d_output_pct', 'max'), d_cs_pct_min=('d_cs_pct_rev', 'min'), d_cs_pct_max=('d_cs_pct_rev', 'max'),
                                            d_cs_mn_min=('d_cs_mn', 'min'), d_cs_mn_max=('d_cs_mn', 'max'))
SC_SUM['d_price_at_lower_bound'] = _end.d_price_pct.first(); SC_SUM['d_price_at_upper_bound'] = _end.d_price_pct.last()
SC_SUM = SC_SUM.reset_index()
SC_ASSUME.to_csv(OUT / 'FR12_scenario_assumptions.csv', index=False); SC_RES.to_csv(OUT / 'FR12_scenario_results.csv', index=False)
SC_SUM.to_csv(OUT / 'FR12_scenario_summary.csv', index=False)
display(SC_ASSUME[['scenario', 'market', 'change', 'hhi_range', 'structure_source']])
display(SC_SUM[['scenario', 'market', 'assumption', 'hhi_min', 'hhi_max', 'd_price_min', 'd_price_max', 'd_price_at_lower_bound', 'd_price_at_upper_bound', 'd_cs_pct_min', 'd_cs_pct_max']].round(2))
_mg = SC_RES[SC_RES.scenario == 'S2'].groupby('market').agg(hhi_post_min=('hhi_post', 'min'), hhi_post_max=('hhi_post', 'max'), d_hhi=('d_hhi', 'first'),
                                                           us=('us_2010_screen', lambda s: ' / '.join(sorted(set(s)))), eu=('eu_screen', lambda s: ' / '.join(sorted(set(s)))),
                                                           fs_mc_cut_min=('fs_required_mc_cut_pct', 'min'), fs_mc_cut_max=('fs_required_mc_cut_pct', 'max'))
MERGER_SCREEN = _mg.reset_index(); display(MERGER_SCREEN.round(1))
chk('scenario welfare: ΔCS has the opposite sign of Δprice in every run', 0.0, bool(((np.sign(SC_RES.d_cs_pct_rev) == -np.sign(SC_RES.d_price_pct)) | (SC_RES.d_price_pct.abs() < 1e-9)).all()))
_s5 = SC_RES[SC_RES.scenario == 'S5']
chk('mixed oligopoly: every calibration reproduces P = 1, Q = 1 and σ', float(_s5.calib_resid.max()), bool(_s5.calib_resid.max() < 1e-6))
