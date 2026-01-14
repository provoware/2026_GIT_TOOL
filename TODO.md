# TODO (strukturiert, barrierefrei, laienverständlich)

## Regeln (verbindlich)
- Pro Runde werden **genau 5 kleine Aufgaben** erledigt.
- Erst **kurz analysieren**, dann **umsetzen**, dann **testen**, dann **dokumentieren**.
- Fachwörter werden **einfach erklärt** (Fachbegriff in Klammern mit kurzer Erklärung).

## Kurz-Ist-Analyse (offene Aufgaben)
- **Risiko**: GUI-Barrierefreiheit ist noch nicht vollständig geprüft (Kontrast, Fokus, Screenreader). → Gefahr: Nutzerinnen und Nutzer können die Oberfläche nicht sicher bedienen.
- **Lücke**: Es fehlt eine konsistente, sichtbare Statusanzeige bei langen Aktionen (Busy-Indikator = Ladeanzeige).
- **Schwachstelle**: Fehlermeldungen sind noch nicht überall in einfacher Sprache mit Lösungsschritt vorhanden.
- **Abhängigkeit**: Für GUI-Tests fehlt eine automatisierte Routine (GUI-Tests = Tests für Benutzeroberflächen).
- **Best Practice**: Aufgaben sollten eindeutige IDs haben und pro Bereich gruppiert sein.

## Runde 2026-01-16 (5 kleinste Aufgaben dieser Runde) – erledigt
- [x] TODO-STR-01: TODO.md bereinigt (Duplikate entfernt, klare Abschnitte). | fertig wenn: Struktur eindeutig und doppelte Einträge entfernt.
- [x] TODO-STR-02: Offene Aufgaben analysiert und Risiken dokumentiert. | fertig wenn: Kurz-Ist-Analyse vorhanden.
- [x] TODO-STR-03: Backlog in klare Bereiche überführt (Start, Module, UX, Tests, Release). | fertig wenn: Aufgaben je Bereich gruppiert.
- [x] TODO-STR-04: todo.txt erstellt/aktualisiert (Release-Checkliste + nächste Schritte). | fertig wenn: todo.txt vorhanden und aktuell.
- [x] TODO-STR-05: Laienhinweise ergänzt (einfacher Text, Fachbegriffe erklärt). | fertig wenn: neue Aufgaben sind laienverständlich.

## Offene Aufgaben (kleinste zuerst)
- [ ] REL-GUI-01: GUI-Kontrastprüfung für alle Themes (Kontrast = Helligkeitsunterschied; Ziel ≥ 4,5:1). | fertig wenn: Dokument mit geprüften Werten vorhanden.
- [ ] REL-GUI-02: Tastatur-Fokusreihenfolge in allen Hauptansichten prüfen (Fokus = aktuell ausgewähltes Element). | fertig wenn: durchgehend per Tab erreichbar.
- [ ] REL-GUI-03: Screenreader-Labels ergänzen (Screenreader = Vorlese-Programm). | fertig wenn: alle Bedienelemente klare Labels haben.
- [ ] REL-GUI-04: Fehler- und Statusmeldungen in einfacher Sprache mit Lösungsschritt. | fertig wenn: Meldungen erklären Ursache + nächsten Schritt.
- [ ] REL-GUI-05: Barrierefreie Ladezustände (Busy-Indikator = Ladeanzeige) ausgeben. | fertig wenn: lange Aktionen zeigen Status an.
- [ ] REL-GUI-06: Responsive Layout für kleine Auflösungen prüfen. | fertig wenn: Bedienung bleibt möglich.

## Backlog (nach Bereichen, noch zu priorisieren)

