#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

printf "\n[Start] Startroutine (Bootstrap) läuft...\n"
printf "[Info] Einfache Sprache: Ich prüfe zuerst Abhängigkeiten (Dependencies) und Code-Qualität.\n"

fail_step() {
  printf "[Fehler] %s\n" "$1"
  exit 1
}

run_step() {
  local label="$1"
  shift
  printf "\n[Schritt] %s\n" "$label"
  if "$@"; then
    printf "[OK] %s abgeschlossen.\n" "$label"
  else
    fail_step "$label fehlgeschlagen. Bitte Hinweise prüfen."
  fi
}

check_command() {
  local cmd="$1"
  local hint="$2"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    fail_step "$hint"
  fi
}

check_command "node" "Node.js fehlt. Bitte Node.js installieren."
check_command "npm" "npm fehlt. Bitte npm installieren."

run_step "Abhängigkeiten (Dependencies) installieren" npm install
run_step "Qualitätsprüfung (Quality Check) starten" npm run quality:auto

printf "\n[Info] Hinweis: Auto-Reparatur (Auto-Fix) läuft schon in der Qualitätsprüfung.\n"
printf "[Info] Alternative: Mit 'npm run quality:fix' kann man Linting/Formatierung manuell reparieren.\n"
printf "[Erfolg] Alle Prüfungen sind erfolgreich.\n"

run_step "Electron-Anwendung starten" npm run start
