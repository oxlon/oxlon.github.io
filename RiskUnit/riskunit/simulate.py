"""FR2 — joint stochastic simulation of the core around the baseline.

Risk is the simulated distribution of the core (Methodology Blueprint §1.1). The engine:

1. draws factor innovations jointly by resampling whole historical years (2003–2025), which
   keeps the observed co-movement of Brent, partner growth, remittances, lending rates and
   regional geopolitical risk without imposing a parametric copula;
2. adds independent hazard events (earthquake: Poisson by magnitude tier; drought: SPI drawn
   from 1961–2025), the conditional devaluation event, micro-signal events and the expert
   overlays declared in the register;
3. transmits every factor through the micro FR1 structural model's step responses
   (distributed-lag convolution of the shock path) or through the estimated direct channel;
4. adds the core's own residual uncertainty so that the total spread matches the macro
   model's fan for the same variable and year (the risk unit never invents its own width).

Every channel is kept as a separate additive component per draw, so risk contributions
(variance shares and lower-tail Euler contributions) are exact decompositions.

v2 (2026-10-06) — two views and three evidence-driven fixes (docs/Risk_Metodologiyasi.md §12):
* view="baseline" (default; scores, heat map, stress tests, DSA): Brent is centred on the macro
  assumption and the median of every outcome equals the official baseline exactly (the risk unit
  publishes no central path) — since v2.1 except in the running year, whose observed months are fixed
  at the year-to-date outturn in both views (the baseline applies to unobserved months only); view="live": Brent centre conditioned on today's market data
  (inverse-MSE combination with the spot, the D6 monitor's driver), median = baseline + the
  deterministic response to the live gap, nothing else.
* R01 procyclical investment reaction: re-estimated on 2007–2025 (the 2005–06 rinv_state splice is
  excluded), NET of the investment response that the FR1 Brent multiplier already contains
  (rinv_state +3.2…3.8 % per +10 USD — the v1 code double-counted it), and SOFAZ-transfer financed:
  it moves growth and CPI but not the state-budget balance. Only the part of investment kept above
  the transfer-financed path (T09 floor) is deficit financed (FR1 balance_n response, mln AZN).
* bands: residual layering fills the calibrated macro fan; the fiscal fan is calibrated to the
  random-walk error of the balance ratio (NFR1 calibration row 'fis').
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

from . import config, factors, fx, parametrler, spine

YEARS = config.FORECAST_YEARS
T = len(YEARS)


@dataclass
class SimResult:
    years: list
    score_year: int
    brent: np.ndarray                     # N×T USD/bbl
    brent_base: np.ndarray                # T
    gpr_reg: np.ndarray                   # N×T
    comp_g: dict = field(default_factory=dict)    # channel -> N×T contribution to non-oil growth, pp
    comp_cpi: dict = field(default_factory=dict)  # channel -> N×T contribution to CPI inflation, pp
    comp_fis: dict = field(default_factory=dict)  # channel -> N×T contribution to budget balance, % GDP
    events: dict = field(default_factory=dict)    # risk_id -> N×T bool
    base: dict = field(default_factory=dict)      # outcome -> T baseline
    meta: dict = field(default_factory=dict)

    def total(self, kind: str) -> np.ndarray:
        comp = {"g": self.comp_g, "cpi": self.comp_cpi, "fis": self.comp_fis}[kind]
        return self.base[kind][None, :] + sum(comp.values())

    def col(self, year: int) -> int:
        return self.years.index(year)


CHANNEL_AZ = {
    "brent": "Neft qiyməti — birbaşa (R01)", "fiscal_react": "Neft qiyməti — prosiklik investisiya reaksiyası (R01)",
    "transition": "Enerji keçidi (R14)", "gpr": "Geosiyasi eskalasiya (R06)",
    "partner": "Tərəfdaş tələbi (R05)", "rate": "Kredit faizi (R02)", "remit": "Pul baratları (R07)",
    "deval": "Devalvasiya (R03)", "quake": "Zəlzələ (R08)", "drought": "Quraqlıq (R09)",
    "bank": "Bank sektoru (R04, ekspert)", "flood": "Daşqın (R10, ekspert)",
    "manuf": "Emal sahələri (R15)", "compet": "Rəqabət (R16)", "resid": "Modelin qalıq qeyri-müəyyənliyi",
    "import": "İdxal qiymətləri (R17)", "food": "Dünya ərzaq qiymətləri (R18)",
}
CHANNEL_RISK = {"brent": "R01", "fiscal_react": "R01", "rate": "R02", "deval": "R03", "bank": "R04", "partner": "R05",
                "gpr": "R06", "remit": "R07", "quake": "R08", "drought": "R09", "flood": "R10",
                "transition": "R14", "manuf": "R15", "compet": "R16", "import": "R17", "food": "R18"}
VIEWS = {"baseline": "baza mərkəzli (rəsmi proqnozlarla uyğun; skorlar və istilik xəritəsi)",
         "live": "canlı məlumatla şərtləndirilmiş (cari bazar; D6 proqnoz təsiri monitoru ilə uyğun)"}

def _step_response(mult: pd.DataFrame, var: str) -> np.ndarray:
    return mult[var].reindex(YEARS).to_numpy(dtype=float)


def _convolve(shock: np.ndarray, step: np.ndarray) -> np.ndarray:
    """Level response of a linear model to an arbitrary shock path, given its response to a
    sustained unit step: r_t = Σ_j Δs_j · m_{t-j}.  shock: N×T in step units."""
    ds = np.diff(np.concatenate([np.zeros((shock.shape[0], 1)), shock], axis=1), axis=1)
    out = np.zeros_like(shock)
    for t in range(T):
        for j in range(t + 1):
            out[:, t] += ds[:, j] * step[t - j]
    return out


def _level_to_growth(level_dev: np.ndarray) -> np.ndarray:
    """% level deviation → pp contribution to annual growth (first difference)."""
    return np.diff(np.concatenate([np.zeros((level_dev.shape[0], 1)), level_dev], axis=1), axis=1)


def _lognormal_from_med_p90(rng, med, p90, size):
    sig = np.log(p90 / med) / stats.norm.ppf(0.9)
    return med * np.exp(sig * rng.standard_normal(size))


def micro_signals() -> dict:
    """R15 (FR10 enterprise early warning) and R16 (FR12 competition early warning):
    probability and impact if the signal materialises, from the micro unit's own outputs."""
    mi = spine.micro_fr1_dataset()
    last = config.LAST_ACTUAL
    man_share = float(mi.loc[last, "va_man_n"] / mi.loc[last, "gdp_nonoil_n"] * 100)
    con_share = float(mi.loc[last, "va_con_n"] / mi.loc[last, "gdp_nonoil_n"] * 100)
    trd_share = float(mi.loc[last, "va_trd_n"] / mi.loc[last, "gdp_nonoil_n"] * 100)
    ews = spine._csv(config.MICRO_FILES["fr10_ews"])
    pl = spine._csv(config.MICRO_FILES["fr10_plausibility"]).copy()
    pl["code"] = pl["code"].astype(str).str.zfill(2)
    ews = ews.assign(code=ews["nace2"].astype(str).str.zfill(2)).merge(
        pl[["code", "worst_5yr", "hist_2010_2019"]], on="code", how="left")
    w = ews[ews["watch_list"]]
    p15 = float((w["n_flags"] / 6).mean()) if len(w) else 0.0
    # loss if the watch-listed branches repeat their worst 5-year average growth instead of their
    # 2010-2019 average: share of manufacturing × gap × manufacturing share of non-oil GDP
    gap = (w["worst_5yr"] - w["hist_2010_2019"]).clip(upper=0)
    i15 = float(-(w["share_2025_pct"] / 100 * gap).sum() * man_share / 100)
    e12 = spine._csv(config.MICRO_FILES["fr12_ews"])
    fl = spine._csv(config.MICRO_FILES["fr12_false_listing"])
    fl2 = float(fl.loc[(fl["z_threshold"] - 2.0).abs().idxmin(), "false_listing_rate"])
    top = e12.sort_values("score", ascending=False).head(2)
    p16 = float(min(1.0, top["score"].max() / 0.30) * (1 - fl2) * 0.5)
    sc = spine._csv(config.MICRO_FILES["fr12_scenarios"])
    merg = sc[sc["scenario"] == "S2"]
    d_out = float(((merg["d_output_min"] + merg["d_output_max"]) / 2).mean())       # % output in the market
    d_pr = float(((merg["d_price_min"] + merg["d_price_max"]) / 2).mean())
    shares = {"CON": con_share, "TRD": trd_share}
    sec = sum(shares.get(g, 0.0) for g in top["group"])
    i16 = float(-d_out / 100 * sec)
    c16 = float(d_pr * sec / 100)
    return {"p15": p15, "i15": i15, "watch": w[["branch", "n_flags", "share_2025_pct", "worst_5yr",
                                                "hist_2010_2019"]], "man_share": man_share,
            "p16": p16, "i16": i16, "c16": c16, "fr12_top": top[["group", "name", "score", "flags"]],
            "false_listing_z2": fl2}


