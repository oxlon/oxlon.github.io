"""fr5_data.py — FR5 (paid services) numbers and figures."""
from . import core, figs
from .common import YEARS, SCEN

TYPE_AZ = {"household": "Məişət xidmətləri", "transport": "Nəqliyyat xidmətləri", "communication": "Rabitə xidmətləri",
           "housing": "Mənzil xidmətləri", "utilities": "Kommunal xidmətlər", "culture": "Mədəniyyət xidmətləri",
           "tourism": "Turizm və ekskursiya", "sport": "Bədən tərbiyəsi və idman", "medical": "Tibbi xidmətlər",
           "sanatoria": "Sanatoriya-sağlamlıq", "legal_bank": "Hüquqi və bank xidmətləri", "education": "Təhsil xidmətləri",
           "other": "Digər pullu xidmətlər", "TOTAL": "Cəmi"}


def load():
    d = {}
    fl = core.csv("FR5_forecast_long.csv")
    d["fl"] = fl
    tot = fl[fl.type == "TOTAL"]
    d["tot"] = {s: tot[tot.scenario == s].set_index("year") for s in SCEN}
    b26 = d["tot"]["Baseline"].loc[2026]
    v25 = b26.volume_2015_prices / (1 + b26.volume_growth_pct / 100)
    w = core.csv("FR5_workbook_paid_services.csv", index_col=0)
    pvi = w["ps_pvi"].dropna()
    pvi = pvi[pvi.index >= 2000]
    lv = {2025: v25}
    for y in range(2025, int(pvi.index.min()), -1):
        lv[y - 1] = lv[y] / (pvi.loc[y] / 100)
    d["vol_hist"] = dict(sorted(lv.items()))
    d["g_hist"] = (pvi - 100).loc[2001:]
    d["fanv"] = core.csv("FR5_fan_volume.csv")
    d["fanval"] = core.csv("FR5_fan_value.csv")
    d["sc"] = core.csv("FR5_scenario_summary.csv").set_index("scenario")
    d["types"] = core.csv("FR5_type_growth_vs_history.csv")
    d["hold"] = core.csv("FR5_holdout_validation.csv")
    d["meta"] = core.csv("FR5_fan_meta.csv").iloc[0]
    d["fr1"] = core.csv("FR5_fr1_comparison.csv", index_col=0)
    d["split"] = core.csv("FR5_institutional_split.csv")
    d["e1"] = core.csv("FR5_e1_coefficients.csv", index_col=0)
    d["ident"] = core.csv("FR5_identity_checks.csv")
    return d


def fan_years(d, key="fanv"):
    f = d[key]
    f = f[f.year.astype(str).str.fullmatch(r"\d{4}")].copy()
    f["year"] = f.year.astype(int)
    return f.set_index("year")


def volume_fig(d):
    h = d["vol_hist"]
    f = fan_years(d)
    data = figs.band(f.index, f.level_p5, f.level_p95)
    data.append(figs.line(list(h), list(h.values()), "Faktiki (zəncirvari həcm indeksindən)", hfmt=",.0f"))
    b = d["tot"]["Baseline"]
    data.append(figs.line([2025] + YEARS, [h[2025]] + list(b.loc[YEARS, "volume_2015_prices"]), "Əsas ssenari (proqnoz)",
                          mode="lines+markers", hfmt=",.0f"))
    data += figs.scen_lines(YEARS, {s: list(d["tot"][s].loc[YEARS, "volume_2015_prices"]) for s in ("Adverse", "Reform")},
                            hfmt=",.0f")
    return figs.spec(data, figs.layout("mln AZN, 2015-ci il qiymətləri ilə", x0=2000))


def growth_fig(d):
    g = d["g_hist"]
    f = fan_years(d)
    data = figs.band(f.index, f.growth_pct_p5, f.growth_pct_p95)
    data.append(figs.line(g.index, g.values, "Faktiki (DSK həcm indeksi)", hfmt=".1f"))
    b = d["tot"]["Baseline"]
    data.append(figs.line([2025] + YEARS, [g.loc[2025]] + list(b.loc[YEARS, "volume_growth_pct"]), "Əsas ssenari (proqnoz)",
                          mode="lines+markers", hfmt=".1f"))
    return figs.spec(data, figs.layout("real artım, %", x0=2001))


def types_fig(d):
    t = d["types"]
    t = t[t.type != "TOTAL"].sort_values("forecast_2026_2030", ascending=False)
    return figs.hbar([TYPE_AZ.get(x, x) for x in t.type], list(t.forecast_2026_2030), "orta illik həcm artımı, %",
                     "Proqnoz 2026–2030", values2=list(t.hist_2021_2025), name2="Faktiki 2021–2025")


def headline(d):
    b = d["tot"]["Baseline"]
    f = fan_years(d)
    return [("Pullu xidmətlərin real həcmi", "mln AZN (2015)", list(b.loc[YEARS, "volume_2015_prices"]),
             (f.loc[2030, "level_p5"], f.loc[2030, "level_p95"]), 0, "FR5")]
