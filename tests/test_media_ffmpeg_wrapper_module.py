from __future__ import annotations

import json
from pathlib import Path

from modules.media_ffmpeg_wrapper import module as ffmpeg_module


def write_config(path: Path, data_path: Path, output_dir: Path) -> None:
    config = {
        "data_path": str(data_path),
        "output_dir": str(output_dir),
        "default_theme": "dunkel",
        "themes": {
            "dunkel": {
                "background": "#000",
                "foreground": "#fff",
                "accent": "#22c55e",
                "panel": "#111",
            }
        },
        "ui": {"title": "Test"},
        "presets": [
            {"id": "mp3", "label": "MP3", "extension": ".mp3", "args": ["-vn", "-b:a", "192k"]}
        ],
        "debug": False,
    }
    path.write_text(json.dumps(config), encoding="utf-8")


def test_ffmpeg_build_and_progress(tmp_path: Path) -> None:
    data_path = tmp_path / "jobs.json"
    output_dir = tmp_path / "exports"
    config_path = tmp_path / "config.json"
    write_config(config_path, data_path, output_dir)

    input_file = tmp_path / "audio.wav"
    input_file.write_text("dummy", encoding="utf-8")

    build_response = ffmpeg_module.run(
        {
            "action": "build_command",
            "input_path": str(input_file),
            "preset_id": "mp3",
            "context": {"config_path": str(config_path)},
        }
    )
    assert build_response["status"] == "ok"
    job_id = build_response["data"]["job_id"]

    progress_response = ffmpeg_module.run(
        {
            "action": "simulate_progress",
            "job_id": job_id,
            "context": {"config_path": str(config_path)},
        }
    )
    assert progress_response["status"] == "ok"
    assert progress_response["data"]["progress"] > 0
