"""M1–M7 — mitigation planning and strategy (FR3 v2): quantified effect of every risk-mitigating
measure on the risk distribution (ΔES, ΔP of threshold breach, ΔVaR/ΔCaR), portfolio optimisation
under a budget and risk-appetite constraints, efficient frontier, residual risk after the plan,
implementation plan with status workflow and overdue alerts, and strategic approaches per family.

Effects are computed, not asserted, wherever an engine exists:
* MicroUnit chain (levers / exogenous overrides) sizes the policy responses (counter-cyclical
  investment, monetary reaction, fiscal rule) — `scalability.run_chain` fails loudly on ignored keys;
* RU's joint Monte Carlo (`simulate.run`) supplies the per-channel draws on which each measure acts
  (channel attenuation, state-contingent injections, hedge pay-offs, insurance layers);
* RU VaR/CaR outputs (V3/V4/K2) and `var.oil_revenue` give the exposure effects.
Expert attenuation parameters (from the register) are labelled as such; costs are documented
assumptions for the Ministry to confirm. Optimisation: scipy `milp` on the linearised individual
effects as the start, then exact re-evaluation with add/drop/swap local search (effects interact).
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd
from scipy import stats

from . import config, measures, parametrler, scalability as sc, simulate, spine

N_OPT = 20000
BUDGETS = (0, 25, 50, 100, 200, 300, 500, 750, 1000, 1500, 2000, 3000)
PLAN_BUDGETS = (100, 500, 1500)
PEG = 1.7
APPETITE_FILE = config.INPUT / "risk_istahi.csv"
APPETITE_DEFAULT = [  # key, value, unit, description — Ministry decision (DR10), placeholders until approved
    ("P_g_max", 0.20, "ehtimal", "P(qeyri-neft artımı < GaR həddi) üçün yuxarı hədd"),
    ("P_cpi_max", 0.50, "ehtimal", "P(inflyasiya > 6%) üçün yuxarı hədd"),
    ("P_fis_max", 0.40, "ehtimal", "P(büdcə balansı < −1% ÜDM) üçün yuxarı hədd"),
    ("CaR_max_mln_usd", 16500.0, "mln USD", "Fiskal kapitala risk (CaR95, 1 il) üçün yuxarı hədd"),
]


def appetite() -> dict:
    if not APPETITE_FILE.exists():
        pd.DataFrame(APPETITE_DEFAULT, columns=["acar", "deyer", "vahid", "izah"]).assign(
            menbe="FƏRZİYYƏ — risk iştahı Nazirlik qərarıdır (DR10)").to_csv(APPETITE_FILE, index=False)
    a = pd.read_csv(APPETITE_FILE)
    return dict(zip(a["acar"], a["deyer"].astype(float)))


# ---------------------------------------------------------------- engine-derived policy responses
def engine_responses() -> dict:
    """MicroUnit chain responses used to size the policy measures (score year)."""
    hy = config.score_year()
    j = sc.YEARS.index(hy)
    D = sc.factor_data()
    base, _ = sc.run_chain({}, "M-base")
    out = {"evidence": {}}

    def dd(ov, label, b=base):
        f, _ = sc.run_chain(ov, label)
        d = sc.derived_delta(b, f, D["rgdpnon_2025"])
        return {t: d[(t, hy)] for t in ("ru:nonoil_g", "ru:nonoil_lvl", "ru:cpi", "ru:budget_gdp")}

    v = [0.0] * len(sc.YEARS)
    v[j] = 1000.0 / D["p_inv"]                                  # +1 bn AZN nominal in the score year (2015 prices)
    r = dd({"FR1": {"exogenous": {"istate_add": {"values": v}}}}, "M-inv")
    out["inv"] = r
    out["evidence"]["T09"] = (f"MikroUnit zənciri: {hy}-də +1 mlrd AZN (nominal) dövlət investisiyası → qeyri-neft artımı "
                              f"{sc.az(r['ru:nonoil_g'])} f.b., İQİ {sc.az(r['ru:cpi'])} f.b., büdcə {sc.az(r['ru:budget_gdp'])}% "
                              "ÜDM; v2.4: ehtiyat 1 000 mln AZN nominal ilə məhdud — əvvəl investisiyanın kəsilməməsi "
                              "(fiscal_react_floor), qalan hissə GaR pozulan ildə inyeksiya; ehtiyatdan çəkilişlər tədbirin "
                              "xərcidir (büdcə məhdudiyyətində) və fiskal kapital itkisi kimi ikinci dəfə sayılmır")
    path = [0.0] * len(sc.YEARS)
    for t in range(j, len(path)):
        path[t] = 1.0
    r = dd({"FR1": {"exogenous": {"polrate": {"add": path}, "deprate": {"add": [0.5 * x for x in path]}}}}, "M-rate")
    out["rate"] = r
    out["evidence"]["T19"] = (f"MikroUnit zənciri: uçot dərəcəsi +1 f.b. ({hy}-dən) → İQİ {sc.az(r['ru:cpi'], 3)} f.b., "
                              f"qeyri-neft artımı {sc.az(r['ru:nonoil_g'], 3)} f.b. (FR1-də faiz kanalı zəifdir)")
    S = sc.factor_specs(D)
    lev = {"fiscal_rule": "nobd", "istate_rule": "policy_level"}
    base_r, _ = sc.run_chain({"FR1": {"levers": lev}}, "M-rule-base")
    ratio, dfis = {}, np.zeros(len(sc.YEARS))
    for k in (-1.0, 1.0):
        ov, _ = S["brent"]["build"](k)
        a = dd(ov, f"M-brent{k}")
        ov2 = {"FR1": {**ov["FR1"], "levers": lev}}
        b = dd(ov2, f"M-brent{k}-rule", base_r)
        for key, t in (("g", "ru:nonoil_lvl"), ("cpi", "ru:cpi"), ("fis", "ru:budget_gdp")):
            ratio.setdefault(key, []).append(b[t] / a[t] if abs(a[t]) > 1e-9 else 1.0)
        fa, _ = sc.run_chain(ov, f"M-brent{k}")                    # all years: additive budget delta per +1σ Brent
        fb, _ = sc.run_chain(ov2, f"M-brent{k}-rule")
        da, db = sc.derived_delta(base, fa, D["rgdpnon_2025"]), sc.derived_delta(base_r, fb, D["rgdpnon_2025"])
        dfis += np.array([(db[("ru:budget_gdp", y)] - da[("ru:budget_gdp", y)]) / k for y in sc.YEARS]) / 2
    # v2.4: g / CPI keep the response RATIO (bounded to [0; 1,5]); the budget uses the ADDITIVE delta per σ of Brent
    # (the base FR1 budget response is ≈ 0 because spending follows revenue, so a ratio of ≈ 27 blew the fiscal
    # cost up when multiplied into RU's Brent channel)
    out["rule_ratio"] = {k: float(np.clip(np.mean(v), 0.0, 1.5)) for k, v in ratio.items()}
    out["rule_dfis_per_sigma"] = dfis
    out["brent_sigma"] = float(S["brent"]["sigma"])
    rr = out["rule_ratio"]
    out["evidence"]["T28"] = (f"MikroUnit FR1 fiscal_rule=nobd + istate_rule=policy_level, Brent ±1σ: cavab nisbəti "
                              f"qeyri-neft ÜDM {sc.az(rr['g'], 2, False)}, İQİ {sc.az(rr['cpi'], 2, False)}; büdcə "
                              f"balansına əlavə təsir {sc.az(float(dfis[j]), 2)}% ÜDM / 1σ Brent ({hy}) — şok ARDNF "
                              "buferinə keçir; konsolidasiya olunmuş fiskal kapitalda yaxşı illərin qənaəti pis illərin "
                              "xərcini örtür")
    out["gdp_n"] = base[("fr1:gdp_n", hy)]
    return out


# ---------------------------------------------------------------- simulation context
def hedge_price(K: float, hy: int, sigma_hist: float) -> dict:
    """T26 put on the score-year ANNUAL-AVERAGE Brent (v2.4, audit M5): forward = latest Brent spot (flat strip —
    no free futures source; parametrler 'hedge_forward_proxy'), σ = CBOE OVX implied vol (FRED OVXCLS; historical
    Brent σ when unavailable), Asian (averaging) variance σ²·(T1 + (T2 − T1)/3) over the averaging window
    [1 Jan hy, 31 Dec hy], Black-76 with the UST 2y discount. Cost and benefit both cover ONE budget year."""
    from . import feeds_market as fm
    today = pd.Timestamp(config.as_of())
    F, sig, src_f, src_s, r = np.nan, sigma_hist, "", "tarixi Brent σ (S0)", 0.04
    try:
        d, _ = fm.load_panels()
        b = d["brent"].dropna()
        F, src_f = float(b.iloc[-1]), f"Brent spot {b.index[-1]:%Y-%m-%d} (FRED DCOILBRENTEU) — düz forvard FƏRZİYYƏSİ"
        if "ovx" in d and d["ovx"].notna().any():
            sig, src_s = float(d["ovx"].dropna().iloc[-1]) / 100, f"OVX {d['ovx'].dropna().index[-1]:%Y-%m-%d} (WTI opsionları)"
        if "ust2" in d and d["ust2"].notna().any():
            r = float(d["ust2"].dropna().iloc[-1]) / 100
    except Exception:                                              # noqa: BLE001
        pass
    if not np.isfinite(F):
        F, src_f = K / 0.9, "forvard yoxdur → baza Brent (EHTİYAT)"
    T1 = max((pd.Timestamp(f"{hy}-01-01") - today).days / 365.25, 0.0)
    T2 = max((pd.Timestamp(f"{hy}-12-31") - today).days / 365.25, 1e-3)
    v = sig ** 2 * (T1 + (T2 - max(T1, 0.0)) / 3)
    d1 = (np.log(F / K) + 0.5 * v) / np.sqrt(v)
    put = np.exp(-r * T2) * (K * stats.norm.cdf(-(d1 - np.sqrt(v))) - F * stats.norm.cdf(-d1))
    return {"put": float(put), "F": F, "sigma": sig, "sigma_asian": float(np.sqrt(v / T2)), "T1": T1, "T2": T2, "r": r,
            "p_market": float(stats.norm.cdf(-(d1 - np.sqrt(v)))), "src_f": src_f, "src_s": src_s,
            "tenor": float(parametrler.get("hedge_tenor_years", 1.0))}


def _react_beta(floor_fis: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Balance-equivalent size of the transfer-financed investment reaction per unit of log Brent deviation, per year:
    the floor run (T09) reveals f(max(−z, 0)) for x < 0; z is linear in x, so OLS through 0 on x < 0 draws."""
    beta = np.zeros(x.shape[1])
    for t in range(x.shape[1]):
        m = x[:, t] < 0
        if m.sum() > 50 and np.abs(floor_fis[m, t]).sum() > 0:
            beta[t] = float((floor_fis[m, t] * x[m, t]).sum() / (x[m, t] ** 2).sum())
    return beta


