#!/usr/bin/env python3
"""Dateinamen-Fixer: korrigiert automatisch nicht-konforme Dateinamen."""

from __future__ import annotations

import argparse
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from config_utils import ensure_path


class FilenameFixerError(Exception):
    """Allgemeiner Fehler für die Dateinamenkorrektur."""


@dataclass(frozen=True)
class RenameAction:
    source: Path
    target: Path


VALID_NAME = re.compile(r"^[a-z0-9_]+$")


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FilenameFixerError(f"{label} fehlt oder ist leer.")
    return value.strip()


def is_snake_case(name: str) -> bool:
    clean_name = _require_text(name, "name")
    return bool(VALID_NAME.match(clean_name))


def normalize_segment(segment: str) -> str:
    clean = _require_text(segment, "segment")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", clean)
    cleaned = cleaned.strip("_").lower()
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned or "datei"


def normalize_filename(path: Path) -> Path:
    ensure_path(path, "path", FilenameFixerError)
    stem = normalize_segment(path.stem)
    suffixes = "".join(path.suffixes).lower()
    return path.with_name(f"{stem}{suffixes}")


def resolve_target(path: Path, candidate: Path) -> Path:
    if candidate == path:
        return candidate
    counter = 1
    target = candidate
    while target.exists():
        target = candidate.with_name(f"{candidate.stem}_{counter}{candidate.suffix}")
        counter += 1
    return target


def collect_targets(root: Path, folders: Iterable[Path]) -> List[Path]:
    ensure_path(root, "root", FilenameFixerError)
    targets: List[Path] = []
    for folder in folders:
        ensure_path(folder, "folder", FilenameFixerError)
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                targets.append(path)
    return targets


def build_rename_actions(paths: Iterable[Path]) -> List[RenameAction]:
    actions: List[RenameAction] = []
    for path in paths:
        if not path.name:
            continue
        if path.name.startswith("."):
            continue
        candidate = normalize_filename(path)
        if candidate.name == path.name:
            continue
        target = resolve_target(path, candidate)
        actions.append(RenameAction(source=path, target=target))
    return actions


def apply_actions(actions: Iterable[RenameAction], dry_run: bool) -> List[str]:
    results: List[str] = []
    for action in actions:
        if dry_run:
            results.append(f"Geplant: {action.source} -> {action.target}")
        else:
            action.target.parent.mkdir(parents=True, exist_ok=True)
            action.source.rename(action.target)
            results.append(f"Korrigiert: {action.source} -> {action.target}")
    return results


def run_fix(root: Path, dry_run: bool) -> List[str]:
    ensure_path(root, "root", FilenameFixerError)
    target_dirs = [root / "data", root / "logs"]
    paths = collect_targets(root, target_dirs)
    actions = build_rename_actions(paths)
    return apply_actions(actions, dry_run)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dateinamen-Korrektur: macht Namen linux-konform (snake_case).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Projektwurzel (Pfad zum Repo).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur anzeigen, nichts umbenennen.",
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
    actions = run_fix(args.root, args.dry_run)
    if not actions:
        logging.info("Dateinamen-Korrektur: keine Anpassungen nötig.")
        return 0
    for line in actions:
        logging.info(line)
    logging.info("Dateinamen-Korrektur: %s Anpassung(en) abgeschlossen.", len(actions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
