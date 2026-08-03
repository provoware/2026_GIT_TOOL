from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.archiv_manager.aliases import (  # noqa: E402
    FUNCTION_ALIASES,
    MANAGED_MARKER,
    STANDARD_ARCHIVE_ALIASES,
    alias_table,
    all_alias_specs,
    archive_alias_specs,
    dispatch_alias,
    install_aliases,
    run_control_center,
    uninstall_aliases,
)
from modules.archiv_manager.service import ArchiveService, ArchiveServiceError  # noqa: E402


def _service(tmp_path: Path) -> ArchiveService:
    return ArchiveService(tmp_path / "archive.sqlite3")


def test_alias_registry_is_unique_and_covers_all_standard_archives(tmp_path: Path):
    service = _service(tmp_path)
    specs = all_alias_specs(service)

    assert len(STANDARD_ARCHIVE_ALIASES) == 7
    assert len({item.name for item in specs}) == len(specs)
    assert {item.target for item in STANDARD_ARCHIVE_ALIASES} == {
        archive.slug for archive in service.list_archives()
    }
    assert {item.name for item in FUNCTION_ALIASES} >= {
        "garch",
        "garch-add",
        "garch-list",
        "garch-new",
        "garch-mode",
        "garch-aliases",
        "garch-help",
    }


def test_control_center_lists_function_and_archive_aliases(tmp_path: Path, capsys):
    service = _service(tmp_path)
    answers = iter(["0"])

    result = run_control_center(service, lambda _prompt: next(answers))

    assert result == 0
    output = capsys.readouterr().out
    assert "GENREARCHIV CLI-STEUERUNG" in output
    for alias in ("garch-add", "garch-list", "garch-new", "garch-mode"):
        assert alias in output
    for spec in STANDARD_ARCHIVE_ALIASES:
        assert spec.name in output


def test_archive_alias_writes_to_shared_database_and_uses_duplicate_rules(tmp_path: Path, capsys):
    database = tmp_path / "archive.sqlite3"
    log_file = tmp_path / "archive.log"

    result = dispatch_alias(
        "garch-gen",
        [
            "--database",
            str(database),
            "--log-file",
            str(log_file),
            "--category",
            "Test",
            "--value",
            "Fantasy, fantasy, Horror",
            "--yes",
        ],
    )

    assert result == 0
    assert {item.value for item in ArchiveService(database).list_entries("genres")} == {
        "Fantasy",
        "Horror",
    }
    assert "Gespeichert: 2" in capsys.readouterr().out


def test_mode_alias_changes_only_requested_archive(tmp_path: Path):
    database = tmp_path / "archive.sqlite3"
    log_file = tmp_path / "archive.log"

    result = dispatch_alias(
        "garch-mode",
        [
            "--database",
            str(database),
            "--log-file",
            str(log_file),
            "genres",
            "whole",
        ],
    )

    assert result == 0
    service = ArchiveService(database)
    assert service.get_archive("genres").split_on_comma is False
    assert service.get_archive("stimmungen").split_on_comma is True


def test_custom_archives_receive_collision_safe_dynamic_alias(tmp_path: Path):
    service = _service(tmp_path)
    archive = service.create_archive(
        "Technische Ideen",
        "Technik",
        split_on_comma=False,
        source="test",
    )

    specs = archive_alias_specs(service)

    assert any(
        item.name == "garch-a-technische-ideen" and item.target == archive.slug
        for item in specs
    )
    assert "garch-a-technische-ideen" in alias_table(service)


