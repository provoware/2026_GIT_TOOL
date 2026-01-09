from __future__ import annotations

import json
from pathlib import Path

from modules.download_aufraeumen import module as download_module


def write_config(path: Path, download_path: Path, log_path: Path) -> None:
    config = {
        "download_path": str(download_path),
        "log_path": str(log_path),
        "default_theme": "hell",
        "themes": {"hell": {"background": "#fff", "foreground": "#000"}},
        "rules": [
            {
                "label": "Dokumente",
                "folder": "Dokumente",
                "extensions": ["txt"],
            },
            {
                "label": "Sonstiges",
                "folder": "Sonstiges",
                "extensions": [],
                "fallback": True,
            },
        ],
        "ui": {"title": "Test"},
        "debug": False,
    }
    path.write_text(json.dumps(config), encoding="utf-8")


def test_scan_apply_and_undo(tmp_path: Path) -> None:
    download_path = tmp_path / "Downloads"
    download_path.mkdir()
    file_txt = download_path / "bericht.txt"
    file_txt.write_text("Hallo", encoding="utf-8")

    config_path = tmp_path / "config.json"
    log_path = tmp_path / "log.json"
    write_config(config_path, download_path, log_path)

    init_response = download_module.init({"config_path": str(config_path)})
    assert init_response["status"] == "ok"

    scan_response = download_module.run(
        {"action": "scan", "context": {"config_path": str(config_path)}}
    )
    assert scan_response["status"] == "ok"
    items = scan_response["data"]["items"]
    assert len(items) == 1

    plan_response = download_module.run(
        {
            "action": "build_plan",
            "items": items,
            "context": {"config_path": str(config_path)},
        }
    )
    operations = plan_response["data"]["operations"]

    apply_response = download_module.run(
        {
            "action": "apply_plan",
            "operations": operations,
            "context": {"config_path": str(config_path)},
        }
    )
    assert apply_response["status"] == "ok"
    moved_path = download_path / "Dokumente" / "bericht.txt"
    assert moved_path.exists()

    undo_response = download_module.run(
        {"action": "undo", "context": {"config_path": str(config_path)}}
    )
    assert undo_response["status"] == "ok"
    assert file_txt.exists()
