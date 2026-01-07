# DEV_DOKU

## Zweck
Diese Dokumentation richtet sich an Entwicklerinnen und Entwickler. Sie beschreibt Struktur, Standards und den geplanten Ablauf.

## Projektstatus
- Derzeit liegt der Fokus auf Dokumentation und Aufgabenplanung.
- Start-Routine, Tests und Modul-Standards werden in den nächsten Tasks umgesetzt.

## Struktur (geplant)
- `src/`: Systemlogik (stabile Kernlogik).
- `config/`: Konfiguration (änderbar ohne Code).
- `data/`: Variable Daten und Laufzeitdateien.
- `scripts/`: Start- und Prüfskripte.

## Standards (geplant)
- Einheitliche Modul-Schnittstellen (Init/Exit).
- Zentrales Datenmodell.
- Barrierefreie UI-Texte (Deutsch, klar, laienverständlich).

## Fortschritt (Zählregel)
- Als Task zählt jede Zeile in `todo.txt`, die mit `[ ]` oder `[x]` beginnt.
- **Erledigt** ist eine Zeile mit `[x]` (Groß/Klein egal).
- **Offen** ist eine Zeile mit `[ ]`.

## Qualitätssicherung
- **Tests**: Automatische Tests für Kernfunktionen.
- **Formatierung**: Automatische Codeformatierung (einheitlicher Stil).
- **Prüfungen**: Start-Routine prüft Struktur und Abhängigkeiten.

## Dokumentationsregeln
- Änderungen werden im `CHANGELOG.md` beschrieben.
- Abgeschlossene Aufgaben kommen nach `DONE.md`.
- Fortschritt wird in `PROGRESS.md` aktualisiert.

## Bauen/Starten/Testen
### Start (Fortschritt aktualisieren)
- `./scripts/start.sh` (berechnet den Fortschritt aus `todo.txt` und aktualisiert `PROGRESS.md`).

### Check (Fortschritt prüfen)
- `node scripts/progress.js --check` (prüft, ob `PROGRESS.md` zu `todo.txt` passt).
