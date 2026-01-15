# GMS Archiv Tool (Genres / Moods / Stile)

## Version

- v1.2.3 (2026-01-06)

## Start

```bash
npm install
npm run dev
```

## Build (Produktionspaket)

```bash
npm run build
```

## Preview (lokale Vorschau)

```bash
npm run preview
```

## Tests & Codequalität (Linting/Formatierung)

```bash
npm run lint
npm run format
```

Bei Fehlern hilft `npm run format:fix`, um das Format automatisch zu korrigieren.

## Daten & Speicherung
- Lokale Speicherung erfolgt im Browser (`localStorage`, lokaler Speicher im Browser).
- Export-Dateien nutzen eindeutige Dateinamen mit Version und Datum.

## Logging & Debugging
- Logeinträge folgen dem Format: `Zeit | Modul | LEVEL | Nachricht`.
- Für Debugging (Fehlersuche) bitte die Browser-Konsole öffnen.

## Barrierefreiheit (Accessibility)
- Tastaturbedienung ist möglich (Tab/Shift+Tab/Enter).
- Fokus-Ring ist sichtbar für klare Orientierung.
- Kontrastreiche Themes sind enthalten.

## Themes (Farbvarianten)
- Paper
- High Contrast
- Nebula
- Midnight

## Laien-Tipps (einfach erklärt)
- Start ohne Risiko: Erst `npm run dev` nutzen (Start im Entwicklungsmodus).
- Hilfe bei Fehlern: Browser-Konsole öffnen (F12) und letzte Meldung lesen.
- Große Schrift testen: Zoom-Funktion nutzen (Ctrl + Mausrad).
- Theme wechseln: In der UI ein kontrastreiches Theme auswählen.

## Fixes

- Fokus bleibt stabil in allen Eingabefeldern (kein Cursor-Sprung)
- Kontrast verbessert (Buttons, Badges, Inputs, Fokus-Ring)
- Themes: Paper/High Contrast/Nebula/Midnight
- Ctrl + Mausrad zoomt die UI (0.8–1.6), Reset im Header
- Autosave: alle 10 Minuten + Debounce nach Änderungen
