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
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

from . import config, factors, spine

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
}
CHANNEL_RISK = {"brent": "R01", "fiscal_react": "R01", "rate": "R02", "deval": "R03", "bank": "R04", "partner": "R05",
                "gpr": "R06", "remit": "R07", "quake": "R08", "drought": "R09", "flood": "R10",
                "transition": "R14", "manuf": "R15", "compet": "R16"}


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
        overrides: dict | None = None) -> SimResult:
    """Joint simulation. `overrides` lets FR3 stress scenarios and tests fix factor paths."""
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

    # ---------------- partial observation of the running year
    as_of = pd.Timestamp(config.as_of())
    f_rem = np.ones(T)
    if YEARS[0] == as_of.year:
        last_obs_month = pd.Timestamp(L["brent_last_date"]).month
        f_rem[0] = max(0.0, (12 - last_obs_month) / 12)
    f_obs_growth = np.ones(T)
    if YEARS[0] == as_of.year:
        f_obs_growth[0] = 0.5          # three quarters observed: half the annual innovation remains

    # ---------------- Brent path: live-conditioned centre + resampled innovations
    w = ch[("brent_combo", "w_struct")]
    base_b = B["brent_usd"].to_numpy()
    lb_last = np.log(L["brent_last_month"])
    centre = np.exp(w * np.log(base_b) + (1 - w) * lb_last)
    if YEARS[0] == as_of.year:
        centre[0] = (1 - f_rem[0]) * L["brent_ytd_avg"] + f_rem[0] * centre[0]
    gpr_part = b_gpr_brent[:, None] * E["gpr"]
    own = E["brent"] - gpr_part
    scale = f_rem[None, :]
    cum_own = np.cumsum(own * scale, axis=1)
    cum_gpr = np.cumsum(gpr_part * scale, axis=1)
    # energy-transition overlay (R14): Bernoulli on the whole path, -x %/yr drift from year 2
    p14 = float(reg.at["R14", "ekspert_ehtimal"]) if "R14" in reg.index else 0.0
    trans_on = rng.random(n) < p14
    det = bool(ov.get("deterministic"))               # stress mode: only the declared shocks act
    if det:
        trans_on[:] = False
    drift = np.array([0.0] + [-0.03 * k for k in range(1, T)])
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
    lv_quake = -p["eq_output_loss"] * dmg * gdp_over_nonoil          # transitory, % of non-oil GDP
    fis_quake = -p["eq_fiscal_share"] * dmg                          # % GDP

    # ---------------- conditional devaluation (one per path at most, permanent level effect)
    hist_b = spine.annual_panel()["brent"].loc[config.LAST_ACTUAL - 2:config.LAST_ACTUAL].to_numpy()
    full = np.concatenate([np.tile(hist_b, (n, 1)), brent], axis=1)
    deval = np.zeros((n, T), dtype=bool)
    happened = np.zeros(n, dtype=bool)
    u = rng.random((n, T))
    for t in range(T):
        prev3 = full[:, t:t + 3].mean(axis=1)
        trig = (full[:, t + 3] / prev3 - 1) * 100 <= p["devaluation_brent_drop"]
        hit = trig & (u[:, t] < dv["p_dev"]) & ~happened
        if "deval_year" in ov:
            hit = np.full(n, YEARS[t] == ov["deval_year"])
        elif det:
            hit = np.zeros(n, dtype=bool)
        deval[:, t] = hit
        happened |= hit
    size = np.log1p(p["devaluation_size"])
    dev_on = np.cumsum(deval, axis=1) > 0
    lv_deval = dev_on * dv["nonoil_residual"] * size / dv["dln_fx_2014_2017"]
    cpi_deval = deval * dv["cpi_passthrough"] * size

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
    # procyclical fiscal reaction (R01): real public investment follows Brent with the historical
    # distributed-lag elasticity; a level shift of x mln AZN enters the FR1 step response per 1 bn.
    inv0 = float(spine.micro_fr1_dataset().loc[config.LAST_ACTUAL, "rinv_state"])
    react_scale = np.ones(T)
    if YEARS[0] == as_of.year:
        react_scale[0] = f_rem[0]                      # the running year's budget is largely set
    def reaction(x):                                   # x: N×T log deviation of Brent from baseline
        x_l1 = np.concatenate([np.zeros((x.shape[0], 1)), x[:, :-1]], axis=1)
        return inv0 / 1000 * (b_inv0[:, None] * x * react_scale[None, :] + b_inv1[:, None] * x_l1)
    x_own = np.log(centre / base_b)[None, :] + cum_own
    react_on = 0.0 if ov.get("fiscal_react_off") else 1.0
    # T09 (no procyclical cut): public investment is never cut below its baseline path
    floor = (lambda z: np.maximum(z, 0.0)) if ov.get("fiscal_react_floor") else (lambda z: z)
    lv_fr_own, c_fr_own, f_fr_own = via(M["stateinv1bn"], react_on * floor(reaction(x_own)))
    lv_fr_gpr, c_fr_gpr, f_fr_gpr = via(M["stateinv1bn"], react_on * floor(reaction(cum_gpr)))
    lv_fr_tr, c_fr_tr, f_fr_tr = via(M["stateinv1bn"], react_on * floor(reaction(cum_tr)))

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
    res.comp_cpi = {"brent": c_b_own, "fiscal_react": c_fr_own, "gpr": c_b_gpr + c_x_gpr + c_fr_gpr,
                    "transition": c_b_tr + c_fr_tr, "partner": c_x_own,
                    "rate": c_r, "deval": cpi_deval, "compet": cpi_compet, "bank": c04, "flood": c10}
    res.comp_fis = {"brent": f_b_own, "fiscal_react": f_fr_own, "gpr": f_b_gpr + f_x_gpr + f_fr_gpr,
                    "transition": f_b_tr + f_fr_tr, "partner": f_x_own,
                    "rate": f_r, "quake": fis_quake, "bank": f04, "flood": f10}

    # ---------------- core residuals: fill the macro fan, never exceed it
    t5 = stats.t(df=5)
    t5_sd = np.sqrt(5 / 3)
    calib = calibration_factors()
    def add_resid(kind, sigma_core, comp):
        fac = np.stack([c for c in comp.values()]).sum(axis=0)
        v_fac = fac.var(axis=0)
        s2 = np.maximum(sigma_core ** 2 - v_fac, (0.5 * sigma_core) ** 2)
        eps = t5.rvs(size=(n, T), random_state=rng) / t5_sd * np.sqrt(s2)[None, :]
        return eps
    sig_g = np.array([spine.baseline_band_sigma("nonoil_realg", y) for y in YEARS]) * f_obs_growth * calib["nonoil"]
    sig_c = np.array([spine.baseline_band_sigma("cpi_infl", y) for y in YEARS]) * f_obs_growth * calib["cpi"]
    sig_f = fiscal_sigma() * f_obs_growth
    res.comp_g["resid"] = add_resid("g", sig_g, res.comp_g) * (not det)
    res.comp_cpi["resid"] = add_resid("cpi", sig_c, res.comp_cpi) * (not det)
    res.comp_fis["resid"] = add_resid("fis", sig_f, res.comp_fis) * (not det)

    res.base = {"g": B["nonoil_realg"].to_numpy(), "cpi": B["cpi_infl"].to_numpy(),
                "fis": B["fr1_balance_pct"].to_numpy()}
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
    }
    res.meta = {"n": n, "seed": seed, "brent_centre": centre, "w_struct": w, "f_rem": f_rem,
                "remit_share": remit_share, "agri_share": agri_share, "sig_core_g": sig_g,
                "sig_core_c": sig_c, "sig_core_f": sig_f, "micro": ms, "gpr_ref": gpr_ref,
                "bootstrap_years": f"{H.index.min()}–{H.index.max()}", "calibration": calib}
    return res