def run(n: int = config.N_SIM, seed: int = config.SEED, score_year: int | None = None,
        overrides: dict | None = None, view: str = "baseline") -> SimResult:
    """Joint simulation. `overrides` lets FR3 stress scenarios and tests fix factor paths.
    view='baseline' (default): centred on the official baseline for unobserved months (median = baseline
    except in the running year, whose observed months are fixed at the YTD outturn — v2.1);
    view='live': Brent centre conditioned on the live market data (see module docstring)."""
    if view not in VIEWS:
        raise ValueError(f"view must be one of {list(VIEWS)}")
    rng = np.random.default_rng(seed)
    ov = overrides or {}
    p = factors.params()
    ch = factors.channels()
    hz = factors.hazards()
    dv = factors.devaluation()
    reg = factors.register().set_index("risk_id")
    B = spine.baseline()
    M = spine.multipliers()
    L = spine.live()
    P = ch["_panel"]
    sy = score_year or config.score_year()

    # ---------------- historical innovation table (whole years resampled jointly)
    H = pd.DataFrame({
        "brent": P["dln_brent"] / 100,
        "partner": P["partner_g"],
        "remit": P["remit_gw"],
        "lend": P["lendrate"].diff(),
        "gpr": P["dl_gpr_reg"] / 100,
        # R17/R18 (CAEM categories): import-price inflation and world food-price growth, each
        # orthogonalised on Brent (and food on imports) so that FR1's Brent channel is not double-counted
        "imp": P["imp_own"],
        "food": P["food_own"],
    }).loc[2003:config.LAST_ACTUAL].dropna()
    H = H - H.mean()
    H["brent"] = H["brent"] * calibration_factors()["brent"]      # NFR1 recalibration of the oil tails
    H["remit"] = H["remit"] - (H["remit"].median() - 0)            # median-centred: 2022 inflow is a tail
    idx = rng.integers(0, len(H), size=(n, T))
    E = {k: H[k].to_numpy()[idx] for k in H.columns}

    # parameter uncertainty of reduced-form channels: one draw per simulated path
    def pdraw(key):
        c = ch[key]
        return c["coef"] + c["se"] * rng.standard_normal(n)
    b_gpr_brent = pdraw(("gpr_brent", "annual_avg"))
    b_gpr_partner = pdraw(("partner_gpr", "dl_gpr_reg"))
    b_gpr_remit = pdraw(("remit_gpr", "dl_gpr_reg"))
    b_brent_remit = pdraw(("remit", "dln_brent"))
    b_spi = pdraw(("agri_spi", "spi"))
    b_inv0 = pdraw(("inv_brent", "dln_brent"))
    b_inv1 = pdraw(("inv_brent", "dln_brent_l1"))
    # single external-price pass-through (factors 'cpi_ext'): joint draw of (b0, b1) per path
    ce = (ch[("cpi_ext", "impA")]["coef"], ch[("cpi_ext", "impA_l1")]["coef"])
    bext = rng.multivariate_normal(ce, ch[("cpi_ext", "cov")], size=n)
    b_ext0, b_ext1 = bext[:, 0], bext[:, 1]
    fxp = fx.draw_params(rng, n)                       # FX module parameter uncertainty (pt, L)

    # ---------------- partial observation of the running year (v2.1, audit C3: YTD nowcast in BOTH views)
    as_of = pd.Timestamp(config.as_of())
    ry = running_year()
    f_rem = np.ones(T)
    if YEARS[0] == as_of.year:
        last_obs_month = pd.Timestamp(L["brent_last_date"]).month
        f_rem[0] = max(0.0, (12 - last_obs_month) / 12)
    f_obs_growth = np.ones(T)
    if YEARS[0] == as_of.year:
        # remaining share of the year after the DSK Jan–M outturn (v2.0: fixed 0,5)
        f_obs_growth[0] = (12 - ry["g_months"]) / 12 if "g_months" in ry else float(parametrler.get("sim_f_obs_growth", 0.5))
    f_obs_cpi = f_obs_growth.copy()
    if YEARS[0] == as_of.year and "cpi_months" in ry:
        f_obs_cpi[0] = (12 - ry["cpi_months"]) / 12

    # ---------------- Brent path: live-conditioned centre + resampled innovations
    w = ch[("brent_combo", "w_struct")]
    base_b = B["brent_usd"].to_numpy()
    if view == "live":
        lb_last = np.log(L["brent_last_month"])
        centre = np.exp(w * np.log(base_b) + (1 - w) * lb_last)
    else:                                   # baseline view: the macro unit's Brent assumption for unobserved months
        centre = base_b.astype(float).copy()
    if YEARS[0] == as_of.year:              # both views: observed months fixed at the year-to-date average
        centre[0] = (1 - f_rem[0]) * L["brent_ytd_avg"] + f_rem[0] * centre[0]
    gpr_part = b_gpr_brent[:, None] * E["gpr"]
    own = E["brent"] - gpr_part
    scale = f_rem[None, :]
    cum_own = np.cumsum(own * scale, axis=1)
    cum_gpr = np.cumsum(gpr_part * scale, axis=1)
    # the centre is the median path by construction: remove the small-sample median of the resampled
    # cumulative innovations (whole-year bootstrap of 23 years is not exactly median-zero)
    cum_own = cum_own - np.median(cum_own + cum_gpr, axis=0)[None, :]
    # energy-transition overlay (R14): Bernoulli on the whole path, -x %/yr drift from year 2
    p14 = float(reg.at["R14", "ekspert_ehtimal"]) if "R14" in reg.index else 0.0
    trans_on = rng.random(n) < p14
    det = bool(ov.get("deterministic"))               # stress mode: only the declared shocks act
    if det:
        trans_on[:] = False
    d_tr = float(parametrler.get("sim_transition_drift", -0.03))
    drift = np.array([0.0] + [d_tr * k for k in range(1, T)])
    cum_tr = trans_on[:, None] * drift[None, :]
    if "brent_path" in ov:                                        # stress scenario override
        brent = np.tile(np.asarray(ov["brent_path"], dtype=float), (n, 1))
        cum_own = np.log(brent / centre[None, :])
        cum_gpr = np.zeros_like(cum_own)
        cum_tr = np.zeros_like(cum_own)
    brent = centre[None, :] * np.exp(cum_own + cum_gpr + cum_tr)
    brent_noshock = centre[None, :] * np.exp(cum_own + cum_gpr)
    # dollar deviation from the macro baseline, split by source
    d_brent_total = brent - base_b[None, :]
    d_brent_gpr = centre[None, :] * np.exp(cum_own) * (np.exp(cum_gpr) - 1)
    d_brent_tr = brent - brent_noshock
    d_brent_own = d_brent_total - d_brent_gpr - d_brent_tr

    # ---------------- regional GPR level path (for R06 event definition)
    gm = factors.regional_gpr_monthly()
    gpr_ref = float(gm.iloc[-12:].mean())
    gpr_reg = gpr_ref * np.exp(np.cumsum(E["gpr"], axis=1))

    # ---------------- partner demand: growth deviations → external demand level (%)
    eps_ext = p["ext_demand_elasticity"]
    part_dev = E["partner"] * f_obs_growth[None, :]
    part_gpr = b_gpr_partner[:, None] * E["gpr"] * 100 * f_obs_growth[None, :]
    part_own = part_dev - part_gpr
    if "partner_dev" in ov:
        part_own = np.tile(np.asarray(ov["partner_dev"], dtype=float), (n, 1))
        part_gpr = np.zeros_like(part_own)
    ext_own = np.cumsum(eps_ext * part_own, axis=1)
    ext_gpr = np.cumsum(eps_ext * part_gpr, axis=1)

    # ---------------- lending rate deviation (pp, transitory)
    lend = E["lend"] * f_obs_growth[None, :]
    if "lend_dev" in ov:
        lend = np.tile(np.asarray(ov["lend_dev"], dtype=float), (n, 1))

    # ---------------- remittances: % growth deviations → level (log) deviation
    rem_brent = b_brent_remit[:, None] * E["brent"] * 100
    rem_gpr = b_gpr_remit[:, None] * E["gpr"] * 100
    rem_own = E["remit"] - rem_brent - rem_gpr
    if "remit_dev" in ov:
        rem_own = np.tile(np.asarray(ov["remit_dev"], dtype=float), (n, 1))
        rem_brent = np.zeros_like(rem_own)
        rem_gpr = np.zeros_like(rem_own)
    remit_share = float(P.loc[config.LAST_ACTUAL, "remit_usd"] * B["usd_azn"].iloc[0]
                        / spine.micro_fr1_dataset().loc[config.LAST_ACTUAL, "gdp_nonoil_n"] * 100)
    mpc = p["remit_mpc"]
    def rem_level(g):
        return np.cumsum(np.log1p(np.clip(g * f_obs_growth[None, :], -90, 300) / 100), axis=1) * 100
    lv_rem_own = remit_share / 100 * mpc * rem_level(rem_own)
    lv_rem_gpr = remit_share / 100 * mpc * rem_level(rem_gpr)
    lv_rem_brent = remit_share / 100 * mpc * rem_level(rem_brent)

    # ---------------- drought: SPI per year (2026 hydrological year already observed)
    spi_hist = hz["spi_hist"].to_numpy()
    spi = rng.choice(spi_hist, size=(n, T))
    if YEARS[0] == as_of.year and as_of.month >= 10:
        spi[:, 0] = hz["spi_now"]
    if "spi" in ov:
        spi = np.tile(np.asarray(ov["spi"], dtype=float), (n, 1))
    agri_share = float(P.loc[config.LAST_ACTUAL, "agri_share_nonoil"])
    lv_drought = b_spi[:, None] * spi * agri_share / 100            # transitory level effect, %

    # ---------------- earthquakes: Poisson by tier, lognormal damage (% GDP)
    lam1, lam2 = hz["eq_lambda_tier1"], hz["eq_lambda_tier2"]
    rem_frac = f_rem.copy()
    n1 = rng.poisson(lam1 * rem_frac[None, :], size=(n, T))
    n2 = rng.poisson(lam2 * rem_frac[None, :], size=(n, T))
    dmg = np.zeros((n, T))
    for k in range(1, int(max(n1.max(), n2.max(), 1)) + 1):
        dmg += (n1 >= k) * _lognormal_from_med_p90(rng, p["eq_damage_med_tier1"], p["eq_damage_p90_tier1"], (n, T))
        dmg += (n2 >= k) * _lognormal_from_med_p90(rng, p["eq_damage_med_tier2"], p["eq_damage_p90_tier2"], (n, T))
    if "quake_damage" in ov:
        dmg = np.tile(np.asarray(ov["quake_damage"], dtype=float), (n, 1))
    elif det:
        dmg = np.zeros((n, T))
    mi_last = spine.micro_fr1_dataset().loc[config.LAST_ACTUAL]
    gdp_over_nonoil = float(mi_last["gdp_n"] / mi_last["gdp_nonoil_n"])     # damage in % GDP → % non-oil GDP
    # v2.1 (same profile as scalability.quake_profiles): the output loss fades as capital is rebuilt; reconstruction
    # (eq_fiscal_share × damage) is spent 25/50/25 % over three years and passes through the FR1 investment multiplier
    from .scalability import QUAKE_REC
    loss_w = np.cumsum((1.0,) + tuple(-w for w in QUAKE_REC))[:len(QUAKE_REC)]       # 1, 0.75, 0.25
    def spread(a, w):
        out = np.zeros_like(a)
        for k, wk in enumerate(w):
            out[:, k:] += wk * a[:, :T - k]
        return out
    lv_quake_dir = -p["eq_output_loss"] * spread(dmg, loss_w) * gdp_over_nonoil      # % of non-oil GDP
    p_inv = float(mi_last["p_inv"])
    rec_bn = p["eq_fiscal_share"] * spread(dmg, QUAKE_REC) / 100 * B["fr1_gdp_n"].to_numpy()[None, :] / p_inv / 1000

    # ---------------- conditional devaluation (one per path at most) — v2.1: ONE FX module (riskunit.fx)
    # trigger = first year of a run of crash years (an episode; consecutive trigger years are one episode, p_dev = 1/3)
    Pa = spine.annual_panel()["brent"]
    hist_b = Pa.loc[config.LAST_ACTUAL - 3:config.LAST_ACTUAL].to_numpy()
    full = np.concatenate([np.tile(hist_b, (n, 1)), brent], axis=1)
    deval = np.zeros((n, T), dtype=bool)
    happened = np.zeros(n, dtype=bool)
    trig_prev = np.full(n, (hist_b[-1] / hist_b[:3].mean() - 1) * 100 <= p["devaluation_brent_drop"])
    u = rng.random((n, T))
    for t in range(T):
        prev3 = full[:, t + 1:t + 4].mean(axis=1)
        trig = (full[:, t + 4] / prev3 - 1) * 100 <= p["devaluation_brent_drop"]
        hit = trig & ~trig_prev & (u[:, t] < dv["p_dev"]) & ~happened
        trig_prev = trig
        if "deval_year" in ov:
            hit = np.full(n, YEARS[t] == ov["deval_year"])
        elif det:
            hit = np.zeros(n, dtype=bool)
        deval[:, t] = hit
        happened |= hit
    size = np.log1p(p["devaluation_size"]) * 100                       # log points
    dev_on = np.cumsum(deval, axis=1) > 0
    x_fx = dev_on * size
    if YEARS[0] == as_of.year:
        x_fx[:, 0] *= f_rem[0]                     # a devaluation in the running year: remaining months of the average
    fxr = fx.responses(x_fx, pt=fxp["pt"], L=fxp["L"])
    lv_deval, cpi_deval, fis_deval = fxr["nonoil_lvl"], fxr["cpi"], fxr["fis"]
    debt_deval = fxr["debt_gdp"]

    # ---------------- micro signals and expert overlays (independent Bernoulli per year)
    ms = micro_signals()
    ev15 = rng.random((n, T)) < ms["p15"]
    ev16 = rng.random((n, T)) < ms["p16"]
    if det:
        ev15[:] = False
        ev16[:] = False
    lv_manuf = -ms["i15"] * ev15
    lv_compet = -ms["i16"] * ev16
    cpi_compet = ev16 * ms["c16"]
    def expert(rid):
        if rid not in reg.index or pd.isna(reg.at[rid, "ekspert_ehtimal"]):
            z = np.zeros((n, T))
            return np.zeros((n, T), dtype=bool), z, z, z
        e = rng.random((n, T)) < float(reg.at[rid, "ekspert_ehtimal"])
        if det:
            e[:] = False
        return (e, -float(reg.at[rid, "ekspert_tesir_qeyri_neft"]) * e,
                float(reg.at[rid, "ekspert_tesir_cpi"]) * e, -float(reg.at[rid, "ekspert_tesir_fiskal"]) * e)
    ev04, g04, c04, f04 = expert("R04")
    ev10, g10, c10, f10 = expert("R10")

    # ---------------- transmission through the FR1 structural step responses
    gdp_n = B["fr1_gdp_n"].to_numpy()
    def via(mult, shock_units):
        g = _convolve(shock_units, _step_response(mult, "rgdpnon"))
        c = _convolve(shock_units, _step_response(mult, "infl"))
        f = _convolve(shock_units, _step_response(mult, "balance_n")) / gdp_n[None, :] * 100
        return g, c, f
    lv_b_own, c_b_own, f_b_own = via(M["brent10"], d_brent_own / 10)
    lv_b_gpr, c_b_gpr, f_b_gpr = via(M["brent10"], d_brent_gpr / 10)
    lv_b_tr, c_b_tr, f_b_tr = via(M["brent10"], d_brent_tr / 10)
    lv_x_own, c_x_own, f_x_own = via(M["extdem10"], ext_own / 10)
    lv_x_gpr, c_x_gpr, f_x_gpr = via(M["extdem10"], ext_gpr / 10)
    # credit easing scenario = -200 bp policy rate; one unit = -2 pp on the lending rate (approximation)
    lv_r, c_r, f_r = via(M["credit_ease200"], -lend / 2)
    # procyclical public-investment reaction (R01), v2 — see module docstring:
    #  (i) EXCESS of the historical elasticity (2007–2025) over the response already inside the FR1
    #      Brent multiplier (e_fr1), so the investment effect of Brent is counted once;
    #  (ii) a deviation response to x = log Brent deviation from the baseline assumption (no drift);
    #  (iii) transfer-financed → balance-neutral; only investment kept above that path (T09) is deficit-financed.
    inv0 = float(spine.micro_fr1_dataset().loc[config.LAST_ACTUAL, "rinv_state"])
    e_fr1 = fr1_embedded_inv_elasticity(M, base_b)
    react_scale = np.ones(T)
    if YEARS[0] == as_of.year:
        react_scale[0] = f_rem[0]                      # the running year's budget is largely set
    def reaction(x, b0=b_inv0, b1=b_inv1):             # x: N×T log deviation of Brent from baseline
        x_l1 = np.concatenate([np.zeros((x.shape[0], 1)), x[:, :-1]], axis=1)
        b0, b1 = np.atleast_1d(b0)[:, None], np.atleast_1d(b1)[:, None]
        return inv0 / 1000 * ((b0 - e_fr1) * x * react_scale[None, :] + b1 * x_l1)
    x_own = np.log(centre / base_b)[None, :] + cum_own
    react_on = 0.0 if ov.get("fiscal_react_off") else 1.0
    floor_on = bool(ov.get("fiscal_react_floor"))       # T09: no cut below the baseline investment path
    def react_channel(x):
        z = react_on * reaction(x)
        z_eff = np.maximum(z, 0.0) if floor_on else z
        g_, c_, _ = via(M["stateinv1bn"], z_eff)
        _, _, f_ = via(M["stateinv1bn"], z_eff - z)    # deficit-financed part only (0 without T09)
        return g_, c_, f_
    lv_fr_own, c_fr_own, f_fr_own = react_channel(x_own)
    lv_fr_gpr, c_fr_gpr, f_fr_gpr = react_channel(cum_gpr)
    lv_fr_tr, c_fr_tr, f_fr_tr = react_channel(cum_tr)
    react_inv_mln = react_on * (reaction(x_own) + reaction(cum_gpr) + reaction(cum_tr)) * 1000   # N×T mln AZN (2015 prices)

    # R17 / R18 / R01 — external prices → CPI, v2.1 (audit M1): ONE pass-through (AZN import-price inflation, b0 + b1·lag);
    # USD import-price inflation deviation = a_imp·ΔlnBrent (→ R01 / R06 / R14 by Brent source) + γ·food_own (→ R18)
    # + imp_own (→ R17); world food growth = a_food·ΔlnBrent + food_own (event definition of R18)
    imp_dev = E["imp"] * f_obs_cpi[None, :]
    food_dev = E["food"] * f_obs_cpi[None, :]
    if det:
        imp_dev, food_dev = np.zeros((n, T)), np.zeros((n, T))
    if "imp_dev" in ov:
        imp_dev = np.tile(np.asarray(ov["imp_dev"], dtype=float), (n, 1))
    if "food_dev" in ov:
        food_dev = np.tile(np.asarray(ov["food_dev"], dtype=float), (n, 1))
    pf = ch["_impfood"]
    dev_b = np.log(brent / base_b[None, :])
    dlb = np.diff(np.concatenate([np.zeros((n, 1)), dev_b], axis=1), axis=1) * 100     # pp Δln Brent vs baseline
    d100 = lambda a: np.diff(np.concatenate([np.zeros((n, 1)), a], axis=1), axis=1) * 100  # noqa: E731
    dlb_gpr, dlb_tr = d100(cum_gpr + 0 * dev_b), d100(cum_tr + 0 * dev_b)
    dlb_own = dlb - dlb_gpr - dlb_tr
    ecpi = lambda d: ext_price_cpi(d, b_ext0, b_ext1)  # noqa: E731
    cpi_imp = ecpi(imp_dev)
    cpi_food = ecpi(pf["gamma"] * food_dev)
    c_x_brent, c_x_gpr_imp, c_x_tr = (ecpi(pf["a_imp"] * d) for d in (dlb_own, dlb_gpr, dlb_tr))
    imp_level = pf["imp_base"][None, :] + pf["a_imp"] * dlb + pf["gamma"] * food_dev + imp_dev
    food_level = pf["food_base"][None, :] + pf["a_food"] * dlb + food_dev

    # earthquake reconstruction through the FR1 investment multiplier (deficit-financed: budget cost)
    lv_qr, c_qr, f_qr = via(M["stateinv1bn"], rec_bn)
    lv_quake, fis_quake = lv_quake_dir + lv_qr, f_qr

    # deterministic response to the live Brent gap (zero in the baseline view): the only allowed median shift
    gap = (centre - base_b)[None, :]
    lv_gap, c_gap, f_gap = via(M["brent10"], gap / 10)
    zg = react_on * reaction(np.log(centre / base_b)[None, :], ch[("inv_brent", "dln_brent")]["coef"],
                             ch[("inv_brent", "dln_brent_l1")]["coef"])
    lv_gr, c_gr, _ = via(M["stateinv1bn"], zg)
    c_gx = ext_price_cpi(pf["a_imp"] * np.diff(np.concatenate([[0.0], np.log(centre / base_b) * 100])))
    live_shift = {"g": _level_to_growth(lv_gap + lv_gr)[0], "cpi": (c_gap + c_gr + c_gx)[0], "fis": f_gap[0]}

    # level contributions are summed per risk channel, then turned into growth contributions
    LV = {
        "brent": lv_b_own + lv_rem_brent, "fiscal_react": lv_fr_own,
        "gpr": lv_b_gpr + lv_x_gpr + lv_rem_gpr + lv_fr_gpr, "transition": lv_b_tr + lv_fr_tr,
        "partner": lv_x_own, "rate": lv_r, "remit": lv_rem_own, "deval": lv_deval,
        "quake": lv_quake, "drought": lv_drought, "manuf": lv_manuf, "compet": lv_compet,
        "bank": g04, "flood": g10,
    }
    # transitory components (hazards, signals, expert) are level effects in the event year only
    res = SimResult(years=YEARS, score_year=sy, brent=brent, brent_base=base_b, gpr_reg=gpr_reg)
    for k, lv in LV.items():
        res.comp_g[k] = _level_to_growth(lv)
    res.comp_cpi = {"brent": c_b_own + c_x_brent, "fiscal_react": c_fr_own, "gpr": c_b_gpr + c_x_gpr + c_fr_gpr + c_x_gpr_imp,
                    "transition": c_b_tr + c_fr_tr + c_x_tr, "partner": c_x_own,
                    "rate": c_r, "deval": cpi_deval, "compet": cpi_compet, "bank": c04, "flood": c10,
                    "import": cpi_imp, "food": cpi_food, "quake": c_qr}
    res.comp_fis = {"brent": f_b_own, "fiscal_react": f_fr_own, "gpr": f_b_gpr + f_x_gpr + f_fr_gpr,
                    "transition": f_b_tr + f_fr_tr, "partner": f_x_own,
                    "rate": f_r, "quake": fis_quake, "bank": f04, "flood": f10, "deval": fis_deval}

    # ---------------- centring targets: official baseline (+ live gap response in the live view); running year =
    # YTD nowcast in BOTH views (v2.1, audit C3: observed months fixed, unobserved months as in the view)
    res.base = {"g": B["nonoil_realg"].to_numpy(), "cpi": B["cpi_infl"].to_numpy(),
                "fis": B["fr1_balance_pct"].to_numpy()}
    targets, obs_share = {}, {}
    for kind in ("g", "cpi", "fis"):
        tg = res.base[kind] + (live_shift[kind] if view == "live" else 0.0)
        tg = np.asarray(tg, float).copy()
        obs_share[kind] = np.nan
        if YEARS[0] == as_of.year and kind in ("g", "cpi"):
            c0, m = nowcast_centre(kind, view, float(res.base[kind][0]), ry)
            if np.isfinite(m):
                tg[0], obs_share[kind] = c0, m
        targets[kind] = tg

    # ---------------- core residuals: fill the calibrated fan (macro for g/CPI, FR1 for the balance)
    t5 = stats.t(df=5)
    t5_sd = np.sqrt(5 / 3)
    calib = calibration_factors()
    layer = {}
    def add_resid(kind, sigma_core, comp):
        fac = np.stack([c for c in comp.values()]).sum(axis=0)
        v_fac = fac.var(axis=0)
        s2 = np.maximum(sigma_core ** 2 - v_fac, (RESID_FLOOR * sigma_core) ** 2)
        layer[kind] = {"sig_target": sigma_core, "sig_factors": np.sqrt(v_fac), "sig_resid": np.sqrt(s2),
                       "sig_total": np.sqrt(v_fac + s2)}
        if kind == "cpi":        # v2.1 (audit M6): right-skewed, bounded below (no deflation 2000–2025)
            return shifted_lognormal(rng.standard_normal((n, T)), targets["cpi"], np.sqrt(s2))
        return t5.rvs(size=(n, T), random_state=rng) / t5_sd * np.sqrt(s2)[None, :]
    f_fis = f_obs_growth.copy()
    if YEARS[0] == as_of.year:
        f_fis[0] = float(parametrler.get("sim_f_obs_growth", FIS_OBS_SHARE))
    sig_g = np.array([spine.baseline_band_sigma("nonoil_realg", y) for y in YEARS]) * f_obs_growth * calib["nonoil"]
    sig_c = np.array([spine.baseline_band_sigma("cpi_infl", y) for y in YEARS]) * f_obs_cpi * calib["cpi"]
    sig_f = fiscal_sigma() * f_fis * calib["fis"]
    res.comp_g["resid"] = add_resid("g", sig_g, res.comp_g) * (not det)
    res.comp_cpi["resid"] = add_resid("cpi", sig_c, res.comp_cpi) * (not det)
    res.comp_fis["resid"] = add_resid("fis", sig_f, res.comp_fis) * (not det)

    # ---------------- centring (no own central path): median = target. The offset is booked on the core residual,
    # whose location belongs to the upstream forecaster; event channels keep their skew (mean − median = balance of risks).
    centring = {}
    for kind, comp in (("g", res.comp_g), ("cpi", res.comp_cpi), ("fis", res.comp_fis)):
        shift = np.zeros(T) if det else np.median(res.total(kind), axis=0) - targets[kind]
        comp["resid"] = comp["resid"] - shift[None, :]
        centring[kind] = shift
    # CPI lower tail (audit M6): additive channels (Brent-linked import prices, residual) can still push the total below
    # zero although 2000–2025 had no deflation. Soft floor, monotone and median-preserving: deviations D below the
    # target are compressed, π = F + (target − F)·exp(D / (target − F)); booked on the residual so the channels still sum.
    if not det:
        tot = res.total("cpi")
        m = np.maximum(targets["cpi"] - CPI_FLOOR, 0.5)[None, :]
        D = tot - targets["cpi"][None, :]
        soft = np.where(D < 0, CPI_FLOOR + m * np.exp(np.minimum(D, 0) / m), tot)
        res.comp_cpi["resid"] = res.comp_cpi["resid"] + (soft - tot)
    res.events = {
        "R01": brent < B["brent_breakeven_ca0"].to_numpy()[None, :],
        "R02": lend >= p["lendrate_shock_threshold"],
        "R03": deval,
        "R04": ev04,
        "R05": part_own <= p["partner_shock_threshold"],
        "R06": gpr_reg >= np.quantile(gm.groupby(gm.index.year).mean(), p["gpr_quantile"]),
        "R07": (rem_own * f_obs_growth[None, :]) <= p["remit_shock_threshold"],
        "R08": (n1 + n2) > 0,
        "R09": spi <= p["spi_threshold"],
        "R10": ev10,
        "R14": np.repeat(trans_on[:, None], T, axis=1),
        "R15": ev15,
        "R16": ev16,
        "R17": imp_level > pf["imp_thr"],
        "R18": food_level > pf["food_thr"],
    }
    res.meta = {"n": n, "seed": seed, "view": view, "view_az": VIEWS[view], "live_shift": live_shift,
                "targets": targets, "nowcast": ry, "react_inv_mln": react_inv_mln, "obs_share": obs_share, "fx_debt_gdp": debt_deval,
                "fx_params": {"pt": fx.calibration()["pt"], "w0": fx.calibration()["w0"], "L": fx.calibration()["L"]},
                "centring": centring, "layering": layer, "e_fr1_inv": e_fr1, "inv0_real": inv0,
                "imp_level": imp_level, "food_level": food_level,
                "brent_centre": centre, "w_struct": w, "f_rem": f_rem,
                "remit_share": remit_share, "agri_share": agri_share, "sig_core_g": sig_g,
                "sig_core_c": sig_c, "sig_core_f": sig_f, "micro": ms, "gpr_ref": gpr_ref,
                "bootstrap_years": f"{H.index.min()}–{H.index.max()}", "calibration": calib}
    return res


