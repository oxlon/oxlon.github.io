@echo off
rem SiyasetModel (MIIS 15.5.4) - API serverini basladir ve siyaset panelini brauzerde acir (Windows). Iki klikle ise salin.
rem Nisanlar: set POLICY_API_TOKENS=siyaset-oxu:read,siyaset-yaz:write  (standart: demo-read / demo-write, yalniz yerli)
rem Avtonom rejim: SiyasetModel_Baslat.bat --schedule 06:30,18:30 --watch     Sebekesiz: set POLICY_NO_NETWORK=1
chcp 65001 >nul
cd /d "%~dp0"
if "%POLICY_API_PORT%"=="" set POLICY_API_PORT=8792
set URL=http://127.0.0.1:%POLICY_API_PORT%/panel/
set PY=
rem Python: POLICY_PYTHON > MIKRO_PYTHON > .venv > %USERPROFILE%\venvs\miis-model > py -3 > python (numpy/pandas/scipy olan ilk namized)
for %%C in ("%POLICY_PYTHON%" "%MIKRO_PYTHON%" ".venv\Scripts\python.exe" "%USERPROFILE%\venvs\miis-model\Scripts\python.exe") do (
  if not defined PY if not "%%~C"=="" if exist "%%~C" ( "%%~C" -c "import numpy, pandas, scipy" >nul 2>nul && set "PY=%%~C" )
)
if not defined PY ( where py >nul 2>nul && ( py -3 -c "import numpy, pandas, scipy" >nul 2>nul && set "PY=py -3" ) )
if not defined PY ( set "PY=python" & echo XEBERDARLIQ: numpy/pandas/scipy olan Python tapilmadi - hesablamalar islemeyecek. Qurasdirin: python -m pip install numpy pandas scipy openpyxl )
if not exist logs\api mkdir logs\api
echo SiyasetModel serveri basladilir: %URL%   (Python: %PY%)
start "SiyasetModel API" %PY% api\server.py --port %POLICY_API_PORT% %*
timeout /t 4 /nobreak >nul
start "" "%URL%"
