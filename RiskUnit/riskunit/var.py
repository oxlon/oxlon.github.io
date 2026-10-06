"""Value-at-Risk / Expected Shortfall of the sovereign balance sheet (RiskUnit v2, U4).

Portfolios (mln USD; AZN = USD x 1.70 under the peg):
  sofaz   — SOFAZ investment portfolio by asset class (fixed income on UST key rates, equities,
            gold, real estate) and by currency (EUR, GBP, CNY, JPY, other vs USD);
  net_fx  — sovereign net foreign-currency position: SOFAZ + CBAR reserves − external public debt
            − external state-guaranteed debt (by currency);
  oil_rev — budget oil revenue at risk (mln AZN) for the score year: FR1 baseline revenue as a
            function of Brent x volume x FX (1-year horizon only).
Methods: (a) historical simulation, (b) age-weighted HS with a FIXED decay (λ = 0,995 daily,
0,98 monthly; Boudoukh-Richardson-Whitelaw 1998 — not estimated), (c) Monte Carlo with empirical
(bootstrap) marginals and a Student-t copula whose ν is fitted by maximum likelihood, (d) EVT
peaks-over-threshold (GPD above the 90 % loss quantile), (e) Cornish-Fisher. Horizons 1 day,
1 month, 1 year; square-root-of-time rows are labelled approximations only. Portfolio P&L is the
static current exposure applied to historical factor moves (hypothetical P&L). No GARCH or any
estimated volatility dynamics anywhere.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import config, feeds_market as fm, parametrler

CONF = (0.95, 0.99)
LAMBDA = {"d": 0.995, "m": 0.98}          # fixed, documented decay (not estimated)
HS_WINDOW_D = 750                          # ≈ 3 years of business days (gold daily history limit)
BT_WINDOW_D = 250                          # rolling window in the daily backtest (Basel minimum: 1 year)
BT_WINDOW_M = 120                          # rolling window in the monthly backtest
EVT_Q = 0.90                               # POT threshold: 90th percentile of losses
N_MC = 50000
WORKING = np.sqrt(1.5)                     # Working (1960): Δ of monthly averages has 2/3 of the variance
RE_BETA = parametrler.get("var_re_beta", 0.5)   # real-estate / infrastructure beta to equities (input/parametrler.csv)
CS_SHARE_DEFAULT = parametrler.get("var_credit_spread_share", 0.376)   # A + BBB + NIG share of SOFAZ fixed income
SEED = config.SEED
PEG = 1.70
XDR_BASKET = {"USD": 0.4338, "EUR": 0.2931, "CNY": 0.1228, "JPY": 0.0759, "GBP": 0.0744}

PORTF_AZ = {"sofaz": "ARDNF investisiya portfeli", "net_fx": "Suveren xalis valyuta mövqeyi",
            "oil_rev": "Büdcənin neft gəlirləri (risk altında)"}
METHOD_AZ = {"hs": "Tarixi simulyasiya", "awhs": "Yaşa görə çəkili tarixi simulyasiya (λ sabit)",
             "mc_tcop": "Monte Karlo: empirik marjinallar + Student-t kopula", "evt": "EVT: GPD quyruğu (POT)",
             "cf": "Kornish-Fişer parametrik", "sqrt_time": "Kök-zaman təxmini (yalnız müqayisə)",
             "sim_joint": "RU birgə Monte Karlo (simulate.py)"}
HORIZON_AZ = {"1g": "1 gün", "1a": "1 ay", "1il": "1 il"}
FACTOR_AZ = {"gold": "Qızıl", "eq": "Səhmlər", "re": "Daşınmaz əmlak (səhm betası)", "ust2": "UST 2 il",
             "ust5": "UST 5 il", "ust10": "UST 10 il", "fx_eur": "EUR/USD", "fx_gbp": "GBP/USD",
             "fx_cny": "CNY/USD", "fx_jpy": "JPY/USD", "fx_oth": "Digər valyutalar (geniş dollar)",
             "cs": "Kredit spredi (Moody's Baa − UST 10 il)"}
CLASS_OF = {"gold": "Qızıl", "eq": "Səhmlər", "re": "Daşınmaz əmlak", "ust2": "Sabit gəlirli",
            "ust5": "Sabit gəlirli", "ust10": "Sabit gəlirli", "fx_eur": "Valyuta", "fx_gbp": "Valyuta",
            "fx_cny": "Valyuta", "fx_jpy": "Valyuta", "fx_oth": "Valyuta", "cs": "Sabit gəlirli"}
RATE_FACTORS = ("ust2", "ust5", "ust10")


# ---------------------------------------------------------------- factor moves
def factor_moves(levels: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Daily ('d') or monthly ('m') factor moves from level panels: log returns of USD prices
    (FX expressed as the USD value of one unit of the currency) and yield changes in pp."""
    L = levels
    eq = L["spx"] if freq == "d" else L.get("eq_oecd_us")
    gold = L["gold"].shift(-1) if freq == "d" else L["gold"]   # CBAR XAU(d) is set on d-1
    out = pd.DataFrame({
        "gold": np.log(gold).diff(), "eq": np.log(eq).diff(),
        "fx_eur": np.log(L["eurusd"]).diff(), "fx_gbp": np.log(L["gbpusd"]).diff(),
        "fx_cny": -np.log(L["usdcny"]).diff(), "fx_jpy": -np.log(L["usdjpy"]).diff(),
        "fx_oth": -np.log(L["usd_broad"]).diff(),
        "ust2": L["ust2"].diff(), "ust5": L["ust5"].diff(), "ust10": L["ust10"].diff(),
        "brent": np.log(L["brent"]).diff(),
    })
    if "baa_spread" in L and L["baa_spread"].notna().sum() > 24:   # credit-spread factor (FRED BAA10Y), pp change
        out["cs"] = L["baa_spread"].diff()
    out["re"] = RE_BETA * out["eq"]
    if freq == "d":                                            # drop stale (holiday) rows
        out = out[(out[["eq", "fx_eur", "ust10"]] != 0).any(axis=1)]
    return out.dropna(subset=[c for c in out.columns if c != "cs"])


