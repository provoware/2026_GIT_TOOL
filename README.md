# 2026_GIT_TOOL

## Kurzbeschreibung
Dieses Projekt ist ein sauberer Neuaufbau mit Fokus auf Robustheit, Nachvollziehbarkeit und Linux. Ziel ist ein barrierefreies Tool, das verständlich bleibt und klare Standards nutzt.

## Ist-Analyse (aktueller Stand)
- Es gibt noch keine vollständige Anwendung mit allen geplanten Modulen; die Start-Routine liegt als Skript vor.
- Die Ordnertrennung ist angelegt (Systemlogik, Konfiguration, Daten), weitere Trennung ist in Arbeit.
- Wichtige Qualitätsziele (Barrierefreiheit, Logging, automatische Prüfungen) sind dokumentiert und teilweise umgesetzt.
- Es fehlen zentrale Architektur-Bausteine wie Plugin-Registry (Registry = zentrale Modul-Liste), Modul-API und ein gemeinsamer Store (Store = Zustands-Speicher).
- Performance- und Stabilitätsmaßnahmen (Lazy Loading, asynchrones Logging) sind noch nicht umgesetzt.

## Ziele (in Arbeit)
- **Barrierefreiheit**: Tastaturbedienung, hoher Kontrast und verständliche Meldungen.
- **Automatische Startprüfung**: Start-Routine prüft Struktur, löst Abhängigkeiten und gibt Nutzer-Feedback.
- **Qualitätssicherung**: Automatische Tests und Codeformatierung (Codeformat = automatische Einheitlichkeit des Codes).
- **Trennung von Bereichen**: Systemlogik getrennt von variablen Dateien und Konfiguration.
- **Einheitliche Standards**: Klare Modul-Schnittstellen und gemeinsames Datenmodell.

## Schnellstart (Doku + vorhandene Skripte)
Die Start-Routine existiert als Skript. Beispiel (Befehl = Kommandozeilen-Anweisung):
- `./scripts/start.sh` (Start-Routine = automatischer Projektstart mit Prüfungen und Feedback)
- `./scripts/run_tests.sh` (Tests + Codequalität = automatische Prüfung von Funktionen und Stil)
- `./scripts/repo_basis_check.sh` (Repo-Check = Basisprüfung für Git-Remote)

## Release-Checks & Test-Automatik
- **Start-Routine** prüft automatisch Struktur, Abhängigkeiten und Module mit klaren Hinweisen (Feedback).
- **Test-Automatik** startet Tests automatisch nach einer abgeschlossenen Runde (5 erledigte Tasks).
- **Modulverbund-Checks** prüfen konsistente Moduleinträge, Selftests und Manifest-IDs.
- **Codequalität & Formatierung** laufen automatisch über Ruff (Linting = Regelprüfung) und Black (Formatierung).

## Architektur & Struktur (geplant)
- **Plugin-System** mit Registry (Registry = zentrale Modul-Liste).
- **Modul-API** mit klaren Schnittstellen, Events und States (State = Zustand).
- **Zentraler Store** (Store = gemeinsamer Zustands-Speicher) als Single Source of Truth (einzige Quelle) für Theme, Settings und Logging.
- **Trennung von System/Config/Daten**: Code in `src/` und `system/`, Konfiguration in `config/`, variable Daten in `data/`.

## Performance & Stabilität (geplant)
- **Lazy Loading** (spätes Laden) für Module, um die Startzeit zu verkürzen.
- **Debounce/Throttle** (gebremstes Auslösen) für teure Aktionen, damit die GUI flüssig bleibt.
- **Asynchrones Logging** (nicht blockierend), damit Logs die Oberfläche nicht bremsen.
- **JSON-Validierung** über geprüftes Modell (z. B. Pydantic) für sichere Daten.

## Bedienbarkeit (geplant)
- Globales Suchfeld im Dashboard (Dateien, Module, Texte).
- Favoritenleiste für oft genutzte Module.
- Mini-Panels für Schnellaktionen (Export, Backup, Notes).
- Auto-Theming (Tag/Nacht-Erkennung).

## Barrierefreiheit
- Tastaturbedienung (Tab/Enter/Esc) für alle Funktionen.
- Kontrastmodus per Hotkey (Schnelltaste).
- Zoom per STRG + Mausrad (global).
- Screenreader-freundliche Struktur (Screenreader = Vorlese-Programm).

## Bedienung in einfacher Sprache
- **Starten**: Nutze `./scripts/start.sh` (Start-Routine = automatischer Start mit Prüfungen).
- **Fehler**: Fehlertexte sollen klar erklären, was passiert ist und was du tun kannst.
- **Tastatur**: Jede Funktion soll ohne Maus erreichbar sein.

## Barrierefreiheit und Kontrast
- Hoher Kontrast zwischen Text und Hintergrund.
- Deutliche Schaltflächen (Buttons) mit klarer Beschriftung.
- Mehrere Farbthemen (Themes) zur Auswahl (z. B. Hell, Dunkel, Kontrast).

## Logging und Debugging
- **Logging (Protokollierung)**: Jede Aktion soll protokolliert werden.
- **Debugging (Fehlersuche)**: Optionaler Modus mit mehr Details.

## Sandbox-Analyse (Kurzfassung)
- **Risiko**: Ohne Sandbox-Regeln können Module zu viele Rechte erhalten.
- **Schutz**: Start ohne Adminrechte, Pfadgrenzen, Safe-Mode (schreibgeschützt) und klare Netzwerkhinweise.

## Weiterführende Vorschläge für Laien
- Lies die Datei `todo.txt`, um die nächsten kleinen Schritte zu sehen.
- Nutze kurze, klare Commit-Nachrichten, z. B. „Doku: README erweitert“.
- Arbeite Schritt für Schritt: erst verstehen, dann ändern, dann testen.
- Starte die Tests mit `./scripts/run_tests.sh` (Tests = automatische Prüfroutinen).
- Bei Fehlern: `logs/test_run.log` öffnen (Log = Protokoll) und den letzten Eintrag lesen.
- Nutze `python system/health_check.py --root . --self-repair` (Self-Repair = Selbstreparatur), wenn Ordner fehlen.

## Dateiübersicht
- `README.md`: Einfache Projekt-Anleitung.
- `STYLEGUIDE.md`: Styleguide (PEP8 + Projektregeln).
- `DEV_DOKU.md`: Entwickler-Dokumentation und Standards.
- `todo.txt`: Offene Aufgaben im Überblick.
- `CHANGELOG.md`: Änderungen je Version.

## Lizenz
Noch nicht festgelegt.
