"""Profil-Manager mit getrennten Projektordnern."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from system.permission_guard import PermissionGuardError, require_write_access

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "profil_manager.json"


class ModuleError(ValueError):
    """Fehler im Profil-Manager."""


@dataclass(frozen=True)
class ModuleConfig:
    base_dir: Path
    state_path: Path
    default_theme: str
    themes: Dict[str, Dict[str, str]]
    ui: Dict[str, Any]
    debug: bool


@dataclass(frozen=True)
class ModuleContext:
    logger: logging.Logger


def init(context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        config = load_config(context)
        ensure_state(config)
        return build_response(
            status="ok",
            message="Profil-Manager ist startbereit.",
            data={"base_dir": str(config.base_dir)},
            ui=build_ui(config),
        )
    except (ModuleError, PermissionGuardError) as exc:
        return build_response(status="error", message=str(exc), data={}, ui={})


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validateInput(input_data)
        action = input_data["action"]
        config = load_config(input_data.get("context"))
        state = load_state(config)
        response = handle_action(action, input_data, config, state)
    except (ModuleError, PermissionGuardError, FileNotFoundError) as exc:
        response = build_response(status="error", message=str(exc), data={}, ui={})

    validateOutput(response)
    return response


def exit(context: ModuleContext | None = None) -> Dict[str, Any]:
    if isinstance(context, ModuleContext):
        context.logger.debug("Profil-Manager: Modul wird beendet.")
    return build_response(status="ok", message="Profil-Manager beendet.", data={}, ui={})


def validateInput(input_data: Dict[str, Any]) -> None:
    if not isinstance(input_data, dict):
        raise ModuleError("Eingabe fehlt oder ist kein Objekt (dict).")
    action = input_data.get("action")
    if action not in {
        "list_profiles",
        "create_profile",
        "set_active",
        "rename_profile",
        "delete_profile",
        "get_active",
    }:
        raise ModuleError("action ist ungültig oder fehlt.")

    if action in {"create_profile", "set_active", "delete_profile"}:
        _require_text(input_data.get("name"), "name")
    if action == "rename_profile":
        _require_text(input_data.get("from"), "from")
        _require_text(input_data.get("to"), "to")


def validateOutput(output: Dict[str, Any]) -> None:
    if not isinstance(output, dict):
        raise ModuleError("Ausgabe ist kein Objekt (dict).")
    status = output.get("status")
    if status not in {"ok", "error"}:
        raise ModuleError("Ausgabe-Status ist ungültig.")
    _require_text(output.get("message"), "message")
    if "data" not in output or "ui" not in output:
        raise ModuleError("Ausgabe enthält keine data- oder ui-Daten.")


def build_response(status: str, message: str, data: Dict[str, Any], ui: Dict[str, Any]) -> Dict[str, Any]:
    response = {"status": status, "message": message, "data": data, "ui": ui}
    validateOutput(response)
    return response


def load_config(context: Optional[Dict[str, Any]] = None) -> ModuleConfig:
    context = context or {}
    config_path = _resolve_path(context.get("config_path", DEFAULT_CONFIG_PATH))
    if not config_path.exists():
        raise ModuleError(f"Konfiguration fehlt: {config_path}")
    raw = _load_json(config_path)
    base_dir = _resolve_path(raw.get("base_dir", "data/profiles"))
    state_path = _resolve_path(raw.get("state_path", "data/profil_state.json"))
    default_theme = _require_text(raw.get("default_theme"), "default_theme")
    themes = raw.get("themes")
    ui = raw.get("ui", {})
    debug = bool(raw.get("debug", False))

    if not isinstance(themes, dict) or not themes:
        raise ModuleError("themes ist leer oder ungültig.")
    for name, theme in themes.items():
        _require_text(name, "theme_name")
        _validate_theme(theme)
    if default_theme not in themes:
        raise ModuleError("default_theme ist nicht in themes enthalten.")

    if not isinstance(ui, dict):
        raise ModuleError("ui ist ungültig.")

    return ModuleConfig(
        base_dir=base_dir,
        state_path=state_path,
        default_theme=default_theme,
        themes=themes,
        ui=ui,
        debug=debug,
    )


def handle_action(
    action: str,
    input_data: Dict[str, Any],
    config: ModuleConfig,
    state: Dict[str, Any],
) -> Dict[str, Any]:
    if action == "list_profiles":
        profiles = _list_profiles(config.base_dir)
        return build_response(
            status="ok",
            message="Profile geladen.",
            data={"profiles": profiles, "active": state.get("active_profile")},
            ui=build_ui(config),
        )

    if action == "create_profile":
        name = _normalize_profile_name(input_data.get("name"))
        profile = _create_profile(config, state, name)
        _save_state(config, state)
        return build_response(
            status="ok",
            message="Profil wurde erstellt.",
            data=profile,
            ui=build_ui(config),
        )

    if action == "set_active":
        name = _normalize_profile_name(input_data.get("name"))
        profile = _set_active_profile(config, state, name)
        _save_state(config, state)
        return build_response(
            status="ok",
            message="Aktives Profil gesetzt.",
            data=profile,
            ui=build_ui(config),
        )

    if action == "rename_profile":
        old = _normalize_profile_name(input_data.get("from"))
        new = _normalize_profile_name(input_data.get("to"))
        profile = _rename_profile(config, state, old, new)
        _save_state(config, state)
        return build_response(
            status="ok",
            message="Profil wurde umbenannt.",
            data=profile,
            ui=build_ui(config),
        )

    if action == "delete_profile":
        name = _normalize_profile_name(input_data.get("name"))
        profile = _delete_profile(config, state, name)
        _save_state(config, state)
        return build_response(
            status="ok",
            message="Profil wurde gelöscht.",
            data=profile,
            ui=build_ui(config),
        )

    if action == "get_active":
        active = state.get("active_profile")
        active_path = _profile_path(config.base_dir, active) if active else None
        return build_response(
            status="ok",
            message="Aktives Profil geladen.",
            data={"active": active, "path": str(active_path) if active_path else None},
            ui=build_ui(config),
        )

    raise ModuleError("Aktion wird nicht unterstützt.")


def build_ui(config: ModuleConfig) -> Dict[str, Any]:
    return {
        "themes": list(config.themes.keys()),
        "default_theme": config.default_theme,
        "menus": config.ui.get("menus", []),
        "actions": config.ui.get("actions", []),
        "hints": config.ui.get("hints", []),
    }


def ensure_state(config: ModuleConfig) -> None:
    if config.state_path.exists():
        return
    require_write_access(Path(__file__), config.state_path, "state_init")
    config.state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"active_profile": None, "profiles": {}, "updated_at": _now_iso()}
    config.state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_state(config: ModuleConfig) -> Dict[str, Any]:
    if not config.state_path.exists():
        ensure_state(config)
    raw = _load_json(config.state_path)
    if not isinstance(raw.get("profiles", {}), dict):
        raise ModuleError("profiles ist ungültig.")
    return raw


def _save_state(config: ModuleConfig, state: Dict[str, Any]) -> None:
    require_write_access(Path(__file__), config.state_path, "state_write")
    state["updated_at"] = _now_iso()
    config.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _create_profile(config: ModuleConfig, state: Dict[str, Any], name: str) -> Dict[str, Any]:
    base_dir = config.base_dir
    profile_dir = _profile_path(base_dir, name)
    if profile_dir.exists():
        raise ModuleError("Profil existiert bereits.")
    require_write_access(Path(__file__), profile_dir, "profile_create")
    _ensure_profile_dirs(profile_dir)
    state["profiles"][name] = {"created_at": _now_iso()}
    if not state.get("active_profile"):
        state["active_profile"] = name
    return {"name": name, "path": str(profile_dir), "active": state.get("active_profile") == name}


def _set_active_profile(config: ModuleConfig, state: Dict[str, Any], name: str) -> Dict[str, Any]:
    profile_dir = _profile_path(config.base_dir, name)
    if not profile_dir.exists():
        raise ModuleError("Profil wurde nicht gefunden.")
    state["active_profile"] = name
    return {"name": name, "path": str(profile_dir), "active": True}


def _rename_profile(config: ModuleConfig, state: Dict[str, Any], old: str, new: str) -> Dict[str, Any]:
    if old == new:
        raise ModuleError("Neuer Name ist identisch.")
    old_dir = _profile_path(config.base_dir, old)
    new_dir = _profile_path(config.base_dir, new)
    if not old_dir.exists():
        raise ModuleError("Altes Profil wurde nicht gefunden.")
    if new_dir.exists():
        raise ModuleError("Neuer Profilname existiert bereits.")
    require_write_access(Path(__file__), new_dir, "profile_rename")
    old_dir.rename(new_dir)
    state["profiles"].pop(old, None)
    state["profiles"][new] = {"created_at": _now_iso()}
    if state.get("active_profile") == old:
        state["active_profile"] = new
    return {"from": old, "to": new, "path": str(new_dir)}


def _delete_profile(config: ModuleConfig, state: Dict[str, Any], name: str) -> Dict[str, Any]:
    profile_dir = _profile_path(config.base_dir, name)
    if not profile_dir.exists():
        raise ModuleError("Profil wurde nicht gefunden.")
    if state.get("active_profile") == name:
        raise ModuleError("Aktives Profil kann nicht gelöscht werden.")
    require_write_access(Path(__file__), profile_dir, "profile_delete")
    for child in sorted(profile_dir.rglob("*"), reverse=True):
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    profile_dir.rmdir()
    state["profiles"].pop(name, None)
    return {"name": name, "deleted": True}


def _list_profiles(base_dir: Path) -> List[Dict[str, Any]]:
    if not base_dir.exists():
        return []
    profiles = []
    for entry in sorted(base_dir.iterdir()):
        if entry.is_dir() and not entry.name.startswith("."):
            profiles.append({"name": entry.name, "path": str(entry)})
    return profiles


def _ensure_profile_dirs(profile_dir: Path) -> None:
    profile_dir.mkdir(parents=True, exist_ok=True)
    for name in ["imports", "exports", "logs", "notes"]:
        (profile_dir / name).mkdir(parents=True, exist_ok=True)


def _profile_path(base_dir: Path, name: str) -> Path:
    return base_dir.expanduser() / name


def _normalize_profile_name(value: object) -> str:
    text = _require_text(value, "name")
    if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", text):
        raise ModuleError(
            "Profilname muss snake_case sein (z. B. projekt_01)."
        )
    return text


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ModuleError(f"JSON ist ungültig: {path}") from exc
    if not isinstance(data, dict):
        raise ModuleError("JSON ist kein Objekt (dict).")
    return data


def _validate_theme(theme: Dict[str, Any]) -> None:
    if not isinstance(theme, dict) or not theme:
        raise ModuleError("Theme ist ungültig.")
    for key, value in theme.items():
        _require_text(key, "theme_key")
        _require_text(value, "theme_value")


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModuleError(f"{label} fehlt oder ist leer.")
    return value.strip()


def _resolve_path(value: object) -> Path:
    if isinstance(value, Path):
        return value
    if not isinstance(value, str) or not value.strip():
        raise ModuleError("Pfad ist leer oder ungültig.")
    return Path(value).expanduser()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
