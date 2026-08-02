# Verantwortlichkeits- und Abhängigkeitsmatrix vor Arbeitsblock 3

Stand: 2026-08-03  
Status: **Analyse abgeschlossen – noch nicht gehärtet**

## Zweck

Diese Matrix grenzt die tatsächlichen Verantwortungen von `system/launcher_gui.py` und `system/main_window.py` ab. Sie ist die verbindliche Vorarbeit für Arbeitsblock 3. In diesem Schritt wurde keine Laufzeitlogik modularisiert.

---

# 1. Gesamtbild

| Datei | Primäre Rolle | Umfang der Verantwortung | Kopplung | Risiko |
| --- | --- | --- | --- | --- |
| `system/launcher_gui.py` | Startübersicht und technische Schaltzentrale | Sehr breit: UI, Themes, Hilfe, Barrierefreiheit, Autosave, Backup, Diagnose, Wartung, Export, Drag-and-Drop, Undo/Redo, Logout und Statusausgabe | Sehr hoch | Sehr hoch |
| `system/main_window.py` | Interaktives 3x3-Modulraster | Modulkarte, Raster, Drag, Resize, Kollisionsschutz, Aktivierung, Deaktivierung, Status und Theme | Hoch | Hoch |

## Zentrale Feststellung

`launcher_gui.py` ist keine reine View. Die Datei ist gleichzeitig:

- UI-Komposition
- Controller
- Prozess-Orchestrator
- Status- und Fehlerausgabe
- Theme-Engine
- Barrierefreiheits-Layer
- Wartungs-Frontend
- Sicherungs- und Logout-Steuerung

`main_window.py` vermischt:

- Widget-Darstellung
- Geometrie-Modell
- Interaktionssteuerung
- Layout-Algorithmus
- Modul-Lebenszyklus
- Theme-Anwendung

---

# 2. Externe Abhängigkeiten

## 2.1 `system/launcher_gui.py`

| Import/Abhängigkeit | Verwendungszweck | Richtung | Kritikalität | Vorgesehene Zielgrenze |
| --- | --- | --- | --- | --- |
| `argparse` | CLI-Parameter | eingehend | niedrig | Bootstrap/CLI |
| `subprocess` | Wartungsskripte und Systemaktionen | ausgehend | hoch | Prozess-Service |
| `threading` | Diagnose, Wartung, Backup und Logout außerhalb des UI-Threads | intern/ausgehend | hoch | Task-Runner |
| `pathlib.Path` | Konfigurations-, Daten-, Log- und Skriptpfade | intern | mittel | Pfadkonfiguration |
| `autosave_manager` | Autosave-Konfiguration, Planung und Erstellung | ausgehend | hoch | Autosave-Service |
| `backup_center` | Backup-Konfiguration und Sicherung | ausgehend | hoch | Backup-Service |
| `diagnostics_runner` | Tests und Codequalität ausführen | ausgehend | hoch | Diagnose-Service |
| `end_audit` | Release-/Aufgabenstatus anreichern | ausgehend | mittel | QA-Berichtsservice |
| `error_simulation` | simulierte Fehlerfälle darstellen | ausgehend | mittel | QA-Berichtsservice |
| `main_window` | separates Modulraster öffnen | ausgehend | hoch | Window-Navigation |
| `module_checker` | Moduleinträge prüfen | ausgehend | hoch | Modul-Prüfservice |
| `module_selftests` | Modul-Selbsttests | ausgehend | hoch | Modul-Prüfservice |
| `qa_checks` | Dateistatus und Schweregrade | ausgehend | hoch | QA-Service |
| `config_models` | typisierte GUI-Konfiguration | eingehend | hoch | Konfigurationsadapter |
| `drag_drop.DragDropManager` | Drag-and-Drop der Startübersicht | ausgehend | mittel | UI-Interaktionsadapter |
| `launcher` | Module laden und filtern | ausgehend | hoch | Modul-Abfrage-Service |
| `logging_center` | Logger und Logging-Konfiguration | ausgehend | mittel | Logging-Port |
| `module_manager.ModuleManagerError` | Fehler beim Öffnen/Steuern des Hauptfensters | eingehend | mittel | Fehlerübersetzung |
| `undo_redo` | Theme-, Filter- und Debug-Aktionen rückgängig machen | intern | mittel | UI-Command-History |
| `tkinter` | gesamte GUI-Laufzeit | Framework | hoch | View-Schicht |

