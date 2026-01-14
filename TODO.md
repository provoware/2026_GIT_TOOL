# TODO (strukturiert, barrierefrei, laienverständlich)

## Regeln (verbindlich)
- Pro Runde werden **genau 4 kleine Aufgaben** erledigt.
- Erst **kurz analysieren**, dann **umsetzen**, dann **testen**, dann **dokumentieren**.
- Fachwörter werden **einfach erklärt** (Fachbegriff in Klammern mit kurzer Erklärung).

## Kurz-Ist-Analyse (offene Aufgaben)
- **Risiko**: GUI-Barrierefreiheit ist noch nicht vollständig geprüft (Kontrast, Fokus, Screenreader). → Gefahr: Nutzerinnen und Nutzer können die Oberfläche nicht sicher bedienen.
- **Lücke**: Es fehlt eine konsistente, sichtbare Statusanzeige bei langen Aktionen (Busy-Indikator = Ladeanzeige).
- **Schwachstelle**: Fehlermeldungen sind noch nicht überall in einfacher Sprache mit Lösungsschritt vorhanden.
- **Abhängigkeit**: Für GUI-Tests fehlt eine automatisierte Routine (GUI-Tests = Tests für Benutzeroberflächen).
- **Best Practice**: Aufgaben sollten eindeutige IDs haben und pro Bereich gruppiert sein.
- **Lücke**: todo.txt und TODO.md waren nicht 1:1 synchron → Risiko: widersprüchlicher Fortschritt.
- **Best Practice**: Eine Kurzliste (todo.txt) soll die gleiche ID-Struktur wie TODO.md nutzen.
- **Erledigt**: Plugin-System mit Registry (Registry = zentrale Liste der Module) umgesetzt.
- **Erledigt**: Modul-API (Schnittstellen, Events, States) ist dokumentiert und mit Beispiel hinterlegt.
- **Erledigt**: Zentraler Store (Store = gemeinsamer Zustands-Speicher) eingeführt; Single Source of Truth (einzige Quelle) für Theme/Settings/Logging umgesetzt.
- **Erledigt**: Lazy Loading (spätes Laden) für Module und Caching eingeführt.
- **Erledigt**: Debounce/Throttle (gebremstes Auslösen) für GUI-Aktualisierung umgesetzt.
- **Erledigt**: Asynchrones Logging (nicht blockierend) eingeführt.
- **Erledigt**: JSON-Validierung ist über geprüfte Modelle abgesichert.
- **Lücke**: Komfortfunktionen wie globale Suche, Favoritenleiste, Mini-Panels und Auto-Theming fehlen.
- **Hinweis**: Zusätzliche Barrierefreiheit (Kontrast-Hotkey, Zoom per STRG+Mausrad, Screenreader-Struktur) ist umgesetzt, Gesamtprüfung bleibt offen.
- **Lücke**: Build/Release-Automatisierung (deb/AppImage/Build-All) fehlt.
- **Lücke**: Sicherheitsfeatures (PIN-Sperre, Modultests vor dem Laden) sind noch offen.
- **Hinweis**: Roadmap-Elemente (Grundtheme/Branding, Safe-Mode, Sandbox-Modus) bleiben außerhalb dieser Runde offen; Logging-Modul ist umgesetzt.

## Kurzliste (aus todo.txt, synchron)
Diese Kurzliste ist **identisch** zu `todo.txt` und wird dort gespiegelt.
- [x] REL-GUI-01: Kontrast prüfen (Kontrast = Helligkeitsunterschied; Ziel ≥ 4,5:1).
- [x] REL-GUI-02: Fokusreihenfolge prüfen (Fokus = aktuelles Element bei Tab).
- [x] REL-GUI-03: Screenreader-Labels ergänzen (Screenreader = Vorlese-Programm).
- [x] REL-GUI-04: Fehler-/Statusmeldungen in einfacher Sprache + Lösungsschritt.
- [x] REL-GUI-05: Ladeanzeige zeigen (Busy-Indikator = sichtbare Ladeanzeige).
- [x] REL-GUI-06: Responsives Layout prüfen (passt sich kleinen Fenstern an).

Runde 2026-01-28 (4 kleinste Aufgaben dieser Runde) – erledigt
- [x] COM-01: One-Click-Diag (Tests + Ergebnisse in Fenster). | fertig wenn: Diagnosen sichtbar.
- [x] SEC-01: Rechteprobleme beim Start automatisch korrigieren. | fertig wenn: Self-Repair behebt Rechte.
- [x] CODE-03: Starke Typisierung + klare Moduleingänge definieren. | fertig wenn: Typen + Entry-Contracts dokumentiert.
- [x] DOC-02: README-/Doku-Autoupdater erstellen. | fertig wenn: Doku aktualisiert.

