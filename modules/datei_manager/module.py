"""Datei-Manager mit Quick-Rename, Tagging und Favoriten."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from system.filename_fixer import normalize_segment, resolve_target
from system.permission_guard import PermissionGuardError, require_write_access

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "datei_manager.json"


class ModuleError(ValueError):
    """Fehler im Datei-Manager."""


@dataclass(frozen=True)
class ModuleConfig:
    data_path: Path
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
        ensure_data_file(config)
        return build_response(
            status="ok",
            message="Datei-Manager ist startbereit.",
            data={"data_path": str(config.data_path)},
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
        context.logger.debug("Datei-Manager: Modul wird beendet.")
    return build_response(status="ok", message="Datei-Manager beendet.", data={}, ui={})


def validateInput(input_data: Dict[str, Any]) -> None:
    if not isinstance(input_data, dict):
        raise ModuleError("Eingabe fehlt oder ist kein Objekt (dict).")
    action = input_data.get("action")
    if action not in {
        "quick_rename",
        "tag_items",
        "toggle_favorite",
        "list_favorites",
        "list_tags",
    }:
        raise ModuleError("action ist ungültig oder fehlt.")

    if action == "quick_rename":
        _require_text(input_data.get("path"), "path")
        _require_text(input_data.get("new_name"), "new_name")
    if action == "tag_items":
        if not isinstance(input_data.get("paths"), list) or not input_data.get("paths"):
            raise ModuleError("paths muss eine nicht-leere Liste sein.")
        if not isinstance(input_data.get("tags"), list) or not input_data.get("tags"):
            raise ModuleError("tags muss eine nicht-leere Liste sein.")
    if action == "toggle_favorite":
        _require_text(input_data.get("path"), "path")


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
    status: str,
    message: str,
    data: Dict[str, Any],
    ui: Dict[str, Any],
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
    data_path = _resolve_path(raw.get("data_path", "data/datei_manager.json"))
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
        data_path=data_path,
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
    if action == "quick_rename":
        result = _quick_rename(input_data)
        _track_item(state, result["new_path"], input_data.get("tags"))
        _save_state(config, state)
        return build_response(
            status="ok",
            message="Datei wurde umbenannt.",
            data=result,
            ui=build_ui(config),
        )

    if action == "tag_items":
        updates = _tag_items(state, input_data)
        _save_state(config, state)
        return build_response(
            status="ok",
            message="Tags wurden gespeichert.",
            data={"items": updates},
            ui=build_ui(config),
        )

    if action == "toggle_favorite":
        favorite = _toggle_favorite(state, input_data)
        _save_state(config, state)
        return build_response(
            status="ok",
            message="Favorit wurde umgeschaltet.",
            data=favorite,
            ui=build_ui(config),
        )

    if action == "list_favorites":
        favorites = [
            _build_item_view(path, item)
            for path, item in sorted(state.get("items", {}).items())
            if item.get("favorite")
        ]
        return build_response(
            status="ok",
            message="Favoriten geladen.",
            data={"favorites": favorites},
            ui=build_ui(config),
        )

    if action == "list_tags":
        summary = _build_tag_summary(state)
        return build_response(
            status="ok",
            message="Tag-Übersicht geladen.",
            data={"tags": summary},
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


def ensure_data_file(config: ModuleConfig) -> None:
    if config.data_path.exists():
        return
    require_write_access(Path(__file__), config.data_path, "data_init")
    payload = {"items": {}, "updated_at": _now_iso()}
    config.data_path.parent.mkdir(parents=True, exist_ok=True)
    config.data_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_state(config: ModuleConfig) -> Dict[str, Any]:
    if not config.data_path.exists():
        ensure_data_file(config)
    raw = _load_json(config.data_path)
    if not isinstance(raw.get("items", {}), dict):
        raise ModuleError("items ist ungültig.")
    return raw


def _save_state(config: ModuleConfig, state: Dict[str, Any]) -> None:
    require_write_access(Path(__file__), config.data_path, "data_write")
    state["updated_at"] = _now_iso()
    config.data_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _quick_rename(input_data: Dict[str, Any]) -> Dict[str, Any]:
    path = Path(input_data["path"]).expanduser()
    if not path.exists():
        raise ModuleError("Datei wurde nicht gefunden.")
    if not path.is_file():
        raise ModuleError("Quick-Rename unterstützt nur Dateien.")

    new_name = _sanitize_name(input_data["new_name"], path.suffix)
    candidate = path.with_name(new_name)
    target = resolve_target(path, candidate)

    dry_run = bool(input_data.get("dry_run", False))
    if not dry_run:
        require_write_access(Path(__file__), target, "quick_rename")
        path.rename(target)
    return {
        "old_path": str(path),
        "new_path": str(target),
        "dry_run": dry_run,
    }


def _sanitize_name(new_name: str, fallback_suffix: str) -> str:
    raw = Path(new_name)
    stem = normalize_segment(raw.stem)
    suffix = "".join(raw.suffixes) or fallback_suffix
    return f"{stem}{suffix}"


def _track_item(state: Dict[str, Any], path: str, tags: Optional[List[str]]) -> None:
    items = state.setdefault("items", {})
    entry = items.get(path, {"tags": [], "favorite": False})
    if tags:
        entry["tags"] = _normalize_tags(tags)
    entry["updated_at"] = _now_iso()
    items[path] = entry


def _tag_items(state: Dict[str, Any], input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    paths = [str(Path(p).expanduser()) for p in input_data.get("paths", [])]
    tags = _normalize_tags(input_data.get("tags", []))
    items = state.setdefault("items", {})
    updates: List[Dict[str, Any]] = []
    for path in paths:
        entry = items.get(path, {"tags": [], "favorite": False})
        entry["tags"] = sorted(set(entry.get("tags", [])) | set(tags))
        entry["updated_at"] = _now_iso()
        items[path] = entry
        updates.append(_build_item_view(path, entry))
    return updates


def _toggle_favorite(state: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    path = str(Path(input_data["path"]).expanduser())
    items = state.setdefault("items", {})
    entry = items.get(path, {"tags": [], "favorite": False})
    entry["favorite"] = not bool(entry.get("favorite"))
    entry["updated_at"] = _now_iso()
    items[path] = entry
    return _build_item_view(path, entry)


def _build_tag_summary(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    summary: Dict[str, int] = {}
    for entry in state.get("items", {}).values():
        for tag in entry.get("tags", []):
            summary[tag] = summary.get(tag, 0) + 1
    return [{"tag": tag, "count": count} for tag, count in sorted(summary.items())]


def _build_item_view(path: str, entry: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "path": path,
        "tags": entry.get("tags", []),
        "favorite": bool(entry.get("favorite")),
        "updated_at": entry.get("updated_at"),
    }


def _normalize_tags(tags: List[Any]) -> List[str]:
    cleaned = []
    for tag in tags:
        if isinstance(tag, str) and tag.strip():
            cleaned.append(tag.strip().lower())
    return sorted(set(cleaned))


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
