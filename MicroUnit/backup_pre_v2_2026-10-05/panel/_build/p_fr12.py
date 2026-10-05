"""p_fr12.py — FR12 Layer-A series: entry/exit/stock for 11 activity groups and 14 regions (+ totals),
concentration bounds by activity group."""
from . import pcore as C
from .pnames import GROUP_AZ, region

MET = {"entry": ("Giriş əmsalı", "%", "rate"), "exit": ("Çıxış əmsalı", "%", "rate"),
       "new": ("Yeni qeydiyyatlar", "vahid", "lvl"), "exits": ("Ləğv edilənlər", "vahid", "lvl"),
       "N": ("Qeydiyyatdakı vahidlər", "vahid", "lvl")}
HIST = {"activity": {"N": "registered", "new": "new", "exits": "dereg", "entry": "entry", "exit": "exit"},
        "region": {"N": "enterprises", "new": "new", "exits": "liquidated", "entry": "entry", "exit": "exit"}}
HOLD = {("activity", "entry"): "entry rate, % (births / identity stock)", ("activity", "exit"): "exit rate, %",
        ("activity", "new"): "log births", ("region", "entry"): "entry rate, % (births / identity stock)",
        ("region", "exit"): "exit rate, %", ("region", "new"): "log births"}
CONC = {"sme_output_share": ("KOS-un buraxılışda payı", "%"), "large_share": ("İri müəssisələrin payı", "%"),
        "hhi_lower": ("HHI, aşağı hədd", "HHI"), "hhi_upper": ("HHI, yuxarı hədd", "HHI"),
        "hhi_upper_floor30": ("HHI, yuxarı hədd (30-dan az iri müəssisə fərziyyəsi)", "HHI"),
        "cr4_upper": ("CR4, yuxarı hədd", "%")}


def _hist_tables():
    g = C.csv("FR12_indicators_groups.csv")
    agg = g.groupby("year")[["registered", "new", "dereg"]].sum().reset_index()
    agg["entry"], agg["exit"], agg["group"] = agg.new / agg.registered * 100, agg.dereg / agg.registered * 100, "ALL"
    g = C.pd.concat([g, agg], ignore_index=True)
    r = C.csv("FR12_indicators_regions.csv")
    ra = r.groupby("year")[["enterprises", "new", "liquidated"]].sum().reset_index()
    ra["entry"], ra["exit"], ra["region"] = ra.new / ra.enterprises * 100, ra.liquidated / ra.enterprises * 100, "ALL"
    r = C.pd.concat([r, ra], ignore_index=True)
    return {"activity": g.rename(columns={"group": "unit"}), "region": r.rename(columns={"region": "unit"})}


def build(R):
    fc = C.csv("FR12_forecast_entry_exit.csv")
    fan = C.csv("FR12_fan_entry_exit.csv")
    hold = C.csv("FR12_holdout_validation.csv")
    H = _hist_tables()
    order = sorted(fc[["panel", "unit"]].drop_duplicates().itertuples(index=False), key=lambda t: (t[0], t[1] != "ALL", t[1]))
    for panel, unit in order:
        g = fc[(fc.panel == panel) & (fc.unit == unit)]
        name = (GROUP_AZ.get(unit, unit) if panel == "activity" else ("Bütün regionlar" if unit == "ALL" else region(unit)))
        grp = "Fəaliyyət qrupları: giriş və çıxış" if panel == "activity" else "Regionlar: giriş və çıxış"
        h = H[panel][H[panel].unit == unit].set_index("year")
        f = fan[(fan.panel == panel) & (fan.unit == unit)].set_index("year")
        for met, (lab, u, kind) in MET.items():
            sc = {s: g[g.scenario == s].set_index("year")[met] for s in C.SC}
            base = g[(g.scenario == "Baseline") & (g.year == 2025)][met]
            hist = h[HIST[panel][met]].to_dict() if HIST[panel][met] in h.columns else {}
            band = None
            if met != "exits" and f"{met}_p5" in f.columns and len(f):
                band = (C.yv(f[f"{met}_p5"], C.YEARS), C.yv(f[f"{met}_p95"], C.YEARS))
            ho = None
            hk = HOLD.get((panel, met))
            if hk and unit == "ALL":
                x = hold[(hold.panel == panel) & (hold.metric == hk)]
                if len(x):
                    x = x.iloc[0]
                    ho = {"rw": C.fnum(x.theil_rule_vs_rw), "cg": C.fnum(x.theil_rule_vs_constant), "rmse": C.fnum(x.rmse_rule),
                          "win": str(x.targets), "src": "FR12_holdout_validation.csv", "cgname": "sabit (təlim ortası)"}
            R.add("FR12", grp, name, u, sc, var=lab, hist=hist, base=base.iloc[0] if len(base) else None, band=band,
                  kind=kind, src="FR12_forecast_entry_exit.csv", info=f"FR12.{panel}", hold=ho,
                  note="2025 — cari qiymətləndirmə (DSK hələ nəşr etməyib)" if panel == "activity" else "")
    cp = C.csv("FR12_concentration_paths.csv")
    cb = C.csv("FR12_concentration_bounds.csv")
    for grp_code, g in cp.groupby("group", sort=True):
        hb = cb[cb.group == grp_code].set_index("year")
        for col, (lab, u) in CONC.items():
            sc = {s: g[g.scenario == s].set_index("year")[col] for s in C.SC}
            base = g[(g.scenario == "Baseline") & (g.year == 2025)][col]
            hist = hb[col].dropna().to_dict() if col in hb.columns else {}
            R.add("FR12", "Konsentrasiya hədləri", GROUP_AZ.get(grp_code, grp_code), u, sc, var=lab, hist=hist,
                  base=base.iloc[0] if len(base) else None, kind="rate" if u == "%" else "lvl",
                  src="FR12_concentration_paths.csv", info="FR12.conc")
