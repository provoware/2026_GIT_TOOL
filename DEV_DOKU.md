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

## UI-Standards (aktuell umgesetzt)
- **Farben/Themes**: zentrale Theme-Definition in `gms-archiv-tool_v1.2.3_2026-01-06/src/App.jsx` (THEMES).
- **Abstände**: feste Skala 4/8/16/24/32 in `gms-archiv-tool_v1.2.3_2026-01-06/src/index.css` (CSS-Variablen).
- **Kontrast (WCAG)**: Mindestziel 4,5:1 für Fließtext, 3:1 für UI-Elemente; Muted-Farben wurden angehoben.

## Qualitätssicherung
- **Tests**: Automatische Tests für Kernfunktionen.
- **Formatierung**: Automatische Codeformatierung (einheitlicher Stil).
- **Prüfungen**: Start-Routine prüft Struktur und Abhängigkeiten.

## Dokumentationsregeln
- Änderungen werden im `CHANGELOG.md` beschrieben.
- Abgeschlossene Aufgaben kommen nach `DONE.md`.
- Fortschritt wird in `PROGRESS.md` aktualisiert.

## Bauen/Starten/Testen
Aktuell gibt es keine zentrale Start-Routine im Repo. Für das UI-Modul:
- `cd gms-archiv-tool_v1.2.3_2026-01-06`
- `npm run build` (Build-Check für die UI)
