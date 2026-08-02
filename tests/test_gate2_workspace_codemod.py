import ast
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from apply_gate2_workspace_geometry_v2 import transform


def test_codemod_is_idempotent():
    source = (Path(__file__).resolve().parents[1] / "system" / "main_window.py").read_text(encoding="utf-8")
    first = transform(source)
    second = transform(first)
    assert first == second
    ast.parse(first)
    assert "from workspace_geometry import" in first
    assert "class Rect:" not in first
    assert "return rect_overlap(a, b)" in first
