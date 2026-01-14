# Standards

## Zweck
Diese Datei definiert verbindliche Standards für alle Module, den Launcher und die Start‑/Test‑Routine. Ziel ist Stabilität, Wartbarkeit und barrierefreie Bedienung.

## Verbindliche Projektstruktur
- `src/`: Systemlogik (stabile Kernlogik, keine variablen Daten).
- `system/`: Systemskripte/Checks (Start‑/Validierungslogik).
- `config/`: Konfiguration (änderbar ohne Code, z. B. Module-Liste, Themes).
- `data/`: Variable Daten und Laufzeitdateien.
- `logs/`: Protokolle (Fehler, Debug, Ereignisse).
- `scripts/`: Start‑ und Prüfskripte (automatisierte Checks).
- `modules/`: Einzelne Module (je Modul eigener Ordner).
- `tests/`: Automatisierte Tests.

## Trennung von Systemlogik und variablen Dateien
- **Systemlogik** liegt ausschließlich in `src/` und `system/`.
- **Variable Dateien** (Nutzdaten/Protokolle) liegen ausschließlich in `data/` und `logs/`.
- **Konfiguration** liegt ausschließlich in `config/` und darf keine Logik enthalten.
- Module lesen Konfigurationen, schreiben aber nur Daten in `data/` (nie in `config/`).
- Der Struktur-Check (`system/structure_checker.py`) prüft diese Trennung automatisch.

## Einheitliche Benennung (Dateien/Module)
- Ordner‑ und Dateinamen: **klein**, **unterstrich** (`snake_case`), **ohne Leerzeichen**.
- Modul‑ID = Ordnername (z. B. `modules/datei_suche`).
- Modul‑ID‑Regel: `^[a-z0-9]+(_[a-z0-9]+)*$` (nur Kleinbuchstaben, Zahlen, Unterstrich).
- Pflichtdateien pro Modul:
  - `modules/<modul_id>/manifest.json`
  - `modules/<modul_id>/module.py`
- Strukturregeln werden zusätzlich in `config/module_structure.json` gepflegt
  (Pflicht-Entry + Ausnahmen für Sonderfälle).
- Konfig‑Dateien tragen den Modul‑ID‑Namen (z. B. `config/datei_suche.json`).
- Daten‑Dateien tragen den Modul‑ID‑Namen (z. B. `data/datei_suche_log.json`).
- Modul‑Pfad in `config/modules.json` muss **genau** `modules/<modul_id>` sein.

## Gemeinsames Datenmodell
- Zentrales Schema in `src/core/data_model.py` ist **verbindlich**.
- Module nutzen dieses Schema für To‑Dos/Kalender, damit Austauschbarkeit gewährleistet ist.

## Modulstandard (Template)
Jedes Modul besitzt:
- `modules/<modulname>/manifest.json`: Metadaten (Name, Version, Kurzbeschreibung, benötigte Berechtigungen).
- `modules/<modulname>/module.<ext>`: Implementierung.

Verbindliche Modul‑Schnittstelle (gleiches Schema in allen Modulen):
- `init(context)` → Initialisierung (z. B. Ressourcen prüfen).
- `run(input)` → Hauptlogik.
- `exit()` → Aufräumen, Logs schreiben.
- `validateInput(input)` → Eingabe prüfen (Fehler in einfacher Sprache).
- `validateOutput(output)` → Ausgabe prüfen (Fehler in einfacher Sprache).

Fehlertexte sind **Deutsch, klar, laienverständlich**.

## Launcher‑Registrierung
- Zentrale Liste in `config/modules.json`.
- Einträge enthalten `id`, `name`, `path`, `enabled`, `description`.
- `path` zeigt auf den Modulordner (z. B. `modules/status`), nicht auf die Datei.
- Launcher lädt **nur** diese Liste, keine Sonderlogik pro Modul.

