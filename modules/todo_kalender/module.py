"""To-do, calendar, appointment and reminder module for Provoware Memo."""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
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
from system.permission_guard import PermissionGuardError, require_write_access

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "todo_kalender.json"
HEX_COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")
TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
MAX_LEGEND_COLORS = 5
MAX_DAY_COLORS = 4
DEFAULT_REMINDER_HOUR = 9
DEFAULT_LEGEND = [
    {"id": "farbe-1", "title": "Wichtig", "color": "#ef4444"},
    {"id": "farbe-2", "title": "Privat", "color": "#f59e0b"},
    {"id": "farbe-3", "title": "Arbeit", "color": "#3b82f6"},
    {"id": "farbe-4", "title": "Familie", "color": "#22c55e"},
    {"id": "farbe-5", "title": "Sonstiges", "color": "#a855f7"},
]


class ModuleError(ValueError):
    """Calendar module validation error."""


@dataclass(frozen=True)
class ModuleConfig:
    data_path: Path
    default_theme: str
    themes: Dict[str, Dict[str, Dict[str, str]]]
    reminder_poll_seconds: int


def init(context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        config = load_config(context)
        ensure_data_file(config.data_path)
        return build_response(
            status="ok",
            message="Kalenderdaten, Termine und Erinnerungen sind bereit.",
            data={
                "data_path": str(config.data_path),
                "legend_slots": MAX_LEGEND_COLORS,
                "max_colors_per_day": MAX_DAY_COLORS,
            },
        )
    except (ModuleError, PermissionGuardError) as exc:
        return build_response(status="error", message=str(exc), data={})


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validateInput(input_data)
        action = input_data["action"]
        config = load_config(input_data.get("context"))
        store = load_store(config.data_path)
        items = [TodoItem.from_dict(item) for item in store["items"]]

        if action == "add":
            item = add_item(items, input_data)
            store["items"] = [entry.to_dict() for entry in items]
            save_store(config.data_path, store)
            response = build_response("ok", "Aufgabe wurde angelegt.", item.to_dict())
        elif action == "complete":
            item = complete_item(items, input_data)
            store["items"] = [entry.to_dict() for entry in items]
            save_store(config.data_path, store)
            response = build_response("ok", "Aufgabe wurde erledigt.", item.to_dict())
        elif action == "list":
            response = build_response(
                "ok", "Aufgaben wurden geladen.", {"items": [item.to_dict() for item in items]}
            )
        elif action == "calendar":
            response = build_response(
                "ok",
                "Kalenderansicht wurde erstellt.",
                build_calendar_view(items, store, input_data, config),
            )
        elif action == "get_settings":
            response = build_response("ok", "Kalenderoptionen wurden geladen.", settings_payload(store, config))
        elif action == "set_legend":
            store["legend"] = validate_legend(input_data.get("legend"))
            _drop_unknown_day_colors(store)
            save_store(config.data_path, store)
            response = build_response("ok", "Farblegende wurde gespeichert.", settings_payload(store, config))
        elif action == "set_day_colors":
            marker = set_day_colors(store, input_data)
            save_store(config.data_path, store)
            response = build_response("ok", "Tagesfarben wurden gespeichert.", marker)
        elif action == "add_appointment":
            appointment = create_appointment(store, input_data)
            save_store(config.data_path, store)
            response = build_response("ok", "Termin wurde gespeichert.", appointment)
        elif action == "update_appointment":
            appointment = update_appointment(store, input_data)
            save_store(config.data_path, store)
            response = build_response("ok", "Termin wurde aktualisiert.", appointment)
        elif action == "delete_appointment":
            deleted_id = delete_appointment(store, input_data)
            save_store(config.data_path, store)
            response = build_response("ok", "Termin wurde gelöscht.", {"id": deleted_id})
        elif action == "list_reminders":
            response = build_response(
                "ok", "Erinnerungen wurden geladen.", reminder_payload(store, input_data)
            )
        elif action == "acknowledge_reminder":
            appointment = acknowledge_reminder(store, input_data)
            save_store(config.data_path, store)
            response = build_response("ok", "Erinnerung wurde bestätigt.", appointment)
        elif action == "sync_todo_txt":
            synced = sync_todo_txt(items, input_data)
            store["items"] = [entry.to_dict() for entry in items]
            save_store(config.data_path, store)
            response = build_response(
                "ok", "To-do-Abgleich wurde abgeschlossen.", {"neu": synced, "gesamt": len(items)}
            )
        else:  # pragma: no cover - protected by validateInput
            raise ModuleError("Unbekannte Aktion.")
    except (
        ModuleError,
        DataModelError,
        TodoFormatError,
        FileNotFoundError,
        PermissionGuardError,
    ) as exc:
        response = build_response("error", str(exc), {})

    validateOutput(response)
    return response


def exit() -> Dict[str, Any]:
    return build_response("ok", "Kalendermodul wurde sauber beendet.", {})


def validateInput(input_data: Dict[str, Any]) -> None:
    if not isinstance(input_data, dict):
        raise ModuleError("Eingabe fehlt oder ist kein Objekt (dict).")
    action = input_data.get("action")
    allowed = {
        "add",
        "complete",
        "list",
        "calendar",
        "get_settings",
        "set_legend",
        "set_day_colors",
        "add_appointment",
        "update_appointment",
        "delete_appointment",
        "list_reminders",
        "acknowledge_reminder",
        "sync_todo_txt",
    }
    if action not in allowed:
        raise ModuleError(f"action ist ungültig. Erlaubt: {', '.join(sorted(allowed))}.")
    if action == "add":
        _require_text(input_data.get("title"), "title")
        _require_text(input_data.get("planned_date"), "planned_date")
    elif action == "complete":
        _require_text(input_data.get("id"), "id")
    elif action == "calendar":
        _require_text(input_data.get("view"), "view")
    elif action == "set_legend":
        if not isinstance(input_data.get("legend"), list):
            raise ModuleError("legend ist keine Liste.")
    elif action == "set_day_colors":
        _require_text(input_data.get("date"), "date")
        if not isinstance(input_data.get("color_ids"), list):
            raise ModuleError("color_ids ist keine Liste.")
    elif action in {"add_appointment", "update_appointment"}:
        if action == "update_appointment":
            _require_text(input_data.get("id"), "id")
        _require_text(input_data.get("title"), "title")
        _require_text(input_data.get("date"), "date")
    elif action in {"delete_appointment", "acknowledge_reminder"}:
        _require_text(input_data.get("id"), "id")


def validateOutput(output: Dict[str, Any]) -> None:
    if not isinstance(output, dict):
        raise ModuleError("Ausgabe ist kein Objekt (dict).")
    if output.get("status") not in {"ok", "error"}:
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
    config_path = _resolve_path(context.get("config_path", DEFAULT_CONFIG_PATH))
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
    poll_seconds = raw.get("reminder_poll_seconds", 60)
    if not isinstance(poll_seconds, int) or not 15 <= poll_seconds <= 3600:
        raise ModuleError("reminder_poll_seconds muss zwischen 15 und 3600 liegen.")
    return ModuleConfig(data_path, default_theme, themes, poll_seconds)


def default_store() -> Dict[str, Any]:
    return {
        "items": [],
        "legend": [dict(entry) for entry in DEFAULT_LEGEND],
        "day_markers": {},
        "appointments": [],
    }


def ensure_data_file(data_path: Path) -> None:
    data_path.parent.mkdir(parents=True, exist_ok=True)
    if not data_path.exists():
        require_write_access(Path(__file__), data_path, "Kalenderdaten anlegen")
        data_path.write_text(
            json.dumps(default_store(), indent=2, ensure_ascii=False), encoding="utf-8"
        )


def load_store(data_path: Path) -> Dict[str, Any]:
    ensure_data_file(data_path)
    raw = _load_json(data_path)
    if not isinstance(raw.get("items", []), list):
        raise ModuleError("items ist kein Array.")
    store = default_store()
    store["items"] = raw.get("items", [])
    store["legend"] = validate_legend(raw.get("legend", DEFAULT_LEGEND))
    markers = raw.get("day_markers", {})
    if not isinstance(markers, dict):
        raise ModuleError("day_markers ist kein Objekt.")
    store["day_markers"] = {}
    allowed = {entry["id"] for entry in store["legend"]}
    for date_value, color_ids in markers.items():
        parsed = parse_iso_date(date_value, "day_marker_date").isoformat()
        normalized = _validate_color_ids(color_ids, allowed)
        if normalized:
            store["day_markers"][parsed] = normalized
    appointments = raw.get("appointments", [])
    if not isinstance(appointments, list):
        raise ModuleError("appointments ist kein Array.")
    store["appointments"] = [validate_appointment(item, allowed) for item in appointments]
    return store


def save_store(data_path: Path, store: Dict[str, Any]) -> None:
    ensure_data_file(data_path)
    payload = {
        "items": list(store.get("items", [])),
        "legend": validate_legend(store.get("legend", DEFAULT_LEGEND)),
        "day_markers": dict(store.get("day_markers", {})),
        "appointments": list(store.get("appointments", [])),
    }
    require_write_access(Path(__file__), data_path, "Kalenderdaten speichern")
    data_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def load_items(data_path: Path) -> List[TodoItem]:
    return [TodoItem.from_dict(item) for item in load_store(data_path)["items"]]


def save_items(data_path: Path, items: Iterable[TodoItem]) -> None:
    store = load_store(data_path)
    store["items"] = [item.to_dict() for item in items]
    save_store(data_path, store)


def add_item(items: List[TodoItem], input_data: Dict[str, Any]) -> TodoItem:
    planned_date = parse_iso_date(input_data.get("planned_date"), "planned_date")
    title = _require_text(input_data.get("title"), "title")
    notes = _require_text(input_data.get("notes", ""), "notes", allow_empty=True)
    item_id = make_todo_id(title, planned_date)
    if any(item.item_id == item_id for item in items):
        raise ModuleError("Aufgabe existiert bereits mit gleicher ID.")
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
    done_date = (
        parse_iso_date(input_data["done_date"], "done_date")
        if input_data.get("done_date")
        else date.today()
    )
    for index, item in enumerate(items):
        if item.item_id == item_id:
            completed_item = TodoItem(
                item_id=item.item_id,
                title=item.title,
                planned_date=item.planned_date,
                status=TodoStatus.ERLEDIGT,
                done_date=done_date,
                notes=item.notes,
                source=item.source,
            )
            items[index] = completed_item
            return completed_item
    raise ModuleError("Aufgaben-ID wurde nicht gefunden.")


def build_calendar_view(
    items: Iterable[TodoItem],
    store: Dict[str, Any],
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
    legend_by_id = {entry["id"]: entry for entry in store["legend"]}
    markers = []
    for day, color_ids in sorted(store["day_markers"].items()):
        parsed = date.fromisoformat(day)
        if start_date <= parsed <= end_date:
            colors = [legend_by_id[color_id] for color_id in color_ids if color_id in legend_by_id]
            markers.append(
                {
                    "date": day,
                    "color_ids": [entry["id"] for entry in colors],
                    "colors": colors,
                    "summary": " · ".join(entry["title"] for entry in colors),
                }
            )
    appointments = [
        dict(item)
        for item in store["appointments"]
        if start_date <= date.fromisoformat(item["date"]) <= end_date
    ]
    appointments.sort(key=lambda item: (item["date"], item.get("start_time") or "", item["title"]))
    return {
        "view": view.value,
        "reference_date": reference_date.isoformat(),
        "range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "theme": theme_name,
        "entries": [entry.to_dict() for entry in entries],
        "legend": store["legend"],
        "day_markers": markers,
        "appointments": appointments,
        "reminders": reminder_payload(store, input_data),
        "options": {
            "legend_slots": MAX_LEGEND_COLORS,
            "max_colors_per_day": MAX_DAY_COLORS,
            "reminder_poll_seconds": config.reminder_poll_seconds,
        },
    }


def settings_payload(store: Dict[str, Any], config: ModuleConfig) -> Dict[str, Any]:
    return {
        "legend": store["legend"],
        "max_colors_per_day": MAX_DAY_COLORS,
        "legend_slots": MAX_LEGEND_COLORS,
        "reminder_poll_seconds": config.reminder_poll_seconds,
    }


def validate_legend(value: Any) -> List[Dict[str, str]]:
    if not isinstance(value, list) or len(value) != MAX_LEGEND_COLORS:
        raise ModuleError(f"Die Farblegende muss genau {MAX_LEGEND_COLORS} Einträge enthalten.")
    result: List[Dict[str, str]] = []
    seen: set[str] = set()
    for index, raw in enumerate(value, start=1):
        if not isinstance(raw, dict):
            raise ModuleError("Ein Legendeneintrag ist kein Objekt.")
        color_id = _require_text(raw.get("id", f"farbe-{index}"), "legend.id").strip()
        if color_id in seen:
            raise ModuleError("Legenden-IDs müssen eindeutig sein.")
        seen.add(color_id)
        title = _require_text(raw.get("title"), "legend.title").strip()
        if len(title) > 40:
            raise ModuleError("Ein Legendentitel darf höchstens 40 Zeichen enthalten.")
        color = _validate_color(raw.get("color"))
        result.append({"id": color_id, "title": title, "color": color})
    return result


def set_day_colors(store: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    day = parse_iso_date(input_data.get("date"), "date").isoformat()
    allowed = {entry["id"] for entry in store["legend"]}
    color_ids = _validate_color_ids(input_data.get("color_ids"), allowed)
    if color_ids:
        store["day_markers"][day] = color_ids
    else:
        store["day_markers"].pop(day, None)
    legend_by_id = {entry["id"]: entry for entry in store["legend"]}
    colors = [legend_by_id[color_id] for color_id in color_ids]
    return {
        "date": day,
        "color_ids": color_ids,
        "colors": colors,
        "summary": " · ".join(entry["title"] for entry in colors),
    }


def create_appointment(store: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    appointment_id = f"termin-{uuid.uuid4().hex[:12]}"
    appointment = appointment_from_input(input_data, appointment_id)
    appointment = validate_appointment(appointment, {entry["id"] for entry in store["legend"]})
    store["appointments"].append(appointment)
    return appointment


def update_appointment(store: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    appointment_id = _require_text(input_data.get("id"), "id")
    for index, existing in enumerate(store["appointments"]):
        if existing["id"] == appointment_id:
            merged = {**existing, **input_data, "id": appointment_id}
            if _reminder_relevant_fields_changed(existing, merged):
                merged["reminder_acknowledged"] = False
            appointment = appointment_from_input(merged, appointment_id, created_at=existing["created_at"])
            appointment = validate_appointment(
                appointment, {entry["id"] for entry in store["legend"]}
            )
            store["appointments"][index] = appointment
            return appointment
    raise ModuleError("Termin-ID wurde nicht gefunden.")


def delete_appointment(store: Dict[str, Any], input_data: Dict[str, Any]) -> str:
    appointment_id = _require_text(input_data.get("id"), "id")
    before = len(store["appointments"])
    store["appointments"] = [item for item in store["appointments"] if item["id"] != appointment_id]
    if len(store["appointments"]) == before:
        raise ModuleError("Termin-ID wurde nicht gefunden.")
    return appointment_id


def appointment_from_input(
    input_data: Dict[str, Any], appointment_id: str, *, created_at: Optional[str] = None
) -> Dict[str, Any]:
    date_value = parse_iso_date(input_data.get("date"), "date").isoformat()
    title = _require_text(input_data.get("title"), "title").strip()
    if len(title) > 180:
        raise ModuleError("Der Termintitel darf höchstens 180 Zeichen enthalten.")
    all_day = bool(input_data.get("all_day", False))
    start_time = _optional_time(input_data.get("start_time"))
    end_time = _optional_time(input_data.get("end_time"))
    if all_day:
        start_time = None
        end_time = None
    elif end_time and start_time and end_time < start_time:
        raise ModuleError("Die Endzeit darf nicht vor der Startzeit liegen.")
    reminder_raw = input_data.get("reminder_minutes")
    reminder_minutes: Optional[int]
    if reminder_raw in (None, "", -1, "-1"):
        reminder_minutes = None
    else:
        try:
            reminder_minutes = int(reminder_raw)
        except (TypeError, ValueError) as exc:
            raise ModuleError("reminder_minutes ist ungültig.") from exc
        if not 0 <= reminder_minutes <= 10080:
            raise ModuleError("Erinnerungen sind zwischen 0 Minuten und 7 Tagen möglich.")
    color_id = input_data.get("color_id") or None
    if color_id is not None:
        color_id = _require_text(color_id, "color_id")
    location = _require_text(input_data.get("location", ""), "location", allow_empty=True)
    notes = _require_text(input_data.get("notes", ""), "notes", allow_empty=True)
    reminder_at = _appointment_reminder_at(date_value, start_time, reminder_minutes)
    now = datetime.now().replace(microsecond=0).isoformat()
    return {
        "id": appointment_id,
        "title": title,
        "date": date_value,
        "all_day": all_day,
        "start_time": start_time,
        "end_time": end_time,
        "location": location,
        "notes": notes,
        "color_id": color_id,
        "reminder_minutes": reminder_minutes,
        "reminder_at": reminder_at,
        "reminder_acknowledged": bool(input_data.get("reminder_acknowledged", False)),
        "created_at": created_at or now,
        "updated_at": now,
    }


def validate_appointment(value: Any, allowed_colors: set[str]) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ModuleError("Ein Termin ist kein Objekt.")
    appointment = appointment_from_input(
        value,
        _require_text(value.get("id"), "appointment.id"),
        created_at=_require_text(value.get("created_at"), "appointment.created_at"),
    )
    color_id = appointment.get("color_id")
    if color_id is not None and color_id not in allowed_colors:
        appointment["color_id"] = None
    appointment["reminder_acknowledged"] = bool(value.get("reminder_acknowledged", False))
    appointment["updated_at"] = _require_text(
        value.get("updated_at", appointment["updated_at"]), "appointment.updated_at"
    )
    return appointment


def reminder_payload(store: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    now_value = input_data.get("now")
    if now_value:
        try:
            now = datetime.fromisoformat(str(now_value))
        except ValueError as exc:
            raise ModuleError("now ist kein gültiger ISO-Zeitstempel.") from exc
    else:
        now = datetime.now()
    horizon_hours = input_data.get("horizon_hours", 168)
    try:
        horizon = max(1, min(int(horizon_hours), 24 * 30))
    except (TypeError, ValueError) as exc:
        raise ModuleError("horizon_hours ist ungültig.") from exc
    due: List[Dict[str, Any]] = []
    upcoming: List[Dict[str, Any]] = []
    horizon_end = now + timedelta(hours=horizon)
    for appointment in store["appointments"]:
        reminder_at_raw = appointment.get("reminder_at")
        if not reminder_at_raw or appointment.get("reminder_acknowledged"):
            continue
        reminder_at = datetime.fromisoformat(reminder_at_raw)
        item = dict(appointment)
        item["reminder_status"] = "due" if reminder_at <= now else "upcoming"
        if reminder_at <= now:
            due.append(item)
        elif reminder_at <= horizon_end:
            upcoming.append(item)
    key = lambda item: (item.get("reminder_at") or "", item["title"])
    return {"due": sorted(due, key=key), "upcoming": sorted(upcoming, key=key), "now": now.isoformat()}


def acknowledge_reminder(store: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    appointment_id = _require_text(input_data.get("id"), "id")
    for appointment in store["appointments"]:
        if appointment["id"] == appointment_id:
            appointment["reminder_acknowledged"] = True
            appointment["updated_at"] = datetime.now().replace(microsecond=0).isoformat()
            return dict(appointment)
    raise ModuleError("Erinnerungs-ID wurde nicht gefunden.")


def sync_todo_txt(items: List[TodoItem], input_data: Dict[str, Any]) -> int:
    todo_path = _resolve_path(input_data.get("todo_path", REPO_ROOT / "todo.txt"))
    if not todo_path.exists():
        raise FileNotFoundError(f"todo.txt nicht gefunden: {todo_path}")
    new_items = 0
    for line in todo_path.read_text(encoding="utf-8").splitlines():
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
        if not start_date <= entry_date <= end_date:
            continue
        icon_config = theme["done"] if item.status == TodoStatus.ERLEDIGT else theme["planned"]
        icon = _require_text(icon_config.get("icon"), "icon")
        color = _require_text(icon_config.get("color"), "color")
        label = _require_text(icon_config.get("label"), "label")
        entries.append(
            CalendarEntry(
                entry_date=entry_date,
                title=item.title,
                status=item.status,
                icon=icon,
                color_name=color,
                aria_label=f"{label}: {item.title} am {entry_date.isoformat()}",
            )
        )
    return sorted(entries, key=lambda entry: (entry.entry_date, entry.title))


def _view_range(view: CalendarViewType, reference_date: date) -> Tuple[date, date]:
    if view == CalendarViewType.JAHR:
        return date(reference_date.year, 1, 1), date(reference_date.year, 12, 31)
    if view == CalendarViewType.MONAT:
        start = date(reference_date.year, reference_date.month, 1)
        next_month = reference_date.replace(day=28) + timedelta(days=4)
        return start, date(next_month.year, next_month.month, 1) - timedelta(days=1)
    start = reference_date - timedelta(days=reference_date.weekday())
    return start, start + timedelta(days=6)


def _resolve_reference_date(value: Optional[str]) -> date:
    return date.today() if value is None else parse_iso_date(value, "reference_date")


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
        section = theme.get(key)
        if not isinstance(section, dict):
            raise ModuleError("Theme fehlt: planned oder done.")
        _require_text(section.get("icon"), "icon")
        _require_text(section.get("color"), "color")
        _require_text(section.get("label"), "label")


def _validate_color(value: Any) -> str:
    if not isinstance(value, str) or not HEX_COLOR_PATTERN.match(value):
        raise ModuleError("Farbe ist ungültig. Erwartet wird #RRGGBB.")
    return value.lower()


def _validate_color_ids(value: Any, allowed: set[str]) -> List[str]:
    if not isinstance(value, list):
        raise ModuleError("color_ids ist keine Liste.")
    result: List[str] = []
    for raw in value:
        color_id = _require_text(raw, "color_id")
        if color_id not in allowed:
            raise ModuleError(f"Unbekannte Farbe: {color_id}")
        if color_id not in result:
            result.append(color_id)
    if len(result) > MAX_DAY_COLORS:
        raise ModuleError(f"Ein Tag kann höchstens {MAX_DAY_COLORS} Farben enthalten.")
    return result


def _drop_unknown_day_colors(store: Dict[str, Any]) -> None:
    allowed = {entry["id"] for entry in store["legend"]}
    for day in list(store["day_markers"]):
        colors = [item for item in store["day_markers"][day] if item in allowed][:MAX_DAY_COLORS]
        if colors:
            store["day_markers"][day] = colors
        else:
            del store["day_markers"][day]
    for appointment in store["appointments"]:
        if appointment.get("color_id") not in allowed:
            appointment["color_id"] = None


def _optional_time(value: Any) -> Optional[str]:
    if value in (None, ""):
        return None
    if not isinstance(value, str) or not TIME_PATTERN.match(value):
        raise ModuleError("Uhrzeit ist ungültig. Erwartet wird HH:MM.")
    return value


def _appointment_reminder_at(
    date_value: str, start_time: Optional[str], reminder_minutes: Optional[int]
) -> Optional[str]:
    if reminder_minutes is None:
        return None
    base_time = time.fromisoformat(start_time) if start_time else time(DEFAULT_REMINDER_HOUR, 0)
    appointment_at = datetime.combine(date.fromisoformat(date_value), base_time)
    return (appointment_at - timedelta(minutes=reminder_minutes)).replace(microsecond=0).isoformat()


def _reminder_relevant_fields_changed(before: Dict[str, Any], after: Dict[str, Any]) -> bool:
    fields = ("date", "start_time", "all_day", "reminder_minutes")
    return any(before.get(field) != after.get(field) for field in fields)


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
    return path if path.is_absolute() else REPO_ROOT / path


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ModuleError(f"JSON ist ungültig: {path}") from exc
    if not isinstance(data, dict):
        raise ModuleError(f"JSON-Wurzel ist kein Objekt: {path}")
    return data


def setup_logging(debug: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
