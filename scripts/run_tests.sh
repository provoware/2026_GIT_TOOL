#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_DIR="${ROOT_DIR}/config"
LOG_DIR="${ROOT_DIR}/logs"
LOG_FILE="${LOG_DIR}/test_run.log"
QUALITY_SCOPE="all"

show_help() {
  cat <<'EOF'
Provoware Memo — Tests und Codequalität

Nutzung:
  ./scripts/run_tests.sh [--startup-gate]

Ohne Option:
  vollständige Test-, Ruff- und Black-Prüfung des gesamten Projekts.

Mit --startup-gate:
  vollständige Funktionstests; branchbezogene kritische Qualitätsprüfung der
  neuen Start-, Vorvalidierungs- und Resolverdateien. Dieser Modus wird von der
  automatischen Startroutine verwendet, damit bestehende projektweite
  Lint-Altlasten nicht als neue Startregression gewertet werden.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --startup-gate)
      QUALITY_SCOPE="startup"
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Fehler: Unbekannte Option: $1" >&2
      exit 2
      ;;
  esac
done

on_error() {
  local exit_code=$?
  echo "Fehler: Tests oder Prüfungen sind fehlgeschlagen." >&2
  echo "Hinweis: Details stehen in logs/test_run.log." >&2
  exit "${exit_code}"
}
trap on_error ERR

if ! command -v python >/dev/null 2>&1 && ! command -v python3 >/dev/null 2>&1; then
  echo "Fehler: Python ist nicht installiert." >&2
  exit 1
fi

PYTHON_BIN="$("${ROOT_DIR}/scripts/ensure_venv.sh" --root "${ROOT_DIR}")"
mkdir -p "${LOG_DIR}"
touch "${LOG_FILE}"
exec > >(tee -a "${LOG_FILE}") 2>&1

for required in requirements.txt pytest.ini ruff.toml black.toml; do
  [[ -f "${CONFIG_DIR}/${required}" ]] || {
    echo "Fehler: ${required} fehlt in config/." >&2
    exit 2
  }
done

echo "Tests: Abhängigkeiten prüfen und gegebenenfalls installieren."
"${PYTHON_BIN}" "${ROOT_DIR}/system/dependency_checker.py" \
  --requirements "${CONFIG_DIR}/requirements.txt"

echo "Tests: Modulverbund-Checks starten."
"${PYTHON_BIN}" "${ROOT_DIR}/system/module_integration_checks.py" \
  --config "${CONFIG_DIR}/modules.json" \
  --selftests "${CONFIG_DIR}/module_selftests.json"

echo "Tests: Vollständige Pytest-Suite starten."
PYTEST_COMMAND=("${PYTHON_BIN}" -m pytest -c "${CONFIG_DIR}/pytest.ini")
if [[ -z "${DISPLAY:-}" ]]; then
  command -v xvfb-run >/dev/null 2>&1 || {
    echo "Fehler: Keine grafische Sitzung und xvfb-run fehlt." >&2
    exit 3
  }
  echo "Tests: Headless-System erkannt; Xvfb wird automatisch verwendet."
  PYTEST_COMMAND=(xvfb-run -a "${PYTEST_COMMAND[@]}")
fi
"${PYTEST_COMMAND[@]}"

if [[ "$QUALITY_SCOPE" == "all" ]]; then
  echo "Qualität: vollständiger projektweiter Ruff-Check."
  "${PYTHON_BIN}" -m ruff check "${ROOT_DIR}" --config "${CONFIG_DIR}/ruff.toml"
  echo "Qualität: vollständiger projektweiter Black-Check."
  "${PYTHON_BIN}" -m black --check "${ROOT_DIR}" --config "${CONFIG_DIR}/black.toml"
else
  CRITICAL_PATHS=(
    system/startup_preflight.py
    system/dependency_checker.py
    system/web_server.py
    system/web_module_bridge.py
    system/module_api_validator.py
    tests/test_startup_preflight.py
    tests/test_dependency_checker_v2.py
    tests/test_web_server.py
    tests/test_web_module_bridge.py
    tests/test_web_ui_contract.py
    tests/test_module_api_validator.py
    tests/test_module_checker.py
    tests/test_datei_manager_window.py
    tests/test_archiv_manager_window.py
  )
  FORMAT_PATHS=(
    system/startup_preflight.py
    system/dependency_checker.py
    system/web_server.py
    system/web_module_bridge.py
    tests/test_startup_preflight.py
    tests/test_dependency_checker_v2.py
    tests/test_web_server.py
    tests/test_web_module_bridge.py
    tests/test_web_ui_contract.py
  )
  echo "Qualität: branchbezogene Syntax- und kritische Ruff-Prüfung."
  "${PYTHON_BIN}" -m py_compile "${CRITICAL_PATHS[@]}"
  "${PYTHON_BIN}" -m ruff check \
    --select E9,F63,F7,F82 \
    "${CRITICAL_PATHS[@]}" \
    --config "${CONFIG_DIR}/ruff.toml"
  echo "Qualität: Black-Prüfung der neuen Start- und Resolverdateien."
  "${PYTHON_BIN}" -m black --diff --check \
    "${FORMAT_PATHS[@]}" \
    --config "${CONFIG_DIR}/black.toml"
fi

echo "Tests: Erfolgreich abgeschlossen."
