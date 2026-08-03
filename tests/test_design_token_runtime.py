from __future__ import annotations

import ast
import copy
import importlib.util
import sys
from pathlib import Path
from types import MappingProxyType

import pytest

ROOT = Path(__file__).resolve().parents[1]
SYSTEM_DIR = ROOT / "system"
if str(SYSTEM_DIR) not in sys.path:
    sys.path.insert(0, str(SYSTEM_DIR))

import generate_design_tokens as generator  # noqa: E402


def test_runtime_data_converts_supported_units_deterministically():
    runtime = generator.build_python_runtime_data(generator.load_tokens())

    assert runtime["meta"]["default_theme"] == "acid-paper"
    assert runtime["themes"]["acid-paper"]["surfaceElevated"] == "#FFFDF3"
    assert runtime["spacing_px"] == {
        "0": 0,
        "1": 4,
        "2": 8,
        "3": 12,
        "4": 16,
        "5": 24,
        "6": 32,
        "7": 48,
    }
    assert runtime["radius_px"]["md"] == 8
    assert runtime["font_size_px"]["2xl"] == 32
    assert runtime["motion_ms"]["normal"] == 200
    assert runtime["breakpoint_px"] == {"desktop": 1200, "phone": 430, "tablet": 768}
    assert runtime["layout_px"]["touchTarget"] == 44


def test_generated_python_is_valid_importable_and_deeply_read_only(tmp_path: Path):
    source = generator.build_python_runtime(generator.load_tokens())
    ast.parse(source)
    target = tmp_path / "design_tokens.py"
    target.write_text(source, encoding="utf-8")

    spec = importlib.util.spec_from_file_location("generated_tokens_test", target)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert isinstance(module.TOKENS, MappingProxyType)
    assert isinstance(module.THEMES["acid-paper"], MappingProxyType)
    assert module.DEFAULT_THEME == "acid-paper"
    assert module.get_theme()["accent"] == "#C7FF00"
    assert module.SPACING_PX["4"] == 16
    assert module.LAYOUT_PX["touchTarget"] == 44
    assert module.theme_names() == ("acid-paper", "neon-scrap")

    with pytest.raises(TypeError):
        module.SPACING_PX["4"] = 99
    with pytest.raises(TypeError):
        module.THEMES["acid-paper"]["accent"] = "#000000"
    with pytest.raises(KeyError):
        module.get_theme("unbekannt")
    with pytest.raises(TypeError):
        module.get_theme(42)


def test_generated_runtime_file_matches_generator_output():
    expected = generator.build_python_runtime(generator.load_tokens())
    actual = (ROOT / "generated" / "design_tokens.py").read_text(encoding="utf-8")

    assert actual == expected
    assert "AUTO-GENERATED" in actual
    assert "config/design-tokens.json" in actual


def test_expected_outputs_registers_importable_python_artifact():
    outputs = generator.expected_outputs(generator.load_tokens())

    assert ROOT / "generated" / "design_tokens.py" in outputs
    assert ROOT / "generated" / "design-tokens.py" not in outputs


def test_unsupported_or_fractional_runtime_units_fail_early():
    tokens = copy.deepcopy(generator.load_tokens())
    tokens["spacing"]["1"] = "1em"
    with pytest.raises(ValueError, match="Einheit"):
        generator.build_python_runtime_data(tokens)

    tokens = copy.deepcopy(generator.load_tokens())
    tokens["spacing"]["1"] = "0.1rem"
    with pytest.raises(ValueError, match="ganzzahlige Pixel"):
        generator.build_python_runtime_data(tokens)

    tokens = copy.deepcopy(generator.load_tokens())
    tokens["motion"]["fast"] = "schnell"
    with pytest.raises(ValueError, match="Millisekunden"):
        generator.build_python_runtime_data(tokens)


def test_runtime_generation_does_not_modify_input():
    tokens = generator.load_tokens()
    snapshot = copy.deepcopy(tokens)

    generator.build_python_runtime_data(tokens)
    generator.build_python_runtime(tokens)

    assert tokens == snapshot
