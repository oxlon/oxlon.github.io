> **Azərbaycan dilində:** [az/FR3_Metodologiya.md](az/FR3_Metodologiya.md)

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
**Implementation:** `FR3.ipynb` (<!-- AUTO:v22_cells -->92 cells, 59 code<!-- /AUTO:v22_cells -->, runs end to end with no errors on the `miis-model` kernel; Part 21 = v2)
**Outputs:** 18 CSV files in `MicroUnit/output/` (new: `FR3_fan_wages.csv`, `FR3_specification_selection.csv`,
`FR3_homogeneity_break_tests.csv`, `FR3_minimum_wage_elasticities.csv`, `FR3_nowcast_2026.csv`, `FR3_forecast_sensitivity.csv`).
`FR3_wage_forecast_full.csv` keeps all its earlier columns (new columns added only).
**v2 outputs:** `FR3_equations.json`, `FR3_indicator_catalog.csv`, `FR3_forecast_tidy.csv`, `FR3_not_forecast.csv`, `FR3_robustness_summary.csv`, `FR3_coef_sensitivity.csv`, `FR3_strings_az.csv`, `engine/FR3_state.json` (+ `.npz`); engine `microlib/engines/fr3.py`.

---

<!-- AUTO:v22_note -->
## v2.2 (2026-10-05): data and approaches from the Ministry's macro module

**Data.** `data/macro_module/fr345_public_sources_panel.csv` (DSK 4.5–4.8 wages and 2.12 hired employees by 19 activities ×
state / non-state, 2005–2024; source path and MD5 in `data/macro_module/README_fr345.md`). Its state / non-state wages equal FR3's
series exactly, so **sector wages are published after all** — §8.1 and §8.2 below are superseded.

