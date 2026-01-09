"""Zentrales Datenmodell für To-Dos und Kalenderansichten."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

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


@dataclass(frozen=True)
class NoteEntry:
    note_id: str
    title: str
    body: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    favorite: bool
    template_id: Optional[str]
    custom_fields: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        validate_note_entry(self)
        return {
            "id": self.note_id,
            "title": self.title,
            "body": self.body,
            "tags": list(self.tags),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "favorite": self.favorite,
            "template_id": self.template_id,
            "custom_fields": dict(self.custom_fields),
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "NoteEntry":
        if not isinstance(data, dict):
            raise DataModelError("Notiz-Daten sind kein Objekt (dict).")
        note_id = _require_text(data.get("id"), "id")
        title = _require_text(data.get("title"), "title")
        body = _require_text(data.get("body"), "body")
        tags = _require_list_of_text(data.get("tags", []), "tags")
        created_at = parse_iso_datetime(data.get("created_at"), "created_at")
        updated_at = parse_iso_datetime(data.get("updated_at"), "updated_at")
        favorite = _require_bool(data.get("favorite", False), "favorite")
        template_id = _require_optional_text(data.get("template_id"), "template_id")
        custom_fields = _require_mapping_of_text(
            data.get("custom_fields", {}), "custom_fields"
        )
        entry = NoteEntry(
            note_id=note_id,
            title=title,
            body=body,
            tags=tags,
            created_at=created_at,
            updated_at=updated_at,
            favorite=favorite,
            template_id=template_id,
            custom_fields=custom_fields,
        )
        validate_note_entry(entry)
        return entry


@dataclass(frozen=True)
class CharacterProfile:
    character_id: str
    name: str
    role: str
    archetype: str
    biography: str
    appearance: str
    traits: List[str]
    goals: List[str]
    conflicts: List[str]
    relationships: List[str]
    voice_notes: str
    tags: List[str]
    favorite: bool
    template_id: Optional[str]
    custom_fields: Dict[str, str]
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        validate_character_profile(self)
        return {
            "id": self.character_id,
            "name": self.name,
            "role": self.role,
            "archetype": self.archetype,
            "biography": self.biography,
            "appearance": self.appearance,
            "traits": list(self.traits),
            "goals": list(self.goals),
            "conflicts": list(self.conflicts),
            "relationships": list(self.relationships),
            "voice_notes": self.voice_notes,
            "tags": list(self.tags),
            "favorite": self.favorite,
            "template_id": self.template_id,
            "custom_fields": dict(self.custom_fields),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "CharacterProfile":
        if not isinstance(data, dict):
            raise DataModelError("Charakter-Daten sind kein Objekt (dict).")
        character_id = _require_text(data.get("id"), "id")
        name = _require_text(data.get("name"), "name")
        role = _require_text(data.get("role"), "role")
        archetype = _require_text(data.get("archetype"), "archetype")
        biography = _require_text(data.get("biography"), "biography", allow_empty=True)
        appearance = _require_text(data.get("appearance"), "appearance", allow_empty=True)
        traits = _require_list_of_text(data.get("traits", []), "traits")
        goals = _require_list_of_text(data.get("goals", []), "goals")
        conflicts = _require_list_of_text(data.get("conflicts", []), "conflicts")
        relationships = _require_list_of_text(data.get("relationships", []), "relationships")
        voice_notes = _require_text(
            data.get("voice_notes", ""), "voice_notes", allow_empty=True
        )
        tags = _require_list_of_text(data.get("tags", []), "tags")
        favorite = _require_bool(data.get("favorite", False), "favorite")
        template_id = _require_optional_text(data.get("template_id"), "template_id")
        custom_fields = _require_mapping_of_text(
            data.get("custom_fields", {}), "custom_fields"
        )
        created_at = parse_iso_datetime(data.get("created_at"), "created_at")
        updated_at = parse_iso_datetime(data.get("updated_at"), "updated_at")
        profile = CharacterProfile(
            character_id=character_id,
            name=name,
            role=role,
            archetype=archetype,
            biography=biography,
            appearance=appearance,
            traits=traits,
            goals=goals,
            conflicts=conflicts,
            relationships=relationships,
            voice_notes=voice_notes,
            tags=tags,
            favorite=favorite,
            template_id=template_id,
            custom_fields=custom_fields,
            created_at=created_at,
            updated_at=updated_at,
        )
        validate_character_profile(profile)
        return profile


def parse_iso_date(value: Any, field_name: str) -> date:
    if not isinstance(value, str) or not value:
        raise DataModelError(f"{field_name} fehlt oder ist kein Text.")
    if not DATE_PATTERN.match(value):
        raise DataModelError(f"{field_name} ist ungültig. Erwartet: JJJJ-MM-TT.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DataModelError(f"{field_name} ist kein gültiges Datum.") from exc


def parse_iso_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise DataModelError(f"{field_name} fehlt oder ist kein Text.")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise DataModelError(f"{field_name} ist kein gültiger Zeitstempel.") from exc


def make_todo_id(title: str, planned_date: date) -> str:
    if not isinstance(title, str) or not title.strip():
        raise DataModelError("Titel fehlt oder ist leer.")
    if not isinstance(planned_date, date):
        raise DataModelError("planned_date ist kein Datum.")
    slug = _slugify(title)
    return f"{planned_date.strftime('%Y%m%d')}-{slug}"


def make_note_id(title: str, created_at: datetime) -> str:
    if not isinstance(title, str) or not title.strip():
        raise DataModelError("Titel fehlt oder ist leer.")
    if not isinstance(created_at, datetime):
        raise DataModelError("created_at ist kein Zeitstempel.")
    slug = _slugify(title)
    return f"{created_at.strftime('%Y%m%d%H%M%S')}-{slug}"


def make_character_id(name: str, created_at: datetime) -> str:
    if not isinstance(name, str) or not name.strip():
        raise DataModelError("Name fehlt oder ist leer.")
    if not isinstance(created_at, datetime):
        raise DataModelError("created_at ist kein Zeitstempel.")
    slug = _slugify(name)
    return f"{created_at.strftime('%Y%m%d%H%M%S')}-{slug}"


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


def validate_note_entry(entry: NoteEntry) -> None:
    if not isinstance(entry, NoteEntry):
        raise DataModelError("entry ist keine NoteEntry.")
    _require_text(entry.note_id, "note_id")
    _require_text(entry.title, "title")
    _require_text(entry.body, "body")
    _require_list_of_text(entry.tags, "tags")
    if not isinstance(entry.created_at, datetime):
        raise DataModelError("created_at ist kein Zeitstempel.")
    if not isinstance(entry.updated_at, datetime):
        raise DataModelError("updated_at ist kein Zeitstempel.")
    _require_bool(entry.favorite, "favorite")
    _require_optional_text(entry.template_id, "template_id")
    _require_mapping_of_text(entry.custom_fields, "custom_fields")


def validate_character_profile(profile: CharacterProfile) -> None:
    if not isinstance(profile, CharacterProfile):
        raise DataModelError("profile ist kein CharacterProfile.")
    _require_text(profile.character_id, "character_id")
    _require_text(profile.name, "name")
    _require_text(profile.role, "role")
    _require_text(profile.archetype, "archetype")
    _require_text(profile.biography, "biography", allow_empty=True)
    _require_text(profile.appearance, "appearance", allow_empty=True)
    _require_list_of_text(profile.traits, "traits")
    _require_list_of_text(profile.goals, "goals")
    _require_list_of_text(profile.conflicts, "conflicts")
    _require_list_of_text(profile.relationships, "relationships")
    _require_text(profile.voice_notes, "voice_notes", allow_empty=True)
    _require_list_of_text(profile.tags, "tags")
    _require_bool(profile.favorite, "favorite")
    _require_optional_text(profile.template_id, "template_id")
    _require_mapping_of_text(profile.custom_fields, "custom_fields")
    if not isinstance(profile.created_at, datetime):
        raise DataModelError("created_at ist kein Zeitstempel.")
    if not isinstance(profile.updated_at, datetime):
        raise DataModelError("updated_at ist kein Zeitstempel.")


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return cleaned or "aufgabe"


def _require_text(value: Any, field_name: str, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise DataModelError(f"{field_name} ist kein Text.")
    if not allow_empty and not value.strip():
        raise DataModelError(f"{field_name} ist leer.")
    return value


def _require_optional_text(value: Any, field_name: str) -> Optional[str]:
    if value is None:
        return None
    return _require_text(value, field_name)


def _require_list_of_text(value: Any, field_name: str) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise DataModelError(f"{field_name} ist keine Liste.")
    normalized: List[str] = []
    for item in value:
        normalized.append(_require_text(item, field_name))
    return normalized


def _require_mapping_of_text(value: Any, field_name: str) -> Dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise DataModelError(f"{field_name} ist kein Objekt (dict).")
    normalized: Dict[str, str] = {}
    for key, item in value.items():
        key_text = _require_text(key, f"{field_name}-key")
        normalized[key_text] = _require_text(item, field_name, allow_empty=True)
    return normalized


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise DataModelError(f"{field_name} ist kein Wahrheitswert.")
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