def working_corrected(m: pd.DataFrame) -> pd.DataFrame:
    """Monthly-average moves rescaled to month-end-equivalent dispersion (labelled approximation)."""
    mu = m.mean()
    return mu + (m - mu) * WORKING


def overlapping(m: pd.DataFrame, k: int = 12) -> pd.DataFrame:
    """Overlapping k-month sums of monthly moves (log returns and pp changes are additive)."""
    return m.rolling(k).sum().dropna()


# ---------------------------------------------------------------- exposures
def _ex(V1: pd.DataFrame, kod: str, col: str = "mln_usd") -> float:
    r = V1.loc[V1["kod"] == kod, col]
    return float(r.iloc[0]) if len(r) and pd.notna(r.iloc[0]) else 0.0


def portfolios(V1: pd.DataFrame | None = None) -> dict:
    """Exposure vectors {portfolio: {factor: (exposure mln USD, kind)}}; kind 'log' → P&L =
    E·(e^r − 1); kind 'rate' → P&L = −E·Δy/100 with E = value × key-rate duration."""
    from .exposures import fi_key_rate_durations
    V1 = V1 if V1 is not None else pd.read_csv(config.OUTPUT / "V1_exposures.csv")
    P = sum(_ex(V1, f"sofaz_class_{k}") for k in ("fixed_income", "equities", "gold", "real_estate"))
    fi = _ex(V1, "sofaz_class_fixed_income")
    mat = {k: _ex(V1, f"sofaz_fi_mat_{k}", "deyer") for k in ("0-1", "1-3", "3-5", "5+")}
    krd = fi_key_rate_durations(mat)
    sof = {"gold": (_ex(V1, "sofaz_class_gold"), "log"), "eq": (_ex(V1, "sofaz_class_equities"), "log"),
           "re": (_ex(V1, "sofaz_class_real_estate"), "log")}
    sof.update({k: (fi * krd[k], "rate") for k in RATE_FACTORS})
    rat = {k: _ex(V1, f"sofaz_fi_rating_{k}", "deyer") for k in ("A", "BBB", "NIG")}
    cs_share = sum(rat.values()) / 100 if sum(rat.values()) > 0 else CS_SHARE_DEFAULT
    sof["cs"] = (fi * cs_share * sum(krd.values()), "rate")     # spread duration ≈ modified duration (credit part)
    for c, f in (("EUR", "fx_eur"), ("GBP", "fx_gbp"), ("CNY", "fx_cny"), ("JPY", "fx_jpy"), ("OTHER", "fx_oth")):
        sof[f] = (_ex(V1, f"sofaz_ccy_{c}"), "log")
    net = {k: list(v) for k, v in sof.items()}
    ext = {c: _ex(V1, f"debt_ext_ccy_{c}") for c in ("EUR", "XDR", "JPY", "OTHER")}
    g_ext = _ex(V1, "cl_guaranteed_ext")
    gmix = {c: _ex(V1, f"cl_guar_ccy_{c}", "deyer") for c in ("USD", "EUR", "JPY", "OTHER")}
    gsum = sum(gmix.values()) or 1.0
    liab = {"EUR": ext["EUR"] + ext["XDR"] * XDR_BASKET["EUR"] + g_ext * gmix["EUR"] / gsum,
            "JPY": ext["JPY"] + ext["XDR"] * XDR_BASKET["JPY"] + g_ext * gmix["JPY"] / gsum,
            "CNY": ext["XDR"] * XDR_BASKET["CNY"], "GBP": ext["XDR"] * XDR_BASKET["GBP"],
            "OTHER": ext["OTHER"] + g_ext * gmix["OTHER"] / gsum}
    for c, f in (("EUR", "fx_eur"), ("GBP", "fx_gbp"), ("CNY", "fx_cny"), ("JPY", "fx_jpy"), ("OTHER", "fx_oth")):
        net[f][0] -= liab[c]
    value_net = (P + _ex(V1, "cbar_reserves") - _ex(V1, "debt_external") - g_ext)
    return {"sofaz": {"lines": sof, "value": P},
            "net_fx": {"lines": {k: tuple(v) for k, v in net.items()}, "value": value_net,
                       "liab_fx": liab}}


