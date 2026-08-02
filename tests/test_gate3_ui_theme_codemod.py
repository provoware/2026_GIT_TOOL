import ast
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from apply_gate3_ui_theme_adapter import transform_launcher, transform_main_window


ROOT = Path(__file__).resolve().parents[1]


def test_launcher_theme_codemod_is_idempotent():
    source = (ROOT / "system" / "launcher_gui.py").read_text(encoding="utf-8")

    first = transform_launcher(source)
    second = transform_launcher(first)

    assert first == second
    ast.parse(first)
    assert "from ui_theme_adapter import (" in first
    assert "theme = resolve_theme(self.gui_config, clean_name, strict=True)" in first
    assert "self.status_palette = build_status_palette(theme)" in first
    assert "apply_theme_tree(self.root, theme, button_font=self.button_font)" in first


def test_main_window_theme_codemod_is_idempotent():
    source = (ROOT / "system" / "main_window.py").read_text(encoding="utf-8")

    first = transform_main_window(source)
    second = transform_main_window(first)

    assert first == second
    ast.parse(first)
    assert "from ui_theme_adapter import (" in first
    assert "apply_module_card_theme(self, theme)" in first
    assert "resolve_theme(self.gui_config, theme_key, strict=False)" in first
    assert "apply_theme_tree(self.root, theme)" in first
