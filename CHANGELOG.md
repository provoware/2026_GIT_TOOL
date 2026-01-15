# Changelog

## [Unreleased] – 2026-02-13
- GUI: Hauptfenster mit 3x3-Modulraster, Drag/Resize und Kollisionsschutz ergänzt.
- Module: Modulmanager für Laden, Aktivieren und Deaktivieren ergänzt.
- GUI: Launcher um Hauptfenster-Button und Shortcut erweitert.
- Tests: Modulmanager-Tests ergänzt.
- Automatisch ergänzt: REL-01: .deb-Paket bauen.
- Automatisch ergänzt: REL-02: Offizielles Icon-Set (Provoware-Look) integrieren.
- Automatisch ergänzt: REL-04: ZIP-Auto-Export alle fünf Entwicklungsschritte.
- Automatisch ergänzt: REL-08: Desktop-File + Icon-Integration für Linux.
- Flow: Event-Bus für globale Modulevents ergänzt.
- Sicherheit: Schreibschutzsystem auf Manifest-Rechten aufgebaut.
- IO: Selektiver Export mit Presets und Launcher-Integration ergänzt.
- Abschluss: End-Audit-Check mit Release-Status in der GUI ergänzt.
- Flow: Drag-and-Drop-Zone im Launcher ergänzt, inkl. Statushinweis.
- Flow: Undo-/Redo-System für globale Aktionen ergänzt.
- IO: Export-Center für JSON/TXT/PDF/ZIP ergänzt (inkl. Launcher-Start).
- IO: Backup-Center mit ZIP-Sicherungen in der GUI integriert.
- GUI: Hilfe- und Entwicklerbereich flexibler angeordnet und erweitert.
- Start: PIN-Login-Konfigurationscheck stabilisiert (kein TypeError beim Start).
- Dashboard: Layout, Farben und Hintergrund an Design_und_Layoutvorgabe angepasst.
- Dashboard: Zeitachse mit kräftigerem Gradient und Glas-Panel-Stil überarbeitet.

## [0.1.12] – 2026-02-12
- Medien: Wavesurfer-Toolkit mit Markern, Regionen, Minimap und Exportprofilen ergänzt.
- Medien: FFmpeg-Wrapper mit Presets, Auto-Name und Fortschrittsanzeige ergänzt.
- Medien: Datei-Manager mit Quick-Rename, Tagging und Favoriten ergänzt.
- Daten: Profil-Manager mit getrennten Projektordnern integriert.
- Tests: Modul-Tests für neue Medien- und Profil-Module ergänzt.

## [0.1.53] – 2026-02-09
- Release: AppImage-Builder mit integriertem Self-Check ergänzt.
- Release: One-File-Build (PyInstaller) mit Konfig und Entry-Skript ergänzt.
- Release: .deb-Postinst-Initialisierung ergänzt (Self-Check + Ordner).
- GUI: Abmelden mit Autosave und sauberem Schließen ergänzt.

## [0.1.52] – 2026-02-07
- GUI: Tooltips für Launcher-Steuerung ergänzt und barrierearm platziert.
- GUI: Kontext-Hilfe im Launcher ergänzt (Fokus + F1).
- Doku: DEV_DOKU um Tooltip- und Kontext-Hilfe aktualisiert.

## [0.1.51] – 2026-02-06
- GUI: Großbutton-UI über neue Layout-Parameter (Breite + Schriftgröße) verstärkt.
- Qualität: GUI-Konfig-Modelle und JSON-Validator prüfen neue Button-Felder.
- Doku: DEV_DOKU und To-Do-Listen mit aktualisierten Launcher-Parametern synchronisiert.

## [0.1.50] – 2026-01-15
- Struktur: Zusatzprojekt dashboard-timeline-tool in dashboard_zeitachsen_werkzeug umbenannt.
- Struktur: Zusatzprojekt genrearchiv_tool_v1_2_3_2026_01_06 in genrearchiv_werkzeug_v1_2_3_2026_01_06 umbenannt.
- Doku: Strukturbaum, Standards und Pfadverweise auf neue Ordnernamen aktualisiert.

## [0.1.49] – 2026-01-15
- Start: PIN-Login wird in der Start-Routine geprüft (optional über config/pin.json).
- Start: Testmodus (--test-mode) als Alias für Safe-Mode ergänzt.
- Autosave: Automatische Sicherungen schreiben ZIP-Archive in data/autosave/ und loggen nach logs/autosave.log.
- Autosave: Autosave-Status wird in data/autosave_state.json gesichert.

