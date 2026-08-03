from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SYSTEM_DIR = ROOT / "system"
if str(SYSTEM_DIR) not in sys.path:
    sys.path.insert(0, str(SYSTEM_DIR))

from validate_ui_governance import (  # noqa: E402
    BLOCK_1_ALLOWED_PATHS,
    BLOCK_2_ALLOWED_PATHS,
    UiGovernanceError,
    allowed_paths_for_block,
    load_policy,
    validate_changed_paths,
    validate_policy,
)


def policy() -> dict:
    return load_policy(ROOT / "config" / "ui-governance.json")


def test_current_governance_contract_is_valid():
    validated = validate_policy(policy(), root=ROOT)

    assert validated["current_block"] == 2
    assert validated["next_permitted_block"] == 3
    assert validated["principles"]["forbid_visual_runtime_migration_in_block_2"] is True


def test_design_tokens_remain_single_source_with_generated_runtime():
    data = policy()
    sources = {
        item["responsibility"]: item
        for item in data["authoritative_sources"]
    }
    planned_targets = {item["target"] for item in data["planned_responsibilities"]}

    assert sources["design_tokens"]["owner"] == "config/design-tokens.json"
    assert sources["python_design_token_runtime"] == {
        "responsibility": "python_design_token_runtime",
        "owner": "generated/design_tokens.py",
        "status": "generated",
    }
    assert "generated/design_tokens.py" not in planned_targets
    assert "system/ui_tokens.py" not in planned_targets
    assert "system/ui_tokens.py" in data["forbidden_parallel_sources"]
    assert "generated/design-tokens.py" in data["forbidden_parallel_sources"]
    assert not (ROOT / "system" / "ui_tokens.py").exists()
    assert not (ROOT / "generated" / "design-tokens.py").exists()


def test_conditional_extraction_requires_real_reuse():
    planned = {
        item["responsibility"]: item
        for item in policy()["planned_responsibilities"]
    }

    assert len(planned["shared_tk_components"]["current_consumers"]) >= 2
    assert planned["shared_table_policy"]["current_consumers"] == [
        "modules/datei_manager/window.py"
    ]
    assert planned["shared_preview_policy"]["current_consumers"] == [
        "modules/datei_manager/window.py"
    ]
    assert not (ROOT / "system" / "ui_tables.py").exists()
    assert not (ROOT / "system" / "ui_preview.py").exists()


def test_protected_contracts_have_real_evidence_files():
    for contract in policy()["protected_contracts"]:
        assert (ROOT / contract["path"]).is_file(), contract["path"]
        assert contract["evidence"], contract["path"]
        for evidence in contract["evidence"]:
            assert (ROOT / evidence).is_file(), evidence


def test_duplicate_inventory_matches_current_repository_evidence():
    topics = {item["topic"] for item in policy()["duplication_register"]}
    assert {
        "theme_palette",
        "spacing_and_widget_metrics",
        "typography",
        "button_configuration",
        "panel_card_surface_styling",
        "status_presentation",
        "responsive_breakpoints_and_minimums",
        "help_focus_and_keyboard_bindings",
        "treeview_and_image_preview",
    } <= topics

    design_tokens = json.loads((ROOT / "config" / "design-tokens.json").read_text(encoding="utf-8"))
    launcher_config = json.loads((ROOT / "config" / "launcher_gui.json").read_text(encoding="utf-8"))
    file_manager_config = json.loads((ROOT / "config" / "datei_manager.json").read_text(encoding="utf-8"))
    launcher_source = (ROOT / "system" / "launcher_gui.py").read_text(encoding="utf-8")
    main_source = (ROOT / "system" / "main_window.py").read_text(encoding="utf-8")
    file_manager_source = (ROOT / "modules" / "datei_manager" / "window.py").read_text(encoding="utf-8")

    assert design_tokens["themes"]
    assert launcher_config["themes"]
    assert file_manager_config["themes"]
    assert launcher_source.count("self.layout.button_padx") >= 6
    assert "padx=16" in main_source
    assert "self.root.minsize(900, 600)" in file_manager_source
    assert "ttk.Treeview(" in file_manager_source
    assert "self.preview_canvas" in file_manager_source


def test_duplicate_responsibility_is_rejected():
    data = copy.deepcopy(policy())
    data["authoritative_sources"].append(copy.deepcopy(data["authoritative_sources"][0]))

    with pytest.raises(UiGovernanceError, match="mehrere Quellenangaben"):
        validate_policy(data, root=ROOT)


def test_missing_evidence_file_is_rejected():
    data = copy.deepcopy(policy())
    data["protected_contracts"][0]["evidence"] = ["tests/fehlt.py"]

    with pytest.raises(UiGovernanceError, match="fehlt"):
        validate_policy(data, root=ROOT)


def test_parallel_token_source_is_rejected_when_it_exists(tmp_path: Path):
    data = copy.deepcopy(policy())
    fake_root = tmp_path / "repo"
    fake_root.mkdir()

    required_paths: set[str] = set()
    required_paths.update(item["owner"] for item in data["authoritative_sources"])
    required_paths.update(item["path"] for item in data["transitional_sources"])
    for contract in data["protected_contracts"]:
        required_paths.add(contract["path"])
        required_paths.update(contract["evidence"])
    for duplicate in data["duplication_register"]:
        required_paths.update(duplicate["locations"])
    for planned in data["planned_responsibilities"]:
        required_paths.update(planned.get("current_consumers", []))
    for path in required_paths:
        target = fake_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("x", encoding="utf-8")

    forbidden = fake_root / "system" / "ui_tokens.py"
    forbidden.parent.mkdir(parents=True, exist_ok=True)
    forbidden.write_text("TOKENS = {}", encoding="utf-8")

    with pytest.raises(UiGovernanceError, match="Verbotene Parallelquelle"):
        validate_policy(data, root=fake_root)


def test_migration_order_must_start_with_next_block():
    data = copy.deepcopy(policy())
    data["next_permitted_block"] = 4

    with pytest.raises(UiGovernanceError, match="unmittelbar"):
        validate_policy(data, root=ROOT)


def test_block_specific_diff_whitelists_reject_visual_runtime_files():
    assert allowed_paths_for_block(1) == BLOCK_1_ALLOWED_PATHS
    assert allowed_paths_for_block(2) == BLOCK_2_ALLOWED_PATHS
    validate_changed_paths(sorted(BLOCK_1_ALLOWED_PATHS), block=1)
    validate_changed_paths(sorted(BLOCK_2_ALLOWED_PATHS), block=2)

    for path in (
        "system/launcher_gui.py",
        "system/main_window.py",
        "modules/datei_manager/window.py",
        "system/ui_theme_adapter.py",
    ):
        with pytest.raises(UiGovernanceError, match="Block 2 darf"):
            validate_changed_paths([path], block=2)

    with pytest.raises(UiGovernanceError, match="noch keine Diff-Whitelist"):
        allowed_paths_for_block(3)