Runde 2026-01-27 (4 kleinste Aufgaben dieser Runde) – erledigt
- [x] ARCH-07: Modul-API-Validator ergänzen (Validator = automatische Prüfung). | fertig wenn: `run`, `validateInput`, `validateOutput` werden geprüft.
- [x] ARCH-08: Modul-Check um Modul-API-Check erweitern (Check = Prüfung). | fertig wenn: klare Fehlermeldungen im Modul-Check erscheinen.
- [x] TEST-07: Tests für Modul-API-Validator ergänzen (Tests = automatische Prüfungen). | fertig wenn: Testfälle für Pflichtfunktionen grün sind.
- [x] DOC-14: MODUL_API.md um Modul-API-Check ergänzen. | fertig wenn: Hinweis auf automatische Prüfung dokumentiert ist.

Runde 2026-01-26 (4 kleinste Aufgaben dieser Runde) – erledigt
- [x] DOC-11: Info-Dateien + README bereinigen und aktualisieren. | fertig wenn: alle Info-Dateien konsistent.
- [x] DOC-12: STRUKTUR.md mit vollständigem Verzeichnisbaum erstellen/pflegen. | fertig wenn: Baum + Pflichtdateien dokumentiert.
- [x] DOC-13: Dummy-Dateien für klar benötigte Dateien anlegen. | fertig wenn: Platzhalter klar gekennzeichnet.
- [x] OPS-01: Rundenlogik auf 4 Tasks umstellen (Test-Gate + Doku). | fertig wenn: Schwelle + Doku aktualisiert.

Nächste 9 kleinste Aufgaben (Runde 2026-01-24) – erledigt
- [x] DATA-06: Trennung von Systemlogik und variablen Daten/Configs (Config = Konfiguration). | fertig wenn: klare Ordnertrennung umgesetzt.
- [x] UX-05: Perfektes Farb- und Kontrastverhalten mit mehreren Themes. | fertig wenn: Themes dokumentiert.
- [x] START-09: Safe-Mode (schreibgeschützt) beim Start. | fertig wenn: Start ohne Schreibzugriffe möglich.
- [x] START-10: Sandbox-Modus (virtuelle Umgebung) implementieren. | fertig wenn: Start in isolierter Umgebung.
- [x] ARCH-05: Projektstruktur final definieren und standardisieren. | fertig wenn: Struktur-Standard dokumentiert.
- [x] START-08: Start-Routine mit Nutzerfeedback für Abhängigkeiten (Dependencies = Abhängigkeiten). | fertig wenn: klare Hinweise + automatische Installation.
- [x] COM-02: Systemscanner vor Start (Rechte/JSON/Ordner). | fertig wenn: Scanner blockiert Fehler.
- [x] COM-04: Ghost-Mode (Testmodus ohne Schreiben). | fertig wenn: keine Writes.
- [x] CODE-04: Styleguide (PEP8 + Projektregeln) als Markdown beilegen. | fertig wenn: Styleguide vorhanden.

Nächste 9 kleinste Aufgaben (Runde 2026-01-25) – erledigt
- [x] ARCH-01: Plugin-System mit zentraler Registry einführen (Registry = Modul-Liste). | fertig wenn: Module nur über Registry geladen werden.
- [x] ARCH-02: Modul-API definieren (Schnittstellen, Events, States). | fertig wenn: API-Dokument + Beispiel vorhanden.
- [x] ARCH-03: Zentralen Store einführen (Store = gemeinsamer Zustands-Speicher). | fertig wenn: Module lesen/schreiben zentral.
- [x] ARCH-04: Single Source of Truth für Theme/Settings/Logging. | fertig wenn: doppelte Logik entfernt.
- [x] ARCH-06: Zentrales Logging-Modul implementieren (Logging = Protokoll). | fertig wenn: ein Logging-Modul genutzt.
- [x] PERF-01: Lazy Loading für Module (spätes Laden) implementieren. | fertig wenn: Startzeit sinkt.
- [x] PERF-02: Debounce/Throttle für teure Aktionen (gebremstes Auslösen). | fertig wenn: UI bleibt flüssig.
- [x] PERF-03: Asynchrones Logging statt blockierend. | fertig wenn: Log schreibt ohne UI-Block.
- [x] PERF-04: JSON-Handling mit geprüftem Modell absichern (z. B. Pydantic). | fertig wenn: Validierung zentral.

Runde 2026-01-23 (5 kleinste Aufgaben dieser Runde) – erledigt
- [x] QA-08: Sandbox-Analyse erweitern (Sandbox = Testumgebung). | fertig wenn: Analyse deckt Sandbox-Risiken ab.
- [x] TEST-03: Robustheitstest für fehlende Rechte/beschädigte Dateien. | fertig wenn: System bleibt stabil.
- [x] TEST-04: Modulübergreifende Funktionschecks implementieren. | fertig wenn: Checks laufen.
- [x] TEST-05: Vollautomatische Codequalität- und Formatprüfung (Linting/Formatting = Code-Check). | fertig wenn: Checks laufen automatisch.
- [x] TEST-06: Vollautomatische Testausführung über Startroutine (Test-Automatik). | fertig wenn: Tests starten selbst.

