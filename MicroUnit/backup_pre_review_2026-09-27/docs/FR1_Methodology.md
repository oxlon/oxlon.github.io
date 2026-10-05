# FR1 — Structural Econometric Methodology for Sector and Market Analysis and Five-Year Forecasting

**Module:** 15.5.2 Microeconomic analysis and forecasting
**Requirement:** FR1 — *deep analysis of economic sectors and markets; forecasting of sector-specific dynamics and trends*
**Model:** AZSEM-FR1 (Azerbaijan Structural Econometric Model, Forecast Round 1)
**Data source:** `Statistik data dinamika 05.06.2026 +.xlsx` (41 sheets, Ministry of Economy statistical dynamics database)
**Vintage:** annual actuals through 2025; cumulative monthly actuals through April 2026
**Forecast horizon:** 2026–2030
**Implementation:** `FR1.ipynb` (runs end to end; 64 code cells, no errors)
**Outputs:** 29 CSV files in `MicroUnit/output/`

---

## 0. Requirement traceability

FR1 requires *"structural, dynamic and multivariate econometric models prepared for each of these sectors, analysed both
separately and jointly, and forecast"*, with the sector partition following the State Statistics Committee (DSK)
classification. AZSEM-FR1 implements that partition exactly:

| FR1 sector (Azerbaijani) | Code | Treatment in the model |
|---|---|---|
| Sənaye — mədənçıxarma | `min` | Volume-determined; constant returns imposed and tested |
| Sənaye — emal sənayesi | `man` | Capacity + construction + export demand |
| Sənaye — elektrik enerjisi, qaz və buxar | `elc` | Derived demand from non-oil activity |
| Sənaye — su təchizatı, tullantıların emalı | `wat` | Per-capita utility demand |
| *Qeyri-neft-qaz sənayesi* | — | Aggregation of the non-hydrocarbon industrial components |
| Kənd, meşə və balıqçılıq təsərrüfatları | `agr` | Capital + trend; credit elasticity from the regional panel |
| Tikinti | `con` | Public and private investment |
| Ticarət; nəqliyyat vasitələrinin təmiri | `trd` | Consumption, unit elasticity imposed and tested |
| Nəqliyyat və anbar təsərrüfatı | `tra` | Non-oil activity + trend |
| Turistlərin yerləşdirilməsi və ictimai iaşə | `tou` | Per-capita disposable income + trend |
| İnformasiya və rabitə | `ict` | ICT capital deepening per capita + trend |
| Sosial və digər xidmətlər | `oth` | Per-capita disposable income + trend |
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

Four constructs involve lags or autoregressive arithmetic and are **not** autoregressive models. Each is flagged in the
notebook where it appears:

| Construct | Why it is not an AR model |
|---|---|
| `K_t = (1−δ)K_{t−1} + I_t` | National-accounting identity; δ is **imposed**, nothing is fitted |
| `cpi_t = cpi_{t−1}(1+π_t)` | A price *level* cumulating an estimated *rate* |
| `debt_t = debt_{t−1} − balance_t` | Stock-flow accounting |
| Chain-linked aggregation | The official aggregator requires last year's nominal weights |

Newey–West **HAC standard errors** correct inference only; they never change a fitted value or a forecast. **ADF/KPSS tests** are
specification pre-tests that choose between a cointegrating and a differenced estimator; they can be deleted without changing
any forecast number.

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
   therefore addressed by **(sheet, row)**, and all 194 addresses are asserted against their expected label and unit at build
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
| Industry sub-branch panel (27 branches) | 2016–2025 | 270 |
| Regional panel (14 economic regions) | 2021–2025 | 70 |

Series with fewer than about ten annual observations (import/export price indices, export diversification indices, VAT) are
excluded from core equations and used only as diagnostics or scenario inputs. A five-observation regressor cannot identify a
structural elasticity.

### 2.3 Audited identities — four real problems found

Twenty-four identities are tested before estimation; nineteen hold to within 0.1%. Four discrepancies were investigated, and
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

### 2.4 Derived variables

- **Population** recovered as `GDP / GDP per capita` — 10.24m in 2025, a series not otherwise in the file.
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

Roughly 33 behavioural equations and 12 identities in eight blocks, 46 endogenous variables solved simultaneously each year.

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

