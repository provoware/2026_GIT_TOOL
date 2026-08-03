from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "system"))

from ui_responsive import (
    LAUNCHER_FOOTER_COMPACT,
    LAUNCHER_FOOTER_FULL,
    LAUNCHER_HELP_COMPACT,
    LAUNCHER_HELP_FULL,
    MAIN_WINDOW_MIN_HEIGHT,
    MAIN_WINDOW_MIN_WIDTH,
    UiResponsiveError,
    resolve_launcher_footer_text,
    resolve_launcher_help_text,
    resolve_launcher_layout,
    resolve_workspace_grid,
)


def test_launcher_uses_three_two_and_one_column_modes():
    assert resolve_launcher_layout(1440).mode == "wide"
    assert resolve_launcher_layout(1440).control_columns == 3
    assert resolve_launcher_layout(1024).mode == "medium"
    assert resolve_launcher_layout(1024).control_columns == 2
    assert resolve_launcher_layout(768).mode == "compact"
    assert resolve_launcher_layout(768).control_columns == 1


def test_help_uses_two_columns_when_1024_pixels_are_available():
    assert resolve_launcher_layout(999).help_columns == 1
    assert resolve_launcher_layout(1024).help_columns == 2
    assert resolve_launcher_layout(1200).help_columns == 2


def test_help_text_is_compact_below_wide_breakpoint_without_losing_help_paths():
    assert resolve_launcher_help_text(1440) == LAUNCHER_HELP_FULL
    assert resolve_launcher_help_text(1024) == LAUNCHER_HELP_COMPACT
    assert resolve_launcher_help_text(768) == LAUNCHER_HELP_COMPACT
    assert "F1" in LAUNCHER_HELP_COMPACT
    assert "Tooltips" in LAUNCHER_HELP_COMPACT
    assert len(LAUNCHER_HELP_COMPACT) < len(LAUNCHER_HELP_FULL) / 2


def test_footer_is_compact_below_wide_breakpoint_and_keeps_core_shortcuts():
    assert resolve_launcher_footer_text(1440) == LAUNCHER_FOOTER_FULL
    assert resolve_launcher_footer_text(1024) == LAUNCHER_FOOTER_COMPACT
    assert resolve_launcher_footer_text(768) == LAUNCHER_FOOTER_COMPACT
    for shortcut in ("F1", "Alt+R", "Alt+G", "Alt+M", "Alt+Q", "Strg+Z/Y"):
        assert shortcut in LAUNCHER_FOOTER_COMPACT
    assert len(LAUNCHER_FOOTER_COMPACT) < len(LAUNCHER_FOOTER_FULL) / 2


def test_developer_actions_use_three_by_two_grid_at_1024_pixels():
    assert resolve_launcher_layout(1024).developer_columns == 3
    assert resolve_launcher_layout(900).developer_columns == 2
    assert resolve_launcher_layout(768).developer_columns == 2


def test_main_window_minimum_supports_tablet_portrait_width():
    assert MAIN_WINDOW_MIN_WIDTH <= 768
    assert MAIN_WINDOW_MIN_HEIGHT <= 1024


def test_workspace_grid_fits_nine_cards_at_new_minimum():
    # 32 px horizontal and about 100 px vertical chrome are reserved by the UI.
    grid = resolve_workspace_grid(9, MAIN_WINDOW_MIN_WIDTH - 32, MAIN_WINDOW_MIN_HEIGHT - 100)

    assert (grid.rows, grid.columns) == (3, 3)
    assert grid.cell_width >= 200
    assert grid.cell_height >= 160


def test_workspace_grid_reduces_columns_when_width_requires_it():
    grid = resolve_workspace_grid(
        4,
        430,
        700,
        maximum_columns=3,
        minimum_width=200,
        minimum_height=160,
    )

    assert (grid.rows, grid.columns) == (2, 2)


def test_workspace_grid_rejects_unusable_viewport():
    with pytest.raises(UiResponsiveError, match="zu klein"):
        resolve_workspace_grid(9, 390, 844)


def test_invalid_width_fails_early():
    with pytest.raises(UiResponsiveError):
        resolve_launcher_layout(0)
