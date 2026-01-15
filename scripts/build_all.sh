#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

show_help() {
  cat <<'DOC'
Build-All (Ein-Befehl-Build mit Checks, Doku und Strukturpflege)

Nutzung:
  ./scripts/build_all.sh [--no-tests] [--no-docs] [--no-records] [--no-structure]

Optionen:
  --no-tests      Tests/Codequalität überspringen.
  --no-docs       Auto-Status-Update überspringen.
  --no-records    Changelog-/DONE-Update überspringen.
  --no-structure  Strukturpflege (Baumstruktur/Manifest/Register) überspringen.
  -h, --help      Hilfe anzeigen.
DOC
}

RUN_TESTS=1
RUN_DOCS=1
RUN_RECORDS=1
RUN_STRUCTURE=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-tests)
      RUN_TESTS=0
      shift
      ;;
    --no-docs)
      RUN_DOCS=0
      shift
      ;;
    --no-records)
      RUN_RECORDS=0
      shift
      ;;
    --no-structure)
      RUN_STRUCTURE=0
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Fehler: Unbekannte Option: $1" >&2
      show_help
      exit 2
      ;;
  esac
done

printf "Build-All: Umgebung wird geprüft...\n"
"${ROOT_DIR}/scripts/check_env.sh"

if [[ "${RUN_STRUCTURE}" -eq 1 ]]; then
  printf "Build-All: Strukturpflege läuft...\n"
  "${ROOT_DIR}/scripts/update_structure.sh"
else
  printf "Build-All: Strukturpflege übersprungen.\n"
fi

if [[ "${RUN_RECORDS}" -eq 1 ]]; then
  printf "Build-All: Changelog-/DONE-Update läuft...\n"
  "${ROOT_DIR}/scripts/update_records.sh"
else
  printf "Build-All: Changelog-/DONE-Update übersprungen.\n"
fi

if [[ "${RUN_DOCS}" -eq 1 ]]; then
  printf "Build-All: Auto-Status-Update läuft...\n"
  "${ROOT_DIR}/scripts/update_docs.sh"
else
  printf "Build-All: Auto-Status-Update übersprungen.\n"
fi

if [[ "${RUN_TESTS}" -eq 1 ]]; then
  printf "Build-All: Tests und Codequalität laufen...\n"
  "${ROOT_DIR}/scripts/run_tests.sh"
else
  printf "Build-All: Tests übersprungen.\n"
fi

printf "Build-All: Fertig. Bitte Ergebnis in logs/ und reports/ prüfen.\n"
