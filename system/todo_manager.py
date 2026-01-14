#!/usr/bin/env python3
"""To-Do Verwaltung: Fortschritt berechnen und erledigte Einträge archivieren."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Tuple

from config_utils import ensure_path
from logging_center import setup_logging as setup_logging_center

CONFIG_DEFAULT = Path(__file__).resolve().parents[1] / "config" / "todo_config.json"


@dataclass(frozen=True)
class TodoConfig:
    todo_path: Path
    archive_path: Path


@dataclass(frozen=True)
class Progress:
    total: int
    done: int

    @property
    def percent(self) -> float:
        if self.total <= 0:
            return 0.0
        return round((self.done / self.total) * 100.0, 2)


class TodoError(Exception):
    """Allgemeiner Fehler für die To-Do-Verwaltung."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _format_percent(value: float) -> str:
    if not isinstance(value, (int, float)):
        raise TodoError("Prozentwert ist keine Zahl.")
    return f"{value:.2f}".replace(".", ",")


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise TodoError(f"Konfiguration fehlt: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TodoError(f"Konfiguration ist kein gültiges JSON: {path}") from exc


def load_config(config_path: Path | None = None) -> TodoConfig:
    config_file = config_path or CONFIG_DEFAULT
    ensure_path(config_file, "config_path", TodoError)
    data = _load_json(config_file)
    todo_path = Path(data.get("todo_path", "todo.txt"))
    archive_path = Path(data.get("archive_path", "data/todo_archive.txt"))
    return TodoConfig(todo_path=todo_path, archive_path=archive_path)


def read_todo_lines(todo_path: Path) -> List[str]:
    ensure_path(todo_path, "todo_path", TodoError)
    if not todo_path.exists():
        raise TodoError(f"To-Do-Datei nicht gefunden: {todo_path}")
    return todo_path.read_text(encoding="utf-8").splitlines(keepends=True)


def write_todo_lines(todo_path: Path, lines: Iterable[str]) -> None:
    ensure_path(todo_path, "todo_path", TodoError)
    todo_path.write_text("".join(lines), encoding="utf-8")


def parse_status(line: str) -> Tuple[bool, bool]:
    if not line.startswith("["):
        return False, False
    if line.startswith("[x]") or line.startswith("[X]"):
        return True, True
    if line.startswith("[ ]"):
        return True, False
    return False, False


def calculate_progress(lines: Iterable[str]) -> Progress:
    total = 0
    done = 0
    for line in lines:
        is_task, is_done = parse_status(line.strip())
        if not is_task:
            continue
        total += 1
        if is_done:
            done += 1
    return Progress(total=total, done=done)


def build_progress_report(progress: Progress, reference_date: str | None = None) -> str:
    if not isinstance(progress, Progress):
        raise TodoError("progress ist kein Progress-Objekt.")
    if reference_date is None:
        reference_date = datetime.now(timezone.utc).date().isoformat()
    else:
        try:
            datetime.fromisoformat(reference_date)
        except ValueError as exc:
            raise TodoError("Stand-Datum ist ungültig. Erwartet: JJJJ-MM-TT.") from exc

    open_tasks = max(progress.total - progress.done, 0)
    percent_text = _format_percent(progress.percent)
    return "\n".join(
        [
            "# PROGRESS",
            "",
            f"Stand: {reference_date}",
            "",
            f"- Gesamt: {progress.total} Tasks",
            f"- Erledigt: {progress.done} Tasks",
            f"- Offen: {open_tasks} Tasks",
            f"- Fortschritt: {percent_text} %",
            "",
        ]
    )


def write_progress_report(progress: Progress, progress_path: Path) -> None:
    ensure_path(progress_path, "progress_path", TodoError)
    report = build_progress_report(progress)
    progress_path.write_text(report, encoding="utf-8")
    if not progress_path.exists():
        raise TodoError("PROGRESS.md konnte nicht geschrieben werden.")


def archive_completed_tasks(todo_path: Path, archive_path: Path) -> Tuple[int, int]:
    ensure_path(todo_path, "todo_path", TodoError)
    ensure_path(archive_path, "archive_path", TodoError)

    lines = read_todo_lines(todo_path)
    remaining: List[str] = []
    archived: List[str] = []

    for line in lines:
        is_task, is_done = parse_status(line.strip())
        if is_task and is_done:
            archived.append(f"{line.rstrip()} | archiviert: {_utc_now_iso()}\n")
        else:
            remaining.append(line)

    if archived:
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        if not archive_path.exists():
            archive_path.write_text("# Archiv für erledigte To-Dos\n", encoding="utf-8")
        with archive_path.open("a", encoding="utf-8") as handle:
            handle.writelines(archived)

    write_todo_lines(todo_path, remaining)
    return len(archived), len(remaining)


def setup_logging(debug: bool) -> None:
    setup_logging_center(debug)


def run_progress(config: TodoConfig, progress_path: Path | None = None) -> int:
    lines = read_todo_lines(config.todo_path)
    progress = calculate_progress(lines)
    logging.info(
        "Fortschritt: %s%% (erledigt: %s von %s)",
        f"{progress.percent:.2f}",
        progress.done,
        progress.total,
    )
    if progress_path is not None:
        write_progress_report(progress, progress_path)
        logging.info("PROGRESS.md aktualisiert: %s", progress_path)
    return 0


def run_archive(config: TodoConfig) -> int:
    archived, remaining = archive_completed_tasks(config.todo_path, config.archive_path)
    logging.info("Archiviert: %s Einträge", archived)
    logging.info("Offen: %s Einträge", remaining)
    if archived == 0:
        logging.info("Keine erledigten Einträge gefunden.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="To-Do Verwaltung (Fortschritt berechnen und Archivierung durchführen)",
    )
    parser.add_argument("--config", type=Path, default=None, help="Pfad zur Konfiguration (JSON)")
    parser.add_argument("--debug", action="store_true", help="Debug-Modus aktivieren")
    sub = parser.add_subparsers(dest="command", required=True)
    progress_parser = sub.add_parser("progress", help="Fortschritt aus todo.txt berechnen")
    progress_parser.add_argument(
        "--write-progress",
        action="store_true",
        help="Schreibt einen PROGRESS-Bericht (PROGRESS.md).",
    )
    progress_parser.add_argument(
        "--progress-path",
        type=Path,
        default=None,
        help="Zielpfad für PROGRESS.md (Standard: PROGRESS.md).",
    )
    sub.add_parser("archive", help="Erledigte Einträge aus todo.txt archivieren")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.debug)

    try:
        config = load_config(args.config)
    except TodoError as exc:
        logging.error("Konfiguration nicht geladen: %s", exc)
        return 2

    if args.command == "progress":
        progress_path = None
        if getattr(args, "write_progress", False):
            progress_path = args.progress_path or Path("PROGRESS.md")
        return run_progress(config, progress_path)
    if args.command == "archive":
        return run_archive(config)

    logging.error("Unbekannter Befehl.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
