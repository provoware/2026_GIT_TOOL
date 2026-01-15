"""Professionelles Datei-Suchmodul mit Filtern, Organisation und Undo."""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from system.permission_guard import PermissionGuardError, require_write_access

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "datei_suche.json"


class ModuleError(ValueError):
    """Fehler im Datei-Suche-Modul."""


@dataclass(frozen=True)
class ModuleConfig:
    search_roots: List[Path]
    exclude_dirs: List[str]
    log_path: Path
    default_theme: str
    themes: Dict[str, Dict[str, str]]
    ui: Dict[str, Any]
    debug: bool
    max_results: int
    text_extensions: List[str]


@dataclass(frozen=True)
class ModuleContext:
    logger: logging.Logger


def init(context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        config = load_config(context)
        ensure_log_file(config.log_path)
        return build_response(
            status="ok",
            message="Datei-Suche ist bereit.",
            data={"search_roots": [str(path) for path in config.search_roots]},
            ui=build_ui(config),
        )
    except (ModuleError, PermissionGuardError) as exc:
        return build_response(status="error", message=str(exc), data={}, ui={})


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validateInput(input_data)
        action = input_data["action"]
        config = load_config(input_data.get("context"))
        ensure_log_file(config.log_path)

        if action == "search":
            result = search_files(config, input_data)
        elif action == "organize":
            result = organize_files(config, input_data)
        elif action == "undo":
            result = undo_last_action(config)
        elif action == "history":
            result = get_history(config)
        else:
            raise ModuleError("Unbekannte Aktion.")

        response = build_response(
            status="ok",
            message=result["message"],
            data=result["data"],
            ui=build_ui(config),
        )
    except (ModuleError, FileNotFoundError, PermissionError, PermissionGuardError) as exc:
        response = build_response(status="error", message=str(exc), data={}, ui={})

    validateOutput(response)
    return response


def exit(context: ModuleContext | None = None) -> Dict[str, Any]:
    if isinstance(context, ModuleContext):
        context.logger.debug("Datei-Suche: Modul wird beendet.")
    return build_response(status="ok", message="Datei-Suche sauber beendet.", data={}, ui={})


def validateInput(input_data: Dict[str, Any]) -> None:
    if not isinstance(input_data, dict):
        raise ModuleError("Eingabe fehlt oder ist kein Objekt (dict).")
    action = input_data.get("action")
    if action not in {"search", "organize", "undo", "history"}:
        raise ModuleError("action ist ungültig. Erlaubt: search, organize, undo, history.")
    if action == "organize":
        items = input_data.get("items")
        if not isinstance(items, list) or not items:
            raise ModuleError("items muss eine nicht-leere Liste sein.")


def validateOutput(output: Dict[str, Any]) -> None:
    if not isinstance(output, dict):
        raise ModuleError("Ausgabe ist kein Objekt (dict).")
    status = output.get("status")
    if status not in {"ok", "error"}:
        raise ModuleError("Ausgabe-Status ist ungültig.")
    if not isinstance(output.get("message"), str) or not output["message"].strip():
        raise ModuleError("Ausgabe enthält keine gültige message.")
    if "data" not in output or "ui" not in output:
        raise ModuleError("Ausgabe enthält keine data- oder ui-Daten.")


def build_response(
    status: str, message: str, data: Dict[str, Any], ui: Dict[str, Any]
) -> Dict[str, Any]:
    return {"status": status, "message": message, "data": data, "ui": ui}


def load_config(context: Optional[Dict[str, Any]] = None) -> ModuleConfig:
    context = context or {}
    config_path = _resolve_path(context.get("config_path", DEFAULT_CONFIG_PATH))
    if not config_path.exists():
        raise ModuleError(f"Konfiguration fehlt: {config_path}")
    raw = _load_json(config_path)
    search_roots = [_resolve_path(path) for path in raw.get("search_roots", ["~"])]
    exclude_dirs = raw.get("exclude_dirs", [])
    log_path = _resolve_path(raw.get("log_path", "data/datei_suche_log.json"))
    default_theme = _require_text(raw.get("default_theme"), "default_theme")
    themes = raw.get("themes")
    ui = raw.get("ui", {})
    debug = bool(raw.get("debug", False))
    max_results = int(raw.get("max_results", 500))
    text_extensions = raw.get("text_extensions", [])

    if not isinstance(themes, dict) or not themes:
        raise ModuleError("themes ist leer oder ungültig.")
    if default_theme not in themes:
        raise ModuleError("default_theme ist nicht in themes enthalten.")
    if not isinstance(ui, dict):
        raise ModuleError("ui ist ungültig.")
    if not isinstance(exclude_dirs, list):
        raise ModuleError("exclude_dirs ist ungültig.")
    if not isinstance(text_extensions, list) or not text_extensions:
        raise ModuleError("text_extensions ist leer oder ungültig.")

    return ModuleConfig(
        search_roots=search_roots,
        exclude_dirs=exclude_dirs,
        log_path=log_path,
        default_theme=default_theme,
        themes=themes,
        ui=ui,
        debug=debug,
        max_results=max_results,
        text_extensions=[ext.lower().lstrip(".") for ext in text_extensions],
    )


def search_files(config: ModuleConfig, input_data: Dict[str, Any]) -> Dict[str, Any]:
    query = input_data.get("query", {})
    if not isinstance(query, dict):
        raise ModuleError("query ist ungültig.")
    results: List[Dict[str, Any]] = []

    for root in config.search_roots:
        if not root.exists():
            continue
        for entry in iter_files(root, config.exclude_dirs):
            if len(results) >= config.max_results:
                break
            if matches_query(entry, query, config):
                results.append(build_file_info(entry))
        if len(results) >= config.max_results:
            break

    message = "Suche abgeschlossen." if results else "Keine passenden Dateien gefunden."
    return {"message": message, "data": {"results": results, "count": len(results)}}


def organize_files(config: ModuleConfig, input_data: Dict[str, Any]) -> Dict[str, Any]:
    items = input_data["items"]
    target_dir = _resolve_path(input_data.get("target_dir"))
    mode = input_data.get("mode", "move")
    if mode not in {"move", "copy"}:
        raise ModuleError("mode ist ungültig. Erlaubt: move, copy.")

    operations = []
    for item in items:
        if not isinstance(item, dict):
            raise ModuleError("items enthält ungültige Einträge.")
        source = _resolve_path(item.get("path"))
        if not source.exists():
            raise ModuleError(f"Datei fehlt: {source}")
        target_dir.mkdir(parents=True, exist_ok=True)
        target = _safe_target_path(target_dir / source.name)

        if mode == "move":
            shutil.move(str(source), str(target))
        else:
            shutil.copy2(str(source), str(target))

        operations.append(
            {
                "source": str(source),
                "target": str(target),
                "action": mode,
                "status": "ok",
            }
        )

    now = datetime.now(timezone.utc)
    log_batch = {
        "id": now.strftime("%Y%m%d%H%M%S"),
        "timestamp": now.isoformat(),
        "operations": operations,
        "undone": False,
    }
    append_log(config.log_path, log_batch)

    return {
        "message": "Organisation abgeschlossen.",
        "data": {"operations": operations, "count": len(operations)},
    }


def undo_last_action(config: ModuleConfig) -> Dict[str, Any]:
    history = load_log(config.log_path)
    if not history:
        raise ModuleError("Es gibt keine Aktionen zum Rückgängig machen.")

    last_batch = next((batch for batch in reversed(history) if not batch["undone"]), None)
    if not last_batch:
        raise ModuleError("Alle Aktionen wurden bereits rückgängig gemacht.")

    undone_ops = []
    for entry in last_batch["operations"]:
        action = entry.get("action")
        target = _resolve_path(entry["target"])
        source = _resolve_path(entry["source"])
        if action == "move" and target.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target), str(source))
            undone_ops.append({"source": str(source), "target": str(target)})
        elif action == "copy" and target.exists():
            target.unlink()
            undone_ops.append({"deleted": str(target)})

    last_batch["undone"] = True
    save_log(config.log_path, history)

    return {
        "message": "Letzte Aktion wurde rückgängig gemacht.",
        "data": {"undone": undone_ops, "batch_id": last_batch["id"]},
    }


