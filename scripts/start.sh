#!/usr/bin/env bash
set -uo pipefail

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

TOTAL_STEPS=10
CURRENT_STEP=0
ERRORS=()

update_progress() {
  local message="$1"
  local percent=$((CURRENT_STEP * 100 / TOTAL_STEPS))
  echo "Start-Routine: ${message} (Fortschritt: ${percent} %)"
}

run_step() {
  local label="$1"
  local suggestion="$2"
  shift 2
  if "$@"; then
    return 0
  fi
  local exit_code=$?
  echo "Start-Routine: Fehler bei '${label}' (Exit-Code: ${exit_code})."
  echo "Start-Routine: Alternative: ${suggestion}"
  ERRORS+=("${label}|${suggestion}")
  return 0
}

CURRENT_STEP=1
update_progress "Umgebung wird geprüft"
run_step "Umgebung wird geprüft" \
  "Bitte ./scripts/check_env.sh ausführen und fehlende Tools installieren." \
  "${ROOT_DIR}/scripts/check_env.sh"

CURRENT_STEP=2
update_progress "Projektstruktur wird geprüft"
run_step "Projektstruktur wird geprüft" \
  "Bitte ./scripts/bootstrap.sh erneut starten, falls Ordner fehlen." \
  "${ROOT_DIR}/scripts/bootstrap.sh"

CURRENT_STEP=3
update_progress "Health-Check (Sicherheitsprüfung + Self-Repair) läuft"
run_step "Health-Check" \
  "Tipp: python system/health_check.py --root . --self-repair ausführen." \
  python "${ROOT_DIR}/system/health_check.py" --root "${ROOT_DIR}" --self-repair "${DEBUG_ARGS[@]}"

CURRENT_STEP=4
update_progress "JSON-Dateien werden geprüft"
run_step "JSON-Validierung" \
  "Bitte JSON-Dateien in config/ und modules/ prüfen (Syntax/Struktur)." \
  python "${ROOT_DIR}/system/json_validator.py" --root "${ROOT_DIR}" "${DEBUG_ARGS[@]}"

CURRENT_STEP=5
update_progress "Dateinamen werden korrigiert"
run_step "Dateinamen-Korrektur" \
  "Tipp: Namen in data/ und logs/ prüfen (snake_case, keine Leerzeichen)." \
  python "${ROOT_DIR}/system/filename_fixer.py" --root "${ROOT_DIR}" "${DEBUG_ARGS[@]}"

CURRENT_STEP=6
update_progress "Abhängigkeiten werden geprüft"
run_step "Abhängigkeiten prüfen" \
  "Tipp: python -m pip install -r config/requirements.txt ausführen." \
  python "${ROOT_DIR}/system/dependency_checker.py" \
  --requirements "${ROOT_DIR}/config/requirements.txt" \
  "${DEBUG_ARGS[@]}"

CURRENT_STEP=7
update_progress "Fortschritt wird aus todo.txt berechnet"
run_step "Fortschritt berechnen" \
  "Bitte todo.txt prüfen (Aufgabenliste/Format)." \
  python "${ROOT_DIR}/system/todo_manager.py" progress --write-progress "${DEBUG_ARGS[@]}"

CURRENT_STEP=8
update_progress "Module werden geprüft (inkl. Verbund-Checks)"
run_step "Module prüfen (Verbund-Checks)" \
  "Bitte config/modules.json und module_selftests.json prüfen (id, path, manifest, tests)." \
  python "${ROOT_DIR}/system/module_integration_checks.py" \
  --config "${ROOT_DIR}/config/modules.json" \
  --selftests "${ROOT_DIR}/config/module_selftests.json" \
  "${DEBUG_ARGS[@]}"

CURRENT_STEP=9
update_progress "Tests werden geprüft (nur nach kompletter Runde)"
run_step "Test-Sperre" \
  "Tipp: ./scripts/run_tests.sh ausführen und Log prüfen." \
  python "${ROOT_DIR}/system/test_gate.py" --config "${ROOT_DIR}/config/test_gate.json" "${DEBUG_ARGS[@]}"

CURRENT_STEP=10
if [[ ${#ERRORS[@]} -gt 0 ]]; then
  update_progress "Start-Routine abgeschlossen (mit Hinweisen)"
  echo "Start-Routine: Es gab ${#ERRORS[@]} Hinweis(e)."
  for entry in "${ERRORS[@]}"; do
    IFS="|" read -r label suggestion <<< "${entry}"
    echo "- ${label}"
    echo "  Tipp: ${suggestion}"
  done
  echo "Start-Routine: PROGRESS.md wurde aktualisiert."
  exit 2
fi

update_progress "Start-Routine abgeschlossen"
echo "Start-Routine: PROGRESS.md wurde aktualisiert."
