"""Zentrales Datenmodell für To-Dos und Kalenderansichten."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Dict, Optional

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class DataModelError(ValueError):
    """Fehler im zentralen Datenmodell (Validierung fehlgeschlagen)."""


class TodoStatus(str, Enum):
    GEPLANT = "geplant"
    ERLEDIGT = "erledigt"


class CalendarViewType(str, Enum):
    JAHR = "jahr"
    MONAT = "monat"
    WOCHE = "woche"


@dataclass(frozen=True)
class TodoItem:
    item_id: str
    title: str
    planned_date: date
    status: TodoStatus
    done_date: Optional[date]
    notes: str
    source: str

    def to_dict(self) -> Dict[str, Any]:
        validate_todo_item(self)
        return {
            "id": self.item_id,
            "title": self.title,
            "planned_date": self.planned_date.isoformat(),
            "status": self.status.value,
            "done_date": self.done_date.isoformat() if self.done_date else None,
            "notes": self.notes,
            "source": self.source,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "TodoItem":
        if not isinstance(data, dict):
            raise DataModelError("To-Do-Daten sind kein Objekt (dict).")
        item_id = _require_text(data.get("id"), "id")
        title = _require_text(data.get("title"), "title")
        planned_date = parse_iso_date(data.get("planned_date"), "planned_date")
        status = _parse_status(data.get("status"))
        done_date_raw = data.get("done_date")
        done_date = None
        if done_date_raw:
            done_date = parse_iso_date(done_date_raw, "done_date")
        notes = _require_text(data.get("notes", ""), "notes", allow_empty=True)
        source = _require_text(data.get("source", "unbekannt"), "source")
        item = TodoItem(
            item_id=item_id,
            title=title,
            planned_date=planned_date,
            status=status,
            done_date=done_date,
            notes=notes,
            source=source,
        )
        validate_todo_item(item)
        return item


@dataclass(frozen=True)
class CalendarEntry:
    entry_date: date
    title: str
    status: TodoStatus
    icon: str
    color_name: str
    aria_label: str

    def to_dict(self) -> Dict[str, str]:
        validate_calendar_entry(self)
        return {
            "date": self.entry_date.isoformat(),
            "title": self.title,
            "status": self.status.value,
            "icon": self.icon,
            "color": self.color_name,
            "aria_label": self.aria_label,
        }


def parse_iso_date(value: Any, field_name: str) -> date:
    if not isinstance(value, str) or not value:
        raise DataModelError(f"{field_name} fehlt oder ist kein Text.")
    if not DATE_PATTERN.match(value):
        raise DataModelError(f"{field_name} ist ungültig. Erwartet: JJJJ-MM-TT.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DataModelError(f"{field_name} ist kein gültiges Datum.") from exc


def make_todo_id(title: str, planned_date: date) -> str:
    if not isinstance(title, str) or not title.strip():
        raise DataModelError("Titel fehlt oder ist leer.")
    if not isinstance(planned_date, date):
        raise DataModelError("planned_date ist kein Datum.")
    slug = _slugify(title)
    return f"{planned_date.strftime('%Y%m%d')}-{slug}"


def validate_todo_item(item: TodoItem) -> None:
    if not isinstance(item, TodoItem):
        raise DataModelError("item ist kein TodoItem.")
    _require_text(item.item_id, "item_id")
    _require_text(item.title, "title")
    if not isinstance(item.planned_date, date):
        raise DataModelError("planned_date ist kein Datum.")
    if item.status == TodoStatus.ERLEDIGT and not item.done_date:
        raise DataModelError("done_date fehlt bei erledigtem To-Do.")
    if item.status == TodoStatus.GEPLANT and item.done_date:
        raise DataModelError("done_date darf bei geplantem To-Do nicht gesetzt sein.")
    _require_text(item.notes, "notes", allow_empty=True)
    _require_text(item.source, "source")


def validate_calendar_entry(entry: CalendarEntry) -> None:
    if not isinstance(entry, CalendarEntry):
        raise DataModelError("entry ist kein CalendarEntry.")
    if not isinstance(entry.entry_date, date):
        raise DataModelError("entry_date ist kein Datum.")
    _require_text(entry.title, "title")
    if entry.status not in (TodoStatus.GEPLANT, TodoStatus.ERLEDIGT):
        raise DataModelError("status ist ungültig.")
    _require_text(entry.icon, "icon")
    _require_text(entry.color_name, "color_name")
    _require_text(entry.aria_label, "aria_label")


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return cleaned or "aufgabe"


def _require_text(value: Any, field_name: str, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise DataModelError(f"{field_name} ist kein Text.")
    if not allow_empty and not value.strip():
        raise DataModelError(f"{field_name} ist leer.")
    return value


def _parse_status(value: Any) -> TodoStatus:
    if isinstance(value, TodoStatus):
        return value
    if not isinstance(value, str):
        raise DataModelError("status ist kein Text.")
    try:
        return TodoStatus(value)
    except ValueError as exc:
        raise DataModelError("status ist ungültig.") from exc
