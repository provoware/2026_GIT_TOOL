# Changelog

## [0.1.9] – 2026-01-09
- GUI-Launcher: Modul-Check ergänzt, der Manifest und Entry-Dateien beim Start meldet.
- Standards: Modul-Check als verpflichtenden Startschritt dokumentiert.
- Module: Modul-Pfade in der Konfiguration auf Modulordner korrigiert.
- Module: Manifest-Dateien um fehlende Pflichtfelder ergänzt (id/entry).

## [0.1.8] – 2026-01-09
- GUI-Launcher: Tastatur-Shortcuts für Theme, Filter, Debug und Aktualisieren ergänzt.
- Doku: Einheitliche Modul-Schnittstelle in der Entwickler-Doku festgehalten.

## [0.1.7] – 2026-01-09
- Launcher: Klick&Start-Skript ergänzt, das die Start-Routine ausführt und die GUI-Startübersicht öffnet.
- Launcher: GUI-Startübersicht mit Theme-Auswahl, Debug-Anzeige und klarer Modul-Liste ergänzt.
- Launcher: Modul-Konfiguration korrigiert, damit die Modul-Liste gültig geladen wird.
- Start: Fortschritt wird jetzt direkt über `todo_manager.py` aktualisiert.
- To-Do-Manager: `progress --write-progress` unterstützt die gewünschte Befehlsreihenfolge.

## [0.1.6] – 2026-01-09
- Launcher: Modulübersicht ergänzt, damit alle Tools klar gelistet werden.
- Module: Status-Check-Modul nach Standard-Schnittstelle integriert.
- Architektur: Zentrales Datenmodell für To-Dos und Kalender eingeführt.
- Module: To-Do-&-Kalender-Modul nach Standards integriert (Manifest, Konfiguration, Datenablage).
- Tests: Neue Unit-Tests für Datenmodell und Modul ergänzt.
- Module: Modul-Check eingeführt, der registrierte Module und deren Manifest prüft.
- Module: Beispielmodul samt Registrierung ergänzt, damit Standards praktisch getestet werden können.

## [0.1.5] – 2026-01-09
- Tests: Test-Sperre ergänzt, damit Tests erst nach kompletter Runde starten.
- Sprache: Testlauf-Hinweis in der CLI auf Deutsch vereinheitlicht.

## [0.1.4] – 2026-01-09
- Launcher: Start-Routine prüft die Projektstruktur und erstellt fehlende Ordner automatisch.
- Launcher: Fortschrittsanzeige beim Start ergänzt (Prozentanzeige pro Schritt).

## [0.1.3] – 2026-01-07
- Steuerung: Fortschrittsbericht aus todo.txt kann PROGRESS.md aktualisieren.
- Logs: Log-Export als ZIP mit eindeutiger Dateiablage ergänzt.

## [0.1.2] – 2026-01-07
- UI: Farbpalette vereinheitlicht und Kontrastwerte für Dark/Light-Themes erhöht.
- UI: Mindestschriftgröße auf 16px abgesichert und Badge-Texte lesbarer gemacht.
- Doku: Vorgehen für UI-Checks (Kontrast/Theme/Schriftgröße) ergänzt.

## [0.1.1] – 2026-01-07
- README überarbeitet: Analyse, Ziele und einfache Anleitung ergänzt
- Entwickler-Dokumentation hinzugefügt
- Fortschritt und erledigte Aufgaben dokumentiert

## [0.1.0] – Initial
- Repo neu aufgesetzt
- Basisstruktur angelegt
