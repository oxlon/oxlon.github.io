#!/usr/bin/env python3
"""MİİS CI — state that must survive between GitHub Actions runs (run from the repository root).

Two layers (see DEPLOY_az.md):
  1. actions/cache (full, fast): RiskUnit/data/vintages + the files below + PolicyUnit/work/fr4_cache.
  2. branch `miis-state` (durable, small): ONLY the DURABLE set below, one squashed commit, force-pushed
     each run, so the branch never grows history. Used when the cache was evicted (7 days unused / 10 GB).

  python3 .github/miis/ci_state.py restore         # overlay miis-state when it is newer than the cache
  python3 .github/miis/ci_state.py save            # stamp + force-push the durable set to miis-state
  python3 .github/miis/ci_state.py list            # print the durable set and its size
  python3 .github/miis/ci_state.py prune-artifact  # drop scratch + old raw vintages from the site tree
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

BRANCH = os.environ.get("MIIS_STATE_BRANCH", "miis-state")
CI = Path(os.environ.get("MIIS_CI_DIR", "_ci"))
STAMP = Path("RiskUnit/output/_ci_state.json")
VINT = Path("RiskUnit/data/vintages")
FILES = ["RiskUnit/output/FR2_score_history.csv", "RiskUnit/output/FR3_status_history.csv",
         "RiskUnit/output/NFR2_update_log.csv", "MicroUnit/logs/history.jsonl", str(STAMP), str(VINT / "manifest.csv")]
DIRS = ["RiskUnit/output/forecast_archive", "RiskUnit/output/monitor_history"]
DATED = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SCRATCH_DIRS = {"work", "logs", "__pycache__", ".ipynb_checkpoints", ".pytest_cache"}
SCRATCH_SUFFIX = (".db", ".db-shm", ".db-wal", ".db-journal", ".sqlite", ".sqlite3", ".print.html", ".lock")


def git(*a, check=True, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *a], check=check, text=True, capture_output=True, **kw)


def durable() -> list[Path]:
    """Histories + manifest + the vintage files the manifest's last good rows point to + per source dir: its
    non-dated files (merged histories, raw zips, files/, posts/) and its latest dated raw-cache dir."""
    out = [Path(f) for f in FILES if Path(f).is_file()]
    for d in DIRS:
        out += [p for p in Path(d).rglob("*") if p.is_file()]
    man = VINT / "manifest.csv"
    if man.is_file():
        import csv
        last = {}
        with open(man, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("status") == "ok":
                    last[r["feed"]] = r["path"]
        out += [VINT / p for p in last.values() if (VINT / p).is_file()]
    for src in (p for p in VINT.iterdir() if p.is_dir() and not DATED.match(p.name)) if VINT.is_dir() else []:
        dated = sorted(p for p in src.iterdir() if p.is_dir() and DATED.match(p.name))
        for p in src.iterdir():
            if p.is_file():
                out.append(p)
            elif p.is_dir() and not DATED.match(p.name):
                out += [q for q in p.rglob("*") if q.is_file()]
        if dated:
            out += [q for q in dated[-1].rglob("*") if q.is_file()]
    return sorted(set(out))


def _stamp(p: Path) -> str:
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("utc", "")
    except Exception:                                              # noqa: BLE001
        return ""


def restore() -> int:
    d = CI / "state_branch"
    shutil.rmtree(d, ignore_errors=True)
    if git("fetch", "--depth", "1", "origin", f"+refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}", check=False).returncode:
        print(f"'{BRANCH}' budağı yoxdur — ilk icra; keş/repozitoriya nüsxəsi istifadə olunur")
        return 0
    d.mkdir(parents=True)
    tar = subprocess.run(["git", "archive", f"origin/{BRANCH}"], check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(d)], input=tar, check=True)
    b, c = _stamp(d / STAMP), _stamp(STAMP)
    if c and c >= b:
        print(f"keş daha yenidir ({c} ≥ {b}) — {BRANCH} tətbiq edilmir")
        return 0
    n = 0
    for p in d.rglob("*"):
        if p.is_file():
            t = p.relative_to(d)
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, t)
            n += 1
    print(f"{BRANCH} ({b}) bərpa olundu: {n} fayl (keş: {c or 'yoxdur'})")
    return 0


def save() -> int:
    STAMP.parent.mkdir(parents=True, exist_ok=True)
    STAMP.write_text(json.dumps({"utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                 "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
                                 "sha": os.environ.get("GITHUB_SHA", "")}), encoding="utf-8")
    files = durable()
    out = CI / "state_out"
    shutil.rmtree(out, ignore_errors=True)
    for p in files:
        (out / p).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, out / p)
    size = sum(p.stat().st_size for p in files) / 2**20
    print(f"davamlı vəziyyət: {len(files)} fayl, {size:.1f} MB")
    if os.environ.get("MIIS_STATE_PUSH", "1") != "1":
        print("MIIS_STATE_PUSH≠1 — budağa yazılmır (yerli məşq)")
        return 0
    env = dict(os.environ, GIT_INDEX_FILE=str((CI / "state.index").resolve()))
    git("--work-tree", str(out), "add", "-A", ".", env=env)
    tree = git("write-tree", env=env).stdout.strip()
    who = ["-c", "user.name=miis-bot", "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com"]
    commit = git(*who, "commit-tree", tree, "-m", f"MİİS vəziyyəti {_stamp(STAMP)} (run {os.environ.get('GITHUB_RUN_ID', '')})").stdout.strip()
    r = git("push", "--force", "origin", f"{commit}:refs/heads/{BRANCH}", check=False)
    print(r.stdout + r.stderr)
    return r.returncode


def prune_artifact() -> int:
    """Remove what must not be published: scratch dirs, DBs, symlinks (Pages rejects them), _ci/, and raw
    vintages outside the durable set (keeps the site bounded; the full archive lives in the cache)."""
    keep = {str(p) for p in durable()}
    n = 0
    for p in list(VINT.rglob("*")) if VINT.is_dir() else []:
        if p.is_file() and str(p) not in keep:
            p.unlink()
            n += 1
    for root in ("MicroUnit", "RiskUnit", "PolicyUnit", "Macro_OxLon", "Macro_MinistryUnit"):   # unit folders only
        for dp, dn, fn in os.walk(root, topdown=True):
            for x in list(dn):
                q = Path(dp) / x
                if q.is_symlink() or x in SCRATCH_DIRS or x.startswith("chrome-profile"):
                    (q.unlink() if q.is_symlink() else shutil.rmtree(q, ignore_errors=True))
                    dn.remove(x)
                    n += 1
            for x in fn:
                q = Path(dp) / x
                if q.is_symlink() or x.endswith(SCRATCH_SUFFIX):
                    q.unlink()
                    n += 1
    shutil.rmtree(CI, ignore_errors=True)
    print(f"artefakt təmizləndi: {n} element silindi")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "list":
        fs = durable()
        print("\n".join(map(str, fs)))
        print(f"{len(fs)} fayl, {sum(p.stat().st_size for p in fs) / 2**20:.1f} MB")
        sys.exit(0)
    sys.exit({"restore": restore, "save": save, "prune-artifact": prune_artifact}.get(cmd, lambda: sys.exit(__doc__))())