## 2.2 `system/main_window.py`

| Import/Abhängigkeit | Verwendungszweck | Richtung | Kritikalität | Vorgesehene Zielgrenze |
| --- | --- | --- | --- | --- |
| `argparse` | CLI-Parameter | eingehend | niedrig | Bootstrap/CLI |
| `dataclasses.dataclass` | `Rect`-Geometriemodell | intern | niedrig | Layout-Modell |
| `pathlib.Path` | Konfigurationspfade | intern | mittel | Pfadkonfiguration |
| `config_models` | GUI-Konfiguration und Themes | eingehend | hoch | Konfigurationsadapter |
| `logging_center` | Startfehler protokollieren | ausgehend | mittel | Logging-Port |
| `module_manager` | Modulzustände, Aktivierung und Deaktivierung | ausgehend | sehr hoch | Modul-Lebenszyklus-Service |
| `tkinter` | Fenster, Modulwidgets und Platzierung | Framework | hoch | View-Schicht |

---

# 3. Verantwortungsmatrix `launcher_gui.py`

| Bereich | Elemente | Eingaben | Ausgaben/Seiteneffekte | Direkte Abhängigkeiten | Refaktorierungsziel |
| --- | --- | --- | --- | --- | --- |
| Fehlervertrag | `GuiLauncherError` | ungültige Werte/Operationen | kontrollierter Abbruch | mehrere | gemeinsamer UI-Fehlertyp |
| Tooltip-System | `Tooltip` | Widget, Text-Provider, Stil | bindet Events, erzeugt/zerstört `Toplevel` | Tkinter | eigenes `ui/tooltip.py` |
| Primitive Validierung | `_require_text`, `_require_bool`, `_require_list_of_strings` | Laufzeitwerte | Fehler bei ungültigen Typen | keine | gemeinsames Validation-Modul |
| Konfiguration | `load_gui_config` | JSON-Pfad | `GuiConfigModel` | `config_models` | Bootstrap/Adapter |
| Modultext | `build_module_lines`, `render_module_text` | Module, Root, Debug | formatierter Text | Modulmodell | Presenter ohne Tkinter |
| Modulprüfung | `run_module_check` | Modulkonfiguration | Fehlerliste | `module_checker` | Prüfservice |
| CLI | `build_parser`, `main` | Argumente | Exitcode/Logging | argparse, config, logger | `launcher_gui_entry.py` |
| GUI-Bootstrap | `run_gui` | Konfiguration | Tk-Root, Mainloop | Tkinter, `LauncherGui` | Fensterfabrik |
| UI-Komposition | `LauncherGui._build_ui` | Konfiguration/Layout | erzeugt alle sichtbaren Bereiche | Tkinter | mehrere View-Komponenten |
| Font/Zoom | `_init_fonts`, `_bind_zoom_controls`, `_on_zoom_mousewheel`, `_adjust_zoom`, `_apply_zoom`, `_apply_button_widths` | Zoomereignisse | globale Tk-Fonts und Buttonbreiten ändern | Tkinter Font | `ZoomController` |
| Tastatur/Barrierefreiheit | `_bind_accessibility_shortcuts`, Fokus- und Hilfefunktionen | Keyboard/Fokus | globale Bindings, Status/Hilfe | Tkinter | `AccessibilityController` |
| Responsive Layout | `_bind_responsive_layout` und zugehörige Layoutreaktionen | Fenstergröße | Grid-/Wrap-Anpassung | Tkinter | `ResponsiveLayoutController` |
| Hilfe | `_bind_help_context`, `_register_help_entries`, `_register_help`, `_announce_context_help` | Fokus/Widget | Kontexttext und Tooltips | Tooltip, Tkinter | `HelpRegistry` |
| Theme | `_resolve_contrast_theme`, `_toggle_contrast_theme`, `_set_theme`, `_on_theme_changed`, `_restore_theme`, `apply_theme`, `_apply_widget_style` | Theme-Name | rekursive Widget-Stiländerung | `GuiConfigModel`, Tkinter | `ThemeController` + Adapter |
| Filter/Debug | `_toggle_show_all`, `_toggle_debug`, `_set_show_all`, `_set_debug` | UI-Aktion | Variablenänderung, Refresh, Undo-Eintrag | Undo/Redo | `LauncherPreferencesController` |
| Undo/Redo | `_record_action`, `undo_action`, `redo_action` | Commands | History und Status | `UndoRedoManager` | eigener Controller |
| Modulübersicht | `request_refresh`, `refresh` | Filter, Debug, Konfiguration | lädt Module, führt Prüfungen aus, aktualisiert Text | launcher, module_checker, qa_checks, end_audit, selftests, simulation | `OverviewService` + Presenter |
| Statusausgabe | `_set_output`, `_append_output`, `_set_status`, `_apply_status_style`, `_show_error` | Texte/Status | Text-Widget, Cursor, Messagebox | Tkinter | `StatusPresenter` |
| Berichtformatierung | `_append_module_check`, `_append_file_status`, `_append_end_audit`, `_append_selftests`, `_append_error_simulation`, Diagnose-/Wartungsformatierer | Resultatobjekte | formatierter Bericht | QA-Modelle | reine Presenter-Funktionen |
| Autosave | `_setup_autosave`, `_schedule_autosave`, `_run_autosave`, `_cancel_autosave_job` | Settings, Timer | Dateien schreiben, Timer planen | `autosave_manager`, Tkinter `after` | `AutosaveController` |
| Logout | `request_logout`, `_execute_logout`, `_finish_logout` | Fenster-Schließen/Shortcut | Autosave, Backup, Thread, Fenster zerstören | autosave, backup, threading | `ShutdownCoordinator` |
| Diagnose | Start-/Run-/Finish-Funktionen | Button/Shortcut | Thread, Testskript, Bericht | diagnostics_runner | `DiagnosticsController` |
| Wartung | `_run_maintenance_task`, `_execute_maintenance`, `_finish_maintenance`, `_format_maintenance_report`, `_set_maintenance_buttons` | Befehlsliste | externe Prozesse, UI-Sperre, Bericht | subprocess, threading | `MaintenanceTaskRunner` |
| Entwickleraktionen | Systemscan, Standards, Logs, Export, Export-Center, Backup | Buttons/Shortcuts | Skriptstart, Ordneröffnung, Dateierzeugung | Prozess-Service, Backup/Export | einzelne Action-Adapter |
| Hauptfenster-Navigation | `open_main_window` | Button/Shortcut | neues Fenster | `main_window` | `WindowNavigator` |
| Drag-and-Drop | `_setup_drag_drop` und Drop-Callbacks | Dateien/Module | Prüfung/Status/Output | `DragDropManager` | eigener UI-Adapter |

