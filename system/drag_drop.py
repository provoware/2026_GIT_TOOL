#!/usr/bin/env python3
"""Globales Drag-and-Drop für Datei- und Modul-Pfade."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List


class DragDropError(Exception):
    """Fehler im Drag-and-Drop-System."""


DropCallback = Callable[[List[Path]], None]


@dataclass(frozen=True)
class DragDropResult:
    paths: List[Path]
    raw_data: str


def parse_drop_data(raw_data: str) -> List[Path]:
    if not isinstance(raw_data, str) or not raw_data.strip():
        raise DragDropError("Drop-Daten fehlen oder sind leer.")
    cleaned = raw_data.strip()
    paths: List[Path] = []
    buffer = ""
    in_braces = False
    for char in cleaned:
        if char == "{":
            in_braces = True
            if buffer.strip():
                paths.append(Path(buffer.strip()))
                buffer = ""
            continue
        if char == "}":
            in_braces = False
            if buffer:
                paths.append(Path(buffer))
                buffer = ""
            continue
        if char.isspace() and not in_braces:
            if buffer.strip():
                paths.append(Path(buffer.strip()))
                buffer = ""
            continue
        buffer += char
    if buffer.strip():
        paths.append(Path(buffer.strip()))
    return [path for path in paths if str(path).strip()]


def _require_callback(callback: DropCallback) -> DropCallback:
    if not callable(callback):
        raise DragDropError("callback ist nicht aufrufbar.")
    return callback


class DragDropManager:
    def __init__(self, root, callback: DropCallback) -> None:
        if root is None:
            raise DragDropError("root fehlt.")
        self.root = root
        self.callback = _require_callback(callback)
        self.enabled = False

    def enable(self, widgets: Iterable[object]) -> bool:
        try:
            self.root.tk.call("package", "require", "tkdnd")
        except Exception:
            self.enabled = False
            return False
        for widget in widgets:
            if widget is None:
                continue
            self.root.tk.call("tkdnd::drop_target", "register", widget, "*")
            widget.bind("<<Drop>>", self._handle_drop)
        self.enabled = True
        return True

    def _handle_drop(self, event) -> None:
        raw_data = getattr(event, "data", "")
        try:
            paths = parse_drop_data(raw_data)
        except DragDropError:
            self.callback([])
            return
        if not paths:
            self.callback([])
            return
        self.callback(paths)

    def describe_state(self) -> str:
        return "aktiv" if self.enabled else "inaktiv"
