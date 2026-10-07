> **Azərbaycan dilində:** [az/FR1_Metodologiya.md](az/FR1_Metodologiya.md)

# FR1 — Structural Econometric Methodology for Sector and Market Analysis and Five-Year Forecasting

**Module:** 15.5.2 Microeconomic analysis and forecasting
**Requirement:** FR1 — *deep analysis of economic sectors and markets; forecasting of sector-specific dynamics and trends*
**Model:** AZSEM-FR1 (Azerbaijan Structural Econometric Model, Forecast Round 1)
**Data source:** `Statistik data dinamika 05.06.2026 +.xlsx` (41 sheets, Ministry of Economy statistical dynamics database)
**Vintage:** annual actuals through 2025; cumulative monthly actuals through April 2026
**Forecast horizon:** 2026–2030
**Implementation:** `FR1.ipynb` (runs end to end, no errors; <!-- AUTO:v23_cells -->Parts 1–17 = 70 code cells<!-- /AUTO:v23_cells -->, Part 18 (v2) = registry, engine export, catalogue and self-test; kernel `miis-model`) and the scenario engine `microlib/engines/fr1.py`
**Outputs:** CSV files `FR1_*.csv` in `MicroUnit/output/`, including `FR1_forecast_full.csv` (now with a `pop` column,
thousand persons) and `FR1_fan_draws.csv` (500 baseline replications for FR3–FR5)

---

## Revision note (2026-09-27)

A methodological review found bugs, estimator errors and over-stated claims. All were fixed and the notebook re-executed; every
number below comes from the re-executed outputs.

| Area | What changed | Why |
|---|---|---|
| Long-run estimator | Every level relation is now estimated by **DOLS** (±1 leads/lags of Δx if df ≥ 10, else contemporaneous Δx, else OLS); the long-run coefficients are what the solver uses | DOLS had been defined but never used |
| Cointegration test | Residual-based Engle–Granger p-values from the MacKinnon response surface (`eg_coint_p`), not ADF p-values with Dickey–Fuller tables; not applied to inflation/deflator equations | The old p-values overstated cointegration (26 of 47 "p<0.05" before; **2 of 30** level relations now) |
| Inference | HAC with n/(n−k) scaling, t(n−k) p-values, restriction tests as HAC-F with the s.e. of the tested combination; non-rejections labelled "low power"; each level coefficient compared with the same equation in first differences | Small samples |
| Restrictions | Re-tested under DOLS: **unit trade elasticity, CRS in mining and α_K = factor share in manufacturing are rejected** and no longer imposed; unit non-oil tax buoyancy and unit public-investment elasticity remain (not rejected, low power). B1 unit pass-through is rejected (p = 0.017) | Previously imposed, or labelled imposed without being imposed (C3) |
| Wrong signs | Household income (E3) re-specified (final: non-oil GDP + pension bill, homogeneity imposed) instead of social spending (n = 7, wrong sign); non-oil GDP dropped from credit (G1, wrong sign); remaining wrong-signed insignificant terms dropped by rule | |
| Credit channel | Credit term omitted from investment: free estimate wrongly signed, panel value 0.134 rejected (HAC-F p = 0.028); a judgemental overlay is offered in the multipliers | Previously bolted on after estimation |
| Simultaneity | Instruments purged of the trend and of state investment (endogenous via F4); DWH test per equation; 2SLS used only if DWH rejects, all first-stage F ≥ 10 and Sargan does not reject — **no equation qualifies** | |
| Panels | Driscoll–Kraay with ⌊T^¼⌋ lags and t(T−1); wild cluster bootstrap (years, Webb weights); labour share recomputed on non-hydrocarbon branches grossed up for the 22% employer contribution (α_K 0.66 → 0.56); regional trade "cross-validation" withdrawn (imputation artefact) | |
| Bugs | Trend contributions ×100 in the growth decomposition; compounded oil-sector investment; the Reform TFP boost is now actually applied; structural table NaN fixed; population growth computed (0.483% p.a., 2021–25) instead of 0.4% hard-coded | |
| 2026 anchor | Jan–Apr growth mapped 1:1 (a robust bridge does not beat 1:1, HLN-DM p = 0.13); anchor increments decay with a one-year half-life | Held to 2030 before |
| Hold-out | Every coefficient, restriction decision, estimator switch and calibrated ratio re-made on ≤2020 data; state investment endogenous (F4); benchmarks RW from 2019 and 2020, constant growth 2010–19 and 2010–20; HLN-DM tests | Leakage and a flattering benchmark before |
| Uncertainty | Historical residual-path resampling of all 29 residuals (no estimated residual dynamics) with joint Brent/oil/gas paths, antithetic sign-preserving parameter draws, jump screen, centring on the baseline; growth fans from per-draw growth; draws exported | 16 equations, iid, no parameter/exogenous uncertainty before |


**Second review round (2026-09-28).** An independent re-review confirmed the estimator, panel, hold-out and bug fixes and asked
for further decisions, all applied: the Jan–Apr bridge (slope 0.52) was an artefact of the 2021 base effect — re-estimated
robustly on 2022–25 it does not beat 1:1 (HLN-DM p = 0.13), so the **1:1 mapping** is used; the **credit term is omitted** from
investment (the panel value 0.134 is rejected by the aggregate data, HAC-F p = 0.028) and credit easing on investment survives only
as a labelled judgemental overlay; **household income** re-specified on non-oil GDP + pension bill with homogeneity tested and
imposed (the wage-bill version failed homogeneity and under-predicted consumption by up to 23%); the **ex-post real rate** was
dropped from consumption (it turned inflation surprises into consumption booms); **transport** keeps hydrocarbon transit (significant
on pre-cut data, t = 5.2); **social-services deflator** unit CPI pass-through imposed (drift kept; the joint no-drift hypothesis is
rejected); wrong-signed insignificant long-run terms dropped by a rule re-applied in the hold-out; the scenario TFP boost is
restricted to supply-side sectors; the hold-out DM tests use h = 3; a units bug in how deflator changes were applied (log
changes applied as simple percentages) was fixed; and the fan charts now **replay historical residual paths** (no estimated
residual dynamics), with joint exogenous paths, antithetic sign-preserving parameter draws, jump screening and centring on the
baseline. These changes alter the point forecasts (Section 7.4).

---

<!-- v2-begin -->
## v2 (2026-10-05): equation registry, scenario engine, robustness

No equation, coefficient or forecast of the model was changed at this stage: the existing `FR1_*.csv` files are identical to
the previous ones (no-regression check: max. relative difference 2·10⁻¹³, kernel `miis-model`, Python 3.13), except two
corrected diagnostic files (see below). Part 18 was added to `FR1.ipynb`.

**Equation registry** — `output/FR1_equations.json`, 146 equations: 47 forecasting equations (46 behavioural/rate equations
and a descriptive trend for the output gap; the G6 GDP deflator is estimated but not used by the solver), 42 rejected /
candidate / sensitivity specifications, 20 2SLS (DWH rule) and 7 instrument-relevance regressions, 5 3SLS, 9 SUR share
equations, 14 panels (Driscoll–Kraay, t(T−1), wild cluster bootstrap p-values in `extra`) and the nowcast bridge. Every
OLS/DOLS/2SLS/panel equation was re-estimated independently with statsmodels and its coefficients are asserted equal to the
notebook's; for restricted forms the registry coefficients map exactly to the solver coefficients (CF) via `to_cf`.
Restriction tests were recomputed and checked against the notebook text. Re-estimation on data ≤2020 and the 2021–2025
dynamic hold-out (RMSE, Theil U against a random walk and constant growth, HLN-DM p) are in each forecasting equation's
`holdout` block (median U over 46 equations: 0.74 against a random walk, 1.20 against constant growth). Only one comparison
specification (E3 with social spending, ≤2020, n = 2 < k) is not registered — it is an exact fit.

**Robustness** (`output/FR1_robustness_summary.csv`; rule in the registry header): of 47 forecasting equations 15 are stable,
12 partly stable, 20 unstable. The unstable ones mostly carry 2013/2015/2020 Chow breaks (devaluation, pandemic) and some
recursive sign changes: B2, B3, C3, C4, C5, C7, C8, C9, C10, C12, D1, D3, D4, E1, E3, G1, G2, G3, G5 (agriculture deflator)
and the descriptive trend. This is consistent with the model not beating constant growth in the 2021–2025 hold-out (§6.2).

**Scenario engine** — `microlib/engines/fr1.py` (+ `_fr1_*.py`), state `output/engine/FR1_state.json`. The Part 11–16 solution
is ported line by line: damped Gauss–Seidel, identities, chain aggregation, base add-factors (2025 residuals) and the decay of
the 2026 anchor increments by 0.5, the policy level of state investment + the F4 response to the oil-revenue deviation, the TFP
add-on, the population path, the accounts (real, deflator, nominal), contributions and decomposition. Editable: 16 base
assumption paths (2026–2030, per scenario), 122 solver coefficients (value, SE, 95% interval from the registry), 10 levers
(mode `shock`/`reanchor`, anchoring and decay, ρ decay, add-factor recalibration, state-investment rule, credit overlay,
homogeneity; from v2.1 an 11th: sector allocation shares `alloc_shares`). The default `shock` mode is the notebook's Part 14
convention; the engine reproduces Part 14's five multiplier experiments to 10⁻¹⁴. The last cell asserts `selftest()`: for all
three scenarios in both modes `FR1_forecast_full.csv`, `FR1_accounts_*` and the contribution/decomposition tables of every
scenario are reproduced to a max. relative difference of ~10⁻¹⁴; one scenario takes ~0.06 s.

**Completeness** — `FR1_indicator_catalog.csv` and `FR1_forecast_tidy.csv`: 471 components × 3 scenarios × 2026–2030 (complete),
history from 1990, a baseline 5–95% band for 43 components. Contributions and decomposition now cover every scenario
(`FR1_gdp_growth_contributions_all.csv`, `FR1_sector_decomposition_all.csv`). New breakdowns: credit by sector
(`FR1_credit_by_sector.csv`; households G2, the other credit at 2023–25 average shares; from v2.1 at the actual 2025 shares —
see below) and real investment by sector (`FR1_investment_by_sector.csv`; the flow used by the capital identity; from v2.1 at
the 2025 shares). What is not forecast, with the reason, is in `FR1_not_forecast.csv`. Azerbaijani versions of the English
texts: `FR1_strings_az.csv` (240 rows).

<!-- AUTO:fr1v236_coefsens -->
**Coefficient sensitivity** (`FR1_coef_sensitivity.csv`, ±1 SE, 2030, baseline; current run): the largest effects come from the E3 household-income coefficients — non-oil GDP (household income −7.61/+22.52%, non-oil GDP −3.66/+10.94%, CPI −1.19/+3.35%) and the real wage bill (household income −2.10/+1.82%); then the D1 income elasticity (non-oil GDP −1.74/+2.56%); for CPI the G4 wage pass-through (+2.35/−2.50%); for employment the E4 participation trend (−0.63/+0.64%). The E3 effects are asymmetric: a ±1 SE change multiplies a log level inside an exponential and is amplified by the income–consumption loop.
<!-- /AUTO:fr1v236_coefsens -->

**Two errors corrected in v2 (only diagnostic / sensitivity outputs change).** (1) `FR1_iv_dwh.csv`: in E2 and G1 the included
exogenous variable (`ln_minwage`, `polrate`) was also counted as an excluded instrument (a duplicated column). Included exogenous
variables now instrument only themselves. The endogenous 2SLS coefficients do not change; corrected statistics: E2 first-stage
F (ln_cpi 5.5 → 9.8; ln_prod_non 43.3 → 76.9), Sargan p 0.044 → 0.011, DWH p 0.683 → 0.663; G1 F 37.7 → 67.1, Sargan p
0.043 → 0.013, DWH p 0.123 → 0.111. No DWH/2SLS decision changes — neither on the full sample nor in the ≤2020 hold-out model
(where D2 and G2 remain 2SLS). (2) The Part 13 ρ sensitivity (`FR1_addfactor_sensitivity.csv`) reused the oil-revenue
reference path left over from the main forecast; it is now computed with its own reference path (new values in §7.4).
(3) Not changed: the 2026 anchoring loop is capped at 20 iterations and reaches its targets to at most 0.12% (tourism; 0.07%
in the Adverse and 0.16% in the Reform scenario) — inside the 0.5% tolerance; the engine's `anchor_maxit` lever can raise it.
<!-- v2-end -->

<!-- v2.1-begin -->
## v2.1 (2026-10-05): sector allocations anchored on the last actual year

**Defect.** An audit found that 2026 real investment by sector (`FR1_investment_by_sector.csv`, ids `fr1:inv:*`) jumped against
the 2025 actual — trade +58%, manufacturing +49%, tourism −25%, electricity −23%, water −22%, ICT +22% — while total real
investment is flat (−0.1%). Cause: 2023–25 *average* shares of total real investment were applied from 2026 to a total whose
2025 composition differs from the average. Credit by sector (`FR1_credit_by_sector.csv`) had the same problem: energy +25.2%
(Reform +28.2%) while business credit grew 3.7%.

