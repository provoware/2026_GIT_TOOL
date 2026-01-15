#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DEBUG_MODE=0
LOG_FILE=""
NO_LOG=0
SAFE_MODE=0
SANDBOX_MODE=0
SANDBOX_ROOT=""

show_help() {
  cat <<'EOF'
Start-Routine (Struktur + Checks + Fortschritt)

Nutzung:
  ./scripts/start.sh [--debug] [--log-file <pfad>] [--no-log] [--safe-mode] [--ghost-mode] [--sandbox]

Optionen:
  --debug           Debug-Modus aktivieren (mehr Diagnoseausgaben).
  --log-file <pfad> Logdatei überschreiben (Standard: logs/start_run.log).
  --no-log          Keine Logdatei schreiben (nur Terminalausgabe).
  --safe-mode       Schreibgeschützter Start (keine Änderungen, nur Checks).
  --ghost-mode      Alias für --safe-mode (Testmodus ohne Schreiben).
  --sandbox         Start in isolierter Sandbox (writes nur in Sandbox).
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
    --safe-mode)
      SAFE_MODE=1
      shift
      ;;
    --ghost-mode)
      SAFE_MODE=1
      shift
      ;;
    --sandbox)
      SANDBOX_MODE=1
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

ORIGINAL_ROOT="${ROOT_DIR}"

create_sandbox() {
  local source_root="$1"
  local sandbox
  sandbox="$(mktemp -d -t git_tool_sandbox_XXXXXX)"

  local dirs=(config system scripts modules src tests data logs)
  for dir in "${dirs[@]}"; do
    if [[ -d "${source_root}/${dir}" ]]; then
      cp -a "${source_root}/${dir}" "${sandbox}/"
    else
      mkdir -p "${sandbox}/${dir}"
    fi
  done

  local files=(todo.txt CHANGELOG.md DEV_DOKU.md DONE.md PROGRESS.md README.md standards.md STYLEGUIDE.md)
  for file in "${files[@]}"; do
    if [[ -f "${source_root}/${file}" ]]; then
      cp -a "${source_root}/${file}" "${sandbox}/${file}"
    fi
  done

  echo "Start-Routine: Sandbox erstellt: ${sandbox}" >&2
  echo "Start-Routine: Alle Schreibzugriffe bleiben in der Sandbox." >&2
  echo "${sandbox}"
}

if [[ "${SAFE_MODE}" -eq 1 ]]; then
  NO_LOG=1
fi

if [[ "${SANDBOX_MODE}" -eq 1 ]]; then
  SANDBOX_ROOT="$(create_sandbox "${ORIGINAL_ROOT}")"
  ROOT_DIR="${SANDBOX_ROOT}"
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
  echo "Start-Routine: Logging deaktiviert (--no-log oder Safe-Mode)."
fi

TOTAL_STEPS=12
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
update_progress "Projektstruktur wird vorbereitet"
if [[ "${SAFE_MODE}" -eq 1 ]]; then
  run_step "Projektstruktur wird vorbereitet" \
    "Safe-Mode aktiv: Bootstrap übersprungen (schreibgeschützt)." \
    bash -c "echo 'Safe-Mode: Bootstrap übersprungen (keine Schreibzugriffe).'"
else
  run_step "Projektstruktur wird vorbereitet" \
    "Bitte ./scripts/bootstrap.sh erneut starten, falls Ordner fehlen." \
    "${ROOT_DIR}/scripts/bootstrap.sh"
fi

CURRENT_STEP=3
update_progress "Strukturtrennung wird geprüft"
run_step "Struktur-Check" \
  "Bitte Ordnerstruktur laut standards.md korrigieren." \
  python "${ROOT_DIR}/system/structure_checker.py" --root "${ROOT_DIR}" "${DEBUG_ARGS[@]}"

CURRENT_STEP=4
update_progress "Self-Repair (Selbstreparatur) wird ausgeführt"
SELF_REPAIR_ARGS=(--root "${ROOT_DIR}")
if [[ "${SAFE_MODE}" -eq 1 ]]; then
  SELF_REPAIR_ARGS+=(--dry-run)
fi
run_step "Self-Repair" \
  "Tipp: python system/self_repair.py --root . ausführen." \
  python "${ROOT_DIR}/system/self_repair.py" "${SELF_REPAIR_ARGS[@]}" "${DEBUG_ARGS[@]}"

CURRENT_STEP=5
update_progress "Health-Check (Sicherheitsprüfung) läuft"
run_step "Health-Check" \
  "Tipp: python system/health_check.py --root . ausführen." \
  python "${ROOT_DIR}/system/health_check.py" --root "${ROOT_DIR}" "${DEBUG_ARGS[@]}"

