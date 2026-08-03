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
    UiGovernanceError,
    load_policy,
    validate_changed_paths,
    validate_policy,
)


def policy() -> dict:
    return load_policy(ROOT / "config" / "ui-governance.json")


def test_current_governance_contract_is_valid():
    validated = validate_policy(policy(), root=ROOT)

    assert validated["current_block"] == 1
    assert validated["next_permitted_block"] == 2
    assert validated["principles"]["forbid_visual_runtime_migration_in_block_1"] is True


def test_design_tokens_remain_the_only_hand_maintained_token_source():
    data = policy()
    sources = {
        item["responsibility"]: item["owner"]
        for item in data["authoritative_sources"]
    }
    planned_targets = {item["target"] for item in data["planned_responsibilities"]}

    assert sources["design_tokens"] == "config/design-tokens.json"
    assert "generated/design-tokens.py" in planned_targets
    assert "system/ui_tokens.py" not in planned_targets
    assert "system/ui_tokens.py" in data["forbidden_parallel_sources"]
    assert not (ROOT / "system" / "ui_tokens.py").exists()


def test_conditional_extraction_requires_real_reuse():
    data = policy()
    planned = {
        item["responsibility"]: item
        for item in data["planned_responsibilities"]
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
    data = policy()

    for contract in data["protected_contracts"]:
        assert (ROOT / contract["path"]).is_file(), contract["path"]
        assert contract["evidence"], contract["path"]
        for evidence in contract["evidence"]:
            assert (ROOT / evidence).is_file(), evidence


def test_duplicate_inventory_matches_current_repository_evidence():
    data = policy()
    topics = {item["topic"] for item in data["duplication_register"]}
    required_topics = {
        "theme_palette",
        "spacing_and_widget_metrics",
        "typography",
        "button_configuration",
        "panel_card_surface_styling",
        "status_presentation",
        "responsive_breakpoints_and_minimums",
        "help_focus_and_keyboard_bindings",
        "treeview_and_image_preview",
    }

    assert required_topics <= topics

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

    for source in data["authoritative_sources"]:
        target = fake_root / source["owner"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("x", encoding="utf-8")
    for source in data["transitional_sources"]:
        target = fake_root / source["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("x", encoding="utf-8")
    for contract in data["protected_contracts"]:
        target = fake_root / contract["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("x", encoding="utf-8")
        for evidence in contract["evidence"]:
            evidence_path = fake_root / evidence
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text("x", encoding="utf-8")
    for duplicate in data["duplication_register"]:
        for location in duplicate["locations"]:
            target = fake_root / location
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("x", encoding="utf-8")
    for planned in data["planned_responsibilities"]:
        for consumer in planned.get("current_consumers", []):
            target = fake_root / consumer
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("x", encoding="utf-8")

    forbidden = fake_root / "system" / "ui_tokens.py"
    forbidden.parent.mkdir(parents=True, exist_ok=True)
    forbidden.write_text("TOKENS = {}", encoding="utf-8")

    with pytest.raises(UiGovernanceError, match="Verbotene Parallelquelle"):
        validate_policy(data, root=fake_root)


def test_migration_order_must_start_with_next_block():
    data = copy.deepcopy(policy())
    data["next_permitted_block"] = 3

    with pytest.raises(UiGovernanceError, match="unmittelbar"):
        validate_policy(data, root=ROOT)


def test_block_one_diff_rejects_visual_runtime_files():
    validate_changed_paths(sorted(BLOCK_1_ALLOWED_PATHS))

    with pytest.raises(UiGovernanceError, match="darf diese Datei nicht ändern"):
        validate_changed_paths(["system/launcher_gui.py"])

    with pytest.raises(UiGovernanceError, match="darf diese Datei nicht ändern"):
        validate_changed_paths(["modules/datei_manager/window.py"])
