#!/usr/bin/env python3
"""UI-unabhängige Autosave- und Shutdown-Orchestrierung."""

from __future__ import annotations

import logging
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
        if not config.enabled:
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
