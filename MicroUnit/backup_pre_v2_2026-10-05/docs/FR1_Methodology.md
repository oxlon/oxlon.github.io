# FR1 — Structural Econometric Methodology for Sector and Market Analysis and Five-Year Forecasting

**Module:** 15.5.2 Microeconomic analysis and forecasting
**Requirement:** FR1 — *deep analysis of economic sectors and markets; forecasting of sector-specific dynamics and trends*
**Model:** AZSEM-FR1 (Azerbaijan Structural Econometric Model, Forecast Round 1)
**Data source:** `Statistik data dinamika 05.06.2026 +.xlsx` (41 sheets, Ministry of Economy statistical dynamics database)
**Vintage:** annual actuals through 2025; cumulative monthly actuals through April 2026
**Forecast horizon:** 2026–2030
**Implementation:** `FR1.ipynb` (runs end to end; 64 code cells, no errors)
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
| Constant base add-factors | Each equation's own 2025 residual, held fixed — consistent with the finding that residuals are generally **not** shown to be stationary; a sensitivity decays them at each residual's autocorrelation ρ̂ |
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

### 2.3 Audited identities — four real problems found

Twenty-four identities are tested before estimation (tolerance 1%, 5% for the budget balance and unemployment identities);
nineteen hold. Four discrepancies were investigated, and
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
- **Household income (E3)** — a share relation: ln(income / pension bill) on ln(non-oil GDP / pension bill), elasticity 0.89 on
  non-oil GDP and 0.11 on the pension bill (homogeneity not rejected, p = 0.12, imposed). Non-oil GDP stands for all market income
  (wages, entrepreneurial and property income). The pension bill is a **proxy**: average pension × total population (the workbook
  has no count of pensioners). Pensions are a policy variable, CPI-indexed in the forecast.
- **Investment** — accelerator on non-oil output (0.20) and state investment (0.89). No credit term: its free estimate is wrongly
  signed and the regional-panel value is rejected by the aggregate data.
- **Public investment (F4)** — real state investment on real oil revenue, estimate 0.90; unit elasticity **not rejected (low
  power**: p = 0.76, s.e. 0.31) and imposed.
- **Non-oil revenue** — long-run buoyancy 1.32 w.r.t. non-oil GDP; unit buoyancy not rejected (low power: p = 0.12, s.e. 0.19)
  and imposed, plus imports (0.56).
- **Credit (G1)** — real deposits (0.52) and the policy rate (−0.043); non-oil GDP removed (wrong sign, −0.67).
- **Inflation** — a structural cost markup: exchange-rate change (0.057) and wage growth (0.31), both significant only at 10%
  (R² 0.20): the weakest-fitting equation, which is why the CPI fan is wide.
- **Deflators** — each sector's deflator inflation on CPI inflation (mining also on the manat oil price). For social & other
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
| Household income: non-oil GDP + pension elasticities = 1 | 0.631 | 0.118 | 0.222 | Not rejected (low power) — imposed |
| Social-services deflator: pass-through 1 (drift free) | 0.59 | 0.222 | — | Not rejected — imposed (no-drift joint test rejected, p = 0.001) |
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
| **Import equation without relative price** | Investment coefficient *negative* — impossible where capital goods are nearly all imported. The 2015–16 devaluation compressed imports while investment moved. | A real-exchange-rate term added. It restores the sign only in static OLS; in the long-run DOLS fit the investment coefficient is wrongly signed and insignificant, so it is dropped: imports depend on consumption and the relative price. |
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

| | Result (14 variables) |
|---|---|
| Beats a random walk from 2020 (pandemic trough) | 13 of 14, median U **0.58** |
| Beats a random walk from 2019 | 11 of 14, median U 0.54 |
| Beats constant growth 2010–2019 (pre-pandemic) | **6 of 14, median U 1.02** |
| Beats constant growth 2010–2020 | 9 of 14, median U 0.96 |
| Significant wins (HLN-DM p < 0.10) | 2 vs RW2020; 2 vs constant growth 2010–19 |
| Real GDP level error after 5 years | **−9.1%** (U 0.60 vs RW2020, 0.92 vs CG 2010–19) |
| Real non-oil GDP level error after 5 years | −9.6% (U 0.45 vs RW2020, 1.31 vs CG 2010–19) |
| Policy-level variant | median U 0.51 vs RW2020, 0.95 vs CG 2010–19 |