**Rule.** As everywhere in the project (FR3 branch wages, FR12 section allocation, the add-factor convention) the allocation is
anchored on the last actual year: each sector's **2025 share is held through 2030** — of total real investment (Part 11.2,
`calibrate`) and of business (non-household) credit (Part 9.7, `CRED_SHARE_ANCH`; "other" remains the exact remainder). 2026
sector values now move exactly with the total: investment −0.1% in every sector (Adverse −3.8%, Reform +2.2%); credit +3.7%
(Adverse −6.0%, Reform +6.3%). No convergence to the averages is imposed: the notebook's reason for averaging is smoothing, not a
long-run share, and the hold-out below gives no clear case for one. The sector history (investment 2000–2025, credit 2006–2025,
`is_forecast = False`) was already in `FR1_forecast_tidy.csv`; it is now continuous with 2026.

**Consequence for the model.** The investment shares are the flows of the capital-stock identity
K<sub>s,t</sub> = (1−δ<sub>s</sub>)K<sub>s,t−1</sub> + share<sub>s</sub>·I<sub>t</sub>, so the same anchored shares are used there
(published sector investment and published capital stocks stay consistent). K<sub>man</sub> (C3) and K<sub>ict</sub> (C10)
matter: with the 2025 shares (manufacturing 3.0% vs 4.5% average, ICT 1.8% vs 2.1%) both stocks are ~9.6% lower in 2030, and
Baseline 2030 value added is lower — manufacturing −3.2%, ICT −7.6%, non-oil GDP −0.93%, real GDP −0.78% (2026 is unchanged:
it is anchored on January–April data). Average growth 2026–30 (v2 → v2.1, both 2026-10-05; the current run is in §7): real GDP 2.56 → **2.40%** (Adverse 1.51 → 1.37, Reform
3.50 → 3.32); non-oil 4.18 → **3.99%** (3.07 → 2.90, 5.26 → 5.03). All run-dependent figures in §6–§9 and in the v2 note
above quoted the v2.1 run (§6–§9 now quote v2.2) (refreshed by script from the output CSVs and the executed notebook). FR3, FR4 and FR5 (which read
`FR1_forecast_full.csv` and `FR1_fan_draws.csv`) were re-run; FR10 and FR12 read the same files.

**Hold-out (same rule at the 2020 cut).** Median Theil U vs RW2020 / constant growth 2010–19, 14 variables:

| Share rule in the capital identity | median U RW2020 | median U CG 2010–19 | real GDP U RW2020 | manufacturing U | ICT U |
|---|---|---|---|---|---|
| 3-year average (pre-v2.1) | 0.578 | 1.024 | 0.595 | 0.677 | 0.282 |
| **cut-year share held (v2.1)** | 0.585 | 1.019 | 0.624 | 0.577 | 0.820 |
| linear convergence to the average over 4 years | 0.594 | 1.026 | 0.613 | 0.611 | 0.596 |
| convergence at the anchor decay 0.5 | 0.580 | 1.026 | 0.609 | 0.625 | 0.516 |

The rules are close except for ICT, whose 2020 investment share was a trough (1.1% vs 2.2% average). The two convergent rules
were not adopted: one is no better on the medians, the other only moves the jump to 2027 (trade +30%).

**Lever and engine.** The 3-year averages are kept (`CAL['inv_share_avg3']`, `CRED_SHARE_FIX`) and printed; engine lever
`alloc_shares='avg3'` restores the pre-v2.1 rule (with `mode='reanchor'` it reproduces the pre-v2.1 forecast to 8·10⁻¹⁶).
`selftest()` now also reproduces `FR1_investment_by_sector.csv` and `FR1_credit_by_sector.csv` (max. rel. diff. 2·10⁻¹⁶).

**Other allocation outputs checked.** `FR1_gdp_growth_contributions_all.csv` and `FR1_sector_decomposition_all.csv` are growth
rates (pp), not share allocations: contributions use the 2025 actual nominal weights; their 2026 values come from the sector
equations and the January–April 2026 anchor (construction −19% real → −1.24 pp), so nothing was changed. Consumer-market shares
show no jump > 25%. The only other 2025→2026 level jump > 25% is the budget balance (difference of two large aggregates).
FR1's 14 Driscoll–Kraay panels already use t(T−1) for both p-values and intervals (checked).
<!-- v2.1-end -->

<!-- AUTO:v23_note -->
## v2.3 (2026-10-05): final FR1 clean-up — fixed add-factor decay, import price term, wage bill in income, fiscal ordering

Four specification questions, each estimated on data ≤ 2020 by the model's own builders and tested in the untouched dynamic
2021–2025 hold-out against the v2.2 specification (new notebook Part 11.7, `FR1_v23_candidates.csv`); the scenario consequences
and the decisions are in Part 14.1 (`FR1_v23_forecast_checks.csv`, `FR1_v23_fiscal_diagnosis.csv`, `FR1_v23_decisions.csv`).
Rule: correct (or neutral) signs on both samples, Theil U of the key variable at most 10% above the v2.2 specification, for E3 a
coherent wage elasticity, and for the fiscal candidates the ordering Adverse < Baseline < Reform of the 2030 budget balance.
Rejected candidates are registered with `used_in_forecast = false`.

| Item | Decision | Evidence |
|---|---|---|
| 1. Add-factor decay sensitivity | **Changed.** Until v2.2 the lever `base_addf_decay` decayed the base add-factors at each equation's *estimated* residual autocorrelation ρ̂ — an estimated residual-AR process, excluded by the client's constraints. Now a fixed, non-estimated half-life: lever `addf_halflife` (default 1 year, factor 0.50 a year — the rule of the January–April anchor increments); ρ̂ is no longer estimated anywhere in the forecast path (DW and BG remain as diagnostic tests) | The forecast (constant add-factors) is unchanged by this item. `FR1_addfactor_sensitivity.csv`, average growth 2026–30 with the decay: real GDP 2.31 / 1.12 / 3.33% (Baseline / Adverse / Reform; constant add-factors 2.57%), non-oil 3.51 / 2.35 / 4.62% (3.76%); with ρ̂ (v2.2 run) real GDP 2.42%, non-oil 3.67% |
| 2. D4 non-oil imports: relative price ln(p_gdp/fx), coefficient −0.245 | **Re-parametrised (adopted).** Real imports are USD imports × exchange rate / GDP deflator (Part 3), so ln(p_gdp/fx) enters the dependent variable with −1 by construction. Estimated in import-volume terms (constant USD prices), the same fit gives the volume elasticity **c = +0.755** (p = 0.0001; ≤ 2020: +0.278) — correctly signed: a real appreciation raises import volumes. The solver keeps c − 1 for real imports at GDP prices, so forecasts and hold-out are identical. Dropping the term (= bounding it at 0, which binds) is rejected | Imports U 0.84 / 0.56 (identical to v2.2). Without the term: imports 0.95 / 0.63 (+13%, material), non-oil revenue U 0.87 vs 0.44, budget balance 0.99 vs 0.61. In first differences the volume elasticity is +0.08 [−0.26, +0.42], so the long-run value lies outside that interval — as for the v2.2 form (reported) |
| 3. E3 household income: + real wage bill | **Adopted.** ln(income / pension bill) on ln(non-oil GDP / pension bill) and ln(wage bill / pension bill), homogeneity imposed: elasticities non-oil GDP 0.603, **real wage bill 0.377** (the 2025 wage share of household income is 0.425), pension bill 0.021; ≤ 2020: 0.690, 0.102, 0.208. Homogeneity is not rejected on the selection sample (p = 0.16) but is on the full sample (p = 0.001), where the free form has a wrongly signed non-oil GDP elasticity (−1.34) — so the test-and-impose variant is rejected. Wage elasticity coherent (first differences 0.20 [−0.20, +0.59]) | Hold-out real disposable income U 1.26 / 1.00 vs 1.24 / 0.98 (+2.3%, below 10%); consumption U 0.08 vs 0.14. **Minimum wage +10%** (Baseline 2030, shock convention): real disposable income −0.31% → **+1.19%**, consumption −0.35% → +1.31%, non-oil GDP −0.21% → +0.51% (wage +3.59%, CPI +1.16%; income-legs lever +1.03%) |
| 4. Fiscal block: Adverse ends with the best budget balance | **Kept — no candidate passes.** Diagnosis, Adverse vs Baseline 2030: revenue −9.2 bn AZN (oil −3.9, non-oil −5.3), spending −10.7 bn (current −5.7, capital −5.0): **1.17 AZN of spending is cut per AZN of revenue lost**. Two links do it: F3 (current spending on total real revenue, elasticity 0.99, 95% CI [0.52, 1.46]) and the scenarios' state-investment paths (Adverse −4% a year: real state investment −23.4% vs real oil revenue −15.9%; F4 unit elasticity, free estimate 0.90 [0.22, 1.58]). With the Baseline state-investment level Adverse would end at −1.85% of GDP | Every structural fix that restores the ordering loses heavily on the hold-out balance (U 0.61 in v2.2, RMSE 1.1 pp of GDP) — table below. The ordering is therefore a property of the estimated fiscal reaction (spending follows revenue, capital spending follows oil revenue), not a coding error; it is disclosed rather than tuned away |

| Fiscal candidate (in the v2.2 model, as in the hold-out) | 2030 balance, % of GDP (Baseline / Adverse / Reform) | Adverse < Baseline < Reform | Hold-out U of the balance (change) | Decision |
|---|---|---|---|---|
| F3: non-oil and oil revenue separately | +1.84 / +3.06 / +1.33 | no | 0.92 (+50%) | rejected |
| F3: non-oil revenue only (oil revenue saved) | −0.13 / −0.76 / +0.67 | yes | 1.43 (+134%) | rejected |
| F3: revenue elasticity at its 95% CI lower bound | +0.43 / +0.62 / +0.64 | no | 1.41 (+131%) | rejected |
| F4: scenario capital-spending rule (Baseline policy level + F4 response), unit elasticity | +0.43 / +0.67 / +0.46 | no | 0.61 (+0%) | rejected |
| F4: scenario capital-spending rule, oil-revenue elasticity at its 95% CI lower bound | +0.43 / −0.83 / +1.43 | yes | 0.75 (+23%) | rejected |

**Effect on the forecast (Baseline 2030, vs the v2.2 run)** — all from the E3 wage-bill term (items 1 and 2 leave the forecast
unchanged): real GDP −1.59%, non-oil GDP −2.10%, nominal GDP +1.68%, CPI +4.25%, real disposable income
−4.26%, consumption −4.63%, non-oil imports −5.60%: the real wage bill grows more slowly than non-oil GDP in the forecast. Average growth
2026–30: real GDP **2.57%** (v2.2 2.90; Adverse 1.32, Reform 3.62), non-oil **3.76%** (4.20; 2.54, 4.91). Budget balance
2030: Baseline +0.01, Adverse +0.98, Reform −0.39% of GDP (v2.2 +0.22 / +1.10 / −0.12). Median hold-out U of the 14 variables
of §6.2: 0.591 vs RW (0.592 in v2.2), 1.036 vs constant growth (1.035).

**Registry, engine, documentation.** `FR1_equations.json`: 174 equations (47 used in the forecast; 157 in v2.2), new: 8
v2.3 specifications (the replaced v2.2 forms of D4 and E3 and the rejected candidates), each with its hold-out comparison and
decision row. Engine: lever `addf_halflife`; the E3 homogeneity tie now has three members (pension-bill elasticity = 1 − non-oil
GDP − wage bill), so a changed coefficient keeps the restriction; self-test passes for every scenario in both modes. The
run-dependent figures that no CSV holds (solver iterations §7.1, the January–April anchor §7.2, the fan diagnostics §7.5, the
v2.2 comparison figures) are exported to `FR1_doc_figures.json` (Part 18.17) and rendered here by `microlib.docrefresh`.
FR3, FR4 and FR5 were re-run on the v2.3 forecast. §6–§9 quote the v2.3 run.

**v2.3.1 fix (2026-10-06): budget-balance multipliers.** `FR1_multipliers.csv` reported the budget balance as a % deviation
from a Baseline balance that crosses zero (−97 mln AZN in 2028), so the responses exploded and changed sign (state
investment +1 bn AZN: −306, −849, +2 248, −3 359, −1 569 "%" in 2026–30; +52 130% in 2028 in v2.2). The model itself was not wrong: every shocked solve
converged (largest residual 1e−10) and the responses in money are smooth. The balance column is now the difference in
mln AZN at current prices (inflation stays in pp, the other columns in %): state investment +1 bn AZN −1980, −2139, −2352, −2577, −2812; Brent
+10 USD/bbl +183, +124, +62, +41, +14; external demand +10% +155, +183, +220, +262, +309. The real and price responses and the forecast are unchanged. The
notebook now asserts that every shocked run converged and that balance_n, rgdpnon and infl keep one sign from year 2 on.

