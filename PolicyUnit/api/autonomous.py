"""
autonomous — avtonom rejim: (1) gündəlik cədvəl (--schedule HH:MM[,HH:MM]) → run_all.py; (2) yuxarı axın
vintajlarının izlənməsi (--watch): MicroUnit/output, RiskUnit/output (baseline_id, σ, tədbirlər), CAEM (Nazirlik
nüsxəsi + PolicyUnit-in sabitlənmiş nüsxəsi), OxLon çatdırılması, IO məlumatı (data/io), konfiqurasiya
(config/*.csv, ssenarilər). Faylın məzmun hash-i son uğurlu icranın manifestindən (logs/api/upstream_manifest.json)
fərqlənəndə və dəyişikliklər bir yoxlama intervalı ərzində sabit qalanda run_all.py başladılır. Hamısı hadisələr
lentinə yazılır. (RiskUnit/api/autonomous.py-dən uyğunlaşdırılıb.)
"""
import hashlib, json, os, re, threading
from datetime import datetime, timedelta
from pathlib import Path

import apidb, pu
from apicore import ApiError, now_iso, read_json

SCHED_RE = re.compile(r"^(\d{1,2}):(\d{2})$")


def parse_schedule(s):
    """'06:30,13:00' → [(6,30), (13,0)]. ValueError on bad input."""
    out = []
    for part in (x.strip() for x in str(s or "").split(",")):
        if not part:
            continue
        m = SCHED_RE.match(part)
        if not m:
            raise ValueError("cədvəl HH:MM formatında olmalıdır: %r" % part)
        h, mi = int(m.group(1)), int(m.group(2))
        if not (0 <= h <= 23 and 0 <= mi <= 59):
            raise ValueError("vaxt yanlışdır: %r" % part)
        out.append((h, mi))
    if not out:
        raise ValueError("cədvəl boşdur")
    if len(set(out)) != len(out):
        raise ValueError("cədvəldə təkrarlanan vaxt var")
    return sorted(out)


def next_run(slots, now=None):
    now = now or datetime.now()
    cands = []
    for h, m in slots:
        t = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if t <= now:
            t += timedelta(days=1)
        cands.append(t)
    return min(cands)


class Scheduler(threading.Thread):
    def __init__(self, cfg, runs, slots, log=print, tick=20.0):
        super().__init__(daemon=True, name="policy-scheduler")
        self.cfg, self.runs, self.slots, self.log, self.tick = cfg, runs, slots, log, tick
        self.next = next_run(slots)
        self.last, self.stop_ev = None, threading.Event()

    def state(self):
        return {"slots": ["%02d:%02d" % s for s in self.slots], "next": self.next.isoformat(timespec="minutes"), "last": self.last}

    def run(self):
        while not self.stop_ev.wait(self.tick):
            if datetime.now() >= self.next:
                self.fire()
                self.next = next_run(self.slots)

    def fire(self):
        try:
            job = self.runs.start(actor="cədvəl", trigger="cədvəl")
            self.last = {"at": now_iso(), "job_id": job["id"]}
        except ApiError as e:
            self.last = {"at": now_iso(), "skipped": e.message}
            apidb.event(self.cfg.db, "schedule.skipped", "Cədvəl üzrə yeniləmə buraxıldı: %s" % e.message)
        self.log("cədvəl: %s" % self.last)
        return self.last


def upstream_files(cfg):
    """{key: path} of every upstream input whose content defines the baseline vintage."""
    c = pu.P("config")
    out = {}

    def add(group, base, pattern="*", recursive=False):
        base = Path(base)
        if base.is_file():
            out["%s:%s" % (group, base.name)] = base
            return
        if not base.is_dir():
            return
        for p in sorted(base.rglob(pattern) if recursive else base.glob(pattern)):
            if p.is_file() and not p.name.startswith((".", "~$", "Icon")):
                out["%s:%s" % (group, p.relative_to(base).as_posix())] = p
    for pat in ("*.csv", "*.json"):
        add("micro", c.MICRO_ROOT / "output", pat)
    add("micro", c.MICRO_ROOT / "data" / "macro_module" / "fr345_public_sources_panel.csv")
    for n in ("_run_summary_v2.json", "S0_factor_sigma.csv", "FR2_risk_scores.csv", "FR3_measures_register.csv"):
        add("risk", c.RISK_ROOT / "output" / n)
    if Path(c.CAEM_UPSTREAM).is_file():
        out["caem:upstream"] = Path(c.CAEM_UPSTREAM)
    if Path(c.CAEM_COPY).is_file():
        out["caem:copy"] = Path(c.CAEM_COPY)
    for n in ("forecast_long.csv", "assumptions.csv", "equations_catalog.csv"):
        add("oxlon", c.OXLON_ROOT / "delivery" / "2_neticeler" / n)
    add("oxlon", c.OXLON_ROOT / "delivery" / "4_melumat" / "macro_annual.csv")
    add("io", Path(c.DATA) / "io", "*", recursive=True)
    add("config", cfg.config_dir, "*.csv")
    add("config", cfg.scenarios_dir, "*.json")
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


