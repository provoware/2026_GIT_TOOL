#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
PRODUCT_NAME="Provoware Memo"
DEBUG_MODE=0
NO_LOG=0
SAFE_MODE=0
SANDBOX_MODE=0
PREFLIGHT_ONLY=0
NO_START=0
NO_BROWSER=0
STRICT_PORT=0
WEB_HOST=""
WEB_PORT=""
WEB_MAX_PORT=""
LOG_FILE=""

usage() {
  cat <<'EOF'
Provoware Memo — automatische Start-, Prüf- und Reparaturroutine

Nutzung: ./scripts/start.sh [Optionen]
  --debug           ausführliche Diagnosen
  --log-file PFAD   eigenes Startprotokoll
  --no-log          kein Dateiprotokoll
  --safe-mode       nur prüfen, nicht reparieren oder starten
  --sandbox         vollständige isolierte Projektkopie verwenden
  --preflight-only  Vorvalidierung einschließlich Systemabhängigkeiten
  --no-start        vollständig prüfen und reparieren, Server nicht starten
  --no-browser      Server starten, Browser nicht automatisch öffnen
  --host ADRESSE    Loopback-Adresse überschreiben
  --port NUMMER     bevorzugten lokalen Port überschreiben
  --max-port NUMMER letzten erlaubten Ersatzport festlegen
  --strict-port     bei belegtem Wunschport abbrechen statt Ersatzport zu nutzen
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --debug) DEBUG_MODE=1; shift ;;
    --log-file)
      [[ -n "${2:-}" ]] || { echo "--log-file braucht einen Pfad" >&2; exit 2; }
      LOG_FILE="$2"
      shift 2
      ;;
    --no-log) NO_LOG=1; shift ;;
    --safe-mode|--ghost-mode|--test-mode) SAFE_MODE=1; shift ;;
    --sandbox) SANDBOX_MODE=1; shift ;;
    --preflight-only) PREFLIGHT_ONLY=1; shift ;;
    --no-start) NO_START=1; shift ;;
    --no-browser) NO_BROWSER=1; shift ;;
    --strict-port) STRICT_PORT=1; shift ;;
    --host)
      [[ -n "${2:-}" ]] || { echo "--host braucht eine Loopback-Adresse" >&2; exit 2; }
      WEB_HOST="$2"
      shift 2
      ;;
    --port)
      [[ -n "${2:-}" ]] || { echo "--port braucht eine Nummer" >&2; exit 2; }
      WEB_PORT="$2"
      shift 2
      ;;
    --max-port)
      [[ -n "${2:-}" ]] || { echo "--max-port braucht eine Nummer" >&2; exit 2; }
      WEB_MAX_PORT="$2"
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unbekannte Option: $1" >&2; usage; exit 2 ;;
  esac
done

required_files=(
  config/product.json config/modules.json config/launcher_gui.json
  config/requirements.txt config/test_gate.json config/web_server.json
  scripts/start.sh scripts/ensure_venv.sh scripts/check_env.sh scripts/bootstrap.sh
  scripts/run_tests.sh system/startup_preflight.py system/dependency_checker.py
  system/web_server.py web/index.html web/app.js web/styles.css
  system/launcher_gui.py system/pin_auth.py system/structure_checker.py
  system/self_repair.py system/health_check.py system/json_validator.py
  system/filename_fixer.py system/todo_manager.py
  system/module_integration_checks.py system/test_gate.py
  modules/archiv_manager/manifest.json
)
missing=()
for item in "${required_files[@]}"; do
  [[ -f "$ROOT_DIR/$item" ]] || missing+=("$item")
