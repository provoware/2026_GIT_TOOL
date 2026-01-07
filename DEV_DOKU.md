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
- `tests/`: Automatische Tests (Unit-Tests).

## Standards (aktuell)
- Einheitliche To-Do-Validierung (Formatprüfung).
- Agent-Zuordnung über zentrale Regeldatei (`config/agent_rules.json`).
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

## Fehlerstandard (aktuell)
Einheitliches Format für Nutzer-Fehlermeldungen:

```
Fehler <Code>: <Titel> (<Fachbegriff/Technik).
Erklärung: <kurz und einfach>.
Nächster Schritt: <konkrete nächste Aktion>.
Details: <optional>.
```

Aktive Fehlertypen:
- **E1001** Datei fehlt oder ist nicht lesbar (Dateizugriff / file access).
- **E2001** Modul reagiert nicht wie erwartet (Modulprüfung / module check).
- **E3001** Selbsttest fehlgeschlagen (Selbsttest / self-test).

## Beispiel-Fehler testen (absichtlich provozieren)
- **Datei fehlt**: Import/Export öffnen, eine Datei auswählen und diese vorher löschen/verschieben. Erwartung: Fehler E1001 mit nächstem Schritt.
- **Modul defekt**: Eine Import-Datei öffnen und absichtlich ungültiges JSON einfügen (z. B. eine fehlende Klammer). Erwartung: Fehler E2001.
- **Test fail**: Daten exportieren, die JSON-Datei manuell beschädigen (z. B. ein Pflichtfeld entfernen), dann Self-Test ausführen. Erwartung: Fehler E3001.

## Qualitätssicherung
- **Tests**: Automatische Tests für Kernfunktionen.
- **Formatierung**: Automatische Codeformatierung (einheitlicher Stil, geplant).
- **Prüfungen**: Start-Routine prüft Struktur und Abhängigkeiten (geplant).

## Dokumentationsregeln
- Änderungen werden im `CHANGELOG.md` beschrieben.
- Abgeschlossene Aufgaben kommen nach `DONE.md`.
- Fortschritt wird in `PROGRESS.md` aktualisiert.

## Bauen/Starten/Testen
### GMS Archiv Tool (Vite)
```bash
cd gms-archiv-tool_v1.2.3_2026-01-06
npm install
npm run dev
```

### Self-Test (manuell in der UI)
1. In der App zu **Import/Export** wechseln.
2. Button **Self-Test** ausführen.
3. Erwartung: „Self-Test OK“ inklusive Log-Queue-Prüfung (max. 10 Logs).
