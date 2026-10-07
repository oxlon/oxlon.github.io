"""
runs — ssenari hesablamaları (POST scenarios/{id}/run, POST runs): fon axınında, irəliləyiş mərhələləri ilə
(runs/{id}), ləğvetmə, nəticə SQLite-da saxlanılır və keş kimi istifadə olunur (eyni ssenari + parametrlər +
vintaj → yenidən hesablanmır). Mühərriklər ENGINE_LOCK ilə ardıcıl işləyir; RiskUnit çağırışları HTTP-dir.
"""
import hashlib, json, threading, time

import apidb, fr4_bridge, pu, results
from apicore import ApiError, dumps, new_id, now_iso
from az_errors import az_exc

STATUS_AZ = {"running": "gedir", "ok": "hazırdır", "failed": "uğursuz", "cancelled": "ləğv edildi",
             "interrupted": "yarımçıq (server yenidən başladı)", "queued": "növbədə"}
SE_MODES = ("full", "rules", "none")


def norm_request(b):
    b = dict(b or {})
    se = b.get("side_effects", "full")
    se = "full" if se is True else "none" if se is False else str(se)
    if se not in SE_MODES:
        raise ApiError(400, "bad_parameter", "side_effects: full | rules | none olmalıdır")
    eng = b.get("engines") or None
    if eng is not None:
        known = pu.P("config").ENGINE_ORDER
        bad = [e for e in eng if e not in known]
        if bad:
            raise ApiError(400, "bad_parameter", "Naməlum mühərrik(lər): %s (mümkün: %s)" % (", ".join(bad), ", ".join(known)))
    try:
        wait = float(b.get("wait", 60))
    except (TypeError, ValueError):
        raise ApiError(400, "bad_parameter", "wait ədəd olmalıdır (saniyə)")
    return {"engines": eng, "side_effects": se, "risk": bool(b.get("risk", True)), "kpis": b.get("kpis") or None,
            "weights": b.get("weights") or None, "detail": b.get("detail", "full"), "wait": max(0.0, min(wait, 600.0)),
            "force": bool(b.get("force"))}


