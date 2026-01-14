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
- Modulverbund-Checks prüfen Selftests, Manifest-IDs und Modul-Konsistenz.
- GUI-Launcher führt beim Aktualisieren zusätzlich den Modul-Check aus und meldet Probleme direkt in der Übersicht.
- GUI-Launcher nutzt zusätzliche Themes und sichtbare Fokusrahmen für bessere Tastaturbedienung.
- GUI-Launcher zeigt eine Statuszeile inkl. Busy-Hinweis bei längeren Aktionen.
- GUI-Launcher bietet Kontrastmodus per Hotkey (Alt+K) und Zoom per Strg+Mausrad.
- GUI-Launcher hat Hilfe-Kurzinfo und klar benannte Bereiche (Einstellungen, Status, Modulübersicht).
- GUI-Launcher validiert Eingaben und Ausgaben mit klaren Fehlermeldungen.
- GUI-Launcher zeigt farbige Statusmeldungen für Erfolg/Fehler/Busy.
- GUI-Launcher nutzt größere Bedienelemente (Großbutton-UI) für bessere Bedienbarkeit.
- GUI-Launcher zeigt Fehlerklassen (leicht/mittel/schwer) im Modul-Check.
- GUI-Launcher zeigt Datei-Ampelstatus inkl. Dateiproblemen.
- GUI-Launcher zeigt Modul-Selbsttests und deren Status.
- GUI-Launcher zeigt Fehler-Simulationen mit klaren Hinweisen.
- Kontrastprüfung für Launcher-Themes ist dokumentiert und automatisch testbar.
- Download-Ordner-Aufräum-Modul bietet Scan, Plan, Undo und Protokoll.
- Datei-Suche-Modul bietet Filter, Organisation und Undo.
- Abhängigkeitsprüfung ignoriert Inline-Kommentare in requirements.txt.
- Abhängigkeitsprüfung ignoriert Inline-Kommentare auch bei Tabs/Mehrfach-Leerzeichen.
- Modul-Check validiert Entry-Pfade gegen Pfad-Traversal.
- Modul-Check blockiert `..`-Segmente im Entry-Pfad mit klarer Fehlermeldung.
- Modul-Check erzwingt die Modulstruktur über `config/module_structure.json` (Standard-Entry).
- Modul-API-Validator prüft `run`, `validateInput`, `validateOutput` ohne Modul-Import.
- Testskript zeigt eine Schritt-für-Schritt-Hilfe und schreibt Logs nach `logs/test_run.log`.
- Testskript bricht bei Fehlern mit klarer Meldung und Log-Hinweis ab.
- Test-Automatik startet nach abgeschlossenen 4 Tasks (Runden-Logik).
- Health-Check prüft wichtige Dateien/Ordner vor dem Start mit klaren Hinweisen.
- Health-Check kann fehlende Basiselemente automatisch per Self-Repair anlegen.
- Start-Routine ruft den Health-Check mit aktivem Self-Repair auf.
- Health-Check repariert Leserechte und Ausführrechte automatisch (Self-Repair aktiv).
- Launcher/GUI nutzen gemeinsame Pfad- und JSON-Validierung, um Duplikate zu reduzieren.
- Health-Check ist lauffähig, Ruff-konform und nutzt konsistente Datumswerte (Self-Repair aktiv).
- Changelog-Abschnitte mit doppelten Versionsnummern sind zusammengeführt (0.1.20/0.1.19/0.1.15).
- Info-Dateien (PROJEKT_INFO/ANALYSE_BERICHT) sind aktualisiert und laienfreundlich erläutert.
- STRUKTUR.md dokumentiert den vollständigen Verzeichnisbaum inkl. Pflicht- und Dummy-Dateien.
- Standards enthalten einen Benennungsstandard für Dateien/Module und eine Datenmodell-Referenz.
- TODO.md ist strukturiert (IDs, Bereiche, klare Offen/Erledigt-Abschnitte).
- todo.txt ist als laienfreundliche Kurzliste gepflegt und mit TODO.md synchronisiert.
- A–I-Backlog (Architektur bis Komfortfunktionen) ist strukturiert dokumentiert.
- README ist um Architektur/Start/Tests/Barrierefreiheit ergänzt.
- Styleguide (PEP8 + Projektregeln) liegt als Markdown-Datei vor.
- Start-Routine nutzt jetzt getrennte Setup-Skripte (check_env.sh, bootstrap.sh).
- Start-Routine unterstützt Debug- und Logging-Modus (Logdatei start_run.log).
- Start-Routine zeigt Fehleralternativen statt sofortigem Abbruch und sammelt Hinweise.
- Start-Routine prüft JSON-Dateien und korrigiert Dateinamen in data/ und logs/.
- Start-Routine bietet Safe-Mode (schreibgeschützt), Ghost-Mode (Alias) und Sandbox-Modus.
- Struktur-Check prüft die Trennung von Systemlogik, Config und Daten.
- System-Scan kann als Vorabprüfung ohne Schreibzugriffe laufen.
- Standards-Viewer zeigt interne Standards und Styleguide per CLI an.
- Launcher-GUI ist für kleine Fenstergrößen optimiert (zweizeilige Steuerleiste + Umbruch im Footer).
- Modul-Registry (Plugin-System) lädt Module zentral über config/modules.json.
- Modul-API ist dokumentiert (Schnittstellen, Events, States) inkl. Beispielmodul.
- Zentraler Store hält Module/Settings/Logging als Single Source of Truth.
- Zentrales Logging-Modul arbeitet asynchron (Queue-Listener) für alle Systemtools.
- Konfigurationsmodelle validieren GUI- und Modul-Config zentral (inkl. Hex-Farben).
- GUI-Launcher nutzt Debounce für Aktualisierung, um Mehrfachklicks abzufangen.
- Modul-Loader cached Modulimporte (Lazy Loading) für schnellere Abläufe.
- Laien-Tool-Anleitung ist als eigenständige Schritt-für-Schritt-Doku ergänzt.
- GUI-Launcher bietet eine One-Click-Diagnose (Tests + Codequalität) mit Ergebnisanzeige.
- Doku-Autoupdater aktualisiert Statusblöcke in README/DEV_DOKU.
- Modul-API-Typen (TypedDicts) sind zentral dokumentiert.
- Modulverbund-Checks führen Selftests aus und blockieren defekte Module.
- Start-Routine zeigt am Ende einen Ampelstatus (grün/rot).
- Recovery-Modus steht als separates Skript für Notfallstarts bereit.

