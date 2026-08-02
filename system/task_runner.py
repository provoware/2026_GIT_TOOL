#!/usr/bin/env python3
"""UI-unabhängige Ausführung kategorisierter Hintergrundaufgaben."""

from __future__ import annotations

import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Generic, List, Optional, Sequence, TypeVar


T = TypeVar("T")


class TaskRunnerError(ValueError):
    """Ungültige Task-Konfiguration oder fehlgeschlagener Thread-Start."""


class CommandValidationError(TaskRunnerError):
    """Benutzerfreundlicher Validierungsfehler für Wartungskommandos."""

    def __init__(self, message: str, status_message: str) -> None:
        super().__init__(message)
        self.status_message = status_message


@dataclass(frozen=True)
class TaskOutcome(Generic[T]):
    category: str
    value: Optional[T] = None
    error: Optional[Exception] = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


@dataclass(frozen=True)
class CommandResult:
    command: List[str]
    output: str
    return_code: int


class TaskRunner:
    """Startet pro Kategorie höchstens einen Task und marshalt Ergebnisse zur UI."""

    def __init__(
        self,
        schedule: Callable[[int, Callable[[], None]], object],
        thread_factory: Callable[..., object] = threading.Thread,
    ) -> None:
        if not callable(schedule):
            raise TaskRunnerError("UI-Scheduler ist nicht aufrufbar.")
        if not callable(thread_factory):
            raise TaskRunnerError("Thread-Factory ist nicht aufrufbar.")
        self._schedule = schedule
        self._thread_factory = thread_factory
        self._active: set[str] = set()
        self._lock = threading.Lock()

    def is_running(self, category: str) -> bool:
        clean_category = _require_text(category, "category")
        with self._lock:
            return clean_category in self._active

    def start(
        self,
        category: str,
        work: Callable[[], T],
        on_complete: Callable[[TaskOutcome[T]], None],
    ) -> bool:
        clean_category = _require_text(category, "category")
        if not callable(work):
            raise TaskRunnerError("Task-Arbeit ist nicht aufrufbar.")
        if not callable(on_complete):
            raise TaskRunnerError("Abschluss-Callback ist nicht aufrufbar.")

        with self._lock:
            if clean_category in self._active:
                return False
            self._active.add(clean_category)

        def worker() -> None:
            try:
                value = work()
                outcome: TaskOutcome[T] = TaskOutcome(
                    category=clean_category,
                    value=value,
                )
            except Exception as exc:
                outcome = TaskOutcome(category=clean_category, error=exc)

            try:
                self._schedule(
                    0,
                    lambda: self._complete(clean_category, outcome, on_complete),
                )
            except Exception:
                self._release(clean_category)

        try:
            thread = self._thread_factory(target=worker, daemon=True)
            thread.start()
        except Exception as exc:
            self._release(clean_category)
            raise TaskRunnerError(f"Hintergrundtask konnte nicht starten: {exc}") from exc
        return True

    def _complete(
        self,
        category: str,
        outcome: TaskOutcome[T],
        on_complete: Callable[[TaskOutcome[T]], None],
    ) -> None:
        self._release(category)
        on_complete(outcome)

    def _release(self, category: str) -> None:
        with self._lock:
            self._active.discard(category)


def validate_command(command: Sequence[str]) -> List[str]:
    if isinstance(command, (str, bytes)) or not isinstance(command, Sequence):
        raise CommandValidationError(
            "Maintenance-Kommando ist ungültig.",
            "Kommando ist ungültig.",
        )
    clean_command: List[str] = []
    for item in command:
        if not isinstance(item, str) or not item.strip():
            raise CommandValidationError(
                "Maintenance-Kommando ist ungültig.",
                "Kommando ist ungültig.",
            )
        clean_command.append(item.strip())
    if not clean_command:
        raise CommandValidationError(
            "Maintenance-Kommando ist leer.",
            "Kommando ist ungültig.",
        )

    executable = clean_command[0]
    if executable in {"bash", "python", "python3", "xdg-open"}:
        if len(clean_command) < 2:
            raise CommandValidationError(
                "Maintenance-Kommando enthält keinen Zielpfad.",
                "Kommando ist ungültig.",
            )
        target = Path(clean_command[1])
        if not target.exists():
            if executable == "xdg-open":
                raise CommandValidationError(
                    f"Pfad {target} fehlt.",
                    "Pfad nicht gefunden.",
                )
            raise CommandValidationError(
                f"Script {target} fehlt.",
                "Script nicht gefunden.",
            )
    return clean_command


def execute_command(
    command: Sequence[str],
    run: Callable[..., object] = subprocess.run,
) -> CommandResult:
    clean_command = validate_command(command)
    if not callable(run):
        raise TaskRunnerError("Prozess-Runner ist nicht aufrufbar.")
    result = run(
        clean_command,
        capture_output=True,
        text=True,
        check=False,
    )
    return_code = getattr(result, "returncode", None)
    if not isinstance(return_code, int):
        raise TaskRunnerError("Prozess-Ergebnis enthält keinen gültigen Exit-Code.")
    stdout = getattr(result, "stdout", "")
    stderr = getattr(result, "stderr", "")
    stdout_text = stdout.strip() if isinstance(stdout, str) else ""
    stderr_text = stderr.strip() if isinstance(stderr, str) else ""
    output = stdout_text or stderr_text or "Keine Ausgabe erhalten."
    return CommandResult(
        command=clean_command,
        output=output,
        return_code=return_code,
    )


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TaskRunnerError(f"{label} fehlt oder ist leer.")
    return value.strip()
