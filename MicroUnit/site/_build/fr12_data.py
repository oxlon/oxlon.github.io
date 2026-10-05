"""fr12_data.py — FR12 (competition environment) Layer-A numbers and figures."""
from . import core, figs
from .common import YEARS, SCEN
from .labels import GROUP_AZ


def load():
    d = {}
    g = core.csv("FR12_indicators_groups.csv")
    d["groups"] = g
    agg = g.groupby("year")[["registered", "new", "dereg"]].sum()
    agg["entry"] = agg.new / agg.registered * 100
    agg["exit"] = agg.dereg / agg.registered * 100
    d["hist"] = agg
    fan = core.csv("FR12_fan_entry_exit.csv")
    d["fan"] = fan
    d["fall"] = fan[(fan.panel == "activity") & (fan.unit == "ALL")].set_index("year")
    fc = core.csv("FR12_forecast_entry_exit.csv")
    d["fc"] = fc
    d["fc_all"] = {s: fc[(fc.panel == "activity") & (fc.unit == "ALL") & (fc.scenario == s)].set_index("year") for s in SCEN}
    d["hold"] = core.csv("FR12_holdout_validation.csv")
    d["sel"] = core.csv("FR12_selection_summary.csv")
    d["scen"] = core.csv("FR12_scenario_summary.csv")
    d["sass"] = core.csv("FR12_scenario_assumptions.csv")
    d["merger"] = core.csv("FR12_merger_screen.csv")
    d["ew"] = core.csv("FR12_early_warning.csv")
    d["fl"] = core.csv("FR12_early_warning_false_listing.csv")
    d["ident"] = core.csv("FR12_identity_checks.csv")
    d["man"] = core.csv("FR12_dsk_manifest.csv")
    d["mat"] = core.csv("FR12_data_source_matrix.csv")
    d["find"] = core.csv("FR12_data_integrity_findings.csv")
    d["gaps"] = core.csv("FR12_data_gaps_and_alternatives.csv")
    d["band"] = core.csv("FR12_band_meta.csv")
    d["bounds"] = core.csv("FR12_concentration_bounds.csv")
    d["cal"] = core.csv("FR12_SYNTHETIC_calibration_errors_summary.csv")
    d["pipe"] = core.csv("FR12_SYNTHETIC_pipeline_tests.csv")
    d["swap"] = core.csv("FR12_business_register_swap_tests.csv")
    d["val"] = core.csv("FR12_business_register_validation_report.csv")
    return d


def filled(i):
    """One series of FR12_series_filled.csv (observed + imputed points), indexed by year."""
    f = core.csv("FR12_series_filled.csv")
    f = f[(f.id == i) & f.value.notna()].set_index("year").sort_index()
    f["imputed"] = f.imputed.astype(bool)
    return f


def rate_fig(d, key, ytitle):
    """National (all activity groups) entry or exit rate: history, nowcast/forecast, band, scenarios."""
    h = d["hist"][key]
    h = h.reindex(range(int(h.index.min()), int(h.index.max()) + 1))
    f = d["fall"]
    yrs = list(f.index)
    data = figs.band(yrs, f[f"{key}_p5"], f[f"{key}_p95"])
    fl = filled(f"fr12:act:{key}:ALL")
    if len(fl):
        h = fl.value
        data += figs.imputed_series(fl.index, fl.value, fl.imputed, "Faktiki (DSK sahibkarlıq, 006)", hfmt=".2f")
    else:
        data.append(figs.line(h.index, h.values, "Faktiki (DSK sahibkarlıq, 006)", mode="lines+markers", hfmt=".2f"))
    b = d["fc_all"]["Baseline"]
    x = [int(h.index.max())] + yrs
    data.append(figs.line(x, [h.iloc[-1]] + list(b.loc[yrs, key]), "Əsas ssenari (2025 — cari qiymətləndirmə)",
                          mode="lines+markers", hfmt=".2f"))
    data += figs.scen_lines(yrs, {s: list(d["fc_all"][s].loc[yrs, key]) for s in ("Adverse", "Reform")}, hfmt=".2f")
    lay = figs.layout(ytitle, x0=2019, dtick=1)
    lay["shapes"][0]["x0"] = 2024.5
    lay["shapes"][1]["x0"] = lay["shapes"][1]["x1"] = 2024.5
    lay["annotations"][0]["x"] = 2024.6
    lay["annotations"][0]["text"] = "Cari qiymətləndirmə 2025, proqnoz 2026–2030"
    return figs.spec(data, lay)


def groups_fig(d):
    fc = d["fc"]
    b = fc[(fc.panel == "activity") & (fc.scenario == "Baseline") & (fc.unit != "ALL")]
    p = b.pivot(index="unit", columns="year", values="entry").sort_values(2030, ascending=False)
    return figs.hbar([GROUP_AZ.get(u, u) for u in p.index], list(p[2030]), "giriş əmsalı, %", "2030 (Əsas)",
                     values2=list(p[2025]), name2="2025 (cari qiymətləndirmə)")


def headline(d):
    b = d["fc_all"]["Baseline"]
    f = d["fall"]
    return [("Bazara giriş əmsalı (bütün sahələr)", "%", list(b.loc[YEARS, "entry"]),
             (f.loc[2030, "entry_p5"], f.loc[2030, "entry_p95"]), 2, "FR12")]
