# Härtungsnachweis – UI-Modernisierung Block 3

Stand: 2026-08-04

## Status

**Gehärtet:** gemeinsame Tk-Komponentenrollen, tokenbasierte Metriken und visuelle Zustände.

## Produktionsdateien

- `system/ui_components.py`
- `system/ui_theme_adapter.py`
- `system/launcher_gui.py`
- `system/main_window.py`

## Belegtests

- `tests/test_ui_components.py`
- `tests/test_ui_theme_adapter.py`
- `tests/test_ui_modernization_block3_codemod.py`
- `tests/test_ui_governance.py`

## Nachgewiesene Verträge

1. Runtimewerte stammen aus `generated/design_tokens.py`.
2. Es existiert keine parallele handgepflegte Komponenten- oder Tokenquelle.
3. Buttonrollen besitzen getrennte Normal-, Hover-, Active-, Focus- und Disabled-Zustände.
4. Primär-, Sekundär-, Neutral- und Gefahrrollen sind visuell unterscheidbar.
5. Eventbindungen werden idempotent registriert.
6. Deaktivierte Widgets ignorieren Hover und Active.
7. Panels und Karten verwenden gemeinsame Flächenregeln.
8. Launcher-Status verwendet gemeinsame visuelle Zustände, ohne den Controllervertrag zu übernehmen.
9. Modulkarten verwenden gemeinsame Aktionsrollen, ohne den ModuleManager zu ersetzen.
10. Der Codemod ist idempotent und erkennt unvollständige Integration.

## Erhaltene Sicherheitsgrenzen

- keine Änderung an TaskRunner-Ausführung
- keine Änderung an Autosave, Backup oder Shutdown
- keine Änderung an Autostart
- keine Änderung an ModuleManager und Modul-Lifecycle
- keine Änderung an Close-Policy
- keine Änderung an Workspace-Geometrie
- keine Änderung an Dateioperationen
- keine neue Hintergrundausführung

## Read-only-Abschluss

Der endgültige Workflow muss verwenden:

```yaml
permissions:
  contents: read
```

Er prüft:

- Komponenten- und Themeverträge
- Codemod-Idempotenz
- Governance und Block-3-Diff
- Python-Syntax
- Design-Token-Drift
- relevante Regression-Gates
- Xvfb-UI-Abnahme
- unverändertes Repository nach Tests

## Bekannte Grenzen

- Tkinter unterstützt keine nativen CSS-Radien oder echten Schatten.
- Rundungswerte sind als Designvertrag vorhanden, werden aber nur dort simuliert, wo dies robust und wiederverwendbar ist.
- Die vollständige Typografie- und Außenlayoutmigration bleibt den Oberflächenblöcken 7 bis 9 vorbehalten.
- Physische Geräteabnahme bleibt Block 10.

## Nächster Block

Block 4 entscheidet anhand der realen Verbraucherzahl über `system/ui_tables.py`. Ohne zweiten produktiven Treeview-Verbraucher erfolgt keine Extraktion.