def prepare(n: int = N_OPT, seed: int = config.SEED, eng: dict | None = None) -> dict:
    """Draws for the optimiser: every channel for ALL forecast years (n×T) — the consolidated fiscal-capital metric
    (state budget + SOFAZ) is cumulated along each path 2026–2030, so savings in good years offset costs in bad ones."""
    from . import exposures, var
    hy = config.score_year()
    res = simulate.run(n=n, seed=seed)
    rfl = simulate.run(n=n, seed=seed, overrides={"fiscal_react_floor": True})
    j, T = res.col(hy), len(res.years)
    comp = {k: {c: np.asarray(a, float).copy() for c, a in d.items()}
            for k, d in (("g", res.comp_g), ("cpi", res.comp_cpi), ("fis", res.comp_fis))}
    floor = {k: np.asarray(d["fiscal_react"], float) for k, d in
             (("g", rfl.comp_g), ("cpi", rfl.comp_cpi), ("fis", rfl.comp_fis)) if "fiscal_react" in d}
    eng = eng or engine_responses()
    oil = {y: var.oil_revenue_inputs(y) for y in res.years}
    inp = oil[hy]
    dev = np.cumsum(res.events["R03"], axis=1) > 0
    vol = np.random.default_rng(seed + 7).normal(0, inp["sigma_vol"], n)
    brent = np.asarray(res.brent, float)
    R = var.oil_revenue(brent[:, j], dev[:, j], vol, inp)
    Y = spine.baseline()["fr1_gdp_n"].reindex(res.years).to_numpy(float)
    x = np.log(brent / np.asarray(res.brent_base, float)[None, :])
    beta = _react_beta(floor["fis"] - comp["fis"]["fiscal_react"], x)
    fk_oil = np.zeros((n, T))                                    # SOFAZ net oil inflow vs plan (mln AZN)
    try:
        plan = exposures.ministry_sofaz_plan()
        for t, y in enumerate(res.years):
            o = oil[y]
            tr_sh = float(np.clip(plan.at[y, "transfer_azn"] / o["R0"], 0, 1))
            fk_oil[:, t] = (plan.at[y, "sofaz_rev_azn"] * (brent[:, t] / plan.at[y, "brent"] - 1)
                            - tr_sh * o["k"] * (brent[:, t] + o.get("spread", 0.0) - o["B0"]))
    except Exception:                                            # noqa: BLE001 — Ministry plan unavailable
        plan = None
    prm = sc.factor_data()["prm"]
    v3 = pd.read_csv(config.OUTPUT / "V3_var_es.csv")
    v3 = v3[(v3["portfel"] == "sofaz") & (v3["horizont"] == "1il") & (v3["metod"] == "mc_tcop") & (v3["etibarlilik"] == 0.95)]
    v4 = pd.read_csv(config.OUTPUT / "V4_var_contributions.csv")
    v4 = v4[(v4["portfel"] == "sofaz") & (v4["horizont"] == "1il") & (v4["etibarlilik"] == 0.95) & (v4["qrup"] == "amil")]
    k2 = pd.read_csv(config.OUTPUT / "K2_car_distribution.csv")
    k2 = k2[(k2["il"] == hy) & k2["variant"].str.contains("xaric")]
    s = float(sc.factor_specs()["brent"]["sigma"])
    B0 = float(res.brent_base[j])
    K = float(parametrler.get("hedge_strike_ratio", 0.9)) * B0
    H = hedge_price(K, hy, s)
    C = {"n": n, "T": T, "j": j, "hy": hy, "years": list(res.years), "comp": comp, "floor": floor,
            "base": {k: np.asarray(res.base[k], float) for k in ("g", "cpi", "fis")},
            "brent": brent, "brent_base": B0, "brent_base_t": np.asarray(res.brent_base, float),
            "brent_q25": np.quantile(brent, 0.25, axis=0), "strike": K, "bs_put": H["put"], "hedge": H,
            "oil": inp, "R": R, "Y": Y, "gdp_n": float(eng["gdp_n"]), "eng": eng, "x": x, "react_beta": beta,
            "fk_oil": fk_oil, "plan_ok": plan is not None,
            "thr": {"g": float(prm["nonoil_gar_threshold"]), "cpi": float(prm["cpi_threshold"]),
                    "fis": float(prm["fiscal_threshold"])},
            "var95": float(v3["VaR_mln_usd"].iloc[0]) if len(v3) else np.nan,
            "var_contrib": dict(zip(v4["komponent"], v4["tohfe_VaR"])),
            "car95": float(k2["CaR95_mln_usd"].iloc[0]) if len(k2) else np.nan,
            "events": {k: np.asarray(v[:, j]) for k, v in res.events.items()},
            "channel_risk": dict(simulate.CHANNEL_RISK)}
    C["fk_hy_var0"] = evaluate(C, None, {})["_fk_hy_var"]
    return C