Runde 2026-01-22 (5 kleinste Aufgaben dieser Runde) – erledigt
- [x] QA-03: Fehlerklassifizierung (leicht/mittel/schwer). | fertig wenn: Fehlerstufe angezeigt.
- [x] QA-04: Ampelsystem für Dateifehler. | fertig wenn: Ampelstatus sichtbar.
- [x] QA-05: Modul-Selbsttests mit GUI-Ausgabe. | fertig wenn: Teststatus sichtbar.
- [x] TEST-01: Automatisierte GUI-Tests einbinden. | fertig wenn: GUI-Tests laufen.
- [x] TEST-02: Fehler-Simulation (Laienfehler) integrieren. | fertig wenn: klare Fehlerfälle.

Runde 2026-01-21 (5 kleinste Aufgaben dieser Runde) – erledigt
- [x] START-06: Fehleralternativen statt Abbruch. | fertig wenn: Vorschläge statt Stop.
- [x] UX-02: Großbutton-UI realisieren (Großbutton = große Schaltflächen). | fertig wenn: große Buttons nutzbar.
- [x] UX-04: Farbiges Sofort-Feedbacksystem (Erfolg/Fehler). | fertig wenn: klare Farben.
- [x] QA-01: JSON-Validator einbauen. | fertig wenn: JSON geprüft.
- [x] QA-02: Automatische Dateinamenkorrektur. | fertig wenn: falsche Namen korrigiert.

## Laien-Tipps (aus todo.txt, erweitert)
- Starte zuerst den GUI-Launcher (Startübersicht) und teste mit der Tab-Taste (Tastaturbedienung).
- Nutze den Health-Check (Systemprüfung) vor dem Start, wenn etwas fehlt.
- Lies die Fehlermeldung bis zum Ende – dort steht der nächste Schritt.
- Wenn etwas nicht klappt: erst neu starten, dann Logdatei prüfen (logs/test_run.log).
- Tipp für Einsteiger: Beginne mit einem kleinen Test-Projektordner, damit Änderungen übersichtlich bleiben.
- Tests starten: `./scripts/run_tests.sh` (Tests = automatische Prüfroutinen).
- Fehler suchen: `logs/test_run.log` öffnen (Log = Protokoll) und letzten Eintrag lesen.
- Selbstreparatur: `python system/health_check.py --root . --self-repair` (Self-Repair = Selbstreparatur).
- Standards lesen: `./scripts/show_standards.sh --list` (Standards = interne Regeln).
- Start mit Debugging: `./scripts/start.sh --debug` (Debugging = detaillierte Fehlersuche).
- Start-Log speichern: `./scripts/start.sh --log-file logs/start_run.log` (Log = Protokoll).
- Anleitung lesen: `ANLEITUNG_TOOL.md` (Schritt-für-Schritt-Hilfe).
- Modul-API lesen: `docs/MODUL_API.md` (API = Schnittstellen-Übersicht).

## Runde 2026-01-20 (5 kleinste Aufgaben dieser Runde) – erledigt
- [x] ACC-01: Kontrastmodus per Hotkey umschaltbar. | fertig wenn: Hotkey aktiv.
- [x] ACC-02: Zoom per STRG + Mausrad global aktivieren. | fertig wenn: Zoom überall funktioniert.
- [x] ACC-03: Screenreader-freundliche Bereichsstruktur. | fertig wenn: Bereiche semantisch benannt.
- [x] UX-03: Hilfetexte direkt in der GUI integrieren. | fertig wenn: Hilfe pro Ansicht.
- [x] QA-06: Jede Funktion validiert Eingabe und Ausgabe (Input/Output = Ein-/Ausgabe). | fertig wenn: Validierung vorhanden.

## Runde 2026-01-19 (5 kleinste Aufgaben dieser Runde) – erledigt
- [x] REL-GUI-06: Responsive Layout für kleine Auflösungen prüfen. | fertig wenn: Bedienung bleibt möglich.
- [x] CODE-02: Setup-Skripte trennen (check_env.sh, bootstrap.sh, start.sh). | fertig wenn: Skripte getrennt vorhanden.
- [x] QA-07: Debugging- und Logging-Modus (Debugging = Fehlersuche). | fertig wenn: Modus schaltbar.
- [x] DOC-04: Interne Standards im Tool anzeigen (Konfig, Regeln, Tests). | fertig wenn: Standards sichtbar.
- [x] DOC-05: Weiterführende Laienvorschläge ergänzen (Tipps für Neulinge). | fertig wenn: Tipps vorhanden.

