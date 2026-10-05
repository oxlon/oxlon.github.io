#!/bin/bash
# MikroModel — serveri başladır və iş panelini brauzerdə açır (macOS). İki kliklə işə salın.
# Nişanları dəyişmək üçün: export API_TOKENS="mikro-oxu:read,mikro-yaz:write" (standart: demo-read / demo-write)
cd "$(dirname "$0")" || exit 1
PORT="${MIKRO_PORT:-8790}"
URL="http://127.0.0.1:${PORT}/panel/"
PY="$(command -v python3)"
if [ -z "$PY" ]; then echo "XƏTA: python3 tapılmadı"; read -r -p "Enter..." _; exit 1; fi
if curl -s -o /dev/null "http://127.0.0.1:${PORT}/api/v1/health"; then
  echo "Server artıq işləyir: ${URL}"; open "$URL"; exit 0
fi
echo "MikroModel serveri başladılır: ${URL}   (dayandırmaq üçün bu pəncərədə Ctrl+C)"
"$PY" api/server.py --port "$PORT" "$@" &
PID=$!
for i in $(seq 1 40); do
  curl -s -o /dev/null "http://127.0.0.1:${PORT}/api/v1/health" && break
  sleep 0.25
done
open "$URL"
trap 'kill $PID 2>/dev/null' INT TERM
wait $PID
