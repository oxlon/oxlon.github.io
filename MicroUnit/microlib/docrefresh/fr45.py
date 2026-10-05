"""FR4 and FR5 — v2.2 notes (macro-module data and competitors) and the FR4 σ passages, EN + AZ; v2.3 notes on the
fixed-half-life add-factor decay (_fr45_v23.py).

FR4 reads FR4_e8_structural_candidates.csv, FR4_budget_sigma_history.csv, FR4_institutional_breakdown.csv and
FR4_equations.json; FR5 reads FR5_macro_module_competition.csv, FR5_share_change_check.csv,
FR5_engel_shrinkage_selection.csv and FR5_equations.json.  The v2.1 σ (0.913) and the v2.1 2030 budget employment
are frozen in v22_reference.json.

FR4 markers are named AUTO:fr4v22_<name>: FR4.ipynb rewrites its English AUTO:v2 block with the pattern
`<!-- AUTO:v2[^>]*-->`, which would also match `<!-- AUTO:v22_... -->` and swallow everything up to /AUTO:v2.
"""
import re

import pandas as pd

from .common import DOCS, Doc, az, csv, ref, registry, run
from ._fr45_v23 import fr4_v23, fr5_v23

azn = az
FR4_NB_TAGS = ("e2gap", "results", "cells", "v2")       # tags FR4.ipynb rewrites with its prefix pattern


def _row(d, s, y):
    return d[(d.iloc[:, 0] == s) & (d.iloc[:, 1] == y)].iloc[0]