done
if (( ${#missing[@]} )); then
  echo "$PRODUCT_NAME: unvollständiger Projektordner; Start vor jeder Installation abgebrochen." >&2
  printf 'Fehlende Kerndatei: %s\n' "${missing[@]}" >&2
  exit 12
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

run_privileged() {
  if [[ "$EUID" -eq 0 ]]; then
    "$@"
    return
  fi
  command -v sudo >/dev/null 2>&1 || return 1
  sudo -n true >/dev/null 2>&1 || return 1
  sudo -n "$@"
}

install_system_runtime_packages() {
  [[ "${PROVOWARE_AUTO_SYSTEM_INSTALL:-1}" == "1" ]] || return 1
  if command -v apt-get >/dev/null 2>&1; then
    run_privileged env DEBIAN_FRONTEND=noninteractive apt-get update \
      && run_privileged env DEBIAN_FRONTEND=noninteractive apt-get install -y \
        python3 python3-venv python3-pip python3-tk xvfb xauth
  elif command -v dnf >/dev/null 2>&1; then
    run_privileged dnf install -y \
      python3 python3-pip python3-tkinter xorg-x11-server-Xvfb xorg-x11-xauth
  elif command -v yum >/dev/null 2>&1; then
    run_privileged yum install -y \
      python3 python3-pip python3-tkinter xorg-x11-server-Xvfb xorg-x11-xauth
  elif command -v pacman >/dev/null 2>&1; then
    run_privileged pacman -Sy --noconfirm python python-pip tk xorg-server-xvfb xorg-xauth
  elif command -v zypper >/dev/null 2>&1; then
    run_privileged zypper --non-interactive install \
      python3 python3-pip python3-tk xorg-x11-server-Xvfb xauth
  elif command -v apk >/dev/null 2>&1; then
    run_privileged apk add python3 py3-pip py3-virtualenv tk xvfb-run xauth
  else
    return 1
  fi
}

probe_system_runtime() {
  local missing_runtime=()
  "$SYSTEM_PYTHON" -c 'import venv, ensurepip' >/dev/null 2>&1 \
    || missing_runtime+=("Python-Venv/ensurepip")
  "$SYSTEM_PYTHON" -c 'import sqlite3' >/dev/null 2>&1 \
    || missing_runtime+=("SQLite")
  "$SYSTEM_PYTHON" -c 'import tkinter' >/dev/null 2>&1 \
    || missing_runtime+=("Tkinter")
  if [[ -z "${DISPLAY:-}" ]] && ! command -v xvfb-run >/dev/null 2>&1; then
    missing_runtime+=("Xvfb")
  fi
  printf '%s\n' "${missing_runtime[@]}"
}

SYSTEM_PYTHON="$(find_python || true)"
if [[ -z "$SYSTEM_PYTHON" ]]; then
  echo "$PRODUCT_NAME: Python >= 3.10 fehlt; sichere nichtinteraktive Installation wird versucht."
  install_system_runtime_packages || {
    echo "$PRODUCT_NAME: Python konnte ohne Passwortdialog nicht installiert werden." >&2
    exit 10
  }
  SYSTEM_PYTHON="$(find_python || true)"
fi
[[ -n "$SYSTEM_PYTHON" ]] || exit 10
export PROVOWARE_PYTHON="$SYSTEM_PYTHON"

mkdir -p data/runtime
"$SYSTEM_PYTHON" system/startup_preflight.py \
  --root "$ROOT_DIR" \
  --report "$ROOT_DIR/data/runtime/preflight_report.json" || exit $?

if [[ "$SANDBOX_MODE" -eq 1 ]]; then
  SANDBOX_ROOT="$(mktemp -d -t provoware_memo_sandbox_XXXXXX)"
  cp -a "$ROOT_DIR/." "$SANDBOX_ROOT/"
  rm -rf "$SANDBOX_ROOT/.git" "$SANDBOX_ROOT/.venv"
  ROOT_DIR="$SANDBOX_ROOT"
  cd "$ROOT_DIR"
  echo "$PRODUCT_NAME: Sandbox aktiv: $ROOT_DIR"
  "$SYSTEM_PYTHON" system/startup_preflight.py \
    --root "$ROOT_DIR" \
    --report "$ROOT_DIR/data/runtime/preflight_report.json" || exit $?
fi

if [[ "$SAFE_MODE" -eq 1 ]]; then
  NO_LOG=1
  export GENREARCHIV_WRITE_MODE=read-only
else
  export GENREARCHIV_WRITE_MODE=normal
fi

if [[ "$NO_LOG" -eq 0 ]]; then
  [[ -n "$LOG_FILE" ]] || LOG_FILE="$ROOT_DIR/logs/start_run.log"
  mkdir -p "$(dirname "$LOG_FILE")"
  touch "$LOG_FILE"
  exec > >(tee -a "$LOG_FILE") 2>&1
fi

echo "$PRODUCT_NAME: Projektordner: $ROOT_DIR"
echo "$PRODUCT_NAME: strukturelle Vorvalidierung bestanden."

DEBUG_ARGS=()
[[ "$DEBUG_MODE" -eq 0 ]] || DEBUG_ARGS=(--debug)
FAILURES=()
STEP=0
TOTAL=17
progress() {
  STEP=$((STEP + 1))
  echo "$PRODUCT_NAME [$STEP/$TOTAL]: $1"
}
run_required() {
  local label="$1"
  shift
  "$@"
  local code=$?
  if [[ "$code" -ne 0 ]]; then
    FAILURES+=("$label (Exit-Code $code)")
    echo "$PRODUCT_NAME: FEHLER — $label (Exit-Code $code)."
  fi
}

progress "Systemabhängigkeiten vorprüfen und erforderlichenfalls reparieren"
RUNTIME_MISSING="$(probe_system_runtime)"
if [[ -n "$RUNTIME_MISSING" ]]; then
  echo "$PRODUCT_NAME: fehlende Systemkomponenten:"
  printf ' - %s\n' $RUNTIME_MISSING
  if [[ "$SAFE_MODE" -eq 1 || "$PREFLIGHT_ONLY" -eq 1 ]]; then
    echo "$PRODUCT_NAME: Prüfmodus verändert keine Systempakete." >&2
    exit 13
  fi
  echo "$PRODUCT_NAME: automatische Systemreparatur wird ausgeführt."
  install_system_runtime_packages || {
    echo "$PRODUCT_NAME: Systemabhängigkeiten konnten ohne Nutzerinteraktion nicht installiert werden." >&2
    exit 13
  }
  SYSTEM_PYTHON="$(find_python || true)"
  [[ -n "$SYSTEM_PYTHON" ]] || exit 10
  export PROVOWARE_PYTHON="$SYSTEM_PYTHON"
  RUNTIME_MISSING="$(probe_system_runtime)"
  if [[ -n "$RUNTIME_MISSING" ]]; then
    echo "$PRODUCT_NAME: Nachvalidierung der Systemabhängigkeiten fehlgeschlagen:" >&2
    printf ' - %s\n' $RUNTIME_MISSING >&2
    exit 13
  fi
fi
echo "$PRODUCT_NAME: Python-Venv, SQLite, Tkinter und erforderliche Anzeigehilfe sind verfügbar."
[[ "$PREFLIGHT_ONLY" -eq 0 ]] || exit 0

progress "Venv und Pip prüfen/reparieren"
VENV_ARGS=(--root "$ROOT_DIR")
[[ "$SAFE_MODE" -eq 0 ]] || VENV_ARGS+=(--no-create)
PYTHON_BIN="$(PROVOWARE_PYTHON="$SYSTEM_PYTHON" scripts/ensure_venv.sh "${VENV_ARGS[@]}")" || exit $?
[[ -x "$PYTHON_BIN" ]] || {
  echo "$PRODUCT_NAME: ungültiger Venv-Interpreter" >&2
  exit 11
}
export PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}"

progress "Alle deklarierten Pakete auflösen und importseitig prüfen"
DEP_ARGS=(
  --requirements config/requirements.txt
  --report data/runtime/dependency_report.json
)
[[ "$SAFE_MODE" -eq 0 ]] || DEP_ARGS+=(--check-only)
run_required "Abhängigkeitsauflösung" \
  "$PYTHON_BIN" system/dependency_checker.py "${DEP_ARGS[@]}" "${DEBUG_ARGS[@]}"

progress "Systemumgebung nachprüfen"
run_required "Umgebungsprüfung" scripts/check_env.sh

progress "PIN und Bootstrap prüfen"
if [[ "$SAFE_MODE" -eq 1 ]]; then
  echo "$PRODUCT_NAME: Safe-Mode — keine schreibende PIN-/Bootstrap-Aktion."
else
  run_required "PIN-Prüfung" \
    "$PYTHON_BIN" system/pin_auth.py \
    --config config/pin.json --state data/pin_state.json "${DEBUG_ARGS[@]}"
  run_required "Bootstrap" scripts/bootstrap.sh
fi

progress "Strukturvertrag prüfen"
run_required "Strukturprüfung" \
  "$PYTHON_BIN" system/structure_checker.py --root "$ROOT_DIR" "${DEBUG_ARGS[@]}"

progress "Self-Repair ausführen"
REPAIR_ARGS=(--root "$ROOT_DIR")
[[ "$SAFE_MODE" -eq 0 ]] || REPAIR_ARGS+=(--dry-run)
run_required "Self-Repair" \
  "$PYTHON_BIN" system/self_repair.py "${REPAIR_ARGS[@]}" "${DEBUG_ARGS[@]}"

progress "Health-Check ausführen"
run_required "Health-Check" \
  "$PYTHON_BIN" system/health_check.py --root "$ROOT_DIR" "${DEBUG_ARGS[@]}"

progress "JSON und Konfiguration validieren"
run_required "JSON-Validierung" \
  "$PYTHON_BIN" system/json_validator.py --root "$ROOT_DIR" "${DEBUG_ARGS[@]}"

progress "Dateinamen validieren/reparieren"
NAME_ARGS=(--root "$ROOT_DIR")
[[ "$SAFE_MODE" -eq 0 ]] || NAME_ARGS+=(--dry-run)
run_required "Dateinamenprüfung" \
  "$PYTHON_BIN" system/filename_fixer.py "${NAME_ARGS[@]}" "${DEBUG_ARGS[@]}"

progress "Archivdatenbank initialisieren und CLI-Aliase synchronisieren"
run_required "Archivinitialisierung" \
  "$PYTHON_BIN" -m modules.archiv_manager --list
if [[ "$SAFE_MODE" -eq 0 ]]; then
  run_required "Alias-Synchronisierung" \
    "$PYTHON_BIN" -m modules.archiv_manager --install-aliases
fi

progress "Fortschrittsdaten prüfen"
TODO_ARGS=(--config config/todo_config.json progress)
[[ "$SAFE_MODE" -eq 0 ]] && TODO_ARGS+=(--write-progress)
run_required "Fortschrittsprüfung" \
  "$PYTHON_BIN" system/todo_manager.py "${TODO_ARGS[@]}" "${DEBUG_ARGS[@]}"

progress "Modulverbund prüfen"
run_required "Modulprüfung" \
  "$PYTHON_BIN" system/module_integration_checks.py \
  --config config/modules.json \
  --selftests config/module_selftests.json "${DEBUG_ARGS[@]}"

progress "Test-Gate prüfen"
if [[ "$SAFE_MODE" -eq 1 ]]; then
  echo "$PRODUCT_NAME: Safe-Mode — Test-Gate bleibt unverändert."
else
  run_required "Test-Gate" \
    "$PYTHON_BIN" system/test_gate.py --config config/test_gate.json "${DEBUG_ARGS[@]}"
fi

progress "Pakete, Tkinter und SQLite abschließend nachvalidieren"
run_required "Abhängigkeits-Nachvalidierung" \
  "$PYTHON_BIN" system/dependency_checker.py \
  --requirements config/requirements.txt \
  --check-only \
  --report data/runtime/dependency_report_final.json "${DEBUG_ARGS[@]}"
run_required "GUI-Bibliotheken" \
  "$PYTHON_BIN" -c 'import tkinter, sqlite3; print("Tkinter und SQLite verfügbar")'

if (( ${#FAILURES[@]} )); then
  echo "$PRODUCT_NAME: Start blockiert — ${#FAILURES[@]} kritische Prüfung(en) fehlgeschlagen."
  printf ' - %s\n' "${FAILURES[@]}"
  echo "$PRODUCT_NAME: Kein unsicherer Teilstart. Berichte: data/runtime/ und logs/."
  exit 2
fi

if [[ "$NO_START" -eq 1 || "$SAFE_MODE" -eq 1 ]]; then
  echo "$PRODUCT_NAME: vollständige Nachvalidierung erfolgreich; Serverstart unterdrückt."
  exit 0
fi

WEB_ARGS=(--config config/web_server.json --check-only --check-browser)
[[ -z "$WEB_HOST" ]] || WEB_ARGS+=(--host "$WEB_HOST")
[[ -z "$WEB_PORT" ]] || WEB_ARGS+=(--port "$WEB_PORT")
[[ -z "$WEB_MAX_PORT" ]] || WEB_ARGS+=(--max-port "$WEB_MAX_PORT")
[[ "$STRICT_PORT" -eq 0 ]] || WEB_ARGS+=(--strict-port)
progress "Webserver-Port und Google-Chrome-Startfähigkeit prüfen"
run_required "Webserver-Vorprüfung" "$PYTHON_BIN" system/web_server.py "${WEB_ARGS[@]}"

if (( ${#FAILURES[@]} )); then
  echo "$PRODUCT_NAME: Serverstart blockiert — Vorprüfung fehlgeschlagen."
  printf ' - %s\n' "${FAILURES[@]}"
  exit 2
fi

SERVER_ARGS=(--config config/web_server.json)
[[ -z "$WEB_HOST" ]] || SERVER_ARGS+=(--host "$WEB_HOST")
[[ -z "$WEB_PORT" ]] || SERVER_ARGS+=(--port "$WEB_PORT")
[[ -z "$WEB_MAX_PORT" ]] || SERVER_ARGS+=(--max-port "$WEB_MAX_PORT")
[[ "$STRICT_PORT" -eq 0 ]] || SERVER_ARGS+=(--strict-port)
[[ "$NO_BROWSER" -eq 0 ]] || SERVER_ARGS+=(--no-browser)
progress "Provoware Memo als integrierte Browseroberfläche starten"
echo "$PRODUCT_NAME: Startkette vollständig erfolgreich. Ampelstatus: grün."
exec "$PYTHON_BIN" system/web_server.py "${SERVER_ARGS[@]}"
