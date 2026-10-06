"""FX transmission (R03 devaluation) — ONE calibration used by simulate, scalability, monitor and the stress tests.

A devaluation is a step in the log level of USD/AZN (x, log points vs the baseline path). Three channels:
1. CPI: pass-through of AZN import-price inflation, distributed over two years (structural distributed lag on an
   exogenous regressor — no lagged dependent variable): cpi_t = a + b0·π^imp,AZN_t + b1·π^imp,AZN_(t−1), HAC,
   2004–2025. The total is CALIBRATED to the 2015–17 episode: excess CPI 2015–18 over the 2012–14 mean, net of the
   USD import-price part, per log point of depreciation 2015–17; timing (event-year share w0) from the regression.
2. Non-oil output: 2015–16 analogue in LEVELS — cumulative non-oil shortfall vs a symmetric benchmark (mean growth
   2010–14 and 2017–19) net of the FR1 oil (Brent step response) and public-investment channels, per log unit of the
   2015–16 depreciation; event-year share from the analogue; parameter range from the pre/post-only benchmarks.
3. Public debt: revaluation of the external (FX) public debt: Δ(debt/GDP) = s_ext · debt/GDP · (e^x − 1).
Layering (never double counts): the MicroUnit chain already moves CPI/output/debt when FR1 `fx` is shocked (G4 has
dln_fx, deflators, AZN oil revenue). Consumers that run the chain add only OVERLAY = calibrated total − chain part,
the chain part being the convolution of the chain's own FX step response (recomputed whenever the MicroUnit engine
fingerprint changes, so a future FR1 import-price channel automatically shrinks the overlay). simulate.py does not
run the chain for FX, so it uses the calibrated total.
"""
from __future__ import annotations

import json
from functools import lru_cache

import numpy as np
import pandas as pd

from . import config

YEARS = list(config.FORECAST_YEARS)
CACHE = config.ROOT / "work" / "fx_chain_cache"
OUT = "FR1_fx_transmission.csv"
EPISODE = (2015, 2016, 2017)


def _lag(a: np.ndarray) -> np.ndarray:
    return np.concatenate([np.zeros((a.shape[0], 1)), a[:, :-1]], axis=1)


def _diff(a: np.ndarray) -> np.ndarray:
    return np.diff(np.concatenate([np.zeros((a.shape[0], 1)), a], axis=1), axis=1)


def _ext_debt() -> dict:
    """External (FX) public debt share and debt/GDP — MinFin bulletin (cached parse, offline) or the seed."""
    from . import exposures
    d = None
    try:
        d = exposures._last_json("minfin", "debt_parsed.json")
    except Exception:                                   # noqa: BLE001
        d = None
    d = d or dict(exposures.SEED_DEBT)
    tot, ext = float(d["total_azn"]), float(d["ext_azn"])
    gdp = float(d.get("gdp_proj_azn") or np.nan)
    guar = float(d.get("guar_ext_azn") or 0.0)
    return {"s_ext": ext / tot, "debt_gdp": tot / gdp * 100, "ext_gdp": ext / gdp * 100,
            "guar_ext_gdp": guar / gdp * 100, "date": d.get("date", ""), "source": "MN dövlət borcu bülleteni"}


