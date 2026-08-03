from __future__ import annotations

import sys
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1] / "modules" / "archiv_manager"
sys.path.insert(0, str(MODULE_DIR))

from service import ArchiveService  # noqa: E402
from storage import DEFAULT_ARCHIVES  # noqa: E402


def test_seven_default_archives_are_seeded(tmp_path: Path):
    service = ArchiveService(tmp_path / "archive.sqlite3")
    archives = service.list_archives()
    assert len(archives) == 7
    assert {archive.name for archive in archives} == {
        "Genres", "Stimmungen", "Besondere Effekte", "Favoriten",
        "Basis-Entwicklungs-Strukturen", "Brainstorm", "Linux",
    }
    assert all(archive.is_default for archive in archives)
    assert len(DEFAULT_ARCHIVES) == 7
    for archive in archives:
        assert service.list_categories(archive.id) == ["Allgemein"]


def test_comma_mode_splits_and_ignores_case_insensitive_duplicates(tmp_path: Path):
    service = ArchiveService(tmp_path / "archive.sqlite3")
    first = service.add_text(
        "genres", "Fantasy, Horror, fantasy, HORROR",
        category="Erzählformen", source="test",
    )
    second = service.add_text(
        "genres", "FANTASY, Science-Fiction", category="Weitere", source="test"
    )
    assert [entry.value for entry in first.inserted] == ["Fantasy", "Horror"]
    assert set(first.duplicates) == {"fantasy", "HORROR"}
    assert [entry.value for entry in second.inserted] == ["Science-Fiction"]
    assert second.duplicates == ("FANTASY",)
    assert {entry.value for entry in service.list_entries("genres")} == {
        "Fantasy", "Horror", "Science-Fiction"
    }


def test_whole_text_mode_keeps_commas_inside_one_entry(tmp_path: Path):
    service = ArchiveService(tmp_path / "archive.sqlite3")
    result = service.add_text(
        "brainstorm", "Erster Gedanke, zweiter Gedanke, offene Frage",
        category="Ideen", source="test",
    )
    assert len(result.inserted) == 1
    assert result.inserted[0].value == "Erster Gedanke, zweiter Gedanke, offene Frage"


def test_archive_mode_can_be_changed_individually(tmp_path: Path):
    service = ArchiveService(tmp_path / "archive.sqlite3")
    brainstorm = service.get_archive("brainstorm")
    assert brainstorm.split_on_comma is False
    updated = service.update_archive(brainstorm.id, split_on_comma=True, source="test")
    result = service.add_text(updated.id, "Idee A, Idee B", category="Allgemein", source="test")
    assert updated.split_on_comma is True
    assert [entry.value for entry in result.inserted] == ["Idee A", "Idee B"]


def test_spelling_suggestion_is_visible_and_only_applied_when_requested(tmp_path: Path):
    service = ArchiveService(tmp_path / "archive.sqlite3")
    _archive, preview = service.prepare_add("besondere-effekte", "Efekte", apply_spelling=False)
    assert preview[0].value == "Efekte"
    assert preview[0].spelling is not None
    assert preview[0].spelling.suggested == "Effekte"
    result = service.add_text(
        "besondere-effekte", "Efekte", category="Visuell", source="test", apply_spelling=True
    )
    assert result.inserted[0].value == "Effekte"


def test_custom_archive_and_all_writes_are_audited(tmp_path: Path):
    service = ArchiveService(tmp_path / "archive.sqlite3")
    archive = service.create_archive(
        "Technische Ideen", "Wiederverwendbare Lösungen",
        split_on_comma=False, source="test",
    )
    service.add_text(archive.id, "Caching, Retry und Logging", category="Backend", source="test")
    entry = service.list_entries(archive.id)[0]
    service.update_entry(entry.id, value="Caching und Retry", category="Backend", source="test")
    actions = [event.action for event in service.repository.list_audit_events()]
    assert "archive_created" in actions
    assert "entries_added" in actions
    assert "entry_updated" in actions
