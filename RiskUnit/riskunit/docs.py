"""Methodology document upkeep: every number in docs/Risk_Metodologiyasi.md sits between
<!-- AUTO:tag --> ... <!-- /AUTO:tag --> markers and is regenerated from the run's outputs,
so the document cannot drift from the results (same convention as the §15.5.2 micro unit)."""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from . import config
from .charts import az

DOC = config.DOCS / "Risk_Metodologiyasi.md"


def _md(df: pd.DataFrame, num: dict | None = None) -> str:
    num = num or {}
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "|".join("---:" if c in num else "---" for c in df.columns) + "|\n"
    rows = []
    for r in df.itertuples(index=False):
        cells = [az(float(v), num[c]) if c in num and pd.notna(v) else ("—" if (isinstance(v, float) and np.isnan(v)) else str(v))
                 for c, v in zip(df.columns, r)]
        rows.append("| " + " | ".join(cells) + " |")
    return head + "\n".join(rows)


def blocks(c: dict) -> dict[str, str]:
    S, res, p = c["S"], c["res"], c["p"]
    j = res.col(res.score_year)
    g = res.total("g")[:, j]
    out = {}
    out["status"] = (f"Vəziyyət tarixi **{c['live']['as_of']}**, qiymətləndirmə ili **{res.score_year}**, baza identifikatoru "
                     f"**{c['baseline_id']}**. Birgə simulyasiya: {res.meta['n']} ssenari, butstrap illəri "
                     f"{res.meta['bootstrap_years']}. Qeyri-neft artımı {res.score_year}: median {az(float(np.median(g)), 2)}%, "
                     f"P10 {az(float(np.quantile(g, .1)), 2)}%, P5 {az(float(np.quantile(g, .05)), 2)}% (makro baza "
                     f"{az(res.base['g'][j], 2)}%). Yüksək prioritetli risklər: "
                     f"{', '.join(S[S['prioritet'] == 'yüksək']['risk_id'])}; xəbərdarlıq sayı {len(c['alerts'])}.")
    ch = pd.read_csv(config.OUTPUT / "FR1_transmission_channels.csv")
    out["fr1_channels"] = _md(ch[["izah", "izahedici", "emsal", "st_xeta", "p", "n", "nümunə", "sübut"]]
                              .rename(columns={"izah": "Kanal", "izahedici": "İzahedici", "emsal": "Əmsal", "st_xeta": "St. xəta",
                                               "nümunə": "Nümunə", "sübut": "Sübut"}),
                              num={"Əmsal": 3, "St. xəta": 3, "p": 3, "n": 0})
    hz = c["hazards"]
    out["fr1_hazards"] = (f"Zəlzələ: M 5,5–6,0 — {hz['eq_n_tier1']} epizod, λ = {az(hz['eq_lambda_tier1'], 3)}/il; M ≥ 6,0 — "
                          f"{hz['eq_n_tier2']} epizod, λ = {az(hz['eq_lambda_tier2'], 3)}/il ({az(hz['eq_years'], 1)} il). "
                          f"Quraqlıq: P(SPI ≤ {az(p['spi_threshold'], 1)}) = {az(hz['p_drought'] * 100, 1)}%; son 12 ayın SPI-si "
                          f"{az(hz['spi_now'], 2)} ({hz['spi_now_end']}).")
    t = S[["sira", "risk_id", "ad", "ehtimal", "tesir_g", "tesir_cpi", "tesir_fis", "P_bal", "I_bal", "skor", "prioritet",
           "quyruq_tohfesi"]].copy()
    t["ehtimal"] *= 100
    out["fr2_scores"] = _md(t.rename(columns={"sira": "№", "risk_id": "ID", "ad": "Risk", "ehtimal": "Ehtimal %",
                                              "tesir_g": "Qeyri-neft f.b.", "tesir_cpi": "İnflyasiya f.b.",
                                              "tesir_fis": "Büdcə % ÜDM", "P_bal": "P", "I_bal": "T", "skor": "Skor",
                                              "prioritet": "Prioritet", "quyruq_tohfesi": "Quyruq töhfəsi f.b."}),
                            num={"Ehtimal %": 1, "Qeyri-neft f.b.": 2, "İnflyasiya f.b.": 2, "Büdcə % ÜDM": 2,
                                 "Quyruq töhfəsi f.b.": 2})
    C = c["contrib_g"][["ad", "dispersiya_payi", "quyruq_tohfesi_merkezlesmis"]].copy()
    C["dispersiya_payi"] *= 100
    out["fr2_contrib"] = _md(C.rename(columns={"ad": "Kanal", "dispersiya_payi": "Dispersiya payı %",
                                               "quyruq_tohfesi_merkezlesmis": "P10 quyruğunda töhfə f.b."}),
                             num={"Dispersiya payı %": 1, "P10 quyruğunda töhfə f.b.": 2})
    st = c["stress"]
    s2 = st[(st["il"] == res.score_year)].pivot_table(index=["ssenari", "ad"], columns="gosterici",
                                                      values=["sapma", "tedbirin_effekti"]).reset_index()
    s2.columns = [" ".join(map(str, x)).strip() for x in s2.columns]
    out["fr3_stress"] = _md(s2, num={k: 2 for k in s2.columns if k not in ("ssenari", "ad")})
    A = pd.read_csv(config.OUTPUT / "FR3_historical_analogues.csv")
    out["fr3_analogues"] = (f"2006–{config.LAST_ACTUAL}: korrelyasiya {az(A[['faktiki_sapma', 'proqnoz_sapma']].corr().iloc[0, 1], 2)}, "
                            f"RMSE {az(float(np.sqrt((A['xeta'] ** 2).mean())), 2)} f.b. (sıfır sapma etalonu "
                            f"{az(float(np.sqrt((A['faktiki_sapma'] ** 2).mean())), 2)} f.b.).\n\n" +
                            _md(A[A["epizod"]][["il", "faktiki_sapma", "proqnoz_sapma", "fiskal_reaksiya", "neft_birbasa",
                                                "terefdas", "devalvasiya", "tolerans_odenilir", "kalibrləməyə_daxil"]],
                                num={"faktiki_sapma": 2, "proqnoz_sapma": 2, "fiskal_reaksiya": 2, "neft_birbasa": 2,
                                     "terefdas": 2, "devalvasiya": 2}))
    T = c["bt_table"]
    out["nfr1"] = (f"Rüb {T['rub'].iloc[0]}: {int((T['netice'] == 'keçdi').sum())}/{len(T)} test keçdi.\n\n" +
                   _md(T[["test_id", "model", "hedef", "n", "metrik", "deyer", "hedd", "netice"]], num={"deyer": 3}) +
                   "\n\nKalibrləmə qərarları:\n\n" + _md(c["calibration"][["hedef", "miqyas", "ehate80", "n", "qerar"]],
                                                         num={"miqyas": 2, "ehate80": 2}))
    rows = []
    for view, r in (("baza mərkəzli", c["res"]), ("canlı", c.get("res_live"))):
        if r is None:
            continue
        jj = r.col(r.score_year)
        for kind, nm in (("g", "Qeyri-neft artımı, %"), ("cpi", "İnflyasiya, %"), ("fis", "Büdcə balansı, % ÜDM")):
            x = r.total(kind)[:, jj]
            rows.append({"Baxış": view, "Göstərici": nm, "Baza": r.base[kind][jj], "P5": np.quantile(x, .05),
                         "P50": np.median(x), "Orta": x.mean(), "P95": np.quantile(x, .95),
                         "Hədəf σ": r.meta["layering"][kind]["sig_target"][jj],
                         "Ümumi σ": r.meta["layering"][kind]["sig_total"][jj]})
    vt = pd.DataFrame(rows)
    out["v2_views"] = (f"Qiymətləndirmə ili {res.score_year}; Brent mərkəzi: baza {az(res.brent_base[j], 1)} USD, canlı "
                       f"{az(float(c['res_live'].meta['brent_centre'][j]), 1)} USD.\n\n" if c.get("res_live") is not None else "") + \
        _md(vt, num={k: 2 for k in ("Baza", "P5", "P50", "Orta", "P95", "Hədəf σ", "Ümumi σ")})
    fs = c["feed_status"]
    out["nfr2"] = _md(fs[["feed", "vintage", "last_obs", "age_days", "n_obs"]], num={"age_days": 0, "n_obs": 0})
    return out


