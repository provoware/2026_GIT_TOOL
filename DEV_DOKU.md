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
- Launcher listet Module aus `config/modules.json` übersichtlich auf.
- Modul-Check prüft registrierte Module über `config/modules.json`.
- GUI-Launcher führt beim Aktualisieren zusätzlich den Modul-Check aus und meldet Probleme direkt in der Übersicht.
- GUI-Launcher nutzt zusätzliche Themes und sichtbare Fokusrahmen für bessere Tastaturbedienung.
- Download-Ordner-Aufräum-Modul bietet Scan, Plan, Undo und Protokoll.
- Datei-Suche-Modul bietet Filter, Organisation und Undo.
- Abhängigkeitsprüfung ignoriert Inline-Kommentare in requirements.txt.
- Modul-Check validiert Entry-Pfade gegen Pfad-Traversal.

## Struktur (aktuell)
- `src/`: Systemlogik (stabile Kernlogik).
  - `src/records/record_updater.py`: Logik für Archivierung und Changelog.
  - `src/core/data_model.py`: Zentrales Datenmodell für To-Dos und Kalender.
- `config/`: Konfiguration (Config = Einstellungen, änderbar ohne Code).
- `config/records.json`: Regeln für Einträge.
  - `config/launcher_gui.json`: GUI-Launcher-Themes und Standard-Theme.
  - `config/modules.json`: Zentrale Modul-Liste für den Launcher.
  - `config/notiz_editor.json`: Konfiguration für den Notiz-Editor (Templates, Themes).
  - `config/charakter_modul.json`: Konfiguration für das Charakter-Modul (Templates, Themes).
  - `config/download_aufraeumen.json`: Konfiguration für Download-Aufräumen (Regeln, Themes).
  - `config/datei_suche.json`: Konfiguration für Datei-Suche (Filter, Themes).
  - `config/requirements.txt`: Python-Abhängigkeiten (pip-Pakete).
  - `config/pytest.ini`: Pytest-Konfiguration.
  - `config/ruff.toml`: Ruff-Regeln für Codequalität (Linting).
  - `config/black.toml`: Black-Regeln für Codeformatierung.
  - `config/test_gate.json`: Regeln für die Test-Sperre (Schwelle + Befehl).
  - `config/modules.json`: Modul-Liste für den Launcher.
  - `config/todo_kalender.json`: Konfiguration für To-Do-&-Kalender-Modul.
  - `config/modules.json`: Registrierte Module für den Modul-Check.
- `system/`: Tool-Logik (CLI-Tools und Automatisierung).
  - `system/todo_manager.py`: Fortschritt berechnen und To-Dos archivieren.
  - `system/log_exporter.py`: Logdateien als ZIP exportieren.
  - `system/launcher.py`: Launcher (Modulübersicht).
  - `system/launcher_gui.py`: GUI-Launcher (Startübersicht mit Themes).
- `system/test_gate.py`: Test-Sperre (Tests erst nach kompletter Runde).
  - `system/module_checker.py`: Modul-Check (Struktur + Manifest + Entry-Datei).
  - `system/dependency_checker.py`: Abhängigkeiten prüfen und automatisch installieren.
- `logs/`: Logdateien (Protokolle).
- `data/log_exports/`: Exporte von Logdateien.
- `data/test_state.json`: Statusdatei für den Test-Start.
- `data/notiz_editor.json`: Datenablage für den Notiz-Editor.
- `data/charakter_modul.json`: Datenablage für das Charakter-Modul.
- `data/download_aufraeumen_log.json`: Protokoll für Aufräum-Aktionen (Undo).
- `data/datei_suche_log.json`: Protokoll für Organisationsaktionen (Undo).
- `modules/`: Standardisierte Module.
  - `modules/status/module.py`: Beispielmodul mit Standard-Schnittstelle.
  - `modules/status/manifest.json`: Metadaten des Beispielmoduls.
- `data/todo_kalender.json`: Datenablage für To-Do-&-Kalender-Modul.
- `scripts/`: Start- und Prüfskripte.
  - `scripts/repo_basis_check.sh`: Repo-Check (Remote + Push-Trockenlauf).
  - `scripts/run_tests.sh`: Tests + Codequalität + Formatprüfung.
