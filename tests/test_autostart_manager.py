from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "system"))

from autostart_manager import (
    MANAGED_MARKER,
    AutostartError,
    AutostartManager,
    build_desktop_entry,
)


def make_start_script(tmp_path: Path) -> Path:
    project = tmp_path / "project with spaces"
    script = project / "scripts" / "start.sh"
    script.parent.mkdir(parents=True)
    script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    return script


def test_desktop_entry_uses_absolute_project_paths(tmp_path):
    script = make_start_script(tmp_path)

    content = build_desktop_entry(script)

    assert "[Desktop Entry]" in content
    assert "TryExec=/bin/bash" in content
    assert f'Exec=/bin/bash "{script.resolve()}"' in content
    assert f"Path={script.resolve().parent.parent}" in content
    assert "X-GNOME-Autostart-enabled=true" in content
    assert MANAGED_MARKER in content


def test_enable_and_disable_managed_autostart(tmp_path):
    script = make_start_script(tmp_path)
    autostart_dir = tmp_path / "config" / "autostart"
    manager = AutostartManager(script, autostart_dir)

    assert manager.is_enabled() is False
    assert manager.set_enabled(True) is True
    assert manager.desktop_path.exists()
    assert manager.is_enabled() is True

    assert manager.set_enabled(False) is False
    assert manager.desktop_path.exists() is False
    assert manager.is_enabled() is False


def test_enable_is_idempotent_for_managed_file(tmp_path):
    script = make_start_script(tmp_path)
    manager = AutostartManager(script, tmp_path / "autostart")

    manager.set_enabled(True)
    first = manager.desktop_path.read_text(encoding="utf-8")
    manager.set_enabled(True)

    assert manager.desktop_path.read_text(encoding="utf-8") == first


def test_foreign_autostart_file_is_never_overwritten_or_deleted(tmp_path):
    script = make_start_script(tmp_path)
    manager = AutostartManager(script, tmp_path / "autostart")
    manager.autostart_dir.mkdir(parents=True)
    foreign = "[Desktop Entry]\nName=Foreign\nExec=/bin/true\n"
    manager.desktop_path.write_text(foreign, encoding="utf-8")

    with pytest.raises(AutostartError, match="nicht überschrieben"):
        manager.set_enabled(True)
    assert manager.desktop_path.read_text(encoding="utf-8") == foreign

    manager.set_enabled(False)
    assert manager.desktop_path.read_text(encoding="utf-8") == foreign


def test_missing_start_script_blocks_activation(tmp_path):
    manager = AutostartManager(
        tmp_path / "missing" / "start.sh",
        tmp_path / "autostart",
    )

    with pytest.raises(AutostartError, match="Startskript fehlt"):
        manager.set_enabled(True)
    assert manager.desktop_path.exists() is False
