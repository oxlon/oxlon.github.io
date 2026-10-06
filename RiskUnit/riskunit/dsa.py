"""Stochastic debt sustainability analysis (Methodology Blueprint L4 / FR3) — RiskUnit v2.

Joint draws (one path = one draw of the RU joint Monte Carlo, simulate.run):
  * real non-oil growth, CPI and the budget balance (% GDP) — all channels of simulate.py;
  * Brent and the conditional manat devaluation event;
  * annual global-market moves (UST yields, EUR/JPY/CNY/GBP vs USD, equities, gold) from the
    VaR layer's t-copula, coupled to each path by the rank of its Brent change (the copula's own
    Brent margin is replaced by simulate.py's Brent, the dependence with assets is kept).
Debt identity (mln AZN, FR1 convention φ = 1: the whole deficit is debt-financed):
  D_t = D_{t-1} − φ·bal_t + VAL_t + ΔINT_t (+ called guarantees and bank recapitalisation in the
  '+ şərti öhdəliklər' variant), with VAL = FX-debt revaluation (devaluation, cross rates) and
  ΔINT = floating-rate debt × ΔUST2y (+ called guarantees and bank recapitalisation in the
  '+ şərti öhdəliklər' variant).
Starting stock (v2.4 reconciliation, audit M7): the END-2025 stock of the MicroUnit FR1 dataset
(MinFin concept, 25 987,5 mln AZN) and the whole 2026 budget year are simulated — the same anchor as
FR1. The latest MinFin bulletin stock (V1 `debt_public_total`, July 2026) is used only as a CHECK of
the simulated mid-2026 path (columns `yoxlama_*`). Nominal GDP = FR1 baseline × (non-oil growth and
CPI deviations) + oil GDP ∝ Brent × FX. Variants: φ = 1 (FR1 rule), φ = 0,5 (half the deficit financed
from SOFAZ — replaces the v2.3 "investment reaction excluded" variant, which was identical because the
reaction is transfer-financed), and φ = 1 + contingent liabilities. Thresholds: the DR10 appetite
values (30/45/60 % GDP) are kept, plus informative thresholds (20/25 % GDP, GFN, debt service/revenue)
and IMF MAC-DSA benchmarks — all in input/parametrler.csv. No estimated time-series dynamics are
added: every stochastic element comes from simulate.py or the VaR copula. Outputs K3_dsa_fan.csv.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config, parametrler

YEARS = config.FORECAST_YEARS
_P = parametrler.get
THRESH_DEBT = (30.0, 45.0, 60.0)          # % GDP — risk-appetite parameters (Ministry decision, DR10)
THRESH_INFO = (_P("dsa_thr_debt_info_1", 20.0), _P("dsa_thr_debt_info_2", 25.0))   # informative, not appetite
THR_GFN = (_P("dsa_thr_gfn_info", 5.0), _P("dsa_thr_gfn_imf", 15.0))
THR_DEBT_IMF = _P("dsa_thr_debt_imf", 70.0)
THR_DS_REV = _P("dsa_thr_ds_rev", 10.0)
INT_EFF = _P("dsa_int_eff", 0.038)        # effective interest rate (MinFin, annualised H1-2026)
AMORT_EXT, AMORT_DOM, AMORT_GUAR = (_P("dsa_amort_ext", 0.119), _P("dsa_amort_dom", 0.074),
                                    _P("dsa_amort_guar", 0.131))   # yearly principal shares (MinFin)
CL_P0, CL_P_STRESS, CL_CALL = _P("dsa_cl_p0", 0.02), _P("dsa_cl_p_stress", 0.20), _P("dsa_cl_call", 0.50)
BANK_LOSS_DEVAL, BANK_LOSS_OIL, BANK_CAP_FLOOR = (_P("dsa_bank_loss_deval", 0.15), _P("dsa_bank_loss_oil", 0.05),
                                                  _P("dsa_bank_cap_floor", 0.10))
PHI_DEBT = _P("dsa_phi_debt", 1.0)        # share of the budget deficit financed by debt (FR1 convention)
PHI_DEBT_ALT = _P("dsa_phi_debt_alt", 0.5)
# A surplus retires at most the maturing principal; the excess is saved (no buy-backs below schedule).


def _x(V1: pd.DataFrame, kod: str, col: str = "mln_azn") -> float:
    r = V1.loc[V1["kod"] == kod, col]
    return float(r.iloc[0]) if len(r) and pd.notna(r.iloc[0]) else 0.0


def start_stock(V1: pd.DataFrame) -> dict:
    """End-of-last-actual-year public debt (FR1 dataset, MinFin concept) + its external share; the latest
    MinFin bulletin stock is returned as the check value (audit M7: one anchor with FR1)."""
    from . import spine
    chk, chk_date = _x(V1, "debt_public_total"), ""
    r = V1.loc[V1["kod"] == "debt_public_total", "tarix"] if "tarix" in V1.columns else []
    chk_date = str(r.iloc[0]) if len(r) else ""
    try:
        d = spine.micro_fr1_dataset().loc[config.LAST_ACTUAL]
        D0, ext = float(d["debt_azn"]), float(d["debt_ext_usd"]) * 1.70
        src = f"MikroUnit FR1 məlumat bazası, {config.LAST_ACTUAL}-ci ilin sonu (Maliyyə Nazirliyi anlayışı)"
        out = {"D0": D0, "ext_sh": ext / D0 if D0 else 0.33, "year_end": config.LAST_ACTUAL, "src": src,
               "check": chk, "check_date": chk_date, "sfa": 0.0, "anchored": False}
        nc = config.MICRO_DIR / "output" / "FR1_debt_nowcast.csv"
        if nc.exists():                     # FR1 v2.3.4: 2026 anchored on the MinFin bulletin via a one-off SFA
            r = pd.read_csv(nc).iloc[-1]
            out.update({"sfa": float(r["sfa_2026"]), "anchored": True, "target_2026": float(r["target_2026"]),
                        "check": float(r["stock_azn"]), "check_date": str(r["date"]),
                        "src": src + f"; 2026: FR1 birdəfəlik qalıq-axın düzəlişi {float(r['sfa_2026']):.1f} mln AZN "
                                     f"(MN bülleteni {r['date']} lövbəri, FR1_debt_nowcast.csv)"})
        return out
    except Exception:                                              # noqa: BLE001
        return {"D0": chk, "ext_sh": None, "year_end": None, "src": f"MN bülleteni ({chk_date}) — FR1 əlçatmazdır",
                "check": chk, "check_date": chk_date}


def couple(sim_dlb: np.ndarray, draws: pd.DataFrame, rng) -> pd.DataFrame:
    """Rank coupling: the k-th smallest simulated Brent change gets the copula draw with the
    k-th smallest Brent move (ties broken at random)."""
    n = len(sim_dlb)
    d = draws.sample(n=n, replace=len(draws) < n, random_state=int(rng.integers(1 << 31))).reset_index(drop=True)
    o_sim = np.argsort(sim_dlb + rng.normal(0, 1e-9, n))
    o_d = np.argsort(d["brent"].to_numpy() + rng.normal(0, 1e-9, n))
    out = pd.DataFrame(index=range(n), columns=d.columns, dtype=float)
    out.iloc[o_sim] = d.iloc[o_d].to_numpy()
    return out


def engine(n: int = config.N_SIM, seed: int = config.SEED, ctx: dict | None = None) -> dict:
    """Joint paths shared by dsa.py and car.py."""
    from . import factors, feeds_market as fm, simulate, spine, var
    ctx = ctx if ctx is not None else {}
    rng = np.random.default_rng(seed + 101)
    res = ctx.get("sim") or simulate.run(n=n, seed=seed)
    n = res.brent.shape[0]
    B = spine.baseline()
    V1 = pd.read_csv(config.OUTPUT / "V1_exposures.csv")
    monthly = ctx["var"]["monthly"] if "var" in ctx else fm.load_panels()[1]
    A = var.annual_factor_draws(monthly, n, seed)
    hist_b = float(spine.annual_panel()["brent"].loc[config.LAST_ACTUAL])
    lb = np.log(np.concatenate([np.full((n, 1), hist_b), res.brent], axis=1))
    moves = [couple(lb[:, t + 1] - lb[:, t], A, rng) for t in range(len(YEARS))]
    g = res.total("g") - res.base["g"][None, :]
    c = res.total("cpi") - res.base["cpi"][None, :]
    fis = res.total("fis")
    fis_noreact = fis - res.comp_fis["fiscal_react"]
    dev_on = np.cumsum(res.events["R03"], axis=1) > 0
    deval_size = factors.params()["devaluation_size"]
    e = 1.70 * (1 + deval_size * dev_on)                       # AZN per USD
    Y0 = B["fr1_gdp_n"].to_numpy()
    fl = spine.macro_fl()
    on = fl[(fl.series_code == "oil_nom") & (fl.source == "ours")].set_index("year")["value"].reindex(YEARS)
    gn = fl[(fl.series_code == "gdp_nom") & (fl.source == "ours")].set_index("year")["value"].reindex(YEARS)
    oil_sh = (on / gn).to_numpy()
    bb = B["brent_usd"].to_numpy()
    lev_non = np.cumprod((1 + g / 100) * (1 + c / 100), axis=1)
    Y = Y0[None, :] * ((1 - oil_sh)[None, :] * lev_non + oil_sh[None, :] * (res.brent / bb[None, :]) * e / 1.70)
    st = start_stock(V1)
    rev0 = B["fr1_rev_tot_n"].to_numpy() if "fr1_rev_tot_n" in B else None
    return {"start": st, "D0": st["D0"], "rev0": rev0, "res": res, "B": B, "V1": V1, "moves": moves, "fis": fis, "fis_noreact": fis_noreact, "e": e,
            "dev_on": dev_on, "Y": Y, "Y0": Y0, "oil_sh": oil_sh, "brent_base": bb, "n": n,
            "nu": A.attrs.get("nu"), "rng": rng}


def debt_paths(E: dict, fis: np.ndarray, with_cl: bool = False, phi: float = PHI_DEBT) -> dict:
    """Debt (mln AZN), debt/GDP (%), gross financing needs (% GDP) and the identity components."""
    V1, Y, e, n = E["V1"], E["Y"], E["e"], E["n"]
    rng = np.random.default_rng(config.SEED + (7 if with_cl else 3))
    st = E.get("start") or {}
    D0 = float(E.get("D0") or _x(V1, "debt_public_total"))
    ext_sh = st.get("ext_sh") or (_x(V1, "debt_external", "mln_usd") * 1.70 / D0 if D0 else 0.33)
    full_first = st.get("year_end") == YEARS[0] - 1          # stock at end of the previous year → full year
    ccy = {c: _x(V1, f"debt_ext_ccy_{c}", "pay_faiz") / 100 for c in ("EUR", "XDR", "JPY", "OTHER")}
    w = {"fx_eur": ccy["EUR"] + 0.2931 * ccy["XDR"], "fx_jpy": ccy["JPY"] + 0.0759 * ccy["XDR"],
         "fx_cny": 0.1228 * ccy["XDR"], "fx_gbp": 0.0744 * ccy["XDR"], "fx_oth": ccy["OTHER"]}
    flt = _x(V1, "debt_floating_total", "deyer") / 100
    guar = _x(V1, "cl_guaranteed_total")
    loans, cap = _x(V1, "bank_loans"), _x(V1, "bank_capital")
    T = len(YEARS)
    D = np.zeros((n, T)); GFN = np.zeros((n, T)); CASH = np.zeros((n, T)); cash = np.zeros(n)
    DS = np.full((n, T), np.nan); MID = np.full(n, np.nan)
    rev0, Y0 = E.get("rev0"), E.get("Y0")
    comp = {k: np.zeros((n, T)) for k in ("balans", "faiz_soku", "mezenne", "sert_ohdelik")}
    prev, e_prev = np.full(n, D0), np.full(n, 1.70)
    brent_low = E["res"].brent < 45.0
    for t in range(T):
        frac = 1.0 if full_first else (0.5 if (YEARS[t] == 2026 and config.as_of().year == 2026) else 1.0)
        bal = fis[:, t] / 100 * Y[:, t] * frac
        mv = E["moves"][t]
        cross = sum(wi * np.expm1(mv[f].to_numpy() * frac) for f, wi in w.items())
        fx_debt = prev * ext_sh
        val = fx_debt * ((e[:, t] / e_prev) * (1 + cross) - 1)
        dint = prev * flt * mv["ust2"].to_numpy() * frac / 100
        cl = np.zeros(n)
        if with_cl:
            stress = E["dev_on"][:, t] | brent_low[:, t]
            p = np.where(stress, CL_P_STRESS, CL_P0) * frac
            cl += (rng.random(n) < p) * guar * CL_CALL * (e[:, t] / 1.70)
            new_dev = E["res"].events["R03"][:, t]
            loss = np.where(new_dev, BANK_LOSS_DEVAL, np.where(brent_low[:, t], BANK_LOSS_OIL * frac, 0.0)) * loans
            cl += np.maximum(0.0, loss - (cap - BANK_CAP_FLOOR * loans))
        amort = prev * (ext_sh * AMORT_EXT + (1 - ext_sh) * AMORT_DOM) * frac
        flow = -phi * bal + dint + cl                     # net new borrowing need (mln AZN)
        repay = np.minimum(np.maximum(-flow, 0.0), amort)  # a surplus retires at most maturing debt ...
        cash += np.maximum(-flow, 0.0) - repay             # ... the rest is saved (treasury / SOFAZ)
        sfa = float(st.get("sfa", 0.0)) if (t == 0 and full_first) else 0.0   # FR1 one-off stock-flow adjustment
        D[:, t] = prev + np.maximum(flow, 0.0) - repay + val + sfa
        CASH[:, t] = cash
        GFN[:, t] = (-bal + amort + dint) / Y[:, t] * 100 / frac
        if rev0 is not None and Y0 is not None:                # debt service (interest + principal) / revenue
            DS[:, t] = (INT_EFF * prev * frac + amort) / (rev0[t] * Y[:, t] / Y0[t]) * 100 / frac
        if t == 0:
            MID = prev + 0.5 * (D[:, 0] - prev)                 # mid-year interpolation (bulletin check)
        comp["balans"][:, t], comp["faiz_soku"][:, t] = np.maximum(-phi * bal, 0.0) - np.minimum(
            np.maximum(phi * bal, 0.0), amort), dint
        comp["mezenne"][:, t], comp["sert_ohdelik"][:, t] = val, cl
        prev, e_prev = D[:, t], e[:, t]
    return {"D": D, "d": D / Y * 100, "GFN": GFN, "comp": comp, "D0": D0, "cash": CASH, "DS_rev": DS, "mid": MID}


def _az(x: float, nd: int = 1) -> str:
    return f"{x:,.{nd}f}".replace(",", " ").replace(".", ",") if np.isfinite(x) else "—"


def _d_last(E: dict) -> float:
    """Debt/GDP at the end of the last actual year (FR1 dataset) — the 'debt ratio rises' threshold."""
    from . import spine
    try:
        g = float(spine.micro_fr1_dataset().loc[config.LAST_ACTUAL, "gdp_n"])
        return float(E.get("D0")) / g * 100
    except Exception:                                              # noqa: BLE001
        return np.nan


QS = (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95)


def fan_table(E: dict) -> pd.DataFrame:
    rows = []
    base_fis = E["B"]["fr1_balance_pct"].to_numpy()
    det = {"Y": E["Y0"][None, :], "e": np.full((1, len(YEARS)), 1.70), "n": 1, "V1": E["V1"],
           "moves": [m.iloc[:1] * 0 for m in E["moves"]], "dev_on": np.zeros((1, len(YEARS)), bool),
           "res": type("R", (), {"brent": E["brent_base"][None, :], "events": {"R03": np.zeros((1, len(YEARS)), bool)}}),
           "start": E.get("start"), "D0": E.get("D0"), "rev0": E.get("rev0"), "Y0": E["Y0"]}
    base = debt_paths(det, base_fis[None, :])
    st = E.get("start") or {}
    fr1_d = E["B"]["fr1_debt_pct"].to_numpy() if "fr1_debt_pct" in E["B"] else np.full(len(YEARS), np.nan)
    variants = (("əsas: RU birgə simulyasiya (bütün fiskal kanallar)", E["fis"], False, PHI_DEBT),
                (f"maliyyələşmə: φ = {PHI_DEBT_ALT:.1f} (kəsirin yarısı ARDNF-dən, profisitin yarısı ARDNF-ə)".replace(".", ","), E["fis"], False,
                 PHI_DEBT_ALT),
                ("əsas + şərti öhdəliklər (zəmanət çağırışı, bank rekapitalizasiyası)", E["fis"], True, PHI_DEBT))
    for name, fis, cl, phi in variants:
        P = debt_paths(E, fis, with_cl=cl, phi=phi)
        for t, y in enumerate(YEARS):
            d = P["d"][:, t]
            q = np.quantile(d, QS)
            row = {"variant": name, "il": y, "baza_FR1_MN": base["d"][0, t], "orta": d.mean(),
                   **{f"p{int(x * 100):02d}": v for x, v in zip(QS, q)},
                   **{f"P_borc_gt_{int(h)}": float((d > h).mean()) for h in THRESH_DEBT},
                   **{f"P_borc_gt_{int(h)}": float((d > h).mean()) for h in THRESH_INFO},
                   f"P_borc_gt_{int(THR_DEBT_IMF)}_BVF": float((d > THR_DEBT_IMF).mean()),
                   f"P_borc_gt_{config.LAST_ACTUAL}_seviyyesi": float((d > _d_last(E)).mean()),
                   **{f"P_GFN_gt_{int(h)}": float((P["GFN"][:, t] > h).mean()) for h in THR_GFN},
                   "borc_xidmeti_gelir_p50": float(np.nanmedian(P["DS_rev"][:, t])),
                   "borc_xidmeti_gelir_p95": float(np.nanquantile(P["DS_rev"][:, t], 0.95)),
                   f"P_borc_xidmeti_gt_{int(THR_DS_REV)}": float((P["DS_rev"][:, t] > THR_DS_REV).mean()),
                   "FR1_borc_ÜDM": float(fr1_d[t]),
                   "GFN_p50": float(np.median(P["GFN"][:, t])), "GFN_p95": float(np.quantile(P["GFN"][:, t], 0.95)),
                   "borc_mln_azn_p50": float(np.median(P["D"][:, t])), "borc_mln_azn_p95": float(np.quantile(P["D"][:, t], 0.95))}
            Yt = E["Y"][:, t]
            for k, v in P["comp"].items():
                row[f"tohfe_{k}_pp"] = float(np.mean(v[:, t] / Yt * 100))
            d_prev0 = _d_last(E) if st.get("year_end") == YEARS[0] - 1 else P["D0"] / E["Y0"][0] * 100
            prevd = P["d"][:, t - 1] if t else np.full(len(d), d_prev0)
            row["tohfe_artim_pp"] = float(np.mean(d - prevd) - sum(row[f"tohfe_{k}_pp"] for k in P["comp"]))
            if t == 0:
                row["yoxlama_MN_bulleten_mln_azn"] = st.get("check", np.nan)
                row["yoxlama_simul_ilortasi_p50"] = float(np.nanmedian(P["mid"]))
                row["yoxlama_tarix"] = st.get("check_date", "")
                row["yoxlama_ferq_pct"] = (np.nan if st.get("anchored") else
                                           (st.get("check", np.nan) / row["yoxlama_simul_ilortasi_p50"] - 1) * 100)
                row["MN_bulleten_rolu"] = "lövbər (FR1 v2.3.4 SFA)" if st.get("anchored") else "yoxlama"
                row["qaliq_axin_duzelisi_2026_mln_azn"] = st.get("sfa", 0.0)
            rows.append(row)
    out = pd.DataFrame(rows)
    out["baslangic_qaliq_mln_azn"] = st.get("D0", np.nan)
    out["qeyd"] = (f"başlanğıc qalıq: {st.get('src', 'MN bülleteni')} = {_az(st.get('D0', np.nan))} mln AZN; "
                   f"MN bülleteni ({st.get('check_date', '')}) = {_az(st.get('check', np.nan))} — "
                   f"{'2026 lövbəri (FR1 ilə eyni qalıq-axın düzəlişi)' if st.get('anchored') else 'yalnız yoxlama'}; "
                   "30/45/60% — risk iştahı (DR10, Nazirlik qərarı); 20/25% və GFN/borc xidməti həddləri məlumat "
                   "xarakterlidir; 70% və GFN 15% — BVF MAC DSA bençmarkı; tohfe_artim_pp = nominal ÜDM artımının "
                   "(və qalıq) borc nisbətinə təsiri")
    return out


def run(ctx: dict | None = None) -> dict:
    ctx = ctx if ctx is not None else {}
    E = ctx.get("engine") or engine(ctx.get("n", config.N_SIM), ctx=ctx)
    ctx["engine"] = E
    K3 = fan_table(E)
    p = config.OUTPUT / "K3_dsa_fan.csv"
    K3.round(6).to_csv(p, index=False, lineterminator="\n")
    from .feeds_market import register_catalog
    register_catalog("K3_dsa_fan.csv", "dsa", "Stoxastik borc davamlılığı: borc/ÜDM yelpiyi 2026–2030, həddi aşma "
                     "ehtimalları, ümumi maliyyələşmə ehtiyacı, borc dinamikasının komponentləri (3 variant)",
                     list(K3.columns), "gündəlik")
    ctx["K3"] = K3
    return {"K3_dsa_fan": str(p)}


if __name__ == "__main__":
    r = run()
    k = pd.read_csv(r["K3_dsa_fan"])
    print(k[["variant", "il", "baza_FR1_MN", "FR1_borc_ÜDM", "p05", "p50", "p95", "P_borc_gt_20", "P_borc_gt_25",
             "P_borc_gt_30", "GFN_p95", "P_GFN_gt_5", "borc_xidmeti_gelir_p95"]].round(3).to_string())
    print(k[["yoxlama_MN_bulleten_mln_azn", "yoxlama_simul_ilortasi_p50", "baslangic_qaliq_mln_azn"]].dropna().iloc[:1])
