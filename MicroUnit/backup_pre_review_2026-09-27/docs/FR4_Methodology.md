# FR4 — Employment indicators of the population
## Structural econometric methodology and five-year forecast

**MIIS module 15.5.2 — Microeconomic analysis and forecasting**
Ministry of Economy of the Republic of Azerbaijan

Companion document to `FR4.ipynb`. Third of three linked deliverables: **FR1** (sector output and the
macro economy), **FR3** (average monthly wages), **FR4** (employment).

---

## 1. The task

> *Əhalinin məşğulluq göstəriciləri (onların iqtisadiyyatın sahələri, dövlət və qeyri-dövlət sektoru,
> büdcə və qeyri-büdcə təşkilatları, neft və qeyri-neft sektoru üzrə **sayı** və **artım sürətləri**)
> təhlili və proqnozlaşdırılması mümkün olmalıdır.*

Analysis and forecasting of the population's employment indicators — **numbers** and **growth rates** —
by (1) sectors of the economy, (2) state and non-state sector, (3) budget and non-budget organisations,
(4) oil and non-oil sector. Horizon 2026–2030.

**Constraints.** No AR, ARIMA, ARCH or GARCH models. Structural econometric models only, so that the
effect of related sectors is visible. Where the workbook lacks data, collect it from the State
Statistical Committee (DSK).

---

## 2. Why outside data was required

The workbook `Statistik data dinamika 05.06.2026 +.xlsx` carries the sector and institutional
breakdown of employment **for five years only**:

| Workbook location | Content | Years |
|---|---|---|
| `Sosial sektor ` r58–r59 | Labour force; employed population | 1995–2025 |
| `DVX üzrə göstəricilər` r91–r103 | Employment contracts: total, oil, state, non-state, 8 sectors | **2021–2025** |
| `DVX üzrə göstəricilər` r130 | Budget-organisation headcount | **2022–2025** |
| four industry sheets | Hired employees, 29 industrial branches | 2016–2025 |
| `Regionlar`…`Regionlar 13` | Hired employees, 14 regions | 2021–2025 |

Five annual observations cannot identify a nineteen-activity structural system. The instruction to
collect DSK data was therefore a precondition, not a refinement.

**Data collected** from `stat.gov.az/source/labour/`, stored in `data/dsk/` and re-downloaded
automatically if absent:

| File | Sheet | Concept | Years |
|---|---|---|---|
| `002_1-2en.xls` | `Dynamics_2.1` | Employed population by 19 activities | 1999–2024 |
| `002_8-9en.xls` | `Dynamics_2.8` | Hired employees by 19 activities | 1999–2024 |
| `002_3en.xls` | `Dynamcs_2.3` | Employed population by property form | 1990–2024 |
| `002_12-13en.xls` | `2.12`, `2.13` | Hired employees by activity × property form | 2023, 2024 |
| `006_1-5en.xls` | `Dynamics_6.1` | State Employment Agency indicators | 1991–2024 |

The sheet name `Dynamcs_2.3` contains the source's own typographical error and must be matched exactly.
No reader assumes a fixed column offset; each locates its year columns by scanning the header row.

**Validation.** Every activity block reproduces its published total to machine precision. Three
independently published DSK tables agree on all twenty rows for 2024. Decisively, the workbook's
employed-population series (`Sosial sektor ` r59) and the DSK activity total are **the same series to
the last decimal in all 26 overlapping years**. The DSK breakdown is therefore a decomposition of
exactly the aggregate FR1 forecasts, so attaching DSK shares to FR1's total involves no splice, no
rebasing and no definitional wedge.

---

## 3. Source reconciliation, and which source does which job

Two sources report employment by sector and they count different things.

- **DSK `Dynamics_2.8`** — hired employees from the establishment survey, classified by the
  establishment's actual activity.
- **Workbook `DVX`** — employment contracts registered with the tax service, classified by the
  taxpayer's registered activity code, end of period.

The **totals** agree within 1–5%. The **sector composition does not**: the DVX/DSK ratio runs from 0.70
(agriculture) to 1.81 (accommodation and food), and the ratios **drift** over 2021–2024 by up to 0.55.
The two sources also disagree about growth, so they cannot be spliced.

| Object | Source used | Why |
|---|---|---|
| 19 activities, 8 sector groups | DSK survey, 1999–2024 | 26 years; adds up exactly; its total *is* the workbook total |
| State / non-state | DSK property form, 1990–2024 | 35 years; the workbook has no employment equivalent |
| Budget / non-budget | DSK activity × property + DVX r130 | Only sources identifying budget-financed employment |
| Oil / non-oil | Workbook industry branches + DVX r92 | Neither DSK activity table isolates oil |
| 2025 values, nowcast anchor | Workbook | DSK activity tables stop at 2024 |