---

# 4. Zustandsmatrix `LauncherGui`

| Zustand | Typ/Rolle | Schreiber | Leser | Risiko |
| --- | --- | --- | --- | --- |
| `root` | Tk-Hauptfenster | Konstruktor | nahezu alle UI-Funktionen | zentraler Framework-Zugriff |
| `module_config` | Modulkonfigurationspfad | Konstruktor | Refresh, Diagnose, Backup, MainWindow | hoher Kopplungspunkt |
| `gui_config` | typisierte UI-Konfiguration | Konstruktor | Theme, Layout, Refresh | Single Source für UI, aber breit genutzt |
| `theme_var`, `current_theme`, `last_non_contrast_theme`, `contrast_theme` | Theme-Zustand | Theme-Funktionen | Styling, Undo/Redo | mehrfach repräsentierter Zustand |
| `show_all_var`, `debug_var` | Filterzustand | UI/Undo | Refresh | UI-Variable und Fachzustand gekoppelt |
| `output_text` | Hauptausgabe | View-Aufbau | Status-/Berichtslogik | Presenter direkt an Widget gekoppelt |
| `status_var`, `status_label`, `status_indicator`, `status_palette` | Statussystem | Theme/Status | alle Controller | globales UI-Querschnittsthema |
| `diagnostics_running`, `maintenance_running`, `logout_running` | Prozess-Sperren | jeweilige Controller | Buttonaktionen | getrennte Boolesche Zustände ohne gemeinsames Taskmodell |
| `refresh_job`, `refresh_debounce_ms` | Refresh-Timer | Refresh-Controller | Refresh-Controller | Tk-Timer direkt gekoppelt |
| `autosave_config`, `autosave_job` | Autosave-Laufzeit | Autosave-Controller | Logout/Autosave | Lebenszyklusrisiko |
| `undo_manager` | Aktionshistorie | Konstruktor/Record | Undo/Redo | UI-Aktionen als Closures gebunden |
| `drag_drop_manager` | DnD-Adapter | Setup | Drop-Ereignisse | Framework-/Featurekopplung |
| Widgetreferenzen | Buttons, Frames, Labels, Menüs | `_build_ui` | Theme, Status, Sperren, Hilfe | sehr viele optionale Felder |
| Fonts/Zoomwerte | Fontobjekte und Basisgrößen | Font-/Zoomlogik | Styling | globaler Tk-Fontseiteneffekt |

