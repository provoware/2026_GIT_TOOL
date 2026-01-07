# DEV_DOKU

## Zweck
Diese Dokumentation richtet sich an Entwicklerinnen und Entwickler. Sie beschreibt Struktur, Standards und den geplanten Ablauf.

## Projektstatus
- Derzeit liegt der Fokus auf Dokumentation und Aufgabenplanung.
- Start-Routine, Tests und Modul-Standards werden schrittweise umgesetzt.
- Start-Check und Modul-Check sind umgesetzt und in der Diagnose sichtbar.
- Modul-Check wird im Self-Test mit einem defekten Modul automatisch geprüft.

## Struktur (geplant)
- `system/`: Systemlogik (stabile Kernlogik).
- `config/`: Konfiguration (änderbar ohne Code).
- `data/`: Variable Daten und Laufzeitdateien.
- `tests/`: Automatische Tests.
## Struktur (aktuell)
- `gms-archiv-tool_v1.2.3_2026-01-06/src/system/`: Systemlogik (Start-Checks).
- `gms-archiv-tool_v1.2.3_2026-01-06/src/config/`: Konfiguration (Modul-Definitionen).
- `gms-archiv-tool_v1.2.3_2026-01-06/src/`: App-UI und Kernlogik.

## Standards (verbindlich)
- Zentrale Standards sind in `standards.md` beschrieben.
- Einheitliche Modul-Schnittstellen (Init/Exit).
- Zentrales Datenmodell.
- Barrierefreie UI-Texte (Deutsch, klar, laienverständlich).
- Fehlermeldungen folgen dem Format: Titel + Erklärung + Lösung.
## Standards (teilweise umgesetzt)
- Modul-Schnittstelle wird beim Start geprüft (Id, Name, Start-Funktion).
- Barrierefreie UI-Texte: Deutsch, klar, laienverständlich.

## Fortschritt (Zählregel)
- Als Task zählt jede Zeile in `todo.txt`, die mit `[ ]` oder `[x]` beginnt.
- **Erledigt** ist eine Zeile mit `[x]` (Groß/Klein egal).
- **Offen** ist eine Zeile mit `[ ]`.

## Qualitätssicherung
- **Tests**: Automatische Tests für Kernfunktionen.
- **Formatierung**: Automatische Codeformatierung (einheitlicher Stil).
- **Prüfungen**: Start-Routine prüft Struktur und Abhängigkeiten.
- **Self-Test im Tool**: Optionaler Selbsttest nach einer Runde (2 erledigte Aufgaben), aktivierbar in den Einstellungen.
- **Tests**: Self-Test inkl. Start-Check (Module, Speicher, Basisdaten).
- **Formatierung**: Vite/Tailwind Standard-Setup.
- **Prüfungen**: Start-Check meldet Fehler/Hinweise in der Diagnose.

## Dokumentationsregeln
- Änderungen werden im `CHANGELOG.md` beschrieben.
- Abgeschlossene Aufgaben kommen nach `DONE.md`.
- Fortschritt wird in `PROGRESS.md` aktualisiert.

## Bauen/Starten/Testen
### Start (Fortschritt aktualisieren)
- `./scripts/start.sh` (berechnet den Fortschritt aus `todo.txt` und aktualisiert `PROGRESS.md`).

### Check (Fortschritt prüfen)
- `node scripts/progress.js --check` (prüft, ob `PROGRESS.md` zu `todo.txt` passt).
### To-Do-Manager (CLI)
- **Fortschritt prüfen**: `python system/todo_manager.py progress`
- **Archivieren**: `python system/todo_manager.py archive`
- **Debug-Modus**: `python system/todo_manager.py progress --debug`
- **Konfiguration**: `config/todo_config.json` (Pfad zu `todo.txt` und Archivdatei)

### Tests
- `python -m unittest discover -s tests`
### Lokales Frontend (GMS Archiv Tool)
```bash
cd gms-archiv-tool_v1.2.3_2026-01-06
npm install
npm run dev
```

### Build-Check
```bash
cd gms-archiv-tool_v1.2.3_2026-01-06
npm run build
```
- Build: `npm -C gms-archiv-tool_v1.2.3_2026-01-06 run build`
- Dev-Start: `npm -C gms-archiv-tool_v1.2.3_2026-01-06 run dev`
- Diagnose: Start-Check oder Self-Test im UI ausführen.
Aktuell gibt es keine lauffähigen Skripte. Diese Sektion wird ergänzt, sobald Start- und Testscripte existieren.

Letzte Prüfung (manuell):
- UI-Textprüfung (Deutsch/Fehlerstil) im Projekt-Übersichtstool.