Price-taking and volume-constrained. Estimated: oil export price on Brent, **elasticity 1.14, R² 0.976** (near-complete
pass-through); mining real value added on oil and gas volumes, **0.80 / 0.20** with constant returns imposed after testing;
hydrocarbon goods exports from volume × price.

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

- **Consumption** — liquidity-constrained permanent income: per-capita disposable income (elasticity 1.34), household credit,
  real lending rate.
- **Investment** — flexible accelerator on non-oil output and public investment, with the credit elasticity transferred from the
  regional panel and entering in **levels** relative to the base year, so a permanent credit expansion has a permanent effect.
- **Public investment (F4)** — real state investment on real oil revenue, elasticity **0.98**, unit elasticity not rejected
  (p = 0.916). This is the channel through which the oil price reaches the non-oil economy. Without it an oil price shock changes
  budget revenue and nothing else, which an earlier version of this model did and which is clearly wrong for Azerbaijan.
- **Non-oil revenue** — buoyancy 0.96 with respect to non-oil GDP, unit buoyancy not rejected (p = 0.793), plus imports.
- **Inflation** — a structural cost markup: exchange-rate change and wage growth, both correctly signed and significant.
- **Deflators** — each sector's deflator inflation on CPI inflation, with mining additionally on the manat oil price
  (coefficient 0.94). The GDP deflator: CPI 0.93 and oil price 0.30, R² 0.78. This closes the nominal side.
- **Sectoral credit allocation** — a share system estimated by SUR with adding-up imposed.

---

## 4. Identification and estimation

### 4.1 Device 1 — restrictions tested, then imposed

Four restrictions pass and are imposed by **re-estimating under the restriction**, each buying back a degree of freedom:

| Restriction | Economic meaning | Wald p | Verdict |
|---|---|---|---|
| Trade VA elasticity to consumption = 1 | Trade margin a stable share of turnover | 0.246 | Imposed |
| Mining oil + gas elasticities = 1 | Constant returns in extraction | 0.321 | Imposed |
| Non-oil tax buoyancy = 1 | Stable effective tax base | 0.793 | Imposed |
| Public investment elasticity to oil revenue = 1 | Investment financed from the resource envelope | 0.916 | Imposed |

Unit population elasticity is additionally imposed on all per-capita equations and on labour force participation.

### 4.2 Device 2 — panel-to-aggregate parameter transfer

Two micro panels carry far more information than the annual series.

**Industry sub-branch panel** (27 branches × 2016–2025, 270 observations). Two-way fixed effects with Driscoll–Kraay standard
errors give a capital elasticity of **0.12** and a labour elasticity of **1.03**. Independently, the observed **labour share in
value added is 0.339 (median)**. The two disagree, and the disagreement is informative rather than a failure: with only ten
years of within-branch variation, value added moves nearly one-for-one with employment (labour hoarding; the
perpetual-inventory capital stock is still dominated by its initial condition), so the panel identifies a *short-run* response.
The income share identifies *long-run* technology under competitive factor pricing, and Azerbaijani industry is capital-intensive
(refining, chemicals, metals). The model therefore imposes **α_K = 0.66, α_L = 0.34** from the income share and reports the panel
estimate as short-run adjustment. Both are shown so the choice is visible.

**Regional panel** (14 economic regions × 2021–2025, 70 observations). Cross-region variation identifies financial elasticities
the aggregate cannot: credit elasticity of output **+0.134** (two-way FE) to **+0.422** (region FE only), of industrial output
**+0.682**, of agricultural output **+0.430**; construction on total investment **+0.518**.

**A genuine cross-validation.** Regional trade value added has elasticity **1.009** with respect to retail turnover, against
**0.98** with respect to consumption in the aggregate annual data. Two independent datasets, two estimators, the same structural
parameter. This is the strongest single piece of evidence in the model.

**Transfer caveat.** Two-way fixed effects identify *relative* (cross-sectional) elasticities purged of aggregate effects. The
regional tax elasticity is 0.30 against 0.96 in the aggregate, precisely because aggregate buoyancy is driven by the national
covariation that fixed effects remove. Only parameters plausibly invariant across the cross-section and the aggregate are
transferred: the credit elasticities are, the tax elasticity is **not**.

### 4.3 Devices 3 and 4 — parsimony and cointegrating estimation