A definitional point that must not be blurred. On the **tax-record basis**, oil + state + non-state =
total **exactly**, so the workbook's state and non-state rows cover the **non-oil economy only**. On the
**DSK basis**, state + non-state = total exactly, but over **all** employment including oil. "State
sector" therefore means different things in the two sources, and FR4 reports the DSK definition as the
headline while reproducing the workbook's narrower split separately.

---

## 4. Data-integrity findings

**F1 — The State Employment Agency series are unusable for estimation.** Registered unemployed jumps
from 81,272 (2019) to 217,608 (2023), with 2020–2022 unpublished; vacancies jump from 5,715 (2022) to
59,849 (2023). Both breaks coincide and reflect a move to digital registration. A vacancy series would
have given FR4 a labour-market tightness channel — the one channel FR3 also lacked — so this is a real
loss, recorded rather than fitted around.

**F2 — The workbook's `priv_share` is not the private share of employment.** It differs from the DSK
non-state employment share by up to 14 percentage points and moves differently. Using it for the
state/non-state split — the obvious shortcut, since it runs 1995–2025 — would have been wrong.

**F3 — The budget-organisation headcount falls 9% in 2025 while total contracts rise.** DVX r130 reads
636.7, 640.7, 645.9 for 2022–2024, then 588.0 for 2025. Calibration uses 2022–2024 only; Part 18 carries
the alternative through to the forecast.

**F4 — DVX rows 127–129 duplicate rows 123–125 byte for byte.** The block that should report budget
organisations' taxpayer count, turnover and receipts repeats the micro-taxpayer block. Only row 130 is
genuine.

**F5 — The workbook carries two employee-count series 11% apart.** Row 91 (contracts, end of period)
reads 1,872.9 thousand for 2024; row 107 (hired, monthly average) reads 2,073.8. The DSK survey gives a
third figure, 1,780.3. FR4 uses the DSK basis throughout and reports the wedge wherever it matters.

---

## 5. The structure to be explained

Four facts govern every modelling choice.

1. **Hired employees are a stable third of the employed.** The ratio has stayed between 0.306 and 0.368
   for 26 years. Roughly two-thirds of the employed are not employees — self-employment, overwhelmingly
   agricultural, dominates the Azerbaijani labour market.
2. **Employment shares move very slowly even when output shares move violently.** Between 2005 and 2024
   industry's share of real value added fell 5.6 points while its share of employment **rose** 0.9 points.
3. **Mining employment is flat while mining output collapsed.** 2010→2024: output −27%, employment −5%.
4. **State employment is a slowly declining near-constant level.** Of the 1,174 thousand rise in
   employment since 2000, 1,399 thousand is non-state and −225 thousand is state.

**Shift-share decomposition** (exact identity, closes to 2.9 × 10⁻¹⁵) of labour-productivity growth,
2001–2024: **within-sector +90.3%**, static reallocation +10.0%, dynamic reallocation −0.4%. Azerbaijani
employment is structurally sticky. An economy whose labour barely reallocates cannot have its employment
composition forecast from which sector grew fastest.

---

## 6. The no-autoregression constraint, stated precisely

No equation contains a lagged dependent variable, a moving-average error, or a conditional variance
process. Three lag constructs appear, each an accounting or inferential device:

| Construct | Where | Why it is not an autoregression |
|---|---|---|
| Newey–West HAC covariance | every time-series equation | Affects standard errors only; point estimates are OLS |
| DOLS leads/lags of **regressor** differences | Part 12 robustness | Standard endogeneity correction in a cointegrating regression |
| Previous-year weights in chain aggregation | driver construction | Accounting identity of the official chain-linking method |

Where employment adjusts slowly, the slow adjustment is captured by estimating a **levels (cointegrating)
relation** rather than by adding a lagged dependent variable. The cost is stated in §11: the model
describes the long-run allocation of labour and understates first-year sluggishness.

**Four identification devices**, as in FR1 and FR3: (1) restrictions tested then imposed;
(2) panel-to-aggregate parameter transfer; (3) parsimony; (4) cointegrating estimation without
autoregression.

---

## 7. Specification search: what was rejected