@lru_cache(maxsize=1)
def calibration() -> dict:
    from . import factors, spine
    P = factors.channels()["_panel"].copy()
    mi = spine.micro_fr1_dataset()
    M = spine.multipliers()
    last = config.LAST_ACTUAL
    P["dfx"] = P["dln_fx"]
    # (1) distributed-lag pass-through of AZN import-price inflation
    ch = factors.channels()                              # the single estimate (factors 'cpi_ext')
    b0, b1 = ch[("cpi_ext", "impA")]["coef"], ch[("cpi_ext", "impA_l1")]["coef"]
    se_sum = float(np.sqrt(ch[("cpi_ext", "cov")].sum()))
    e = ch[("cpi_ext", "meta")]
    # (2) 2015–17 episode, net of the USD import-price part predicted by (1)
    pre = float(P.loc[2012:2014, "cpi"].mean())
    imp_bar = float(P.loc[2012:2014, "imp"].mean())
    E = P.loc[2015:2018]
    usd = b0 * (E["imp"] - imp_bar) + b1 * (P["imp"].shift(1).loc[2015:2018] - imp_bar)
    net = (E["cpi"] - pre) - usd
    dfx_ep = float(P.loc[list(EPISODE), "dfx"].clip(lower=0).sum())
    pt_ep = float(net.sum() / dfx_ep)
    X = np.c_[E["dfx"].clip(lower=0), P["dfx"].shift(1).loc[2015:2018].clip(lower=0)]
    c_ls, *_ = np.linalg.lstsq(X, net.to_numpy(), rcond=None)
    w0 = b0 / (b0 + b1)
    pred_reg = float((b0 + b1) * dfx_ep)
    # (3) non-oil analogue in levels (2015–16)
    g = P["nonoil_g"]
    m1, m2 = (float(v) for v in M["brent10"]["rgdpnon"].iloc[:2])
    k1, k2 = (float(v) for v in M["stateinv1bn"]["rgdpnon"].iloc[:2])
    b_bar = float(P.loc[2010:2014, "brent"].mean())
    d15, d16 = P.at[2015, "brent"] - b_bar, P.at[2016, "brent"] - b_bar
    oil15, oil16 = d15 / 10 * m1, d15 / 10 * m2 + (d16 - d15) / 10 * m1
    i_bar = float(mi.loc[2010:2014, "rinv_state"].mean())
    i15, i16 = (mi.at[2015, "rinv_state"] - i_bar) / 1000, (mi.at[2016, "rinv_state"] - i_bar) / 1000
    inv15, inv16 = i15 * k1, i15 * k2 + (i16 - i15) * k1
    dfx_1516 = float(P.loc[[2015, 2016], "dfx"].sum())

    def resid(bench):
        s15 = g[2015] - bench
        s16 = s15 + g[2016] - bench
        return s15 - oil15 - inv15, s16 - oil16 - inv16
    benches = {"simmetrik": float((g.loc[2010:2014].mean() + g.loc[2017:2019].mean()) / 2),   # equal-weight windows
               "əvvəl": float(g.loc[2010:2014].mean()), "sonra": float(g.loc[2017:2019].mean())}
    R = {k: resid(v) for k, v in benches.items()}
    L = {k: float(v[1] / dfx_1516 * 100) for k, v in R.items()}           # % level per log unit
    w0g = float(np.clip(R["simmetrik"][0] / R["simmetrik"][1], 0.0, 1.0)) if R["simmetrik"][1] else 0.5
    # (5) devaluation episodes (consecutive trigger years = one episode)
    drop = (P["brent"] / P["brent"].shift(1).rolling(3).mean() - 1) * 100
    fxg = P["usd_azn"].pct_change(fill_method=None) * 100
    trig = [int(y) for y in drop[drop <= factors.params()["devaluation_brent_drop"]].dropna().index]
    eps, cur = [], []
    for y in trig:
        if cur and y != cur[-1] + 1:
            eps.append(cur)
            cur = []
        cur.append(y)
    if cur:
        eps.append(cur)
    dev_eps = [ep for ep in eps if any(fxg.get(y, 0) > 10 for y in ep)]
    return {"b0": b0, "b1": b1, "se_sum": se_sum, "n_reg": e["n"], "sample_reg": e["sample"],
            "pt_reg": b0 + b1, "pt_episode": pt_ep, "pt_ls": float(c_ls.sum()), "w0_ls": float(c_ls[0] / c_ls.sum()),
            "pt": pt_ep, "w0": w0, "pt_lo": min(b0 + b1, pt_ep) - se_sum, "pt_hi": max(float(c_ls.sum()), pt_ep) + se_sum,
            "episode_excess": float((E["cpi"] - pre).sum()), "episode_net": float(net.sum()), "dfx_episode": dfx_ep,
            "pred_reg_episode": pred_reg, "cpi_pre": pre,
            "L": L["simmetrik"], "L_lo": min(L.values()), "L_hi": max(L.values()), "L_all": L, "w0g": w0g,
            "bench": benches, "oil_ch": oil16, "inv_ch": inv16, "resid15": R["simmetrik"][0], "resid16": R["simmetrik"][1],
            "dfx_1516": dfx_1516, **_ext_debt(),
            "trigger_years": trig, "episodes": eps, "dev_episodes": dev_eps,
            "p_dev": len(dev_eps) / max(len(eps), 1)}


