# FR4 — Employment indicators of the population
## Structural econometric methodology and five-year forecast

**MIIS module 15.5.2 — Microeconomic analysis and forecasting**
Ministry of Economy of the Republic of Azerbaijan

Companion document to `FR4.ipynb`. Third of three linked deliverables: **FR1** (sector output and the
macro economy), **FR3** (average monthly wages), **FR4** (employment).

---

## Revision note (2026-09-27, second round 2026-09-28)

A review found that the first version's selection and validation overlapped, that several claims
(cointegration, "reproduces the anchor exactly", "no actual employment outcomes") did not hold, and that
no uncertainty was published. The notebook was revised in two rounds under the shared fix contract and
re-executed end to end (0 errors, no fallback warnings) on FR1's re-run outputs (population path and
500 macro replication paths). Every number below comes from that run.

1. **Selection no longer sees the hold-out.** Every choice uses data up to 2019 only and scores only
   years up to 2019: origins 2011–2014 (after the 2010 classification break), five-year windows.
   Candidates are compared with constant shares by a Diebold–Mariano test (HLN correction) on the loss
   differential **averaged by target year** (one observation per scored year, eight in all), because
   overlapping origins that score the same year are not independent.
2. **Sector allocation (second round).** A pooled, restricted share system — one common elasticity of
   the relative employment share on the relative real output share, estimated in first differences
   with group fixed effects — is scored against constant shares. It does not win at 10% (6.48% vs
   6.96%, p = 0.45), so the **baseline is the equal-weight combination** of the two, at Tier 1 and
   inside industry. Pure constant shares, the pooled system alone and the group-specific drivers are
   Part 18 sensitivities. Income per capita (the first version's winner) is reported only.
3. **The 2010 classification break** in the DSK activity tables: a step dummy in every level equation,
   the 2010 difference dropped in first-difference estimates, origins and fan-chart resampling start in
   2011, and the shift-share 2010 row is excluded from the headline split.
4. **Estimation and inference.** DOLS for level relations (estimator and df recorded), residual-based
   cointegration p-values (`eg_coint_p`), HAC with n/(n−k) scaling, t/F small-sample inference, and a
   difference-form estimate beside each level coefficient. Most relations are not cointegrated, so
   their t-statistics are labelled descriptive.
5. **Decisions on pre-2019 data**: the E1 unit population elasticity (HAC-F p = 0.081 on data up to
   2019; 0.38 on the full sample; not rejected, low power), the E3 no-trend decision (t = 0.28 on data
   up to 2019), and the E8 estimation sample (2000 start; a 1990 start forecasts far worse, DM p = 0.03).
6. **Aggregate block and anchors.** Headline employment and labour force are FR1's, and E1–E2 is a
   cross-check anchored on 2025. There is one employee-share path (the 2024 actual, 0.3540), so the old
   2026 jump is gone. All 2025 anchors are reproduced.
7. **Institutions.** Budget = σ × hired in the four budget activities, with σ = 0.913 the state share
   from DSK tables 2.12–2.13; finding F3 is re-read as definitional. The claim in R7 is corrected. E9 is
   OLS on n = 10, its hold-out is not estimable, and both oil bases are anchored on 2025.
8. **Mining and refining are consistent with E9 (second round).** Oil extraction plus oilfield
   services (about 86% of mining) and refining (inside manufacturing) follow E9. The non-oil rest of
   industry is shared out by the Tier-1 mechanism.
9. **Hold-out without actual outcomes**: totals are simulated by pre-2019 E1–E2 with projected
   population, and every constant is re-estimated to 2019.
10. **Shift-share** uses nominal-share Törnqvist weights, so no chain-linked volumes are added. Oil and
    non-oil are split within one basis each. Text errors are fixed.
11. **Fan charts** (`FR4_fan_employment.csv`): historical residual-path resampling from 2011 (no
    estimated autocorrelation), parameter draws, and FR1's 500 draws. The notebook asserts that every
    point forecast lies inside its inter-quartile band. Add-factors are held constant; their decay at
    ρ̂ is shown as a sensitivity only.

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
636.7, 640.7, 645.9 for 2022–2024, then 588.0 for 2025. *Revised reading:* DSK tables 2.12–2.13 split the
four budget activities' 2024 hired workforce into 588.6 thousand state and 58.8 thousand non-state. The
2022–2024 values match all hired employees of those activities (ratio 0.994); the 2025 value matches
their state part (−0.1%), and the fall (57.8 thousand) matches the non-state part. The "fall" is most
plausibly a change in what the row counts; confirmation is requested from the data owner.

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

**Shift-share decomposition** (exact identity, closes to 7 × 10⁻¹⁵), 2001–2024, chain-consistent:
growth rates with Törnqvist nominal value-added share weights, so chain-linked volumes are never added
across sectors (industry's weight is the additive nominal sum of its four branches). Of +133.4 log
points of cumulative labour-productivity growth, within-sector +122.9 and reallocation +10.4. The 2010
row contains the classification break (within +2.91, reallocation +0.39 that year). **Excluding it,
92.3% of productivity growth is within sectors and 7.7% comes from reallocation.** Azerbaijani
employment is structurally sticky.

---

## 6. The no-autoregression constraint, stated precisely

No equation contains a lagged dependent variable, a moving-average error, or a conditional variance
process, and no fitted autocorrelation drives any forecast or fan chart. The lag constructs that appear:

| Construct | Where | Why it is not an autoregression |
|---|---|---|
| Newey–West HAC covariance, n/(n−k) scaling | every time-series equation | Standard errors only |
| DOLS leads/lags of **regressor** differences | level equations with a stochastic regressor | Endogeneity correction; the level coefficients are used |
| First differences with group fixed effects | pooled share systems (Tier 1, industry) | Differences of employment and output shares within a year; no lagged dependent variable on the right-hand side |
| One lag in the residual-based cointegration test | every level equation | A test statistic only |
| Constant add-factor; decay at ρ̂ | Parts 15, 18 | A fixed level adjustment; the decay is a **sensitivity only**, not a forecast rule |
| Historical residual-path resampling | fan charts | Replays observed forecast-error paths $u_{s+h}-u_s$; no estimated dynamics |
| Nominal share weights | shift-share | Accounting identity |

FR4 has no partial-year data, so the contract's nowcast add-factor rule does not arise.

---

## 7. Specification search: what was rejected

| # | Specification | Verdict | Evidence |
|---|---|---|---|
| R1 | ln(sector employment) on ln(sector real value added) | spurious | unstable between levels and differences; mean difference-form R² 0.026 |
| R2 | mining employment on crude oil production | wrong sign | −0.052 (t = −1.8) |
| R3 | oil extraction on combined oil+gas volume | wrong sign | −0.670 (t = −4.4) |
| R4 | participation rate on the real wage | wrong sign | −0.072 (t = −12.6) |
| R5 | public-service employment, free population elasticity | implausible | 2.8, and 4.8 in the bloc split |
| R6 | state employment on fiscal capacity or output | no driver passes both tests | real GDP per capita: level t = −2.12 (p = 0.044), difference t = +0.50 (corrects "none significant") |
| R7 | market services with a real-credit term | wrong sign | −0.167 (t = −4.1) |
| R8 | wage term in sector labour demand | reported, not imposed | panel −0.128 (t = −0.7), n = 290 |
| R9 | group-specific relative-output elasticities at Tier 1 | not adopted | 7.32% vs 6.96%, DM p = 0.42 |
| R10 | real non-oil GDP per capita at Tier 1 (first version) | rejected | 7.45% vs 6.96%, DM p = 0.24 |
| R11 | a bare trend at Tier 1 | rejected | 12.23%, significantly worse (p = 0.07) |
| R12 | income per capita + relative output | rejected | 13.70% |
| R13 | pooled output system **alone** at Tier 1 | not adopted alone | 6.48% vs 6.96%, DM p = 0.45 → enters by equal-weight combination |

---

## 8. The model

### 8.1 Aggregate block — cross-check, not headline

The headline total employed population and labour force are **FR1's** (`emp`, `lf`). FR4's own block
is the cross-check of §11 and the engine of the §10 hold-out.

$$L_t = N_t \,\pi_t\,(1-u_t), \qquad H_t = \phi_t L_t$$

- **E1 — labour force.** Free population elasticity: on data up to 2019 (the decision sample) −3.64
  (s.e. 2.49), HAC-F(1,16) = 3.47, p = 0.081. On the full sample it is 0.14 (s.e. 0.96), p = 0.38.
  ln(population) and the trend correlate at 0.996. The unit elasticity is **not rejected (low power)**
  and is imposed as an identifying assumption. Participation has no trend (t = 0.4 on data up to 2019)
  and is held at its **2025 actual, 0.5256**.
- **E2 — employment rate.** DOLS: $\ln(L/LF) = -0.860 + 0.0824\ln Q^{non} - 0.0036\,t$. The difference form
  gives 0.0967 (95% CI 0.021–0.172), which contains the level estimate. The cointegration p-value is
  0.225 and the DW 0.58, so the level t-statistics are descriptive. FR1's form (per-capita non-oil GDP,
  no trend, with a participation trend) gives 0.0337 (cointegration p = 0.171). <!-- AUTO:e2gap -->The two blocks differ by 0.95% in 2030 employment (1.21% at most across scenarios and years) and 0.23% at most in the labour force. Both reproduce 2025.<!-- /AUTO:e2gap -->
- **E3 — employee share.** On data up to 2019 the trend is +0.0006 (t = 0.28), and on the full sample
  t = 1.97. The difference form shows no drift, and the series is U-shaped. It is held at its **2024
  actual, 0.3540, for every year from 2025**.

### 8.2 Sector allocation — a share system with a forecast combination

$$\ln\!\left(\frac{s^L_{i,t}}{s^L_{r,t}}\right) = \alpha_i + \boldsymbol{\beta}_i'\mathbf{x}_t + \varepsilon_{i,t},
\qquad s^L_i = \frac{\exp(z_i)}{\sum_j \exp(z_j)}$$

**Selection design.** Candidates are scored on origins 2011–2014, five-year windows scored no later than
2019, both bases pooled, with errors measured on shares. Each candidate starts from actual shares. The
DM (HLN) test uses the target-year loss differential:

| Candidate | Pooled OOS RMSE | DM p vs constant |
|---|---|---|
| Pooled restricted output system (one elasticity, FD with group FE) | 6.48% | 0.45 |
| **Equal-weight combination: constant + pooled — baseline** | **6.56%** | 0.14 |
| Constant shares (null) | 6.96% | — |
| Group-specific relative output | 7.32% | 0.42 |
| Real non-oil GDP per capita | 7.45% | 0.24 |
| Trend | 12.23% | 0.07 (worse) |
| Income per capita + relative output | 13.70% | 0.13 (worse) |

**Adopted rule.** The pooled system becomes the baseline if it beats constant shares at p < 0.10. It
does not, so the baseline is the **equal-weight combination** of the two forecasts. The rationale: a
pure constant-share baseline is itself a persistence forecast and gives FR1's sector scenarios no route
to sector employment, while a driver whose gain is not significant should not carry full weight.

**Pooled elasticity** (first differences, group fixed effects, 2010 difference dropped, Driscoll–Kraay):
**0.108** on the employed basis (s.e. 0.048, n = 161) and **0.174** on the hired basis (s.e. 0.030).
The fixed effects identify β, but the group drifts are not extrapolated (a bare trend fails out of
sample). Each group starts from its 2024 log-odds and moves by β × the change in its relative output
share, at half weight.

A damped income elasticity was also tried (λ ∈ {0.2,…,1}, on pre-2019 origins). The best, λ = 0.2, has
DM p = 0.29, which becomes 1.0 after allowing for the search. The **group-specific income elasticities**
(DOLS with a 2010 step dummy) are descriptive:
- Only 3 of 14 are cointegrated at 10%, 1 has a significant difference-form coefficient, and 2 lie
  outside their difference CI.
- Employed basis: agriculture −0.055, industry +0.184, construction +0.216, trade −0.003,
  accommodation +0.595, transport −0.008, ICT +0.003.

### 8.3 Within-group allocation

- **Within industry.** Oil extraction plus oilfield services (86% of mining in 2024: 28.3 of 33.0
  thousand hired) and refining (4.0 thousand, inside manufacturing) follow **E9**: they are actual in
  2024–2025 and then move with real oil GDP. The **non-oil rest** of industry is shared among non-oil
  mining, non-refining manufacturing, electricity and water by the same combination rule. The pooled
  within-industry elasticity is 0.054 (employed) and 0.160 (hired). Selection used origins 2014–2016
  (branch VA starts 2009, so this is a thin design): pooled 10.64% vs constant 10.81%, DM p = 0.42, so
  the combination is used. Non-oil mining has no output series; its driver is non-oil industrial
  output. Result: mining now falls with its oil part (§11), no longer rising with the industry total while oil
  employment falls.
- **Services bloc split (E6)**: ln(market/budget services) on ln(real other-services VA) with a 2010
  step, DOLS. The elasticity is 0.702 (employed) and 1.626 (hired). It is not cointegrated (p = 0.84,
  0.39), and the level estimates lie outside their difference-form CIs, so the t-statistics are
  descriptive. Out of sample it beats a constant split, 6.71% vs 9.50%, DM p = 0.015, so it is kept.
  Add-factors are +0.054 and +0.028, held constant.
- **Composition inside each bloc (E7)**: trend vs constant for each activity, both starting from the
  actual value, pre-2019 origins, bases pooled. **No trend is retained (0 of 7).** There is no
  activity-level output for market services, so the pooled mechanism cannot be applied there. As a
  result, employed-basis real estate, which the first version extrapolated at about −1.8% a year,
  now grows with the market-services bloc (§11). This is a data limitation, recorded in §13.

### 8.4 State and non-state

R6: no driver passes both the level and the difference test. E8 is a logistic trend; its sample is
chosen on pre-2019 origins (a 1990 start forecasts far worse, 22.3% vs 2.7%, DM p = 0.03). On 2000–2024
the trend is −0.0239 a year (t = −21.7, R² = 0.963). The difference-form mean change is −0.0261 (CI
−0.041 to −0.011) and contains it, and the trend-stationarity p-value is 0.063. The state share is a
policy lever.

### 8.5 Budget and non-budget

$$B_t = \sigma \sum_{i \in \{\text{pubadm, educ, health, art}\}} H_{i,t}, \qquad \text{non-budget}_t = H_t - B_t$$

σ is the **state share** of hired employees in the four activities, from DSK tables 2.12–2.13: 0.9169
(2023) and 0.9092 (2024), mean **0.913**. The first version's κ = 0.994 on all hired employees
reproduced DVX r130 for 2022–2024 but counted private schools and clinics. The identity gives 596.7
thousand for 2025 against r130's 588.0 (+1.5%), consistent with the definitional reading of F3. History
before 2023 assumes the same σ.

### 8.6 Oil and non-oil

Statistical basis: 30.87 thousand in 2025. Tax-record basis (DVX r92): 47.78. **E9** is OLS (n = 10,
df = 8), elasticity 0.80 (t = 4.9). Its difference form (−0.45, CI −1.13 to 0.24) excludes it and the
cointegration p-value is 0.17, so it is descriptive. It is kept as the only scenario channel, and it
now also drives the oil parts of mining and manufacturing. Refining and support are held at their 2025
ratios to extraction, so 2025 is reproduced. Non-oil is computed within each basis.

---

## 9. Solution and add-factors

The system is block-recursive:
- FR1 total → hired (φ) → 8 groups (combination) → industry (oil parts on E9, non-oil rest by the
  combination) and services (E6, then constant composition) → 19 activities.
- State (E8) is applied to the total, and budget (σ) to the hired allocation.

Add-factors are each estimated equation's own anchor-year residual, read once and **held constant**,
because residuals are generally not shown to be stationary:
- E6: +0.054 (employed) and +0.028 (hired).
- E8: −0.018.
- E9: anchored on the 2025 actual.

The share blocks need none. Decay at ρ̂ is reported as a **sensitivity only** (§12). The anchors are
reproduced exactly (the 2025-anchor check in Part 19): shares on 2024 (to 3 × 10⁻¹⁴%), and the total, labour force, oil
on both bases and tax-record contracts on 2025. **Population** is FR1's published path.

---

## 10. Validation

**Dynamic hold-out, 2020–2024, with nothing after 2019 used.**
- Totals are simulated by FR4's E1–E2 re-estimated to 2019: population is projected at 1.07% a year,
  participation is 0.5073, the employee share 0.3441, and the E2 elasticity 0.077.
- Every share anchor, pooled elasticity, slope and add-factor is re-estimated to 2019.
- The model gets actual output drivers.
- The oil carve-out inside industry is not applied, because E9 is not estimable before 2020 (4
  observations). **E9's hold-out is reported as not estimable.**
- Benchmarks get the same information: random walk = the 2019 level; constant growth = the 2005–2019
  average (2005 is the start of the oil boom).

| Series | RMSE | U vs random walk | U vs constant growth |
|---|---|---|---|
| Total employed (E1–E2, simulated) | 1.12% | **0.37** | **0.73** |
| Hired employees | 2.06% | **0.39** | 2.41 |
| Labour force | 0.10% | **0.03** | **0.67** |
| State employment | 3.89% | **0.60** | **0.82** |
| Oil extraction (E9) | not estimable | — | — |

| Level | Median RMSE | Beats RW | Median U (RW) | Beats CG | Median U (CG) |
|---|---|---|---|---|---|
| 19 activities, employed | 4.85% | 9/19 | 1.04 | 6/19 | 1.36 |
| 8 groups, employed | 2.79% | 5/8 | 0.77 | 4/8 | 1.11 |
| 19 activities, hired | 7.12% | 9/19 | 1.06 | 11/19 | 0.98 |
| 8 groups, hired | 7.21% | 5/8 | 0.80 | 5/8 | 0.97 |

First version, for comparison: total U = 0.35 / 0.69, and 14/19 and 10/19 activities beat the random
walk. That version was given actual totals and chose its driver with 2020–2024 in view.

**Ten identity and anchor checks pass:**
1. The 19 activities sum to the total.
2. State + non-state = employed.
3. Budget + non-budget = hired.
4. Oil + non-oil = total within each basis.
5. The model reproduces every activity in the 2024 anchor year.
6. Every share stays inside (0,1).
7. Employment / labour force < 1, both from FR1.
8. Every add-factor is applied.
9. The 2025 anchors are reproduced.
10. There is one employee-share path.

**2025 nowcast vs tax records — a weak check.** The mean absolute drift of the DVX/DSK sector ratios
from 2024 to 2025 is 0.033. It mostly compares tax-record sector growth with total growth.

**Consistency with FR3.** FR4's hired path is a constant 12.3% below FR3's, and growth agrees to 0.000 pp —
by construction, so this is consistency, not corroboration.

---

<!-- AUTO:results (generated by FR4.ipynb Part 20.2 from the run's outputs; do not edit by hand) -->
## 11. Baseline results, 2026–2030

Total employment (FR1) rises from 5,105 to 5,274 thousand, **+0.65% a year** (90% band -0.22% to +1.57%).

| Group | % a year | 90% band |
|---|---|---|
| Accommodation & food | +1.00 | -1.69 to +4.08 |
| Information & communication | +0.95 | -0.13 to +2.09 |
| Transport & storage | +0.74 | -0.56 to +2.17 |
| Trade & repair | +0.70 | -0.17 to +1.62 |
| Agriculture, forestry & fishing | +0.68 | -0.11 to +1.51 |
| Other services (9 activities) | +0.63 | -0.32 to +1.66 |
| Industry | +0.50 | -0.59 to +1.53 |
| Construction | +0.48 | -0.85 to +1.81 |

- **Inside industry** (employed basis): mining -1.63% a year (its oil part follows E9), manufacturing +0.72%.
- **Inside other services**: market services grow (+1.81% a year employed, +3.83% hired) and budget-financed services fall on the employed basis (-0.09%) and fall on the hired basis (-0.61%): E6 moves employment from the budget-financed bloc towards market services as other-services output grows, fast enough here to shrink the budget-financed bloc in absolute terms.
- **Construction**: FR1 has construction output changing -19.0% in 2026; construction employment changes -0.60% that year against +0.54% for the total — a dip, but a damped one (half weight on a small elasticity).

First version, for comparison: accommodation +2.42%, ICT +1.43%, construction +1.24% … trade +0.32%, total +0.53% on FR1's earlier path.

- **State** employment: 1,049.3 → 984.7 thousand (-1.26% a year; band -2.38% to -0.22%), share 20.6% → 18.7%.
- **Budget organisations** (σ = 0.913): 596.7 → 578.6 thousand (-0.61% a year; band -1.81% to +0.51%), 31.0% of employees in 2030.
- **Oil** employment, tax-record basis: 47.8 → 41.6 thousand (-2.72% a year; band -4.46% to -1.00%); statistical basis 30.9 → 26.9.

**Scenarios.** In 2030 FR1's scenarios differ by 20.5% in real oil GDP, 11.07% in non-oil GDP and 0.35% in employment; FR4's employment therefore differs by 0.35% (18.6 thousand). Oil employment separates by 16.1% (Adverse 37.6 vs Reform 43.7 thousand).

**Fan charts** (`FR4_fan_employment.csv`, `FR4_fan_summary_2030.csv`): 2,000 replications combining historical residual-path resampling (8 joint 6-year paths starting 2011–2018 across 18 equations, centred; E9 starts 2016–2020), parameter draws and FR1's 500 macro draws. Every point forecast lies inside its inter-quartile band (asserted in Part 17.5).

---

## 12. Levers and sensitivities (2030, baseline)

| Lever | 2030 effect |
|---|---|
| population growth 0.3pp lower | total -78.6 thousand (-1.5%); labour force -82.4 thousand (-1.5%); agriculture -27.9 thousand (-1.5%) |
| population growth 0.3pp higher | total +79.6 thousand (+1.5%); labour force +83.4 thousand (+1.5%); agriculture +28.2 thousand (+1.5%) |
| employee share +2pp by 2030 | hired +105.5 thousand (+5.7%); budget +32.7 thousand (+5.7%); nonbudget +72.8 thousand (+5.7%) |
| state share frozen at its 2024 level | state +120.0 thousand (+12.2%); nonstate -120.0 thousand (-2.8%) |
| budget = all hired in the 4 activities (kappa = 0.994, first version) | budget +51.2 thousand (+8.8%) |
| Tier 1 + industry: pure constant shares | hotel -2.3 thousand (-2.1%); ict -1.2 thousand (-1.8%); construction +4.0 thousand (+0.9%) |
| Tier 1 + industry: pooled output system alone | hotel +2.3 thousand (+2.1%); ict +1.2 thousand (+1.8%); construction -4.0 thousand (-0.9%) |
| Tier-1 driver: group-specific relative output share (not adopted) | hotel +7.6 thousand (+6.8%); ict -1.5 thousand (-2.4%); construction +5.8 thousand (+1.4%) |
| Tier-1 driver: group-specific income per capita (not adopted) | hotel +11.0 thousand (+9.9%); construction +20.7 thousand (+4.9%); industry +17.7 thousand (+4.2%) |
| SENSITIVITY ONLY: add-factors decay at residual rho (E6, E8) | market services -11.5 thousand (-2.1%); state +14.2 thousand (+1.4%); budget +4.6 thousand (+0.8%) |

The decay row is a sensitivity only, not a forecast rule. The state-share lever remains the largest swing: a political decision, not an econometric one.

---

<!-- /AUTO:results -->

## 13. Limitations

1. **The sector composition responds to the economy only weakly.** No driver beat constant shares out
   of sample before 2020. The baseline is an equal-weight combination with a small pooled output
   elasticity. Market-services composition is constant, for lack of activity-level output data.
2. **Activity-level accuracy is limited**: 9 of 19 activities beat a random walk on each basis in the
   honest hold-out.
3. **Most level relations are not cointegrated**, so their t-statistics are descriptive.
4. **It is a levels model**: the speed of adjustment is not estimated.
5. **Total employment and the labour force are FR1's**; FR4's own block is a cross-check (gap ≤ 1.45%).
6. **Population is FR1's assumption.**
7. **The employee share and the state share are set, not forecast.**
8. **Oil employment rests on ten observations**, cannot be tested out of sample, and now also drives
   the oil parts of mining and manufacturing.
9. **The 2010 classification break** is handled by a step dummy, not a back-cast.
10. **Oil/non-oil cannot be added to state/non-state.**
11. **There is no tightness channel and no wage channel.**

### What would improve the next vintage

- A consistent vacancy or registered-unemployment series through the 2023 break.
- DSK activity × property-form tables for more years, and a DSK back-cast across the 2010 break.
- Activity-level output for market services.
- An official population projection, and a longer industrial branch panel.
- Confirmation of what DVX r130 counts in 2025 (F3) and of rows 127–129 (F4).

---

## 14. Outputs

`FR4.ipynb` — <!-- AUTO:cells -->114 cells (79 code, 35 markdown)<!-- /AUTO:cells -->, executes end to end with 0 errors. Its Part 20.2 cell regenerates this document's §8.1 cross-check gap, §11 and §12 from the run (between the `AUTO` markers), so those figures are never typed by hand.
`docs/FR4_Methodology.md` — this document. CSV files in `output/`:

| File | Content |
|---|---|
| `FR4_employment_long.csv` | Tidy: scenario × basis × year × activity, level and growth rate |
| `FR4_employed_by_activity.csv`, `FR4_hired_by_activity.csv` | Levels, 19 activities, 3 scenarios |
| `FR4_employed_growth_rates.csv`, `FR4_hired_growth_rates.csv` | Growth rates |
| `FR4_institutional_breakdown.csv` | State/non-state, budget/non-budget, oil/non-oil (both bases), FR1 labour force |
| `FR4_fan_employment.csv`, `FR4_fan_summary_2030.csv` | Quantile bands with the point forecast, levels and growth |
| `FR4_dsk_*.csv` (5 files) | The collected DSK history |
| `FR4_tier1_driver_selection.csv`, `FR4_tier2_driver_selection.csv`, `FR4_e6_bloc_split_selection.csv` | Pre-2019 selection with target-year DM tests |
| `FR4_tier1_income_elasticities_descriptive.csv` | DOLS elasticities with cointegration and difference-form tests |
| `FR4_rejected_specifications.csv` | Rejected / not-adopted specifications |
| `FR4_holdout_validation.csv`, `FR4_holdout_validation_groups.csv`, `FR4_holdout_summary.csv`, `FR4_holdout_aggregate.csv` | Theil U vs random walk and constant growth |
| `FR4_identity_checks.csv`, `FR4_equation_audit.csv`, `FR4_add_factors.csv` | Verification; the audit carries estimator, df, `eg_coint_p`, inference label and difference-form CI |
| `FR4_sensitivity_levers.csv`, `FR4_scenario_summary.csv` | Levers and scenarios |
| `FR4_shift_share_decomposition.csv` | The chain-consistent decomposition |

---

<!-- AUTO:v2 (generated by FR4.ipynb Part 26 from the run's outputs; do not edit by hand) -->
## 15. v2 — tənliklər reyestri, tam proqnoz cədvəli, ssenari mühərriki və dayanıqlıq

*Bu bölmə FR4.ipynb-nin 21–26-cı hissələri tərəfindən hər icrada yenidən yazılır.*

**Tənliklər reyestri** (`output/FR4_equations.json`, 21-ci hissə): notebook-da qiymətləndirilən hər tənlik — cəmi **122**, onlardan **11**-i proqnozda istifadə olunur. Bloklar üzrə: A 9, B 37, C 31, D 5, E 1, R 39 (R — rədd edilmiş/alternativ spesifikasiyalar, A — məcmu blok, B — 1-ci pillə pay sistemi, C — sənaye daxilində və xidmətlər, D — institusional bölgülər, E — shift-share). Reyestr hər tənliyi statsmodels ilə eyni (y, X) üzərində müstəqil yenidən qiymətləndirir və əmsalların notebook-un öz qiymətləndirmələrinə bərabər olduğunu yoxlayır (hamısı uyğun gəlir); diaqnostika (DW, BG, JB, White, RESET, VIF, kointeqrasiya, fərq forması), rekursiv və bir ili çıxarmaqla qiymətləndirmələr, Chow və CUSUM əlavə olunur.

**Dayanıqlıq hökmləri** (`FR4_robustness_summary.csv`): bütün tənliklər — stabil 19, qismən stabil 40, qeyri-stabil 63; proqnozda istifadə olunanlar — stabil 4, qismən stabil 4, qeyri-stabil 3. Kövrək (qeyri-stabil) proqnoz tənlikləri: `FR4.E5_pooled_emp` (rekursiv: d_lo_sq işarəsi son yarıda dəyişir; bir ili çıxarmaqla: d_lo_sq işarəsi dəyişir); `FR4.E6_emp` (rekursiv: d2010 işarəsi son yarıda dəyişir; Chow 2012 (orta nöqtə) p = 0.000; Chow 2015 (2015) p = 0.000; Chow 2020 (2020) p = 0.000; CUSUM p = 0.022); `FR4.E6_hired` (Chow 2012 (orta nöqtə) p = 0.034; Chow 2015 (2015) p = 0.012; Chow 2020 (2020) p = 0.000). Kointeqrasiya testi aparılan 70 səviyyə tənliyindən yalnız 11-ində 10%-də müəyyən edilir — t-statistikaları əksər hallarda təsviridir (19.4-cü hissə ilə uyğun). R9 sənaye panelində əmək haqqı elastikliyi -0.128: Driscoll–Kraay p = 0.491, wild-cluster bootstrap (illər üzrə, Webb) p = 0.544; buraxılış elastikliyinin bootstrap p-dəyəri 0.066 (DK: 0.011).

**Tam proqnoz cədvəli** (`FR4_forecast_tidy.csv`): 75 komponent × 3 ssenari, tarix ilk mövcud ildən, 2025 (nowcast) və 2026–2030; tamlıq yoxlanılır (1125 dəyər). 8 qrup və iki xidmət bloku indi hər üç ssenari üçün verilir (əvvəl qruplar yalnız Əsas ssenarinin fan cədvəlində idi). Zolaqlar (5–95%) Əsas ssenari üçün 14 sıra üzrə. Proqnozlaşdırılmayanlar və səbəbləri: `FR4_not_forecast.csv` (15 sıra: Məşğulluq Agentliyinin qırılan sıraları, vergi uçotu üzrə sahə bölgüsü, DVX r130/r107, regionlar). Kataloq: `FR4_indicator_catalog.csv` (id-lər `fr4:emp:<fəaliyyət>`, `fr4:hired:<fəaliyyət>`, `fr4:<əsas>:grp:<qrup>`, `fr4:<əsas>:bloc:pub|mkt`, `fr4:state`, `fr4:budget`, `fr4:oil:stat|tax`, `fr4:lf`, `fr4:phi` və s.).

**Ssenari mühərriki** (`microlib/engines/fr4.py`, vəziyyət `output/engine/FR4_state.json`): notebook-un 15–17-ci hissələrdəki həllini təkrarlayır. Redaktə olunan girişlər: 16 ekzogen FR1 yolu (`fr1:emp`, `fr1:lf`, `fr1:pop`, `fr1:rgdpnon`, `fr1:rgdpoil`, 11 `fr1:rva_*`), 10 əmsal (birləşdirilmiş β-lar, birləşmə çəkiləri, E6, E8, E9) və 6 rıçaq (əhali artımı, muzdlu payı, dövlət payı trend/dondurulmuş, σ/κ, düzəliş əmsallarının sönməsi). `upstream={"FR1": ...}` verildikdə FR1 mühərrikinin yolları istifadə olunur; FR3 proqnozda istifadə olunmur. Özünü yoxlama: hər ssenari üzrə notebook CSV-ləri maksimal nisbi fərq 1.9e-16 ilə təkrarlanır, 18-ci hissənin rıçaq cədvəli də (34 dəyər) təkrarlanır; bir ssenari ~17 ms.

**Əmsal həssaslığı** (`FR4_coef_sensitivity.csv`, ±1 standart xəta, 2030, Əsas): dövlət məşğulluğu — `FR4.E8_state|trend` ilə -0.54% / +0.54%; büdcə təşkilatları — `FR4.E6_hired|ln_rva_oth` ilə +0.97% / -0.98%; ən böyük üç qrup (Kənd, meşə və balıqçılıq, Digər xidmətlər (9 fəaliyyət), Ticarət və təmir) birləşmə çəkisinə ən həssasdır (çəki üçün SE olmadığından ±0.25) — Kənd, meşə və balıqçılıq ±0.06%, Digər xidmətlər (9 fəaliyyət) ±0.07%, Ticarət və təmir ±0.17%. Ümumi məşğulluq FR1-dəndir və FR4 əmsallarından asılı deyil.

Yeni fayllar: `FR4_equations.json`, `FR4_indicator_catalog.csv`, `FR4_forecast_tidy.csv`, `FR4_not_forecast.csv`, `FR4_robustness_summary.csv`, `FR4_coef_sensitivity.csv`, `FR4_strings_az.csv` (istifadəçiyə görünən hər ingiliscə sətrin Azərbaycan dilində qarşılığı, 424 sətir), `engine/FR4_state.json` (yalnız sadə məlumat). v2-dən əvvəlki bütün CSV-lər dəyişməz qalır (reqressiya yoxlaması).

<!-- /AUTO:v2 -->
