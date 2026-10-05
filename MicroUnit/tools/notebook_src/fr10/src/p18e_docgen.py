# %%
sl = rd('share_system_selection', index_col=0)
G['select'] = '\n\n'.join(f'**{lab}**\n\n' + mdt(sl[sl.system == lab].drop(columns=['system']).reset_index(), dflt='{:.3f}')
                          for lab in ['manufacturing', 'mining', 'regions'])
ho = rd('holdout_validation')
G['holdout'] = mdt(ho[ho.selected][['system', 'measure', 'weighting', 'model', 'RMSE', 'U_vs_random_walk', 'U_vs_constant_growth', 'DM_p_vs_rw', 'DM_p_vs_cg']], dflt='{:.3f}')
G['holdout_full_alt'] = mdt(ho[(~ho.selected) & ho.system.str.contains('forecasting model')][['measure', 'weighting', 'model', 'RMSE', 'U_vs_random_walk', 'U_vs_constant_growth']], dflt='{:.3f}')
G['holdout_info'] = mdt(ho[(~ho.selected) & (~ho.system.str.contains('forecasting model')) & (ho.weighting == 'unweighted') & ho.measure.isin(['nominal', 'shares_pp'])]
                        [['system', 'measure', 'model', 'RMSE', 'U_vs_random_walk', 'U_vs_constant_growth']], dflt='{:.3f}')
G['forecast'] = (mdt(ss.reset_index()) + '\n\nSections, baseline:\n\n' + mdt(SEC_FC.reset_index().rename(columns={'index': 'section'})))
fan_ = rd('fan_charts', index_col=[0, 1, 2])
def band(ind, u):
    r = fan_.loc[(ind, u, gk)]
    return f"baseline {pc(r.baseline)}, median {pc(r.p50)}, 90% band {pc(r.p5, 1)} to {pc(r.p95, 1)}"
G['bands'] = (f"{int(fm.n_reps)} FR1 replications; {int(fm.n_paths_C)} historical model-error paths for the branch allocation and "
              f"{int(fm.n_paths_R)} for regions (paths crossing the 2019 coverage break excluded). Average growth 2026–2030 — industry output: "
              f"{band('industry output, mn AZN', 'Industry')}; " + '; '.join(f"{SECT[s_].lower()}: {band('section output, mn AZN', SECT[s_])}" for s_ in SECV)
              + ". The baseline is FR1's scenario path, the median is that of the replications; they differ because FR1's draws are not centred on its scenario. "
              f"The wide industry and electricity tails come from FR1's oil- and electricity-price draws: with FR1's prices held at their baseline paths the bands are — industry: "
              f"{band('industry output, mn AZN — FR1 prices held at baseline', 'Industry')}; electricity: {band('section output, mn AZN — FR1 prices held at baseline', 'Electricity')}. "
              f"Refining share of manufacturing in {FC_YEARS[-1]}: {fan_.loc[('branch share of manufacturing, %', '19', str(FC_YEARS[-1])), 'p5']:.1f}–"
              f"{fan_.loc[('branch share of manufacturing, %', '19', str(FC_YEARS[-1])), 'p95']:.1f}% (baseline {fan_.loc[('branch share of manufacturing, %', '19', str(FC_YEARS[-1])), 'baseline']:.1f}%). "
              f"Manufacturing GOS share of VA in {FC_YEARS[-1]}: {fan_.loc[('section GOS, % of value added', 'Manufacturing', str(FC_YEARS[-1])), 'p5']:.1f}–"
              f"{fan_.loc[('section GOS, % of value added', 'Manufacturing', str(FC_YEARS[-1])), 'p95']:.1f}%. Baseline inside the inter-quartile band in "
              f"{fm.share_inside_iqr:.1f}% of series-years, inside the 90% band in {fm.share_inside_90:.1f}%.")
G['plaus'] = (mdt(pl.reset_index()[['code', 'unit', 'forecast_real_growth', 'hist_2010_2019', 'hist_2021_2025', 'best_5yr', 'worst_5yr', 'flag', 'hist_2010_19_inside_90band']])
              + f"\n\n{int((pl.flag.fillna('') != '').sum())} of {len(pl)} units flagged.")
G['ew'] = (mdt(ew.reset_index()[['nace2', 'branch', 'share_2025_pct', 'margin_2023_25', 'margin_z', 'share_z', 'lp_z', 'F_renewal', 'F_stocks', 'n_flags', 'watch_list']])
           + f"\n\nWatch list ({int(ew.watch_list.sum())}): " + ', '.join(ew[ew.watch_list].sort_values('n_flags', ascending=False).branch) + '.')
_pre = 'SYNTHETIC_' if DATA_MODE == 'SYNTHETIC' else 'FIRM_'
pm = PANEL_META
G['mode_header'] = (f"**Layer-B data mode: {pm['mode']}** — input file `data/firm_panel/{pm['file']}`, {pm['rows']:,} rows, {pm['firms']:,} firms, "
                    f"{pm['branches']} NACE divisions, {pm['year_min']}–{pm['year_max']}."
                    + (" The firm panel is **SYNTHETIC — not real enterprise data**; Layer-B outputs are a pipeline demonstration, not findings."
                       if pm['mode'] == 'SYNTHETIC' else " Layer-B outputs (`FR10_FIRM_*.csv`) are computed from the Ministry's enterprise data."))
G['layerb'] = (G['mode_header'] + "\n\n"
               + ("**This section is a pipeline demonstration, not findings.** The Ministry replaces "
                  "`data/firm_panel/FR10_firm_panel_SYNTHETIC.csv` with its own data in its own system (`FR10_firm_panel.csv/.xlsx` or "
                  "`FIRM_PANEL_PATH`) and re-runs the notebook; outputs then become `FR10_FIRM_*.csv`.\n\n" if pm['mode'] == 'SYNTHETIC' else '')
               + 'Pipeline tests on the loaded panel:\n\n' + mdt(rd(f'{_pre}pipeline_tests')[['test', 'value', 'passed']])
               + '\n\nSwap tests (temporary directory; the project never holds a real-named file it did not receive):\n\n'
               + mdt(rd('firm_panel_swap_tests')) + f"\n\nValidator on the loaded panel: {int((VREP.severity == 'warning').sum())} warnings, 0 hard errors "
               "(`FR10_firm_panel_validation_report.csv`).")
ck = rd('identity_checks')
G['checks'] = f"{int(ck.passed.sum())} of {len(ck)} arithmetic checks pass (`FR10_identity_checks.csv`); every one holds by construction."
G['outputs'] = ', '.join(f'`{p.name}`' for p in sorted(OUT.glob('FR10_*.csv')))
doc = DOC.read_text(); missing = []
for k, v in G.items():
    pat = re.compile(rf'(<!-- AUTO:{k} -->)(.*?)(<!-- /AUTO:{k} -->)', re.S)
    if not pat.search(doc): missing.append(k); continue
    doc = pat.sub(lambda m: m.group(1) + '\n' + v + '\n' + m.group(3), doc)
assert not missing, f'doc markers missing: {missing}'
left = set(re.findall(r'<!-- AUTO:(\w+) -->', doc)) - set(G)
assert not left, f'doc has markers the notebook does not fill: {left}'
DOC.write_text(doc)
print(f'docs/FR10_Methodology.md: {len(G)} generated blocks filled from this run\'s CSV outputs: {sorted(G)}')
