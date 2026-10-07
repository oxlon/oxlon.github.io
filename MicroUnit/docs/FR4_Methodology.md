> **Azərbaycan dilində:** [az/FR4_Metodologiya.md](az/FR4_Metodologiya.md)

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
7. **Institutions.** Budget = σ × hired in the four budget activities, with σ = <!-- AUTO:fr4v22_sigma1 -->0.9092 (v2.2: the 2024 value; 0.913 before)<!-- /AUTO:fr4v22_sigma1 --> the state share
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
    point forecast lies inside its inter-quartile band. Add-factors are held constant; their decay with a
    fixed one-year half-life (v2.3; nothing estimated) is shown as a sensitivity only.

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
| Constant add-factor; decay with a fixed half-life | Parts 15, 18 | A fixed level adjustment; the decay (0.5 a year, half-life one year — v2.3, no estimated residual autocorrelation) is a **sensitivity only**, not a forecast rule |
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
  no trend, with a participation trend) gives 0.0337 (cointegration p = 0.171). <!-- AUTO:e2gap -->The two blocks differ by 1.05% in 2030 employment (1.33% at most across scenarios and years) and 0.23% at most in the labour force. Both reproduce 2025.<!-- /AUTO:e2gap -->
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

σ is the **state share** of hired employees in the four activities, from DSK tables 2.12–2.13: <!-- AUTO:fr4v22_sigma2 -->0.9169
(2023) and 0.9092 (2024). **v2.2:** `Dynamics_2.12` gives every year since 2005 and holding the last published
year beats the two-year mean on origins 2010–2019, so σ = **0.9092** (2024; was the mean 0.913).<!-- /AUTO:fr4v22_sigma2 --> The first version's κ = 0.994 on all hired employees
reproduced DVX r130 for 2022–2024 but counted private schools and clinics. The identity gives <!-- AUTO:fr4v22_r130 -->594.2
thousand for 2025 against r130's 588.0 (+1.0%; 596.7 with the old mean)<!-- /AUTO:fr4v22_r130 -->, consistent with the definitional reading of F3. <!-- AUTO:fr4v22_history -->History
2005–2022 uses the observed σ (v2.2); before 2005 there is no property split, so no budget history.<!-- /AUTO:fr4v22_history -->

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

The share blocks need none. Decay with a fixed one-year half-life (v2.3; ρ̂ is not used) is reported as a **sensitivity only** (§12, §18). The anchors are
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

Total employment (FR1) rises from 5,105 to 5,270 thousand, **+0.64% a year** (90% band -0.27% to +1.52%).

| Group | % a year | 90% band |
|---|---|---|
| Accommodation & food | +0.90 | -1.89 to +3.77 |
| Information & communication | +0.86 | -0.32 to +1.96 |
| Transport & storage | +0.74 | -0.61 to +2.20 |
| Agriculture, forestry & fishing | +0.67 | -0.21 to +1.52 |
| Trade & repair | +0.64 | -0.28 to +1.56 |
| Other services (9 activities) | +0.60 | -0.41 to +1.61 |
| Industry | +0.55 | -0.64 to +1.64 |
| Construction | +0.52 | -0.96 to +1.89 |

- **Inside industry** (employed basis): mining -0.46% a year (its oil part follows E9), manufacturing +0.66%.
- **Inside other services**: market services grow (+1.67% a year employed, +3.49% hired) and budget-financed services fall on the employed basis (-0.04%) and fall on the hired basis (-0.50%): E6 moves employment from the budget-financed bloc towards market services as other-services output grows, fast enough here to shrink the budget-financed bloc in absolute terms.
- **Construction**: FR1 has construction output changing -19.0% in 2026; construction employment changes -0.60% that year against +0.53% for the total — a dip, but a damped one (half weight on a small elasticity).

First version, for comparison: accommodation +2.42%, ICT +1.43%, construction +1.24% … trade +0.32%, total +0.53% on FR1's earlier path.

