#!/usr/bin/env python3
"""Integriert den gemeinsamen Themeadapter kontrolliert in beide UI-Dateien."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LAUNCHER = ROOT / "system" / "launcher_gui.py"
DEFAULT_MAIN_WINDOW = ROOT / "system" / "main_window.py"

LAUNCHER_IMPORT = '''from ui_theme_adapter import (
    UiThemeError,
    apply_theme_tree,
    apply_widget_style,
    build_status_palette,
    build_tooltip_style,
    resolve_contrast_theme,
    resolve_theme,
)
'''
MAIN_WINDOW_IMPORT = '''from ui_theme_adapter import (
    UiThemeError,
    apply_module_card_theme,
    apply_theme_tree,
    resolve_theme,
)
'''

LAUNCHER_METHODS = {
    "_resolve_contrast_theme": '''    def _resolve_contrast_theme(self) -> Optional[str]:
        try:
            return resolve_contrast_theme(self.gui_config)
        except UiThemeError as exc:
            raise GuiLauncherError(str(exc)) from exc''',
    "apply_theme": '''    def apply_theme(self, theme_name: str) -> None:
        clean_name = _require_text(theme_name, "theme_name")
        try:
            theme = resolve_theme(self.gui_config, clean_name, strict=True)
        except UiThemeError as exc:
            raise GuiLauncherError(str(exc)) from exc
        self.current_theme = theme.name
        self.component_theme = theme
        self.status_palette = build_status_palette(theme)
        self.tooltip_style = build_tooltip_style(theme)
        apply_theme_tree(self.root, theme, button_font=self.button_font)
        self._apply_status_style("success")''',
    "_apply_widget_style": '''    def _apply_widget_style(
        self,
        widget,
        background: str,
        foreground: str,
        accent: str,
        button_bg: str,
        button_fg: str,
    ) -> None:
        colors = {
            "background": background,
            "foreground": foreground,
            "accent": accent,
            "button_background": button_bg,
            "button_foreground": button_fg,
        }
        try:
            apply_widget_style(widget, colors, button_font=self.button_font)
        except UiThemeError as exc:
            raise GuiLauncherError(str(exc)) from exc''',
}

MODULE_WIDGET_METHODS = {
    "_apply_theme": '''    def _apply_theme(self, theme: Dict[str, str]) -> None:
        try:
            apply_module_card_theme(self, theme)
        except UiThemeError as exc:
            raise MainWindowError(str(exc)) from exc''',
}

MAIN_WINDOW_METHODS = {
    "_theme_colors": '''    def _theme_colors(self) -> Dict[str, str]:
        theme_key = self.theme_var.get() if self.theme_var is not None else self.theme_name
        try:
            return dict(resolve_theme(self.gui_config, theme_key, strict=False).colors)
        except UiThemeError as exc:
            raise MainWindowError(str(exc)) from exc''',
    "_apply_theme": '''    def _apply_theme(self) -> None:
        theme = self._theme_colors()
        try:
            apply_theme_tree(self.root, theme)
        except UiThemeError as exc:
            raise MainWindowError(str(exc)) from exc
        for module_widget in self.module_widgets:
            module_widget._apply_theme(theme)''',
}


def _replace_methods(source: str, class_name: str, replacements: Mapping[str, str]) -> str:
    tree = ast.parse(source)
    target_class = next(
        (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name),
        None,
    )
    if target_class is None:
        raise RuntimeError(f"Klasse fehlt: {class_name}")
    methods = {
        node.name: node
        for node in target_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    missing = sorted(set(replacements) - set(methods))
    if missing:
        raise RuntimeError(f"Methoden fehlen in {class_name}: {', '.join(missing)}")

    lines = source.splitlines(keepends=True)
    edits = []
    for name, replacement in replacements.items():
        node = methods[name]
        start = min([node.lineno] + [item.lineno for item in node.decorator_list]) - 1
        edits.append((start, node.end_lineno, replacement.rstrip("\n") + "\n"))
    for start, end, replacement in sorted(edits, reverse=True):
        lines[start:end] = [replacement]
    result = "".join(lines)
    ast.parse(result)
    return result


def transform_launcher(source: str) -> str:
    result = _replace_methods(source, "LauncherGui", LAUNCHER_METHODS)
    if LAUNCHER_IMPORT not in result:
        anchor = "from undo_redo import UndoRedoAction, UndoRedoError, UndoRedoManager\n"
        if anchor not in result:
            raise RuntimeError("Launcher-Importanker fehlt.")
        result = result.replace(anchor, LAUNCHER_IMPORT + anchor)
    ast.parse(result)
    return result


def transform_main_window(source: str) -> str:
    result = _replace_methods(source, "ModuleWidget", MODULE_WIDGET_METHODS)
    result = _replace_methods(result, "MainWindow", MAIN_WINDOW_METHODS)
    if MAIN_WINDOW_IMPORT not in result:
        anchor = (
            "from workspace_geometry import Rect, build_grid, clamp_rect, has_collision, "
            "move_rect, rect_overlap, resize_rect\n"
        )
        if anchor not in result:
            raise RuntimeError("Hauptfenster-Importanker fehlt.")
        result = result.replace(anchor, anchor + MAIN_WINDOW_IMPORT)
    ast.parse(result)
    return result


def _process(path: Path, transform, check: bool) -> bool:
    source = path.read_text(encoding="utf-8")
    result = transform(source)
    changed = result != source
    if changed and not check:
        path.write_text(result, encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--launcher", type=Path, default=DEFAULT_LAUNCHER)
    parser.add_argument("--main-window", type=Path, default=DEFAULT_MAIN_WINDOW)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    changed_launcher = _process(args.launcher, transform_launcher, args.check)
    changed_main = _process(args.main_window, transform_main_window, args.check)
    if args.check and (changed_launcher or changed_main):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