# ---------------------------------------------------------------- applying measures to the draws
def _es_low(x, q=0.10):
    k = max(1, int(len(x) * q))
    return float(np.partition(x, k - 1)[:k].mean())


def _es_high(x, q=0.10):
    return -_es_low(-x, q)


def _var(x, q=0.05):
    return float(x.mean() - np.quantile(x, q))


def evaluate(C: dict, M: pd.DataFrame, sel: dict) -> dict:
    """sel = {tedbir_id: strength 0..1} (1 = fully implemented). Returns risk metrics.

    Arrays are n×T (all forecast years); g / CPI / budget metrics are read in the score year j. The consolidated
    fiscal-capital flow FK_t (mln AZN, deviation from the plan) = Δ state budget balance + SOFAZ net oil inflow
    (Ministry 'base 60' SOFAZ revenue ∝ Brent minus the transfer part of the FR1 budget oil revenue) − the
    transfer-financed procyclical investment reaction (+ in bad years when it is cut, − in good years) + reserve
    draws already charged as the measure's cost (T09). ES10_FK uses the path sum 2026–2030 (v2.4, audit M4)."""
    j, T, n = C["j"], C["T"], C["n"]
    comp = {k: {c: a.copy() for c, a in d.items()} for k, d in C["comp"].items()}
    add = {k: np.zeros((n, T)) for k in ("g", "cpi", "fis")}
    react = np.ones((n, T))                       # multiplier on the transfer-financed investment reaction
    addback = np.zeros((n, T))                    # pre-funded reserve draws (mln AZN)
    later, dvar, R = [], 0.0, C["R"].copy()
    Y = C["Y"][None, :]
    for tid, w in sel.items():
        if w <= 0:
            continue
        r = M.loc[tid]
        mdl, chs, a = r["effekt_modeli"], [c for c in str(r["effekt_kanal"]).split(";") if c], float(r["effekt_guc"])
        if mdl == "scale":
            for k in comp:
                for c in chs:
                    if c in comp[k]:
                        comp[k][c] *= 1 - a * w
            if "fiscal_react" in chs:
                react *= 1 - a * w
        elif mdl == "fiscal_rule":
            rr = C["eng"]["rule_ratio"]
            for k in ("g", "cpi"):
                for c in chs:
                    if c in comp[k]:
                        comp[k][c] *= 1 - w * (1 - rr[k])
            dfis = np.asarray(C["eng"].get("rule_dfis_per_sigma", np.zeros(T)), float)[:T]
            add["fis"] += w * dfis[None, :] * C["x"] / C["eng"].get("brent_sigma", 0.3)
            if "fiscal_react" in chs:
                react *= 1 - w * (1 - rr["g"])
        elif mdl == "react_cushion":
            mask = (C["brent"] >= C["brent_q25"][None, :]) & (C["brent"] < C["brent_base_t"][None, :])
            for k in comp:
                if "fiscal_react" in comp[k]:
                    comp[k]["fiscal_react"][mask] *= 1 - w
            # FK: the cut avoided in moderately bad years is financed by the precautionary margin of the conservative
            # budget oil price saved in normal/good years (mean-neutral over the cycle) → no consolidated FK effect
        elif mdl == "floor_inject":                # reserve of a mln AZN (nominal): no-cut floor first, then injection
            rem = np.full(n, a * w)
            for t in range(T):
                d = {k: C["floor"][k][:, t] - C["comp"][k]["fiscal_react"][:, t] for k in C["floor"]}
                cost = np.maximum(0.0, -d["fis"] * C["Y"][t] / 100)
                sc_ = np.where(cost > 0, np.minimum(1.0, rem / np.where(cost > 0, cost, 1.0)), 1.0)
                for k in d:
                    comp[k]["fiscal_react"][:, t] += sc_ * d[k]
                rem -= sc_ * cost
                addback[:, t] += sc_ * cost
            later.append(("inject", rem, a * w))
        elif mdl == "rate_response":
            later.append(("rate", w, a))
        elif mdl == "cat_cover":
            loss = -comp["fis"].get("quake", np.zeros((n, T)))
            cover = a / C["Y"][None, :] * 100
            add["fis"] += w * (np.minimum(cover, np.maximum(0.0, loss - 0.3)) - 0.03 * cover)
        elif mdl == "reserve_layer":
            loss = -sum(comp["fis"].get(c, 0.0) for c in chs)
            add["fis"] += w * np.minimum(np.maximum(loss, 0.0), a / C["Y"][None, :] * 100)
        elif mdl == "put_hedge":                   # one budget year (score year): premium and pay-off on the same tenor
            k_usd = C["oil"]["k"]
            pay = a * k_usd * np.maximum(0.0, C["strike"] - C["brent"][:, j])
            prem = a * k_usd * C["bs_put"]
            add["fis"][:, j] += w * (pay - prem) / C["Y"][j] * 100
            R = R + w * (pay - prem)
        elif mdl == "var_rebalance":
            dvar -= w * a * sum(C["var_contrib"].get(c, 0.0) for c in chs)
    tot = {k: C["base"][k][None, :] + sum(comp[k].values()) + add[k] for k in comp}
    for kind, p1, p2 in later:
        if kind == "inject":
            e, rem, cap = C["eng"]["inv"], p1.copy(), p2
            for t in range(T):
                hit = (tot["g"][:, t] < C["thr"]["g"]) & (rem > 1e-9)
                inj = np.where(hit, np.minimum(rem, cap), 0.0)
                tot["g"][:, t] += inj / 1000 * e["ru:nonoil_g"]
                tot["cpi"][:, t] += inj / 1000 * e["ru:cpi"]
                tot["fis"][:, t] += inj / 1000 * e["ru:budget_gdp"]
                rem -= inj
                addback[:, t] += inj
        else:
            e = C["eng"]["rate"]
            hit = tot["cpi"] > C["thr"]["cpi"]
            tot["cpi"] = tot["cpi"] + hit * p1 * p2 * e["ru:cpi"]
            tot["g"] = tot["g"] + hit * p1 * p2 * e["ru:nonoil_g"]
            tot["fis"] = tot["fis"] + hit * p1 * p2 * e["ru:budget_gdp"]
    fk = ((tot["fis"] - C["base"]["fis"][None, :]) * Y / 100 + C["fk_oil"]
          - C["react_beta"][None, :] * C["x"] * react * Y / 100 + addback)
    fk_cum = fk.sum(axis=1) / C["Y"][j] * 100                  # % of score-year GDP
    fk_hy = fk[:, :j + 1].sum(axis=1)                            # mln AZN, to the score year (K2 horizon)
    g, c, f = tot["g"][:, j], tot["cpi"][:, j], tot["fis"][:, j]
    R0 = C["oil"]["R0"]
    oar = R0 - float(np.quantile(R, 0.05))
    out = {"ES10_g": _es_low(g), "VaR05_g": float(np.quantile(g, 0.05)), "P_g": float((g < C["thr"]["g"]).mean()),
           "ES10_cpi": _es_high(c), "P_cpi": float((c > C["thr"]["cpi"]).mean()),
           "ES10_fis": _es_low(f), "VaR05_fis": float(np.quantile(f, 0.05)), "P_fis": float((f < C["thr"]["fis"]).mean()),
           "ES10_FK": _es_low(fk_cum), "E_FK": float(fk_cum.mean()), "VaR95_FK": _var(fk_cum),
           "ORaR95": oar, "VaR95_ARDNF": C["var95"] + dvar, "_fk_hy_var": _var(fk_hy)}
    # CaR95 (K2, score year) + ΔVaR of the SOFAZ portfolio + Δ95% VaR of the consolidated fiscal-capital flow
    out["CaR95"] = C["car95"] + dvar + (out["_fk_hy_var"] - C.get("fk_hy_var0", out["_fk_hy_var"])) / PEG
    out["CaR95_bazar"] = C["car95"] + dvar          # market part only (objective; the FK part is in the fiscal term)
    out["_tot"], out["_comp"], out["_fk"] = {k: v[:, j] for k, v in tot.items()}, \
        {k: {ch: v[:, j] for ch, v in d.items()} for k, d in comp.items()}, fk_cum
    return out


