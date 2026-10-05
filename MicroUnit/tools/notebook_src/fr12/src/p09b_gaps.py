# %% [markdown]
# ### 9.2 Boşluqlar, alternativlər və tədbirlər; 9.3 MİİS istifadəçi görünüşləri

# %%
GAPS = pd.DataFrame([
 ('Firm-level revenue by NACE × region (DSK business register)', 'no firm HHI/CR4, no market-share mobility, no Boone indicator',
  'size-class concentration bounds (Part 8); branch-share instability from FR10', 'bounds are wide where SMEs dominate; activity groups are broader than antitrust markets',
  'confirm the register extract (requested 24 Aug 2026); agree pseudonymised firm_id and annual delivery'),
 ('Firm entry and exit dates', 'no cohort survival, no entrant/exiter size', 'DSK 006 registration flows; 024-028 age structure; register flows 2_1/2_3',
  '006 counts registrations incl. individual entrepreneurs, not market entry; register exit understates exit (F14)', 'include registration/liquidation dates in the register extract'),
 ('Long time series of entry/exit by activity', 'only 5 annual observations per group (2019-2024, no 2021); low test power',
  'archived DSK vintages (Part 4)', 'definitions changed between vintages ("newly created" → "newly registered")', 'ask DSK for the 2010-2025 series of table 006 and 2_1 in one consistent vintage'),
 ('Firm costs (cost of sales, operating costs)', 'no firm price-cost margin or Boone indicator', 'section PCM proxy from national accounts', 'aggregate PCM mixes capital returns with rents',
  'link the FR10 Tax Service panel by firm_id, or add cost fields to the register extract'),
 ('Import penetration by sector', 'import-competition scenarios need a domestic-share calibration', 'literature fringe shares; FR1/FR5 aggregate imports', 'not sector-specific',
  'customs HS × NACE concordance from the State Customs Committee'),
 ('Narrow product markets', 'activity groups understate concentration in product markets', 'FR10 product location shares; licence types', 'partial coverage',
  'agree priority markets (fuel, cement, telecom, pharmaceuticals, retail chains) for product-level data'),
 ('Licensing and inspections by NACE', 'barrier proxies mapped to groups by licence type', 'mapping of 24 licence types to 11 groups (Part 5)', 'several types are cross-sector',
  'request licence and inspection registers with NACE codes'),
 ('DVX micro-taxpayer rows', 'micro rows duplicate budget organisations (F8)', 'micro excluded from DVX concentration', 'economy-wide bound slightly overstated',
  'Tax Service to correct rows r123-r126')],
 columns=['gap', 'impact', 'alternative_used_now', 'bias_or_limitation_of_alternative', 'action_to_agree_with_Customer'])
GAPS.to_csv(OUT / 'FR12_data_gaps_and_alternatives.csv', index=False)
PRES = pd.DataFrame([
 ('V1', 'Competition dashboard by sector', 'KPI cards per activity group: entry, exit, churn, net entry, PCM proxy, HHI bounds, early-warning score', 'FR12_indicators_groups.csv, FR12_concentration_bounds.csv, FR12_early_warning.csv', 'annual'),
 ('V2', 'Entry/exit dynamics with forecast fan', 'history 2019-2025 and 2026-2030 under three FR1 scenarios with 5-95% bands; stock of active units', 'FR12_forecast_entry_exit.csv, FR12_fan_entry_exit.csv', 'annual'),
 ('V3', 'Region × sector heat map', 'entry and exit rates by region (2021-2025) and by NACE section; forecasts by region', 'FR12_indicators_regions.csv, FR12_indicators_sections.csv, FR12_forecast_entry_exit.csv (panel = region)', 'annual'),
 ('V4', 'Concentration bounds chart', 'range bars [lower, upper] for HHI and CR4 by group; projected bounds 2026-2030', 'FR12_concentration_bounds.csv, FR12_concentration_paths.csv', 'annual'),
 ('V5', 'Scenario simulator with assumptions panel', 'Cournot toolkit: entry, merger, cost/tax, import, SOE scenarios; Δprice, Δmarkup, Δoutput, ΔCS, ΔPS with elasticity ranges', 'FR12_scenario_*.csv', 'on demand'),
 ('V6', 'Early-warning list', 'flags per sector, composite score, watch list, insufficient-data markers', 'FR12_early_warning.csv', 'annual'),
 ('V7', 'Firm-level market structure view (Layer B)', 'HHI, CR4/CR8, entropy, Gini, share mobility, survival curves, Boone by NACE × region; SYNTHETIC watermark until the register arrives', 'FR12_SYNTHETIC_*.csv → FR12_FIRM_*.csv', 'annual')],
 columns=['view', 'name', 'content', 'feeding_csv', 'refresh'])
PRES.to_csv(OUT / 'FR12_presentation_spec.csv', index=False)
display(GAPS[['gap', 'alternative_used_now']]); display(PRES[['view', 'name', 'feeding_csv']])
print(f"source matrix: {len(MATRIX)} indicators ({', '.join(f'{k} {v}' for k, v in MATRIX.status.value_counts().items())}); "
      f'{len(GAPS)} gaps; {len(PRES)} MIIS views')
