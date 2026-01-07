# Standards

## Zweck
Diese Datei ist die zentrale Quelle für verbindliche Regeln. Sie sorgt dafür, dass alle Module gleich aufgebaut sind und die Bedienung barrierefrei (Accessibility) bleibt.

## Ordnerstruktur (Pflicht)
- `src/`: Systemlogik (stabile Kernlogik, nicht benutzerspezifisch)
- `config/`: Konfiguration (änderbar ohne Code)
- `data/`: Variable Daten (Laufzeitdaten)
- `logs/`: Protokolle (Logs)
- `scripts/`: Start- und Prüfskripte

## Modul-Standard (Pflicht)
Jedes Modul muss einer festen Struktur folgen, damit der Launcher es automatisch laden kann.

### Modul-Ordner
- `modules/<modul-id>/`
  - `module.json` (Metadaten)
  - `index.js` oder `main.py` (Einstiegspunkt)
  - `README.md` (kurze Erklärung in einfacher Sprache)

### module.json (Minimalfelder)
```json
{
  "id": "beispiel-modul",
  "title": "Beispielmodul",
  "description": "Kurze Erklärung in einfacher Sprache (Plain Language).",
  "version": "1.0.0",
  "entry": "index.js",
  "group": "Beispiele",
  "order": 10,
  "enabled": true
}
```

### Einheitliche Schnittstelle (Init/Exit)
Jeder Einstiegspunkt muss diese Funktionen anbieten:
- `init(config, services)`  
  - **Aufgabe**: Startet das Modul.  
  - **Pflicht**: Eingaben validieren (Input-Validierung), klare Fehlermeldung, Rückgabewert prüfen.  
- `exit()`  
  - **Aufgabe**: Ressourcen sauber freigeben.  

**Rückgabe-Standard**:  
Ein Objekt mit klarer Status-Aussage, z. B. `{ "ok": true, "message": "Gestartet." }`.

## Bedienung & Barrierefreiheit (Pflicht)
- Tastaturbedienung vollständig möglich (Tab-Reihenfolge, Fokus sichtbar).
- Kontrast ausreichend (Text gut lesbar).
- Klare, kurze und deutsche UI-Texte.

## Fehlertexte (Pflicht)
- Laienverständlich, kurze Sätze, konkrete Hilfe.
- Beispiel: „Das Modul konnte nicht gestartet werden. Bitte prüfen Sie die Datei module.json.“

## Logging & Debugging (Pflicht)
- Jede Aktion erzeugt einen Logeintrag.
- Debug-Modus (Fehlersuche): zusätzliche Details, aber niemals sensible Daten.

## Tests & Formatierung (Pflicht)
- Automatische Tests für Kernfunktionen.
- Automatische Codeformatierung (Formatter).
