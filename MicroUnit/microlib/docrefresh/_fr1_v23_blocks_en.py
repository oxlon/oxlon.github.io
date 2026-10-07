"""FR1 run-dependent passages that were hand-written until v2.3 (EN): §3.3 E3, §7.1 solver, §7.2 anchor, §7.5 fan, §9 item 17.
Figures: FR1_doc_figures.json (Part 18.17), FR1_forecast_full.csv, FR1_sector_decomposition_all.csv."""
from .common import pm

FANV = {"rgdp": "real GDP", "rgdpnon": "non-oil", "rcons": "consumption", "rhhdisp": "income", "rexp_cur": "current spending",
        "rev_tot_n": "revenue"}


def ict_dec(F):
    d = F.dec[(F.dec.scenario == "Baseline") & (F.dec.sector == "Information & communication")].set_index("year")
    return d.loc[2026, "add-factor change (anchor)"], d.loc[2027, "add-factor change (anchor)"], d.loc[2027, "K_ict_pc"]


def frac(x):
    """0.0625 -> '1/16'"""
    from fractions import Fraction
    q = Fraction(x).limit_denominator(1000)
    return f"{q.numerator}/{q.denominator}" if q.denominator <= 64 and abs(float(q) - x) < 1e-12 else f"{x:.3g}"


def sci(x):
    return f"{x:.0e}".replace("-", "−")


def share(x):
    return f"{x * 100:.1f}%"


