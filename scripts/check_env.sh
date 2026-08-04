#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

show_help() {
  cat <<'EOF'
Provoware Memo — Umgebungsprüfung

Nutzung:
  ./scripts/check_env.sh

Geprüft werden:
  - Python ab Version 3.10
  - ausführbare Start-Routine
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

find_python() {
  local candidate
  for candidate in "${PROVOWARE_PYTHON:-}" python3 python; do
    [[ -n "$candidate" ]] || continue
    if command -v "$candidate" >/dev/null 2>&1 \
      && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
      command -v "$candidate"
      return 0
    fi
  done
  return 1
}

PYTHON_BIN="$(find_python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  echo "Fehler: Python ab Version 3.10 ist nicht verfügbar." >&2
  exit 1
fi

if [[ ! -x "${ROOT_DIR}/scripts/start.sh" ]]; then
  echo "Fehler: Start-Routine fehlt oder ist nicht ausführbar: scripts/start.sh" >&2
  exit 1
fi

echo "Umgebungs-Check: OK — ${PYTHON_BIN} ($("$PYTHON_BIN" --version 2>&1))."
