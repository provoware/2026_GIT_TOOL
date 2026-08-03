#!/usr/bin/env python3
"""Kanonische Responsive-Integration mit verdichtetem 1024-Pixel-Profil."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

import apply_ui_responsive_acceptance as base

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LAUNCHER = ROOT / "system" / "launcher_gui.py"
DEFAULT_MAIN = ROOT / "system" / "main_window.py"
DEFAULT_ACCEPTANCE = ROOT / "system" / "ui_acceptance.py"


def _normalize_launcher_template() -> None:
    template = base.LAUNCHER_METHODS["_update_layout_by_width"]
    old_medium = '''            elif layout.mode == "medium":
                positions = {
                    self.theme_label: (0, 0, 1, "w"),
                    self.theme_menu: (0, 1, 1, "w"),
                    self.show_all_check: (1, 0, 2, "w"),
                    self.debug_check: (2, 0, 2, "w"),
                    self.autostart_check: (3, 0, 2, "w"),
                    self.diagnostics_button: (4, 0, 1, "ew"),
                    self.refresh_button: (4, 1, 1, "ew"),
                    self.main_window_button: (5, 0, 1, "ew"),
                    self.logout_button: (5, 1, 1, "ew"),
                }
'''
    new_medium = '''            elif layout.mode == "medium":
                positions = {
                    self.theme_label: (0, 0, 1, "w"),
                    self.theme_menu: (0, 1, 1, "w"),
                    self.show_all_check: (1, 0, 1, "w"),
                    self.debug_check: (1, 1, 1, "w"),
                    self.autostart_check: (2, 0, 2, "w"),
                    self.diagnostics_button: (3, 0, 1, "ew"),
                    self.refresh_button: (3, 1, 1, "ew"),
                    self.main_window_button: (4, 0, 1, "ew"),
                    self.logout_button: (4, 1, 1, "ew"),
                }
'''
    old_developer = '''            if layout.developer_columns == 4:
                positions = ((1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1))
                hint_span = 4
            else:
                positions = ((1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1))
                hint_span = 2
'''
    new_developer = '''            if layout.developer_columns == 4:
                positions = ((1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1))
                hint_span = 4
            elif layout.developer_columns == 3:
                positions = ((1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2))
                hint_span = 3
            else:
                positions = ((1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1))
                hint_span = 2
'''
    if old_medium not in template and new_medium not in template:
        raise RuntimeError("Mittleres Launcher-Template ist unbekannt.")
    if old_developer not in template and new_developer not in template:
        raise RuntimeError("Entwickler-Template ist unbekannt.")
    template = template.replace(old_medium, new_medium)
    template = template.replace(old_developer, new_developer)
    base.LAUNCHER_METHODS["_update_layout_by_width"] = template


def transform_launcher(source: str) -> str:
    _normalize_launcher_template()
    return base.transform_launcher(source)


def transform_main(source: str) -> str:
    return base.transform_main(source)


def transform_acceptance(source: str) -> str:
    import_line = (
        "from ui_responsive import MAIN_WINDOW_MIN_HEIGHT, MAIN_WINDOW_MIN_WIDTH\n"
    )
    if import_line not in source:
        anchor = "from typing import Any, Iterable, Mapping, Sequence\n"
        if anchor not in source:
            raise RuntimeError("Acceptance-Importanker fehlt.")
        source = source.replace(anchor, anchor + "\n" + import_line, 1)
    source = source.replace(
        '    SurfaceSpec("main_window", "Hauptfenster", 960, 680),\n',
        '    SurfaceSpec(\n'
        '        "main_window",\n'
        '        "Hauptfenster",\n'
        '        MAIN_WINDOW_MIN_WIDTH,\n'
        '        MAIN_WINDOW_MIN_HEIGHT,\n'
        '    ),\n',
        1,
    )
    if "MAIN_WINDOW_MIN_WIDTH" not in source or '"main_window"' not in source:
        raise RuntimeError("Acceptance-Mindestgröße konnte nicht integriert werden.")
    ast.parse(source)
    return source


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--launcher", type=Path, default=DEFAULT_LAUNCHER)
    parser.add_argument("--main-window", type=Path, default=DEFAULT_MAIN)
    parser.add_argument("--acceptance", type=Path, default=DEFAULT_ACCEPTANCE)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    launcher_source = args.launcher.read_text(encoding="utf-8")
    main_source = args.main_window.read_text(encoding="utf-8")
    acceptance_source = args.acceptance.read_text(encoding="utf-8")
    launcher_result = transform_launcher(launcher_source)
    main_result = transform_main(main_source)
    acceptance_result = transform_acceptance(acceptance_source)
    changed = (
        launcher_result != launcher_source
        or main_result != main_source
        or acceptance_result != acceptance_source
    )
    if args.check:
        return 1 if changed else 0
    if launcher_result != launcher_source:
        args.launcher.write_text(launcher_result, encoding="utf-8")
    if main_result != main_source:
        args.main_window.write_text(main_result, encoding="utf-8")
    if acceptance_result != acceptance_source:
        args.acceptance.write_text(acceptance_result, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
