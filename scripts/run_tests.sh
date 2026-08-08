#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECK_SCRIPT="${ROOT_DIR}/scripts/private_tool_check.sh"
DIST_DIR="${ROOT_DIR}/dist"
ZIP_PATH="${DIST_DIR}/2026_GIT_TOOL_PRIVAT.zip"

show_help() {
  cat <<'EOF'
Provoware Memo — private Tool-Prüfung

Nutzung:
  ./scripts/run_tests.sh [--startup-gate]

Führt den einzigen lokalen Privattool-Prüfvertrag aus:
  scripts/private_tool_check.sh

Bei Erfolg wird dist/2026_GIT_TOOL_PRIVAT.zip erstellt. In einer grafischen
Linux-Sitzung wird anschließend der Ordner dist/ bestmöglich geöffnet.

--startup-gate bleibt aus Kompatibilitätsgründen erhalten und verwendet denselben
Prüfvertrag. Dadurch existiert keine zweite, abweichende Testkette mehr.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --startup-gate)
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Fehler: Unbekannte Option: $1" >&2
      exit 2
      ;;
  esac
done

[[ -x "${CHECK_SCRIPT}" || -f "${CHECK_SCRIPT}" ]] || {
  echo "Fehler: Zentraler Privattool-Check fehlt: ${CHECK_SCRIPT}" >&2
  exit 2
}

echo "Diagnose: zentralen Privattool-Check starten."
bash "${CHECK_SCRIPT}"

[[ -f "${ZIP_PATH}" ]] || {
  echo "Fehler: Prüfung war erfolgreich, aber das Privat-ZIP fehlt: ${ZIP_PATH}" >&2
  exit 3
}

echo "Diagnose: erfolgreich."
echo "Privat-ZIP: ${ZIP_PATH}"

if [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]] && command -v xdg-open >/dev/null 2>&1; then
  xdg-open "${DIST_DIR}" >/dev/null 2>&1 &
fi
