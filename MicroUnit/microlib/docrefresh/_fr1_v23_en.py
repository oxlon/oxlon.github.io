"""FR1 v2.3 passages, English (docs/FR1_Methodology.md): the v2.3 note and the formerly hand-written run-dependent text."""
from .common import pm
from ._fr1_v23_vals import FISC, SCEN, gfmt, mult_fix, v23_vals
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
FR3, FR4 and FR5 were re-run on the v2.3 forecast. §6–§9 quote the v2.3 run.

{_mfix_en(F)}

{_dfix_en(F)}

{_g4fix_en(F)}"""


def _mfix_en(F):
    from .fr1 import EXP
    m = mult_fix(F); p = lambda e: ", ".join(pm(v, 0) for v in m["path"][e].tolist())
    old = ", ".join(f"{v:+,.0f}".replace(",", " ").replace("-", "−") for v in m["old"])
    return f"""**v2.3.1 fix (2026-10-06): budget-balance multipliers.** `FR1_multipliers.csv` reported the budget balance as a % deviation
from a Baseline balance that crosses zero ({pm(m['b28'], 0)} mln AZN in 2028), so the responses exploded and changed sign (state
investment +1 bn AZN: {old} "%" in 2026–30; +{f"{m['old22']:,.0f}".replace(",", " ")}% in 2028 in v2.2). The model itself was not wrong: every shocked solve
converged (largest residual {m['conv']:.0e}) and the responses in money are smooth. The balance column is now the difference in
mln AZN at current prices (inflation stays in pp, the other columns in %): state investment +1 bn AZN {p(EXP[1])}; Brent
+10 USD/bbl {p(EXP[0])}; external demand +10% {p(EXP[4])}. The real and price responses and the forecast are unchanged. The
notebook now asserts that every shocked run converged and that balance_n, rgdpnon and infl keep one sign from year 2 on.""".replace("e-", "e−")


def v23_en(F):
    B = {"v23_note": (note_en(F), False)}
    B.update(blocks_en(F))
    return B


def _dfix_en(F):
    pre = F.ref["v23"]["pre_debt_fix"]; d = F.docfig["v23"]; y5 = d["debt"][str(F.LAST)]
    t = lambda v, k=1: f"{v:,.{k}f}".replace(",", " ")
    cur = {s: (F.fc[s].loc[2030, "debt_azn"] / F.fc[s].loc[2030, "gdp_n"] * 100, F.fc[s].loc[2030, "balance_n"] / F.fc[s].loc[2030, "gdp_n"] * 100)
           for s in SCEN}
    ds = F.base.loc[2026, "debt_serv_n"]
    return f"""**v2.3.2 fix (2026-10-06): public debt.** `debt_azn` converted the workbook's total public debt at the exchange rate, but that
