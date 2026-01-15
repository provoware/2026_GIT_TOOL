#!/usr/bin/env python3
"""JSON-Validator: prüft Konfigurationsdateien auf gültige Struktur."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List

from config_utils import ensure_path
from logging_center import get_logger
from logging_center import setup_logging as setup_logging_center


class JsonValidationError(Exception):
    """Allgemeiner Fehler für den JSON-Validator."""


@dataclass(frozen=True)
class ValidationResult:
    path: Path
    issues: List[str]


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JsonValidationError(f"{label} fehlt oder ist leer.")
    return value.strip()


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise JsonValidationError(f"{label} ist kein Wahrheitswert (bool).")
    return value


def _require_list(value: object, label: str) -> list:
    if not isinstance(value, list):
        raise JsonValidationError(f"{label} ist keine Liste.")
    return value


def _require_dict(value: object, label: str) -> dict:
    if not isinstance(value, dict):
        raise JsonValidationError(f"{label} ist kein Objekt (dict).")
    return value


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise JsonValidationError(f"JSON ist nicht lesbar: {path}") from exc
    except json.JSONDecodeError as exc:
        raise JsonValidationError(f"JSON ist ungültig: {path}") from exc


def validate_modules_config(data: dict) -> None:
    modules = _require_list(data.get("modules"), "modules")
    _require_text(data.get("version", "1.0"), "version")
    if not modules:
        raise JsonValidationError("modules darf nicht leer sein.")
    for index, entry in enumerate(modules, start=1):
        entry_obj = _require_dict(entry, f"modules[{index}]")
        module_id = _require_module_id(entry_obj.get("id"), f"modules[{index}].id")
        _require_text(entry_obj.get("name"), f"modules[{index}].name")
        _require_module_path(entry_obj.get("path"), module_id, f"modules[{index}].path")
        _require_bool(entry_obj.get("enabled"), f"modules[{index}].enabled")
        _require_text(entry_obj.get("description"), f"modules[{index}].description")


def validate_launcher_gui_config(data: dict) -> None:
    default_theme = _require_text(data.get("default_theme"), "default_theme")
    themes = _require_dict(data.get("themes"), "themes")
    layout = _require_dict(data.get("layout"), "layout")
    refresh_debounce_ms = data.get("refresh_debounce_ms", 200)
    if not isinstance(refresh_debounce_ms, int) or refresh_debounce_ms < 50:
        raise JsonValidationError("refresh_debounce_ms muss mindestens 50 sein.")
    if not themes:
        raise JsonValidationError("themes darf nicht leer sein.")
    if default_theme not in themes:
        raise JsonValidationError("default_theme ist nicht in themes enthalten.")
    _validate_layout(layout)
    for name, entry in themes.items():
        theme_name = _require_text(name, "themes.key")
        entry_obj = _require_dict(entry, f"themes.{theme_name}")
        _require_text(entry_obj.get("label"), f"themes.{theme_name}.label")
        colors = _require_dict(entry_obj.get("colors"), f"themes.{theme_name}.colors")
        for key in (
            "background",
            "foreground",
            "accent",
            "button_background",
            "button_foreground",
            "status_success",
            "status_error",
            "status_busy",
            "status_foreground",
        ):
            _require_text(colors.get(key), f"themes.{theme_name}.colors.{key}")


def validate_test_gate_config(data: dict) -> None:
    threshold = data.get("threshold", 1)
    if not isinstance(threshold, int) or threshold <= 0:
        raise JsonValidationError("threshold muss eine positive Zahl sein.")
    _require_text(data.get("todo_path", "todo.txt"), "todo_path")
    _require_text(data.get("state_path", "data/test_state.json"), "state_path")
    tests_command = _require_list(data.get("tests_command", []), "tests_command")
    if not tests_command:
        raise JsonValidationError("tests_command darf nicht leer sein.")
    for item in tests_command:
        _require_text(item, "tests_command")


def validate_todo_config(data: dict) -> None:
    _require_text(data.get("todo_path"), "todo_path")
    _require_text(data.get("archive_path"), "archive_path")


def validate_filename_suffixes(data: dict) -> None:
    defaults = _require_dict(data.get("defaults"), "defaults")
    if not defaults:
        raise JsonValidationError("defaults darf nicht leer sein.")
    for key, value in defaults.items():
        _require_text(key, "defaults.key")
        suffix = _require_text(value, f"defaults.{key}")
        if not suffix.startswith("."):
            raise JsonValidationError(f"defaults.{key} muss mit '.' beginnen.")


def validate_pin_config(data: dict) -> None:
    enabled = data.get("enabled", False)
    if not isinstance(enabled, bool):
        raise JsonValidationError("enabled ist kein Wahrheitswert (bool).")
    _require_text(data.get("pin_hint"), "pin_hint")
    _require_text(data.get("pin_hash"), "pin_hash")
    _require_text(data.get("salt"), "salt")
    _require_int_min(data.get("max_attempts", 1), "max_attempts", 1)
    _require_int_min(data.get("lock_min_seconds", 1), "lock_min_seconds", 1)
    _require_int_min(data.get("lock_max_seconds", 1), "lock_max_seconds", 1)
    if data.get("lock_min_seconds", 1) > data.get("lock_max_seconds", 1):
        raise JsonValidationError("lock_min_seconds darf nicht größer als lock_max_seconds sein.")


def validate_manifest(data: dict, path: Path) -> None:
    _require_module_id(data.get("id"), f"{path.name}.id")
    _require_text(data.get("name"), f"{path.name}.name")
    _require_text(data.get("version"), f"{path.name}.version")
    _require_text(data.get("entry"), f"{path.name}.entry")


def _require_module_id(value: object, label: str) -> str:
    module_id = _require_text(value, label)
    if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", module_id):
        raise JsonValidationError(f"{label} muss snake_case sein (z. B. modul_name_1).")
    return module_id


def _require_module_path(value: object, module_id: str, label: str) -> str:
    path = _require_text(value, label)
    path_parts = Path(path).parts
    if len(path_parts) != 2 or path_parts[0] != "modules" or path_parts[1] != module_id:
        raise JsonValidationError(f"{label} muss 'modules/{module_id}' entsprechen.")
    return path


def _require_int_min(value: object, label: str, minimum: int) -> int:
    if not isinstance(value, int):
        raise JsonValidationError(f"{label} ist kein Integer.")
    if value < minimum:
        raise JsonValidationError(f"{label} muss mindestens {minimum} sein.")
    return value


def _validate_layout(layout: dict) -> None:
    _require_int_min(layout.get("gap_xs"), "layout.gap_xs", 0)
    _require_int_min(layout.get("gap_sm"), "layout.gap_sm", 0)
    _require_int_min(layout.get("gap_md"), "layout.gap_md", 0)
    _require_int_min(layout.get("gap_lg"), "layout.gap_lg", 0)
    _require_int_min(layout.get("gap_xl"), "layout.gap_xl", 0)
    _require_int_min(layout.get("button_padx"), "layout.button_padx", 0)
    _require_int_min(layout.get("button_pady"), "layout.button_pady", 0)
    _require_int_min(layout.get("button_min_width"), "layout.button_min_width", 0)
    _require_int_min(layout.get("button_font_size"), "layout.button_font_size", 8)
    _require_int_min(layout.get("field_padx"), "layout.field_padx", 0)
    _require_int_min(layout.get("field_pady"), "layout.field_pady", 0)
    _require_int_min(layout.get("focus_thickness"), "layout.focus_thickness", 0)
    text_spacing = _require_dict(layout.get("text_spacing"), "layout.text_spacing")
    _require_int_min(text_spacing.get("before"), "layout.text_spacing.before", 0)
    _require_int_min(text_spacing.get("line"), "layout.text_spacing.line", 0)
    _require_int_min(text_spacing.get("after"), "layout.text_spacing.after", 0)


VALIDATORS: Dict[str, Callable[[dict], None]] = {
    "modules.json": validate_modules_config,
    "launcher_gui.json": validate_launcher_gui_config,
    "test_gate.json": validate_test_gate_config,
    "todo_config.json": validate_todo_config,
    "filename_suffixes.json": validate_filename_suffixes,
    "pin.json": validate_pin_config,
}


def iter_json_files(root: Path) -> Iterable[Path]:
    config_dir = root / "config"
    if config_dir.exists():
        yield from sorted(config_dir.glob("*.json"))
    modules_dir = root / "modules"
    if modules_dir.exists():
        yield from sorted(modules_dir.glob("*/manifest.json"))


def validate_json_file(path: Path) -> ValidationResult:
    ensure_path(path, "json_path", JsonValidationError)
    try:
        data = _load_json(path)
    except JsonValidationError as exc:
        return ValidationResult(path=path, issues=[str(exc)])
    issues: List[str] = []
    validator = VALIDATORS.get(path.name)
    try:
        if path.name == "manifest.json":
            validate_manifest(data, path)
        elif validator is not None:
            validator(data)
    except JsonValidationError as exc:
        issues.append(str(exc))
    return ValidationResult(path=path, issues=issues)


def validate_all(root: Path) -> List[ValidationResult]:
    ensure_path(root, "root", JsonValidationError)
    results: List[ValidationResult] = []
    for path in iter_json_files(root):
        results.append(validate_json_file(path))
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="JSON-Validator: prüft Konfigurationsdateien und Manifeste.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Projektwurzel für die Prüfung.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Bei erstem Fehler abbrechen.",
    )
    parser.add_argument("--debug", action="store_true", help="Debug-Modus aktivieren.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging_center(args.debug)
    logger = get_logger("json_validator")
    results = validate_all(args.root)
    if not results:
        logger.error("Keine JSON-Dateien gefunden.")
        return 2
    total_issues = 0
    for result in results:
        if not result.issues:
            logger.info("JSON OK: %s", result.path)
            continue
        total_issues += len(result.issues)
        for issue in result.issues:
            logger.error("JSON-Problem in %s: %s", result.path, issue)
        if args.strict:
            return 2
    if total_issues:
        logger.error("JSON-Validierung: %s Problem(e) gefunden.", total_issues)
        return 2
    logger.info("JSON-Validierung: alle Prüfungen ok.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
