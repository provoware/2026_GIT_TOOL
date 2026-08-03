#!/usr/bin/env python3
"""Sichere Verwaltung des benutzerspezifischen Linux-XDG-Autostarts."""

from __future__ import annotations

import os
from pathlib import Path


class AutostartError(ValueError):
    """Ungültige oder nicht sicher verwaltbare Autostart-Konfiguration."""


MANAGED_MARKER = "X-Genrearchiv-Managed=true"
DESKTOP_FILE_NAME = "genrearchiv.desktop"


def default_autostart_dir() -> Path:
    config_home = os.environ.get("XDG_CONFIG_HOME", "").strip()
    base = Path(config_home).expanduser() if config_home else Path.home() / ".config"
    return base / "autostart"


def _desktop_quote(value: Path) -> str:
    text = str(value)
    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("`", "\\`").replace("$", "\\$")
    return f'"{escaped}"'


def build_desktop_entry(start_script: Path) -> str:
    if not isinstance(start_script, Path):
        raise AutostartError("start_script ist kein Pfad (Path).")
    script = start_script.expanduser().resolve()
    if not script.exists() or not script.is_file():
        raise AutostartError(f"Startskript fehlt: {script}")
    project_root = script.parent.parent
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Version=1.0\n"
        "Name=Genrearchiv\n"
        "Comment=Genrearchiv beim Anmelden starten\n"
        f"Exec=/bin/bash {_desktop_quote(script)}\n"
        f"Path={_desktop_quote(project_root)}\n"
        "Terminal=false\n"
        "X-GNOME-Autostart-enabled=true\n"
        f"{MANAGED_MARKER}\n"
    )


class AutostartManager:
    """Aktiviert oder deaktiviert ausschließlich den eigenen Desktop-Eintrag."""

    def __init__(self, start_script: Path, autostart_dir: Path | None = None) -> None:
        if not isinstance(start_script, Path):
            raise AutostartError("start_script ist kein Pfad (Path).")
        if autostart_dir is not None and not isinstance(autostart_dir, Path):
            raise AutostartError("autostart_dir ist kein Pfad (Path).")
        self.start_script = start_script.expanduser().resolve()
        self.autostart_dir = (autostart_dir or default_autostart_dir()).expanduser()
        self.desktop_path = self.autostart_dir / DESKTOP_FILE_NAME

    def is_enabled(self) -> bool:
        if not self.desktop_path.exists() or not self.desktop_path.is_file():
            return False
        try:
            content = self.desktop_path.read_text(encoding="utf-8")
        except OSError:
            return False
        return MANAGED_MARKER in content and "X-GNOME-Autostart-enabled=true" in content

    def set_enabled(self, enabled: bool) -> bool:
        if not isinstance(enabled, bool):
            raise AutostartError("enabled ist kein boolescher Wert.")
        if enabled:
            self._enable()
            return True
        self._disable()
        return False

    def _enable(self) -> None:
        if self.desktop_path.exists() and not self._is_managed_file():
            raise AutostartError(
                f"Autostart-Datei wird nicht überschrieben, weil sie nicht vom Tool verwaltet wird: {self.desktop_path}"
            )
        content = build_desktop_entry(self.start_script)
        self.autostart_dir.mkdir(parents=True, exist_ok=True)
        temporary = self.autostart_dir / f".{DESKTOP_FILE_NAME}.tmp"
        try:
            temporary.write_text(content, encoding="utf-8")
            temporary.replace(self.desktop_path)
        except OSError as exc:
            temporary.unlink(missing_ok=True)
            raise AutostartError(f"Autostart konnte nicht aktiviert werden: {exc}") from exc

    def _disable(self) -> None:
        if not self.desktop_path.exists():
            return
        if not self._is_managed_file():
            return
        try:
            self.desktop_path.unlink()
        except OSError as exc:
            raise AutostartError(f"Autostart konnte nicht deaktiviert werden: {exc}") from exc

    def _is_managed_file(self) -> bool:
        try:
            return MANAGED_MARKER in self.desktop_path.read_text(encoding="utf-8")
        except OSError:
            return False
