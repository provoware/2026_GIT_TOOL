# DEV_DOKU

## Zweck
Diese Dokumentation richtet sich an Entwicklerinnen und Entwickler. Sie beschreibt Struktur, Standards und den geplanten Ablauf.

## Projektstatus
- Start-Routine prüft die Projektstruktur und erstellt fehlende Ordner.
- Tests und Modul-Standards werden in den nächsten Tasks umgesetzt.
- Der Fokus liegt aktuell auf stabilen Start- und Test-Abläufen.
- Erste automatische Tests (Tests/automatische Prüfungen) sind eingerichtet.
- Derzeit liegt der Fokus auf Dokumentation und Aufgabenplanung.
- Die Startroutine prüft beim Start Browser, Speicher und Datenmodell mit Fortschrittsanzeige.
- Weitere Tests und Modul-Standards folgen in den nächsten Tasks.
- Start-Routine und Tests werden in den nächsten Tasks umgesetzt.

## Struktur (geplant)
- `src/`: Systemlogik (stabile Kernlogik).
- `config/`: Konfiguration (änderbar ohne Code).
- `data/`: Variable Daten und Laufzeitdateien.
- `logs/`: Protokolle (Log-Dateien).
- `scripts/`: Start- und Prüfskripte.

## Standards (verbindlich)
- Zentrale Standards stehen in `standards.md`.
- Einheitliche Modul-Schnittstellen (Init/Exit).
- Zentrales Datenmodell (`data/schema.json`).
## Standards (verbindlich)
- Siehe `standards.md` für verbindliche Vorgaben.
- Einheitliche Modul-Schnittstellen (Init/Exit, Run, Shutdown).
- Barrierefreie UI-Texte (Deutsch, klar, laienverständlich).
- Verbindliche Regeln in `standards.md`.

## Qualitätssicherung
- **Tests**: Automatische Tests für Kernfunktionen.
- **Formatierung**: Automatische Codeformatierung (einheitlicher Stil).
- **Prüfungen**: Start-Routine prüft Struktur und legt fehlende Ordner an.
- **Tests**: Automatische Tests (Tests/automatische Prüfungen) für Kernfunktionen.
- **Formatierung**: Einheitlicher Stil durch feste Regeln (Formatierung/einheitliches Layout).
- **Prüfungen**: Start-Routine prüft Struktur und Daten.

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
### Start (lokal)
1. In das Projekt wechseln: `cd gms-archiv-tool_v1.2.3_2026-01-06`
2. Starten: `npm run dev`

### Build (lokal)
1. In das Projekt wechseln: `cd gms-archiv-tool_v1.2.3_2026-01-06`
2. Build ausführen: `npm run build`
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
### Minimaler Startlauf (Beispiel)
Projektordner für das Frontend: `gms-archiv-tool_v1.2.3_2026-01-06`
1) Abhängigkeiten installieren (Dependencies):
   `npm install`
2) Entwicklungsstart (Development-Server):
   `npm run dev`
3) Build (kompiliertes Paket):
   `npm run build`
4) Vorschau (Preview) des Builds:
   `npm run preview`

Hinweis: Aktuell gibt es kein `npm test`. Tests werden ergänzt, sobald Testskripte vorhanden sind.

### Push-Probe (Prüfung)
1) Branch prüfen:
   `git branch --show-current`
2) Push ausführen (Übertragung zum Remote):
   `git push origin <branch>`

**Prüfkriterium:** Push erfolgreich (keine Fehlermeldung, Remote nimmt die Änderung an).

### Remote prüfen (Sollzustand)
Mit `git remote -v` prüfen, ob ein Remote gesetzt ist. Wenn keiner vorhanden ist, muss ein Remote hinzugefügt werden (z. B. `git remote add origin <url>`).