Eleven candidate specifications were rejected or set aside, each on stated evidence. The reasons fall
into four families: **wrong sign**, **implausible magnitude**, **no significant driver**, and — the most
important category — **fails out of sample**.

| # | Specification | Verdict | Evidence |
|---|---|---|---|
| R1 | ln(sector employment) on ln(sector real value added) | spurious | coefficient collapses with a trend, vanishes in differences |
| R2 | mining employment on crude oil production | wrong sign | −0.052 (t = −1.9) |
| R3 | oil-extraction employment on combined oil+gas volume | wrong sign | −0.670 (t = −4.9); gas extraction is far more capital-intensive |
| R4 | participation rate on the real wage | wrong sign | −0.072 (t = −13.4) |
| R5 | public-service employment, free population elasticity | implausible | elasticity 2.8, and 4.8 in the bloc split |
| R6 | state employment on fiscal capacity or output | no driver significant | largest \|t\| on any driver = 2.2 |
| R7 | market-service employment with a real-credit term | wrong sign | credit −0.167 (t = −4.5) |
| R8 | wage term in sector labour demand | reported, not imposed | panel elasticity −0.128 (t = −0.7), n = 290 |
| R9 | **relative output shares as the Tier-1 driver** | **fails out of sample** | **12.45% vs 10.34% for constant shares** |
| R10 | a bare trend as the Tier-1 driver | fails out of sample | 12.86% |
| R11 | income per capita and relative output jointly | collinear, worst of five | 17.06% |

A robustness comparison (not a rejection) found real and nominal value-added shares equally stable
between levels and differences; real shares were preferred on theory, sample length and the fact that
the volume series is what FR1 forecasts.

---

## 8. The model

### 8.1 Aggregate block

$$L_t = N_t \,\pi_t\,(1-u_t), \qquad H_t = \phi_t L_t$$

- **E1 — labour force.** A unit population elasticity was tested (Wald χ² = 3.46, p = 0.063, not
  rejected) and **imposed**; the participation rate is trendless (t = 0.4) and is held at its 2021–2025
  mean of 0.5179.
- **E2 — employment rate.** Okun-type: $\ln(L/LF) = a + 0.093\ln Q^{non} - 0.004\,t$, R² = 0.939.
  The **level estimate (0.0934) and the difference estimate (0.0967) agree to 3.4%** — the evidence that
  this is structural and not a shared trend, which is exactly what R1 failed. A 1% rise in real non-oil
  output raises the employment rate by 0.089 percentage points.
- **E3 — employee share.** The linear trend is marginally significant (t = 2.1) but the series is
  **U-shaped**, falling to 0.306 in 2002 and recovering to 0.354; a linear trend fitted to a U extrapolates
  the recovery leg indefinitely. Imposed constant at the 2020–2024 mean of 0.3548 and exposed as a
  formalisation lever.

### 8.2 Sector allocation — a multinomial-logit share system

$$\ln\!\left(\frac{s^L_{i,t}}{s^L_{r,t}}\right) = \alpha_i + \boldsymbol{\beta}_i'\mathbf{x}_t + \varepsilon_{i,t},
\qquad s^L_i = \frac{\exp(z_i)}{\sum_j \exp(z_j)}$$

The softmax forces shares to sum to one exactly, so the nineteen activities always reproduce the
published total. No residual sector, no post-hoc normalisation.

**Driver selection is by out-of-sample forecast accuracy, not fit.** Five candidates, three cut-offs
(2015, 2018, 2019), both measurement bases pooled, error measured on **shares**:

| Candidate | Pooled out-of-sample RMSE |
|---|---|
| **Real non-oil GDP per capita** | **9.05%** |
| Constant shares (the null) | 10.34% |
| Relative real output share | 12.45% |
| Trend | 12.86% |
| Income per capita + relative output | 17.06% |

Two of these results overturn what one would write down first.

- **Relative output shares are worse than doing nothing.** The elasticity is 0.20–0.35, significant in
  every variant — levels, levels with year effects, first differences — and it still makes the five-year
  forecast worse than holding shares constant. A coefficient can describe average historical co-movement
  correctly and be useless for forecasting if the variation it is fitted to is short-lived. This is §5's
  shift-share result in another form.
- **Income per capita works**, and it is the specification with the clearest structural content: the
  **Kuznets–Chenery structural-transformation mechanism**, in which the composition of employment is
  governed by the level of development rather than by last year's relative output.

Optimal shrinkage of the income elasticity is λ ≈ 1.2 against 1.0, a 0.8% difference; **λ = 1 is imposed**
rather than tuning λ on the same hold-out that chose the driver.

