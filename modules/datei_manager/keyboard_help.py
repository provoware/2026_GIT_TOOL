"""Kleine, zentral gepflegte Tastaturhilfe für den Datei-Manager."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShortcutHelp:
    keys: str
    action: str


SHORTCUT_HELP = (
    ShortcutHelp("F1", "Diese Kurzhilfe öffnen"),
    ShortcutHelp("Enter", "Ausgewählten Ordner öffnen oder Vorschau aktualisieren"),
    ShortcutHelp("Backspace / Alt+↑", "Zum übergeordneten Ordner wechseln"),
    ShortcutHelp("F5 / Strg+R", "Aktuellen Ordner aktualisieren"),
    ShortcutHelp("Spaltenkopf", "Nach Name, Typ, Größe oder Änderungsdatum sortieren"),
)


def build_help_text() -> str:
    """Liefert den vollständigen, testbaren Hilfetext."""
    width = max(len(item.keys) for item in SHORTCUT_HELP)
    rows = ["Tastatur und Bedienung", ""]
    rows.extend(f"{item.keys:<{width}}  {item.action}" for item in SHORTCUT_HELP)
    rows.extend(("", "Die aktive Sortierrichtung wird mit ▲ oder ▼ angezeigt."))
    return "\n".join(rows)


def install_keyboard_help(app) -> None:
    """Ergänzt F1 und ein Hilfemenü, ohne bestehende Fensterverträge zu ändern."""
    import tkinter as tk
    from tkinter import ttk

    root = app.root
    existing_menu = root.cget("menu")
    menu = root.nametowidget(existing_menu) if existing_menu else tk.Menu(root)
    help_menu = tk.Menu(menu, tearoff=False)

    def show_help(_event=None) -> str:
        current = getattr(app, "_keyboard_help_window", None)
        try:
            if current is not None and current.winfo_exists():
                current.deiconify()
                current.lift()
                current.focus_force()
                return "break"
        except Exception:
            pass

        window = tk.Toplevel(root)
        app._keyboard_help_window = window
        window.title("Datei-Manager – Hilfe")
        window.transient(root)
        window.resizable(False, False)

        body = ttk.Frame(window, padding=18)
        body.pack(fill="both", expand=True)
        ttk.Label(
            body,
            text=build_help_text(),
            justify="left",
            anchor="w",
            font="TkFixedFont",
        ).pack(fill="both", expand=True)
        ttk.Button(body, text="Schließen", command=window.destroy).pack(anchor="e", pady=(16, 0))

        window.bind("<Escape>", lambda _e: window.destroy())
        window.protocol("WM_DELETE_WINDOW", window.destroy)
        window.update_idletasks()
        x = root.winfo_rootx() + max((root.winfo_width() - window.winfo_width()) // 2, 0)
        y = root.winfo_rooty() + max((root.winfo_height() - window.winfo_height()) // 2, 0)
        window.geometry(f"+{x}+{y}")
        window.focus_force()
        return "break"

    help_menu.add_command(label="Tastatur-Kurzhilfe", accelerator="F1", command=show_help)
    menu.add_cascade(label="Hilfe", menu=help_menu)
    root.configure(menu=menu)
    root.bind("<F1>", show_help, add="+")
    app.show_keyboard_help = show_help
