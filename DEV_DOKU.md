# DEV_DOKU

## Zweck
Diese Dokumentation richtet sich an Entwicklerinnen und Entwickler. Sie beschreibt Struktur, Standards und den geplanten Ablauf.

## Projektstatus
- Derzeit liegt der Fokus auf Dokumentation und Aufgabenplanung.
- Start-Routine, Tests und Modul-Standards werden in den nächsten Tasks umgesetzt.

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

## Standards (geplant)
- Einheitliche Modul-Schnittstellen (Init/Exit).
- Zentrales Datenmodell.
- Barrierefreie UI-Texte (Deutsch, klar, laienverständlich).

## Qualitätssicherung
- **Tests**: Automatische Tests für Kernfunktionen.
- **Formatierung**: Automatische Codeformatierung (einheitlicher Stil).
- **Prüfungen**: Start-Routine prüft Struktur und Abhängigkeiten.

## Dokumentationsregeln
- Änderungen werden im `CHANGELOG.md` beschrieben.
- Abgeschlossene Aufgaben kommen nach `DONE.md`.
- Fortschritt wird in `PROGRESS.md` aktualisiert.

## Bauen/Starten/Testen
Aktuell gibt es keine Start-Routine für das gesamte Projekt.

**Einträge archivieren und Changelog ergänzen**:
- `python scripts/update_records.py`
- Optionaler Testlauf (Dry-Run = Probelauf ohne Schreiben): `python scripts/update_records.py --dry-run`
