# Standards

## Zweck
Diese Datei definiert verbindliche Standards für alle Module, den Launcher und die Start‑/Test‑Routine. Ziel ist Stabilität, Wartbarkeit und barrierefreie Bedienung.

## Verbindliche Projektstruktur
- `src/`: Systemlogik (stabile Kernlogik, keine variablen Daten).
- `config/`: Konfiguration (änderbar ohne Code, z. B. Module-Liste, Themes).
- `data/`: Variable Daten und Laufzeitdateien.
- `logs/`: Protokolle (Fehler, Debug, Ereignisse).
- `scripts/`: Start‑ und Prüfskripte (automatisierte Checks).
- `modules/`: Einzelne Module (je Modul eigener Ordner).

## Trennung von Systemlogik und variablen Dateien
- **Systemlogik** liegt ausschließlich in `src/` und `system/`.
- **Variable Dateien** (Nutzdaten/Protokolle) liegen ausschließlich in `data/` und `logs/`.
- **Konfiguration** liegt ausschließlich in `config/` und darf keine Logik enthalten.
- Module lesen Konfigurationen, schreiben aber nur Daten in `data/` (nie in `config/`).

## Einheitliche Benennung (Dateien/Module)
- Ordner‑ und Dateinamen: **klein**, **unterstrich** (`snake_case`), **ohne Leerzeichen**.
- Modul‑ID = Ordnername (z. B. `modules/datei_suche`).
- Pflichtdateien pro Modul:
  - `modules/<modul_id>/manifest.json`
  - `modules/<modul_id>/module.py`
- Konfig‑Dateien tragen den Modul‑ID‑Namen (z. B. `config/datei_suche.json`).
- Daten‑Dateien tragen den Modul‑ID‑Namen (z. B. `data/datei_suche_log.json`).

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

## Barrierefreiheit & Themes
- Tastaturbedienung (Tab, Enter, Esc) überall möglich.
- Kontraststarke Farben und klare Buttons.
- Mehrere Themes in `config/themes/` (z. B. Hell, Dunkel, Hoher Kontrast).

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
