from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for import_path in (ROOT, ROOT / "system", ROOT / "modules" / "datei_manager"):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from browser import BrowserError, list_directory  # noqa: E402
from module_history import create_history_entry, format_history  # noqa: E402
from workspace_geometry import ModuleSize, WorkspaceGeometryError  # noqa: E402


def test_module_size_contract_is_safe_and_stable() -> None:
    size = ModuleSize()

    assert (size.width, size.height) == (320, 220)
    assert (size.min_width, size.min_height) == (200, 160)
    assert size.width >= size.min_width
    assert size.height >= size.min_height

    with pytest.raises(WorkspaceGeometryError):
        ModuleSize(width=size.min_width - 1)


def test_module_history_rejects_incomplete_entries_and_formats_latest_first() -> None:
    first = create_history_entry("1.0.0", "idle", "Modul geladen.")
    second = create_history_entry("1.0.0", "ok", "Modul aktiviert.")

    output = format_history([first, second])
    lines = output.splitlines()

    assert len(lines) == 2
    assert "ok: Modul aktiviert." in lines[0]
    assert "idle: Modul geladen." in lines[1]
    assert all("Version 1.0.0" in line for line in lines)

    for invalid in (
        ("", "ok", "Aktiviert"),
        ("1.0.0", "", "Aktiviert"),
        ("1.0.0", "ok", ""),
    ):
        with pytest.raises(ValueError):
            create_history_entry(*invalid)


def test_file_manager_rejects_missing_paths_and_lists_deterministically(tmp_path: Path) -> None:
    (tmp_path / "zeta.txt").write_text("z", encoding="utf-8")
    (tmp_path / "Alpha.txt").write_text("a", encoding="utf-8")
    (tmp_path / "beta.txt").write_text("b", encoding="utf-8")

    entries = list_directory(tmp_path)
    names = [entry.name for entry in entries]

    assert names == sorted(names, key=str.casefold)

    with pytest.raises(BrowserError, match="Ordnerpfad"):
        list_directory("")
    with pytest.raises(BrowserError):
        list_directory(tmp_path / "nicht-vorhanden")


def test_main_window_keeps_version_history_and_shared_size_integration() -> None:
    source = (ROOT / "system" / "main_window.py").read_text(encoding="utf-8")

    required_markers = (
        "from module_history import format_history",
        "ModuleSize",
        'text=f"Version: {version}"',
        'text="Verlauf"',
        "format_history(self.state.history or [])",
        "minimum_width=ModuleSize().min_width",
        "minimum_height=ModuleSize().min_height",
    )
    for marker in required_markers:
        assert marker in source, marker


def test_lifecycle_keeps_textual_status_signals_for_accessibility() -> None:
    source = (ROOT / "system" / "module_lifecycle.py").read_text(encoding="utf-8")

    for signal in (
        "Rot – Fehler",
        "Gelb – Hinweis",
        "Grün – aktiv",
        "Grau – inaktiv",
        'status_text=f"Ampel: {signal}"',
    ):
        assert signal in source, signal


def test_module_manager_records_load_activate_and_deactivate_history() -> None:
    source = (ROOT / "system" / "module_manager.py").read_text(encoding="utf-8")

    assert "history: list[ModuleHistoryEntry] | None = None" in source
    assert source.count("self._record_history(state)") >= 3
    assert "state.history.append(create_history_entry(" in source
