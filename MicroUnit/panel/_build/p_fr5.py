"""p_fr5.py — FR5 series: total and 13 service types (volume, value, deflator, share), institutional splits."""
from . import pcore as C

TYPE_AZ = {"TOTAL": "Pullu xidmətlər, cəmi", "household": "Məişət xidmətləri", "transport": "Nəqliyyat xidmətləri",
           "communication": "Rabitə xidmətləri", "housing": "Mənzil xidmətləri", "utilities": "Kommunal xidmətlər",
           "culture": "Mədəniyyət xidmətləri", "tourism": "Turizm və ekskursiya", "sport": "Bədən tərbiyəsi və idman",
           "medical": "Tibbi xidmətlər", "sanatoria": "Sanatoriya-sağlamlıq", "legal_bank": "Hüquqi və bank xidmətləri",
           "education": "Təhsil xidmətləri", "other": "Digər pullu xidmətlər"}
VAR = [("volume_2015_prices", "Real həcm", "mln AZN (2015)", "FR5_volume_by_type_history.csv"),
       ("value_current", "Nominal dəyər", "mln AZN", "FR5_dsk_value_by_type_history.csv"),
       ("deflator", "Deflyator", "2015 = 100", "FR5_deflator_by_type_history.csv"),
       ("share_pct", "Pay", "%", "FR5_shares_by_type_history.csv")]
SPLIT = {"indiv": "Fərdi sahibkarlar", "legal": "Hüquqi şəxslər", "state": "Dövlət", "nonstate": "Qeyri-dövlət"}


def _fy(df, key="year"):
    df = df[df[key].astype(str).str.fullmatch(r"\d{4}")].copy()
    df[key] = df[key].astype(int)
    return df.set_index(key)


def build(R):
    fl = C.csv("FR5_forecast_long.csv")
    fv, fval = _fy(C.csv("FR5_fan_volume.csv")), _fy(C.csv("FR5_fan_value.csv"))
    fs = C.csv("FR5_fan_shares.csv")
    hv = C.csv("FR5_holdout_validation.csv")
    hb = hv[hv.window.str.startswith("B")].iloc[0]
    hs = C.csv("FR5_holdout_shares.csv")
    hs = hs[hs.iloc[:, 0] == "B"].set_index("type")
    # total volume history: chain the DSK volume index back from the 2025 anchor
    w = C.csv("FR5_workbook_paid_services.csv", index_col=0)
    pvi = w["ps_pvi"].dropna()
    tot = fl[(fl.type == "TOTAL") & (fl.scenario == "Baseline")].set_index("year")
    v25 = tot.loc[2026, "volume_2015_prices"] / (1 + tot.loc[2026, "volume_growth_pct"] / 100)
    vh = {2025: v25}
    for y in range(2025, max(int(pvi.index.min()), 2000), -1):
        vh[y - 1] = vh[y] / (pvi.loc[y] / 100)
    for typ in fl.type.unique():
        for col, lab, unit, hfile in VAR:
            if typ == "TOTAL" and col == "share_pct":
                continue
            m = fl[fl.type == typ]
            sc = {s: m[m.scenario == s].set_index("year")[col] for s in C.SC}
            h = C.csv(hfile, index_col=0)
            hcol = "total" if typ == "TOTAL" else typ
            hist = h[hcol].to_dict() if hcol in h.columns else {}
            if typ == "TOTAL" and col == "volume_2015_prices":
                hist = vh
            band = hold = None
            if typ == "TOTAL" and col == "volume_2015_prices":
                band = (C.yv(fv.level_p5, C.YEARS), C.yv(fv.level_p95, C.YEARS))
                hold = {"rw": C.fnum(hb.U_vs_random_walk), "cg": C.fnum(hb.U_vs_constant_growth),
                        "rmse": C.fnum(hb.RMSE_pct), "win": str(hb.scored_years), "src": "FR5_holdout_validation.csv"}
            elif typ == "TOTAL" and col == "value_current":
                band = (C.yv(fval.level_p5, C.YEARS), C.yv(fval.level_p95, C.YEARS))
            elif col == "share_pct":
                f = fs[fs.type == typ].set_index("year")
                band = (C.yv(f.share_pct_p5, C.YEARS), C.yv(f.share_pct_p95, C.YEARS)) if len(f) else None
                if typ in hs.index:
                    hold = {"rw": C.fnum(hs.loc[typ, "U_vs_random_walk"]), "cg": None, "rmse": C.fnum(hs.loc[typ, "share_RMSE_pp"]),
                            "win": "test pəncərəsi", "src": "FR5_holdout_shares.csv"}
            R.add("FR5", "Cəmi" if typ == "TOTAL" else "13 xidmət növü", TYPE_AZ.get(typ, typ), unit, sc, var=lab,
                  hist=hist, band=band, kind="rate" if col == "share_pct" else "lvl", src="FR5_forecast_long.csv",
                  info="FR5.total" if typ == "TOTAL" else "FR5.type", hold=hold)
    sp = C.csv("FR5_institutional_split.csv")
    fsp = C.csv("FR5_fan_splits.csv")
    st = C.csv("FR5_dsk_state_nonstate_history.csv", index_col=0)
    for key, name in SPLIT.items():
        m = sp.copy()
        m[f"{key}_share"] = m[f"{key}_share"] * 100
        f = fsp[fsp.series == f"{key}_share"].set_index("year")
        band = (C.yv(f.share_pct_p5, C.YEARS), C.yv(f.share_pct_p95, C.YEARS)) if len(f) else None
        hist_v = st[key].to_dict() if key in st.columns else {}
        sh = (st[key] / st["total"] * 100).to_dict() if key in st.columns else {}
        R.add("FR5", "İnstitusional bölgülər", name, "%", {s: m[m.scenario == s].set_index("year")[f"{key}_share"] for s in C.SC},
              var="Pay", hist=sh, band=band, kind="rate", src="FR5_institutional_split.csv", info="FR5.split")
        R.add("FR5", "İnstitusional bölgülər", name, "mln AZN", {s: m[m.scenario == s].set_index("year")[f"{key}_value"] for s in C.SC},
              var="Nominal dəyər", hist=hist_v, src="FR5_institutional_split.csv", info="FR5.split")
