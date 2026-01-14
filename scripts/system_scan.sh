#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DEBUG_MODE=0

show_help() {
  cat <<'DOC'
System-Scan (Vorabprüfung = Scanner vor dem Start)

Nutzung:
  ./scripts/system_scan.sh [--debug]

Dieser Scan prüft nur lesend (keine Schreibzugriffe):
  - Umgebung (Python, Start-Skript)
  - Ordnerstruktur und Trennung (System/Config/Daten/Logs)
  - Health-Check (ohne Self-Repair)
  - JSON-Validierung
  - Modul-Check + Modulverbund-Checks
  - Abhängigkeiten (ohne Auto-Installation)
DOC
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --debug)
      DEBUG_MODE=1
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

run_step() {
  local label="$1"
  local suggestion="$2"
  shift 2
  echo "System-Scan: ${label}"
  if "$@"; then
    return 0
  fi
  local exit_code=$?
  echo "System-Scan: Fehler bei '${label}' (Exit-Code: ${exit_code})."
  echo "System-Scan: Tipp: ${suggestion}"
  return 1
}

run_step "Umgebung prüfen" \
  "Bitte ./scripts/check_env.sh ausführen und Hinweise prüfen." \
  "${ROOT_DIR}/scripts/check_env.sh"

run_step "Struktur & Trennung prüfen" \
  "Bitte Ordnerstruktur laut standards.md korrigieren." \
  python "${ROOT_DIR}/system/structure_checker.py" --root "${ROOT_DIR}" "${DEBUG_ARGS[@]}"

run_step "Health-Check (ohne Self-Repair)" \
  "Bitte python system/health_check.py --root . ausführen und Hinweise lesen." \
  python "${ROOT_DIR}/system/health_check.py" --root "${ROOT_DIR}" "${DEBUG_ARGS[@]}"

run_step "JSON-Validierung" \
  "Bitte JSON-Dateien in config/ und modules/ prüfen." \
  python "${ROOT_DIR}/system/json_validator.py" --root "${ROOT_DIR}" "${DEBUG_ARGS[@]}"

run_step "Modul-Check" \
  "Bitte config/modules.json und Module prüfen." \
  python "${ROOT_DIR}/system/module_checker.py" --config "${ROOT_DIR}/config/modules.json" "${DEBUG_ARGS[@]}"

run_step "Modulverbund-Checks" \
  "Bitte module_selftests.json und Manifest-IDs prüfen." \
  python "${ROOT_DIR}/system/module_integration_checks.py" \
  --config "${ROOT_DIR}/config/modules.json" \
  --selftests "${ROOT_DIR}/config/module_selftests.json" \
  "${DEBUG_ARGS[@]}"

run_step "Abhängigkeiten prüfen (ohne Auto-Installation)" \
  "Bitte python -m pip install -r config/requirements.txt ausführen." \
  python "${ROOT_DIR}/system/dependency_checker.py" \
  --requirements "${ROOT_DIR}/config/requirements.txt" \
  --no-auto-install \
  "${DEBUG_ARGS[@]}"

echo "System-Scan: abgeschlossen."