---

# 5. Verantwortungsmatrix `main_window.py`

| Bereich | Elemente | Eingaben | Ausgaben/Seiteneffekte | Direkte Abhängigkeiten | Refaktorierungsziel |
| --- | --- | --- | --- | --- | --- |
| Fehlervertrag | `MainWindowError` | Konfigurationsfehler | kontrollierter Exit | config_models | gemeinsamer UI-Fehlertyp |
| Geometriemodell | `Rect` | x, y, Breite, Höhe | unverpackter veränderlicher Zustand | keine | eigenes Layout-Modell |
| Modulkachel | `ModuleWidget` | `ModuleState`, Theme, Callbacks | erzeugt Widgets und Eventbindungen | Tkinter | `ModuleCardView` |
| Drag-Interaktion | `_bind_drag`, `_start_drag`, `_drag`, `_end_drag` | Mausereignisse | Callback an Fenstercontroller | Tkinter | `DragGesture` |
| Resize-Interaktion | `_bind_resize`, `_start_resize`, `_resize`, `_end_resize` | Mausereignisse | Callback an Fenstercontroller | Tkinter | `ResizeGesture` |
| Kachelstatus | `update_status` | Text/Farbe | Labeländerung | Tkinter | View-Methode beibehalten |
| Fensteraufbau | `MainWindow._build_ui` | Konfiguration | Header, Steuerung, Workspace, Status | Tkinter | `MainWindowView` |
| Modulabfrage | `_create_module_widgets` | Manager-Zustände | maximal neun Kacheln | ModuleManager | Controller/Factory |
| Initiallayout | `_layout_modules` | Workspacegröße | 3x3-Positionen | Rect, Tkinter | `GridLayoutEngine` |
| Bounds-Korrektur | `_ensure_within_bounds` | Workspacegröße, Rects | Positionskorrektur | Rect | `LayoutEngine` |
| Drag-Koordination | `_drag_widget` | Delta und Widget | neue Position/Blockade | Kollisionslogik, Status | `LayoutController` |
| Resize-Koordination | `_resize_widget` | Zielgröße und Widget | neue Größe/Blockade | Kollisionslogik, Status | `LayoutController` |
| Kollision | `_is_collision`, `_rect_overlap` | Rechtecke | boolesch | keine/Tk-Objektliste | reine `geometry.py` |
| Modulaktivierung | `_activate_widget`, `_deactivate_widget`, `_apply_action_result` | Modul-ID | Manager-Aufruf und UI-Status | ModuleManager | `ModuleLifecycleController` |
| Fensterstatus | `_set_status` | Nachricht/Farbe | Statuslabel | Tkinter | StatusPresenter |
| Schließen | `_on_close` | Window-Event | alle Module deaktivieren, Fenster zerstören | ModuleManager, Tkinter | `ShutdownCoordinator` |
| Themeauflösung | `_theme_colors` | Themevar | Farbdictionary | GuiConfigModel | ThemeAdapter |
| Themeanwendung | `_apply_theme` | Themefarben | rekursive/partielle Widget-Stile | Tkinter | gemeinsame Theme-Engine |
| CLI/Bootstrap | `build_parser`, `load_gui_config_safe`, `run_main_window`, `main` | Argumente/Pfade | Mainloop/Exitcode | argparse, config, logger | Entry-Modul |

---

# 6. Zustandsmatrix `MainWindow` und `ModuleWidget`

