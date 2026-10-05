"""FR2 — scale and impact of each risk, probability × impact scoring, ranking, alerts.

Probability and impact come from the same joint simulation (simulate.run), so they are
mutually consistent. For a factor risk:
    P = share of draws in which the risk event occurs in the scoring year;
    I = shift of the channel's contribution in those draws relative to its unconditional mean
        (non-oil growth, pp; inflation, pp; budget balance, % GDP).
For an outcome risk (R11-R13): P = probability of crossing the threshold; I = expected
shortfall beyond it. Expert overlays (R04, R10, R14 probability) are kept and labelled.

The heat-map score (1-5 × 1-5) is the presentation layer requested by the TT. The
quantitative prioritisation that underlies it — contribution to the variance and to the lower
tail of non-oil growth — is published beside it (Methodology Blueprint, note on FR2).
"""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd

from . import config, factors, simulate, spine

OUTCOME = {"R11": "fis", "R12": "cpi", "R13": "g"}
RISK_CHANNELS = {}
for _ch, _rid in simulate.CHANNEL_RISK.items():
    RISK_CHANNELS.setdefault(_rid, []).append(_ch)


def band(x: float, cuts: list[float]) -> int:
    """1..5 by upper cut-offs (len 4)."""
    if x is None or np.isnan(x):
        return 1
    return int(1 + sum(x > c for c in cuts))


def scales(p: dict) -> dict:
    return {"p": [p[f"p_band_{i}"] for i in range(1, 5)],
            "g": [p[f"i_nonoil_{i}"] for i in range(1, 5)],
            "cpi": [p[f"i_cpi_{i}"] for i in range(1, 5)],
            "fis": [p[f"i_fiscal_{i}"] for i in range(1, 5)]}


def gpr_transition_probability() -> dict:
    """R06: empirical probability that next year's regional GPR is in the historical top decile,
    given the regime of the current year (no AR model — transition counts)."""
    p = factors.params()
    gm = factors.regional_gpr_monthly()
    a = gm.groupby(gm.index.year).agg(["mean", "count"])
    full = a[a["count"] == 12]["mean"]
    q_hi = full.quantile(p["gpr_quantile"])
    q_reg = full.quantile(0.75)
    cur_year = config.as_of().year
    cur = float(gm[gm.index.year == cur_year].mean())
    state_high = cur >= q_reg
    prev, nxt = full.iloc[:-1], full.shift(-1).iloc[:-1]
    cond = (prev >= q_reg) if state_high else (prev < q_reg)
    n = int(cond.sum())
    k = int((nxt[cond] >= q_hi).sum())
    return {"p": (k + 0.5) / (n + 1), "k": k, "n": n, "q_hi": float(q_hi), "q_regime": float(q_reg),
            "current": cur, "state_high": bool(state_high),
            "sample": f"{full.index.min()}–{full.index.max()}"}


