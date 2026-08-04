import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from workspace_geometry import ModuleSize, Rect, WorkspaceGeometryError, build_grid, clamp_rect, has_collision, move_rect, rect_overlap, resize_rect


def test_overlap_cases():
    a = Rect(0, 0, 100, 100)
    assert not rect_overlap(a, Rect(100, 0, 20, 20))
    assert rect_overlap(a, Rect(90, 90, 20, 20))
    assert rect_overlap(a, Rect(10, 10, 20, 20))


def test_clamp_and_move():
    assert clamp_rect(Rect(-20, -10, 50, 40), 200, 100) == Rect(0, 0, 50, 40)
    assert clamp_rect(Rect(190, 90, 50, 40), 200, 100) == Rect(150, 60, 50, 40)
    assert move_rect(Rect(20, 20, 50, 40), -100, 200, 200, 100) == Rect(0, 60, 50, 40)


def test_resize_bounds():
    assert resize_rect(Rect(150, 80, 20, 20), 10, 10, 200, 100, 40, 30) == Rect(150, 80, 40, 20)
    result = resize_rect(Rect(250, 120, 10, 10), 50, 50, 200, 100, 20, 20)
    assert result.width == 0 and result.height == 0


def test_collision_uses_supplied_rectangles():
    current = Rect(0, 0, 100, 100)
    assert not has_collision(current, [])
    assert has_collision(current, [Rect(50, 50, 20, 20)])


def test_grid_limit_bounds_and_reflow():
    rects = build_grid(12, 1200, 820)
    assert len(rects) == 9
    for index, rect in enumerate(rects):
        assert rect.x + rect.width <= 1200
        assert rect.y + rect.height <= 820
        assert not has_collision(rect, rects[:index])
    for width, height in ((360, 300), (1600, 1000)):
        resized = build_grid(6, width, height)
        assert all(r.x + r.width <= width and r.y + r.height <= height for r in resized)


def test_invalid_inputs():
    with pytest.raises(WorkspaceGeometryError):
        Rect(0, 0, -1, 10)
    with pytest.raises(WorkspaceGeometryError):
        build_grid(1, -1, 100)


def test_module_size_defines_safe_defaults():
    size = ModuleSize()
    assert (size.width, size.height) == (320, 220)
    assert size.width >= size.min_width and size.height >= size.min_height
    with pytest.raises(WorkspaceGeometryError):
        ModuleSize(width=100)
