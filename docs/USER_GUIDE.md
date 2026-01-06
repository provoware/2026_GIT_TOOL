# Schritt-für-Schritt-Anleitung (User Guide)

## Ziel
Diese Anleitung ist für Laien (Anfängerinnen und Anfänger) geschrieben. Fachwörter sind in Klammern erklärt.

## Schnellstart
1. **Projekt öffnen**
   - Öffne den Projektordner `2026_GIT_TOOL`.

2. **Startroutine starten** (Bootstrap)
   - Öffne ein Terminal (Eingabe-Fenster).
   - Führe aus:
     ```bash
     npm run start:bootstrap
     ```
   - Die Startroutine installiert automatisch alle Abhängigkeiten (Dependencies).
   - Danach werden Tests und Qualitätsprüfungen automatisch ausgeführt.

3. **Programm starten**
   - Wenn alles erfolgreich war, startet die App automatisch.

## Häufige Aufgaben
### Tests ausführen (Tests)
```bash
npm test
```

### Code-Qualität prüfen (Linting)
```bash
npm run lint
```

### Code-Format prüfen (Formatting)
```bash
npm run format
```

### Alles automatisch prüfen (Quality Check)
```bash
npm run quality
```

### Automatisch reparieren (Auto Fix)
```bash
npm run quality:fix
```
*Hinweis:* Diese Aktion kann Dateien ändern.

## Themen (Themes)
- Es gibt mehrere Hoch-Kontrast-Themes (High Contrast).
- Du kannst im Dashboard per Button wechseln.
- Standard-Theme wird in `config/user/app.config.json` gesetzt.

## Hilfe bei Problemen
- Prüfe, ob **Node.js** installiert ist.
- Prüfe, ob `npm` verfügbar ist.
- Starte die Startroutine erneut.
