"""FR1 v2.2 note (EN): what was taken from the Ministry's macro module.  Figures: this run's FR1_v22_macro_candidates.csv,
FR1_equations.json, forecasts and data; v2.1 comparisons and non-exported figures: v22_reference.json."""
from types import SimpleNamespace

from .common import pm
from .fr1 import sp

V_LEGS = "E3: income legs (macro module, nominal)"
V_LEGS_R = "E3: income legs deflated by consumer prices"
V_G5 = "G5 mining: export price index + exchange rate (macro module)"
V_G5C = "G5 mining: CPI + export price index + exchange rate"
V_D4 = "D4 imports: absorption + REER (macro module)"
V_F = "Fiscal: non-oil balance / non-oil GDP held at the cut year"
MED = "median of the 14 Part-11.5 variables"


def vals(F):
    N = SimpleNamespace(); R = F.ref; v21 = R["v21"]; v22 = R["v22"]; ne = F.docfig["v22"]   # ne: FR1_doc_figures.json
    c, cur, pre = F.cand, F.cur, F.pre
    coef = lambda eq, nm: next(x for x in F.E[eq]["coefficients"] if x["name"] == nm)
    N.plan_oil, N.act_oil = F.plan25["oil"], F.A.loc[F.LAST, "oil_prod"]
    N.err_oil = (N.plan_oil / N.act_oil - 1) * 100
    N.err_gas = (F.plan25["gas"] / F.A.loc[F.LAST, "gas_prod"] - 1) * 100
    N.oil30, N.oil30_21 = ne["oil_2030_baseline_mt"], v21["oil_2030_baseline_mt"]
    N.onestep = ne["legs_onestep_rmse_pp"]
    N.el = [coef("FR1.E3a_wb", "dln_payroll")["coef"], coef("FR1.E3b_tr", "dln_dsmf")["coef"], coef("FR1.E3c_oth", "dln_gdpnon_n")["coef"]]
    N.legs, N.legs_c, N.legs_n = c(V_LEGS, "rhhdisp"), c(V_LEGS, "rcons"), c(V_LEGS, "hhdisp_n")
    N.legs_r = c(V_LEGS_R, "rhhdisp")
    N.price30 = abs(ne["cpi_level_holdout_err_2025"])
    N.g5 = {k: c(V_G5, k) for k in ("p_min", "gdp_n", "p_gdp", "rgdp")}
    N.imp_cur, N.imp_pre = cur("rm_non").U_rw, pre("rm_non").U_rw
    N.g5c = c(V_G5C, "p_min").U_rw
    g5 = F.E["FR1.G5_defl_min"]
    N.fit = [coef("FR1.G5_defl_min", k)["coef"] for k in ("const", "dln_xpi", "dln_fx")]
    N.r2a = g5["fit"]["r2_adj"]; N.verdict = g5["robustness"]["verdict"]
    N.chow = g5["robustness"]["chow"]
    N.sip, N.sip25, N.sipsh = F.sip, F.A.loc[F.LAST, "exp_pubinv_n"], ne["sip_share_2025"]
    N.ist26, N.ist26_21 = v22["rinv_state_growth_2026_baseline"], v21["rinv_state_growth_2026_baseline"]
    N.f_exp, N.f_bal = c(V_F, "exp_tot_n"), c(V_F, "bal_gdp")
    N.bal30 = v22["balance_gdp_2030"]                 # the v2.2 run (this note records the v2.2 stage)
    N.lever = ne["nobd_lever_balance_2030_bn"]
    N.reer20 = ne["reer_coef_to2020"]; N.reer = coef("FR1.D4_mnon.absorb_reer", "ln_reer")
    N.d4 = c(V_D4, "rm_non")
    N.d30 = {k: (v22["baseline_2030"][k] / v21["baseline_2030"][k] - 1) * 100 for k in v21["baseline_2030"]}
    N.avg_g, N.avg_n = v22["avg_growth_rgdp"], v22["avg_growth_rgdpnon"]
    N.avg_g21, N.avg_n21 = v21["avg_growth_rgdp"]["Baseline"], v21["avg_growth_rgdpnon"]["Baseline"]
    N.bal26, N.bal26_21 = v22["balance_2026_baseline"], v21["balance_2026_baseline"]
    N.med, N.med_pre = cur(MED), pre(MED)
    N.neq, N.nused, N.ncat = v22["n_equations"], v22["n_used"], v22["n_catalog"]
    N.mw = ne["minwage_legs_rhhdisp_2030"]
    return N


