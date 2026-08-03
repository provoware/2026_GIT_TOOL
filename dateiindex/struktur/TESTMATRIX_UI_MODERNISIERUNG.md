# Testmatrix UI-Modernisierung

Stand: 2026-08-03  
Aktueller Status: **Block 2 abgeschlossen**

## 1. Blockfolge

| Block | Verantwortung | Produktionsmigration | Status |
| --- | --- | --- | --- |
| 1 | Governance, Verantwortlichkeiten, Duplikate, Nicht-Ziele | nein | abgeschlossen |
| 2 | deterministische Python-Tokenabbildung | nein | abgeschlossen |
| 3 | gemeinsame Tk-Komponenten und visuelle States | ja | nächster Schritt |
| 4 | Tabellenstandard bei erreichter Wiederverwendungsgrenze | bedingt | gesperrt |
| 5 | Vorschaukomponente bei erreichter Wiederverwendungsgrenze | bedingt | gesperrt |
| 7 | visuelle Modernisierung des Datei-Managers | ja | gesperrt |
| 8 | visuelle Modernisierung des Launchers | ja | gesperrt |
| 9 | visuelle Modernisierung des Hauptfensters | ja | gesperrt |
| 10 | vollständige UI-, Responsive- und Accessibility-Abnahme | nein | gesperrt |

## 2. Block-1-Prüfungen

| ID | Prüfung | Ergebnis |
| --- | --- | --- |
| GOV-001 | Governance-JSON vollständig und valide | grün |
| GOV-002 | eindeutige Verantwortungseigentümer | grün |
| GOV-003 | einzige handgepflegte Tokenquelle | `config/design-tokens.json` |
| GOV-004 | keine verbotene Parallelquelle | grün |
| GOV-005 | geschützte Dateien und Belegtests vorhanden | grün |
| GOV-006 | Duplikatinventar vollständig | grün |
| GOV-007 | Wiederverwendungsgrenze | grün |
| GOV-008 | lokale Treeview-/Previewgrenze | grün |
| GOV-009 | Block-1-Diff-Sperre | grün |
| GOV-010 | Design-Token-Drift | grün |

## 3. Block-2-Prüfungen

| ID | Prüfung | Beleg | Ergebnis |
| --- | --- | --- | --- |
| TOK-001 | Runtime-Daten deterministisch | `test_runtime_data_converts_supported_units_deterministically` | grün |
| TOK-002 | Pythonquelle syntaktisch gültig | AST + `py_compile` | grün |
| TOK-003 | regulärer Import | Workflowimport | grün |
| TOK-004 | tiefe Unveränderlichkeit | MappingProxy-Negativtests | grün |
| TOK-005 | Standardthemeauflösung | `get_theme()` | grün |
| TOK-006 | unbekanntes Theme | `KeyError` | grün |
| TOK-007 | falscher Themetyp | `TypeError` | grün |
| TOK-008 | `rem`-Umrechnung | 16-Pixel-Basis | grün |
| TOK-009 | `px`-Umrechnung | direkte Ganzzahl | grün |
| TOK-010 | `ms`-Umrechnung | direkte Ganzzahl | grün |
| TOK-011 | unbekannte Einheit | früher Abbruch | grün |
| TOK-012 | nicht ganzzahlige Pixel | früher Abbruch | grün |
| TOK-013 | ungültige Millisekunden | früher Abbruch | grün |
| TOK-014 | Eingabedaten unverändert | Deep-Copy-Vergleich | grün |
| TOK-015 | generierte Datei entspricht Generator | Bytevergleich | grün |
| TOK-016 | bisherige Generatorausgaben driftfrei | `--check` | grün |
| TOK-017 | Block-2-Diff-Sperre | Governance-Validator | grün |
| TOK-018 | Repository-Sauberkeit | `git diff --exit-code` | grün |

## 4. Negativtests

| Fall | Erwarteter Schutz |
| --- | --- |
| doppelte Verantwortung | Validator bricht ab |
| fehlende Evidence-Datei | Validator bricht ab |
| vorhandenes `system/ui_tokens.py` | Validator bricht ab |
| vorhandenes `generated/design-tokens.py` | Validator bricht ab |
| nächster Block ungleich 3 | Validator bricht ab |
| nicht definierter Block-Diff | Validator bricht ab |
| Änderung an `system/launcher_gui.py` in Block 2 | Diff-Prüfung bricht ab |
| Änderung an `system/main_window.py` in Block 2 | Diff-Prüfung bricht ab |
| Änderung an `modules/datei_manager/window.py` in Block 2 | Diff-Prüfung bricht ab |

## 5. Ab Block 3 erforderliche Regressionen

Sobald produktive UI-Pfade migriert werden, sind abhängig vom Scope erneut auszuführen:

- Gate 1: Launcher-Berichte
- Gate 2: Workspace-Geometrie
- Gate 3: Themeadapter
- Gate 4: Task-Runner
- Gate 5: Session-Lifecycle und Safe-Mode
- Gate 6: Modul-Lifecycle und Close-Policy
- Gate 7: Launcher-Controller
- UI-Acceptance unter Xvfb
- Datei-Manager-Vorschau und Sortierung
- Token-Runtime und Governance

## 6. Stop-Regel

Ein Folgeblock darf erst beginnen, wenn:

- sein Vorgänger vollständig grün ist,
- der tatsächliche Diff der vorgesehenen Verantwortung entspricht,
- keine unerklärte Regression verbleibt,
- alle Workflows `contents: read` verwenden,
- Dateiindex und Härtungsnachweis aktualisiert sind.
