"""
autonomous — avtonom rejim: düşmə qovluğunun izlənməsi, gündəlik icra və DSK fayllarının yenilənməsi.

    python3 api/server.py --watch data/inbox_drop --auto-run [--poll 30] [--schedule 06:30] [--dsk-refresh]

* Düşmə qovluğu: hər N saniyədə yoxlanılır. Ölçüsü və vaxtı iki yoxlama arasında dəyişməyən (kopyalanması
  bitmiş) fayl adına/uzantısına görə təsnif edilir (alt qovluq da nəzərə alınır: inbox_drop/dsk_services/x.xls),
  yoxlanılır, tətbiq olunur və --auto-run varsa ilk təsirlənən mərhələdən icra başladılır. Rədd edilən fayl
  inbox_drop/_rejected/ altına hesabatla (<ad>.report.json və <ad>.report.txt) köçürülür; qəbul edilən
  inbox_drop/_applied/ altına. İcra gedərkən fayllar tətbiq edilmir — növbəti yoxlamaya qədər gözləyir.
* --schedule HH:MM: hər gün həmin vaxtda tam icra (--dsk-refresh ilə: əvvəl DSK yenilənir və yalnız
  dəyişiklik olduqda, təsirlənən mərhələlərdən icra).
* --dsk-refresh: modulların manifestlərindəki DSK faylları brauzer User-Agent-i ilə yenidən endirilir,
  sha256 müqayisə olunur, dəyişən fayl köhnəsi data/_replaced/ altına saxlanılaraq əvəz olunur.
  MICRO_NO_NETWORK=1 olduqda endirmə qadağandır (sınaqlar).
"""
import csv, hashlib, json, os, shutil, threading, time, urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import apidb
import nbextract
from apicore import ApiError, now_iso, stamp, write_json
from upload_store import KIND_AZ, classify
from validate_dsk import DSK_DIRS, FR10_LOCAL_DIR, XLS_MAGIC
from az_errors import az_exc

BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/126.0 Safari/537.36")
SKIP_DIRS = {"_rejected", "_applied"}


def is_junk(name):
    return name.startswith((".", "~$")) or (name.startswith("Icon") and len(name) <= 5) or \
        name.endswith((".part", ".crdownload", ".tmp", ".download"))


