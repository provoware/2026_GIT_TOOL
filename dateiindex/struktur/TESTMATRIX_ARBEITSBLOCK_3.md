# Testmatrix Arbeitsblock 3

Stand: 2026-08-03
Status: Gates 1 bis 7 abgeschlossen; Arbeitsblock 3 ist testseitig abgeschlossen

## Zweck

Vor jeder Auslagerung aus `system/launcher_gui.py` oder `system/main_window.py` musste ein passendes Sicherungstest-Gate bestehen. Strukturänderungen, visuelle Änderungen und Verhaltensänderungen wurden getrennt.

## Abgeschlossene Reihenfolge

1. Berichtformatierer – abgeschlossen
2. Workspace-Geometrie und Kollision – abgeschlossen
3. Einheitlicher Themeadapter – abgeschlossen
4. Task-Runner für Threads und Prozesse – abgeschlossen
5. Autosave, Shutdown und Autostart – abgeschlossen
6. Modulkarten und Modul-Lebenszyklus – abgeschlossen
7. Launcher-Controller und Teilviews – abgeschlossen

## Gate 1 – Berichtformatierer

### Abgeschlossen

- Wartungsbericht
- Diagnosebericht
- Datei-Ampelstatus
- End-Audit
- Modul-Selbsttests
- Fehlersimulation
- UI-, Thread- und Dialogseiteneffekte bleiben außerhalb der reinen Formatierer

### Sicherung

- `system/launcher_reports.py`
- `tests/test_launcher_reports.py`
- `scripts/apply_gate1_launcher_reports.py`
- `tests/test_gate1_launcher_codemod.py`
- `.github/workflows/gate-1-launcher-reports.yml`

## Gate 2 – Geometrie und Kollision

### Abgeschlossen

- Rechtecküberschneidung an allen Kanten
- Berührung ohne Überschneidung
- Bounds-Clamping
- Mindestgrößen
- 3×3-Initiallayout
- Verhalten bei kleinen Workspaces
- Drag-, Resize- und Kollisionsdelegation

### Sicherung

- `system/workspace_geometry.py`
- `tests/test_workspace_geometry.py`
- `tests/test_gate2_workspace_codemod.py`
- `scripts/apply_gate2_workspace_geometry_v2.py`
- `.github/workflows/gate-2-workspace-geometry.yml`

## Gate 3 – Themeadapter

### Abgeschlossen

- identische Tokenauflösung in beiden Fenstern
- strikte Launcher-Auflösung und Standard-Fallback im Hauptfenster
- vollständige Status- und Tooltipfarben
- Kontrast-Theme-Auflösung
- rekursive Widgetanwendung
- OptionMenu-/Menügestaltung
- modulkartenspezifische Akzente
- Fehler bei fehlenden Farbschlüsseln vor Widgetmutation

### Sicherung

- `system/ui_theme_adapter.py`
- `tests/test_ui_theme_adapter.py`
- `tests/test_gate3_ui_theme_codemod.py`
- `scripts/apply_gate3_ui_theme_adapter.py`
- `.github/workflows/gate-3-ui-theme-adapter.yml`
- `dateiindex/gehaertet/GATE_3_UI_THEME_ADAPTER.md`

## Gate 4 – Task-Runner

### Abgeschlossen

- höchstens ein paralleler Task pro Kategorie
- unterschiedliche Kategorien dürfen parallel laufen
- UI-Callback ausschließlich über den injizierten Scheduler
- Erfolgs-, Fehler- und Ausnahmezustand über `TaskOutcome`
- Freigabe der Kategorie vor dem Abschluss-Callback
- Wiederherstellung deaktivierter Schaltflächen
- kontrollierte Thread-Start- und Schedulerfehler
- zentrale Kommando- und Pfadvalidierung
- kein Tkinter-Zugriff aus Worker-Threads

### Sicherung

- `system/task_runner.py`
- `tests/test_task_runner.py`
- `tests/test_gate4_task_runner_codemod.py`
- `scripts/apply_gate4_task_runner.py`
- `.github/workflows/gate-4-task-runner.yml`
- `dateiindex/gehaertet/GATE_4_TASK_RUNNER.md`

## Gate 5 – Autosave, Shutdown und Autostart

### Abgeschlossen

- Autosave aktiviert und deaktiviert
- Autosave-Fehler mit fortgesetztem Backup-Versuch
- Backup-Erfolg und Backup-Fehler
- kombinierter Logoutbericht bei Erfolg und Teilerfolg
- genau ein Logout-Lauf über Task-Runner-Kategorie `shutdown`
- planbarer und idempotenter Autosave-Job-Abbruch
- Fensterzerstörung erst nach Bericht, Status und Autosave-Abbruch
- sichere Linux-XDG-Autostartaktivierung über Launcher-Schalter
- atomisches Schreiben und Schutz fremder Autostartdateien
- Safe-Mode blockiert Autosave, Backup und Autostartänderungen
- Inline- und datengetriebene Autostart-Hilfe werden als gleichwertig erkannt