## [0.1.48] – 2026-02-05
- Timeline: Zeitachse responsiv mit horizontalem Scroll und anpassbarer Höhe umgesetzt.
- Timeline: Hover-Details, Zoom-Regler und flexibler Abstand integriert.
- Timeline: Lesbarkeit durch bessere Kontraste, klare Detailbox und Tastaturhinweise verbessert.
- Barrierefreiheit: Zusätzliche ARIA-Beschreibungen und Fokusführung in der Zeitachse ergänzt.
- System: Modul-Loader setzt Root-Pfad und stabile Registrierung für Selftests.
- Tooling: Black-Konfiguration erweitert und betroffene Dateien formatiert.

## [0.1.47] – 2026-02-04
- GUI: Entwicklerbereich im Launcher ergänzt (System-Scan, Standards-Liste, Log-Ordner).
- GUI: Sofort-Feedback über Status-Punkt und klarere Statusfarben erweitert.
- GUI: Basis-Branding und neue „Papierkorb“-Themevariante ergänzt.

## [0.1.46] – 2026-01-15
- Doku: Changelog-Automatik ergänzt und Rundentasks in todo.txt werden automatisch archiviert.
- Daten: Globale Settings-Datei ergänzt und in Health-Check/Self-Repair aufgenommen.
- Daten: Strukturpflege aktualisiert baumstruktur.txt, manifest.json und dummy_register.json automatisch.
- Release: Build-All-Skript bündelt Checks, Strukturpflege, Doku-Update und Tests.

## [0.1.45] – 2026-02-03
- Start: Venv-Automatik ergänzt, Start-Routine nutzt den Venv-Interpreter.
- Start: GUI-Voraussetzungen (Tkinter) werden geprüft und klar gemeldet.
- Start: GUI-Launcher startet nach erfolgreichem Startlauf automatisch.
- Tests: run_tests.sh nutzt den gleichen Venv-Interpreter.

## [0.1.44] – 2026-01-15
- Sicherheit: PIN-Login mit Zufallssperre und Statusdatei ergänzt.
- Start: Self-Repair-Bibliothek ergänzt und in die Start-Routine integriert.
- Qualität: Self-Repair repariert fehlende Dateien, JSON und Rechte automatisch.
- Daten: Suffix-Standards für data/logs ergänzt, Dateinamen-Fixer berücksichtigt diese Regeln.
- Tests: PIN-Check und Suffix-Standards mit Unit-Tests abgesichert.

## [0.1.43] – 2026-02-02
- Branding: Genrearchiv-Frontend umbenannt (Ordner, Package, UI-Titel).
- Daten: Storage-Keys und Export-Dateinamen auf Genrearchiv umgestellt, mit Legacy-Migration.
- Doku: Pfade/Beispiele für das Genrearchiv-Frontend aktualisiert.

## [0.1.42] – 2026-01-15
- Qualität: Modulverbund-Checks prüfen Modulnamen gegen Manifest-Namen.
- Tests: Modulverbund-Checks mit Test für Namensabweichungen ergänzt.
- Doku: TODO.md Dubletten (START-09/10, DATA-06, UX-05) bereinigt.

## [0.1.41] – 2026-01-15
- Doku: Start-Tasks (START-03/05/06/07) in TODO.md und todo.txt synchronisiert.
- Doku: Fortschritt und Auto-Status aktualisiert.

## [0.1.40] – 2026-02-01
- Standards: Genrearchiv-Frontend-Pfad auf snake_case-Standard umgestellt.
- Qualität: Linting- und Format-Skripte für das Genrearchiv-Frontend ergänzt.
- Doku: Genrearchiv-Frontend-README und Entwicklerdoku aktualisiert.

## [0.1.39] – 2026-01-30
- Qualität: Modulstruktur-Validator mit Pflicht-Entry + Konfig-Ausnahmen ergänzt.
- Sicherheit: Modulverbund-Check führt Selftests aus und blockiert fehlerhafte Module.
- Start: Ampelstatus am Ende der Start-Routine ergänzt.
- Start: Recovery-Modus als Notfallstart-Skript ergänzt.
- Health-Check: Standarddatei für Modulstruktur-Config ergänzt.
- Doku: Recovery-Modus und Modulstruktur-Regeln dokumentiert.
- Dashboard: Globale Suche für Module, Einträge, Aktionen und Notizen ergänzt.
- Dashboard: Favoritenleiste für Module inkl. Umschalten ergänzt.
- Dashboard: Mini-Panels für Export/Backup/Schnellnotizen ergänzt.
- Dashboard: Auto-Theming (Tag/Nacht) inkl. manueller Umschaltung ergänzt.
- Qualität: Ruff- und Black-Hinweise in GUI- und Modul-API-Dateien bereinigt.

