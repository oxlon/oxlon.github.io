# %%
# v2 blocks of the methodology document (section 20), generated from this run's outputs
_sf = rd('series_filled'); _imp = _sf[_sf.imputed]
_fam = {'act': 'fəaliyyət qrupları (006)', 'conc': 'KOS payları (012/013)', 'sec': 'NACE bölmələri, tam il (2_1)', 'sec_h1': 'NACE bölmələri, yanvar–iyun (2_1)', 'reg': 'regionlar', 'info': 'digər'}
_g = _imp.assign(fam=_imp.id.str.split(':').str[1]).groupby('fam').agg(series=('id', 'nunique'), values=('id', 'size'), years=('year', lambda s: ', '.join(map(str, sorted(set(s))))))
_g.index = [_fam.get(i, i) for i in _g.index]
_lead = _sf[_sf.method.str.startswith('not filled')].assign(fam=lambda d: d.id.str.split(':').str[1]).groupby('fam').agg(series=('id', 'nunique'), years=('year', lambda s: f'{min(s)}–{max(s)}'))
_lead.index = [_fam.get(i, i) for i in _lead.index]
G_['v2_gaps'] = (f"Doldurulmuş dəyərlər: {len(_imp)} ({_imp.id.nunique()} sıra). Qiymətləndirmə yalnız müşahidə edilmiş məlumatla aparılır.\n\n"
                 + mdt(_g.reset_index().rename(columns={'index': 'sıra ailəsi', 'series': 'sıra', 'values': 'dəyər', 'years': 'doldurulmuş illər'}))
                 + '\n\nİlkin boşluqlar (doldurulmayıb, ekstrapolyasiya yoxdur):\n\n' + mdt(_lead.reset_index().rename(columns={'index': 'sıra ailəsi', 'series': 'sıra', 'years': 'illər'})))
_gs = rd('gapfill_sensitivity')
_gc = _gs[_gs.kind == 'coefficient'][['item', 'term', 'observed_only', 'with_filled', 'rel_diff_pct']]
_gf = _gs[(_gs.kind == 'forecast_2030') & _gs.item.str.startswith('fr12:act')][['item', 'term', 'observed_only', 'with_filled', 'rel_diff_pct']]
_gsme = _gs[_gs.item.str.contains('sme_output_share', na=False)]
G_['v2_gapsens'] = ('Əmsallar (yalnız müşahidə vs doldurulmuş 2021 daxil):\n\n' + mdt(_gc, fmt={'observed_only': '{:.4f}', 'with_filled': '{:.4f}'})
                    + '\n\n2030 proqnozları (bütün qruplar):\n\n' + mdt(_gf, fmt={'observed_only': '{:,.3f}', 'with_filled': '{:,.3f}'})
                    + f"\n\nKOS-un buraxılış payı 2030: maksimal |dəyişmə| {_gsme['diff'].abs().max():.2f} faiz bəndi.")
_nf = rd('not_forecast')
G_['v2_notforecast'] = (f"`FR12_not_forecast.csv`: {len(_nf)} id. " + '; '.join(f"{k}: {v}" for k, v in _nf.id.str.split(':').str[1].value_counts().items())
                        + '.\n\n' + mdt(_nf[_nf.id.str.contains('floor30')][['id', 'reason_az']]))