## Start‑Routine (automatisch, autonom)
Die Startroutine erledigt vollständig und selbstständig:
1. **Strukturprüfung**: Fehlende Ordner werden automatisch erstellt.
2. **Abhängigkeitsprüfung** (Dependencies): Prüft benötigte Pakete und löst sie automatisch.
3. **Feedback an Nutzende**: Fortschritt in Prozent + klare Meldungen.
4. **Fehlerbehandlung**: Verständliche Hinweise und Lösungsvorschläge.
5. **Modul-Check**: Prüft aktivierte Module, Manifest und Entry-Dateien vor dem Start der Übersicht.

## Logging & Debugging
- Einheitliches Logformat: Zeitstempel, Modul, Ebene, Nachricht.
- Debug‑Modus per `config/debug.json` aktivierbar.
- Logs immer in `logs/` ablegen, nie im Code oder in `config/`.

## Fehlerhandling (verbindlich)
- **Struktur**: Titel → Ursache → Lösungsschritt → Hinweis auf Logdatei.
- **Lösungsschritt** ist Pflicht (konkreter nächster Schritt).
- **Schweregrad** angeben (leicht/mittel/schwer), sofern ermittelt.
- **Kein Abbruch ohne Alternative**: Wenn möglich, eine sichere Alternative anbieten.
- **Logging**: Fehler immer mit Kontext (Modul, Aktion, Datei) protokollieren.

Beispiel (einfach, laienverständlich):
> Fehler: Modul-Check fehlgeschlagen.  
> Ursache: Modulordner fehlt.  
> Lösung: Ordner `modules/status` anlegen und erneut starten.  
> Hinweis: Details stehen in `logs/start_run.log`.

## Barrierefreiheit & Themes
- Tastaturbedienung (Tab, Enter, Esc) überall möglich.
- Kontraststarke Farben und klare Buttons.
- Mehrere Themes liegen in den Modul-Configs (`config/*.json`) und in `config/launcher_gui.json`.
- Mindestens ein **Kontrast-Theme** ist pro Modul/Launcher Pflicht.

## UI-Abstände & visuelle Führung (verbindlich)
- Einheitliches **Abstands-Raster** über Tokens in `config/launcher_gui.json` (`layout.*`).
- Standard-Tokens: `gap_xs=4`, `gap_sm=8`, `gap_md=12`, `gap_lg=16`, `gap_xl=24`.
- Buttons/Felder nutzen zentrale Werte (`button_padx`, `button_pady`, `field_padx`, `field_pady`).
- **Visuelle Führung**: klare Überschriften, gruppierte Bereiche, eindeutige Primäraktion.
- **Kontrast & Fokus**: deutlicher Fokusrahmen (`focus_thickness`) und hohe Lesbarkeit.

## Start-Modi (Safe-Mode & Sandbox)
- **Safe-Mode**: reine Prüfungen ohne Schreibzugriffe (`./scripts/start.sh --safe-mode`).
- **Ghost-Mode**: Alias für Safe-Mode (Testmodus ohne Schreiben).
- **Sandbox**: Start in isolierter Kopie, Schreibzugriffe bleiben in der Sandbox.

## Tests & Codequalität
- Automatische Tests für Kernfunktionen.
- Code‑Formatierung (Formatter) ist verpflichtend.
- Statische Prüfungen (Lint) laufen vor jedem Release.

## Eingabe‑ und Ausgabekontrolle
- Jede Funktion validiert Eingaben und Ausgaben.
- Fehler werden **verständlich** beschrieben und enthalten einen Lösungstipp.

## Dateinamen & Sicherheit
- Dateinamen sind Linux‑konform, eindeutig und ohne Leerzeichen.
- Keine Überschreibungen ohne Bestätigung.

## Laienhilfe (einfache Sprache)
- **Status prüfen**: `git status` (zeigt Änderungen).
- **Änderungen sichern**: `git add .` (legt Änderungen bereit) und `git commit -m "Kurztext"`.
- **Prüfungen starten**: `./scripts/checks.sh` (falls vorhanden, startet Tests und Formatierung).

Glossar (Fachbegriffe):
- **Dependencies** (Abhängigkeiten): Zusätzliche Pakete, die ein Programm braucht.
- **Lint** (Stilprüfung): Automatischer Check für sauberen Code.
- **Formatter** (Formatierer): Tool, das Code einheitlich formatiert.
