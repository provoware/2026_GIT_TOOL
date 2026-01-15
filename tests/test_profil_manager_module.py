from __future__ import annotations

import json
from pathlib import Path

from modules.profil_manager import module as profil_manager_module


def write_config(path: Path, base_dir: Path, state_path: Path) -> None:
    config = {
        "base_dir": str(base_dir),
        "state_path": str(state_path),
        "default_theme": "dunkel",
        "themes": {
            "dunkel": {
                "background": "#000",
                "foreground": "#fff",
                "accent": "#8b5cf6",
                "panel": "#111",
            }
        },
        "ui": {"title": "Test"},
        "debug": False,
    }
    path.write_text(json.dumps(config), encoding="utf-8")


def test_profil_manager_lifecycle(tmp_path: Path) -> None:
    base_dir = tmp_path / "profiles"
    state_path = tmp_path / "state.json"
    config_path = tmp_path / "config.json"
    write_config(config_path, base_dir, state_path)

    create_response = profil_manager_module.run(
        {
            "action": "create_profile",
            "name": "projekt_01",
            "context": {"config_path": str(config_path)},
        }
    )
    assert create_response["status"] == "ok"

    list_response = profil_manager_module.run(
        {"action": "list_profiles", "context": {"config_path": str(config_path)}}
    )
    assert len(list_response["data"]["profiles"]) == 1

    rename_response = profil_manager_module.run(
        {
            "action": "rename_profile",
            "from": "projekt_01",
            "to": "projekt_02",
            "context": {"config_path": str(config_path)},
        }
    )
    assert rename_response["status"] == "ok"

    set_active = profil_manager_module.run(
        {
            "action": "set_active",
            "name": "projekt_02",
            "context": {"config_path": str(config_path)},
        }
    )
    assert set_active["status"] == "ok"
