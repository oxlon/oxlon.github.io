"""risk_web — in-browser backend of the Risk paneli (Pyodide). The same analysis functions the local API calls
(api/routes.py → engine_call): analysis_stress.run (MicroUnit chain + RU joint Monte Carlo, same seed),
analysis_scal.run (scalability through the chain) and analysis_opt.Optimizer.run (portfolio optimisation).
REPLAY (webcore): spine.baseline_id (hash of ~70 MB of upstream files), exposures.ministry_sofaz_plan (11 MB Ministry
workbook) and simulate.fiscal_sigma (σ of the 4.5 MB FR1 fan draws) are replayed from their native build-time results;
everything else runs unchanged."""
import json

import webcore

ROOT = webcore.unit_root(__file__)
webcore.paths(ROOT, ROOT / "api")

import apicore  # noqa: E402
from apicore import ApiError  # noqa: E402

UNIT = "RiskUnit"
PACKAGES = ["numpy", "pandas", "scipy", "statsmodels"]
INCLUDE = ["RiskUnit/riskunit/*.py", "MicroUnit/microlib/engines/*.py", "RiskUnit/input/*.csv",
           "MicroUnit/output/engine/*_state.json"]
ROUTES = [["POST", "^stress/run$"], ["POST", "^scalability/run$"], ["POST", "^optimize/run$"]]
REPLAY = {"riskunit.spine.baseline_id": ("noargs", "same"), "riskunit.exposures.ministry_sofaz_plan": ("noargs", "fresh"),
          "riskunit.simulate.fiscal_sigma": ("noargs", "fresh")}
STRESS = [
    {"name": "Neft −2σ + devalvasiya", "shocks": [{"factor": "brent", "k_sigma": -2}, {"factor": "fx", "size": 25}]},
    {"name": "Quraqlıq + qida", "shocks": [{"factor": "drought", "k_sigma": 2}, {"factor": "food", "k_sigma": 1.5}],
     "micro_overrides": {"FR1": {"exogenous": {"brent": {"pct": [-10, -10, -10, -10, -10]}}}}, "n": 3000},
    {"name": "Pul köçürmələri + faiz", "shocks": [{"factor": "remit", "k_sigma": -1.5}, {"factor": "rate", "k_sigma": 1}],
     "with_measures": False},
]
SCAL = [{"factor": "brent"}, {"factor": "fx", "sizes": [10, 20]}, {"factor": "remit", "k_sigma": [-3, 3]}]
OPT = [{"budget": 500}, {"budget": 1500, "include": ["T09"]}, {"budget": 1000, "appetite": {"P_g_max": 0.15}}]
SAMPLES = [["POST", "stress/run", STRESS[1]], ["POST", "scalability/run", SCAL[0]], ["POST", "optimize/run", OPT[0]]]
TESTS = [["POST", "stress/run", b] for b in STRESS] + [["POST", "scalability/run", b] for b in SCAL] + \
        [["POST", "optimize/run", b] for b in OPT]
NOTES = ["Monte Karlo eyni toxumla (config.SEED) və eyni N ilə hesablanır."]
_A = {}


def app():
    if not _A:
        import analysis_base, analysis_opt, data_views
        webcore.install(REPLAY)
        cfg = apicore.Config(root=ROOT, warm=False)
        _A["base"] = analysis_base.Base(cfg)
        _A["opt"] = analysis_opt.Optimizer(_A["base"])
        _A["views"] = data_views.Views(cfg)
    return _A


def _route(method, path, b):
    import analysis_scal, analysis_stress
    a = app()
    if method == "POST" and path == "stress/run":
        return analysis_stress.run(a["base"], b)
    if method == "POST" and path == "scalability/run":
        return analysis_scal.run(a["base"], b, a["views"])
    if method == "POST" and path == "optimize/run":
        return a["opt"].run(b or {})
    raise ApiError(404, "not_found", "Brauzer rejimində bu sorğu yoxdur: %s /%s (yalnız server)" % (method, path))


def handle(method, path, body_json):
    from az_errors import az_exc
    body = json.loads(body_json) if body_json else None
    return webcore.respond(lambda: _route(method, path.strip("/"), body), apicore.dumps, ApiError, az_exc)
