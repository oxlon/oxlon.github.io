# %% [markdown]
# ### 18.5 Sənədləşdirmə addımı
#
# `docs/FR10_Methodology.md` sənədindəki icradan asılı hər rəqəm burada yenicə yazılmış CSV fayllarından
# `<!-- AUTO:name -->` və `<!-- /AUTO:name -->` işarələri arasında yaradılır. Xana hər işarənin mövcud olduğunu yoxlama
# ifadəsi ilə təsdiqləyir.

# %%
DOC = BASE / 'docs' / 'FR10_Methodology.md'
rd = lambda n, **kw: pd.read_csv(OUT / f'FR10_{n}.csv', **kw)
def mdt(df, fmt=None, index=False, dflt='{:.2f}'):
    fmt = fmt or {}
    d = df.reset_index() if index else df.copy()
    def cell(c, v):
        if isinstance(v, (float, np.floating)):
            return '—' if not np.isfinite(v) else fmt.get(c, dflt).format(v)
        if isinstance(v, (bool, np.bool_)): return 'yes' if v else 'no'
        return str(v).replace('|', '/')
    out = ['| ' + ' | '.join(str(c) for c in d.columns) + ' |', '|' + '---|' * len(d.columns)]
    out += ['| ' + ' | '.join(cell(c, r[c]) for c in d.columns) + ' |' for _, r in d.iterrows()]
    return '\n'.join(out)
pc = lambda v, d=2: f'{v:+.{d}f}%'
G = {}
man = rd('dsk_manifest'); fnd = rd('data_integrity_findings'); mx_ = rd('data_source_matrix'); gp = rd('data_gaps_and_alternatives')
ss = rd('scenario_summary', index_col=0); fm = rd('fan_meta').iloc[0]; pl = rd('plausibility', index_col=0); ew = rd('early_warning', index_col=0)
G['rev'] = (f"This run: {int(man.status.isin(['present', 'downloaded']).sum())} DSK tables, {len(fnd)} integrity findings, "
            f"{len(mx_)} indicators in the source matrix ({', '.join(f'{k} {v}' for k, v in mx_.status_group.value_counts().items())}); "
            f"branch model: {', '.join(BNAME[b] for b in OIL)} by throughput capacity and the oil price, non-oil branches by the "
            f"{'pooled related-sector model' if MAN_MODE == 'pooled' else 'equal-weight combination of the pooled related-sector model (β = ' + format(BETA, '.3f') + ') and constant shares'}; "
            f"regions {REG_LABEL.get(LABEL[SELECT['R']['chosen']], LABEL[SELECT['R']['chosen']])}"
            + (f" (κ = {SELECT['R']['kappa']:g})" if SELECT['R']['chosen'] != 'const' else '')
            + f"; baseline industry output {pc(ss.loc['Baseline', 'industry nominal output growth % pa'])} a year (nominal) 2026–2030; "
            f"{len(list(OUT.glob('FR10_*.csv')))} FR10 CSV files, of which {len(list(OUT.glob('FR10_SYNTHETIC_*.csv')))} SYNTHETIC.")
G['data'] = (mdt(man.groupby('section').status.value_counts().unstack(fill_value=0).reset_index())
             + f"\n\nBranch output adds up to the published mining, manufacturing and industry totals to "
             f"{pd.DataFrame(REC).max_gap_pct.iloc[:3].max():.3f}% in {yrs_full[0]}–{yrs_full[-1]}; national-accounts branch VA to "
             f"{REC2[1]['max_gap_pct']:.3f}%; FR1 and DSK section value added coincide in {LAST_ACT}.")
G['integrity'] = mdt(fnd[['id', 'finding', 'evidence', 'consequence']])
cnt = mx_.groupby(['pillar', 'status_group']).size().unstack(fill_value=0)
G['matrix_summary'] = mdt(cnt.reset_index(), dflt='{:.0f}')
G['matrix'] = mdt(mx_[['id', 'pillar', 'indicator_az', 'indicator_en', 'source_institution', 'dataset_table_row', 'granularity',
                       'years_available_now', 'status', 'integration_into_MIIS', 'analytical_use', 'presentation_form', 'alternative_if_unavailable']])