- **State** employment: 1,049.3 → 984.0 thousand (-1.28% a year; band -2.40% to -0.19%), share 20.6% → 18.7%.
- **Budget organisations** (σ = 0.909): 594.2 → 579.5 thousand (-0.50% a year; band -1.75% to +0.55%), 31.1% of employees in 2030.
- **Oil** employment, tax-record basis: 47.8 → 45.5 thousand (-0.97% a year; band -2.46% to +0.69%); statistical basis 30.9 → 29.4.

**Scenarios.** In 2030 FR1's scenarios differ by 22.0% in real oil GDP, 12.10% in non-oil GDP and 0.39% in employment; FR4's employment therefore differs by 0.39% (20.3 thousand). Oil employment separates by 17.3% (Adverse 40.7 vs Reform 47.8 thousand).

**Fan charts** (`FR4_fan_employment.csv`, `FR4_fan_summary_2030.csv`): 2,000 replications combining historical residual-path resampling (8 joint 6-year paths starting 2011–2018 across 18 equations, centred; E9 starts 2016–2020), parameter draws and FR1's 500 macro draws. Every point forecast lies inside its inter-quartile band (asserted in Part 17.5).

---

## 12. Levers and sensitivities (2030, baseline)

| Lever | 2030 effect |
|---|---|
| population growth 0.3pp lower | total -78.6 thousand (-1.5%); labour force -82.4 thousand (-1.5%); agriculture -27.9 thousand (-1.5%) |
| population growth 0.3pp higher | total +79.5 thousand (+1.5%); labour force +83.4 thousand (+1.5%); agriculture +28.2 thousand (+1.5%) |
| employee share +2pp by 2030 | hired +105.4 thousand (+5.7%); budget +32.7 thousand (+5.7%); nonbudget +72.7 thousand (+5.7%) |
| state share frozen at its 2024 level | state +119.9 thousand (+12.2%); nonstate -119.9 thousand (-2.8%) |
| budget = all hired in the 4 activities (kappa = 0.994, first version) | budget +53.9 thousand (+9.3%) |
| Tier 1 + industry: pure constant shares | hotel -1.8 thousand (-1.7%); ict -0.9 thousand (-1.5%); construction +2.9 thousand (+0.7%) |
| Tier 1 + industry: pooled output system alone | hotel +1.8 thousand (+1.7%); ict +0.9 thousand (+1.5%); construction -2.9 thousand (-0.7%) |
| Tier-1 driver: group-specific relative output share (not adopted) | hotel +6.5 thousand (+5.8%); ict -1.2 thousand (-1.9%); construction +4.4 thousand (+1.0%) |
| Tier-1 driver: group-specific income per capita (not adopted) | hotel +10.1 thousand (+9.1%); construction +17.9 thousand (+4.3%); industry +15.0 thousand (+3.5%) |
| SENSITIVITY ONLY: add-factors decay, fixed half-life 1 year (E6, E8) | market services -17.8 thousand (-3.3%); state +14.3 thousand (+1.4%); budget +4.7 thousand (+0.8%) |

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

`FR4.ipynb` — <!-- AUTO:cells -->119 cells (83 code, 36 markdown)<!-- /AUTO:cells -->, executes end to end with 0 errors. Its Part 20.2 cell regenerates this document's §8.1 cross-check gap, §11 and §12 from the run (between the `AUTO` markers), so those figures are never typed by hand.
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
## 15. v2 — equation registry, complete forecast table, scenario engine and robustness

*This section is rewritten on every run by Parts 21–26 of FR4.ipynb.*

**Equation registry** (`output/FR4_equations.json`, Part 21): every equation estimated in the notebook — **125** in total, of which **11** are used in the forecast. By block: A 9, B 37, C 31, D 5, E 1, R 42 (R — rejected/alternative specifications, A — aggregate block, B — tier-1 share system, C — within industry and services, D — institutional splits, E — shift-share). The registry re-estimates every equation independently with statsmodels on the same (y, X) and checks that the coefficients equal the notebook's own estimates (all match); diagnostics (DW, BG, JB, White, RESET, VIF, cointegration, difference form), recursive and leave-one-year-out estimates, Chow and CUSUM are added.

