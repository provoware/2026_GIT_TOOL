from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "system"))

from task_runner import (
    CommandValidationError,
    TaskRunner,
    TaskRunnerError,
    execute_command,
    validate_command,
)


class ImmediateThread:
    def __init__(self, *, target, daemon):
        self.target = target
        self.daemon = daemon

    def start(self):
        self.target()


class FailingThread(ImmediateThread):
    def start(self):
        raise RuntimeError("thread start failed")


def queued_scheduler():
    callbacks = []

    def schedule(delay, callback):
        callbacks.append((delay, callback))

    return callbacks, schedule


def test_only_one_task_per_category_until_ui_callback():
    callbacks, schedule = queued_scheduler()
    outcomes = []
    runner = TaskRunner(schedule, thread_factory=ImmediateThread)

    assert runner.start("maintenance", lambda: "ok", outcomes.append) is True
    assert runner.is_running("maintenance") is True
    assert runner.start("maintenance", lambda: "second", outcomes.append) is False
    assert callbacks[0][0] == 0

    callbacks[0][1]()

    assert runner.is_running("maintenance") is False
    assert outcomes[0].succeeded is True
    assert outcomes[0].value == "ok"


def test_different_categories_may_run_concurrently():
    callbacks, schedule = queued_scheduler()
    runner = TaskRunner(schedule, thread_factory=ImmediateThread)

    assert runner.start("maintenance", lambda: 1, lambda _outcome: None) is True
    assert runner.start("diagnostics", lambda: 2, lambda _outcome: None) is True
    assert runner.is_running("maintenance") is True
    assert runner.is_running("diagnostics") is True

    for _delay, callback in callbacks:
        callback()

    assert runner.is_running("maintenance") is False
    assert runner.is_running("diagnostics") is False


def test_exception_is_delivered_through_scheduler_and_releases_category_first():
    callbacks, schedule = queued_scheduler()
    observations = []
    runner = TaskRunner(schedule, thread_factory=ImmediateThread)

    def fail():
        raise RuntimeError("boom")

    def complete(outcome):
        observations.append((runner.is_running("diagnostics"), outcome))

    assert runner.start("diagnostics", fail, complete) is True
    callbacks[0][1]()

    running, outcome = observations[0]
    assert running is False
    assert outcome.succeeded is False
    assert isinstance(outcome.error, RuntimeError)
    assert str(outcome.error) == "boom"


def test_thread_start_failure_releases_category():
    callbacks, schedule = queued_scheduler()
    runner = TaskRunner(schedule, thread_factory=FailingThread)

    with pytest.raises(TaskRunnerError, match="konnte nicht starten"):
        runner.start("maintenance", lambda: None, lambda _outcome: None)

    assert callbacks == []
    assert runner.is_running("maintenance") is False


def test_scheduler_failure_releases_category():
    def broken_schedule(_delay, _callback):
        raise RuntimeError("window closed")

    runner = TaskRunner(broken_schedule, thread_factory=ImmediateThread)
    assert runner.start("maintenance", lambda: None, lambda _outcome: None) is True
    assert runner.is_running("maintenance") is False


def test_validate_command_checks_script_and_target_paths(tmp_path):
    script = tmp_path / "job.py"
    script.write_text("print('ok')\n", encoding="utf-8")
    folder = tmp_path / "logs"
    folder.mkdir()

    assert validate_command(["python", str(script), "--check"]) == [
        "python",
        str(script),
        "--check",
    ]
    assert validate_command(["xdg-open", str(folder)]) == ["xdg-open", str(folder)]

    missing = tmp_path / "missing.py"
    with pytest.raises(CommandValidationError) as exc_info:
        validate_command(["python", str(missing)])
    assert exc_info.value.status_message == "Script nicht gefunden."


def test_validate_command_rejects_empty_or_invalid_items():
    with pytest.raises(CommandValidationError):
        validate_command([])
    with pytest.raises(CommandValidationError):
        validate_command("python job.py")
    with pytest.raises(CommandValidationError):
        validate_command(["python", ""])


def test_execute_command_preserves_stdout_precedence_and_exit_code(tmp_path):
    script = tmp_path / "job.py"
    script.write_text("print('ok')\n", encoding="utf-8")
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=3, stdout=" result \n", stderr="ignored")

    result = execute_command(["python", str(script)], run=fake_run)

    assert result.command == ["python", str(script)]
    assert result.output == "result"
    assert result.return_code == 3
    assert calls[0][1] == {
        "capture_output": True,
        "text": True,
        "check": False,
    }


def test_execute_command_uses_fallback_for_empty_output(tmp_path):
    script = tmp_path / "job.sh"
    script.write_text("#!/bin/sh\n", encoding="utf-8")

    result = execute_command(
        ["bash", str(script)],
        run=lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout="",
            stderr="",
        ),
    )

    assert result.output == "Keine Ausgabe erhalten."
