#!/usr/bin/env python3
"""GUI-Launcher: zeigt Module in einer barrierefreien Startübersicht an."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

import config_utils
import module_checker
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
    return lines


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
    return module_checker.check_modules(entries)


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

        self.root.title("Launcher – Startübersicht")
        self.root.minsize(720, 480)
        self._build_ui(show_all)

    def _build_ui(self, show_all: bool) -> None:
        import tkinter as tk

        header = tk.Label(
            self.root,
            text="Startübersicht: Module",
            font=("Arial", 18, "bold"),
            anchor="w",
        )
        header.pack(fill="x", padx=16, pady=(16, 8))

        controls = tk.Frame(self.root)
        controls.pack(fill="x", padx=16, pady=(0, 12))

        tk.Label(controls, text="Farbschema:").grid(row=0, column=0, sticky="w")
        self.theme_var = tk.StringVar(value=self.gui_config.default_theme)
        self.theme_menu = tk.OptionMenu(
            controls,
            self.theme_var,
            *self.gui_config.themes.keys(),
            command=lambda _value: self.apply_theme(self.theme_var.get()),
        )
        self.theme_menu.configure(takefocus=1)
        self.theme_menu.grid(row=0, column=1, sticky="w", padx=(8, 16))

        self.show_all_var = tk.BooleanVar(value=show_all)
        self.show_all_check = tk.Checkbutton(
            controls,
            text="Alle Module anzeigen (inkl. deaktiviert)",
            variable=self.show_all_var,
            command=self.refresh,
        )
        self.show_all_check.configure(takefocus=1, underline=0)
        self.show_all_check.grid(row=0, column=2, sticky="w", padx=(0, 16))

        self.debug_var = tk.BooleanVar(value=self.debug)
        self.debug_check = tk.Checkbutton(
            controls,
            text="Debug-Details anzeigen",
            variable=self.debug_var,
            command=self.refresh,
        )
        self.debug_check.configure(takefocus=1, underline=0)
        self.debug_check.grid(row=0, column=3, sticky="w")

        self.refresh_button = tk.Button(
            controls,
            text="Übersicht aktualisieren",
            command=self.refresh,
        )
        self.refresh_button.configure(takefocus=1, underline=0)
        self.refresh_button.grid(row=0, column=4, sticky="e", padx=(16, 0))

        controls.columnconfigure(4, weight=1)

        self.status_var = tk.StringVar(value="Status: Bereit.")
        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
        )
        self.status_label.pack(fill="x", padx=16, pady=(0, 8))

        output_label = tk.Label(
            self.root,
            text="Modulübersicht (Ausgabe)",
            anchor="w",
        )
        output_label.pack(fill="x", padx=16, pady=(0, 4))

        self.output_text = tk.Text(
            self.root,
            wrap="word",
            height=16,
            font=("Arial", 14),
            borderwidth=2,
            relief="groove",
            takefocus=1,
        )
        self.output_text.configure(spacing1=4, spacing2=2, spacing3=4, highlightthickness=2)
        self.output_text.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.output_text.configure(state="disabled")

        footer = tk.Label(
            self.root,
            text=(
                "Tipp: Mit Tabulator erreichst du alle Bedienelemente. "
                "Shortcuts: Alt+A (alle Module), Alt+D (Debug), "
                "Alt+R (aktualisieren), Alt+T (Theme), Alt+Q (beenden)."
            ),
            anchor="w",
        )
        footer.pack(fill="x", padx=16, pady=(0, 12))

        self._bind_accessibility_shortcuts()
        self.apply_theme(self.gui_config.default_theme)
        self.refresh()
        self.root.after(100, lambda: self._focus_widget(self.theme_menu))

    def _bind_accessibility_shortcuts(self) -> None:
        self.root.bind_all("<Alt-a>", lambda _event: self._toggle_show_all())
        self.root.bind_all("<Alt-d>", lambda _event: self._toggle_debug())
        self.root.bind_all("<Alt-r>", lambda _event: self._refresh_from_shortcut())
        self.root.bind_all("<Alt-t>", lambda _event: self._focus_widget(self.theme_menu))
        self.root.bind_all("<Alt-q>", lambda _event: self.root.quit())
        self.root.bind_all("<Control-r>", lambda _event: self._refresh_from_shortcut())

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

    def apply_theme(self, theme_name: str) -> None:
        if theme_name not in self.gui_config.themes:
            raise GuiLauncherError("Unbekanntes Farbschema.")
        theme = self.gui_config.themes[theme_name]

        bg = theme.colors["background"]
        fg = theme.colors["foreground"]
        accent = theme.colors["accent"]
        button_bg = theme.colors["button_background"]
        button_fg = theme.colors["button_foreground"]

        widgets = self.root.winfo_children()
        self.root.configure(background=bg)
        for widget in widgets:
            self._apply_widget_style(widget, bg, fg, accent, button_bg, button_fg)

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

        for child in widget.winfo_children():
            self._apply_widget_style(child, background, foreground, accent, button_bg, button_fg)

    def refresh(self) -> None:
        show_all = bool(self.show_all_var.get())
        debug = bool(self.debug_var.get())
        try:
            self._set_status("Prüfe Module…", busy=True)
            modules = load_modules(self.module_config)
            modules = filter_modules(modules, show_all)
            root_dir = self.module_config.resolve().parents[1]
            text = render_module_text(modules, root_dir, debug)
            issues = run_module_check(self.module_config)
            text = self._append_module_check(text, issues)
        except (LauncherError, GuiLauncherError) as exc:
            text = (
                "Fehler beim Aktualisieren.\n"
                f"Ursache: {exc}\n"
                "Lösung: Bitte config/modules.json und die Modulordner prüfen, "
                "danach erneut auf „Übersicht aktualisieren“ klicken.\n"
            )
            logging.error("GUI-Launcher Fehler: %s", exc)
            self._show_error(str(exc))
            self._set_status("Fehler aufgetreten. Bitte Hinweise lesen.", busy=False)
        else:
            self._set_status("Bereit.", busy=False)

        self._set_output(text)

    def _set_output(self, text: str) -> None:
        if not isinstance(text, str) or not text.strip():
            raise GuiLauncherError("Ausgabetext ist leer.")
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", text)
        self.output_text.configure(state="disabled")

    def _set_status(self, message: str, busy: bool) -> None:
        if not isinstance(message, str) or not message.strip():
            raise GuiLauncherError("Statusmeldung ist leer.")
        if self.status_var is not None:
            self.status_var.set(f"Status: {message}")
        self.root.configure(cursor="watch" if busy else "")
        self.root.update_idletasks()

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
            lines.extend([f"- {issue}" for issue in issues])
            lines.append("Lösung: Bitte config/modules.json und die Modulordner korrigieren.")
            self._show_error("Modul-Check: Probleme gefunden. Details stehen in der Übersicht.")
            logging.error("Modul-Check: %s Problem(e) gefunden.", len(issues))
            for issue in issues:
                logging.error("Modul-Check: %s", issue)
        else:
            lines.append("Alle aktiven Module sind vorhanden und korrekt.")
        return "\n".join(lines).rstrip() + "\n"


def run_gui(module_config: Path, gui_config: GuiConfig, show_all: bool, debug: bool) -> int:
    if not isinstance(module_config, Path):
        raise GuiLauncherError("module_config ist kein Pfad (Path).")

    import tkinter as tk

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
    return 0


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
