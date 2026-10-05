"""p_fr3.py — FR3 series: wage breakdowns (nominal, real), branch wages, hired employment by sector, model variables."""
from . import pcore as C
from .plabels import FR3_SEC

BRK = {"average wage": "Orta aylıq əmək haqqı", "state sector": "Dövlət sektoru", "private sector": "Qeyri-dövlət sektoru",
       "non-oil sector": "Qeyri-neft sektoru", "oil sector": "Neft sektoru"}
FANKEY = {"average wage": "w_avg", "state sector": "w_state", "private sector": "w_priv", "non-oil sector": "w_non",
          "oil sector": "w_oil"}
HOLD = {"average wage": "average wage", "non-oil sector": "non-oil wage", "private sector": "private wage",
        "state sector": "state wage", "oil sector": "oil wage (non-oil x premium lever)"}
FULL = {"w_avg": "Orta əmək haqqı (uzlaşdırılmış)", "w_state": "Dövlət sektoru", "w_priv": "Qeyri-dövlət sektoru",
        "w_non": "Qeyri-neft sektoru", "w_oil": "Neft sektoru", "prem_oil": "Neft mükafatı (dəfə)",
        "minwage": "Minimum əmək haqqı", "cpi": "İstehlak qiymətləri indeksi", "hired": "Muzdlu işçilər, min",
        "kaitz": "Kaitz indeksi (minimum / orta)", "wagebill": "Əmək haqqı fondu", "rw_avg": "Real orta əmək haqqı",
        "rw_non": "Real: qeyri-neft", "rw_priv": "Real: qeyri-dövlət", "rw_state": "Real: dövlət", "rw_oil": "Real: neft",
        "balance_factor": "Uzlaşdırma əmsalı", "agg_gap_pct": "Aqreqasiya fərqi, %", "oil_split_gap_pct": "Neft bölgüsü fərqi, %"}


def _hold(key):
    h = C.csv("FR3_holdout_validation.csv").set_index("variable")
    if key not in h.index:
        return None
    r = h.loc[key]
    return {"rw": C.fnum(r["U vs random walk"]), "cg": C.fnum(r["U vs const growth"]), "rmse": C.fnum(r.model_RMSE),
            "win": "2021–2025", "src": "FR3_holdout_validation.csv"}


def build(R):
    L = C.csv("FR3_wage_accounts_long.csv")
    fan = C.csv("FR3_fan_wages.csv")
    fan = fan[fan.sources == "all"]
    for brk, name in BRK.items():
        for met, lab in (("nominal", "Nominal"), ("real", "Real (2015 qiymətləri)")):
            hist = L[(L.breakdown == brk) & (L.scenario == "ACTUAL")].set_index("year")[met].to_dict()
            sc = {s: L[(L.breakdown == brk) & (L.scenario == s)].set_index("year")[met] for s in C.SC}
            band = None
            if met == "nominal":
                f = fan[(fan.variable == FANKEY[brk]) & (fan.measure == "level")].set_index("year")
                if len(f):
                    band = (C.yv(f.q05, C.YEARS), C.yv(f.q95, C.YEARS))
            R.add("FR3", "Bölgülər üzrə əmək haqqı", name, "AZN/ay", sc, var=lab, hist=hist, band=band,
                  src="FR3_wage_accounts_long.csv", info="FR3.wage", hold=_hold(HOLD[brk]) if met == "nominal" else None)
    w = C.csv("FR3_fan_wages.csv")
    wb = w[(w.sources == "all") & (w.variable == "wagebill") & (w.measure == "level")].set_index("year")
    full = C.csv("FR3_wage_forecast_full.csv")
    full = full.rename(columns={full.columns[0]: "scenario", full.columns[1]: "year"})
    for col in [c for c in full.columns[2:]]:
        sc = {s: full[full.scenario == s].set_index("year")[col] for s in C.SC}
        band = (C.yv(wb.q05, C.YEARS), C.yv(wb.q95, C.YEARS)) if col == "wagebill" and len(wb) else None
        kind = "rate" if col.endswith("_pct") else "lvl"
        R.add("FR3", "Model dəyişənləri", FULL.get(col, col), "", sc, band=band, kind=kind,
              src="FR3_wage_forecast_full.csv", info="FR3.model", note=f"kod: {col}")
    br = C.csv("FR3_industry_branch_wages.csv")
    br = br.rename(columns={br.columns[0]: "scenario", br.columns[1]: "year"})
    for col in br.columns[2:]:
        sc = {s: br[br.scenario == s].set_index("year")[col] for s in C.SC}
        R.add("FR3", "Sənaye sahələri üzrə əmək haqqı", col, "AZN/ay", sc, src="FR3_industry_branch_wages.csv",
              info="FR3.branch")
    se = C.csv("FR3_sector_employment.csv")
    se = se.rename(columns={se.columns[0]: "scenario", se.columns[1]: "year"})
    for col in se.columns[2:]:
        sc = {s: se[se.scenario == s].set_index("year")[col] for s in C.SC}
        R.add("FR3", "Sektorlar üzrə muzdlu işçilər", FR3_SEC.get(col, col), "min nəfər", sc,
              src="FR3_sector_employment.csv", info="FR3.sectemp")
