#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DEBUG_MODE=0
LOG_FILE=""
NO_LOG=0

show_help() {
  cat <<'EOF'
Start-Routine (Struktur + Checks + Fortschritt)

Nutzung:
  ./scripts/start.sh [--debug] [--log-file <pfad>] [--no-log]

Optionen:
  --debug           Debug-Modus aktivieren (mehr Diagnoseausgaben).
  --log-file <pfad> Logdatei überschreiben (Standard: logs/start_run.log).
  --no-log          Keine Logdatei schreiben (nur Terminalausgabe).
  -h, --help        Diese Hilfe anzeigen.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --debug)
      DEBUG_MODE=1
      shift
      ;;
    --log-file)
      if [[ -z "${2:-}" ]]; then
        echo "Fehler: --log-file braucht einen Pfad."
        exit 2
      fi
      LOG_FILE="$2"
      shift 2
      ;;
    --no-log)
      NO_LOG=1
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Fehler: Unbekannte Option: $1"
      show_help
      exit 2
      ;;
  esac
done

DEBUG_ARGS=()
if [[ "${DEBUG_MODE}" -eq 1 ]]; then
  DEBUG_ARGS=(--debug)
fi

if [[ "${NO_LOG}" -eq 0 ]]; then
  if [[ -z "${LOG_FILE}" ]]; then
    LOG_FILE="${ROOT_DIR}/logs/start_run.log"
  fi
  LOG_DIR="$(dirname "${LOG_FILE}")"
  mkdir -p "${LOG_DIR}"
  touch "${LOG_FILE}"
  exec > >(tee -a "${LOG_FILE}") 2>&1
  echo "Start-Routine: Logdatei aktiv: ${LOG_FILE}"
else
  echo "Start-Routine: Logging deaktiviert (--no-log)."
fi

TOTAL_STEPS=8
CURRENT_STEP=0

update_progress() {
  local message="$1"
  local percent=$((CURRENT_STEP * 100 / TOTAL_STEPS))
  echo "Start-Routine: ${message} (Fortschritt: ${percent} %)"
}

CURRENT_STEP=1
update_progress "Umgebung wird geprüft"
"${ROOT_DIR}/scripts/check_env.sh"

CURRENT_STEP=2
update_progress "Projektstruktur wird geprüft"
"${ROOT_DIR}/scripts/bootstrap.sh"

CURRENT_STEP=3
update_progress "Health-Check (Sicherheitsprüfung) läuft"
update_progress "Health-Check (Sicherheitsprüfung + Self-Repair) läuft"
python "${ROOT_DIR}/system/health_check.py" --root "${ROOT_DIR}" --self-repair "${DEBUG_ARGS[@]}"

CURRENT_STEP=4
update_progress "Abhängigkeiten werden geprüft"
python "${ROOT_DIR}/system/dependency_checker.py" \
  --requirements "${ROOT_DIR}/config/requirements.txt" \
  "${DEBUG_ARGS[@]}"

CURRENT_STEP=5
update_progress "Fortschritt wird aus todo.txt berechnet"
python "${ROOT_DIR}/system/todo_manager.py" progress --write-progress "${DEBUG_ARGS[@]}"

CURRENT_STEP=6
update_progress "Module werden geprüft"
python "${ROOT_DIR}/system/module_checker.py" --config "${ROOT_DIR}/config/modules.json" "${DEBUG_ARGS[@]}"

CURRENT_STEP=7
update_progress "Tests werden geprüft (nur nach kompletter Runde)"
python "${ROOT_DIR}/system/test_gate.py" --config "${ROOT_DIR}/config/test_gate.json" "${DEBUG_ARGS[@]}"

CURRENT_STEP=8
update_progress "Start-Routine abgeschlossen"
echo "Start-Routine: PROGRESS.md wurde aktualisiert."
