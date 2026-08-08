#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${DIST_DIR:-${ROOT_DIR}/dist}"
PACKAGE_NAME="${PACKAGE_NAME:-2026_GIT_TOOL_PRIVAT}"
STAGE_DIR="${DIST_DIR}/${PACKAGE_NAME}"
ZIP_PATH="${DIST_DIR}/${PACKAGE_NAME}.zip"
PYTHON_BIN="${PYTHON_BIN:-python3}"

rm -rf "${STAGE_DIR}" "${ZIP_PATH}"
mkdir -p "${STAGE_DIR}" "${DIST_DIR}"

ROOT_LOGS="$(find "${ROOT_DIR}" -maxdepth 1 -type f \( -name '*.log' -o -name '*.log.*' -o -name '*.trace' -o -name '*.out' \) -print)"
if [[ -n "${ROOT_LOGS}" ]]; then
  echo "Fehler: Protokolldateien im Projekt-Hauptordner gefunden:" >&2
  printf '%s\n' "${ROOT_LOGS}" >&2
  exit 2
fi

rsync -a "${ROOT_DIR}/" "${STAGE_DIR}/" \
  --exclude '.git/' \
  --exclude '.github/' \
  --exclude '.venv/' \
  --exclude 'venv/' \
  --exclude 'node_modules/' \
  --exclude '__pycache__/' \
  --exclude '.pytest_cache/' \
  --exclude '.mypy_cache/' \
  --exclude '.ruff_cache/' \
  --exclude 'build/' \
  --exclude 'dist/' \
  --exclude 'tests/' \
  --exclude '*.pyc' \
  --exclude '*.pyo' \
  --exclude '*.log' \
  --exclude '*.log.*' \
  --exclude '*.trace' \
  --exclude '*.out'

mkdir -p "${STAGE_DIR}/logs"
cp "${ROOT_DIR}/logs/README.md" "${STAGE_DIR}/logs/README.md"
: > "${STAGE_DIR}/logs/.gitkeep"

COMMIT="unbekannt"
if command -v git >/dev/null 2>&1 && git -C "${ROOT_DIR}" rev-parse HEAD >/dev/null 2>&1; then
  COMMIT="$(git -C "${ROOT_DIR}" rev-parse HEAD)"
fi
cat > "${STAGE_DIR}/RELEASE_INFO.txt" <<EOF
2026_GIT_TOOL – private Desktop-Ausgabe
Geprüfter Commit: ${COMMIT}
Erstellt (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)
Start: ./scripts/start.sh
Prüfung: bash scripts/private_tool_check.sh
Hilfe: HILFE.md
Logs: logs/
Nicht enthalten: Git-Metadaten, Tests, Caches und Laufzeitprotokolle
EOF

"${PYTHON_BIN}" -m compileall -q "${STAGE_DIR}/system" "${STAGE_DIR}/modules"
PYTHONPATH="${STAGE_DIR}/system" "${PYTHON_BIN}" "${STAGE_DIR}/system/launcher.py" --help >/dev/null
PYTHONPATH="${STAGE_DIR}/system" "${PYTHON_BIN}" "${STAGE_DIR}/system/private_launcher.py" --help >/dev/null

(
  cd "${DIST_DIR}"
  zip -qr -9 "${PACKAGE_NAME}.zip" "${PACKAGE_NAME}"
)
unzip -t "${ZIP_PATH}" >/dev/null

if unzip -Z1 "${ZIP_PATH}" | grep -E "^${PACKAGE_NAME}/[^/]+\.(log|trace|out)(\.[0-9]+)?$"; then
  echo "Fehler: Das Release-ZIP enthält eine Protokolldatei im Hauptordner." >&2
  exit 3
fi

if unzip -Z1 "${ZIP_PATH}" | grep -E "(^|/)(\.github|__pycache__|\.pytest_cache)(/|$)"; then
  echo "Fehler: Das private Release-ZIP enthält ausgeschlossene Entwicklungsbestandteile." >&2
  exit 4
fi

printf '%s\n' "${ZIP_PATH}"
