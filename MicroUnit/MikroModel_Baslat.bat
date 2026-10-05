@echo off
rem MikroModel - serveri basladir ve is panelini brauzerde acir (Windows). Iki klikle ise salin.
rem Nisanlar: set API_TOKENS=mikro-oxu:read,mikro-yaz:write  (standart: demo-read / demo-write)
chcp 65001 >nul
cd /d "%~dp0"
if "%MIKRO_PORT%"=="" set MIKRO_PORT=8790
set URL=http://127.0.0.1:%MIKRO_PORT%/panel/
where py >nul 2>nul && (set PY=py -3) || (set PY=python)
echo MikroModel serveri basladilir: %URL%
start "MikroModel API" %PY% api\server.py --port %MIKRO_PORT% %*
timeout /t 3 /nobreak >nul
start "" "%URL%"
