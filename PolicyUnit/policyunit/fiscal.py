"""Ex-ante direct fiscal cost of instruments (cost_rule in instruments.csv) and nominal-GDP
scaling paths. Positive cost = worse budget balance (spending up or revenue down).

Financing is allocated PER INSTRUMENT (each instrument's own `financing` field): `instrument_costs`
returns one cost path per instrument with its financing and whether FR1 already books it."""
from __future__ import annotations

from functools import lru_cache

from . import config, microbridge, registry, scenario as scn

REV = {"vat": ("vat_rate", "vat_rev_gdp"), "cit": ("cit_rate", "cit_rev_gdp"),
       "pit": ("pit_rate", "pit_rev_gdp"), "customs": ("customs_rate", "customs_base_gdp")}
PENSION_INDEXED = {"pension_spending", "dsmf_spending"}      # uprated with the FR1 average pension
PENSION_BASE_2025 = 496.6                                     # FR1 CAL pens_base_pension (2025)


@lru_cache(maxsize=1)
def gdp_nominal() -> dict:
    """Baseline nominal GDP (mln AZN): FR1 Baseline 2026–2030, after 2030 extended at the
    2029→2030 FR1 growth rate (scaling denominator only, not a forecast)."""
    b = microbridge.baseline()
    g = microbridge.series(b, "FR1", "fr1:gdp_n")
    out = dict(zip(config.MICRO_YEARS, g))
    gr = g[-1] / g[-2]
    for y in range(config.MICRO_YEARS[-1] + 1, 2040):
        out[y] = out[y - 1] * gr
    return out


@lru_cache(maxsize=1)
def pension_path() -> dict:
    b = microbridge.baseline()
    p = microbridge.series(b, "FR1", "fr1:pension")
    out = dict(zip(config.MICRO_YEARS, p))
    gr = p[-1] / p[-2]
    for y in range(config.MICRO_YEARS[-1] + 1, 2040):
        out[y] = out[y - 1] * gr
    return out


def base_value(param: str, y: int) -> float:
    """Benefit / spending base in year y (mln AZN): pension-type bases follow the FR1 baseline average
    pension from their 2025 value, all others nominal GDP from 2026."""
    v = registry.params("fiscal")[param]
    if param in PENSION_INDEXED:
        return v * pension_path()[y] / PENSION_BASE_2025
    g = gdp_nominal()
    return v * g[y] / g[config.FIRST_YEAR]


def _fuel_gain(s: float, y: int) -> float:
    """Revenue gain of a regulated fuel-price rise (mln AZN, positive = more revenue): VAT on the higher
    sales value plus profit tax on the extra margin (demand elasticity applied)."""
    p = registry.params("fiscal")
    sales = base_value("fuel_sales_base", y)
    x = s / 100
    new_sales = sales * (1 + x) * (1 + p["fuel_price_elasticity"] * x)
    d_val = new_sales - sales
    vat = p["vat_rate"] / (100 + p["vat_rate"]) * d_val
    margin = (d_val - vat) * p["fuel_margin_tax"] / 100
    return vat + margin


@lru_cache(maxsize=64)
def _tsa_microsim(year: int, pct: float) -> float:
    """ÜSY cost: the microsimulation's beneficiary-based definition (eng_microsim.tsa_spending), so P1 and
    P3 use one definition (C6); after 2030 scaled with nominal GDP; fallback = fiscal_params tsa_spending."""
    y = min(year, config.MICRO_YEARS[-1])
    try:
        from . import eng_microsim
        d = eng_microsim.tsa_spending(y, pct)["delta_mln"]
    except Exception:  # noqa: BLE001 — microsim not available: documented fallback base
        d = pct / 100 * base_value("tsa_spending", y)
    g = gdp_nominal()
    return d * g[year] / g[y]


def direct_cost(it: dict, years) -> list[float]:
    """Direct (static, before feedback) fiscal cost per year, mln AZN."""
    r = registry.instrument(it["instrument"])
    rule = str(r.get("cost_rule", "none"))
    p = registry.params("fiscal")
    gdp = gdp_nominal()
    size = scn.path(it, years)
    out = []
    for y, s in zip(years, size):
        if s == 0 or rule == "none":
            out.append(0.0)
        elif rule == "mw_budget":
            from . import mw_budget
            out.append(mw_budget.cost_path([s], [y])[0])
        elif rule == "tsa_microsim":
            out.append(_tsa_microsim(int(y), float(s)))
        elif rule == "fuel_revenue":
            out.append(-_fuel_gain(s, y))
        elif rule == "spend":
            out.append(s)
        elif rule.startswith("revenue:"):
            kind = rule.split(":", 1)[1]
            rate, base = REV[kind]
            if kind == "customs":
                d_rev = s / 100 * p[base] / 100 * gdp[y]
            else:
                d_rev = s / p[rate] * p[base] / 100 * gdp[y]
            out.append(-d_rev)
        elif rule.startswith("benefit:"):
            out.append(s / 100 * base_value(rule.split(":", 1)[1], y))
        else:
            raise registry.ConfigError(f"{it['instrument']}: naməlum cost_rule '{rule}'")
    return out


def instrument_costs(s: dict, years, only=None) -> list[dict]:
    """[{instrument, financing, in_fr1, cost: [...]}] — per-instrument financing (C2)."""
    out = []
    for it in s["instruments"]:
        if only is not None and it["instrument"] not in only:
            continue
        out.append({"instrument": it["instrument"], "financing": it.get("financing") or "deficit",
                    "in_fr1": registry.instrument(it["instrument"]).get("cost_in_fr1", "no") == "yes",
                    "cost": direct_cost(it, years)})
    return out


def scenario_cost(s: dict, years, only=None) -> dict:
    """Total direct cost, the part NOT in the FR1 budget, and the cost by financing type."""
    n = len(years)
    res = {"total": [0.0] * n, "off_fr1": [0.0] * n,
           "by_fin": {f: [0.0] * n for f in ("deficit", "sofaz", "tax", "reallocation")}}
    for c in instrument_costs(s, years, only):
        add = lambda a: [x + y for x, y in zip(a, c["cost"])]
        res["total"] = add(res["total"])
        if not c["in_fr1"]:
            res["off_fr1"] = add(res["off_fr1"])
        res["by_fin"][c["financing"]] = add(res["by_fin"][c["financing"]])
    return res


def financing(s: dict) -> str:
    """Label only (mixed scenarios are allocated per instrument by scenario_cost)."""
    fins = {it.get("financing") or "deficit" for it in s["instruments"]}
    return fins.pop() if len(fins) == 1 else "mixed"
