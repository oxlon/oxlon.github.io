"""p_fr10.py — FR10 Layer-A series: 30 branches × 8 indicators, 4 sections, industry, 14 regions, HHI,
non-state share, ~130 products. (Layer B is synthetic and goes to the separate synthetic bundle.)"""
from . import pcore as C
from .pnames import nace, region

IND = {"output_nominal_mn_AZN": ("Nominal buraxılış", "mln AZN", "FR10_branch_history.csv", "output_nominal_mn_AZN",
                                 "branch nominal output, mn AZN"),
       "output_real_mn_AZN_2015": ("Real buraxılış", "mln AZN (2015)", "FR10_branch_history.csv", "output_real_mn_AZN_2015",
                                   "branch real output, mn AZN 2015 prices"),
       "share_of_industry": ("Sənayedə pay", "%", "FR10_branch_shares_history.csv", "share_of_industry_pct",
                             "branch share of industry, %"),
       "share_of_manufacturing": ("Emalda pay", "%", "FR10_branch_shares_history.csv", "share_of_manufacturing_pct",
                                  "branch share of manufacturing, %"),
       "employees": ("İşçilər", "nəfər", "FR10_branch_history.csv", "employees", None),
       "lp_thsd_AZN_2015": ("Əmək məhsuldarlığı", "min AZN (2015) / işçi", None, None,
                            "labour productivity, thsd AZN 2015 prices per employee"),
       "wage_AZN_month": ("Orta əmək haqqı", "AZN/ay", "FR10_branch_history.csv", "wage_AZN_month", None),
       "gos_proxy_margin_pct": ("Marja (ümumi mənfəət / buraxılış)", "%", "FR10_efficiency_branches.csv",
                                "gos_proxy_margin_pct", "GOS-proxy margin, % of output")}
SEC = {"VA": ("Əlavə dəyər", "mln AZN"), "CE": ("İşçilərə ödəmələr", "mln AZN"), "OTP": ("İstehsala digər vergilər", "mln AZN"),
       "GOS": ("Ümumi mənfəət", "mln AZN"), "GOS_share_VA": ("Ümumi mənfəət / əlavə dəyər", "%"),
       "labour_share_VA": ("Əməyin payı / əlavə dəyər", "%"), "output": ("Buraxılış", "mln AZN")}
SEC_EN = {"B": "Mining", "C": "Manufacturing", "D": "Electricity", "E": "Water"}


def _fan(fan, ind, unit):
    f = fan[(fan.indicator == ind) & (fan.unit == unit)]
    if f.empty:
        return None
    f = f.set_index("year")
    return (C.yv(f.p5, C.YEARS), C.yv(f.p95, C.YEARS))


def _hist(cache, file, series, unit):
    if file is None:
        return {}
    if file not in cache:
        cache[file] = C.csv(file, dtype={"unit": str})
    h = cache[file]
    return h[(h.series == series) & (h.unit == unit)].set_index("year")["value"].to_dict()


def build(R):
    fb = C.csv("FR10_forecast_branches.csv")
    fb["code"] = fb.nace2.astype(int).map(lambda n: f"{n:02d}")
    fan = C.csv("FR10_fan_charts.csv", dtype={"unit": str})
    fan = fan[fan.year.astype(str).str.fullmatch(r"\d{4}")].copy()
    fan["year"] = fan.year.astype(int)
    hb = C.csv("FR10_holdout_branches.csv").set_index("branch")
    names_en = C.csv("FR10_branch_scorecard.csv", dtype={"nace2": str}).set_index("nace2")["branch"]
    cache = {}
    for (ind, code), g in fb.groupby(["indicator", "code"], sort=True):
        if ind not in IND:
            continue
        lab, unit, hf, hs, fanind = IND[ind]
        # FR10_forecast_branches.csv stores the two share indicators as FRACTIONS (0.079), while their history
        # (FR10_branch_shares_history.csv, *_pct) and the fan chart are in PERCENT: put the forecast on the % scale.
        mult = 100.0 if ind in ("share_of_industry", "share_of_manufacturing") else 1.0
        sc = {s: g[g.scenario == s].set_index("year")["value"] * mult for s in C.SC}
        base = g[(g.scenario == "Baseline") & (g.year == 2025)]["value"] * mult
        hold = None
        en = names_en.get(code)
        if ind == "output_nominal_mn_AZN" and en in hb.index:
            hold = {"rw": C.fnum(hb.loc[en, "U vs RW"]), "cg": C.fnum(hb.loc[en, "U vs CG"]),
                    "rmse": C.fnum(hb.loc[en, "model RMSE, nominal %"]), "win": "2020–2025", "src": "FR10_holdout_branches.csv"}
        R.add("FR10", "Sənaye sahələri (NACE)", f"{code} · {nace(code)}", unit, sc, var=lab,
              hist=_hist(cache, hf, hs, code), base=base.iloc[0] if len(base) else None,
              band=_fan(fan, fanind, code) if fanind else None, kind="rate" if unit == "%" else "lvl",
              src="FR10_forecast_branches.csv", info="FR10.branch", hold=hold)
    fs = C.csv("FR10_forecast_sections.csv")
    bh = C.csv("FR10_branch_history.csv", dtype={"unit": str})
    br = bh[(bh.series == "output_nominal_mn_AZN") & bh.unit.str.isdigit()].copy()
    br["sec"] = br.unit.astype(int).map(lambda n: "B" if n <= 9 else "C" if n <= 33 else "D" if n == 35 else "E")
    sec_out = br.pivot_table(index="year", columns="sec", values="value", aggfunc="sum")
    for sec in ["B", "C", "D", "E"]:
        m = fs[fs.sec == sec]
        for col, (lab, unit) in SEC.items():
            sc = {s: m[m.scenario == s].set_index("year")[col] for s in C.SC}
            base = m[(m.scenario == "Baseline") & (m.year == 2025)][col]
            hist = sec_out[sec].to_dict() if col == "output" else (
                _hist(cache, "FR10_branch_history.csv", "va_nominal_NA", sec) if col == "VA" else {})
            band = _fan(fan, "section output, mn AZN", SEC_EN[sec]) if col == "output" else (
                _fan(fan, "section GOS, % of value added", SEC_EN[sec]) if col == "GOS_share_VA" else None)
            R.add("FR10", "Sənaye bölmələri", nace(sec), unit, sc, var=lab, hist=hist, band=band,
                  base=base.iloc[0] if len(base) else None, kind="rate" if unit == "%" else "lvl",
                  src="FR10_forecast_sections.csv", info="FR10.section")
    tot = fs.groupby(["scenario", "year"])["output"].sum()
    R.add("FR10", "Sənaye bölmələri", "Sənaye, cəmi (4 bölmə)", "mln AZN",
          {s: tot.loc[s] for s in C.SC}, var="Buraxılış", hist=sec_out.sum(axis=1).to_dict(), base=tot.loc[("Baseline", 2025)],
          band=_fan(fan, "industry output, mn AZN", "Industry"), src="FR10_forecast_sections.csv (cəm)", info="FR10.section")
    _regions(R, fan)
    _concentration(R, fan)
    _products(R)