## Runde 2026-01-18 (5 kleinste Aufgaben dieser Runde) – erledigt
- [x] DOC-06: Aufgaben A–I strukturiert in TODO.md ergänzt (mit IDs + Kriterien). | fertig wenn: A–I-Backlog vorhanden.
- [x] DOC-07: README um Architektur, Start-Routine, Tests, Struktur und Barrierefreiheit erweitert. | fertig wenn: README enthält klare Abschnitte.
- [x] DOC-08: Styleguide (PEP8 + Projektregeln) als Markdown ergänzt. | fertig wenn: Styleguide-Datei vorhanden.
- [x] DOC-09: Weiterführende Laienvorschläge ergänzt (einfach erklärt). | fertig wenn: neue Tipps vorhanden.
- [x] DOC-10: todo.txt mit neuer Rundeliste synchronisiert. | fertig wenn: todo.txt deckungsgleich.

## Runde 2026-01-17 (5 kleinste Aufgaben dieser Runde) – erledigt
- [x] TODO-DOK-01: todo.txt-Kurzliste in TODO.md integriert (Release-Checkliste + IDs). | fertig wenn: Abschnitt deckungsgleich.
- [x] TODO-DOK-02: Kurz-Ist-Analyse um Synchronitäts-Lücke ergänzt. | fertig wenn: Analyse zeigt Risiko.
- [x] TODO-DOK-03: Offene Aufgaben mit Hinweis auf Synchronität ergänzt. | fertig wenn: klare Verbindung TODO.md ↔ todo.txt.
- [x] TODO-DOK-04: todo.txt mit IDs und Hinweis auf TODO.md aktualisiert. | fertig wenn: Kurzliste konsistent.
- [x] TODO-DOK-05: Laien-Tipps in TODO.md ergänzt und erweitert. | fertig wenn: Tipps vorhanden.

## Runde 2026-01-17 (5 kleinste Aufgaben dieser Runde) – erledigt
- [x] REL-GUI-01: GUI-Kontrastprüfung für alle Themes (Kontrast = Helligkeitsunterschied; Ziel ≥ 4,5:1). | fertig wenn: Dokument mit geprüften Werten vorhanden.
- [x] REL-GUI-02: Tastatur-Fokusreihenfolge in allen Hauptansichten prüfen (Fokus = aktuell ausgewähltes Element). | fertig wenn: durchgehend per Tab erreichbar.
- [x] REL-GUI-03: Screenreader-Labels ergänzen (Screenreader = Vorlese-Programm). | fertig wenn: alle Bedienelemente klare Labels haben.
- [x] REL-GUI-04: Fehler- und Statusmeldungen in einfacher Sprache mit Lösungsschritt. | fertig wenn: Meldungen erklären Ursache + nächsten Schritt.
- [x] REL-GUI-05: Barrierefreie Ladezustände (Busy-Indikator = Ladeanzeige) ausgeben. | fertig wenn: lange Aktionen zeigen Status an.

## Runde 2026-01-16 (5 kleinste Aufgaben dieser Runde) – erledigt
- [x] TODO-STR-01: TODO.md bereinigt (Duplikate entfernt, klare Abschnitte). | fertig wenn: Struktur eindeutig und doppelte Einträge entfernt.
- [x] TODO-STR-02: Offene Aufgaben analysiert und Risiken dokumentiert. | fertig wenn: Kurz-Ist-Analyse vorhanden.
- [x] TODO-STR-03: Backlog in klare Bereiche überführt (Start, Module, UX, Tests, Release). | fertig wenn: Aufgaben je Bereich gruppiert.
- [x] TODO-STR-04: todo.txt erstellt/aktualisiert (Release-Checkliste + nächste Schritte). | fertig wenn: todo.txt vorhanden und aktuell.
- [x] TODO-STR-05: Laienhinweise ergänzt (einfacher Text, Fachbegriffe erklärt). | fertig wenn: neue Aufgaben sind laienverständlich.

## Offene Aufgaben (kleinste zuerst)
Hinweis: Diese Liste entspricht der Kurzliste in `todo.txt` (je Runde 4 Tasks).
- [x] ARCH-07: Modul-API-Validator ergänzen (Validator = automatische Prüfung). | fertig wenn: `run`, `validateInput`, `validateOutput` werden geprüft.
- [x] ARCH-08: Modul-Check um Modul-API-Check erweitern (Check = Prüfung). | fertig wenn: klare Fehlermeldungen im Modul-Check erscheinen.
- [x] TEST-07: Tests für Modul-API-Validator ergänzen (Tests = automatische Prüfungen). | fertig wenn: Testfälle für Pflichtfunktionen grün sind.
- [x] DOC-14: MODUL_API.md um Modul-API-Check ergänzen. | fertig wenn: Hinweis auf automatische Prüfung dokumentiert ist.
- [x] DOC-11: Info-Dateien + README bereinigen und aktualisieren. | fertig wenn: alle Info-Dateien konsistent.
- [x] DOC-12: STRUKTUR.md mit vollständigem Verzeichnisbaum erstellen/pflegen. | fertig wenn: Baum + Pflichtdateien dokumentiert.
- [x] DOC-13: Dummy-Dateien für klar benötigte Dateien anlegen. | fertig wenn: Platzhalter klar gekennzeichnet.
- [x] OPS-01: Rundenlogik auf 4 Tasks umstellen (Test-Gate + Doku). | fertig wenn: Schwelle + Doku aktualisiert.