def pnl_components(moves: pd.DataFrame, lines: dict) -> pd.DataFrame:
    """Per-factor P&L (mln USD) of the current exposures under each historical / simulated move."""
    out = {}
    for f, (E, kind) in lines.items():
        if f not in moves:
            continue
        x = moves[f].to_numpy(float)
        out[f] = -E * x / 100.0 if kind == "rate" else E * np.expm1(x)
    return pd.DataFrame(out, index=moves.index)


# ---------------------------------------------------------------- risk measures on a P&L sample
def hs(pnl: np.ndarray, q: float) -> tuple[float, float]:
    x = np.asarray(pnl, float)
    v = -np.quantile(x, 1 - q)
    tail = x[x <= -v]
    return float(v), float(-tail.mean()) if len(tail) else float(v)


def age_weights(n: int, lam: float) -> np.ndarray:
    w = lam ** np.arange(n - 1, -1, -1, dtype=float)       # newest observation has weight 1
    return w / w.sum()


def awhs(pnl: np.ndarray, q: float, lam: float) -> tuple[float, float]:
    x = np.asarray(pnl, float)
    w = age_weights(len(x), lam)
    o = np.argsort(x)
    cw = np.cumsum(w[o])
    k = int(np.searchsorted(cw, 1 - q))
    v = -x[o][min(k, len(x) - 1)]
    tw = w[o][:k + 1]
    es = -np.sum(x[o][:k + 1] * tw) / tw.sum()
    return float(v), float(es)


def cf_quantile(p, mu, sd, S, K):
    z = stats.norm.ppf(p)
    zc = z + (z ** 2 - 1) * S / 6 + (z ** 3 - 3 * z) * K / 24 - (2 * z ** 3 - 5 * z) * S ** 2 / 36
    return mu + sd * zc


def cornish_fisher(pnl: np.ndarray, q: float) -> tuple[float, float]:
    x = np.asarray(pnl, float)
    mu, sd = x.mean(), x.std(ddof=1)
    S, K = stats.skew(x), stats.kurtosis(x)                  # K = excess kurtosis
    v = -cf_quantile(1 - q, mu, sd, S, K)
    grid = (np.arange(2000) + 0.5) / 2000 * (1 - q)          # ES = mean of the CF quantile function
    es = -np.mean(cf_quantile(grid, mu, sd, S, K))
    return float(v), float(es)


def gpd_fit(loss: np.ndarray, q_u: float = EVT_Q) -> dict:
    L = np.asarray(loss, float)
    u = np.quantile(L, q_u)
    ex = L[L > u] - u
    if len(ex) < 15:
        raise ValueError("EVT: həddən yuxarı müşahidə azdır")
    xi, _, beta = stats.genpareto.fit(ex, floc=0)
    return {"u": float(u), "xi": float(xi), "beta": float(beta), "n_u": int(len(ex)), "n": int(len(L))}


def evt(pnl: np.ndarray, q: float, fit: dict | None = None) -> tuple[float, float, dict]:
    f = fit or gpd_fit(-np.asarray(pnl, float))
    p_u = f["n_u"] / f["n"]
    xi, b, u = f["xi"], f["beta"], f["u"]
    if abs(xi) < 1e-6:
        v = u + b * np.log(p_u / (1 - q))
    else:
        v = u + b / xi * ((p_u / (1 - q)) ** xi - 1)
    es = (v + b - xi * u) / (1 - xi) if xi < 1 else np.inf
    return float(v), float(es), f


# ---------------------------------------------------------------- Student-t copula Monte Carlo
def _nearest_pd(R: np.ndarray) -> np.ndarray:
    w, V = np.linalg.eigh((R + R.T) / 2)
    R2 = V @ np.diag(np.clip(w, 1e-6, None)) @ V.T
    d = np.sqrt(np.diag(R2))
    return R2 / np.outer(d, d)


def fit_t_copula(X: pd.DataFrame, nus=(2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30, 50)) -> dict:
    """Correlation from Kendall's τ (R = sin(πτ/2)); ν by profile maximum likelihood on the
    pseudo-observations (ranks). Returns {'R', 'nu', 'loglik', 'cols'}."""
    U = (X.rank().to_numpy() - 0.5) / len(X)
    tau = X.corr(method="kendall").to_numpy()
    R = _nearest_pd(np.sin(np.pi * tau / 2))
    best = None
    for nu in nus:
        Z = stats.t.ppf(U, nu)
        ll = stats.multivariate_t(loc=np.zeros(len(R)), shape=R, df=nu).logpdf(Z).sum() \
            - stats.t.logpdf(Z, nu).sum()
        if best is None or ll > best[1]:
            best = (nu, ll)
    return {"R": R, "nu": best[0], "loglik": float(best[1]), "cols": list(X.columns), "n": len(X)}


def sample_t_copula(cop: dict, X: pd.DataFrame, n: int, rng) -> pd.DataFrame:
    """Simulated factor moves: t-copula dependence, empirical marginals (linear interpolation of
    the historical quantile function = smoothed bootstrap)."""
    R, nu = cop["R"], cop["nu"]
    Z = rng.multivariate_normal(np.zeros(len(R)), R, size=n, method="cholesky")
    W = rng.chisquare(nu, size=n) / nu
    U = stats.t.cdf(Z / np.sqrt(W)[:, None], nu)
    out = {c: np.quantile(X[c].to_numpy(float), U[:, j]) for j, c in enumerate(cop["cols"])}
    return pd.DataFrame(out)


