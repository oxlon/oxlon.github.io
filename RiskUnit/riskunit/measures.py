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


STRESS_KINDS = (("g", "qeyri-neft artımı, f.b."), ("cpi", "inflyasiya, f.b."), ("fis", "büdcə balansı, % ÜDM"))
_REF = {}


def neutral_overrides() -> dict:
    """Deterministic stress mode: only the declared shocks act (no residual, no random events, factor paths at zero)."""
    T = len(config.FORECAST_YEARS)
    return {"deterministic": True, "spi": [0.0] * T, "quake_damage": [0.0] * T, "remit_dev": [0.0] * T,
            "partner_dev": [0.0] * T, "lend_dev": [0.0] * T}


def stress_centre() -> list:
    """Brent reference path of the stress set = the baseline-view centre (2026 observed months at the YTD average)."""
    return list(simulate.run(n=200).meta["brent_centre"])


def stress_vector(overrides: dict, with_measures: bool = True, n: int = N_SCEN) -> pd.DataFrame:
    """The S1–S8 rule applied to ANY factor-shock vector (public; used by stress_scenarios and the API):
    deviation = median(run with {neutral + centre + overrides}) − median(neutral reference run), per outcome and year;
    with_measures: the same with the T09 floor (no procyclical investment cut) in both runs.
    `overrides` = simulate.run override keys (brent_path, partner_dev, remit_dev, lend_dev, spi, quake_damage,
    deval_year, imp_dev, food_dev, fiscal_react_off, ...). Returns rows kind, gosterici, il, sapma, sapma_tedbirle,
    tedbirin_effekti (sapma_tedbirle/tedbirin_effekti NaN without measures)."""
    yrs = config.FORECAST_YEARS
    neutral = neutral_overrides()
    centre = stress_centre()
    full = {**neutral, **(overrides or {})}
    full.setdefault("brent_path", centre)
    key = (tuple(np.round(centre, 6)), n)
    if key not in _REF:
        _REF.clear()
        _REF[key] = {"ref": simulate.run(n=n, overrides={**neutral, "brent_path": centre}),
                     "ref_floor": simulate.run(n=n, overrides={**neutral, "brent_path": centre, "fiscal_react_floor": True})}
    a = simulate.run(n=n, overrides=full)
    b = simulate.run(n=n, overrides={**full, "fiscal_react_floor": True}) if with_measures else None
    rows = []
    for kind, var in STRESS_KINDS:
        d = _med(a, kind) - _med(_REF[key]["ref"], kind)
        dm = _med(b, kind) - _med(_REF[key]["ref_floor"], kind) if b is not None else np.full(len(yrs), np.nan)
        for t, y in enumerate(yrs):
            rows.append({"kind": kind, "gosterici": var, "il": y, "sapma": float(d[t]), "sapma_tedbirle": float(dm[t]),
                         "tedbirin_effekti": float(dm[t] - d[t])})
    return pd.DataFrame(rows)


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
    """Named standing stress set (Methodology Blueprint L4), each a shock vector through the same transmission
    (stress_vector), with and without the mitigation package (no procyclical cut, T09). v2.1: every shock is a
    shock-year impulse or an explicit path; S3 devaluation through the single FX module (riskunit.fx)."""
    yrs = config.FORECAST_YEARS
    T = len(yrs)
    L = spine.live()
    B = spine.baseline()
    centre = stress_centre()
    y26 = [L["brent_ytd_avg"] * 0.75 + 0.25 * x for x in (45.0, 60.0)]
    p = factors.params()
    S = {
        "S1": ("Davamlı aşağı neft qiyməti", "Brent 2026-nın qalan ayları (IV rüb) və 2027–2030: 45 USD/barel",
               {"brent_path": [y26[0]] + [45.0] * (T - 1)}),
        "S2": ("Tərəfdaş ölkələrdə resessiya", "tərəfdaş artımı baza yolundan 2027: −3 f.b., 2028: −1,5 f.b.",
               {"partner_dev": [0, -3.0, -1.5] + [0] * (T - 3)}),
        "S3": ("Məzənnəyə təzyiq və ehtiyatların azalması", "S1 (Brent 2026 IV rüb – 2030: 45 USD) + 2027-də 25% devalvasiya (vahid məzənnə modulu: İQİ, qeyri-neft, büdcə, borc)",
               {"brent_path": [y26[0]] + [45.0] * (T - 1), "deval_year": 2027}),
        "S4": ("Regional münaqişənin eskalasiyası", "pul baratları 2027: −30%; tərəfdaş −2 f.b.; kredit faizi +1 f.b. (2014–2015 analoqu)",
               {"remit_dev": [0, -30.0] + [0] * (T - 2), "partner_dev": [0, -2.0] + [0] * (T - 2),
                "lend_dev": [0, 1.0] + [0] * (T - 2)}),
        "S5": ("Güclü seysmik hadisə", f"2027: birbaşa zərər ÜDM-in {p['eq_damage_p90_tier2']:.0f}%-i (M ≥ 6 üçün P90); bərpa 25/50/25%",
               {"quake_damage": [0, p["eq_damage_p90_tier2"]] + [0] * (T - 2)}),
        "S6": ("Enerji keçidi — tələbin struktur azalması", "Brent mərkəzi yoldan hər il −5% (2027-dən)",
               {"brent_path": [centre[0]] + [centre[k] * 0.95 ** k for k in range(1, T)]}),
        "S7": ("Şiddətli quraqlıq", "2027: SPI = −2,0", {"spi": [0, -2.0] + [0] * (T - 2)}),
        "S8": ("Cari neft şokunun geri dönməsi", "Brent 2026 IV rüb və 2027: 60 USD, 2028–2030: makro baza yolu",
               {"brent_path": [y26[1], 60.0] + list(B["brent_usd"].iloc[2:])}),
    }
    rows = []
    for sid, (name, desc, ov) in S.items():
        V = stress_vector(ov)
        for r in V.itertuples():
            rows.append({"ssenari": sid, "ad": name, "sok_vektoru": desc, "gosterici": r.gosterici, "il": r.il,
                         "sapma": r.sapma, "sapma_tedbirle": r.sapma_tedbirle, "tedbirin_effekti": r.tedbirin_effekti})
    return pd.DataFrame(rows)


