#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_DIR="${ROOT_DIR}/config"

usage() {
  cat <<'USAGE'
Nutzung: ./scripts/run_tests.sh [--help]

Dieses Skript führt automatische Tests (Pytest), Codequalität (Ruff) und
Formatprüfung (Black) aus. Fehlende Abhängigkeiten werden nach Rückfrage
über die Start-Routine automatisch installiert.
USAGE
}

on_error() {
  local exit_code=$?
  echo "Fehler: Tests oder Prüfungen sind fehlgeschlagen." >&2
  echo "Hinweis: Bitte die Fehlermeldung oben prüfen und danach erneut starten." >&2
  exit "${exit_code}"
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

trap on_error ERR

if ! command -v python >/dev/null 2>&1; then
  echo "Fehler: Python ist nicht installiert. Bitte Python installieren, damit Tests laufen können." >&2
  exit 1
fi

if [[ ! -f "${CONFIG_DIR}/requirements.txt" ]]; then
  echo "Fehler: requirements.txt fehlt in config/." >&2
  exit 2
fi

if [[ ! -f "${CONFIG_DIR}/pytest.ini" ]]; then
  echo "Fehler: pytest.ini fehlt in config/." >&2
  exit 2
fi

if [[ ! -f "${CONFIG_DIR}/ruff.toml" ]]; then
  echo "Fehler: ruff.toml fehlt in config/." >&2
  exit 2
fi

if [[ ! -f "${CONFIG_DIR}/black.toml" ]]; then
  echo "Fehler: black.toml fehlt in config/." >&2
  exit 2
fi

echo "Tests: Abhängigkeiten prüfen und ggf. installieren."
python "${ROOT_DIR}/system/dependency_checker.py" --requirements "${CONFIG_DIR}/requirements.txt"

echo "Tests: Pytest wird gestartet."
python -m pytest -c "${CONFIG_DIR}/pytest.ini"

echo "Qualität: Ruff (Linting/Regelprüfung) wird gestartet."
python -m ruff check "${ROOT_DIR}" --config "${CONFIG_DIR}/ruff.toml"

echo "Qualität: Black (Formatprüfung) wird gestartet."
python -m black --check "${ROOT_DIR}" --config "${CONFIG_DIR}/black.toml"

echo "Tests: Erfolgreich abgeschlossen."
