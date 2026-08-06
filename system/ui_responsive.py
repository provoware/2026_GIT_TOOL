#!/usr/bin/env python3
"""Reine Responsive-Regeln für Launcher und Hauptfenster."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil


class UiResponsiveError(ValueError):
    """Viewport oder Layoutanforderung kann nicht erfüllt werden."""


@dataclass(frozen=True)
class LauncherLayout:
    mode: str
    control_columns: int
    developer_columns: int
    help_columns: int


@dataclass(frozen=True)
class WorkspaceGrid:
    rows: int
    columns: int
    cell_width: int
    cell_height: int


LAUNCHER_WIDE_BREAKPOINT = 1200
LAUNCHER_BALANCED_BREAKPOINT = 1000
LAUNCHER_MEDIUM_BREAKPOINT = 800
MAIN_WINDOW_MIN_WIDTH = 720
MAIN_WINDOW_MIN_HEIGHT = 680

LAUNCHER_HELP_FULL = (
    "Schnellstart: 1. Farbschema wählen. 2. Mit „Übersicht aktualisieren“ die Module "
    "neu laden. 3. „Hauptfenster öffnen“ wählen. Bei einem Problem zuerst "
    "„Diagnose starten“ verwenden; technische Details stehen ausschließlich im Ordner "
    "logs/. F1 erklärt das aktuell fokussierte Element. Tastatur: Tab wechselt den Fokus, "
    "Alt+K schaltet den Kontrast um, Strg + Mausrad ändert den Zoom. Wichtige Kurzbefehle: "
    "Alt+R Aktualisieren, Alt+M Hauptfenster, Alt+G Diagnose, Alt+L Logs, Alt+B Backup "
    "und Alt+Q Speichern und Beenden. Strg+Z/Y führt Änderungen zurück oder erneut aus. "
    "Die vollständige Anleitung steht in HILFE.md; Tooltips erklären einzelne Schaltflächen."
)
LAUNCHER_HELP_COMPACT = (
    "Schnellstart: Aktualisieren, Hauptfenster öffnen, Modul wählen. Bei Problemen Alt+G "
    "für Diagnose und danach logs/tool.log prüfen. Tab wechselt den Fokus, F1 und Tooltips "
    "zeigen Hilfe, Strg+Z/Y steuert Undo/Redo. Details: HILFE.md."
)
LAUNCHER_FOOTER_FULL = (
    "Hilfe: F1 · Aktualisieren: Alt+R · Hauptfenster: Alt+M · Diagnose: Alt+G · "
    "Logs: Alt+L · Backup: Alt+B · Kontrast: Alt+K · Beenden: Alt+Q · "
    "Rückgängig/Wiederholen: Strg+Z/Y · Zoom: Strg + Mausrad."
)
LAUNCHER_FOOTER_COMPACT = "F1 · Alt+R · Alt+M · Alt+G · Alt+Q · Strg+Z/Y"


def _positive_int(value: int, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise UiResponsiveError(f"{name} muss eine positive Ganzzahl sein.")
    return value


def resolve_launcher_layout(width: int) -> LauncherLayout:
    width = _positive_int(width, "width")
    if width >= LAUNCHER_WIDE_BREAKPOINT:
        return LauncherLayout("wide", control_columns=3, developer_columns=4, help_columns=2)
    if width >= LAUNCHER_BALANCED_BREAKPOINT:
        return LauncherLayout("medium", control_columns=2, developer_columns=3, help_columns=2)
    if width >= LAUNCHER_MEDIUM_BREAKPOINT:
        return LauncherLayout("medium", control_columns=2, developer_columns=2, help_columns=1)
    return LauncherLayout("compact", control_columns=1, developer_columns=2, help_columns=1)


def resolve_launcher_help_text(width: int) -> str:
    layout = resolve_launcher_layout(width)
    return LAUNCHER_HELP_FULL if layout.mode == "wide" else LAUNCHER_HELP_COMPACT


def resolve_launcher_footer_text(width: int) -> str:
    layout = resolve_launcher_layout(width)
    return LAUNCHER_FOOTER_FULL if layout.mode == "wide" else LAUNCHER_FOOTER_COMPACT


def resolve_workspace_grid(
    count: int,
    width: int,
    height: int,
    *,
    maximum_columns: int = 3,
    gap: int = 12,
    minimum_width: int = 200,
    minimum_height: int = 160,
) -> WorkspaceGrid:
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise UiResponsiveError("count muss eine nichtnegative Ganzzahl sein.")
    width = _positive_int(width, "width")
    height = _positive_int(height, "height")
    maximum_columns = _positive_int(maximum_columns, "maximum_columns")
    minimum_width = _positive_int(minimum_width, "minimum_width")
    minimum_height = _positive_int(minimum_height, "minimum_height")
    if not isinstance(gap, int) or isinstance(gap, bool) or gap < 0:
        raise UiResponsiveError("gap muss eine nichtnegative Ganzzahl sein.")
    if count == 0:
        return WorkspaceGrid(rows=0, columns=0, cell_width=width, cell_height=height)

    for columns in range(min(maximum_columns, count), 0, -1):
        rows = ceil(count / columns)
        cell_width = (width - gap * (columns - 1)) // columns
        cell_height = (height - gap * (rows - 1)) // rows
        if cell_width >= minimum_width and cell_height >= minimum_height:
            return WorkspaceGrid(rows, columns, cell_width, cell_height)
    raise UiResponsiveError(
        "Viewport ist für die sichtbaren Modulkarten zu klein: "
        f"{width}×{height}, Module={count}."
    )
