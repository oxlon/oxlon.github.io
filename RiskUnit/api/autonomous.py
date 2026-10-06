"""
autonomous — avtonom rejim: (1) gündəlik cədvəl (--schedule HH:MM[,HH:MM]; ilk vaxt tam icra, qalanları gündəlik
monitor; «06:30=full,13:00=daily» kimi açıq rejim də olar), (2) yuxarı axın vintajlarının izlənməsi (--watch):
spine manifestindəki faylların (Macro_OxLon/delivery, MicroUnit/output, Macro_MinistryUnit) hash-i son icranın
output/spine_manifest.csv-dəki hash-dən fərqlənəndə tam icra başladılır. Hamısı hadisələr lentinə və jurnala yazılır.
RISK_NO_NETWORK=1 mühitə ötürülür: axınlar keşdən oxunur.
"""
import hashlib, os, re, threading, time
from datetime import datetime, timedelta

import apidb
from apicore import ApiError, now_iso

SCHED_RE = re.compile(r"^(\d{1,2}):(\d{2})(?:\s*[=@]\s*(daily|full|pipeline))?$")


def parse_schedule(s):
    """'06:30,13:00' → [(6,30,'full'), (13,0,'daily')]; '07:00=daily' explicit. ValueError on bad input."""
    out = []
    for i, part in enumerate(x.strip() for x in str(s or "").split(",")):
        if not part:
            continue
        m = SCHED_RE.match(part)
        if not m:
            raise ValueError("cədvəl HH:MM[=daily|full] formatında olmalıdır: %r" % part)
        h, mi = int(m.group(1)), int(m.group(2))
        if not (0 <= h <= 23 and 0 <= mi <= 59):
            raise ValueError("vaxt yanlışdır: %r" % part)
        out.append((h, mi, m.group(3) or ("full" if i == 0 else "daily")))
    if not out:
        raise ValueError("cədvəl boşdur")
    if len({(h, m) for h, m, _ in out}) != len(out):
        raise ValueError("cədvəldə təkrarlanan vaxt var")
    return sorted(out)


def next_run(slots, now=None):
    """Next (datetime, mode) strictly after `now` (local time)."""
    now = now or datetime.now()
    cands = []
    for h, m, mode in slots:
        t = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if t <= now:
            t += timedelta(days=1)
        cands.append((t, mode))
    return min(cands)


class Scheduler(threading.Thread):
    def __init__(self, cfg, runs, slots, log=print, tick=20.0):
        super().__init__(daemon=True, name="risk-scheduler")
        self.cfg, self.runs, self.slots, self.log, self.tick = cfg, runs, slots, log, tick
        self.next, self.next_mode = next_run(slots)
        self.last, self.stop_ev = None, threading.Event()

    def state(self):
        return {"slots": ["%02d:%02d=%s" % s for s in self.slots], "next": self.next.isoformat(timespec="minutes"),
                "next_mode": self.next_mode, "last": self.last}

    def run(self):
        while not self.stop_ev.wait(self.tick):
            if datetime.now() >= self.next:
                self.fire(self.next_mode)
                self.next, self.next_mode = next_run(self.slots)

    def fire(self, mode):
        try:
            job = self.runs.start(mode=mode, actor="cədvəl", trigger="cədvəl")
            self.last = {"at": now_iso(), "mode": mode, "job_id": job["id"]}
        except ApiError as e:
            self.last = {"at": now_iso(), "mode": mode, "skipped": e.message}
            apidb.event(self.cfg.db, "schedule.skipped", "Cədvəl üzrə yeniləmə buraxıldı: %s" % e.message, {"mode": mode})
        self.log("cədvəl: %s" % self.last)
        return self.last


def upstream_files():
    from riskunit import config
    files = {}
    for d in (config.MACRO_FILES, config.MICRO_FILES, config.MACRO_FILES_V2, config.MICRO_FILES_V2, config.MINISTRY_FILES):
        files.update({k: p for k, p in d.items()})
    return files


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


class Watcher(threading.Thread):
    """Polls (size, mtime) of every spine file; on change hashes it and compares with the last run's manifest."""

    def __init__(self, cfg, runs, poll=300.0, log=print, files=None, mode="full"):
        super().__init__(daemon=True, name="risk-watcher")
        self.cfg, self.runs, self.poll, self.log, self.mode = cfg, runs, poll, log, mode
        self._files = files
        self.stat, self.pending, self.last_scan, self.detected = {}, {}, None, []
        self.stop_ev = threading.Event()

    def files(self):
        return self._files() if callable(self._files) else (self._files or upstream_files())

    def manifest_hashes(self):
        import csv
        p = self.cfg.output / "spine_manifest.csv"
        if not p.exists():
            return {}
        with open(p, encoding="utf-8") as f:
            return {r["key"]: r.get("sha256") or "" for r in csv.DictReader(f)}

    def state(self):
        return {"poll_s": self.poll, "files": len(self.stat), "last_scan": self.last_scan, "pending": sorted(self.pending),
                "detected": self.detected[-20:], "mode": self.mode}

    def scan(self):
        """One poll. Returns list of changed keys that triggered (or are waiting for) a run."""
        man = self.manifest_hashes()
        changed = []
        for key, p in self.files().items():
            try:
                st = os.stat(p)
                sig = (st.st_size, st.st_mtime_ns)
            except OSError:
                sig = None
            if self.stat.get(key) == sig and key not in self.pending:
                continue
            self.stat[key] = sig
            h = sha256(p) if sig else ""
            if man and man.get(key, "") != h and not (h == "" and not man.get(key)):
                changed.append(key)
        self.last_scan = now_iso()
        for k in changed:
            self.pending.setdefault(k, now_iso())
        if self.pending:
            keys = sorted(self.pending)
            try:
                job = self.runs.start(mode=self.mode, actor="izləmə", trigger="izləmə (yeni vintaj)",
                                      note="dəyişən: " + ", ".join(keys)[:400])
                self.detected.append({"at": now_iso(), "keys": keys, "job_id": job["id"]})
                apidb.event(self.cfg.db, "watch.vintage", "Yeni yuxarı axın vintajı: %s → tam icra %s" % (", ".join(keys), job["id"]),
                            {"keys": keys, "job_id": job["id"]})
                self.pending = {}
            except ApiError as e:
                self.log("izləmə: yeni vintaj (%s), amma icra başlamadı: %s — növbəti yoxlamada" % (", ".join(keys), e.message))
        return changed

    def run(self):
        try:
            self.scan()                                   # baseline: records sizes, detects changes since last run
        except Exception as e:                            # pragma: no cover
            self.log("izləmə xətası: %s" % e)
        while not self.stop_ev.wait(self.poll):
            try:
                self.scan()
            except Exception as e:                        # pragma: no cover
                self.log("izləmə xətası: %s" % e)
