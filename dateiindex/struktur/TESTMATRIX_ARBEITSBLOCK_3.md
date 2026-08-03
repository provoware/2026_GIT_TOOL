# Testmatrix Arbeitsblock 3

Stand: 2026-08-03
Status: Gates 1 bis 5 abgeschlossen; Gate 6 ist der nächste zulässige Schritt

## Zweck

Vor jeder Auslagerung aus `system/launcher_gui.py` oder `system/main_window.py` muss ein passendes Sicherungstest-Gate bestehen. Strukturänderungen, visuelle Änderungen und Verhaltensänderungen bleiben getrennt.

## Verbindliche Reihenfolge

1. Berichtformatierer – abgeschlossen
2. Workspace-Geometrie und Kollision – abgeschlossen
3. Einheitlicher Themeadapter – abgeschlossen
4. Task-Runner für Threads und Prozesse – abgeschlossen
5. Autosave, Shutdown und Autostart – abgeschlossen
6. Modulkarten und Modul-Lebenszyklus – als Nächstes
7. Launcher-Controller und Teilviews

## Gate 1 – Berichtformatierer

### Umfang

Nur Funktionen ohne UI-, Thread-, Prozess-, Logging- oder Dialogseiteneffekte:

- Wartungsbericht
- Diagnosebericht
- Datei-Ampelstatus
- End-Audit
- Modul-Selbsttests
- Fehlersimulation

`_append_module_check` bleibt im Controller, weil die Methode zusätzlich Fehlerdialoge und Logging ausführt.

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
- UI-Callback ausschließlich über den injizierten `root.after`-Scheduler
- Erfolgs-, Fehler- und Ausnahmezustand über `TaskOutcome`
- Kategorie wird vor dem Abschluss-Callback freigegeben
- Wiederherstellung deaktivierter Diagnose- und Wartungsschaltflächen
- kontrollierte Thread-Start- und Schedulerfehler
- zentrale Kommando- und Pfadvalidierung
- zentrale Wartungsprozessausführung
- kein Tkinter-Zugriff aus Worker-Threads
- deterministische Abschlussresultate für Wartung und Diagnose

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
- keine Tkinter-Nutzung im Worker
- sichere Linux-XDG-Autostartaktivierung über Launcher-Schalter
- atomisches Schreiben des eigenen Desktop-Eintrags
- Schutz fremder gleichnamiger Autostartdateien
- standardkonforme `Exec`-Quotierung, `TryExec` und Arbeitsverzeichnis
- Safe-Mode verhindert Autosave-Planung
- Safe-Mode überspringt Autosave und Backup vollständig
- Safe-Mode blockiert Autostartänderungen

### Sicherung

- `system/session_lifecycle.py`
- `system/autostart_manager.py`
- `tests/test_session_lifecycle.py`
- `tests/test_autostart_manager.py`
- `tests/test_gate5_safe_mode.py`
- `tests/test_gate5_session_lifecycle_codemod.py`
- `scripts/apply_gate5_session_lifecycle.py`
- `.github/workflows/gate-5-session-lifecycle.yml`
- `dateiindex/gehaertet/GATE_5_SESSION_LIFECYCLE.md`

## Gate 6 – Modulkarten und Lebenszyklus

Vor der Auslagerung erforderlich:

- Aktivierung/Deaktivierung
- Warn- und Fehlerstatus
- Widgetzustand entspricht Managerzustand
- Close-Policy explizit getestet
- keine unbeabsichtigte globale Deaktivierung

## Gate 7 – Launcher-Controller und Teilviews

Erforderlich:

- Refresh-Debounce
- Show-all und Debug
- Themewechsel mit Undo/Redo
- Hilfe- und Shortcutregistrierung
- Statusübergänge
- Controller ohne echte Tkinter-Hauptschleife testbar

## Globale Stopregeln

- Kein Produktionscode ohne grünes Gate verschieben.
- Keine parallele Modularisierung beider UI-Dateien.
- Keine visuellen Änderungen im Strukturcommit.
- Bei unerwarteter Ausgangsstruktur sofort abbrechen.
- Gehärtet erst nach Testnachweis und dokumentierter Restgrenze.