**Robustness verdicts** (`FR4_robustness_summary.csv`): all equations — stable 19, partly stable 40, unstable 66; used in the forecast — stable 4, partly stable 4, unstable 3. Fragile (unstable) forecast equations: `FR4.E5_pooled_emp` (recursive: sign of d_lo_sq flips in the last half; leave-one-year-out: sign of d_lo_sq flips); `FR4.E6_emp` (recursive: sign of d2010 flips in the last half; Chow 2012 (midpoint) p = 0.000; Chow 2015 (2015) p = 0.000; Chow 2020 (2020) p = 0.000; CUSUM p = 0.022); `FR4.E6_hired` (Chow 2012 (midpoint) p = 0.034; Chow 2015 (2015) p = 0.012; Chow 2020 (2020) p = 0.000). Of the 73 level equations with a cointegration test, cointegration is established at 10% in only 11 — the t-statistics are mostly descriptive (consistent with Part 19.4). In the R9 industry panel the wage elasticity is -0.128: Driscoll–Kraay p = 0.508, wild-cluster bootstrap (by year, Webb) p = 0.544; the output elasticity's bootstrap p-value is 0.066 (DK: 0.031).

**Complete forecast table** (`FR4_forecast_tidy.csv`): 75 components × 3 scenarios, history from the first available year, 2025 (nowcast) and 2026–2030; completeness is checked (1125 values). The 8 groups and the two service blocs are now given for all three scenarios (before, the groups were only in the Baseline fan table). Bands (5–95%) for 14 series in the Baseline. Not forecast, with the reasons: `FR4_not_forecast.csv` (15 series: the broken Employment Agency series, the split by activity of the tax register, DVX r130/r107, regions). Catalogue: `FR4_indicator_catalog.csv` (ids `fr4:emp:<activity>`, `fr4:hired:<activity>`, `fr4:<base>:grp:<group>`, `fr4:<base>:bloc:pub|mkt`, `fr4:state`, `fr4:budget`, `fr4:oil:stat|tax`, `fr4:lf`, `fr4:phi` etc.).

**Scenario engine** (`microlib/engines/fr4.py`, state `output/engine/FR4_state.json`): reproduces the notebook's solution in Parts 15–17. Editable inputs: 16 exogenous FR1 paths (`fr1:emp`, `fr1:lf`, `fr1:pop`, `fr1:rgdpnon`, `fr1:rgdpoil`, 11 `fr1:rva_*`), 10 coefficients (the pooled βs, the pooling weights, E6, E8, E9) and 7 levers (population growth, hired share, state share trend/frozen, σ/κ, add-factor decay). With `upstream={"FR1": ...}` the FR1 engine's paths are used; FR3 is not used in the forecast. Self-test: in every scenario the notebook CSVs are reproduced with a maximum relative difference of 3.8e-16, and so is the lever table of Part 18 (34 values); one scenario ~16 ms.

**Coefficient sensitivity** (`FR4_coef_sensitivity.csv`, ±1 standard error, 2030, Baseline): state employment — `FR4.E8_state|trend` gives -0.54% / +0.54%; budget organisations — `FR4.E6_hired|ln_rva_oth` gives +0.87% / -0.88%; the three largest groups (Agriculture, forestry & fishing, Other services (9 activities), Trade & repair) are most sensitive to the pooling weight (±0.25, as the weight has no SE) — Agriculture, forestry & fishing ±0.07%, Other services (9 activities) ±0.09%, Trade & repair ±0.06%. Total employment comes from FR1 and does not depend on FR4's coefficients.

New files: `FR4_equations.json`, `FR4_indicator_catalog.csv`, `FR4_forecast_tidy.csv`, `FR4_not_forecast.csv`, `FR4_robustness_summary.csv`, `FR4_coef_sensitivity.csv`, `FR4_strings_az.csv` (the Azerbaijani equivalent of every user-visible English string, 438 strings), `engine/FR4_state.json` (plain data only). Every CSV from before v2 is unchanged (regression check).

<!-- /AUTO:v2 -->

