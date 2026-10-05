#!/usr/bin/env python3
"""
MicroUnit — modulların avtomatik icra ardıcıllığı (orkestrator / pipeline runner).

Dəftərləri asılılıq qrafı üzrə icra edir, sonra paneli və saytı yenidən yığır:

    FR1 → FR3 → FR4 → FR5 → FR10 → FR12 → panel/build_panel.py → site/build_site.py

    python3 run_all.py                     # bütün mərhələlər
    python3 run_all.py --stage FR4         # FR4 və ondan asılı olanlar (FR10, FR12) + panel/sayt
    python3 run_all.py --stage FR4,FR5     # bir neçə başlanğıc mərhələ (asılılar birləşdirilir)
    python3 run_all.py --only FR5          # yalnız FR5 (+ panel/sayt; --skip-build ilə olmadan)
    python3 run_all.py --dry-run           # heç nə icra etmədən plan, girişlər və asılılıqlar
    python3 run_all.py --list              # asılılıq qrafı və dəftərlərdə tapılan oxumalar
    python3 run_all.py --snapshot --keep 5 # output/ surəti output/vintages/<run_id>/ altında

Asılılıqlar (hər dəftərin kodunda read_csv ilə oxunan fayllardan yoxlanılıb):
    FR3 ← FR1;  FR4 ← FR1, FR3;  FR5 ← FR1;  FR10 ← FR1, FR3, FR4;  FR12 ← FR1, FR10

Hər icra üçün ROOT/logs/<run_id>/: run.log, hər mərhələnin jurnalı (FRx.log, panel.log, site.log),
progress.json (canlı vəziyyət) və manifest.json (mərhələlər, vaxtlar, girişlərin sha256-sı, çıxışların
md5-i, xətalar və əvvəlki uğurlu icra ilə bayt-bayt müqayisə). İlk xətada dayanır: asılı mərhələlər
köhnə girişlərlə icra edilmir. Çıxış kodları: 0 uğur, 1 mərhələ xətası, 2 istifadə xətası,
3 başqa icra gedir, 130 ləğv edildi.

Yalnız Python standart kitabxanası (dəftərləri `jupyter nbconvert` icra edir).
"""
import argparse, glob, hashlib, json, os, re, shutil, signal, subprocess, sys, time, uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGES = ["FR1", "FR3", "FR4", "FR5", "FR10", "FR12"]
DEPS = {"FR1": [], "FR3": ["FR1"], "FR4": ["FR1", "FR3"], "FR5": ["FR1"],
        "FR10": ["FR1", "FR3", "FR4"], "FR12": ["FR1", "FR10"]}
BUILD = [("panel", "panel/build_panel.py"), ("site", "site/build_site.py")]
WB_DEFAULT = "Statistik data dinamika 05.06.2026 +.xlsx"
# data inputs besides the workbook (glob patterns relative to ROOT)
DATA_INPUTS = {
    "FR1": [], "FR3": [],
    "FR4": ["data/dsk/*.xls"],
    "FR5": ["data/dsk_services/*.xls"],
    "FR10": ["data/dsk_enterprise/*/*.xls", "data/firm_panel/FR10_firm_panel.csv",
             "data/firm_panel/FR10_firm_panel.xlsx", "data/firm_panel/FR10_firm_panel_SYNTHETIC.csv"],
    "FR12": ["data/dsk_enterprise/*/*.xls", "data/dsk_competition/*/*.xls",
             "data/business_register/FR12_business_register.csv",
             "data/business_register/FR12_business_register.xlsx",
             "data/business_register/FR12_business_register_SYNTHETIC.csv"],
}
EXTRA_OUTPUTS = {"FR10": ["data/firm_panel/FR10_firm_panel_*"],
                 "FR12": ["data/business_register/FR12_business_register_*"]}
