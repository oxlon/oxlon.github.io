"""
stub_engine — sınaqlar üçün saxta ssenari mühərriki (müqavilə §B interfeysi ilə eyni forma).

    inputs_for(module) -> {"exogenous": [...], "coefficients": [...], "levers": [...]}
    run_chain(overrides_by_module, scenario, modules=None) -> {"scenario", "results": {m: {"series", "meta", "warnings"}}, ...}

Qaydalar sadədir və determinlidir: FR1 ÜDM-i = 100 · (1 + g)^t, burada g ekzogen «fr1:oil_price» dəyişəninə
bağlıdır; aşağı axın modulları FR1-in nəticəsini miqyaslayır. Yalnız standart kitabxana.
"""
YEARS = [2026, 2027, 2028, 2029, 2030]
ORDER = ["FR1", "FR3", "FR4", "FR5", "FR10", "FR12"]
UPSTREAM = {"FR1": [], "FR3": ["FR1"], "FR4": ["FR1", "FR3"], "FR5": ["FR1"], "FR10": ["FR1"], "FR12": ["FR1", "FR10"]}
BASE_OIL = {"Baseline": [75.0, 74.0, 73.0, 72.0, 71.0], "Adverse": [55.0, 55.0, 56.0, 57.0, 58.0],
            "Reform": [75.0, 74.0, 73.0, 72.0, 71.0]}
CALLS = []


def inputs_for(module):
    m = module.upper()
    if m not in ORDER:
        raise ValueError("naməlum modul %s" % module)
    exo = []
    if m == "FR1":
        exo.append({"id": "fr1:oil_price", "label_az": "Brent neftinin qiyməti", "unit": "ABŞ dolları/barrel", "years": YEARS,
                    "baseline": BASE_OIL, "min": 20, "max": 150, "step": 1})
    return {"exogenous": exo,
            "coefficients": [{"eq_id": "%s.E1" % m, "name": "elasticity", "label_az": "elastiklik", "value": 0.5, "se": 0.1,
                              "ci_low": 0.3, "ci_high": 0.7, "sign_expected": "+", "editable": True}],
            "levers": []}


def _oil(ov, scenario):
    base = list(BASE_OIL[scenario])
    spec = (ov.get("exogenous") or {}).get("fr1:oil_price")
    if isinstance(spec, dict) and "pct" in spec:
        return [b * (1 + float(spec["pct"]) / 100.0) for b in base]
    if isinstance(spec, list):
        if len(spec) != len(YEARS):
            raise ValueError("fr1:oil_price üçün 5 dəyər gözlənilir")
        return [float(x) for x in spec]
    return base


def run(module, ov, scenario, upstream):
    coef = float((ov.get("coefficients") or {}).get("%s.E1|elasticity" % module, 0.5))
    if module == "FR1":
        oil = _oil(ov, scenario)
        g = [0.02 + coef * 0.02 * (o / 75.0 - 1) for o in oil]
        lvl, series = 100.0, {}
        for y, gi in zip(YEARS, g):
            lvl *= 1 + gi
            series.setdefault("fr1:rgdp", {})[y] = round(lvl, 6)
        series["fr1:oil_price"] = dict(zip(YEARS, oil))
    else:
        src = (upstream or {}).get("FR1", {}).get("series", {}).get("fr1:rgdp", {y: 100.0 for y in YEARS})
        series = {"%s:index" % module.lower(): {y: round(v * (1 + coef / 10), 6) for y, v in src.items()}}
    return {"series": series, "meta": {"module": module, "scenario": scenario, "stub": True}, "warnings": []}


def run_chain(overrides_by_module=None, scenario="Baseline", modules=None):
    if scenario not in BASE_OIL:
        raise ValueError("naməlum ssenari %s" % scenario)
    ov = overrides_by_module or {}
    CALLS.append({"overrides": ov, "scenario": scenario, "modules": modules})
    out = {"scenario": scenario, "results": {}, "order": [], "skipped": [], "errors": {}, "warnings": []}
    for m in ORDER:
        if modules is not None and m not in modules:
            continue
        up = {u: out["results"][u] for u in UPSTREAM[m] if u in out["results"]}
        out["results"][m] = run(m, ov.get(m, {}), scenario, up)
        out["order"].append(m)
    return out
