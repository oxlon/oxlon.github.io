# %% [markdown]
# ## Hissə 18 — Yoxlamalar, nəticə faylları və sənədləşdirmə addımı
#
# ### 18.1 Nəticə faylları və arifmetik yoxlamalar

# %%
_ig = IND_G.merge(PCM_G.PCM.reset_index().rename(columns={'group': 'group'}), on=['group', 'year'], how='left')
_ig = _ig.merge(SME.reset_index(), on=['group', 'year'], how='left')
_ig['name'] = _ig.group.map(lambda g: GROUPS[g][0])
_ig.to_csv(OUT / 'FR12_indicators_groups.csv', index=False)
_is = IND_S.merge(NA.reset_index()[['sec', 'year', 'PCM']], on=['sec', 'year'], how='left'); _is['name'] = _is.sec.map(lambda s: SECT[s][0])
_is.to_csv(OUT / 'FR12_indicators_sections.csv', index=False)
RG[['region', 'year', 'enterprises', 'new', 'liquidated', 'micro', 'small', 'medium', 'entry', 'exit', 'churn', 'net']].to_csv(OUT / 'FR12_indicators_regions.csv', index=False)
REGDISP.to_csv(OUT / 'FR12_regional_dispersion.csv')
SURV.reset_index().to_csv(OUT / 'FR12_cohort_size_ratio.csv', index=False)
TAXB.to_csv(OUT / 'FR12_taxpayer_concentration.csv')
pd.concat([BARR, LIC_G.add_prefix('licences_')], axis=1).to_csv(OUT / 'FR12_barriers.csv')
INSTAB.to_frame().to_csv(OUT / 'FR12_share_instability_branches.csv')
NA.reset_index()[['sec', 'year', 'GO', 'VA', 'CE', 'GOS', 'PCM']].to_csv(OUT / 'FR12_pcm_sections.csv', index=False)
FLOWS.to_csv(OUT / 'FR12_register_flows.csv', index=False)
pd.DataFrame(SELTAB).to_csv(OUT / 'FR12_selection_scores.csv', index=False)
SELSUM = selsum()
SELSUM['applied_at_last_origin'] = [', '.join(FINAL[(r.panel, r.dep)]['spec']) or 'no driver (null)' if (r.panel, r.dep) in FINAL else 'see Part 14' for r in SELSUM.itertuples()]
SELSUM.to_csv(OUT / 'FR12_selection_summary.csv', index=False)
HOLDV.to_csv(OUT / 'FR12_holdout_validation.csv', index=False); HOLDTAB.to_csv(OUT / 'FR12_holdout_detail.csv', index=False)
pd.DataFrame(COHLOG).drop_duplicates(subset=['key', 'origin', 'driver']).to_csv(OUT / 'FR12_coherence.csv', index=False)
FULL.to_csv(OUT / 'FR12_fe_estimates.csv', index=False)
BAND_META.to_csv(OUT / 'FR12_band_meta.csv', index=False)
MERGER_SCREEN.to_csv(OUT / 'FR12_merger_screen.csv', index=False)
FINDINGS.to_csv(OUT / 'FR12_data_integrity_findings.csv', index=False)
BR_SCHEMA.to_csv(OUT / 'FR12_business_register_schema.csv', index=False)
# arithmetic checks
_t = FC[FC.panel == 'activity'].groupby(['scenario', 'year']).N.sum(); _a = AGG[AGG.panel == 'activity'].set_index(['scenario', 'year']).N
chk('aggregate N = sum of group N in every scenario-year', float((_t - _a).abs().max()), (_t - _a).abs().max() < 1e-6)
chk('fan: p5 <= p50 <= p95 for every series', 0.0, bool(((FAN.entry_p5 <= FAN.entry_p50 + 1e-9) & (FAN.entry_p50 <= FAN.entry_p95 + 1e-9) & (FAN.N_p5 <= FAN.N_p95)).all()))
chk('SME + large output shares = 100 (all groups, years)', float((SME.sme_output_share + SME.large_output_share - 100).abs().max()), (SME.sme_output_share + SME.large_output_share - 100).abs().max() < 1e-9)
chk('early-warning score in [0, 1]', float(EWS.score.max()), bool(EWS.score.between(0, 1).all()))
CHKS = pd.DataFrame(CHK); CHKS.to_csv(OUT / 'FR12_identity_checks.csv', index=False)
display(CHKS)
assert CHKS.passed.all(), 'arithmetic check failed'
print(f'{len(CHKS)} arithmetic checks pass; {len(list(OUT.glob("FR12_*.csv")))} FR12 CSV files in output/ '
      f'({len(list(OUT.glob("FR12_SYNTHETIC_*.csv")))} SYNTHETIC, {len(list(OUT.glob("FR12_FIRM_*.csv")))} FIRM)')
