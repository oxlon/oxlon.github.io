# FR5 — Paid services rendered to the population
## Structural econometric methodology and five-year forecast

**MIIS module 15.5.2 — Microeconomic analysis and forecasting**
Ministry of Economy of the Republic of Azerbaijan

Companion to `FR5.ipynb`. Fourth in a linked set: **FR1** (sector output and the macro economy),
**FR3** (wages), **FR4** (employment), **FR5** (paid services).

---

## 1. The task

> *Əhaliyə göstərilən pullu xidmətlərin **həcmi** və **artım sürətinin** təhlili və proqnozlaşdırılması.*

Analysis and forecasting of the **volume** and the **growth rate** of paid services rendered to the
population, 2026–2030. No AR, ARIMA, ARCH or GARCH models; structural econometric models only; missing
data to be collected from the State Statistical Committee (DSK).

## 2. What "structural" means here

Paid services to the population are **household consumption of services**. The structural model of that
object is a **demand system**, not a time-series relation. FR5 is built in two tiers:

1. **How much** — an aggregate demand equation for the real volume per head, in real household income
   per head and the relative price of services. This yields the *həcm* and its *artım sürəti*.
2. **Of what** — a **linear-approximate almost-ideal demand system (LA-AIDS)** across the thirteen
   published types of service, written in log-odds so that shares are positive and sum to one by
   construction. Its expenditure coefficients *are* the Engel elasticities, which is the answer to which
   service markets grow as households get richer.

Two institutional cuts are added: legal entities versus individual entrepreneurs, and state versus
non-state.

---

## 3. Data, and why DSK was required

The workbook holds the aggregate and the provider split but **no breakdown by type of service at all**.
Without it there is no demand system and no way to say which services grow.

| Source | Content | Years |
|---|---|---|
| Workbook `Sosial sektor ` r27–r34 | Total value and real growth; legal entities; non-state; individuals | 1990–2025 |
| Workbook `Sosial sektor ` r35–r36 | Population nominal income, total and per head | 1997–2025 |
| Workbook `Monetar sektoru` r89, r93 | **Paid-services CPI**, 12-month and average annual | 2000–2025 |
| Workbook `Regionlar`…`13` r100 | Real growth of services by 14 economic regions | 2021–2025 |
| **DSK `007_4-5en.xls` sheet 7.4** | **Value by 13 types of service** | **1995–2025** |
| **DSK `007_18en.xls` sheet 7.18** | **Physical volume index by type** | **2006–2025** |
| DSK `007_3en.xls` sheet 7.3 | State/non-state, value and volume index | 1995–2025 |
| DSK `007_1en.xls` sheet 7.1 | The long total series | 1985–2025 |

**Validation.** The thirteen types reproduce the published total to 2 × 10⁻¹⁴% in all 31 years, so they
are an exhaustive partition whose budget shares sum to one — which is what makes a demand system the
right object and adding-up automatic. Four independently published tables agree on the nominal total to
within the workbook's rounding, and on the real growth index exactly.

## 4. The key identity

The **implicit deflator of the published series is exactly the workbook's paid-services average annual
CPI** — agreement to 0.04 index points in every one of nineteen overlapping years:

$$\frac{\text{value}_t/\text{value}_{t-1}}{\text{volume index}_t} = \text{paid-services CPI}_t$$

The price side of this market is therefore **observed, not estimated**. Consequences: the volume can be
modelled structurally and the value follows by identity; the relative price is an observed regressor; and
FR1's deflator forecast is used directly rather than adding a second source of error. FR5's volume and
value series agree with FR1's to 0.0005% and 0.02% respectively, so the thirteen-type breakdown
decomposes FR1's own aggregate.

## 5. Data-integrity findings

**F1 — Nominal values before 1995 are in pre-denomination manats.** The workbook's row 27 stores
pre-1995 values in thousands of old manats and 1995+ values in millions of present manats, **in the same
row, with no footnote**; the ratio between the workbook and DSK figures is exactly 1000 before 1995 and
1.000 after. A growth rate computed across 1994/1995 from that row is meaningless. FR5 uses nominal data
from 1995 only; volume indices are unaffected.

**F2 — Several DSK cells are stored as text** with non-breaking-space thousands separators and comma
decimals (`'4 088 188,1'`). Read naively they become missing, silently dropping 2009, 2014 and 2016–2022
from the long series. A dedicated parser handles them; the four-source reconciliation proves it worked.

