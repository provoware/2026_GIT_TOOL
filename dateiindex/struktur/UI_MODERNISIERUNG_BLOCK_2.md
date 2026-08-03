# UI-Modernisierung – Block 2: zentrale Token-Laufzeitabbildung

Stand: 2026-08-03  
Status: **abgeschlossen**  
Sichtbare Produktionsmigration: **nein**

## 1. Ziel

Block 2 macht die bestehende autoritative Quelle `config/design-tokens.json` direkt und sicher für Python-/Tkinter-Code nutzbar, ohne eine zweite handgepflegte Tokenquelle einzuführen.

Das neue Artefakt lautet:

```text
generated/design_tokens.py
```

Die Unterstrich-Schreibweise ist bewusst gewählt, damit das Artefakt regulär importiert werden kann:

```python
from generated import design_tokens
```

Die frühere Planbezeichnung `generated/design-tokens.py` wurde verworfen und als verbotene Parallelquelle registriert.

## 2. Erzeugte Runtimegruppen

Das generierte Modul stellt tief unveränderlich bereit:

- `THEMES`
- `SPACING_PX`
- `RADIUS_PX`
- `FONT_FAMILY`
- `FONT_SIZE_PX`
- `FONT_WEIGHT`
- `LINE_HEIGHT`
- `SHADOW`
- `MOTION_MS`
- `Z_INDEX`
- `BREAKPOINT_PX`
- `LAYOUT_PX`
- `TOKENS`

Zusätzlich:

- `DEFAULT_THEME`
- `theme_names()`
- `get_theme(name)`

## 3. Einheitenvertrag

| Quelle | Runtime |
| --- | --- |
| `0.25rem` | `4` Pixel |
| `1rem` | `16` Pixel |
| `44px` | `44` Pixel |
| `200ms` | `200` Millisekunden |

Der Generator verwendet eine feste Runtimebasis von 16 Pixeln pro `rem`.

Nicht unterstützt werden:

- unbekannte Einheiten wie `em`, `%` oder `vh`,
- negative Werte,
- Werte, die keine ganzzahligen Runtimepixel ergeben,
- nicht ganzzahlige Millisekunden.

Solche Werte brechen die Erzeugung mit einer konkreten Fehlermeldung ab.

## 4. Unveränderlichkeit

Das generierte Modul verwendet rekursiv `MappingProxyType`. Dadurch sind auch verschachtelte Themefarben und Metrikgruppen nicht veränderbar.

Die Anwendung kann Token lesen, aber nicht zur Laufzeit überschreiben. Änderungen müssen immer über `config/design-tokens.json` und den Generator erfolgen.

## 5. Verhaltenserhalt

Die bisherigen Ausgaben bleiben weiterhin Bestandteil derselben Driftprüfung:

- `generated/design-tokens.css`
- `generated/design-tokens-webmanifest.json`
- `generated/design-tokens-module-manifest.json`
- `docs/DESIGN_TOKENS.generated.md`

Block 2 ergänzt nur das Python-Artefakt. Es verändert keine vorhandene Oberfläche und keine bestehende generierte Darstellung.

## 6. Nicht veränderte Dateien

Insbesondere unverändert bleiben:

- `system/launcher_gui.py`
- `system/main_window.py`
- `modules/datei_manager/window.py`
- `system/ui_theme_adapter.py`
- `system/ui_responsive.py`
- alle Controller-, Task-, Lifecycle- und Close-Policy-Dateien.

## 7. Prüfungen

Automatisiert geprüft werden:

1. deterministische Runtime-Daten,
2. korrekte Pixel- und Millisekundenwerte,
3. gültige Python-Syntax,
4. regulärer Modulimport,
5. tiefe Unveränderlichkeit,
6. Themeauflösung,
7. unbekannte Themefehler,
8. ungültige Typen,
9. unbekannte Einheiten,
10. nicht ganzzahlige Pixelwerte,
11. nicht ganzzahlige Millisekunden,
12. unveränderte Eingabedaten,
13. vollständige Generator-Driftprüfung,
14. Block-2-Diff-Whitelist,
15. Repository-Sauberkeit.

## 8. Governance-Fortschritt

`generated/design_tokens.py` ist nun die autoritative generierte Python-Runtimequelle.

Weiterhin verboten sind:

- `system/ui_tokens.py`
- `config/ui-tokens.json`
- `config/design_tokens_runtime.json`
- `modules/datei_manager/ui_tokens.py`
- `generated/design-tokens.py`

## 9. Nächster zulässiger Block

**Block 3: gemeinsame Tk-Komponenten und visuelle Zustände**

Block 3 darf erstmals produktive UI-Darstellung migrieren. Er muss:

- die generierten Runtimewerte konsumieren,
- den vorhandenen Themeadapter erweitern statt ersetzen,
- Button-, Panel-, Karten- und Statusdarstellung zentralisieren,
- Commands, Controller und Lifecycleverträge unverändert lassen,
- vor jeder Migration Sicherungstests ergänzen.
