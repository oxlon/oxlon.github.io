"""
run_manager — run_all.py-ni fon prosesi kimi işə salır, izləyir və ləğv edir. Eyni anda yalnız bir icra.

Vəziyyət SQLite-dakı `run` cədvəlində, canlı irəliləyiş logs/<run_id>/progress.json-da, yekun
logs/<run_id>/manifest.json-da. İcra gedərkən yeni tələb gəlsə: API 409 qaytarır; avtonom rejim və
`?run=1` ilə tətbiq isə tələbi növbəyə qoyur (mərhələlər birləşdirilir) və cari icra bitəndə başladır.
"""
import importlib.util, json, os, signal, subprocess, sys, threading, time
from pathlib import Path

import apidb
from apicore import API_DIR, ApiError, DB_LOCK, now_iso, read_json

_dwb, sys.dont_write_bytecode = sys.dont_write_bytecode, True          # never leave __pycache__ in MicroUnit/
_spec = importlib.util.spec_from_file_location("run_all", str(API_DIR.parent / "run_all.py"))
run_all = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_all)
sys.dont_write_bytecode = _dwb
STAGES, DEPS, downstream, RUN_ID_RE = run_all.STAGES, run_all.DEPS, run_all.downstream, run_all.RUN_ID_RE


def pid_alive(pid):
    if not pid:
        return False
    try:
        if os.name == "nt":                                          # pragma: no cover
            out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid], capture_output=True, text=True).stdout
            return str(pid) in out
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def tail(path, n=40):
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 64 * 1024))
            txt = f.read().decode("utf-8", errors="replace")
    except OSError:
        return None
    return "\n".join(run_all.ANSI.sub("", txt).splitlines()[-n:])