**F3 — "Other paid services" is definitionally unstable**: its share falls from 31.4% (1995) to 0.3%
(2005) while communication rises from 4.0% to 34.2% — reclassification, not behaviour. The demand system
is estimated from 2006, which is also the first year of published volume indices by type.

**F4 — Component volumes do not aggregate to the published total**, by up to 21%. This is the standard
non-additivity of chain-linked volumes when component relative prices diverge (by 2025 the utilities
deflator stands at 181 against 107 for communication, 2015 = 100). Nominal components add up exactly.
FR5 therefore models the **total volume** and the **nominal shares**, so no forecast relies on additivity
that does not hold.

**F5 — The regional series cannot be reconciled with the national.** For 2023–2025 the national growth
index lies **outside the range of every reporting region**: in 2023 the national index is 114.0 while the
highest region is 109.6 and Baku — the majority of the market — is 108.2. A weighted average of a
complete partition must lie between its extremes. Either the regional rows are on a narrower concept or a
large component is missing. The regional data are therefore reported but used neither as validation nor
as a driver. One region (Şərqi Zəngəzur) reports only zeros and is excluded.

---

## 6. The no-autoregression constraint

No equation contains a lagged dependent variable, a moving-average error, or a conditional variance
process. Three lag constructs appear, each an accounting or inference device:

| Construct | Where | Why it is not an autoregression |
|---|---|---|
| Newey–West HAC covariance | every time-series equation | Standard errors only; point estimates are OLS |
| Chained volume indices | §4 | The official identity $Q_t = Q_{t-1} I_t$ between a published level and a published index |
| DOLS leads/lags of **regressor** differences | robustness | Endogeneity correction in a cointegrating regression |

**Dummies for 2020 and 2021** also appear. A dummy is not a lag: it identifies a named historical event
rather than propagating the dependent variable. Omitting them loads a lockdown onto the income
elasticity; they are set to zero over the forecast.

---

## 7. Specifications tested and rejected

| # | Specification | Verdict | Evidence |
|---|---|---|---|
| R1 | Volume per head on a deterministic trend | rejected — not structural | fits (R² 0.84) but has no economic content and cannot respond to a scenario; scores 148.9% out of sample |
| R2 | Non-oil GDP per head in place of household income | rejected — wrong-signed price term | price coefficient **+1.536** when GDP replaces household income |
| R3 | Relative price in the aggregate equation | rejected — fails out of sample | pooled OOS RMSE 13.64% against 10.14% for income alone |
| R4 | Income deflated by the service price (homogeneity imposed) | rejected | OOS RMSE 25.2% |
| R5 | Per-category choice of share specification | rejected — selection bias | wins the selection windows (1.31 pp) and **loses** the withheld window (2.015 vs 1.960 pp) |
| R6 | Unrestricted own-price coefficients in the demand system | **restricted** — violated the law of demand | 4 of 12 types implied a *positive* own-price elasticity |

---

## 8. The model

### 8.1 Tier 1 — aggregate demand

$$\ln(Q_t/N_t) = \alpha + \eta \ln(Y^d_t/N_t) + \varepsilon \ln(P^s_t/P_t) + \delta_{20}D^{2020} + \delta_{21}D^{2021} + u_t$$

Selection across five candidates on three pooled hold-out cut-offs; **income alone wins** (10.14% RMSE).

**Estimated:** $\eta = 1.561$ (t = 36.6), n = 26 (2000–2025), R² = 0.988. The Wald test of $\eta = 1$
gives χ² = 172.4, p < 0.0001: **paid services are a luxury**, which is why the services market grows
faster than the economy. Pandemic dummies −0.221 (t = −9.5) and −0.096 (t = −4.3).

The difference-form estimate is 1.183 (t = 5.4), 24% below the level estimate. Both are precise; the
level coefficient is a long-run elasticity and the difference coefficient an impact elasticity. Because
no lagged dependent variable is permitted, the speed of adjustment is not estimated — stated as a
limitation, not hidden.

**Price elasticity**, reported but not imposed: $\varepsilon = -0.174$ (t = −0.7) — correctly signed,
insignificant, and it degrades the forecast. It is exposed as a scenario lever so a tariff decision can
still be analysed with the elasticity the data do support.

