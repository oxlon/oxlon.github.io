# FR3 — Structural Econometric Methodology for Wage Analysis and Five-Year Forecasting

**Module:** 15.5.2 Microeconomic analysis and forecasting
**Requirement:** FR3 — *"Orta aylıq əmək haqqının (onların iqtisadiyyatın sahələri, dövlət və qeyri-dövlət sektoru, büdcə və
qeyri-büdcə təşkilatları, neft və qeyri-neft sektoru üzrə səviyyəsi və artım sürətləri) təhlili və proqnozlaşdırılması"* —
analysis and forecasting of the average monthly wage, its **level** and **growth rate**, by economic sector, state and non-state
sector, budget and non-budget organisations, and oil and non-oil sector.

**Model:** AZWAGE-FR3
**Source:** `Statistik data dinamika 05.06.2026 +.xlsx`
**Actuals:** annual through 2025; **monthly through February 2026** for every published wage series
**Forecast:** 2026–2030, on FR1's three macro scenarios
**Implementation:** `FR3.ipynb` (69 cells, 39 code, runs end to end with no errors)
**Outputs:** 11 CSV files in `MicroUnit/output/`

---

## 1. Headline finding: the four required breakdowns do not nest

This determines the architecture, and it is settled numerically before any modelling.

| Breakdown | Structure | Numerical verification |
|---|---|---|
| **State × non-state** | **Exact partition** of hired employees | Aggregate wage = employment-weighted average to **0.17–0.31%** |
| **Economic sectors** (8 DSK) | **Exact partition** of hired employees | Sector employment sums to the total **exactly (0.000)** |
| **Oil / non-oil** | **Cross-cutting**, not a third group | Treating it as a third group **double-counts by 6.7–10.4%** |
| **Budget / non-budget** | Sub-partition of the state sector, partly observable | Headcount and contributions observed; wage level **not** identifiable |

The double-counting result is the informative one: oil companies are *both* state (SOCAR) and private (the AIOC consortium), so
oil is a classification that cuts across the institutional split rather than sitting inside it. Adding it alongside state and
private counts oil employees twice, and since they earn 3.75× the average, inflates the implied mean by up to 10%.

**Consequence:** the model cannot be a single hierarchy. FR3 maintains **two independent exact aggregations** to the same
national average wage — by institution and by economic sector — and reconciles the oil dimension against them rather than
nesting it inside either.

---

## 2. A measurement issue that must be handled first

A wage is paid to a **hired employee** (*muzdla çalışan*). The workbook also reports **total employed persons**, which includes
the self-employed. In Azerbaijan these differ by a factor of 2.5: **2.06 million** hired against **5.11 million** employed in
2025, because agriculture and much of retail is self-employed.

| Wage bill, 2025 | mln AZN |
|---|---|
| wage × **hired** × 12 | 27,263 |
| DVX reported wage fund | 26,527 |
| compensation of employees (national accounts) | 38,227 |
| wage × **total employed** × 12 | **67,566** ← wrong by 2.5× |

The first two agree to 2.8%, which validates the concept. Hired employment is published only for 2021–2025, so for the
estimation sample it is **derived** from compensation of employees divided by the annual wage, with one calibrated wedge (1.429)
for employers' contributions and in-kind pay. It tracks the published series to within **3.2%** over the overlap.

**A correction owed to FR1:** FR1's household-income equation builds its wage bill on total employment, so that variable's level
is overstated. Because it enters in logs the error is absorbed by the intercept and the estimated elasticity is affected only
through the slow drift in the hired share, so FR1's results stand — but the variable is mislabelled and should be rebuilt.

---

## 3. Theory and the restrictions actually tested

The structural wage equation is

$$\ln W = \alpha + \beta \ln(\text{productivity}) + \gamma \ln P + \delta \ln(\text{minimum wage}) + \theta\,\text{tightness} + \sum_j \phi_j \ln W_j$$

Four implications are **tested**, not assumed.

### 3.1 Nominal homogeneity, γ = 1 — accepted and imposed

| Specification | CPI elasticity | Wald p | Verdict |
|---|---|---|---|
| productivity + CPI | 1.269 | 0.000 | rejected |
| productivity + CPI + minimum wage | **1.042** | **0.654** | **not rejected** |
| non-oil productivity + CPI + minimum wage | 0.578 | 0.000 | rejected (collinearity) |

Homogeneity is therefore imposed by estimating every equation in **real terms**. This is not a convenience: it is a restriction
the data accept, and it buys back one parameter per equation on samples of 21–26 observations.

### 3.2 Productivity elasticity, β = 1