**Headline:** the random walk from 2020 flatters the model (2020 was the pandemic trough). Against constant growth estimated over
the pre-pandemic decade the model is roughly **on par** (median U 1.02; 2 significant wins). Tracked well: consumption (RMSE
1.8%), trade 3.0%, employment 3.0%, agriculture 4.3%, real GDP 7.0%. Tracked poorly: construction 19.4%, transport 17.6%,
manufacturing 16.6%, state investment 20.0% — sectors transformed after 2020 (new manufacturing capacity, the Karabakh and East
Zangezur reconstruction, the Middle Corridor). Real current spending is over-predicted by 38% by 2025.

### 6.3 Other checks

Per equation: sign and magnitude against theory; small-sample HAC significance; residual-based cointegration; first-difference
cross-check; heteroskedasticity; normality; VIF and condition number; and Chow tests at 2015, 2020 and 2022 on the final
specifications (**10 of 20** tested coefficient sets show instability). System-wide: identity closure, convergence for every
solved year, and a static solution check (mean |real GDP error| 1.7%; consumption within ±10% except 2016–18).

---

## 7. Solution, anchoring and forecasting

### 7.1 Solver

Each year is solved by **damped Gauss–Seidel** iteration to a fixed point (residual < 1e-10; 63–76 iterations per forecast year,
55–63 in the hold-out), with identities imposed exactly at every iteration.

### 7.2 Anchoring 2026 on observed data

2026 is four months observed. All twelve GDP components have published year-to-date real growth indices. A robust (Huber)
proportional bridge from January–April to full-year growth, estimated on 2022–2025 (2021 excluded: its January–April growth is a
2020 base effect), has slope 0.68 and a cross-validated RMSE of 3.9 pp against 6.4 pp for the 1:1 mapping, but it does **not** beat
1:1 on an HLN-corrected Diebold–Mariano test (one-sided p = 0.126), so the **1:1 mapping** is used. Each component's implied
full-year level is an anchoring target reached through add-factor increments; **the increments apply fully in 2026 and decay by half
each year** (1/16 remains in 2030). The largest is construction (−0.202 log points, from −19% January–April growth).

**The 2026→2027 sawtooth.** Because the construction anchor unwinds at a one-year half-life, construction goes −19.0% (2026) →
+11.1% (2027) → +5.7% (2028); non-oil GDP +0.71% → +5.84% → +5.11%, i.e. roughly 1 pp of the 2027 non-oil figure is the unwinding.
ICT (+9.0% → +9.2%) and agriculture (+2.0% → +4.8%, the second being its estimated trend) show no anchor-driven sawtooth.

| | Published Jan–Apr | Model 2026 (full year) | Difference |
|---|---|---|---|
| Real GDP growth | +0.20% | +0.28% | +0.08 pp |
| Real non-oil GDP growth | +0.70% | +0.71% | +0.01 pp |

Two data tensions are passed to the user: construction contracting 19% while total investment rises 15%, and a steep Q1 fall in
both exports and imports.

### 7.3 Scenarios

Because hydrocarbons are exogenous, the forecast is scenario-conditional by construction — a feature that forces assumptions
into the open. Calibrated on the 2025 starting point (Brent 69.1, oil 27.68 mt, gas 50.92 bcm, FX 1.70, policy rate 6.75%).
Common to all scenarios: population +0.483% a year (computed), oil-sector investment moving with the oil-output path (compounded),
pensions indexed to CPI, minimum wage +5% a year.

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
| Non-oil TFP | trend | trend | +0.4 log points a year from 2027 on every sector with a TFP/trend term (agr, man, elc, wat, tou, tra, ict, oth) — now actually applied by the solver |

### 7.4 Headline results

