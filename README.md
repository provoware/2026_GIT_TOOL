# 2026_GIT_TOOL

Privates Linux-Desktoptool für eine übersichtliche Modulverwaltung, lokale Datenpflege, Diagnose, Backups und Exporte. Der Schwerpunkt liegt auf verständlicher Bedienung, robuster lokaler Ausführung und einer kleinen, nachvollziehbaren Prüfstrecke.

## Schnellstart

```bash
./scripts/start.sh
```

Die Startroutine prüft die Projektstruktur, richtet bei Bedarf eine lokale Python-Umgebung ein und öffnet anschließend die Benutzeroberfläche.

Weitere Startarten:

```bash
./scripts/start.sh --safe-mode   # sichere Prüfung und eingeschränkter Start
./scripts/start.sh --test-mode   # nur Vorprüfung
./scripts/start.sh --sandbox     # isolierte Testkopie
```

Die vollständige Bedienhilfe steht in **[HILFE.md](HILFE.md)**.

## Bedienung

1. Farbschema und gewünschte Filter wählen.
2. **Übersicht aktualisieren** ausführen.
3. **Hauptfenster öffnen** und das gewünschte Modul starten.
4. Bei Problemen zuerst **Diagnose starten** verwenden.
5. Vor größeren Änderungen ein **Backup** erstellen.
6. Mit **Abmelden** speichern und sauber beenden.

Alle wichtigen Funktionen sind per Tastatur erreichbar. `F1` zeigt die Hilfe zum fokussierten Bedienelement.

## Protokolle

Laufzeit- und Diagnoseprotokolle liegen ausschließlich unter:

```text
logs/
```

Die zentrale Datei ist `logs/tool.log`. Im Projekt-Hauptordner werden keine Logdateien erzeugt. Logs werden weder versioniert noch in das private Release-ZIP übernommen.

## Lokale Prüfung und Privat-ZIP

Ein vollständiger privater Kerncheck:

```bash
./scripts/private_tool_check.sh
```

Direkt ein geprüftes ZIP erstellen:

```bash
./scripts/build_private_release.sh
```

Ausgabe:

```text
dist/2026_GIT_TOOL_PRIVAT.zip
```

Der Kerncheck umfasst nur Punkte, die für ein privates Einzelplatztool unmittelbar relevant sind:

- Projekt- und Logablagestruktur
- JSON-Validierung
- Python- und Shell-Syntax
- Design-Token-Konsistenz
- Modulverträge
- vollständige Funktionstests
- kritische Ruff-Fehlerklassen
- Start-Smoke-Test
- ZIP-Struktur- und Laufprüfung

## GitHub-Prüfung

Es gibt nur noch einen gemeinsamen Workflow:

```text
Private Tool Check
```

Er führt dieselbe Kernprüfung aus und veröffentlicht das geprüfte Privat-ZIP. Frühere Einzel-Gates, Codemod-, Modernisierungs-, Export- und Modulworkflows wurden entfernt. Ihre fachlichen Tests bleiben Bestandteil der gemeinsamen Pytest-Suite.

## Ordnerübersicht

| Pfad | Zweck |
|---|---|
| `system/` | Kernlogik und Benutzeroberfläche |
| `modules/` | Toolmodule |
| `config/` | Einstellungen und Prüfkonfiguration |
| `data/` | lokale Nutzdaten und Backups |
| `logs/` | ausschließlich lokale Laufzeitprotokolle |
| `scripts/` | Start, Prüfung, Reparatur und Paketbau |
| `mcp_dispatch/` | optionale, eng begrenzte GitHub-Workflow-Anbindung |
| `tests/` | gemeinsame Funktionstests für die Entwicklung |

## Diagnose und Reparatur

```bash
python system/diagnostics_runner.py
python system/health_check.py --root . --self-repair
```

Die Diagnose zeigt verständliche Ergebnisse. Technische Einzelheiten werden unter `logs/` oder in temporären Prüfberichten unter `build/` abgelegt.

## Datenschutz und privater Betrieb

- Nutzdaten bleiben standardmäßig lokal.
- Laufzeitlogs bleiben lokal und werden nicht paketiert.
- Der Start benötigt keine Administratorrechte.
- Netzwerkfunktionen sind optional. Die MCP-Anbindung wird nur verwendet, wenn sie ausdrücklich eingerichtet und gestartet wurde.
- Backups liegen unter `data/backups/`.

<!-- AUTO-STATUS:START -->
**Auto-Status (aktualisiert: 2026-08-04)**

- Gesamt: 260 Tasks
- Erledigt: 247 Tasks
- Offen: 13 Tasks
- Fortschritt: 95 %
<!-- AUTO-STATUS:END -->

## Weiterführende Dokumentation

- `HILFE.md` – Bedienung und Fehlerbehebung
- `DEV_DOKU.md` – technische Entwicklungshinweise
- `STYLEGUIDE.md` – Projekt- und Codestandards
- `STRUKTUR.md` – Projektstruktur
- `CHANGELOG.md` – Änderungshistorie
- `todo.txt` – offene Aufgaben

## Lizenz

Noch nicht festgelegt.