### 8.2 Tier 2 — the thirteen-type demand system

$$\ln\!\left(\frac{w_{i,t}}{w_{r,t}}\right) = \alpha_i + \beta_i \ln\!\left(\frac{X_t}{N_t P^s_t}\right) + \gamma_i \ln\!\left(\frac{p_{i,t}}{p_{r,t}}\right) + u_{i,t}, \qquad w_i = \frac{e^{z_i}}{\sum_j e^{z_j}}$$

Reference type: transport. Estimated 2006–2025.

**Selection.** Five hold-out windows, **four used to choose and the fifth withheld entirely**; errors in
percentage points of the share; 2020–21 excluded from scoring.

| Specification | Selection windows | **Withheld window** |
|---|---|---|
| Constant shares | 1.507 pp | 2.375 pp |
| Engel term only | 1.458 pp | 2.304 pp |
| **Engel + relative price (LA-AIDS)** | 1.552 pp | **1.960 pp** |
| Per-category choice | **1.309 pp** | 2.015 pp |

The uniform LA-AIDS is best on the window that played no part in choosing it, and it beats constant
shares by 17% there. The per-category variant wins where it was tuned and loses where it was not — which
is exactly why a window was withheld.

### 8.3 A restriction the free system violated

Under the softmax, $\partial \ln w_i/\partial \ln p_i = \gamma_i(1-w_i)$, so the own-price elasticity of
volume is $\gamma_i(1-w_i)-1$ and the law of demand requires $\gamma_i \le 1/(1-w_i)$. **Four of twelve
types violated it** — public utilities (+0.27), education (+0.72), culture (+3.32), medical (+3.48).

These are not a random four. They are precisely the services whose prices are **administered**: tariffs,
tuition and health charges are raised as part of cost-recovery and expansion programmes, so price and
quantity rise together for institutional reasons. The price variable is endogenous and the coefficient is
not an elasticity.

A demand system implying upward-sloping demand curves should not be published whatever its forecast
score. The restriction was **imposed at the boundary** (own-price elasticity zero — a perfectly
price-inelastic volume, the natural description of an administered price). It *improved* the selection
window (1.552 → 1.427 pp) and cost 0.012 pp on the withheld window. All twelve elasticities are now
non-positive.

### 8.4 Expenditure elasticities — the core result

Within-services elasticity, and its product with the aggregate elasticity 1.56:

| Service | Within services | Income elasticity | |
|---|---|---|---|
| Physical culture and sport | 2.46 | 3.84 | luxury |
| Medical services | 2.40 | 3.75 | luxury |
| Tourist and excursion services | 2.03 | 3.16 | luxury |
| Educational services | 1.99 | 3.10 | luxury |
| Housing services | 0.82 | 1.28 | necessity |
| Household (personal) services | 0.77 | 1.20 | necessity |
| Public utility services | 0.56 | 0.87 | necessity |
| Communication services | 0.34 | 0.52 | necessity |

The share-weighted mean expenditure elasticity is **1.000000** — the adding-up restriction appearing in
the results rather than being imposed on them. This table is the structural chain the task asks for:
household income → the services budget → the individual market.

### 8.5 Institutional splits

Logit shares, specification chosen out of sample. The **individual-entrepreneur** share is best forecast
as **constant** (24.9% in 2025) — its history is a hump, not a trend. The **state** share responds to
income (−0.406, t = −4.9) and falls from 42.1% in 1995 to 22.2% in 2025.

---

## 9. Solution and validation

Block-recursive; no iterative solver needed. Add-factors are each equation's own residual read once, held
constant, not decaying. The model reproduces 2025 to machine precision on volume, value and all thirteen
shares. Population is assumed to continue at its 2021–2025 average growth of 0.483% a year (FR1 publishes
no population path). Relative prices by type are carried forward on damped recent drift — an assumption
affecting only the volume/price split within each type, never the totals.

**Hold-out A, pre-pandemic** (estimate to 2013, simulate 2014–2019): aggregate volume beats a random walk
(U = 0.87) and constant growth (U = 0.14); shares beat a random walk in **9 of 13** types, median
U = 0.88, median error 0.42 pp.

