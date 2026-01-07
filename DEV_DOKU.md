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

## Qualitätssicherung
- **Tests**: Automatische Tests für Kernfunktionen.
- **Formatierung**: Automatische Codeformatierung (einheitlicher Stil).
- **Prüfungen**: Start-Routine prüft Struktur und Abhängigkeiten.

## Dokumentationsregeln
- Änderungen werden im `CHANGELOG.md` beschrieben.
- Abgeschlossene Aufgaben kommen nach `DONE.md`.
- Fortschritt wird in `PROGRESS.md` aktualisiert.

## Bauen/Starten/Testen
### GMS Archiv Tool (Frontend)
**Voraussetzung:** Node.js (Laufzeitumgebung für JavaScript).

- Start (Entwicklung):
  - `cd gms-archiv-tool_v1.2.3_2026-01-06`
  - `npm run dev -- --host 0.0.0.0 --port 4173`
- Build (Produktions-Build):
  - `cd gms-archiv-tool_v1.2.3_2026-01-06`
  - `npm run build`

### Manuelle Checks
- Log-Export prüfen: Im Dashboard den Button **„Logs exportieren“** klicken → eine `.json`-Datei wird heruntergeladen.