## [0.1.38] – 2026-01-29
- Standards: Modulnamen-Validierung (snake_case + Pfadregel) ergänzt.
- GUI: Einheitliche Abstände über Layout-Tokens in der GUI-Konfiguration eingeführt.
- Qualität: Fehlerhandling-Standard (Ursache/Lösung/Log) dokumentiert.
- Doku: Laienhinweise zu Modulnamen und Layout-Token ergänzt.

## [0.1.37] – 2026-01-28
- GUI: One-Click-Diagnose im Launcher ergänzt (Tests + Codequalität im Fenster).
- Qualität: Health-Check repariert Leserechte/Ausführrechte im Self-Repair.
- Architektur: Modul-API-Typen (TypedDicts) ergänzt und dokumentiert.
- Doku: Auto-Status-Blöcke mit Doc-Updater für README/DEV_DOKU ergänzt.
- Tests: Diagnoserunner und Doku-Updater mit Unit-Tests abgesichert.

## [0.1.36] – 2026-01-27
- Architektur: Modul-API-Validator ergänzt (prüft `run`, `validateInput`, `validateOutput`).
- Architektur: Modul-Check um Modul-API-Check erweitert (klare Fehlermeldungen).
- Tests: Unit-Tests für den Modul-API-Validator ergänzt.
- Doku: MODUL_API.md um automatische Modul-API-Prüfung ergänzt.

## [0.1.35] – 2026-01-26
- Doku: Info-Dateien und README bereinigt/aktualisiert, STRUKTUR.md ergänzt.
- Doku: Dummy-Platzhalter für Pflichtdateien dokumentiert und angelegt.
- Tests: Test-Sperre auf 4 Tasks pro Runde umgestellt (Config + Doku).

## [0.1.34] – 2026-01-25
- Architektur: Zentrale Modul-Registry (Plugin-System) und Store eingeführt.
- Architektur: Modul-API dokumentiert (Schnittstellen, Events, States) mit Beispiel.
- Architektur: Single Source of Truth für Theme/Settings/Logging umgesetzt.
- Logging: Asynchrones Logging-Modul für alle Systemtools eingeführt.
- Performance: Lazy Loading/Caching für Modul-Imports ergänzt.
- Performance: Debounce für GUI-Aktualisierung ergänzt.
- Qualität: Konfigurationen über geprüfte Modelle zentral validiert.
- Doku: Laien-Tool-Anleitung mit FAQ, Befehlen und Tipps ergänzt.

## [0.1.33] – 2026-01-24
- Start: Safe-Mode (schreibgeschützt) und Ghost-Mode ergänzt.
- Start: Sandbox-Modus implementiert (isolierte Kopie).
- Start: Struktur-Check für Ordnertrennung ergänzt.
- Start: Abhängigkeits-Feedback klarer ausgegeben.
- Tooling: System-Scan als Vorabprüfung ergänzt.
- Doku: Struktur- und Theme-Standard aktualisiert.
- Tests: Test-Automatik auf 9 Tasks pro Runde angepasst.

## [0.1.32] – 2026-01-23
- Analyse: Sandbox-Risiken dokumentiert und Schutzmaßnahmen ergänzt.
- Tests: Modulverbund-Checks ergänzt (Selftests, Manifest-IDs, Konsistenz).
- Tests: Robustheit für beschädigte JSONs und fehlende Leserechte abgesichert.
- Tests: Test-Automatik auf 5 Tasks pro Runde angepasst.
- Tooling: Testskript ergänzt Modulverbund-Checks vor dem Testlauf.

## [0.1.31] – 2026-01-22
- Qualität: Fehlerklassifizierung (leicht/mittel/schwer) für Modul-Checks ergänzt.
- Qualität: Datei-Ampelsystem mit klaren Problemhinweisen ergänzt.
- Qualität: Modul-Selbsttests mit GUI- und CLI-Ausgabe ergänzt.
- Tests: Fehler-Simulation für typische Laienfehler ergänzt.
- Tests: Zusätzliche Tests für Qualitätschecks, Selbsttests und Simulation ergänzt.

