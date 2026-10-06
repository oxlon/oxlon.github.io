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


MODEL_RISK_VARS = {"nonoil_gdp_growth": ("g", -1), "cpi_inflation": ("cpi", +1)}
MR_FILE = "FR2_model_risk.csv"


def _consensus_sources() -> tuple[pd.DataFrame | None, set]:
    """D3 long table and the set of STALE sources: any value flagged 'köhnəlmiş' (an old vintage that still carries a
    projection for an observed year — CAEM CF04, Bottom-up/8 vərəq), plus CAEM whenever C6 lists CF04."""
    f = config.OUTPUT / "D3_consensus_long.csv"
    if not f.exists():
        return None, set()
    L = pd.read_csv(f)
    stale = set(L[L["flag"] == "köhnəlmiş"]["source"])
    c6 = config.OUTPUT / "C6_caem_findings.csv"
    if c6.exists() and (pd.read_csv(c6)["finding_id"] == "CF04").any():
        stale.add("caem")
    return L, stale


def model_risk_table(res: simulate.SimResult | None = None) -> pd.DataFrame:
    """R19 (audit M3) — NOT a P×I risk: the vote share of v2.0 counted stale sources and is not a probability. Per
    variable and year: the NON-STALE consensus of the other units (median of distinct values, excluding stale and
    'qeyri-real' values and OxLon itself), its gap to the baseline, and — when `res` is given — the consensus-shifted
    ALTERNATIVE distribution (the baseline-view draws shifted by the gap) with the threshold probabilities in both.
    Alert ('xeberdarliq') when the adverse gap ≥ model_risk_gap_pp (hedler, 0,5 f.b.)."""
    p = factors.params()
    thr = float(p.get("model_risk_gap_pp", 0.5))
    L, stale = _consensus_sources()
    if L is None:
        return pd.DataFrame()
    rows = []
    for var, (kind, sgn) in MODEL_RISK_VARS.items():
        for y in sorted(L[L["variable"] == var]["year"].unique()):
            if res is not None and y not in res.years:
                continue
            g = L[(L["variable"] == var) & (L["year"] == y)]
            b = g[g["source"] == "oxlon"]["value"]
            if b.empty:
                continue
            base = float(b.iloc[0])
            ok = g[(g["source"] != "oxlon") & ~g["source"].isin(stale) & (g["flag"].fillna("") != "qeyri-real")]
            vals = ok.drop_duplicates("value")
            allv = g[(g["source"] != "oxlon")].drop_duplicates("value")
            cons = float(vals["value"].median()) if len(vals) else np.nan
            gap = cons - base if np.isfinite(cons) else np.nan
            adverse = sgn * gap if np.isfinite(gap) else np.nan
            r = {"gosterici": kind, "deyisen": var, "il": int(y), "baza_oxlon": base, "konsensus_kohnelmemis": cons,
                 "n_menbe": int(len(vals)), "menbeler": ";".join(vals["source"]), "kohnelmis_xaric": ";".join(sorted(stale)),
                 "konsensus_hamisi": float(allv["value"].median()) if len(allv) else np.nan,
                 "ferq": gap, "elverissiz_ferq": adverse,
                 "yayilma_kohnelmemis": float(vals["value"].max() - vals["value"].min()) if len(vals) > 1 else 0.0,
                 "hedd": thr, "xeberdarliq": bool(np.isfinite(adverse) and adverse >= thr)}
            if res is not None and np.isfinite(gap):
                j = res.col(int(y))
                x = res.total(kind)[:, j]
                h = float(p["nonoil_gar_threshold"] if kind == "g" else p["cpi_threshold"])
                P = (lambda v: float((v < h).mean())) if kind == "g" else (lambda v: float((v > h).mean()))
                for nm, v in (("baza", x), ("alt", x + gap)):
                    q = np.quantile(v, [0.05, 0.5, 0.95])
                    r.update({f"{nm}_p05": q[0], f"{nm}_p50": q[1], f"{nm}_p95": q[2], f"{nm}_P_hedd": P(v)})
                r["hedd_gosterici"] = h
            rows.append(r)
    return pd.DataFrame(rows)


