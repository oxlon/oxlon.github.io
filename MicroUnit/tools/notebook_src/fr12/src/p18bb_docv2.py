# %%
# v2 blocks of the methodology document (section 20), generated from this run's outputs. The English document gets English
# wording (`_v2('en')`); the same blocks worded in Azerbaijani (`_v2('az')`) go to output/FR12_doc_blocks_az.json, from which
# microlib/docgen_az_fr10_fr12.py writes docs/az/FR12_Metodologiya.md (same numbers).
from microlib import docgen_en as DE
_sf = rd('series_filled'); _imp = _sf[_sf.imputed]
_FAM = {'az': {'act': 'fəaliyyət qrupları (006)', 'conc': 'KOS payları (012/013)', 'sec': 'NACE bölmələri, tam il (2_1)', 'sec_h1': 'NACE bölmələri, yanvar–iyun (2_1)', 'reg': 'regionlar', 'info': 'digər'},
        'en': {'act': 'activity groups (006)', 'conc': 'SME shares (012/013)', 'sec': 'NACE sections, full year (2_1)', 'sec_h1': 'NACE sections, January–June (2_1)', 'reg': 'regions', 'info': 'other'}}
_g0 = _imp.assign(fam=_imp.id.str.split(':').str[1]).groupby('fam').agg(series=('id', 'nunique'), values=('id', 'size'), years=('year', lambda s: ', '.join(map(str, sorted(set(s))))))
_lead0 = _sf[_sf.method.str.startswith('not filled')].assign(fam=lambda d: d.id.str.split(':').str[1]).groupby('fam').agg(series=('id', 'nunique'), years=('year', lambda s: f'{min(s)}–{max(s)}'))
_gs = rd('gapfill_sensitivity')
_gc = _gs[_gs.kind == 'coefficient'][['item', 'term', 'observed_only', 'with_filled', 'rel_diff_pct']]
_gf = _gs[(_gs.kind == 'forecast_2030') & _gs.item.str.startswith('fr12:act')][['item', 'term', 'observed_only', 'with_filled', 'rel_diff_pct']]
_gsme = _gs[_gs.item.str.contains('sme_output_share', na=False)]
_nf = rd('not_forecast')
_ah = rd('section_allocation_holdout'); _sm = rd('sme_employment_model'); _smr = _sm[_sm.table == 'rule'].iloc[0]
_cat2 = rd('indicator_catalog')
_nc = rd('section_nowcast_2026').query("variable == 'new'").sort_values('allocation_2026_before', ascending=False).head(6)[
    ['section', 'h1_2026_observed', 'nowcast_fy_2026', 'allocation_2026_before', 'adjusted_2026', 'change_2026_pct', 'h1_2027_implied_before', 'h1_2027_implied']]
_es = ECON['tables']['summary']; _rc = ECON['recovery']; _ese = ECON['summary_en']
_RT = REGX.table()
_cs = COEFSENS.loc[COEFSENS.groupby('headline').swing_pct.idxmax()][['headline', 'headline_az', 'eq_id', 'coefficient', 'effect_minus_1se_pct', 'effect_plus_1se_pct']]
_HL_EN = {'fr12:act:N:ALL': 'registered entities, all activities (006)', 'fr12:act:entry:ALL': 'entry rate, all activities (006)',
          'fr12:act:exit:ALL': 'exit rate, all activities (006)', 'fr12:reg:N:ALL': 'statistical units, all regions'}
