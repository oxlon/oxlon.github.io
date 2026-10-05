# %% [markdown]
# ### 8.1 Boşluqlar, alternativlər və Sifarişçi ilə razılaşdırılmalı tədbirlər
#
# FR10 göstəricisini məhdudlaşdıran hər boşluq, onun təsiri, FR10-un hələlik istifadə etdiyi proksi və həmin proksinin
# **meyli (sürüşməsi)**, habelə Nazirliklə razılaşdırılmalı tədbir (`output/FR10_data_gaps_and_alternatives.csv`).

# %%
GAPS = pd.DataFrame([
 ('Enterprise balance sheet and P&L panel (Tax Service, >= 5 years)', 'No firm ratios, distress scores, firm-level HHI, entry/exit by firm; Layer B runs on synthetic data only',
  'Section GOS margins (NA 013), branch GOS proxy, DVX declaration aggregates, concentration bound from the register', 'Aggregates hide dispersion; the GOS proxy omits other taxes and non-employee compensation (overstates margins)',
  'Sign the data-sharing agreement on the Part 17.1 schema; pseudonymised VÖEN; annual delivery after the declaration deadline'),
 ('Firm employment and wage bill (DSMF)', 'No firm productivity or TFP', 'DSK branch headcount and wages (006, 006_2), workbook industry sheets', 'Branch averages only', 'DSMF agreement keyed on the same pseudonymised VÖEN'),
 ('Fixed-asset renewal, disposal, depreciation rates by branch (F1)', 'No direct renewal indicator', 'Investment rate I/GO (DSK 019/010); CFC/VA by section (NA 013, 025)', 'Investment rate ignores stock age and is lumpy; section CFC hides branches',
  'Ask DSK to restore tables 017_2-017_7 or deliver them to MIIS'),
 ('Capital-yield index (old DSK 018_1)', 'No published capital efficiency', 'Capital productivity from perpetual inventory', 'Depends on depreciation rate (0.07) and the 2010 starting stock', 'As above'),
 ('Exports by branch / product (State Customs Committee)', 'Export orientation cannot enter the share system or the determinants panel', 'Industrial-park exports (workbook Park)', 'Covers parks and zones only, with no branch structure',
  'Monthly HS-level exports from DGK with an HS-NACE concordance'),
 ('Producer prices by NACE 2-digit branch', 'Real branch output relies on implicit deflators', 'Implicit output deflator = nominal output / chained volume (DSK 010, 009)', 'Composition effects inside a branch enter the deflator', 'DSK PPI by branch'),
 ('Energy costs by branch', 'No energy-intensity indicator', 'SME electricity and fuel costs (entrepreneurship 035, 037; 2023-2024)', 'SMEs only, two years', 'DSK / Azerenerji branch energy use'),
 ('Credit and NPLs by branch (CBAR)', 'No financing-condition driver by branch', 'FR1 industry credit at section level', 'Section level', 'CBAR loan register aggregates by NACE'),
 ('SME indicators as a time series (F11)', 'SME share cannot be projected', 'Held at 2024', 'Ignores any trend', 'DSK back-series of entrepreneurship tables from 2019'),
 ('Industrial output by region x branch', 'Regional forecasts cannot use branch composition', 'Regional totals (022) and products by place of production (018_1 2011-2025, 018_2 2019-2025)', 'Products cover physical units only, main products only', 'DSK region x NACE output table'),
 ('Profit-tax declarations by branch and size class (DVX)', 'Financial condition only economy-wide from declarations', 'Economy-wide DVX aggregates', 'Dominated by oil and large payers', 'DVX breakdown of r215-r232 by NACE and size'),
 ('Budget-organisation taxpayer rows (F8)', 'Budget organisations cannot be separated', 'None', '-', 'DVX to correct rows 127-129 of the workbook'),
 ('Workbook 2025 branch vintage (F2)', 'Workbook 2025 branch data unusable', 'DSK final 2025', 'None once DSK final is used', 'Refresh procedure: workbook rows overwritten from DSK when the final release appears'),
 ('Regional coverage break 2019 (F9)', 'Level break in regional shares', 'Step dummy; shares on the regional sum', 'Pre-2019 shares exclude household industry', 'DSK back-cast of regional output on the 2019+ coverage'),
 ('Published non-state share 2013-2016 inconsistent (F12)', 'Ownership history uncertain in 4 years', 'Composition identity', 'None in the forecast', 'Query DSK'),
 ('FR3 branch wage levels not anchored on 2025 (F13)', 'FR3 branch wage levels unusable for margins', "FR1 average-wage index on DSK 2025 branch wages", 'Common wage growth across branches', 'FR3 maintainers to anchor branch levels on 2025 actuals'),
], columns=['gap', 'impact', 'alternative_proxy', 'bias_of_proxy', 'action_to_agree_with_Customer'])
GAPS.index = [f'G{i+1:02d}' for i in range(len(GAPS))]
display(GAPS)

