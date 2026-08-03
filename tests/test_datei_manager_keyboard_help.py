from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = PROJECT_ROOT / "modules" / "datei_manager"
SYSTEM_DIR = PROJECT_ROOT / "system"
for import_path in (str(MODULE_DIR), str(SYSTEM_DIR)):
    if import_path not in sys.path:
        sys.path.insert(0, import_path)

from keyboard_help import SHORTCUT_HELP, build_help_text, install_keyboard_help  # noqa: E402


def test_help_text_covers_all_active_shortcuts():
    text = build_help_text()

    assert len(SHORTCUT_HELP) == 5
    for item in SHORTCUT_HELP:
        assert item.keys in text
        assert item.action in text
    assert "▲" in text
    assert "▼" in text


def test_entry_routes_all_window_starts_through_help_installer():
    entry_path = MODULE_DIR / "entry.py"
    spec = importlib.util.spec_from_file_location("datei_manager_entry_help_test", entry_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    calls = []
    sentinel = object()
    module.window_module.open_window = lambda parent=None, initial_path=None: sentinel
    module.keyboard_help_module.install_keyboard_help = calls.append

    result = module.open_window(initial_path=Path.home())

    assert result is sentinel
    assert calls == [sentinel]


def test_f1_opens_single_reusable_help_window(tmp_path: Path):
    import tkinter as tk

    window_path = MODULE_DIR / "window.py"
    spec = importlib.util.spec_from_file_location("datei_manager_window_help_test", window_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    root = tk.Tk()
    try:
        root.geometry("1000x640+0+0")
        app = module.FileManagerWindow(root, initial_path=tmp_path)
        install_keyboard_help(app)
        root.update_idletasks()

        assert root.cget("menu")
        assert callable(app.show_keyboard_help)
        assert app.show_keyboard_help() == "break"
        root.update_idletasks()
        first = app._keyboard_help_window
        assert first.winfo_exists()
        assert "Hilfe" in first.title()

        assert app.show_keyboard_help() == "break"
        assert app._keyboard_help_window is first
    finally:
        root.destroy()