| | Baseline | Adverse | Reform |
|---|---|---|---|
| Real GDP growth, avg % p.a. 2026–30 | **2.56** (first round 1.34; original 1.23) | 1.51 | 3.50 |
| Real non-oil GDP growth, avg % p.a. | **4.18** (first round 2.68; original 2.35) | 3.07 | 5.26 |
| CPI inflation 2030, % | 4.55 | 4.21 | 4.93 |
| Unemployment 2030, % | 4.60 | 4.78 | 4.44 |
| Budget balance 2030, % of GDP | +0.26 | +1.36 | −0.24 |
| Public debt 2030, % of GDP | 20.0 | 20.7 | 19.1 |
| Hydrocarbon share of value added 2030, % | 14.3 | 10.4 | 16.8 |
| Nominal GDP 2030, bn AZN | 179 | 160 | 196 |

Baseline path, % growth:

| | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| Real GDP | 0.28 | 3.02 | 3.08 | 3.13 | 3.30 |
| Real non-oil GDP | 0.71 | 5.84 | 5.11 | 4.73 | 4.61 |
| Consumption | 4.68 | 4.02 | 4.28 | 4.30 | 4.42 |
| Manufacturing | 6.21 | 6.85 | 6.86 | 6.90 | 6.97 |
| Agriculture | 2.00 | 4.75 | 4.29 | 4.06 | 3.94 |
| Construction | −18.99 | 11.08 | 5.70 | 3.16 | 2.06 |
| ICT | 9.00 | 9.22 | 8.96 | 8.78 | 8.65 |

**Why higher than the first revision.** The re-specified household-income equation ties income to non-oil GDP (share relation),
so the demand loop non-oil GDP → income → consumption → trade, taxes and services → non-oil GDP is stronger; consumption now grows
4–4.7% a year (history about 5%), where the first revision's wage-bill version gave 0.1–2.4% and under-predicted consumption by up to
23% in-sample. The 1:1 YTD mapping, the transport transit term and the deflator units fix also contribute. Non-oil growth of
4.2% a year is inside the 2021–25 range (2.7–9.1%) but above the 2015–25 average (about 3%).

**Plausibility flags, disclosed.** *Manufacturing* grows ~6.9% a year: capacity plus the export ↔ manufacturing loop (C3 export
elasticity 0.71 × D3 manufacturing elasticity 0.35; loop gain 0.25) applied to +3% a year external demand. Recent history is
comparable (≈8% a year 2021–25), but the hold-out RMSE for manufacturing is 16.6%; no pre-cut evidence supports a different
specification (every candidate fails the sign screen on pre-cut data). *Agriculture* grows ~4.2% a year, 90% of it the estimated
deterministic trend, against 0.9–3.4% in recent years; a 2015 trend break was tested on pre-cut data and not significant
(p = 0.52), so no break is imposed. More than half of 2027–2030 growth is deterministic trend in transport (105%), agriculture
(90%), ICT (78%) and electricity (64%) — those paths are as good as the assumption that the historical trend continues.

**Add-factor sensitivity:** if the base add-factors decay at each residual's autocorrelation instead of being held, average growth
is lower — real GDP 2.10% (baseline), 1.10% (adverse), 3.01% (reform); non-oil 3.67%, 2.62%, 4.70%.

**The clearest structural result:** the hydrocarbon share of value added falls from 25.6% to 14.3% in the baseline, because oil
volumes decline while non-oil sectors grow.

### 7.5 Uncertainty

500 baseline replications combine: (1) **historical residual-path resampling** — a start year s (2010–2020) is drawn and the joint
deviations u_{s+h} − u_s (h = 1…5) of all 29 behavioural residuals are added to the constant add-factors; nothing is estimated on
the residual dynamics; paths are centred and used with both signs (antithetic); (2) the same five-year history for log Brent, oil
and gas output, **with the same start year**; (3) antithetic, sign-preserving parameter draws from N(β̂, V̂_HAC) (21.9% of coefficient
draws rejected for a sign flip), with base add-factors recomputed to reproduce 2025. 2026 deviations are scaled by 0.84 (the
remaining full-year uncertainty once January–April is known) and 2/3 for the exogenous drivers.