def measures(pnl: np.ndarray, q: float, freq: str) -> dict:
    """All sample-based methods on one P&L sample: {method: (VaR, ES, note)}."""
    out = {"hs": (*hs(pnl, q), ""), "awhs": (*awhs(pnl, q, LAMBDA[freq]), f"λ={LAMBDA[freq]}"),
           "cf": (*cornish_fisher(pnl, q), "")}
    try:
        v, e, f = evt(pnl, q)
        out["evt"] = (v, e, f"ξ={f['xi']:.3f}, β={f['beta']:.2f}, n_u={f['n_u']}")
    except Exception as exc:                                       # noqa: BLE001
        out["evt"] = (np.nan, np.nan, f"uyğunlaşdırılmadı: {exc}")
    return out


# ---------------------------------------------------------------- Euler contributions
def euler(comp: pd.DataFrame, q: float, lines: dict) -> pd.DataFrame:
    """Component VaR (kernel estimate of −E[P&L_i | P&L ≈ −VaR], rescaled to sum to VaR) and
    exact component ES (−E[P&L_i | P&L ≤ −VaR]) from simulated scenarios."""
    tot = comp.sum(axis=1).to_numpy()
    n = len(tot)
    o = np.argsort(tot)
    k = int(np.floor((1 - q) * n))
    m = max(25, int(0.0025 * n))
    band = o[max(0, k - m):k + m + 1]
    var = -tot[o[k]]
    raw = -comp.iloc[band].mean()
    scale = var / raw.sum() if raw.sum() != 0 else np.nan
    es_c = -comp.iloc[o[:k + 1]].mean()
    rows = []
    for f in comp.columns:
        E = lines[f][0]
        rows.append({"komponent": f, "komponent_ad": FACTOR_AZ.get(f, f), "aktiv_sinfi": CLASS_OF.get(f, ""),
                     "ekspozisiya_mln_usd": E, "tohfe_VaR": raw[f] * scale, "tohfe_VaR_xam": raw[f],
                     "tohfe_ES": es_c[f], "marginal_VaR": raw[f] * scale / E if E else np.nan})
    out = pd.DataFrame(rows)
    out["pay_VaR"] = out["tohfe_VaR"] / var
    out["pay_ES"] = out["tohfe_ES"] / es_c.sum()
    out.attrs.update({"VaR": var, "ES": float(es_c.sum()), "scale": scale})
    return out


# ---------------------------------------------------------------- the VaR table
FACTORS_CORE = ["gold", "eq", "re", "ust2", "ust5", "ust10", "fx_eur", "fx_gbp", "fx_cny", "fx_jpy", "fx_oth"]
FACTORS = FACTORS_CORE + ["cs"]          # 'cs' (credit spread) is used only when the V2 panel has BAA10Y


def factors_in(*frames) -> list:
    """FACTORS present (with data) in every move frame: the credit-spread factor drops out when V2 lacks it."""
    return [f for f in FACTORS if all(f in m.columns and m[f].notna().sum() > 24 for m in frames)]


def horizon_samples(daily: pd.DataFrame, monthly: pd.DataFrame) -> dict:
    """Historical factor-move samples per horizon (only rows where every factor is observed)."""
    fd, fm_ = factor_moves(daily, "d"), factor_moves(monthly, "m")
    F = factors_in(fd, fm_)
    d = fd[F].dropna().iloc[-HS_WINDOW_D:]
    m = fm_[F].dropna()
    return {"1g": {"X": d, "freq": "d", "label": f"son {len(d)} iş günü"},
            "1a": {"X": working_corrected(m), "freq": "m", "raw": m,
                   "label": f"{m.index.min():%Y-%m}–{m.index.max():%Y-%m} aylıq orta, Working düzəlişi √1,5"},
            "1il": {"X": overlapping(m, 12), "freq": "m", "raw": m,
                    "label": f"üst-üstə düşən 12 aylıq dəyişmələr, {m.index.min():%Y}–{m.index.max():%Y}"}}


def simulate_moves(H: dict, n: int = N_MC, seed: int = SEED) -> dict:
    """t-copula Monte Carlo per horizon; 1 year = sum of 12 i.i.d. corrected monthly draws."""
    rng = np.random.default_rng(seed)
    out, cops = {}, {}
    cop_d = fit_t_copula(H["1g"]["X"])
    out["1g"] = sample_t_copula(cop_d, H["1g"]["X"], n, rng)
    cop_m = fit_t_copula(H["1a"]["X"])
    out["1a"] = sample_t_copula(cop_m, H["1a"]["X"], n, rng)
    acc = None
    for _ in range(12):
        s = sample_t_copula(cop_m, H["1a"]["X"], n, rng)
        acc = s if acc is None else acc + s
    out["1il"] = acc
    cops["1g"], cops["1a"], cops["1il"] = cop_d, cop_m, cop_m
    return {"moves": out, "copulas": cops}