RESID_FLOOR = 0.25      # the core residual keeps at least (0.25 σ_target)² — 6 % of the target variance
CPI_FLOOR = 0.0         # CPI residual lower bound (shifted lognormal): no annual deflation in 2000–2025 (min 1,1 %, n = 26)
CALIB_N0 = 10           # shrinkage of NFR1 band-scale factors toward 1: weight n / (n + N0) (N0 = 10 pseudo-years)
FIS_OBS_SHARE = 0.5     # budget balance is NOT conditioned on Jan–M execution (strong Q4 seasonality): half the σ remains


def running_year() -> dict:
    """Year-to-date nowcast of the running year (v2.1, audit C3) — DSK monthly via the spine feeds (D4/D5) and Brent YTD.
    Returns months observed and the YTD values; empty dict if the running year is not the first forecast year or the
    data are missing (then the v2.0 fallback applies: half of the annual innovation remains)."""
    as_of = pd.Timestamp(config.as_of())
    if YEARS[0] != as_of.year:
        return {}
    out = {"year": YEARS[0]}
    try:
        from . import monitor
        g, gd = monitor.last("dsk_macro", "dsk_gdp_nonoil_ytd_yoy")
        if gd is not None and gd.year == YEARS[0] and np.isfinite(g):
            out.update({"g_ytd": float(g), "g_months": int(gd.month), "g_date": gd.date().isoformat()})
        ytd, d = monitor.last("dsk_cpi", "dsk_cpi_ytd_avg_yoy")
        yoy, _ = monitor.last("dsk_cpi", "dsk_cpi_yoy")
        if not np.isfinite(ytd):
            ytd, d = monitor.last("dsk_macro", "dsk_cpi_ytd_yoy")
            yoy = yoy if np.isfinite(yoy) else ytd
        if d is not None and d.year == YEARS[0] and np.isfinite(ytd):
            out.update({"cpi_ytd": float(ytd), "cpi_last_yoy": float(yoy if np.isfinite(yoy) else ytd),
                        "cpi_months": int(d.month), "cpi_date": d.date().isoformat()})
    except Exception as exc:                             # noqa: BLE001 — never block the simulation on the nowcast
        out["xeta"] = f"{type(exc).__name__}: {exc}"[:160]
    L = spine.live()
    out.update({"brent_ytd": float(L["brent_ytd_avg"]), "brent_months": int(pd.Timestamp(L["brent_last_date"]).month),
                "brent_date": str(L["brent_last_date"])})
    return out