_LEN = _cat2.set_index('id').label_en
_rob = ROBS[ROBS.used_in_forecast][['equation', 'verdict', 'failed_test']]
def _v2(lang):
    az = lang == 'az'; B = {}
    fam = _FAM[lang]
    _g = _g0.copy(); _g.index = [fam.get(i, i) for i in _g.index]
    _lead = _lead0.copy(); _lead.index = [fam.get(i, i) for i in _lead.index]
    if az:
        B['v2_gaps'] = (f"Doldurulmuş dəyərlər: {len(_imp)} ({_imp.id.nunique()} sıra). Qiymətləndirmə yalnız müşahidə edilmiş məlumatla aparılır.\n\n"
                        + mdt(_g.reset_index().rename(columns={'index': 'sıra ailəsi', 'series': 'sıra', 'values': 'dəyər', 'years': 'doldurulmuş illər'}))
                        + '\n\nİlkin boşluqlar (doldurulmayıb, ekstrapolyasiya yoxdur):\n\n' + mdt(_lead.reset_index().rename(columns={'index': 'sıra ailəsi', 'series': 'sıra', 'years': 'illər'})))
        B['v2_gapsens'] = ('Əmsallar (yalnız müşahidə vs doldurulmuş 2021 daxil):\n\n' + mdt(_gc, fmt={'observed_only': '{:.4f}', 'with_filled': '{:.4f}'})
                           + '\n\n2030 proqnozları (bütün qruplar):\n\n' + mdt(_gf, fmt={'observed_only': '{:,.3f}', 'with_filled': '{:,.3f}'})
                           + f"\n\nKOS-un buraxılış payı 2030: maksimal |dəyişmə| {_gsme['diff'].abs().max():.2f} faiz bəndi.")
        B['v2_notforecast'] = (f"`FR12_not_forecast.csv`: {len(_nf)} id. " + '; '.join(f"{k}: {v}" for k, v in _nf.id.str.split(':').str[1].value_counts().items())
                               + '.\n\n' + mdt(_nf[_nf.id.str.contains('floor30')][['id', 'reason_az']]))
    else:
        B['v2_gaps'] = (f"Filled values: {len(_imp)} ({_imp.id.nunique()} series). Estimation uses observed data only.\n\n"
                        + mdt(_g.reset_index().rename(columns={'index': 'series family', 'series': 'series', 'values': 'values', 'years': 'filled years'}))
                        + '\n\nLeading gaps (not filled, no extrapolation):\n\n' + mdt(_lead.reset_index().rename(columns={'index': 'series family', 'series': 'series', 'years': 'years'})))
        B['v2_gapsens'] = ('Coefficients (observed data only vs with the filled 2021 values):\n\n' + mdt(_gc, fmt={'observed_only': '{:.4f}', 'with_filled': '{:.4f}'})
                           + '\n\n2030 forecasts (all groups):\n\n' + mdt(_gf, fmt={'observed_only': '{:,.3f}', 'with_filled': '{:,.3f}'})
                           + f"\n\nSME output share 2030: largest |change| {_gsme['diff'].abs().max():.2f} percentage points.")
        B['v2_notforecast'] = (f"`FR12_not_forecast.csv`: {len(_nf)} ids. " + '; '.join(f"{k}: {v}" for k, v in _nf.id.str.split(':').str[1].value_counts().items())
                               + '.\n\n' + mdt(_nf[_nf.id.str.contains('floor30')][['id', 'reason_en']].rename(columns={'reason_en': 'reason'})))
    _ahx = mdt(_ah[['variable', 'variant', 'used_in_baseline', 'rmse', 'theil_vs_other_variant', 'dm_p_anchored_vs_average']])
    _coh = _smr.coherence_last_origin if isinstance(_smr.coherence_last_origin, str) else ('uyğunluq qeydi yoxdur' if az else 'no coherence note')
    B['v2_alloc'] = ((f"Kataloq: {len(_cat2)} id, onlardan {int(_cat2.has_forecast.sum())} tam proqnozlaşdırılır (3 ssenari × 2026–2030), {int((~_cat2.has_forecast).sum())} yalnız tarix / qismən. "
                      f"Bölüşdürmənin nümunədən kənar yoxlaması (2024 → 2025, faktiki cəm verilmişkən):\n\n" if az else
                      f"Catalogue: {len(_cat2)} ids, of which {int(_cat2.has_forecast.sum())} are fully forecast (3 scenarios × 2026–2030), {int((~_cat2.has_forecast).sum())} history only / partial. "
                      f"Out-of-sample check of the allocation (2024 → 2025, given the actual total):\n\n") + _ahx
                     + ('\n\n2026 cari qiymətləndirmə (yanvar–iyun 2026 faktı), ən böyük bölmələr, doğulmalar (Əsas ssenari):\n\n' if az else
                        '\n\n2026 nowcast (January–June 2026 actual), largest sections, births (Baseline):\n\n') + mdt(_nc, dflt='{:,.1f}')
                     + (f"\n\nKOS-un işçi sayında payı: qayda **{_smr.rule}** (ən yaxşı namizəd {_smr.best_candidate}, sıfır modelə qarşı DM p = {float(_smr.dm_p_vs_null):.2f}); "
                        f"son mənbə ilində tətbiq olunan: {_smr.applied_at_last_origin} ({_coh})." if az else
                        f"\n\nSME share of employment: rule **{_smr.rule}** (best candidate {_smr.best_candidate}, DM p against the null = {float(_smr.dm_p_vs_null):.2f}); "
                        f"applied at the last source year: {_smr.applied_at_last_origin} ({_coh})."))
    _rcx = (mdt(_rc.groupby('block', sort=False).agg(parameters=('parameter', 'size'), covered=('covered', 'sum')).reset_index()) if _rc is not None else None)
    if az:
        B['v2_econ'] = (f"Rejim: **{DATA_MODE}** ({ECON_TAG[DATA_MODE]}). Nəticələr: `{ECON['prefix']}*.csv`.\n\n" + mdt(_es[['model', 'model_az', 'n', 'interpretation_az']])
                        + ('\n\nParametr bərpası (həqiqi dəyər 95% EI daxilində):\n\n' + _rcx if _rc is not None else '\n\nREAL rejimdə parametr bərpası tətbiq olunmur (həqiqi parametr yoxdur).'))
    else:
        B['v2_econ'] = (f"Mode: **{DATA_MODE}** ({ECON_TAG_EN[DATA_MODE]}). Results: `{ECON['prefix']}*.csv`.\n\n"
                        + mdt(_ese[['model', 'model_en', 'n', 'interpretation_en']].rename(columns={'model_en': 'label', 'interpretation_en': 'interpretation'}))
                        + ('\n\nParameter recovery (true value inside the 95% CI):\n\n' + _rcx if _rc is not None else '\n\nIn REAL mode parameter recovery does not apply (there are no true parameters).'))
    _rg = _RT.groupby(['used', 'verdict']).size().rename('tənlik' if az else 'equations').reset_index()
    if not az: _rg['verdict'] = _rg.verdict.map(DE.verdict)
    _nmis = int((_RT.coef_match == False).sum())  # noqa: E712
    B['v2_registry'] = ((f"`FR12_equations.json`: {len(REGX)} tənlik, proqnozda istifadə olunan {int(_RT.used.sum())}, sintetik {sum(e['synthetic'] for e in REGX.equations)}; "
                         f"bütün qiymətləndirilmiş əmsallar reyestrin statsmodels yenidən hesablaması ilə üst-üstə düşür (uyğunsuzluq: {_nmis}).\n\n" if az else
                         f"`FR12_equations.json`: {len(REGX)} equations, {int(_RT.used.sum())} used in the forecast, {sum(e['synthetic'] for e in REGX.equations)} synthetic; "
                         f"every estimated coefficient matches the registry's statsmodels re-estimation (mismatches: {_nmis}).\n\n") + mdt(_rg))
    _mx = max(v['max_rel_diff'] for v in ST12['detail'].values())
    B['v2_engine'] = (f"`microlib/engines/fr12.py`: {len(_inp['exogenous'])} ekzogen yol (FR1 sektor ƏDV, faiz, kredit, qeyri-neft ÜDM; FR10 regional buraxılış; marja fərziyyələri), "
                      f"{len(_inp['coefficients'])} redaktə edilə bilən əmsal (giriş/çıxış sürücüləri və qırılma termini), {len(_inp['levers'])} rıçaq (IO ssenarisi: ε, θ, ΔN, birləşmə payları, xərc şoku, idxal payı, dövlət payı σ, λ). "
                      f"Yuxarı axın: FR1 və FR10 (`run_chain`). Öz-özünü yoxlama: {'keçdi' if ST12['ok'] else 'KEÇMƏDİ'} (maks. nisbi fərq {_mx:.1e}); bir ssenari {_te:.2f} s." if az else
                      f"`microlib/engines/fr12.py`: {len(_inp['exogenous'])} exogenous paths (FR1 sector value added, interest rate, credit, non-oil GDP; FR10 regional output; margin assumptions), "
                      f"{len(_inp['coefficients'])} editable coefficients (entry/exit drivers and the break term), {len(_inp['levers'])} levers (IO scenario: ε, θ, ΔN, merger shares, cost shock, import share, state share σ, λ). "
                      f"Upstream: FR1 and FR10 (`run_chain`). Self-test: {'passed' if ST12['ok'] else 'FAILED'} (max rel. diff {_mx:.1e}); one scenario {_te:.2f} s.")
    _rr = _rob.copy(); _c = _cs.drop(columns='headline' if az else 'headline_az')
    if not az:
        _rr["verdict"] = _rr.verdict.map(DE.verdict); _rr["failed_test"] = _rr.failed_test.map(DE.tests)
        _c.insert(0, 'headline_en', _c.pop('headline').map(lambda h: _HL_EN.get(h, _LEN.get(h, h)))); _c = _c.rename(columns={'headline_en': 'headline'})
    B["v2_robust"] = (mdt(_rr) + ('\n\nƏmsal həssaslığı (±1 SE, 2030, Əsas ssenari) — hər başlıq göstəricisi üçün ən böyük təsir:\n\n' if az else
                                 '\n\nCoefficient sensitivity (±1 SE, 2030, Baseline) — the largest effect for each headline indicator:\n\n')
                      + mdt(_c, fmt={'effect_minus_1se_pct': '{:+.3f}', 'effect_plus_1se_pct': '{:+.3f}'}))
    return B
G_.update(_v2('en')); G_AZ = _v2('az')
if DE.MISSES: print('WARNING: failed-test phrases without an English rule (microlib/docgen_en.py):', sorted(set(DE.MISSES)))
