#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v node >/dev/null 2>&1; then
  echo "Fehler: Node.js ist nicht installiert. Bitte Node.js installieren, damit die Start-Routine läuft."
  exit 1
fi

echo "Start-Routine: Fortschritt wird aus todo.txt berechnet ..."
node "${ROOT_DIR}/scripts/progress.js" --update

echo "Start-Routine: Fortschritt angezeigt und PROGRESS.md aktualisiert."
