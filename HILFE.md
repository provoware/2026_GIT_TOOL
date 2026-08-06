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
4. **Diagnose starten** – prüft die wichtigsten Funktionen und zeigt verständliche Ergebnisse.
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

## 4. Schnelle Fehlerbehebung

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

### Vollständige lokale Prüfung

```bash
./scripts/private_tool_check.sh
```

Die Prüfung kontrolliert ausschließlich die für das private Tool erforderlichen Punkte: Datenformate, Python- und Shell-Syntax, Design-Tokens, Modulverträge, Funktionstests und einen Start-Smoke-Test.

## 5. Tastaturbedienung

| Taste | Funktion |
|---|---|
| `Tab` | Zum nächsten Bedienelement wechseln |
| `Umschalt+Tab` | Zum vorherigen Bedienelement wechseln |
| `Enter` / `Leertaste` | Ausgewählte Funktion ausführen |
| `F1` | Hilfe zum aktuellen Bedienelement anzeigen |
| `Alt+R` | Übersicht aktualisieren |
| `Alt+M` | Hauptfenster öffnen |
| `Alt+G` | Diagnose starten |
| `Alt+L` | Logordner öffnen |
| `Alt+B` | Backup erstellen |
| `Alt+K` | Kontrastmodus umschalten |
| `Alt+Q` | Speichern und beenden |
| `Strg+Z` / `Strg+Y` | Rückgängig / Wiederholen |
| `Strg+Mausrad` | Ansicht vergrößern oder verkleinern |

## 6. Private Datensicherung

Vor größeren Änderungen ein Backup erstellen. Backups werden unter `data/backups/` abgelegt. Persönliche Daten, lokale Logs, Caches und temporäre Prüfberichte gehören nicht in das Quellcode-ZIP.

## 7. Welche Prüfungen sind nötig?

Für den privaten Einzelplatzbetrieb genügt ein gemeinsamer Prüfjob mit:

- Struktur- und Datenprüfung
- Python- und Shell-Syntax
- Design-Token-Konsistenz
- vollständiger Pytest-Suite
- Start-Smoke-Test
- ZIP-Strukturprüfung

Separate Gate-, Modernisierungs-, Export-, MCP- und Modul-Workflows sind für die tägliche private Entwicklung nicht erforderlich. Die zugehörigen Tests bleiben erhalten und werden vom gemeinsamen Prüfjob ausgeführt.