row is on three bases (§2.3, item 5): {F.LAST} was {t(d['debt_old_2025'], 0)} mln AZN instead of **{t(y5['external x FX + domestic (mln AZN)'])} mln AZN** (external
{t(y5['external, mln USD'])} mln USD × {y5['FX end-year']:.2f} + domestic {t(y5['domestic, mln AZN'])} mln AZN; {d['debt_gdp_2025']:.1f}% of GDP), and 2010–2020 were mis-scaled by the exchange
rate. Public debt is now external × end-year rate + domestic in every year — the Ministry of Finance concept (state-guaranteed
debt is not included and not in the workbook); `fr1:debt_azn` is labelled accordingly. The calibrated debt-service rate (2023–25
average of debt service / debt) and the debt identity use the corrected stock: 2026 debt service {t(ds, 0)} mln AZN (was
{t(pre['Baseline']['debt_serv_2026'], 0)}); 2030 public debt {cur['Baseline'][0]:.1f} / {cur['Adverse'][0]:.1f} / {cur['Reform'][0]:.1f}% of GDP (Baseline / Adverse / Reform; was
{pre['Baseline']['debt_gdp_2030']:.1f} / {pre['Adverse']['debt_gdp_2030']:.1f} / {pre['Reform']['debt_gdp_2030']:.1f}); budget balance 2030 {pm(cur['Baseline'][1])} / {pm(cur['Adverse'][1])} / {pm(cur['Reform'][1])}% (was {pm(pre['Baseline']['bal_gdp_2030'])} / {pm(pre['Adverse']['bal_gdp_2030'])} / {pm(pre['Reform']['bal_gdp_2030'])})."""


def _g4fix_en(F):
    g = F.docfig["v23"]["deval"]; e, n4 = g["engine"], g["engine_no_f4"]; v0 = F.ref["v23"]["pre_g4_deval"]
    dec = F.dec23[F.dec23.group == "G4"].set_index("spec")
    rows = "; ".join(f"{r.variant.split(': ', 1)[1]} {r.U_rw:.2f} ({pm(r.U_loss_pct, 0)}%)" for _, r in dec.iterrows())
    infl27 = {s: F.fc[s].loc[[2027, 2028, 2029, 2030], "infl"].mean() for s in SCEN}
    cn = g["cpi_nowcast"]; w = F.base["wage"]; cn_w26 = (w.loc[2026] / F.A.loc[F.LAST, "wage"] - 1) * 100
    return f"""**v2.3.3 (2026-10-06): exchange-rate pass-through.** G4 had a pass-through of 0.06 (a +16.5% devaluation: CPI {pm(v0['infl_2026'])} pp in
year 1, {pm(v0['infl_2027'])} pp in year 2, and non-oil GDP *rising* {pm(v0['rgdpnon_2030'])}% by 2030), against ≈{g['hist_passthrough_2015_17']:.2f} in 2015–17. Candidates (Part 11.7, lags of
regressors only, no lagged inflation), hold-out U of inflation vs RW (v2.2 form {dec.U_rw_v22.iloc[0]:.2f}): {rows}. **Adopted: manat import-price inflation, current +
previous year** (largest gain; signs right; the post-2015 regime interaction is not better). Devaluation +16.5% now: CPI **{pm(e['infl'][2026])} pp
in year 1, {pm(e['infl'][2027])} pp in year 2** (CPI level {pm(e['cpi'][2030], 1)}% by 2030), non-oil GDP {pm(e['rgdpnon'][2026])}% in 2026 and {pm(e['rgdpnon'][2030])}% in 2030, real disposable
income {pm(e['rhhdisp'][2030])}%, consumption {pm(e['rcons'][2030])}%, public debt {pm(e['debt_gdp'][2030])} pp of GDP. Why non-oil GDP rose before: with almost no pass-through real
incomes barely fell, while manat oil revenue ({pm(e['rev_oil_n'][2030], 1)}%) raises current spending (F3) and state investment (F4, {pm(e['rinv_state'][2030], 1)}%); the real-income
channel (real wage bill in E3, CPI-indexed pensions) was present but too weak. Without the F4 response non-oil GDP would fall
{pm(n4['rgdpnon'][2030])}%. **2026 CPI anchor and the Baseline.** 2026 inflation is anchored on the latest monthly CPI, as the real sectors are on
January–April: {cn['source'].split(' (md5')[0].split('/')[-1]} gives {cn['yoy_latest']:.1f}% y/y in month {int(cn['month'])} of {int(cn['year'])}; the remaining months repeat last year's month-on-month
changes (1:1; on 2021–25 this bridge has an RMSE of {cn['bridge_rmse_pp']:.1f} pp), so December {int(cn['year'])} = {cn['infl_2026']:.1f}%. G4's add-factor is set so that Baseline {int(cn['year'])}
inflation equals the nowcast (2025 residual {pm(g['infl_addf_2025'], 2)} pp + anchor shift {pm(g['cpi_shift'], 2)} pp) and is held from 2027; the nowcast refreshes when a new
monthly file arrives in `data/dsk_cpi/` or a RiskUnit DSK vintage. The model's own 2026 value was already close to the nowcast, so the
anchor changes little: Baseline CPI inflation 2027–30 averages {infl27['Baseline']:.1f}% (Adverse {infl27['Adverse']:.1f}, Reform {infl27['Reform']:.1f}) — wage growth
recovers from its January–April-anchored {cn_w26:.1f}% in 2026 to about 8%, and the add-factor is not a one-off (the 2023–24 residuals are of the same size, with
USD import prices falling in the macro-module series). The import-price path is an editable assumption (`pm_usd_infl`)."""


def _g4fix_en(F):                    # v2.3.4: supersedes the v2.3.3 version above (history + data check + CPI anchor)
    from ._fr1_v234 import g4_en
    from ._fr1_v235 import v235_en
    return g4_en(F) + "\n\n" + v235_en(F) + "\n\n" + __import__('microlib.docrefresh._fr1_v236', fromlist=['x']).v236_en(F)
