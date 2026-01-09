from __future__ import annotations

import json
from pathlib import Path

from modules.datei_suche import module as search_module


def write_config(path: Path, root: Path, log_path: Path) -> None:
    config = {
        "search_roots": [str(root)],
        "exclude_dirs": [],
        "log_path": str(log_path),
        "default_theme": "hell",
        "themes": {"hell": {"background": "#fff", "foreground": "#000"}},
        "ui": {"title": "Test"},
        "debug": False,
        "max_results": 100,
        "text_extensions": ["txt"],
    }
    path.write_text(json.dumps(config), encoding="utf-8")


def test_search_organize_and_undo(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    file_txt = root / "notiz.txt"
    file_txt.write_text("Hallo Welt", encoding="utf-8")

    config_path = tmp_path / "config.json"
    log_path = tmp_path / "log.json"
    write_config(config_path, root, log_path)

    search_response = search_module.run(
        {
            "action": "search",
            "query": {"content_contains": "Welt"},
            "context": {"config_path": str(config_path)},
        }
    )
    assert search_response["status"] == "ok"
    results = search_response["data"]["results"]
    assert len(results) == 1

    target_dir = root / "Ziel"
    organize_response = search_module.run(
        {
            "action": "organize",
            "items": results,
            "target_dir": str(target_dir),
            "mode": "move",
            "context": {"config_path": str(config_path)},
        }
    )
    assert organize_response["status"] == "ok"
    moved_path = target_dir / "notiz.txt"
    assert moved_path.exists()

    undo_response = search_module.run(
        {"action": "undo", "context": {"config_path": str(config_path)}}
    )
    assert undo_response["status"] == "ok"
    assert file_txt.exists()
