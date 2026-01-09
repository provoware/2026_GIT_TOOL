# Changelog

## [0.1.19] – 2026-01-14
- Qualität: Unbenutzten Import im Health-Check entfernt (Ruff sauber).
- Doku: Doppelte Changelog-Einträge für Version 0.1.16 zusammengeführt.
## [0.1.19] – 2026-01-09
- Doku: PROJEKT_INFO mit Ordnerstruktur und Tooldateien ergänzt (Pflegepflicht).
- Doku: Analysebericht zu Inkonsistenzen, Redundanzen und Robustheit ergänzt.
- Qualität: Unbenutzten Import im Health-Check entfernt (Linting/Formatierung grün).

## [0.1.18] – 2026-01-09
- Tests: Testskript robuster gemacht (klare Fehlerhinweise + konsistente Hilfe-Ausgabe).
- Tests: Hilfe-Option für den Testlauf als geführte Schritt-für-Schritt-Anleitung ergänzt.

## [0.1.17] – 2026-01-13
- Start: Health-Check ergänzt, der wichtige Dateien/Ordner vor dem Start prüft.
- Qualität: Gemeinsame Pfad- und JSON-Validierung für Launcher/GUI eingeführt (Duplikate reduziert).

## [0.1.16] – 2026-01-13
- Tests: Fehler-Log-Hinweis im Testskript ergänzt.
- Tests: Schritt-für-Schritt-Hilfe für den Testlauf ergänzt.
- Qualität: Requirements-Parser ignoriert Inline-Kommentare auch bei Tabs/Mehrfach-Leerzeichen.
- Module: Modul-Check blockiert `..`-Segmente im Entry-Pfad mit klarer Fehlermeldung.

## [0.1.15] – 2026-01-13
- Tests: Testskript robuster gemacht (Fehlerfalle + klare Hinweise).
- Tests: Hilfe-Option für das Testskript ergänzt.
## [0.1.15] – 2026-01-09
- Qualität: Requirements-Parser ignoriert Inline-Kommentare.
- Module: Modul-Check validiert Entry-Pfade gegen Pfad-Traversal.

## [0.1.14] – 2026-01-12
- Module: Download-Ordner-Aufräumen mit Scan, Plan, Undo und Protokoll ergänzt.
- Module: Datei-Suche mit Filtern, Organisation und Undo ergänzt.
- Tests: Unit-Tests für Download-Aufräumen und Datei-Suche ergänzt.

## [0.1.13] – 2026-01-11
- Module: Notiz-Editor-Modul mit Templates, Favoriten und Dashboard-Statistiken ergänzt.
- Module: Charakter-Modul mit Templates, Favoriten und Dashboard-Statistiken ergänzt.
- Architektur: Zentrales Datenmodell um Notiz- und Charakterdaten erweitert.
- Tests: Unit-Tests für neue Datenmodelle und Module ergänzt.

## [0.1.12] – 2026-01-10
- Tests: Pytest als Standard-Testlauf ergänzt und in die Test-Sperre integriert.
- Qualität: Ruff- und Black-Prüfungen als automatischen Prüf-Schritt ergänzt.
- Skript: Zentrales Testskript für Tests, Codequalität und Formatprüfung ergänzt.

## [0.1.11] – 2026-01-09
- GUI-Launcher: Fokusrahmen und Menüfarben für bessere Tastaturbedienung ergänzt.
- GUI-Launcher: Zwei zusätzliche Farbschemata mit hohem Kontrast ergänzt.

## [0.1.10] – 2026-01-10
- Start-Routine: Abhängigkeitsprüfung ergänzt, inklusive automatischer Installation über requirements.txt.
- Setup: Repo-Basis-Check als Skript ergänzt, inklusive Push-Trockenlauf.

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