def nowcast_centre(kind: str, view: str, base0: float, ry: dict) -> tuple[float, float]:
    """(centre, observed share) of the running-year outcome. Observed months are fixed at the YTD outturn in BOTH views;
    unobserved months: baseline view — the official forecast rate; live view — the latest observed rate persists."""
    key = {"g": ("g_ytd", "g_months", "g_ytd"), "cpi": ("cpi_ytd", "cpi_months", "cpi_last_yoy")}.get(kind)
    if not ry or key is None or key[0] not in ry:
        return base0, np.nan
    m = ry[key[1]] / 12
    rest = base0 if view == "baseline" else ry[key[2]]
    return m * ry[key[0]] + (1 - m) * rest, m


def fiscal_reaction(brent_path, base_path, M: dict | None = None, coefs: tuple | None = None) -> dict:
    """R01 procyclical public-investment reaction (EXCESS over FR1's own F4 response, SOFAZ-financed, balance-neutral)
    to a deterministic Brent path — the same function the joint simulation uses, exposed for D6 / S-grid / API.
    Returns T arrays: g_lvl (% level non-oil), g (pp growth), cpi (pp), fis (0)."""
    M = M or spine.multipliers()
    ch = factors.channels()
    b0, b1 = coefs or (ch[("inv_brent", "dln_brent")]["coef"], ch[("inv_brent", "dln_brent_l1")]["coef"])
    base_path = np.asarray(base_path, float)
    x = np.log(np.asarray(brent_path, float) / base_path)[None, :]
    x_l1 = np.concatenate([np.zeros((1, 1)), x[:, :-1]], axis=1)
    inv0 = float(spine.micro_fr1_dataset().loc[config.LAST_ACTUAL, "rinv_state"])
    e_fr1 = fr1_embedded_inv_elasticity(M, base_path)
    rs = np.ones(T)
    if YEARS[0] == pd.Timestamp(config.as_of()).year:
        rs[0] = max(0.0, (12 - pd.Timestamp(spine.live()["brent_last_date"]).month) / 12)
    z = inv0 / 1000 * ((b0 - e_fr1) * x * rs[None, :] + b1 * x_l1)
    lv = _convolve(z, _step_response(M["stateinv1bn"], "rgdpnon"))
    c = _convolve(z, _step_response(M["stateinv1bn"], "infl"))
    return {"g_lvl": lv[0], "g": _level_to_growth(lv)[0], "cpi": c[0], "fis": np.zeros(T), "inv_bn": z[0]}