def _csv(name):
    p = config.OUTPUT / name
    return pd.read_csv(p) if p.exists() else None


def blocks_v21(c: dict) -> dict[str, str]:
    """v2.1 evidence that must stay current (audit: hard-coded numbers drifted from the outputs)."""
    out, res = {}, c["res"]
    sy = res.score_year
    j = res.col(sy)
    rl = c.get("res_live")
    st = c.get("stress")
    rows = [{"Göstərici": f"Büdcə balansının medianı {sy}, % ÜDM", "Baza baxışı": float(np.median(res.total("fis")[:, j])),
             "Canlı baxış": float(np.median(rl.total("fis")[:, j])) if rl is not None else np.nan}]
    if st is not None and len(st):
        for sid in ("S1", "S3"):
            for var in sorted(st["gosterici"].unique()):
                v = st[(st["ssenari"] == sid) & (st["il"] == sy) & (st["gosterici"] == var)]["sapma"]
                if len(v):
                    rows.append({"Göstərici": f"{sid} sapması {sy}: {var}", "Baza baxışı": float(v.iloc[0]), "Canlı baxış": np.nan})
    out["v2_evidence"] = _md(pd.DataFrame(rows), num={"Baza baxışı": 2, "Canlı baxış": 2})
    A = _csv("FR3_historical_analogues.csv")
    T = c.get("bt_table")
    if A is not None:
        ratio = float(np.sqrt((A["xeta"] ** 2).mean()) / np.sqrt((A["faktiki_sapma"] ** 2).mean()))
        d4 = T[T["test_id"] == "D4"]["deyer"] if T is not None and "test_id" in T else pd.Series(dtype=float)
        out["d4_note"] = (f"Cari analoq cədvəli üzrə RMSE / RMSE(sıfır sapma) = {az(ratio, 3)} (n = {len(A)}); NFR1 D4 sətri "
                          + (f"{az(float(d4.iloc[0]), 3)} — rüblük sınağın ({T['rub'].iloc[0]}) vintajıdır, analoq düsturu "
                             "v2.1-də dəyişdiyi üçün növbəti rüblük sınaqda yenilənir" if len(d4) else "yoxdur")
                          + ". Korrelyasiya və RMSE nisbəti fərqli metrikalardır.")
    F = _csv("FR1_fx_transmission.csv")
    if F is not None:
        P = F[F["setir_novu"] == "parametr"][["parametr", "deyer", "izah", "n", "numune"]]
        R = F[F["setir_novu"] == "cavab"].pivot_table(index="parametr", columns="il", values="cemi").reset_index()
        R.columns = [str(x) for x in R.columns]
        out["fx_table"] = (_md(P, num={"deyer": 3}) + "\n\n+16,5% devalvasiyaya kalibrlənmiş cəmi cavab:\n\n" +
                           _md(R, num={k: 2 for k in R.columns if k != "parametr"}))
    return out


