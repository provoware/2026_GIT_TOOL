# Provoware Memo: automatische Start- und Installationsroutine

## Produktidentität

Das Hauptprodukt heißt **Provoware Memo**. Archivverwaltung, GUI, CLI, Datei-Manager und alle weiteren Module bleiben Bestandteile dieses Haupttools. Es wird kein eigenständiges Archivprodukt, kein nachzuladendes Basisprojekt und kein Release-Overlay erzeugt.

## Autoritativer Start

```bash
./scripts/start.sh
```

Die Startroutine arbeitet in einer transparenten, fail-fast ausgeführten Kette:

1. Shell-Kontextprüfung der vollständigen Hauptprojektstruktur.
2. Python ab Version 3.10 ermitteln; bei sicher möglicher, nichtinteraktiver Systeminstallation automatisch nachinstallieren.
3. Standardbibliotheksbasierte Vorvalidierung von Produktidentität, Kerndateien, Verzeichnissen, JSON, Speicherplatz und Schreibrechten.
4. Systemkomponenten `venv`, `ensurepip`, SQLite, Tkinter und bei Headless-Betrieb Xvfb prüfen.
5. Fehlende Systemkomponenten über den vorhandenen Linux-Paketmanager ohne Passwortdialog reparieren und erneut prüfen.
6. Venv prüfen; einen beschädigten Stand datiert sichern und automatisch neu erstellen.
7. Pip über `ensurepip` reparieren.
8. Alle Einträge aus `config/requirements.txt` distributionsbasiert prüfen, installieren und importseitig nachvalidieren.
9. Den gesamten Paketgraphen mit `pip check` prüfen.
10. Bestehende Struktur-, Sicherheits-, JSON-, Modul- und Test-Gates ausführen.
11. Archivdatenbank initialisieren und alle `garch`-Aliase idempotent synchronisieren.
12. Abhängigkeiten abschließend erneut prüfen.
13. Lokalen Webserver und Google Chrome erst starten, wenn keine kritische Prüfung fehlgeschlagen ist.
14. Memo, Aufgaben, Kalender, Charaktere, Archive, Dateien, Medien, Profile und Systemwerkzeuge in einer gemeinsamen Browseroberfläche bereitstellen.

## Schutzregeln

- Ein unvollständiger Projektordner stoppt vor Venv, Pip, Datenbank und Aliasinstallation.
- Das System lädt kein Repository und sucht kein fremdes Basisprojekt.
- `Pillow` wird als Distribution geprüft und über `PIL` importseitig validiert.
- Beschädigte oder fehlende Python-Pakete werden automatisch erneut installiert.
- Fremde Aliasdateien werden nicht still überschrieben.
- Safe-Mode und `--preflight-only` führen keine schreibende Systemreparatur aus.
- Ein notwendiger Systemeingriff wird nur als Root oder über passwortfreies `sudo -n` ausgeführt; Sicherheitsmechanismen werden nicht umgangen.
- Berichte liegen unter `data/runtime/`, Startprotokolle unter `logs/`.
- Statische Browserdateien werden mit `Cache-Control: no-store` ausgeliefert, damit keine veraltete, funktionslose JavaScript-Version weiterverwendet wird.
- Der Browsercode besitzt eine sichtbare Fehlergrenze; ein Initialisierungsfehler kann nicht mehr unbemerkt alle Klicks deaktivieren.
- Der integrierte Datei-Manager stellt Ordnernavigation, sortierbare Listen, Metadaten und große Bildvorschau bereit.

## Prüfmodi

```bash
./scripts/start.sh --preflight-only
./scripts/start.sh --no-start
./scripts/start.sh --safe-mode
./scripts/start.sh --sandbox
```

## Test- und Qualitätsstrategie

Der automatische Start verwendet:

```bash
./scripts/run_tests.sh --startup-gate
```

Dabei werden die vollständige Pytest-Suite und die branchbezogenen kritischen Qualitätsprüfungen ausgeführt. Auf einem Headless-System wird automatisch Xvfb eingesetzt.

Der explizite Entwicklerlauf bleibt unverändert streng und prüft weiterhin das gesamte Repository mit Ruff und Black:

```bash
./scripts/run_tests.sh
```

Damit werden bestehende projektweite Lint-Altlasten transparent erhalten, aber nicht fälschlich als neue Startregression bewertet.

## Vollständiger Export

Das Workflow-Gate `Provoware Memo Startup and Full Export` erzeugt erst nach bestandener Vorvalidierung, vollständiger Funktionsprüfung und isolierter Startkette das Artefakt:

```text
Provoware_Memo_FULL.zip
```

Das ZIP enthält den gesamten Hauptprojektstand unter dem Projektordner `Provoware_Memo/`, nicht nur geänderte Dateien oder ein Overlay. Ausgeschlossen werden ausschließlich Git-Metadaten, Venv, Python-Caches, Laufzeitprotokolle und lokale SQLite-Laufzeitdaten.
