"""NFR2 method comparison (N2_): for each scenario × concept × horizon where ≥2 methods give a value —
each method's headline effect, spread, sign agreement and a short Azerbaijani explanation.
Methods: core = MikroUnit chain (+ long-run extension after 2030), caem, oxlon, io, microsim."""
from __future__ import annotations

import math

import pandas as pd

from . import integrate as I, registry

METHODS = ["micro", "caem", "oxlon", "riskfx", "io", "microsim"]
NAME = {"micro": "MikroUnit", "caem": "CAEM", "oxlon": "OxLon", "riskfx": "RiskUnit FX", "io": "IO",
        "microsim": "mikrosimulyasiya"}
BASE = ["gdp_real", "gdp_nonoil_real", "cpi", "infl", "unemp_rate", "employment", "employment_hired",
        "wage_nominal", "wage_real", "hh_disp_real", "cons_real", "exports_nonoil_real", "budget_balance_pct",
        "debt_pct", "gini", "poverty_rate", "poverty_gap"]
PREFIX = ("sector_va:", "sector_emp:", "sector_hired:", "sector_price:")
GROUP = {"gdp_real": "gdp", "gdp_nonoil_real": "gdp", "cons_real": "gdp", "exports_nonoil_real": "gdp",
         "cpi": "price", "infl": "price", "unemp_rate": "labour", "employment": "labour",
         "employment_hired": "labour", "wage_nominal": "labour", "wage_real": "labour", "hh_disp_real": "social",
         "budget_balance_pct": "fiscal", "debt_pct": "fiscal", "gini": "social", "poverty_rate": "social",
         "poverty_gap": "social"}
REASON = {
    ("caem", "gdp"): "CAEM-də parametrlər kalibrlənib, fiskal blok gəlir dəyişməsini xərcə ötürür və uçot dərəcəsi "
                     "endogen reaksiya verir; FR1-də pul siyasəti ekzogendir, idxal sızması (D4) və sektor tənlikləri "
                     "Azərbaycan məlumatı ilə qiymətləndirilib",
    ("caem", "labour"): "FR1 ümumi (İQS) məşğulluğun ÜDM-ə elastikliyi kiçikdir (E1 ≈ 0,034) — formal iş yerləri FR4 muzdlu "
                        "işçilərdə; CAEM Okun qanunu ilə işsizliyə daha güclü ötürür",
    ("caem", "price"): "CAEM-də inflyasiya Phillips əyrisi və uçot dərəcəsinin reaksiyası ilə söndürülür; FR1-də İQİ "
                       "maaş (E2) və məzənnə kanalları ilə, pul siyasəti reaksiyası olmadan",
    ("caem", "fiscal"): "CAEM-də pb_y ilkin balansdır və kapital xərci (gcap_y) ilkin balansa/borca yazılmır; FR1 balansı "
                        "ümumi balansdır, borc kumulyativ kəsirlə artır",
    ("caem", "social"): "CAEM-də ev təsərrüfatı gəliri ayrıca yoxdur",
    ("io", "gdp"): "IO sabit əmsallı, tələb yönümlü modeldir: qiymət, sıxışdırma və təklif məhdudiyyəti yoxdur — adətən "
                   "yuxarı hədd; FR1 sektor tənlikləri sürücülərlə (istehlak, investisiya, ixrac) qiymətləndirilib",
    ("io", "sector"): "IO sektorlararası aralıq istehlak əlaqələrini (geri/irəli əlaqə) birbaşa izləyir; FR1/FR4 sektor "
                      "nəticələri makro sürücülərdən paylanır — sektor bölgüsündə fərq gözləniləndir",
    ("io", "price"): "IO Leontief qiymət modeli tam xərc ötürülməsini (marja sabit) fərz edir; FR1 overlay ötürmə payı ilə",
    ("io", "labour"): "IO məşğulluq əmsalları sabitdir (məhsuldarlıq dəyişmir); FR1/FR4 elastiklikləri qiymətləndirilib",
    ("oxlon", "price"): "OxLon FR13 (Nazirliyin tənlik kataloqu) yalnız 16 sıra verir; məzənnənin İQİ-yə ötürülməsi orada zəifdir",
    ("oxlon", "labour"): "OxLon FR13 qeyri-neft maaşını ayrıca tənliklə verir",
    ("microsim", "social"): "Mikrosimulyasiya statik ilk raund vergi-müavinət hesablamasıdır (SİNTETİK ev təsərrüfatları): "
                            "paylanma (desil, Gini, yoxsulluq) fərqlərini göstərir, makro geri əlaqə yoxdur",
    ("microsim", "labour"): "Mikrosimulyasiya MikroUnit maaş yollarını İSTİFADƏ ETMİR: minimum əmək haqqında yalnız yeni "
                            "minimumdan aşağı qazananları ona qaldıran statik döşəmədir (yuxarı maaşlara ötürmə yoxdur, "
                            "yalnız etiketli spill-over seçimi aktiv olduqda); MikroUnit E2 tənliyi bütün maaş paylanmasının "
                            "və İQİ-nin makro reaksiyasını verir — iki rəqəm diapazonun aşağı və yuxarı sərhədidir",
    ("riskfx", "price"): "RiskUnit FX ötürməsi 2015–17 epizoduna kalibrlənib (cəmi 0,30, hadisə ilində 68 %) və FR4 üçün "
                         "əsas mənbədir; FR1 zəncirində İQİ-yə məzənnə ötürülməsi zəifdir (G4: dln_fx 0,04 + 0,13) — "
                         "2015 devalvasiyası RiskUnit kalibrləməsi üçün nümunədaxilidir",
    ("riskfx", "gdp"): "RiskUnit qeyri-neft səviyyə itkisi 2015–16 analoqundandır (neft və investisiya kanalları çıxılıb)",
    ("riskfx", "fiscal"): "RiskUnit yalnız xarici borcun yenidənqiymətləndirilməsini verir; FR1 neft gəlirinin AZN artımını "
                          "və fiskal qaydaların xərc reaksiyasını",
}


