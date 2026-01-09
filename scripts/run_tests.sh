#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
LOG_FILE="${LOG_DIR}/test_run.log"

show_help() {
  cat <<'EOF'
Tests starten (Wizard = geführter Ablauf)

Schritt-für-Schritt:
1) Voraussetzung prüfen: Python installieren (Programmiersprache).
2) Im Projektordner ausführen: ./scripts/run_tests.sh
3) Der Ablauf prüft automatisch:
   - Abhängigkeiten (Dependencies = benötigte Pakete)
   - Tests (Pytest = Testlauf)
   - Codequalität (Linting = Regelprüfung)
   - Codeformat (Formatierung = einheitlicher Stil)
4) Nach dem Lauf sehen Sie:
   - "Erfolgreich abgeschlossen" bei Erfolg
   - Bei Fehlern: Details im Fehlerprotokoll (Log) unter logs/test_run.log

Optionen:
  -h, --help  Diese Hilfe anzeigen
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  show_help
  exit 0
fi

if ! command -v python >/dev/null 2>&1; then
  echo "Fehler: Python ist nicht installiert. Bitte Python installieren, damit Tests laufen können." >&2
  exit 1
fi

mkdir -p "${LOG_DIR}"
touch "${LOG_FILE}"
exec > >(tee -a "${LOG_FILE}") 2>&1

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

echo "Hinweis: Details stehen im Fehlerprotokoll (Log) unter logs/test_run.log."
echo "Tests: Abhängigkeiten prüfen und ggf. installieren."
python "${ROOT_DIR}/system/dependency_checker.py" --requirements "${ROOT_DIR}/config/requirements.txt"

echo "Tests: Pytest wird gestartet."
python -m pytest -c "${ROOT_DIR}/config/pytest.ini"

echo "Qualität: Ruff (Linting/Regelprüfung) wird gestartet."
python -m ruff check "${ROOT_DIR}" --config "${ROOT_DIR}/config/ruff.toml"

echo "Qualität: Black (Formatprüfung) wird gestartet."
python -m black --check "${ROOT_DIR}" --config "${ROOT_DIR}/config/black.toml"

echo "Tests: Erfolgreich abgeschlossen."