**Estimated income elasticities of the employment share** (employed basis, reference = other services):

| Group | Elasticity | t | R² |
|---|---|---|---|
| Agriculture, forestry & fishing | −0.071 | −7.4 | 0.702 |
| Industry | +0.039 | 1.5 | 0.138 |
| Construction | +0.410 | 10.3 | 0.874 |
| Trade & repair | −0.085 | −8.3 | 0.743 |
| Accommodation & food | +1.038 | 8.1 | 0.839 |
| Transport & storage | −0.041 | −6.0 | 0.600 |
| Information & communication | +0.513 | 9.0 | 0.765 |

Textbook structural transformation: as real non-oil income per head rises, labour leaves agriculture and
transport for construction, hospitality and ICT. Accommodation and food has the largest elasticity —
the tourism economy of the last decade appearing in the labour market.

### 8.3 Within-group allocation

- **Within industry** (mining, manufacturing, electricity, water): the same five candidates were tested
  **independently**, and income per capita won again (7.35% against 12.49% for relative output and 9.78%
  for constant shares). The agreement across levels is a result, not an assumption. An honest
  qualification: a bare trend scores 7.58%, statistically indistinguishable over sixteen years; income
  per capita is chosen because it carries an interpretation and makes the forecast scenario-sensitive,
  which a trend would not be.
- **Within other services**: the nine activities divide into **budget-financed** (public administration,
  education, health, arts) and **market** services (finance, real estate, professional, administrative
  support, other). The bloc split is estimated on real other-services value added (elasticity 0.637
  employed / 1.189 hired). Composition inside each bloc follows activity-specific trends, and each
  trend is retained or dropped **by out-of-sample test rather than by t-statistic**. This matters:
  administrative-support employment jumped from 25 to 76 thousand between 2015 and 2020 on an
  outsourcing reclassification and has been flat since. Its trend is strongly significant and would
  extrapolate that one-off jump for five more years; the out-of-sample test rejects it where a t-test
  would have accepted it. Where a trend is retained it is then re-estimated on the full sample.

### 8.4 State and non-state

Part 7 R6 tested state investment, total public expenditure, service-sector output and GDP per capita:
**none is significant**, while a trend is overwhelmingly so (t = −22.6, R² = 0.963). Public-sector
headcount in Azerbaijan is an administrative decision, not a function of output or fiscal capacity. The
honest representation is a **logistic trend in the state share**, exposed as a policy lever. A logistic
form keeps the share inside (0,1) and lets its decline decelerate. The 1990s are excluded from the
forecasting sample: the fall from 70.7% (1990) to 36.2% (1999) was privatisation, a one-off that must
not be projected. Non-state employment is the residual, so the two sum to the total by construction.

### 8.5 Budget and non-budget

An identity with one calibrated constant:

$$B_t = \kappa \sum_{i \in \{\text{pubadm, educ, health, art}\}} H_{i,t}, \qquad \text{non-budget}_t = H_t - B_t$$

κ = 0.9901, 0.9936, 0.9976 for 2022, 2023, 2024 — **within 0.6% of one and varying by less than 1%**.
Budget-organisation employment *is*, to within a rounding, the hired workforce of those four activities.
The identity is accepted, so budget employment inherits the education and health equations instead of
needing a free-standing equation on four observations. The 2025 value is excluded (finding F3) and the
alternative κ = 0.908 it implies is carried through as a lever.

### 8.6 Oil and non-oil

Two measurement bases, both published:

- **Statistical** — crude oil and gas extraction + oil refining + mining support services (oilfield
  services). 30.9 thousand in 2025. The four mining branches reproduce the published mining total to
  machine precision.
- **Tax-record** — DVX row 92, 47.8 thousand in 2025; wider, including oil-sector service and trading
  companies registered outside mining and manufacturing.

**E9**: ln(extraction employment) on ln(real oil GDP), elasticity **0.800** (t = 4.8), R² = 0.646, n = 10.
Real oil GDP is used rather than crude oil volume because FR1 forecasts it, avoiding the unit-conversion
trap that FR1 itself hit. Refining is carried at 0.186 of extraction and mining support at 0.453, their
recent five-year averages. The tax-record level is anchored at 2025 and carried forward with the
estimated growth rate.

---

## 9. Solution and add-factors

The system is **block-recursive**, not simultaneous: employment is allocated downwards and each level
sums exactly to the level above, so no Gauss–Seidel iteration is needed.

