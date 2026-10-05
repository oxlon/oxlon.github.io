"""FR1 v2.3 passages, English (docs/FR1_Methodology.md): the v2.3 note and the formerly hand-written run-dependent text."""
from .common import pm
from ._fr1_v23_vals import FISC, SCEN, gfmt, v23_vals
from ._fr1_v23_blocks_en import blocks_en


def _fisc_rows(N):
    out = []
    for k in FISC:
        r = N.dec(k)
        out.append(f"| {r.name} | {pm(r.bal_2030_Baseline)} / {pm(r.bal_2030_Adverse)} / {pm(r.bal_2030_Reform)} | "
                   f"{'yes' if r.balance_order_ok else 'no'} | {r.U_rw:.2f} ({pm(r.U_loss_pct, 0)}%) | rejected |")
    return "\n".join(out)


def note_en(F):
    N = v23_vals(F); e3, d4 = N.e3, N.d4; g, n = N.af_dec["g"], N.af_dec["n"]
    du, dn, ew = N.dec("D4u"), N.dec("D4n"), N.dec("E3w")
    mb, ma, ml = N.mw["v2.2 E3"], N.mw["v2.3 E3"], N.mw["income legs (lever)"]
    fis, b22, ref = N.fis, N.ref22("bal_gdp"), N.ref22
    rev = fis["oil revenue"].difference + fis["non-oil revenue"].difference
    exp = fis["current spending"].difference + fis["capital spending"].difference + fis["debt service"].difference
    el3, el4 = N.el["F3"], N.el["F4"]
    return f"""## v2.3 (2026-10-05): final FR1 clean-up — fixed add-factor decay, import price term, wage bill in income, fiscal ordering

Four specification questions, each estimated on data ≤ 2020 by the model's own builders and tested in the untouched dynamic
2021–2025 hold-out against the v2.2 specification (new notebook Part 11.7, `FR1_v23_candidates.csv`); the scenario consequences
and the decisions are in Part 14.1 (`FR1_v23_forecast_checks.csv`, `FR1_v23_fiscal_diagnosis.csv`, `FR1_v23_decisions.csv`).
Rule: correct (or neutral) signs on both samples, Theil U of the key variable at most 10% above the v2.2 specification, for E3 a
coherent wage elasticity, and for the fiscal candidates the ordering Adverse < Baseline < Reform of the 2030 budget balance.
Rejected candidates are registered with `used_in_forecast = false`.

| Item | Decision | Evidence |
|---|---|---|
| 1. Add-factor decay sensitivity | **Changed.** Until v2.2 the lever `base_addf_decay` decayed the base add-factors at each equation's *estimated* residual autocorrelation ρ̂ — an estimated residual-AR process, excluded by the client's constraints. Now a fixed, non-estimated half-life: lever `addf_halflife` (default {gfmt(N.hl)} year, factor {N.decay:.2f} a year — the rule of the January–April anchor increments); ρ̂ is no longer estimated anywhere in the forecast path (DW and BG remain as diagnostic tests) | The forecast (constant add-factors) is unchanged by this item. `FR1_addfactor_sensitivity.csv`, average growth 2026–30 with the decay: real GDP {g['Baseline']:.2f} / {g['Adverse']:.2f} / {g['Reform']:.2f}% (Baseline / Adverse / Reform; constant add-factors {N.af_const['g']['Baseline']:.2f}%), non-oil {n['Baseline']:.2f} / {n['Adverse']:.2f} / {n['Reform']:.2f}% ({N.af_const['n']['Baseline']:.2f}%); with ρ̂ (v2.2 run) real GDP {N.af_rho['rgdp']['Baseline']:.2f}%, non-oil {N.af_rho['rgdpnon']['Baseline']:.2f}% |
| 2. D4 non-oil imports: relative price ln(p_gdp/fx), coefficient {pm(d4['cf_relprice'], 3)} | **Re-parametrised (adopted).** Real imports are USD imports × exchange rate / GDP deflator (Part 3), so ln(p_gdp/fx) enters the dependent variable with −1 by construction. Estimated in import-volume terms (constant USD prices), the same fit gives the volume elasticity **c = {pm(d4['c_full'], 3)}** (p = {d4['p_full']:.4f}; ≤ 2020: {pm(d4['c_cut'], 3)}) — correctly signed: a real appreciation raises import volumes. The solver keeps c − 1 for real imports at GDP prices, so forecasts and hold-out are identical. Dropping the term (= bounding it at 0, which binds) is rejected | Imports U {du.U_rw:.2f} / {du.U_cg:.2f} (identical to v2.2). Without the term: imports {dn.U_rw:.2f} / {dn.U_cg:.2f} ({pm(dn.U_loss_pct, 0)}%, material), non-oil revenue U {N.c('D4n', 'rrev_nonoil').U_rw:.2f} vs {ref('rrev_nonoil').U_rw:.2f}, budget balance {N.c('D4n', 'bal_gdp').U_rw:.2f} vs {b22.U_rw:.2f}. In first differences the volume elasticity is {pm(d4['diff_rm'][0] + 1)} [{pm(d4['diff_rm'][1] + 1)}, {pm(d4['diff_rm'][2] + 1)}], so the long-run value lies outside that interval — as for the v2.2 form (reported) |
| 3. E3 household income: + real wage bill | **Adopted.** ln(income / pension bill) on ln(non-oil GDP / pension bill) and ln(wage bill / pension bill), homogeneity imposed: elasticities non-oil GDP {e3['cf_full']['ln_gdpnon']:.3f}, **real wage bill {e3['cf_full']['ln_wagebill_r']:.3f}** (the 2025 wage share of household income is {e3['wage_share_2025']:.3f}), pension bill {e3['cf_full']['ln_pens_r']:.3f}; ≤ 2020: {e3['cf_cut']['ln_gdpnon']:.3f}, {e3['cf_cut']['ln_wagebill_r']:.3f}, {e3['cf_cut']['ln_pens_r']:.3f}. Homogeneity is not rejected on the selection sample (p = {e3['homog_p_cut']:.2f}) but is on the full sample (p = {e3['homog_p_full']:.3f}), where the free form has a wrongly signed non-oil GDP elasticity ({pm(e3['free_gdpnon'])}) — so the test-and-impose variant is rejected. Wage elasticity coherent (first differences {e3['diff_wb'][0]:.2f} [{pm(e3['diff_wb'][1])}, {pm(e3['diff_wb'][2])}]) | Hold-out real disposable income U {ew.U_rw:.2f} / {ew.U_cg:.2f} vs {ew.U_rw_v22:.2f} / {ew.U_cg_v22:.2f} ({pm(ew.U_loss_pct, 1)}%, below 10%); consumption U {N.c('E3w', 'rcons').U_rw:.2f} vs {ref('rcons').U_rw:.2f}. **Minimum wage +10%** (Baseline 2030, shock convention): real disposable income {pm(mb['rhhdisp'])}% → **{pm(ma['rhhdisp'])}%**, consumption {pm(mb['rcons'])}% → {pm(ma['rcons'])}%, non-oil GDP {pm(mb['rgdpnon'])}% → {pm(ma['rgdpnon'])}% (wage {pm(ma['wage'])}%, CPI {pm(ma['cpi'])}%; income-legs lever {pm(ml['rhhdisp'])}%) |
| 4. Fiscal block: Adverse ends with the best budget balance | **Kept — no candidate passes.** Diagnosis, Adverse vs Baseline 2030: revenue {pm(rev/1000, 1)} bn AZN (oil {pm(fis['oil revenue'].difference/1000, 1)}, non-oil {pm(fis['non-oil revenue'].difference/1000, 1)}), spending {pm(exp/1000, 1)} bn (current {pm(fis['current spending'].difference/1000, 1)}, capital {pm(fis['capital spending'].difference/1000, 1)}): **{N.cut_per_azn:.2f} AZN of spending is cut per AZN of revenue lost**. Two links do it: F3 (current spending on total real revenue, elasticity {el3.Baseline:.2f}, 95% CI [{el3.difference:.2f}, {el3.pct:.2f}]) and the scenarios' state-investment paths (Adverse −4% a year: real state investment {pm(N.oil_vs_inv.Adverse, 1)}% vs real oil revenue {pm(N.oil_vs_inv.difference, 1)}%; F4 unit elasticity, free estimate {el4.Adverse:.2f} [{el4.difference:.2f}, {el4.pct:.2f}]). With the Baseline state-investment level Adverse would end at {pm(N.adv_istate.Adverse)}% of GDP | Every structural fix that restores the ordering loses heavily on the hold-out balance (U {b22.U_rw:.2f} in v2.2, RMSE {b22.rmse:.1f} pp of GDP) — table below. The ordering is therefore a property of the estimated fiscal reaction (spending follows revenue, capital spending follows oil revenue), not a coding error; it is disclosed rather than tuned away |

| Fiscal candidate (in the v2.2 model, as in the hold-out) | 2030 balance, % of GDP (Baseline / Adverse / Reform) | Adverse < Baseline < Reform | Hold-out U of the balance (change) | Decision |
|---|---|---|---|---|
{_fisc_rows(N)}

**Effect on the forecast (Baseline 2030, vs the v2.2 run)** — all from the E3 wage-bill term (items 1 and 2 leave the forecast
unchanged): real GDP {pm(N.d30['rgdp'], 2)}%, non-oil GDP {pm(N.d30['rgdpnon'], 2)}%, nominal GDP {pm(N.d30['gdp_n'], 2)}%, CPI {pm(N.d30['cpi'], 2)}%, real disposable income
{pm(N.d30['rhhdisp'], 2)}%, consumption {pm(N.d30['rcons'], 2)}%, non-oil imports {pm(N.d30['rm_non'], 2)}%: the real wage bill grows more slowly than non-oil GDP in the forecast. Average growth
2026–30: real GDP **{N.avg['g']['Baseline']:.2f}%** (v2.2 {N.avg22['g']['Baseline']:.2f}; Adverse {N.avg['g']['Adverse']:.2f}, Reform {N.avg['g']['Reform']:.2f}), non-oil **{N.avg['n']['Baseline']:.2f}%** ({N.avg22['n']['Baseline']:.2f}; {N.avg['n']['Adverse']:.2f}, {N.avg['n']['Reform']:.2f}). Budget balance
2030: Baseline {pm(N.bal['Baseline'])}, Adverse {pm(N.bal['Adverse'])}, Reform {pm(N.bal['Reform'])}% of GDP (v2.2 {pm(N.bal22['Baseline'])} / {pm(N.bal22['Adverse'])} / {pm(N.bal22['Reform'])}). Median hold-out U of the 14 variables
of §6.2: {N.med.U_rw:.3f} vs RW ({N.med22.U_rw:.3f} in v2.2), {N.med.U_cg:.3f} vs constant growth ({N.med22.U_cg:.3f}).

**Registry, engine, documentation.** `FR1_equations.json`: {N.neq} equations ({N.nused} used in the forecast; {N.neq22} in v2.2), new: {N.nrej}
v2.3 specifications (the replaced v2.2 forms of D4 and E3 and the rejected candidates), each with its hold-out comparison and
decision row. Engine: lever `addf_halflife`; the E3 homogeneity tie now has three members (pension-bill elasticity = 1 − non-oil
GDP − wage bill), so a changed coefficient keeps the restriction; self-test passes for every scenario in both modes. The
run-dependent figures that no CSV holds (solver iterations §7.1, the January–April anchor §7.2, the fan diagnostics §7.5, the
v2.2 comparison figures) are exported to `FR1_doc_figures.json` (Part 18.17) and rendered here by `microlib.docrefresh`.
FR3, FR4 and FR5 were re-run on the v2.3 forecast. §6–§9 quote the v2.3 run."""


def v23_en(F):
    B = {"v23_note": (note_en(F), False)}
    B.update(blocks_en(F))
    return B
