# Gate 2 – Workspace-Geometrie

Status: gehärtet

## Umfang

- `system/workspace_geometry.py`: reine Raster-, Bounds-, Move-, Resize- und Kollisionsberechnungen
- `tests/test_workspace_geometry.py`: Sicherung der mathematischen Verträge
- `tests/test_gate2_workspace_codemod.py`: Syntax- und Idempotenzsicherung
- `scripts/apply_gate2_workspace_geometry.py`: ursprünglicher deterministischer Codemod
- `scripts/apply_gate2_workspace_geometry_v2.py`: normalisierte, idempotente Ausführung
- `system/main_window.py`: dünne Adapter auf die ausgelagerte Geometriebibliothek

## Nachweise

1. Geometrietests erfolgreich
2. Codemod-Test nach Zeilenendenormalisierung erfolgreich und idempotent
3. Codemod auf einer vollständigen Arbeitskopie zweimal geprüft
4. transformierte `main_window.py` erfolgreich kompiliert
5. Codemod auf dem realen Integrationsbranch erfolgreich angewendet
6. finaler Produktionsdiff auf `Rect`, Raster, Bounds, Drag, Resize und Kollision begrenzt
7. Workflow-Schreibrecht und gezielter Push auf den internen PR-Head erfolgreich

## Abgrenzung

Nicht verändert wurden:

- Theme- und Farbsteuerung
- Tkinter-Widgetaufbau
- Modulaktivierung und Moduldeaktivierung
- Statuskommunikation
- Fenster-Lebenszyklus und Shutdown

## Restgrenzen

- Das responsive Verhalten nutzt nach dem ersten Rasteraufbau weiterhin die bestehende `_layout_ready`-Policy.
- Eine grundlegende Reflow- oder Layout-Policy-Änderung gehört nicht zu Gate 2.
- Der Modul-Lebenszyklus bleibt bis Gate 6 unverändert.