| Equation | β | Wald p | Reading |
|---|---|---|---|
| Aggregate real wage | 0.693 | 0.000 | **rejected** — the labour share has fallen |
| Non-oil real wage | 0.864 | 0.088 | **not rejected** — non-oil real wages track productivity one-for-one |

### 3.3 Cross-wage spillovers — the "related sectors" mechanism

Three channels were tested. **All three were rejected**, and this is the substantive econometric result of FR3:

- **Oil-sector wage leadership** (the Dutch-disease channel). Significant in-sample on the full sample (+0.186, p = 0.048) and it
  raises R² from 0.856 to 0.895 — but the coefficient **flips sign** when estimated to 2020 (−0.015) and adding it makes the
  five-year out-of-sample error **worse** (19.7% against 15.7%). That is the signature of a relationship identified by a handful
  of recent observations, not a stable structure.
- **Public-sector wage leadership.** The private wage has no independent role in the state equation once fiscal capacity and the
  minimum wage are included (+0.009, p = 0.984).
- **Minimum wage in the private equation.** Significant but **negative** (−0.165, p = 0.007). The timing explains it: in 2018 the
  real minimum wage nearly doubled (104 → 197) in years when real private wages were still falling after the 2015–16
  devaluation, while real state wages were rising strongly. The 2018 reform was in substance a *public-sector* pay measure. It is
  excluded from the private equation, because a coefficient telling the Ministry that raising the wage floor cuts private pay is
  not acceptable in a model built for policy simulation.

### 3.4 Labour-market tightness — no channel exists

Unemployment enters positively in growth form and insignificantly in levels. Measured unemployment has stayed within
**4.9–5.6% every year except 2020**, so there is no variation to identify a Phillips relation. Dropped.

---

## 4. Specifications chosen on out-of-sample performance

In-sample fit pointed the wrong way in two cases, so specification choice is made by a **pseudo-out-of-sample test**: estimate
on 2005–2020, predict 2021–2025 using *actual* drivers, compare errors.

**Private real wage** — five candidates:

| Specification | in-sample R² | out-of-sample RMSE | chosen |
|---|---|---|---|
| **non-oil wage only** | 0.771 | **15.7%** | ✓ |
| productivity + minimum wage | 0.856 | 17.2% | |
| productivity only | 0.795 | 19.2% | |
| productivity + non-oil wage | 0.798 | 19.2% | |
| productivity + **oil wage** (Dutch disease) | **0.837** | **19.7%** ← worst | |

**State real wage** — three candidates:

| Specification | out-of-sample RMSE | chosen |
|---|---|---|
| **minimum wage + productivity** | **5.6%** | ✓ |
| minimum wage only | 10.2% | |
| fiscal capacity + minimum wage | 19.0% | |

The fiscal-capacity version is economically more appealing — it carries an explicit budget constraint — but forecasts three times
worse and starts only in 2010. Fiscal restraint is still simulable through the minimum wage, which is the instrument the
government actually uses to reset public pay.

**Oil real wage** — no specification works:

| Specification | out-of-sample RMSE |
|---|---|
| constant premium (unit elasticity to the non-oil wage) | 19.3% |
| premium on a linear trend | 54.2% |
| premium on a quadratic trend | 142.7% |

The premium rose from 3.2× (2010) to 6.6× (2017) and has fallen steadily to **3.75× (2025)**. No pre-2021 specification
anticipates the reversal, and trend extrapolations are far worse than assuming a constant premium. This is a **structural break
in oil-sector pay setting**. The constant-premium form is retained as least-bad, with two safeguards: the constant adjustment
anchors the premium on its *actual* latest value rather than a historical average, and the premium path is exposed as a
**scenario lever**.

---

## 5. The final equation set

| # | Dependent | Drivers | n | R² | Engle–Granger p |
|---|---|---|---|---|---|
| E1 | ln real average wage | productivity, real minimum wage | 26 | 0.975 | 0.13 |
| E2 | ln real non-oil wage | non-oil productivity, real minimum wage | 21 | 0.942 | 0.04 |
| E3 | ln real private wage | real non-oil wage | 21 | 0.771 | — |
| E4 | ln real state wage | real minimum wage, non-oil productivity | 21 | 0.915 | 0.10 |
| E5 | ln real oil wage | real non-oil wage (unit elasticity not rejected, p = 0.739) | 21 | 0.583 | 0.16 |
| P1 | ln minimum wage | ln average wage (elasticity 1.28 — reported, not used to forecast) | 26 | 0.962 | 0.03 |