G['gaps'] = mdt(gp)
G['pres'] = mdt(rd('presentation_spec'))
cc = rd('concentration', index_col=0)
G['market'] = (f"Manufacturing HHI across branches {cc.loc[2005, 'HHI manufacturing branches']:.0f} (2005) → "
               f"{cc.loc[LAST_ACT, 'HHI manufacturing branches']:.0f} ({LAST_ACT}); CR4 {cc.loc[LAST_ACT, 'CR4 manufacturing, %']:.1f}%; HHI across "
               f"14 regions {cc.loc[LAST_ACT, 'HHI 14 regions']:.0f}. {LAST_ACT} leaders: " + ', '.join(f'{BNAME[b]} {v*100:.1f}%' for b, v in top.head(5).items())
               + f". Non-state share of industry {NS.loc[LAST_ACT, 'ALL']*100:.1f}% (manufacturing {NS.loc[LAST_ACT, 'C']*100:.1f}%, mining "
               f"{NS.loc[LAST_ACT, 'B']*100:.1f}%). Active industrial enterprises {NENT.loc[LAST_ACT, 'ALL']:,.0f} ({LAST_ACT}) vs "
               f"{NENT.loc[2015, 'ALL']:,.0f} (2015). Firm-concentration bound: large (non-SME) enterprises produce "
               f"{HHI_BOUND['non_sme_output_share']*100:.1f}% of industrial output (2024) and the register counts {HHI_BOUND['n_large_units']:.0f} large "
               f"industrial units (1 July 2026); an equal split among them gives HHI = {HHI_BOUND['hhi_lower_bound']:.1f}, and any unequal split "
               f"raises it, so this is a lower bound (the two sources refer to different dates). "
               f"The output-weighted branch non-state shares reproduce the published industry figure to {OWN_GAP:.2f} pp except in "
               + ', '.join(f'{int(y)} ({v:+.1f} pp)' for y, v in OWN_BAD.items()) + ' (F12).')
st_ = rd('tfp_sections', index_col=[0, 1]); tb = rd('tfp_branches', index_col=0)
G['eff'] = (mdt((st_.groupby(level=0).mean() * 100).round(2).reset_index().rename(columns={'section': 'section (mean % a year, 2007–2025)'}))
            + '\n\nBranch TFP (gross output, 2017–2025 cumulative, log points × 100), highest and lowest:\n\n'
            + mdt(pd.concat([tb.sort_values('TFP', ascending=False).head(4), tb.sort_values('TFP').head(4)]).reset_index()))
fs = rd('financial_sections', index_col=[0, 1])
G['fin'] = (mdt(fs['GOS_share_VA'].unstack(0).loc[[2005, 2010, 2015, 2019, 2022, LAST_ACT]].rename(columns=SECT).reset_index())
            + f"\n\nDVX profit-tax declarations: net margin {true_marg.min():.1f}–{true_marg.max():.1f}% (2021–{LAST_ACT}); declared losses "
            f"{(DVX.pt_loss/DVX.pt_profit*100).min():.0f}–{(DVX.pt_loss/DVX.pt_profit*100).max():.0f}% of taxable profit; tax arrears "
            f"{DVX.arrears.loc[2021]:,.0f} → {DVX.arrears.loc[LAST_ACT]:,.0f} mn AZN; investment self-financing "
            + ', '.join(f'{int(y)} {v:.1f}%' for y, v in SELF_FIN.items()) + f". Branch GOS-proxy margin {LAST_ACT}: median {GOSP.loc[LAST_ACT].median():.1f}% "
            f"of output, negative in " + (', '.join(BNAME[b] for b in GOSP.columns[GOSP.loc[LAST_ACT] < 0]) or 'none') + '.')
dt = rd('determinants_panel')
G['det'] = (mdt(dt[['spec', 'regressor', 'coef', 'se_DK', 'p_DK_t', 'p_wild', 'between_coef', 'n', 'years']], fmt={'n': '{:.0f}', 'years': '{:.0f}'}, dflt='{:.3f}')
            + f"\n\nContributions to real manufacturing growth 2016–{LAST_ACT} (log points × 100): top " + ', '.join(f'{BNAME[b]} {v:+.1f}' for b, v in cum[::-1].head(5).items())
            + '; bottom ' + ', '.join(f'{BNAME[b]} {v:+.1f}' for b, v in cum.head(3).items()) + '.')
