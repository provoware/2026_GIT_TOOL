#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

show_help() {
  cat <<'DOC'
Changelog-Automatik (To-Do archivieren + DONE/CHANGELOG aktualisieren)

Nutzung:
  ./scripts/update_records.sh [--dry-run] [--debug]

Optionen:
  --dry-run   Nur prüfen, nichts schreiben.
  --debug     Ausführliche Diagnoseausgaben.
  -h, --help  Hilfe anzeigen.
DOC
}

DRY_RUN=0
DEBUG_MODE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --debug)
      DEBUG_MODE=1
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Fehler: Unbekannte Option: $1" >&2
      show_help
      exit 2
      ;;
  esac
done

PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  if ! PYTHON_BIN="$("${ROOT_DIR}/scripts/ensure_venv.sh" --root "${ROOT_DIR}")"; then
    echo "Fehler: Venv konnte nicht bereitgestellt werden." >&2
    exit 1
  fi
fi

ARGS=("${ROOT_DIR}/src/records/record_updater.py")
if [[ "${DRY_RUN}" -eq 1 ]]; then
  ARGS+=(--dry-run)
fi
if [[ "${DEBUG_MODE}" -eq 1 ]]; then
  ARGS+=(--debug)
fi

"${PYTHON_BIN}" "${ARGS[@]}"