Two to three theory-selected regressors per equation, with VIF and condition-number screening; equations with VIF above 10 are
exactly where restrictions and panel transfers are used instead of free estimates. Long-run relations use **Dynamic OLS
(Stock–Watson)**: the levels regression is augmented with leads and lags of the *differences of the regressors*, so the
dependent variable's own lags never appear. Residual stationarity is checked equation by equation (Engle–Granger), and
non-rejections are reported rather than hidden — at n = 16–26 that test has very low power.

### 4.4 Simultaneity

Identification rests on exclusion restrictions plus a genuinely exogenous instrument set: Brent, oil and gas volumes,
population, public investment, the policy rate, the minimum wage and lagged exogenous variables. (Lagged variables as
*instruments* is standard simultaneous-equation practice and introduces no autoregressive forecasting mechanism.) Estimation
escalates from 2SLS per equation to **3SLS** for the simultaneous core, with first-stage F, Sargan J and OLS-versus-2SLS
comparison reported for every equation. Where OLS and 2SLS are close, OLS is retained for its lower variance, which matters
greatly at n ≈ 20. The cross-equation covariance Σ estimated by 3SLS is reused to generate the forecast fan charts, so
uncertainty bands inherit the true co-movement of shocks.

---

## 5. Specifications that failed, and what was done instead

This section exists because a model is only as trustworthy as its disclosed failures. Each of these was tried, rejected on
evidence, and replaced — all documented in the notebook with the rejected output shown.

| What failed | Evidence | What the model does instead |
|---|---|---|
| **Output gap** in the inflation equation | Four measures tried. Freely estimated production function gives a *negative* labour elasticity; with panel factor shares imposed it implies −2.2% a year TFP and a drifting "gap"; a linear deterministic trend gap is insignificant; a segmented trend gap is significant but flips the exchange-rate coefficient negative because its breaks coincide with the devaluation. Real credit growth as a proxy enters *negatively*. | No demand-pressure term. Inflation is a pure cost markup. Activity still reaches inflation through endogenous wages, but a separate output-gap effect is **not** identified and the model says so. |
| **User cost of capital** in investment | Wrongly signed in all four measures (real lending rate, nominal, GDP-deflator-based, smoothed). State investment is ~47% of the total; with 20 observations and a pegged rate there is too little independent variation. | User cost excluded; the financial channel is identified from the regional panel instead. |
| **Policy-rate pass-through** to market rates | Wrongly signed. In 2016–17 the policy rate was raised to 15% defensively while lending rates *fell* (20.7% in 2010 → 16.4% in 2016): over this sample it is a crisis instrument, not a steering rate. | Lending rate on the **deposit rate** (pass-through 1.26, R² 0.77) plus an NPL risk premium; the deposit rate is a scenario variable. The policy rate acts on credit **quantities**, where it is correctly signed (−0.041, p = 0.0002). |
| **Labour demand in levels** | VIF above 20; extrapolated, it moved unemployment more than a percentage point in the first forecast year. | An Okun-type **employment-rate** relation: `ln(emp/lf)` on non-oil GDP per capita, elasticity 0.045, R² 0.80, single regressor. Measured unemployment has been 4.9–5.6% every year since 2010 except 2020. |
| **Free labour-force equation** | Population elasticity collapses to 0.05 with a 1.1%-a-year trend (VIF > 100), implying unemployment drifting up 3 pp. | Unit population elasticity imposed; only participation drift estimated (+0.045% a year). The participation rate is in fact flat: 52.3% in 2010, 52.6% in 2025. |
| **Import equation without relative price** | Investment coefficient *negative* — impossible where capital goods are nearly all imported. The 2015–16 devaluation compressed imports while investment moved. | A real-exchange-rate term added; the investment sign is restored and R² rises from 0.77 to 0.85. |
| **Hydrocarbon export value as a regression** | Elasticity of 1.285 on oil revenue — impossible, since value *is* volume × price. A unit error: volume in tonnes, price per barrel. | Replaced by an **identity** with the recovered 7.400 barrels-per-tonne conversion (exact) and a calibrated 1.007 ratio to the balance-of-payments measure. |
| **Mechanical resource rule for public investment** | Applying the estimated unit elasticity over a declining-oil horizon cuts real public investment ~30% by 2030 and produces a ~3%-of-GDP surplus — a projection of pro-cyclical austerity, not a neutral baseline, and not what a country with a sovereign wealth fund would do. | Public investment is set as a **policy level** (stated openly in each scenario) while oil-revenue *deviations* from the scenario's own reference path move it with the estimated elasticity — so the oil transmission channel operates at full strength in the multiplier experiments. |