def analogues() -> pd.DataFrame:
    """Historical check of the transmission engine: observed factor moves in each year passed
    through the first-year responses, against the observed non-oil growth deviation from the
    previous five-year average. Tolerance: same sign and |error| ≤ 3 pp for named episodes.
    v2.1: the devaluation term comes from the single FX module (level loss per log unit, two-year timing);
    the investment reaction is the EXCESS over FR1's embedded elasticity (no double count with the Brent term)."""
    from . import fx
    P = factors.channels()["_panel"]
    ch = factors.channels()
    M = spine.multipliers()
    mi = spine.micro_fr1_dataset()
    c = fx.calibration()
    k_b = float(M["brent10"]["rgdpnon"].iloc[0])
    k_x = float(M["extdem10"]["rgdpnon"].iloc[0])
    k_i = float(M["stateinv1bn"]["rgdpnon"].iloc[0])
    k_r = float(M["credit_ease200"]["rgdpnon"].iloc[0])
    e_fr1 = simulate.fr1_embedded_inv_elasticity(M, spine.baseline()["brent_usd"].to_numpy())
    b0, b1 = ch[("inv_brent", "dln_brent")]["coef"] - e_fr1, ch[("inv_brent", "dln_brent_l1")]["coef"]
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
        dl0 = 100 * np.log(P.at[y, "usd_azn"] / P.at[y - 1, "usd_azn"])
        dl1 = 100 * np.log(P.at[y - 1, "usd_azn"] / P.at[y - 2, "usd_azn"])
        dev = c["L"] / 100 * (c["w0g"] * dl0 + (1 - c["w0g"]) * dl1) if max(dl0, dl1) > 10 else 0.0
        pred = direct + react + part + rate + drought + dev
        rows.append({"il": y, "faktiki_sapma": act, "proqnoz_sapma": pred, "xeta": act - pred,
                     "neft_birbasa": direct, "fiskal_reaksiya": react, "terefdas": part, "faiz": rate,
                     "quraqliq": drought, "devalvasiya": dev,
                     "epizod": y in (2009, 2015, 2016, 2020),
                     "kalibrləməyə_daxil": y in (2015, 2016)})
    A = pd.DataFrame(rows)
    A["tolerans_odenilir"] = (np.sign(A["faktiki_sapma"]) == np.sign(A["proqnoz_sapma"])) & (A["xeta"].abs() <= 3)
    return A


# ---------------------------------------------------------------- v2: strategy, cost, workflow (input/tedbirler_v2.csv)
STATUS_FLOW = ["təklif", "təsdiqlənib", "icrada", "tamamlanıb"]          # təklif → təsdiq → icrada → tamamlandı
STATUS_LABEL = {"təklif": "təklif", "təsdiqlənib": "təsdiq", "icrada": "icrada", "tamamlanıb": "tamamlandı",
                "dayandırılıb": "dayandırılıb"}
STRATEGY_V2 = {"qaçınma", "ötürmə", "azaltma", "qəbul"}
V2_FILE = config.INPUT / "tedbirler_v2.csv"


