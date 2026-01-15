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

Hinweis:
  Der Testlauf nutzt automatisch die Venv (.venv), wenn vorhanden.

Optionen:
  -h, --help  Diese Hilfe anzeigen
EOF
}

CONFIG_DIR="${ROOT_DIR}/config"

on_error() {
  local exit_code=$?
  echo "Fehler: Tests oder Prüfungen sind fehlgeschlagen." >&2
  echo "Hinweis: Details stehen im Fehlerprotokoll (Log) unter logs/test_run.log." >&2
  echo "Tipp: Bitte die Fehlermeldung oben prüfen und danach erneut starten." >&2
  exit "${exit_code}"
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

trap on_error ERR

if ! command -v python >/dev/null 2>&1; then
  echo "Fehler: Python ist nicht installiert. Bitte Python installieren, damit Tests laufen können." >&2
  exit 1
fi

PYTHON_BIN="$("${ROOT_DIR}/scripts/ensure_venv.sh" --root "${ROOT_DIR}")"

mkdir -p "${LOG_DIR}"
touch "${LOG_FILE}"
exec > >(tee -a "${LOG_FILE}") 2>&1

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

echo "Hinweis: Details stehen im Fehlerprotokoll (Log) unter logs/test_run.log."
echo "Tests: Abhängigkeiten prüfen und ggf. installieren."
"${PYTHON_BIN}" "${ROOT_DIR}/system/dependency_checker.py" --requirements "${CONFIG_DIR}/requirements.txt"

echo "Tests: Modulverbund-Checks werden gestartet."
"${PYTHON_BIN}" "${ROOT_DIR}/system/module_integration_checks.py" \
  --config "${CONFIG_DIR}/modules.json" \
  --selftests "${CONFIG_DIR}/module_selftests.json"

echo "Tests: Pytest wird gestartet."
"${PYTHON_BIN}" -m pytest -c "${CONFIG_DIR}/pytest.ini"

echo "Qualität: Ruff (Linting/Regelprüfung) wird gestartet."
"${PYTHON_BIN}" -m ruff check "${ROOT_DIR}" --config "${CONFIG_DIR}/ruff.toml"

echo "Qualität: Black (Formatprüfung) wird gestartet."
"${PYTHON_BIN}" -m black --check "${ROOT_DIR}" --config "${CONFIG_DIR}/black.toml"

echo "Tests: Erfolgreich abgeschlossen."
