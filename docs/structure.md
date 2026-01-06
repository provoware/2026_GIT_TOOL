# Struktur-Regeln (Project Structure)

Diese Regeln helfen, den Code klar und wartbar zu halten.

## Ordner (Folders)

- `src/core/`: Systemlogik (System Logic). Beispiel: Config, Logging, Validierung, Startprüfung.
- `src/services/`: Tool-Logik (Tool Logic). Beispiel: Templates, Module, Qualitätsprüfung.
- `config/`: Konfiguration (Configuration). Nur feste Einstellungen, keine Nutzerdaten.
- `data/`: Variable Daten (Variable Data). Beispiel: Logs, Exporte, Seeds, Backups.

## Regeln (Rules)

1. Lege neue Systemlogik immer in `src/core/` ab.
2. Lege neue Tool-Features in `src/services/` ab.
3. Lege neue Config-Dateien nur in `config/` ab (`config/system/` oder `config/user/`).
4. Lege Nutzerdaten nur in `data/` ab (z. B. Logs, Exporte, Backups).
5. Passe Importe an die Ordner an, damit Pfade klar bleiben.
6. Die Startroutine (Startup) prüft alles automatisch und gibt Nutzerfeedback (User Feedback).

## Kurz-Check (Quick Check)

- Fehlt eine Config? Startroutine anstoßen und die Meldung lesen.
- Neue Logik? Erst entscheiden: System (core) oder Tool (services).
- Neue Daten? In `data/` speichern, nicht in `src/`.
