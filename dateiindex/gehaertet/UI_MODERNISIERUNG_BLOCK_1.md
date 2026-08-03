# Härtungsnachweis – UI-Modernisierung Block 1

Stand: 2026-08-03

## Status

Block 1 definiert und prüft den Governance-Rahmen der UI-Modernisierung.

Es wurden bewusst **keine** sichtbaren Produktionsoberflächen verändert.

## Gehärtete Artefakte

### `config/ui-governance.json`

Maschinenlesbare Festlegung für:

- autoritative Quellen,
- Übergangsquellen,
- geplante Verantwortlichkeiten,
- verbotene Parallelquellen,
- geschützte Verträge,
- Duplikatentscheidungen,
- Nicht-Ziele,
- Akzeptanzkriterien,
- Migrationsreihenfolge.

### `system/validate_ui_governance.py`

Prüft:

- Pflichtfelder und Datentypen,
- eindeutige Verantwortungseigentümer,
- Existenz aller aktuellen Quellen,
- Existenz geschützter Verträge und Belegtests,
- sichere relative Pfade,
- Abwesenheit verbotener Parallelquellen,
- Verbraucher bedingter Shared-Komponenten,
- eindeutige Duplikat-IDs und Themen,
- spätere Zielblöcke,
- aufsteigende Migrationsreihenfolge,
- nächsten zulässigen Block,
- zulässige Block-1-Änderungsdateien.

### `tests/test_ui_governance.py`

Sichert positive und negative Fälle:

- gültiger Gesamtvertrag,
- einzige Tokenquelle,
- Wiederverwendungsgrenze,
- reale Evidence-Dateien,
- belegtes Duplikatinventar,
- doppelte Verantwortung,
- fehlende Evidence-Datei,
- verbotene Parallelquelle,
- ungültige Migrationsreihenfolge,
- unerlaubte visuelle Laufzeitänderung.

## Autoritative Entscheidungen

1. `config/design-tokens.json` bleibt einzige handgepflegte Tokenquelle.
2. Ein neues `system/ui_tokens.py` ist verboten.
3. Block 2 erweitert den vorhandenen Generator um ein deterministisches Python-Artefakt.
4. `system/ui_theme_adapter.py` bleibt gemeinsamer Tkinter-Themeadapter.
5. Shared-Komponenten benötigen grundsätzlich zwei reale Verbraucher.
6. Treeview- und Vorschaucode bleiben bis zu einem zweiten Verbraucher im Datei-Manager.
7. Fachliche Statusmodelle werden nicht zugunsten eines universellen UI-Statusmodells zusammengelegt.
8. Bereits gehärtete Gates bleiben verbindliche Regressionen.

## Unveränderte Produktionsverantwortungen

- Launcher-View und Launcher-Controller
- Hauptfenster und Workspace-Geometrie
- Themeadapter und Responsive-Regeln
- Datei-Manager-Browser und Vorschaufenster
- Task-Runner
- Autosave, Backup und Shutdown
- Autostart
- Modul-Lifecycle und Close-Policy
- Berichtformatierer

## Sicherheitsgrenzen

- kein UI-Zugriff aus Worker-Threads,
- keine neue Schreibfunktion,
- keine Änderung an Safe-Mode,
- keine Änderung an Dateioperationen,
- keine native Mobilfreigabe für Tkinter,
- keine neue externe Laufzeitabhängigkeit.

## Nächster zulässiger Schritt

**Block 2: zentrale Token-Laufzeitabbildung**

Block 2 darf den Token-Generator und generierte Artefakte erweitern, aber noch keine großflächige sichtbare Oberflächenmigration durchführen.