def ext_price_cpi(dimp, b0=None, b1=None) -> np.ndarray:
    """CPI (pp) from a USD import-price inflation deviation path (pp; N×T or T): the single external-price
    pass-through (factors 'cpi_ext'): b0 in the year, b1 the year after."""
    ch = factors.channels()
    b0 = ch[("cpi_ext", "impA")]["coef"] if b0 is None else b0
    b1 = ch[("cpi_ext", "impA_l1")]["coef"] if b1 is None else b1
    d = np.atleast_2d(np.asarray(dimp, float))
    b0, b1 = np.atleast_1d(b0)[:, None], np.atleast_1d(b1)[:, None]
    return b0 * d + b1 * np.concatenate([np.zeros((d.shape[0], 1)), d[:, :-1]], axis=1)


def brent_import_cpi(brent_path, base_path) -> np.ndarray:
    """Brent-linked part of import (incl. food) prices → CPI, attributed to R01 (T array, pp)."""
    a_imp = factors.channels()["_impfood"]["a_imp"]
    dev = np.log(np.asarray(brent_path, float) / np.asarray(base_path, float)) * 100
    dl = np.diff(np.concatenate([[0.0], dev]))
    return ext_price_cpi(a_imp * dl)[0]


def shifted_lognormal(z: np.ndarray, centre: np.ndarray, sd: np.ndarray, floor: float = CPI_FLOOR) -> np.ndarray:
    """Right-skewed residual with lower bound `floor − centre`, median 0 and standard deviation `sd`:
    e = m·(exp(σ_l·z) − 1), m = centre − floor, exp(σ_l²) = (1 + √(1 + 4 (sd/m)²)) / 2."""
    m = np.maximum(np.asarray(centre, float) - floor, 0.5)
    r = np.asarray(sd, float) / m
    s_l = np.sqrt(np.log((1 + np.sqrt(1 + 4 * r ** 2)) / 2))
    return m[None, :] * (np.exp(s_l[None, :] * z) - 1)