def score(res: simulate.SimResult) -> pd.DataFrame:
    p = factors.params()
    sc = scales(p)
    reg = factors.register()
    j = res.col(res.score_year)
    tot_g = res.total("g")[:, j]
    tail = tot_g <= np.quantile(tot_g, 0.10)
    gpr_tp = gpr_transition_probability()
    rows = []
    for r in reg.itertuples():
        rid = r.risk_id
        out = {"risk_id": rid, "aile": r.aile, "ad": r.ad, "nov": r.nov, "sahib": r.sahib,
               "ufuq": res.score_year}
        if rid in OUTCOME:
            kind = OUTCOME[rid]
            x = res.total(kind)[:, j]
            if rid == "R11":
                thr = p["fiscal_threshold"]; ev = x < thr; short = (thr - x)[ev]
            elif rid == "R12":
                thr = p["cpi_threshold"]; ev = x > thr; short = (x - thr)[ev]
            else:
                thr = p["nonoil_gar_threshold"]; ev = x < thr; short = (thr - x)[ev]
            out.update({"ehtimal": float(ev.mean()), "ehtimal_menbe": "model (birgə simulyasiya)",
                        "tesir_g": float(short.mean()) if kind == "g" and ev.any() else 0.0,
                        "tesir_cpi": float(short.mean()) if kind == "cpi" and ev.any() else 0.0,
                        "tesir_fis": float(short.mean()) if kind == "fis" and ev.any() else 0.0,
                        "tesir_menbe": "model: həddən kənar gözlənilən çatışmazlıq",
                        "dispersiya_payi": np.nan, "quyruq_tohfesi": np.nan})
        else:
            chs = RISK_CHANNELS.get(rid, [])
            ev_mat = res.events.get(rid)
            if rid == "R14":
                jj = slice(0, len(res.years))          # long-horizon risk: cumulative to the last year
                out["ufuq"] = res.years[-1]
                ev = ev_mat[:, -1]
                def cum(comp):
                    return sum(comp[c][:, jj].sum(axis=1) for c in chs if c in comp) if chs else np.zeros(len(ev))
            else:
                ev = ev_mat[:, j]
                def cum(comp):
                    return sum(comp[c][:, j] for c in chs if c in comp) if any(c in comp for c in chs) \
                        else np.zeros(len(ev))
            cg, cc, cf = cum(res.comp_g), cum(res.comp_cpi), cum(res.comp_fis)
            def shift(c):
                return float(c[ev].mean() - c.mean()) if ev.any() else 0.0
            prob = float(ev.mean())
            src = "model (birgə simulyasiya)"
            if rid == "R06":
                prob, src = gpr_tp["p"], (f"empirik keçid tezliyi: {gpr_tp['k']}/{gpr_tp['n']} "
                                          f"({gpr_tp['sample']})")
            if r.nov == "ekspert" and not pd.isna(r.ekspert_ehtimal):
                src = "EKSPERT ÖRTÜYÜ — Nazirlik təsdiq etməlidir"
            if r.nov == "siqnal":
                src = "siqnal əsaslı (mikro EWS → ehtimal xəritələnməsi)"
            if rid == "R03":
                src = "model: P(Brent çöküşü) × P(devalvasiya | çöküş) — birgə simulyasiya"
            cg_t = cg[tail].mean() - cg.mean() if np.ndim(cg) else 0.0
            out.update({"ehtimal": prob, "ehtimal_menbe": src,
                        "tesir_g": -shift(cg), "tesir_cpi": shift(cc), "tesir_fis": -shift(cf),
                        "tesir_menbe": ("ekspert" if (r.nov == "ekspert" and rid != "R14") else
                                        "model: hadisə baş verən simulyasiyalarda kanal töhfəsinin sürüşməsi"),
                        "dispersiya_payi": float(np.cov(cg, tot_g)[0, 1] / tot_g.var(ddof=1)) if rid != "R14" else np.nan,
                        "quyruq_tohfesi": float(cg_t) if rid != "R14" else np.nan})
        out["P_bal"] = band(out["ehtimal"], sc["p"])
        ig, ic, ifs = band(max(out["tesir_g"], 0), sc["g"]), band(max(out["tesir_cpi"], 0), sc["cpi"]), \
            band(max(out["tesir_fis"], 0), sc["fis"])
        out["I_bal"] = max(ig, ic, ifs)
        out["I_olcu"] = ("qeyri-neft ÜDM" if ig == out["I_bal"] else
                         "inflyasiya" if ic == out["I_bal"] else "büdcə")
        out["skor"] = out["P_bal"] * out["I_bal"]
        out["gozlenilen_itki_g"] = out["ehtimal"] * max(out["tesir_g"], 0)
        rows.append(out)
    S = pd.DataFrame(rows)
    S["prioritet"] = np.where(S["skor"] >= p["score_high"], "yüksək",
                              np.where(S["skor"] >= p["score_medium"], "orta", "aşağı"))
    S["kemiyyet_sirasi"] = S["quyruq_tohfesi"].rank(method="min").astype("Int64")
    S = S.sort_values(["skor", "gozlenilen_itki_g", "ehtimal"], ascending=False).reset_index(drop=True)
    S.insert(0, "sira", range(1, len(S) + 1))
    S["baseline_id"] = spine.baseline_id()
    S["as_of"] = config.as_of().isoformat()
    return S


def heatmap(S: pd.DataFrame) -> pd.DataFrame:
    grid = []
    for pb in range(5, 0, -1):
        for ib in range(1, 6):
            ids = S[(S["P_bal"] == pb) & (S["I_bal"] == ib)]["risk_id"].tolist()
            grid.append({"P_bal": pb, "I_bal": ib, "skor": pb * ib, "riskler": ";".join(ids)})
    return pd.DataFrame(grid)


HISTORY = config.OUTPUT / "FR2_score_history.csv"