# ------------------------------------------------------------------ drop folder
class Watcher(threading.Thread):
    def __init__(self, cfg, uploads, runs, folder, poll=30, auto_run=False, log=print):
        super().__init__(daemon=True, name="watcher")
        self.cfg, self.uploads, self.runs = cfg, uploads, runs
        self.folder, self.poll, self.auto_run, self.log = Path(folder), max(1.0, float(poll)), auto_run, log
        self.seen, self.stop_ev = {}, threading.Event()
        self.last_scan, self.processed = None, []
        for d in (self.folder, self.folder / "_rejected", self.folder / "_applied"):
            d.mkdir(parents=True, exist_ok=True)

    def candidates(self):
        out = []
        for p in sorted(self.folder.rglob("*")):
            rel = p.relative_to(self.folder)
            if not p.is_file() or rel.parts[0] in SKIP_DIRS or any(is_junk(x) for x in rel.parts):
                continue
            out.append(p)
        return out

    def scan(self):
        """Bir yoxlama dövrü; işlənmiş faylların siyahısını qaytarır."""
        self.last_scan = now_iso()
        stable = []
        for p in self.candidates():
            st = p.stat()
            sig = (st.st_size, st.st_mtime_ns)
            if self.seen.get(p) == sig:
                stable.append(p)
            self.seen[p] = sig
        if not stable or self.runs.busy():
            return []
        done, stages = [], set()
        for p in stable:
            res = self.process(p)
            self.seen.pop(p, None)
            done.append(res)
            stages |= set(res.get("affected_stages") or [])
        if stages and self.auto_run:
            r = self.runs.queue(sorted(stages), actor="watcher", trigger="watch")
            self.log("avtonom rejim: icra %s" % ((r or {}).get("id") or r))
        self.processed = (done + self.processed)[:100]
        return done

    def process(self, p):
        rel = p.relative_to(self.folder)
        kind, why = classify(p.name)
        sub = None
        if kind == "dsk" and len(rel.parts) > 1:
            sub = "/".join(rel.parts[:-1])
        res = {"file": str(rel), "kind": kind, "at": now_iso()}
        if kind is None:
            return self._reject(p, rel, {"ok": False, "errors": [{"message": why}], "warnings": []}, res)
        try:
            with open(p, "rb") as f:
                up = self.uploads.create(kind, p.name, stream=f, length=p.stat().st_size, subfolder=sub,
                                         actor="watcher", note="düşmə qovluğu: %s" % rel, source="watch")
        except ApiError as e:
            return self._reject(p, rel, {"ok": False, "errors": [{"message": e.message}], "warnings": []}, res)
        rep = up.get("report") or {}
        res["upload_id"] = up["id"]
        if not up["valid"]:
            return self._reject(p, rel, rep, res)
        try:
            ap = self.uploads.apply(up["id"], actor="watcher")
        except ApiError as e:
            rep = dict(rep, ok=False, errors=(rep.get("errors") or []) + [{"message": "Tətbiq edilmədi: " + e.message}])
            return self._reject(p, rel, rep, res)
        dst = self.folder / "_applied" / ("%s_%s" % (stamp(), p.name))
        shutil.move(str(p), str(dst))
        res.update(status="applied", target=ap["target"], affected_stages=ap["apply"].get("affected_stages"))
        self.log("avtonom rejim: %s tətbiq olundu → %s" % (rel, ap["target"]))
        return res

    def _reject(self, p, rel, rep, res):
        dst = self.folder / "_rejected" / p.name
        if dst.exists():
            dst = dst.with_name("%s_%s" % (stamp(), p.name))
        shutil.move(str(p), str(dst))
        write_json(dst.with_name(dst.name + ".report.json"), rep)
        lines = ["Fayl rədd edildi: %s" % rel, "Vaxt: %s" % now_iso(), ""]
        lines += ["XƏTA: %s%s" % (("sətir %s, %s: " % (e["row"], e.get("field"))) if e.get("row") else "", e.get("message"))
                  for e in (rep.get("errors") or [])[:200]]
        lines += ["XƏBƏRDARLIQ: %s" % w.get("message") for w in (rep.get("warnings") or [])[:50]]
        dst.with_name(dst.name + ".report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        apidb.event(self.cfg.db, "watch", "Düşmə qovluğu: %s rədd edildi" % rel, {"upload_id": res.get("upload_id")})
        self.log("avtonom rejim: %s RƏDD EDİLDİ — %s" % (rel, dst.name + ".report.txt"))
        return dict(res, status="rejected", report=str(dst.relative_to(self.folder)) + ".report.json")

    def run(self):
        while not self.stop_ev.is_set():
            try:
                self.scan()
            except Exception as e:                                   # keep the watcher alive
                self.log("avtonom rejim: yoxlama xətası: %s" % e)
            self.stop_ev.wait(self.poll)


# ------------------------------------------------------------------ DSK refresh
def download(url, timeout=60):
    """Bir faylı brauzer User-Agent-i ilə endirir (vaxt limiti ilə). Sınaqlarda MICRO_NO_NETWORK=1 bunu qadağan edir."""
    if os.environ.get("MICRO_NO_NETWORK") == "1":
        raise RuntimeError("şəbəkə qadağandır (MICRO_NO_NETWORK=1)")
    req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def dsk_targets(cfg):
    """[{url, path (data/-dan nisbi), stage, source}] — FR4/FR5 yükləmə siyahıları və FR10/FR12 manifestləri."""
    root, out, seen = cfg.root, [], set()

    def add(url, rel, stage, src):
        if rel not in seen and url:
            seen.add(rel)
            out.append({"url": url, "path": rel, "stage": stage, "source": src})
    for nb, fl, ul, sub, st in (("FR4", "DSK_FILES", "DSK_URL", "dsk", "FR4"), ("FR5", "SFILES", "SURL", "dsk_services", "FR5")):
        files = nbextract.assigned(root / ("%s.ipynb" % nb), fl, []) or []
        base = nbextract.assigned(root / ("%s.ipynb" % nb), ul, None)
        for fn in files if base else []:
            add(base + fn, "%s/%s" % (sub, fn), st, "%s.ipynb %s" % (nb, fl))
    m10 = cfg.output / "FR10_dsk_manifest.csv"
    if m10.exists():
        tmpl = nbextract.assigned(root / "FR10.ipynb", "DSK_URL", "https://www.stat.gov.az/source/{sec}/en/{fn}")
        for r in _rows(m10):
            d = FR10_LOCAL_DIR.get(r.get("section", ""))
            if d and r.get("file") and str(r.get("status", "")).startswith(("present", "downloaded")):
                add(tmpl.format(sec=r["section"], fn=r["file"]), "dsk_enterprise/%s/%s" % (d, r["file"]), "FR10", "FR10_dsk_manifest.csv")
    m12 = cfg.output / "FR12_dsk_manifest.csv"
    if m12.exists():
        for r in _rows(m12):
            lp = (r.get("local_path") or "").replace("data/", "", 1)
            if r.get("origin") == "DSK current" and lp.startswith("dsk_competition/current/"):    # archived vintages never change
                add(r.get("source_url"), lp, "FR12", "FR12_dsk_manifest.csv")
    return out


def dsk_refresh(cfg, fetch=download, timeout=60, apply=True, log=print):
    """Endirir, sha256 ilə müqayisə edir; dəyişən faylları (köhnəsini data/_replaced/ altına saxlayıb) əvəz edir."""
    rep = {"started": now_iso(), "checked": 0, "changed": [], "unchanged": 0, "failed": [], "affected_stages": []}
    bdir = cfg.replaced / ("%s_dsk-refresh" % stamp())
    for t in dsk_targets(cfg):
        rep["checked"] += 1
        p = cfg.data / t["path"]
        try:
            blob = fetch(t["url"], timeout=timeout)
        except Exception as e:
            rep["failed"].append({"path": t["path"], "url": t["url"], "error": az_exc(e), "detail": str(e)[:200]})
            continue
        if blob[:8] != XLS_MAGIC:
            rep["failed"].append({"path": t["path"], "url": t["url"], "error": "cavab .xls deyil (HTML səhifə?)"})
            continue
        new = hashlib.sha256(blob).hexdigest()
        old = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
        if new == old:
            rep["unchanged"] += 1
            continue
        rec = {"path": t["path"], "old_sha256": old, "new_sha256": new, "stage": t["stage"], "bytes": len(blob)}
        if apply:
            if p.exists():
                (bdir / t["path"]).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, bdir / t["path"])
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_name(".%s.tmp" % p.name)
            tmp.write_bytes(blob)
            os.replace(tmp, p)
        rep["changed"].append(rec)
    from run_manager import downstream
    rep["affected_stages"] = downstream(sorted({c["stage"] for c in rep["changed"]}))
    rep["finished"] = now_iso()
    if rep["changed"] and apply:
        write_json(bdir / "manifest.json", rep)
    apidb.event(cfg.db, "dsk", "DSK yeniləməsi: %d yoxlanıldı, %d dəyişdi, %d xəta"
                % (rep["checked"], len(rep["changed"]), len(rep["failed"])), {"changed": [c["path"] for c in rep["changed"]]})
    log("DSK yeniləməsi: %d yoxlanıldı, %d dəyişdi, %d uğursuz" % (rep["checked"], len(rep["changed"]), len(rep["failed"])))
    return rep