def blocks_caem(c: dict) -> dict[str, str]:
    out = {}
    C2 = _csv("C2_balance_of_risks.csv")
    if C2 is not None:
        t = C2[C2["category"] == "CƏMİ"].pivot_table(index="version", columns="year", values="weighted").reset_index()
        t.columns = [str(x) for x in t.columns]
        out["c2_index"] = _md(t, num={k: 1 for k in t.columns if k != "version"})
    S = c.get("S")
    if S is not None and (S["risk_id"] == "R01").any():
        r = S[S["risk_id"] == "R01"].iloc[0]
        out["c2_r01"] = f"FR2 R01 skoru {int(r['skor'])}-dir ({r['prioritet']} prioritet; P {int(r['P_bal'])} × T {int(r['I_bal'])})"
    C5 = _csv("C5_transmission_comparison.csv")
    if C5 is not None:
        C5 = C5.dropna(subset=["year"])
        g = C5.groupby(["shock_az", "concept_az", "model"])
        t = g.apply(lambda d: f"{az(d.sort_values('year')['value'].iloc[0], 2)} → {az(d.sort_values('year')['value'].iloc[-1], 2)}")
        t = t.rename("2026 → 2030").reset_index()
        out["c5_table"] = _md(t.rename(columns={"shock_az": "Şok", "concept_az": "Göstərici", "model": "Model"}))
    return out


