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
- **Modulnamen**: Modul-IDs sind `snake_case` (z. B. `datei_suche`) und entsprechen dem Ordnernamen.
- **Trennung der Bereiche**:
  - `src/` und `system/` = Systemlogik.
  - `config/` = Konfiguration.
  - `data/` und `logs/` = variable Daten/Protokolle.
- **Start-Modi**:
  - Safe-Mode = nur prüfen, nichts schreiben.
  - Ghost-Mode = Alias für Safe-Mode (Testmodus ohne Schreiben).
  - Sandbox = isolierte Kopie, Änderungen bleiben dort.
- **Validierung**: Jede Funktion prüft Eingabe und Ausgabe (Input/Output = Ein-/Ausgabe).
- **Logging**: Einheitliches Format, keine blockierenden UI-Aktionen.
- **Keine Überschreibungen**: Dateien nie unbemerkt überschreiben.
- **Modul-Standard**: Module folgen der gemeinsamen Schnittstelle (init/run/exit/validateInput/validateOutput).
- **Fehlerhandling**: Meldungen haben **Ursache + Lösungsschritt** und verweisen auf Logs.

## UI-Layout (Abstände & Führung)
- **Abstands-Raster**: nutze `layout.*` aus `config/launcher_gui.json`.
- **Konsistente Buttons**: gleiche Innenabstände (`button_padx`, `button_pady`).
- **Lesbarkeit**: klare Überschriften, gruppierte Bereiche, ausreichend Weißraum.

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
