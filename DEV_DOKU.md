# DEV_DOKU

## Zweck
Diese Dokumentation richtet sich an Entwicklerinnen und Entwickler. Sie beschreibt Struktur, Standards und den geplanten Ablauf.

## Projektstatus
- Derzeit liegt der Fokus auf Dokumentation und Aufgabenplanung.
- Start-Routine, Tests und Modul-Standards werden schrittweise umgesetzt.
- Start-Check und Modul-Check sind umgesetzt und in der Diagnose sichtbar.
- Modul-Check wird im Self-Test mit einem defekten Modul automatisch geprüft.

## Struktur (aktuell)
- `src/`: Systemlogik (stabile Kernlogik).
  - `src/records/record_updater.py`: Logik für Archivierung und Changelog.
- `config/`: Konfiguration (Config = Einstellungen, änderbar ohne Code).
  - `config/records.json`: Regeln für Einträge.
- `scripts/`: Start- und Prüfskripte.
- `tests/`: Automatische Tests (Unit-Tests).

## Standards (aktuell)
- Einheitliche To-Do-Validierung (Formatprüfung).
- Agent-Zuordnung über zentrale Regeldatei (`config/agent_rules.json`).
- Barrierefreie UI-Texte (Deutsch, klar, laienverständlich).
- Logging-Format: `Zeit | Modul | LEVEL | Nachricht` (ISO-Zeitstempel).
- Fehler-Logs sind optisch hervorgehoben (Level `ERROR`).

## Qualitätssicherung
- **Tests**: Automatische Tests für Kernfunktionen.
- **Formatierung**: Automatische Codeformatierung (einheitlicher Stil, geplant).
- **Prüfungen**: Start-Routine prüft Struktur und Abhängigkeiten (geplant).

## Dokumentationsregeln
- Änderungen werden im `CHANGELOG.md` beschrieben.
- Abgeschlossene Aufgaben kommen nach `DONE.md`.
- Fortschritt wird in `PROGRESS.md` aktualisiert.

## Bauen/Starten/Testen
Aktuell gibt es keine lauffähigen Skripte. Diese Sektion wird ergänzt, sobald Start- und Testscripte existieren.

### Manuelle Checks (UI)
- Tastaturtest: Mit `Tab`/`Shift+Tab` die Reihenfolge prüfen, mit `Enter`/`Leertaste` (Space) Buttons auslösen.
- Fokusprüfung: Fokus-Ringe müssen klar sichtbar sein (Kontrast sichtbar).