**Adopted — sector wages (8 DSK sectors) and budget / non-budget wages** (new components `fr3:sw:*`, `fr3:swg:*`, `fr3:w_budget`,
`fr3:w_nonbudget` + growth; `FR3_sector_wages.csv`, history `FR3_dsk_sector_wages_history.csv`). Rule chosen on rolling origins
2014–2016 (scored ≤ 2020): each sector keeps its relative wage of the last published year (2024); a relative-productivity driver is
worse (RMSE 14.9% vs 12.3%, DM p = 0.004; pooled β = +0.045, se 0.063) and is
registered as rejected. Sector hired weights move with FR3's sector employment; the weighted average equals FR3's average wage
(× the 2024 DSK aggregation ratio), so 2024 is reproduced exactly. Budget organisations (state units in public administration,
education, health and arts — FR4's definition; 588.6 thousand in 2024) keep their 2024 ratio to the state wage (0.923); the
non-budget wage follows from the identity. 2025 is an estimate (DSK ends in 2024). Hold-out (cut 2020, 2021–2024) with FR3's own
simulated average wage: beats the random walk in 6/8 sectors and constant growth in 1/8 (median U
0.64 / 1.28) — the sector errors inherit the aggregate's +12.7% bias; given the actual average wage
the composition rule beats them in 7/8 and 6/8. Budget wage: U 0.57 / 2.18.

| Baseline | 2024 actual | 2030 | % a year |
|---|---|---|---|
| Industry | 1,247.4 | 1,934.3 | +7.59 |
| Agriculture | 611.7 | 948.6 | +7.59 |
| Construction | 1,087.1 | 1,685.7 | +7.59 |
| Trade | 691.7 | 1,072.6 | +7.59 |
| Tourism & catering | 751.7 | 1,165.6 | +7.59 |
| Transport & storage | 1,392.5 | 2,159.3 | +7.59 |
| ICT | 1,672.1 | 2,592.9 | +7.59 |
| Social & other services | 1,025.6 | 1,590.4 | +7.59 |
| Budget organisations | 900.7 | 1,502.0 | +8.90 |
| Non-budget | 1,058.6 | 1,578.1 | +6.88 |

Because the relative wages are held at 2024, **every sector grows at the same rate** — the average-wage growth corrected for the
shift of employment between sectors (a factor common to all sectors); there is no sector-specific wage dynamics. This is the honest
result of the pre-cut test (no sector driver beats the anchored relative wage), not a convenience choice.

**Rejected (registered, not used).** (a) Aggregate, state and private wage equations re-estimated as activity-panel growth equations
(19 activities, 2006–2020, CPI + productivity + minimum wage, no lagged dependent variable): hold-out U vs random walk / constant
growth 0.73/3.82 (average; current 0.49/3.02), 0.59/1.92 (state; current 0.32/1.24),
1.04/8.70 (private; current 0.87/8.48) — CPI pass-through overshoots the 2021–22 inflation spike; **no wage equation
beats constant growth**, the weakness of §6.1 remains. (b) Sector employment on the long DSK 2.12 panel (two-way FE, β = 0.165,
DK se 0.058): share RMSE in the 2021–2024 hold-out 15.50% vs 14.22% for the current DVX elasticity (constant
shares 16.89%), so the current elasticity is kept. All tests: `FR3_macro_module_tests.csv`.

Registry now 97 equations (12 used); 109 components × 3 scenarios × 2026–2030; `FR3_not_forecast.csv`: 0 rows.
<!-- /AUTO:v22_note -->

---

## v2 (2026-10-05): tənliklər reyestri, ssenari mühərriki, dayanıqlıq

<!-- AUTO:v2 -->
**Tənliklər reyestri** (`output/FR3_equations.json`): 97 tənlik, onlardan 12-i proqnozda istifadə olunur
(E1–E4 DOLS, homogenlik real forma ilə qoyulub; sektor məşğulluğu üçün iki tərəfli FE; beş 2026 nowcast nisbəti; sahə
between paneli yalnız lövbərsiz həssaslıqda). Qalanları: E5, sürüşən başlanğıc namizədləri, həssaslıq variantları, ≤2020 qırılma/homogenlik test
reqressiyaları, P1, minimum əmək haqqı OLS/2SLS (DWH ilə), Gregory–Hansen, rədd edilmiş spesifikasiyalar, 2SLS/3SLS, sənaye və
region panelləri (within və between). Hər OLS/DOLS/2SLS/panel tənliyi statsmodels ilə yenidən qiymətləndirilib, əmsallar notebook-un
öz qiymətləri ilə yoxlanılıb (uyğunsuzluq: 0). Dayanıqlıq hökmləri (bütün tənliklər): qeyri-stabil 43, qismən stabil 38, stabil 16;
proqnozda istifadə olunanlar: qismən stabil 9, qeyri-stabil 2, stabil 1 — qeyri-stabil: FR3.E1_w_avg, FR3.E3_w_priv
(`FR3_robustness_summary.csv`).

**Ssenari mühərriki** (`microlib/engines/fr3.py`, `_fr3_core.py`; vəziyyət `output/engine/FR3_state.json` + `.npz`): notebook-un həll
kodu dəyişmədən köçürülüb (real forma/homogenlik, E4 → E1 → E2 → E3 ardıcıllığı, birgə WLS uzlaşdırması, nowcast artımının yarım
ömürlə sönməsi, sektor məşğulluğu, sahə əmək haqları). Girişlər: 16 FR1 yolu (`fr1:cpi`, `fr1:rgdp`,
`fr1:rgdpnon`, `fr1:emp`, `fr1:rexp_cur`, `fr1:rva_*`), 6 redaktə edilə bilən əmsal
(SE və 95% interval reyestrdən), 6 rıçaq (minimum əmək haqqı artımı, neft mükafatı hədəfi/yolu, nowcast yarım ömrü,
E1-in uzlaşdırmada rolu, sahə lövbəri). `selftest()`: bütün 3 ssenaridə CSV çıxışları təkrarlanır (maks. nisbi fərq
4.9e-14); rıçaqlar Part 15 həssaslıq cədvəlini dəqiq təkrarlayır. Bir ssenari < 0.1 s.

**Tam proqnoz cədvəli** (`FR3_forecast_tidy.csv`, `FR3_indicator_catalog.csv`): 109 komponent × 3 ssenari × 2026–2030
(hamısı dolu), tarix ilə; 5–95% zolaqlar 13 komponent üçün (Əsas ssenari). `FR3_not_forecast.csv`: 0 komponent —
heç bir komponent qalmır (v2.2: 8 sektorun və büdcə/qeyri-büdcə təşkilatlarının əmək haqları DSK 4.5–4.8 əsasında proqnozlaşdırılır, `FR3_sector_wages.csv`).

**Sahə əmək haqları (v2).** Baza proqnoz LÖVBƏRLƏNİB (digər modullardakı düzəliş əmsalı qaydası): hər sahənin between əlaqəsindən
2025 qalığı sabit saxlanılır, əlavə dəyəri olmayan iki sahə (metal filizləri, digər mədənçıxarma; əvvəllər boş) 2025 nisbi əmək
haqqında saxlanılır və məşğulluqla çəkilmiş orta bütün 29 sahə üzrə sənaye əmək haqqına dəqiq bərabərdir. FR1 sahəyə xas məhsuldarlıq
yolu vermədiyi üçün bütün sahələr sənaye əmək haqqı tempi ilə artır: 2026-da +6.67%…+6.67%
(bütün ssenarilərdə). Hər sahənin öz 2017-2025 tarixi ilə müqayisə (`FR3_branch_wage_plausibility.csv`): 2026 artımı öz
illik diapazonundan kənarda — 0 / 87 sahə-ssenari; 2026–2030 orta artımı öz 5 illik orta
diapazonundan kənarda — 35 (Avtomobil, qoşqu və yarımqoşquların istehsalı, Dəri və dəridən məmulatların,ayaqqabıların istehsalı, Elektrik enerjisi, qaz və buxar istehsalı, bölüşdürülməsi və təchizatı, Geyim istehsalı, Kimya sənayesi, Komputer, elektron və optik məhsulların istehsalı, Maşın və avadanlıqların istehsalı, Metal filizlərinin hasilatı, Metallurgiya sənayesi, Mədənçıxarma sənayesinin digər sahələri, Neft məhsullarının istehsalı, Su təchizatı, tullantıların təmizlənməsi və emalı, Tikinti materiallarının istehsalı, Toxuculuq sənayesi, Tütün məmulatlarının istehsalı, Xam neft və təbii qaz hasilatı, Zərgərlik məmulatları, musiqi alətləri,idman mallarının və tibb avadanlıqlarının istehsalı).
Lövbərsiz yol (sahə məhsuldarlığına uyğun nisbi səviyyə; 2026-da -25%…+76%,
54 sahə-ssenari öz tarixi diapazonundan kənarda) yalnız həssaslıqdır:
`FR3_industry_branch_wages_unanchored.csv`, mühərrikdə `branch_anchor = False`.

**Əmsal həssaslığı** (`FR3_coef_sensitivity.csv`, ±1 SE, 2030, Əsas): ən böyük təsirlər — Real orta aylıq əmək haqqı: FR3.E2_w_non|ln_prod_non (-0.67% / +0.68%); Real qeyri-dövlət (özəl) sektor əmək haqqı: FR3.E3_w_priv|ln_prod_non (-1.98% / +2.02%); Real dövlət sektoru əmək haqqı: FR3.E4_w_state|ln_prod_non (-1.51% / +1.51%). Mətnlər: `FR3_strings_az.csv` (431 ingiliscə mətn → azərbaycanca). Kernel: `miis-model` (Python 3.13).
<!-- /AUTO:v2 -->

---

## Revision note (2026-09-27)

This version implements an external review and the common fix contract shared with FR1, FR4 and FR5.

| # | What changed | Why |
|---|---|---|
| 1 | Every specification choice (drivers, homogeneity, break dummy) is made on data **ending in 2020**: tests on ≤2020 data and a **rolling-origin** forecast comparison (origins 2014–2016, scored on 2015–2020, Diebold–Mariano/HLN). 2021–2025 is used only as the final hold-out, scored against a random walk **and** constant growth. The oil-wage check now validates the mechanism actually used (non-oil wage × premium lever), and the wage bill is dropped from the validation table. | Specifications had been chosen and validated on the same 2021–25 window; the wage-bill "validation" repeated the average-wage error by construction. |
| 2 | The private wage is no longer regressed on the non-oil wage; it has its own fundamentals (chosen: non-oil productivity, homogeneous form). State-wage, oil-wage and ratio alternatives were tested and not selected. | The old E3 was near-tautological (private pay is over half the non-oil wage bill). |
| 3 | Minimum wage: removed from the instrument set; IV with its **lagged decree level**, Durbin–Wu–Hausman tests, a **2018 break** dummy and test (plus Gregory–Hansen), elasticities reported as a **range**; exclusion from the private equation re-decided on forecasting evidence. | The minimum wage responds to wages and was treated as exogenous; the 2018 reform dominates its variation. |
| 4 | Homogeneity is tested as the restriction the real form actually imposes — **CPI + nominal-driver elasticities = 1** — per equation, within DOLS, HAC-F; it is imposed in all forecasting equations on theory grounds (second round), rejections disclosed, unrestricted forms as sensitivities. | The earlier test (CPI elasticity = 1 alone) was the wrong restriction. |
| 5 | Engle–Granger p-values from MacKinnon's cointegration response surface; **DOLS** long-run coefficients (DOLS rule) are the ones used to forecast; EG reported for every equation; difference-form comparison. | The earlier p-values were plain ADF p-values; `dols` was defined but unused. |
| 6 | Hired-employment wedge calibrated on 2021–23 and validated on 2024–25; history spliced to the DVX level. | The wedge was calibrated and "validated" on the same years; the wage bill jumped at the forecast origin. |
| 7 | **Joint WLS reconciliation** of both breakdowns (state × private and oil × non-oil) over the component equations — both identities hold exactly; E1 a cross-check; adjustment factors reported. | The oil/non-oil dimension was never reconciled (5–6% gap by 2030). |
| 8 | Nowcast from a multi-year seasonal ratio, with a backtest error band; its increment decays with a one-year half-life. | One year's ratio was applied and the adjustment held to 2030. |
| 9 | True **between** estimator for the panels; Driscoll–Kraay bandwidth floor(T^¼), t(T−1) inference; the "panels support the levels form" argument deleted. | The 0.336 "between" was a one-way within estimator. |
| 10 | Non-oil productivity divides by **non-oil** employment. | It divided by all employed including oil. |
| 11 | **Fan charts** implemented (historical residual-path resampling + parameter + nowcast + FR1 macro draws), exported to `FR3_fan_wages.csv`. | Promised but not implemented. |
| 12 | Narrative corrected throughout (see §3, §6, §8). | Several statements contradicted the outputs. |

**Second round (2026-09-28).** An independent verification led to five further decisions, all implemented:
(a) the hold-out anchors **exactly as the forecast does** (each equation's own residual in the last pre-cut year); (b) long-run
**homogeneity is imposed in every forecasting equation on theory grounds** (no permanent money illusion), disclosed where the
short sample rejects it, with the unrestricted forms as sensitivities; (c) the 2018 **break dummy is not in the baseline**
because it cannot be scored out of sample before 2018 (its 0.843 state-wage elasticity is a sensitivity), and the
Diebold–Mariano tests are robust to overlapping multi-origin errors (Bartlett HAC, h−1 lags); (d) **E1 is a cross-check, not a
level constraint** in the reconciliation; (e) the fan charts use **historical residual-path resampling** (no estimated residual
dynamics); FR1 draws are screened only for non-finite values; (f) a **policy-lever coherence rule** (common to FR1/FR3/FR5): the
minimum wage enters a baseline equation only if its sign is consistent with theory (or its difference-form estimate is
significantly of the same sign) and it survives the 2018 break control — this excludes it from the private wage.

**Consequences for the headline numbers.** Baseline average-wage growth 2026–2030 is **+7.13% a year nominal, +2.64% real**
(first version +5.26% / +1.19%). Under the forecast's own anchoring rule the 2021–2025 hold-out is **poor against constant
growth**: the model beats a random walk for 4 of 5 series but constant growth for **none** (average wage: Theil U 0.49 vs random
walk, 3.03 vs constant growth; +12.7% level error by 2025). No equation establishes cointegration; the equations are descriptive
long-run relations with constant add-factors, not validated cointegrating relations.

**Dependency note.** FR3 reads FR1's scenarios and `FR1_fan_draws.csv` (500 draws in this run, none excluded). All numbers below
are from this run and will move with the final sequential FR1 → FR3 re-run.

---

## 1. Headline finding: the four required breakdowns do not nest

| Breakdown | Structure | Numerical verification |
|---|---|---|
| **State × non-state** | **Exact partition** of hired employees | Aggregate wage = employment-weighted average to **0.17–0.31%** |
| **Economic sectors** (8 DSK) | **Exact partition** of hired employees | Sector employment sums to the total **exactly (0.000)** |
| **Oil / non-oil** | **Cross-cutting**, not a third group | Treating it as a third group **double-counts by 6.7–10.4%**; oil/non-oil weighting reproduces the average to 1.9–3.7% |
| **Budget / non-budget** | Sub-partition of the state sector, partly observable | Headcount and contributions observed; wage level **not** identifiable |

Oil companies are *both* state (SOCAR) and private (the AIOC consortium), so oil cuts across the institutional split. FR3
therefore carries **two aggregations** to the same national average and, in the forecast, reconciles **both** to it jointly (§6.3).

---

## 2. A measurement issue that must be handled first

A wage is paid to a **hired employee**. Total employed persons include the self-employed: **2.06 million** hired against **5.11
million** employed in 2025.

| Wage bill, 2025 | mln AZN |
|---|---|
| wage × **hired** × 12 | 27,263 |
| DVX reported wage fund | 26,527 |
| compensation of employees (national accounts) | 38,227 |
| wage × **total employed** × 12 | **67,566** ← wrong by 2.5× |

Hired employment is published only for 2021–2025. For earlier years it is derived from compensation of employees divided by the
annual wage, with a wedge (**1.452**) **calibrated on 2021–2023** (in-sample error ≤ 1.51%) and **validated on 2024–2025**
(out-of-sample error up to **4.6%**). The history is then **spliced** to the DVX level (DVX itself for 2021–2025; the derived
series ratio-spliced at 2021, factor 1.014), and the forecast starts from the same DVX level — so the 2026 wage bill grows by
+7.5%, i.e. the wage growth (+6.9%) plus hired-employment growth, with no level break.

**A correction owed to FR1:** FR1's household-income equation builds its wage bill on total employment; the level is overstated,
though in logs the error is mostly absorbed by the intercept.

**Non-oil productivity** is non-oil value added divided by **non-oil** employment. Oil employment is the DVX count (2021–2025),
proxied before 2021 by the mining headcount ratio-spliced to DVX (2016–2020) and a constant share before 2016; in the forecast
the 2025 oil share (0.94% of employed persons) is held. The correction changes the level by about 1% and 2005–2025 growth by
0.5 pp in total.

---

## 3. Theory and the restrictions actually tested

$$\ln W = \alpha + \beta \ln(\text{productivity}) + \gamma \ln P + \delta \ln(\text{minimum wage}) + \theta\,\text{tightness} + \sum_j \phi_j \ln W_j$$

All inference uses HAC (Newey–West) with the n/(n−k) scaling, t(n−k) p-values and HAC-F(m, n−k) Wald tests. Long-run
relations are estimated by **DOLS** (leads and lags of the *regressor* differences only; ±1 when the residual df ≥ 10, else
contemporaneous differences, else OLS).

### 3.1 Nominal homogeneity — tested correctly, then imposed on theory grounds

With a nominal regressor in the equation (minimum wage, another wage), writing the equation in real terms imposes
**γ + δ = 1**, not γ = 1. The original version tested only γ = 1 (p = 0.65 in OLS levels); the correct restriction is rejected
for the aggregate in OLS levels (sum 1.186, se 0.073, HAC-F p = 0.018).

The restriction is tested per candidate, within DOLS, on data ending in 2020 (full sample for information;
`FR3_homogeneity_break_tests.csv`). For the chosen equations:

| Equation (drivers) | sum of price elasticities ≤2020 (se) | HAC-F p ≤2020 | sum / p ≤2025 | test result |
|---|---|---|---|---|
| E1 aggregate (productivity) | 1.305 (0.148) | 0.057 | 1.290 / 0.000 | not rejected ≤2020 (low power); rejected on the full sample |
| E2 non-oil (non-oil productivity) | 1.017 (0.196) | 0.932 | 1.028 / 0.849 | not rejected (low power) |
| E3 private (non-oil productivity) | 0.805 (0.043) | 0.001 | 0.588 / 0.009 | **rejected** |
| E4 state (non-oil productivity, minimum wage) | 0.970 (0.156) | 0.850 | 1.177 / 0.365 | not rejected (low power) |
| E5 oil (non-oil wage; reference only) | 2.185 (0.261) | 0.001 | 1.569 / 0.116 | rejected — E5 not used to forecast |

**Decision.** Long-run homogeneity is **imposed in every forecasting equation on theory grounds**: with a sum c ≠ 1 the real
wage would drift by (c − 1) × inflation every year for ever (for the private wage, the unrestricted CPI elasticity of 0.59 would
erode real private pay by about 0.4 × inflation a year). The rejection for the private wage is disclosed; it reflects the
2021–22 inflation spike (CPI +12.0% and +14.4%), when nominal private pay lagged prices. All candidates are scored in the
homogeneous form (§4), and the unrestricted forms are forecast sensitivities (§7). Standard errors of 0.10–0.20 on the tested
sums mean "not rejected" is low power, not confirmation.

### 3.2 The 2018 minimum-wage reform: a break test

A level-shift dummy D18 (1 from 2018) is tested in the general form of every candidate (HAC-F, ≤2020). It is significant for the
state wage (p < 0.001 on both samples), for the non-oil candidate with the minimum wage and for the ratio model; not for E1
(p = 0.559), E2 (0.961) or the chosen E3 (0.754). Because D18 is zero at every selection origin (2014–2016), a specification with
it **cannot be scored out of sample**, so it is **not in the baseline**; the state-wage version with D18 (minimum-wage elasticity
0.843) is a forecast sensitivity. A Gregory–Hansen-type test (one level shift at an unknown date, model C critical values) does
not establish cointegration for any forecasting equation (ADF* −3.94 to −4.32 against 5% critical values −4.61 / −4.95).

### 3.3 Cross-wage spillovers — the "related sectors" mechanism

Tested as candidates in the rolling-origin comparison (§4); none is selected:

- **Oil-sector wage (Dutch disease)** in the private wage: rolling RMSE 5.84% vs 5.09% for the chosen equation (DM p = 0.16).
- **State-wage spillover** into the private wage: 5.18% vs 5.09% (DM p = 0.85) — no better, and more complex.
- **Private/state ratio model**: 12.62% vs 5.09% (DM p = 0.006).
- **Private-wage spillover into state pay** (OLS levels, with fiscal capacity and the floor): +0.009, p = 0.987.
- The original E3 (private on the real non-oil wage) is dropped as near-tautological (OLS 0.53 vs 2SLS 0.17 in the first run).

Wages are linked through the two aggregation identities and the reconciliation, and the oil wage through the premium lever.

### 3.4 The minimum wage: indexation, endogeneity and a range of elasticities

The minimum wage responds to wages: long-run elasticity to the average wage **1.50** (DOLS; unit indexation rejected, p < 0.001).
It is instrumented with its **lagged decree level** (fixed before the year's wage outcomes; an instrument, not an autoregressive
term). Where the instrument is strong (5 cases, first-stage F 10–32: all four equations without D18, and the aggregate with it)
**Durbin–Wu–Hausman rejects exogeneity in 4 of 5** (not for the private wage, p = 0.34); in the other D18 variants it is weak
(F 0.5) and those IV estimates are discarded. Ranges across
the credible variants (OLS levels, DOLS, 2SLS; with/without D18; all in the homogeneous form):

| Equation | range of the minimum-wage elasticity | in the forecast |
|---|---|---|
| aggregate (E1 candidate) | 0.14 – 0.32 | no (not selected) |
| non-oil (E2 candidate) | 0.06 – 0.49 | no (not selected) |
| **private** (E3 candidate) | **−0.25 – −0.01** | **no** — fails the lever-coherence rule; sensitivity only (−0.247) |
| **state** (E4) | **0.24 – 0.84** | **yes: 0.386** (DOLS, no dummy; 3SLS 0.096; D18 version 0.843 as sensitivity) |

In the homogeneous form the minimum wage has the lowest rolling RMSE for the private wage (3.65% vs 5.09% without it, DM
p = 0.054), but with a **negative** sign. It fails the **policy-lever coherence rule** on ≤2020 data: (a) level −0.044 with a
difference-form estimate of −0.029 (p = 0.66), so neither theory-consistent nor significantly negative in differences; (b) with the
2018 dummy it becomes +0.008 (p = 0.93) — a timing artefact of the reform (it raised public pay; private pay did not follow). It
is therefore **excluded from the private equation**; the E3-with-minimum-wage variant is a labelled sensitivity. The minimum-wage
lever now acts on the state wage (and through the reconciliation on the aggregate), and the scenario ordering is monotone for
every group (§7).

### 3.5 Labour-market tightness — no channel exists

Unemployment enters positively in growth form (+1.3 to +2.0, p 0.10–0.41) and insignificantly in levels. Measured unemployment
stayed within **4.9–5.6% every year except 2020**. Dropped.

---

## 4. Specifications chosen on rolling origins before the hold-out

Origins 2014, 2015 and 2016; estimate on data ≤ origin (DOLS rule), anchor on the origin year's own residual, predict every year
to 2020 with actual drivers (15 errors per candidate), all candidates in the homogeneous form. Candidates whose policy lever fails
the coherence rule (§3.4) are scored and shown but cannot be selected. Lowest RMSE wins unless a simpler
candidate is not significantly worse (DM-HLN with Bartlett HAC over h−1 = 5 lags, robust to the overlap of multi-origin errors;
p > 0.10).

| Group | Candidate | lever coherent | homogeneity test ≤2020 | rolling RMSE % | DM p vs best | chosen |
|---|---|---|---|---|---|---|
| E1 | productivity + minimum wage | yes | not rejected | 10.24 | 0.68 | |
| E1 | **productivity** | — | not rejected | **8.87** | — | ✓ |
| E2 | non-oil productivity + minimum wage | yes | not rejected | 12.36 | 0.12 | |
| E2 | **non-oil productivity** | — | not rejected | **8.26** | — | ✓ |
| E3 | **non-oil productivity** | — | rejected | **5.09** | — | ✓ |
| E3 | non-oil productivity + minimum wage | **NO** | rejected | 3.65 | better (p 0.054) | excluded |
| E3 | + state wage | — | rejected | 5.18 | 0.85 | |
| E3 | + oil wage (Dutch disease) | — | not rejected | 5.84 | 0.16 | |
| E3 | ratio to the state wage | — | not rejected | 12.62 | 0.006 | |
| E4 | **non-oil productivity + minimum wage** | yes | not rejected | **15.96** | — | ✓ |
| E4 | minimum wage only | yes | rejected | 46.43 | 0.005 | |
| E4 | fiscal capacity + minimum wage | **NO** (fails the break control) | not rejected | 22.08 | 0.46 | |

**Oil wage.** On the same origins, holding the oil/non-oil premium at its latest value (RMSE 22.9%) beats the pre-origin average
(37.7%, DM p = 0.003) and a linear trend (41.1%, p = 0.047); a quadratic trend is worse (54.5%, p = 0.27). The premium rose from
3.2× (2010) to 6.6× (2017) and has fallen to **3.75× (2025)**. The oil wage is **not** forecast from E5; it is the reconciled
non-oil wage times an explicit **premium lever**.

---

## 5. The final equation set

Full-sample DOLS in the homogeneous (real) form; the long-run coefficients are used in the forecast.

| # | Dependent | Long-run coefficients (HAC se) | estimator, n, df | R² | EG coint p | difference form |
|---|---|---|---|---|---|---|
| E1 | ln real average wage (cross-check) | productivity 1.040 (0.054) | DOLS(±1), 25, 20 | 0.974 | 0.339 | 0.563 ⚑ |
| E2 | ln real non-oil wage | non-oil productivity 1.052 (0.086) | DOLS(±1), 20, 15 | 0.956 | 0.794 | 0.880 |
| E3 | ln real private wage | non-oil productivity 0.432 (0.129) | DOLS(±1), 20, 15 | 0.851 | 0.614 | 0.457 |
| E4 | ln real state wage | non-oil productivity 0.626 (0.154); real minimum wage 0.386 (0.074) | DOLS(±1), 20, 11 | 0.981 | 0.330 | 0.988; 0.104 ⚑ |
| E5 | ln nominal oil wage (reference only) | non-oil wage −0.089 (0.514); ln CPI 1.658 (0.822) | DOLS(0), 20, 15 | 0.916 | 0.927 | — |
| P1 | ln minimum wage (reported, not used) | average wage 1.502 (0.052) | DOLS(±1), 25, 20 | 0.988 | 0.905 | — |

⚑ = level coefficient outside the difference-form 95% interval. **Cointegration is not established for any equation** (EG p
0.33–0.93), so all t-statistics are labelled *descriptive* in `FR3_equation_audit.csv`; base add-factors are held constant because
residuals are not shown to be stationary.

**Panels.** The industry panel (27 branches with value added, 10 years) gives a two-way **within** elasticity of 0.065 (DK, t(9)
p = 0.078) and a true **between** elasticity (branch means) of **0.305** (se 0.049); the one-way FE estimate 0.336 is a within
estimator. The regional panel gives within 0.070 and between 0.269 (se 0.186, 13 regions). These are cross-sectional facts about
level differences; they do **not** establish a cointegrating levels relation for the national series.

**Simultaneity.** The contemporaneous minimum wage is no longer an instrument. With the revised set, 2SLS moves the state-wage
minimum-wage coefficient (with D18) from 0.474 (OLS) to 0.922 but with a **weak** first stage (F = 4.0) and Sargan p = 0.032
(**rejected**); for E5, OLS 0.257 vs 2SLS −0.387, Sargan p = 0.043 (**rejected**). These differences are large. 3SLS on the four
forecasting equations (2010–2025, 16 observations) is a cross-check only (state-wage minimum-wage coefficient 0.096).

---

## 6. Validation

**Estimators** are revalidated against `statsmodels` to machine precision (OLS, HC1, HAC with n/(n−k), Engle–Granger p via
`coint`, 2SLS, 3SLS, panel FE).

### 6.1 Dynamic ex-post hold-out, 2021–2025

Everything re-estimated on data ≤ 2020; add-factors follow **exactly the forecast's rule** (each equation's own 2020 residual);
premium lever held at its 2020 value (5.14×); reconciliation as in the forecast (E1 a cross-check), with employment shares from
2021 DVX (stated proxy — no earlier split exists) and identity discrepancies evaluated with 2020 wages; actual drivers and minimum
wage; no wage fed back; no nowcast. Log errors ×100; constant growth = 2010–2020 average growth of each series.

| Variable | model RMSE | U vs random walk | U vs constant growth | DM p vs RW / CG | 2025 level error |
|---|---|---|---|---|---|
| **average wage** | 14.5% | **0.49** | **3.03** | 0.15 / 0.01 | +12.7% |
| non-oil wage | 11.9% | 0.37 | 1.50 | 0.11 / 0.20 | +8.8% |
| private wage | 18.8% | 0.87 | 8.48 | 0.63 / 0.01 | +20.0% |
| state wage | 11.8% | 0.33 | 1.24 | 0.09 / 0.47 | +7.4% |
| oil wage (non-oil × premium lever) | 35.3% | 3.80 | 1.07 | 0.003 / 0.39 | +49.3% |

**Headline: beats a random walk for 4 of 5 (median U 0.49) and constant growth for none (median U 1.50).** Where DM p < 0.10
against constant growth (average and private wage) the model is significantly *worse*. The errors come from anchoring on the
2020 (COVID-year) residual and from the 2021–22 inflation spike: with the 2018–2020 average residual as anchor (labelled
sensitivity) the RMSE would be 5.3% (average), 3.4% (non-oil), 15.5% (private), 6.5% (state), 25.8% (oil). Other sensitivities:
the unreconciled E1 alone has an average-wage RMSE of 8.7%; giving E1 a finite weight gives 12.6%; reconciling *to* E1 8.7%.
The wage bill is not a separate target (its error equals the average-wage error by construction). The oil error is the premium:
held at 5.14× while the actual fell to 3.75×.

### 6.2 2026 nowcast

The 2026 January–February average is divided by the **average ratio of that window to the annual average over 2021–2025**. A
backtest (each year using only earlier ratios, 2022–2025) gives the error band. In this short backtest the multi-year rule is not
more accurate than the single-year y/y rule (average wage RMSE 2.18% vs 2.11%); it is preferred because it does not rest on one
year's seasonality, and its band enters the fan charts.

| Series | 2025 | 2026 nowcast | growth | backtest RMSE | old y/y rule |
|---|---|---|---|---|---|
| average wage | 1,102.9 | 1,179.4 | +6.94% | ±2.2% | 1,161.6 |
| oil sector | 3,938.6 | 4,320.2 | +9.69% | ±6.3% | 4,330.8 |
| non-oil sector | 1,050.7 | 1,124.4 | +7.02% | ±1.8% | 1,105.3 |
| state sector | 1,080.8 | 1,167.2 | +7.99% | ±2.6% | 1,152.4 |
| private sector | 1,124.4 | 1,187.1 | +5.58% | ±1.8% | 1,168.5 |

The nowcast increment over the model applies fully in 2026 and decays by half each year (a judgemental adjustment rule, not a
model of the dependent variable). Base add-factors (own 2025 residuals: E1 0.139, E2 0.043, E3 −0.092, E4 0.077 log points) stay
constant.

### 6.3 Joint reconciliation of both breakdowns

The component equations (E2, E3, E4; the oil wage via the premium) are reconciled by weighted least squares (Stone's method),
with weights inversely proportional to each equation's pre-2021 rolling-origin MSE, subject to both identities, exactly:
institutional $W = k_1(s_{state}W_{state}+s_{priv}W_{priv})$ and oil/non-oil $W = k_2(s_{oil}\,\text{prem}\,W_{non}+(1-s_{oil})W_{non})$,
with the data's own 2025 discrepancies $k_1$ = 0.998, $k_2$ = 0.982 held fixed. **E1 is not a level constraint**: it is driven by
total productivity, which falling oil output drags down, while the components use non-oil productivity, so E1 and E2 drift apart
(with a finite E1 weight the aggregate was pulled down and the non-oil wage pushed ~3% below its own equation by 2030); E1's
pre-2021 record (RMSE 8.9%) is no better than E2's (8.3%). The aggregate is the identity over the reconciled components and E1 is
a cross-check. Identity residuals < 10⁻⁷% in every scenario and year. Baseline factors (reconciled ÷ equation), 2026 → 2030:
state 1.005 → 1.062, private 1.001 → 1.007, non-oil 0.997 → 0.966; the reconciled aggregate differs from E1's own
prediction by 0.0% → +3.9%. In 2026 the reconciled values are within 0.6% of the nowcasts.

---

## 7. Forecast results, 2026–2030

Macro drivers come from FR1's scenarios. FR3's levers: **minimum wage** (6% / 3% / 9% nominal growth a year) and the **oil premium
path** (from the 2026 nowcast value 3.84× to 3.4× / 3.2× / 3.7× by 2030). Hired employment follows FR1's employment at the 2025
hired share from the DVX level; state/private and oil shares are held. FR3 uses no population assumption.

| Baseline | 2025 | 2030 | nominal % p.a. | real % p.a. |
|---|---|---|---|---|
| Average wage | 1,102.9 | 1,556.4 | **+7.13** | **+2.64** |
| Non-oil sector | 1,050.7 | 1,495.0 | +7.31 | +2.81 |
| State sector | 1,080.8 | 1,625.9 | +8.51 | +3.96 |
| Private sector | 1,124.4 | 1,507.1 | +6.03 | +1.59 |
| Oil sector | 3,938.6 | 5,083.1 | +5.23 | +0.83 |

| | Baseline | Adverse | Reform |
|---|---|---|---|
| Average wage, nominal % p.a. | 7.13 | 5.67 | 8.59 |
| Average wage, **real** % p.a. | 2.64 | 1.55 | 3.74 |
| Real non-oil wage % p.a. | 2.81 | 1.82 | 3.76 |
| Real private wage % p.a. | 1.59 | 1.13 | 2.03 |
| Real state wage % p.a. | 3.96 | 2.10 | 5.83 |
| Real oil wage % p.a. | 0.83 | −1.35 | 3.49 |

The ordering **Adverse ≤ Baseline ≤ Reform holds for every group** (checked in the notebook).

Baseline wage bill: 29,302 mln AZN in 2026 (+7.5%) rising to 39,729 mln in 2030. The
**state/private ratio** is 0.99 in 2026 and 1.08 in 2030 in the baseline (passing 1.00 in 2027), 1.01 in 2030 in
the Adverse and 1.15 in the Reform scenario, driven by the minimum wage in the state equation.

**Sensitivity** (baseline, nominal % p.a.; average / state / private):

| Variant | average | state | private |
|---|---|---|---|
| **Main** (joint WLS, E1 cross-check, constant base add-factors) | 7.13 | 8.51 | 6.03 |
| reconciled strictly to E1 | 6.31 | 6.91 | 5.84 |
| E1 as a weighted constraint | 6.89 | 8.04 | 5.98 |
| base add-factors decaying at the residual ρ̂ (contract decision 4) | 6.83 | 6.08 | 7.39 |
| E3 unrestricted (ln CPI elasticity 0.588) | 7.16 | 8.46 | 6.13 |
| E3 with the minimum wage (−0.247; fails lever coherence) | 7.36 | 8.09 | 6.79 |
| E4 unrestricted (ln CPI free) | 7.05 | 8.30 | 6.05 |
| E4 with the 2018 dummy (minimum-wage elasticity 0.843; unscored) | 7.16 | 8.57 | 6.03 |

**Against FR1's own wage forecast.** FR3's average wage differs from FR1's `wage` column by +3.6% in 2026 and
+3.4% in 2030 (baseline); across scenarios the gap is +1.6% to +5.4%. FR3 is the published wage forecast.

**Decomposition.** Historically (2021–2025) almost all growth is the **within** term; the **between** term is small and positive
(+0.10 to +0.30 pp a year), as employment shifted toward the better-paid non-state sector. In the forecast the shares are held, so
the between term is zero by construction.

### 7.1 Forecast uncertainty

1,000 replications combining **historical residual-path resampling** — a start year *s* is drawn and the joint deviations
$u_{s+h}-u_s$ ($h$ = 1…4) of the four equations' long-run residuals and the log premium are added for 2027–2030, which carries the
empirical persistence and cross-equation correlation without estimating any residual process (no AR component) — with
coefficient draws from N(β̂, V̂_HAC), a joint nowcast-error draw and FR1's baseline macro draws (500 used of 500; screened for non-finite values only, 0 excluded). Growth bands are quantiles of per-replication
growth.

| Baseline, 2030 | 5% | 25% | median | 75% | 95% | central |
|---|---|---|---|---|---|---|
| Average wage, AZN | 1,104 | 1,335 | 1,586 | 1,872 | 2,313 | 1,556 |
| Average wage growth in 2030, % | −4.0 | 3.1 | 8.2 | 14.2 | 23.8 | 7.3 |
| State wage, AZN | 1,122 | 1,373 | 1,630 | 1,933 | 2,424 | 1,626 |
| Private wage, AZN | 1,017 | 1,286 | 1,534 | 1,858 | 2,315 | 1,507 |
| Oil wage, AZN | 3,021 | 4,007 | 4,988 | 6,364 | 9,341 | 5,083 |

**Sanity check.** From FR3's own sources alone (macro at baseline) the 90% level half-widths for the average wage are
3.5% (2026) and 10–17% (2027–2030), against a hold-out RMSE of 14.5%; for the state wage
14–22% against 11.8%; for the private wage 9–14% against 18.8%. The level bands are of the
same order as the realised hold-out errors. Single-year growth bands are wider than the historical growth range (the lowest annual
average-wage growth since 2005 is +3.0%), because historical residual deviations include large year-to-year swings; with 17
possible start years the bands are lumpy. Both variants are in `FR3_fan_wages.csv` (column `sources`).

---

## 8. What the data cannot deliver

### 8.1 Average wages by economic sector — not derivable

<!-- AUTO:v22_s81 -->
> **v2.2: superseded.** DSK 4.5–4.8 publishes them (2005–2024); FR3 now forecasts all eight (see the v2.2 note).
<!-- /AUTO:v22_s81 -->

**Attempt 1** — allocate wages by value added per hired worker with the between-branch elasticity (0.305), anchored to the national
wage. Rejected: the derived **industry** wage is **25–42% above** the actual one (industrial value added per worker, 216 thousand
AZN, is largely oil and gas rent), and **agriculture becomes the best-paid sector at 1.40–1.46× the average** (only about 50 of
~1,000 thousand agricultural workers are hired).

**Attempt 2** — strip the rent and search for the elasticity that fits industry: always possible for one target, but agriculture
still comes out far above average. Curve-fitting, not identification.

**Delivered instead:** industrial wages at 2-digit level (v2: all 29 sub-branches that publish wages are forecast, anchored on each branch's own 2025 residual — the add-factor convention — with the adding-up over all 29 exact; the unanchored between-branch path is a labelled sensitivity), the
hired-employment composition of all eight sectors, and the decomposition machinery. **What would fix it:** a sector breakdown of the
wage fund or of compensation of employees.

### 8.2 Budget versus non-budget average wages — not identifiable

<!-- AUTO:v22_s82 -->
> **v2.2: superseded.** DSK 4.5–4.8 state wages in the four budget-financed activities identify them (2024: 900.7 vs 1,058.6 AZN); forecast in v2.2.
<!-- /AUTO:v22_s82 -->

The employer rate is recoverable from the budget's accounts (212100 ÷ 211xxx ≈ 0.218, the statutory 22%), but applying assumed
rates to DVX budget-organisation contributions gives a 2025 budget wage of 1,062–1,399 AZN depending only on the rate, and every
variant puts the budget wage above the non-budget wage, contradicting the published state < private ordering. The split is
reported as observables — headcount (588 thousand, 29% of hired employees) and contributions (34% of the total). The fiscal
211xxx pay lines (**4,017 mln AZN** in 2025) cannot be the economy-wide budget payroll: education spending alone is 4,618 mln.

### 8.3 A data error found in the source

Rows **127–129** of the DVX sheet are byte-identical to rows 123–125 (micro taxpayers). Only row 130 (employee count) is genuine.

---

## 9. Limitations

1. <!-- AUTO:v22_limits -->(v2.2) Sector and budget / non-budget wages are published only to 2024 and are forecast with relative wages held at 2024 — no sector-specific driver beats that rule.
2. (v2.2) The DSK and published averages differ by up to 1.05% (hired weights); the ratio is held at 2024.<!-- /AUTO:v22_limits -->
3. Source data error in DVX rows 127–129 (§8.3).
4. The **oil wage** is not forecast by an equation: it is the non-oil wage times a stated premium lever; in the hold-out a random
   walk beats that mechanism (U 3.80) and constant growth roughly ties (1.07).
5. **The hold-out is poor against constant growth**: under the forecast's own anchoring rule the model beats constant growth for
   none of five series (average wage U 3.03, +12.7% by 2025). The anchor year matters a great deal (2018–20 average anchor: 5.3%).
6. **Cointegration is not established** for any equation (EG and Gregory–Hansen); t-statistics are descriptive and base
   add-factors are held constant.
7. **Homogeneity is imposed on theory grounds** though rejected for the private wage on the short sample; the unrestricted form
   gives 6.13% instead of 6.03% a year private-wage growth.
8. The **minimum-wage effect is imprecise**: state 0.24–0.84 (forecast 0.386; 0.843 with the unscored break dummy). In the
   private wage its estimates are negative (−0.25 to −0.01) but fail the lever-coherence rule, so it is excluded there; any true
   private-sector effect is not captured.
9. **No tightness channel.**
10. **Hired employment before 2021 is derived** (out-of-sample error up to 4.6% in 2024–25).
11. **Short samples:** 20–25 observations per forecasting equation (residual df 11–20), 15 overlapping errors per candidate in
    the selection, 5 hold-out years, 5 years of DVX employment.
12. **Employment composition is held fixed** beyond 2026 (state and oil shares, branch structure, hired share).
13. **FR3 inherits FR1's macro uncertainty** through the FR1 draws (§7.1).
14. The **two source systems disagree by −4% to +2%** on the average wage (DSK vs DVX); FR3 forecasts DSK.

## 10. What would most improve FR3

1. **Sector wage funds or compensation of employees by sector** — the largest gap, the first breakdown FR3 asks for.
2. **The statutory contribution-rate schedule by segment**, or the budget-organisation wage fund.
3. **Hired employment by sector and institution back to 2005.**
4. **Monthly wage data before 2021** — would make the nowcast seasonal factor and its error band far more reliable.
5. **A published median wage or wage distribution** — to identify the minimum wage's compression effects.
