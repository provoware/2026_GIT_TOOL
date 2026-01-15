#!/usr/bin/env python3
"""GUI-Launcher: zeigt Module in einer barrierefreien Startübersicht an."""

from __future__ import annotations

import argparse
import subprocess
import threading
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import diagnostics_runner
import error_simulation
import module_checker
import module_selftests
import qa_checks
from config_models import ConfigModelError, GuiConfigModel
from config_models import load_gui_config as load_gui_config_model
from launcher import LauncherError, filter_modules, load_modules
from logging_center import get_logger
from logging_center import setup_logging as setup_logging_center

DEFAULT_MODULE_CONFIG = Path(__file__).resolve().parents[1] / "config" / "modules.json"
DEFAULT_GUI_CONFIG = Path(__file__).resolve().parents[1] / "config" / "launcher_gui.json"
BRAND_NAME = "Genrearchiv"
ICON_SET = {
    "header": "🧭",
    "theme": "🎨",
    "refresh": "🔄",
    "diagnostics": "🧪",
    "developer": "🛠️",
    "scan": "🩺",
    "standards": "📏",
    "logs": "📂",
}


class GuiLauncherError(Exception):
    """Allgemeiner Fehler für den GUI-Launcher."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GuiLauncherError(f"{label} fehlt oder ist leer.")
    return value.strip()


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise GuiLauncherError(f"{label} ist kein boolescher Wert.")
    return value


def _require_list_of_strings(value: object, label: str) -> List[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise GuiLauncherError(f"{label} ist keine Liste von Texten.")
    return value


def load_gui_config(config_path: Path) -> GuiConfigModel:
    try:
        return load_gui_config_model(config_path)
    except ConfigModelError as exc:
        raise GuiLauncherError(str(exc)) from exc


def build_module_lines(
    modules: Iterable[object],
    root: Path,
    debug: bool,
) -> List[str]:
    if not isinstance(root, Path):
        raise GuiLauncherError("root ist kein Pfad (Path).")

    lines: List[str] = []
    for index, module in enumerate(modules, start=1):
        if not hasattr(module, "name") or not hasattr(module, "module_id"):
            raise GuiLauncherError("Modul-Eintrag ist ungültig.")
        status = "aktiv" if getattr(module, "enabled", False) else "deaktiviert"
        lines.append(f"{index}. {module.name} ({module.module_id}) – {status}")
        lines.append(f"   Beschreibung: {module.description}")
        if debug:
            lines.append(f"   Pfad: {module.path}")
        lines.append("")

    if not lines:
        return ["Keine Module gefunden."]
    return _require_list_of_strings(lines, "module_lines")


def render_module_text(modules: Iterable[object], root: Path, debug: bool) -> str:
    lines = build_module_lines(modules, root, debug)
    output = "\n".join(lines).rstrip() + "\n"
    if not output.strip():
        raise GuiLauncherError("GUI-Ausgabe ist leer.")
    return output


def setup_logging(debug: bool) -> None:
    setup_logging_center(debug)


def run_module_check(config_path: Path) -> List[str]:
    if not isinstance(config_path, Path):
        raise GuiLauncherError("config_path ist kein Pfad (Path).")
    try:
        entries = module_checker.load_modules(config_path)
    except module_checker.ModuleCheckError as exc:
        raise GuiLauncherError(f"Modul-Check konnte nicht starten: {exc}") from exc
    issues = module_checker.check_modules(entries)
    return _require_list_of_strings(issues, "module_check")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="GUI-Launcher: Startübersicht für Module.",
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
        "--show-all",
        action="store_true",
        help="Zeigt auch deaktivierte Module an.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug-Modus aktivieren.",
    )
    if not isinstance(parser, argparse.ArgumentParser):
        raise GuiLauncherError("Parser ist ungültig.")
    return parser


class LauncherGui:
    def __init__(
        self,
        root,
        module_config: Path,
        gui_config: GuiConfigModel,
        show_all: bool,
        debug: bool,
    ) -> None:
        self.root = root
        self.module_config = module_config
        self.gui_config = gui_config
        self.debug = debug

        self.theme_var = None
        self.show_all_var = None
        self.debug_var = None
        self.output_text = None
        self.theme_menu = None
        self.show_all_check = None
        self.debug_check = None
        self.refresh_button = None
        self.diagnostics_button = None
        self.scan_button = None
        self.standards_button = None
        self.logs_button = None
        self.diagnostics_running = False
        self.maintenance_running = False
        self.refresh_job = None
        self.refresh_debounce_ms = gui_config.refresh_debounce_ms
        self.logger = get_logger("launcher_gui")
        self.status_var = None
        self.status_label = None
        self.status_indicator = None
        self.footer_label = None
        self.help_label = None
        self.developer_hint = None
        self.header_font = None
        self.output_font = None
        self.button_font = None
        self.base_font_sizes: Dict[str, int] = {}
        self.base_header_size = 18
        self.base_output_size = 14
        self.base_button_size = 14
        self.zoom_level = 1.0
        self.last_non_contrast_theme = self.gui_config.default_theme
        self.contrast_theme = self._resolve_contrast_theme()
        self.status_palette: Dict[str, str] = {}
        self.layout = self.gui_config.layout

        self.root.title(f"{BRAND_NAME} – Startübersicht")
        self.root.minsize(640, 420)
        self._build_ui(show_all)

    def _build_ui(self, show_all: bool) -> None:
        import tkinter as tk
        import tkinter.font as tkfont

        _require_bool(show_all, "show_all")
        self._init_fonts(tkfont)

        header = tk.Label(
            self.root,
            text=f"{ICON_SET['header']} {BRAND_NAME} – Startübersicht",
            font=self.header_font,
            anchor="w",
        )
        header.pack(
            fill="x",
            padx=self.layout.gap_lg,
            pady=(self.layout.gap_lg, self.layout.gap_sm),
        )

        controls_section = tk.LabelFrame(self.root, text="Einstellungen und Filter")
        controls_section.pack(fill="x", padx=self.layout.gap_lg, pady=(0, self.layout.gap_md))
        controls = tk.Frame(controls_section)
        controls.pack(fill="x", padx=self.layout.gap_md, pady=self.layout.gap_sm)

        tk.Label(controls, text=f"{ICON_SET['theme']} Farbschema:").grid(
            row=0, column=0, sticky="w"
        )
        self.theme_var = tk.StringVar(value=self.gui_config.default_theme)
        self.theme_menu = tk.OptionMenu(
            controls,
            self.theme_var,
            *self.gui_config.themes.keys(),
            command=lambda _value: self.apply_theme(self.theme_var.get()),
        )
        if self.button_font is not None:
            self.theme_menu.configure(font=self.button_font)
        self.theme_menu.configure(padx=self.layout.field_padx, pady=self.layout.field_pady)
        self.theme_menu.configure(takefocus=1)
        self.theme_menu.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(self.layout.gap_sm, self.layout.gap_xl),
        )

        self.show_all_var = tk.BooleanVar(value=show_all)
        self.show_all_check = tk.Checkbutton(
            controls,
            text="Alle Module anzeigen (inkl. deaktiviert)",
            variable=self.show_all_var,
            command=self.refresh,
        )
        if self.button_font is not None:
            self.show_all_check.configure(font=self.button_font)
        self.show_all_check.configure(padx=self.layout.field_padx, pady=self.layout.field_pady)
        self.show_all_check.configure(takefocus=1, underline=0)
        self.show_all_check.grid(
            row=0,
            column=2,
            sticky="w",
            padx=(self.layout.gap_sm, 0),
            pady=self.layout.gap_xs,
        )

        self.debug_var = tk.BooleanVar(value=self.debug)
        self.debug_check = tk.Checkbutton(
            controls,
            text="Debug-Details anzeigen",
            variable=self.debug_var,
            command=self.refresh,
        )
        if self.button_font is not None:
            self.debug_check.configure(font=self.button_font)
        self.debug_check.configure(padx=self.layout.field_padx, pady=self.layout.field_pady)
        self.debug_check.configure(takefocus=1, underline=0)
        self.debug_check.grid(
            row=1,
            column=0,
            sticky="w",
            pady=(self.layout.gap_sm, 0),
            padx=(0, self.layout.gap_md),
        )

        self.refresh_button = tk.Button(
            controls,
            text=f"{ICON_SET['refresh']} Übersicht aktualisieren",
            command=self.request_refresh,
        )
        if self.button_font is not None:
            self.refresh_button.configure(font=self.button_font)
        self.refresh_button.configure(padx=self.layout.button_padx, pady=self.layout.button_pady)
        self.refresh_button.configure(takefocus=1, underline=0)
        self.refresh_button.grid(
            row=1,
            column=2,
            sticky="e",
            padx=(0, 0),
            pady=(self.layout.gap_sm, 0),
        )

        self.diagnostics_button = tk.Button(
            controls,
            text=f"{ICON_SET['diagnostics']} Diagnose starten",
            command=self.start_diagnostics,
        )
        if self.button_font is not None:
            self.diagnostics_button.configure(font=self.button_font)
        self.diagnostics_button.configure(
            padx=self.layout.button_padx, pady=self.layout.button_pady
        )
        self.diagnostics_button.configure(takefocus=1, underline=0)
        self.diagnostics_button.grid(
            row=1,
            column=1,
            sticky="w",
            padx=(self.layout.gap_sm, self.layout.gap_md),
            pady=(self.layout.gap_sm, 0),
        )

        controls.columnconfigure(2, weight=1)

        help_section = tk.LabelFrame(self.root, text="Hilfe (Kurzinfo)")
        help_section.pack(fill="x", padx=self.layout.gap_lg, pady=(0, self.layout.gap_md))
        self.help_label = tk.Label(
            help_section,
            text=(
                "So geht's: Farbschema wählen, Module einblenden und mit "
                "„Übersicht aktualisieren“ prüfen. "
                "Diagnose: „Diagnose starten“ führt Tests und Codeprüfungen aus. "
                "Entwicklerbereich: System-Scan (Prüfung), Standards (Regeln) und "
                "Log-Ordner (Protokolle). "
                "Kontrastmodus: Alt+K. Zoom: Strg + Mausrad. "
                "Tastatur: Tab für Fokus, Alt+A (alle Module), Alt+D (Debug), "
                "Alt+R (aktualisieren), Alt+G (Diagnose), Alt+S (System-Scan), "
                "Alt+P (Standards), Alt+L (Logs), Alt+T (Theme), Alt+Q (beenden)."
            ),
            anchor="w",
            justify="left",
        )
        self.help_label.pack(fill="x", padx=self.layout.gap_md, pady=self.layout.gap_sm)

        developer_section = tk.LabelFrame(
            self.root, text=f"{ICON_SET['developer']} Entwicklerbereich (für Profis)"
        )
        developer_section.pack(fill="x", padx=self.layout.gap_lg, pady=(0, self.layout.gap_md))
        developer_frame = tk.Frame(developer_section)
        developer_frame.pack(fill="x", padx=self.layout.gap_md, pady=self.layout.gap_sm)

        self.developer_hint = tk.Label(
            developer_frame,
            text=(
                "Hier findest du technische Hilfen: System-Scan (Prüfung), "
                "Standards-Liste (Regeln) und Log-Ordner (Protokolle)."
            ),
            anchor="w",
            justify="left",
        )
        self.developer_hint.grid(row=0, column=0, columnspan=3, sticky="w")

        self.scan_button = tk.Button(
            developer_frame,
            text=f"{ICON_SET['scan']} System-Scan starten",
            command=self.start_system_scan,
        )
        if self.button_font is not None:
            self.scan_button.configure(font=self.button_font)
        self.scan_button.configure(padx=self.layout.button_padx, pady=self.layout.button_pady)
        self.scan_button.configure(takefocus=1, underline=0)
        self.scan_button.grid(row=1, column=0, sticky="w", padx=(0, self.layout.gap_md))

        self.standards_button = tk.Button(
            developer_frame,
            text=f"{ICON_SET['standards']} Standards anzeigen",
            command=self.show_standards,
        )
        if self.button_font is not None:
            self.standards_button.configure(font=self.button_font)
        self.standards_button.configure(padx=self.layout.button_padx, pady=self.layout.button_pady)
        self.standards_button.configure(takefocus=1, underline=0)
        self.standards_button.grid(row=1, column=1, sticky="w", padx=(0, self.layout.gap_md))

        self.logs_button = tk.Button(
            developer_frame,
            text=f"{ICON_SET['logs']} Log-Ordner öffnen",
            command=self.open_logs,
        )
        if self.button_font is not None:
            self.logs_button.configure(font=self.button_font)
        self.logs_button.configure(padx=self.layout.button_padx, pady=self.layout.button_pady)
        self.logs_button.configure(takefocus=1, underline=0)
        self.logs_button.grid(row=1, column=2, sticky="w")

        developer_frame.columnconfigure(2, weight=1)

        self.status_var = tk.StringVar(value="Status: Bereit.")
        status_section = tk.LabelFrame(self.root, text="Status")
        status_section.pack(fill="x", padx=self.layout.gap_lg, pady=(0, self.layout.gap_sm))
        self.status_indicator = tk.Label(status_section, text="●", width=2, anchor="w")
        self.status_indicator.pack(side="left", padx=(self.layout.gap_md, 0))
        self.status_label = tk.Label(
            status_section,
            textvariable=self.status_var,
            anchor="w",
        )
        self.status_label.pack(
            fill="x",
            padx=(self.layout.gap_sm, self.layout.gap_md),
            pady=self.layout.field_pady,
        )

        output_section = tk.LabelFrame(self.root, text="Modulübersicht")
        output_section.pack(
            fill="both",
            expand=True,
            padx=self.layout.gap_lg,
            pady=(0, self.layout.gap_lg),
        )
        self.output_text = tk.Text(
            output_section,
            wrap="word",
            height=16,
            font=self.output_font,
            borderwidth=2,
            relief="groove",
            takefocus=1,
        )
        self.output_text.configure(
            spacing1=self.layout.text_spacing.before,
            spacing2=self.layout.text_spacing.line,
            spacing3=self.layout.text_spacing.after,
            highlightthickness=self.layout.focus_thickness,
        )
        self.output_text.pack(
            fill="both", expand=True, padx=self.layout.gap_md, pady=self.layout.gap_md
        )
        self.output_text.configure(state="disabled")

        self.footer_label = tk.Label(
            self.root,
            text=(
                "Tipp: Mit Tabulator erreichst du alle Bedienelemente. "
                "Kurzbefehle: Alt+A (alle Module), Alt+D (Debug), Alt+R "
                "(aktualisieren), Alt+G (Diagnose), Alt+S (System-Scan), "
                "Alt+P (Standards), Alt+L (Logs), Alt+T (Theme), Alt+K (Kontrast), "
                "Strg + Mausrad (Zoom), Alt+Q (beenden)."
            ),
            anchor="w",
        )
        self.footer_label.pack(fill="x", padx=self.layout.gap_lg, pady=(0, self.layout.gap_md))

        self._bind_accessibility_shortcuts()
        self._bind_responsive_layout()
        self._bind_zoom_controls()
        self.apply_theme(self.gui_config.default_theme)
        self.request_refresh()
        self.root.after(100, lambda: self._focus_widget(self.theme_menu))

    def _init_fonts(self, tkfont) -> None:
        if tkfont is None:
            raise GuiLauncherError("tkfont ist nicht verfügbar.")
        named_fonts = ["TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"]
        for name in named_fonts:
            try:
                font_obj = tkfont.nametofont(name)
            except Exception as exc:
                raise GuiLauncherError(f"Standardfont {name} fehlt: {exc}") from exc
            self.base_font_sizes[name] = int(font_obj.cget("size"))
        self.header_font = tkfont.Font(family="Arial", size=self.base_header_size, weight="bold")
        self.output_font = tkfont.Font(family="Arial", size=self.base_output_size)
        self.button_font = tkfont.Font(family="Arial", size=self.base_button_size, weight="bold")
        self._apply_zoom()

    def _bind_accessibility_shortcuts(self) -> None:
        self.root.bind_all("<Alt-a>", lambda _event: self._toggle_show_all())
        self.root.bind_all("<Alt-d>", lambda _event: self._toggle_debug())
        self.root.bind_all("<Alt-r>", lambda _event: self._refresh_from_shortcut())
        self.root.bind_all("<Alt-t>", lambda _event: self._focus_widget(self.theme_menu))
        self.root.bind_all("<Alt-k>", lambda _event: self._toggle_contrast_theme())
        self.root.bind_all("<Alt-g>", lambda _event: self.start_diagnostics())
        self.root.bind_all("<Alt-s>", lambda _event: self.start_system_scan())
        self.root.bind_all("<Alt-p>", lambda _event: self.show_standards())
        self.root.bind_all("<Alt-l>", lambda _event: self.open_logs())
        self.root.bind_all("<Alt-q>", lambda _event: self.root.quit())
        self.root.bind_all("<Control-r>", lambda _event: self._refresh_from_shortcut())

    def _bind_zoom_controls(self) -> None:
        self.root.bind_all("<Control-MouseWheel>", self._on_zoom_mousewheel)
        self.root.bind_all("<Control-Button-4>", lambda _event: self._adjust_zoom(1))
        self.root.bind_all("<Control-Button-5>", lambda _event: self._adjust_zoom(-1))

    def _on_zoom_mousewheel(self, event) -> None:
        if not hasattr(event, "delta"):
            raise GuiLauncherError("Zoom-Event ist ungültig.")
        direction = 1 if event.delta > 0 else -1
        self._adjust_zoom(direction)

    def _adjust_zoom(self, direction: int) -> None:
        if not isinstance(direction, int):
            raise GuiLauncherError("Zoom-Richtung ist ungültig.")
        step = 0.1
        new_level = min(max(self.zoom_level + step * direction, 0.8), 1.6)
        if abs(new_level - self.zoom_level) < 0.001:
            return
        self.zoom_level = new_level
        self._apply_zoom()
        percent = int(round(self.zoom_level * 100))
        self._set_status(f"Zoom: {percent} %", state="success")

    def _apply_zoom(self) -> None:
        if not isinstance(self.zoom_level, (int, float)):
            raise GuiLauncherError("Zoom-Level ist keine Zahl.")
        for name, base_size in self.base_font_sizes.items():
            if not isinstance(base_size, int):
                raise GuiLauncherError("Basis-Fontgröße ist ungültig.")
            base_abs = abs(base_size)
            new_abs = max(9, int(round(base_abs * self.zoom_level)))
            new_size = -new_abs if base_size < 0 else new_abs
            import tkinter.font as tkfont

            tkfont.nametofont(name).configure(size=new_size)
        if self.header_font is not None:
            header_size = max(12, int(round(self.base_header_size * self.zoom_level)))
            self.header_font.configure(size=header_size)
        if self.output_font is not None:
            output_size = max(11, int(round(self.base_output_size * self.zoom_level)))
            self.output_font.configure(size=output_size)
        if self.button_font is not None:
            button_size = max(12, int(round(self.base_button_size * self.zoom_level)))
            self.button_font.configure(size=button_size)

    def _bind_responsive_layout(self) -> None:
        self.root.bind("<Configure>", lambda _event: self._update_wrap_length())
        self._update_wrap_length()

    def _update_wrap_length(self) -> None:
        width = max(self.root.winfo_width() - 32, 280)
        if self.footer_label is not None:
            self.footer_label.configure(wraplength=width, justify="left")
        if self.help_label is not None:
            self.help_label.configure(wraplength=width, justify="left")
        if self.developer_hint is not None:
            self.developer_hint.configure(wraplength=width, justify="left")

    def _focus_widget(self, widget) -> None:
        if widget is not None:
            widget.focus_set()

    def _toggle_show_all(self) -> None:
        self.show_all_var.set(not bool(self.show_all_var.get()))
        self.request_refresh()

    def _toggle_debug(self) -> None:
        self.debug_var.set(not bool(self.debug_var.get()))
        self.request_refresh()

    def _refresh_from_shortcut(self) -> None:
        self.request_refresh()

    def _resolve_contrast_theme(self) -> Optional[str]:
        if not isinstance(self.gui_config, GuiConfigModel):
            raise GuiLauncherError("gui_config ist ungültig.")
        if "kontrast" in self.gui_config.themes:
            return "kontrast"
        for name, theme in self.gui_config.themes.items():
            if "kontrast" in theme.label.lower():
                return name
        return None

    def _toggle_contrast_theme(self) -> None:
        if self.theme_var is None:
            raise GuiLauncherError("Theme-Auswahl ist nicht verfügbar.")
        if self.contrast_theme is None:
            self._set_status("Kein Kontrast-Theme vorhanden.", state="error")
            return
        current = self.theme_var.get()
        if current == self.contrast_theme:
            target = self.last_non_contrast_theme or self.gui_config.default_theme
        else:
            self.last_non_contrast_theme = current
            target = self.contrast_theme
        self._set_theme(target)
        label = self.gui_config.themes[target].label
        self._set_status(f"Farbschema aktiv: {label}", state="success")

    def request_refresh(self) -> None:
        if self.refresh_job is not None:
            self.root.after_cancel(self.refresh_job)
        self._set_status("Aktualisierung wird vorbereitet…", state="busy")
        self.refresh_job = self.root.after(self.refresh_debounce_ms, self.refresh)

    def _set_theme(self, theme_name: str) -> None:
        clean_name = _require_text(theme_name, "theme_name")
        if clean_name not in self.gui_config.themes:
            raise GuiLauncherError("Unbekanntes Farbschema.")
        self.theme_var.set(clean_name)
        self.apply_theme(clean_name)

    def apply_theme(self, theme_name: str) -> None:
        clean_name = _require_text(theme_name, "theme_name")
        if clean_name not in self.gui_config.themes:
            raise GuiLauncherError("Unbekanntes Farbschema.")
        theme = self.gui_config.themes[clean_name]

        bg = theme.colors["background"]
        fg = theme.colors["foreground"]
        accent = theme.colors["accent"]
        button_bg = theme.colors["button_background"]
        button_fg = theme.colors["button_foreground"]
        self.status_palette = {
            "success": theme.colors["status_success"],
            "error": theme.colors["status_error"],
            "busy": theme.colors["status_busy"],
            "foreground": theme.colors["status_foreground"],
        }

        widgets = self.root.winfo_children()
        self.root.configure(background=bg)
        for widget in widgets:
            self._apply_widget_style(widget, bg, fg, accent, button_bg, button_fg)
        self._apply_status_style("success")

    def _apply_widget_style(
        self,
        widget,
        background: str,
        foreground: str,
        accent: str,
        button_bg: str,
        button_fg: str,
    ) -> None:
        import tkinter as tk

        widget_type = widget.winfo_class()
        if widget_type == "Frame":
            widget.configure(bg=background)
        elif widget_type == "Label":
            widget.configure(bg=background, fg=foreground)
        elif widget_type == "Labelframe":
            widget.configure(
                bg=background,
                fg=foreground,
                highlightbackground=accent,
                highlightcolor=accent,
            )
        elif widget_type in {"Checkbutton", "Button", "Menubutton"}:
            widget.configure(
                bg=button_bg,
                fg=button_fg,
                activebackground=accent,
                activeforeground=button_fg,
                highlightbackground=accent,
                highlightcolor=accent,
                highlightthickness=2,
            )
        elif widget_type == "Text":
            widget.configure(bg=background, fg=foreground, insertbackground=foreground)
        elif widget_type == "OptionMenu":
            widget.configure(bg=button_bg, fg=button_fg, activebackground=accent)

        if isinstance(widget, tk.Text):
            widget.configure(highlightbackground=accent, highlightcolor=accent)
        if isinstance(widget, tk.OptionMenu):
            if self.button_font is not None:
                widget.configure(font=self.button_font)
            widget.configure(
                highlightbackground=accent,
                highlightcolor=accent,
                highlightthickness=2,
            )
            menu = widget["menu"]
            menu.configure(
                bg=button_bg,
                fg=button_fg,
                activebackground=accent,
                activeforeground=button_fg,
            )
            if self.button_font is not None:
                menu.configure(font=self.button_font)

        for child in widget.winfo_children():
            self._apply_widget_style(child, background, foreground, accent, button_bg, button_fg)

    def refresh(self) -> None:
        self.refresh_job = None
        show_all = bool(self.show_all_var.get())
        debug = bool(self.debug_var.get())
        try:
            self._set_status("Prüfe Module…", state="busy")
            modules = load_modules(self.module_config)
            modules = filter_modules(modules, show_all)
            root_dir = self.module_config.resolve().parents[1]
            text = render_module_text(modules, root_dir, debug)
            issues = run_module_check(self.module_config)
            text = self._append_module_check(text, issues)
            file_report = qa_checks.check_release_files(root_dir)
            text = self._append_file_status(text, file_report)
            selftests = module_selftests.run_selftests(self.module_config)
            text = self._append_selftests(text, selftests)
            simulations = error_simulation.run_simulations()
            text = self._append_error_simulation(text, simulations)
        except (LauncherError, GuiLauncherError) as exc:
            text = (
                "Fehler beim Aktualisieren.\n"
                f"Ursache: {exc}\n"
                "Lösung: Bitte config/modules.json und die Modulordner prüfen, "
                "danach erneut auf „Übersicht aktualisieren“ klicken.\n"
            )
            self.logger.error("GUI-Launcher Fehler: %s", exc)
            self._show_error(str(exc))
            self._set_status("Fehler aufgetreten. Bitte Hinweise lesen.", state="error")
        else:
            self._set_status("Bereit.", state="success")

        self._set_output(text)

    def start_diagnostics(self) -> None:
        if self.diagnostics_running:
            self._set_status("Diagnose läuft bereits…", state="busy")
            return
        self.diagnostics_running = True
        if self.diagnostics_button is not None:
            self.diagnostics_button.configure(state="disabled")
        self._set_status("Diagnose wird gestartet…", state="busy")
        thread = threading.Thread(target=self._run_diagnostics, daemon=True)
        thread.start()

    def start_system_scan(self) -> None:
        script_path = self.module_config.resolve().parents[1] / "scripts" / "system_scan.sh"
        self._run_maintenance_task("System-Scan", ["bash", str(script_path)])

    def show_standards(self) -> None:
        script_path = self.module_config.resolve().parents[1] / "scripts" / "show_standards.sh"
        self._run_maintenance_task("Standards-Liste", ["bash", str(script_path), "--list"])

    def open_logs(self) -> None:
        logs_path = self.module_config.resolve().parents[1] / "logs"
        self._run_maintenance_task("Log-Ordner öffnen", ["xdg-open", str(logs_path)])

    def _run_maintenance_task(self, title: str, command: List[str]) -> None:
        clean_title = _require_text(title, "maintenance_title")
        if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
            raise GuiLauncherError("Maintenance-Kommando ist ungültig.")
        if self.maintenance_running:
            self._set_status("Wartung läuft bereits…", state="busy")
            return
        if command and command[0] == "bash":
            script_path = Path(command[1])
            if not script_path.exists():
                self._set_status("Script nicht gefunden.", state="error")
                self._append_output(f"{clean_title}:\nFehler: Script {script_path} fehlt.\n")
                return
        if command and command[0] == "xdg-open":
            target_path = Path(command[1])
            if not target_path.exists():
                self._set_status("Pfad nicht gefunden.", state="error")
                self._append_output(f"{clean_title}:\nFehler: Pfad {target_path} fehlt.\n")
                return
        self.maintenance_running = True
        self._set_maintenance_buttons("disabled")
        self._set_status(f"{clean_title} läuft…", state="busy")
        thread = threading.Thread(
            target=self._execute_maintenance, args=(clean_title, command), daemon=True
        )
        thread.start()

    def _execute_maintenance(self, title: str, command: List[str]) -> None:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
            output = result.stdout.strip() or result.stderr.strip()
            if not output:
                output = "Keine Ausgabe erhalten."
            status = "success" if result.returncode == 0 else "error"
            report = self._format_maintenance_report(title, command, output, result.returncode)
        except Exception as exc:
            status = "error"
            report = (
                f"{title}:\n"
                f"Fehler: {exc}\n"
                "Lösung: Bitte das Skript prüfen und erneut versuchen.\n"
            )
        self.root.after(0, lambda: self._finish_maintenance(title, report, status))

    def _finish_maintenance(self, title: str, report: str, status: str) -> None:
        self.maintenance_running = False
        self._set_maintenance_buttons("normal")
        self._append_output(report)
        if status == "success":
            self._set_status(f"{title} abgeschlossen.", state="success")
        else:
            self._set_status(f"{title} mit Problemen.", state="error")

    def _format_maintenance_report(
        self, title: str, command: List[str], output: str, return_code: int
    ) -> str:
        clean_title = _require_text(title, "maintenance_title")
        if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
            raise GuiLauncherError("Maintenance-Kommando ist ungültig.")
        if not isinstance(output, str) or not output.strip():
            raise GuiLauncherError("Maintenance-Ausgabe ist leer.")
        if not isinstance(return_code, int):
            raise GuiLauncherError("Maintenance-Exit-Code ist ungültig.")
        lines = [
            f"{clean_title}:",
            f"Kommando: {' '.join(command)}",
            f"Exit-Code: {return_code}",
            "",
            "Ausgabe:",
            output,
            "",
        ]
        return "\n".join(lines)

    def _set_maintenance_buttons(self, state: str) -> None:
        clean_state = _require_text(state, "maintenance_state")
        for button in (self.scan_button, self.standards_button, self.logs_button):
            if button is not None:
                button.configure(state=clean_state)

    def _run_diagnostics(self) -> None:
        script_path = self.module_config.resolve().parents[1] / "scripts" / "run_tests.sh"
        try:
            result = diagnostics_runner.run_diagnostics(script_path)
        except diagnostics_runner.DiagnosticsError as exc:
            result = diagnostics_runner.DiagnosticsResult(
                status="error",
                output=f"Diagnose fehlgeschlagen: {exc}",
                exit_code=2,
                duration_seconds=0.0,
                command=["bash", str(script_path)],
            )
        self.root.after(0, lambda: self._finish_diagnostics(result))

    def _finish_diagnostics(self, result: diagnostics_runner.DiagnosticsResult) -> None:
        if not isinstance(result, diagnostics_runner.DiagnosticsResult):
            raise GuiLauncherError("Diagnose-Ergebnis ist ungültig.")
        self.diagnostics_running = False
        if self.diagnostics_button is not None:
            self.diagnostics_button.configure(state="normal")
        report = self._format_diagnostics_report(result)
        current = ""
        if self.output_text is not None:
            current = self.output_text.get("1.0", "end").strip()
        combined = f"{current}\n\n{report}" if current else report
        self._set_output(combined)
        if result.status == "ok":
            self._set_status("Diagnose abgeschlossen.", state="success")
        else:
            self._set_status("Diagnose mit Problemen abgeschlossen.", state="error")

    def _format_diagnostics_report(self, result: diagnostics_runner.DiagnosticsResult) -> str:
        duration = f"{result.duration_seconds:.1f}"
        lines = [
            "Diagnose (Tests + Codequalität):",
            f"Status: {result.status}",
            f"Dauer: {duration} Sekunden",
            f"Exit-Code: {result.exit_code}",
            f"Kommando: {' '.join(result.command)}",
            "",
            "Ausgabe:",
            result.output or "Keine Ausgabe erhalten.",
        ]
        return "\n".join(lines).rstrip() + "\n"

    def _set_output(self, text: str) -> None:
        clean_text = _require_text(text, "output_text")
        if not clean_text.strip():
            raise GuiLauncherError("Ausgabetext ist leer.")
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", clean_text)
        self.output_text.configure(state="disabled")

    def _append_output(self, text: str) -> None:
        clean_text = _require_text(text, "append_text")
        if not clean_text.strip():
            raise GuiLauncherError("Ausgabetext ist leer.")
        current = ""
        if self.output_text is not None:
            current = self.output_text.get("1.0", "end").rstrip()
        combined = f"{current}\n\n{clean_text}" if current else clean_text
        self._set_output(combined)

    def _set_status(self, message: str, state: str = "success") -> None:
        if not isinstance(message, str) or not message.strip():
            raise GuiLauncherError("Statusmeldung ist leer.")
        clean_state = _require_text(state, "status_state")
        if clean_state not in {"success", "error", "busy"}:
            raise GuiLauncherError("Status-State ist ungültig.")
        if self.status_var is not None:
            self.status_var.set(f"Status: {message}")
        self._apply_status_style(clean_state)
        self.root.configure(cursor="watch" if clean_state == "busy" else "")
        self.root.update_idletasks()

    def _apply_status_style(self, state: str) -> None:
        if self.status_label is None or not self.status_palette:
            return
        bg = self.status_palette.get(state, self.status_palette.get("success", ""))
        fg = self.status_palette.get("foreground", "")
        if bg:
            self.status_label.configure(bg=bg)
            if self.status_indicator is not None:
                self.status_indicator.configure(bg=bg, fg=fg or "#ffffff")
        if fg:
            self.status_label.configure(fg=fg)

    def _show_error(self, message: str) -> None:
        import tkinter.messagebox as messagebox

        cleaned = message.strip() if isinstance(message, str) else "Unbekannter Fehler."
        friendly = (
            "Es gab ein Problem beim Aktualisieren der Modulübersicht.\n\n"
            f"Ursache: {cleaned}\n\n"
            "Lösung: Prüfe die Einträge in config/modules.json und die Modulordner. "
            "Danach erneut auf „Übersicht aktualisieren“ klicken."
        )
        messagebox.showerror("Fehler", friendly)

    def _append_module_check(self, text: str, issues: List[str]) -> str:
        if not isinstance(text, str) or not text.strip():
            raise GuiLauncherError("Ausgabetext ist leer.")
        lines = [text.rstrip(), "", "Modul-Check:"]
        if issues:
            lines.append("Es wurden Probleme gefunden:")
            lines.extend(
                [f"- {issue} (Stufe: {qa_checks.classify_issue(issue)})" for issue in issues]
            )
            lines.append("Lösung: Bitte config/modules.json und die Modulordner korrigieren.")
            self._show_error("Modul-Check: Probleme gefunden. Details stehen in der Übersicht.")
            self.logger.error("Modul-Check: %s Problem(e) gefunden.", len(issues))
            for issue in issues:
                self.logger.error("Modul-Check: %s", issue)
        else:
            lines.append("Alle aktiven Module sind vorhanden und korrekt.")
        return "\n".join(lines).rstrip() + "\n"

    def _append_file_status(self, text: str, report: qa_checks.FileStatusReport) -> str:
        if not isinstance(text, str) or not text.strip():
            raise GuiLauncherError("Ausgabetext ist leer.")
        lines = [text.rstrip(), "", "Datei-Status (Ampel):"]
        lines.append(f"Ampelstatus: {report.traffic_light}")
        if report.issues:
            lines.append("Datei-Probleme:")
            for issue in report.issues:
                lines.append(f"- {issue.message} (Stufe: {issue.severity})")
        else:
            lines.append("Keine Datei-Probleme gefunden.")
        return "\n".join(lines).rstrip() + "\n"

    def _append_selftests(self, text: str, results: List[module_selftests.SelftestResult]) -> str:
        if not isinstance(text, str) or not text.strip():
            raise GuiLauncherError("Ausgabetext ist leer.")
        lines = [text.rstrip(), "", "Modul-Selbsttests:"]
        for result in results:
            lines.append(
                f"- {result.name} ({result.module_id}): {result.status} – {result.message}"
            )
        return "\n".join(lines).rstrip() + "\n"

    def _append_error_simulation(
        self, text: str, results: List[error_simulation.SimulationResult]
    ) -> str:
        if not isinstance(text, str) or not text.strip():
            raise GuiLauncherError("Ausgabetext ist leer.")
        lines = [text.rstrip(), "", "Fehler-Simulation (Laienfehler):"]
        for result in results:
            lines.append(f"- Fall: {result.title}")
            lines.append(f"  Ergebnis: {result.status}")
            lines.append(f"  Meldung: {result.message}")
            lines.append(f"  Hinweis: {result.hint}")
        return "\n".join(lines).rstrip() + "\n"


def run_gui(
    module_config: Path,
    gui_config: GuiConfigModel,
    show_all: bool,
    debug: bool,
) -> int:
    if not isinstance(module_config, Path):
        raise GuiLauncherError("module_config ist kein Pfad (Path).")

    import tkinter as tk

    _require_bool(show_all, "show_all")
    _require_bool(debug, "debug")
    root = tk.Tk()
    app = LauncherGui(
        root=root,
        module_config=module_config,
        gui_config=gui_config,
        show_all=show_all,
        debug=debug,
    )
    app.apply_theme(app.theme_var.get())
    root.mainloop()
    return_code = 0
    if not isinstance(return_code, int):
        raise GuiLauncherError("Rückgabewert ist ungültig.")
    return return_code


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.debug)
    logger = get_logger("launcher_gui")

    try:
        gui_config = load_gui_config(args.gui_config)
        return run_gui(args.config, gui_config, args.show_all, args.debug)
    except (GuiLauncherError, LauncherError) as exc:
        logger.error("GUI-Launcher konnte nicht starten: %s", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
