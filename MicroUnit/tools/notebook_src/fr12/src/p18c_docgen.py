# %%
G_['select'] = mdt(ss_.round(3))
_co = rd('coherence')
G_['coh'] = mdt(_co[['key', 'origin', 'driver', 'fe', 'fd', 'fd_lo', 'fd_hi', 'transitions', 'status']].round(3)) if len(_co) else 'No structural driver was checked.'
G_['holdout'] = mdt(hv[['panel', 'metric', 'rule', 'implied_rw_weight', 'n', 'targets', 'rmse_rule', 'rmse_null', 'rmse_rw', 'rmse_constant', 'theil_rule_vs_rw',
                        'theil_rule_vs_constant', 'theil_null_vs_rw', 'theil_constant_vs_rw', 'dm_p_rule_vs_rw', 'dm_p_rule_vs_constant']].round(3))
fa = fc_[fc_.unit == 'ALL'].pivot_table(index=['panel', 'year'], columns='scenario', values=['new', 'entry', 'exit', 'N']).round(2)
fa.columns = [f'{a} {b}' for a, b in fa.columns]
_nf = {c: '{:,.0f}' for c in fa.columns if c.startswith('N ') or c.startswith('new ')}
G_['forecast'] = (mdt(fa.reset_index(), fmt=_nf)
                  + '\n\nBaseline bands (5–95%):\n\n' + mdt(fan_[(fan_.unit == 'ALL') & fan_.year.isin([2025, 2026, 2028, 2030])][['panel', 'year', 'new_baseline', 'new_p5', 'new_p95',
                    'entry_baseline', 'entry_p5', 'entry_p95', 'exit_baseline', 'exit_p5', 'exit_p95', 'N_baseline', 'N_p5', 'N_p95']],
                    fmt={c: '{:,.0f}' for c in ['new_baseline', 'new_p5', 'new_p95', 'N_baseline', 'N_p5', 'N_p95']})
                  + '\n\nBand construction:\n\n' + mdt(rd('band_meta')))
pl_ = rd('plausibility'); lb_ = rd('last_actual_vs_2026_band')
G_['plaus'] = (f"{int(pl_.flag.notna().sum())} of {len(pl_)} unit-variable forecasts flagged:\n\n" + mdt(pl_[pl_.flag.notna()].round(2))
               + f"\n\nLast actual entry rate against the 2026 band: {int((~lb_.inside).sum())} of {len(lb_)} outside, each with its reason:\n\n"
               + mdt(lb_[~lb_.inside].round(2)))
cpb = rd('concentration_paths'); cpb = cpb[(cpb.scenario == 'Baseline') & cpb.year.isin([2026, 2030])]
_cp = cpb.pivot_table(index='group', columns='year', values=['large_share', 'hhi_lower', 'hhi_upper']).round(1)
G_['concpaths'] = mdt(_cp.set_axis([f'{a} {b}' for a, b in _cp.columns], axis=1).reset_index())
_s5 = SC_RES[SC_RES.scenario == 'S5']
G_['scen'] = (mdt(sca[['scenario', 'market', 'change', 'assumption', 'hhi_range', 'structure_source']])
              + '\n\nResults over the whole range (HHI lower → upper bound × ε 0.5–2 × θ ∈ {1, 0.5}); endpoints at ε = 1, θ = 1:\n\n'
              + mdt(scs[['scenario', 'market', 'assumption', 'hhi_min', 'hhi_max', 'd_price_min', 'd_price_max', 'd_price_at_lower_bound', 'd_price_at_upper_bound',
                         'd_output_min', 'd_output_max', 'd_cs_pct_min', 'd_cs_pct_max', 'd_cs_mn_min', 'd_cs_mn_max']], fmt={'hhi_min': '{:,.0f}', 'hhi_max': '{:,.0f}'})
              + '\n\nMerger screens (S2):\n\n' + mdt(rd('merger_screen').round(1))
              + f"\n\nMixed oligopoly (S5): the welfare-maximising SOE prices at its rising marginal cost and expands output; privatisation makes it restrict "
              f"output like a private firm, so its share falls (to {_s5.soe_share_after.min():.1f}–{_s5.soe_share_after.max():.1f}% across cases), the price rises by "
              f"{_s5.d_price_pct.min():.2f}–{_s5.d_price_pct.max():.2f}% and total welfare changes by {_s5.d_welfare_pct_rev.min():.2f} to {_s5.d_welfare_pct_rev.max():.2f}% of market revenue; "
              f"private Cournot firms (symmetric-equivalent) {_s5.n_private.min():.1f}–{_s5.n_private.max():,.0f}.")