def model_risk(year: int, res: simulate.SimResult | None = None) -> dict:
    """R19 summary row for FR2_risk_scores (kept for schema stability; outside the heat map: P_bal = I_bal = 0)."""
    T = model_risk_table(res)
    out = {"ehtimal": 0.0, "tesir_g": 0.0, "tesir_cpi": 0.0, "tesir_fis": 0.0, "dispersiya_payi": np.nan,
           "quyruq_tohfesi": np.nan, "istilik_xeritesi": False,
           "tesir_menbe": "istilik xəritəsindən kənar — ayrıca göstərici (FR2_model_risk.csv)"}
    if T.empty:
        out["ehtimal_menbe"] = "D3 cədvəli yoxdur — yoxlanıla bilmir"
        return out
    t = T[T["il"] == year]
    for r in t.itertuples():
        out[f"model_riski_ferq_{r.gosterici}"] = r.ferq
        out[f"tesir_{r.gosterici}"] = max(float(r.elverissiz_ferq), 0.0) if np.isfinite(r.elverissiz_ferq) else 0.0
    out["model_riski_xeberdarliq"] = bool(t["xeberdarliq"].any()) if len(t) else False
    out["ehtimal_menbe"] = (f"model riski (P×T deyil): köhnəlməmiş konsensus ({', '.join(sorted(set(';'.join(t['menbeler']).split(';')) - {''}))}) "
                            f"ilə baza fərqi; köhnəlmiş xaric: {t['kohnelmis_xaric'].iloc[0] if len(t) else ''}; hədd {t['hedd'].iloc[0] if len(t) else ''} f.b.")
    return out


def threshold_sensitivity(res: simulate.SimResult) -> pd.DataFrame:
    """Outcome risks R11–R13 (audit M3): P(threshold crossing) on a grid of thresholds, with the distance of the
    baseline to the threshold in σ units and P from the core residual alone (how much is mere proximity of the
    baseline to the threshold, not risk factors)."""
    p = factors.params()
    j = res.col(res.score_year)
    spec = {"R12": ("cpi", +1, p["cpi_threshold"], (4.0, 5.0, 5.5, 6.0, 6.5, 7.0, 8.0)),
            "R13": ("g", -1, p["nonoil_gar_threshold"], (0.0, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0)),
            "R11": ("fis", -1, p["fiscal_threshold"], (-3.0, -2.0, -1.5, -1.0, -0.5, 0.0))}
    rows = []
    for rid, (kind, side, thr0, grid) in spec.items():
        x = res.total(kind)[:, j]
        med = float(np.median(x))
        sd = float(x.std())
        rr = {"g": res.comp_g, "cpi": res.comp_cpi, "fis": res.comp_fis}[kind]["resid"][:, j]
        core = med + rr - np.median(rr)          # same median, core residual only: pure proximity to the threshold
        for h in grid:
            P = float((x > h).mean()) if side > 0 else float((x < h).mean())
            Pc = float((core > h).mean()) if side > 0 else float((core < h).mean())
            rows.append({"risk_id": rid, "gosterici": kind, "il": res.score_year, "hedd": h, "esas_hedd": bool(abs(h - thr0) < 1e-9),
                         "median": med, "baza": float(res.base[kind][j]), "mesafe_sigma": (h - med) / sd * side if sd else np.nan,
                         "P": P, "P_yalniz_qaliq": Pc, "P_amillerin_payi": P - Pc})
    return pd.DataFrame(rows)


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
        if r.nov == "model":                           # R19: forecast disagreement (D3), outside the MC and the heat map
            out.update(model_risk(res.score_year, res))
        elif rid in OUTCOME:
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
        out.setdefault("istilik_xeritesi", True)
        if not out["istilik_xeritesi"]:            # R19: separate indicator, not a P × I cell (audit M3)
            out["P_bal"], out["I_bal"] = 0, 0
        out["skor"] = out["P_bal"] * out["I_bal"]
        out["gozlenilen_itki_g"] = out["ehtimal"] * max(out["tesir_g"], 0)
        rows.append(out)
    S = pd.DataFrame(rows)
    S["prioritet"] = np.where(S["skor"] >= p["score_high"], "yüksək",
                              np.where(S["skor"] >= p["score_medium"], "orta", "aşağı"))
    S.loc[~S["istilik_xeritesi"].astype(bool), "prioritet"] = "ayrıca göstərici"
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