**v2.3.2 fix (2026-10-06): public debt.** `debt_azn` converted the workbook's total public debt at the exchange rate, but that
row is on three bases (§2.3, item 5): 2025 was 38 451 mln AZN instead of **25 987.5 mln AZN** (external
4 813.5 mln USD × 1.70 + domestic 17 804.5 mln AZN; 20.1% of GDP), and 2010–2020 were mis-scaled by the exchange
rate. Public debt is now external × end-year rate + domestic in every year — the Ministry of Finance concept (state-guaranteed
debt is not included and not in the workbook); `fr1:debt_azn` is labelled accordingly. The calibrated debt-service rate (2023–25
average of debt service / debt) and the debt identity use the corrected stock: 2026 debt service 1 491 mln AZN (was
1 871); 2030 public debt 12.3 / 12.9 / 11.5% of GDP (Baseline / Adverse / Reform; was
20.5 / 22.2 / 18.9); budget balance 2030 +0.01 / +0.98 / −0.39% (was +0.09 / +0.99 / −0.26).

**v2.3.3 (2026-10-06): exchange-rate pass-through.** G4 (exchange rate + wages) had a pass-through of 0.06: a +16.5% devaluation
raised CPI +1.14 pp in year 1 and +0.02 pp in year 2, and non-oil GDP *rose* (+0.44% by 2030), against ≈0.29 in 2015–17.
Candidates (Part 11.7; lags of regressors only, no lagged inflation), inflation hold-out U vs RW (v2.3 form 1.30): + exchange-rate change of the previous year 1.37; manat import-price inflation (USD import prices + exchange rate) 0.73; manat import-price inflation, current + previous year 0.51; pass-through in the post-2015 floating regime, current + previous year 1.39; manat import prices with the DSK index spliced for 2021-25, current + previous year 0.88.
v2.3.3 adopted manat import-price inflation (macro-module USD import prices + exchange rate, current + previous year; U
0.50): devaluation CPI +3.63 / +0.99 pp, but Baseline CPI inflation 2027–30 of 7.3%. Why non-oil GDP rose:
with almost no pass-through real incomes barely fell, while manat oil revenue raises current spending (F3) and state investment
(F4); the real-income channel (real wage bill in E3, CPI-indexed pensions) was present but too weak.

**v2.3.4 (2026-10-06): import-price data check — G4 = exchange rate + exchange rate (t−1) + wages.** The v2.3.3 residuals of
2023–25 (−0.5, +3.2, +3.4 pp) came from the import-price series: USD import-price inflation 2021–25 is +33.5, +15.3, −12.7, −6.3, −8.9% in the
macro-module series but +20.5, +21.9, +15.8, +19.4, +32.1% in the workbook's DSK import-price index (`Monetar sektoru` row 98, 2021–25 only) —
opposite signs in 3 of 5 years. (A) The DSK index spliced in for 2021–25 (macro-module growth rates to 2020, DSK
2021–25): hold-out U 0.88 (macro form 0.51; outside the 10% rule) and 2023–25 residuals −5.2, −1.9, −3.9 pp — not removed,
reversed. The two sources cannot be reconciled, so (B) **FX + FX(t−1)** is adopted (U 1.37, +5% vs the v2.3 form,
within the rule; 2023–25 residuals −2.9, +0.8, +0.8 pp; `FR1_v234_g4_check.csv`). The import-price forms stay registered
(`used_in_forecast = false`). Devaluation +16.5% now: CPI **+0.82 pp in year 1, +2.20 pp in year 2** (level +2.9% by
2030), non-oil GDP +0.26% (2026) / −0.07% (2030), real disposable income −0.68%, public debt −0.02 pp of GDP; without the
F4 response non-oil GDP −0.60%.

**2026 CPI anchor.** 2026 inflation is anchored on the latest monthly CPI, as the real sectors are on January–April:
dsk_cpi.csv gives 5.7% y/y in month 8 of 2026; the remaining months repeat last year's month-on-month changes (1:1;
RMSE 3.6 pp on 2021–25), so December 2026 = 5.7%. As for the January–April real-sector anchors, this partial-year
information enters as an **increment**: G4's base add-factor stays its 2025 residual (+0.77 pp, held constant), and the 2026 increment
(+2.69 pp = nowcast − model) applies fully in 2026 and decays with the one-year half-life from 2027 (×0.5, ×0.25, …). It refreshes when a
new monthly file arrives in `data/dsk_cpi/` or a RiskUnit DSK vintage. Baseline CPI inflation 2026–30: 5.7, 6.1, 5.2, 4.9, 4.6%
(2027–30 average 5.2%; Adverse 4.4, Reform 6.0).

**2026 public-debt anchor (v2.3.4).** The latest Ministry of Finance stock, 23 830.6 mln AZN on 2026-07-01 (−8.3% vs
end-2025 25 987.5; debt_parsed.json), anchors 2026 as CPI and the real sectors are anchored: end-2026 debt = the observed stock − the
model's 2026 budget balance × the remaining 6/12 of the year = **23 387.4 mln AZN** (17.3% of GDP). The identity alone (debt
− balance) would give 25 101.0; the gap, −1714 mln AZN, is the 2026 stock-flow adjustment implied in the Baseline (repayments financed
below the line, e.g. from SOFAZ). The formula is applied inside the solver in every run (scenarios, shocks, engine), so only the
second-half balance moves end-2026 debt (Δdebt = −0.50 × Δbalance): Adverse 23 518.5,
Reform 23 479.8 mln AZN; from 2027 the identity applies. It refreshes when a
newer bulletin arrives in `data/minfin_debt/` or a RiskUnit MinFin vintage (`FR1_debt_nowcast.csv`). Public debt 2030: 12.3 /
12.9 / 11.5% of GDP (Baseline / Adverse / Reform).

**v2.3.5 (2026-10-06): pension cost, employment, minimum wage.** (1) A real pension increase improved the budget balance: pensions
are paid by DSMF, outside the state budget, and FR1 had no financing identity, so only the revenue gain (consumption → VAT) showed.
A real increase above CPI indexation (policy input `pension_real_g`) is now financed by a state-budget transfer to DSMF (current
spending) = DSMF pension spending (7 783 mln AZN in 2025, bridged from 2024) × (1 − 1/cumulative real increase); actual pension
rises in history and the hold-out are inside the observed spending (off there). +10% real pensions from 2026: balance
−825, −902, −1001, −1106, −1216 mln AZN in 2026–30 (before: +30, +36, +43, +50, +58); spending +912, +998, +1109, +1227, +1352, revenue +87, +97, +108, +121, +136. (2) Employment:
FR1's E1 relates the employment RATE to per-capita non-oil GDP with an elasticity of 0.034 (p = 0.008; measured
unemployment is very stable), so +1 bn AZN of state investment raises non-oil GDP +1.20% but employment only
+0.040% by 2030 — the estimated elasticity, not re-specified. FR4's sector equations give a higher elasticity for hired (formal) employees than for total employment: sector share 0.174 vs 0.108, market services 1.63 vs 0.70; a policy unit should read FR1's employment as total (LFS) employment, dominated by self-employment and agriculture, and take formal-job effects from FR4. (3) The workbook's minimum wage (`Sosial sektor` row 51)
shows in year t the level in force from 1 January t+1 (2024: 400, effective 01.01.2025). FR1 now uses the annual average of the level in force
(`data/dsk_minwage/`, DSK 004_1): 2019 203.3 (v2.3.5; 195.0 in v2.3.6), 2024 345, 2025 400. E2
re-estimated: minimum-wage elasticity 0.186 (p = 0.14) → **0.384** (p = 0.000), productivity 0.82 → 0.49,
CPI 0.62 → 0.39; wage hold-out U 0.52 → 0.58 (a data correction, not a specification choice). Minimum wage +10%
(2030): wage +2.64 → +4.67%, real disposable income +0.91 → +1.59%, CPI
+0.85 → +1.50%. Baseline CPI inflation 2026–30: 5.7, 5.2, 4.5, 4.3, 4.0% (before: 5.7, 5.9, 5.1, 4.9, 4.5). (v2.3.5 run; corrected in v2.3.6 below.)

**v2.3.6 (2026-10-06): minimum wage — month weighting and the public-pay channel.** (1) The annual minimum wage is the
month-weighted level in force from the DSK 004_1 schedule: 2019 = (2×130 + 6×180 + 4×250)/12 = 195.0 (v2.3.5: 203.3); FR3 uses the
same series and the legal 2026 level (400 AZN, in force since 01.01.2025), its growth lever applying from 2027. (2) Every
minimum-wage increase (2019, 2022, 2023) coincided with a public-pay reform. The minimum-wage elasticity is +0.598 for STATE wages
(p = 0.000) and -0.032 for NON-STATE wages (p = 0.69), so a single average-wage elasticity attributes public pay to
every employee. Candidates (Part 11.7, wage hold-out U vs RW, v2.3.5 form 0.55): + public-pay reform steps (2019, 2022, 2023): U 0.55 (wrong sign — rejected); + cumulative public-pay reform index: U 0.25 (wrong sign — rejected); minimum-wage elasticity restricted to the state / non-state channels: U 0.49. **Adopted: the minimum-wage elasticity
restricted to the state / non-state channels** (minimum-wage elasticity = state wage-bill share 0.483 x state +0.598 + non-state -0.032 x 0.517 = 0.272): **0.384 → 0.272**; productivity and CPI are
re-estimated (0.86, 0.44). Minimum wage +20% (Baseline 2030): average wage +9.11 → **+6.98%**, real GDP +1.13 →
+0.85%, real disposable income +3.07 → +2.30%, CPI +2.86 → +2.21% (inflation +3.04 → +2.36 pp in 2026).
(3) G4's wage pass-through is 0.347 (s.e. 0.176, p = 0.06; 95% interval about -0.02 to +0.72): it treats public-pay
rises like private unit labour costs, so the minimum wage → wage → CPI response remains on the strong side (the PolicyUnit 2019
validation: observed CPI response far smaller); a non-state-wage cost term needs a non-state wage block and is not adopted here.
Baseline CPI inflation 2026–30: 5.7, 6.1, 5.2, 4.9, 4.6% (v2.3.5: 5.7, 5.2, 4.5, 4.3, 4.0).
<!-- /AUTO:v23_note -->

<!-- AUTO:v22_note -->
## v2.2 (2026-10-05): what was taken from the Ministry's macro module (15.5.1)

The macro module (`18august/model`, read-only) covers FR1–FR5 from the macro side. Its data and official plan figures were
reviewed for FR1; every candidate was **re-estimated in FR1's framework** (same sample conventions, small-sample HAC, coherence
rule), selected on data ≤ 2020 and tested in the **untouched dynamic 2021–2025 hold-out** of §6.2, against the pre-v2.2 model
(new notebook Part 11.6, `FR1_v22_macro_candidates.csv`). Data copies with source path and MD5: `data/macro_module/README_FR1.md`.
Nothing from the macro module's own forecasting (AR(1)/five-year-average profiles, CPI/wage/unemployment ensembles, ECM/AR(6)
specifications, Okun equation, its 2026 GDP path that ignores the January–April 2026 actuals) is used.