<!-- AUTO-STATUS:START -->
**Auto-Status (aktualisiert: 2026-01-14)**

- Gesamt: 89 Tasks
- Erledigt: 89 Tasks
- Offen: 0 Tasks
- Fortschritt: 100,00 %
<!-- AUTO-STATUS:END -->

## Struktur (aktuell)
Die **vollständige** Struktur steht in `STRUKTUR.md` (Single Source of Truth).
Hier nur die wichtigsten Bereiche:
- `PROJEKT_INFO.md`: Übersicht zu Ordnerstruktur und Tooldateien.
- `ANALYSE_BERICHT.md`: Analysebericht zu Risiken, Lücken und Best Practices.
- `STRUKTUR.md`: Verzeichnisbaum inkl. Pflicht- und Dummy-Dateien.
- `README.md`: Schnellstart, Ziele und Hinweise.
- `config/`: Konfiguration (z. B. Themes, Module, Test-Gate).
- `data/`: Variable Daten (z. B. Logs, Zustände, Platzhalterdateien).
- `logs/`: Laufzeit-Logs (Test- und Startprotokolle).
- `modules/`: Module mit `manifest.json` + `module.py`.
- `reports/`: Prüfberichte (z. B. Kontrastprüfung).
- `scripts/`: Start-, Test- und Diagnose-Skripte.
- `src/` und `system/`: Kernlogik und System-Tools.
- `tests/`: Automatisierte Tests.
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
- Einheitliche Benennung für Dateien/Module (snake_case, Modul-ID = Ordnername, Pflichtdateien manifest.json + module.py).
- Modul-Pfade in `config/modules.json` zeigen auf Modulordner (nicht auf einzelne Dateien).
- Notiz-Editor und Charakter-Modul nutzen Templates, Themes und Dashboard-Statistiken.

