#!/usr/bin/env python3
"""Backup-Center: Vollständige Sicherungen als ZIP-Archiv."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List
from zipfile import ZIP_DEFLATED, ZipFile

from config_utils import ensure_path, load_json


class BackupCenterError(Exception):
    """Fehler im Backup-Center."""


@dataclass(frozen=True)
class BackupConfig:
    output_dir: Path
    sources: List[Path]
    exclude_dirs: List[str]
    max_backups: int


@dataclass(frozen=True)
class BackupResult:
    archive_path: Path
    timestamp: datetime
    file_count: int

    @property
    def summary(self) -> str:
        return f"Backup erstellt ({self.file_count} Datei(en)): {self.archive_path.name}"


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BackupCenterError(f"{label} fehlt oder ist leer.")
    return value.strip()


def _require_int(value: object, label: str, minimum: int) -> int:
    if not isinstance(value, int):
        raise BackupCenterError(f"{label} ist keine Zahl.")
    if value < minimum:
        raise BackupCenterError(f"{label} muss mindestens {minimum} sein.")
    return value


def _require_list(value: object, label: str) -> List:
    if not isinstance(value, list):
        raise BackupCenterError(f"{label} ist keine Liste.")
    return value


def load_backup_config(path: Path) -> BackupConfig:
    ensure_path(path, "config_path", BackupCenterError)
    data = load_json(
        path,
        BackupCenterError,
        "Backup-Konfiguration fehlt",
        "Backup-Konfiguration ungültig",
    )
    output_dir = Path(_require_text(data.get("output_dir"), "output_dir"))
    sources_raw = _require_list(data.get("sources"), "sources")
    sources = [Path(_require_text(item, "sources")) for item in sources_raw]
    exclude_raw = _require_list(data.get("exclude_dirs", []), "exclude_dirs")
    exclude_dirs = [_require_text(item, "exclude_dirs") for item in exclude_raw]
    max_backups = _require_int(data.get("max_backups", 5), "max_backups", 1)
    return BackupConfig(
        output_dir=output_dir,
        sources=sources,
        exclude_dirs=exclude_dirs,
        max_backups=max_backups,
    )


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _collect_files(sources: Iterable[Path], exclude_dirs: Iterable[str]) -> List[Path]:
    exclude_set = set(exclude_dirs)
    files: List[Path] = []
    for source in sources:
        if not source.exists():
            continue
        if source.is_file():
            files.append(source)
            continue
        for path in source.rglob("*"):
            if path.is_dir():
                continue
            if any(part in exclude_set for part in path.parts):
                continue
            files.append(path)
    return sorted(files)


def _cleanup_old_backups(output_dir: Path, max_backups: int) -> None:
    backups = sorted(output_dir.glob("backup_*.zip"))
    if len(backups) <= max_backups:
        return
    for path in backups[: len(backups) - max_backups]:
        path.unlink(missing_ok=True)


def create_backup(config: BackupConfig, state_path: Path) -> BackupResult:
    if not isinstance(config, BackupConfig):
        raise BackupCenterError("config ist keine BackupConfig.")
    ensure_path(state_path, "state_path", BackupCenterError)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc)
    archive_path = config.output_dir / f"backup_{_timestamp()}.zip"
    files = _collect_files(config.sources, config.exclude_dirs)
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        for file_path in files:
            archive.write(file_path, arcname=str(file_path))
    if not archive_path.exists():
        raise BackupCenterError("Backup-Archiv konnte nicht erstellt werden.")
    result = BackupResult(archive_path=archive_path, timestamp=timestamp, file_count=len(files))
    payload = {
        "last_backup": result.timestamp.isoformat(),
        "archive": str(result.archive_path),
        "file_count": result.file_count,
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    _cleanup_old_backups(config.output_dir, config.max_backups)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backup-Center: Vollständige Sicherung erstellen.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "config" / "backup.json",
        help="Pfad zur Backup-Konfiguration (JSON).",
    )
    parser.add_argument(
        "--state-path",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "backup_state.json",
        help="Pfad für den Backup-Status (JSON).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config = load_backup_config(args.config)
    try:
        result = create_backup(config, args.state_path)
    except BackupCenterError as exc:
        print(f"Fehler: {exc}")
        return 1
    print(result.summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
