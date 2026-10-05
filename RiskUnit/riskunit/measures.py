"""FR3 — risk-mitigating measures: register, risk-measure linkage, status tracking, residual
risk, model-sized policy levers, named stress scenarios and historical analogues.

The register (input/tedbirler_reyestri.csv) is the Ministry's working document: measure,
responsible body, deadline, status. This module validates it, links it to the risk register,
tracks status changes over time and quantifies, where the core allows, what each measure buys.
"""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd

from . import config, factors, simulate, spine

STATUS_W = {"təklif": 0.0, "təsdiqlənib": 0.25, "icrada": 0.5, "tamamlanıb": 1.0, "dayandırılıb": 0.0}
STRATEGY = {"azaltma", "ötürmə", "qaçınma", "qəbul", "izləmə"}
REQUIRED = ["tedbir_id", "risk_idler", "tedbir", "strategiya", "mesul", "muddet", "status"]


def load() -> pd.DataFrame:
    m = pd.read_csv(config.INPUT / "tedbirler_reyestri.csv", dtype=str).fillna("")
    missing = [c for c in REQUIRED if c not in m.columns]
    if missing:
        raise ValueError(f"tedbirler_reyestri.csv: sütun çatışmır: {missing}")
    for c in ("effekt_ehtimal_pct", "effekt_tesir_pct"):
        m[c] = pd.to_numeric(m[c], errors="coerce").fillna(0.0)
    m["status_w"] = m["status"].map(STATUS_W)
    today = pd.Timestamp(config.as_of())
    continuous = (m["strategiya"] == "izləmə") & (m["status"] == "icrada")
    m["gecikir"] = (pd.to_datetime(m["muddet"]) < today) & ~m["status"].isin(["tamamlanıb", "dayandırılıb"]) & ~continuous
    m["yoxlama"] = [_check(r) for r in m.itertuples()]
    return m


def _check(r) -> str:
    errs = []
    if r.status not in STATUS_W:
        errs.append(f"status '{r.status}' lüğətdə yoxdur")
    if r.strategiya not in STRATEGY:
        errs.append(f"strategiya '{r.strategiya}' lüğətdə yoxdur")
    if not r.mesul.strip():
        errs.append("məsul göstərilməyib")
    try:
        pd.Timestamp(r.muddet)
    except Exception:
        errs.append("müddət tarix deyil")
    return "; ".join(errs) or "ok"


def coverage(m: pd.DataFrame) -> pd.DataFrame:
    """Acceptance check: every active risk has at least one registered measure."""
    reg = factors.register()
    links = m.assign(risk_id=m["risk_idler"].str.split(";")).explode("risk_id")
    links["risk_id"] = links["risk_id"].str.strip()
    unknown = sorted(set(links["risk_id"]) - set(reg["risk_id"]))
    rows = []
    for r in reg.itertuples():
        mm = links[links["risk_id"] == r.risk_id]
        rows.append({"risk_id": r.risk_id, "ad": r.ad, "tedbir_sayi": len(mm),
                     "aktiv_tedbir": int(mm["status"].isin(["təsdiqlənib", "icrada"]).sum()),
                     "tamamlanmis": int((mm["status"] == "tamamlanıb").sum()),
                     "gecikən": int(mm["gecikir"].sum()),
                     "tedbirler": ";".join(mm["tedbir_id"]), "qebul_serti": "ödənilib" if len(mm) else "ÖDƏNİLMƏYİB"})
    out = pd.DataFrame(rows)
    out.attrs["unknown_links"] = unknown
    return out


def residual(S: pd.DataFrame, m: pd.DataFrame) -> pd.DataFrame:
    """Residual risk after measures: effects weighted by implementation status (current) and at
    full implementation of every non-stopped measure (target)."""
    from .scoring import band, scales
    sc = scales(factors.params())
    links = m.assign(risk_id=m["risk_idler"].str.split(";")).explode("risk_id")
    rows = []
    for r in S.itertuples():
        mm = links[links["risk_id"].str.strip() == r.risk_id]
        out = {"risk_id": r.risk_id, "ad": r.ad, "skor": r.skor}
        for label, w in (("cari", mm["status_w"]), ("hedef", (mm["status"] != "dayandırılıb").astype(float))):
            fp = float(np.prod(1 - w * mm["effekt_ehtimal_pct"] / 100)) if len(mm) else 1.0
            fi = float(np.prod(1 - w * mm["effekt_tesir_pct"] / 100)) if len(mm) else 1.0
            pr = r.ehtimal * fp
            ib = max(band(max(r.tesir_g, 0) * fi, sc["g"]), band(max(r.tesir_cpi, 0) * fi, sc["cpi"]),
                     band(max(r.tesir_fis, 0) * fi, sc["fis"]))
            out[f"ehtimal_{label}"] = pr
            out[f"skor_{label}"] = band(pr, sc["p"]) * ib
        rows.append(out)
    return pd.DataFrame(rows)


