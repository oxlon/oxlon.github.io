"""Writes the IO engine outputs (P2_*, V_io_*, D_io_*) and registers them in output/_catalog.csv.

CLI: python3 -m policyunit.io_outputs     (offline-safe; ~10 s)
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from . import catalog
from . import config
from . import eng_io as E
from . import io_data as D
from . import io_models as M
from . import io_validate as V

OWNER = "io"


def _w(df, name, desc):
    return catalog.write_csv(df, name, OWNER, desc)


def _models():
    return {"2021": E.model(2021), "2025": E.model(2025)}


def sector_table(m) -> pd.DataFrame:
    s = D.sectors().set_index("code")
    return pd.DataFrame({"sector": m.codes, "name_az": [s.loc[c, "name_az"] for c in m.codes]})


def multipliers(ms):
    out = []
    for lab, m in ms.items():
        d = m.multipliers().reset_index().rename(columns={"index": "sector"})
        d.insert(0, "table", m.label)
        d.insert(2, "name_az", sector_table(m)["name_az"].to_numpy())
        d["rank_output_I"] = d["output_I"].rank(ascending=False).astype(int)
        d["rank_emp_I"] = d["emp_I"].rank(ascending=False).astype(int)
        out.append(d)
    return pd.concat(out, ignore_index=True)


def linkages(ms):
    out = []
    for lab, m in ms.items():
        lk = m.linkages().join(m.extraction())
        d = lk.reset_index().rename(columns={"index": "sector"})
        d.insert(0, "table", m.label)
        d.insert(2, "name_az", sector_table(m)["name_az"].to_numpy())
        out.append(d)
    return pd.concat(out, ignore_index=True)


def key_sectors(lk):
    d = lk[lk.table == lk.table.iloc[-1]].copy()
    d["rank_bl"] = d["bl_index"].rank(ascending=False).astype(int)
    d["rank_fl"] = d["fl_index"].rank(ascending=False).astype(int)
    d["rank_extraction"] = d["extract_total_pct"].rank(ascending=False).astype(int)
    d = d.sort_values(["key", "rank_extraction"])
    return d[["table", "sector", "name_az", "key", "bl_index", "fl_index", "rank_bl", "rank_fl",
              "extract_total_pct", "extract_backward_pct", "extract_forward_pct", "rank_extraction",
              "own_output_share_pct"]]


def fr10_link() -> pd.DataFrame:
    p = D.MP / "MicroUnit" / "output" / "FR10_branch_scorecard.csv"
    if not p.exists():
        return pd.DataFrame()
    b = pd.read_csv(p, dtype={"nace2": str})
    b["nace2"] = b["nace2"].str.zfill(2)
    s = D.sectors()
    lut = {d: r["code"] for _, r in s.iterrows() for d in r["fr10_branch_map"].split(";") if d}
    b["sector"] = b["nace2"].map(lut)
    b = b.dropna(subset=["sector"])
    w = b["share_of_industry_2025_pct"].fillna(0)
    g = b.assign(w=w)
    agg = g.groupby("sector").apply(lambda x: pd.Series({
        "fr10_share_of_industry_2025_pct": x["w"].sum(),
        "fr10_lp_2025_thsd_azn": np.average(x["lp_2025_thsd_AZN"].fillna(0), weights=x["w"] + 1e-9),
        "fr10_nonstate_share_2025_pct": np.average(x["nonstate_share_2025_pct"].fillna(0), weights=x["w"] + 1e-9),
        "fr10_forecast_growth_2026_30_pct_pa": np.average(x["forecast_real_growth_2026_30_pct_pa"].fillna(0), weights=x["w"] + 1e-9),
        "fr10_branches": ";".join(x["nace2"])}), include_groups=False)
    return agg.reset_index()


def competitiveness(ms):
    out = []
    f10 = fr10_link()
    for lab, m in ms.items():
        d = m.competitiveness().reset_index().rename(columns={"index": "sector"})
        d.insert(0, "table", m.label)
        d.insert(2, "name_az", sector_table(m)["name_az"].to_numpy())
        if len(f10):
            d = d.merge(f10, on="sector", how="left")
        out.append(d)
    return pd.concat(out, ignore_index=True)


UNIT_SHOCKS = [("fuel_price", 10, None), ("elec_tariff", 10, None), ("gas_tariff", 10, None),
               ("water_tariff", 10, None), ("labour_cost", 10, None), ("fx_deval", 10, None),
               ("import_tariff", 5, None), ("vat_rate", 1, None), ("product_tax", 5, "FOOD")]


def price_unit_shocks(m):
    rows = []
    for iid, size, tgt in UNIT_SHOCKS:
        sp = E._new_spec(m.n)
        E.HANDLERS[{"elec_tariff": "elec_tariff", "gas_tariff": "gas_tariff", "water_tariff": "water_tariff",
                    "labour_cost": "labour_cost", "product_tax": "product_tax"}.get(iid, iid)](m, sp, size, tgt, {})
        res = E.solve_year(m, sp)
        for j, c in enumerate(m.codes):
            rows.append({"shock": iid, "size": size, "target": tgt or "", "sector": c,
                         "dp_basic_pct": res["pr"]["dp"][j] * 100,
                         "dp_consumer_item_pct": res["cpi"][c] * 100})
        rows.append({"shock": iid, "size": size, "target": tgt or "", "sector": "CPI",
                     "dp_basic_pct": np.nan, "dp_consumer_item_pct": res["cpi"]["CPI"] * 100})
    return pd.DataFrame(rows)


def ghosh_forward(m):
    rows = []
    for k in ["ENERGY", "PETR", "OILGAS", "TRANS", "AGR"]:
        d = m.supply_shock(k, -0.10)
        for c, r in d.iterrows():
            rows.append({"shocked_sector": k, "shock_pct": -10, "sector": c,
                         "dx_mln": r["dx"] / 1e3, "dx_pct": r["dx_pct"]})
    return pd.DataFrame(rows)


def table_long(m):
    t = m.t
    d = pd.DataFrame(t.Z / 1e3, index=t.codes, columns=t.codes)
    for k in D.FD_KEYS:
        d[f"fd_{k}"] = t.fd[k].to_numpy() / 1e3
    d["imports"] = t.imp / 1e3
    d["output"] = t.x / 1e3
    d["import_share_s"] = m.s_imp
    va = t.va.loc[D.VA_KEYS].T / 1e3
    va.columns = [f"va_{c}" for c in va.columns]
    d = d.join(va)
    d["net_product_taxes_paid"] = t.tax / 1e3
    d.insert(0, "table", m.label)
    return d.reset_index().rename(columns={"index": "sector"})


DEMOS = [
    {"id": "io_demo_pub_invest", "name_az": "Dövlət əsaslı investisiyası +1 mlrd AZN (2026)",
     "start_year": 2026, "instruments": [{"instrument": "pub_invest", "size": 1000, "years": [2026]}]},
    {"id": "io_demo_construction", "name_az": "Bərpa tikintisi proqramı +1 mlrd AZN (yalnız tikinti)",
     "start_year": 2026, "instruments": [{"instrument": "pub_invest", "size": 1000, "years": [2026],
                                          "target": "CONS"}]},
    {"id": "io_demo_export_man", "name_az": "Emal sənayesi ixracına subsidiya 200 mln AZN",
     "start_year": 2026, "instruments": [{"instrument": "export_subsidy", "size": 200, "years": [2026],
                                          "target": "man"}]},
    {"id": "io_demo_fuel20", "name_az": "Tənzimlənən yanacaq qiymətləri +20 %",
     "start_year": 2026, "instruments": [{"instrument": "fuel_price", "size": 20, "years": [2026]}]},
    {"id": "io_demo_utility10", "name_az": "Elektrik, qaz və su tarifləri +10 %",
     "start_year": 2026, "instruments": [{"instrument": "utility_tariff", "size": 10, "years": [2026]}]},
    {"id": "io_demo_tariff5", "name_az": "Malların idxal rüsumu +5 f.b.",
     "start_year": 2026, "instruments": [{"instrument": "import_tariff", "size": 5, "years": [2026]}]},
    {"id": "io_demo_agri_tfp", "name_az": "Kənd təsərrüfatında məhsuldarlıq +5 %",
     "start_year": 2026, "instruments": [{"instrument": "sector_productivity", "size": 5, "years": [2026],
                                          "target": "AGR"}]},
    {"id": "io_demo_energy_cut", "name_az": "Enerji təchizatı şoku −10 % (Ghosh)",
     "start_year": 2026, "instruments": [{"instrument": "sector_supply_shock", "size": -10,
                                          "years": [2026], "target": "ENERGY"}]},
]


def config_scenarios():
    """Scenario JSON files of the core agent that use at least one IO-adapted instrument."""
    out = []
    try:
        from . import scenario as S
        ad = set(E._adapters()["instrument"])
        for sid in S.all_ids():
            try:
                s = S.load(sid)
            except Exception:
                continue
            if any(it["instrument"] in ad for it in s["instruments"]):
                out.append(s)
    except Exception:
        pass
    return out


def scenarios_frame():
    frames, aff = [], []
    for s in DEMOS + config_scenarios():
        r = E.run(s, {"io_table": 2025})
        f = r.frame.copy()
        if not len(f):
            continue
        f.insert(0, "scenario", s["id"])
        f.insert(1, "scenario_name_az", s.get("name_az", ""))
        frames.append(f)
        y0 = int(f["year"].min())
        g = f[(f.year == y0) & (f.group != "ümumi")].copy()
        g["kind"] = g["indicator"].str.split(":").str[0].map(
            {"io_output": "buraxılış", "io_va": "əlavə dəyər", "io_emp": "məşğulluq",
             "io_price": "qiymət", "io_output_ghosh": "buraxılış (Ghosh)"})
        g["abs_pct"] = g["delta_pct"].abs()
        g["rank"] = g.groupby("kind")["abs_pct"].rank(ascending=False, method="first").astype(int)
        g = g[g["abs_pct"] > 1e-3]
        aff.append(g[["scenario", "scenario_name_az", "year", "group", "kind", "delta_pct", "delta",
                      "unit", "rank", "method"]].rename(columns={"group": "sector"}))
    sc = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    af = pd.concat(aff, ignore_index=True) if aff else pd.DataFrame()
    if len(af):
        names = D.sectors().set_index("code")["name_az"]
        af.insert(4, "name_az", af["sector"].map(names))
        af = af.sort_values(["scenario", "kind", "rank"])
    return sc, af


def main(argv=None):
    config.ensure_dirs()
    ms = _models()
    m25 = ms["2025"]
    written = []
    sm = D.aggregate(D.load_iot(2021))
    pm = pd.DataFrame({"cpa": D.load_iot(2021).codes, "product_name_en": D.load_iot(2021).names})
    pm["sector"] = D.product_map(list(pm["cpa"]))
    written.append(_w(pm, "D_io_sector_map.csv", "CPA məhsulları (81) → IO sektoru (23) xəritəsi (DSK 2021 IOT)"))
    written.append(_w(pd.concat([table_long(ms["2021"]), table_long(m25)]), "D_io_tables.csv",
                      "Aqreqasiya olunmuş IO cədvəlləri (2021 benchmark və 2025 GRAS), mln AZN, əsas qiymətlər"))
    written.append(_w(multipliers(ms), "P2_io_multipliers.csv",
                      "Buraxılış, əlavə dəyər, əmək ödənişi, məşğulluq (nəfər / 1 mln AZN), idxal multiplikatorları — tip I və II"))
    lk = linkages(ms)
    written.append(_w(lk, "P2_io_linkages.csv", "Rasmussen geri/irəli əlaqə indeksləri, dispersiya, hipotetik çıxarma"))
    written.append(_w(key_sectors(lk), "P2_io_key_sectors.csv", "Açar sektorlar (BL>1 və FL>1) və çıxarma itkisi üzrə rütbələr (2025)"))
    written.append(_w(competitiveness(ms), "P2_io_competitiveness.csv",
                      "Rəqabətlilik: vahid əmək xərci, məhsuldarlıq, idxal nüfuzu, ixrac yönümü, ixracda yaradılan əlavə dəyər; FR10 emal sahələri ilə əlaqə"))
    written.append(_w(price_unit_shocks(m25), "P2_io_price_shocks.csv",
                      "Vahid qiymət şokları (yanacaq, elektrik, qaz, su, əmək xərci, məzənnə, rüsum, ƏDV, aksiz) → sektor qiymətləri və İQİ"))
    written.append(_w(ghosh_forward(m25), "P2_io_ghosh_supply.csv",
                      "Ghosh təklif modeli: −10 % təklif şokunun irəli ötürülməsi (məhdud şərh)"))
    from . import io_update as U
    t, diag, info = U.update(sm, 2025)
    diag.insert(0, "year", 2025)
    written.append(_w(diag, "P2_io_update_2025.csv", "GRAS yeniləməsi 2021→2025: hədəflər (FR1, DSK 027) və nəticələr, min AZN"))
    written.append(_w(pd.DataFrame([{k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in info.items()}]),
                      "P2_io_update_info.csv", "GRAS yığılması: iterasiya sayı, qalıq, MH uyğunsuzluğu"))
    sc, af = scenarios_frame()
    written.append(_w(sc, "P2_io_scenarios.csv", "IO alətli ssenarilərin nəticələri (harmonizə edilmiş çıxış formatı)"))
    written.append(_w(af, "P2_io_affected_sectors.csv",
                      "FR2 qəbul formatı: təsirlənən sektorlar və hər biri üzrə faiz dəyişimi, rütbə"))
    st, ss = [], []
    for a, b in [(2016, 2021), (2011, 2016)]:
        df, s = V.stability(a, b)
        st.append(df)
        ss.append(s)
    written.append(_w(pd.concat(st), "V_io_stability.csv", "IO əmsallarının sabitliyi: sektor buraxılışının geriyə proqnozu (2016→2021, 2011→2016)"))
    written.append(_w(pd.DataFrame(ss), "V_io_stability_summary.csv", "Sabitlik testi xülasəsi: RMSE, MAPE, çəkili MAPE, sadə etalonla müqayisə"))
    dev, sect = V.e7_fuel(2021)
    written.append(_w(dev, "V_io_e7_fuel_2024.csv", "E7 (30.06.2024 yanacaq və tarif paketi): IO qiymət modeli vs DSK İQİ, sapma hesabatı"))
    written.append(_w(sect, "V_io_e7_sectors.csv", "E7: sektor əsas qiymətləri və İQİ maddələri üzrə model təsiri"))
    written.append(_w(V.e7_sensitivity(), "V_io_e7_sensitivity.csv", "E7: yanacaq qarışığı çəkiləri və cədvəl ili üzrə həssaslıq"))
    D.write_manifest()
    for p in written:
        print("yazıldı:", p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
