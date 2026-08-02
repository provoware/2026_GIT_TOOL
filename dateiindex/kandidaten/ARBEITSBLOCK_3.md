# Kandidaten fuer Arbeitsblock 3

Stand: 3. August 2026

## Prioritaet 1

### `system/launcher_gui.py`
Breite Verantwortung: GUI-Aufbau, Tooltips, Module, Diagnose, Autosave, Backup, Drag-and-drop, Undo/Redo und Entwickleraktionen.

Vor Zerlegung pruefen:

- globale und gemeinsam genutzte Zustaende
- direkte Widget-Zugriffe
- Thread- und Subprocess-Nutzung
- Fehlerweitergabe und Nutzerfeedback
- Abhaengigkeiten zu `main_window.py`, Manager, Store und Konfiguration

## Prioritaet 2

### `system/main_window.py`
Enthaelt Modul-Kacheln, Layout, Dragging, Resize, Theme-Anwendung und Modulstatus.

Moegliche spaetere Zielmodule:

- `ui/main_window.py`
- `ui/module_tile.py`
- `ui/layout_engine.py`
- `ui/theme_adapter.py`

## Prioritaet 3

- `system/module_manager.py`
- `system/store.py`
- `system/module_loader.py`
- `system/module_registry.py`
- `system/config_models.py`

Diese Dateien bilden die fachlichen Grenzen, die vor dem Auslagern der GUI-Logik stabil sein muessen.

## Historische Kandidaten

- `genrearchiv_werkzeug_v1_2_3_2026_01_06/src/App.jsx`
- `genrearchiv_werkzeug_v1_2_3_2026_01_06/src/index.css`

Status: historisch. Erst Funktionswert pruefen, dann gezielt uebernehmen oder archivieren. Keine parallele Vollrefaktorierung zusammen mit der Tkinter-Linie.

## Stopregel

Arbeitsblock 3 beginnt erst nach einer vollstaendigen Verantwortlichkeits- und Abhaengigkeitsmatrix fuer `launcher_gui.py` und `main_window.py`. Pro Durchlauf wird nur eine logisch zusammenhaengende Funktionsgruppe ausgelagert.
