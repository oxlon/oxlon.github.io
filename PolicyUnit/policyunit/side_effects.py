"""FR4 — automatic side-effect generation (MİİS §15.5.4).

(1) Rules library `config/side_effect_rules.csv` (no programming to add a rule: pick a metric from
METRICS below, thresholds t1;t2;t3;t4 -> severity 1–4, an Azerbaijani explanation template).
(2) Side-effect SCENARIOS generated automatically for every policy scenario (policy under adverse
conditions: Brent −1σ, manat −1σ, weaker transmission = top Sobol drivers at −1 SE, alternative
financing) — run through the core (`integrate.run_scenario`, `eng_micro.plan`, `microbridge`).
Policy effect under a condition = (policy + condition) − (condition alone), same vintage."""
from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
import pandas as pd

from . import config, fiscal, integrate as I, microbridge as mb, registry

RULES_CSV = config.CONFIG / "side_effect_rules.csv"
RULE_COLS = ["id", "name_az", "family", "instruments", "metric", "op", "thresholds", "unit", "affected_group",
             "affected_sector", "risk_ids", "params", "tier", "template_az"]
FAMILIES = ["fiskal sürüşmə", "inflyasiya", "idxal sızması", "qeyri-formallaşma", "rent axtarışı",
            "regional disbalans", "sıxışdırma (crowding-out)", "borc dayanıqlılığı", "rəqabət/bazar gücü",
            "sosial bölgü"]
SEVERITY_AZ = {1: "aşağı", 2: "orta", 3: "yüksək", 4: "kritik"}
SE_COLS = ["scenario", "variant", "variant_name_az", "rule_id", "name_az", "family", "metric", "value", "unit",
           "low", "high", "threshold", "severity", "severity_az", "horizon", "year", "affected_group",
           "affected_sector", "risk_ids", "tier", "explanation_az"]


class RuleError(ValueError):
    pass


def az(x, nd=2) -> str:
    """Azerbaijani number format: decimal comma, thin-space thousands."""
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "—"
    s = f"{x:,.{nd}f}".replace(",", " ").replace(".", ",")
    return s


def _params(txt) -> dict:
    out = {}
    for part in filter(None, str(txt or "").split(";")):
        k, _, v = part.partition("=")
        try:
            out[k.strip()] = float(v)
        except ValueError:
            out[k.strip()] = v.strip()
    return out


def load_rules(path=None) -> pd.DataFrame:
    df = pd.read_csv(path or RULES_CSV, dtype=str, keep_default_na=False)
    miss = [c for c in RULE_COLS if c not in df.columns]
    if miss:
        raise RuleError("side_effect_rules.csv: çatışmayan sütun(lar): " + ", ".join(miss))
    errs = []
    if df["id"].duplicated().any():
        errs.append("təkrarlanan qayda id: " + ", ".join(df.loc[df["id"].duplicated(), "id"]))
    for r in df.itertuples():
        if r.family not in FAMILIES:
            errs.append(f"{r.id}: naməlum ailə '{r.family}' (mümkün: {', '.join(FAMILIES)})")
        if r.metric not in METRICS:
            errs.append(f"{r.id}: naməlum metrika '{r.metric}'")
        if r.op not in (">", "<"):
            errs.append(f"{r.id}: op yalnız '>' və ya '<' ola bilər")
        try:
            t = [float(x) for x in r.thresholds.split(";")]
            if len(t) != 4 or (t != sorted(t) if r.op == ">" else t != sorted(t, reverse=True)):
                raise ValueError
        except ValueError:
            errs.append(f"{r.id}: thresholds 4 monoton ədəd olmalıdır (t1;t2;t3;t4)")
    if errs:
        raise RuleError("side_effect_rules.csv xətaları:\n- " + "\n- ".join(errs))
    return df


