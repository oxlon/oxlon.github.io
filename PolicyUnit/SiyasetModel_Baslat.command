#!/bin/bash
# SiyasətModel (MİİS §15.5.4) — API serverini başladır və siyasət panelini brauzerdə açır (macOS). İki kliklə işə salın.
# Nişanlar: export POLICY_API_TOKENS="siyaset-oxu:read,siyaset-yaz:write"   (standart: demo-read / demo-write, yalnız yerli)
# Avtonom rejim:  ./SiyasetModel_Baslat.command --schedule 06:30,18:30 --watch
# Şəbəkəsiz:      POLICY_NO_NETWORK=1 ./SiyasetModel_Baslat.command
cd "$(dirname "$0")" || exit 1
PORT="${POLICY_API_PORT:-8792}"
URL="http://127.0.0.1:${PORT}/panel/"
# Python: POLICY_PYTHON > MIKRO_PYTHON > .venv > ~/venvs/miis-model > python3 — numpy/pandas/scipy olan ilk namizəd
PY=""; FALLBACK=""
for c in "$POLICY_PYTHON" "$MIKRO_PYTHON" ".venv/bin/python3" "../.venv/bin/python3" "$HOME/venvs/miis-model/bin/python3" "$(command -v python3)"; do
  if [ -n "$c" ] && [ -x "$c" ]; then
    [ -z "$FALLBACK" ] && FALLBACK="$c"
    if "$c" -c "import numpy, pandas, scipy" 2>/dev/null; then PY="$c"; break; fi
  fi
done
if [ -z "$PY" ]; then
  if [ -z "$FALLBACK" ]; then echo "XƏTA: python3 tapılmadı"; read -r -p "Enter..." _; exit 1; fi
  PY="$FALLBACK"
  echo "XƏBƏRDARLIQ: $PY mühitində numpy/pandas/scipy yoxdur — panel açılacaq, lakin hesablamalar işləməyəcək."
  echo "  Quraşdırmaq üçün: $PY -m pip install numpy pandas scipy openpyxl"
fi
if curl -s -o /dev/null "http://127.0.0.1:${PORT}/api/v1/health"; then
  echo "Server artıq işləyir: ${URL}"; open "$URL"; exit 0
fi
echo "SiyasətModel serveri başladılır: ${URL}   (Python: $PY; dayandırmaq üçün bu pəncərədə Ctrl+C)"
"$PY" api/server.py --port "$PORT" --python "$PY" "$@" &
PID=$!
for i in $(seq 1 60); do
  curl -s -o /dev/null "http://127.0.0.1:${PORT}/api/v1/health" && break
  sleep 0.25
done
open "$URL"
trap 'kill $PID 2>/dev/null' INT TERM
wait $PID