## Backlog (nach Bereichen, noch zu priorisieren)

### A. Architektur & Struktur
- [x] ARCH-01: Plugin-System mit zentraler Registry einführen (Registry = Modul-Liste). | fertig wenn: Module nur über Registry geladen werden.
- [x] ARCH-02: Modul-API definieren (Schnittstellen, Events, States). | fertig wenn: API-Dokument + Beispiel vorhanden.
- [x] ARCH-03: Zentralen Store einführen (Store = gemeinsamer Zustands-Speicher). | fertig wenn: Module lesen/schreiben zentral.
- [x] ARCH-04: Single Source of Truth für Theme/Settings/Logging. | fertig wenn: doppelte Logik entfernt.
- [x] ARCH-05: Projektstruktur final definieren und standardisieren. | fertig wenn: Struktur-Standard dokumentiert.
- [x] ARCH-06: Zentrales Logging-Modul implementieren (Logging = Protokoll). | fertig wenn: ein Logging-Modul genutzt.
- [x] ARCH-07: Modul-API-Validator ergänzen (Validator = automatische Prüfung). | fertig wenn: `run`, `validateInput`, `validateOutput` werden geprüft.
- [x] ARCH-08: Modul-Check um Modul-API-Check erweitern (Check = Prüfung). | fertig wenn: klare Fehlermeldungen im Modul-Check erscheinen.

### B. Performance & Stabilität
- [x] PERF-01: Lazy Loading für Module (spätes Laden) implementieren. | fertig wenn: Startzeit sinkt.
- [x] PERF-02: Debounce/Throttle für teure Aktionen (gebremstes Auslösen). | fertig wenn: UI bleibt flüssig.
- [x] PERF-03: Asynchrones Logging statt blockierend. | fertig wenn: Log schreibt ohne UI-Block.
- [x] PERF-04: JSON-Handling mit geprüftem Modell absichern (z. B. Pydantic). | fertig wenn: Validierung zentral.

### C. Bedienbarkeit
- [ ] UX-06: Globales Suchfeld im Dashboard (Dateien/Module/Texte). | fertig wenn: zentrale Suche nutzbar.
- [ ] UX-07: Favoritenleiste für oft genutzte Module. | fertig wenn: Favoriten sichtbar/umschaltbar.
- [ ] UX-08: Mini-Panels für Schnellaktionen (Export/Backup/Notes). | fertig wenn: Quick-Actions sichtbar.
- [ ] UX-09: Auto-Theming (Tag/Nacht-Erkennung) integrieren. | fertig wenn: Theme passt sich an.

### D. Barrierefreiheit (zusätzlich)
- [x] ACC-01: Kontrastmodus per Hotkey umschaltbar. | fertig wenn: Hotkey aktiv.
- [x] ACC-02: Zoom per STRG + Mausrad global aktivieren. | fertig wenn: Zoom überall funktioniert.
- [x] ACC-03: Screenreader-freundliche Bereichsstruktur. | fertig wenn: Bereiche semantisch benannt.

### E. Code-Sauberkeit
- [ ] CODE-01: Einheitliche Modulstruktur erzwingen (`module.json`, `main.py`, `ui/`). | fertig wenn: Validator blockiert Abweichung.
- [x] CODE-02: Setup-Skripte trennen (check_env.sh, bootstrap.sh, start.sh). | fertig wenn: Skripte getrennt vorhanden.
- [x] CODE-03: Starke Typisierung + klare Moduleingänge definieren. | fertig wenn: Typen + Entry-Contracts dokumentiert.
- [x] CODE-04: Styleguide (PEP8 + Projektregeln) als Markdown beilegen. | fertig wenn: Styleguide vorhanden.

### F. Sicherheit
- [x] SEC-01: Rechteprobleme beim Start automatisch korrigieren. | fertig wenn: Self-Repair behebt Rechte.
- [ ] SEC-02: PIN-Prozess mit Zufallssperre bei Fehleingabe. | fertig wenn: Sperre greift.
- [ ] SEC-03: Modul-Tests vor dem Laden erzwingen. | fertig wenn: defekte Module blockiert.
- [ ] SEC-04: Self-Repair-Bibliothek programmieren (Dateinamen/JSON/Rechte). | fertig wenn: Fehler automatisch reparierbar.

### G. Medienmodule
- [ ] MEDIA-01: Wavesurfer erweitern (Markers/Regions/Minimap/Exportprofil). | fertig wenn: Funktionen sichtbar.
- [ ] MEDIA-02: FFmpeg-Wrapper verbessern (Presets/Auto-Name/Fortschritt). | fertig wenn: Komfortfunktionen aktiv.
- [ ] MEDIA-03: Dateimanager erweitern (Quick-Rename/Tagging/Favoriten). | fertig wenn: Features vorhanden.