class Watcher(threading.Thread):
    """Polls (size, mtime) of every upstream file; on change hashes it and compares with the last run's manifest."""

    def __init__(self, cfg, runs, poll=300.0, log=print, files=None):
        super().__init__(daemon=True, name="policy-watcher")
        self.cfg, self.runs, self.poll, self.log = cfg, runs, poll, log
        self._files = files
        self.stat, self.hash, self.pending, self.last_scan, self.detected = {}, {}, {}, None, []
        self.snap, self.stop_ev = {}, threading.Event()
        runs.on_start.append(self._on_start)
        runs.on_finish.append(self._on_finish)

    @property
    def manifest_path(self):
        return self.cfg.logs / "upstream_manifest.json"

    def files(self):
        return self._files() if callable(self._files) else (self._files or upstream_files(self.cfg))

    def current(self):
        out = {}
        for key, p in self.files().items():
            try:
                st = os.stat(p)
                sig = (st.st_size, st.st_mtime_ns)
            except OSError:
                continue
            if self.stat.get(key) != sig or key not in self.hash:
                self.stat[key], self.hash[key] = sig, sha256(p)
            out[key] = self.hash[key]
        return out

    def _on_start(self, jid):
        self.snap[jid] = self.current()

    def _on_finish(self, job):
        snap = self.snap.pop(job["id"], None)
        if job.get("status") == "ok" and snap is not None:
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
            self.manifest_path.write_text(json.dumps({"job_id": job["id"], "at": now_iso(), "files": snap},
                                                     ensure_ascii=False), encoding="utf-8")

    def state(self):
        return {"poll_s": self.poll, "files": len(self.stat), "last_scan": self.last_scan, "pending": sorted(self.pending),
                "detected": self.detected[-20:], "manifest": str(self.manifest_path) if self.manifest_path.exists() else None}

    def scan(self):
        """One poll. Returns the keys that differ from the manifest (a run starts once they are stable)."""
        cur = self.current()
        man = (read_json(self.manifest_path) or {}).get("files")
        self.last_scan = now_iso()
        if man is None:                        # first start: compare MicroUnit/CAEM vintage with the last run_all
            meta = pu.last_run_meta(self.cfg).get("vintage") or {}
            v = pu.vintage(self.cfg)
            stale = [k for k, mk in (("micro_vintage", "micro_vintage"), ("caem_md5", "caem_md5"))
                     if meta.get(mk) and meta.get(mk) != v.get(k)]
            changed = ["vintage:" + k for k in stale]
            if not changed:
                self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
                self.manifest_path.write_text(json.dumps({"job_id": None, "at": now_iso(), "files": cur,
                                                          "note": "ilk skan — baza manifest"}), encoding="utf-8")
        else:
            changed = sorted(k for k in set(cur) | set(man) if cur.get(k) != man.get(k))
        fresh = [k for k in changed if k not in self.pending]
        for k in fresh:
            self.pending[k] = now_iso()
        for k in list(self.pending):
            if k not in changed:
                self.pending.pop(k)
        if self.pending and not fresh:         # stable for one interval → run
            keys = sorted(self.pending)
            try:
                job = self.runs.start(actor="izləmə", trigger="izləmə (yeni vintaj)", note="dəyişən: " + ", ".join(keys)[:400])
                self.detected.append({"at": now_iso(), "keys": keys[:50], "n": len(keys), "job_id": job["id"]})
                apidb.event(self.cfg.db, "watch.vintage", "Yeni yuxarı axın vintajı (%d fayl) → run_all %s" % (len(keys), job["id"]),
                            {"keys": keys[:50], "job_id": job["id"]})
                self.pending = {}
            except ApiError as e:
                self.log("izləmə: yeni vintaj (%d fayl), amma icra başlamadı: %s" % (len(keys), e.message))
        elif fresh:
            apidb.event(self.cfg.db, "watch.change", "Yuxarı axında dəyişiklik (%d fayl) — sabitləşməsi gözlənilir" % len(fresh),
                        {"keys": fresh[:50]})
        return changed

    def run(self):
        while True:
            try:
                self.scan()
            except Exception as e:                        # pragma: no cover
                self.log("izləmə xətası: %s" % e)
            if self.stop_ev.wait(self.poll):
                return
