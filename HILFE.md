# Hilfe – 2026_GIT_TOOL

## 1. Tool starten

Empfohlener Start:

```bash
./scripts/start.sh
```

Der normale Start ist bewusst kurz. Er prüft nur Kerndateien, Python ab Version 3.10, die lokale Python-Umgebung sowie Tkinter und SQLite. Danach wird direkt die Privattool-Oberfläche geöffnet.

Nur den Minimal-Preflight prüfen, ohne die Oberfläche zu starten:

```bash
./scripts/start.sh --preflight-only
```

`--test-mode`, `--safe-mode` und `--no-start` bleiben kompatible Aliase für denselben Minimal-Preflight.

## 2. Bedienoberfläche

Die Standardansicht ist für den privaten Alltag reduziert:

1. **Farbschema wählen** – Farben und Kontrast anpassen.
2. **Übersicht aktualisieren** – Modulübersicht neu laden.
3. **Hauptfenster öffnen** – verfügbare Module anzeigen.
4. **Diagnose + Privat-ZIP** – vollständigen lokalen Privattool-Check starten.
5. **Log-Ordner öffnen** – lokale Protokolle anzeigen.
6. **Backup erstellen** – private Daten sichern.
7. **Abmelden** – speichern und sauber beenden.

### Erweitert

Über **Erweitert anzeigen** bleiben selten benötigte Werkzeuge verfügbar:

- System-Scan
- Standards-Liste
- selektiver Export
- Export-Center

Für den normalen Privatbetrieb werden diese Funktionen nicht benötigt.

## 3. Statusanzeige

Der Prüfablauf soll ohne technische Interpretation verständlich sein:

```text
Bereit
→ Diagnose läuft …
→ Geprüft – ZIP erstellt
```

Falls der Check zwar beendet wird, aber das erwartete ZIP fehlt, wird ausdrücklich **„Prüfung abgeschlossen – ZIP fehlt“** als Fehlerzustand angezeigt.

## 4. Protokolle

Alle Laufzeitprotokolle befinden sich unter:

```text
logs/
```

Wichtige Dateien:

```text
logs/tool.log
logs/start_run.log
```

Die neuesten Meldungen stehen am Dateiende. Laufzeitlogs liegen nicht im Hauptordner, werden nicht versioniert und nicht in das private Release-ZIP aufgenommen.

## 5. Einziger vollständiger Prüfweg

In der GUI:

```text
Alt+G
```

oder im Terminal:

```bash
bash scripts/private_tool_check.sh
```

Bei Erfolg entsteht:

```text
dist/2026_GIT_TOOL_PRIVAT.zip
```

Geprüft werden:

- Ablagestruktur und Logtrennung
- JSON-Daten des Desktop-Tools
- produktive Python-Kompilierung
- Shell-Syntax
- Design-Tokens
- Modulverträge
- Funktionstests
- kritische Ruff-Fehler
- Start-Smoke-Test des Basis- und Privat-Launchers
- ZIP-Inhalt und ZIP-Integrität

## 6. Schnelle Fehlerbehebung

### Oberfläche startet nicht

```bash
./scripts/start.sh --preflight-only
```

Der Minimal-Preflight meldet fehlende Kerndateien, eine ungeeignete Python-Version oder fehlendes Tkinter/SQLite direkt. Danach `logs/start_run.log` prüfen.

Der normale Start installiert keine Systempakete und führt keine automatische Systemreparatur aus.

### Module fehlen

**Alle Module anzeigen** aktivieren und anschließend **Übersicht aktualisieren** wählen.

### Bewusste Reparatur bei einem bestätigten Strukturproblem

```bash
python system/health_check.py --root . --self-repair
```

Diese Reparatur gehört nicht zum normalen Start.

## 7. Tastaturbedienung

| Taste | Funktion |
|---|---|
| `Tab` | Zum nächsten Bedienelement wechseln |
| `Umschalt+Tab` | Zum vorherigen Bedienelement wechseln |
| `Enter` / `Leertaste` | Ausgewählte Funktion ausführen |
| `F1` | Hilfe zum aktuellen Bedienelement anzeigen |
| `Alt+R` | Übersicht aktualisieren |
| `Alt+M` | Hauptfenster öffnen |
| `Alt+G` | Privattool prüfen und ZIP erstellen |
| `Alt+L` | Logordner öffnen |
| `Alt+B` | Backup erstellen |
| `Alt+K` | Kontrastmodus umschalten |
| `Alt+Q` | Speichern und beenden |
| `Strg+Z` / `Strg+Y` | Rückgängig / Wiederholen |
| `Strg+Mausrad` | Ansicht vergrößern oder verkleinern |

Die Profi-Kurzbefehle für System-Scan, Standards und Export bleiben erhalten, auch wenn die Schaltflächen unter **Erweitert** liegen.

## 8. Private Datensicherung

Vor größeren Änderungen ein Backup erstellen. Backups werden unter `data/backups/` abgelegt. Persönliche Daten, lokale Logs, Caches und temporäre Prüfberichte gehören nicht in das Quellcode-ZIP.

## 9. Warum keine GitHub-Workflows oder Start-Gates mehr?

Für ein privates Einzelplatztool verursachen Cloud-Workflows und umfangreiche Prüfketten bei jedem Start mehr Wartezeit und Fehlerquellen als Nutzen.

Die Aufgaben sind deshalb getrennt:

```text
Normaler Start
→ Minimal-Preflight
→ Python/Venv
→ Tkinter/SQLite
→ Privat-GUI

Vollständige Prüfung
→ Diagnose + Privat-ZIP / Alt+G
→ private_tool_check.sh
→ Privat-ZIP
```

`scripts/run_tests.sh` bleibt nur als kompatibler Einstieg auf denselben zentralen Privattool-Check erhalten und enthält keine zweite Testkette.
