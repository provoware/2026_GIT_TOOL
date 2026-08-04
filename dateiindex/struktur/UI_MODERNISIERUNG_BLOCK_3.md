# UI-Modernisierung – Block 3

Stand: 2026-08-04  
Status: **Gemeinsame Tk-Komponenten und visuelle Zustände integriert**

## 1. Ziel

Block 3 führt eine kleine gemeinsame Darstellungsbasis für bestehende Tk-Widgets ein. Es entsteht kein neues GUI-Framework und keine parallele Theme-Engine.

Autoritative Verantwortung:

- Designwerte: `config/design-tokens.json`
- Python-Runtime: `generated/design_tokens.py`
- Komponentenrollen und Zustände: `system/ui_components.py`
- Themeauflösung und rekursive Tk-Anwendung: `system/ui_theme_adapter.py`

## 2. Komponentenvertrag

### Buttonrollen

- `primary`
- `secondary`
- `neutral`
- `danger`

Jede Rolle besitzt getrennte Werte für:

- normal
- hover
- active
- focus
- disabled

Eventbindungen werden nur einmal registriert. Deaktivierte Widgets können nicht in Hover- oder Active-Darstellungen wechseln.

### Flächenrollen

- `panel`
- `card`
- `elevated`

Die Tiefenwirkung bleibt auf Hintergrundabstufung, schmale Kontur und native Tk-Reliefs begrenzt. Es werden keine Canvas-Sonderlösungen für jedes Widget erzeugt.

### Statuszustände

- `idle`
- `busy`
- `success`
- `warning`
- `error`
- `disabled`

Jeder Zustand besitzt Farbe und Symbol. Fachlicher Text und fachlicher Zustand bleiben bei Launcher-Controller beziehungsweise Modul-Lifecycle.

## 3. Produktionsintegration

### Launcher

Registriert wurden:

- Primär: Übersicht aktualisieren, Backup
- Sekundär: Diagnose, Hauptfenster, Exporte
- Neutral: Systemscan, Standards, Logs
- Destruktiv: Abmelden und sichern
- Panels: Einstellungen, Hilfe, Entwicklerbereich, Status, Modulübersicht
- hervorgehobene Drop-Zone
- zentrale Statussymbole und Statusflächen

Unverändert blieben:

- Commands
- TaskRunner-Kategorien
- Refresh-Debounce
- Undo/Redo
- Hilferegister
- Shortcuts
- Autosave, Backup, Logout und Autostart

### Hauptfenster

Registriert wurden:

- Steuerbereich und Workspace als Panels
- Modulkarten als erhöhte Kartenfläche
- Aktivieren als Primäraktion
- Deaktivieren als destruktive Aktion

Entfernt wurden zwei lokale Metrikduplikate:

- festes `pady=7` der Modulkartenbuttons
- festes `padx=6, pady=8` des Theme-Menüs

Unverändert blieben:

- ModuleManager als Zustandsquelle
- Aktivierung und Deaktivierung
- Close-Policy
- Workspace-Geometrie
- Kollision, Drag und Resize

## 4. Codesparsamkeit

- keine neue Tokenquelle
- keine zweite Themeauflösung
- keine abstrakte Widget-Hierarchie
- bestehende Widgets werden nur registriert
- reine Berechnung ist ohne Tk-Root testbar
- Eventbindungen sind idempotent
- Tabellen- und Vorschaucode bleibt featurelokal

## 5. Fehlerbehandlung

Ungültige Fälle brechen kontrolliert ab:

- unbekannte Rollen
- ungültige Hex-Farben
- unzulässige Mischverhältnisse
- fehlende generierte Tokenruntime
- inkompatible Widgetklassen
- unvollständige Modulkarten

## 6. Nicht-Ziele

Nicht Bestandteil dieses Blocks:

- vollständiges Redesign des Launchers
- vollständiges Redesign des Hauptfensters
- visuelle Migration des Datei-Managers
- generische Treeview- oder Vorschauabstraktion
- native Mobile-App
- dekorative Daueranimation
- Änderung fachlicher Controller- oder Lifecycleverträge

## 7. Nächster zulässiger Block

**Block 4: Entscheidung über einen gemeinsamen Tabellenstandard.**

Eine Extraktion erfolgt nur, wenn ein zweiter realer Treeview-Verbraucher existiert. Andernfalls wird Block 4 mit der begründeten Entscheidung abgeschlossen, die Dateimanager-Sortierung featurelokal zu belassen.
