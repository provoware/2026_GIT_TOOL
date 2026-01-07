# Tool-Standards

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