class RunManager:
    def __init__(self, cfg):
        self.cfg = cfg
        self.lock = threading.RLock()
        self.proc, self.current, self.pending = None, None, None
        self.on_finish = []                                          # callbacks(run_row)
        self._recover()

    def _recover(self):
        con = apidb.conn(self.cfg.db)
        with DB_LOCK:
            for r in con.execute("SELECT id,pid FROM run WHERE status IN ('queued','running')").fetchall():
                if not pid_alive(r["pid"]):
                    con.execute("UPDATE run SET status='interrupted', finished_at=?, error=? WHERE id=?",
                                (now_iso(), "server yenidən başladı — icranın nəticəsi naməlumdur", r["id"]))
            con.commit()

    # ------------------------------------------------------------ state
    def external(self):
        info = read_json(self.cfg.logs / ".run_all.pid")
        return info if info and pid_alive(info.get("pid")) else None

    def busy(self):
        with self.lock:
            if self.proc is not None and self.proc.poll() is None:
                return {"run_id": self.current, "source": "api"}
        ext = self.external()
        return {"run_id": ext.get("run_id"), "source": "cli"} if ext else None

    @staticmethod
    def make_plan(stage=None, only=None, stages=None, skip_build=False):
        try:
            if stages:
                stage = ",".join(stages) if isinstance(stages, (list, tuple, set)) else str(stages)
            st, builds = run_all.plan(stage, only, skip_build)
        except ValueError as e:
            raise ApiError(400, "bad_stage", "Mərhələ yanlışdır: %s" % e)
        return stage, only, st + builds

    # ------------------------------------------------------------ start / queue
    def start(self, stage=None, only=None, stages=None, skip_build=False, dry_run=False, snapshot=None,
              actor="api", trigger="api"):
        stage, only, plan = self.make_plan(stage, only, stages, skip_build)
        with self.lock:
            b = self.busy()
            if b:
                raise ApiError(409, "busy", "Hazırda başqa icra gedir (%s, %s). Bitməsini gözləyin və ya ləğv edin."
                               % (b.get("run_id"), "API" if b["source"] == "api" else "komanda sətri"), extra={"running": b})
            rid = run_all.new_run_id()
            dry = bool(dry_run or self.cfg.dry_run_runs)
            args = [self.cfg.python or sys.executable, str(self.cfg.runner), "--run-id", rid, "--trigger", trigger,
                    "--root", str(self.cfg.root), "--timeout", str(self.cfg.stage_timeout)]
            args += ["--stage", stage] if stage else (["--only", only] if only else [])
            if skip_build:
                args.append("--skip-build")
            if dry:
                args.append("--dry-run")
            if snapshot if snapshot is not None else self.cfg.snapshot:
                args += ["--snapshot", "--keep", str(self.cfg.keep_vintages)]
            args += list(self.cfg.run_extra_args or [])
            ldir = self.cfg.logs / rid
            ldir.mkdir(parents=True, exist_ok=True)
            out = open(ldir / "orchestrator.out", "ab")
            kw = {"start_new_session": True} if os.name != "nt" else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
            p = subprocess.Popen(args, cwd=str(self.cfg.root), stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, **kw)
            out.close()
            req = {"stage": stage, "only": only, "skip_build": skip_build, "dry_run": dry, "snapshot": snapshot}
            con = apidb.conn(self.cfg.db)
            with DB_LOCK:
                con.execute("INSERT INTO run(id,status,request,plan,actor,trigger,pid,created_at,started_at,log_dir) "
                            "VALUES(?,?,?,?,?,?,?,?,?,?)", (rid, "running", json.dumps(req), json.dumps(plan), actor, trigger,
                                                            p.pid, now_iso(), now_iso(), "logs/%s" % rid))
                con.commit()
            self.proc, self.current = p, rid
            threading.Thread(target=self._wait, args=(rid, p), daemon=True, name="run-" + rid).start()
        apidb.event(self.cfg.db, "run", "İcra başladı: %s (%s)%s" % (rid, " → ".join(plan), " [dry-run]" if dry else ""),
                    {"run_id": rid, "trigger": trigger})
        return self.get(rid)

    def queue(self, stages, actor="api", trigger="auto", **kw):
        """Məşğuldursa mərhələləri növbəyə birləşdirir, deyilsə dərhal başladır."""
        stages = [s for s in STAGES if s in set(stages)]
        if not stages:
            return None
        with self.lock:
            if self.busy():
                cur = set((self.pending or {}).get("stages", []))
                self.pending = {"stages": [s for s in STAGES if s in cur | set(stages)], "actor": actor, "trigger": trigger, **kw}
                apidb.event(self.cfg.db, "run", "İcra növbəyə qoyuldu: %s" % ",".join(self.pending["stages"]))
                return {"queued": True, "stages": self.pending["stages"]}
            return self.start(stages=stages, actor=actor, trigger=trigger, **kw)

    def _wait(self, rid, p):
        rc = p.wait()
        m = read_json(self.cfg.logs / rid / "manifest.json") or {}
        status = m.get("status") or ("ok" if rc == 0 else "failed")
        killed = os.name != "nt" and rc in (-signal.SIGTERM, -signal.SIGKILL)
        if status == "running":
            status = "cancelled" if killed or (self.cfg.logs / rid / "CANCEL").exists() else "failed"
        con = apidb.conn(self.cfg.db)
        with DB_LOCK:
            con.execute("UPDATE run SET status=?, finished_at=?, returncode=?, error=? WHERE id=?",
                        (status, now_iso(), rc, m.get("error"), rid))
            con.commit()
        apidb.event(self.cfg.db, "run", "İcra bitdi: %s — %s" % (rid, status), {"run_id": rid, "returncode": rc})
        with self.lock:
            if self.current == rid:
                self.proc, self.current = None, None
            nxt, self.pending = self.pending, None
        for cb in list(self.on_finish):
            try:
                cb(self.get(rid))
            except Exception:
                pass
        if nxt:
            st = nxt.pop("stages")
            try:
                self.start(stages=st, **nxt)
            except ApiError:
                with self.lock:
                    self.pending = self.pending or dict(nxt, stages=st)

    # ------------------------------------------------------------ cancel
    def cancel(self, rid):
        with self.lock:
            if self.current != rid or self.proc is None or self.proc.poll() is not None:
                r = self.get(rid)
                if not r:
                    raise ApiError(404, "not_found", "İcra tapılmadı: %s" % rid)
                raise ApiError(409, "not_running", "İcra artıq işləmir (vəziyyət: %s)" % r["status"])
            p = self.proc
        (self.cfg.logs / rid / "CANCEL").write_text(now_iso(), encoding="utf-8")   # run_all.py checks it every 0.5 s

        def escalate():
            for sig, wait in ((signal.SIGTERM, 20), (getattr(signal, "SIGKILL", signal.SIGTERM), 10)):
                t0 = time.time()
                while time.time() - t0 < wait:
                    if p.poll() is not None:
                        return
                    time.sleep(0.2)
                try:
                    if os.name != "nt":
                        os.killpg(p.pid, sig)
                    else:                                                # pragma: no cover
                        p.terminate()
                except OSError:
                    return
        threading.Thread(target=escalate, daemon=True).start()
        apidb.event(self.cfg.db, "run", "İcranın ləğvi tələb olundu: %s" % rid)
        return {"run_id": rid, "cancel_requested": True}

    # ------------------------------------------------------------ read
    def get(self, rid, log_lines=40):
        if not RUN_ID_RE.match(rid or ""):
            return None
        con = apidb.conn(self.cfg.db)
        r = apidb.row(con.execute("SELECT * FROM run WHERE id=?", (rid,)).fetchone(), ("request", "plan"))
        ldir = self.cfg.logs / rid
        if r is None:
            if not ldir.is_dir():
                return None
            m = read_json(ldir / "manifest.json") or {}
            r = {"id": rid, "status": m.get("status", "unknown"), "trigger": m.get("trigger", "cli"), "plan": m.get("plan"),
                 "started_at": m.get("started"), "finished_at": m.get("finished"), "log_dir": "logs/%s" % rid, "source": "cli"}
        prog = read_json(ldir / "progress.json") or {}
        r["progress"] = prog
        if r["status"] == "running" and prog.get("status") in ("ok", "failed", "cancelled", "dry-run"):
            r["status_hint"] = prog["status"]
        steps = prog.get("steps") or []
        done = sum(1 for s in steps if s.get("status") in ("ok", "planned"))
        r["percent"] = round(100.0 * done / len(steps), 1) if steps else 0.0
        m = read_json(ldir / "manifest.json")
        if m:
            r["manifest"] = {k: m.get(k) for k in ("status", "dry_run", "started", "finished", "seconds", "error",
                                                    "reproducibility", "snapshot", "dependency_check")}
            r["manifest"]["steps"] = [{k: s.get(k) for k in ("name", "status", "seconds", "error", "log", "deps_detected")}
                                      for s in m.get("steps", [])]
        r["log_tail"] = tail(ldir / "run.log", log_lines) or tail(ldir / "orchestrator.out", log_lines)
        cur = prog.get("current")
        if cur:
            r["stage_log_tail"] = tail(ldir / ("%s.log" % cur), log_lines)
        else:
            failed = next((s for s in steps if s.get("status") in ("failed", "timeout")), None)
            if failed:
                r["stage_log_tail"] = tail(ldir / ("%s.log" % failed["name"]), log_lines)
        r["pending"] = self.pending if self.current == rid else None
        return r

    def list(self, limit=50):
        con = apidb.conn(self.cfg.db)
        rows = [apidb.row(x, ("request", "plan")) for x in
                con.execute("SELECT * FROM run ORDER BY created_at DESC, id DESC LIMIT ?", (limit,))]
        known = {r["id"] for r in rows}
        hist = self.cfg.logs / "history.jsonl"
        if hist.exists():                                       # runs started from the command line
            for line in hist.read_text(encoding="utf-8").splitlines()[-limit:]:
                try:
                    h = json.loads(line)
                except ValueError:
                    continue
                if h.get("run_id") not in known:
                    rows.append({"id": h["run_id"], "status": h.get("status"), "trigger": h.get("trigger", "cli"),
                                 "plan": h.get("plan"), "started_at": h.get("started"), "finished_at": h.get("finished"),
                                 "source": "cli", "identical_to_previous": h.get("identical_to_previous")})
        rows.sort(key=lambda r: r.get("started_at") or r.get("created_at") or "", reverse=True)
        return rows[:limit]

    def last(self):
        rows = self.list(limit=10)
        return rows[0] if rows else None
