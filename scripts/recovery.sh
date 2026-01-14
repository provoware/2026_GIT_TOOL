#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DEBUG_MODE=0
LOG_FILE=""
NO_LOG=0
SAFE_MODE=0

show_help() {
  cat <<'HELP'
Recovery-Modus (Notfallstart mit Reparatur)

Nutzung:
  ./scripts/recovery.sh [--debug] [--log-file <pfad>] [--no-log] [--safe-mode]

Optionen:
  --debug           Debug-Modus aktivieren (mehr Diagnoseausgaben).
  --log-file <pfad> Logdatei überschreiben (Standard: logs/recovery_run.log).
  --no-log          Keine Logdatei schreiben (nur Terminalausgabe).
  --safe-mode       Schreibgeschützt arbeiten (keine Reparatur/Änderungen).
  -h, --help        Diese Hilfe anzeigen.
HELP
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

if ! command -v python >/dev/null 2>&1; then
  echo "Fehler: Python ist nicht installiert. Bitte Python installieren."
  exit 1
fi

DEBUG_ARGS=()
if [[ "${DEBUG_MODE}" -eq 1 ]]; then
  DEBUG_ARGS=(--debug)
fi

if [[ "${NO_LOG}" -eq 0 ]]; then
  if [[ -z "${LOG_FILE}" ]]; then
    LOG_FILE="${ROOT_DIR}/logs/recovery_run.log"
  fi
  LOG_DIR="$(dirname "${LOG_FILE}")"
  mkdir -p "${LOG_DIR}"
  touch "${LOG_FILE}"
  exec > >(tee -a "${LOG_FILE}") 2>&1
  echo "Recovery-Modus: Logdatei aktiv: ${LOG_FILE}"
else
  echo "Recovery-Modus: Logging deaktiviert (--no-log)."
fi

ERRORS=()

run_step() {
  local label="$1"
  local suggestion="$2"
  shift 2
  if "$@"; then
    echo "Recovery-Modus: OK – ${label}"
    return 0
  fi
  local exit_code=$?
  echo "Recovery-Modus: Problem bei '${label}' (Exit-Code: ${exit_code})."
  echo "Recovery-Modus: Tipp: ${suggestion}"
  ERRORS+=("${label}|${suggestion}")
  return 0
}

echo "Recovery-Modus: Notfallstart läuft (minimale Prüfungen + Reparatur)."

run_step "Struktur-Check" \
  "Ordnerstruktur laut standards.md prüfen und korrigieren." \
  python "${ROOT_DIR}/system/structure_checker.py" --root "${ROOT_DIR}" "${DEBUG_ARGS[@]}"

HEALTH_ARGS=(--root "${ROOT_DIR}")
if [[ "${SAFE_MODE}" -eq 0 ]]; then
  HEALTH_ARGS+=(--self-repair)
fi
run_step "Health-Check" \
  "Tipp: python system/health_check.py --root . --self-repair" \
  python "${ROOT_DIR}/system/health_check.py" "${HEALTH_ARGS[@]}" "${DEBUG_ARGS[@]}"

run_step "JSON-Validierung" \
  "Konfigurationsdateien prüfen (Syntax/Struktur)." \
  python "${ROOT_DIR}/system/json_validator.py" --root "${ROOT_DIR}" "${DEBUG_ARGS[@]}"

run_step "Modul-Check (ohne Selftests)" \
  "Module/Manifeste prüfen und Fehler korrigieren." \
  python "${ROOT_DIR}/system/module_integration_checks.py" \
  --config "${ROOT_DIR}/config/modules.json" \
  --selftests "${ROOT_DIR}/config/module_selftests.json" \
  --skip-selftests \
  "${DEBUG_ARGS[@]}"

if [[ ${#ERRORS[@]} -gt 0 ]]; then
  echo "Recovery-Modus: Fertig mit ${#ERRORS[@]} Hinweis(en)."
  for entry in "${ERRORS[@]}"; do
    IFS="|" read -r label suggestion <<< "${entry}"
    echo "- ${label}"
    echo "  Tipp: ${suggestion}"
  done
  echo "Recovery-Modus: Danach bitte ./scripts/start.sh ausführen."
  exit 2
fi

echo "Recovery-Modus: Fertig. Bitte ./scripts/start.sh für den Normalstart ausführen."
