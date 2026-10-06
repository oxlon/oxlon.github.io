"""b_mon.py — Monitor bundles: feeds, consensus/model risk (data/mon.js, loaded with the page), the market panel and
market factors (data/d4.js, data/v2.js) and the full forecast-impact table (data/d6.js) — the last three on demand."""
from . import bcore as C, b_names


def build(tr):
    out = []
    T = {}
    for name in ("D2_feed_status.csv", "D3_consensus_baselines.csv", "D3_consensus_long.csv", "D3_model_risk.csv"):
        d = C.csv(name, "mon")
        T[name[:-4]] = C.table(tr.df(d))
    man = C.csv("manifest.csv", "mon", required=False, base=C.UNIT / "data" / "vintages")
    if man is not None:
        T["vintages_manifest"] = C.table(man.sort_values(["feed", "vintage"]), ["feed", "vintage", "retrieved_utc", "n_obs",
                                                                               "first_obs", "last_obs", "status", "url"])
    out.append(("mon", T))

    # D4: one series per key → {meta, x: dates, y: values}; long daily series thinned to business days already
    d4 = C.csv("D4_market_panel.csv", "d4")
    S = {}
    if d4 is not None:
        for key, g in d4.sort_values(["series", "date"]).groupby("series", sort=True):
            r0 = g.iloc[0]
            nm, un = b_names.name(str(key), C.cell(r0["name"]), C.cell(r0["unit"]))
            S[str(key)] = {"name": nm, "unit": un if un not in (None, "None") else "", "feed": C.cell(r0["feed"]),
                           "grp": b_names.group(str(r0["feed"])),
                           "freq": C.cell(r0["freq"]), "mat": C.cell(r0.get("maturity_days")), "isin": C.cell(r0.get("isin")),
                           "x": [str(x) for x in g["date"]], "y": [C.fnum(v, 6) for v in g["value"]]}
    out.append(("d4", {"D4_market_panel": S}))

    v2 = C.csv("V2_market_factors.csv", "v2")
    V = {}
    if v2 is not None:
        for fq, g in v2.sort_values("tarix").groupby("tezlik", sort=True):
            cols = [c for c in g.columns if c not in ("tarix", "tezlik")]
            V[str(fq)] = {"x": [str(x) for x in g["tarix"]], "s": {c: [C.fnum(v, 6) for v in g[c]] for c in cols}}
    out.append(("v2", {"V2_market_factors": V}))

    d6 = C.csv("D6_forecast_impact.csv", "d6")
    out.append(("d6", {"D6_forecast_impact": C.table(tr.df(d6), sig=6, pool=("driver", "label_az", "unit", "channel", "source",
                                                                            "scenario_note"))}))
    return out
