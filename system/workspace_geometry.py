#!/usr/bin/env python3
"""Reine Geometrie- und Rasterberechnungen für das Tkinter-Hauptfenster."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


class WorkspaceGeometryError(ValueError):
    """Ungültige Eingaben für Workspace-Berechnungen."""


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        for name, value in (
            ("x", self.x),
            ("y", self.y),
            ("width", self.width),
            ("height", self.height),
        ):
            if not isinstance(value, int):
                raise WorkspaceGeometryError(f"{name} muss ganzzahlig sein.")
        if self.width < 0 or self.height < 0:
            raise WorkspaceGeometryError("Breite und Höhe dürfen nicht negativ sein.")


@dataclass(frozen=True)
class ModuleSize:
    """Dokumentierte Standard- und Mindestgröße einer Modulkarte."""

    width: int = 320
    height: int = 220
    min_width: int = 200
    min_height: int = 160

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise WorkspaceGeometryError(f"{name} muss eine positive Ganzzahl sein.")
        if self.width < self.min_width or self.height < self.min_height:
            raise WorkspaceGeometryError("Standardgröße darf nicht kleiner als die Mindestgröße sein.")


def _require_non_negative(value: int, label: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise WorkspaceGeometryError(f"{label} muss eine nichtnegative Ganzzahl sein.")
    return value


def rect_overlap(a: Rect, b: Rect) -> bool:
    if not isinstance(a, Rect) or not isinstance(b, Rect):
        raise WorkspaceGeometryError("Kollisionsprüfung benötigt zwei Rect-Objekte.")
    return (
        a.x < b.x + b.width
        and a.x + a.width > b.x
        and a.y < b.y + b.height
        and a.y + a.height > b.y
    )


def clamp_rect(rect: Rect, workspace_width: int, workspace_height: int) -> Rect:
    if not isinstance(rect, Rect):
        raise WorkspaceGeometryError("rect muss ein Rect-Objekt sein.")
    workspace_width = _require_non_negative(workspace_width, "workspace_width")
    workspace_height = _require_non_negative(workspace_height, "workspace_height")
    width = min(rect.width, workspace_width)
    height = min(rect.height, workspace_height)
    x = min(max(rect.x, 0), max(0, workspace_width - width))
    y = min(max(rect.y, 0), max(0, workspace_height - height))
    return Rect(x, y, width, height)


def move_rect(
    rect: Rect,
    delta_x: int,
    delta_y: int,
    workspace_width: int,
    workspace_height: int,
) -> Rect:
    if not isinstance(delta_x, int) or not isinstance(delta_y, int):
        raise WorkspaceGeometryError("Verschiebung muss ganzzahlig sein.")
    return clamp_rect(
        Rect(rect.x + delta_x, rect.y + delta_y, rect.width, rect.height),
        workspace_width,
        workspace_height,
    )


def resize_rect(
    rect: Rect,
    requested_width: int,
    requested_height: int,
    workspace_width: int,
    workspace_height: int,
    min_width: int,
    min_height: int,
) -> Rect:
    if not isinstance(rect, Rect):
        raise WorkspaceGeometryError("rect muss ein Rect-Objekt sein.")
    for label, value in (
        ("requested_width", requested_width),
        ("requested_height", requested_height),
        ("min_width", min_width),
        ("min_height", min_height),
    ):
        _require_non_negative(value, label)
    workspace_width = _require_non_negative(workspace_width, "workspace_width")
    workspace_height = _require_non_negative(workspace_height, "workspace_height")
    available_width = max(0, workspace_width - max(0, rect.x))
    available_height = max(0, workspace_height - max(0, rect.y))
    width = min(max(min_width, requested_width), available_width)
    height = min(max(min_height, requested_height), available_height)
    return Rect(max(0, rect.x), max(0, rect.y), width, height)


def has_collision(candidate: Rect, others: Iterable[Rect]) -> bool:
    if not isinstance(candidate, Rect):
        raise WorkspaceGeometryError("candidate muss ein Rect-Objekt sein.")
    for rect in others:
        if not isinstance(rect, Rect):
            raise WorkspaceGeometryError("others darf nur Rect-Objekte enthalten.")
        if rect_overlap(candidate, rect):
            return True
    return False


def build_grid(
    count: int,
    workspace_width: int,
    workspace_height: int,
    *,
    rows: int = 3,
    cols: int = 3,
    gap: int = 12,
    min_width: int = 180,
    min_height: int = 120,
) -> List[Rect]:
    for label, value in (
        ("count", count),
        ("workspace_width", workspace_width),
        ("workspace_height", workspace_height),
        ("rows", rows),
        ("cols", cols),
        ("gap", gap),
        ("min_width", min_width),
        ("min_height", min_height),
    ):
        _require_non_negative(value, label)
    if rows == 0 or cols == 0:
        raise WorkspaceGeometryError("rows und cols müssen größer als null sein.")
    visible_count = min(count, rows * cols)
    if visible_count == 0:
        return []
    usable_width = max(0, workspace_width - gap * (cols + 1))
    usable_height = max(0, workspace_height - gap * (rows + 1))
    cell_width = usable_width // cols
    cell_height = usable_height // rows
    if workspace_width >= min_width + 2 * gap:
        cell_width = max(min_width, cell_width)
    if workspace_height >= min_height + 2 * gap:
        cell_height = max(min_height, cell_height)
    cell_width = min(cell_width, max(0, workspace_width - 2 * gap))
    cell_height = min(cell_height, max(0, workspace_height - 2 * gap))
    result: List[Rect] = []
    for index in range(visible_count):
        row = index // cols
        col = index % cols
        x = gap + col * (cell_width + gap)
        y = gap + row * (cell_height + gap)
        result.append(clamp_rect(Rect(x, y, cell_width, cell_height), workspace_width, workspace_height))
    return result
