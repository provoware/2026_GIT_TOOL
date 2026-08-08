#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

REPORT_DIR="${REPORT_DIR:-${ROOT_DIR}/build/private-tool-check}"
mkdir -p "${REPORT_DIR}"
SUMMARY="${REPORT_DIR}/summary.txt"
: > "${SUMMARY}"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON="${PYTHON_BIN}"
else
  PYTHON="$("${ROOT_DIR}/scripts/ensure_venv.sh" --root "${ROOT_DIR}")"
fi

step() {
  printf '\n[%s] %s\n' "$1" "$2" | tee -a "${SUMMARY}"
}

fail() {
  local status=$?
  printf '\nERGEBNIS: FEHLGESCHLAGEN (Status %s)\n' "${status}" | tee -a "${SUMMARY}" >&2
  exit "${status}"
}
trap fail ERR

step "1/8" "Ablagestruktur und Hauptordner prüfen"
mkdir -p logs
ROOT_LOGS="$(find . -maxdepth 1 -type f \( -name '*.log' -o -name '*.log.*' -o -name '*.trace' -o -name '*.out' \) -print)"
test -z "${ROOT_LOGS}" || {
  echo "Protokolldateien im Hauptordner:" | tee -a "${SUMMARY}" >&2
  printf '%s\n' "${ROOT_LOGS}" | tee -a "${SUMMARY}" >&2
  exit 2
}
test -f logs/README.md

step "2/8" "JSON-Dateien validieren"
"${PYTHON}" - <<'PY' | tee "${REPORT_DIR}/json.txt"
import json
from pathlib import Path

excluded = {'.git', '.venv', 'venv', 'node_modules', 'build', 'dist'}
files = [path for path in Path('.').rglob('*.json') if not any(part in excluded for part in path.parts)]
for path in sorted(files):
    with path.open('r', encoding='utf-8') as handle:
        json.load(handle)
print(f'OK: {len(files)} JSON-Dateien')
PY

step "3/8" "Produktiven Python-Quellbestand kompilieren"
"${PYTHON}" -m compileall -q system modules

step "4/8" "Shell-Syntax und Design-Tokens prüfen"
find scripts -type f -name '*.sh' -print0 | sort -z | xargs -0 -r -n1 bash -n
"${PYTHON}" system/generate_design_tokens.py --check

step "5/8" "Modulverträge prüfen"
"${PYTHON}" system/module_integration_checks.py \
  --config config/modules.json \
  --selftests config/module_selftests.json

step "6/8" "Funktionstests ausführen"
PYTEST=("${PYTHON}" -m pytest -q -c config/pytest.ini)
if [[ -z "${DISPLAY:-}" ]] && command -v xvfb-run >/dev/null 2>&1; then
  PYTEST=(xvfb-run -a "${PYTEST[@]}")
fi
"${PYTEST[@]}" 2>&1 | tee "${REPORT_DIR}/pytest.txt"

step "7/8" "Kritische statische Fehler und Start prüfen"
"${PYTHON}" -m ruff check \
  --select E9,F63,F7,F82 \
  system modules \
  --config config/ruff.toml
PYTHONPATH=system "${PYTHON}" system/launcher.py --help >/dev/null
PYTHONPATH=system "${PYTHON}" system/launcher.py --show-all >"${REPORT_DIR}/launcher-smoke.txt"
PYTHONPATH=system "${PYTHON}" system/private_launcher.py --help >/dev/null

step "8/8" "Privates Release-ZIP bauen und prüfen"
PYTHON_BIN="${PYTHON}" "${ROOT_DIR}/scripts/build_private_release.sh" | tee "${REPORT_DIR}/release-path.txt"

printf '\nERGEBNIS: ALLE PRIVATTOOL-KERNPRÜFUNGEN ERFOLGREICH.\n' | tee -a "${SUMMARY}"
