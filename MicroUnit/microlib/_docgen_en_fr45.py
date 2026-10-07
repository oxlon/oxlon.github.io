"""English wording of the v2 blocks of docs/FR4_Methodology.md (§15, AUTO:v2) and docs/FR5_Methodology.md (AUTO:v2).

Called from the documentation cells of FR4.ipynb (Part 26.1) and FR5.ipynb (Part 19.11) with the notebook's namespace:

    LV2_AZ = LV2;  LV2 = _docgen_en_fr45.fr4_v2(globals())     # FR4: list of lines
    _v2_az = _v2;  _v2 = _docgen_en_fr45.fr5_v2(globals())     # FR5: one text

The Azerbaijani wording stays in the notebook cell and goes to docs/az (microlib/docgen_az.py: fr4_v2 / write_v2);
both are built from the same objects, so the numbers are identical. Nothing here changes a model output.
"""
import pandas as pd

from . import docgen_en as DE


def _labels(ns, module):
    from . import project_root
    import os
    return pd.read_csv(os.path.join(project_root(), "output", f"{module}_indicator_catalog.csv")).set_index("id").label_en


def fr4_v2(ns):
    g = ns.get
    RBS, U, frag, t, TOP3 = g("RBS"), g("_u"), g("_frag"), g("_t"), g("TOP3")
    blk = g("_blk")
    fp9, WB9, WB9o, ST4, tt = g("fp9"), g("WB9"), g("WB9o"), g("ST4"), g("_tt")
    FC = g("FC_YEARS")
    lab = _labels(ns, "FR4")
    G8_EN = {k: str(lab.get(f"fr4:emp:grp:{k}", k)).replace(" (employed population)", "") for k in TOP3}
    return [
        "## 15. v2 — equation registry, complete forecast table, scenario engine and robustness", "",
        "*This section is rewritten on every run by Parts 21–26 of FR4.ipynb.*", "",
        f"**Equation registry** (`output/FR4_equations.json`, Part 21): every equation estimated in the notebook — "
        f"**{len(RBS)}** in total, of which **{len(U)}** are used in the forecast. By block: "
        + ", ".join(f"{k} {int(v)}" for k, v in sorted(blk.items())) + " (R — rejected/alternative specifications, "
        "A — aggregate block, B — tier-1 share system, C — within industry and services, D — institutional splits, E — shift-share). "
        "The registry re-estimates every equation independently with statsmodels on the same (y, X) and checks that the "
        "coefficients equal the notebook's own estimates (all match); diagnostics (DW, BG, JB, White, RESET, VIF, "
        "cointegration, difference form), recursive and leave-one-year-out estimates, Chow and CUSUM are added.", "",
        f"**Robustness verdicts** (`FR4_robustness_summary.csv`): all equations — {DE.counts(g('_vc'))}; used in the forecast — "
        f"{DE.counts(g('_vu'))}. Fragile (unstable) forecast equations: "
        + "; ".join(f"`{r.equation}` ({DE.tests(r.failed_tests_az)})" for r in frag.itertuples()) + ". "
        f"Of the {g('_neg')} level equations with a cointegration test, cointegration is established at 10% in only {g('_nci')} — "
        "the t-statistics are mostly descriptive (consistent with Part 19.4). In the R9 industry panel the wage elasticity is "
        f"{fp9.beta[1]:+.3f}: Driscoll–Kraay p = {fp9.pval[1]:.3f}, wild-cluster bootstrap (by year, Webb) p = {WB9['p_wild']:.3f}; "
        f"the output elasticity's bootstrap p-value is {WB9o['p_wild']:.3f} (DK: {fp9.pval[0]:.3f}).", "",
        f"**Complete forecast table** (`FR4_forecast_tidy.csv`): {g('TIDY').id.nunique()} components × {len(g('SCEN'))} scenarios, "
        f"history from the first available year, {g('LAST_ACT')} (nowcast) and {FC[0]}–{FC[-1]}; completeness is checked "
        f"({len(g('CATDF')) * len(g('SCEN')) * len(FC)} values). The 8 groups and the two service blocs are now given for all three "
        "scenarios (before, the groups were only in the Baseline fan table). "
        f"Bands (5–95%) for {len(g('BANDS'))} series in the Baseline. Not forecast, with the reasons: "
        f"`FR4_not_forecast.csv` ({len(g('NFDF'))} series: the broken Employment Agency series, the split by activity of the tax "
        "register, DVX r130/r107, regions). Catalogue: `FR4_indicator_catalog.csv` (ids `fr4:emp:<activity>`, `fr4:hired:<activity>`, "
        "`fr4:<base>:grp:<group>`, `fr4:<base>:bloc:pub|mkt`, `fr4:state`, `fr4:budget`, `fr4:oil:stat|tax`, `fr4:lf`, `fr4:phi` etc.).", "",
        f"**Scenario engine** (`microlib/engines/fr4.py`, state `output/engine/FR4_state.json`): reproduces the notebook's solution "
        f"in Parts 15–17. Editable inputs: {len(g('_ex'))} exogenous FR1 paths (`fr1:emp`, `fr1:lf`, `fr1:pop`, `fr1:rgdpnon`, "
        f"`fr1:rgdpoil`, 11 `fr1:rva_*`), {len(g('_co'))} coefficients (the pooled βs, the pooling weights, E6, E8, E9) and "
        f"{len(g('_lv'))} levers (population growth, hired share, state share trend/frozen, σ/κ, add-factor decay). With "
        '`upstream={"FR1": ...}` the FR1 engine\'s paths are used; FR3 is not used in the forecast. Self-test: in every scenario '
        f"the notebook CSVs are reproduced with a maximum relative difference of {ST4['max_rel_diff']:.1e}, and so is the lever "
        f"table of Part 18 ({ST4['levers']['n_checked']} values); one scenario ~{max(tt.values()) * 1000:.0f} ms.", "",
        f"**Coefficient sensitivity** (`FR4_coef_sensitivity.csv`, ±1 standard error, {FC[-1]}, Baseline): state employment — "
        f"`{t.loc['fr4:state', 'coefficient']}` gives {t.loc['fr4:state', 'effect_minus_pct']:+.2f}% / {t.loc['fr4:state', 'effect_plus_pct']:+.2f}%; "
        f"budget organisations — `{t.loc['fr4:budget', 'coefficient']}` gives {t.loc['fr4:budget', 'effect_minus_pct']:+.2f}% / "
        f"{t.loc['fr4:budget', 'effect_plus_pct']:+.2f}%; the three largest groups (" + ", ".join(G8_EN[k] for k in TOP3)
        + ") are most sensitive to the pooling weight (±0.25, as the weight has no SE) — " + ", ".join(
            f"{G8_EN[k]} ±{t.loc[f'fr4:emp:grp:{k}', 'swing_pct'] / 2:.2f}%" for k in TOP3)
        + ". Total employment comes from FR1 and does not depend on FR4's coefficients.", "",
        "New files: `FR4_equations.json`, `FR4_indicator_catalog.csv`, `FR4_forecast_tidy.csv`, `FR4_not_forecast.csv`, "
        "`FR4_robustness_summary.csv`, `FR4_coef_sensitivity.csv`, `FR4_strings_az.csv` (the Azerbaijani equivalent of every "
        f"user-visible English string, {len(g('STRDF'))} strings), `engine/FR4_state.json` (plain data only). Every CSV from "
        "before v2 is unchanged (regression check).", ""]


