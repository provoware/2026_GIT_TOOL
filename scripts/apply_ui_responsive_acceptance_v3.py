#!/usr/bin/env python3
"""Kanonische Responsive-Integration mit viewportgerechter Kurzhilfe."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

import apply_ui_responsive_acceptance as base
import apply_ui_responsive_acceptance_v2 as v2

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LAUNCHER = ROOT / "system" / "launcher_gui.py"
DEFAULT_MAIN = ROOT / "system" / "main_window.py"
DEFAULT_ACCEPTANCE = ROOT / "system" / "ui_acceptance.py"

OLD_IMPORT = "from ui_responsive import resolve_launcher_layout\n"
NEW_IMPORT = (
    "from ui_responsive import resolve_launcher_help_text, resolve_launcher_layout\n"
)


def _normalize_help_template() -> None:
    v2._normalize_launcher_template()
    template = base.LAUNCHER_METHODS["_update_layout_by_width"]
    old = '''        layout = resolve_launcher_layout(width)
        self._update_wrap_length()
'''
    new = '''        layout = resolve_launcher_layout(width)
        if self.help_label is not None:
            self.help_label.configure(text=resolve_launcher_help_text(width))
        self._update_wrap_length()
'''
    if old not in template and new not in template:
        raise RuntimeError("Responsive-Hilfe-Template ist unbekannt.")
    base.LAUNCHER_METHODS["_update_layout_by_width"] = template.replace(old, new)
    base.LAUNCHER_IMPORT = NEW_IMPORT


def transform_launcher(source: str) -> str:
    _normalize_help_template()
    if OLD_IMPORT in source:
        source = source.replace(OLD_IMPORT, NEW_IMPORT, 1)
    elif NEW_IMPORT not in source:
        raise RuntimeError("Responsive-Launcher-Import fehlt.")
    result = base.transform_launcher(source)
    if OLD_IMPORT in result:
        raise RuntimeError("Veralteter Responsive-Import ist verblieben.")
    ast.parse(result)
    return result


def _collapse_repeated(text: str, fragment: str) -> str:
    repeated = fragment + fragment
    while repeated in text:
        text = text.replace(repeated, fragment, 1)
    return text


def _preserve_component_metrics(source: str, result: str) -> str:
    """Verhindert, dass der historische Responsive-Codemod Block-3-Metriken zurücksetzt."""
    if "from ui_components import register_component" not in source:
        return result
    menu_line = "        menu.configure(takefocus=1)\n"
    button_block = (
        "        for button in (self.activate_button, self.deactivate_button):\n"
        "            button.configure(takefocus=1)\n"
    )
    result = result.replace(
        "        menu.configure(padx=6, pady=8, takefocus=1)\n",
        menu_line,
        1,
    )
    result = result.replace(
        "        for button in (self.activate_button, self.deactivate_button):\n"
        "            button.configure(pady=7, takefocus=1)\n",
        button_block,
        1,
    )
    result = _collapse_repeated(result, menu_line)
    result = _collapse_repeated(result, button_block)
    return result


def transform_main(source: str) -> str:
    result = v2.transform_main(source)
    result = _preserve_component_metrics(source, result)
    ast.parse(result)
    return result


def transform_acceptance(source: str) -> str:
    return v2.transform_acceptance(source)


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
