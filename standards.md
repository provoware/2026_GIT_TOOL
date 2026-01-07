# Standards

## Zweck
Diese Datei ist die zentrale Quelle für verbindliche Regeln. Sie sorgt dafür, dass alle Module gleich aufgebaut sind und die Bedienung barrierefrei (Accessibility) bleibt.

## Ordnerstruktur (Pflicht)
- `src/`: Systemlogik (stabile Kernlogik, nicht benutzerspezifisch)
- `config/`: Konfiguration (änderbar ohne Code)
- `data/`: Variable Daten (Laufzeitdaten)
- `logs/`: Protokolle (Logs)
- `scripts/`: Start- und Prüfskripte

## Modul-Standard (Pflicht)
Jedes Modul muss einer festen Struktur folgen, damit der Launcher es automatisch laden kann.

### Modul-Ordner
- `modules/<modul-id>/`
  - `module.json` (Metadaten)
  - `index.js` oder `main.py` (Einstiegspunkt)
  - `README.md` (kurze Erklärung in einfacher Sprache)

### module.json (Minimalfelder)
```json
{
  "id": "beispiel-modul",
  "title": "Beispielmodul",
  "description": "Kurze Erklärung in einfacher Sprache (Plain Language).",
  "version": "1.0.0",
  "entry": "index.js",
  "group": "Beispiele",
  "order": 10,
  "enabled": true
}
```

### Einheitliche Schnittstelle (Init/Exit)
Jeder Einstiegspunkt muss diese Funktionen anbieten:
- `init(config, services)`  
  - **Aufgabe**: Startet das Modul.  
  - **Pflicht**: Eingaben validieren (Input-Validierung), klare Fehlermeldung, Rückgabewert prüfen.  
- `exit()`  
  - **Aufgabe**: Ressourcen sauber freigeben.  

**Rückgabe-Standard**:  
Ein Objekt mit klarer Status-Aussage, z. B. `{ "ok": true, "message": "Gestartet." }`.

## Bedienung & Barrierefreiheit (Pflicht)
- Tastaturbedienung vollständig möglich (Tab-Reihenfolge, Fokus sichtbar).
- Kontrast ausreichend (Text gut lesbar).
- Klare, kurze und deutsche UI-Texte.

## Fehlertexte (Pflicht)
- Laienverständlich, kurze Sätze, konkrete Hilfe.
- Beispiel: „Das Modul konnte nicht gestartet werden. Bitte prüfen Sie die Datei module.json.“

## Logging & Debugging (Pflicht)
- Jede Aktion erzeugt einen Logeintrag.
- Debug-Modus (Fehlersuche): zusätzliche Details, aber niemals sensible Daten.

## Tests & Formatierung (Pflicht)
- Automatische Tests für Kernfunktionen.
- Automatische Codeformatierung (Formatter).
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
## Zweck und Geltungsbereich
Diese Standards gelten für alle Tools, Module und Skripte im Projekt. Sie sollen stabile, wartbare und barrierefreie Lösungen sichern.

## Ordnerstruktur (verbindlich)
- `src/`: Systemlogik (stabile Kernlogik, keine nutzerspezifischen Daten).
- `config/`: Konfiguration (änderbar ohne Codeänderung).
- `data/`: Variable Daten und Laufzeitdateien.
- `logs/`: Protokolle (Log-Dateien).
- `scripts/`: Start- und Prüfscripte.
- `tests/`: Automatische Tests.

## Namensregeln
- Dateinamen: klein, eindeutig, Linux-konform (nur `a-z`, `0-9`, `-`, `_`).
- Keine Leerzeichen oder Sonderzeichen.
- Ordnernamen folgen denselben Regeln.

## Modul-Schnittstelle (Init/Exit)
Jedes Modul folgt derselben Struktur, damit es leicht austauschbar bleibt:
- `init(config)`: validiert Eingaben, lädt Abhängigkeiten, gibt Status zurück.
- `run(input)`: verarbeitet Eingaben, protokolliert Aktionen, gibt Ergebnis zurück.
- `shutdown()`: räumt Ressourcen auf, protokolliert Abschluss.

**Rückgabeformat (Standard):**
- `ok` (bool): Erfolg ja/nein.
- `message` (string): klare Meldung auf Deutsch.
- `data` (object|null): Ergebnisdaten.

## Logging-Pflicht
- Jede wichtige Aktion wird protokolliert.
- Fehler werden mit klarer Ursache und Lösungshinweis protokolliert.
- Zwei Modi:
  - **Normal**: kurze, verständliche Einträge.
  - **Debug** (Fehlersuche): detaillierte technische Informationen.

## Fehlertexte (Deutsch, klar)
- Keine Fachwörter ohne Erklärung.
- Form: **Problem + Ursache + Lösung**.
- Beispiel: „Datei nicht gefunden. Ursache: Pfad falsch. Lösung: Pfad prüfen und erneut starten.“

## Barrierefreiheit (Accessibility) – Checkliste
- Tastaturbedienung vollständig möglich.
- Kontrast und Lesbarkeit geprüft (Hell/Dunkel).
- Klare, eindeutige Buttons und Meldungen.
- Mehrere Farbthemen (Themes) zur Auswahl.
- Rückmeldungen sind verständlich und eindeutig.

## Validierung
- Jede Funktion validiert Eingaben (Input) und bestätigt den Erfolg (Output).
- Fehlende oder ungültige Werte werden sauber abgefangen.

## Start- und Prüfregeln
- Die Startroutine prüft automatisch alle nötigen Ordner und Abhängigkeiten.
- Fehlende Abhängigkeiten werden möglichst automatisch installiert.
- Nutzerfeedback ist Pflicht (Statusanzeige, klare Hinweise).

## Testregeln (Qualität)
- **Lint** (Regelprüfung): verhindert Stil- und Qualitätsfehler.
- **Format** (Formatierung): sorgt für einheitliches Layout.
- **Unit-Tests** (Einzeltests): prüfen Kernfunktionen.
- Tests sind automatisierbar und vor jedem Release auszuführen.
