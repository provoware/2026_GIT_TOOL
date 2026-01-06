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

printf "[Info] Automatische Qualitätsprüfung (Quality Check) startet...\n"
npm run quality

printf "[Info] Hinweis: Mit 'npm run quality:fix' können Formatierung und Linting automatisch repariert werden.\n"

printf "[Erfolg] Alle Prüfungen sind erfolgreich.\n"
printf "[Start] Starte Electron-Anwendung...\n"
npm run start
