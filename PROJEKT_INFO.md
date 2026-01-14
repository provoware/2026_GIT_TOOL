# PROJEKT_INFO

## Zweck
Diese Datei gibt eine **kurze Übersicht** zur Ordnerstruktur und zu wichtigen Tooldateien.
Bitte **bei jeder Struktur- oder Tool-Änderung** mit aktualisieren.
Die vollständige Struktur steht in `STRUKTUR.md`.

## Ordnerstruktur (Top-Level)
- `config/`: Konfigurationen (Einstellungen, Regeln, Themes). Änderbar ohne Code.
- `data/`: Nutzdaten und Protokolle (z. B. Moduldaten, Logs).
- `logs/`: Laufzeit-Logs (z. B. Testprotokolle).
- `modules/`: Module nach Standard (Manifest + Entry-Datei).
- `reports/`: Prüfberichte (z. B. Kontrastprüfungen).
- `scripts/`: Start- und Prüfskripte (Automatisierung).
- `src/`: Kernlogik (stabile System-Logik, unabhängig von Config).
- `system/`: Tool-Logik (CLI-Tools, Checks, Launcher).
- `tests/`: Automatische Tests (Unit-Tests).
- `gms-archiv-tool_v1.2.3_2026-01-06/`: UI-Frontend (separates Projekt).

## Tooldateien (wichtige Einstiege)
- `klick_start.sh`: Startet die komplette Start-Routine und öffnet die GUI-Übersicht.
- `scripts/start.sh`: Führt die Start-Routine (Health-Check, Struktur, Abhängigkeiten) aus.
- `scripts/system_scan.sh`: System-Scan (Vorabprüfung ohne Schreiben).
- `scripts/run_tests.sh`: Führt Tests, Codequalität (Linting) und Formatprüfung aus.
- `scripts/update_docs.sh`: Aktualisiert Auto-Status in README und DEV_DOKU.
- `scripts/repo_basis_check.sh`: Prüft Git-Setup (Remote + Push-Trockenlauf).
- `scripts/generate_launcher_gui_contrast_report.py`: Erstellt den Kontrastbericht für den GUI-Launcher.
- `system/launcher.py`: CLI-Launcher (Modulübersicht).
- `system/launcher_gui.py`: GUI-Launcher (Startübersicht mit Themes).
- `system/health_check.py`: Health-Check (Pflichtdateien/Ordner prüfen).
- `system/structure_checker.py`: Struktur-Check (Trennung von System/Config/Daten/Logs).
- `system/dependency_checker.py`: Abhängigkeiten (Dependencies) prüfen und installieren.
- `system/diagnostics_runner.py`: One-Click-Diagnose (Tests + Codequalität mit Zusammenfassung).
- `system/module_checker.py`: Modul-Check (Manifest + Entry-Datei validieren).
- `system/module_registry.py`: Modul-Registry (Plugin-System) für zentrales Laden.
- `system/store.py`: Zentraler Store für gemeinsame Zustände.
- `system/config_models.py`: Geprüfte Konfigurationsmodelle (GUI/Module).
- `system/logging_center.py`: Zentrales asynchrones Logging.
- `system/module_loader.py`: Lazy Loader für Modul-Imports (Caching).
- `system/module_api_types.py`: Standard-Typen für Modul-Input/Output.
- `system/doc_updater.py`: Doku-Autoupdater für Auto-Status-Blöcke.
- `system/todo_manager.py`: Fortschritt berechnen und To-Dos archivieren.
- `system/log_exporter.py`: Logdateien als ZIP exportieren.
- `ANLEITUNG_TOOL.md`: Laienfreundliche Tool-Anleitung (Schritte, Tipps, FAQ).
- `docs/MODUL_API.md`: Modul-API (Schnittstellen, Events, States) mit Beispiel.
- `STRUKTUR.md`: Verzeichnisbaum + Pflichtdateien (inkl. Dummy-Platzhalter).

## Automatik: Was beim Start geprüft wird
Die Start-Routine führt eine **vollautomatische Prüfung (Check)** aus und gibt **klare Rückmeldungen (Feedback)**:
1. **Health-Check**: Pflichtdateien und Ordner werden geprüft, fehlende Elemente werden bei Bedarf erstellt.
2. **Struktur-Check**: Projektordner werden geprüft und Trennung wird validiert.
3. **Abhängigkeits-Check**: `config/requirements.txt` wird geprüft; fehlende Pakete werden installiert.
4. **Modul-Check**: Module werden validiert (Manifest, Entry, Pfad-Sicherheit).
5. **Fortschritt**: Der Fortschritt aus `todo.txt` wird berechnet und angezeigt.

Hinweis zu Start-Modi:
- **Safe-Mode** (`./scripts/start.sh --safe-mode`): Nur prüfen, keine Schreibzugriffe.
- **Ghost-Mode** (`./scripts/start.sh --ghost-mode`): Alias für Safe-Mode.
- **Sandbox** (`./scripts/start.sh --sandbox`): Isolierte Kopie, Schreibzugriffe bleiben dort.

## Barrierefreiheit und Qualität (Kurzstandard)
- **Tastaturbedienung**: Alle Funktionen müssen ohne Maus erreichbar sein.
- **Kontrast**: Themes mit hoher Lesbarkeit (Ziel: 4,5:1) bereitstellen.
- **Validierung**: Jede Funktion prüft Eingaben (Input) und Ergebnisse (Output).
- **Logging**: Aktionen werden protokolliert; Debug-Modus (Debugging) zeigt Details.

## Weiterführende Hinweise für Laien
- **Starten**: `./klick_start.sh` nutzt alle Prüfungen automatisch.
- **Fehler verstehen**: Fehlermeldungen nennen Ursache + Lösungsschritt.
- **Hilfe ansehen**: `./scripts/run_tests.sh --help` erklärt den Testlauf Schritt für Schritt.
- **Logs prüfen**: Bei Problemen zuerst `logs/test_run.log` öffnen.

## Aktualisierungspflicht
- **Bei Ordneränderungen**: Abschnitt „Ordnerstruktur“ aktualisieren.
- **Bei neuen/entfernten Tools**: Abschnitt „Tooldateien“ aktualisieren.
- **Bei neuen Einstiegen**: Startbefehle in DEV_DOKU.md ergänzen.
