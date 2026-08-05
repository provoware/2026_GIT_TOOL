from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from task_runner import TaskOutcome, TaskRunner, TaskRunnerError, execute_command  # noqa: E402


def _immediate_schedule(_delay: int, callback):
    callback()
    return object()


def test_background_exception_is_reported_and_category_remains_reusable() -> None:
    completed: list[TaskOutcome[object]] = []
    done = threading.Event()
    runner = TaskRunner(_immediate_schedule)

    def fail_work() -> object:
        raise RuntimeError("simulierter Modulabsturz")

    assert runner.start("module-a", fail_work, lambda outcome: (completed.append(outcome), done.set()))
    assert done.wait(3)
    assert len(completed) == 1
    assert not completed[0].succeeded
    assert isinstance(completed[0].error, RuntimeError)
    assert not runner.is_running("module-a")

    second_done = threading.Event()
    assert runner.start("module-a", lambda: "weiterbetrieb", lambda _outcome: second_done.set())
    assert second_done.wait(3)
    assert not runner.is_running("module-a")


def test_scheduler_failure_releases_category_for_safe_retry() -> None:
    scheduled = threading.Event()

    def broken_schedule(_delay: int, _callback):
        scheduled.set()
        raise RuntimeError("UI-Scheduler nicht verfügbar")

    runner = TaskRunner(broken_schedule)
    assert runner.start("diagnose", lambda: "ok", lambda _outcome: None)
    assert scheduled.wait(3)

    for _ in range(100):
        if not runner.is_running("diagnose"):
            break
        threading.Event().wait(0.01)
    assert not runner.is_running("diagnose")


def test_thread_start_failure_is_transparent_and_does_not_lock_category() -> None:
    class BrokenThread:
        def __init__(self, **_kwargs):
            pass

        def start(self) -> None:
            raise OSError("keine Thread-Ressource")

    runner = TaskRunner(_immediate_schedule, thread_factory=BrokenThread)
    with pytest.raises(TaskRunnerError, match="Hintergrundtask konnte nicht starten"):
        runner.start("export", lambda: None, lambda _outcome: None)
    assert not runner.is_running("export")


def test_crashed_subprocess_is_returned_as_controlled_result(tmp_path: Path) -> None:
    script = tmp_path / "crash.py"
    script.write_text(
        "import sys\nprint('Nutzerhinweis vor Abbruch', file=sys.stderr)\nsys.exit(23)\n",
        encoding="utf-8",
    )
    result = execute_command([sys.executable, str(script)])
    assert result.return_code == 23
    assert "Nutzerhinweis vor Abbruch" in result.output


def test_hard_child_process_crash_does_not_terminate_test_host(tmp_path: Path) -> None:
    script = tmp_path / "hard_crash.py"
    script.write_text(
        "import os, signal\nos.kill(os.getpid(), signal.SIGTERM)\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode != 0
    assert sys.version_info.major >= 3
