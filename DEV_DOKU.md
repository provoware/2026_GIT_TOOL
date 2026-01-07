# DEV_DOKU

## Zweck
Diese Dokumentation richtet sich an Entwicklerinnen und Entwickler. Sie beschreibt Struktur, Standards und den geplanten Ablauf.

## Projektstatus
- Start-Check und Modul-Check sind umgesetzt und in der Diagnose sichtbar.
- Modul-Check wird im Self-Test mit einem defekten Modul automatisch geprüft.

## Struktur (aktuell)
- `gms-archiv-tool_v1.2.3_2026-01-06/src/system/`: Systemlogik (Start-Checks).
- `gms-archiv-tool_v1.2.3_2026-01-06/src/config/`: Konfiguration (Modul-Definitionen).
- `gms-archiv-tool_v1.2.3_2026-01-06/src/`: App-UI und Kernlogik.

## Standards (geplant)
- Einheitliche Modul-Schnittstellen (Init/Exit).
- Zentrales Datenmodell.
- Barrierefreie UI-Texte (Deutsch, klar, laienverständlich).
- Fehlermeldungen folgen dem Format: Titel + Erklärung + Lösung.
## Standards (teilweise umgesetzt)
- Modul-Schnittstelle wird beim Start geprüft (Id, Name, Start-Funktion).
- Barrierefreie UI-Texte: Deutsch, klar, laienverständlich.

## Qualitätssicherung
- **Tests**: Self-Test inkl. Start-Check (Module, Speicher, Basisdaten).
- **Formatierung**: Vite/Tailwind Standard-Setup.
- **Prüfungen**: Start-Check meldet Fehler/Hinweise in der Diagnose.

## Dokumentationsregeln
- Änderungen werden im `CHANGELOG.md` beschrieben.
- Abgeschlossene Aufgaben kommen nach `DONE.md`.
- Fortschritt wird in `PROGRESS.md` aktualisiert.

## Bauen/Starten/Testen
- Build: `npm -C gms-archiv-tool_v1.2.3_2026-01-06 run build`
- Dev-Start: `npm -C gms-archiv-tool_v1.2.3_2026-01-06 run dev`
- Diagnose: Start-Check oder Self-Test im UI ausführen.
Aktuell gibt es keine lauffähigen Skripte. Diese Sektion wird ergänzt, sobald Start- und Testscripte existieren.

Letzte Prüfung (manuell):
- UI-Textprüfung (Deutsch/Fehlerstil) im Projekt-Übersichtstool.
