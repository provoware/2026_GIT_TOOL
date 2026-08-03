from __future__ import annotations

import sys
from pathlib import Path

SYSTEM_DIR = Path(__file__).resolve().parents[1] / "system"
if str(SYSTEM_DIR) not in sys.path:
    sys.path.insert(0, str(SYSTEM_DIR))

from module_loader import ModuleLoader  # noqa: E402
from module_registry import load_manifest, resolve_entry_path  # noqa: E402


MODULE_DIR = Path(__file__).resolve().parents[1] / "modules" / "datei_manager"


def test_manifest_points_to_gui_capable_entry():
    manifest = load_manifest(MODULE_DIR)
    entry_path = resolve_entry_path(MODULE_DIR, manifest.entry)

    assert manifest.version == "1.1.0"
    assert manifest.entry == "entry.py"
    assert entry_path.name == "entry.py"


def test_loader_preserves_backend_contract_and_exposes_ui_hook():
    manifest = load_manifest(MODULE_DIR)
    entry_path = resolve_entry_path(MODULE_DIR, manifest.entry)
    loaded = ModuleLoader().load("datei_manager_test", entry_path)

    for name in ("init", "run", "exit", "validateInput", "validateOutput", "open_ui"):
        assert callable(getattr(loaded, name, None)), name
    loaded.validateInput({"action": "list_favorites"})


def test_registry_context_does_not_replace_module_specific_config():
    manifest = load_manifest(MODULE_DIR)
    loaded = ModuleLoader().load(
        "datei_manager_context_test",
        resolve_entry_path(MODULE_DIR, manifest.entry),
    )

    cleaned = loaded._backend_context(
        {
            "config_path": "/projekt/config/modules.json",
            "debug": True,
            "headless": True,
        }
    )

    assert "config_path" not in cleaned
    assert "headless" not in cleaned
    assert cleaned["debug"] is True