### H. Build & Release
- [ ] REL-05: .deb-Paket mit postinst-Initialisierung. | fertig wenn: postinst läuft.
- [ ] REL-06: AppImage mit integriertem Self-Check. | fertig wenn: Self-Check startet.
- [ ] REL-07: Build-Skripte automatisieren (`./build_all.sh`). | fertig wenn: Ein-Befehl-Build.

### I. Zentrale Komfortfunktionen

### J. Tests
- [x] TEST-07: Tests für Modul-API-Validator ergänzen (Tests = automatische Prüfungen). | fertig wenn: Testfälle für Pflichtfunktionen grün sind.

### K. Dokumentation
- [x] DOC-14: MODUL_API.md um Modul-API-Check ergänzen. | fertig wenn: Hinweis auf automatische Prüfung dokumentiert ist.
- [x] COM-01: One-Click-Diag (Tests + Ergebnisse in Fenster). | fertig wenn: Diagnosen sichtbar.
- [x] COM-02: Systemscanner vor Start (Rechte/JSON/Ordner). | fertig wenn: Scanner blockiert Fehler.
- [ ] COM-03: Recovery-Modus starten können. | fertig wenn: Start im Notfall.
- [x] COM-04: Ghost-Mode (Testmodus ohne Schreiben). | fertig wenn: keine Writes.

### Start & Launcher
- [ ] START-01: GUI-Launcher erstellen (Fenster, Theme, Layout). | fertig wenn: Startfenster stabil geöffnet.
- [ ] START-02: PIN-Login implementieren (PIN = kurze Zahlen-Passwort). | fertig wenn: Anmeldung funktioniert.
- [ ] START-03: Automatische Projektordner-Prüfung + Erzeugung. | fertig wenn: fehlende Ordner werden erstellt.
- [ ] START-04: Vollständige Self-Repair-Routine integrieren (Self-Repair = Selbstreparatur). | fertig wenn: fehlende Dateien automatisch ergänzt.
- [ ] START-05: Visuelle Fortschrittsanzeige beim Start. | fertig wenn: Prozent sichtbar.
- [ ] START-06: Fehleralternativen statt Abbruch. | fertig wenn: Vorschläge statt Stop.
- [ ] START-07: Gesundheitsprüfung vor Start (Health-Check = Systemprüfung). | fertig wenn: wichtige Dateien geprüft.
- [x] START-08: Start-Routine mit Nutzerfeedback für Abhängigkeiten (Dependencies = Abhängigkeiten). | fertig wenn: klare Hinweise + automatische Installation.
- [ ] START-09: Safe-Mode (schreibgeschützt) beim Start. | fertig wenn: Start ohne Schreibzugriffe möglich.
- [ ] START-10: Sandbox-Modus (virtuelle Umgebung) implementieren. | fertig wenn: Start in isolierter Umgebung.
- [ ] START-11: Ampelstatus + Fortschrittsanzeige beim Start. | fertig wenn: Ampel/Fortschritt sichtbar.

### Hauptfenster & Module
- [ ] MOD-01: Zentrales Hauptfenster bauen (Grid/9 Module = Raster mit 9 Bereichen). | fertig wenn: Module sichtbar.
- [ ] MOD-02: Modulmanager implementieren (laden/aktivieren/deaktivieren). | fertig wenn: Module steuerbar.
- [ ] MOD-03: Verschiebbare und skalierbare Modulfenster realisieren. | fertig wenn: Fenster ziehen/größern.
- [ ] MOD-04: Kollisionserkennung für Module (keine Überlappung). | fertig wenn: Kollision verhindert.
- [ ] MOD-05: Standardgrößen + Auto-Layout definieren. | fertig wenn: Module ordnen sich.
- [ ] MOD-06: Modul-Status visuell anzeigen (Ampel = grün/gelb/rot). | fertig wenn: Status sichtbar.

### Profil- & Datenstruktur
- [ ] DATA-01: Profil-System mit getrennten Projektordnern. | fertig wenn: Profile trennen Daten.
- [ ] DATA-02: Globale Settings als zentrale Datei. | fertig wenn: eine Settings-Datei existiert.
- [ ] DATA-03: Versionierung pro Modul + Änderungsverläufe. | fertig wenn: Historie sichtbar.
- [ ] DATA-04: Automatische Pflege von baumstruktur.txt/manifest.json/dummy_register.json. | fertig wenn: Dateien automatisch aktualisiert.
- [ ] DATA-05: Dateinamen-Suffix-Standards implementieren. | fertig wenn: Endungen folgen Standard.
- [ ] DATA-06: Trennung von Systemlogik und variablen Daten/Configs (Config = Konfiguration). | fertig wenn: klare Ordnertrennung umgesetzt.