def _regions(R, fan):
    r = C.csv("FR10_forecast_regions.csv", header=[0, 1])
    sc_col, yr_col = r.columns[0], r.columns[1]
    r = r[r[sc_col].isin(list(C.SC))].copy()
    r["_s"], r["_y"] = r[sc_col], r[yr_col].astype(int)
    rh = C.csv("FR10_regional_history.csv")
    for kind, lab, unit, hser, mult in (("share", "Sənaye buraxılışında pay", "%", "share", 100),
                                        ("output_mn_AZN", "Sənaye buraxılışı", "mln AZN", "output_mn_AZN", 1)):
        for reg in [c[1] for c in r.columns if c[0] == kind]:
            sc = {s: (r[r._s == s].set_index("_y")[(kind, reg)].astype(float) * mult) for s in C.SC}
            hist = rh[(rh.series == hser) & (rh.unit == reg)].set_index("year")["value"]
            hist = (hist * (100 if kind == "share" and hist.max() <= 1.0 else 1)).to_dict()
            base = r[(r._s == "Baseline") & (r._y == 2025)][(kind, reg)]
            band = _fan(fan, "regional share of industrial output, %", reg) if kind == "share" else None
            R.add("FR10", "İqtisadi regionlar", region(reg), unit, sc, var=lab, hist=hist,
                  base=float(base.iloc[0]) * mult if len(base) else None, band=band,
                  kind="rate" if unit == "%" else "lvl", src="FR10_forecast_regions.csv", info="FR10.region")


def _concentration(R, fan):
    c = C.csv("FR10_concentration.csv", index_col=0)
    hist = c["HHI manufacturing branches"].loc[:2025].dropna().to_dict()
    R.add("FR10", "Bazar mövqeyi", "Emal sahələri üzrə HHI", "HHI (0–10 000)",
          {s: c[f"HHI manufacturing branches, {s}"] for s in C.SC}, hist=hist,
          band=_fan(fan, "HHI across manufacturing branches", "Manufacturing"), src="FR10_concentration.csv", info="FR10.hhi")
    o = C.csv("FR10_ownership.csv", index_col=0)
    R.add("FR10", "Bazar mövqeyi", "Qeyri-dövlət sektorunun sənayedə payı", "%",
          {s: o[f"forecast non-state share %, {s}"] for s in C.SC}, hist=o["published non-state share, %"].to_dict(),
          band=_fan(fan, "non-state share of industry, %", "Industry"), kind="rate", src="FR10_ownership.csv", info="FR10.own")


def _products(R):
    p = C.csv("FR10_product_forecasts_derived.csv", dtype={"branch": str})
    q = C.csv("FR10_products.csv").drop_duplicates("product").set_index("product")
    for r in p.itertuples(index=False):
        d = r._asdict()
        sc = {s: [d[f"{s}_{y}"] for y in C.YEARS] for s in C.SC}
        prod = d["product"]
        hist = {}
        if prod in q.index:
            hist = {2020: q.loc[prod, "2020"], 2025: q.loc[prod, "2025"]}
        unit = prod.rsplit(",", 1)[-1].strip() if "," in prod else ""
        R.add("FR10", "Məhsullar (natural ifadədə)", prod, unit, sc, hist=hist,
              src="FR10_product_forecasts_derived.csv", info="FR10.product",
              note=f"sahə: {nace(d['branch'])}" if isinstance(d["branch"], str) else "")
