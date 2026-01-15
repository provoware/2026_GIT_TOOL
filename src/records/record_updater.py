from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, List

DATED_TASK_PATTERN = re.compile(
    r"^\[(?P<status>[ xX])\]\s+(?P<date>\d{4}-\d{2}-\d{2})\s+\|\s+"
    r"(?P<area>[^|]+?)\s+\|\s+(?P<title>[^|]+?)\s+\|"
)
ROUND_HEADER_PATTERN = re.compile(
    r"^Nächste 4 kleinste Aufgaben \\(Runde (?P<date>\d{4}-\d{2}-\d{2})\\)"
)
ROUND_TASK_PATTERN = re.compile(r"^\[(?P<status>[ xX])\]\s+(?P<text>.+)$")
DONE_ENTRY_PATTERN = re.compile(
    r"^-\s+\[x\]\s+(?P<date>\d{4}-\d{2}-\d{2})\s+\|\s+"
    r"(?P<area>[^|]+?)\s+\|\s+(?P<title>[^|]+?)\s*$"
)
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class TodoTask:
    status: str
    date: str
    area: str
    title: str
    raw_line: str

    @property
    def identifier(self) -> str:
        return f"{self.date}|{self.area}|{self.title}"

    @property
    def summary(self) -> str:
        return f"{self.area}: {self.title}"


@dataclass(frozen=True)
class UpdateResult:
    archived_tasks: List[TodoTask]
    removed_done_lines: int


@dataclass(frozen=True)
class RecordConfig:
    changelog_section_label: str
    changelog_entry_prefix: str
    done_entry_prefix: str


def load_config(config_path: Path) -> RecordConfig:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    config = RecordConfig(
        changelog_section_label=data["changelog_section_label"],
        changelog_entry_prefix=data["changelog_entry_prefix"],
        done_entry_prefix=data["done_entry_prefix"],
    )
    validate_config(config)
    return config


def validate_config(config: RecordConfig) -> None:
    if not config.changelog_section_label:
        raise ValueError("Konfiguration: Abschnittsname für Changelog fehlt.")
    if not config.changelog_entry_prefix:
        raise ValueError("Konfiguration: Prefix für Changelog-Einträge fehlt.")
    if not config.done_entry_prefix:
        raise ValueError("Konfiguration: Prefix für DONE-Einträge fehlt.")


def _parse_round_task(text: str, date: str, raw_line: str) -> TodoTask | None:
    stripped = text.strip()
    if not stripped:
        return None
    if "|" in stripped:
        stripped = stripped.split("|", 1)[0].strip()
    if ":" in stripped:
        area, title = stripped.split(":", 1)
        area = area.strip()
        title = title.strip()
    else:
        area = "Allgemein"
        title = stripped
    if not title:
        return None
    return TodoTask(status="", date=date, area=area, title=title, raw_line=raw_line)


def parse_todo_lines(lines: Iterable[str]) -> List[TodoTask]:
    tasks: List[TodoTask] = []
    current_round_date: str | None = None
    round_locked = False
    for line in lines:
        header_match = ROUND_HEADER_PATTERN.match(line.strip())
        if header_match:
            if not round_locked:
                current_round_date = header_match.group("date")
                round_locked = True
            else:
                current_round_date = None
            continue

        match = DATED_TASK_PATTERN.match(line)
        if match:
            tasks.append(
                TodoTask(
                    status=match.group("status"),
                    date=match.group("date"),
                    area=match.group("area").strip(),
                    title=match.group("title").strip(),
                    raw_line=line,
                )
            )
            continue

        if current_round_date:
            round_match = ROUND_TASK_PATTERN.match(line.strip())
            if round_match:
                task = _parse_round_task(round_match.group("text"), current_round_date, line)
                if task:
                    tasks.append(
                        TodoTask(
                            status=round_match.group("status"),
                            date=task.date,
                            area=task.area,
                            title=task.title,
                            raw_line=line,
                        )
                    )
    return tasks


def validate_tasks(tasks: Iterable[TodoTask]) -> None:
    for task in tasks:
        if not DATE_PATTERN.match(task.date):
            raise ValueError(f"Ungültiges Datum im To-Do: {task.date}. Erwartet: JJJJ-MM-TT.")
        if not task.area:
            raise ValueError("Bereich im To-Do darf nicht leer sein.")
        if not task.title:
            raise ValueError("Titel im To-Do darf nicht leer sein.")


def parse_done_entries(lines: Iterable[str]) -> set[str]:
    entries: set[str] = set()
    for line in lines:
        match = DONE_ENTRY_PATTERN.match(line)
        if match:
            identifier = (
                f"{match.group('date')}|{match.group('area').strip()}|"
                f"{match.group('title').strip()}"
            )
            entries.add(identifier)
    return entries


def archive_done_tasks(
    todo_lines: List[str], done_entries: set[str]
) -> tuple[List[str], List[TodoTask], int]:
    updated_todo_lines: List[str] = []
    archived_tasks: List[TodoTask] = []
    removed_done_lines = 0
    current_round_date: str | None = None
    round_locked = False

    for line in todo_lines:
        header_match = ROUND_HEADER_PATTERN.match(line.strip())
        if header_match:
            if not round_locked:
                current_round_date = header_match.group("date")
                round_locked = True
            else:
                current_round_date = None
            updated_todo_lines.append(line)
            continue

        match = DATED_TASK_PATTERN.match(line)
        if match:
            task = TodoTask(
                status=match.group("status"),
                date=match.group("date"),
                area=match.group("area").strip(),
                title=match.group("title").strip(),
                raw_line=line,
            )
        else:
            task = None
            if current_round_date:
                round_match = ROUND_TASK_PATTERN.match(line.strip())
                if round_match:
                    task = _parse_round_task(round_match.group("text"), current_round_date, line)
                    if task:
                        task = TodoTask(
                            status=round_match.group("status"),
                            date=task.date,
                            area=task.area,
                            title=task.title,
                            raw_line=line,
                        )

        if not task:
            updated_todo_lines.append(line)
            continue

        if task.status.lower() == "x":
            removed_done_lines += 1
            if task.identifier not in done_entries:
                archived_tasks.append(task)
            continue

        updated_todo_lines.append(line)

    return updated_todo_lines, archived_tasks, removed_done_lines


