#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

show_help() {
  cat <<'EOF'
Standards anzeigen (Tool-Regeln = interne Vorgaben)

Nutzung:
  ./scripts/show_standards.sh [--section <name>] [--list]

Optionen:
  --section <name>  Bereich anzeigen: standards, styleguide oder all.
  --list            Verfügbare Bereiche auflisten.
  -h, --help        Diese Hilfe anzeigen.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

python "${ROOT_DIR}/system/standards_viewer.py" "$@"
