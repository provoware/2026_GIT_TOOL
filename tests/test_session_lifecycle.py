from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "system"))

import autosave_manager
import backup_center
from session_lifecycle import (
    AutosaveSession,
    ShutdownOutcome,
    complete_shutdown,
    run_shutdown_sequence,
)


class FakeScheduler:
    def __init__(self):
        self.jobs = {}
        self.cancelled = []
        self.counter = 0

    def schedule(self, delay, callback):
        self.counter += 1
        job_id = f"job-{self.counter}"
        self.jobs[job_id] = (delay, callback)
        return job_id

    def cancel(self, job_id):
        self.cancelled.append(job_id)
        self.jobs.pop(job_id, None)


def autosave_result(tmp_path: Path):
    return autosave_manager.AutosaveResult(
        archive_path=tmp_path / "autosave.zip",
        timestamp=datetime.now(timezone.utc),
        saved_files=["one.json"],
    )


def backup_result(tmp_path: Path):
    return backup_center.BackupResult(
        archive_path=tmp_path / "backup.zip",
        timestamp=datetime.now(timezone.utc),
        file_count=2,
    )


def backup_config(tmp_path: Path):
    return backup_center.BackupConfig(
        output_dir=tmp_path,
        sources=[],
        exclude_dirs=[],
        max_backups=2,
    )


def test_autosave_session_disabled_creates_no_job():
    scheduler = FakeScheduler()
    session = AutosaveSession(scheduler.schedule, scheduler.cancel, lambda: None)

    started = session.start(autosave_manager.AutosaveConfig(False, 10))

    assert started is False
    assert session.active is False
    assert session.job_id is None
    assert scheduler.jobs == {}


def test_autosave_session_runs_and_reschedules():
    scheduler = FakeScheduler()
    calls = []
    session = AutosaveSession(scheduler.schedule, scheduler.cancel, lambda: calls.append("saved"))

    assert session.start(autosave_manager.AutosaveConfig(True, 3)) is True
    first_job = session.job_id
    delay, callback = scheduler.jobs[first_job]
    assert delay == 180000

    callback()

    assert calls == ["saved"]
    assert session.job_id != first_job
    assert session.job_id in scheduler.jobs


def test_autosave_session_reschedules_after_callback_error():
    scheduler = FakeScheduler()
    session = AutosaveSession(
        scheduler.schedule,
        scheduler.cancel,
        lambda: (_ for _ in ()).throw(RuntimeError("save failed")),
    )
    session.start(autosave_manager.AutosaveConfig(True, 1))
    _delay, callback = scheduler.jobs[session.job_id]

    try:
        callback()
    except RuntimeError as exc:
        assert str(exc) == "save failed"

    assert session.job_id in scheduler.jobs


def test_autosave_job_can_be_cancelled_once():
    scheduler = FakeScheduler()
    session = AutosaveSession(scheduler.schedule, scheduler.cancel, lambda: None)
    session.start(autosave_manager.AutosaveConfig(True, 2))
    job_id = session.job_id

    assert session.cancel() is True
    assert scheduler.cancelled == [job_id]
    assert session.active is False
    assert session.job_id is None
    assert session.cancel() is False


def test_shutdown_success_combines_autosave_and_backup(tmp_path):
    outcome = run_shutdown_sequence(
        autosave_config=autosave_manager.AutosaveConfig(True, 10),
        data_root=tmp_path / "data",
        logs_root=tmp_path / "logs",
        logger=logging.getLogger("gate5-success"),
        backup_config_path=tmp_path / "backup.json",
        backup_state_path=tmp_path / "state.json",
        create_autosave=lambda *_args: autosave_result(tmp_path),
        load_backup_config=lambda _path: backup_config(tmp_path),
        create_backup=lambda *_args: backup_result(tmp_path),
    )

    assert isinstance(outcome, ShutdownOutcome)
    assert outcome.success is True
    assert "Erfolg: Autosave erstellt" in outcome.report
    assert "Erfolg: Backup erstellt" in outcome.report
    assert outcome.report.endswith("\n")


