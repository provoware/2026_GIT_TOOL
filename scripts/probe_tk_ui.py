#!/usr/bin/env python3
"""Vermisst Launcher und Hauptfenster unter einem realen Tk/X11-Server."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "system"))

from config_models import load_gui_config
from launcher_gui import LauncherGui
from main_window import MainWindow
from ui_acceptance import DEVICE_PROFILES, DeviceProfile


INTERACTIVE_CLASSES = {
    "Button",
    "Checkbutton",
    "Entry",
    "Listbox",
    "Menubutton",
    "Radiobutton",
    "Scale",
    "Scrollbar",
    "Spinbox",
    "Text",
}


def _descendants(widget) -> list[Any]:
    result: list[Any] = []
    pending = list(widget.winfo_children())
    while pending:
        current = pending.pop(0)
        result.append(current)
        pending.extend(current.winfo_children())
    return result


def _widget_name(widget) -> str:
    label = ""
    try:
        label = str(widget.cget("text")).strip()
    except Exception:
        pass
    suffix = f" [{label[:80]}]" if label else ""
    return f"{widget.winfo_class()}:{widget}{suffix}"


def _measure(root, profile: DeviceProfile, surface: str) -> dict[str, Any]:
    root.update_idletasks()
    root.update()
    root.update_idletasks()

    root_x = root.winfo_rootx()
    root_y = root.winfo_rooty()
    root_width = root.winfo_width()
    root_height = root.winfo_height()
    overflow: list[dict[str, Any]] = []
    undersized: list[dict[str, Any]] = []
    focusable: list[str] = []

    for widget in _descendants(root):
        if not widget.winfo_ismapped():
            continue
        width = widget.winfo_width()
        height = widget.winfo_height()
        if width <= 1 or height <= 1:
            continue
        left = widget.winfo_rootx() - root_x
        top = widget.winfo_rooty() - root_y
        right = left + width
        bottom = top + height
        name = _widget_name(widget)
        if left < -1 or top < -1 or right > root_width + 1 or bottom > root_height + 1:
            overflow.append(
                {
                    "widget": name,
                    "bounds": [left, top, right, bottom],
                    "window": [root_width, root_height],
                }
            )
        widget_class = widget.winfo_class()
        if widget_class in INTERACTIVE_CLASSES:
            focusable.append(name)
            if profile.input_mode == "touch" and (width < 44 or height < 44):
                undersized.append(
                    {"widget": name, "width": width, "height": height}
                )

    return {
        "profile": profile.key,
        "surface": surface,
        "requested_size": [profile.width, profile.height],
        "actual_size": [root_width, root_height],
        "overflow_widgets": overflow,
        "focusable_count": len(focusable),
        "focusable_widgets": focusable,
        "undersized_touch_targets": undersized,
    }


def _capture(root, path: Path) -> None:
    executable = Path("/usr/bin/import")
    if not executable.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(executable), "-window", str(root.winfo_id()), str(path)],
        check=True,
        timeout=20,
    )


def _probe_surface(
    profile: DeviceProfile,
    surface: str,
    factory: Callable[[Any], Any],
    screenshots: Path | None,
) -> dict[str, Any]:
    import tkinter as tk

    root = tk.Tk()
    try:
        root.geometry(f"{profile.width}x{profile.height}+0+0")
        factory(root)
        root.geometry(f"{profile.width}x{profile.height}+0+0")
        record = _measure(root, profile, surface)
        if screenshots is not None:
            _capture(root, screenshots / f"{surface}__{profile.key}.png")
        return record
    finally:
        root.destroy()


def _launcher_factory(module_config: Path, gui_config):
    def build(root):
        original_autosave = LauncherGui._setup_autosave
        original_refresh = LauncherGui.request_refresh
        original_drag_drop = LauncherGui._setup_drag_drop
        try:
            LauncherGui._setup_autosave = lambda self: None
            LauncherGui.request_refresh = lambda self: None
            LauncherGui._setup_drag_drop = lambda self: None
            return LauncherGui(
                root=root,
                module_config=module_config,
                gui_config=gui_config,
                show_all=False,
                debug=False,
            )
        finally:
            LauncherGui._setup_autosave = original_autosave
            LauncherGui.request_refresh = original_refresh
            LauncherGui._setup_drag_drop = original_drag_drop

    return build


def _main_window_factory(module_config: Path, gui_config):
    def build(root):
        return MainWindow(
            root=root,
            module_config=module_config,
            gui_config=gui_config,
            debug=False,
            theme_name=gui_config.default_theme,
        )

    return build


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--screenshots", type=Path)
    parser.add_argument(
        "--profiles",
        nargs="*",
        default=[profile.key for profile in DEVICE_PROFILES],
    )
    args = parser.parse_args()

    os.environ["GENREARCHIV_WRITE_MODE"] = "read-only"
    module_config = ROOT / "config" / "modules.json"
    gui_config = load_gui_config(ROOT / "config" / "launcher_gui.json")
    selected = {key.strip() for key in args.profiles if key.strip()}
    profiles = [profile for profile in DEVICE_PROFILES if profile.key in selected]
    unknown = selected - {profile.key for profile in profiles}
    if unknown:
        raise SystemExit(f"Unbekannte Geräteprofile: {', '.join(sorted(unknown))}")

    records: list[dict[str, Any]] = []
    for profile in profiles:
        records.append(
            _probe_surface(
                profile,
                "launcher",
                _launcher_factory(module_config, gui_config),
                args.screenshots,
            )
        )
        records.append(
            _probe_surface(
                profile,
                "main_window",
                _main_window_factory(module_config, gui_config),
                args.screenshots,
            )
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"schema_version": 1, "records": records}, indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