| Item | Decision | Hold-out evidence (Theil U vs RW 2020 / vs constant growth 2010–19; RMSE) |
|---|---|---|
| 1. Oil and gas output | **Adopted** (assumption): Baseline growth 2027–30 = Ministry plan (`8_vereq_original.xlsx`, 2.4.1.4) on the 2026 level from the January–March outturn; Adverse = pre-v2.2 Baseline oil decline (−4.2…−3.0%), gas plan − 1 pp; Reform = plan + the pre-v2.2 Reform gaps | Plan, not an estimate. The plan over-stated 2025 oil output (28.45 vs 27.68 mt, +2.8%; gas −1.0%). Baseline oil 2030: 26.0 mt (pre-v2.2 22.8) |
| 2. Household income by source (wage bill + DSMF transfers + other income, Δln legs) | **Rejected** for the forecast; engine lever `income_block = legs` | In sample the legs fit better (one-step RMSE of real income growth ≤ 2020: 3.5 vs 5.0 pp; elasticities 0.83 wage bill, 0.52 DSMF, 1.24 other income — as in the macro module). Dynamic hold-out, real disposable income: U 1.79 / 1.42, RMSE 11.6% vs **1.27 / 1.01, 8.3%**; consumption 0.28 vs 0.13. The legs are nominal: the pre-cut model under-predicts the 2025 price level by 31%, and the under-indexed nominal legs turn that into too much real income. Deflated by consumer prices: 1.52 / 1.21 (rejected). Nominal disposable income is better with the legs (U 0.53 vs 0.65) |
| 3. Mining deflator on the export-value-weighted oil+gas export price index + exchange rate | **Adopted** (the macro module's form, no CPI term) | Mining deflator U **0.13 / 0.16** (RMSE 6.8%) vs 0.52 / 0.63 (27.3%); nominal GDP 0.48 / 0.75 vs 0.64 / 1.00; GDP deflator 0.36 vs 0.62. Side effects: real GDP 0.72 / 1.12 vs 0.62 / 0.96 (chain weights), imports 0.83 vs 0.68 (the wrong-signed relative price in D4). The CPI-augmented variant (smallest pre-cut s.e.) is worse (0.63) and rejected. New fit: 2.5 + 1.02 Δln XPI + 0.51 Δln FX, adj. R² 0.80; robustness *qeyri-stabil* (Chow at the 2016 mid-point, p = 0.005) |
| 4. State Investment Programme 2026 | **Adopted**: 2 700 mln AZN (own workbook, `DİP 2016-2026`, planned; 2025 actual 2 305; the macro module cites the same cell) | Assumption. Its 2025 share of real state investment (20.4%) is replaced in 2026 by the programme at the model's 2026 investment deflator (fixed point); 2026 real state investment +3.9% (pre-v2.2 +1.5%). Published as `fr1:exp_pubinv_n` (= 2 700 in 2026 in every scenario) |
| 5. Fiscal closure: non-oil balance held at its cut-year ratio to non-oil GDP | **Rejected**; engine lever `fiscal_rule = nobd`; the ratio is published (`fr1:nobd_pct`) | Total spending improves (U 0.32 vs 0.51) but the budget balance, the purpose of the rule, is much worse: RMSE 5.2 vs 1.1 pp of GDP (U 2.80 vs 0.61), because oil-revenue errors pass 1:1 into the balance. Under F3 Adverse keeps the best 2030 balance (+1.1% of GDP; Baseline +0.2, Reform −0.1): spending follows revenue and Adverse cuts state investment 4% a year. With the lever, 2030 balances are −13.4 / −15.2 / −12.0 bn AZN (Adverse worst) |
| 6. Imports on absorption + REER | **Rejected** | REER wrongly signed in both samples (≤ 2020 −1.06, p = 0.02; full −0.32, p = 0.12); imports U 1.31 / 0.87 vs 0.68 / 0.45. D4 unchanged |
| 7. Sector deflators on sector price drivers | **Skipped** | The drivers (agricultural producer prices, transport and communication tariffs, construction deflator) have no exogenous 2026–30 paths: the macro module projects them with AR/average profiles (`pdrv_*`), and several exist only from 2021 |

**Effect on the forecast (Baseline, vs v2.1).** 2026 is unchanged in real terms (anchored on January–April); the changes come
from 2027: real GDP 2030 +2.5% (oil-gas GDP +11.8%), non-oil GDP +1.0%, nominal GDP +4.4% (mining deflator), CPI 2030 +0.3%,
real disposable income +0.9%. Average growth 2026–30: real GDP **2.90%** (v2.1 2.40; Adverse 1.76, Reform 3.85), non-oil **4.20%**
(3.99; 3.09, 5.23). Scenario ordering of activity is unchanged (Adverse < Baseline < Reform). Budget balance 2030 +0.22% of GDP
(Baseline), the 2026 balance is lower (+636 vs +948 mln AZN: the programme). Median hold-out U of the 14 variables of §6.2: 0.59
vs RW (0.58 before), 1.04 vs constant growth (1.02); median RMSE 13.2% (14.6%).

**Registry and engine.** `FR1_equations.json`: 157 equations (47 used in the forecast): new — the four income legs
(E3a–E3d, estimated and registered, `used_in_forecast = false`, with their hold-out comparison), their CPI-deflated variants, the
pre-v2.2 and CPI-augmented mining deflators, D4 with absorption + REER; G5_defl_min replaced. Engine (`microlib/engines/fr1.py`,
`_fr1_*.py`): new inputs `sip_n` (programme, nominal) and `dsmf_add_g`; levers `income_block`, `fiscal_rule`; new series
`fr1:gdpnon_n`, `hhdisp_n`, `nobd_pct`, `exp_pubinv_n`, `gas_exp_price`, `xsh_oil`, `dln_xpi` (478 catalogue components).
With `income_block = legs` a 10% higher minimum wage raises real disposable income by ~1.0% by 2030; in the forecast model
(E3) it does not (−0.31%, via prices). Self-test passes for all scenarios in both modes; FR3, FR4 and FR5 were re-run.
This note records the v2.2 stage (its forecast figures are those of the v2.2 run, as are the v2 and v2.1 notes' of theirs);
§6–§9 quote the current (v2.3) run.
<!-- /AUTO:v22_note -->


## 0. Requirement traceability

FR1 requires *"structural, dynamic and multivariate econometric models prepared for each of these sectors, analysed both
separately and jointly, and forecast"*, with the sector partition following the State Statistics Committee (DSK)
classification. AZSEM-FR1 implements that partition exactly:

| FR1 sector (Azerbaijani) | Code | Treatment in the model |
|---|---|---|
| Sənaye — mədənçıxarma | `min` | Volume-determined; constant returns tested and rejected |
| Sənaye — emal sənayesi | `man` | Capacity + construction + export demand (α_K = factor share tested, rejected) |
| Sənaye — elektrik enerjisi, qaz və buxar | `elc` | Derived demand from non-oil activity |
| Sənaye — su təchizatı, tullantıların emalı | `wat` | Per-capita utility demand |
| *Qeyri-neft-qaz sənayesi* | — | Aggregation of the non-hydrocarbon industrial components |
| Kənd, meşə və balıqçılıq təsərrüfatları | `agr` | Trend (capital term dropped: wrong-signed, insignificant; a 2015 trend break tested on pre-cut data and not adopted) |
| Tikinti | `con` | Public and private investment |
| Ticarət; nəqliyyat vasitələrinin təmiri | `trd` | Consumption (unit elasticity tested and rejected; long-run 0.96) |
| Nəqliyyat və anbar təsərrüfatı | `tra` | Hydrocarbon transit volume + trend (non-oil GDP dropped: wrong-signed, insignificant) |
| Turistlərin yerləşdirilməsi və ictimai iaşə | `tou` | Per-capita disposable income + trend |
| İnformasiya və rabitə | `ict` | ICT capital deepening per capita + trend |
| Sosial və digər xidmətlər | `oth` | Per-capita disposable income + trend; deflator with unit CPI pass-through |
| Məhsula və idxala xalis vergilər | `nettax` | Consumption + imports (links to the fiscal block) |

**"Separately"** is delivered by one structural equation per sector, each with its own drivers, elasticities, restriction tests
and residual diagnostics. **"Jointly"** is delivered by solving those equations as one **simultaneous system** closed by
national-accounts, fiscal, monetary and balance-of-payments identities, so every sector's forecast is conditioned on every
other's, and by the multiplier analysis in Part 14 of the notebook, which traces how a shock to any one driver propagates
across all twelve components.

---

## 1. Methodological stance

### 1.1 The exclusion, and what it does and does not cover

No autoregressive, ARIMA, ARCH or GARCH component appears anywhere. Specifically: **no behavioural equation contains a lagged
dependent variable**, no variable is forecast from its own history, and forecast uncertainty comes from bootstrapping estimated
structural residual *vectors* rather than from a conditional-variance model.

The constructs below involve lags, persistence or autoregressive-looking arithmetic and are **not** autoregressive models of
any variable. Each is flagged in the notebook where it appears:

| Construct | Why it is not an AR model |
|---|---|
| `K_t = (1−δ)K_{t−1} + I_t` | National-accounting identity; δ is **imposed**, nothing is fitted |
| `cpi_t = cpi_{t−1}(1+π_t)` | A price *level* cumulating an estimated *rate* |
| `debt_t = debt_{t−1} − balance_t` | Stock-flow accounting |
| Chain-linked aggregation | The official aggregator requires last year's nominal weights |
| DOLS leads/lags | Leads and lags of the **differenced regressors** only; the dependent variable's own lags never enter |
| Constant base add-factors | Each equation's own 2025 residual, held fixed — consistent with the finding that residuals are generally **not** shown to be stationary; a sensitivity decays them at a fixed, user-set half-life (v2.3; until v2.2 at each residual's estimated autocorrelation ρ̂, now removed) |
| Decay of the 2026 anchor increment | A **judgemental rule**: the add-factor increment derived from Jan–Apr 2026 data applies fully in 2026 and decays by a fixed 0.5 a year (half-life one year); nothing is estimated from a variable's history |
| Jan–Apr → full-year bridge | Relates two measurements of the same year |
| Fan-chart shocks | Historical five-year residual *paths* are replayed (u_{s+h} − u_s); nothing is estimated on the residual dynamics |
| Pension indexation to CPI | A statutory policy rule for a policy variable |

Newey–West **HAC standard errors** correct inference only; they never change a fitted value or a forecast. **ADF/KPSS tests** are
specification diagnostics; they can be deleted without changing any forecast number. Residual-based cointegration tests
(MacKinnon) are diagnostics too.

### 1.2 Why structural is the right choice here

- **The dominant driver is exogenous.** Hydrocarbons are 28.5% of GDP, 85.6% of goods exports and 48.1% of budget revenue
  (2025). Oil output has declined 4.9% a year since 2019 and gas reached plateau (+1.0% in 2025 after +6.1% a year). No filter
  can know this; it must be imposed as a scenario.
- **Policy questions require policy levers.** The model must answer what happens if public investment, credit conditions or the
  oil price change. Only a structural model has those levers, and Part 14 quantifies each.
- **Structural breaks dominate the sample.** The 2015 devaluation (0.78→1.77), the 2020 pandemic and the 2021–22 gas price shock
  make any autoregressive parameterisation unstable. A structural model attributes these to their causes.

---

## 2. Data layer

### 2.1 Workbook anatomy and three traps

Indicators run down rows, periods across columns, in two kinds: **annual** (a bare four-digit year) and **year-to-date
cumulative** (`2026 yanvar-aprel` = January through April cumulated). Three traps silently corrupt results if missed:

1. **Mixed decimal conventions** — `29886,9`, `2.472,8`, `1 234,5`, and `-` for missing, sometimes in one row.
2. **Repeated labels** — `"Sənaye"` appears in the value-added, gross-output *and* investment blocks of one sheet. Variables are
   therefore addressed by **(sheet, row)**, and all 196 addresses are asserted against their expected label and unit at build
   time. A future row insertion fails loudly instead of silently modelling the wrong series.
3. **Azerbaijani casing** — `"İ".lower()` returns `i` + U+0307, not `"i"`. This actually dropped a variable during development.
   Note the converse trap too: `"I".lower()` returns `i`, not the Azerbaijani dotless `ı`, so folding `ı` to `i` breaks every
   match against a literal containing it (`buraxılış`, `sayı`, `balıqçılıq`). Only the combining-dot case is folded.

### 2.2 Coverage dictates a block-recursive design

| Block | Sample | n |
|---|---|---|
| Sectoral value added, output, consumption, income, labour | 2000–2025 | 26 |
| Industry sub-branches | 2005–2025 | 21 |
| Monetary, credit, deposits, dollarization | 2006–2025 | 20 |
| Fiscal, balance of payments, customs trade, unemployment | 2010–2025 | 16 |
| Industry sub-branch panel (29 branches) | 2016–2025 | 290 rows; 259 branch-years (27 branches) usable for the production function |
| Regional panel (14 economic regions) | 2021–2025 | 70 |

Series with fewer than about ten annual observations (import/export price indices, export diversification indices, VAT) are
excluded from core equations and used only as diagnostics or scenario inputs. A five-observation regressor cannot identify a
structural elasticity.

### 2.3 Audited identities — five real problems found

Twenty-four identities are tested before estimation (tolerance 1%, 5% for the budget balance and unemployment identities);
nineteen hold. Four discrepancies were investigated (a fifth, public debt, was found in v2.3.2), and
each changed the model:

1. **Budget expenditure** — `total ≠ current + capital`; the true identity is `total = current + capital + debt service`, which
   holds to 0.0 in every year 2010–2025. A two-way identity would misstate spending by up to 10%.
2. **Total investment before 2006** — the oil/non-oil, domestic/foreign and state/private decompositions agree with each other
   but not with the reported total (2004: 4,922.8 vs 8,840.0). They reconcile exactly from 2006, so investment equations start
   there.
3. **Industry investment 1995–97** — sub-components recorded as literal zeros while the total is positive; false zeros, reset to
   missing.
4. **Industry investment 2024** — sub-components sum 3.6% below the published total. A genuine source inconsistency, flagged
   rather than adjusted, and worth raising with the data provider.
<!-- AUTO:v23_debt -->
5. **Public debt (v2.3.2)** — the workbook total ('Ümumi dövlət borcu', `Fiskal sektor` row 22, labelled mln USD) is on three
   bases: 2010–2020 in mln AZN (2020: 16 938.8 = external 8 821.5 mln USD × 1.7000 + domestic
   1 942.3 mln AZN), 2021–2024 in mln USD (2024: 16 106.0), and 2025 the unconverted sum 22 618.0 =
   4 813.5 (USD) + 17 804.5 (AZN). Converting the whole row at the exchange rate gave 38 451 mln AZN for 2025
   and mis-scaled 2010–2020 by the exchange rate (×0.80 in 2010, ×1.70 in 2020). Public debt is now external (row 24) × end-year exchange rate + domestic (row 23) in every
   year — the Ministry of Finance concept, without state-guaranteed debt: **25 987.5 mln AZN in 2025
   (20.1% of GDP)**. The three bases are asserted in the notebook.
<!-- /AUTO:v23_debt -->

### 2.4 Derived variables

- **Population** recovered as `GDP / GDP per capita` — 10.24m in 2025, a series not otherwise in the file. The forecast uses its
  **2021–2025 average growth, 0.483% a year, computed in the code**; the path is exported as `pop` (thousand persons) in
  `FR1_forecast_full.csv` and used identically by FR4 and FR5.
- **Constant-price (2015) volumes** by chaining the official previous-year=100 growth indices.
- **Implicit deflators** as `nominal / real`, so the price block is *derived from* the quantity block rather than assumed.
- **Capital stocks** by perpetual inventory with asset-life-differentiated depreciation (ICT 12%, construction 8%, manufacturing
  and mining 7%, trade 6%, agriculture 5%, electricity and other services 4%, water 3%). "Social and other services" has no
  single investment row, so it is built as public administration + education + health capital spending.

### 2.5 Two aggregation facts that govern the whole model

**The aggregator is validated before it is used.** Official real GDP growth is chain-linked with previous-year price weights:
`g_t = Σ_i w_{i,t−1} · g_{i,t}`. Reproducing published growth 2010–2025 gives **MAE 0.028 pp (max 0.107 pp)**. The naive
alternative — summing fixed-2015-weight real components — errs by **up to 2.03 pp**, because mining's nominal weight collapsed
from 45.9% (2010) to 25.6% (2025) while its volume fell. All forecast aggregation uses the validated rule, which is what keeps
model output reconcilable with DSK publications.

**Chained volumes are not additive.** `real oil GDP + real non-oil GDP ≠ real GDP`; the gap drifts from −5.3% (2010) to +4.9%
(2025). Real non-oil GDP must therefore be built from **its own** chain-linked growth rate, never by subtraction. The *nominal*
split, by contrast, is exact: `non-oil GDP = Σ(non-mining VA) + net taxes − (oil GDP − mining VA)` holds to 0.000% in every
year, the wedge being oil refining and oil services (3–4 bn AZN).

---

## 3. Model architecture

30 behavioural level relations, 17 rate (inflation/deflator) equations and about a dozen identities in eight blocks; 51 endogenous
variables solved simultaneously each year.

```
     ┌──────────── A. EXOGENOUS / SCENARIO ────────────┐
     │ Brent · oil output · gas output · gas export    │
     │ price · population · exchange rate · policy &   │
     │ deposit rates · public investment LEVEL ·       │
     │ external demand · minimum wage                  │
     └───────┬─────────────────────────────────┬───────┘
             ▼                                 ▼
     ┌── B. HYDROCARBON ──┐            ┌── F. FISCAL ──────────────┐
     │ export prices      │───────────▶│ oil revenue               │
     │ mining value added │            │ non-oil revenue           │
     │ oil & gas exports  │            │ current expenditure       │
     └─────────┬──────────┘            │ PUBLIC INVESTMENT (F4) ◀──┤ the oil-to-non-oil
               │                       │ deficit, debt             │ transmission channel
               │                       └───────┬───────────────────┘
               ▼                               ▼
     ┌─────────────── C. REAL SECTOR (11 sectors + tax wedge) ──────────┐
     │  agr  min  man  elc  wat  con  trd  tou  tra  ict  oth  nettax   │
     │  each: capacity + inter-sector linkages + demand + trend TFP     │
     └──────┬────────────────────────────────────────────────┬──────────┘
            │           chain-linked GDP identity            │
            ▼                                                ▼
   ┌── D. DEMAND ──┐                                ┌── E. INCOME/LABOUR ──┐
   │ consumption   │◀──────────────────────────────▶│ participation         │
   │ investment    │                                │ employment rate       │
   │ exports       │                                │ wages                 │
   │ imports       │                                │ disposable income     │
   └───────┬───────┘                                └───────────┬───────────┘
           ▼                                                    ▼
   ┌── G. MONEY & PRICES ──┐                         ┌── H. EXTERNAL ──┐
   │ deposits, credit      │                         │ current account │
   │ sectoral allocation   │                         │ trade balance   │
   │ lending rate          │                         └─────────────────┘
   │ CPI inflation         │
   │ 12 sector deflators   │
   └───────────────────────┘
```

### 3.1 Block B — hydrocarbons as quasi-exogenous income

Price-taking and volume-constrained. Estimated: oil export price on Brent, **long-run elasticity 1.17** — **unit pass-through
is rejected** (HAC-F p = 0.017; s.e. 0.068), i.e. the Azerbaijani export price over-reacts to Brent; mining real value added on oil
and gas volumes, **0.86 / 0.26** — constant returns are **rejected** (p = 0.046) and not imposed; hydrocarbon goods exports from
volume × price (an identity with 7.400 barrels per tonne and a BOP ratio of 1.002).

The gas *export* price is **deliberately not modelled**: regressed on Brent it gives R² 0.17 with no significant coefficient,
because the 2022 European gas shock decoupled the two (276 → 790 USD/kcm while Brent moved far less). Forcing a relationship
would fabricate a transmission channel that no longer exists, so it is an exogenous scenario variable.

### 3.2 Block C — inter-sector transmission

Each sector takes the form

> `ln(real VA_i) = α_i + β_i ln(capacity_i) + Σ_j δ_ij ln(real VA_j) + γ_i ln(demand_i) + λ_i·trend`

where the `δ_ij` answer FR1's requirement to show how each sector is affected by related sectors. Linkages are chosen from
input–output logic *a priori*, never by searching for fit: construction ← public and private investment; manufacturing ←
capital, construction (building materials) and non-oil exports; trade ← consumption; transport ← non-oil activity; tourism and
other services ← per-capita disposable income; ICT ← ICT capital per capita; electricity and water ← derived demand; net taxes ←
consumption and imports.

**A trend-discipline lesson.** An early specification used `ln(population)` as the scale variable and produced elasticities of
2–4, because population is a near-deterministic trend over 2000–2025 and was absorbing TFP growth. Two corrections are applied
throughout: household-driven sectors are modelled **per capita** (imposing unit population elasticity rather than estimating
it), and technical progress is carried by an **explicit trend** rather than smuggled in through a trending regressor.

### 3.3 Blocks D–H, and the fiscal transmission channel

- **Consumption** — per-capita disposable income (long-run elasticity 0.93) and household credit (0.12, insignificant). The
  ex-post real lending rate was dropped (Section 5).
<!-- AUTO:v23_e3 -->
- **Household income (E3)** — a share relation (v2.3: with the real wage bill): ln(income / pension bill) on ln(non-oil GDP /
  pension bill) and ln(wage bill / pension bill), elasticities 0.60 on non-oil GDP, 0.38 on the real wage bill (average
  wage × employment / consumer prices; the 2025 wage share of household income is 0.43) and 0.02 on the pension bill
  (homogeneity imposed: not rejected on data ≤ 2020, p = 0.16; rejected on the full sample, p = 0.001, where the free form
  has a wrongly signed non-oil GDP term). Non-oil GDP stands for the remaining market income (entrepreneurial and property
  income); the wage bill carries the wage and minimum-wage channel. The pension bill is a **proxy**: average pension × total
  population (the workbook has no count of pensioners). Pensions are a policy variable, CPI-indexed in the forecast.
<!-- /AUTO:v23_e3 -->
- **Investment** — accelerator on non-oil output (0.20) and state investment (0.89). No credit term: its free estimate is wrongly
  signed and the regional-panel value is rejected by the aggregate data.
- **Public investment (F4)** — real state investment on real oil revenue, estimate 0.90; unit elasticity **not rejected (low
  power**: p = 0.76, s.e. 0.31) and imposed.
- **Non-oil revenue** — long-run buoyancy 1.32 w.r.t. non-oil GDP; unit buoyancy not rejected (low power: p = 0.12, s.e. 0.19)
  and imposed, plus imports (0.56).
- **Credit (G1)** — real deposits (0.52) and the policy rate (−0.043); non-oil GDP removed (wrong sign, −0.67).
<!-- AUTO:v23_g4 -->
- **Inflation** — a structural cost markup (v2.3.4): the exchange-rate change in the current year (0.041, p = 0.25) and
  the previous year (0.131, p = 0.010; a lag of the regressor, no lagged inflation) and wage growth (0.347, p = 0.06);
  R² 0.31. Cumulative exchange-rate pass-through 0.17 (2015–17 history: 0.29); the import-price
  forms were dropped because the two import-price sources contradict each other in 2021–25 (v2.3.4 note).
<!-- /AUTO:v23_g4 -->
- **Deflators** — each sector's deflator inflation on CPI inflation; mining (v2.2, macro-module form) on the export-value-weighted
  oil + gas export price index (USD) and the exchange rate, without a CPI term. For social & other
  services the free estimate (drift 6.6 pp, pass-through 0.59) implied ~9% a year; the joint hypothesis "no drift, unit
  pass-through" is rejected (p = 0.001) but unit pass-through alone is not (p = 0.22), so unit pass-through is imposed and the
  drift kept. Deflator log changes are now applied exactly (exp), fixing a units bug.
- **Sectoral credit allocation** — a share system estimated by SUR with adding-up imposed.

## 4. Identification and estimation

### 4.1 Device 1 — restrictions tested, then imposed

Restrictions are tested on the long-run DOLS coefficients with a small-sample HAC-F test and imposed (by re-estimating under the
restriction) only if not rejected; a non-rejection is reported with the s.e. of the tested combination and read as "not rejected
(low power)", never as confirmation:

| Restriction | Estimate | HAC-F p | s.e. of combination | Verdict |
|---|---|---|---|---|
| Oil export price: unit pass-through from Brent | 1.174 | 0.017 | 0.068 | Rejected (not imposed) |
| Trade VA elasticity to consumption = 1 | 0.961 | 0.003 | 0.011 | **Rejected** |
| Mining oil + gas elasticities = 1 | 1.126 | 0.046 | 0.056 | **Rejected** |
| Oil-gas GDP oil + gas elasticities = 1 | 1.246 | 0.000 | 0.026 | Rejected |
| Manufacturing capital elasticity = factor share 0.56 | 0.241 | 0.029 | 0.120 | **Rejected** |
| Investment credit elasticity = regional-panel 0.134 | −0.135 | 0.028 | — | **Rejected** (credit term omitted) |
| <!-- AUTO:fr1v236_e3hom -->Household income: non-oil GDP + pension + wage-bill elasticities = 1 | 0.342 | 0.001 | 0.132 | **Rejected** — imposed on theory grounds (v2.3)<!-- /AUTO:fr1v236_e3hom --> |
| <!-- AUTO:fr1v236_socdefl -->Social-services deflator: pass-through 1 (drift free) | 0.59 | 0.222 | — | Not rejected — imposed (no-drift joint test rejected, p = 0.001)<!-- /AUTO:fr1v236_socdefl --> |
| Non-oil tax buoyancy = 1 | 1.322 | 0.124 | 0.192 | Not rejected (low power) — imposed |
| Public investment elasticity to oil revenue = 1 | 0.901 | 0.757 | 0.312 | Not rejected (low power) — imposed |

Unit population elasticity is additionally imposed on all per-capita equations and on labour-force participation.

### 4.2 Device 2 — panel-to-aggregate parameter transfer

Two micro panels carry far more information than the annual series.

**Industry sub-branch panel** (29 branches × 2016–2025, 290 rows; 259 branch-years from 27 branches in the value-added
function). Two-way fixed effects with Driscoll–Kraay standard errors (1 lag, t(9) inference) give a capital elasticity of **0.12**
(wild cluster bootstrap p = 0.16) and a labour elasticity of **1.03** (p = 0.001). The observed **labour share** is 0.339 (median,
all branches, wages only — the figure used before), 0.361 on non-hydrocarbon branches, and **0.441 on non-hydrocarbon branches
grossed up for the 22% employer social contribution** (aggregate ratio 0.375). The first figure was biased down twice — it omitted
employer contributions and included crude-oil extraction and refining, whose value added is mostly rent (labour shares 3–4%). The two disagree, and the disagreement is informative rather than a failure: with only ten
years of within-branch variation, value added moves nearly one-for-one with employment (labour hoarding; the
perpetual-inventory capital stock is still dominated by its initial condition), so the panel identifies a *short-run* response.
The income share identifies *long-run* technology under competitive factor pricing, and Azerbaijani industry is capital-intensive
(refining, chemicals, metals). The corrected factor share gives **α_K = 0.56, α_L = 0.44**. It is used as a *candidate* restriction on
aggregate manufacturing, and there it is **rejected** (long-run capital elasticity 0.24, p = 0.029), so the manufacturing capital
elasticity is estimated freely. (The previous version printed "IMPOSED α_K = 0.66" but actually estimated the equation freely.)

**Regional panel** (14 economic regions × 2021–2025, 70 observations). With T = 5, inference uses Driscoll–Kraay with 1 lag and
t(4), plus wild cluster bootstrap p-values (clusters = years, Webb six-point weights). Credit elasticity of output **+0.134**
(DK p < 0.001, wild p = 0.022; +0.422 with region effects only), of industrial output **+0.682** (wild p = 0.016), of agricultural
output **+0.430** (wild p = 0.027); construction on total investment **+0.518** (wild p = 0.021). The panel starts after the
hold-out cut, so none of these can enter the hold-out model.

**Not evidence: the regional trade equation.** Regional trade value added is an exact **0.320 multiple of retail turnover in 58
of 63 region-years** — an imputation by the source. Its "elasticity" of 1.009 reproduces the imputation rule, and the earlier
claim that it cross-validated the aggregate trade equation has been withdrawn.

**Transfer caveat.** Two-way fixed effects identify *relative* (cross-sectional) elasticities purged of aggregate effects. The
regional tax elasticity is 0.30 against a long-run aggregate buoyancy of 1.32 (free estimate), precisely because aggregate buoyancy is driven by the national
covariation that fixed effects remove. Only parameters plausibly invariant across the cross-section and the aggregate are
transferred. Neither is: the output-credit elasticity is rejected by the aggregate investment data (HAC-F p = 0.028) and is an
output, not an investment, elasticity, so it appears only as a labelled judgemental overlay in the multiplier experiments; the
tax elasticity is not transferred.

### 4.3 Devices 3 and 4 — parsimony and cointegrating estimation

One to three theory-selected regressors per equation, screened by VIF and the condition number of the standardised regressor
matrix (three equations flagged high: E2, D3, C4). Long-run relations use **Dynamic OLS (Stock–Watson)**: the levels regression is
augmented with the contemporaneous value and leads/lags of the *differences of the regressors*, so the dependent variable's own
lags never appear. 15 equations use DOLS ±1, 12 DOLS with contemporaneous differences, 3 static OLS (no stochastic regressor);
estimator and residual df per equation are in `FR1_equation_audit.csv`. Wrong-signed, insignificant long-run terms are dropped
by a rule applied inside the estimation (and re-applied on pre-cut data in the hold-out); none remains.

**Cointegration is mostly not established.** With the correct residual-based (MacKinnon) p-values, cointegration is found at 5% in
only **2 of 30** level relations (mining, non-oil revenue) and at 10% in **4** (adding oil revenue and the lending rate). For the
other 26 the t-statistics are labelled *descriptive*, and in 21 equations at least one level coefficient lies outside the 95%
interval of the same equation estimated in first differences. Consequences: base add-factors are held constant (no evidence the
residuals die out), with a decay sensitivity; and the dynamic hold-out is the binding test.

### 4.4 Simultaneity

Excluded instruments are only variables exogenous in the model: Brent (current and lagged), oil and gas output, population, the
policy rate and the minimum wage. The trend (a regressor, not an instrument) and state investment (endogenous through F4, and
itself instrumented in C6 and D2) were removed. For each of the 20 equations with a model-endogenous regressor a Durbin–Wu–Hausman
test (control function, HAC-F) is run. **Rule:** 2SLS replaces DOLS/OLS only if DWH rejects at 5%, every first-stage F ≥ 10 and
Sargan does not reject. DWH rejects in 2 equations, Sargan rejects in 14 of 20, and **no equation qualifies**; 3SLS on the core is
reported as a robustness check only. The 3SLS covariance is not used for the fan charts (Section 7.5).

## 5. Specifications that failed, and what was done instead

This section exists because a model is only as trustworthy as its disclosed failures. Each of these was tried, rejected on
evidence, and replaced — all documented in the notebook with the rejected output shown.

| What failed | Evidence | What the model does instead |
|---|---|---|
| **Output gap** in the inflation equation | Four measures tried. Freely estimated production function gives a *negative* labour elasticity; with panel factor shares imposed it implies −1.31% a year TFP and a drifting "gap"; a linear deterministic trend gap is insignificant; a segmented trend gap is significant but flips the exchange-rate coefficient negative because its breaks coincide with the devaluation. Real credit growth as a proxy enters *negatively*. | No demand-pressure term. Inflation is a pure cost markup. Activity still reaches inflation through endogenous wages, but a separate output-gap effect is **not** identified and the model says so. |
| **User cost of capital** in investment | Wrongly signed in all four measures (real lending rate, nominal, GDP-deflator-based, smoothed). State investment is 53% of total investment (2025); with 20 observations and a pegged rate there is too little independent variation. | User cost excluded. A credit term is omitted too: its free estimate is wrongly signed (−0.14) and the regional-panel 0.134 is rejected (HAC-F p = 0.028). |
| **Household income on budget social spending** | n = 7 for four parameters, social spending wrongly signed (−0.10); in the hold-out n = 2 (exact fit). A wage-bill + pension-bill replacement failed homogeneity (sum 0.62, p < 0.001) and under-predicted consumption by up to 23% in the static solution. | Non-oil GDP + pension bill (average pension × total population; the workbook has no pensioner count), chosen on pre-cut evidence; homogeneity not rejected (p = 0.12, low power) and imposed. Static consumption errors are now within ±10% except 2016–18 (−12% to −14%). A guard stops any hold-out regression with fewer than 5 residual df. |
| **Ex-post real rate in consumption** | Long-run −0.019 vs −0.001 in first differences; with current inflation inside it, a 1-s.d. inflation shock raised real consumption 14%. | Dropped. |
| **Wrong-signed, insignificant long-run terms** | Agricultural capital (−0.004), investment in imports (−0.07), non-oil GDP in transport (−0.10). | Dropped by a rule re-applied on pre-cut data in the hold-out. No wrong-signed long-run coefficient remains. |
| **Jan–Apr → full-year bridge** | The pooled slope 0.52 came from the 2021 base effect (tourism −32.8%/+99.3%). A Huber bridge on 2022–25 (slope 0.68) does not beat 1:1: HLN-DM one-sided p = 0.126. | 1:1 mapping. |
| **Credit on non-oil GDP** | Wrong sign (−0.67) next to deposits. | Dropped. |
| **Imposed unit/CRS restrictions** | Trade unit elasticity, mining CRS and manufacturing α_K are rejected under DOLS + HAC-F. | Left free. |
| **Regional trade cross-validation** | An imputation artefact (0.320 × retail in 58 of 63 region-years). | Withdrawn as evidence. |
| **Policy-rate pass-through** to market rates | Wrongly signed. In 2016–17 the policy rate was raised to 15% defensively while lending rates *fell* (20.7% in 2010 → 16.4% in 2016): over this sample it is a crisis instrument, not a steering rate. | Lending rate on the **deposit rate** (long-run pass-through 1.40) plus an NPL risk premium; the deposit rate is a scenario variable. The policy rate acts on credit **quantities**, where it is correctly signed (−0.043). |
| **Labour demand in levels** | VIF above 20; extrapolated, it moved unemployment more than a percentage point in the first forecast year. | An Okun-type **employment-rate** relation: `ln(emp/lf)` on non-oil GDP per capita, long-run elasticity 0.034, single regressor. Measured unemployment has been 4.9–5.6% every year since 2010 except 2020. |
| **Free labour-force equation** | Population elasticity collapses to 0.05 with a 1.1%-a-year trend (VIF > 100), implying unemployment drifting up 3 pp. | Unit population elasticity imposed; only participation drift estimated (+0.045% a year). The participation rate is in fact flat: 51.35% in 2010, 52.56% in 2025. |
| **Import equation without relative price** | Investment coefficient *negative* — impossible where capital goods are nearly all imported. The 2015–16 devaluation compressed imports while investment moved. | A real-exchange-rate term added. It restores the sign only in static OLS; in the long-run DOLS fit the investment coefficient is wrongly signed and insignificant, so it is dropped: imports depend on consumption and the relative price (v2.3: estimated in import-volume form, where its elasticity is positive — see the v2.3 note). |
| **Hydrocarbon export value as a regression** | Elasticity of 1.285 on oil revenue — impossible, since value *is* volume × price. A unit error: volume in tonnes, price per barrel. | Replaced by an **identity** with the recovered 7.400 barrels-per-tonne conversion (exact) and a calibrated 1.002 ratio (2021–25) to the balance-of-payments measure. |
| **Mechanical resource rule for public investment** | Applying the estimated unit elasticity over a declining-oil horizon cuts real public investment ~30% by 2030 and produces a ~3%-of-GDP surplus — a projection of pro-cyclical austerity, not a neutral baseline, and not what a country with a sovereign wealth fund would do. | Public investment is set as a **policy level** (stated openly in each scenario) while oil-revenue *deviations* from the scenario's own reference path move it with the estimated elasticity — so the oil transmission channel operates at full strength in the multiplier experiments. |

Five solver-side errors found during development are also documented, because each produced plausible-looking but wrong
forecasts:

1. **Decaying the base add-factors** injected a spurious growth swing (+18% then −18% real GDP). Base adjustments are held
   constant (the residuals are not shown to be stationary); only the partial-year 2026 anchor increment decays.
2. **Solving for adjustments that reproduced the whole system exactly** diverged, because the simultaneous feedback amplifies
   each step. Reading residuals off a single forward pass **double-counted**, because employment, defined multiplicatively on the
   labour force, absorbed that variable's error too. Each equation's **own residual** avoids both.
3. **Re-anchoring shock runs** forced anchored variables back onto the observed 2026 targets and so cancelled the shock, making
   the fiscal multiplier look far too small. Shock runs reuse the baseline adjustments.
4. **Three equations silently omitted their constant adjustment** (household credit, deposits, hydrocarbon exports), producing a
   20% level discontinuity in the first forecast year. An automated self-check now asserts full coverage.
5. **Composite aggregates lost their forecast real path** because the first forecast year had no previous-year chain weights.
   The chain now starts from the last actual year.

---

## 6. Validation

### 6.1 Estimator correctness

`linearmodels` is unavailable in this environment, so OLS/HAC, 2SLS, 3SLS, SUR, DOLS and panel FE with Driscoll–Kraay errors
are implemented directly and **validated against `statsmodels` to machine precision** (coefficients and standard errors, HC1 and
small-sample Newey–West HAC, 2SLS, 3SLS-equals-2SLS in the just-identified case, the panel within-transform, and the residual-based
cointegration p-value against `statsmodels.tsa.stattools.coint`).

### 6.2 Dynamic ex-post hold-out, 2021–2025 — the binding test

Everything is re-made **on data through 2020 only**: all coefficients (same builders and DOLS rule; smallest residual df 7, a guard
stops any regression below 5), every restriction and wrong-sign decision, the DWH estimator rule, the manufacturing α_K test
(factor share from 2016–2020 panel years), and every calibrated share and ratio. The regional panel starts in 2021 and is never
used. The system is solved **dynamically** for 2021–2025 with only actual *exogenous* paths; **state investment is endogenous and
follows F4** (a policy-level variant feeding actual state investment is reported separately); pensions follow CPI indexation plus
their actual real increase. Coefficient signs agree between the pre-2021 and full samples in 28 of 30 level equations (flips: C3,
G3). DM tests use the HLN correction with h = 3 (the errors are 1–5-step errors of one path; with five observations the
correction is defined only up to h = 3) and are indicative only.

<!-- AUTO:v22_holdout -->
| | Result (14 variables) |
|---|---|
| Beats a random walk from 2020 (pandemic trough) | 14 of 14, median U **0.59** |
| Beats a random walk from 2019 | 11 of 14, median U 0.58 |
| Beats constant growth 2010–2019 (pre-pandemic) | **6 of 14, median U 1.04** |
| Beats constant growth 2010–2020 | 8 of 14, median U 0.95 |
| Significant wins (HLN-DM p < 0.10) | 2 vs RW2020; 1 vs constant growth 2010–19 |
| Real GDP level error after 5 years | **−11.4%** (U 0.71 vs RW2020, 1.10 vs CG 2010–19) |
| Real non-oil GDP level error after 5 years | −10.6% (U 0.47 vs RW2020, 1.39 vs CG 2010–19) |
| Policy-level variant | median U 0.54 vs RW2020, 0.90 vs CG 2010–19 |

*(v2.2 figures: the mining deflator on the hydrocarbon export price index — see the v2.2 note. Its own hold-out error falls
from 27.3% to 6.8% and nominal GDP's from 25.6% to 19.1%, but real GDP's rises from 7.3% to 8.5% because the more accurate
2021–22 mining prices give mining, whose volume fell, a larger chain weight.)*
<!-- /AUTO:v22_holdout -->

<!-- AUTO:v22_headline62 -->
**Headline:** the random walk from 2020 flatters the model (2020 was the pandemic trough). Against constant growth estimated over
the pre-pandemic decade the model is roughly **on par** (median U 1.04; 1 significant win). Tracked well: consumption (RMSE
1.1%), trade 2.4%, employment 3.0%, agriculture 4.3%, real GDP 8.3%. Tracked poorly: construction 21.0%, transport 17.6%,
manufacturing 14.5%, state investment 17.9%, ICT 25.7% (v2.1: 2020, the cut year, was an ICT investment trough) — sectors transformed after 2020 (new manufacturing capacity, the Karabakh and East
Zangezur reconstruction, the Middle Corridor). Real current spending is over-predicted by 33% by 2025.
<!-- /AUTO:v22_headline62 -->

### 6.3 Other checks

Per equation: sign and magnitude against theory; small-sample HAC significance; residual-based cointegration; first-difference
cross-check; heteroskedasticity; normality; VIF and condition number; and Chow tests at 2015, 2020 and 2022 on the final
specifications (**10 of 20** tested coefficient sets show instability). System-wide: identity closure, convergence for every
solved year, and a static solution check (mean |real GDP error| 1.7%; consumption within ±10% except 2016–19).

---

## 7. Solution, anchoring and forecasting

### 7.1 Solver

Each year is solved by **damped Gauss–Seidel** iteration to a fixed point (residual < 1e-10; <!-- AUTO:v23_solver -->57–78 iterations per forecast year,
52–57 in the hold-out<!-- /AUTO:v23_solver -->), with identities imposed exactly at every iteration.

### 7.2 Anchoring 2026 on observed data

<!-- AUTO:v23_anchor -->
2026 is four months observed. All twelve GDP components have published year-to-date real growth indices. A robust (Huber)
proportional bridge from January–April to full-year growth, estimated on 2022–2025 (2021 excluded: its January–April growth is a
2020 base effect), has slope 0.68 and a cross-validated RMSE of 3.9 pp against 6.4 pp for the 1:1 mapping, but it does
**not** beat 1:1 on an HLN-corrected Diebold–Mariano test (one-sided p = 0.126), so the **1:1 mapping** is used. Each
component's implied full-year level is an anchoring target reached through add-factor increments; **the increments apply fully in
2026 and decay by half each year** (1/16 remains in 2030). The largest is construction (−0.210 log points, from
−19% January–April growth).
<!-- /AUTO:v23_anchor -->

**The 2026→2027 sawtooth.** Because the construction anchor unwinds at a one-year half-life, construction goes <!-- AUTO:v22_sawtooth -->−19.0% (2026) →
+12.1% (2027) → +6.4% (2028); non-oil GDP +0.66% → +4.81% → +4.31%<!-- /AUTO:v22_sawtooth --> (v2.3), i.e. roughly 1 pp of the 2027 non-oil figure is the unwinding.
Agriculture (<!-- AUTO:v23_agr -->+2.0% → +4.8%<!-- /AUTO:v23_agr -->, the second being its estimated trend) shows no anchor-driven sawtooth; ICT (<!-- AUTO:v22_sawtooth_ict -->+9.0% → +6.3%<!-- /AUTO:v22_sawtooth_ict -->) now does: <!-- AUTO:v23_ict -->its January–April anchor adds 1.7 pp in 2026 and takes back 0.9 pp in 2027, and per-capita ICT capital no longer grows at the 2025 investment share (−0.1 pp in 2027<!-- /AUTO:v23_ict -->, `FR1_sector_decomposition_all.csv`).

<!-- AUTO:v23_jantable -->
| | Published Jan–Apr | Model 2026 (full year) | Difference |
|---|---|---|---|
| Real GDP growth | +0.20% | +0.24% | +0.04 pp |
| Real non-oil GDP growth | +0.70% | +0.66% | −0.04 pp |
<!-- /AUTO:v23_jantable -->

Two data tensions are passed to the user: construction contracting 19% while total investment rises 15%, and a steep Q1 fall in
both exports and imports.

### 7.3 Scenarios

Because hydrocarbons are exogenous, the forecast is scenario-conditional by construction — a feature that forces assumptions
into the open. Calibrated on the 2025 starting point (Brent 69.1, oil 27.68 mt, gas 50.92 bcm, FX 1.70, policy rate 6.75%).
Common to all scenarios: population +0.483% a year (computed), oil-sector investment moving with the oil-output path (compounded),
<!-- AUTO:fr1v236_pens -->pensions at the decided 2026 indexation (+9.3%, Presidential Order; `data/dsmf_pension/pension_indexation.csv`) and indexed to CPI from 2027<!-- /AUTO:fr1v236_pens -->, <!-- AUTO:fr1v236_mw -->minimum wage at the legal 400 AZN in 2026 and then +6% a year (Adverse +3%, Reform +9%; `data/dsk_minwage/minwage_path.json`, the same path as FR3)<!-- /AUTO:fr1v236_mw -->; v2.2: 2026 oil and gas output from the January–March outturn in every
scenario, and 2026 state investment anchored on the <!-- AUTO:v22_sip -->approved State Investment Programme (2 700 mln AZN, sheet `DİP 2016-2026`)<!-- /AUTO:v22_sip -->.

<!-- AUTO:v22_scenarios -->
| Driver | Baseline | Adverse | Reform |
|---|---|---|---|
| Brent by 2030 | ~66 USD/bbl | ~48 | ~80 |
| Oil output 2027–30 (v2.2) | Ministry plan growth: −2.1, −1.8, +3.0, −0.4% | pre-v2.2 Baseline decline: −4.2, −3.8, −3.5, −3.0% | plan + 1.2, 0.8, 0.5, 0 pp |
| Gas output 2027–30 (v2.2) | Ministry plan growth: −1.1, −4.7, +5.2, 0.0% | plan − 1 pp | plan + 3 pp |
| State Investment Programme 2026 | 2 700 mln AZN (approved) | same | same |
| Gas export price | → 300 USD/kcm | 230 | 380 |
| Public investment (policy level, real) | +1.5% p.a. | −4% p.a. | +5% p.a. |
| Policy / deposit rate | easing | tightening | easing |
| Exchange rate | 1.70 | 1.70 | 1.70 |
| External demand | +3% p.a. | +0.5% p.a. | +5% p.a. |
| Non-oil TFP | trend | trend | +0.4 log points a year from 2027 on every sector with a TFP/trend term (agr, man, elc, wat, tou, tra, ict, oth) — now actually applied by the solver |
<!-- /AUTO:v22_scenarios -->

### 7.4 Headline results

<!-- AUTO:v22_results -->
| | Baseline | Adverse | Reform |
|---|---|---|---|
| Real GDP growth, avg % p.a. 2026–30 | **2.57** (this run; earlier versions: v2.2 2.90, v2.1 2.40, v2 (2026-10-05) 2.56; first round 1.34; original 1.23) | 1.32 | 3.62 |
| Real non-oil GDP growth, avg % p.a. | **3.76** (this run; earlier versions: v2.2 4.20, v2.1 3.99, v2 (2026-10-05) 4.18; first round 2.68; original 2.35) | 2.54 | 4.91 |
| CPI inflation 2030, % | 4.58 | 3.86 | 5.34 |
| Unemployment 2030, % | 4.67 | 4.86 | 4.49 |
| Budget balance 2030, % of GDP | +0.01 | +0.98 | −0.39 |
| Public debt 2030, % of GDP | 12.3 | 12.9 | 11.5 |
| Hydrocarbon share of value added 2030, % | 16.7 | 12.2 | 19.8 |
| Nominal GDP 2030, bn AZN | 188 | 163 | 212 |
| Non-oil budget balance 2030, % of non-oil GDP (v2.2) | −11.3 | −8.4 | −13.1 |
<!-- /AUTO:v22_results -->

<!-- AUTO:v22_path -->
Baseline path, % growth (v2.3):

| | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| Real GDP | 0.24 | 2.55 | 2.47 | 4.37 | 3.25 |
| Real non-oil GDP | 0.66 | 4.81 | 4.31 | 4.78 | 4.28 |
| Consumption | 4.60 | 1.83 | 2.79 | 3.89 | 3.77 |
| Manufacturing | 6.20 | 6.05 | 6.20 | 6.75 | 6.53 |
| Agriculture | 2.00 | 4.75 | 4.29 | 4.06 | 3.94 |
| Construction | −19.00 | 12.07 | 6.39 | 5.27 | 2.74 |
| ICT | 9.00 | 6.35 | 6.90 | 7.34 | 7.55 |
<!-- /AUTO:v22_path -->

**Why higher than the first revision.** The re-specified household-income equation ties income to non-oil GDP (share relation),
so the demand loop non-oil GDP → income → consumption → trade, taxes and services → non-oil GDP is stronger; consumption now <!-- AUTO:v22_whycons -->grows
1.8–4.6% a year (history<!-- /AUTO:v22_whycons --> about 5%), where the first revision's wage-bill version gave 0.1–2.4% and under-predicted consumption by up to
23% in-sample. The 1:1 YTD mapping, the transport transit term and the deflator units fix also contribute. Non-oil growth <!-- AUTO:v22_whynonoil -->of
3.8% a year (v2.3)<!-- /AUTO:v22_whynonoil --> is inside the 2021–25 range (2.7–9.1%) but above the 2015–25 average (about 3%).

**Plausibility flags, disclosed.** *Manufacturing* grows <!-- AUTO:v22_man -->~6.3% a year (v2.3<!-- /AUTO:v22_man -->; 6.9% with the pre-v2.1 3-year investment shares): capacity plus the export ↔ manufacturing loop (C3 export
elasticity 0.71 × D3 manufacturing elasticity 0.35; loop gain 0.25) applied to +3% a year external demand. Recent history is
comparable (≈8% a year 2021–25), but <!-- AUTO:v22_manrmse -->the hold-out RMSE for manufacturing is 14.5%<!-- /AUTO:v22_manrmse -->; no pre-cut evidence supports a different
specification (every candidate fails the sign screen on pre-cut data). *Agriculture* grows ~4.2% a year, 90% of it the estimated
deterministic trend, against 0.9–3.4% in recent years; a 2015 trend break was tested on pre-cut data and not significant
(p = 0.52), so no break is imposed. More than half of 2027–2030 growth is deterministic trend in <!-- AUTO:v22_trend -->transport (102%), ICT (98%;
v2.3), agriculture (90%) and electricity (65%)<!-- /AUTO:v22_trend --> — those paths are as good as the assumption that the historical trend continues.

**Add-factor sensitivity:** if the base add-factors decay at a fixed, non-estimated half-life (v2.3; no residual autocorrelation is
estimated) instead of being held, average growth is lower — <!-- AUTO:v22_addfactor -->real GDP 2.31% (baseline), 1.12% (adverse), 3.33% (reform); non-oil 3.51%, 2.35%, 4.62% (v2.3, half-life 1 year; constant add-factors: 2.57% and 3.76%)<!-- /AUTO:v22_addfactor --> (v2: each sensitivity run now builds its own oil-revenue reference path).

**The clearest structural result:** the hydrocarbon share of value added falls <!-- AUTO:v22_hcshare -->from 25.6% to 16.7% in the baseline (v2.2: Ministry output plan; 14.5% in v2.1)<!-- /AUTO:v22_hcshare -->, because oil
volumes decline while non-oil sectors grow.

### 7.5 Uncertainty

<!-- AUTO:v23_fan -->
500 baseline replications combine: (1) **historical residual-path resampling** — a start year s (2010–2020) is drawn and the joint
deviations u_{s+h} − u_s (h = 1…5) of all 29 behavioural residuals are added to the constant add-factors; nothing is estimated on
the residual dynamics; paths are centred and used with both signs (antithetic); (2) the same five-year history for log Brent, oil
and gas output, **with the same start year**; (3) antithetic, sign-preserving parameter draws from N(β̂, V̂_HAC) (21.1% of coefficient
draws rejected for a sign flip), with base add-factors recomputed to reproduce 2025. 2026 deviations are scaled by 0.84 (the
remaining full-year uncertainty once January–April is known) and 2/3 for the exogenous drivers.

**Diagnostics.** 856 replications were attempted (428 antithetic pairs) to obtain 500 valid (58.4%). Discarded:
194 for a one-year move more than 0.3 log points away from the baseline's (or 1.5× the largest move the variable
made in 2000–2025, where larger — e.g. tourism, state investment, oil-linked prices), 7 non-finite, 0 explosive,
1 for non-convergence (a failed member discards its antithetic pair). The screen therefore truncates the tails somewhat. In
the exported draws the share of draw-years with |Δlog| > 0.3 is 0.0% for real GDP, 0.0% for non-oil GDP, 0.0% for CPI,
0.0% for employment, 0.2% for consumption, 10.0% for real current spending and 18% for non-oil investment (whose own
history has larger moves).