BUILD_OUTPUTS = {"panel": ["panel/data/*.js", "panel/coverage_report.csv", "index.html"],
                 "site": ["site/*.html", "site/fr/*.html"]}
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
RUN_ID_RE = re.compile(r"^r\d{8}-\d{6}-[0-9a-f]{4}$")


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def new_run_id():
    return datetime.now().strftime("r%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]


def is_junk(path):
    """Google Drive «Icon\\r», gizli və müvəqqəti Office faylları nəzərə alınmır."""
    n = os.path.basename(str(path))
    return n.startswith((".", "~$")) or n.startswith("Icon") and len(n) <= 5


_HASH_CACHE = {}


def file_hash(path, algo):
    st = os.stat(path)
    key = (str(path), algo, st.st_size, st.st_mtime_ns)
    if key not in _HASH_CACHE:
        h = hashlib.new(algo)
        with open(path, "rb") as f:
            for blk in iter(lambda: f.read(1 << 20), b""):
                h.update(blk)
        _HASH_CACHE[key] = h.hexdigest()
    return _HASH_CACHE[key]


def expand(root, patterns):
    out = set()
    for pat in patterns:
        for p in glob.glob(str(Path(root) / pat)):
            if os.path.isfile(p) and not is_junk(p):
                out.add(os.path.relpath(p, root).replace(os.sep, "/"))
    return sorted(out)


def nb_code(nb_path):
    """Dəftərin yalnız kod hücrələrinin mətni."""
    nb = json.loads(Path(nb_path).read_text(encoding="utf-8"))
    parts = []
    for c in nb.get("cells", []):
        if c.get("cell_type") == "code":
            s = c.get("source", "")
            parts.append("".join(s) if isinstance(s, list) else s)
    return "\n".join(parts)


def detect(root, stage):
    """Dəftərin kodundan oxunan iş kitabı və digər modulların çıxış faylları (read_csv girişləri)."""
    p = Path(root) / f"{stage}.ipynb"
    if not p.exists():
        return {"notebook": False, "workbooks": [], "upstream": {}, "read_csv": 0, "code_sha256": None}
    src = nb_code(p)
    wbs = sorted(set(re.findall(r"Statistik data dinamika[^'\"\n]*?\.xlsx", src)))
    ups = {}
    for fn, num in re.findall(r"['\"/](FR(\d+)_[A-Za-z0-9_]+\.csv)['\"]", src):
        mod = "FR" + num
        if mod != stage:
            ups.setdefault(mod, set()).add(fn)
    return {"notebook": True, "workbooks": wbs, "upstream": {k: sorted(v) for k, v in sorted(ups.items())},
            "read_csv": len(re.findall(r"read_csv\(", src)),
            "code_sha256": hashlib.sha256(src.encode("utf-8")).hexdigest()}


def dep_check(root):
    """Elan olunmuş asılılıqları dəftərlərdə tapılan oxumalarla müqayisə edir."""
    rep = {}
    for s in STAGES:
        d = detect(root, s)
        found = sorted(d["upstream"], key=lambda m: STAGES.index(m) if m in STAGES else 99)
        rep[s] = {"declared": DEPS[s], "detected": found, "files": d["upstream"],
                  "ok": set(found) == set(DEPS[s]),
                  "undeclared": [m for m in found if m not in DEPS[s]],
                  "unused": [m for m in DEPS[s] if m not in found],
                  "order_ok": all(m in STAGES and STAGES.index(m) < STAGES.index(s) for m in found)}
    return rep


def downstream(stages):
    """Verilən mərhələlər və onlardan (birbaşa və ya dolayı) asılı olanlar, icra sırası ilə."""
    sel, changed = set(stages), True
    while changed:
        changed = False
        for s in STAGES:
            if s not in sel and any(d in sel for d in DEPS[s]):
                sel.add(s)
                changed = True
    return [s for s in STAGES if s in sel]


def parse_stage_list(value):
    out = []
    for x in re.split(r"[,\s;]+", value or ""):
        if not x:
            continue
        k = x.strip().upper()
        if k not in STAGES:
            raise ValueError("naməlum mərhələ «%s» — mümkün olanlar: %s" % (x, ", ".join(STAGES)))
        if k not in out:
            out.append(k)
    return out


def plan(stage=None, only=None, skip_build=False):
    if stage and only:
        raise ValueError("--stage və --only birlikdə verilə bilməz")
    if only:
        st = [s for s in STAGES if s in parse_stage_list(only)]
    elif stage:
        st = downstream(parse_stage_list(stage))
    else:
        st = list(STAGES)
    return st, ([] if skip_build else [b for b, _ in BUILD])


def write_json(path, obj):
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


# ------------------------------------------------------------------ lock (one run at a time)
class RunLock:
    """logs/.run_all.lock üzərində eksklüziv kilid (POSIX: fcntl, Windows: msvcrt)."""

    def __init__(self, logs):
        self.path = Path(logs) / ".run_all.lock"
        self.fh = None

    def acquire(self, info):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fh = open(self.path, "a+")
        try:
            if os.name == "nt":
                import msvcrt
                self.fh.seek(0)
                msvcrt.locking(self.fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.fh.close()
            self.fh = None
            return False
        write_json(self.path.parent / ".run_all.pid", info)
        return True

    def release(self):
        try:
            (self.path.parent / ".run_all.pid").unlink()
        except OSError:
            pass
        if self.fh:
            try:
                if os.name == "nt":
                    import msvcrt
                    self.fh.seek(0)
                    msvcrt.locking(self.fh.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
            finally:
                self.fh.close()
                self.fh = None


def nbconvert_cmd(nb, timeout, kernel=None):
    """`jupyter nbconvert --to notebook --execute --inplace` (venv-dəki jupyter, yoxdursa python -m nbconvert)."""
    jup = Path(sys.executable).with_name("jupyter.exe" if os.name == "nt" else "jupyter")
    base = [str(jup)] if jup.exists() else ([shutil.which("jupyter")] if shutil.which("jupyter") else None)
    base = (base + ["nbconvert"]) if base else [sys.executable, "-m", "nbconvert"]
    cmd = base + ["--to", "notebook", "--execute", "--inplace", "--ExecutePreprocessor.timeout=%d" % timeout]
    if kernel:
        cmd.append("--ExecutePreprocessor.kernel_name=%s" % kernel)
    return cmd + [str(nb)]


def error_tail(log_path, n=40):
    try:
        txt = ANSI.sub("", Path(log_path).read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return None, None
    lines = [l for l in txt.splitlines() if l.strip()]
    summary = next((l.strip() for l in reversed(lines)
                    if re.match(r"^\s*[A-Za-z_.]*(Error|Exception|Interrupt)\b", l)), lines[-1].strip() if lines else None)
    return summary, "\n".join(lines[-n:])


class Runner:
    def __init__(self, a):
        self.a = a
        self.root = Path(a.root).resolve()
        self.run_id = a.run_id or new_run_id()
        if not RUN_ID_RE.match(self.run_id):
            raise ValueError("run_id formatı yanlışdır: %s" % self.run_id)
        self.logs = self.root / "logs"
        self.dir = self.logs / self.run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.cancel_file = self.dir / "CANCEL"
        self.cancelled = False
        self.stages, self.builds = plan(a.stage, a.only, a.skip_build)
        self.m = {"run_id": self.run_id, "status": "running", "dry_run": bool(a.dry_run), "trigger": a.trigger,
                  "root": str(self.root), "argv": sys.argv[1:], "python": sys.executable,
                  "python_version": sys.version.split()[0], "kernel": a.kernel or "(dəftərin öz kernel-i)",
                  "timeout_s": a.timeout, "started": now_iso(), "finished": None, "seconds": None,
                  "plan": self.stages + self.builds, "steps": [], "dependency_check": None,
                  "snapshot": None, "reproducibility": None, "error": None}

    # ---- logging / progress
    def log(self, msg):
        line = "%s  %s" % (datetime.now().strftime("%H:%M:%S"), msg)
        print(line, flush=True)
        with open(self.dir / "run.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def progress(self, current=None):
        write_json(self.dir / "progress.json", {
            "run_id": self.run_id, "status": self.m["status"], "current": current, "dry_run": self.m["dry_run"],
            "updated": now_iso(), "started": self.m["started"],
            "steps": [{k: s.get(k) for k in ("name", "kind", "status", "started", "finished", "seconds", "error")}
                      for s in self.m["steps"]]})

    def on_signal(self, signum, frame):
        self.cancelled = True

    # ---- hashing
    def stage_inputs(self, s):
        d = detect(self.root, s)
        wbs = d["workbooks"] or [WB_DEFAULT]
        files = ["data/" + w for w in wbs] + expand(self.root, DATA_INPUTS.get(s, []))
        files += ["output/" + f for fs in d["upstream"].values() for f in fs]
        out = {}
        for rel in sorted(set(files)):
            p = self.root / rel
            out[rel] = file_hash(p, "sha256") if p.is_file() else None      # None = missing
        out["%s.ipynb#code" % s] = d["code_sha256"]
        return out, d

    def stage_outputs(self, name):
        pats = (["output/%s_*" % name, "output/engine/%s_*" % name] + EXTRA_OUTPUTS.get(name, [])
                if name in STAGES else BUILD_OUTPUTS.get(name, []))
        return {rel: file_hash(self.root / rel, "md5") for rel in expand(self.root, pats)}

    # ---- one subprocess with timeout and cancellation
    def _kill(self, p):
        try:
            p.terminate()
            p.wait(15)
        except Exception:
            try:
                p.kill()
                p.wait(5)
            except Exception:
                pass

    def run_cmd(self, cmd, log_path):
        t0 = time.time()
        with open(log_path, "ab") as lf:
            lf.write(("$ %s\n" % " ".join(cmd)).encode("utf-8"))
            lf.flush()
            p = subprocess.Popen(cmd, cwd=str(self.root), stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
            status = None
            while True:
                rc = p.poll()
                if rc is not None:
                    status = "ok" if rc == 0 else "failed"
                    break
                if self.cancelled or self.cancel_file.exists():
                    self.cancelled = True
                    self._kill(p)
                    status = "cancelled"
                    break
                if time.time() - t0 > self.a.timeout:
                    self._kill(p)
                    status = "timeout"
                    break
                time.sleep(0.5)
        return status, p.returncode, round(time.time() - t0, 1)

    # ---- the steps
    def step(self, name, kind):
        rec = {"name": name, "kind": kind, "status": "pending", "started": None, "finished": None, "seconds": None,
               "returncode": None, "log": "logs/%s/%s.log" % (self.run_id, name), "command": None,
               "inputs": {}, "outputs": {}, "error": None, "error_tail": None}
        if kind == "notebook":
            rec["deps_declared"] = DEPS[name]
        self.m["steps"].append(rec)
        return rec

    def execute(self, rec):
        name = rec["name"]
        if rec["kind"] == "notebook":
            nb = self.root / ("%s.ipynb" % name)
            rec["inputs"], d = self.stage_inputs(name)
            rec["deps_detected"] = sorted(d["upstream"], key=lambda m: STAGES.index(m) if m in STAGES else 99)
            rec["command"] = nbconvert_cmd(nb.name, self.a.timeout, self.a.kernel)
            missing = [k for k, v in rec["inputs"].items() if v is None]
            if not nb.exists():
                rec["status"], rec["error"] = "failed", "dəftər tapılmadı: %s" % nb.name
                return False
        else:
            script = dict(BUILD)[name]
            rec["command"] = [sys.executable, script]
            missing = [] if (self.root / script).exists() else [script]
        rec["started"] = now_iso()
        self.progress(name)
        if self.a.dry_run:
            rec["status"] = "planned"
            if missing:
                rec["error"] = "çatışmayan girişlər: " + ", ".join(missing)
            if self.a.sleep:
                t0 = time.time()
                while time.time() - t0 < self.a.sleep and not (self.cancelled or self.cancel_file.exists()):
                    time.sleep(0.1)
                if self.cancelled or self.cancel_file.exists():
                    self.cancelled = True
                    rec["status"] = "cancelled"
            rec["finished"] = now_iso()
            self.log("[%s] plan: %s%s" % (name, " ".join(rec["command"][-1:]), ("  (%s)" % rec["error"]) if rec["error"] else ""))
            return rec["status"] != "cancelled"
        self.log("[%s] başladı" % name)
        status, rc, secs = self.run_cmd(rec["command"], self.root / rec["log"])
        rec.update(status=status, returncode=rc, seconds=secs, finished=now_iso())
        rec["outputs"] = self.stage_outputs(name)
        if status != "ok":
            summ, tail = error_tail(self.root / rec["log"])
            rec["error"] = {"timeout": "vaxt limiti (%d s) aşıldı" % self.a.timeout,
                            "cancelled": "istifadəçi tərəfindən ləğv edildi"}.get(status, summ or "naməlum xəta")
            rec["error_tail"] = tail
            self.log("[%s] %s: %s (%.0f s) — jurnal: %s" % (name, status.upper(), rec["error"], secs, rec["log"]))
            return False
        self.log("[%s] uğurla bitdi (%.0f s, %d çıxış faylı)" % (name, secs, len(rec["outputs"])))
        return True

    # ---- after the run
    def previous_manifest(self):
        hist = self.logs / "history.jsonl"
        if not hist.exists():
            return None
        for line in reversed(hist.read_text(encoding="utf-8").splitlines()):
            try:
                h = json.loads(line)
            except ValueError:
                continue
            if h.get("run_id") != self.run_id and h.get("status") == "ok" and not h.get("dry_run"):
                mp = self.logs / h["run_id"] / "manifest.json"
                if mp.exists():
                    return json.loads(mp.read_text(encoding="utf-8"))
        return None

    def reproducibility(self):
        prev = self.previous_manifest()
        if not prev:
            return {"previous_run": None, "identical": None, "note": "müqayisə üçün əvvəlki uğurlu icra yoxdur"}
        po = {s["name"]: s.get("outputs") or {} for s in prev.get("steps", []) if s.get("status") == "ok"}
        co = {s["name"]: s.get("outputs") or {} for s in self.m["steps"] if s.get("status") == "ok"}
        common = sorted(set(po) & set(co), key=lambda n: (STAGES + [b for b, _ in BUILD]).index(n))
        changed, added, removed = [], [], []
        for n in common:
            a, b = po[n], co[n]
            changed += [f for f in sorted(set(a) & set(b)) if a[f] != b[f]]
            added += sorted(set(b) - set(a))
            removed += sorted(set(a) - set(b))
        return {"previous_run": prev["run_id"], "compared_steps": common,
                "files_compared": sum(len(set(po[n]) & set(co[n])) for n in common),
                "identical": not (changed or added or removed) if common else None,
                "changed": changed[:500], "added": added[:200], "removed": removed[:200]}

    def snapshot(self):
        src = self.root / "output"
        dst = src / "vintages" / self.run_id
        dst.mkdir(parents=True, exist_ok=True)
        n = 0
        for p in sorted(src.iterdir()):
            if p.is_file() and not is_junk(p):
                shutil.copy2(p, dst / p.name)
                n += 1
        if (src / "engine").is_dir():
            shutil.copytree(src / "engine", dst / "engine", dirs_exist_ok=True)
        keep = max(1, int(self.a.keep))
        olds = sorted(d for d in (src / "vintages").iterdir() if d.is_dir() and RUN_ID_RE.match(d.name))
        pruned = [d.name for d in olds[:-keep]]
        for d in olds[:-keep]:
            shutil.rmtree(d, ignore_errors=True)
        return {"path": "output/vintages/%s" % self.run_id, "files": n, "keep": keep, "pruned": pruned}

    def finish(self, status, t0):
        self.m["status"] = status
        self.m["finished"] = now_iso()
        self.m["seconds"] = round(time.time() - t0, 1)
        if not self.m["dry_run"]:
            self.m["reproducibility"] = self.reproducibility()
            if status == "ok" and self.a.snapshot:
                self.m["snapshot"] = self.snapshot()
        write_json(self.dir / "manifest.json", self.m)
        write_json(self.logs / "latest.json", {k: v for k, v in self.m.items() if k != "steps"} |
                   {"steps": [{k: s.get(k) for k in ("name", "status", "seconds", "error")} for s in self.m["steps"]]})
        with open(self.logs / "history.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"run_id": self.run_id, "status": status, "dry_run": self.m["dry_run"],
                                "started": self.m["started"], "finished": self.m["finished"], "plan": self.m["plan"],
                                "trigger": self.m["trigger"],
                                "identical_to_previous": (self.m["reproducibility"] or {}).get("identical")},
                               ensure_ascii=False) + "\n")
        self.progress(None)

    def run(self):
        t0 = time.time()
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self.on_signal)
        self.m["dependency_check"] = dep_check(self.root)
        bad = {s: r for s, r in self.m["dependency_check"].items() if not r["ok"]}
        for s, r in bad.items():
            self.log("XƏBƏRDARLIQ: %s asılılıqları elan olunandan fərqlidir — elan: %s, dəftərdə: %s"
                     % (s, ",".join(r["declared"]) or "-", ",".join(r["detected"]) or "-"))
        self.log("icra %s%s: %s" % (self.run_id, " (DRY-RUN)" if self.a.dry_run else "", " → ".join(self.m["plan"])))
        recs = [self.step(s, "notebook") for s in self.stages] + [self.step(b, "build") for b in self.builds]
        self.progress(None)
        status = "dry-run" if self.a.dry_run else "ok"
        for i, rec in enumerate(recs):
            if self.cancelled or self.cancel_file.exists():
                self.cancelled = True
            ok = (not self.cancelled) and self.execute(rec)
            if not ok:
                if rec["status"] == "pending":
                    rec["status"] = "cancelled"
                status = "cancelled" if (self.cancelled or rec["status"] == "cancelled") else "failed"
                self.m["error"] = "%s: %s" % (rec["name"], rec["error"])
                for r in recs[i + 1:]:
                    r["status"] = "skipped"
                    r["error"] = "əvvəlki mərhələ uğursuz oldu — köhnə girişlərlə icra edilmədi"
                break
            self.progress(None)
        self.finish(status, t0)
        self.log("icra %s bitdi: %s (%.0f s)%s" % (self.run_id, status, self.m["seconds"],
                 "" if self.m["dry_run"] else "; əvvəlki icra ilə bayt-bayt eyni: %s"
                 % (self.m["reproducibility"] or {}).get("identical")))
        return {"ok": 0, "dry-run": 0, "failed": 1, "cancelled": 130}[status]


def print_graph(root):
    print("Asılılıq qrafı (elan) və dəftərlərdə tapılan oxumalar (read_csv girişləri):")
    for s, r in dep_check(root).items():
        mark = "OK " if r["ok"] else "FƏRQ"
        print("  %-5s ← %-14s  dəftərdə: %-14s %s" % (s, ",".join(r["declared"]) or "-", ",".join(r["detected"]) or "-", mark))
        for m, fs in r["files"].items():
            print("          %s: %s" % (m, ", ".join(fs)))
    print("Sonra: " + " → ".join(b for b, _ in BUILD))


def main(argv=None):
    ap = argparse.ArgumentParser(description="MicroUnit modullarının avtomatik icrası (FR1 → FR3 → FR4 → FR5 → FR10 → FR12 → panel → sayt)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--stage", help="bu mərhələ(lər) və ondan asılı olanlar, məs. FR4 və ya FR4,FR5")
    g.add_argument("--only", help="yalnız bu mərhələ(lər), asılılar icra edilmir")
    ap.add_argument("--skip-build", action="store_true", help="panel/build_panel.py və site/build_site.py icra edilməsin")
    ap.add_argument("--dry-run", action="store_true", help="heç nə icra etmədən planı və girişləri göstər")
    ap.add_argument("--list", action="store_true", help="asılılıq qrafını və dəftərlərdəki oxumaları göstər")
    ap.add_argument("--timeout", type=int, default=int(os.environ.get("MICRO_STAGE_TIMEOUT", "3600")),
                    help="bir mərhələ üçün vaxt limiti, saniyə (standart 3600)")
    ap.add_argument("--kernel", default=os.environ.get("MICRO_KERNEL") or "miis-model",
                    help="Jupyter kernel adı (standart: layihə mühiti 'miis-model'; dəftərin öz kernel-i üçün --kernel '')")
    ap.add_argument("--snapshot", action="store_true", default=os.environ.get("MICRO_SNAPSHOT") == "1",
                    help="uğurlu icradan sonra output/ surətini output/vintages/<run_id>/ altında saxla")
    ap.add_argument("--keep", type=int, default=int(os.environ.get("MICRO_KEEP_VINTAGES", "5")),
                    help="saxlanılan surətlərin sayı (standart 5)")
    ap.add_argument("--run-id", help=argparse.SUPPRESS)
    ap.add_argument("--trigger", default="cli", help=argparse.SUPPRESS)
    ap.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    ap.add_argument("--sleep", type=float, default=0.0, help=argparse.SUPPRESS)   # tests: simulate a slow dry-run step
    a = ap.parse_args(argv)
    if a.list:
        print_graph(Path(a.root))
        return 0
    try:
        r = Runner(a)
    except ValueError as e:
        print("XƏTA: %s" % e, file=sys.stderr)
        return 2
    lock = None
    if not a.dry_run:
        lock = RunLock(r.logs)
        if not lock.acquire({"pid": os.getpid(), "run_id": r.run_id, "started": now_iso()}):
            print("XƏTA: başqa icra hazırda gedir (logs/.run_all.lock). Bitməsini gözləyin.", file=sys.stderr)
            shutil.rmtree(r.dir, ignore_errors=True)
            return 3
    try:
        return r.run()
    finally:
        if lock:
            lock.release()


if __name__ == "__main__":
    sys.exit(main())
