# PROJEKT_INFO

## Zweck
Diese Datei gibt eine **kurze Übersicht** zur Ordnerstruktur und zu wichtigen Tooldateien.
Bitte **bei jeder Struktur- oder Tool-Änderung** mit aktualisieren.

## Ordnerstruktur (Top-Level)
- `config/`: Konfigurationen (Einstellungen, Regeln, Themes).
- `data/`: Nutzdaten und Protokolle (z. B. Moduldaten, Logs).
- `logs/`: Laufzeit-Logs (z. B. Testprotokolle).
- `modules/`: Module nach Standard (Manifest + Entry-Datei).
- `scripts/`: Start- und Prüfskripte.
- `src/`: Kernlogik (stabile System-Logik).
- `system/`: Tool-Logik (CLI-Tools, Checks, Launcher).
- `tests/`: Automatische Tests (Unit-Tests).
- `gms-archiv-tool_v1.2.3_2026-01-06/`: UI-Frontend (separates Projekt).

## Tooldateien (wichtige Einstiege)
- `klick_start.sh`: Startet die komplette Start-Routine und öffnet die GUI-Übersicht.
- `scripts/start.sh`: Führt die Start-Routine (Health-Check, Struktur, Abhängigkeiten) aus.
- `scripts/run_tests.sh`: Führt Tests, Codequalität (Linting) und Formatprüfung aus.
- `scripts/repo_basis_check.sh`: Prüft Git-Setup (Remote + Push-Trockenlauf).
- `system/launcher.py`: CLI-Launcher (Modulübersicht).
- `system/launcher_gui.py`: GUI-Launcher (Startübersicht mit Themes).
- `system/health_check.py`: Health-Check (Pflichtdateien/Ordner prüfen).
- `system/dependency_checker.py`: Abhängigkeiten prüfen und installieren.
- `system/module_checker.py`: Modul-Check (Manifest + Entry-Datei validieren).
- `system/todo_manager.py`: Fortschritt berechnen und To-Dos archivieren.
- `system/log_exporter.py`: Logdateien als ZIP exportieren.

## Aktualisierungspflicht
- **Bei Ordneränderungen**: Abschnitt „Ordnerstruktur“ aktualisieren.
- **Bei neuen/entfernten Tools**: Abschnitt „Tooldateien“ aktualisieren.
- **Bei neuen Einstiegen**: Startbefehle in DEV_DOKU.md ergänzen.
