#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v python >/dev/null 2>&1; then
  echo "Fehler: Python ist nicht installiert. Bitte Python installieren, damit Tests laufen können." >&2
  exit 1
fi

if [[ ! -f "${ROOT_DIR}/config/requirements.txt" ]]; then
  echo "Fehler: requirements.txt fehlt in config/." >&2
  exit 2
fi

if [[ ! -f "${ROOT_DIR}/config/pytest.ini" ]]; then
  echo "Fehler: pytest.ini fehlt in config/." >&2
  exit 2
fi

if [[ ! -f "${ROOT_DIR}/config/ruff.toml" ]]; then
  echo "Fehler: ruff.toml fehlt in config/." >&2
  exit 2
fi

if [[ ! -f "${ROOT_DIR}/config/black.toml" ]]; then
  echo "Fehler: black.toml fehlt in config/." >&2
  exit 2
fi

echo "Tests: Abhängigkeiten prüfen und ggf. installieren."
python "${ROOT_DIR}/system/dependency_checker.py" --requirements "${ROOT_DIR}/config/requirements.txt"

echo "Tests: Pytest wird gestartet."
python -m pytest -c "${ROOT_DIR}/config/pytest.ini"

echo "Qualität: Ruff (Linting/Regelprüfung) wird gestartet."
python -m ruff check "${ROOT_DIR}" --config "${ROOT_DIR}/config/ruff.toml"

echo "Qualität: Black (Formatprüfung) wird gestartet."
python -m black --check "${ROOT_DIR}" --config "${ROOT_DIR}/config/black.toml"

echo "Tests: Erfolgreich abgeschlossen."
