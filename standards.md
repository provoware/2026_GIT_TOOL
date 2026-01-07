# Tool-Standards

Stand: 2026-01-07

## Zweck
Diese Datei legt verbindliche Standards für alle Tools fest. Ziel ist ein gemeinsames Datenmodell, klare Validierung und verständliche Dokumentation.

## Gemeinsames Schema (Datenmodell)
Es gibt drei Kernobjekte: `task`, `log`, `module`.

### Pflichtfelder (für alle Objekte)
- `id`: Eindeutige Kennung (String).
- `status`: Zustand (String, vordefiniert).
- `zeit`: Zeitpunkt im ISO-Format (String, z. B. `2026-01-07T12:00:00Z`).
- `quelle`: Ursprung der Daten (String, z. B. `user`, `system`, `import`).

### Objekt: task
- `titel`: Klarer Titel in einfacher Sprache.
- `beschreibung`: Kurze Erklärung, was zu tun ist.
- `prioritaet`: `niedrig`, `mittel`, `hoch`.

### Objekt: log
- `level`: `info`, `warn`, `error`, `debug`.
- `nachricht`: Klare, laienverständliche Meldung.
- `kontext`: Optionales Objekt mit Zusatzdaten.

### Objekt: module
- `name`: Modulname in Klartext.
- `version`: Semver-String.
- `status_detail`: Freitext für technische Details.

## Validierungsregeln (Input-Prüfung)
- **Pflichtfelder** müssen vorhanden und nicht leer sein.
- `id` darf nur Kleinbuchstaben, Ziffern und Bindestriche enthalten (Regex: `^[a-z0-9-]+$`).
- `status` ist auf feste Werte begrenzt:
  - `task`: `offen`, `in_arbeit`, `erledigt`, `blockiert`
  - `log`: `info`, `warn`, `error`, `debug`
  - `module`: `aktiv`, `inaktiv`, `fehler`
- `zeit` muss ISO-Format haben und darf nicht in der Zukunft liegen.
- Jede Funktion prüft Eingaben und bestätigt erfolgreiche Ausgaben (Erfolgsmeldung).
- Fehlertexte sind auf Deutsch, kurz, und erklären den nächsten Schritt.

## Dokumentationsabschnitt (verbindlich)
- Jede Änderung an Schema oder Logik wird in `CHANGELOG.md` dokumentiert.
- Neue oder geänderte Standards werden in `DEV_DOKU.md` erklärt.
- Abgeschlossene Aufgaben werden in `DONE.md` eingetragen.
- Der Fortschritt wird in `PROGRESS.md` aktualisiert.

## Barrierefreiheit und Qualität
- Alle UI-Texte sind Deutsch, klar und laienverständlich.
- Tastaturbedienung ist Pflicht.
- Kontrast und Lesbarkeit sind zu prüfen.
- Für Logs gibt es einen Debug-Modus mit klarer Kennzeichnung.