_fl = rd('early_warning_false_listing')
G_['ew'] = (f"Threshold z* = {Z_STAR:g}. Simulated false-listing rates (share of no-change sectors reaching the watch list):\n\n"
            + mdt(_fl[['z_threshold', 'null', 'false_listing_rate']].round(3)) + '\n\n'
            + mdt(ew_[['group', 'name', 'z_conc', 'z_entry', 'z_exit', 'z_mob', 'z_margin', 'F_conc', 'F_entry', 'F_exit', 'F_mob', 'F_margin_entry', 'n_available',
                       'n_flags', 'score', 'watch_list', 'info_licences_z', 'info_cohort_size_ratio_change_pct', 'info_state_share_of_active_SMEs_2024']].round(2))
            + f"\n\nWatch list ({int(ew_.watch_list.sum())}): " + ('; '.join(f"{r['name']} — {r['flags']}" for _, r in ew_[ew_.watch_list].iterrows()) or 'none')
            + '. Single flags (monitor): ' + ('; '.join(f"{r['name']} — {r['flags']}" for _, r in ew_[(ew_.n_flags >= 1) & ~ew_.watch_list].iterrows()) or 'none') + '.')
_pre = 'SYNTHETIC_' if syn else 'FIRM_'
_cs = rd(f"{_pre}{'calibration_errors' if syn else 'coverage_vs_dsk'}_summary")
G_['layerb'] = (G_['mode_header'] + '\n\n' + ("**This section is a pipeline demonstration, not findings.** The Ministry replaces "
                "`data/business_register/FR12_business_register_SYNTHETIC.csv` with its own register in its own system (`FR12_business_register.csv/.xlsx` or "
                "`BUSREG_PATH`) and re-runs the notebook; outputs then become `FR12_FIRM_*.csv`.\n\n" if syn else '')
                + ('Calibration errors against the DSK aggregates:\n\n' if syn else 'Coverage of the register against the DSK aggregates:\n\n')
                + mdt(_cs.drop(columns=['WATERMARK'], errors='ignore').round(3))
                + '\n\nPipeline tests:\n\n' + mdt(rd(f'{_pre}pipeline_tests').drop(columns=['WATERMARK'], errors='ignore')[['test', 'value', 'passed']].round(3))
                + '\n\nSwap tests (temporary directory):\n\n' + mdt(rd('business_register_swap_tests'))
                + f"\n\nValidator on the loaded register: {int((VREP.severity == 'warning').sum())} warnings, 0 hard errors.")
ck = rd('identity_checks')
G_['checks'] = f"{int(ck.passed.sum())} of {len(ck)} arithmetic checks pass (`FR12_identity_checks.csv`)."
G_['outputs'] = ', '.join(f'`{p.name}`' for p in sorted(OUT.glob('FR12_*.csv')))
doc = DOC.read_text(); missing = []
for k, v in G_.items():
    pat = re.compile(rf'(<!-- AUTO:{k} -->)(.*?)(<!-- /AUTO:{k} -->)', re.S)
    if not pat.search(doc): missing.append(k); continue
    doc = pat.sub(lambda m: m.group(1) + '\n' + v + '\n' + m.group(3), doc)
assert not missing, f'doc markers missing: {missing}'
left = set(re.findall(r'<!-- AUTO:(\w+) -->', doc)) - set(G_)
assert not left, f'doc has markers the notebook does not fill: {left}'
DOC.write_text(doc)
# Azerbaijani wording of the v2 blocks (built with them in the v2 cell) for docs/az/FR12_Metodologiya.md (microlib/docgen_az_fr10_fr12.py)
from microlib import docgen_az_fr10_fr12 as _DAZ
_DAZ.write_az_sources('FR12', {k: '\n' + G_[k] + '\n' for k in G_AZ}, {k: '\n' + v + '\n' for k, v in G_AZ.items()})
print(f'docs/FR12_Methodology.md: {len(G_)} generated blocks filled from this run\'s CSV outputs; total runtime {time.time() - T0:.0f} s')