def get_history(config: ModuleConfig) -> Dict[str, Any]:
    history = load_log(config.log_path)
    return {
        "message": "Historie geladen.",
        "data": {"history": history[-10:]},
    }


def iter_files(root: Path, exclude_dirs: Iterable[str]) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in exclude_dirs for part in path.parts):
            continue
        if path.is_file():
            yield path


def matches_query(entry: Path, query: Dict[str, Any], config: ModuleConfig) -> bool:
    name_contains = str(query.get("name_contains", "")).strip().lower()
    content_contains = str(query.get("content_contains", "")).strip().lower()
    extensions = [ext.lower().lstrip(".") for ext in query.get("extensions", [])]
    min_size = query.get("min_size")
    max_size = query.get("max_size")
    created_after = _parse_datetime(query.get("created_after"))
    created_before = _parse_datetime(query.get("created_before"))
    modified_after = _parse_datetime(query.get("modified_after"))
    modified_before = _parse_datetime(query.get("modified_before"))

    stat = entry.stat()
    size = stat.st_size
    created_at = datetime.fromtimestamp(stat.st_ctime)
    modified_at = datetime.fromtimestamp(stat.st_mtime)

    if name_contains and name_contains not in entry.name.lower():
        return False
    if extensions and entry.suffix.lower().lstrip(".") not in extensions:
        return False
    if min_size is not None and size < int(min_size):
        return False
    if max_size is not None and size > int(max_size):
        return False
    if created_after and created_at < created_after:
        return False
    if created_before and created_at > created_before:
        return False
    if modified_after and modified_at < modified_after:
        return False
    if modified_before and modified_at > modified_before:
        return False
    if content_contains:
        if entry.suffix.lower().lstrip(".") not in config.text_extensions:
            return False
        if not file_contains_text(entry, content_contains):
            return False

    return True