class View:
    """Harmonised results of ONE scenario (variant) with the core-first fallback of the KPI module."""

    def __init__(self, f: pd.DataFrame, s: dict, extra: dict | None = None):
        self.f, self.s, self.x = f, s, extra or {}
        self.core = I.core_frame(f) if len(f) else f
        self.start = int(s["start_year"])

    def ind(self, ind, engines=("core", "caem", "io", "microsim")) -> pd.DataFrame:
        for e in engines:
            g = self.core if e == "core" else self.f[self.f.engine == e]
            g = g[g.indicator == ind] if len(g) else g
            if len(g):
                return g.sort_values("year")
        return pd.DataFrame(columns=self.f.columns)

    def prefix(self, p) -> pd.DataFrame:
        g = self.core
        return g[g.indicator.str.startswith(p)] if len(g) else g

    def hz(self, g, hz="orta"):
        h = g[g.horizon.isin(hz.split("+"))]
        return h if len(h) else g[g.horizon == "qısa"]

    def micro_years(self, g):
        return g[g.year <= config.MICRO_YEARS[-1]]

    def has(self, iid):
        return [it for it in self.s["instruments"] if it["instrument"] == iid]

    def gdp(self) -> dict:
        out = dict(fiscal.gdp_nominal())          # FR1 baseline, extended after 2030 (denominator only)
        g = self.ind("gdp_nominal", ("core",))
        out.update(dict(zip(g.year, g.baseline)))
        return out


def _res(v, year=None, **info):
    if v is None or not np.isfinite(v):
        return None
    return {"value": float(v), "year": None if year is None else int(year), **info}


# ------------------------------------------------------------------ metrics (fn(View, params) -> dict|None)
def m_fiscal_cost_gdp(V, p):
    c = V.micro_years(V.ind("fiscal_cost"))
    c = c[c.delta.abs() > 1e-9]
    if c.empty:
        return None
    gdp = V.gdp()
    v = [100 * d / gdp.get(y, np.nan) for d, y in zip(c.delta, c.year)]
    return _res(float(np.nanmean(v)), c.year.iloc[0], financing=",".join(
        sorted({str(it.get("financing") or "deficit") for it in V.s["instruments"]})))


def m_fiscal_drift_mln(V, p):
    b, c = V.micro_years(V.ind("budget_balance", ("core",))), V.micro_years(V.ind("fiscal_cost", ("core",)))
    if b.empty:
        return None
    cost = dict(zip(c.year, c.delta)) if len(c) else {}
    gap = [(-d - max(cost.get(y, 0.0), 0.0), y) for d, y in zip(b.delta, b.year) if y >= V.start]
    if not gap or max(cost.values() or [0]) <= 1e-6:
        return None                   # no ex-ante cost: balance effects are reported by SE17/SE24
    tot = sum(g for g, _ in gap)
    return _res(tot, max(gap)[1])


def m_cost_escalation_pct(V, p):
    c = V.ind("fiscal_cost", ("core",))
    c = c[c.delta > 1e-6]
    if len(c) < 3:
        return None
    gdp = V.gdp()               # escalation in % of GDP (nominal growth alone is not drift)
    r0, r1 = c.delta.iloc[0] / gdp[c.year.iloc[0]], c.delta.iloc[-1] / gdp[c.year.iloc[-1]]
    return _res(100 * (r1 / r0 - 1), c.year.iloc[-1])


def m_d_infl_max(V, p):
    g = V.ind("infl")
    if g.empty:
        return None
    i = g.delta.idxmax()
    return _res(g.delta.max(), g.loc[i, "year"])


def m_d_cpi_level(V, p):
    g = V.hz(V.ind("cpi"))
    return _res(g.delta_pct.mean(), g.year.max()) if len(g) else None


def m_import_leakage(V, p):
    m, y = V.hz(V.ind("imports_nonoil_real"), "qısa+orta"), V.hz(V.ind("gdp_nonoil_real"), "qısa+orta")
    if m.empty or y.empty or y.delta.sum() <= 1.0 or m.delta.sum() <= 0:
        return None
    return _res(m.delta.sum() / y.delta.sum(), m.loc[m.delta.idxmax(), "year"])


