# Gate 6 – Modulkarten und Modul-Lebenszyklus

Stand: 2026-08-03
Status: abgeschlossen

## Gehärteter Umfang

- `system/module_lifecycle.py`
- Aktivierung und Deaktivierung über einen gemeinsamen Aktionsvertrag
- erneutes Lesen des Managerzustands nach jeder Modulaktion
- Status-, Farb- und Schaltflächenzustand der Modulkarten
- Synchronisation aller Karten nach einem Themewechsel
- explizite Close-Policy für das Hauptfenster
- kontrollierte Integration in `system/main_window.py`

## Zustandsvertrag

1. Der Zustand in `ModuleManager` ist die einzige autoritative Quelle.
2. Eine angeforderte Aktivierung macht eine Karte nicht automatisch aktiv.
3. Nach jeder Aktion wird `get_state()` erneut aufgerufen.
4. Eine fehlgeschlagene Aktivierung bleibt sichtbar inaktiv und erneut aktivierbar.
5. Eine fehlgeschlagene Deaktivierung bleibt sichtbar aktiv und erneut deaktivierbar.
6. Deaktivierte oder strukturell fehlerhafte Module erhalten keine aktive Aktivieren-Schaltfläche.
7. Die Deaktivieren-Schaltfläche ist nur bei einem tatsächlich aktiven Modul verfügbar.
8. Warnungen verwenden den vorhandenen Busy-/Hinweisstatus; Fehler verwenden den Fehlerstatus.

## Close-Policy

Beim Schließen des Hauptfensters gilt folgende Reihenfolge:

1. Vorhandene Modulzustände erfassen.
2. Ausschließlich aktuell aktive Module über den fenstereigenen Manager deaktivieren.
3. Zustände erneut erfassen.
4. Alle Modulkarten mit den tatsächlichen Ergebnissen synchronisieren.
5. Fenster nur zerstören, wenn kein Modul aktiv geblieben ist.

Ein Exit-Fehler, nach dem das Modul aktiv bleibt, blockiert `root.destroy()` vollständig. Bereits erfolgreich deaktivierte Module bleiben deaktiviert und werden korrekt dargestellt. Ein Warnresultat darf das Schließen nur dann freigeben, wenn das betreffende Modul anschließend tatsächlich inaktiv ist.

## Schutz vor globalen Nebenwirkungen

- Es werden keine Registry-Einträge geändert.
- Es werden keine Module aktiviert, die vor dem Schließen inaktiv waren.
- `deactivate_all()` wirkt nur auf den `ModuleManager` dieser Hauptfensterinstanz.
- Theme-, Workspace- und Launcher-Lifecycle bleiben unverändert.
- Modulimplementierungen und deren `init`-/`exit`-Funktionen werden nicht umgeschrieben.

## Testnachweis

- inaktive Karte mit neutralem Status und korrekten Schaltflächen
- aktive Karte mit Erfolgsstatus und korrekten Schaltflächen
- deaktivierte und fehlerhafte Module nicht aktivierbar
- fehlgeschlagene Aktivierung bleibt inaktiv
- erfolgreiche Aktivierung und Deaktivierung folgen dem Managerzustand
- fehlgeschlagene Deaktivierung bleibt aktiv und erneut bedienbar
- Schließen ohne aktive Module verursacht keine Deaktivierung
- nur aktive Module werden beim Schließen deaktiviert
- Warnung bei anschließend inaktivem Modul erlaubt das Schließen
- Exit-Fehler mit verbleibendem aktiven Modul blockiert das Schließen
- unbekannte Modulaktion wird vor einer Mutation abgewiesen
- Codemod idempotent und syntaktisch gültig
- vollständige `main_window.py` erfolgreich transformiert und kompiliert
- reale Integration über GitHub Actions erfolgreich
- finaler Workflow wieder auf `contents: read` beschränkt
- Regression-Gates 2 und 3 erfolgreich

## Integrationsdateien

- `tests/test_module_lifecycle.py`
- `tests/test_gate6_module_lifecycle_codemod.py`
- `scripts/apply_gate6_module_lifecycle.py`
- `.github/workflows/gate-6-module-lifecycle.yml`

## Restgrenze

Nicht Bestandteil von Gate 6:

- Zerlegung des Launcher-Controllers in Teilviews
- Refresh-Debounce und Filtersteuerung
- Undo/Redo des Themewechsels
- Hilfe- und Shortcutregistrierung
- physische visuelle Abnahme der Karten auf realen Displays

## Nächster zulässiger Schritt

Gate 7: Launcher-Controller und Teilviews.
