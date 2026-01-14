# Styleguide (PEP8 + Projektregeln)

## Zweck
Dieser Styleguide erklärt die wichtigsten Regeln für sauberen, wartbaren Code.
Er ergänzt die Projekt-Standards in `standards.md`.

## PEP8 (Python-Standard, kurz erklärt)
- **Einrückung**: 4 Leerzeichen, keine Tabs.
- **Zeilenlänge**: max. 88 Zeichen (passt zu Black).
- **Namen**:
  - Funktionen/Variablen: `snake_case` (z. B. `lade_daten`).
  - Klassen: `PascalCase` (z. B. `ModuleChecker`).
  - Konstanten: `UPPER_CASE` (z. B. `MAX_RETRIES`).
- **Imports**: Standardbibliothek, externe Pakete, Projekt-Module getrennt gruppieren.
- **Leerzeilen**: 2 Leerzeilen zwischen Top-Level-Funktionen/Klassen.
- **Kommentare**: kurz, klar, erklären den „Warum“-Grund.

## Projektregeln (verbindlich)
- **Einfache Sprache**: Fehler- und Hilfetexte sind Deutsch und laienverständlich.
- **Barrierefreiheit**: Tastaturbedienung, klarer Kontrast, eindeutige Buttons.
- **Trennung der Bereiche**:
  - `src/` und `system/` = Systemlogik.
  - `config/` = Konfiguration.
  - `data/` und `logs/` = variable Daten/Protokolle.
- **Validierung**: Jede Funktion prüft Eingabe und Ausgabe (Input/Output = Ein-/Ausgabe).
- **Logging**: Einheitliches Format, keine blockierenden UI-Aktionen.
- **Keine Überschreibungen**: Dateien nie unbemerkt überschreiben.
- **Modul-Standard**: Module folgen der gemeinsamen Schnittstelle (init/run/exit/validateInput/validateOutput).

## Qualitätssicherung (automatisch)
- **Formatter**: Black (Formatierer = automatische Vereinheitlichung).
- **Linting**: Ruff (Stilprüfung = automatische Regelkontrolle).
- **Tests**: Pytest (Test-Runner = automatische Funktionsprüfung).

## Beispiele
```python
# gut: klare Namen, kurze Funktion

def lade_daten(pfad: str) -> str:
    """Liest eine Datei und gibt den Text zurück."""
    with open(pfad, "r", encoding="utf-8") as datei:
        return datei.read()
```

```python
# schlecht: unklare Namen, kein Typ

def ld(p):
    return open(p).read()
```
