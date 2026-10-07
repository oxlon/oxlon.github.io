"""NFR1 — model predictions of historical policy effects (one function per method).

The MicroUnit chain only runs 2026–2030 and its coefficients are full-sample estimates, so a
historical event is re-played as a TRANSPLANTED SHOCK: the event's instrument path (derived from
data: annual-average minimum wage, AMB exchange rate, IO fuel shock) is applied from 2026 and the
response in year h (scenario − baseline of the same vintage) is the prediction for event year
y0 + h. Every method returns {pred, lo, hi, tier, note_az} or None (not applicable)."""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import pandas as pd

from . import config, microbridge as mb
from . import nfr1_data as D

Y = config.MICRO_YEARS
OFFSET = 1   # event year y0 <-> chain year Y[1] = 2027: 2026 is a nowcast-anchored year in FR3
METHOD_LABEL_AZ = {
    "micro_chain": "MikroUnit struktur zənciri (köçürülmüş şok)",
    "e2_direct": "MikroUnit FR1 E2 tənliyi (birbaşa, qismən tarazlıq)",
    "fr3_direct": "MikroUnit FR3 E4 dövlət sektoru tənliyi (birbaşa)",
    "io_price": "IO qiymət modeli (Leontief, tam ötürmə)",
    "io_e7": "IO qiymət modeli — E7 xüsusi şoku (IO agenti)",
    "caem": "Nazirlik CAEM modeli — müqayisə",
    "microsim": "Ev təsərrüfatı mikrosimulyasiyası (SİNTETİK)",
}
# methods whose parameters were NOT fitted on the event (row in-sample flag overridden): microsimulation
# calibrated to 2018 / 2024 aggregates and predicting 2019 / 2025; IO = fixed benchmark-table coefficients
METHOD_SAMPLE = {"microsim": "xeyr", "io_price": "xeyr", "io_e7": "xeyr"}
# coefficients behind each chain response (relative s.e. combined in quadrature; covariances ignored)
CHAIN_COEF = {
    "mw": {"wage_growth": ["FR1.E2_wage|ln_minwage"],
           "rwage_growth": ["FR1.E2_wage|ln_minwage", "FR1.G4_infl|dln_wage"],
           "did_wage": ["FR3.E4_w_state|ln_rmw"],
           "infl": ["FR1.E2_wage|ln_minwage", "FR1.G4_infl|dln_wage"],
           "gdp_nonoil_growth": ["FR1.E2_wage|ln_minwage", "FR1.D1_cons|ln_hhdisp_pc"]},
    "fx": {k: ["FR1.G4_infl|dln_fx+dln_fx_L1"] for k in ("infl", "cpi_cum", "rwage_growth")},
}


def coef(key: str) -> tuple[float, float]:
    """'FR1.G4_infl|a+b' -> (value, s.e.) from the live MicroUnit catalogue (sum: s.e. in quadrature)."""
    eq, names = key.split("|")
    cat = mb.catalogue(eq.split(".")[0])["coefficients"]
    v, s2 = 0.0, 0.0
    for nm in names.split("+"):
        c = next(c for c in cat if c["eq_id"] == eq and c["name"] == nm)
        v += float(c["value"])
        s2 += float(c["se"]) ** 2 if c["se"] not in (None, "") else math.nan   # restricted: no s.e.
    return v, math.sqrt(s2)


def rel_se(keys) -> float:
    """Combined relative s.e.; coefficients fixed by restriction (no s.e.) are skipped."""
    r = [(s / v) ** 2 for v, s in (coef(k) for k in keys) if math.isfinite(s) and v]
    return math.sqrt(sum(r)) if r else math.nan


# ------------------------------------------------------------------ shocks (from data)
def shock(ev: pd.Series) -> dict:
    kind, arg = ev["shock"].split("=", 1)
    y0 = int(ev["event_start"])
    if kind == "mw_avg":
        m = D.mw_annual()
        dev = [100 * (m.get(y0 + h, m.iloc[-1]) / m[y0 - 1] - 1) for h in range(len(Y))]
        return {"type": "mw", "dev": dev, "dlnmw": {int(t): math.log(m[t] / m[t - 1]) for t in m.index[1:]},
                "desc_az": f"minimum əmək haqqı (illik orta) {m[y0 - 1]:.1f} AZN əks-faktuala nisbətən"}
    if kind == "fx_avg":
        f = D.fx_annual()
        dev = [100 * (f.get(y0 + h, f.iloc[-1]) / f[y0 - 1] - 1) for h in range(len(Y))]
        return {"type": "fx", "dev": dev, "desc_az": f"AZN/USD {f[y0 - 1]:.4f} (y0−1) səviyyəsinə nisbətən"}
    if kind == "fuel_from":
        f = D.io_e7()
        size = float(f.loc[arg.split(":", 1)[1], "model_pct"]) if not f.empty else math.nan
        return {"type": "fuel", "dev": [size] * len(Y), "desc_az": "ev təsərrüfatı yanacaq qiyməti (IO E7 qarışığı)"}
    raise ValueError(f"naməlum şok '{ev['shock']}'")


