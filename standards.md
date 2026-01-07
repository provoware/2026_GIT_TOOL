# Zentrale Tool-Standards

Diese Datei definiert verbindliche Standards für alle Tools in diesem Repository.
Ziel: konsistente Struktur, verständliche Texte, barrierefreie Bedienung und stabile Qualität.

## 1) Struktur (Pflicht)
- `src/`: stabile Systemlogik (Kerncode).
- `config/`: Konfiguration (änderbar ohne Codeänderung).
- `data/`: variable Daten und Laufzeitdateien.
- `scripts/`: Start- und Prüfskripte.

## 2) Modul-Schnittstelle (Pflicht)
Jedes Modul stellt eine klar dokumentierte **Init**- und **Exit**-Struktur bereit.
- **Init**: prüft Abhängigkeiten, validiert Eingaben, gibt einen klaren Status zurück.
- **Exit**: räumt Ressourcen auf und meldet Erfolg oder Fehler verständlich.

## 3) Texte & Barrierefreiheit (Pflicht)
- Alle UI-Texte sind **Deutsch**, klar und laienverständlich.
- Fachbegriffe stehen **in Klammern** und werden kurz erklärt.
- Tastaturbedienung ist möglich, Buttons sind eindeutig beschriftet.
- Kontrast ist hoch, Lesbarkeit ist in Hell- und Dunkelmodus gegeben.

## 4) Qualitätssicherung (Pflicht)
- Jede Funktion validiert Eingaben und prüft den Erfolg der Ausgabe.
- Fehler werden sauber behandelt und verständlich beschrieben.
- Logging (Protokollierung) ist zentral und eindeutig.

## 5) Änderungskontrolle (Pflicht)
- Änderungen werden in `CHANGELOG.md` dokumentiert.
- Abgeschlossene Aufgaben werden in `DONE.md` erfasst.
- Fortschritt wird in `PROGRESS.md` aktualisiert.
