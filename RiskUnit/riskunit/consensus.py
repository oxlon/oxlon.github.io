"""Cross-source baseline consensus (D3) and the forecast-disagreement "model risk" indicator.

For the shared headline variables the baselines of every unit are lined up for 2025–2030:
OxLon §15.5.1 (source=ours), Ministry CAEM, Ministry Bottom-up (base 60), Ministry 8-vərəq annex, MicroUnit FR1
and, where available, the IMF Art. IV reference / OxLon ministry-spec rows of forecast_long.

Statistics per (variable, year): n sources, min/max (and which source), spread = max − min, sd, cv = sd/|mean|,
disagreement_index = sd / scale where scale is the historical annual sd of the variable (rates: sd of the level
2010–2025 in OxLon actuals; levels: sd of annual % changes × |median|), i.e. "how many historical standard deviations
the units disagree by". Model-risk level: < 0,25 aşağı, 0,25–0,50 orta, ≥ 0,50 yüksək.

Implausibility rule (documented, applied in this order):
 1. bounds   — value outside the physically plausible range of the variable (BOUNDS)  → "qeyri-real: hədd"
 2. defect   — automatic checks of known upstream defects: Bottom-up CPI identical to the trade deflator row;
               CAEM current account while CAEM reserves turn negative                 → "qeyri-real: məlum qüsur"
 2b. stale   — for years ≤ LAST_ACTUAL a source still carrying an old projection that differs from the observed
               actual (kind=actual in OxLon / FR1) by more than floor/2                 → "köhnəlmiş"
 3. outlier  — with ≥ 3 sources: |x − median(others)| > max(3·1,4826·MAD(others), floor) → "kənar dəyər"
Flagged values stay in the table (transparency); "qeyri-real" and "köhnəlmiş" values are excluded from
spread_clean / disagreement_index_clean, while "kənar dəyər" values are kept there (an outlying unit is itself
forecast disagreement — the model risk we want to measure).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config, upstream

YEARS = list(range(2025, 2031))
SRC_LABEL = {"oxlon": "OxLon (makro §15.5.1)", "caem": "Nazirlik CAEM", "bu60": "Nazirlik Bottom-up (base 60)",
             "v8": "Nazirlik 8 vərəq", "fr1": "MicroUnit FR1", "imf": "BVF Art. IV (istinad)",
             "mspec": "OxLon: Nazirlik spesifikasiyası (FR13)"}
REF_SOURCES = {"imf", "mspec"}                  # reference rows: shown, not used in the outlier test of others

# selector: ("id", stable id, transform) or ("ref", workbook row_ref, transform); transform: level|growth|div1000
V = {
    "real_gdp_growth": ("Real ÜDM artımı", "%", "rate", {
        "oxlon": ("id", "mx:gdp_realg", "level"), "caem": ("ref", "CAEM.xlsx/6a. SEI!R9", "level"),
        "bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R6", "level"), "v8": ("ref", "8 vərəq.xlsx/2.4.1.1.!R5", "level"),
        "fr1": ("id", "fr1:rgdp", "growth"), "imf": ("id", "mx:imf:gdp_realg", "level")}),
    "nonoil_gdp_growth": ("Qeyri-neft ÜDM artımı", "%", "rate", {
        "oxlon": ("id", "mx:nonoil_realg", "level"), "caem": ("ref", "CAEM.xlsx/MOE_report!R38", "level"),
        "bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R13", "level"), "v8": ("ref", "8 vərəq.xlsx/2.4.1.1.!R12", "level"),
        "fr1": ("id", "fr1:rgdpnon", "growth"), "imf": ("id", "mx:imf:nonoil_realg", "level")}),
    "oilgas_gdp_growth": ("Neft-qaz ÜDM artımı", "%", "rate", {
        "oxlon": ("id", "mx:oil_realg", "level"), "caem": ("ref", "CAEM.xlsx/MOE_report!R34", "level"),
        "bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R9", "level"), "v8": ("ref", "8 vərəq.xlsx/2.4.1.1.!R8", "level"),
        "fr1": ("id", "fr1:rgdpoil", "growth")}),
    "cpi_inflation": ("İnflyasiya (İQİ, orta illik)", "%", "rate", {
        "oxlon": ("id", "mx:cpi_infl", "level"), "caem": ("ref", "CAEM.xlsx/6a. SEI!R19", "level"),
        "bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R124", "level"),
        "v8": ("ref", "8 vərəq.xlsx/2.4.1.5.-7.!R54", "level"), "fr1": ("id", "fr1:infl", "level"),
        "imf": ("id", "mx:imf:cpi_infl", "level"), "mspec": ("id", "mx:mspec:cpi_infl", "level")}),
    "brent_usd": ("Brent neftinin qiyməti (fərziyyə)", "ABŞ dolları/barel", "level", {
        "oxlon": ("id", "mx:brent_usd", "level"), "caem": ("ref", "CAEM.xlsx/Oil_and_gas_sector!R69", "level"),
        "bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R141", "level"),
        "v8": ("ref", "8 vərəq.xlsx/2.4.1.5.-7.!R4", "level"), "fr1": ("id", "fr1:exo:brent", "level")}),
    "oil_export_price": ("Neftin ixrac qiyməti", "ABŞ dolları/barel", "level", {
        "caem": ("ref", "CAEM.xlsx/Oil_and_gas_sector!R71", "level"), "fr1": ("id", "fr1:oil_exp_price", "level")}),
    "oil_production": ("Neft hasilatı", "mln ton", "level", {
        "oxlon": ("id", "mx:oilgas_q_oil_mkt", "level"), "caem": ("ref", "CAEM.xlsx/Oil_and_gas_sector!R20", "div1000"),
        "bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R75", "level"), "fr1": ("id", "fr1:exo:oil_prod", "level")}),
    "gas_production_mkt": ("Əmtəəlik qaz hasilatı", "mlrd m³", "level", {
        "oxlon": ("id", "mx:oilgas_q_gas_mkt", "level"), "caem": ("ref", "CAEM.xlsx/Oil_and_gas_sector!R37", "div1000"),
        "bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R86", "level")}),
    "gas_production_gross": ("Qaz hasilatı (ümumi)", "mlrd m³", "level", {
        "bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R81", "level"), "fr1": ("id", "fr1:exo:gas_prod", "level")}),
    "usd_azn": ("Manatın məzənnəsi", "AZN/ABŞ dolları", "level", {
        "oxlon": ("id", "mx:fx_usd_azn_avg", "level"), "caem": ("ref", "CAEM.xlsx/MOE_report!R122", "level"),
        "bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R140", "level"), "fr1": ("id", "fr1:exo:fx", "level")}),
    "state_budget_balance": ("Dövlət büdcəsinin balansı", "mln AZN", "level", {
        "caem": ("ref", "CAEM.xlsx/MOE_report!R97", "level"), "bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R92", "level"),
        "fr1": ("id", "fr1:balance_n", "level")}),
    "current_account_pct_gdp": ("Cari hesab balansı / ÜDM", "%", "rate", {
        "oxlon": ("id", "mx:ca_gdp_ratio", "level"), "caem": ("ref", "CAEM.xlsx/6a. SEI!R37", "level"),
        "bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R142", "level")}),
    "current_account_usd": ("Cari hesab balansı", "mln ABŞ dolları", "level", {
        "oxlon": ("id", "mx:current_account", "level"), "caem": ("ref", "CAEM.xlsx/MOE_report!R105", "level"),
        "bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R126", "level")}),
    "nominal_gdp": ("Nominal ÜDM", "mln AZN", "level", {
        "oxlon": ("id", "mx:gdp_nom", "level"), "caem": ("ref", "CAEM.xlsx/MOE_report!R29", "level"),
        "bu60": ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R4", "level"), "v8": ("ref", "8 vərəq.xlsx/2.4.1.1.!R4", "level"),
        "fr1": ("id", "fr1:gdp_n", "level")}),
}
BOUNDS = {"real_gdp_growth": (-15, 20), "nonoil_gdp_growth": (-15, 20), "oilgas_gdp_growth": (-25, 25),
          "cpi_inflation": (-3, 30), "brent_usd": (15, 200), "oil_export_price": (15, 200), "oil_production": (15, 45),
          "gas_production_mkt": (15, 70), "gas_production_gross": (20, 80), "usd_azn": (1.0, 3.5),
          "state_budget_balance": (-20000, 20000), "current_account_pct_gdp": (-12, 40),
          "current_account_usd": (-15000, 40000), "nominal_gdp": (80000, 400000)}
FLOOR = {"real_gdp_growth": 2.0, "nonoil_gdp_growth": 2.0, "oilgas_gdp_growth": 3.0, "cpi_inflation": 2.0,
         "brent_usd": 10.0, "oil_export_price": 10.0, "oil_production": 2.0, "gas_production_mkt": 3.0,
         "gas_production_gross": 3.0, "usd_azn": 0.1, "state_budget_balance": 1500.0, "current_account_pct_gdp": 4.0,
         "current_account_usd": 3000.0, "nominal_gdp": 12000.0}
SD_LEVEL = {"current_account_usd", "state_budget_balance"}     # cross zero: % changes meaningless → sd of level
HIST_ID = {"real_gdp_growth": "mx:gdp_realg", "nonoil_gdp_growth": "mx:nonoil_realg", "oilgas_gdp_growth": "mx:oil_realg",
           "cpi_inflation": "mx:cpi_infl", "brent_usd": "mx:brent_usd", "oil_export_price": "mx:brent_usd",
           "oil_production": "mx:oilgas_q_oil_mkt", "gas_production_mkt": "mx:oilgas_q_gas_mkt",
           "gas_production_gross": "mx:oilgas_q_gas_mkt", "usd_azn": "mx:fx_usd_azn_avg",
           "state_budget_balance": "fr1:balance_n", "current_account_pct_gdp": "mx:ca_gdp_ratio",
           "current_account_usd": "mx:current_account", "nominal_gdp": "mx:gdp_nom"}


def _pick(S: pd.DataFrame, sel) -> pd.DataFrame:
    how, key, tr = sel
    s = S[S["id"] == key] if how == "id" else S[S["row_ref"] == key]
    s = s[s["scenario"].isin(["Baseline", "ACTUAL"]) | s["source"].str.startswith("ministry")]
    if s.empty:
        return pd.DataFrame(columns=["year", "value", "kind", "sid"])
    s = s.assign(pri=(s["scenario"] == "Baseline").astype(int)).sort_values(["year", "pri"])
    s = s.drop_duplicates("year", keep="last").set_index("year")
    v, kind = s["value"].astype(float), s["kind"]
    if tr == "growth":
        v = (v / v.shift(1) - 1) * 100
    elif tr == "div1000":
        v = v / 1000
    out = pd.DataFrame({"value": v, "kind": kind, "sid": s["id"]}).reset_index()
    return out[out["year"].isin(YEARS)].dropna(subset=["value"])


def extract(S: pd.DataFrame | None = None) -> pd.DataFrame:
    S = upstream.store() if S is None else S
    rows = []
    for var, (lab, unit, typ, srcs) in V.items():
        for src, sel in srcs.items():
            d = _pick(S, sel)
            for r in d.itertuples():
                rows.append({"variable": var, "label_az": lab, "unit": unit, "type": typ, "source": src,
                             "source_az": SRC_LABEL[src], "year": int(r.year), "value": float(r.value),
                             "kind": r.kind, "upstream_id": r.sid, "ref": sel[1]})
    return pd.DataFrame(rows)


def hist_scale(S: pd.DataFrame, var: str) -> float:
    """Historical annual variability of the variable (2010–2025, after the oil-boom years): rates → sd of the level, levels → sd of the
    annual % change × |median level| (an absolute scale in the variable's unit)."""
    s = S[(S["id"] == HIST_ID[var]) & (S["scenario"] == "ACTUAL")].set_index("year")["value"].astype(float)
    s = s[(s.index >= 2010) & (s.index <= config.LAST_ACTUAL)].sort_index()
    if len(s) < 5:
        return FLOOR[var] * 2
    if V[var][2] == "rate" or var in SD_LEVEL:
        return float(s.std())
    return float((s.pct_change().dropna()).std() * abs(s.median()))


def _defects(S: pd.DataFrame, L: pd.DataFrame) -> dict[tuple[str, str], str]:
    out = {}
    cpi = _pick(S, ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R124", "level")).set_index("year")["value"]
    trd = _pick(S, ("ref", "MOE REPORT 3 PAGES.xlsx/base 60!R49", "level")).set_index("year")["value"]
    j = cpi.index.intersection(trd.index)
    if len(j) >= 3 and float((cpi[j] - trd[j]).abs().max()) < 0.01:
        out[("cpi_inflation", "bu60")] = "İQİ sətri ticarət deflyatoru (base 60 R49) ilə eynidir — qırıq keçid"
        v8 = _pick(S, ("ref", "8 vərəq.xlsx/2.4.1.5.-7.!R54", "level")).set_index("year")["value"]
        jj = v8.index.intersection(trd.index)
        if len(jj) >= 3 and float((v8[jj] - trd[jj]).abs().max()) < 0.01:
            out[("cpi_inflation", "v8")] = "8 vərəq İQİ sətri ticarət deflyatoru ilə eynidir — qırıq keçid"
    res = S[S["id"] == "mn:caem:sei:reserves_percent_of_gdp"]
    if len(res) and (res[res["year"].between(2025, 2030)]["value"] < 0).any():
        why = "CAEM ehtiyatları mənfiyə düşür (6a. SEI R40) — cari hesab yolu daxili ziddiyyətlidir"
        out[("current_account_pct_gdp", "caem")] = why
        out[("current_account_usd", "caem")] = why
    return out


def flag(L: pd.DataFrame, S: pd.DataFrame) -> pd.DataFrame:
    L = L.copy()
    L["flag"], L["flag_reason"] = "", ""
    defects = _defects(S, L)
    for i, r in L.iterrows():
        lo, hi = BOUNDS[r.variable]
        if not lo <= r.value <= hi:
            L.loc[i, ["flag", "flag_reason"]] = ["qeyri-real", f"hədd [{lo}; {hi}] xaricində"]
        elif (r.variable, r.source) in defects:
            L.loc[i, ["flag", "flag_reason"]] = ["qeyri-real", defects[(r.variable, r.source)]]
    for (var, yr), g in L.groupby(["variable", "year"]):          # 2b. stale vintage vs the observed actual
        act = g[g["kind"] == "actual"]["value"]
        if yr > config.LAST_ACTUAL or act.empty:
            continue
        ref = float(act.median())
        for i, r in g[(g["kind"] != "actual") & (g["flag"] == "")].iterrows():
            if abs(r.value - ref) > FLOOR[var] / 2:
                L.loc[i, ["flag", "flag_reason"]] = ["köhnəlmiş", f"{yr} faktiki ({ref:.4g}) ilə fərq {r.value - ref:+.3g} "
                                                                  "— mənbə əvvəlki vintajdır"]
    for (var, yr), g in L.groupby(["variable", "year"]):
        ok = g[(g["flag"] == "") & ~g["source"].isin(REF_SOURCES)]
        if len(ok) < 3:
            continue
        for i, r in ok.iterrows():
            oth = ok.drop(index=i)["value"]
            med = float(oth.median())
            mad = float((oth - med).abs().median()) * 1.4826
            thr = max(3 * mad, FLOOR[var])
            if abs(r.value - med) > thr:
                L.loc[i, ["flag", "flag_reason"]] = ["kənar dəyər", f"digər mənbələrin medianından {r.value - med:+.2f} "
                                                                     f"(hədd ±{thr:.2f})"]
    return L


def _level(x: float) -> str:
    if not np.isfinite(x):
        return "qiymətləndirilmir"
    return "aşağı" if x < 0.25 else ("orta" if x < 0.5 else "yüksək")


def build(S: pd.DataFrame | None = None) -> pd.DataFrame:
    """Wide D3 table: one row per (variable, year) with each source's value, statistics and flags."""
    S = upstream.store() if S is None else S
    L = flag(extract(S), S)
    rows = []
    for (var, yr), g in L.groupby(["variable", "year"], sort=False):
        lab, unit, typ, _ = V[var]
        sc = hist_scale(S, var)
        core = g[~g["source"].isin(REF_SOURCES)]
        clean = core[~core["flag"].isin(["qeyri-real", "köhnəlmiş"])]   # outliers stay: they ARE disagreement
        r = {"variable": var, "label_az": lab, "unit": unit, "year": int(yr)}
        for src in SRC_LABEL:
            x = g[g["source"] == src]
            r[f"v_{src}"] = float(x["value"].iloc[0]) if len(x) else np.nan
        for tag, d in (("", core), ("_clean", clean)):
            v = d["value"]
            r[f"n{tag}"] = int(v.size)
            r[f"min{tag}"], r[f"max{tag}"] = (float(v.min()), float(v.max())) if v.size else (np.nan, np.nan)
            r[f"spread{tag}"] = r[f"max{tag}"] - r[f"min{tag}"] if v.size else np.nan
            sd = float(v.std(ddof=0)) if v.size >= 2 else np.nan
            r[f"sd{tag}"] = sd
            r[f"disagreement_index{tag}"] = sd / sc if sc and np.isfinite(sd) else np.nan
        r["min_source"] = core.loc[core["value"].idxmin(), "source"] if len(core) else ""
        r["max_source"] = core.loc[core["value"].idxmax(), "source"] if len(core) else ""
        m = float(core["value"].mean()) if len(core) else np.nan
        r["cv"] = r["sd"] / abs(m) if typ == "level" and m and np.isfinite(r["sd"]) else np.nan
        r["hist_scale"] = sc
        r["model_risk"] = _level(r["disagreement_index_clean"])
        fl = g[g["flag"] != ""]
        r["flags"] = " | ".join(f"{SRC_LABEL[a]}: {b} ({c})" for a, b, c in zip(fl["source"], fl["flag"], fl["flag_reason"]))
        rows.append(r)
    D = pd.DataFrame(rows)
    L.to_csv(config.OUTPUT / "D3_consensus_long.csv", index=False, float_format="%.6g")
    D.to_csv(config.OUTPUT / "D3_consensus_baselines.csv", index=False, float_format="%.6g")
    return D


def model_risk(D: pd.DataFrame) -> pd.DataFrame:
    """Forecast-disagreement indicator per variable (2026–2030 mean of the clean disagreement index) —
    proposed as a new register risk 'Proqnoz qeyri-müəyyənliyi / model riski'."""
    f = D[D["year"] >= 2026]
    g = f.groupby(["variable", "label_az", "unit"], sort=False)
    M = g.agg(disagreement_index=("disagreement_index_clean", "mean"), disagreement_max=("disagreement_index_clean", "max"),
              spread_mean=("spread_clean", "mean"), n_sources=("n", "max"), n_flags=("flags", lambda x: int((x != "").sum()))
              ).reset_index()
    M["model_risk"] = M["disagreement_index"].map(_level)
    M["risk_id_teklif"] = "R-new (MOD)"
    M["risk_adi"] = "Proqnoz qeyri-müəyyənliyi / model riski"
    M["izah"] = ("Bölmələrin baza proqnozları arasında fərq tarixi dəyişkənliyin "
                 + M["disagreement_index"].map(lambda x: f"{x:.2f}".replace(".", ",") if np.isfinite(x) else "—")
                 + " mislidir; qiymətləndirmə üçün təmiz (bayraqsız) mənbələr götürülür")
    return M


def run(ctx: dict | None = None, verbose: bool = True) -> dict:
    from . import spine
    D = build()
    M = model_risk(D)
    M.to_csv(config.OUTPUT / "D3_model_risk.csv", index=False, float_format="%.4g")
    spine.register_output("D3_consensus_baselines.csv", "consensus",
                          "Bölmələrarası baza proqnozları (OxLon, CAEM, Bottom-up, 8 vərəq, FR1, BVF) 2025–2030: hər mənbənin "
                          "dəyəri, yayılma (maks−min), fikir ayrılığı indeksi, qeyri-real/köhnəlmiş/kənar mənbə bayraqları",
                          list(D.columns), "yuxarı axın yeni vintaj verdikdə")
    spine.register_output("D3_consensus_long.csv", "consensus", "D3-ün uzun forması: dəyişən × il × mənbə, bayraq və səbəb",
                          ["variable", "year", "source", "value", "kind", "flag", "flag_reason", "upstream_id", "ref"],
                          "yuxarı axın yeni vintaj verdikdə")
    spine.register_output("D3_model_risk.csv", "consensus",
                          "Model riski göstəricisi (proqnoz fikir ayrılığı) — reyestr üçün təklif: «Proqnoz qeyri-müəyyənliyi / "
                          "model riski»", list(M.columns), "yuxarı axın yeni vintaj verdikdə")
    if verbose:
        for r in M.itertuples():
            print(f"  {r.label_az:38s} fikir ayrılığı {r.disagreement_index:5.2f} → {r.model_risk:8s} bayraq {r.n_flags}")
    return {"consensus": D, "model_risk": M}


if __name__ == "__main__":
    run()
