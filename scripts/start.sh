#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v node >/dev/null 2>&1; then
  echo "Fehler: Node.js ist nicht installiert. Bitte Node.js installieren, damit die Start-Routine läuft."
  exit 1
fi

TOTAL_STEPS=3
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
update_progress "Fortschritt wird aus todo.txt berechnet"
node "${ROOT_DIR}/scripts/progress.js" --update

CURRENT_STEP=3
update_progress "Start-Routine abgeschlossen"
echo "Start-Routine: PROGRESS.md wurde aktualisiert."