### UX & Barrierefreiheit
- [ ] UX-01: Barrierefreiheits-Set ergänzen (Kontrast, ARIA, Tastatur). | fertig wenn: Checkliste erfüllt.
- [ ] UX-02: Großbutton-UI realisieren (Großbutton = große Schaltflächen). | fertig wenn: große Buttons nutzbar.
- [x] UX-03: Hilfetexte direkt in der GUI integrieren. | fertig wenn: Hilfe pro Ansicht.
- [ ] UX-04: Farbiges Sofort-Feedbacksystem (Erfolg/Fehler). | fertig wenn: klare Farben.
- [ ] UX-05: Perfektes Farb- und Kontrastverhalten mit mehreren Themes. | fertig wenn: Themes dokumentiert.
- [ ] UX-10: Grundtheme + Trash-Design implementieren. | fertig wenn: Basis-Theme + Papierkorb-Design vorhanden.
- [ ] UX-11: Basis-Iconset und Branding einfügen. | fertig wenn: Icons + Branding konsistent.

### Workflow-Logik
- [ ] FLOW-01: Globales Drag-and-Drop (Dateien/Module). | fertig wenn: Ziehen funktioniert.
- [ ] FLOW-02: Undo-/Redo-System global. | fertig wenn: Rückgängig möglich.
- [ ] FLOW-03: Autosave alle 10 Minuten. | fertig wenn: automatische Sicherung läuft.
- [ ] FLOW-04: Globales Event-/Signal-System. | fertig wenn: Module reagieren konsistent.
- [ ] FLOW-05: Rechte- und Schreibschutzsystem. | fertig wenn: Schutz aktiv.

### Kernmodule
- [ ] CORE-01: Dateimanager-Modul finalisieren. | fertig wenn: Kernfunktionen stabil.
- [ ] CORE-02: Bildvorschau-Modul einbauen. | fertig wenn: Vorschau sichtbar.
- [ ] CORE-03: Audio-Player-Modul integrieren. | fertig wenn: Audio abspielbar.
- [ ] CORE-04: FFmpeg-basierte Slideshow-Funktion erstellen (FFmpeg = Medien-Tool). | fertig wenn: Slideshow läuft.
- [ ] CORE-05: Wavesurfer-Modul implementieren (Wellenform, Regionen, Export). | fertig wenn: Wellenform sichtbar.
- [ ] CORE-06: To-Do-Modul mit Kalenderverknüpfung bauen. | fertig wenn: Kalender verknüpft.
- [ ] CORE-07: Konsolen-Modul (sicher) einbauen. | fertig wenn: sichere Eingaben.
- [ ] CORE-08: Wiki/Info-Modul mit 3 Ebenen (Thema–Quelle–Detail). | fertig wenn: 3 Ebenen nutzbar.
- [ ] CORE-09: Persona-Modul entwickeln. | fertig wenn: Profile nutzbar.
- [ ] CORE-10: Story-Sampler bauen. | fertig wenn: Stories verwaltbar.
- [ ] CORE-11: Projektorganizer erstellen. | fertig wenn: Projekte ordnen.
- [ ] CORE-12: Asset-Finder integrieren. | fertig wenn: Assets gefunden.
- [ ] CORE-13: Quote/Line-Manager erstellen. | fertig wenn: Zitate verwaltbar.
- [ ] CORE-14: Songtext- und Genre-Archive integrieren. | fertig wenn: Archive nutzbar.

### Speicherung & Export
- [ ] IO-01: Exportcenter (JSON, TXT, PDF, ZIP) implementieren. | fertig wenn: Exporte laufen.
- [ ] IO-02: Backup-System vollständig integrieren. | fertig wenn: Sicherungen laufen.
- [ ] IO-03: Testmodus (schreibgeschützt) einbauen. | fertig wenn: keine Schreibzugriffe.
- [ ] IO-04: Autosave in Logs protokollieren. | fertig wenn: Logs enthalten Autosave.
- [ ] IO-05: Selektive Exporte aktivieren. | fertig wenn: Teil-Exporte möglich.

### Fehler- & Strukturprüfung
- [ ] QA-01: JSON-Validator einbauen. | fertig wenn: JSON geprüft.
- [ ] QA-02: Automatische Dateinamenkorrektur. | fertig wenn: falsche Namen korrigiert.
- [x] QA-03: Fehlerklassifizierung (leicht/mittel/schwer). | fertig wenn: Fehlerstufe angezeigt.
- [x] QA-04: Ampelsystem für Dateifehler. | fertig wenn: Ampelstatus sichtbar.
- [x] QA-05: Modul-Selbsttests mit GUI-Ausgabe. | fertig wenn: Teststatus sichtbar.
- [x] QA-06: Jede Funktion validiert Eingabe und Ausgabe (Input/Output = Ein-/Ausgabe). | fertig wenn: Validierung vorhanden.
- [x] QA-07: Debugging- und Logging-Modus (Debugging = Fehlersuche). | fertig wenn: Modus schaltbar.
- [x] QA-08: Sandbox-Analyse erweitern (Sandbox = Testumgebung). | fertig wenn: Analyse deckt Sandbox-Risiken ab.

