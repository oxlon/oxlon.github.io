"""policy_web — in-browser backend of the Siyasət paneli (Pyodide). A run is the API's own sequence (api/runs.py
Runs._work): policyunit.integrate.run_scenario → fr4_bridge.analyse → results.build, synchronously; validation is
scenarios.Store.validate, comparison is compare_views.compare (unchanged) over an in-memory store/run cache.

Browser limits (Azerbaijani notes in the result): engines micro, caem, io, longrun, microsim run; oxlon (subprocess)
and riskfx (RiskUnit HTTP) do not. Side effects run in «rules» mode; RiskUnit cannot be called, so the FR4 risk profile
uses the primary-source rule (b): PolicyUnit location shift of the last RiskUnit unconditional distribution.
REPLAY (webcore): CAEM workbook cells, the IO .xls sheets, file hashes (vintages) and the cached RiskUnit distribution."""
import copy, json, time, types

import webcore

ROOT = webcore.unit_root(__file__)
webcore.paths(ROOT, ROOT / "api")

import apicore  # noqa: E402
from apicore import ApiError  # noqa: E402

UNIT = "PolicyUnit"
PACKAGES = ["numpy", "pandas", "scipy", "sqlite3"]
INCLUDE = ["PolicyUnit/policyunit/*.py", "PolicyUnit/config/*.csv", "PolicyUnit/config/scenarios/*.json", "PolicyUnit/data/io/raw/*.xls",
           "MicroUnit/microlib/engines/*.py", "MicroUnit/output/engine/*_state.json"]
ROUTES = [["POST", "^runs$"], ["POST", "^scenarios/[a-z0-9_]+/run$"], ["POST", "^scenarios/validate$"], ["POST", "^compare$"]]
REPLAY = {"policyunit.caem_core.load": ("noargs", "same"), "policyunit.caem_core.vintage_status": ("noargs", "fresh"),
          "policyunit.io_data.read_sheet": ("basename", "fresh"), "pu.vintage": ("noargs", "fresh"),
          "policyunit.risk_link._any_cached_unconditional": ("noargs", "fresh"),
          "policyunit.microbridge.vintage": ("noargs", "fresh"), "policyunit.io_data.md5": ("basename", "fresh")}
ENGINES = ("micro", "caem", "io", "microsim", "longrun")
SKIP_AZ = {"oxlon": "Brauzer rejimi: OxLon FR13 mühərriki ayrıca prosesdə işləyir — brauzerdə hesablanmır (serverlə hesablayın)",
           "riskfx": "Brauzer rejimi: RiskUnit məzənnə ötürməsi HTTP ilə çağırılır — brauzerdə hesablanmır (serverlə hesablayın)"}
RISK_NOTE = ("Brauzer rejimi: RiskUnit-ə müraciət mümkün deyil — FR4 risk profili əsas mənbə qaydası (b) ilə verilir: "
             "PolicyUnit sürüşməsi (P1) RiskUnit-in son şərtsiz paylanmasına tətbiq olunub; yan təsirlər yalnız qaydalarla.")
OFFICIAL = ["pubinv1bn_deficit", "vat_minus2", "mw20_2027"]
SAMPLES = [["POST", "scenarios/%s/run" % OFFICIAL[0], {"wait": 60}],
           ["POST", "compare", {"scenarios": OFFICIAL[1:], "side_effects": "rules"}]]
TESTS = [["POST", "scenarios/%s/run" % s, {"side_effects": "rules", "risk": False, "engines": list(ENGINES)}] for s in OFFICIAL]
NOTES = [RISK_NOTE]
_A = {}


def app():
    """SimpleNamespace(cfg, store, runs) — the attributes compare_views.compare uses of the API's App."""
    if _A:
        return _A["ns"]
    import compare_views, kpi_views, pu, runs, scenarios  # noqa: F401
    webcore.install(REPLAY)
    cfg = apicore.Config(root=ROOT, db="/tmp/policy_browser.db", warm=False)

    class Store(scenarios.Store):                      # official scenarios from config/, drafts from the browser
        local = {}

        def _draft(self, sid):
            b = self.local.get(sid)
            return {"body": b, "created": None, "updated": None, "actor": "brauzer", "note": None, "origin": "brauzer"} if b else None

        def last_run(self, sid):
            return None

    class Runs:                                        # synchronous, in-memory (api/runs.py needs threads + SQLite)
        def __init__(self):
            self.res, self.by = {}, {}

        def latest_ok(self, s, vid):
            return self.by.get(json.dumps(s, sort_keys=True, default=str))

        def submit(self, s, src, req, actor="brauzer"):
            rid = "BR-%d" % (len(self.res) + 1)
            self.res[rid] = run_now(s, req, rid)
            if src != "adhoc":                         # as Runs.latest_ok: ad-hoc runs are not reused
                self.by[json.dumps(s, sort_keys=True, default=str)] = rid
            return rid, False

        def wait(self, rid, seconds):
            return None

        def get(self, rid, detail="full", with_result=True):
            return {"run_id": rid, "status": "ok", "vintage_id": self.res[rid]["vintage"]["vintage_id"], "error": None}

        def result(self, rid):
            return self.res[rid]
    _A["ns"] = types.SimpleNamespace(cfg=cfg, store=Store(cfg), runs=Runs())
    return _A["ns"]


