> **Azərbaycan dilində:** [az/FR5_Metodologiya.md](az/FR5_Metodologiya.md)

# FR5 — Paid services rendered to the population
## Structural econometric methodology and five-year forecast

**MIIS module 15.5.2 — Microeconomic analysis and forecasting**
Ministry of Economy of the Republic of Azerbaijan

Companion to `FR5.ipynb`. Fourth in a linked set: **FR1** (sector output and the macro economy),
**FR3** (wages), **FR4** (employment), **FR5** (paid services).

---

<!-- AUTO:v22_note -->
## v2.2 (2026-10-05): competitors from the Ministry's macro module

The macro module explains real paid-services growth by real final-consumption growth (its U ≈ 0.60), and the Ministry's own workbook
(`MOE SOCIAL.xlsx` eq8, copied to `data/macro_module/fr345_ministry_equations_catalog.csv`) uses Δln paid services = −0.0055 +
1.07 Δln trade + 0.38 Δln wage. Both forms (growth forms, no lagged dependent variable) and the Ministry's published coefficients
were scored with E1's own rules: pre-cut origins 2011–2017 (scored ≤ 2019) and the untouched 2020–2025 window (2020–21 excluded).
`FR5_macro_module_competition.csv`:

| specification | selection RMSE % | DM p vs E1 | test RMSE % | U (RW) | U (CG) | 2025 error % | decision |
|---|---|---|---|---|---|---|---|
| M1 growth: real household consumption per head | 20.32 | 0.000 | 12.61 | 0.99 | 0.68 | -19.1 | rejected |
| M2 growth: Ministry form, re-estimated (trade + wage) | 22.76 | 0.011 | 33.30 | 2.61 | 1.79 | +21.8 | rejected |
| M3 Ministry equation, published coefficients (not re-estimated) | 38.01 | 0.001 | 50.32 | 3.95 | 2.70 | +42.4 | rejected |
| reference: E1 (income + relative price), re-estimated to 2019 | 7.18 |  | 9.77 | 0.77 | 0.52 | -2.8 | reference |
| reference: hold-out B procedure (specification re-selected at 2019) |  |  | 12.82 | 1.01 | 0.69 | -1.4 | reference |

**Nothing is adopted.** The consumption form (elasticity 1.71, se 0.27) beats the hold-out *procedure* result quoted
before (U 1.01) only marginally and loses to E1 itself re-estimated to 2019 (U 0.77 / 0.52); it is far worse on the
pre-cut origins and ends 2025 -19% off; the Ministry form is worse still (with its published coefficients, which use the
test years, U 3.95). Registered as `FR5.M1_cons_growth`, `FR5.M2_ministry_reest`, `FR5.M3_ministry_fixed` (rejected).

**Share models — no-change behaviour.** With κ = 512 shrinkage and 2025 anchoring the shares are close to a no-change path: 2025→2030
the median type share moves 0.02 pp (max 0.29 pp, household services), 12 of 13 types move < 0.1 pp, and
the 2020–2025 hold-out U vs the random walk is 1.00 for 11 types (`FR5_share_change_check.csv`). This is the selected
outcome of the pre-cut κ search, not an own-history model: the type paths are driven by the aggregate and the type prices.
<!-- /AUTO:v22_note -->

<!-- AUTO:v23_note -->
## v2.3 (2026-10-05): add-factor decay with a fixed half-life (no estimated residual AR)

