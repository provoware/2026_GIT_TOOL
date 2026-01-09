#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v python >/dev/null 2>&1; then
  echo "Fehler: Python ist nicht installiert. Bitte Python installieren, damit die Start-Routine läuft."
  exit 1
fi

TOTAL_STEPS=7
CURRENT_STEP=0

update_progress() {
  local message="$1"
  local percent=$((CURRENT_STEP * 100 / TOTAL_STEPS))
  echo "Start-Routine: ${message} (Fortschritt: ${percent} %)"
}

create_required_dirs() {
  local dirs=(
    "src"
    "config"
    "data"
    "logs"
    "scripts"
    "modules"
    "system"
    "tests"
  )

  for dir in "${dirs[@]}"; do
    local path="${ROOT_DIR}/${dir}"
    if [[ -d "$path" ]]; then
      echo "Strukturprüfung: Ordner vorhanden: ${dir}"
    else
      mkdir -p "$path"
      echo "Strukturprüfung: Ordner fehlte und wurde erstellt: ${dir}"
    fi
  done
}

CURRENT_STEP=1
update_progress "Projektstruktur wird geprüft"
create_required_dirs

CURRENT_STEP=2
update_progress "Health-Check (Sicherheitsprüfung) läuft"
python "${ROOT_DIR}/system/health_check.py" --root "${ROOT_DIR}" --self-repair

CURRENT_STEP=3
update_progress "Abhängigkeiten werden geprüft"
python "${ROOT_DIR}/system/dependency_checker.py" --requirements "${ROOT_DIR}/config/requirements.txt"

CURRENT_STEP=4
update_progress "Fortschritt wird aus todo.txt berechnet"
python "${ROOT_DIR}/system/todo_manager.py" progress --write-progress

CURRENT_STEP=5
update_progress "Module werden geprüft"
python "${ROOT_DIR}/system/module_checker.py" --config "${ROOT_DIR}/config/modules.json"

CURRENT_STEP=6
update_progress "Tests werden geprüft (nur nach kompletter Runde)"
python "${ROOT_DIR}/system/test_gate.py" --config "${ROOT_DIR}/config/test_gate.json"

CURRENT_STEP=7
update_progress "Start-Routine abgeschlossen"
echo "Start-Routine: PROGRESS.md wurde aktualisiert."