# %% [markdown]
# ### 8.2 Təqdimat spesifikasiyası: MİİS istifadəçi görünüşləri və onları qidalandıran fayllar
#
# Hər görünüş Hissə 18-də yazılan bir və ya bir neçə `output/FR10_*.csv` faylını oxuyur; sütunların düzülüşü sabitdir,
# belə ki, MİİS-in istifadəçi interfeysi onlara birbaşa bağlana bilər.

# %%
PRES = pd.DataFrame([
 ('V1 Branch scorecard', 'One card per branch: share of industry and manufacturing, real growth, labour productivity, GOS-proxy margin, investment rate, flags', 'KPI cards + sparkline', 'FR10_branch_scorecard.csv'),
 ('V2 Efficiency vs financial health', 'Labour-productivity growth against GOS-proxy margin, bubble = market share; quadrant labels', 'scatter / quadrant', 'FR10_quadrant.csv'),
 ('V3 Market-share dynamics', 'Branch shares 2005-2025 and 2026-2030 with 50/80/90% bands; HHI, CR4', 'stacked area; fan chart; KPI', 'FR10_branch_shares_history.csv, FR10_forecast_branches.csv, FR10_fan_charts.csv, FR10_concentration.csv'),
 ('V4 Region x activity', 'Regional shares of industrial output by year; non-state share; enterprises; entry/exit; forecast shares', 'map + heat map', 'FR10_regional_history.csv, FR10_forecast_regions.csv, FR10_regional_entry_exit.csv'),
 ('V5 Product view', 'Main products in physical units, 2020-2025 growth, branch link', 'table with sparklines', 'FR10_products.csv'),
 ('V6 Forecast with bands', 'Section and branch output (nominal, real), margins, non-state share under three scenarios with 5-95% bands', 'time series with fan', 'FR10_forecast_branches.csv, FR10_forecast_sections.csv, FR10_fan_charts.csv, FR10_scenario_summary.csv'),
 ('V7 Early-warning flags', 'Margin, market-share, renewal, stocks and productivity flags; watch list', 'flag table (traffic lights)', 'FR10_early_warning.csv'),
 ('V8 Financial condition', 'Section GOS margins, labour share, CFC; DVX declaration margins, losses, arrears; self-financing', 'time series; KPI cards', 'FR10_financial_sections.csv, FR10_dvx_declarations.csv'),
 ('V9 Key factors', 'Growth contributions by branch; determinants panel with honest inference', 'waterfall; coefficient table', 'FR10_growth_contributions.csv, FR10_determinants_panel.csv'),
 ('V10 Efficiency', 'TFP decomposition, capital productivity, wage-productivity gap, innovation intensity', 'decomposition bars', 'FR10_efficiency_branches.csv, FR10_tfp_sections.csv'),
 ('V11 Data catalogue', 'Indicator, source, table/row, years, status, integration route, alternative', 'searchable table', 'FR10_data_source_matrix.csv, FR10_data_gaps_and_alternatives.csv, FR10_data_integrity_findings.csv'),
 ('V12 Firm view (Layer B)', 'Firm scorecard, peer percentiles, distress zone, firm HHI by NACE x region, firm forecast — ACTIVE ONLY when the DVX/DSMF panel arrives', 'firm card; heat map', 'FR10_SYNTHETIC_*.csv now (pipeline test only, watermarked)'),
], columns=['view', 'content', 'form', 'feeding_files'])
display(PRES)
