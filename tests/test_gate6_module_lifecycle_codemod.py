from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from apply_gate6_module_lifecycle import transform


def source_text() -> str:
    return (Path(__file__).resolve().parents[1] / "system" / "main_window.py").read_text(
        encoding="utf-8"
    )


def test_gate6_codemod_is_idempotent_and_syntax_valid():
    first = transform(source_text())
    second = transform(first)

    assert first == second
    ast.parse(first)


def test_gate6_uses_authoritative_manager_state_for_cards():
    transformed = transform(source_text())

    assert "from module_lifecycle import (" in transformed
    assert "def apply_presentation(" in transformed
    assert "perform_module_action(" in transformed
    assert "def _apply_action_outcome(" in transformed
    assert "def _sync_widget_state(" in transformed
    assert "def _sync_all_widgets(" in transformed
    assert "self._apply_action_result(widget, result, active=True)" not in transformed
    assert "def _apply_action_result(" not in transformed
    assert 'state="normal" if presentation.activate_enabled else "disabled"' in transformed
    assert 'state="normal" if presentation.deactivate_enabled else "disabled"' in transformed


def test_gate6_close_policy_blocks_destroy_until_deactivation_is_safe():
    transformed = transform(source_text())

    assert "decision = prepare_close(self.manager)" in transformed
    assert "self._sync_all_widgets()" in transformed
    assert "if decision.allow_close:" in transformed
    assert "self.root.destroy()" in transformed
    assert "self.manager.deactivate_all()\n        self.root.destroy()" not in transformed


def test_gate6_theme_change_resynchronizes_without_replacing_gate3_methods():
    transformed = transform(source_text())

    assert 'command=lambda _value: self._apply_theme_and_sync(),' in transformed
    assert "def _apply_theme_and_sync(self) -> None:" in transformed
    assert "def _theme_colors(self) -> Dict[str, str]:" in transformed
    assert "apply_theme_tree(self.root, theme)" in transformed
    assert "apply_module_card_theme(self, theme)" in transformed


def test_gate6_keeps_geometry_and_launcher_lifecycle_outside_scope():
    transformed = transform(source_text())

    for marker in (
        "def _layout_modules(self) -> None:",
        "def _drag_widget(self, widget: ModuleWidget, delta_x: int, delta_y: int) -> None:",
        "def _resize_widget(self, widget: ModuleWidget, width: int, height: int) -> None:",
        "def _is_collision(self, candidate: Rect, current: ModuleWidget) -> bool:",
        "def _apply_theme(self) -> None:",
    ):
        assert marker in transformed

    assert "AutosaveSession" not in transformed
    assert "AutostartManager" not in transformed
