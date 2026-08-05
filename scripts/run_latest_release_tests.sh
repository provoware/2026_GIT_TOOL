#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

"$PYTHON_BIN" -m pytest -q \
  tests/test_latest_release_regressions.py \
  tests/test_workspace_geometry.py \
  tests/test_module_lifecycle.py \
  tests/test_module_manager.py \
  tests/test_module_history.py \
  tests/test_datei_manager_browser.py \
  tests/test_datei_manager_entry.py

"$PYTHON_BIN" -m py_compile \
  system/module_history.py \
  system/module_manager.py \
  system/module_lifecycle.py \
  system/workspace_geometry.py \
  system/main_window.py \
  modules/datei_manager/browser.py

git diff --check

echo "Release-Regressionsprüfung erfolgreich abgeschlossen."
