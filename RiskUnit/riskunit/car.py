"""Capital-at-Risk of the economy (RiskUnit v2, U4): sovereign net worth ("fiscal capital"),
SOFAZ adequacy under stress, a contingent-claims distance-to-distress approximation and the
macro "X-at-Risk" summary.

Fiscal capital NW_t (mln USD) = SOFAZ_t + CBAR reserves_t − public debt_t (− called contingent
liabilities in the '+ şərti öhdəliklər' variant), simulated jointly (dsa.engine) for 2026–2030:
  SOFAZ_t   = SOFAZ_{t−1}·(1 + R_t + carry) + (inflow_t − transfer_t)/e_t,
              R_t from the VaR copula (coupled to the path's Brent), inflow_t = Ministry 'base 60'
              SOFAZ revenue × Brent_t / Ministry Brent (elasticity 1, ASSUMPTION), transfer_t =
              Ministry plan (the budget gap is debt-financed, φ = 1, as in dsa.py);
  CBAR_t    = CBAR_{t−1} + κ·ΔCA_t (κ = 0,1; ΔCA from the OxLon Brent sensitivity of the current
              account), and −60 % in a devaluation year (2015 analogue) — ASSUMPTIONS;
  debt_t    = dsa.debt_paths (MinFin stock, φ = 1).
CaR_q = E[NW] − Q_{1−q}(NW); ES_q = E[NW] − E[NW | NW ≤ Q_{1−q}]. Thresholds are parameters
(Ministry decision, V1b DR10). Outputs K1, K2, K4, K5.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import config, dsa, parametrler

YEARS = config.FORECAST_YEARS
PEG = 1.70
_P = parametrler.get
KAPPA_CA = _P("car_kappa_ca", 0.1)        # CBAR share of the oil-driven CA deviation (most of it is in SOFAZ inflows)
CBAR_DEVAL_DRAIN = _P("car_cbar_deval_drain", 0.60)   # reserve loss in a devaluation year (2015: 13,8 → 5,0 bn USD)
CARRY = {"fixed_income": None, "equities": _P("car_carry_equities", 0.015),
         "real_estate": _P("car_carry_real_estate", 0.03), "gold": _P("car_carry_gold", 0.0)}   # None = UST 5y yield
CBAR_AVAILABLE = _P("cca_cbar_available", 0.5)        # CCA: share of CBAR reserves available to the sovereign
APPETITE = {"nw_gdp_min_pct": (50.0, 75.0), "sofaz_cover_years_min": 3.0}


def _x(V1, kod, col="mln_usd"):
    return dsa._x(V1, kod, col)


def sofaz_lines(V1):
    from . import var
    return var.portfolios(V1)["sofaz"]


def ca_slope(B: pd.DataFrame) -> np.ndarray:
    """mln USD of current account per +1 USD/bbl (OxLon: CA under Brent lo80/hi80)."""
    from . import spine
    lo = spine.macro_series("current_account_brent_lo80", "forecast")["value"].reindex(YEARS).to_numpy()
    hi = spine.macro_series("current_account_brent_hi80", "forecast")["value"].reindex(YEARS).to_numpy()
    return (hi - lo) / (B["brent_usd_hi80"].to_numpy() - B["brent_usd_lo80"].to_numpy())


def nw_paths(E: dict, with_cl: bool = False, fis=None) -> dict:
    from . import exposures, var
    V1, n, e, res = E["V1"], E["n"], E["e"], E["res"]
    plan = exposures.ministry_sofaz_plan()
    sl = sofaz_lines(V1)
    P0 = _x(V1, "sofaz_total")
    ust5 = float(E.get("ust5_level", 4.0))
    shares = {k: _x(V1, f"sofaz_class_{k}") / sl["value"] for k in CARRY}
    carry = sum(s * (ust5 / 100 if CARRY[k] is None else CARRY[k]) for k, s in shares.items())
    slope = ca_slope(E["B"])
    R0 = _x(V1, "cbar_reserves")
    debt = dsa.debt_paths(E, E["fis"] if fis is None else fis, with_cl=with_cl)
    T = len(YEARS)
    S, C, NW, cover = (np.zeros((n, T)) for _ in range(4))
    s_prev, c_prev = np.full(n, P0), np.full(n, R0)
    for t, y in enumerate(YEARS):
        frac = 0.5 if (y == 2026 and config.as_of().year == 2026) else 1.0
        R = var.pnl_components(E["moves"][t], sl["lines"]).sum(axis=1).to_numpy() / sl["value"]
        R = np.expm1(np.log1p(np.clip(R, -0.95, None)) * frac) + carry * frac
        infl = plan.at[y, "sofaz_rev_azn"] * res.brent[:, t] / plan.at[y, "brent"]
        out = plan.at[y, "sofaz_exp_azn"]
        S[:, t] = s_prev * (1 + R) + (infl - out) * frac / e[:, t]
        dca = slope[t] * (res.brent[:, t] - E["brent_base"][t]) * frac
        new_dev = res.events["R03"][:, t]
        C[:, t] = np.maximum(0.0, (c_prev + KAPPA_CA * dca) * np.where(new_dev, 1 - CBAR_DEVAL_DRAIN, 1.0))
        NW[:, t] = S[:, t] + C[:, t] + (debt["cash"][:, t] - debt["D"][:, t]) / e[:, t]
        cover[:, t] = S[:, t] * e[:, t] / plan.at[y, "transfer_azn"]
        s_prev, c_prev = S[:, t], C[:, t]
    gdp_usd = E["Y"] / e
    return {"S": S, "C": C, "NW": NW, "NW_gdp": NW / gdp_usd * 100, "cover": cover, "debt": debt,
            "carry": carry, "plan": plan}


def car_table(E: dict) -> tuple[pd.DataFrame, dict]:
    rows, keep = [], {}
    for name, cl in (("şərti öhdəliklər xaric", False), ("şərti öhdəliklər daxil", True)):
        P = nw_paths(E, with_cl=cl)
        keep[cl] = P
        for t, y in enumerate(YEARS):
            x, xg = P["NW"][:, t], P["NW_gdp"][:, t]
            m = x.mean()
            r = {"variant": name, "il": y, "horizont_il": round(y - config.as_of().year
                                                               + (13 - config.as_of().month) / 12, 2),
                 "NW_orta_mln_usd": m, "NW_p50": np.median(x)}
            for q in (0.95, 0.99):
                Q = np.quantile(x, 1 - q)
                r[f"NW_p{int(round((1 - q) * 100)):02d}"] = Q
                r[f"CaR{int(q * 100)}_mln_usd"] = m - Q
                r[f"ES{int(q * 100)}_mln_usd"] = m - x[x <= Q].mean()
            r["NW_ÜDM_orta_pct"], r["NW_ÜDM_p05_pct"] = xg.mean(), np.quantile(xg, 0.05)
            for h in APPETITE["nw_gdp_min_pct"]:
                r[f"P_NW_ÜDM_lt_{int(h)}"] = float((xg < h).mean())
            r["P_NW_menfi"] = float((x < 0).mean())
            r["ARDNF_p05_mln_usd"], r["ARDNF_p50_mln_usd"] = np.quantile(P["S"][:, t], 0.05), np.median(P["S"][:, t])
            r["AMB_p05_mln_usd"] = np.quantile(P["C"][:, t], 0.05)
            r["qeyd"] = (f"CaR = orta − kvantil; ARDNF daşıma gəliri {P['carry'] * 100:.1f}%/il (FƏRZİYYƏ); "
                         "risk iştahı həddləri Nazirlik qərarıdır (DR10)")
            rows.append(r)
    return pd.DataFrame(rows), keep


# ---------------------------------------------------------------- SOFAZ adequacy under S1–S8
def stress_brent_paths() -> dict:
    """Brent paths of the standing stress set — mirrors measures.stress_scenarios() (keep in sync)."""
    from . import simulate, spine
    T = len(YEARS)
    L, B = spine.live(), spine.baseline()
    centre = list(simulate.run(n=200).meta["brent_centre"])
    y26 = [L["brent_ytd_avg"] * 0.75 + 0.25 * x for x in (45.0, 60.0)]
    s1 = [y26[0]] + [45.0] * (T - 1)
    return {"istinad": (centre, None), "S1": (s1, None), "S2": (centre, None), "S3": (s1, 2027),
            "S4": (centre, None), "S5": (centre, None),
            "S6": ([centre[0]] + [centre[k] * 0.95 ** k for k in range(1, T)], None), "S7": (centre, None),
            "S8": ([y26[1], 60.0] + list(B["brent_usd"].iloc[2:]), None)}


def _cond_return(A_years: list, sl: dict, dlb: float, t: int) -> float:
    from . import var
    a = A_years[t]
    k = max(50, int(0.02 * len(a)))
    idx = np.argsort(np.abs(a["brent"].to_numpy() - dlb))[:k]
    return float((var.pnl_components(a.iloc[idx], sl["lines"]).sum(axis=1) / sl["value"]).mean())


def sofaz_adequacy(E: dict, stress: pd.DataFrame | None, P_base: dict) -> pd.DataFrame:
    from . import exposures, factors, spine
    V1, plan = E["V1"], exposures.ministry_sofaz_plan()
    sl = sofaz_lines(V1)
    P0, carry = _x(V1, "sofaz_total"), P_base["carry"]
    dsz = factors.params()["devaluation_size"]
    hist_b = float(spine.annual_panel()["brent"].loc[config.LAST_ACTUAL])
    fisdev = {}
    if stress is not None and len(stress):
        f = stress[stress["gosterici"].str.startswith("büdcə")]
        fisdev = {sid: g.set_index("il")["sapma"].reindex(YEARS).to_numpy() for sid, g in f.groupby("ssenari")}
    rows = []
    paths = stress_brent_paths()
    ref = {}
    for sid, (bp, dev_year) in paths.items():
        for psi in (0, 1):
            S, prev_b = P0, hist_b
            for t, y in enumerate(YEARS):
                frac = 0.5 if (y == 2026 and config.as_of().year == 2026) else 1.0
                e = PEG * (1 + dsz) if (dev_year and y >= dev_year) else PEG
                dlb = np.log(bp[t] / prev_b)
                R = _cond_return(E["moves"], sl, dlb, t) * frac + carry * frac
                gap = max(0.0, -fisdev.get(sid, np.zeros(len(YEARS)))[t]) / 100 * E["Y0"][t] * frac if sid != "istinad" else 0.0
                infl = plan.at[y, "sofaz_rev_azn"] * bp[t] / plan.at[y, "brent"] * frac
                S = S * (1 + R) + (infl - plan.at[y, "sofaz_exp_azn"] * frac - psi * gap) / e
                prev_b = bp[t]
                if sid == "istinad":
                    ref[(psi, y)] = S
                rows.append({"ssenari": sid, "psi_kesir_ARDNF_den": psi, "il": y, "brent": bp[t],
                             "ARDNF_mln_usd": S, "ARDNF_istinaddan_ferq_mln_usd": S - ref.get((psi, y), S),
                             "transfer_plan_mln_azn": plan.at[y, "transfer_azn"], "elave_cixaris_mln_azn": psi * gap,
                             "ortuk_ili": S * e / (plan.at[y, "transfer_azn"] + psi * gap / frac),
                             "portfel_gelirliyi_sertli": R, "manat_mezennesi": e})
    out = pd.DataFrame(rows)
    sto = []
    for t, y in enumerate(YEARS):
        cv = P_base["cover"][:, t]
        sto.append({"ssenari": "stoxastik", "psi_kesir_ARDNF_den": 0, "il": y,
                    "ARDNF_mln_usd": float(np.median(P_base["S"][:, t])),
                    "ARDNF_p05_mln_usd": float(np.quantile(P_base["S"][:, t], 0.05)),
                    "ortuk_ili": float(np.median(cv)), "ortuk_ili_p05": float(np.quantile(cv, 0.05)),
                    "P_ortuk_lt_hedd": float((cv < APPETITE["sofaz_cover_years_min"]).mean()),
                    "transfer_plan_mln_azn": plan.at[y, "transfer_azn"]})
    out = pd.concat([out, pd.DataFrame(sto)], ignore_index=True)
    out["qeyd"] = ("ψ=1: büdcə balansının ssenari sapması ARDNF-dən əlavə transfertlə örtülür; ψ=0: yalnız plan "
                   "transferti; gəlirlilik = Brent dəyişməsinə şərti kopula ortası + daşıma gəliri; inflow ∝ Brent")
    return out


# ---------------------------------------------------------------- CCA (Gray–Merton–Bodie), approximation
def merton(A: float, DB: float, sigma: float, r: float, T: float = 1.0) -> dict:
    d1 = (np.log(A / DB) + (r + sigma ** 2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    put = DB * np.exp(-r * T) * stats.norm.cdf(-d2) - A * stats.norm.cdf(-d1)
    spread = max(0.0, -np.log(max(1e-300, 1 - put / (DB * np.exp(-r * T)))) / T)
    return {"DD": float(d2), "PD_risk_neytral": float(stats.norm.cdf(-d2)), "put_mln_usd": float(put),
            "spred_bp": float(spread * 1e4)}


def _sofaz_sigma_v3(default: float) -> tuple[float, str]:
    """Annual SOFAZ asset volatility implied by the V3 1-year t-copula VaR99 (σ ≈ VaR99% / z99)."""
    f = config.OUTPUT / "V3_var_es.csv"
    try:
        v = pd.read_csv(f)
        r = v[(v.portfel == "sofaz") & (v.horizont == "1il") & (v.metod == "mc_tcop") & (v.etibarlilik == 0.99)]
        return float(r["VaR_pct"].iloc[0]) / 100 / stats.norm.ppf(0.99), "V3 (ARDNF 1 il, t-kopula VaR99 / z99)"
    except Exception:                                              # noqa: BLE001
        return default, "kopula illik paylanmasının sd-si"


def cca_table(E: dict, K4: pd.DataFrame, P_base: dict) -> pd.DataFrame:
    """Sovereign CCA (Gray–Merton–Bodie). v2.4 (audit M7): rebuilt with partial CBAR availability, CBAR
    reserve volatility (devaluation drain), SOFAZ σ from V3 and the full guaranteed debt — and DEMOTED to an
    appendix: with net liquid FX assets ≈ 4× the distress barrier the distance-to-distress stays » 3 in every
    variant, so the measure is uninformative for decisions (K2 CaR and K4 cover are the decision metrics)."""
    from . import var
    V1 = E["V1"]
    sl = sofaz_lines(V1)
    R1 = var.pnl_components(E["moves"][1], sl["lines"]).sum(axis=1).to_numpy() / sl["value"]
    sig_cop = float(np.std(np.log1p(np.clip(R1, -0.95, None))))
    sig_v3, sig_src = _sofaz_sigma_v3(sig_cop)
    S0, C0 = _x(V1, "sofaz_total"), _x(V1, "cbar_reserves")
    ext, gext = _x(V1, "debt_external"), _x(V1, "cl_guaranteed_ext")
    st = E.get("start") or {}
    tot_pub = float(st.get("D0") or _x(V1, "debt_public_total", "mln_azn")) / PEG
    guar = _x(V1, "cl_guaranteed_total")
    r = float(E.get("ust2_level", 4.0)) / 100
    db_fx = (dsa.AMORT_EXT * ext + dsa.AMORT_GUAR * gext) + 0.5 * ((1 - dsa.AMORT_EXT) * ext + (1 - dsa.AMORT_GUAR) * gext)
    st_all = dsa.AMORT_EXT * ext + dsa.AMORT_DOM * (tot_pub - ext) + dsa.AMORT_GUAR * guar
    db_all = st_all + 0.5 * (tot_pub + guar - st_all)
    p_dev = float(np.mean(E["res"].events["R03"][:, 1])) if E["res"].events["R03"].shape[1] > 1 else 0.0
    sig_c = CBAR_DEVAL_DRAIN * np.sqrt(p_dev * (1 - p_dev))             # CBAR reserves: devaluation-drain risk
    A4 = S0 + CBAR_AVAILABLE * C0
    w = S0 / A4
    sig4 = float(np.sqrt((w * sig_v3) ** 2 + ((1 - w) * sig_c) ** 2))
    s3 = K4[(K4.ssenari == "S3") & (K4.psi_kesir_ARDNF_den == 1)].set_index("il")["ARDNF_mln_usd"]
    d_s3 = P_base["debt"]["D"][:, -1] / E["e"][:, -1]
    rows = []
    for name, A, DB, sig, note in (
            ("V1: likvid valyuta aktivləri (ARDNF+AMB) / xarici dövlət + zəmanətli borc", S0 + C0, db_fx,
             sig_cop * S0 / (S0 + C0), "v2.3 yanaşması: AMB ehtiyatları risksiz və tam konsolidasiya"),
            ("V2: likvid valyuta aktivləri / bütün dövlət + zəmanətli borc (USD, 1,70)", S0 + C0, db_all,
             sig_cop * S0 / (S0 + C0), "v2.3 yanaşması: AMB ehtiyatları risksiz və tam konsolidasiya"),
            ("V3: S3 (Brent 45 + devalvasiya) sonrası 2030 ARDNF + AMB / 2030 stoxastik borcun p95-i",
             float(s3.iloc[-1]) + C0 * (1 - CBAR_DEVAL_DRAIN),
             float(np.quantile(d_s3, 0.95)) * db_all / (tot_pub + guar), sig_cop, "stress ssenarisi S3"),
            (f"V4 (yenidən qurulmuş): ARDNF + AMB-nin {CBAR_AVAILABLE:.0%}-i / bütün dövlət + zəmanətli borc "
             f"({guar * PEG:,.1f} mln AZN)".replace(",", " ").replace(".", ","), A4, db_all, sig4,
             f"σ: ARDNF {sig_v3:.3f} ({sig_src}), AMB {sig_c:.3f} (devalvasiya ehtimalı {p_dev:.3f} × itki "
             f"{CBAR_DEVAL_DRAIN:.0%})")):
        m = merton(A, DB, sig, r)
        rows.append({"variant": name, "aktivler_mln_usd": A, "qeza_hedd_mln_usd": DB, "aktiv_volatilliyi": sig,
                     "risksiz_faiz": r, "horizont_il": 1.0, **m,
                     "qezaya_qeder_aktiv_dusmesi_pct": (1 - DB / A) * 100,
                     "DD_3_ucun_lazim_sigma": float(np.log(A / DB) / 3.0),
                     "status": "ƏLAVƏ — məlumatsız göstərici (qərar üçün istifadə olunmur)",
                     "qeyd": "TƏXMİNİ YANAŞMA (əlavə): aktivlər log-normal; qəza həddi = qısamüddətli + 0,5×uzunmüddətli "
                             "borc (KMV); gələcək neft gəlirlərinin və manat öhdəliklərinin bazar dəyəri daxil deyil. "
                             "Suveren xalis kreditordur → DD » 3 bütün variantlarda; qərar göstəriciləri: K2 (CaR), "
                             "K4 (ARDNF örtüyü). " + note})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- X-at-Risk summary
def at_risk_summary(E: dict, K2: pd.DataFrame, K3: pd.DataFrame, P_base: dict, V3: pd.DataFrame | None) -> pd.DataFrame:
    res, B = E["res"], E["B"]
    sy = config.score_year()
    j = res.col(sy)
    rows = []

    def add(kod, ad, unit, yr, base, x, adverse="low", src="RU birgə Monte Karlo (simulate.py)", note=""):
        q05, q10, q50, q95 = np.quantile(x, [0.05, 0.10, 0.50, 0.95])
        if adverse == "low":
            tail = x[x <= q10].mean()
            risk = base - q05
        else:
            tail = x[x >= np.quantile(x, 0.90)].mean()
            risk = q95 - base
        rows.append({"gosterici": kod, "ad": ad, "vahid": unit, "il": yr, "baza": base, "p05": q05, "p10": q10,
                     "median": q50, "p95": q95, "ES10_quyruq": tail, "risk_altinda": risk,
                     "pis_istiqamet": "aşağı" if adverse == "low" else "yuxarı", "menbe": src, "qeyd": note})
    add("GaR", "ÜDM-ə risk (qeyri-neft real artım)", "%", sy, res.base["g"][j], res.total("g")[:, j],
        note="risk_altinda = baza − p05")
    add("IaR", "İnflyasiyaya risk (illik orta İQİ)", "%", sy, res.base["cpi"][j], res.total("cpi")[:, j], "high",
        note="risk_altinda = p95 − baza")
    add("FaR", "Fiskal risk (büdcə balansı / ÜDM)", "% ÜDM", sy, res.base["fis"][j], res.total("fis")[:, j],
        note="bütün fiskal kanallar, prosiklik investisiya reaksiyası daxil")
    slope = ca_slope(B)
    gdp_usd = E["Y"][:, j] / E["e"][:, j]
    ca = (B["current_account"].to_numpy()[j] + slope[j] * (res.brent[:, j] - E["brent_base"][j])) / gdp_usd * 100
    ca_base = B["current_account"].to_numpy()[j] / (E["Y0"][j] / PEG) * 100
    add("CAaR", "Cari əməliyyatlar balansına risk (% ÜDM)", "% ÜDM", sy, ca_base, ca,
        src="OxLon cari hesab–Brent həssaslığı × RU Brent paylanması", note="yalnız Brent kanalı")
    for yr in (sy, YEARS[-1]):
        k = K3[(K3.variant.str.startswith("əsas: RU")) & (K3.il == yr)].iloc[0]
        rows.append({"gosterici": "DaR", "ad": "Borca risk (dövlət borcu / ÜDM)", "vahid": "% ÜDM", "il": yr,
                     "baza": k["baza_FR1_MN"], "p05": k["p05"], "p10": k["p10"], "median": k["p50"], "p95": k["p95"],
                     "ES10_quyruq": np.nan, "risk_altinda": k["p95"] - k["baza_FR1_MN"], "pis_istiqamet": "yuxarı",
                     "menbe": "dsa.py stoxastik DSA", "qeyd": (f"P(borc > 20% ÜDM) = {k.get('P_borc_gt_20', np.nan):.3f}; "
                                                               f"P(> 25%) = {k.get('P_borc_gt_25', np.nan):.3f}; "
                                                               f"P(> 30%, DR10) = {k['P_borc_gt_30']:.3f}")})
        t = YEARS.index(yr)
        add("SaR", "ARDNF aktivlərinə risk", "mln USD", yr, float(P_base["S"][:, t].mean()), P_base["S"][:, t],
            src="car.py (kopula gəlirliliyi + neft axınları + plan transferti)", note="baza = simulyasiya ortası")
        c = K2[(K2.variant == "şərti öhdəliklər xaric") & (K2.il == yr)].iloc[0]
        rows.append({"gosterici": "CaR", "ad": "Fiskal kapitala risk (ARDNF + AMB − dövlət borcu)", "vahid": "mln USD",
                     "il": yr, "baza": c["NW_orta_mln_usd"], "p05": c["NW_p05"], "p10": np.nan, "median": c["NW_p50"],
                     "p95": np.nan, "ES10_quyruq": np.nan, "risk_altinda": c["CaR95_mln_usd"], "pis_istiqamet": "aşağı",
                     "menbe": "car.py", "qeyd": f"CaR99 = {c['CaR99_mln_usd']:.0f}; ES99 = {c['ES99_mln_usd']:.0f}"})
    if V3 is not None:
        for pid, meth, kod, ad in (("oil_rev", "sim_joint", "ORaR", "Büdcənin neft gəlirlərinə risk"),
                                   ("sofaz", "mc_tcop", "VaR_ARDNF", "ARDNF portfelinin bazar VaR-ı (1 il)")):
            v = V3[(V3.portfel == pid) & (V3.metod == meth) & (V3.horizont == "1il")]
            for q in (0.95, 0.99):
                r = v[v.etibarlilik == q]
                if len(r):
                    r = r.iloc[0]
                    unit = "mln AZN" if pid == "oil_rev" else "mln USD"
                    val = r["VaR_mln_azn"] if pid == "oil_rev" else r["VaR_mln_usd"]
                    es = r["ES_mln_azn"] if pid == "oil_rev" else r["ES_mln_usd"]
                    rows.append({"gosterici": f"{kod}{int(q * 100)}", "ad": ad, "vahid": unit, "il": sy,
                                 "baza": r["portfel_deyeri_mln_usd"] * (PEG if pid == "oil_rev" else 1),
                                 "risk_altinda": val, "ES10_quyruq": es, "pis_istiqamet": "aşağı",
                                 "menbe": "var.py", "qeyd": f"etibarlılıq {q:.0%}; {r['metod_ad']}"})
    return pd.DataFrame(rows)


def run(ctx: dict | None = None) -> dict:
    ctx = ctx if ctx is not None else {}
    from . import feeds_market as fm, measures
    if "K3" not in ctx:
        dsa.run(ctx)
    E, K3 = ctx["engine"], ctx["K3"]
    daily = ctx["var"]["daily"] if "var" in ctx else fm.load_panels()[0]
    for k in ("ust2", "ust5"):
        if k in daily:
            E[f"{k}_level"] = float(daily[k].dropna().iloc[-1])
    K2, keep = car_table(E)
    try:
        stress = ctx.get("stress") if ctx.get("stress") is not None else measures.stress_scenarios()
        st_src = "measures.stress_scenarios() (cari)"
    except Exception as exc:                                       # noqa: BLE001
        f = config.OUTPUT / "FR3_stress_scenarios.csv"
        stress = pd.read_csv(f) if f.exists() else None
        st_src = f"FR3_stress_scenarios.csv (saxlanılmış; {type(exc).__name__})"
    K4 = sofaz_adequacy(E, stress, keep[False])
    K4["stress_menbe"] = st_src
    K5 = cca_table(E, K4, keep[False])
    V3 = ctx["var"]["V3"] if "var" in ctx else (pd.read_csv(config.OUTPUT / "V3_var_es.csv")
                                                  if (config.OUTPUT / "V3_var_es.csv").exists() else None)
    K1 = at_risk_summary(E, K2, K3, keep[False], V3)
    out = {}
    desc = {"K1_at_risk_summary": "Makro «X-risk altında» xülasəsi: ÜDM, inflyasiya, fiskal, cari hesab, borc, ARDNF, "
                                  "fiskal kapital, neft gəlirləri, ARDNF VaR — baza, kvantillər, risk altında olan məbləğ",
            "K2_car_distribution": "Fiskal kapitalın (ARDNF + AMB − dövlət borcu) 2026–2030 paylanması: CaR/ES 95/99%, "
                                   "risk iştahı həddlərinin aşılma ehtimalları (şərti öhdəliklərlə və onlarsız)",
            "K4_sofaz_adequacy": "ARDNF-in adekvatlığı: S1–S8 stress ssenarilərində aktivlərin yolu və transfert örtüyü "
                                 "(il), stoxastik örtük",
            "K5_cca": "ƏLAVƏ: suveren şərti öhdəliklər yanaşması (CCA, Gray–Merton–Bodie) — qəzaya qədər məsafə, "
                      "risk-neytral ehtimal, aktivlərin qəzaya qədər düşmə payı (TƏXMİNİ; suveren xalis kreditor olduğu "
                      "üçün məlumatsızdır, qərar göstəricisi deyil)"}
    for name, df in (("K1_at_risk_summary", K1), ("K2_car_distribution", K2), ("K4_sofaz_adequacy", K4), ("K5_cca", K5)):
        p = config.OUTPUT / f"{name}.csv"
        df.round(6).to_csv(p, index=False, lineterminator="\n")
        fm.register_catalog(f"{name}.csv", "car", desc[name], list(df.columns), "gündəlik")
        out[name] = str(p)
    return out


if __name__ == "__main__":
    import sys
    ctx = {"n": int(sys.argv[1]) if len(sys.argv) > 1 else config.N_SIM}
    r = run(ctx)
    print(r)
    print(pd.read_csv(r["K1_at_risk_summary"])[["gosterici", "il", "baza", "p05", "median", "p95", "risk_altinda"]].round(2))
