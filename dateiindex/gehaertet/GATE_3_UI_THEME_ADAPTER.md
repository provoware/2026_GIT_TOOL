# Gate 3 – Gemeinsamer UI-Themeadapter

Stand: 2026-08-03
Status: gehärtet

## Umfang

- `system/ui_theme_adapter.py`
- `tests/test_ui_theme_adapter.py`
- `tests/test_gate3_ui_theme_codemod.py`
- `scripts/apply_gate3_ui_theme_adapter.py`
- `.github/workflows/gate-3-ui-theme-adapter.yml`
- Integration in `system/launcher_gui.py`
- Integration in `system/main_window.py`

## Vereinheitlichter Vertrag

Der Adapter übernimmt zentral:

- strikte oder fehlertolerante Theme-Auflösung
- Fallback auf das konfigurierte Standard-Theme
- Auflösung des Kontrast-Themes
- unveränderliche Farbübergabe an Verbraucher
- Statuspalette
- Tooltipfarben
- rekursive Tkinter-Widgetgestaltung
- OptionMenu-/Menügestaltung
- modulkartenspezifische Akzentgestaltung

## Nachweis

- sieben Themevertragstests erfolgreich
- Launcher-Codemod idempotent
- Hauptfenster-Codemod idempotent
- vollständige Kopien beider UI-Dateien erfolgreich transformiert
- transformierte Dateien erfolgreich kompiliert
- reale Integration über GitHub Actions erfolgreich
- dauerhafter Workflow anschließend auf `contents: read` zurückgehärtet
- Gates 1 und 2 mit dem integrierten Stand erneut erfolgreich

## Produktionsänderungsgrenze

`system/launcher_gui.py` delegiert ausschließlich:

- Kontrast-Theme-Auflösung
- Theme-Auflösung
- Status- und Tooltip-Paletten
- rekursive Widgetgestaltung

`system/main_window.py` delegiert ausschließlich:

- Theme-Auflösung mit Standard-Fallback
- rekursive Widgetgestaltung
- modulkartenspezifische Farben

## Unverändert

- konkrete Farbinhalte der Konfiguration
- UI-Aufbau und Anordnung
- Zoomsteuerung
- Hilfe und Shortcuts
- Statusabläufe
- Modulaktivierung und -deaktivierung
- Workspace-Geometrie
- Autosave, Backup und Shutdown

## Restgrenzen

- Der Adapter steuert keine Geschäftslogik.
- Visuelle physische Abnahmen auf Linux, Tablet und iPhone bleiben ein separater Prüfblock.
- Thread-, Prozess- und Busy-State-Orchestrierung bleibt Gate 4.