def pu_shift_profile(s, r):
    """FR4 risk rows by rule (b): risk_link._rows with the PolicyUnit shift as the primary figure."""
    from policyunit import risk_link as RL
    ru, st, at = RL._any_cached_unconditional()
    if not ru or not ru.get("ru"):
        return None
    dist = ru["ru"]["distribution"]
    gb = [d["baza"] for d in sorted((d for d in dist if d["kind"] == "g" and d["baxis"] == "şərtsiz"), key=lambda d: d["il"])]
    rows = RL._rows(s["id"], ("base", "əsas ssenari"), dist, ru["ru"]["metrics"], RL.policy_shift(r["frame"], s, gb), {},
                    ru.get("score_year"), "brauzer: " + st, ru.get("baseline_id"), at, "şərtsiz", None, {}, RISK_NOTE,
                    ("PolicyUnit", RISK_NOTE))
    return {"rows": rows, "status": ["brauzer: " + st], "calls": []}


def run_now(s, req, rid):
    import fr4_bridge, pu, results
    a, t0 = app(), time.perf_counter()
    vin = pu.vintage(a.cfg)
    want = req["engines"] or pu.P("integrate").engines_for_scenario(s)
    r = pu.P("integrate").run_scenario(s, [e for e in want if e in ENGINES])
    st = r["status"]
    r["status"] = {e: st.get(e) or {"status": "yoxdur", "message_az": SKIP_AZ.get(e, "Brauzer rejimi: hesablanmır")} for e in want}
    t_eng = time.perf_counter() - t0
    mode = "none" if req["side_effects"] == "none" else "rules"
    fr4 = fr4_bridge.analyse(s, r, mode, False, None)
    if req["side_effects"] == "full":
        fr4["requested_mode"] = "full"
        fr4["warnings"].append(RISK_NOTE)
        try:
            fr4["risk_profile"] = pu_shift_profile(s, r)
            fr4["esas_menbe"] = ["PolicyUnit"] if fr4["risk_profile"] else []
        except Exception as e:  # noqa: BLE001
            fr4["warnings"].append("Risk profili brauzerdə qurulmadı: %s" % e)
    res = results.build(s, r, fr4, req["kpis"], req["weights"], "full")
    secs = round(time.perf_counter() - t0, 2)
    res.update(run_id=rid, vintage=vin, seconds=secs,
               timings={"engines": round(t_eng, 2), **{"fr4_" + k: v for k, v in fr4.get("timings", {}).items()}, "total": secs})
    return res


def _run(s, body, src):
    import kpi_views, runs
    if not isinstance(body, dict):
        raise ApiError(400, "bad_json", "JSON obyekt gözlənilir")
    a = app()
    req = runs.norm_request(body)
    if req["kpis"] or body.get("kpi_set") or req["weights"]:
        req["kpis"], req["weights"], _ = kpi_views.resolve(a.cfg, body)
    rid, _ = a.runs.submit(s, src, req)
    res = copy.deepcopy(a.runs.result(rid))
    res["cached"] = False
    if req["detail"] == "summary":
        res.pop("effects", None)
    return res


def _route(method, path, b):
    a = app()
    S = a.store
    if method != "POST":
        raise ApiError(405, "method_not_allowed", "Brauzer rejimində yalnız hesablama sorğuları var")
    for sc in (b or {}).get("_local") or [] if isinstance(b, dict) else []:
        if isinstance(sc, dict) and sc.get("id"):
            S.local[sc["id"]] = sc
    if path == "scenarios/validate":
        return S.validate(b)
    if path == "runs":
        if not isinstance(b, dict) or not isinstance(b.get("scenario"), dict):
            raise ApiError(400, "bad_json", "Gövdə {scenario: {...}, ...} formatında olmalıdır")
        return _run(S._require_valid(b["scenario"])["normalised"], b, "adhoc")
    parts = path.split("/")
    if len(parts) == 3 and parts[0] == "scenarios" and parts[2] == "run":
        s, src = S.load(parts[1])
        return _run(s, b or {}, src)
    if path == "compare":
        import compare_views
        return compare_views.compare(a, b, "brauzer")
    raise ApiError(404, "not_found", "Brauzer rejimində bu sorğu yoxdur: POST /%s (yalnız server)" % path)


def handle(method, path, body_json):
    from az_errors import az_exc
    body = json.loads(body_json) if body_json else None
    return webcore.respond(lambda: _route(method, path.strip("/"), body), apicore.dumps, ApiError, az_exc)
