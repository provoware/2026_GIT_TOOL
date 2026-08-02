# Testmatrix Arbeitsblock 3

Stand: 2026-08-03
Status: Gate 1 in Umsetzung

## Zweck

Vor jeder Auslagerung aus `system/launcher_gui.py` oder `system/main_window.py` muss ein passendes Sicherungstest-Gate bestehen. Strukturänderungen, visuelle Änderungen und Verhaltensänderungen bleiben getrennt.

## Verbindliche Reihenfolge

1. Berichtformatierer
2. Workspace-Geometrie und Kollision
3. Einheitlicher Themeadapter
4. Task-Runner für Threads und Prozesse
5. Autosave und Shutdown
6. Modulkarten und Modul-Lebenszyklus
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

### Integrationsstrategie

Die große Datei `system/launcher_gui.py` wird nicht manuell rekonstruiert. Ein deterministischer, AST-validierter Codemod:

1. prüft, ob `LauncherGui` und alle sechs erwarteten Methoden vorhanden sind,
2. ergänzt genau einen Importblock,
3. ersetzt ausschließlich die sechs freigegebenen Methodenkörper,
4. validiert die resultierende Python-Syntax,
5. ist idempotent und unterstützt `--check`,
6. bricht bei abweichender Ausgangsstruktur ab.

CI wendet den Codemod zunächst auf eine temporäre Arbeitskopie an und führt danach Syntax- und Gate-Tests aus. Erst bei grünem Gate wird die echte Datei mit demselben Codemod geändert.

## Gate 2 – Geometrie und Kollision

Erforderlich vor Auslagerung:

- Rechtecküberschneidung an allen Kanten
- Berührung ohne Überschneidung
- Bounds-Clamping
- Mindestgrößen
- 3×3-Initiallayout
- Verhalten bei kleinen Workspaces
- Reflow nach Größenänderung

## Gate 3 – Themeadapter

Erforderlich:

- identische Tokenauflösung in beiden Fenstern
- Fallback auf Standard-Theme
- vollständige Statusfarben
- rekursive Widgetanwendung
- kein Zugriff auf fehlende Farbschlüssel

## Gate 4 – Task-Runner

Erforderlich:

- genau ein paralleler Task pro Kategorie
- UI-Callback über `root.after`
- Erfolgs-, Fehler- und Ausnahmezustand
- Wiederherstellung deaktivierter Buttons
- Kommando- und Pfadvalidierung

## Gate 5 – Autosave und Shutdown

Erforderlich:

- Autosave aktiviert/deaktiviert
- Autosave-Fehler
- Backup-Erfolg/-Fehler
- kombinierter Logoutbericht
- Job-Abbruch
- Fensterzerstörung erst nach Abschluss

## Gate 6 – Modulkarten und Lebenszyklus

Erforderlich:

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