| Objekt | Zustand | Bedeutung | Risiko |
| --- | --- | --- | --- |
| `ModuleWidget` | `state` | fachlicher Modulzustand beim Erstellen | kann nach Manager-Aktionen veralten |
| `ModuleWidget` | `_drag_start`, `_resize_start` | laufende Mausgeste | direkt an Root-Koordinaten gekoppelt |
| `ModuleWidget` | `rect`, `last_valid_rect` | aktuelle und letzte gültige Geometrie | mutable Doppelhaltung |
| `ModuleWidget` | `min_width`, `min_height` | feste Mindestmaße | nicht aus Design-Tokens |
| `ModuleWidget` | Callbackfelder | Aktivieren, Deaktivieren, Drag, Resize, Status | hohe Rückkopplung an Controller |
| `MainWindow` | `manager` | Modul-Lebenszyklus | zentrale fachliche Abhängigkeit |
| `MainWindow` | `module_widgets` | sichtbare Kacheln | zugleich Viewliste und Kollisionsquelle |
| `MainWindow` | `workspace` | Layoutcontainer | Frameworkkopplung |
| `MainWindow` | `theme_name`, `theme_var` | Themeauswahl | doppelte Theme-Repräsentation |
| `MainWindow` | `_layout_ready` | Initiallayout-Schalter | verhindert vollständiges Reflow nach Größenänderung |

---

# 7. Direkte Aufruf- und Ereignisketten

## Startübersicht

```text
main
→ build_parser
→ setup_logging
→ load_gui_config
→ run_gui
→ Tk()
→ LauncherGui(...)
→ _build_ui
→ Theme/Hilfe/Shortcuts/DnD/Autosave registrieren
→ request_refresh
→ mainloop
```

## Aktualisierung

```text
Button/Shortcut/Filteränderung
→ request_refresh
→ Tk.after(debounce)
→ refresh
→ load_modules + filter_modules
→ render_module_text
→ Modulcheck/QA/Selftests/End-Audit/Simulation
→ Berichtformatierer
→ _set_output
→ _set_status oder _show_error
```

## Diagnose/Wartung

```text
Button/Shortcut
→ Sperrstatus setzen
→ Thread starten
→ externer Runner oder subprocess
→ root.after(0, Finish-Callback)
→ Bericht ausgeben
→ Buttons freigeben
→ Status setzen
```

## Logout

```text
WM_DELETE_WINDOW oder Alt+Q
→ request_logout
→ Thread
→ Autosave
→ Backup
→ root.after
→ Bericht/Status
→ Timer abbrechen
→ root.destroy
```

## Hauptfenster

```text
main/run_main_window oder LauncherGui.open_main_window
→ MainWindow
→ ModuleManager
→ _build_ui
→ _create_module_widgets
→ Workspace-Configure
→ _layout_modules
```

## Drag/Resize

```text
ModuleWidget Mausbindung
→ Gesture-Start
→ Delta berechnen
→ MainWindow._drag_widget/_resize_widget
→ Bounds prüfen
→ _is_collision
→ place(...) oder Rücksetzen
→ Statusmeldung
```

## Modul-Lebenszyklus

```text
Kachelbutton
→ ModuleWidget Callback
→ MainWindow._activate_widget/_deactivate_widget
→ ModuleManager
→ ModuleActionResult
→ Kachelstatus + Fensterstatus
```

---

# 8. Kritische Kopplungen und Schwachstellen

