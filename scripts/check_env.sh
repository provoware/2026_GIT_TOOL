#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

show_help() {
  cat <<'EOF'
Umgebungs-Check (Prerequisites = Voraussetzungen)

Nutzung:
  ./scripts/check_env.sh

Dieser Check prüft:
  - Python ist installiert und erreichbar.
  - Die Start-Routine ist ausführbar.

Hinweis:
  Bei Fehlern erhalten Sie eine klare Lösungsmeldung.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

if ! command -v python >/dev/null 2>&1; then
  echo "Fehler: Python ist nicht installiert. Bitte Python installieren, damit die Start-Routine läuft."
  exit 1
fi

if [[ ! -x "${ROOT_DIR}/scripts/start.sh" ]]; then
  echo "Fehler: Start-Routine fehlt oder ist nicht ausführbar: scripts/start.sh"
  echo "Tipp: Ausführbar machen mit: chmod +x scripts/start.sh"
  exit 1
fi

echo "Umgebungs-Check: OK. Voraussetzungen sind erfüllt."