def var_table(H: dict, MC: dict, ports: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, contrib = [], []
    for pid in ("sofaz", "net_fx"):
        lines, value = ports[pid]["lines"], ports[pid]["value"]
        for h in ("1g", "1a", "1il"):
            X = H[h]["X"]
            pnl = pnl_components(X, lines).sum(axis=1).to_numpy()
            comp_mc = pnl_components(MC["moves"][h], lines)
            cop = MC["copulas"][h]
            for q in CONF:
                res = measures(pnl, q, H[h]["freq"])
                vmc, emc = hs(comp_mc.sum(axis=1).to_numpy(), q)
                res["mc_tcop"] = (vmc, emc, f"ν={cop['nu']}, N={len(comp_mc)}"
                                  + (", 12 aylıq i.i.d. cəm" if h == "1il" else ""))
                if h != "1g":
                    v1, e1 = hs(pnl_components(H["1g"]["X"], lines).sum(axis=1).to_numpy(), q)
                    k = 21 if h == "1a" else 252
                    res["sqrt_time"] = (v1 * np.sqrt(k), e1 * np.sqrt(k), f"1 günlük HS × √{k} — TƏXMİNİ")
                for meth, (v, e, note) in res.items():
                    extra = " | üst-üstə düşən müşahidələr: n_eff ≈ n/12" if h == "1il" and meth in (
                        "hs", "awhs", "evt", "cf") else ""
                    rows.append({"portfel": pid, "portfel_ad": PORTF_AZ[pid], "metod": meth,
                                 "metod_ad": METHOD_AZ[meth], "etibarlilik": q, "horizont": h,
                                 "horizont_ad": HORIZON_AZ[h], "VaR_mln_usd": v, "ES_mln_usd": e,
                                 "VaR_mln_azn": v * PEG, "ES_mln_azn": e * PEG,
                                 "VaR_pct": v / value * 100, "ES_pct": e / value * 100,
                                 "portfel_deyeri_mln_usd": value,
                                 "n_musahide": len(comp_mc) if meth == "mc_tcop" else len(pnl),
                                 "pencere": H[h]["label"], "qeyd": note + extra,
                                 "etibarli": not (h == "1il" and meth == "evt"),
                                 "etibar_qeydi": EVT_OVERLAP_NOTE if (h == "1il" and meth == "evt") else ""})
                eu = euler(comp_mc, q, lines)
                eu.insert(0, "etibarlilik", q)
                eu.insert(0, "horizont", h)
                eu.insert(0, "portfel", pid)
                contrib.append(eu)
    return pd.DataFrame(rows), pd.concat(contrib, ignore_index=True)


EVT_OVERLAP_NOTE = ("ETİBARSIZ: GPD üst-üstə düşən 12 aylıq pəncərələrə uyğunlaşdırılıb (müstəqil müşahidə ≈ n/12, "
                    "n_u həddindən yuxarı müşahidələr asılıdır, ξ < 0 qeyri-real sərhəd verir) — yalnız müqayisə; "
                    "1 illik quyruq üçün mc_tcop (aylıq müstəqil çəkilişlərin cəmi) istifadə olunur")


# ---------------------------------------------------------------- backtests
def _predictive(x: np.ndarray, meth: str, q: float, freq: str, fit: dict | None = None) -> tuple[float, float, dict]:
    """VaR, ES and the parameters needed to sample the method's predictive distribution."""
    if meth == "hs":
        v, e = hs(x, q)
        return v, e, {"w": None}
    if meth == "awhs":
        v, e = awhs(x, q, LAMBDA[freq])
        return v, e, {"w": age_weights(len(x), LAMBDA[freq])}
    if meth == "cf":
        v, e = cornish_fisher(x, q)
        return v, e, {"mom": (x.mean(), x.std(ddof=1), stats.skew(x), stats.kurtosis(x))}
    v, e, f = evt(x, q, fit)
    return v, e, {"gpd": f}


def _draw(x, meth, par, rng, M):
    if meth == "cf":
        return cf_quantile(rng.random(M), *par["mom"])
    if meth == "awhs":
        d = x[rng.choice(len(x), size=M, p=par["w"])]
    else:
        d = x[rng.integers(0, len(x), size=M)]
    if meth == "evt":
        f = par["gpd"]
        hit = -d > f["u"]
        d[hit] = -(f["u"] + stats.genpareto.rvs(f["xi"], scale=f["beta"], size=int(hit.sum()), random_state=rng))
    return d


def acerbi_szekely_z2(x, var, es, alpha) -> float:
    """Z2 = Σ X_t·1{X_t < −VaR_t} / (T·α·ES_t) + 1 (Acerbi & Székely 2014); E_H0[Z2] = 0,
    negative values mean the ES was underestimated. X = P&L (gains positive)."""
    x, var, es = map(np.asarray, (x, var, es))
    I = x < -var
    return float(np.sum(x * I / es) / (len(x) * alpha) + 1)


def rolling_backtest(pnl: pd.Series, window: int, freq: str, methods=("hs", "awhs", "cf", "evt"),
                     M: int = 1000, seed: int = SEED) -> tuple[pd.DataFrame, dict]:
    """One-step-ahead rolling VaR/ES forecasts and realised P&L. Returns the forecast history and
    per (method, q) the H0 draws of Z2 (simulated under the method's own predictive distribution)."""
    from .backtest import kupiec, christoffersen                     # NFR1 battery (shared)
    rng = np.random.default_rng(seed)
    x_all = pnl.to_numpy(float)
    T = len(x_all) - window
    if T <= 0:
        return pd.DataFrame(), {}
    hist = {"tarix": pnl.index[window:], "pnl": x_all[window:]}
    tests = []
    fits: dict = {}
    for meth in methods:
        for q in CONF:
            V, E, Z2sim = np.full(T, np.nan), np.full(T, np.nan), np.zeros(M)
            for t in range(T):
                w = x_all[t:t + window]
                try:
                    if meth == "evt" and t not in fits:
                        fits[t] = gpd_fit(-w)
                    V[t], E[t], par = _predictive(w, meth, q, freq, fits.get(t) if meth == "evt" else None)
                except Exception:                                      # noqa: BLE001
                    fits.setdefault(t, None)
                    continue
                d = _draw(w.copy(), meth, par, rng, M)
                Z2sim += d * (d < -V[t]) / E[t]
            ok = ~np.isnan(V)
            n = int(ok.sum())
            Z2sim = Z2sim / (max(n, 1) * (1 - q)) + 1
            hist[f"VaR{int(q * 100)}_{meth}"] = V
            hist[f"ES{int(q * 100)}_{meth}"] = E
            if n == 0:
                tests.append({"metod": meth, "etibarlilik": q, "test": "bütün testlər", "n": 0,
                              "netice": "yoxlanıla bilməz", "qeyd": "proqnoz qurulmadı"})
                continue
            xb, vb, eb = hist["pnl"][ok], V[ok], E[ok]
            br = xb < -vb
            lr, p = kupiec(br, 1 - q)
            ch = christoffersen(br, 1 - q)
            z2 = acerbi_szekely_z2(xb, vb, eb, 1 - q)
            pz = float(np.mean(Z2sim <= z2))
            exp_b = n * (1 - q)
            base = {"metod": meth, "etibarlilik": q, "n": n, "pozuntu": int(br.sum()), "gozlenilen": exp_b}
            verdict = lambda pv: ("yoxlanıla bilməz" if exp_b < 1 or np.isnan(pv) else  # noqa: E731
                                  "keçdi" if pv >= 0.05 else "keçmədi")
            tests += [{**base, "test": "Kupiec POF", "statistika": lr, "p_deyer": p, "netice": verdict(p)},
                      {**base, "test": "Christoffersen müstəqillik", "statistika": ch["LR_ind"], "p_deyer": ch["p_ind"],
                       "netice": verdict(ch["p_ind"])},
                      {**base, "test": "Christoffersen şərti örtük", "statistika": ch["LR_cc"], "p_deyer": ch["p_cc"],
                       "netice": verdict(ch["p_cc"])},
                      {**base, "test": "Acerbi–Székely Z2 (ES)", "statistika": z2, "p_deyer": pz, "netice": verdict(pz),
                       "qeyd": f"p-dəyəri H0 altında {M} simulyasiya (metodun öz proqnoz paylanması)"}]
            if q == 0.99 and freq == "d":
                last = br[-250:]
                k = int(last.sum())
                zone = "yaşıl" if k <= 4 else ("sarı" if k <= 9 else "qırmızı")
                tests.append({**base, "n": len(last), "pozuntu": k, "gozlenilen": len(last) * 0.01,
                              "test": "Bazel svetoforu (son 250 gün)", "statistika": k, "p_deyer": np.nan,
                              "netice": f"{zone} zona" if len(last) >= 250 else "yoxlanıla bilməz",
                              "qeyd": "0–4 yaşıl, 5–9 sarı, ≥10 qırmızı"})
    return pd.DataFrame(hist).set_index("tarix"), {"tests": pd.DataFrame(tests)}


# ---------------------------------------------------------------- oil revenue at risk (1 year)
def oil_revenue_inputs(year: int | None = None) -> dict:
    from . import factors, spine
    y = year or config.score_year()
    B = spine.baseline()
    M = spine.multipliers()["brent10"]
    R0, T0 = float(B.at[y, "fr1_rev_oil_n"]), float(B.at[y, "fr1_rev_tot_n"])
    k = float(M.at[y, "rev_tot_n"]) / 100 * T0 / 10            # mln AZN per +1 USD/bbl (FR1 structural)
    b_base = float(B.at[y, "brent_usd"])
    return {"year": y, "R0": R0, "B0": float(B.at[y, "fr1_oil_exp_price"]), "k": k, "brent_base": b_base,
            "spread": float(B.at[y, "fr1_oil_exp_price"]) - b_base,    # export price = Brent + spread (FR1 baseline)
            "elasticity": k * float(B.at[y, "fr1_oil_exp_price"]) / R0,
            "deval": float(factors.params()["devaluation_size"]), "sigma_vol": np.log(1.05) / stats.norm.ppf(0.9)}


def oil_revenue(brent, deval_on, vol_shock, inp: dict) -> np.ndarray:
    R = (inp["R0"] + inp["k"] * (np.asarray(brent) + inp.get("spread", 0.0) - inp["B0"])) * np.exp(vol_shock)
    return np.maximum(R, 0.0) * (1 + inp["deval"] * np.asarray(deval_on, float))


def oil_revenue_at_risk(monthly: pd.DataFrame, n: int = config.N_SIM, seed: int = SEED) -> pd.DataFrame:
    from . import simulate
    inp = oil_revenue_inputs()
    rng = np.random.default_rng(seed + 7)
    rows = []
    res = simulate.run(n=n, seed=seed)
    j = res.col(inp["year"])
    dev = np.cumsum(res.events["R03"], axis=1)[:, j] > 0
    R_mc = oil_revenue(res.brent[:, j], dev, rng.normal(0, inp["sigma_vol"], n), inp)
    b = monthly["brent"].dropna()
    b = b[b.index >= "1990-01-01"]
    d12 = np.log(b).diff(12).dropna().to_numpy()
    anchor = inp["brent_base"]                                   # ONE anchor for every method (audit M7): the
    R_hs = oil_revenue(anchor * np.exp(d12), np.zeros(len(d12)), np.zeros(len(d12)), inp)   # baseline Brent
    loss_hs = inp["R0"] - R_hs                                   # shortfall vs FR1 budget baseline
    for q in CONF:
        qq = np.quantile(R_mc, 1 - q)
        cand = {"sim_joint": (inp["R0"] - qq, inp["R0"] - R_mc[R_mc <= qq].mean(),
                              f"Brent (baza mərkəzli baxış, median ≈ baza {anchor:.1f}) və devalvasiya RU birgə "
                              f"simulyasiyasından (N={n}), həcm ±5% (80%)")}
        for meth, (v, e) in (("hs", hs(-loss_hs, q)), ("awhs", awhs(-loss_hs, q, LAMBDA["m"])),
                             ("cf", cornish_fisher(-loss_hs, q))):
            cand[meth] = (v, e, f"Brent-in üst-üstə düşən 12 aylıq log-dəyişmələri 1990-dan, baza Brent {anchor:.1f} "
                                f"lövbərinə tətbiq (cari spot {b.iloc[-1]:.1f} yalnız məlumat üçün)")
        try:
            v, e, f = evt(-loss_hs, q)
            cand["evt"] = (v, e, f"ξ={f['xi']:.3f}, n_u={f['n_u']}; üst-üstə düşən müşahidələr")
        except Exception as exc:                                   # noqa: BLE001
            cand["evt"] = (np.nan, np.nan, f"uyğunlaşdırılmadı: {exc}")
        for meth, (v, e, note) in cand.items():
            rows.append({"portfel": "oil_rev", "portfel_ad": PORTF_AZ["oil_rev"], "metod": meth,
                         "metod_ad": METHOD_AZ[meth], "etibarlilik": q, "horizont": "1il", "horizont_ad": "1 il",
                         "VaR_mln_usd": v / PEG, "ES_mln_usd": e / PEG, "VaR_mln_azn": v, "ES_mln_azn": e,
                         "VaR_pct": v / inp["R0"] * 100, "ES_pct": e / inp["R0"] * 100,
                         "portfel_deyeri_mln_usd": inp["R0"] / PEG,
                         "n_musahide": n if meth == "sim_joint" else len(d12),
                         "pencere": f"{inp['year']} büdcə ili; FR1 bazası {inp['R0']:.0f} mln AZN, Brent {inp['B0']:.1f}",
                         "qeyd": note + f" | elastiklik {inp['elasticity']:.2f} (FR1 Brent+10 multiplikatoru); "
                                        f"vahid lövbər: FR1 baza gəliri R0 və baza Brent {anchor:.1f}",
                         "etibarli": meth != "evt", "etibar_qeydi": EVT_OVERLAP_NOTE if meth == "evt" else ""})
    return pd.DataFrame(rows)


def annual_factor_draws(monthly: pd.DataFrame, n: int, seed: int = SEED) -> pd.DataFrame:
    """Annual factor moves incl. Brent (12 i.i.d. corrected monthly t-copula draws) for car.py.
    Draws are de-meaned: expected price change 0; income (carry) is added explicitly in car.py."""
    mv = factor_moves(monthly, "m")
    m = mv[factors_in(mv) + ["brent"]].dropna()
    X = working_corrected(m)
    X = X - X.mean()                     # zero price drift: the risk layer does not forecast returns
    cop = fit_t_copula(X)
    rng = np.random.default_rng(seed + 11)
    acc = None
    for _ in range(12):
        s = sample_t_copula(cop, X, n, rng)
        acc = s if acc is None else acc + s
    acc.attrs["nu"] = cop["nu"]
    return acc


# ---------------------------------------------------------------- run
def _contrib_table(C: pd.DataFrame) -> pd.DataFrame:
    C = C.assign(qrup="amil")
    agg = (C.groupby(["portfel", "horizont", "etibarlilik", "aktiv_sinfi"], as_index=False)
           [["ekspozisiya_mln_usd", "tohfe_VaR", "tohfe_VaR_xam", "tohfe_ES", "pay_VaR", "pay_ES"]].sum())
    agg = agg.assign(qrup="aktiv sinfi", komponent=agg["aktiv_sinfi"], komponent_ad=agg["aktiv_sinfi"])
    agg["marginal_VaR"] = agg["tohfe_VaR"] / agg["ekspozisiya_mln_usd"].replace(0, np.nan)
    return pd.concat([C, agg], ignore_index=True)[
        ["portfel", "horizont", "etibarlilik", "qrup", "komponent", "komponent_ad", "aktiv_sinfi",
         "ekspozisiya_mln_usd", "tohfe_VaR", "tohfe_VaR_xam", "pay_VaR", "tohfe_ES", "pay_ES", "marginal_VaR"]]


def run(ctx: dict | None = None) -> dict:
    ctx = ctx if ctx is not None else {}
    if ctx.get("fetch") or not (config.OUTPUT / "V2_market_factors.csv").exists():
        fm.build(ctx)
    if not (config.OUTPUT / "V1_exposures.csv").exists():
        from . import exposures
        exposures.run(ctx)
    daily, monthly = fm.load_panels()
    ports = portfolios()
    H = horizon_samples(daily, monthly)
    MC = simulate_moves(H, ctx.get("n_mc", N_MC))
    V3, C = var_table(H, MC, ports)
    V3 = pd.concat([V3, oil_revenue_at_risk(monthly)], ignore_index=True)
    V4 = _contrib_table(C)
    # backtests: daily (window 250) and monthly (window 120) one-step-ahead, hypothetical P&L
    md, mm = factor_moves(daily, "d"), factor_moves(monthly, "m")
    F = factors_in(md, mm)
    md, mm = md[F].dropna(), mm[F].dropna()
    bt_rows, hist = [], {}
    for pid in ("sofaz", "net_fx"):
        L = ports[pid]["lines"]
        for h, mv, win, fr in (("1g", md, BT_WINDOW_D, "d"), ("1a", mm, BT_WINDOW_M, "m")):
            pnl = pnl_components(mv, L).sum(axis=1)
            hh, t = rolling_backtest(pnl, win, fr)
            if len(t.get("tests", [])):
                bt_rows.append(t["tests"].assign(portfel=pid, horizont=h, pencere=win,
                                                 dovr=f"{hh.index.min():%Y-%m-%d}–{hh.index.max():%Y-%m-%d}"))
            hist[(pid, h)] = hh
        bt_rows.append(pd.DataFrame([{"portfel": pid, "horizont": "1il", "metod": "bütün", "test": "bütün testlər",
                                      "n": 0, "netice": "yoxlanıla bilməz",
                                      "qeyd": "illik müstəqil müşahidə sayı < 25 (üst-üstə düşən 12 aylıq pəncərələr)"}]))
    bt_rows.append(pd.DataFrame([{"portfel": "oil_rev", "horizont": "1il", "metod": "bütün", "test": "bütün testlər",
                                  "n": 0, "netice": "yoxlanıla bilməz",
                                  "qeyd": "büdcə neft gəlirlərinin illik faktiki seriyası qısadır; VaR proqnoz arxivi yığılır"}]))
    V5 = pd.concat(bt_rows, ignore_index=True)
    V5 = V5[["portfel", "horizont", "metod", "etibarlilik", "test", "n", "pozuntu", "gozlenilen", "statistika",
             "p_deyer", "netice", "pencere", "dovr", "qeyd"]]
    s = hist[("sofaz", "1g")].copy()
    s = s[["pnl"] + [c for c in s.columns if c.startswith(("VaR", "ES"))]]
    for c in [c for c in s.columns if c.startswith("VaR99")]:
        s["pozuntu_" + c] = (s["pnl"] < -s[c]).astype(int)
    nf = hist[("net_fx", "1g")]
    s["netfx_pnl"], s["netfx_VaR99_hs"] = nf["pnl"], nf["VaR99_hs"]
    V6 = s.rename(columns={"pnl": "sofaz_pnl_hipotetik"}).reset_index()
    V6["tarix"] = pd.to_datetime(V6["tarix"]).dt.strftime("%Y-%m-%d")
    out = {}
    for name, df in (("V3_var_es", V3), ("V4_var_contributions", V4), ("V5_var_backtest", V5), ("V6_var_history", V6)):
        p = config.OUTPUT / f"{name}.csv"
        df.round(6).to_csv(p, index=False, lineterminator="\n")
        out[name] = str(p)
    desc = {"V3_var_es": "VaR və ES: ARDNF portfeli, suveren xalis valyuta mövqeyi, büdcənin neft gəlirləri; 5 metod, "
                         "95/99%, 1 gün / 1 ay / 1 il",
            "V4_var_contributions": "Komponent (Euler) və marjinal VaR/ES: amillər və aktiv sinifləri üzrə (t-kopula MK)",
            "V5_var_backtest": "VaR/ES geriyə doğru sınaqları: Kupiec, Christoffersen, Acerbi–Székely Z2, Bazel svetoforu (n ilə)",
            "V6_var_history": "Gündəlik sürüşən VaR/ES tarixçəsi və hipotetik P&L (idarə paneli üçün)"}
    for name, p in out.items():
        fm.register_catalog(f"{name}.csv", "var", desc[name], list(pd.read_csv(p, nrows=0).columns), "gündəlik")
    ctx["var"] = {"ports": ports, "H": H, "MC": MC, "V3": V3, "monthly": monthly, "daily": daily}
    return {**out, "nu": {h: MC["copulas"][h]["nu"] for h in ("1g", "1a")}}


if __name__ == "__main__":
    r = run({"fetch": False})
    print(r)
    v = pd.read_csv(r["V3_var_es"])
    print(v.pivot_table(index=["portfel", "horizont", "metod"], columns="etibarlilik", values="VaR_mln_usd").round(0))