**Centring.** Shocks and parameter deviations are symmetric, but aggregates are arithmetic sums of log-normally shocked parts
(chain-linked GDP, oil + non-oil revenue, the income loop), so the raw median lies above the baseline: by 2030 +1.6% (real GDP), +2.4% (non-oil), +3.1% (consumption), +1.6% (income), +6.2% (current spending), +5.6% (revenue). The exported draws are then centred on the baseline (multiplicatively for levels, additively for
rates): the median equals the published baseline in every year (max gap 1e−13), dispersion unchanged; cross-variable
identities hold only up to those shifts.
<!-- /AUTO:v23_fan -->

<!-- AUTO:v22_bands -->
| 2030, baseline | 5–95% band (% of median) | 25–75% | hold-out 5-year error |
|---|---|---|---|
| Real GDP | 19.5 | 7.8 | −11.4% |
| Real non-oil GDP | 25.3 | 10.3 | −10.6% |
| CPI level | 52.6 | 31.3 | −30.7% |
| Employment | 8.9 | 4.2 | −4.2% |
| Real disposable income | 42.9 | 15.1 | +10.5% |
| Real consumption | 58.7 | 25.7 | +0.7% |
| Real current spending | 67.8 | 27.5 | +32.5% |
<!-- /AUTO:v22_bands -->

