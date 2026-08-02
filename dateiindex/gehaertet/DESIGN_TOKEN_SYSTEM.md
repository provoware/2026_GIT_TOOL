# Gehaertet: Design-Token-System

Stand: 3. August 2026

## Quelldateien

- `config/design-tokens.json`
- `system/generate_design_tokens.py`

## Schutzmassnahmen

- zentrale maschinenlesbare Token-Quelle
- Pruefung aller Pflichtgruppen
- Pruefung des Standard-Themes
- Pruefung verbindlicher Farbwerte pro Theme
- verstaendliche Fehlerausgabe bei fehlender oder ungueltiger Quelle
- deterministische Sortierung der erzeugten Werte
- klar gekennzeichnete generierte Dateien
- `--check`-Modus fuer fehlende oder veraltete Ausgaben
- getrennte Exitcodes fuer Drift und ungueltige Quelldaten

## Abgeleitete Dateien

- `generated/design-tokens.css`
- `generated/design-tokens-webmanifest.json`
- `generated/design-tokens-module-manifest.json`
- `docs/DESIGN_TOKENS.generated.md`

Diese Dateien sind generiert und duerfen nicht als fuehrende Quelle manuell bearbeitet werden.

## Pruefgrenze

Die Pruefung erfolgte als Quellcode-, Struktur- und Konsistenzpruefung ueber die GitHub-Schnittstelle. Eine direkte Programmausfuehrung war in der Connector-Umgebung nicht moeglich. Der erste lokale oder CI-Lauf muss mindestens ausfuehren:

```bash
python system/generate_design_tokens.py
python system/generate_design_tokens.py --check
```
