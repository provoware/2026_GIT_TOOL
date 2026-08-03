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

    exit_code = main(
        [
            "--database",
            str(database),
            "--log-file",
            str(log_file),
            "--archive",
            "genres",
            "--category",
            "Test",
            "--value",
            "Fantasy, fantasy, Horror",
            "--yes",
        ]
    )

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

    exit_code = main(
        [
            "--database",
            str(database),
            "--log-file",
            str(log_file),
            "--create-archive",
            "Werkzeuge",
            "--description",
            "Hilfreiche Werkzeuge",
            "--split-mode",
            "whole",
        ]
    )

    assert exit_code == 0
    archive = ArchiveService(database).get_archive("werkzeuge")
    assert archive.description == "Hilfreiche Werkzeuge"
    assert archive.split_on_comma is False


def test_cli_can_set_archive_mode_directly(tmp_path: Path):
    database = tmp_path / "archive.sqlite3"
    log_file = tmp_path / "archive.log"

    exit_code = main(
        [
            "--database",
            str(database),
            "--log-file",
            str(log_file),
            "--archive",
            "genres",
            "--set-mode",
            "whole",
        ]
    )

    assert exit_code == 0
    assert ArchiveService(database).get_archive("genres").split_on_comma is False


def test_logging_reconfigures_for_a_new_log_path(tmp_path: Path):
    from modules.archiv_manager.cli import configure_logging

    first = tmp_path / "first.log"
    second = tmp_path / "second.log"
    logger = configure_logging(first)
    logger.info("erste Datei")
    logger = configure_logging(second)
    logger.info("zweite Datei")
    for handler in logger.handlers:
        handler.flush()

    assert first.exists()
    assert second.exists()
    assert "zweite Datei" in second.read_text(encoding="utf-8")


def test_cli_rejects_value_without_archive(tmp_path: Path, capsys):
    exit_code = main(
        [
            "--database",
            str(tmp_path / "archive.sqlite3"),
            "--log-file",
            str(tmp_path / "archive.log"),
            "--value",
            "Fantasy",
            "--yes",
        ]
    )

    assert exit_code == 2
    assert "--value benötigt zusätzlich --archive" in capsys.readouterr().err


def test_cli_initialization_failure_is_controlled(tmp_path: Path, capsys):
    invalid_log_path = tmp_path / "log-directory"
    invalid_log_path.mkdir()

    exit_code = main(
        [
            "--database",
            str(tmp_path / "archive.sqlite3"),
            "--log-file",
            str(invalid_log_path),
            "--list",
        ]
    )

    assert exit_code == 2
    assert "CLI konnte nicht initialisiert werden" in capsys.readouterr().err
