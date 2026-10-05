# %% [markdown]
# ## Hissə 18B — Göstəricilər kataloqu, tam proqnoz cədvəli və proqnozlaşdırılmayanlar
#
# `FR12_forecast_tidy.csv`: hər göstərici identifikatoru × ssenari × il üçün bir sətir — ilk mövcud ildən başlayan tarixi
# məlumatlar (hər ssenari üçün təkrarlanır ki, hər trayektoriya tam olsun), 2025 (fəaliyyət qrupları: cari qiymətləndirmə)
# və 2026–2030 proqnozları, mövcud olduqda 5–95% zolağı (Əsas ssenari), interpolyasiya edilmiş tarixi məlumatlarda
# `imputed = True` (Hissə 7.1). İdentifikatorlar `fr12:<block>:<metric>:<unit>` formasındadır və reyestrin `components`
# blokunun, mühərrik sıralarının və panelin identifikatorları ilə eynidir. Proqnozlaşdırıla bilməyən komponentlər səbəbi ilə
# birlikdə `FR12_not_forecast.csv` faylında sadalanır; aşağıdakı tamlıq yoxlaması qalan bütün komponentləri əhatə edir.

# %%
MET = {'new': ('Yeni qeydiyyatlar (doğulmalar)', 'New registrations (births)', 'vahid', 'level'), 'exits': ('Ləğv edilənlər (ölümlər)', 'Deregistrations (deaths)', 'vahid', 'level'),
       'N': ('Qeydiyyatdakı vahidlər (ehtiyat)', 'Registered units (stock)', 'vahid', 'level'), 'entry': ('Giriş əmsalı', 'Entry rate', '%', 'rate'),
       'exit': ('Çıxış əmsalı', 'Exit rate', '%', 'rate')}
CMET = {'sme_output_share': ('KOS-un buraxılışda payı', 'SME share of output', '%', 'share'), 'large_share': ('İri müəssisələrin buraxılışda payı', 'Large-firm share of output', '%', 'share'),
        'hhi_lower': ('HHI, aşağı hədd', 'HHI lower bound', 'HHI (0–10 000)', 'index'), 'hhi_upper': ('HHI, yuxarı hədd', 'HHI upper bound', 'HHI (0–10 000)', 'index'),
        'hhi_upper_floor30': ('HHI, yuxarı hədd (iri müəssisələr ≥ 30 mln AZN fərziyyəsi)', 'HHI upper bound, 30 mn AZN floor', 'HHI (0–10 000)', 'index'),
        'cr4_lower': ('CR4, aşağı hədd', 'CR4 lower bound', '%', 'share'), 'cr4_upper': ('CR4, yuxarı hədd', 'CR4 upper bound', '%', 'share'),
        'sme_employment_share': ('KOS-un məşğulluqda payı', 'SME share of employees', '%', 'share')}
TID, CAT = [], []
def put(sid, sc, y, v, fc, imp=False, lo=np.nan, hi=np.nan):
    TID.append(dict(id=sid, scenario=sc, year=int(y), value=float(v) if v == v else np.nan, lower_5=lo, upper_95=hi, is_forecast=bool(fc), imputed=bool(imp)))
SF = SERIES_FILLED[SERIES_FILLED.value.notna()].set_index(['id', 'year'])
def hist_from_fill(sid):
    return SF.loc[sid].sort_index() if sid in SF.index.get_level_values(0) else pd.DataFrame(columns=['value', 'imputed'])
_fcall = pd.concat([FC.assign(unit=FC.unit), AGG.assign(unit='ALL')], ignore_index=True)
_rgall = RG.groupby('year')[['enterprises', 'new', 'liquidated']].sum()
for pn, pab in [('activity', 'act'), ('region', 'reg')]:
    for u in UNITS[pn]:
        for m, (laz, len_, uaz, kind) in MET.items():
            sid = f'fr12:{pab}:{m}:{iid(u)}'
            if pn == 'region' and u == 'ALL':
                h = pd.DataFrame({'value': {'N': _rgall.enterprises, 'new': _rgall.new, 'exits': _rgall.liquidated, 'entry': _rgall.new / _rgall.enterprises * 100,
                                            'exit': _rgall.liquidated / _rgall.enterprises * 100}[m], 'imputed': False})
            else: h = hist_from_fill(sid)
            f = _fcall[(_fcall.panel == pn) & (_fcall.unit == u)]
            fb = FAN[(FAN.panel == pn) & (FAN.unit == u)].set_index('year')
            for sc in SCEN:
                for y, r in h.iterrows(): put(sid, sc, y, r.value, False, r.imputed)
                for _, r in f[f.scenario == sc].sort_values('year').iterrows():
                    b = (fb.loc[r.year, f'{m}_p5'], fb.loc[r.year, f'{m}_p95']) if (sc == 'Baseline' and m != 'exits' and r.year in fb.index) else (np.nan, np.nan)
                    put(sid, sc, r.year, r[m], True, False, *b)
            grp_az = ('Fəaliyyət qrupları (qeydiyyatdakı sahibkarlıq subyektləri, DSK 006)' if pn == 'activity' else 'İqtisadi rayonlar (statistik vahidlər, DSK 2_3)')
            CAT.append(dict(id=sid, group_az=grp_az, label_az=f"{laz}: {(GROUP_AZ if pn == 'activity' else REGION_AZ).get(u, u)}", label_en=f'{len_}: {u}', unit_az=uaz, kind=kind,
                            has_forecast=True, scenarios=SCEN, has_band=m != 'exits', source_csv='FR12_forecast_entry_exit.csv; FR12_fan_entry_exit.csv',
                            source_column={'N': 'N', 'new': 'new', 'exits': 'exits', 'entry': 'entry', 'exit': 'exit'}[m],
                            equation_ids=[EQ_MAP[k] for k in EQ_MAP if k[0] == pn and (k[1] == 'exit' or m in ('new', 'entry', 'N'))],
                            imputed_years=sorted({int(y) for y, r in h.iterrows() if r.imputed})))
