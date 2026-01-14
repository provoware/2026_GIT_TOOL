#!/usr/bin/env python3
"""GUI-Launcher: zeigt Module in einer barrierefreien Startübersicht an."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import config_utils
import error_simulation
import module_checker
import module_selftests
import qa_checks
from launcher import (
    LauncherError,
    filter_modules,
    load_modules,
    resolve_module_path,
)

DEFAULT_MODULE_CONFIG = Path(__file__).resolve().parents[1] / "config" / "modules.json"
DEFAULT_GUI_CONFIG = Path(__file__).resolve().parents[1] / "config" / "launcher_gui.json"


class GuiLauncherError(Exception):
    """Allgemeiner Fehler für den GUI-Launcher."""


@dataclass(frozen=True)
class Theme:
    name: str
    label: str
    colors: Dict[str, str]


@dataclass(frozen=True)
class GuiConfig:
    default_theme: str
    themes: Dict[str, Theme]


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


def _validate_color(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GuiLauncherError(f"Farbe fehlt: {label}.")
    text = value.strip()
    if not text.startswith("#") or len(text) not in {4, 7}:
        raise GuiLauncherError(f"Farbe {label} ist ungültig. Erwartet z. B. #fff oder #ffffff.")
    return text


def load_gui_config(config_path: Path) -> GuiConfig:
    config_utils.ensure_path(config_path, "config_path", GuiLauncherError)
    data = config_utils.load_json(
        config_path,
        GuiLauncherError,
        "GUI-Konfiguration fehlt",
        "GUI-Konfiguration ist kein gültiges JSON",
    )
    default_theme = _require_text(data.get("default_theme"), "default_theme")
    themes_raw = data.get("themes")
    if not isinstance(themes_raw, dict) or not themes_raw:
        raise GuiLauncherError("themes fehlen oder sind leer.")

    themes: Dict[str, Theme] = {}
    for name, entry in themes_raw.items():
        theme_name = _require_text(name, "theme_name")
        if not isinstance(entry, dict):
            raise GuiLauncherError(f"Theme {theme_name} ist kein Objekt.")
        label = _require_text(entry.get("label"), f"themes.{theme_name}.label")
        colors_raw = entry.get("colors")
        if not isinstance(colors_raw, dict):
            raise GuiLauncherError(f"Theme {theme_name} hat keine Farben.")
        colors = {
            "background": _validate_color(colors_raw.get("background"), "background"),
            "foreground": _validate_color(colors_raw.get("foreground"), "foreground"),
            "accent": _validate_color(colors_raw.get("accent"), "accent"),
            "button_background": _validate_color(
                colors_raw.get("button_background"), "button_background"
            ),
            "button_foreground": _validate_color(
                colors_raw.get("button_foreground"), "button_foreground"
            ),
            "status_success": _validate_color(colors_raw.get("status_success"), "status_success"),
            "status_error": _validate_color(colors_raw.get("status_error"), "status_error"),
            "status_busy": _validate_color(colors_raw.get("status_busy"), "status_busy"),
            "status_foreground": _validate_color(
                colors_raw.get("status_foreground"), "status_foreground"
            ),
        }
        themes[theme_name] = Theme(name=theme_name, label=label, colors=colors)

    if default_theme not in themes:
        raise GuiLauncherError("default_theme ist nicht in themes enthalten.")

    return GuiConfig(default_theme=default_theme, themes=themes)


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
            module_path = resolve_module_path(root, module.path)
            lines.append(f"   Pfad: {module_path}")
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
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


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
        gui_config: GuiConfig,
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
        self.status_var = None
        self.status_label = None
        self.footer_label = None
        self.help_label = None
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

        self.root.title("Launcher – Startübersicht")
        self.root.minsize(640, 420)
        self._build_ui(show_all)

    def _build_ui(self, show_all: bool) -> None:
        import tkinter as tk
        import tkinter.font as tkfont

        _require_bool(show_all, "show_all")
        self._init_fonts(tkfont)

        header = tk.Label(
            self.root,
            text="Startübersicht: Module",
            font=self.header_font,
            anchor="w",
        )
        header.pack(fill="x", padx=16, pady=(16, 8))

        controls_section = tk.LabelFrame(self.root, text="Einstellungen und Filter")
        controls_section.pack(fill="x", padx=16, pady=(0, 12))
        controls = tk.Frame(controls_section)
        controls.pack(fill="x", padx=12, pady=8)

        tk.Label(controls, text="Farbschema:").grid(row=0, column=0, sticky="w")
        self.theme_var = tk.StringVar(value=self.gui_config.default_theme)
        self.theme_menu = tk.OptionMenu(
            controls,
            self.theme_var,
            *self.gui_config.themes.keys(),
            command=lambda _value: self.apply_theme(self.theme_var.get()),
        )
        if self.button_font is not None:
            self.theme_menu.configure(font=self.button_font)
        self.theme_menu.configure(padx=8, pady=4)
        self.theme_menu.configure(takefocus=1)
        self.theme_menu.grid(row=0, column=1, sticky="w", padx=(8, 24))

        self.show_all_var = tk.BooleanVar(value=show_all)
        self.show_all_check = tk.Checkbutton(
            controls,
            text="Alle Module anzeigen (inkl. deaktiviert)",
            variable=self.show_all_var,
            command=self.refresh,
        )
        if self.button_font is not None:
            self.show_all_check.configure(font=self.button_font)
        self.show_all_check.configure(padx=6, pady=4)
        self.show_all_check.configure(takefocus=1, underline=0)
        self.show_all_check.grid(row=0, column=2, sticky="w", padx=(8, 0), pady=4)

        self.debug_var = tk.BooleanVar(value=self.debug)
        self.debug_check = tk.Checkbutton(
            controls,
            text="Debug-Details anzeigen",
            variable=self.debug_var,
            command=self.refresh,
        )
        if self.button_font is not None:
            self.debug_check.configure(font=self.button_font)
        self.debug_check.configure(padx=6, pady=4)
        self.debug_check.configure(takefocus=1, underline=0)
        self.debug_check.grid(row=1, column=0, sticky="w", pady=(8, 0), padx=(0, 12))

        self.refresh_button = tk.Button(
            controls,
            text="Übersicht aktualisieren",
            command=self.refresh,
        )
        if self.button_font is not None:
            self.refresh_button.configure(font=self.button_font)
        self.refresh_button.configure(padx=12, pady=6)
        self.refresh_button.configure(takefocus=1, underline=0)
        self.refresh_button.grid(row=1, column=2, sticky="e", padx=(0, 0), pady=(8, 0))

        controls.columnconfigure(2, weight=1)

        help_section = tk.LabelFrame(self.root, text="Hilfe (Kurzinfo)")
        help_section.pack(fill="x", padx=16, pady=(0, 12))
        self.help_label = tk.Label(
            help_section,
            text=(
                "So geht's: Farbschema wählen, Module einblenden und mit "
                "„Übersicht aktualisieren“ prüfen. "
                "Kontrastmodus: Alt+K. Zoom: Strg + Mausrad. "
                "Tastatur: Tab für Fokus, Alt+A (alle Module), Alt+D (Debug), "
                "Alt+R (aktualisieren), Alt+T (Theme), Alt+Q (beenden)."
            ),
            anchor="w",
            justify="left",
        )
        self.help_label.pack(fill="x", padx=12, pady=8)

        self.status_var = tk.StringVar(value="Status: Bereit.")
        status_section = tk.LabelFrame(self.root, text="Status")
        status_section.pack(fill="x", padx=16, pady=(0, 8))
        self.status_label = tk.Label(
            status_section,
            textvariable=self.status_var,
            anchor="w",
        )
        self.status_label.pack(fill="x", padx=12, pady=6)

        output_section = tk.LabelFrame(self.root, text="Modulübersicht")
        output_section.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.output_text = tk.Text(
            output_section,
            wrap="word",
            height=16,
            font=self.output_font,
            borderwidth=2,
            relief="groove",
            takefocus=1,
        )
        self.output_text.configure(spacing1=4, spacing2=2, spacing3=4, highlightthickness=2)
        self.output_text.pack(fill="both", expand=True, padx=12, pady=12)
        self.output_text.configure(state="disabled")

        self.footer_label = tk.Label(
            self.root,
            text=(
                "Tipp: Mit Tabulator erreichst du alle Bedienelemente. "
                "Kurzbefehle: Alt+A (alle Module), Alt+D (Debug), Alt+R "
                "(aktualisieren), Alt+T (Theme), Alt+K (Kontrast), "
                "Strg + Mausrad (Zoom), Alt+Q (beenden)."
            ),
            anchor="w",
        )
        self.footer_label.pack(fill="x", padx=16, pady=(0, 12))

        self._bind_accessibility_shortcuts()
        self._bind_responsive_layout()
        self._bind_zoom_controls()
        self.apply_theme(self.gui_config.default_theme)
        self.refresh()
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
        if self.footer_label is None:
            return
        width = max(self.root.winfo_width() - 32, 280)
        self.footer_label.configure(wraplength=width, justify="left")

    def _focus_widget(self, widget) -> None:
        if widget is not None:
            widget.focus_set()

    def _toggle_show_all(self) -> None:
        self.show_all_var.set(not bool(self.show_all_var.get()))
        self.refresh()

    def _toggle_debug(self) -> None:
        self.debug_var.set(not bool(self.debug_var.get()))
        self.refresh()

    def _refresh_from_shortcut(self) -> None:
        if self.refresh_button is not None:
            self.refresh_button.invoke()
        else:
            self.refresh()

    def _resolve_contrast_theme(self) -> Optional[str]:
        if not isinstance(self.gui_config, GuiConfig):
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
            logging.error("GUI-Launcher Fehler: %s", exc)
            self._show_error(str(exc))
            self._set_status("Fehler aufgetreten. Bitte Hinweise lesen.", state="error")
        else:
            self._set_status("Bereit.", state="success")

        self._set_output(text)

    def _set_output(self, text: str) -> None:
        clean_text = _require_text(text, "output_text")
        if not clean_text.strip():
            raise GuiLauncherError("Ausgabetext ist leer.")
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", clean_text)
        self.output_text.configure(state="disabled")

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
            logging.error("Modul-Check: %s Problem(e) gefunden.", len(issues))
            for issue in issues:
                logging.error("Modul-Check: %s", issue)
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


def run_gui(module_config: Path, gui_config: GuiConfig, show_all: bool, debug: bool) -> int:
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

    try:
        gui_config = load_gui_config(args.gui_config)
        return run_gui(args.config, gui_config, args.show_all, args.debug)
    except (GuiLauncherError, LauncherError) as exc:
        logging.error("GUI-Launcher konnte nicht starten: %s", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
