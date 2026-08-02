# Dateiindex

Dieses Verzeichnis dokumentiert die Projektstruktur, zentrale Einstiegspunkte, Härtungskandidaten und bereits gehärtete Dateien.

## Zweck

- wichtige Dateien schnell auffindbar machen
- große oder risikoreiche Dateien vor Refaktorierungen erfassen
- Härtungsstatus nachvollziehbar dokumentieren
- geprüfte Kernbestandteile von bloßen Kandidaten unterscheiden

## Ordner

- `struktur/`: lesbare Projekt- und Einstiegspunktübersichten
- `kandidaten/`: Dateien, die noch geprüft, gehärtet oder zerlegt werden müssen
- `gehaertet/`: Register bereits gehärteter Dateien
- `index.json`: maschinenlesbares Gesamtregister

## Statuswerte

- `entdeckt`: Datei wurde erfasst, aber noch nicht vertieft geprüft
- `kandidat`: Datei ist für Härtung oder Refaktorierung vorgesehen
- `in_pruefung`: Prüfung läuft
- `gehaertet`: definierte Prüfungen und Schutzmaßnahmen sind dokumentiert abgeschlossen
- `generiert`: automatisch erzeugte Datei; Quelle statt Ausgabe bearbeiten
- `historisch`: Altbestand, der nicht ungeprüft in die Zielarchitektur übernommen werden darf

## Aufnahmeregel für gehärtete Dateien

Eine Datei wird erst unter `gehaertet/` registriert, wenn mindestens Folgendes dokumentiert ist:

1. Zweck und Verantwortlichkeit sind eindeutig.
2. Eingaben und Fehlerfälle werden geprüft.
3. Abhängigkeiten und Seiteneffekte sind bekannt.
4. Relevante Tests oder statische Prüfungen sind benannt.
5. Die Datei enthält keine ungeklärten kritischen Befunde.
6. Datum, Prüfumfang und verbleibende Grenzen sind eingetragen.

Generierte Dateien werden nicht als eigenständig gehärtete Quellen geführt. Ihre Generator- und Quelldateien werden geprüft.