D5_RISK = (("brent", "R01"), ("azeri", "R01"), ("sofaz", "R01"), ("usd_azn", "R03"), ("policy_rate", "R02"),
          ("bfb", "R02"), ("vix", "R02"), ("ust", "R02"), ("cpi", "R12"), ("dsk_gdp_nonoil", "R13"),
          ("dsk_budget", "R11"), ("gpr", "R06"), ("epu", "R06"), ("strategic_reserves", "R03"))


def _d5_risk(ind: str) -> str:
    return next((rid for k, rid in D5_RISK if str(ind).startswith(k)), "")


def alerts(S: pd.DataFrame, res: simulate.SimResult, ind: pd.DataFrame, measures: pd.DataFrame | None = None,
           feed_status: pd.DataFrame | None = None, res_live: simulate.SimResult | None = None,
           monitor: pd.DataFrame | None = None, d2: pd.DataFrame | None = None) -> pd.DataFrame:
    """Alert types: yüksək prioritet, skor artımı, göstərici həddi, baza köhnəlib (live view vs baseline),
    tədbir gecikir, məlumat köhnəlib (v1 feeds and v2 D2 freshness), gündəlik monitor (D5 'xəbərdarlıq'),
    model riski (R19). `res` is the baseline-centred run; `res_live` the live-conditioned one."""
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
    rl = res_live if res_live is not None else res
    j = rl.col(rl.score_year)
    for kind, nm, unit in (("g", "qeyri-neft artımının", "%"), ("cpi", "inflyasiyanın", "%"),
                           ("fis", "büdcə balansının", "% ÜDM")):
        med = float(np.median(rl.total(kind)[:, j]))
        base = float(rl.base[kind][j])
        if abs(med - base) >= (1.0 if kind != "fis" else 0.5):
            add("baza köhnəlib", "orta", {"g": "R13", "cpi": "R12", "fis": "R11"}[kind],
                f"{rl.score_year}: canlı məlumatla şərtləndirilmiş {nm} medianı {med:.1f}{unit} — rəsmi baza "
                f"{base:.1f}{unit}. Fərq həddi aşır: yuxarı axın modelinin fərziyyələrinin yenilənməsi tövsiyə olunur")
    c = rl.meta["brent_centre"][j]
    if abs(c / rl.brent_base[j] - 1) >= 0.20:
        add("baza köhnəlib", "orta", "R01",
            f"{rl.score_year}: Brent mərkəzi yolu {c:.0f} USD (canlı) — makro fərziyyə {rl.brent_base[j]:.0f} USD")
    if monitor is not None and len(monitor):
        w = monitor[monitor["signal"].astype(str).str.startswith("xəbərdarlıq")].drop_duplicates("indicator")
        for r in w.itertuples():
            z = f", z = {r.z_score:.1f}" if pd.notna(getattr(r, "z_score", np.nan)) else ""
            add("gündəlik monitor", "orta", _d5_risk(r.indicator),
                f"{r.label_az}: {r.latest:.4g} ({r.date}){z} — {r.signal}")
    if d2 is not None and len(d2) and "tazelik" in d2:
        for r in d2[d2["tazelik"].isin(["köhnə", "köhnəlir"])].itertuples():
            add("məlumat köhnəlib", "aşağı" if r.tazelik == "köhnəlir" else "orta", "",
                f"{r.feed} ({r.source}): son müşahidə {r.last_obs}, {int(r.yas_gun)} gün — {r.tazelik}; status: {r.status}")
        for r in d2[d2["status"].astype(str).str.startswith(("xəta", "uğursuz"))].itertuples():
            add("axın xətası", "orta", "", f"{r.feed}: {r.status} — son yaxşı keş istifadə olunur")
    for r in S[S["risk_id"] == "R19"].itertuples():
        if bool(getattr(r, "model_riski_xeberdarliq", False)):
            add("model riski", "orta", "R19", f"{r.ad}: {r.ehtimal_menbe}; əlverişsiz fərq {max(r.tesir_g, r.tesir_cpi):.2f} f.b. "
                f"(hədd {p.get('model_risk_gap_pp', 0.5):g} f.b.; alternativ paylanma FR2_model_risk.csv)")
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