Bands are of the same order as the model's own 2021–25 errors except consumption (far wider than its small hold-out error, because
of the income loop). **Growth and CPI bands** — real GDP growth p5–p95 of <!-- AUTO:v22_growthband -->about −4% to +14% a year, CPI inflation about −5% to
+16%<!-- /AUTO:v22_growthband --> — replay the 2015–16 devaluation, the 2020 pandemic and the 2021–22 inflation episode, *with both signs*: the upper CPI tail is
the 2016 devaluation (15.7%), while the deflationary lower tail is the mirror image of those episodes and has no historical
precedent under the peg — it should be read as an artefact of symmetric resampling of an asymmetric history.

### 7.6 Multipliers — the FR1 answer on inter-sector transmission

Each experiment shocks one exogenous driver in the **solved** system, reusing the baseline add-factor paths. Deviations from
baseline by 2030, in per cent (`FR1_multipliers.csv`):

<!-- AUTO:v22_multipliers -->
| | Brent +10 USD/bbl | Public investment +1 bn AZN | Credit easing (estimated) | Credit easing + judgemental overlay | External demand +10% |
|---|---|---|---|---|---|
| Construction | +1.72 | +5.60 | +0.02 | +1.32 | +0.12 |
| Manufacturing | +0.62 | +2.07 | +0.00 | +0.40 | +9.46 |
| Trade | +0.35 | +1.12 | +0.85 | +1.08 | +1.36 |
| ICT | +1.00 | +3.52 | −0.01 | +0.36 | −0.02 |
| Real GDP (chain-linked) | −0.06 | +0.96 | +0.22 | +0.41 | +1.17 |
| Real non-oil GDP | +0.38 | +1.20 | +0.27 | +0.52 | +1.46 |
| Consumption | +0.36 | +1.16 | +0.89 | +1.12 | +1.41 |
| Non-oil investment | +3.47 | +11.42 | −0.03 | +1.17 | −0.08 |
| Budget revenue | +3.78 | +1.41 | +0.57 | +0.86 | +1.75 |
| Non-oil imports | −0.16 | +1.14 | +0.91 | +1.14 | +1.37 |
<!-- /AUTO:v22_multipliers -->

