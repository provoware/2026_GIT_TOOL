# Archiv-Verwaltung: GUI, CLI und kurze Aliase

## Zweck

Das Modul verwaltet strukturierte Archive in einer gemeinsamen SQLite-Datenbank. Die grafische Oberfläche, der Konsolenassistent, die kurzen Alias-Befehle und die Modul-API verwenden dieselbe Geschäftslogik. Einträge werden deshalb unabhängig vom Zugangsweg identisch geprüft, gespeichert, gefiltert und protokolliert.

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

## Klassischen CLI-Assistenten starten

Im Projektordner:

```bash
python -m modules.archiv_manager
```

Der Assistent erklärt jeden Schritt, zeigt die Archivbeschreibung und den aktiven Eingabemodus, fragt Kategorie und Inhalt ab, zeigt Rechtschreibhinweise sowie Duplikate und speichert erst nach Bestätigung.

## Kurze Aliase installieren

Einmalig oder nach dem Anlegen weiterer Archive ausführen:

```bash
python -m modules.archiv_manager --install-aliases
```

Standardziel ist `~/.local/bin`. Ist dieser Ordner noch nicht in `PATH`, meldet die Installation den passenden Hinweis. Ein alternatives Ziel ist möglich:

```bash
python -m modules.archiv_manager \
  --install-aliases \
  --alias-dir /gewünschter/bin-ordner
```

Die Installation überschreibt keine fremden gleichnamigen Dateien. `--force` muss ausdrücklich angegeben werden, um eine Namenskollision zu ersetzen. Verwaltete Aliase lassen sich sicher entfernen:

```bash
python -m modules.archiv_manager --uninstall-aliases
```

Nach einem Umzug des Projektordners oder einem Wechsel der Python-Installation müssen die Aliase erneut installiert werden, weil die Wrapper absichtlich auf den geprüften Projekt- und Interpreterpfad zeigen.

## Zentrale Steueroberfläche

```bash
garch
```

`garch` zeigt alle verfügbaren CLI-Funktionen, alle Standardarchive, benutzerdefinierte Archive und die zugehörigen Alias-Befehle. Von dort können Eingabe, Übersicht, Archiv-Erstellung, Moduswechsel, Alias-Hilfe und Alias-Aktualisierung direkt gestartet werden.

## Funktionsaliase

| Alias | Funktion |
|---|---|
| `garch` | Zentrale CLI-Steueroberfläche |
| `garch-add` | Geführte Eingabe mit freier Archivwahl |
| `garch-list` | Archive, Beschreibungen und Eingabemodi anzeigen |
| `garch-new` | Neues Archiv anlegen |
| `garch-mode` | Komma- oder Gesamttext-Modus ändern |
| `garch-aliases` | Aliasübersicht anzeigen oder Aliase aktualisieren |
| `garch-help` | Ausführliche Alias- und Bedienhilfe |

Beispiele:

```bash
garch-new "Technische Ideen" \
  --description "Wiederverwendbare technische Lösungsansätze" \
  --split-mode whole

garch-mode genres whole

garch-list
```

## Aliase der sieben Standardarchive

| Archiv | Alias |
|---|---|
| Genres | `garch-gen` |
| Stimmungen | `garch-stim` |
| Besondere Effekte | `garch-fx` |
| Favoriten | `garch-fav` |
| Basis-Entwicklungs-Strukturen | `garch-basis` |
| Brainstorm | `garch-brain` |
| Linux | `garch-linux` |

Ohne Optionen startet ein Archiv-Alias die geführte Eingabe für genau dieses Archiv:

```bash
garch-linux
```

Direkte, bestätigte Eingabe:

```bash
garch-gen \
  --category Allgemein \
  --value "Fantasy, Horror, Science-Fiction" \
  --yes
```

Benutzerdefinierte Archive erhalten beim Aktualisieren der Aliase einen kollisionsfreien Befehl nach dem Muster:

```text
garch-a-<archivkennung>
```

Beispiel: Aus dem Archiv „Technische Ideen“ wird `garch-a-technische-ideen`.

## Lange CLI-Befehle

Direkte Eingabe ohne Alias:

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

Eingabemodus direkt ändern:

```bash
python -m modules.archiv_manager \
  --archive genres \
  --set-mode whole
```

Alle Aliasnamen anzeigen:

```bash
python -m modules.archiv_manager --show-aliases
```

## Daten und Protokollierung

Standardpfade:

- Datenbank: `data/archiv_manager.sqlite3`
- rotierendes CLI-Protokoll: `logs/archiv_manager.log`

Zusätzlich protokolliert die Datenbank bestätigte Änderungen in `audit_events`. Duplikate werden archivweit anhand normalisierter Schreibweise erkannt; Groß- und Kleinschreibung beeinflusst die Erkennung nicht.

Für Tests oder getrennte Arbeitsstände kann die Datenbank überschrieben werden:

```bash
GENREARCHIV_ARCHIVE_DB=/pfad/test.sqlite3 garch-list
```

## Sicherheits- und Robustheitsregeln

- Alle Aliase verwenden denselben `ArchiveService` und dieselbe SQLite-Datenbank wie GUI und Modul-API.
- Aliasnamen besitzen durchgehend das Präfix `garch`, damit sie eindeutig zuordenbar bleiben.
- Fremde Dateien im Alias-Zielordner werden ohne ausdrückliches `--force` nicht überschrieben.
- Die Deinstallation entfernt ausschließlich Dateien mit eindeutiger GenreArchiv-Verwaltungsmarkierung.
- Installation und Aktualisierung schreiben Wrapper atomar.
- Benutzerdefinierte Archive verwenden das Präfix `garch-a-`, damit sie nicht mit Funktionsaliasen kollidieren.
- Leere oder widersprüchliche Direktoptionen werden mit verständlichem Fehlercode abgewiesen.
- Nicht bestätigte Eingaben werden nicht gespeichert.
