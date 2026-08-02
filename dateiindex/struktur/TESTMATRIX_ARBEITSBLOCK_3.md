# Testmatrix vor Arbeitsblock 3

Stand: 2026-08-03
Status: verbindliche Vorbedingung für die Modularisierung

## Zweck

Diese Matrix ordnet vorhandene Tests den sieben geplanten Refaktorierungsschritten zu und definiert fehlende Sicherungstests. Eine Auslagerung darf erst beginnen, wenn die für den jeweiligen Schritt als **Gate** markierten Tests vorhanden und erfolgreich sind.

## Bestand

| Testdatei | Aktuelle Abdeckung | Aussagekraft | Grenze |
| --- | --- | --- | --- |
| `tests/test_launcher_gui.py` | Konfigurationsladen, ungültige Farbe, Modulzeilen mit Debug-Pfad | niedrig bis mittel | keine echte GUI, keine Controller-Abläufe, keine Threads |
| `tests/test_module_manager.py` | Registry laden, Modul aktivieren/deaktivieren | mittel | kein Widgetabgleich, kein Shutdown, kein Fehlerpfad |
| `tests/test_drag_drop.py` | Parsing von Drop-Daten mit Leerzeichen/Klammern | niedrig | keine GUI-Integration, keine Pfadvalidierung |
| `tests/test_undo_redo.py` | Undo-/Redo-Grundablauf | mittel | keine Launcher-Zustände, keine Theme-/Filterintegration |
| `tests/test_diagnostics_runner.py` | Diagnose-Runner separat | mittel | keine GUI-Thread- oder Callback-Kette |
| `tests/test_autosave_manager.py` | Autosave separat, soweit vorhanden | mittel | keine Logout-/Shutdown-Orchestrierung |
| `tests/test_backup_center.py` | Backup separat, soweit vorhanden | mittel | keine kombinierte Logout-Kette |

## Gate 1: Berichtformatierer auslagern

### Vorhandene indirekte Abdeckung

- `tests/test_launcher_gui.py`
- Tests der Fachmodule `qa_checks`, `end_audit`, `module_selftests`, `error_simulation`

### Fehlende Pflichtprüfungen

Neue Datei: `tests/test_launcher_reports.py`

Pflichtfälle:

1. Diagnosebericht enthält Status, Dauer, Exit-Code, Kommando und Ausgabe.
2. Wartungsbericht behandelt erfolgreichen und fehlerhaften Exit-Code deterministisch.
3. Modulprüfung ohne Fehler erzeugt Erfolgstext.
4. Modulprüfung mit Fehlern enthält Klassifizierung und Lösungshinweis.
5. Datei-Status, End-Audit, Selbsttests und Fehlersimulation behalten Reihenfolge und Überschriften.
6. Leere oder typfalsche Eingaben werden kontrolliert abgewiesen.
7. Formatierer verändern keine GUI-Zustände.

**Gate:** vollständig grün, bevor Formatierer aus `launcher_gui.py` entfernt werden.

## Gate 2: Geometrie und Kollisionslogik auslagern

### Vorhandene Abdeckung

Keine direkte Abdeckung.

### Fehlende Pflichtprüfungen

Neue Datei: `tests/test_workspace_geometry.py`

Pflichtfälle:

1. Rechtecküberschneidung: vollständig getrennt.
2. Rechtecküberschneidung: Kantenkontakt gilt nicht als Überschneidung.
3. Rechtecküberschneidung: teilweise und vollständig enthalten.
4. Begrenzung negativer X-/Y-Werte.
5. Begrenzung an rechter und unterer Workspace-Kante.
6. Mindestbreite und Mindesthöhe.
7. Resize darf keine negative Restgröße erzeugen.
8. Kollisionsprüfung ignoriert das aktuell bewegte Element.
9. Initiales 3x3-Raster erzeugt höchstens neun gültige Positionen.
10. Reflow bei kleinerem und größerem Workspace bleibt innerhalb der Grenzen.

**Gate:** vollständig grün, bevor `_rect_overlap`, Bounds-, Raster-, Drag- oder Resize-Berechnung ausgelagert werden.

## Gate 3: Themeadapter vereinheitlichen

### Vorhandene indirekte Abdeckung

- `tests/test_launcher_gui.py`: Konfigurationsvalidierung
- vorhandene Kontrasttests

### Fehlende Pflichtprüfungen

Neue Datei: `tests/test_ui_theme_adapter.py`

Pflichtfälle:

1. gültiges Theme wird in ein einheitliches UI-Farbmodell übersetzt.
2. unbekanntes Theme fällt kontrolliert auf das Standard-Theme zurück oder erzeugt den definierten Fehler.
3. alle Statusfarben sind vorhanden.
4. Launcher und Hauptfenster erhalten dieselben semantischen Farben.
5. Themewechsel verändert keine Modulzustände.
6. Kontrast-Theme lässt sich aktivieren und zum vorherigen Theme zurückschalten.
7. Design-Token-Quelle und GUI-Konfiguration werden auf Drift geprüft.

**Gate:** vollständig grün, bevor Themecode aus einer der beiden UI-Dateien entfernt wird.

## Gate 4: Task-Runner für Threads und Prozesse

### Vorhandene indirekte Abdeckung

- `tests/test_diagnostics_runner.py`
- separate Tests einzelner Wartungsdienste

### Fehlende Pflichtprüfungen

Neue Datei: `tests/test_ui_task_runner.py`

Pflichtfälle:

1. paralleler Start derselben Task-Kategorie wird blockiert.
2. Buttons werden beim Start deaktiviert und beim Abschluss reaktiviert.
3. Erfolg, Fehler, Exception und leerer Prozess-Output werden unterschieden.
4. Callback wird über den UI-Scheduler aufgerufen.
5. Prozesskommando wird nicht per Shell-String ausgeführt.
6. fehlende Skripte und Zielpfade werden vor Threadstart erkannt.
7. ein fehlgeschlagener Task lässt den Busy-Zustand nicht hängen.
8. Diagnose- und Wartungstasks beeinflussen ihre Statusflags nicht gegenseitig.

**Gate:** vollständig grün, bevor Thread-/Subprocess-Steuerung ausgelagert wird.

## Gate 5: Autosave und Shutdown trennen

### Vorhandene indirekte Abdeckung

- Autosave- und Backup-Einzeltests

### Fehlende Pflichtprüfungen

Neue Datei: `tests/test_shutdown_coordinator.py`

Pflichtfälle:

1. doppelter Logout wird blockiert.
2. Autosave aktiviert: Autosave läuft vor Backup.
3. Autosave deaktiviert: verständlicher Hinweis, Backup läuft dennoch.
4. Autosavefehler verhindert Backup nicht.
5. Backupfehler wird dokumentiert.
6. geplanter Autosave-Job wird beim Schließen abgebrochen.
7. Fenster wird erst nach Abschlussbericht und Statusaktualisierung geschlossen.
8. Hauptfenster deaktiviert nicht pauschal fremde Module ohne explizite Policy.
9. Shutdown ist idempotent.

**Gate:** vollständig grün, bevor Logout-/Shutdown-Logik ausgelagert oder verändert wird.

## Gate 6: Modulkarten und Modul-Lebenszyklus trennen

### Vorhandene indirekte Abdeckung

- `tests/test_module_manager.py`

### Fehlende Pflichtprüfungen

Neue Dateien:

- `tests/test_module_card_presenter.py`
- `tests/test_module_lifecycle_controller.py`

Pflichtfälle:

1. Karte zeigt Namen, Beschreibung und tatsächlichen Aktivstatus.
2. Aktivierungserfolg aktualisiert Manager und Präsentationsmodell.
3. Aktivierungsfehler zeigt keinen falschen Aktivstatus.
4. Deaktivierung liest den tatsächlichen Managerzustand zurück.
5. Statusfarben werden semantisch, nicht als feste Hexwerte übergeben.
6. maximal neun Karten sind eine View-Policy und keine Managerbegrenzung.
7. Schließen des Fensters folgt einer expliziten Lebenszyklus-Policy.
8. Managerfehler werden in kontrollierte UI-Ergebnisse übersetzt.

**Gate:** vollständig grün, bevor `ModuleWidget` oder Modulaktivierungslogik ausgelagert wird.

## Gate 7: Launcher-View zerlegen

### Vorhandene indirekte Abdeckung

- einzelne Hilfsfunktions- und Komponentenprüfungen

### Fehlende Pflichtprüfungen

Neue Datei: `tests/test_launcher_controller.py`

Pflichtfälle:

1. Initialisierung setzt Standard-Theme, Filter, Debugstatus und Bereitschaft.
2. Refresh-Debounce führt mehrere schnelle Anforderungen nur einmal aus.
3. Theme-, Filter- und Debugänderungen werden korrekt in Undo/Redo aufgenommen.
4. Kontext-Hilfe und Tooltips verändern keine Fachzustände.
5. Zoom bleibt innerhalb 80–160 Prozent.
6. responsive Umschaltung verändert nur Layout, nicht Daten.
7. Refreshfehler setzt Fehlerstatus und lässt die GUI weiter bedienbar.
8. Diagnose-, Wartungs-, Export- und Backupaktionen delegieren ausschließlich an Controller/Dienste.
9. View-Erstellung startet keine unkontrollierten externen Prozesse.

**Gate:** vollständig grün, bevor `_build_ui` in Teilviews zerlegt wird.

## Empfohlene Teststruktur

```text
tests/
├── test_launcher_reports.py
├── test_workspace_geometry.py
├── test_ui_theme_adapter.py
├── test_ui_task_runner.py
├── test_shutdown_coordinator.py
├── test_module_card_presenter.py
├── test_module_lifecycle_controller.py
└── test_launcher_controller.py
```

## Ausführungsreihenfolge

1. zuerst reine Logiktests ohne Tkinter-Display
2. danach Controller-Tests mit Fakes für Root, Scheduler und Widgets
3. zuletzt wenige GUI-Smoke-Tests unter Xvfb oder realem Linux-Display
4. nach jedem Refaktorierungsschritt nur das zugehörige Gate plus bestehende Regressionstests
5. kompletter Testlauf erst nach Abschluss einer stabilen Teilstufe

## Stopregeln

- Kein Produktionscode wird verschoben, solange das zugehörige Gate fehlt.
- Bei rotem Gate maximal ein gezielter Korrekturdurchlauf.
- Keine gleichzeitige Auslagerung aus `launcher_gui.py` und `main_window.py`.
- Keine visuellen Änderungen im selben Commit wie eine reine Strukturauslagerung.
- Eine Datei wird erst in `dateiindex/gehaertet/` aufgenommen, wenn ihr Gate grün und ihre Restgrenzen dokumentiert sind.

## Nächste freigegebene Arbeit

Zuerst Gate 1 implementieren: reine Berichtformatierer absichern. Danach dürfen ausschließlich die Berichtformatierer in ein separates Modul ausgelagert werden.
