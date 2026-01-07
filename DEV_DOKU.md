# DEV_DOKU

## Zweck
Diese Dokumentation richtet sich an Entwicklerinnen und Entwickler. Sie beschreibt Struktur, Standards und den geplanten Ablauf.

## Projektstatus
- Start-Routine prüft die Projektstruktur und erstellt fehlende Ordner.
- Tests und Modul-Standards werden in den nächsten Tasks umgesetzt.

## Struktur (geplant)
- `src/`: Systemlogik (stabile Kernlogik).
- `config/`: Konfiguration (änderbar ohne Code).
- `data/`: Variable Daten und Laufzeitdateien.
- `logs/`: Protokolle (Log-Dateien).
- `scripts/`: Start- und Prüfskripte.

## Standards (geplant)
- Einheitliche Modul-Schnittstellen (Init/Exit).
- Zentrales Datenmodell.
- Barrierefreie UI-Texte (Deutsch, klar, laienverständlich).

## Qualitätssicherung
- **Tests**: Automatische Tests für Kernfunktionen.
- **Formatierung**: Automatische Codeformatierung (einheitlicher Stil).
- **Prüfungen**: Start-Routine prüft Struktur und legt fehlende Ordner an.

## Dokumentationsregeln
- Änderungen werden im `CHANGELOG.md` beschrieben.
- Abgeschlossene Aufgaben kommen nach `DONE.md`.
- Fortschritt wird in `PROGRESS.md` aktualisiert.

## Bauen/Starten/Testen
### Start-Check (Projektstruktur)
```bash
cd gms-archiv-tool_v1.2.3_2026-01-06
npm run start-check
```

Optionaler Trockenlauf (dry run):
```bash
cd gms-archiv-tool_v1.2.3_2026-01-06
npm run start-check -- --dry-run
```

### Lokaler Start (Entwicklung)
```bash
cd gms-archiv-tool_v1.2.3_2026-01-06
npm run dev
```