METRICS_AZ = {
    "ES10_g": ("Gözlənilən itki (ES10): qeyri-neft artımı", "%", +1),
    "VaR05_g": ("Riskə məruz dəyər (5%): qeyri-neft artımı", "%", +1),
    "P_g": ("P(qeyri-neft artımı < GaR həddi)", "ehtimal", -1),
    "ES10_cpi": ("Gözlənilən itki (ES10, yuxarı quyruq): inflyasiya", "%", -1),
    "P_cpi": ("P(inflyasiya > 6%)", "ehtimal", -1),
    "ES10_fis": ("Gözlənilən itki (ES10): dövlət büdcəsinin balansı (yalnız məlumat)", "% ÜDM", +1),
    "VaR05_fis": ("Riskə məruz dəyər (5%): büdcə balansı", "% ÜDM", +1),
    "P_fis": ("P(büdcə balansı < −1% ÜDM)", "ehtimal", -1),
    "ES10_FK": ("Gözlənilən itki (ES10): konsolidasiya olunmuş fiskal kapital axını (büdcə + ARDNF), 2026–2030 cəmi",
                "% ÜDM", +1),
    "E_FK": ("Konsolidasiya olunmuş fiskal kapital axınının ortası (yaxşı və pis illər simmetrik)", "% ÜDM", +1),
    "VaR95_FK": ("Konsolidasiya olunmuş fiskal kapital axınının VaR-ı (95%, orta − p05)", "% ÜDM", -1),
    "ORaR95": ("Büdcənin neft gəlirlərinə risk (95%)", "mln AZN", -1),
    "VaR95_ARDNF": ("ARDNF portfelinin VaR-ı (95%, 1 il)", "mln USD", -1),
    "CaR95": ("Fiskal kapitala risk (CaR95, 1 il; K2 + ARDNF VaR və konsolidasiya olunmuş fiskal axının VaR dəyişməsi)",
              "mln USD", -1),
    "CaR95_bazar": ("Fiskal kapitala risk — yalnız bazar hissəsi (məqsəd funksiyası üçün; fiskal axın ayrıca)", "mln USD", -1),
}


