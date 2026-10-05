"""fr4_data.py — FR4 (employment) numbers and figures."""
from . import core, figs
from .common import YEARS

GRP_AZ = {"Agriculture, forestry & fishing": "Kənd, meşə və balıqçılıq", "Industry": "Sənaye",
          "Construction": "Tikinti", "Trade & repair": "Ticarət və təmir", "Accommodation & food": "Yerləşdirmə və iaşə",
          "Transport & storage": "Nəqliyyat və anbar", "Information & communication": "İnformasiya və rabitə",
          "Other services (9 activities)": "Digər xidmətlər (9 fəaliyyət)",
          "total employed": "Məşğul əhali, cəmi", "hired employees": "Muzdlu işçilər", "state": "Dövlət sektoru",
          "budget organisations": "Büdcə təşkilatları", "oil, tax-record basis": "Neft sektoru (vergi uçotu əsasında)",
          "oil, statistical basis": "Neft sektoru (statistik əsasda)"}
HOLD_AZ = {"total employed (E1-E2, simulated)": "Məşğul əhali, cəmi (simulyasiya)",
           "hired employees (E3 x simulated total)": "Muzdlu işçilər",
           "labour force (E1, projected population)": "İqtisadi fəal əhali",
           "state employment (E8 x simulated total)": "Dövlət sektorunda məşğulluq",
           "oil extraction employment (E9)": "Neft hasilatında məşğulluq (E9)"}
BASIS_AZ = {"employed population": "məşğul əhali", "hired employees": "muzdlu işçilər"}
LEVEL_AZ = {"19 activities": "19 fəaliyyət növü", "8 groups": "8 qrup"}


def load():
    d = {}
    f = core.csv("FR4_fan_employment.csv")
    d["lev"] = f[f.measure == "level, thousand persons"].copy()
    d["lev"]["year"] = d["lev"].year.astype(int)
    d["avg"] = f[f.measure == "average growth, % a year"].set_index("variable")
    d["hist"] = core.csv("FR4_dsk_employed_by_activity_history.csv", index_col=0)["total"]
    d["prop"] = core.csv("FR4_dsk_property_form_history.csv", index_col=0)
    d["sc"] = core.csv("FR4_scenario_summary.csv").set_index("scenario")
    d["hagg"] = core.csv("FR4_holdout_aggregate.csv")
    d["hsum"] = core.csv("FR4_holdout_summary.csv")
    d["inst"] = core.csv("FR4_institutional_breakdown.csv")
    d["inst"].columns = ["scenario", "year"] + list(d["inst"].columns[2:])
    d["ident"] = core.csv("FR4_identity_checks.csv")
    return d


def lev(d, var):
    return d["lev"][d["lev"].variable == var].set_index("year")


def total_fig(d):
    h = d["hist"]
    L = lev(d, "total employed")
    fy = [y for y in L.index if y >= 2026]
    data = figs.band(fy, L.loc[fy, "q05"], L.loc[fy, "q95"])
    hx = list(h.index) + [2025]
    hy = list(h.values) + [L.loc[2025, "point"]]
    data.append(figs.line(hx, hy, "Faktiki (DSK; 2025 — FR1)", hfmt=",.0f"))
    data.append(figs.line([2025] + fy, list(L.loc[[2025] + fy, "point"]), "Əsas ssenari (proqnoz)",
                          mode="lines+markers", hfmt=",.0f"))
    return figs.spec(data, figs.layout("min nəfər", x0=2000))


def state_fig(d):
    p = d["prop"]
    data = []
    for var, hcol, col in (("state", "state", figs.ACCENT), ("budget organisations", None, figs.GREY)):
        L = lev(d, var)
        fy = [y for y in L.index if y >= 2026]
        data += figs.band(fy, L.loc[fy, "q05"], L.loc[fy, "q95"], name=f"5–95 % zolağı: {GRP_AZ[var].lower()}")
        if hcol:
            data.append(figs.line(list(p.index), list(p[hcol]), GRP_AZ[var] + " — faktiki", col, hfmt=",.0f"))
        data.append(figs.line([2025] + fy, list(L.loc[[2025] + fy, "point"]), GRP_AZ[var] + " — proqnoz", col,
                              "solid", 2.6, mode="lines+markers", hfmt=",.0f"))
    return figs.spec(data, figs.layout("min nəfər", x0=2000))


def groups_fig(d):
    a = d["avg"]
    g = [k for k in a.index if k in GRP_AZ and k[0].isupper()]
    g = sorted(g, key=lambda k: -a.loc[k, "point"])
    return figs.hbar([GRP_AZ[k] for k in g], [a.loc[k, "point"] for k in g], "orta illik artım, 2026–2030, %",
                     "Əsas ssenari")


def headline(d):
    L = lev(d, "total employed")
    return [("Məşğul əhali", "min nəfər", list(L.loc[YEARS, "point"]), (L.loc[2030, "q05"], L.loc[2030, "q95"]), 0, "FR4")]
