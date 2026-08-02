# UI-Einstiegspunkte und Refaktorierungslandkarte

Stand: 3. August 2026

## Produktive Python-/Tkinter-Linie

### `scripts/start.sh`
Vorgesehener Linux-Startpfad. Führt vorbereitende Prüfungen und den eigentlichen Anwendungsstart zusammen.

### `system/launcher.py`
Kommandozeilen-Einstieg für Modulliste, Filterung und Pfadvalidierung. Vergleichsweise klar abgegrenzt.

### `system/launcher_gui.py`
Zentraler GUI-Launcher. Verbindet Konfiguration, Tooltips, Module, Diagnose, Backups, Autosave, Drag-and-drop, Undo/Redo, Entwicklerfunktionen und weitere Aktionen. Aufgrund der breiten Verantwortung ist diese Datei der wichtigste Kandidat für Arbeitsblock 3.

Vorgeschlagene spätere Modulgrenzen:

- GUI-Bootstrap und Fensterstart
- Theme- und Token-Anbindung
- Header und Statusereignisse
- Modulübersicht und Filterung
- Entwicklerbereich
- Tooltips und Hilfetexte
- Diagnose-, Backup- und Exportaktionen
- Drag-and-drop sowie Undo/Redo

### `system/main_window.py`
Hauptfenster mit Modulraster, Aktivierung, Status, Dragging, Größenänderung und Theme-Anwendung. Zweiter zentraler Refaktorierungskandidat.

Vorgeschlagene spätere Modulgrenzen:

- Fensteraufbau
- Modul-Kachelkomponente
- Layout- und Kollisionslogik
- Theme-Anwendung
- Modulaktionen und Statusrückmeldungen

### Unterstützende Kernbereiche

- `system/module_manager.py`: Modulzustände und Aktionen
- `system/module_loader.py`: Laden und Initialisieren
- `system/module_registry.py`: Registry und Metadaten
- `system/store.py`: gemeinsamer Zustand
- `system/config_models.py`: validierte Konfigurationsmodelle
- `system/logging_center.py`: zentrale Protokollierung

Diese Dateien müssen vor einer Zerlegung von `launcher_gui.py` auf zyklische Abhängigkeiten und Direktzugriffe geprüft werden.

## Historische React-/Vite-Linie

Unter `genrearchiv_werkzeug_v1_2_3_2026_01_06/` liegt ein separates historisches Frontend:

- `src/main.jsx`: Einstiegspunkt
- `src/App.jsx`: zentrale React-Oberfläche
- `src/index.css`: zentrale Styles
- `src/config/modules.js`: Modulkonfiguration
- `src/system/startupChecks.js`: Startprüfungen

Diese Linie ist als `historisch` eingestuft. Sie darf nicht automatisch mit der produktiven Tkinter-Architektur vermischt werden. Vor einer Übernahme einzelner Funktionen ist jeweils zu entscheiden: übernehmen, neu implementieren, archivieren oder entfernen.

## Reihenfolge vor Arbeitsblock 3

1. `launcher_gui.py` vollständig nach Verantwortlichkeiten kartieren.
2. Abhängigkeiten zu Manager, Store, Konfiguration und Diagnose erfassen.
3. `main_window.py` und Modul-Kachellogik getrennt bewerten.
4. Historische React-Linie gegen aktuelle Funktionsanforderungen abgleichen.
5. Erst danach konkrete Modulgrenzen festschreiben und jeweils nur eine Funktionsgruppe auslagern.
