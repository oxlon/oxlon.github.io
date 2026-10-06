"""S1–S7 — dynamic risk scalability (miqyaslanma): how the size of each quantified risk factor
scales into every MicroUnit component, which variables and which estimated parameters carry it,
and what today's live deviations imply for the headline forecasts (daily decision table).

Method (structural only — contract §Binding constraints):
* every factor is a shock in natural units and in σ units, σ from the 1990–2025 history
  (log changes for prices, levels/changes for rates; robust σ where one year dominates);
* the shock is a persistent deviation of the factor from the baseline over 2026–2030, applied
  through the MicroUnit chain FR1→FR3→FR4→FR5→FR10→FR12 (`chain.run_chain`) as an exogenous
  path, a lever, or an intercept shift of the FR1 equation that carries the channel (with
  `addf_recalibrate=False`, so the shift is not absorbed by the 2025 add-factor);
* responses are differences from the chain's own Baseline run with the same lever settings;
* sizes k ∈ {−3,−2,−1,−0,5,+0,5,+1,+2,+3}σ and today's live deviation (D5) are scanned, so
  the response per unit, asymmetry and curvature (non-linearity: bounds, clipping, chained
  real GDP, ratios) are read off the engine itself — no linearisation is assumed.
Unknown override keys only warn inside the engines: this module fails loudly on them.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import config, spine

K_GRID = (-3.0, -2.0, -1.0, -0.5, 0.5, 1.0, 2.0, 3.0)
YEARS = list(config.FORECAST_YEARS)
CACHE = config.ROOT / "work" / "scalability_cache"
VERSION = "s-2026-10-06b"      # v2.1: shock-year impulses, RU layer (FX + R01 reaction overlays)
PEG = 1.7


class EngineError(RuntimeError):
    """An override was ignored or an engine failed — never silently accepted."""


# ---------------------------------------------------------------- MicroUnit access
def _micro():
    p = str(config.MICRO_DIR)
    if p not in sys.path:
        sys.path.insert(0, p)
    from microlib.engines import chain, fr1  # noqa: WPS433
    return chain, fr1


def _bad(w: str) -> bool:
    return "naməlum" in w or ("nəzərə alınmadı" in w and "upstream" not in w and "yuxarı axın" not in w)


def _check(warnings, errors, label):
    errs = {k: v for k, v in (errors or {}).items() if not str(k).endswith("_trace")}
    if errs:
        raise EngineError(f"{label}: mühərrik xətası {errs}")
    bad = [w for w in warnings if _bad(w)]
    if bad:
        raise EngineError(f"{label}: override nəzərə alınmadı → {bad}")
    return [w for w in warnings if "kəsildi" in w]


def _with_levers(ov: dict | None) -> dict:
    ov = {m: {s: (dict(v) if isinstance(v, dict) else v) for s, v in d.items()} for m, d in (ov or {}).items()}
    f = ov.setdefault("FR1", {})
    f["levers"] = {"addf_recalibrate": False, **(f.get("levers") or {})}
    return ov


def _flat(results: dict) -> dict:
    out = {}
    for res in results.values():
        for sid, d in res["series"].items():
            for y, v in d.items():
                if v is not None and np.isfinite(v):
                    out[(sid, int(y))] = float(v)
    return out


CHAINLINK_NOTE = ("FR1: real ÜDM zəncirvari üsulla (əvvəlki ilin qiymətləri) hesablanır — neft-qaz qiyməti artanda azalan "
                  "neft-qaz hasilatının çəkisi artır və real ÜDM baza ilə müqayisədə azala bilər; fəallığı qeyri-neft ÜDM üzrə oxuyun")


@contextlib.contextmanager
def addf_impulse(addf: dict | None):
    """One-year intercept shifts of FR1 equations: {var: [Δ per forecast year]} added to the FR1 add-factor path
    of the final pass (var = 'infl' pp, 'rva_agr' / 'rhhdisp' log units, 'lendrate' pp). Coefficient overrides are
    scalars (every year), so a shock-year impulse needs this; nothing is written to MicroUnit (runtime wrapper)."""
    addf = {k: list(v) for k, v in (addf or {}).items() if np.any(np.asarray(v, float) != 0)}
    if not addf:
        yield
        return
    _micro()
    from microlib.engines import _fr1_fc as FCM  # noqa: WPS433
    orig = FCM.final_pass

    def patched(M, CF, CAL, ex_path, path, ref):
        path = {y: dict(a) for y, a in path.items()}
        for var, inc in addf.items():
            for y, v in zip(YEARS, inc):
                if y in path and v:
                    path[y][var] = path[y].get(var, 0.0) + float(v)
        return orig(M, CF, CAL, ex_path, path, ref)
    FCM.final_pass = patched
    try:
        yield
    finally:
        FCM.final_pass = orig


def _exo_path(spec, base: np.ndarray) -> np.ndarray:
    """Same semantics as microlib.engines.base._exo_value (pct / add / values / {year: v} / list)."""
    base = np.asarray(base, float)
    if isinstance(spec, dict):
        if "pct" in spec:
            return base * (1 + np.asarray(spec["pct"], float) / 100.0)
        if "add" in spec:
            return base + np.asarray(spec["add"], float)
        if "values" in spec:
            return np.asarray(spec["values"], float)
        out = base.copy()
        for y, v in spec.items():
            out[YEARS.index(int(y))] = float(v)
        return out
    return np.asarray(spec, float) * np.ones(len(base)) if np.ndim(spec) == 0 else np.asarray(spec, float)


def ru_overlays(ov: dict | None) -> dict:
    """RU transmission layer added on top of a chain run so that every consumer uses the SAME channel set as the
    joint simulation: (a) FX — calibrated total − chain part (riskunit.fx); (b) R01 procyclical public-investment
    reaction in EXCESS of FR1's own F4 response, SOFAZ-financed (balance-neutral), as in simulate.py.
    Returns {(ru:ovl:<channel>:<var>, year): Δ} with var ∈ cpi, nonoil_lvl, debt_gdp, budget_gdp."""
    from . import fx, simulate
    exo = ((ov or {}).get("FR1") or {}).get("exogenous") or {}
    out = {}
    if "fx" in exo:
        b = exo_base("fx")
        x = fx.path_from_fx(_exo_path(exo["fx"], b), b)
        if np.any(np.abs(x) > 1e-9):
            o = fx.overlay(x)
            for v in ("cpi", "nonoil_lvl", "debt_gdp"):
                for t, y in enumerate(YEARS):
                    out[(f"ru:ovl:fx:{v}", y)] = float(o[v][0, t])
    if "brent" in exo:
        b = exo_base("brent")
        r = simulate.fiscal_reaction(_exo_path(exo["brent"], b), b)
        for v, k in (("nonoil_lvl", "g_lvl"), ("cpi", "cpi")):
            for t, y in enumerate(YEARS):
                out[(f"ru:ovl:react:{v}", y)] = float(r[k][t])
    return out


def run_chain(ov: dict | None = None, label: str = "", overlays: bool = True) -> tuple[dict, list]:
    """One chain run → ({(id, year): value}, clip warnings). Raises EngineError on ignored keys.
    v2.1: an optional top-level key "RU" = {"addf": {var: [T]}, "overlays": bool} carries the RU layer (one-year
    FR1 intercept impulses; FX / R01-reaction overlays, see ru_overlays) — it is stripped before the chain sees it.
    Overlay values are returned under ids 'ru:ovl:*' and enter only the ru:* headline deltas (derived_delta)."""
    chain, _ = _micro()
    ov = dict(ov or {})
    ru = ov.pop("RU", None) or {}
    with addf_impulse(ru.get("addf")):
        r = chain.run_chain(_with_levers(ov))
    clip = _check(r["warnings"], r["errors"], label)
    missing = [m for m in chain.ORDER if m not in r["results"]]
    if missing:
        raise EngineError(f"{label}: modullar işləmədi {missing}")
    flat = _flat(r["results"])
    if overlays and ru.get("overlays", True):
        flat.update(ru_overlays(ov))
    return flat, clip


def run_fr1(ov_fr1: dict | None = None, label: str = "") -> tuple[dict, list]:
    _, fr1 = _micro()
    o = _with_levers({"FR1": ov_fr1 or {}})["FR1"]
    r = fr1.run(o)
    clip = _check(r["warnings"], {}, label)
    return _flat({"FR1": r}), clip


def fr1_catalogue() -> dict:
    _, fr1 = _micro()
    return fr1.inputs()


def coef_base(key: str) -> float:
    for c in fr1_catalogue()["coefficients"]:
        if f"{c['eq_id']}|{c['name']}" == key:
            return float(c["value"])
    raise EngineError(f"naməlum əmsal {key}")


def exo_base(key: str) -> np.ndarray:
    for e in fr1_catalogue()["exogenous"]:
        if e["id"] == key:
            return np.asarray(e["baseline"]["Baseline"], float)
    raise EngineError(f"naməlum ekzogen {key}")


def micro_catalog() -> pd.DataFrame:
    fr = []
    for m in config.MICRO_MODULES:
        c = pd.read_csv(config.MICRO_FILES_V2[f"{m.lower()}_catalog"]).drop_duplicates("id")
        fr.append(c[["id", "module", "group_az", "label_az", "unit_az", "kind"]])
    return pd.concat(fr, ignore_index=True).set_index("id")


def engine_fingerprint() -> str:
    h = hashlib.sha256(VERSION.encode())
    root = Path(config.MICRO_DIR)
    for p in sorted((root / "output" / "engine").glob("*")) + sorted((root / "microlib" / "engines").glob("*.py")):
        if p.is_file():
            h.update(p.name.encode())
            h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()[:16]


# ---------------------------------------------------------------- headline derived metrics
HEAD = {  # id → (label_az, unit, how the delta is measured)
    "ru:nonoil_lvl": ("Qeyri-neft real ÜDM səviyyəsi", "% (baza ilə fərq)", "pct"),
    "ru:nonoil_g": ("Qeyri-neft ÜDM real artımı", "f.b.", "abs"),
    "ru:cpi": ("İnflyasiya (İQİ, illik orta)", "f.b.", "abs"),
    "ru:budget_gdp": ("Büdcə balansı", "% ÜDM (f.b.)", "abs"),
    "ru:tb_gdp": ("Mal ticarəti balansı (cari hesab proksisi)", "% ÜDM (f.b.)", "abs"),
    "ru:debt_gdp": ("Dövlət borcu", "% ÜDM (f.b.)", "abs"),
}
HEAD_IDS = ["fr1:rgdpnon", "fr1:rgdp", "fr1:gdp_n", "fr1:infl", "fr1:balance_n", "fr1:nobd_pct", "fr1:rcons",
            "fr1:rinv_tot", "fr1:rinv_state", "fr1:rx_non", "fr1:rm_non", "fr1:emp", "fr1:unemp", "fr1:wage",
            "fr1:rhhdisp", "fr1:lendrate", "fr1:rcred_tot", "fr1:rev_oil_n", "fr1:rev_tot_n", "fr1:debt_azn",
            "fr1:rva_agr", "fr1:rva_man", "fr1:rva_con", "fr1:rva_trd", "fr3:rw_avg", "fr4:budget",
            "fr5:vol:total", "fr10:ind_output", "fr12:ew:score:CON", "fr12:ew:score:TRD", "fr12:act:N:ALL"]


def _tb(f, y):
    return (f.get(("fr1:acc:x_oil:nominal", y), np.nan) + f.get(("fr1:acc:x_non:nominal", y), np.nan)
            - f.get(("fr1:acc:m_non:nominal", y), np.nan))


def derived_delta(base: dict, shock: dict, rgdpnon_2025: float) -> dict:
    """Headline deltas: growth pp, CPI pp, budget/trade balance as Δ mln AZN / Baseline gdp_n
    (contract update v2.3.1), debt ratio difference."""
    out = {}
    shock = _apply_overlays(shock)
    for y in YEARS:
        g = lambda f, k: f.get((k, y), np.nan)  # noqa: E731
        pb = rgdpnon_2025 if y == YEARS[0] else base.get(("fr1:rgdpnon", y - 1), np.nan)
        ps = rgdpnon_2025 if y == YEARS[0] else shock.get(("fr1:rgdpnon", y - 1), np.nan)
        gb = (g(base, "fr1:rgdpnon") / pb - 1) * 100
        gs = (g(shock, "fr1:rgdpnon") / ps - 1) * 100
        gdp0 = g(base, "fr1:gdp_n")
        out[("ru:nonoil_lvl", y)] = (g(shock, "fr1:rgdpnon") / g(base, "fr1:rgdpnon") - 1) * 100
        out[("ru:nonoil_g", y)] = gs - gb
        out[("ru:cpi", y)] = g(shock, "fr1:infl") - g(base, "fr1:infl")
        out[("ru:budget_gdp", y)] = (g(shock, "fr1:balance_n") - g(base, "fr1:balance_n")) / gdp0 * 100
        out[("ru:tb_gdp", y)] = (_tb(shock, y) - _tb(base, y)) / gdp0 * 100
        out[("ru:debt_gdp", y)] = ((g(shock, "fr1:debt_azn") / g(shock, "fr1:gdp_n") - g(base, "fr1:debt_azn") / gdp0) * 100
                                  + _ovl(shock, "debt_gdp", y))
    return out


def _ovl(f: dict, var: str, y: int) -> float:
    return float(sum(v for (k, yy), v in f.items() if yy == y and k.startswith("ru:ovl:") and k.endswith(":" + var)))


def _apply_overlays(shock: dict) -> dict:
    """RU-layer overlays (ru:ovl:*) folded into the headline inputs: rgdpnon × (1 + Δlevel/100), infl + Δcpi.
    FR1 component rows (S1 fr1:*, S4) stay pure chain output; only the ru:* headline deltas include the layer."""
    if not any(str(k).startswith("ru:ovl:") for k, _ in shock):
        return shock
    s2 = dict(shock)
    for y in YEARS:
        if ("fr1:rgdpnon", y) in s2:
            s2[("fr1:rgdpnon", y)] = s2[("fr1:rgdpnon", y)] * (1 + _ovl(shock, "nonoil_lvl", y) / 100)
        if ("fr1:infl", y) in s2:
            s2[("fr1:infl", y)] = s2[("fr1:infl", y)] + _ovl(shock, "cpi", y)
    return s2


# ---------------------------------------------------------------- factor definitions (σ from history)
def _sd(x) -> tuple[float, int]:
    x = pd.Series(x).dropna()
    return float(x.std()), int(len(x))


def _robust_sd(x) -> tuple[float, int]:
    x = pd.Series(x).dropna()
    return float(1.4826 * np.median(np.abs(x - x.median()))), int(len(x))


def _ols_passthrough(dep: pd.Series, x: pd.Series, fx: pd.Series) -> dict:
    """Structural pass-through of an external price into AZ CPI inflation (HAC OLS, contemporaneous,
    no lagged dependent variable): cpi_t = a + b·x_t + c·dln_fx_t."""
    import statsmodels.api as sm
    d = pd.concat([dep.rename("y"), x.rename("x"), fx.rename("fx")], axis=1).dropna()
    m = sm.OLS(d["y"], sm.add_constant(d[["x", "fx"]])).fit(cov_type="HAC", cov_kwds={"maxlags": 2})
    return {"coef": float(m.params["x"]), "se": float(m.bse["x"]), "n": int(len(d)),
            "years": f"{d.index.min()}–{d.index.max()}"}


def factor_data() -> dict:
    """All inputs the factor definitions need (history, channels, engine baselines)."""
    from . import caem, factors
    P = spine.annual_panel()
    mi = spine.micro_fr1_dataset()
    ch = factors.channels()
    pn = ch["_panel"]
    hz = factors.hazards()
    prm = factors.params()
    food, _ = caem.food_monthly()
    fa = food.groupby(food.index.year).mean() if food is not None else pd.Series(dtype=float)
    fg = (fa.pct_change() * 100).loc[2004:config.LAST_ACTUAL] if len(fa) else pd.Series(dtype=float)
    imp = caem.external_block()["import_price_infl"].astype(float)
    # v2.1 (audit M1): ONE external-price pass-through for food, imports and FX — factors 'cpi_ext'
    b0, b1 = ch[("cpi_ext", "impA")]["coef"], ch[("cpi_ext", "impA_l1")]["coef"]
    se = float(np.sqrt(ch[("cpi_ext", "cov")].sum()))
    meta = ch[("cpi_ext", "meta")]
    gam = float(ch["_impfood"]["gamma"])
    pt_ext = {"b0": b0, "b1": b1, "coef": b0 + b1, "se": se, "n": meta["n"], "years": meta["sample"]}
    pt_food = {**pt_ext, "coef": (b0 + b1) * gam, "se": se * gam, "gamma": gam}
    pt_imp = dict(pt_ext)
    L = mi.loc[config.LAST_ACTUAL]
    return {"P": P, "mi": mi, "ch": ch, "pn": pn, "hz": hz, "prm": prm, "food_g": fg, "food_annual": fa,
            "imp": imp, "pt_food": pt_food, "pt_imp": pt_imp, "pt_ext": pt_ext,
            "s_h": float(P.at[config.LAST_ACTUAL, "remit_usd"] * PEG / L["hhdisp_n"]),
            "gdp_over_nonoil": float(L["gdp_n"] / L["gdp_nonoil_n"]), "p_inv": float(L["p_inv"]),
            "rgdpnon_2025": float(L["rgdpnon"])}


def _paths(j: int):
    """Shock-year impulse helpers (v2.1, audit C2): imp(v) — v in the shock year only; step(v) — v from the shock
    year on (the level after a one-off innovation in a CHANGE); lag2(a, b) — a in the shock year, b the year after.
    The shock year is read from a cell so `build_at(k, j)` can place the same shock in another year (live rows)."""
    T = len(YEARS)
    cell = {"j": j}
    def imp(v):
        out = [0.0] * T
        out[cell["j"]] = float(v)
        return out
    def step(v):
        return [0.0] * cell["j"] + [float(v)] * (T - cell["j"])
    def lag2(a, b):
        out = imp(a)
        if cell["j"] + 1 < T:
            out[cell["j"] + 1] = float(b)
        return out
    return imp, step, lag2, cell


SHOCK_RULE_AZ = ("şok yalnız şok ilində ({y}) verilir (2026 = 0): dəyişmə ilə ölçülən amillərdə (qiymətlərin log dəyişməsi, "
                 "faiz dəyişməsi, artım tempi) səviyyə sonra yeni yolda qalır (illik dəyişmələrin avtokorrelyasiyası ≈ 0); "
                 "səviyyə/axın amillərində (SPI, xərc şoku, ərzaq/idxal inflyasiyası, GPR sıçrayışı) yalnız şok ilinin impulsu")


def factor_specs(D: dict | None = None) -> dict:
    """Factor key → spec {ad, risk_idler, vahid, kind, sigma, basis, n, adverse, build(k) → (ov, size)}.
    v2.1: every factor is a SHOCK-YEAR impulse (score year), see SHOCK_RULE_AZ; CPI-type shocks enter as one-year
    FR1 intercept impulses (RU addf layer) with the single external-price pass-through (factors 'cpi_ext')."""
    D = D or factor_data()
    P, mi, ch, pn, prm, hz = D["P"], D["mi"], D["ch"], D["pn"], D["prm"], D["hz"]
    j = YEARS.index(config.score_year())
    imp, step, lag2, cell = _paths(j)
    yrs = slice(2003, config.LAST_ACTUAL)
    S = {}

    def add(key, ad, risks, unit, kind, sig, basis, n, adverse, channel, build):
        S[key] = {"ad": ad, "risk_idler": risks, "vahid": unit, "kind": kind, "sigma": sig, "sigma_esasi": basis,
                  "n": n, "pis_istiqamet": adverse, "kanal": channel, "build": build, "sok_qaydasi": "",
                  "qeyd": ""}

    b_br, g_ex, ist = exo_base("brent"), exo_base("gas_exp_price"), exo_base("istate_level")
    s, n = _sd(P["dln_brent"].loc[yrs] / 100)
    add("brent", "Brent neft qiyməti", "R01;R03;R14", "USD/barel", "log", s,
        f"illik orta Brent-in log dəyişməsinin sd, 2003–{config.LAST_ACTUAL}", n, -1,
        "FR1 ekzogen `brent` (şok ilindən səviyyə) + RU qatı: R01 prosiklik investisiya reaksiyası (simulate ilə eyni)",
        lambda k, s=s: ({"FR1": {"exogenous": {"brent": {"pct": step((np.exp(k * s) - 1) * 100)}}}},
                        b_br[j] * (np.exp(k * s) - 1)))
    s, n = _sd(np.log(mi["gas_exp_price"]).diff().loc[2007:config.LAST_ACTUAL])
    add("gas", "Qazın ixrac qiyməti", "R01;R11", "USD/min m³", "log", s,
        f"FR1 qaz ixrac qiymətinin log dəyişməsinin sd, 2007–{config.LAST_ACTUAL}", n, -1, "FR1 ekzogen `gas_exp_price`",
        lambda k, s=s: ({"FR1": {"exogenous": {"gas_exp_price": {"pct": step((np.exp(k * s) - 1) * 100)}}}},
                        g_ex[j] * (np.exp(k * s) - 1)))
    s, n = _sd(mi["dln_fx"].loc[2004:config.LAST_ACTUAL] / 100)
    add("fx", "Manatın məzənnəsi (+ = devalvasiya)", "R03", "% (USD/AZN)", "log", s,
        f"USD/AZN log dəyişməsinin sd, 2004–{config.LAST_ACTUAL} (2015–2016 rejim dəyişikliyi daxil)", n, +1,
        "FR1 ekzogen `fx` (şok ilindən səviyyə) + RU qatı: məzənnə modulu (İQİ iki illik ötürmə, qeyri-neft analoqu, "
        "xarici borcun yenidənqiymətləndirilməsi) − zəncirin öz cavabı",
        lambda k, s=s: ({"FR1": {"exogenous": {"fx": {"pct": step((np.exp(k * s) - 1) * 100)}}}}, (np.exp(k * s) - 1) * 100))
    s, n = _sd(P["partner_g"].loc[yrs])
    eps = float(prm["ext_demand_elasticity"])
    add("partner", "Tərəfdaş ölkələrin artımı (xarici tələb)", "R05", "f.b. (artım)", "add", s,
        f"tərəfdaş real ÜDM artımının sd, 2003–{config.LAST_ACTUAL}; xarici tələb elastikliyi {eps:g}", n, -1,
        "FR1 ekzogen `extdem` (şok ilində birdəfəlik artım şoku → səviyyə qalır)",
        lambda k, s=s: ({"FR1": {"exogenous": {"extdem": {"pct": step(eps * k * s)}}}}, k * s))
    s, n = _sd(mi["polrate"].diff().loc[2007:config.LAST_ACTUAL])
    add("rate", "Uçot dərəcəsi / maliyyə şəraiti", "R02", "f.b.", "add", s,
        f"AMB uçot dərəcəsinin illik dəyişməsinin sd, 2007–{config.LAST_ACTUAL}; depozit faizi 0,5× (FR1 multiplikator nisbəti)",
        n, +1, "FR1 ekzogen `polrate` (G1 kredit) + `deprate` (G3 kredit faizi; real təsiri yoxdur — D1-də real faiz yoxdur)",
        lambda k, s=s: ({"FR1": {"exogenous": {"polrate": {"add": step(k * s)}, "deprate": {"add": step(0.5 * k * s)}}}}, k * s))
    s, n = _sd(np.log(mi["rinv_state"]).diff().loc[2004:config.LAST_ACTUAL])
    add("state_inv", "Dövlət investisiyası (− = kəsinti)", "R11;R13", "mln AZN (2015 qiym.)", "log", s,
        f"real dövlət investisiyasının log dəyişməsinin sd, 2004–{config.LAST_ACTUAL}", n, -1,
        "FR1 ekzogen `istate_add` (şok ilindən səviyyə)",
        lambda k, s=s: ({"FR1": {"exogenous": {"istate_add": {"values": list(ist * (np.exp(k * s) - 1) * np.asarray(step(1.0)))}}}},
                        float(ist[j] * (np.exp(k * s) - 1))))
    s, n = _robust_sd(P["remit_g"].loc[yrs] / 100)
    sh = D["s_h"]
    add("remit", "Pul baratları", "R07", "%", "log", s,
        f"pul baratları artımının robast sd (1,4826×MAD; 2022 axını quyruqdur), 2003–{config.LAST_ACTUAL}; "
        f"baratlar / sərəncamda qalan gəlir = {sh * 100:.1f}%", n, -1,
        "FR1 E3 (sərəncamda qalan gəlir) düzəliş əmsalı ln(1 + pay·Δ), şok ilindən",
        lambda k, s=s: ({"FR1": {}, "RU": {"addf": {"rhhdisp": step(np.log1p(sh * (np.exp(k * s) - 1)))}}},
                        (np.exp(k * s) - 1) * 100))
    b_spi = float(ch[("agri_spi", "spi")]["coef"])
    add("drought", "Quraqlıq (SPI; − = quraq)", "R09", "SPI vahidi", "add", 1.0,
        f"SPI standartlaşdırılıb (σ = 1); SPI → kənd təsərrüfatı artımı {b_spi:.3f} %/vahid (HAC, RU FR1)", 0, -1,
        "FR1 C1 (kənd təsərrüfatı, səviyyə tənliyi) düzəliş əmsalı — yalnız şok ili (keçici)",
        lambda k: ({"FR1": {}, "RU": {"addf": {"rva_agr": imp(b_spi / 100 * k)}}}, k))
    b0, b1 = D["pt_ext"]["b0"], D["pt_ext"]["b1"]
    gam = float(ch["_impfood"]["gamma"])
    for key, ad, risks, src, load, why in (
            ("food", "Dünya ərzaq qiymətləri (Brent-dən asılı olmayan hissə)", "R18;R12", pn["food_own"], gam,
             f"ərzaq → USD idxal qiymətləri {gam:.2f}"),
            ("import", "İdxal qiymətləri (Brent və ərzaqdan asılı olmayan hissə)", "R17;R12", pn["imp_own"], 1.0, "birbaşa")):
        s, n = _sd(src.loc[2004:config.LAST_ACTUAL])
        add(key, ad, risks, "% (illik artım)", "add", s,
            f"Brent-ə ortoqonal hissənin sd (n={n}); İQİ-yə ötürmə: AZN idxal qiymətləri b0 {b0:.3f} + b1 {b1:.3f} "
            f"(vahid qiymətləndirmə 'cpi_ext'), {why}", n, +1,
            "FR1 G4 (inflyasiya) düzəliş əmsalı: şok ilində b0·Δ, növbəti ildə b1·Δ (artım şoku, səviyyə qalır)",
            lambda k, s=s, a=load: ({"FR1": {}, "RU": {"addf": {"infl": lag2(b0 * a * k * s, b1 * a * k * s)}}}, k * s))
    s_c = float(spine.baseline_band_sigma("cpi_infl", YEARS[0]))
    add("costpush", "Daxili xərc şoku (inflyasiya sürprizi)", "R12", "f.b.", "add", s_c,
        "OxLon İQİ yelpiyinin σ-sı (80% zolaqdan), 2026", 0, +1, "FR1 G4 düzəliş əmsalı — yalnız şok ili",
        lambda k, s=s_c: ({"FR1": {}, "RU": {"addf": {"infl": imp(k * s)}}}, k * s))
    s, n = _sd(pn["dl_gpr_reg"].loc[yrs] / 100)
    bgb, bgp, bgr = (float(ch[c]["coef"]) for c in (("gpr_brent", "annual_avg"), ("partner_gpr", "dl_gpr_reg"),
                                                     ("remit_gpr", "dl_gpr_reg")))
    add("geo", "Regional geosiyasi risk (GPR, təxmin edilmiş kanallar)", "R06", "% (GPR)", "log", s,
        f"regional GPR log dəyişməsinin sd, 2003–{config.LAST_ACTUAL}; kanallar: Brent {bgb:.4f}, tərəfdaş {bgp:.4f}, "
        f"baratlar {bgr:.3f} (RU FR1 HAC/LP)", n, +1, "Brent + xarici tələb + E3 (baratlar) — keçici: yalnız şok ili",
        lambda k, s=s: ({"FR1": {"exogenous": {"brent": {"pct": imp((np.exp(bgb * k * s) - 1) * 100)},
                                               "extdem": {"pct": imp(eps * bgp * k * s * 100)}}},
                         "RU": {"addf": {"rhhdisp": imp(np.log1p(sh * bgr * k * s))}}},
                        (np.exp(k * s) - 1) * 100))
    S["geo"]["qeyd"] = ("təxmin edilmiş kanallar üzrə xalis təsir müsbət ola bilər: GPR sıçrayışı Brent-i qaldırır (neft ixracatçısı "
                        "üçün əlverişli); əlverişsiz eskalasiya ssenarisi `geo_stress` (S4 vektoru) ilə verilir")
    add("geo_stress", "Geosiyasi eskalasiya (S4 analoq vektoru)", "R06;R07;R05", "S4 vektorunun payı", "add", 0.5,
        "1σ := S4 stress vektorunun yarısı (baratlar −30%, tərəfdaş −2 f.b., kredit faizi +1 f.b.) — EKSPERT", 0, +1,
        "E3 + xarici tələb + depozit faizi (→ kredit faizi G3) — yalnız şok ili",
        lambda k: ({"FR1": {"exogenous": {"extdem": {"pct": imp(eps * (-2.0) * 0.5 * k)},
                                          "deprate": {"add": imp(0.5 * k / coef_base("FR1.G3_lendrate|deprate"))}}},
                    "RU": {"addf": {"rhhdisp": imp(np.log1p(sh * (-0.30) * 0.5 * k))}}}, 0.5 * k))
    s, n = _sd(mi["npl_ratio"].diff().loc[2007:config.LAST_ACTUAL])
    add("npl", "Bank aktivlərinin keyfiyyəti (NPL payı)", "R04", "f.b.", "add", s,
        f"problemli kreditlər payının illik dəyişməsinin sd, 2007–{config.LAST_ACTUAL}", n, +1,
        "FR1 ekzogen `npl_ratio` → G3 kredit faizi (şok ilindən)",
        lambda k, s=s: ({"FR1": {"exogenous": {"npl_ratio": {"add": step(k * s)}}}}, k * s))
    S["npl"]["qeyd"] = ("MƏHDUDİYYƏT: NPL yalnız kredit faizini (G3) dəyişir; FR1-də kredit faizi real tərəfə ötürülmür "
                        "(D1 istehlak tənliyində real faiz yoxdur, G1 kredit həcmi uçot dərəcəsindən asılıdır) — real təsir "
                        "konstruksiya üzrə sıfırdır. Təklif olunan kanal: NPL → kredit təklifi (G1: Δln kredit = −θ·ΔNPL, θ "
                        "AMB bank paneli ilə qiymətləndirilməli) və ya D1/D2-yə real faiz; məlumat sorğusu V1b")
    _quake_spec(S, D, prm)
    for f, v in S.items():
        v["sok_qaydasi"] = v["sok_qaydasi"] or SHOCK_RULE_AZ.format(y=YEARS[j])
        if f != "quake":
            def build_at(k, jj, b=v["build"]):
                cell["j"] = jj
                try:
                    return b(k)
                finally:
                    cell["j"] = j
            v["build_at"] = build_at
    return S


QUAKE_REC = (0.25, 0.50, 0.25)      # reconstruction outlays: event year, +1, +2 (KALİBRLƏMƏ FƏRZİYYƏSİ)


def quake_profiles(T: int, j: int) -> tuple[np.ndarray, np.ndarray]:
    """v2.1 (audit: 15 % damage gave non-oil +0,83 % in the event year): capital is restored as reconstruction is
    spent, so the output loss is 1 in the event year and (1 − restored share) afterwards; reconstruction outlays
    are 25 % in the event year, 50 % and 25 % in the next two. Returns (loss weights, reconstruction weights)."""
    loss, rec = np.zeros(T), np.zeros(T)
    done = 0.0
    for k, w in enumerate(QUAKE_REC):
        if j + k < T:
            loss[j + k] = 1.0 - done
            rec[j + k] = w
        done += w
    return loss, rec


def _quake_spec(S: dict, D: dict, prm: dict) -> None:
    """Earthquake (one-sided hazard): direct damage d % GDP in the score year → supply-side TFP level loss (FR1
    `tfp_boost`, calibrated to eq_output_loss × d of non-oil GDP), fading as the capital is rebuilt, + reconstruction
    (FR1 `istate_add`, eq_fiscal_share × d over three years, QUAKE_REC). k ≥ 0 only: damage = median·exp(k·σ_log)."""
    j = YEARS.index(config.score_year())
    med, p90 = float(prm["eq_damage_med_tier2"]), float(prm["eq_damage_p90_tier2"])
    s_log = float(np.log(p90 / med) / 1.2815515655)
    cal = {}

    def tfp_per_unit():
        if "s" not in cal:
            v = [0.0] * len(YEARS)
            v[j] = -1.0
            b, _ = run_fr1({}, "quake-cal-base")
            f, _ = run_fr1({"exogenous": {"tfp_boost": {"values": v}}}, "quake-cal")
            y = YEARS[j]
            cal["s"] = abs(f[("fr1:rgdpnon", y)] / b[("fr1:rgdpnon", y)] - 1) * 100
            cal["gdp"] = b[("fr1:gdp_n", y)]
        return cal

    def build(k):
        if k <= 0:
            return None, 0.0
        d = min(med * np.exp(k * s_log), 15.0)
        c = tfp_per_unit()
        loss = float(prm["eq_output_loss"]) * d * D["gdp_over_nonoil"]
        lw, rw = quake_profiles(len(YEARS), j)
        # tfp_boost is cumulated by FR1 (tfp_cum) and bounded at ±3 per year: the loss and the reconstruction are
        # scaled by the SAME ratio when the bound binds (otherwise the rebuild would outweigh a truncated loss)
        a = loss / c["s"]
        ratio = min(1.0, 3.0 / a) if a > 0 else 1.0
        tfp = list(np.diff(np.concatenate([[0.0], -a * ratio * lw])))
        rec = float(prm["eq_fiscal_share"]) * d / 100 * c["gdp"] / D["p_inv"] * ratio
        return {"FR1": {"exogenous": {"tfp_boost": {"values": tfp}, "istate_add": {"values": list(rec * rw)}}}}, d

    S["quake"] = {"ad": "Güclü zəlzələ (birbaşa zərər)", "risk_idler": "R08", "vahid": "% ÜDM (zərər)", "kind": "hazard",
                  "sigma": s_log, "sigma_esasi": f"zərərin log-normal paylanması (M≥6: median {med:g}%, P90 {p90:g}% ÜDM — "
                  "KALİBRLƏMƏ FƏRZİYYƏSİ); yuxarı hədd 15% ÜDM", "n": 0, "pis_istiqamet": +1,
                  "kanal": f"FR1 `tfp_boost` (çıxış itkisi {prm['eq_output_loss']:g}×zərər, kapital bərpa olunduqca azalır) + "
                           f"`istate_add` (bərpa {prm['eq_fiscal_share']:g}×zərər: 25/50/25% üç ilə)",
                  "build": build, "sok_qaydasi": "hadisə şok ilində; itki bərpa ilə azalır (1; 0,75; 0,25), bərpa 25/50/25%",
                  "qeyd": "bərpa xərcləri hadisə ilində yalnız 25% — xalis təsir hadisə ilində mənfidir"}


# ---------------------------------------------------------------- today's live deviations (D5)
def _d5() -> pd.DataFrame:
    p = config.OUTPUT / "D5_daily_monitor.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame(columns=["indicator", "baseline_source"])


def _row(d5, ind, src="MicroUnit FR1", year=None):
    r = d5[(d5["indicator"] == ind) & (d5["baseline_source"] == src)]
    if year is not None and "baseline_year" in r:
        r = r[r["baseline_year"] == year]
    return r.iloc[0] if len(r) else None


def live_deviations(S: dict, D: dict) -> dict:
    """Factor key → {k, size, ov, tesvir, menbe}. Missing live data → no entry (stated in S7)."""
    d5, j, out = _d5(), YEARS.index(config.score_year()), {}
    sp, im = _row(d5, "brent_spot"), _row(d5, "brent_implied_annual")
    if sp is not None and im is not None:
        b = exo_base("brent")
        path = [float(im["latest"])] + [float(sp["latest"])] * (len(YEARS) - 1)
        out["brent"] = {"k": float(np.log(path[j] / b[j]) / S["brent"]["sigma"]), "size": path[j] - b[j],
                        "ov": {"FR1": {"exogenous": {"brent": {"values": path}}}},
                        "tesvir": f"Brent spot {sp['latest']:.1f} USD ({sp['date']}); 2026 illik {im['latest']:.1f}; "
                                  f"FR1 fərziyyəsi {b[j]:.0f} ({config.score_year()})", "menbe": "D5 (FRED)"}
    r = _row(d5, "usd_azn")
    if r is not None:
        x = float(r["deviation_pct"])
        f_rem = max(0.0, (12 - config.as_of().month) / 12)          # 2026 annual average: remaining months only
        out["fx"] = {"k": float(np.log1p(x / 100) / S["fx"]["sigma"]), "size": x,
                     "ov": {"FR1": {"exogenous": {"fx": {"pct": [x * f_rem] + [x] * (len(YEARS) - 1)}}}},
                     "tesvir": f"USD/AZN {r['latest']:.4f} ({r['date']}), fərziyyə {r['baseline_assumption']:.4f}",
                     "menbe": "D5 (AMB)"}
    r26, r27 = _row(d5, "policy_rate", year=2026), _row(d5, "policy_rate", year=config.score_year())
    if r27 is not None:
        d26 = float(r26["deviation"]) if r26 is not None else 0.0
        try:                                     # v2.1: 2026 = effective average (YTD steps + current rate), not the spot
            from . import monitor
            pi = monitor.policy_implied()
            d26 = float(pi["path"][YEARS[0]] - exo_base("polrate")[0]) if pi else d26
        except Exception:                        # noqa: BLE001
            pass
        d27 = float(r27["deviation"])
        path = [d26] + [d27] * (len(YEARS) - 1)
        out["rate"] = {"k": d27 / S["rate"]["sigma"], "size": d27,
                       "ov": {"FR1": {"exogenous": {"polrate": {"add": path}, "deprate": {"add": [0.5 * v for v in path]}}}},
                       "tesvir": f"uçot dərəcəsi {r27['latest']:.2f}% ({r27['date']}), FR1 {config.score_year()} fərziyyəsi "
                                 f"{r27['baseline_assumption']:.2f}%", "menbe": "D5 (AMB)"}
    r = _row(d5, "dsk_budget_exp_ytd_exec")
    if r is not None:
        x = float(r["deviation_pct"])
        ist = exo_base("istate_level")
        v = [0.0] * len(YEARS)
        v[0] = float(ist[0] * x / 100)
        out["state_inv"] = {"k": float(np.log1p(x / 100) / S["state_inv"]["sigma"]), "size": v[0],
                            "ov": {"FR1": {"exogenous": {"istate_add": {"values": v}}}},
                            "tesvir": f"PROKSİ: büdcə xərclərinin icrası planın {r['latest']:.1f}%-i (gözlənilən "
                                      f"{r['baseline_assumption']:.1f}%), yalnız 2026-ya tətbiq; mövsümilik nəzərə alınmır",
                            "menbe": "D5 (DSK)"}
    spi = float(D["hz"]["spi_now"])
    if np.isfinite(spi):
        ov, size = S["drought"]["build_at"](spi, 0)
        out["drought"] = {"k": spi, "size": size, "ov": ov, "menbe": "ERA5 SPI (RU FR1)",
                          "tesvir": f"cari hidroloji il SPI = {spi:.2f} — yalnız {YEARS[0]} məhsuluna (keçici)"}
    c1p = config.OUTPUT / "C1_caem_signals.csv"
    if c1p.exists():
        c1 = pd.read_csv(c1p)
        fl = c1[(c1["indicator"] == "food_price") & (c1["year"] == YEARS[0])]
        lv, bs = fl[fl["period"] == "canlı"], fl[fl["primary"] == True]  # noqa: E712
        if len(lv) and len(bs):
            dev = float(lv["value"].iloc[0] - bs["value"].iloc[0])
            # v2.1: only the Brent-orthogonal part is R18 (the Brent-linked part is in the brent row, R01)
            a_f = float(D["ch"]["_impfood"]["a_food"])
            bl = spine.live()
            b_cur = (0.75 * bl["brent_ytd_avg"] + 0.25 * bl["brent_last"]) if YEARS[0] == config.as_of().year else np.nan
            dlb = 100 * np.log(b_cur / exo_base("brent")[0]) if np.isfinite(b_cur) else 0.0
            own = dev - a_f * dlb
            k = own / S["food"]["sigma"]
            ov, size = S["food"]["build_at"](k, 0)
            out["food"] = {"k": k, "size": size, "ov": ov, "menbe": "C1 (FRED PFOODINDEXM)",
                           "tesvir": f"dünya ərzaq indeksi 2026 (ilin əvvəlindən) {lv['value'].iloc[0]:.1f}% vs OxLon fərziyyəsi "
                                     f"{bs['value'].iloc[0]:.1f}%; Brent-ə bağlı hissə {a_f * dlb:+.1f} f.b. (R01 sətrində), "
                                     f"öz hissə {own:+.1f} f.b."}
    r = _row(d5, "cpi_implied_annual")
    if r is not None:
        k = float(r["deviation"]) / S["costpush"]["sigma"]
        ov, size = S["costpush"]["build_at"](k, 0)
        out["costpush"] = {"k": k, "size": size, "ov": ov, "menbe": "D5 (DSK)",
                           "tesvir": f"İQİ 2026 {r['latest']:.2f}% vs FR1 {r['baseline_assumption']:.2f}% (yalnız {YEARS[0]} "
                                     "impulsu; ərzaq və Brent sətirləri ilə qismən üst-üstə düşür)"}
    from . import factors
    gm = factors.regional_gpr_monthly().dropna()
    if len(gm) > 130:
        x = float(np.log(gm.iloc[-3:].mean() / gm.iloc[-123:-3].mean()))
        k = x / S["geo"]["sigma"]
        ov, size = S["geo"]["build"](k)
        out["geo"] = {"k": k, "size": size, "ov": ov, "menbe": "GPR (Caldara–Iacoviello)",
                      "tesvir": f"regional GPR son 3 ay / əvvəlki 10 il: {np.exp(x) * 100 - 100:+.0f}%"}
    eq = spine.live().get("eq_last") or {}
    mag = float(eq.get("value", 0) or 0)
    tier = float(D["prm"]["eq_mag_tier1"])
    if mag >= tier:
        ov, size = S["quake"]["build"](0.0001)
        out["quake"] = {"k": 0.0, "size": size, "ov": ov, "menbe": "USGS",
                        "tesvir": f"son hadisə M{mag:.1f} {eq.get('place', '')} ({eq.get('date', '')}) — zərər qiymətləndirilməlidir"}
    return out


def live_note(key: str, D: dict) -> str:
    eq = spine.live().get("eq_last") or {}
    if key == "quake":
        return (f"son hadisə M{float(eq.get('value', 0) or 0):.1f} ({eq.get('date', '')}, {eq.get('place', '')}) — "
                f"M ≥ {D['prm']['eq_mag_tier1']:g} həddindən aşağı; zərər yoxdur")
    return "canlı məlumat yoxdur — yalnız ssenari elastikliyi (σ şəbəkəsi)"


# ---------------------------------------------------------------- S1 grid scan
def base_levels(base: dict) -> dict:
    B = spine.baseline()
    out = {}
    for y in YEARS:
        gdp = base.get(("fr1:gdp_n", y), np.nan)
        out[("ru:nonoil_g", y)] = float(B.at[y, "nonoil_realg"])
        out[("ru:cpi", y)] = float(B.at[y, "cpi_infl"])
        out[("ru:budget_gdp", y)] = float(B.at[y, "fr1_balance_pct"])
        out[("ru:tb_gdp", y)] = _tb(base, y) / gdp * 100
        out[("ru:debt_gdp", y)] = base.get(("fr1:debt_azn", y), np.nan) / gdp * 100
        out[("ru:nonoil_lvl", y)] = 0.0
    return out


def labels() -> dict:
    cat = micro_catalog()
    lab = {i: (r.label_az, r.unit_az) for i, r in cat.iterrows()}
    lab.update({k: (v[0], v[1]) for k, v in HEAD.items()})
    return lab


PRICE_FACTORS = {"brent", "gas", "fx", "geo"}
OVL_VAR = {"ru:cpi": "cpi", "ru:nonoil_lvl": "nonoil_lvl", "ru:debt_gdp": "debt_gdp"}


def _pct_ok(b0: float, v: float) -> bool:
    """A % change is meaningful only for a positive base that the shock does not push through zero and when the
    ratio is not explosive (near-zero bases: balances, increments) — otherwise report the level difference."""
    return np.isfinite(b0) and np.isfinite(v) and b0 > 1e-9 and v > 0 and abs(v / b0 - 1) <= 5.0


def head_rows(f, spec, variant, k, size, base, fl, dd, bl, clip, lab):
    rows = []
    note = "; ".join(sorted(set(clip)))[:300]
    for tid in list(HEAD) + HEAD_IDS:
        for y in YEARS:
            ru_q = np.nan
            if tid in HEAD:
                b0, d = bl.get((tid, y), np.nan), dd.get((tid, y), np.nan)
                dp = d if HEAD[tid][2] == "pct" else np.nan
                if tid in OVL_VAR:
                    ru_q = _ovl(fl, OVL_VAR[tid], y)
            else:
                if (tid, y) not in base:
                    continue
                b0 = base[(tid, y)]
                v = fl.get((tid, y), np.nan)
                d = v - b0
                dp = d / abs(b0) * 100 if _pct_ok(b0, v) else np.nan
            izah = CHAINLINK_NOTE if (tid == "fr1:rgdp" and f in PRICE_FACTORS) else ""
            rows.append({"amil": f, "amil_ad": spec["ad"], "variant": variant, "k_sigma": k, "olcu": size,
                         "olcu_vahidi": spec["vahid"], "hedef_id": tid, "hedef_ad": lab.get(tid, (tid, ""))[0],
                         "vahid": lab.get(tid, ("", ""))[1], "il": y, "baza": b0, "ssenari": b0 + d, "delta": d,
                         "delta_pct": dp, "qeyd": note, "ru_qat": ru_q, "izah": izah})
    return rows


_head_rows = head_rows          # backward-compatible private name (API)


def scan(S: dict, D: dict, live: dict, keep=(1.0, -1.0), grid: bool = True) -> tuple[dict, pd.DataFrame, dict]:
    """All factors × k-grid (+ live) through the chain. Returns (baseline flat, S1 rows, full flats
    for k ∈ keep and the live runs)."""
    base, _ = run_chain({}, "baseline")
    bl, lab = base_levels(base), labels()
    rows, comp = [], {}
    for f, spec in S.items():
        runs = ([("σ-şəbəkə", k) for k in K_GRID] if grid else []) + ([("canlı", "live")] if f in live else [])
        for variant, k in runs:
            if k == "live":
                ov, size, kk = live[f]["ov"], live[f]["size"], live[f]["k"]
            else:
                ov, size = spec["build"](k)
                kk = k
            if ov is None:
                continue
            fl, clip = run_chain(ov, f"{f}@{k}")
            dd = derived_delta(base, fl, D["rgdpnon_2025"])
            rows += head_rows(f, spec, variant, kk, size, base, fl, dd, bl, clip, lab)
            if k in keep or k == "live":
                comp[(f, k)] = {**fl, **{("Δ" + a, y): v for (a, y), v in dd.items()}}
    return base, pd.DataFrame(rows), comp


_base_levels, _labels = base_levels, labels          # backward-compatible private names (API)


# ---------------------------------------------------------------- S2 elasticities, S3 non-linearity
def elasticities(S1: pd.DataFrame, S: dict) -> pd.DataFrame:
    g = S1.copy()
    g["delta_per_sigma"] = np.where(g["k_sigma"].abs() > 1e-9, g["delta"] / g["k_sigma"], np.nan)
    g["delta_per_unit"] = np.where(g["olcu"].abs() > 1e-12, g["delta"] / g["olcu"], np.nan)
    pct_factor = g["amil"].map(lambda f: S[f]["kind"] == "log")
    fac_pct = np.where(pct_factor, (np.exp(g["k_sigma"] * g["amil"].map(lambda f: S[f]["sigma"])) - 1) * 100, np.nan)
    g["elastiklik"] = np.where(np.isfinite(g["delta_pct"]) & pct_factor, g["delta_pct"] / fac_pct, np.nan)
    g["vahid_cavab_izah"] = g["vahid"] + " / " + g["olcu_vahidi"]
    return g[["amil", "amil_ad", "variant", "hedef_id", "hedef_ad", "il", "k_sigma", "olcu", "olcu_vahidi", "delta",
              "vahid", "delta_per_sigma", "delta_per_unit", "vahid_cavab_izah", "elastiklik", "delta_pct"]]


THRESH = {"ru:nonoil_g": ("Growth-at-Risk həddi (qeyri-neft artımı < hədd)", "nonoil_gar_threshold", -1),
          "ru:cpi": ("İnflyasiya həddi (> hədd)", "cpi_threshold", +1),
          "ru:budget_gdp": ("Büdcə balansı həddi (< hədd, % ÜDM)", "fiscal_threshold", -1),
          "ru:debt_gdp": ("Dövlət borcu > 30% ÜDM (DSA həddi)", None, +1),
          "ru:tb_gdp": ("Mal ticarəti balansı < 0 (kəsir)", None, -1)}
PLAUS = {"ru:nonoil_lvl": 10.0, "ru:nonoil_g": 6.0, "ru:cpi": 10.0, "ru:budget_gdp": 8.0, "ru:debt_gdp": 15.0,
         "ru:tb_gdp": 15.0}


def _cross(ks, lv, thr, side):
    """Smallest |k| in each direction where level crosses thr (side −1: below, +1: above)."""
    hit = (lambda v: v < thr) if side < 0 else (lambda v: v > thr)
    res = {}
    for sgn in (-1, 1):
        pts = sorted([(abs(k), v) for k, v in zip(ks, lv) if np.sign(k) == sgn or k == 0])
        prev = None
        res[sgn] = np.nan
        for a, v in pts:
            if hit(v):
                if prev is None or a == prev[0]:
                    res[sgn] = a
                else:
                    a0, v0 = prev
                    res[sgn] = a0 + (thr - v0) / (v - v0) * (a - a0) if v != v0 else a
                break
            prev = (a, v)
    return res


def nonlinearity(S1: pd.DataFrame, S: dict, D: dict) -> pd.DataFrame:
    prm = D["prm"]
    g = S1[S1["variant"] == "σ-şəbəkə"]
    rows = []
    for (f, tid, y), d in g.groupby(["amil", "hedef_id", "il"]):
        r = dict(zip(d["k_sigma"], d["delta"]))
        sz = dict(zip(d["k_sigma"], d["olcu"]))
        out = {"amil": f, "amil_ad": S[f]["ad"], "hedef_id": tid, "hedef_ad": d["hedef_ad"].iloc[0], "il": y,
               "vahid": d["vahid"].iloc[0], "cavab_m1": r.get(-1.0, np.nan), "cavab_p1": r.get(1.0, np.nan)}
        flags = []
        for k in (0.5, 1.0, 2.0, 3.0):
            a, b = r.get(k, np.nan), r.get(-k, np.nan)
            den = abs(a) + abs(b)
            out[f"asimmetriya_{k:g}"] = abs(a) / abs(b) if abs(b) > 1e-12 else np.nan
            out[f"eyrilik_{k:g}"] = (a + b) / den if den > 1e-12 else np.nan
        for k in (2.0, 3.0):
            for sgn in (1, -1):
                a1, ak = r.get(sgn * 1.0, np.nan), r.get(sgn * k, np.nan)
                out[f"miqyas_sapmasi_{'+' if sgn > 0 else '-'}{k:g}"] = ak / (k * a1) - 1 if abs(a1) > 1e-12 else np.nan
        e = [abs(out.get(f"eyrilik_{k:g}", np.nan)) for k in (1.0, 2.0, 3.0)]
        m = [abs(out.get(c, np.nan)) for c in out if str(c).startswith("miqyas_sapmasi")]
        scale = max(abs(out["cavab_m1"]), abs(out["cavab_p1"]))
        material = scale > 0.01
        if material and np.nanmax(e + [0]) > 0.10:
            flags.append("asimmetrik cavab")
        if material and np.nanmax(m + [0]) > 0.10:
            flags.append("qeyri-proporsional miqyas")
        clipped = d.loc[d["qeyd"].fillna("").str.len() > 0, "k_sigma"].tolist()
        if clipped:
            flags.append("sərhəd kəsilməsi k=" + ",".join(f"{c:g}" for c in sorted(clipped)))
        out["qeyri_xetti"] = bool(flags and material)
        out["qeyd"] = "; ".join(flags)
        if tid in THRESH:
            nm, key, side = THRESH[tid]
            thr = float(prm[key]) if key else (30.0 if tid == "ru:debt_gdp" else 0.0)
            b0 = d["baza"].iloc[0]
            ks = [0.0] + list(d["k_sigma"])
            lv = [b0] + list(b0 + d["delta"])
            cr = _cross(ks, lv, thr, side)
            out.update({"hedd_ad": nm, "hedd": thr, "baza_seviyye": b0, "k_hedd_menfi": cr[-1], "k_hedd_musbet": cr[1]})
            for sgn, c in ((-1, "olcu_hedd_menfi"), (1, "olcu_hedd_musbet")):
                kk = cr[sgn]
                xs = sorted((x for x in sz if np.sign(x) == sgn), key=abs)
                if not np.isfinite(kk) or not xs:
                    out[c] = np.nan
                else:
                    out[c] = float(np.interp(kk, [0.0] + [abs(x) for x in xs], [0.0] + [sz[x] for x in xs]))
        if tid in PLAUS:
            lim = PLAUS[tid]
            over = [k for k, v in r.items() if abs(v) > lim]
            out["inandiriciliq_hedd"] = lim
            out["inandiriciliq_asilir_k"] = ",".join(f"{k:g}" for k in sorted(over)) if over else ""
        rows.append(out)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- S4 impact map (all components)
def effect(kind: str, unit: str, base: float, shock: float, gdp: float | None = None) -> tuple[float, str]:
    """Component effect for the impact map. v2.1: % change only where it is meaningful (_pct_ok); a near-zero or
    sign-crossing base (balances, increments) gives the level difference — in % of GDP for mln AZN flows when
    `gdp` (mln AZN) is given, in pp for rates/shares."""
    if kind in ("level", "index"):
        if _pct_ok(base, shock):
            return (shock / base - 1) * 100, "%"
        d = shock - base
        if gdp and "mln" in str(unit) and "AZN" in str(unit):
            return d / gdp * 100, "% ÜDM (f.b.)"
        return d, str(unit)
    d = shock - base
    if kind == "share" and "%" not in str(unit):
        return d * 100, "f.b."
    return d, "f.b." if "%" in str(unit) else str(unit)


def _effect(kind, unit, base, shock, gdp=None):            # backward-compatible private name (API)
    return effect(kind, unit, base, shock, gdp)


def impact_map(base: dict, comp: dict, S: dict) -> pd.DataFrame:
    cat = micro_catalog()
    hy = config.score_year()
    ids = sorted({i for (i, y) in base if y == hy and i in cat.index})
    gdp_h, gdp_l = base.get(("fr1:gdp_n", hy)), base.get(("fr1:gdp_n", YEARS[-1]))
    rows = []
    for (f, k), fl in comp.items():
        if k != 1.0:
            continue
        for i in ids:
            c = cat.loc[i]
            e1, u = effect(c["kind"], c["unit_az"], base[(i, hy)], fl.get((i, hy), np.nan), gdp_h)
            e2, _ = effect(c["kind"], c["unit_az"], base.get((i, YEARS[-1]), np.nan), fl.get((i, YEARS[-1]), np.nan), gdp_l)
            rows.append({"amil": f, "amil_ad": S[f]["ad"], "seviyye": "komponent", "modul": c["module"],
                         "qrup": c["group_az"], "komponent_id": i, "komponent_ad": c["label_az"], "olcu_sinfi": u,
                         f"tesir_{hy}": e1, f"tesir_{YEARS[-1]}": e2})
    M = pd.DataFrame(rows)
    if M.empty:
        return M
    M["sinif"] = np.where(M["olcu_sinfi"] == "%", "faiz dəyişməsi", "mütləq dəyişmə")
    a = M[f"tesir_{hy}"].abs()
    # v2.1: normalised by the 95th percentile within factor × measurement class (robust to a single outlier)
    mx = a.groupby([M["amil"], M["sinif"]]).transform(lambda x: x.quantile(0.95)).replace(0, np.nan)
    M["ehemiyyet"] = (a / mx).clip(upper=1.0).fillna(0.0)
    M["sira"] = M.groupby(["amil", "sinif"])["ehemiyyet"].rank(ascending=False, method="first").astype(int)
    G = (M.groupby(["amil", "amil_ad", "modul", "qrup"], as_index=False)
         .agg(ehemiyyet=("ehemiyyet", "mean"), max_ehemiyyet=("ehemiyyet", "max"), n=("komponent_id", "size")))
    top = M.loc[M.groupby(["amil", "modul", "qrup"])["ehemiyyet"].idxmax(), ["amil", "modul", "qrup", "komponent_id",
                                                                           "komponent_ad", f"tesir_{hy}"]]
    G = G.merge(top, on=["amil", "modul", "qrup"], how="left").assign(seviyye="qrup")
    G["sira"] = G.groupby("amil")["ehemiyyet"].rank(ascending=False, method="first").astype(int)
    G = G.rename(columns={"n": "komponent_sayi"})
    return pd.concat([G, M], ignore_index=True)[
        ["amil", "amil_ad", "seviyye", "modul", "qrup", "komponent_id", "komponent_ad", "komponent_sayi", "sinif",
         "olcu_sinfi", f"tesir_{hy}", f"tesir_{YEARS[-1]}", "ehemiyyet", "max_ehemiyyet", "sira"]]


# ---------------------------------------------------------------- S5 parameters carrying the transmission
SENS_TARGETS = ("ru:nonoil_lvl", "ru:cpi", "ru:budget_gdp", "ru:tb_gdp")


def _merge_fr1(shock: dict, coef_shift: dict) -> dict:
    """shock FR1 override + additive coefficient shifts {key: Δ} (absolute values recomputed)."""
    o = {s: (dict(v) if isinstance(v, dict) else v) for s, v in shock.items()}
    co = dict(o.get("coefficients") or {})
    for k, dv in coef_shift.items():
        co[k] = co.get(k, coef_base(k)) + dv
    o["coefficients"] = co
    return o


def _perturb(c: dict, sgn: int, x25: dict, cat: dict) -> dict:
    """±1 SE on a slope, with the add-factor recalibration done explicitly on the intercept
    (a_new = a_old − Δb·x_2025, as the engine's Part 13.4 convention) and homogeneity ties kept."""
    eq, nm, se = c["eq_id"], c["name"], float(c["se"])
    sh = {f"{eq}|{nm}": sgn * se}
    if c.get("tied_with"):
        sh[f"{eq}|{c['tied_with']}"] = -sgn * se
    x = x25.get(eq.split(".", 1)[1], {})
    if x and f"{eq}|const" in cat:
        sh[f"{eq}|const"] = -sum(dv * x.get(k.split("|")[1], 0.0) for k, dv in sh.items())
    return sh


def parameter_sensitivity(S: dict, D: dict) -> pd.DataFrame:
    _, fr1 = _micro()
    x25 = fr1._st()["x25"]
    cat = {f"{c['eq_id']}|{c['name']}": c for c in fr1_catalogue()["coefficients"]}
    slopes = [c for c in cat.values() if c["name"] != "const" and c.get("se") and float(c["se"]) > 0]
    hy = config.score_year()
    shocks = {f: S[f]["build"](1.0)[0] for f in S}
    shocks = {f: o["FR1"] for f, o in shocks.items() if o}

    def responses(shift):
        b, _ = run_fr1(_merge_fr1({}, shift), "S5-base")
        out = {}
        for f, o in shocks.items():
            s, _ = run_fr1(_merge_fr1(o, shift), f"S5-{f}")
            dd = derived_delta(b, s, D["rgdpnon_2025"])
            out[f] = {t: dd[(t, hy)] for t in SENS_TARGETS}
        return out

    r0 = responses({})
    rows = []
    for c in slopes:
        key = f"{c['eq_id']}|{c['name']}"
        up, dn = responses(_perturb(c, +1, x25, cat)), responses(_perturb(c, -1, x25, cat))
        for f in shocks:
            for t in SENS_TARGETS:
                a, b, z = up[f][t], dn[f][t], r0[f][t]
                rows.append({"amil": f, "amil_ad": S[f]["ad"], "hedef_id": t, "hedef_ad": HEAD[t][0], "il": hy,
                             "parametr": key, "tenlik": c["eq_title_az"], "parametr_ad": c["label_az"],
                             "deyer": float(c["value"]), "se": float(c["se"]), "cavab_baza": z, "cavab_plus_1se": a,
                             "cavab_minus_1se": b, "d_cavab_d_parametr": (a - b) / (2 * float(c["se"])),
                             "nisbi_dalgalanma": (a - b) / (2 * abs(z)) if abs(z) > 0.01 else np.nan,
                             "metod": "hədəfli ±1 SE (FR1, şok altında; 2025 düzəlişi saxlanılır)"})
    T = pd.DataFrame(rows)
    T["abs_dal"] = T["nisbi_dalgalanma"].abs()
    T["sira"] = T.groupby(["amil", "hedef_id"])["abs_dal"].rank(ascending=False, method="first")
    return T.drop(columns="abs_dal")


def downstream_parameters(S4: pd.DataFrame) -> pd.DataFrame:
    """Static ±1 SE swings of the downstream modules' coefficients (MicroUnit FRx_coef_sensitivity),
    weighted by how strongly each factor moves the component they act on (S4 importance)."""
    rows = []
    for m in ("FR3", "FR4", "FR5", "FR10", "FR12"):
        p = Path(config.MICRO_DIR) / "output" / f"{m}_coef_sensitivity.csv"
        if not p.exists():
            continue
        d = pd.read_csv(p)
        if "input" in d.columns:                                        # FR10 layout
            d = d[d["type"] == "coefficient"].rename(columns={"input": "parametr", "component": "komponent_id"})
            d["swing"] = (d["effect_high_pct"] - d["effect_low_pct"]).abs()
        else:
            comp = "component_id" if "component_id" in d.columns else "headline"
            nm = d["name"] if "name" in d.columns else d["coefficient"]
            d = d.assign(parametr=d["eq_id"] + "|" + nm.astype(str), komponent_id=d[comp], swing=d["swing_pct"].abs())
        d = d.groupby(["parametr", "komponent_id"], as_index=False).agg(swing=("swing", "max"),
                                                                       parametr_ad=("label_az", "first"))
        rows.append(d.assign(modul=m))
    if not rows:
        return pd.DataFrame()
    P = pd.concat(rows, ignore_index=True)
    C = S4[S4["seviyye"] == "komponent"][["amil", "amil_ad", "komponent_id", "komponent_ad", "ehemiyyet"]]
    X = P.merge(C, on="komponent_id", how="inner")
    X["oturme_cekili_dalgalanma"] = X["swing"] * X["ehemiyyet"]
    X["metod"] = "statik ±1 SE (MikroUnit FRx_coef_sensitivity, baza) × S4 əhəmiyyəti"
    X["sira"] = X.groupby("amil")["oturme_cekili_dalgalanma"].rank(ascending=False, method="first")
    return X[X["sira"] <= 15]


# ---------------------------------------------------------------- S6 model dispersion (same shocks, other models)
CAEM_MAP = {  # factor → (CAEM 8a shock, persistent-flow superposition?, scale(+1σ) in CAEM units)
    "brent": ("dPoil", False), "fx": ("dS", False), "partner": ("dy_f", False), "rate": ("CR", True),
    "state_inv": ("gcap_y", True), "food": ("dP", True), "import": ("dP", True), "costpush": ("dP", True)}
CONCEPTS = {"nonoil_level": ("Qeyri-neft ÜDM səviyyəsi", "%", "ru:nonoil_lvl"),
            "cpi_infl": ("İnflyasiya", "f.b.", "ru:cpi"),
            "fiscal_pct": ("Büdcə balansı (CAEM: ilkin balans)", "% ÜDM", "ru:budget_gdp"),
            "ca_pct": ("Cari hesab (MikroUnit: mal ticarəti proksisi)", "% ÜDM", "ru:tb_gdp")}
C5_KEY = {"brent": "brent10", "partner": "extdem10", "rate": "rate_m200", "state_inv": "stateinv1bn"}


def _caem_units(f: str, S: dict, D: dict, base: dict) -> float:
    s, hy = S[f]["sigma"], config.score_year()
    if f in ("brent", "fx"):
        return (np.exp(s) - 1) * 100
    if f in ("partner", "rate", "costpush"):
        return s
    if f == "state_inv":
        return S[f]["build"](1.0)[1] * D["p_inv"] / base[("fr1:gdp_n", hy)] * 100
    return D["pt_food" if f == "food" else "pt_imp"]["coef"] * s


def cross_model(S: dict, D: dict, base: dict, S1: pd.DataFrame) -> pd.DataFrame:
    rows = []
    g = S1[(S1["variant"] == "σ-şəbəkə") & (S1["k_sigma"] == 1.0)]
    for f in S:
        for con, (az, unit, tid) in CONCEPTS.items():
            for y in YEARS:
                v = g[(g["amil"] == f) & (g["hedef_id"] == tid) & (g["il"] == y)]["delta"]
                if len(v):
                    rows.append({"amil": f, "konsept": con, "konsept_ad": az, "il": y, "model": "MikroUnit zənciri (RU S1)",
                                 "deyer": float(v.iloc[0]), "vahid": unit, "miqyaslama": "+1σ birbaşa"})
    lib = config.OUTPUT / "C4_caem_shock_library.csv"
    if lib.exists():
        L = pd.read_csv(lib, usecols=["library", "shock_id", "variable", "horizon", "response"])
        L = L[L["library"] == "8a"]
        for f, (sid, persist) in CAEM_MAP.items():
            if f not in S:
                continue
            x = _caem_units(f, S, D, base)
            for con, var in (("nonoil_level", "dy_ncom"), ("cpi_infl", "dP"), ("fiscal_pct", "pb_y")):
                irf = L[(L["shock_id"] == sid) & (L["variable"] == var)].set_index("horizon")["response"].sort_index()
                if irf.empty:
                    continue
                r = irf.reindex(range(0, 13)).fillna(0.0).to_numpy()
                resp = np.cumsum(r) if persist else r                          # persistent flow = superposition
                if con == "nonoil_level":
                    resp = np.cumsum(resp)                                      # growth → level
                for h, y in enumerate(YEARS, start=1):
                    rows.append({"amil": f, "konsept": con, "konsept_ad": CONCEPTS[con][0], "il": y,
                                 "model": "Nazirlik CAEM modeli — müqayisə", "deyer": float(resp[h] * x),
                                 "vahid": CONCEPTS[con][1],
                                 "miqyaslama": f"8a `{sid}` × {x:.3g} ({'davamlı axın: IRF cəmi' if persist else 'səviyyə şoku'})"})
    c5p = config.OUTPUT / "C5_transmission_comparison.csv"
    if c5p.exists():
        C5 = pd.read_csv(c5p)
        for f, key in C5_KEY.items():
            if f not in S:
                continue
            size = S[f]["build"](1.0)[1]
            sc = {"brent": size / 10, "partner": float(D["prm"]["ext_demand_elasticity"]) * size / 10,
                  "rate": -size / 2.0, "state_inv": size / 1000}[f]
            sub = C5[(C5["shock_key"] == key) & C5["model"].str.contains("OxLon|MikroUnit FR1", regex=True)]
            for r in sub.itertuples():
                if pd.isna(r.year):
                    continue
                rows.append({"amil": f, "konsept": r.concept, "konsept_ad": r.concept_az, "il": int(r.year),
                             "model": r.model, "deyer": float(r.value) * sc, "vahid": r.unit,
                             "miqyaslama": f"C5 `{key}` × {sc:.3g} (xətti miqyas)"})
    X = pd.DataFrame(rows)
    if X.empty:
        return X
    disp = (X[X["konsept"].isin(list(CONCEPTS))].groupby(["amil", "konsept", "konsept_ad", "il", "vahid"], as_index=False)
            .agg(n_model=("deyer", "size"), min_=("deyer", "min"), max_=("deyer", "max")))
    disp = disp[disp["n_model"] >= 2]
    disp = disp.assign(model="dispersiya (modellər arası)", deyer=disp["max_"] - disp["min_"],
                       miqyaslama="max − min; n_model = " + disp["n_model"].astype(str))
    return pd.concat([X, disp.drop(columns=["n_model", "min_", "max_"])], ignore_index=True)


# ---------------------------------------------------------------- S7 daily decision table
def az(x, d=2, sign=True) -> str:
    if x is None or not np.isfinite(x):
        return "—"
    s = f"{x:+,.{d}f}" if sign else f"{x:,.{d}f}"
    return s.replace(",", " ").replace(".", ",")


ADVERSE = {"ru:nonoil_lvl": -1, "ru:cpi": +1, "ru:budget_gdp": -1, "ru:tb_gdp": -1}


def _measures_for(risks: str) -> list[str]:
    try:
        from . import measures
        m = measures.load_v2()
    except Exception:  # noqa: BLE001
        return []
    want = {r.strip() for r in str(risks).split(";")}
    hit = m[m["risk_idler"].map(lambda s: bool(want & {x.strip() for x in str(s).split(";")}))]
    eff = config.OUTPUT / "M1_measures_v2.csv"
    if eff.exists():
        e = pd.read_csv(eff)[["tedbir_id", "effekt_hedef_funksiya"]]
        hit = hit.merge(e, on="tedbir_id", how="left").sort_values("effekt_hedef_funksiya", ascending=False)
    return [f"{r.tedbir_id} ({str(r.tedbir)[:60]})" for r in hit.head(3).itertuples()]


def daily_decision(S, D, live, base, comp, S1, S5) -> pd.DataFrame:
    prm, hy = D["prm"], config.score_year()
    band = {"ru:nonoil_lvl": prm["i_nonoil_3"], "ru:cpi": prm["i_cpi_3"], "ru:budget_gdp": prm["i_fiscal_3"],
            "ru:tb_gdp": 2 * prm["i_fiscal_3"]}
    cat = micro_catalog()
    g1 = S1[(S1["variant"] == "σ-şəbəkə")]
    rows = []
    for f, spec in S.items():
        rec = {"amil": f, "amil_ad": spec["ad"], "risk_idler": spec["risk_idler"]}
        if f in live and (f, "live") in comp:
            L, fl = live[f], comp[(f, "live")]
            d = {t: fl.get(("Δ" + t, hy), np.nan) for t in ADVERSE}
            rec.update({"canli_sapma": L["tesvir"], "sigma_sapma": L["k"], "olcu": L["size"], "menbe": L["menbe"],
                        "tesir_novu": "canlı sapma (dəqiq zəncir hesabı)"})
            kk = L["k"]
            lin = g1[(g1["amil"] == f) & (g1["hedef_id"] == "ru:nonoil_lvl") & (g1["il"] == hy)]
            lin_v = np.interp(kk, lin["k_sigma"], lin["delta"]) if len(lin) and np.isfinite(kk) else np.nan
            rec["xetti_tegrib_qeyri_neft"] = lin_v
            top = []
            for i in cat.index:
                if (i, hy) in base and (i, hy) in fl and cat.at[i, "kind"] in ("level", "index") \
                        and _pct_ok(base[(i, hy)], fl[(i, hy)]) and "diaqnostika" not in str(cat.at[i, "group_az"]) \
                        and str(cat.at[i, "unit_az"]).strip() != "log":
                    top.append((abs(fl[(i, hy)] / base[(i, hy)] - 1) * 100, i))
            top.sort(reverse=True)
            rec["en_cox_tesirlenen"] = "; ".join(f"{cat.at[i, 'label_az'][:45]} ({az(v * np.sign(fl[(i, hy)] - base[(i, hy)]), 2)}%)"
                                                for v, i in top[:5])
        else:
            adv = spec["pis_istiqamet"]
            sub = g1[(g1["amil"] == f) & (g1["il"] == hy) & (g1["k_sigma"] == float(adv))]
            d = {t: (sub[sub["hedef_id"] == t]["delta"].iloc[0] if (sub["hedef_id"] == t).any() else np.nan)
                 for t in ADVERSE}
            rec.update({"canli_sapma": live_note(f, D), "sigma_sapma": np.nan, "olcu": np.nan, "menbe": "",
                        "tesir_novu": f"potensial: {'+' if adv > 0 else '−'}1σ əlverişsiz istiqamətdə", "en_cox_tesirlenen": "",
                        "xetti_tegrib_qeyri_neft": np.nan})
        rec.update({f"qeyri_neft_seviyye_{hy}_pct": d["ru:nonoil_lvl"], f"inflyasiya_{hy}_fb": d["ru:cpi"],
                    f"budce_{hy}_pct_udm": d["ru:budget_gdp"], f"ticaret_balansi_{hy}_pct_udm": d["ru:tb_gdp"]})
        adv_s = sum(max(ADVERSE[t] * d[t], 0) / band[t] for t in ADVERSE if np.isfinite(d[t]))
        fav_s = sum(max(-ADVERSE[t] * d[t], 0) / band[t] for t in ADVERSE if np.isfinite(d[t]))
        rec["elverissiz_bal"], rec["elverisli_bal"] = adv_s, fav_s
        if S5 is not None and len(S5):
            p = S5[(S5["amil"] == f) & (S5["hedef_id"] == "ru:nonoil_lvl")].nsmallest(3, "sira")
            rec["en_hessas_parametrler"] = "; ".join(f"{r.parametr} ({az(r.nisbi_dalgalanma * 100, 0)}%)" for r in p.itertuples())
        rec["teklif_olunan_tedbirler"] = "; ".join(_measures_for(spec["risk_idler"]))
        rows.append(rec)
    T = pd.DataFrame(rows)
    T["canli"] = T["tesir_novu"].str.startswith("canlı")
    T = T.sort_values(["canli", "elverissiz_bal", "elverisli_bal"], ascending=[False, False, False]).reset_index(drop=True)
    T.insert(0, "sira", np.arange(1, len(T) + 1))
    import re
    dec = lambda x: re.sub(r"(?<=\d)\.(?=\d)", ",", str(x))  # noqa: E731 — AZ decimal comma in prose
    T["canli_sapma"] = T["canli_sapma"].map(dec)
    T["qerar_qeydi"] = [dec(_note(r, hy)) for r in T.itertuples()]
    T["tarix"] = config.as_of().isoformat()
    return T.drop(columns="canli")


def _note(r, hy) -> str:
    g, c, b = (getattr(r, f"qeyri_neft_seviyye_{hy}_pct"), getattr(r, f"inflyasiya_{hy}_fb"), getattr(r, f"budce_{hy}_pct_udm"))
    head = (f"{r.amil_ad}: {r.canli_sapma}" + (f" ({az(r.sigma_sapma, 1)}σ)" if np.isfinite(r.sigma_sapma) else "") + ". "
            f"{hy}: qeyri-neft ÜDM {az(g)}%, inflyasiya {az(c)} f.b., büdcə {az(b)}% ÜDM.")
    if not r.tesir_novu.startswith("canlı"):
        act = "Ssenari elastikliyi; canlı göstərici əlavə olunmalıdır."
    elif r.elverissiz_bal >= 1.0:
        act = "QƏRAR: tədbirlərin hazırlığı (" + (r.teklif_olunan_tedbirler.split(";")[0] or "tədbir reyestri") + ")."
    elif r.elverissiz_bal >= 0.3:
        act = "İzləmə gücləndirilsin; həddə yaxınlaşma həftəlik yoxlanılsın."
    elif r.elverisli_bal >= 0.3:
        act = "Əlverişli sapma: əlavə gəlirin qənaətə yönəldilməsi (prosiklik xərc artımından çəkinmək)."
    else:
        act = "Normal izləmə."
    return head + " " + act


# ---------------------------------------------------------------- run
def sigma_table(S: dict, live: dict) -> pd.DataFrame:
    rows = []
    for f, s in S.items():
        _, one = s["build"](1.0)
        L = live.get(f, {})
        rows.append({"amil": f, "amil_ad": s["ad"], "risk_idler": s["risk_idler"], "vahid": s["vahid"],
                     "sok_novu": {"log": "log (nisbi)", "add": "əlavə (mütləq)", "hazard": "təhlükə (birtərəfli)"}[s["kind"]],
                     "sigma": s["sigma"], "sigma_esasi": s["sigma_esasi"], "n": s["n"], "olcu_1sigma": one,
                     "pis_istiqamet": "artım" if s["pis_istiqamet"] > 0 else "azalma", "oturme_kanali": s["kanal"],
                     "canli_k_sigma": L.get("k", np.nan), "canli_olcu": L.get("size", np.nan),
                     "canli_tesvir": L.get("tesvir", ""), "sok_qaydasi": s.get("sok_qaydasi", ""),
                     "qeyd": s.get("qeyd", "")})
    return pd.DataFrame(rows)


def _cache_paths(key):
    return {n: CACHE / f"{n}_{key}.csv" for n in ("S1", "S4", "S5")}


def _load_cache(key):
    p = _cache_paths(key)
    if all(v.exists() for v in p.values()):
        return tuple(pd.read_csv(p[n]) for n in ("S1", "S4", "S5"))
    return None


def _save_cache(key, S1g, S4, S5):
    CACHE.mkdir(parents=True, exist_ok=True)
    for old in CACHE.glob("S*_*.csv"):
        if key not in old.name:
            old.unlink()
    for n, df in (("S1", S1g), ("S4", S4), ("S5", S5)):
        df.to_csv(_cache_paths(key)[n], index=False)


CATALOG = {
    "S0_factor_sigma.csv": "Risk amillərinin σ vahidləri (tarixi əsas), şokun MikroUnit-ə ötürülmə kanalı və bugünkü canlı sapma (σ ilə)",
    "S1_scalability_grid.csv": "Miqyaslanma şəbəkəsi: hər amil × k ∈ {±0,5; ±1; ±2; ±3}σ + canlı sapma → MikroUnit zənciri (FR1–FR12) üzrə əsas göstəricilərin baza ilə fərqi, 2026–2030",
    "S2_elasticities.csv": "Elastikliklər: σ vahidinə və təbii vahidə düşən cavab, nisbi elastiklik (log amillər), ölçüyə görə",
    "S3_nonlinearity.csv": "Qeyri-xəttilik: ±k asimmetriyası, əyrilik, miqyas sapması, sərhəd kəsilməsi; risk iştahı və inandırıcılıq həddinin keçildiyi σ ölçüsü",
    "S4_impact_map.csv": "Təsir xəritəsi: amil (+1σ) × bütün MikroUnit komponentləri (≈1 500) və qruplar üzrə normallaşdırılmış əhəmiyyət — hansı dəyişənlər təsirlənir",
    "S5_parameter_sensitivity.csv": "Ötürməni daşıyan parametrlər: FR1 əmsallarının ±1 SE dəyişməsi şok altında cavabı necə dəyişir (d cavab / d əmsal) + aşağı axın modullarının statik həssaslığı",
    "S6_cross_model.csv": "Modellər arası dispersiya: eyni +1σ şok MikroUnit zənciri, Nazirlik CAEM (müqayisə) və OxLon həssaslıqları ilə",
    "S7_daily_decision.csv": "Gündəlik qərar cədvəli: bugünkü canlı sapmalar × elastikliklər → baş proqnozlara təsir, təsirlənən dəyişənlər, həssas parametrlər, təklif olunan tədbirlər (sıralanmış)",
}


def run(ctx: dict | None = None) -> dict:
    """Stage S (scalability). ctx keys: force (ignore cache), no_params (skip targeted S5 runs)."""
    ctx = ctx if ctx is not None else {}
    t0 = time.time()
    D = factor_data()
    S = factor_specs(D)
    live = live_deviations(S, D)
    S0 = sigma_table(S, live)
    key = engine_fingerprint() + "-" + hashlib.sha256(S0[["amil", "sigma"]].round(10).to_csv().encode()).hexdigest()[:8]
    cached = None if ctx.get("force") else _load_cache(key)
    if cached is not None:
        S1g, S4, S5 = cached
        base, S1l, comp = scan(S, D, live, grid=False)
        src = "keş"
    else:
        base, S1all, comp = scan(S, D, live)
        S1g, S1l = S1all[S1all["variant"] == "σ-şəbəkə"], S1all[S1all["variant"] == "canlı"]
        S4 = impact_map(base, comp, S)
        S5 = pd.DataFrame() if ctx.get("no_params") else parameter_sensitivity(S, D)
        S5 = pd.concat([S5, downstream_parameters(S4)], ignore_index=True)
        if not ctx.get("no_params"):
            _save_cache(key, S1g, S4, S5)
        src = "yeni hesablama"
    S1 = pd.concat([S1g, S1l], ignore_index=True)
    S2 = elasticities(S1, S)
    S3 = nonlinearity(S1, S, D)
    S6 = cross_model(S, D, base, S1)
    S7 = daily_decision(S, D, live, base, comp, S1, S5[S5["metod"].str.startswith("hədəfli")] if len(S5) else S5)
    out = {"S0_factor_sigma.csv": S0, "S1_scalability_grid.csv": S1, "S2_elasticities.csv": S2,
           "S3_nonlinearity.csv": S3, "S4_impact_map.csv": S4, "S5_parameter_sensitivity.csv": S5,
           "S6_cross_model.csv": S6, "S7_daily_decision.csv": S7}
    if not ctx.get("no_write"):
        for name, df in out.items():
            df.to_csv(config.OUTPUT / name, index=False, float_format="%.6g")
            spine.register_output(name, "riskunit.scalability", CATALOG[name], list(df.columns), "gündəlik (canlı sətirlər); "
                                  "MikroUnit mühərriki dəyişəndə tam yenidən hesablama")
    return {**{k.split(".")[0]: v for k, v in out.items()}, "key": key, "source": src,
            "n_components": int(len({i for (i, _) in base})), "seconds": round(time.time() - t0, 1)}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="RiskUnit S1–S7 miqyaslanma modeli")
    ap.add_argument("--force", action="store_true", help="keşi nəzərə alma")
    ap.add_argument("--no-params", action="store_true", help="hədəfli S5 parametr qaçışlarını burax")
    a = ap.parse_args()
    r = run({"force": a.force, "no_params": a.no_params})
    print(f"S1–S7 hazırdır ({r['source']}, {r['seconds']} s, {r['n_components']} komponent, açar {r['key']})")
    print(r["S7_daily_decision"][["sira", "amil_ad", "sigma_sapma", "elverissiz_bal", "qerar_qeydi"]].head(8).to_string())
