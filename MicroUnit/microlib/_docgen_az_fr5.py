"""FR5 Azerbaijani AUTO blocks (docs/az/FR5_Metodologiya.md), rendered from the same CSV outputs as the English
documentation step (FR5.ipynb Part 18, last cell before v2). Part 1: decision tables, Tier 1/Tier 2 blocks."""
from types import SimpleNamespace

import pandas as pd

from .docgen_az import num, translator, md_table, ordsuf

HEAD = {"specification": "spesifikasiya", "selection RMSE %": "seçim RMSE, %", "DM/HLN p vs best": "DM/HLN p (ən yaxşıya qarşı)",
        "level η": "səviyyə η", "difference η": "fərq η", "selection RMSE pp": "seçim RMSE, f.b.",
        "service": "xidmət", "type": "növ", "label": "ad", "lever": "rıçaq", "estimate": "qiymətləndirmə",
        "forecast avg 2026–30 %": "proqnoz ortası 2026–30, %", "max forecast year %": "proqnozun maks. ili, %",
        "2010–19 %": "2010–19, %", "2021–25 %": "2021–25, %", "best 5-yr avg %": "ən yaxşı 5 illik orta, %",
        "window": "pəncərə", "exceeds best 5-yr": "ən yaxşı 5 illiyi aşır",
        "value vs baseline %": "dəyər, Əsas ssenariyə nisbətən %", "volume vs baseline %": "həcm, Əsas ssenariyə nisbətən %"}
SCEN = {"Baseline": "Əsas", "Adverse": "Mənfi", "Reform": "İslahat"}


def ctx(ns):
    n = SimpleNamespace(**{k: v for k, v in ns.items() if not k.startswith("__")})
    n.rd = lambda name, **kw: pd.read_csv(n.OUT / f"FR5_{name}.csv", **kw)
    n.tr = translator("FR5", HEAD)
    fix = lambda s: str(s).replace("contemporaneous dx", "eyni dövrün Δx-i")  # noqa: E731
    n.trx = lambda s: fix(n.tr(s))
    return n


def g(x):
    """'{:g}' in prose: 512.0 -> '512', 0.5 -> '0,5'."""
    return f"{float(x):g}".replace(".", ",")