def m_ca_drop_gdp(V, p):
    g = V.micro_years(V.ind("ca_proxy", ("core",)))
    if g.empty:
        return None
    gdp = V.gdp()
    v = pd.Series([100 * d / gdp.get(y, np.nan) for d, y in zip(g.delta, g.year)], index=g.year.values)
    return _res(v.min(), v.idxmin())


def _hired(V):
    g = V.hz(V.ind("employment_hired", ("core",)))
    return (g.baseline.mean(), g.delta.mean()) if len(g) else (np.nan, np.nan)


def m_mw_disemployment(V, p):
    its = V.has("min_wage")
    if not its:
        return None
    size = float(its[0]["size"])
    base, fr4 = _hired(V)
    if not np.isfinite(base):
        return None
    nb = p.get("bound_share", 0.15) * base
    jobs = {k: p.get(k, d) * size * nb / 100 for k, d in (("eps_low", -0.3), ("eps_mid", -0.1), ("eps_high", 0.0))}
    k0 = k1 = np.nan
    try:
        bl = mb.baseline()
        mw, w = mb.series(bl, "FR3", "fr3:minwage"), mb.series(bl, "FR1", "fr1:wage")
        i = max(0, min(len(mw) - 1, V.start - config.MICRO_YEARS[0]))
        wg = V.ind("wage_nominal", ("core",))
        w1 = wg[wg.year == V.start].value.iloc[0] if len(wg[wg.year == V.start]) else w[i]
        k0, k1 = mw[i] / w[i], mw[i] * (1 + size / 100) / w1
    except Exception:  # noqa: BLE001 — Kaitz is informative only
        pass
    return _res(jobs["eps_mid"], V.start, low=jobs["eps_low"], high=jobs["eps_high"], kaitz0=k0, kaitz1=k1,
                fr4_jobs=fr4, inf_pct=100 * p.get("inf_share", 0.6), informal_mid=-jobs["eps_mid"] * p.get("inf_share", 0.6))


def m_tax_informality(V, p):
    its = [it for it in V.has("pit_rate") if float(it["size"]) > 0]
    if not its:
        return None
    base, _ = _hired(V)
    size = float(its[0]["size"])
    j = {k: p.get(k, d) * size * base / 100 for k, d in (("semi_low", -0.67), ("semi_mid", -0.3), ("semi_high", 0.0))}
    return _res(j["semi_mid"], V.start, low=j["semi_low"], high=j["semi_high"])


def m_d_hired_min(V, p):
    g = V.ind("employment_hired", ("core",))
    g = g[g.year >= V.start]
    return _res(g.delta_pct.min(), g.loc[g.delta_pct.idxmin(), "year"]) if len(g) else None


FR1_SEC = {"agr", "min", "man", "elc", "wat", "con", "trd", "tou", "tra", "ict", "oth"}
SEC_AZ = {"agr": "kənd təsərrüfatı", "min": "mədənçıxarma", "man": "emal sənayesi", "elc": "elektrik enerjisi",
          "wat": "su təchizatı", "con": "tikinti", "trd": "ticarət", "tou": "turizm və iaşə", "tra": "nəqliyyat",
          "ict": "informasiya və rabitə", "oth": "digər xidmətlər"}


def m_subsidy_intensity(V, p):
    its = [it for it in V.s["instruments"] if it["instrument"] in
           ("agri_subsidy", "export_subsidy", "credit_subsidy", "io_sector_demand")]
    if not its:
        return None
    it = its[0]
    sec = str(it.get("target") or "").lower()
    sec = {"agri": "agr", "manuf": "man"}.get(sec, sec)
    y = V.start
    if sec in FR1_SEC:
        va, pr = V.ind(f"sector_va:{sec}", ("core",)), V.ind(f"sector_price:{sec}", ("core",))
        va, pr = va[va.year == y], pr[pr.year == y]
        if va.empty or pr.empty:
            return None
        den, lab = va.baseline.iloc[0] * pr.baseline.iloc[0], SEC_AZ[sec]
    else:
        den, lab = V.gdp().get(y, np.nan), "bütün qeyri-neft iqtisadiyyatı"
    return _res(100 * float(it["size"]) / den, y, sector=lab)