def blocks_scal(c: dict) -> dict[str, str]:
    out = {}
    from . import factors
    ch = factors.channels()
    b0, b1 = ch[("cpi_ext", "impA")]["coef"], ch[("cpi_ext", "impA_l1")]["coef"]
    meta = ch[("cpi_ext", "meta")]
    out["s_passthrough"] = (f"Vahid xarici qiymət ötürməsi (`cpi_ext`, HAC, {meta['sample']}, n = {meta['n']}): AZN idxal qiymətləri "
                            f"b0 = {az(b0, 3)}, b1 = {az(b1, 3)}; ərzaq → USD idxal qiymətləri γ = {az(ch['_impfood']['gamma'], 2)}; "
                            f"Brent → idxal qiymətləri {az(ch['_impfood']['a_imp'], 2)}.")
    S1 = _csv("S1_scalability_grid.csv")
    if S1 is not None:
        g = S1[(S1["variant"] == "σ-şəbəkə") & (S1["k_sigma"] == 1.0) & S1["amil"].isin(["food", "import", "costpush", "fx"])
               & S1["hedef_id"].isin(["ru:cpi", "ru:nonoil_lvl", "ru:budget_gdp"])]
        t = g.pivot_table(index=["amil_ad", "hedef_ad"], columns="il", values="delta").reset_index()
        t.columns = [str(x) for x in t.columns]
        t = t.rename(columns={"amil_ad": "Amil (+1σ)", "hedef_ad": "Göstərici"})
        out["s_food"] = _md(t, num={k: 2 for k in t.columns if k not in ("Amil (+1σ)", "Göstərici")})
    M1 = _csv("M1_measures_v2.csv")
    if M1 is not None:
        t = M1[M1["tedbir_id"].isin(["T09", "T26", "T28"])][["tedbir_id", "effekt_hedef_funksiya", "effekt_hedef_simmetrik",
                                                               "effekt_hedef_quyruq"]]
        out["m_results"] = _md(t.rename(columns={"effekt_hedef_funksiya": "λ = 0,5", "effekt_hedef_simmetrik": "λ = 0",
                                                 "effekt_hedef_quyruq": "λ = 1"}), num={"λ = 0,5": 2, "λ = 0": 2, "λ = 1": 2})
    return out


def _apply(path, bl: dict, strict: bool) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    for tag, body in bl.items():
        pat = re.compile(rf"(<!-- AUTO:{tag} -->)(.*?)(<!-- /AUTO:{tag} -->)", re.S)
        if not pat.search(text):
            if strict:
                raise KeyError(f"{path.name}: AUTO:{tag} markeri yoxdur")
            continue
        text = pat.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(3)}", text)
    path.write_text(text, encoding="utf-8")


def update_methodology(c: dict) -> None:
    """Main methodology (strict: every block must have its marker) + v2.1 blocks and the CAEM / scalability docs
    (blocks rendered from the outputs wherever their markers exist)."""
    _apply(DOC, blocks(c), strict=True)
    for path, fn in ((DOC, blocks_v21), (config.DOCS / "CAEM_inteqrasiya.md", blocks_caem),
                     (config.DOCS / "Miqyaslanma_ve_tedbirler.md", blocks_scal)):
        try:
            _apply(path, fn(c), strict=False)
        except Exception as exc:                          # noqa: BLE001 — one stale doc must not stop the run
            print(f"   DİQQƏT: {path.name} AUTO blokları yenilənmədi ({type(exc).__name__}: {exc})")
    from . import docs_varcar                      # VaR/CaR methodology §15: numbers rendered from the outputs
    docs_varcar.update()