class Runs:
    def __init__(self, cfg, log=print):
        self.cfg, self.log = cfg, log
        self.live, self.lock = {}, threading.Lock()
        for r in apidb.query(cfg.db, "SELECT id FROM run WHERE status IN ('running','queued')"):
            apidb.execute(cfg.db, "UPDATE run SET status='interrupted', finished=? WHERE id=?", (now_iso(), r["id"]))

    def key(self, s, req, vid):
        k = {"s": s, "e": req["engines"], "se": req["side_effects"], "risk": req["risk"], "v": vid}
        return hashlib.sha1(json.dumps(k, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:24]

    # ------------------------------------------------------------ submit
    def submit(self, s, source, req, actor="api"):
        vin = pu.vintage(self.cfg)
        key = self.key(s, req, vin["vintage_id"])
        if not req["force"]:
            hit = apidb.query(self.cfg.db, "SELECT id FROM run WHERE cache_key=? AND status='ok' ORDER BY finished DESC LIMIT 1",
                              (key,))
            if hit:
                return hit[0]["id"], True
            with self.lock:
                for rid, st in self.live.items():
                    if st.get("key") == key and st["status"] == "running":
                        return rid, False
        rid = new_id("PR")
        st = {"status": "running", "key": key, "cancel": threading.Event(), "t0": time.time(), "steps": [], "pct": 0.0,
              "stage": "start", "stage_az": "Başladı (mühərriklər məşğuldursa növbədə gözləyir)"}
        with self.lock:
            self.live[rid] = st
        apidb.execute(self.cfg.db, "INSERT INTO run(id,scenario_id,source,request,scenario,cache_key,vintage_id,status,actor,started) "
                      "VALUES(?,?,?,?,?,?,?,?,?,?)", (rid, s["id"], source, json.dumps(req, default=str), dumps(s), key,
                                                        vin["vintage_id"], "running", actor, now_iso()))
        apidb.event(self.cfg.db, "run.started", "Hesablama başladı: %s (%s)" % (s["id"], rid), {"run_id": rid, "scenario": s["id"]})
        t = threading.Thread(target=self._work, args=(rid, s, req, vin), daemon=True, name="run-" + rid)
        st["thread"] = t
        t.start()
        return rid, False

    def wait(self, rid, seconds):
        st = self.live.get(rid)
        if st and st.get("thread"):
            st["thread"].join(seconds)

    # ------------------------------------------------------------ work
    def _step(self, rid, kind, label, pct=None):
        st = self.live[rid]
        now = time.time()
        if st["steps"]:
            st["steps"][-1]["seconds"] = round(now - st["steps"][-1]["_t"], 2)
        st["steps"].append({"stage": kind, "stage_az": label, "at": now_iso(), "_t": now})
        st["stage"], st["stage_az"] = kind, label
        st["pct"] = max(st["pct"], pct if pct is not None else min(95.0, st["pct"] + 12.0))
        apidb.event(self.cfg.db, "run.progress", "%s: %s" % (rid, label), {"run_id": rid, "stage": kind, "pct": st["pct"]})

    def _work(self, rid, s, req, vin):
        st = self.live[rid]
        t0 = time.perf_counter()
        try:
            self._step(rid, "engines", "Mühərriklər: %s" % ", ".join(req["engines"] or pu.P("integrate").engines_for_scenario(s)), 5)
            with pu.ENGINE_LOCK:
                if st["cancel"].is_set():
                    raise fr4_bridge.Cancelled()
                r = pu.P("integrate").run_scenario(s, req["engines"])
            t_eng = time.perf_counter() - t0
            st["pct"] = 35.0
            fr4 = fr4_bridge.analyse(s, r, req["side_effects"], req["risk"], self.cfg.risk_api,
                                     step=lambda k, lab: self._step(rid, k, lab), cancelled=st["cancel"].is_set)
            if st["cancel"].is_set():
                raise fr4_bridge.Cancelled()
            self._step(rid, "kpi", "KPI, metodların müqayisəsi, izah", 95)
            res = results.build(s, r, fr4, req["kpis"], req["weights"], "full")
            secs = round(time.perf_counter() - t0, 2)
            res.update(run_id=rid, vintage=vin, seconds=secs,
                       timings={"engines": round(t_eng, 2), **{"fr4_" + k: v for k, v in fr4.get("timings", {}).items()},
                                "total": secs})
            if secs > 30:
                res["warnings"].append("Hesablama %s s çəkdi (hədəf < 30 s)" % str(secs).replace(".", ","))
            self._finish(rid, "ok", result=res, seconds=secs)
        except fr4_bridge.Cancelled:
            self._finish(rid, "cancelled", error="İstifadəçi tərəfindən ləğv edildi", seconds=round(time.perf_counter() - t0, 2))
        except Exception as e:
            self._finish(rid, "failed", error="Hesablama alınmadı: %s" % az_exc(e),
                         detail="%s: %s" % (type(e).__name__, str(e)[:800]), seconds=round(time.perf_counter() - t0, 2))

    def _finish(self, rid, status, result=None, error=None, detail=None, seconds=None):
        st = self.live.get(rid, {})
        if st.get("steps"):
            st["steps"][-1]["seconds"] = round(time.time() - st["steps"][-1]["_t"], 2)
        prog = self._progress(st, status)
        apidb.execute(self.cfg.db, "UPDATE run SET status=?, result=?, error=?, progress=?, finished=?, seconds=? WHERE id=?",
                      (status, dumps(result) if result is not None else None,
                       json.dumps({"message": error, "detail": detail}, ensure_ascii=False) if error else None,
                       dumps(prog), now_iso(), seconds, rid))
        st["status"] = status
        apidb.event(self.cfg.db, "run.finished", "Hesablama bitdi: %s — %s%s" % (rid, STATUS_AZ[status],
                    " (%s s)" % seconds if seconds is not None else ""), {"run_id": rid, "status": status, "seconds": seconds})
        self.log("hesablama %s: %s %s s" % (rid, status, seconds))
        with self.lock:
            self.live.pop(rid, None)

    @staticmethod
    def _progress(st, status):
        steps = [{k: v for k, v in x.items() if k != "_t"} for x in st.get("steps", [])]
        return {"pct": 100.0 if status == "ok" else round(st.get("pct", 0.0), 1), "stage": st.get("stage"),
                "stage_az": st.get("stage_az"), "steps": steps,
                "elapsed": round(time.time() - st["t0"], 1) if st.get("t0") else None}

    # ------------------------------------------------------------ read
    def get(self, rid, detail="full", with_result=True):
        rows = apidb.query(self.cfg.db, "SELECT * FROM run WHERE id=?", (rid,), ("request", "progress", "error"))
        if not rows:
            raise ApiError(404, "not_found", "Hesablama tapılmadı: %s" % rid)
        r = rows[0]
        st = self.live.get(rid)
        out = {"run_id": rid, "scenario_id": r["scenario_id"], "source": r["source"], "status": r["status"],
               "status_az": STATUS_AZ.get(r["status"], r["status"]), "started": r["started"], "finished": r["finished"],
               "seconds": r["seconds"], "vintage_id": r["vintage_id"], "request": r["request"],
               "progress": self._progress(st, "running") if st else r["progress"], "error": r["error"]}
        if with_result and r["status"] == "ok" and r["result"]:
            res = json.loads(r["result"])
            if detail == "summary":
                res.pop("effects", None)
            out["result"] = res
        return out

    def result(self, rid):
        r = apidb.query(self.cfg.db, "SELECT result FROM run WHERE id=? AND status='ok'", (rid,))
        if not r or not r[0]["result"]:
            raise ApiError(404, "not_found", "Hazır hesablama nəticəsi tapılmadı: %s" % rid)
        return json.loads(r[0]["result"])

    def list(self, scenario=None, limit=100):
        sql, args = "SELECT id FROM run", ()
        if scenario:
            sql, args = sql + " WHERE scenario_id=?", (scenario,)
        rows = apidb.query(self.cfg.db, sql + " ORDER BY started DESC LIMIT ?", args + (int(limit),))
        return [self.get(r["id"], with_result=False) for r in rows]

    def latest_ok(self, s, vid):
        """Latest successful run of exactly this (normalised) scenario content at this vintage (not ad-hoc runs)."""
        want = json.loads(dumps(s))
        for r in apidb.query(self.cfg.db, "SELECT id, scenario FROM run WHERE scenario_id=? AND vintage_id=? AND status='ok' "
                             "AND source!='adhoc' ORDER BY finished DESC LIMIT 20", (s["id"], vid)):
            try:
                if json.loads(r["scenario"]) == want:
                    return r["id"]
            except (TypeError, ValueError):
                continue
        return None

    def cancel(self, rid):
        st = self.live.get(rid)
        if not st:
            r = self.get(rid, with_result=False)
            raise ApiError(409, "not_running", "Hesablama artıq işləmir (vəziyyət: %s)" % r["status_az"])
        st["cancel"].set()
        apidb.event(self.cfg.db, "run.cancel", "Hesablamanın ləğvi tələb olundu: %s" % rid, {"run_id": rid})
        return {"run_id": rid, "cancel_requested": True}

    def busy(self):
        with self.lock:
            return [rid for rid, st in self.live.items() if st["status"] == "running"]
