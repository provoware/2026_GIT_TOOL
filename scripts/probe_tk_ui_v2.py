#!/usr/bin/env python3
"""Kanonische Tk-Probe mit kontrolliertem Callback-Abbruch vor destroy()."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import probe_tk_ui as base
from ui_acceptance import DeviceProfile


def _cancel_pending_callbacks(root) -> None:
    try:
        root.unbind("<Configure>")
    except Exception:
        pass
    try:
        pending = root.tk.splitlist(root.tk.call("after", "info"))
    except Exception:
        pending = ()
    for callback_id in pending:
        try:
            root.after_cancel(callback_id)
        except Exception:
            pass
    try:
        root.update_idletasks()
    except Exception:
        pass


def _probe_surface(
    profile: DeviceProfile,
    surface: str,
    factory: Callable[[Any], Any],
    screenshots: Path | None,
) -> dict[str, Any]:
    import tkinter as tk

    root = tk.Tk()
    try:
        root.geometry(f"{profile.width}x{profile.height}+0+0")
        factory(root)
        root.geometry(f"{profile.width}x{profile.height}+0+0")
        record = base._measure(root, profile, surface)
        if screenshots is not None:
            base._capture(root, screenshots / f"{surface}__{profile.key}.png")
        return record
    finally:
        _cancel_pending_callbacks(root)
        root.destroy()


def main() -> int:
    base._probe_surface = _probe_surface
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
