# %% [markdown]
# ### 18.2 Sənədləşdirmə addımı
#
# `docs/FR12_Methodology.md` sənədindəki icradan asılı hər rəqəm burada yenicə yazılmış CSV fayllarından
# `<!-- AUTO:name -->` və `<!-- /AUTO:name -->` işarələri arasında yaradılır. Xana hər işarənin mövcud olduğunu və sənəddə
# notebook-un doldurmadığı heç bir işarənin olmadığını yoxlama ifadəsi ilə təsdiqləyir.

# %%
DOC = BASE / 'docs' / 'FR12_Methodology.md'
rd = lambda n, **kw: pd.read_csv(OUT / f'FR12_{n}.csv', **kw)
def mdt(df, fmt=None, dflt='{:.2f}'):
    fmt = fmt or {}; d = df.copy()
    def cell(c, v):
        if isinstance(v, (bool, np.bool_)): return 'yes' if v else 'no'
        if isinstance(v, str) and v in ('True', 'False'): return 'yes' if v == 'True' else 'no'
        if isinstance(v, (float, np.floating)): return '—' if not np.isfinite(v) else fmt.get(c, dflt).format(v)
        if isinstance(v, (int, np.integer)): return f'{int(v)}'
        return str(v).replace('|', '/')
    out = ['| ' + ' | '.join(str(c) for c in d.columns) + ' |', '|' + '---|' * len(d.columns)]
    out += ['| ' + ' | '.join(cell(c, r[c]) for c in d.columns) + ' |' for _, r in d.iterrows()]
    return '\n'.join(out)
yl = lambda xs: ', '.join(str(int(x)) for x in sorted(set(xs)))
G_ = {}
man = rd('dsk_manifest'); mx_ = rd('data_source_matrix'); fnd_ = rd('data_integrity_findings'); hv = rd('holdout_validation'); ss_ = rd('selection_summary')
fan_ = rd('fan_entry_exit'); fc_ = rd('forecast_entry_exit'); ew_ = rd('early_warning'); scs = rd('scenario_summary'); sca = rd('scenario_assumptions')
pm = REG_META; syn = DATA_MODE == 'SYNTHETIC'
G_['mode_header'] = (f"**Layer-B data mode: {pm['mode']}** — input file `data/business_register/{pm['file']}`, {pm['rows']:,} rows, {pm['records']:,} records "
                     f"({pm['enterprises_last']:,.0f} active enterprises in {pm['year_max']}), {pm['sections']} NACE sections, {pm['divisions']} divisions, "
                     f"{pm['regions']} regions, {pm['year_min']}–{pm['year_max']}."
                     + (" The register is **SYNTHETIC — not real enterprise data**; Layer-B outputs are a pipeline demonstration, not findings." if syn else
                        " Layer-B outputs (`FR12_FIRM_*.csv`) are computed from the Ministry's register."))
_ab = fan_[(fan_.unit == 'ALL') & (fan_.panel == 'activity')].set_index('year'); _rb = fan_[(fan_.unit == 'ALL') & (fan_.panel == 'region')].set_index('year')
G_['rev'] = (f"This run: {int((man.origin == 'archived vintage').sum())} archived DSK vintages and {len(man)} input files (URL and SHA-256 each); "
             f"{len(fnd_)} data-integrity findings; {len(mx_)} indicators in the source matrix ({', '.join(f'{k} {v}' for k, v in mx_.status.value_counts().items())}); "
             f"baseline 2030, registered entrepreneurship subjects: {_ab.loc[2030, 'new_baseline']:,.0f} new registrations (90% band {_ab.loc[2030, 'new_p5']:,.0f}–{_ab.loc[2030, 'new_p95']:,.0f}), "
             f"entry rate {_ab.loc[2030, 'entry_baseline']:.2f}% ({_ab.loc[2030, 'entry_p5']:.2f}–{_ab.loc[2030, 'entry_p95']:.2f}), exit rate {_ab.loc[2030, 'exit_baseline']:.2f}%; "
             f"statistical units {_rb.loc[2030, 'N_baseline']:,.0f} ({_rb.loc[2030, 'N_p5']:,.0f}–{_rb.loc[2030, 'N_p95']:,.0f}); early-warning threshold z* = {Z_STAR:g}, "
             f"watch list: {', '.join(ew_[ew_.watch_list].name) or 'none'}; {len(list(OUT.glob('FR12_*.csv')))} FR12 CSV files, of which "
             f"{len(list(OUT.glob('FR12_SYNTHETIC_*.csv')))} SYNTHETIC; runtime {time.time() - T0:.0f} s.")