CPI elasticity = 1 is imposed on all five by construction. Panel blocks support the levels form: both the 27-branch industry
panel and the 14-region panel give a *within* wage–productivity elasticity near 0.07, against a *cross-sectional* elasticity of
0.336 — year-to-year wage adjustment is weak while permanent productivity differences are paid, which is why the long-run
relation is estimated as a cointegrating levels relation rather than in growth rates.

---

## 6. Validation

**Estimators.** Identical to FR1's, reproduced for self-containment and revalidated against `statsmodels` to machine precision.

**Dynamic ex-post hold-out, 2021–2025.** Every equation re-estimated on data through 2020, then the system solved dynamically
with actual drivers and no wage fed back:

| Variable | model RMSE | Theil U vs random walk | 2025 level error |
|---|---|---|---|
| **average wage** | 9.1% | **0.37** | **+0.78%** |
| wage bill | 9.1% | 0.29 | +0.78% |
| state wage | 9.6% | 0.33 | +2.13% |
| non-oil wage | 12.4% | 0.47 | +8.35% |
| private wage | 18.9% | 1.01 | +17.2% |
| oil wage | 45.1% | **5.17** | +52.7% |

Beats a random walk on **4 of 6**; median Theil U **0.42**.

**The two failures are identifiable breaks, not diffuse error.** The oil wage error is almost entirely the premium: holding it at
its 2020 value of 5.14× when the actual fell to 3.75× over-predicts by ~37%, and the non-oil wage error compounds it. The private
wage error is the 2021–22 inflation spike, which squeezed real private pay in a way no pre-2021 relationship anticipates.

**Aggregation identity.** Rather than let the aggregate and component equations drift apart — an earlier version drifted to 3.8%
by 2030 — the aggregate *level* is taken from E1 (the best-forecasting equation) and component levels are backed out from the
ratio the component equations imply. The identity then holds **exactly (2×10⁻¹⁴%)** at every horizon, with a rebalancing factor of
0.977–1.000.

**2026 nowcast.** All five wage series have January–February 2026 observations. The workbook's monthly columns hold
*cumulative-period averages*, so the nowcast compares the same window year-on-year. The model is anchored on the result to within
**0.017%**.

| Series | 2025 | 2026 nowcast | growth |
|---|---|---|---|
| average wage | 1,102.9 | 1,161.6 | +5.32% |
| oil sector | 3,938.6 | 4,330.8 | +9.96% |
| non-oil sector | 1,050.7 | 1,105.3 | +5.20% |
| state sector | 1,080.8 | 1,152.4 | +6.62% |
| private sector | 1,124.4 | 1,168.5 | +3.92% |

---

## 7. Forecast results, 2026–2030

Macro drivers come from FR1's scenarios. FR3 adds two levers of its own: the **minimum wage** (6% / 3% / 9% nominal growth per
year) and the **oil premium path** (compressing to 3.4× / 3.2× / stabilising at 3.7×).

| Baseline | 2025 | 2030 | nominal % p.a. | real % p.a. |
|---|---|---|---|---|
| Average wage | 1,102.9 | 1,424.9 | **+5.26** | **+1.19** |
| Non-oil sector | 1,050.7 | 1,410.8 | +6.07 | +1.98 |
| State sector | 1,080.8 | 1,450.7 | +6.06 | +1.97 |
| Private sector | 1,124.4 | 1,404.4 | +4.55 | +0.51 |
| Oil sector | 3,938.6 | 4,796.8 | +4.02 | **0.00** |

| | Baseline | Adverse | Reform |
|---|---|---|---|
| Average wage, nominal % p.a. | 5.26 | 4.42 | 5.88 |
| Average wage, **real** % p.a. | 1.19 | 0.50 | 1.77 |
| Real private wage % p.a. | 0.51 | 0.06 | 0.87 |
| Real state wage % p.a. | 1.97 | 0.98 | 2.81 |

**Two results worth flagging to policy readers.** First, the **state/private ratio crosses 1.0 in 2027**, completing a two-decade
catch-up from 0.46 in 2005 — public pay overtakes private pay. Second, the **real oil wage is flat** in the baseline, so the
premium compression continues; that is an assumption, and the lever to change it is exposed.

**Decomposition.** The exact shift-share identity attributes almost all historical growth to the **within** term — pay rising
inside both groups — with a small *negative* **between** term, as employment shifted toward the non-state sector while the two
were still converging.

---

## 8. What the data cannot deliver

### 8.1 Average wages by economic sector — not derivable

The first breakdown FR3 names is the one the workbook does not publish. Two derivations were attempted and both rejected:

**Attempt 1** — allocate wages by value added per hired worker, anchored so the employment-weighted average reproduces the
national wage. Rejected on two independent grounds:

