# DONE

## 2026-01-07
- Doku: Entwickler-Dokumentation strukturiert.
- Doku: Projekt-Anleitung für Laien erstellt.
- UI: Einheitliche Farben und Abstände definiert.
- UI: Kontrast und Lesbarkeit optimiert.
- Steuerung: Fortschritt aus To-Dos berechnet und als Bericht schreibbar gemacht.
- Logs: Log-Export als ZIP eingeführt.

## 2026-01-09
- Launcher: Start-Routine prüft Projektstruktur und erstellt fehlende Ordner.
- Launcher: Fortschrittsanzeige beim Start ergänzt.
- Tests: Tests erst nach kompletter Runde ausführen.
- Sprache: Alle UI-Texte auf Deutsch geprüft.
- Launcher: Modulübersicht ergänzt und Module aus Konfiguration gelistet.
- Module: Status-Check-Modul nach Standard-Schnittstelle integriert.
- Architektur: Zentrales Datenmodell für To-Dos und Kalender eingeführt.
- Module: To-Do-&-Kalender-Modul nach Standards integriert.
- Module: Beispielmodul nach Standards integriert.
- Module: Modul-Check beim Start ergänzt.
- Launcher: Klick&Start-Skript ergänzt und GUI-Startübersicht erstellt.
- Steuerung: To-Do-Manager akzeptiert `progress --write-progress` wie dokumentiert.
- UI: Tastaturbedienung der GUI-Startübersicht ergänzt (Shortcuts + Fokus).
- Architektur: Einheitliche Modul-Schnittstelle dokumentiert.
- Module: Modul-Check in der GUI-Startübersicht ergänzt.
- Architektur: Modul-Check als verpflichtender Startschritt in den Standards festgehalten.
- Module: Modul-Pfade in `config/modules.json` auf Modulordner umgestellt.
- Module: Manifest-Pflichtfelder (id/entry) für Status- und To-Do-Kalender-Modul ergänzt.
- UI: Launcher-GUI mit klaren Fokusrahmen für Tastaturbedienung erweitert.
- UI: Launcher-GUI um zusätzliche barrierefreie Farbschemata ergänzt.
- Qualität: Requirements mit Inline-Kommentaren robust eingelesen.
- Module: Modul-Check gegen Pfad-Traversal bei Entry-Pfaden abgesichert.
- Qualität: Requirements-Parser ignoriert Inline-Kommentare auch bei Tabs/Mehrfach-Leerzeichen.
- Module: Modul-Check blockiert `..` im Entry-Pfad mit klarer Fehlermeldung.
- Tests: Testskript robuster gemacht (klare Fehlerhinweise + Log-Hinweis).
- Tests: Hilfe-Option für den Testlauf als Schritt-für-Schritt-Anleitung ergänzt.
- Doku: PROJEKT_INFO mit Ordnerstruktur und Tooldateien ergänzt.
- Analyse: Inkonsistenzen/Redundanzen/Robustheit dokumentiert.
- Qualität: Unbenutzten Import im Health-Check entfernt.

## 2026-01-10
- Setup: Repo-Basis-Check mit Push-Trockenlauf ergänzt.
- Launcher: Abhängigkeitsprüfung in der Start-Routine ergänzt.
- Tests: Pytest als Standard-Testlauf ergänzt und Testskript ergänzt.
- Qualität: Ruff- und Black-Prüfungen für Codequalität und Format ergänzt.

## 2026-01-11
- Module: Notiz-Editor-Modul mit Templates, Favoriten und Dashboard ergänzt.
- Module: Charakter-Modul mit Templates, Favoriten und Dashboard ergänzt.

## 2026-01-12
- Module: Download-Ordner-Aufräum-Modul mit Plan, Log und Undo ergänzt.
- Module: Datei-Suche mit Filtern, Organisation und Undo ergänzt.

## 2026-01-13
- Tests: Fehler-Log-Hinweis im Testskript ergänzt.
- Tests: Schritt-für-Schritt-Hilfe in `run_tests.sh --help` ergänzt.
- Tests: Testskript robuster gemacht (Fehlerfalle + klare Hinweise).
- Tests: Testskript mit Hilfe-Option für Laien ergänzt.
- Start: Health-Check vor dem Start ergänzt (wichtige Dateien/Ordner).
- Qualität: Gemeinsame Pfad- und JSON-Validierung für Launcher/GUI eingeführt.

## 2026-01-14
- Qualität: Health-Check bereinigt und wieder lauffähig gemacht (Syntax, Self-Repair, Datum).
- Doku: Doppelte Changelog-Abschnitte zusammengeführt (0.1.20/0.1.19/0.1.15).

## 2026-01-15
- Start: Health-Check um Selbstreparatur ergänzt (fehlende Dateien/Ordner werden erstellt).
- Qualität: Pfad-Validierung zentralisiert, Duplikate über `config_utils.ensure_path` entfernt.
- Start: Health-Check um Self-Repair für fehlende Basiselemente ergänzt.
- Start: Start-Routine nutzt Self-Repair und zeigt klaren Hinweis.

## 2026-01-16
- Doku: PROJEKT_INFO um Automatik, Barrierefreiheit und Laienhinweise ergänzt.
- Doku: ANALYSE_BERICHT mit Ist-Analyse, Best Practices und Laienvorschlägen aktualisiert.
- Doku: Standards um Benennungsstandard und Datenmodell-Referenz ergänzt.
- Doku: Release-Checkliste für die GUI in todo.txt ergänzt.