<!-- AUTO:fr1v236_brent -->
**Brent +10 and chain-linked real GDP.** Real GDP deviates by +0.18, +0.07, −0.01, −0.01, −0.06% in 2026–2030 although no sector's value added falls (smallest sector deviation +0.00%). Chain-linked GDP weights each sector's growth by its previous-year nominal share; the higher oil price raises the share of mining, whose real output follows the declining oil and gas path (−1.1% a year), so the same sector volumes add up to slightly lower aggregate growth. It is a weighting effect of the index, not a contraction; non-oil GDP rises.
<!-- /AUTO:fr1v236_brent -->

Transport no longer responds to any of these shocks (its equation is transit volume + trend). **Credit easing** (−200 bp policy,
−100 bp deposit rate) works only through household credit and consumption in the estimated model; the column labelled
"judgemental overlay" additionally applies the regional-panel output elasticity 0.134 to deviations of credit in the investment
equation — a user lever, **not** an estimated effect (the aggregate data reject it, HAC-F p = 0.028).

<!-- AUTO:v22_fiscal -->
**Fiscal multiplier (`FR1_fiscal_multiplier.csv`).** +1 bn AZN of real state investment a year (actual injection 977 mln after the
F4 response): real non-oil GDP +741 mln (2015 prices) in 2030 — a **2030 level multiplier of 0.76**; **cumulative multiplier**
(sum of Δ non-oil GDP 2026–30 / sum of injections) **0.63** (0.57 on chain-weighted real GDP). It is larger than in the first
revision (0.54/0.46) because of the stronger income loop; imports now rise (+1.14%).
<!-- /AUTO:v22_fiscal -->