### Timeline & Visualisierung
- [ ] VIS-01: Timeline-Tool responsiv überarbeiten. | fertig wenn: passt sich an.
- [ ] VIS-02: Hover-Details, Zoom + flexible Abstände integrieren. | fertig wenn: Details und Zoom.
- [ ] VIS-03: Lesbarkeit + skalierende Elemente verbessern. | fertig wenn: besser lesbar.

### Dokumentation & Systempflege
- [ ] DOC-01: CHANGELOG-Automatik einbauen. | fertig wenn: Changelog automatisch.
- [x] DOC-02: README-/Doku-Autoupdater erstellen. | fertig wenn: Doku aktualisiert.
- [ ] DOC-03: Developer-Panel im Dashboard integrieren. | fertig wenn: Panel sichtbar.
- [x] DOC-04: Interne Standards im Tool anzeigen (Konfig, Regeln, Tests). | fertig wenn: Standards sichtbar.
- [x] DOC-05: Weiterführende Laienvorschläge ergänzen (Tipps für Neulinge). | fertig wenn: Tipps vorhanden.
- [x] DOC-11: Info-Dateien + README bereinigen und aktualisieren. | fertig wenn: alle Info-Dateien konsistent.
- [x] DOC-12: STRUKTUR.md mit vollständigem Verzeichnisbaum erstellen/pflegen. | fertig wenn: Baum + Pflichtdateien dokumentiert.
- [x] DOC-13: Dummy-Dateien für klar benötigte Dateien anlegen. | fertig wenn: Platzhalter klar gekennzeichnet.
- [x] OPS-01: Rundenlogik auf 4 Tasks umstellen (Test-Gate + Doku). | fertig wenn: Schwelle + Doku aktualisiert.

### Tests & Stabilität
- [x] TEST-01: Automatisierte GUI-Tests einbinden. | fertig wenn: GUI-Tests laufen.
- [x] TEST-02: Fehler-Simulation (Laienfehler) integrieren. | fertig wenn: klare Fehlerfälle.
- [x] TEST-03: Robustheitstest für fehlende Rechte/beschädigte Dateien. | fertig wenn: System bleibt stabil.
- [x] TEST-04: Modulübergreifende Funktionschecks implementieren. | fertig wenn: Checks laufen.
- [x] TEST-05: Vollautomatische Codequalität- und Formatprüfung (Linting/Formatting = Code-Check). | fertig wenn: Checks laufen automatisch.
- [x] TEST-06: Vollautomatische Testausführung über Startroutine (Test-Automatik). | fertig wenn: Tests starten selbst.

### Release-Build
- [ ] REL-01: .deb-Paket bauen. | fertig wenn: Paket erzeugt.
- [ ] REL-02: Offizielles Icon-Set (Provoware-Look) integrieren. | fertig wenn: Icons vorhanden.
- [ ] REL-03: One-File-Distribution (AppImage/PyInstaller). | fertig wenn: Ein-Datei-Build.
- [ ] REL-04: ZIP-Auto-Export alle fünf Entwicklungsschritte. | fertig wenn: ZIP-Automatik läuft.
- [ ] REL-08: Desktop-File + Icon-Integration für Linux. | fertig wenn: Desktop-Startdatei vorhanden.

### Abschlusslogik
- [ ] END-01: Logout: Save-All + sauberes Schließen. | fertig wenn: Daten gespeichert.
- [ ] END-02: End-Audit-Check (Release-Status) integrieren. | fertig wenn: Audit sichtbar.

## Archiv (erledigt, konsolidiert)
- [x] 2026-01-07: Setup, Architektur-Standards, Modul-Schnittstelle, UI-Farben, Logging, To-Do-Validierung, Modul-Check, Basis-Tests.
- [x] 2026-01-09: Launcher-GUI, Themes, Fokus, Start-Routine, Abhängigkeiten, Modul-Check, Testskript-Hilfen.
- [x] 2026-01-10: Pytest + Ruff + Black als Standard-Checks.
- [x] 2026-01-11: Notiz-Editor und Charakter-Modul integriert.
- [x] 2026-01-12: Download-Aufräumen + Datei-Suche mit Undo.
- [x] 2026-01-13: Health-Check, Testskript-Verbesserungen, Pfad-Validierung.
- [x] 2026-01-14: Health-Check bereinigt, Changelog-Duplikate entfernt.
- [x] 2026-01-15: Health-Check Self-Repair, Start-Routine Self-Repair.
- [x] 2026-01-16: Doku-Updates (PROJEKT_INFO, ANALYSE_BERICHT, Standards, Release-Checkliste).