<!-- v2.1-begin -->
## 16. v2.1 (2026-10-05) — Driscoll–Kraay p-values on t(T−1)

**Defect.** In `FR4_equations.json` the p-values of the Driscoll–Kraay panel equations came from t(n−k) (n = unit-years) while their
confidence intervals used t(T−1) (T = number of years, the DK time clusters) — e.g. `FR4.E4_pooled_emp`: p = 0.028 under t(n−k),
0.037 under t(T−1). The notebook's own `panel_fe` (Part 8) also reported t(n−k) p-values.

**Fix.** `panel_fe` now computes p-values from t(T−1), the convention of FR1, FR3 and the registry (microlib convention 7);
coefficients, standard errors (DK, 2 lags, n/(n−k) scaling) and t-statistics are unchanged. The registry receives these p-values
(`fit_p`) and the export cell asserts, for every DK coefficient, that the registry p equals the notebook p, equals
2·P(t<sub>T−1</sub> > |t|) and that the interval uses the same t(T−1) quantile. No forecast, selection or rejection decision uses
these p-values (decisions use t-statistics, signs and out-of-sample tests), so no CSV changes; only `FR4_equations.json`, the
R9 note and §15 above change.

| Equation | coefficient | T−1 | t | p before (t(n−k)) | p after (t(T−1)) |
|---|---|---|---|---|---|
| C1_real_lvl = E4_panel_hired_lvl | lo_sq | 24 | 5.99 | 1.3e-08 | 3.5e-06 |
| C1_real_diff = E4_panel_hired_fd | d_lo_sq | 23 | 5.80 | 3.4e-08 | 6.5e-06 |
| C1_nom_lvl | lo_sq | 19 | 2.68 | 0.0083 | 0.0148 |
| C1_nom_diff | d_lo_sq | 18 | 4.36 | 0.00003 | 0.00038 |
| R9_wage_panel | ln_real_output | 9 | 2.55 | 0.0114 | 0.0313 |
| R9_wage_panel | ln_real_wage | 9 | −0.69 | 0.491 | 0.508 |
| E4_pooled_emp | d_lo_sq | 22 | 2.22 | 0.0279 | 0.0371 |
| E4_panel_emp_fd | d_lo_sq | 23 | 2.31 | 0.0223 | 0.0303 |
| E4_pooled_hired | d_lo_sq | 22 | 5.91 | 2.1e-08 | 6.0e-06 |
| E4_panel_hired_lvl_tw | lo_sq | 24 | 3.77 | 0.00024 | 0.00093 |
| E5_pooled_emp | d_lo_sq | 13 | 0.64 | 0.527 | 0.535 |
| E5_pooled_hired | d_lo_sq | 13 | 0.82 | 0.416 | 0.426 |
| E4_panel_emp_lvl, E4_panel_emp_lvl_tw | lo_sq | 24 | 12.7, 13.5 | < 1e-15 | 4.1e-12, 1.1e-12 |

No significance verdict at 5% changes (C1_nom_lvl moves from the 1% to the 5% band). FR4's employment forecasts changed in this
run only because FR1 v2.1 changed its inputs (`FR1_forecast_full.csv`, `FR1_fan_draws.csv`; see the FR1 v2.1 note).
<!-- v2.1-end -->

---

<!-- AUTO:fr4v22_note -->
## 17. v2.2 (2026-10-05) — data from the Ministry's macro module

**State employment (E8).** Structural alternatives without a trend or own lags, scored like E8 (origins 2011–2014 scored ≤ 2019;
hold-out 2020–2024 × the simulated total): real government final consumption per head (MOE SNA `GC`, 1995–2024, from
`data/macro_module/fr345_moe_spec_panel.csv`), its ratio to real non-oil GDP, real non-oil GDP per head, and a composition model
(activity state shares from DSK `Dynamics_2.12` held at the origin × the activity hired forecast). File `FR4_e8_structural_candidates.csv`.