def _group(ind: str) -> str:
    return "sector" if ind.startswith(PREFIX) else GROUP.get(ind, "gdp")


def _io_alias(g: pd.DataFrame) -> pd.DataFrame:
    """IO ids -> comparable concepts: io_va_total->gdp_real, io_cpi->cpi, io_va:<code> summed to the FR1
    group (sector_va:<fr1>), io_emp:<code> summed to a single FR4 section (sector_emp:<fr4>)."""
    if g.empty:
        return g
    from . import config
    alias = g[g.indicator.isin(["io_va_total", "io_cpi"])].copy()
    alias["indicator"] = alias["indicator"].map({"io_va_total": "gdp_real", "io_cpi": "cpi"})
    parts = [g[~g.indicator.isin(["gdp_real", "cpi"])], alias]
    if config.IO_SECTORS_CSV.exists():
        sec = pd.read_csv(config.IO_SECTORS_CSV, dtype=str).fillna("")
        for pref, col, new in (("io_va:", "fr1_group", "sector_va:"), ("io_emp:", "fr4_sector_map", "sector_emp:")):
            mp = {r.code: getattr(r, col) for r in sec.itertuples() if getattr(r, col) and ";" not in getattr(r, col)}
            x = g[g.indicator.str.startswith(pref)].copy()
            x["grp"] = x.indicator.str[len(pref):].map(mp)
            x = x.dropna(subset=["grp"])
            if x.empty:
                continue
            a = x.groupby(["grp", "year", "horizon"], as_index=False)[["baseline", "value"]].sum()
            a["indicator"] = new + a["grp"]
            a["delta"] = a["value"] - a["baseline"]
            a["delta_pct"] = 100 * a["delta"] / a["baseline"]
            a["label_az"] = new + a["grp"] + " (IO, toplanmış)"
            a["tier"], a["engine"] = x.tier.iloc[0], "io"
            parts.append(a.drop(columns="grp"))
    return pd.concat(parts, ignore_index=True)


def _frames(fs: pd.DataFrame) -> dict:
    out = {"micro": I.core_frame(fs)}
    for m in METHODS[1:]:
        out[m] = fs[fs.engine == m]
    out["io"] = _io_alias(out["io"])
    return out