def _mean_by(V, prefix, col="delta_pct"):
    g = V.hz(V.prefix(prefix))
    return g.groupby("indicator")[col].mean().dropna() if len(g) else pd.Series(dtype=float)


def m_d_hhi_mean(V, p):
    s = _mean_by(V, "hhi")
    return _res(s.mean(), None) if len(s) else None


def m_d_margin_max(V, p):
    s = _mean_by(V, "industry_margin:", "delta")
    return _res(s.max(), None, sector="NACE " + s.idxmax().split(":")[1]) if len(s) and s.max() > 0 else None


def m_regional_spread(V, p):
    s = _mean_by(V, "region_output:")
    if len(s) < 2:
        return None
    return _res(s.max() - s.min(), None, sector=s.idxmax().split(":", 1)[1].replace("_", " "))


def m_crowd_private_inv(V, p):
    b, s = (V.x.get("fr1_base") or {}).get("fr1:rinv_non"), (V.x.get("fr1_scen") or {}).get("fr1:rinv_non")
    if not b or not s:
        return None
    d = [(100 * (v / a - 1), y) for a, v, y in zip(b, s, config.MICRO_YEARS) if y >= V.start + 2 or y == config.MICRO_YEARS[-1]]
    return _res(float(np.mean([x for x, _ in d])), d[-1][1]) if d else None


def m_sector_loser_min(V, p):
    g = V.hz(V.ind("gdp_real", ("core",)))
    s = _mean_by(V, "sector_va:")
    if g.empty or g.delta_pct.mean() <= 0 or s.empty:
        return None
    k = s.idxmin().split(":")[1]
    return _res(s.min(), None, sector=SEC_AZ.get(k, k))


def m_d_debt_end(V, p):
    g = V.ind("debt_pct")
    return _res(g.delta.iloc[-1], g.year.iloc[-1]) if len(g) else None


def m_sofaz_drawdown(V, p):
    g = V.ind("sofaz_assets", ("core",))
    return _res(g.delta.min(), g.loc[g.delta.idxmin(), "year"]) if len(g) else None


def m_d_real_income(V, p):
    g = V.hz(V.ind("hh_disp_real", ("core",)))
    return _res(g.delta_pct.mean(), g.year.max()) if len(g) else None


def m_fixed_income_loss(V, p):
    if V.has("pension_index") or V.has("tsa_benefit"):
        return None
    g = V.ind("cpi")
    g = g[g.horizon == "qısa"]
    return _res(-g.delta_pct.max(), g.loc[g.delta_pct.idxmax(), "year"]) if len(g) else None


def m_d_gini(V, p):
    g = V.ind("gini", ("microsim",))
    return _res(g.delta.max(), g.loc[g.delta.idxmax(), "year"]) if len(g) else None


def m_d_poverty(V, p):
    g = V.ind("poverty_rate", ("microsim",))
    return _res(g.delta.max(), g.loc[g.delta.idxmax(), "year"]) if len(g) else None


def _risk(kind):
    def f(V, p):
        r = V.x.get("risk")
        if r is None or r.empty:
            return None
        g = r[(r.kind == kind) & (r.variant == V.x.get("variant", "base")) & (r.year >= V.start)].dropna(subset=["dP"])
        return _res(g.dP.max(), g.loc[g.dP.idxmax(), "year"]) if len(g) else None
    return f


def m_fx_debt_reval(V, p):
    its = [it for it in V.has("fx_deval") if float(it["size"]) > 0]
    return _res(float(its[0]["size"]) * p.get("fx_debt_gdp", 0.10), V.start) if its else None


METRICS = {k[2:]: v for k, v in dict(globals()).items() if k.startswith("m_") and callable(v)}
METRICS.update({"risk_dP_cpi": _risk("cpi"), "risk_dP_fis": _risk("fis"), "risk_dP_g": _risk("g")})


# ------------------------------------------------------------------ rule evaluation
class _Safe(defaultdict):
    def __missing__(self, k):
        return "—"


