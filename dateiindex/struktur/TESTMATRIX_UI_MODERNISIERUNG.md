# Testmatrix UI-Modernisierung

Stand: 2026-08-03  
Aktueller Status: **Block 1 in Prüfung**

## 1. Blockfolge

| Block | Verantwortung | Produktionsmigration | Status |
| --- | --- | --- | --- |
| 1 | Governance, Verantwortlichkeiten, Duplikate, Nicht-Ziele | nein | in Prüfung |
| 2 | deterministische Python-Tokenabbildung | nein | nächster Schritt |
| 3 | gemeinsame Tk-Komponenten und visuelle States | ja | gesperrt |
| 4 | Tabellenstandard bei erreichter Wiederverwendungsgrenze | bedingt | gesperrt |
| 5 | Vorschaukomponente bei erreichter Wiederverwendungsgrenze | bedingt | gesperrt |
| 7 | visuelle Modernisierung des Datei-Managers | ja | gesperrt |
| 8 | visuelle Modernisierung des Launchers | ja | gesperrt |
| 9 | visuelle Modernisierung des Hauptfensters | ja | gesperrt |
| 10 | vollständige UI-, Responsive- und Accessibility-Abnahme | nein | gesperrt |

## 2. Block-1-Prüfungen

| ID | Prüfung | Beleg | Erwartung |
| --- | --- | --- | --- |
| GOV-001 | Governance-JSON vollständig und valide | `validate_policy` | grün |
| GOV-002 | eindeutige Verantwortungseigentümer | `tests/test_ui_governance.py` | keine doppelte Verantwortung |
| GOV-003 | einzige handgepflegte Tokenquelle | Governance-Test | `config/design-tokens.json` |
| GOV-004 | keine verbotene Parallelquelle | Governance-Test | kein `system/ui_tokens.py` |
| GOV-005 | geschützte Dateien vorhanden | Governance-Test | alle Pfade vorhanden |
| GOV-006 | Belegtests vorhanden | Governance-Test | alle Evidence-Pfade vorhanden |
| GOV-007 | Duplikatinventar vollständig | Governance- und Quellbaumtest | definierte Kernthemen vorhanden |
| GOV-008 | Extraktionsschwelle | Governance-Test | mindestens zwei reale Verbraucher |
| GOV-009 | lokale Treeview-/Previewgrenze | Governance-Test | kein vorschnelles Shared-Modul |
| GOV-010 | Migrationsreihenfolge | Governance-Test | nächster Block = 2 |
| GOV-011 | zulässiger Dateidiff | Validator + Git-Diff | keine Laufzeit-UI-Datei geändert |
| GOV-012 | Design-Token-Drift | `generate_design_tokens.py --check` | keine Drift |
| GOV-013 | Python-Syntax | `py_compile` | gültig |
| GOV-014 | Repository-Sauberkeit | `git diff --exit-code` | unverändert nach Tests |

## 3. Negativtests

| Fall | Erwarteter Schutz |
| --- | --- |
| doppelte Verantwortung | Validator bricht ab |
| fehlende Evidence-Datei | Validator bricht ab |
| vorhandenes `system/ui_tokens.py` | Validator bricht ab |
| nächster Block ungleich 2 | Validator bricht ab |
| Änderung an `system/launcher_gui.py` in Block 1 | Diff-Prüfung bricht ab |
| Änderung an `modules/datei_manager/window.py` in Block 1 | Diff-Prüfung bricht ab |

## 4. Weiterhin erforderliche Regressionen ab Block 2

Sobald produktive UI-/Tokenpfade verändert werden, sind abhängig vom Scope erneut auszuführen:

- Gate 1: Launcher-Berichte
- Gate 2: Workspace-Geometrie
- Gate 3: Themeadapter
- Gate 4: Task-Runner
- Gate 5: Session-Lifecycle und Safe-Mode
- Gate 6: Modul-Lifecycle und Close-Policy
- Gate 7: Launcher-Controller
- UI-Acceptance unter Xvfb
- Datei-Manager-Vorschau und Sortierung

## 5. Stop-Regel

Ein Folgeblock darf erst beginnen, wenn:

- sein Vorgänger vollständig grün ist,
- der tatsächliche Diff der vorgesehenen Verantwortung entspricht,
- keine unerklärte Regression verbleibt,
- Workflowrechte wieder auf `contents: read` stehen,
- Dateiindex und Härtungsnachweis aktualisiert sind.
