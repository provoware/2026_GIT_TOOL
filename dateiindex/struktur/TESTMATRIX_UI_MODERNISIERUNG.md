# Testmatrix UI-Modernisierung

Stand: 2026-08-04  
Aktueller Status: **Block 3 in Abschlussprüfung**

## 1. Blockfolge

| Block | Verantwortung | Produktionsmigration | Status |
| --- | --- | --- | --- |
| 1 | Governance, Verantwortlichkeiten, Duplikate, Nicht-Ziele | nein | abgeschlossen |
| 2 | deterministische Python-Tokenabbildung | nein | abgeschlossen |
| 3 | gemeinsame Tk-Komponenten und visuelle Zustände | begrenzt | in Abschlussprüfung |
| 4 | Tabellenstandard bei erreichter Wiederverwendungsgrenze | bedingt | nächster Schritt |
| 5 | Vorschaukomponente bei erreichter Wiederverwendungsgrenze | bedingt | gesperrt |
| 7 | visuelle Modernisierung des Datei-Managers | ja | gesperrt |
| 8 | visuelle Modernisierung des Launchers | ja | gesperrt |
| 9 | visuelle Modernisierung des Hauptfensters | ja | gesperrt |
| 10 | vollständige UI-, Responsive- und Accessibility-Abnahme | nein | gesperrt |

## 2. Abgeschlossene Grundlagen

| Bereich | Nachweis | Status |
| --- | --- | --- |
| Block-1-Governance | Eigentümer, Duplikate, Nicht-Ziele, Diff-Sperre | grün |
| Block-2-Tokenruntime | Generatorgleichheit, Import, Deep-Readonly, Einheiten | grün |
| einzige Tokenquelle | `config/design-tokens.json` | grün |
| keine Parallelquellen | Governance-Negativtests | grün |

## 3. Block-3-Komponentenprüfungen

| ID | Prüfung | Beleg | Erwartung |
| --- | --- | --- | --- |
| CMP-001 | Metriken aus generierter Runtime | `test_metrics_are_loaded_from_generated_runtime` | konkrete Pixel-/Millisekundenwerte |
| CMP-002 | Legacy-Theme auf semantische Palette | `test_legacy_theme_is_mapped_to_semantic_palette` | kompatible Farbzuordnung |
| CMP-003 | deterministische Farbmischung | `test_color_mixing_and_contrast_are_deterministic` | stabile Hexwerte |
| CMP-004 | Primär/Sekundär/Neutral/Gefahr unterscheidbar | `test_button_roles_produce_distinct_visual_contracts` | getrennte Rollen |
| CMP-005 | Hoverzustand unterscheidbar | Primärbutton-Test | nicht identisch zum Normalzustand |
| CMP-006 | Eventbindungen idempotent | `test_button_registration_applies_metrics_and_binds_states_once` | eine Bindung pro Ereignis |
| CMP-007 | Disabled blockiert Hover/Active | `test_disabled_button_never_switches_to_hover_or_active_palette` | Disabled-Palette bleibt aktiv |
| CMP-008 | Panel-, Karten- und Statusvertrag rein testbar | Surface-/Status-Tests | kein Tk-Root erforderlich |
| CMP-009 | registrierter Komponentenbaum | `test_component_tree_styles_registered_surfaces_buttons_and_status` | Rollen werden rekursiv angewandt |
| CMP-010 | Status verändert keinen Fachtext | `test_status_widget_preserves_domain_text_and_only_changes_visuals` | Text bleibt erhalten |
| CMP-011 | ungültige Rollen brechen früh ab | Negativtests | keine Teilmutation |

## 4. Theme- und Integrationsprüfungen

| ID | Prüfung | Erwartung |
| --- | --- | --- |
| INT-001 | Themeauflösung bleibt unveränderlich | bestehender Gate-3-Vertrag grün |
| INT-002 | Tooltip und Menü bleiben kompatibel | bestehende Tests grün |
| INT-003 | registrierte Primärrolle wird rekursiv verwendet | grün |
| INT-004 | Panel erhält gemeinsame Fläche und Kontur | grün |
| INT-005 | Modulkartenfläche erhält Tiefenstufe | grün |
| INT-006 | Aktivieren = Primäraktion | grün |
| INT-007 | Deaktivieren = Gefahraktion | grün |
| INT-008 | Launcherstatus nutzt Symbol und gemeinsame Palette | Codemod-/Runtimebeleg grün |
| INT-009 | Launcher-Controllertext und Cursor bleiben erhalten | Quellvertrag grün |
| INT-010 | ModuleManager und Close-Policy bleiben erhalten | Gate 6 grün |
| INT-011 | Workspace-Geometrie bleibt erhalten | Gate 2 grün |
| INT-012 | TaskRunner und Shutdown bleiben erhalten | Gates 4 und 5 grün |

## 5. Codemod- und Governanceprüfungen

| ID | Prüfung | Erwartung |
| --- | --- | --- |
| MOD-001 | integrierter Codemod idempotent | keine zweite Änderung |
| MOD-002 | `--check` akzeptiert Endstand | Exitcode 0 |
| MOD-003 | unvollständige Integration wird erkannt | geänderter Pfad wird gemeldet |
| GOV-301 | `system/ui_components.py` ist eindeutiger Eigentümer | grün |
| GOV-302 | begrenzte visuelle Migration ist ausdrücklich erlaubt | `visual_runtime_migration_scoped=true` |
| GOV-303 | parallele Komponentenquelle verboten | Negativtest grün |
| GOV-304 | Block-3-Diff-Whitelist | nur definierte Dateien |
| GOV-305 | Datei-Manager bleibt außerhalb Block 3 | Änderung wird abgelehnt |
| GOV-306 | nächster Block = 4 | grün |

## 6. Laufzeit- und Regressionsabnahme

Vor Merge erforderlich:

- UI Modernization Block 3 Components
- UI Modernization Governance
- Gate 3 UI Theme Adapter
- Gate 1 Launcher Reports, sofern ausgelöst
- Gate 2 Workspace Geometry, sofern ausgelöst
- Gate 4 Task Runner, sofern ausgelöst
- Gate 5 Session Lifecycle, sofern ausgelöst
- Gate 6 Module Lifecycle, sofern ausgelöst
- Gate 7 Launcher Controller, sofern ausgelöst
- UI Acceptance Linux and Mobile Viewports
- Python-Kompilierung
- Design-Token-Drift
- Repository-Sauberkeit

## 7. Stop-Regel

Block 4 darf erst beginnen, wenn:

- Block-3-Workflow dauerhaft `contents: read` verwendet,
- alle ausgelösten Regressionen grün sind,
- der tatsächliche Diff der Block-3-Whitelist entspricht,
- keine unerklärte UI-Abweichung verbleibt,
- Dateiindex und Härtungsnachweis aktuell sind.