**Hold-out B, spanning the pandemic** (estimate to 2019, simulate 2020–2025): the 2020 error is **+25.2%**
— the model was given actual household income and still could not know that venues were closed by
decree. No income-based demand system could. By 2025 the error is −3.8%, so the structure recovers rather
than drifting. Over the window, U = 0.52 and 0.35.

**Nine identity checks**, all passing to machine precision: shares sum to one; value by type sums to the
total; value = volume × deflator for the total and for every type; the anchor year is reproduced; no share
or volume is non-positive; expenditure elasticities average to one.

**Consistency with FR1**, which forecasts this aggregate with a *different* equation: FR5 and FR1 differ
by at most 4.73% by 2030 — genuine corroboration rather than construction.

---

## 10. Baseline forecast 2026–2030

| | 2025 | 2030 | per year |
|---|---|---|---|
| Volume, mn AZN at 2015 prices | 8,735 | 9,263 | **+1.18%** |
| Value, mn AZN current prices | 14,957 | 18,495 | **+4.34%** |
| Volume per head, AZN | 853 | 883 | +0.70% |

Average annual volume growth by type: communication +3.68%, transport +1.24%, culture +1.23%, public
utilities +0.85%, household services +0.70%, housing +0.41%.

Realised growth was +1.62% a year from the pre-pandemic peak (2019) to 2025 and +4.67% a year over
2010–2019. **The forecast is slower than the 2010s because FR1 projects real household income per head to
be roughly flat**, and an elasticity of 1.56 applied to a flat driver gives a flat result.

**On 2026.** The model forecasts −0.05% volume growth in 2026 immediately after +9.0% in 2025. This is not
a statement about the services market: FR1 has real household income rising +0.14% in 2026 while the
population assumption adds +0.48%, so income *per head* falls 0.34%. Anyone who disagrees with that income
path should change it — §11 quantifies the effect — rather than reading this as a service-sector contraction.

**Scenarios** span only 0.36% of 2030 volume. That is inherited: FR1's household income paths differ by
only 0.23% in 2030 across its three scenarios, because the FR1 scenarios concentrate their divergence in
hydrocarbons rather than in household income. It is not evidence that service demand is insensitive to the
macroeconomy — the income elasticity is 1.56.

## 11. Levers

| Lever | Effect on 2030 volume |
|---|---|
| Income elasticity 1.18 instead of 1.56 | −0.83% |
| Services relative price 10% higher / lower | −1.65% / +1.85% |
| Population growth ±0.3pp | ∓0.83% |

The elasticity effect is small **once the model is correctly re-anchored on 2025**, because real income per
head barely moves over the horizon. An elasticity sensitivity that is not re-anchored instead shows a
spurious double-digit level shift — a trap worth naming.

## 12. Limitations

1. **The forecast is driven by FR1's income path**; with η = 1.56 that projection does almost all the work.
2. **The income elasticity is a range** (1.18–1.56), not a point.
3. **No adjustment dynamics**, so the first forecast year responds faster than households really do.
4. **The aggregate price channel is weak**; within the system prices matter much more, and for four
   administered-price services the response had to be restricted rather than believed.
5. **Thirteen forecast price paths are an assumption**, affecting the volume/price split within each type.
6. **Regional data could not be reconciled** (F5).
7. **"Other paid services" has definitional breaks**, costing eleven years of otherwise usable data.
8. **No household budget survey data**, so the elasticities are aggregate and cannot be read
   distributionally.

### What would improve the next vintage

- Household budget survey microdata, to identify the demand system properly and allow income-group detail.
- Reconciliation of the regional series with the national total (F5).
- A published price index per type of service, removing the need for thirteen implicit deflators.
- An official population projection.
- A consistent back-series for "other paid services" before 2006.

## 13. Outputs

`FR5.ipynb` — 63 cells (41 code, 22 markdown), 0 errors. `docs/FR5_Methodology.md` — this document.
28 CSVs in `output/`, including `FR5_forecast_long.csv` (tidy: scenario × year × type, volume, value,
deflator, share, growth), `FR5_volume_by_type.csv`, `FR5_volume_growth_by_type.csv`,
`FR5_expenditure_elasticities.csv`, `FR5_own_price_elasticities_{unrestricted,restricted}.csv`,
`FR5_demand_system_specification_selection.csv`, `FR5_rejected_specifications.csv`,
`FR5_holdout_validation.csv`, `FR5_identity_checks.csv`, and the extracted DSK history.