def load_v2() -> pd.DataFrame:
    """Register + v2 attributes (strategy type, cost mln AZN with basis, lead time, KPI threshold,
    effect model used by riskunit.optimize). Every register measure must have a v2 row."""
    m = load()
    if not V2_FILE.exists():
        raise FileNotFoundError(f"{V2_FILE} yoxdur")
    a = pd.read_csv(V2_FILE, dtype={"tedbir_id": str}).fillna({"effekt_kanal": "", "effekt_esasi": ""})
    missing = sorted(set(m["tedbir_id"]) - set(a["tedbir_id"]))
    if missing:
        raise ValueError(f"tedbirler_v2.csv: atributu olmayan tədbirlər {missing}")
    bad = sorted(set(a["strategiya_v2"]) - STRATEGY_V2)
    if bad:
        raise ValueError(f"tedbirler_v2.csv: naməlum strategiya {bad}")
    out = m.merge(a, on="tedbir_id", how="left")
    out["status_az"] = out["status"].map(STATUS_LABEL).fillna(out["status"])
    out["merhele_no"] = out["status"].map({s: i + 1 for i, s in enumerate(STATUS_FLOW)}).fillna(0).astype(int)
    out["novbeti_addim"] = out["status"].map({"təklif": "təsdiq üçün təqdim", "təsdiqlənib": "icraya başlanması",
                                              "icrada": "KPI ölçümü və tamamlanma", "tamamlanıb": "effektin qiymətləndirilməsi",
                                              "dayandırılıb": "yenidən baxış"}).fillna("")
    return out


# ---------------------------------------------------------------- stage F entry point (run_all._measures_any)
def run(ctx: dict | None = None) -> dict:
    """FR3 stage: register, coverage, residual risk, levers, stress S1–S8, analogues — plus the v2.1 core-transmission
    outputs that need the scored simulation: FR1_fx_transmission (riskunit.fx), FR2_model_risk (R19 consensus-shifted
    alternative), FR2_threshold_sensitivity (R11–R13), NFR1_calibration_shrinkage. Sets ctx stress/levers/measures/
    coverage/residual (report.py)."""
    from . import fx, scoring
    ctx = ctx if ctx is not None else {}
    res = ctx.get("sim") or simulate.run()
    S = ctx.get("S")
    if S is None:
        S = scoring.score(res)
    m = load()
    cov = coverage(m)
    if cov.attrs.get("unknown_links"):
        print("   DİQQƏT: reyestrdə olmayan risk ID-ləri:", cov.attrs["unknown_links"])
    resid = residual(S, m)
    track_status(m)
    lev = levers(res)
    stress = stress_scenarios()
    out = config.OUTPUT
    m.to_csv(out / "FR3_measures_register.csv", index=False)
    cov.to_csv(out / "FR3_coverage.csv", index=False)
    resid.to_csv(out / "FR3_residual_risk.csv", index=False, float_format="%.5g")
    lev.to_csv(out / "FR3_levers.csv", index=False, float_format="%.5g")
    stress.to_csv(out / "FR3_stress_scenarios.csv", index=False, float_format="%.5g")
    analogues().to_csv(out / "FR3_historical_analogues.csv", index=False, float_format="%.4g")
    extra = {
        "FR2_model_risk.csv": (scoring.model_risk_table(res),
                               "R19 model riski (istilik xəritəsindən kənar): köhnəlməmiş konsensus (köhnəlmiş CAEM/Bottom-up xaric), "
                               "baza ilə fərq, konsensusa sürüşdürülmüş alternativ paylanma və hədd ehtimalları; xəbərdarlıq ≥ 0,5 f.b."),
        "FR2_threshold_sensitivity.csv": (scoring.threshold_sensitivity(res),
                                          "R11–R13 nəticə riskləri: hədd şəbəkəsi üzrə ehtimal, bazanın həddə məsafəsi (σ) və yalnız "
                                          "qalıq qeyri-müəyyənlikdən gələn ehtimal (yaxınlıq effekti)"),
        "NFR1_calibration_shrinkage.csv": (simulate.calibration_report(),
                                           "NFR1 kalibrləmə əmsallarının 1-ə doğru büzülməsi (n/(n+10)), butstrap aralığı və miqyaslamadan "
                                           "sonra 80% örtüyün yenidən yoxlanılması"),
    }
    for f, (df, desc) in extra.items():
        df.to_csv(out / f, index=False, float_format="%.5g")
        spine.register_output(f, "riskunit.measures/scoring/simulate", desc, list(df.columns), "hər tam dövr")
    try:
        fx.run(ctx)
    except Exception as exc:                                 # noqa: BLE001
        print(f"   DİQQƏT: FR1_fx_transmission yazılmadı ({type(exc).__name__}: {exc})")
    ctx.update({"measures": m, "coverage": cov, "residual": resid, "levers": lev, "stress": stress})
    return ctx
