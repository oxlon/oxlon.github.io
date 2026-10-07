"""Pipeline stage: rebuild the Siyasət paneli data bundles (panel/build_panel.py, all build checks) after a run."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _build_panel(args, log):
    script = ROOT / "panel" / "build_panel.py"
    if not script.exists():
        log("panel yoxdur — mərhələ buraxıldı")
        return
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=900, cwd=str(ROOT))
    if r.returncode:
        log((r.stdout + r.stderr)[-2000:])
        raise RuntimeError(f"panel/build_panel.py çıxış kodu {r.returncode}")
    log("Siyasət paneli yenidən quruldu")


def register(R):
    R.add("panel.build", _build_panel, owner="panel", after=["core.kpi"], optional=True,
          description_az="Siyasət paneli: məlumat paketlərinin yenidən qurulması (bütün yoxlamalarla)")
