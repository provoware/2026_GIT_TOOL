from __future__ import annotations

import sys
from pathlib import Path

import pytest

MODULE_DIR = Path(__file__).resolve().parents[1] / "modules" / "datei_manager"
sys.path.insert(0, str(MODULE_DIR))

from browser import (  # noqa: E402
    BrowserError,
    IMAGE_SUFFIXES,
    build_preview_plan,
    fit_inside,
    format_size,
    list_directory,
    sort_entries,
)


def test_list_directory_returns_metadata_and_hides_dotfiles(tmp_path: Path):
    folder = tmp_path / "Bilder"
    folder.mkdir()
    visible = tmp_path / "urlaub.jpg"
    visible.write_bytes(b"x" * 2048)
    hidden = tmp_path / ".intern.png"
    hidden.write_bytes(b"x")

    entries = list_directory(tmp_path)
    names = {entry.name for entry in entries}

    assert names == {"Bilder", "urlaub.jpg"}
    image = next(entry for entry in entries if entry.name == "urlaub.jpg")
    assert image.is_image is True
    assert image.type_label == "JPG"
    assert image.size_label == "2.0 KB"

    with_hidden = list_directory(tmp_path, show_hidden=True)
    assert {entry.name for entry in with_hidden} == {"Bilder", "urlaub.jpg", ".intern.png"}


def test_sort_entries_keeps_directories_first_and_toggles_direction(tmp_path: Path):
    (tmp_path / "z_ordner").mkdir()
    (tmp_path / "a_ordner").mkdir()
    (tmp_path / "z.txt").write_bytes(b"z")
    (tmp_path / "a.txt").write_bytes(b"a" * 50)
    entries = list_directory(tmp_path)

    ascending = sort_entries(entries, sort_by="name")
    descending = sort_entries(entries, sort_by="name", descending=True)
    by_size = sort_entries(entries, sort_by="size", descending=True)

    assert [entry.name for entry in ascending] == ["a_ordner", "z_ordner", "a.txt", "z.txt"]
    assert [entry.name for entry in descending] == ["z_ordner", "a_ordner", "z.txt", "a.txt"]
    assert [entry.name for entry in by_size][-2:] == ["a.txt", "z.txt"]


def test_fit_inside_preserves_ratio_without_unwanted_upscale():
    assert fit_inside(4000, 2000, 800, 600) == (800, 400)
    assert fit_inside(1000, 2000, 600, 600) == (300, 600)
    assert fit_inside(200, 100, 800, 600) == (200, 100)
    assert fit_inside(200, 100, 800, 600, allow_upscale=True) == (800, 400)


def test_preview_plan_distinguishes_images_and_other_files(tmp_path: Path):
    image = tmp_path / "motiv.webp"
    image.write_bytes(b"placeholder")
    text = tmp_path / "notiz.txt"
    text.write_text("Text", encoding="utf-8")

    image_plan = build_preview_plan(
        image,
        source_size=(2400, 1600),
        available_width=900,
        available_height=700,
    )
    text_plan = build_preview_plan(
        text,
        source_size=None,
        available_width=900,
        available_height=700,
    )

    assert image_plan.supported is True
    assert (image_plan.target_width, image_plan.target_height) == (900, 600)
    assert text_plan.supported is False
    assert text_plan.target_width == 0


def test_supported_formats_include_common_photo_and_web_types():
    assert {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"} <= IMAGE_SUFFIXES


def test_invalid_inputs_fail_early(tmp_path: Path):
    with pytest.raises(BrowserError, match="Ordnerpfad"):
        list_directory("")
    with pytest.raises(BrowserError):
        list_directory(tmp_path / "fehlt")
    with pytest.raises(BrowserError):
        sort_entries([], sort_by="unknown")
    with pytest.raises(BrowserError):
        fit_inside(0, 100, 500, 500)
    with pytest.raises(BrowserError):
        format_size(-1)