def note_en(F):
    N = vals(F); L, Lp = N.legs, N.legs
    g = N.g5; m, mp = N.med, N.med_pre
    return f"""## v2.2 (2026-10-05): what was taken from the Ministry's macro module (15.5.1)

The macro module (`18august/model`, read-only) covers FR1–FR5 from the macro side. Its data and official plan figures were
reviewed for FR1; every candidate was **re-estimated in FR1's framework** (same sample conventions, small-sample HAC, coherence
rule), selected on data ≤ 2020 and tested in the **untouched dynamic 2021–2025 hold-out** of §6.2, against the pre-v2.2 model
(new notebook Part 11.6, `FR1_v22_macro_candidates.csv`). Data copies with source path and MD5: `data/macro_module/README_FR1.md`.
Nothing from the macro module's own forecasting (AR(1)/five-year-average profiles, CPI/wage/unemployment ensembles, ECM/AR(6)
specifications, Okun equation, its 2026 GDP path that ignores the January–April 2026 actuals) is used.

| Item | Decision | Hold-out evidence (Theil U vs RW 2020 / vs constant growth 2010–19; RMSE) |
|---|---|---|
| 1. Oil and gas output | **Adopted** (assumption): Baseline growth 2027–30 = Ministry plan (`8_vereq_original.xlsx`, 2.4.1.4) on the 2026 level from the January–March outturn; Adverse = pre-v2.2 Baseline oil decline (−4.2…−3.0%), gas plan − 1 pp; Reform = plan + the pre-v2.2 Reform gaps | Plan, not an estimate. The plan over-stated 2025 oil output ({N.plan_oil:.2f} vs {N.act_oil:.2f} mt, {pm(N.err_oil, 1)}%; gas {pm(N.err_gas, 1)}%). Baseline oil 2030: {N.oil30:.1f} mt (pre-v2.2 {N.oil30_21:.1f}) |
| 2. Household income by source (wage bill + DSMF transfers + other income, Δln legs) | **Rejected** for the forecast; engine lever `income_block = legs` | In sample the legs fit better (one-step RMSE of real income growth ≤ 2020: {N.onestep[0]:.1f} vs {N.onestep[1]:.1f} pp; elasticities {N.el[0]:.2f} wage bill, {N.el[1]:.2f} DSMF, {N.el[2]:.2f} other income — as in the macro module). Dynamic hold-out, real disposable income: U {L.U_rw:.2f} / {L.U_cg:.2f}, RMSE {L.rmse:.1f}% vs **{Lp.U_rw_pre:.2f} / {Lp.U_cg_pre:.2f}, {Lp.rmse_pre:.1f}%**; consumption {N.legs_c.U_rw:.2f} vs {N.legs_c.U_rw_pre:.2f}. The legs are nominal: the pre-cut model under-predicts the 2025 price level by {N.price30:.0f}%, and the under-indexed nominal legs turn that into too much real income. Deflated by consumer prices: {N.legs_r.U_rw:.2f} / {N.legs_r.U_cg:.2f} (rejected). Nominal disposable income is better with the legs (U {N.legs_n.U_rw:.2f} vs {N.legs_n.U_rw_pre:.2f}) |
| 3. Mining deflator on the export-value-weighted oil+gas export price index + exchange rate | **Adopted** (the macro module's form, no CPI term) | Mining deflator U **{g['p_min'].U_rw:.2f} / {g['p_min'].U_cg:.2f}** (RMSE {g['p_min'].rmse:.1f}%) vs {g['p_min'].U_rw_pre:.2f} / {g['p_min'].U_cg_pre:.2f} ({g['p_min'].rmse_pre:.1f}%); nominal GDP {g['gdp_n'].U_rw:.2f} / {g['gdp_n'].U_cg:.2f} vs {g['gdp_n'].U_rw_pre:.2f} / {g['gdp_n'].U_cg_pre:.2f}; GDP deflator {g['p_gdp'].U_rw:.2f} vs {g['p_gdp'].U_rw_pre:.2f}. Side effects: real GDP {g['rgdp'].U_rw:.2f} / {g['rgdp'].U_cg:.2f} vs {g['rgdp'].U_rw_pre:.2f} / {g['rgdp'].U_cg_pre:.2f} (chain weights), imports {N.imp_cur:.2f} vs {N.imp_pre:.2f} (the wrong-signed relative price in D4). The CPI-augmented variant (smallest pre-cut s.e.) is worse ({N.g5c:.2f}) and rejected. New fit: {N.fit[0]:.1f} + {N.fit[1]:.2f} Δln XPI + {N.fit[2]:.2f} Δln FX, adj. R² {N.r2a:.2f}; robustness *{N.verdict}* (Chow at the {N.chow['break_year']} mid-point, p = {N.chow['p']:.3f}) |
| 4. State Investment Programme 2026 | **Adopted**: {sp(N.sip)} mln AZN (own workbook, `DİP 2016-2026`, planned; 2025 actual {sp(N.sip25)}; the macro module cites the same cell) | Assumption. Its 2025 share of real state investment ({N.sipsh:.1f}%) is replaced in 2026 by the programme at the model's 2026 investment deflator (fixed point); 2026 real state investment {pm(N.ist26, 1)}% (pre-v2.2 {pm(N.ist26_21, 1)}%). Published as `fr1:exp_pubinv_n` (= {sp(N.sip)} in 2026 in every scenario) |
| 5. Fiscal closure: non-oil balance held at its cut-year ratio to non-oil GDP | **Rejected**; engine lever `fiscal_rule = nobd`; the ratio is published (`fr1:nobd_pct`) | Total spending improves (U {N.f_exp.U_rw:.2f} vs {N.f_exp.U_rw_pre:.2f}) but the budget balance, the purpose of the rule, is much worse: RMSE {N.f_bal.rmse:.1f} vs {N.f_bal.rmse_pre:.1f} pp of GDP (U {N.f_bal.U_rw:.2f} vs {N.f_bal.U_rw_pre:.2f}), because oil-revenue errors pass 1:1 into the balance. Under F3 Adverse keeps the best 2030 balance ({pm(N.bal30['Adverse'], 1)}% of GDP; Baseline {pm(N.bal30['Baseline'], 1)}, Reform {pm(N.bal30['Reform'], 1)}): spending follows revenue and Adverse cuts state investment 4% a year. With the lever, 2030 balances are {pm(N.lever['Baseline'], 1)} / {pm(N.lever['Adverse'], 1)} / {pm(N.lever['Reform'], 1)} bn AZN (Adverse worst) |
| 6. Imports on absorption + REER | **Rejected** | REER wrongly signed in both samples (≤ 2020 {pm(N.reer20[0])}, p = {N.reer20[1]:.2f}; full {pm(N.reer['coef'])}, p = {N.reer['p']:.2f}); imports U {N.d4.U_rw:.2f} / {N.d4.U_cg:.2f} vs {N.d4.U_rw_pre:.2f} / {N.d4.U_cg_pre:.2f}. D4 unchanged |
| 7. Sector deflators on sector price drivers | **Skipped** | The drivers (agricultural producer prices, transport and communication tariffs, construction deflator) have no exogenous 2026–30 paths: the macro module projects them with AR/average profiles (`pdrv_*`), and several exist only from 2021 |

**Effect on the forecast (Baseline, vs v2.1).** 2026 is unchanged in real terms (anchored on January–April); the changes come
from 2027: real GDP 2030 {pm(N.d30['rgdp'], 1)}% (oil-gas GDP {pm(N.d30['rgdpoil'], 1)}%), non-oil GDP {pm(N.d30['rgdpnon'], 1)}%, nominal GDP {pm(N.d30['gdp_n'], 1)}% (mining deflator), CPI 2030 {pm(N.d30['cpi'], 1)}%,
real disposable income {pm(N.d30['rhhdisp'], 1)}%. Average growth 2026–30: real GDP **{N.avg_g['Baseline']:.2f}%** (v2.1 {N.avg_g21:.2f}; Adverse {N.avg_g['Adverse']:.2f}, Reform {N.avg_g['Reform']:.2f}), non-oil **{N.avg_n['Baseline']:.2f}%**
({N.avg_n21:.2f}; {N.avg_n['Adverse']:.2f}, {N.avg_n['Reform']:.2f}). Scenario ordering of activity is unchanged (Adverse < Baseline < Reform). Budget balance 2030 {pm(N.bal30['Baseline'])}% of GDP
(Baseline), the 2026 balance is lower ({pm(N.bal26, 0)} vs {pm(N.bal26_21, 0)} mln AZN: the programme). Median hold-out U of the 14 variables of §6.2: {m.U_rw:.2f}
vs RW ({mp.U_rw:.2f} before), {m.U_cg:.2f} vs constant growth ({mp.U_cg:.2f}); median RMSE {m.rmse:.1f}% ({mp.rmse:.1f}%).

**Registry and engine.** `FR1_equations.json`: {N.neq} equations ({N.nused} used in the forecast): new — the four income legs
(E3a–E3d, estimated and registered, `used_in_forecast = false`, with their hold-out comparison), their CPI-deflated variants, the
pre-v2.2 and CPI-augmented mining deflators, D4 with absorption + REER; G5_defl_min replaced. Engine (`microlib/engines/fr1.py`,
`_fr1_*.py`): new inputs `sip_n` (programme, nominal) and `dsmf_add_g`; levers `income_block`, `fiscal_rule`; new series
`fr1:gdpnon_n`, `hhdisp_n`, `nobd_pct`, `exp_pubinv_n`, `gas_exp_price`, `xsh_oil`, `dln_xpi` ({N.ncat} catalogue components).
With `income_block = legs` a 10% higher minimum wage raises real disposable income by ~{N.mw[0]:.1f}% by 2030; in the forecast model
(E3) it does not ({pm(N.mw[1])}%, via prices). Self-test passes for all scenarios in both modes; FR3, FR4 and FR5 were re-run.
This note records the v2.2 stage (its forecast figures are those of the v2.2 run, as are the v2 and v2.1 notes' of theirs);
§6–§9 quote the current (v2.3) run."""


from ._fr1_note_az import note_az  # noqa: E402,F401