def explain(ind, vals: dict, proxy: bool, tax: bool) -> str:
    ms = [m for m, v in vals.items() if v is not None and not math.isnan(v)]
    tol = 0.005
    nz = [vals[m] for m in ms if abs(vals[m]) > tol]
    parts = []
    if len(nz) < len(ms) and nz:
        zero = [m for m in ms if abs(vals[m]) <= tol]
        parts.append(f"{', '.join(NAME[m] for m in zero)} bu göstəriciyə praktik olaraq təsir göstərmir (|təsir| ≤ {tol}).")
    if len(nz) >= 2:
        parts.append("İşarələr uyğundur." if all(v > 0 for v in nz) or all(v < 0 for v in nz)
                     else "İşarələr fərqlidir.")
        lo, hi = sorted(abs(v) for v in nz)[0], sorted(abs(v) for v in nz)[-1]
        if lo > 0 and hi / lo >= 1.5:
            parts.append(f"Ölçü fərqi ~{hi / lo:.1f} dəfə.")
    g = _group(ind)
    for m in ms:
        if m != "micro" and (m, g) in REASON:
            parts.append(REASON[(m, g)] + ".")
    if proxy:
        parts.append("MikroUnit nəticəsi bu alət üçün proksidir (FR1 elastiklikləri ilə overlay, sübut səviyyəsi D).")
    if tax and "caem" in ms:
        parts.append("CAEM-də vergi şoku yalnız büdcə kanalı ilə işləyir (qiymət/gəlir kanalı yoxdur): gəlir itkisi "
                     "xərclərin azalmasına çevrilir, ona görə vergi endirimi orada daralmaya səbəb ola bilər.")
    return " ".join(parts)


def table(f: pd.DataFrame, scenarios: dict) -> pd.DataFrame:
    rows = []
    for sid, fs in f.groupby("scenario", sort=False):
        fr = _frames(fs)
        s = scenarios.get(sid, {})
        fams = {registry.instrument(it["instrument"])["family"] for it in s.get("instruments", [])}
        proxy = (fs[fs.engine == "micro"].tier == "D").any()
        inds = [i for i in sorted(set(fs.indicator)) if i in BASE or i.startswith(PREFIX)]
        for ind in inds:
            for hz in ("qısa", "orta", "uzun"):
                vals, label, yrs = {}, "", ""
                for m, g in fr.items():
                    g = g[(g.indicator == ind) & (g.horizon == hz)]
                    if g.empty or g["delta_pct"].isna().all() and g["delta"].isna().all():
                        continue
                    vals[m] = I.effect(g, ind)
                    label = label or g.label_az.iloc[0]
                    yrs = yrs or f"{g.year.min()}–{g.year.max()}"
                vals = {m: v for m, v in vals.items() if v is not None and not math.isnan(v)}
                if len(vals) < 2:
                    continue
                v = list(vals.values())
                r = {"scenario": sid, "scenario_name": fs.scenario_name.iloc[0], "indicator": ind,
                     "label_az": label, "horizon": hz, "years": yrs, "effect_unit": I._eff_unit(ind),
                     "methods": ";".join(vals)}
                r.update({m: round(vals[m], 4) if m in vals else None for m in METHODS})
                nz = [x for x in v if abs(x) > 0.005]
                r["spread"] = round(max(v) - min(v), 4)
                r["sign_agree"] = (all(x > 0 for x in nz) or all(x < 0 for x in nz)) if nz else None
                r["explanation_az"] = explain(ind, vals, proxy and "micro" in vals, "vergi" in fams)
                bad = fr["caem"][(fr["caem"].indicator == ind) & fr["caem"].note_az.astype(str).str.contains("ETİBARSIZ")]
                r["caem_reliable"] = "" if "caem" not in vals else ("bəli" if bad.empty else "xeyr")
                if "caem" in vals and not bad.empty:
                    r["explanation_az"] += (" CAEM-in bu fiskal nəticəsi ETİBARSIZDIR (vergi şokunda balans/borc işarə "
                                            "uyğunsuzluğu) — fiskal KPI-lardan çıxarılıb.")
                rows.append(r)
    return pd.DataFrame(rows)
