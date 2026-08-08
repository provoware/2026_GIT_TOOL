#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PRODUCT_NAME="Provoware Memo"
DEBUG_MODE=0
PREFLIGHT_ONLY=0
NO_LOG=0
LOG_FILE=""

usage() {
  cat <<'EOF'
Provoware Memo — schneller Privatstart

Nutzung: ./scripts/start.sh [Optionen]

  --debug           zusätzliche GUI-Diagnoseausgaben
  --preflight-only  nur Minimal-Preflight ausführen, GUI nicht starten
  --test-mode       Alias für --preflight-only
  --safe-mode       Alias für --preflight-only
  --no-start        Alias für --preflight-only
  --log-file PFAD   eigenes Startprotokoll verwenden
  --no-log          kein Startprotokoll schreiben
  -h, --help        diese Hilfe anzeigen

Die vollständige Toolprüfung und das Privat-ZIP werden bewusst nicht beim Start
 ausgeführt. Dafür in der GUI „Diagnose starten“ bzw. Alt+G verwenden.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --debug)
      DEBUG_MODE=1
      shift
      ;;
    --preflight-only|--test-mode|--safe-mode|--no-start)
      PREFLIGHT_ONLY=1
      shift
      ;;
    --log-file)
      [[ -n "${2:-}" ]] || { echo "--log-file braucht einen Pfad" >&2; exit 2; }
      LOG_FILE="$2"
      shift 2
      ;;
    --no-log)
      NO_LOG=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unbekannte Option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

required_files=(
  config/modules.json
  config/launcher_gui.json
  config/requirements.txt
  scripts/ensure_venv.sh
  scripts/private_tool_check.sh
  system/launcher_gui.py
)

for item in "${required_files[@]}"; do
  [[ -f "$ROOT_DIR/$item" ]] || {
    echo "$PRODUCT_NAME: Kerndatei fehlt: $item" >&2
    echo "$PRODUCT_NAME: Bitte Projektstand prüfen oder erneut git pull ausführen." >&2
    exit 12
  }
done

mkdir -p logs data dist build

if [[ "$NO_LOG" -eq 0 ]]; then
  [[ -n "$LOG_FILE" ]] || LOG_FILE="$ROOT_DIR/logs/start_run.log"
  mkdir -p "$(dirname "$LOG_FILE")"
  touch "$LOG_FILE"
  exec > >(tee -a "$LOG_FILE") 2>&1
fi

echo "$PRODUCT_NAME: Minimal-Preflight startet."

SYSTEM_PYTHON=""
for candidate in "${PROVOWARE_PYTHON:-}" python3 python; do
  [[ -n "$candidate" ]] || continue
  if command -v "$candidate" >/dev/null 2>&1 \
    && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
    SYSTEM_PYTHON="$(command -v "$candidate")"
    break
  fi
done

if [[ -z "$SYSTEM_PYTHON" ]]; then
  echo "$PRODUCT_NAME: Python >= 3.10 fehlt." >&2
  echo "$PRODUCT_NAME: Keine automatische Systeminstallation beim normalen Start." >&2
  exit 10
fi

export PROVOWARE_PYTHON="$SYSTEM_PYTHON"
PYTHON_BIN="$("$ROOT_DIR/scripts/ensure_venv.sh" --root "$ROOT_DIR")"
[[ -x "$PYTHON_BIN" ]] || {
  echo "$PRODUCT_NAME: virtuelle Python-Umgebung ist nicht startfähig." >&2
  exit 11
}

"$PYTHON_BIN" -c 'import tkinter, sqlite3' >/dev/null 2>&1 || {
  echo "$PRODUCT_NAME: Tkinter oder SQLite fehlt." >&2
  echo "$PRODUCT_NAME: Bitte Systemabhängigkeit installieren; der Start verändert keine Systempakete automatisch." >&2
  exit 13
}

export PYTHONPATH="$ROOT_DIR/system${PYTHONPATH:+:$PYTHONPATH}"

echo "$PRODUCT_NAME: Minimal-Preflight erfolgreich."
echo "$PRODUCT_NAME: Vollprüfung und Privat-ZIP: Diagnose starten / Alt+G."

if [[ "$PREFLIGHT_ONLY" -eq 1 ]]; then
  exit 0
fi

GUI_ARGS=()
[[ "$DEBUG_MODE" -eq 0 ]] || GUI_ARGS+=(--debug)

exec "$PYTHON_BIN" "$ROOT_DIR/system/launcher_gui.py" "${GUI_ARGS[@]}"