def file_contains_text(path: Path, needle: str) -> bool:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return needle.lower() in content.lower()


def build_file_info(entry: Path) -> Dict[str, Any]:
    stat = entry.stat()
    return {
        "name": entry.name,
        "path": str(entry),
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "extension": entry.suffix.lower().lstrip("."),
    }


def build_ui(config: ModuleConfig) -> Dict[str, Any]:
    return {
        "title": config.ui.get("title", "Datei-Suche"),
        "description": config.ui.get("description", ""),
        "themes": config.themes,
        "default_theme": config.default_theme,
        "panels": config.ui.get("panels", []),
        "actions": config.ui.get("actions", []),
        "accessibility": config.ui.get("accessibility", {}),
    }


def ensure_log_file(log_path: Path) -> None:
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        save_log(log_path, [])


def load_log(log_path: Path) -> List[Dict[str, Any]]:
    if not log_path.exists():
        return []
    return _load_json(log_path)


def save_log(log_path: Path, entries: List[Dict[str, Any]]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    require_write_access(Path(__file__), log_path, "Such-Log speichern")
    log_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def append_log(log_path: Path, entry: Dict[str, Any]) -> None:
    history = load_log(log_path)
    history.append(entry)
    save_log(log_path, history)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_path(value: Any) -> Path:
    if isinstance(value, Path):
        return value.expanduser()
    if isinstance(value, str) and value.strip():
        return Path(value).expanduser()
    raise ModuleError("Pfad ist ungültig oder fehlt.")


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModuleError(f"{field} ist ungültig oder fehlt.")
    return value.strip()


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value in {None, ""}:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            raise ModuleError("Datum/Zeit-Format ist ungültig. Nutze ISO-Format.")
    raise ModuleError("Datum/Zeit-Format ist ungültig.")


def _safe_target_path(target: Path) -> Path:
    if not target.exists():
        return target
    counter = 1
    while True:
        candidate = target.with_name(f"{target.stem}_{counter}{target.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1
