"""Modul-Einstieg mit bestehendem Datenvertrag und optionaler GUI."""

from __future__ import annotations

import sys
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from module import (  # noqa: E402,F401
    ModuleConfig,
    ModuleContext,
    ModuleError,
    build_response,
    build_ui,
    exit,
    handle_action,
    init,
    load_config,
    load_state,
    run,
    validateInput,
    validateOutput,
)
from window import FileManagerWindow, open_window  # noqa: E402,F401


def open_ui(parent=None, *, initial_path: Path | str | None = None) -> FileManagerWindow:
    """Öffnet die Dateimanager-Oberfläche innerhalb der Hauptanwendung."""
    return open_window(parent, initial_path=initial_path)
