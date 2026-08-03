# UI-Modernisierung – Block 1: Entwicklungs- und Designregeln

Stand: 2026-08-03  
Status: **Governance und Bestandsanalyse**  
Produktive visuelle Migration: **nicht Bestandteil dieses Blocks**

## 1. Ziel

Block 1 schafft einen verbindlichen, maschinenprüfbaren Rahmen für die weitere UI-Modernisierung. Er verhindert:

- neue parallele Tokenquellen,
- unkontrollierte Sonderkomponenten,
- wiederholte Button-, Karten- und Statuslogik,
- visuelle Änderungen ohne Sicherungstests,
- Vermischung mit bereits gehärteten Lifecycle- und Controllerverträgen,
- unnötige Abstraktionen bei nur einem realen Verbraucher.

Der maschinenlesbare Vertrag liegt in `config/ui-governance.json`. Die Prüfung erfolgt über `system/validate_ui_governance.py` und `tests/test_ui_governance.py`.

---

## 2. Zentrale Architekturentscheidung

### 2.1 Bestehende Tokenquelle bleibt autoritativ

`config/design-tokens.json` ist bereits die zentrale Design-Token-Quelle. Sie enthält:

- Themefarben,
- Abstände,
- Radien,
- Typografie,
- Schatten,
- Bewegungszeiten,
- Ebenen,
- Breakpoints,
- Layoutgrößen und Touch-Zielgröße.

Deshalb wird **kein** zusätzliches handgepflegtes `system/ui_tokens.py` eingeführt.

Block 2 darf stattdessen ausschließlich ein deterministisches Python-Artefakt aus der bestehenden Quelle erzeugen, beispielsweise:

```text
generated/design-tokens.py
```

Die Erzeugung bleibt Aufgabe von `system/generate_design_tokens.py`.

### 2.2 Übergangsquellen werden reduziert, nicht dupliziert

Folgende Dateien besitzen aktuell noch überlappende UI-Werte:

- `config/launcher_gui.json`
- `config/datei_manager.json`
- `system/launcher_gui.py`
- `system/main_window.py`
- `modules/datei_manager/window.py`

Sie bleiben zunächst funktionsfähig, dürfen aber nicht als neue langfristige Designquellen ausgebaut werden.

### 2.3 Keine vorschnellen Universalmodule

Ein generisches Modul wird erst extrahiert, wenn mindestens zwei reale Verbraucher existieren oder eine klar belegte Risiko-/Komplexitätsgrenze vorliegt.

Daraus folgt aktuell:

- `system/ui_components.py`: zulässig, weil Launcher, Hauptfenster und Datei-Manager gemeinsame Komponenten benötigen.
- `system/ui_tables.py`: noch nicht automatisch zulässig; aktuell existiert nur eine produktive Treeview im Datei-Manager.
- `system/ui_preview.py`: noch nicht automatisch zulässig; aktuell existiert nur die Datei-Manager-Vorschau.
- gemeinsame Tooltiplogik: erst bei einem zweiten realen Verbraucher.

Die vorhandene Datei-Manager-Logik in `modules/datei_manager/browser.py` und `modules/datei_manager/window.py` bleibt deshalb vorerst lokal.

---

## 3. Verantwortlichkeitsmatrix