**Diagnostics.** 748 replications were attempted (374 antithetic pairs) to obtain 500 valid (66.8%). Discarded: 133 for a
one-year move more than 0.3 log points away from the baseline's (or 1.5× the largest move the variable made in 2000–2025, where
larger — e.g. tourism, state investment, oil-linked prices), 5 non-finite, 1 explosive; none for non-convergence. The screen
therefore truncates the tails somewhat. In the exported draws the share of draw-years with |Δlog| > 0.3 is 0% for real GDP,
non-oil GDP, CPI and employment, 0.2% for consumption, 9.5% for real current spending and 26% for non-oil investment (whose own
history has larger moves).

**Centring.** Shocks and parameter deviations are symmetric, but aggregates are arithmetic sums of log-normally shocked parts
(chain-linked GDP, oil + non-oil revenue, the income loop), so the raw median lies above the baseline: by 2030 +1.2% (real GDP),
+1.8% (non-oil), +2.1% (consumption), +2.4% (income), +3.8% (current spending), +8.7% (revenue). The exported draws are then
centred on the baseline (multiplicatively for levels, additively for rates): the median equals the published baseline in every
year (max gap 6e−14), dispersion unchanged; cross-variable identities hold only up to those shifts.

| 2030, baseline | 5–95% band (% of median) | 25–75% | hold-out 5-year error |
|---|---|---|---|
| Real GDP | 18.2 | 6.6 | −9.1% |
| Real non-oil GDP | 24.4 | 7.6 | −9.6% |
| CPI level | 70.2 | 36.0 | −29.7% |
| Employment | 8.9 | 4.0 | −4.1% |
| Real disposable income | 28.2 | 13.0 | +11.3% |
| Real consumption | 48.7 | 24.4 | +1.5% |
| Real current spending | 72.0 | 27.6 | +38.0% |

Bands are of the same order as the model's own 2021–25 errors except consumption (far wider than its small hold-out error, because
of the income loop). **Growth and CPI bands** — real GDP growth p5–p95 of about −4% to +13% a year, CPI inflation about −10% to
+21% — replay the 2015–16 devaluation, the 2020 pandemic and the 2021–22 inflation episode, *with both signs*: the upper CPI tail is
the 2016 devaluation (15.7%), while the deflationary lower tail is the mirror image of those episodes and has no historical
precedent under the peg — it should be read as an artefact of symmetric resampling of an asymmetric history.

### 7.6 Multipliers — the FR1 answer on inter-sector transmission

Each experiment shocks one exogenous driver in the **solved** system, reusing the baseline add-factor paths. Deviations from
baseline by 2030, in per cent (`FR1_multipliers.csv`):

| | Brent +10 USD/bbl | Public investment +1 bn AZN | Credit easing (estimated) | Credit easing + judgemental overlay | External demand +10% |
|---|---|---|---|---|---|
| Construction | +1.28 | **+5.90** | +0.01 | +1.38 | +0.11 |
| Manufacturing | +0.50 | +2.37 | 0.00 | +0.44 | **+9.45** |
| Trade | +0.30 | +1.30 | +0.88 | +1.14 | +1.48 |
| ICT | +0.79 | +3.94 | −0.01 | +0.38 | −0.04 |
| Real GDP (chain-linked) | −0.49 | +1.08 | +0.23 | +0.45 | +1.23 |
| Real non-oil GDP | +0.31 | +1.34 | +0.29 | +0.56 | +1.53 |
| Consumption | +0.31 | +1.35 | +0.92 | +1.19 | +1.54 |
| Non-oil investment | +2.47 | +11.58 | −0.04 | +1.15 | −0.15 |
| Budget revenue | +3.88 | +1.66 | +0.62 | +0.95 | +1.93 |
| Non-oil imports | −0.37 | +1.32 | +0.93 | +1.20 | +1.49 |

Transport no longer responds to any of these shocks (its equation is transit volume + trend). **Credit easing** (−200 bp policy,
−100 bp deposit rate) works only through household credit and consumption in the estimated model; the column labelled
"judgemental overlay" additionally applies the regional-panel output elasticity 0.134 to deviations of credit in the investment
equation — a user lever, **not** an estimated effect (the aggregate data reject it, HAC-F p = 0.028).

