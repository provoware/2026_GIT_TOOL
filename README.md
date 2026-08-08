# 2026_GIT_TOOL

Privates Linux-Desktoptool für Modulverwaltung, lokale Datenpflege, Diagnose, Backups und Exporte. Der aktuelle Zielzustand ist bewusst klein: schneller lokaler Start, verständliche Privat-GUI und genau ein vollständiger Prüf- und Paketweg.

## Schnellstart

```bash
./scripts/start.sh
```

Der normale Start führt nur einen Minimal-Preflight aus:

```text
Kerndateien
→ Python >= 3.10
→ lokale Venv
→ Tkinter + SQLite
→ Privat-GUI
```

Nur prüfen, ohne die GUI zu öffnen:

```bash
./scripts/start.sh --preflight-only
```

`--test-mode`, `--safe-mode` und `--no-start` bleiben kompatible Aliase für denselben Minimal-Preflight.

Die vollständige Bedienhilfe steht in **[HILFE.md](HILFE.md)**.

## Privat-GUI

Die Standardansicht zeigt nur die regelmäßig benötigten Wartungsfunktionen:

- **Diagnose + Privat-ZIP** (`Alt+G`)
- **Log-Ordner öffnen**
- **Backup erstellen**
- **Erweitert anzeigen**

Unter **Erweitert** bleiben System-Scan, Standards-Liste, selektiver Export und Export-Center verfügbar. Sie werden nicht entfernt, sondern nur aus der täglichen Standardansicht herausgehalten.

Statusanzeige:

```text
Bereit
→ Diagnose läuft …
→ Geprüft – ZIP erstellt
```

## Protokolle

Laufzeit- und Diagnoseprotokolle liegen ausschließlich unter:

```text
logs/
```

Wichtige Dateien sind `logs/tool.log` und `logs/start_run.log`. Im Projekt-Hauptordner werden keine Laufzeitlogs abgelegt. Logs werden nicht in das private Release-ZIP übernommen.

## Einziger vollständiger Prüfweg

In der GUI:

```text
Alt+G
```

oder im Terminal:

```bash
bash scripts/private_tool_check.sh
```

Der Privattool-Check umfasst:

- Ablagestruktur und Logtrennung
- JSON-Validierung
- produktive Python-Kompilierung
- Shell-Syntax
- Design-Tokens
- Modulverträge
- Funktionstests
- kritische Ruff-Fehlerklassen
- Basis- und Privat-Launcher-Smoke-Test
- ZIP-Bau und ZIP-Integrität

Bei Erfolg entsteht:

```text
dist/2026_GIT_TOOL_PRIVAT.zip
```

## Keine GitHub-Workflow-Abhängigkeit

Für den privaten Einzelplatzbetrieb gibt es keinen verpflichtenden GitHub-Actions-Prüfpfad. Prüfung und Paketbau laufen lokal auf dem Rechner, auf dem das Tool tatsächlich verwendet wird. Dadurch entstehen keine Runner-Wartezeiten und keine doppelte Cloud-/Lokalprüfung.

## Ordnerübersicht

| Pfad | Zweck |
|---|---|
| `system/` | Kernlogik und Benutzeroberfläche |
| `modules/` | Toolmodule |
| `config/` | Laufzeit- und Toolkonfiguration |
| `data/` | lokale Nutzdaten und Backups |
| `logs/` | lokale Laufzeitprotokolle |
| `scripts/` | Schnellstart, lokaler Check, Reparaturhilfen und Paketbau |
| `tests/` | funktionale Entwicklungs- und Regressionstests |

## Diagnose und bewusste Reparatur

Normale Probleme zuerst über **Diagnose + Privat-ZIP** prüfen. Reparaturskripte werden nicht automatisch beim Start ausgeführt.

Nur bei einem tatsächlich festgestellten Struktur-/Ordnerproblem:

```bash
python system/health_check.py --root . --self-repair
```

## Datenschutz und privater Betrieb

- Nutzdaten bleiben lokal.
- Laufzeitlogs bleiben lokal.
- Der normale Start installiert keine Systempakete automatisch.
- Vollprüfungen laufen nur bewusst über `Alt+G` beziehungsweise `private_tool_check.sh`.
- Backups liegen unter `data/backups/`.

## Weiterführende Dokumentation

- `HILFE.md` – Bedienung und Fehlerbehebung
- `DEV_DOKU.md` – technische Entwicklungshinweise
- `STYLEGUIDE.md` – Projekt- und Codestandards
- `STRUKTUR.md` – Projektstruktur
- `CHANGELOG.md` – Änderungshistorie
- `todo.txt` – offene Aufgaben

## Lizenz

Noch nicht festgelegt.