def responses(dlog, pt=None, w0=None, L=None, w0g=None) -> dict:
    """Calibrated TOTAL response to a USD/AZN log-level deviation path `dlog` (log points ×100 vs baseline; N×T or T).
    Returns cpi (pp), nonoil_lvl (% level), nonoil_g (pp growth), debt_gdp (pp of GDP); parameters may be arrays (N)."""
    c = calibration()
    x = np.atleast_2d(np.asarray(dlog, float))
    p = lambda v, d: np.atleast_1d(c[d] if v is None else v).astype(float)[:, None]  # noqa: E731
    pt, w0, L, w0g = p(pt, "pt"), p(w0, "w0"), p(L, "L"), p(w0g, "w0g")
    dx = _diff(x)
    cpi = pt * (w0 * dx + (1 - w0) * _lag(dx))
    lvl = L / 100 * (w0g * x + (1 - w0g) * _lag(x))
    debt = c["s_ext"] * c["debt_gdp"] * (np.exp(x / 100) - 1)
    return {"cpi": cpi, "nonoil_lvl": lvl, "nonoil_g": _diff(lvl), "debt_gdp": debt}


def draw_params(rng, n: int) -> dict:
    """Parameter uncertainty for the Monte Carlo: pt ~ N(pt, se_sum) floored at 0; L ~ triangular(L_lo, L, L_hi)."""
    c = calibration()
    lo, md, hi = sorted([c["L_lo"], c["L"], c["L_hi"]])[0], c["L"], sorted([c["L_lo"], c["L"], c["L_hi"]])[-1]
    md = min(max(md, lo), hi)
    L = rng.triangular(lo, md, hi, size=n) if hi > lo else np.full(n, md)
    return {"pt": np.maximum(c["pt"] + c["se_sum"] * rng.standard_normal(n), 0.0), "L": L}


def _fingerprint() -> str:
    from . import scalability
    return scalability.engine_fingerprint()


@lru_cache(maxsize=1)
def chain_step() -> dict:
    """MicroUnit chain response per log point to a sustained +10 % USD/AZN step from the first forecast year
    (ru:cpi pp, ru:nonoil_lvl %, ru:debt_gdp pp, debt_reval pp) — cached per engine fingerprint."""
    key = _fingerprint()
    p = CACHE / f"fx_step3_{key}.json"
    if p.exists():
        return {k: np.asarray(v, float) for k, v in json.loads(p.read_text()).items()}
    from . import scalability as sc
    base, _ = sc.run_chain({}, "fx-step-base", overlays=False)
    shock, _ = sc.run_chain({"FR1": {"exogenous": {"fx": {"pct": 10.0}}}}, "fx-step", overlays=False)
    dd = sc.derived_delta(base, shock, sc.factor_data()["rgdpnon_2025"])
    u = 100 * np.log(1.10)
    out = {k: [dd[(f"ru:{k}", y)] / u for y in YEARS] for k in ("cpi", "nonoil_lvl", "debt_gdp", "budget_gdp")}
    # the chain's own revaluation of the debt stock (Δ debt_azn / GDP); its nominal-GDP denominator effect is NOT an
    # FX-debt channel and stays in the chain (overlay for debt = calibrated revaluation − chain revaluation)
    # impact-year stock change only: later debt_azn changes are deficit FLOWS (already in the chain), not revaluation
    y0 = YEARS[0]
    r0 = (shock[("fr1:debt_azn", y0)] - base[("fr1:debt_azn", y0)]) / base[("fr1:gdp_n", y0)] * 100 / u
    out["debt_reval"] = [r0] * len(YEARS)
    CACHE.mkdir(parents=True, exist_ok=True)
    for old in CACHE.glob("fx_step*.json"):
        old.unlink()
    p.write_text(json.dumps(out))
    return {k: np.asarray(v, float) for k, v in out.items()}


def chain_part(dlog) -> dict:
    """What the MicroUnit chain delivers for the same FX path (linear convolution of its step response)."""
    from .simulate import _convolve
    x = np.atleast_2d(np.asarray(dlog, float))
    st = chain_step()
    out = {k: _convolve(x, st[k]) for k in ("cpi", "nonoil_lvl")}
    out["debt_gdp"] = _convolve(x, st["debt_reval"])
    out["nonoil_g"] = _diff(out["nonoil_lvl"])
    return out


def overlay(dlog) -> dict:
    """Calibrated total − chain part: what a consumer that already ran the chain must ADD (never double counts)."""
    t, c = responses(dlog), chain_part(dlog)
    return {k: t[k] - c[k] for k in t}


def path_from_fx(fx_new, fx_base) -> np.ndarray:
    """USD/AZN level paths → log-point deviation path."""
    return 100 * np.log(np.asarray(fx_new, float) / np.asarray(fx_base, float))