Five solver-side errors found during development are also documented, because each produced plausible-looking but wrong
forecasts:

1. **Decaying add-factors** injected a spurious growth swing (+18% then −18% real GDP). Constant adjustments are correct, since
   they represent persistent intercept errors.
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
are implemented directly and **validated against `statsmodels` to machine precision** (max difference ~1e-15 on coefficients
and standard errors, including HC1 and Newey–West HAC, 2SLS, 3SLS-equals-2SLS in the just-identified case, and the panel
within-transform). The Wald machinery is checked against a known true parameter.

### 6.2 Dynamic ex-post hold-out, 2021–2025 — the binding test

Every equation is re-estimated **on data through 2020 only**; the full system is then solved **dynamically** for 2021–2025, each
year's solution feeding the next, with only actual *exogenous* paths supplied. The window spans the pandemic rebound, the 2022
energy shock and the 2023–25 normalisation.

| | Result |
|---|---|
| Beats a random walk | **12 of 13** variables |
| Beats constant historical growth | 2 of 13 |
| Median Theil U vs random walk | **0.64** |
| Real GDP level error after 5 years | **−13.6%** |
| Real non-oil GDP level error after 5 years | −16.7% |

**The error pattern is the most informative output.** Tracked well (RMSE under 8%): agriculture 3.6%, employment 3.3%,
trade 7.4%, non-oil investment 7.8%. Tracked poorly (RMSE over 20%): manufacturing 24.0%, construction 24.9%,
transport 24.6%, nominal GDP 30.4%.

The split is not random. The model tracks **demand-determined** variables well, because their drivers are in the model and
behaved as estimated. It under-predicts **manufacturing, construction and transport** by roughly 30% — precisely the sectors
that went through a post-2020 *supply-side* transformation that coefficients estimated to 2020 could not know about: new
manufacturing capacity, the Karabakh and East Zangezur reconstruction programme, and the Middle Corridor transit build-out.
Manufacturing real value added is up 86% since 2015; no relationship fitted on pre-2020 data anticipates that.

**Reading:** the model is usable for the demand side and for policy transmission. Its sector forecasts for manufacturing,
construction and transport are conditional on no repeat of that kind of capacity shock, and should be read with that caveat.

### 6.3 Other checks

Per equation: sign and magnitude against theory; HAC-corrected significance; Engle–Granger residual stationarity;
heteroskedasticity; normality; VIF; and Chow tests at 2015, 2020 and 2022 (8 of 16 tested coefficient sets show instability,
reported openly). System-wide: identity closure to numerical tolerance, and convergence with iteration counts reported for
every solved year.

---

## 7. Solution, anchoring and forecasting

### 7.1 Solver

Each year is solved by **damped Gauss–Seidel** iteration to a fixed point (residual < 1e-10, typically 120–155 iterations),
with identities imposed exactly at every iteration.

### 7.2 Anchoring 2026 on observed data

2026 is four months observed, and that information is used rather than discarded. All twelve GDP components have published
year-to-date real growth indices, and each is used as an anchoring target through constant adjustments, iterated to convergence
(the system is simultaneous, so one adjustment step does not hit the targets). Hydrocarbon **volumes** for 2026 are taken from
the year-to-date outturn rather than from the scenario's assumed decline, because for a partly-observed year the data are better
information than an assumption; the scenario's decline rates resume from 2027.

The anchoring matches every target to within **0.5%**, and this yields a genuine consistency test: the model's own
chain-linked 2026 aggregate can be compared with the **published** aggregate index.

| | Published YTD | Model 2026 | Difference |
|---|---|---|---|
| Real GDP growth | +0.20% | +0.24% | 0.04 pp |
| Real non-oil GDP growth | +0.70% | +0.66% | −0.04 pp |

Two data tensions are passed to the user rather than smoothed away: construction contracting 19% while total investment rises
15% (a composition shift out of construction works into largely imported equipment), and a steep Q1 fall in both exports and
imports.

### 7.3 Scenarios

Because hydrocarbons are exogenous, the forecast is scenario-conditional by construction — a feature that forces assumptions
into the open. Calibrated on the 2025 starting point (Brent 69.1, oil 27.68 mt, gas 50.92 bcm, FX 1.70, policy rate 6.75%):