def fr1_embedded_inv_elasticity(M: dict, base_b: np.ndarray) -> float:
    """Elasticity of real state investment to Brent that the FR1 structural model already contains:
    rinv_state response (%) to the +10 USD step ÷ the step in log points, averaged over the horizon."""
    r = M["brent10"]["rinv_state"].reindex(YEARS).to_numpy(dtype=float) / 100
    if np.isnan(r).all():
        return 0.0
    return float(np.nanmean(r / np.log((base_b + 10) / base_b)))


# economically required signs of the standing stress set (first stressed year, deviation from reference)
STRESS_SIGNS = {"S1": {"g": -1, "fis": -1, "cpi": -1}, "S2": {"g": -1, "fis": -1},
                "S3": {"g": -1, "fis": -1, "cpi": +1}, "S4": {"g": -1}, "S5": {"g": -1, "fis": -1},
                "S6": {"g": -1, "fis": -1}, "S7": {"g": -1}, "S8": {"g": -1, "fis": -1}}
_STRESS_VAR = {"qeyri-neft": "g", "inflyasiya": "cpi", "büdcə": "fis"}


def check_stress_signs(stress: pd.DataFrame, year: int | None = None, tol: float = 1e-6) -> pd.DataFrame:
    """Sign assertion for FR3_stress_scenarios (the v1 S1 'Brent 45 improves the budget' defect).
    Returns the violations (empty = all economically sensible); run_all raises on any violation."""
    if stress is None or not len(stress):
        return pd.DataFrame(columns=["ssenari", "gosterici", "il", "sapma", "gozlenilen_isare"])
    yr = year or (config.FORECAST_YEARS[1] if len(config.FORECAST_YEARS) > 1 else config.FORECAST_YEARS[0])
    bad = []
    for r in stress[stress["il"] == yr].itertuples():
        kind = next((v for k, v in _STRESS_VAR.items() if str(r.gosterici).startswith(k)), None)
        sgn = STRESS_SIGNS.get(r.ssenari, {}).get(kind)
        if sgn is not None and sgn * r.sapma < -tol:
            bad.append({"ssenari": r.ssenari, "gosterici": r.gosterici, "il": yr, "sapma": r.sapma,
                        "gozlenilen_isare": "+" if sgn > 0 else "−"})
    return pd.DataFrame(bad, columns=["ssenari", "gosterici", "il", "sapma", "gozlenilen_isare"])