STATUS_HISTORY = config.OUTPUT / "FR3_status_history.csv"


def track_status(m: pd.DataFrame) -> pd.DataFrame:
    """Append a row whenever a measure's status (or deadline) differs from the last snapshot."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cur = m[["tedbir_id", "status", "muddet", "mesul"]].copy()
    if STATUS_HISTORY.exists():
        h = pd.read_csv(STATUS_HISTORY, dtype=str)
        last = h.groupby("tedbir_id").tail(1).set_index("tedbir_id")
        changed = [r for r in cur.itertuples() if r.tedbir_id not in last.index
                   or last.at[r.tedbir_id, "status"] != r.status or last.at[r.tedbir_id, "muddet"] != r.muddet]
        new = pd.DataFrame([{"qeyd_utc": now, "as_of": config.as_of().isoformat(), "tedbir_id": r.tedbir_id,
                             "status": r.status, "muddet": r.muddet, "mesul": r.mesul,
                             "evvelki_status": last.at[r.tedbir_id, "status"] if r.tedbir_id in last.index else ""}
                            for r in changed])
        h = pd.concat([h, new], ignore_index=True) if len(new) else h
    else:
        h = cur.assign(qeyd_utc=now, as_of=config.as_of().isoformat(), evvelki_status="")[
            ["qeyd_utc", "as_of", "tedbir_id", "status", "muddet", "mesul", "evvelki_status"]]
    h.to_csv(STATUS_HISTORY, index=False)
    return h


# ---------------------------------------------------------------- levers and stress scenarios
N_SCEN = 4000


def _med(res, kind):
    return np.median(res.total(kind), axis=0)


def levers(res: simulate.SimResult) -> pd.DataFrame:
    """Size of each policy lever needed to close the Growth-at-Risk gap, from the FR1 step
    responses, and the model-based effect of avoiding the procyclical investment cut (T09)."""
    M = spine.multipliers()
    j = res.col(res.score_year)
    g = res.total("g")[:, j]
    base_med = float(np.median(g))
    p10 = float(np.quantile(g, 0.10))
    gap = base_med - p10
    k_inv = float(M["stateinv1bn"]["rgdpnon"].iloc[0])
    k_cr = float(M["credit_ease200"]["rgdpnon"].iloc[0])
    k_fis = float(M["stateinv1bn"]["balance_n"].iloc[0])
    C = simulate.contributions(res, "g")
    gap_f = float(-C[C["kanal"] != "resid"]["quyruq_tohfesi_merkezlesmis"].sum())     # risk-factor part of the tail
    no_react = simulate.run(n=config.N_SIM, overrides={"fiscal_react_floor": True})
    g2 = no_react.total("g")[:, j]
    rows = [
        {"alet": "Kontrtsiklik dövlət investisiyası", "tedbir_id": "T09",
         "olcu": "mlrd AZN (real)", "lazim_olan": gap / k_inv, "lazim_olan_amil": gap_f / k_inv,
         "mumkunluk": "mümkün (büdcə xərci ilə)" if gap_f / k_inv <= 3 else "qismən — ARDNF buferi tələb olunur",
         "izah": f"P10 ilə median arasındakı {gap:.2f} f.b. fərqi bağlamaq üçün; 1 mlrd AZN → qeyri-neft ÜDM +{k_inv:.2f}% (FR1)",
         "fiskal_xerc": gap / k_inv * k_fis, "fiskal_xerc_vahid": "mln AZN büdcə balansına (FR1, 1-ci il)"},
        {"alet": "Monetar yumşalma (siyasət faizi)", "tedbir_id": "T19",
         "olcu": "baza bəndi", "lazim_olan": gap / k_cr * 200, "lazim_olan_amil": gap_f / k_cr * 200,
         "mumkunluk": "tək başına mümkün deyil" if gap_f / k_cr * 200 > 500 else "mümkün",
         "izah": f"−200 b.p. → qeyri-neft ÜDM +{k_cr:.2f}% (FR1); tələb olunan ölçü real faiz həddini aşa bilər",
         "fiskal_xerc": np.nan, "fiskal_xerc_vahid": ""},
        {"alet": "Prosiklik investisiya kəsintisindən imtina (fiskal qayda)", "tedbir_id": "T09; T01",
         "olcu": "f.b. (P10 dəyişməsi)", "lazim_olan": float(np.quantile(g2, 0.10) - p10), "lazim_olan_amil": np.nan,
         "mumkunluk": "fiskal qayda qərarı",
         "izah": (f"Brent enəndə dövlət investisiyası baza yolundan aşağı kəsilmirsə: P10 {p10:.2f}% → "
                  f"{np.quantile(g2, 0.10):.2f}%; ES10 {g[g <= p10].mean():.2f}% → "
                  f"{g2[g2 <= np.quantile(g2, 0.10)].mean():.2f}%"),
         "fiskal_xerc": np.nan, "fiskal_xerc_vahid": ""},
    ]
    return pd.DataFrame(rows)


def stress_scenarios() -> pd.DataFrame:
    """Named standing stress set (Methodology Blueprint L4), each a shock vector through the
    same transmission, with and without the mitigation package (no procyclical cut, T09)."""
    yrs = config.FORECAST_YEARS
    T = len(yrs)
    L = spine.live()
    B = spine.baseline()
    centre = simulate.run(n=200).meta["brent_centre"]
    y26 = [L["brent_ytd_avg"] * 0.75 + 0.25 * x for x in (45.0, 60.0)]
    p = factors.params()
    S = {
        "S1": ("Davamlı aşağı neft qiyməti", "Brent 2027–2030: 45 USD/barel",
               {"brent_path": [y26[0]] + [45.0] * (T - 1)}),
        "S2": ("Tərəfdaş ölkələrdə resessiya", "tərəfdaş artımı baza yolundan 2027: −3 f.b., 2028: −1,5 f.b.",
               {"partner_dev": [0, -3.0, -1.5] + [0] * (T - 3)}),
        "S3": ("Məzənnəyə təzyiq və ehtiyatların azalması", "S1 + 2027-də 25% devalvasiya",
               {"brent_path": [y26[0]] + [45.0] * (T - 1), "deval_year": 2027}),
        "S4": ("Regional münaqişənin eskalasiyası", "pul baratları 2027: −30%; tərəfdaş −2 f.b.; kredit faizi +1 f.b. (2014–2015 analoqu)",
               {"remit_dev": [0, -30.0] + [0] * (T - 2), "partner_dev": [0, -2.0] + [0] * (T - 2),
                "lend_dev": [0, 1.0] + [0] * (T - 2)}),
        "S5": ("Güclü seysmik hadisə", f"2027: birbaşa zərər ÜDM-in {p['eq_damage_p90_tier2']:.0f}%-i (M ≥ 6 üçün P90)",
               {"quake_damage": [0, p["eq_damage_p90_tier2"]] + [0] * (T - 2)}),
        "S6": ("Enerji keçidi — tələbin struktur azalması", "Brent mərkəzi yoldan hər il −5% (2027-dən)",
               {"brent_path": [centre[0]] + [centre[k] * 0.95 ** k for k in range(1, T)]}),
        "S7": ("Şiddətli quraqlıq", "2027: SPI = −2,0", {"spi": [0, -2.0] + [0] * (T - 2)}),
        "S8": ("Cari neft şokunun geri dönməsi", "Brent 2027: 60 USD, 2028–2030: makro baza yolu",
               {"brent_path": [y26[1], 60.0] + list(B["brent_usd"].iloc[2:])}),
    }
    ref = simulate.run(n=200)
    neutral = {"deterministic": True, "spi": [0.0] * T, "quake_damage": [0.0] * T, "remit_dev": [0.0] * T,
               "partner_dev": [0.0] * T, "lend_dev": [0.0] * T}
    ref_det = simulate.run(n=N_SCEN, overrides={**neutral, "brent_path": list(ref.meta["brent_centre"])})
    rows = []
    for sid, (name, desc, ov) in S.items():
        full = {**neutral, **ov}
        if "brent_path" not in full:
            full["brent_path"] = list(ref.meta["brent_centre"])
        a = simulate.run(n=N_SCEN, overrides=full)
        b = simulate.run(n=N_SCEN, overrides={**full, "fiscal_react_floor": True})
        b_ref = simulate.run(n=N_SCEN, overrides={**neutral, "brent_path": list(ref.meta["brent_centre"]),
                                                  "fiscal_react_floor": True})
        for kind, var in (("g", "qeyri-neft artımı, f.b."), ("cpi", "inflyasiya, f.b."), ("fis", "büdcə balansı, % ÜDM")):
            d = _med(a, kind) - _med(ref_det, kind)
            dm = _med(b, kind) - _med(b_ref, kind)
            for t, y in enumerate(yrs):
                rows.append({"ssenari": sid, "ad": name, "sok_vektoru": desc, "gosterici": var, "il": y,
                             "sapma": d[t], "sapma_tedbirle": dm[t], "tedbirin_effekti": dm[t] - d[t]})
    out = pd.DataFrame(rows)
    return out


def analogues() -> pd.DataFrame:
    """Historical check of the transmission engine: observed factor moves in each year passed
    through the first-year responses, against the observed non-oil growth deviation from the
    previous five-year average. Tolerance: same sign and |error| ≤ 3 pp for named episodes."""
    P = factors.channels()["_panel"]
    ch = factors.channels()
    M = spine.multipliers()
    p = factors.params()
    dv = factors.devaluation()
    mi = spine.micro_fr1_dataset()
    k_b = float(M["brent10"]["rgdpnon"].iloc[0])
    k_x = float(M["extdem10"]["rgdpnon"].iloc[0])
    k_i = float(M["stateinv1bn"]["rgdpnon"].iloc[0])
    k_r = float(M["credit_ease200"]["rgdpnon"].iloc[0])
    b0, b1 = ch[("inv_brent", "dln_brent")]["coef"], ch[("inv_brent", "dln_brent_l1")]["coef"]
    b_spi = ch[("agri_spi", "spi")]["coef"]
    rows = []
    for y in range(2006, config.LAST_ACTUAL + 1):
        pre = P.loc[y - 5:y - 1]
        act = P.at[y, "nonoil_g"] - pre["nonoil_g"].mean()
        d_b = P.at[y, "brent"] - P.at[y - 1, "brent"]
        x0 = np.log(P.at[y, "brent"] / P.at[y - 1, "brent"])
        x1 = np.log(P.at[y - 1, "brent"] / P.at[y - 2, "brent"])
        inv_prev = mi.at[y - 1, "rinv_state"] / 1000
        direct = d_b / 10 * k_b
        react = (b0 * x0 + b1 * x1) * inv_prev * k_i
        part = (P.at[y, "partner_g"] - pre["partner_g"].mean()) / 10 * k_x
        rate = -(P.at[y, "lendrate"] - P.at[y - 1, "lendrate"]) / 2 * k_r if not np.isnan(P.at[y - 1, "lendrate"]) else 0.0
        drought = b_spi * P.at[y, "spi"] * P.at[y, "agri_share_nonoil"] / 100
        dev = (dv["nonoil_residual"] * np.log(P.at[y, "usd_azn"] / P.at[y - 1, "usd_azn"]) / dv["dln_fx_2014_2017"]
               if P.at[y, "usd_azn"] / P.at[y - 1, "usd_azn"] > 1.10 else 0.0)
        pred = direct + react + part + rate + drought + dev
        rows.append({"il": y, "faktiki_sapma": act, "proqnoz_sapma": pred, "xeta": act - pred,
                     "neft_birbasa": direct, "fiskal_reaksiya": react, "terefdas": part, "faiz": rate,
                     "quraqliq": drought, "devalvasiya": dev,
                     "epizod": y in (2009, 2015, 2016, 2020),
                     "kalibrləməyə_daxil": y in (2015, 2016)})
    A = pd.DataFrame(rows)
    A["tolerans_odenilir"] = (np.sign(A["faktiki_sapma"]) == np.sign(A["proqnoz_sapma"])) & (A["xeta"].abs() <= 3)
    return A
