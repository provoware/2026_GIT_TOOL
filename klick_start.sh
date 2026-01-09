#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python >/dev/null 2>&1; then
  echo "Fehler: Python ist nicht installiert. Bitte Python installieren, damit der Start funktioniert."
  exit 1
fi

if [[ ! -x "${ROOT_DIR}/scripts/start.sh" ]]; then
  echo "Fehler: Start-Routine fehlt oder ist nicht ausführbar: scripts/start.sh"
  echo "Tipp: Ausführbar machen mit: chmod +x scripts/start.sh"
  exit 1
fi

echo "Klick&Start: Startroutine läuft (automatische Prüfungen + Fortschritt)."
"${ROOT_DIR}/scripts/start.sh"

echo "Klick&Start: Startübersicht wird geöffnet."
python "${ROOT_DIR}/system/launcher_gui.py"
