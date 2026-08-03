# Archiv-Verwaltung: GUI und CLI mit gemeinsamer Datenbank

## Zweck

Das Modul verwaltet strukturierte Archive in einer gemeinsamen SQLite-Datenbank. Die grafische Oberfläche, der Konsolenassistent und die Modul-API verwenden dieselbe Geschäftslogik. Dadurch werden Einträge unabhängig vom Zugangsweg identisch geprüft, gespeichert, gefiltert und protokolliert.

## Standardarchive

1. Genres
2. Stimmungen
3. Besondere Effekte
4. Favoriten
5. Basis-Entwicklungs-Strukturen
6. Brainstorm
7. Linux

Jedes Archiv besitzt einen eigenen Schalter:

- **Komma-Modus:** Ein Komma trennt einzelne Einträge.
- **Gesamttext-Modus:** Die vollständige Eingabe wird als ein Eintrag gespeichert.

## CLI starten

Im Projektordner:

```bash
python -m modules.archiv_manager
```

Der Assistent erklärt jeden Schritt, zeigt Archivbeschreibung und Eingabemodus, fragt Kategorie und Inhalt ab, weist auf Rechtschreibung sowie Duplikate hin und speichert erst nach Bestätigung.

Direkte Eingabe:

```bash
python -m modules.archiv_manager \
  --archive genres \
  --category Allgemein \
  --value "Fantasy, Horror, Science-Fiction" \
  --yes
```

Archivübersicht:

```bash
python -m modules.archiv_manager --list
```

Neues Archiv:

```bash
python -m modules.archiv_manager \
  --create-archive "Technische Ideen" \
  --description "Wiederverwendbare technische Lösungsansätze" \
  --split-mode whole
```

## Daten und Protokollierung

Standardpfade:

- Datenbank: `data/archiv_manager.sqlite3`
- rotierendes CLI-Protokoll: `logs/archiv_manager.log`

Zusätzlich protokolliert die Datenbank bestätigte Änderungen in `audit_events`. Duplikate werden archivweit anhand normalisierter Schreibweise erkannt; Groß- und Kleinschreibung beeinflusst die Erkennung nicht.

Für Tests oder getrennte Arbeitsstände kann die Datenbank überschrieben werden:

```bash
GENREARCHIV_ARCHIVE_DB=/pfad/test.sqlite3 python -m modules.archiv_manager
```