def _applies(rule, s) -> bool:
    want = str(rule["instruments"]).strip()
    if want in ("", "*"):
        return True
    ids = {it["instrument"] for it in s["instruments"]}
    return bool(ids & set(want.split(";")))


def _severity(v, op, th) -> int:
    return sum(1 for t in th if (v > t if op == ">" else v < t))


def evaluate(s: dict, f: pd.DataFrame, extra: dict | None = None, rules: pd.DataFrame | None = None,
             variant=("base", "əsas ssenari")) -> list[dict]:
    rules = load_rules() if rules is None else rules
    extra = dict(extra or {}, variant=variant[0])
    V = View(f, s, extra)
    tgt = ",".join(str(it.get("target")) for it in s["instruments"] if it.get("target")) or "—"
    out = []
    for _, r in rules.iterrows():
        if not _applies(r, s):
            continue
        p = _params(r["params"])
        try:
            res = METRICS[r["metric"]](V, p)
        except Exception as e:  # noqa: BLE001 — one metric must not stop the review
            res = None
            extra.setdefault("errors", []).append(f"{r['id']}: {type(e).__name__}: {e}")
        if res is None:
            continue
        th = [float(x) for x in r["thresholds"].split(";")]
        sev = _severity(res["value"], r["op"], th)
        if sev == 0:
            continue
        yr = res.get("year")
        hz = I.horizon(yr, s["start_year"]) if yr else "orta"
        fill = _Safe(None, {k: (az(v) if isinstance(v, float) else v) for k, v in res.items()})
        fill.update(year=yr or "—", horizon={"qısa": "qısa", "orta": "orta", "uzun": "uzun"}[hz],
                    unit=r["unit"], scenario=s["name_az"], target=tgt)
        sector = str(r["affected_sector"]).replace("{target}", tgt).format_map(fill)
        out.append({"scenario": s["id"], "variant": variant[0], "variant_name_az": variant[1], "rule_id": r["id"],
                    "name_az": r["name_az"], "family": r["family"], "metric": r["metric"],
                    "value": round(res["value"], 4), "unit": r["unit"], "low": res.get("low"), "high": res.get("high"),
                    "threshold": th[0], "severity": sev, "severity_az": SEVERITY_AZ[sev], "horizon": hz, "year": yr,
                    "affected_group": str(r["affected_group"]).format_map(fill), "affected_sector": sector,
                    "risk_ids": r["risk_ids"], "tier": r["tier"],
                    "explanation_az": str(r["template_az"]).format_map(fill)})
    return out


# ------------------------------------------------------------------ automatic side-effect scenarios
SIGMA_FALLBACK = {"brent": 0.2952, "fx": 0.1524}       # RiskUnit stress/inputs σ (log), cached fallback
VARIANT_ENGINES = ["micro", "caem", "io", "longrun"]   # microsim/oxlon skipped in variants (run time)
FIN_ALT = {"deficit": "tax", "sofaz": "deficit", "tax": "deficit", "reallocation": "deficit"}


def _yr_path(x, start):
    return [x if y >= start else 0.0 for y in config.MICRO_YEARS]


