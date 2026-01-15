from __future__ import annotations

import json
from pathlib import Path

from modules.media_wavesurfer import module as wavesurfer_module


def write_config(path: Path, data_path: Path) -> None:
    config = {
        "data_path": str(data_path),
        "default_theme": "dunkel",
        "themes": {
            "dunkel": {
                "background": "#000",
                "foreground": "#fff",
                "accent": "#38bdf8",
                "panel": "#111",
            }
        },
        "ui": {"title": "Test"},
        "export_profiles": [
            {"id": "wav", "label": "WAV", "format": "wav"},
        ],
        "minimap": {"height": 40, "zoom": 1.0, "color": "#38bdf8"},
        "debug": False,
    }
    path.write_text(json.dumps(config), encoding="utf-8")


def test_wavesurfer_markers_and_regions(tmp_path: Path) -> None:
    data_path = tmp_path / "wavesurfer.json"
    config_path = tmp_path / "config.json"
    write_config(config_path, data_path)

    list_response = wavesurfer_module.run(
        {"action": "list_features", "context": {"config_path": str(config_path)}}
    )
    assert list_response["status"] == "ok"
    assert list_response["data"]["export_profiles"][0]["id"] == "wav"

    marker_response = wavesurfer_module.run(
        {
            "action": "add_marker",
            "time": 1.5,
            "label": "Intro",
            "context": {"config_path": str(config_path)},
        }
    )
    assert marker_response["status"] == "ok"

    region_response = wavesurfer_module.run(
        {
            "action": "add_region",
            "start": 2.0,
            "end": 4.5,
            "label": "Strophe",
            "context": {"config_path": str(config_path)},
        }
    )
    assert region_response["status"] == "ok"

    markers_list = wavesurfer_module.run(
        {"action": "list_markers", "context": {"config_path": str(config_path)}}
    )
    assert len(markers_list["data"]["markers"]) == 1

    regions_list = wavesurfer_module.run(
        {"action": "list_regions", "context": {"config_path": str(config_path)}}
    )
    assert len(regions_list["data"]["regions"]) == 1