def test_alias_installer_creates_executable_wrappers_and_wrapper_runs(tmp_path: Path):
    service = _service(tmp_path)
    target = tmp_path / "bin"
    log_file = tmp_path / "wrapper.log"

    installed = install_aliases(
        service,
        target,
        project_root=PROJECT_ROOT,
        python_executable=sys.executable,
    )

    assert len(installed) == len(all_alias_specs(service))
    wrapper = target / "garch-list"
    assert wrapper.exists()
    assert os.stat(wrapper).st_mode & stat.S_IXUSR
    assert MANAGED_MARKER in wrapper.read_text(encoding="utf-8")

    completed = subprocess.run(
        [
            str(wrapper),
            "--database",
            str(service.database_path),
            "--log-file",
            str(log_file),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert completed.returncode == 0, completed.stderr
    assert "ARCHIVÜBERSICHT" in completed.stdout
    assert "Genres" in completed.stdout
    assert log_file.exists()


def test_installer_refuses_foreign_collision_without_force(tmp_path: Path):
    service = _service(tmp_path)
    target = tmp_path / "bin"
    target.mkdir()
    foreign = target / "garch"
    foreign.write_text("#!/bin/sh\necho fremd\n", encoding="utf-8")

    try:
        install_aliases(service, target)
    except ArchiveServiceError as exc:
        assert "fremde Dateien" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Fremde Aliasdatei wurde unerwartet überschrieben.")

    assert "echo fremd" in foreign.read_text(encoding="utf-8")


def test_refresh_removes_only_stale_managed_wrappers(tmp_path: Path):
    service = _service(tmp_path)
    target = tmp_path / "bin"
    target.mkdir()
    stale = target / "garch-a-entfernt"
    stale.write_text(f"#!/bin/sh\n{MANAGED_MARKER}\n", encoding="utf-8")
    foreign = target / "garch-private"
    foreign.write_text("privat", encoding="utf-8")

    install_aliases(service, target)

    assert not stale.exists()
    assert foreign.read_text(encoding="utf-8") == "privat"


def test_uninstall_removes_only_managed_aliases(tmp_path: Path):
    service = _service(tmp_path)
    target = tmp_path / "bin"
    install_aliases(service, target)
    foreign = target / "garch-private"
    foreign.write_text("privat", encoding="utf-8")

    removed = uninstall_aliases(target)

    assert removed
    assert not (target / "garch").exists()
    assert foreign.exists()


def test_unknown_alias_returns_clear_error(tmp_path: Path, capsys):
    result = dispatch_alias(
        "garch-unbekannt",
        [
            "--database",
            str(tmp_path / "archive.sqlite3"),
            "--log-file",
            str(tmp_path / "archive.log"),
        ],
    )

    assert result == 2
    assert "Unbekannter CLI-Alias" in capsys.readouterr().err


def test_function_aliases_cover_create_help_and_generic_add(tmp_path: Path, capsys):
    database = tmp_path / "archive.sqlite3"
    log_file = tmp_path / "archive.log"

    assert dispatch_alias(
        "garch-new",
        [
            "--database",
            str(database),
            "--log-file",
            str(log_file),
            "Technische Ideen",
            "--description",
            "Technik",
            "--split-mode",
            "whole",
        ],
    ) == 0
    assert ArchiveService(database).get_archive("technische-ideen").split_on_comma is False

    assert dispatch_alias(
        "garch-add",
        [
            "--database",
            str(database),
            "--log-file",
            str(log_file),
            "--archive",
            "linux",
            "--value",
            "grep, awk",
            "--yes",
        ],
    ) == 0
    assert {item.value for item in ArchiveService(database).list_entries("linux")} == {"grep", "awk"}

    assert dispatch_alias(
        "garch-help",
        ["--database", str(database), "--log-file", str(log_file)],
    ) == 0
    output = capsys.readouterr().out
    assert "GENREARCHIV CLI-ALIASE" in output
    assert "garch-a-technische-ideen" in output


def test_foreign_manifest_is_not_overwritten_or_removed(tmp_path: Path):
    service = _service(tmp_path)
    target = tmp_path / "bin"
    target.mkdir()
    manifest = target / ".garch-aliases.json"
    manifest.write_text('{"owner": "fremd"}\n', encoding="utf-8")

    try:
        install_aliases(service, target)
    except ArchiveServiceError as exc:
        assert ".garch-aliases.json" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Fremdes Manifest wurde unerwartet überschrieben.")

    uninstall_aliases(target)
    assert manifest.read_text(encoding="utf-8") == '{"owner": "fremd"}\n'


def test_alias_initialization_failure_returns_controlled_error(tmp_path: Path, capsys):
    invalid_log_path = tmp_path / "log-directory"
    invalid_log_path.mkdir()

    result = dispatch_alias(
        "garch-list",
        [
            "--database",
            str(tmp_path / "archive.sqlite3"),
            "--log-file",
            str(invalid_log_path),
        ],
    )

    assert result == 2
    assert "konnte nicht initialisiert werden" in capsys.readouterr().err


def test_documentation_lists_every_registered_alias(tmp_path: Path):
    service = _service(tmp_path)
    documentation = (PROJECT_ROOT / "docs" / "ARCHIV_MANAGER.md").read_text(encoding="utf-8")

    for spec in all_alias_specs(service):
        assert f"`{spec.name}`" in documentation or spec.name in documentation