def variant_specs(s: dict, drivers: dict | None = None, sigma: dict | None = None) -> list[dict]:
    from . import eng_micro
    sig = dict(SIGMA_FALLBACK, **(sigma or {}))
    st, out = int(s["start_year"]), []
    try:
        handled = eng_micro.plan(s)["handled"]
    except Exception:  # noqa: BLE001
        handled = []
    if handled:
        b = 100 * (math.exp(-sig["brent"]) - 1)
        out.append({"id": "oil_m1s", "name_az": f"Brent neft qiyməti −1σ ({az(b, 1)} %, {st}-dən)", "kind": "micro_cond",
                    "cond": {"FR1": {"exogenous": {"brent": {"pct": _yr_path(b, st)}}}},
                    "ru": {"shocks": [{"factor": "brent", "k_sigma": -1}]}})
    if not any(it["instrument"] == "fx_deval" for it in s["instruments"]):
        d = round(100 * (math.exp(sig["fx"]) - 1), 1)
        out.append({"id": "fx_p1s", "name_az": f"Manatın devalvasiyası +1σ ({az(d, 1)} %, {st}-dən)", "kind": "scenario_cond",
                    "instrument": {"instrument": "fx_deval", "years": "all", "size": d, "unit": "pct",
                                   "target": None, "financing": None},
                    "ru": {"shocks": [{"factor": "fx", "size": d}]}})
    if drivers and handled:
        out.append({"id": "weak_coef", "kind": "micro_coef", "coefs": drivers,
                    "name_az": "Zəif ötürmə: ən təsirli 3 əmsal əlverişsiz istiqamətdə 1 SE (" + ", ".join(drivers) + ")"})
    cat = registry.instruments()
    alt, changed = [], False
    for it in s["instruments"]:
        it = dict(it)
        if cat.loc[it["instrument"], "cost_rule"] != "none":
            new = FIN_ALT.get(it.get("financing") or "deficit")
            changed = changed or bool(new)
            it["financing"] = new or it.get("financing")
        alt.append(it)
    if changed:
        fin = ", ".join(sorted({str(it["financing"]) for it in alt}))
        out.append({"id": "fin_alt", "kind": "scenario_alt", "instruments": alt,
                    "name_az": f"Alternativ maliyyələşmə ({fin})"})
    return out


def _merge(a: dict, b: dict) -> dict:
    out = {m: {k: dict(v) if isinstance(v, dict) else v for k, v in d.items()} for m, d in a.items()}
    for m, d in b.items():
        for k, v in d.items():
            out.setdefault(m, {}).setdefault(k, {}).update(v)
    return out


def _diff(f2: pd.DataFrame, f3: pd.DataFrame) -> pd.DataFrame:
    """Policy effect under a condition: value(policy+cond) − value(cond); cond-free engines keep baseline."""
    from .engine_base import NO_PCT, is_rate
    keys = ["engine", "indicator", "year"]
    m = f2.merge(f3[keys + ["value"]].rename(columns={"value": "_c"}), on=keys, how="left")
    m["baseline"] = m["_c"].where(m["_c"].notna(), m["baseline"])
    m["delta"] = m["value"] - m["baseline"]
    rate = m["unit"].map(is_rate)
    pct = 100 * m["delta"] / m["baseline"].abs().where(m["baseline"].abs() > 0)
    m["delta_pct"] = np.where(rate, m["delta"], pct)
    m.loc[m.indicator.isin(NO_PCT), "delta_pct"] = np.nan
    return m.drop(columns="_c")


def _meta(r, key):
    res = r["results"].get("micro")
    return res.meta.get(key) if res is not None else None