def table(size: float = 0.165) -> pd.DataFrame:
    """FR1_fx_transmission.csv: parameters (with n, se, sample) and the responses to a `size` devaluation from
    the first forecast year — calibrated total, chain part, overlay."""
    c = calibration()
    rows = [
        ("pt_reg", c["pt_reg"], f"b0 {c['b0']:.3f} + b1 {c['b1']:.3f}; se(cəm) {c['se_sum']:.3f}", c["n_reg"], c["sample_reg"],
         "İQİ ← AZN idxal qiymətləri inflyasiyası (cari + 1 il gecikmə), HAC; asılı dəyişənin gecikməsi yoxdur"),
        ("pt_episode", c["pt_episode"], f"2015–18 artıq İQİ {c['episode_excess']:.1f} f.b., USD idxal hissəsi çıxılmaqla "
         f"{c['episode_net']:.1f} f.b. / {c['dfx_episode']:.1f} log bənd", 4, "2015–2018", "KALİBRLƏMƏ: cəmi ötürmə (istifadə olunur)"),
        ("w0", c["w0"], f"epizod LS: {c['w0_ls']:.2f} (cəm {c['pt_ls']:.3f})", c["n_reg"], c["sample_reg"],
         "hadisə ilinin payı (qalan hissə növbəti ildə)"),
        ("pt_range", c["pt_hi"] - c["pt_lo"], f"[{c['pt_lo']:.3f}; {c['pt_hi']:.3f}]", np.nan, "", "qeyri-müəyyənlik aralığı"),
        ("L_nonoil", c["L"], f"aralıq [{c['L_lo']:.1f}; {c['L_hi']:.1f}] (etalon: {', '.join(f'{k} {v:.2f}' for k, v in c['bench'].items())})",
         2, "2015–2016", "qeyri-neft səviyyə itkisi, % / log vahid (neft və investisiya kanalları çıxılmaqla)"),
        ("w0g", c["w0g"], f"2015 qalığı {c['resid15']:.2f} / 2016 məcmu {c['resid16']:.2f}", 2, "2015–2016", "hadisə ilinin payı"),
        ("s_ext", c["s_ext"], f"borc/ÜDM {c['debt_gdp']:.1f}%, xarici {c['ext_gdp']:.1f}% (zəmanətli xarici {c['guar_ext_gdp']:.1f}% daxil deyil)",
         np.nan, str(c["date"]), "xarici (valyuta) borcun payı — yenidənqiymətləndirmə"),
        ("p_dev", c["p_dev"], f"epizodlar {c['episodes']}; devalvasiya: {c['dev_episodes']}", len(c["episodes"]), "",
         "P(devalvasiya | Brent çöküşü epizodu)"),
    ]
    T = pd.DataFrame(rows, columns=["parametr", "deyer", "izah", "n", "numune", "qeyd"])
    T["setir_novu"] = "parametr"
    x = np.zeros(len(YEARS))
    x[:] = 100 * np.log1p(size)
    tot, chp = responses(x), None
    try:
        chp = chain_part(x)
    except Exception:                                   # noqa: BLE001 — engine unavailable: totals still valid
        chp = None
    R = []
    for k, lab in (("cpi", "inflyasiya, f.b."), ("nonoil_lvl", "qeyri-neft səviyyəsi, %"), ("nonoil_g", "qeyri-neft artımı, f.b."),
                   ("debt_gdp", "dövlət borcu, % ÜDM (f.b.)")):
        for t, y in enumerate(YEARS):
            ch = float(chp[k][0, t]) if chp is not None else np.nan
            R.append({"parametr": k, "deyer": float(tot[k][0, t]), "izah": lab, "n": np.nan, "numune": str(y),
                      "qeyd": f"+{size * 100:g}% devalvasiya ({YEARS[0]}-dən)", "setir_novu": "cavab",
                      "il": y, "cemi": float(tot[k][0, t]), "zencir": ch, "elave_qat": float(tot[k][0, t]) - ch})
    return pd.concat([T, pd.DataFrame(R)], ignore_index=True)


def run(ctx: dict | None = None) -> dict:
    from . import spine
    T = table()
    T.to_csv(config.OUTPUT / OUT, index=False, float_format="%.6g")
    spine.register_output(OUT, "riskunit.fx", "Məzənnə ötürməsi (vahid modul): İQİ-yə iki illik ötürmə (2015–17 ilə kalibrlənmiş), "
                          "qeyri-neft səviyyə itkisi (2015–16 analoqu), xarici borcun yenidənqiymətləndirilməsi; +16,5% "
                          "devalvasiyaya cavab — cəmi, MikroUnit zənciri və əlavə qat", list(T.columns), "rüblük / mühərrik dəyişəndə")
    return {"fx": T}


if __name__ == "__main__":
    print(run()["fx"].to_string())
