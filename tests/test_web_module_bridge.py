from __future__ import annotations

from pathlib import Path

import pytest

from system.web_module_bridge import MODULE_ACTIONS, WebModuleBridge, WebModuleBridgeError


ROOT = Path(__file__).resolve().parents[1]


def test_catalog_exposes_every_registered_main_module_once() -> None:
    bridge = WebModuleBridge(ROOT)
    catalog = bridge.catalog()
    module_ids = [item["id"] for item in catalog]
    assert len(module_ids) == len(set(module_ids)) == 12
    assert set(module_ids) == set(MODULE_ACTIONS)
    assert all(item["actions"] for item in catalog)
    assert all(item["default_action"] in {action["id"] for action in item["actions"]} for item in catalog)


def test_all_action_ids_are_unique_per_module() -> None:
    for module_id, actions in MODULE_ACTIONS.items():
        action_ids = [item["id"] for item in actions]
        assert len(action_ids) == len(set(action_ids)), module_id


def test_read_only_snapshots_cover_every_module_without_crashing() -> None:
    snapshots = WebModuleBridge(ROOT).snapshots()
    assert set(snapshots) == set(MODULE_ACTIONS)
    assert all(item["status"] == "ok" for item in snapshots.values())


def test_unknown_or_unregistered_action_is_rejected() -> None:
    bridge = WebModuleBridge(ROOT)
    with pytest.raises(WebModuleBridgeError, match="nicht freigegeben"):
        bridge.invoke("notiz_editor", "delete_everything", {})
    with pytest.raises(WebModuleBridgeError, match="nicht verfügbar"):
        bridge.invoke("unknown", "run", {})


def test_example_snapshot_receives_safe_default_text() -> None:
    result = WebModuleBridge(ROOT).invoke("beispiel_modul", "echo", {})
    assert result["status"] == "ok"
    assert result["data"]["ok"] is True
