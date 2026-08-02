#!/usr/bin/env python3
"""Wendet Gate 2 kontrolliert auf system/main_window.py an."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "system" / "main_window.py"
IMPORT = "from workspace_geometry import Rect, build_grid, clamp_rect, has_collision, move_rect, rect_overlap, resize_rect\n"
METHODS = {
    "_layout_modules": '''    def _layout_modules(self) -> None:\n        if self.workspace is None:\n            return\n        width = self.workspace.winfo_width()\n        height = self.workspace.winfo_height()\n        if width < 10 or height < 10:\n            return\n        if self._layout_ready:\n            self._ensure_within_bounds(width, height)\n            return\n        rects = build_grid(len(self.module_widgets), width, height, rows=3, cols=3, gap=12, min_width=200, min_height=160)\n        for widget, rect in zip(self.module_widgets, rects):\n            widget.rect = rect\n            widget.last_valid_rect = rect\n            widget.frame.place(x=rect.x, y=rect.y, width=rect.width, height=rect.height)\n        self._layout_ready = True\n''',
    "_ensure_within_bounds": '''    def _ensure_within_bounds(self, width: int, height: int) -> None:\n        for widget in self.module_widgets:\n            candidate = clamp_rect(widget.rect, width, height)\n            if candidate != widget.rect:\n                widget.rect = candidate\n                widget.last_valid_rect = candidate\n                widget.frame.place(x=candidate.x, y=candidate.y, width=candidate.width, height=candidate.height)\n''',
    "_drag_widget": '''    def _drag_widget(self, widget: ModuleWidget, delta_x: int, delta_y: int) -> None:\n        candidate = move_rect(widget.rect, delta_x, delta_y, self.workspace.winfo_width(), self.workspace.winfo_height())\n        if self._is_collision(candidate, widget):\n            widget.frame.place(x=widget.last_valid_rect.x, y=widget.last_valid_rect.y, width=widget.last_valid_rect.width, height=widget.last_valid_rect.height)\n            self._set_status("Position blockiert: Module dürfen sich nicht überlappen.", self._theme_colors()["status_error"])\n            return\n        widget.rect = candidate\n        widget.last_valid_rect = candidate\n        widget.frame.place(x=candidate.x, y=candidate.y, width=candidate.width, height=candidate.height)\n''',
    "_resize_widget": '''    def _resize_widget(self, widget: ModuleWidget, width: int, height: int) -> None:\n        candidate = resize_rect(widget.rect, width, height, self.workspace.winfo_width(), self.workspace.winfo_height(), widget.min_width, widget.min_height)\n        if self._is_collision(candidate, widget):\n            widget.frame.place(x=widget.last_valid_rect.x, y=widget.last_valid_rect.y, width=widget.last_valid_rect.width, height=widget.last_valid_rect.height)\n            self._set_status("Größe blockiert: Module dürfen sich nicht überlappen.", self._theme_colors()["status_error"])\n            return\n        widget.rect = candidate\n        widget.last_valid_rect = candidate\n        widget.frame.place(x=candidate.x, y=candidate.y, width=candidate.width, height=candidate.height)\n''',
    "_is_collision": '''    def _is_collision(self, candidate: Rect, current: ModuleWidget) -> bool:\n        return has_collision(candidate, (widget.rect for widget in self.module_widgets if widget is not current))\n''',
    "_rect_overlap": '''    @staticmethod\n    def _rect_overlap(a: Rect, b: Rect) -> bool:\n        return rect_overlap(a, b)\n''',
}


def transform(source: str) -> str:
    tree = ast.parse(source)
    main_class = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "MainWindow"), None)
    rect_class = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Rect"), None)
    if main_class is None:
        raise RuntimeError("MainWindow fehlt.")
    found = {n.name: n for n in main_class.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    missing = sorted(set(METHODS) - set(found))
    if missing:
        raise RuntimeError(f"Methoden fehlen: {', '.join(missing)}")
    lines = source.splitlines(keepends=True)
    edits = []
    if rect_class is not None:
        start = min([rect_class.lineno] + [d.lineno for d in rect_class.decorator_list]) - 1
        edits.append((start, rect_class.end_lineno, ""))
    for name, replacement in METHODS.items():
        node = found[name]
        start = min([node.lineno] + [d.lineno for d in node.decorator_list]) - 1
        edits.append((start, node.end_lineno, replacement + "\n"))
    for start, end, replacement in sorted(edits, reverse=True):
        lines[start:end] = [replacement]
    result = "".join(lines)
    result = result.replace("from dataclasses import dataclass\n", "")
    if IMPORT not in result:
        anchor = "from module_manager import ModuleActionResult, ModuleManager, ModuleManagerError, ModuleState\n"
        if anchor not in result:
            raise RuntimeError("Importanker fehlt.")
        result = result.replace(anchor, anchor + IMPORT)
    ast.parse(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=TARGET)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = args.path.read_text(encoding="utf-8")
    result = transform(source)
    changed = result != source
    if args.check:
        return 1 if changed else 0
    if changed:
        args.path.write_text(result, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