Up to v2.2 the Part 17 sensitivity "add-factors decay" let the 2025 add-factors of E1, the share equations and the two splits fade
at each equation's estimated first-order residual autocorrelation ρ̂ (E1 ρ̂ = 0.59) — an estimated AR(1) coefficient inside
a scenario path, which the client's constraint excludes. From v2.3 the decay is **fixed, not estimated**: 0.5^(h/H), h = years
after 2025, half-life **H = 1 year** (0.50 a year; the project's partial-year rule). H is the engine lever `addf_half_life`
(0.25–10 years, active only with `addf_decay`). ρ̂ is still reported as a diagnostic only. The scenarios keep constant
add-factors and are unchanged. 2030 total volume under the decay sensitivity: −492 million manat
(−4.62%) vs Baseline; v2.2 (decay at ρ̂): −483 (−4.44%).
<!-- /AUTO:v23_note -->

---

## v2 (2026-10-05): tənliklər reyestri, ssenari mühərriki, dayanıqlıq

<!-- AUTO:v2 -->
**Tənliklər reyestri** (`output/FR5_equations.json`): 84 tənlik, onlardan 15-i proqnozda istifadə
olunur — E1 (gəlir + nisbi qiymət, DOLS(0: contemporaneous dx), η = 1.155, ε = -0.182), proqnoz sistemindəki 12 büzülmüş Engel meyli
(κ = 512, seçim pəncərələri ≤2019) və iki sabit institusional pay. Qeydiyyatda həmçinin: Tier 1 namizədləri (yalnız gəlir, deflyasiya
edilmiş gəlir, gəlir + trend, yalnız trend, artım forması) və E1-in fərq forması, Part 9-un statik alternativləri, 12 pay tənliyinin
səviyyə (DOLS) və fərq formaları, qiymətlə genişləndirilmiş MNL, LA-AIDS (SUR, homogenlik + simmetriya), bölgü namizədləri (gəlir,
trend). Hər OLS/DOLS tənliyi statsmodels ilə yenidən qiymətləndirilib və notebook-un qiymətləri ilə yoxlanılıb (uyğunsuzluq: 0).
Dayanıqlıq hökmləri (bütün tənliklər): qeyri-stabil 49, qismən stabil 34, stabil 1; proqnozda istifadə olunanlar: qismən stabil 15 (büzülmüş meyllər və sabit
paylar üçün rekursiv testlər tətbiq olunmur; E1: rekursiv: c20 işarəsi yolun ilk yarısında dəyişir; bir ili çıxarmaqla: c20 işarəsi dəyişir; rekursiv: c21 işarəsi yolun ilk yarısında dəyişir).

**Ssenari mühərriki** (`microlib/engines/fr5.py`, `_fr5_core.py`; vəziyyət `output/engine/FR5_state.json` + `.npz`): Part 14-ün `solve()`
funksiyası köçürülüb. Girişlər: 4 FR1 yolu (`fr1:rhhdisp`, `fr1:p_cons`, `fr1:p_serv_hh`,
`fr1:pop`) və 13 növ üzrə nisbi qiymət yolu, 14 redaktə edilə bilən əmsal (η, ε və 12 büzülmüş
Engel meyli; SE və 95% interval reyestrdən), 6 rıçaq (növ qiymət qaydası, η seçimi, xidmətlərin nisbi qiyməti, əhali
artımı, düzəliş əmsalının sönməsi). `selftest()`: bütün 3 ssenaridə CSV çıxışları təkrarlanır (maks. nisbi fərq
2.5e-16); rıçaqlar Part 17 rıçaq cədvəlini dəqiq təkrarlayır. Bir ssenari < 0.1 s.

**Tam proqnoz cədvəli** (`FR5_forecast_tidy.csv`, `FR5_indicator_catalog.csv`): 79 komponent (cəmi həcm və dəyər, adambaşına
həcm, deflyator və artım templəri, 13 növün həcmi, dəyəri, payı, deflyatoru və artımı, iki bölgünün payları və dəyərləri) ×
3 ssenari × 2026–2030, hamısı dolu, tarix ilə; 5–95% zolaqlar 21 komponent üçün (Əsas).
`FR5_not_forecast.csv`: regional sıralar (milli sıra ilə uzlaşmır, Part 13).

**Əmsal həssaslığı** (`FR5_coef_sensitivity.csv`, ±1 SE, 2030, Əsas; başlıq: cəmi həcm və dəyər, 2030 dəyərinə görə ən böyük üç növ —
Rabitə xidmətləri, Kommunal xidmətlər, Nəqliyyat xidmətləri): ən böyük təsirlər — Pullu xidmətlər, cəmi: nominal dəyər: FR5.E1_income_relprice|ln_income_pc (-1.65% / +1.67%); Rabitə xidmətləri: real həcm: FR5.E1_income_relprice|ln_income_pc (-1.65% / +1.68%); Pullu xidmətlər, cəmi: real həcm: FR5.E1_income_relprice|ln_income_pc (-1.65% / +1.67%); Nəqliyyat xidmətləri: real həcm: FR5.E1_income_relprice|ln_income_pc (-1.68% / +1.71%); Kommunal xidmətlər: real həcm: FR5.E1_income_relprice|ln_income_pc (-1.68% / +1.71%). Mətnlər: `FR5_strings_az.csv` (446 ingiliscə mətn → azərbaycanca). Kernel: `miis-model` (Python 3.13).
<!-- /AUTO:v2 -->

---

## Revision note (2026-09-27; further rounds 2026-09-28)

Numbers in §7–§11 are **generated by the notebook** (last code cell) from the CSV outputs of the run
that produced them, between `AUTO` markers, so the document cannot drift from the outputs.

<!-- AUTO:rev -->
Current headline (this run): Tier 1 = income + relative price, η = 1.155; Tier 2 = MNL: Engel term, level slope if coherent else difference-form with Engel-slope shrinkage κ = 512; volume +4.04% and value +7.58% a year 2026–2030; E1 sign-rejection rate 22.8%; 56 FR5 CSV outputs.
<!-- /AUTO:rev -->

What changed and why:

1. **Cointegration tests corrected** (MacKinnon residual-based `eg_coint_p`); non-cointegrating level
   relations are labelled descriptive and no longer called cointegrating.
2. **Estimator and inference** — DOLS for level relations (contract df rule); HAC with n/(n−k) scaling,
   t(n−k), HAC-F; every level equation also estimated in first differences.
3. **One decision rule for every choice** (aggregate, shares, shrinkage, splits): candidates not
   significantly worse than the best on windows scored ≤ 2019 (DM/HLN, p > 0.10); among them prefer
   **coherent** ones (level slopes inside the 95% CI of the same equation in differences, on the
   estimation sample); then the simplest. A growth-form Tier-1 candidate competes in the same design.
   The homogeneity-imposed equation (level η 0.43 against 1.29 in differences) is rejected as incoherent.
4. **"Luxury" withdrawn** as a statistical finding; the relative price of services **fell** 2005–2025.
5. **Tier 2 relabelled** a multinomial-logit share system; elasticity $1+\beta_i-\sum_j w_j\beta_j$; the
   mean elasticity of 1 is mechanical; IIA and the reference type's own-price elasticity stated; a
   genuine LA-AIDS added as a candidate. Incoherent level Engel slopes are replaced by difference-form
   slopes, and all type slopes are **shrunk** towards the common elasticity 1 by precision-weighted
   empirical Bayes, with the intensity chosen by the same rule — with FR1's final, much stronger income
   path the unshrunk slopes produced implausible type paths.
6. **Selection without look-ahead** in forecast scores; 2020–2025 is an untouched test window.
7. **Law of demand imposed exactly** in the price-augmented variants (not selected; exported as
   `FR5_nonselected_*`); `FR5_own_price_elasticities_forecast_system.csv` gives what the forecast uses.
8. **Type ranking** — weakly supported whatever the rule; compared with each type's own history.
9. **No own-history price extrapolation**; **population from FR1**; **hold-outs** re-run with the whole
   decision rule pre-cut; **institutional splits** forecast and exported with fans.
10. **Fan charts** — centred historical residual-path resampling (no ρ̂ process), parameter draws with
    sign rejection, FR1 macro draws screened for non-finite values only; only nine joint paths are
    usable (disclosed); a per-equation pooled variant is reported.

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
2. **Of what** — a **multinomial-logit share system** across the thirteen published types of service,
   written in log-odds so that shares are positive and sum to one by construction. Its Engel slopes give
   the expenditure elasticities — which service markets grow as households spend more.

Two institutional cuts are added and forecast: legal entities versus individual entrepreneurs, and
state versus non-state.

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
process. The lag-like constructs are accounting or inference devices:

| Construct | Where | Why it is not an autoregression |
|---|---|---|
| Newey–West HAC covariance (n/(n−k) scaled) | every time-series equation | Standard errors only |
| Chained volume indices | §4 | The official identity $Q_t = Q_{t-1} I_t$ between a published level and a published index |
| DOLS leads/lags of **regressor** differences | every level relation | Endogeneity correction; the dependent variable's lags never enter |
| Engle–Granger residual ADF (maxlag 1) | cointegration tests | A test statistic, not a model |
| Residual autocorrelation ρ̂ | diagnostic tables only | A diagnostic statistic (like DW); since v2.3 used in no forecast, scenario or sensitivity path; never a regressor |
| Add-factor decay (sensitivity only) | Part 17 | A **fixed** one-year half-life (0.5 a year; the project's partial-year rule); nothing is estimated |
| Historical residual paths $u_{s+h}-u_s$ | fan charts | Resampled observed deviations; no autocorrelation is estimated |
| Cumulation of a growth-form candidate from the anchor | Tier-1 candidate | The chain identity $Q_t = Q_{t-1}(1+g_t)$, not a fitted lag |

**Dummies for 2020 and 2021** identify a named event and are set to zero over the forecast. They are
zero — and unidentified — in every sample ending before 2020, so they are not a selection candidate and
are absent from selection windows and hold-outs. FR5 uses no partial-year data, so the contract's
nowcast add-factor rule does not arise.

---

## 7. Specifications tested — the decision tables

**Tier 1** (origins 2011–2017, scores ≤ 2019; coherence on the estimation sample):

<!-- AUTO:t1table -->
| specification | slopes | selection RMSE % | DM/HLN p vs best | level η | difference η | coherent | decision |
|---|---|---|---|---|---|---|---|
| income + relative price | 2 | 7.18 | — | 1.15 | 1.44 | yes | CHOSEN: simplest coherent non-inferior level specification |
| income deflated by service price | 1 | 8.14 | 0.681 | 0.43 | 1.29 | no | — |
| income only | 1 | 8.80 | 0.000 | 1.67 | 1.35 | yes | — |
| income + trend | 2 | 11.86 | 0.000 | 1.64 | 1.35 | yes | — |
| growth form: deflated income | 1 | 28.98 | 0.078 | — | — | yes | — |
| trend only | 1 | 63.74 | 0.000 | — | — | no | — |
<!-- /AUTO:t1table -->

**Tier 2** (same windows and rule):

<!-- AUTO:t2table -->
| specification | selection RMSE pp | DM/HLN p vs best | slopes | non_inferior | coherent | decision |
|---|---|---|---|---|---|---|
| constant shares | 0.77 | 0.011 | 0 | no | yes | — |
| MNL: Engel term only | 0.68 | — | 1 | yes | no | — |
| MNL: Engel term, difference-form slopes | 0.75 | 0.381 | 1 | yes | yes | — |
| MNL: Engel term, level slope if coherent else difference-form | 0.73 | 0.331 | 1 | yes | yes | CHOSEN |
| MNL: Engel + own relative price (unrestricted) | 1.22 | 0.072 | 3 | no | no | — |
| MNL: Engel + own relative price, law of demand imposed | 0.89 | 0.154 | 2 | yes | no | — |
| LA-AIDS (linear shares, Stone index, homogeneity+symmetry, SUR) | 2.69 | 0.065 | 2 | no | no | — |
<!-- /AUTO:t2table -->

**Engel-slope shrinkage intensity** (same windows and rule; more shrinkage = simpler):

<!-- AUTO:shrink -->
| specification | selection RMSE pp | DM/HLN p vs best | non_inferior | decision |
|---|---|---|---|---|
| coherence rule, shrinkage kappa = 0.0 (none) | 0.73 | 0.512 | yes | — |
| coherence rule, shrinkage kappa = 0.5 | 0.72 | 0.521 | yes | — |
| coherence rule, shrinkage kappa = 1.0 | 0.72 | 0.528 | yes | — |
| coherence rule, shrinkage kappa = 2.0 | 0.71 | 0.542 | yes | — |
| coherence rule, shrinkage kappa = 4.0 | 0.70 | 0.566 | yes | — |
| coherence rule, shrinkage kappa = 8.0 | 0.69 | 0.604 | yes | — |
| coherence rule, shrinkage kappa = 16.0 | 0.68 | 0.661 | yes | — |
| coherence rule, shrinkage kappa = 32.0 | 0.67 | 0.746 | yes | — |
| coherence rule, shrinkage kappa = 64.0 | 0.66 | 0.871 | yes | — |
| coherence rule, shrinkage kappa = 128.0 | 0.66 | — | yes | — |
| coherence rule, shrinkage kappa = 256.0 | 0.66 | 0.655 | yes | — |
| coherence rule, shrinkage kappa = 512.0 | 0.68 | 0.271 | yes | CHOSEN |
| coherence rule, shrinkage kappa = 1024.0 | 0.70 | 0.058 | no | — |
| coherence rule, shrinkage kappa = 4096.0 | 0.74 | 0.013 | no | — |
| constant shares | 0.77 | 0.014 | no | — |

Chosen: **coherence rule, shrinkage kappa = 512.0** — the most shrinkage that is not significantly worse than the best (κ = 128.0); full shrinkage (constant shares) is inferior (p = 0.014).
<!-- /AUTO:shrink -->

**Splits:** constant shares chosen for both (no richer candidate significantly better).
**Other rejected variants:** per-category choice of share specification (nested test, no gain);
pandemic dummies extended to 2022 or a post-2020 intercept shift (identical to the baseline on every
pre-2020 window, so they cannot be selected); non-oil GDP in place of income (wrong-signed price term).
Test-window scores are printed in the notebook for information only.

---

## 8. The model

### 8.1 Tier 1 — aggregate demand

$$\ln(Q_t/N_t) = \alpha + \eta \ln(Y^d_t/N_t) + \varepsilon \ln(P^s_t/P_t) + \delta_{20}D^{2020} + \delta_{21}D^{2021} + u_t$$

$Y^d$ is FR1 real disposable income (consumer deflator); $Q$ the paid-services volume (services
deflator); $P^s/P$ the wedge between the two.

<!-- AUTO:e1 -->
**Chosen: income + relative price.** Estimated by DOLS(0: contemporaneous dx) on 2005-2025 (df 13): ln_income_pc +1.155 (s.e. 0.116), ln_relprice -0.182 (s.e. 0.248), c20 -0.273 (s.e. 0.041), c21 -0.167 (s.e. 0.044). **eg_coint_p = 0.41** — not cointegrating; t-statistics descriptive. Difference form: η = 1.44 (95% CI 0.86–2.02); the level estimate is **inside** it (coherent). 2025 add-factor +0.049; residual first-order autocorrelation 0.59 (diagnostic only).

| estimate | eta | se | eg_coint_p | df | p(η = 1) |
|---|---|---|---|---|---|
| income + relative price, DOLS levels 2005-2025 | 1.155 | 0.116 | 0.41 | 13 | 0.204 |
| income + relative price, difference form | 1.440 | 0.271 | — | 15 | 0.125 |
| income only, DOLS levels 2000-2025 | 1.665 | 0.062 | 0.13 | 16 | 0.000 |
| income only, DOLS levels 2005-2025 | 1.443 | 0.145 | 0.30 | 13 | 0.009 |
| income only, difference form | 1.350 | 0.246 | — | 21 | 0.169 |

η ranges 1.15–1.67; the difference-form estimates range 1.35–1.44 and none rejects η = 1 at 5%.
<!-- /AUTO:e1 -->

Services are probably income-elastic, but **"luxury" is not statistically established**.

### 8.2 Tier 2 — the thirteen-type share system

$$\ln\!\left(\frac{w_{i,t}}{w_{r,t}}\right) = \alpha_i + \beta_i \ln(Q_t/N_t) + \delta_{i}D^{2020,2021} + u_{i,t}, \qquad w_i = \frac{e^{z_i}}{\sum_j e^{z_j}}$$

Reference type transport, 2006–2025. A **multinomial-logit share system**, not an LA-AIDS:
$e_i = 1+\beta_i-\sum_j w_j\beta_j$; the share-weighted mean of the $e_i$ is 1 for any coefficients; with a
price term the own-price elasticity is $\gamma_i(1-w_i)-1$, the reference type's
$\sum_{j\ne r}w_j\gamma_j-1$, and cross-price elasticities $-w_i\gamma_i$ are identical across types (IIA).
The selected system has no price term (own −1, cross 0).

**Coherence rule.** <!-- AUTO:coh -->
Of the 12 level Engel slopes, 1 is/are cointegrating and **9 lie outside the 95% CI of the same equation in differences** (household, communication, housing, culture, sport, medical, sanatoria, legal_bank, other); these use the difference-form slope, the others (utilities, tourism, education) their DOLS level slope. medical: level +2.82, difference -0.21 [-0.77, 0.34]. culture: level -2.42, difference +1.05 [0.03, 2.07].
<!-- /AUTO:coh -->

**Shrinkage.** The slopes (level or difference-form, each with its own standard error $s_i$) are shrunk
towards the common value at which every expenditure elasticity equals 1: deviations
$d_i=\beta_i-\sum_j w_j\beta_j$ are multiplied by $1-B_i$, $B_i=\kappa s_i^2/(\kappa s_i^2+\hat\tau^2)$,
with $\hat\tau^2$ the method-of-moments between-type variance; κ = 0 is no shrinkage, κ → ∞ constant
shares. Imprecise slopes are shrunk most. κ is chosen in §7.

**Pandemic break (level slopes).**

<!-- AUTO:pandemic -->
| variant | culture beta (level) | medical beta (level) | education beta (level) | utilities beta (level) | selection RMSE pp (windows <= 2019), level system |
|---|---|---|---|---|---|
| baseline: dummies 2020, 2021 | -2.42 | 2.82 | 0.95 | 0.58 | 0.68 |
| dummies extended to 2022 | -2.60 | 3.48 | 1.45 | 0.91 | 0.68 |
| post-2020 intercept shift (break) + 2020, 2021 dummies | 0.00 | 1.15 | 0.59 | -0.65 | 0.68 |
<!-- /AUTO:pandemic -->

### 8.3 Price responses (non-selected variants)

The unrestricted price-augmented system implies positive own-price elasticities for the administered-
price services (utilities, education, culture, medical). With γ = 0 there and γ ≤ 1 elsewhere the
system is not selected; the endogeneity moves into β. See `FR5_nonselected_own_price_elasticities_*.csv`.

### 8.4 Expenditure elasticities — a weakly supported ranking

At 2025 shares, forecasting system (coherence rule + shrinkage), 90% parameter bands, with the
orderings an all-level and an all-difference system would give:

<!-- AUTO:elast -->
| service | e_i (forecast system) | 5% | 95% | rank | rank, all level | rank, all difference |
|---|---|---|---|---|---|---|
| Housing services | 1.04 | 0.99 | 1.09 | 1 | 8 | 8 |
| Other paid services | 1.04 | 0.99 | 1.09 | 2 | 12 | 3 |
| Legal and banking services | 1.03 | 0.97 | 1.08 | 3 | 11 | 7 |
| Physical culture and sport | 1.03 | 0.97 | 1.08 | 4 | 10 | 1 |
| Culture services | 1.03 | 0.97 | 1.08 | 5 | 13 | 2 |
| Sanatoria and health services | 1.02 | 0.97 | 1.08 | 6 | 9 | 4 |
| Educational services | 1.02 | 0.97 | 1.07 | 7 | 2 | 6 |
| Tourist and excursion services | 1.02 | 0.97 | 1.07 | 8 | 3 | 5 |
| Public utility services | 1.02 | 0.98 | 1.06 | 9 | 4 | 11 |
| Transport services | 1.02 | 1.00 | 1.04 | 10 | 5 | 9 |
| Medical services | 1.02 | 0.97 | 1.07 | 11 | 1 | 10 |
| Communication services | 1.01 | 0.96 | 1.05 | 12 | 6 | 13 |
| Household (personal) services | 0.85 | 0.81 | 0.90 | 13 | 7 | 12 |
<!-- /AUTO:elast -->

The ranking depends on which slope estimate is believed and is **weakly supported**. The selected
shrinkage is strong, so the forecasting system's elasticities are close to 1 and the type forecasts
differ little from proportional growth (§10): the data do not support a sharper ordering.

### 8.5 Institutional splits

<!-- AUTO:splits -->
Both splits are forecast as constant shares at their 2025 values (individual entrepreneurs 24.87%, state 22.19%). 2030 baseline values: legal entities 16,192, individual entrepreneurs 5,361, state 4,783, non-state 16,770 mn AZN. 2030 90% bands: individual-entrepreneur share 20.1–28.9%, state share 19.7–28.2%.
<!-- /AUTO:splits -->

---

## 9. Solution and validation

Block-recursive; FR1 supplies income, population (`pop`) and the two deflators for all scenarios.
Add-factors are each equation's 2025 residual, held constant; type relative prices held at 2025. The
model reproduces 2025 exactly. Eleven arithmetic checks pass (they hold by construction).

**Hold-outs** (whole decision rule re-applied on data to the cut-off; shares driven by the simulated
total; constant-growth benchmark = five years before the cut, 2008–13 being the late oil boom):

<!-- AUTO:holdout -->
| specification | A: pre-pandemic 2014-2019 | B: test window 2020-2025 |
|---|---|---|
| tier1_spec | income deflated by service price | income deflated by service price |
| tier1_estimator | OLS (df too small for DOLS) | DOLS(0: contemporaneous dx) |
| cg_rate_pct | 9.44 | 2.24 |
| cg_window | 2008-2013 | 2014-2019 |
| RMSE_pct | 4.88 | 12.82 |
| U_vs_random_walk | 0.41 | 1.01 |
| U_vs_constant_growth | 0.18 | 0.69 |
| final_year_err_pct | 8.74 | -1.38 |
| scored_years | 2014-2019 | 2022-2025 (2020-21 excluded) |
| tier2_spec | constant shares | coherence rule, shrinkage kappa = 512.0 |
| shares_RMSE_pp | 0.79 | 2.38 |
| shares_U_vs_random_walk | 1.00 | 1.00 |
| types_beating_rw | 0 | 3 |
| RMSE_pct_incl_pandemic | — | 18.92 |
| U_vs_rw_incl_pandemic | — | 0.82 |
| U_vs_cg_incl_pandemic | — | 0.68 |
<!-- /AUTO:holdout -->

**FR1 comparison.** <!-- AUTO:fr1gap -->
FR5 differs from FR1's own forecast of this series by +0.67% in 2026, +1.06% in 2030, and at most +1.87% (2028). Both start from the same 2025 value and use the same FR1 drivers but are different equations: the gap is a genuine modelling difference, not corroboration.
<!-- /AUTO:fr1gap -->

---

## 10. Baseline forecast 2026–2030

<!-- AUTO:forecast -->
| | 2025 | 2030 | per year |
|---|---|---|---|
| Volume, mn AZN at 2015 prices | 8,735 | 10,650 | **+4.04%** |
| Value, mn AZN current prices | 14,957 | 21,554 | **+7.58%** |

Annual volume growth: 2026 +0.64%, 2027 +5.55%, 2028 +4.70%, 2029 +5.01%, 2030 +4.41%. FR1 baseline real income per head: 2026 +0.04%, 2027 +4.17%, 2028 +3.46%, 2029 +3.72%, 2030 +3.21%; services deflator growth +3.40% a year on average; relative price of services -0.047 log points by 2030.
<!-- /AUTO:forecast -->

**Volume growth by type against its own history** (% a year):

<!-- AUTO:types -->
| type | label | forecast avg 2026–30 % | max forecast year % | 2010–19 % | 2021–25 % | best 5-yr avg % | window | exceeds best 5-yr |
|---|---|---|---|---|---|---|---|---|
| housing | Housing services | 4.18 | 5.74 | -1.06 | 20.59 | 51.93 | 2005-2010 | no |
| other | Other paid services | 4.18 | 5.74 | 7.65 | 7.30 | 100.30 | 2006-2011 | no |
| legal_bank | Legal and banking services | 4.14 | 5.69 | -4.01 | 8.60 | 78.20 | 2005-2010 | no |
| sport | Physical culture and sport | 4.14 | 5.68 | 8.04 | 13.08 | 79.97 | 2005-2010 | no |
| culture | Culture services | 4.13 | 5.68 | 7.36 | 14.47 | 61.25 | 2005-2010 | no |
| sanatoria | Sanatoria and health services | 4.13 | 5.68 | 6.58 | 24.92 | 44.52 | 2005-2010 | no |
| education | Educational services | 4.13 | 5.67 | 6.81 | 22.90 | 45.52 | 2005-2010 | no |
| tourism | Tourist and excursion services | 4.13 | 5.67 | 11.47 | 30.77 | 34.46 | 2006-2011 | no |
| utilities | Public utility services | 4.12 | 5.66 | 5.92 | 7.15 | 9.31 | 2005-2010 | no |
| transport | Transport services | 4.12 | 5.65 | 6.18 | 16.14 | 25.94 | 2005-2010 | no |
| medical | Medical services | 4.11 | 5.64 | 15.05 | 15.64 | 51.14 | 2005-2010 | no |
| communication | Communication services | 4.06 | 5.58 | 9.09 | 6.95 | 22.19 | 2005-2010 | no |
| household | Household (personal) services | 3.50 | 4.77 | 3.43 | 11.25 | 16.39 | 2005-2010 | no |
| TOTAL | TOTAL | 4.04 | 5.55 | 4.67 | 9.87 | 29.34 | 2003-2008 | no |

Flagged (forecast average above the type's own best five-year average): none.
<!-- /AUTO:types -->

**Uncertainty.** <!-- AUTO:bands -->
*Caution: only 9 joint historical residual paths (start years 2006–2014) are usable; the bands are indicative.* 1,000 replications (centred paths, parameter draws with sign rejection — 22.8% of E1 draws rejected — and 500 FR1 macro draws): 2030 volume 90% band 8,589–14,144 mn AZN (median 10,619); average volume growth -0.3% to +10.1% (median +3.98%); average value growth +1.5% to +15.7% (median +7.74%). FR5's own residual and parameter uncertainty alone: +2.2% to +6.7%. Variant pooling E1 and split paths over their own full samples: volume -0.6% to +11.2%, value +1.3% to +16.9%. Point forecasts inside the inter-quartile band: volume 5/5 years, value 5/5, shares 64/65 type-years.
<!-- /AUTO:bands -->

<!-- AUTO:scen -->
**Scenarios** (2030 volume): Baseline 10,650, Adverse 10,096, Reform 11,191 mn AZN — a 10.9% span; volume growth Baseline +4.04%, Adverse +2.94%, Reform +5.08%; value growth Baseline +7.58%, Adverse +6.23%, Reform +8.85%.
<!-- /AUTO:scen -->

## 11. Levers

<!-- AUTO:levers -->
| lever | volume 2030 | volume vs baseline % | value vs baseline % |
|---|---|---|---|
| chosen spec (income + relative price), eta = 1.44: its difference-form estimate | 11,094 | 4.17 | 4.17 |
| alternative specification: income deflated by service price (DOLS 2005-2025; incoherent), eta = 0.43, eps = -0.43 | 9,708 | -8.84 | -8.84 |
| alternative specification: income only (DOLS 2000-2025), eta = 1.67, eps = +0.00 | 11,361 | 6.68 | 6.68 |
| services relative price 10% higher (tariff lever) | 10,467 | -1.72 | 8.11 |
| services relative price 10% lower | 10,856 | 1.94 | -8.26 |
| population growth 0.3pp lower | 10,675 | 0.23 | 0.23 |
| population growth 0.3pp higher | 10,625 | -0.23 | -0.23 |
| add-factors decay, fixed half-life 1 year | 10,158 | -4.62 | -4.62 |
| type relative prices: 2020-25 drift continued, damped 0.5 | 10,650 | 0.00 | 0.00 |
| type relative prices: administered tariffs +2% a year | 10,650 | 0.00 | 0.00 |

Type relative-price levers change only the volume/price split within types; e.g. communication 2026 volume growth +0.64% in the baseline and +6.10% if its 2020–25 price drift were continued.
<!-- /AUTO:levers -->

Alternative specifications change the equation, not a parameter, and are labelled as such. The
add-factor decay case is a sensitivity only.

## 12. Limitations

1. **Driven by FR1's income and price paths.**
2. **The income elasticity is a range** from non-cointegrating level relations; "luxury" is not
   established.
3. **No adjustment dynamics** (no lagged dependent variable permitted).
4. **The type ranking is weakly supported**; shrinkage compresses it towards a common elasticity.
5. **IIA**, and no price term in the selected share system.
6. **Relative prices by type held constant** — exposed as levers.
7. **Add-factors held constant**; decay is a sensitivity only.
8. **Fans rest on nine centred joint paths** — indicative only.
9. **The aggregate does not beat a random walk on the 2022–2025 test window** (§9).
10. **Regional data could not be reconciled** (F5); "other paid services" has breaks; no household survey.

### What would improve the next vintage

- Household budget survey microdata.
- Reconciliation of the regional series with the national total (F5).
- A published price index per type of service and an administered-tariff calendar.
- An official population projection.
- A consistent back-series for "other paid services" before 2006.

## 13. Outputs

`FR5.ipynb` — executed end to end with 0 errors; its last code cell regenerates the numeric blocks of
this document. CSVs in `output/` include `FR5_forecast_long.csv`, `FR5_institutional_split.csv`,
`FR5_demand_system_coefficients.csv` (coefficients used, with SEs), `FR5_e1_coefficients.csv`,
`FR5_expenditure_elasticities.csv`, `FR5_income_elasticity_range.csv`,
`FR5_aggregate_specification_selection.csv`, `FR5_demand_system_specification_selection.csv`,
`FR5_engel_shrinkage_selection.csv`, `FR5_engel_level_vs_difference.csv`,
`FR5_type_growth_vs_history.csv`, `FR5_own_price_elasticities_forecast_system.csv`, `FR5_nonselected_*`,
`FR5_type_ranking_level_vs_difference_*.csv`, `FR5_holdout_validation.csv`, `FR5_fr1_comparison.csv`,
`FR5_fr1_drivers_baseline.csv`, `FR5_fan_*.csv`, `FR5_sensitivity_levers.csv`, `FR5_type_price_levers.csv`,
`FR5_equation_audit.csv`, `FR5_identity_checks.csv`, `FR5_rejected_specifications.csv`, and the DSK history.

**v2 (Part 19):** `FR5_equations.json` (tənliklər reyestri), `FR5_indicator_catalog.csv`, `FR5_forecast_tidy.csv`, `FR5_not_forecast.csv`, `FR5_robustness_summary.csv`, `FR5_coef_sensitivity.csv`, `FR5_strings_az.csv`, `engine/FR5_state.json` (+ `.npz`); ssenari mühərriki `microlib/engines/fr5.py`. Notebook `miis-model` kernel-i ilə işləyir (83 xana, 59 kod).
