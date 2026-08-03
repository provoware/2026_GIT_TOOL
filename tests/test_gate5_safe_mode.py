from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "system"))

import autosave_manager
from autostart_manager import AutostartError, AutostartManager
from session_lifecycle import AutosaveSession, run_shutdown_sequence


class Scheduler:
    def __init__(self):
        self.jobs = []

    def schedule(self, delay, callback):
        self.jobs.append((delay, callback))
        return "job"

    def cancel(self, _job_id):
        return None


def test_safe_mode_prevents_autosave_scheduling(monkeypatch):
    monkeypatch.setenv("GENREARCHIV_WRITE_MODE", "read-only")
    scheduler = Scheduler()
    session = AutosaveSession(scheduler.schedule, scheduler.cancel, lambda: None)

    assert session.start(autosave_manager.AutosaveConfig(True, 10)) is False
    assert session.active is False
    assert session.job_id is None
    assert scheduler.jobs == []


def test_safe_mode_skips_shutdown_writes(monkeypatch, tmp_path):
    monkeypatch.setenv("GENREARCHIV_WRITE_MODE", "read-only")
    writes = []

    outcome = run_shutdown_sequence(
        autosave_config=autosave_manager.AutosaveConfig(True, 10),
        data_root=tmp_path / "data",
        logs_root=tmp_path / "logs",
        logger=logging.getLogger("gate5-safe-mode"),
        backup_config_path=tmp_path / "backup.json",
        backup_state_path=tmp_path / "state.json",
        create_autosave=lambda *_args: writes.append("autosave"),
        load_backup_config=lambda _path: writes.append("load-backup"),
        create_backup=lambda *_args: writes.append("backup"),
    )

    assert outcome.success is True
    assert writes == []
    assert "Schreibgeschützter Modus" in outcome.report
    assert "Autosave und Backup wurden ohne Schreibzugriff übersprungen" in outcome.report


def test_safe_mode_blocks_autostart_changes(monkeypatch, tmp_path):
    script = tmp_path / "project" / "scripts" / "start.sh"
    script.parent.mkdir(parents=True)
    script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    manager = AutostartManager(script, tmp_path / "autostart")
    monkeypatch.setenv("GENREARCHIV_WRITE_MODE", "read-only")

    with pytest.raises(AutostartError, match="schreibgeschützten Modus"):
        manager.set_enabled(True)

    assert manager.desktop_path.exists() is False