def fr4_texts():
    R4 = ref('FR4')['v21']
    C8 = csv('FR4_e8_structural_candidates.csv', index_col=0); SG = csv('FR4_budget_sigma_history.csv', index_col=0)
    IB = csv('FR4_institutional_breakdown.csv')
    b25, b30 = _row(IB, 'Baseline', 2025)['budget organisations'], _row(IB, 'Baseline', 2030)['budget organisations']
    o30 = R4['budget_org_2030_baseline']
    s30 = _row(IB, 'Baseline', 2030)['state']
    E4, _ = registry('FR4'); bs = E4['FR4.B_sigma']['holdout']
    tr = C8.loc['trend (E8, used)']
    rows = '\n'.join(f"| {i} | {r.pooled_OOS_RMSE_pct:.2f} | {r.DM_p_vs_null:.3f} | {r.holdout_U_vs_random_walk:.2f} | {r.holdout_U_vs_constant_growth:.2f} | "
                     f"{'' if pd.isna(r.coef) else f'{r.coef:+.3f} (t {r.t:+.1f}); diff {r.difference_coef:+.3f} (t {r.difference_t:+.1f})'} | {r.decision} |"
                     for i, r in C8.iterrows())
    rows_az = '\n'.join(f"| {r.specification_az} | {azn(r.pooled_OOS_RMSE_pct)} | {azn(r.DM_p_vs_null, 3) if pd.notna(r.DM_p_vs_null) else '—'} | "
                        f"{azn(r.holdout_U_vs_random_walk)} | {azn(r.holdout_U_vs_constant_growth)} | {r.decision_az} |" for i, r in C8.iterrows())
    EN4 = f"""## 17. v2.2 (2026-10-05) — data from the Ministry's macro module

**State employment (E8).** Structural alternatives without a trend or own lags, scored like E8 (origins 2011–2014 scored ≤ 2019;
hold-out 2020–2024 × the simulated total): real government final consumption per head (MOE SNA `GC`, 1995–2024, from
`data/macro_module/fr345_moe_spec_panel.csv`), its ratio to real non-oil GDP, real non-oil GDP per head, and a composition model
(activity state shares from DSK `Dynamics_2.12` held at the origin × the activity hired forecast). File `FR4_e8_structural_candidates.csv`.

| specification | selection RMSE % | DM p vs trend | hold-out U (RW) | U (CG) | level / difference coefficient | decision |
|---|---|---|---|---|---|---|
{rows}

**None beats the trend** (U {tr.holdout_U_vs_random_walk:.2f} / {tr.holdout_U_vs_constant_growth:.2f}); the fiscal and output drivers are negative in levels (the share falls as
they rise — both trend) and insignificant in differences, and the composition model misses the privatisation inside activities
(state shares fell in 17 of 19 activities 2005–2024). E8 stays the logistic trend presented as a policy lever; the three
regressions are registered as `FR4.E8_alt_G1–G3` (rejected).

**Budget organisations (σ).** `data/dsk/002_12-13en.xls` already holds `Dynamics_2.12` (2005–2024); FR4 had read only the 2023 and
2024 sheets. σ is now observed every year ({SG.sigma.iloc[0]:.4f} in 2005, {SG.sigma.loc[2019]:.4f} in 2019, {SG.sigma.loc[2024]:.4f} in 2024; `FR4_budget_sigma_history.csv`), so the
2005–2022 budget history is no longer imputed (1999–2004 dropped: no σ). On origins 2010–2019 holding the last published year beats
the two-year mean (budget-employment RMSE {bs['rmse']:.2f}% vs {bs['rmse_other_rule']:.2f}%), which is also the anchoring rule of the other
modules: **σ = {SG.sigma.loc[2024]:.4f}** (was {R4['sigma']:.3f}). Baseline budget employment {b25:,.1f} thousand in 2025 (DVX r130: 588.0) and
{b30:,.1f} in 2030 (was {o30:,.1f}, {(b30/o30-1)*100:+.2f}%); state employment unchanged ({s30:,.1f} thousand in 2030).

**Sector employment.** The 19 activities already run 1999–2024 (DSK 2.1 / 2.8); the macro module's `L_*` series and DSK 2.12 add
no longer history, so the sector equations are unchanged."""
    AZ4 = f"""## 17. v2.2 (2026-10-05) — Nazirliyin makro modulunun məlumatları

**Dövlət sektorunda məşğulluq (E8).** Trendsiz və öz gecikmələri olmayan struktur alternativlər E8 kimi yoxlanılıb (2011–2014
başlanğıcları, ≤2019; 2020–2024 yoxlaması × simulyasiya edilmiş cəm): adambaşına real dövlət istehlakı (MOE SNA `GC`, 1995–2024,
`data/macro_module/fr345_moe_spec_panel.csv`), onun real qeyri-neft ÜDM-ə nisbəti, adambaşına real qeyri-neft ÜDM və tərkib modeli
(DSK `Dynamics_2.12` üzrə fəaliyyətlərin dövlət payları). Fayl: `FR4_e8_structural_candidates.csv`.

| spesifikasiya | seçim RMSE, % | DM p (trendə qarşı) | yoxlama U (TG) | U (SA) | qərar |
|---|---|---|---|---|---|
{rows_az}

**Heç biri trendi üstələmir**; fiskal və buraxılış sürücüləri səviyyədə mənfi işarəlidir və fərq formasında əhəmiyyətsizdir, tərkib
modeli isə fəaliyyətlər daxilində özəlləşdirməni tutmur. E8 siyasət rıçağı kimi logistik trend olaraq qalır; üç reqressiya
`FR4.E8_alt_G1–G3` kimi reyestrdədir (rədd edilib).

**Büdcə təşkilatları (σ).** `Dynamics_2.12` vərəqi (2005–2024) σ-nı hər il üçün verir ({azn(SG.sigma.iloc[0], 4)} — 2005, {azn(SG.sigma.loc[2024], 4)} — 2024);
2005–2022 tarixi artıq doldurulmuş deyil. 2010–2019 başlanğıclarında son dərc olunmuş il iki ilin ortasından dəqiqdir (RMSE
{azn(bs['rmse'])}% və {azn(bs['rmse_other_rule'])}%): **σ = {azn(SG.sigma.loc[2024], 4)}** (əvvəl {az(R4['sigma'], 3)}). Əsas ssenaridə büdcə məşğulluğu 2030-da {azn(b30, 1)} min
(əvvəl {azn(o30, 1)}, {azn((b30/o30-1)*100)}%); dövlət məşğulluğu dəyişmir.

**Sahə məşğulluğu.** 19 fəaliyyət artıq 1999–2024-ü əhatə edir; makro modul daha uzun tarix vermir, tənliklər dəyişmir."""

    sig = SG.sigma.loc[2024]; s0 = R4['sigma']
    en = dict(
        fr4v22_sigma1=f"{sig:.4f} (v2.2: the 2024 value; {s0:.3f} before)",
        fr4v22_sigma2=(f"0.9169\n(2023) and 0.9092 (2024). **v2.2:** `Dynamics_2.12` gives every year since 2005 and holding the last published\n"
                       f"year beats the two-year mean on origins 2010–2019, so σ = **{sig:.4f}** (2024; was the mean {s0:.3f})."),
        fr4v22_r130=f"{b25:,.1f}\nthousand for 2025 against r130's 588.0 ({(b25/588-1)*100:+.1f}%; 596.7 with the old mean)",
        fr4v22_history="History\n2005–2022 uses the observed σ (v2.2); before 2005 there is no property split, so no budget history.")
    azd = dict(
        fr4v22_sigma1=f"{azn(sig, 4)} (v2.2: 2024 dəyəri; əvvəl {azn(s0, 3)})",
        fr4v22_sigma2=(f"0,9169\n(2023) və 0,9092 (2024). **v2.2:** `Dynamics_2.12` 2005-ci ildən hər ili verir; son dərc olunmuş il 2010–2019\n"
                       f"başlanğıclarında iki ilin ortasından dəqiqdir, buna görə σ = **{azn(sig, 4)}** (əvvəl orta {azn(s0, 3)})."),
        fr4v22_r130=f"üçün\nr130-un 588,0 min göstəricisinə qarşı {azn(b25, 1)} min verir ({azn((b25/588-1)*100, 1)}%; köhnə orta ilə 596,7)",
        fr4v22_history="2005–2022-ci illər üçün\nmüşahidə olunan σ istifadə olunur (v2.2); 2005-dən əvvəl mülkiyyət bölgüsü yoxdur.")
    return EN4, AZ4, en, azd


