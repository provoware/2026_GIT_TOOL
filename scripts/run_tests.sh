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
3) Der Ablauf prüft automatisch Abhängigkeiten, Tests und Codequalität.
4) Headless-Systeme verwenden automatisch Xvfb, sofern keine grafische Sitzung aktiv ist.

Optionen:
  -h, --help  Diese Hilfe anzeigen
EOF
}

CONFIG_DIR="${ROOT_DIR}/config"

on_error() {
  local exit_code=$?
  echo "Fehler: Tests oder Prüfungen sind fehlgeschlagen." >&2
  echo "Hinweis: Details stehen im Fehlerprotokoll unter logs/test_run.log." >&2
  echo "Tipp: Bitte die Fehlermeldung oben prüfen und danach erneut starten." >&2
  exit "${exit_code}"
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

trap on_error ERR

if ! command -v python >/dev/null 2>&1; then
  echo "Fehler: Python ist nicht installiert." >&2
  exit 1
fi

PYTHON_BIN="$("${ROOT_DIR}/scripts/ensure_venv.sh" --root "${ROOT_DIR}")"

mkdir -p "${LOG_DIR}"
touch "${LOG_FILE}"
exec > >(tee -a "${LOG_FILE}") 2>&1

for required in requirements.txt pytest.ini ruff.toml black.toml; do
  if [[ ! -f "${CONFIG_DIR}/${required}" ]]; then
    echo "Fehler: ${required} fehlt in config/." >&2
    exit 2
  fi
done

echo "Hinweis: Details stehen im Fehlerprotokoll unter logs/test_run.log."
echo "Tests: Abhängigkeiten prüfen und ggf. installieren."
"${PYTHON_BIN}" "${ROOT_DIR}/system/dependency_checker.py" \
  --requirements "${CONFIG_DIR}/requirements.txt"

echo "Tests: Modulverbund-Checks werden gestartet."
"${PYTHON_BIN}" "${ROOT_DIR}/system/module_integration_checks.py" \
  --config "${CONFIG_DIR}/modules.json" \
  --selftests "${CONFIG_DIR}/module_selftests.json"

echo "Tests: Pytest wird gestartet."
PYTEST_COMMAND=("${PYTHON_BIN}" -m pytest -c "${CONFIG_DIR}/pytest.ini")
if [[ -z "${DISPLAY:-}" ]]; then
  if ! command -v xvfb-run >/dev/null 2>&1; then
    echo "Fehler: Keine grafische Sitzung und xvfb-run ist nicht installiert." >&2
    exit 3
  fi
  echo "Tests: Keine grafische Sitzung erkannt; Xvfb wird automatisch verwendet."
  PYTEST_COMMAND=(xvfb-run -a "${PYTEST_COMMAND[@]}")
fi
"${PYTEST_COMMAND[@]}"

echo "Qualität: Ruff wird gestartet."
"${PYTHON_BIN}" -m ruff check "${ROOT_DIR}" --config "${CONFIG_DIR}/ruff.toml"

echo "Qualität: Black wird gestartet."
"${PYTHON_BIN}" -m black --check "${ROOT_DIR}" --config "${CONFIG_DIR}/black.toml"

echo "Tests: Erfolgreich abgeschlossen."
