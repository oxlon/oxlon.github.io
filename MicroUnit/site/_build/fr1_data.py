"""fr1_data.py — FR1 numbers and figures, read from MicroUnit/output at build time."""
from . import core, figs
from .common import YEARS, SCEN

VAR_AZ = {"real GDP": "Real ÜDM", "real non-oil GDP": "Real qeyri-neft ÜDM", "real consumption": "Real istehlak",
          "manufacturing VA": "Emal sənayesi, ƏD", "construction VA": "Tikinti, ƏD", "trade VA": "Ticarət, ƏD",
          "transport VA": "Nəqliyyat, ƏD", "agriculture VA": "Kənd təsərrüfatı, ƏD", "ICT VA": "İKT, ƏD",
          "non-oil investment": "Qeyri-neft investisiyaları", "state investment": "Dövlət investisiyaları",
          "employment": "Məşğulluq", "nominal GDP": "Nominal ÜDM", "budget revenue": "Büdcə gəlirləri"}


def load():
    d = {}
    ds = core.csv("FR1_analysis_dataset.csv").set_index("year")
    ff = core.csv("FR1_forecast_full.csv", index_col=0)
    d["hist"] = {k: core.growth(ds[k]).loc[2006:2025] for k in ("rgdp", "rgdpnon")}
    d["last"] = {k: ds.loc[2025, k] for k in ("rgdp", "rgdpnon", "emp", "wage")}
    sc = {}
    for s in SCEN:
        f = ff[ff.scenario == s].sort_index()
        g = {}
        for k in ("rgdp", "rgdpnon"):
            lv = [d["last"][k]] + list(f[k])
            g[k] = [(lv[i + 1] / lv[i] - 1) * 100 for i in range(5)]
        y30 = f.loc[2030]
        g["infl30"] = y30["infl"]
        g["unemp30"] = y30["unemp"]
        g["bal30"] = y30["balance_n"] / y30["gdp_n"] * 100
        g["debt30"] = y30["debt_azn"] / y30["gdp_n"] * 100
        g["gdpn30"] = y30["gdp_n"] / 1000
        sm = core.csv(f"FR1_accounts_summary_{s.lower()}.csv")
        g["summary"] = sm
        agg = sm.set_index("entity")
        g["avg_rgdp"] = agg.loc["GDP at market prices", "real_growth_avg_pct"]
        g["avg_rgdpnon"] = agg.loc["Non-oil GDP", "real_growth_avg_pct"]
        sc[s] = g
    d["scen"] = sc
    d["fan"] = {k: core.csv(f"FR1_fan_growth_{k}.csv", index_col=0) for k in ("rgdp", "rgdpnon")}
    d["hold"] = core.csv("FR1_holdout_validation.csv")
    au = core.csv("FR1_equation_audit.csv")
    lev = au[au.kind == "level"]
    d["coint"] = (int((lev.eg_coint_p < 0.05).sum()), int(len(lev)), int((lev.eg_coint_p < 0.10).sum()))
    d["n_eq"] = len(au)
    ic = core.csv("FR1_identity_checks.csv")
    d["ident"] = (int((ic.verdict == "OK").sum()), len(ic))
    d["draws"] = int(core.csv("FR1_fan_draws.csv", usecols=["draw"])["draw"].nunique())
    return d


def growth_fig(d, k, title_y):
    h = d["hist"][k]
    fan = d["fan"][k]
    base = d["scen"]["Baseline"][k]
    data = figs.band(fan.index, fan["p5"], fan["p95"])
    data.append(figs.line(h.index, h.values, "Faktiki", figs.ACCENT, hfmt=".1f"))
    data.append(figs.line([2025] + YEARS, [h.loc[2025]] + base, "Əsas ssenari (proqnoz)", figs.ACCENT, "solid", 3,
                          mode="lines+markers", hfmt=".1f"))
    data += figs.scen_lines(YEARS, {s: d["scen"][s][k] for s in ("Adverse", "Reform")}, hfmt=".1f")
    lay = figs.layout(title_y, x0=2006, ysuffix="")
    return figs.spec(data, lay)


def sectors_fig(d):
    sm = d["scen"]["Baseline"]["summary"]
    sec = sm[sm.group.str.startswith("1 ")].sort_values("real_growth_avg_pct", ascending=False)
    adv = d["scen"]["Adverse"]["summary"].set_index("entity").loc[sec.entity, "real_growth_avg_pct"]
    return figs.hbar(list(sec.entity_az), list(sec.real_growth_avg_pct), "orta illik real artım, 2026–2030, %",
                     "Əsas ssenari", values2=list(adv), name2="Mənfi ssenari")


def hold_summary(d):
    h = d["hold"]
    from .common import beat_count, median
    return {
        "rw20": beat_count(h.U_rw2020) + (median(h.U_rw2020),),
        "rw19": beat_count(h.U_rw2019) + (median(h.U_rw2019),),
        "cg19": beat_count(h.U_cg1019) + (median(h.U_cg1019),),
        "cg20": beat_count(h.U_cg1020) + (median(h.U_cg1020),),
        "sig_rw": int((h.DM_p_rw2020 < 0.10).sum()),
        "sig_cg": int(((h.DM_p_cg1019 < 0.10) & (h.U_cg1019 < 1)).sum()),
        "gdp": h[h.variable == "real GDP"].iloc[0],
        "non": h[h.variable == "real non-oil GDP"].iloc[0],
    }


def headline(d):
    """Rows for the index page headline table."""
    rows = []
    for k, lab in (("rgdp", "Real ÜDM, artım"), ("rgdpnon", "Qeyri-neft ÜDM, real artım")):
        fan = d["fan"][k]
        rows.append((lab, "%", d["scen"]["Baseline"][k], (fan.loc[2030, "p5"], fan.loc[2030, "p95"]), 1, "FR1"))
    return rows
