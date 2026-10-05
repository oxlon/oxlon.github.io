"""
scenario_engine — ssenari mühərriki adapteri (müqavilə §B) və saxlanmış ssenarilər (SQLite).

    microlib.engines.chain.run_chain(overrides_by_module, scenario) -> nəticə
    microlib.engines.<frx>.inputs()                                  -> redaktə edilə bilən girişlər

`microlib` hələ idxal oluna bilmirsə endpoint-lər 503 qaytarır. Uğursuz idxal yadda saxlanmır: mühərrik
hazır olan kimi server yenidən başladılmadan işləyir. Sınaqlar üçün --engine-chain ilə başqa modul
(məs. api/tests/stub_engine.py) göstərilə bilər; o modul `inputs_for(module)` funksiyası da verə bilər.
"""
import importlib, importlib.util, inspect, json, sys, threading, time

import apidb
from apicore import ApiError, DB_LOCK, MODULES, SCENARIOS, jsonable, module_name, new_id, now_iso

UNAVAILABLE = ("Ssenari mühərriki hələ mövcud deyil: «%s» modulu yüklənmədi. Mühərrik modulları (microlib/engines) "
               "ayrıca hazırlanır; hazır olduqda bu endpoint server yenidən başladılmadan işləyəcək.")


class Engine:
    def __init__(self, cfg):
        self.cfg = cfg
        self._chain = None
        self.lock = threading.Lock()

    def _paths(self):
        for p in reversed(self.cfg.engine_paths or []):
            if p not in sys.path:
                sys.path.insert(0, p)

    def _import(self, name):
        self._paths()
        try:
            return importlib.import_module(name)
        except Exception as e:
            raise ApiError(503, "engine_unavailable", UNAVAILABLE % name, detail="%s: %s" % (type(e).__name__, e))

    def chain(self):
        if self._chain is None:
            mod = self._import(self.cfg.engine_chain)
            if not callable(getattr(mod, "run_chain", None)):
                raise ApiError(503, "engine_unavailable", UNAVAILABLE % self.cfg.engine_chain,
                               detail="modulda run_chain(overrides_by_module, scenario) funksiyası yoxdur")
            self._chain = mod
        return self._chain

    def available(self):
        """Ucuz yoxlama (idxal etmədən, find_spec ilə) — /status üçün."""
        if self._chain is not None:
            return {"available": True, "module": self.cfg.engine_chain}
        self._paths()
        try:
            ok = importlib.util.find_spec(self.cfg.engine_chain) is not None
        except (ImportError, ValueError) as e:
            return {"available": False, "module": self.cfg.engine_chain, "message": UNAVAILABLE % self.cfg.engine_chain,
                    "detail": str(e)}
        return {"available": ok, "module": self.cfg.engine_chain,
                **({} if ok else {"message": UNAVAILABLE % self.cfg.engine_chain})}

    def inputs(self, module):
        m = module_name(module)
        ch = self.chain()
        try:
            if callable(getattr(ch, "inputs_for", None)):
                res = ch.inputs_for(m)
            else:
                res = self._import("%s.%s" % (self.cfg.engine_pkg, m.lower())).inputs()
        except ApiError:
            raise
        except Exception as e:
            raise ApiError(500, "engine_error", "%s mühərrikinin girişləri oxunmadı" % m, detail="%s: %s" % (type(e).__name__, e))
        return {"module": m, "inputs": jsonable(res)}

    def run(self, overrides, scenario="Baseline", modules=None):
        if overrides is None:
            overrides = {}
        if not isinstance(overrides, dict):
            raise ApiError(400, "bad_request", "«overrides» obyekt olmalıdır: {modul: {exogenous, coefficients, levers}}")
        ov = {}
        for k, v in overrides.items():
            m = module_name(k)
            if not isinstance(v, dict):
                raise ApiError(400, "bad_request", "«overrides.%s» obyekt olmalıdır" % k)
            unknown = sorted(set(v) - {"exogenous", "coefficients", "levers"})
            if unknown:
                raise ApiError(400, "bad_request", "«overrides.%s» daxilində naməlum açarlar: %s (exogenous, coefficients, levers gözlənilir)"
                               % (k, ", ".join(unknown)))
            ov[m] = v
        if scenario not in SCENARIOS:
            raise ApiError(400, "bad_parameter", "Ssenari yanlışdır: %r. Mümkün olanlar: %s" % (scenario, ", ".join(SCENARIOS)))
        kw = {}
        if modules:
            if not isinstance(modules, (list, tuple)):
                raise ApiError(400, "bad_request", "«modules» siyahı olmalıdır, məs. [\"FR1\", \"FR3\"]")
            kw["modules"] = [module_name(m) for m in modules]
        ch = self.chain()
        if kw and "modules" not in inspect.signature(ch.run_chain).parameters:
            kw = {}
        t0 = time.time()
        with self.lock:
            try:
                res = ch.run_chain(ov, scenario, **kw)
            except (ValueError, KeyError, TypeError) as e:
                raise ApiError(400, "bad_overrides", "Ssenari parametrləri qəbul edilmədi: %s" % e, detail=type(e).__name__)
            except Exception as e:
                raise ApiError(500, "engine_error", "Ssenari hesablanarkən xəta baş verdi", detail="%s: %s" % (type(e).__name__, e))
        return {"scenario": scenario, "overrides": ov, "modules": kw.get("modules"), "seconds": round(time.time() - t0, 3),
                "result": jsonable(res)}


