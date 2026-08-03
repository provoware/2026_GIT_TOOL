#!/usr/bin/env python3
"""Integriert Gate 7 kontrolliert in den produktiven Launcher."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "system" / "launcher_gui.py"

CONTROLLER_IMPORT = '''from launcher_controller import (
    LauncherController,
    LauncherControllerError,
    RefreshDebouncer,
    StateChange,
    build_help_entries,
    build_shortcut_specs,
    build_status_view,
    record_state_change,
)
'''

METHODS = {
    "_bind_accessibility_shortcuts": '''    def _bind_accessibility_shortcuts(self) -> None:
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
            )''',
    "_set_context_help": '''    def _set_context_help(self, text: str) -> None:
        try:
            change = self.controller.set_help(text)
        except LauncherControllerError as exc:
            raise GuiLauncherError(str(exc)) from exc
        self.current_help_text = str(change.current)
        if self.context_help_label is not None:
            self.context_help_label.configure(text=self.current_help_text)''',
    "_announce_context_help": '''    def _announce_context_help(self) -> None:
        text = self.controller.state.help_text
        if not text.strip():
            return
        self._set_status(f"Hilfe: {text}", state="success")''',
    "_register_help_entries": '''    def _register_help_entries(self) -> None:
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
                self._register_help(widget, entry.tooltip, entry.context)''',
    "request_refresh": '''    def request_refresh(self) -> None:
        self._set_status("Aktualisierung wird vorbereitet…", state="busy")
        try:
            self.refresh_debouncer.request()
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Aktualisierung konnte nicht geplant werden: %s", exc)
            self._set_status("Aktualisierung konnte nicht geplant werden.", state="error")''',
    "_record_action": '''    def _record_action(self, change: StateChange, apply_value) -> None:
        try:
            record_state_change(self.undo_manager, change, apply_value)
        except (LauncherControllerError, UndoRedoError) as exc:
            raise GuiLauncherError(str(exc)) from exc''',
    "_set_theme": '''    def _set_theme(self, theme_name: str) -> StateChange:
        try:
            change = self.controller.set_theme(theme_name, self.gui_config.themes)
        except LauncherControllerError as exc:
            raise GuiLauncherError(str(exc)) from exc
        target = str(change.current)
        if self.theme_var is not None:
            self.theme_var.set(target)
        self.apply_theme(target)
        self.current_theme = target
        return change''',
    "_on_theme_changed": '''    def _on_theme_changed(self, theme_name: str) -> None:
        target = _require_text(theme_name, "theme_name")
        if self.controller.state.theme_name == target:
            return
        change = self._set_theme(target)
        self._record_action(
            change,
            lambda value: self._restore_theme(str(value)),
        )
        label = self.gui_config.themes[target].label
        self._set_status(f"Farbschema aktiv: {label}", state="success")''',
    "_restore_theme": '''    def _restore_theme(self, theme_name: str) -> None:
        self._set_theme(theme_name)''',
    "_set_show_all": '''    def _set_show_all(self, value: bool, record_action: bool) -> None:
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
            )''',
    "_set_debug": '''    def _set_debug(self, value: bool, record_action: bool) -> None:
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
            )''',
    "refresh": '''    def refresh(self) -> None:
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

        self._set_output(text)''',
    "_set_status": '''    def _set_status(self, message: str, state: str = "success") -> None:
        try:
            view = build_status_view(message, state)
        except LauncherControllerError as exc:
            raise GuiLauncherError(str(exc)) from exc
        if self.status_var is not None:
            self.status_var.set(view.display_text)
        self._apply_status_style(view.state)
        self.root.configure(cursor=view.cursor)
        self.root.update_idletasks()''',
}


def _replace_methods(source: str, replacements: Mapping[str, str]) -> str:
    tree = ast.parse(source)
    target_class = next(
        (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "LauncherGui"),
        None,
    )
    if target_class is None:
        raise RuntimeError("Klasse LauncherGui fehlt.")
    methods = {
        node.name: node
        for node in target_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    missing = sorted(set(replacements) - set(methods))
    if missing:
        raise RuntimeError(f"Launcher-Methoden fehlen: {', '.join(missing)}")

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


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    if new in source:
        return source
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: erwartete Struktur nicht eindeutig ({count}).")
    return source.replace(old, new, 1)


def transform(source: str) -> str:
    result = source
    if CONTROLLER_IMPORT not in result:
        anchor = "from module_manager import ModuleManagerError\n"
        if anchor not in result:
            raise RuntimeError("Controller-Importanker fehlt.")
        result = result.replace(anchor, CONTROLLER_IMPORT + anchor, 1)

    result = _replace_once(
        result,
        "        self.task_runner = TaskRunner(self.root.after)\n        self.refresh_job = None\n        self.refresh_debounce_ms = gui_config.refresh_debounce_ms\n",
        "        self.task_runner = TaskRunner(self.root.after)\n        self.refresh_debounce_ms = gui_config.refresh_debounce_ms\n",
        "Refresh-Initialisierung",
    )
    result = _replace_once(
        result,
        "        self.current_help_text = self.context_help_default\n        self.help_texts: Dict[object, str] = {}\n",
        "        self.controller = LauncherController(\n            show_all=show_all,\n            debug=debug,\n            theme_name=self.gui_config.default_theme,\n            help_text=self.context_help_default,\n        )\n        self.refresh_debouncer = RefreshDebouncer(\n            self.root.after,\n            self.root.after_cancel,\n            self.refresh_debounce_ms,\n            self.refresh,\n        )\n        self.current_help_text = self.controller.state.help_text\n        self.help_texts: Dict[object, str] = {}\n",
        "Controller-Initialisierung",
    )
    result = _replace_once(
        result,
        "        self.current_theme = self.gui_config.default_theme\n",
        "        self.current_theme = self.controller.state.theme_name\n",
        "Theme-Initialisierung",
    )
    result = _replace_once(
        result,
        "        self.theme_var = tk.StringVar(value=self.gui_config.default_theme)\n",
        "        self.theme_var = tk.StringVar(value=self.controller.state.theme_name)\n",
        "Theme-View",
    )
    result = _replace_once(
        result,
        "        self.show_all_var = tk.BooleanVar(value=show_all)\n",
        "        self.show_all_var = tk.BooleanVar(value=self.controller.state.show_all)\n",
        "Show-all-View",
    )
    result = _replace_once(
        result,
        "        self.debug_var = tk.BooleanVar(value=self.debug)\n",
        "        self.debug_var = tk.BooleanVar(value=self.controller.state.debug)\n",
        "Debug-View",
    )
    result = _replace_once(
        result,
        "        self.apply_theme(self.gui_config.default_theme)\n",
        "        self.apply_theme(self.controller.state.theme_name)\n",
        "Initiales Theme",
    )

    result = _replace_methods(result, METHODS)
    ast.parse(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    source = args.path.read_text(encoding="utf-8")
    transformed = transform(source)
    changed = transformed != source
    if changed and not args.check:
        args.path.write_text(transformed, encoding="utf-8")
    if args.check and changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
