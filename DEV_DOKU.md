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
- **Formatierung**: Automatische Codeformatierung (einheitlicher Stil).
- **Prüfungen**: Start-Routine prüft Struktur und Abhängigkeiten.

## Dokumentationsregeln
- Änderungen werden im `CHANGELOG.md` beschrieben.
- Abgeschlossene Aufgaben kommen nach `DONE.md`.
- Fortschritt wird in `PROGRESS.md` aktualisiert.

## Bauen/Starten/Testen
Aktuell nutzbare Befehle (im Ordner `gms-archiv-tool_v1.2.3_2026-01-06`):
- **Bauen (Build)**: `npm run build`
- **Starten lokal (Development Server)**: `npm run dev`