### Start & Launcher
- [ ] START-01: GUI-Launcher erstellen (Fenster, Theme, Layout). | fertig wenn: Startfenster stabil geöffnet.
- [ ] START-02: PIN-Login implementieren (PIN = kurze Zahlen-Passwort). | fertig wenn: Anmeldung funktioniert.
- [ ] START-03: Automatische Projektordner-Prüfung + Erzeugung. | fertig wenn: fehlende Ordner werden erstellt.
- [ ] START-04: Vollständige Self-Repair-Routine integrieren (Self-Repair = Selbstreparatur). | fertig wenn: fehlende Dateien automatisch ergänzt.
- [ ] START-05: Visuelle Fortschrittsanzeige beim Start. | fertig wenn: Prozent sichtbar.
- [ ] START-06: Fehleralternativen statt Abbruch. | fertig wenn: Vorschläge statt Stop.
- [ ] START-07: Gesundheitsprüfung vor Start (Health-Check = Systemprüfung). | fertig wenn: wichtige Dateien geprüft.
- [ ] START-08: Start-Routine mit Nutzerfeedback für Abhängigkeiten (Dependencies = Abhängigkeiten). | fertig wenn: klare Hinweise + automatische Installation.

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
- [ ] UX-03: Hilfetexte direkt in der GUI integrieren. | fertig wenn: Hilfe pro Ansicht.
- [ ] UX-04: Farbiges Sofort-Feedbacksystem (Erfolg/Fehler). | fertig wenn: klare Farben.
- [ ] UX-05: Perfektes Farb- und Kontrastverhalten mit mehreren Themes. | fertig wenn: Themes dokumentiert.

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

### Fehler- & Strukturprüfung
- [ ] QA-01: JSON-Validator einbauen. | fertig wenn: JSON geprüft.
- [ ] QA-02: Automatische Dateinamenkorrektur. | fertig wenn: falsche Namen korrigiert.
- [ ] QA-03: Fehlerklassifizierung (leicht/mittel/schwer). | fertig wenn: Fehlerstufe angezeigt.
- [ ] QA-04: Ampelsystem für Dateifehler. | fertig wenn: Ampelstatus sichtbar.
- [ ] QA-05: Modul-Selbsttests mit GUI-Ausgabe. | fertig wenn: Teststatus sichtbar.
- [ ] QA-06: Jede Funktion validiert Eingabe und Ausgabe (Input/Output = Ein-/Ausgabe). | fertig wenn: Validierung vorhanden.
- [ ] QA-07: Debugging- und Logging-Modus (Debugging = Fehlersuche). | fertig wenn: Modus schaltbar.

### Timeline & Visualisierung
- [ ] VIS-01: Timeline-Tool responsiv überarbeiten. | fertig wenn: passt sich an.
- [ ] VIS-02: Hover-Details, Zoom + flexible Abstände integrieren. | fertig wenn: Details und Zoom.
- [ ] VIS-03: Lesbarkeit + skalierende Elemente verbessern. | fertig wenn: besser lesbar.

### Dokumentation & Systempflege
- [ ] DOC-01: CHANGELOG-Automatik einbauen. | fertig wenn: Changelog automatisch.
- [ ] DOC-02: README-/Doku-Autoupdater erstellen. | fertig wenn: Doku aktualisiert.
- [ ] DOC-03: Developer-Panel im Dashboard integrieren. | fertig wenn: Panel sichtbar.
- [ ] DOC-04: Interne Standards im Tool anzeigen (Konfig, Regeln, Tests). | fertig wenn: Standards sichtbar.
- [ ] DOC-05: Weiterführende Laienvorschläge ergänzen (Tipps für Neulinge). | fertig wenn: Tipps vorhanden.

### Tests & Stabilität
- [ ] TEST-01: Automatisierte GUI-Tests einbinden. | fertig wenn: GUI-Tests laufen.
- [ ] TEST-02: Fehler-Simulation (Laienfehler) integrieren. | fertig wenn: klare Fehlerfälle.
- [ ] TEST-03: Robustheitstest für fehlende Rechte/beschädigte Dateien. | fertig wenn: System bleibt stabil.
- [ ] TEST-04: Modulübergreifende Funktionschecks implementieren. | fertig wenn: Checks laufen.
- [ ] TEST-05: Vollautomatische Codequalität- und Formatprüfung (Linting/Formatting = Code-Check). | fertig wenn: Checks laufen automatisch.
- [ ] TEST-06: Vollautomatische Testausführung über Startroutine (Test-Automatik). | fertig wenn: Tests starten selbst.

### Release-Build
- [ ] REL-01: .deb-Paket bauen. | fertig wenn: Paket erzeugt.
- [ ] REL-02: Offizielles Icon-Set (Provoware-Look) integrieren. | fertig wenn: Icons vorhanden.
- [ ] REL-03: One-File-Distribution (AppImage/PyInstaller). | fertig wenn: Ein-Datei-Build.
- [ ] REL-04: ZIP-Auto-Export alle fünf Entwicklungsschritte. | fertig wenn: ZIP-Automatik läuft.

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
