#!/bin/sh
# MİİS §15.5.3 — NFR2 avtomatik yeniləmə (macOS launchd / Linux cron).
# Qovluq bu skriptin yerindən müəyyən edilir (sabit yol yoxdur):  scheduler/run_update.sh --daily | --full
RU="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RU" || exit 1
PY="${MIIS_PYTHON:-}"
[ -z "$PY" ] && [ -x "$RU/.venv/bin/python3" ] && PY="$RU/.venv/bin/python3"
[ -z "$PY" ] && [ -x "$HOME/venvs/miis-model/bin/python3" ] && PY="$HOME/venvs/miis-model/bin/python3"
[ -z "$PY" ] && PY="$(command -v python3)"
LOCK="$RU/output/.update.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "$(date -u +%FT%TZ) başqa yeniləmə gedir — buraxıldı" >> "$RU/output/NFR2_cron.log"; exit 0
fi
trap 'rmdir "$LOCK"' EXIT INT TERM
echo "$(date -u +%FT%TZ) başladı: update.py $*" >> "$RU/output/NFR2_cron.log"
"$PY" update.py "$@" >> "$RU/output/NFR2_cron.log" 2>&1
RC=$?
echo "$(date -u +%FT%TZ) bitdi (kod $RC)" >> "$RU/output/NFR2_cron.log"
exit $RC