# ------------------------------------------------------------------ saved scenarios
def saved_list(db, author=None, limit=200):
    con = apidb.conn(db)
    sql, args = "SELECT id,name,author,scenario,note,created_at,updated_at, result IS NOT NULL AS has_result FROM scenario_saved", []
    if author:
        sql += " WHERE author=?"
        args.append(author)
    sql += " ORDER BY updated_at DESC LIMIT ?"
    return [dict(r, has_result=bool(r["has_result"])) for r in con.execute(sql, args + [limit])]


def saved_get(db, sid):
    r = apidb.row(apidb.conn(db).execute("SELECT * FROM scenario_saved WHERE id=?", (sid,)).fetchone(), ("overrides", "result"))
    if not r:
        raise ApiError(404, "not_found", "Saxlanmış ssenari tapılmadı: %s" % sid)
    return r


def saved_put(db, body, actor):
    if not isinstance(body, dict):
        raise ApiError(400, "bad_request", "JSON obyekt gözlənilir")
    name = str(body.get("name") or "").strip()
    if not name:
        raise ApiError(400, "bad_request", "«name» (ssenarinin adı) tələb olunur")
    scen = body.get("scenario") or "Baseline"
    if scen not in SCENARIOS:
        raise ApiError(400, "bad_parameter", "Ssenari yanlışdır: %r" % scen)
    ov = body.get("overrides") or {}
    if not isinstance(ov, dict):
        raise ApiError(400, "bad_request", "«overrides» obyekt olmalıdır")
    for k in ov:
        module_name(k)
    author = str(body.get("author") or actor or "api")[:120]
    ts, con = now_iso(), apidb.conn(db)
    res = json.dumps(jsonable(body["result"]), ensure_ascii=False) if body.get("result") is not None else None
    sid = body.get("id")
    with DB_LOCK:
        if sid and con.execute("SELECT 1 FROM scenario_saved WHERE id=?", (sid,)).fetchone():
            con.execute("UPDATE scenario_saved SET name=?, author=?, scenario=?, overrides=?, result=COALESCE(?, result), note=?, "
                        "updated_at=? WHERE id=?", (name, author, scen, json.dumps(ov, ensure_ascii=False), res,
                                                    body.get("note"), ts, sid))
            created = False
        else:
            sid = new_id("s")
            con.execute("INSERT INTO scenario_saved(id,name,author,scenario,overrides,result,note,created_at,updated_at) "
                        "VALUES(?,?,?,?,?,?,?,?,?)", (sid, name, author, scen, json.dumps(ov, ensure_ascii=False), res,
                                                      body.get("note"), ts, ts))
            created = True
        con.commit()
    return saved_get(db, sid), created


def saved_delete(db, sid):
    con = apidb.conn(db)
    with DB_LOCK:
        n = con.execute("DELETE FROM scenario_saved WHERE id=?", (sid,)).rowcount
        con.commit()
    if not n:
        raise ApiError(404, "not_found", "Saxlanmış ssenari tapılmadı: %s" % sid)
    return {"deleted": sid}
