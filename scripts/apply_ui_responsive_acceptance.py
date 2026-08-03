#!/usr/bin/env python3
"""Integriert die durch die UI-Abnahme bestätigten Responsive-Korrekturen."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LAUNCHER = ROOT / "system" / "launcher_gui.py"
DEFAULT_MAIN = ROOT / "system" / "main_window.py"

LAUNCHER_IMPORT = '''from ui_responsive import resolve_launcher_layout
'''
MAIN_IMPORT = '''from ui_responsive import (
    MAIN_WINDOW_MIN_HEIGHT,
    MAIN_WINDOW_MIN_WIDTH,
    UiResponsiveError,
    resolve_workspace_grid,
)
'''

LAUNCHER_METHODS = {
    "_update_wrap_length": '''    def _update_wrap_length(self) -> None:
        width = max(self.root.winfo_width(), 1)
        layout = resolve_launcher_layout(width)
        full_width = max(width - 64, 280)
        help_width = max((width - 96) // 2, 280) if layout.help_columns == 2 else full_width
        if self.footer_label is not None:
            self.footer_label.configure(wraplength=full_width, justify="left")
        if self.help_label is not None:
            self.help_label.configure(wraplength=help_width, justify="left")
        if self.context_help_label is not None:
            self.context_help_label.configure(wraplength=help_width, justify="left")
        if self.developer_hint is not None:
            self.developer_hint.configure(wraplength=full_width, justify="left")
        if self.drop_zone_label is not None:
            self.drop_zone_label.configure(wraplength=full_width, justify="left")
        if self.status_label is not None:
            self.status_label.configure(wraplength=full_width, justify="left")''',
    "_update_layout_by_width": '''    def _update_layout_by_width(self) -> None:
        width = max(self.root.winfo_width(), 1)
        layout = resolve_launcher_layout(width)
        self._update_wrap_length()

        if (
            self.help_section is not None
            and self.help_label is not None
            and self.context_help_label is not None
        ):
            if layout.help_columns == 2:
                self.help_label.grid_configure(row=0, column=0, columnspan=1, sticky="nw")
                self.context_help_label.grid_configure(
                    row=0, column=1, columnspan=1, sticky="nw"
                )
                drop_row = 1
            else:
                self.help_label.grid_configure(row=0, column=0, columnspan=2, sticky="nw")
                self.context_help_label.grid_configure(
                    row=1, column=0, columnspan=2, sticky="nw"
                )
                drop_row = 2
            if self.drop_zone_label is not None:
                self.drop_zone_label.grid_configure(
                    row=drop_row, column=0, columnspan=2, sticky="ew"
                )

        controls = self.controls_frame
        if controls is not None:
            for column in range(4):
                controls.columnconfigure(column, weight=0)
            if layout.mode == "wide":
                positions = {
                    self.theme_label: (0, 0, 1, "w"),
                    self.theme_menu: (0, 1, 1, "w"),
                    self.show_all_check: (0, 2, 1, "w"),
                    self.debug_check: (1, 0, 1, "w"),
                    self.diagnostics_button: (1, 1, 1, "ew"),
                    self.refresh_button: (1, 2, 1, "ew"),
                    self.autostart_check: (2, 0, 1, "w"),
                    self.main_window_button: (2, 1, 1, "ew"),
                    self.logout_button: (2, 2, 1, "ew"),
                }
                for column in range(3):
                    controls.columnconfigure(column, weight=1 if column else 0)
            elif layout.mode == "medium":
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
                controls.columnconfigure(0, weight=1)
                controls.columnconfigure(1, weight=1)
            else:
                positions = {
                    self.theme_label: (0, 0, 1, "w"),
                    self.theme_menu: (0, 1, 1, "w"),
                    self.show_all_check: (1, 0, 2, "w"),
                    self.debug_check: (2, 0, 2, "w"),
                    self.autostart_check: (3, 0, 2, "w"),
                    self.diagnostics_button: (4, 0, 2, "ew"),
                    self.refresh_button: (5, 0, 2, "ew"),
                    self.main_window_button: (6, 0, 2, "ew"),
                    self.logout_button: (7, 0, 2, "ew"),
                }
                controls.columnconfigure(0, weight=1)
                controls.columnconfigure(1, weight=1)
            for widget, (row, column, columnspan, sticky) in positions.items():
                if widget is not None:
                    widget.grid_configure(
                        row=row,
                        column=column,
                        columnspan=columnspan,
                        sticky=sticky,
                        padx=self.layout.gap_xs,
                        pady=self.layout.gap_xs,
                    )

        developer = self.developer_frame
        if developer is not None:
            for column in range(4):
                developer.columnconfigure(column, weight=0)
            buttons = (
                self.scan_button,
                self.standards_button,
                self.logs_button,
                self.export_button,
                self.export_center_button,
                self.backup_button,
            )
            if layout.developer_columns == 4:
                positions = ((1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1))
                hint_span = 4
            else:
                positions = ((1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1))
                hint_span = 2
            if self.developer_hint is not None:
                self.developer_hint.grid_configure(
                    row=0, column=0, columnspan=hint_span, sticky="w"
                )
            for column in range(hint_span):
                developer.columnconfigure(column, weight=1)
            for widget, (row, column) in zip(buttons, positions):
                if widget is not None:
                    widget.grid_configure(
                        row=row,
                        column=column,
                        columnspan=1,
                        sticky="ew",
                        padx=self.layout.gap_xs,
                        pady=self.layout.gap_xs,
                    )''',
}

MAIN_METHODS = {
    "_layout_modules": '''    def _layout_modules(self) -> None:
        if self.workspace is None:
            return
        width = self.workspace.winfo_width()
        height = self.workspace.winfo_height()
        if width < 10 or height < 10:
            return
        layout_size = (width, height)
        if self._layout_ready and self._layout_size == layout_size:
            return
        try:
            grid = resolve_workspace_grid(
                len(self.module_widgets),
                width,
                height,
                maximum_columns=3,
                gap=12,
                minimum_width=200,
                minimum_height=160,
            )
        except UiResponsiveError as exc:
            self._set_status(str(exc), self._theme_colors()["status_error"])
            return
        rects = build_grid(
            len(self.module_widgets),
            width,
            height,
            rows=grid.rows,
            cols=grid.columns,
            gap=12,
            min_width=200,
            min_height=160,
        )
        for widget, rect in zip(self.module_widgets, rects):
            widget.rect = rect
            widget.last_valid_rect = rect
            widget.description.configure(wraplength=max(rect.width - 16, 120))
            widget.frame.place(
                x=rect.x,
                y=rect.y,
                width=rect.width,
                height=rect.height,
            )
        if self.note_label is not None:
            self.note_label.configure(
                wraplength=max(self.root.winfo_width() - 220, 240),
                justify="left",
            )
        self._layout_ready = True
        self._layout_size = layout_size''',
}


def _replace_methods(source: str, class_name: str, replacements: Mapping[str, str]) -> str:
    tree = ast.parse(source)
    target = next(
        (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name),
        None,
    )
    if target is None:
        raise RuntimeError(f"Klasse {class_name} fehlt.")
    methods = {
        node.name: node
        for node in target.body
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
        anchor = "from ui_theme_adapter import (\n"
        if anchor not in result:
            raise RuntimeError("Launcher-Importanker fehlt.")
        result = result.replace(anchor, LAUNCHER_IMPORT + anchor, 1)
    if "        self.theme_label = None\n" not in result:
        anchor = "        self.theme_menu = None\n"
        if anchor not in result:
            raise RuntimeError("Theme-Label-Zustandsanker fehlt.")
        result = result.replace(anchor, anchor + "        self.theme_label = None\n", 1)
    legacy_theme = '''        tk.Label(controls, text=f"{ICON_SET['theme']} Farbschema:").grid(
            row=0, column=0, sticky="w"
        )
'''
    responsive_theme = '''        self.theme_label = tk.Label(
            controls, text=f"{ICON_SET['theme']} Farbschema:"
        )
        self.theme_label.grid(row=0, column=0, sticky="w")
'''
    if legacy_theme in result:
        result = result.replace(legacy_theme, responsive_theme, 1)
    elif responsive_theme not in result:
        raise RuntimeError("Theme-Label konnte nicht integriert werden.")
    ast.parse(result)
    return result


def transform_main(source: str) -> str:
    result = _replace_methods(source, "MainWindow", MAIN_METHODS)
    if MAIN_IMPORT not in result:
        anchor = "from workspace_geometry import "
        index = result.find(anchor)
        if index < 0:
            raise RuntimeError("Hauptfenster-Importanker fehlt.")
        result = result[:index] + MAIN_IMPORT + result[index:]
    if "        self.note_label = None\n" not in result:
        anchor = "        self.theme_var = None\n"
        if anchor not in result:
            raise RuntimeError("Hinweislabel-Zustandsanker fehlt.")
        result = result.replace(anchor, anchor + "        self.note_label = None\n", 1)
    if "        self._layout_size: tuple[int, int] | None = None\n" not in result:
        anchor = "        self._layout_ready = False\n"
        if anchor not in result:
            raise RuntimeError("Layoutgrößenanker fehlt.")
        result = result.replace(
            anchor,
            anchor + "        self._layout_size: tuple[int, int] | None = None\n",
            1,
        )
    result = result.replace(
        "        self.root.minsize(960, 680)\n",
        "        self.root.minsize(MAIN_WINDOW_MIN_WIDTH, MAIN_WINDOW_MIN_HEIGHT)\n",
        1,
    )
    legacy_note = "        note = tk.Label(\n"
    if legacy_note in result:
        result = result.replace(legacy_note, "        self.note_label = tk.Label(\n", 1)
        result = result.replace(
            "        note.pack(side=\"left\", fill=\"x\", expand=True)\n",
            "        self.note_label.pack(side=\"left\", fill=\"x\", expand=True)\n",
            1,
        )
    if "self.note_label = tk.Label(" not in result:
        raise RuntimeError("Hinweislabel konnte nicht integriert werden.")
    option_anchor = "        menu.pack(side=\"left\", padx=(8, 16))\n"
    option_config = (
        "        menu.configure(padx=6, pady=8, takefocus=1)\n"
        "        menu.pack(side=\"left\", padx=(8, 16))\n"
    )
    if option_config not in result:
        if option_anchor not in result:
            raise RuntimeError("Theme-Menü-Anker fehlt.")
        result = result.replace(option_anchor, option_config, 1)
    button_anchor = '''        self.activate_button.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self.deactivate_button.pack(side="left", expand=True, fill="x", padx=(4, 0))
'''
    button_config = '''        for button in (self.activate_button, self.deactivate_button):
            button.configure(pady=7, takefocus=1)
        self.activate_button.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self.deactivate_button.pack(side="left", expand=True, fill="x", padx=(4, 0))
'''
    if button_config not in result:
        if button_anchor not in result:
            raise RuntimeError("Modulkarten-Buttonanker fehlt.")
        result = result.replace(button_anchor, button_config, 1)
    ast.parse(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--launcher", type=Path, default=DEFAULT_LAUNCHER)
    parser.add_argument("--main-window", type=Path, default=DEFAULT_MAIN)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    launcher_source = args.launcher.read_text(encoding="utf-8")
    main_source = args.main_window.read_text(encoding="utf-8")
    launcher_result = transform_launcher(launcher_source)
    main_result = transform_main(main_source)
    changed = launcher_result != launcher_source or main_result != main_source
    if args.check:
        return 1 if changed else 0
    if launcher_result != launcher_source:
        args.launcher.write_text(launcher_result, encoding="utf-8")
    if main_result != main_source:
        args.main_window.write_text(main_result, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