| Verantwortung | Aktueller Eigentümer | Status | Nächste zulässige Veränderung |
| --- | --- | --- | --- |
| Design-Tokens | `config/design-tokens.json` | autoritativ | Block 2: Python-Artefakt erzeugen |
| Token-Generierung und Driftprüfung | `system/generate_design_tokens.py` | gehärtet | Block 2: Ausgabeformat erweitern |
| Tkinter-Themeauflösung und Anwendung | `system/ui_theme_adapter.py` | gehärtet | vorhandenen Adapter erweitern, nicht ersetzen |
| Responsive Regeln | `system/ui_responsive.py` | gehärtet | Werte aus generierten Tokens ableiten |
| UI-Abnahme | `system/ui_acceptance.py` | gehärtet | neue Komponenten in bestehende Messung aufnehmen |
| Launcherzustand und Viewmodelle | `system/launcher_controller.py` | geschützt | keine visuelle Zustandslogik zurück in den Launcher verschieben |
| Launcher-View | `system/launcher_gui.py` | Übergangs-View | ab Block 3 dünne Komponenten nutzen |
| Workspace-Geometrie | `system/workspace_geometry.py` | geschützt | keine Stylingverantwortung aufnehmen |
| Modul-Lifecycle | `system/module_lifecycle.py` | geschützt | keine Designlogik aufnehmen |
| Hauptfenster-View | `system/main_window.py` | Übergangs-View | ab Block 3 Komponenten nutzen |
| Task-Ausführung | `system/task_runner.py` | geschützt | visuelle Modernisierung darf Vertrag nicht verändern |
| Autosave/Backup/Shutdown | `system/session_lifecycle.py` | geschützt | visuelle Modernisierung darf Vertrag nicht verändern |
| Datei-Browsermodell | `modules/datei_manager/browser.py` | featurelokal | lokal behalten, bis Wiederverwendung belegt ist |
| Datei-Manager-View | `modules/datei_manager/window.py` | featurelokal | Block 7 visuell modernisieren |

---

## 4. Duplikatinventar

### 4.1 DUP-001 – Themefarben

**Schwere:** hoch

Aktuelle Quellen:

- `config/design-tokens.json`
- `config/launcher_gui.json`
- `config/datei_manager.json`

Risiko:

- Farbänderungen können auseinanderlaufen.
- Kontrastkorrekturen müssen mehrfach gepflegt werden.
- Themebezeichnungen und Farblogik besitzen unterschiedliche Strukturen.

Entscheidung:

- Block 2 erzeugt einen Python-kompatiblen Runtime-Tokenvertrag.
- `config/launcher_gui.json` behält nur launcherbezogene Verhaltenseinstellungen und notwendige Kompatibilitätsdaten.
- `config/datei_manager.json` behält Modulaktionen, Hinweise und Datenpfade.

### 4.2 DUP-002 – Abstände und Widgetmetriken

**Schwere:** hoch

Aktuelle Quellen:

- zentrale `spacing`- und `layout`-Tokens,
- `config/launcher_gui.json` mit `gap_*`, Button- und Feldmetriken,
- harte Werte in `system/main_window.py`,
- harte Werte in `modules/datei_manager/window.py`.

Entscheidung:

- Block 2 führt eine eindeutige Tk-Metrikabbildung ein.
- Block 3 ersetzt wiederholte direkte Konfigurationen durch minimale gemeinsame Helfer.

### 4.3 DUP-003 – Typografie

**Schwere:** hoch

Beispiele:

- zentrale Typografie-Tokens,
- `Arial`-Fontobjekte im Launcher,
- `TkDefaultFont` im Datei-Manager,
- lokale Größen und Gewichtungen in einzelnen Fenstern.

Entscheidung:

- Block 2 erzeugt eine Tk-kompatible Typografieabbildung.
- Plattformverfügbare Fallbacks bleiben erforderlich.
- Keine Schriftdateien werden in das Projekt aufgenommen oder verteilt.

### 4.4 DUP-004 – Buttonkonfiguration

**Schwere:** hoch

Befund:

- Der Launcher wiederholt Buttonfont, `padx`, `pady`, Mindestbreite, Fokus und Unterstreichung an vielen Stellen.
- Das Hauptfenster definiert eigene Mindestpolsterung.
- Der Datei-Manager verwendet eine separate ttk-Buttondarstellung.

Entscheidung:

- Block 3 definiert maximal vier semantische Buttontypen.
- Commands und Lifecycle bleiben im jeweiligen Fenster.
- Gemeinsame Helfer konfigurieren nur Darstellung, Fokus und Zustände.