def weights() -> dict:
    s = pd.read_csv(config.OUTPUT / "FR2_risk_scores.csv").set_index("risk_id")["skor"]
    get = lambda r, d: float(s.get(r, d))  # noqa: E731
    return {"g": get("R13", 10), "cpi": get("R12", 10), "fis": get("R11", 10), "car": get("R01", 10)}


FK_TAIL_WEIGHT = parametrler.get("obj_fk_tail_weight", 0.5)


def fk_ce(m: dict, lam: float) -> float:
    """Certainty equivalent of the consolidated fiscal-capital flow: E − λ·(E − ES10); λ = 0 treats good and bad
    states symmetrically (mean), λ = 1 is the pure tail (ES10). λ is a Ministry risk-appetite choice."""
    return m["E_FK"] - lam * (m["E_FK"] - m["ES10_FK"])


def objective(m: dict, m0: dict, W: dict, C: dict, lam: float | None = None) -> float:
    """Priority-weighted share of the baseline tail gap removed (ES vs baseline; CaR relative). v2.4 (audit M4):
    the fiscal term is the CONSOLIDATED fiscal capital (state budget + SOFAZ, path sum 2026–2030), not the state
    budget alone — a measure that moves an oil shock from the budget to SOFAZ, or saves in good years what it
    spends in bad ones, is no longer penalised as if the money were lost."""
    j = C.get("j", 0)
    bg, bc = np.atleast_1d(C["base"]["g"])[min(j, np.size(C["base"]["g"]) - 1)], \
        np.atleast_1d(C["base"]["cpi"])[min(j, np.size(C["base"]["cpi"]) - 1)]
    gap_g = max(bg - m0["ES10_g"], 1e-6)
    gap_c = max(m0["ES10_cpi"] - bc, 1e-6)
    lam = FK_TAIL_WEIGHT if lam is None else lam
    gap_f = max(m0["E_FK"] - m0["ES10_FK"], 1e-6)
    k0 = m0.get("CaR95_bazar", m0["CaR95"])
    red = {"g": (m["ES10_g"] - m0["ES10_g"]) / gap_g, "cpi": (m0["ES10_cpi"] - m["ES10_cpi"]) / gap_c,
           "fis": (fk_ce(m, lam) - fk_ce(m0, lam)) / gap_f,
           "car": (k0 - m.get("CaR95_bazar", m["CaR95"])) / k0 if np.isfinite(k0) and k0 else 0.0}
    return float(sum(W[k] * red[k] for k in W) / sum(W.values()) * 100)


def appetite_ok(m: dict, A: dict) -> dict:
    return {"P_g": m["P_g"] <= A["P_g_max"], "P_cpi": m["P_cpi"] <= A["P_cpi_max"],
            "P_fis": m["P_fis"] <= A["P_fis_max"], "CaR95": m["CaR95"] <= A["CaR_max_mln_usd"]}


# ---------------------------------------------------------------- measures table, individual effects
def measure_table(C: dict) -> pd.DataFrame:
    M = measures.load_v2().set_index("tedbir_id")
    M["xerc_mln_azn"] = pd.to_numeric(M["xerc_mln_azn"], errors="coerce").fillna(0.0)
    M["effekt_guc"] = pd.to_numeric(M["effekt_guc"], errors="coerce").fillna(0.0)
    hedge = M["effekt_modeli"] == "put_hedge"
    if hedge.any():                                     # premium × hedge share × ONE budget year (same tenor as the pay-off)
        H = C["hedge"]
        prem = M.loc[hedge, "effekt_guc"] * C["oil"]["k"] * C["bs_put"] * H["tenor"]
        M.loc[hedge, "xerc_mln_azn"] = prem.round(1)
        act = float(np.maximum(0.0, C["strike"] - C["brent"][:, C["j"]]).mean())
        txt = (f"model: Asiya (illik orta) put, Blek-76: forvard {H['F']:.1f} ({H['src_f']}), σ {H['sigma']:.2f} "
               f"({H['src_s']}) → orta üzrə σ {H['sigma_asian']:.2f}, K = 0,9×baza {C['brent_base']:.1f} = {C['strike']:.1f}; "
               f"mükafat {C['bs_put']:.2f} USD/barel × hedc payı × {C['oil']['k']:.0f} mln AZN/USD × {H['tenor']:.0f} il "
               f"(fayda da {C['hy']}-ci il üzrə); bazar P(Brent < K) = {H['p_market']:.2f}, RU baza baxışında "
               f"ödənişin ortası {act:.2f} USD/barel — fərq baza fərziyyəsi ilə bazar arasındakı uyğunsuzluqdur")
        M.loc[hedge, "xerc_esasi"] = [txt.replace(".", ",")] * int(hedge.sum())
    return M


def individual_effects(C, M, m0, W) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, summ = [], []
    ev = C["eng"]["evidence"]
    for tid, r in M.iterrows():
        m = evaluate(C, M, {tid: 1.0}) if r["effekt_modeli"] != "none" else m0
        ob = objective(m, m0, W, C)
        for key, (az, unit, good) in METRICS_AZ.items():
            rows.append({"tedbir_id": tid, "tedbir": r["tedbir"], "metrika": key, "metrika_ad": az, "vahid": unit,
                         "baza": m0[key], "tedbirle": m[key], "delta": m[key] - m0[key],
                         "yaxsilasma": (m[key] - m0[key]) * good,
                         "metod": r["effekt_modeli"], "esas": ev.get(tid, r["effekt_esasi"])})
        summ.append({"tedbir_id": tid, "effekt_hedef_funksiya": ob,
                     "effekt_hedef_simmetrik": objective(m, m0, W, C, 0.0),
                     "effekt_hedef_quyruq": objective(m, m0, W, C, 1.0),
                     **{f"d_{k}": m[k] - m0[k] for k in METRICS_AZ},
                     "xerc_effektivliyi_100mln": ob / r["xerc_mln_azn"] * 100 if r["xerc_mln_azn"] > 0 else np.nan,
                     "kemiyyet_metodu": ("model (mühərrik)" if r["effekt_modeli"] in
                                         ("floor_inject", "rate_response", "fiscal_rule", "put_hedge", "var_rebalance",
                                          "cat_cover", "reserve_layer", "react_cushion")
                                         else "ekspert parametri × RU ötürmə" if r["effekt_modeli"] == "scale"
                                         else "kəmiyyətlənmir (imkanlandırıcı/izləmə)"),
                     "effekt_sübutu": ev.get(tid, r["effekt_esasi"])})
    return pd.DataFrame(rows), pd.DataFrame(summ)


