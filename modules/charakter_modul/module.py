"""Charakter-Modul für konsistente Profile mit Templates und Dashboard."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.data_model import (
    CharacterProfile,
    DataModelError,
    make_character_id,
    parse_iso_datetime,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "charakter_modul.json"


class ModuleError(ValueError):
    """Fehler im Charakter-Modul."""


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
        message="Charakter-Modul ist startbereit.",
        data={"data_path": str(config.data_path)},
        ui=build_ui(config),
    )


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validateInput(input_data)
        action = input_data["action"]
        config = load_config(input_data.get("context"))
        profiles = load_profiles(config.data_path)
        response = handle_action(action, input_data, config, profiles)
    except (ModuleError, DataModelError, FileNotFoundError) as exc:
        response = build_response(status="error", message=str(exc), data={}, ui={})

    validateOutput(response)
    return response


def exit(context: ModuleContext | None = None) -> Dict[str, Any]:
    if isinstance(context, ModuleContext):
        context.logger.debug("Charakter-Modul: Modul wird beendet.")
    return build_response(status="ok", message="Charakter-Modul sauber beendet.", data={}, ui={})


def validateInput(input_data: Dict[str, Any]) -> None:
    if not isinstance(input_data, dict):
        raise ModuleError("Eingabe fehlt oder ist kein Objekt (dict).")
    action = input_data.get("action")
    if action not in {
        "create_character",
        "update_character",
        "list_characters",
        "get_character",
        "toggle_favorite",
        "list_templates",
        "dashboard",
    }:
        raise ModuleError("action ist ungültig oder fehlt.")

    if action == "create_character":
        _require_text(input_data.get("name"), "name")
        _require_text(input_data.get("role"), "role")
        _require_text(input_data.get("archetype"), "archetype")
    if action == "update_character":
        _require_text(input_data.get("id"), "id")
    if action in {"get_character", "toggle_favorite"}:
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
    data_path = _resolve_path(raw.get("data_path", "data/charakter_modul.json"))
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
    profiles: List[CharacterProfile],
) -> Dict[str, Any]:
    if action == "list_templates":
        return build_response(
            status="ok",
            message="Templates geladen.",
            data={"templates": config.templates},
            ui=build_ui(config),
        )

    if action == "create_character":
        profile = create_character(profiles, input_data)
        save_profiles(config.data_path, profiles)
        return build_response(
            status="ok",
            message="Charakterprofil wurde erstellt.",
            data=profile.to_dict(),
            ui=build_ui(config),
        )

    if action == "update_character":
        profile = update_character(profiles, input_data)
        save_profiles(config.data_path, profiles)
        return build_response(
            status="ok",
            message="Charakterprofil wurde aktualisiert.",
            data=profile.to_dict(),
            ui=build_ui(config),
        )

    if action == "get_character":
        profile = find_profile(profiles, input_data.get("id"))
        return build_response(
            status="ok",
            message="Charakterprofil geladen.",
            data=profile.to_dict(),
            ui=build_ui(config),
        )

    if action == "toggle_favorite":
        profile = toggle_favorite(profiles, input_data)
        save_profiles(config.data_path, profiles)
        return build_response(
            status="ok",
            message="Favoritenstatus aktualisiert.",
            data=profile.to_dict(),
            ui=build_ui(config),
        )

    if action == "list_characters":
        filtered = filter_profiles(profiles, input_data)
        return build_response(
            status="ok",
            message="Charakterliste geladen.",
            data={"characters": [profile.to_dict() for profile in filtered]},
            ui=build_ui(config),
        )

    if action == "dashboard":
        stats = build_dashboard(profiles)
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
        data_path.write_text(json.dumps({"characters": []}, indent=2), encoding="utf-8")


def load_profiles(data_path: Path) -> List[CharacterProfile]:
    ensure_data_file(data_path)
    raw = _load_json(data_path)
    profiles_raw = raw.get("characters", [])
    if not isinstance(profiles_raw, list):
        raise ModuleError("characters ist kein Array.")
    return [CharacterProfile.from_dict(profile) for profile in profiles_raw]


def save_profiles(data_path: Path, profiles: List[CharacterProfile]) -> None:
    ensure_data_file(data_path)
    payload = {"characters": [profile.to_dict() for profile in profiles]}
    data_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    if not data_path.exists():
        raise ModuleError("Daten konnten nicht geschrieben werden.")


def create_character(
    profiles: List[CharacterProfile], input_data: Dict[str, Any]
) -> CharacterProfile:
    name = _require_text(input_data.get("name"), "name")
    role = _require_text(input_data.get("role"), "role")
    archetype = _require_text(input_data.get("archetype"), "archetype")
    biography = _require_text(input_data.get("biography", ""), "biography", allow_empty=True)
    appearance = _require_text(input_data.get("appearance", ""), "appearance", allow_empty=True)
    traits = _require_text_list(input_data.get("traits", []), "traits")
    goals = _require_text_list(input_data.get("goals", []), "goals")
    conflicts = _require_text_list(input_data.get("conflicts", []), "conflicts")
    relationships = _require_text_list(input_data.get("relationships", []), "relationships")
    voice_notes = _require_text(input_data.get("voice_notes", ""), "voice_notes", allow_empty=True)
    tags = _require_text_list(input_data.get("tags", []), "tags")
    template_id = _require_optional_text(input_data.get("template_id"), "template_id")
    custom_fields = _require_text_mapping(input_data.get("custom_fields", {}), "custom_fields")
    created_at = datetime.now()
    updated_at = created_at
    character_id = _ensure_unique_id(profiles, make_character_id(name, created_at))

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
        favorite=False,
        template_id=template_id,
        custom_fields=custom_fields,
        created_at=created_at,
        updated_at=updated_at,
    )
    profiles.append(profile)
    return profile


def update_character(
    profiles: List[CharacterProfile], input_data: Dict[str, Any]
) -> CharacterProfile:
    character_id = _require_text(input_data.get("id"), "id")
    profile = find_profile(profiles, character_id)
    updated_profile = CharacterProfile(
        character_id=profile.character_id,
        name=_require_text(input_data.get("name", profile.name), "name"),
        role=_require_text(input_data.get("role", profile.role), "role"),
        archetype=_require_text(input_data.get("archetype", profile.archetype), "archetype"),
        biography=_require_text(
            input_data.get("biography", profile.biography),
            "biography",
            allow_empty=True,
        ),
        appearance=_require_text(
            input_data.get("appearance", profile.appearance),
            "appearance",
            allow_empty=True,
        ),
        traits=_require_text_list(input_data.get("traits", profile.traits), "traits"),
        goals=_require_text_list(input_data.get("goals", profile.goals), "goals"),
        conflicts=_require_text_list(input_data.get("conflicts", profile.conflicts), "conflicts"),
        relationships=_require_text_list(
            input_data.get("relationships", profile.relationships), "relationships"
        ),
        voice_notes=_require_text(
            input_data.get("voice_notes", profile.voice_notes),
            "voice_notes",
            allow_empty=True,
        ),
        tags=_require_text_list(input_data.get("tags", profile.tags), "tags"),
        favorite=_require_bool(input_data.get("favorite", profile.favorite), "favorite"),
        template_id=_require_optional_text(
            input_data.get("template_id", profile.template_id), "template_id"
        ),
        custom_fields=_require_text_mapping(
            input_data.get("custom_fields", profile.custom_fields), "custom_fields"
        ),
        created_at=profile.created_at,
        updated_at=datetime.now(),
    )
    _replace_profile(profiles, updated_profile)
    return updated_profile


def toggle_favorite(
    profiles: List[CharacterProfile], input_data: Dict[str, Any]
) -> CharacterProfile:
    character_id = _require_text(input_data.get("id"), "id")
    profile = find_profile(profiles, character_id)
    updated_profile = CharacterProfile(
        character_id=profile.character_id,
        name=profile.name,
        role=profile.role,
        archetype=profile.archetype,
        biography=profile.biography,
        appearance=profile.appearance,
        traits=profile.traits,
        goals=profile.goals,
        conflicts=profile.conflicts,
        relationships=profile.relationships,
        voice_notes=profile.voice_notes,
        tags=profile.tags,
        favorite=not profile.favorite,
        template_id=profile.template_id,
        custom_fields=profile.custom_fields,
        created_at=profile.created_at,
        updated_at=datetime.now(),
    )
    _replace_profile(profiles, updated_profile)
    return updated_profile


def find_profile(profiles: List[CharacterProfile], character_id: Optional[str]) -> CharacterProfile:
    character_id = _require_text(character_id, "id")
    for profile in profiles:
        if profile.character_id == character_id:
            return profile
    raise ModuleError("Charakter-ID nicht gefunden.")


def filter_profiles(
    profiles: List[CharacterProfile], input_data: Dict[str, Any]
) -> List[CharacterProfile]:
    favorites_only = input_data.get("favorites_only", False)
    tag_filter = input_data.get("tag")
    query = input_data.get("query")

    filtered = profiles
    if favorites_only:
        filtered = [profile for profile in filtered if profile.favorite]
    if tag_filter:
        tag_text = _require_text(tag_filter, "tag")
        filtered = [profile for profile in filtered if tag_text in profile.tags]
    if query:
        query_text = _require_text(query, "query").lower()
        filtered = [
            profile
            for profile in filtered
            if query_text in profile.name.lower()
            or query_text in profile.biography.lower()
            or query_text in profile.role.lower()
        ]
    return filtered


def build_dashboard(profiles: List[CharacterProfile]) -> Dict[str, Any]:
    total = len(profiles)
    favorites = sum(1 for profile in profiles if profile.favorite)
    roles: Dict[str, int] = {}
    last_updated = None
    for profile in profiles:
        roles[profile.role] = roles.get(profile.role, 0) + 1
        if last_updated is None or profile.updated_at > last_updated:
            last_updated = profile.updated_at
    return {
        "total_characters": total,
        "favorite_characters": favorites,
        "role_counts": roles,
        "last_updated": last_updated.isoformat() if last_updated else None,
    }


def _replace_profile(profiles: List[CharacterProfile], updated_profile: CharacterProfile) -> None:
    for index, profile in enumerate(profiles):
        if profile.character_id == updated_profile.character_id:
            profiles[index] = updated_profile
            return
    raise ModuleError("Charakter-ID nicht gefunden.")


def _ensure_unique_id(profiles: List[CharacterProfile], base_id: str) -> str:
    if not any(profile.character_id == base_id for profile in profiles):
        return base_id
    counter = 2
    while True:
        candidate = f"{base_id}-{counter}"
        if not any(profile.character_id == candidate for profile in profiles):
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
    _require_text_list(template.get("sections", []), "sections")
    _require_text_list(template.get("prompts", []), "prompts")


def _require_text(value: Any, field_name: str, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ModuleError(f"{field_name} ist kein Text.")
    if not allow_empty and not value.strip():
        raise ModuleError(f"{field_name} ist leer.")
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
            item, field_name, allow_empty=True
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