| Driver | Baseline | Adverse | Reform |
|---|---|---|---|
| Brent by 2030 | ~66 USD/bbl | ~48 | ~80 |
| Oil output | −4.5% p.a. decelerating | −6.5% p.a. | −3.0% p.a. |
| Gas output | +1.0% p.a. (plateau) | flat | +4.0% p.a. |
| Gas export price | → 300 USD/kcm | 230 | 380 |
| Public investment (policy level, real) | +1.5% p.a. | −4% p.a. | +5% p.a. |
| Policy / deposit rate | easing | tightening | easing |
| Exchange rate | 1.70 | 1.70 | 1.70 |
| External demand | +3% p.a. | +0.5% p.a. | +5% p.a. |

### 7.4 Headline results

| | Baseline | Adverse | Reform |
|---|---|---|---|
| Real GDP growth, avg % p.a. 2026–30 | **1.23** | 0.86 | 1.39 |
| Real non-oil GDP growth, avg % p.a. | **2.35** | 2.07 | 2.42 |
| CPI inflation 2030, % | 4.13 | 4.11 | 4.19 |
| Unemployment 2030, % | 4.78 | 4.83 | 4.76 |
| Budget balance 2030, % of GDP | −0.88 | +0.27 | −1.66 |
| Public debt 2030, % of GDP | 24.4 | 24.6 | 25.0 |
| Hydrocarbon share of value added 2030, % | 15.9 | 11.0 | 19.1 |
| Nominal GDP 2030, bn AZN | 164 | 153 | 172 |

**The clearest structural result:** the hydrocarbon share of value added falls from 25.6% to 15.9% in the baseline, not because
non-oil growth is fast but because oil volumes decline while non-oil sectors grow modestly. Diversification here is arithmetic
as much as achievement — a point worth making explicitly to policy readers.

### 7.5 Uncertainty

Fan charts come from resampling the **vector** of estimated structural residuals across 16 equations, preserving the
contemporaneous cross-equation covariance, plus parameter uncertainty; 400 replications, all converged. No conditional-variance
model is used or needed.

### 7.6 Multipliers — the FR1 answer on inter-sector transmission

Each experiment shocks one exogenous driver in the **solved** system. Deviations from baseline by 2030, in per cent:

| | Brent +10 USD/bbl | Public investment +1 bn AZN | Credit easing | External demand +10% |
|---|---|---|---|---|
| Construction | +1.87 | **+3.04** | +1.21 | +0.09 |
| Manufacturing | +0.60 | +1.02 | +0.14 | **+3.00** |
| Trade | −0.04 | +0.50 | **+1.90** | +0.25 |
| Transport | +0.15 | +0.39 | +0.41 | +0.23 |
| ICT | +1.85 | +3.18 | +0.37 | +0.01 |
| Real non-oil GDP | +0.21 | +0.52 | +0.68 | +0.38 |
| Consumption | −0.10 | +0.31 | +1.90 | +0.26 |
| Budget revenue | +5.65 | +1.09 | +1.24 | +0.41 |

The sector ordering is exactly what theory predicts and is *derived*, not asserted: public investment hits **construction**
first, then manufacturing through building-materials demand, then trade and services through income; external demand hits
**manufacturing** (the export-exposed sector); credit easing hits **consumption and trade**. The implied fiscal multiplier on
real non-oil GDP is about **0.4**, below one because a large share of investment spending leaks into imports — visible directly
in the +2.3% import response.

**One result needs explaining, and is correct.** An oil price rise *lowers* chain-weighted real GDP (−0.25%) while raising every
non-oil sector and non-oil GDP (+0.21%). Real GDP is chain-linked with previous-year nominal weights, so a higher oil price
raises the mining *deflator* and hence mining's weight — and mining's volume is falling. Hydrocarbon volumes are exogenous, so
there is no offsetting volume effect. For welfare and policy the relevant numbers are non-oil GDP, consumption and budget
revenue, not the chain-weighted real aggregate. Any correctly built model of a commodity exporter shows this.

---

## 8. Complete accounts: five metrics for every sector and market

Part 16 of the notebook delivers the full account an analyst needs: for **49 entities** — the 12 DSK sectors, 7 aggregates,
4 consumer markets, 5 investment aggregates, 5 labour-market series, 4 credit and deposit series, 3 external-trade series,
7 fiscal series and 2 price indices — five aligned series over both history (2005–2025) and forecast (2026–2030), for all
three scenarios:

**real value · real growth rate · deflator · deflator inflation · nominal value**

linked by the identity `nominal = real × deflator`, verified numerically (max absolute error 7×10⁻¹²).

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
   0.01% on gas). The spurious elasticity had been *amplifying* the projected export decline: hydrocarbon exports fell 40% to
   2030 under the regression against 17% under the identity. B4 is now an identity with a calibrated ratio (1.007) linking the
   customs volume × price product to the broader balance-of-payments measure.
2. **Three equations were silently missing their constant adjustment** in the solver — household credit, deposits and
   hydrocarbon exports. The effect was visible once the accounts were tabulated: real household credit fell 20% in the first
   forecast year and then grew normally, an obvious level discontinuity. The notebook now carries an **automated self-check**
   that asserts every adjusted variable actually applies its term inside the solver, so this class of bug cannot recur silently.

### 8.4 Headline five-metric results, baseline

| | Real growth<br>% p.a. | Deflator infl.<br>% p.a. | Nominal growth<br>cum. % | Nominal 2030<br>mln AZN |
|---|---|---|---|---|
| **GDP** | +1.23 | +3.69 | +27.4 | 164,494 |
| **Non-oil GDP** | +2.35 | +5.54 | +47.0 | 135,722 |
| Oil and gas GDP | −2.84 | −2.01 | −21.8 | 28,771 |
| Information & communication | **+9.00** | −2.94 | +32.5 | 3,537 |
| Transport & storage | +4.82 | +0.72 | +31.1 | 11,942 |
| Tourism & catering | +4.64 | +4.53 | +56.6 | 5,595 |
| Agriculture | +3.14 | +3.04 | +35.6 | 10,370 |
| Manufacturing | +3.13 | +3.52 | +38.7 | 10,705 |
| Water supply & waste | +2.71 | +3.50 | +35.8 | 410 |
| Trade & vehicle repair | +2.18 | +5.80 | +47.7 | 21,595 |
| Social & other services | +1.63 | +8.97 | +66.7 | 46,767 |
| Electricity, gas & steam | +1.51 | +4.57 | +34.8 | 1,962 |
| Net taxes on products | +1.36 | +5.82 | +42.0 | 17,606 |
| Mining & quarrying | −2.27 | −2.39 | −21.0 | 26,156 |
| Construction | −3.07 | +1.97 | −5.7 | 7,949 |

**Why all five metrics matter, not just real growth.** The deflator varies enormously across sectors, so real and nominal
rankings differ sharply. ICT has the fastest real growth in the economy (+9.0% a year) but a *falling* deflator (−2.9%),
so its nominal value added grows only 32.5% — slower than social services, whose real growth is a fifth of ICT's but whose
deflator rises 9.0% a year. Mining's deflator falls with the oil price, compounding its volume decline into a 21% nominal
contraction. Since budget revenue, wage bills and credit demand are all paid out of *nominal* magnitudes, reporting real
growth alone would mislead on exactly the questions the model exists to answer.

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
   reported in the notebook.
7. **The exchange rate is a de facto peg** since 2017, so pass-through is identified almost entirely by the 2015–16 devaluation.
   Any scenario moving the rate extrapolates from a single episode.
8. **Sector investment deflators are not published**, so the aggregate investment deflator is applied to every sector.
9. **Chain-linked volumes are not additive**; the non-oil wedge uses a calibrated correction whose size is reported.
10. **Manufacturing, construction and transport forecasts are the weakest** (hold-out RMSE 23–24%), for the supply-side reasons
    in Section 6.2.
11. **Calibrated shares are held fixed** (sector investment shares, social-spending share, debt-service rate); structural change
    in these is not captured.
12. **Public investment's level is an assumption, not a forecast** (Section 5, last row). It should be set deliberately per
    exercise.

## 10. What would most improve the model

1. A **supply-use / input–output table** — replaces estimated linkages with measured ones and unlocks policy-module FR2.
2. **Employment and compensation by sector**, annual — completes the production-function block and serves FR3/FR4 directly.
3. **Partner-weighted external demand** and an import price index with history — properly identifies the trade block.
4. **Quarterly national accounts by sector** — roughly quadruples the effective sample, making dynamics estimable rather than imposed.
5. **A longer regional panel** — the cross-section is the model's best identification device and currently only five years deep.
