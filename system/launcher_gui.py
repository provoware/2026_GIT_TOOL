#!/usr/bin/env python3
"""GUI-Launcher: zeigt Module in einer barrierefreien Startübersicht an."""

from __future__ import annotations

import argparse
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
from launcher_reports import (
    append_end_audit,
    append_error_simulation,
    append_file_status,
    append_selftests,
    format_diagnostics_report,
    format_maintenance_report,
)
from launcher_controller import (
    LauncherController,
    LauncherControllerError,
    RefreshDebouncer,
    StateChange,
    build_help_entries,
    build_shortcut_specs,
    build_status_view,
    record_state_change,
)
from module_manager import ModuleManagerError
from ui_responsive import resolve_launcher_help_text, resolve_launcher_layout
from ui_theme_adapter import (
    UiThemeError,
    apply_theme_tree,
    apply_widget_style,
    build_status_palette,
    build_tooltip_style,
    resolve_contrast_theme,
    resolve_theme,
)
from autostart_manager import AutostartError, AutostartManager
from session_lifecycle import (
    AutosaveSession,
    ShutdownOutcome,
    complete_shutdown,
    run_shutdown_sequence,
)
from task_runner import (
    CommandResult,
    CommandValidationError,
    TaskOutcome,
    TaskRunner,
    TaskRunnerError,
    execute_command,
    validate_command,
)
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
        self.autostart_var = None
        self.output_text = None
        self.theme_menu = None
        self.theme_label = None
        self.show_all_check = None
        self.debug_check = None
        self.autostart_check = None
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
        self.task_runner = TaskRunner(self.root.after)
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
        self.controller = LauncherController(
            show_all=show_all,
            debug=debug,
            theme_name=self.gui_config.default_theme,
            help_text=self.context_help_default,
        )
        self.refresh_debouncer = RefreshDebouncer(
            self.root.after,
            self.root.after_cancel,
            self.refresh_debounce_ms,
            self.refresh,
        )
        self.current_help_text = self.controller.state.help_text
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
        project_root = self.module_config.resolve().parents[1]
        self.autostart_manager = AutostartManager(
            project_root / "scripts" / "start.sh"
        )
        self.autosave_config: autosave_manager.AutosaveConfig | None = None
        self.autosave_session = AutosaveSession(
            self.root.after,
            self.root.after_cancel,
            self._run_autosave,
        )
        self.undo_manager = UndoRedoManager(limit=50)
        self.drag_drop_manager = None
        self.current_theme = self.controller.state.theme_name

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

        self.theme_label = tk.Label(
            controls, text=f"{ICON_SET['theme']} Farbschema:"
        )
        self.theme_label.grid(row=0, column=0, sticky="w")
        self.theme_var = tk.StringVar(value=self.controller.state.theme_name)
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

        self.show_all_var = tk.BooleanVar(value=self.controller.state.show_all)
        self.show_all_check = tk.Checkbutton(
            controls,
            text="Alle Module anzeigen (inkl. deaktiviert)",
            variable=self.show_all_var,
            command=lambda: self._set_show_all(
                bool(self.show_all_var.get()), record_action=True
            ),
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

        self.debug_var = tk.BooleanVar(value=self.controller.state.debug)
        self.debug_check = tk.Checkbutton(
            controls,
            text="Debug-Details anzeigen",
            variable=self.debug_var,
            command=lambda: self._set_debug(
                bool(self.debug_var.get()), record_action=True
            ),
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

        self.autostart_var = tk.BooleanVar(value=self.autostart_manager.is_enabled())
        self.autostart_check = tk.Checkbutton(
            controls,
            text="Beim Hochfahren automatisch starten",
            variable=self.autostart_var,
            command=self._toggle_autostart,
        )
        if self.button_font is not None:
            self.autostart_check.configure(font=self.button_font)
        self.autostart_check.configure(
            padx=self.layout.field_padx,
            pady=self.layout.field_pady,
            takefocus=1,
            underline=0,
        )
        self.autostart_check.grid(
            row=2,
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
        self.apply_theme(self.controller.state.theme_name)
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
        actions = {
            "toggle_show_all": self._toggle_show_all,
            "toggle_debug": self._toggle_debug,
            "refresh": self._refresh_from_shortcut,
            "focus_theme": lambda: self._focus_widget(self.theme_menu),
            "toggle_contrast": self._toggle_contrast_theme,
            "diagnostics": self.start_diagnostics,
            "main_window": self.open_main_window,
            "system_scan": self.start_system_scan,
            "standards": self.show_standards,
            "logs": self.open_logs,
            "selective_export": self.start_selective_export,
            "export_center": self.start_export_center,
            "backup": self.start_backup,
            "logout": self.request_logout,
            "undo": self.undo_action,
            "redo": self.redo_action,
            "announce_help": self._announce_context_help,
        }
        for spec in build_shortcut_specs():
            callback = actions.get(spec.action)
            if callback is None:
                raise GuiLauncherError(f"Shortcut-Aktion fehlt: {spec.action}")
            self.root.bind_all(
                spec.sequence,
                lambda _event, action=callback: action(),
            )

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
            self.status_label.configure(wraplength=full_width, justify="left")

    def _update_layout_by_width(self) -> None:
        width = max(self.root.winfo_width(), 1)
        layout = resolve_launcher_layout(width)
        if self.help_label is not None:
            self.help_label.configure(text=resolve_launcher_help_text(width))
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
                    self.show_all_check: (1, 0, 1, "w"),
                    self.debug_check: (1, 1, 1, "w"),
                    self.autostart_check: (2, 0, 2, "w"),
                    self.diagnostics_button: (3, 0, 1, "ew"),
                    self.refresh_button: (3, 1, 1, "ew"),
                    self.main_window_button: (4, 0, 1, "ew"),
                    self.logout_button: (4, 1, 1, "ew"),
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
            elif layout.developer_columns == 3:
                positions = ((1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2))
                hint_span = 3
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
        try:
            change = self.controller.set_help(text)
        except LauncherControllerError as exc:
            raise GuiLauncherError(str(exc)) from exc
        self.current_help_text = str(change.current)
        if self.context_help_label is not None:
            self.context_help_label.configure(text=self.current_help_text)

    def _announce_context_help(self) -> None:
        text = self.controller.state.help_text
        if not text.strip():
            return
        self._set_status(f"Hilfe: {text}", state="success")

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
        widgets = {
            "theme_menu": self.theme_menu,
            "show_all_check": self.show_all_check,
            "debug_check": self.debug_check,
            "autostart_check": self.autostart_check,
            "refresh_button": self.refresh_button,
            "logout_button": self.logout_button,
            "diagnostics_button": self.diagnostics_button,
            "main_window_button": self.main_window_button,
            "scan_button": self.scan_button,
            "standards_button": self.standards_button,
            "logs_button": self.logs_button,
            "export_button": self.export_button,
            "export_center_button": self.export_center_button,
            "backup_button": self.backup_button,
            "output_text": self.output_text,
            "status_label": self.status_label,
            "drop_zone_label": self.drop_zone_label,
        }
        for entry in build_help_entries():
            widget = widgets.get(entry.key)
            if widget is not None:
                self._register_help(widget, entry.tooltip, entry.context)

    def _focus_widget(self, widget) -> None:
        if widget is not None:
            widget.focus_set()

    def _toggle_show_all(self) -> None:
        self._set_show_all(not bool(self.show_all_var.get()), record_action=True)

    def _toggle_debug(self) -> None:
        self._set_debug(not bool(self.debug_var.get()), record_action=True)

    def _toggle_autostart(self) -> None:
        if self.autostart_var is None:
            raise GuiLauncherError("Autostart-Auswahl ist nicht verfügbar.")
        enabled = bool(self.autostart_var.get())
        try:
            active = self.autostart_manager.set_enabled(enabled)
        except AutostartError as exc:
            self.autostart_var.set(self.autostart_manager.is_enabled())
            self._append_output(f"Autostart:\nFehler: {exc}\n")
            self._set_status("Autostart konnte nicht geändert werden.", state="error")
            return
        label = "aktiviert" if active else "deaktiviert"
        self._set_status(f"Autostart beim Hochfahren: {label}.", state="success")

    def _refresh_from_shortcut(self) -> None:
        self.request_refresh()

    def request_logout(self) -> None:
        if self.task_runner.is_running("shutdown"):
            self._set_status("Abmelden läuft bereits…", state="busy")
            return
        if self.logout_button is not None:
            self.logout_button.configure(state="disabled")
        self._set_status("Abmelden: Sicherung wird vorbereitet…", state="busy")
        try:
            started = self.task_runner.start(
                "shutdown",
                self._execute_logout,
                self._finish_logout,
            )
        except TaskRunnerError as exc:
            if self.logout_button is not None:
                self.logout_button.configure(state="normal")
            self._set_status(f"Abmelden konnte nicht starten: {exc}", state="error")
            return
        if not started:
            if self.logout_button is not None:
                self.logout_button.configure(state="normal")
            self._set_status("Abmelden läuft bereits…", state="busy")

    def _execute_logout(self) -> ShutdownOutcome:
        project_root = self.module_config.resolve().parents[1]
        return run_shutdown_sequence(
            autosave_config=self.autosave_config,
            data_root=DEFAULT_DATA_ROOT,
            logs_root=DEFAULT_LOG_ROOT,
            logger=self.logger,
            backup_config_path=project_root / "config" / "backup.json",
            backup_state_path=DEFAULT_DATA_ROOT / "backup_state.json",
        )

    def _finish_logout(self, outcome: TaskOutcome[ShutdownOutcome]) -> None:
        if self.logout_button is not None:
            self.logout_button.configure(state="normal")
        if outcome.error is not None:
            result = ShutdownOutcome(
                report=(
                    "Abmelden: Sicherung und sauberes Schließen\n"
                    "Fehler: Shutdown konnte nicht vollständig ausgeführt werden.\n"
                    f"Ursache: {outcome.error}\n"
                ),
                success=False,
            )
        else:
            result = outcome.value
        if not isinstance(result, ShutdownOutcome):
            raise GuiLauncherError("Shutdown-Ergebnis ist ungültig.")
        complete_shutdown(
            result,
            append_report=self._append_output,
            set_status=lambda message, state: self._set_status(message, state=state),
            cancel_autosave=self._cancel_autosave_job,
            schedule=self.root.after,
            destroy=self.root.destroy,
        )

    def _cancel_autosave_job(self) -> None:
        self.autosave_session.cancel()

    def _resolve_contrast_theme(self) -> Optional[str]:
        try:
            return resolve_contrast_theme(self.gui_config)
        except UiThemeError as exc:
            raise GuiLauncherError(str(exc)) from exc

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
        self._set_status("Aktualisierung wird vorbereitet…", state="busy")
        try:
            self.refresh_debouncer.request()
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Aktualisierung konnte nicht geplant werden: %s", exc)
            self._set_status("Aktualisierung konnte nicht geplant werden.", state="error")

    def _record_action(self, change: StateChange, apply_value) -> None:
        try:
            record_state_change(self.undo_manager, change, apply_value)
        except (LauncherControllerError, UndoRedoError) as exc:
            raise GuiLauncherError(str(exc)) from exc

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

    def _set_theme(self, theme_name: str) -> StateChange:
        try:
            change = self.controller.set_theme(theme_name, self.gui_config.themes)
        except LauncherControllerError as exc:
            raise GuiLauncherError(str(exc)) from exc
        target = str(change.current)
        if self.theme_var is not None:
            self.theme_var.set(target)
        self.apply_theme(target)
        self.current_theme = target
        return change

    def _on_theme_changed(self, theme_name: str) -> None:
        target = _require_text(theme_name, "theme_name")
        if self.controller.state.theme_name == target:
            return
        change = self._set_theme(target)
        self._record_action(
            change,
            lambda value: self._restore_theme(str(value)),
        )
        label = self.gui_config.themes[target].label
        self._set_status(f"Farbschema aktiv: {label}", state="success")

    def _restore_theme(self, theme_name: str) -> None:
        self._set_theme(theme_name)

    def _set_show_all(self, value: bool, record_action: bool) -> None:
        try:
            change = self.controller.set_show_all(bool(value))
        except LauncherControllerError as exc:
            raise GuiLauncherError(str(exc)) from exc
        if self.show_all_var is not None:
            self.show_all_var.set(bool(change.current))
        if not change.changed:
            return
        self.request_refresh()
        if record_action:
            self._record_action(
                change,
                lambda target: self._set_show_all(bool(target), record_action=False),
            )

    def _set_debug(self, value: bool, record_action: bool) -> None:
        try:
            change = self.controller.set_debug(bool(value))
        except LauncherControllerError as exc:
            raise GuiLauncherError(str(exc)) from exc
        self.debug = bool(change.current)
        if self.debug_var is not None:
            self.debug_var.set(self.debug)
        if not change.changed:
            return
        self.request_refresh()
        if record_action:
            self._record_action(
                change,
                lambda target: self._set_debug(bool(target), record_action=False),
            )

    def apply_theme(self, theme_name: str) -> None:
        clean_name = _require_text(theme_name, "theme_name")
        try:
            theme = resolve_theme(self.gui_config, clean_name, strict=True)
        except UiThemeError as exc:
            raise GuiLauncherError(str(exc)) from exc
        self.current_theme = theme.name
        self.status_palette = build_status_palette(theme)
        self.tooltip_style = build_tooltip_style(theme)
        apply_theme_tree(self.root, theme, button_font=self.button_font)
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
            raise GuiLauncherError(str(exc)) from exc

    def _setup_autosave(self) -> None:
        try:
            config = autosave_manager.load_autosave_config(DEFAULT_SETTINGS_CONFIG)
        except autosave_manager.AutosaveError as exc:
            self.logger.error("Autosave: Konfiguration ungültig: %s", exc)
            return
        self.autosave_config = config
        if not config.enabled:
            self.logger.info("Autosave: Deaktiviert.")
            return
        self._schedule_autosave()

    def _schedule_autosave(self) -> None:
        if self.autosave_config is None:
            return
        self.autosave_session.start(self.autosave_config)

    def _run_autosave(self) -> None:
        if self.autosave_config is None:
            return
        try:
            autosave_manager.create_autosave(DEFAULT_DATA_ROOT, DEFAULT_LOG_ROOT, self.logger)
        except autosave_manager.AutosaveError as exc:
            self.logger.error("Autosave fehlgeschlagen: %s", exc)

    def refresh(self) -> None:
        show_all = self.controller.state.show_all
        debug = self.controller.state.debug
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
        if self.task_runner.is_running("diagnostics"):
            self._set_status("Diagnose läuft bereits…", state="busy")
            return
        if self.diagnostics_button is not None:
            self.diagnostics_button.configure(state="disabled")
        self._set_status("Diagnose wird gestartet…", state="busy")
        try:
            started = self.task_runner.start(
                "diagnostics",
                self._run_diagnostics,
                self._finish_diagnostics,
            )
        except TaskRunnerError as exc:
            if self.diagnostics_button is not None:
                self.diagnostics_button.configure(state="normal")
            self._set_status(f"Diagnose konnte nicht starten: {exc}", state="error")
            return
        if not started:
            if self.diagnostics_button is not None:
                self.diagnostics_button.configure(state="normal")
            self._set_status("Diagnose läuft bereits…", state="busy")

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
        try:
            clean_command = validate_command(command)
        except CommandValidationError as exc:
            self._set_status(exc.status_message, state="error")
            self._append_output(f"{clean_title}:\nFehler: {exc}\n")
            return
        if self.task_runner.is_running("maintenance"):
            self._set_status("Wartung läuft bereits…", state="busy")
            return
        self._set_maintenance_buttons("disabled")
        self._set_status(f"{clean_title} läuft…", state="busy")
        try:
            started = self.task_runner.start(
                "maintenance",
                lambda: self._execute_maintenance(clean_command),
                lambda outcome: self._finish_maintenance(clean_title, outcome),
            )
        except TaskRunnerError as exc:
            self._set_maintenance_buttons("normal")
            self._append_output(
                f"{clean_title}:\nFehler: {exc}\n"
                "Lösung: Bitte das Skript prüfen und erneut versuchen.\n"
            )
            self._set_status(f"{clean_title} konnte nicht starten.", state="error")
            return
        if not started:
            self._set_maintenance_buttons("normal")
            self._set_status("Wartung läuft bereits…", state="busy")

    def _execute_maintenance(self, command: List[str]) -> CommandResult:
        return execute_command(command)

    def _finish_maintenance(
        self,
        title: str,
        outcome: TaskOutcome[CommandResult],
    ) -> None:
        self._set_maintenance_buttons("normal")
        if outcome.error is not None:
            status = "error"
            report = (
                f"{title}:\n"
                f"Fehler: {outcome.error}\n"
                "Lösung: Bitte das Skript prüfen und erneut versuchen.\n"
            )
        else:
            result = outcome.value
            if not isinstance(result, CommandResult):
                raise GuiLauncherError("Wartungs-Ergebnis ist ungültig.")
            status = "success" if result.return_code == 0 else "error"
            report = self._format_maintenance_report(
                title,
                result.command,
                result.output,
                result.return_code,
            )
        self._append_output(report)
        if status == "success":
            self._set_status(f"{title} abgeschlossen.", state="success")
        else:
            self._set_status(f"{title} mit Problemen.", state="error")

    def _format_maintenance_report(
        self, title: str, command: List[str], output: str, return_code: int
    ) -> str:
        return format_maintenance_report(title, command, output, return_code)

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

    def _run_diagnostics(self) -> diagnostics_runner.DiagnosticsResult:
        script_path = self.module_config.resolve().parents[1] / "scripts" / "run_tests.sh"
        try:
            return diagnostics_runner.run_diagnostics(script_path)
        except diagnostics_runner.DiagnosticsError as exc:
            return diagnostics_runner.DiagnosticsResult(
                status="error",
                output=f"Diagnose fehlgeschlagen: {exc}",
                exit_code=2,
                duration_seconds=0.0,
                command=["bash", str(script_path)],
            )

    def _finish_diagnostics(
        self,
        outcome: TaskOutcome[diagnostics_runner.DiagnosticsResult],
    ) -> None:
        if self.diagnostics_button is not None:
            self.diagnostics_button.configure(state="normal")
        if outcome.error is not None:
            script_path = self.module_config.resolve().parents[1] / "scripts" / "run_tests.sh"
            result = diagnostics_runner.DiagnosticsResult(
                status="error",
                output=f"Diagnose fehlgeschlagen: {outcome.error}",
                exit_code=2,
                duration_seconds=0.0,
                command=["bash", str(script_path)],
            )
        else:
            result = outcome.value
        if not isinstance(result, diagnostics_runner.DiagnosticsResult):
            raise GuiLauncherError("Diagnose-Ergebnis ist ungültig.")
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
        return format_diagnostics_report(result)

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
        try:
            view = build_status_view(message, state)
        except LauncherControllerError as exc:
            raise GuiLauncherError(str(exc)) from exc
        if self.status_var is not None:
            self.status_var.set(view.display_text)
        self._apply_status_style(view.state)
        self.root.configure(cursor=view.cursor)
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
        return append_file_status(text, report)

    def _append_end_audit(self, text: str, report: end_audit.AuditReport) -> str:
        return append_end_audit(text, report)

    def _append_selftests(self, text: str, results: List[module_selftests.SelftestResult]) -> str:
        return append_selftests(text, results)

    def _append_error_simulation(
        self, text: str, results: List[error_simulation.SimulationResult]
    ) -> str:
        return append_error_simulation(text, results)


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
