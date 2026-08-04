#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ALLOW_CREATE=1
QUIET=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      [[ -n "${2:-}" ]] || { echo "Fehler: --root braucht einen Pfad." >&2; exit 2; }
      ROOT_DIR="$(cd "$2" && pwd)"
      shift 2
      ;;
    --no-create)
      ALLOW_CREATE=0
      shift
      ;;
    --quiet)
      QUIET=1
      shift
      ;;
    *)
      echo "Fehler: Unbekannte Option: $1" >&2
      exit 2
      ;;
  esac
done

log_info() {
  [[ "$QUIET" -eq 1 ]] || echo "$*" >&2
}

find_python() {
  local candidate
  for candidate in "${PROVOWARE_PYTHON:-}" python3 python; do
    [[ -n "$candidate" ]] || continue
    if command -v "$candidate" >/dev/null 2>&1 \
      && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
      command -v "$candidate"
      return 0
    fi
  done
  return 1
}

BASE_PYTHON="$(find_python || true)"
if [[ -z "$BASE_PYTHON" ]]; then
  echo "Fehler: Python >= 3.10 wurde nicht gefunden." >&2
  exit 10
fi

VENV_DIR="${ROOT_DIR}/.venv"
VENV_PYTHON="${VENV_DIR}/bin/python"

venv_healthy() {
  [[ -x "$VENV_PYTHON" ]] \
    && "$VENV_PYTHON" -c 'import sys, venv; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1
}

if venv_healthy; then
  if ! "$VENV_PYTHON" -m pip --version >/dev/null 2>&1; then
    "$VENV_PYTHON" -m ensurepip --upgrade >/dev/null
  fi
  log_info "Venv: geprüft und wiederverwendet (${VENV_DIR})."
  echo "$VENV_PYTHON"
  exit 0
fi

if [[ -e "$VENV_DIR" ]]; then
  if [[ "$ALLOW_CREATE" -eq 0 ]]; then
    log_info "Venv: beschädigt; Safe-Mode nutzt System-Python."
    echo "$BASE_PYTHON"
    exit 0
  fi
  backup="${VENV_DIR}.broken.$(date +%Y%m%d%H%M%S)"
  mv "$VENV_DIR" "$backup"
  log_info "Venv: beschädigter Stand gesichert: ${backup}"
fi

if [[ "$ALLOW_CREATE" -eq 0 ]]; then
  log_info "Venv: nicht vorhanden; System-Python wird geprüft."
  echo "$BASE_PYTHON"
  exit 0
fi

log_info "Venv: wird mit ${BASE_PYTHON} erstellt."
"$BASE_PYTHON" -m venv "$VENV_DIR"

if ! venv_healthy; then
  echo "Fehler: Venv konnte nicht funktionsfähig erstellt werden." >&2
  exit 11
fi

if ! "$VENV_PYTHON" -m pip --version >/dev/null 2>&1; then
  "$VENV_PYTHON" -m ensurepip --upgrade
fi
"$VENV_PYTHON" -m pip --version >/dev/null

log_info "Venv: erfolgreich erstellt und Pip nachvalidiert."
echo "$VENV_PYTHON"
