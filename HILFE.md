# Hilfe – 2026_GIT_TOOL

## 1. Tool starten

Empfohlener Start:

```bash
./scripts/start.sh
```

Die Startroutine prüft die benötigten Ordner, richtet bei Bedarf die lokale Python-Umgebung ein und öffnet anschließend die Benutzeroberfläche.

Nur prüfen, ohne regulär zu starten:

```bash
./scripts/start.sh --test-mode
```

Bei Startproblemen:

```bash
./scripts/start.sh --safe-mode
```

## 2. Bedienoberfläche

1. **Farbschema wählen** – passt Farben und Kontrast an.
2. **Übersicht aktualisieren** – lädt die Modulübersicht neu.
3. **Hauptfenster öffnen** – zeigt die verfügbaren Module.
4. **Diagnose starten** – führt den zentralen Privattool-Check aus und erstellt bei Erfolg das geprüfte Privat-ZIP. In einer grafischen Linux-Sitzung wird anschließend `dist/` geöffnet.
5. **Backup erstellen** – sichert die privaten Daten als ZIP.
6. **Abmelden** – speichert den aktuellen Zustand und beendet das Tool sauber.

Deaktivierte Module werden nur angezeigt, wenn **Alle Module anzeigen** aktiviert ist. **Debug-Details** sollten nur zur Fehlersuche eingeschaltet werden.

## 3. Protokolle

Alle Laufzeitprotokolle befinden sich im Ordner:

```text
logs/
```

Wichtige Datei:

```text
logs/tool.log
```

Die neuesten Meldungen stehen am Dateiende. Rotierte ältere Protokolle heißen beispielsweise `tool.log.1`.

Logdateien sind lokale Arbeitsdaten. Sie werden nicht im Hauptordner abgelegt, nicht versioniert und nicht in das private Release-ZIP aufgenommen.

## 4. Prüfung und schnelle Fehlerbehebung

### Einziger empfohlener Prüfweg in der Oberfläche

**Diagnose starten** oder `Alt+G` verwenden.

Die Oberfläche ruft intern denselben zentralen Prüfvertrag auf wie:

```bash
bash scripts/private_tool_check.sh
```

Bei Erfolg entsteht:

```text
dist/2026_GIT_TOOL_PRIVAT.zip
```

Geprüft werden ausschließlich:

- Ablagestruktur und Logtrennung
- JSON-Daten des Desktop-Tools
- Python- und Shell-Syntax
- Design-Tokens
- Modulverträge
- Desktop-Funktionstests
- kritische Ruff-Fehler
- Start-Smoke-Test
- ZIP-Inhalt und ZIP-Integrität

Der optionale MCP-Server, GitHub-Automation und öffentliche Release-Infrastruktur gehören nicht zum privaten Standardcheck und nicht zum Privat-ZIP.

### Oberfläche startet nicht

```bash
./scripts/start.sh --safe-mode
```

Danach `logs/tool.log` prüfen.

### Module fehlen

In der Startübersicht **Alle Module anzeigen** aktivieren und anschließend **Übersicht aktualisieren** wählen.

### Ordner oder Rechte fehlen

```bash
python system/health_check.py --root . --self-repair
```

## 5. Tastaturbedienung

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

Bei schmalen Fenstern zeigt die Fußzeile platzsparend nur die Kernkürzel `F1`, `Alt+R`, `Alt+M`, `Alt+G`, `Alt+Q` und `Strg+Z/Y`.

## 6. Private Datensicherung

Vor größeren Änderungen ein Backup erstellen. Backups werden unter `data/backups/` abgelegt. Persönliche Daten, lokale Logs, Caches und temporäre Prüfberichte gehören nicht in das Quellcode-ZIP.

## 7. Warum keine GitHub-Workflows mehr?

Für ein privates Einzelplatztool verursachen automatische Cloud-Workflows mehr Wartezeit und Fehlerquellen als Nutzen. Die lokale Prüfung verwendet exakt den Quellstand auf dem eigenen Rechner, benötigt keinen freien Runner und liefert das ZIP direkt im Projektordner.

Spezielle Gate-, Modernisierungs-, Export-, MCP- und Modul-Workflows sind daher entfernt. Die relevanten Desktop-Tests bleiben erhalten und werden durch `scripts/private_tool_check.sh` gemeinsam ausgeführt. `scripts/run_tests.sh` ist nur noch ein kompatibler Einstieg auf denselben Prüfvertrag und enthält keine zweite Testkette mehr.
