#!/usr/bin/env python3
"""MİİS CI — stage runner and job summary (run from the repository root).

  python3 .github/miis/ci_summary.py run micro -- bash .github/miis/pipeline.sh micro
      runs the command, streams its output to the log and to _ci/micro.log, records rc/duration in
      _ci/status.json; always exits 0 so the next stage runs on the last good outputs (fail-soft).
  python3 .github/miis/ci_summary.py report
      writes the stage table (+ RiskUnit/PolicyUnit/MicroUnit internal statuses) to $GITHUB_STEP_SUMMARY
      (or stdout) and exits 1 when a stage failed -> the job is red and GitHub notifies by e-mail.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

CI = Path(os.environ.get("MIIS_CI_DIR", "_ci"))
STATUS = CI / "status.json"
LABEL = {"micro": "MicroUnit run_all.py", "risk": "RiskUnit run_all.py", "policy": "PolicyUnit run_all.py",
         "panels": "Panellər/saytlar (yenidən qurulma)", "state": "Vəziyyətin saxlanması"}


def _load() -> dict:
    try:
        return json.loads(STATUS.read_text(encoding="utf-8"))
    except Exception:                                              # noqa: BLE001
        return {}


def run(name: str, cmd: list[str]) -> int:
    CI.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with open(CI / f"{name}.log", "w", encoding="utf-8") as log:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
        for line in p.stdout:
            sys.stdout.write(line)
            log.write(line)
        rc = p.wait()
    st = _load()
    st[name] = {"rc": rc, "seconds": round(time.time() - t0, 1), "cmd": " ".join(cmd)}
    STATUS.write_text(json.dumps(st, indent=1), encoding="utf-8")
    print(f"::{'notice' if rc == 0 else 'error'}::{LABEL.get(name, name)}: rc={rc} ({st[name]['seconds']} s)")
    return 0


def _risk_detail() -> tuple[str, bool]:
    try:
        m = json.loads(Path("RiskUnit/output/_run_summary_v2.json").read_text(encoding="utf-8"))
    except Exception:                                              # noqa: BLE001
        return "xülasə tapılmadı", True
    rows = m.get("merheleler", [])
    bad = [r["stage"] for r in rows if str(r.get("seviyye", r.get("status", ""))).startswith("xəta")]
    warn = [r["stage"] for r in rows if str(r.get("seviyye", "")).startswith("xəbərdarlıq")]
    txt = (f"{len(rows)} mərhələ; xəta: {', '.join(bad) or '0'}; xəbərdarlıq: {', '.join(warn) or '0'}; "
           f"baza {m.get('baseline_id')}; şəbəkə: {m.get('sebeke', '?')}")
    return txt, bool(bad)


def _policy_detail() -> str:
    p = Path("PolicyUnit/logs/run_all.log")
    if not p.exists():
        return "jurnal yoxdur"
    t = p.read_text(encoding="utf-8", errors="replace")
    t = t[t.rfind("=== run_all"):]
    errs = re.findall(r"^\[([^\]]+)\] (?:XƏTA|KONFİQURASİYA)", t, re.M)
    ok = len(re.findall(r"^\[[^\]]+\] OK", t, re.M))
    return f"{ok} mərhələ OK; xəta: {', '.join(errs) or '0'}"


def _micro_detail() -> str:
    try:
        m = json.loads(Path("MicroUnit/logs/latest.json").read_text(encoding="utf-8"))
        return f"status {m.get('status')}; {m.get('seconds')} s; plan {' → '.join(m.get('plan', []))}"
    except Exception:                                              # noqa: BLE001
        return "manifest yoxdur"


def report() -> int:
    st = _load()
    detail = {"micro": _micro_detail(), "policy": _policy_detail()}
    risk_txt, risk_bad = _risk_detail()
    detail["risk"] = risk_txt
    lines = ["## MİİS gündəlik yeniləmə", "", "| Mərhələ | Nəticə | Müddət, s | Təfərrüat |", "|---|---|---|---|"]
    failed = []
    for k in ("micro", "risk", "policy", "panels", "state"):
        if k not in st:
            lines.append(f"| {LABEL[k]} | — icra olunmayıb | | |")
            continue
        bad = st[k]["rc"] != 0 or (k == "risk" and risk_bad)
        failed += [k] if bad else []
        lines.append(f"| {LABEL[k]} | {'XƏTA' if bad else 'OK'} (rc={st[k]['rc']}) | {st[k]['seconds']} | "
                     f"{detail.get(k, '')} |")
    total = sum(v["seconds"] for v in st.values())
    lines += ["", f"Cəmi: {total / 60:.1f} dəq. OxLon mühərriki: "
              f"{'söndürülüb (POLICY_OXLON_DISABLED=1)' if os.environ.get('POLICY_OXLON_DISABLED') == '1' else 'aktiv'}.",
              "Uğursuz mərhələdə sayt əvvəlki (repozitoriyadakı) nəticələrlə dərc olunur." if failed else ""]
    out = "\n".join(lines) + "\n"
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(out)
    print(out)
    return 1 if failed else 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["run"] and "--" in a:
        sys.exit(run(a[1], a[a.index("--") + 1:]))
    if a[:1] == ["report"]:
        sys.exit(report())
    sys.exit(__doc__)
