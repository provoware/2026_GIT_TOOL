"""Modul für To-Do-Verwaltung und Kalenderansichten."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.core.data_model import (
    CalendarEntry,
    CalendarViewType,
    DataModelError,
    TodoItem,
    TodoStatus,
    make_todo_id,
    parse_iso_date,
)
from src.core.todo_parser import TodoFormatError, parse_todo_line

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "todo_kalender.json"


class ModuleError(ValueError):
    """Fehler im To-Do-Kalender-Modul."""


@dataclass(frozen=True)
class ModuleConfig:
    data_path: Path
    default_theme: str
    themes: Dict[str, Dict[str, Dict[str, str]]]


def init(context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    config = load_config(context)
    ensure_data_file(config.data_path)
    return build_response(
        status="ok",
        message="Modul initialisiert. Datenablage ist bereit.",
        data={"data_path": str(config.data_path)},
    )


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validateInput(input_data)
        action = input_data["action"]
        config = load_config(input_data.get("context"))
        items = load_items(config.data_path)

        if action == "add":
            item = add_item(items, input_data)
            save_items(config.data_path, items)
            response = build_response(
                status="ok",
                message="To-Do wurde angelegt.",
                data=item.to_dict(),
            )
        elif action == "complete":
            item = complete_item(items, input_data)
            save_items(config.data_path, items)
            response = build_response(
                status="ok",
                message="To-Do wurde als erledigt markiert.",
                data=item.to_dict(),
            )
        elif action == "list":
            response = build_response(
                status="ok",
                message="To-Do-Liste geladen.",
                data={"items": [item.to_dict() for item in items]},
            )
        elif action == "calendar":
            view_data = build_calendar_view(items, input_data, config)
            response = build_response(
                status="ok",
                message="Kalenderansicht erstellt.",
                data=view_data,
            )
        elif action == "sync_todo_txt":
            synced = sync_todo_txt(items, input_data)
            save_items(config.data_path, items)
            response = build_response(
                status="ok",
                message="To-Do-Abgleich abgeschlossen.",
                data={"neu": synced, "gesamt": len(items)},
            )
        else:
            raise ModuleError("Unbekannte Aktion.")
    except (ModuleError, DataModelError, TodoFormatError, FileNotFoundError) as exc:
        response = build_response(status="error", message=str(exc), data={})

    validateOutput(response)
    return response


def exit() -> Dict[str, Any]:
    return build_response(status="ok", message="Modul sauber beendet.", data={})


def validateInput(input_data: Dict[str, Any]) -> None:
    if not isinstance(input_data, dict):
        raise ModuleError("Eingabe fehlt oder ist kein Objekt (dict).")
    action = input_data.get("action")
    if action not in {"add", "complete", "list", "calendar", "sync_todo_txt"}:
        raise ModuleError(
            "action ist ungültig. Erlaubt: add, complete, list, calendar, sync_todo_txt."
        )
    if action == "add":
        _require_text(input_data.get("title"), "title")
        _require_text(input_data.get("planned_date"), "planned_date")
    if action == "complete":
        _require_text(input_data.get("id"), "id")
    if action == "calendar":
        _require_text(input_data.get("view"), "view")


def validateOutput(output: Dict[str, Any]) -> None:
    if not isinstance(output, dict):
        raise ModuleError("Ausgabe ist kein Objekt (dict).")
    status = output.get("status")
    if status not in {"ok", "error"}:
        raise ModuleError("Ausgabe-Status ist ungültig.")
    _require_text(output.get("message"), "message")
    if "data" not in output:
        raise ModuleError("Ausgabe enthält keine data-Daten.")


def build_response(status: str, message: str, data: Dict[str, Any]) -> Dict[str, Any]:
    response = {"status": status, "message": message, "data": data}
    validateOutput(response)
    return response


def load_config(context: Optional[Dict[str, Any]] = None) -> ModuleConfig:
    context = context or {}
    config_path = context.get("config_path", DEFAULT_CONFIG_PATH)
    config_path = _resolve_path(config_path)
    if not config_path.exists():
        raise ModuleError(f"Konfiguration fehlt: {config_path}")
    raw = _load_json(config_path)
    data_path = _resolve_path(raw.get("data_path", "data/todo_kalender.json"))
    default_theme = _require_text(raw.get("default_theme"), "default_theme")
    themes = raw.get("themes")
    if not isinstance(themes, dict) or not themes:
        raise ModuleError("themes ist leer oder ungültig.")
    for name, theme in themes.items():
        _require_text(name, "theme_name")
        _validate_theme(theme)
    if default_theme not in themes:
        raise ModuleError("default_theme ist nicht in themes enthalten.")
    return ModuleConfig(
        data_path=data_path,
        default_theme=default_theme,
        themes=themes,
    )


def ensure_data_file(data_path: Path) -> None:
    data_path.parent.mkdir(parents=True, exist_ok=True)
    if not data_path.exists():
        data_path.write_text(json.dumps({"items": []}, indent=2), encoding="utf-8")


def load_items(data_path: Path) -> List[TodoItem]:
    ensure_data_file(data_path)
    raw = _load_json(data_path)
    items_raw = raw.get("items", [])
    if not isinstance(items_raw, list):
        raise ModuleError("items ist kein Array.")
    items = [TodoItem.from_dict(item) for item in items_raw]
    return items


def save_items(data_path: Path, items: Iterable[TodoItem]) -> None:
    ensure_data_file(data_path)
    data = {"items": [item.to_dict() for item in items]}
    data_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    if not data_path.exists():
        raise ModuleError("Daten konnten nicht geschrieben werden.")


def add_item(items: List[TodoItem], input_data: Dict[str, Any]) -> TodoItem:
    planned_date = parse_iso_date(input_data.get("planned_date"), "planned_date")
    title = _require_text(input_data.get("title"), "title")
    notes = _require_text(input_data.get("notes", ""), "notes", allow_empty=True)
    item_id = make_todo_id(title, planned_date)
    if any(item.item_id == item_id for item in items):
        raise ModuleError("To-Do existiert bereits mit gleicher ID.")
    item = TodoItem(
        item_id=item_id,
        title=title,
        planned_date=planned_date,
        status=TodoStatus.GEPLANT,
        done_date=None,
        notes=notes,
        source="todo_kalender",
    )
    items.append(item)
    return item


def complete_item(items: List[TodoItem], input_data: Dict[str, Any]) -> TodoItem:
    item_id = _require_text(input_data.get("id"), "id")
    done_date_value = input_data.get("done_date")
    done_date = None
    if done_date_value:
        done_date = parse_iso_date(done_date_value, "done_date")
    for index, item in enumerate(items):
        if item.item_id == item_id:
            completed_item = TodoItem(
                item_id=item.item_id,
                title=item.title,
                planned_date=item.planned_date,
                status=TodoStatus.ERLEDIGT,
                done_date=done_date or date.today(),
                notes=item.notes,
                source=item.source,
            )
            items[index] = completed_item
            return completed_item
    raise ModuleError("To-Do-ID nicht gefunden.")


def build_calendar_view(
    items: Iterable[TodoItem],
    input_data: Dict[str, Any],
    config: ModuleConfig,
) -> Dict[str, Any]:
    view = _parse_view(input_data.get("view"))
    reference_date = _resolve_reference_date(input_data.get("reference_date"))
    theme_name = input_data.get("theme", config.default_theme)
    theme = config.themes.get(theme_name)
    if theme is None:
        raise ModuleError("Theme ist nicht verfügbar.")
    start_date, end_date = _view_range(view, reference_date)
    entries = _calendar_entries(items, theme, start_date, end_date)
    return {
        "view": view.value,
        "reference_date": reference_date.isoformat(),
        "range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "theme": theme_name,
        "entries": [entry.to_dict() for entry in entries],
    }


def sync_todo_txt(items: List[TodoItem], input_data: Dict[str, Any]) -> int:
    todo_path_value = input_data.get("todo_path", REPO_ROOT / "todo.txt")
    todo_path = _resolve_path(todo_path_value)
    if not todo_path.exists():
        raise FileNotFoundError(f"todo.txt nicht gefunden: {todo_path}")
    lines = todo_path.read_text(encoding="utf-8").splitlines()
    new_items = 0
    for line in lines:
        if not line.strip().startswith("["):
            continue
        todo_line = parse_todo_line(line)
        planned_date = parse_iso_date(todo_line.date, "planned_date")
        title = f"{todo_line.area}: {todo_line.task}"
        status = TodoStatus.ERLEDIGT if todo_line.status == "x" else TodoStatus.GEPLANT
        done_date = planned_date if status == TodoStatus.ERLEDIGT else None
        item_id = make_todo_id(title, planned_date)
        if any(item.item_id == item_id for item in items):
            continue
        items.append(
            TodoItem(
                item_id=item_id,
                title=title,
                planned_date=planned_date,
                status=status,
                done_date=done_date,
                notes=todo_line.done_criteria,
                source="todo.txt",
            )
        )
        new_items += 1
    return new_items


def _calendar_entries(
    items: Iterable[TodoItem],
    theme: Dict[str, Dict[str, str]],
    start_date: date,
    end_date: date,
) -> List[CalendarEntry]:
    entries: List[CalendarEntry] = []
    for item in items:
        entry_date = item.done_date if item.status == TodoStatus.ERLEDIGT else item.planned_date
        if not (start_date <= entry_date <= end_date):
            continue
        icon_config = theme["done"] if item.status == TodoStatus.ERLEDIGT else theme["planned"]
        icon = _require_text(icon_config.get("icon"), "icon")
        color = _require_text(icon_config.get("color"), "color")
        label = _require_text(icon_config.get("label"), "label")
        aria_label = f"{label}: {item.title} am {entry_date.isoformat()}"
        entries.append(
            CalendarEntry(
                entry_date=entry_date,
                title=item.title,
                status=item.status,
                icon=icon,
                color_name=color,
                aria_label=aria_label,
            )
        )
    return sorted(entries, key=lambda entry: entry.entry_date)


def _view_range(view: CalendarViewType, reference_date: date) -> Tuple[date, date]:
    if view == CalendarViewType.JAHR:
        start = date(reference_date.year, 1, 1)
        end = date(reference_date.year, 12, 31)
        return start, end
    if view == CalendarViewType.MONAT:
        start = date(reference_date.year, reference_date.month, 1)
        next_month = reference_date.replace(day=28) + timedelta(days=4)
        end = date(next_month.year, next_month.month, 1) - timedelta(days=1)
        return start, end
    week_start = reference_date - timedelta(days=reference_date.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def _resolve_reference_date(value: Optional[str]) -> date:
    if value is None:
        return date.today()
    return parse_iso_date(value, "reference_date")


def _parse_view(value: Any) -> CalendarViewType:
    if not isinstance(value, str):
        raise ModuleError("view ist kein Text.")
    try:
        return CalendarViewType(value)
    except ValueError as exc:
        raise ModuleError("view ist ungültig. Erlaubt: jahr, monat, woche.") from exc


def _validate_theme(theme: Any) -> None:
    if not isinstance(theme, dict):
        raise ModuleError("Theme ist kein Objekt (dict).")
    for key in ("planned", "done"):
        if key not in theme:
            raise ModuleError("Theme fehlt: planned oder done.")
        section = theme[key]
        if not isinstance(section, dict):
            raise ModuleError("Theme-Bereich ist kein Objekt (dict).")
        _require_text(section.get("icon"), "icon")
        _require_text(section.get("color"), "color")
        _require_text(section.get("label"), "label")


def _require_text(value: Any, field_name: str, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ModuleError(f"{field_name} ist kein Text.")
    if not allow_empty and not value.strip():
        raise ModuleError(f"{field_name} ist leer.")
    return value


def _resolve_path(value: Any) -> Path:
    if isinstance(value, Path):
        path = value
    elif isinstance(value, str):
        path = Path(value)
    else:
        raise ModuleError("Pfad ist ungültig.")
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ModuleError(f"JSON ist ungültig: {path}") from exc


def setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
