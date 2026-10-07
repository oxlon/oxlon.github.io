> **Azərbaycan dilində:** [az/FR10_Metodologiya.md](az/FR10_Metodologiya.md)

# FR10 — Financial condition, production efficiency and market position of enterprises and productions
## Structural methodology, indicator system and five-year forecast

**MIIS module 15.5.2 — Microeconomic analysis and forecasting**
Ministry of Economy of the Republic of Azerbaijan

Companion to `FR10.ipynb`. Builds on **FR1** (sector output, prices, macro economy), **FR3** (wages) and
**FR4** (employment).

---

## Revision / status note (2026-10-05, v2)

**v2 adds, without changing any Layer-A result:** (1) an equation registry `output/FR10_equations.json` with every
equation estimated in the notebook (full regression output in Azerbaijani, diagnostics, recursive / leave-one-year-out
robustness, hold-out blocks), (2) an indicator catalogue and a complete forecast table for every component, scenario and
year, (3) a scenario engine `microlib/engines/fr10.py` that reproduces the forecast exactly and lets the user change
FR1's driver paths, the forecast coefficients and the levers, (4) a robustness summary and a coefficient tornado,
(5) Azerbaijani versions of every English string in the CSVs (official DSK names for products and places), and
(6) a **full firm-level econometric analysis in Layer B** (§15.1) that runs on whatever firm panel is loaded — on the
SYNTHETIC panel now, every output watermarked and registered `synthetic: true`. Details: §19.

*Xülasə (AZ):* v2 tənliklər reyestrini, göstərici kataloqunu, tam proqnoz cədvəlini, ssenari mühərrikini, dayanıqlıq
xülasəsini və B qatında müəssisə səviyyəsində tam ekonometrik təhlili əlavə edir; A qatının nəticələri dəyişmir. B qatı
hazırda **sintetik məlumat — texniki nümayiş** üzərində işləyir.

## Revision / status note (2026-10-05, v2.1 — data-integrity fixes)

**What was wrong.** Branch real output (`output_real_mn_AZN_2015`) and the branch deflator (`deflator_2015_1`) are
chained from DSK's volume indices (table 009, sheet 9.1) on 2015 nominal output. For several small branches DSK's index
is inconsistent with the branch's own nominal output — e.g. electrical equipment (27) 2020: index 8 500% while nominal
output fell 7% (implied deflator ÷ 100); pharmaceuticals (21) 2020: 11 200%; motor vehicles (29) 2010: 84 400% and
2018: 31 000%. Chained as published, real output in 2025 was 429 times nominal output in branch 27, 195 times in 21 and
44 times in 16; the forecast then took branch 27 to about 186 bn AZN (2015 prices) in 2030 — more than national real
GDP — with labour productivity of 61 mn AZN per worker, and product volumes jumped by up to +181% from 2025 to 2026.
The defect predates v2.

