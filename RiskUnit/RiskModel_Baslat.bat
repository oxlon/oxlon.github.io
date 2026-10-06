@echo off
rem RiskModel (MIIS 15.5.3) - API serverini basladir ve risk panelini brauzerde acir (Windows). Iki klikle ise salin.
rem Nisanlar: set RISK_API_TOKENS=risk-oxu:read,risk-yaz:write  (standart: demo-read / demo-write, yalniz yerli)
rem Avtonom rejim: RiskModel_Baslat.bat --schedule 06:30,13:00,18:30 --watch     Sebekesiz: set RISK_NO_NETWORK=1
chcp 65001 >nul
cd /d "%~dp0"
if "%RISK_API_PORT%"=="" set RISK_API_PORT=8791
set URL=http://127.0.0.1:%RISK_API_PORT%/panel/
set PY=
rem Python: RISK_PYTHON > MIKRO_PYTHON > .venv > %USERPROFILE%\venvs\miis-model > py -3 > python (numpy/pandas/scipy olan ilk namized)
for %%C in ("%RISK_PYTHON%" "%MIKRO_PYTHON%" ".venv\Scripts\python.exe" "%USERPROFILE%\venvs\miis-model\Scripts\python.exe") do (
  if not defined PY if not "%%~C"=="" if exist "%%~C" ( "%%~C" -c "import numpy, pandas, scipy" >nul 2>nul && set "PY=%%~C" )
)
if not defined PY ( where py >nul 2>nul && ( py -3 -c "import numpy, pandas, scipy" >nul 2>nul && set "PY=py -3" ) )
if not defined PY ( set "PY=python" & echo XEBERDARLIQ: numpy/pandas/scipy olan Python tapilmadi - hesablamalar islemeyecek. Qurasdirin: python -m pip install -r requirements.txt )
if not exist logs\api mkdir logs\api
echo RiskModel serveri basladilir: %URL%   (Python: %PY%)
start "RiskModel API" %PY% api\server.py --port %RISK_API_PORT% %*
timeout /t 4 /nobreak >nul
start "" "%URL%"
