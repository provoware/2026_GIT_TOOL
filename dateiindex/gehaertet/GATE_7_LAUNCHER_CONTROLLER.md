# Gate 7 – Launcher-Controller und Teilviews

Stand: 2026-08-03
Status: abgeschlossen

## Gehärteter Umfang

- `system/launcher_controller.py`
- autoritativer Zustand für `show_all`, `debug`, Theme und Kontext-Hilfe
- generationssicheres Refresh-Debouncing
- Undo/Redo nur für tatsächliche Zustandsänderungen
- datengetriebene Shortcut-Definitionen
- datengetriebene Hilfe-Teilviews
- testbare Statusübergänge ohne Tkinter-Hauptschleife
- kontrollierte Integration in `system/launcher_gui.py`

## Controllervertrag

1. Filter-, Theme- und Hilfestatus werden zentral im Controller gehalten.
2. Tkinter-Variablen bilden diesen Zustand ab und sind nicht länger die alleinige Wahrheitsquelle.
3. Mausbedienung, Tastenkürzel, Undo und Redo verwenden dieselben Zustandsmethoden.
4. No-op-Änderungen erzeugen weder einen Refresh noch einen Undo-Eintrag.
5. Nach einer Debug-Änderung wird auch der vom Hauptfenster verwendete Debugwert synchronisiert.
6. Ein Themewechsel wird vor der Anwendung gegen die bekannten Themes validiert.
7. Statusmeldungen verwenden ausschließlich `success`, `error` oder `busy`.
8. Der Busy-Cursor wird aus demselben Status-Viewmodell abgeleitet.

## Refresh-Debounce

- Es ist höchstens ein aktueller Refresh geplant.
- Ein vorheriger Job wird nach Möglichkeit abgebrochen.
- Veraltete Callbacks werden zusätzlich über eine Generationserkennung ignoriert.
- Dadurch kann auch ein fehlgeschlagener Scheduler-Abbruch keinen doppelten Refresh auslösen.
- Nach Ausführung oder Planungsfehler bleibt keine falsche Job-ID zurück.

## Teilviews

### Shortcuts

Die vollständige Shortcutliste wird durch `build_shortcut_specs()` bereitgestellt. Sequenzen sind eindeutig; gemeinsam genutzte Aktionen wie Refresh und Redo können mehrere Sequenzen besitzen.

### Hilfe

Die Hilfeeinträge werden durch `build_help_entries()` bereitgestellt. Jeder Eintrag besitzt:

- einen eindeutigen Widgetschlüssel,
- einen Tooltiptext,
- einen Kontext-Hilfetext.

Der Gate-5-Autostart-Hilfeeintrag wird im datengetriebenen Teilview weitergeführt. Der Gate-5-Codemod erkennt Inline- und Teilview-Hilfe als gleichwertige integrierte Zustände.

## Testnachweis

- initialer Controllerzustand
- Show-all- und Debugänderungen
- No-op-Änderungen ohne Verlaufseintrag
- Undo-/Redo-Rundlauf für Filter
- Themevalidierung und Theme-Undo/Redo
- Kontext-Hilfe und Leertextvalidierung
- Status-Viewmodelle und Cursorzustände
- letzter Refresh gewinnt
- veralteter Callback bleibt wirkungslos, auch wenn der Abbruch scheitert
- expliziter Refresh-Abbruch
- Planungsfehler ohne hängende Job-ID
- eindeutige und vollständige Shortcutdefinitionen
- eindeutige und vollständige Hilfeeinträge
- idempotenter kanonischer Codemod
- Python-Kompilierungsprüfung des vollständigen Launchers
- reale Integration über GitHub Actions
- read-only Abschlussprüfung
- Regression-Gates 1, 3, 4 und 5 erfolgreich

## Integrationsdateien

- `system/launcher_controller.py`
- `tests/test_launcher_controller.py`
- `tests/test_gate7_launcher_controller_codemod.py`
- `scripts/apply_gate7_launcher_controller.py`
- `scripts/apply_gate7_launcher_controller_v2.py`
- `.github/workflows/gate-7-launcher-controller.yml`
- `scripts/apply_gate5_session_lifecycle_v2.py`

Der kanonische Gate-7-Codemod ist:

- `scripts/apply_gate7_launcher_controller_v2.py`

## Unverändert

- Berichtformatierer
- Themeadapter und konkrete Farbwerte
- Task-Runner und Prozessausführung
- Autosave-, Backup- und Shutdown-Abläufe
- Autostartverwaltung
- Hauptfenster, Workspace-Geometrie und Modul-Lebenszyklus
- visuelles Layout und responsive Breakpoints

## Restgrenze

Arbeitsblock 3 ist mit Gates 1 bis 7 abgeschlossen. Noch offen bleiben:

- physische visuelle Abnahme auf Linux,
- physische Abnahme auf Tablet und iPhone,
- Bedienprüfung mit realem Fenstermanager und Desktop-Autostart,
- spätere visuelle oder responsive Änderungen als eigener, erneut testgesicherter Arbeitsblock.