**Add-factors.** Each equation's constant is adjusted so the model **reproduces the anchor year exactly**,
and the adjustment is **held constant**. Two mistakes were avoided, both learned in FR1: the add-factor
is each equation's **own** residual read once — not solved for iteratively, which diverges, and not
re-read from a simulated path, which double-counts — and it does **not decay**, because a decaying
adjustment injects spurious movement into the early forecast years.

**Two anchor years.** The DSK activity tables end in 2024, the workbook total in 2025. FR4 anchors the
*shares* on 2024 and the *total* on 2025, producing a **2025 nowcast** of the breakdown as well as the
2026–2030 forecast. The model reproduces every one of the nineteen activities in 2024 to 4 × 10⁻¹⁴%.

**Population** is an assumption, not a model result: continuation of the 2021–2025 average growth of
0.483% a year. FR1 publishes no population path. The lever is tested in §12.

**Driver continuity** was checked at the history/forecast junction: no driver's 2025→2026 growth lies
outside its own historical range. FR1 forecasts construction output to contract 19.0% in 2026, which is
large but not unprecedented (−22.6% in 2016), so it is passed through unaltered. The consequence is the
model's clearest structural statement: because labour reallocates weakly, construction **employment**
does not fall in proportion to construction **output**. This is testable in 2026.

---

## 10. Validation

**Dynamic ex-post hold-out.** Everything — every coefficient, composition trend and add-factor — is
re-estimated on data ending 2019, then simulated over 2020–2024 given actual drivers but no actual
employment outcomes. The window contains the pandemic deliberately.

Aggregate and institutional equations, scored by Theil's U (U < 1 beats the benchmark):

| Equation | RMSE | U vs random walk | U vs constant growth |
|---|---|---|---|
| Total employed (E1–E2) | 1.06% | **0.35** | **0.69** |
| State employment (E8) | 3.14% | **0.48** | **0.66** |
| Oil extraction employment (E9) | 4.34% | 1.56 | **0.72** |

The aggregate equation cuts the random-walk error by about two-thirds. The oil equation does not beat a
random walk, which was anticipated: a near-flat series of 20 thousand people is almost a random walk by
nature, and the equation earns its place by making oil employment respond to the oil-output scenario.

**At activity level the record is mixed and is reported as such**: the model beats a random walk in
**14 of 19** activities on the employed basis (median U = 0.78) and **10 of 19** on the hired basis
(median U = 0.89). Median activity RMSE is 3.36% (employed) and 7.84% (hired). Water supply, finance and
administrative services carry double-digit five-year errors.

**Eight identity checks**, all passing to machine precision: the 19 activities sum to the total in every
scenario and year; state + non-state = employed; budget + non-budget = hired; oil + non-oil = hired;
the anchor year is reproduced; no share leaves (0,1); employment never exceeds the labour force; and
every adjusted equation applies its add-factor — an automated check added after FR1 was found to have
silently omitted three add-factors.

**2025 nowcast against the tax records** — an independent test on data the share model never saw. The
DVX/DSK sector ratios move by only 0.028 on average between 2024 and the nowcast year, so the DSK-based
nowcast is not drifting away from the independent 2025 evidence.

**Consistency with FR3.** FR4's hired path sits a constant 12.1% below FR3's and the growth rates agree
to 0.000 percentage points. An honest qualification: this is largely **by construction**, since both
build their employee count from FR1's total. The check confirms the deliverables are mutually consistent
— they will never publish contradictory employee growth — but it is not independent corroboration. The
independent test is the 2025 nowcast above.

---

## 11. Baseline results, 2026–2030

Total employment rises from 5,105 to 5,242 thousand, **+0.53% a year**. Average annual growth by group:

| Group | % a year |
|---|---|
| Accommodation & food | +2.42 |
| Information & communication | +1.43 |
| Construction | +1.24 |
| Industry | +0.55 |
| Other services (9 activities) | +0.48 |
| Transport & storage | +0.40 |
| Agriculture, forestry & fishing | +0.35 |
| Trade & repair | +0.32 |

The ordering is the structural-transformation mechanism of §8.2 working through a five-year horizon:
the activities with the largest income elasticities grow fastest, agriculture and trade grow slowest,
and no sector's employment moves anywhere near as much as its output.

- **State employment** falls 6.7% to 979 thousand, its share from 20.6% to 18.7%; non-state absorbs all growth.
- **Budget organisations** are broadly flat near 650 thousand, their share of employees easing from
  36.0% to 34.9%.