_ah = rd('section_allocation_holdout'); _sm = rd('sme_employment_model'); _smr = _sm[_sm.table == 'rule'].iloc[0]
_cat2 = rd('indicator_catalog')
G_['v2_alloc'] = (f"Kataloq: {len(_cat2)} id, onlardan {int(_cat2.has_forecast.sum())} tam proqnozlaşdırılır (3 ssenari × 2026–2030), {int((~_cat2.has_forecast).sum())} yalnız tarix / qismən. "
                  f"Bölüşdürmənin nümunədən kənar yoxlaması (2024 → 2025, faktiki cəm verilmişkən):\n\n"
                  + mdt(_ah[['variable', 'variant', 'used_in_baseline', 'rmse', 'theil_vs_other_variant', 'dm_p_anchored_vs_average']])
                  + '\n\n2026 cari qiymətləndirmə (yanvar–iyun 2026 faktı), ən böyük bölmələr, doğulmalar (Əsas ssenari):\n\n'
                  + mdt(rd('section_nowcast_2026').query("variable == 'new'").sort_values('allocation_2026_before', ascending=False).head(6)[
                        ['section', 'h1_2026_observed', 'nowcast_fy_2026', 'allocation_2026_before', 'adjusted_2026', 'change_2026_pct', 'h1_2027_implied_before', 'h1_2027_implied']], dflt='{:,.1f}')
                  + f"\n\nKOS-un işçi sayında payı: qayda **{_smr.rule}** (ən yaxşı namizəd {_smr.best_candidate}, sıfır modelə qarşı DM p = {float(_smr.dm_p_vs_null):.2f}); "
                  f"son mənbə ilində tətbiq olunan: {_smr.applied_at_last_origin} ({_smr.coherence_last_origin if isinstance(_smr.coherence_last_origin, str) else 'uyğunluq qeydi yoxdur'}).")
_es = ECON['tables']['summary']; _rc = ECON['recovery']
G_['v2_econ'] = (f"Rejim: **{DATA_MODE}** ({ECON_TAG[DATA_MODE]}). Nəticələr: `{ECON['prefix']}*.csv`.\n\n" + mdt(_es[['model', 'model_az', 'n', 'interpretation_az']])
                 + ('\n\nParametr bərpası (həqiqi dəyər 95% EI daxilində):\n\n' + mdt(_rc.groupby('block', sort=False).agg(parameters=('parameter', 'size'), covered=('covered', 'sum')).reset_index())
                    if _rc is not None else '\n\nREAL rejimdə parametr bərpası tətbiq olunmur (həqiqi parametr yoxdur).'))
_RT = REGX.table()
G_['v2_registry'] = (f"`FR12_equations.json`: {len(REGX)} tənlik, proqnozda istifadə olunan {int(_RT.used.sum())}, sintetik {sum(e['synthetic'] for e in REGX.equations)}; "
                     f"bütün qiymətləndirilmiş əmsallar reyestrin statsmodels yenidən hesablaması ilə üst-üstə düşür (uyğunsuzluq: {int((_RT.coef_match == False).sum())}).\n\n"
                     + mdt(_RT.groupby(['used', 'verdict']).size().rename('tənlik').reset_index()))
G_['v2_engine'] = (f"`microlib/engines/fr12.py`: {len(_inp['exogenous'])} ekzogen yol (FR1 sektor ƏDV, faiz, kredit, qeyri-neft ÜDM; FR10 regional buraxılış; marja fərziyyələri), "
                   f"{len(_inp['coefficients'])} redaktə edilə bilən əmsal (giriş/çıxış sürücüləri və qırılma termini), {len(_inp['levers'])} rıçaq (IO ssenarisi: ε, θ, ΔN, birləşmə payları, xərc şoku, idxal payı, dövlət payı σ, λ). "
                   f"Yuxarı axın: FR1 və FR10 (`run_chain`). Öz-özünü yoxlama: {'keçdi' if ST12['ok'] else 'KEÇMƏDİ'} (maks. nisbi fərq {max(v['max_rel_diff'] for v in ST12['detail'].values()):.1e}); bir ssenari {_te:.2f} s.")
_cs = COEFSENS.loc[COEFSENS.groupby('headline').swing_pct.idxmax()][['headline_az', 'eq_id', 'coefficient', 'effect_minus_1se_pct', 'effect_plus_1se_pct']]
G_['v2_robust'] = (mdt(ROBS[ROBS.used_in_forecast][['equation', 'verdict', 'failed_test']]) + '\n\nƏmsal həssaslığı (±1 SE, 2030, Əsas ssenari) — hər başlıq göstəricisi üçün ən böyük təsir:\n\n'
                   + mdt(_cs, fmt={'effect_minus_1se_pct': '{:+.3f}', 'effect_plus_1se_pct': '{:+.3f}'}))