### Sicherung

- `system/session_lifecycle.py`
- `system/autostart_manager.py`
- `tests/test_session_lifecycle.py`
- `tests/test_autostart_manager.py`
- `tests/test_gate5_safe_mode.py`
- `tests/test_gate5_session_lifecycle_codemod.py`
- `scripts/apply_gate5_session_lifecycle.py`
- `scripts/apply_gate5_session_lifecycle_v2.py`
- `.github/workflows/gate-5-session-lifecycle.yml`
- `dateiindex/gehaertet/GATE_5_SESSION_LIFECYCLE.md`

## Gate 6 – Modulkarten und Lebenszyklus

### Abgeschlossen

- Kartenstatus ausschließlich aus dem autoritativen Managerzustand
- fehlgeschlagene Aktivierung bleibt sichtbar inaktiv
- fehlgeschlagene Deaktivierung bleibt sichtbar aktiv
- Schaltflächen entsprechen dem tatsächlichen Zustand
- Karten werden nach Themewechseln erneut synchronisiert
- ausschließlich aktive Fenstermodule werden beim Schließen deaktiviert
- Exit-Fehler mit verbleibendem aktivem Modul blockiert `root.destroy()`
- keine Registry- oder globale Modulkonfiguration wird verändert

### Sicherung

- `system/module_lifecycle.py`
- `tests/test_module_lifecycle.py`
- `tests/test_gate6_module_lifecycle_codemod.py`
- `scripts/apply_gate6_module_lifecycle.py`
- `.github/workflows/gate-6-module-lifecycle.yml`
- `dateiindex/gehaertet/GATE_6_MODULE_LIFECYCLE.md`

## Gate 7 – Launcher-Controller und Teilviews

### Abgeschlossen

- autoritativer Zustand für Show-all, Debug, Theme und Kontext-Hilfe
- sichtbare Checkboxen, Tastenkürzel, Undo und Redo verwenden denselben Controller
- No-op-Änderungen erzeugen weder Refresh noch Verlaufseintrag
- generationssicheres Refresh-Debouncing
- veraltete Refresh-Callbacks bleiben auch bei fehlgeschlagenem Abbruch wirkungslos
- Themewechsel werden validiert und sind über Undo/Redo wiederherstellbar
- Hilfe- und Shortcutdefinitionen sind datengetrieben, vollständig und eindeutig
- Statusübergänge und Busy-Cursor werden aus einem testbaren Viewmodell abgeleitet
- Controller ist ohne echte Tkinter-Hauptschleife testbar
- vorherige Gates 1, 3, 4 und 5 bleiben grün

### Sicherung

- `system/launcher_controller.py`
- `tests/test_launcher_controller.py`
- `tests/test_gate7_launcher_controller_codemod.py`
- `scripts/apply_gate7_launcher_controller.py`
- `scripts/apply_gate7_launcher_controller_v2.py`
- `.github/workflows/gate-7-launcher-controller.yml`
- `dateiindex/gehaertet/GATE_7_LAUNCHER_CONTROLLER.md`

## Ergebnis Arbeitsblock 3

Die zuvor gemischten Verantwortlichkeiten der beiden produktiven UI-Einstiegspunkte sind testgesichert in klar abgegrenzte Bausteine überführt. Alle sieben Gates wurden vor der jeweiligen Produktionsintegration geprüft und anschließend erneut gegen die betroffenen Regression-Gates validiert.

## Verbleibende Abnahme

Nicht durch Unit-, Struktur- oder Codemodtests ersetzbar sind:

- physische visuelle Abnahme auf Linux,
- physische Bedienprüfung mit echtem Fenstermanager,
- Autostartprüfung nach realer Benutzeranmeldung,
- responsive Abnahme auf Tablet und iPhone,
- Prüfung von Kontrast, Fokusführung, Zoom, Drag/Resize und langen Texten im realen Rendering.

Visuelle oder responsive Änderungen müssen in einem neuen, erneut begrenzten Arbeitsblock erfolgen.

## Globale Stopregeln

- Kein Produktionscode ohne grünes Gate verschieben.
- Keine parallele Modularisierung beider UI-Dateien.
- Keine visuellen Änderungen im Strukturcommit.
- Bei unerwarteter Ausgangsstruktur sofort abbrechen.
- Gehärtet erst nach Testnachweis und dokumentierter Restgrenze.
