#!/usr/bin/env python3
"""GUI-Launcher: zeigt Module in einer barrierefreien Startübersicht an."""

from __future__ import annotations

import argparse
import subprocess
import threading
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import autosave_manager
import backup_center
import diagnostics_runner
import end_audit
import error_simulation
import main_window
import module_checker
import module_selftests
import qa_checks
from config_models import ConfigModelError, GuiConfigModel
from config_models import load_gui_config as load_gui_config_model
from drag_drop import DragDropManager
from launcher import LauncherError, filter_modules, load_modules
from logging_center import get_logger
from logging_center import setup_logging as setup_logging_center
from module_manager import ModuleManagerError
from undo_redo import UndoRedoAction, UndoRedoError, UndoRedoManager

DEFAULT_MODULE_CONFIG = Path(__file__).resolve().parents[1] / "config" / "modules.json"
DEFAULT_GUI_CONFIG = Path(__file__).resolve().parents[1] / "config" / "launcher_gui.json"
DEFAULT_SETTINGS_CONFIG = Path(__file__).resolve().parents[1] / "config" / "global_settings.json"
DEFAULT_DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
DEFAULT_LOG_ROOT = Path(__file__).resolve().parents[1] / "logs"
BRAND_NAME = "Genrearchiv"
ICON_SET = {
    "header": "🧭",
    "theme": "🎨",
    "refresh": "🔄",
    "diagnostics": "🧪",
    "main_window": "🧩",
    "developer": "🛠️",
    "logout": "🚪",
    "scan": "🩺",
    "standards": "📏",
    "logs": "📂",
    "export": "📦",
    "export_center": "📤",
    "backup": "🗄️",
    "drop": "🧲",
}


class GuiLauncherError(Exception):
    """Allgemeiner Fehler für den GUI-Launcher."""


