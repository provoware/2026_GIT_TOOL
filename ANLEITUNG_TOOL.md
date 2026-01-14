# ANLEITUNG_TOOL (einfach erklärt, Schritt für Schritt)

> **Ziel:** Diese Anleitung erklärt das Tool in **einfacher Sprache**. Fachbegriffe stehen in Klammern.
> Jeder Punkt enthält einen **Tipp**, damit Einsteiger:innen schneller vorankommen.

## 1) Schnellstart (Schritt für Schritt)
1. **Projektordner öffnen** (Ordner = Speicherort der Dateien).
   - **Befehl:** `cd /workspace/2026_GIT_TOOL`
   - **Tipp:** Arbeite immer im Projektordner, damit Pfade stimmen.
2. **Start-Routine ausführen** (Start-Routine = automatische Prüfungen + Start).
   - **Befehl:** `./klick_start.sh`
   - **Tipp:** Die Start-Routine prüft automatisch Struktur, Abhängigkeiten und Module.
3. **GUI-Übersicht nutzen** (GUI = Oberfläche mit Buttons).
   - **Aktion:** In der GUI „Übersicht aktualisieren“ drücken.
   - **Tipp:** Mit **Tab** kannst du alle Buttons ohne Maus erreichen.

## 2) Vollautomatische Prüfungen (Autopilot)
1. **System-Scan vorab** (Scan = Vorabprüfung ohne Schreiben).
   - **Befehl:** `./scripts/system_scan.sh`
   - **Tipp:** So erkennst du Probleme, bevor etwas geändert wird.
2. **Health-Check mit Selbstreparatur** (Self-Repair = automatische Reparatur).
   - **Befehl:** `python system/health_check.py --root . --self-repair`
   - **Tipp:** Ideal nach dem ersten Klonen oder wenn Ordner fehlen.
3. **Abhängigkeiten prüfen/installieren** (Dependencies = benötigte Pakete).
   - **Befehl:** `python system/dependency_checker.py --requirements config/requirements.txt`
   - **Tipp:** Der Check meldet klar, was fehlt und installiert bei Bedarf.

## 3) Tests, Codequalität, Format (vollautomatisch)
1. **Kompletter Testlauf** (Tests = automatische Prüfroutinen).
   - **Befehl:** `./scripts/run_tests.sh`
   - **Tipp:** Das Skript enthält Linting (Regelprüfung) und Formatierung (Stilprüfung).
2. **Nur JSON prüfen** (Validator = Strukturprüfung).
   - **Befehl:** `python system/json_validator.py --root .`
   - **Tipp:** Schnelltest für fehlerhafte JSON-Dateien.
3. **Nur Modul-Checks** (Modul-Check = Manifest + Entry prüfen).
   - **Befehl:** `python system/module_checker.py --config config/modules.json`
   - **Tipp:** Hilfreich, wenn ein Modul nicht lädt.

## 4) Modul- und Funktionsschwerpunkte (was kann welches Modul?)
- **download_aufraeumen**: Dateien im Download-Ordner prüfen, organisieren und rückgängig machen.
  - **Tipp:** Erst „Scan“, dann „Plan“ ausführen – so behältst du die Kontrolle.
- **datei_suche**: Dateien nach Text, Typ oder Datum suchen; optional organisieren.
  - **Tipp:** Nutze kleine Suchbegriffe, damit die Liste übersichtlich bleibt.
- **notiz_editor**: Notizen anlegen, bearbeiten, löschen und exportieren.
  - **Tipp:** Kurze Titel helfen beim Wiederfinden.
- **charakter_modul**: Charakterdaten pflegen (z. B. für Schreibprojekte).
  - **Tipp:** Nutze Vorlagen (Templates = Muster), um schneller zu starten.
- **todo_kalender**: Aufgaben als Kalenderansicht darstellen.
  - **Tipp:** Nutze klare Status-Wörter („geplant“, „erledigt“).
- **status**: Systemstatus prüfen (Status = Kurzmeldung).
  - **Tipp:** Gut für schnelle Tests, ob Module starten.

## 5) Einstellungen, Themes und Barrierefreiheit
1. **Theme wechseln** (Theme = Farbschema).
   - **Aktion:** In der GUI das Farbschema auswählen.
   - **Tipp:** „Kontrast“ hilft bei starker Sonneneinstrahlung.
2. **Kontrastmodus** (Kontrast = Helligkeitsunterschied).
   - **Aktion:** **Alt+K** drücken.
   - **Tipp:** Bei Leseschwierigkeiten zuerst Kontrastmodus aktivieren.
3. **Zoom** (Zoom = Vergrößerung).
   - **Aktion:** **Strg + Mausrad**.
   - **Tipp:** Für Präsentationen den Zoom auf 120–140 % setzen.

## 6) Debugging & Logging (Fehlersuche)
1. **Start mit Debug-Modus** (Debugging = detaillierte Fehlersuche).
   - **Befehl:** `./scripts/start.sh --debug`
   - **Tipp:** Debug-Ausgaben helfen, wenn Module nicht starten.
2. **Logdateien speichern** (Log = Protokoll).
   - **Befehl:** `./scripts/start.sh --log-file logs/start_run.log`
   - **Tipp:** Logdateien sind ideal, um Fehler später zu melden.
3. **Log-Export erstellen** (Export = Sammelpaket).
   - **Befehl:** `python system/log_exporter.py --root . --output logs/export.zip`
   - **Tipp:** Für Support immer den Export mitsenden.

## 7) Häufige Fragen & Lösungen (FAQ)
- **Problem:** „Module werden nicht angezeigt.“
  - **Lösung:** `config/modules.json` prüfen und `./scripts/system_scan.sh` ausführen.
  - **Tipp:** Achte darauf, dass `enabled` auf `true` steht.
- **Problem:** „GUI startet, zeigt aber Fehler.“
  - **Lösung:** `python system/json_validator.py --root .` ausführen.
  - **Tipp:** JSON-Dateien müssen gültig sein – fehlende Kommas sind häufige Fehler.
- **Problem:** „Tests schlagen fehl.“
  - **Lösung:** `./scripts/run_tests.sh` ausführen und `logs/test_run.log` lesen.
  - **Tipp:** Im Log steht meist der nächste sinnvolle Schritt.
- **Problem:** „Abhängigkeiten fehlen.“
  - **Lösung:** `python system/dependency_checker.py --requirements config/requirements.txt`
  - **Tipp:** Den Check nach einem Update immer einmal laufen lassen.
- **Problem:** „GUI reagiert träge.“
  - **Lösung:** Weniger Module anzeigen (Checkbox „Alle Module“ deaktivieren).
  - **Tipp:** Aktualisieren nur bei Bedarf auslösen.

## 8) Weiterführende Tipps (Laienfreundlich)
- **Klein starten:** Teste mit einem kleinen Ordner, bevor du große Daten verschiebst.
  - **Tipp:** Kleine Schritte sind sicherer und leichter rückgängig zu machen.
- **Fehler lesen:** Fehlermeldungen immer bis zum Ende lesen – dort steht der Lösungsschritt.
  - **Tipp:** Notiere dir die erste Fehlermeldung, sie ist meist die wichtigste.
- **Ordnung halten:** Logs und Daten in `logs/` und `data/` lassen.
  - **Tipp:** So bleiben Systemdateien sauber getrennt.
- **Struktur prüfen:** `STRUKTUR.md` lesen (Struktur = Verzeichnisbaum).
  - **Tipp:** Dort siehst du alle Pflichtdateien und Platzhalter (Dummy-Dateien).
