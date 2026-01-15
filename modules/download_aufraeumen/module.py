"""Download-Ordner professionell und interaktiv aufräumen."""

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
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "download_aufraeumen.json"


class ModuleError(ValueError):
    """Fehler im Download-Aufräumen-Modul."""


@dataclass(frozen=True)
class ModuleConfig:
    download_path: Path
    log_path: Path
    default_theme: str
    themes: Dict[str, Dict[str, str]]
    ui: Dict[str, Any]
    rules: List[Dict[str, Any]]
    debug: bool


@dataclass(frozen=True)
class ModuleContext:
    logger: logging.Logger


def init(context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        config = load_config(context)
        ensure_log_file(config.log_path)
        return build_response(
            status="ok",
            message="Download-Ordner ist bereit für die Aufräumübersicht.",
            data={"download_path": str(config.download_path)},
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

        if action == "scan":
            result = scan_downloads(config, input_data)
        elif action == "build_plan":
            result = build_plan(config, input_data)
        elif action == "apply_plan":
            result = apply_plan(config, input_data)
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
        context.logger.debug("Download-Aufräumen: Modul wird beendet.")
    return build_response(status="ok", message="Download-Aufräumen sauber beendet.", data={}, ui={})


def validateInput(input_data: Dict[str, Any]) -> None:
    if not isinstance(input_data, dict):
        raise ModuleError("Eingabe fehlt oder ist kein Objekt (dict).")
    action = input_data.get("action")
    if action not in {"scan", "build_plan", "apply_plan", "undo", "history"}:
        raise ModuleError(
            "action ist ungültig. Erlaubt: scan, build_plan, apply_plan, undo, history."
        )

    if action == "apply_plan":
        operations = input_data.get("operations")
        if not isinstance(operations, list) or not operations:
            raise ModuleError("operations muss eine nicht-leere Liste sein.")


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
    download_path = _resolve_path(raw.get("download_path", "~/Downloads"))
    log_path = _resolve_path(raw.get("log_path", "data/download_aufraeumen_log.json"))
    default_theme = _require_text(raw.get("default_theme"), "default_theme")
    themes = raw.get("themes")
    ui = raw.get("ui", {})
    rules = raw.get("rules", [])
    debug = bool(raw.get("debug", False))

    if not isinstance(themes, dict) or not themes:
        raise ModuleError("themes ist leer oder ungültig.")
    if default_theme not in themes:
        raise ModuleError("default_theme ist nicht in themes enthalten.")
    if not isinstance(ui, dict):
        raise ModuleError("ui ist ungültig.")
    if not isinstance(rules, list) or not rules:
        raise ModuleError("rules ist leer oder ungültig.")
    for rule in rules:
        _validate_rule(rule)

    return ModuleConfig(
        download_path=download_path,
        log_path=log_path,
        default_theme=default_theme,
        themes=themes,
        ui=ui,
        rules=rules,
        debug=debug,
    )


def scan_downloads(config: ModuleConfig, input_data: Dict[str, Any]) -> Dict[str, Any]:
    download_path = _resolve_path(input_data.get("download_path", config.download_path))
    include_hidden = bool(input_data.get("include_hidden", False))
    max_files = int(input_data.get("max_files", 5000))
    if not download_path.exists():
        raise ModuleError(f"Download-Ordner nicht gefunden: {download_path}")

    items: List[Dict[str, Any]] = []
    for entry in sorted(download_path.iterdir()):
        if len(items) >= max_files:
            break
        if entry.is_dir():
            continue
        if not include_hidden and entry.name.startswith("."):
            continue
        info = build_file_info(entry, config, download_path)
        items.append(info)

    summary = build_summary(items)
    message = "Download-Scan abgeschlossen." if items else "Download-Ordner ist bereits aufgeräumt."
    return {"message": message, "data": {"items": items, "summary": summary}}


def build_plan(config: ModuleConfig, input_data: Dict[str, Any]) -> Dict[str, Any]:
    items = input_data.get("items")
    if not isinstance(items, list) or not items:
        raise ModuleError("items muss eine nicht-leere Liste sein.")

    selected = set(input_data.get("selected", []))
    operations = []
    for item in items:
        if not isinstance(item, dict):
            raise ModuleError("items enthält ungültige Einträge.")
        source = item.get("path")
        target = item.get("suggested_target")
        if not source or not target:
            continue
        if selected and source not in selected:
            continue
        operations.append({"source": source, "target": target})

    if not operations:
        raise ModuleError("Es gibt keine ausgewählten Dateien zum Organisieren.")

    return {
        "message": "Aufräumplan wurde erstellt.",
        "data": {"operations": operations, "count": len(operations)},
    }


def apply_plan(config: ModuleConfig, input_data: Dict[str, Any]) -> Dict[str, Any]:
    operations = input_data["operations"]
    dry_run = bool(input_data.get("dry_run", False))
    now = datetime.now(timezone.utc)
    batch_id = now.strftime("%Y%m%d%H%M%S")
    batch_ops = []

    for entry in operations:
        if not isinstance(entry, dict):
            raise ModuleError("operations enthält ungültige Einträge.")
        source = _resolve_path(entry.get("source"))
        target_dir = _resolve_path(entry.get("target"))
        if not source.exists():
            raise ModuleError(f"Quelle fehlt: {source}")
        target_dir.mkdir(parents=True, exist_ok=True)
        target = _safe_target_path(target_dir / source.name)

        if not dry_run:
            shutil.move(str(source), str(target))

        batch_ops.append(
            {
                "source": str(source),
                "target": str(target),
                "action": "move",
                "status": "ok",
            }
        )

    log_batch = {
        "id": batch_id,
        "timestamp": now.isoformat(),
        "operations": batch_ops,
        "undone": False,
    }
    append_log(config.log_path, log_batch)

    message = (
        "Aufräumplan wurde simuliert (Testlauf)." if dry_run else "Aufräumplan wurde ausgeführt."
    )
    return {
        "message": message,
        "data": {"batch_id": batch_id, "operations": batch_ops},
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
        if entry.get("action") != "move":
            continue
        target = _resolve_path(entry["target"])
        source = _resolve_path(entry["source"])
        if target.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target), str(source))
            undone_ops.append({"source": str(source), "target": str(target)})

    last_batch["undone"] = True
    save_log(config.log_path, history)

    return {
        "message": "Letzte Aufräumaktion wurde rückgängig gemacht.",
        "data": {"undone": undone_ops, "batch_id": last_batch["id"]},
    }


def get_history(config: ModuleConfig) -> Dict[str, Any]:
    history = load_log(config.log_path)
    return {
        "message": "Historie geladen.",
        "data": {"history": history[-10:]},
    }


def build_file_info(entry: Path, config: ModuleConfig, base_path: Path) -> Dict[str, Any]:
    stat = entry.stat()
    category = categorize_file(entry, config.rules)
    suggested = base_path / category["folder"]
    return {
        "name": entry.name,
        "path": str(entry),
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "category": category["label"],
        "suggested_target": str(suggested),
    }


def build_summary(items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    item_list = list(items)
    total_size = sum(item.get("size_bytes", 0) for item in item_list)
    per_category: Dict[str, int] = {}
    for item in item_list:
        category = item.get("category", "Unbekannt")
        per_category[category] = per_category.get(category, 0) + 1
    return {
        "count": len(item_list),
        "total_size": total_size,
        "by_category": per_category,
    }


def categorize_file(entry: Path, rules: List[Dict[str, Any]]) -> Dict[str, str]:
    extension = entry.suffix.lower().lstrip(".")
    for rule in rules:
        extensions = [ext.lower().lstrip(".") for ext in rule.get("extensions", [])]
        if extension and extension in extensions:
            return {"label": rule["label"], "folder": rule["folder"]}
    fallback = next((rule for rule in rules if rule.get("fallback")), rules[-1])
    return {"label": fallback["label"], "folder": fallback["folder"]}


def build_ui(config: ModuleConfig) -> Dict[str, Any]:
    return {
        "title": config.ui.get("title", "Download-Ordner aufräumen"),
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
    require_write_access(Path(__file__), log_path, "Aufräum-Log speichern")
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


def _validate_rule(rule: Dict[str, Any]) -> None:
    if not isinstance(rule, dict):
        raise ModuleError("rules enthält ungültige Einträge.")
    _require_text(rule.get("label"), "rule.label")
    _require_text(rule.get("folder"), "rule.folder")
    extensions = rule.get("extensions", [])
    if not isinstance(extensions, list):
        raise ModuleError("rule.extensions muss eine Liste sein.")


def _safe_target_path(target: Path) -> Path:
    if not target.exists():
        return target
    counter = 1
    while True:
        candidate = target.with_name(f"{target.stem}_{counter}{target.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1
