#!/usr/bin/env python3
"""Erzeugt einen Screenshotbeleg der sortierbaren Liste und Bildvorschau."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "modules" / "datei_manager"
sys.path.insert(0, str(MODULE_DIR))

from window import FileManagerWindow  # noqa: E402


def _sample_image(path: Path) -> None:
    image = Image.new("RGB", (1800, 1100), (28, 42, 64))
    draw = ImageDraw.Draw(image)
    draw.rectangle((100, 100, 1700, 1000), outline=(245, 158, 11), width=18)
    draw.text((160, 170), "Genrearchiv – Bildvorschau", fill=(248, 250, 252))
    draw.text((160, 250), "Sortierbare Listenansicht · große Detailfläche", fill=(203, 213, 225))
    image.save(path, quality=92)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    import tkinter as tk

    with tempfile.TemporaryDirectory(prefix="datei-manager-preview-") as temp_dir:
        folder = Path(temp_dir)
        image_path = folder / "bildvorschau.jpg"
        _sample_image(image_path)
        (folder / "Dokumente").mkdir()
        (folder / "notizen.txt").write_text("Datei-Manager Test", encoding="utf-8")

        root = tk.Tk()
        root.geometry("1280x760+0+0")
        app = FileManagerWindow(root, initial_path=folder)
        root.update_idletasks()
        root.update()
        image_item = next(
            item_id
            for item_id, entry in app.entry_by_id.items()
            if entry.path == image_path
        )
        app.tree.selection_set(image_item)
        app._on_selection()
        root.update_idletasks()
        root.update()

        args.output.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["/usr/bin/import", "-window", str(root.winfo_id()), str(args.output)],
            check=True,
            timeout=20,
        )
        root.destroy()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
