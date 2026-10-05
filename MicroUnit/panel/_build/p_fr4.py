"""p_fr4.py — FR4 series: 19 activities × 2 bases, 8 groups, institutional breakdowns (state, budget, oil)."""
from . import pcore as C
from .plabels import FR4_ACT

BASIS = {"employed population": ("Məşğul əhali", "FR4_dsk_employed_by_activity_history.csv"),
         "hired employees": ("Muzdlu işçilər", "FR4_dsk_hired_by_activity_history.csv")}
GRP = {"Agriculture, forestry & fishing": "Kənd, meşə və balıqçılıq", "Industry": "Sənaye", "Construction": "Tikinti",
       "Trade & repair": "Ticarət və təmir", "Accommodation & food": "Yerləşdirmə və iaşə",
       "Transport & storage": "Nəqliyyat və anbar", "Information & communication": "İnformasiya və rabitə",
       "Other services (9 activities)": "Digər xidmətlər (9 fəaliyyət)"}
INST = {"employed, total": "Məşğul əhali, cəmi", "labour force (FR1)": "İqtisadi fəal əhali (FR1)", "state": "Dövlət sektoru",
        "non-state": "Qeyri-dövlət sektoru", "state share, %": "Dövlət sektorunun payı, %", "hired, total": "Muzdlu işçilər, cəmi",
        "budget organisations": "Büdcə təşkilatları", "non-budget": "Qeyri-büdcə təşkilatları",
        "budget share of hired, %": "Büdcənin muzdlu işçilərdə payı, %", "oil, statistical basis": "Neft sektoru (statistik)",
        "non-oil, statistical basis (hired)": "Qeyri-neft sektoru (statistik, muzdlu)",
        "employment contracts, tax-record basis": "Əmək müqavilələri (vergi uçotu)",
        "oil, tax-record basis": "Neft sektoru (vergi uçotu)", "non-oil, tax-record basis": "Qeyri-neft sektoru (vergi uçotu)"}
INST_FAN = {"employed, total": "total employed", "hired, total": "hired employees", "state": "state",
            "budget organisations": "budget organisations", "oil, tax-record basis": "oil, tax-record basis",
            "oil, statistical basis": "oil, statistical basis"}


def _fanband(f, var):
    x = f[(f.variable == var) & (f.measure == "level, thousand persons")].copy()
    if x.empty:
        return None
    x["year"] = x.year.astype(int)
    x = x.set_index("year")
    return (C.yv(x.q05, C.YEARS), C.yv(x.q95, C.YEARS)), x


def build(R):
    L = C.csv("FR4_employment_long.csv")
    hv = C.csv("FR4_holdout_validation.csv")
    fan = C.csv("FR4_fan_employment.csv")
    for basis, (lab, hfile) in BASIS.items():
        hist = C.csv(hfile, index_col=0)
        for act in L.activity.unique():
            m = L[(L.basis == basis) & (L.activity == act)]
            sc = {s: m[m.scenario == s].set_index("year")["persons_thsd"] for s in C.SC}
            base = m[(m.scenario == "Baseline") & (m.year == 2025)]["persons_thsd"]
            h = hist[act].loc[:2024].to_dict() if act in hist.columns else {}
            hh = hv[(hv.basis == basis) & (hv.activity == act)]
            hold = ({"rw": C.fnum(hh.U_vs_random_walk.iloc[0]), "cg": C.fnum(hh.U_vs_constant_growth.iloc[0]),
                     "rmse": C.fnum(hh.model_RMSE_pct.iloc[0]), "win": "2020–2024", "src": "FR4_holdout_validation.csv"}
                    if len(hh) else None)
            band = None
            if act == "total":
                fb = _fanband(fan, "total employed" if basis == "employed population" else "hired employees")
                band = fb[0] if fb else None
            R.add("FR4", "19 fəaliyyət növü", FR4_ACT.get(act, act), "min nəfər", sc, var=lab, hist=h,
                  base=base.iloc[0] if len(base) else None, band=band, src="FR4_employment_long.csv",
                  info="FR4.activity", hold=hold)
    # 8 groups: the module exports the Baseline path with its fan
    hg = C.csv("FR4_holdout_validation_groups.csv")
    for g, name in GRP.items():
        fb = _fanband(fan, g)
        if not fb:
            continue
        band, x = fb
        hh = hg[(hg.basis == "employed population") & (hg.group == g)]
        hold = ({"rw": C.fnum(hh.U_vs_random_walk.iloc[0]), "cg": C.fnum(hh.U_vs_constant_growth.iloc[0]),
                 "rmse": C.fnum(hh.model_RMSE_pct.iloc[0]), "win": "2020–2024", "src": "FR4_holdout_validation_groups.csv"}
                if len(hh) else None)
        R.add("FR4", "8 fəaliyyət qrupu", name, "min nəfər", {"Baseline": x["point"]}, var="Məşğul əhali",
              base=x.loc[2025, "point"] if 2025 in x.index else None, band=band, src="FR4_fan_employment.csv",
              info="FR4.group", hold=hold, expect=("B",))
    I = C.csv("FR4_institutional_breakdown.csv")
    I = I.rename(columns={I.columns[0]: "scenario", I.columns[1]: "year"})
    prop = C.csv("FR4_dsk_property_form_history.csv", index_col=0)
    for col in I.columns[2:]:
        sc = {s: I[I.scenario == s].set_index("year")[col] for s in C.SC}
        base = I[(I.scenario == "Baseline") & (I.year == 2025)][col]
        hist = {}
        if col == "state":
            hist = prop["state"].to_dict()
        elif col == "non-state":
            hist = prop["nonstate"].to_dict()
        elif col == "employed, total":
            hist = prop["total"].to_dict()
        fb = _fanband(fan, INST_FAN[col]) if col in INST_FAN else None
        R.add("FR4", "İnstitusional bölgülər", INST.get(col, col), "%" if "%" in col else "min nəfər", sc, hist=hist,
              base=base.iloc[0] if len(base) else None, band=fb[0] if fb else None, kind="rate" if "%" in col else "lvl",
              src="FR4_institutional_breakdown.csv", info="FR4.inst")