def fiscal_sigma() -> np.ndarray:
    """σ of the budget balance (% GDP) in the micro FR1 core's own stochastic simulation."""
    d = spine._csv(config.MICRO_FILES["fr1_draws"])
    s = (d["balance_n"] / d["gdp_n"] * 100).groupby(d["year"]).std()
    return s.reindex(YEARS).to_numpy()


def calibration_factors(raw: bool = False) -> dict:
    """Band-scale factors set by the quarterly NFR1 backtest (output/NFR1_calibration.csv); 1.0 until a backtest has
    recalibrated them. v2.1 (audit M6): small-sample factors are SHRUNK toward 1 with weight n / (n + CALIB_N0)
    (non-oil n = 9, fiscal n = 14, Brent n = 30); `raw=True` returns the backtest values. calibration_report() re-tests
    the 80 % coverage after scaling and gives bootstrap intervals."""
    f = config.OUTPUT / "NFR1_calibration.csv"
    out = {"nonoil": 1.0, "cpi": 1.0, "brent": 1.0, "fis": 1.0}
    if f.exists():
        c = pd.read_csv(f)
        for r in c.itertuples():
            if r.hedef in out:
                n = float(getattr(r, "n", 0) or 0)
                out[r.hedef] = float(r.miqyas) if raw else _shrunk(r.hedef, float(r.miqyas), n)
    return out


def _shrunk(h: str, raw: float, n: float) -> float:
    """Shrink toward 1 (weight n/(n+N0)), then re-test: if the 80 % coverage on the same out-of-sample points leaves
    the tolerance band, move back toward the raw factor until it is inside (closest-to-shrunk factor that passes)."""
    f_s = 1 + n / (n + CALIB_N0) * (raw - 1)
    try:
        z = _calib_z(h)
    except Exception:                                 # noqa: BLE001
        z = np.array([])
    if len(z) < 3 or abs(raw - 1) < 1e-12:
        return float(f_s)
    p = factors.params()
    lo, hi = p["coverage80_lo"], p["coverage80_hi"]
    cov = lambda x: float(np.mean(z <= stats.norm.ppf(0.9) * x))  # noqa: E731
    if lo <= cov(f_s) <= hi:
        return float(f_s)
    for x in np.linspace(f_s, raw, 401):
        if lo <= cov(x) <= hi:
            return float(x)
    return float(raw)


def _calib_z(hedef: str):
    """|z| of the out-of-sample PITs behind each factor (or RW errors / σ for the budget balance)."""
    o = config.OUTPUT
    if hedef in ("nonoil", "cpi") and (o / "NFR1_macro_fan_pit.csv").exists():
        d = pd.read_csv(o / "NFR1_macro_fan_pit.csv")
        pit = d[d["hedef"] == {"nonoil": "nonoil_realg", "cpi": "cpi_infl"}[hedef]]["pit"].to_numpy()
        return np.abs(stats.norm.ppf(np.clip(pit, 1e-6, 1 - 1e-6)))
    if hedef == "brent" and (o / "NFR1_brent_density_pit.csv").exists():
        pit = pd.read_csv(o / "NFR1_brent_density_pit.csv")["pit"].to_numpy()
        return np.abs(stats.norm.ppf(np.clip(pit, 1e-6, 1 - 1e-6)))
    if hedef == "fis":
        from . import backtest
        mi = spine.micro_fr1_dataset()
        b = (mi["balance_n"] / mi["gdp_n"] * 100).loc[2010:config.LAST_ACTUAL].dropna()
        err = (b.shift(-2) - b).dropna().to_numpy()
        s_fr1 = backtest.fiscal_fan_calibration()["sigma_fr1"]
        return np.abs(err) / s_fr1
    return np.array([])


def calibration_report(n_boot: int = 2000, seed: int = 5) -> pd.DataFrame:
    """NFR1_calibration_shrinkage.csv: raw factor (backtest), n, bootstrap 90 % interval of the raw factor, shrinkage
    weight, shrunk factor, and the 80 % coverage re-tested on the same out-of-sample points BEFORE scaling, after the
    RAW and after the SHRUNK factor (target band from hedler: coverage80_lo–hi)."""
    raw, shr = calibration_factors(raw=True), calibration_factors()
    p = factors.params()
    z90 = stats.norm.ppf(0.9)
    rng = np.random.default_rng(seed)
    c = pd.read_csv(config.OUTPUT / "NFR1_calibration.csv") if (config.OUTPUT / "NFR1_calibration.csv").exists() else None
    rows = []
    for h in ("nonoil", "cpi", "brent", "fis"):
        z = _calib_z(h)
        n = int(c[c["hedef"] == h]["n"].iloc[0]) if c is not None and (c["hedef"] == h).any() else len(z)
        cov = lambda f: float(np.mean(z <= z90 * f)) if len(z) else np.nan  # noqa: E731
        if len(z) >= 3:
            est = (lambda v: np.clip(np.sqrt(np.mean(v ** 2)), 0.25, 1.0)) if h == "fis" else \
                (lambda v: np.clip(np.quantile(v, 0.8) / z90, 0.25, 2.0))
            bs = [est(rng.choice(z, len(z))) for _ in range(n_boot)]
            lo, hi = np.quantile(bs, [0.05, 0.95])
        else:
            lo = hi = np.nan
        rows.append({"hedef": h, "n": n, "n_test": len(z), "miqyas_xam": raw[h], "xam_90_asagi": lo, "xam_90_yuxari": hi,
                     "cekI_w": n / (n + CALIB_N0), "miqyas_buzulmus": 1 + n / (n + CALIB_N0) * (raw[h] - 1),
                     "ehate80_buzulmus": cov(1 + n / (n + CALIB_N0) * (raw[h] - 1)), "miqyas_istifade": shr[h], "ehate80_evvel": cov(1.0),
                     "ehate80_xam": cov(raw[h]), "ehate80_istifade": cov(shr[h]),
                     "tolerans": f"[{p['coverage80_lo']:.2f}; {p['coverage80_hi']:.2f}]",
                     "qeyd": f"büzülmə: 1 + n/(n+{CALIB_N0})·(xam − 1); örtük eyni nümunədən kənar nöqtələrdə yenidən "
                             "yoxlanılır — tolerans xaricindədirsə, tolerans daxilində ən yaxın əmsala qədər xam əmsala tərəf"})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- summaries
