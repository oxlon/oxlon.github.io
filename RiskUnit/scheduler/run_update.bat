@echo off
rem MİİS §15.5.3 — NFR2 avtomatik yeniləmə (Windows Task Scheduler). Qovluq bu faylın yerindən müəyyən edilir.
rem   scheduler\run_update.bat --daily   |   scheduler\run_update.bat --full
set "RU=%~dp0.."
cd /d "%RU%" || exit /b 1
if "%MIIS_PYTHON%"=="" (if exist "%RU%\.venv\Scripts\python.exe" (set "MIIS_PYTHON=%RU%\.venv\Scripts\python.exe") else (set "MIIS_PYTHON=python"))
echo %DATE% %TIME% baslandi: update.py %* >> "%RU%\output\NFR2_cron.log"
"%MIIS_PYTHON%" update.py %* >> "%RU%\output\NFR2_cron.log" 2>&1
echo %DATE% %TIME% bitdi (kod %ERRORLEVEL%) >> "%RU%\output\NFR2_cron.log"
