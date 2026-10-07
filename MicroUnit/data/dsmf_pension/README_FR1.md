# Labour-pension indexation (actual decisions)

`pension_indexation.csv` records the indexation actually decided for each year (Presidential Order; DSMF / Ministry of
Labour and Social Protection announcement). FR1 (Part 13 `build_scenario`, latest-actual rule) uses the row for the first
forecast year: 2026 average pension = 2025 average pension x (1 + 9.3%) in every scenario. From 2027 the projection rule is
unchanged: CPI indexation plus any scenario real increase (`pension_real_g`). A real increase above the rule is financed by a
state-budget transfer to DSMF (v2.3.5); the decided 2026 indexation is the baseline policy, financed within the DSMF spending
relation (E3d), not by that transfer. Add a row when a new indexation is decided.
