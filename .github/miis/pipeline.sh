#!/usr/bin/env bash
# MİİS — one pipeline stage, run from the repository root (the SAME commands in GitHub Actions and in the
# local rehearsal deploy/rehearse.sh).  Usage: bash .github/miis/pipeline.sh micro|risk|policy|panels
# Environment (set by the workflow): PYTHON (default python3), MICRO_KERNEL=miis-model, POLICY_OXLON_DISABLED=1,
# RISK_FETCH=1 (RiskUnit --fetch), RISK_PDF=0 (adds --no-pdf), RISK_NO_NETWORK / POLICY_NO_NETWORK (0|1).
set -uo pipefail
PY="${PYTHON:-python3}"
ROOT="$(pwd)"
stage="${1:?stage: micro|risk|policy|panels}"
case "$stage" in
  micro)
    cd "$ROOT/MicroUnit" && "$PY" run_all.py --kernel "${MICRO_KERNEL:-miis-model}"; rc=$?
    if [ $rc -ne 0 ]; then          # stage output goes to logs/<run_id>/<stage>.log — show it in the CI log
      d=$(ls -td logs/r*/ 2>/dev/null | head -1); for f in "$d"*.log; do echo "== $f"; tail -n 40 "$f"; done
    fi
    exit $rc ;;
  risk)
    args=()
    [ "${RISK_FETCH:-1}" = "1" ] && [ "${RISK_NO_NETWORK:-0}" != "1" ] && args+=(--fetch)
    [ "${RISK_PDF:-1}" = "0" ] && args+=(--no-pdf)
    cd "$ROOT/RiskUnit" && "$PY" run_all.py "${args[@]+"${args[@]}"}" ;;
  policy)
    cd "$ROOT/PolicyUnit" && "$PY" run_all.py ;;
  panels)
    # rebuild every panel/site last, so all hubs carry the stamps of THIS run (also after a failed stage)
    rc=0
    for b in MicroUnit/panel/build_panel.py MicroUnit/site/build_site.py RiskUnit/panel/build_panel.py \
             PolicyUnit/panel/build_panel.py; do
      echo "== $b"
      (cd "$ROOT/$(dirname "$(dirname "$b")")" && "$PY" "${b#*/}") || { echo "XƏTA: $b"; rc=1; }
    done
    exit $rc ;;
  *) echo "naməlum mərhələ: $stage" >&2; exit 2 ;;
esac
