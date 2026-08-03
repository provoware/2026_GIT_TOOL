from __future__ import annotations

import sys
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1] / "modules" / "archiv_manager"
sys.path.insert(0, str(MODULE_DIR))

from service import ArchiveService  # noqa: E402
from window import ArchiveManagerWindow  # noqa: E402


def test_window_loads_archives_filters_and_shared_entries(tmp_path: Path):
    import tkinter as tk

    service = ArchiveService(tmp_path / "archive.sqlite3")
    service.add_text("linux", "grep, find, awk", category="Befehle", source="test")
    root = tk.Tk()
    try:
        root.geometry("1100x700+0+0")
        app = ArchiveManagerWindow(root, service=service)
        root.update_idletasks()
        root.update()
        assert len(app.archive_tree.get_children()) == 7
        linux_item = next(
            item_id for item_id, archive in app.archives_by_item.items()
            if archive.slug == "linux"
        )
        app.archive_tree.selection_set(linux_item)
        app._on_archive_selected()
        root.update_idletasks()
        assert app.archive_title_var.get() == "Linux"
        assert app.split_var.get() is True
        assert len(app.entry_tree.get_children()) == 3
        assert "Befehle" in app.category_filter["values"]
        app.search_var.set("aw")
        app.refresh_entries()
        visible = app.entry_tree.get_children()
        assert len(visible) == 1
        assert app.entry_tree.item(visible[0], "text") == "awk"
    finally:
        root.destroy()
