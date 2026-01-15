"""Wavesurfer-Toolkit mit Markern, Regionen, Minimap und Exportprofilen."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from system.permission_guard import PermissionGuardError, require_write_access

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "media_wavesurfer.json"


class ModuleError(ValueError):
    """Fehler im Wavesurfer-Toolkit."""


@dataclass(frozen=True)
class ModuleConfig:
    data_path: Path
    default_theme: str
    themes: Dict[str, Dict[str, str]]
    ui: Dict[str, Any]
    export_profiles: List[Dict[str, Any]]
    minimap: Dict[str, Any]
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
            message="Wavesurfer-Toolkit ist startbereit.",
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
        context.logger.debug("Wavesurfer-Toolkit: Modul wird beendet.")
    return build_response(status="ok", message="Wavesurfer-Toolkit beendet.", data={}, ui={})


def validateInput(input_data: Dict[str, Any]) -> None:
    if not isinstance(input_data, dict):
        raise ModuleError("Eingabe fehlt oder ist kein Objekt (dict).")
    action = input_data.get("action")
    if action not in {
        "list_features",
        "add_marker",
        "add_region",
        "list_markers",
        "list_regions",
        "set_minimap",
        "export_profile",
    }:
        raise ModuleError("action ist ungültig oder fehlt.")

    if action == "add_marker":
        _require_number(input_data.get("time"), "time")
    if action == "add_region":
        _require_number(input_data.get("start"), "start")
        _require_number(input_data.get("end"), "end")
    if action == "set_minimap":
        if "height" not in input_data and "zoom" not in input_data:
            raise ModuleError("minimap benötigt height oder zoom.")
    if action == "export_profile":
        _require_text(input_data.get("profile_id"), "profile_id")


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
    data_path = _resolve_path(raw.get("data_path", "data/media_wavesurfer.json"))
    default_theme = _require_text(raw.get("default_theme"), "default_theme")
    themes = raw.get("themes")
    ui = raw.get("ui", {})
    export_profiles = raw.get("export_profiles", [])
    minimap = raw.get("minimap", {})
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

    if not isinstance(export_profiles, list) or not export_profiles:
        raise ModuleError("export_profiles ist leer oder ungültig.")
    for profile in export_profiles:
        _validate_export_profile(profile)

    if not isinstance(minimap, dict):
        raise ModuleError("minimap ist ungültig.")

    return ModuleConfig(
        data_path=data_path,
        default_theme=default_theme,
        themes=themes,
        ui=ui,
        export_profiles=export_profiles,
        minimap=minimap,
        debug=debug,
    )


def handle_action(
    action: str,
    input_data: Dict[str, Any],
    config: ModuleConfig,
    state: Dict[str, Any],
) -> Dict[str, Any]:
    if action == "list_features":
        return build_response(
            status="ok",
            message="Wavesurfer-Funktionen geladen.",
            data=_build_feature_payload(config, state),
            ui=build_ui(config),
        )

    if action == "add_marker":
        marker = _add_marker(state, input_data)
        _save_state(config, state)
        return build_response(
            status="ok",
            message="Marker wurde gespeichert.",
            data=marker,
            ui=build_ui(config),
        )

    if action == "add_region":
        region = _add_region(state, input_data)
        _save_state(config, state)
        return build_response(
            status="ok",
            message="Region wurde gespeichert.",
            data=region,
            ui=build_ui(config),
        )

    if action == "list_markers":
        return build_response(
            status="ok",
            message="Marker-Liste geladen.",
            data={"markers": state.get("markers", [])},
            ui=build_ui(config),
        )

    if action == "list_regions":
        return build_response(
            status="ok",
            message="Regionen-Liste geladen.",
            data={"regions": state.get("regions", [])},
            ui=build_ui(config),
        )

    if action == "set_minimap":
        minimap = _update_minimap(state, config, input_data)
        _save_state(config, state)
        return build_response(
            status="ok",
            message="Minimap-Einstellungen aktualisiert.",
            data={"minimap": minimap},
            ui=build_ui(config),
        )

    if action == "export_profile":
        profile_id = input_data.get("profile_id")
        profile = _find_export_profile(config.export_profiles, profile_id)
        return build_response(
            status="ok",
            message="Exportprofil geladen.",
            data={"profile": profile},
            ui=build_ui(config),
        )

    raise ModuleError("Aktion wird nicht unterstützt.")


def build_ui(config: ModuleConfig) -> Dict[str, Any]:
    return {
        "themes": list(config.themes.keys()),
        "default_theme": config.default_theme,
        "menus": config.ui.get("menus", []),
        "actions": config.ui.get("actions", []),
        "sections": config.ui.get("sections", []),
    }


def ensure_data_file(config: ModuleConfig) -> None:
    if config.data_path.exists():
        return
    require_write_access(Path(__file__), config.data_path, "data_init")
    payload = {
        "markers": [],
        "regions": [],
        "minimap": dict(config.minimap),
        "updated_at": _now_iso(),
    }
    config.data_path.parent.mkdir(parents=True, exist_ok=True)
    config.data_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_state(config: ModuleConfig) -> Dict[str, Any]:
    if not config.data_path.exists():
        ensure_data_file(config)
    raw = _load_json(config.data_path)
    if not isinstance(raw.get("markers", []), list):
        raise ModuleError("Marker-Liste ist ungültig.")
    if not isinstance(raw.get("regions", []), list):
        raise ModuleError("Regionen-Liste ist ungültig.")
    if not isinstance(raw.get("minimap", {}), dict):
        raise ModuleError("Minimap-Daten sind ungültig.")
    return raw


def _save_state(config: ModuleConfig, state: Dict[str, Any]) -> None:
    require_write_access(Path(__file__), config.data_path, "data_write")
    state["updated_at"] = _now_iso()
    config.data_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_feature_payload(config: ModuleConfig, state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "markers": state.get("markers", []),
        "regions": state.get("regions", []),
        "minimap": state.get("minimap", {}),
        "export_profiles": config.export_profiles,
    }


def _add_marker(state: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    marker = {
        "id": _make_id(),
        "time": float(input_data["time"]),
        "label": _optional_text(input_data.get("label"), "Marker"),
        "color": _optional_text(input_data.get("color"), "#38bdf8"),
    }
    markers = state.setdefault("markers", [])
    markers.append(marker)
    return marker


def _add_region(state: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    start = float(input_data["start"])
    end = float(input_data["end"])
    if end <= start:
        raise ModuleError("Region: end muss größer als start sein.")
    region = {
        "id": _make_id(),
        "start": start,
        "end": end,
        "label": _optional_text(input_data.get("label"), "Region"),
        "color": _optional_text(input_data.get("color"), "#22c55e"),
    }
    regions = state.setdefault("regions", [])
    regions.append(region)
    return region


def _update_minimap(
    state: Dict[str, Any],
    config: ModuleConfig,
    input_data: Dict[str, Any],
) -> Dict[str, Any]:
    minimap = dict(config.minimap)
    minimap.update(state.get("minimap", {}))
    if "height" in input_data:
        minimap["height"] = int(input_data["height"])
    if "zoom" in input_data:
        minimap["zoom"] = float(input_data["zoom"])
    state["minimap"] = minimap
    return minimap


def _find_export_profile(profiles: List[Dict[str, Any]], profile_id: str) -> Dict[str, Any]:
    for profile in profiles:
        if profile.get("id") == profile_id:
            return profile
    raise ModuleError("Exportprofil wurde nicht gefunden.")


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


def _validate_export_profile(profile: Dict[str, Any]) -> None:
    if not isinstance(profile, dict):
        raise ModuleError("Exportprofil ist ungültig.")
    _require_text(profile.get("id"), "export_profile.id")
    _require_text(profile.get("label"), "export_profile.label")
    _require_text(profile.get("format"), "export_profile.format")


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModuleError(f"{label} fehlt oder ist leer.")
    return value.strip()


def _require_number(value: object, label: str) -> float:
    if not isinstance(value, (int, float)):
        raise ModuleError(f"{label} ist keine Zahl.")
    return float(value)


def _optional_text(value: object, fallback: str) -> str:
    if value is None:
        return fallback
    if not isinstance(value, str) or not value.strip():
        return fallback
    return value.strip()


def _resolve_path(value: object) -> Path:
    if isinstance(value, Path):
        return value
    if not isinstance(value, str) or not value.strip():
        raise ModuleError("Pfad ist leer oder ungültig.")
    return Path(value).expanduser()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_id() -> str:
    return uuid.uuid4().hex