def test_shutdown_reports_disabled_autosave_but_still_runs_backup(tmp_path):
    backup_calls = []
    outcome = run_shutdown_sequence(
        autosave_config=autosave_manager.AutosaveConfig(False, 10),
        data_root=tmp_path / "data",
        logs_root=tmp_path / "logs",
        logger=logging.getLogger("gate5-disabled"),
        backup_config_path=tmp_path / "backup.json",
        backup_state_path=tmp_path / "state.json",
        create_autosave=lambda *_args: (_ for _ in ()).throw(AssertionError("not expected")),
        load_backup_config=lambda _path: backup_config(tmp_path),
        create_backup=lambda *_args: backup_calls.append(True) or backup_result(tmp_path),
    )

    assert outcome.success is True
    assert "Autosave ist deaktiviert" in outcome.report
    assert backup_calls == [True]


def test_shutdown_continues_to_backup_after_autosave_error(tmp_path):
    outcome = run_shutdown_sequence(
        autosave_config=autosave_manager.AutosaveConfig(True, 10),
        data_root=tmp_path / "data",
        logs_root=tmp_path / "logs",
        logger=logging.getLogger("gate5-autosave-error"),
        backup_config_path=tmp_path / "backup.json",
        backup_state_path=tmp_path / "state.json",
        create_autosave=lambda *_args: (_ for _ in ()).throw(
            autosave_manager.AutosaveError("disk full")
        ),
        load_backup_config=lambda _path: backup_config(tmp_path),
        create_backup=lambda *_args: backup_result(tmp_path),
    )

    assert outcome.success is False
    assert "Fehler: Autosave fehlgeschlagen." in outcome.report
    assert "Ursache: disk full" in outcome.report
    assert "Erfolg: Backup erstellt" in outcome.report


def test_shutdown_reports_backup_error_without_losing_autosave_result(tmp_path):
    outcome = run_shutdown_sequence(
        autosave_config=autosave_manager.AutosaveConfig(True, 10),
        data_root=tmp_path / "data",
        logs_root=tmp_path / "logs",
        logger=logging.getLogger("gate5-backup-error"),
        backup_config_path=tmp_path / "backup.json",
        backup_state_path=tmp_path / "state.json",
        create_autosave=lambda *_args: autosave_result(tmp_path),
        load_backup_config=lambda _path: (_ for _ in ()).throw(
            backup_center.BackupCenterError("invalid config")
        ),
        create_backup=lambda *_args: backup_result(tmp_path),
    )

    assert outcome.success is False
    assert "Erfolg: Autosave erstellt" in outcome.report
    assert "Fehler: Backup fehlgeschlagen." in outcome.report
    assert "Ursache: invalid config" in outcome.report


def test_complete_shutdown_cancels_autosave_before_scheduling_destroy():
    events = []
    scheduled = []

    def schedule(delay, callback):
        events.append("schedule")
        scheduled.append((delay, callback))
        return "destroy-job"

    result = complete_shutdown(
        ShutdownOutcome("report\n", True),
        append_report=lambda report: events.append(("report", report)),
        set_status=lambda message, state: events.append(("status", message, state)),
        cancel_autosave=lambda: events.append("cancel"),
        schedule=schedule,
        destroy=lambda: events.append("destroy"),
    )

    assert result == "destroy-job"
    assert events == [
        ("report", "report\n"),
        ("status", "Abmelden abgeschlossen.", "success"),
        "cancel",
        "schedule",
    ]
    assert scheduled[0][0] == 200
    assert "destroy" not in events

    scheduled[0][1]()
    assert events[-1] == "destroy"


def test_complete_shutdown_uses_error_status_for_partial_failure():
    statuses = []
    complete_shutdown(
        ShutdownOutcome("problem\n", False),
        append_report=lambda _report: None,
        set_status=lambda message, state: statuses.append((message, state)),
        cancel_autosave=lambda: None,
        schedule=lambda _delay, _callback: "job",
        destroy=lambda: None,
    )

    assert statuses == [("Abmelden mit Problemen.", "error")]
