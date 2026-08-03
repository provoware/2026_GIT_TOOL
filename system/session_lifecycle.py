#!/usr/bin/env python3
"""UI-unabhängige Autosave- und Shutdown-Orchestrierung."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import autosave_manager
import backup_center


class SessionLifecycleError(ValueError):
    """Ungültige Lifecycle-Konfiguration oder Scheduler-Verwendung."""


@dataclass(frozen=True)
class ShutdownOutcome:
    report: str
    success: bool


def write_mode_allows_changes() -> bool:
    return os.environ.get("GENREARCHIV_WRITE_MODE", "normal").strip().lower() != "read-only"


class AutosaveSession:
    """Verwaltet genau einen geplanten Autosave-Job und dessen Abbruch."""

    def __init__(
        self,
        schedule: Callable[[int, Callable[[], None]], object],
        cancel: Callable[[object], None],
        callback: Callable[[], None],
    ) -> None:
        if not callable(schedule):
            raise SessionLifecycleError("Autosave-Scheduler ist nicht aufrufbar.")
        if not callable(cancel):
            raise SessionLifecycleError("Autosave-Abbruch ist nicht aufrufbar.")
        if not callable(callback):
            raise SessionLifecycleError("Autosave-Callback ist nicht aufrufbar.")
        self._schedule = schedule
        self._cancel = cancel
        self._callback = callback
        self._config: Optional[autosave_manager.AutosaveConfig] = None
        self._job_id: object | None = None
        self._active = False

    @property
    def job_id(self) -> object | None:
        return self._job_id

    @property
    def active(self) -> bool:
        return self._active

    def start(self, config: autosave_manager.AutosaveConfig) -> bool:
        if not isinstance(config, autosave_manager.AutosaveConfig):
            raise SessionLifecycleError("Autosave-Konfiguration ist ungültig.")
        self.cancel()
        self._config = config
        if not config.enabled or not write_mode_allows_changes():
            self._active = False
            return False
        self._active = True
        self._schedule_next()
        return True

    def cancel(self) -> bool:
        self._active = False
        job_id = self._job_id
        self._job_id = None
        if job_id is None:
            return False
        try:
            self._cancel(job_id)
        except Exception:
            return False
        return True

    def _schedule_next(self) -> None:
        if not self._active or self._config is None:
            return
        delay_ms = self._config.interval_minutes * 60 * 1000
        self._job_id = self._schedule(delay_ms, self._run_scheduled)

    def _run_scheduled(self) -> None:
        self._job_id = None
        if not self._active:
            return
        try:
            self._callback()
        finally:
            self._schedule_next()


def run_shutdown_sequence(
    *,
    autosave_config: autosave_manager.AutosaveConfig | None,
    data_root: Path,
    logs_root: Path,
    logger: logging.Logger,
    backup_config_path: Path,
    backup_state_path: Path,
    create_autosave: Callable[..., autosave_manager.AutosaveResult] = autosave_manager.create_autosave,
    load_backup_config: Callable[[Path], backup_center.BackupConfig] = backup_center.load_backup_config,
    create_backup: Callable[[backup_center.BackupConfig, Path], backup_center.BackupResult] = backup_center.create_backup,
) -> ShutdownOutcome:
    """Erstellt die Logout-Sicherungen und liefert ein deterministisches Ergebnis."""

    for value, label in (
        (data_root, "data_root"),
        (logs_root, "logs_root"),
        (backup_config_path, "backup_config_path"),
        (backup_state_path, "backup_state_path"),
    ):
        if not isinstance(value, Path):
            raise SessionLifecycleError(f"{label} ist kein Pfad (Path).")
    if not isinstance(logger, logging.Logger):
        raise SessionLifecycleError("logger ist kein Logger.")

    if not write_mode_allows_changes():
        return ShutdownOutcome(
            report=(
                "Abmelden: Sicherung und sauberes Schließen\n"
                "Hinweis: Schreibgeschützter Modus ist aktiv.\n"
                "Autosave und Backup wurden ohne Schreibzugriff übersprungen.\n"
            ),
            success=True,
        )

    report_lines = ["Abmelden: Sicherung und sauberes Schließen"]
    success = True

    if autosave_config is not None and autosave_config.enabled:
        try:
            result = create_autosave(data_root, logs_root, logger)
            report_lines.append(f"Erfolg: {result.summary}")
        except autosave_manager.AutosaveError as exc:
            success = False
            report_lines.extend(
                [
                    "Fehler: Autosave fehlgeschlagen.",
                    f"Ursache: {exc}",
                    "Lösung: logs/autosave.log prüfen oder Safe-Mode nutzen.",
                ]
            )
    else:
        report_lines.extend(
            [
                "Hinweis: Autosave ist deaktiviert.",
                (
                    "Lösung: In config/global_settings.json aktivieren, "
                    "wenn du Sicherungen willst."
                ),
            ]
        )

    try:
        backup_config = load_backup_config(backup_config_path)
        backup_result = create_backup(backup_config, backup_state_path)
        report_lines.append(f"Erfolg: {backup_result.summary}")
    except backup_center.BackupCenterError as exc:
        success = False
        report_lines.extend(
            [
                "Fehler: Backup fehlgeschlagen.",
                f"Ursache: {exc}",
                "Lösung: config/backup.json prüfen und erneut versuchen.",
            ]
        )

    return ShutdownOutcome(
        report="\n".join(report_lines).rstrip() + "\n",
        success=success,
    )


def complete_shutdown(
    outcome: ShutdownOutcome,
    *,
    append_report: Callable[[str], None],
    set_status: Callable[[str, str], None],
    cancel_autosave: Callable[[], object],
    schedule: Callable[[int, Callable[[], None]], object],
    destroy: Callable[[], None],
    delay_ms: int = 200,
) -> object:
    """Schließt die Sitzung geordnet ab und plant erst zuletzt die Zerstörung."""

    if not isinstance(outcome, ShutdownOutcome):
        raise SessionLifecycleError("Shutdown-Ergebnis ist ungültig.")
    for callback, label in (
        (append_report, "append_report"),
        (set_status, "set_status"),
        (cancel_autosave, "cancel_autosave"),
        (schedule, "schedule"),
        (destroy, "destroy"),
    ):
        if not callable(callback):
            raise SessionLifecycleError(f"{label} ist nicht aufrufbar.")
    if not isinstance(delay_ms, int) or delay_ms < 0:
        raise SessionLifecycleError("delay_ms ist ungültig.")

    if outcome.report:
        append_report(outcome.report)
    message = "Abmelden abgeschlossen." if outcome.success else "Abmelden mit Problemen."
    state = "success" if outcome.success else "error"
    set_status(message, state)
    cancel_autosave()
    return schedule(delay_ms, destroy)