- the derived **industry** wage is **31–51% above** the actual one, because industrial value added per worker (216 thousand AZN)
  is largely oil and gas **rent** accruing to capital and the budget, not to the 197 thousand industrial employees;
- it makes **agriculture the best-paid sector at 1.45× the average**, because agricultural value added is 7.6 bn AZN but only
  **50 of roughly 1,000 thousand** agricultural workers are *hired* — the output is produced by the self-employed.

**Attempt 2** — strip the resource rent and search for the elasticity that fits industry. An elasticity can always be found that
fits one target, but the same value still puts agriculture far above the national average. Fitting one sector while ignoring what
it does to the others is curve-fitting, not identification.

**Delivered instead:** industrial wages at **2-digit level (27 sub-branches, published data)**, forecast structurally; a full
forecast of **hired-employment composition for all eight sectors**; and the exact decomposition machinery ready to quantify the
reallocation effect once sector wages exist.

**What would fix it:** a sector breakdown of the **wage fund** (*əmək haqqı fondu*) or of compensation of employees. The State Tax
Service already publishes the *total* wage fund alongside sector employment and sector turnover in this very sheet, so this is a
data request, not a modelling problem.

### 8.2 Budget versus non-budget average wages — not identifiable

Contributions and headcount are observed; converting contributions into a wage bill needs the **differentiated statutory rates**,
which are not in the workbook. The employer rate is recoverable from the budget's own accounts — 212100 ÷ the 211xxx pay lines
gives 0.219, confirming the statutory 22% — but applying it to DVX budget-organisation contributions gives a wage that varies by
about a third across plausible rate assumptions, and **every variant puts the budget wage above the non-budget wage**, whereas
the published state wage sits *below* the published private wage. That contradiction is the signature of the non-oil private
sector's reduced regime, which makes its contributions understate its payroll.

The budget/non-budget split is therefore reported as **observables** — headcount (588 thousand, 29% of hired employees) and
contributions (34% of the total) — and not as a forecast average wage.

Note also that the fiscal 211xxx pay lines (3,775 mln AZN in 2025) **cannot** be the economy-wide budget payroll: education
spending alone is 4,618 mln and is mostly pay. Those lines cover only the institutions inside that block.

### 8.3 A data error found in the source

Rows **127–129** of the DVX sheet — budget-organisation taxpayer count, turnover and receipts — are **byte-identical** to rows
123–125 (micro taxpayers). Only the employee count in row 130 is genuine. Rows 127–129 are discarded, and this should be
reported to the data provider.

---

## 9. Limitations

1. Sector average wages not published and not derivable (§8.1).
2. Budget/non-budget average wages not identifiable (§8.2).
3. Source data error in DVX rows 127–129 (§8.3).
4. The **oil wage** is the weakest equation: no fundamental explains it, the premium break is unpredictable, and a random walk
   beats the model (Theil U 5.17). The premium is a stated scenario lever.
5. The **private wage** barely beats a random walk (Theil U 1.01), because of the 2021–22 real-wage squeeze.
6. The **minimum wage has no credible private-sector effect** in this data, so minimum-wage simulations work through the state
   sector and the aggregate and understate any true private effect.
7. **No tightness channel** — unemployment has no usable variation.
8. **Hired employment before 2021 is derived**, not observed (tracks the published series to 3.2%).
9. **Short samples:** 21 annual observations for the component equations, 16 for the fiscal variant, 5 for the DVX employment and
   contribution series, 5 years for the regional panel.
10. **Employment composition is held fixed** beyond 2026 — the state share, branch structure within industry, and the hired
    share of total employment — so the between-group term is zero by construction and this is a forecast of pay rates, not of
    workforce restructuring.
11. **FR3 inherits FR1's macro uncertainty**; FR1's own five-year hold-out error on real GDP is about −13%.
12. The **two source systems disagree by −4% to +2%** on the average wage (DSK survey versus DVX tax records). FR3 forecasts the
    DSK series and uses DVX only for employment weights.

## 10. What would most improve FR3

1. **Sector wage funds or compensation of employees by sector** — unlocks the largest gap, which is the first breakdown FR3 asks for.
2. **The statutory contribution-rate schedule by segment**, or the budget-organisation wage fund — closes the budget/non-budget breakdown.
3. **Hired employment by sector and institution back to 2005** — would let the identities and the decomposition run over the whole estimation sample rather than five years.
4. **A published median wage or wage distribution** — the average alone cannot show the minimum wage's compression effects, which this analysis shows are central to how Azerbaijani pay is actually set.
