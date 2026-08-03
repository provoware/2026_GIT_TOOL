# Gate 5 – Session-Lifecycle, Shutdown und Autostart

Stand: 2026-08-03
Status: abgeschlossen

## Gehärteter Umfang

- `system/session_lifecycle.py`
- `system/autostart_manager.py`
- Autosave-Planung und kontrollierter Job-Abbruch
- kombinierte Autosave-/Backup-Abfolge beim Abmelden
- deterministischer Logoutbericht bei Erfolg, Teilerfolg und erwarteten Fehlern
- Logout als Kategorie `shutdown` des gehärteten Task-Runners
- Fensterzerstörung ausschließlich nach UI-Abschlusscallback und Autosave-Abbruch
- benutzerspezifischer Linux-XDG-Autostart über einen sichtbaren Launcher-Schalter
- durchgängige Schreibsperre bei `GENREARCHIV_WRITE_MODE=read-only`

## Sicherheitsvertrag

1. Pro Kategorie kann nur ein Shutdown-Lauf aktiv sein.
2. Autosave und Backup laufen außerhalb des Tkinter-Threads.
3. Der UI-Abschluss wird ausschließlich über den Task-Runner-Scheduler zugestellt.
4. Ein Autosave-Fehler verhindert den anschließenden Backup-Versuch nicht.
5. Ein Backup-Fehler verwirft einen erfolgreichen Autosave-Nachweis nicht.
6. Der geplante Autosave-Job wird vor der Fensterzerstörung beendet.
7. `root.destroy` wird nur verzögert geplant und nicht aus dem Worker aufgerufen.
8. Der Autostart-Eintrag wird atomar geschrieben.
9. Nur Dateien mit `X-Genrearchiv-Managed=true` dürfen aktualisiert oder entfernt werden.
10. Fremde gleichnamige Desktop-Einträge werden weder überschrieben noch gelöscht.
11. Im schreibgeschützten Modus werden Autosave, Backup und Autostartänderungen vollständig blockiert.

## Testnachweis

- Autosave aktiviert und deaktiviert
- korrekte Intervallplanung und Neuplanung
- Job-Abbruch und idempotenter Abbruch
- Autosave-Fehler mit anschließendem Backup
- Backup-Fehler bei erhaltenem Autosave-Ergebnis
- kombinierter Erfolgsbericht
- kontrollierte Reihenfolge Bericht → Status → Job-Abbruch → Destroy-Planung
- keine Fensterzerstörung vor Ausführung des geplanten Callbacks
- Autostart aktivieren, deaktivieren und erneut aktivieren
- absolute Start- und Arbeitsverzeichnisse
- XDG-Desktop-Entry mit `TryExec`, argumentweiser `Exec`-Quotierung und verwaltetem Marker
- Schutz fremder Autostartdateien
- fehlendes Startskript
- Safe-Mode verhindert Autosave-Planung
- Safe-Mode überspringt Autosave und Backup ohne Schreibzugriff
- Safe-Mode blockiert Autostartänderungen
- idempotenter Launcher-Codemod
- Python-Kompilierungsprüfung des integrierten Zustands
- Regression-Gates 1, 3 und 4 erfolgreich

## Integrationsdateien

- `tests/test_session_lifecycle.py`
- `tests/test_autostart_manager.py`
- `tests/test_gate5_safe_mode.py`
- `tests/test_gate5_session_lifecycle_codemod.py`
- `scripts/apply_gate5_session_lifecycle.py`
- `.github/workflows/gate-5-session-lifecycle.yml`

## Restgrenze

Nicht Bestandteil von Gate 5:

- Modulkarten und Modul-Lebenszyklus
- Close-Policy des Hauptfensters
- Launcher-Teilviews und Controllerzerlegung
- systemweiter Autostart vor Benutzeranmeldung

Der Schalter verwendet bewusst den benutzerspezifischen XDG-Autostart nach der Linux-Anmeldung. Dadurch sind keine Root-Rechte oder systemweiten Dienste erforderlich.

## Nächster zulässiger Schritt

Gate 6: Modulkarten und Modul-Lebenszyklus.
