# Provoware Memo: automatische Start- und Installationsroutine

## Produktidentität

Das Hauptprodukt heißt **Provoware Memo**. Archivverwaltung, GUI, CLI, Datei-Manager und alle weiteren Module bleiben Bestandteile dieses Haupttools. Es wird kein eigenständiges Archivprodukt und kein Release-Overlay erzeugt.

## Autoritativer Start

```bash
./scripts/start.sh
```

Die Startroutine arbeitet in einer transparenten, fail-fast ausgeführten Kette:

1. Shell-Kontextprüfung der vollständigen Hauptprojektstruktur.
2. Python ab Version 3.10 ermitteln; bei sicher möglicher, nichtinteraktiver Systeminstallation automatisch nachinstallieren.
3. Standardbibliotheksbasierte Vorvalidierung von Produktidentität, Kerndateien, Verzeichnissen, JSON, Speicherplatz und Schreibrechten.
4. Venv prüfen; einen beschädigten Stand datiert sichern und automatisch neu erstellen.
5. Pip über `ensurepip` reparieren.
6. Alle Einträge aus `config/requirements.txt` distributionsbasiert prüfen, installieren und importseitig nachvalidieren.
7. Den gesamten Paketgraphen mit `pip check` prüfen.
8. Bestehende Struktur-, Sicherheits-, JSON-, Modul- und Test-Gates ausführen.
9. Archivdatenbank initialisieren und alle `garch`-Aliase idempotent synchronisieren.
10. Abhängigkeiten abschließend erneut prüfen.
11. GUI erst starten, wenn keine kritische Prüfung fehlgeschlagen ist.

## Schutzregeln

- Ein unvollständiger Projektordner stoppt vor Venv, Pip, Datenbank und Aliasinstallation.
- Das System lädt kein Repository und sucht kein fremdes Basisprojekt.
- `Pillow` wird als Distribution geprüft und über `PIL` importseitig validiert.
- Fremde Aliasdateien werden nicht still überschrieben.
- Safe-Mode führt keine schreibenden Reparaturen aus.
- Berichte liegen unter `data/runtime/`, Startprotokolle unter `logs/`.

## Prüfmodi

```bash
./scripts/start.sh --preflight-only
./scripts/start.sh --no-start
./scripts/start.sh --safe-mode
./scripts/start.sh --sandbox
```

## Vollständiger Export

Das Workflow-Gate `Provoware Memo Startup and Full Export` erzeugt nach bestandener Vorvalidierung und Regression ein vollständiges Artefakt:

```text
Provoware_Memo_FULL.zip
```

Das ZIP enthält den gesamten Hauptprojektstand unter dem Projektordner `Provoware_Memo/`, nicht nur geänderte Dateien oder ein Overlay.
