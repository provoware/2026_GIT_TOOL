# Härtungsnachweis – UI-Modernisierung Block 2

Stand: 2026-08-03

## Status

Block 2 ist abgeschlossen. Die zentrale JSON-Tokenquelle besitzt nun eine deterministische, importierbare und tief unveränderliche Python-Laufzeitabbildung.

## Gehärtete Artefakte

### `system/generate_design_tokens.py`

Zusätzlich gehärtet für:

- explizite `rem`-/`px`-Umrechnung,
- explizite Millisekundenwerte,
- ganzzahlige Runtimegrößen,
- nichtnegative Z-Ebenen einschließlich `base = 0`,
- deterministische Python-Quelltexterzeugung,
- gemeinsame Driftprüfung aller fünf Ausgaben.

### `generated/design_tokens.py`

Eigenschaften:

- regulär importierbar,
- automatisch erzeugt,
- nicht handzupflegen,
- rekursiv unveränderlich,
- klar benannte semantische Gruppen,
- definierte Standardthemeauflösung,
- frühe Fehler für unbekannte Themes und falsche Argumenttypen.

### `tests/test_design_token_runtime.py`

Sichert:

- konkrete Runtimewerte,
- deterministische Ausgabe,
- gültige Syntax und Import,
- tiefe Unveränderlichkeit,
- Generatorgleichheit,
- korrekten Ausgabepfad,
- unbekannte Einheiten,
- nicht ganzzahlige Pixelwerte,
- ungültige Millisekunden,
- unveränderte Eingabedaten.

### Governance

Der Governance-Validator unterstützt nun blockabhängige Whitelists. Block 2 darf keine produktiven UI-Dateien verändern.

## Unveränderte Produktionsverträge

- Themeadapter
- Responsive-Regeln
- Launcher-Controller
- Launcher-View
- Hauptfenster
- Datei-Manager-View
- Workspace-Geometrie
- Task-Runner
- Session-Lifecycle
- Modul-Lifecycle
- Close-Policy
- Safe-Mode

## Sicherheits- und Qualitätsgrenzen

- keine zweite handgepflegte Tokenquelle,
- keine veränderbaren globalen Runtime-Dictionaries,
- keine stillen Einheitenannahmen außer der dokumentierten 16-Pixel-`rem`-Basis,
- keine visuellen Änderungen in Block 2,
- keine Workflow-Schreibrechte,
- keine neue externe Abhängigkeit.

## Prüfbelege

- Governance-Gate: erfolgreich
- Token-Runtime-Gate: erfolgreich
- Generator `--check`: erfolgreich
- regulärer Import: erfolgreich
- Python-Kompilierung: erfolgreich
- Block-2-Diff-Sperre: erfolgreich
- Repository-Sauberkeit: erfolgreich

## Nächster zulässiger Schritt

**Block 3: gemeinsame Tk-Komponenten und visuelle Zustände**
