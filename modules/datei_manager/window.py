"""Tkinter-Dateimanager mit sortierbarer Listenansicht und großer Bildvorschau."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    from .browser import BrowserError, FileEntry, list_directory, sort_entries
except ImportError:  # direkter Start als Skript
    from browser import BrowserError, FileEntry, list_directory, sort_entries


class FileManagerWindowError(RuntimeError):
    """Die Dateimanager-Oberfläche konnte nicht aufgebaut oder aktualisiert werden."""


class FileManagerWindow:
    COLUMNS = ("type", "size", "modified")
    HEADINGS = {
        "#0": "Name",
        "type": "Typ",
        "size": "Größe",
        "modified": "Geändert",
    }

    def __init__(self, root, *, initial_path: Path | str | None = None) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.root = root
        self.tk = tk
        self.ttk = ttk
        self.current_path = Path(initial_path or Path.home()).expanduser()
        self.entries: list[FileEntry] = []
        self.entry_by_id: dict[str, FileEntry] = {}
        self.sort_by = "name"
        self.sort_descending = False
        self._preview_source = None
        self._preview_photo = None
        self._preview_path: Path | None = None
        self._preview_after_id: str | None = None

        self.path_var = tk.StringVar(value=str(self.current_path))
        self.show_hidden_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Bereit.")
        self.preview_title_var = tk.StringVar(value="Keine Datei ausgewählt")
        self.preview_meta_var = tk.StringVar(
            value="Wähle links eine Bilddatei aus. Die Vorschau passt sich automatisch an."
        )

        self.root.title("Genrearchiv – Datei-Manager")
        self.root.geometry("1280x760")
        self.root.minsize(900, 600)
        self._build_ui()
        self._bind_shortcuts()
        self.open_directory(self.current_path)

    def _build_ui(self) -> None:
        tk = self.tk
        ttk = self.ttk

        toolbar = ttk.Frame(self.root, padding=(12, 10))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="↑ Übergeordnet", command=self.go_up).pack(side="left")
        ttk.Button(toolbar, text="↻ Aktualisieren", command=self.refresh).pack(
            side="left", padx=(8, 12)
        )
        ttk.Label(toolbar, text="Ordner:").pack(side="left")
        path_entry = ttk.Entry(toolbar, textvariable=self.path_var)
        path_entry.pack(side="left", fill="x", expand=True, padx=(8, 8))
        path_entry.bind("<Return>", lambda _event: self.open_directory(self.path_var.get()))
        ttk.Button(toolbar, text="Öffnen", command=lambda: self.open_directory(self.path_var.get())).pack(
            side="left"
        )
        ttk.Checkbutton(
            toolbar,
            text="Versteckte Dateien",
            variable=self.show_hidden_var,
            command=self.refresh,
        ).pack(side="left", padx=(12, 0))

        pane = ttk.Panedwindow(self.root, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        list_frame = ttk.Frame(pane)
        preview_frame = ttk.Frame(pane, padding=(12, 8))
        pane.add(list_frame, weight=3)
        pane.add(preview_frame, weight=4)

        tree_container = ttk.Frame(list_frame)
        tree_container.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(
            tree_container,
            columns=self.COLUMNS,
            show="tree headings",
            selectmode="browse",
        )
        self.tree.heading("#0", command=lambda: self.set_sort("name"))
        self.tree.heading("type", command=lambda: self.set_sort("type"))
        self.tree.heading("size", command=lambda: self.set_sort("size"))
        self.tree.heading("modified", command=lambda: self.set_sort("modified"))
        self.tree.column("#0", width=360, minwidth=180, stretch=True, anchor="w")
        self.tree.column("type", width=100, minwidth=80, stretch=False, anchor="w")
        self.tree.column("size", width=110, minwidth=90, stretch=False, anchor="e")
        self.tree.column("modified", width=155, minwidth=135, stretch=False, anchor="w")

        y_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self._on_selection)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Return>", self._on_enter)

        ttk.Label(
            preview_frame,
            textvariable=self.preview_title_var,
            font=("TkDefaultFont", 13, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        canvas_frame = ttk.Frame(preview_frame, relief="sunken", borderwidth=1)
        canvas_frame.pack(fill="both", expand=True)
        self.preview_canvas = tk.Canvas(
            canvas_frame,
            background="#111827",
            highlightthickness=0,
            width=560,
            height=520,
        )
        self.preview_canvas.pack(fill="both", expand=True)
        self.preview_canvas.bind("<Configure>", self._schedule_preview_render)

        ttk.Label(
            preview_frame,
            textvariable=self.preview_meta_var,
            anchor="w",
            justify="left",
            wraplength=620,
        ).pack(fill="x", pady=(10, 0))

        status = ttk.Label(self.root, textvariable=self.status_var, anchor="w", padding=(12, 6))
        status.pack(fill="x")
        self._update_headings()

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Control-r>", lambda _event: self.refresh())
        self.root.bind("<F5>", lambda _event: self.refresh())
        self.root.bind("<BackSpace>", lambda _event: self.go_up())
        self.root.bind("<Alt-Up>", lambda _event: self.go_up())

    def open_directory(self, path: Path | str) -> None:
        candidate = Path(path).expanduser()
        try:
            entries = list_directory(candidate, show_hidden=bool(self.show_hidden_var.get()))
            candidate = candidate.resolve(strict=True)
        except BrowserError as exc:
            self._set_status(str(exc), error=True)
            return
        self.current_path = candidate
        self.path_var.set(str(candidate))
        self.entries = entries
        self._render_entries()
        self._clear_preview("Keine Datei ausgewählt")
        self._set_status(f"{len(entries)} Einträge in {candidate}")

    def refresh(self) -> None:
        self.open_directory(self.current_path)

    def go_up(self) -> None:
        parent = self.current_path.parent
        self.open_directory(parent)

    def set_sort(self, sort_by: str) -> None:
        if self.sort_by == sort_by:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_by = sort_by
            self.sort_descending = False
        self._render_entries()

    def _render_entries(self) -> None:
        selected_path = self._selected_entry().path if self._selected_entry() else None
        ordered = sort_entries(
            self.entries,
            sort_by=self.sort_by,
            descending=self.sort_descending,
            directories_first=True,
        )
        self.tree.delete(*self.tree.get_children())
        self.entry_by_id.clear()
        selected_id = None
        for index, entry in enumerate(ordered):
            item_id = f"entry-{index}"
            icon = "📁 " if entry.is_directory else "🖼 " if entry.is_image else "📄 "
            self.tree.insert(
                "",
                "end",
                iid=item_id,
                text=f"{icon}{entry.name}",
                values=(entry.type_label, entry.size_label, entry.modified_label),
            )
            self.entry_by_id[item_id] = entry
            if selected_path is not None and entry.path == selected_path:
                selected_id = item_id
        if selected_id is not None:
            self.tree.selection_set(selected_id)
            self.tree.see(selected_id)
        self._update_headings()

    def _update_headings(self) -> None:
        active = {
            "name": "#0",
            "type": "type",
            "size": "size",
            "modified": "modified",
        }[self.sort_by]
        indicator = " ▼" if self.sort_descending else " ▲"
        for column, label in self.HEADINGS.items():
            self.tree.heading(column, text=label + (indicator if column == active else ""))

    def _selected_entry(self) -> FileEntry | None:
        selected = self.tree.selection()
        if not selected:
            return None
        return self.entry_by_id.get(selected[0])

    def _on_selection(self, _event=None) -> None:
        entry = self._selected_entry()
        if entry is None:
            self._clear_preview("Keine Datei ausgewählt")
            return
        if entry.is_directory:
            self._clear_preview(entry.name, "Ordner – Doppelklick oder Enter zum Öffnen.")
            return
        if entry.is_image:
            self._load_image(entry)
            return
        self._clear_preview(
            entry.name,
            f"{entry.type_label} · {entry.size_label} · geändert {entry.modified_label}\n"
            "Für diesen Dateityp ist keine Bildvorschau verfügbar.",
        )

    def _on_double_click(self, _event=None) -> None:
        entry = self._selected_entry()
        if entry is not None and entry.is_directory:
            self.open_directory(entry.path)

    def _on_enter(self, _event=None) -> str:
        entry = self._selected_entry()
        if entry is not None and entry.is_directory:
            self.open_directory(entry.path)
        elif entry is not None:
            self._on_selection()
        return "break"

    def _load_image(self, entry: FileEntry) -> None:
        try:
            from PIL import Image, ImageOps, UnidentifiedImageError
        except ImportError:
            self._clear_preview(
                entry.name,
                "Bild erkannt, aber Pillow ist nicht installiert. Installiere die Projektabhängigkeiten.",
            )
            self._set_status("Bildvorschau benötigt Pillow.", error=True)
            return

        try:
            Image.MAX_IMAGE_PIXELS = 80_000_000
            with Image.open(entry.path) as opened:
                image = ImageOps.exif_transpose(opened)
                self._preview_source = image.convert("RGBA").copy()
                source_width, source_height = self._preview_source.size
                mode = opened.mode
                image_format = opened.format or entry.type_label
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
            self._clear_preview(entry.name, f"Bild konnte nicht geladen werden: {exc}")
            self._set_status(f"Vorschau fehlgeschlagen: {entry.name}", error=True)
            return

        self._preview_path = entry.path
        self.preview_title_var.set(entry.name)
        self.preview_meta_var.set(
            f"{image_format} · {source_width} × {source_height} Pixel · {mode} · "
            f"{entry.size_label}\nDie Vorschau nutzt den verfügbaren Bereich, ohne das Bild zu verzerren."
        )
        self._render_preview()
        self._set_status(f"Vorschau geladen: {entry.name}")

    def _schedule_preview_render(self, _event=None) -> None:
        if self._preview_source is None:
            return
        if self._preview_after_id is not None:
            try:
                self.root.after_cancel(self._preview_after_id)
            except Exception:
                pass
        self._preview_after_id = self.root.after(120, self._render_preview)

    def _render_preview(self) -> None:
        if self._preview_source is None:
            return
        try:
            from PIL import Image, ImageTk
        except ImportError:
            return
        self._preview_after_id = None
        available_width = max(self.preview_canvas.winfo_width() - 24, 1)
        available_height = max(self.preview_canvas.winfo_height() - 24, 1)
        image = self._preview_source.copy()
        image.thumbnail((available_width, available_height), Image.Resampling.LANCZOS)
        self._preview_photo = ImageTk.PhotoImage(image)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(
            self.preview_canvas.winfo_width() // 2,
            self.preview_canvas.winfo_height() // 2,
            image=self._preview_photo,
            anchor="center",
        )

    def _clear_preview(self, title: str, message: str | None = None) -> None:
        self._preview_source = None
        self._preview_photo = None
        self._preview_path = None
        self.preview_canvas.delete("all")
        self.preview_canvas.create_text(
            max(self.preview_canvas.winfo_width() // 2, 200),
            max(self.preview_canvas.winfo_height() // 2, 180),
            text="Keine Bildvorschau",
            fill="#e5e7eb",
            font=("TkDefaultFont", 16, "bold"),
        )
        self.preview_title_var.set(title)
        self.preview_meta_var.set(message or "Wähle links eine Bilddatei aus.")

    def _set_status(self, message: str, *, error: bool = False) -> None:
        prefix = "Fehler: " if error else ""
        self.status_var.set(prefix + message)


def open_window(parent=None, *, initial_path: Path | str | None = None):
    """Öffnet den Datei-Manager als Toplevel oder eigenständiges Fenster."""
    import tkinter as tk

    owns_root = parent is None
    root = tk.Tk() if owns_root else tk.Toplevel(parent)
    app = FileManagerWindow(root, initial_path=initial_path)
    if owns_root:
        root.mainloop()
    return app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Datei-Manager mit Bildvorschau.")
    parser.add_argument("path", nargs="?", type=Path, default=Path.home())
    args = parser.parse_args(argv)
    open_window(initial_path=args.path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