def fr5_v2(ns):
    g = ns.get
    U5, ROB5, ci5, st5, tor5, TOP3 = g("_u5"), g("ROB5"), g("_ci5"), g("_st5"), g("_tor5"), g("TOP3")
    lab = _labels(ns, "FR5")
    vc = lambda d: ", ".join(f"{DE.verdict(k)} {v}" for k, v in d.value_counts().items())
    typ = lambda k: str(lab.get(f"fr5:vol:{k}", k)).split(":")[0]
    e1 = DE.tests(U5[U5.equation == "FR5.E1_income_relprice"].failed_tests_az.iloc[0])
    return (
        f"**Equation registry** (`output/FR5_equations.json`): {len(g('REGX'))} equations, of which {int(g('REG_TAB5').used.sum())} are used in the "
        f"forecast — E1 (income + relative price, {g('EQ_A').estimator}, η = {g('ETA'):.3f}, ε = {g('EPS_MODEL'):+.3f}), the 12 shrunk Engel slopes\n"
        f"of the forecast system (κ = {g('_KCH'):g}, selection windows ≤2019) and two constant institutional shares. Also registered: the Tier 1\n"
        "candidates (income only, deflated income, income + trend, trend only, growth form) and E1's difference form, the static alternatives\n"
        "of Part 9, the level (DOLS) and difference forms of the 12 share equations, the price-augmented MNL, LA-AIDS (SUR, homogeneity +\n"
        "symmetry), the split candidates (income, trend). Every OLS/DOLS equation is re-estimated with statsmodels and checked against the\n"
        f"notebook's estimates (mismatches: 0). Robustness verdicts (all equations): {vc(ROB5.verdict)}; used in the forecast: {vc(U5.verdict)}\n"
        f"(recursive tests do not apply to the shrunk slopes and the constant shares; E1: {e1}).\n\n"
        "**Scenario engine** (`microlib/engines/fr5.py`, `_fr5_core.py`; state `output/engine/FR5_state.json` + `.npz`): Part 14's `solve()`\n"
        f"function is ported. Inputs: {sum('fr1_column' in e for e in ci5['exogenous'])} FR1 paths (`fr1:rhhdisp`, `fr1:p_cons`, `fr1:p_serv_hh`,\n"
        f"`fr1:pop`) and relative-price paths for the 13 types, {sum(c['editable'] for c in ci5['coefficients'])} editable coefficients (η, ε and the 12 shrunk\n"
        f"Engel slopes; SE and 95% interval from the registry), {len(ci5['levers'])} levers (type price rule, choice of η, relative price of services,\n"
        f"population growth, add-factor decay). `selftest()`: the CSV outputs are reproduced in all {len(st5['detail'])} scenarios (max. relative\n"
        f"difference {st5['max_rel_diff']:.1e}); the levers reproduce the Part 17 lever table exactly. One scenario < 0.1 s.\n\n"
        f"**Complete forecast table** (`FR5_forecast_tidy.csv`, `FR5_indicator_catalog.csv`): {len(g('CATDF5'))} components (total volume and\n"
        "value, volume per head, deflator and growth rates, volume, value, share, deflator and growth of the 13 types, shares and values of\n"
        f"the two splits) × {len(g('SCEN'))} scenarios × 2026–2030, all filled, with history; 5–95% bands for {sum(r['has_band'] for r in g('CAT5'))}\n"
        "components (Baseline). `FR5_not_forecast.csv`: regional series (they do not reconcile with the national series, Part 13).\n\n"
        "**Coefficient sensitivity** (`FR5_coef_sensitivity.csv`, ±1 SE, 2030, Baseline; headline: total volume and value, the three largest\n"
        f"types by 2030 value — {', '.join(typ(k) for k in TOP3)}): largest effects — " + "; ".join(
            f"{lab.get(r.component_id, r.component_id)}: {r.eq_id}|{r.coefficient} ({r.effect_minus_se_pct:+.2f}% / {r.effect_plus_se_pct:+.2f}%)"
            for r in tor5.itertuples())
        + f". Strings: `FR5_strings_az.csv` ({len(g('STR5'))} English strings → Azerbaijani). Kernel: `miis-model` (Python 3.13).")