# ---------------------------------------------------------------- portfolio optimisation
def score(C, M, sel, m0, W, A, need_app):
    """(objective − appetite penalty, metrics, appetite flags) of the portfolio `sel` (all at full strength)."""
    m = evaluate(C, M, {t: 1.0 for t in sel})
    ok = appetite_ok(m, A)
    pen = 0.0 if not need_app else 100.0 * sum(not v for v in ok.values())
    return objective(m, m0, W, C) - pen, m, ok


_score = score                                                       # backward-compatible alias (api/analysis_opt.py)


def optimise(C, M, E, m0, W, A, budget, cand, fixed=(), excluded=()) -> dict:
    """Max objective s.t. Σ cost ≤ budget (and risk appetite when feasible).

    fixed    — measures forced into the portfolio (their cost counts against the budget; never dropped);
    excluded — measures never selected. Returns sel (incl. fixed), obj, m, ok, cost (incl. fixed), fixed,
    appetite_feasible, milp_start and budget_ok (False when the fixed measures alone exceed the budget)."""
    from scipy.optimize import Bounds, LinearConstraint, milp
    fixed = [t for t in dict.fromkeys(fixed) if t in M.index]
    fx = set(fixed)
    cand = [t for t in cand if t not in fx and t not in set(excluded)]
    cost_of = lambda s: float(sum(M.at[t, "xerc_mln_azn"] for t in s))  # noqa: E731
    free = budget - cost_of(fx)
    budget_ok = free >= -1e-9
    free = max(free, 0.0)
    cost = M.loc[cand, "xerc_mln_azn"].to_numpy(float)
    gain = E.set_index("tedbir_id").loc[cand, "effekt_hedef_funksiya"].to_numpy(float)
    x0 = np.zeros(len(cand))
    if len(cand):
        r = milp(c=-gain, constraints=[LinearConstraint(cost[None, :], -np.inf, free)],
                 integrality=np.ones(len(cand)), bounds=Bounds(0, 1))
        if r.success:
            x0 = np.round(r.x)
    sel = {cand[i] for i in range(len(cand)) if x0[i] > 0.5 and gain[i] > 0}
    full_ok = all(appetite_ok(evaluate(C, M, {t: 1.0 for t in list(cand) + fixed
                                              if M.at[t, "xerc_mln_azn"] <= free or t in fx}), A).values())
    need_app = full_ok
    best, bm, bok = score(C, M, sel | fx, m0, W, A, need_app)
    for _ in range(60):                                              # add / drop / swap local search (exact)
        improved = False
        moves = [sel | {t} for t in cand if t not in sel] + [sel - {t} for t in sel] + \
                [(sel - {a}) | {b} for a in sel for b in cand if b not in sel]
        for s_ in moves:
            if cost_of(s_) > free + 1e-9:
                continue
            v, m, ok = score(C, M, s_ | fx, m0, W, A, need_app)
            if v > best + 1e-6:
                best, bm, bok, sel, improved = v, m, ok, s_, True
        if not improved:
            break
    return {"sel": sorted(sel | fx), "obj": objective(bm, m0, W, C), "m": bm, "ok": bok, "cost": cost_of(sel | fx),
            "fixed": sorted(fx), "budget_ok": budget_ok, "appetite_feasible": need_app,
            "milp_start": sorted(cand[i] for i in range(len(cand)) if x0[i] > 0.5)}


def portfolios(C, M, E, m0, W, A):
    cand = [t for t in M.index if M.at[t, "effekt_modeli"] != "none" and M.at[t, "status"] != "dayandırılıb"]
    base_pkg = [t for t in M.index if M.at[t, "effekt_modeli"] == "none"      # enablers / monitoring (≤ 1 mln) — always
                and M.at[t, "xerc_mln_azn"] <= 1.0]
    base_cost = float(M.loc[base_pkg, "xerc_mln_azn"].sum())
    fr, plans = [], {}
    for B in sorted(set(BUDGETS) | set(PLAN_BUDGETS)):
        o = optimise(C, M, E, m0, W, A, max(B - base_cost, 0.0), cand)
        plans[B] = o
        fr.append({"budce_mln_azn": B, "secilmis_xerc_mln_azn": o["cost"] + base_cost, "hedef_funksiya": o["obj"],
                   "secilmis_tedbirler": ";".join(o["sel"]), "tedbir_sayi": len(o["sel"]),
                   **{f"qaliq_{k}": o["m"][k] for k in METRICS_AZ},
                   **{f"istah_{k}": v for k, v in o["ok"].items()},
                   "istah_mumkun": o["appetite_feasible"], "milp_baslangic": ";".join(o["milp_start"])})
    F = pd.DataFrame(fr)
    F["semereli_serhed"] = F["hedef_funksiya"].cummax() == F["hedef_funksiya"]
    rows = []
    for B in PLAN_BUDGETS:
        o = plans[B]
        full = o["obj"]
        for t in o["sel"] + base_pkg:
            rest = [x for x in o["sel"] if x != t]
            marg = full - objective(evaluate(C, M, {x: 1.0 for x in rest}), m0, W, C) if t in o["sel"] else 0.0
            rows.append({"budce_mln_azn": B, "tedbir_id": t, "tedbir": M.at[t, "tedbir"], "strategiya_v2": M.at[t, "strategiya_v2"],
                         "mesul": M.at[t, "mesul"], "xerc_mln_azn": M.at[t, "xerc_mln_azn"],
                         "rol": "optimal seçim" if t in o["sel"] else "imkanlandırıcı minimum paket",
                         "marginal_tohfe": marg, "portfel_hedef_funksiya": full, "portfel_xerc": o["cost"] + base_cost,
                         "istah_odenilir": all(o["ok"].values())})
    return F, pd.DataFrame(rows), plans, base_pkg


