from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from apply_gate7_launcher_controller import transform


def launcher_source() -> str:
    return (Path(__file__).resolve().parents[1] / "system" / "launcher_gui.py").read_text(
        encoding="utf-8"
    )


def test_gate7_codemod_is_idempotent_and_syntax_valid():
    first = transform(launcher_source())
    second = transform(first)

    assert first == second
    ast.parse(first)


def test_gate7_installs_authoritative_controller_and_debouncer():
    transformed = transform(launcher_source())

    assert "from launcher_controller import (" in transformed
    assert transformed.count("from launcher_controller import (") == 1
    assert "self.controller = LauncherController(" in transformed
    assert "self.refresh_debouncer = RefreshDebouncer(" in transformed
    assert "self.refresh_job = None" not in transformed
    assert "self.current_theme = self.controller.state.theme_name" in transformed
    assert "self.current_help_text = self.controller.state.help_text" in transformed


def test_gate7_uses_data_driven_shortcut_and_help_views():
    transformed = transform(launcher_source())

    assert "for spec in build_shortcut_specs():" in transformed
    assert "for entry in build_help_entries():" in transformed
    assert '"toggle_show_all": self._toggle_show_all' in transformed
    assert '"announce_help": self._announce_context_help' in transformed
    assert '"autostart_check": self.autostart_check' in transformed
    assert '"drop_zone_label": self.drop_zone_label' in transformed
    assert 'self.root.bind_all("<Alt-a>"' not in transformed


def test_gate7_refresh_and_filters_use_controller_state():
    transformed = transform(launcher_source())

    assert "self.refresh_debouncer.request()" in transformed
    assert "show_all = self.controller.state.show_all" in transformed
    assert "debug = self.controller.state.debug" in transformed
    assert "change = self.controller.set_show_all(bool(value))" in transformed
    assert "change = self.controller.set_debug(bool(value))" in transformed
    assert transformed.count("if not change.changed:") >= 2
    assert "self.debug = bool(change.current)" in transformed


def test_gate7_routes_theme_and_history_through_controller():
    transformed = transform(launcher_source())

    assert "change = self.controller.set_theme(theme_name, self.gui_config.themes)" in transformed
    assert "record_state_change(self.undo_manager, change, apply_value)" in transformed
    assert "self.controller.state.theme_name == target" in transformed
    assert "UndoRedoAction(" not in transformed
    assert "metadata={\"previous\"" not in transformed


def test_gate7_status_and_help_are_testable_view_transitions():
    transformed = transform(launcher_source())

    assert "view = build_status_view(message, state)" in transformed
    assert "self.status_var.set(view.display_text)" in transformed
    assert "self.root.configure(cursor=view.cursor)" in transformed
    assert "change = self.controller.set_help(text)" in transformed
    assert "text = self.controller.state.help_text" in transformed


def test_gate7_keeps_previous_hardened_boundaries_untouched():
    transformed = transform(launcher_source())

    for marker in (
        "self.task_runner = TaskRunner(self.root.after)",
        'self.task_runner.start(\n                "diagnostics"',
        'self.task_runner.start(\n                "maintenance"',
        'self.task_runner.start(\n                "shutdown"',
        "self.autosave_session = AutosaveSession(",
        "complete_shutdown(",
        "self.autostart_manager = AutostartManager(",
        "return format_diagnostics_report(result)",
        "return append_file_status(text, report)",
        "apply_theme_tree(self.root, theme, button_font=self.button_font)",
    ):
        assert marker in transformed