## [0.1.30] – 2026-01-21
- Start-Routine: Fehleralternativen statt Abbruch ergänzt (Hinweise + Sammelreport).
- Start-Routine: JSON-Validierung und Dateinamenkorrektur integriert.
- GUI-Launcher: Großbutton-UI (größere Buttons/Schriften) umgesetzt.
- GUI-Launcher: Farbiges Sofort-Feedback im Statusbereich ergänzt.
- Qualität: JSON-Validator und Dateinamen-Fixer inklusive Tests ergänzt.

## [0.1.29] – 2026-01-20
- GUI-Launcher: Kontrastmodus per Hotkey (Alt+K) ergänzt.
- GUI-Launcher: Zoom per Strg+Mausrad für bessere Lesbarkeit ergänzt.
- GUI-Launcher: Hilfe-Kurzinfo und Bereichsstruktur für Screenreader ergänzt.
- Qualität: Eingabe-/Ausgabe-Validierung im GUI-Launcher erweitert.
- Doku: TODO-Listen mit neuer Rundeliste und Roadmap-Lücken ergänzt.

## [0.1.28] – 2026-01-19
- GUI-Launcher: Steuerleiste zweizeilig gemacht, Footer-Text responsiv umbrochen.
- GUI-Launcher: Mindestgröße reduziert, damit kleine Fenster besser nutzbar sind.
- Start: Setup-Skripte getrennt (check_env.sh, bootstrap.sh) und Start-Routine erweitert.
- Start: Debug- und Logging-Modus ergänzt (start_run.log).
- Tooling: Standards-Viewer ergänzt (Standards + Styleguide per CLI).
- Doku: Responsivitäts-Check der Launcher-GUI dokumentiert.
- Doku: DEV_DOKU und To-Do-Listen aktualisiert.

## [0.1.27] – 2026-01-18
- Doku: A–I-Backlog (Architektur bis Komfortfunktionen) strukturiert in TODO.md ergänzt.
- Doku: README um Architektur, Start-Routine, Tests und Barrierefreiheit erweitert.
- Doku: Styleguide (PEP8 + Projektregeln) ergänzt.
- Doku: todo.txt mit neuer Rundeliste synchronisiert.

## [0.1.26] – 2026-01-17
- GUI-Launcher: Statusanzeige mit Busy-Modus ergänzt, inkl. klarer Fehlerhinweise.
- GUI-Launcher: Ausgabe mit zusätzlichem Label für Screenreader ergänzt.
- Tests: Kontrasttest für Launcher-Themes ergänzt.
- Doku: Kontrastbericht für Launcher-Themes ergänzt.
- Tooling: Berichtsskript und Farb-Kontrast-Utils ergänzt.

## [0.1.25] – 2026-01-17
- Doku: todo.txt in TODO.md als synchronisierte Kurzliste integriert.
- Doku: todo.txt mit IDs und Hinweis auf TODO.md vereinheitlicht.
- Doku: Laien-Tipps erweitert und in TODO.md gespiegelt.

## [0.1.24] – 2026-01-16
- Doku: TODO.md strukturiert, Dubletten entfernt und Backlog gruppiert.
- Doku: todo.txt als laienfreundliche Kurzliste ergänzt.

## [0.1.23] – 2026-01-16
- Doku: Standards um Benennungsstandard und Datenmodell-Referenz ergänzt.
- Doku: Release-Checkliste für die GUI in todo.txt ergänzt.

## [0.1.22] – 2026-01-14
- Qualität: Health-Check bereinigt und wieder lauffähig gemacht (Syntax + Self-Repair).
- Doku: Doppelte Versionsabschnitte im Changelog zusammengeführt.

## [0.1.21] – 2026-01-16
- Doku: PROJEKT_INFO um Automatik, Barrierefreiheit und Laienhinweise ergänzt.
- Doku: ANALYSE_BERICHT mit Ist-Analyse, Best Practices und Laienvorschlägen aktualisiert.

## [0.1.20] – 2026-01-15
- Start: Health-Check mit Selbstreparatur ergänzt (fehlende Dateien/Ordner werden erstellt).
- Qualität: Pfad-Validierung in System-Skripten vereinheitlicht (Duplikate reduziert).
- Start: Health-Check mit Self-Repair ergänzt, der fehlende Basiselemente automatisch anlegt.
- Start: Start-Routine ruft den Health-Check jetzt mit Self-Repair und klarer Meldung auf.

## [0.1.19] – 2026-01-14
- Qualität: Unbenutzten Import im Health-Check entfernt (Ruff sauber).
- Doku: Doppelte Changelog-Einträge für Version 0.1.16 zusammengeführt.
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