def _mw_overrides(dev):
    m = mb.series(mb.baseline(), "FR3", "fr3:minwage")
    m0 = m[0] ** 2 / m[1]
    new = [mi * (1 + d / 100) for mi, d in zip(m, dev)]
    g = [100 * (new[i] / (new[i - 1] if i else m0) - 1) for i in range(len(Y))]
    return {"FR1": {"exogenous": {"minwage": {"pct": dev}}}, "FR3": {"levers": {"mw_growth": g}}}


def _fuel_scenario(size):
    return {"id": "nfr1_e7", "name_az": "NFR1 E7 yanacaq", "description_az": "", "start_year": Y[OFFSET],
            "tags": [], "instruments": [{"instrument": "fuel_price", "years": list(Y[OFFSET:]), "size": size,
                                         "unit": "pct", "target": None, "financing": None}]}


@lru_cache(maxsize=16)
def _chain(event_id: str, shock_spec: str, y0: int):
    sh = shock(pd.Series({"shock": shock_spec, "event_start": y0}))
    if sh["type"] == "fuel":
        from . import eng_micro
        r = eng_micro.run(_fuel_scenario(sh["dev"][0]), {})
        b, s = r.meta["fr1_base"], r.meta["fr1_scen"]
        return sh, (lambda mod, sid: (b.get(sid), s.get(sid)))
    dev = [0.0] * OFFSET + sh["dev"][:len(Y) - OFFSET]
    ov = _mw_overrides(dev) if sh["type"] == "mw" else {"FR1": {"exogenous": {"fx": {"pct": dev}}}}
    base, scen = mb.baseline(), mb.run(ov)
    return sh, (lambda mod, sid: (mb.series(base, mod, sid), mb.series(scen, mod, sid)))


CHAIN_SERIES = {"wage_growth": ("FR1", "fr1:wage", "g"), "rwage_growth": ("FR1", "fr1:rwage", "g"),
                "gdp_nonoil_growth": ("FR1", "fr1:rgdpnon", "g"), "infl": ("FR1", "fr1:infl", "pp"),
                "cpi_cum": ("FR1", "fr1:cpi", "lvl"), "cpi_dec": ("FR1", "fr1:cpi", "lvl"),
                "emp_nonstate_growth": ("FR4", "fr4:nonstate", "g")}


def _resp(get, mod, sid, how, h):
    b, s = get(mod, sid)
    if b is None or s is None:
        return math.nan
    if how == "pp":
        return s[h] - b[h]
    d = [si / bi - 1 for bi, si in zip(b, s)]
    if how == "lvl":
        return 100 * d[h]
    return 100 * ((1 + d[h]) / (1 + (d[h - 1] if h else 0.0)) - 1)


def _band(pred, rel):
    if not math.isfinite(rel):
        return math.nan, math.nan
    return pred - 1.96 * rel * abs(pred), pred + 1.96 * rel * abs(pred)


def m_micro_chain(row):
    h = int(row["year"]) - int(row["event_start"]) + OFFSET
    sh, get = _chain(row["event_id"], row["shock"], int(row["event_start"]))
    ind = row["indicator"]
    if ind == "did_wage":
        pred = _resp(get, "FR3", "fr3:w_state", "g", h) - _resp(get, "FR3", "fr3:w_priv", "g", h)
    elif ind in CHAIN_SERIES:
        pred = _resp(get, *CHAIN_SERIES[ind], h)
    else:
        return None
    lo, hi = _band(pred, rel_se(CHAIN_COEF.get(sh["type"], {}).get(ind, [])))
    note = (f"şok: {sh['desc_az']}; zəncir ili {Y[h]} ↔ {row['year']}; struktur cari vintajdır"
            + ("; overlay proksisi (D), statistik interval yoxdur" if sh["type"] == "fuel" else ""))
    return {"pred": pred, "lo": lo, "hi": hi, "tier": "D" if sh["type"] == "fuel" else "C", "note_az": note}


def _direct(row, key, ind_ok):
    if row["indicator"] != ind_ok:
        return None
    sh = shock(row)
    d = sh.get("dlnmw", {}).get(int(row["year"]), math.nan)
    b, se = coef(key)
    f = lambda bb: 100 * (math.exp(bb * d) - 1)  # noqa: E731
    if not math.isfinite(se):
        return {"pred": f(b), "lo": math.nan, "hi": math.nan, "tier": "C",
                "note_az": f"elastiklik {b:.3f} (məhdudiyyətlə sabitlənib, s.x. yoxdur) × Δln(min. əmək haqqı) {d:.3f}"}
    return {"pred": f(b), "lo": f(b - 1.96 * se), "hi": f(b + 1.96 * se), "tier": "C",
            "note_az": f"elastiklik {b:.3f} (s.x. {se:.3f}) × Δln(min. əmək haqqı) {d:.3f}"}


def m_e2_direct(row):
    return _direct(row, "FR1.E2_wage|ln_minwage", "wage_growth")