_mg = man.groupby(['origin', 'status']).size().rename('files').reset_index()
_mv = man[man.origin != 'FR10 download (read only)'][['file', 'source_url', 'content', 'sha256']].assign(sha256=lambda d: d.sha256.str[:16] + '…')
G_['data'] = (mdt(_mg) + '\n\nArchived vintages and new DSK downloads (full list with SHA-256 in `FR12_dsk_manifest.csv`):\n\n' + mdt(_mv)
              + f"\n\nActivity panel years: {yl(PA.year)}; region panel: {yl(PR.year)}; register flows by section: full years "
              f"{yl(FLOWS[(FLOWS.kind == 'section') & (FLOWS.period == 'FY')].year)}, half-years {yl(FLOWS[(FLOWS.kind == 'section') & (FLOWS.period == 'H1')].year)}.")
G_['integrity'] = mdt(fnd_)
G_['matrix_summary'] = mdt(mx_.groupby(['pillar', 'status']).size().unstack(fill_value=0).reset_index())
G_['matrix'] = mdt(mx_[['id', 'pillar', 'indicator_az', 'indicator_en', 'formula', 'source_institution', 'dataset_table_row', 'granularity', 'years_available_now',
                        'status', 'integration_into_MIIS', 'analytical_use', 'presentation_form', 'alternative_if_unavailable']])
G_['gaps'] = mdt(rd('data_gaps_and_alternatives')); G_['pres'] = mdt(rd('presentation_spec'))
ig = rd('indicators_groups')
G_['ind_groups'] = ('New registrations:\n\n' + mdt(ig.pivot_table(index='name', columns='year', values='new').reset_index(), dflt='{:,.0f}')
                    + '\n\nEntry rate, %:\n\n' + mdt(ig.pivot_table(index='name', columns='year', values='entry').round(2).reset_index())
                    + '\n\nExit rate, %:\n\n' + mdt(ig.pivot_table(index='name', columns='year', values='exit').round(2).reset_index()))
isec = rd('indicators_sections'); _p = isec.pivot_table(index=['sec', 'name'], columns='year', values=['entry', 'exit']).round(2)
G_['ind_sections'] = mdt(_p.set_axis([f'{a} {b}' for a, b in _p.columns], axis=1).reset_index())
G_['ind_other'] = (f"Regions: entry {RG.entry.min():.1f}–{RG.entry.max():.1f}%, exit {RG.exit.min():.2f}–{RG.exit.max():.2f}% (2021–2025); coefficient of variation of "
                   f"regional entry {REGDISP.cv_entry.iloc[0]:.2f} (2021) → {REGDISP.cv_entry.iloc[-1]:.2f} ({int(REGDISP.index[-1])}); HHI of units across regions "
                   f"{REGDISP.hhi_units.iloc[-1]:.0f}. Manufacturing branch-share instability {INSTAB.loc[2006:2015].mean()*100:.1f} pp a year (2006–15) vs "
                   f"{INSTAB.loc[2016:].mean()*100:.1f} pp (2016–25). Licences issued {int(BARR.licences_new.loc[2016])} (2016) → {int(BARR.licences_new.loc[LAST_ACT])} "
                   f"({LAST_ACT}) — an entry indicator. Inspections are not comparable over time (F18: coverage widened in 2020–2022).\n\n"
                   "Price-cost margin proxy by group, % of output:\n\n" + mdt(PCM_G.PCM.unstack(0).loc[[2015, 2019, 2022, 2024, LAST_ACT]].T.round(1).reset_index())
                   + '\n\nCohort-size ratio (active SMEs aged k / aged 1, same year — mixes cohort size and survival; **not** a survival rate):\n\n' + mdt(SURV.round(2).reset_index()))
b24 = BND[BND.year == 2024]
G_['bounds'] = (mdt(b24[['group', 'market_output_mn', 'n_large', 'large_share', 'caps_used', 'hhi_lower', 'hhi_upper', 'cr4_lower', 'cr4_upper',
                         'hhi_upper_floor30', 'cr4_upper_floor30', 'hhi_upper_floor15', 'cr4_upper_floor15']].round(1))
                + '\n\nTaxpayer size classes (DVX, micro excluded — F8):\n\n' + mdt(TAXB.round(2).reset_index()))
G_['noar'] = mdt(rd('noar_constructs'))
G_['fe'] = mdt(rd('fe_estimates').round(3))
