"""IO engine of the PolicyUnit (MİİS §15.5.4 FR2): sector-based policy effects.

``run(scenario, ctx) -> Result`` — harmonised tidy frame (engine_base.OUT_COLS) with the list
of affected sectors (group = IO sector code) and % changes in output, value added,
employment and prices, plus totals and the CPI effect.  Static fixed-coefficient model:
each active year's effect is the instantaneous (same-year) effect of that year's instrument
size; no dynamics, no supply constraints, prices and quantities do not interact (Tier D).
Adapter rows: config/adapters.csv with engine = io; transform `custom:<handler>` names a
handler in this module (HANDLERS); `*k` scales the instrument size.
ctx keys (dict or attributes, all optional): io_table (2025 = GRAS update [default] | 2021),
io_type ("I" [default] | "II"), years (list).
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from . import engine_base as EB
from . import io_data as D
from . import io_models as M

ENGINE = "io"
TIER = "D"
# assumption shares (docs/Metodologiya_IO.md §5)
FUEL_REG_SHARE_USE = 0.75     # AI-92 + diesel in domestic use of CPA 19 (value)
FUEL_REG_SHARE_HH = 0.90      # AI-92 + diesel in household motor-fuel spending
ELEC_SHARE_D = 0.55           # electricity in CPA 35 output (rest: gas distribution, steam)
GAS_SHARE_D = 0.40
VAT_EXEMPT = {"AGR", "EDU", "HEALTH", "FIN", "REAL", "PUB"}
GOODS = ["AGR", "OILGAS", "MINOTH", "FOOD", "LIGHT", "PETR", "CHEM", "METMIN", "MACH"]
_CACHE: dict = {}


def _get(ctx, key, default=None):
    if ctx is None:
        return default
    if isinstance(ctx, dict):
        return ctx.get(key, default)
    return getattr(ctx, key, default)


def _fp(name, default):
    try:
        from . import registry
        v = registry.params("fiscal").get(name, default)
        return float(v)
    except Exception:
        return default


def model(table=2025) -> M.IOModel:
    """Cached model: 2025 = 2021 benchmark updated by GRAS to FR1/NA 2025 margins."""
    key = int(table)
    if key not in _CACHE:
        base = D.aggregate(D.load_iot(2021))
        if key == 2021:
            m = M.IOModel(base, D.employment(2021), label="DSK 2021 (benchmark)")
            m.update_info = {}
        else:
            from . import io_update as U
            t, diag, info = U.update(base, key)
            m = M.IOModel(t, D.employment(key), label=f"DSK 2021 → {key} GRAS")
            m.update_info = info
        _CACHE[key] = m
    return _CACHE[key]


def target_weights(m: M.IOModel, target, basis: np.ndarray | None = None) -> np.ndarray | None:
    """Target -> sector weights (sum 1). Accepts IO code, FR1 group (agr, man, ...), FR4
    sector (manuf, trade, ...), NACE section letter, CPA 2-digit, or a ';' list.
    Weights within a multi-sector target follow `basis` (default: output)."""
    if target in (None, "", "all", "null"):
        return None
    sec = D.sectors().set_index("code").reindex(m.codes)
    hit = np.zeros(m.n, bool)
    for tg in str(target).split(";"):
        tg = tg.strip()
        for j, c in enumerate(m.codes):
            r = sec.loc[c]
            if (tg.upper() == c or tg == r["fr1_group"] or tg in r["fr4_sector_map"].split(";")
                    or tg.upper() in r["nace_section"].split(";")
                    or tg.zfill(2) in r["nace_list"].split(";")):
                hit[j] = True
    if not hit.any():
        raise ValueError(f"IO hədəfi '{target}' tanınmadı (io_sectors.csv kodları, FR1/FR4 sektorları və ya NACE)")
    b = np.where(hit, (m.x if basis is None else basis), 0.0)
    b = np.maximum(b, 0.0)
    return b / b.sum() if b.sum() > 0 else hit / hit.sum()


def _new_spec(n):
    return {"df": np.zeros(n), "fd_imp": 0.0, "dv": np.zeros(n), "dpm": np.zeros(n),
            "exog": {}, "retail": {}, "dti": np.zeros(n), "dtf": np.zeros(n),
            "ghosh": np.zeros(n), "emp_adj": np.zeros(n), "notes": []}


def _demand(m, sp, size_mln, col, target):
    """Final-demand injection of size_mln (mln AZN, purchasers ~ basic) with the product
    structure of FD column `col` (or the target sector); imported part leaks."""
    w_tot = m.x.copy() if col == "x" else m.t.fd[col].clip(lower=0).to_numpy()
    if target is not None:
        w = target_weights(m, target, basis=w_tot if w_tot.sum() > 0 else None)
        dom_share = 1 - m.s_imp
    else:
        w = w_tot / w_tot.sum()
        dd = m.fdd[col].clip(lower=0).to_numpy()
        dom_share = np.where(w_tot > 0, dd / np.where(w_tot > 0, w_tot, 1), 0.0)
    if col == "exp":
        dom_share = np.ones(m.n)
    tot = size_mln * 1e3 * w
    sp["df"] += tot * dom_share
    sp["fd_imp"] += float((tot * (1 - dom_share)).sum())


# ----------------------------------------------------------------------------- handlers
def h_pub_invest(m, sp, size, target, it):
    _demand(m, sp, size, "gfcf", target)
    sp["notes"].append("investisiya ƏKÜY məhsul strukturu ilə (hədəf verilərsə — həmin sektorun məhsulu)")


def h_gov_current(m, sp, size, target, it):
    _demand(m, sp, size, "gov", target)


def h_sector_demand(m, sp, size, target, it):
    if target is None:
        raise ValueError("io_sector_demand: 'target' (IO sektoru) məcburidir")
    _demand(m, sp, size, "x", target)


def h_export_demand(m, sp, size, target, it):
    _demand(m, sp, size, "exp", target if target is not None else "man")


def h_export_subsidy(m, sp, size, target, it):
    """Subsidy S (mln AZN) to exporters of the target -> export price falls by S/E ->
    exports rise by elasticity * S (fiscal_params export_price_elasticity)."""
    eps = _fp("export_price_elasticity", 1.5)
    e = m.t.fd["exp"].clip(lower=0).to_numpy().copy()
    e[m.codes.index("OILGAS")] = 0.0
    w = target_weights(m, target or "man", basis=e)
    sp["df"] += eps * size * 1e3 * w
    sp["notes"].append(f"ixrac qiymət elastikliyi {eps:g}")


def h_household_income(m, sp, size_mln, target, it):
    """Household income injection (mln AZN) -> consumption mpc*(1-tax) with the domestic
    HH structure (Type I quantity on the induced consumption)."""
    sp["df"] += size_mln * 1e3 * m.c
    sp["fd_imp"] += size_mln * 1e3 * m.mpc * (1 - m.tax_wedge) * \
        float(m.fdm["hh"].sum() / (m.t.fd["hh"].sum() + m.t.fd_tax.get("hh", 0.0)))


def h_public_wage(m, sp, size, target, it):
    wb = _fp("public_wagebill", 6000.0)
    h_household_income(m, sp, size / 100 * wb, None, it)
    sp["notes"].append(f"büdcə əmək haqqı fondu {wb:g} mln AZN × {size:g} %")


def h_fuel_price(m, sp, size, target, it):
    """Regulated AI-92/diesel prices +size % -> CPA 19 basic price (use-weighted share),
    household fuel item (HH share)."""
    sp["exog"]["PETR"] = sp["exog"].get("PETR", 0.0) + size / 100 * FUEL_REG_SHARE_USE
    sp["retail"]["PETR"] = sp["retail"].get("PETR", 0.0) + size / 100 * FUEL_REG_SHARE_HH
    sp["notes"].append(f"yanacaq: tənzimlənən pay istifadədə {FUEL_REG_SHARE_USE:g}, ev təsərrüfatında {FUEL_REG_SHARE_HH:g}")


def _reg(sp, sector, dp):
    sp["exog"][sector] = sp["exog"].get(sector, 0.0) + dp
    sp["retail"][sector] = sp["retail"].get(sector, 0.0) + dp


def h_utility_tariff(m, sp, size, target, it):
    _reg(sp, "ENERGY", size / 100)
    _reg(sp, "WATER", size / 100)


def h_elec_tariff(m, sp, size, target, it):
    _reg(sp, "ENERGY", size / 100 * ELEC_SHARE_D)


def h_gas_tariff(m, sp, size, target, it):
    _reg(sp, "ENERGY", size / 100 * GAS_SHARE_D)


def h_water_tariff(m, sp, size, target, it):
    _reg(sp, "WATER", size / 100)


def h_vat_rate(m, sp, size, target, it):
    """VAT is deductible for registered producers -> only final household prices change;
    exempt sectors unaffected; full pass-through (IO assumption)."""
    w = target_weights(m, target)
    cov = np.array([0.0 if c in VAT_EXEMPT else 1.0 for c in m.codes])
    if w is not None:
        cov = cov * (w > 0)
    sp["dtf"] += size / 100 * cov
    sp["notes"].append("ƏDV: yalnız son istehlak qiymətləri (istehsalçı üçün əvəzləşdirilir); tam ötürmə")


def h_product_tax(m, sp, size, target, it):
    """Non-deductible indirect tax (excise) / subsidy (negative) on the target products,
    pp of the basic price, paid by intermediate and final users."""
    w = target_weights(m, target)
    hit = np.ones(m.n) if w is None else (w > 0).astype(float)
    xs = np.where(m.x > 0, m.x, 1.0)
    sp["dti"] += (size / 100) * (hit[:, None] * m.t.Z).sum(0) / xs
    sp["dtf"] += size / 100 * hit


def h_import_tariff(m, sp, size, target, it):
    """Ad valorem tariff change (pp) on imports of the target goods (default: all goods);
    full pass-through to import prices; no import substitution (no Armington)."""
    w = target_weights(m, target)
    hit = np.array([c in GOODS for c in m.codes], float) if w is None else (w > 0).astype(float)
    sp["dpm"] += size / 100 * hit
    sp["notes"].append("idxalın əvəzlənməsi modelləşdirilmir (sabit idxal payları)")


def h_fx_deval(m, sp, size, target, it):
    sp["dpm"] += size / 100 * np.ones(m.n)
    sp["notes"].append("məzənnə: idxal qiymətlərinə tam ötürmə (AZN ilə); ixrac qiymətləri qiymət modelində yoxdur")


def h_labour_cost(m, sp, size, target, it):
    w = target_weights(m, target)
    hit = np.ones(m.n) if w is None else (w > 0).astype(float)
    sp["dv"] += size / 100 * m.w * hit


def h_productivity(m, sp, size, target, it):
    """Productivity gain g % in the target: primary-input cost per unit falls by g*v_j
    (price model) and employment per unit of output falls by g (labour-saving)."""
    w = target_weights(m, target)
    hit = np.ones(m.n) if w is None else (w > 0).astype(float)
    sp["dv"] -= size / 100 * m.v * hit
    sp["emp_adj"] -= size / 100 * m.emp * hit / (1 + size / 100)


def h_agri_subsidy(m, sp, size, target, it):
    """Output subsidy S to agriculture: (i) cost-push price model, AGR unit cost -S/x;
    (ii) Ghosh supply-side propagation of the additional primary input (labelled)."""
    k = m.codes.index("AGR")
    sp["dv"][k] -= size * 1e3 / m.x[k]
    sp["ghosh"][k] += size * 1e3 * _fp("agri_supply_mult", 0.6)


def h_supply_shock(m, sp, size, target, it):
    w = target_weights(m, target)
    if w is None:
        raise ValueError("sector_supply_shock: 'target' məcburidir")
    prim = m.x - m.Zd.sum(0)
    sp["ghosh"] += size / 100 * prim * (w > 0)


HANDLERS = {k[2:]: v for k, v in dict(globals()).items() if k.startswith("h_") and callable(v)}


# ----------------------------------------------------------------------------- run
def _adapters() -> pd.DataFrame:
    try:
        from . import registry
        return registry.adapters_for(ENGINE).copy()
    except Exception:
        p = D.CONFIG / "adapters.csv"
        a = pd.read_csv(p, dtype=str, keep_default_na=False) if p.exists() else pd.DataFrame()
        return a[a.get("engine", pd.Series(dtype=str)) == ENGINE] if len(a) else a


def _scale(tr: str) -> tuple[str, float]:
    tr = (tr or "").strip()
    if "*" in tr:
        a, b = tr.rsplit("*", 1)
        return a.strip(), float(b)
    return tr, 1.0


def _years(scenario, ctx):
    ys = _get(ctx, "years")
    if ys:
        return sorted(int(y) for y in ys)
    out = set()
    for it in scenario.get("instruments", []):
        y = it.get("years", "all")
        if y == "all":
            s0 = int(scenario.get("start_year", 2026))
            out.update(range(s0, s0 + 10))
        else:
            out.update(int(v) for v in y)
    return sorted(out)


def solve_year(m: M.IOModel, sp: dict, type2: bool = False) -> dict:
    q = m.quantity(sp["df"], type2=type2)
    q2 = m.quantity(sp["df"], type2=True)
    pr = m.price(dv=sp["dv"], dpm=sp["dpm"], exog=sp["exog"], dtax_int=sp["dti"])
    if not hasattr(m, "_w"):
        try:
            m._w = m.cpi_weights(D.aggregate_supply(D.load_supply(2021)))
        except Exception:
            m._w = m.cpi_weights(None)
    retail = dict(sp["retail"])
    cpi = m.cpi_effect(pr, m._w, exog_retail=retail,
                       dtax_final=sp["dtf"] if np.any(sp["dtf"]) else None)
    gx = m.ghosh(sp["ghosh"]) if np.any(sp["ghosh"]) else np.zeros(m.n)
    return {"q": q, "q2": q2, "pr": pr, "cpi": cpi, "ghosh": gx}


def _rows(m, y, res, sp, type2):
    R = []
    q, cpi = res["q"], res["cpi"]
    meth_q = f"IO Leontief kəmiyyət (tip {'II' if type2 else 'I'})"
    meth_p = "IO Leontief qiymət (xərc ötürülməsi)"
    xs = m.x / 1e3
    vb = m.va_vec / 1e3
    dx = q["dx"] / 1e3
    dva = q["dva"] / 1e3
    demp = q["demp"] + sp["emp_adj"]
    order = np.argsort(-np.abs(dx / np.where(xs > 0, xs, 1)))
    rank = {j: r + 1 for r, j in enumerate(order)}
    for j, c in enumerate(m.codes):
        nm = m.t.names[j]
        if abs(dx[j]) > 1e-9:
            note = f"təsir rütbəsi {rank[j]}"
            R.append(EB.row(f"io_output:{c}", f"Ümumi buraxılış — {nm}", "mln AZN", y, xs[j],
                            xs[j] + dx[j], meth_q, TIER, c, note))
            R.append(EB.row(f"io_va:{c}", f"Əlavə dəyər — {nm}", "mln AZN", y, vb[j],
                            vb[j] + dva[j], meth_q, TIER, c, note))
        if abs(demp[j]) > 1e-9:
            R.append(EB.row(f"io_emp:{c}", f"Məşğulluq — {nm}", "min nəfər", y, m.emp[j],
                            m.emp[j] + demp[j], meth_q, TIER, c))
        dp = res["pr"]["dp"][j]
        if abs(dp) > 1e-9:
            R.append(EB.row(f"io_price:{c}", f"Əsas qiymət — {nm}", "indeks (baza=100)", y, 100.0,
                            100 * (1 + dp), meth_p, TIER, c, "", 100 * dp, 100 * dp))
        if abs(res["ghosh"][j]) > 1e-9:
            g = res["ghosh"][j] / 1e3
            R.append(EB.row(f"io_output_ghosh:{c}", f"Buraxılış (Ghosh təklif modeli) — {nm}",
                            "mln AZN", y, xs[j], xs[j] + g, "IO Ghosh təklif (məhdud şərh)", TIER, c,
                            "Ghosh: sabit bölgü əmsalları; kəmiyyət şərhi şərtidir"))
    tot = [("io_output_total", "Ümumi buraxılış (IO, cəmi)", xs.sum(), dx.sum(), "mln AZN"),
           ("io_va_total", "Əlavə dəyər, əsas qiymətlərlə (IO, cəmi)", vb.sum(), dva.sum(), "mln AZN"),
           ("employment", "Məşğulluq (IO, cəmi)", m.emp.sum(), demp.sum(), "min nəfər"),
           ("io_imports_total", "İdxal (aralıq + son tələbin idxal hissəsi)",
            m.t.imp.sum() / 1e3, (q["dimp"].sum() + sp["fd_imp"]) / 1e3, "mln AZN")]
    for ind, lab, b, d, u in tot:
        if abs(d) > 1e-9:
            R.append(EB.row(ind, lab, u, y, b, b + d, meth_q, TIER, "ümumi"))
    if np.any(res["q2"]["dx"]) and not type2:
        q2 = res["q2"]
        R.append(EB.row("io_output_total_t2", "Ümumi buraxılış (tip II, ev təsərrüfatları endogen)",
                        "mln AZN", y, xs.sum(), xs.sum() + q2["dx"].sum() / 1e3,
                        "IO Leontief kəmiyyət (tip II)", TIER, "ümumi", "yuxarı sərhəd"))
        R.append(EB.row("io_emp_total_t2", "Məşğulluq (tip II)", "min nəfər", y, m.emp.sum(),
                        m.emp.sum() + q2["demp"].sum(), "IO Leontief kəmiyyət (tip II)", TIER,
                        "ümumi", "yuxarı sərhəd"))
    if np.any(res["ghosh"]):
        g = res["ghosh"].sum() / 1e3
        R.append(EB.row("io_output_ghosh_total", "Ümumi buraxılış (Ghosh təklif modeli, cəmi)",
                        "mln AZN", y, xs.sum(), xs.sum() + g, "IO Ghosh təklif (məhdud şərh)", TIER,
                        "ümumi", "Ghosh: sabit bölgü əmsalları; kəmiyyət şərhi şərtidir"))
    if abs(cpi["CPI"]) > 1e-12:
        R.append(EB.row("io_cpi", "İQİ səviyyəsinə təsir (IO qiymət modeli)", "indeks (baza=100)",
                        y, 100.0, 100 * (1 + cpi["CPI"]), meth_p, TIER, "ümumi",
                        "birbaşa + dolayı ötürmə, tam ötürmə fərziyyəsi", 100 * cpi["CPI"],
                        100 * cpi["CPI"]))
    return R


def run(scenario: dict, ctx=None) -> EB.Result:
    t0 = time.time()
    table = int(_get(ctx, "io_table", 2025))
    type2 = str(_get(ctx, "io_type", "I")).upper() == "II"
    warn, notes = [], []
    try:
        m = model(table)
    except Exception as e:   # graceful degradation to the benchmark
        warn.append(f"{table} GRAS cədvəli qurulmadı ({e}); 2021 benchmark istifadə olunur")
        m = model(2021)
    ad = _adapters()
    years = _years(scenario, ctx)
    rows, cpi_path, used = [], {}, []
    for y in years:
        sp = _new_spec(m.n)
        active = False
        for it in scenario.get("instruments", []):
            iid = it.get("instrument")
            yrs = it.get("years", "all")
            if yrs != "all" and y not in [int(v) for v in yrs]:
                continue
            arows = ad[ad["instrument"] == iid] if len(ad) else ad
            if not len(arows):
                msg = f"'{iid}': IO mühərriki üçün adapter yoxdur — IO kanalı tətbiq edilmir"
                if msg not in warn:
                    warn.append(msg)
                continue
            for _, a in arows.iterrows():
                tr, k = _scale(a["transform"])
                name = tr.split(":", 1)[1] if tr.startswith("custom:") else a["target_key"]
                fn = HANDLERS.get(name)
                if fn is None:
                    raise ValueError(f"adapters.csv: IO funksiyası '{name}' yoxdur ({iid})")
                fn(m, sp, float(it.get("size", 0.0)) * k, it.get("target"), it)
                active = True
                used.append(iid)
        if not active:
            continue
        res = solve_year(m, sp, type2)
        notes += [n for n in sp["notes"] if n not in notes]
        rows += _rows(m, y, res, sp, type2)
        cpi_path[y] = res["cpi"]["CPI"]
    prev = 0.0
    for y in years:            # inflation (pp) = change of the price-level effect
        lvl = cpi_path.get(y, 0.0)
        if abs(lvl - prev) > 1e-12:
            rows.append(EB.row("infl", "İnflyasiyaya təsir (IO qiymət modeli)", "%", y, 0.0,
                               100 * ((1 + lvl) / (1 + prev) - 1), "IO Leontief qiymət", TIER,
                               "ümumi", "birdəfəlik səviyyə şoku il ərzində"))
        prev = lvl
    meta = {"vintage": {"io_table": m.label, "io_benchmark_md5": m.t.meta.get("md5", ""),
                        "io_update": getattr(m, "update_info", {})},
            "runtime_s": round(time.time() - t0, 3), "warnings": warn,
            "assumptions": ["sabit texniki əmsallar; təklif məhdudiyyəti yoxdur",
                            "idxal mütənasibliyi (məhsul üzrə sabit idxal payı)",
                            "qiymət modelində tam xərc ötürülməsi; qiymət–kəmiyyət qarşılıqlı təsiri yoxdur",
                            "statik: hər ilin təsiri həmin ilin alət ölçüsünə görə"] + notes,
            "instruments_used": sorted(set(used)), "applicable": bool(rows)}
    return EB.Result(ENGINE, pd.DataFrame(rows), meta)