def run_variant(s: dict, v: dict, base_frame: pd.DataFrame) -> dict:
    from . import eng_micro, micro_harmonise as H, micro_overlay, scenario as scn
    from .engine_base import Result
    if v["kind"] in ("micro_cond", "micro_coef"):
        m = eng_micro.plan(s)
        cond = v.get("cond") or {}
        if v["kind"] == "micro_coef":
            cond = {}
            for k, val in v["coefs"].items():
                cond = _merge(cond, {k.split(".")[0]: {"coefficients": {k: val}}})
        ov = eng_micro.make_overlay(m)
        note = "yan təsir ssenarisi: " + v["name_az"]
        try:
            c_only = _merge({mod: {"levers": lv} for mod, lv in m["struct_levers"].items()}, cond)
            b, sc = mb.run(c_only), mb.run(_merge(m["overrides"], cond), overlay=ov)
            rows = H.rows(b, sc, eng_micro.METHOD, "D", note)
        except (TypeError, ValueError, mb.MicroOverrideError):
            if v["kind"] != "micro_coef":
                raise
            from .sensitivity import candidates         # 1 SE is in the unstable region: use 0.5 SE
            base = {c["key"]: c["value"] for c in candidates()}
            cond = {}
            for k, val in v["coefs"].items():
                cond = _merge(cond, {k.split(".")[0]: {"coefficients": {k: base[k] + 0.5 * (val - base[k])}}})
            note += " — 1 SE-də zəncir dinamik qeyri-sabitdir (P4_instability.csv), 0,5 SE istifadə olunub"
            c_only = _merge({mod: {"levers": lv} for mod, lv in m["struct_levers"].items()}, cond)
            b, sc = mb.run(c_only), mb.run(_merge(m["overrides"], cond), overlay=ov)
            rows = H.rows(b, sc, eng_micro.METHOD, "D", note)
        fr = I.combine(s, {"micro": Result("micro", pd.DataFrame(rows))})
        keep = base_frame[(base_frame.engine == "micro") & base_frame.indicator.isin(["fiscal_cost", "sofaz_assets"])]
        return {"frame": pd.concat([fr, keep], ignore_index=True),
                "extra": {"fr1_base": eng_micro._fr1(b), "fr1_scen": eng_micro._fr1(sc)}}
    if v["kind"] == "scenario_cond":
        s2 = scn.normalise(dict(s, instruments=list(s["instruments"]) + [v["instrument"]]))
        s3 = scn.normalise(dict(s, instruments=[v["instrument"]]))
        r2, r3 = I.run_scenario(s2, VARIANT_ENGINES), I.run_scenario(s3, VARIANT_ENGINES)
        fr = _diff(r2["frame"], r3["frame"])
        fr = fr[fr.engine.isin(I.engines_for_scenario(s))]        # engines that carry the policy itself
        return {"frame": fr, "extra": {"fr1_base": _meta(r3, "fr1_scen"), "fr1_scen": _meta(r2, "fr1_scen")}}
    s4 = dict(s, instruments=v["instruments"])
    r = I.run_scenario(s4, [e for e in I.engines_for_scenario(s4) if e in VARIANT_ENGINES])
    return {"frame": r["frame"], "extra": {"fr1_base": _meta(r, "fr1_base"), "fr1_scen": _meta(r, "fr1_scen")}}


# ------------------------------------------------------------------ public per-scenario entry point (stage + API)
def _hired_base(frame):
    g = I.core_frame(frame)
    g = g[(g.indicator == "employment_hired") & (g.horizon == "orta")]
    return float(g.baseline.mean()) if len(g) else np.nan


def variant_table(s, frame, vres, specs) -> list[dict]:
    rows = []
    hb = I.headline(frame.assign(scenario=s["id"]))
    for v in specs:
        if v["id"] not in vres:
            continue
        hv = I.headline(vres[v["id"]]["frame"].assign(scenario=s["id"], scenario_name=s["name_az"]))
        if hv.empty or hb.empty:
            continue
        m = hb.merge(hv[["indicator", "horizon", "effect"]], on=["indicator", "horizon"], how="inner",
                     suffixes=("_base", "_variant"))
        for r in m.itertuples():
            rows.append({"scenario": s["id"], "variant": v["id"], "variant_name_az": v["name_az"], "kind": v["kind"],
                         "indicator": r.indicator, "label_az": r.label_az, "horizon": r.horizon,
                         "effect_unit": r.effect_unit, "effect_base": r.effect_base,
                         "effect_variant": r.effect_variant, "change": r.effect_variant - r.effect_base})
    return rows


