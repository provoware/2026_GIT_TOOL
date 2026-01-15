#!/usr/bin/env python3
"""AppImage-Builder mit integriertem Self-Check."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from config_utils import ensure_path, load_json
from desktop_entry import DesktopEntryConfig
from desktop_entry import load_config as load_desktop_config

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = DEFAULT_ROOT / "config" / "appimage_package.json"


class AppImageBuildError(ValueError):
    """Fehler beim AppImage-Build."""


@dataclass(frozen=True)
class AppImageConfig:
    app_id: str
    app_name: str
    version: str
    install_root: str
    desktop_entry_config: Path
    icon_source: Path
    exclude_paths: List[str]
    output_dir: Path
    self_check_command: str
    start_command: str


def load_config(path: Path) -> AppImageConfig:
    data = load_json(
        path,
        AppImageBuildError,
        "AppImage-Konfiguration fehlt",
        "AppImage-Konfiguration ungültig",
    )
    config = AppImageConfig(
        app_id=str(data.get("app_id", "")).strip(),
        app_name=str(data.get("app_name", "")).strip(),
        version=str(data.get("version", "")).strip(),
        install_root=str(data.get("install_root", "")).strip(),
        desktop_entry_config=Path(str(data.get("desktop_entry_config", "")).strip()),
        icon_source=Path(str(data.get("icon_source", "")).strip()),
        exclude_paths=list(data.get("exclude_paths", [])),
        output_dir=Path(str(data.get("output_dir", "dist")).strip()),
        self_check_command=str(data.get("self_check_command", "")).strip(),
        start_command=str(data.get("start_command", "")).strip(),
    )
    validate_config(config)
    return config


def validate_config(config: AppImageConfig) -> None:
    if not config.app_id:
        raise AppImageBuildError("App-ID fehlt in der AppImage-Konfiguration.")
    if not config.app_name:
        raise AppImageBuildError("App-Name fehlt in der AppImage-Konfiguration.")
    if not config.version:
        raise AppImageBuildError("Version fehlt in der AppImage-Konfiguration.")
    if not config.install_root:
        raise AppImageBuildError("Installationsziel fehlt in der AppImage-Konfiguration.")
    if not config.desktop_entry_config:
        raise AppImageBuildError("Desktop-Entry-Konfiguration fehlt.")
    if not config.icon_source:
        raise AppImageBuildError("Icon-Quelle fehlt.")
    if not config.self_check_command:
        raise AppImageBuildError("Self-Check-Kommando fehlt.")
    if not config.start_command:
        raise AppImageBuildError("Start-Kommando fehlt.")


def _resolve_repo_path(repo_root: Path, path_value: Path) -> Path:
    ensure_path(repo_root, "repo_root", AppImageBuildError)
    ensure_path(path_value, "path_value", AppImageBuildError)
    if path_value.is_absolute():
        return path_value
    return repo_root / path_value


def _copy_repo_tree(repo_root: Path, target_root: Path, exclude_paths: Iterable[str]) -> int:
    file_count = 0
    for path in repo_root.rglob("*"):
        rel = path.relative_to(repo_root)
        rel_posix = rel.as_posix()
        if any(rel_posix == item or rel_posix.startswith(f"{item}/") for item in exclude_paths):
            continue
        dest = target_root / rel
        if path.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        file_count += 1
    return file_count


def _build_desktop_entry(config: DesktopEntryConfig) -> str:
    categories = ";".join(config.categories) + ";"
    keywords = ";".join(config.keywords) + ";" if config.keywords else ""
    terminal = "true" if config.terminal else "false"
    lines = [
        "[Desktop Entry]",
        "Type=Application",
        f"Name={config.app_name}",
        f"Comment={config.comment}",
        "Exec=AppRun",
        f"Icon={config.icon_name}",
        f"Terminal={terminal}",
        f"Categories={categories}",
        f"Keywords={keywords}",
        f"StartupWMClass={config.app_id}",
    ]
    return "\n".join(lines) + "\n"


def _build_apprun(config: AppImageConfig) -> str:
    app_root = config.install_root.rstrip("/")
    self_check = config.self_check_command.format(app_root=app_root)
    start_cmd = config.start_command.format(app_root=app_root)
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        'APPDIR="$(cd "$(dirname "$0")" && pwd)"',
        f'APP_ROOT="${{APPDIR}}{app_root}"',
        'SAFE_MODE=""',
        'mkdir -p "${APP_ROOT}/logs" "${APP_ROOT}/data"',
        "if ! command -v python3 >/dev/null 2>&1; then",
        '  echo "Fehler: python3 fehlt."',
        '  echo "Lösung: python3 installieren und erneut starten."',
        "  exit 1",
        "fi",
        'echo "AppImage: Self-Check startet..."',
        f"if ! {self_check}; then",
        '  echo "Warnung: Self-Check fehlgeschlagen."',
        '  echo "Lösung: Health-Check manuell ausführen oder Safe-Mode nutzen."',
        '  SAFE_MODE="--safe-mode"',
        "fi",
        'echo "AppImage: Start-Routine wird ausgeführt..."',
        f"exec {start_cmd} $SAFE_MODE",
    ]
    return "\n".join(lines) + "\n"


def build_appimage(repo_root: Path, config: AppImageConfig, logger: logging.Logger) -> Path:
    appimagetool = shutil.which("appimagetool")
    if not appimagetool:
        raise AppImageBuildError("appimagetool fehlt. Bitte 'appimagetool' installieren.")

    output_dir = repo_root / config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = config.app_name.replace(" ", "_")
    output_path = output_dir / f"{safe_name}_{config.version}_{timestamp}.AppImage"

    with tempfile.TemporaryDirectory() as tmpdir:
        appdir = Path(tmpdir) / f"{config.app_id}.AppDir"
        appdir.mkdir(parents=True, exist_ok=True)

        install_root = appdir / config.install_root.lstrip("/")
        file_count = _copy_repo_tree(repo_root, install_root, config.exclude_paths)
        if file_count == 0:
            raise AppImageBuildError("Keine Dateien für das AppImage gefunden.")

        desktop_config = load_desktop_config(
            _resolve_repo_path(repo_root, config.desktop_entry_config)
        )
        desktop_content = _build_desktop_entry(desktop_config)
        desktop_path = appdir / f"{desktop_config.app_id}.desktop"
        desktop_path.write_text(desktop_content, encoding="utf-8")

        icon_source = _resolve_repo_path(repo_root, config.icon_source)
        icon_target = appdir / f"{desktop_config.icon_name}.svg"
        icon_target.write_bytes(icon_source.read_bytes())

        apprun_path = appdir / "AppRun"
        apprun_path.write_text(_build_apprun(config), encoding="utf-8")
        apprun_path.chmod(0o755)

        logger.info("AppDir erstellt: %s", appdir)
        subprocess.run([appimagetool, str(appdir), str(output_path)], check=True)

    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Erstellt ein AppImage mit integriertem Self-Check.",
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Projekt-Root")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Konfig-Datei")
    parser.add_argument("--debug", action="store_true", help="Debug-Modus aktivieren")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    logger = logging.getLogger("appimage_builder")

    try:
        config = load_config(args.config)
        output_path = build_appimage(args.root, config, logger)
        logger.info("AppImage erstellt: %s", output_path)
    except (
        AppImageBuildError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as exc:
        logger.error("AppImage-Build fehlgeschlagen: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