for g in GRP:
    bh = BND[BND.group == g].set_index('year'); sh = {c: hist_from_fill(f'fr12:conc:{c}:{g}') for c in ['sme_output_share', 'large_share', 'sme_employment_share']}
    for c, (laz, len_, uaz, kind) in CMET.items():
        sid = f'fr12:conc:{c}:{g}'; hist = sh[c] if c in sh else pd.DataFrame({'value': bh[c], 'imputed': False}) if c in bh else pd.DataFrame(columns=['value', 'imputed'])
        for sc in SCEN:
            for y, r in hist.iterrows(): put(sid, sc, y, r.value, False, r.imputed)
            src_ = SMEEMP_FC if c == 'sme_employment_share' else CONCP
            for _, r in src_[(src_.scenario == sc) & (src_.group == g)].sort_values('year').iterrows(): put(sid, sc, r.year, r[c], True)
        CAT.append(dict(id=sid, group_az='Konsentrasiya: KOS payı və HHI/CR4 hədləri (fəaliyyət qrupları)', label_az=f'{laz}: {GROUP_AZ[g]}', label_en=f'{len_}: {g}', unit_az=uaz,
                        kind=kind, has_forecast=True, scenarios=SCEN, has_band=False,
                        source_csv=('FR12_sme_employment_model.csv; FR12_forecast_tidy.csv' if c == 'sme_employment_share' else 'FR12_concentration_paths.csv; FR12_concentration_bounds.csv; FR12_indicators_groups.csv'),
                        source_column=c, equation_ids=([EQ_MAP[k] for k in EQ_MAP if k[0] == 'sme'] + ['FR12.conc_bounds_map']) if c != 'sme_employment_share' else [EQ_MAP[k] for k in EQ_MAP if k[0] == 'sme_emp'],
                        imputed_years=sorted({int(y) for y, r in hist.iterrows() if r.imputed})))
    sid = f'fr12:ew:score:{g}'
    for sc in SCEN:
        put(sid, sc, 2024, float(EWS.set_index('group').score[g]), False)
        for _, r in EW_PROJ[(EW_PROJ.scenario == sc) & (EW_PROJ.group == g)].sort_values('year').iterrows(): put(sid, sc, r.year, r.score, True)
    CAT.append(dict(id=sid, group_az='Erkən xəbərdarlıq', label_az=f'Erkən xəbərdarlıq balı (0–1): {GROUP_AZ[g]}', label_en=f'Early-warning score: {g}', unit_az='bal (0–1)', kind='index',
                    has_forecast=True, scenarios=SCEN, has_band=False, source_csv='FR12_early_warning.csv; FR12_early_warning_projected.csv', source_column='score', equation_ids=[], imputed_years=[]))
for fam, F_, mets, gaz in [('sec', FSEC, ['stock', 'new', 'liq', 'entry', 'exit'], 'NACE bölmələri: statistik vahidlərin yaranması və ləğvi (DSK 2_1, tam il)'),
                           ('sec_h1', FSEC_H1, ['stock', 'new', 'liq'], 'NACE bölmələri: yanvar–iyun axınları (DSK 2_1)')]:
    for s in MKT:
        for m in mets:
            sid = f'fr12:{fam}:{m}:{s}'; h = hist_from_fill(sid)
            fq = SECFC[(SECFC.fam == fam) & (SECFC.sec == s) & (SECFC.metric == m)]
            for sc in SCEN:
                for y, r in h.iterrows(): put(sid, sc, y, r.value, False, r.imputed)
                for r in fq[fq.scenario == sc].sort_values('year').itertuples(): put(sid, sc, r.year, r.value, True, False, r.lower_5, r.upper_95)
            laz = {'stock': 'Statistik vahidlər', 'new': 'Yaradılmış vahidlər', 'liq': 'Ləğv edilmiş vahidlər', 'entry': 'Giriş əmsalı', 'exit': 'Çıxış əmsalı'}[m]
            CAT.append(dict(id=sid, group_az=gaz, label_az=f'{laz}: {SECT_AZ[s]}', label_en=f'{m}: section {s}', unit_az='%' if m in ('entry', 'exit') else 'vahid',
                            kind='rate' if m in ('entry', 'exit') else 'level', has_forecast=True, scenarios=SCEN, has_band=m != 'liq',
                            source_csv='derived: allocation — FR12_section_allocation.csv (history: FR12_register_flows.csv; FR12_series_filled.csv)', source_column='derived: allocation',
                            equation_ids=['FR12.alloc_sections' if fam == 'sec' else 'FR12.alloc_sections_h1'] + ([] if fam == 'sec' else ['FR12.alloc_sections']) + [EQ_MAP[k] for k in EQ_MAP if k[0] == 'region'],
                            imputed_years=sorted({int(y) for y, r in h.iterrows() if r.imputed})))
TIDY = pd.DataFrame(TID)
_cat = pd.DataFrame(CAT).set_index('id'); TIDY = TIDY.merge(_cat[['unit_az', 'kind']], left_on='id', right_index=True, how='left')
TIDY = TIDY[['id', 'scenario', 'year', 'value', 'lower_5', 'upper_95', 'unit_az', 'kind', 'is_forecast', 'imputed']].sort_values(['id', 'scenario', 'year']).reset_index(drop=True)
