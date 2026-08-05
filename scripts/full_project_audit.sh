#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
REPORT_DIR="${REPORT_DIR:-build/full-project-audit}"
mkdir -p "$REPORT_DIR"

printf '2026_GIT_TOOL – Vollständiger Projekt-Audit\n' | tee "$REPORT_DIR/summary.txt"
printf 'Commit: %s\n' "$(git rev-parse HEAD)" | tee -a "$REPORT_DIR/summary.txt"
printf 'UTC: %s\n\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$REPORT_DIR/summary.txt"

printf '[1/8] Repository-Zustand prüfen\n' | tee -a "$REPORT_DIR/summary.txt"
git diff --check | tee "$REPORT_DIR/git-diff-check.txt"

printf '[2/8] JSON-Dateien validieren\n' | tee -a "$REPORT_DIR/summary.txt"
"$PYTHON_BIN" - <<'PY' | tee "$REPORT_DIR/json-validation.txt"
import json
from pathlib import Path

excluded = {'.git', '.venv', 'venv', 'node_modules', 'build', 'dist'}
files = [
    path for path in Path('.').rglob('*.json')
    if not any(part in excluded for part in path.parts)
]
for path in sorted(files):
    with path.open('r', encoding='utf-8') as handle:
        json.load(handle)
print(f'OK: {len(files)} JSON-Dateien validiert.')
PY

printf '[3/8] Python-Quellbestand kompilieren\n' | tee -a "$REPORT_DIR/summary.txt"
"$PYTHON_BIN" - <<'PY' | tee "$REPORT_DIR/python-compile.txt"
import py_compile
from pathlib import Path

excluded = {'.git', '.venv', 'venv', 'node_modules', 'build', 'dist'}
files = [
    path for path in Path('.').rglob('*.py')
    if not any(part in excluded for part in path.parts)
]
for path in sorted(files):
    py_compile.compile(str(path), doraise=True)
print(f'OK: {len(files)} Python-Dateien kompiliert.')
PY

printf '[4/8] Shell-Skripte syntaktisch prüfen\n' | tee -a "$REPORT_DIR/summary.txt"
find . -type f -name '*.sh' \
  -not -path './.git/*' -not -path './.venv/*' -not -path './venv/*' \
  -not -path './node_modules/*' -not -path './build/*' -not -path './dist/*' \
  -print0 | sort -z | xargs -0 -r -n1 bash -n
printf 'OK: Shell-Syntax gültig.\n' | tee "$REPORT_DIR/shell-syntax.txt"

printf '[5/8] Vollständige vorhandene Tests ausführen\n' | tee -a "$REPORT_DIR/summary.txt"
if [[ -x scripts/run_tests.sh ]]; then
  bash scripts/run_tests.sh 2>&1 | tee "$REPORT_DIR/test-run.txt"
else
  "$PYTHON_BIN" -m pytest -q 2>&1 | tee "$REPORT_DIR/test-run.txt"
fi

printf '[6/8] Release-Regressionssuite ausführen\n' | tee -a "$REPORT_DIR/summary.txt"
if [[ -f scripts/run_latest_release_tests.sh ]]; then
  bash scripts/run_latest_release_tests.sh 2>&1 | tee "$REPORT_DIR/release-regressions.txt"
else
  printf 'Nicht vorhanden – übersprungen.\n' | tee "$REPORT_DIR/release-regressions.txt"
fi

printf '[7/8] End-Audit ausführen\n' | tee -a "$REPORT_DIR/summary.txt"
if [[ -f system/end_audit.py ]]; then
  "$PYTHON_BIN" system/end_audit.py 2>&1 | tee "$REPORT_DIR/end-audit.txt"
else
  printf 'Nicht vorhanden – übersprungen.\n' | tee "$REPORT_DIR/end-audit.txt"
fi

printf '[8/8] Projektinventar erzeugen\n' | tee -a "$REPORT_DIR/summary.txt"
"$PYTHON_BIN" - <<'PY' | tee "$REPORT_DIR/inventory.txt"
from pathlib import Path
from collections import Counter

excluded = {'.git', '.venv', 'venv', 'node_modules', 'build', 'dist', '__pycache__'}
files = [
    path for path in Path('.').rglob('*')
    if path.is_file() and not any(part in excluded for part in path.parts)
]
extensions = Counter(path.suffix.lower() or '<ohne Endung>' for path in files)
print(f'Dateien gesamt: {len(files)}')
for suffix, count in sorted(extensions.items(), key=lambda item: (-item[1], item[0])):
    print(f'{suffix}: {count}')
PY

printf '\nERGEBNIS: ALLE AUTOMATISCHEN PRÜFUNGEN ERFOLGREICH.\n' | tee -a "$REPORT_DIR/summary.txt"
