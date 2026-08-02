# Gate 4 – Task-Runner

Status: abgeschlossen und in `system/launcher_gui.py` integriert

## Gehärteter Umfang

- `system/task_runner.py`
  - höchstens ein aktiver Task pro Kategorie
  - getrennte Kategorien dürfen parallel laufen
  - Worker-Ausführung in einem Hintergrundthread
  - Abschluss ausschließlich über den injizierten UI-Scheduler
  - Freigabe der Kategorie vor dem Abschluss-Callback
  - Erfolgs- und Ausnahmeergebnisse über `TaskOutcome`
  - kontrollierte Freigabe bei Thread-Start- oder Schedulerfehlern
  - zentrale Kommando- und Pfadvalidierung
  - zentrale Prozessausführung und normalisiertes `CommandResult`
- `system/launcher_gui.py`
  - Diagnose und Wartung delegieren an `TaskRunner`
  - direkte `subprocess.run`-Ausführung entfernt
  - direkte Diagnose- und Wartungsthreads entfernt
  - parallele Bool-Flags durch kategorisierten Zustand ersetzt
  - deaktivierte Schaltflächen werden in allen Abschluss- und Startfehlerpfaden wiederhergestellt

## Nachweise

- `tests/test_task_runner.py`
  - Einzelbelegung einer Kategorie
  - parallele unterschiedliche Kategorien
  - UI-Scheduling mit Verzögerung `0`
  - Erfolgs- und Ausnahmeausgang
  - Freigabe vor Abschluss-Callback
  - Thread-Startfehler
  - Scheduler-Ausfall
  - Kommando- und Pfadvalidierung
  - Prozessausgabe und Exit-Code
- `tests/test_gate4_task_runner_codemod.py`
  - idempotenter Codemod
  - gültige Python-Syntax
  - keine Veränderung der Gate-5-, Theme- oder Layoutbereiche
- vollständige `launcher_gui.py` erfolgreich transformiert und kompiliert
- reale Integration über GitHub Actions erfolgreich
- dauerhafter Workflow anschließend auf `contents: read` zurückgehärtet
- finaler integrierter Zustand erfolgreich geprüft
- Regression-Gates 1 und 3 erfolgreich

## Kanonische Integration

- `scripts/apply_gate4_task_runner.py`
- `.github/workflows/gate-4-task-runner.yml`

## Bewusste Restgrenzen

Nicht Bestandteil von Gate 4:

- Logout-Thread und Logoutbericht
- Autosave-Planung und Job-Abbruch
- Backup-Abfolge beim Abmelden
- Fensterzerstörung nach Abschluss
- Modul-Lebenszyklus
- Refresh-Debounce und übriger Launcher-Controller

Diese Bereiche bleiben bis zu den vorgesehenen Gates unverändert.
