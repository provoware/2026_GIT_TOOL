#!/usr/bin/env python3
"""Hauptfenster mit 3x3-Modulraster und Modulverwaltung."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from config_models import ConfigModelError, GuiConfigModel, load_gui_config
from logging_center import get_logger, setup_logging
from module_manager import ModuleActionResult, ModuleManager, ModuleManagerError, ModuleState

DEFAULT_GUI_CONFIG = Path(__file__).resolve().parents[1] / "config" / "launcher_gui.json"
DEFAULT_MODULE_CONFIG = Path(__file__).resolve().parents[1] / "config" / "modules.json"


class MainWindowError(ValueError):
    """Fehler im Hauptfenster."""


@dataclass
class Rect:
    x: int
    y: int
    width: int
    height: int


class ModuleWidget:
    def __init__(
        self,
        parent,
        state: ModuleState,
        theme: Dict[str, str],
        on_activate,
        on_deactivate,
        on_drag,
        on_resize,
        on_status,
    ) -> None:
        import tkinter as tk

        self.state = state
        self._on_activate = on_activate
        self._on_deactivate = on_deactivate
        self._on_drag = on_drag
        self._on_resize = on_resize
        self._on_status = on_status
        self._drag_start: Optional[tuple[int, int]] = None
        self._resize_start: Optional[tuple[int, int, int, int]] = None
        self.rect = Rect(0, 0, 100, 100)
        self.last_valid_rect = Rect(0, 0, 100, 100)
        self.min_width = 180
        self.min_height = 120

        self.frame = tk.Frame(parent, highlightthickness=2)
        self.header = tk.Frame(self.frame)
        self.title_label = tk.Label(
            self.header,
            text=state.entry.name,
            anchor="w",
        )
        self.drag_label = tk.Label(self.header, text="⇕", anchor="e")
        self.header.pack(fill="x")
        self.title_label.pack(side="left", padx=6, pady=4, fill="x", expand=True)
        self.drag_label.pack(side="right", padx=6)

        self.description = tk.Label(
            self.frame,
            text=state.entry.description,
            justify="left",
            anchor="w",
            wraplength=260,
        )
        self.description.pack(fill="x", padx=8)

        self.status_label = tk.Label(self.frame, text="Status: inaktiv", anchor="w")
        self.status_label.pack(fill="x", padx=8, pady=(4, 0))

        button_row = tk.Frame(self.frame)
        button_row.pack(fill="x", padx=8, pady=6)
        self.activate_button = tk.Button(
            button_row,
            text="Aktivieren",
            command=self._handle_activate,
        )
        self.deactivate_button = tk.Button(
            button_row, text="Deaktivieren", command=self._handle_deactivate
        )
        self.activate_button.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self.deactivate_button.pack(side="left", expand=True, fill="x", padx=(4, 0))

        self.resize_handle = tk.Label(self.frame, text="↘", anchor="e")
        self.resize_handle.pack(fill="x", padx=6, pady=(0, 4))

        self._apply_theme(theme)
        self._bind_drag(tk)
        self._bind_resize(tk)

    def _apply_theme(self, theme: Dict[str, str]) -> None:
        self.frame.configure(background=theme["background"], highlightbackground=theme["accent"])
        self.header.configure(background=theme["background"])
        self.title_label.configure(background=theme["background"], foreground=theme["foreground"])
        self.drag_label.configure(background=theme["background"], foreground=theme["accent"])
        self.description.configure(background=theme["background"], foreground=theme["foreground"])
        self.status_label.configure(background=theme["background"], foreground=theme["foreground"])
        self.activate_button.configure(
            background=theme["button_background"], foreground=theme["button_foreground"]
        )
        self.deactivate_button.configure(
            background=theme["button_background"], foreground=theme["button_foreground"]
        )
        self.resize_handle.configure(background=theme["background"], foreground=theme["accent"])

    def update_status(self, text: str, color: str) -> None:
        self.status_label.configure(text=text, foreground=color)

    def _bind_drag(self, tk) -> None:
        for widget in (self.header, self.title_label, self.drag_label):
            widget.bind("<ButtonPress-1>", self._start_drag, add="+")
            widget.bind("<B1-Motion>", self._drag, add="+")
            widget.bind("<ButtonRelease-1>", self._end_drag, add="+")
        self.frame.bind("<ButtonPress-1>", self._start_drag, add="+")
        self.frame.bind("<B1-Motion>", self._drag, add="+")
        self.frame.bind("<ButtonRelease-1>", self._end_drag, add="+")

    def _bind_resize(self, tk) -> None:
        self.resize_handle.bind("<ButtonPress-1>", self._start_resize, add="+")
        self.resize_handle.bind("<B1-Motion>", self._resize, add="+")
        self.resize_handle.bind("<ButtonRelease-1>", self._end_resize, add="+")

    def _start_drag(self, event) -> None:
        self._drag_start = (event.x_root, event.y_root)
        self.last_valid_rect = Rect(self.rect.x, self.rect.y, self.rect.width, self.rect.height)

    def _drag(self, event) -> None:
        if self._drag_start is None:
            return
        start_x, start_y = self._drag_start
        delta_x = event.x_root - start_x
        delta_y = event.y_root - start_y
        self._on_drag(self, delta_x, delta_y)

    def _end_drag(self, _event) -> None:
        self._drag_start = None

    def _start_resize(self, event) -> None:
        self._resize_start = (event.x_root, event.y_root, self.rect.width, self.rect.height)
        self.last_valid_rect = Rect(self.rect.x, self.rect.y, self.rect.width, self.rect.height)

    def _resize(self, event) -> None:
        if self._resize_start is None:
            return
        start_x, start_y, start_width, start_height = self._resize_start
        delta_x = event.x_root - start_x
        delta_y = event.y_root - start_y
        self._on_resize(self, start_width + delta_x, start_height + delta_y)

    def _end_resize(self, _event) -> None:
        self._resize_start = None

    def _handle_activate(self) -> None:
        self._on_activate(self)

    def _handle_deactivate(self) -> None:
        self._on_deactivate(self)


class MainWindow:
    def __init__(
        self,
        root,
        module_config: Path,
        gui_config: GuiConfigModel,
        debug: bool,
        theme_name: Optional[str] = None,
    ) -> None:
        self.root = root
        self.module_config = module_config
        self.gui_config = gui_config
        self.debug = debug
        self.logger = get_logger("main_window")
        self.theme_name = theme_name or gui_config.default_theme
        self.manager = ModuleManager(module_config, debug=debug)
        self.module_widgets: list[ModuleWidget] = []
        self.workspace = None
        self.status_label = None
        self.theme_var = None
        self._layout_ready = False
        self._build_ui()

    def _build_ui(self) -> None:
        import tkinter as tk

        self.root.title("Genrearchiv – Hauptfenster")
        self.root.geometry("1200x820")
        self.root.minsize(960, 680)
        self.root.configure(background=self._theme_colors()["background"])

        header = tk.Label(
            self.root,
            text="Hauptfenster: Module verschieben, skalieren und aktivieren",
            anchor="w",
        )
        header.pack(fill="x", padx=16, pady=(16, 4))

        controls = tk.Frame(self.root)
        controls.pack(fill="x", padx=16, pady=(0, 8))
        tk.Label(controls, text="Farbschema:").pack(side="left")
        self.theme_var = tk.StringVar(value=self.theme_name)
        menu = tk.OptionMenu(
            controls,
            self.theme_var,
            *self.gui_config.themes.keys(),
            command=lambda _value: self._apply_theme(),
        )
        menu.pack(side="left", padx=(8, 16))

        note = tk.Label(
            controls,
            text=(
                "Tipp: Ziehen per Maus. Größe ändern über ↘ unten rechts. "
                "Kollisionen werden blockiert (keine Überlappung)."
            ),
            anchor="w",
        )
        note.pack(side="left", fill="x", expand=True)

        self.workspace = tk.Frame(self.root)
        self.workspace.pack(fill="both", expand=True, padx=16, pady=8)
        self.workspace.bind("<Configure>", lambda _event: self._layout_modules())

        self.status_label = tk.Label(self.root, text="Bereit.", anchor="w")
        self.status_label.pack(fill="x", padx=16, pady=(0, 12))

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._apply_theme()
        self._create_module_widgets(tk)

    def _create_module_widgets(self, tk) -> None:
        states = self.manager.list_states(include_disabled=False)
        visible_states = states[:9]
        if len(states) > 9:
            self._set_status(
                "Hinweis: Es werden die ersten 9 Module angezeigt.",
                self._theme_colors()["status_busy"],
            )
        theme = self._theme_colors()
        for state in visible_states:
            widget = ModuleWidget(
                self.workspace,
                state,
                theme,
                on_activate=self._activate_widget,
                on_deactivate=self._deactivate_widget,
                on_drag=self._drag_widget,
                on_resize=self._resize_widget,
                on_status=self._set_status,
            )
            self.module_widgets.append(widget)

    def _layout_modules(self) -> None:
        if self.workspace is None:
            return
        width = self.workspace.winfo_width()
        height = self.workspace.winfo_height()
        if width < 10 or height < 10:
            return
        if self._layout_ready:
            self._ensure_within_bounds(width, height)
            return
        gap = 12
        rows, cols = 3, 3
        cell_width = max(200, (width - gap * (cols + 1)) // cols)
        cell_height = max(160, (height - gap * (rows + 1)) // rows)
        for index, widget in enumerate(self.module_widgets):
            row = index // cols
            col = index % cols
            x = gap + col * (cell_width + gap)
            y = gap + row * (cell_height + gap)
            widget.rect = Rect(x, y, cell_width, cell_height)
            widget.last_valid_rect = Rect(x, y, cell_width, cell_height)
            widget.frame.place(x=x, y=y, width=cell_width, height=cell_height)
        self._layout_ready = True

    def _ensure_within_bounds(self, width: int, height: int) -> None:
        for widget in self.module_widgets:
            rect = widget.rect
            new_x = min(max(rect.x, 0), max(0, width - rect.width))
            new_y = min(max(rect.y, 0), max(0, height - rect.height))
            if new_x != rect.x or new_y != rect.y:
                rect.x = new_x
                rect.y = new_y
                widget.frame.place(x=rect.x, y=rect.y, width=rect.width, height=rect.height)

    def _drag_widget(self, widget: ModuleWidget, delta_x: int, delta_y: int) -> None:
        rect = widget.rect
        new_x = rect.x + delta_x
        new_y = rect.y + delta_y
        width = self.workspace.winfo_width()
        height = self.workspace.winfo_height()
        new_x = min(max(new_x, 0), max(0, width - rect.width))
        new_y = min(max(new_y, 0), max(0, height - rect.height))
        candidate = Rect(new_x, new_y, rect.width, rect.height)
        if self._is_collision(candidate, widget):
            widget.frame.place(
                x=widget.last_valid_rect.x,
                y=widget.last_valid_rect.y,
                width=widget.last_valid_rect.width,
                height=widget.last_valid_rect.height,
            )
            self._set_status(
                "Position blockiert: Module dürfen sich nicht überlappen.",
                self._theme_colors()["status_error"],
            )
            return
        widget.rect = candidate
        widget.last_valid_rect = Rect(candidate.x, candidate.y, candidate.width, candidate.height)
        widget.frame.place(
            x=candidate.x,
            y=candidate.y,
            width=candidate.width,
            height=candidate.height,
        )

    def _resize_widget(self, widget: ModuleWidget, width: int, height: int) -> None:
        width = max(widget.min_width, width)
        height = max(widget.min_height, height)
        workspace_width = self.workspace.winfo_width()
        workspace_height = self.workspace.winfo_height()
        width = min(width, workspace_width - widget.rect.x)
        height = min(height, workspace_height - widget.rect.y)
        candidate = Rect(widget.rect.x, widget.rect.y, width, height)
        if self._is_collision(candidate, widget):
            widget.frame.place(
                x=widget.last_valid_rect.x,
                y=widget.last_valid_rect.y,
                width=widget.last_valid_rect.width,
                height=widget.last_valid_rect.height,
            )
            self._set_status(
                "Größe blockiert: Module dürfen sich nicht überlappen.",
                self._theme_colors()["status_error"],
            )
            return
        widget.rect = candidate
        widget.last_valid_rect = Rect(candidate.x, candidate.y, candidate.width, candidate.height)
        widget.frame.place(
            x=candidate.x,
            y=candidate.y,
            width=candidate.width,
            height=candidate.height,
        )

    def _is_collision(self, candidate: Rect, current: ModuleWidget) -> bool:
        for widget in self.module_widgets:
            if widget is current:
                continue
            rect = widget.rect
            if self._rect_overlap(candidate, rect):
                return True
        return False

    @staticmethod
    def _rect_overlap(a: Rect, b: Rect) -> bool:
        return (
            a.x < b.x + b.width
            and a.x + a.width > b.x
            and a.y < b.y + b.height
            and a.y + a.height > b.y
        )

    def _activate_widget(self, widget: ModuleWidget) -> None:
        result = self.manager.activate_module(widget.state.entry.module_id)
        self._apply_action_result(widget, result, active=True)

    def _deactivate_widget(self, widget: ModuleWidget) -> None:
        result = self.manager.deactivate_module(widget.state.entry.module_id)
        active = self.manager.get_state(widget.state.entry.module_id).active
        self._apply_action_result(widget, result, active=active)

    def _apply_action_result(
        self, widget: ModuleWidget, result: ModuleActionResult, active: bool
    ) -> None:
        theme = self._theme_colors()
        color = theme["status_success"] if result.status == "ok" else theme["status_error"]
        status_text = "Status: aktiv" if active else "Status: inaktiv"
        widget.update_status(status_text, color)
        self._set_status(result.message, color)

    def _set_status(self, message: str, color: str) -> None:
        if self.status_label is None:
            return
        self.status_label.configure(text=message, foreground=color)

    def _on_close(self) -> None:
        self.manager.deactivate_all()
        self.root.destroy()

    def _theme_colors(self) -> Dict[str, str]:
        theme_key = self.theme_var.get() if self.theme_var is not None else self.theme_name
        theme = self.gui_config.themes.get(theme_key, None)
        if theme is None:
            theme = self.gui_config.themes[self.gui_config.default_theme]
        return theme.colors

    def _apply_theme(self) -> None:
        theme = self._theme_colors()
        self.root.configure(background=theme["background"])
        for widget in self.root.winfo_children():
            if hasattr(widget, "configure"):
                widget.configure(background=theme["background"])
                if widget.winfo_class() == "Label":
                    widget.configure(foreground=theme["foreground"])
        for module_widget in self.module_widgets:
            module_widget._apply_theme(theme)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Hauptfenster mit Modulraster und Modulverwaltung.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_MODULE_CONFIG,
        help="Pfad zur Modul-Liste (JSON).",
    )
    parser.add_argument(
        "--gui-config",
        type=Path,
        default=DEFAULT_GUI_CONFIG,
        help="Pfad zur GUI-Konfiguration (JSON).",
    )
    parser.add_argument(
        "--theme",
        type=str,
        default="",
        help="Optionales Farbschema (Theme-Name).",
    )
    parser.add_argument("--debug", action="store_true", help="Debug-Modus aktivieren.")
    return parser


def load_gui_config_safe(path: Path) -> GuiConfigModel:
    try:
        return load_gui_config(path)
    except ConfigModelError as exc:
        raise MainWindowError(str(exc)) from exc


def run_main_window(
    module_config: Path,
    gui_config: GuiConfigModel,
    debug: bool,
    theme_name: Optional[str] = None,
) -> int:
    import tkinter as tk

    root = tk.Tk()
    MainWindow(
        root,
        module_config=module_config,
        gui_config=gui_config,
        debug=debug,
        theme_name=theme_name,
    )
    root.mainloop()
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.debug)
    try:
        gui_config = load_gui_config_safe(args.gui_config)
        theme_name = (
            args.theme.strip() if isinstance(args.theme, str) and args.theme.strip() else None
        )
        run_main_window(args.config, gui_config, debug=args.debug, theme_name=theme_name)
    except (MainWindowError, ModuleManagerError) as exc:
        logger = get_logger("main_window")
        logger.error("Hauptfenster konnte nicht gestartet werden: %s", exc)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
