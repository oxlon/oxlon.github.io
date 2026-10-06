"""b_core.py — data/core.js: everything the start page and the risk register need (loaded on every page).

Tables are keyed by the output file stem (e.g. FR2_risk_scores); the JS reads them with U.T('<stem>').
"""
from . import bcore as C

HEADLINE = {"fr1:rgdp", "fr1:rgdpnon", "fr1:infl", "fr1:gdp_n", "fr1:rev_tot_n", "fr1:balance_n"}


def build(tr):
    B = "core"
    T = {}

    def add(name, cols=None, required=True, base=C.OUT, stem=None, df=None, **kw):
        d = df if df is not None else C.csv(name, B, required=required, base=base, dtype=kw.pop("dtype", None))
        if d is None:
            return None
        T[stem or name.rsplit(".", 1)[0]] = C.table(tr.df(d), cols, **kw)
        return d

    reg = add("risk_reyestri.csv", base=C.INP, stem="input_risk_reyestri", dtype=str)
    add("hedler.csv", base=C.INP, stem="input_hedler")
    add("risk_istahi.csv", base=C.INP, stem="input_risk_istahi", required=False)
    add("FR2_risk_scores.csv")
    add("FR2_score_history.csv")
    add("FR2_alerts.csv")
    add("FR2_heatmap.csv")
    add("FR1_indicator_base.csv")
    add("FR1_transmission_channels.csv")
    add("FR1_event_chronology.csv")
    add("FR1_hazard_parameters.csv")
    add("FR2_contributions.csv")
    add("FR2_distribution.csv")
    add("FR2_distribution_live.csv")
    add("FR2_band_layering.csv")
    add("FR2_gar_crosscheck.csv")
    add("FR3_residual_risk.csv")
    add("D5_daily_monitor.csv")
    add("D7_changes.csv")
    add("S0_factor_sigma.csv")
    add("S7_daily_decision.csv")
    add("C2_balance_of_risks.csv")
    add("C3_category_map.csv")
    add("K1_at_risk_summary.csv")
    for opt in ("FR1_fx_transmission.csv", "FR2_model_risk.csv", "FR2_threshold_sensitivity.csv"):
        add(opt, required=False)              # newer outputs of the modelling agents (shown when present)
    d6 = C.csv("D6_forecast_impact.csv", B)
    if d6 is not None:
        h = d6[d6["target_id"].isin(HEADLINE) | ~d6["target_id"].str.startswith("fr")]
        T["D6_headline"] = C.table(tr.df(h), pool=("channel", "source", "scenario_note", "label_az", "unit"))
    nfr2 = add("NFR2_update_log.csv")
    rs = C.run_summary()
    cat = C.csv("_catalog_v2.csv", B)
    T["_catalog_v2"] = C.table(tr.df(cat), ["file", "owner_module", "description_az", "update_frequency", "updated_utc"])
    meta = {"run": tr.deep(rs), "run_daily": tr.deep(C.run_summary_daily()), "risks": sorted(reg["risk_id"].tolist()) if reg is not None else [],
            "n_feeds": None, "nfr2": len(nfr2) if nfr2 is not None else 0}
    T["_meta"] = meta
    return B, T
