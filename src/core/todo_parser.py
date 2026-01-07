"""Parser und Validator für das einheitliche To-Do-Format."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import TodoFormatError

TODO_PATTERN = re.compile(
    r"^\[(?P<status>[ xX])\]\s+"
    r"(?P<date>\d{4}-\d{2}-\d{2})\s+\|\s+"
    r"(?P<area>[^|]+?)\s+\|\s+"
    r"(?P<task>[^|]+?)\s+\|\s+"
    r"fertig wenn:\s+(?P<done>.+)$"
)


@dataclass(frozen=True)
class TodoItem:
    status: str
    date: str
    area: str
    task: str
    done_criteria: str

    def normalized_text(self) -> str:
        """Text für die Agent-Zuordnung (kleingeschrieben, ohne Sonderzeichen)."""
        return f"{self.area} {self.task} {self.done_criteria}".lower()


def parse_todo_line(line: str) -> TodoItem:
    """Validiert und parst eine To-Do-Zeile.

    Format:
    [ ] 2026-01-07 | Bereich | Beschreibung | fertig wenn: Kriterium
    """
    if not isinstance(line, str) or not line.strip():
        raise TodoFormatError(
            "To-Do-Zeile fehlt oder ist leer. Bitte ein gültiges Format nutzen."
        )

    match = TODO_PATTERN.match(line.strip())
    if not match:
        raise TodoFormatError(
            "Ungültiges To-Do-Format. Erwartet: "
            "[ ] JJJJ-MM-TT | Bereich | Beschreibung | fertig wenn: Kriterium"
        )

    status = match.group("status").lower()
    return TodoItem(
        status=status,
        date=match.group("date"),
        area=match.group("area").strip(),
        task=match.group("task").strip(),
        done_criteria=match.group("done").strip(),
    )