- **Oil employment** falls 10.9% on the tax-record basis, to 42.6 thousand — a small direct effect against
  total employment above five million. The labour-market consequence of declining hydrocarbon output runs
  mainly through non-oil GDP and the aggregate employment equation, not through oil-sector headcount.

**Scenarios.** FR4's three employment paths differ by only 0.08% in 2030. This is **inherited, not a
property of FR4**: FR1's scenarios differ by 20% in real oil GDP but under 2% in real non-oil GDP, and its
labour force path is identical across all three. It should not be read as evidence that the Azerbaijani
labour market is insensitive to macroeconomic conditions. The scenarios separate where the oil channel
bites — a 15.9% spread in oil-sector employment by 2030, because that elasticity is 0.80 against 0.09
for the aggregate employment rate.

---

## 12. Levers: what is assumed rather than forecast

| Lever | 2030 effect | Why it is a lever |
|---|---|---|
| State share frozen at its 2024 level | **+119 thousand state (+12.2%)** | No fiscal or output driver is significant (§8.4) |
| Employee share +2pp by 2030 | +105 thousand employees (+5.6%), total unchanged | Trendless and U-shaped; raising it is a policy objective |
| Budget constant κ = 0.908 | −56 thousand budget (−8.6%) | The 2025 published figure implies it (finding F3) |
| Population growth ±0.3pp | ±2.8 thousand agriculture | FR1 publishes no population path |

The state-share lever is by far the largest swing, and that is the useful conclusion: the most
consequential uncertainty about state employment is a political decision, not an econometric one, and
the model says so rather than disguising it as a forecast.

---

## 13. Limitations

1. **Activity-level accuracy is limited.** The model beats a random walk in 14 of 19 activities
   (employed basis) and 10 of 19 (hired). Broad-group and institutional aggregates are considerably more
   reliable than individual activities; the §11 tables should be read with the §10 error columns beside them.
2. **It is a levels model.** With no lagged dependent variable permitted, the speed of adjustment is not
   estimated, so the first forecast year understates how sluggishly employment actually responds.
3. **The total is inherited from FR1.** FR4's own block agrees to within 2.6%, but an error in FR1's
   employment path passes straight through.
4. **Population is an assumption.** §12 shows it matters slightly more for sector composition than FR1's
   entire scenario range does.
5. **The employee share and state share are set, not forecast.** Both were tested against candidate
   drivers and neither is identified.
6. **Oil/non-oil cannot be added to state/non-state.** The two sources define state/non-state over
   different populations (§3).
7. **No labour-market tightness channel**, because finding F1 destroys the vacancy series. This is the
   clearest gap and the easiest to close.
8. **Wages do not enter sector employment.** The branch panel gives a correctly-signed but insignificant
   real-wage elasticity, so no wage term is imposed; FR3 informs FR4 through consistency checks only.

### What would improve the next vintage

- A consistent vacancy or registered-unemployment series through the 2023 break.
- DSK activity × property-form tables for more than 2023–2024, allowing the state share to be modelled
  by activity.
- An official population projection.
- A longer industrial branch panel, to identify the wage elasticity of labour demand.
- Clarification of DVX row 130 for 2025 (F3) and rows 127–129 (F4).

---

## 14. Outputs

`FR4.ipynb` — 88 cells (61 code, 27 markdown), executes with 0 errors.
`docs/FR4_Methodology.md` — this document.
22 CSV files in `output/`, including:

| File | Content |
|---|---|
| `FR4_employment_long.csv` | Tidy: scenario × basis × year × activity, level and growth rate |
| `FR4_employed_by_activity.csv`, `FR4_hired_by_activity.csv` | Levels, 19 activities, 3 scenarios |
| `FR4_employed_growth_rates.csv`, `FR4_hired_growth_rates.csv` | Growth rates |
| `FR4_institutional_breakdown.csv` | State/non-state, budget/non-budget, oil/non-oil |
| `FR4_dsk_*.csv` (4 files) | The collected DSK history, as extracted |
| `FR4_tier1_driver_selection.csv`, `FR4_tier2_driver_selection.csv` | The out-of-sample selection evidence |
| `FR4_rejected_specifications.csv` | The 11 rejections with their evidence |
| `FR4_holdout_validation.csv` | Theil U by activity |
| `FR4_identity_checks.csv`, `FR4_equation_audit.csv` | Verification |
| `FR4_sensitivity_levers.csv`, `FR4_scenario_summary.csv` | Levers and scenarios |
| `FR4_shift_share_decomposition.csv` | The exact decomposition |