def insert_done_entries(
    done_lines: List[str], tasks: Iterable[TodoTask], config: RecordConfig
) -> List[str]:
    if not tasks:
        return done_lines

    updated_lines = list(done_lines)
    existing_sections: dict[str, int] = {}
    for index, line in enumerate(updated_lines):
        if line.startswith("## "):
            existing_sections[line.strip()] = index

    for task in tasks:
        header = f"## {task.date}"
        entry = f"- {config.done_entry_prefix} {task.date} | {task.area} | {task.title}\n"
        if header not in existing_sections:
            if not updated_lines or updated_lines[-1].strip():
                updated_lines.append("\n")
            updated_lines.append(f"{header}\n")
            updated_lines.append(entry)
            existing_sections[header] = len(updated_lines) - 2
        else:
            insert_index = existing_sections[header] + 1
            while insert_index < len(updated_lines) and updated_lines[insert_index].startswith(
                "- "
            ):
                insert_index += 1
            updated_lines.insert(insert_index, entry)
            for key in list(existing_sections.keys()):
                if existing_sections[key] >= insert_index:
                    existing_sections[key] += 1

    return updated_lines


def update_changelog(
    changelog_lines: List[str],
    tasks: Iterable[TodoTask],
    config: RecordConfig,
) -> List[str]:
    tasks = list(tasks)
    if not tasks:
        return changelog_lines

    today = date.today().isoformat()
    section_header = f"## [{config.changelog_section_label}] – {today}"

    updated_lines = list(changelog_lines)
    header_index = None
    for index, line in enumerate(updated_lines):
        if line.strip() == section_header:
            header_index = index
            break
    if header_index is None:
        for index, line in enumerate(updated_lines):
            if line.startswith("# Changelog"):
                header_index = index + 1
                break
        if header_index is None:
            header_index = 0
        updated_lines.insert(header_index, "\n")
        updated_lines.insert(header_index + 1, f"{section_header}\n")
        header_index = header_index + 1
    insert_at = header_index + 1
    while insert_at < len(updated_lines) and updated_lines[insert_at].startswith("- "):
        insert_at += 1
    for task in tasks:
        entry = f"- {config.changelog_entry_prefix}: {task.summary}\n"
        updated_lines.insert(insert_at, entry)
        insert_at += 1

    return updated_lines


def format_summary(tasks: Iterable[TodoTask]) -> str:
    summaries = [task.summary for task in tasks]
    if not summaries:
        return "Keine neuen abgeschlossenen Aufgaben gefunden."
    return "Neue abgeschlossene Aufgaben: " + ", ".join(summaries)


def run_update(
    repo_root: Path,
    config: RecordConfig,
    dry_run: bool,
    logger: logging.Logger,
) -> UpdateResult:
    todo_path = repo_root / "todo.txt"
    done_path = repo_root / "DONE.md"
    changelog_path = repo_root / "CHANGELOG.md"

    for path in (todo_path, done_path, changelog_path):
        if not path.exists():
            raise FileNotFoundError(
                f"Datei fehlt: {path}. Bitte Struktur prüfen und erneut starten."
            )

    todo_lines = todo_path.read_text(encoding="utf-8").splitlines(keepends=True)
    done_lines = done_path.read_text(encoding="utf-8").splitlines(keepends=True)
    changelog_lines = changelog_path.read_text(encoding="utf-8").splitlines(keepends=True)

    tasks = parse_todo_lines(todo_lines)
    validate_tasks(tasks)
    done_entries = parse_done_entries(done_lines)

    updated_todo_lines, archived_tasks, removed_done_lines = archive_done_tasks(
        todo_lines, done_entries
    )

    updated_done_lines = insert_done_entries(done_lines, archived_tasks, config)
    updated_changelog_lines = update_changelog(changelog_lines, archived_tasks, config)

    logger.info(format_summary(archived_tasks))
    logger.info("Entfernte erledigte To-Do-Zeilen: %s", removed_done_lines)

    if dry_run:
        logger.info("Testlauf aktiv: Dateien werden nicht geändert.")
        return UpdateResult(archived_tasks=archived_tasks, removed_done_lines=removed_done_lines)

    todo_path.write_text("".join(updated_todo_lines), encoding="utf-8")
    done_path.write_text("".join(updated_done_lines), encoding="utf-8")
    changelog_path.write_text("".join(updated_changelog_lines), encoding="utf-8")

    return UpdateResult(archived_tasks=archived_tasks, removed_done_lines=removed_done_lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=("Archiviert erledigte To-Dos und ergänzt den Changelog automatisch.")
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Zeigt Änderungen, ohne Dateien zu schreiben.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Aktiviert ausführliche Protokollierung.",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    logger = logging.getLogger("records")

    repo_root = Path(__file__).resolve().parents[2]
    config_path = repo_root / "config" / "records.json"
    if not config_path.exists():
        logger.error("Konfiguration fehlt: %s", config_path)
        return 1

    config = load_config(config_path)

    try:
        run_update(repo_root, config, args.dry_run, logger)
    except (ValueError, FileNotFoundError) as exc:
        logger.error(str(exc))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
