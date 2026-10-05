"""fr10_data.py — FR10 (enterprises: finance, efficiency, market position), Layer A numbers and figures."""
from . import core, figs
from .common import YEARS, SCEN


def load():
    d = {}
    bh = core.csv("FR10_branch_history.csv", dtype={"unit": str})
    br = bh[(bh.series == "output_nominal_mn_AZN") & bh.unit.str.isdigit()].copy()
    br["sec"] = br.unit.astype(int).map(lambda n: "B" if n <= 9 else "C" if n <= 33 else "D" if n == 35 else "E")
    d["sec_hist"] = br.pivot_table(index="year", columns="sec", values="value", aggfunc="sum").loc[2005:]
    fs = core.csv("FR10_forecast_sections.csv")
    d["sec_fc"] = {s: fs[fs.scenario == s].pivot(index="year", columns="sec", values="output") for s in SCEN}
    fan = core.csv("FR10_fan_charts.csv", dtype={"unit": str})
    fan = fan[fan.year.astype(str).str.fullmatch(r"\d{4}")].copy()
    fan["year"] = fan.year.astype(int)
    d["fan"] = fan
    d["conc"] = core.csv("FR10_concentration.csv", index_col=0)
    d["sc"] = core.csv("FR10_scenario_summary.csv").set_index("scenario")
    d["ew"] = core.csv("FR10_early_warning.csv", dtype={"nace2": str})
    d["hold"] = core.csv("FR10_holdout_validation.csv")
    d["plaus"] = core.csv("FR10_plausibility.csv")
    d["ident"] = core.csv("FR10_identity_checks.csv")
    d["man"] = core.csv("FR10_dsk_manifest.csv")
    d["mat"] = core.csv("FR10_data_source_matrix.csv")
    d["find"] = core.csv("FR10_data_integrity_findings.csv")
    d["gaps"] = core.csv("FR10_data_gaps_and_alternatives.csv")
    d["pool"] = core.csv("FR10_pooled_related_sector_model.csv").iloc[0]
    d["pipe"] = core.csv("FR10_SYNTHETIC_pipeline_tests.csv")
    d["swap"] = core.csv("FR10_firm_panel_swap_tests.csv")
    d["val"] = core.csv("FR10_firm_panel_validation_report.csv")
    return d


def fan_of(d, ind, unit):
    f = d["fan"]
    return f[(f.indicator == ind) & (f.unit == unit)].set_index("year")


def industry_fig(d):
    h = d["sec_hist"].sum(axis=1)
    fn = fan_of(d, "industry output, mn AZN", "Industry")
    data = figs.band(fn.index, fn.p5, fn.p95)
    data.append(figs.line(h.index, h.values, "Faktiki (DSK)", hfmt=",.0f"))
    b = d["sec_fc"]["Baseline"].sum(axis=1)
    data.append(figs.line([2025] + YEARS, [h.loc[2025]] + list(b.loc[YEARS]), "Əsas ssenari (proqnoz)",
                          mode="lines+markers", hfmt=",.0f"))
    data += figs.scen_lines(YEARS, {s: list(d["sec_fc"][s].sum(axis=1).loc[YEARS]) for s in ("Adverse", "Reform")},
                            hfmt=",.0f")
    return figs.spec(data, figs.layout("mln AZN, cari qiymətlərlə"))


def sections_fig(d):
    h = d["sec_hist"]
    data = []
    for code, en, col in (("B", "Mining", figs.GREY), ("C", "Manufacturing", figs.ACCENT)):
        fn = fan_of(d, "section output, mn AZN", en)
        lab = "Mədənçıxarma" if code == "B" else "Emal sənayesi"
        data += figs.band(fn.index, fn.p5, fn.p95, name=f"5–95 % zolağı: {lab.lower()}")
        b = d["sec_fc"]["Baseline"][code]
        data.append(figs.line(list(h.index) + YEARS, list(h[code]) + list(b.loc[YEARS]), lab, col, "solid", 2.6,
                              hfmt=",.0f"))
    return figs.spec(data, figs.layout("mln AZN, cari qiymətlərlə"))


def hhi_fig(d):
    c = d["conc"]
    hist = c["HHI manufacturing branches"].loc[:2025].dropna()
    fn = fan_of(d, "HHI across manufacturing branches", "Manufacturing")
    data = figs.band(fn.index, fn.p5, fn.p95)
    data.append(figs.line(hist.index, hist.values, "Faktiki", hfmt=",.0f"))
    base = c["HHI manufacturing branches, Baseline"].loc[YEARS]
    data.append(figs.line([2025] + YEARS, [hist.loc[2025]] + list(base), "Əsas ssenari (proqnoz)",
                          mode="lines+markers", hfmt=",.0f"))
    data += figs.scen_lines(YEARS, {s: list(c[f"HHI manufacturing branches, {s}"].loc[YEARS]) for s in ("Adverse", "Reform")},
                            hfmt=",.0f")
    return figs.spec(data, figs.layout("HHI (0–10 000)"))


def headline(d):
    b = d["sec_fc"]["Baseline"].sum(axis=1)
    fn = fan_of(d, "industry output, mn AZN", "Industry")
    return [("Sənaye məhsulu, nominal", "mln AZN", list(b.loc[YEARS]), (fn.loc[2030, "p5"], fn.loc[2030, "p95"]), 0, "FR10")]