QS = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
BASE_NOTE = {False: "rəsmi proqnoz", True: "rəsmi proqnoz (YTD məlumatından əvvəl) — zolaq il-əvvəlindən faktiki ilə "
             "şərtləndirilib, 'baza' zolaqdan kənar ola bilər; mərkəz = 'merkez'"}


def distribution_table(res: SimResult) -> pd.DataFrame:
    rows = []
    for kind, name, unit in (("g", "Qeyri-neft ÜDM-in real artımı", "%"),
                             ("cpi", "İnflyasiya (illik orta)", "%"),
                             ("fis", "Büdcə balansı / ÜDM", "%")):
        tot = res.total(kind)
        for j, y in enumerate(res.years):
            q = np.quantile(tot[:, j], QS)
            tail = tot[:, j][tot[:, j] <= q[1]] if kind != "cpi" else tot[:, j][tot[:, j] >= q[5]]
            obs = res.meta.get("obs_share", {}).get(kind, np.nan) if j == 0 else np.nan
            rows.append({"baxis": res.meta.get("view", "baseline"), "gosterici": kind, "ad": name, "vahid": unit,
                         "il": y, "baza": res.base[kind][j],
                         **{f"p{int(x*100):02d}": v for x, v in zip(QS, q)},
                         "orta": tot[:, j].mean(), "ES10": tail.mean(),
                         "merkez": float(res.meta.get("targets", {}).get(kind, res.base[kind])[j]),
                         "musahide_payi": obs, "baza_izah": BASE_NOTE[np.isfinite(obs)]})
    for j, y in enumerate(res.years):
        q = np.quantile(res.brent[:, j], QS)
        fr = res.meta.get("f_rem", np.ones(len(res.years)))[j]
        rows.append({"baxis": res.meta.get("view", "baseline"), "gosterici": "brent", "ad": "Brent neft qiyməti",
                     "vahid": "USD/barel", "il": y,
                     "baza": res.brent_base[j], **{f"p{int(x*100):02d}": v for x, v in zip(QS, q)},
                     "orta": res.brent[:, j].mean(), "ES10": res.brent[:, j][res.brent[:, j] <= q[1]].mean(),
                     "merkez": float(res.meta["brent_centre"][j]), "musahide_payi": 1 - fr if fr < 1 else np.nan,
                     "baza_izah": BASE_NOTE[bool(fr < 1)]})
    return pd.DataFrame(rows)


def contributions(res: SimResult, kind: str = "g") -> pd.DataFrame:
    """Variance shares and lower-tail (Euler / expected-shortfall) contributions per channel
    in the score year. For inflation the upper tail is the adverse one."""
    j = res.col(res.score_year)
    comp = {"g": res.comp_g, "cpi": res.comp_cpi, "fis": res.comp_fis}[kind]
    tot = res.total(kind)[:, j]
    v = tot.var(ddof=1)                     # same convention as np.cov below, so shares sum to 1
    if kind == "cpi":
        tail = tot >= np.quantile(tot, 0.90)
    else:
        tail = tot <= np.quantile(tot, 0.10)
    rows = []
    for k, c in comp.items():
        cj = c[:, j]
        rows.append({"kanal": k, "ad": CHANNEL_AZ[k], "risk_id": CHANNEL_RISK.get(k, ""),
                     "orta": cj.mean(), "dispersiya_payi": float(np.cov(cj, tot)[0, 1] / v),
                     "quyruq_tohfesi": float(cj[tail].mean()),
                     "quyruq_tohfesi_merkezlesmis": float(cj[tail].mean() - cj.mean())})
    out = pd.DataFrame(rows)
    out["gosterici"] = kind
    out["il"] = res.score_year
    return out.sort_values("quyruq_tohfesi_merkezlesmis", ascending=(kind != "cpi")).reset_index(drop=True)


# ---------------------------------------------------------------- Growth-at-Risk cross-check
GAR_X = ["dln_brent", "ln_gpr_reg"]
GAR_Q = [0.10, 0.25, 0.50, 0.75, 0.90]


def _gar_frame() -> pd.DataFrame:
    P = factors.channels()["_panel"].copy()
    P["ln_gpr_reg"] = np.log(P["gpr_reg"])
    d = pd.DataFrame({"y": P["nonoil_g"].shift(-1), "dln_brent": P["dln_brent"],
                      "ln_gpr_reg": P["ln_gpr_reg"]})
    return d


def gar_fit(d: pd.DataFrame):
    import statsmodels.formula.api as smf
    d = d.dropna()
    return {q: smf.quantreg("y ~ dln_brent + ln_gpr_reg", d).fit(q=q, max_iter=5000) for q in GAR_Q}


def gar_quantiles(fits: dict, x: dict) -> np.ndarray:
    xq = pd.DataFrame([x])
    q = np.array([float(fits[k].predict(xq).iloc[0]) for k in GAR_Q])
    return np.sort(q)                                 # monotone rearrangement (Chernozhukov et al.)


def skew_fit(qv: np.ndarray):
    """Skew-normal fitted to the five predicted quantiles — gives p5 and a full density."""
    from scipy.optimize import minimize
    def loss(th):
        a, loc, sc = th
        if sc <= 0:
            return 1e9
        return float(np.sum((stats.skewnorm.ppf(GAR_Q, a, loc, sc) - qv) ** 2))
    best = min((minimize(loss, [a0, qv[2], max((qv[4] - qv[0]) / 2.56, 0.3)], method="Nelder-Mead")
                for a0 in (-3, -1, 0, 1)), key=lambda r: r.fun)
    return best.x


def gar_now() -> dict:
    """Quantile-regression Growth-at-Risk for the score year, conditioned on today's data."""
    d = _gar_frame()
    fits = gar_fit(d)
    L = spine.live()
    P = spine.annual_panel()
    gm = factors.regional_gpr_monthly()
    sy = config.score_year()
    cur_year = sy - 1
    brent_cur = L["brent_ytd_avg"] if cur_year == config.as_of().year else float(P.loc[cur_year, "brent"])
    x = {"dln_brent": float(np.log(brent_cur / P.loc[cur_year - 1, "brent"]) * 100),
         "ln_gpr_reg": float(np.log(gm[gm.index.year == cur_year].mean()))}
    qv = gar_quantiles(fits, x)
    a, loc, sc = skew_fit(qv)
    coef = pd.DataFrame({q: f.params for q, f in fits.items()}).T
    pv = pd.DataFrame({q: f.pvalues for q, f in fits.items()}).T
    return {"x": x, "q": dict(zip(GAR_Q, qv)), "p05": float(stats.skewnorm.ppf(0.05, a, loc, sc)),
            "skew": (a, loc, sc), "coef": coef, "pvalues": pv, "n": int(d.dropna().shape[0]),
            "year": sy}
