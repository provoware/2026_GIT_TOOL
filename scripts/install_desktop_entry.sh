#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

show_help() {
  cat <<'DOC'
Desktop-Entry installieren (Linux)

Nutzung:
  ./scripts/install_desktop_entry.sh [--debug]

Optionen:
  --debug     Ausführliche Diagnoseausgaben.
  -h, --help  Hilfe anzeigen.
DOC
}

DEBUG_MODE=0

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

ARGS=("${ROOT_DIR}/system/desktop_entry.py" --install --install-icon)
if [[ "${DEBUG_MODE}" -eq 1 ]]; then
  ARGS+=(--debug)
fi

"${PYTHON_BIN}" "${ARGS[@]}"
