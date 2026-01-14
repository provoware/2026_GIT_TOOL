#!/usr/bin/env python3
"""Struktur-Check: prüft Ordnertrennung und verbotene Dateitypen."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from config_utils import ensure_path


class StructureCheckError(Exception):
    """Fehler im Struktur-Check."""


@dataclass(frozen=True)
class StructureIssue:
    path: Path
    message: str


REQUIRED_DIRS = (
    "src",
    "system",
    "config",
    "data",
    "logs",
    "scripts",
    "modules",
    "tests",
)

CONFIG_DISALLOWED_SUFFIXES = {".py", ".sh", ".bat", ".ps1", ".exe"}
DATA_DISALLOWED_SUFFIXES = {".py", ".sh", ".bat", ".ps1", ".exe", ".toml", ".ini", ".yml", ".yaml"}
SYSTEM_DISALLOWED_SUFFIXES = {".log", ".csv", ".tsv"}


def _iter_files(folder: Path) -> Iterable[Path]:
    if not folder.exists():
        return []
    return (path for path in folder.rglob("*") if path.is_file())


def _collect_disallowed(
    folder: Path, disallowed_suffixes: set[str], label: str
) -> List[StructureIssue]:
    issues: List[StructureIssue] = []
    for path in _iter_files(folder):
        if path.suffix.lower() in disallowed_suffixes:
            issues.append(
                StructureIssue(
                    path=path,
                    message=(
                        f"{label}: Datei-Typ nicht erlaubt ({path.suffix}). "
                        "Bitte in den passenden Ordner verschieben."
                    ),
                )
            )
    return issues


def _check_required_dirs(root: Path) -> List[StructureIssue]:
    issues: List[StructureIssue] = []
    for entry in REQUIRED_DIRS:
        path = root / entry
        if not path.exists():
            issues.append(
                StructureIssue(
                    path=path,
                    message=(
                        "Pflichtordner fehlt. "
                        "Bitte bootstrap.sh ausführen oder Ordner manuell anlegen."
                    ),
                )
            )
        elif not path.is_dir():
            issues.append(
                StructureIssue(
                    path=path,
                    message="Pfad ist kein Ordner. Bitte Struktur korrigieren.",
                )
            )
    return issues


def run_check(root: Path) -> List[StructureIssue]:
    ensure_path(root, "root", StructureCheckError)
    issues: List[StructureIssue] = []
    issues.extend(_check_required_dirs(root))
    issues.extend(_collect_disallowed(root / "config", CONFIG_DISALLOWED_SUFFIXES, "Config"))
    issues.extend(_collect_disallowed(root / "data", DATA_DISALLOWED_SUFFIXES, "Daten"))
    issues.extend(_collect_disallowed(root / "logs", DATA_DISALLOWED_SUFFIXES, "Logs"))
    issues.extend(_collect_disallowed(root / "system", SYSTEM_DISALLOWED_SUFFIXES, "Systemlogik"))
    issues.extend(_collect_disallowed(root / "src", SYSTEM_DISALLOWED_SUFFIXES, "Systemlogik"))
    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Struktur-Check: prüft Ordnertrennung (System/Config/Daten/Logs).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Projektwurzel (Pfad zum Repo).",
    )
    parser.add_argument("--debug", action="store_true", help="Debug-Modus aktivieren.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    issues = run_check(args.root)
    if issues:
        logging.error("Struktur-Check: %s Hinweis(e) gefunden.", len(issues))
        for issue in issues:
            logging.error("- %s (%s)", issue.message, issue.path)
        logging.error("Bitte Struktur laut standards.md korrigieren.")
        return 2
    logging.info("Struktur-Check: OK. Ordnertrennung ist eingehalten.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