## Qualitätssicherung
- **Tests**: Automatische Tests für Kernfunktionen (Start erst nach kompletter Runde).
- **Codequalität (Linting)**: Ruff prüft Fehler und Stilregeln automatisch.
- **Formatierung**: Black prüft den Code auf einheitliches Format.
- **Prüfungen**: Start-Routine prüft Struktur und Abhängigkeiten automatisch.
- **Prüfungen**: Struktur-Check stellt Trennung von System/Config/Daten/Logs sicher.
- **Prüfungen**: System-Scan bietet eine Vorabprüfung ohne Schreibzugriff.
- **Prüfungen**: Modul-Check validiert aktivierte Module und deren Manifest.
- **Prüfungen**: Modul-API-Validator prüft Pflichtfunktionen ohne Modul-Import.
- **Prüfungen**: Modul-Selbsttests melden Status pro Modul (GUI und CLI).
- **Prüfungen**: Modulverbund-Checks prüfen Selftests, IDs und Manifest-Konsistenz.
- **Prüfungen**: Fehler-Simulation zeigt typische Laienfehler mit Lösungshinweis.

## Dokumentationsregeln
- Änderungen werden im `CHANGELOG.md` beschrieben.
- Abgeschlossene Aufgaben kommen nach `DONE.md`.
- Fortschritt wird in `PROGRESS.md` aktualisiert.
- `PROJEKT_INFO.md` ist Pflicht und wird bei Struktur- oder Tool-Änderungen aktualisiert.
- Release-Checkliste für die GUI wird in `todo.txt` gepflegt und in TODO.md gespiegelt.
- TODO.md enthält die vollständige Aufgabenstruktur (IDs + Bereiche) inkl. Kurzliste aus todo.txt.

## Bauen/Starten/Testen
### Fortschritt aus todo.txt berechnen
1. `python system/todo_manager.py progress`
2. Optional: `python system/todo_manager.py progress --write-progress` (schreibt PROGRESS.md)

### Start-Routine (Struktur + Fortschritt)
1. `./scripts/start.sh`
2. Die Start-Routine erstellt fehlende Ordner automatisch, führt den Health-Check mit Selbstreparatur aus, prüft JSONs, korrigiert Dateinamen, prüft Abhängigkeiten, prüft Module und zeigt den Fortschritt in Prozent.
3. Tests laufen automatisch, sobald eine Runde (4 erledigte Tasks) erreicht ist.
4. Optional: `./scripts/start.sh --debug` (Debugging = detaillierte Diagnoseausgaben).
5. Optional: `./scripts/start.sh --log-file logs/start_run.log` (Logdatei festlegen).
6. Optional: `./scripts/start.sh --safe-mode` (schreibgeschützt, keine Änderungen).
7. Optional: `./scripts/start.sh --ghost-mode` (Alias für Safe-Mode).
8. Optional: `./scripts/start.sh --sandbox` (isolierte Sandbox, Schreibzugriffe nur dort).
9. Notfall: `./scripts/recovery.sh` (Recovery-Modus mit Reparatur und Minimalchecks).

### System-Scan (Vorabprüfung ohne Schreiben)
1. `./scripts/system_scan.sh`
2. Optional: `./scripts/system_scan.sh --debug` (Debugging = detaillierte Diagnoseausgaben).

### Setup-Skripte (separat ausführbar)
1. `./scripts/check_env.sh` (Voraussetzungen prüfen)
2. `./scripts/bootstrap.sh` (Basis-Ordner anlegen)

### Health-Check (manuell)
1. `python system/health_check.py --root . --self-repair`
2. Optional: `python system/health_check.py --root . --self-repair --debug` (Debugging = detaillierte Diagnose-Ausgaben).

### Tests + Codequalität (manuell)
1. `./scripts/run_tests.sh`
2. Führt Pytest, Ruff (Linting) und Black (Formatprüfung) in dieser Reihenfolge aus.
3. Vor den Tests laufen Modulverbund-Checks (Selftests + Manifest-IDs).
4. Hinweis: Details zu Fehlern stehen im Fehlerprotokoll (Log) unter `logs/test_run.log`.
5. Hilfe: `./scripts/run_tests.sh --help` zeigt den geführten Ablauf.
6. Optional: `./scripts/run_tests.sh --help` (kurze Erklärung für Laien).

