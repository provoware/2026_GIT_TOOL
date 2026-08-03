"""Modul-Einstieg mit bestehendem Datenvertrag und optionaler GUI."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))


def _load_sibling(module_name: str, filename: str) -> ModuleType:
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    path = MODULE_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Datei-Manager-Komponente kann nicht geladen werden: {path}")
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = loaded
    try:
        spec.loader.exec_module(loaded)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return loaded


backend = _load_sibling("_genrearchiv_datei_manager_backend", "module.py")
window_module = _load_sibling("_genrearchiv_datei_manager_window", "window.py")

ModuleConfig = backend.ModuleConfig
ModuleContext = backend.ModuleContext
ModuleError = backend.ModuleError
FileManagerWindow = window_module.FileManagerWindow
open_window = window_module.open_window
build_response = backend.build_response
build_ui = backend.build_ui
handle_action = backend.handle_action
load_config = backend.load_config
load_state = backend.load_state
validateOutput = backend.validateOutput

_window_instance: FileManagerWindow | None = None


def _backend_context(context: dict[str, Any] | None) -> dict[str, Any]:
    cleaned = dict(context or {})
    config_path = cleaned.get("config_path")
    if config_path:
        try:
            if Path(config_path).name != "datei_manager.json":
                cleaned.pop("config_path", None)
        except TypeError:
            cleaned.pop("config_path", None)
    cleaned.pop("ui_parent", None)
    cleaned.pop("headless", None)
    return cleaned


def _default_parent():
    try:
        import tkinter as tk
    except ImportError:
        return None
    parent = getattr(tk, "_default_root", None)
    if parent is None:
        return None
    try:
        return parent if parent.winfo_exists() else None
    except Exception:
        return None


def open_ui(parent=None, *, initial_path: Path | str | None = None) -> FileManagerWindow:
    """Öffnet oder fokussiert die Dateimanager-Oberfläche."""
    global _window_instance
    if _window_instance is not None:
        try:
            if _window_instance.root.winfo_exists():
                _window_instance.root.deiconify()
                _window_instance.root.lift()
                _window_instance.root.focus_force()
                return _window_instance
        except Exception:
            _window_instance = None
    parent = parent or _default_parent()
    _window_instance = open_window(parent, initial_path=initial_path)
    return _window_instance


def _schedule_ui_open(initial_path: Path | str | None = None) -> bool:
    parent = _default_parent()
    if parent is None:
        return False
    parent.after_idle(lambda: open_ui(parent, initial_path=initial_path))
    return True


def validateInput(input_data: dict[str, Any]) -> None:
    if isinstance(input_data, dict) and input_data.get("action") == "open_browser":
        initial_path = input_data.get("path")
        if initial_path is not None and (
            not isinstance(initial_path, (str, Path)) or not str(initial_path).strip()
        ):
            raise ModuleError("path ist für open_browser ungültig.")
        return
    backend.validateInput(input_data)


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    validateInput(input_data)
    if input_data.get("action") != "open_browser":
        return backend.run(input_data)
    scheduled = _schedule_ui_open(input_data.get("path"))
    config = backend.load_config(_backend_context(input_data.get("context")))
    response = backend.build_response(
        status="ok" if scheduled else "error",
        message=(
            "Datei-Manager wird geöffnet."
            if scheduled
            else "Datei-Manager benötigt eine aktive grafische Hauptanwendung."
        ),
        data={"scheduled": scheduled},
        ui=backend.build_ui(config),
    )
    backend.validateOutput(response)
    return response


def init(context: dict[str, Any] | None = None) -> dict[str, Any]:
    response = backend.init(_backend_context(context))
    if response.get("status") == "ok" and not bool((context or {}).get("headless", False)):
        _schedule_ui_open()
    return response


def exit(context: ModuleContext | None = None) -> dict[str, Any]:
    global _window_instance
    if _window_instance is not None:
        try:
            if _window_instance.root.winfo_exists():
                _window_instance.root.destroy()
        except Exception:
            pass
        _window_instance = None
    return backend.exit(context)
