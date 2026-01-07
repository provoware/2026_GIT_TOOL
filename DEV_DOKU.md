# DEV_DOKU

## Zweck
Diese Dokumentation richtet sich an Entwicklerinnen und Entwickler. Sie beschreibt Struktur, Standards und den geplanten Ablauf.

## Projektstatus
- Derzeit liegt der Fokus auf Dokumentation und Aufgabenplanung.
- Start-Routine und Tests werden in den nächsten Tasks umgesetzt.

## Struktur (geplant)
- `src/`: Systemlogik (stabile Kernlogik).
- `config/`: Konfiguration (änderbar ohne Code).
- `data/`: Variable Daten und Laufzeitdateien.
- `scripts/`: Start- und Prüfskripte.

## Standards (verbindlich)
- Zentrale Standards stehen in `standards.md`.
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