### Diagnose (One-Click)
1. GUI-Launcher: Button „Diagnose starten“ ausführen.
2. CLI: `python system/diagnostics_runner.py` (Diagnose = Tests + Codequalität).
3. Ergebnis: Zusammenfassung + Ausgabe im Textbereich/Terminal.

### Doku-Update (Auto-Status)
1. `./scripts/update_docs.sh`
2. Aktualisiert die Auto-Status-Blöcke in `README.md` und `DEV_DOKU.md`.

### Modul-Selbsttests (manuell)
1. `python system/module_selftests.py`
2. Zeigt pro Modul einen Status (ok/fehler/übersprungen) an.

### Fehler-Simulation (manuell)
1. `python system/error_simulation.py`
2. Zeigt typische Laienfehler mit Meldung und Lösungsschritt an.

### Kontrastbericht (Launcher-Themes)
1. `python scripts/generate_launcher_gui_contrast_report.py`
2. Der Bericht wird unter `reports/kontrastpruefung_launcher_gui.md` gespeichert.

### Themes & Kontrast (Pflege)
1. Launcher-Themes stehen in `config/launcher_gui.json` (z. B. `hell`, `dunkel`, `kontrast`).
2. Modul-Themes stehen in `config/<modul>.json` unter `themes`.
3. Pflicht: Mindestens ein Kontrast-Theme pro Modul/Launcher.
4. Tipp: Vor Änderungen den Kontrastbericht ausführen.

### Abhängigkeiten (manuell prüfen)
1. `python system/dependency_checker.py --requirements config/requirements.txt`
2. Optional: `python system/dependency_checker.py --requirements config/requirements.txt --no-auto-install`

### JSON-Validator (manuell)
1. `python system/json_validator.py --root .`
2. Optional: `python system/json_validator.py --root . --strict` (stoppt beim ersten Fehler).

### Dateinamen-Korrektur (manuell)
1. `python system/filename_fixer.py --root .`
2. Optional: `python system/filename_fixer.py --root . --dry-run` (nur anzeigen).

### Repo-Basis-Check (Push-Trockenlauf)
1. `./scripts/repo_basis_check.sh`
2. Hinweis: Bei fehlendem Remote erscheint eine klare Lösungsmeldung.

### Klick&Start (für Laien)
1. `./klick_start.sh`
2. Die Start-Routine läuft automatisch, danach öffnet sich die GUI-Startübersicht.
3. Optional: `./klick_start.sh --debug` (Debugging = detaillierte Diagnoseausgaben).
4. Optional: `./klick_start.sh --log-file logs/start_run.log` (Logdatei festlegen).

### Launcher (Modulübersicht)
1. `python system/launcher.py`
2. Optional: `python system/launcher.py --show-all` (zeigt auch deaktivierte Module).

### GUI-Launcher (Startübersicht)
1. `python system/launcher_gui.py`
2. Optional: `python system/launcher_gui.py --show-all --debug` (Details anzeigen).
3. Tastatur-Shortcuts: Alt+A (alle Module), Alt+D (Debug), Alt+R (aktualisieren), Alt+G (Diagnose), Alt+T (Theme), Alt+K (Kontrast), Alt+Q (beenden).
4. Zoom: Strg + Mausrad (Zoom = Schriftgröße vergrößern/verkleinern).
5. Modul-Check: Wird bei jeder Aktualisierung automatisch ausgeführt (Status steht in der Übersicht).
6. UI-Abstände anpassen: `config/launcher_gui.json` → `layout.*` (Spacing = Abstände).
### Modul-Check (manuell)
1. `python system/module_checker.py --config config/modules.json`
2. Modul-IDs sind `snake_case` und Pfade müssen `modules/<modul_id>` entsprechen.
3. Bei Fehlern werden klare Hinweise und Lösungsvorschläge ausgegeben.

### Test-Sperre (manuell)
1. `python system/test_gate.py --config config/test_gate.json`
2. Tests starten erst nach kompletter Runde (4 Tasks), sonst erscheint ein Hinweis.

### Log-Export (ZIP)
1. `python system/log_exporter.py`
2. Optional: `python system/log_exporter.py --logs-dir logs --export-dir data/log_exports`

### Standards anzeigen (im Tool)
1. `./scripts/show_standards.sh --list`
2. `./scripts/show_standards.sh --section standards`
3. `./scripts/show_standards.sh --section styleguide`

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