class Tooltip:
    def __init__(
        self,
        widget,
        text_provider,
        delay_ms: int = 500,
        max_width: int = 360,
        font=None,
    ) -> None:
        if widget is None:
            raise GuiLauncherError("Tooltip-Widget fehlt.")
        if not callable(text_provider):
            raise GuiLauncherError("Tooltip-Provider ist ungültig.")
        if not isinstance(delay_ms, int) or delay_ms < 0:
            raise GuiLauncherError("Tooltip-Delay ist ungültig.")
        if not isinstance(max_width, int) or max_width < 120:
            raise GuiLauncherError("Tooltip-Breite ist ungültig.")
        self.widget = widget
        self.text_provider = text_provider
        self.delay_ms = delay_ms
        self.max_width = max_width
        self.font = font
        self._after_id = None
        self._tip_window = None

        self.widget.bind("<Enter>", self._schedule, add="+")
        self.widget.bind("<Leave>", self._hide, add="+")
        self.widget.bind("<FocusIn>", self._schedule, add="+")
        self.widget.bind("<FocusOut>", self._hide, add="+")

    def _schedule(self, _event=None) -> None:
        self._cancel()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self) -> None:
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self) -> None:
        if self._tip_window is not None:
            return
        payload = self.text_provider()
        if not isinstance(payload, dict):
            raise GuiLauncherError("Tooltip-Payload ist ungültig.")
        text = payload.get("text", "")
        if not isinstance(text, str) or not text.strip():
            return
        import tkinter as tk

        bg = payload.get("bg", "#1f1f1f")
        fg = payload.get("fg", "#ffffff")
        border = payload.get("border", "#ffffff")
        self._tip_window = tk.Toplevel(self.widget)
        tip = self._tip_window
        tip.wm_overrideredirect(True)
        tip.configure(background=border)

        container = tk.Frame(tip, background=border, padx=1, pady=1)
        container.pack(fill="both", expand=True)
        label = tk.Label(
            container,
            text=text,
            background=bg,
            foreground=fg,
            justify="left",
            wraplength=self.max_width,
            padx=8,
            pady=6,
        )
        if self.font is not None:
            label.configure(font=self.font)
        label.pack(fill="both", expand=True)

        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        tip.wm_geometry(f"+{x}+{y}")

    def _hide(self, _event=None) -> None:
        self._cancel()
        if self._tip_window is not None:
            self._tip_window.destroy()
            self._tip_window = None


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
        self.main_window_button = None
        self.logout_button = None
        self.scan_button = None
        self.standards_button = None
        self.logs_button = None
        self.export_button = None
        self.export_center_button = None
        self.backup_button = None
        self.diagnostics_running = False
        self.maintenance_running = False
        self.refresh_job = None
        self.refresh_debounce_ms = gui_config.refresh_debounce_ms
        self.logger = get_logger("launcher_gui")
        self.status_var = None
        self.status_label = None
        self.status_indicator = None
        self.footer_label = None
        self.help_section = None
        self.help_label = None
        self.context_help_label = None
        self.drop_zone_label = None
        self.context_help_default = (
            "Kontext-Hilfe: Wähle ein Feld oder einen Knopf, "
            "dann erscheint hier eine kurze Erklärung."
        )
        self.current_help_text = self.context_help_default
        self.help_texts: Dict[object, str] = {}
        self.tooltips: List[Tooltip] = []
        self.tooltip_style: Dict[str, str] = {}
        self.developer_hint = None
        self.controls_frame = None
        self.developer_frame = None
        self.header_font = None
        self.output_font = None
        self.button_font = None
        self.base_font_sizes: Dict[str, int] = {}
        self.base_header_size = 18
        self.base_output_size = 14
        self.base_button_size = 14
        self.button_min_width = 0
        self.zoom_level = 1.0
        self.last_non_contrast_theme = self.gui_config.default_theme
        self.contrast_theme = self._resolve_contrast_theme()
        self.status_palette: Dict[str, str] = {}
        self.layout = self.gui_config.layout
        self.base_button_size = self.layout.button_font_size
        self.button_min_width = self.layout.button_min_width
        self.autosave_config: autosave_manager.AutosaveConfig | None = None
        self.autosave_job = None
        self.logout_running = False
        self.undo_manager = UndoRedoManager(limit=50)
        self.drag_drop_manager = None
        self.current_theme = self.gui_config.default_theme

        self.root.title(f"{BRAND_NAME} – Startübersicht")
        self.root.minsize(640, 420)
        self._build_ui(show_all)
        self._setup_autosave()

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
        self.controls_frame = controls

        tk.Label(controls, text=f"{ICON_SET['theme']} Farbschema:").grid(
            row=0, column=0, sticky="w"
        )
        self.theme_var = tk.StringVar(value=self.gui_config.default_theme)
        self.theme_menu = tk.OptionMenu(
            controls,
            self.theme_var,
            *self.gui_config.themes.keys(),
            command=lambda _value: self._on_theme_changed(self.theme_var.get()),
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
        self.refresh_button.configure(
            padx=self.layout.button_padx,
            pady=self.layout.button_pady,
            width=self.button_min_width,
        )
        self.refresh_button.configure(takefocus=1, underline=0)
        self.refresh_button.grid(
            row=1,
            column=2,
            sticky="e",
            padx=(0, 0),
            pady=(self.layout.gap_sm, 0),
        )

        self.logout_button = tk.Button(
            controls,
            text=f"{ICON_SET['logout']} Abmelden & sichern",
            command=self.request_logout,
        )
        if self.button_font is not None:
            self.logout_button.configure(font=self.button_font)
        self.logout_button.configure(
            padx=self.layout.button_padx,
            pady=self.layout.button_pady,
            width=self.button_min_width,
        )
        self.logout_button.configure(takefocus=1, underline=0)
        self.logout_button.grid(
            row=2,
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
            padx=self.layout.button_padx,
            pady=self.layout.button_pady,
            width=self.button_min_width,
        )
        self.diagnostics_button.configure(takefocus=1, underline=0)
        self.diagnostics_button.grid(
            row=1,
            column=1,
            sticky="w",
            padx=(self.layout.gap_sm, self.layout.gap_md),
            pady=(self.layout.gap_sm, 0),
        )

        self.main_window_button = tk.Button(
            controls,
            text=f"{ICON_SET['main_window']} Hauptfenster öffnen",
            command=self.open_main_window,
        )
        if self.button_font is not None:
            self.main_window_button.configure(font=self.button_font)
        self.main_window_button.configure(
            padx=self.layout.button_padx,
            pady=self.layout.button_pady,
            width=self.button_min_width,
        )
        self.main_window_button.configure(takefocus=1, underline=0)
        self.main_window_button.grid(
            row=2,
            column=1,
            sticky="w",
            padx=(self.layout.gap_sm, self.layout.gap_md),
            pady=(self.layout.gap_sm, 0),
        )

        controls.columnconfigure(2, weight=1)

        help_section = tk.LabelFrame(self.root, text="Hilfe (Kurzinfo)")
        help_section.pack(fill="x", padx=self.layout.gap_lg, pady=(0, self.layout.gap_md))
        help_section.columnconfigure(0, weight=1)
        help_section.columnconfigure(1, weight=1)
        self.help_section = help_section
        self.help_label = tk.Label(
            help_section,
            text=(
                "So geht's: Farbschema wählen, Module einblenden und mit "
                "„Übersicht aktualisieren“ prüfen. "
                "Diagnose: „Diagnose starten“ führt Tests und Codeprüfungen aus. "
                "Entwicklerbereich: System-Scan (Prüfung), Standards (Regeln) und "
                "Log-Ordner (Protokolle), Backup (Sicherung) und Export-Center "
                "(Export = Ausgabedatei) sowie selektiver Export (Teil-Export). "
                "Kontrastmodus: Alt+K. Zoom: Strg + Mausrad. "
                "Tastatur: Tab für Fokus, F1 für Kontext-Hilfe. "
                "Kurzbefehle: Alt+A (alle Module), Alt+D (Debug), Alt+R (aktualisieren), "
                "Alt+G (Diagnose), Alt+M (Hauptfenster), Alt+S (System-Scan), Alt+P (Standards), "
                "Alt+L (Logs), Alt+E (Export), Alt+X (Export-Center), Alt+B (Backup), "
                "Alt+T (Theme), Alt+Q (abmelden & sichern), Strg+Z (Undo), Strg+Y (Redo)."
            ),
            anchor="w",
            justify="left",
        )
        self.help_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=self.layout.gap_md,
            pady=self.layout.gap_sm,
        )

        self.context_help_label = tk.Label(
            help_section,
            text=self.context_help_default,
            anchor="w",
            justify="left",
        )
        self.context_help_label.grid(
            row=0,
            column=1,
            sticky="w",
            padx=self.layout.gap_md,
            pady=self.layout.gap_sm,
        )

        self.drop_zone_label = tk.Label(
            help_section,
            text=(
                f"{ICON_SET['drop']} Dateien/Module hierher ziehen "
                "(Drag-and-Drop = Ziehen & Ablegen)."
            ),
            anchor="w",
            justify="left",
            relief="ridge",
            padx=self.layout.gap_sm,
            pady=self.layout.gap_sm,
        )
        self.drop_zone_label.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=self.layout.gap_md,
            pady=(0, self.layout.gap_sm),
        )

        developer_section = tk.LabelFrame(
            self.root, text=f"{ICON_SET['developer']} Entwicklerbereich (für Profis)"
        )
        developer_section.pack(fill="x", padx=self.layout.gap_lg, pady=(0, self.layout.gap_md))
        developer_frame = tk.Frame(developer_section)
        developer_frame.pack(fill="x", padx=self.layout.gap_md, pady=self.layout.gap_sm)
        self.developer_frame = developer_frame

        self.developer_hint = tk.Label(
            developer_frame,
            text=(
                "Hier findest du technische Hilfen: System-Scan (Prüfung), "
                "Standards-Liste (Regeln), Log-Ordner (Protokolle) und "
                "selektive Exporte (Teil-Exporte), Export-Center (Mehrformat) "
                "sowie Backups (Sicherungen)."
            ),
            anchor="w",
            justify="left",
        )
        self.developer_hint.grid(row=0, column=0, columnspan=4, sticky="w")

        self.scan_button = tk.Button(
            developer_frame,
            text=f"{ICON_SET['scan']} System-Scan starten",
            command=self.start_system_scan,
        )
        if self.button_font is not None:
            self.scan_button.configure(font=self.button_font)
        self.scan_button.configure(
            padx=self.layout.button_padx,
            pady=self.layout.button_pady,
            width=self.button_min_width,
        )
        self.scan_button.configure(takefocus=1, underline=0)
        self.scan_button.grid(row=1, column=0, sticky="w", padx=(0, self.layout.gap_md))

        self.standards_button = tk.Button(
            developer_frame,
            text=f"{ICON_SET['standards']} Standards anzeigen",
            command=self.show_standards,
        )
        if self.button_font is not None:
            self.standards_button.configure(font=self.button_font)
        self.standards_button.configure(
            padx=self.layout.button_padx,
            pady=self.layout.button_pady,
            width=self.button_min_width,
        )
        self.standards_button.configure(takefocus=1, underline=0)
        self.standards_button.grid(row=1, column=1, sticky="w", padx=(0, self.layout.gap_md))

        self.logs_button = tk.Button(
            developer_frame,
            text=f"{ICON_SET['logs']} Log-Ordner öffnen",
            command=self.open_logs,
        )
        if self.button_font is not None:
            self.logs_button.configure(font=self.button_font)
        self.logs_button.configure(
            padx=self.layout.button_padx,
            pady=self.layout.button_pady,
            width=self.button_min_width,
        )
        self.logs_button.configure(takefocus=1, underline=0)
        self.logs_button.grid(row=1, column=2, sticky="w")

        self.export_button = tk.Button(
            developer_frame,
            text=f"{ICON_SET['export']} Selektiver Export",
            command=self.start_selective_export,
        )
        if self.button_font is not None:
            self.export_button.configure(font=self.button_font)
        self.export_button.configure(
            padx=self.layout.button_padx,
            pady=self.layout.button_pady,
            width=self.button_min_width,
        )
        self.export_button.configure(takefocus=1, underline=0)
        self.export_button.grid(row=1, column=3, sticky="w", padx=(self.layout.gap_md, 0))

        self.export_center_button = tk.Button(
            developer_frame,
            text=f"{ICON_SET['export_center']} Export-Center",
            command=self.start_export_center,
        )
        if self.button_font is not None:
            self.export_center_button.configure(font=self.button_font)
        self.export_center_button.configure(
            padx=self.layout.button_padx,
            pady=self.layout.button_pady,
            width=self.button_min_width,
        )
        self.export_center_button.configure(takefocus=1, underline=0)
        self.export_center_button.grid(row=2, column=0, sticky="w", padx=(0, self.layout.gap_md))

        self.backup_button = tk.Button(
            developer_frame,
            text=f"{ICON_SET['backup']} Backup erstellen",
            command=self.start_backup,
        )
        if self.button_font is not None:
            self.backup_button.configure(font=self.button_font)
        self.backup_button.configure(
            padx=self.layout.button_padx,
            pady=self.layout.button_pady,
            width=self.button_min_width,
        )
        self.backup_button.configure(takefocus=1, underline=0)
        self.backup_button.grid(row=2, column=1, sticky="w", padx=(0, self.layout.gap_md))

        developer_frame.columnconfigure(3, weight=1)

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
                "Kurzbefehle: F1 (Kontext-Hilfe), Alt+A (alle Module), Alt+D (Debug), Alt+R "
                "(aktualisieren), Alt+G (Diagnose), Alt+S (System-Scan), "
                "Alt+P (Standards), Alt+L (Logs), Alt+E (Export), Alt+X (Export-Center), "
                "Alt+B (Backup), Alt+T (Theme), Alt+K (Kontrast), Strg+Z (Undo), "
                "Strg+Y (Redo), Strg + Mausrad (Zoom), Alt+Q (abmelden & sichern)."
            ),
            anchor="w",
        )
        self.footer_label.pack(fill="x", padx=self.layout.gap_lg, pady=(0, self.layout.gap_md))

        self._bind_accessibility_shortcuts()
        self._bind_responsive_layout()
        self._bind_zoom_controls()
        self._bind_help_context()
        self._register_help_entries()
        self._setup_drag_drop()
        self.root.protocol("WM_DELETE_WINDOW", self.request_logout)
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
        self.root.bind_all("<Alt-m>", lambda _event: self.open_main_window())
        self.root.bind_all("<Alt-s>", lambda _event: self.start_system_scan())
        self.root.bind_all("<Alt-p>", lambda _event: self.show_standards())
        self.root.bind_all("<Alt-l>", lambda _event: self.open_logs())
        self.root.bind_all("<Alt-e>", lambda _event: self.start_selective_export())
        self.root.bind_all("<Alt-x>", lambda _event: self.start_export_center())
        self.root.bind_all("<Alt-b>", lambda _event: self.start_backup())
        self.root.bind_all("<Alt-q>", lambda _event: self.request_logout())
        self.root.bind_all("<Control-r>", lambda _event: self._refresh_from_shortcut())
        self.root.bind_all("<Control-z>", lambda _event: self.undo_action())
        self.root.bind_all("<Control-y>", lambda _event: self.redo_action())
        self.root.bind_all("<Control-Shift-Z>", lambda _event: self.redo_action())
        self.root.bind_all("<F1>", lambda _event: self._announce_context_help())

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
        self._apply_button_widths()

    def _apply_button_widths(self) -> None:
        width = max(0, int(round(self.button_min_width * self.zoom_level)))
        for button in (
            self.refresh_button,
            self.diagnostics_button,
            self.logout_button,
            self.scan_button,
            self.standards_button,
            self.logs_button,
            self.export_button,
            self.export_center_button,
            self.backup_button,
        ):
            if button is not None:
                button.configure(width=width)

    def _bind_responsive_layout(self) -> None:
        self.root.bind("<Configure>", lambda _event: self._update_layout_by_width())
        self._update_layout_by_width()

    def _update_wrap_length(self) -> None:
        width = max(self.root.winfo_width() - 32, 280)
        if self.footer_label is not None:
            self.footer_label.configure(wraplength=width, justify="left")
        if self.help_label is not None:
            self.help_label.configure(wraplength=width, justify="left")
        if self.context_help_label is not None:
            self.context_help_label.configure(wraplength=width, justify="left")
        if self.developer_hint is not None:
            self.developer_hint.configure(wraplength=width, justify="left")
        if self.drop_zone_label is not None:
            self.drop_zone_label.configure(wraplength=width, justify="left")
        if self.status_label is not None:
            self.status_label.configure(wraplength=width, justify="left")

    def _update_layout_by_width(self) -> None:
        width = self.root.winfo_width()
        self._update_wrap_length()
        if (
            self.help_section is not None
            and self.help_label is not None
            and self.context_help_label is not None
        ):
            if width >= 900:
                self.help_label.grid_configure(row=0, column=0, columnspan=1, sticky="w")
                self.context_help_label.grid_configure(
                    row=0,
                    column=1,
                    columnspan=1,
                    sticky="w",
                )
            else:
                self.help_label.grid_configure(row=0, column=0, columnspan=2, sticky="w")
                self.context_help_label.grid_configure(
                    row=1,
                    column=0,
                    columnspan=2,
                    sticky="w",
                )
        if self.drop_zone_label is not None:
            row = 1 if width >= 900 else 2
            self.drop_zone_label.grid_configure(row=row, column=0, columnspan=2, sticky="ew")
        if self.developer_frame is not None and self.export_center_button is not None:
            if width >= 900:
                self.export_center_button.grid_configure(row=2, column=0)
                if self.backup_button is not None:
                    self.backup_button.grid_configure(row=2, column=1)
            else:
                self.export_center_button.grid_configure(
                    row=3,
                    column=0,
                    padx=(0, self.layout.gap_md),
                )
                if self.backup_button is not None:
                    self.backup_button.grid_configure(
                        row=3,
                        column=1,
                        padx=(0, self.layout.gap_md),
                    )

    def _bind_help_context(self) -> None:
        self.root.bind_all("<FocusIn>", self._handle_focus_in, add="+")
        self.root.bind_all("<FocusOut>", self._handle_focus_out, add="+")

    def _handle_focus_in(self, event) -> None:
        widget = getattr(event, "widget", None)
        if widget in self.help_texts:
            self._set_context_help(self.help_texts[widget])

    def _handle_focus_out(self, _event) -> None:
        self._set_context_help(self.context_help_default)

    def _set_context_help(self, text: str) -> None:
        clean_text = _require_text(text, "context_help")
        self.current_help_text = clean_text
        if self.context_help_label is not None:
            self.context_help_label.configure(text=clean_text)

    def _announce_context_help(self) -> None:
        if not isinstance(self.current_help_text, str) or not self.current_help_text.strip():
            return
        self._set_status(f"Hilfe: {self.current_help_text}", state="success")

    def _setup_drag_drop(self) -> None:
        if self.drop_zone_label is None:
            return
        self.drag_drop_manager = DragDropManager(self.root, self._handle_drop_paths)
        enabled = self.drag_drop_manager.enable([self.drop_zone_label, self.root])
        status_text = (
            "Drag-and-Drop bereit."
            if enabled
            else "Drag-and-Drop nicht verfügbar. Bitte per Datei-Dialog arbeiten."
        )
        self._set_status(status_text, state="success" if enabled else "error")

    def _handle_drop_paths(self, paths: List[Path]) -> None:
        if not paths:
            self._set_status("Drop ohne Dateien erkannt.", state="error")
            return
        summary = self._summarize_drop(paths)
        self._append_output(summary)
        self._set_status("Drop verarbeitet.", state="success")

    def _summarize_drop(self, paths: List[Path]) -> str:
        lines = ["Drag-and-Drop erkannt:", ""]
        for path in paths:
            label = "Datei"
            if path.is_dir():
                label = "Ordner"
            elif "modules" in path.parts:
                label = "Modul"
            lines.append(f"- {label}: {path}")
        lines.append("")
        lines.append("Tipp: Prüfe die Pfade und starte bei Bedarf den Export oder ein Backup.")
        return "\n".join(lines) + "\n"

    def _tooltip_payload(self, text: str) -> Dict[str, str]:
        clean_text = _require_text(text, "tooltip_text")
        payload = {
            "text": clean_text,
            "bg": self.tooltip_style.get("bg", "#1f1f1f"),
            "fg": self.tooltip_style.get("fg", "#ffffff"),
            "border": self.tooltip_style.get("border", "#ffffff"),
        }
        return payload

    def _register_tooltip(self, widget, text: str) -> None:
        clean_text = _require_text(text, "tooltip_text")
        tooltip = Tooltip(
            widget=widget,
            text_provider=lambda: self._tooltip_payload(clean_text),
            delay_ms=500,
            max_width=360,
            font=self.button_font,
        )
        self.tooltips.append(tooltip)

    def _register_help(self, widget, tooltip_text: str, context_text: str) -> None:
        clean_context = _require_text(context_text, "context_help")
        self.help_texts[widget] = clean_context
        self._register_tooltip(widget, tooltip_text)

    def _register_help_entries(self) -> None:
        if self.theme_menu is not None:
            self._register_help(
                self.theme_menu,
                "Farbschema wählen (Theme = Farbstil).",
                "Farbschema wählen: Wähle ein Theme (Farbstil), um Kontrast und Farben anzupassen.",
            )
        if self.show_all_check is not None:
            self._register_help(
                self.show_all_check,
                "Zeigt alle Module (auch deaktivierte).",
                "Alle Module anzeigen: Zeigt auch deaktivierte Module, damit du sie prüfen kannst.",
            )
        if self.debug_check is not None:
            self._register_help(
                self.debug_check,
                "Zeigt technische Details (Debugging = Fehlersuche).",
                "Debug-Details: Zeigt technische Zusatzinfos (Debugging = Fehlersuche).",
            )
        if self.refresh_button is not None:
            self._register_help(
                self.refresh_button,
                "Aktualisiert die Modulübersicht.",
                "Übersicht aktualisieren: Lädt Module neu und prüft Fehler.",
            )
        if self.logout_button is not None:
            self._register_help(
                self.logout_button,
                "Sichert Daten und beendet das Tool.",
                "Abmelden: Erst wird eine Sicherung erstellt, danach wird sauber beendet.",
            )
        if self.diagnostics_button is not None:
            self._register_help(
                self.diagnostics_button,
                "Startet Tests und Codeprüfungen.",
                "Diagnose starten: Führt Tests und Codequalität (Linting/Format) aus.",
            )
        if self.main_window_button is not None:
            self._register_help(
                self.main_window_button,
                "Öffnet das Hauptfenster mit Modulraster.",
                "Hauptfenster öffnen: Zeigt ein 3x3-Modulraster mit Drag/Resize und Start/Stop.",
            )
        if self.scan_button is not None:
            self._register_help(
                self.scan_button,
                "Startet den System-Scan (Vorabprüfung).",
                "System-Scan: Prüft Dateien, Ordner und Rechte ohne Schreiben.",
            )
        if self.standards_button is not None:
            self._register_help(
                self.standards_button,
                "Zeigt die Standards (interne Regeln).",
                "Standards anzeigen: Zeigt die internen Regeln (Standards = Regeln).",
            )
        if self.logs_button is not None:
            self._register_help(
                self.logs_button,
                "Öffnet den Log-Ordner (Protokolle).",
                "Log-Ordner öffnen: Zeigt Protokolle (Logs), falls etwas schiefgeht.",
            )
        if self.export_button is not None:
            self._register_help(
                self.export_button,
                "Erstellt einen Teil-Export (ZIP).",
                "Selektiver Export: Erstellt ein ZIP mit ausgewählten Bereichen (z. B. Logs).",
            )
        if self.export_center_button is not None:
            self._register_help(
                self.export_center_button,
                "Exportiert JSON, TXT, PDF und ZIP.",
                "Export-Center: Erstellt Exporte (Ausgabedateien) in mehreren Formaten.",
            )
        if self.backup_button is not None:
            self._register_help(
                self.backup_button,
                "Erstellt ein vollständiges Backup (ZIP).",
                "Backup: Erstellt eine vollständige Sicherung in data/backups.",
            )
        if self.output_text is not None:
            self._register_help(
                self.output_text,
                "Hier stehen Module und Prüfergebnisse.",
                "Modulübersicht: Zeigt Module, Prüfungen und Hinweise in einfacher Sprache.",
            )
        if self.status_label is not None:
            self._register_help(
                self.status_label,
                "Zeigt Statusmeldungen (bereit, läuft, Fehler).",
                "Status: Zeigt ob das Tool bereit ist, arbeitet oder einen Fehler meldet.",
            )
        if self.drop_zone_label is not None:
            self._register_help(
                self.drop_zone_label,
                "Dateien/Module per Drag-and-Drop ablegen.",
                "Drag-and-Drop: Ziehe Dateien oder Module auf diese Fläche, um sie zu prüfen.",
            )

    def _focus_widget(self, widget) -> None:
        if widget is not None:
            widget.focus_set()

    def _toggle_show_all(self) -> None:
        self._set_show_all(not bool(self.show_all_var.get()), record_action=True)

    def _toggle_debug(self) -> None:
        self._set_debug(not bool(self.debug_var.get()), record_action=True)

    def _refresh_from_shortcut(self) -> None:
        self.request_refresh()

    def request_logout(self) -> None:
        if self.logout_running:
            self._set_status("Abmelden läuft bereits…", state="busy")
            return
        self.logout_running = True
        self._set_status("Abmelden: Sicherung wird vorbereitet…", state="busy")
        thread = threading.Thread(target=self._execute_logout, daemon=True)
        thread.start()

    def _execute_logout(self) -> None:
        report_lines = ["Abmelden: Sicherung und sauberes Schließen"]
        success = True
        if self.autosave_config and self.autosave_config.enabled:
            try:
                result = autosave_manager.create_autosave(
                    DEFAULT_DATA_ROOT, DEFAULT_LOG_ROOT, self.logger
                )
                report_lines.append(f"Erfolg: {result.summary}")
            except autosave_manager.AutosaveError as exc:
                success = False
                report_lines.extend(
                    [
                        "Fehler: Autosave fehlgeschlagen.",
                        f"Ursache: {exc}",
                        "Lösung: logs/autosave.log prüfen oder Safe-Mode nutzen.",
                    ]
                )
        else:
            report_lines.extend(
                [
                    "Hinweis: Autosave ist deaktiviert.",
                    (
                        "Lösung: In config/global_settings.json aktivieren, "
                        "wenn du Sicherungen willst."
                    ),
                ]
            )
        try:
            backup_config = backup_center.load_backup_config(
                self.module_config.resolve().parents[1] / "config" / "backup.json"
            )
            backup_state = DEFAULT_DATA_ROOT / "backup_state.json"
            backup_result = backup_center.create_backup(backup_config, backup_state)
            report_lines.append(f"Erfolg: {backup_result.summary}")
        except backup_center.BackupCenterError as exc:
            success = False
            report_lines.extend(
                [
                    "Fehler: Backup fehlgeschlagen.",
                    f"Ursache: {exc}",
                    "Lösung: config/backup.json prüfen und erneut versuchen.",
                ]
            )
        report = "\n".join(report_lines).rstrip() + "\n"
        self.root.after(0, lambda: self._finish_logout(report, success))

    def _finish_logout(self, report: str, success: bool) -> None:
        if report:
            self._append_output(report)
        status = "Abmelden abgeschlossen." if success else "Abmelden mit Problemen."
        self._set_status(status, state="success" if success else "error")
        self._cancel_autosave_job()
        self.root.after(200, self.root.destroy)

    def _cancel_autosave_job(self) -> None:
        if self.autosave_job is not None:
            try:
                self.root.after_cancel(self.autosave_job)
            except Exception:
                pass
            self.autosave_job = None

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

    def _record_action(
        self,
        name: str,
        undo_action,
        redo_action,
        metadata: dict | None = None,
    ) -> None:
        clean_name = _require_text(name, "action_name")
        meta = metadata if isinstance(metadata, dict) else {}
        self.undo_manager.record(
            UndoRedoAction(name=clean_name, undo=undo_action, redo=redo_action, metadata=meta)
        )

    def undo_action(self) -> None:
        try:
            action = self.undo_manager.undo()
        except UndoRedoError as exc:
            self._set_status(f"Undo nicht möglich: {exc}", state="error")
            return
        self._set_status(f"Undo: {action.name}", state="success")

    def redo_action(self) -> None:
        try:
            action = self.undo_manager.redo()
        except UndoRedoError as exc:
            self._set_status(f"Redo nicht möglich: {exc}", state="error")
            return
        self._set_status(f"Redo: {action.name}", state="success")

    def _set_theme(self, theme_name: str) -> None:
        clean_name = _require_text(theme_name, "theme_name")
        if clean_name not in self.gui_config.themes:
            raise GuiLauncherError("Unbekanntes Farbschema.")
        self.theme_var.set(clean_name)
        self.apply_theme(clean_name)

    def _on_theme_changed(self, theme_name: str) -> None:
        previous = self.current_theme
        target = _require_text(theme_name, "theme_name")
        if previous == target:
            return
        self._set_theme(target)
        self.current_theme = target
        self._record_action(
            f"Farbschema wechseln ({previous} → {target})",
            undo_action=lambda: self._restore_theme(previous),
            redo_action=lambda: self._restore_theme(target),
        )
        label = self.gui_config.themes[target].label
        self._set_status(f"Farbschema aktiv: {label}", state="success")

    def _restore_theme(self, theme_name: str) -> None:
        self._set_theme(theme_name)
        self.current_theme = theme_name

    def _set_show_all(self, value: bool, record_action: bool) -> None:
        previous = bool(self.show_all_var.get())
        self.show_all_var.set(bool(value))
        self.request_refresh()
        if record_action:
            self._record_action(
                "Alle Module anzeigen",
                undo_action=lambda: self._set_show_all(previous, record_action=False),
                redo_action=lambda: self._set_show_all(bool(value), record_action=False),
                metadata={"previous": previous, "current": bool(value)},
            )

    def _set_debug(self, value: bool, record_action: bool) -> None:
        previous = bool(self.debug_var.get())
        self.debug_var.set(bool(value))
        self.request_refresh()
        if record_action:
            self._record_action(
                "Debug-Details anzeigen",
                undo_action=lambda: self._set_debug(previous, record_action=False),
                redo_action=lambda: self._set_debug(bool(value), record_action=False),
                metadata={"previous": previous, "current": bool(value)},
            )

    def apply_theme(self, theme_name: str) -> None:
        clean_name = _require_text(theme_name, "theme_name")
        if clean_name not in self.gui_config.themes:
            raise GuiLauncherError("Unbekanntes Farbschema.")
        theme = self.gui_config.themes[clean_name]
        self.current_theme = clean_name

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
        self.tooltip_style = {
            "bg": theme.colors["button_background"],
            "fg": theme.colors["button_foreground"],
            "border": theme.colors["accent"],
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

    def _setup_autosave(self) -> None:
        try:
            config = autosave_manager.load_autosave_config(DEFAULT_SETTINGS_CONFIG)
        except autosave_manager.AutosaveError as exc:
            self.logger.error("Autosave: Konfiguration ungültig: %s", exc)
            return

        if not config.enabled:
            self.logger.info("Autosave: Deaktiviert.")
            return

        self.autosave_config = config
        self._schedule_autosave()

    def _schedule_autosave(self) -> None:
        if self.autosave_config is None:
            return
        autosave_manager.schedule_next_autosave(
            self.autosave_config.interval_minutes,
            self.root.after,
            self._run_autosave,
        )

    def _run_autosave(self) -> None:
        if self.autosave_config is None:
            return
        try:
            autosave_manager.create_autosave(DEFAULT_DATA_ROOT, DEFAULT_LOG_ROOT, self.logger)
        except autosave_manager.AutosaveError as exc:
            self.logger.error("Autosave fehlgeschlagen: %s", exc)
        finally:
            self._schedule_autosave()

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
            audit_report = end_audit.run_end_audit(root_dir)
            text = self._append_end_audit(text, audit_report)
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

    def open_main_window(self) -> None:
        import tkinter as tk

        self._set_status("Hauptfenster wird geöffnet…", state="busy")
        try:
            window = tk.Toplevel(self.root)
            main_window.MainWindow(
                window,
                module_config=self.module_config,
                gui_config=self.gui_config,
                debug=self.debug,
                theme_name=self.current_theme,
            )
        except (main_window.MainWindowError, ModuleManagerError) as exc:
            self.logger.error("Hauptfenster konnte nicht geöffnet werden: %s", exc)
            self._show_error(str(exc))
            self._set_status("Hauptfenster konnte nicht geöffnet werden.", state="error")
        else:
            self._set_status("Hauptfenster geöffnet.", state="success")

    def start_system_scan(self) -> None:
        script_path = self.module_config.resolve().parents[1] / "scripts" / "system_scan.sh"
        self._run_maintenance_task("System-Scan", ["bash", str(script_path)])

    def show_standards(self) -> None:
        script_path = self.module_config.resolve().parents[1] / "scripts" / "show_standards.sh"
        self._run_maintenance_task("Standards-Liste", ["bash", str(script_path), "--list"])

    def open_logs(self) -> None:
        logs_path = self.module_config.resolve().parents[1] / "logs"
        self._run_maintenance_task("Log-Ordner öffnen", ["xdg-open", str(logs_path)])

    def start_selective_export(self) -> None:
        script_path = self.module_config.resolve().parents[1] / "system" / "selective_exporter.py"
        self._run_maintenance_task(
            "Selektiver Export",
            ["python", str(script_path), "--preset", "support_pack"],
        )

    def start_export_center(self) -> None:
        script_path = self.module_config.resolve().parents[1] / "system" / "export_center.py"
        self._run_maintenance_task("Export-Center", ["python", str(script_path)])

    def start_backup(self) -> None:
        script_path = self.module_config.resolve().parents[1] / "system" / "backup_center.py"
        self._run_maintenance_task("Backup", ["python", str(script_path)])

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
        if command and command[0] == "python":
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
        for button in (
            self.scan_button,
            self.standards_button,
            self.logs_button,
            self.export_button,
            self.export_center_button,
            self.backup_button,
        ):
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

    def _append_end_audit(self, text: str, report: end_audit.AuditReport) -> str:
        if not isinstance(text, str) or not text.strip():
            raise GuiLauncherError("Ausgabetext ist leer.")
        lines = [text.rstrip(), "", "End-Audit (Release-Status):"]
        lines.append(f"Status: {report.status}")
        lines.append(f"Offene Aufgaben: {report.open_tasks}")
        if report.issues:
            lines.append("Hinweise:")
            for issue in report.issues:
                lines.append(f"- {issue.message} (Stufe: {issue.severity})")
        else:
            lines.append("Keine offenen Hinweise. Release-Status ist grün.")
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