**Fiscal multiplier (`FR1_fiscal_multiplier.csv`).** +1 bn AZN of real state investment a year (actual injection 970 mln after the
F4 response): real non-oil GDP +843 mln (2015 prices) in 2030 — a **2030 level multiplier of 0.87**; **cumulative multiplier**
(sum of Δ non-oil GDP 2026–30 / sum of injections) **0.70** (0.64 on chain-weighted real GDP). It is larger than in the first
revision (0.54/0.46) because of the stronger income loop; imports now rise (+1.32%).

**An oil price rise lowers chain-weighted real GDP** (−0.49%) while raising non-oil GDP (+0.31%) and budget revenue (+3.88%):
a higher oil price raises the mining deflator and hence mining's chain weight while mining's volume (exogenous) falls.

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

| | Real growth<br>% p.a. | Deflator infl.<br>% p.a. | Nominal growth<br>cum. % | Nominal 2030<br>mln AZN |
|---|---|---|---|---|
| **GDP** | +2.6 | +4.1 | +38.4 | 178,639 |
| **Non-oil GDP** | +4.2 | +5.8 | +63.0 | 150,446 |
| Oil and gas GDP | −3.4 | −1.9 | −23.4 | 28,193 |
| Tourism & catering | **+10.0** | +5.0 | +105.6 | 7,346 |
| Information & communication | +8.9 | −2.8 | +32.9 | 3,545 |
| Manufacturing | +6.8 | +3.9 | +68.3 | 12,989 |
| Transport & storage | +4.9 | +1.3 | +36.0 | 12,383 |
| Water supply & waste | +4.6 | +3.9 | +51.6 | 458 |
| Trade & vehicle repair | +4.2 | +6.3 | +66.7 | 24,376 |
| Net taxes on products | +4.0 | +6.4 | +66.1 | 20,599 |
| Agriculture | +3.8 | +3.5 | +42.8 | 10,926 |
| Electricity, gas & steam | +2.9 | +5.8 | +52.7 | 2,223 |
| Social & other services | +2.7 | +8.7 | +73.7 | 48,743 |
| Construction | +0.0 | +2.2 | +11.9 | 9,428 |
| Mining & quarrying | −3.1 | −1.9 | −22.6 | 25,624 |

Tourism's +10% a year comes from its income elasticity (1.9) on faster-growing per-capita income plus trend — another demand-loop
result to read with caution. The social-services deflator still rises 8.7% a year: unit CPI pass-through is imposed, but the
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
10. **Manufacturing, construction and transport forecasts are the weakest** (hold-out RMSE 16.6–19.4%); against pre-pandemic
    constant growth the model is only on par (median U 1.02).
11. **Calibrated shares are held fixed** (sector investment shares, social-spending share, debt-service rate).
12. **Public investment's level is an assumption, not a forecast** (Section 5, last row).
13. **Cointegration is established for only 2 of 30 level relations** (4 at 10%); most level t-statistics are descriptive and
    the forecast level depends on the constant-add-factor assumption (Section 7.4 sensitivity).
14. **Trend-carried growth** — transport, agriculture, ICT and electricity growth in 2027–2030 is mostly estimated deterministic
    trend (Section 7.4).
15. **A strong demand loop** (income tied to non-oil GDP) raises growth, tourism and the fiscal multiplier; manufacturing is
    amplified by the export ↔ manufacturing link. The household-income elasticity rests on a pension-bill proxy
    (average pension × total population).
16. **No aggregate credit channel** in investment; credit easing on investment is a judgemental overlay.
17. **Fans** are wide for CPI, consumption and current spending, are truncated by the jump screen (one-third of replications
    replaced), carry a mirrored deflationary CPI tail, and are centred on the baseline after a reported median correction.

## 10. What would most improve the model

1. A **supply-use / input–output table** — replaces estimated linkages with measured ones and unlocks policy-module FR2.
2. **Employment and compensation by sector**, annual — completes the production-function block and serves FR3/FR4 directly.
3. **Partner-weighted external demand** and an import price index with history — properly identifies the trade block.
4. **Quarterly national accounts by sector** — roughly quadruples the effective sample, making dynamics estimable rather than imposed.
5. **A longer regional panel** — the cross-section is the model's best identification device and currently only five years deep.