def m_fr3_direct(row):
    r = _direct(row, "FR3.E4_w_state|ln_rmw", "did_wage")
    if r:
        r["note_az"] += "; qeyri-dövlət sektoru elastikliyi 0 qəbul edilir (MikroUnit-də əhəmiyyətsiz)"
    return r


@lru_cache(maxsize=4)
def _io_cpi_per_pct(table: int) -> float:
    from . import eng_io
    s = {"id": "nfr1_fx", "name_az": "", "start_year": Y[0], "instruments": [
        {"instrument": "fx_deval", "years": [Y[0]], "size": 10.0, "unit": "pct", "target": None, "financing": None}]}
    f = eng_io.run(s, {"io_table": table, "years": [Y[0]]}).frame
    return float(f.loc[f.indicator == "io_cpi", "delta_pct"].iloc[0]) / 10.0


def m_io_price(row):
    if row["indicator"] != "cpi_cum":
        return None
    sh = shock(row)
    size = sh["dev"][int(row["year"]) - int(row["event_start"])]
    v = {t: _io_cpi_per_pct(t) * size for t in (2016, 2021, 2025)}
    return {"pred": float(v[2016]), "lo": float(min(v.values())), "hi": float(max(v.values())), "tier": "D",
            "note_az": f"AZN/USD +{size:.1f} % idxal qiymətlərinə tam ötürmə; mərkəz 2021→2016 GRAS cədvəli, "
                       f"interval 2016/2021/2025 cədvəlləri"}


SENS_COL = {"cpi_total_pack": "cpi_package_pp", "other_transport": "other_transport_pct"}


def m_io_e7(row):
    f = D.io_e7()
    ind = row["series"].split(":", 1)[1]
    if f.empty or ind not in f.index:
        return None
    lo = hi = math.nan
    p = config.OUTPUT / "V_io_e7_sensitivity.csv"
    if ind in SENS_COL and p.exists():
        s = pd.read_csv(p)[SENS_COL[ind]]
        lo, hi = float(s.min()), float(s.max())
    return {"pred": float(f.loc[ind, "model_pct"]), "lo": lo, "hi": hi, "tier": "D",
            "note_az": str(f.loc[ind, "note_az"])}


def m_caem(row):
    if row["indicator"] != "cpi_dec":
        return None
    from . import integrate
    sh = shock(row)
    r = integrate.run_scenario(_fuel_scenario(sh["dev"][0]), engines=["caem"])
    f = r["frame"]
    g = f[(f.engine == "caem") & (f.indicator == "cpi") & (f.year == Y[OFFSET])]
    if g.empty:
        return None
    return {"pred": float(g["delta_pct"].iloc[0]), "lo": math.nan, "hi": math.nan, "tier": "D",
            "note_az": "CAEM dP xərc şoku = birbaşa İQİ təsiri; yalnız yanacaq (tariflər yoxdur)"}


MS_2019 = ("V_microsim_2019_package.csv", "2019 orta illik qaydalar")
MS_2025 = ("V_microsim_2025_minwage.csv", "yalnız minimum əmək haqqı")
MS_MAP = {"poverty": [("poverty_rate", 1)], "wage_growth": [("wage_avg", 1)],
          "did_wage": [("wage_state", 1), ("wage_nonstate", -1)],
          "emp_nonstate_growth": [("nonstate_employees", 1)]}


def _ms_val(fname, variant, ind, col="model_static"):
    r = D.ms_row(f"ms:{fname}|{variant}|{ind}")
    if r is None:
        return math.nan
    if col == "model_static" and "model_behavioural" in r and pd.notna(r.get("model_behavioural")):
        col = "model_behavioural"
    return float(r[col]) if pd.notna(r[col]) else math.nan


def m_microsim(row):
    """Reads the microsimulation agent's NFR1 files (owner: microsim) — no re-run here."""
    note = "SİNTETİK — real ev təsərrüfatı məlumatı deyil. "
    if row["kind"] == "ms_file":
        r = D.ms_row(row["series"])
        if r is None:
            return None
        return {"pred": float(r["model_static"]) - float(r["naive_trend"]), "lo": math.nan, "hi": math.nan,
                "tier": "D", "note_az": note + "2024 paylanması → 2025, yalnız minimum əmək haqqı (statik)"}
    fname, variant = MS_2019 if int(row["year"]) == 2019 else MS_2025
    ind = row["indicator"]
    if int(row["year"]) != 2019:
        if ind != "wage_growth":
            return None
        v = _ms_val(fname, variant, "orta əmək haqqı (%)")
        parts = [v]
    else:
        if ind not in MS_MAP:
            return None
        parts = [k * _ms_val(fname, variant, i) for i, k in MS_MAP[ind]]
    pred = float(sum(parts))
    if not math.isfinite(pred):
        return None
    beh = ind == "emp_nonstate_growth"
    return {"pred": pred, "lo": math.nan, "hi": math.nan, "tier": "D",
            "note_az": note + ("davranış qatı (formallaşma)" if beh else "statik ilk dövrə təsiri (yayılma yoxdur)")}


METHODS = {k: globals()["m_" + k] for k in METHOD_LABEL_AZ}
