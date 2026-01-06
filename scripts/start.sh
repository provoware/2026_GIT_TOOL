#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

printf "\n[Start] Startroutine (Bootstrap) läuft...\n"

if ! command -v node >/dev/null 2>&1; then
  printf "[Fehler] Node.js fehlt. Bitte Node.js installieren.\n"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  printf "[Fehler] npm fehlt. Bitte npm installieren.\n"
  exit 1
fi

printf "[Info] Abhängigkeiten (Dependencies) werden installiert...\n"
npm install

printf "[Info] Code-Qualität (Linting) wird geprüft...\n"
npm run lint

printf "[Info] Code-Formatierung (Formatting) wird geprüft...\n"
npm run format

printf "[Info] Tests laufen...\n"
npm test

printf "[Erfolg] Alle Prüfungen sind erfolgreich.\n"
printf "[Start] Starte Electron-Anwendung...\n"
npm run start
