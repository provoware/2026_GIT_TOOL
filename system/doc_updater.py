#!/usr/bin/env python3
"""Doku-Autoupdater: aktualisiert Statusblöcke in README/DEV_DOKU."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from config_utils import ensure_path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
START_MARKER = "<!-- AUTO-STATUS:START -->"
END_MARKER = "<!-- AUTO-STATUS:END -->"


class DocUpdaterError(ValueError):
    """Fehler beim Doku-Update."""


@dataclass(frozen=True)
class ProgressStats:
    stand: str
    total: int
    done: int
    open: int
    percent: str


def _parse_progress(progress_path: Path) -> ProgressStats:
    ensure_path(progress_path, "progress_path", DocUpdaterError)
    if not progress_path.exists():
        raise DocUpdaterError(f"PROGRESS.md fehlt: {progress_path}")
    content = progress_path.read_text(encoding="utf-8")
    stand_match = re.search(r"Stand:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", content)
    if not stand_match:
        raise DocUpdaterError("PROGRESS.md enthält kein gültiges Stand-Datum.")
    patterns = {
        "total": r"- Gesamt:\s*(\d+)",
        "done": r"- Erledigt:\s*(\d+)",
        "open": r"- Offen:\s*(\d+)",
        "percent": r"- Fortschritt:\s*([0-9.,]+ %)",
    }
    data: Dict[str, str] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if not match:
            raise DocUpdaterError(f"PROGRESS.md enthält kein Feld für {key}.")
        data[key] = match.group(1).strip()
    return ProgressStats(
        stand=stand_match.group(1),
        total=int(data["total"]),
        done=int(data["done"]),
        open=int(data["open"]),
        percent=data["percent"],
    )


def _build_status_block(stats: ProgressStats) -> str:
    lines = [
        START_MARKER,
        f"**Auto-Status (aktualisiert: {stats.stand})**",
        "",
        f"- Gesamt: {stats.total} Tasks",
        f"- Erledigt: {stats.done} Tasks",
        f"- Offen: {stats.open} Tasks",
        f"- Fortschritt: {stats.percent}",
        END_MARKER,
    ]
    return "\n".join(lines)


def _update_file(path: Path, block: str, write: bool) -> bool:
    ensure_path(path, "path", DocUpdaterError)
    if not path.exists():
        raise DocUpdaterError(f"Datei fehlt: {path}")
    content = path.read_text(encoding="utf-8")
    if START_MARKER not in content or END_MARKER not in content:
        raise DocUpdaterError(f"Auto-Status-Marker fehlen in: {path}")
    before, rest = content.split(START_MARKER, 1)
    _, after = rest.split(END_MARKER, 1)
    updated = before.rstrip() + "\n\n" + block + "\n\n" + after.lstrip()
    if updated == content:
        return False
    if write:
        path.write_text(updated, encoding="utf-8")
    return True


def update_docs(root: Path, write: bool) -> List[Path]:
    ensure_path(root, "root", DocUpdaterError)
    progress_path = root / "PROGRESS.md"
    stats = _parse_progress(progress_path)
    block = _build_status_block(stats)
    targets = [root / "README.md", root / "DEV_DOKU.md"]
    changed: List[Path] = []
    for target in targets:
        if _update_file(target, block, write=write):
            changed.append(target)
    return changed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aktualisiert Auto-Status-Blöcke in README und DEV_DOKU.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Projekt-Root (Standard: Repository-Wurzel).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Änderungen tatsächlich schreiben (sonst nur prüfen).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        changed = update_docs(args.root, write=args.write)
    except DocUpdaterError as exc:
        print(f"Doku-Update fehlgeschlagen: {exc}")
        return 2
    if changed and args.write:
        print("Doku aktualisiert:")
        for path in changed:
            print(f"- {path}")
    elif changed:
        print("Doku kann aktualisiert werden (nutze --write).")
    else:
        print("Doku ist bereits aktuell.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
