# DEV_DOKU

## Zweck
Diese Dokumentation richtet sich an Entwicklerinnen und Entwickler. Sie beschreibt Struktur, Standards und den geplanten Ablauf.

## Projektstatus
- Der Fokus liegt aktuell auf stabilen Start- und Test-Abläufen.
- Erste automatische Tests (Tests/automatische Prüfungen) sind eingerichtet.

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
- **Tests**: Automatische Tests (Tests/automatische Prüfungen) für Kernfunktionen.
- **Formatierung**: Einheitlicher Stil durch feste Regeln (Formatierung/einheitliches Layout).
- **Prüfungen**: Start-Routine prüft Struktur und Daten.

## Dokumentationsregeln
- Änderungen werden im `CHANGELOG.md` beschrieben.
- Abgeschlossene Aufgaben kommen nach `DONE.md`.
- Fortschritt wird in `PROGRESS.md` aktualisiert.

## Bauen/Starten/Testen
Alle Befehle bitte im Ordner `gms-archiv-tool_v1.2.3_2026-01-06` ausführen:

1. Abhängigkeiten installieren (Dependencies/benötigte Pakete):
   - `npm install`
2. Tests ausführen (Vitest/Test-Runner):
   - `npm test`
3. Entwicklungsstart (Dev-Server/Entwicklungsserver):
   - `npm run dev`
4. Produktion bauen (Build/Release-Build):
   - `npm run build`
5. Vorschau starten (Preview/Vorschau):
   - `npm run preview`
