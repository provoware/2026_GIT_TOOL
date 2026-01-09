"""Notiz-Editor-Modul mit Templates, Favoriten und Dashboard-Statistiken."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.data_model import (
    DataModelError,
    NoteEntry,
    make_note_id,
    parse_iso_datetime,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "notiz_editor.json"


class ModuleError(ValueError):
    """Fehler im Notiz-Editor-Modul."""


@dataclass(frozen=True)
class ModuleConfig:
    data_path: Path
    default_theme: str
    themes: Dict[str, Dict[str, str]]
    templates: List[Dict[str, Any]]
    ui: Dict[str, Any]
    debug: bool


@dataclass(frozen=True)
class ModuleContext:
    logger: logging.Logger


def init(context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    config = load_config(context)
    ensure_data_file(config.data_path)
    return build_response(
        status="ok",
        message="Notiz-Editor ist startbereit.",
        data={"data_path": str(config.data_path)},
        ui=build_ui(config),
    )


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validateInput(input_data)
        action = input_data["action"]
        config = load_config(input_data.get("context"))
        notes = load_notes(config.data_path)
        response = handle_action(action, input_data, config, notes)
    except (ModuleError, DataModelError, FileNotFoundError) as exc:
        response = build_response(status="error", message=str(exc), data={}, ui={})

    validateOutput(response)
    return response


def exit(context: ModuleContext | None = None) -> Dict[str, Any]:
    if isinstance(context, ModuleContext):
        context.logger.debug("Notiz-Editor: Modul wird beendet.")
    return build_response(
        status="ok", message="Notiz-Editor sauber beendet.", data={}, ui={}
    )


def validateInput(input_data: Dict[str, Any]) -> None:
    if not isinstance(input_data, dict):
        raise ModuleError("Eingabe fehlt oder ist kein Objekt (dict).")
    action = input_data.get("action")
    if action not in {
        "create_note",
        "update_note",
        "list_notes",
        "get_note",
        "toggle_favorite",
        "list_templates",
        "dashboard",
    }:
        raise ModuleError("action ist ungültig oder fehlt.")

    if action == "create_note":
        _require_text(input_data.get("title"), "title")
        _require_text(input_data.get("body"), "body")
    if action == "update_note":
        _require_text(input_data.get("id"), "id")
    if action in {"get_note", "toggle_favorite"}:
        _require_text(input_data.get("id"), "id")


def validateOutput(output: Dict[str, Any]) -> None:
    if not isinstance(output, dict):
        raise ModuleError("Ausgabe ist kein Objekt (dict).")
    status = output.get("status")
    if status not in {"ok", "error"}:
        raise ModuleError("Ausgabe-Status ist ungültig.")
    _require_text(output.get("message"), "message")
    if "data" not in output or "ui" not in output:
        raise ModuleError("Ausgabe enthält keine data- oder ui-Daten.")


def build_response(
    status: str, message: str, data: Dict[str, Any], ui: Dict[str, Any]
) -> Dict[str, Any]:
    response = {"status": status, "message": message, "data": data, "ui": ui}
    validateOutput(response)
    return response


def load_config(context: Optional[Dict[str, Any]] = None) -> ModuleConfig:
    context = context or {}
    config_path = _resolve_path(context.get("config_path", DEFAULT_CONFIG_PATH))
    if not config_path.exists():
        raise ModuleError(f"Konfiguration fehlt: {config_path}")
    raw = _load_json(config_path)
    data_path = _resolve_path(raw.get("data_path", "data/notiz_editor.json"))
    default_theme = _require_text(raw.get("default_theme"), "default_theme")
    themes = raw.get("themes")
    templates = raw.get("templates")
    ui = raw.get("ui", {})
    debug = bool(raw.get("debug", False))

    if not isinstance(themes, dict) or not themes:
        raise ModuleError("themes ist leer oder ungültig.")
    for name, theme in themes.items():
        _require_text(name, "theme_name")
        _validate_theme(theme)
    if default_theme not in themes:
        raise ModuleError("default_theme ist nicht in themes enthalten.")

    if not isinstance(templates, list) or not templates:
        raise ModuleError("templates ist leer oder ungültig.")
    for template in templates:
        _validate_template(template)

    if not isinstance(ui, dict):
        raise ModuleError("ui ist ungültig.")

    return ModuleConfig(
        data_path=data_path,
        default_theme=default_theme,
        themes=themes,
        templates=templates,
        ui=ui,
        debug=debug,
    )


def handle_action(
    action: str,
    input_data: Dict[str, Any],
    config: ModuleConfig,
    notes: List[NoteEntry],
) -> Dict[str, Any]:
    if action == "list_templates":
        return build_response(
            status="ok",
            message="Templates geladen.",
            data={"templates": config.templates},
            ui=build_ui(config),
        )

    if action == "create_note":
        entry = create_note(notes, input_data)
        save_notes(config.data_path, notes)
        return build_response(
            status="ok",
            message="Notiz wurde erstellt.",
            data=entry.to_dict(),
            ui=build_ui(config),
        )

    if action == "update_note":
        entry = update_note(notes, input_data)
        save_notes(config.data_path, notes)
        return build_response(
            status="ok",
            message="Notiz wurde aktualisiert.",
            data=entry.to_dict(),
            ui=build_ui(config),
        )

    if action == "get_note":
        entry = find_note(notes, input_data.get("id"))
        return build_response(
            status="ok",
            message="Notiz geladen.",
            data=entry.to_dict(),
            ui=build_ui(config),
        )

    if action == "toggle_favorite":
        entry = toggle_favorite(notes, input_data)
        save_notes(config.data_path, notes)
        return build_response(
            status="ok",
            message="Favoritenstatus aktualisiert.",
            data=entry.to_dict(),
            ui=build_ui(config),
        )

    if action == "list_notes":
        filtered = filter_notes(notes, input_data)
        return build_response(
            status="ok",
            message="Notizliste geladen.",
            data={"notes": [note.to_dict() for note in filtered]},
            ui=build_ui(config),
        )

    if action == "dashboard":
        stats = build_dashboard(notes)
        return build_response(
            status="ok",
            message="Dashboard-Statistiken erstellt.",
            data=stats,
            ui=build_ui(config),
        )

    raise ModuleError("Aktion wird nicht unterstützt.")


def build_ui(config: ModuleConfig) -> Dict[str, Any]:
    return {
        "themes": list(config.themes.keys()),
        "default_theme": config.default_theme,
        "menus": config.ui.get("menus", []),
        "actions": config.ui.get("actions", []),
        "dashboard_cards": config.ui.get("dashboard_cards", []),
    }


def ensure_data_file(data_path: Path) -> None:
    data_path.parent.mkdir(parents=True, exist_ok=True)
    if not data_path.exists():
        data_path.write_text(json.dumps({"notes": []}, indent=2), encoding="utf-8")


def load_notes(data_path: Path) -> List[NoteEntry]:
    ensure_data_file(data_path)
    raw = _load_json(data_path)
    notes_raw = raw.get("notes", [])
    if not isinstance(notes_raw, list):
        raise ModuleError("notes ist kein Array.")
    return [NoteEntry.from_dict(note) for note in notes_raw]


def save_notes(data_path: Path, notes: List[NoteEntry]) -> None:
    ensure_data_file(data_path)
    payload = {"notes": [note.to_dict() for note in notes]}
    data_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if not data_path.exists():
        raise ModuleError("Daten konnten nicht geschrieben werden.")


def create_note(notes: List[NoteEntry], input_data: Dict[str, Any]) -> NoteEntry:
    title = _require_text(input_data.get("title"), "title")
    body = _require_text(input_data.get("body"), "body")
    tags = _require_text_list(input_data.get("tags", []), "tags")
    template_id = _require_optional_text(input_data.get("template_id"), "template_id")
    custom_fields = _require_text_mapping(
        input_data.get("custom_fields", {}), "custom_fields"
    )
    created_at = datetime.now()
    updated_at = created_at
    note_id = _ensure_unique_id(notes, make_note_id(title, created_at))
    entry = NoteEntry(
        note_id=note_id,
        title=title,
        body=body,
        tags=tags,
        created_at=created_at,
        updated_at=updated_at,
        favorite=False,
        template_id=template_id,
        custom_fields=custom_fields,
    )
    notes.append(entry)
    return entry


def update_note(notes: List[NoteEntry], input_data: Dict[str, Any]) -> NoteEntry:
    note_id = _require_text(input_data.get("id"), "id")
    entry = find_note(notes, note_id)
    title = input_data.get("title", entry.title)
    body = input_data.get("body", entry.body)
    tags = input_data.get("tags", entry.tags)
    template_id = input_data.get("template_id", entry.template_id)
    custom_fields = input_data.get("custom_fields", entry.custom_fields)
    favorite = input_data.get("favorite", entry.favorite)

    updated_entry = NoteEntry(
        note_id=entry.note_id,
        title=_require_text(title, "title"),
        body=_require_text(body, "body"),
        tags=_require_text_list(tags, "tags"),
        created_at=entry.created_at,
        updated_at=datetime.now(),
        favorite=_require_bool(favorite, "favorite"),
        template_id=_require_optional_text(template_id, "template_id"),
        custom_fields=_require_text_mapping(custom_fields, "custom_fields"),
    )
    _replace_note(notes, updated_entry)
    return updated_entry


def toggle_favorite(notes: List[NoteEntry], input_data: Dict[str, Any]) -> NoteEntry:
    note_id = _require_text(input_data.get("id"), "id")
    entry = find_note(notes, note_id)
    new_status = not entry.favorite
    updated_entry = NoteEntry(
        note_id=entry.note_id,
        title=entry.title,
        body=entry.body,
        tags=entry.tags,
        created_at=entry.created_at,
        updated_at=datetime.now(),
        favorite=new_status,
        template_id=entry.template_id,
        custom_fields=entry.custom_fields,
    )
    _replace_note(notes, updated_entry)
    return updated_entry


def find_note(notes: List[NoteEntry], note_id: Optional[str]) -> NoteEntry:
    note_id = _require_text(note_id, "id")
    for entry in notes:
        if entry.note_id == note_id:
            return entry
    raise ModuleError("Notiz-ID nicht gefunden.")


def filter_notes(notes: List[NoteEntry], input_data: Dict[str, Any]) -> List[NoteEntry]:
    favorites_only = input_data.get("favorites_only", False)
    tag_filter = input_data.get("tag")
    query = input_data.get("query")

    filtered = notes
    if favorites_only:
        filtered = [note for note in filtered if note.favorite]
    if tag_filter:
        tag_text = _require_text(tag_filter, "tag")
        filtered = [note for note in filtered if tag_text in note.tags]
    if query:
        query_text = _require_text(query, "query").lower()
        filtered = [
            note
            for note in filtered
            if query_text in note.title.lower() or query_text in note.body.lower()
        ]
    return filtered


def build_dashboard(notes: List[NoteEntry]) -> Dict[str, Any]:
    total = len(notes)
    favorites = sum(1 for note in notes if note.favorite)
    tags: Dict[str, int] = {}
    last_updated = None
    for note in notes:
        for tag in note.tags:
            tags[tag] = tags.get(tag, 0) + 1
        if last_updated is None or note.updated_at > last_updated:
            last_updated = note.updated_at
    return {
        "total_notes": total,
        "favorite_notes": favorites,
        "tag_counts": tags,
        "last_updated": last_updated.isoformat() if last_updated else None,
    }


def _replace_note(notes: List[NoteEntry], updated_entry: NoteEntry) -> None:
    for index, note in enumerate(notes):
        if note.note_id == updated_entry.note_id:
            notes[index] = updated_entry
            return
    raise ModuleError("Notiz-ID nicht gefunden.")


def _ensure_unique_id(notes: List[NoteEntry], base_id: str) -> str:
    if not any(note.note_id == base_id for note in notes):
        return base_id
    counter = 2
    while True:
        candidate = f"{base_id}-{counter}"
        if not any(note.note_id == candidate for note in notes):
            return candidate
        counter += 1


def _validate_theme(theme: Any) -> None:
    if not isinstance(theme, dict):
        raise ModuleError("Theme ist kein Objekt (dict).")
    for key in ("primary", "accent", "background", "text"):
        _require_text(theme.get(key), key)


def _validate_template(template: Any) -> None:
    if not isinstance(template, dict):
        raise ModuleError("Template ist kein Objekt (dict).")
    _require_text(template.get("id"), "template_id")
    _require_text(template.get("name"), "template_name")
    _require_text(template.get("description"), "template_description")
    sections = template.get("sections", [])
    prompts = template.get("prompts", [])
    _require_text_list(sections, "sections")
    _require_text_list(prompts, "prompts")


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModuleError(f"{field_name} ist leer oder ungültig.")
    return value.strip()


def _require_optional_text(value: Any, field_name: str) -> Optional[str]:
    if value is None:
        return None
    return _require_text(value, field_name)


def _require_text_list(value: Any, field_name: str) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ModuleError(f"{field_name} ist keine Liste.")
    return [_require_text(item, field_name) for item in value]


def _require_text_mapping(value: Any, field_name: str) -> Dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ModuleError(f"{field_name} ist kein Objekt (dict).")
    mapping: Dict[str, str] = {}
    for key, item in value.items():
        mapping[_require_text(key, f"{field_name}-key")] = _require_text(
            item, field_name
        )
    return mapping


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ModuleError(f"{field_name} ist kein Wahrheitswert.")
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


def parse_timestamp(value: Any, field_name: str) -> datetime:
    try:
        return parse_iso_datetime(value, field_name)
    except DataModelError as exc:
        raise ModuleError(str(exc)) from exc
