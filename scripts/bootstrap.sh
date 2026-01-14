#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

show_help() {
  cat <<'EOF'
Bootstrap (Grundstruktur = Basis-Ordner)

Nutzung:
  ./scripts/bootstrap.sh

Dieser Schritt legt fehlende Standard-Ordner an:
  src, config, data, logs, scripts, modules, system, tests
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

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

create_required_dirs