### 4.5 DUP-005 – Panel-, Karten- und Flächenstil

**Schwere:** mittel

Befund:

- Launcher nutzt `LabelFrame`-Sektionen.
- Hauptfenster besitzt eigene Modulkarten.
- Datei-Manager nutzt ttk-Frames und eine hart gefärbte Canvas-Fläche.
- Der Themeadapter kennt bisher primär Standardwidgets und Modulkarten.

Entscheidung:

- bestehenden Themeadapter erweitern,
- nur wenige gemeinsame Komponenten einführen,
- keine Canvas-Sonderlösung für jedes Widget.

### 4.6 DUP-006 – Statusdarstellung

**Schwere:** mittel

Fachliche Zustände liegen korrekt getrennt in:

- `launcher_controller.py`,
- `module_lifecycle.py`,
- Task- und Session-Lifecycle.

Die visuelle Darstellung ist jedoch noch uneinheitlich, insbesondere im Datei-Manager.

Entscheidung:

- nur visuelle Statustokens und gemeinsame Darstellungsregeln teilen,
- fachliche Statusmodelle nicht zusammenführen.

### 4.7 DUP-007 – Breakpoints und Mindestgrößen

**Schwere:** hoch

Aktuelle Quellen:

- `config/design-tokens.json`,
- `system/ui_responsive.py`,
- Launcher-Mindestgröße,
- Datei-Manager-Geometrie und Mindestgröße.

Entscheidung:

- Block 2 leitet Pythonwerte aus Design-Tokens ab.
- Fensterspezifische Mindestgrößen dürfen als semantische Ableitung bestehen, nicht als unabhängige Designquelle.

### 4.8 DUP-008 – Icons und Aktionsbeschriftungen

**Schwere:** mittel

Entscheidung:

- nur übergreifende Aktionssemantik zentralisieren,
- featurebezogene Icons lokal belassen,
- keine universelle Iconbibliothek ohne tatsächlichen Mehrfachnutzen aufbauen.

### 4.9 DUP-009 – Hilfe, Fokus und Tastatur

**Schwere:** mittel

Befund:

- Launcher besitzt Kontext-Hilfe, Tooltips und zentrale Shortcutdefinitionen.
- Hauptfenster besitzt eigene Fokus- und Interaktionslogik.
- Datei-Manager besitzt lokale Navigationsshortcuts.

Entscheidung:

- zunächst Verträge messen und testen,
- nur tatsächlich identisches Binding-/Fokusverhalten extrahieren,
- fachliche Shortcuts bleiben bei ihrem Fenster.

### 4.10 DUP-010 – Treeview und Bildvorschau

**Schwere:** Information, derzeit keine echte Duplikation

Aktuell existiert nur ein realer Verbraucher:

- Datei-Manager.

Entscheidung:

- Browser-, Sortier- und Vorschaulogik bleibt lokal.
- Ein gemeinsames Tabellen- oder Vorschaumodul wird erst nach einem zweiten produktiven Verbraucher erstellt.

---

## 5. Codesparsamkeitsregeln

### 5.1 Vor jeder neuen Komponente

Es ist in dieser Reihenfolge zu prüfen:

1. Bestehenden Eigentümer erweitern.
2. Bestehende reine Funktion parametrisieren.
3. Kleine lokale Hilfsfunktion verwenden.
4. Gemeinsame Komponente nur bei mindestens zwei realen Verbrauchern.
5. Zustandsbehaftete Klasse nur bei tatsächlichem Lebenszyklus oder eigenem Zustand.

### 5.2 Erlaubte Ein-Verbraucher-Ausnahmen

Eine Auslagerung bei nur einem Verbraucher ist erlaubt, wenn mindestens eines gilt:

- reine Logik ist unabhängig testbar,
- Sicherheits- oder Lifecyclegrenze,
- nachweisbare Reduktion einer hochriskanten Fensterklasse.

### 5.3 Verbotene Muster