# ------------------------------------------------------------------ schedule
def next_at(hhmm, now=None):
    h, m = [int(x) for x in hhmm.split(":")]
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError(hhmm)
    now = now or datetime.now()
    t = now.replace(hour=h, minute=m, second=0, microsecond=0)
    return t if t > now else t + timedelta(days=1)


class Scheduler(threading.Thread):
    """--schedule HH:MM gündəlik icra; --dsk-refresh: icradan əvvəl DSK yenilənir, dəyişiklik yoxdursa icra edilmir.
    --dsk-refresh cədvəlsiz verilərsə: başlanğıcda və hər `refresh_hours` saatda bir."""

    def __init__(self, cfg, runs, schedule=None, dsk=False, refresh_hours=24.0, auto_run=True, log=print):
        super().__init__(daemon=True, name="scheduler")
        self.cfg, self.runs, self.schedule, self.dsk = cfg, runs, schedule, dsk
        self.refresh_hours, self.auto_run, self.log = refresh_hours, auto_run, log
        self.stop_ev, self.last, self.next = threading.Event(), None, None
        if schedule:
            next_at(schedule)                                           # validate early

    def job(self):
        stages = None
        if self.dsk:
            if self.runs.busy():
                self.log("cədvəl: icra gedir — DSK yeniləməsi təxirə salındı")
                return
            rep = dsk_refresh(self.cfg, log=self.log)
            self.last = {"at": now_iso(), "dsk": {k: rep[k] for k in ("checked", "unchanged", "affected_stages")} |
                         {"changed": len(rep["changed"]), "failed": len(rep["failed"])}}
            stages = rep["affected_stages"]
            if not stages:
                self.log("cədvəl: DSK fayllarında dəyişiklik yoxdur — icra edilmir")
                return
        elif self.schedule:
            stages = ["FR1"]                                             # full run
            self.last = {"at": now_iso()}
        if stages and self.auto_run:
            r = self.runs.queue(stages, actor="scheduler", trigger="schedule")
            self.log("cədvəl: icra %s" % ((r or {}).get("id") or r))

    def run(self):
        if self.dsk and not self.schedule:
            self.next = datetime.now()
        while not self.stop_ev.is_set():
            if self.schedule:
                self.next = next_at(self.schedule)
            wait = max(0.0, (self.next - datetime.now()).total_seconds())
            if self.stop_ev.wait(wait):
                break
            try:
                self.job()
            except Exception as e:
                self.log("cədvəl: xəta: %s" % e)
            if not self.schedule:
                self.next = datetime.now() + timedelta(hours=self.refresh_hours)
