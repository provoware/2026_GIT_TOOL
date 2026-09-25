# AGENTS.md (global, verbindlich)

## Prinzip
- Arbeite immer Punkte aus todo.txt ab und dann immer so weiter (4 Task pro Runde).
- Erst analysieren, dann umsetzen, dann testen, dann dokumentieren. 
- Kein Rumprobieren ohne Ende: max. 2 Fix-Runden pro Task. Wenn es klemmt: Task splitten.

## Reihenfolge je Runde (verbindlich)
1) Lies todo.txt und nimm die 4 vom Aufwand kleinsten offenen Task.
2) Führe eine kurze Ist-Analyse durch: Fehler, Lücken, Platzhalter, Risiken, Schwachstellen, best practices.
3) Setze nur diese Task vollständig um (release-tauglich, konsistent).
4) Validiere Erfolg: Tests/Checks laufen grün, Start läuft, Kernfunktion ok.
5) Aktualisiere Dateien:
   - CHANGELOG.md (was geändert, warum)
   - DEV_DOKU.md (wie gebaut/getestet)
   - DONE.md (Task abgeschlossen + Datum)
   - PROGRESS.md (Prozent + Zähler)
   - README.md + DEV_DOKU.md Auto-Status per `./scripts/update_docs.sh` aktualisieren

## Qualitätsregeln
- Stabilität vor neuen Features.
- Keine vorhandenen funktionierenden Teile kaputtmachen.
- Tooltexte: Deutsch, klar, laienverständlich (Menüs/Hilfe/Fehlertexte).
- Dateinamen Linux-konform, keine Überschreibungen, immer eindeutig.
- Barrierefreiheit: Tastaturbedienung, Kontrast, klare Buttons, verständliche Meldungen.

## Definition „fertig“
- Task erfüllt + Test bestanden + Doku aktualisiert + Progress aktualisiert.

---

## PROVOWARE GLOBAL DEVELOPMENT CONTRACT

Dieser globale Kern gilt zusätzlich zu den projektspezifischen Regeln. Bei Sicherheits- oder Nachvollziehbarkeitskonflikten hat er Vorrang; lokale Regeln dürfen ihn verschärfen, nicht stillschweigend abschwächen.

- **Frozen Current Plan:** Laufenden freigegebenen Plan nicht durch neue Ideen erweitern; Neues in die nächste Iteration einordnen.
- **Conflict Gate:** Unterbrechen nur bei nachgewiesenem Konflikt mit Planvoraussetzung, Sicherheit, Ausgangs-SHA, Scope oder Invariant.
- **Single Writer:** Pro produktivem Scope nur ein autorisierter Executor; Analyse/Planung/Prüfung dürfen parallel lesen.
- **SHA + Scope:** Vor Mutation HEAD und erlaubten/verbotenen Scope prüfen; keine stillen Nebenrefactorings.
- **Evidence:** Kein PASS ohne echten Test; Evidence muss zum geprüften HEAD gehören.
- **Controlled Evidence Lab:** Echte Mutationen, Fehler-Injektion und Recovery-Tests nur in isolierten Testbereichen; Produktivdaten bleiben geschützt.
- **Next Queue:** Neue Anforderungen/Findings append-only erfassen und Beziehungen wie BLOCKS, REQUIRES, SUPERSEDES, DUPLICATE oder CONFLICTS dokumentieren.
- **Statusklarheit:** OBSERVED/SUSPECTED/REPRODUCED/CONFIRMED/DISPROVED nicht vermischen.
- **Recovery Key:** Nach Abbruch oder Agentenwechsel müssen Stand, Ziel, Frozen Plan, Scope, Findings, Gates und nächster erlaubter Schritt ohne alten Chat rekonstruierbar sein.
- **Traceability:** Requirement/Decision → Finding → Plan → Change → Test/Evidence → Gate/Checkpoint nachvollziehbar halten.
- **Negativtests:** Schutzmechanismen absichtlich gegen falschen SHA, zweiten Writer, Scope-Verstoß und unbelegtes PASS testen.
- **Sichtbarer Fortschritt:** Längere Prüfungen mit Schritt, Fortschritt, Ergebnis und Ampelstatus darstellen.

Leitsatz: **Kein Agent muss sich erinnern. Kein Agent darf raten. Keine Änderung verliert ihren Ursprung. Kein PASS existiert ohne Evidence.**
