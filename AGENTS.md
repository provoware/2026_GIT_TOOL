# AGENTS.md (global, verbindlich)

## Prinzip
- Arbeite immer nur an 2 kleinsten Punkten aus todo.txt und dann immer so weiter (zwei Task pro Runde).
- Erst analysieren, dann umsetzen, dann testen, dann dokumentieren. 
- Kein Rumprobieren ohne Ende: max. 2 Fix-Runden pro Task. Wenn es klemmt: Task splitten.

## Reihenfolge je Runde (verbindlich)
1) Lies todo.txt und nimm die zwei vom Aufwand kleinsten offenen Task .
2) Führe eine kurze Ist-Analyse durch: Fehler, Lücken, Platzhalter, Risiken, Schwachstellen, best practices.
3) Setze nur diese Task vollständig um (release-tauglich, konsistent).
4) Validiere Erfolg: Tests/Checks laufen grün, Start läuft, Kernfunktion ok.
5) Aktualisiere Dateien:
   - CHANGELOG.md (was geändert, warum)
   - DEV_DOKU.md (wie gebaut/getestet)
   - DONE.md (Task abgeschlossen + Datum)
   - PROGRESS.md (Prozent + Zähler)

## Qualitätsregeln
- Stabilität vor neuen Features.
- Keine vorhandenen funktionierenden Teile kaputtmachen.
- Tooltexte: Deutsch, klar, laienverständlich (Menüs/Hilfe/Fehlertexte).
- Dateinamen Linux-konform, keine Überschreibungen, immer eindeutig.
- Barrierefreiheit: Tastaturbedienung, Kontrast, klare Buttons, verständliche Meldungen.

## Definition „fertig“
- Task erfüllt + Test bestanden + Doku aktualisiert + Progress aktualisiert.
