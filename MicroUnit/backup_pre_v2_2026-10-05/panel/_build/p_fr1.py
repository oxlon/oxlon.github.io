"""p_fr1.py — FR1 series: sector/market accounts (real, nominal, deflator), model variables, growth contributions."""
from . import pcore as C
from .plabels import FR1_VAR, FR1_RATE, FR1_GROUP, METRIC, UNIT_AZ

HOLD_MAP = {"GDP at market prices": "real GDP", "Non-oil GDP": "real non-oil GDP", "Manufacturing": "manufacturing VA",
            "Construction": "construction VA", "Trade & vehicle repair": "trade VA", "Transport & storage": "transport VA",
            "Agriculture, forestry & fishing": "agriculture VA", "Information & communication": "ICT VA",
            "Non-oil investment": "non-oil investment", "State investment": "state investment", "Employment": "employment"}
HOLD_VAR = {"rgdp": "real GDP", "rgdpnon": "real non-oil GDP", "rcons": "real consumption", "rva_man": "manufacturing VA",
            "rva_con": "construction VA", "rva_trd": "trade VA", "rva_tra": "transport VA", "rva_agr": "agriculture VA",
            "rva_ict": "ICT VA", "rinv_non": "non-oil investment", "rinv_state": "state investment", "emp": "employment",
            "gdp_n": "nominal GDP", "rev_tot_n": "budget revenue"}
FANS = ["cpi", "emp", "infl", "rcons", "rcred_tot", "rev_tot_n", "rexp_cur", "rgdp", "rgdpnon", "rhhdisp", "rinv_non",
        "rva_con", "rva_man", "unemp", "wage"]


def _hold(name):
    h = C.csv("FR1_holdout_validation.csv").set_index("variable")
    if name not in h.index:
        return None
    r = h.loc[name]
    return {"rw": C.fnum(r.U_rw2020), "cg": C.fnum(r.U_cg1019), "rmse": C.fnum(r.model_RMSE),
            "win": "2021–2025", "src": "FR1_holdout_validation.csv"}


def build(R):
    ff = C.csv("FR1_forecast_full.csv", index_col=0)
    ds = C.csv("FR1_analysis_dataset.csv").set_index("year")
    fans = {k: C.csv(f"FR1_fan_{k}.csv", index_col=0) for k in FANS}
    # 2) accounts: every entity × metric, history 2005–2025
    a = C.csv("FR1_accounts_long.csv")
    sm = C.csv("FR1_accounts_summary_baseline.csv").set_index("entity")
    base_ff = ff[ff.scenario == "Baseline"]
    for (grp, ent), g in a.groupby(["group", "entity"], sort=False):
        unit = UNIT_AZ.get(sm.loc[ent, "unit"], sm.loc[ent, "unit"]) if ent in sm.index else ""
        name = sm.loc[ent, "entity_az"] if ent in sm.index else ent
        mets = [mt for mt in ("real", "nominal", "deflator") if not g[g.metric == mt].empty]
        vals = {mt: g[g.metric == mt].sort_values(["scenario", "year"])["value"].round(9).tolist() for mt in mets}
        if "real" in vals and "nominal" in vals and vals["real"] == vals["nominal"]:
            mets.remove("nominal")                        # persons, %, rates: one series, not two copies
        single = len(mets) == 1
        for met in mets:
            m = g[g.metric == met]
            hist = m[m.scenario == "ACTUAL"].set_index("year")["value"].to_dict()
            sc = {s: m[m.scenario == s].set_index("year")["value"] for s in C.SC}
            u = "2015 = 1" if met == "deflator" and unit not in ("2015 = 100", "%") else unit
            kind = "rate" if unit == "%" else "lvl"
            band = None                                   # attach a fan only where the series IS the fanned model variable
            bvals = C.yv(sc["Baseline"], C.YEARS)
            for code in FANS:
                fv = C.yv(base_ff[code], C.YEARS)
                if all(x is not None and y is not None and abs(x - y) <= 1e-6 * max(1, abs(y)) for x, y in zip(bvals, fv)):
                    f = fans[code]
                    band = (C.yv(f["p5"], C.YEARS), C.yv(f["p95"], C.YEARS))
                    break
            R.add("FR1", FR1_GROUP.get(grp, grp), name, u, sc, var="" if single else METRIC[met], hist=hist, band=band, kind=kind,
                  src="FR1_accounts_long.csv", info="FR1.accounts",
                  hold=_hold(HOLD_MAP[ent]) if (ent in HOLD_MAP and met == "real") else None)
    # 2b) contributions to GDP growth (Baseline only — the module exports the baseline decomposition)
    c = C.csv("FR1_gdp_growth_contributions.csv").set_index("year")
    names = C.csv("FR1_accounts_summary_baseline.csv").set_index("entity")["entity_az"]
    for col in c.columns:
        R.add("FR1", "ÜDM artımına töhfələr", names.get(col, col), "faiz bəndi", {"Baseline": c[col]}, kind="rate",
              src="FR1_gdp_growth_contributions.csv", info="FR1.contrib", expect=("B",))
    # 3) model variables (last in the list: technical) (exact codes; fan bands attach here)
    for code in [c for c in ff.columns if c != "scenario"]:
        sc = {s: ff[ff.scenario == s][code] for s in C.SC}
        hist = ds[code].loc[2005:2025].to_dict() if code in ds.columns else {}
        band = None
        if code in fans:
            f = fans[code]
            band = (C.yv(f["p5"], C.YEARS), C.yv(f["p95"], C.YEARS))
        R.add("FR1", "Model dəyişənləri", FR1_VAR.get(code, code), "", sc, var="", hist=hist, band=band,
              kind="rate" if code in FR1_RATE else "lvl", src="FR1_forecast_full.csv", info="FR1.model",
              hold=_hold(HOLD_VAR[code]) if code in HOLD_VAR else None, note=f"kod: {code}")