| Befund | Auswirkung | Priorität für Arbeitsblock 3 |
| --- | --- | --- |
| `launcher_gui.py` besitzt sehr viele Verantwortungen | Änderungen erzeugen breite Regressionen | P0 |
| Geschäfts-/Prozesslogik schreibt direkt in Tk-Widgets | schwer isoliert testbar | P0 |
| Threads werden manuell pro Feature verwaltet | uneinheitliche Fehler- und Abbruchpfade | P0 |
| `subprocess.run` liegt im UI-Controller | Sicherheits-, Test- und Portabilitätsrisiko | P0 |
| Theme-Systeme in beiden Dateien sind getrennt und unterschiedlich | visuelle Drift | P0 |
| `main_window.py` nutzt feste Pixelwerte statt Design-Tokens | keine zentrale Designsteuerung | P1 |
| Modulzustand und Widgetzustand können auseinanderlaufen | falsche Statusanzeige möglich | P1 |
| `MainWindow._on_close` deaktiviert pauschal alle Module | potenziell unerwarteter Seiteneffekt | P1 |
| `ModuleWidget._apply_theme` wird von außen als private Methode aufgerufen | verletzte Kapselung | P1 |
| initiales 3x3-Layout wird nach `_layout_ready` nicht neu verteilt | begrenzte Responsivität | P1 |
| rekursive Widget-Stilisierung in `launcher_gui.py` kennt Widgetklassen nur teilweise | inkonsistente Darstellung | P1 |
| zahlreiche optionale Widgetfelder | Laufzeitfehler bei unvollständigem Aufbau möglich | P2 |
| allgemeine `except Exception` in Prozesspfaden | Fehlerursachen können verwischt werden | P2 |
| Undo/Redo speichert Closures auf UI-Objekte | schwer serialisierbar und testbar | P2 |

---

# 9. Verbindliche Modulgrenzen für Arbeitsblock 3

## Phase 3A – reine Logik ohne Verhaltensänderung

1. `system/ui/validation.py`
   - primitive Validierungen
2. `system/ui/presenters/launcher_reports.py`
   - Text- und Berichtformatierung
3. `system/ui/geometry.py`
   - `Rect`, Bounds und Kollisionsprüfung
4. `system/ui/theme_adapter.py`
   - Themeauflösung und normalisierte Farbschnittstelle

## Phase 3B – Controller auslagern

1. `system/ui/controllers/status_controller.py`
2. `system/ui/controllers/zoom_controller.py`
3. `system/ui/controllers/help_controller.py`
4. `system/ui/controllers/autosave_controller.py`
5. `system/ui/controllers/task_runner.py`
6. `system/ui/controllers/module_layout_controller.py`
7. `system/ui/controllers/module_lifecycle_controller.py`

## Phase 3C – Views verkleinern

1. `system/ui/views/launcher_view.py`
2. `system/ui/views/module_card.py`
3. `system/ui/views/main_window_view.py`

## Phase 3D – schlanke Einstiegspunkte

- `system/launcher_gui.py`: Argumente, Konfiguration, Komposition und Start
- `system/main_window.py`: Argumente, Konfiguration, Komposition und Start

---

# 10. Reihenfolge mit Stopregeln

| Schritt | Änderung | Pflichtprüfung | Stoppregel |
| --- | --- | --- | --- |
| 1 | reine Berichtformatierer auslagern | bestehende Texttests unverändert | bei Textabweichung stoppen |
| 2 | Geometrie/Kollision auslagern | Drag-/Resize-Unit-Tests | bei Geometrieabweichung stoppen |
| 3 | Themeadapter vereinheitlichen | alle Themes und Kontrast prüfen | bei Farb-/Keyfehler stoppen |
| 4 | Task-Runner extrahieren | Erfolgs-, Fehler- und Exceptionpfad | bei UI-Thread-Zugriff stoppen |
| 5 | Autosave/Logout koordinieren | Timer, Backupfehler, Schließen | bei Datenrisiko stoppen |
| 6 | ModuleCard/View trennen | Aktivieren, Deaktivieren, Status | bei Zustandsdrift stoppen |
| 7 | LauncherView zerlegen | Tastatur, Hilfe, Fokus, Zoom | bei Barrierefreiheitsverlust stoppen |

Pro Schritt nur eine logische Verantwortung auslagern. Kein paralleles Großrefactoring.

---

# 11. Abnahmekriterien vor Beginn der Code-Modularisierung

- [x] Verantwortungen beider Dateien erfasst
- [x] externe Abhängigkeiten erfasst
- [x] zentrale Zustände erfasst
- [x] Seiteneffekte erfasst
- [x] UI-Ereignisketten erfasst
- [x] Zielmodule definiert
- [x] Risikoreihenfolge festgelegt
- [ ] lokale/CI-Testbasis erneut ausführen
- [ ] aktuelle Zeilenanzahl und Komplexitätswerte automatisiert erfassen
- [ ] Tests den geplanten Zielmodulen zuordnen

## Abschlussstatus

**MATRIX ABGESCHLOSSEN – ARBEITSBLOCK 3 NOCH NICHT BEGONNEN**