| specification | selection RMSE % | DM p vs trend | hold-out U (RW) | U (CG) | level / difference coefficient | decision |
|---|---|---|---|---|---|---|
| trend (E8, used) | 2.73 | nan | 0.60 | 0.81 |  | used |
| C composition (activity state shares) | 5.15 | 0.162 | 1.50 | 2.05 |  | rejected |
| G3 non-oil GDP per head | 6.11 | 0.315 | 1.23 | 1.68 | -0.402 (t -3.8); diff +0.076 (t +0.6) | rejected |
| G1 government consumption per head | 6.97 | 0.305 | 0.96 | 1.31 | -0.296 (t -5.5); diff -0.020 (t -0.3) | rejected |
| G2 government consumption / non-oil GDP | 10.35 | 0.129 | 1.07 | 1.46 | -1.209 (t -4.7); diff -0.038 (t -0.5) | rejected |

**None beats the trend** (U 0.60 / 0.81); the fiscal and output drivers are negative in levels (the share falls as
they rise — both trend) and insignificant in differences, and the composition model misses the privatisation inside activities
(state shares fell in 17 of 19 activities 2005–2024). E8 stays the logistic trend presented as a policy lever; the three
regressions are registered as `FR4.E8_alt_G1–G3` (rejected).

**Budget organisations (σ).** `data/dsk/002_12-13en.xls` already holds `Dynamics_2.12` (2005–2024); FR4 had read only the 2023 and
2024 sheets. σ is now observed every year (0.9586 in 2005, 0.9384 in 2019, 0.9092 in 2024; `FR4_budget_sigma_history.csv`), so the
2005–2022 budget history is no longer imputed (1999–2004 dropped: no σ). On origins 2010–2019 holding the last published year beats
the two-year mean (budget-employment RMSE 1.46% vs 1.59%), which is also the anchoring rule of the other
modules: **σ = 0.9092** (was 0.913). Baseline budget employment 594.2 thousand in 2025 (DVX r130: 588.0) and
579.5 in 2030 (was 579.5, +0.00%); state employment unchanged (984.0 thousand in 2030).

**Sector employment.** The 19 activities already run 1999–2024 (DSK 2.1 / 2.8); the macro module's `L_*` series and DSK 2.12 add
no longer history, so the sector equations are unchanged.
<!-- /AUTO:fr4v22_note -->

<!-- AUTO:fr4v23_note -->
## 18. v2.3 (2026-10-05) — add-factor decay with a fixed half-life (no estimated residual AR)

The client's constraint excludes any estimated residual-AR process. Up to v2.2 the Part 18 sensitivity "add-factors decay" let
the E6 bloc-split and E8 state-share add-factors fade at each equation's estimated first-order residual autocorrelation ρ̂
(E6 employed 0.85, hired 0.63; E8 0.52) — an estimated AR(1) coefficient inside a scenario path. From v2.3 the
decay is **fixed, not estimated**: the add-factor is multiplied by 0.5^(h/H), h = years after the anchor year (2024), with
half-life **H = 1 year** (0.50 a year) — the project's partial-year (nowcast) rule, as in FR1 and FR3. H is an engine lever
(`addfactor_half_life`, 0.25–10 years; it acts only with `addfactor_decay` on). ρ̂ remains a reported diagnostic (beside DW and
BG) and enters no forecast, scenario or sensitivity path; `FR4_add_factors.csv` lists the half-life and the yearly factor instead.
The Baseline, Adverse and Reform scenarios keep constant add-factors and are unchanged. Decay sensitivity, 2030 vs Baseline
(thousand persons):

| quantity | v2.2: decay at ρ̂ | v2.3: half-life 1 year |
|---|---|---|
| state employment | +14.2 (+1.44%) | +14.3 (+1.45%) |
| budget organisations | +4.5 (+0.79%) | +4.7 (+0.81%) |
| market services | −11.4 (−2.09%) | −17.8 (−3.26%) |
| services (total) | 0.0 (0.00%) | 0.0 (0.00%) |

The fixed decay is faster than ρ̂, so more of E6's 2024 add-factor is gone by 2030 and market services move further; the state-share effect hardly changes (E8's ρ̂ was close to 0.5).
<!-- /AUTO:fr4v23_note -->