def fiscal_sigma() -> np.ndarray:
    """σ of the budget balance (% GDP) in the micro FR1 core's own stochastic simulation."""
    d = spine._csv(config.MICRO_FILES["fr1_draws"])
    s = (d["balance_n"] / d["gdp_n"] * 100).groupby(d["year"]).std()
    return s.reindex(YEARS).to_numpy()


def calibration_factors() -> dict:
    """Band-scale factors set by the quarterly NFR1 backtest (output/NFR1_calibration.csv);
    1.0 until a backtest has recalibrated them."""
    f = config.OUTPUT / "NFR1_calibration.csv"
    out = {"nonoil": 1.0, "cpi": 1.0, "brent": 1.0}
    if f.exists():
        c = pd.read_csv(f)
        for r in c.itertuples():
            if r.hedef in out:
                out[r.hedef] = float(r.miqyas)
    return out


# ---------------------------------------------------------------- summaries
QS = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]


def distribution_table(res: SimResult) -> pd.DataFrame:
    rows = []
    for kind, name, unit in (("g", "Qeyri-neft ÜDM-in real artımı", "%"),
                             ("cpi", "İnflyasiya (illik orta)", "%"),
                             ("fis", "Büdcə balansı / ÜDM", "%")):
        tot = res.total(kind)
        for j, y in enumerate(res.years):
            q = np.quantile(tot[:, j], QS)
            tail = tot[:, j][tot[:, j] <= q[1]] if kind != "cpi" else tot[:, j][tot[:, j] >= q[5]]
            rows.append({"gosterici": kind, "ad": name, "vahid": unit, "il": y, "baza": res.base[kind][j],
                         **{f"p{int(x*100):02d}": v for x, v in zip(QS, q)},
                         "orta": tot[:, j].mean(), "ES10": tail.mean()})
    for j, y in enumerate(res.years):
        q = np.quantile(res.brent[:, j], QS)
        rows.append({"gosterici": "brent", "ad": "Brent neft qiyməti", "vahid": "USD/barel", "il": y,
                     "baza": res.brent_base[j], **{f"p{int(x*100):02d}": v for x, v in zip(QS, q)},
                     "orta": res.brent[:, j].mean(), "ES10": res.brent[:, j][res.brent[:, j] <= q[1]].mean()})
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
