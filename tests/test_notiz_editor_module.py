import json
from pathlib import Path

from modules.notiz_editor import module as notiz_module


def _write_config(tmp_path: Path) -> Path:
    config = {
        "data_path": str(tmp_path / "notes.json"),
        "default_theme": "hell",
        "themes": {
            "hell": {
                "primary": "#111111",
                "accent": "#222222",
                "background": "#ffffff",
                "text": "#000000",
            }
        },
        "templates": [
            {
                "id": "test",
                "name": "Test",
                "description": "Vorlage",
                "sections": ["A"],
                "prompts": ["B"],
            }
        ],
        "ui": {"menus": [], "actions": [], "dashboard_cards": []},
        "debug": False,
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def test_notiz_editor_create_and_dashboard(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    init_result = notiz_module.init({"config_path": str(config_path)})
    assert init_result["status"] == "ok"

    create_result = notiz_module.run(
        {
            "action": "create_note",
            "title": "Idee",
            "body": "Inhalt",
            "tags": ["roman"],
            "context": {"config_path": str(config_path)},
        }
    )
    assert create_result["status"] == "ok"

    list_result = notiz_module.run(
        {"action": "list_notes", "context": {"config_path": str(config_path)}}
    )
    assert list_result["status"] == "ok"
    assert len(list_result["data"]["notes"]) == 1

    dashboard = notiz_module.run(
        {"action": "dashboard", "context": {"config_path": str(config_path)}}
    )
    assert dashboard["data"]["total_notes"] == 1