def residual(C, M, m0, plan_sel, base_pkg) -> pd.DataFrame:
    """Residual risk after the plan: per risk, its channels' lower-tail (Euler) contribution before,
    at current status (status-weighted), and after full implementation; overall metrics rows."""
    from . import factors
    from .scoring import band, scales
    scs = scales(factors.params())
    cur = {t: float(M.at[t, "status_w"]) for t in M.index}
    runs = {"baza": m0, "cari": evaluate(C, M, cur), "plan": evaluate(C, M, {t: 1.0 for t in plan_sel})}
    S = pd.read_csv(config.OUTPUT / "FR2_risk_scores.csv").set_index("risk_id")
    rows = []
    tails = {}
    for lab, m in runs.items():
        tot = m["_tot"]
        for k, side in (("g", -1), ("cpi", +1), ("fis", -1)):
            q = np.quantile(tot[k], 0.10 if side < 0 else 0.90)
            mask = tot[k] <= q if side < 0 else tot[k] >= q
            tails[(lab, k)] = {c: float(a[mask].mean()) for c, a in m["_comp"][k].items()}
    for rid, r in S.iterrows():
        chans = [c for c, x in C["channel_risk"].items() if x == rid]
        rec = {"risk_id": rid, "ad": r["ad"], "kanallar": ";".join(chans), "FR2_skor": r["skor"],
               "ehtimal": r["ehtimal"]}
        ratio = {}
        for k in ("g", "cpi", "fis"):
            b = sum(tails[("baza", k)].get(c, 0.0) for c in chans)
            for lab in ("baza", "cari", "plan"):
                rec[f"quyruq_{k}_{lab}"] = sum(tails[(lab, k)].get(c, 0.0) for c in chans)
            ratio[k] = rec[f"quyruq_{k}_plan"] / b if abs(b) > 1e-6 else 1.0
        ib = max(band(max(r["tesir_g"], 0) * ratio["g"], scs["g"]), band(max(r["tesir_cpi"], 0) * ratio["cpi"], scs["cpi"]),
                 band(max(r["tesir_fis"], 0) * ratio["fis"], scs["fis"]))
        rec["qaliq_skor_plan"] = band(r["ehtimal"], scs["p"]) * ib
        rec["qaliq_prioritet"] = "yüksək" if rec["qaliq_skor_plan"] >= 12 else "orta" if rec["qaliq_skor_plan"] >= 6 else "aşağı"
        links = M[M["risk_idler"].str.contains(rid)].index
        rec["plandaki_tedbirler"] = ";".join(t for t in links if t in plan_sel or t in base_pkg)
        rows.append(rec)
    for key, (az, unit, _) in METRICS_AZ.items():
        rows.append({"risk_id": "ÜMUMİ", "ad": az, "kanallar": unit, **{f"metrika_{lab}": m[key] for lab, m in runs.items()}})
    return pd.DataFrame(rows)


PHASES = (("hazırlıq", 0.0, 0.25), ("təsdiq", 0.25, 0.35), ("icra", 0.35, 0.9), ("KPI qiymətləndirməsi", 0.9, 1.0))


def implementation_plan(M, plan_sel) -> pd.DataFrame:
    today = pd.Timestamp(config.as_of())
    rows = []
    for t, r in M.iterrows():
        s, e = pd.Timestamp(r["baslama"]), pd.Timestamp(r["muddet"])
        if e <= s:
            e = s + pd.DateOffset(months=max(int(r.get("hazirliq_ay", 1) or 1), 1))
        span = (e - s).days
        overdue = bool(r["gecikir"])
        days_left = (pd.Timestamp(r["muddet"]) - today).days
        alert = ("GECİKİR: müddət keçib, status «" + r["status_az"] + "»" if overdue else
                 f"xəbərdarlıq: {days_left} gün qalıb, hələ «{r['status_az']}»" if 0 <= days_left <= 30 and r["merhele_no"] < 3
                 else "")
        for ph, a, b in PHASES:
            rows.append({"tedbir_id": t, "tedbir": r["tedbir"], "mesul": r["mesul"], "strategiya_v2": r["strategiya_v2"],
                         "plan": "optimal plan" if t in plan_sel else "reyestr", "merhele": ph,
                         "baslama": (s + pd.Timedelta(days=int(a * span))).date().isoformat(),
                         "bitme": (s + pd.Timedelta(days=int(b * span))).date().isoformat(),
                         "status": r["status_az"], "is_axini_addimi": f"{r['merhele_no']}/4", "novbeti_addim": r["novbeti_addim"],
                         "kpi": r["kpi"], "kpi_hedd": r["kpi_hedd"], "hazirliq_ay": r["hazirliq_ay"],
                         "xerc_mln_azn": r["xerc_mln_azn"], "gecikir": overdue, "qalan_gun": days_left, "xeberdarliq": alert})
    return pd.DataFrame(rows)


FAMILY = {
    "MAL": ("Maliyyə və əmtəə bazarları", "azaltma + ötürmə",
            "Neft gəlirinin büdcəyə ötürülməsini struktur fiskal qayda (T28) və konservativ büdcə qiyməti (T01) ilə "
            "azaltmaq; quyruq itkisinin bir hissəsini opsion hedcinqi ilə bazara ötürmək (T26); ARDNF valyuta "
            "uyğunsuzluğunu balanslaşdırmaq (T27); bank buferləri (T04). Qəbul edilən qalıq ARDNF buferi ilə örtülür."),
    "XSI": ("Xarici iqtisadi və siyasi mühit", "azaltma",
            "Tərəfdaş və bazar konsentrasiyasını şaxələndirmə ilə azaltmaq (T08, T10, T12); idxal və ərzaq qiymət "
            "şoklarının daxili qiymətlərə ötürülməsini ehtiyat və rüsum çevikliyi ilə zəiflətmək (T24, T25); "
            "geosiyasi indekslərin gündəlik izlənməsi (T11) — qaçınmaq mümkün olmayan xarici risklər."),
    "TEB": ("Təbii fəlakətlər", "ötürmə + qəbul (maliyyələşdirilmiş)",
            "Laylı maliyyələşdirmə: ilk zərər qatı büdcə ehtiyat fondundan (T29, qəbul), orta qat parametrik "
            "sığorta/fəlakət istiqrazı ilə ötürülür (T13), kənd təsərrüfatı itkiləri aqrar sığortaya (T16); "
            "fiziki həssaslığın azaldılması — suvarma (T15). Məlumat sorğuları (T14, T17) kalibrləmə üçün şərtdir."),
    "DAX": ("Daxili makroiqtisadi nəticələr", "azaltma",
            "Nəticə riskləri (büdcə, inflyasiya, GaR) amillərin idarə olunması ilə azalır: kontrtsiklik investisiya "
            "ehtiyatı (T09), monetar reaksiya (T19 — FR1-də zəif kanal), fiskal lövbərin stress yoxlaması (T18); "
            "model riski bölmələrarası konsensusla idarə olunur (T30)."),
    "SEK": ("Sektor və bazar strukturu", "azaltma",
            "Erkən xəbərdarlıq siyahısındakı sahələr üçün hədəfli diaqnostika (T22) və rəqabət təhlili (T23); "
            "makro təsir kiçikdir — əsasən izləmə və hədəfli tədbir."),
}


