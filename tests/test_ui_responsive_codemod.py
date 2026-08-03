from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from apply_ui_responsive_acceptance import transform_launcher, transform_main

ROOT = Path(__file__).resolve().parents[1]


def launcher_source() -> str:
    return (ROOT / "system" / "launcher_gui.py").read_text(encoding="utf-8")


def main_source() -> str:
    return (ROOT / "system" / "main_window.py").read_text(encoding="utf-8")


def test_responsive_codemod_is_idempotent_and_syntax_valid():
    launcher_first = transform_launcher(launcher_source())
    main_first = transform_main(main_source())

    assert transform_launcher(launcher_first) == launcher_first
    assert transform_main(main_first) == main_first
    ast.parse(launcher_first)
    ast.parse(main_first)


def test_launcher_integrates_three_responsive_modes():
    transformed = transform_launcher(launcher_source())

    assert "from ui_responsive import resolve_launcher_layout" in transformed
    assert "self.theme_label = tk.Label(" in transformed
    assert 'if layout.mode == "wide":' in transformed
    assert 'elif layout.mode == "medium":' in transformed
    assert "self.diagnostics_button: (4, 0, 1, \"ew\")" in transformed
    assert "self.diagnostics_button: (4, 0, 2, \"ew\")" in transformed
    assert "layout.developer_columns == 4" in transformed
    assert "layout.help_columns == 2" in transformed


def test_main_window_reflows_and_honors_tablet_minimum():
    transformed = transform_main(main_source())

    assert "MAIN_WINDOW_MIN_WIDTH" in transformed
    assert "MAIN_WINDOW_MIN_HEIGHT" in transformed
    assert "self._layout_size: tuple[int, int] | None = None" in transformed
    assert "grid = resolve_workspace_grid(" in transformed
    assert "self._layout_size == layout_size" in transformed
    assert "widget.description.configure(wraplength=max(rect.width - 16, 120))" in transformed
    assert "self.root.minsize(960, 680)" not in transformed


def test_touch_targets_are_enlarged_without_changing_actions():
    transformed = transform_main(main_source())

    assert "menu.configure(padx=6, pady=8, takefocus=1)" in transformed
    assert "button.configure(pady=7, takefocus=1)" in transformed
    assert "command=self._handle_activate" in transformed
    assert "command=self._handle_deactivate" in transformed


def test_previous_hardened_boundaries_remain_present():
    launcher = transform_launcher(launcher_source())
    main = transform_main(main_source())

    for marker in (
        "self.controller = LauncherController(",
        "self.task_runner = TaskRunner(self.root.after)",
        "self.autosave_session = AutosaveSession(",
        "complete_shutdown(",
        "apply_theme_tree(self.root, theme, button_font=self.button_font)",
    ):
        assert marker in launcher
    for marker in (
        "perform_module_action(",
        "prepare_close(self.manager)",
        "resolve_card_presentation(widget.state)",
        "has_collision(candidate",
    ):
        assert marker in main
