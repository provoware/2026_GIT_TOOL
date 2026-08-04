# Provoware Memo – vollständige integrierte Browseroberfläche

## Korrigierte Architektur

Die Browseroberfläche ist keine reduzierte Ersatzanwendung. Sie ist die gemeinsame Bedienoberfläche des bestehenden Haupttools **Provoware Memo** und greift über geprüfte Modulverträge auf den vorhandenen Funktionsbestand zu.

## Enthaltene Hauptbereiche

- Dashboard mit Kennzahlen, Schnellaktionen, Favoriten und letzten Ereignissen
- globale Suche über Notizen, Aufgaben, Charaktere, Archive und Module
- Memo- und Notizverwaltung mit Vorlagen, Filtern und Favoriten
- Aufgabenverwaltung und Kalenderansichten für Jahr, Monat und Woche
- Charakterverwaltung mit Vorlagen, Eigenschaften, Zielen und Favoriten
- gemeinsame Archivdatenbank mit Archiv- und Eintragsverwaltung
- Datei-Manager mit Ordnernavigation, sortierbarer Liste, Metadaten und großer Bildvorschau
- Datei-Suche, Organisation, Download-Aufräumen, Tags, Favoriten und Undo
- Wavesurfer- und FFmpeg-Funktionen
- Profilverwaltung
- vollständiger Aktionskatalog aller registrierten Module
- Backup, Export, selektiver Export, Diagnose, Systemscan, Audit, Standards, Logs und Fortschritt
- Systemstatus, Hilfe, Shortcuts und Ereignisfooter

## Fehlerursache der vorherigen Oberfläche

Die vorherige JavaScript-Version band beim Initialisieren Ereignisse an nicht mehr vorhandene HTML-IDs (`refreshAll` und `calendarLoad`). Die erste fehlende Referenz löste eine Ausnahme aus; alle nachfolgenden Klickbindungen wurden dadurch übersprungen.

Die Korrektur verwendet eine zentrale Ereignisdelegation auf Dokumentebene. Dynamisch erzeugte Buttons und Formulare funktionieren damit ebenfalls. Globale JavaScript- und Promise-Fehler werden sichtbar in der Oberfläche angezeigt.

## Sicherheits- und Datenprinzipien

- Serverbindung ausschließlich an Loopback
- Google Chrome als verbindlicher Browser
- keine beliebigen Modul- oder Shellaufrufe; nur explizit freigegebene Aktionen
- schreibende oder folgenreiche Aktionen mit Bestätigung
- Datei-Browser nur innerhalb des Benutzerordners beziehungsweise des Projektordners
- Bildvorschau über kontrollierten lokalen Endpunkt
- gemeinsame bestehende SQLite-Archivdatenbank
- kein separates Archivfenster im Normalbetrieb

## Abnahme

Die Abnahme umfasst:

- vollständige Python-Test-Suite einschließlich nativer Tk-/Xvfb-Regressionen
- statische UI-Vertragsprüfung aller Navigationen und zwingenden Elemente
- Modulaktionskatalog und read-only Modul-Snapshots
- echte HTTP-, Datei- und Cache-Header-Prüfungen
- echte Google-Chrome-Headless-Interaktionen: alle Navigationsbuttons, Modaldialog und Datei-Manager
- JavaScript-, Python-, Shell-, Ruff- und Black-Prüfungen
- isolierte vollständige Startroutine
- bereinigten vollständigen Projekt-Export
