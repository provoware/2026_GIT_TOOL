#!/usr/bin/env python3
"""Log-Export: Logdateien bündeln und als ZIP ablegen."""

from __future__ import annotations

import argparse
import logging
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class LogExportConfig:
    logs_dir: Path
    export_dir: Path


class LogExportError(Exception):
    """Fehler beim Log-Export."""


def _ensure_path(path: Path, label: str) -> None:
    if not isinstance(path, Path):
        raise LogExportError(f"{label} ist kein Pfad (Path).")


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def list_log_files(logs_dir: Path) -> List[Path]:
    _ensure_path(logs_dir, "logs_dir")
    if not logs_dir.exists():
        raise LogExportError(f"Log-Ordner fehlt: {logs_dir}")
    if not logs_dir.is_dir():
        raise LogExportError(f"Log-Pfad ist kein Ordner: {logs_dir}")

    files = [path for path in logs_dir.iterdir() if path.is_file()]
    if not files:
        raise LogExportError("Keine Logdateien gefunden.")
    return sorted(files)


def build_export_path(export_dir: Path, base_name: str) -> Path:
    _ensure_path(export_dir, "export_dir")
    export_dir.mkdir(parents=True, exist_ok=True)
    candidate = export_dir / f"{base_name}.zip"
    counter = 1
    while candidate.exists():
        candidate = export_dir / f"{base_name}_{counter}.zip"
        counter += 1
    return candidate


def export_logs(logs_dir: Path, export_dir: Path) -> Path:
    _ensure_path(logs_dir, "logs_dir")
    _ensure_path(export_dir, "export_dir")
    files = list_log_files(logs_dir)
    export_path = build_export_path(export_dir, f"logs_export_{_timestamp()}")

    with zipfile.ZipFile(export_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for log_file in files:
            archive.write(log_file, arcname=log_file.relative_to(logs_dir))

    if not export_path.exists():
        raise LogExportError("Log-Export konnte nicht erstellt werden.")
    return export_path


def setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Exportiert Logdateien als ZIP-Archiv.",
    )
    parser.add_argument(
        "--logs-dir",
        type=Path,
        default=Path("logs"),
        help="Ordner mit Logdateien (Standard: logs).",
    )
    parser.add_argument(
        "--export-dir",
        type=Path,
        default=Path("data/log_exports"),
        help="Zielordner für Exporte (Standard: data/log_exports).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug-Modus aktivieren.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.debug)

    config = LogExportConfig(logs_dir=args.logs_dir, export_dir=args.export_dir)
    try:
        export_path = export_logs(config.logs_dir, config.export_dir)
    except LogExportError as exc:
        logging.error("Log-Export fehlgeschlagen: %s", exc)
        return 2

    logging.info("Log-Export erstellt: %s", export_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
