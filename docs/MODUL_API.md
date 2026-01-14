# MODUL_API (Schnittstellen, Events, States)

## Ziel (einfach erklärt)
Diese Datei beschreibt, **wie ein Modul aufgebaut sein muss**, damit es zentral über die Registry geladen werden kann.
Alle Begriffe sind in einfacher Sprache erklärt (Fachbegriff in Klammern).

## Pflicht-Dateien pro Modul
- `manifest.json` (Manifest = Steckbrief des Moduls)
- `module.py` (Entry = Startdatei des Moduls)

### Beispiel: manifest.json
```json
{
  "id": "beispiel_modul",
  "name": "Beispiel-Modul",
  "version": "1.0.0",
  "entry": "module.py"
}
```
**Tipp:** `id` muss eindeutig sein, sonst blockiert der Modul-Check.

## Modul-API (Schnittstellen)
Ein Modul muss diese Funktionen anbieten (mindestens `run`).

### 1) init(context) – optional
- **Zweck:** Initialisierung (Vorbereitung).
- **Input:** `context` (Kontext = gemeinsamer Zustand).
- **Output:** optionaler Kontext.

**Tipp:** Nutze `init`, um z. B. Logger einzurichten.

### 2) run(input_data) – Pflicht
- **Zweck:** Führt die Hauptaktion aus.
- **Input:** `input_data` (Eingaben = Daten für die Aktion).
- **Output:** `dict` mit Status und Daten.

**Erwartetes Ausgabeformat (einfach):**
```json
{
  "status": "ok",
  "message": "Kurzmeldung in einfacher Sprache",
  "data": {"result": "..."},
  "ui": {"title": "..."}
}
```
**Tipp:** Gib immer `status`, `message` und **mindestens** `data` oder `ui` zurück.

### 3) exit(context) – optional
- **Zweck:** Aufräumen (z. B. Dateien schließen).
- **Input:** `context`.
- **Output:** optionaler Kontext.

**Tipp:** `exit` sollte nie still fehlschlagen – klare Fehlermeldung nutzen.

## Events (Ereignisse)
Module können folgende Ereignisse nutzen (Events = kleine Zustandswechsel):
- `start`: Modul wurde gestartet.
- `validate`: Eingaben wurden geprüft.
- `run`: Hauptaktion läuft.
- `finish`: Modul ist fertig.
- `error`: Fehler ist aufgetreten.

**Tipp:** Schreibe Ereignisse ins Log, damit Fehler schneller gefunden werden.

## States (Zustände)
Standard-Zustände (States = Status):
- `ok` (alles gut)
- `warn` (Hinweis, aber kein Abbruch)
- `error` (Fehler mit Lösungsschritt)

**Tipp:** Nutze `warn`, wenn Nutzer:innen noch selbst korrigieren können.

## Validierung (Input/Output prüfen)
- **Input prüfen:** Typen, Pflichtfelder, leere Werte.
- **Output prüfen:** `status`, `message`, `data/ui` vorhanden.

**Tipp:** Fehlertexte **immer** in einfacher Sprache schreiben und einen nächsten Schritt nennen.

## Beispiel-Modul (minimal, laienfreundlich)
```python
# module.py
from typing import Any, Dict

class ModuleError(ValueError):
    pass


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(input_data, dict):
        raise ModuleError("Eingabe fehlt oder ist kein Objekt (dict).")
    text = str(input_data.get("text", "")).strip()
    if not text:
        raise ModuleError("Eingabe-Feld 'text' ist leer.")
    return {
        "status": "ok",
        "message": "Text wurde verarbeitet.",
        "data": {"result": text.upper()},
    }
```
**Tipp:** Halte die Ausgabe stabil – das macht Tests und GUI-Anzeige zuverlässig.
