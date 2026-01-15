#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/opt/2026_git_tool"

printf "Post-Installation: Initialisierung startet...\n"
if [[ ! -d "${APP_ROOT}" ]]; then
  printf "Fehler: Installationspfad fehlt: %s\n" "${APP_ROOT}" >&2
  printf "Lösung: Paket neu installieren oder den Pfad anlegen.\n" >&2
  exit 1
fi

mkdir -p "${APP_ROOT}/logs" "${APP_ROOT}/data"
chmod -R a+rwX "${APP_ROOT}/logs" "${APP_ROOT}/data" || true

if command -v python3 >/dev/null 2>&1 && [[ -f "${APP_ROOT}/system/health_check.py" ]]; then
  printf "Post-Installation: Self-Check läuft...\n"
  if ! python3 "${APP_ROOT}/system/health_check.py" --root "${APP_ROOT}" --self-repair; then
    printf "Warnung: Self-Check fehlgeschlagen.\n" >&2
    printf "Lösung: \'%s\' manuell ausführen und Logs prüfen.\n" "python3 ${APP_ROOT}/system/health_check.py --root ${APP_ROOT} --self-repair" >&2
  fi
else
  printf "Hinweis: python3 oder health_check.py fehlt.\n" >&2
  printf "Lösung: python3 installieren und Self-Check später starten.\n" >&2
fi

printf "Post-Installation: Fertig.\n"
