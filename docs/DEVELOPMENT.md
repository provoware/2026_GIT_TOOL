# Entwickler-Dokumentation (Development Guide)

## Überblick
Dieses Projekt nutzt **globale Standards** über ein Manifest:
- Datei: `config/system/standards.manifest.json`
- Inhalt: Tools, Skripte und Ordnerstruktur.

## Ordnerstruktur (Struktur)
- `src/`: Anwendungscode (App Code)
- `config/system/`: System-Standards und Manifest
- `config/user/`: Nutzer-Konfigurationen (User Config)
- `scripts/`: Automatisierung (Automation)
- `tests/`: Automatische Tests
- `docs/`: Dokumentation

## Start und Qualitätsprüfung (Quality Check)
**Empfohlener Ablauf:**
1. **Startroutine starten** (Bootstrap):
   ```bash
   npm run start:bootstrap
   ```
   Diese Routine:
   - installiert Abhängigkeiten (Dependencies)
   - prüft Code-Qualität (Linting)
   - prüft Formatierung (Formatting)
   - führt Tests aus

2. **Qualitätsprüfung manuell:**
   ```bash
   npm run quality
   ```

3. **Automatische Reparatur (Auto Fix):**
   ```bash
   npm run quality:fix
   ```
   *Hinweis:* Dies formatiert Code automatisch und kann Dateien ändern.

## Konfiguration
- Pfad: `config/user/app.config.json`
- Wichtige Felder:
  - `appName` = App-Name
  - `debugEnabled` = Debug-Modus (Debug Mode)
  - `loggingEnabled` = Logging-Modus (Logging Mode)
  - `theme` = Standard-Theme (Theme)
  - `availableThemes` = Liste der Themes

## Logging und Debugging
- Logger: `src/utils/logger.js`
- Konfiguration: `config/user/app.config.json`
- Jede Log-Nachricht enthält Zeitstempel und Level.

## Tests
- Test-Framework: `node:test`
- Tests liegen in `tests/`
- Beispiele:
  - `tests/validation.test.js`
  - `tests/config.test.js`
  - `tests/logger.test.js`

## Best Practices (empfohlen)
- Schreibe kleine, klare Funktionen.
- Nutze Validierung (Validation), bevor Daten verarbeitet werden.
- Verwende aussagekräftige Fehlermeldungen.
- Halte Konfigurationen in `config/user/`.
- Halte System-Standards in `config/system/`.
