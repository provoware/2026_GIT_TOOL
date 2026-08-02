import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "scripts"))

from apply_gate1_launcher_reports import METHOD_REPLACEMENTS, transform


def test_codemod_is_syntax_safe_and_idempotent() -> None:
    source = (ROOT / "system" / "launcher_gui.py").read_text(encoding="utf-8")
    transformed = transform(source)

    ast.parse(transformed)
    assert transform(transformed) == transformed
    assert "from launcher_reports import (" in transformed

    for method_name, replacement in METHOD_REPLACEMENTS.items():
        assert replacement in transformed, method_name


def test_codemod_does_not_remove_side_effectful_module_check() -> None:
    source = (ROOT / "system" / "launcher_gui.py").read_text(encoding="utf-8")
    transformed = transform(source)

    assert "def _append_module_check" in transformed
    assert "self._show_error" in transformed
    assert "self.logger.error" in transformed
