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
  - `scripts/update_records.py`: Startet die automatische Archivierung.

## Regeln für automatische Einträge
- Ein Eintrag wird erzeugt, wenn eine To-Do-Zeile mit `[x]` markiert ist.
- Das Datum muss im Format `JJJJ-MM-TT` stehen.
- Der Bereich und der Titel dürfen nicht leer sein.
- **DONE.md** erhält den vollständigen Task-Eintrag.
- **CHANGELOG.md** bekommt einen Eintrag im Abschnitt **[Unreleased]** mit Datum und Inhalt.

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

## UI-Standards (aktuell umgesetzt)
- **Farben/Themes**: zentrale Theme-Definition in `gms-archiv-tool_v1.2.3_2026-01-06/src/App.jsx` (THEMES).
- **Abstände**: feste Skala 4/8/16/24/32 in `gms-archiv-tool_v1.2.3_2026-01-06/src/index.css` (CSS-Variablen).
- **Kontrast (WCAG)**: Mindestziel 4,5:1 für Fließtext, 3:1 für UI-Elemente; Muted-Farben wurden angehoben.

## Qualitätssicherung
- **Tests**: Automatische Tests für Kernfunktionen.
- **Formatierung**: Automatische Codeformatierung (einheitlicher Stil).
- **Prüfungen**: Start-Routine prüft Struktur und Abhängigkeiten.
- **Validierung**: Import-Daten werden beim Einlesen geprüft (z. B. Datumsformat).
- **Self-Test im Tool**: Optionaler Selbsttest nach einer Runde (2 erledigte Aufgaben), aktivierbar in den Einstellungen.
- **Tests**: Self-Test inkl. Start-Check (Module, Speicher, Basisdaten).
- **Formatierung**: Vite/Tailwind Standard-Setup.
- **Prüfungen**: Start-Check meldet Fehler/Hinweise in der Diagnose.

## Dokumentationsregeln
- Änderungen werden im `CHANGELOG.md` beschrieben.
- Abgeschlossene Aufgaben kommen nach `DONE.md`.
- Fortschritt wird in `PROGRESS.md` aktualisiert.

## Bauen/Starten/Testen
Aktuell gibt es keine zentrale Start-Routine im Repo. Für das UI-Modul:
- `cd gms-archiv-tool_v1.2.3_2026-01-06`
- `npm run build` (Build-Check für die UI)