def analyse(scenario: dict, frame: pd.DataFrame | None = None, ctx: dict | None = None, mode: str = "full") -> dict:
    """FR4 for ONE scenario. scenario = normalised dict (scenario.load); frame = its P1 rows (all engines;
    None -> integrate.run_scenario). mode "rules": rule library on the base results only (fast, no RiskUnit,
    no variants, no sensitivity); "full": + sensitivity, side-effect scenarios, RiskUnit profile, mitigation.
    ctx (all optional): client (risk_link.Client; default Client() — no server start), evaluator
    (sensitivity.Evaluator; None -> cached sensitivity only), rules, mitigation_map, sigma, log.
    Returns {"scenario", "mode", "side_effects", "variant_table", "risk_profile", "mitigation", "kpi_inputs",
    "sensitivity", "variants", "status"}."""
    from . import risk_link as RL, sensitivity as SN
    if mode not in ("full", "rules"):
        raise ValueError("mode yalnız 'full' və ya 'rules' ola bilər")
    ctx, s = dict(ctx or {}), scenario
    log = ctx.get("log") or (lambda *_: None)
    rules = ctx.get("rules") if ctx.get("rules") is not None else load_rules()
    if frame is None or len(frame) == 0:
        frame = I.run_scenario(s)["frame"]
    rm = I.run_scenario(s, ["micro"])
    mm = rm["results"].get("micro")
    extra = {"fr1_base": mm.meta.get("fr1_base"), "fr1_scen": mm.meta.get("fr1_scen")} if mm else {}
    out = {"scenario": s["id"], "mode": mode, "variant_table": [], "risk_profile": pd.DataFrame(columns=RL.RISK_COLS),
           "mitigation": pd.DataFrame(columns=RL.MIT_COLS), "sensitivity": None, "variants": [], "status": {}}
    if mode == "rules":
        se = evaluate(s, frame, extra, rules)
        for x in se:
            x["change_vs_base"] = ""
        out.update(side_effects=se, kpi_inputs=[{"scenario": s["id"], "kpi": "side_effects", "value": float(len(se))}])
        out["status"]["riskunit"] = "istifadə edilmir (rules rejimi)"
        return out
    c = ctx.get("client") or RL.Client()
    mmap = ctx.get("mitigation_map") if ctx.get("mitigation_map") is not None else RL.load_map()
    sig = ctx.get("sigma") or RL.sigma(c)
    se08 = _params(rules.set_index("id").loc["SE08", "params"]) if "SE08" in set(rules.id) else {}
    sens = SN.run(s, ctx.get("evaluator"), _hired_base(frame), se08, log)
    specs = variant_specs(s, sens["drivers"], sig)
    vres = {}
    for v in specs:
        try:
            vres[v["id"]] = run_variant(s, v, frame)
        except Exception as e:  # noqa: BLE001 — a failed variant must not stop the review
            out["status"][f"variant:{v['id']}"] = f"alınmadı — {type(e).__name__}: {e}"
    ov = mm.meta.get("overrides") if mm else None
    pnote = ("RiskUnit sürüşməsi overlay/proksi kanallarını görmür — PolicyUnit çarpaz yoxlamasına (_pu) baxın"
             if mm and (mm.meta.get("proxy") or mm.meta.get("overlay")) else "")
    prof = RL.profile(c, s, frame, ov, specs, {k: r["frame"] for k, r in vres.items()}, note=pnote)
    se = evaluate(s, frame, {**extra, "risk": prof}, rules)
    for x in se:
        x["change_vs_base"] = ""
    sev0 = {x["rule_id"]: x["severity"] for x in se}
    for v in specs:
        if v["id"] not in vres:
            continue
        for x in evaluate(s, vres[v["id"]]["frame"], {**vres[v["id"]]["extra"], "risk": prof}, rules,
                          (v["id"], v["name_az"])):
            b0 = sev0.get(x["rule_id"])                     # keep only what the condition changes
            if b0 is None or b0 != x["severity"]:
                x["change_vs_base"] = "yeni" if b0 is None else "güclənir" if x["severity"] > b0 else "zəifləyir"
                se.append(x)
    mit = RL.mitigate(c, s, se, prof, mmap)
    fin = RL.financing_proposal(s, se)
    if fin:
        mit = pd.concat([mit, pd.DataFrame(fin, columns=RL.MIT_COLS)], ignore_index=True)
    out.update(side_effects=se, variant_table=variant_table(s, frame, vres, specs), risk_profile=prof,
               mitigation=mit, kpi_inputs=RL.kpi_inputs(s["id"], se, prof, s["start_year"]), sensitivity=sens,
               variants=[v["id"] for v in specs if v["id"] in vres])
    out["status"]["riskunit"] = prof["status"].iloc[0] if len(prof) else "—"
    out["status"]["sensitivity"] = "keş" if sens.get("cached") else "hesablandı"
    return out
