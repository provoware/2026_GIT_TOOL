#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DEBUG_MODE=0
LOG_FILE=""
NO_LOG=0

show_help() {
  cat <<'EOF'
Klick&Start (Laienmodus)

Nutzung:
  ./klick_start.sh [--debug] [--log-file <pfad>] [--no-log]

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

if ! command -v python >/dev/null 2>&1; then
  echo "Fehler: Python ist nicht installiert. Bitte Python installieren, damit der Start funktioniert."
  exit 1
fi

if [[ ! -x "${ROOT_DIR}/scripts/start.sh" ]]; then
  echo "Fehler: Start-Routine fehlt oder ist nicht ausführbar: scripts/start.sh"
  echo "Tipp: Ausführbar machen mit: chmod +x scripts/start.sh"
  exit 1
fi

if [[ ! -f "${ROOT_DIR}/config/pin.json" ]]; then
  echo "Fehler: PIN-Konfiguration fehlt: config/pin.json"
  echo "Tipp: Self-Repair starten: python system/self_repair.py --root ."
  exit 1
fi

START_ARGS=()
GUI_ARGS=()
if [[ "${DEBUG_MODE}" -eq 1 ]]; then
  START_ARGS+=(--debug)
  GUI_ARGS+=(--debug)
fi
if [[ -n "${LOG_FILE}" ]]; then
  START_ARGS+=(--log-file "${LOG_FILE}")
fi
if [[ "${NO_LOG}" -eq 1 ]]; then
  START_ARGS+=(--no-log)
fi

echo "Klick&Start: PIN-Check läuft (falls aktiviert)."
python "${ROOT_DIR}/system/pin_auth.py" --config "${ROOT_DIR}/config/pin.json" \
  --state "${ROOT_DIR}/data/pin_state.json" "${GUI_ARGS[@]}"

echo "Klick&Start: Startroutine läuft (automatische Prüfungen + Fortschritt)."
"${ROOT_DIR}/scripts/start.sh" "${START_ARGS[@]}"

echo "Klick&Start: Startübersicht wird geöffnet."
python "${ROOT_DIR}/system/launcher_gui.py" "${GUI_ARGS[@]}"
