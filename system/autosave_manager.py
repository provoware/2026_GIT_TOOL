#!/usr/bin/env python3
"""Autosave-Manager: zeitgesteuerte Sicherungen + Log-Einträge."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from zipfile import ZIP_DEFLATED, ZipFile

from config_utils import ensure_path, load_json


class AutosaveError(Exception):
    """Allgemeiner Fehler für den Autosave-Manager."""


@dataclass(frozen=True)
class AutosaveConfig:
    enabled: bool
    interval_minutes: int


@dataclass(frozen=True)
class AutosaveResult:
    archive_path: Path
    timestamp: datetime
    saved_files: List[str]

    @property
    def summary(self) -> str:
        file_count = len(self.saved_files)
        return f"Autosave erstellt ({file_count} Datei(en)): {self.archive_path.name}"


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise AutosaveError(f"{label} ist kein boolescher Wert.")
    return value


def _require_int_min(value: object, label: str, minimum: int) -> int:
    if not isinstance(value, int):
        raise AutosaveError(f"{label} ist keine Zahl.")
    if value < minimum:
        raise AutosaveError(f"{label} muss mindestens {minimum} sein.")
    return value


def load_autosave_config(config_path: Path) -> AutosaveConfig:
    ensure_path(config_path, "config_path", AutosaveError)
    data = load_json(
        config_path,
        AutosaveError,
        "Autosave-Konfiguration fehlt",
        "Autosave-Konfiguration ungültig",
    )
    autosave = data.get("autosave", {})
    if not isinstance(autosave, dict):
        raise AutosaveError("autosave ist kein Objekt (dict).")
    enabled = _require_bool(autosave.get("enabled", False), "autosave.enabled")
    interval = _require_int_min(
        autosave.get("interval_minutes", 10), "autosave.interval_minutes", 1
    )
    return AutosaveConfig(enabled=enabled, interval_minutes=interval)


def _list_data_files(data_root: Path, autosave_dir: Path) -> List[Path]:
    if not data_root.exists():
        return []
    files: List[Path] = []
    for path in data_root.rglob("*"):
        if path.is_dir():
            continue
        if autosave_dir in path.parents:
            continue
        files.append(path)
    return sorted(files)


def _write_state(path: Path, result: AutosaveResult) -> None:
    ensure_path(path, "state_path", AutosaveError)
    payload = {
        "last_run": result.timestamp.isoformat(),
        "archive": str(result.archive_path),
        "files": list(result.saved_files),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_log(log_path: Path, message: str) -> None:
    ensure_path(log_path, "log_path", AutosaveError)
    if not isinstance(message, str) or not message.strip():
        raise AutosaveError("Autosave-Logtext fehlt oder ist leer.")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with log_path.open("a", encoding="utf-8", errors="replace") as handle:
        handle.write(f"{timestamp} | {message}\n")


def _build_archive_name(timestamp: datetime) -> str:
    if not isinstance(timestamp, datetime):
        raise AutosaveError("timestamp ist kein datetime.")
    return f"autosave_{timestamp.strftime('%Y%m%d_%H%M%S')}.zip"


def create_autosave(
    data_root: Path,
    logs_root: Path,
    logger: logging.Logger,
) -> AutosaveResult:
    ensure_path(data_root, "data_root", AutosaveError)
    ensure_path(logs_root, "logs_root", AutosaveError)
    if not isinstance(logger, logging.Logger):
        raise AutosaveError("logger ist kein Logger.")

    autosave_dir = data_root / "autosave"
    autosave_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc)
    archive_path = autosave_dir / _build_archive_name(timestamp)
    files = _list_data_files(data_root, autosave_dir)
    saved_files: List[str] = []

    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        for file_path in files:
            relative = file_path.relative_to(data_root)
            archive.write(file_path, arcname=str(relative))
            saved_files.append(str(relative))

    if not archive_path.exists():
        raise AutosaveError("Autosave-Archiv konnte nicht erstellt werden.")

    result = AutosaveResult(archive_path=archive_path, timestamp=timestamp, saved_files=saved_files)
    _write_state(data_root / "autosave_state.json", result)
    _append_log(logs_root / "autosave.log", result.summary)
    logger.info(result.summary)
    return result


def schedule_next_autosave(
    interval_minutes: int,
    schedule_func: callable,
    callback: callable,
) -> None:
    if not isinstance(interval_minutes, int):
        raise AutosaveError("interval_minutes ist keine Zahl.")
    if interval_minutes < 1:
        raise AutosaveError("interval_minutes muss mindestens 1 sein.")
    if not callable(schedule_func):
        raise AutosaveError("schedule_func ist nicht aufrufbar.")
    if not callable(callback):
        raise AutosaveError("callback ist nicht aufrufbar.")
    schedule_func(interval_minutes * 60 * 1000, callback)
