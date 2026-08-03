from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from apply_gate5_session_lifecycle_v2 import transform


def source_text() -> str:
    return (Path(__file__).resolve().parents[1] / "system" / "launcher_gui.py").read_text(
        encoding="utf-8"
    )


def test_gate5_codemod_is_idempotent_and_syntax_valid():
    first = transform(source_text())
    second = transform(first)

    assert first == second
    ast.parse(first)


def test_gate5_codemod_integrates_shutdown_and_autosave_contracts():
    transformed = transform(source_text())

    assert "from session_lifecycle import (" in transformed
    assert "self.autosave_session = AutosaveSession(" in transformed
    assert 'self.task_runner.start(\n                "shutdown"' in transformed
    assert "return run_shutdown_sequence(" in transformed
    assert "complete_shutdown(" in transformed
    assert "self.autosave_session.cancel()" in transformed
    assert "self.autosave_session.start(self.autosave_config)" in transformed
    assert "self.logout_running" not in transformed
    assert "self.autosave_job" not in transformed
    assert "threading.Thread(target=self._execute_logout" not in transformed
    assert "import threading" not in transformed


def test_gate5_codemod_adds_tested_autostart_switch():
    transformed = transform(source_text())

    assert "from autostart_manager import AutostartError, AutostartManager" in transformed
    assert "self.autostart_manager = AutostartManager(" in transformed
    assert "Beim Hochfahren automatisch starten" in transformed
    assert "command=self._toggle_autostart" in transformed
    assert "def _toggle_autostart(self) -> None:" in transformed
    assert "self.autostart_manager.set_enabled(enabled)" in transformed
    assert "self.autostart_check" in transformed
    assert (
        '"autostart_check": self.autostart_check' in transformed
        or "if self.autostart_check is not None:" in transformed
    )


def test_gate5_keeps_previous_gates_and_future_scope_untouched():
    transformed = transform(source_text())

    for marker in (
        "self.task_runner.is_running(\"diagnostics\")",
        "self.task_runner.is_running(\"maintenance\")",
        "def apply_theme(self, theme_name: str) -> None:",
        "def _update_layout_by_width(self) -> None:",
        "def _append_module_check(self, text: str, issues: List[str]) -> str:",
    ):
        assert marker in transformed
