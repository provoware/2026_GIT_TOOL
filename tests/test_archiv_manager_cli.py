from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.archiv_manager.cli import main  # noqa: E402
from modules.archiv_manager.service import ArchiveService  # noqa: E402


def test_cli_direct_input_uses_same_database_and_duplicate_rules(tmp_path: Path, capsys):
    database = tmp_path / "archive.sqlite3"
    log_file = tmp_path / "archive.log"
    exit_code = main([
        "--database", str(database), "--log-file", str(log_file),
        "--archive", "genres", "--category", "Test",
        "--value", "Fantasy, fantasy, Horror", "--yes",
    ])
    assert exit_code == 0
    assert log_file.exists()
    service = ArchiveService(database)
    assert {entry.value for entry in service.list_entries("genres")} == {"Fantasy", "Horror"}
    output = capsys.readouterr().out
    assert "Gespeichert: 2" in output
    assert "Duplikate ignoriert: 1" in output


def test_cli_can_create_expandable_archive(tmp_path: Path):
    database = tmp_path / "archive.sqlite3"
    log_file = tmp_path / "archive.log"
    exit_code = main([
        "--database", str(database), "--log-file", str(log_file),
        "--create-archive", "Werkzeuge", "--description", "Hilfreiche Werkzeuge",
        "--split-mode", "whole",
    ])
    assert exit_code == 0
    archive = ArchiveService(database).get_archive("werkzeuge")
    assert archive.description == "Hilfreiche Werkzeuge"
    assert archive.split_on_comma is False
