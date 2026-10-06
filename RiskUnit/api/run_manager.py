"""
run_manager — yeniləmə işləri (update.py --daily / --full, run_all.py) fon prosesi kimi: eyni anda yalnız biri,
jurnal (logs/api/<id>.log), mərhələ irəliləyişi (jurnaldakı «[HH:MM:SS] A0 ...» sətirlərindən), ləğvetmə.

Kilid: prosesdaxili + fayl sistemi kilidi output/.update.lock (scheduler/run_update.sh ilə eyni mkdir kilidi),
beləliklə cron/launchd və API eyni anda boru xəttini işə salmır. API-nin sahibliyi yanındakı
output/.update.lock.api.json faylında qeyd olunur (kilid qovluğu boş qalmalıdır: skript rmdir edir).
"""
import json, os, re, signal, subprocess, sys, threading, time
from pathlib import Path

import apidb
from apicore import ApiError, new_id, now_iso, read_json

STAGE_RE = re.compile(r"^\[(\d\d:\d\d:\d\d)\]\s+(\S+)\s+(.*)$")
STATUS_AZ = {"running": "gedir", "ok": "uğurlu", "failed": "uğursuz", "cancelled": "ləğv edildi",
             "interrupted": "yarımçıq (server yenidən başladı)"}
MODES = ("daily", "full", "pipeline")


def pid_alive(pid):
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def tail_lines(path, n=200):
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 128 * 1024))
            return f.read().decode("utf-8", errors="replace").splitlines()[-n:]
    except OSError:
        return []


