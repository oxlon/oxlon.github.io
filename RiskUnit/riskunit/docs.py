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
    fs = c["feed_status"]
    out["nfr2"] = _md(fs[["feed", "vintage", "last_obs", "age_days", "n_obs"]], num={"age_days": 0, "n_obs": 0})
    return out


def update_methodology(c: dict) -> None:
    if not DOC.exists():
        return
    text = DOC.read_text(encoding="utf-8")
    for tag, body in blocks(c).items():
        pat = re.compile(rf"(<!-- AUTO:{tag} -->)(.*?)(<!-- /AUTO:{tag} -->)", re.S)
        if not pat.search(text):
            raise KeyError(f"Metodologiya sənədində AUTO:{tag} markeri yoxdur")
        text = pat.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(3)}", text)
    DOC.write_text(text, encoding="utf-8")