- `klick_start.sh`: Klick&Start-Skript (führt Start-Routine aus und öffnet die GUI-Startübersicht).
- `tests/`: Automatische Tests (Unit-Tests).
- `modules/`: Modul-Ordner (Standard: manifest.json + module.py).
  - `modules/todo_kalender/`: To-Do-&-Kalender-Modul.
- `modules/notiz_editor/`: Notiz-Editor-Modul mit Templates und Dashboard.
- `modules/charakter_modul/`: Charakter-Modul für konsistente Profile.
- `modules/download_aufraeumen/`: Download-Ordner-Aufräumen (Scan/Plan/Undo).
- `modules/datei_suche/`: Datei-Suche mit Filter und Organisationsfunktionen.
- `modules/`: Module nach Standard (Manifest + Entry).

## Standards (aktuell)
- Einheitliche To-Do-Validierung (Formatprüfung).
- Agent-Zuordnung über zentrale Regeldatei (`config/agent_rules.json`).
- Barrierefreie UI-Texte (Deutsch, klar, laienverständlich).
- Logging-Format: `Zeit | Modul | LEVEL | Nachricht` (ISO-Zeitstempel).
- Fehler-Logs sind optisch hervorgehoben (Level `ERROR`).
- Zentrales Datenmodell für To-Dos/Kalender in `src/core/data_model.py`.
- Einheitliche Modul-Schnittstelle (init/run/exit/validateInput/validateOutput) gemäß `standards.md`.
- Modul-Pfade in `config/modules.json` zeigen auf Modulordner (nicht auf einzelne Dateien).
- Notiz-Editor und Charakter-Modul nutzen Templates, Themes und Dashboard-Statistiken.

## Qualitätssicherung
- **Tests**: Automatische Tests für Kernfunktionen (Start erst nach kompletter Runde).
- **Codequalität (Linting)**: Ruff prüft Fehler und Stilregeln automatisch.
- **Formatierung**: Black prüft den Code auf einheitliches Format.
- **Prüfungen**: Start-Routine prüft Struktur und Abhängigkeiten automatisch.
- **Prüfungen**: Modul-Check validiert aktivierte Module und deren Manifest.

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
2. Die Start-Routine erstellt fehlende Ordner automatisch, prüft Abhängigkeiten, prüft Module und zeigt den Fortschritt in Prozent.
3. Tests laufen automatisch, sobald eine Runde (3 erledigte Tasks) erreicht ist.

### Tests + Codequalität (manuell)
1. `./scripts/run_tests.sh`
2. Führt Pytest, Ruff (Linting) und Black (Formatprüfung) in dieser Reihenfolge aus.
3. Optional: `./scripts/run_tests.sh --help` (kurze Erklärung für Laien).

### Abhängigkeiten (manuell prüfen)
1. `python system/dependency_checker.py --requirements config/requirements.txt`
2. Optional: `python system/dependency_checker.py --requirements config/requirements.txt --no-auto-install`

### Repo-Basis-Check (Push-Trockenlauf)
1. `./scripts/repo_basis_check.sh`
2. Hinweis: Bei fehlendem Remote erscheint eine klare Lösungsmeldung.

### Klick&Start (für Laien)
1. `./klick_start.sh`
2. Die Start-Routine läuft automatisch, danach öffnet sich die GUI-Startübersicht.

### Launcher (Modulübersicht)
1. `python system/launcher.py`
2. Optional: `python system/launcher.py --show-all` (zeigt auch deaktivierte Module).

### GUI-Launcher (Startübersicht)
1. `python system/launcher_gui.py`
2. Optional: `python system/launcher_gui.py --show-all --debug` (Details anzeigen).
3. Tastatur-Shortcuts: Alt+A (alle Module), Alt+D (Debug), Alt+R (aktualisieren), Alt+T (Theme), Alt+Q (beenden).
4. Modul-Check: Wird bei jeder Aktualisierung automatisch ausgeführt (Status steht in der Übersicht).
### Modul-Check (manuell)
1. `python system/module_checker.py --config config/modules.json`
2. Bei Fehlern werden klare Hinweise und Lösungsvorschläge ausgegeben.

### Test-Sperre (manuell)
1. `python system/test_gate.py --config config/test_gate.json`
2. Tests starten erst nach kompletter Runde, sonst erscheint ein Hinweis.

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
- Fokusrahmen prüfen (Tabulator: deutlich sichtbarer Rahmen).
