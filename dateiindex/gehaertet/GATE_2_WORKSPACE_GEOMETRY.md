# Gate 2 – Workspace-Geometrie

Status: Integration und CI-Prüfung ausstehend

## Umfang

- `system/workspace_geometry.py`: reine Raster-, Bounds-, Move-, Resize- und Kollisionsberechnungen
- `tests/test_workspace_geometry.py`: Sicherung der mathematischen Verträge
- `scripts/apply_gate2_workspace_geometry.py`: deterministische Integration in `system/main_window.py`

## Abgrenzung

Keine Änderung an Theme, Modul-Lebenszyklus, Tkinter-Widgetaufbau oder Statuskommunikation.

## Abschlusskriterien

1. Geometrietests grün
2. Codemod-Test grün und idempotent
3. `main_window.py` kompiliert
4. realer Diff auf `Rect` und sechs Geometrieadapter begrenzt
5. erst danach Status `gehaertet`
