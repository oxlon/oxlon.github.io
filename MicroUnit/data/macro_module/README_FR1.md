# data/macro_module — files FR1 (v2.2) takes from the Ministry's macro module (15.5.1)

Source module (read-only, never modified): `/Users/econ0757/My Drive/OxLon/18august/model`.
Copies are kept here so the MicroUnit project is self-contained. FR1 takes DATA and OFFICIAL PLAN FIGURES only;
none of the macro module's own projections (AR(1)/five-year-average profiles, ensembles, its 2026 GDP path) is used.
Read by `FR1.ipynb`, Part 3.6. Other files in this folder with the prefix `fr345_` belong to FR3/FR4/FR5.

| File | Source path (in the macro module) | MD5 | What it is | Used by FR1 for |
|---|---|---|---|---|
| `8_vereq_original.xlsx` | `data/8_vereq_original.xlsx` | `eb11d02be05aa825b09b2107bdfb87a5` (identical copy) | Ministry workbook "natural indicators of the main products by sector"; sheet `2.4.1.4.` rows "Neft hasilatı" (thousand t) and "Qaz hasilatı" (mln m³): 2013–2024 report, 2025–2030 plan ("Proqnoz") | **Baseline oil and gas output growth 2027–2030** (plan growth rates applied to the 2026 level implied by the January–March 2026 outturn). Plan 2025 = 28.45 mt oil vs actual 27.68 (plan +2.8%); gas 50.39 bcm vs 50.92 (−1.0%). |
| `dsmf_sspf_budget_1995_2024.csv` | extracted from `src/data_layer.py` (MD5 `428c7401306bbd8412fd45c871982838`), dictionary `MOE_SSPF`, lines 3389–3405; the macro module's own source is `MOE FISCAL.xlsx`, sheet `Pension Fund` (rows 4, 10, 12, 13, 14), not present in either project | `05e520d9fd6f6e2b37f942e1b20ad0c6` (this CSV) | State Social Protection Fund (DSMF) budget, mln AZN: revenue, transfers from the state budget, **expenditure**, payments to population, labour pensions; actuals 1995 (2000/2005)–2024 | Transfers leg of the household income decomposition (E3b) and its pension bridge (E3d). Estimated and registered; **not used in the forecast** (hold-out, Part 11.6) — available through the engine lever `income_block = legs`. |
| `external_block_annual.csv` | `data/external_block_annual.csv` | `c3f35af1e65caa10dbc3ce0611f8cedd` (identical copy) | Annual external block: policy rates, spreads, partner GDP, NEER, **REER (2015 = 1)**, import prices; 2000–2025 actual, 2026–2030 that module's projections | REER **actuals only (≤ 2025)** for the D4 import-equation candidate (rejected: wrong-signed REER, worse hold-out). The 2026–2030 rows are not used. |

Also used, but from this project's OWN workbook (`data/Statistik data dinamika 05.06.2026 +.xlsx`, sheet `DİP 2016-2026`,
row "Dövlət əsaslı vəsait qoyuluşunun cəmi"): the State Investment Programme 2016–2025 actual expenditure and the
**2026 planned allocation of 2 700.0 mln AZN** (2025 actual 2 305.1; executed to 01.04.2026: 365.4). The macro module
uses the same cell (`data/assumptions.csv`, key `state_capex_realg`, 2026 note "DİP 2016-2026 vərəqinin 'Nəzərdə
tutulmuş vəsait' xanası (2 700.0 mln AZN)").

Household income account rows (workbook `Sosial sektor`, rows 35, 37, 41–44) are read from the project's own
workbook as well (the same file, MD5 `6c043c8cda81569dfebe3a2585a74622`, sits in the macro module's `data/`).