def fr4():
    EN4, AZ4, en, azd = fr4_texts()
    V23 = fr4_v23()                          # v2.3: fixed-half-life add-factor decay (AUTO:fr4v23_note)
    LEG = ('<!-- AUTO:v22 -->', '<!-- /AUTO:v22 -->')

    def filler(note, inl, wild, v23):
        def fill(d):
            d.put('fr4v22_note', note, legacy=LEG)
            d.put('fr4v23_note', v23)
            for tag, body in inl.items():
                d.put(tag, body, inline=True)
            if wild:
                d.check_wildcard(FR4_NB_TAGS)
        return fill
    run('FR4', [(Doc(DOCS / 'FR4_Methodology.md'), filler(EN4, en, True, V23[0])),
                (Doc(DOCS / 'az' / 'FR4_Metodologiya.md'), filler(AZ4, azd, False, V23[1]))])


def fr5_texts():
    M5 = csv('FR5_macro_module_competition.csv', index_col=0); SH = csv('FR5_share_change_check.csv', index_col=0)
    KS = csv('FR5_engel_shrinkage_selection.csv', index_col=0)
    kap = float(re.search(r"kappa = ([0-9.]+)", KS.index[KS.decision == 'CHOSEN'][0]).group(1))
    KAPPA = f"{kap:g}"
    imax = SH.change_pp.abs().idxmax()
    MAXNAME = {'household': 'household services'}.get(imax, str(SH.loc[imax, 'label']).lower())
    ref_ = M5.iloc[-2]; pro = M5.iloc[-1]
    r5 = '\n'.join(f"| {i} | {'' if pd.isna(r.selection_RMSE_pct) else f'{r.selection_RMSE_pct:.2f}'} | {'' if pd.isna(r.DM_p_vs_selected) else f'{r.DM_p_vs_selected:.3f}'} | "
                   f"{r.test_RMSE_pct:.2f} | {r.U_vs_random_walk:.2f} | {r.U_vs_constant_growth:.2f} | {r.final_year_err_pct:+.1f} | {r.decision} |" for i, r in M5.iterrows())
    E5, _ = registry('FR5'); m1 = {c['name']: c for c in E5['FR5.M1_cons_growth']['coefficients']}
    ref = ref_
    EN5 = f"""## v2.2 (2026-10-05): competitors from the Ministry's macro module

The macro module explains real paid-services growth by real final-consumption growth (its U ≈ 0.60), and the Ministry's own workbook
(`MOE SOCIAL.xlsx` eq8, copied to `data/macro_module/fr345_ministry_equations_catalog.csv`) uses Δln paid services = −0.0055 +
1.07 Δln trade + 0.38 Δln wage. Both forms (growth forms, no lagged dependent variable) and the Ministry's published coefficients
were scored with E1's own rules: pre-cut origins 2011–2017 (scored ≤ 2019) and the untouched 2020–2025 window (2020–21 excluded).
`FR5_macro_module_competition.csv`:

| specification | selection RMSE % | DM p vs E1 | test RMSE % | U (RW) | U (CG) | 2025 error % | decision |
|---|---|---|---|---|---|---|---|
{r5}

**Nothing is adopted.** The consumption form (elasticity {m1['ln_cons_pc']['coef']:.2f}, se {m1['ln_cons_pc']['se']:.2f}) beats the hold-out *procedure* result quoted
before (U {pro.U_vs_random_walk:.2f}) only marginally and loses to E1 itself re-estimated to 2019 (U {ref.U_vs_random_walk:.2f} / {ref.U_vs_constant_growth:.2f}); it is far worse on the
pre-cut origins and ends 2025 {M5.iloc[0].final_year_err_pct:+.0f}% off; the Ministry form is worse still (with its published coefficients, which use the
test years, U {M5.iloc[2].U_vs_random_walk:.2f}). Registered as `FR5.M1_cons_growth`, `FR5.M2_ministry_reest`, `FR5.M3_ministry_fixed` (rejected).

**Share models — no-change behaviour.** With κ = {KAPPA} shrinkage and 2025 anchoring the shares are close to a no-change path: 2025→2030
the median type share moves {SH.change_pp.abs().median():.2f} pp (max {SH.change_pp.abs().max():.2f} pp, {MAXNAME}), {int((SH.change_pp.abs() < 0.1).sum())} of {len(SH)} types move < 0.1 pp, and
the 2020–2025 hold-out U vs the random walk is 1.00 for {int((SH.holdout_U_vs_rw.round(2) == 1).sum())} types (`FR5_share_change_check.csv`). This is the selected
outcome of the pre-cut κ search, not an own-history model: the type paths are driven by the aggregate and the type prices."""
    AZ5 = f"""## v2.2 (2026-10-05): Nazirliyin makro modulundan rəqib tənliklər

Makro modulda pullu xidmətlərin real artımı son istehlakın real artımı ilə izah olunur (U ≈ 0,60), Nazirliyin öz iş kitabında isə
(`MOE SOCIAL.xlsx` eq8) Δln pullu xidmətlər = −0,0055 + 1,07 Δln ticarət + 0,38 Δln əmək haqqı. Hər iki forma (artım forması,
gecikmiş asılı dəyişənsiz) və Nazirliyin dərc olunmuş əmsalları E1-in öz qaydaları ilə qiymətləndirilib (≤2019 başlanğıclar və
toxunulmamış 2020–2025 pəncərəsi). Nəticə (`FR5_macro_module_competition.csv`): istehlak forması yoxlamada U {azn(M5.iloc[0].U_vs_random_walk)} / {azn(M5.iloc[0].U_vs_constant_growth)},
2019-a qədər yenidən qiymətləndirilmiş E1 isə {azn(ref.U_vs_random_walk)} / {azn(ref.U_vs_constant_growth)}; Nazirliyin forması {azn(M5.iloc[1].U_vs_random_walk)} (yenidən qiymətləndirilmiş) və {azn(M5.iloc[2].U_vs_random_walk)}
(dərc olunmuş əmsallarla). **Heç biri qəbul edilmir**; hamısı ≤2019 başlanğıclarda E1-dən əhəmiyyətli dərəcədə pisdir. Reyestrdə:
`FR5.M1_cons_growth`, `FR5.M2_ministry_reest`, `FR5.M3_ministry_fixed` (rədd edilib).

**Pay modelləri — dəyişməzlik davranışı.** κ = {KAPPA} büzülmə və 2025 lövbəri ilə paylar dəyişməz yola yaxındır: 2025→2030 median
dəyişmə {azn(SH.change_pp.abs().median())} f.b. (ən çox {azn(SH.change_pp.abs().max())} f.b.), {len(SH)} növdən {int((SH.change_pp.abs() < 0.1).sum())}-si 0,1 f.b.-dən az dəyişir, yoxlamada U (təsadüfi gəzişmə) {int((SH.holdout_U_vs_rw.round(2) == 1).sum())} növ üçün
1,00-dır (`FR5_share_change_check.csv`). Bu, ≤2019 κ seçiminin nəticəsidir, öz keçmişinə əsaslanan model deyil."""

    return EN5, AZ5


def fr5():
    EN5, AZ5 = fr5_texts()
    LEG = ('<!-- AUTO:v22 -->', '<!-- /AUTO:v22 -->')
    V23 = fr5_v23()                          # v2.3: fixed-half-life add-factor decay (AUTO:v23_note)

    def fill(body, v23):
        def f(d):
            d.put('v22_note', body, legacy=LEG)
            d.put('v23_note', v23)
        return f
    run('FR5', [(Doc(DOCS / 'FR5_Methodology.md'), fill(EN5, V23[0])),
                (Doc(DOCS / 'az' / 'FR5_Metodologiya.md'), fill(AZ5, V23[1]))])