**The rule (Part 5.1, toolkit `validate_volume_index`).** Before chaining, every branch-year index is tested.
**T1:** the implied deflator change (N_t / N_t−1) / (I_t / 100) outside ×1/3…×3. **T2** (after T1, walking outward
from 2015): the branch deflator relative to the manufacturing (section C) deflator, 2015 = 1, outside 1/6…6. Both bands
lie just outside the envelope of the branches T1 never flags (figures in the block below), so the rule cannot touch a
well-behaved branch in 2005–2025. A failing index is replaced by the branch's nominal growth deflated by the
manufacturing deflator change of the same year (the branch's relative price is held in that year). The replaced points
are flagged: `imputed` = True in `FR10_forecast_tidy.csv` and `imputed_years` in the catalogue (for real output and
labour productivity, the year whose real level is derived through the replaced link), finding **F15** (English and
Azerbaijani) lists every replaced branch-year with its published index, and `FR10_volume_index_validation.csv` gives the
details. The notebook asserts that afterwards every branch passes both tests in every year and that every branch's
2030 real output stays below section C real output.

**Effect.** No coefficient of an equation used in the forecast changes: the share systems, the pooled related-sector
model, the refining block, the mining rules and the regional system are estimated on nominal shares, the refining
deflator and FR1's drivers. What changes: real output, the deflator, labour productivity, TFP and the growth
decomposition of the affected branches, in history and forecast (non-oil real output = nominal ÷ (2025 deflator × FR1
index), so the 2025 deflator carries the fix into 2026–2030); the determinants panel (not used in the forecast, §10); the real-output hold-out scores (§12); the plausibility
flags (§14).
Nominal output, shares, sections, regions — hence FR12's inputs — do not change.

**Also in v2.1.** (i) **Products** are anchored on the 2025 actual (constant base add-factor; there are no partial-year
product data, so no decaying increment); with the 2023–25 average intensity, 38 products had jumped by more than 25%
between 2025 and 2026. (ii) The 13 **regional equations** whose slope is empirical-Bayes-shrunk now carry an
`eb_shrinkage` restriction (`imposed: true`, estimate, prior mean, weight, κ, τ²) and `fixed: true` on the shrunk
coefficient. (iii) The **scenario engine** takes FR4's hired-employee paths from the upstream FR4 result in a chained run
(`chain.run_chain`), so an FR4 change reaches FR10's employment and labour productivity; FR3 is not used by FR10 (F13).

<!-- AUTO:v21 -->
Volume-index validation: **64 branch-year indices replaced in 15 branches** (T1 41, T2 23; 29 in 2005–2025). Bands from the 17 branches T1 never flags: their one-year deflator changes 1996–2025 lie in ×0.34–×2.85 (T1 band ×1/3–×3) and their deflators relative to manufacturing 2005–2025 in 0.26–5.24 (T2 band 1/6–6). After the fix every branch passes both tests in every year, and every branch's 2030 real output is below section C real output in all scenarios (largest: 06, 13,084 vs 18,341+ mn AZN 2015). Full list: `FR10_volume_index_validation.csv`; per-branch deflator ranges: `FR10_branch_deflator_check.csv`.

| nace2 | branch | replaced (year, test, published index) | real/nominal 2025, published indices | real/nominal 2025, validated | real output 2030 (Baseline), mn AZN 2015 | labour productivity 2030, thsd AZN 2015 |
|---|---|---|---|---|---|---|
| 07 | Metal ores | 2000 (T1, 631.7), 2003 (T1, 829.3), 2008 (T1, 159.7) | 0.22 | 0.22 | 151.61 | 64.16 |
| 14 | Wearing apparel | 1998 (T2, 82.6) | 1.31 | 1.31 | 410.80 | 74.55 |
| 16 | Wood products | 1997 (T1, 21.1), 1999 (T2, 103.1), 2000 (T1, 194.5), 2013 (T1, 91.6), 2014 (T1, 305.9), 2020 (T2, 256), 2023 (T1, 165.1), 2024 (T2, 125.9) | 44.24 | 4.20 | 249.98 | 301.42 |
| 17 | Paper products | 1999 (T2, 171), 2002 (T2, 61.3) | 0.31 | 0.31 | 134.85 | 55.85 |
| 21 | Pharmaceuticals | 2011 (T2, 83.7), 2016 (T1, 122.4), 2020 (T1, 11200) | 194.91 | 0.96 | 45.45 | 75.76 |
| 22 | Rubber and plastics | 1996 (T1, 77.8), 1998 (T2, 80.5), 1999 (T2, 40.3), 2000 (T2, 76.7), 2001 (T1, 52.9), 2002 (T2, 86.9), 2004 (T2, 126.5) | 1.75 | 1.75 | 1,819.75 | 247.38 |
| 25 | Fabricated metal products | 1996 (T1, 85.7) | 0.79 | 0.79 | 907.05 | 128.70 |
| 26 | Computer and electronics | 2000 (T2, 36.9), 2002 (T2, 54.4), 2004 (T2, 67.5), 2005 (T1, 75.7), 2006 (T2, 64.9), 2007 (T2, 92.3) | 2.26 | 2.26 | 247.64 | 965.90 |
| 27 | Electrical equipment | 2011 (T1, 72.9), 2016 (T1, 333.8), 2020 (T1, 8500) | 428.67 | 1.11 | 476.16 | 157.59 |
| 28 | Machinery and equipment | 2025 (T1, 84.1) | 1.42 | 0.40 | 81.77 | 28.16 |
| 29 | Motor vehicles | 1997 (T1, 112.3), 2000 (T1, 1156.4), 2003 (T1, 119.5), 2006 (T1, 2230.7), 2009 (T1, 23), 2010 (T1, 84400), 2012 (T1, 27.8), 2014 (T1, 158.2), 2017 (T1, 1.2), 2018 (T1, 31000) | 4.17 | 0.76 | 398.47 | 405.38 |
| 30 | Other transport equipment | 1996 (T2, 124.6), 1997 (T1, 110.5), 1998 (T2, 114.9), 1999 (T1, 88.2), 2000 (T1, 143), 2002 (T2, 178.6), 2003 (T2, 117.4), 2004 (T1, 97.9), 2005 (T2, 208.2), 2006 (T2, 105.7), 2014 (T1, 339.9), 2021 (T1, 12.5), 2024 (T1, 54.9) | 0.13 | 2.62 | 169.23 | 119.09 |
| 31 | Furniture | 2002 (T1, 47.1), 2010 (T1, 24.1) | 0.87 | 0.87 | 543.08 | 60.11 |
| 33 | Repair and installation | 1996 (T1, 104.9) | 0.40 | 0.40 | 687.22 | 65.67 |
| 36 | Water supply and waste | 1996 (T1, 95), 1998 (T1, 89.5), 1999 (T1, 96.6) | 0.57 | 0.57 | 472.06 | 9.41 |

Products: anchored on the 2025 actual; 0 of 127 products change by more than 25% from 2025 to 2026 (Baseline). Regional share equations: 13 coefficients carry an `eb_shrinkage` restriction (`imposed: true`, `fixed: true`) recording the estimate, prior mean, shrinkage weight, κ and τ² behind the value used in the forecast.
<!-- /AUTO:v21 -->

*Xülasə (AZ):* v2.1 DSK həcm indekslərinin yoxlanmasını əlavə edir: bəzi kiçik sahələrdə (16, 21, 27, 29, 30 və s.)
indeks sahənin öz nominal buraxılışı ilə uyğun gəlmir, buna görə zəncirlənmiş real buraxılış qeyri-real səviyyələrə
çatırdı. Deflyatorun bir illik dəyişməsi ×1/3…×3 intervalından (T1) və ya emal sənayesi deflyatoruna nisbətən deflyator
1/6…6 intervalından (T2) çıxdıqda indeks nominal artımın emal sənayesi deflyatoru dəyişməsinə bölünməsi ilə əvəz olunur;
əvəz olunan dəyərlər doldurulmuş kimi işarələnir (F15). Proqnozda istifadə olunan tənliklərin əmsalları
dəyişmir. Məhsul proqnozları 2025 faktiki səviyyəsinə bağlanır; regional əmsalların empirik Bayes büzülməsi reyestrdə
məhdudiyyət kimi qeyd olunur; mühərrik FR4 yuxarı axın nəticəsini istifadə edir.

## Revision / status note (2026-10-01)

**Layer B runs on a replaceable firm-panel file.** The Ministry will not share enterprise data with the project; it
will load its own data into its own system. Layer B therefore reads `data/firm_panel/`: the delivered file
`FR10_firm_panel_SYNTHETIC.csv/.xlsx` is **synthetic** (every row marked "SYNTHETIC — not real enterprise data"), and
the Ministry replaces it with `FR10_firm_panel.csv/.xlsx` (or `FIRM_PANEL_PATH`) in the same schema. The data mode
below is generated by the run; in SYNTHETIC mode every Layer-B output is `output/FR10_SYNTHETIC_*.csv`, watermarked,
and used nowhere in the findings. Layer A (enterprise groups: branches, size classes, ownership, regions, products) is
operational on DSK and workbook data now.

Numbers in this document are **generated by the notebook's last code cell** from the CSV outputs of the run, between
`AUTO` markers, so the document cannot drift from the outputs.

<!-- AUTO:mode_header -->
**Layer-B data mode: SYNTHETIC** — input file `data/firm_panel/FR10_firm_panel_SYNTHETIC.csv`, 22,495 rows, 5,255 firms, 24 NACE divisions, 2019–2025. The firm panel is **SYNTHETIC — not real enterprise data**; Layer-B outputs are a pipeline demonstration, not findings.
<!-- /AUTO:mode_header -->

<!-- AUTO:rev -->
This run: 114 DSK tables, 15 integrity findings, 52 indicators in the source matrix (available now 40, requested 7, not available 5); branch model: Refined petroleum products by throughput capacity and the oil price, non-oil branches by the equal-weight combination of the pooled related-sector model (β = 0.219) and constant shares; regions MNL: oil-sector mix (FR1 mining/manufacturing VA) (κ = 0.5); baseline industry output +4.76% a year (nominal) 2026–2030; 88 FR10 CSV files, of which 24 SYNTHETIC.
<!-- /AUTO:rev -->

Standards applied (the lessons of the FR1–FR5 review): no lagged dependent variable and no own-history forecast;
level relations by DOLS with MacKinnon residual-based cointegration p-values; small-sample HAC and t(n−k) inference;
the coherence rule (a level slope outside its own difference-form 95% CI is not used); panels by two-way fixed effects
with Driscoll–Kraay errors on t(T−1) and wild cluster bootstrap by year; empirical-Bayes shrinkage of noisy
unit-specific slopes with the intensity chosen pre-cut; every choice on rolling origins scored ≤ 2019 with an
untouched 2020–2025 hold-out; Theil U against both a random walk and constant growth; DM/HLN tests on the loss
averaged by target year; softmax share systems anchored on 2025; constant add-factors; plausibility against each
unit's own history; arithmetic identity checks labelled as such.

---

## 1. The task

> *Müəssisələrin və istehsalatların maliyyə vəziyyəti, istehsal effektivliyi və bazar paylarının təhlili və
> proqnozlaşdırılması mümkün olmalıdır.*

Analytical assessment, comparative analysis and forecasting of enterprises' and productions' **financial condition,
production efficiency and market position**, linking enterprise, financial, production and market indicators from
several sources; goals: compare performance efficiency; identify growth or decline of production; compare by region,
activity, product; identify key factors; forecast production and market indicators; support decisions. The result
must state concretely **which data, from which source, are used for which indicator, in which form** — §5–§7.

Constraints (as FR1–FR5): no AR/ARIMA/ARCH/GARCH, no lagged dependent variable, no variable forecast from its own
history; structural models showing the effect of related sectors; missing data collected from DSK; forecast accuracy
tested against simple benchmarks on information available at the forecast time (NFR1).

## 2. Architecture

| Layer | Units | Status |
|---|---|---|
| **A — operational** | 30 industrial branches (NACE 06–09, 10–33, 35, 36), 4 sections, size classes, state/non-state, 14 economic regions, ~140 products | results (§8–§14) |
| **B — firm engine** | the enterprise (schema, validator, ratios, Altman Z''-EM, TFP index, market shares/HHI/CR4 by NACE × region, entry/exit/survival, peer benchmarking, firm forecasts) | pipeline tested on SYNTHETIC data only (§15) |

Links: FR1 supplies real value added and deflators of mining, manufacturing, electricity and water, the oil export
price, the average wage and total employment in three scenarios plus 500 baseline draws; FR4 supplies hired
employees by activity; FR3's branch wage table is read but not used for levels (finding F13).

## 3. Data collected

DSK tables were downloaded from `stat.gov.az/source/<section>/en/` into `data/dsk_enterprise/` (industry,
entrepreneurship, statistical register, national accounts) and are re-read from disk on later runs; a parse cache
(`_fr10_parse_cache.pkl`, keyed on file sizes and dates) skips re-parsing. Status by section:

<!-- AUTO:data -->
| section | NOT PUBLISHED (URL returns an HTML page, HTTP 200) | present |
|---|---|---|
| entrepreneurship | 0 | 29 |
| industry | 6 | 60 |
| st_units | 0 | 10 |
| system_nat_accounts | 0 | 15 |

Branch output adds up to the published mining, manufacturing and industry totals to 0.001% in 1996–2025; national-accounts branch VA to 0.018%; FR1 and DSK section value added coincide in 2025.
<!-- /AUTO:data -->

Workbook sheets used: `Emal Sənayesi`, `Mədənçıxarma`, `Elektrik enerjisi `, `Su təchizatı` (branches 2016–2025),
`DVX üzrə göstəricilər` (r43 arrears, r53–r57 turnover, r111–r129 taxpayer size classes, r215–r232 profit- and
income-tax declarations), `Real sektor` (r80, r114–r118 investment by source; r10 private share), `Regionlar*`
(enterprises, entry, exit, size, industrial output by region 2021–2025), `Park`, `KOBİA`, `İnvestisiya təşviqi sənədi `.

## 4. Data-integrity findings

<!-- AUTO:integrity -->
| id | finding | evidence | consequence |
|---|---|---|---|
| F1 | DSK no longer publishes the fixed-asset renewal, disposal and depreciation tables by branch, nor the capital-yield index | 6 URLs (017_2en.xls, 017_3en.xls, 017_4en.xls, 017_5en.xls, 017_6en.xls, 017_7en.xls) return an HTML page with HTTP 200; the section is commented out of the DSK industry index and file numbers 017_1/018_1/018_2 now hold regional product tables | Renewal and depreciation rates by branch are NOT AVAILABLE; FR10 uses the investment rate (I/GO, DSK 019) and the national-accounts consumption of fixed capital and fixed assets by section (DSK NA 013, 031) as alternatives (gaps table) |
| F2 | The workbook's 2025 branch columns are a different (preliminary) vintage from DSK | workbook industry total 63,123 vs DSK 63,011 mn AZN (+0.18%); largest branch gaps: Machinery and equipment +228%, Fabricated metal products -40%, Basic metals -20%, Other transport equipment -12%; 2016-2024 agree to 0.000% | FR10 takes 2025 branch data from DSK; the workbook branch rows are used only where they match DSK |
| F3 | Branch investment does not add up to the industry total before 2010 | unattributed investment -3.05% to -0.41% of the total in 2005-2009; exact (<0.01%) from 2010; mining-support investment printed as "-" until 2017 although its output was 1,342 mn AZN a year | Investment rates are used from 2010 in the determinants panel; mining-support investment before 2018 is treated as missing, not zero |
| F4 | Volume indices printed in thousands of per cent with a "t." suffix | DSK 009 prints e.g. "7.8 t." (= 7 800% of 2010) in 48 cells of sheet 9.2 and 4 of sheet 9.1; read naively these cells become missing | to_num reads the suffix (Part 2); real output is chained from 9.1 (previous year = 100) only |
| F5 | National-accounts income account does not close by section in 2016 | VA - compensation - other taxes - GOS = C -22.5, D +7.3, E +15.2 mn AZN in 2016 (sum -0.00); exact in every other year | An allocation error between sections C, D, E; GOS margins of those sections in 2016 are uncertain by these amounts |
| F6 | Water supply runs a negative gross operating surplus; the income-account total row carries the section code "C" | section E GOS -155.7 mn AZN in 2025 (compensation 454.3 > value added 301.7); negative in 5 of 21 years | Not an error but an economic fact (a subsidised utility); the total row is identified by its label, not its code |
| F7 | The DVX "rentabellik" (profitability) row is a tax ratio, not profitability | r223 equals payable profit tax / income after deductions to 0.05 pp in every year 2021-2025 (2.2-2.8%); the profitability the declarations imply, (income after deductions - deductible expenses) / deductible expenses, is 10.0-13.2%; taxable profit minus declared loss equals that net result to 7.60 mn AZN | FR10 reports the declaration margin computed from the components and labels r223 as an effective tax ratio |
| F8 | DVX budget-organisation rows duplicate the micro-taxpayer rows; micro-taxpayer count carries a money unit | rows 127-129 equal rows 123-125 in every year: True; row 123 (a count) is labelled "mln. manat" | Budget-organisation taxpayer counts are NOT AVAILABLE; the size-class table uses the micro rows only (as FR4 F4) |
| F14 | DVX taxpayer counts carry a population unit | rows 111, 115 and 119 (numbers of large, medium and small taxpayers, e.g. 846 large payers in 2022) are labelled "min nəfər" (thousand persons) | Read as counts of taxpayers; the unit should be corrected in the workbook |
| F9 | Regional industrial output does not add up to the national total before 2019, and includes household industry after | sum of 14 regions vs DSK 010: -13.9% to -1.7% in 2003-2018, exact from 2019; DSK 022 footnotes 2019+ as "considering industrial activities of households and informal individual owners" | Regional shares are modelled on the regional sum (shares add to one by construction); the 2018/2019 change of coverage is a level break, handled by a step dummy in the regional share equations |
| F10 | FR1's 2024 section value added is an earlier vintage than DSK's | FR1 manufacturing VA 2024 7,475.5 vs DSK NA 7,019.4 mn AZN (+6.5%); the two agree exactly in 2025 | FR10 anchors on 2025, where FR1 and DSK coincide, and uses FR1 only as growth indices from 2025 |
| F11 | SME indicators exist for two years only; the statistical register is a single snapshot | DSK entrepreneurship tables cover 2023 and 2024; st_units tables are as of 1 July 2026 (entry/exit January-June 2026) | SME shares and register-based entry/exit rates are presented, not modelled: no time series exists to identify a projection |
| F15 | DSK volume indices of small branches are inconsistent with their own nominal output | 64 branch-year volume indices (DSK 009, sheet 9.1) fail the validation in 15 branches: T1 (one-year implied deflator change outside x1/3-x3) 41, T2 (deflator relative to manufacturing, 2015 = 1, outside 1/6-6) 23. Replaced (year and published index, previous year = 100): 07: 2000 631.7, 2003 829.3, 2008 159.7; 14: 1998 82.6; 16: 1997 21.1, 1999 103.1, 2000 194.5, 2013 91.6, 2014 305.9, 2020 256, 2023 165.1, 2024 125.9; 17: 1999 171, 2002 61.3; 21: 2011 83.7, 2016 122.4, 2020 11200; 22: 1996 77.8, 1998 80.5, 1999 40.3, 2000 76.7, 2001 52.9, 2002 86.9, 2004 126.5; 25: 1996 85.7; 26: 2000 36.9, 2002 54.4, 2004 67.5, 2005 75.7, 2006 64.9, 2007 92.3; 27: 2011 72.9, 2016 333.8, 2020 8500; 28: 2025 84.1; 29: 1997 112.3, 2000 1156.4, 2003 119.5, 2006 2230.7, 2009 23, 2010 84400, 2012 27.8, 2014 158.2, 2017 1.2, 2018 31000; 30: 1996 124.6, 1997 110.5, 1998 114.9, 1999 88.2, 2000 143, 2002 178.6, 2003 117.4, 2004 97.9, 2005 208.2, 2006 105.7, 2014 339.9, 2021 12.5, 2024 54.9; 31: 2002 47.1, 2010 24.1; 33: 1996 104.9; 36: 1996 95, 1998 89.5, 1999 96.6. Chained on the published indices, real / nominal output in 2025 was 429 (27), 195 (21), 44.2 (16) | Each failing index is replaced by the branch's nominal growth deflated by the manufacturing deflator change of the same year (relative price held); the affected real output and labour productivity values are flagged imputed (FR10_volume_index_validation.csv); the indices should be queried with DSK |
| F12 | The published non-state share of industry is inconsistent with its own branch breakdown in some years | output-weighted branch non-state shares (DSK 010_2 x 010) differ from the published industry total by 2005 -0.8 pp, 2013 +6.3 pp, 2014 +7.6 pp, 2015 +7.9 pp, 2016 +6.7 pp; within 0.15 pp in every other year | The forecast of the non-state share is built from the branch composition (consistent by construction); the published total for those years should be queried with DSK |
| F13 | FR3's branch wage paths are not anchored on 2025 branch wages and share one growth rate | FR3 2026 branch wage / DSK 2025 branch wage - 1 ranges -21% to +20% across 29 branches; 2026-2030 growth is 7.18-7.18% a year for every branch | FR10 applies FR1's average-wage index to each branch's 2025 DSK wage; FR3 is not used for levels |
<!-- /AUTO:integrity -->

## 5. The indicator system: which data, from which source, for which indicator, in which form

One row per indicator, exported as `output/FR10_data_source_matrix.csv` with the full set of columns (formula, unit,
frequency, update frequency included). "Years available now" is computed from the files read, not typed. Status:
*available now* — in the workbook or downloadable from DSK today; *requested* — in the 24 Aug 2026 request, not yet
received; *not available* — no source publishes it, an alternative is named.

Count by pillar and status:

<!-- AUTO:matrix_summary -->
| pillar | available now | not available | requested |
|---|---|---|---|
| financial condition | 13 | 1 | 5 |
| market position | 18 | 1 | 1 |
| production efficiency | 9 | 3 | 1 |
<!-- /AUTO:matrix_summary -->

Integration routes: **file download** (scheduled retrieval of DSK `.xls` tables, parsed by label, never by offset,
with adding-up assertions); **workbook upload** (the Ministry's workbook, read by sheet and row label); **data-sharing
agreement + secure API** (DVX, DSMF, DGK, CBAR for firm and transaction data).

<!-- AUTO:matrix -->
| id | pillar | indicator_az | indicator_en | source_institution | dataset_table_row | granularity | years_available_now | status | integration_into_MIIS | analytical_use | presentation_form | alternative_if_unavailable |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I01 | market position | Sahənin sənaye məhsulunda payı | Branch share of industrial output | DSK | industry 010 | branch (30) | 1995-2025 | available now | file download (DSK xls, scheduled) | share system, HHI (Parts 7, 11) | ranking table; time series with fan | — |
| I02 | market position | Emal sənayesində sahənin payı | Branch share of manufacturing output | DSK | industry 010 | branch (24) | 1995-2025 | available now | file download (DSK xls, scheduled) | MNL share system (Part 11), forecast | stacked area; fan chart | — |
| I03 | market position | Konsentrasiya indeksi (HHİ, CR4) — sahələr | Concentration across branches (HHI, CR4) | DSK | industry 010 (derived) | industry / manufacturing | 1995-2025 | available now | file download (DSK xls, scheduled) | market-structure KPI, forecast | dashboard KPI card | — |
| I04 | market position | Müəssisə səviyyəsində HHİ | Firm-level HHI / CR4 by NACE x region | DVX / DSMF | enterprise panel (requested 24.08.2026) | firm | none | requested | data-sharing agreement + secure API | Layer B concentration | heat map NACE x region | lower bound from DSK register large-unit count and SME output share (Part 7.1) |
| I05 | market position | Qeyri-dövlət bölməsinin payı | Non-state share of output by branch | DSK | industry 010_2 | branch | 1997-2025 | available now | file download (DSK xls, scheduled) | ownership composition forecast (Part 14) | time series; KPI card | — |
| I06 | market position | Fəaliyyət göstərən müəssisələrin sayı | Active enterprises by branch and ownership | DSK | industry 004-007-008 sheet 4;7 | branch x ownership | 1995-2025 | available now | file download (DSK xls, scheduled) | entry/net-entry rates, determinants panel | ranking table | — |
| I07 | market position | Ölçü qrupları üzrə müəssisələr | Enterprises by size class | DSK | industry 004-007-008 sheet 8 | branch x size | 2009-2025 | available now | file download (DSK xls, scheduled) | size structure, concentration bound | stacked bar | — |
| I08 | market position | KOB-ların payı (buraxılış, məşğulluq, investisiya) | SME share of output, employment, investment | DSK | entrepreneurship 001_1, 012, 013, 015 | section x size | 2023-2024 | available now (2 years) | file download (DSK xls, scheduled) | held constant (not identifiable, F11) | KPI card | DVX taxpayer size classes r111-r126 (2022-2025) |
| I09 | market position | Vergi ödəyicilərinin ölçü qrupları | Taxpayer size classes: count, turnover, employees | DVX | workbook 'DVX üzrə göstəricilər' r111-r126 | size class | 2022-2025 | available now | workbook upload (Ministry of Economy) | size structure cross-check | table | — |
| I10 | market position | Regionun sənaye məhsulunda payı | Regional share of industrial output | DSK | industry 022 (and 023 volume index) | economic region (14) | 2003-2025 | available now | file download (DSK xls, scheduled) | regional share system (Part 12) | map; region x year heat map | — |
| I11 | market position | Regionlarda qeyri-dövlət payı | Non-state share of industrial output by region | DSK | industry 024 | region | 2005-2025 | available now | file download (DSK xls, scheduled) | regional ownership profile | map | — |
| I12 | market position | Regionlarda müəssisələrin sayı | Industrial enterprises by region | DSK | industry 021 | region | 2005-2025 | available now | file download (DSK xls, scheduled) | regional entry dynamics | map | — |
| I13 | market position | Yeni yaradılmış / ləğv edilmiş müəssisələr (regionlar) | New and liquidated enterprises by region (all sectors) | DSK via workbook | workbook 'Regionlar*' rows 'Müəssisə və təşkilatların sayı', 'Yeni yaradılmış', 'Ləğv edilmiş' | region | 2021-2025 | available now | workbook upload (Ministry of Economy) | entry/exit rates | map; table | — |
| I14 | market position | Yaradılmış və ləğv edilmiş vahidlər (fəaliyyət növləri) | Created and liquidated statistical units by activity | DSK | st_units 2_1-2_3 (snapshot 1 Jul 2026) | section, region, ownership | H1 2026 | available now (snapshot) | file download (DSK xls, scheduled) | entry/exit rates | table | DVX register flows (requested) |
| I15 | market position | Əsas məhsulların natura ilə istehsalı | Main products in physical units | DSK | industry 018; product lists in 014_x, 015_x, 016, 017 | product (~140) x branch | 1995-2025 | available now | file download (DSK xls, scheduled) | product view, growth ranking | product table with sparklines | — |
| I16 | market position | Regionlar üzrə məhsullar | Main products by place of production; product location shares | DSK | industry 018_1 (2011-2025), 018_2 (2019-2025); 017_1 (to 2022) | product x city/district | 2011-2025 | available now | file download (DSK xls, scheduled) | product market shares by place, HHI across places (Part 14.3) | map; product table | — |
| I17 | market position | Sahələr üzrə ixrac | Exports by branch (export orientation) | State Customs Committee (DGK) | HS-level exports (not in project) | branch / product | none | not available | data-sharing agreement + secure API with DGK; HS-NACE concordance | share-system driver, determinants panel | scatter; time series | industrial-park exports (workbook Park, 2019-2025); DSK shipped goods 011 is not exports |
| I18 | market position | Sənaye parkları: istehsal, ixrac, iş yerləri | Industrial parks and zones: output, exports, jobs, investment | Industrial-park operators (İZİA, Ministry of Economy) | workbook 'Park' | park | 2019-2025 | available now | workbook upload (Ministry of Economy) | park performance | table; KPI card | — |
| I19 | market position | İnvestisiya təşviqi sənədləri | Investment promotion certificates: projects, jobs, value | Ministry of Economy | workbook 'İnvestisiya təşviqi sənədi ' | national | 2016-2025 | available now | workbook upload (Ministry of Economy) | support-measure context | table | — |
| I20 | market position | KOBİA dəstək xidmətləri | SME agency (KOBİA) support services | KOBİA | workbook 'KOBİA' | national / SME house | 2021-2025 | available now | workbook upload (Ministry of Economy) | support-measure context | table | — |
| I21 | production efficiency | Əmək məhsuldarlığı (buraxılış/işçi) | Labour productivity, real output per employee | DSK; workbook | industry 010, 009, 006; industry sheets (headcount) | branch | 2016-2025 | available now | file download (DSK xls, scheduled); workbook upload (Ministry of Economy) | efficiency ranking, quadrant, forecast path | ranking table; quadrant; fan | — |
| I22 | production efficiency | Əmək məhsuldarlığı (ƏD/işçi) | Labour productivity, real value added per employee | DSK | national accounts 015_2; 006 | branch | 2016-2025 | available now | file download (DSK xls, scheduled) | efficiency ranking | ranking table | — |
| I23 | production efficiency | Əmək məhsuldarlığı (rəsmi) | Labour productivity by section (official) | DSK | national accounts 030_2 | section | 2017-2025 | available now | file download (DSK xls, scheduled) | cross-check | KPI card | — |
| I24 | production efficiency | Aralıq istehlakın payı | Intermediate-consumption share of output | DSK | national accounts 015, 015_1 | branch | 2005-2025 | available now | file download (DSK xls, scheduled) | TFP materials share; cost structure | time series | — |
| I25 | production efficiency | Kapital məhsuldarlığı | Capital productivity | DSK | industry 019; national accounts 031 | branch / section | 2010-2025 | available now (derived) | file download (DSK xls, scheduled) | efficiency, TFP capital input | time series | — |
| I26 | production efficiency | Ümumi amil məhsuldarlığı (TFP) | TFP growth, gross output (branches) and value added (sections) | DSK; FR1; FR4 | NA 013, 015, 015_1, 031; industry 019; FR4 hired | branch, section | 2017-2025 | available now (derived) | file download (DSK xls, scheduled) | efficiency decomposition (Part 7.2) | waterfall / decomposition chart | — |
| I27 | production efficiency | Əmək haqqı - məhsuldarlıq fərqi | Wage-productivity gap | DSK; workbook | industry 006_2; industry sheets | branch | 2016-2025 | available now | file download (DSK xls, scheduled) | unit-labour-cost pressure | bar chart | — |
| I28 | production efficiency | İnnovasiya intensivliyi | Innovation intensity | DSK | industry 020_3 (also 020_1, 020_2, 020_4, 020_5) | branch | 2005-2025 | available now | file download (DSK xls, scheduled) | efficiency profile | ranking table | — |
| I29 | production efficiency | İnvestisiya norması | Investment rate (renewal proxy) | DSK | industry 019, 010 | branch | 2005-2025 | available now | file download (DSK xls, scheduled) | determinants panel; early-warning flag | heat map | — |
| I30 | production efficiency | Əsas fondların yenilənmə, çıxma, köhnəlmə dərəcəsi | Fixed-asset renewal, disposal and depreciation rates | DSK | industry 017_2-017_7 (no longer published, F1) | branch | none | not available | request to DSK to resume publication | renewal flag | heat map | investment rate (DSK 019/010); consumption of fixed capital / VA by section (NA 013, 025) |
| I31 | production efficiency | Kapital qoyuluşlarının səmərəlilik indeksi | Capital-yield index | DSK | industry 018_1 (old numbering, discontinued) | branch | none | not available | request to DSK | efficiency | time series | capital productivity from perpetual inventory |
| I32 | production efficiency | Enerji intensivliyi | Energy intensity of production | DSK; Azerenerji | not published by branch (SME electricity costs only, entrepreneurship 037, 2023-2024) | branch | none | not available | data-sharing agreement + secure API | cost structure, determinants | ranking table | SME electricity and fuel costs (entrepreneurship 035, 037) |
| I33 | financial condition | Ümumi əməliyyat mənfəəti (bölmələr) | Gross operating surplus margin by section | DSK | national accounts 013 | section (B, C, D, E) | 2005-2025 | available now | file download (DSK xls, scheduled) | financial-condition forecast (Part 14) | time series with fan | — |
| I34 | financial condition | Əmək haqqının ƏD-də payı | Labour share of value added | DSK | national accounts 013, 023 | section | 2005-2025 | available now | file download (DSK xls, scheduled) | margin decomposition | time series | — |
| I35 | financial condition | Əsas kapitalın istehlakı | Consumption of fixed capital / VA | DSK | national accounts 013, 025 | section | 2005-2025 | available now | file download (DSK xls, scheduled) | renewal proxy, net margin | time series | — |
| I36 | financial condition | Sahə üzrə mənfəət proksisi | GOS-proxy margin by manufacturing branch | DSK; workbook | NA 015, 015_2; industry 006, 006_2; industry sheets | branch | 2016-2025 | available now (derived) | file download (DSK xls, scheduled); workbook upload (Ministry of Economy) | quadrant, early warning, forecast | quadrant; ranking; fan | — |
| I37 | financial condition | Mənfəət vergisi bəyannamələri: xalis marja | Profit-tax declarations: net margin | DVX | workbook 'DVX üzrə göstəricilər' r215-r222 | all payers | 2021-2025 | available now | workbook upload (Ministry of Economy) | economy-wide profitability KPI | KPI card | branch breakdown requested from DVX |
| I38 | financial condition | Bəyan edilmiş zərər | Declared losses | DVX | DVX r221 | all payers | 2021-2025 | available now | workbook upload (Ministry of Economy) | distress KPI | KPI card | — |
| I39 | financial condition | Effektiv mənfəət vergisi nisbəti | Effective profit-tax ratio (DVX "rentabellik", F7) | DVX | DVX r223 | all payers | 2021-2025 | available now | workbook upload (Ministry of Economy) | tax burden | KPI card | — |
| I40 | financial condition | Gəlir vergisi bəyannamələri (fərdi sahibkarlar) | Income-tax declarations of individual entrepreneurs | DVX | DVX r224-r232 | all payers | 2021-2025 | available now | workbook upload (Ministry of Economy) | small-business profitability | KPI card | — |
| I41 | financial condition | Vergi borcları | Tax arrears | DVX | DVX r43 | national | 2021-2025 | available now | workbook upload (Ministry of Economy) | early-warning context | KPI card | — |
| I42 | financial condition | Sənaye dövriyyəsi (vergi bazası) | Industry turnover on the tax basis | DVX | DVX r53-r57 | industry / non-oil industry | 2021-2025 | available now | workbook upload (Ministry of Economy) | cross-check of output | time series | — |
| I43 | financial condition | İnvestisiyanın öz vəsaitləri hesabına maliyyələşməsi | Investment self-financing share | DSK via workbook | workbook 'Real sektor' r114 / r80 | national | 2023-2025 | available now (3 years annual) | workbook upload (Ministry of Economy) | financial capacity KPI | KPI card | — |
| I44 | financial condition | Hazır məhsul ehtiyatları | Finished-goods stocks to output | DSK | industry 013 | branch | 1999-2025 | available now | file download (DSK xls, scheduled) | early-warning flag (rising stocks) | heat map | — |
| I45 | financial condition | KOB-ların aktivləri, ehtiyatları, vergiləri | SME assets, stocks and taxes paid | DSK | entrepreneurship 039, 040, 041 | section x size | 2023-2024 | available now (2 years) | file download (DSK xls, scheduled) | SME balance-sheet profile | table | — |
| I46 | financial condition | Likvidlik əmsalları | Liquidity: current, quick, cash ratios | DVX | enterprise balance sheet and P&L panel (requested 24.08.2026) | firm | none | requested | data-sharing agreement + secure API | Layer B engine (Part 17) | firm scorecard; peer percentile; early-warning list | none for firms; aggregate proxies above |
| I47 | financial condition | Borc yükü, faiz örtüyü | Leverage and interest cover | DVX | enterprise balance sheet and P&L panel (requested 24.08.2026) | firm | none | requested | data-sharing agreement + secure API | Layer B engine (Part 17) | firm scorecard; peer percentile; early-warning list | none for firms; aggregate proxies above |
| I48 | financial condition | Rentabellik (DuPont) | Profitability: ROE (DuPont), ROA, EBIT margin | DVX | enterprise balance sheet and P&L panel (requested 24.08.2026) | firm | none | requested | data-sharing agreement + secure API | Layer B engine (Part 17) | firm scorecard; peer percentile; early-warning list | none for firms; aggregate proxies above |
| I49 | financial condition | Dövriyyə göstəriciləri | Turnover: assets, inventories, receivable days | DVX | enterprise balance sheet and P&L panel (requested 24.08.2026) | firm | none | requested | data-sharing agreement + secure API | Layer B engine (Part 17) | firm scorecard; peer percentile; early-warning list | none for firms; aggregate proxies above |
| I50 | financial condition | Altman Z''-EM | Distress score (Altman Z''-EM, literature coefficients) | DVX | enterprise balance sheet and P&L panel (requested 24.08.2026) | firm | none | requested | data-sharing agreement + secure API | Layer B engine (Part 17) | firm scorecard; peer percentile; early-warning list | none for firms; aggregate proxies above |
| I51 | production efficiency | Müəssisə məşğulluğu və əmək haqqı fondu | Firm employment and wage bill | DSMF | contributor records (requested) | firm | none | requested | data-sharing agreement + secure API | Layer B productivity, TFP | firm scorecard | branch headcount (DSK 006, workbook) |
| I52 | financial condition | Sahələr üzrə kredit, problemli kreditlər | Credit and NPLs by branch | CBAR | not in project (FR1 holds total industry credit) | branch | none | not available | data-sharing agreement + secure API with CBAR | financial-condition driver | time series | FR1 industry credit (cred_ind_n) at section level |
<!-- /AUTO:matrix -->

## 6. Gaps, alternatives and actions to agree with the Customer

<!-- AUTO:gaps -->
| id | gap | impact | alternative_proxy | bias_of_proxy | action_to_agree_with_Customer |
|---|---|---|---|---|---|
| G01 | Enterprise balance sheet and P&L panel (Tax Service, >= 5 years) | No firm ratios, distress scores, firm-level HHI, entry/exit by firm; Layer B runs on synthetic data only | Section GOS margins (NA 013), branch GOS proxy, DVX declaration aggregates, concentration bound from the register | Aggregates hide dispersion; the GOS proxy omits other taxes and non-employee compensation (overstates margins) | Sign the data-sharing agreement on the Part 17.1 schema; pseudonymised VÖEN; annual delivery after the declaration deadline |
| G02 | Firm employment and wage bill (DSMF) | No firm productivity or TFP | DSK branch headcount and wages (006, 006_2), workbook industry sheets | Branch averages only | DSMF agreement keyed on the same pseudonymised VÖEN |
| G03 | Fixed-asset renewal, disposal, depreciation rates by branch (F1) | No direct renewal indicator | Investment rate I/GO (DSK 019/010); CFC/VA by section (NA 013, 025) | Investment rate ignores stock age and is lumpy; section CFC hides branches | Ask DSK to restore tables 017_2-017_7 or deliver them to MIIS |
| G04 | Capital-yield index (old DSK 018_1) | No published capital efficiency | Capital productivity from perpetual inventory | Depends on depreciation rate (0.07) and the 2010 starting stock | As above |
| G05 | Exports by branch / product (State Customs Committee) | Export orientation cannot enter the share system or the determinants panel | Industrial-park exports (workbook Park) | Covers parks and zones only, with no branch structure | Monthly HS-level exports from DGK with an HS-NACE concordance |
| G06 | Producer prices by NACE 2-digit branch | Real branch output relies on implicit deflators | Implicit output deflator = nominal output / chained volume (DSK 010, 009) | Composition effects inside a branch enter the deflator | DSK PPI by branch |
| G07 | Energy costs by branch | No energy-intensity indicator | SME electricity and fuel costs (entrepreneurship 035, 037; 2023-2024) | SMEs only, two years | DSK / Azerenerji branch energy use |
| G08 | Credit and NPLs by branch (CBAR) | No financing-condition driver by branch | FR1 industry credit at section level | Section level | CBAR loan register aggregates by NACE |
| G09 | SME indicators as a time series (F11) | SME share cannot be projected | Held at 2024 | Ignores any trend | DSK back-series of entrepreneurship tables from 2019 |
| G10 | Industrial output by region x branch | Regional forecasts cannot use branch composition | Regional totals (022) and products by place of production (018_1 2011-2025, 018_2 2019-2025) | Products cover physical units only, main products only | DSK region x NACE output table |
| G11 | Profit-tax declarations by branch and size class (DVX) | Financial condition only economy-wide from declarations | Economy-wide DVX aggregates | Dominated by oil and large payers | DVX breakdown of r215-r232 by NACE and size |
| G12 | Budget-organisation taxpayer rows (F8) | Budget organisations cannot be separated | — | - | DVX to correct rows 127-129 of the workbook |
| G13 | Workbook 2025 branch vintage (F2) | Workbook 2025 branch data unusable | DSK final 2025 | None once DSK final is used | Refresh procedure: workbook rows overwritten from DSK when the final release appears |
| G14 | Regional coverage break 2019 (F9) | Level break in regional shares | Step dummy; shares on the regional sum | Pre-2019 shares exclude household industry | DSK back-cast of regional output on the 2019+ coverage |
| G15 | Published non-state share 2013-2016 inconsistent (F12) | Ownership history uncertain in 4 years | Composition identity | None in the forecast | Query DSK |
| G16 | FR3 branch wage levels not anchored on 2025 (F13) | FR3 branch wage levels unusable for margins | FR1 average-wage index on DSK 2025 branch wages | Common wage growth across branches | FR3 maintainers to anchor branch levels on 2025 actuals |
<!-- /AUTO:gaps -->

## 7. Presentation specification — the MIIS user views

<!-- AUTO:pres -->
| view | content | form | feeding_files |
|---|---|---|---|
| V1 Branch scorecard | One card per branch: share of industry and manufacturing, real growth, labour productivity, GOS-proxy margin, investment rate, flags | KPI cards + sparkline | FR10_branch_scorecard.csv |
| V2 Efficiency vs financial health | Labour-productivity growth against GOS-proxy margin, bubble = market share; quadrant labels | scatter / quadrant | FR10_quadrant.csv |
| V3 Market-share dynamics | Branch shares 2005-2025 and 2026-2030 with 50/80/90% bands; HHI, CR4 | stacked area; fan chart; KPI | FR10_branch_shares_history.csv, FR10_forecast_branches.csv, FR10_fan_charts.csv, FR10_concentration.csv |
| V4 Region x activity | Regional shares of industrial output by year; non-state share; enterprises; entry/exit; forecast shares | map + heat map | FR10_regional_history.csv, FR10_forecast_regions.csv, FR10_regional_entry_exit.csv |
| V5 Product view | Main products in physical units, 2020-2025 growth, branch link | table with sparklines | FR10_products.csv |
| V6 Forecast with bands | Section and branch output (nominal, real), margins, non-state share under three scenarios with 5-95% bands | time series with fan | FR10_forecast_branches.csv, FR10_forecast_sections.csv, FR10_fan_charts.csv, FR10_scenario_summary.csv |
| V7 Early-warning flags | Margin, market-share, renewal, stocks and productivity flags; watch list | flag table (traffic lights) | FR10_early_warning.csv |
| V8 Financial condition | Section GOS margins, labour share, CFC; DVX declaration margins, losses, arrears; self-financing | time series; KPI cards | FR10_financial_sections.csv, FR10_dvx_declarations.csv |
| V9 Key factors | Growth contributions by branch; determinants panel with honest inference | waterfall; coefficient table | FR10_growth_contributions.csv, FR10_determinants_panel.csv |
| V10 Efficiency | TFP decomposition, capital productivity, wage-productivity gap, innovation intensity | decomposition bars | FR10_efficiency_branches.csv, FR10_tfp_sections.csv |
| V11 Data catalogue | Indicator, source, table/row, years, status, integration route, alternative | searchable table | FR10_data_source_matrix.csv, FR10_data_gaps_and_alternatives.csv, FR10_data_integrity_findings.csv |
| V12 Firm view (Layer B) | Firm scorecard, peer percentiles, distress zone, firm HHI by NACE x region, firm forecast — ACTIVE ONLY when the DVX/DSMF panel arrives | firm card; heat map | FR10_SYNTHETIC_*.csv now (pipeline test only, watermarked) |
<!-- /AUTO:pres -->

## 8. Layer A analytics, 2005–2025

### 8.1 Market position

Shares are of **nominal** output (nominal values add up exactly; chain-linked volumes do not). Concentration across
branches and regions is measured by HHI (×10 000) and CR4. Firm-level concentration needs firm data; the data allow
a bound: if N large units produce a share s of output, the firm HHI is at least s²/N.

<!-- AUTO:market -->
Manufacturing HHI across branches 2188 (2005) → 1400 (2025); CR4 62.4%; HHI across 14 regions 6460. 2025 leaders: Refined petroleum products 25.3%, Food products 23.0%, Chemicals 7.3%, Non-metallic minerals 6.8%, Basic metals 5.2%. Non-state share of industry 78.1% (manufacturing 64.9%, mining 94.1%). Active industrial enterprises 4,831 (2025) vs 2,583 (2015). Firm-concentration bound: large (non-SME) enterprises produce 89.2% of industrial output (2024) and the register counts 237 large industrial units (1 July 2026); an equal split among them gives HHI = 33.6, and any unequal split raises it, so this is a lower bound (the two sources refer to different dates). The output-weighted branch non-state shares reproduce the published industry figure to 0.15 pp except in 2005 (-0.8 pp), 2013 (+6.3 pp), 2014 (+7.6 pp), 2015 (+7.9 pp), 2016 (+6.7 pp) (F12).
<!-- /AUTO:market -->

The forecast of the non-state share is built from branch composition (finding F12).

### 8.2 Production efficiency

Labour productivity (real output and real value added per employee), intermediate-consumption share, capital
productivity (perpetual inventory from branch investment, δ = 0.07 as FR1, 2010 stock = the section's observed fixed
assets allocated by 2005–2010 investment shares), and TFP by growth accounting with **observed** cost shares — gross
output Törnqvist for branches (s_M = IC/GO, s_L = wage bill × 1.22 / GO, s_K residual), value-added form for sections
(s_L = compensation/VA, K = national-accounts fixed assets at constant prices). No production-function parameter is
estimated; branch-years whose labour + materials shares exceed one are flagged. Section TFP:

<!-- AUTO:eff -->
| section (mean % a year, 2007–2025) | dlnVA | labour | capital | TFP |
|---|---|---|---|---|
| Electricity | 2.21 | 0.11 | 7.00 | -4.90 |
| Manufacturing | 5.04 | 0.46 | 4.36 | 0.23 |
| Mining | 1.08 | -0.08 | 8.02 | -6.87 |
| Water | 4.73 | 2.93 | 2.35 | -0.56 |

Branch TFP (gross output, 2017–2025 cumulative, log points × 100), highest and lowest:

| branch | output growth 2016-25, log pts x100 | materials | labour | capital | TFP | mean capital share |
|---|---|---|---|---|---|---|
| Other transport equipment | 224.49 | 115.45 | -78.31 | 44.64 | 142.71 | -0.69 |
| Tobacco products | 217.68 | 130.10 | 12.56 | 0.09 | 74.92 | 0.33 |
| Non-metallic minerals | 185.06 | 112.37 | 0.44 | 0.40 | 71.86 | 0.25 |
| Fabricated metal products | 103.16 | 37.18 | 8.04 | -10.44 | 68.37 | 0.23 |
| Motor vehicles | 73.20 | 213.97 | 1.96 | 22.04 | -164.77 | 0.23 |
| Refined petroleum products | 7.19 | 5.77 | -0.15 | 73.42 | -71.85 | 0.44 |
| Machinery and equipment | -115.06 | -49.97 | -13.29 | -5.26 | -46.56 | 0.15 |
| Repair and installation | -51.15 | -33.64 | 10.59 | 5.57 | -33.66 | 0.15 |
<!-- /AUTO:eff -->

Reading: TFP here is the residual after observed inputs; in mining it captures field depletion as much as
technology, and small-branch TFP is noisy (implicit deflators, perpetual-inventory capital).

### 8.3 Financial condition

Three windows, each with its limit: national-accounts GOS by section; a GOS proxy by manufacturing branch (value
added − gross wage bill, an upper bound because other taxes and non-employee compensation are omitted);
economy-wide profit-tax declarations (DVX). GOS as % of value added by section:

<!-- AUTO:fin -->
| year | Mining | Manufacturing | Electricity | Water |
|---|---|---|---|---|
| 2005.00 | 89.35 | 73.95 | 29.25 | 16.41 |
| 2010.00 | 96.40 | 83.45 | 68.18 | 18.00 |
| 2015.00 | 91.88 | 76.68 | 70.42 | 2.25 |
| 2019.00 | 93.40 | 62.68 | 62.46 | 9.17 |
| 2022.00 | 96.85 | 72.42 | 70.10 | -33.24 |
| 2025.00 | 93.56 | 65.82 | 65.44 | -51.61 |

DVX profit-tax declarations: net margin 10.0–13.2% (2021–2025); declared losses 14–27% of taxable profit; tax arrears 1,897 → 3,253 mn AZN; investment self-financing 2023 50.1%, 2024 49.1%, 2025 51.4%. Branch GOS-proxy margin 2025: median 20.4% of output, negative in Pharmaceuticals, Other transport equipment.
<!-- /AUTO:fin -->

Liquidity, leverage, interest cover, DuPont ROE and the distress score require balance sheets and are defined in
Layer B.

## 9. The no-autoregression constraint

| Construct | Where | Why it is not an autoregression |
|---|---|---|
| HAC / Driscoll–Kraay covariance | all equations | standard errors only |
| DOLS leads/lags of regressor differences | share equations | endogeneity correction; no own lag |
| Residual ADF, one fixed lag | `eg_coint_p` | a test statistic |
| Chained volume levels; perpetual inventory | data construction | accounting identities |
| One-year lags of other regressors | determinants panel | predetermined regressors; branch growth never on the right |
| Constant add-factor (2025 anchor) | share systems | level anchor held constant over the horizon; FR10 applies no decay (there is no decay-at-ρ̂ sensitivity) |
| Historical residual paths | fan charts | replay of observed error paths |
| Held-at-2025 forecast rules | forecast | stated assumptions (`FR10_forecast_assumptions.csv`) |

## 10. Key factors behind growth and decline

The robust answer is the exact Törnqvist decomposition of real manufacturing growth into branch contributions; the
econometric answer is a two-way fixed-effects panel of branch real growth on lagged investment rate, relative-price
change, non-state share, stocks-to-output and enterprise growth (specification A, 2011–2025), plus real wage and labour
share (B, 2018–2025). 21 of the 24 manufacturing branches have complete data and enter. The panel is unbalanced, so the
two-way within transformation is computed by alternating projections (identical to dummy-variable OLS, checked in
Part 3), including inside the wild bootstrap. Driscoll–Kraay errors with ⌊T^¼⌋ lags on t(T−1), wild cluster bootstrap
(Webb) by year; the between estimator is reported and not read as an effect. To limit division bias, ratios with
output in the denominator use output at t−2. Export orientation, credit and energy costs are not available by branch.

<!-- AUTO:det -->
| spec | regressor | coef | se_DK | p_DK_t | p_wild | between_coef | n | years |
|---|---|---|---|---|---|---|---|---|
| A: 2011-2025, core | inv_rate_l1 | -0.062 | 0.027 | 0.036 | 0.120 | 0.049 | 265 | 15 |
| A: 2011-2025, core | drelp_l1 | 0.079 | 0.066 | 0.253 | 0.300 | -0.478 | 265 | 15 |
| A: 2011-2025, core | nonstate_l1 | 0.009 | 0.202 | 0.965 | 0.950 | 0.060 | 265 | 15 |
| A: 2011-2025, core | stocks_go_l1 | -0.002 | 0.017 | 0.899 | 0.903 | -0.011 | 265 | 15 |
| A: 2011-2025, core | dln_ent_l1 | -0.250 | 0.175 | 0.175 | 0.154 | 0.038 | 265 | 15 |
| B: 2018-2025, + wage and labour share | inv_rate_l1 | 0.017 | 0.016 | 0.333 | 0.338 | 0.092 | 151 | 8 |
| B: 2018-2025, + wage and labour share | drelp_l1 | -0.243 | 0.376 | 0.538 | 0.556 | 0.043 | 151 | 8 |
| B: 2018-2025, + wage and labour share | nonstate_l1 | 0.265 | 0.335 | 0.455 | 0.460 | 0.086 | 151 | 8 |
| B: 2018-2025, + wage and labour share | stocks_go_l1 | 0.348 | 0.412 | 0.426 | 0.465 | -0.138 | 151 | 8 |
| B: 2018-2025, + wage and labour share | dln_ent_l1 | -0.174 | 0.346 | 0.631 | 0.772 | -0.064 | 151 | 8 |
| B: 2018-2025, + wage and labour share | dln_rwage_l1 | -0.258 | 0.320 | 0.447 | 0.458 | 0.320 | 151 | 8 |
| B: 2018-2025, + wage and labour share | labour_share_l1 | -0.026 | 0.676 | 0.970 | 0.944 | -0.003 | 151 | 8 |

Contributions to real manufacturing growth 2016–2025 (log points × 100): top Food products +17.3, Non-metallic minerals +10.9, Chemicals +6.4, Rubber and plastics +5.9, Tobacco products +3.6; bottom Machinery and equipment -2.5, Repair and installation -2.3, Refined petroleum products -1.3.
<!-- /AUTO:det -->

How much the division-bias correction moves the coefficients (t−2 denominators used vs same-year denominators):

<!-- AUTO:divb -->
| spec | regressor | coef_t2_denominator | coef_same_year_denominator | change | p_t2 | p_same |
|---|---|---|---|---|---|---|
| A | inv_rate_l1 | -0.062 | -0.049 | -0.013 | 0.036 | 0.078 |
| A | stocks_go_l1 | -0.002 | 0.002 | -0.004 | 0.899 | 0.987 |
| B | inv_rate_l1 | 0.017 | 0.040 | -0.023 | 0.333 | 0.211 |
| B | stocks_go_l1 | 0.348 | 0.540 | -0.192 | 0.426 | 0.212 |
| B | labour_share_l1 | -0.026 | 0.211 | -0.237 | 0.970 | 0.475 |
<!-- /AUTO:divb -->

Coefficients that are not significant on both tests are "not established (low power)", not "no effect".

## 11. Branch and regional allocation

### 11.1 Share systems with sector-wide drivers (benchmark)

Branch nominal shares of manufacturing and mining and regional shares of industrial output as multinomial-logit
systems driven by the scale of the sector and an oil channel (FR1), with DOLS slopes, the coherence rule and
empirical-Bayes shrinkage; candidates scored on origins 2011–2017 (scores ≤ 2019, DM/HLN by target year). For branches
constant shares were selected; this system is kept as the benchmark against which the structural model is judged.

<!-- AUTO:select -->
**manufacturing**

| candidate | RMSE_pp | DM_HLN_vs_best | DM_p_vs_best | target_years | slopes | non_inferior | decision | stage | DM_p_vs_const |
|---|---|---|---|---|---|---|---|---|---|
| constant shares | 1.869 | — | — | — | 0.000 | yes | CHOSEN | specification | — |
| MNL: scale (FR1 real sector VA) | 2.493 | -2.258 | 0.058 | 8.000 | 1.000 | no | — | specification | — |
| MNL: oil export price | 1.950 | -1.166 | 0.282 | 8.000 | 1.000 | yes | — | specification | — |
| MNL: scale + oil price | 4.737 | -2.387 | 0.048 | 8.000 | 2.000 | no | — | specification | — |
| combination: 1/2 constant + 1/2 MNL scale | 2.037 | -2.544 | 0.038 | 8.000 | 1.000 | no | — | specification | — |

**mining**

| candidate | RMSE_pp | DM_HLN_vs_best | DM_p_vs_best | target_years | slopes | non_inferior | decision | stage | DM_p_vs_const |
|---|---|---|---|---|---|---|---|---|---|
| constant shares | 3.754 | -1.611 | 0.151 | 8.000 | 0.000 | yes | CHOSEN | specification | — |
| MNL: scale (FR1 real sector VA) | 3.712 | -1.531 | 0.170 | 8.000 | 1.000 | yes | — | specification | — |
| MNL: oil export price | 3.760 | -1.660 | 0.141 | 8.000 | 1.000 | yes | — | specification | — |
| MNL: scale + oil price | 3.306 | — | — | — | 2.000 | yes | — | specification | — |
| combination: 1/2 constant + 1/2 MNL scale | 3.733 | -1.572 | 0.160 | 8.000 | 1.000 | yes | — | specification | — |

**regions**

| candidate | RMSE_pp | DM_HLN_vs_best | DM_p_vs_best | target_years | slopes | non_inferior | decision | stage | DM_p_vs_const |
|---|---|---|---|---|---|---|---|---|---|
| constant shares | 1.215 | -2.360 | 0.050 | 8.000 | 0.000 | no | — | specification | — |
| MNL: scale (FR1 real sector VA) | 1.377 | -2.862 | 0.024 | 8.000 | 1.000 | no | — | specification | — |
| MNL: oil-sector mix (FR1 mining/manufacturing VA) | 1.131 | — | — | — | 1.000 | yes | CHOSEN | specification | — |
| MNL: scale + oil-sector mix | 1.341 | -4.354 | 0.003 | 8.000 | 2.000 | no | — | specification | — |
| combination: 1/2 constant + 1/2 MNL scale | 1.294 | -2.791 | 0.027 | 8.000 | 1.000 | no | — | specification | — |
| kappa = 0 (no shrinkage) | 1.091 | — | — | — | — | yes | — | shrinkage | 0.151 |
| kappa = 0.5 | 1.110 | -0.697 | 0.508 | — | — | yes | CHOSEN | shrinkage | 0.054 |
| kappa = 1 | 1.131 | -0.995 | 0.353 | — | — | yes | — | shrinkage | 0.050 |
| kappa = 2 | 1.152 | -1.203 | 0.268 | — | — | yes | — | shrinkage | 0.047 |
| kappa = 4 | 1.170 | -1.347 | 0.220 | — | — | yes | — | shrinkage | 0.043 |
| kappa = 8 | 1.185 | -1.446 | 0.191 | — | — | yes | — | shrinkage | 0.041 |
| kappa = 16 | 1.196 | -1.512 | 0.174 | — | — | yes | — | shrinkage | 0.038 |
| kappa = 64 | 1.209 | -1.580 | 0.158 | — | — | yes | — | shrinkage | 0.036 |
| kappa = 256 | 1.213 | -1.602 | 0.153 | — | — | yes | — | shrinkage | 0.035 |
<!-- /AUTO:select -->

### 11.2 Refining as a capacity-constrained, oil-priced processor

Real output = throughput (DSK 018 tonnage of the branch's top-level products), baseline at the 2023–25 average,
lever at the 2015–25 maximum; price = FR1 oil export price in manat with an estimated elasticity (first differences,
no constant carried forward; the exchange rate is held because FR1's forecast has none). The capacity rule is adopted
for a branch only if it beats growing with the sector on the pre-cut windows.

<!-- AUTO:oil -->
| branch | name | n_products | corr_dlnQ_dlnThroughput | real_growth_2015_25 | price_elasticity_oil | price_el_p | cap_factor_baseline | cap_factor_max | precut_RMSE_capacity | precut_RMSE_sector_rate | precut_DM_p | capacity_rule_adopted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 19 | Refined petroleum products | 7 | 0.622 | -0.235 | 0.330 | 0.000 | 0.982 | 1.033 | 20.218 | 32.591 | 0.030 | yes |
| 20 | Chemicals | 8 | 0.855 | 9.640 | 0.417 | 0.067 | 1.005 | 1.034 | 61.077 | 35.440 | 0.009 | no |

Capacity rule adopted for: Refined petroleum products; Chemicals joins the non-oil allocation (the capacity rule is significantly less accurate pre-cut, p 0.009).
<!-- /AUTO:oil -->

### 11.3 Non-oil branches: pooled related-sector demand model

Building materials, fabricated metals and quarrying ← construction; food and beverages ← household consumption;
machinery, electrical and transport equipment and repair ← non-oil investment; other branches ← their sector total.
One common elasticity of the branch share on the related-sector index relative to the sector total, branch fixed
effects in first differences (drifts not extrapolated), softmax renormalisation. Rule fixed in advance (as FR4): the
pooled model is the baseline if it beats constant shares at p < 0.10, otherwise the equal-weight combination of the
two, so that FR1's sector scenarios reach the branches.

<!-- AUTO:pooled -->
β = 0.219 (Driscoll–Kraay s.e. 0.090, p 0.025 on t(19); wild-bootstrap p 0.089); 10 linked branches × 20 years; levels-with-FE estimate 0.082, inside the first-difference 95% CI [0.03, 0.41].

| candidate | RMSE_pp | DM_HLN_vs_const | DM_p_vs_const | target_years | decision |
|---|---|---|---|---|---|
| const | 2.048 | — | — | — | — |
| pooled | 2.359 | 1.996 | 0.086 | 8.000 | — |
| combo | 2.195 | 2.010 | 0.084 | 8.000 | BASELINE |

Baseline allocation: **equal-weight combination of the pooled model and constant shares** (decision rule fixed in advance). On the pre-cut windows the pooled model is less accurate than constant shares (2.359 vs 2.048 pp, DM p 0.086) and the combination 2.195 pp (p 0.084): the related-sector channel is an economically motivated, statistically significant in-sample elasticity whose out-of-sample allocation gain is not established.
<!-- /AUTO:pooled -->

### 11.4 Mining: non-oil branches modelled directly

Quarrying (v2): the unit-elasticity link to FR1's construction value added is adopted only if it is significantly more
accurate than the anchored null — real output constant at its last actual level, priced at FR1's construction deflator —
on the pre-cut design, both rules anchored on the origin's last actual (DM/HLN by target year, p < 0.10). It is not (the
null is significantly more accurate, and the free elasticity rejects the unit restriction), so the baseline holds real
quarrying output at its 2025 level, with no step in 2026, and the construction link is kept as the engine lever
`quarrying_rule`; metal ores are held at their 2023–25 average unless an FR1 driver wins pre-cut, at FR1's GDP deflator; crude
oil and gas and mining support services follow FR1's oil-and-gas real GDP, and their nominal output is the residual of
FR1's mining output, so the section reconciles exactly. The same logic applies in manufacturing (refining is the oil
part); electricity and water are stand-alone sections.

<!-- AUTO:mining -->
| rule | RMSE_log_pct | DM_p_vs_first | decision | branch |
|---|---|---|---|---|
| neutral: held at the last actual level | 67.384 | — | CHOSEN | 8 |
| unit elasticity to construction | 89.668 | 0.042 | — | 8 |
| estimated elasticity to construction | 84.157 | 0.011 | information only | 8 |
| neutral: held at trailing 3-year average | 79.006 | — | — | 7 |
| grows with FR1 mining VA | 72.297 | 0.009 | CHOSEN | 7 |
| grows with FR1 construction VA | 85.660 | 0.198 | — | 7 |

Quarrying: **neutral: held at the last actual level** — the unit-elasticity link to FR1 construction VA against the neutral null: DM/HLN p = 0.042 (both rules anchored on the origin's last actual; pre-cut RMSE 89.7 vs 67.4 log-% for the null; the link is adopted only if significantly MORE accurate, p < 0.10); the free elasticity 0.111 (s.e. 0.334) rejects the unit restriction (p = 0.016). The construction link is kept as the engine lever `quarrying_rule`. Metal ores: grows with FR1 mining VA. Crude oil and natural gas: 33,349.0 → 31,439.6 mn AZN nominal, real -1.21% a year. Metal ores: 729.9 → 884.9 mn AZN nominal, real -1.10% a year. Other mining and quarrying: 244.8 → 280.8 mn AZN nominal, real +0.00% a year. Mining support services: 2,698.4 → 2,543.9 mn AZN nominal, real -1.21% a year. Reconciliation: the four branches equal FR1's mining output to 2.2e-14% in every scenario and year (asserted); the implied deflator of the oil part grows +0.03% a year against FR1's mining deflator +0.07%.
<!-- /AUTO:mining -->

### 11.5 Regions

The κ rule: when constant shares are rejected at the specification stage, the shrinkage intensity is the
lowest-RMSE κ among those significantly better than constant shares (or among the non-inferior ones if none is).

<!-- AUTO:regions -->
Selected: MNL: oil-sector mix (FR1 mining/manufacturing VA), κ = 0.5. Baku's share of industrial output 79.9% in 2025; in 2030: Baseline 77.8%, Adverse 76.8%, Reform 78.2%.
<!-- /AUTO:regions -->

## 12. Hold-out validation, 2020–2025

The forecasting model actually used is re-estimated on data to 2019 (pooled elasticity, oil-price elasticity,
capacity factor) and simulated 2020–2025 with FR1's actual sector value added, deflators, oil price and related-sector
aggregates; no FR10 outcome is fed in. Benchmarks: random walk and constant growth (own 2014–2019 average).

<!-- AUTO:holdout -->
| system | measure | weighting | model | RMSE | U_vs_random_walk | U_vs_constant_growth | DM_p_vs_rw | DM_p_vs_cg |
|---|---|---|---|---|---|---|---|---|
| manufacturing (24 branches): forecasting model | nominal | unweighted | oil block + combo | 50.664 | 0.793 | 0.823 | 0.099 | 0.180 |
| manufacturing (24 branches): forecasting model | nominal | share-weighted | oil block + combo | 38.160 | 0.814 | 0.981 | 0.039 | 0.714 |
| manufacturing (24 branches): forecasting model | real | unweighted | oil block + combo | 56.492 | 0.801 | 0.525 | 0.044 | 0.041 |
| manufacturing (24 branches): forecasting model | real | share-weighted | oil block + combo | 30.814 | 0.765 | 0.704 | 0.088 | 0.051 |
| 14 economic regions | shares_pp | unweighted | MNL: oil-sector mix (FR1 mining/manufacturing VA) | 0.877 | 0.789 | 0.330 | 0.051 | 0.047 |
<!-- /AUTO:holdout -->

<!-- AUTO:holdout_note -->
Real branch output **beats constant growth**: U = 0.525 unweighted (significantly better, DM p 0.041) and 0.704 share-weighted (significantly better, DM p 0.051); for the Part 11 constant-share system the figures were 0.531 (p 0.039, unweighted), 0.701 (p 0.031, share-weighted). Real branch paths should be read with their bands; nominal output is the more reliable output.
<!-- /AUTO:holdout_note -->

Alternative allocations inside the same model (information only):

<!-- AUTO:holdout_full_alt -->
| measure | weighting | model | RMSE | U_vs_random_walk | U_vs_constant_growth |
|---|---|---|---|---|---|
| nominal | unweighted | oil block + pooled | 50.821 | 0.795 | 0.826 |
| nominal | share-weighted | oil block + pooled | 37.915 | 0.809 | 0.975 |
| real | unweighted | oil block + pooled | 56.579 | 0.803 | 0.526 |
| real | share-weighted | oil block + pooled | 30.628 | 0.760 | 0.700 |
| nominal | unweighted | oil block + const | 50.538 | 0.791 | 0.821 |
| nominal | share-weighted | oil block + const | 38.425 | 0.820 | 0.988 |
| real | unweighted | oil block + const | 56.437 | 0.801 | 0.525 |
| real | share-weighted | oil block + const | 31.027 | 0.770 | 0.709 |
<!-- /AUTO:holdout_full_alt -->

Part 11.1 share systems, re-estimated to 2019 (information only; used for no choice):

<!-- AUTO:holdout_info -->
| system | measure | model | RMSE | U_vs_random_walk | U_vs_constant_growth |
|---|---|---|---|---|---|
| manufacturing (24 branches) (Part 11 share systems) | nominal | constant shares | 47.315 | 0.740 | 0.769 |
| manufacturing (24 branches) (Part 11 share systems) | shares_pp | constant shares | 1.462 | 1.000 | 0.586 |
| manufacturing (24 branches) (Part 11 share systems) | nominal | MNL: scale (FR1 real sector VA) | 63.336 | 0.991 | 1.029 |
| manufacturing (24 branches) (Part 11 share systems) | shares_pp | MNL: scale (FR1 real sector VA) | 2.247 | 1.537 | 0.901 |
| manufacturing (24 branches) (Part 11 share systems) | nominal | MNL: oil export price | 48.597 | 0.760 | 0.790 |
| manufacturing (24 branches) (Part 11 share systems) | shares_pp | MNL: oil export price | 1.458 | 0.997 | 0.585 |
| manufacturing (24 branches) (Part 11 share systems) | nominal | MNL: scale + oil price | 66.203 | 1.036 | 1.076 |
| manufacturing (24 branches) (Part 11 share systems) | shares_pp | MNL: scale + oil price | 2.134 | 1.460 | 0.856 |
| manufacturing (24 branches) (Part 11 share systems) | nominal | combination: 1/2 constant + 1/2 MNL scale | 53.326 | 0.834 | 0.866 |
| manufacturing (24 branches) (Part 11 share systems) | shares_pp | combination: 1/2 constant + 1/2 MNL scale | 1.509 | 1.033 | 0.605 |
| mining (4 branches) (Part 11 share systems) | nominal | constant shares | 55.733 | 0.962 | 0.616 |
| mining (4 branches) (Part 11 share systems) | shares_pp | constant shares | 3.122 | 1.000 | 0.337 |
| mining (4 branches) (Part 11 share systems) | nominal | MNL: scale (FR1 real sector VA) | 55.733 | 0.962 | 0.616 |
| mining (4 branches) (Part 11 share systems) | shares_pp | MNL: scale (FR1 real sector VA) | 3.122 | 1.000 | 0.337 |
| mining (4 branches) (Part 11 share systems) | nominal | MNL: oil export price | 53.597 | 0.925 | 0.593 |
| mining (4 branches) (Part 11 share systems) | shares_pp | MNL: oil export price | 2.695 | 0.863 | 0.291 |
| mining (4 branches) (Part 11 share systems) | nominal | MNL: scale + oil price | 49.263 | 0.850 | 0.545 |
| mining (4 branches) (Part 11 share systems) | shares_pp | MNL: scale + oil price | 1.976 | 0.633 | 0.213 |
| mining (4 branches) (Part 11 share systems) | nominal | combination: 1/2 constant + 1/2 MNL scale | 55.733 | 0.962 | 0.616 |
| mining (4 branches) (Part 11 share systems) | shares_pp | combination: 1/2 constant + 1/2 MNL scale | 3.122 | 1.000 | 0.337 |
| 14 economic regions | shares_pp | constant shares | 1.111 | 1.000 | 0.418 |
| 14 economic regions | shares_pp | MNL: scale (FR1 real sector VA) | 0.888 | 0.799 | 0.334 |
| 14 economic regions | shares_pp | MNL: scale + oil-sector mix | 0.928 | 0.835 | 0.349 |
| 14 economic regions | shares_pp | combination: 1/2 constant + 1/2 MNL scale | 0.931 | 0.838 | 0.351 |
<!-- /AUTO:holdout_info -->

## 13. Forecast 2026–2030 under FR1's three scenarios

Section output = 2025 output × FR1 nominal VA index. Refining per §11.2; the rest of manufacturing output is allocated
to the non-oil branches per §11.3; mining branches per §11.4. Non-oil real output = nominal ÷ (2025 deflator ×
FR1 section deflator index). Employment = 2025 DSK headcount × FR4 section index; wages (productivity and margin
sensitivities) = 2025 DSK wage × FR1 average-wage index (F13).

<!-- AUTO:forecast -->
| scenario | industry nominal output growth % pa | manufacturing nominal growth % pa | manufacturing real growth % pa (FR1 rva_man) | refining real growth % pa | mining share of industry 2030 % | non-state share 2030 % (composition) | HHI manufacturing 2030 | Baku share 2030 % | manufacturing GOS % VA 2030 |
|---|---|---|---|---|---|---|---|---|---|
| Baseline | 4.76 | 11.36 | 6.35 | -0.36 | 44.21 | 76.85 | 1198.44 | 77.83 | 65.81 |
| Adverse | -1.16 | 7.12 | 2.86 | -0.36 | 37.33 | 73.53 | 1213.19 | 76.82 | 65.81 |
| Reform | 9.53 | 15.49 | 9.72 | -0.36 | 47.18 | 78.79 | 1187.32 | 78.22 | 65.81 |

Sections, baseline:

| section | nominal output growth % pa | GOS % of VA 2025 | GOS % of VA 2030 |
|---|---|---|---|
| Mining | -1.03 | 93.56 | 94.39 |
| Manufacturing | 11.36 | 65.82 | 65.81 |
| Electricity | 11.23 | 65.44 | 65.89 |
| Water | 9.12 | -51.61 | -40.05 |
<!-- /AUTO:forecast -->

**Branches.**

<!-- AUTO:branches -->
| nace2 | branch | model | nominal growth % pa | real growth % pa | share of industry 2030 % | LP growth % pa |
|---|---|---|---|---|---|---|
| 06 | Crude oil and natural gas | FR1 oil & gas real; residual nominal | -1.17 | -1.21 | 39.54 | -0.51 |
| 07 | Metal ores | metal ores: grows with FR1 mining VA | 3.93 | -1.10 | 1.11 | -0.40 |
| 08 | Other mining and quarrying | quarrying: neutral: held at the last actual level | 2.78 | 0.00 | 0.35 | 0.70 |
| 09 | Mining support services | FR1 oil & gas real; residual nominal | -1.17 | -1.21 | 3.20 | -0.51 |
| 10 | Food products | related-sector: rcons | 14.44 | 9.29 | 12.31 | 8.48 |
| 11 | Beverages | related-sector: rcons | 14.44 | 9.29 | 2.26 | 8.48 |
| 12 | Tobacco products | sector total | 14.80 | 9.63 | 2.80 | 8.82 |
| 13 | Textiles | sector total | 14.80 | 9.63 | 1.03 | 8.82 |
| 14 | Wearing apparel | sector total | 14.80 | 9.63 | 0.50 | 8.82 |
| 15 | Leather and footwear | sector total | 14.80 | 9.63 | 0.09 | 8.82 |
| 16 | Wood products | sector total | 14.80 | 9.63 | 0.09 | 8.82 |
| 17 | Paper products | sector total | 14.80 | 9.63 | 0.68 | 8.82 |
| 18 | Printing | sector total | 14.80 | 9.63 | 0.39 | 8.82 |
| 19 | Refined petroleum products | capacity + oil price | -0.96 | -0.36 | 6.58 | -1.10 |
| 20 | Chemicals | sector total | 14.80 | 9.63 | 3.97 | 8.82 |
| 21 | Pharmaceuticals | sector total | 14.80 | 9.63 | 0.07 | 8.82 |
| 22 | Rubber and plastics | sector total | 14.80 | 9.63 | 1.64 | 8.82 |
| 23 | Non-metallic minerals | related-sector: rva_con | 14.14 | 9.00 | 3.62 | 8.19 |
| 24 | Basic metals | sector total | 14.80 | 9.63 | 2.83 | 8.82 |
| 25 | Fabricated metal products | related-sector: rva_con | 14.14 | 9.00 | 1.82 | 8.19 |
| 26 | Computer and electronics | sector total | 14.80 | 9.63 | 0.17 | 8.82 |
| 27 | Electrical equipment | related-sector: rinv_non | 14.32 | 9.18 | 0.68 | 8.37 |
| 28 | Machinery and equipment | related-sector: rinv_non | 14.32 | 9.18 | 0.32 | 8.37 |
| 29 | Motor vehicles | related-sector: rinv_non | 14.32 | 9.18 | 0.83 | 8.37 |
| 30 | Other transport equipment | related-sector: rinv_non | 14.32 | 9.18 | 0.10 | 8.37 |
| 31 | Furniture | sector total | 14.80 | 9.63 | 0.98 | 8.82 |
| 32 | Other manufacturing | sector total | 14.80 | 9.63 | 0.30 | 8.82 |
| 33 | Repair and installation | related-sector: rinv_non | 14.32 | 9.18 | 2.69 | 8.37 |
| 35 | Electricity, gas and steam | sector total | 11.23 | 2.90 | 7.74 | 2.35 |
| 36 | Water supply and waste | sector total | 9.12 | 4.39 | 1.29 | 3.73 |

Manufacturing branches, baseline real growth 2026–2030: min -0.36% (Refined petroleum products), max +9.63% (Tobacco products). Implied non-oil manufacturing real growth +8.95% a year against +8.11% (2010–19), +9.45% (2021–25), best five-year +10.32% — within history.

Implied cross-sector multipliers (% change in branch output per 1% in the related sector, sector total given):

| nace2 | branch | related_sector | multiplier | multiplier_p5 | multiplier_p95 |
|---|---|---|---|---|---|
| 23 | Non-metallic minerals | rva_con | 0.100 | 0.032 | 0.167 |
| 25 | Fabricated metal products | rva_con | 0.105 | 0.034 | 0.175 |
| 08 | Other mining and quarrying | rva_con | 0.109 | 0.035 | 0.182 |
| 10 | Food products | rcons | 0.076 | 0.025 | 0.127 |
| 11 | Beverages | rcons | 0.103 | 0.034 | 0.173 |
| 27 | Electrical equipment | rinv_non | 0.108 | 0.035 | 0.181 |
| 28 | Machinery and equipment | rinv_non | 0.109 | 0.035 | 0.182 |
| 29 | Motor vehicles | rinv_non | 0.107 | 0.035 | 0.180 |
| 30 | Other transport equipment | rinv_non | 0.109 | 0.035 | 0.183 |
| 33 | Repair and installation | rinv_non | 0.102 | 0.033 | 0.171 |
<!-- /AUTO:branches -->

**Operating-surplus margin — conditional.** The baseline holds each section's labour share of value added at its
2023–25 average, so the margin is neutral by construction; it measures **cash generation and rents, not solvency**
(no balance sheet enters). The branch GOS proxy also omits other taxes and non-employee compensation and, because
DSK branch output includes informal and household production that has no recorded wage bill, it overstates margins
in branches with much informal output.

<!-- AUTO:margin -->
Baseline (labour share of VA held at its 2023–25 average): manufacturing GOS 65.8% of VA in 2025 and 65.8% in 2030. Sensitivities: FR1 wage path 71.7%; wages constant in product terms 73.7%. Median branch GOS-proxy margin 2030: baseline 19.7%, FR1 wage path 24.5%.

| lever | manufacturing real branch growth, min % pa | manufacturing real branch growth, max % pa | refining real growth % pa | building materials real growth % pa | manufacturing GOS % VA 2030 | median branch GOS-proxy margin 2030 | HHI manufacturing 2030 |
|---|---|---|---|---|---|---|---|
| baseline | -0.36 | 9.63 | -0.36 | 9.00 | 65.81 | 19.71 | 1198.44 |
| allocation: pooled model alone | -0.36 | 9.89 | -0.36 | 8.63 | 65.81 | 19.71 | 1194.16 |
| allocation: constant shares | -0.36 | 9.37 | -0.36 | 9.37 | 65.81 | 19.71 | 1202.82 |
| oil-linked branches at maximum throughput | 0.66 | 9.44 | 0.66 | 8.81 | 65.81 | 19.71 | 1202.62 |
| margin: FR1 wage path | -0.36 | 9.63 | -0.36 | 9.00 | 71.65 | 24.46 | 1198.44 |
| margin: wages constant in product terms | -0.36 | 9.63 | -0.36 | 9.00 | 73.70 | 25.46 | 1198.44 |
<!-- /AUTO:margin -->

**Non-state share.**

<!-- AUTO:ns -->
Mining falls from 58.8% to 44.2% of industrial output (baseline); with within-branch non-state shares held (mining 94.1%, refining 1.9%, electricity 3.4%), the industry non-state share moves from 78.1% to 76.8% — **pure composition, not an ownership forecast**.

| nace2 | branch | non-state share held (2025), % | share of industry 2025, % | share of industry 2030, % |
|---|---|---|---|---|
| 6 | Crude oil and natural gas | 95.71 | 52.93 | 39.54 |
| 7 | Metal ores | 39.61 | 1.16 | 1.11 |
| 8 | Other mining and quarrying | 98.02 | 0.39 | 0.35 |
| 9 | Mining support services | 88.50 | 4.28 | 3.20 |
| 10 | Food products | 99.99 | 7.91 | 12.31 |
| 11 | Beverages | 99.11 | 1.45 | 2.26 |
| 12 | Tobacco products | 100.00 | 1.77 | 2.80 |
| 13 | Textiles | 91.75 | 0.65 | 1.03 |
| 14 | Wearing apparel | 95.73 | 0.31 | 0.50 |
| 15 | Leather and footwear | 94.94 | 0.06 | 0.09 |
| 16 | Wood products | 99.84 | 0.06 | 0.09 |
| 17 | Paper products | 100.00 | 0.43 | 0.68 |
| 18 | Printing | 98.44 | 0.24 | 0.39 |
| 19 | Refined petroleum products | 1.86 | 8.72 | 6.58 |
| 20 | Chemicals | 20.13 | 2.51 | 3.97 |
| 21 | Pharmaceuticals | 100.00 | 0.05 | 0.07 |
| 22 | Rubber and plastics | 100.00 | 1.04 | 1.64 |
| 23 | Non-metallic minerals | 99.60 | 2.36 | 3.62 |
| 24 | Basic metals | 100.00 | 1.79 | 2.83 |
| 25 | Fabricated metal products | 60.39 | 1.18 | 1.82 |
| 26 | Computer and electronics | 92.74 | 0.11 | 0.17 |
| 27 | Electrical equipment | 98.83 | 0.44 | 0.68 |
| 28 | Machinery and equipment | 93.75 | 0.21 | 0.32 |
| 29 | Motor vehicles | 76.47 | 0.54 | 0.83 |
| 30 | Other transport equipment | 87.96 | 0.07 | 0.10 |
| 31 | Furniture | 100.00 | 0.62 | 0.98 |
| 32 | Other manufacturing | 89.80 | 0.19 | 0.30 |
| 33 | Repair and installation | 54.15 | 1.74 | 2.69 |
| 35 | Electricity, gas and steam | 3.37 | 5.73 | 7.74 |
| 36 | Water supply and waste | 29.10 | 1.05 | 1.29 |
<!-- /AUTO:ns -->

**Products.** Product volume paths are derived from the branch forecast with the product mix held and anchored on the
2025 actual (v2.1: volume_t = volume_2025 × branch real output_t / real output_2025, a constant base add-factor; a labelled
derivation, not a product model); product market shares are by place of production (DSK 018_1).

<!-- AUTO:products -->
127 products in 25 branches receive **derived** volume paths (product mix held at 2023–25); 91 products have producing places in 2025 (median 3 places, median top-place share 81%). Most concentrated by place:

| product | places | top_place | top_place_share_pct | HHI_places | coverage_of_national_pct |
|---|---|---|---|---|---|
| Light petroleum products, light distillates, thsd. tonnes | 1 | Baku city | 100.0 | 10000.0 | 100.0 |
| Cotton yarn, ton | 1 | Baku city | 100.0 | 10000.0 | — |
| Medicaments, thsd. manat | 1 | Baku city | 100.0 | 10000.0 | 100.0 |
| Mayonnaise, ton | 1 | Sumgayit city | 100.0 | 10000.0 | 100.0 |
| Lubricants, thsd. tonnes | 1 | Baku city | 100.0 | 10000.0 | 100.0 |
| Aluminum pipes, ton | 1 | Ganja city | 100.0 | 10000.0 | 100.0 |
| Laptops, unit | 1 | Mingachevir city | 100.0 | 10000.0 | 100.0 |
| Kerosene, thsd. tonnes | 1 | Baku city | 100.0 | 10000.0 | 100.0 |
<!-- /AUTO:products -->

**Uncertainty.** Each of FR1's 500 baseline replications is combined with a centred historical model-error path
($e_h = u_{s+h} - u_s$ of the model residuals, joint across units; no estimated autocorrelation), parameter draws with
sign rejection, and FR1's employment draw; the batch simulation reproduces the scenario solver exactly.

<!-- AUTO:bands -->
500 FR1 replications; 16 historical model-error paths for the branch allocation and 11 for regions (paths crossing the 2019 coverage break excluded). Average growth 2026–2030 — industry output: baseline +4.76%, median +5.12%, 90% band -3.4% to +14.4%; mining: baseline -1.03%, median -1.06%, 90% band -11.0% to +9.3%; manufacturing: baseline +11.36%, median +11.06%, 90% band +0.8% to +22.4%; electricity: baseline +11.23%, median +11.37%, 90% band -4.8% to +33.8%; water: baseline +9.12%, median +9.16%, 90% band +1.1% to +19.0%. The baseline is FR1's scenario path, the median is that of the replications; they differ because FR1's draws are not centred on its scenario. The wide industry and electricity tails come from FR1's oil- and electricity-price draws: with FR1's prices held at their baseline paths the bands are — industry: baseline +4.76%, median +4.72%, 90% band +1.9% to +8.8%; electricity: baseline +11.23%, median +11.23%, 90% band +8.2% to +14.4%. Refining share of manufacturing in 2030: 9.9–20.0% (baseline 14.1%). Manufacturing GOS share of VA in 2030: 65.8–65.8%. Baseline inside the inter-quartile band in 98.6% of series-years, inside the 90% band in 100.0%.
<!-- /AUTO:bands -->

## 14. Plausibility and early warning

Each forecast growth rate against the unit's own 2010–2019 and 2021–2025 averages and its best and worst five-year
averages since 2005; flags are published with their root cause.

<!-- AUTO:plaus -->
| code | unit | forecast_real_growth | hist_2010_2019 | hist_2021_2025 | best_5yr | worst_5yr | flag | hist_2010_19_inside_90band |
|---|---|---|---|---|---|---|---|---|
| 06 | Crude oil and natural gas | -1.21 | -2.57 | -0.01 | 17.50 | -3.46 | — | no |
| 07 | Metal ores | -1.10 | 10.43 | -0.42 | 252.03 | -8.81 | — | no |
| 08 | Other mining and quarrying | 0.00 | 12.22 | 15.14 | 27.98 | -8.70 | — | no |
| 09 | Mining support services | -1.21 | 18.79 | -18.41 | 27.50 | -20.68 | — | no |
| 10 | Food products | 9.29 | 3.80 | 10.22 | 10.22 | 2.39 | — | yes |
| 11 | Beverages | 9.29 | 8.73 | 7.56 | 10.96 | 0.24 | — | yes |
| 12 | Tobacco products | 9.63 | 16.66 | 13.10 | 50.73 | -14.63 | — | yes |
| 13 | Textiles | 9.63 | 18.84 | 11.63 | 43.24 | -22.65 | — | yes |
| 14 | Wearing apparel | 9.63 | 10.32 | 5.29 | 21.66 | 0.71 | — | yes |
| 15 | Leather and footwear | 9.63 | -9.20 | 10.64 | 19.67 | -18.10 | — | yes |
| 16 | Wood products | 9.63 | 41.13 | -12.70 | 73.42 | -17.94 | — | no |
| 17 | Paper products | 9.63 | 6.84 | 7.41 | 60.85 | -18.43 | — | yes |
| 18 | Printing | 9.63 | 31.14 | -12.71 | 38.68 | -12.71 | — | no |
| 19 | Refined petroleum products | -0.36 | -3.18 | 3.78 | 3.78 | -5.46 | — | no |
| 20 | Chemicals | 9.63 | 12.52 | 10.04 | 17.94 | -3.85 | — | yes |
| 21 | Pharmaceuticals | 9.63 | -3.24 | 40.95 | 55.64 | -30.70 | — | yes |
| 22 | Rubber and plastics | 9.63 | 11.86 | 16.26 | 28.01 | -2.69 | — | yes |
| 23 | Non-metallic minerals | 9.00 | 14.58 | 25.80 | 29.01 | -3.50 | — | yes |
| 24 | Basic metals | 9.63 | 8.71 | 5.98 | 28.12 | -15.56 | — | yes |
| 25 | Fabricated metal products | 9.00 | 6.32 | 15.15 | 29.97 | -17.49 | — | yes |
| 26 | Computer and electronics | 9.63 | 14.59 | -2.03 | 31.08 | -4.94 | — | yes |
| 27 | Electrical equipment | 9.18 | 29.25 | 3.96 | 49.69 | 1.45 | — | yes |
| 28 | Machinery and equipment | 9.18 | -3.70 | -22.20 | 33.34 | -22.20 | — | yes |
| 29 | Motor vehicles | 9.18 | 32.29 | 28.95 | 151.62 | -27.11 | — | yes |
| 30 | Other transport equipment | 9.18 | -1.18 | 91.08 | 91.08 | -23.93 | — | yes |
| 31 | Furniture | 9.63 | 32.66 | 21.72 | 34.29 | 9.58 | — | no |
| 32 | Other manufacturing | 9.63 | 12.63 | 30.95 | 30.95 | -27.63 | — | yes |
| 33 | Repair and installation | 9.18 | 23.16 | 4.10 | 57.65 | -11.50 | — | yes |
| 35 | Electricity, gas and steam | 2.90 | 3.96 | 2.08 | 7.48 | 0.73 | — | yes |
| 36 | Water supply and waste | 4.39 | 4.47 | 9.07 | 9.07 | -4.22 | — | yes |
| B | Mining | -1.10 | -2.21 | -1.39 | 23.44 | -3.37 | — | — |
| C | Manufacturing | 6.35 | 4.32 | 8.09 | 10.15 | 1.28 | — | — |
| D | Electricity | 2.90 | 4.21 | 2.06 | 7.57 | 0.36 | — | — |
| E | Water | 4.39 | 4.51 | 8.88 | 8.88 | 0.59 | — | — |

0 of 34 units flagged.
<!-- /AUTO:plaus -->

Early-warning flags compare 2023–25 with 2020–22 averages, scaled by each branch's own volatility; branches under 0.5%
of manufacturing need two flags only for reporting, a negative margin is an automatic watch, and missing investment is
"insufficient data", never zero. Transparent dashboard thresholds, not estimated probabilities.

<!-- AUTO:ew -->
| nace2 | branch | share_2025_pct | margin_2023_25 | margin_z | share_z | lp_z | F_renewal | F_stocks | n_flags | watch_list |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 | Food products | 22.96 | 20.33 | 0.18 | -2.45 | 1.83 | FLAG | FLAG | 3 | yes |
| 11 | Beverages | 4.22 | 26.51 | -0.10 | 1.87 | 2.13 | — | — | 0 | no |
| 12 | Tobacco products | 5.14 | 40.31 | 0.78 | 0.54 | 0.56 | — | — | 0 | no |
| 13 | Textiles | 1.90 | 22.42 | -0.61 | -0.35 | 1.51 | — | — | 0 | no |
| 14 | Wearing apparel | 0.91 | 7.43 | 0.20 | -0.82 | -0.28 | FLAG | — | 1 | no |
| 15 | Leather and footwear | 0.16 | 11.86 | 0.70 | 0.17 | 4.10 | — | — | 0 | no |
| 16 | Wood products | 0.17 | 19.41 | -1.13 | -4.07 | -0.56 | insufficient data | — | 2 | no |
| 17 | Paper products | 1.25 | 17.09 | 3.43 | 1.68 | 0.53 | — | — | 0 | no |
| 18 | Printing | 0.71 | 27.97 | 0.70 | 0.77 | -0.91 | — | insufficient data | 0 | no |
| 19 | Refined petroleum products | 25.31 | 36.80 | -1.85 | 0.90 | 0.41 | — | — | 1 | no |
| 20 | Chemicals | 7.28 | 27.44 | 0.25 | -0.26 | 3.28 | — | — | 0 | no |
| 21 | Pharmaceuticals | 0.14 | 1.62 | 0.02 | 0.89 | 0.78 | — | insufficient data | 0 | yes |
| 22 | Rubber and plastics | 3.02 | 14.67 | 1.62 | 0.59 | 2.98 | — | — | 0 | no |
| 23 | Non-metallic minerals | 6.84 | 24.15 | -0.19 | 1.17 | 3.24 | — | — | 0 | no |
| 24 | Basic metals | 5.19 | 25.24 | -2.89 | 0.02 | -0.11 | — | — | 1 | no |
| 25 | Fabricated metal products | 3.43 | 17.04 | -0.58 | 0.17 | 1.53 | — | — | 0 | no |
| 26 | Computer and electronics | 0.32 | 22.22 | 0.63 | -0.29 | 1.75 | insufficient data | — | 0 | no |
| 27 | Electrical equipment | 1.27 | 13.25 | 0.64 | -0.30 | 1.69 | — | — | 0 | no |
| 28 | Machinery and equipment | 0.60 | 22.53 | 1.11 | -0.49 | -0.23 | — | — | 0 | no |
| 29 | Motor vehicles | 1.56 | 19.77 | -0.00 | 2.09 | 1.97 | FLAG | — | 1 | no |
| 30 | Other transport equipment | 0.19 | -44.89 | 0.70 | 1.26 | 1.99 | — | insufficient data | 0 | yes |
| 31 | Furniture | 1.81 | 18.29 | 1.84 | 2.95 | 1.49 | FLAG | — | 1 | no |
| 32 | Other manufacturing | 0.56 | 17.41 | 0.05 | -0.78 | 0.23 | — | insufficient data | 0 | no |
| 33 | Repair and installation | 5.05 | 17.45 | 0.70 | 0.74 | -1.49 | — | insufficient data | 1 | no |

Watch list (3): Food products, Pharmaceuticals, Other transport equipment.
<!-- /AUTO:ew -->

## 15. Layer B — the firm-level engine on a replaceable firm panel

**Input.** `data/firm_panel/` holds the synthetic panel (`FR10_firm_panel_SYNTHETIC.csv` and `.xlsx` with a bold
bilingual README sheet and a schema sheet), an empty template with one marked example row
(`FR10_firm_panel_TEMPLATE.csv/.xlsx`), the column map English ↔ Azerbaijani ↔ unit ↔ required ↔ source
(`FR10_firm_panel_column_map.csv`) and `README_FR10_firm_panel.md` (AZ/EN). The schema is the data contract
(`output/FR10_input_schema.csv`): identifiers, NACE Rev.2 division (all sections), region, ownership, size class,
balance sheet (incl. retained earnings, interest-bearing debt, trade payables), P&L (incl. depreciation), operating
cash flow, capex, employees, wage bill, exports, product codes, registration and liquidation dates.

**Loader.** Priority: `FIRM_PANEL_PATH` (environment variable or configuration cell) → `data/firm_panel/FR10_firm_panel.csv`
or `.xlsx` → the SYNTHETIC file. A file whose `data_status` is not the synthetic marker, or that has none, is REAL.
English or Azerbaijani headers are accepted. The validator writes `FR10_firm_panel_validation_report.csv` per row and
field; hard errors (missing required column, non-numeric or negative values, duplicates, invalid codes, balance-sheet
identities) stop the run with a message; warnings (EBIT consistency, missing retained earnings) do not. The synthetic
generator writes only SYNTHETIC-named files and never a real-named one.

**Engine.** Liquidity, leverage, interest cover, DuPont ROE, turnover ratios, Altman Z''-EM (coefficients and zones from
Altman 2005 — not estimated; not computed where retained earnings are missing), multilateral Törnqvist TFP index with
observed cost shares, shares/HHI/CR4 by NACE × region, entry/exit/survival, peer percentiles, firm forecasts = Layer-A
branch forecast × projected share (share growth on lagged relative productivity and leverage, HC1 errors, no lagged
share). Outputs: `FR10_SYNTHETIC_*.csv` (watermarked) in SYNTHETIC mode, `FR10_FIRM_*.csv` in REAL mode.

<!-- AUTO:layerb -->
**Layer-B data mode: SYNTHETIC** — input file `data/firm_panel/FR10_firm_panel_SYNTHETIC.csv`, 22,495 rows, 5,255 firms, 24 NACE divisions, 2019–2025. The firm panel is **SYNTHETIC — not real enterprise data**; Layer-B outputs are a pipeline demonstration, not findings.

**This section is a pipeline demonstration, not findings.** The Ministry replaces `data/firm_panel/FR10_firm_panel_SYNTHETIC.csv` with its own data in its own system (`FR10_firm_panel.csv/.xlsx` or `FIRM_PANEL_PATH`) and re-runs the notebook; outputs then become `FR10_FIRM_*.csv`.

Pipeline tests on the loaded panel:

| test | value | passed |
|---|---|---|
| validator catches 6 seeded corruptions (balance, NACE, negative cash) | 6 | yes |
| DuPont: margin x turnover x multiplier = ROE (max abs) | 1.4e-14 | yes |
| TFP index equals an independent firm-by-firm re-computation (NACE 10, 2024; max abs gap) | 8.9e-16 | yes |
| market shares sum to one in every NACE-year cell (max gap) | 2.2e-16 | yes |
| firm forecasts add up to the Layer-A branch forecast (%) | 2.2e-14 | yes |
| firm-level econometric models estimated (statsmodels = independent numpy computation, asserted) | 14 | yes |
| parameter recovery: consistent estimators within 4 s.e. of the true values (count) | 30/30 | yes |
| peer percentile ranks lie in (0, 100] | 0.048 | yes |
| firm revenues add up to DSK branch output (max gap, %) | 1.5e-08 | yes |
| firm counts equal DSK active enterprises (max gap) | 0.000 | yes |
| determinant model recovers the DGP (true 0.15, -0.30) | 0.152, -0.296 (s.e. 0.005, 0.010) | yes |

Swap tests (temporary directory; the project never holds a real-named file it did not receive):

| test | passed | detail |
|---|---|---|
| real-named file with neutral data_status -> DATA_MODE = REAL | yes | mode REAL, file FR10_firm_panel.csv |
| REAL file passes the validator (0 hard errors) | yes | 0 warnings |
| REAL mode writes FR10_FIRM_* only, without watermark, all tests pass | yes | 11 files, e.g. ['FR10_FIRM_cohort_survival.csv', 'FR10_FIRM_concentration_nace.csv', 'FR10_FIRM_concentration_nace_region_2025.csv'] |
| Azerbaijani headers (xlsx, FIRM_PANEL_PATH) load and validate | yes | 3000 rows, unknown columns [], mode REAL |
| FIRM_PANEL_PATH has priority over the real-named file | yes | loaded panel_az.xlsx |
| broken file: missing required column reported as fatal | yes | required column missing (EN or AZ header) |
| broken file: total assets < current assets flagged per row and the run stops | yes | firm panel rejected: 15 hard errors (first: row 2, field total_assets: total assets < current + fixed assets); see rep.csv |

Validator on the loaded panel: 0 warnings, 0 hard errors (`FR10_firm_panel_validation_report.csv`).
<!-- /AUTO:layerb -->

### 15.1 Firm-level econometrics (v2) — runs on the loaded panel, SYNTHETIC now

The same code runs in SYNTHETIC and REAL mode (a swap test re-runs it on a REAL-named copy and requires identical
estimates). Models: (a) profitability — ROA and the operating margin on size, leverage, liquidity, age, ownership,
export share, region, branch demand growth and unit labour cost, by two-way fixed effects (firm + year) and by pooled
OLS with NACE × year fixed effects; (b) a Cobb–Douglas value-added production function by the within estimator and by
pooled OLS with sector and year dummies, with returns to scale and a cluster-robust CRS test; (c) determinants of
index-number TFP and of production-function TFP; (d) a financial-distress logit (Altman Z''-EM distress zone or negative
equity at t on predictors at t−1) with average marginal effects, ROC/AUC in sample and on the last two years out of
sample, and a calibration table; (e) investment-rate determinants (no lagged investment rate); (f) the market-share
model with its full output; (g) an export-participation logit. All standard errors are cluster-robust by firm
(CR1, t(G−1)); statsmodels results are cross-checked against an independent numpy computation. **Olley–Pakes,
Levinsohn–Petrin and Ackerberg–Caves–Frazer are not used**: they identify the production function by estimating a
first-order Markov (autoregressive) law of motion for productivity, which the requester's constraints exclude.

**Parameter recovery.** v2's synthetic generator overwrites the free balance-sheet and P&L items through a structural
layer with known parameters (exports, value-added share and margin, the production function, investment), keeping
every v1 draw that the share model and the Layer-A consistency checks use. ROA, index-number TFP and the distress zone
are non-linear accounting functions of these blocks, so no closed-form true parameter exists for them (stated in the
tables). Coverage is measured over replications of the structural layer.

**Calibration of the SYNTHETIC panel (v2.2, `DGP_CAL`; level constants, not estimated parameters).** In the previous
version the share of loss-making firms (profit before tax < 0) drifted from 29% (2019) to 42% (2025) and the
aggregate net margin was 5.4% of revenue in 2025 (4.8–8.0% over 2019–2025; profit before tax 6.7–11.5% of deductible
expenses): the capital scale constant was set by branch only, so nominal labour-productivity growth raised capital /
revenue and the interest burden mechanically year after year. Three changes: (1) the capital scale constant is
additive in branch and year (median capital / revenue = 0.5 in every branch-year); (2) the mark-up of the value-added
share over the branch unit labour cost is 0.18 (was 0.15); (3) a year-common intercept $\delta_t$ of the value-added
share is set by bisection so that **25% of firms are loss-making in every year**. Basis of the target: the DVX
declarations report the *amount* of declared losses (14–27% of taxable profit) but not the *number* of loss-making
payers; in firm-level accounts data the loss-making share in manufacturing is typically between a fifth and a third,
and 25% is the middle of that range — a calibration choice, not an Azerbaijani statistic. The reference for the
aggregate margin is the DVX declaration net margin (10.0–13.2% of deductible expenses, 2021–2025, all payers).
Result (2019–2025): loss-making share 25.0% in every year (was 28.9–43.3%); profit before tax 9.2–12.7% of deductible
expenses (was 6.7–11.5%); net profit 6.6–8.8% of revenue (was 4.8–8.0%; 2025: 8.5%, was 5.4%); Altman Z''-EM distress
zone 6.3–8.2% of firms (was 7.5–11.4%), safe zone 79–81% (was 74–80%). Declared losses equal 5–9% of the profits of
profitable firms, below the DVX range (the declarations cover all sectors, and their losses are concentrated in large
payers, which the synthetic panel does not attempt to mimic). $\delta_t$ and the capital year constant are absorbed by
the year effects of every estimator (firm + year, NACE × year, NACE + year), so the true parameters in `DGP_TRUE` are
unchanged; parameter recovery stays 30/30 within 4 s.e. for the consistent estimators, and the Monte Carlo coverage is
essentially unchanged. Revenues still add up to DSK branch output and firm counts equal DSK active enterprises; every
file keeps the SYNTHETIC watermark.

<!-- AUTO:econ_models -->
**Data mode: SYNTHETIC** (FR10_firm_panel_SYNTHETIC.csv, 22,495 rows, 5,255 firms, 2019–2025) — **SYNTHETIC — pipeline test, not results** / *sintetik məlumat — texniki nümayiş*.

| model_id | estimator | dependent | n_obs | n_firms | r2 | r2_type | auc | auc_oos | RTS | crs_p |
|---|---|---|---|---|---|---|---|---|---|---|
| B_roa_fe | Two-way fixed effects (firm + year), firm-demeaned; cluster(firm) | roa | 21888 | 4648 | 0.258 | within R² | — | — | — | — |
| B_roa_pool | Pooled LS + NACE x year fixed effects; cluster(firm) | roa | 22495 | 5255 | 0.435 | R² | — | — | — | — |
| B_margin_fe | Two-way fixed effects (firm + year), firm-demeaned; cluster(firm) | op_margin | 21849 | 4644 | 0.410 | within R² | — | — | — | — |
| B_margin_pool | Pooled LS + NACE x year fixed effects; cluster(firm) | op_margin | 22456 | 5251 | 0.643 | R² | — | — | — | — |
| B_pf_fe | Two-way fixed effects (firm + year), firm-demeaned; cluster(firm) | ln_va | 21888 | 4648 | 0.950 | within R² | — | — | 0.945 | 0.000 |
| B_pf_pool | Pooled LS + NACE and year dummies; cluster(firm) | ln_va | 22495 | 5255 | 0.991 | R² | — | — | 0.955 | 0.000 |
| B_tfp_idx | Pooled LS + NACE x year fixed effects; cluster(firm) | tfp_idx | 22495 | 5255 | 0.151 | R² | — | — | — | — |
| B_tfp_idx_fe | Two-way fixed effects (firm + year), firm-demeaned; cluster(firm) | tfp_idx | 21888 | 4648 | 0.033 | within R² | — | — | — | — |
| B_tfp_pf | Pooled LS + NACE x year fixed effects; cluster(firm) | tfp_pf | 22495 | 5255 | 0.601 | R² | — | — | — | — |
| B_distress | Logit (MLE), dummies year; cluster(firm) | distress | 17240 | 4648 | 0.387 | McFadden pseudo-R² | 0.918 | 0.920 | — | — |
| B_invest_fe | Two-way fixed effects (firm + year), firm-demeaned; cluster(firm) | inv_rate | 16279 | 3687 | 0.457 | within R² | — | — | — | — |
| B_invest_pool | Pooled LS + NACE x year fixed effects; cluster(firm) | inv_rate | 17240 | 4648 | 0.518 | R² | — | — | — | — |
| B_export | Logit (MLE), dummies nace2 + year; cluster(firm) | exporter | 17240 | 4648 | 0.112 | McFadden pseudo-R² | 0.724 | — | — | — |

Coefficients (cluster-robust by firm):

| model_id | term | coef | se | p | ci_low | ci_high |
|---|---|---|---|---|---|---|
| B_roa_fe | ln_emp | 0.0152 | 0.0024 | 0.0000 | 0.0105 | 0.0200 |
| B_roa_fe | leverage | -0.1807 | 0.0262 | 0.0000 | -0.2322 | -0.1293 |
| B_roa_fe | ln_current_ratio | -0.0150 | 0.0024 | 0.0000 | -0.0197 | -0.0104 |
| B_roa_fe | ln_age | 0.0026 | 0.0015 | 0.0817 | -0.0003 | 0.0054 |
| B_roa_fe | export_share | 0.0296 | 0.0043 | 0.0000 | 0.0211 | 0.0380 |
| B_roa_fe | demand_growth | 0.0885 | 0.0072 | 0.0000 | 0.0743 | 0.1027 |
| B_roa_fe | ulc | -1.1098 | 0.0636 | 0.0000 | -1.2345 | -0.9851 |
| B_roa_pool | ln_emp | 0.0102 | 0.0009 | 0.0000 | 0.0085 | 0.0120 |
| B_roa_pool | leverage | -0.1753 | 0.0088 | 0.0000 | -0.1926 | -0.1579 |
| B_roa_pool | ln_current_ratio | -0.0136 | 0.0023 | 0.0000 | -0.0182 | -0.0090 |
| B_roa_pool | ln_age | 0.0034 | 0.0009 | 0.0002 | 0.0016 | 0.0052 |
| B_roa_pool | state | -0.0349 | 0.0038 | 0.0000 | -0.0423 | -0.0275 |
| B_roa_pool | foreign | 0.0218 | 0.0042 | 0.0000 | 0.0136 | 0.0300 |
| B_roa_pool | joint | 0.0085 | 0.0049 | 0.0811 | -0.0010 | 0.0180 |
| B_roa_pool | export_share | 0.0244 | 0.0048 | 0.0000 | 0.0151 | 0.0338 |
| B_roa_pool | baku | 0.0059 | 0.0021 | 0.0046 | 0.0018 | 0.0100 |
| B_roa_pool | ulc | -1.0098 | 0.0330 | 0.0000 | -1.0745 | -0.9451 |
| B_margin_fe | ln_emp | 0.0094 | 0.0012 | 0.0000 | 0.0070 | 0.0117 |
| B_margin_fe | leverage | -0.0614 | 0.0134 | 0.0000 | -0.0877 | -0.0352 |
| B_margin_fe | ln_current_ratio | 0.0120 | 0.0013 | 0.0000 | 0.0094 | 0.0145 |
| B_margin_fe | ln_age | 0.0042 | 0.0009 | 0.0000 | 0.0025 | 0.0059 |
| B_margin_fe | export_share | 0.0513 | 0.0030 | 0.0000 | 0.0455 | 0.0572 |
| B_margin_fe | demand_growth | 0.0778 | 0.0022 | 0.0000 | 0.0736 | 0.0820 |
| B_margin_fe | ulc | -1.0063 | 0.0142 | 0.0000 | -1.0342 | -0.9784 |
| B_margin_pool | ln_emp | 0.0156 | 0.0004 | 0.0000 | 0.0149 | 0.0163 |
| B_margin_pool | leverage | -0.0585 | 0.0044 | 0.0000 | -0.0671 | -0.0499 |
| B_margin_pool | ln_current_ratio | 0.0115 | 0.0012 | 0.0000 | 0.0091 | 0.0138 |
| B_margin_pool | ln_age | 0.0064 | 0.0005 | 0.0000 | 0.0055 | 0.0074 |
| B_margin_pool | state | -0.0283 | 0.0017 | 0.0000 | -0.0317 | -0.0249 |
| B_margin_pool | foreign | 0.0238 | 0.0021 | 0.0000 | 0.0197 | 0.0278 |
| B_margin_pool | joint | 0.0053 | 0.0027 | 0.0528 | -0.0001 | 0.0107 |
| B_margin_pool | export_share | 0.0545 | 0.0029 | 0.0000 | 0.0488 | 0.0602 |
| B_margin_pool | baku | 0.0087 | 0.0011 | 0.0000 | 0.0065 | 0.0108 |
| B_margin_pool | ulc | -0.9946 | 0.0085 | 0.0000 | -1.0112 | -0.9779 |
| B_pf_fe | ln_L | 0.4468 | 0.0025 | 0.0000 | 0.4419 | 0.4517 |
| B_pf_fe | ln_K | 0.4984 | 0.0014 | 0.0000 | 0.4958 | 0.5011 |
| B_pf_pool | ln_L | 0.4956 | 0.0027 | 0.0000 | 0.4903 | 0.5009 |
| B_pf_pool | ln_K | 0.4599 | 0.0021 | 0.0000 | 0.4558 | 0.4640 |
| B_tfp_idx | ln_emp | -0.0210 | 0.0009 | 0.0000 | -0.0229 | -0.0192 |
| B_tfp_idx | ln_age | -0.0034 | 0.0009 | 0.0002 | -0.0051 | -0.0016 |
| B_tfp_idx | state | -0.0175 | 0.0035 | 0.0000 | -0.0244 | -0.0107 |
| B_tfp_idx | foreign | 0.0260 | 0.0054 | 0.0000 | 0.0154 | 0.0365 |
| B_tfp_idx | joint | 0.0089 | 0.0067 | 0.1843 | -0.0042 | 0.0220 |
| B_tfp_idx | exporter | -0.0055 | 0.0015 | 0.0002 | -0.0085 | -0.0026 |
| B_tfp_idx | leverage | 0.0196 | 0.0063 | 0.0019 | 0.0072 | 0.0319 |
| B_tfp_idx | baku | -0.0014 | 0.0024 | 0.5692 | -0.0062 | 0.0034 |
| B_tfp_idx_fe | ln_emp | -0.0201 | 0.0015 | 0.0000 | -0.0230 | -0.0172 |
| B_tfp_idx_fe | ln_age | -0.0014 | 0.0008 | 0.0883 | -0.0030 | 0.0002 |
| B_tfp_idx_fe | exporter | -0.0036 | 0.0009 | 0.0001 | -0.0054 | -0.0018 |
| B_tfp_idx_fe | leverage | 0.0288 | 0.0143 | 0.0437 | 0.0008 | 0.0569 |
| B_tfp_pf | state | -0.0756 | 0.0082 | 0.0000 | -0.0917 | -0.0595 |
| B_tfp_pf | foreign | 0.0983 | 0.0089 | 0.0000 | 0.0809 | 0.1157 |
| B_tfp_pf | joint | 0.0350 | 0.0140 | 0.0127 | 0.0075 | 0.0625 |
| B_distress | leverage_l1 | 10.0756 | 0.3592 | 0.0000 | 9.3716 | 10.7796 |
| B_distress | ln_current_ratio_l1 | 0.0172 | 0.1188 | 0.8849 | -0.2156 | 0.2500 |
| B_distress | roa_w_l1 | -7.7893 | 0.4027 | 0.0000 | -8.5785 | -7.0000 |
| B_distress | ln_emp_l1 | -0.0677 | 0.0254 | 0.0077 | -0.1175 | -0.0179 |
| B_distress | export_share_l1 | 0.3731 | 0.2626 | 0.1554 | -0.1417 | 0.8878 |
| B_distress | ln_age | -0.1709 | 0.0468 | 0.0003 | -0.2627 | -0.0791 |
| B_distress | state | 0.2897 | 0.1183 | 0.0143 | 0.0578 | 0.5217 |
| B_distress | foreign | -0.0374 | 0.1535 | 0.8075 | -0.3383 | 0.2635 |
| B_distress | demand_growth | -2.5513 | 0.1566 | 0.0000 | -2.8583 | -2.2443 |
| B_invest_fe | sales_growth | 0.0810 | 0.0010 | 0.0000 | 0.0791 | 0.0830 |
| B_invest_fe | leverage_l1 | -0.0578 | 0.0103 | 0.0000 | -0.0780 | -0.0376 |
| B_invest_fe | roa_w_l1 | 0.2080 | 0.0044 | 0.0000 | 0.1992 | 0.2167 |
| B_invest_fe | ln_emp_l1 | -0.0045 | 0.0010 | 0.0000 | -0.0064 | -0.0026 |
| B_invest_pool | sales_growth | 0.0820 | 0.0013 | 0.0000 | 0.0795 | 0.0845 |
| B_invest_pool | leverage_l1 | -0.0523 | 0.0024 | 0.0000 | -0.0570 | -0.0475 |
| B_invest_pool | roa_w_l1 | 0.2102 | 0.0040 | 0.0000 | 0.2024 | 0.2180 |
| B_invest_pool | ln_emp_l1 | -0.0040 | 0.0003 | 0.0000 | -0.0045 | -0.0034 |
| B_invest_pool | state | -0.0207 | 0.0014 | 0.0000 | -0.0233 | -0.0180 |
| B_invest_pool | foreign | -0.0004 | 0.0016 | 0.8184 | -0.0034 | 0.0027 |
| B_invest_pool | joint | -0.0001 | 0.0019 | 0.9670 | -0.0038 | 0.0037 |
| B_export | ln_emp_l1 | 0.4057 | 0.0138 | 0.0000 | 0.3787 | 0.4327 |
| B_export | foreign | 1.0329 | 0.0624 | 0.0000 | 0.9107 | 1.1551 |
| B_export | state | -0.6258 | 0.0642 | 0.0000 | -0.7517 | -0.4999 |
| B_export | joint | 0.3588 | 0.1114 | 0.0013 | 0.1404 | 0.5772 |
| B_export | ln_age | 0.1913 | 0.0247 | 0.0000 | 0.1429 | 0.2397 |
| B_export | baku | 0.2878 | 0.0385 | 0.0000 | 0.2123 | 0.3633 |
| B_share | rel_lp_l1 | 0.1520 | 0.0046 | 0.0000 | 0.1431 | 0.1610 |
| B_share | rel_leverage_l1 | -0.2963 | 0.0104 | 0.0000 | -0.3167 | -0.2759 |

Interpretation (Azerbaijani):

- **B_roa_fe**: [sintetik məlumat — texniki nümayiş] 4,648 müəssisə, 21,888 müşahidə (2019–2025). Daxili R² = 0.258. Əsas amillər: vahid əmək xərci (əmək haqqı fondu / gəlir) −1.110 (azaldır, p < 0.001); sahə tələbinin artımı (Δln DSK buraxılışı) 0.089 (artırır, p < 0.001); borc yükü (öhdəliklər / aktivlər) −0.181 (azaldır, p < 0.001); ixracın gəlirdə payı 0.030 (artırır, p < 0.001). Zamanla dəyişməyən amillər (mülkiyyət, region) müəssisə effektlərinə daxildir; onlar birləşdirilmiş modeldə qiymətləndirilir.
- **B_roa_pool**: [sintetik məlumat — texniki nümayiş] 5,255 müəssisə, 22,495 müşahidə (2019–2025). R² = 0.435. Əsas amillər: vahid əmək xərci (əmək haqqı fondu / gəlir) −1.010 (azaldır, p < 0.001); borc yükü (öhdəliklər / aktivlər) −0.175 (azaldır, p < 0.001); ln işçilərin sayı (ölçü) 0.010 (artırır, p < 0.001); dövlət mülkiyyəti −0.035 (azaldır, p < 0.001). Sahə tələbinin artımı NACE × il effektlərinə daxildir; o, iki yönlü FE modelində qiymətləndirilir.
- **B_margin_fe**: [sintetik məlumat — texniki nümayiş] 4,644 müəssisə, 21,849 müşahidə (2019–2025). Daxili R² = 0.410. Əsas amillər: vahid əmək xərci (əmək haqqı fondu / gəlir) −1.006 (azaldır, p < 0.001); sahə tələbinin artımı (Δln DSK buraxılışı) 0.078 (artırır, p < 0.001); ixracın gəlirdə payı 0.051 (artırır, p < 0.001); ln cari likvidlik əmsalı 0.012 (artırır, p < 0.001). Zamanla dəyişməyən amillər (mülkiyyət, region) müəssisə effektlərinə daxildir; onlar birləşdirilmiş modeldə qiymətləndirilir.
- **B_margin_pool**: [sintetik məlumat — texniki nümayiş] 5,251 müəssisə, 22,456 müşahidə (2019–2025). R² = 0.643. Əsas amillər: vahid əmək xərci (əmək haqqı fondu / gəlir) −0.995 (azaldır, p < 0.001); ln işçilərin sayı (ölçü) 0.016 (artırır, p < 0.001); ixracın gəlirdə payı 0.054 (artırır, p < 0.001); dövlət mülkiyyəti −0.028 (azaldır, p < 0.001). Sahə tələbinin artımı NACE × il effektlərinə daxildir; o, iki yönlü FE modelində qiymətləndirilir.
- **B_pf_fe**: [sintetik məlumat — texniki nümayiş] 4,648 müəssisə, 21,888 müşahidə (2019–2025). Daxili R² = 0.950. Əmək elastikliyi 0.447, kapital elastikliyi 0.498; miqyasdan gəlir 0.945 [0.941, 0.949]; sabit gəlir (CRS) hipotezi p = 0.0000 ilə rədd edilir. Olley–Pakes / Levinsohn–Petrin / ACF tətbiq edilmir: onlar məhsuldarlıq üçün avtoreqressiv (Markov) hərəkət qanunu qiymətləndirir, bu isə sifarişçinin məhdudiyyətinə ziddir.
- **B_pf_pool**: [sintetik məlumat — texniki nümayiş] 5,255 müəssisə, 22,495 müşahidə (2019–2025). R² = 0.991. Əmək elastikliyi 0.496, kapital elastikliyi 0.460; miqyasdan gəlir 0.955 [0.953, 0.958]; sabit gəlir (CRS) hipotezi p = 0.0000 ilə rədd edilir. Olley–Pakes / Levinsohn–Petrin / ACF tətbiq edilmir: onlar məhsuldarlıq üçün avtoreqressiv (Markov) hərəkət qanunu qiymətləndirir, bu isə sifarişçinin məhdudiyyətinə ziddir. Birləşdirilmiş OLS müəssisənin daimi məhsuldarlığını nəzərə almır; FE qiymətləndiricisi ilə fərq bu sürüşməni göstərir.
- **B_tfp_idx**: [sintetik məlumat — texniki nümayiş] 5,255 müəssisə, 22,495 müşahidə (2019–2025). R² = 0.151. TFP ilə əlaqəli amillər: ln işçilərin sayı (ölçü) −0.021 (azaldır, p < 0.001); dövlət mülkiyyəti −0.018 (azaldır, p < 0.001); xarici mülkiyyət 0.026 (artırır, p < 0.001); ln(1 + yaş) −0.003 (azaldır, p < 0.001).
- **B_tfp_idx_fe**: [sintetik məlumat — texniki nümayiş] 4,648 müəssisə, 21,888 müşahidə (2019–2025). Daxili R² = 0.033. TFP ilə əlaqəli amillər: ln işçilərin sayı (ölçü) −0.020 (azaldır, p < 0.001); ixracatçı (0/1) −0.004 (azaldır, p < 0.001); borc yükü (öhdəliklər / aktivlər) 0.029 (artırır, p = 0.044).
- **B_tfp_pf**: [sintetik məlumat — texniki nümayiş] 5,255 müəssisə, 22,495 müşahidə (2019–2025). R² = 0.601. TFP ilə əlaqəli amillər: xarici mülkiyyət 0.098 (artırır, p < 0.001); dövlət mülkiyyəti −0.076 (azaldır, p < 0.001); birgə mülkiyyət 0.035 (artırır, p = 0.013).
- **B_distress**: [sintetik məlumat — texniki nümayiş] 4,648 müəssisə, 17,240 müşahidə (2020–2025). Çətinlik tezliyi 7.1%. AUC nümunədə 0.918, son iki ildə (nümunədən kənar, 2020-2023 üzrə qiymətləndirilmiş) 0.920; Brier 0.0460; Hosmer–Lemeshow p = 0.152. Ən böyük orta marjinal effektlər: borc yükü, t−1 0.4550; ROA, t−1 (±0,3 hüdudunda) −0.3518; sahə tələbinin artımı (Δln DSK buraxılışı) −0.1152. Gecikmiş çətinlik statusu modelə daxil edilmir.
- **B_invest_fe**: [sintetik məlumat — texniki nümayiş] 3,687 müəssisə, 16,279 müşahidə (2020–2025). Daxili R² = 0.457. İnvestisiya normasının amilləri: satışların artımı (Δln gəlir) 0.081 (artırır, p < 0.001); ROA, t−1 (±0,3 hüdudunda) 0.208 (artırır, p < 0.001); borc yükü, t−1 −0.058 (azaldır, p < 0.001); ln işçilərin sayı, t−1 −0.004 (azaldır, p < 0.001). Gecikmiş investisiya norması modeldə yoxdur.
- **B_invest_pool**: [sintetik məlumat — texniki nümayiş] 4,648 müəssisə, 17,240 müşahidə (2020–2025). R² = 0.518. İnvestisiya normasının amilləri: satışların artımı (Δln gəlir) 0.082 (artırır, p < 0.001); ROA, t−1 (±0,3 hüdudunda) 0.210 (artırır, p < 0.001); borc yükü, t−1 −0.052 (azaldır, p < 0.001); dövlət mülkiyyəti −0.021 (azaldır, p < 0.001). Gecikmiş investisiya norması modeldə yoxdur.
- **B_export**: [sintetik məlumat — texniki nümayiş] 4,648 müəssisə, 17,240 müşahidə (2020–2025). İxracatçıların payı 25.3%; AUC 0.724. Ən böyük orta marjinal effektlər: xarici mülkiyyət 0.1703; dövlət mülkiyyəti −0.1031; ln işçilərin sayı, t−1 0.0669.
- **B_share**: [sintetik məlumat — texniki nümayiş] Bazar payının illik dəyişməsi əvvəlki ilin nisbi əmək məhsuldarlığı ilə 0.152 (s.x. 0.005), nisbi borc yükü ilə −0.296 (s.x. 0.010) əlaqəlidir; 17,240 müşahidə. Gecikmiş pay modeldə yoxdur; proqnozda paylar sahə daxilində normallaşdırılır.
- **recovery**: [sintetik məlumat — texniki nümayiş] Generatorun məlum parametrləri ilə müqayisə: 35/43 həqiqi parametr 95% etibarlılıq intervalına düşür; ardıcıl (FE, logit, pay modeli) qiymətləndiricilərdə 26/30. Birləşdirilmiş OLS-in istehsal funksiyasında və marjanın ölçü əmsalında sürüşmə gözləniləndir (daimi müəssisə effekti izahedici dəyişənlərlə korrelyasiyalıdır). ROA, indeks TFP və çətinlik modeli üçün generatorda qapalı həqiqi parametr yoxdur.
- **recovery_mc**: [sintetik məlumat — texniki nümayiş] 40 təkrarlamada (struktur qat yenidən çəkilir) ardıcıl qiymətləndiricilərin 23 parametri üzrə 95% etibarlılıq intervalının orta əhatəsi 94.7% (minimum 88%); sürüşmə testinin maksimum |t| = 3.8. Birləşdirilmiş OLS-də maksimum |t| = 131: daimi müəssisə effektləri nəzərə alınmadıqda əmsallar sürüşür.
<!-- /AUTO:econ_models -->

<!-- AUTO:econ_recovery -->
| model_id | term | true | estimate | se | ci_low | ci_high | covered |
|---|---|---|---|---|---|---|---|
| B_margin_fe | ln_emp | 0.0100 | 0.0094 | 0.0012 | 0.0070 | 0.0117 | yes |
| B_margin_fe | leverage | -0.0600 | -0.0614 | 0.0134 | -0.0877 | -0.0352 | yes |
| B_margin_fe | ln_current_ratio | 0.0120 | 0.0120 | 0.0013 | 0.0094 | 0.0145 | yes |
| B_margin_fe | ln_age | 0.0060 | 0.0042 | 0.0009 | 0.0025 | 0.0059 | no |
| B_margin_fe | export_share | 0.0500 | 0.0513 | 0.0030 | 0.0455 | 0.0572 | yes |
| B_margin_fe | demand_growth | 0.0800 | 0.0778 | 0.0022 | 0.0736 | 0.0820 | yes |
| B_margin_fe | ulc | -1.0000 | -1.0063 | 0.0142 | -1.0342 | -0.9784 | yes |
| B_margin_pool | ln_emp | 0.0100 | 0.0156 | 0.0004 | 0.0149 | 0.0163 | no |
| B_margin_pool | leverage | -0.0600 | -0.0585 | 0.0044 | -0.0671 | -0.0499 | yes |
| B_margin_pool | ln_current_ratio | 0.0120 | 0.0115 | 0.0012 | 0.0091 | 0.0138 | yes |
| B_margin_pool | ln_age | 0.0060 | 0.0064 | 0.0005 | 0.0055 | 0.0074 | yes |
| B_margin_pool | state | -0.0300 | -0.0283 | 0.0017 | -0.0317 | -0.0249 | yes |
| B_margin_pool | foreign | 0.0250 | 0.0238 | 0.0021 | 0.0197 | 0.0278 | yes |
| B_margin_pool | joint | 0.0100 | 0.0053 | 0.0027 | -0.0001 | 0.0107 | yes |
| B_margin_pool | export_share | 0.0500 | 0.0545 | 0.0029 | 0.0488 | 0.0602 | yes |
| B_margin_pool | baku | 0.0100 | 0.0087 | 0.0011 | 0.0065 | 0.0108 | yes |
| B_margin_pool | ulc | -1.0000 | -0.9946 | 0.0085 | -1.0112 | -0.9779 | yes |
| B_pf_fe | ln_L | 0.4500 | 0.4468 | 0.0025 | 0.4419 | 0.4517 | yes |
| B_pf_fe | ln_K | 0.5000 | 0.4984 | 0.0014 | 0.4958 | 0.5011 | yes |
| B_pf_fe | RTS | 0.9500 | 0.9452 | 0.0021 | 0.9410 | 0.9494 | no |
| B_pf_pool | ln_L | 0.4500 | 0.4956 | 0.0027 | 0.4903 | 0.5009 | no |
| B_pf_pool | ln_K | 0.5000 | 0.4599 | 0.0021 | 0.4558 | 0.4640 | no |
| B_pf_pool | RTS | 0.9500 | 0.9555 | 0.0015 | 0.9526 | 0.9584 | no |
| B_tfp_pf | state | -0.0800 | -0.0756 | 0.0082 | -0.0917 | -0.0595 | yes |
| B_tfp_pf | foreign | 0.1000 | 0.0983 | 0.0089 | 0.0809 | 0.1157 | yes |
| B_tfp_pf | joint | 0.0500 | 0.0350 | 0.0140 | 0.0075 | 0.0625 | yes |
| B_invest_fe | sales_growth | 0.0800 | 0.0810 | 0.0010 | 0.0791 | 0.0830 | yes |
| B_invest_fe | leverage_l1 | -0.0600 | -0.0578 | 0.0103 | -0.0780 | -0.0376 | yes |
| B_invest_fe | roa_w_l1 | 0.2000 | 0.2080 | 0.0044 | 0.1992 | 0.2167 | yes |
| B_invest_fe | ln_emp_l1 | -0.0040 | -0.0045 | 0.0010 | -0.0064 | -0.0026 | yes |
| B_invest_pool | sales_growth | 0.0800 | 0.0820 | 0.0013 | 0.0795 | 0.0845 | yes |
| B_invest_pool | leverage_l1 | -0.0600 | -0.0523 | 0.0024 | -0.0570 | -0.0475 | no |
| B_invest_pool | roa_w_l1 | 0.2000 | 0.2102 | 0.0040 | 0.2024 | 0.2180 | no |
| B_invest_pool | ln_emp_l1 | -0.0040 | -0.0040 | 0.0003 | -0.0045 | -0.0034 | yes |
| B_invest_pool | state | -0.0200 | -0.0207 | 0.0014 | -0.0233 | -0.0180 | yes |
| B_export | ln_emp_l1 | 0.4000 | 0.4057 | 0.0138 | 0.3787 | 0.4327 | yes |
| B_export | foreign | 1.0000 | 1.0329 | 0.0624 | 0.9107 | 1.1551 | yes |
| B_export | state | -0.6000 | -0.6258 | 0.0642 | -0.7517 | -0.4999 | yes |
| B_export | joint | 0.4000 | 0.3588 | 0.1114 | 0.1404 | 0.5772 | yes |
| B_export | ln_age | 0.2000 | 0.1913 | 0.0247 | 0.1429 | 0.2397 | yes |
| B_export | baku | 0.3000 | 0.2878 | 0.0385 | 0.2123 | 0.3633 | yes |
| B_share | rel_lp_l1 | 0.1500 | 0.1520 | 0.0046 | 0.1431 | 0.1610 | yes |
| B_share | rel_leverage_l1 | -0.3000 | -0.2963 | 0.0104 | -0.3167 | -0.2759 | yes |

Over 40 replications of the structural layer (`FR10_SYNTHETIC_econ_recovery_mc.csv`): consistent estimators' mean 95% coverage 94.7% (minimum 88%), largest |bias t| 3.77; pooled OLS (production function, margin size effect) largest |bias t| 131 — the bias the within estimator removes.

| model_id | term | true | mean_estimate | mc_sd | mean_se | coverage_95 | bias_t |
|---|---|---|---|---|---|---|---|
| B_pf_fe | ln_L | 0.4500 | 0.4500 | 0.0027 | 0.0025 | 0.9000 | 0.1063 |
| B_pf_fe | ln_K | 0.5000 | 0.5002 | 0.0011 | 0.0014 | 1.0000 | 1.0525 |
| B_pf_fe | RTS | 0.9500 | 0.9502 | 0.0025 | 0.0021 | 0.9500 | 0.5976 |
| B_pf_pool | ln_L | 0.4500 | 0.4953 | 0.0027 | 0.0027 | 0.0000 | 106.3899 |
| B_pf_pool | ln_K | 0.5000 | 0.4592 | 0.0020 | 0.0020 | 0.0000 | -130.5119 |
| B_pf_pool | RTS | 0.9500 | 0.9544 | 0.0012 | 0.0015 | 0.1000 | 23.6317 |
| B_margin_fe | ln_emp | 0.0100 | 0.0099 | 0.0012 | 0.0012 | 0.9750 | -0.4439 |
| B_margin_fe | leverage | -0.0600 | -0.0616 | 0.0127 | 0.0134 | 0.9750 | -0.7993 |
| B_margin_fe | ln_current_ratio | 0.0120 | 0.0118 | 0.0013 | 0.0013 | 0.9500 | -0.7807 |
| B_margin_fe | ln_age | 0.0060 | 0.0060 | 0.0009 | 0.0009 | 0.9500 | 0.3225 |
| B_margin_fe | export_share | 0.0500 | 0.0504 | 0.0029 | 0.0030 | 0.9750 | 0.9139 |
| B_margin_fe | demand_growth | 0.0800 | 0.0801 | 0.0022 | 0.0021 | 0.9500 | 0.2799 |
| B_margin_fe | ulc | -1.0000 | -0.9979 | 0.0175 | 0.0142 | 0.8750 | 0.7490 |
| B_margin_pool | ln_emp | 0.0100 | 0.0156 | 0.0004 | 0.0004 | 0.0000 | 94.7993 |
| B_margin_pool | leverage | -0.0600 | -0.0561 | 0.0041 | 0.0044 | 0.8750 | 5.9568 |
| B_margin_pool | ln_current_ratio | 0.0120 | 0.0121 | 0.0011 | 0.0012 | 0.9500 | 0.6802 |
| B_margin_pool | ln_age | 0.0060 | 0.0066 | 0.0004 | 0.0005 | 0.8500 | 10.6394 |
| B_margin_pool | state | -0.0300 | -0.0299 | 0.0018 | 0.0017 | 0.9250 | 0.4389 |
| B_margin_pool | foreign | 0.0250 | 0.0245 | 0.0019 | 0.0020 | 0.9500 | -1.7820 |
| B_margin_pool | joint | 0.0100 | 0.0101 | 0.0029 | 0.0028 | 0.9250 | 0.1139 |
| B_margin_pool | export_share | 0.0500 | 0.0509 | 0.0026 | 0.0029 | 0.9750 | 2.2057 |
| B_margin_pool | baku | 0.0100 | 0.0099 | 0.0009 | 0.0011 | 1.0000 | -0.9627 |
| B_margin_pool | ulc | -1.0000 | -0.9904 | 0.0083 | 0.0085 | 0.7750 | 7.3042 |
| B_invest_fe | sales_growth | 0.0800 | 0.0800 | 0.0009 | 0.0010 | 0.9750 | 0.0194 |
| B_invest_fe | leverage_l1 | -0.0600 | -0.0537 | 0.0105 | 0.0103 | 0.9250 | 3.7716 |
| B_invest_fe | roa_w_l1 | 0.2000 | 0.1999 | 0.0038 | 0.0045 | 0.9750 | -0.1291 |
| B_invest_fe | ln_emp_l1 | -0.0040 | -0.0040 | 0.0010 | 0.0010 | 0.9250 | -0.1100 |
| B_tfp_pf | state | -0.0800 | -0.0787 | 0.0078 | 0.0077 | 0.9000 | 1.0428 |
| B_tfp_pf | foreign | 0.1000 | 0.0975 | 0.0087 | 0.0088 | 0.9250 | -1.8122 |
| B_tfp_pf | joint | 0.0500 | 0.0505 | 0.0113 | 0.0128 | 1.0000 | 0.2770 |
| B_export | ln_emp_l1 | 0.4000 | 0.4000 | 0.0162 | 0.0134 | 0.9000 | -0.0087 |
| B_export | foreign | 1.0000 | 0.9834 | 0.0446 | 0.0618 | 1.0000 | -2.3469 |
| B_export | state | -0.6000 | -0.6159 | 0.0700 | 0.0671 | 0.9500 | -1.4362 |
| B_export | joint | 0.4000 | 0.3957 | 0.0908 | 0.0920 | 0.9250 | -0.2991 |
| B_export | ln_age | 0.2000 | 0.1961 | 0.0230 | 0.0241 | 0.9250 | -1.0839 |
| B_export | baku | 0.3000 | 0.3013 | 0.0333 | 0.0382 | 0.9500 | 0.2411 |
<!-- /AUTO:econ_recovery -->

## 16. Arithmetic checks

<!-- AUTO:checks -->
32 of 32 arithmetic checks pass (`FR10_identity_checks.csv`); every one holds by construction.
<!-- /AUTO:checks -->

## 17. Limitations

1. The related-sector elasticity is significant in sample but its out-of-sample allocation gain over constant shares
   is not established; the baseline combination follows a rule fixed in advance (§11.3).
2. Real branch output rests on implicit deflators and on DSK volume indices that are inconsistent with nominal output
   for several small branches (F15; the failing indices are replaced by the v2.1 rule and flagged imputed); its
   hold-out score is in §12. Nominal output remains the more reliable output.
3. The refining capacity rule assumes no new capacity; the lever shows the 2015–25 maximum.
4. Financial condition is aggregate until Layer-B data arrive; the margin is conditional on the labour-share rule and
   the branch GOS proxy is an upper bound (informal output, omitted taxes).
5. Efficiency measures rely on implicit deflators and perpetual-inventory capital; small-branch TFP is noisy.
6. The determinants panel has the power of its 15 (8) years.
7. Exports, branch PPIs, energy costs, branch credit and renewal rates are not available (§6).
8. In SYNTHETIC mode the Layer-B econometrics (§15.1) demonstrate the method and recover the generator's known
   parameters; they are not findings about Azerbaijani enterprises. They become an analysis when the Ministry loads its data.

## 18. Outputs

`FR10.ipynb` — executed end to end with 0 errors; its last code cell regenerates the numeric blocks of this document.
The notebook locates its files relative to its own directory.

<!-- AUTO:outputs -->
`FR10_SYNTHETIC_cohort_survival.csv`, `FR10_SYNTHETIC_concentration_nace.csv`, `FR10_SYNTHETIC_concentration_nace_region_2025.csv`, `FR10_SYNTHETIC_coverage_vs_layer_a.csv`, `FR10_SYNTHETIC_econ_coefficients.csv`, `FR10_SYNTHETIC_econ_distress_ame.csv`, `FR10_SYNTHETIC_econ_distress_calibration.csv`, `FR10_SYNTHETIC_econ_distress_roc.csv`, `FR10_SYNTHETIC_econ_export_ame.csv`, `FR10_SYNTHETIC_econ_export_calibration.csv`, `FR10_SYNTHETIC_econ_export_roc.csv`, `FR10_SYNTHETIC_econ_interpretation_az.csv`, `FR10_SYNTHETIC_econ_models.csv`, `FR10_SYNTHETIC_econ_production_function.csv`, `FR10_SYNTHETIC_econ_recovery.csv`, `FR10_SYNTHETIC_econ_recovery_mc.csv`, `FR10_SYNTHETIC_econ_sample_rules.csv`, `FR10_SYNTHETIC_econ_true_parameters.csv`, `FR10_SYNTHETIC_entry_exit.csv`, `FR10_SYNTHETIC_firm_forecast.csv`, `FR10_SYNTHETIC_firm_ratios_2025.csv`, `FR10_SYNTHETIC_pipeline_tests.csv`, `FR10_SYNTHETIC_share_model.csv`, `FR10_SYNTHETIC_validation_seeded_corruptions.csv`, `FR10_branch_deflator_check.csv`, `FR10_branch_growth_table.csv`, `FR10_branch_history.csv`, `FR10_branch_scorecard.csv`, `FR10_branch_shares_history.csv`, `FR10_coef_sensitivity.csv`, `FR10_concentration.csv`, `FR10_cross_sector_multipliers.csv`, `FR10_data_gaps_and_alternatives.csv`, `FR10_data_integrity_findings.csv`, `FR10_data_source_matrix.csv`, `FR10_determinants_division_bias.csv`, `FR10_determinants_panel.csv`, `FR10_dsk_manifest.csv`, `FR10_dvx_declarations.csv`, `FR10_early_warning.csv`, `FR10_efficiency_branches.csv`, `FR10_fan_charts.csv`, `FR10_fan_meta.csv`, `FR10_financial_sections.csv`, `FR10_firm_panel_swap_tests.csv`, `FR10_firm_panel_swap_tests_econ.csv`, `FR10_firm_panel_validation_report.csv`, `FR10_forecast_assumptions.csv`, `FR10_forecast_branches.csv`, `FR10_forecast_regions.csv`, `FR10_forecast_sections.csv`, `FR10_forecast_tidy.csv`, `FR10_growth_contributions.csv`, `FR10_holdout_branches.csv`, `FR10_holdout_validation.csv`, `FR10_identity_checks.csv`, `FR10_indicator_catalog.csv`, `FR10_input_schema.csv`, `FR10_mining_reconciliation.csv`, `FR10_mining_rules_selection.csv`, `FR10_noar_constructs.csv`, `FR10_nonoil_allocation_selection.csv`, `FR10_nonoil_growth_vs_history.csv`, `FR10_nonstate_composition.csv`, `FR10_nonstate_composition_summary.csv`, `FR10_not_forecast.csv`, `FR10_oil_linked_block.csv`, `FR10_ownership.csv`, `FR10_plausibility.csv`, `FR10_pooled_related_sector_model.csv`, `FR10_presentation_spec.csv`, `FR10_product_forecasts_derived.csv`, `FR10_product_location_shares.csv`, `FR10_products.csv`, `FR10_quadrant.csv`, `FR10_regional_entry_exit.csv`, `FR10_regional_history.csv`, `FR10_rejected_specifications.csv`, `FR10_robustness_summary.csv`, `FR10_scenario_summary.csv`, `FR10_sensitivity_levers.csv`, `FR10_share_system_coefficients.csv`, `FR10_share_system_selection.csv`, `FR10_strings_az.csv`, `FR10_tfp_branches.csv`, `FR10_tfp_sections.csv`, `FR10_volume_index_validation.csv`, `FR10_wage_productivity_gap.csv`
<!-- /AUTO:outputs -->

## 19. v2: equation registry, scenario engine, robustness, Azerbaijani strings

**Registry** (`output/FR10_equations.json`, built with `microlib.registry`; the registry re-estimates every OLS, DOLS
and panel equation with statsmodels and asserts the coefficients equal the notebook's). Registered: the regional share
system actually used (level and difference forms per region and the shrunk system), the manufacturing and mining
share-system candidates as estimated at the 2019 cut (rejected: constant shares were chosen), the pooled related-sector
model and its levels variant, the oil-linked price elasticities, the mining rules, the determinants panel (two-way FE,
DK, wild bootstrap p-values, division-bias variants, between and co-movement regressions) and every Layer-B model.

<!-- AUTO:v2_registry -->
133 equations (119 Layer A, 14 Layer B — SYNTHETIC, `synthetic: true`); 18 Layer-A equations enter the forecast. Registry vs notebook: 111 coefficient checks, max abs difference 0.0e+00.

| layer | subtask | equations | used in forecast | stable | partly stable | unstable |
|---|---|---|---|---|---|---|
| A | A1. Market shares: manufacturing branches | 71 | 1 | 20 | 27 | 24 |
| A | A2. Market shares: mining branches | 12 | 2 | 0 | 3 | 9 |
| A | A3. Regional split: industry shares of the economic regions | 27 | 14 | 13 | 12 | 2 |
| A | A4. Oil-linked branches (refining, chemicals) | 2 | 1 | 1 | 1 | 0 |
| A | A5. Drivers of growth and decline (determinants panel) | 7 | 0 | 0 | 3 | 4 |
| B | B. Firm level: SYNTHETIC data — pipeline demonstration — (a) Profitability determinants | 4 | 0 | 4 | 0 | 0 |
| B | B. Firm level: SYNTHETIC data — pipeline demonstration — (b) Production function | 2 | 0 | 2 | 0 | 0 |
| B | B. Firm level: SYNTHETIC data — pipeline demonstration — (c) TFP determinants | 3 | 0 | 3 | 0 | 0 |
| B | B. Firm level: SYNTHETIC data — pipeline demonstration — (d) Financial distress model | 1 | 0 | 0 | 1 | 0 |
| B | B. Firm level: SYNTHETIC data — pipeline demonstration — (e) Investment rate | 2 | 0 | 1 | 1 | 0 |
| B | B. Firm level: SYNTHETIC data — pipeline demonstration — (f) Market-share determinants | 1 | 1 | 1 | 0 | 0 |
| B | B. Firm level: SYNTHETIC data — pipeline demonstration — (g) Export participation | 1 | 0 | 1 | 0 | 0 |

Equations used in the forecast:

| equation | estimator | verdict | failed_tests |
|---|---|---|---|
| FR10.reg_Nakhchivan_AR_fd | OLS | unstable | Chow 2016 p=0.007; Chow 2015 p=0.011 |
| FR10.reg_Absheron_Khizi_fd | OLS | partly stable | CUSUM p=0.026 |
| FR10.reg_Daghlig_Shirvan_fd | OLS | stable | value used (x2 = -0.422) outside the 95% interval (EB shrinkage) |
| FR10.reg_Ganja_Dashkasan_fd | OLS | partly stable | CUSUM p=0.042 |
| FR10.reg_Garabagh_fd | OLS | stable | value used (x2 = -0.256) outside the 95% interval (EB shrinkage) |
| FR10.reg_Gazakh_Tovuz_fd | OLS | stable | value used (x2 = -0.403) outside the 95% interval (EB shrinkage) |
| FR10.reg_Guba_Khachmaz_lvl | DOLS(+-1) | stable | cointegration not established; value used (x2 = -0.246) outside the 95% interval (EB shrinkage) |
| FR10.reg_Lankaran_Astara_fd | OLS | stable | value used (x2 = -0.412) outside the 95% interval (EB shrinkage) |
| FR10.reg_Central_Aran_lvl | DOLS(+-1) | partly stable | CUSUM p=0.003; cointegration not established; value used (x2 = -0.288) outside the 95% interval (EB shrinkage) |
| FR10.reg_Mil_Mughan_fd | OLS | stable | — |
| FR10.reg_Shaki_Zagatala_fd | OLS | stable | value used (x2 = -0.254) outside the 95% interval (EB shrinkage) |
| FR10.reg_Eastern_Zangezur_fd | OLS | partly stable | recursive sign flip (x2) |
| FR10.reg_Shirvan_Salyan_fd | OLS | partly stable | recursive sign flip (x2) |
| FR10.reg_system | MNL log-odds share system, empirical-Bayes shrinkage (kappa=0.5) | partly stable | — |
| FR10.pooled | FE-oneway (branch), first differences | partly stable | recursive sign flip (x) |
| FR10.oil_19 | OLS | partly stable | CUSUM p=0.046 |
| FR10.mining_08_rule | Calibrated rule: anchored null, real output constant at the last actual level | partly stable | — |
| FR10.mining_07 | Calibrated rule: unit elasticity, chosen pre-cut | partly stable | — |
<!-- /AUTO:v2_registry -->

**Components and forecast table.** `output/FR10_indicator_catalog.csv`, `output/FR10_forecast_tidy.csv`,
`output/FR10_not_forecast.csv`.

<!-- AUTO:v2_tidy -->
414 components (prod 127, lp_thsd_AZN_2015 30, output_real_mn_AZN_2015 30, wage_AZN_month 30, output_nominal_mn_AZN 30, employees 30, share_of_industry 30, share_of_manufacturing 24, gos_proxy_margin_pct 24, reg_share 14, reg_output 14, sec_output 4, sec_VA 4, sec_OTP 4, sec_GOS 4, sec_GOS_share_VA 4, sec_labour_share_VA 4, sec_CE 4, ind_output 1, hhi_man 1, nonstate_share 1) × 3 scenarios × 5 years: complete (asserted); history from each series' first year; 5–95% bands for 193 components (Baseline). Not forecast, with the reason:

| id_pattern | label | reason |
|---|---|---|
| fr10:tfp:<branch/section> | TFP by branch and section | TFP is measured by growth accounting; forecasting it needs branch capital stocks and intermediate consumption, which FR1 does not provide by branch |
| fr10:early_warning:<branch> | early-warning flags | The flags are decision rules on recent observed changes (2023–25 vs 2020–22); not a forecast object |
| fr10:investment_rate:<branch> | investment rate, stocks, innovation, capital productivity | FR1 has no exogenous driver for these efficiency indicators; a forecast from their own history is not allowed (no autoregression) |
| fr10:sme_share:<activity> | SME shares | Only 2023–2024 (two years) available; held at the 2024 level, no model |
| fr10:enterprises:<branch/region> | enterprise counts, entry and exit | No structural driver model for entry and exit has been built; a forecast from their own history is not allowed |
| fr10:dvx:<indicator> | DVX declaration aggregates | Only 2021–2025 (5 years) and economy-wide, not by branch — not enough for a forecast |
| fr10:product_location_share:<product> | product shares by place of production | No driver for the shares by place of production; descriptive indicator |
| fr10:firm:<firm_id> | firm-level forecasts (Layer B) | Layer B runs on the SYNTHETIC panel; in synthetic mode it is a pipeline demonstration only (FR10_SYNTHETIC_firm_forecast.csv), not a Layer-A component |
| fr10:regional_nonstate_share:<region> | regional non-state share | No model for the regional ownership structure; historical indicator |
<!-- /AUTO:v2_tidy -->

**Scenario engine** (`microlib/engines/fr10.py`, state `output/engine/FR10_state.json` + `.npz`). Upstream FR1 (driver
paths `fr1:<code>`) and, since v2.1, FR4 (`fr4:hired:<activity>` → section employment indices, 2025 = 1); without
upstream results the CSV baselines in the state are used; FR3 is not used (F13). FR4's indices are also editable exogenous inputs. Coefficients editable with value, s.e. and CI from
the registry; levers: refinery capacity factor, labour-share shift and margin rule, the combination weight of the
non-oil allocation, κ of the regional system, the quarrying rule and — as a lever, not an estimated coefficient — the
elasticity of its construction link (`quarrying_link_elasticity` = 1, the unit-link rule; the baseline uses the anchored null).

<!-- AUTO:v2_engine -->
Inputs: 20 exogenous paths (FR1 drivers and FR4 indices, 2026–2030, per scenario), 16 coefficients, 7 levers. Self-test: Baseline max rel. diff 1.3e-15 over 2070 values, Adverse max rel. diff 1.1e-15 over 2070 values, Reform max rel. diff 1.4e-15 over 2070 values — PASS; run time 0.008 s per scenario.

| eq_id | name | label | value | se | ci_low | ci_high |
|---|---|---|---|---|---|---|
| FR10.pooled | x | Related-sector elasticity β (non-oil branch shares) | 0.219 | 0.090 | 0.031 | 0.408 |
| FR10.oil_19 | dln_oil_azn | Refined petroleum products: elasticity of the deflator to the oil price | 0.330 | 0.074 | 0.175 | 0.486 |
| FR10.mining_07 | dln_rva_min | Metal ores: elasticity to the driver (rule: 1) | 1.000 | — | — | — |
| FR10.reg_system | Nakhchivan_AR | Nakhchivan AR: elasticity to the oil-sector mix (shrunk) | -0.161 | 0.130 | -0.417 | 0.094 |
| FR10.reg_system | Absheron_Khizi | Absheron-Khizi: elasticity to the oil-sector mix (shrunk) | -0.164 | 0.127 | -0.414 | 0.085 |
| FR10.reg_system | Daghlig_Shirvan | Daghlig Shirvan: elasticity to the oil-sector mix (shrunk) | -0.422 | 0.108 | -0.634 | -0.210 |
| FR10.reg_system | Ganja_Dashkasan | Ganja-Dashkasan: elasticity to the oil-sector mix (shrunk) | -0.203 | 0.133 | -0.464 | 0.057 |
| FR10.reg_system | Garabagh | Garabagh: elasticity to the oil-sector mix (shrunk) | -0.256 | 0.132 | -0.514 | 0.002 |
| FR10.reg_system | Gazakh_Tovuz | Gazakh-Tovuz: elasticity to the oil-sector mix (shrunk) | -0.403 | 0.106 | -0.612 | -0.194 |
| FR10.reg_system | Guba_Khachmaz | Guba-Khachmaz: elasticity to the oil-sector mix (shrunk) | -0.246 | 0.132 | -0.505 | 0.013 |
| FR10.reg_system | Lankaran_Astara | Lankaran-Astara: elasticity to the oil-sector mix (shrunk) | -0.412 | 0.086 | -0.580 | -0.243 |
| FR10.reg_system | Central_Aran | Central Aran: elasticity to the oil-sector mix (shrunk) | -0.288 | 0.136 | -0.554 | -0.022 |
| FR10.reg_system | Mil_Mughan | Mil-Mughan: elasticity to the oil-sector mix (shrunk) | -0.127 | 0.127 | -0.376 | 0.121 |
| FR10.reg_system | Shaki_Zagatala | Shaki-Zagatala: elasticity to the oil-sector mix (shrunk) | -0.254 | 0.129 | -0.508 | -0.001 |
| FR10.reg_system | Eastern_Zangezur | Eastern Zangezur: elasticity to the oil-sector mix (shrunk) | -0.096 | 0.153 | -0.397 | 0.204 |
| FR10.reg_system | Shirvan_Salyan | Shirvan-Salyan: elasticity to the oil-sector mix (shrunk) | -0.119 | 0.122 | -0.358 | 0.120 |

The quarrying (08) construction-link elasticity is a lever (`quarrying_link_elasticity` = 1.000, the unit-link rule), not an estimated coefficient: it acts only when `quarrying_rule = construction_link`; the baseline uses the anchored null. The estimate (`FR10.mining_08`) is 0.111 (95% CI -0.59 to 0.81); unit elasticity is rejected (p = 0.016).
<!-- /AUTO:v2_engine -->

**Robustness and sensitivity** (`output/FR10_robustness_summary.csv`, `output/FR10_coef_sensitivity.csv`). Verdict rule
of the registry: *stabil* if every used coefficient keeps its sign in the recursive and leave-one-year-out paths and
Chow/CUSUM p > 0.05; *qeyri-stabil* if a sign flips in the last half of the recursive path or Chow p < 0.01; otherwise
*qismən stabil*. FR10's section totals are FR1's paths, so the coefficients redistribute output between branches and
regions but do not move the industry, manufacturing or mining totals — the tornado shows this honestly.

<!-- AUTO:v2_sens -->
Robustness verdicts: A unstable: 39, A partly stable: 46, A stable: 34, B partly stable: 2, B stable: 12. Non-zero 2030 effects on the headline components (Baseline, % of the baseline value, −1 s.e. / +1 s.e. or lever low / high); no coefficient or lever moves: industrial output, total; Manufacturing: output; Mining: output (they are FR1 paths). 

| component | type | input | effect_low_pct | effect_high_pct |
|---|---|---|---|---|
| Manufacturing: GOS share of value added | lever | margin_mode | +8.877 | +11.995 |
| Manufacturing: GOS share of value added | lever | labour_share_shift_pp | +1.520 | -1.520 |
| 19 Refined petroleum products: share of manufacturing output | lever | cap_factor_19 | -5.091 | +5.091 |
| 19 Refined petroleum products: share of manufacturing output | coefficient | FR10.oil_19/dln_oil_azn | +0.683 | -0.678 |

Each coefficient's largest 2030 effect on any component (± 1 s.e.):

| input | component | effect_low_pct | effect_high_pct |
|---|---|---|---|
| FR10.pooled/x | 23 Non-metallic minerals: real output, 2015 prices | +0.694 | -0.688 |
| FR10.oil_19/dln_oil_azn | 19 Refined petroleum products: nominal output | +0.683 | -0.678 |
| FR10.reg_system/Nakhchivan_AR | Nakhchivan AR: share of industrial output | +7.924 | -7.347 |
| FR10.reg_system/Absheron_Khizi | Absheron-Khizi: share of industrial output | +7.156 | -6.715 |
| FR10.reg_system/Daghlig_Shirvan | Daghlig Shirvan: share of industrial output | +6.577 | -6.172 |
| FR10.reg_system/Ganja_Dashkasan | Ganja-Dashkasan: share of industrial output | +7.978 | -7.401 |
| FR10.reg_system/Garabagh | Garabagh: share of industrial output | +7.867 | -7.306 |
| FR10.reg_system/Gazakh_Tovuz | Gazakh-Tovuz: share of industrial output | +6.385 | -6.007 |
| FR10.reg_system/Guba_Khachmaz | Guba-Khachmaz: share of industrial output | +8.034 | -7.441 |
| FR10.reg_system/Lankaran_Astara | Lankaran-Astara: share of industrial output | +5.154 | -4.903 |
| FR10.reg_system/Central_Aran | Central Aran: share of industrial output | +8.187 | -7.578 |
| FR10.reg_system/Mil_Mughan | Mil-Mughan: share of industrial output | +7.667 | -7.128 |
| FR10.reg_system/Shaki_Zagatala | Shaki-Zagatala: share of industrial output | +7.844 | -7.279 |
| FR10.reg_system/Eastern_Zangezur | Eastern Zangezur: share of industrial output | +9.449 | -8.634 |
| FR10.reg_system/Shirvan_Salyan | Shirvan-Salyan: share of industrial output | +7.333 | -6.840 |
<!-- /AUTO:v2_sens -->

**Azerbaijani strings** (`output/FR10_strings_az.csv`).

<!-- AUTO:v2_strings -->
1082 English strings in FR10's CSVs; translation template 865, DSK az (018) 137, DSK az (018_1) 49, branch dictionary 24, region dictionary 4, composed at run time (v2.1) 3. Products with the official DSK Azerbaijani name: 142 of 142.
<!-- /AUTO:v2_strings -->
