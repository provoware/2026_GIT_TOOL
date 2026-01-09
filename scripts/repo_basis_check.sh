#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v git >/dev/null 2>&1; then
  echo "Fehler: Git ist nicht installiert. Bitte Git installieren." >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Fehler: Kein Git-Repository gefunden." >&2
  exit 1
fi

REMOTE_NAME="$(git remote | head -n 1)"
if [[ -z "$REMOTE_NAME" ]]; then
  echo "Hinweis: Es ist kein Remote-Repository eingerichtet." >&2
  echo "Lösung: git remote add origin <URL>" >&2
  exit 2
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Hinweis: Es gibt nicht gespeicherte Änderungen (git status prüfen)." >&2
  exit 2
fi

echo "Repo-Check: Remote gefunden (${REMOTE_NAME})."

echo "Repo-Check: Push wird als Trockenlauf (dry-run) geprüft."
if git push --dry-run "$REMOTE_NAME" >/dev/null 2>&1; then
  echo "Repo-Check: Push-Trockenlauf erfolgreich." 
  exit 0
fi

echo "Fehler: Push-Trockenlauf fehlgeschlagen." >&2
echo "Lösung: Zugangsdaten prüfen oder Remote-URL korrigieren." >&2
exit 2