def part1(n):
    tr, G = n.tr, {}
    t1 = n.rd("aggregate_specification_selection", index_col=0)
    G["t1table"] = md_table(t1[["slopes", "RMSE_pct", "DM_p_vs_best", "level_slope", "difference_slope", "coherent", "decision"]]
                            .rename(columns={"RMSE_pct": "selection RMSE %", "DM_p_vs_best": "DM/HLN p vs best",
                                             "level_slope": "level η", "difference_slope": "difference η"}),
                            fmt={"slopes": "{:.0f}", "DM/HLN p vs best": "{:.3f}"}, tr=tr)
    e1 = n.rd("e1_coefficients", index_col=0)
    er = n.rd("income_elasticity_range", index_col=0)
    e = e1.iloc[0]
    dlo, dhi = e["diff_lo"], e["diff_hi"]
    inside = dlo <= e1.iloc[1]["coef"] <= dhi
    isd = er.index.str.contains("difference")
    G["e1"] = (f"**Seçilmiş spesifikasiya: {n.trx(e['spec'])}.** {n.trx(e['estimator'])} ilə {e['sample']} nümunəsində "
               f"qiymətləndirilib (sərbəstlik dərəcəsi {int(e['df'])}): "
               + ", ".join(f"{k} {num(e1.loc[k, 'coef'], 3, True)} (s.x. {num(e1.loc[k, 'se'], 3)})"
                           for k in e1.index if k != "const")
               + f". **eg_coint_p = {num(e['eg_coint_p'], 2)}** — "
               + ("kointeqrasiya yoxdur; t-statistikaları təsviridir." if e["eg_coint_p"] > 0.10
                  else "kointeqrasiya 10% səviyyəsində təsdiqlənir.")
               + f" Fərq forması: η = {num(e['diff_eta'], 2)} (95% etibarlılıq intervalı {num(dlo, 2)}–{num(dhi, 2)}); "
               + ("səviyyə qiyməti bu intervalın **daxilindədir** (uyğundur)." if inside
                  else "səviyyə qiyməti bu intervaldan **kənardadır**.")
               + f" 2025-ci il düzəliş əmsalı {num(e['addf_2025'], 3, True)}; qalığın ρ̂ əmsalı {num(e['resid_rho'], 2)} "
               "(yalnız həssaslıq üçün).\n\n"
               + md_table(er[["eta", "se", "eg_coint_p", "df", "p_eta_eq_1"]].rename(columns={"p_eta_eq_1": "p(η = 1)"}),
                          fmt={"eta": "{:.3f}", "se": "{:.3f}", "eg_coint_p": "{:.2f}", "df": "{:.0f}", "p(η = 1)": "{:.3f}"},
                          tr=n.trx)
               + f"\n\nη {num(er.eta.min(), 2)}–{num(er.eta.max(), 2)} intervalında dəyişir; fərq forması qiymətləri "
               f"{num(er.eta[isd].min(), 2)}–{num(er.eta[isd].max(), 2)} arasındadır və "
               + ("onların heç biri 5% səviyyəsində η = 1 fərziyyəsini rədd etmir."
                  if (er.p_eta_eq_1[isd] > 0.05).all() else "onlardan bəziləri 5% səviyyəsində η = 1 fərziyyəsini rədd edir."))
    t2 = n.rd("demand_system_specification_selection", index_col=0)
    G["t2table"] = md_table(t2[["RMSE_pp", "DM_p_vs_best", "slopes", "non_inferior", "coherent", "decision"]]
                            .rename(columns={"RMSE_pp": "selection RMSE pp", "DM_p_vs_best": "DM/HLN p vs best"}),
                            fmt={"DM/HLN p vs best": "{:.3f}", "slopes": "{:.0f}"}, tr=tr)
    if (n.OUT / "FR5_engel_shrinkage_selection.csv").exists():
        ks = n.rd("engel_shrinkage_selection", index_col=0)
        kbest = ks.index[ks.RMSE_pp.values.argmin()].split("= ")[1].split(" ")[0]
        G["shrink"] = (md_table(ks[["RMSE_pp", "DM_p_vs_best", "non_inferior", "decision"]].rename(
                           columns={"RMSE_pp": "selection RMSE pp", "DM_p_vs_best": "DM/HLN p vs best"}),
                           fmt={"DM/HLN p vs best": "{:.3f}"}, tr=tr)
                       + f"\n\nSeçilmiş: **{tr(ks.index[ks.decision == 'CHOSEN'][0])}** — ən yaxşıdan statistik əhəmiyyətli "
                       f"dərəcədə pis olmayan ən güclü büzülmə (ən kiçik RMSE: κ = {g(kbest)}); tam büzülmə (sabit paylar) "
                       f"daha pisdir (p = {num(ks.loc['constant shares', 'DM_p_vs_best'], 3)}).")
    rk = n.rd("type_ranking_level_vs_difference_elasticities", index_col=0)
    name = lambda c: tr(rk.label.get(c, c)) if c in rk.index else tr(c)  # noqa: E731
    lv = n.rd("engel_level_vs_difference", index_col=0)
    out = lv.index[lv.outside_diff_CI].tolist()
    G["coh"] = (f"{len(lv)} səviyyə Engel meylindən kointeqrasiya olunanların sayı: {int((lv.eg_coint_p <= 0.10).sum())}; "
                f"**{len(out)} meyl eyni tənliyin fərq formasındakı 95% etibarlılıq intervalından kənardadır** "
                f"({', '.join(name(c) for c in out)}); bunlar üçün fərq forması meyli, qalanları "
                f"({', '.join(name(c) for c in lv.index[~lv.outside_diff_CI])}) üçün isə DOLS səviyyə meyli istifadə olunur. "
                + " ".join(f"{name(k)}: səviyyə {num(lv.loc[k, 'level_beta'], 2, True)}, fərq {num(lv.loc[k, 'diff_beta'], 2, True)} "
                           f"[{num(lv.loc[k, 'diff_ci_lo'], 2)}; {num(lv.loc[k, 'diff_ci_hi'], 2)}]."
                           for k in ["medical", "culture"] if k in lv.index))
    pv = n.rd("nonselected_pandemic_dummy_variants", index_col=0)
    G["pandemic"] = md_table(pv[[c for c in pv.columns if "level" in c or "RMSE" in c]], tr=tr)
    el = n.rd("expenditure_elasticities", index_col=0)
    _el = pd.DataFrame({"xidmət": [tr(x) for x in rk.label],
                        "e_i (proqnoz sistemi)": el.loc[rk.index, "expenditure_elasticity_at_2025_shares"].values,
                        "5%": el.loc[rk.index, "p05_2025"].values, "95%": el.loc[rk.index, "p95_2025"].values,
                        "sıra": rk["rank, forecasting system"].values, "sıra, hamısı səviyyə": rk["rank, all level"].values,
                        "sıra, hamısı fərq forması": rk["rank, all difference form"].values})
    G["elast"] = md_table(_el, fmt={"sıra": "{:.0f}", "sıra, hamısı səviyyə": "{:.0f}", "sıra, hamısı fərq forması": "{:.0f}"},
                          index=False, tr=tr)
    return G, e1, t2


def yr(y):
    return f"{y}-{ordsuf(y)}"
