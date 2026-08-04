from __future__ import annotations

import ast
import importlib.util
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "apply_ui_modernization_block3.py"


def _load_codemod():
    spec = importlib.util.spec_from_file_location("block3_codemod", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _copy_targets(tmp_path: Path) -> Path:
    for relative in (
        "system/ui_components.py",
        "system/launcher_gui.py",
        "system/main_window.py",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return tmp_path


def test_codemod_is_idempotent_and_produces_valid_python(tmp_path: Path):
    codemod = _load_codemod()
    worktree = _copy_targets(tmp_path)

    first = codemod.apply(worktree, check=False)
    second = codemod.apply(worktree, check=False)

    assert first == [
        "system/ui_components.py",
        "system/launcher_gui.py",
        "system/main_window.py",
    ]
    assert second == []
    for relative in codemod.TARGETS.values():
        ast.parse((worktree / relative).read_text(encoding="utf-8"))


def test_check_mode_reports_missing_integration_without_writing(tmp_path: Path):
    codemod = _load_codemod()
    worktree = _copy_targets(tmp_path)
    before = {
        relative.as_posix(): (worktree / relative).read_text(encoding="utf-8")
        for relative in codemod.TARGETS.values()
    }

    changed = codemod.apply(worktree, check=True)

    assert changed == [
        "system/ui_components.py",
        "system/launcher_gui.py",
        "system/main_window.py",
    ]
    after = {
        relative.as_posix(): (worktree / relative).read_text(encoding="utf-8")
        for relative in codemod.TARGETS.values()
    }
    assert before == after


def test_launcher_roles_and_status_contract_are_integrated(tmp_path: Path):
    codemod = _load_codemod()
    worktree = _copy_targets(tmp_path)
    codemod.apply(worktree, check=False)
    source = (worktree / "system/launcher_gui.py").read_text(encoding="utf-8")

    assert "from ui_components import UiComponentError, configure_status_widget, register_component" in source
    assert 'register_component(self.refresh_button, "primary")' in source
    assert 'register_component(self.logout_button, "danger")' in source
    assert 'register_component(self.backup_button, "primary")' in source
    assert source.count('register_component(') >= 16
    assert "self.component_theme = theme" in source
    assert "style = configure_status_widget(" in source
    assert "self.status_indicator.configure(text=style.symbol)" in source
    assert "build_status_view(message, state)" in source
    assert "self.root.configure(cursor=view.cursor)" in source


def test_main_window_roles_preserve_lifecycle_and_geometry_contracts(tmp_path: Path):
    codemod = _load_codemod()
    worktree = _copy_targets(tmp_path)
    codemod.apply(worktree, check=False)
    source = (worktree / "system/main_window.py").read_text(encoding="utf-8")

    assert "from ui_components import register_component" in source
    assert 'register_component(controls, "panel")' in source
    assert 'register_component(self.workspace, "panel")' in source
    assert "button.configure(pady=7, takefocus=1)" not in source
    assert "menu.configure(padx=6, pady=8, takefocus=1)" not in source
    assert "perform_module_action(" in source
    assert "prepare_close(" in source
    assert "resolve_workspace_grid(" in source
    assert "build_grid(" in source


def test_hover_fix_always_produces_distinct_primary_state(tmp_path: Path):
    codemod = _load_codemod()
    worktree = _copy_targets(tmp_path)
    codemod.apply(worktree, check=False)
    source = (worktree / "system/ui_components.py").read_text(encoding="utf-8")

    assert 'hover_bg = mix_hex(normal_bg, "#ffffff", 0.12)' in source
    assert 'hover_bg = mix_hex(normal_bg, palette.accent, 0.20)' not in source
