"""Engine `microsim` — household tax-benefit microsimulation (FR3: employment, income
distribution / Gini, poverty). run(scenario, ctx) -> Result (OUT_COLS).

Static first-round incidence on the calibrated household file (SYNTHETIC unless the Ministry's
HBS file is loaded — see hh_data). Instruments are translated through config/adapters.csv
rows with engine = microsim (target_key grammar: `param:<tax_benefit param>`,
`pol:<policy key>[:<sub>]`, or transform `custom:<fn>` = function `c_<fn>` below).
Macro/IO linkage (ms_links): MicroUnit FR4 hired jobs by sector and FR1 wage, IO prices."""
from __future__ import annotations

import time
from functools import lru_cache

import numpy as np
import pandas as pd

from . import config, hh_data, ms_links, ms_uprate
from . import ms_policy as MP
from . import ms_targets as MT
from .engine_base import Result, row
from .ms_indicators import indicators
from .taxben import Params

ENGINE = "microsim"
YEARS = range(2024, 2031)
DIRECT = {"min_wage", "pension_index", "tsa_benefit", "tsa_need", "min_pension", "pit_rate",
          "pit_nonoil_private", "ssc_employee", "public_wage", "vat_rate", "consumer_price",
          "fuel_price", "utility_tariff", "fx_deval", "import_tariff", "agri_subsidy",
          "sector_jobs"}


@lru_cache(maxsize=1)
def base():
    p, cal, synth = hh_data.load()
    return MP.prepare(p), cal, synth, MT.load(int(cal["base_year"]))


@lru_cache(maxsize=8)
def year_state(year):
    p, cal, synth, T = base()
    q, c = ms_uprate.project(p, cal, T, year)
    return q, c


def adapters():
    try:
        a = pd.read_csv(config.ADAPTERS_CSV, dtype=str, keep_default_na=False)
        a = a[a.engine == ENGINE]
    except FileNotFoundError:
        a = pd.DataFrame(columns=["instrument", "engine", "target_key", "transform", "note_az"])
    return a


def _years(it, start):
    y = it.get("years", "all")
    return list(range(start, config.LONG_END + 1)) if y == "all" else [int(v) for v in y]


def translate(s, year, ctx=None):
    """Scenario instruments active in `year` -> (pol dict, notes, warnings)."""
    pol = {"params": {}, "wage_pct": {}, "prices_pct": {}, "income_pct": {}, "hired_pct": {}}
    notes, warn, ad = [], [], adapters()
    for it in s.get("instruments", []):
        if year not in _years(it, int(s["start_year"])):
            continue
        rows = ad[ad.instrument == it["instrument"]]
        if rows.empty:
            warn.append(f"{it['instrument']}: mikrosimulyasiya adapteri yoxdur")
        size = float(it["size"])
        for r in rows.itertuples():
            tr, k = r.transform.rsplit("*", 1) if "*" in r.transform else (r.transform, "1")
            v = size * float(k)
            if tr.startswith("custom:"):
                globals()["c_" + tr.split(":", 1)[1]](pol, v, it, year, ctx)
            elif r.target_key.startswith("param:"):
                op = {"pct": "pct", "add": "add", "level": "set"}[tr]
                pol["params"][r.target_key[6:]] = {op: v}
            elif r.target_key.startswith("pol:"):
                key = r.target_key[4:].split(":")
                if len(key) == 2:
                    pol[key[0]][key[1]] = pol[key[0]].get(key[1], 0.0) + v
                else:
                    pol[key[0]] = 1 + v / 100 if tr == "pct" and key[0].endswith("scale") else v
            notes.append(r.note_az)
    return pol, notes, warn


# ---- custom adapters (size in instrument units) -------------------------------------
def c_pit_all_rates(pol, v, it, year, ctx):          # pp on every bracket rate, all regimes
    for reg in ("state", "priv"):
        for prm in ("pit_r1", "pit_r2", "pit_r3"):
            pol["params"][f"{prm}@{reg}"] = {"add": v / 100}


def c_ssc_employee(pol, v, it, year, ctx):
    for reg in ("state", "priv"):
        for prm in ("ssc_ee", "ssc_ee_hi"):
            pol["params"][f"{prm}@{reg}"] = {"add": v / 100}