class RefreshManager:
    def __init__(self, cfg, log=print):
        self.cfg, self.log = cfg, log
        self.lock = threading.RLock()
        self.proc, self.current = None, None
        self.on_finish = []
        cfg.logs.mkdir(parents=True, exist_ok=True)
        self._recover()

    @property
    def owner_file(self):
        return self.cfg.output / ".update.lock.api.json"

    def _recover(self):
        for r in apidb.query(self.cfg.db, "SELECT id,pid FROM job WHERE status='running'"):
            if not pid_alive(r["pid"]):
                apidb.execute(self.cfg.db, "UPDATE job SET status='interrupted', finished=? WHERE id=?", (now_iso(), r["id"]))
        own = read_json(self.owner_file)
        if own and not pid_alive(own.get("pid")) and self.cfg.lock_dir.is_dir():
            try:
                self.cfg.lock_dir.rmdir()                    # stale lock left by a killed API job
            except OSError:
                pass
        if own and not pid_alive(own.get("pid")):
            self.owner_file.unlink(missing_ok=True)

    # ------------------------------------------------------------ state
    def busy(self):
        with self.lock:
            if self.proc is not None and self.proc.poll() is None:
                return {"job_id": self.current, "source": "api"}
        if self.cfg.lock_dir.is_dir():
            return {"job_id": None, "source": "xarici (cron/launchd və ya komanda sətri)",
                    "since": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self.cfg.lock_dir.stat().st_mtime))}
        return None

    def command(self, mode, no_fetch):
        if self.cfg.refresh_cmd:
            return list(self.cfg.refresh_cmd)
        py = self.cfg.python or sys.executable
        if mode == "pipeline":
            return [py, str(self.cfg.root / "run_all.py"), "--no-pdf"]
        return [py, str(self.cfg.root / "update.py"), "--" + mode] + (["--no-fetch"] if no_fetch else [])

    def expected_stages(self, mode):
        d = read_json(self.cfg.output / "_run_summary_daily.json") or {}
        f = read_json(self.cfg.output / "_run_summary_v2.json") or {}
        nd = len(d.get("merheleler") or []) or 6
        nf = len([s for s in (f.get("merheleler") or []) if not str(s.get("stage", "")).startswith("A")]) or 18
        return {"daily": nd, "full": nd + nf, "pipeline": nd + nf}.get(mode, nd)

    # ------------------------------------------------------------ start
    def start(self, mode="daily", no_fetch=False, actor="api", trigger="api", note=None):
        if mode not in MODES:
            raise ApiError(400, "bad_parameter", "Naməlum rejim: %r. Mümkün olanlar: %s" % (mode, ", ".join(MODES)))
        with self.lock:
            b = self.busy()
            if b:
                raise ApiError(409, "busy", "Hazırda başqa yeniləmə gedir (%s). Bitməsini gözləyin və ya ləğv edin."
                               % (b["job_id"] or b["source"]), extra={"running": b})
            try:
                self.cfg.lock_dir.mkdir()
            except FileExistsError:
                raise ApiError(409, "busy", "Yeniləmə kilidi tutulub (output/.update.lock)")
            jid = new_id("R")
            logp = self.cfg.logs / ("%s.log" % jid)
            cmd = self.command(mode, no_fetch)
            env = dict(os.environ, PYTHONUNBUFFERED="1")
            try:
                out = open(logp, "ab")
                out.write(("%s başladı: %s (tətik: %s%s)\n" % (now_iso(), " ".join(cmd), trigger,
                                                              "; RISK_NO_NETWORK=1" if env.get("RISK_NO_NETWORK") == "1" else "")).encode())
                out.flush()
                p = subprocess.Popen(cmd, cwd=str(self.cfg.root), stdout=out, stderr=subprocess.STDOUT,
                                     stdin=subprocess.DEVNULL, env=env, start_new_session=True)
                out.close()
            except Exception:
                self.cfg.lock_dir.rmdir()
                raise
            self.owner_file.write_text(json.dumps({"pid": p.pid, "job_id": jid, "started": now_iso()}), encoding="utf-8")
            apidb.execute(self.cfg.db, "INSERT INTO job(id,mode,trigger,actor,status,command,pid,started,log,note) "
                          "VALUES(?,?,?,?,?,?,?,?,?,?)", (jid, mode, trigger, actor, "running", json.dumps(cmd), p.pid,
                                                          now_iso(), str(logp), note))
            self.proc, self.current, self._t0 = p, jid, time.time()
            threading.Thread(target=self._wait, args=(jid, p, time.time()), daemon=True, name="refresh-" + jid).start()
        apidb.event(self.cfg.db, "refresh.started", "Yeniləmə başladı: %s (%s, %s)" % (jid, mode, trigger),
                    {"job_id": jid, "mode": mode, "trigger": trigger})
        self.log("yeniləmə başladı: %s %s" % (jid, " ".join(cmd)))
        return self.get(jid)

    def _wait(self, jid, p, t0):
        rc = p.wait()
        cancelled = (self.cfg.logs / ("%s.cancel" % jid)).exists()
        status = "cancelled" if cancelled else ("ok" if rc == 0 else "failed")
        apidb.execute(self.cfg.db, "UPDATE job SET status=?, finished=?, seconds=?, returncode=? WHERE id=?",
                      (status, now_iso(), round(time.time() - t0, 1), rc, jid))
        with self.lock:
            if self.current == jid:
                self.proc, self.current = None, None
            self.owner_file.unlink(missing_ok=True)
            try:
                self.cfg.lock_dir.rmdir()
            except OSError:
                pass
        with open(self.cfg.logs / ("%s.log" % jid), "ab") as f:
            f.write(("%s bitdi: kod %s — %s\n" % (now_iso(), rc, STATUS_AZ[status])).encode())
        apidb.event(self.cfg.db, "refresh.finished", "Yeniləmə bitdi: %s — %s" % (jid, STATUS_AZ[status]),
                    {"job_id": jid, "returncode": rc, "status": status})
        self.log("yeniləmə bitdi: %s %s" % (jid, status))
        for cb in list(self.on_finish):
            try:
                cb(self.get(jid))
            except Exception:
                pass

    # ------------------------------------------------------------ cancel
    def cancel(self, jid):
        with self.lock:
            if self.current != jid or self.proc is None or self.proc.poll() is not None:
                r = self.get(jid)
                if not r:
                    raise ApiError(404, "not_found", "Yeniləmə işi tapılmadı: %s" % jid)
                raise ApiError(409, "not_running", "İş artıq işləmir (vəziyyət: %s)" % r["status_az"])
            p = self.proc
        (self.cfg.logs / ("%s.cancel" % jid)).write_text(now_iso(), encoding="utf-8")

        def escalate():
            for sig, wait in ((signal.SIGTERM, 15), (signal.SIGKILL, 10)):
                try:
                    os.killpg(p.pid, sig)
                except OSError:
                    return
                t0 = time.time()
                while time.time() - t0 < wait:
                    if p.poll() is not None:
                        return
                    time.sleep(0.2)
        threading.Thread(target=escalate, daemon=True).start()
        apidb.event(self.cfg.db, "refresh.cancel", "Yeniləmənin ləğvi tələb olundu: %s" % jid, {"job_id": jid})
        return {"job_id": jid, "cancel_requested": True}

    # ------------------------------------------------------------ read
    def get(self, jid, tail=60):
        rows = apidb.query(self.cfg.db, "SELECT * FROM job WHERE id=?", (jid,), ("command",))
        if not rows:
            return None
        r = rows[0]
        r["status_az"] = STATUS_AZ.get(r["status"], r["status"])
        lines = tail_lines(r["log"], 4000) if r.get("log") else []
        stages = [m.groups() for m in (STAGE_RE.match(x) for x in lines) if m]
        exp = self.expected_stages(r["mode"])
        done = len(stages)
        r["progress"] = {"stage": stages[-1][1] if stages else None, "name": stages[-1][2] if stages else None,
                         "done": done, "expected": exp,
                         "pct": 100.0 if r["status"] == "ok" else round(min(99.0, 100.0 * done / max(exp, 1)), 1)}
        if r["status"] == "running":
            r["seconds"] = round(time.time() - getattr(self, "_t0", time.time()), 1)
        r["log_tail"] = lines[-int(tail):] if tail else []
        return r

    def list(self, limit=50):
        rows = apidb.query(self.cfg.db, "SELECT * FROM job ORDER BY started DESC LIMIT ?", (int(limit),), ("command",))
        for r in rows:
            r["status_az"] = STATUS_AZ.get(r["status"], r["status"])
        return rows

    def active(self):
        with self.lock:
            cur = self.current
        return self.get(cur, tail=20) if cur else None
