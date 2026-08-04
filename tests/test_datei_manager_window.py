from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.datei_manager.window import FileManagerWindow  # noqa: E402


def test_window_shows_sortable_list_and_large_image_preview(tmp_path: Path):
    import tkinter as tk

    (tmp_path / "Unterordner").mkdir()
    image_path = tmp_path / "beispiel.jpg"
    Image.new("RGB", (1600, 900), (40, 90, 160)).save(image_path, quality=90)
    (tmp_path / "notiz.txt").write_text("Vorschautest", encoding="utf-8")

    root = tk.Tk()
    try:
        root.geometry("1200x720+0+0")
        app = FileManagerWindow(root, initial_path=tmp_path)
        root.update_idletasks()
        root.update()

        assert len(app.tree.get_children()) == 3
        assert app.preview_canvas.winfo_width() >= 420
        assert app.preview_canvas.winfo_height() >= 400
        assert "▲" in app.tree.heading("#0")["text"]

        app.set_sort("size")
        root.update_idletasks()
        assert "▲" in app.tree.heading("size")["text"]
        app.set_sort("size")
        assert "▼" in app.tree.heading("size")["text"]

        image_item = next(
            item_id
            for item_id, entry in app.entry_by_id.items()
            if entry.path == image_path
        )
        app.tree.selection_set(image_item)
        app._on_selection()
        root.update_idletasks()
        root.update()

        assert app._preview_source is not None
        assert app._preview_photo is not None
        assert app.preview_title_var.get() == "beispiel.jpg"
        assert "1600 × 900" in app.preview_meta_var.get()
        assert app.preview_canvas.find_all()
    finally:
        root.destroy()


def test_directory_double_click_contract_opens_selected_folder(tmp_path: Path):
    import tkinter as tk

    child = tmp_path / "Unterordner"
    child.mkdir()
    (child / "datei.txt").write_text("Inhalt", encoding="utf-8")

    root = tk.Tk()
    try:
        app = FileManagerWindow(root, initial_path=tmp_path)
        root.update_idletasks()
        folder_item = next(
            item_id
            for item_id, entry in app.entry_by_id.items()
            if entry.path == child
        )
        app.tree.selection_set(folder_item)
        app._on_double_click()
        root.update_idletasks()

        assert app.current_path == child.resolve()
        assert app.path_var.get() == str(child.resolve())
        assert len(app.tree.get_children()) == 1
    finally:
        root.destroy()