def _prices(pol, d):
    for c, x in d.items():
        pol["prices_pct"][c] = pol["prices_pct"].get(c, 0.0) + x


def c_vat(pol, v, it, year, ctx):
    pol["params"]["vat_rate"] = {"add": v / 100}
    _prices(pol, MP.prices_from_instruments(vat_pp=v, vat0=Params().get("vat_rate", year)))


def c_fuel(pol, v, it, year, ctx):
    _prices(pol, MP.prices_from_instruments(fuel_pct=v))


def c_utility(pol, v, it, year, ctx):
    _prices(pol, MP.prices_from_instruments(utility_pct=v))


def c_fx(pol, v, it, year, ctx):
    _prices(pol, MP.prices_from_instruments(fx_pct=v))


def c_tariff(pol, v, it, year, ctx):
    _prices(pol, MP.prices_from_instruments(tariff_pp=v))


def c_cons_price(pol, v, it, year, ctx):
    tgt = it.get("target") or "food"
    _prices(pol, {c: v for c in str(tgt).split(";")})


def c_agri_subsidy(pol, v, it, year, ctx):
    pol["agri_subsidy_mln"] = pol.get("agri_subsidy_mln", 0.0) + v


def c_sector_jobs(pol, v, it, year, ctx):
    for sct in str(it.get("target") or "").split(";"):
        if sct:
            pol["hired_pct"][sct] = pol["hired_pct"].get(sct, 0.0) + v


def c_from_links(pol, v, it, year, ctx):
    pol["use_links"] = True


def _compose(P0, ov, year):
    """Turn relative overrides into levels on top of the baseline parameter set."""
    from .taxben import _apply
    out = {}
    for k, op in ov.items():
        name, _, reg = k.partition("@")
        v = _apply(P0.get(name, year, reg or "all"), op)
        if np.isfinite(v):                  # parameter not defined for this regime -> skip
            out[k] = {"set": max(v, 0.0) if name.startswith(("pit_r", "ssc_")) else v}
    return out


SPILL_CORE = {"mw_spill": 0.5, "mw_spill_band": 1.25, "mw_spill_taper": False}
SPILL_HEAD = ["poverty_rate", "poverty_gap", "poverty_rate:need", "gini", "gini_cons",
              "income_mean_pc", "wage_nominal", "hh_disp_real", "fiscal_cost",
              "ms_fiscal:budget_wagebill"]


def options(s, ctx=None):
    """Microsim options: scenario['microsim_options'] or ctx['microsim_options'] (e.g. the
    labelled minimum-wage spill-over SPILL_CORE). Default = static floor, no spill-over."""
    o = dict((ctx or {}).get("microsim_options", {}) if isinstance(ctx, dict) else {})
    o.update(s.get("microsim_options", {}) or {})
    return o


def simulate(s, year, ctx=None, behaviour=None, opts=None):
    """Baseline vs scenario for one year. Returns dict with hh/per frames + meta."""
    q, cal = year_state(year)
    P0, mw_proj = ms_uprate.baseline_params(year)
    pol, notes, warn = translate(s, year, ctx)
    lk = ms_links.from_ctx(ctx, year)
    if pol.pop("use_links", False) or any(it["instrument"] not in DIRECT
                                          for it in s.get("instruments", [])):
        for k_, v_ in lk["hired_pct"].items():
            pol["hired_pct"][k_] = pol["hired_pct"].get(k_, 0.0) + v_
        if lk["wage_pct"] is not None and not pol["wage_pct"]:
            pol["wage_pct"]["all"] = lk["wage_pct"]
        _prices(pol, lk["prices_pct"])
    elif lk["prices_pct"] and pol["prices_pct"]:
        pol["prices_pct"] = lk["prices_pct"]        # IO price model replaces first-round map
    P1 = P0.with_overrides(_compose(P0, pol.pop("params"), year))
    hb, pb = MP.compute(q, cal, year, P0)
    qs = q
    if pol.get("hired_pct"):
        qs = MP.prepare(ms_links.switch_employment(q, pol["hired_pct"]))
    if pol.get("agri_subsidy_mln"):
        tot = float(np.sum(qs["weight"] * qs["inc_agri"]))
        add = pol.pop("agri_subsidy_mln") * 1e6 / 12 / max(tot, 1.0)
        qs = qs.assign(inc_agri=qs["inc_agri"] * (1 + add))
    pol["mw_old"] = P0.get("minwage", year)
    pol.update({k: v for k, v in (opts if opts is not None else options(s, ctx)).items()
                if k.startswith("mw_spill")})
    ids_q = pd.Index(pd.factorize(q["hh_id"])[1])
    ids_s = [i.rstrip("s") for i in pd.factorize(qs["hh_id"])[1]]
    hba = hb.iloc[ids_q.get_indexer(ids_s)].reset_index(drop=True)   # base aligned to scen hh
    pol["base_y"] = hba["y_total"].to_numpy()
    pol["take_base"] = (hba["utsy"] > 0).to_numpy()
    hs, ps = MP.compute(qs, cal, year, P1, pol)
    return {"base": (hb, pb, q), "scen": (hs, ps, qs), "base_aligned": hba, "cal": cal,
            "P0": P0, "P1": P1,
            "notes": notes, "warn": warn, "links": lk, "pol": pol}


