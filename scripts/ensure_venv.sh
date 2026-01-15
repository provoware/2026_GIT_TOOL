#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ALLOW_CREATE=1
QUIET=0

show_help() {
  cat <<'EOF'
Virtuelle Umgebung vorbereiten (Venv = isolierte Python-Umgebung)

Nutzung:
  ./scripts/ensure_venv.sh [--root <pfad>] [--no-create] [--quiet]

Optionen:
  --root <pfad>   Projektwurzel festlegen (Standard: Repo-Root).
  --no-create     Keine neue Venv anlegen (nur nutzen, falls vorhanden).
  --quiet         Keine Statusausgaben (nur Python-Pfad ausgeben).
  -h, --help      Hilfe anzeigen.

Ausgabe:
  Gibt den Pfad zum Python-Interpreter (Venv oder System) aus.
EOF
}

log_info() {
  if [[ "${QUIET}" -eq 0 ]]; then
    echo "$@" >&2
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      if [[ -z "${2:-}" ]]; then
        echo "Fehler: --root braucht einen Pfad." >&2
        exit 2
      fi
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

if ! command -v python >/dev/null 2>&1; then
  echo "Fehler: Python ist nicht installiert. Bitte Python installieren." >&2
  exit 1
fi

VENV_DIR="${ROOT_DIR}/.venv"
VENV_PYTHON="${VENV_DIR}/bin/python"

if [[ -x "${VENV_PYTHON}" ]]; then
  log_info "Venv: Bereits vorhanden (${VENV_DIR})."
  echo "${VENV_PYTHON}"
  exit 0
fi

if [[ "${ALLOW_CREATE}" -eq 0 ]]; then
  log_info "Venv: Nicht vorhanden, nutze System-Python."
  command -v python
  exit 0
fi

log_info "Venv: Erstelle neue virtuelle Umgebung in ${VENV_DIR}."
python -m venv "${VENV_DIR}"

if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "Fehler: Venv konnte nicht erstellt werden (${VENV_PYTHON} fehlt)." >&2
  exit 1
fi

if ! "${VENV_PYTHON}" -m pip --version >/dev/null 2>&1; then
  echo "Fehler: Pip ist in der Venv nicht verfügbar." >&2
  exit 1
fi

log_info "Venv: Bereit (${VENV_DIR})."
echo "${VENV_PYTHON}"
