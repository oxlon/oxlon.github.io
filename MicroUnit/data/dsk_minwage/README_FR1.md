# Minimum monthly wage (AZN) by effective date - FR1 v2.3.5

The Ministry workbook ('Sosial sektor', row 51) records in year t the minimum wage in force from 1 January of year t+1
(e.g. 400 AZN for 2024, effective 01.01.2025; 250 for 2018, while 2019 had 130 AZN in January–February, 180 from 1 March and 250 from 1 September: annual average 195.0).
FR1 (Part 3.6) builds the ANNUAL AVERAGE minimum wage (months in force / 12) from this file and asserts the one-year
shift against the workbook. 2017-2025 dates: DSK table 004_1; earlier dates inferred from the workbook shift.
Add a row when a new decree takes effect.

**Forecast path (2026-10-06): `minwage_path.json`** is the single source of the minimum-wage forecast for FR1 and FR3.
The first forecast year is the annual average of the decree schedule above (2026: the legal 400 AZN; both notebooks assert
it equals `legal_level_first_forecast_year_azn`); from the second forecast year the level grows at
`growth_pct_a_year_from_second_forecast_year` (Baseline 6%, Adverse 3%, Reform 9%). FR1 builds its exogenous `minwage`
from it (Part 13 `build_scenario`), FR3 its default path (`MW_LEGAL26`, `MW_GROWTH`); FR3's `mw_growth` lever overrides
only FR3.