<!-- AUTO:v22_oilprice -->
**An oil price rise lowers chain-weighted real GDP** (−0.06%; −0.48% before v2.2) while raising non-oil GDP (+0.38%) and budget revenue (+3.78%):
a higher oil price raises the mining deflator and hence mining's chain weight while mining's volume (exogenous) falls. v2.2: the
mining deflator now follows the export-value-weighted oil + gas export price index (oil is 58% of hydrocarbon exports in 2025),
not the Brent price in manat with a unit-like elasticity, so the weight effect — and the fall in real GDP — is smaller.
<!-- /AUTO:v22_oilprice -->

---

## 8. Complete accounts: five metrics for every sector and market

Part 16 of the notebook delivers the full account an analyst needs: for **49 entities** — the 12 DSK sectors, 7 aggregates,
4 consumer markets, 5 investment aggregates, 5 labour-market series, 4 credit and deposit series, 3 external-trade series,
7 fiscal series and 2 price indices — five aligned series over both history (2005–2025) and forecast (2026–2030), for all
three scenarios:

**real value · real growth rate · deflator · deflator inflation · nominal value**

linked by the identity `nominal = real × deflator`, verified numerically (max absolute error 1.5×10⁻¹¹).

### 8.1 What "real" and "deflator" mean per entity — stated, not assumed

Value-added sectors and the consumer markets have their **own** implicit deflator (nominal ÷ chain-linked real, derived in
Section 2.4). Financial, fiscal and labour aggregates have no published deflator, so one must be *chosen*, and the choice is
declared per entity:

| Entity group | Own deflator? | Deflator used | Meaning of "real" |
|---|---|---|---|
| 12 sectors, GDP, non-oil GDP, oil-gas GDP | Yes, implicit | Nominal ÷ real value added | Constant-price volume |
| Consumer market, retail, catering, paid services | Yes, implicit | Turnover deflator | Constant-price turnover |
| Fixed investment (5 aggregates) | Yes, implicit | Aggregate investment deflator | Constant-price investment |
| Credit, deposits, budget revenue and spending, debt | No | **GDP deflator** | Purchasing power over domestic output |
| Wages | No | **CPI** | Purchasing power over consumption |
| Employment, labour force | n/a | — | The quantity *is* real |
| Goods exports and imports | Partly | GDP deflator on the manat value | Constant-price trade volume |

**Validation:** every historical nominal series in the accounts reproduces the workbook's own published series to
**0.000000%** across all entities checked, including the oil / non-oil GDP split, which uses the exact published nominal
decomposition in history and a calibrated mining-to-oil-GDP ratio (1.100) only in the forecast.

### 8.2 Markets added to close the coverage

The request covers markets as well as sectors, so the consumer market was resolved into its three published components —
retail trade, catering and paid services — whose identity with the total holds exactly in the source. Their **nominal shares**
are estimated as a system by SUR with adding-up imposed, but are **not extrapolated**, and the reason is visible in the data:
the shares moved sharply in 2020 and have been *reverting* ever since (paid services 19.0% in 2019 → 14.6% in 2020 → 17.5% in
2025). A trend specification fits well in sample (R² ≈ 0.84) yet projects retail to 85.5% and paid services to 11.5% by 2030 —
the opposite of the last five years. The composition is therefore held at its three-year average and renormalised, the same
treatment given to the sectoral credit shares and for the same reason.

### 8.3 Two further errors the accounts work exposed

Building the accounts forced every series to be reconciled against the source, and that surfaced two defects that the
forecast tables alone had hidden:

1. **A unit error in the hydrocarbon export equation.** Estimated as a regression it gave an elasticity of **1.285** on oil
   revenue — economically impossible, since export value *is* volume × price. The excess came from mixing units: oil export
   volume is in million **tonnes** while the export price is per **barrel**. Recovering the conversion from the published oil
   export value gives **7.400 barrels per tonne**, and with it the relationship is an exact identity (max error 0.00% on oil,
   0.01% on gas). B4 is an identity with a calibrated ratio (1.002, 2021–25 average) linking the
   customs volume × price product to the broader balance-of-payments measure.
2. **Three equations were silently missing their constant adjustment** in the solver — household credit, deposits and
   hydrocarbon exports. The effect was visible once the accounts were tabulated: real household credit fell 20% in the first
   forecast year and then grew normally, an obvious level discontinuity. The notebook now carries an **automated self-check**
   that asserts every adjusted variable actually applies its term inside the solver, so this class of bug cannot recur silently.

### 8.4 Headline five-metric results, baseline

<!-- AUTO:v22_accounts -->
| | Real growth<br>% p.a. | Deflator infl.<br>% p.a. | Nominal growth<br>cum. % | Nominal 2030<br>mln AZN |
|---|---|---|---|---|
| **GDP** | +2.6 | +5.1 | +45.4 | 187,727 |
| **Non-oil GDP** | +3.8 | +6.7 | +65.9 | 153,142 |
| Oil and gas GDP | −1.2 | −0.0 | −6.0 | 34,585 |
| **Tourism & catering** | **+8.2** | +5.9 | +97.5 | 7,055 |
| Information & communication | +7.4 | −2.7 | +25.0 | 3,337 |
| Manufacturing | +6.3 | +4.7 | +71.3 | 13,220 |
| Transport & storage | +5.0 | +2.7 | +46.0 | 13,299 |
| Water supply & waste | +4.4 | +4.5 | +54.7 | 467 |
| Agriculture | +3.8 | +4.3 | +48.5 | 11,360 |
| Trade & vehicle repair | +3.2 | +7.1 | +65.2 | 24,163 |
| Net taxes on products | +3.2 | +7.2 | +66.0 | 20,575 |
| Electricity, gas & steam | +2.9 | +8.1 | +70.3 | 2,478 |
| Social & other services | +2.4 | +9.7 | +79.0 | 50,244 |
| Construction | +0.9 | +2.8 | +19.8 | 10,096 |
| Mining & quarrying | −1.1 | +0.1 | −5.1 | 31,433 |
<!-- /AUTO:v22_accounts -->

Tourism's <!-- AUTO:fr1v236_tou -->+8.2% a year comes from its income elasticity (1.9)<!-- /AUTO:fr1v236_tou --> on faster-growing per-capita income plus trend — another demand-loop
result to read with caution. The social-services deflator still rises <!-- AUTO:fr1v236_soc -->9.7% a year<!-- /AUTO:fr1v236_soc -->: unit CPI pass-through is imposed, but the
estimated drift is kept because the no-drift hypothesis is rejected.

## 9. Limitations

Each is specific and traceable to the data, not a generic caveat.

1. **No input–output table** in the workbook, so inter-sector linkages are *estimated* from time-series and panel covariation
   rather than *measured*. This is the highest-value data addition and is in any case required by the policy module's FR2.
2. **No sector-level employment** at annual frequency — only industrial sub-branches (2016–2025) and regions (2021–2025). Full
   sector production functions are estimable only for industry. This directly limits what FR3 and FR4 (wages and employment *by
   sector*) can deliver from this file alone.
3. **No external demand variable** anywhere in the workbook, so it is a user-set scenario input and the non-oil export equation
   is supply-side only.
4. **No identified interest-rate or output-gap channel** (Section 5). The model cannot simulate a policy-rate change through
   market rates, nor a pure demand-pressure effect on inflation.
5. **Short fiscal and BOP samples** (16 annual observations) mean those blocks carry materially wider parameter uncertainty.
6. **The regional panel is only five years long**; several coefficients change sign between one-way and two-way specifications,
   reported in the notebook. Its inference now uses t(4) and a wild cluster bootstrap over the five years.
7. **The exchange rate is a de facto peg** since 2017, so pass-through is identified almost entirely by the 2015–16 devaluation.
   Any scenario moving the rate extrapolates from a single episode.
8. **Sector investment deflators are not published**, so the aggregate investment deflator is applied to every sector.
9. **Chain-linked volumes are not additive**; the non-oil wedge uses a calibrated correction whose size is reported.
10. **ICT, construction, transport and manufacturing forecasts are the weakest** (<!-- AUTO:v22_lim10 -->hold-out RMSE 14.5–25.7%<!-- /AUTO:v22_lim10 -->; ICT because 2020, the hold-out cut, was a trough of its investment share); against pre-pandemic
    constant growth the model is only on par (median U 1.02).
11. **Calibrated shares are held fixed** (sector investment and credit shares — v2.1: at their 2025 values —, social-spending share, debt-service rate).
12. **Public investment's level is an assumption, not a forecast** (Section 5, last row).
13. **Cointegration is established for only 2 of 30 level relations** (4 at 10%); most level t-statistics are descriptive and
    the forecast level depends on the constant-add-factor assumption (Section 7.4 sensitivity).
14. **Trend-carried growth** — transport, agriculture, ICT and electricity growth in 2027–2030 is mostly estimated deterministic
    trend (Section 7.4).
15. **A strong demand loop** (income tied to non-oil GDP) raises growth, tourism and the fiscal multiplier; manufacturing is
    amplified by the export ↔ manufacturing link. The household-income elasticity rests on a pension-bill proxy
    (average pension × total population); v2.2 tested the macro module's income-by-source decomposition (DSMF transfers):
    better in-sample, worse in the dynamic hold-out, so it is an engine lever, not the forecast (v2.2 note).
16. **No aggregate credit channel** in investment; credit easing on investment is a judgemental overlay.
<!-- AUTO:v23_lim17 -->
17. **Fans** are wide for CPI, consumption and current spending, are truncated by the jump screen (22.7% of attempted
    replications rejected, 41.6% replaced with their antithetic pairs), carry a mirrored deflationary CPI tail, and are centred on the
    baseline after a reported median correction.
<!-- /AUTO:v23_lim17 -->

## 10. What would most improve the model

1. A **supply-use / input–output table** — replaces estimated linkages with measured ones and unlocks policy-module FR2.
2. **Employment and compensation by sector**, annual — completes the production-function block and serves FR3/FR4 directly.
3. **Partner-weighted external demand** and an import price index with history — properly identifies the trade block.
4. **Quarterly national accounts by sector** — roughly quadruples the effective sample, making dynamics estimable rather than imposed.
5. **A longer regional panel** — the cross-section is the model's best identification device and currently only five years deep.
