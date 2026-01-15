"""FFmpeg-Wrapper mit Presets, Auto-Name und Fortschrittsanzeige."""

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
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "media_ffmpeg_wrapper.json"


class ModuleError(ValueError):
    """Fehler im FFmpeg-Wrapper."""


@dataclass(frozen=True)
class ModuleConfig:
    data_path: Path
    output_dir: Path
    default_theme: str
    themes: Dict[str, Dict[str, str]]
    ui: Dict[str, Any]
    presets: List[Dict[str, Any]]
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
            message="FFmpeg-Wrapper ist startbereit.",
            data={"data_path": str(config.data_path), "output_dir": str(config.output_dir)},
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
        context.logger.debug("FFmpeg-Wrapper: Modul wird beendet.")
    return build_response(status="ok", message="FFmpeg-Wrapper beendet.", data={}, ui={})


def validateInput(input_data: Dict[str, Any]) -> None:
    if not isinstance(input_data, dict):
        raise ModuleError("Eingabe fehlt oder ist kein Objekt (dict).")
    action = input_data.get("action")
    if action not in {"list_presets", "build_command", "simulate_progress", "get_job"}:
        raise ModuleError("action ist ungültig oder fehlt.")

    if action == "build_command":
        _require_text(input_data.get("input_path"), "input_path")
        _require_text(input_data.get("preset_id"), "preset_id")
    if action in {"simulate_progress", "get_job"}:
        _require_text(input_data.get("job_id"), "job_id")


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
    data_path = _resolve_path(raw.get("data_path", "data/media_ffmpeg_jobs.json"))
    output_dir = _resolve_path(raw.get("output_dir", "data/ffmpeg_exports"))
    default_theme = _require_text(raw.get("default_theme"), "default_theme")
    themes = raw.get("themes")
    ui = raw.get("ui", {})
    presets = raw.get("presets", [])
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

    if not isinstance(presets, list) or not presets:
        raise ModuleError("presets ist leer oder ungültig.")
    for preset in presets:
        _validate_preset(preset)

    return ModuleConfig(
        data_path=data_path,
        output_dir=output_dir,
        default_theme=default_theme,
        themes=themes,
        ui=ui,
        presets=presets,
        debug=debug,
    )


def handle_action(
    action: str,
    input_data: Dict[str, Any],
    config: ModuleConfig,
    state: Dict[str, Any],
) -> Dict[str, Any]:
    if action == "list_presets":
        return build_response(
            status="ok",
            message="Presets geladen.",
            data={"presets": config.presets},
            ui=build_ui(config),
        )

    if action == "build_command":
        job = _create_job(config, state, input_data)
        _save_state(config, state)
        return build_response(
            status="ok",
            message="FFmpeg-Befehl erstellt.",
            data=job,
            ui=build_ui(config),
        )

    if action == "simulate_progress":
        progress = _advance_progress(state, input_data.get("job_id"))
        _save_state(config, state)
        return build_response(
            status="ok",
            message="Fortschritt aktualisiert.",
            data=progress,
            ui=build_ui(config),
        )

    if action == "get_job":
        job = _find_job(state, input_data.get("job_id"))
        return build_response(
            status="ok",
            message="Job geladen.",
            data=job,
            ui=build_ui(config),
        )

    raise ModuleError("Aktion wird nicht unterstützt.")


def build_ui(config: ModuleConfig) -> Dict[str, Any]:
    return {
        "themes": list(config.themes.keys()),
        "default_theme": config.default_theme,
        "menus": config.ui.get("menus", []),
        "actions": config.ui.get("actions", []),
        "tips": config.ui.get("tips", []),
    }


def ensure_data_file(config: ModuleConfig) -> None:
    if config.data_path.exists():
        return
    require_write_access(Path(__file__), config.data_path, "data_init")
    payload = {"jobs": [], "updated_at": _now_iso()}
    config.data_path.parent.mkdir(parents=True, exist_ok=True)
    config.data_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_state(config: ModuleConfig) -> Dict[str, Any]:
    if not config.data_path.exists():
        ensure_data_file(config)
    raw = _load_json(config.data_path)
    if not isinstance(raw.get("jobs", []), list):
        raise ModuleError("jobs ist ungültig.")
    return raw


def _save_state(config: ModuleConfig, state: Dict[str, Any]) -> None:
    require_write_access(Path(__file__), config.data_path, "data_write")
    state["updated_at"] = _now_iso()
    config.data_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _create_job(config: ModuleConfig, state: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    input_path = Path(input_data["input_path"]).expanduser()
    preset_id = input_data["preset_id"]
    preset = _find_preset(config.presets, preset_id)

    if not input_path.exists():
        raise ModuleError("Eingabedatei wurde nicht gefunden.")

    output_name = input_data.get("output_name")
    output_path = _build_output_path(config.output_dir, input_path, preset, output_name)

    require_write_access(Path(__file__), output_path, "output_prepare")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    job = {
        "job_id": uuid.uuid4().hex,
        "preset_id": preset_id,
        "input_path": str(input_path),
        "output_path": str(output_path),
        "command": _build_ffmpeg_command(input_path, output_path, preset),
        "progress": 0,
        "progress_index": 0,
        "created_at": _now_iso(),
    }
    state.setdefault("jobs", []).append(job)
    return job


def _build_output_path(
    output_dir: Path,
    input_path: Path,
    preset: Dict[str, Any],
    output_name: Optional[str],
) -> Path:
    output_dir = output_dir.expanduser()
    suffix = _require_text(preset.get("extension"), "preset.extension")
    if not suffix.startswith("."):
        suffix = f".{suffix}"

    if output_name:
        name = Path(output_name).stem
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        name = f"{input_path.stem}_{preset['id']}_{timestamp}"
    return output_dir / f"{name}{suffix}"


def _build_ffmpeg_command(input_path: Path, output_path: Path, preset: Dict[str, Any]) -> str:
    args = preset.get("args", [])
    if not isinstance(args, list):
        raise ModuleError("preset.args ist ungültig.")
    parts = ["ffmpeg", "-i", str(input_path)] + [str(arg) for arg in args] + [str(output_path)]
    return " ".join(parts)


def _advance_progress(state: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    job = _find_job(state, job_id)
    steps = [0, 25, 50, 75, 100]
    index = int(job.get("progress_index", 0))
    index = min(index + 1, len(steps) - 1)
    job["progress_index"] = index
    job["progress"] = steps[index]
    job["updated_at"] = _now_iso()
    return {"job_id": job_id, "progress": job["progress"], "done": job["progress"] >= 100}


def _find_job(state: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    for job in state.get("jobs", []):
        if job.get("job_id") == job_id:
            return job
    raise ModuleError("Job wurde nicht gefunden.")


def _find_preset(presets: List[Dict[str, Any]], preset_id: str) -> Dict[str, Any]:
    for preset in presets:
        if preset.get("id") == preset_id:
            return preset
    raise ModuleError("Preset wurde nicht gefunden.")


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


def _validate_preset(preset: Dict[str, Any]) -> None:
    if not isinstance(preset, dict):
        raise ModuleError("Preset ist ungültig.")
    _require_text(preset.get("id"), "preset.id")
    _require_text(preset.get("label"), "preset.label")
    _require_text(preset.get("extension"), "preset.extension")


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