def strategy(M, R5, E, plan_sel) -> pd.DataFrame:
    reg = pd.read_csv(config.INPUT / "risk_reyestri.csv", dtype=str)
    rows = []
    e = E.set_index("tedbir_id")
    for fam, (ad, approach, text) in FAMILY.items():
        rids = reg[reg["aile"] == fam]["risk_id"].tolist()
        tids = [t for t in M.index if any(r in str(M.at[t, "risk_idler"]).split(";") for r in rids)]
        rr = R5[R5["risk_id"].isin(rids)]
        mix = M.loc[tids, "strategiya_v2"].value_counts().to_dict() if tids else {}
        rows.append({"aile": fam, "aile_ad": ad, "riskler": ";".join(rids), "esas_yanasma": approach,
                     "strategiya_qarisigi": "; ".join(f"{k}: {v}" for k, v in mix.items()),
                     "tedbirler": ";".join(tids), "plandaki_tedbirler": ";".join(t for t in tids if t in plan_sel),
                     "xerc_plan_mln_azn": float(M.loc[[t for t in tids if t in plan_sel], "xerc_mln_azn"].sum()),
                     "hedef_funksiya_tohfesi": float(e.loc[[t for t in tids if t in plan_sel], "effekt_hedef_funksiya"].sum()),
                     "yuksek_qaliq_risk": ";".join(rr[rr["qaliq_prioritet"] == "yüksək"]["risk_id"]),
                     "strateji_izah": text})
    return pd.DataFrame(rows)


CATALOG = {
    "M1_measures_v2.csv": "Tədbirlər reyestri v2: strategiya növü (qaçınma/ötürmə/azaltma/qəbul), məsul, xərc (mln AZN, əsaslandırma), hazırlıq müddəti, status, KPI, kəmiyyətləndirilmiş effekt və xərc-effektivlik",
    "M2_measure_effects.csv": "Hər tədbirin risk paylanmasına təsiri: ES10, VaR, hədd pozulma ehtimalı, neft gəlirinə risk, ARDNF VaR, CaR — baza vs tədbirlə, metod və mühərrik sübutu",
    "M3_portfolio.csv": "Optimal tədbir portfeli (büdcə 100/500/1 500 mln AZN): seçilmiş tədbirlər, marginal töhfə, risk iştahının ödənilməsi",
    "M4_frontier.csv": "Səmərəli sərhəd: büdcə → maksimal risk azalması (prioritet çəkili ES/CaR) və qalıq metrikalar",
    "M5_residual_v2.csv": "Plandan sonra qalıq risk: risk üzrə kanal quyruq töhfələri (baza / cari status / plan), qalıq skor və ümumi metrikalar",
    "M6_implementation_plan.csv": "İcra planı (Qant): mərhələlər, məsul qurumlar, status iş axını (təklif → təsdiq → icrada → tamamlandı), KPI həddləri, gecikmə xəbərdarlıqları",
    "M7_strategy.csv": "Risk ailələri üzrə strateji yanaşmalar (Azərbaycan dilində xülasə), plandakı tədbirlər və qalıq yüksək risklər",
}


def run(ctx: dict | None = None) -> dict:
    """Stage M (mitigation/strategy). ctx: n (draws), no_write."""
    ctx = ctx if ctx is not None else {}
    t0 = time.time()
    A = appetite()
    C = prepare(n=int(ctx.get("n", N_OPT)))
    M = measure_table(C)
    W = weights()
    m0 = evaluate(C, M, {})
    M2, E = individual_effects(C, M, m0, W)
    F, P3, plans, base_pkg = portfolios(C, M, E, m0, W, A)
    mid = plans[PLAN_BUDGETS[1]]["sel"]
    R5 = residual(C, M, m0, mid, base_pkg)
    M6 = implementation_plan(M, set(mid) | set(base_pkg))
    M7 = strategy(M, R5, E, set(mid) | set(base_pkg))
    M1 = M.reset_index().merge(E, on="tedbir_id", how="left")
    M1["optimal_planda_500"] = M1["tedbir_id"].isin(set(mid) | set(base_pkg))
    keep = ["tedbir_id", "risk_idler", "tedbir", "strategiya", "strategiya_v2", "alet_novu", "mesul", "baslama", "muddet",
            "status", "status_az", "merhele_no", "novbeti_addim", "gecikir", "xerc_mln_azn", "xerc_esasi", "hazirliq_ay",
            "kpi", "kpi_hedd", "effekt_modeli", "effekt_kanal", "effekt_guc", "effekt_esasi", "kemiyyet_metodu",
            "effekt_hedef_funksiya", "xerc_effektivliyi_100mln"] + [f"d_{k}" for k in METRICS_AZ] + \
           ["effekt_hedef_simmetrik", "effekt_hedef_quyruq"] + \
           ["effekt_sübutu", "optimal_planda_500", "effekt_ehtimal_pct", "effekt_tesir_pct"]
    M1 = M1[keep]
    out = {"M1_measures_v2.csv": M1, "M2_measure_effects.csv": M2, "M3_portfolio.csv": P3, "M4_frontier.csv": F,
           "M5_residual_v2.csv": R5, "M6_implementation_plan.csv": M6, "M7_strategy.csv": M7}
    if not ctx.get("no_write"):
        for name, df in out.items():
            df.to_csv(config.OUTPUT / name, index=False, float_format="%.6g")
            spine.register_output(name, "riskunit.optimize", CATALOG[name], list(df.columns),
                                  "gündəlik (status/gecikmə); tədbir reyestri və ya risk paylanması dəyişəndə tam")
    return {**{k.split(".")[0]: v for k, v in out.items()}, "base_metrics": {k: m0[k] for k in METRICS_AZ},
            "weights": W, "appetite": A, "plans": {B: {k: plans[B][k] for k in ("sel", "obj", "cost")} for B in PLAN_BUDGETS},
            "seconds": round(time.time() - t0, 1)}


if __name__ == "__main__":
    r = run()
    print(f"M1–M7 hazırdır ({r['seconds']} s)")
    for B, p in r["plans"].items():
        print(f"büdcə {B}: {', '.join(p['sel'])} | xərc {p['cost']:.0f} | hədəf funksiyası {p['obj']:.1f}")