- neue handgepflegte Tokenquelle,
- paralleler Themeadapter,
- Designwerte direkt in neuen Fensterklassen,
- neue Universalbasis ohne reale Verbraucher,
- Fachzustand aus Widgetzuständen ableiten,
- UI-Zugriff aus Worker-Threads,
- dekorative Animation ohne realen Prozesszustand,
- visuelle Änderung ohne Test- und Abnahmevertrag.

### 5.4 Qualitätskennzahlen je Block

Jeder Folgeblock dokumentiert:

- entfernte Duplikate,
- wiederverwendete Komponenten,
- neu entstandene Produktionszeilen,
- veränderte autoritative Quellen,
- erhaltene gehärtete Verträge,
- ausgeführte Regressionstests,
- gemessene UI-Profile.

---

## 6. Geschützte Verträge

Folgende Verantwortungen dürfen durch die UI-Modernisierung nicht still verändert werden:

- Berichtformatierung,
- Workspace-Geometrie und Kollisionsschutz,
- Themeauflösung,
- Task-Runner,
- Autosave, Backup und Shutdown,
- Autostart,
- Modulaktivierung und -deaktivierung,
- Close-Policy,
- Launcher-Controller,
- Refresh-Debounce,
- Undo/Redo,
- UI-Abnahmevertrag,
- Datei-Browser-, Sortier- und Vorschauvertrag.

Die vollständige Pfad-/Testzuordnung steht in `config/ui-governance.json`.

---

## 7. Nicht-Ziele

Block 1 und die folgende Modernisierung sind keine:

- Neuschreibung,
- Frameworkmigration,
- Webanwendung,
- native Mobil-App,
- Cloud- oder Synchronisationsfunktion,
- Bildbearbeitung,
- versteckte Dateikonvertierung,
- fachliche Änderung von Modul-, Task- oder Shutdownverträgen.

Mobile iPhone-/Tabletprofile bleiben bei Tkinter ausdrücklich Viewportsimulationen.

---

## 8. Zulässiger Block-1-Diff

Block 1 darf ausschließlich Governance-, Test-, Workflow- und Indexdateien ändern:

- `config/ui-governance.json`
- `system/validate_ui_governance.py`
- `tests/test_ui_governance.py`
- `.github/workflows/ui-modernization-block-1.yml`
- diese Struktur- und Härtungsdokumente
- `dateiindex/index.json`

Nicht zulässig sind in Block 1 insbesondere Änderungen an:

- `system/launcher_gui.py`
- `system/main_window.py`
- `system/ui_theme_adapter.py`
- `system/ui_responsive.py`
- `modules/datei_manager/window.py`
- `modules/datei_manager/browser.py`
- bestehenden Lifecycle- und Controllerdateien.

---

## 9. Abnahmekriterien

Block 1 ist abgeschlossen, wenn:

1. jede aktuelle Verantwortung genau einen Eigentümer besitzt,
2. `config/design-tokens.json` einzige handgepflegte Tokenquelle bleibt,
3. alle geschützten Verträge und Belegtests existieren,
4. jedes Duplikat eine konkrete Entscheidung und einen Zielblock besitzt,
5. bedingte Komponenten reale Verbraucher ausweisen,
6. keine verbotene Parallelquelle existiert,
7. keine visuelle Laufzeitdatei verändert wurde,
8. Design-Token-Ausgaben driftfrei sind,
9. Validator und Tests im read-only Workflow bestehen,
10. Block 2 als einziger nächster Schritt festgelegt ist.

---

## 10. Nächster zulässiger Block

**Block 2: zentrale Token-Laufzeitabbildung**

Ziel:

- deterministisches Python-Tokenartefakt erzeugen,
- Theme-, Typografie-, Abstands- und Breakpointwerte für Tkinter bereitstellen,
- noch keine großflächige sichtbare Migration,
- vorhandene Konfigurationen schrittweise auf die gemeinsame Quelle abbilden.
