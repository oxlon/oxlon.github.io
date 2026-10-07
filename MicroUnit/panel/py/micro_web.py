"""micro_web — in-browser backend of the Mikro Model paneli (Pyodide). POST scenarios/run calls the same
scenario_engine.Engine.run → microlib.engines.chain.run_chain (FR1 → FR3, FR4, FR5, FR10 → FR12) as the local API
(api/routes.py); saving scenarios needs the server (SQLite) and is not offered in the browser."""
import json

import webcore

ROOT = webcore.unit_root(__file__)
webcore.paths(ROOT, ROOT / "api")

import apicore  # noqa: E402
import scenario_engine as SE  # noqa: E402
from apicore import ApiError  # noqa: E402

UNIT = "MicroUnit"
PACKAGES = ["numpy", "pandas", "scipy", "sqlite3"]
INCLUDE = ["MicroUnit/microlib/engines/*.py", "MicroUnit/output/engine/*_state.json", "MicroUnit/output/engine/*_state.npz"]
ROUTES = [["POST", "^scenarios/run$"]]
REPLAY = {}
SAMPLES = [
    ["POST", "scenarios/run", {"overrides": {}, "scenario": "Baseline", "save": False}],
    ["POST", "scenarios/run", {"overrides": {"FR1": {"exogenous": {"brent": [52, 48, 50, 55, 58]}}}, "scenario": "Adverse",
                               "save": False}],
    ["POST", "scenarios/run", {"overrides": {"FR1": {"coefficients": {"FR1.B1_oil_price|ln_brent": 1.25}},
                                             "FR3": {"levers": {"mw_growth": 10}}}, "scenario": "Reform", "save": False}],
]
_E = {}


def engine():
    if "e" not in _E:
        _E["e"] = SE.Engine(apicore.Config(root=ROOT, db=ROOT / "api" / "micro_browser.db"))
    return _E["e"]


def _route(method, path, b):
    if method == "POST" and path == "scenarios/run":
        if not isinstance(b, dict):
            raise ApiError(400, "bad_request", "JSON obyekt gözlənilir: {\"overrides\": {...}, \"scenario\": \"Baseline\"}")
        res = engine().run(b.get("overrides"), b.get("scenario") or "Baseline", b.get("modules"))
        if b.get("name") and b.get("save", True):
            res["warnings_az"] = ["Brauzer rejimində ssenari serverdə saxlanılmır — «JSON ixrac» düyməsindən istifadə edin."]
        return res
    raise ApiError(404, "not_found", "Brauzer rejimində bu sorğu yoxdur: %s /%s (yalnız server)" % (method, path))


def handle(method, path, body_json):
    body = json.loads(body_json) if body_json else None
    return webcore.respond(lambda: _route(method, path.strip("/"), body), apicore.dumps, ApiError)