CURRENT_STEP=6
update_progress "JSON-Dateien werden geprüft"
run_step "JSON-Validierung" \
  "Bitte JSON-Dateien in config/ und modules/ prüfen (Syntax/Struktur)." \
  python "${ROOT_DIR}/system/json_validator.py" --root "${ROOT_DIR}" "${DEBUG_ARGS[@]}"

CURRENT_STEP=7
update_progress "Dateinamen werden korrigiert"
FILENAME_ARGS=(--root "${ROOT_DIR}")
if [[ "${SAFE_MODE}" -eq 1 ]]; then
  FILENAME_ARGS+=(--dry-run)
fi
run_step "Dateinamen-Korrektur" \
  "Tipp: Namen in data/ und logs/ prüfen (snake_case, keine Leerzeichen)." \
  python "${ROOT_DIR}/system/filename_fixer.py" "${FILENAME_ARGS[@]}" "${DEBUG_ARGS[@]}"

CURRENT_STEP=8
update_progress "Abhängigkeiten werden geprüft"
DEPENDENCY_ARGS=(--requirements "${ROOT_DIR}/config/requirements.txt")
if [[ "${SAFE_MODE}" -eq 1 || "${SANDBOX_MODE}" -eq 1 ]]; then
  DEPENDENCY_ARGS+=(--no-auto-install)
fi
run_step "Abhängigkeiten prüfen" \
  "Tipp: python -m pip install -r config/requirements.txt ausführen." \
  python "${ROOT_DIR}/system/dependency_checker.py" \
  "${DEPENDENCY_ARGS[@]}" \
  "${DEBUG_ARGS[@]}"

CURRENT_STEP=9
update_progress "Fortschritt wird aus todo.txt berechnet"
TODO_BASE_ARGS=(--config "${ROOT_DIR}/config/todo_config.json")
TODO_PROGRESS_ARGS=()
PROGRESS_WRITE=0
if [[ "${SAFE_MODE}" -eq 0 ]]; then
  TODO_PROGRESS_ARGS+=(--write-progress)
  PROGRESS_WRITE=1
fi
run_step "Fortschritt berechnen" \
  "Bitte todo.txt prüfen (Aufgabenliste/Format)." \
  python "${ROOT_DIR}/system/todo_manager.py" "${TODO_BASE_ARGS[@]}" progress \
  "${TODO_PROGRESS_ARGS[@]}" "${DEBUG_ARGS[@]}"

CURRENT_STEP=10
update_progress "Module werden geprüft (inkl. Verbund-Checks)"
run_step "Module prüfen (Verbund-Checks)" \
  "Bitte config/modules.json und module_selftests.json prüfen (id, path, manifest, tests)." \
  python "${ROOT_DIR}/system/module_integration_checks.py" \
  --config "${ROOT_DIR}/config/modules.json" \
  --selftests "${ROOT_DIR}/config/module_selftests.json" \
  "${DEBUG_ARGS[@]}"

CURRENT_STEP=11
update_progress "Tests werden geprüft (nur nach kompletter Runde)"
if [[ "${SAFE_MODE}" -eq 1 ]]; then
  run_step "Test-Sperre" \
    "Safe-Mode aktiv: Test-Sperre übersprungen (schreibgeschützt)." \
    bash -c "echo 'Safe-Mode: Test-Sperre übersprungen (keine Schreibzugriffe).'"
else
  run_step "Test-Sperre" \
    "Tipp: ./scripts/run_tests.sh ausführen und Log prüfen." \
    python "${ROOT_DIR}/system/test_gate.py" --config "${ROOT_DIR}/config/test_gate.json" "${DEBUG_ARGS[@]}"
fi

CURRENT_STEP=12
if [[ ${#ERRORS[@]} -gt 0 ]]; then
  update_progress "Start-Routine abgeschlossen (mit Hinweisen)"
  echo "Start-Routine: Es gab ${#ERRORS[@]} Hinweis(e)."
  for entry in "${ERRORS[@]}"; do
    IFS="|" read -r label suggestion <<< "${entry}"
    echo "- ${label}"
    echo "  Tipp: ${suggestion}"
  done
  if [[ "${PROGRESS_WRITE}" -eq 1 ]]; then
    echo "Start-Routine: PROGRESS.md wurde aktualisiert."
  else
    echo "Start-Routine: PROGRESS.md wurde nicht geschrieben (Safe-Mode)."
  fi
  echo "Start-Routine: Ampelstatus: rot (mindestens ein Fehler)."
  exit 2
fi

update_progress "Start-Routine abgeschlossen"
if [[ "${PROGRESS_WRITE}" -eq 1 ]]; then
  echo "Start-Routine: PROGRESS.md wurde aktualisiert."
else
  echo "Start-Routine: PROGRESS.md wurde nicht geschrieben (Safe-Mode)."
fi
echo "Start-Routine: Ampelstatus: grün (keine Fehler)."
