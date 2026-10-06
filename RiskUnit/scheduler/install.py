"""Generate (and optionally install) the NFR2 schedules with paths DERIVED from this folder — never hard-coded.

    python3 scheduler/install.py                 # write the macOS plists, crontab line and Windows Task XMLs
    python3 scheduler/install.py --install       # macOS: also copy the plists to ~/Library/LaunchAgents and load them
    python3 scheduler/install.py --uninstall     # macOS: unload and remove them

Schedule (Asia/Baku local time of the server): 06:30 --full (feeds + monitor + full scoring pipeline and reports),
13:30 and 18:30 --daily (feeds + forecast-impact monitor; CBAR publishes the next day's official rates in the
afternoon, DSK releases at 10:00–17:00). The wrappers run_update.sh / run_update.bat find the RiskUnit folder from
their own location, so moving the folder only requires re-running this script (launchd/cron need absolute paths).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
RU = HERE.parent
JOBS = {"full": ("az.miis.risk.update", "--full", [(6, 30)]),
        "daily": ("az.miis.risk.daily", "--daily", [(13, 30), (18, 30)])}


def plist(label: str, flag: str, times) -> str:
    cal = "".join(f"<dict><key>Hour</key><integer>{h}</integer><key>Minute</key><integer>{m}</integer></dict>"
                  for h, m in times)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<!-- MİİS §15.5.3 NFR2 — scheduler/install.py tərəfindən yaradılıb ({RU}). Əl ilə redaktə etməyin:
     qovluq köçürüldükdə `python3 scheduler/install.py --install` yenidən işlədin. -->
<plist version="1.0"><dict>
  <key>Label</key><string>{label}</string>
  <key>ProgramArguments</key><array>
    <string>/bin/sh</string><string>{escape(str(HERE / 'run_update.sh'))}</string><string>{flag}</string>
  </array>
  <key>WorkingDirectory</key><string>{escape(str(RU))}</string>
  <key>EnvironmentVariables</key><dict><key>MIIS_PYTHON</key><string>{escape(sys.executable)}</string></dict>
  <key>StartCalendarInterval</key><array>{cal}</array>
  <key>StandardOutPath</key><string>{escape(str(RU / 'output' / 'NFR2_launchd.log'))}</string>
  <key>StandardErrorPath</key><string>{escape(str(RU / 'output' / 'NFR2_launchd.log'))}</string>
  <key>RunAtLoad</key><false/>
</dict></plist>
"""


def cron() -> str:
    sh = str(HERE / "run_update.sh").replace(" ", "\\ ")
    lines = ["# MİİS §15.5.3 NFR2 — scheduler/install.py tərəfindən yaradılıb. `crontab -e` ilə əlavə edin.",
             f"# Qovluq: {RU}", f"MIIS_PYTHON={sys.executable}"]
    for _k, (_l, flag, times) in JOBS.items():
        for h, m in times:
            lines.append(f"{m} {h} * * *  /bin/sh {sh} {flag}")
    return "\n".join(lines) + "\n"


def task_xml(name: str, flag: str, times) -> str:
    trig = "".join(f"""
    <CalendarTrigger><StartBoundary>2026-10-07T{h:02d}:{m:02d}:00</StartBoundary><Enabled>true</Enabled>
      <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay></CalendarTrigger>""" for h, m in times)
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<!-- MİİS §15.5.3 NFR2. İdxal: schtasks /Create /TN "{name}" /XML "{name}.xml"
     %MIIS_RISK_DIR% — RiskUnit qovluğu (setx MIIS_RISK_DIR "D:\\...\\RiskUnit"); və ya bu faylı Windows-da
     `python scheduler\\install.py` ilə yenidən yaradın — onda yol avtomatik yazılır. -->
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>MİİS §15.5.3 risk bölməsi: update.py {flag}</Description></RegistrationInfo>
  <Triggers>{trig}
  </Triggers>
  <Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><StartWhenAvailable>true</StartWhenAvailable>
    <ExecutionTimeLimit>PT2H</ExecutionTimeLimit><Enabled>true</Enabled></Settings>
  <Actions Context="Author"><Exec>
    <Command>cmd.exe</Command>
    <Arguments>/c "{escape(WIN_ROOT)}\\scheduler\\run_update.bat" {flag}</Arguments>
    <WorkingDirectory>{escape(WIN_ROOT)}</WorkingDirectory>
  </Exec></Actions>
</Task>
"""


WIN_ROOT = str(RU) if os.name == "nt" else "%MIIS_RISK_DIR%"


def write() -> list[Path]:
    out = []
    for key, (label, flag, times) in JOBS.items():
        p = HERE / f"{label}.plist"
        p.write_text(plist(label, flag, times), encoding="utf-8")
        out.append(p)
        x = HERE / f"windows_task_{key}.xml"
        x.write_text(task_xml(f"MIIS_Risk_{key}", flag, times), encoding="utf-16")
        out.append(x)
    (HERE / "crontab.txt").write_text(cron(), encoding="utf-8")
    out.append(HERE / "crontab.txt")
    st = ["Windows Task Scheduler (schtasks) — RiskUnit qovluğunda işlədin:"]
    for key, (_l, flag, times) in JOBS.items():
        st.append(f'schtasks /Create /TN "MIIS_Risk_{key}" /XML "scheduler\\windows_task_{key}.xml"')
        for h, m in times:
            st.append(f'rem və ya: schtasks /Create /TN "MIIS_Risk_{key}_{h:02d}{m:02d}" /SC DAILY /ST {h:02d}:{m:02d} '
                      f'/TR "cmd /c \\"{WIN_ROOT}\\scheduler\\run_update.bat\\" {flag}"')
    (HERE / "windows_task.xml.txt").write_text("\n".join(st) + "\n", encoding="utf-8")
    out.append(HERE / "windows_task.xml.txt")
    return out


def install(uninstall: bool = False) -> None:
    la = Path.home() / "Library" / "LaunchAgents"
    la.mkdir(parents=True, exist_ok=True)
    for _k, (label, _f, _t) in JOBS.items():
        dst = la / f"{label}.plist"
        if dst.exists():
            subprocess.run(["launchctl", "unload", str(dst)], check=False)
        if uninstall:
            dst.unlink(missing_ok=True)
            print(f"silindi: {dst}")
            continue
        dst.write_text((HERE / f"{label}.plist").read_text(encoding="utf-8"), encoding="utf-8")
        subprocess.run(["launchctl", "load", str(dst)], check=True)
        print(f"quraşdırıldı: {dst}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    a = ap.parse_args()
    for p in write():
        print(f"yazıldı: {p.relative_to(RU)}")
    if a.install or a.uninstall:
        if sys.platform != "darwin":
            sys.exit("--install yalnız macOS üçündür (Linux: crontab.txt, Windows: windows_task_*.xml)")
        install(uninstall=a.uninstall)
