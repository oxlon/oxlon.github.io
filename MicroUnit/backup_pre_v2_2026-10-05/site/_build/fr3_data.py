"""fr3_data.py — FR3 (wages) numbers and figures."""
from . import core, figs
from .common import YEARS, SCEN

BRK_AZ = {"average wage": "Orta aylıq əmək haqqı", "state sector": "Dövlət sektoru", "private sector": "Qeyri-dövlət sektoru",
          "non-oil sector": "Qeyri-neft sektoru", "oil sector": "Neft sektoru"}
HOLD_AZ = {"average wage": "Orta əmək haqqı", "non-oil wage": "Qeyri-neft sektoru", "private wage": "Qeyri-dövlət sektoru",
           "state wage": "Dövlət sektoru", "oil wage (non-oil x premium lever)": "Neft sektoru (qeyri-neft × mükafat rıçağı)"}


def load():
    d = {}
    L = core.csv("FR3_wage_accounts_long.csv")
    d["long"] = L
    d["sum"] = core.csv("FR3_wage_summary.csv")
    fan = core.csv("FR3_fan_wages.csv")
    d["fan"] = fan[(fan.sources == "all") & (fan.measure == "level")]
    d["fang"] = fan[(fan.sources == "all") & (fan.measure == "growth_pct")]
    d["hold"] = core.csv("FR3_holdout_validation.csv").rename(columns={"U vs random walk": "U_rw", "U vs const growth": "U_cg"})
    d["now"] = core.csv("FR3_nowcast_2026.csv")
    d["bnb"] = core.csv("FR3_budget_nonbudget_range.csv")
    au = core.csv("FR3_equation_audit.csv")
    d["n_eq"] = len(au)
    d["coint"] = int((au.eg_coint_p < 0.05).sum())
    return d


def series(d, brk, scen):
    L = d["long"]
    a = L[(L.breakdown == brk) & (L.scenario == "ACTUAL")].set_index("year")["nominal"]
    f = L[(L.breakdown == brk) & (L.scenario == scen)].set_index("year")["nominal"]
    return a, f


def wavg_fig(d):
    a, _ = series(d, "average wage", "Baseline")
    a = a.loc[2005:]
    fan = d["fan"][d["fan"].variable == "w_avg"].set_index("year")
    data = figs.band(fan.index, fan["q05"], fan["q95"])
    data.append(figs.line(a.index, a.values, "Faktiki", hfmt=",.0f"))
    _, f = series(d, "average wage", "Baseline")
    data.append(figs.line([2025] + list(f.index), [a.loc[2025]] + list(f.values), "Əsas ssenari (proqnoz)",
                          mode="lines+markers", hfmt=",.0f"))
    data += figs.scen_lines(YEARS, {s: list(series(d, "average wage", s)[1].values) for s in ("Adverse", "Reform")},
                            hfmt=",.0f")
    return figs.spec(data, figs.layout("AZN, ayda (nominal)"))


def breakdown_fig(d):
    data = []
    styles = {"state sector": (figs.ACCENT, "solid"), "private sector": (figs.GREY, "solid"),
              "non-oil sector": (figs.ACCENT, "dot"), "average wage": (figs.GREY, "dot")}
    for brk, (col, dash) in styles.items():
        a, f = series(d, brk, "Baseline")
        a = a.loc[2005:]
        data.append(figs.line(list(a.index) + list(f.index), list(a.values) + list(f.values), BRK_AZ[brk],
                              col, dash, 2.4, hfmt=",.0f"))
    return figs.spec(data, figs.layout("AZN, ayda (nominal)"))


def headline(d):
    _, f = series(d, "average wage", "Baseline")
    fan = d["fan"][d["fan"].variable == "w_avg"].set_index("year")
    return [("Orta aylıq nominal əmək haqqı", "AZN", list(f.loc[YEARS].values),
             (fan.loc[2030, "q05"], fan.loc[2030, "q95"]), 0, "FR3")]