def append_history(S: pd.DataFrame) -> pd.DataFrame:
    """One block of rows per as_of date (re-runs on the same date replace it)."""
    keep = ["as_of", "baseline_id", "risk_id", "ehtimal", "tesir_g", "tesir_cpi", "tesir_fis",
            "P_bal", "I_bal", "skor", "prioritet"]
    new = S[keep].copy()
    new.insert(0, "hesablandi_utc", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    if HISTORY.exists():
        h = pd.read_csv(HISTORY)
        h = h[h["as_of"] != new["as_of"].iloc[0]]
        new = pd.concat([h, new], ignore_index=True)
    new.to_csv(HISTORY, index=False, float_format="%.6g")
    return new


def previous_scores(as_of: str) -> pd.Series:
    if not HISTORY.exists():
        return pd.Series(dtype=float)
    h = pd.read_csv(HISTORY)
    prev = h[h["as_of"] < as_of]
    if prev.empty:
        return pd.Series(dtype=float)
    last = prev[prev["as_of"] == prev["as_of"].max()]
    return last.set_index("risk_id")["skor"]


def alerts(S: pd.DataFrame, res: simulate.SimResult, ind: pd.DataFrame, measures: pd.DataFrame | None = None,
           feed_status: pd.DataFrame | None = None) -> pd.DataFrame:
    p = factors.params()
    A = []
    def add(tip, sev, rid, msg):
        A.append({"tip": tip, "ciddilik": sev, "risk_id": rid, "mesaj": msg})
    prev = previous_scores(config.as_of().isoformat())
    for r in S.itertuples():
        if r.prioritet == "yüksək":
            add("yüksək prioritet", "yüksək", r.risk_id,
                f"{r.ad}: ehtimal {r.ehtimal:.0%}, skor {r.skor} (P {r.P_bal} × T {r.I_bal}, ölçü: {r.I_olcu})")
        if r.risk_id in prev.index and r.skor - prev[r.risk_id] >= p["score_jump_alert"]:
            add("skor artımı", "orta", r.risk_id, f"{r.ad}: skor {int(prev[r.risk_id])} → {r.skor}")
    for r in ind[ind["status"] == "xəbərdarlıq"].itertuples():
        add("göstərici həddi", "orta", "", f"{r.ad}: son dəyər {r.son_deyer:.4g} ({r.son_tarix}), "
            f"tarixi paylanmanın {r.tarixi_faiz:.0f}-cı faizi" if not np.isnan(r.tarixi_faiz)
            else f"{r.ad}: {r.son_deyer:.4g} ({r.son_tarix})")
    j = res.col(res.score_year)
    med = float(np.median(res.total("g")[:, j]))
    base = float(res.base["g"][j])
    if abs(med - base) >= 1.0:
        add("baza köhnəlib", "orta", "R01",
            f"{res.score_year}: canlı məlumatla şərtləndirilmiş qeyri-neft artımının medianı {med:.1f}% — "
            f"makro baza yolu {base:.1f}%. Fərq ≥ 1 f.b.: makro modelin Brent fərziyyəsinin yenilənməsi tövsiyə olunur")
    c = res.meta["brent_centre"][j]
    if abs(c / res.brent_base[j] - 1) >= 0.20:
        add("baza köhnəlib", "orta", "R01",
            f"{res.score_year}: Brent mərkəzi yolu {c:.0f} USD (canlı) — makro fərziyyə {res.brent_base[j]:.0f} USD")
    if measures is not None and len(measures):
        for r in measures[measures["gecikir"]].itertuples():
            add("tədbir gecikir", "orta", r.risk_idler, f"{r.tedbir_id}: {r.tedbir[:80]} — müddət {r.muddet}, status {r.status}")
    if feed_status is not None:
        limits = {"brent": 7, "vix": 7, "ust10": 7, "eurusd": 14, "fedfunds": 45, "gpr": 45, "epu": 120,
                  "usgs": 400, "era5": 45}
        for r in feed_status.itertuples():
            if r.age_days > limits.get(r.feed, 60):
                add("məlumat köhnəlib", "aşağı", "", f"{r.feed}: son müşahidə {r.last_obs} ({int(r.age_days)} gün)")
    out = pd.DataFrame(A, columns=["tip", "ciddilik", "risk_id", "mesaj"])
    out.insert(0, "as_of", config.as_of().isoformat())
    out["baseline_id"] = spine.baseline_id()
    return out