def blocks_en(F):
    d = F.docfig; S, A, Fn = d["solver"], d["nowcast"], d["fan"]; e3 = d["v23"]["e3"]
    from ._fr1_v23_vals import code_cells_before_part18
    B = {"v23_cells": (f"Parts 1–17 = {code_cells_before_part18()} code cells", True)}
    B["v23_e3"] = (f"""- **Household income (E3)** — a share relation (v2.3: with the real wage bill): ln(income / pension bill) on ln(non-oil GDP /
  pension bill) and ln(wage bill / pension bill), elasticities {e3['cf_full']['ln_gdpnon']:.2f} on non-oil GDP, {e3['cf_full']['ln_wagebill_r']:.2f} on the real wage bill (average
  wage × employment / consumer prices; the 2025 wage share of household income is {e3['wage_share_2025']:.2f}) and {e3['cf_full']['ln_pens_r']:.2f} on the pension bill
  (homogeneity imposed: not rejected on data ≤ 2020, p = {e3['homog_p_cut']:.2f}; rejected on the full sample, p = {e3['homog_p_full']:.3f}, where the free form
  has a wrongly signed non-oil GDP term). Non-oil GDP stands for the remaining market income (entrepreneurial and property
  income); the wage bill carries the wage and minimum-wage channel. The pension bill is a **proxy**: average pension × total
  population (the workbook has no count of pensioners). Pensions are a policy variable, CPI-indexed in the forecast.""", False)
    db = d["v23"]["debt"]; y5 = db[str(F.LAST)]; y0 = db["2020"]; y4 = db["2024"]; old = d["v23"]["debt_old_2025"]
    t = lambda v, k: f"{v:,.{k}f}".replace(",", " ")
    B["v23_debt"] = (f"""5. **Public debt (v2.3.2)** — the workbook total ('Ümumi dövlət borcu', `Fiskal sektor` row 22, labelled mln USD) is on three
   bases: 2010–2020 in mln AZN (2020: {t(y0['total (row 22)'], 1)} = external {t(y0['external, mln USD'], 1)} mln USD × {y0['FX end-year']:.4f} + domestic
   {t(y0['domestic, mln AZN'], 1)} mln AZN), 2021–2024 in mln USD (2024: {t(y4['total (row 22)'], 1)}), and {F.LAST} the unconverted sum {t(y5['total (row 22)'], 1)} =
   {t(y5['external, mln USD'], 1)} (USD) + {t(y5['domestic, mln AZN'], 1)} (AZN). Converting the whole row at the exchange rate gave {t(old, 0)} mln AZN for {F.LAST}
   and mis-scaled 2010–2020 by the exchange rate (×{float(F.A.loc[2010, 'fx']):.2f} in 2010, ×{y0['FX end-year']:.2f} in 2020). Public debt is now external (row 24) × end-year exchange rate + domestic (row 23) in every
   year — the Ministry of Finance concept, without state-guaranteed debt: **{t(y5['external x FX + domestic (mln AZN)'], 1)} mln AZN in {F.LAST}
   ({d['v23']['debt_gdp_2025']:.1f}% of GDP)**. The three bases are asserted in the notebook.""", False)
    g4 = d["v23"]["deval"]; cf4, p4 = g4["g4_cf"], g4["g4_p"]
    if "dln_fx_L1" in cf4:
        B["v23_g4"] = (f"""- **Inflation** — a structural cost markup (v2.3.4): the exchange-rate change in the current year ({cf4['dln_fx']:.3f}, p = {p4['dln_fx']:.2f}) and
  the previous year ({cf4['dln_fx_L1']:.3f}, p = {p4['dln_fx_L1']:.3f}; a lag of the regressor, no lagged inflation) and wage growth ({cf4['dln_wage']:.3f}, p = {p4['dln_wage']:.2f});
  R² {g4['g4_r2']:.2f}. Cumulative exchange-rate pass-through {cf4['dln_fx'] + cf4['dln_fx_L1']:.2f} (2015–17 history: {g4['hist_passthrough_2015_17']:.2f}); the import-price
  forms were dropped because the two import-price sources contradict each other in 2021–25 (v2.3.4 note).""", False)
    else:
        B["v23_g4"] = (f"""- **Inflation** — a structural cost markup (v2.3.3): manat import-price inflation (USD import prices + exchange rate) in the
  current year ({cf4['dln_pm_azn']:.3f}, p = {p4['dln_pm_azn']:.3f}) and the previous year ({cf4['dln_pm_azn_L1']:.3f}, p = {p4['dln_pm_azn_L1']:.2f}; a lag of the regressor, no lagged
  inflation) and wage growth ({cf4['dln_wage']:.3f}, p = {p4['dln_wage']:.2f}); R² {g4['g4_r2']:.2f}. Cumulative exchange-rate pass-through {cf4['dln_pm_azn'] + cf4['dln_pm_azn_L1']:.2f} (2015–17
  history: {g4['hist_passthrough_2015_17']:.2f}). USD import prices are a base assumption (0% a year, input `pm_usd_infl`).""", False)
    B["v23_solver"] = (f"{S['forecast_iter'][0]}–{S['forecast_iter'][1]} iterations per forecast year,\n"
                       f"{S['holdout_iter'][0]}–{S['holdout_iter'][1]} in the hold-out", True)
    li = A["largest_increment"]; beat = A["choice"] != "1:1 mapping"
    B["v23_anchor"] = (f"""2026 is four months observed. All twelve GDP components have published year-to-date real growth indices. A robust (Huber)
proportional bridge from January–April to full-year growth, estimated on 2022–2025 (2021 excluded: its January–April growth is a
2020 base effect), has slope {A['bridge_slope']:.2f} and a cross-validated RMSE of {A['bridge_cv_rmse']:.1f} pp against {A['one2one_cv_rmse']:.1f} pp for the 1:1 mapping, but it does
{'' if beat else '**not** '}beat 1:1 on an HLN-corrected Diebold–Mariano test (one-sided p = {A['bridge_dm_p']:.3f}), so the **{A['choice']}** is used. Each
component's implied full-year level is an anchoring target reached through add-factor increments; **the increments apply fully in
2026 and decay by half each year** ({frac(A['anchor_remaining_2030'])} remains in 2030). The largest is {li['label']} ({pm(li['value'], 3)} log points, from
{pm(li['ytd_growth'], 0)}% January–April growth).""", False)
    ga = F.g("rva_agr")
    B["v23_agr"] = (f"{pm(ga[2026], 1)}% → {pm(ga[2027], 1)}%", True)
    a26, a27, k27 = ict_dec(F)
    B["v23_ict"] = (f"its January–April anchor adds {a26:.1f} pp in 2026 and takes back {abs(a27):.1f} pp in 2027, and per-capita ICT "
                    f"capital no longer grows at the 2025 investment share ({pm(k27, 1)} pp in 2027", True)
    rows = "\n".join(f"| {'Real GDP growth' if t['variable'] == 'real GDP' else 'Real non-oil GDP growth'} | {pm(t['published_ytd'])}% | "
                     f"{pm(t['model_2026'])}% | {pm(t['diff_pp'])} pp |" for t in A["table"])
    B["v23_jantable"] = ("| | Published Jan–Apr | Model 2026 (full year) | Difference |\n|---|---|---|---|\n" + rows, False)
    fl = Fn["fail"]; sg = Fn["share_gt03"]; mg = Fn["medgap_raw_2030"]
    gaps = ", ".join(f"{pm(mg[k], 1)}% ({v})" for k, v in FANV.items())
    B["v23_fan"] = (f"""{Fn['nsim']} baseline replications combine: (1) **historical residual-path resampling** — a start year s ({Fn['start_years'][0]}–{Fn['start_years'][1]}) is drawn and the joint
deviations u_{{s+h}} − u_s (h = 1…5) of all {Fn['n_resid']} behavioural residuals are added to the constant add-factors; nothing is estimated on
the residual dynamics; paths are centred and used with both signs (antithetic); (2) the same five-year history for log Brent, oil
and gas output, **with the same start year**; (3) antithetic, sign-preserving parameter draws from N(β̂, V̂_HAC) ({share(Fn['param_rej_share'])} of coefficient
draws rejected for a sign flip), with base add-factors recomputed to reproduce 2025. 2026 deviations are scaled by {Fn['nowcast_scale']:.2f} (the
remaining full-year uncertainty once January–April is known) and {frac(Fn['exo_scale'])} for the exogenous drivers.

**Diagnostics.** {Fn['attempts']} replications were attempted ({Fn['pairs']} antithetic pairs) to obtain {Fn['valid']} valid ({share(Fn['valid_share'])}). Discarded:
{fl.get('year-on-year jump above ceiling', 0)} for a one-year move more than {Fn['jump_max']:.1f} log points away from the baseline's (or 1.5× the largest move the variable
made in 2000–2025, where larger — e.g. tourism, state investment, oil-linked prices), {fl.get('non-finite', 0)} non-finite, {fl.get('explosive (>50% from baseline)', 0)} explosive,
{fl.get('non-convergence', 0)} for non-convergence (a failed member discards its antithetic pair). The screen therefore truncates the tails somewhat. In
the exported draws the share of draw-years with |Δlog| > 0.3 is {sg['rgdp']:.1f}% for real GDP, {sg['rgdpnon']:.1f}% for non-oil GDP, {sg['cpi']:.1f}% for CPI,
{sg['emp']:.1f}% for employment, {sg['rcons']:.1f}% for consumption, {sg['rexp_cur']:.1f}% for real current spending and {sg['rinv_non']:.0f}% for non-oil investment (whose own
history has larger moves).

**Centring.** Shocks and parameter deviations are symmetric, but aggregates are arithmetic sums of log-normally shocked parts
(chain-linked GDP, oil + non-oil revenue, the income loop), so the raw median lies above the baseline: by 2030 {gaps}. The exported draws are then centred on the baseline (multiplicatively for levels, additively for
rates): the median equals the published baseline in every year (max gap {sci(Fn['medgap_after_max'])}), dispersion unchanged; cross-variable
identities hold only up to those shifts.""", False)
    B["v23_lim17"] = (f"""17. **Fans** are wide for CPI, consumption and current spending, are truncated by the jump screen ({share(Fn['jump_fail_share'])} of attempted
    replications rejected, {share(Fn['replaced_share'])} replaced with their antithetic pairs), carry a mirrored deflationary CPI tail, and are centred on the
    baseline after a reported median correction.""", False)
    return B
