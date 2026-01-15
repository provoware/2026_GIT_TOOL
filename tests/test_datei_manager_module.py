from __future__ import annotations

import json
from pathlib import Path

from modules.datei_manager import module as datei_manager_module


def write_config(path: Path, data_path: Path) -> None:
    config = {
        "data_path": str(data_path),
        "default_theme": "dunkel",
        "themes": {
            "dunkel": {
                "background": "#000",
                "foreground": "#fff",
                "accent": "#f59e0b",
                "panel": "#111",
            }
        },
        "ui": {"title": "Test"},
        "debug": False,
    }
    path.write_text(json.dumps(config), encoding="utf-8")


def test_datei_manager_rename_and_tags(tmp_path: Path) -> None:
    data_path = tmp_path / "manager.json"
    config_path = tmp_path / "config.json"
    write_config(config_path, data_path)

    file_path = tmp_path / "Meine Datei.txt"
    file_path.write_text("Test", encoding="utf-8")

    rename_response = datei_manager_module.run(
        {
            "action": "quick_rename",
            "path": str(file_path),
            "new_name": "Projekt Datei",
            "context": {"config_path": str(config_path)},
        }
    )
    assert rename_response["status"] == "ok"
    new_path = Path(rename_response["data"]["new_path"])
    assert new_path.exists()

    tag_response = datei_manager_module.run(
        {
            "action": "tag_items",
            "paths": [str(new_path)],
            "tags": ["Audio", "Projekt"],
            "context": {"config_path": str(config_path)},
        }
    )
    assert tag_response["status"] == "ok"
    assert "audio" in tag_response["data"]["items"][0]["tags"]

    favorite_response = datei_manager_module.run(
        {
            "action": "toggle_favorite",
            "path": str(new_path),
            "context": {"config_path": str(config_path)},
        }
    )
    assert favorite_response["status"] == "ok"
    assert favorite_response["data"]["favorite"] is True