def run(scenario, ctx=None):
    t0 = time.perf_counter()
    p, cal, synth, T = base()
    start = int(scenario.get("start_year", config.FIRST_YEAR))
    years = sorted({y for it in scenario.get("instruments", []) for y in _years(it, start)})
    years = [y for y in years if y in YEARS] or [y for y in YEARS if y >= start][:1]
    frames, warns, notes = [], [], set()
    has_mw = any(it["instrument"] == "min_wage" for it in scenario.get("instruments", []))
    for y in years:
        r = simulate(scenario, y, ctx)
        frames.append(indicators(r, y, synth))
        warns += r["warn"]
        notes.update(n for n in r["notes"] if n)
        if has_mw and not options(scenario, ctx).get("mw_spill"):
            f = indicators(simulate(scenario, y, ctx, opts=SPILL_CORE), y, synth)
            f = f[f.indicator.isin(SPILL_HEAD)].copy()
            f["indicator"] = f["indicator"] + "@spill"
            f["method"] = "mikrosimulyasiya (MƏH yayılma variantı: +25 %-ə qədər 1/2)"
            f["note_az"] = f["note_az"] + "; diapazonun yuxarı ucu (fərziyyə)"
            frames.append(f)
    if any(y > max(YEARS) for it in scenario.get("instruments", []) for y in _years(it, start)):
        warns.append("mikrosimulyasiya 2030-dan sonrakı illər üçün hesablanmır (MikroUnit baza "
                     "üfüqü); uzun müddət üçün longrun mühərrikinə baxın")
    df = pd.concat(frames, ignore_index=True) if frames else None
    meta = {"warnings": sorted(set(warns)), "assumptions": sorted(notes),
            "data_mode": "SYNTHETIC" if synth else "REAL",
            "watermark": hh_data.WATERMARK if synth else "",
            "base_year": cal["base_year"], "kappa": cal.get("kappa"),
            "vintage": ms_uprate.microunit_baseline()["meta"],
            "runtime_s": round(time.perf_counter() - t0, 2)}
    return Result(ENGINE, df, meta)


def tsa_spending(year, pct=0.0, need_pct=0.0):
    """ÜSY spending definition shared with the core (beneficiary-based, mln AZN/year):
    baseline = sum over recipient households of max(0, members x need - income), take-up
    calibrated to DSMF recipients; scenario = payments x (1 + pct/100) and/or need criterion
    +need_pct. Returns dict base_mln, scen_mln, delta_mln, recipients_k (base, scenario)."""
    ins = []
    if pct:
        ins.append({"instrument": "tsa_benefit", "years": [year], "size": pct})
    if need_pct:
        ins.append({"instrument": "tsa_need", "years": [year], "size": need_pct})
    r = simulate({"id": "tsa", "name_az": "tsa", "start_year": year, "instruments": ins}, year)
    hb, hs = r["base"][0], r["scen"][0]
    rec = lambda h: float(np.sum(h.w * h.n * (h.utsy > 0))) / 1e3
    b, s_ = float(np.sum(hb.w * hb.utsy)) * 12e-6, float(np.sum(hs.w * hs.utsy)) * 12e-6
    return {"year": year, "base_mln": b, "scen_mln": s_, "delta_mln": s_ - b,
            "recipients_base_k": rec(hb), "recipients_scen_k": rec(hs)}
