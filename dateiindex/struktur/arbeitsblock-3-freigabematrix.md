# Arbeitsblock 3 – Freigabematrix

Stand: 3. August 2026

## Ziel

Arbeitsblock 3 darf erst mit einer kleinen, reversiblen Modularisierung beginnen, wenn die technischen Grenzen der produktiven Tkinter-Linie dokumentiert und durch das Release-Gate abgesichert sind.

## Verbindliche Reihenfolge

1. Design-Token-Drift und Python-Syntax laufen im CI fehlerfrei.
2. `system/launcher_gui.py` und `system/main_window.py` werden funktionsweise abgegrenzt.
3. Direkte Zustands-, Widget-, Thread- und Subprocess-Zugriffe werden vor jeder Auslagerung benannt.
4. Pro Pull Request wird nur eine zusammenhängende Funktionsgruppe ausgelagert.
5. Verhalten, öffentliche Funktionen und Startpfade bleiben während der Zerlegung kompatibel.

## Verantwortlichkeitsmatrix

| Bereich | Primärdatei | Abhängigkeiten | Risiko | Erster sinnvoller Schnitt |
| --- | --- | --- | --- | --- |
| GUI-Bootstrap und Konfiguration | `system/launcher_gui.py` | `config_models.py`, `launcher.py`, Logging | hoch | unverändert lassen, bis Hilfskomponenten ausgelagert sind |
| Tooltips und Hilfetexte | `system/launcher_gui.py` | Tkinter-Widgets, Theme-Farben | mittel | eigenständige Tooltip-Komponente |
| Diagnose und Selbsttests | `system/launcher_gui.py` | `diagnostics_runner.py`, `module_selftests.py`, `qa_checks.py` | mittel | Controller ohne direkte Layout-Verantwortung |
| Backup, Export und Autosave | `system/launcher_gui.py` | `backup_center.py`, `autosave_manager.py`, Dateisystem | hoch | Aktionsdienst mit klaren Rückgaben und Fehlern |
| Drag-and-drop sowie Undo/Redo | `system/launcher_gui.py` | `drag_drop.py`, `undo_redo.py`, gemeinsamer Zustand | hoch | erst nach Zustandsanalyse auslagern |
| Modulraster und Kacheln | `system/main_window.py` | `module_manager.py`, Tkinter, Modulstatus | hoch | Kachelkomponente mit stabiler Schnittstelle |
| Layout und Größenänderung | `system/main_window.py` | Widget-Geometrie, Dragging, Kollisionslogik | hoch | Layout-Engine ohne Modulaktionen |
| Theme-Anwendung | beide Dateien | Design-Tokens, Widget-Konfiguration | mittel | gemeinsamer Theme-Adapter |
| Header und Statusereignisse | beide Dateien | Prozesse, Speicherungen, Fehlerstatus | mittel | Ereignismodell vor visueller Komponente |

## Freigabekriterien für den ersten Refaktorierungs-PR

- Release-Gate ist grün.
- Der Schnitt betrifft nur eine Funktionsgruppe.
- Keine Änderung am Nutzerablauf oder an gespeicherten Datenformaten.
- Importpfade und Startskripte bleiben funktionsfähig.
- Fehler werden weiterhin sichtbar protokolliert und nutzerverständlich ausgegeben.
- Rückbau ist durch einen einzelnen Revert möglich.
- Dateiindex und Härtungsstatus werden im selben PR aktualisiert.

## Empfohlener erster Schnitt

`Tooltip` aus `system/launcher_gui.py` in eine kleine UI-Hilfskomponente auslagern. Dieser Bereich hat eine erkennbare Verantwortung, vergleichsweise wenige fachliche Abhängigkeiten und ist leichter isoliert prüfbar als Backup-, Thread-, Status- oder Modulmanagement.

## Stopregeln

Die Modularisierung wird gestoppt, wenn mindestens einer dieser Fälle eintritt:

- CI ist rot oder die generierten Design-Tokens weisen Drift auf.
- Ein Schnitt erfordert gleichzeitig Änderungen an mehreren fachlichen Bereichen.
- Direkte globale Zustände oder zyklische Imports sind ungeklärt.
- Nutzerverhalten, gespeicherte Daten oder Startpfade ändern sich unbeabsichtigt.
- Der Dateiindex bildet die tatsächliche Struktur nicht mehr ab.
