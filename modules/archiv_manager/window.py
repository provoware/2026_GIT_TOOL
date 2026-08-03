"""Tkinter-Oberfläche für strukturierte, gemeinsam gespeicherte Archive."""

from __future__ import annotations

import logging
from pathlib import Path

try:
    from .service import ArchiveService, ArchiveServiceError, ArchiveStorageError
except ImportError:
    from service import ArchiveService, ArchiveServiceError, ArchiveStorageError


class ArchiveManagerWindow:
    """Archiv-, Kategorie- und Eintragsverwaltung auf der gemeinsamen Datenbank."""

    def __init__(self, root, *, service: ArchiveService) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.root = root
        self.service = service
        self.tk = tk
        self.ttk = ttk
        self.archives_by_item: dict[str, object] = {}
        self.entries_by_item: dict[str, object] = {}
        self.current_archive = None
        self._filter_after_id: str | None = None

        self.search_var = tk.StringVar()
        self.category_filter_var = tk.StringVar(value="Alle Kategorien")
        self.split_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Bereit.")
        self.archive_title_var = tk.StringVar(value="Archiv auswählen")
        self.archive_description_var = tk.StringVar(
            value="GUI und CLI verwenden dieselbe Archivdatenbank."
        )
        self.mode_info_var = tk.StringVar()

        root.title("Genrearchiv – Archiv-Verwaltung")
        root.geometry("1280x760")
        root.minsize(940, 620)
        self._build_ui()
        self._bind_shortcuts()
        self.refresh_archives()

    def _build_ui(self) -> None:
        ttk = self.ttk
        header = ttk.Frame(self.root, padding=(16, 12))
        header.pack(fill="x")
        ttk.Label(header, text="Archiv-Verwaltung", font=("TkDefaultFont", 17, "bold")).pack(anchor="w")
        ttk.Label(
            header,
            text=(
                "Strukturierte Archive für GUI und CLI. Duplikate werden archivweit "
                "ohne Beachtung der Groß- und Kleinschreibung erkannt."
            ),
            wraplength=1080,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        pane = ttk.Panedwindow(self.root, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        left = ttk.Frame(pane, padding=(0, 4, 10, 4))
        right = ttk.Frame(pane, padding=(10, 4, 0, 4))
        pane.add(left, weight=2)
        pane.add(right, weight=5)

        ttk.Label(left, text="Archive", font=("TkDefaultFont", 12, "bold")).pack(anchor="w", pady=(0, 6))
        self.archive_tree = ttk.Treeview(
            left, columns=("count", "mode"), show="tree headings", selectmode="browse"
        )
        for column, title, width in (("#0", "Name", 210), ("count", "Einträge", 75), ("mode", "Modus", 80)):
            self.archive_tree.heading(column, text=title)
            self.archive_tree.column(column, width=width, minwidth=65, stretch=column == "#0")
        self.archive_tree.pack(fill="both", expand=True)
        self.archive_tree.bind("<<TreeviewSelect>>", self._on_archive_selected)
        buttons = ttk.Frame(left)
        buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(buttons, text="Neues Archiv", command=self.create_archive_dialog).pack(side="left")
        ttk.Button(buttons, text="Bearbeiten", command=self.edit_archive_dialog).pack(side="left", padx=6)
        ttk.Button(buttons, text="Löschen", command=self.delete_archive).pack(side="left")

        title = ttk.Frame(right)
        title.pack(fill="x")
        ttk.Label(title, textvariable=self.archive_title_var, font=("TkDefaultFont", 15, "bold")).pack(side="left", fill="x", expand=True)
        ttk.Button(title, text="↻ Aktualisieren", command=self.refresh_all).pack(side="right")
        ttk.Label(right, textvariable=self.archive_description_var, wraplength=820, justify="left").pack(fill="x", pady=(4, 8))

        mode = ttk.LabelFrame(right, text="Eingabeverhalten", padding=(10, 8))
        mode.pack(fill="x", pady=(0, 10))
        self.split_check = ttk.Checkbutton(
            mode,
            text="Komma trennt einzelne Einträge",
            variable=self.split_var,
            command=self._on_split_changed,
        )
        self.split_check.pack(anchor="w")
        ttk.Label(mode, textvariable=self.mode_info_var, wraplength=790, justify="left").pack(anchor="w", pady=(3, 0))

        filters = ttk.Frame(right)
        filters.pack(fill="x", pady=(0, 8))
        ttk.Label(filters, text="Suche:").pack(side="left")
        self.search_entry = ttk.Entry(filters, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(6, 12))
        ttk.Label(filters, text="Kategorie:").pack(side="left")
        self.category_filter = ttk.Combobox(
            filters, textvariable=self.category_filter_var, state="readonly", width=24
        )
        self.category_filter.pack(side="left", padx=(6, 0))
        self.category_filter.bind("<<ComboboxSelected>>", lambda _event: self.refresh_entries())
        self.search_var.trace_add("write", self._schedule_filter)

        tree_frame = ttk.Frame(right)
        tree_frame.pack(fill="both", expand=True)
        self.entry_tree = ttk.Treeview(
            tree_frame,
            columns=("category", "source", "updated"),
            show="tree headings",
            selectmode="browse",
        )
        settings = (
            ("#0", "Eintrag", 420, True),
            ("category", "Kategorie", 180, False),
            ("source", "Quelle", 85, False),
            ("updated", "Geändert", 190, False),
        )
        for column, title_text, width, stretch in settings:
            self.entry_tree.heading(column, text=title_text)
            self.entry_tree.column(column, width=width, minwidth=70, stretch=stretch)
        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.entry_tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.entry_tree.xview)
        self.entry_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.entry_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        self.entry_tree.bind("<Double-1>", lambda _event: self.edit_entry_dialog())

        entry_buttons = ttk.Frame(right)
        entry_buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(entry_buttons, text="Eintrag hinzufügen", command=self.add_entry_dialog).pack(side="left")
        ttk.Button(entry_buttons, text="Eintrag bearbeiten", command=self.edit_entry_dialog).pack(side="left", padx=6)
        ttk.Button(entry_buttons, text="Eintrag löschen", command=self.delete_entry).pack(side="left")
        ttk.Button(entry_buttons, text="CLI-Hilfe", command=self.show_cli_help).pack(side="right")
        ttk.Label(self.root, textvariable=self.status_var, anchor="w", padding=(16, 6)).pack(fill="x")

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Control-n>", lambda _event: self.add_entry_dialog())
        self.root.bind("<Control-f>", lambda _event: self._focus_search())
        self.root.bind("<F5>", lambda _event: self.refresh_all())
        self.root.bind("<Delete>", lambda _event: self.delete_entry())
        self.root.bind("<F1>", lambda _event: self.show_cli_help())

    def _focus_search(self) -> str:
        self.search_entry.focus_set()
        self.search_entry.selection_range(0, "end")
        return "break"

    def refresh_all(self) -> None:
        selected_id = self.current_archive.id if self.current_archive else None
        self.refresh_archives(selected_id=selected_id)

    def refresh_archives(self, *, selected_id: int | None = None) -> None:
        archives = self.service.list_archives()
        self.archive_tree.delete(*self.archive_tree.get_children())
        self.archives_by_item.clear()
        for archive in archives:
            item_id = f"archive-{archive.id}"
            self.archive_tree.insert(
                "", "end", iid=item_id, text=archive.name,
                values=(len(self.service.list_entries(archive.id)), "Komma" if archive.split_on_comma else "Gesamt"),
            )
            self.archives_by_item[item_id] = archive
        if archives:
            target = f"archive-{selected_id}" if selected_id else f"archive-{archives[0].id}"
            if target not in self.archives_by_item:
                target = f"archive-{archives[0].id}"
            self.archive_tree.selection_set(target)
            self.archive_tree.see(target)
            self._on_archive_selected()

    def _on_archive_selected(self, _event=None) -> None:
        selected = self.archive_tree.selection()
        if not selected:
            return
        self.current_archive = self.archives_by_item[selected[0]]
        self.archive_title_var.set(self.current_archive.name)
        self.archive_description_var.set(self.current_archive.description)
        self.split_var.set(self.current_archive.split_on_comma)
        self._update_mode_info()
        categories = ["Alle Kategorien", *self.service.list_categories(self.current_archive.id)]
        self.category_filter["values"] = categories
        if self.category_filter_var.get() not in categories:
            self.category_filter_var.set("Alle Kategorien")
        self.refresh_entries()

    def _update_mode_info(self) -> None:
        self.mode_info_var.set(
            "Jedes Komma trennt einen eigenen Eintrag."
            if self.split_var.get()
            else "Die vollständige Eingabe wird als ein zusammenhängender Eintrag gespeichert."
        )

    def _on_split_changed(self) -> None:
        if self.current_archive is None:
            return
        try:
            self.current_archive = self.service.update_archive(
                self.current_archive.id,
                split_on_comma=bool(self.split_var.get()),
                source="gui",
            )
            self._update_mode_info()
            self.refresh_archives(selected_id=self.current_archive.id)
            self._set_status("Eingabemodus gespeichert.")
        except ArchiveStorageError as exc:
            self.split_var.set(self.current_archive.split_on_comma)
            self._show_error(str(exc))

    def _schedule_filter(self, *_args) -> None:
        if self._filter_after_id is not None:
            try:
                self.root.after_cancel(self._filter_after_id)
            except Exception:
                pass
        self._filter_after_id = self.root.after(120, self.refresh_entries)

    def refresh_entries(self) -> None:
        self._filter_after_id = None
        self.entry_tree.delete(*self.entry_tree.get_children())
        self.entries_by_item.clear()
        if self.current_archive is None:
            return
        entries = self.service.list_entries(
            self.current_archive.id,
            category=self.category_filter_var.get(),
            query=self.search_var.get(),
        )
        for entry in entries:
            item_id = f"entry-{entry.id}"
            self.entry_tree.insert(
                "", "end", iid=item_id, text=entry.value,
                values=(entry.category, entry.source, entry.updated_at),
            )
            self.entries_by_item[item_id] = entry
        self._set_status(f"{len(entries)} sichtbare Einträge in {self.current_archive.name}.")

    def _selected_entry(self):
        selected = self.entry_tree.selection()
        return self.entries_by_item.get(selected[0]) if selected else None

    def add_entry_dialog(self) -> str:
        from tkinter import messagebox, simpledialog
        if self.current_archive is None:
            self._show_error("Bitte zuerst ein Archiv auswählen.")
            return "break"
        category = simpledialog.askstring(
            "Kategorie", "Kategorie oder leer für Allgemein:", parent=self.root,
            initialvalue="Allgemein",
        )
        if category is None:
            return "break"
        raw_text = simpledialog.askstring(
            f"Eintrag – {self.current_archive.name}",
            self.current_archive.description + "\n\n" + self.mode_info_var.get()
            + "\nDuplikate werden unabhängig von Groß- und Kleinschreibung ignoriert.",
            parent=self.root,
        )
        if raw_text is None:
            return "break"
        try:
            _archive, prepared = self.service.prepare_add(self.current_archive.id, raw_text)
            suggestions = [item.spelling for item in prepared if item.spelling is not None]
            apply_spelling = False
            if suggestions:
                preview = "\n".join(f"• {item.original} → {item.suggested}" for item in suggestions[:8])
                apply_spelling = messagebox.askyesno(
                    "Rechtschreibhinweise", f"{preview}\n\nVorschläge übernehmen?", parent=self.root
                )
            result = self.service.add_text(
                self.current_archive.id, raw_text,
                category=category or "Allgemein", source="gui",
                apply_spelling=apply_spelling,
            )
            self.refresh_archives(selected_id=self.current_archive.id)
            self._set_status(f"{len(result.inserted)} gespeichert; {len(result.duplicates)} Duplikate ignoriert.")
        except (ArchiveStorageError, ArchiveServiceError) as exc:
            self._show_error(str(exc))
        return "break"

    def edit_entry_dialog(self) -> str:
        from tkinter import simpledialog
        entry = self._selected_entry()
        if entry is None:
            self._show_error("Bitte einen Eintrag auswählen.")
            return "break"
        category = simpledialog.askstring("Kategorie", "Kategorie:", initialvalue=entry.category, parent=self.root)
        if category is None:
            return "break"
        value = simpledialog.askstring("Eintrag bearbeiten", "Eintrag:", initialvalue=entry.value, parent=self.root)
        if value is None:
            return "break"
        try:
            self.service.update_entry(entry.id, value=value, category=category or "Allgemein", source="gui")
            self.refresh_archives(selected_id=entry.archive_id)
        except (ArchiveStorageError, ArchiveServiceError) as exc:
            self._show_error(str(exc))
        return "break"

    def delete_entry(self) -> str:
        from tkinter import messagebox
        entry = self._selected_entry()
        if entry is None or not messagebox.askyesno("Eintrag löschen", f"Eintrag löschen?\n\n{entry.value}", parent=self.root):
            return "break"
        try:
            self.service.delete_entry(entry.id, source="gui")
            self.refresh_archives(selected_id=entry.archive_id)
        except ArchiveStorageError as exc:
            self._show_error(str(exc))
        return "break"

    def create_archive_dialog(self) -> None:
        from tkinter import messagebox, simpledialog
        name = simpledialog.askstring("Neues Archiv", "Eindeutiger Archivname:", parent=self.root)
        if not name:
            return
        description = simpledialog.askstring("Beschreibung", "Archivzweck:", parent=self.root)
        if description is None:
            return
        split = messagebox.askyesno("Komma-Modus", "Soll jedes Komma einen Eintrag trennen?", parent=self.root)
        try:
            archive = self.service.create_archive(name, description, split_on_comma=split, source="gui")
            self.refresh_archives(selected_id=archive.id)
        except ArchiveStorageError as exc:
            self._show_error(str(exc))

    def edit_archive_dialog(self) -> None:
        from tkinter import simpledialog
        if self.current_archive is None:
            return
        name = simpledialog.askstring("Archiv bearbeiten", "Name:", initialvalue=self.current_archive.name, parent=self.root)
        if name is None:
            return
        description = simpledialog.askstring(
            "Archiv bearbeiten", "Beschreibung:", initialvalue=self.current_archive.description, parent=self.root
        )
        if description is None:
            return
        try:
            archive = self.service.update_archive(
                self.current_archive.id, name=name, description=description, source="gui"
            )
            self.refresh_archives(selected_id=archive.id)
        except ArchiveStorageError as exc:
            self._show_error(str(exc))

    def delete_archive(self) -> None:
        from tkinter import messagebox
        if self.current_archive is None:
            return
        if self.current_archive.is_default:
            self._show_error("Die sieben Standardarchive können nicht gelöscht werden.")
            return
        if not messagebox.askyesno(
            "Archiv löschen", f"Archiv '{self.current_archive.name}' samt Einträgen löschen?", parent=self.root
        ):
            return
        try:
            self.service.delete_archive(self.current_archive.id, source="gui")
            self.current_archive = None
            self.refresh_archives()
        except ArchiveStorageError as exc:
            self._show_error(str(exc))

    def show_cli_help(self) -> str:
        from tkinter import messagebox
        messagebox.showinfo(
            "CLI-Zugang",
            "Im Projektordner starten:\n\npython -m modules.archiv_manager\n\n"
            "Direkte Eingabe:\npython -m modules.archiv_manager --archive genres "
            "--category Allgemein --value \"Fantasy, Horror\" --yes\n\n"
            "Der Assistent nutzt dieselbe Datenbank wie dieses Fenster.",
            parent=self.root,
        )
        return "break"

    def _show_error(self, message: str) -> None:
        from tkinter import messagebox
        self._set_status(f"Fehler: {message}")
        messagebox.showerror("Archiv-Verwaltung", message, parent=self.root)

    def _set_status(self, message: str) -> None:
        self.status_var.set(message)


def open_window(parent=None, *, database_path: Path | str, logger: logging.Logger | None = None):
    import tkinter as tk
    owns_root = parent is None
    root = tk.Tk() if owns_root else tk.Toplevel(parent)
    app = ArchiveManagerWindow(root, service=ArchiveService(database_path, logger=logger))
    if owns_root:
        root.mainloop()
    return app
