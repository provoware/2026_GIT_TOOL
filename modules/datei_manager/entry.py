"""Modul-Einstieg mit bestehendem Datenvertrag und optionaler GUI."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

import module as backend  # noqa: E402
from window import FileManagerWindow, open_window  # noqa: E402

ModuleConfig = backend.ModuleConfig
ModuleContext = backend.ModuleContext
ModuleError = backend.ModuleError
build_response = backend.build_response
build_ui = backend.build_ui
handle_action = backend.handle_action
load_config = backend.load_config
load_state = backend.load_state
run = backend.run
validateInput = backend.validateInput
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


def _schedule_ui_open() -> None:
    parent = _default_parent()
    if parent is None:
        return
    parent.after_idle(lambda: open_ui(parent))


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
