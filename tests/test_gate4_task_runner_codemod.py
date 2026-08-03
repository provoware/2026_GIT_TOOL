from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from apply_gate4_task_runner import transform


def test_gate4_codemod_is_idempotent_and_syntax_valid():
    source = (Path(__file__).resolve().parents[1] / "system" / "launcher_gui.py").read_text(
        encoding="utf-8"
    )

    first = transform(source)
    second = transform(first)

    assert first == second
    ast.parse(first)


def test_gate4_codemod_changes_only_task_orchestration_contracts():
    source = (Path(__file__).resolve().parents[1] / "system" / "launcher_gui.py").read_text(
        encoding="utf-8"
    )
    transformed = transform(source)

    assert "from task_runner import (" in transformed
    assert "self.task_runner = TaskRunner(self.root.after)" in transformed
    assert "self.diagnostics_running = False" not in transformed
    assert "self.maintenance_running = False" not in transformed
    assert "subprocess.run(" not in transformed
    assert "threading.Thread(target=self._run_diagnostics" not in transformed
    assert "target=self._execute_maintenance" not in transformed
    assert 'self.task_runner.start(\n                "diagnostics"' in transformed
    assert 'self.task_runner.start(\n                "maintenance"' in transformed
    assert 'self._set_maintenance_buttons("normal")' in transformed
    assert 'self.diagnostics_button.configure(state="normal")' in transformed
    assert 'self.task_runner.start(\n                "shutdown"' in transformed
    assert "threading.Thread(target=self._execute_logout" not in transformed


def test_gate4_codemod_keeps_later_lifecycle_and_ui_areas_untouched():
    source = (Path(__file__).resolve().parents[1] / "system" / "launcher_gui.py").read_text(
        encoding="utf-8"
    )
    transformed = transform(source)

    for marker in (
        "def request_logout(self) -> None:",
        "def _execute_logout(self) -> ShutdownOutcome:",
        "def _setup_autosave(self) -> None:",
        "def _toggle_autostart(self) -> None:",
        "def apply_theme(self, theme_name: str) -> None:",
        "def _update_layout_by_width(self) -> None:",
    ):
        assert marker in transformed
