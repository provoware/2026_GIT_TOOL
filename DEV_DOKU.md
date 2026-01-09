# DEV_DOKU

## Zweck
Diese Dokumentation richtet sich an Entwicklerinnen und Entwickler. Sie beschreibt Struktur, Standards und den geplanten Ablauf.

## Projektstatus
- Derzeit liegt der Fokus auf Dokumentation und Aufgabenplanung.
- Start-Routine, Tests und Modul-Standards werden schrittweise umgesetzt.
- Start-Check und Modul-Check sind umgesetzt und in der Diagnose sichtbar.
- Modul-Check wird im Self-Test mit einem defekten Modul automatisch geprüft.
- Start-Routine prüft die Projektstruktur und erstellt fehlende Ordner automatisch.
- Start-Routine zeigt Fortschritt in Prozent je Schritt.

## Struktur (aktuell)
- `src/`: Systemlogik (stabile Kernlogik).
  - `src/records/record_updater.py`: Logik für Archivierung und Changelog.
- `config/`: Konfiguration (Config = Einstellungen, änderbar ohne Code).
  - `config/records.json`: Regeln für Einträge.
- `system/`: Tool-Logik (CLI-Tools und Automatisierung).
  - `system/todo_manager.py`: Fortschritt berechnen und To-Dos archivieren.
  - `system/log_exporter.py`: Logdateien als ZIP exportieren.
- `logs/`: Logdateien (Protokolle).
- `data/log_exports/`: Exporte von Logdateien.
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
- **Prüfungen**: Start-Routine prüft Struktur (automatisch) und Abhängigkeiten (geplant).

## Dokumentationsregeln
- Änderungen werden im `CHANGELOG.md` beschrieben.
- Abgeschlossene Aufgaben kommen nach `DONE.md`.
- Fortschritt wird in `PROGRESS.md` aktualisiert.

## Bauen/Starten/Testen
### Fortschritt aus todo.txt berechnen
1. `python system/todo_manager.py progress`
2. Optional: `python system/todo_manager.py progress --write-progress` (schreibt PROGRESS.md)

### Start-Routine (Struktur + Fortschritt)
1. `./scripts/start.sh`
2. Die Start-Routine erstellt fehlende Ordner automatisch und zeigt den Fortschritt in Prozent.

### Log-Export (ZIP)
1. `python system/log_exporter.py`
2. Optional: `python system/log_exporter.py --logs-dir logs --export-dir data/log_exports`

### Lokaler Start (UI prüfen)
1. `cd gms-archiv-tool_v1.2.3_2026-01-06`
2. `npm install`
3. `npm run dev`

### Build/Preview
1. `cd gms-archiv-tool_v1.2.3_2026-01-06`
2. `npm install`
3. `npm run build`
4. `npm run preview`

### Manuelle UI-Checks (Barrierefreiheit)
- Kontrast prüfen (Dark/Light-Theme vergleichen, Ziel ≥ 4,5:1).
- Schriftgröße prüfen (mind. 16px).
- Darkmode-Lesbarkeit prüfen (Text + Buttons).
