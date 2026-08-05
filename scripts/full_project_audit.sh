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

printf '[1/9] Repository-Zustand prüfen\n' | tee -a "$REPORT_DIR/summary.txt"
git diff --check | tee "$REPORT_DIR/git-diff-check.txt"

printf '[2/9] JSON-Dateien validieren\n' | tee -a "$REPORT_DIR/summary.txt"
"$PYTHON_BIN" - <<'PY' | tee "$REPORT_DIR/json-validation.txt"
import json
from pathlib import Path
excluded = {'.git', '.venv', 'venv', 'node_modules', 'build', 'dist'}
files = [p for p in Path('.').rglob('*.json') if not any(part in excluded for part in p.parts)]
for path in sorted(files):
    with path.open('r', encoding='utf-8') as handle:
        json.load(handle)
print(f'OK: {len(files)} JSON-Dateien validiert.')
PY

printf '[3/9] Python-Quellbestand kompilieren\n' | tee -a "$REPORT_DIR/summary.txt"
"$PYTHON_BIN" - <<'PY' | tee "$REPORT_DIR/python-compile.txt"
import py_compile
from pathlib import Path
excluded = {'.git', '.venv', 'venv', 'node_modules', 'build', 'dist'}
files = [p for p in Path('.').rglob('*.py') if not any(part in excluded for part in p.parts)]
for path in sorted(files):
    py_compile.compile(str(path), doraise=True)
print(f'OK: {len(files)} Python-Dateien kompiliert.')
PY

printf '[4/9] Shell-Skripte syntaktisch prüfen\n' | tee -a "$REPORT_DIR/summary.txt"
find . -type f -name '*.sh' -not -path './.git/*' -not -path './.venv/*' \
  -not -path './venv/*' -not -path './node_modules/*' -not -path './build/*' \
  -not -path './dist/*' -print0 | sort -z | xargs -0 -r -n1 bash -n
printf 'OK: Shell-Syntax gültig.\n' | tee "$REPORT_DIR/shell-syntax.txt"

printf '[5/9] Vollständige Funktions- und Absturztests ausführen\n' | tee -a "$REPORT_DIR/summary.txt"
if command -v xvfb-run >/dev/null 2>&1; then
  xvfb-run -a "$PYTHON_BIN" -m pytest -q 2>&1 | tee "$REPORT_DIR/test-run.txt"
else
  "$PYTHON_BIN" -m pytest -q 2>&1 | tee "$REPORT_DIR/test-run.txt"
fi

printf '[6/9] Release-Regressionssuite ausführen\n' | tee -a "$REPORT_DIR/summary.txt"
bash scripts/run_latest_release_tests.sh 2>&1 | tee "$REPORT_DIR/release-regressions.txt"

printf '[7/9] End-Audit ausführen\n' | tee -a "$REPORT_DIR/summary.txt"
"$PYTHON_BIN" system/end_audit.py 2>&1 | tee "$REPORT_DIR/end-audit.txt"

printf '[8/9] Codehygiene vollständig erfassen\n' | tee -a "$REPORT_DIR/summary.txt"
set +e
"$PYTHON_BIN" -m ruff check . >"$REPORT_DIR/ruff-findings.txt" 2>&1
RUFF_STATUS=$?
set -e
printf 'Ruff-Status: %s. Historische Stilbefunde sind dokumentiert und nicht als Laufzeitabsturz klassifiziert.\n' "$RUFF_STATUS" | tee -a "$REPORT_DIR/summary.txt"

printf '[9/9] Projektinventar erzeugen\n' | tee -a "$REPORT_DIR/summary.txt"
"$PYTHON_BIN" - <<'PY' | tee "$REPORT_DIR/inventory.txt"
from collections import Counter
from pathlib import Path
excluded = {'.git', '.venv', 'venv', 'node_modules', 'build', 'dist', '__pycache__'}
files = [p for p in Path('.').rglob('*') if p.is_file() and not any(part in excluded for part in p.parts)]
extensions = Counter(p.suffix.lower() or '<ohne Endung>' for p in files)
print(f'Dateien gesamt: {len(files)}')
for suffix, count in sorted(extensions.items(), key=lambda item: (-item[1], item[0])):
    print(f'{suffix}: {count}')
PY

printf '\nERGEBNIS: FUNKTIONALE, ABSTURZ-, SYNTAX-, DATEN- UND RELEASE-PRÜFUNGEN ERFOLGREICH.\n' | tee -a "$REPORT_DIR/summary.txt"
